# core/investisseur.py

from core import logger

def simuler_investissement(pool):
    """
    Simule un investissement dans une pool.
    Affiche les informations pertinentes pour le log.
    """
    plateforme = pool.get("plateforme", "inconnue")
    nom = pool.get("nom", "inconnue")
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)
    score = pool.get("score", 0)

    logger.log_info("💰 Simulation d’investissement dans la pool suivante :")
    logger.log_info(f"    ➤ Plateforme : {plateforme}")
    logger.log_info(f"    ➤ Nom         : {nom}")
    logger.log_info(f"    ➤ TVL         : ${tvl:,.2f}")
    logger.log_info(f"    ➤ APR         : {apr:.2f}%")
    logger.log_info(f"    ➤ Score       : {score}")
