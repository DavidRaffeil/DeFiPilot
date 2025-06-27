# generer_graphique.py – Génère un graphique d'évolution du solde simulé

import csv
import matplotlib.pyplot as plt
import os

CHEMIN_CSV = "logs/journal_gain_simule.csv"
CHEMIN_IMAGE = "resultats_simulation.png"

# Vérifie si le fichier existe
if not os.path.exists(CHEMIN_CSV):
    print("❌ Le fichier journal_gain_simule.csv est introuvable.")
    exit(1)

# Lecture des données depuis le CSV
dates = []
soldes = []

with open(CHEMIN_CSV, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        dates.append(row["datetime"])
        soldes.append(float(row["solde_simule"]))

# Génération du graphique
plt.figure(figsize=(10, 5))
plt.plot(dates, soldes, marker="o")
plt.xticks(rotation=45)
plt.xlabel("Jour")
plt.ylabel("Solde simulé (USDC)")
plt.title("Évolution du solde simulé sur 30 jours")
plt.tight_layout()
plt.grid(True)
plt.savefig(CHEMIN_IMAGE)
plt.close()

print(f"✅ Graphique généré : {CHEMIN_IMAGE}")
