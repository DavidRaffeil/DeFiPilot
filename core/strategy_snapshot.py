# core/strategy_snapshot.py — V6.0.1

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_DECISIONS_JOURNAL_PATH = Path("data/logs/journal_decisions.jsonl")

StrategySnapshot = Dict[str, Any]


def lire_dernier_snapshot(
    path: Path = DEFAULT_DECISIONS_JOURNAL_PATH,
) -> Optional[StrategySnapshot]:
    """
    Lit le journal JSONL des décisions et retourne le dernier objet JSON valide.

    - Si le fichier n'existe pas → None
    - Ignore les lignes invalides
    - Ne lève jamais d'exception
    """
    if not path.exists() or not path.is_file():
        return None

    dernier_snapshot: Optional[StrategySnapshot] = None

    try:
        with path.open("r", encoding="utf-8") as f:
            for ligne in f:
                raw = ligne.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    dernier_snapshot = payload
    except OSError:
        return None

    return dernier_snapshot


def journaliser_decision(
    snapshot: Optional[StrategySnapshot],
    path: Path = DEFAULT_DECISIONS_JOURNAL_PATH,
) -> None:
    if snapshot is None:
        return

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    try:
        with path.open("a", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False)
            f.write("\n")
    except OSError:
        return


__all__ = ["journaliser_decision", "lire_dernier_snapshot"]
