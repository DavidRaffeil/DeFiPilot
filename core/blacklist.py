# core/blacklist.py

import json
import os

BLACKLIST_PATH = "blacklist_temporaire.json"

def charger_blacklist():
    if not os.path.exists(BLACKLIST_PATH):
        return []
    with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_blacklist(liste):
    with open(BLACKLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(liste, f, indent=2, ensure_ascii=False)

def filtrer_pools_exclues(pools, blacklist):
    return [pool for pool in pools if pool["name"] not in blacklist or blacklist[pool["name"]] <= 0]

def maj_blacklist(blacklist, pool_name):
    blacklist[pool_name] = 5  # 5 jours d’exclusion
    sauvegarder_blacklist(blacklist)
    return blacklist

def nettoyer_blacklist(blacklist):
    nouvelles_entrees = {}
    for pool_name, jours in blacklist.items():
        if jours > 1:
            nouvelles_entrees[pool_name] = jours - 1
        elif jours == 1:
            print(f"✅ Fin de l'exclusion : {pool_name}")
    sauvegarder_blacklist(nouvelles_entrees)
    return nouvelles_entrees
