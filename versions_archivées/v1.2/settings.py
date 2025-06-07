# Profil d'investissement actif
PROFIL_INVESTISSEUR = "modéré"

PROFILS_JSON = "profils.json"

# Fonction pour changer le profil dynamiquement
def set_profil(nouveau_profil):
    global PROFIL_INVESTISSEUR
    PROFIL_INVESTISSEUR = nouveau_profil

# Seuil de score à partir duquel on investit
SEUIL_INVESTISSEMENT = 0.6

# Intervalle entre chaque cycle (en secondes)
INTERVAL_SECONDES = 600

# Options diverses
ACTIVER_LOGS_JOURNALIERS = True
# Mode simulation : si True, aucune action réelle (investir/désinvestir/log) n'est effectuée
MODE_SIMULATION = True

NB_CYCLES_BLACKLIST = 3

# Profils d'investissement (ajouté)
PROFILS = {
    "prudent": {
        "apy": 0.2,
        "volume": 0.2,
        "tvl": 0.3,
        "stability": 0.2,
        "risk": -0.1,
        "seuil_score": 0.7,
        "max_pools": 2
    },
    "modéré": {
        "apy": 0.3,
        "volume": 0.25,
        "tvl": 0.2,
        "stability": 0.2,
        "risk": -0.05,
        "seuil_score": 0.6,
        "max_pools": 3
    },
    "agressif": {
        "apy": 0.4,
        "volume": 0.3,
        "tvl": 0.1,
        "stability": 0.1,
        "risk": 0,
        "seuil_score": 0.5,
        "max_pools": 5
    }
}
# Numéro du cycle actuel (à incrémenter manuellement pour l’instant)
CYCLE_ACTUEL = 1
