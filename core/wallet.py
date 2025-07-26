# core/wallet.py

"""Fonctions liées à l'utilisation d'un wallet via Web3."""

from web3 import Web3
from core import logger

def detecter_adresse_wallet(w3):
    """Retourne l'adresse publique EVM du wallet connecté.

    Parameters
    ----------
    w3 : Web3
        Instance Web3 préalablement configurée avec un HTTPProvider.

    Returns
    -------
    str or None
        Adresse EVM détectée ou ``None`` si aucune adresse n'est disponible.
    """
    try:
        adresse = w3.eth.default_account
        if not adresse and w3.eth.accounts:
            adresse = w3.eth.accounts[0]
        if adresse:
            adresse = Web3.to_checksum_address(adresse)
            logger.log_info(f"🔗 Adresse wallet détectée : {adresse}")
            return adresse
        logger.log_warning("Aucune adresse de wallet détectée via Web3.")
    except Exception as exc:
        logger.log_erreur(f"Erreur lors de la détection du wallet : {exc}")
    return None

def obtenir_solde_usdc():
    """
    Simule un solde USDC. Cette fonction sera remplacée plus tard par une vraie lecture du wallet.
    """
    return 1000.0  # Valeur simulée, ex: 1000 USDC
