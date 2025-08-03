# main.py
# 🧩 Version : V2.8 – Nettoyée (suppression DEBUG)

from core.defi_sources import defillama
from core import scoring, journal, simulateur_logique
from core.profil import PROFIL_ACTIF
import datetime

def main():
    print("🚀 Lancement de DeFiPilot")

    profil_utilisateur = scoring.charger_profil_utilisateur()
    print(f"[{datetime.date.today()}] INFO 🏗 Profil actif : {PROFIL_ACTIF} (APR {profil_utilisateur['ponderations']['apr']}, TVL {profil_utilisateur['ponderations']['tvl']})")

    pools = defillama.recuperer_pools()
    print(f"[{datetime.date.today()}] INFO ✅ {len(pools)} pools récupérées")

    historique_pools = {}

    for pool in pools:
        gain_affiche, gain_valeur = simulateur_logique.simuler_gains(pool)
        pool["gain_simule"] = gain_valeur
        pool["gain_affiche"] = gain_affiche

    solde_usdc = 5000.00
    resultats, gain_total = scoring.calculer_scores_et_gains(pools, profil_utilisateur, solde_usdc, historique_pools)

    print(f"\n📊 Résumé du {datetime.date.today()} – Profil : {PROFIL_ACTIF}")
    for pool, score in resultats:
        nom = f"{pool['plateforme']} | {pool['nom']}"
        apr = pool.get("apr", 0)
        gain = pool.get("gain_simule", 0)
        print(f"  • {nom} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")

    for pool, score in resultats[:3]:
        nom_pool = f"{pool['plateforme']} | {pool['nom']}"
        apr_farming = pool.get("farming_apr", 10.0)
        montant_lp = round(pool["gain_simule"] / 2, 4)
        montant_farm = simulateur_logique.simuler_gain_farming_lp(montant_lp, apr_farming)
        solde_usdc += pool["gain_simule"]
        print(f"💰 Gain simulé : +{pool['gain_simule']:.2f} $ USDC → Nouveau solde : {solde_usdc:.2f} $ USDC")
        print(f"🗓️ LP simulé reçu : {montant_lp:.4f} LP-{pool['nom']}")
        print(f"🌾 Farming LP simulé : {montant_farm:.4f} $ USDC générés avec {apr_farming:.2f}% APR")

    print(f"\n📊 Solde LP simulé :")
    for pool, score in resultats[:3]:
        montant_lp = round(pool["gain_simule"] / 2, 4)
        print(f" - LP-{pool['nom']} : {montant_lp:.4f}")

if __name__ == "__main__":
    main()
