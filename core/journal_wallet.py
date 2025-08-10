# core/journal_wallet.py – V3.5  ← (en-tête OBLIGATOIRE)
"""Module de journalisation des actions et des soldes du wallet.

Ce module enregistre les actions effectuées par un wallet et les
instantanés de ses soldes dans des fichiers CSV. Les fichiers sont
créés automatiquement avec leurs en-têtes et les horodatages sont en UTC.
"""

from __future__ import annotations

from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from typing import Any
import logging

logger = logging.getLogger(__name__)

LOG_DIR = Path("logs")
ACTIONS_CSV = LOG_DIR / "journal_wallet_actions.csv"
BALANCES_CSV = LOG_DIR / "journal_wallet_balances.csv"

ACTIONS_HEADER = [
    "date_iso",
    "timestamp",
    "action",
    "token_in",
    "amount_in",
    "token_out",
    "amount_out",
    "fee_usdc",
    "tx_hash",
    "notes",
]

BALANCES_HEADER = [
    "date_iso",
    "timestamp",
    "wallet",
    "chain",
    "balances_json",
    "notes",
]

def _ensure_dir(p: Path) -> None:
    """Crée le dossier ``p`` s'il n'existe pas."""
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception("Erreur lors de la création du dossier %s", p)


def _ensure_csv_with_header(path: Path, header: list[str]) -> None:
    """Crée le fichier CSV avec en-tête s'il est absent."""
    try:
        _ensure_dir(path.parent)
        if not path.exists() or path.stat().st_size == 0:
            with path.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)
    except Exception:
        logger.exception("Impossible d'initialiser le fichier %s", path)


def _utc_now_fields() -> tuple[str, int]:
    """Retourne la date ISO et le timestamp UTC actuel."""
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp = int(now.timestamp())
    return date_iso, timestamp


def _safe_float(x: Any) -> float | None:
    """Convertit ``x`` en float si possible, sinon ``None``."""
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def init_logs() -> None:
    """Initialise les fichiers de journalisation."""
    _ensure_csv_with_header(ACTIONS_CSV, ACTIONS_HEADER)
    _ensure_csv_with_header(BALANCES_CSV, BALANCES_HEADER)


def log_wallet_action(
    *,
    action: str,
    token_in: str | None = None,
    amount_in: float | None = None,
    token_out: str | None = None,
    amount_out: float | None = None,
    fee_usdc: float | None = None,
    tx_hash: str | None = None,
    notes: str | None = None,
) -> None:
    """Journalise une action du wallet."""
    if not action:
        logger.error("Action manquante pour le journal")
        return
    try:
        _ensure_csv_with_header(ACTIONS_CSV, ACTIONS_HEADER)
        date_iso, timestamp = _utc_now_fields()
        amount_in_f = _safe_float(amount_in)
        amount_out_f = _safe_float(amount_out)
        fee_usdc_f = _safe_float(fee_usdc)
        clean_notes = notes.replace("\n", " ") if notes else ""
        row = [
            date_iso,
            timestamp,
            action,
            token_in or "",
            amount_in_f if amount_in_f is not None else "",
            token_out or "",
            amount_out_f if amount_out_f is not None else "",
            fee_usdc_f if fee_usdc_f is not None else "",
            tx_hash or "",
            clean_notes,
        ]
        with ACTIONS_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception:
        logger.exception("Erreur lors de la journalisation de l'action")


def log_wallet_balance(
    *,
    wallet: str,
    chain: str,
    balances: dict[str, float],
    notes: str | None = None,
) -> None:
    """Journalise un instantané de soldes du wallet."""
    if not wallet or not chain:
        logger.error("Wallet ou chaîne manquant pour le journal")
        return
    try:
        _ensure_csv_with_header(BALANCES_CSV, BALANCES_HEADER)
        date_iso, timestamp = _utc_now_fields()
        balances_json = json.dumps(balances, ensure_ascii=False, separators=(",", ":"))
        clean_notes = notes.replace("\n", " ") if notes else ""
        row = [date_iso, timestamp, wallet, chain, balances_json, clean_notes]
        with BALANCES_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
    except Exception:
        logger.exception("Erreur lors de la journalisation du solde")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_logs()
    log_wallet_action(action="approve", token_in="USDC", notes="dryrun")
    log_wallet_balance(
        wallet="0xDEMO",
        chain="polygon",
        balances={"USDC": 123.45, "ETH": 0.001},
        notes="après approve",
    )