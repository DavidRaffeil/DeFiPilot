# json_saver.py

import json
import os

FICHIER_JSON = "resultats_top3.json"

def sauvegarder_top3_json(pools_top3):
    """
    Enregistre les 3 meilleures pools dans un fichier JSON.
    Chaque pool doit être un dictionnaire avec les champs :
    dex, pair, tvl, apr, score
    """
    try:
        with open(FICHIER_JSON, "w", encoding="utf-8") as f:
            json.dump(pools_top3, f, indent=4, ensure_ascii=False)
        print(f"💾 Données TOP 3 enregistrées dans {FICHIER_JSON}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde JSON : {e}")
