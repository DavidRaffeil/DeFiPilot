# core/market_signals_adapter.py — V5.5.0
"""Adaptateur entre les signaux de marché et le moteur de stratégie.

Objectifs (hérité V4.x) :
- Rester compatible avec l'existant (signatures publiques inchangées).
- Tirer parti des métriques ajoutées dans ``core.market_signals``.
- Support optionnel d'une policy d'allocation fournie par la config.
- Journal JSONL compatible GUI.

Ajout V5.5 (Étape 4/8) :
- Calcul LECTURE SEULE d'un mode global (NORMAL/TENSION/ALERTE/CRISE/PANIC)
  à partir de la config stratégie (strategy_v5_5.json).
- Journalisation JSONL d'un événement dédié "strategy_mode_v5_5".

Contraintes :
- Aucune dépendance web.
- Bibliothèque standard + import de core.market_signals.
- Best effort : aucune erreur ne doit casser le flux.
- Commentaires/docstrings en français.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, Mapping

from core.market_signals import (
    MarketParams,
    MarketDecision,
    load_params_from_config,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
)

_CONTEXT_ALIAS: Mapping[str, str] = {
    "bull": "favorable",
    "flat": "neutre",
    "bear": "defavorable",
}

_MODES_ORDER: tuple[str, ...] = ("NORMAL", "TENSION", "ALERTE", "CRISE", "PANIC")
_SEVERITY_ORDER: Mapping[str, int] = {"NORMAL": 0, "TENSION": 1, "ALERTE": 2, "CRISE": 3, "PANIC": 4}

_TRIGGER_ALIASES: Mapping[str, tuple[str, ...]] = {
    "slippage": ("slippage", "slippage_bps", "avg_slippage_bps", "max_slippage_bps"),
    "tvl_drop": ("tvl_drop", "tvl_drop_pct", "tvl_change_pct", "tvl_drop_percent"),
    "drawdown": ("drawdown", "drawdown_pct", "max_drawdown_pct"),
    "apr_spike": ("apr_spike", "apr_change_pct", "apr_variation_pct", "apr_spike_pct"),
    "stablecoin_depeg": (
        "stablecoin_depeg",
        "stablecoin_depeg_abs",
        "depeg",
        "depeg_abs",
        "peg_price",
        "stable_price",
    ),
}


def _policy_from_cfg(context: str, cfg: Mapping[str, Any]) -> Optional[Dict[str, float]]:
    """Retourne une policy depuis la config si disponible et valide."""
    policies_cfg = cfg.get("ALLOCATION_POLICIES") if isinstance(cfg, Mapping) else None
    if not isinstance(policies_cfg, Mapping):
        return None

    if context in policies_cfg:
        policy = policies_cfg[context]
    else:
        alias_key = next((k for k, v in _CONTEXT_ALIAS.items() if v == context), None)
        if alias_key and alias_key in policies_cfg:
            policy = policies_cfg[alias_key]
        else:
            return None

    if not isinstance(policy, Mapping):
        return None

    p = {str(k): float(v) for k, v in policy.items() if k in ("risque", "modéré", "prudent")}
    total = sum(p.values())
    if total <= 0:
        return None
    if abs(total - 1.0) > 1e-9:
        p = {k: v / total for k, v in p.items()}
    return p


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _lookup_metric_in_mapping(mapping: Mapping[str, Any], aliases: tuple[str, ...]) -> Optional[float]:
    for key in aliases:
        if key in mapping and _is_number(mapping[key]):
            return float(mapping[key])
    return None


def _aggregate_from_pools(pools_stats: list[dict], aliases: tuple[str, ...]) -> Optional[float]:
    if not isinstance(pools_stats, list):
        return None

    values: list[float] = []
    for pool in pools_stats:
        if not isinstance(pool, Mapping):
            continue
        for key in aliases:
            if key in pool and _is_number(pool[key]):
                values.append(float(pool[key]))

    if not values:
        return None
    return max(values, key=lambda v: abs(v))


def _extract_metric_value(decision: MarketDecision, pools_stats: list[dict], trigger_key: str) -> Optional[float]:
    aliases = _TRIGGER_ALIASES.get(trigger_key, (trigger_key,))

    metrics = getattr(decision, "metrics", None)
    if isinstance(metrics, Mapping):
        value = _lookup_metric_in_mapping(metrics, aliases)
        if value is not None:
            return value

    return _aggregate_from_pools(pools_stats, aliases)


def _append_jsonl(journal_path: str, payload: Mapping[str, Any]) -> None:
    try:
        with open(journal_path, "a", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
            f.write("\n")
    except Exception:
        return


def _load_strategy_cfg_v5_5() -> tuple[Optional[Mapping[str, Any]], str]:
    cfg_path = os.environ.get("DEFIPILOT_STRATEGY_CFG", "config/strategy_v5_5.json")

    try:
        from core.strategy_config import load_strategy_config
    except Exception:
        return None, cfg_path

    try:
        cfg = load_strategy_config(cfg_path)
    except Exception:
        return None, cfg_path

    if not isinstance(cfg, Mapping):
        return None, cfg_path

    return cfg, cfg_path


def _get_mode_thresholds(trig_cfg: Mapping[str, Any], trigger_name: str) -> Optional[Mapping[str, Any]]:
    if trigger_name == "slippage":
        thr = trig_cfg.get("thresholds_bps")
        return thr if isinstance(thr, Mapping) else None
    if trigger_name in {"tvl_drop", "drawdown", "apr_spike"}:
        thr = trig_cfg.get("thresholds_pct")
        return thr if isinstance(thr, Mapping) else None
    if trigger_name == "stablecoin_depeg":
        thr = trig_cfg.get("thresholds_abs")
        return thr if isinstance(thr, Mapping) else None
    return None


def _trigger_level_for_value(trigger_name: str, value: float, thresholds: Mapping[str, Any]) -> Optional[str]:
    best_level = "NORMAL"

    for mode in ("TENSION", "ALERTE", "CRISE", "PANIC"):
        raw = thresholds.get(mode)
        if not _is_number(raw):
            continue

        thr = float(raw)

        if trigger_name == "stablecoin_depeg":
            active = value <= thr
        else:
            active = value >= thr

        if active and _SEVERITY_ORDER.get(mode, 0) > _SEVERITY_ORDER.get(best_level, 0):
            best_level = mode

    return None if best_level == "NORMAL" else best_level


def _mode_from_levels(levels: list[str], min_counts: Mapping[str, Any]) -> str:
    counts_at_or_above: dict[str, int] = {"TENSION": 0, "ALERTE": 0, "CRISE": 0, "PANIC": 0}

    for lvl in levels:
        s = _SEVERITY_ORDER.get(str(lvl).upper(), 0)
        if s >= _SEVERITY_ORDER["TENSION"]:
            counts_at_or_above["TENSION"] += 1
        if s >= _SEVERITY_ORDER["ALERTE"]:
            counts_at_or_above["ALERTE"] += 1
        if s >= _SEVERITY_ORDER["CRISE"]:
            counts_at_or_above["CRISE"] += 1
        if s >= _SEVERITY_ORDER["PANIC"]:
            counts_at_or_above["PANIC"] += 1

    def _min_for(mode: str, default: int) -> int:
        raw = min_counts.get(mode)
        if _is_number(raw):
            return int(raw)
        return default

    for mode in ("PANIC", "CRISE", "ALERTE", "TENSION"):
        required = _min_for(mode, 1)
        if counts_at_or_above.get(mode, 0) >= max(1, required):
            return mode

    return "NORMAL"


def _compute_mode_v5_5(decision: MarketDecision, pools_stats: list[dict]) -> tuple[str, Dict[str, Any]]:
    cfg, cfg_path = _load_strategy_cfg_v5_5()
    if not isinstance(cfg, Mapping):
        return "NORMAL", {"reason": "config_unavailable", "config_path": cfg_path}

    global_cfg = cfg.get("global")
    if isinstance(global_cfg, Mapping):
        enabled = bool(global_cfg.get("enabled", True))
        dry_run_only = bool(global_cfg.get("dry_run_only", True))
    else:
        enabled = True
        dry_run_only = True

    if not enabled:
        return "NORMAL", {"reason": "global_disabled", "config_path": cfg_path, "dry_run_only": dry_run_only}

    triggers_cfg = cfg.get("triggers")
    if not isinstance(triggers_cfg, Mapping):
        return "NORMAL", {"reason": "triggers_missing", "config_path": cfg_path, "dry_run_only": dry_run_only}

    mode_engine_cfg = cfg.get("mode_engine")
    promotion_rules = mode_engine_cfg.get("promotion_rules") if isinstance(mode_engine_cfg, Mapping) else None
    min_trigger_count = promotion_rules.get("min_trigger_count") if isinstance(promotion_rules, Mapping) else {}
    if not isinstance(min_trigger_count, Mapping):
        min_trigger_count = {}

    active_triggers: list[dict[str, Any]] = []
    evaluated_metrics: dict[str, Any] = {}
    per_trigger_level: list[str] = []

    for trigger_name in ("slippage", "tvl_drop", "drawdown", "apr_spike", "stablecoin_depeg"):
        trig_cfg = triggers_cfg.get(trigger_name)
        if not isinstance(trig_cfg, Mapping):
            continue

        if not bool(trig_cfg.get("enabled", True)):
            continue

        metric_value = _extract_metric_value(decision, pools_stats, trigger_name)
        evaluated_metrics[trigger_name] = metric_value
        if metric_value is None or not _is_number(metric_value):
            continue

        thresholds = _get_mode_thresholds(trig_cfg, trigger_name)
        if not isinstance(thresholds, Mapping):
            continue

        level = _trigger_level_for_value(trigger_name, float(metric_value), thresholds)
        if level is None:
            continue

        per_trigger_level.append(level)

        active_triggers.append(
            {
                "trigger": trigger_name,
                "value": float(metric_value),
                "level": level,
                "thresholds": {m: float(thresholds[m]) for m in thresholds if _is_number(thresholds[m])},
            }
        )

    mode = _mode_from_levels(per_trigger_level, min_trigger_count)

    details: Dict[str, Any] = {
        "config_path": cfg_path,
        "active_triggers": active_triggers,
        "evaluated_metrics": evaluated_metrics,
        "min_trigger_count": dict(min_trigger_count),
        "dry_run_only": dry_run_only,
    }
    return mode, details


def _journaliser_mode_v5_5(
    decision: MarketDecision,
    mode: str,
    details: Dict[str, Any],
    run_id: Optional[str],
    journal_path: str,
) -> None:
    payload = {
        "event_type": "strategy_mode_v5_5",
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "version": "V5.5.0",
        "run_id": run_id,
        "context": getattr(decision, "context", None),
        "details": details,
    }
    _append_jsonl(journal_path, payload)


def calculer_contexte_et_policy(
    pools_stats: list[dict],
    cfg: dict,
    last_context: Optional[str] = None,
    run_id: Optional[str] = None,
    version: str = "V5.5.0",
    journal_path: str = "journal_signaux.jsonl",
) -> Tuple[MarketDecision, Dict[str, float]]:
    params: MarketParams = load_params_from_config(cfg)

    decision: MarketDecision = detect_market_context(
        pools_stats=pools_stats,
        params=params,
        last_context=last_context,
    )

    policy = _policy_from_cfg(decision.context, cfg) or get_allocation_policy_for_context(decision.context)

    journaliser_signaux(
        decision,
        policy,
        run_id=run_id,
        version=version,
        journal_path=journal_path,
    )

    try:
        mode_v5_5, details_v5_5 = _compute_mode_v5_5(decision, pools_stats)
        try:
            setattr(decision, "mode_v5_5", mode_v5_5)
            setattr(decision, "mode_v5_5_details", details_v5_5)
        except Exception:
            pass
        _journaliser_mode_v5_5(decision, mode_v5_5, details_v5_5, run_id, journal_path)
    except Exception:
        pass

    return decision, policy
