# test_market_threshold_B.py
from core.market_signals import MarketParams, detect_market_context, get_allocation_policy_for_context

# Cas B (moyen) identique au smoke test
pools_B = [
    {"apr": 0.05, "volume_24h": 400_000, "tvl": 6_000_000},
    {"apr": 0.04, "volume_24h": 300_000, "tvl": 5_000_000},
]

# Seuil favorable plus strict: 0.70
params = MarketParams(favorable_threshold=0.70)

decision = detect_market_context(pools_B, params)
policy = get_allocation_policy_for_context(decision.context)
print(f"context={decision.context} score={decision.score:.4f} policy={policy} total={sum(policy.values()):.6f}")
