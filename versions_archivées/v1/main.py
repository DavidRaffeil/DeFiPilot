import time
import threading
import sys 
from scanner_pools import get_pools
from scoring import score_pool
from strategy import make_decision, afficher_profil
from logger import init_log_file, log_decision
from executor import investir, desinvestir
from portfolio import (
    est_investi,
    ajouter_pool,
    retirer_pool,
    init_portefeuille,
    sauvegarder_snapshot_portefeuille
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
from portfolio import exporter_portefeuille
from portfolio import snapshot_portefeuille
from cycle_stats import sauvegarder_stats_cycle
from profile_simulator import simuler_profil
from interface import InterfaceBot

# --- Blacklist temporaire (en mémoire) ---
blacklist = {}
interface = None
user_input = {}

def enregistrer_rejet(pool_name, cycle_actuel):
    duree = get("nb_cycles_blacklist", 3)
    expiration = cycle_actuel + duree
    blacklist[pool_name] = expiration
    print(f"🚫 Pool '{pool_name}' blacklistée jusqu'au cycle {expiration}")

def est_blacklistee(pool_name, cycle_actuel):
    expiration = blacklist.get(pool_name)
    if expiration and cycle_actuel <= expiration:
        return True
    return False

def afficher_commandes_disponibles():
    print("\n🧭 Commandes clavier disponibles :")
    print("-" * 40)
    print("q           → Quitter proprement le bot")
    print("p           → Mettre en pause le bot")
    print("profil      → Afficher le profil actif")
    print("profil xxx  → Changer de profil : prudent | modéré | agressif")
    print("stats       → Afficher les statistiques cumulées")
    print("wait xxx    → Modifier l'intervalle entre les cycles (ex: wait 60)")
    print("reload      → Recharger le profil depuis profils.json")
    print("dryrun x    → Exécuter x cycles et arrêter")
    print("-" * 40 + "\n")

def afficher_tableau(donnees):
    print("\n📋 Résumé des décisions")
    print("-" * 80)
    print(f"{'Pool':<15} {'Score':<8} {'Décision':<20} {'Taux compounding'}")
    print("-" * 80)
    for ligne in donnees:
        pool = ligne['pool']
        score = round(ligne['score'], 4)
        decision = ligne['decision']
        compounding = ligne.get("compounding", "-")
        print(f"{pool:<15} {score:<8} {decision:<20} {compounding}")
    print("-" * 80 + "\n")

def lancer_bot():
    global user_input
    stats = Statistiques()
    cycle = 1

    mode_simulation = get("mode_simulation", True)
    if mode_simulation:
        print("🧪 Mode simulation ACTIVÉ – Aucune action réelle ne sera effectuée.")
        log_journal("🧪 Mode simulation activé")

    profil_defaut = get("profil_defaut", "modéré")
    profil_actif = charger_profil(profil_defaut)
    if not profil_actif:
        print("❌ Impossible de charger le profil. Arrêt du bot.")
        return

    user_input = {
        "stop": False,
        "pause": False,
        "interval": get("interval_secondes", 600),
        "profil_actif": profil_actif,
        "seuil_score": profil_actif["seuil_score"],
        "nombre_max": profil_actif["max_pools"],
        "dryrun": None
    }

    while True:
        try:
            print(f"\n🕒 Cycle #{cycle} lancé...")
            log_journal(f"🚀 Cycle #{cycle} lancé.")
            afficher_profil()

            pools = get_pools()
            print(f"💧 {len(pools)} pools détectées.")
            log_journal(f"💧 {len(pools)} pools détectées.")

            max_apy = max(pool["apy"] for pool in pools)
            max_tvl = max(pool["tvl"] for pool in pools)
            max_volume = max(pool["volume_24h"] for pool in pools)

            scored_pools = []
            for pool in pools:
                if est_blacklistee(pool["name"], cycle):
                    print(f"⛔ Pool {pool['name']} ignorée (blacklistée)")
                    continue

                score = score_pool(pool, max_apy, max_tvl, max_volume)
                if score >= user_input["seuil_score"]:
                    scored_pools.append((pool, score))
                else:
                    enregistrer_rejet(pool["name"], cycle)

            scored_pools.sort(key=lambda x: x[1], reverse=True)
            top_pools = scored_pools[:user_input["nombre_max"]]

            tableau = []
            for pool, score in scored_pools:
                decision = make_decision(pool, score)
                ligne = {
                    "pool": decision["pool"],
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

            texte_interface = f"Cycle #{cycle}\n"
            for ligne in tableau:
                texte_interface += f"{ligne['pool']} - Score: {round(ligne['score'],4)} - Décision: {ligne['decision']}\n"
            interface.update_text(texte_interface)

            if not mode_simulation:
                sauvegarder_snapshot_portefeuille()

            stats.ajouter_cycle(tableau)
            stats.afficher_stats_globales()

            total_pools = len(tableau)
            score_total = sum(l["score"] for l in tableau)
            score_moyen = round(score_total / total_pools, 4) if total_pools else 0
            generer_rapport_journalier(cycle, tableau, total_pools, score_moyen)
            sauvegarder_stats_cycle(cycle, tableau, get("profil_defaut", "modéré"))

            if user_input["dryrun"] and cycle >= user_input["dryrun"]:
                print(f"✅ Dryrun terminé après {cycle} cycles. Le bot s'arrête.")
                log_journal(f"✅ Dryrun terminé après {cycle} cycles.")
                interface.update_text("✅ Bot terminé.\nVous pouvez fermer cette fenêtre.")
                break

            if user_input["stop"]:
                print("🛑 Arrêt demandé.")
                log_journal("🛑 Arrêt manuel demandé.")
                interface.update_text("🛑 Arrêt manuel.\nVous pouvez fermer cette fenêtre.")
                break

            print(f"⏳ Prochain cycle dans {user_input['interval']} secondes...\n")

            time.sleep(user_input["interval"])
            cycle += 1

            if user_input["pause"]:
                print("⏸️ Bot en pause. Appuie sur Entrée pour reprendre.")
                input()
                user_input["pause"] = False

        except Exception as e:
            log_erreur(f"Cycle #{cycle} - {type(e).__name__}: {e}")
            print(f"❌ Une erreur est survenue (voir errors.log)")

# --- Main Principal ---

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dryrun":
        from dryrun import lancer_dryrun
        print("🧪 Mode Dryrun automatique détecté. Lancement de 5 cycles en simulation...")
        lancer_dryrun(5)
        return

    global interface
    init_log_file()
    init_portefeuille()
    afficher_commandes_disponibles()
    charger_config()

    print("🕒 Pause de 10 secondes avant démarrage du premier cycle...")
    time.sleep(10)

    interface = InterfaceBot()

    threading.Thread(target=lancer_bot, daemon=True).start()
    interface.lancer()

if __name__ == "__main__":
    main()
