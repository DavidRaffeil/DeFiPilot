# test_signer_transaction.py

from web3 import Web3
from core.swap_reel import signer_transaction_swap
from core.real_wallet import get_wallet_address

# Connexion à Polygon via Infura
infura_url = "https://polygon-mainnet.infura.io/v3/f197d43d05194bb9a717a63d222e8372"
w3 = Web3(Web3.HTTPProvider(infura_url))

# Récupération de l'adresse du wallet
from_address = get_wallet_address()

# Construction d'une transaction factice avec une adresse valide (checksummée)
tx = {
    "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # adresse Ethereum valide (Binance)
    "value": w3.to_wei(0.001, "ether"),
    "gas": 21000,
    "gasPrice": w3.to_wei("2", "gwei"),
    "nonce": w3.eth.get_transaction_count(from_address),
    "chainId": 137  # Polygon Mainnet
}

# Signature
signed_tx = signer_transaction_swap(w3, tx)

# Affichage du résultat
print("✅ Transaction signée avec succès")
print(f"Hash : {signed_tx.hash.hex()}")
print(f"Raw Transaction : {signed_tx.rawTransaction.hex()}")
