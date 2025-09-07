# core/real_wallet.py – V3.8.9 (env-priority hotfix)
"""Module wallet réel avec gestion multi-wallets, priorité .env, et journalisation.

Priorité de sélection du wallet :
1) .env si WALLET_ACTIVE_NAME=ENV, ou (active_name is None et WALLET_ADDRESS/ADDRESS défini)
2) core.wallets_manager (get_wallet / get_default_wallet)
3) Fallback .env (même incomplet)

Sécurité : la clé privée n'est JAMAIS affichée dans les logs.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

# Imports robustes (tolérer l'absence des libs côté environnement)
try:  # Web3
    from web3 import Web3  # type: ignore
except Exception:  # pragma: no cover
    Web3 = None  # type: ignore

try:  # eth-account
    from eth_account import Account  # type: ignore
    try:
        from eth_account.messages import encode_defunct  # type: ignore
    except Exception:  # pragma: no cover
        encode_defunct = None  # type: ignore
except Exception:  # pragma: no cover
    Account = None  # type: ignore
    encode_defunct = None  # type: ignore

# Journalisation (optionnelle)
try:
    from core.journal_wallet import log_wallet_action  # type: ignore
except Exception:  # pragma: no cover
    log_wallet_action = None  # type: ignore

# Gestion multi-wallets (optionnelle)
try:
    from core.wallets_manager import get_default_wallet, get_wallet, WalletConfigError  # type: ignore
except Exception:  # pragma: no cover
    get_default_wallet = None  # type: ignore
    get_wallet = None  # type: ignore
    class WalletConfigError(Exception):
        pass

# ────────────────────────────────────────────────────────────────────────────────
# État interne & configuration
# ────────────────────────────────────────────────────────────────────────────────
_logger = logging.getLogger(__name__)

_W3: Optional[Any] = None  # instance Web3 mise en cache
_ADDRESS: Optional[str] = None  # adresse publique mise en cache
_ACTIVE_NAME: Optional[str] = None  # nom du wallet actif

# Support des différentes variables d'env pour l'URL RPC
def _select_rpc_from_env() -> Optional[str]:
    return (
        os.getenv("POLYGON_RPC_URL")
        or os.getenv("RPC_POLYGON")
        or os.getenv("WEB3_RPC_URL")
        or os.getenv("RPC_URL")
    )

_RPC_URL: Optional[str] = _select_rpc_from_env()

# ────────────────────────────────────────────────────────────────────────────────
# Utilitaires privés
# ────────────────────────────────────────────────────────────────────────────────

def _mask_addr(addr: Optional[str]) -> str:
    """Masque une adresse pour les logs (0xABCD…1234)."""
    if not addr or len(addr) < 10:
        return addr or "?"
    return f"{addr[:6]}…{addr[-4:]}"


def _env_wallet_tuple(active_name: Optional[str]) -> Dict[str, str]:
    """Lit l'adresse/clé depuis .env, avec support de noms."""
    name = active_name or os.getenv("WALLET_ACTIVE_NAME") or "default"
    addr = (
        (os.getenv(f"WALLET_{name.upper()}_ADDRESS") if active_name else None)
        or os.getenv("WALLET_ADDRESS")
        or os.getenv("ADDRESS")
        or ""
    )
    pk = (
        (os.getenv(f"WALLET_{name.upper()}_PRIVATE_KEY") if active_name else None)
        or os.getenv("PRIVATE_KEY")
        or ""
    )
    return {"name": name, "address": addr, "private_key": pk}


def _load_active_wallet(active_name: Optional[str] = None) -> Dict[str, Any]:
    """Charge la définition du wallet en respectant la priorité .env.

    Retourne un dict : {"name", "address", "private_key"}.
    Lève RuntimeError en cas de configuration invalide.
    """
    env_mode = (os.getenv("WALLET_ACTIVE_NAME") or "").upper() == "ENV"
    env_addr = os.getenv("WALLET_ADDRESS") or os.getenv("ADDRESS") or ""
    env_pk = os.getenv("PRIVATE_KEY") or ""

    # 1) Forçage ENV
    if env_mode:
        return {"name": "ENV", "address": env_addr, "private_key": env_pk}

    # 2) Priorité .env si pas de nom explicite et .env fournit une adresse
    if active_name is None and env_addr:
        return {"name": "ENV", "address": env_addr, "private_key": env_pk}

    # 3) wallets_manager par nom
    if active_name and callable(get_wallet):
        try:
            data = get_wallet(active_name)  # type: ignore[call-arg]
        except Exception as exc:
            raise RuntimeError(f"Configuration wallet invalide : {exc}") from exc
        required = {"name", "address", "private_key"}
        if not isinstance(data, dict) or not required.issubset(data):
            raise RuntimeError("Données wallet incomplètes (attendu name/address/private_key).")
        return {"name": str(data["name"]), "address": str(data["address"]), "private_key": str(data["private_key"]) }

    # 4) wallets_manager par défaut
    if callable(get_default_wallet):
        try:
            data = get_default_wallet()  # type: ignore[call-arg]
        except Exception as exc:
            raise RuntimeError(f"Configuration wallet invalide : {exc}") from exc
        required = {"name", "address", "private_key"}
        if not isinstance(data, dict) or not required.issubset(data):
            raise RuntimeError("Données wallet incomplètes (attendu name/address/private_key).")
        return {"name": str(data["name"]), "address": str(data["address"]), "private_key": str(data["private_key"]) }

    # 5) Fallback .env
    return _env_wallet_tuple(active_name)

# ────────────────────────────────────────────────────────────────────────────────
# API publique
# ────────────────────────────────────────────────────────────────────────────────

def get_wallet_address(active_name: Optional[str] = None) -> Optional[str]:
    """Retourne l'adresse publique du wallet actif (ou None si indisponible).

    Met en cache l'adresse pour éviter les recomputations.
    Compatible avec l'appel `get_wallet_address()` sans paramètre.
    """
    global _ADDRESS, _ACTIVE_NAME
    try:
        if _ADDRESS is not None and (active_name is None or active_name == _ACTIVE_NAME):
            return _ADDRESS
        data = _load_active_wallet(active_name)
        addr = str(data.get("address") or "").strip()
        if not addr:
            return None
        _ADDRESS = addr
        _ACTIVE_NAME = str(data.get("name") or active_name or "default")
        return _ADDRESS
    except Exception:
        return None


def get_private_key(name: Optional[str] = None) -> str:
    """Retourne la clé privée du wallet demandé.

    Si `name` est None, utilise le wallet par défaut. Lève RuntimeError si introuvable.
    """
    data = _load_active_wallet(name)
    pk = str(data.get("private_key") or "").strip()
    if pk:
        return pk
    raise RuntimeError("clé privée introuvable")


def get_web3() -> Optional[Any]:
    """Retourne une instance Web3 connectée à l'URL RPC configurée, sinon None."""
    global _W3, _RPC_URL
    if Web3 is None:
        return None
    if _W3 is not None:
        return _W3
    if not _RPC_URL:
        _logger.warning("Aucune URL RPC (POLYGON_RPC_URL / RPC_POLYGON / WEB3_RPC_URL / RPC_URL) définie.")
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(_RPC_URL))  # type: ignore[attr-defined]
        ok = False
        try:
            ok = bool(w3.is_connected())
        except Exception:
            try:
                ok = bool(w3.isConnected())  # type: ignore[attr-defined]
            except Exception:
                ok = False
        if not ok:
            _logger.error("Web3 non connecté (%s)", _RPC_URL)
            return None
        _W3 = w3
        return _W3
    except Exception as exc:
        _logger.exception("Erreur de connexion Web3: %s", exc)
        return None


def connect_wallet(active_name: Optional[str] = None) -> Tuple[Optional[str], Optional[Any]]:
    """Charge l'adresse active et tente une connexion Web3.

    Journalise un `wallet_connect` si le hook est disponible.
    """
    global _ADDRESS, _ACTIVE_NAME
    addr = get_wallet_address(active_name)
    if not addr:
        _logger.error("Aucune adresse wallet disponible")
        return None, None
    if callable(log_wallet_action):
        try:
            log_wallet_action(action="wallet_connect", notes=f"connexion {_mask_addr(addr)}")
        except Exception:
            pass
    w3 = get_web3()
    return addr, w3


def disconnect_wallet() -> None:
    """Réinitialise l'état interne et journalise `wallet_disconnect`."""
    global _W3, _ADDRESS, _ACTIVE_NAME
    try:
        if callable(log_wallet_action) and _ADDRESS:
            try:
                log_wallet_action(action="wallet_disconnect", notes=f"déconnexion {_mask_addr(_ADDRESS)}")
            except Exception:
                pass
        _logger.info("Wallet déconnecté")
    finally:
        _W3 = None
        _ADDRESS = None
        _ACTIVE_NAME = None


def sign_message(message: str, active_name: Optional[str] = None) -> Optional[str]:
    """Signe un message arbitraire et retourne la signature hex (ou None)."""
    if Account is None:
        _logger.warning("eth_account indisponible : signature impossible.")
        return None
    try:
        pk = get_private_key(active_name)
    except RuntimeError:
        _logger.error("Signature impossible : clé privée introuvable.")
        return None
    addr = get_wallet_address(active_name)
    if not addr:
        _logger.error("Signature impossible : adresse indisponible.")
        return None
    try:
        if encode_defunct is not None:
            msg = encode_defunct(text=message)  # type: ignore
            signed = Account.sign_message(msg, private_key=pk)
        else:
            return None
        sig_hex = signed.signature.hex()
        _logger.info("Message signé par %s", _mask_addr(addr))
        return sig_hex
    except Exception as exc:
        _logger.exception("Erreur de signature : %s", exc)
        return None


if __name__ == "__main__":  # Test léger
    logging.basicConfig(level=logging.INFO)
    a, w = connect_wallet()
    if a and w:
        _logger.info("Adresse active : %s", _mask_addr(a))
