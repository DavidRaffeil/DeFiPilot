# core/blacklist.py

import json
import os
from datetime import datetime, timedelta

BLACKLIST_PATH = "data/blacklist_temporaire.json"

def charger_blacklist():
    if os.path.exists(BLACKLIST_PATH):
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def enregistrer_blacklist(blacklist):
    with open(BLACKLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, indent=2, ensure_ascii=False)

def ajouter_a_blacklist_temporaire(pool_nom, jours=3):
    date_fin = (datetime.now() + timedelta(days=jours)).strftime("%Y-%m-%d")
    blacklist = charger_blacklist()
    blacklist[pool_nom] = date_fin
    enregistrer_blacklist(blacklist)

def appliquer_blacklist_temporaire(pools):
    blacklist = charger_blacklist()
    today = datetime.now().date()

    def est_blacklistee(pool):
        nom = f"{pool.get('platform')} | {pool.get('id')}"
        if nom in blacklist:
            date_fin = datetime.strptime(blacklist[nom], "%Y-%m-%d").date()
            return date_fin >= today
        return False

    return [p for p in pools if not est_blacklistee(p)]
