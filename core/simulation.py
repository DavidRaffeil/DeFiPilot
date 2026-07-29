# core/simulation.py – V6.0 Stress Engine

import csv
import os
import time
import logging
from datetime import datetime

FICHIER_JOURNAL = "logs/journal_gain_simule.csv"
FICHIER_SWAP_LP = "logs/journal_swaps_lp.csv"

LOGGER = logging.getLogger("DeFiPilot.V6Simulation")


def enregistrer_gain_simule(date, pool, gain, score):
    os.makedirs("logs", exist_ok=True)
    with open(FICHIER_JOURNAL, mode="a", newline="", encoding="utf-8") as fichier:
        writer = csv.writer(fichier)
        writer.writerow([date, pool, gain, score])


def afficher_gains_historique():
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

    print("Résumé des rendements journaliers :")
    for date, gain in sorted(journaux.items()):
        print(f"{date} : {gain:.4f} USDC")


def run_simulation(argv: list[str]) -> int:
    """
    Moteur minimal de stress test V6.0.
    Boucle stable avec écriture périodique.
    """

    LOGGER.info("Démarrage moteur simulation stress test V6.0")

    iteration = 0
    valeur = 100.0

    try:
        while True:
            iteration += 1

            # Petit calcul stable
            valeur *= 1.0001

            # Toutes les 100 itérations on log
            if iteration % 100 == 0:
                LOGGER.info(
                    "Iteration %d | Valeur simulée: %.4f",
                    iteration,
                    valeur,
                )

                enregistrer_gain_simule(
                    datetime.now().date().isoformat(),
                    "STRESS_POOL",
                    0.01,
                    50.0,
                )

            time.sleep(0.001)  # limite CPU volontaire

    except KeyboardInterrupt:
        LOGGER.info("Arrêt manuel du stress test (Ctrl+C)")
        return 0
    except Exception as e:
        LOGGER.exception("Erreur inattendue pendant la simulation: %s", e)
        return 1