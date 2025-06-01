# core/historique.py

import csv
import os
from datetime import datetime

FICHIER_CSV = "historique_cycles.csv"

def ajouter_au_csv(pools_top3):
    """
    Ajoute les 3 meilleures pools du cycle courant dans un fichier CSV historique.
    Si le fichier n'existe pas, il est créé avec les en-têtes.
    """
    creer_fichier = not os.path.exists(FICHIER_CSV)

    with open(FICHIER_CSV, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if creer_fichier:
            writer.writerow([
                "date", "rang", "plateforme", "nom", "TVL (USD)", "APR (%)", "score"
            ])

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for i, pool in enumerate(pools_top3, start=1):
            writer.writerow([
                date_str,
                i,
                pool["plateforme"],
                pool["nom"],
                pool["tvl_usd"],
                pool["apr"],
                pool["score"]
            ])
