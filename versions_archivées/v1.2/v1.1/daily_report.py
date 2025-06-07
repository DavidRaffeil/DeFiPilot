# daily_report.py

import datetime
import os

DOSSIER_RAPPORTS = "daily_reports"

def generer_rapport_journalier(cycle, tableau, total_pools, score_moyen):
    if not os.path.exists(DOSSIER_RAPPORTS):
        os.makedirs(DOSSIER_RAPPORTS)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    nom_fichier = f"{DOSSIER_RAPPORTS}/rapport_{date_str}.txt"

    lignes = []
    lignes.append(f"📅 Rapport journalier – {date_str}")
    lignes.append(f"🔁 Cycle #{cycle}")
    lignes.append(f"📊 Pools analysées : {total_pools}")
    lignes.append(f"📈 Score moyen du jour : {round(score_moyen, 4)}")
    lignes.append("")

    top_pools = sorted(tableau, key=lambda x: x['score'], reverse=True)[:3]
    lignes.append("🔝 Top 3 pools du jour :")
    for pool in top_pools:
        lignes.append(f" - {pool['pool']} (Score : {round(pool['score'], 4)})")
    lignes.append("")

    nb_invest = sum(1 for l in tableau if l["decision"] == "INVESTIR")
    nb_desinvest = sum(1 for l in tableau if l["decision"] != "INVESTIR" and l.get("compounding"))
    
    lignes.append(f"✅ Investissements du jour : {nb_invest}")
    lignes.append(f"⚠️ Désinvestissements : {nb_desinvest}")
    lignes.append("")

    with open(nom_fichier, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))

    print(f"📁 Rapport sauvegardé dans {nom_fichier}")
