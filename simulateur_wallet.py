# simulateur_wallet.py

"""Outils de simulation d'investissement et gestion d'un wallet fictif."""

import json
import os
from datetime import datetime


SOLDE_INITIAL = 1000.0
DUREE_SIMULATION_JOURS = 7
FICHIER_WALLET = "wallet_simulation.json"
FICHIER_LOGS = "logs_simulations.txt"


def charger_solde():
    """Charge le solde simulé depuis ``FICHIER_WALLET``."""
    if not os.path.exists(FICHIER_WALLET):
        return 0.0
    try:
        with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
            data = json.load(f)
            return float(data.get("solde", 0.0))
    except Exception:
        return 0.0


def sauvegarder_solde(solde: float) -> None:
    """Sauvegarde le solde simulé dans ``FICHIER_WALLET``."""
    try:
        with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
            json.dump({"solde": float(solde)}, f, indent=2)
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder le solde : {e}")


def mettre_a_jour_solde(gain: float) -> float:
    """Ajoute ``gain`` au solde simulé puis le sauvegarde."""
    solde = charger_solde()
    solde += gain
    sauvegarder_solde(solde)
    return solde


def simuler_gains(pool: dict, montant: float = 100) -> tuple[str, float]:
    """Calcule le gain estimé sur 24h pour un montant donné."""
    try:
        apr = abs(float(pool.get("apr", 0)))
        gain = montant * (apr / 100) / 365
    except Exception:
        gain = 0.0
    gain_str = f"~{gain:.2f} € / 24h"
    return gain_str, gain


def journaliser_resultats(profil: str, solde: float, pools: list, montant: float) -> None:
    """Ajoute un récapitulatif dans ``FICHIER_LOGS``."""
    lignes = [
        "\n========================================",
        f"\U0001F4C5  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Profil : {profil} | Solde simulé : ${solde:.2f}",
    ]
    for i, pool in enumerate(pools, 1):
        gain_str, _ = simuler_gains(pool, montant)
        nom = pool.get("nom", "?")
        plateforme = pool.get("plateforme", "?")
        apr = pool.get("apr", 0)
        score = pool.get("score", 0)
        lignes.append(f"TOP {i} - {plateforme} | {nom}")
        lignes.append(f"  APR : {apr:.2f}% | Score : {score:.2f}")
        lignes.append(f"  💰 Gain estimé (24h, {montant}$ simulés) : {gain_str}")
    lignes.append("========================================\n")

    try:
        with open(FICHIER_LOGS, "a", encoding="utf-8") as f:
            for ligne in lignes:
                f.write(ligne + "\n")
    except Exception as e:
        print(f"[ERREUR] Impossible d'enregistrer les logs de simulation : {e}")

def simuler_investissement(pools):
    """
    Simule un investissement simple (1/3 sur chaque pool) sur une période définie.
    Affiche les gains estimés pour chaque pool et le total.
    """
    montant_par_pool = SOLDE_INITIAL / len(pools)
    gains = []

    print(f"\n🔢 Simulation simple sur {len(pools)} pools")
    for pool in pools:
        apr = pool.get("apr", 0)
        gain = montant_par_pool * (apr / 100) * (DUREE_SIMULATION_JOURS / 365)
        gains.append(gain)
        print(f"➡️ Pool : {pool['plateforme']} | {pool['nom']} | APR : {apr:.2f}% → Gain simulé : {gain:.2f}$")

    total_gain = sum(gains)
    print(f"\n📅 Durée : {DUREE_SIMULATION_JOURS} jours")
    print(f"💰 Gain total estimé : {total_gain:.2f}$")


# Optionnel : exécution directe en test
if __name__ == "__main__":
    # Exemple fictif si exécuté seul
    pools = [
        {"plateforme": "beefy", "nom": "NOICE-WETH", "apr": 138013.21},
        {"plateforme": "spectra-v2", "nom": "STUSD", "apr": 54046.60},
        {"plateforme": "berapaw", "nom": "BULLISHV2", "apr": 28862.79},
    ]
    simuler_investissement(pools)
