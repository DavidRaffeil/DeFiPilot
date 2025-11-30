# core/strategy_snapshot.py – V5.1.1
"""
Utilitaires pour lire le dernier snapshot de stratégie/journal.

Ce module est utilisé par la GUI et par d'autres composants pour récupérer
un résumé "prêt à consommer" de la stratégie actuelle :

- contexte de marché (favorable / neutre / défavorable, etc.),
- score de la décision,
- profil effectif,
- nombre de signaux pris en compte,
- scoring des pools (top3, gain total journalier, profil),
- allocation actuelle par catégorie de risque,
- allocation simulée après rééquilibrage.

Les données sont lues dans le fichier JSONL :

    data/logs/journal_strategie.jsonl

produit par journal_daemon.py (V5.1.5+).

À partir de la V5.1.1, ce module fournit également une fonction utilitaire
pour journaliser une décision de stratégie dans un fichier dédié :

    data/logs/journal_decisions.jsonl
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import json


# Même chemin que STRATEGY_JOURNAL_PATH dans journal_daemon.py
DEFAULT_STRATEGY_JOURNAL_PATH = Path("data/logs/journal_strategie.jsonl")

# Nouveau journal dédié aux décisions de stratégie
DEFAULT_DECISIONS_JOURNAL_PATH = Path("data/logs/journal_decisions.jsonl")

StrategySnapshot = Dict[str, Any]

__all__ = [
    "DEFAULT_STRATEGY_JOURNAL_PATH",
    "DEFAULT_DECISIONS_JOURNAL_PATH",
    "lire_dernier_snapshot",
    "charger_snapshot_brut",
    "journaliser_decision",
]


def charger_snapshot_brut(path: Path = DEFAULT_STRATEGY_JOURNAL_PATH) -> Optional[StrategySnapshot]:
    """
    Lit le fichier JSONL de stratégie et renvoie le DERNIER snapshot brut (dict).

    - Si le fichier n'existe pas : retourne None.
    - Si le fichier est vide ou corrompu : retourne None.
    - Si la dernière ligne n'est pas un JSON valide : essaie les lignes précédentes.

    Cette fonction ne fait *aucune* transformation métier : elle renvoie
    exactement le dict tel qu'il est stocké dans le journal.
    """
    if not path.exists() or not path.is_file():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            lignes = f.readlines()
    except OSError:
        return None

    # On parcourt les lignes en partant de la fin pour trouver un JSON valide
    for raw in reversed(lignes):
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    return None


def lire_dernier_snapshot(path: Path = DEFAULT_STRATEGY_JOURNAL_PATH) -> Optional[StrategySnapshot]:
    """
    Renvoie le dernier snapshot de stratégie dans une forme "prête à consommer"
    par la GUI ou d'autres modules.

    Si aucun snapshot n'est disponible, retourne None.

    Le dict retourné contient au minimum les clés suivantes (si présentes
    dans le journal d'origine) :

    - timestamp
    - run_id
    - version
    - context
    - decision_score
    - profil
    - nb_signaux
    - allocation_actuelle_usd
    - allocation_simulee_apres_reequilibrage
    - scoring (solde_reference_usd, gain_total_journalier_usd, resultats_top3, profil_scoring)
    """
    brut = charger_snapshot_brut(path=path)
    if brut is None:
        return None

    # On ne modifie pas la structure, mais on peut garantir quelques types simples
    snapshot: StrategySnapshot = dict(brut)

    # Normalisation minimale de certains champs numériques (best effort)
    try:
        if "decision_score" in snapshot:
            snapshot["decision_score"] = float(snapshot["decision_score"])
    except (TypeError, ValueError):
        pass

    try:
        if "nb_signaux" in snapshot:
            snapshot["nb_signaux"] = int(snapshot["nb_signaux"])
    except (TypeError, ValueError):
        pass

    scoring = snapshot.get("scoring")
    if isinstance(scoring, dict):
        try:
            scoring["solde_reference_usd"] = float(scoring.get("solde_reference_usd", 0.0))
        except (TypeError, ValueError):
            scoring["solde_reference_usd"] = 0.0
        try:
            scoring["gain_total_journalier_usd"] = float(
                scoring.get("gain_total_journalier_usd", 0.0)
            )
        except (TypeError, ValueError):
            scoring["gain_total_journalier_usd"] = 0.0

    snapshot["scoring"] = scoring

    return snapshot


# ---------------------------------------------------------------------------
# Journalisation des décisions (V5.1.1)
# ---------------------------------------------------------------------------


def _safe_float(value: Any) -> Optional[float]:
    """Convertit en float ou renvoie None en cas d'erreur."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_decision_entry(snapshot: StrategySnapshot) -> Dict[str, Any]:
    """
    Construit une entrée de décision normalisée à partir d'un snapshot.

    Le format retourné est pensé pour être stable et exploitable
    par la GUI ou d'autres modules. Il ne dépend pas de la structure
    interne exacte de journal_daemon, mais uniquement des clés exposées
    dans le snapshot.
    """
    scoring = snapshot.get("scoring")
    scoring_dict: Dict[str, Any] = {}
    if isinstance(scoring, dict):
        solde_ref = _safe_float(scoring.get("solde_reference_usd"))
        gain_jour = _safe_float(scoring.get("gain_total_journalier_usd"))
        scoring_dict["solde_reference_usd"] = solde_ref if solde_ref is not None else 0.0
        scoring_dict["gain_total_journalier_usd"] = gain_jour if gain_jour is not None else 0.0

        # Extraction du Top 1 depuis resultats_top3 si disponible
        top3 = scoring.get("resultats_top3")
        top1_obj: Dict[str, Any] = {}
        if isinstance(top3, list) and top3:
            first = top3[0]
            label = None
            score_val: Optional[float] = None
            gain_val: Optional[float] = None

            if isinstance(first, (list, tuple)) and first:
                try:
                    label = first[0]
                except Exception:
                    label = str(first)
                if len(first) > 1:
                    score_val = _safe_float(first[1])
                if len(first) > 2:
                    gain_val = _safe_float(first[2])
            else:
                label = str(first)

            if label is not None:
                top1_obj["label"] = label
            if score_val is not None:
                top1_obj["score"] = score_val
            if gain_val is not None:
                top1_obj["gain_usd"] = gain_val

        if top1_obj:
            scoring_dict["top1"] = top1_obj

    entry: Dict[str, Any] = {
        "timestamp": snapshot.get("timestamp"),
        "run_id": snapshot.get("run_id"),
        "version": snapshot.get("version"),
        "context": snapshot.get("context"),
        "profil": snapshot.get("profil"),
        "decision_score": _safe_float(snapshot.get("decision_score")),
        "nb_signaux": snapshot.get("nb_signaux"),
        "allocation_actuelle_usd": snapshot.get("allocation_actuelle_usd"),
        "allocation_simulee_apres_reequilibrage": snapshot.get(
            "allocation_simulee_apres_reequilibrage"
        ),
        "scoring": scoring_dict,
    }

    return entry


def journaliser_decision(
    snapshot: Optional[StrategySnapshot],
    path: Path = DEFAULT_DECISIONS_JOURNAL_PATH,
) -> None:
    """
    Journalise une décision de stratégie dans un fichier JSONL dédié.

    Paramètres
    ----------
    snapshot :
        Snapshot de stratégie tel que retourné par `lire_dernier_snapshot`,
        ou dict équivalent. Si snapshot est None, la fonction ne fait rien.

    path :
        Chemin du fichier JSONL de sortie. Par défaut, utilise
        DEFAULT_DECISIONS_JOURNAL_PATH.

    Comportement
    ------------
    - Si `snapshot` est None, la fonction retourne immédiatement.
    - Le dossier parent est créé au besoin.
    - L'entrée est ajoutée en fin de fichier, sous forme d'une seule ligne JSON.
    """
    if snapshot is None:
        return

    entry = _build_decision_entry(snapshot)

    # Création du dossier parent si nécessaire
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        # On ignore les erreurs de création de dossier pour ne pas casser
        # la stratégie en cas de problème de FS ; la décision ne sera
        # simplement pas journalisée.
        return

    try:
        with path.open("a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
    except OSError:
        # Même logique : on n'interrompt pas la stratégie si le journal
        # ne peut pas être écrit.
        return
