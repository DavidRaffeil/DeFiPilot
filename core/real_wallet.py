# core/real_wallet.py – V3.8.10 (ENV priority + .env PRIVATE_KEY)
"""
Sélection/accès wallet réel avec priorité ENV et lecture de la clé privée depuis .env.

Règles de priorité :
1) Si WALLET_ACTIVE_NAME == "ENV" (ou si aucun wallet explicite et qu'une adresse ENV est fournie), alors :
   - Adresse = WALLET_ADDRESS (ou ADDRESS)
   - Clé privée = PRIVATE_KEY (ou PK)
2) Sinon, tentative via core.wallets_manager (get_wallet / get_default_wallet / get_private_key)
3) Fallback : variables d'environnement si disponibles.

Signatures stables :
- get_wallet_address(name: str | None = None) -> str | None
- get_private_key(name: str | None = None) -> str | None
"""
from __future__ import annotations

import os
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()  # charge .env si présent
logger = logging.getLogger(__name__)

# --- Helpers ENV ---

def _env(*keys: str) -> Optional[str]:
    for k in keys:
        v = os.getenv(k)
        if v:
            return v.strip()
    return None


def _env_active_is_ENV() -> bool:
    return (_env("WALLET_ACTIVE_NAME") or "").upper() == "ENV"


# --- API ---

def get_wallet_address(name: Optional[str] = None) -> Optional[str]:
    """Retourne l'adresse du wallet (checksum non imposé ici).

    Priorité ENV si WALLET_ACTIVE_NAME=ENV, sinon wallets_manager, sinon fallback ENV.
    """
    # 1) Priorité explicite ENV
    if _env_active_is_ENV():
        addr = _env("WALLET_ADDRESS", "ADDRESS")
        if addr:
            logger.debug("[real_wallet] adresse via ENV=%s", addr)
            return addr

    # 2) Tentative via wallets_manager si disponible
    try:
        from core import wallets_manager as wm  # type: ignore
        if name:
            w = wm.get_wallet(name)
            if w and w.get("address"):
                return w["address"]
        w = wm.get_default_wallet()
        if w and w.get("address"):
            return w["address"]
    except Exception as e:  # ImportError ou autres
        logger.debug("[real_wallet] wallets_manager indisponible: %s", e)

    # 3) Fallback ENV (même si WALLET_ACTIVE_NAME != ENV)
    addr = _env("WALLET_ADDRESS", "ADDRESS")
    if addr:
        logger.debug("[real_wallet] adresse via fallback ENV=%s", addr)
        return addr
    return None


def get_private_key(name: Optional[str] = None) -> Optional[str]:
    """Retourne la clé privée (hex 0x...). NE PAS logger la valeur.

    Priorité ENV quand actif, sinon wallets_manager, sinon fallback ENV.
    """
    # 1) Priorité explicite ENV
    if _env_active_is_ENV():
        pk = _env("PRIVATE_KEY", "PK")
        if pk:
            return pk

    # 2) Tentative via wallets_manager si disponible
    try:
        from core import wallets_manager as wm  # type: ignore
        if name:
            pk = wm.get_private_key(name)
            if pk:
                return pk
        # Parfois le manager expose la clé du default wallet
        w = wm.get_default_wallet()
        if w and w.get("private_key"):
            return w["private_key"]
    except Exception as e:
        logger.debug("[real_wallet] wallets_manager.get_private_key indisponible: %s", e)

    # 3) Fallback ENV générique
    pk = _env("PRIVATE_KEY", "PK")
    if pk:
        return pk
    return None
