import os
from datetime import datetime

# Définir le dossier où les logs seront enregistrés
DOSSIER_LOGS = "logs"

# Fonction pour obtenir le fichier d'erreur du jour
def get_fichier_erreur_journalier():
    # Génère le nom du fichier en fonction de la date actuelle
    date_str = datetime.now().strftime("%Y-%m-%d")
    nom_fichier = f"errors_{date_str}.log"
    return os.path.join(DOSSIER_LOGS, nom_fichier)

# Fonction pour enregistrer les erreurs
def log_erreur(message):
    # Vérifie si le dossier existe, sinon le crée
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)
        print(f"Le dossier logs/ a été créé à {DOSSIER_LOGS}")  # Message de confirmation dans la console

    # Ajoute un horodatage à chaque message d'erreur
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    
    # Récupère le chemin du fichier journalier des erreurs
    chemin_fichier = get_fichier_erreur_journalier()
    
    # Ouvre le fichier en mode ajout (a) et écrit l'erreur avec l'horodatage
    with open(chemin_fichier, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {message}\n")
    
    # Optionnel : Affiche un message de confirmation pour dire que l'erreur a été enregistrée
    print(f"Erreur enregistrée dans {chemin_fichier}")
