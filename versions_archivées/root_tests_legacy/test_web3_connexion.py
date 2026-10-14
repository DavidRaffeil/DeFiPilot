# test_web3_connexion.py

from web3 import Web3
from dotenv import load_dotenv
import os

# charger .env
load_dotenv()

# récupérer RPC depuis .env
rpc_url = os.getenv("RPC_URL")

# connexion Web3
w3 = Web3(Web3.HTTPProvider(rpc_url))

# test connexion
if w3.is_connected():
    print("✅ Connexion Web3 réussie")
    print("Chain ID :", w3.eth.chain_id)
    print("Bloc actuel :", w3.eth.block_number)
else:
    print("❌ Connexion Web3 échouée")