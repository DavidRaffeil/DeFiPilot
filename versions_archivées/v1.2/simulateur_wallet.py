# simulateur_wallet.py

import json
import os

FICHIER_WALLET = "wallet_simulation.json"

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
