# test_swap_reel.py

from core.swap_reel import initialiser_web3, executer_swap_reel, effectuer_swap_reel
from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()

def test_initialiser_web3():
    w3 = initialiser_web3()
    if w3 and (w3.is_connected() if hasattr(w3, "is_connected") else w3.isConnected()):
        print("✅ Web3 initialisé avec succès.")
    else:
        print("❌ Échec de la connexion Web3.")

def test_swap_simule():
    token_from = "USDC"
    token_to = "ETH"
    montant = 100
    wallet_address = os.getenv("WALLET_ADDRESS")
    print("▶ Test effectuer_swap_reel :")
    effectuer_swap_reel(token_from, token_to, montant, wallet_address)

def test_swap_reel_preparation():
    token_from = "USDC"
    token_to = "ETH"
    montant = 100
    wallet_address = os.getenv("WALLET_ADDRESS")
    print("▶ Test executer_swap_reel :")
    success = executer_swap_reel(token_from, token_to, montant, wallet_address)
    print("✅ Préparation réussie." if success else "❌ Préparation échouée.")

# Exécution des tests
if __name__ == "__main__":
    test_initialiser_web3()
    test_swap_simule()
    test_swap_reel_preparation()
