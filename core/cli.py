# core/cli.py – V6.0

from __future__ import annotations

import logging
from core.strategy_engine import StrategyEngine

LOGGER = logging.getLogger("DeFiPilot.CLI")


def run_cli(argv: list[str]) -> int:
    """Entrée CLI principale pour DeFiPilot V6."""
    LOGGER.info("Démarrage CLI DeFiPilot V6")

    try:
        engine = StrategyEngine("config/strategy_v6_0.json")

        result = engine.run()

        for action in result["actions"]:
            print(action)

        LOGGER.info("Cycle stratégie terminé")
        return 0

    except Exception as exc:
        LOGGER.exception("Erreur pendant l'exécution CLI : %s", exc)
        return 1