# tests/test_rebalancing.py – V6.0.0
"""Tests unitaires dédiés pour l'Optimisation de la Logique de Rééquilibrage et Allocation (Étape 2.2)."""

import unittest

from core.rebalancing import (
    _verifier_rentabilite_nette,
    generer_plan_reequilibrage_contexte,
)


class TestRebalancingOptimization(unittest.TestCase):
    def test_net_profitability_cancellation(self) -> None:
        """Vérifier l'annulation du rééquilibrage lorsque les frais de gas/slippage dépassent les gains."""
        params_strategie = {
            "mode_execution": "simulation",
            "pool_id": "test_pool",
            "rebalance": {
                "enabled": True,
                "threshold_pct": 0.01,
                "estimated_gas_usd_per_action": 10.0,  # Frais de Gas prohibitifs (10$ par action)
                "min_profitability_ratio": 5.0,
            },
        }
        allocation_actuelle = {"Prudent": 50.0, "Modere": 50.0, "Risque": 0.0}

        plan = generer_plan_reequilibrage_contexte(
            context="neutre",
            profil_effectif="modere",
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=100.0,
            signaux_normalises=[],
            params_strategie=params_strategie,
            run_id="run_test_rentabilite",
            journal_path="data/logs/journal_strategie.jsonl",
        )

        self.assertEqual(len(plan["actions"]), 0)
        self.assertIsNotNone(plan["safety"]["motif_annulation"])
        self.assertIn("Rentabilité nette insuffisante", plan["safety"]["motif_annulation"])

    def test_min_trade_amount_filtering(self) -> None:
        """Vérifier le filtrage des ordres inférieurs à min_trade_amount_usd."""
        params_strategie = {
            "mode_execution": "simulation",
            "pool_id": "test_pool",
            "rebalance": {
                "enabled": True,
                "threshold_pct": 0.001,
                "min_trade_amount_usd": 50.0,  # Seuil min à 50$
            },
        }
        # Allocation presque parfaite : petits deltas de 5$
        allocation_actuelle = {"Prudent": 32.0, "Modere": 38.0, "Risque": 30.0}

        plan = generer_plan_reequilibrage_contexte(
            context="neutre",
            profil_effectif="modere",
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=100.0,
            signaux_normalises=[],
            params_strategie=params_strategie,
            run_id="run_test_min_trade",
            journal_path="data/logs/journal_strategie.jsonl",
        )

        # Les deltas de 2$ à 5$ sont tous inférieurs à min_trade_amount_usd (50$), donc zéro action générée
        self.assertEqual(len(plan["actions"]), 0)

    def test_min_score_delta_enforcement(self) -> None:
        """Vérifier l'annulation si l'écart de score (score_delta) est inférieur au seuil min (min_score_delta)."""
        params_strategie = {
            "mode_execution": "simulation",
            "pool_id": "test_pool",
            "score_delta": 0.1,  # Delta négligeable
            "rebalance": {
                "enabled": True,
                "min_score_delta": 1.0,  # Exigence minimale de 1.0
            },
        }
        allocation_actuelle = {"Prudent": 100.0, "Modere": 0.0, "Risque": 0.0}

        plan = generer_plan_reequilibrage_contexte(
            context="neutre",
            profil_effectif="modere",
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=100.0,
            signaux_normalises=[],
            params_strategie=params_strategie,
            run_id="run_test_score_delta",
            journal_path="data/logs/journal_strategie.jsonl",
        )

        self.assertEqual(len(plan["actions"]), 0)
        self.assertIsNotNone(plan["safety"]["motif_annulation"])
        self.assertIn("inférieur au seuil d'arbitrage minimum", plan["safety"]["motif_annulation"])

    def test_profitable_rebalancing_plan_generation(self) -> None:
        """Vérifier qu'un plan nettement rentable et valide génère les actions d'arbitrage."""
        params_strategie = {
            "mode_execution": "simulation",
            "pool_id": "aave_v3_usdt",
            "rebalance": {
                "enabled": True,
                "threshold_pct": 0.05,
                "min_trade_amount_usd": 10.0,
                "estimated_gas_usd_per_action": 0.05,
                "min_profitability_ratio": 1.1,
            },
        }
        allocation_actuelle = {"Prudent": 100_000.0, "Modere": 0.0, "Risque": 0.0}

        plan = generer_plan_reequilibrage_contexte(
            context="favorable",
            profil_effectif="modere",
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=100_000.0,
            signaux_normalises=[],
            params_strategie=params_strategie,
            run_id="run_test_profitable",
            journal_path="data/logs/journal_strategie.jsonl",
        )

        self.assertGreater(len(plan["actions"]), 0)
        self.assertIsNone(plan["safety"]["motif_annulation"])


if __name__ == "__main__":
    unittest.main()
