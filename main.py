# main.py – Version V1.8 (simulation multi-jours avec pondération historique)

import os
from datetime import datetime, timedelta
from defi_sources.defillama import recuperer_pools_defillama
from core.scoring import calculer_scores_et_gains
from core.profil import charger_profil_utilisateur
from core import historique

# Configuration simple
NB_JOURS_SIMULATION = 30
SOLDE_INITIAL = 1000.0
profil = charger_profil_utilisateur()
solde_simule = SOLDE_INITIAL

# Chargement de l'historique
historique_pools = historique.charger_historique()

# Journal CSV
CHEMIN_LOG = "logs/journal_gain_simule.csv"
os.makedirs("logs", exist_ok=True)
if not os.path.exists(CHEMIN_LOG):
    with open(CHEMIN_LOG, "w") as f:
        f.write("datetime,profil,solde_simule,top1_nom,top1_apr,top1_gain,top2_nom,top2_apr,top2_gain,top3_nom,top3_apr,top3_gain,gain_total\n")

# Boucle de simulation journalière
for jour in range(1, NB_JOURS_SIMULATION + 1):
    date_simulee = datetime.now() + timedelta(days=jour - 1)
    print(f"\n🔁 Simulation du jour {jour}/{NB_JOURS_SIMULATION} ({date_simulee.strftime('%Y-%m-%d')})")

    pools = recuperer_pools_defillama()
    top3, gain_total = calculer_scores_et_gains(pools, profil, solde_simule, historique_pools)

    solde_simule += gain_total

    # Mise à jour historique avec la meilleure pool
    top1_nom, top1_apr, top1_gain = top3[0]
    historique.maj_historique(historique_pools, top1_nom, top1_gain)

    # Affichage résumé
    print(f"📅 Jour {jour} – Solde : {solde_simule:.2f} USDC | Gain : +{top1_gain:.2f} | Pool top : {top1_nom} ({top1_apr:.2f} % APR)")

    # Log CSV
    line = f"{date_simulee.strftime('%Y-%m-%d')},{profil['nom']},{solde_simule:.2f}"
    for nom, apr, gain in top3:
        line += f",{nom},{apr:.2f},{gain:.2f}"
    line += f",{gain_total:.2f}\n"
    with open(CHEMIN_LOG, "a") as f:
        f.write(line)

# Sauvegarde finale de l’historique
historique.sauvegarder_historique(historique_pools)

print("\n✅ Simulation terminée.")
