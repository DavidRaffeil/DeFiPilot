# core/blacklist.py

import json
import os

BLACKLIST_PATH = "blacklist_temporaire.json"

def charger_blacklist():
    if not os.path.exists(BLACKLIST_PATH):
        return []
    with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def filtrer_blacklist(pools):
    blacklist = charger_blacklist()
    return [pool for pool in pools if pool["id"] not in blacklist]

def ajouter_a_blacklist(pool_id):
    blacklist = charger_blacklist()
    if pool_id not in blacklist:
        blacklist.append(pool_id)
        with open(BLACKLIST_PATH, "w", encoding="utf-8") as f:
            json.dump(blacklist, f, indent=2, ensure_ascii=False)
