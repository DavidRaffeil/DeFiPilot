# core/config.py

import json

def charger_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)
