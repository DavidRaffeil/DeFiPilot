import os

# Liste des fichiers à supprimer (à adapter si besoin)
fichiers_a_supprimer = [
    "journal_gain_simule.csv",
    "journal_gain_csv.py",
    "historique_cycles.csv",
    "journal_rendement.csv",
    "solde_virtuel.json",
    "resultats_top3_agressif.json",
    "resultats_top3_modéré.json",
    "resultats_top3_prudent.json"
]

# Dossiers à supprimer
dossiers_a_supprimer = [
    "logs"
]

def clean():
    for f in fichiers_a_supprimer:
        if os.path.exists(f):
            os.remove(f)
            print(f"Supprimé : {f}")
    for d in dossiers_a_supprimer:
        if os.path.exists(d):
            try:
                for root, dirs, files in os.walk(d, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(d)
                print(f"Dossier supprimé : {d}")
            except Exception as e:
                print(f"Erreur suppression {d} : {e}")

if __name__ == "__main__":
    clean()
