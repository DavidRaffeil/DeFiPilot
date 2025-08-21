# core/journal.py – V3.8
# Logs add_liquidity : schéma CSV figé + fonction dry-run alignée

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from uuid import uuid4

# Emplacement du journal (surchargé dans les tests via monkeypatch)
JOURNAL_LIQUIDITE = Path("journal_liquidite.csv")

# --- Schéma figé pour add_liquidity (ordre & casse stricts) ---
CSV_COLUMNS: List[str] = [
    "timestamp_iso", "run_id", "mode", "chain", "platform", "pool_address",
    "tokenA_symbol", "tokenB_symbol", "tokenA_address", "tokenB_address",
    "amountA_in", "amountB_in", "amountA_used", "amountB_used",
    "expected_priceA", "expected_priceB",
    "slippage_bps", "gas_estimate", "router_address",
    "lp_token_address", "lp_amount", "tx_hash", "status", "notes"
]

# JSONL utilisera les mêmes clés que CSV + champs d'erreurs si besoin
JSONL_KEYS = CSV_COLUMNS + ["error_code", "error_message"]


def enregistrer_liquidite_dryrun(resultat: Dict[str, Any]) -> None:
    """Enregistre un ajout de liquidité simulé (dry-run) selon le schéma CSV_COLUMNS.
    - Crée le fichier + en-tête si nécessaire.
    - Ajoute un run_id si absent.
    - Non-bloquant en cas d'erreur I/O.
    """
    run_id = resultat.get("run_id") or str(uuid4())

    # Conversion slippage: pourcentage → basis points (ex: 0.5 -> 50 bps)
    slippage_pct = resultat.get("slippage_applique_pct", 0)
    try:
        slippage_bps = int(round(float(slippage_pct) * 100))
    except Exception:
        slippage_bps = ""

    ligne = {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "mode": "dryrun",
        "chain": resultat.get("chain", ""),
        "platform": resultat.get("platform", ""),
        "pool_address": resultat.get("pool_address", ""),
        "tokenA_symbol": resultat.get("tokenA_symbol", ""),
        "tokenB_symbol": resultat.get("tokenB_symbol", ""),
        "tokenA_address": resultat.get("tokenA_address", ""),
        "tokenB_address": resultat.get("tokenB_address", ""),
        "amountA_in": resultat.get("amountA", ""),
        "amountB_in": resultat.get("amountB", ""),
        "amountA_used": resultat.get("amountA_effectif", ""),
        "amountB_used": resultat.get("amountB_effectif", ""),
        "expected_priceA": resultat.get("expected_priceA", ""),
        "expected_priceB": resultat.get("expected_priceB", ""),
        "slippage_bps": slippage_bps,
        "gas_estimate": resultat.get("gas_estimate", ""),
        "router_address": resultat.get("router_address", ""),
        "lp_token_address": resultat.get("lp_token_address", ""),
        "lp_amount": resultat.get("lp_tokens_estimes", ""),
        "tx_hash": "",
        "status": "dryrun",
        "notes": resultat.get("details", ""),
    }

    try:
        fichier_existe = JOURNAL_LIQUIDITE.exists()
        with JOURNAL_LIQUIDITE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not fichier_existe:
                writer.writeheader()
            writer.writerow({k: ligne.get(k, "") for k in CSV_COLUMNS})
    except Exception:
        # Non bloquant côté CLI
        pass
