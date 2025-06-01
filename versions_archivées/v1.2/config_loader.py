# core/config_loader.py

import json
import os

CONFIG_PATH = "config.json"
_config = {}

def charger_config():
    global _config
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Fichier de configuration '{CONFIG_PATH}' introuvable.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _config = json.load(f)

def get(parametre, valeur_defaut=None):
    return _config.get(parametre, valeur_defaut)
