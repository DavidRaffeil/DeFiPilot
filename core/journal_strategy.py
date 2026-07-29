# core/journal_strategy.py — V6.0.0
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

logger = logging.getLogger(__name__)

DEFAULT_STRATEGY_JOURNAL_PATH = Path("data/logs/journal_strategie.jsonl")


def _get_strategy_journal_path() -> Path:
    return DEFAULT_STRATEGY_JOURNAL_PATH


def _ensure_parent_dir(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(
            "Impossible de créer le répertoire parent pour le journal de stratégie : %s",
            path,
        )


def _now_iso_utc() -> str:
    """Retourne la date/heure courante au format ISO 8601 en UTC."""
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
    profil: Optional[str] = None,
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
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Construit et écrit une entrée de journal stratégique dans le fichier JSONL.

    Compatible V6.0 : accepte l'alias `profil_effectif` via kwargs.
    """

    # Alias V6.0 : profil_effectif -> profil (fallback uniquement)
    if profil is None:
        profil_effectif = kwargs.get("profil_effectif")
        if isinstance(profil_effectif, str) and profil_effectif.strip():
            profil = profil_effectif
        else:
            # Aucun profil fourni : on sécurise sans lever d'exception bloquante
            profil = "inconnu"

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
    """Lit et retourne la dernière entrée du journal de stratégie."""
    path = _get_strategy_journal_path()
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            lignes = f.readlines()
            if not lignes:
                return None
            return json.loads(lignes[-1])
    except Exception:
        logger.exception(
            "Erreur lors de la lecture du journal de stratégie : %s",
            path,
        )
        return None


__all__ = [
    "journaliser_entree_strategique",
    "lire_derniere_entree_strategique",
]
