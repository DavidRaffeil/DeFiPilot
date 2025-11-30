# control/ai_analyzer.py — V5.0.0
"""DeFiPilot / ControlPilot — Analyse contextuelle IA (basique) (V5.0.0)

FR (objectif)
==============
Module d'analyse locale (sans dépendances) qui infère un **contexte IA**
("favorable", "neutre", "defavorable") et un **score de confiance** à partir
d'une fenêtre de signaux consolidés (APR, TVL, volume, volatilité, tendance APR).

EN (goal)
=========
Local (no-deps) analyzer that infers an **AI context** ("favorable", "neutral",
"unfavorable") and a **confidence score** from a window of consolidated signals
(APR, TVL, volume, volatility, APR trend).

Contraintes / Constraints
-------------------------
- Python 3.11+, bibliothèque standard uniquement.
- Entrées : liste d'objets (dict) issus d'un JSONL consolidé (clés "metrics" ou
  "metrics_locales", timestamps en ISO, context FR/EN accepté).
- Sorties principales :
  - `ai_context` (str)
  - `confidence` (float in [0, 1])
  - `score` (float, non borné — utile pour debug)
  - `window` (résumé de la fenêtre utilisée)
  - `features` (valeurs agrégées calculées)

Seuils et logique basique
-------------------------
Nous combinons des features agrégées sur la fenêtre :
- apr_mean_avg        → plus c'est haut, mieux c'est (>= ~0.12 favorable)
- apr_trend_avg_avg   → plus c'est haut, mieux c'est (>= 0.0 tendance haussière)
- volume_per_tvl      → volume_sum / tvl_sum (activité relative)
- volatility_cv_avg   → plus c'est bas, mieux c'est

Score linéaire :
    score = + 2.0 * apr_mean_avg
            + 1.5 * apr_trend_avg_avg
            + 1.0 * volume_per_tvl
            - 1.0 * volatility_cv_avg

Décision :
- score >= 0.15 → "favorable"
- score <= -0.05 → "defavorable"
- sinon → "neutre"

`confidence` est dérivée d'une sigmoïde simple sur |score - seuil_du_centre|,
bornée à [0, 1].

Utilisation (CLI de démonstration)
----------------------------------
Ce module expose un CLI minimal (lecture JSONL → fenêtre → inférence → print).
Il **n'écrit rien** dans les journaux (l'intégration/écriture sera faite à l'étape 3).

Exemples :
  python -m control.ai_analyzer --file journal_signaux.jsonl --last 32
  python -m control.ai_analyzer --file journal_signaux.jsonl --minutes 60

"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import argparse
import json
import math
from typing import Any, Iterable, Sequence

ISO_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S",
)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


@dataclass(slots=True)
class AIResult:
    ai_context: str
    confidence: float
    score: float
    window: dict[str, Any]
    features: dict[str, float]


def _nan_to_none(x: Any) -> float | None:
    try:
        fx = float(x)
        if math.isnan(fx) or math.isinf(fx):
            return None
        return fx
    except Exception:
        return None


def _extract_metrics(obj: dict[str, Any]) -> dict[str, float | None]:
    block = obj.get("metrics") or obj.get("metrics_locales") or {}
    return {
        "apr_mean": _nan_to_none(block.get("apr_mean")),
        "tvl_sum": _nan_to_none(block.get("tvl_sum")),
        "volume_sum": _nan_to_none(block.get("volume_sum")),
        "volatility_cv": _nan_to_none(block.get("volatility_cv")),
        "apr_trend_avg": _nan_to_none(block.get("apr_trend_avg")),
    }


def _safe_mean(values: Sequence[float | None]) -> float | None:
    xs = [v for v in values if isinstance(v, (int, float)) and not math.isnan(v)]
    return sum(xs) / len(xs) if xs else None


def _bound01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def infer_ai_context(records: Sequence[dict[str, Any]]) -> AIResult:
    """Infère le contexte IA et la confiance à partir d'une fenêtre de `records`.

    `records` : liste d'objets JSON (déjà parsés) issus d'un JSONL consolidé.
    """
    if not records:
        # Choix conservateur si aucune donnée
        return AIResult(
            ai_context="neutre",
            confidence=0.0,
            score=0.0,
            window={"count": 0, "from": None, "to": None},
            features={"apr_mean_avg": 0.0, "apr_trend_avg_avg": 0.0, "volume_per_tvl": 0.0, "volatility_cv_avg": 0.0},
        )

    # bornes temporelles
    dts = [
        _parse_iso(obj.get("timestamp") or obj.get("ts"))
        for obj in records
    ]
    dts_ok = [d for d in dts if d is not None]
    from_ts = min(dts_ok).isoformat() + "Z" if dts_ok else None
    to_ts = max(dts_ok).isoformat() + "Z" if dts_ok else None

    mlist = [_extract_metrics(o) for o in records]

    apr_mean_avg = _safe_mean([m["apr_mean"] for m in mlist]) or 0.0
    apr_trend_avg_avg = _safe_mean([m["apr_trend_avg"] for m in mlist]) or 0.0

    tvl_sum_total = sum([m["tvl_sum"] or 0.0 for m in mlist])
    volume_sum_total = sum([m["volume_sum"] or 0.0 for m in mlist])
    volatility_cv_avg = _safe_mean([m["volatility_cv"] for m in mlist]) or 0.0

    volume_per_tvl = (volume_sum_total / tvl_sum_total) if tvl_sum_total > 0 else 0.0

    # Score linéaire simple (voir docstring)
    score = (
        2.0 * apr_mean_avg
        + 1.5 * apr_trend_avg_avg
        + 1.0 * volume_per_tvl
        - 1.0 * volatility_cv_avg
    )

    # Décision
    if score >= 0.15:
        ai_ctx = "favorable"
        center = 0.15
    elif score <= -0.05:
        ai_ctx = "defavorable"
        center = -0.05
    else:
        ai_ctx = "neutre"
        center = 0.05  # distance au milieu de la bande neutre (~[-0.05,0.15])

    # Confiance : sigmoïde sur l'écart au centre (plus on s'éloigne, plus c'est confiant)
    gap = abs(score - center)
    confidence = 1.0 / (1.0 + math.exp(-10.0 * gap))  # pente 10.0
    confidence = _bound01(confidence)

    return AIResult(
        ai_context=ai_ctx,
        confidence=confidence,
        score=score,
        window={"count": len(records), "from": from_ts, "to": to_ts},
        features={
            "apr_mean_avg": apr_mean_avg,
            "apr_trend_avg_avg": apr_trend_avg_avg,
            "volume_per_tvl": volume_per_tvl,
            "volatility_cv_avg": volatility_cv_avg,
        },
    )


# ===================== CLI de démonstration ===================== #

def _load_jsonl(path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _select_window(records: list[dict[str, Any]], last: int | None, minutes: int | None) -> list[dict[str, Any]]:
    if minutes:
        # filtre sur la fenêtre temporelle glissante (minutes)
        now = max((_parse_iso(r.get("timestamp") or r.get("ts")) for r in records), default=None)
        if now is None:
            return records[-last:] if last else records
        cutoff = now - timedelta(minutes=minutes)
        win = [r for r in records if (_parse_iso(r.get("timestamp") or r.get("ts")) or now) >= cutoff]
        return win[-last:] if last else win
    if last:
        return records[-last:]
    return records


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="control.ai_analyzer",
        description="Inférence de contexte IA sur une fenêtre de signaux consolidés (démo).",
    )
    ap.add_argument("--file", required=True, help="Fichier JSONL d'entrée (journal_signaux.jsonl)")
    ap.add_argument("--last", type=int, default=32, help="Taille max de la fenêtre (n dernières lignes)")
    ap.add_argument("--minutes", type=int, default=None, help="Fenêtre glissante en minutes (prioritaire sur --last)")
    args = ap.parse_args(argv)

    data = _load_jsonl(args.file)
    window = _select_window(data, last=args.last, minutes=args.minutes)

    res = infer_ai_context(window)

    print("================= AI ANALYZE (BASIC) =================")
    print(f"File     : {args.file}")
    print(f"Window   : count={res.window['count']} from={res.window['from']} to={res.window['to']}")
    print(f"Features : {res.features}")
    print(f"Score    : {res.score:.6f}")
    print(f"AI ctx   : {res.ai_context}  | confidence={res.confidence:.3f}")
    print("======================================================")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
