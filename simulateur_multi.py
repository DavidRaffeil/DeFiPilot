# simulateur_multi.py

from core import profil, scoring, config_loader
import core.historique_rendements as historique_rendements
from defi_sources import defillama
from graphiques import gains_profils

SOLDE_INITIAL = 1000.0
DUREE_SIMULATION_JOURS = 7  # ← simulation sur 7 jours

def simuler_investissement(pools, solde, jours=7, pond_apr=1.0):
    montant_par_pool = solde / len(pools)
    gains = []
    for pool in pools:
        apr = pool.get("apr", 0)
        gain = montant_par_pool * (apr / 100) * (jours / 365) * pond_apr
        gains.append(gain)
    return round(sum(gains), 2)


def formater_resultats(profil_nom, top3, gain):
    texte = f"🧪 Profil : {profil_nom}\n"
    for i, pool in enumerate(top3, 1):
        texte += (f"TOP {i} : {pool['plateforme']} | {pool['nom']} | "
                  f"TVL ${pool['tvl_usd']:.2f} | APR {pool['apr']:.2f}% | "
                  f"Score {pool['score']:.2f}\n")
    texte += f"📅 Durée : {DUREE_SIMULATION_JOURS} jours\n"
    texte += f"💰 Gain estimé : {gain:.2f}$\n\n"
    return texte


def analyser_par_profil(pools, profils, callback_affichage=None):
    resultats_gains = {}
    texte_final = ""

    for nom_profil in profils:
        ponderations = profil.charger_ponderations(nom_profil)
        pools_avec_scores = scoring.calculer_scores(pools.copy(), ponderations)
        pools_triees = sorted(pools_avec_scores, key=lambda p: p["score"], reverse=True)
        top3 = pools_triees[:3]

        gain_total = simuler_investissement(
            top3,
            SOLDE_INITIAL,
            jours=DUREE_SIMULATION_JOURS,
            pond_apr=ponderations["apr"]
        )

        historique_rendements.enregistrer_resultats(nom_profil, top3, gain_total)
        resultats_gains[nom_profil] = gain_total
        texte_final += formater_resultats(nom_profil, top3, gain_total)

    # Graphe
    gains_profils.afficher_et_sauvegarder_gains(resultats_gains, duree_jours=DUREE_SIMULATION_JOURS)

    # Affichage des résultats dans l’interface si callback fourni
    if callback_affichage:
        callback_affichage(texte_final)
    else:
        print(texte_final)


def main(callback_affichage=None):
    config_loader.charger_config()
    pools = defillama.recuperer_pools()
    if not pools:
        texte = "❌ Aucune pool récupérée."
        if callback_affichage:
            callback_affichage(texte)
        else:
            print(texte)
        return

    profils_a_tester = ["prudent", "modere", "equilibre", "dynamique", "agressif"]
    analyser_par_profil(pools, profils_a_tester, callback_affichage=callback_affichage)


if __name__ == "__main__":
    main()
