# startup_check.py

import os
import sys

ELEMENTS_CRITIQUES = [
    ("FICHIER", "settings.json"),
    ("FICHIER", "profil_invest.json"),
    ("DOSSIER", "logs"),
    ("DOSSIER", "results")
]

def verifier_elements():
    tout_est_ok = True

    for type_element, chemin in ELEMENTS_CRITIQUES:
        if type_element == "FICHIER":
            if not os.path.isfile(chemin):
                print(f"❌ Fichier manquant : {chemin}")
                tout_est_ok = False
        elif type_element == "DOSSIER":
            if not os.path.isdir(chemin):
                print(f"❌ Dossier manquant : {chemin}")
                tout_est_ok = False

    if not tout_est_ok:
        print("\n🛑 Erreur critique : certains fichiers ou dossiers sont manquants.")
        print("👉 Corrigez les éléments manquants avant de relancer le bot.")
        sys.exit(1)

    print("✅ Vérification des fichiers et dossiers : OK")

if __name__ == "__main__":
    verifier_elements()
