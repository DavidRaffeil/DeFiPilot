import os
import json
import csv
from datetime import datetime, timedelta
from core.profil import charger_profil_utilisateur
from core.blacklist import filtrer_pools_exclues, maj_blacklist, nettoyer_blacklist
from core.simulation import simuler_gain
from core.historique import charger_historique, sauvegarder_historique, maj_historique, calculer_bonus
from defi_sources.defillama import recuperer_pools
from core.scoring import calculer_score_pool

NB_JOURS_SIMULATION = 30
SOLDE_INITIAL = 1000

profil = charger_profil_utilisateur()
print(f"ℹ️ INFO 🏗 Profil actif : {profil['nom']} (APR {profil['ponderations']['apr']}, TVL {profil['ponderations']['tvl']})")

historique = charger_historique()
blacklist = {}
solde = SOLDE_INITIAL
journal = []

def afficher_pools_exclues():
    if blacklist:
        exclues = [f"{pool} (reste {jours} jours)" for pool, jours in blacklist.items() if jours > 0]
        if exclues:
            print("🔒 Pools exclues temporairement : " + ", ".join(exclues))

for jour in range(1, NB_JOURS_SIMULATION + 1):
    date_simulation = datetime(2025, 6, 28) + timedelta(days=jour)
    print(f"\n💁 Simulation du jour {jour}/30 ({date_simulation.date()})")

    pools = recuperer_pools()

    for pool in pools:
        if "name" not in pool:
            pool["name"] = pool.get("id", "inconnu")

    pools_valides = filtrer_pools_exclues(pools, blacklist)

    if not pools_valides:
        afficher_pools_exclues()
        print("⚠️ Aucune pool valide après filtrage. Passage au jour suivant.")
        blacklist = nettoyer_blacklist(blacklist)
        continue

    meilleures_pools = sorted(
        pools_valides,
        key=lambda pool: calculer_score_pool(pool, profil["ponderations"], historique, profil),
        reverse=True
    )
    top_pool = meilleures_pools[0]

    bonus = calculer_bonus(historique, top_pool['name'], profil['historique_max_bonus'], profil['historique_max_malus'])
    gain = simuler_gain(top_pool['apr'], solde, bonus)
    solde += gain

    print(f"🔕 Jour {jour} – Solde : {solde:.2f} USDC | Gain : +{gain:.2f} | Pool top : {top_pool.get('dex', 'unknown')} | {top_pool.get('symbol', 'unknown')} ({top_pool['apr']} % APR)")
    print(f"   🧪 Bonus historique appliqué : {bonus * 100:.2f}%")

    maj_historique(historique, top_pool['name'], gain)
    sauvegarder_historique(historique)

    journal.append({
        "datetime": date_simulation.strftime("%Y-%m-%d"),
        "solde_simule": round(solde, 2),
        "top1_nom": top_pool['name'],
        "top1_apr": top_pool['apr'],
        "top1_gain": round(gain, 2),
        "bonus_historique": round(bonus * 100, 2)
    })

    if gain < 0.5:
        print(f"⛔ Pool exclue temporairement : {top_pool.get('dex', 'unknown')} | {top_pool.get('symbol', 'unknown')} pour 5 jours")
        blacklist = maj_blacklist(blacklist, top_pool['name'])

    blacklist = nettoyer_blacklist(blacklist)

# Sauvegarde du journal en CSV
os.makedirs("logs", exist_ok=True)
with open("logs/journal_gain_simule.csv", "w", newline="") as f:
    fieldnames = ["datetime", "solde_simule", "top1_nom", "top1_apr", "top1_gain", "bonus_historique"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(journal)

print("\n✅ Simulation terminée.")
