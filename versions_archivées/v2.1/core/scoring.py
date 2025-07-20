# core/scoring.py – Version V1.8 avec bonus historique

from core import historique

PROFILS = {
    "prudent": {"apr": 0.2, "tvl": 0.8, "historique_max_bonus": 0.10, "historique_max_malus": -0.05},
    "modere": {"apr": 0.3, "tvl": 0.7, "historique_max_bonus": 0.15, "historique_max_malus": -0.10},
    "equilibre": {"apr": 0.5, "tvl": 0.5, "historique_max_bonus": 0.20, "historique_max_malus": -0.10},
    "dynamique": {"apr": 0.7, "tvl": 0.3, "historique_max_bonus": 0.25, "historique_max_malus": -0.15},
    "agressif": {"apr": 0.8, "tvl": 0.2, "historique_max_bonus": 0.30, "historique_max_malus": -0.20},
}

def charger_ponderations(profil_nom):
    return PROFILS.get(profil_nom, PROFILS["modere"])

def charger_profil_utilisateur():
    profil_nom = "modere"
    base = PROFILS.get(profil_nom, PROFILS["modere"])
    return {
        "nom": profil_nom,
        "ponderations": {"apr": base["apr"], "tvl": base["tvl"]},
        "historique_max_bonus": base["historique_max_bonus"],
        "historique_max_malus": base["historique_max_malus"]
    }

def calculer_score_pool(pool, ponderations, historique_pools, profil):
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    score = (
        apr * ponderations["apr"] +
        tvl * ponderations["tvl"]
    )

    nom_pool = f"{pool.get('plateforme')} | {pool.get('nom')}"
    bonus = historique.calculer_bonus(
        historique_pools,
        nom_pool,
        max_bonus=profil.get("historique_max_bonus", 0.15),
        max_malus=profil.get("historique_max_malus", -0.10)
    )
    score *= (1 + bonus)
    return round(score, 2)

def calculer_scores(pools, ponderations, historique_pools, profil):
    for pool in pools:
        pool["score"] = calculer_score_pool(pool, ponderations, historique_pools, profil)
    return pools

def calculer_scores_et_gains(pools, profil, solde, historique_pools):
    ponderations = profil["ponderations"]
    pools = calculer_scores(pools, ponderations, historique_pools, profil)
    pools_tries = sorted(pools, key=lambda p: p["score"], reverse=True)

    top3 = pools_tries[:3]
    resultats = []
    gain_total = 0

    for pool in top3:
        apr = pool.get("apr", 0)
        nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
        gain = round((solde * apr / 100) / 365, 2)
        resultats.append((nom, apr, gain))
        gain_total += gain

    return resultats, round(gain_total, 2)
