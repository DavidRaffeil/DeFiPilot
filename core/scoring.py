# core/scoring.py

def calculer_score_pool(pool, ponderations):
    """
    Calcule un score basé sur les pondérations APR et TVL pour une pool donnée.
    """
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    score = (
        apr * ponderations["apr"] +
        tvl * ponderations["tvl"]
    )

    return round(score, 2)


def calculer_scores(pools, ponderations):
    """
    Calcule le score pour chaque pool de la liste et l’ajoute au dictionnaire.
    Retourne la liste mise à jour.
    """
    for pool in pools:
        pool["score"] = calculer_score_pool(pool, ponderations)
    return pools
