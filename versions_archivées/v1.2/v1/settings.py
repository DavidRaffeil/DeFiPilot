# settings.py

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
