from core.strategy_engine import StrategyEngine, PoolCandidate
from core.strategy_context import StrategyContext


def afficher_allocations(label_contexte: str, ctx: StrategyContext) -> None:
    print("\n==============================")
    print(f"Contexte testé : {label_contexte}")
    print("==============================")

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

    print("Profile utilisé :", result["profile"])
    print("Contexte retourné :", result["context"])
    print("Allocations cibles :")
    for alloc in result["allocations"]:
        print(f"  - pool_id={alloc['pool_id']}, target_pct={alloc['target_pct']:.4f}")


def main() -> None:
    # Contexte favorable
    ctx_fav = StrategyContext(
        timestamp="2025-11-15T10:00:00Z",
        label="favorable",
        ai_score=0.7,
        confiance=0.8,
        resume="Contexte favorable de test",
        metrics={},
        nb_signaux=3,
    )

    # Contexte défavorable
    ctx_defav = StrategyContext(
        timestamp="2025-11-15T10:05:00Z",
        label="defavorable",
        ai_score=0.3,
        confiance=0.8,
        resume="Contexte défavorable de test",
        metrics={},
        nb_signaux=3,
    )

    afficher_allocations("favorable", ctx_fav)
    afficher_allocations("defavorable", ctx_defav)


if __name__ == "__main__":
    main()
