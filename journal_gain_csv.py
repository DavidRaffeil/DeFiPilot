# journal_gain_csv.py

import csv
from datetime import datetime
import os

FICHIER_CSV = "journal_gain_simule.csv"

def enregistrer_cycle(profil, solde_simule, top3, montant_investi):
    """
    Enregistre un cycle d’analyse dans un fichier CSV.
    
    :param profil: nom du profil d’investissement utilisé
    :param solde_simule: solde du wallet simulé après mise à jour
    :param top3: liste des 3 meilleures pools sélectionnées
    :param montant_investi: montant simulé investi par pool
    """
    ligne = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profil": profil,
        "solde_simule": round(solde_simule, 2),
    }

    gain_total = 0

    for i, pool in enumerate(top3, start=1):
        nom_court = f"{pool['plateforme']} | {pool['nom']}"
        apr = round(pool['apr'], 2)
        gain = round(pool['apr'] * montant_investi / 100, 2)
        gain_total += gain

        ligne[f"top{i}_nom"] = nom_court
        ligne[f"top{i}_apr"] = apr
        ligne[f"top{i}_gain"] = gain

    ligne["gain_total"] = round(gain_total, 2)

    fichier_existe = os.path.isfile(FICHIER_CSV)
    with open(FICHIER_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ligne.keys())

        if not fichier_existe:
            writer.writeheader()
        writer.writerow(ligne)
