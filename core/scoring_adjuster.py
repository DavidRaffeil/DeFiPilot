# core/scoring_adjuster.py – V5.1.0
from __future__ import annotations

from dataclasses import dataclass, field
import logging
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


def ajuster_score_pool(
    pool: Dict[str, object],
    score_initial: float,
    signaux: List[SignalNormalise],
    contexte: str,
    retourner_details: bool = False,
) -> float | tuple[float, ScoreDetails]:
    """Ajuste dynamiquement le score d'une pool selon les signaux fournis."""

    coeff_contexte = _calculer_coeff_contexte(contexte)
    coeff_ai, ai_score_moyen = _calculer_coeff_ai(signaux)
    coeff_risque, drapeaux_risque = _evaluer_risque(signaux)

    LOGGER.debug("Contexte '%s' ➜ coeff %.3f", contexte, coeff_contexte)
    LOGGER.debug("Score IA moyen %.3f ➜ coeff %.3f", ai_score_moyen or 0.0, coeff_ai)
    if drapeaux_risque:
        LOGGER.debug(
            "Drapeaux risque %s ➜ coeff %.3f", drapeaux_risque, coeff_risque
        )
    else:
        LOGGER.debug("Aucun drapeau risque ➜ coeff %.3f", coeff_risque)

    # Calcul du score ajusté sans plafonner artificiellement à 10,
    # mais en évitant les valeurs négatives.
    score_intermediaire = score_initial * coeff_contexte * coeff_ai * coeff_risque
    if score_intermediaire < 0:
        score_final = 0.0
    else:
        score_final = score_intermediaire

    if retourner_details:
        LOGGER.info(
            "Ajustement pool %s (%s) : %.2f ➜ %.2f",
            pool.get("id", "inconnu"),
            contexte,
            score_initial,
            score_final,
        )
        details = ScoreDetails(
            score_initial=score_initial,
            score_final=score_final,
            coeff_contexte=coeff_contexte,
            coeff_ai=coeff_ai,
            coeff_risque=coeff_risque,
            contexte=contexte,
            ai_score_moyen=ai_score_moyen,
            drapeaux_risque=drapeaux_risque,
        )
        return score_final, details

    return score_final



def _calculer_coeff_contexte(contexte: str) -> float:
    """Calcule le coefficient global selon le contexte de marché."""

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
    """Calcule le coefficient lié aux scores IA des signaux."""

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
    """Analyse les métriques des signaux pour déduire un coefficient de risque."""

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


def _calculer_coeff_risque(signaux: List[SignalNormalise]) -> float:
    """Retourne seulement le coefficient de risque agrégé."""

    coeff, _ = _evaluer_risque(signaux)
    return coeff


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Borne une valeur dans l'intervalle [minimum, maximum]."""

    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def _extraire_champ(signal: SignalNormalise, champ: str, default: Any = None) -> Any:
    """Récupère un champ depuis un signal, quel que soit son format."""

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
    """Extrait une métrique en tenant compte des variations de casse."""

    noms_normalises = {nom.lower() for nom in noms}
    for cle, valeur in metrics.items():
        if cle.lower() in noms_normalises and isinstance(valeur, (int, float)):
            return float(valeur)
    return None