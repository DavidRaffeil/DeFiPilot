# utils/check_balance.py – V3.8
# Petit outil pour afficher le solde ERC‑20 du wallet actif
# Utilise core.real_wallet.get_web3 / get_wallet_address et l'ABI core/abi/erc20.json

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

from web3 import Web3

# Imports EXACTS depuis le dépôt (get_web3 peut ne pas exister)
try:
    from core.real_wallet import get_wallet_address, get_web3  # type: ignore
except ImportError:
    from core.real_wallet import get_wallet_address  # type: ignore
    get_web3 = None  # type: ignore


def load_abi(name: str):
    abi_path = Path(__file__).resolve().parent.parent / "core" / "abi" / f"{name}.json"
    with abi_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_w3() -> Web3:
    w3 = None
    try:
        if callable(get_web3):  # type: ignore
            w3 = get_web3()  # type: ignore
    except Exception:
        w3 = None
    if w3 is None:
        rpc = os.getenv("POLYGON_RPC")
        if not rpc:
            raise SystemExit("POLYGON_RPC manquant dans l'environnement et get_web3() indisponible")
        w3 = Web3(Web3.HTTPProvider(rpc))
    if not (getattr(w3, "is_connected", getattr(w3, "isConnected", lambda: False))()):
        raise SystemExit("Connexion Web3 échouée")
    return w3


def main():
    p = argparse.ArgumentParser(description="Afficher le solde ERC‑20 du wallet actif")
    p.add_argument("--token", required=True, help="Adresse du token ERC‑20")
    p.add_argument("--symbol", default=None, help="Symbole optionnel pour l'affichage")
    args = p.parse_args()

    w3 = get_w3()
    wallet = get_wallet_address()
    if not wallet:
        raise SystemExit("Adresse du wallet introuvable")
    wallet = w3.to_checksum_address(wallet)

    token_addr = w3.to_checksum_address(args.token)
    erc20 = w3.eth.contract(address=token_addr, abi=load_abi("erc20"))

    decimals = erc20.functions.decimals().call()
    symbol = args.symbol or erc20.functions.symbol().call()
    raw = erc20.functions.balanceOf(wallet).call()
    human = raw / (10 ** decimals)

    print(f"Wallet: {wallet}")
    print(f"Token : {symbol} ({token_addr})")
    print(f"Decimals: {decimals}")
    print(f"Balance raw: {raw}")
    print(f"Balance: {human}")


if __name__ == "__main__":
    main()
