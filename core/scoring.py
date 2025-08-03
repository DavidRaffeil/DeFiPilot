# core/scoring.py
# 🧩 Version : V2.8 – Étape 3 finalisée
# 🎯 Intégration propre de `poids_slippage` + nettoyage

from core import historique, config, profil


def charger_ponderations(profil_nom):
    """
    Charge les pondérations APR/TVL depuis le profil défini dans config.
    """
    base = config.PROFILS.get(profil_nom, config.PROFILS["modere"])
    return {
        "apr": base["apr"],
        "tvl": base["tvl"]
    }


def charger_profil_utilisateur():
    """
    Charge l’ensemble des paramètres du profil actif, y compris le poids du slippage LP.
    """
    profil_actif = profil.PROFIL_ACTIF
    base = config.PROFILS.get(profil_actif, config.PROFILS["modere"])
    return {
        "nom": profil_actif,
        "ponderations": {
            "apr": base["apr"],
            "tvl": base["tvl"]
        },
        "historique_max_bonus": base["historique_max_bonus"],
        "historique_max_malus": base["historique_max_malus"],
        # Ce poids est appliqué aux pools LP pour réduire leur score
        "poids_slippage": base["poids_slippage"],
    }


def calculer_score_pool(pool, ponderations, historique_pools, profil):
    """
    Calcule le score pondéré d'une pool, incluant bonus historique et malus slippage LP.
    """
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    score_base = apr * ponderations["apr"] + tvl * ponderations["tvl"]
    nom_pool = f"{pool.get('plateforme')} | {pool.get('nom')}"

    bonus = historique.calculer_bonus(
        historique_pools,
        nom_pool,
        max_bonus=profil.get("historique_max_bonus", 0.15),
        max_malus=profil.get("historique_max_malus", -0.10)
    )

    score_final = score_base * (1 + bonus)

    # 🛡️ Appliquer une pénalité via `poids_slippage` si le pool est un LP
    if pool.get("lp"):
        poids_slippage = profil.get("poids_slippage", 0)
        score_final *= (1 - poids_slippage)

    # 🔍 Affichage debug bonus
    print(f"[SCORE] {nom_pool} | Score base : {round(score_base,2)} | Bonus : {round(bonus*100,2)}% → Score final : {round(score_final,2)}")

    return round(score_final, 2)


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
        resultats.append((pool, pool["score"]))
        gain_total += gain

    return resultats, round(gain_total, 2)
