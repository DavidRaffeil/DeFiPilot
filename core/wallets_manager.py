# core/wallets_manager.py – V3.4
"""Wallet configuration manager for DeFiPilot.

This module provides simple helpers to load and validate wallet
configurations from ``config/wallets.json``. It is designed to support
multi-wallet setups without affecting existing single-wallet logic.

Only the Python standard library is used and no other project modules
are imported. Any configuration or JSON error raises ``WalletConfigError``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_WALLETS_PATH = Path("config/wallets.json")


class WalletConfigError(Exception):
    """Raised when the wallets configuration is invalid."""


def _validate_wallet(w: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Validate a single wallet entry.

    Parameters
    ----------
    w:
        Wallet dictionary to validate.
    index:
        Position of the wallet in the configuration list.
    """
    if not isinstance(w, dict):
        raise WalletConfigError(f"Wallet at index {index} is not an object")

    required = {"name", "address", "private_key"}
    keys = set(w)
    if keys != required:
        missing = required - keys
        extra = keys - required
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unexpected keys: {', '.join(sorted(extra))}")
        raise WalletConfigError(
            f"Wallet at index {index} is invalid ({'; '.join(details)})"
        )

    name = w["name"]
    address = w["address"]
    private_key = w["private_key"]

    if not isinstance(name, str) or not name:
        raise WalletConfigError(f"Wallet at index {index} has invalid name")

    if not isinstance(address, str) or not address.startswith("0x") or len(address) != 42:
        raise WalletConfigError(
            f"Wallet '{name}' has invalid address"
        )

    if not isinstance(private_key, str) or not private_key:
        raise WalletConfigError(
            f"Wallet '{name}' has invalid private_key"
        )

    return w


def load_wallets(path: Path = DEFAULT_WALLETS_PATH) -> List[Dict[str, Any]]:
    """Load and validate wallets from a JSON file."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise WalletConfigError(str(exc)) from exc

    if not isinstance(data, list):
        raise WalletConfigError("Wallet configuration must be a list")

    wallets: List[Dict[str, Any]] = []
    for idx, wallet in enumerate(data):
        wallets.append(_validate_wallet(wallet, idx))
    return wallets


def list_wallet_names(path: Path = DEFAULT_WALLETS_PATH) -> List[str]:
    """Return the list of wallet names."""
    return [w["name"] for w in load_wallets(path)]


def get_wallet(name: str, path: Path = DEFAULT_WALLETS_PATH) -> Dict[str, Any]:
    """Retrieve a wallet by name.

    Raises
    ------
    WalletConfigError
        If the wallet is not found.
    """
    wallets = load_wallets(path)
    for wallet in wallets:
        if wallet["name"] == name:
            return wallet

    available = ", ".join(w["name"] for w in wallets)
    raise WalletConfigError(
        f"Wallet '{name}' not found. Available wallets: {available}"
    )


def get_default_wallet(path: Path = DEFAULT_WALLETS_PATH) -> Dict[str, Any]:
    """Return the first wallet in the configuration."""
    wallets = load_wallets(path)
    if not wallets:
        raise WalletConfigError("No wallets configured")
    return wallets[0]


# Minimal usage examples (not executed)
# ------------------------------------
# from pathlib import Path
# wallets = load_wallets()
# names = list_wallet_names()
# default = get_default_wallet()
# main = get_wallet(names[0])
# custom_path = Path("/tmp/wallets.json")
# wallets_alt = load_wallets(custom_path)