# control/context_bridge.py – V5.1.0
"""Pont de lecture pour le contexte IA issu du journal ControlPilot."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Iterator, Literal, Optional, TypedDict

ContexteLabel = Literal["favorable", "neutre", "defavorable"]


class ContextSnapshot(TypedDict, total=False):
    """Représentation normalisée d'un contexte IA provenant du journal."""

    context_label: ContexteLabel
    context_score: float
    source: str
    timestamp: str


__all__ = [
    "ContexteLabel",
    "ContextSnapshot",
    "lire_derniere_context_snapshot",
]

_LOGGER = logging.getLogger(__name__)


def _iter_lignes_non_vides_vers_arriere(path: Path) -> Iterator[str]:
    """Retourne les lignes non vides du fichier en partant de la fin."""

    try:
        with path.open("r", encoding="utf-8") as fichier:
            lignes = fichier.readlines()
    except OSError as exc:  # pragma: no cover - dépend du système de fichiers
        _LOGGER.debug("Impossible de lire le journal %s : %s", path, exc)
        return iter(())

    return (ligne for ligne in reversed([l.strip() for l in lignes]) if ligne)


def _normaliser_label_contexte(brut: str) -> Optional[ContexteLabel]:
    """Normalise un libellé quelconque vers un label de contexte officiel."""

    if not brut:
        return None

    valeur = brut.strip().lower()
    mapping = {
        "favorable": "favorable",
        "favori": "favorable",
        "positif": "favorable",
        "bull": "favorable",
        "bullish": "favorable",
        "neutre": "neutre",
        "neutral": "neutre",
        "flat": "neutre",
        "defavorable": "defavorable",
        "défavorable": "defavorable",
        "negatif": "defavorable",
        "négatif": "defavorable",
        "bear": "defavorable",
        "bearish": "defavorable",
        "unfavorable": "defavorable",
    }

    return mapping.get(valeur)


def _extraire_score(data: dict[str, object]) -> Optional[float]:
    """Extrait un score de confiance numérique si présent."""

    for cle in ("AI_confidence", "context_score"):
        if cle not in data:
            continue
        valeur = data.get(cle)
        try:
            score = float(valeur)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if math.isnan(score) or math.isinf(score):
            continue
        return score
    return None


def _extraire_timestamp(data: dict[str, object]) -> Optional[str]:
    """Retourne un horodatage s'il est présent dans les champs attendus."""

    for cle in ("timestamp", "ts"):
        brut = data.get(cle)
        if isinstance(brut, str) and brut.strip():
            return brut.strip()
    return None


def lire_derniere_context_snapshot(
    chemin_journal: str = "journal_control.jsonl",
) -> Optional[ContextSnapshot]:
    """Lit le dernier enregistrement valide de contexte IA dans un journal JSONL."""

    path = Path(chemin_journal)
    try:
        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            return None
    except OSError as exc:  # pragma: no cover - dépend du système de fichiers
        _LOGGER.debug("Impossible de stat le journal %s : %s", path, exc)
        return None

    for ligne in _iter_lignes_non_vides_vers_arriere(path):
        try:
            donnees = json.loads(ligne)
        except json.JSONDecodeError:
            continue
        if not isinstance(donnees, dict):
            continue

        brut = None
        for cle in ("AI_context", "context", "contexte"):
            valeur = donnees.get(cle)
            if isinstance(valeur, str) and valeur.strip():
                brut = valeur
                break
        if brut is None:
            continue

        label = _normaliser_label_contexte(brut)
        if label is None:
            continue

        snapshot: ContextSnapshot = {
            "context_label": label,
            "source": "controlpilot",
        }

        score = _extraire_score(donnees)
        if score is not None:
            snapshot["context_score"] = score

        horodatage = _extraire_timestamp(donnees)
        if horodatage is not None:
            snapshot["timestamp"] = horodatage

        return snapshot

    return None
