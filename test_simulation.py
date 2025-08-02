# test_simulation.py

import simulateur_wallet

# Pool fictive pour le test
pool_test = {
    "dex": "beefy",
    "symbol": "ETH-USDC",
    "apr": 36.5,
    "tvl_usd": 500000  # Clé indispensable pour le calcul
}

# Appel de la fonction
gain_lisible, gain_brut = simulateur_wallet.simuler_gains_wallet(pool_test)

# Affichage du résultat
print("---- TEST SIMULATION ----")
print(f"APR pool : {pool_test['apr']}%")
print(f"TVL pool : {pool_test['tvl_usd']} USDC")
print(f"Gain estimé (24h) : {gain_lisible} (brut : {gain_brut:.4f})")
