# core/journal_farming.py – V3.9.0
"""Module de journalisation pour les opérations de farming LP."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

VERSION = "V3.9.0"
CSV_HEADERS = [
    "date",
    "run_id",
    "platform",
    "chain",
    "wallet",
    "action",
    "pool_id",
    "lp_token",
    "lp_decimals",
    "amount_lp_requested",
    "amount_lp_effectif",
    "rewards_token",
    "rewards_amount",
    "tx_status",
    "tx_hash",
    "gas_used",
    "effective_gas_price",
    "tx_cost_native",
    "balances_after_json",
    "dry_run",
    "notes",
    "version",
]
CSV_PATH = Path("journal_farming.csv")
JSONL_PATH = Path("journal_farming.jsonl")

_logger = logging.getLogger(__name__)


def _ensure_csv_ready(path: Path, headers: list[str]) -> None:
    """Garantit que le fichier CSV existe et contient l'en-tête."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)


def _to_json_string(obj: str | dict | None) -> str:
    """Convertit un objet en chaîne JSON compacte selon les règles métiers."""
    if obj is None:
        return "{}"
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        try:
            return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        except TypeError as exc:  # pragma: no cover - sécurise en cas d'objet non sérialisable
            _logger.warning("Impossible de sérialiser balances_after_json: %s", exc)
            return "{}"
    return str(obj)


def _sanitize(value: Any) -> str:
    """Transforme une valeur en chaîne adaptée à l'écriture CSV."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def enregistrer_farming(
    date: str,
    run_id: str,
    platform: str,
    chain: str,
    wallet: str,
    action: str,
    pool_id: int | None,
    lp_token: str | None,
    lp_decimals: int | None,
    amount_lp_requested: float | None,
    amount_lp_effectif: float | None,
    rewards_token: str | None,
    rewards_amount: float | None,
    tx_status: str | None,
    tx_hash: str | None,
    gas_used: int | None,
    effective_gas_price: float | int | None,
    tx_cost_native: float | None,
    balances_after_json: str | dict | None,
    dry_run: bool,
    notes: str = "",
    version: str = VERSION,
) -> dict:
    """Écrit 1 ligne CSV + 1 ligne JSONL. Retourne un dict récapitulatif."""

    try:
        _ensure_csv_ready(CSV_PATH, CSV_HEADERS)
        balances_str = _to_json_string(balances_after_json)
        dry_run_str = "true" if dry_run else "false"
        version_value = version or VERSION

        line_data = {
            "date": _sanitize(date),
            "run_id": _sanitize(run_id),
            "platform": _sanitize(platform),
            "chain": _sanitize(chain),
            "wallet": _sanitize(wallet),
            "action": _sanitize(action),
            "pool_id": _sanitize(pool_id),
            "lp_token": _sanitize(lp_token),
            "lp_decimals": _sanitize(lp_decimals),
            "amount_lp_requested": _sanitize(amount_lp_requested),
            "amount_lp_effectif": _sanitize(amount_lp_effectif),
            "rewards_token": _sanitize(rewards_token),
            "rewards_amount": _sanitize(rewards_amount),
            "tx_status": _sanitize(tx_status),
            "tx_hash": _sanitize(tx_hash),
            "gas_used": _sanitize(gas_used),
            "effective_gas_price": _sanitize(effective_gas_price),
            "tx_cost_native": _sanitize(tx_cost_native),
            "balances_after_json": balances_str,
            "dry_run": dry_run_str,
            "notes": _sanitize(notes),
            "version": _sanitize(version_value),
        }

        with CSV_PATH.open("a", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
            writer.writerow(line_data)

        json_line = {key: line_data[key] for key in CSV_HEADERS}
        JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with JSONL_PATH.open("a", encoding="utf-8") as jsonl_file:
            jsonl_file.write(json.dumps(json_line, ensure_ascii=False) + "\n")

        _logger.info(
            "Journal farming enregistré: action=%s status=%s tx=%s",
            action,
            tx_status,
            tx_hash or "",
        )

        return {
            "success": True,
            "csv_path": str(CSV_PATH),
            "jsonl_path": str(JSONL_PATH),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - gestion globale des erreurs
        _logger.exception("Échec de l'enregistrement du journal farming: %s", exc)
        return {
            "success": False,
            "csv_path": str(CSV_PATH),
            "jsonl_path": str(JSONL_PATH),
            "error": str(exc),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo_result = enregistrer_farming(
        date="2024-01-01T00:00:00Z",
        run_id="demo",
        platform="demo_platform",
        chain="demo_chain",
        wallet="0x0000000000000000000000000000000000000000",
        action="stake",
        pool_id=123,
        lp_token="DEMO-LP",
        lp_decimals=18,
        amount_lp_requested=1.2345,
        amount_lp_effectif=1.2345,
        rewards_token="DEMO",
        rewards_amount=0.1234,
        tx_status="success",
        tx_hash="0xdeadbeef",
        gas_used=21000,
        effective_gas_price=50_000_000_000,
        tx_cost_native=0.00105,
        balances_after_json={"lp": "1.2345"},
        dry_run=True,
        notes="Exemple de journalisation.",
    )
    logging.info("Résultat démonstration: %s", demo_result)