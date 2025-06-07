# dex_traderjoe.py

import requests

def get_pools_traderjoe(limit=10):
    url = "https://api.dexscreener.com/latest/dex/pairs"
    
    try:
        response = requests.get(url)
        print("Status code:", response.status_code)
        data = response.json()

        pools = []
        count = 0
        for pair in data.get("pairs", []):
            if pair.get("dexId", "").lower() != "traderjoe":
                continue
            if pair.get("chainId", "").lower() != "avalanche":
                continue

            formatted = {
                "dex": "TraderJoe",
                "address": pair.get("pairAddress"),
                "token0": pair["baseToken"]["symbol"],
                "token1": pair["quoteToken"]["symbol"],
                "tvl_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                "apr": float(pair.get("apy", 0)),  # APY utilisé comme estimation APR
            }

            pools.append(formatted)
            count += 1
            if count >= limit:
                break

        return pools

    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer les pools Trader Joe : {e}")
        return []
