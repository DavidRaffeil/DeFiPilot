# core/profil.py

PROFILS = {
    "prudent": {"tvl": 0.9, "apr": 0.1},
    "modéré": {"tvl": 0.7, "apr": 0.3},
    "agressif": {"tvl": 0.3, "apr": 0.7}
}

def charger_profil(nom_profil: str) -> dict:
    data = PROFILS.get(nom_profil.lower(), PROFILS["modéré"])
    return {
        "nom": nom_profil,
        "ponderations": {"tvl": data["tvl"], "apr": data["apr"]}
    }
