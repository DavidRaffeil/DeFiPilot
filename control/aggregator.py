# control/aggregator.py — V4.9.0
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AggregatedSnapshot:
    """Représente un instantané agrégé des journaux de DeFiPilot."""

    timestamp: datetime
    source_files: List[str]
    metrics: Dict[str, Any]


def parse_timestamp(value: str | datetime) -> datetime:
    """Convertit une valeur en objet :class:`datetime` normalisé.

    Paramètres
    ----------
    value : str | datetime
        Chaîne de caractères au format ISO 8601 ou objet datetime déjà préparé.

    Retour
    ------
    datetime
        Objet datetime sans information de fuseau.

    Lève
    ----
    ValueError
        Lorsque la valeur fournie ne peut pas être interprétée comme un datetime.
    """

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Impossible de parser un timestamp vide.")

        if text.endswith("Z"):
            text = text[:-1]

        try:
            return datetime.fromisoformat(text)
        except ValueError as exc:  # pragma: no cover - futur tests
            raise ValueError(f"Format de timestamp invalide: {value!r}") from exc

    raise ValueError(
        "Le timestamp doit être fourni sous forme de chaîne ISO 8601 ou de datetime."
    )


def load_and_aggregate(
    files: List[str],
    encoding: str = "utf-8",
) -> AggregatedSnapshot:
    """Charge une liste de journaux et construit un instantané minimal.

    La fonction se contente de lire des fichiers JSONL existants, de compter
    les entrées valides et de produire un dictionnaire de métriques rudimentaires.
    Les fichiers inexistants ou illisibles sont ignorés avec un avertissement.
    """

    processed_files: List[str] = []
    by_file: Dict[str, int] = {}
    total_events = 0

    for path in files:
        if not os.path.exists(path):
            logger.warning("Fichier introuvable ignoré: %s", path)
            continue

        _, ext = os.path.splitext(path)
        if ext.lower() != ".jsonl":
            logger.info("Extension non prise en charge, fichier ignoré: %s", path)
            continue

        try:
            with open(path, "r", encoding=encoding) as handle:
                valid_lines = 0
                for line in handle:
                    content = line.strip()
                    if not content:
                        continue

                    try:
                        json.loads(content)
                    except json.JSONDecodeError:
                        logger.debug("Ligne JSON invalide ignorée dans %s", path)
                        continue

                    valid_lines += 1

        except OSError:
            logger.warning("Impossible de lire le fichier: %s", path)
            continue

        processed_files.append(path)
        by_file[path] = valid_lines
        total_events += valid_lines

    if not processed_files:
        raise FileNotFoundError("Aucun fichier JSONL valide n'a été trouvé pour l'agrégation.")

    metrics: Dict[str, Any] = {
        "total_events": total_events,
        "by_file": by_file,
    }

    snapshot = AggregatedSnapshot(
        timestamp=datetime.utcnow(),
        source_files=processed_files,
        metrics=metrics,
    )
    return snapshot


def aggregate_from_config(config: Dict[str, Any]) -> AggregatedSnapshot:
    """Construit un instantané agrégé à partir d'une configuration simple."""

    files_obj: Optional[Any] = config.get("files")
    if not isinstance(files_obj, list) or not files_obj:
        raise ValueError(
            "La configuration doit contenir une liste de fichiers sous la clé 'files'."
        )

    str_files: List[str] = []
    for item in files_obj:
        if isinstance(item, str):
            str_files.append(item)
        else:
            logger.warning("Chemin ignoré car non textuel: %r", item)

    if not str_files:
        raise ValueError(
            "La configuration ne fournit aucun chemin de fichier exploitable pour l'agrégation."
        )

    return load_and_aggregate(str_files)