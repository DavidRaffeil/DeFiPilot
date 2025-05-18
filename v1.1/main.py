import os
import sys
import time
import threading
import msvcrt  # Pour Windows (écoute clavier)

# 🔍 Check des fichiers essentiels avant démarrage
from startup_check import verifier_elements
verifier_elements()

# 📦 Import des modules principaux
from scanner_pools import get_pools
from strategy import make_decision, afficher_profil
from logger import init_log_file, log_decision
from executor import investir, desinvestir
from portfolio import (
    est_investi,
    ajouter_pool,
    retirer_pool,
    init_portefeuille,
    sauvegarder_snapshot_portefeuille,
    exporter_portefeuille,
    snapshot_portefeuille
)
from compounder import get_compounding_rate
from config_loader import charger_config, get
from settings import set_profil
from error_logger import log_erreur
from daily_summary import generer_resume
from stats import Statistiques
from daily_report import generer_rapport_journalier
from profil_loader import charger_profil
from daily_reports.journal_logger import log_journal
from cycle_stats import sauvegarder_stats_cycle

# 🧠 Mémoire temporaire
blacklist = {}
user_input = {}

# 🎧 Écoute clavier (q = quit, p = pause)
def ecoute_clavier():
    while True:
        if msvcrt.kbhit():
            touche = msvcrt.getwch()
            if touche == 'q':
                user_input["stop"] = True
                print("🛑 Arrêt demandé (touche q).")
                break
            elif touche == 'p':
                user_input["pause"] = True
                print("⏸️ Pause demandée (touche p).")

# 🔒 Blacklist temporaire
def enregistrer_rejet(pool_name, cycle_actuel):
    duree = get("nb_cycles_blacklist", 3)
    expiration = cycle_actuel + duree
    blacklist[pool_name] = expiration
    print(f"🚫 Pool '{pool_name}' blacklistée jusqu'au cycle {expiration}")

def est_blacklistee(pool_name, cycle_actuel):
    expiration = blacklist.get(pool_name)
    return expiration and cycle_actuel <= expiration

# 🧭 Aide commandes utilisateur
def afficher_commandes_disponibles():
    print("\n🧭 Commandes clavier disponibles :")
    print("-" * 40)
    print("q           → Quitter proprement le bot")
    print("p           → Mettre en pause le bot")
    print("-" * 40 + "\n")

# 📊 Affichage du tableau des décisions
def afficher_tableau(donnees):
    print("\n📋 Résumé des décisions")
    print("-" * 80)
    print(f"{'Pool':<15} {'Score':<8} {'Décision':<20} {'Taux compounding'}")
    print("-" * 80)
    for ligne in donnees:
        print(f"{ligne['pool']:<15} {round(ligne['score'], 4):<8} {ligne['decision']:<20} {ligne.get('compounding', '-')}")  
    print("-" * 80 + "\n")

# 🚀 Lancement principal du bot
def lancer_bot():
    print("✅ Démarrage de DeFiPilot")
    global stats, user_input
    stats = Statistiques()
    cycle = 1

    # Chargement profil
    profil_defaut = get("profil_defaut", "modéré")
    profil_data = charger_profil(profil_defaut)

    print(f"👤 Profil actif : {profil_data.get('nom', 'inconnu')}")
    print(f"➡️  Pondérations : APR={profil_data['apy']} | TVL={profil_data['tvl']} | Durée={profil_data['volume']}")
    print(f"🌟 Seuil de rentabilité minimum : {profil_data.get('seuil_score', 0.6)}")

    mode_simulation = get("mode_simulation", True)
    if mode_simulation:
        print("🧪 Mode simulation ACTIVÉ – Aucune action réelle ne sera effectuée.")
        log_journal("🧪 Mode simulation activé")

    user_input = {
        "stop": False,
        "pause": False,
        "interval": get("interval_secondes", 600),
        "profil_actif": profil_data,
        "seuil_score": profil_data.get("seuil_score", 0.6),
        "nombre_max": profil_data.get("max_pools", 3),
        "dryrun": 2  # ⛔ Limitation temporaire à 2 cycles
    }

    if len(sys.argv) >= 3 and sys.argv[1] == "dryrun":
        try:
            user_input["dryrun"] = int(sys.argv[2])
            print(f"🔁 Mode dryrun activé pour {user_input['dryrun']} cycles.")
        except ValueError:
            print("⚠️ Valeur invalide pour dryrun. Ignorée.")

    while True:
        try:
            if user_input["dryrun"] > 0 and cycle > user_input["dryrun"]:
                print(f"✅ Dryrun terminé après {cycle - 1} cycles. Le bot s'arrête.")
                log_journal(f"✅ Dryrun terminé après {cycle - 1} cycles.")
                break

            print(f"\n🕒 Cycle #{cycle} lancé...")
            log_journal(f"🚀 Cycle #{cycle} lancé.")
            afficher_profil()

            pools = get_pools()
            print(f"✅ Pools récupérées : {pools}")
            log_journal(f"💧 {len(pools)} pools détectées.")

            scored_pools = []
            for pool in pools:
                if "duree" not in pool:
                    print(f"⚠️ Pool {pool['name']} ignorée (champ 'duree' manquant)")
                    continue
                if est_blacklistee(pool["name"], cycle):
                    print(f"⛔️ Pool {pool['name']} ignorée (blacklistée)")
                    continue

                score = (
                    pool["apy"] * profil_data["apy"] +
                    pool["tvl"] * profil_data["tvl"] +
                    pool["duree"] * profil_data["volume"]
                )

                if score >= user_input["seuil_score"]:
                    scored_pools.append((pool, score))
                else:
                    enregistrer_rejet(pool["name"], cycle)

            scored_pools.sort(key=lambda x: x[1], reverse=True)
            top_pools = scored_pools[:user_input["nombre_max"]]

            tableau = []
            for pool, score in scored_pools:
                decision = make_decision(pool, score, user_input["seuil_score"])
                ligne = {
                    "pool": pool["name"],
                    "score": score,
                    "decision": decision["decision"]
                }

                if pool in [tp[0] for tp in top_pools]:
                    if not est_investi(pool["name"]):
                        if not mode_simulation:
                            investir(pool["name"])
                            ajouter_pool(pool["name"])
                    else:
                        taux = get_compounding_rate(pool["name"])
                        ligne["compounding"] = f"{round(taux * 100, 2)}%"
                else:
                    if est_investi(pool["name"]):
                        if not mode_simulation:
                            desinvestir(pool["name"])
                            retirer_pool(pool["name"])
                    ligne["compounding"] = "-"

                tableau.append(ligne)

            afficher_tableau(tableau)
            generer_resume(tableau, cycle)

            if not mode_simulation:
                sauvegarder_snapshot_portefeuille()

            stats.ajouter_cycle(tableau)
            stats.afficher_stats_globales()

            score_moyen = round(sum(l["score"] for l in tableau) / len(tableau), 4) if tableau else 0
            generer_rapport_journalier(cycle, tableau, len(tableau), score_moyen)
            sauvegarder_stats_cycle(cycle, tableau, profil_defaut)

            if user_input["stop"]:
                print("🛑 Arrêt demandé.")
                log_journal("🛑 Arrêt manuel demandé.")
                break

            cycle += 1
            print(f"⏳ Prochain cycle dans {user_input['interval']} secondes...\n")
            time.sleep(user_input["interval"])

            if user_input["pause"]:
                print("⏸️ Bot en pause. Appuie sur Entrée pour reprendre.")
                input()
                user_input["pause"] = False

        except Exception as e:
            log_erreur(f"Cycle #{cycle} - {type(e).__name__}: {e}")
            print(f"❌ Une erreur est survenue (voir errors.log)")
            cycle += 1

# 🎬 Point d'entrée
def main():
    init_log_file()
    init_portefeuille()
    afficher_commandes_disponibles()
    charger_config()

    print("🕒 Pause de 10 secondes avant démarrage du premier cycle...")
    time.sleep(10)

    threading.Thread(target=ecoute_clavier, daemon=True).start()
    lancer_bot()

if __name__ == "__main__":
    main()
