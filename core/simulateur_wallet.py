# simulateur_wallet.py – Version V2.5 corrigée temporairement (slippage désactivé)

import os
import json
import csv
from datetime import datetime
# from core.journal import enregistrer_slippage_lp  # Désactivé temporairement
from core.utils import ligne_deja_presente

FICHIER_WALLET = "data/wallet_simule.json"
FICHIER_LOG = "logs/journal_top3.csv"


def simuler_gains(pool, montant):
    try:
        apr = pool.get("apr", 0)
        gain_brut = (montant * apr / 100) / 365
        gain_lisible = f"{gain_brut:.2f} $ USDC"
        return gain_lisible, round(gain_brut, 4)
    except Exception as e:
        print(f"[ERREUR] Échec de la simulation de gains : {e}")
        return "0.00 $ USDC", 0.0


def simuler_gains_wallet(pool, montant: float = 100.0):
    return simuler_gains(pool, montant)


class WalletSimule:
    def __init__(self, montant_initial: float = 4953.25) -> None:
        self.solde = montant_initial
        self._charger()

    def _charger(self) -> None:
        if os.path.exists(FICHIER_WALLET):
            try:
                with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.solde = float(data.get("solde", self.solde))
            except Exception:
                pass

    def _sauvegarder(self) -> None:
        os.makedirs("data", exist_ok=True)
        with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
            json.dump({"solde": round(self.solde, 4)}, f, indent=2)

    def get_solde(self) -> float:
        return self.solde

    def investir(self, montant: float):
        solde_avant = self.solde
        self.solde += montant
        self._sauvegarder()
        return solde_avant, montant, self.solde


class WalletLP:
    def __init__(self) -> None:
        self.soldes_lp: dict[str, float] = {}

    def ajouter_lp(self, pool_name: str, montant: float) -> None:
        if pool_name in self.soldes_lp:
            self.soldes_lp[pool_name] += montant
        else:
            self.soldes_lp[pool_name] = montant

    def afficher_soldes(self) -> None:
        print("\n📊 Solde LP simulé :")
        if not self.soldes_lp:
            print("(vide)")
            return
        for pool, montant in self.soldes_lp.items():
            print(f" - {pool} : {montant:.4f} LP")


def charger_solde():
    if not os.path.exists(FICHIER_WALLET):
        return 0.0
    try:
        with open(FICHIER_WALLET, "r", encoding="utf-8") as f:
            data = json.load(f)
            return float(data.get("solde", 0.0))
    except Exception:
        return 0.0


def mettre_a_jour_solde(gain):
    solde = charger_solde()
    nouveau_solde = round(solde + gain, 4)
    os.makedirs("data", exist_ok=True)
    with open(FICHIER_WALLET, "w", encoding="utf-8") as f:
        json.dump({"solde": nouveau_solde}, f, indent=2)
    return nouveau_solde


def ligne_deja_presente(date_str):
    if not os.path.exists(FICHIER_LOG):
        return False
    with open(FICHIER_LOG, "r", encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith(date_str):
                return True
