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
