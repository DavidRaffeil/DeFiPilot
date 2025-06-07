# cycle_manager.py

import json
import os

FICHIER_CYCLE = "cycle.json"

def get_cycle_actuel():
    if not os.path.exists(FICHIER_CYCLE):
        return 1
    with open(FICHIER_CYCLE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("cycle", 1)

def incrementer_cycle():
    cycle = get_cycle_actuel() + 1
    with open(FICHIER_CYCLE, "w", encoding="utf-8") as f:
        json.dump({"cycle": cycle}, f)
    return cycle
