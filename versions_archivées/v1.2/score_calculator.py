# score_calculator.py

import math

def calculer_score(pool, poids_apr=0.7, poids_tvl=0.3):
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    score_apr = apr  # on suppose un APR en %
    score_tvl = math.log10(tvl + 1) if tvl > 0 else 0  # logarithme pour éviter les écarts extrêmes

    score = (poids_apr * score_apr) + (poids_tvl * score_tvl)
    return round(score, 2)
