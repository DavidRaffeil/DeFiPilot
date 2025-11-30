# control/signals_bridge.py – V5.1.0
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

SignalConsolide = Dict[str, Any]

__all__ = [
    "SignalConsolide",
    "lire_derniers_signaux",
]

_LOGGER = logging.getLogger(__name__)


def _iter_lignes_non_vides_vers_arriere(path: Path) -> Iterable[str]:
    """Itère sur les lignes non vides d'un fichier en partant de la fin.

    Les lignes sont retournées déjà `str.strip()`.
    """
    try:
        with path.open("r", encoding="utf-8") as fichier:
            lignes = [ligne.strip() for ligne in fichier.readlines()]
    except OSError as exc:
        _LOGGER.debug("Impossible de lire le journal %s : %s", path, exc)
        return ()
    return (ligne for ligne in reversed(lignes) if ligne)


def lire_derniers_signaux(
    n: int = 1,
    chemin_journal: str = "journal_signaux.jsonl",
) -> List[SignalConsolide]:
    """
    Lit les n derniers signaux consolidés dans un journal JSONL.

    Les signaux sont retournés du plus récent au plus ancien.
    Les lignes vides ou invalides (JSON corrompu, non dict) sont ignorées.
    Retourne une liste vide si le fichier est introuvable, vide ou inexploitable.
    """
    if n <= 0:
        return []

    chemin = Path(chemin_journal)

    if not chemin.exists() or not chemin.is_file():
        _LOGGER.debug("Journal de signaux introuvable ou invalide: %s", chemin)
        return []

    try:
        if chemin.stat().st_size == 0:
            _LOGGER.debug("Journal de signaux vide: %s", chemin)
            return []
    except OSError as exc:
        _LOGGER.debug("Impossible d'accéder au journal %s : %s", chemin, exc)
        return []

    signaux: List[SignalConsolide] = []
    for ligne in _iter_lignes_non_vides_vers_arriere(chemin):
        try:
            signal = json.loads(ligne)
        except json.JSONDecodeError as exc:
            _LOGGER.debug("Ligne ignorée (JSON invalide) dans %s : %s", chemin, exc)
            continue

        if not isinstance(signal, dict):
            _LOGGER.debug("Ligne ignorée (structure inattendue) dans %s", chemin)
            continue

        signaux.append(signal)
        if len(signaux) >= n:
            break

    return signaux