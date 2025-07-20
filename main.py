import json
import os
import csv
from datetime import datetime
from web3 import Web3
from defi_sources.defillama import recuperer_pools
from core.scoring import calculer_score_pool
from core.profil import charger_profil_utilisateur
from core.historique import charger_historique, maj_historique, calculer_bonus
from core.blacklist import charger_blacklist
from core.rendement import enregistrer
from core.wallet import detecter_adresse_wallet
from core.seuil import ajuster_seuil

CONFIG_PATH = "config.json"
JOURNAL_TOP3_PATH = "journal_top3_enrichi.csv"
JOURNAL_REEL_PATH = "logs/journal_gain_reel.csv"
SOLDE_INITIAL = 1000
PLAFOND_GAIN_JOURNALIER = 0.20  # 20 %

def charger_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def afficher_infos_profil(profil):
    print(f"\nℹ️ INFO 🏗 Profil actif : {profil['nom']} (APR {profil['ponderations']['apr']}, TVL {profil['ponderations']['tvl']})")

def afficher_top3(top3):
    print("\n😇 Top 3 pools du jour :")
    for i, pool in enumerate(top3, start=1):
        apr = f"{pool['apr']:.2f}%" if pool['apr'] else "N/A"
        tag_lp = " [LP]" if pool.get("lp") else ""
        print(f"   {i}. {pool['id']} | {pool['plateforme']} | Score : {pool['score']:.2f} | APR : {apr}{tag_lp}")

def log_top3(top3):
    entetes = ["date", "id", "plateforme", "apr", "score", "type_pool"]
    ligne_date = datetime.now().strftime("%Y-%m-%d")
    fichier_existe = os.path.exists(JOURNAL_TOP3_PATH)

    with open(JOURNAL_TOP3_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(entetes)
        for pool in top3:
            ligne = [
                ligne_date,
                pool.get("id"),
                pool.get("plateforme"),
                round(pool.get("apr", 0), 2),
                round(pool.get("score", 0), 2),
                "LP" if pool.get("lp") else "standard"
            ]
            writer.writerow(ligne)

def log_gain_reel(date, pool, gain, solde_avant, solde_apres, bonus):
    entetes = ["date", "pool", "gain", "solde_avant", "solde_apres", "bonus_applique"]
    fichier_existe = os.path.exists(JOURNAL_REEL_PATH)
    ligne = [date, pool, round(gain, 2), round(solde_avant, 2), round(solde_apres, 2), round(bonus * 100, 2)]

    with open(JOURNAL_REEL_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(entetes)
        writer.writerow(ligne)

def date_deja_loggee(journal_path, date):
    if not os.path.exists(journal_path):
        return False
    with open(journal_path, "r", encoding="utf-8") as f:
        lignes = f.readlines()
        for ligne in lignes[1:]:
            if ligne.startswith(date):
                return True
    return False

def main():
    config = charger_config()
    mode_reel = config.get("mode_reel", False)

    if mode_reel:
        print("\n⚠️ MODE TEST RÉEL ACTIVÉ : Les transactions seront simulées comme réelles, sans envoi.\n")

    w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    adresse = detecter_adresse_wallet(w3)
    if adresse:
        print(f"💼 Wallet : {adresse}")
    else:
        print("⚠️ AVERTISSEMENT Aucune adresse de wallet détectée via Web3.")

    profil = charger_profil_utilisateur()
    afficher_infos_profil(profil)
    ponderations = profil["ponderations"]
    historique = charger_historique()
    solde = SOLDE_INITIAL
    date_aujourdhui = datetime.now().strftime("%Y-%m-%d")

    if date_deja_loggee(JOURNAL_REEL_PATH, date_aujourdhui):
        print(f"\n⛔ Le journal contient déjà une ligne pour la date {date_aujourdhui}. Aucune simulation exécutée.")
        return

    print(f"\n📅 Simulation du jour ({date_aujourdhui})")

    pools = recuperer_pools()
    blacklist = charger_blacklist()
    pools = [p for p in pools if p["id"] not in blacklist]

    if config.get("ignorer_lp", False):
        pools = [pool for pool in pools if not pool.get("lp", False)]

    for pool in pools:
        pool["score"] = calculer_score_pool(pool, ponderations, historique, profil)

    scores = [pool["score"] for pool in pools]
    seuil_score = ajuster_seuil(scores)
    print(f"   🔢 Seuil dynamique : {seuil_score}")

    pools_triees = sorted(pools, key=lambda x: x["score"], reverse=True)
    top3 = pools_triees[:3]
    afficher_top3(top3)
    log_top3(top3)

    solde_avant = solde
    bonus = calculer_bonus(historique, f"{top3[0].get('plateforme')} | {top3[0].get('nom')}")
    nom_pool = f"{top3[0].get('plateforme')} | {top3[0].get('nom')}"
    apr = top3[0]["apr"]

    if top3[0]["score"] >= seuil_score:
        gain_brut = solde * (apr / 100)
        gain = min(gain_brut, solde * PLAFOND_GAIN_JOURNALIER)
        print(f"\n💰 Pool sélectionnée : {top3[0]['id']} | APR : {apr:.2f}%")
        print(f"   ➕ Gain brut       : {gain_brut:.2f} USDC")
        print(f"   ➖ Gain plafonné   : {gain:.2f} USDC")
    else:
        gain = 0
        print("\n⛔ Aucune pool ne dépasse le seuil. Aucun investissement simulé aujourd’hui.")

    solde_apres = solde_avant + gain
    maj_historique(historique, nom_pool, gain)
    enregistrer(gain, solde_avant, solde_apres, bonus_applique=bonus)
    log_gain_reel(date_aujourdhui, nom_pool, gain, solde_avant, solde_apres, bonus)

    print(f"\n🧪 Bonus historique appliqué : {bonus * 100:.2f}%")
    print(f"\n📊 RÉSUMÉ DU JOUR")
    print(f"   Gain simulé    : {gain:.2f} USDC")
    print(f"   Solde avant    : {solde_avant:.2f} USDC")
    print(f"   Solde après    : {solde_apres:.2f} USDC")

if __name__ == "__main__":
    main()
