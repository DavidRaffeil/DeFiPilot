"""Test minimal de l'adaptateur de signaux de marché.

Ce module valide le bon fonctionnement de ``calculer_contexte_et_policy`` en
utilisant des données synthétiques faciles à vérifier. Il peut être exécuté
depuis la racine du projet avec ``python test_market_signals_adapter.py``.
"""

from __future__ import annotations

from typing import Dict, List

from core.market_signals_adapter import calculer_contexte_et_policy


def build_cfg(
    hysteresis_margin: float = 0.0, cooldown_cycles: int = 0, min_samples: int = 3
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Construit une configuration minimale pour l'adaptateur de signaux.

    Parameters
    ----------
    hysteresis_margin: float
        Marge de sécurité appliquée pour éviter les oscillations de contexte.
    cooldown_cycles: int
        Nombre de cycles pendant lesquels on évite de changer de contexte.
    min_samples: int
        Nombre minimal d'échantillons requis pour analyser un signal.
    """

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


def run_case(label: str, pools_stats: List[Dict[str, float]], cfg: Dict) -> None:
    """Exécute un scénario synthétique et affiche le contexte retourné."""

    decision, policy = calculer_contexte_et_policy(
        pools_stats=pools_stats,
        cfg=cfg,
        last_context=None,
        run_id=f"adapter-{label}",
        version="V4.0.4",
        journal_path="journal_signaux.jsonl",
    )
    print(f"\n[{label}]")
    print(f" context   : {decision.context}")
    print(f" score     : {decision.score:.3f}")
    print(f" apr_med   : {decision.indicators.apr_change_pct_median:.3f}%")
    print(f" tvl_med   : {decision.indicators.tvl_change_pct_median:.3f}%")
    print(f" samples   : {decision.indicators.sample_size}")
    print(f" reason    : {decision.reason}")
    print(
        " policy    : "
        f"risque={policy['risque']:.2f}  modéré={policy['modéré']:.2f}  "
        f"prudent={policy['prudent']:.2f}"
    )


def main() -> None:
    """Point d'entrée du script de test."""

    cfg = build_cfg(hysteresis_margin=0.0, cooldown_cycles=0, min_samples=3)

    pools_bull = [
        {"apr_change_pct": +10.0, "tvl_change_pct": +7.0},
        {"apr_change_pct": +9.0, "tvl_change_pct": +5.5},
        {"apr_change_pct": +11.0, "tvl_change_pct": +6.0},
    ]
    pools_flat = [
        {"apr_change_pct": +1.0, "tvl_change_pct": 0.0},
        {"apr_change_pct": +0.5, "tvl_change_pct": +0.2},
        {"apr_change_pct": 0.0, "tvl_change_pct": -0.3},
    ]
    pools_bear = [
        {"apr_change_pct": -10.0, "tvl_change_pct": -6.0},
        {"apr_change_pct": -9.0, "tvl_change_pct": -5.5},
        {"apr_change_pct": -11.0, "tvl_change_pct": -6.5},
    ]

    run_case("BULL", pools_bull, cfg)
    run_case("FLAT", pools_flat, cfg)
    run_case("BEAR", pools_bear, cfg)

    print("\nJournal JSONL: journal_signaux.jsonl (1 ligne par scénario)")


if __name__ == "__main__":
    main()