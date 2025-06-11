# graphiques/gains_profils.py

import matplotlib.pyplot as plt
import os

def afficher_et_sauvegarder_gains(gains_par_profil, duree_jours=7):
    """
    Affiche un graphique en barres des gains simulés par profil
    et l’enregistre sous forme d’image PNG.
    """
    profils = list(gains_par_profil.keys())
    gains = list(gains_par_profil.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(profils, gains)

    # Ajoute les valeurs sur les barres
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, f'{yval:.0f}$', ha='center', va='bottom')

    plt.title(f"Comparaison des gains simulés sur {duree_jours} jours")
    plt.xlabel("Profil d'investissement")
    plt.ylabel("Gain estimé ($)")
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Affichage
    plt.tight_layout()
    plt.show()

    # Sauvegarde
    dossier = "graphique_export"
    os.makedirs(dossier, exist_ok=True)
    chemin_image = os.path.join(dossier, f"gains_profils_{duree_jours}j.png")
    plt.savefig(chemin_image)
    print(f"📸 Graphe enregistré : {chemin_image}")
