def est_une_pool_a_farming(pool_data: dict) -> bool:
    """
    Détermine si une pool nécessite du farming de LP tokens.
    Pour l’instant, détection simulée via un champ fictif 'is_farming'.

    Args:
        pool_data (dict): Données de la pool

    Returns:
        bool: True si farming détecté, sinon False
    """
    return pool_data.get("is_farming", False)
