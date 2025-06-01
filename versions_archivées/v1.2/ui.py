import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# --- Constantes ---
CONFIG_PATH = "config_investor_profiles.json"

# --- Fonctions utilitaires ---
def charger_profil_actif():
    if not os.path.exists(CONFIG_PATH):
        messagebox.showerror("Erreur", f"Config introuvable : {CONFIG_PATH}")
        fenetre.destroy()
        return None, None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    profil_nom = data.get("profil_actif")
    profil = data["profils"].get(profil_nom)
    return profil_nom, profil

def lancer_bot():
    statut_label.config(text="Bot lancé ! (fonction à connecter)")
    # Ici tu pourras lancer ton bot ou ta fonction principale

# --- Création de la fenêtre principale ---
fenetre = tk.Tk()
fenetre.title("DeFiPilot v1.2 - Interface")
fenetre.geometry("340x250")
fenetre.resizable(False, False)

# --- Chargement du profil ---
profil_nom, profil = charger_profil_actif()

# --- Affichage du profil investisseur ---
frame_profil = ttk.LabelFrame(fenetre, text="Profil investisseur")
frame_profil.pack(padx=20, pady=15, fill="x")

if profil and profil_nom:
    label_nom = ttk.Label(frame_profil, text=f"Nom : {profil_nom.capitalize()}")
    label_nom.pack(anchor="w", padx=10, pady=2)

    label_pond = ttk.Label(frame_profil, text=f"Pondération risque : {profil['pondération_risque']}")
    label_pond.pack(anchor="w", padx=10, pady=2)

    label_seuil = ttk.Label(frame_profil, text=f"Seuil de score : {profil['seuil_score']}")
    label_seuil.pack(anchor="w", padx=10, pady=2)
else:
    label_nom = ttk.Label(frame_profil, text="Erreur : profil non trouvé")
    label_nom.pack(anchor="w", padx=10, pady=2)

# --- Bouton "Lancer" ---
bouton_lancer = ttk.Button(fenetre, text="Lancer", command=lancer_bot)
bouton_lancer.pack(pady=10)

# --- Label de statut ---
statut_label = ttk.Label(fenetre, text="En attente du lancement…")
statut_label.pack(pady=(5, 15))

# --- Lancement de la boucle principale Tkinter ---
fenetre.mainloop()
