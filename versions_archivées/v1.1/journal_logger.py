import os
from datetime import datetime

DOSSIER_LOGS = "logs"

def init_journal():
    """Crée le dossier de logs s'il n'existe pas."""
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)

def get_nom_fichier_journal():
    """Retourne le nom du fichier journal du jour."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DOSSIER_LOGS, f"journal_{date_str}.log")

def log_journal(message):
    """Ajoute un message horodaté au journal du jour."""
    init_journal()
    horodatage = datetime.now().strftime("[%H:%M:%S]")
    ligne = f"{horodatage} {message}\n"
    with open(get_nom_fichier_journal(), "a", encoding="utf-8") as f:
        f.write(ligne)
