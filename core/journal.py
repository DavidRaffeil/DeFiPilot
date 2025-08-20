# core/journal.py – V3.8
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

# Emplacement du journal (surchargé dans les tests via monkeypatch)
JOURNAL_LIQUIDITE = Path("journal_liquidite.csv")


def enregistrer_liquidite_dryrun(resultat: Dict[str, Any]) -> None:
    """Enregistre un ajout de liquidité simulé (dry-run) dans un CSV.

    - Crée le fichier avec un en-tête si nécessaire.
    - Ajoute un run_id (UUID4) si absent dans *resultat*.
    - Comportement non bloquant : les erreurs d'I/O sont ignorées.
    """
    entetes = [
        "date",
        "run_id",
        "platform",
        "chain",
        "tokenA",
        "tokenB",
        "amountA",
        "amountB",
        "amountA_effectif",
        "amountB_effectif",
        "lp_tokens_estimes",
        "slippage_applique_pct",
        "ratio_contraint",
        "details",
    ]

    ligne = {
        "date": datetime.now(timezone.utc).isoformat(),
        "run_id": resultat.get("run_id") or str(uuid4()),
        "platform": resultat.get("platform"),
        "chain": resultat.get("chain"),
        "tokenA": resultat.get("tokenA_symbol"),
        "tokenB": resultat.get("tokenB_symbol"),
        "amountA": resultat.get("amountA"),
        "amountB": resultat.get("amountB"),
        "amountA_effectif": resultat.get("amountA_effectif"),
        "amountB_effectif": resultat.get("amountB_effectif"),
        "lp_tokens_estimes": resultat.get("lp_tokens_estimes"),
        "slippage_applique_pct": resultat.get("slippage_applique_pct"),
        "ratio_contraint": resultat.get("ratio_contraint"),
        "details": resultat.get("details"),
    }

    try:
        fichier_existe = JOURNAL_LIQUIDITE.exists()
        with JOURNAL_LIQUIDITE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=entetes)
            if not fichier_existe:
                writer.writeheader()
            writer.writerow(ligne)
    except Exception:
        # Non bloquant côté CLI
        pass
