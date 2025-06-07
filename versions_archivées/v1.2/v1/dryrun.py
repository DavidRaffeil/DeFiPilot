# dryrun.py - gestion du mode dryrun

import time

def lancer_dryrun(nb_cycles):
    for i in range(1, nb_cycles + 1):
        print(f"🕒 Cycle dryrun #{i} en cours...")
        # Simulation d'un cycle
        time.sleep(2)
        print(f"✅ Fin du cycle #{i}\n")

    print("🏁 Tous les cycles dryrun sont terminés.")
