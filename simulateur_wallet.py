"""Outils de simulation d'investissement et gestion d'un wallet fictif."""

import json
import os
import csv
from datetime import datetime
from core.seuil import ajuster_seuil
import matplotlib.pyplot as plt

SOLDE_INITIAL = 1000.0
DUREE_SIMULATION_JOURS = 7
FICHIER_WALLET = "wallet_simulation.json"
FICHIER_LOGS = "logs_simulations.txt"
FICHIER_CSV = "journal_simulation.csv"
FICHIER_PNG = "resultats_simulation.png"

PROFILS = {
    "prudent": {"tvl": 0.9, "apr": 0.1},
    "modéré": {"tvl": 0.7, "apr": 0.3},
    "agressif": {"tvl": 0.3, "apr": 0.7}
}


def charger_solde():
    if not os.path.exists(FICHIER_WALLET):
        return 0.0
    try:
        with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
            data = json.load(f)
            return float(data.get("solde", 0.0))
    except Exception:
        return 0.0


def sauvegarder_solde(solde: float) -> None:
    try:
        with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
            json.dump({"solde": float(solde)}, f, indent=2)
    except Exception as e:
        print(f"[ERREUR] Échec de la sauvegarde du solde : {e}")


def journaliser_resultats(profil: str, solde: float, pools: list, montants: list, pools_écartées: list = None):
    lignes = []
    lignes.append(f"\n📊 Résultats de simulation ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    lignes.append(f"Profil : {profil} | Solde simulé : {solde:.2f}$")
    lignes.append("Montants investis pondérés selon les scores :\n")

    for i, pool in enumerate(pools, 1):
        gain_str, _ = simuler_gains(pool, montants[i - 1])
        nom = pool.get("nom", "?")
        plateforme = pool.get("plateforme", "?")
        apr = pool.get("apr", 0)
        score = pool.get("score", 0)
        montant = montants[i - 1]
        lignes.append(f"TOP {i} - {plateforme} | {nom}")
        lignes.append(f"  APR : {apr:.2f}% | Score : {score:.2f}")
        lignes.append(f"  Montant investi : {montant:.2f}$")
        lignes.append(f"  💰 Gain estimé : {gain_str}")

    if pools_écartées:
        lignes.append("\n❌ Pools écartées (score trop bas) :")
        for pool in pools_écartées:
            nom = pool.get("nom", "?")
            plateforme = pool.get("plateforme", "?")
            score = pool.get("score", 0)
            lignes.append(f"  ⚠️ {plateforme} | {nom} | Score : {score:.2f}")

    lignes.append("========================================\n")

    try:
        with open(FICHIER_LOGS, "a", encoding="utf-8") as f:
            for ligne in lignes:
                f.write(ligne + "\n")
    except Exception as e:
        print(f"[ERREUR] Impossible d'enregistrer les logs de simulation : {e}")


def journaliser_csv(profil: str, score_moyen: float, seuil: float, pools: list, montants: list, gains: list, gain_total: float):
    existe = os.path.exists(FICHIER_CSV)
    with open(FICHIER_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not existe:
            writer.writerow([
                "date", "profil", "score_moyen", "seuil",
                "pools", "montants_investis", "gains_simulés", "gain_total"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            profil,
            f"{score_moyen:.2f}",
            f"{seuil:.2f}",
            ", ".join([p.get("nom", "?") for p in pools]),
            ", ".join([f"{m:.2f}" for m in montants]),
            ", ".join([f"{g:.2f}" for g in gains]),
            f"{gain_total:.2f}"
        ])


def generer_graphique(pools, montants, gains, profil="modéré"):
    noms = [p.get("nom", "?") for p in pools]
    x = range(len(pools))

    plt.figure(figsize=(10, 6))
    plt.bar(x, montants, width=0.4, label="Montants investis", align='center')
    plt.bar(x, gains, width=0.4, label="Gains simulés", align='edge')
    plt.xticks(x, noms, rotation=45)
    plt.xlabel("Pools")
    plt.ylabel("$")
    plt.title(f"Simulation DeFiPilot ({profil}) : Investissement vs Gain")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"resultats_simulation_{profil}.png")
    plt.close()


def simuler_gains(pool: dict, montant: float):
    apr = pool.get("apr", 0)
    gain = montant * (apr / 100) * (DUREE_SIMULATION_JOURS / 365)
    return f"{gain:.2f}$", gain


def simuler_investissement(pools, profil="modéré"):
    scores = [pool.get("score", 0) for pool in pools]
    seuil_invest = ajuster_seuil(scores)
    score_moyen = sum(scores) / len(scores)

    pools_valides = [p for p in pools if p.get("score", 0) >= seuil_invest]
    pools_écartées = [p for p in pools if p.get("score", 0) < seuil_invest]

    print(f"\n🔢 Simulation {profil} sur {len(pools_valides)} pools (score ≥ {seuil_invest})")

    if pools_écartées:
        print(f"\n❌ Pools écartées (score < seuil {seuil_invest}):")
        for pool in pools_écartées:
            print(f"  ⚠️ {pool['plateforme']} | {pool['nom']} | Score : {pool['score']:.2f}")

    if not pools_valides:
        print("⚠️ Aucune pool ne dépasse le seuil recommandé. Aucun investissement simulé.")
        return

    total_score = sum(p.get("score", 0) for p in pools_valides)
    montants_pondérés = [
        (p.get("score", 0) / total_score) * SOLDE_INITIAL for p in pools_valides
    ]

    gains = []

    for pool, montant in zip(pools_valides, montants_pondérés):
        apr = pool.get("apr", 0)
        score = pool.get("score", 0)
        gain = montant * (apr / 100) * (DUREE_SIMULATION_JOURS / 365)
        gains.append(gain)
        print(f"➡️ {pool['plateforme']} | {pool['nom']} | APR : {apr:.2f}% | Score : {score:.2f} | Investi : {montant:.2f}$ → Gain : {gain:.2f}$")

    total_gain = sum(gains)
    print(f"\n📅 Durée : {DUREE_SIMULATION_JOURS} jours")
    print(f"🎯 Seuil d'investissement suggéré : {seuil_invest} (score moyen : {score_moyen:.2f})")
    print(f"💰 Gain total estimé : {total_gain:.2f}$")

    journaliser_resultats(profil, SOLDE_INITIAL, pools_valides, montants_pondérés, pools_écartées)
    journaliser_csv(profil, score_moyen, seuil_invest, pools_valides, montants_pondérés, gains, total_gain)
    generer_graphique(pools_valides, montants_pondérés, gains, profil)


def simuler_tous_profils(pools):
    for profil in PROFILS:
        print("\n" + "="*40 + f"\n▶ Profil en cours : {profil}\n" + "="*40)
        simuler_investissement(pools, profil=profil)


if __name__ == "__main__":
    pools = [
        {"plateforme": "beefy", "nom": "NOICE-WETH", "apr": 138013.21, "score": 37812.54},
        {"plateforme": "spectra-v2", "nom": "STUSD", "apr": 54046.60, "score": 14807.12},
        {"plateforme": "berapaw", "nom": "BULLISHV2", "apr": 28862.79, "score": 50.0},
    ]
    simuler_tous_profils(pools)
