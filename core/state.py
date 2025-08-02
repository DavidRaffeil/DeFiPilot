# core/state.py

from datetime import datetime
import os

FICHIER_ETAT = "etat_simulation.txt"

def get_current_day() -> int:
    """
    Récupère le jour courant de simulation à partir du fichier d'état.
    :return: Numéro du jour (int)
    """
    if not os.path.exists(FICHIER_ETAT):
        return 1
    with open(FICHIER_ETAT, "r") as f:
        contenu = f.read()
        if contenu.isdigit():
            return int(contenu)
        return 1

def increment_day() -> None:
    """
    Incrémente et sauvegarde le jour de simulation.
    """
    jour = get_current_day() + 1
    with open(FICHIER_ETAT, "w") as f:
        f.write(str(jour))
