# smoke_test_market_signals.py
from core.market_signals import (
    MarketParams, load_params_from_config, detect_market_context,
    get_allocation_policy_for_context, journaliser_signaux
)

# --- Cas A: favorable (APR/volume/TVL élevés)
pools_A = [
    {"apr": 0.18, "volume_24h": 2_500_000, "tvl": 25_000_000},
    {"apr": 0.12, "volume_24h": 1_200_000, "tvl": 12_000_000},
]

# --- Cas B: neutre (moyens)
pools_B = [
    {"apr": 0.05, "volume_24h": 400_000, "tvl": 6_000_000},
    {"apr": 0.04, "volume_24h": 300_000, "tvl": 5_000_000},
]

# --- Cas C: défavorable (faibles)
pools_C = [
    {"apr": 0.01, "volume_24h": 50_000, "tvl": 800_000},
    {"apr": 0.0, "volume_24h": 0, "tvl": 0},
]

params = MarketParams()
for label, pools in [("A:favorable", pools_A), ("B:neutre", pools_B), ("C:defavorable", pools_C)]:
    decision = detect_market_context(pools, params, last_context=None)
    policy = get_allocation_policy_for_context(decision.context)
    total = sum(policy.values())
    print(f"[{label}] context={decision.context} score={decision.score:.4f} "
          f"metrics={decision.metrics} policy={policy} total={total:.6f}")
