# test_market_policy_integration.py – V4.0.4
"""
Test d'intégration minimal : market_signals -> policy d'allocation.

Usage (depuis la racine du projet, avec dossier core/ présent) :
    python test_market_policy_integration.py

Ce script :
1) Définit un cfg minimal (MARKET_SIGNALS + ALLOCATION_POLICIES).
2) Construit des pools_stats synthétiques (trois scénarios : bull/flat/bear).
3) Appelle detect_market_context(...) pour chaque scénario.
4) Mappe vers la politique d'allocation correspondante via get_allocation_policy_for_context(...).
5) Affiche un récap (context, score, policy) et journalise en JSONL.
"""

from core.market_signals import (
    MarketParams,
    MarketDecision,
    load_params_from_config,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
)

def build_cfg(hysteresis_margin: float = 1.0, cooldown_cycles: int = 0, min_samples: int = 3) -> dict:
    """Construit une configuration minimale pour les tests d'intégration."""
    return {
        "MARKET_SIGNALS": {
            "apr_up_threshold_pct": 5.0,
            "apr_down_threshold_pct": -5.0,
            "tvl_up_threshold_pct": 3.0,
            "tvl_down_threshold_pct": -3.0,
            "min_samples": min_samples,
            "smoothing_alpha": 0.3,
            "cooldown_cycles": cooldown_cycles,
            "hysteresis_margin": hysteresis_margin,
            "weights_apr": 0.6,
            "weights_tvl": 0.4,
            "override_context": None,
        },
        "ALLOCATION_POLICIES": {
            "bull": {"risque": 0.60, "modéré": 0.30, "prudent": 0.10},
            "flat": {"risque": 0.33, "modéré": 0.34, "prudent": 0.33},
            "bear": {"risque": 0.10, "modéré": 0.30, "prudent": 0.60},
        },
    }

def run_case(label: str, pools_stats: list[dict], params: MarketParams, policies: dict, last_context: str | None):
    """Exécute un scénario, affiche la décision et la politique, et journalise en JSONL."""
    decision: MarketDecision = detect_market_context(pools_stats, params, last_context=last_context)
    policy = get_allocation_policy_for_context(decision.context, policies)

    print(f"\n[{label}]")
    print(f" context   : {decision.context}")
    print(f" score     : {decision.score:.3f}")
    print(f" apr_med   : {decision.indicators.apr_change_pct_median:.3f}%")
    print(f" tvl_med   : {decision.indicators.tvl_change_pct_median:.3f}%")
    print(f" samples   : {decision.indicators.sample_size}")
    print(f" reason    : {decision.reason}")
    print(f" policy    : risque={policy['risque']:.2f}  modéré={policy['modéré']:.2f}  prudent={policy['prudent']:.2f}")

    journaliser_signaux(decision, run_id=f"policy-integ-{label}", version="V4.0.4", path_jsonl="journal_signaux.jsonl")

def main():
    # --- Config & params
    cfg = build_cfg(hysteresis_margin=0.0, cooldown_cycles=0, min_samples=3)
    params: MarketParams = load_params_from_config(cfg)
    policies = cfg["ALLOCATION_POLICIES"]

    # --- Scénarios synthétiques
    pools_bull = [
        {"apr_change_pct": +10.0, "tvl_change_pct": +7.0},
        {"apr_change_pct": +9.0,  "tvl_change_pct": +5.5},
        {"apr_change_pct": +11.0, "tvl_change_pct": +6.0},
    ]
    pools_flat = [
        {"apr_change_pct": +1.0, "tvl_change_pct": 0.0},
        {"apr_change_pct": +0.5, "tvl_change_pct": +0.2},
        {"apr_change_pct":  0.0, "tvl_change_pct": -0.3},
    ]
    pools_bear = [
        {"apr_change_pct": -10.0, "tvl_change_pct": -6.0},
        {"apr_change_pct": -9.0,  "tvl_change_pct": -5.5},
        {"apr_change_pct": -11.0, "tvl_change_pct": -6.5},
    ]

    # last_context=None pour illustrer un démarrage de run
    run_case("BULL", pools_bull, params, policies, last_context=None)
    run_case("FLAT", pools_flat, params, policies, last_context=None)
    run_case("BEAR", pools_bear, params, policies, last_context=None)

    print("\nJournal JSONL: journal_signaux.jsonl (1 ligne par scénario)")

if __name__ == "__main__":
    main()