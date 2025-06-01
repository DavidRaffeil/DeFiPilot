# profil_loader.py

import json

FICHIER_PROFILS = "profils.json"

def charger_profil(nom_profil):
    try:
        with open(FICHIER_PROFILS, "r", encoding="utf-8") as f:
            profils = json.load(f)
        return profils.get(nom_profil)
    except Exception as e:
        print(f"⚠️ Erreur chargement profil : {e}")
        return None
