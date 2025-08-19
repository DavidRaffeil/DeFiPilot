# core/journal.py – V3.8
import csv
import json
import os
from pathlib import Path
from typing import Dict, Any

from core.config import JOURNAL_LIQUIDITY_CSV, JOURNAL_LIQUIDITY_JSONL

CSV_HEADER = ["date_iso","version","chain","platform","router","tokenA","tokenB","amountA_in","amountB_in","amountAMin","amountBMin","slippage","deadline_ts","dry_run","approvals_done","tx_hash","tx_status","gas_used","lp_tokens_received","wallet","error"]

DEFAULTS: Dict[str, Any] = {
    "date_iso": "",
    "version": "",
    "chain": "",
    "platform": "",
    "router": "",
    "tokenA": "",
    "tokenB": "",
    "amountA_in": 0.0,
    "amountB_in": 0.0,
    "amountAMin": 0.0,
    "amountBMin": 0.0,
    "slippage": 0.0,
    "deadline_ts": 0,
    "dry_run": False,
    "approvals_done": "none",  # <- corrigé (string, pas bool)
    "tx_hash": "",
    "tx_status": "",
    "gas_used": 0,
    "lp_tokens_received": 0.0,
    "wallet": "",
    "error": ""
}

def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def _safe_get(d: Dict[str, Any], key: str, default: Any) -> Any:
    value = d.get(key, default)
    if isinstance(default, bool):
        return "true" if bool(value) else "false"
    if isinstance(default, int) and not isinstance(default, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    if isinstance(default, float):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if value is None:
        return ""
    return str(value)

def enregistrer_liquidity_csv(d: Dict[str, Any]) -> None:
    try:
        path = Path(JOURNAL_LIQUIDITY_CSV)
        _ensure_parent(path)
        file_exists = path.is_file()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(CSV_HEADER)
            row = [_safe_get(d, key, DEFAULTS[key]) for key in CSV_HEADER]
            writer.writerow(row)
    except Exception:
        pass

def enregistrer_liquidity_jsonl(d: Dict[str, Any]) -> None:
    try:
        path = Path(JOURNAL_LIQUIDITY_JSONL)
        _ensure_parent(path)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    except Exception:
        pass

# === V3.2 – Correction : enregistrer_pools_risquées (robuste) ===

def enregistrer_pools_risquées(pools: list, date: str, profil: str):
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_risques.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "plateforme", "nom_pool", "apr", "tvl", "risque", "raisons"])

        for pool in pools:
            # Ne journaliser que les pools marquées à risque
            if not bool(pool.get("risque", False)):
                continue

            plateforme = pool.get("platform") or pool.get("plateforme") or ""
            nom_pool = (
                pool.get("name")
                or pool.get("nom")
                or pool.get("pair")
                or f"{pool.get('token0', '?')}-{pool.get('token1', '?')}"
            )
            apr = pool.get("apr", 0)
            tvl = pool.get("tvl", 0)
            raisons = pool.get("raisons_risque") or pool.get("raisons") or []

            writer.writerow([
                date,
                profil,
                plateforme,
                nom_pool,
                apr,
                tvl,
                "true",  # marqué à risque
                ";".join(map(str, raisons))
            ])
