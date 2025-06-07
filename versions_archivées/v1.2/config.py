# config.py

from settings import SEUIL_INVESTISSEMENT, PROFIL_INVESTISSEUR

# Seuil de score à partir duquel on investit
THRESHOLD_SCORE = SEUIL_INVESTISSEMENT

# Pondérations des critères selon le profil
PROFIL_WEIGHTS = {
    "prudent": {
        "apy": 0.2,
        "tvl": 0.3,
        "volume": 0.1,
        "stability": 0.3,
        "risk_penalty": 0.1
    },
    "modéré": {
        "apy": 0.4,
        "tvl": 0.25,
        "volume": 0.15,
        "stability": 0.1,
        "risk_penalty": 0.1
    },
    "agressif": {
        "apy": 0.6,
        "tvl": 0.1,
        "volume": 0.2,
        "stability": 0.05,
        "risk_penalty": 0.05
    }
}

def get_weights():
    return PROFIL_WEIGHTS.get(PROFIL_INVESTISSEUR, PROFIL_WEIGHTS["modéré"])
