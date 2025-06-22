import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

def detecter_adresse_wallet():
    rpc_url = os.getenv("RPC_URL")
    adresse_wallet = os.getenv("ADRESSE_WALLET")

    if not rpc_url or not adresse_wallet:
        print("❌ Variables d'environnement manquantes.")
        return None

    web3 = Web3(Web3.HTTPProvider(rpc_url))

    if not web3.is_connected():
        print("❌ Connexion au réseau échouée.")
        return None

    print(f"🔗 URL RPC définie : {rpc_url}")
    print(f"✅ Adresse EVM détectée : {adresse_wallet}")
    return adresse_wallet
