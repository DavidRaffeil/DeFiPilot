# core/rendement.py

import csv
import os
from datetime import datetime

FICHIER_RENDEMENT = "journal_rendement.csv"

def enregistrer(gain, solde_avant, solde_apres, bonus_applique=None):
    """
    Enregistre un cycle dans le fichier CSV avec date, gain simulé, solde et bonus.
    """
    entetes = ["date", "gain_simule", "solde_avant", "solde_apres", "bonus_applique"]
    ligne = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        round(gain, 4),
        round(solde_avant, 4),
        round(solde_apres, 4),
        round(bonus_applique, 4) if bonus_applique is not None else ""
    ]

    fichier_existe = os.path.exists(FICHIER_RENDEMENT)

    try:
        with open(FICHIER_RENDEMENT, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not fichier_existe:
                writer.writerow(entetes)
            writer.writerow(ligne)
    except Exception as e:
        print(f"[ERREUR] Impossible d’enregistrer le rendement simulé : {e}")
