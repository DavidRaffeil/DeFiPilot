# core/profil.py

PROFILS = {
    "prudent": {"apr": 0.2, "tvl": 0.8},
    "modere": {"apr": 0.3, "tvl": 0.7},
    "equilibre": {"apr": 0.5, "tvl": 0.5},
    "dynamique": {"apr": 0.7, "tvl": 0.3},
    "agressif": {"apr": 0.8, "tvl": 0.2},
}

def charger_ponderations(profil_nom):
    """
    Retourne les pondérations (APR, TVL) associées à un profil d'investisseur donné.
    """
    return PROFILS.get(profil_nom, PROFILS["modere"])
