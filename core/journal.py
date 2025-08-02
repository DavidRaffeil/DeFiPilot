# core/journal.py

import os
import csv

def enregistrer_resume_journalier(date, profil, nb_pools, gain_total, gain_moyen):
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_resume.csv")
    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "nb_pools", "gain_total", "gain_moyen"])
        writer.writerow([date, profil, nb_pools, round(gain_total, 4), round(gain_moyen, 4)])

def enregistrer_top3(date, top3, profil):
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
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_swaps_lp.csv")
    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "nom_pool", "plateforme", "montant", "token1", "token2", "slippage", "profil"])
        writer.writerow([date, nom_pool, plateforme, round(montant, 4), token1, token2, round(slippage, 4), profil])

def enregistrer_lp_tokens(date, nom_pool, plateforme, lp_token, montant, profil):
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_lp_tokens.csv")
    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "nom_pool", "plateforme", "lp_token", "montant", "profil"])
        writer.writerow([date, nom_pool, plateforme, lp_token, round(montant, 4), profil])

def enregistrer_farming(date, nom_pool, plateforme, montant_lp, farming_apr, gain_farming, profil):
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

def lire_historique_pools():
    return []
