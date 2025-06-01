# utils/data_cleaner.py

def nettoyer_pools(pools):
    """
    Nettoie et uniformise les données des pools.
    Remplace les valeurs manquantes ou invalides pour 'tvl', 'apr', 'symbol' et 'platform'.
    """
    pools_nettoyes = []
    for pool in pools:
        # Nettoyage du TVL
        tvl = pool.get("tvl")
        if not isinstance(tvl, (int, float)):
            tvl = 0

        # Nettoyage de l'APR
        apr = pool.get("apr")
        if not isinstance(apr, (int, float)):
            apr = 0

        # Symboles
        symbol = pool.get("symbol") or "Unknown"
        platform = pool.get("platform") or "Unknown"

        # Mise à jour des valeurs nettoyées
        pool["tvl"] = tvl
        pool["apr"] = apr
        pool["symbol"] = symbol
        pool["platform"] = platform

        pools_nettoyes.append(pool)

    return pools_nettoyes
