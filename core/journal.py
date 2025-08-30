# core/journal.py – V3.8.1
# Patch 2/5 — Journaux enrichis (gas_used, effective_gas_price, tx_cost_native, tx_status)
#
# Objectif
# - Enrichir les journaux réels pour add/remove liquidity (et actions associées)
# - Assurer un en-tête stable (extension automatique si l'ancien schéma manque des colonnes)
# - Conserver la rétrocompatibilité: les appels existants avec un dict "row" continuent de marcher
#
# Points clés
# - SCHEMA_REQ: liste d'attributs requis (ajoutés si manquants)
# - enregistrer_liquidity_csv(row: dict)
# - enregistrer_liquidity_jsonl(row: dict)
# - Les champs gas_* sont extraits automatiquement si row.get("details") contient ces infos
# - Ajout automatique d'un timestamp ISO et d'un run_id si absent

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Fichiers par défaut (à la racine du dépôt)
CSV_PATH = Path("journal_liquidite.csv")
JSONL_PATH = Path("journal_liquidite.jsonl")
BACKUP_PATH = Path("journal_liquidite.backup.csv")

# Schéma requis minimal + nouveaux champs gas
SCHEMA_REQ: List[str] = [
    # Meta
    "timestamp_iso",   # ajout auto
    "run_id",          # conseillé; auto si manquant
    "mode",            # "real"/"dryrun"
    "action",          # "addLiquidity" | "removeLiquidity" | etc.
    "platform",        # ex: "sushiswap"
    "chain",           # ex: "polygon"
    # Tokens & montants
    "tokenA_symbol",
    "tokenB_symbol",
    "amountA_in",      # float/str
    "amountB_in",
    "amountA_out",
    "amountB_out",
    "slippage_bps",
    # TX & gas
    "tx_hash",
    "tx_status",               # nouveau
    "gas_used",                # nouveau
    "effective_gas_price",     # nouveau (wei)
    "tx_cost_native",          # nouveau (MATIC sur Polygon)
    # Divers
    "notes",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gen_run_id() -> str:
    return datetime.now(timezone.utc).strftime("real-%Y%m%d-%H%M%S")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_header(path: Path) -> List[str]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return []
    return header


def _rewrite_with_new_header(path: Path, new_header: List[str]) -> None:
    """Réécrit le CSV pour ajouter les colonnes manquantes, en conservant les lignes existantes.
    Sauvegarde une copie BACKUP avant réécriture.
    """
    # Backup
    if path.exists():
        data = path.read_text(encoding="utf-8")
        BACKUP_PATH.write_text(data, encoding="utf-8")

    rows: List[Dict[str, Any]] = []
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))

    # Complète les lignes existantes avec colonnes manquantes
    for row in rows:
        for col in new_header:
            row.setdefault(col, "")

    _ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=new_header)
        writer.writeheader()
        writer.writerows(rows)


def _ensure_schema(path: Path, required: List[str]) -> List[str]:
    """Vérifie l'en-tête et l'étend si nécessaire. Retourne la liste finale de colonnes."""
    existing = _read_header(path)
    if not existing:
        # Fichier nouveau ou vide
        final = list(required)
        _ensure_parent(path)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=final)
            writer.writeheader()
        return final

    # Ajoute les colonnes manquantes en fin d'en-tête
    final = list(existing)
    changed = False
    for col in required:
        if col not in final:
            final.append(col)
            changed = True
    if changed:
        _rewrite_with_new_header(path, final)
    return final


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Complète les champs manquants + extrait metrics gas depuis row['details'] si présent."""
    out = dict(row)

    # Timestamp + run_id
    out.setdefault("timestamp_iso", _now_iso())
    out.setdefault("run_id", _gen_run_id())

    # Extraire metrics depuis details (TxResult.details)
    details = out.get("details") or {}
    if isinstance(details, dict):
        out.setdefault("gas_used", details.get("gas_used"))
        out.setdefault("effective_gas_price", details.get("effective_gas_price"))
        out.setdefault("tx_cost_native", details.get("tx_cost_native"))
        # Propager un éventuel status si transmis ailleurs
        out.setdefault("tx_status", details.get("status"))

    # Normaliser colonnes attendues (laisser vide si non fournies)
    for col in SCHEMA_REQ:
        out.setdefault(col, "")

    # Nettoyage: éviter d'écrire la clé 'details' dans le CSV
    out.pop("details", None)
    return out


def enregistrer_liquidity_csv(row: Dict[str, Any], path: Path = CSV_PATH) -> None:
    """Écrit une ligne CSV en respectant le schéma enrichi.
    Étend l'en-tête si besoin et crée un backup si modification de schéma.
    """
    final_header = _ensure_schema(path, SCHEMA_REQ)
    out = _normalize_row(row)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=final_header, extrasaction="ignore")
        writer.writerow(out)


def enregistrer_liquidity_jsonl(row: Dict[str, Any], path: Path = JSONL_PATH) -> None:
    """Écrit une ligne JSONL; on y laisse toutes les clés utiles (y compris 'details')."""
    tmp = dict(row)
    tmp.setdefault("timestamp_iso", _now_iso())
    tmp.setdefault("run_id", _gen_run_id())
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(tmp, ensure_ascii=False) + "\n")


# ==============================
# Aides pratiques (facultatives)
# ==============================

def construire_ligne_liquidity(*,
                               run_id: str,
                               mode: str,
                               action: str,
                               platform: str,
                               chain: str,
                               tokenA_symbol: str,
                               tokenB_symbol: str,
                               amountA_in: Any = "",
                               amountB_in: Any = "",
                               amountA_out: Any = "",
                               amountB_out: Any = "",
                               slippage_bps: Any = "",
                               tx_hash: str = "",
                               tx_status: Any = "",
                               notes: str = "",
                               details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Construit un dict prêt pour enregistrer_liquidity_* avec les bons champs.
    - 'details' peut contenir gas_used/effective_gas_price/tx_cost_native qui seront extraits.
    """
    row = {
        "run_id": run_id,
        "mode": mode,
        "action": action,
        "platform": platform,
        "chain": chain,
        "tokenA_symbol": tokenA_symbol,
        "tokenB_symbol": tokenB_symbol,
        "amountA_in": amountA_in,
        "amountB_in": amountB_in,
        "amountA_out": amountA_out,
        "amountB_out": amountB_out,
        "slippage_bps": slippage_bps,
        "tx_hash": tx_hash,
        "tx_status": tx_status,
        "notes": notes,
    }
    if details:
        row["details"] = details
    return row
