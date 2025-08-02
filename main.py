# main.py – Version V2.6+ avec journal LP cumulatif et mode --simulate

import argparse
import builtins
import logging
import random
from datetime import datetime

from core import scoring, journal
from core.wallet_simule import WalletSimule
from core.wallet_lp import WalletLP
from core.defi_sources import defillama
from core.scoring import simuler_gain_farming_lp
from core.journal import enregistrer_farming
from core.journal_lp_cumul import enregistrer_lp_cumul

# Argument --simulate (mode silencieux)
parser = argparse.ArgumentParser(description="DeFiPilot")
parser.add_argument("--simulate", action="store_true", help="Exécute en mode silencieux")
args = parser.parse_args()
mode_silencieux = args.simulate

# Désactiver tous les print si mode silencieux
if mode_silencieux:
    builtins.print = lambda *args, **kwargs: None

# Logger configuré selon le mode
logging.basicConfig(
    level=logging.CRITICAL if mode_silencieux else logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d"
)

print("🚀 Lancement de DeFiPilot")

# Chargement du profil
profil = "modere"
logging.info(f"🏗 Profil actif : {profil} (APR {scoring.PROFILS[profil]['apr']}, TVL {scoring.PROFILS[profil]['tvl']})")

# Initialisation des wallets
wallet = WalletSimule()
wallet_lp = WalletLP()

# Récupération des pools
logging.info("🧪 Récupération des pools via DefiLlama")
pools = defillama.recuperer_pools()
logging.info(f"✅ {len(pools)} pools récupérées")

# Traitement
historique_pools = journal.lire_historique_pools()
pools_tries = scoring.trier_pools(pools, profil, historique_pools)
solde_disponible = wallet.get_solde()
profil_data = scoring.charger_profil_utilisateur()
resultats, gain_total = scoring.calculer_scores_et_gains(
    pools_tries, profil_data, solde_disponible, historique_pools
)

# Journalisation du résumé
date_du_jour = datetime.now().strftime("%Y-%m-%d")
print(f"\n📊 Résumé du {date_du_jour} – Profil : {profil}")
for nom, apr, gain in resultats:
    print(f"  • {nom} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")

journal.enregistrer_resume_journalier(
    date_du_jour, profil, len(resultats), gain_total,
    round(gain_total / len(resultats), 4)
)

# Simulation LP pour les 3 meilleures pools
for pool in pools_tries[:3]:
    nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
    apr = pool.get("apr", 0)
    gain = round((solde_disponible * apr / 100) / 365, 2)
    solde_avant, gain_simule, nouveau_solde = wallet.investir(gain)
    print(f"💰 Gain simulé : +{gain_simule:.2f} $ USDC → Nouveau solde : {nouveau_solde:.2f} $ USDC")

    if pool.get("lp"):
        montant_lp = gain
        tokens = pool.get("nom", "").split("-")
        token1 = tokens[0]
        token2 = tokens[1] if len(tokens) > 1 else tokens[0]
        slippage = random.uniform(-0.005, 0.005)

        journal.enregistrer_swap_lp(
            date_du_jour,
            pool.get("nom"),
            pool.get("plateforme"),
            montant_lp,
            token1,
            token2,
            slippage,
            profil,
        )

        montant_token1 = (montant_lp / 2) * (1 - slippage)
        montant_token2 = (montant_lp / 2) * (1 - slippage)
        montant_lp_tokens = min(montant_token1, montant_token2)
        lp_token = f"LP-{token1}-{token2}"
        wallet_lp.ajouter(lp_token, montant_lp_tokens)

        journal.enregistrer_lp_tokens(
            date_du_jour,
            pool.get("nom"),
            pool.get("plateforme"),
            lp_token,
            montant_lp_tokens,
            profil,
        )

        print(f"📅 LP simulé reçu : {montant_lp_tokens:.4f} {lp_token}")

        farming_apr = pool.get("farming_apr", 0)
        gain_farming = simuler_gain_farming_lp(montant_lp_tokens, farming_apr)
        enregistrer_farming(
            date_du_jour,
            pool.get("nom"),
            pool.get("plateforme"),
            montant_lp_tokens,
            farming_apr,
            gain_farming,
            profil,
        )

        enregistrer_lp_cumul(
            pool.get("nom"),
            pool.get("plateforme"),
            montant_lp_tokens,
            gain_farming,
        )

        print(f"🌾 Farming LP simulé : {gain_farming:.4f} $ USDC générés avec {farming_apr:.2f}% APR")

# Affichage final des soldes LP simulés
wallet_lp.afficher_soldes()
