# core/signals_normalizer.py – V5.1.0
"""Outils de normalisation des signaux consolidés."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, TypedDict


class SignalNormalise(TypedDict, total=False):
    """Représente un signal consolidé normalisé et exploitable par la stratégie."""

    timestamp: str
    context_label: str
    metrics: Dict[str, Any]
    ai_score: float


__all__ = ["SignalNormalise", "normaliser_signaux"]


def normaliser_signaux(signaux_bruts: List[Dict[str, Any]]) -> List[SignalNormalise]:
    """Convertit une liste de signaux bruts (dict) en liste de signaux normalisés.

    La fonction :
    - ignore les entrées non dict ou vides,
    - tente d'extraire un horodatage, un label de contexte et un score IA,
    - isole un dictionnaire de métriques numériques utiles (APR, TVL, etc.),
    - retourne uniquement les signaux pour lesquels au moins une de ces
      informations est disponible.
    """

    signaux_normalises: List[SignalNormalise] = []

    for signal in signaux_bruts:
        if not isinstance(signal, dict):
            continue

        timestamp = _extraire_timestamp(signal)
        context_label = _extraire_context_label(signal)
        ai_score = _extraire_ai_score(signal)
        metrics = _extraire_metrics(signal)

        if (
            timestamp is None
            and context_label is None
            and not metrics
            and ai_score is None
        ):
            continue

        signal_norm: SignalNormalise = {}
        if timestamp:
            signal_norm["timestamp"] = timestamp
        if context_label:
            signal_norm["context_label"] = context_label
        if ai_score is not None:
            signal_norm["ai_score"] = ai_score
        if metrics:
            signal_norm["metrics"] = metrics

        signaux_normalises.append(signal_norm)

    return signaux_normalises


def _extraire_timestamp(signal: Dict[str, Any]) -> Optional[str]:
    for cle in ("timestamp", "ts"):
        texte = signal.get(cle)
        if isinstance(texte, str):
            valeur = texte.strip()
        elif texte is None:
            continue
        else:
            valeur = str(texte).strip()
        if valeur:
            return valeur
    return None


def _extraire_context_label(signal: Dict[str, Any]) -> Optional[str]:
    for cle in ("AI_context", "context", "contexte"):
        label = _normaliser_label_contexte(signal.get(cle))
        if label:
            return label
    return None


def _extraire_ai_score(signal: Dict[str, Any]) -> Optional[float]:
    for cle in ("AI_confidence", "context_score"):
        valeur = signal.get(cle)
        score = _convertir_float(valeur)
        if score is not None:
            return score
    return None


def _extraire_metrics(signal: Dict[str, Any]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    cles_prioritaires = (
        "APR",
        "apr",
        "APY",
        "apy",
        "TVL",
        "tvl",
        "tvl_usd",
        "volatilite",
        "volatility",
        "volume",
        "fees",
        "liquidity",
        "utilization",
    )

    for cle in cles_prioritaires:
        if cle in signal and signal[cle] is not None:
            metrics[cle] = signal[cle]

    for cle, valeur in signal.items():
        if cle in metrics:
            continue
        if _est_nombre(valeur):
            metrics[cle] = valeur

    return metrics


def _normaliser_label_contexte(brut: Any) -> Optional[str]:
    """Normalise une valeur brute de contexte vers une forme standardisée."""

    texte = _nettoyer_str(brut)
    if not texte:
        return None

    mapping_favorable = {"favorable", "bull", "bullish", "positif"}
    mapping_neutre = {"neutre", "neutral", "flat"}
    mapping_defavorable = {
        "defavorable",
        "défavorable",
        "unfavorable",
        "bear",
        "bearish",
        "negatif",
        "négatif",
    }

    if texte in mapping_favorable:
        return "favorable"
    if texte in mapping_neutre:
        return "neutre"
    if texte in mapping_defavorable:
        return "defavorable"
    return None


def _convertir_float(valeur: Any) -> Optional[float]:
    if valeur is None or isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        resultat = float(valeur)
    else:
        texte = _nettoyer_str(valeur)
        if not texte:
            return None
        try:
            resultat = float(texte)
        except (TypeError, ValueError):
            return None
    if not math.isfinite(resultat):
        return None
    return resultat


def _est_nombre(valeur: Any) -> bool:
    if isinstance(valeur, bool):
        return False
    if isinstance(valeur, int):
        return True
    if isinstance(valeur, float):
        return math.isfinite(valeur)
    return False


def _nettoyer_str(valeur: Any) -> Optional[str]:
    if valeur is None:
        return None
    if isinstance(valeur, str):
        texte = valeur.strip().lower()
    else:
        texte = str(valeur).strip().lower()
    return texte or None