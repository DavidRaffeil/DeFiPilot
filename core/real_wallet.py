# core/real_wallet.py – V3.6
"""Module wallet réel (Polygon) avec gestion multi-wallets et journalisation.

Ce module fournit une API simple pour :
- récupérer l'adresse publique du wallet actif,
- se connecter à un endpoint RPC Polygon via Web3,
- journaliser les connexions/déconnexions,
- signer un message.

Sources des données wallet :
- **Principal** : core.wallets_manager (get_default_wallet / get_wallet)
- Dégradation : si wallets_manager indisponible, le module fonctionne a minima
  mais `get_wallet_address()` peut retourner None.

Sécurité : la clé privée n'est **jamais** affichée dans les logs.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Tuple

# Import robustes (tolérer l'absence des libs côté environnement)
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

# Journalisation wallet (optionnelle)
try:
    from core.journal_wallet import log_wallet_action  # type: ignore
except Exception:  # pragma: no cover
    log_wallet_action = None  # type: ignore

# Gestion multi-wallets (source principale)
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

_W3: Any | None = None  # instance Web3 mise en cache
_ADDRESS: str | None = None  # adresse publique mise en cache
_ACTIVE_NAME: str | None = None  # nom du wallet actif (optionnel)
_CHAIN: str = os.getenv("CHAIN_NAME", "polygon")

# Support des deux variables d'env possibles pour l'URL RPC
_RPC_URL: str | None = (
    os.getenv("POLYGON_RPC_URL")
    or os.getenv("RPC_POLYGON")
    or None
)

# ────────────────────────────────────────────────────────────────────────────────
# Utilitaires privés
# ────────────────────────────────────────────────────────────────────────────────

def _mask_addr(addr: str) -> str:
    """Retourne une version masquée de l'adresse pour logs (0xABCD…1234)."""
    if not addr or len(addr) < 10:
        return addr or "?"
    return f"{addr[:6]}…{addr[-4:]}"


def _load_active_wallet(active_name: str | None = None) -> Dict[str, Any]:
    """Charge la définition du wallet (via wallets_manager).

    Retourne un dict minimal : {"name", "address", "private_key"}.
    Lève RuntimeError si indisponible/incomplet.
    """
    if get_default_wallet is None or get_wallet is None:
        raise RuntimeError("wallets_manager indisponible : impossible de charger le wallet.")

    try:
        data: Dict[str, Any] = (
            get_wallet(active_name) if active_name else get_default_wallet()
        )
    except WalletConfigError as exc:
        raise RuntimeError(f"Configuration wallet invalide : {exc}") from exc

    required = {"name", "address", "private_key"}
    if not isinstance(data, dict) or not required.issubset(data):
        raise RuntimeError("Données wallet incomplètes (attendu name/address/private_key).")
    return data


# ────────────────────────────────────────────────────────────────────────────────
# API publique
# ────────────────────────────────────────────────────────────────────────────────

def get_wallet_address(active_name: str | None = None) -> str | None:
    """Retourne l'adresse publique du wallet actif (ou None si indisponible).

    Met en cache l'adresse pour éviter les recomputations.
    Compatible avec l'appel `get_wallet_address()` sans paramètre (main.py).
    """
    global _ADDRESS, _ACTIVE_NAME
    try:
        if _ADDRESS is not None and (active_name is None or active_name == _ACTIVE_NAME):
            return _ADDRESS
        data = _load_active_wallet(active_name)
        _ADDRESS = str(data.get("address"))
        _ACTIVE_NAME = str(data.get("name"))
        return _ADDRESS
    except Exception:
        return None


def get_private_key(active_name: str | None = None) -> str | None:
    """Retourne la clé privée du wallet actif (ou None). **Ne pas logguer** la clé."""
    try:
        data = _load_active_wallet(active_name)
        pk = str(data.get("private_key", ""))
        return pk or None
    except Exception:
        return None


def get_web3() -> Any | None:
    """Retourne une instance Web3 connectée à l'URL RPC configurée, sinon None.

    Mise en cache de l'instance. Ne lève pas d'exception fatale.
    """
    global _W3
    if Web3 is None:
        return None
    if _W3 is not None:
        return _W3
    if not _RPC_URL:
        _logger.warning("Aucune URL RPC (POLYGON_RPC_URL / RPC_POLYGON) définie.")
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(_RPC_URL))  # type: ignore[attr-defined]
        # Certaines versions utilisent w3.is_connected(), d'autres w3.isConnected()
        ok = False
        try:
            ok = bool(w3.is_connected())
        except Exception:
            try:
                ok = bool(w3.isConnected())  # type: ignore[attr-defined]
            except Exception:
                ok = False
        if not ok:
            _logger.error("Connexion RPC échouée : %s", _RPC_URL)
            return None
        _W3 = w3
        return _W3
    except Exception as exc:
        _logger.exception("Erreur d'initialisation Web3 : %s", exc)
        return None


def is_connected() -> bool:
    """Retourne True si une connexion Web3 viable est disponible."""
    w3 = get_web3()
    return bool(w3 is not None)


def connect_wallet(active_name: str | None = None) -> Tuple[str | None, Any | None]:
    """Initialise la connexion Web3 et renvoie (adresse, web3).

    Journalise une action `wallet_connect` si possible.
    Ne lève pas d'exception fatale : en cas d'échec, retourne (None, None).
    """
    addr = get_wallet_address(active_name)
    w3 = get_web3()
    if addr and w3:
        if callable(log_wallet_action):
            try:
                log_wallet_action(action="wallet_connect", notes=f"connexion {_mask_addr(addr)} sur {_CHAIN}")
            except Exception:
                pass
        _logger.info("Wallet connecté : %s (%s)", _mask_addr(addr), _CHAIN)
        return addr, w3
    _logger.error("Connexion wallet impossible (adresse ou RPC indisponible).")
    return None, None


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


def sign_message(message: str, active_name: str | None = None) -> str | None:
    """Signe un message arbitraire et retourne la signature hex (ou None).

    Pré-requis : eth_account disponible et clé privée valide.
    """
    if Account is None:
        _logger.warning("eth_account indisponible : signature impossible.")
        return None
    pk = get_private_key(active_name)
    addr = get_wallet_address(active_name)
    if not pk or not addr:
        _logger.error("Signature impossible : clé privée ou adresse indisponible.")
        return None
    try:
        if encode_defunct is not None:
            msg = encode_defunct(text=message)  # type: ignore
            signed = Account.sign_message(msg, private_key=pk)
        else:
            # Dégradation : signer le hash du message si encode_defunct absent
            # (moins standard, mais évite de planter)
            from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict  # type: ignore
            # Fallback minimaliste : pas d'usage réel en prod sans encode_defunct
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
    disconnect_wallet()
