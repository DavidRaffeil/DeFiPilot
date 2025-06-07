# compounder.py

from datetime import datetime
from portfolio import get_date_investissement

def get_compounding_rate(pool_name):
    """
    Calcule le taux de réinvestissement dégressif :
    Jour 0 → 100%
    Jour 1 → 50%
    Jour 2 → 25%
    etc.
    """
    date_str = get_date_investissement(pool_name)

    if not date_str:
        return 0.0  # Aucun enregistrement → on ne compose pas

    try:
        date_invest = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"⚠️ Format de date invalide pour {pool_name}: {date_str}")
        return 0.0

    aujourd_hui = datetime.now()
    jours_passes = (aujourd_hui - date_invest).days
    taux = 1 / (2 ** jours_passes)
    return round(taux, 4)
