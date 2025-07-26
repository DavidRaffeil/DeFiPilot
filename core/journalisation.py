import os
import csv

def log_gain_simule(date, solde_avant, solde_apres, gain_journalier, gain_percent, pool, apr, tvl, score):
    """
    Enregistre les résultats journaliers simulés dans le fichier CSV journal_gain_simule.csv
    Ne duplique pas les dates déjà présentes.
    """
    chemin = "logs/journal_gain_simule.csv"
    fichier_existe = os.path.exists(chemin)

    if fichier_existe:
        with open(chemin, mode="r", encoding="utf-8") as f:
            lignes = list(csv.reader(f))
            dates_deja_log = [ligne[0] for ligne in lignes[1:] if ligne]
            if date in dates_deja_log:
                print(f"⚠️ Journal déjà existant pour {date}, aucune écriture.")
                return

    with open(chemin, mode="a", newline="", encoding="utf-8") as fichier_csv:
        writer = csv.writer(fichier_csv)

        if not fichier_existe:
            writer.writerow([
                "date", "solde_avant", "solde_apres", "gain_journalier", "gain_%", 
                "pool_selectionnee", "APR", "TVL", "score_pool"
            ])

        writer.writerow([
            date,
            round(solde_avant, 2),
            round(solde_apres, 2),
            round(gain_journalier, 2),
            round(gain_percent, 2),
            pool,
            apr,
            tvl,
            round(score, 2)
        ])
        print(f"📝 Résultat journalier enregistré pour {date}")


def afficher_resume_journalier(date, gain_journalier, gain_percent, pool, apr, tvl, score):
    """
    Affiche un résumé clair et synthétique des performances journalières.
    """
    print()
    print(f"📊 RÉSUMÉ DU JOUR ({date}) : {gain_journalier:+.2f} USDC / {gain_percent:+.2f}%")
    print(f"🥇 Pool : {pool} | APR : {apr} | TVL : {tvl} | Score : {round(score, 2)}")
