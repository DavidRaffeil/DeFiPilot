# defi_sources/defillama.py

def recuperer_pools():
    """
    Simulation de récupération de pools depuis une API DeFi (ex: DefiLlama).
    Renvoie une liste de dictionnaires représentant les pools.
    """
    return [
        {
            "id": "beefy-noice-weth",
            "plateforme": "beefy",
            "nom": "NOICE-WETH",
            "tvl_usd": 30528.00,
            "apr": 138013.21,
        },
        {
            "id": "spectra-stusd",
            "plateforme": "spectra-v2",
            "nom": "STUSD",
            "tvl_usd": 132448.00,
            "apr": 54046.60,
        },
        {
            "id": "berapaw-bullishv2",
            "plateforme": "berapaw",
            "nom": "BULLISHV2",
            "tvl_usd": 28784.00,
            "apr": 28862.79,
        },
        {
            "id": "nonsense-dust",
            "plateforme": "randomswap",
            "nom": "DUST-WBTC",
            "tvl_usd": 512.00,
            "apr": 2.5,
        }
    ]
