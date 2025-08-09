"""Analyse simplifiée du risque des pools.

Cette version se concentre sur quelques critères basiques afin de
simuler une détection de pools potentiellement risquées.
"""

from typing import Dict, List


def analyser_risque(pool: Dict) -> Dict:
    """Analyse un pool pour déterminer s'il présente des risques.

    Modifie le dictionnaire pool en ajoutant :
    - pool["risque"] : booléen
    - pool["raisons_risque"] : liste de strings

    Parameters
    ----------
    pool: Dict
        Dictionnaire décrivant une pool avec les clés ``apr`` et ``tvl_usd``.

    Returns
    -------
    Dict
        La pool enrichie avec les champs "risque" et "raisons_risque"
    """
    raisons: List[str] = []

    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    if apr > 15:
        raisons.append("APR élevé")
    if tvl < 5_000:
        raisons.append("TVL faible")

    pool["risque"] = bool(raisons)
    pool["raisons_risque"] = raisons

    return pool
