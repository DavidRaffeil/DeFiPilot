# core/real_wallet.py – V3.8 (patch dotenv explicite + dérivation adresse sans RPC)
"""
Gestion du wallet réel (lecture .env, récupération adresse et clé privée).
"""

# --- DOTENV PATCH (doit être tout en haut) ---
import os
import pathlib
from dotenv import load_dotenv

_ENV_PATH = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)
# --- FIN PATCH ---

from eth_account import Account
from web3 import Web3

# (Re)lire les variables d'env après chargement
_DEF_RPC = os.getenv("POLYGON_RPC_URL") or os.getenv("WEB3_PROVIDER_URL")


def _normalize_pk(pk: str) -> str:
    pk = pk.strip()
    if pk.startswith("0x") or pk.startswith("0X"):
        pk = pk[2:]
    if len(pk) != 64 or any(c not in "0123456789abcdefABCDEF" for c in pk):
        raise RuntimeError("PRIVATE_KEY manquante ou invalide")
    return "0x" + pk.lower()


def get_private_key() -> str:
    """Retourne la clé privée normalisée (0x… 64 hex)."""
    pk = os.getenv("PRIVATE_KEY")
    if not pk:
        raise RuntimeError("PRIVATE_KEY manquante")
    return _normalize_pk(pk)


def get_wallet_address() -> str:
    """Retourne l'adresse publique checksum du wallet.

    - Si PRIVATE_KEY est définie, dérive l'adresse à partir de la clé (sans besoin de RPC).
    - Sinon, utilise WALLET_ADDRESS (variable d'environnement).
    """
    pk = os.getenv("PRIVATE_KEY")
    if pk:
        acct = Account.from_key(_normalize_pk(pk))
        return Web3.to_checksum_address(acct.address)

    addr = os.getenv("WALLET_ADDRESS")
    if not addr:
        raise RuntimeError("WALLET_ADDRESS manquante")
    return Web3.to_checksum_address(addr.strip())


def get_web3() -> Web3:
    """Retourne une instance Web3 connectée au RPC Polygon (lève RuntimeError sinon)."""
    if not _DEF_RPC:
        raise RuntimeError("POLYGON_RPC_URL manquant")
    w3 = Web3(Web3.HTTPProvider(_DEF_RPC))
    try:
        ok = w3.is_connected() if hasattr(w3, "is_connected") else w3.isConnected()  # v6 / v5
    except Exception:
        ok = False
    if not ok:
        raise RuntimeError(f"Connexion RPC échouée: {_DEF_RPC}")
    return w3


if __name__ == "__main__":
    # Petit test manuel
    w3 = get_web3()
    addr = get_wallet_address()
    print("✅ Connexion OK:", w3.is_connected())
    print("Adresse wallet :", addr)
    print("Solde MATIC    :", w3.from_wei(w3.eth.get_balance(addr), "ether"))
