# test_strategy_adapter.py
from core.engine.strategy_adapter import calculer_contexte_et_policy

# Jeux de données simples (comme le smoke test)
pools_stats = [
    {"apr": 0.05, "volume_24h": 400_000, "tvl": 6_000_000},
    {"apr": 0.04, "volume_24h": 300_000, "tvl": 5_000_000},
]

# Seuil favorable plus strict pour que ce cas soit "neutre"
cfg = {"market_params": {"favorable_threshold": 0.70}}

decision, policy = calculer_contexte_et_policy(
    pools_stats=pools_stats,
    cfg=cfg,
    last_context=None,
    run_id="test-adapter",
    version="V4.0.4",
    journal_path="journal_signaux.jsonl",
)

print("context=", decision.context)
print("score=", round(decision.score, 4))
print("policy=", policy)
print("policy_total=", round(sum(policy.values()), 6))
