# journal_logger.py

import os
from datetime import datetime

DOSSIER_LOGS = "logs"

def get_nom_fichier_journal():
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DOSSIER_LOGS, f"journal_{date_str}.log")

def log_journal(message):
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)
    
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    chemin_fichier = get_nom_fichier_journal()
    
    with open(chemin_fichier, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
