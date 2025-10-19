# core/market_signals.py — V4.0.4
"""Module de signaux de marché pour déterminer un contexte d'investissement."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, replace
from datetime import datetime, timezone
from typing import Dict, Mapping, Optional, Sequence


@dataclass(frozen=True)
class MarketParams:
    """Paramètres de pondération et de normalisation pour le scoring de marché."""

    apr_weight: float = 0.4
    volume_weight: float = 0.35
    tvl_weight: float = 0.25
    apr_normalizer: float = 0.1
    volume_normalizer: float = 1_000_000.0
    tvl_normalizer: float = 10_000_000.0
    smoothing_factor: float = 0.6
    favorable_threshold: float = 0.65
    unfavorable_threshold: float = 0.35


@dataclass(frozen=True)
class MarketDecision:
    """Décision de contexte de marché dérivée du score pondéré."""

    context: str
    score: float
    metrics: Dict[str, float]
    last_context: Optional[str] = None


def load_params_from_config(cfg: Mapping[str, object]) -> MarketParams:
    """Charge les paramètres de marché à partir d'une configuration.

    Seules les clés présentes dans :class:`MarketParams` sont utilisées.
    """

    params = MarketParams()
    config_section = cfg.get("market_params") if isinstance(cfg, Mapping) else None
    if not isinstance(config_section, Mapping):
        return params

    valid_fields = {field.name for field in fields(params)}
    filtered_values = {
        key: value
        for key, value in config_section.items()
        if key in valid_fields
    }
    if not filtered_values:
        return params

    return replace(params, **filtered_values)


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


def detect_market_context(
    pools_stats: Sequence[Mapping[str, float]],
    params: MarketParams,
    last_context: Optional[str] = None,
) -> MarketDecision:
    """Détermine le contexte de marché actuel en fonction des statistiques des pools."""

    apr_values = _extract_positive_values(pools_stats, "apr")
    volume_values = _extract_positive_values(pools_stats, "volume_24h")
    tvl_values = _extract_positive_values(pools_stats, "tvl")

    apr_mean = sum(apr_values) / len(apr_values) if apr_values else 0.0
    volume_sum = sum(volume_values)
    tvl_sum = sum(tvl_values)

    apr_score = min(1.0, apr_mean / params.apr_normalizer) if params.apr_normalizer else 0.0
    vol_score = min(1.0, volume_sum / params.volume_normalizer) if params.volume_normalizer else 0.0
    tvl_score = min(1.0, tvl_sum / params.tvl_normalizer) if params.tvl_normalizer else 0.0

    raw = (
        apr_score * params.apr_weight
        + vol_score * params.volume_weight
        + tvl_score * params.tvl_weight
    )
    smoothed = params.smoothing_factor * raw + (1 - params.smoothing_factor) * raw

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
    }

    return MarketDecision(
        context=context,
        score=smoothed,
        metrics=metrics,
        last_context=last_context,
    )


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


def journaliser_signaux(
    decision: MarketDecision,
    policy: Mapping[str, float],
    run_id: Optional[str] = None,
    version: Optional[str] = None,
    journal_path: str = "journal_signaux.jsonl",
) -> None:
    """Journalise la décision de marché et la politique associée en format JSON Lines."""

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "context": decision.context,
        "score": decision.score,
        "metrics": decision.metrics,
        "last_context": decision.last_context,
        "policy": dict(policy),
        "run_id": run_id,
        "version": version,
    }

    with open(journal_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")