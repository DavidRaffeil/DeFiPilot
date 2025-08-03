# core/journal.py – V2.7

import os
import csv


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


def enregistrer_lp(date, profil, nom_pool, token1, token2, valeur_totale, poids_profil, slippage_simule):
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_lp.csv")
    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow([
                "date",
                "profil",
                "nom_pool",
                "token1",
                "token2",
                "valeur_totale",
                "poids_profil",
                "slippage_simule",
            ])
        writer.writerow([
            date,
            profil,
            nom_pool,
            token1,
            token2,
            round(valeur_totale, 4),
            round(poids_profil, 4),
            round(slippage_simule, 4),
        ])


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


def journaliser_scores(date, profil, pools, historique_pools):
    """
    Enregistre dans un fichier CSV les scores détaillés des pools simulées.
    """
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_scores.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "nom_pool", "apr", "tvl", "score_brut", "bonus", "score_final"])

        for pool in pools:
            apr = pool.get("apr", 0)
            tvl = pool.get("tvl_usd", 0)
            nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
            score_final = pool.get("score", 0)
            score_brut = apr * profil["ponderations"]["apr"] + tvl * profil["ponderations"]["tvl"]
            bonus = round((score_final / score_brut - 1) if score_brut else 0, 4)

            writer.writerow([
                date,
                profil["nom"],
                nom,
                round(apr, 2),
                round(tvl, 2),
                round(score_brut, 4),
                bonus,
                round(score_final, 2)
            ])
