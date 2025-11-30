# core/wallet_reader.py — V4.7.3
"""Module de lecture seule pour récupérer les soldes d'un wallet DeFiPilot via Web3.

Ce module fournit une interface simple pour initialiser un client Web3, lire le solde
natif et interroger les soldes d'une liste de tokens ERC-20. Toutes les opérations sont
strictement en lecture, sans transaction ni signature.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

from web3 import Web3

ENV_RPC_URL = "DEFIPILOT_RPC_URL"
ENV_WALLET_ADDRESS = "DEFIPILOT_WALLET_ADDRESS"

ERC20_ABI_MIN = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


def creer_web3(rpc_url: str) -> Web3:
    """Crée un client Web3 connecté à l'URL RPC fournie.

    Args:
        rpc_url: URL du noeud RPC à utiliser.

    Returns:
        Instance de Web3 configurée avec un fournisseur HTTP.

    Raises:
        ValueError: Si la connexion au noeud échoue.
    """

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise ValueError(f"Impossible de se connecter au noeud RPC : {rpc_url}")
    return web3


def lire_adresse_env() -> str:
    """Retourne l'adresse du wallet lue dans les variables d'environnement.

    Returns:
        Adresse du wallet DeFiPilot.

    Raises:
        ValueError: Si la variable d'environnement est absente ou vide.
    """

    adresse = os.environ.get(ENV_WALLET_ADDRESS, "").strip()
    if not adresse:
        raise ValueError(
            "Variable d'environnement DEFIPILOT_WALLET_ADDRESS manquante ou vide."
        )
    return adresse


def lire_rpc_env() -> str:
    """Retourne l'URL RPC lue dans les variables d'environnement.

    Returns:
        URL du noeud RPC.

    Raises:
        ValueError: Si la variable d'environnement est absente ou vide.
    """

    rpc_url = os.environ.get(ENV_RPC_URL, "").strip()
    if not rpc_url:
        raise ValueError(
            "Variable d'environnement DEFIPILOT_RPC_URL manquante ou vide."
        )
    return rpc_url


def lire_solde_native(web3: Web3, adresse: str) -> float:
    """Lit le solde natif du wallet et le retourne en unité principale.

    Args:
        web3: Instance Web3 connectée au réseau cible.
        adresse: Adresse publique du wallet.

    Returns:
        Solde natif converti en float.
    """

    balance_wei = web3.eth.get_balance(adresse)
    return float(web3.from_wei(balance_wei, "ether"))


def lire_solde_erc20(
    web3: Web3, token_address: str, holder: str
) -> tuple[int, int] | None:
    """Interroge un token ERC-20 pour obtenir le solde brut et les décimales.

    Args:
        web3: Instance Web3 connectée.
        token_address: Adresse du contrat du token ERC-20.
        holder: Adresse du détenteur dont on lit le solde.

    Returns:
        Tuple (balance_raw, decimals) si la lecture réussit, sinon None.
    """

    try:
        contrat = web3.eth.contract(address=token_address, abi=ERC20_ABI_MIN)
        balance: int = contrat.functions.balanceOf(holder).call()
        decimals: int = contrat.functions.decimals().call()
        return balance, decimals
    except Exception:
        return None


def lire_soldes_tokens(
    web3: Web3, holder: str, tokens: Mapping[str, dict[str, Any]]
) -> dict[str, float]:
    """Calcule les soldes des tokens ERC-20 fournis.

    Args:
        web3: Instance Web3 connectée au réseau cible.
        holder: Adresse publique du wallet.
        tokens: Mapping symbol -> configuration du token, incluant au minimum "address".

    Returns:
        Dictionnaire des soldes convertis en float par symbole.
    """

    soldes: dict[str, float] = {}
    for symbole, config in tokens.items():
        token_address = str(config.get("address", "")).strip()
        if not token_address:
            continue

        balance_info = lire_solde_erc20(web3, token_address, holder)
        if balance_info is None:
            continue

        balance_raw, decimals_token = balance_info
        decimals_config = config.get("decimals")
        if isinstance(decimals_config, int) and decimals_config >= 0:
            decimals_effectifs = decimals_config
        else:
            decimals_effectifs = decimals_token

        if decimals_effectifs < 0:
            continue

        soldes[symbole] = balance_raw / (10**decimals_effectifs)

    return soldes


def lire_soldes_depuis_env(
    tokens: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, float]:
    """Récupère les soldes natif et ERC-20 en utilisant les variables d'environnement.

    Args:
        tokens: Mapping facultatif des tokens ERC-20 à interroger.

    Returns:
        Dictionnaire contenant au minimum la clé "native" avec le solde natif.

    Raises:
        ValueError: Si la configuration nécessaire est absente ou invalide.
    """

    rpc_url = lire_rpc_env()
    adresse = lire_adresse_env()
    web3 = creer_web3(rpc_url)

    soldes: dict[str, float] = {"native": lire_solde_native(web3, adresse)}

    if tokens:
        soldes.update(lire_soldes_tokens(web3, adresse, tokens))

    return soldes
