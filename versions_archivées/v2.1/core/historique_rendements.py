# core/historique_rendements.py

import csv
import os
from datetime import datetime

FICHIER_CSV = "historique_rendements.csv"

def enregistrer_resultats(profil_nom, pools, gain_total):
    """
    Enregistre les résultats d'une simulation dans un fichier CSV.
    Chaque ligne correspond à une pool du TOP 3.
    """
    fichier_existe = os.path.isfile(FICHIER_CSV)
    with open(FICHIER_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(["date", "profil", "plateforme", "nom_pool", "tvl_usd", "apr", "score", "gain_simule"])

        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for pool in pools:
            writer.writerow([
                date_now,
                profil_nom,
                pool.get("plateforme"),
                pool.get("nom"),
                round(pool.get("tvl_usd", 0), 2),
                round(pool.get("apr", 0), 2),
                round(pool.get("score", 0), 2),
                gain_total
            ])
