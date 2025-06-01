# historique.py

import csv
import os
from datetime import datetime

FICHIER_CSV = "historique_cycles.csv"

def ajouter_au_csv(pools_top3):
    """
    Ajoute les 3 meilleures pools du cycle courant dans un fichier CSV historique.
    Si le fichier n'existe pas, il est créé avec les en-têtes.
    """
    fichier_existe = os.path.exists(FICHIER_CSV)

    try:
        with open(FICHIER_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Écrire les en-têtes si le fichier est vide
            if not fichier_existe:
                writer.writerow(["datetime", "rank", "dex", "pair", "tvl", "apr", "score"])

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for pool in pools_top3:
                writer.writerow([
                    timestamp,
                    pool["rank"],
                    pool["dex"],
                    pool["pair"],
                    pool["tvl"],
                    pool["apr"],
                    pool["score"]
                ])

        print(f"📈 Historique mis à jour dans {FICHIER_CSV}")

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde de l'historique : {e}")
