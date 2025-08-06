# core/real_wallet.py – Version V3.0

"""
Contient les fonctions liées au wallet réel :
– Chargement de la clé privée et connexion Web3
– Simulation d’un swap réel (à remplacer plus tard)
– Lecture du solde réel via Web3
"""

import os
import logging
from dotenv import load_dotenv
from web3 import Web3

# Chargement des variables d’environnement
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL")

# Connexion Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
wallet_address = w3.eth.account.from_key(PRIVATE_KEY).address if PRIVATE_KEY else None


def effectuer_swap_reel(token_from, token_to, montant, wallet_address):
    """
    Simule un swap réel – à remplacer par une vraie transaction plus tard.

    Args:
        token_from (str): Symbole du token à échanger.
        token_to (str): Symbole du token cible.
        montant (float): Montant à échanger.
        wallet_address (str): Adresse du wallet utilisateur.

    Returns:
        str: Résultat simulé du swap.
    """
    logging.info(
        f"Swap simulé {token_from} → {token_to} : {montant:.2f} $ vers {wallet_address}"
    )
    return f"🔄 Swap réel simulé : {montant:.2f} {token_from} -> {token_to} vers {wallet_address}"


def get_solde_reel(address: str):
    """
    Récupère le solde réel d'un wallet Ethereum via Web3.

    Args:
        address (str): Adresse Ethereum à interroger.

    Returns:
        float | None: Solde en ETH ou None si une erreur survient.
    """
    try:
        if not w3.is_connected():
            logging.error("Connexion Web3 échouée")
            return None
        if not w3.is_address(address):
            logging.error("Adresse Ethereum invalide")
            return None
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, "ether")
        return float(balance_eth)
    except Exception as e:  # noqa: BLE001
        logging.error(f"Erreur lors de la récupération du solde : {e}")
        return None


# 🔓 Fonctions ajoutées pour compatibilité avec swap_reel.py
def get_wallet_address():
    return wallet_address

def get_private_key():
    return PRIVATE_KEY
