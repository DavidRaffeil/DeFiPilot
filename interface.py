import tkinter as tk
from tkinter import messagebox, Toplevel
import matplotlib.pyplot as plt

import simulateur_wallet
from core import config_loader, profil
from defi_sources import defillama
from core import scoring, blacklist
from core import historique

import os
import csv
import collections

dernier_top3 = []

def lancer_analyse():
    global dernier_top3
    try:
        config_loader.charger_config()
        profil_actif = config_loader.get("profil_defaut", "modéré")
        ponderations = profil.charger_ponderations(profil_actif)
        pools = defillama.recuperer_pools()
        pools_filtrees = blacklist.filtrer_blacklist(pools)
        tvl_min = config_loader.get("tvl_min", 0)
        apr_min = config_loader.get("apr_min", 0)

        pools_filtrees = [
            pool for pool in pools_filtrees
            if pool["tvl_usd"] >= tvl_min and pool["apr"] >= apr_min
        ]

        pools_scored = scoring.calculer_scores(pools_filtrees, ponderations)
        top3 = sorted(pools_scored, key=lambda x: x["score"], reverse=True)[:3]

        try:
            seuil_val = float(entry_seuil.get())
        except ValueError:
            seuil_val = config_loader.get("seuil_score_investissement", 0)
        top3 = [pool for pool in top3 if pool["score"] >= seuil_val]

        dernier_top3 = top3

        zone_resultat.delete(1.0, tk.END)
        if not top3:
            zone_resultat.insert(tk.END, "Aucune pool ne correspond aux critères.")
            return

        # ✅ NOUVEAU : calcul réel des gains simulés
        montant_simule = 100
        solde = simulateur_wallet.charger_solde()
        gains_simules = [simulateur_wallet.simuler_gains(pool, montant_simule)[1] for pool in top3]
        gain_total = sum(gains_simules)

        texte = (
            f"Profil : {profil_actif}\n"
            f"Solde simulé : ${solde:.2f}\n"
            f"Gain estimé (Top 3) : ~{gain_total:.2f} € / 24h\n\n"
        )

        for i, pool in enumerate(top3, 1):
            gain_lisible, _ = simulateur_wallet.simuler_gains(pool, montant=100)
            texte += f"TOP {i} - {pool['plateforme']} | {pool['nom']}\n"
            texte += f"  TVL: ${pool['tvl_usd']:.2f} | APR: {pool['apr']:.2f}% | Score: {pool['score']:.2f}\n"
            texte += f"  💰 Gain estimé (24h, 100$ simulés) : {gain_lisible}\n\n"

        zone_resultat.insert(tk.END, texte)

        simulateur_wallet.journaliser_resultats(profil_actif, solde, top3, montant=100)
        historique.ajouter_au_csv(top3)

    except Exception as e:
        messagebox.showerror("Erreur", str(e))

def reinitialiser_wallet():
    reponse = messagebox.askyesno("Confirmation", "Réinitialiser le solde simulé à 100.00 $ ?")
    if reponse:
        simulateur_wallet.sauvegarder_solde(100.0)
        zone_resultat.delete(1.0, tk.END)
        zone_resultat.insert(tk.END, "✅ Solde réinitialisé à 100.00 $")

def exporter_analyse():
    contenu = zone_resultat.get("1.0", tk.END).strip()
    if not contenu:
        messagebox.showinfo("Exportation", "Aucune analyse à exporter.")
        return
    try:
        with open("derniere_analyse.txt", "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("Exportation", "✅ Analyse exportée dans 'derniere_analyse.txt'")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'exporter l'analyse : {e}")

def afficher_graphique():
    if not dernier_top3:
        messagebox.showinfo("Graphique", "Aucune donnée disponible. Lance une analyse d'abord.")
        return

    noms = [f"{p['plateforme']} | {p['nom']}" for p in dernier_top3]
    scores = [p['score'] for p in dernier_top3]

    plt.figure(figsize=(8, 5))
    plt.bar(noms, scores)
    plt.title("Score des 3 meilleures pools")
    plt.ylabel("Score")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.show()

def afficher_historique():
    chemin_csv = "historique_cycles.csv"
    if not os.path.exists(chemin_csv):
        messagebox.showinfo("Historique", "Aucun historique trouvé.")
        return
    try:
        with open(chemin_csv, "r", encoding="utf-8") as f:
            lecteur = csv.reader(f)
            lignes = list(lecteur)
        if not lignes or len(lignes) < 2:
            messagebox.showinfo("Historique", "Aucun historique à afficher.")
            return
        entetes = lignes[0]
        data = lignes[1:]

        dates = [row[0] for row in data if row]
        dex = [row[2] for row in data if len(row) > 2]
        scores = [float(row[6]) for row in data if len(row) > 6 and row[6].replace('.','',1).isdigit()]
        try:
            score_min = min(scores)
            score_max = max(scores)
        except ValueError:
            score_min = score_max = "N/A"

        date_min = min(dates) if dates else "N/A"
        date_max = max(dates) if dates else "N/A"
        cycles = len(data)
        if dex:
            pool_freq = collections.Counter(dex).most_common(1)[0]
            pool_freq_str = f"{pool_freq[0]} ({pool_freq[1]} fois)"
        else:
            pool_freq_str = "N/A"

        resume = (
            f"Nombre de cycles simulés : {cycles}\n"
            f"Du : {date_min} au {date_max}\n"
            f"Score min : {score_min} | Score max : {score_max}\n"
            f"Pool la plus fréquente (col. 'dex') : {pool_freq_str}\n"
            "-----------------------------------------------\n"
        )

        fen_histo = Toplevel(fenetre)
        fen_histo.title("Historique des rendements simulés")
        fen_histo.geometry("1100x650")
        canvas = tk.Canvas(fen_histo)
        frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(fen_histo, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0,0), window=frame, anchor='nw')

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind('<Configure>', on_configure)

        label_resume = tk.Label(frame, text=resume, font=("Courier New", 11, "bold"), fg="#2a2", bg="#e9ffe9", anchor="w", justify="left", padx=8, pady=6)
        label_resume.grid(row=0, column=0, columnspan=len(entetes), sticky="nsew")

        for col, titre in enumerate(entetes):
            label = tk.Label(frame, text=titre, font=("Courier New", 10, "bold"), borderwidth=1, relief="solid", padx=2, pady=2, bg="#e3e3e3")
            label.grid(row=1, column=col, sticky="nsew")

        for row_idx, ligne in enumerate(data, start=2):
            for col_idx, valeur in enumerate(ligne):
                bgcol = "#fff" if row_idx % 2 == 0 else "#f9f9f9"
                label = tk.Label(frame, text=valeur, font=("Courier New", 10), borderwidth=1, relief="solid", padx=2, pady=2, bg=bgcol)
                label.grid(row=row_idx, column=col_idx, sticky="nsew")

        for col in range(len(entetes)):
            frame.grid_columnconfigure(col, weight=1)

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lire ou afficher l'historique : {e}")

# --- Interface principale ---
fenetre = tk.Tk()
fenetre.title("DeFiPilot - Interface claire")
fenetre.geometry("700x660")
fenetre.configure(bg="white")

label_titre = tk.Label(fenetre, text="DeFiPilot (mode simulation)", font=("Helvetica", 18, "bold"), bg="white", fg="#222")
label_titre.pack(pady=10)

frame_seuil = tk.Frame(fenetre, bg="white")
frame_seuil.pack()
label_seuil = tk.Label(frame_seuil, text="Seuil score min. (optionnel) :", bg="white")
label_seuil.pack(side="left", padx=(0,6))
entry_seuil = tk.Entry(frame_seuil, width=12)
entry_seuil.pack(side="left")
entry_seuil.insert(0, str(config_loader.get("seuil_score_investissement", 0)))

frame_boutons = tk.Frame(fenetre, bg="white")
frame_boutons.pack(pady=5)

btn_analyse = tk.Button(frame_boutons, text="Lancer une analyse", width=25, command=lancer_analyse)
btn_analyse.grid(row=0, column=0, padx=10, pady=5)

btn_reset = tk.Button(frame_boutons, text="Réinitialiser le wallet", width=25, command=reinitialiser_wallet)
btn_reset.grid(row=0, column=1, padx=10, pady=5)

btn_export = tk.Button(frame_boutons, text="Exporter l’analyse", width=25, command=exporter_analyse)
btn_export.grid(row=1, column=0, padx=10, pady=5)

btn_graph = tk.Button(frame_boutons, text="Afficher le graphique", width=25, command=afficher_graphique)
btn_graph.grid(row=1, column=1, padx=10, pady=5)

btn_histo = tk.Button(frame_boutons, text="Afficher l’historique", width=25, command=afficher_historique)
btn_histo.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

frame_resultat = tk.Frame(fenetre, bg="white")
frame_resultat.pack(padx=15, pady=10, fill="both", expand=True)

zone_resultat = tk.Text(
    frame_resultat,
    height=20,
    font=("Courier New", 10),
    wrap="word",
    bg="#f5f5f5",
    fg="#222"
)
zone_resultat.pack(side="left", fill="both", expand=True)

scrollbar = tk.Scrollbar(frame_resultat, command=zone_resultat.yview)
scrollbar.pack(side="right", fill="y")

zone_resultat.config(yscrollcommand=scrollbar.set)

fenetre.mainloop()
