# core/env_validator.py – V6.0
"""Validation d'environnement réel (V6.0)."""

from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from typing import Any


def _is_hex_string(value: str, *, allow_prefix: bool = True) -> bool:
    if not isinstance(value, str):
        return False
    text = value
    if allow_prefix and text.startswith("0x"):
        text = text[2:]
    if not text:
        return False
    try:
        int(text, 16)
    except ValueError:
        return False
    return True


def _is_wallet_address(value: str) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("0x")
        and len(value) == 42
        and _is_hex_string(value)
    )


def _is_private_key(value: str) -> bool:
    if not isinstance(value, str):
        return False
    text = value[2:] if value.startswith("0x") else value
    return len(text) == 64 and _is_hex_string(text, allow_prefix=False)


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float)) and not math.isnan(value)


def _check_journal_path(path: str) -> bool:
    if not path:
        return False
    if os.path.exists(path):
        return os.access(path, os.W_OK)
    parent = os.path.dirname(path) or "."
    return os.path.isdir(parent) and os.access(parent, os.W_OK)


def _fetch_chain_id(rpc_url: str, timeout_s: float = 3.0) -> tuple[int | None, str | None]:
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_chainId",
        "params": [],
        "id": 1,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        rpc_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            body = response.read(1024 * 1024)
    except Exception as exc:
        return None, f"RPC connection failed: {exc}"

    try:
        decoded = json.loads(body.decode("utf-8"))
    except Exception as exc:
        return None, f"RPC response invalid JSON: {exc}"

    result = decoded.get("result") if isinstance(decoded, dict) else None
    if not isinstance(result, str) or not result.startswith("0x"):
        return None, "RPC response missing chainId"

    try:
        chain_id = int(result, 16)
    except ValueError:
        return None, "RPC response invalid chainId"

    return chain_id, None


def valider_environnement_reel(
    *,
    mode_execution: str,
    rpc_url: str | None,
    expected_chain_id: int,
    wallet_address: str | None,
    private_key: str | None,
    limites: dict,
    journal_execution_path: str | None,
) -> dict:
    """Valide l'environnement réel avant toute exécution on-chain."""

    errors: list[str] = []
    details: dict[str, Any] = {}

    if mode_execution != "real":
        return {
            "status": "SKIPPED",
            "errors": [],
            "details": {"mode_execution": mode_execution},
        }

    if not rpc_url:
        errors.append("RPC URL manquante")
    else:
        chain_id, rpc_error = _fetch_chain_id(rpc_url)
        if rpc_error:
            errors.append(rpc_error)
        else:
            details["chain_id"] = chain_id
            if chain_id != expected_chain_id:
                errors.append("Chain ID inattendu")

    if not wallet_address:
        errors.append("Adresse wallet manquante")
    elif not _is_wallet_address(wallet_address):
        errors.append("Adresse wallet invalide")

    if not private_key:
        errors.append("Clé privée manquante")
    elif not _is_private_key(private_key):
        errors.append("Clé privée invalide")

    if not isinstance(limites, dict):
        errors.append("Limites invalides")
    else:
        for key in (
            "max_invest_par_jour_usd",
            "max_invest_par_pool_usd",
            "max_invest_par_bucket_usd",
        ):
            value = limites.get(key)
            if not _is_number(value) or value < 0:
                errors.append(f"Limite invalide: {key}")

    if not journal_execution_path:
        errors.append("Chemin journal manquant")
    elif not _check_journal_path(journal_execution_path):
        errors.append("Chemin journal non accessible en écriture")

    status = "ENV_OK" if not errors else "ENV_INVALID"
    return {"status": status, "errors": errors, "details": details}
