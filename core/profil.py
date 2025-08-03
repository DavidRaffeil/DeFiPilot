# core/profil.py

"""Gestion du profil utilisateur actif.

Le profil actif est stocké directement dans ce module afin de pouvoir être
modifié depuis une interface externe (par exemple ``controlpilot.py``).
"""

# Profil actuellement utilisé par l'application.
PROFIL_ACTIF = "agressif"

PROFILS = {
    "prudent": {"tvl": 0.9, "apr": 0.1},
    "modéré": {"tvl": 0.7, "apr": 0.3},
    "modere": {"tvl": 0.7, "apr": 0.3},
    "agressif": {"tvl": 0.3, "apr": 0.7}
}


def charger_profil(nom_profil: str) -> dict:
    """Retourne les pondérations associées au ``nom_profil`` fourni."""
    data = PROFILS.get(nom_profil.lower(), PROFILS["modere"])
    return {
        "nom": nom_profil,
        "ponderations": {"tvl": data["tvl"], "apr": data["apr"]},
    }


def charger_profil_utilisateur() -> dict:
    """Charge le profil actuellement défini comme actif."""
    return charger_profil(PROFIL_ACTIF)
