import requests
import random

_POOLS_FALLBACK = [
    {
        "id": "beefy-noice-weth",
        "plateforme": "beefy",
        "nom": "NOICE-WETH",
        "tvl_usd": 30528.0,
        "apr": 138013.21,
        "lp": True,
        "farming_apr": random.uniform(5, 50),
    },
    {
        "id": "spectra-stusd",
        "plateforme": "spectra-v2",
        "nom": "STUSD",
        "tvl_usd": 132448.0,
        "apr": 54046.6,
        "lp": False,
    },
    {
        "id": "berapaw-bullishv2",
        "plateforme": "berapaw",
        "nom": "BULLISHV2",
        "tvl_usd": 28784.0,
        "apr": 28862.79,
        "lp": False,
    },
]

def recuperer_pools():
    """Retourne une liste de pools depuis DefiLlama. Sinon, fallback."""
    url = "https://yields.llama.fi/pools"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        pools = []
        for item in data.get("data", []):
            symbol = item.get("symbol", "")
            is_lp = "lp" in symbol.lower()
            pool = {
                "id": f"{item.get('project', '')}-{symbol}",
                "nom": symbol,
                "plateforme": item.get("project", ""),
                "tvl_usd": item.get("tvlUsd", 0),
                "apr": item.get("apy", item.get("apr", 0)),
                "lp": is_lp,
            }
            if is_lp:
                pool["farming_apr"] = round(random.uniform(5, 50), 2)
            pools.append(pool)

        return pools

    except Exception as e:
        print(f"[ERREUR] Échec de récupération des pools : {e}")
        print("➡️ Utilisation des données locales de secours.")
        return _POOLS_FALLBACK
