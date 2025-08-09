# core/defi_sources/defillama.py
# 🧩 Version : V3.2 – Alias get_pools_defillama + TVL fictif

def recuperer_pools():
    """
    Simule la récupération de pools DeFi depuis DefiLlama.
    Injecte une valeur fictive pour 'tvl_usd' afin de permettre la simulation.
    """
    pools = [
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

    # 💠 Ajout d'une TVL fictive pour chaque pool (valeur stable pour simulation)
    for pool in pools:
        pool["tvl_usd"] = 10000.0

    return pools


# ✅ Alias attendu par main.py
get_pools_defillama = recuperer_pools
