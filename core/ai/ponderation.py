# core/ai/ponderation.py – V3.3
"""Outils de pondération APR/TVL basés sur des journaux CSV.

Ce module propose des fonctions pour charger des statistiques récentes et
calculer des pondérations dynamiques entre APR et TVL. Aucune dépendance
externe n'est requise.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Tuple


def parse_float_sur(val: str | None) -> float:
    """Convertit une chaîne en ``float`` en toute sécurité.

    Les virgules sont tolérées comme séparateur décimal. En cas d'échec,
    ``0.0`` est retourné.
    """
    if val is None:
        return 0.0
    try:
        return float(str(val).replace(",", ".").strip())
    except (ValueError, TypeError):
        return 0.0


def _parse_date(val: str | None) -> Optional[date]:
    """Tente de convertir ``val`` en ``date``.

    Plusieurs formats simples sont supportés. ``None`` est renvoyé si la
    conversion échoue.
    """
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _est_dans_fenetre(date_str: str | None, jours: int) -> bool:
    """Indique si ``date_str`` est dans les ``jours`` derniers jours.

    Si ``date_str`` est vide ou illisible, ``True`` est renvoyé pour ne pas
    filtrer l'entrée.
    """
    parsed = _parse_date(date_str)
    if parsed is None:
        return True
    limite = datetime.utcnow().date() - timedelta(days=jours)
    return parsed >= limite


def charger_stats_recent(csv_resume: str, jours: int) -> Dict[str, Optional[float]]:
    """Charge les statistiques APR récentes.

    Parameters
    ----------
    csv_resume: str
        Chemin vers ``journal_resume.csv``.
    jours: int
        Taille de la fenêtre en jours.

    Returns
    -------
    dict
        ``{"moy_apr": float | None, "nb_lignes": int}``.
        ``moy_apr`` vaut ``None`` si aucune donnée.
    """
    try:
        with open(csv_resume, "r", encoding="utf-8", newline="") as fichier:
            lecteur = csv.DictReader(fichier, delimiter=";")
            has_date = lecteur.fieldnames and "date" in lecteur.fieldnames
            total = 0.0
            nb = 0
            for ligne in lecteur:
                if has_date and not _est_dans_fenetre(ligne.get("date"), jours):
                    continue
                total += parse_float_sur(ligne.get("apr") or ligne.get("APR"))
                nb += 1
    except FileNotFoundError:
        return {"moy_apr": None, "nb_lignes": 0}

    if nb == 0:
        return {"moy_apr": None, "nb_lignes": 0}
    return {"moy_apr": total / nb, "nb_lignes": nb}


def charger_risques_recents(csv_risques: str, jours: int) -> Dict[str, int]:
    """Compte les entrées de risques récentes.

    Parameters
    ----------
    csv_risques: str
        Chemin vers ``journal_risques.csv``.
    jours: int
        Fenêtre temporelle en jours.

    Returns
    -------
    dict
        ``{"nb_risques": int}``. ``0`` si fichier absent.
    """
    try:
        with open(csv_risques, "r", encoding="utf-8", newline="") as fichier:
            lecteur = csv.DictReader(fichier, delimiter=";")
            has_date = lecteur.fieldnames and "date" in lecteur.fieldnames
            nb = 0
            for ligne in lecteur:
                if has_date and not _est_dans_fenetre(ligne.get("date"), jours):
                    continue
                nb += 1
    except FileNotFoundError:
        return {"nb_risques": 0}
    return {"nb_risques": nb}


def normaliser(apr: float, tvl: float) -> Tuple[float, float]:
    """Borne et normalise deux poids.

    Les poids sont d'abord bornés à ``[0.1, 0.9]`` puis normalisés afin que
    ``apr + tvl = 1.0``. En cas de somme nulle, ``(0.5, 0.5)`` est renvoyé.
    """
    apr = max(0.1, min(0.9, apr))
    tvl = max(0.1, min(0.9, tvl))
    total = apr + tvl
    if total == 0:
        return 0.5, 0.5
    return apr / total, tvl / total


def calculer_ponderations_dynamiques(
    profil: str,
    base_apr: float,
    base_tvl: float,
    csv_resume: str = "logs/journal_resume.csv",
    csv_risques: str = "logs/journal_risques.csv",
    fenetre_jours: int = 7,
) -> Dict[str, float]:
    """Calcule des pondérations APR/TVL ajustées dynamiquement.

    La base est fournie par ``base_apr`` et ``base_tvl``. Les ajustements sont:

    * ``nb_risques >= 3``  → ``+0.10`` sur TVL, ``-0.10`` sur APR
    * ``moy_apr >= 4.0``   → ``+0.05`` sur APR, ``-0.05`` sur TVL

    Les poids sont ensuite bornés et normalisés.
    """
    stats = charger_stats_recent(csv_resume, fenetre_jours)
    risques = charger_risques_recents(csv_risques, fenetre_jours)

    apr = base_apr
    tvl = base_tvl

    if risques.get("nb_risques", 0) >= 3:
        apr -= 0.10
        tvl += 0.10

    moy_apr = stats.get("moy_apr")
    if moy_apr is not None and moy_apr >= 4.0:
        apr += 0.05
        tvl -= 0.05

    apr, tvl = normaliser(apr, tvl)
    return {"apr": apr, "tvl": tvl}


if __name__ == "__main__":
    BASE_APR = 0.3
    BASE_TVL = 0.7
    PROFIL = "modere"
    poids = calculer_ponderations_dynamiques(PROFIL, BASE_APR, BASE_TVL)
    print(poids)