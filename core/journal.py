# core/journal.py — V4.6.1
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def journaliser_rebalancing(plan: dict[str, Any], chemin_journal: str | Path) -> None:
    """Enregistre un plan de rééquilibrage dans un fichier JSONL.

    Args:
        plan (dict[str, Any]): Le plan de rééquilibrage généré par
            ``calculer_plan_rebalancing(...)``.
        chemin_journal (str | Path): Le chemin vers le fichier de journal à
            compléter.

    Le plan est sérialisé en JSON compact (une ligne par plan) puis écrit dans le
    fichier indiqué. Aucune autre ressource n'est modifiée et la fonction ne
    retourne rien.
    """

    journal_path = Path(chemin_journal)
    ligne = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))

    with journal_path.open("a", encoding="utf-8") as flux:
        flux.write(ligne)
        flux.write("\n")
