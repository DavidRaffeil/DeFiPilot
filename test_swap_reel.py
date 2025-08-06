# test_swap_reel.py – Version V3.0

"""
Script de test pour vérifier les fonctions liées au swap réel et au wallet :
– Chargement du wallet
– Simulation d’un swap réel
– Lecture du solde réel du wallet
– Préparation d’une transaction réelle de swap
"""

from core.real_wallet import (
    effectuer_swap_reel,
    wallet_address,
    get_solde_reel,
)
from core.swap_reel import (
    preparer_transaction_swap,
)

print(f"✅ Wallet chargé : {wallet_address}")

print("\n🧪 Test de effectuer_swap_reel()")
resultat = effectuer_swap_reel("USDC", "ETH", 12.34, wallet_address)
print(resultat)

print("\n🧪 Test de get_solde_reel()")
solde = get_solde_reel(wallet_address)
if solde is not None:
    print(f"💰 Solde du wallet : {solde:.6f} ETH")
else:
    print("❌ Impossible de récupérer le solde réel")

print("\n🧪 Test de preparer_transaction_swap()")
tx = preparer_transaction_swap(wallet_address, "ETH", "USDC", 0.001)
if tx:
    print("📦 Transaction préparée :")
    for cle, valeur in tx.items():
        print(f"  {cle} : {valeur}")
else:
    print("❌ Échec de la préparation de la transaction")
if solde is not None:
    print(f"💰 Solde du wallet : {solde:.6f} ETH")
else:
    print("❌ Impossible de récupérer le solde réel")

print("\n🧪 Test de preparer_transaction_swap()")
tx = preparer_transaction_swap(wallet_address, "ETH", "USDC", 0.001)
if tx:
    print("📦 Transaction préparée :")
    for cle, valeur in tx.items():
        print(f"  {cle} : {valeur}")
else:
    print("❌ Échec de la préparation de la transaction")
