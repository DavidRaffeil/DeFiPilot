# dex_defillama.py

import requests

def get_pools_defillama(limit=10):
    url = "https://yields.llama.fi/pools"

    try:
        response = requests.get(url)
        print("Status code:", response.status_code)
        data = response.json()

        pools = []
        count = 0
        for pool in data.get("data", []):
            if not pool.get("tvlUsd") or pool["tvlUsd"] <= 0:
                continue
            if not pool.get("apy"):
                continue

            # Format standard pour DeFiPilot
            formatted = {
                "dex": pool.get("project", "Unknown"),
                "address": pool.get("pool"),
                "token0": pool.get("symbol", "").split("-")[0],
                "token1": pool.get("symbol", "").split("-")[-1],
                "tvl_usd": float(pool["tvlUsd"]),
                "apr": float(pool["apy"]),
                "source": "defillama"
            }

            pools.append(formatted)
            count += 1
            if count >= limit:
                break

        return pools

    except Exception as e:
        print(f"[ERREUR] Impossible de récupérer les pools DefiLlama : {e}")
        return []
