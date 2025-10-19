# interface.py

import tkinter as tk
from tkinter import messagebox, scrolledtext
import matplotlib.pyplot as plt

import simulateur_wallet
from core import config_loader, profil
from defi_sources import defillama
from core.engine import scoring, blacklist

dernier_top3 = []
zone_resultats = None  # défini globalement


def afficher_dans_interface(texte):
    zone_resultats.config(state="normal")
    zone_resultats.delete("1.0", tk.END)
    zone_resultats.insert(tk.END, texte)
    zone_resultats.config(state="disabled")


def lancer_analyse():
    global dernier_top3
    try:
        config_loader.charger_config()
        profil_actif = config_loader.get("profil_defaut", "modere")
        ponderations = profil.charger_ponderations(profil_actif)
        pools = defillama.recuperer_pools()

        if not pools:
            afficher_dans_interface("Aucune pool récupérée.")
            return

        pools_avec_scores = scoring.calculer_scores(pools, ponderations)
        pools_triees = sorted(pools_avec_scores, key=lambda p: p["score"], reverse=True)
        top3 = pools_triees[:3]
        dernier_top3 = top3

        texte = ""
        for i, pool in enumerate(top3, 1):
            texte += (f"TOP {i} : {pool['plateforme']} | {pool['nom']} | "
                      f"TVL ${pool['tvl_usd']:.2f} | APR {pool['apr']:.2f}% | "
                      f"Score {pool['score']:.2f}\n")
        afficher_dans_interface(texte)

    except Exception as e:
        afficher_dans_interface(f"Erreur d'analyse : {str(e)}")


def lancer_simulation():
    if not dernier_top3:
        afficher_dans_interface("Veuillez d’abord lancer une analyse.")
        return
    import io
    import sys

    # Rediriger temporairement les prints
    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer
    simulateur_wallet.simuler_investissement(dernier_top3)
    sys.stdout = old_stdout

    texte = buffer.getvalue()
    afficher_dans_interface(texte)


def lancer_simulation_multi_profils():
    try:
        config_loader.charger_config()
        from simulateur_multi import main as simuler_multi
        simuler_multi(callback_affichage=afficher_dans_interface)
    except Exception as e:
        afficher_dans_interface(f"Erreur simulation multi-profils : {str(e)}")


# Interface graphique principale
root = tk.Tk()
root.title("DeFiPilot")

label = tk.Label(root, text="Bienvenue dans DeFiPilot", font=("Arial", 16))
label.pack(pady=10)

btn_analyse = tk.Button(root, text="Analyser les pools", command=lancer_analyse)
btn_analyse.pack(pady=5)

btn_simuler = tk.Button(root, text="Simulation simple", command=lancer_simulation)
btn_simuler.pack(pady=5)

btn_multi = tk.Button(root, text="Simulation multi-profils", command=lancer_simulation_multi_profils)
btn_multi.pack(pady=5)

btn_quitter = tk.Button(root, text="Quitter", command=root.quit)
btn_quitter.pack(pady=10)

zone_resultats = scrolledtext.ScrolledText(root, height=20, width=80, wrap=tk.WORD, state="disabled")
zone_resultats.pack(padx=10, pady=10)

root.mainloop()
