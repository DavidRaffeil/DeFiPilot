# core/scoring.py – V3.3

from core.simulateur_logique import simuler_gains

# Flag IA (placeholder, pas utilisé dans cette version simplifiée)
AI_PONDERATION_ACTIVE = True


def charger_profil_utilisateur():
    """Charge et retourne les pondérations du profil utilisateur actif."""
    from core.config import charger_config, PROFILS
    config = charger_config()
    nom_profil = config.get("profil_defaut", "modere")
    return PROFILS[nom_profil]


def calculer_scores_et_gains(pools, profil_data, solde, historique_pools):
    """Calcule les scores des pools et renvoie (pool, score) comme attendu par main.py.
    Le gain total n'est pas utilisé par main.py, on retourne 0.0 pour compatibilité.
    """
    resultats = []
    gain_total = 0.0

    for pool in pools:
        apr = pool.get("apr", 0)
        tvl = pool.get("tvl_usd", 0)
        score_base = (apr * profil_data.get("apr", 0)) + (tvl * profil_data.get("tvl", 0))

        # Bonus/malus simple si historique disponible (optionnel, safe)
        bonus = 0.0
        nom_pool = pool.get("nom")
        if isinstance(historique_pools, dict) and nom_pool in historique_pools:
            bonus = float(historique_pools[nom_pool].get("bonus", 0))

        score_final = score_base * (1 + bonus / 100)
        pool["score"] = round(score_final, 2)

        # IMPORTANT: renvoyer (pool, score) car main.py s'attend à cette structure
        resultats.append((pool, pool["score"]))

    return resultats, gain_total
