import shutil
import os
from datetime import datetime

# Liste des fichiers à archiver (ajuste selon tes besoins)
fichiers = [
    "journal_gain_simule.csv",
    "journal_gain_csv.py",
    "historique_cycles.csv",
    "journal_rendement.csv",
    "solde_virtuel.json",
    "logs",  # dossier entier (facultatif)
    # Ajoute ici d'autres fichiers ou dossiers à archiver si besoin
]

# Nom de l'archive basé sur la date et l'heure
nom_archive = f"archive_simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

def fichiers_existants(flist):
    return [f for f in flist if os.path.exists(f)]

def main():
    to_archive = fichiers_existants(fichiers)
    if to_archive:
        print(f"Fichiers à archiver : {to_archive}")
        shutil.make_archive(nom_archive.replace('.zip', ''), 'zip', root_dir='.', base_dir='.')
        print(f"Archive créée : {nom_archive}")
    else:
        print("Aucun fichier à archiver.")

if __name__ == "__main__":
    main()
