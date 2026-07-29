import json
import os
from datetime import datetime

DOSSIER_STATS = "cycle_stats"

def sauvegarder_stats_cycle(cycle_num, tableau, profil):
    if not os.path.exists(DOSSIER_STATS):
        os.makedirs(DOSSIER_STATS)

    total = len(tableau)
    score_total = sum(row["score"] for row in tableau)
    score_moyen = round(score_total / total, 4) if total else 0
    nb_investies = sum(1 for row in tableau if "INVESTIR" in row["decision"].upper())

    donnees = {
        "cycle": cycle_num,
        "total_pools": total,
        "score_moyen": score_moyen,
        "nombre_investies": nb_investies,
        "profil": profil,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    nom_fichier = f"{DOSSIER_STATS}/cycle_{cycle_num:03}.json"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=2)
