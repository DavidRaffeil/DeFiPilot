import os
import json
import csv
from datetime import datetime

FICHIER_WALLET = "data/wallet_simule.json"
FICHIER_LOG = "logs/journal_top3.csv"

def charger_solde():
    if not os.path.exists(FICHIER_WALLET):
        return 0.0
    try:
        with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
            data = json.load(f)
            return float(data.get("solde", 0.0))
    except Exception:
        return 0.0

def mettre_a_jour_solde(gain):
    solde = charger_solde()
    nouveau_solde = round(solde + gain, 4)
    os.makedirs("data", exist_ok=True)
    with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
        json.dump({"solde": nouveau_solde}, f, indent=2)
    return nouveau_solde

def ligne_deja_presente(date_str):
    if not os.path.exists(FICHIER_LOG):
        return False
    with open(FICHIER_LOG, "r", encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith(date_str):
                return True
    return False

def journaliser_resultats(profil, nouveau_solde, top_pools, montants, pools_écartées):
    lignes = []
    lignes.append(f"\n📅 Résultats du jour pour le profil : {profil}")
    lignes.append(f"💼 Nouveau solde simulé : {round(nouveau_solde, 2)} USDC")
    
    lignes.append("\n🥇 TOP 3 Pools sélectionnées :")
    for i, pool in enumerate(top_pools):
        nom = pool.get("nom", "?")
        plateforme = pool.get("plateforme", "?")
        score = pool.get("score", 0)
        montant = montants[i]
        lignes.append(f"  {i+1}. {plateforme} | {nom} | Score : {score:.2f} | Montant investi : {round(montant, 2)} USDC")

    # ❌ Affichage des pools rejetées supprimé pour alléger la sortie

    for ligne in lignes:
        print(ligne)

    # Journalisation CSV
    os.makedirs("logs", exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    if ligne_deja_presente(date_str):
        return

    try:
        with open(FICHIER_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["date", "solde_simule", "top1_nom", "top1_apr", "top1_gain", "bonus_historique"])
            top1 = top_pools[0]
            writer.writerow([
                date_str,
                round(nouveau_solde, 2),
                top1.get("nom", "?"),
                top1.get("apr", "?"),
                round(montants[0] * top1.get("apr", 0) / 100 / 365, 2),
                "0.00"
            ])
    except Exception as e:
        print(f"[ERREUR] Impossible d’écrire dans le journal CSV : {e}")
