# core/journal.py – V3.8.23
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

# Emplacements des journaux
JOURNAL_LIQUIDITE = Path("journal_liquidite.csv")            # dry-run
JOURNAL_BALANCES_CSV = Path("journal_liquidity_runs.csv")    # post-check balances (CSV)
JOURNAL_BALANCES_JSONL = Path("journal_liquidity_runs.jsonl")# post-check balances (JSONL)


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

    valeurs = {
        "date": resultat.get("date") or datetime.now(timezone.utc).isoformat(),
        "run_id": resultat.get("run_id") or str(uuid4()),
        "platform": resultat.get("platform"),
        "chain": resultat.get("chain"),
        "tokenA": resultat.get("tokenA"),
        "tokenB": resultat.get("tokenB"),
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
            writer.writerow(valeurs)
    except Exception:
        # Non bloquant côté CLI
        pass


def enregistrer_liquidity_csv(ligne: Dict[str, Any]) -> None:
    """Journal CSV pour les opérations RÉELLES (une ligne par événement)."""
    path = Path("journal_liquidity_real.csv")
    entetes = sorted(ligne.keys())
    try:
        fichier_existe = path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=entetes)
            if not fichier_existe:
                writer.writeheader()
            writer.writerow(ligne)
    except Exception:
        pass


def enregistrer_liquidity_jsonl(ligne: Dict[str, Any]) -> None:
    """Journal JSONL pour les opérations RÉELLES (une ligne JSON par événement)."""
    path = Path("journal_liquidity_real.jsonl")
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    except Exception:
        pass


def enregistrer_balances_finales(resultat: Dict[str, Any]) -> None:
    """[V3.8.BALANCE_LOG_1] Journalise les balances finales (CSV + JSONL)."""
    header = [
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
        "tx_status",
        "balance_USDC_after",
        "balance_WETH_after",
        "balance_POL_after",
        "balance_SLP_after",
        "slippage_bps",
    ]

    valeurs = {
        "date": resultat.get("date") or datetime.now(timezone.utc).isoformat(),
        "run_id": resultat.get("run_id") or str(uuid4()),
        "platform": resultat.get("platform"),
        "chain": resultat.get("chain"),
        "tokenA": resultat.get("tokenA_symbol") or resultat.get("tokenA"),
        "tokenB": resultat.get("tokenB_symbol") or resultat.get("tokenB"),
        "amountA": resultat.get("amountA"),
        "amountB": resultat.get("amountB"),
        "amountA_effectif": resultat.get("amountA_effectif"),
        "amountB_effectif": resultat.get("amountB_effectif"),
        "lp_tokens_estimes": resultat.get("lp_tokens_estimes"),
        "slippage_applique_pct": resultat.get("slippage_applique_pct"),
        "ratio_contraint": resultat.get("ratio_contraint"),
        "details": resultat.get("details"),
        "tx_status": resultat.get("tx_status"),
        "balance_USDC_after": resultat.get("balance_USDC_after"),
        "balance_WETH_after": resultat.get("balance_WETH_after"),
        "balance_POL_after": resultat.get("balance_POL_after"),
        "balance_SLP_after": resultat.get("balance_SLP_after"),
        "slippage_bps": resultat.get("slippage_bps"),
    }

    # Écriture CSV (post-check balances)
    try:
        besoin_entete = True
        if JOURNAL_BALANCES_CSV.exists():
            try:
                with JOURNAL_BALANCES_CSV.open("r", newline="", encoding="utf-8") as fr:
                    lecteur = csv.reader(fr)
                    premiere_ligne = next(lecteur, None)
                    besoin_entete = not premiere_ligne
            except Exception:
                besoin_entete = True
        with JOURNAL_BALANCES_CSV.open("a", newline="", encoding="utf-8") as fw:
            writer = csv.DictWriter(fw, fieldnames=header)
            if besoin_entete:
                writer.writeheader()
            writer.writerow(valeurs)
    except Exception:
        pass

    # Écriture JSONL (post-check balances)
    try:
        with JOURNAL_BALANCES_JSONL.open("a", encoding="utf-8") as fj:
            fj.write(json.dumps(valeurs, ensure_ascii=False) + "\n")
    except Exception:
        pass
