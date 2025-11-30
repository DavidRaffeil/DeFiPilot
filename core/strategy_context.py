# core/strategy_context.py – V5.1.0
"""Gestion du contexte global de stratégie pour DeFiPilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional, Sequence, Literal, cast

from .signals_normalizer import SignalNormalise

ContextLabel = Literal["favorable", "neutre", "defavorable"]


@dataclass
class StrategyContext:
    """Représente le contexte global de stratégie construit à partir des signaux normalisés."""

    timestamp: str
    label: ContextLabel
    ai_score: float
    confiance: float
    resume: str
    metrics: Dict[str, Any]
    nb_signaux: int


def _filtrer_signaux_valides(signaux: Sequence[SignalNormalise]) -> List[SignalNormalise]:
    """Conserve uniquement les signaux compatibles avec le format attendu."""

    signaux_valides: List[SignalNormalise] = []
    for signal in signaux:
        if isinstance(signal, dict):
            signaux_valides.append(signal)
    return signaux_valides


def _extraire_ai_scores(signaux: Sequence[SignalNormalise]) -> List[float]:
    """Extrait les scores IA numériques disponibles dans les signaux."""

    scores: List[float] = []
    for signal in signaux:
        mapping = cast(Dict[str, Any], signal)
        valeur = mapping.get("ai_score")
        if isinstance(valeur, (int, float)):
            scores.append(float(valeur))
    return scores


def _calculer_ai_score_global(scores: Sequence[float]) -> float:
    """Calcule le score global à partir des scores individuels."""

    if scores:
        return float(mean(scores))
    return 0.5


def _determiner_label_brut(ai_score: float) -> ContextLabel:
    """Associe le score global à un label de contexte brut."""

    if ai_score >= 0.6:
        return "favorable"
    if ai_score <= 0.4:
        return "defavorable"
    return "neutre"


def _appliquer_lissage_contexte(
    label_brut: ContextLabel,
    contexte_precedent: Optional[ContextLabel],
    confiance: float,
) -> ContextLabel:
    """Évite les changements brusques de label lorsque la confiance est faible."""

    if (
        contexte_precedent is not None
        and confiance < 0.3
        and label_brut != contexte_precedent
    ):
        return contexte_precedent
    return label_brut


def _generer_resume(label: ContextLabel) -> str:
    """Produit un résumé humain en fonction du label final."""

    if label == "favorable":
        return "La majorité des signaux IA indiquent un contexte favorable pour intensifier l'exposition."
    if label == "defavorable":
        return "Les signaux IA sont majoritairement négatifs, suggérant un environnement risqué."
    return "Les signaux IA sont mitigés ou insuffisants pour dégager une tendance claire."


def _timestamp_utc() -> str:
    """Retourne l'horodatage courant en UTC au format ISO 8601."""

    maintenant = datetime.now(timezone.utc).replace(microsecond=0)
    return maintenant.isoformat().replace("+00:00", "Z")


def construire_contexte_strategie(
    signaux: List[SignalNormalise],
    contexte_precedent: Optional[ContextLabel] = None,
) -> StrategyContext:
    """Construit le contexte global de stratégie à partir des signaux normalisés."""

    signaux_valides = _filtrer_signaux_valides(signaux)
    scores_ai = _extraire_ai_scores(signaux_valides)
    ai_score = _calculer_ai_score_global(scores_ai)
    nb_signaux = len(signaux_valides)
    confiance = min(1.0, nb_signaux / 5.0)

    label_brut = _determiner_label_brut(ai_score)
    label_final = _appliquer_lissage_contexte(label_brut, contexte_precedent, confiance)
    resume = _generer_resume(label_final)
    metrics = {
        "ai_score_moyen": ai_score,
        "nb_signaux": nb_signaux,
        "label_brut": label_brut,
    }

    return StrategyContext(
        timestamp=_timestamp_utc(),
        label=label_final,
        ai_score=ai_score,
        confiance=confiance,
        resume=resume,
        metrics=metrics,
        nb_signaux=nb_signaux,
    )


def est_contexte_favorable(contexte: StrategyContext) -> bool:
    """Indique si le contexte global est considéré comme favorable pour augmenter le risque."""

    return contexte.label == "favorable"
