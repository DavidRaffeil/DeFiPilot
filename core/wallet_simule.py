# core/wallet_simule.py

import os
import json

FICHIER_SIMULATION = "wallet_simulation.json"

class WalletSimule:
    def __init__(self, montant_initial=100.0):
        self.solde = montant_initial
        self._charger()

    def _charger(self):
        if os.path.exists(FICHIER_SIMULATION):
            try:
                with open(FICHIER_SIMULATION, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.solde = data.get("solde", self.solde)
            except Exception as e:
                print(f"[ERREUR] Impossible de charger le fichier de simulation : {e}")

    def _sauvegarder(self):
        try:
            with open(FICHIER_SIMULATION, "w", encoding="utf-8") as f:
                json.dump({"solde": round(self.solde, 2)}, f, indent=2)
        except Exception as e:
            print(f"[ERREUR] Impossible de sauvegarder la simulation : {e}")

    def investir(self, gain_estime):
        solde_avant = self.solde
        self.solde += gain_estime
        self._sauvegarder()
        return solde_avant, gain_estime, self.solde

    def reset(self, nouveau_montant=100.0):
        self.solde = nouveau_montant
        self._sauvegarder()

    def get_solde(self):
        return self.solde
