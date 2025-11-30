# core/context_provider.py – V5.1.0
from __future__ import annotations

from typing import Any, Dict, Literal, Mapping, Optional, TypedDict, cast

from control.context_bridge import (
    ContexteLabel,
    ContextSnapshot,
    lire_derniere_context_snapshot,
)

SourceContexte = Literal["controlpilot", "state", "default"]


class ContexteActuel(TypedDict, total=False):
    """Représente le contexte de marché effectivement utilisé par DeFiPilot."""

    contexte: ContexteLabel
    source: SourceContexte
    score: Optional[float]
    timestamp: Optional[str]


__all__ = [
    "ContexteActuel",
    "SourceContexte",
    "obtenir_contexte_actuel",
]

_LABELS_AUTORISES: tuple[ContexteLabel, ...] = ("favorable", "neutre", "defavorable")


def obtenir_contexte_actuel(
    etat_precedent: Optional[Mapping[str, Any]] = None,
    chemin_journal_control: str = "journal_control.jsonl",
) -> ContexteActuel:
    """Retourne le contexte de marché actuel utilisé par DeFiPilot.

    Priorité :
      1) contexte provenant de ControlPilot (journal_control.jsonl),
      2) contexte stocké dans l'état précédent,
      3) contexte par défaut "neutre".

    Cette fonction ne modifie pas l'état et ne l'enregistre pas.
    """

    snapshot = lire_derniere_context_snapshot(chemin_journal_control)
    contexte_control = _extraire_contexte_control(snapshot)
    if contexte_control is not None:
        return contexte_control

    if etat_precedent is not None and isinstance(etat_precedent, Mapping):
        label_state = _extraire_contexte_depuis_state(etat_precedent)
        if label_state is not None:
            return _construire_contexte_actuel(label_state, "state")

    return _construire_contexte_actuel("neutre", "default")


def _extraire_contexte_control(
    snapshot: Optional[ContextSnapshot],
) -> Optional[ContexteActuel]:
    """Normalise le snapshot issu de ControlPilot si possible."""

    if not snapshot:
        return None

    label_brut = snapshot.get("context_label")
    label = _valider_contexte_label(label_brut)
    if label is None:
        return None

    score = _convertir_score(snapshot.get("context_score"))
    timestamp = _normaliser_timestamp(snapshot.get("timestamp"))
    return _construire_contexte_actuel(label, "controlpilot", score, timestamp)


def _extraire_contexte_depuis_state(
    etat_precedent: Mapping[str, Any]
) -> Optional[ContexteLabel]:
    """Tente de récupérer un label valide depuis l'état précédent."""

    for cle in ("contexte_marche", "contexte"):
        valeur = etat_precedent.get(cle)
        label = _valider_contexte_label(valeur)
        if label is not None:
            return label
    return None


def _valider_contexte_label(valeur: Any) -> Optional[ContexteLabel]:
    """Valide et normalise un label de contexte brut."""

    if not isinstance(valeur, str):
        return None

    normalise = valeur.strip().lower()
    if not normalise:
        return None

    if normalise in _LABELS_AUTORISES:
        return cast(ContexteLabel, normalise)
    return None


def _convertir_score(valeur: Any) -> Optional[float]:
    """Convertit un score éventuel en float si possible."""

    if isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        return float(valeur)
    return None


def _normaliser_timestamp(valeur: Any) -> Optional[str]:
    """Nettoie le timestamp fourni par ControlPilot."""

    if isinstance(valeur, str):
        nettoye = valeur.strip()
        if nettoye:
            return nettoye
    return None


def _construire_contexte_actuel(
    label: ContexteLabel,
    source: SourceContexte,
    score: Optional[float] = None,
    timestamp: Optional[str] = None,
) -> ContexteActuel:
    """Assemble la structure ContexteActuel en appliquant les champs optionnels."""

    contexte: Dict[str, Any] = {
        "contexte": label,
        "source": source,
    }
    if score is not None:
        contexte["score"] = score
    if timestamp is not None:
        contexte["timestamp"] = timestamp
    return cast(ContexteActuel, contexte)