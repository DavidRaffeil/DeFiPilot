# core/logger.py

import os
from datetime import datetime

DOSSIER_LOGS = "logs"

def _get_fichier_log_journalier():
    date_str = datetime.now().strftime("%Y-%m-%d")
    nom_fichier = f"journal_{date_str}.log"
    return os.path.join(DOSSIER_LOGS, nom_fichier)

def _ecrire_log(prefixe, message):
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)
    
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    ligne = f"{timestamp} {prefixe} {message}"
    
    # Affiche aussi dans le terminal
    print(ligne)

    # Écrit dans le fichier log du jour
    chemin_fichier = _get_fichier_log_journalier()
    with open(chemin_fichier, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")

def log_info(message):
    _ecrire_log("ℹ️ INFO", message)

def log_succes(message):
    _ecrire_log("✅ SUCCÈS", message)

def log_warning(message):
    _ecrire_log("⚠️ AVERTISSEMENT", message)

def log_erreur(message):
    _ecrire_log("🛑 ERREUR", message)
