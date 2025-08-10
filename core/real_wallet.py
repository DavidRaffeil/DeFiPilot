# core/real_wallet.py – V3.4
# Adaptation multi-wallet : expose get_wallet_address / get_private_key via wallets_manager.
# Compatible mono-wallet : par défaut, utilise le premier wallet de config/wallets.json.

from __future__ import annotations

from typing import Any, Dict
from core.wallets_manager import get_default_wallet, get_wallet, WalletConfigError


def load_active_wallet(active_name: str | None = None) -> Dict[str, Any]:
    """
    Charge et renvoie le wallet actif sous forme de dict {"name","address","private_key"}.
    - Si active_name est fourni, charge ce wallet ; sinon, utilise le premier (par défaut).
    - Lève RuntimeError avec message clair si la configuration est invalide/absente.
    """
    try:
        wallet: Dict[str, Any] = get_wallet(active_name) if active_name else get_default_wallet()
    except WalletConfigError as exc:  # Pas de log/print ici
        raise RuntimeError(
            f"Wallet configuration error: {exc}. Verify config/wallets.json."
        ) from exc

    required = {"name", "address", "private_key"}
    if not isinstance(wallet, dict) or not required.issubset(wallet):
        raise RuntimeError("Incomplete wallet data. Verify config/wallets.json.")

    return wallet


def get_wallet_address(active_name: str | None = None) -> str:
    """Renvoie l'adresse du wallet actif."""
    return load_active_wallet(active_name)["address"]


def get_private_key(active_name: str | None = None) -> str:
    """Renvoie la clé privée du wallet actif."""
    return load_active_wallet(active_name)["private_key"]


# --- Exemples d'utilisation (commentés) ---
# w = load_active_wallet()  # premier wallet de config/wallets.json
# addr = get_wallet_address()
# pk = get_private_key()
# w2 = load_active_wallet("wallet_abonnements")
# addr2 = get_wallet_address("wallet_abonnements")
# pk2 = get_private_key("wallet_abonnements")
