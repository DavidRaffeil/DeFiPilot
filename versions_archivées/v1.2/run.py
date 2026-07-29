# run.py

import time
from main import dryrun
from config_loader import charger_config, get

def run_en_boucle():
    try:
        charger_config()
        interval = get("interval_secondes", 60)
        mode_simulation = get("mode_simulation", True)

        print(f"🚀 DeFiPilot démarré en mode {'simulation' if mode_simulation else 'réel'}")
        print(f"⏱️ Intervalle entre les cycles : {interval} secondes\n")

        while True:
            print("🔁 Nouveau cycle lancé...\n")
            dryrun()
            print(f"⏳ Attente de {interval} secondes...\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt manuel du bot. À bientôt !")

if __name__ == "__main__":
    run_en_boucle()
