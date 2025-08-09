# core/simulateur_logique.py
# 🧩 Version : V2.9 – Journalisation du slippage LP (import désactivé pour test V3.2)

from typing import Tuple
# from .journal import enregistrer_slippage_lp  # Désactivé temporairement

def simuler_gains(pool: dict) -> Tuple[str, float]:
    """
    Simule les gains journaliers en USDC pour une pool classique (non LP).
    """
    try:
        apr = float(pool.get("apr", 0))
        tvl = float(pool.get("tvl_usd", 0))
        gain = (tvl * apr / 100) / 365
        gain = round(gain, 4)
        return f"{gain:.4f} $ USDC", gain
    except Exception as e:
        print(f"[ERREUR] Échec du calcul de gain : {e}")
        return "0.0000 $ USDC", 0.0


def simuler_gain_farming_lp(montant_lp: float, farming_apr: float) -> float:
    """
    Simule les gains journaliers issus du farming de LP tokens.
    """
    try:
        montant_lp = montant_lp * 0.98  # slippage LP simulé de 2 %
        gain = (montant_lp * farming_apr / 100) / 365
        return round(gain, 4)
    except Exception as e:
        print(f"[ERREUR] Échec du calcul farming LP : {e}")
        return 0.0


def simuler_farming_lp(date: str, nom_pool: str, plateforme: str, montant_lp: float, farming_apr: float, profil: str) -> float:
    """
    Simule le farming de LP tokens et journalise le slippage subi.
    """
    try:
        slippage_lp = montant_lp * 0.02  # slippage LP simulé de 2 %
        montant_apres_slippage = montant_lp - slippage_lp
        # enregistrer_slippage_lp(date, nom_pool, plateforme, montant_lp, slippage_lp, profil)  # Désactivé
        gain = (montant_apres_slippage * farming_apr / 100) / 365
        return round(gain, 4)
    except Exception as e:
        print(f"[ERREUR] Échec du farming LP : {e}")
        return 0.0
