# core/scoring_adjuster.py — V5.5.0
from __future__ import annotations

import importlib
import json
import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from .signals_normalizer import SignalNormalise

__all__ = ["ajuster_score_pool", "ScoreDetails"]

LOGGER = logging.getLogger(__name__)


@dataclass
class ScoreDetails:
    """Détails d'ajustement appliqués à un score de pool."""

    score_initial: float
    score_final: float
    coeff_contexte: float
    coeff_ai: float
    coeff_risque: float
    contexte: str
    ai_score_moyen: Optional[float] = None
    drapeaux_risque: List[str] = field(default_factory=list)
    mode_v5_5: str = "NORMAL"
    coeff_mode_v5_5: float = 1.0
    config_path: Optional[str] = None


def ajuster_score_pool(
    pool: Dict[str, object],
    score_initial: float,
    signaux: List[SignalNormalise],
    contexte: str,
    retourner_details: bool = False,
    mode_v5_5: Optional[str] = None,
    strategy_cfg: Optional[Dict[str, Any]] = None,
) -> float | tuple[float, ScoreDetails]:

    """Ajuste dynamiquement le score d'une pool selon les signaux fournis."""

    coeff_contexte = _calculer_coeff_contexte(contexte)
    coeff_ai, ai_score_moyen = _calculer_coeff_ai(signaux)
    coeff_risque, drapeaux_risque = _evaluer_risque(signaux)

    cfg, cfg_path = _charger_config_v5_5()
    mode_effectif = (mode_v5_5 or _deduire_mode_v5_5(signaux) or "NORMAL").strip().upper()

    coeff_mode_v5_5 = 1.0
    coeff_penalite_slippage = 1.0

    if cfg is not None:
        coeff_mode_v5_5, coeff_risque, coeff_penalite_slippage = _appliquer_multiplicateurs_v5_5(
            coeff_risque=coeff_risque,
            mode=mode_effectif,
            cfg=cfg,
            signaux=signaux,
        )

    score_intermediaire = (
        float(score_initial)
        * float(coeff_contexte)
        * float(coeff_ai)
        * float(coeff_risque)
        * float(coeff_mode_v5_5)
        * float(coeff_penalite_slippage)
    )

    score_final = 0.0 if score_intermediaire < 0 else score_intermediaire

    if retourner_details:
        LOGGER.info(
            "Ajustement pool %s (%s) : %.2f ➜ %.2f",
            pool.get("id", "inconnu"),
            contexte,
            score_initial,
            score_final,
        )
        details = ScoreDetails(
            score_initial=float(score_initial),
            score_final=float(score_final),
            coeff_contexte=float(coeff_contexte),
            coeff_ai=float(coeff_ai),
            coeff_risque=float(coeff_risque),
            contexte=str(contexte),
            ai_score_moyen=ai_score_moyen,
            drapeaux_risque=drapeaux_risque,
            mode_v5_5=mode_effectif,
            coeff_mode_v5_5=float(coeff_mode_v5_5) * float(coeff_penalite_slippage),
            config_path=cfg_path if cfg is not None else None,
        )
        return float(score_final), details

    return float(score_final)


def _calculer_coeff_contexte(contexte: str) -> float:
    contexte_normalise = (contexte or "").strip().lower()
    mapping = {
        "favorable": 1.08,
        "bull": 1.06,
        "haussier": 1.05,
        "neutre": 1.0,
        "defavorable": 0.9,
        "bear": 0.92,
        "risque": 0.93,
        "crash": 0.87,
    }
    return mapping.get(contexte_normalise, 1.0)


def _calculer_coeff_ai(signaux: List[SignalNormalise]) -> Tuple[float, Optional[float]]:
    ai_scores: List[float] = []
    for signal in signaux:
        ai_score = _extraire_champ(signal, "ai_score")
        if isinstance(ai_score, (int, float)):
            ai_scores.append(float(ai_score))

    if not ai_scores:
        return 1.0, None

    moyenne = sum(ai_scores) / len(ai_scores)
    if moyenne >= 0.7:
        coeff = 1.08
    elif moyenne >= 0.4:
        coeff = 1.04
    elif moyenne <= -0.7:
        coeff = 0.92
    elif moyenne <= -0.4:
        coeff = 0.96
    else:
        coeff = 1.0

    coeff = clamp(coeff, 0.9, 1.1)
    return coeff, moyenne


def _evaluer_risque(signaux: List[SignalNormalise]) -> Tuple[float, List[str]]:
    coeff = 1.0
    drapeaux: List[str] = []

    for signal in signaux:
        metrics = _extraire_champ(signal, "metrics")
        if not isinstance(metrics, dict):
            continue

        apr = _extraire_metric(metrics, {"apr", "apr_pct"})
        tvl = _extraire_metric(metrics, {"tvl", "liquidity"})
        volatilite = _extraire_metric(metrics, {"volatilite", "volatility"})

        if isinstance(apr, (int, float)):
            if apr > 5000:
                coeff *= 0.85
                drapeaux.append("apr_extreme")
            elif apr > 1500:
                coeff *= 0.93
                drapeaux.append("apr_eleve")
            elif 5 < apr < 250:
                coeff *= 1.02

        if isinstance(tvl, (int, float)):
            if tvl < 10_000:
                coeff *= 0.9
                drapeaux.append("tvl_faible")
            elif tvl > 100_000_000:
                coeff *= 1.02

        if isinstance(volatilite, (int, float)):
            if volatilite > 0.8:
                coeff *= 0.9
                drapeaux.append("volatilite_elevee")
            elif 0.2 < volatilite < 0.5:
                coeff *= 1.01

    coeff = clamp(coeff, 0.8, 1.05)
    return coeff, drapeaux


def _deduire_mode_v5_5(signaux: List[SignalNormalise]) -> Optional[str]:
    champs_mode = ("mode_v5_5", "mode", "strategie_mode")
    for signal in signaux:
        for champ in champs_mode:
            valeur = _extraire_champ(signal, champ)
            if isinstance(valeur, str) and valeur.strip():
                return valeur.strip().upper()

        metrics = _extraire_champ(signal, "metrics")
        if isinstance(metrics, dict):
            for champ in champs_mode:
                valeur_metric = metrics.get(champ)
                if isinstance(valeur_metric, str) and valeur_metric.strip():
                    return valeur_metric.strip().upper()

    return None


def _appliquer_multiplicateurs_v5_5(
    coeff_risque: float,
    mode: str,
    cfg: Dict[str, Any],
    signaux: List[SignalNormalise],
) -> Tuple[float, float, float]:
    overrides = (
        cfg.get("scoring_overrides", {})
        .get("mode_multipliers", {})
        .get((mode or "").upper())
    )

    coeff_mode = 1.0
    coeff_penalite_slippage = 1.0

    if not isinstance(overrides, dict):
        LOGGER.debug("Aucun override V5.5 pour le mode '%s'", mode)
        return coeff_mode, coeff_risque, coeff_penalite_slippage

    risk_mult = overrides.get("risk")
    if isinstance(risk_mult, (int, float)) and float(risk_mult) > 0:
        coeff_risque = clamp(float(coeff_risque) / float(risk_mult), 0.7, 1.2)

    apr_mult = overrides.get("apr")
    tvl_mult = overrides.get("tvl")
    multiplicateurs = [
        float(m) for m in (apr_mult, tvl_mult) if isinstance(m, (int, float)) and float(m) > 0
    ]
    if multiplicateurs:
        coeff_mode = clamp(sum(multiplicateurs) / len(multiplicateurs), 0.5, 1.5)

    coeff_penalite_slippage = _calculer_penalite_slippage(signaux, overrides.get("slippage"))

    LOGGER.debug(
        "Mode V5.5 '%s' ➜ coeff_mode %.3f, coeff_risque %.3f, coeff_slippage %.3f",
        mode,
        coeff_mode,
        coeff_risque,
        coeff_penalite_slippage,
    )

    return float(coeff_mode), float(coeff_risque), float(coeff_penalite_slippage)


def _calculer_penalite_slippage(signaux: List[SignalNormalise], slippage_multiplier: Any) -> float:
    if not isinstance(slippage_multiplier, (int, float)) or float(slippage_multiplier) <= 0:
        return 1.0

    slippage_valeur: Optional[float] = None
    for signal in signaux:
        metrics = _extraire_champ(signal, "metrics")
        if not isinstance(metrics, dict):
            continue

        slippage_valeur = _extraire_metric(metrics, {"slippage", "slippage_bps", "swap_slippage"})
        if slippage_valeur is None:
            continue

        keys_lower = {k.lower() for k in metrics.keys()}
        raw = float(abs(slippage_valeur))

        if "slippage_bps" in keys_lower:
            raw = raw / 10_000.0
        elif raw > 1.0:
            raw = raw / 100.0

        slippage_valeur = clamp(raw, 0.0, 1.0)
        break

    if slippage_valeur is None:
        return 1.0

    penalite = 1.0 / (1.0 + float(slippage_multiplier) * float(slippage_valeur))
    return clamp(penalite, 0.5, 1.0)


def clamp(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


@lru_cache(maxsize=1)
def _charger_config_v5_5() -> Tuple[Optional[Dict[str, Any]], str]:
    chemin = os.environ.get("DEFIPILOT_STRATEGY_CFG", "config/strategy_v5_5.json")

    chargeur = _recuperer_chargeur_config()
    if chargeur is not None:
        try:
            config = chargeur(chemin)
            if isinstance(config, dict):
                return config, chemin
            return None, chemin
        except Exception as exc:
            LOGGER.debug("Impossible de charger la config V5.5 via loader (%s): %s", chemin, exc)
            return None, chemin

    try:
        with open(chemin, "r", encoding="utf-8") as fichier:
            data = json.load(fichier)
        return data if isinstance(data, dict) else None, chemin
    except Exception as exc:
        LOGGER.debug("Lecture JSON V5.5 impossible (%s): %s", chemin, exc)
        return None, chemin


def _recuperer_chargeur_config() -> Optional[Any]:
    try:
        module = importlib.import_module("core.strategy_config")
        chargeur = getattr(module, "load_strategy_config", None)
        return chargeur if callable(chargeur) else None
    except Exception:
        return None


def _extraire_champ(signal: SignalNormalise, champ: str, default: Any = None) -> Any:
    if isinstance(signal, dict):
        return signal.get(champ, default)

    try:
        return getattr(signal, champ)
    except AttributeError:
        pass

    try:
        return signal[champ]  # type: ignore[index]
    except Exception:
        return default


def _extraire_metric(metrics: Dict[str, Any], noms: set[str]) -> Optional[float]:
    noms_normalises = {nom.lower() for nom in noms}
    for cle, valeur in metrics.items():
        if cle.lower() in noms_normalises and isinstance(valeur, (int, float)):
            return float(valeur)
    return None
