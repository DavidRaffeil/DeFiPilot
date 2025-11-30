# control/anomaly_detector.py — V4.9.0
"""Détection simple d'anomalies sur un instantané agrégé."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List
import logging

from .aggregator import AggregatedSnapshot


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Anomaly:
    """Représente une anomalie détectée dans les journaux agrégés."""

    timestamp: datetime
    severity: str
    code: str
    message: str
    details: Dict[str, Any]


HIGH_VOLUME_THRESHOLD = 10_000


def _normalize_total_events(metrics: Dict[str, Any]) -> int:
    """Extrait et normalise le nombre total d'événements."""
    total = metrics.get("total_events", 0)
    if isinstance(total, bool):
        logger.debug("Valeur booléenne inattendue pour total_events: %s", total)
        return 0
    if isinstance(total, int):
        return total
    if isinstance(total, float):
        return int(total)
    logger.debug("total_events absent ou invalide (%r), utilisation de 0", total)
    return 0


def _normalize_by_file(metrics: Dict[str, Any]) -> Dict[str, int]:
    """Retourne une copie filtrée des métriques par fichier."""
    raw_by_file = metrics.get("by_file", {})
    if not isinstance(raw_by_file, dict):
        logger.debug("by_file absent ou invalide (%r), utilisation d'un dict vide", raw_by_file)
        return {}

    cleaned: Dict[str, int] = {}
    for path, count in raw_by_file.items():
        if not isinstance(path, str):
            logger.debug("Clé de fichier ignorée car non str: %r", path)
            continue
        if isinstance(count, bool):
            logger.debug("Compteur booléen ignoré pour %s: %s", path, count)
            continue
        if isinstance(count, (int, float)):
            cleaned[path] = int(count)
        else:
            logger.debug("Compteur non numérique ignoré pour %s: %r", path, count)
    return cleaned


def detect_anomalies(snapshot: AggregatedSnapshot) -> List[Anomaly]:
    """Analyse les métriques d'un instantané agrégé et détecte des anomalies simples."""
    metrics: Dict[str, Any] = getattr(snapshot, "metrics", {})
    if not isinstance(metrics, dict):
        logger.debug("Métriques inattendues sur l'instantané: %r", metrics)
        metrics = {}

    anomalies: List[Anomaly] = []
    detection_time = datetime.utcnow()

    total_events = _normalize_total_events(metrics)
    by_file = _normalize_by_file(metrics)

    if total_events <= 0:
        anomalies.append(
            Anomaly(
                timestamp=detection_time,
                severity="warning",
                code="NO_EVENTS",
                message="Aucun événement valide n'a été trouvé dans les journaux agrégés.",
                details={"total_events": total_events},
            )
        )

    for path, count in by_file.items():
        if count <= 0:
            anomalies.append(
                Anomaly(
                    timestamp=detection_time,
                    severity="warning",
                    code="FILE_EMPTY",
                    message=f"Aucun événement valide n'a été trouvé dans le fichier {path}.",
                    details={"file": path, "events": count},
                )
            )

    if total_events > HIGH_VOLUME_THRESHOLD:
        anomalies.append(
            Anomaly(
                timestamp=detection_time,
                severity="info",
                code="HIGH_EVENT_VOLUME",
                message="Le nombre total d'événements dépasse le seuil attendu.",
                details={"total_events": total_events, "threshold": HIGH_VOLUME_THRESHOLD},
            )
        )

    return anomalies


def has_critical_anomalies(anomalies: List[Anomaly]) -> bool:
    """Indique si la liste contient au moins une anomalie critique."""
    for anomaly in anomalies:
        if anomaly.severity == "critical":
            return True
    return False


def summarize_anomalies(anomalies: List[Anomaly]) -> Dict[str, Any]:
    """Synthétise les anomalies sous forme d'indicateurs agrégés."""
    by_severity: Dict[str, int] = {}
    codes: set[str] = set()

    for anomaly in anomalies:
        by_severity[anomaly.severity] = by_severity.get(anomaly.severity, 0) + 1
        codes.add(anomaly.code)

    return {
        "total": len(anomalies),
        "by_severity": by_severity,
        "codes": sorted(codes),
    }


__all__ = [
    "Anomaly",
    "detect_anomalies",
    "has_critical_anomalies",
    "summarize_anomalies",
]