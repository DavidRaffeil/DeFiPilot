# main.py – Version V3.1 – Étape 4

import argparse
import logging
from datetime import datetime
from web3 import Web3

from core.config import charger_config, PROFILS
from core.defi_sources.defillama import recuperer_pools
from core.scoring import calculer_scores
from core.simulateur_logique import simuler_gains
from core.journal import enregistrer_top3
from core.real_wallet import get_wallet_address
from core.swap_reel import effectuer_swap_reel

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d")


def executer_test_swap_reel():
    """Effectue un test de swap réel simulé via Web3."""
    from_token = "USDC"
    to_token = "ETH"
    amount = 12.34
    dex = "uniswap"
    infura_url = "https://polygon-mainnet.infura.io/v3/f197d43d05194bb9a717a63d222e8372"
    w3 = Web3(Web3.HTTPProvider(infura_url))

    if not w3.is_connected():
        logging.error("❌ Web3 non connecté")
        return

    wallet_address = get_wallet_address()
    logging.info(f"✅ Wallet : {wallet_address}")
    resultat = effectuer_swap_reel(w3, from_token, to_token, amount, dex)
    print(resultat)


def main():
    parser = argparse.ArgumentParser(description="DeFiPilot – Bot DeFi personnel")
    parser.add_argument("--test-swap-reel", action="store_true", help="Effectuer un test de swap réel simulé")
    args = parser.parse_args()

    if args.test_swap_reel:
        print("🧪 Mode test : swap réel simulé")
        executer_test_swap_reel()
        return

    print("🚀 Lancement de DeFiPilot")

    # Charger la config et le profil actif
    config = charger_config()
    nom_profil = config.get("profil_defaut", "modere")
    profil = PROFILS[nom_profil]
    print(f"[{datetime.today().date()}] INFO 🏗 Profil actif : {nom_profil} (APR {profil['apr']}, TVL {profil['tvl']})")

    # Récupérer les pools
    pools = recuperer_pools()
    print(f"[{datetime.today().date()}] INFO ✅ {len(pools)} pools récupérées")

    # Calculer les scores avec historique vide
    historique_pools = []
    ponderations = {"apr": profil["apr"], "tvl": profil["tvl"]}
    pools_notees = calculer_scores(pools, ponderations, historique_pools, profil)
    pools_triees = sorted(pools_notees, key=lambda x: x["score"], reverse=True)
    top3 = pools_triees[:3]

    # Simulation des gains et affichage
    date_du_jour = str(datetime.today().date())
    top3_journal = []

    for pool in top3:
        nom = pool["nom"]
        apr = pool.get("apr", 0)
        _, gain = simuler_gains(pool)
        print(f"  • {nom} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")
        top3_journal.append((nom, apr, gain))

    # Journalisation
    enregistrer_top3(date_du_jour, top3_journal, nom_profil)


if __name__ == "__main__":
    main()
