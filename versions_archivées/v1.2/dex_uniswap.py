# dex_uniswap.py

import requests

def get_pools_uniswap(limit=10):
    url = "https://api.dexscreener.com/latest/dex/pairs/uniswapv3"

    try:
        response = requests.get(url)
        print("Status code:", response.status_code)
        data = response.json()

        pools = []
        count = 0
        for pair in data.get("pairs", []):
            formatted = {
                "dex": "UniswapV3",
                "address": pair.get("pairAddress"),
                "token0": pair["baseToken"]["symbol"],
                "token1": pair["quoteToken"]["symbol"],
                "tvl_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                "apr": float(pair.get("apy", 0)),  # approximation
            }
            pools.append(formatted)
            count += 1
            if count >= limit:
                break

        return pools

    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer les pools Uniswap : {e}")
        return []
