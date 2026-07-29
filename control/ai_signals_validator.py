# control/ai_signals_validator.py — V5.0.0
"""DeFiPilot / ControlPilot — Validateur de journaux de signaux agrégés (V5.0.0)

FR 🇫🇷
-------
But :
  - Lire un fichier JSONL de signaux consolidés (APR, TVL, volatilité, contexte, etc.).
  - Vérifier la présence et la cohérence des champs clés.
  - Produire un résumé (période couverte, répartition des contextes, statistiques rapides).
  - Sortie *0* si tout est valide (ou seulement des avertissements), *1* si erreurs bloquantes.

EN
---
Goal:
  - Read a consolidated signals JSONL file (APR, TVL, volatility, context, etc.).
  - Validate key fields and their ranges/types.
  - Print a quick summary (covered period, context distribution, quick stats).
  - Exit *0* on success (or warnings only), *1* if blocking errors are found.

Contraintes / Constraints:
  - Python 3.11+, bibliothèque standard uniquement / standard library only.
  - Aucune dépendance externe.

Utilisation / Usage:
  python -m control.ai_signals_validator --file journal_signaux.jsonl
  python -m control.ai_signals_validator --file path/to/file.jsonl --strict
  python -m control.ai_signals_validator --help

Note:
  - Le validateur accepte les clés "metrics" et/ou "metrics_locales".
  - Les contextes acceptés (FR/EN) : {"favorable", "neutre", "defavorable", "neutral", "unfavorable"}.
  - Les champs métriques attendus si présents : apr_mean, tvl_sum, volume_sum, volatility_cv, apr_trend_avg (facultatif).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from collections import Counter
from datetime import datetime
from typing import Any, Iterable

ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",  # ex: 2025-11-05T10:05:47Z
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S",
)

ACCEPTED_CONTEXTS = {"favorable", "neutre", "defavorable", "neutral", "unfavorable"}

EXPECTED_METRIC_KEYS = {"apr_mean", "tvl_sum", "volume_sum", "volatility_cv"}
OPTIONAL_METRIC_KEYS = {"apr_trend_avg"}


@dataclasses.dataclass(slots=True)
class RecordIssue:
    line_no: int
    level: str  # "ERROR" | "WARN"
    message: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="control.ai_signals_validator",
        description="Valide un fichier JSONL de signaux consolidés pour ControlPilot/DeFiPilot.",
    )
    p.add_argument(
        "--file",
        required=True,
        help="Chemin du fichier JSONL (ex: journal_signaux.jsonl)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Échoue (exit 1) en présence d'avertissements (WARN).",
    )
    return p.parse_args(argv)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def _is_finite_number(x: Any) -> bool:
    if isinstance(x, (int, float)):
        return not (math.isnan(x) or math.isinf(x))
    return False


def _validate_metrics(prefix: str, metrics: dict[str, Any], line_no: int) -> Iterable[RecordIssue]:
    present = set(metrics.keys())
    missing = EXPECTED_METRIC_KEYS - present
    for k in sorted(missing):
        yield RecordIssue(line_no, "ERROR", f"{prefix}: clé manquante '{k}'")

    # Ranges & types
    def check_nonneg(name: str):
        v = metrics.get(name)
        if not _is_finite_number(v):
            return RecordIssue(line_no, "ERROR", f"{prefix}: '{name}' doit être un nombre fini")
        if name in {"tvl_sum", "volume_sum", "volatility_cv"} and v < 0:
            return RecordIssue(line_no, "ERROR", f"{prefix}: '{name}' doit être ≥ 0 (val={v})")
        if name == "apr_mean" and not (-1.0 <= float(v) <= 5.0):  # bornes raisonnables (‑100%..+500%)
            return RecordIssue(line_no, "WARN", f"{prefix}: 'apr_mean' hors plage raisonnable (val={v})")
        return None

    for key in EXPECTED_METRIC_KEYS:
        issue = check_nonneg(key)
        if issue:
            yield issue

    # Optionnel mais si présent, doit être nombre fini
    if "apr_trend_avg" in metrics and not _is_finite_number(metrics.get("apr_trend_avg")):
        yield RecordIssue(line_no, "ERROR", f"{prefix}: 'apr_trend_avg' doit être un nombre fini")


def validate_file(path: str) -> tuple[list[RecordIssue], dict[str, Any]]:
    issues: list[RecordIssue] = []
    contexts = Counter()
    first_dt: datetime | None = None
    last_dt: datetime | None = None
    n = 0

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                issues.append(RecordIssue(i, "ERROR", f"JSON invalide: {e}"))
                continue

            n += 1
            ts = obj.get("timestamp") or obj.get("ts")
            dt = _parse_iso(ts)
            if dt is None:
                issues.append(RecordIssue(i, "WARN", "Horodatage manquant ou invalide (timestamp/ts)"))
            else:
                first_dt = dt if first_dt is None else min(first_dt, dt)
                last_dt = dt if last_dt is None else max(last_dt, dt)

            ctx = (obj.get("context") or obj.get("contexte") or "").lower()
            if ctx not in ACCEPTED_CONTEXTS:
                issues.append(RecordIssue(i, "WARN", f"Contexte inconnu ou manquant: '{ctx}'"))
            else:
                contexts[ctx] += 1

            # Accept either 'metrics' or 'metrics_locales' (or both)
            metrics_blocks = []
            if isinstance(obj.get("metrics"), dict):
                metrics_blocks.append(("metrics", obj["metrics"]))
            if isinstance(obj.get("metrics_locales"), dict):
                metrics_blocks.append(("metrics_locales", obj["metrics_locales"]))

            if not metrics_blocks:
                issues.append(RecordIssue(i, "ERROR", "Aucun bloc 'metrics' ni 'metrics_locales'"))
            else:
                for name, block in metrics_blocks:
                    issues.extend(_validate_metrics(name, block, i))

    summary = {
        "lines": n,
        "first_ts": first_dt.isoformat() + "Z" if first_dt else None,
        "last_ts": last_dt.isoformat() + "Z" if last_dt else None,
        "contexts": dict(contexts),
    }
    return issues, summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = args.file

    try:
        issues, summary = validate_file(path)
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable: {path}")
        return 1
    except Exception as e:  # garde‑fou
        print(f"[ERREUR] Exception lors de la validation: {e}")
        return 1

    errors = [x for x in issues if x.level == "ERROR"]
    warns = [x for x in issues if x.level == "WARN"]

    print("================= RÉSUMÉ / SUMMARY =================")
    print(f"Fichier           : {path}")
    print(f"Lignes lues       : {summary['lines']}")
    print(f"Première entrée   : {summary['first_ts']}")
    print(f"Dernière entrée   : {summary['last_ts']}")
    print(f"Contexts (FR/EN)  : {summary['contexts']}")
    print("=====================================================")

    if issues:
        print("\nDétails:")
        for it in issues:
            print(f" - L{i:=04d}".replace("i", str(it.line_no)), it.level, ":", it.message)

    status = 0
    if errors:
        status = 1
    elif warns and args.strict:
        status = 1

    if status == 0:
        print("\n[OK] Validation terminée — aucun problème bloquant.")
        if warns:
            print(f"[AVERTISSEMENTS] {len(warns)} avertissement(s) — utiliser --strict pour échouer en leur présence.")
    else:
        print("\n[ECHEC] Des problèmes ont été détectés.")
        print(f"        Erreurs     : {len(errors)} | Avertissements : {len(warns)}")

    return status


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
