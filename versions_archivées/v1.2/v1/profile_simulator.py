import json
from strategy import make_decision
from scoring import score_pool
from settings import PROFILS_JSON

def charger_profil_depuis_fichier(nom):
    try:
        with open(PROFILS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(nom)
    except:
        return None

def simuler_profil(profil_nom, pools, max_apy, max_tvl, max_volume):
    profil = charger_profil_depuis_fichier(profil_nom)
    if not profil:
        return 0

    seuil = profil["seuil_score"]
    max_invest = profil["max_pools"]

    scored = []
    for pool in pools:
        score = score_pool(pool, max_apy, max_tvl, max_volume)
        decision = make_decision(pool, score, threshold=seuil)
        if decision["decision"] == "INVESTIR":
            scored.append((pool["name"], score))

    return scored[:max_invest]
