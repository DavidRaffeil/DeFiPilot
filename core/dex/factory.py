# core/dex/factory.py – V6.5.0
"""
Factory d'initialisation du routeur multi-DEX par défaut (Polygon Mainnet).
"""

from __future__ import annotations

from typing import Any

from core.dex.base import BaseDEXAdapter
from core.dex.exceptions import DEXError
from core.dex.quickswap import QuickswapAdapter
from core.dex.router import DEXRouter
from core.dex.sushiswap import SushiswapAdapter
from core.dex.uniswap_v3 import UniswapV3Adapter
from core.dex.utils import CHAIN_ID_POLYGON

# Alias de compatibilité nommage CamelCase
QuickSwapAdapter = QuickswapAdapter
SushiSwapAdapter = SushiswapAdapter


class UnsupportedChainError(DEXError, ValueError):
    """Chaîne EVM non supportée par la configuration DEX par défaut."""


def create_default_dex_router(
    web3_client: Any,
    chain_id: int = CHAIN_ID_POLYGON,
    timeout: float = 3.0,
) -> DEXRouter:
    """
    Construit et retourne un `DEXRouter` préconfiguré pour Polygon Mainnet (chain_id=137)
    avec les adaptateurs officiels Uniswap V3, QuickSwap V3 et SushiSwap V2.

    Args:
        web3_client: instance Web3 connectée au réseau cible.
        chain_id: identifiant de la chaîne EVM (seul Polygon Mainnet 137 est supporté).
        timeout: délai maximum (en secondes) par adaptateur lors des cotations.

    Raises:
        ValueError / UnsupportedChainError: si `chain_id` n'est pas supporté ou si
            les paramètres sont invalides.
    """
    if web3_client is None:
        raise ValueError("web3_client ne peut pas être None")

    if isinstance(chain_id, bool) or not isinstance(chain_id, int):
        raise UnsupportedChainError(f"chain_id invalide : {chain_id!r}")

    if chain_id != CHAIN_ID_POLYGON:
        raise UnsupportedChainError(
            f"Chaîne non supportée (chain_id={chain_id}). "
            f"Seul Polygon Mainnet (chain_id={CHAIN_ID_POLYGON}) est supporté."
        )

    adapters: list[BaseDEXAdapter] = [
        UniswapV3Adapter(web3=web3_client),
        QuickswapAdapter(web3=web3_client),
        SushiswapAdapter(web3=web3_client),
    ]

    return DEXRouter(adapters=adapters, default_timeout=timeout)


__all__ = [
    "QuickSwapAdapter",
    "SushiSwapAdapter",
    "UnsupportedChainError",
    "create_default_dex_router",
]
