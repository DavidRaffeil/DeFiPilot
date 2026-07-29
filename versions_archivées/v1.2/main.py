# main.py

import sys
import os
import json
import time
from datetime import datetime

# Ajout du chemin du dossier courant pour les imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Chrono pour mesurer la durée du cycle
start_time = time.time()

from core import config_loader
from core import logger
from core import profil
from core import scoring
from core import blacklist
from core import historique
from core import investisseur

from defi_sources import defillama

# Chargement de la configuration utilisateur
try:
    config_loader.charger_config()
    logger.log_succes("Fichier de configuration chargé avec succès.")
except Exception as e:
    logger.log_erreur(f"Erreur lors du chargement de la configuration : {e}")
    exit(1)

# Initialisation du cycle
logger.log_info("🔁 Démarrage d’un nouveau cycle d’analyse DeFiPilot")
profil_actif = config_loader.get("profil_defaut", "modéré")
ponderations = profil.charger_ponderations(profil_actif)

logger.log_info(f"🏗 Profil actif : {profil_actif} (APR {ponderations['apr']}, TVL {ponderations['tvl']})")

# Récupération des pools via DefiLlama
try:
    logger.log_info("🧪 Mode Dryrun : récupération des pools via DefiLlama")
    pools = defillama.recuperer_pools()
    logger.log_succes(f"{len(pools)} pools récupérées avec succès.")
except Exception as e:
    logger.log_erreur(f"Échec de récupération des pools : {e}")
    exit(1)

# Filtrage des pools blacklistées
pools_filtrees = blacklist.filtrer_blacklist(pools)
nb_blacklistees = len(pools) - len(pools_filtrees)
logger.log_info(f"🛑 {nb_blacklistees} pool(s) ignorée(s) car blacklistée(s).")

# Filtres APR / TVL minimaux
tvl_min = config_loader.get("tvl_min", 0)
apr_min = config_loader.get("apr_min", 0)

pools_filtrees = [
    pool for pool in pools_filtrees
    if pool["tvl_usd"] >= tvl_min and pool["apr"] >= apr_min
]

logger.log_info(f"🧹 Après filtres TVL ≥ {tvl_min} et APR ≥ {apr_min} : {len(pools_filtrees)} pool(s) restante(s)")

# Calcul des scores pondérés
logger.log_info("📊 Calcul des scores (profil pondéré) :")
pools_scored = scoring.calculer_scores(pools_filtrees, ponderations)
pools_scored = sorted(pools_scored, key=lambda x: x["score"], reverse=True)

# Sélection du TOP 3
top3 = pools_scored[:3]
for i, pool in enumerate(top3, start=1):
    message = (
        f"TOP {i} : {pool['plateforme']} | {pool['nom']} | "
        f"TVL ${pool['tvl_usd']:,} | APR {pool['apr']:.2f}% | Score {pool['score']:.2f}"
    )
    logger.log_succes(message)
    investisseur.simuler_investissement(pool)

# Sauvegarde dans resultats_top3.json
try:
    with open("resultats_top3.json", "w", encoding="utf-8") as f:
        json.dump(top3, f, indent=4, ensure_ascii=False)
    logger.log_succes("💾 Données TOP 3 enregistrées dans resultats_top3.json")
except Exception as e:
    logger.log_erreur(f"Erreur lors de la sauvegarde du fichier JSON : {e}")

# Ajout à l’historique CSV
try:
    historique.ajouter_au_csv(top3)
    logger.log_succes("📈 Historique mis à jour dans historique_cycles.csv")
except Exception as e:
    logger.log_erreur(f"Erreur lors de l’écriture dans le fichier historique : {e}")

# Résumé de fin de cycle
duree_cycle = round(time.time() - start_time, 2)
logger.log_info("📄 Résumé du cycle :")
logger.log_info(f"- Pools analysées : {len(pools)}")
logger.log_info(f"- Pools sélectionnées : {len(top3)}")
logger.log_info(f"- Meilleure pool : {top3[0]['plateforme']} | {top3[0]['nom']} | Score {top3[0]['score']}")
logger.log_info(f"- Durée du cycle : {duree_cycle} secondes")

# Fin du cycle
logger.log_info("✅ Fin du cycle d’analyse DeFiPilot.")
