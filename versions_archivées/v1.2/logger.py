# utils/logger.py

import os
from datetime import datetime

DOSSIER_LOGS = "logs"

def sauvegarder_resume_cycle(pools_top3):
    if not os.path.exists(DOSSIER_LOGS):
        os.makedirs(DOSSIER_LOGS)

    lignes = ["🎯 TOP 3 POOLS :"]
    for i, pool in enumerate(pools_top3, 1):
        tvl_val = pool.get("tvl")
        apr_val = pool.get("apr")
        score_val = pool.get("score")

        tvl = f"${tvl_val:,.2f}" if isinstance(tvl_val, (int, float)) else "N/A"
        apr = f"{apr_val:.2f}%" if isinstance(apr_val, (int, float)) else "N/A"
        score = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else "N/A"

        lignes.append(
            f"#{i} - {pool.get('platform', 'N/A')} | {pool.get('symbol', 'N/A')} | TVL: {tvl} | APR: {apr} | Score: {score}"
        )

    contenu = "\n".join(lignes)
    fichier_path = os.path.join(DOSSIER_LOGS, "dernier_cycle.txt")
    with open(fichier_path, "w", encoding="utf-8") as f:
        f.write(contenu)
