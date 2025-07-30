# main.py – Version V2.5 stable avec simulation farming LP

import logging
from datetime import datetime
from core import scoring, journal
from core.wallet_simule import WalletSimule
from core.wallet_lp import WalletLP
from core.defi_sources import defillama

print("🚀 Lancement de DeFiPilot")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d"
)

profil = "modere"
logging.info(f"🏗 Profil actif : {profil} (APR {scoring.PROFILS[profil]['apr']}, TVL {scoring.PROFILS[profil]['tvl']})")

wallet = WalletSimule()
wallet_lp = WalletLP()

logging.info("🧪 Récupération des pools via DefiLlama")
pools = defillama.recuperer_pools()
logging.info(f"✅ {len(pools)} pools récupérées")

historique_pools = journal.lire_historique_pools()
pools_tries = scoring.trier_pools(pools, profil, historique_pools)

solde_disponible = wallet.get_solde()
profil_data = scoring.charger_profil_utilisateur()
resultats, gain_total = scoring.calculer_scores_et_gains(pools_tries, profil_data, solde_disponible, historique_pools)

date_du_jour = datetime.now().strftime("%Y-%m-%d")
print(f"\n📊 Résumé du {date_du_jour} – Profil : {profil}")
for nom, apr, gain in resultats:
    print(f"  • {nom} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")

journal.enregistrer_resume_journalier(date_du_jour, profil, len(resultats), gain_total, round(gain_total / len(resultats), 4))

from core.scoring import simuler_gain_farming_lp
from core.journal import enregistrer_farming

for pool in pools_tries[:3]:
    nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
    apr = pool.get("apr", 0)
    gain = round((solde_disponible * apr / 100) / 365, 2)
    solde_avant, gain_simule, nouveau_solde = wallet.investir(gain)
    print(f"💰 Gain simulé : +{gain_simule:.2f} $ USDC → Nouveau solde : {nouveau_solde:.2f} $ USDC")

    if pool.get("lp"):
        montant_lp = gain
        farming_apr = pool.get("farming_apr", 0)
        gain_farming = simuler_gain_farming_lp(montant_lp, farming_apr)
        journal.enregistrer_farming(date_du_jour, pool.get("nom"), pool.get("plateforme"), montant_lp, farming_apr, gain_farming, profil)
        print(f"🌾 Farming LP simulé : {gain_farming:.4f} $ USDC générés avec {farming_apr:.2f}% APR")

wallet_lp.afficher_soldes()
