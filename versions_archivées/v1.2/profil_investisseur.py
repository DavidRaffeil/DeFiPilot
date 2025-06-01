# profil_investisseur.py

import json
import os

def get_profils_investisseur():
    return {
        "prudent":    {"poids_apr": 0.3, "poids_tvl": 0.7},
        "modere":     {"poids_apr": 0.5, "poids_tvl": 0.5},
        "agressif":   {"poids_apr": 0.8, "poids_tvl": 0.2}
    }

def get_profil_actif():
    chemin = os.path.join("config", "profil_investisseur.json")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("profil", "modere")  # "modere" par défaut
    except Exception as e:
        print(f"[⚠️] Erreur lecture du profil : {e}")
        return "modere"
