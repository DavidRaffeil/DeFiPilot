# error_logger.py

import os
from datetime import datetime

DOSSIER_LOGS = "logs"

def get_fichier_erreur_journalier():
    date_str = datetime.now().strftime("%Y-%m-%d")
    nom_fichier = f"errors_{date_str}.log"
    return os.path.join(DOSSIER_LOGS, nom_fichier)

def log_erreur(message):
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)

    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    chemin_fichier = get_fichier_erreur_journalier()
    with open(chemin_fichier, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
