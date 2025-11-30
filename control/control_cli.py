# control/control_cli.py — V4.9.0
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .aggregator import AggregatedSnapshot, aggregate_from_config
from .anomaly_detector import Anomaly, detect_anomalies, summarize_anomalies

logger = logging.getLogger(__name__)


def build_arg_parser() -> argparse.ArgumentParser:
    """Crée le parseur CLI pour agréger des journaux DeFiPilot et détecter des anomalies."""
    parser = argparse.ArgumentParser(
        description=(
            "Agrège des journaux DeFiPilot puis détecte les anomalies pour ControlPilot."
        ),
    )
    parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        type=Path,
        required=False,
        help="Chemins des journaux JSONL à analyser.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("journal_anomalies.jsonl"),
        help=(
            "Chemin du fichier JSONL où consigner les anomalies "
            "(défaut: journal_anomalies.jsonl)."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Active un mode verbeux avec journalisation INFO.",
    )
    return parser


def configure_logging(verbose: bool) -> None:
    """Configure un logging minimaliste pour l'exécution du CLI."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _serialize_anomaly(anomaly: Anomaly) -> Dict[str, Any]:
    """Prépare un dictionnaire sérialisable décrivant une anomalie."""
    try:
        record: Dict[str, Any] = asdict(anomaly)  # type: ignore[arg-type]
    except TypeError:
        record = {
            "timestamp": getattr(anomaly, "timestamp", datetime.utcnow()),
            "severity": getattr(anomaly, "severity", "inconnue"),
            "code": getattr(anomaly, "code", ""),
            "message": getattr(anomaly, "message", ""),
            "details": getattr(anomaly, "details", {}),
        }

    timestamp = record.get("timestamp", None)
    if isinstance(timestamp, datetime):
        record["timestamp"] = timestamp.isoformat()
    elif timestamp is None:
        record["timestamp"] = datetime.utcnow().isoformat()
    else:
        record["timestamp"] = str(timestamp)

    record.setdefault("severity", getattr(anomaly, "severity", "inconnue"))
    record.setdefault("code", getattr(anomaly, "code", ""))
    record.setdefault("message", getattr(anomaly, "message", ""))

    details = record.get("details")
    if not isinstance(details, dict):
        record["details"] = {"raw_details": details}

    return record


def write_anomalies_jsonl(path: Path, anomalies: List[Anomaly]) -> None:
    """Écrit les anomalies dans un fichier JSONL, une ligne par entrée."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            for anomaly in anomalies:
                record = _serialize_anomaly(anomaly)
                stream.write(json.dumps(record, ensure_ascii=False))
                stream.write("\n")
    except OSError as exc:
        logger.error("Impossible d'écrire le journal des anomalies '%s': %s", path, exc)
        raise


def _format_summary(
    summary: Dict[str, Any],
    anomalies: List[Anomaly],
    files_count: int,
    output_path: Path | str,
) -> str:
    """Construit un résumé textuel des anomalies."""
    if isinstance(summary, dict):
        total = summary.get("total")
        by_severity: Any = summary.get("by_severity")
        codes: Any = summary.get("codes")
    else:
        total = None
        by_severity = None
        codes = None

    if not isinstance(total, int):
        total = len(anomalies)

    if not isinstance(by_severity, dict):
        by_severity = {}

    if not isinstance(codes, list):
        codes = [getattr(a, "code", "") for a in anomalies if getattr(a, "code", "")]

    return (
        "=== ControlPilot — Résumé des anomalies ===\n"
        f"Fichiers analysés : {files_count}\n"
        f"Anomalies totales : {total}\n"
        f"Par sévérité      : {by_severity}\n"
        f"Codes détectés    : {codes}\n"
        f"Journal anomalies : {output_path}\n"
        "==========================================="
    )


def run_from_args(args: argparse.Namespace) -> int:
    """Exécute le pipeline CLI à partir des arguments parsés."""
    if not args.files:
        print("Erreur: aucun fichier journal fourni.", file=sys.stderr)
        return 1

    try:
        input_files = [str(path) for path in args.files]
        config: Dict[str, Any] = {"files": input_files}

        snapshot: AggregatedSnapshot = aggregate_from_config(config)
        anomalies: List[Anomaly] = detect_anomalies(snapshot)

        output_path = args.output if isinstance(args.output, Path) else Path(str(args.output))
        write_anomalies_jsonl(output_path, anomalies)

        summary: Dict[str, Any] = summarize_anomalies(anomalies)
        formatted = _format_summary(summary, anomalies, len(input_files), output_path)
        print(formatted)
        return 0
    except Exception as exc:  # noqa: BLE001 - propagation contrôlée pour CLI
        logger.exception("Échec de l'exécution du CLI ControlPilot: %s", exc)
        print(
            "Erreur: l'exécution du contrôle a échoué. Consultez les logs pour plus de détails.",
            file=sys.stderr,
        )
        return 2


def main() -> int:
    """Point d'entrée principal de la ligne de commande ControlPilot."""
    parser = build_arg_parser()
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args.verbose)
    return run_from_args(args)


if __name__ == "__main__":
    raise SystemExit(main())
