# test_swap_reel.py – Version V3.1

"""
Script de test pour vérifier les fonctions liées au swap réel et au wallet :
– Chargement du wallet
– Simulation d’un swap réel
– Lecture du solde réel du wallet
– Préparation d’une transaction réelle de swap
"""

from web3 import Web3
from core.real_wallet import get_wallet_address, get_solde_reel
from core.swap_reel import effectuer_swap_reel, preparer_transaction_swap

# Connexion Web3 (réseau Polygon via Infura)
INFURA_URL = "https://polygon-mainnet.infura.io/v3/f197d43d05194bb9a717a63d222e8372"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Chargement du wallet
wallet_address = get_wallet_address()
print(f"✅ Wallet chargé : {wallet_address}")

# Test de effectuer_swap_reel()
print("\n🧪 Test de effectuer_swap_reel()")
resultat_swap = effectuer_swap_reel(w3, "USDC", "ETH", 12.34, "uniswap")
print(resultat_swap)

# Test de get_solde_reel()
print("\n🧪 Test de get_solde_reel()")
solde = get_solde_reel(wallet_address)
if solde is not None:
    print(f"💰 Solde du wallet : {solde:.6f} ETH")
else:
    print("❌ Impossible de récupérer le solde réel")

# Test de preparer_transaction_swap()
print("\n🧪 Test de preparer_transaction_swap()")
tx = preparer_transaction_swap(wallet_address, "ETH", "USDC", 0.001)
if tx:
    print("📦 Transaction préparée :")
    for cle, valeur in tx.items():
        print(f"  {cle} : {valeur}")
else:
    print("❌ Échec de la préparation de la transaction")

# Test avec DEX invalide
print("\n🧪 Test avec DEX invalide (unknownDEX)")
resultat_invalide = effectuer_swap_reel(w3, "MATIC", "USDC", 1.0, "unknownDEX")
print(resultat_invalide)
