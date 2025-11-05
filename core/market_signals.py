# core/market_signals.py — V4.2.0
"""Signaux de marché et scoring de contexte (V4.2.0)

Objectifs V4.2 :
- Préparer l'intégration de métriques avancées *sans casser* l'existant.
- Conserver les clés et signatures publiques.
- Ajouter des métriques : volatilité (dispersion APR), tendance APR (24h vs 7j) — optionnelles.
- Normaliser proprement le score même si le total des poids change.

Notes de compatibilité :
- Le journal JSONL inclut désormais *deux* clés de métriques :
  - ``metrics_locales`` (clé *préférée* par l'UI V4.1.x)
  - ``metrics`` (conservée pour compat ascendante)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, fields, replace
from datetime import datetime, timezone
from typing import Dict, Mapping, Optional, Sequence, Iterable, Tuple


# ============================
# Paramètres
# ============================
@dataclass(frozen=True)
class MarketParams:
    """Paramètres de pondération et de normalisation pour le scoring.

    Les nouveaux poids (V4.2) sont à 0 par défaut afin de ne pas changer
    le comportement tant qu'ils ne sont pas activés dans la config.
    """

    # Poids historiques (somme initiale = 1.0)
    apr_weight: float = 0.4
    volume_weight: float = 0.35
    tvl_weight: float = 0.25

    # Normalisations historiques
    apr_normalizer: float = 0.1
    volume_normalizer: float = 1_000_000.0
    tvl_normalizer: float = 10_000_000.0

    # Lissage (EWMA simple, conservé pour compat)
    smoothing_factor: float = 0.6

    # Seuils de décision
    favorable_threshold: float = 0.65
    unfavorable_threshold: float = 0.35

    # === V4.2 : nouveaux poids (désactivés par défaut) ===
    volatility_weight: float = 0.0  # pondère la stabilité (plus c'est stable, mieux c'est)
    apr_trend_weight: float = 0.0   # pondère l'évolution des APR (tendance)

    # === V4.2 : normalisateurs pour nouvelles métriques ===
    volatility_normalizer: float = 1.0  # CV ~ échelle 0..1 (1 = CV de 100%)
    apr_trend_normalizer: float = 0.1   # variation relative (10% ≈ 0.1)


# ============================
# Décision & extraction
# ============================
@dataclass(frozen=True)
class MarketDecision:
    """Décision de contexte de marché dérivée du score pondéré."""

    context: str
    score: float
    metrics: Dict[str, float]
    last_context: Optional[str] = None


def load_params_from_config(cfg: Mapping[str, object]) -> MarketParams:
    """Charge les paramètres de marché à partir d'un mapping de config.

    Seules les clés présentes dans :class:`MarketParams` sont utilisées.
    """

    params = MarketParams()
    config_section = cfg.get("market_params") if isinstance(cfg, Mapping) else None
    if not isinstance(config_section, Mapping):
        return params

    valid_fields = {field.name for field in fields(params)}
    filtered_values = {k: v for k, v in config_section.items() if k in valid_fields}
    if not filtered_values:
        return params

    return replace(params, **filtered_values)


# ============================
# Utilitaires
# ============================

def _extract_positive_values(
    stats: Sequence[Mapping[str, float]],
    key: str,
) -> list[float]:
    """Extrait les valeurs strictement positives d'une clé donnée."""

    values: list[float] = []
    for item in stats:
        value = item.get(key)
        if isinstance(value, (int, float)) and value > 0:
            values.append(float(value))
    return values


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stdev(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = _mean(values)
    var = sum((x - m) ** 2 for x in values) / (n - 1)
    return math.sqrt(var)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _compute_volatility_score(apr_values: Sequence[float], normalizer: float) -> Tuple[float, float]:
    """Retourne (score_volatilité, cv) où le score augmente quand la volatilité baisse.

    - On mesure la dispersion *entre pools* des APR instantanés via le **coefficient de variation** : CV = stdev/mean.
    - Plus CV est **faible**, plus la situation est considérée stable (score proche de 1).
    - `normalizer` (~1.0) règle à quelle échelle un CV donné est ramené entre 0 et 1.
    """
    if not apr_values:
        return 0.0, 0.0
    m = _mean(apr_values)
    if m <= 0:
        return 0.0, 0.0
    cv = _stdev(apr_values) / m
    score = _clamp(1.0 - (cv / max(1e-12, normalizer)))
    return score, cv


def _compute_apr_trend_score(stats: Sequence[Mapping[str, float]], normalizer: float) -> Tuple[float, float]:
    """Estime une tendance APR moyenne à partir de clés disponibles.

    Heuristique simple : si une pool fournit `apr_24h` et `apr_7d`, on considère la
    variation relative t = (apr_24h - apr_7d) / max(1e-12, abs(apr_7d)).
    On moyenne ces t, puis on mappe sur [0,1] via : score = clamp(0.5 + 0.5 * (t/normalizer)).
    """
    trends: list[float] = []
    for item in stats:
        a24 = item.get("apr_24h")
        a7 = item.get("apr_7d")
        if isinstance(a24, (int, float)) and isinstance(a7, (int, float)) and a7 != 0:
            t = (float(a24) - float(a7)) / max(1e-12, abs(float(a7)))
            trends.append(t)
    if not trends:
        return 0.0, 0.0
    tavg = _mean(trends)
    score = _clamp(0.5 + 0.5 * (tavg / max(1e-12, normalizer)))
    return score, tavg


# ============================
# Détection de contexte
# ============================

def detect_market_context(
    pools_stats: Sequence[Mapping[str, float]],
    params: MarketParams,
    last_context: Optional[str] = None,
) -> MarketDecision:
    """Détermine le contexte de marché actuel en fonction des stats de pools.

    - Conserve les métriques historiques (apr_mean, volume_sum, tvl_sum).
    - Ajoute des métriques avancées V4.2 (volatility_cv, apr_trend_avg) — optionnelles.
    - Score normalisé par la somme des poids actifs pour rester dans [0,1].
    """

    apr_values = _extract_positive_values(pools_stats, "apr")
    volume_values = _extract_positive_values(pools_stats, "volume_24h")
    tvl_values = _extract_positive_values(pools_stats, "tvl")

    apr_mean = _mean(apr_values)
    volume_sum = sum(volume_values)
    tvl_sum = sum(tvl_values)

    # Scores de base (bornés 0..1)
    apr_score = _clamp(apr_mean / params.apr_normalizer) if params.apr_normalizer else 0.0
    vol_score = _clamp(volume_sum / params.volume_normalizer) if params.volume_normalizer else 0.0
    tvl_score = _clamp(tvl_sum / params.tvl_normalizer) if params.tvl_normalizer else 0.0

    # V4.2 : métriques avancées
    volty_score, cv = _compute_volatility_score(apr_values, params.volatility_normalizer)
    trend_score, trend_avg = _compute_apr_trend_score(pools_stats, params.apr_trend_normalizer)

    # Agrégation pondérée (on normalise par la somme des poids *actifs*)
    weights = [
        (apr_score, params.apr_weight),
        (vol_score, params.volume_weight),
        (tvl_score, params.tvl_weight),
        (volty_score, params.volatility_weight),
        (trend_score, params.apr_trend_weight),
    ]
    total_w = sum(w for _, w in weights)
    if total_w <= 0:
        # garde-fou : si tout est à 0, on retombe sur l'ancien comportement APR/volume/TVL
        total_w = params.apr_weight + params.volume_weight + params.tvl_weight
        if total_w <= 0:
            total_w = 1.0
    raw = sum(s * w for s, w in weights) / total_w

    # Lissage conservé (ici identique à raw, mais compatible avec d'autres schémas)
    alpha = _clamp(params.smoothing_factor)
    smoothed = alpha * raw + (1 - alpha) * raw

    if smoothed >= params.favorable_threshold:
        context = "favorable"
    elif smoothed <= params.unfavorable_threshold:
        context = "defavorable"
    else:
        context = "neutre"

    metrics = {
        "apr_mean": apr_mean,
        "volume_sum": volume_sum,
        "tvl_sum": tvl_sum,
        # V4.2 : nouvelles métriques exposées
        "volatility_cv": cv,
        "apr_trend_avg": trend_avg,
    }

    return MarketDecision(
        context=context,
        score=smoothed,
        metrics=metrics,
        last_context=last_context,
    )


# ============================
# Allocation
# ============================

def get_allocation_policy_for_context(context: str) -> Dict[str, float]:
    """Retourne la politique d'allocation adaptée au contexte fourni."""

    policies: Dict[str, Dict[str, float]] = {
        "favorable": {"risque": 0.6, "modéré": 0.3, "prudent": 0.1},
        "neutre": {"risque": 0.4, "modéré": 0.4, "prudent": 0.2},
        "defavorable": {"risque": 0.2, "modéré": 0.3, "prudent": 0.5},
    }

    if context not in policies:
        raise ValueError(f"Contexte inconnu: {context}")

    policy = policies[context]
    total = sum(policy.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError("La somme des pondérations doit être égale à 1.0")
    return policy


# ============================
# Journalisation
# ============================

def journaliser_signaux(
    decision: MarketDecision,
    policy: Mapping[str, float],
    run_id: Optional[str] = None,
    version: Optional[str] = None,
    journal_path: str = "journal_signaux.jsonl",
) -> None:
    """Journalise la décision + policy en JSON Lines.

    Compatibilité UI V4.1.x : on écrit **metrics_locales** (préférée par l'UI)
    et **metrics** (héritage) pour ne rien casser.
    """

    # Timestamp unique en UTC, format ISO 8601 avec suffixe Z pour compat
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    ts_iso = now_utc.isoformat().replace("+00:00", "Z")

    entry = {
        "timestamp": ts_iso,                # clé historique (existant dans ton journal)
        "ts": ts_iso,                       # clé courte, conservée pour l'avenir
        "context": decision.context,
        "score": decision.score,
        "metrics_locales": decision.metrics,  # clé préférée par l'UI V4.1.x
        "metrics": decision.metrics,          # conservée pour compat ascendante
        "last_context": decision.last_context,
        "policy": dict(policy),
        "run_id": run_id,
        "version": version,
        "journal_path": journal_path,       # pour tracer la source exacte
    }

    with open(journal_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
