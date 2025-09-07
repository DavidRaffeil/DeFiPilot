# add_liquidity.py – V3.8
"""Ajout de liquidité (dry-run) / Liquidity addition (dry-run)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict


logger = logging.getLogger(__name__)


def ajouter_liquidite_reelle(
    token_a: str,
    token_b: str,
    montant_a: float,
    montant_b: float,
    slippage: float,
    wallet_name: str,
    dex: str,
    network: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Simule l'ajout de liquidité.

    Parameters
    ----------
    token_a: str
        Première adresse du token.
    token_b: str
        Seconde adresse du token.
    montant_a: float
        Quantité du token A.
    montant_b: float
        Quantité du token B.
    slippage: float
        Slippage toléré en pourcentage.
    wallet_name: str
        Nom du wallet.
    dex: str
        DEX utilisée.
    network: str
        Réseau utilisé.
    dry_run: bool, optional
        Simulation sans transaction réelle.

    Returns
    -------
    Dict[str, Any]
        Résultat de la simulation.
    """

    now = datetime.now().isoformat(timespec="seconds")

    if montant_a <= 0 or montant_b <= 0:
        message = "Montants invalides: doivent être > 0."
        logger.error(message)
        return {
            "success": False,
            "tx_hash": None,
            "lp_tokens_recus": None,
            "message": message,
            "dex": dex,
            "network": network,
            "token_a": token_a,
            "token_b": token_b,
            "montant_a": montant_a,
            "montant_b": montant_b,
            "slippage": slippage,
            "wallet_name": wallet_name,
            "date": now,
            "statut": "FAIL",
        }

    if not 0 <= slippage <= 100:
        message = "Slippage invalide: doit être entre 0 et 100."
        logger.error(message)
        return {
            "success": False,
            "tx_hash": None,
            "lp_tokens_recus": None,
            "message": message,
            "dex": dex,
            "network": network,
            "token_a": token_a,
            "token_b": token_b,
            "montant_a": montant_a,
            "montant_b": montant_b,
            "slippage": slippage,
            "wallet_name": wallet_name,
            "date": now,
            "statut": "FAIL",
        }

    lp_tokens = (montant_a + montant_b) / 2
    message = "Dry-run: aucune transaction envoyée."
    if not dry_run:
        logger.warning("Mode non dry-run demandé mais non pris en charge.")
        message = "Mode non dry-run non supporté. Aucune transaction envoyée."

    logger.info(
        "Simulation d'ajout de liquidité %s/%s sur %s (%s)",
        token_a,
        token_b,
        dex,
        network,
    )

    return {
        "success": True,
        "tx_hash": None,
        "lp_tokens_recus": lp_tokens,
        "message": message,
        "dex": dex,
        "network": network,
        "token_a": token_a,
        "token_b": token_b,
        "montant_a": montant_a,
        "montant_b": montant_b,
        "slippage": slippage,
        "wallet_name": wallet_name,
        "date": now,
        "statut": "OK",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultat = ajouter_liquidite_reelle(
        token_a="TOKENA",
        token_b="TOKENB",
        montant_a=1.0,
        montant_b=2.0,
        slippage=0.5,
        wallet_name="test_wallet",
        dex="uniswap",
        network="ethereum",
        dry_run=True,
    )
    print(resultat)