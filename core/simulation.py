import csv
import os
from datetime import datetime

FICHIER_JOURNAL = "logs/journal_gain_simule.csv"
FICHIER_SWAP_LP = "logs/journal_swaps_lp.csv"

def enregistrer_gain_simule(date, pool, gain, score):
    """Ajoute une entrée dans le journal des gains simulés."""
    os.makedirs("logs", exist_ok=True)
    with open(FICHIER_JOURNAL, mode="a", newline="", encoding="utf-8") as fichier:
        writer = csv.writer(fichier)
        writer.writerow([date, pool, gain, score])

def afficher_gains_historique():
    """Affiche un résumé des gains par jour."""
    if not os.path.exists(FICHIER_JOURNAL):
        print("Aucun journal de gains trouvé.")
        return

    journaux = {}
    with open(FICHIER_JOURNAL, mode="r", encoding="utf-8") as fichier:
        lecteur = csv.reader(fichier)
        for ligne in lecteur:
            if len(ligne) != 4:
                continue
            date, _, gain, _ = ligne
            gain = float(gain)
            journaux[date] = journaux.get(date, 0) + gain

    print("📈 Résumé des rendements journaliers :")
    for date, gain in sorted(journaux.items()):
        print(f"  • {date} : {gain:.4f} USDC")

def enregistrer_swap_lp(date, nom_pool, montant_token1, montant_token2):
    """Enregistre un swap LP simulé."""
    os.makedirs("logs", exist_ok=True)
    with open(FICHIER_SWAP_LP, mode="a", newline="", encoding="utf-8") as fichier:
        writer = csv.writer(fichier)
        writer.writerow([date.isoformat(), nom_pool, montant_token1, montant_token2])

def swap_lp_existe(date, nom_pool):
    """Vérifie si un swap LP est déjà enregistré pour ce jour et cette pool."""
    if not os.path.exists(FICHIER_SWAP_LP):
        return False

    with open(FICHIER_SWAP_LP, mode="r", encoding="utf-8") as fichier:
        lecteur = csv.reader(fichier)
        for ligne in lecteur:
            if len(ligne) != 4:
                continue
            date_ligne, nom, _, _ = ligne
            if date_ligne == date.isoformat() and nom == nom_pool:
                return True
    return False

def lire_swaps_lp(date):
    """Lit tous les swaps LP enregistrés pour une date donnée."""
    resultats = []
    if not os.path.exists(FICHIER_SWAP_LP):
        return resultats

    with open(FICHIER_SWAP_LP, mode="r", encoding="utf-8") as fichier:
        lecteur = csv.reader(fichier)
        for ligne in lecteur:
            if len(ligne) != 4:
                continue
            date_ligne, nom_pool, token1, token2 = ligne
            if date_ligne == date.isoformat():
                resultats.append((nom_pool, float(token1), float(token2)))
    return resultats

def calculer_stats_lp():
    """Calcule les statistiques globales LP (nombre de swaps, gains, score moyen)."""
    stats = {}
    if not os.path.exists(FICHIER_JOURNAL):
        return []

    with open(FICHIER_JOURNAL, mode="r", encoding="utf-8") as fichier:
        lecteur = csv.reader(fichier)
        for ligne in lecteur:
            if len(ligne) != 4:
                continue
            _, pool, gain, score = ligne
            try:
                gain = float(gain)
                score = float(score)
            except ValueError:
                continue
            if pool not in stats:
                stats[pool] = {"occurences": 0, "total_gain": 0.0, "total_score": 0.0}
            stats[pool]["occurences"] += 1
            stats[pool]["total_gain"] += gain
            stats[pool]["total_score"] += score

    resultats = []
    for pool, donnees in stats.items():
        occurences = donnees["occurences"]
        gain_moyen = donnees["total_gain"] / occurences
        score_moyen = donnees["total_score"] / occurences
        resultats.append({
            "pool": pool,
            "occurences": occurences,
            "gain_moyen": gain_moyen,
            "score_moyen": score_moyen,
        })

    resultats = sorted(resultats, key=lambda x: x["gain_moyen"], reverse=True)
    return resultats
