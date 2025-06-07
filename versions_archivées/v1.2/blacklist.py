# blacklist.py

import json
import os
from settings import NB_CYCLES_BLACKLIST

FICHIER_BLACKLIST = "blacklist.json"

def charger_blacklist():
    if not os.path.exists(FICHIER_BLACKLIST):
        return {}
    try:
        with open(FICHIER_BLACKLIST, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def sauvegarder_blacklist(data):
    with open(FICHIER_BLACKLIST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def enregistrer_rejet(pool_name, cycle_actuel):
    """
    Enregistre la pool rejetée et la rend inaccessible pour NB_CYCLES_BLACKLIST cycles.
    """
    data = charger_blacklist()
    cycle_expiration = cycle_actuel + NB_CYCLES_BLACKLIST
    data[pool_name] = cycle_expiration
    sauvegarder_blacklist(data)

def est_blacklistee(pool_name, cycle_actuel):
    """
    Vérifie si la pool est toujours blacklistée à ce cycle.
    """
    data = charger_blacklist()
    cycle_exp = data.get(pool_name)
    if cycle_exp is None:
        return False
    return cycle_actuel < cycle_exp
def afficher_blacklist(cycle_actuel):
    data = charger_blacklist()
    actives = {p: exp for p, exp in data.items() if cycle_actuel < exp}
    if not actives:
        print("✅ Aucune pool actuellement blacklistée.")
    else:
        print("⛔ Pools actuellement blacklistées :")
        for pool, exp in actives.items():
            print(f" - {pool} (jusqu'au cycle {exp})")
def reset_blacklist():
    if os.path.exists(FICHIER_BLACKLIST):
        os.remove(FICHIER_BLACKLIST)
        print("✅ Blacklist réinitialisée.")
    else:
        print("ℹ️ Aucune blacklist à réinitialiser.")
