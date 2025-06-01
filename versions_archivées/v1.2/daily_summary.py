# daily_summary.py

from datetime import datetime

def generer_resume(tableau, cycle):
    total_pools = len(tableau)
    nb_invest = sum(1 for ligne in tableau if ligne["decision"] == "INVESTIR")
    nb_desinvest = sum(1 for ligne in tableau if ligne["decision"] != "INVESTIR" and ligne.get("compounding"))
    moyenne_score = round(sum(l["score"] for l in tableau) / total_pools, 4) if total_pools else 0

    print("\n📊 Résumé du cycle")
    print("-" * 80)
    print(f"Cycle #{cycle}")
    print(f"Total de pools analysées : {total_pools}")
    print(f"Nombre d'investissements : {nb_invest}")
    print(f"Nombre de désinvestissements : {nb_desinvest}")
    print(f"Score moyen : {moyenne_score}")
    print("-" * 80 + "\n")

    # Tu peux aussi l’écrire dans un fichier résumé plus tard si besoin
