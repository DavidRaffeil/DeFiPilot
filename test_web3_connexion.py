from web3 import Web3

# URL Infura pour Polygon
infura_url = "https://polygon-mainnet.infura.io/v3/f197d43d05194bb9a717a63d222e8372"

# Connexion Web3
w3 = Web3(Web3.HTTPProvider(infura_url))

# Test de connexion
print("✅ Connexion Web3 réussie" if w3.is_connected() else "❌ Connexion Web3 échouée")
