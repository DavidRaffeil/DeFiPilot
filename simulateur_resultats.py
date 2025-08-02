# simulateur_resultats.py

from datetime import datetime

def generer_resume_journalier(pool: dict, gain_str: str, gain_val: float, rang: int) -> str:
    """
    Génère un résumé textuel des résultats d'une simulation pour une pool donnée.

    :param pool: Dictionnaire contenant les données de la pool.
    :param gain_str: Texte représentant le gain simulé.
    :param gain_val: Valeur numérique du gain.
    :param rang: Rang de la pool dans le classement du jour.
    :return: Résumé formaté à afficher dans la console ou à logger.
    """
    score = pool.get("score", 0)
    symbole = pool.get("symbol", "")
    nom_pool = pool.get("name", "")
    plateforme = pool.get("dex", "unknown")

    return f"{rang}. {nom_pool} | {symbole} | Score : {score:.2f} | {gain_str}"
