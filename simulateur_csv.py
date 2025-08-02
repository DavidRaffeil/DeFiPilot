# simulateur_csv.py

import csv
import os
from datetime import date

FICHIER_CSV = "journal_simulation.csv"

def deja_journalise_aujourdhui(pool_id: str) -> bool:
    """
    Vérifie si un résultat pour cette pool a déjà été enregistré aujourd'hui.

    :param pool_id: Identifiant unique de la pool.
    :return: True si déjà enregistré aujourd'hui, sinon False.
    """
    if not os.path.exists(FICHIER_CSV):
        return False

    with open(FICHIER_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('date') == str(date.today()) and row.get('pool_id') == pool_id:
                return True
    return False

def journaliser_resultats(pool: dict, gain: float) -> None:
    """
    Enregistre le résultat simulé dans un fichier CSV.

    :param pool: Dictionnaire contenant les infos de la pool.
    :param gain: Gain simulé en USDC.
    """
    fichier_existe = os.path.exists(FICHIER_CSV)
    with open(FICHIER_CSV, 'a', newline='') as csvfile:
        champs = ['date', 'pool_id', 'nom', 'plateforme', 'gain_usdc']
        writer = csv.DictWriter(csvfile, fieldnames=champs)

        if not fichier_existe:
            writer.writeheader()

        writer.writerow({
            'date': str(date.today()),
            'pool_id': pool.get('id', 'inconnu'),
            'nom': pool.get('symbol', 'N/A'),
            'plateforme': pool.get('dex', 'N/A'),
            'gain_usdc': round(gain, 2)
        })
