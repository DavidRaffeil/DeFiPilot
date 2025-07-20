# generer_graphique_seuil.py

import csv
import matplotlib.pyplot as plt

JOURNAL_SEUIL_PATH = "journal_seuil.csv"
OUTPUT_IMAGE_PATH = "graphique_seuils.png"

def generer_graphique_seuil():
    jours = []
    seuils = []

    with open(JOURNAL_SEUIL_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            jours.append(int(ligne["jour"]))
            seuils.append(float(ligne["seuil"]))

    plt.figure(figsize=(10, 5))
    plt.plot(jours, seuils, marker="o", linestyle="-")
    plt.title("Évolution du seuil d’investissement sur 30 jours")
    plt.xlabel("Jour")
    plt.ylabel("Seuil (score)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE_PATH)
    plt.show()

if __name__ == "__main__":
    generer_graphique_seuil()
