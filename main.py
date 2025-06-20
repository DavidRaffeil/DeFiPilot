# main.py (version finale avec ordre corrigé)
import logging
from datetime import datetime
import csv

from core import config_loader, profil
from core import scoring, blacklist
from defi_sources import defillama
import simulateur_wallet
import real_wallet


def main():
    # Initialiser le logging dès le début
    logging.basicConfig(
        filename="logs/journal.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    logging.info("🔁 Démarrage d’un nouveau cycle d’analyse DeFiPilot")

    # Charger la configuration
    config_loader.charger_config()
    print("DEBUG: mode_reel =", config_loader.get("mode_reel", False))

    # Lecture du mode réel depuis la config (après chargement)
    mode_reel = config_loader.get("mode_reel", False)

    # Journaliser séparément le mode actif dans mode.log
    with open("logs/mode.log", "a") as mode_file:
        mode_file.write(f"{datetime.now().isoformat()} | mode_reel = {mode_reel}\n")

    if mode_reel:
        print("\n❗❗❗ ATTENTION : MODE RÉEL ACTIVÉ ❗❗❗")
        logging.info("⚠️ Mode réel activé — attention, des transactions pourraient être effectuées.")
    else:
        logging.info("🔒 Mode réel désactivé — exécution en simulation uniquement.")

    adresse_wallet = real_wallet.detecter_adresse_wallet()
    if adresse_wallet:
        logging.info(f"🔑 Adresse EVM détectée : {adresse_wallet}")
    else:
        logging.warning("⚠️ Aucune adresse de wallet détectée.")

    profil_defaut = config_loader.get("profil_defaut", "modéré")
    ponderations = profil.charger_ponderations(profil_defaut)
    logging.info(f"🏗 Profil actif : {profil_defaut} "
                 f"(APR {ponderations['apr']}, TVL {ponderations['tvl']})")

    pools = defillama.recuperer_pools()
    if not pools:
        logging.warning("Aucune pool récupérée. Fin du cycle.")
        return

    pools_filtrees = blacklist.filtrer_blacklist(pools)
    pools_notees = scoring.calculer_scores(pools_filtrees, ponderations)
    top3 = sorted(pools_notees, key=lambda x: x['score'], reverse=True)[:3]

    print("\n🏆 TOP 3 POOLS SÉLECTIONNÉES :")
    for i, pool in enumerate(top3, start=1):
        dex = pool.get("plateforme", "N/A")
        pair = pool.get("nom", "N/A")
        tvl = pool.get("tvl_usd", 0)
        apr = pool.get("apr", 0)
        score = pool.get("score", 0)

        print(f"{i}. {dex} | {pair} | TVL: {tvl} | APR: {apr} | SCORE: {score}")

        logging.info(f"TOP {i} | {dex} | {pair} | TVL: {tvl} | APR: {apr} | Score: {score}")


if __name__ == "__main__":
    main()
