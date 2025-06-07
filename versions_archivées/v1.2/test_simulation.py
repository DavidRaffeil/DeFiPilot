# test_simulation.py

import simulateur_wallet

# Pool fictive pour le test
pool_test = {
    "dex": "beefy",
    "symbol": "ETH-USDC",
    "apr": 36.5  # 36.5% annuel
}

# Montant simulé
montant = 100

# Appel de la fonction
gain_lisible, gain_brut = simulateur_wallet.simuler_gains(pool_test, montant)

# Affichage du résultat
print("---- TEST SIMULATION ----")
print(f"Montant simulé : {montant} €")
print(f"APR pool : {pool_test['apr']}%")
print(f"Gain estimé (24h) : {gain_lisible} (brut : {gain_brut:.4f})")
