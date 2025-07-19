import csv
from collections import Counter

JOURNAL_REEL_PATH = "logs/journal_gain_reel.csv"
FICHIER_RESUME = "resume_simulation.txt"

def charger_donnees():
    with open(JOURNAL_REEL_PATH, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def generer_resume(donnees):
    if not donnees:
        return "Aucune donnée disponible."

    solde_initial = float(donnees[0]["solde_avant"])
    solde_final = float(donnees[-1]["solde_apres"])
    gain_total = solde_final - solde_initial
    rendement = (gain_total / solde_initial) * 100

    pools = [ligne["pool"] for ligne in donnees]
    pool_frequente = Counter(pools).most_common(1)[0][0]
    jours_invest = sum(1 for ligne in donnees if float(ligne["gain"]) > 0)
    bonus_moyen = sum(float(l["bonus_applique"]) for l in donnees) / len(donnees)

    resume = f"""Résumé de la simulation réelle – Version V2.1

Solde initial  : {solde_initial:,.2f} USDC
Solde final    : {solde_final:,.2f} USDC
Gain total     : {gain_total:,.2f} USDC
Rendement      : {rendement:.2f} %

Nombre de jours avec investissement : {jours_invest} / {len(donnees)}
Pool la plus fréquente              : {pool_frequente}
Bonus historique moyen              : {bonus_moyen:.2f} %
"""
    return resume

def enregistrer_resume(texte):
    with open(FICHIER_RESUME, "w", encoding="utf-8") as f:
        f.write(texte)

if __name__ == "__main__":
    donnees = charger_donnees()
    resume = generer_resume(donnees)
    enregistrer_resume(resume)
    print("✅ Fichier résumé généré :", FICHIER_RESUME)
