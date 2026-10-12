"""
Script de diagnostic pre-vol - Phase 1.4 (Lecture seule).
"""
import os
import sys
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
NETWORK = os.getenv("NETWORK", "polygon-mainnet")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_TRADE_USD = float(os.getenv("MAX_TRADE_AMOUNT_USD", "5.0"))

USDC_ADDRESS = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

def main():
    print("=" * 50)
    print("  DeFiPilot V6.1 - Controle pre-vol (Phase 1.4)")
    print("=" * 50)

    if not WALLET_ADDRESS:
        print(" Erreur : WALLET_ADDRESS absente du fichier .env")
        sys.exit(1)

    print(f"Portefeuille : {WALLET_ADDRESS}")
    print(f"Reseau       : {NETWORK}")
    print(f"Mode         : {'SIMULATION (DRY-RUN)' if DRY_RUN else 'REEL'}")
    print(f"Plafond max  : {MAX_TRADE_USD} USD")

    rpc_url = os.getenv("RPC_URL") or os.getenv("POLYGON_RPC_URL") or "https://polygon-rpc.com"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(" Impossible de joindre le RPC Polygon.")
        sys.exit(1)

    print(" Connexion RPC : OK")

    raw_pol = w3.eth.get_balance(Web3.to_checksum_address(WALLET_ADDRESS))
    pol_balance = w3.from_wei(raw_pol, "ether")
    print(f" Solde POL (Gaz) : {pol_balance:.4f} POL")

    usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    raw_usdc = usdc_contract.functions.balanceOf(Web3.to_checksum_address(WALLET_ADDRESS)).call()
    decimals = usdc_contract.functions.decimals().call()
    usdc_balance = raw_usdc / (10 ** decimals)
    print(f" Solde USDC      : {usdc_balance:.2f} USDC")

    print("-" * 50)
    if pol_balance < 2:
        print(" Attention : reserve de POL un peu faible pour le gaz.")
    elif usdc_balance < 1:
        print(" Attention : solde USDC insuffisant.")
    else:
        print(" Tous les voyants sont au vert !")
    print("=" * 50)

if __name__ == "__main__":
    main()
