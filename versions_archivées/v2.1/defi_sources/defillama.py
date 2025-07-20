import requests

def recuperer_pools():
    url = "https://yields.llama.fi/pools"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        pools = []
        for item in data.get("data", []):
            pool = {
                "id": item.get("project", "") + "-" + item.get("symbol", ""),
                "nom": item.get("symbol", ""),
                "plateforme": item.get("project", ""),
                "tvlUsd": item.get("tvlUsd", 0),
                "apr": item.get("apy", 0),  # parfois appelé 'apy' au lieu de 'apr'
                "lp": "lp" in item.get("symbol", "").lower(),  # détection simple
            }
            pools.append(pool)

        return pools

    except requests.RequestException as e:
        print(f"[ERREUR] Échec de récupération des pools : {e}")
        return []
