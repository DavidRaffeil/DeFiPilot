# interface.py

import tkinter as tk

class InterfaceBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DeFiPilot - Résumé des Cycles")
        self.root.geometry("700x500")

        self.titre = tk.Label(self.root, text="📋 Résumé des cycles DeFiPilot", font=("Helvetica", 16, "bold"))
        self.titre.pack(pady=10)

        self.contenu_var = tk.StringVar()
        self.contenu_var.set("En attente de démarrage...")

        self.label_contenu = tk.Label(self.root, textvariable=self.contenu_var, font=("Consolas", 12), justify="left", anchor="nw")
        self.label_contenu.pack(expand=True, fill="both", padx=20, pady=10)

        self.bouton_quitter = tk.Button(self.root, text="🚪 Quitter", command=self.root.destroy, font=("Helvetica", 12))
        self.bouton_quitter.pack(pady=10)

    def update_text(self, texte):
        self.contenu_var.set(texte)

    def lancer(self):
        self.root.mainloop()
