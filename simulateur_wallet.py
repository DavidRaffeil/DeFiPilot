# simulateur_wallet.py

import json
import os
from datetime import datetime

FICHIER_WALLET = "wallet_simulation.json"
FICHIER_LOGS = "logs_simulations.txt"

def charger_solde():
    """Charge le solde simulé depuis le fichier JSON, ou initialise à 0."""
    if not os.path.exists(FICHIER_WALLET):
        return 0.0
    with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
        donnees = json.load(f)
        return donnees.get("solde", 0.0)

def sauvegarder_solde(solde):
    """Sauvegarde le solde simulé dans le fichier JSON."""
    with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
        json.dump({"solde": solde}, f, indent=2)

def mettre_a_jour_solde(gain):
    """Ajoute un gain au solde simulé et le sauvegarde."""
    solde = charger_solde()
    solde += gain
    sauvegarder_solde(solde)
    return solde  # pour affichage ou log

def simuler_gains(pool, montant=100):
    """
    Calcule le gain estimé sur 24h à partir de l'APR annuel d'une pool.

    Args:
        pool (dict) : Dictionnaire contenant au minimum la clé 'apr'.
        montant (float) : Montant investi simulé (en euros ou dollars).

    Returns:
        tuple : (str lisible, float brut)
            - str lisible ex : "~3.25 € / 24h"
            - float brut ex : 3.25
    """
    try:
        apr = abs(float(pool.get("apr", 0)))  # APR en %, sécurité en positif
        taux_journalier = apr / 100 / 365
        gain = montant * taux_journalier
        return f"~{gain:.2f} € / 24h", gain
    except Exception as e:
        return f"(Erreur simulation : {e})", 0.0

def journaliser_resultats(profil, solde, pools, montant=100):
    """
    Enregistre les résultats d'une simulation dans un fichier texte.
    """
    try:
        with open(FICHIER_LOGS, "a", encoding="utf-8") as f:
            f.write("\n" + "="*40 + "\n")
            f.write(f"🗓️  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Profil : {profil} | Solde simulé : ${solde:.2f}\n")
            for i, pool in enumerate(pools, 1):
                gain_lisible, _ = simuler_gains(pool, montant)
                f.write(f"TOP {i} - {pool['plateforme']} | {pool['nom']}\n")
                f.write(f"  APR : {pool['apr']:.2f}% | Score : {pool['score']:.2f}\n")
                f.write(f"  💰 Gain estimé (24h, {montant}$ simulés) : {gain_lisible}\n")
            f.write("="*40 + "\n")
    except Exception as e:
        print(f"Erreur lors de la journalisation : {e}")
