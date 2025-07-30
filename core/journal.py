# core/journal.py – Version V2.5 complète avec historique + farming LP

import csv
import os
from datetime import datetime

def lire_historique_pools():
    """
    Retourne un historique simulé (vide pour l'instant).
    Peut être modifié plus tard pour lire un fichier.
    """
    return {}

def enregistrer_resume_journalier(date, profil, nb_pools, gain_total, gain_moyen):
    """
    Enregistre un résumé quotidien dans le journal principal.
    """
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_gain_simule.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "nb_pools", "gain_total", "gain_moyen"])
        writer.writerow([date, profil, nb_pools, round(gain_total, 4), round(gain_moyen, 4)])

def enregistrer_top3(date, top3, profil):
    """
    Enregistre le top 3 des pools dans un journal CSV.
    """
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_top3.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "nom_pool", "apr", "gain_simule"])
        for nom, apr, gain in top3:
            writer.writerow([date, profil, nom, round(apr, 2), round(gain, 2)])

def enregistrer_swap_lp(date, nom_pool, plateforme, montant, token1, token2, slippage, profil):
    """
    Enregistre les swaps simulés vers des tokens LP dans un journal CSV.
    """
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_lp_swap.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "plateforme", "pool", "montant", "token1", "token2", "slippage"])
        writer.writerow([date, profil, plateforme, nom_pool, round(montant, 4), token1, token2, round(slippage, 4)])

def enregistrer_farming(date, nom_pool, plateforme, montant_lp, farming_apr, gain_farming, profil):
    """
    Enregistre dans un journal CSV les gains simulés issus du farming de LP tokens.
    """
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_farming.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "plateforme", "pool", "montant_lp", "farming_apr", "gain_farming"])
        writer.writerow([
            date,
            profil,
            plateforme,
            nom_pool,
            round(montant_lp, 4),
            round(farming_apr, 2),
            round(gain_farming, 4)
        ])
