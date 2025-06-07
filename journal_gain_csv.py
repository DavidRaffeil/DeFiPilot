# journal_gain_csv.py

import csv
import os
from datetime import datetime

FICHIER_CSV = "journal_gain_simule.csv"

def initialiser_fichier():
    """
    Crée le fichier CSV avec les en-têtes s’il n’existe pas encore.
    """
    if not os.path.exists(FICHIER_CSV):
        with open(FICHIER_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "datetime", "profil", "solde_simule",
                "top1_nom", "top1_apr", "top1_gain",
                "top2_nom", "top2_apr", "top2_gain",
                "top3_nom", "top3_apr", "top3_gain",
                "gain_total"
            ])

def enregistrer_cycle(profil, solde, pools, montant=100):
    """
    Enregistre un cycle dans le fichier CSV.
    """
    initialiser_fichier()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lignes = [now, profil, f"{solde:.2f}"]

    total_gain = 0.0
    for i in range(3):
        if i < len(pools):
            pool = pools[i]
            nom = f"{pool.get('plateforme', 'inconnu')} | {pool.get('nom', 'inconnu')}"
            apr = f"{float(pool.get('apr', 0)):.2f}"
            gain = f"{simuler_gain_brut(pool, montant):.2f}"
            total_gain += float(gain)
        else:
            nom, apr, gain = "", "", ""
        lignes.extend([nom, apr, gain])

    lignes.append(f"{total_gain:.2f}")

    with open(FICHIER_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(lignes)

def simuler_gain_brut(pool, montant):
    try:
        apr = abs(float(pool.get("apr", 0)))
        taux_journalier = apr / 100 / 365
        return montant * taux_journalier
    except Exception:
        return 0.0
