"""Module simulating DeFiLlama data for local testing.

This lightweight stub provides a :func:`get_pools` function returning a
hard‑coded list of liquidity pool dictionaries.  It allows the rest of the
application (e.g. ``main.py``) to run in environments without network access or
external dependencies.

The data here is purely fictitious and serves only as a placeholder for real
API responses.
"""

from __future__ import annotations

from typing import Dict, List


def get_pools() -> List[Dict[str, object]]:
    """Return a list of sample liquidity pools.

    The pools are intentionally simple and contain only the keys required by the
    rest of the codebase:

    - ``nom``: Name of the pool.
    - ``plateforme``: Platform or DEX hosting the pool.
    - ``apr``: Annual Percentage Rate for the pool.
    - ``lp``: Boolean flag indicating that this is an LP pool (always ``True``).
    - ``farming_apr``: APR for farming rewards associated with the pool.
    """

    return [
        {
            "nom": "USDC-ETH",
            "plateforme": "uniswap",
            "apr": 5.0,
            "lp": True,
            "farming_apr": 10.0,
        },
        {
            "nom": "DAI-ETH",
            "plateforme": "sushiswap",
            "apr": 4.2,
            "lp": True,
            "farming_apr": 8.5,
        },
        {
            "nom": "USDT-BTC",
            "plateforme": "curve",
            "apr": 3.0,
            "lp": True,
            "farming_apr": 7.1,
        },
    ]


# Backwards compatibility ---------------------------------------------------
#
# Older parts of the project might still import ``recuperer_pools``.  Map this
# name to ``get_pools`` so those callers continue to function during the local
# simulation phase.
recuperer_pools = get_pools
