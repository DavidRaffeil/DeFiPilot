# core/journal_swaps.py - V3.7
"""Swap events CSV logger / Journal CSV des swaps."""

import csv
from pathlib import Path

_LOG_DIR = Path("logs")
_LOG_FILE = _LOG_DIR / "swaps.csv"

_HEADERS = [
    "timestamp_iso",
    "network",
    "dex",
    "status",
    "token_in",
    "token_out",
    "amount_in_wei",
    "amount_out_min_wei",
    "slippage_bps",
    "recipient",
    "tx_hash",
]

def _ensure_file() -> None:
    """Create log dir/file if missing / Crée dossier/fichier de log si absent."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not _LOG_FILE.exists():
        with _LOG_FILE.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(list(_HEADERS))

def log_swap_event(event: dict, status: str, *, timestamp_iso: str) -> None:
    """Append swap event to CSV log / Ajoute un swap au journal CSV."""
    _ensure_file()
    path = event.get("path")
    token_in = path[0] if path else event.get("token_in", "")
    token_out = path[-1] if path else event.get("token_out", "")
    row = [
        timestamp_iso,
        event.get("network", ""),
        event.get("dex", ""),
        status,
        token_in,
        token_out,
        event.get("amount_in_wei", ""),
        event.get("amount_out_min_wei", ""),
        event.get("slippage_bps", ""),
        event.get("recipient", ""),
        event.get("tx_hash", ""),
    ]
    with _LOG_FILE.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(row)