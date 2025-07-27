# core/logs_erreur.py

import os
from datetime import datetime

LOGS_PATH = "logs/logs_erreur.csv"

def log_exception(module, fonction, exception):
    """Enregistre une erreur dans le fichier logs/logs_erreur.csv"""
    try:
        os.makedirs(os.path.dirname(LOGS_PATH), exist_ok=True)
        fichier_existe = os.path.exists(LOGS_PATH)

        with open(LOGS_PATH, "a", encoding="utf-8", newline="") as f:
            from csv import writer
            writer = writer(f)
            if not fichier_existe:
                writer.writerow(["date", "module", "fonction", "erreur"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                module,
                fonction,
                str(exception)
            ])
    except Exception as e:
        print(f"[ERREUR FATALE] Impossible d’enregistrer l’erreur : {e}")
