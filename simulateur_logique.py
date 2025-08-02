# simulateur_logique.py

"""Fonctions logiques pour la simulation de gains."""

from typing import Tuple


def simuler_gains(pool: dict) -> Tuple[str, float]:
    """Calcule le gain potentiel sur 24h pour une pool.

    Parameters
    ----------
    pool : dict
        Dictionnaire décrivant la pool avec les clés ``"apr"`` et ``"tvl_usd"``.

    Returns
    -------
    Tuple[str, float]
        Une chaîne lisible du gain estimé et la valeur numérique correspondante.
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