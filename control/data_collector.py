# control/data_collector.py — V4.8.2
"""Module de collecte qui lit des journaux JSONL et extrait des indicateurs de base."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable


logger = logging.getLogger(__name__)


def charger_evenements_signaux(chemin_journal: Path) -> list[dict[str, Any]]:
    """Charge les événements du journal de signaux depuis un fichier JSONL."""
    if not chemin_journal.exists():
        logger.warning("Fichier de journal introuvable: %s", chemin_journal)
        return []

    evenements: list[dict[str, Any]] = []

    try:
        with chemin_journal.open("r", encoding="utf-8") as fichier:
            for ligne in fichier:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    donnees = json.loads(ligne)
                except json.JSONDecodeError as exc:
                    logger.warning("Ligne JSON invalide (%s): %s", exc, ligne)
                    continue

                if not isinstance(donnees, dict):
                    logger.warning("Événement ignoré, type inattendu: %s", type(donnees).__name__)
                    continue

                evenements.append(donnees)
    except OSError as exc:
        logger.error("Erreur lors de la lecture du journal %s: %s", chemin_journal, exc)
        return []

    return evenements


def extraire_indicateurs_de_base(evenements: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Agrège une séquence d'événements du journal_signaux.jsonl en indicateurs de suivi."""
    evenements_list = list(evenements)

    if not evenements_list:
        return {
            "nb_evenements": 0,
            "ts_debut": None,
            "ts_fin": None,
            "context_courant": None,
            "context_precedent": None,
            "repartition_context": {},
            "score_moyen": None,
            "score_min": None,
            "score_max": None,
            "metrics_locales_moyennes": {},
            "derniere_policy": None,
        }

    nb_evenements = len(evenements_list)
    premier = evenements_list[0]
    dernier = evenements_list[-1]

    ts_debut = premier.get("ts")
    if ts_debut is None:
        ts_debut = premier.get("timestamp")

    ts_fin = dernier.get("ts")
    if ts_fin is None:
        ts_fin = dernier.get("timestamp")

    context_courant = dernier.get("context")
    context_precedent = dernier.get("last_context")

    repartition_context: dict[str, int] = {}
    scores: list[float] = []
    metrics_somme: dict[str, float] = {}
    metrics_compte: dict[str, int] = {}

    for evt in evenements_list:
        contexte_evt = evt.get("context")
        if isinstance(contexte_evt, str):
            repartition_context[contexte_evt] = repartition_context.get(contexte_evt, 0) + 1

        score = evt.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            scores.append(float(score))

        metrics_locales = evt.get("metrics_locales")
        if isinstance(metrics_locales, dict):
            for cle, valeur in metrics_locales.items():
                if isinstance(valeur, (int, float)) and not isinstance(valeur, bool):
                    metrics_somme[cle] = metrics_somme.get(cle, 0.0) + float(valeur)
                    metrics_compte[cle] = metrics_compte.get(cle, 0) + 1

    if scores:
        score_moyen = sum(scores) / len(scores)
        score_min = min(scores)
        score_max = max(scores)
    else:
        score_moyen = None
        score_min = None
        score_max = None

    metrics_locales_moyennes: dict[str, float] = {}
    for cle, somme in metrics_somme.items():
        compteur = metrics_compte.get(cle, 0)
        if compteur > 0:
            metrics_locales_moyennes[cle] = somme / compteur

    derniere_policy = dernier.get("policy") if "policy" in dernier else None

    return {
        "nb_evenements": nb_evenements,
        "ts_debut": ts_debut,
        "ts_fin": ts_fin,
        "context_courant": context_courant,
        "context_precedent": context_precedent,
        "repartition_context": repartition_context,
        "score_moyen": score_moyen,
        "score_min": score_min,
        "score_max": score_max,
        "metrics_locales_moyennes": metrics_locales_moyennes,
        "derniere_policy": derniere_policy,
    }