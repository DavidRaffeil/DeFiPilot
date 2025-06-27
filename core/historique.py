import os
import json

HISTORIQUE_PATH = "data/historique_pools.json"

def charger_historique():
    if os.path.exists(HISTORIQUE_PATH):
        with open(HISTORIQUE_PATH, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_historique(historique):
    os.makedirs("data", exist_ok=True)
    with open(HISTORIQUE_PATH, "w") as f:
        json.dump(historique, f, indent=2)

def maj_historique(historique, nom_pool, gain):
    if nom_pool not in historique:
        historique[nom_pool] = {"count": 0, "total_gain": 0.0}
    historique[nom_pool]["count"] += 1
    historique[nom_pool]["total_gain"] += gain

def calculer_bonus(historique, nom_pool, max_bonus=0.15, max_malus=-0.10):
    if nom_pool not in historique:
        return 0.0
    count = historique[nom_pool]["count"]
    total_gain = historique[nom_pool]["total_gain"]
    if count == 0:
        return 0.0
    gain_moyen = total_gain / count

    if gain_moyen >= 10000:
        return max_bonus
    elif gain_moyen <= 0:
        return max_malus
    else:
        return max_malus + (gain_moyen / 10000) * (max_bonus - max_malus)
