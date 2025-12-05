# core/journal_strategy.py – V5.3.0
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)


def _get_strategy_journal_path() -> Path:
    """
    Retourne le chemin du journal de stratégie.

    Utilise la variable d'environnement ``DEFIPILOT_STRATEGY_JOURNAL`` si
    définie, sinon ``data/journal_strategy.jsonl``.
    """
    env_path = os.environ.get("DEFIPILOT_STRATEGY_JOURNAL")
    if env_path:
        return Path(env_path)
    return Path("data") / "journal_strategy.jsonl"


def _ensure_parent_dir(path: Path) -> None:
    """
    S'assure que le répertoire parent du fichier existe.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(
            "Impossible de créer le répertoire parent pour le journal de stratégie : %s",
            path,
        )


def _now_iso_utc() -> str:
    """
    Retourne la date/heure courante au format ISO 8601 en UTC.
    """
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def journaliser_entree_strategique(
    *,
    event_type: str,
    version: str,
    run_id: str,
    context: str,
    profil: str,
    decision_score: Optional[float] = None,
    nb_signaux: Optional[int] = None,
    source_signaux: Optional[str] = None,
    allocation_avant_usd: Optional[Mapping[str, float]] = None,
    allocation_apres_usd: Optional[Mapping[str, float]] = None,
    delta_allocation_usd: Optional[Mapping[str, float]] = None,
    pools_selectionnees: Optional[Sequence[Mapping[str, Any]]] = None,
    performance: Optional[Mapping[str, Any]] = None,
    meta: Optional[Mapping[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construit et écrit une entrée de journal stratégique dans le fichier JSONL.

    Cette fonction est volontairement générique pour pouvoir être utilisée
    aussi bien par le moteur de stratégie que par un module de rééquilibrage.

    :param event_type: Type d'événement (ex: ``"strategy_decision"``,
        ``"rebalancing_applied"``).
    :param version: Version de DeFiPilot au moment de la décision (ex: ``"V5.3.0"``).
    :param run_id: Identifiant de la boucle/cycle courant (souvent celui du
        journal des signaux).
    :param context: Contexte de marché détecté (ex: ``"favorable"``,
        ``"neutre"``, ``"defavorable"``).
    :param profil: Profil d'investissement choisi pour ce cycle
        (ex: ``"Prudent"``, ``"Modere"``, ``"Risque"``).
    :param decision_score: Score global de décision (si disponible).
    :param nb_signaux: Nombre total de signaux utilisés.
    :param source_signaux: Source principale des signaux (fichier ou module).
    :param allocation_avant_usd: Allocation avant décision, en USD par profil.
    :param allocation_apres_usd: Allocation après décision, en USD par profil.
    :param delta_allocation_usd: Différence allocation_apres - allocation_avant.
    :param pools_selectionnees: Liste des pools retenues pour ce cycle.
    :param performance: Bloc de performance (gain du jour, gain cumulé, etc.).
    :param meta: Bloc libre pour ajouter des informations contextuelles.
    :param timestamp: Horodatage ISO 8601 (si None, l'heure courante UTC est utilisée).
    :return: Le dictionnaire représentant l'entrée écrite.
    """
    entry: Dict[str, Any] = {
        "timestamp": timestamp or _now_iso_utc(),
        "version": version,
        "run_id": run_id,
        "event_type": event_type,
        "context": context,
        "profil": profil,
    }

    if decision_score is not None:
        entry["decision_score"] = float(decision_score)

    if nb_signaux is not None:
        entry["nb_signaux"] = int(nb_signaux)

    if source_signaux is not None:
        entry["source_signaux"] = str(source_signaux)

    if allocation_avant_usd is not None:
        entry["allocation_avant_usd"] = dict(allocation_avant_usd)

    if allocation_apres_usd is not None:
        entry["allocation_apres_usd"] = dict(allocation_apres_usd)

    if delta_allocation_usd is not None:
        entry["delta_allocation_usd"] = dict(delta_allocation_usd)

    if pools_selectionnees is not None:
        entry["pools_selectionnees"] = list(pools_selectionnees)

    if performance is not None:
        entry["performance"] = dict(performance)

    if meta is not None:
        entry["meta"] = dict(meta)

    path = _get_strategy_journal_path()
    _ensure_parent_dir(path)

    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False))
            f.write("\n")
    except Exception:
        logger.exception(
            "Erreur lors de l'écriture dans le journal de stratégie : %s",
            path,
        )

    return entry


def lire_derniere_entree_strategique() -> Optional[Dict[str, Any]]:
    """
    Lit et retourne la dernière entrée du journal de stratégie.

    :return: Un dictionnaire représentant la dernière entrée, ou None si le
        journal est vide ou inaccessible.
    """
    path = _get_strategy_journal_path()
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            last_line: Optional[str] = None
            for line in f:
                line = line.strip()
                if line:
                    last_line = line

        if not last_line:
            return None

        return json.loads(last_line)
    except Exception:
        logger.exception(
            "Erreur lors de la lecture de la dernière entrée du journal de stratégie : %s",
            path,
        )
        return None


def lire_historique_strategie(max_lignes: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Lit l'historique complet (ou partiel) du journal de stratégie.

    :param max_lignes: Nombre maximal de lignes à retourner en partant de la fin.
        Si None, toutes les lignes sont retournées.
    :return: Une liste de dictionnaires représentant les entrées du journal.
    """
    path = _get_strategy_journal_path()
    if not path.exists():
        return []

    try:
        entries: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            if max_lignes is None or max_lignes <= 0:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(
                            "Ligne JSON invalide ignorée dans le journal de stratégie : %r",
                            line,
                        )
            else:
                # Lecture simple puis découpe depuis la fin.
                all_lines: List[str] = [ln.strip() for ln in f if ln.strip()]
                slice_lines = all_lines[-max_lignes:]
                for line in slice_lines:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(
                            "Ligne JSON invalide ignorée dans le journal de stratégie : %r",
                            line,
                        )

        return entries
    except Exception:
        logger.exception(
            "Erreur lors de la lecture de l'historique du journal de stratégie : %s",
            path,
        )
        return []
