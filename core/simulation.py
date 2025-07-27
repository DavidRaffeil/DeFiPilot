def simuler_gains(pool, montant_usdc):
    """
    Simule le gain quotidien d’un investissement dans une pool donnée.

    Parameters
    ----------
    pool : dict
        Pool sélectionnée.
    montant_usdc : float
        Montant à investir (simulé) en USDC.

    Returns
    -------
    tuple
        (nom_pool, gain_simulé)
    """
    apr = pool.get("apr", 0)
    nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
    gain = (montant_usdc * apr / 100) / 365
    return nom, round(gain, 4)
