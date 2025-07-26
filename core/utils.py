# core/utils.py

import os
import csv

def ligne_deja_presente(fichier, date_str):
    """Vérifie si une ligne pour la date donnée existe dans le fichier CSV."""
    if not os.path.exists(fichier):
        return False

    try:
        with open(fichier, "r", encoding="utf-8") as f:
            lecteur = csv.reader(f)
            for ligne in lecteur:
                if ligne and ligne[0] == date_str:
                    return True
    except Exception as e:
        print(f"[ERREUR] Impossible de lire le fichier {fichier} : {e}")
    return False
