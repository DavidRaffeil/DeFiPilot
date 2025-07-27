# ✅ Fichier main.py intégral avec journalisation rendement + erreurs (V2.4.2)

from core.wallet_lp import WalletLP
from core.config import config
from core.profil import charger_profil
from core.blacklist import appliquer_blacklist_temporaire
from core.historique import charger_historique
from core.scoring import calculer_score_pool
from core.simulation import simuler_gains
from core.journal import (
    enregistrer_swap_lp_csv,
    enregistrer_historique_swap_lp,
    afficher_journal_swaps_lp,
    afficher_stats_historique_swaps_lp,
    enregistrer_resume_journalier
)
from core.rendement import (
    afficher_rendements_journaliers,
    enregistrer as enregistrer_rendement  # ✅ Ajout fonction d'enregistrement
)
from core.logs_erreur import log_exception  # ✅ Nouveau module de logs d'erreurs
from defi_sources.defillama import recuperer_pools

import datetime
import logging

# Initialisation du logger
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

# Chargement du profil d'investissement
nom_profil = config.get("profil_defaut", "modéré")
profil = charger_profil(nom_profil)
logging.info(f"🏗 Profil actif : {profil['nom']} (APR {profil['ponderations']['apr']}, TVL {profil['ponderations']['tvl']})")

# Chargement du seuil dynamique et autres paramètres
seuil_invest = config.get('seuil_invest', 30000)
slippage_simule = config.get('slippage_simule', 0.005)

# Chargement de l'historique des scores
historique_scores = charger_historique()

# Initialisation du wallet LP simulé
wallet_lp = WalletLP()

# Récupération des pools
logging.info("🧪 Récupération des pools via DefiLlama")
try:
    pools = recuperer_pools()
    logging.info(f"✅ {len(pools)} pools récupérées")
except Exception as e:
    log_exception("defillama", "recuperer_pools", e)
    pools = []

# Application de la blacklist temporaire
pools_filtrees = appliquer_blacklist_temporaire(pools)

# Filtrage et scoring des pools
resultats = []
for pool in pools_filtrees:
    try:
        score = calculer_score_pool(pool, profil["ponderations"], historique_scores, profil)
        if score > seuil_invest:
            resultats.append((pool, score))
    except Exception as e:
        log_exception(pool.get("id", "unknown_pool"), "calculer_score_pool", e)

# Tri des résultats par score décroissant
resultats = sorted(resultats, key=lambda x: x[1], reverse=True)

# Simulation sur les 3 meilleures pools
top_pools = resultats[:3]
total_gain = 0

for pool, score in top_pools:
    logging.info(f"🔍 Pool sélectionnée : {pool['nom']} | Score : {score:.2f}")
    try:
        _, gain_simule = simuler_gains(pool, 1000.0)
        total_gain += gain_simule
        token_lp = f"LP-{pool['id']}"
        wallet_lp.ajouter_lp(token_lp, gain_simule)

        # ✅ Enregistrement CSV du swap LP simulé
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        token_a = pool['nom'].split("-")[0] if "-" in pool["nom"] else "TOKEN1"
        token_b = pool['nom'].split("-")[1] if "-" in pool["nom"] else "TOKEN2"
        enregistrer_swap_lp_csv(
            date_str=date_str,
            pool=pool["id"],
            token_a=token_a,
            amount_a=500.0,
            token_b=token_b,
            amount_b=500.0
        )

        # ✅ Journalisation complète dans l'historique
        enregistrer_historique_swap_lp(
            date_str=date_str,
            pool=pool["id"],
            token_a=token_a,
            amount_a=500.0,
            token_b=token_b,
            amount_b=500.0,
            score=score,
            profil=profil["nom"],
            gain_simule=gain_simule
        )

    except Exception as e:
        log_exception(pool.get("id", "unknown_pool"), "simuler_gains", e)

# ✅ Enregistrement du résumé global du jour
nb_pools = len(top_pools)
gain_moyen = total_gain / nb_pools if nb_pools > 0 else 0.0
date_str = datetime.datetime.now().strftime("%Y-%m-%d")

enregistrer_resume_journalier(
    date_str=date_str,
    profil=profil["nom"],
    nb_pools=nb_pools,
    gain_total=round(total_gain, 4),
    gain_moyen=round(gain_moyen, 4)
)

# ✅ Enregistrement dans journal_rendement.csv
solde_avant = 1000.0
solde_apres = solde_avant + total_gain
enregistrer_rendement(
    gain=total_gain,
    solde_avant=solde_avant,
    solde_apres=solde_apres,
    bonus_applique=0.00  # Bonus désactivé ici mais prêt pour usage
)

# ✅ Affichage du portefeuille LP simulé
wallet_lp.afficher_soldes()

# ✅ Affichage du journal LP du jour et stats globales
logging.info("📄 Lecture des swaps LP du jour")
afficher_journal_swaps_lp(date_str)

logging.info("📊 Statistiques historiques LP")
afficher_stats_historique_swaps_lp()

# ✅ Affichage du rendement journalier
afficher_rendements_journaliers()

logging.info("✅ Fin du cycle de simulation.")
