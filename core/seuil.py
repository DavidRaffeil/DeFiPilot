from typing import List

# Seuils ajustables selon le score moyen
SEUILS = [
    (10000, 50),
    (25000, 100),
    (50000, 150),
    (float("inf"), 200),
]

def ajuster_seuil(score_list: List[float]) -> float:
    """
    Calcule un seuil d'investissement automatiquement en fonction
    de la moyenne des scores fournis.
    """
    if not score_list:
        raise ValueError("La liste des scores ne peut pas être vide.")

    moyenne = sum(score_list) / len(score_list)

    for seuil_max, valeur in SEUILS:
        if moyenne < seuil_max:
            return valeur

    # Valeur par défaut (ne devrait jamais être atteinte)
    return 100.0
