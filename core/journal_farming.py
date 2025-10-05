# core/journal_farming.py – V3.9.4
"""Journalisation unifiée (CSV + JSONL) des opérations de farming LP.

Exigences clés (rappel):
- Schéma final UNIQUE (22 champs) pour CSV et JSONL, même ordre.
- Réécriture automatique de l'en-tête CSV si absent/incorrect (sans réécrire l'historique des lignes).
- Compat historique : accepter `pid` en argument mais ne journaliser que `pool_id`.
- `balances_after_json` toujours sérialisé en chaîne JSON compacte (CSV et JSONL).
- `dry_run` écrit en 'true'/'false' (CSV), bool natif (JSONL).
- Fichier complet, propre, ≤ 2 erreurs.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

VERSION = "V3.9.4"

CSV_HEADERS = [
    "date",                    # 1
    "run_id",                  # 2
    "platform",                # 3
    "chain",                   # 4
    "wallet",                  # 5
    "action",                  # 6
    "pool_id",                 # 7 (remplace définitivement pid)
    "lp_token",                # 8
    "lp_decimals",             # 9
    "amount_lp_requested",     # 10
    "amount_lp_effectif",      # 11
    "rewards_token",           # 12
    "rewards_amount",          # 13
    "tx_status",               # 14
    "tx_hash",                 # 15
    "gas_used",                # 16
    "effective_gas_price",     # 17
    "tx_cost_native",          # 18
    "balances_after_json",     # 19 (chaîne JSON compacte)
    "dry_run",                 # 20 ('true'/'false' pour CSV)
    "notes",                   # 21
    "version",                 # 22
]

CSV_PATH = Path("journal_farming.csv")
JSONL_PATH = Path("journal_farming.jsonl")

_logger = logging.getLogger(__name__)


def _ensure_csv_header(path: Path, headers: list[str]) -> None:
    """Garantit un en-tête CSV conforme (22 colonnes), sans toucher à l'historique.

    - Si le fichier n'existe pas ou est vide → créer l'en-tête.
    - Si le premier enregistrement ne correspond pas à `headers` → réécrire l'en-tête
      puis ré-apposer le reste des lignes existantes inchangées.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(headers)
        return

    # Lire le fichier existant
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(headers)
        return

    # Comparer le header existant
    reader = csv.reader([lines[0]])
    existing_header = next(reader, [])

    if existing_header == headers:
        return  # conforme → rien à faire

    # Réécrire l'en-tête en conservant l'historique (lignes > 0)
    with path.open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(headers)
        if len(lines) > 1:
            f.write("".join(lines[1:]))
    _logger.info("En-tête CSV mis à jour pour %s (colonnes=%d)", path, len(headers))


def _to_json_string(obj: Any) -> str:
    """Sérialise `balances_after_json` en chaîne JSON compacte.

    - None → "{}"
    - str → renvoyée telle quelle
    - dict/obj → json.dumps(..., separators=(",", ":")) ou "{}" en cas d'échec
    """
    if obj is None:
        return "{}"
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except TypeError as exc:  # sécurise en cas d'objet non sérialisable
        _logger.warning("Impossible de sérialiser balances_after_json: %s", exc)
        return "{}"


def _sanitize(value: Any) -> str:
    """Normalise une valeur en chaîne pour le CSV (évite formats locaux)."""
    if value is None:
        return ""
    if isinstance(value, float):
        return repr(value)  # conserve la précision, séparateur '.'
    return str(value)


def _string_or_empty(value: Any) -> str:
    return "" if value is None else str(value)


def _resolve_pool_id(pool_id: Any, pid: Any) -> str:
    """Compat historique pid → pool_id (priorité à pool_id)."""
    if pool_id not in (None, ""):
        return str(pool_id)
    if pid not in (None, ""):
        return str(pid)
    return ""


def enregistrer_farming(
    *,
    date: str,
    run_id: str,
    platform: str,
    chain: str,
    wallet: str,
    action: str,
    pool_id: int | str | None,
    lp_token: str | None,
    lp_decimals: int | str | None,
    amount_lp_requested: float | int | str | None,
    amount_lp_effectif: float | int | str | None,
    rewards_token: str | None,
    rewards_amount: float | int | str | None,
    tx_status: str | None,
    tx_hash: str | None,
    gas_used: int | None,
    effective_gas_price: float | int | None,
    tx_cost_native: float | int | None,
    balances_after_json: Any,
    dry_run: bool,
    notes: str = "",
    version: str = VERSION,
    # compat
    pid: int | str | None = None,
) -> dict:
    """Écrit 1 ligne CSV + 1 ligne JSONL et retourne un petit récap.

    Cette fonction est conçue pour être appelée par le code existant (CLI / core.farming_*).
    La signature conserve une compat minimale via `pid` (remappé vers `pool_id`).
    """
    try:
        # Préparer données normalisées
        resolved_pool_id = _resolve_pool_id(pool_id, pid)
        balances_str = _to_json_string(balances_after_json)
        dry_run_str = "true" if dry_run else "false"
        version_value = version or VERSION

        # Dictionnaire JSONL (22 clés, types natifs sauf balances_after_json en str)
        json_line: dict[str, Any] = {
            "date": _string_or_empty(date),
            "run_id": _string_or_empty(run_id),
            "platform": _string_or_empty(platform),
            "chain": _string_or_empty(chain),
            "wallet": _string_or_empty(wallet),
            "action": _string_or_empty(action),
            "pool_id": _string_or_empty(resolved_pool_id),
            "lp_token": _string_or_empty(lp_token),
            "lp_decimals": lp_decimals,
            "amount_lp_requested": amount_lp_requested,
            "amount_lp_effectif": amount_lp_effectif,
            "rewards_token": _string_or_empty(rewards_token),
            "rewards_amount": rewards_amount,
            "tx_status": _string_or_empty(tx_status),
            "tx_hash": _string_or_empty(tx_hash),
            "gas_used": gas_used,
            "effective_gas_price": effective_gas_price,
            "tx_cost_native": tx_cost_native,
            "balances_after_json": balances_str,  # string compact
            "dry_run": bool(dry_run),
            "notes": _string_or_empty(notes),
            "version": _string_or_empty(version_value),
        }

        # Rangée CSV alignée avec le même ordre (22 colonnes, tout en str)
        csv_row: dict[str, str] = {
            "date": _sanitize(json_line["date"]),
            "run_id": _sanitize(json_line["run_id"]),
            "platform": _sanitize(json_line["platform"]),
            "chain": _sanitize(json_line["chain"]),
            "wallet": _sanitize(json_line["wallet"]),
            "action": _sanitize(json_line["action"]),
            "pool_id": _sanitize(json_line["pool_id"]),
            "lp_token": _sanitize(json_line["lp_token"]),
            "lp_decimals": _sanitize(json_line["lp_decimals"]),
            "amount_lp_requested": _sanitize(json_line["amount_lp_requested"]),
            "amount_lp_effectif": _sanitize(json_line["amount_lp_effectif"]),
            "rewards_token": _sanitize(json_line["rewards_token"]),
            "rewards_amount": _sanitize(json_line["rewards_amount"]),
            "tx_status": _sanitize(json_line["tx_status"]),
            "tx_hash": _sanitize(json_line["tx_hash"]),
            "gas_used": _sanitize(json_line["gas_used"]),
            "effective_gas_price": _sanitize(json_line["effective_gas_price"]),
            "tx_cost_native": _sanitize(json_line["tx_cost_native"]),
            "balances_after_json": _sanitize(json_line["balances_after_json"]),
            "dry_run": dry_run_str,
            "notes": _sanitize(json_line["notes"]),
            "version": _sanitize(json_line["version"]),
        }

        # Assurer un en-tête correct puis écrire
        _ensure_csv_header(CSV_PATH, CSV_HEADERS)
        with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writerow(csv_row)

        JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with JSONL_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(json_line, ensure_ascii=False, separators=(",", ":")) + "\n")

        _logger.info(
            "Journal farming enregistré: action=%s status=%s tx=%s",
            json_line["action"],
            json_line["tx_status"],
            json_line["tx_hash"],
        )

        return {
            "success": True,
            "csv_path": str(CSV_PATH),
            "jsonl_path": str(JSONL_PATH),
            "error": None,
        }

    except Exception as exc:  # gestion globale des erreurs
        _logger.exception("Échec de l'enregistrement du journal farming: %s", exc)
        return {
            "success": False,
            "csv_path": str(CSV_PATH),
            "jsonl_path": str(JSONL_PATH),
            "error": str(exc),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = enregistrer_farming(
        date="2025-01-01T00:00:00Z",
        run_id="demo",
        platform="demo_platform",
        chain="demo_chain",
        wallet="0x0000000000000000000000000000000000000000",
        action="stake",
        pool_id=1,
        lp_token="DEMO-LP",
        lp_decimals=18,
        amount_lp_requested=1.0,
        amount_lp_effectif=1.0,
        rewards_token="DEMO",
        rewards_amount=0.1234,
        tx_status="dryrun",
        tx_hash="",
        gas_used=21000,
        effective_gas_price=50_000_000_000,
        tx_cost_native=0.00105,
        balances_after_json={"lp": 1.0},
        dry_run=True,
        notes="exemple",
        version=VERSION,
    )
    logging.info("Résultat démonstration: %s", demo)
