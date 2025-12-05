from core.strategy_engine import StrategyEngine, PoolCandidate
from core.strategy_context import StrategyContext


def main() -> None:
    # Contexte global "favorable" de test
    ctx = StrategyContext(
        timestamp="2025-11-15T10:00:00Z",
        label="favorable",
        ai_score=0.7,
        confiance=0.8,
        resume="Contexte de test",
        metrics={},
        nb_signaux=3,
    )

    # Deux pools factices pour tester le tri
    pools = [
        PoolCandidate(
            pool_id="poolA",
            platform="dex1",
            chain="polygon",
            symbols="USDC-WETH",
            tvl=1_000_000,
            apr=50.0,
        ),
        PoolCandidate(
            pool_id="poolB",
            platform="dex1",
            chain="polygon",
            symbols="USDC-MATIC",
            tvl=500_000,
            apr=80.0,
        ),
    ]

    engine = StrategyEngine(config_path="strategy_config.json", dry_run=True)
    result = engine.run(pools=pools, context=ctx)

    print("=== CONTEXTE ===")
    print(result["context"])
    print("=== CANDIDATES (ordre) ===")
    print([c["pool_id"] for c in result["candidates"]])


if __name__ == "__main__":
    main()
