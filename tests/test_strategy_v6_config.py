# tests/test_strategy_v6_config.py – V6.0.0
"""Tests unitaires pour l'Optimisation des Stratégies et Paramétrage Avancé (Étape 1.2)."""

import json
import os
import tempfile
import unittest

from core.rebalancing import generer_plan_reequilibrage_contexte
from core.strategy_config import load_strategy_config, validate_strategy_config
from core.strategy_engine import PoolCandidate, StrategyEngine


class TestStrategyV6Config(unittest.TestCase):
    def setUp(self) -> None:
        self.config_v6_path = "config/strategy_v6_0.json"

    def test_strategy_v6_config_loading_and_validation(self) -> None:
        """Vérifier que strategy_v6_0.json se charge et se valide correctement."""
        cfg = load_strategy_config(self.config_v6_path)
        self.assertEqual(str(cfg.get("version")), "6.0")
        self.assertTrue(cfg.get("dry_run"))
        self.assertIn("trading_pairs", cfg)
        self.assertIn("rebalance", cfg)
        self.assertIn("risk_management", cfg)
        validate_strategy_config(cfg)

    def test_trading_pairs_whitelist_filtering(self) -> None:
        """Vérifier que StrategyEngine filtre les candidates selon la liste blanche trading_pairs."""
        engine = StrategyEngine(config_path=self.config_v6_path, dry_run=True)

        candidate_ok = PoolCandidate(
            pool_id="USDC-WETH-01",
            platform="sushiswap",
            chain="polygon",
            symbols="USDC-WETH",
            tvl=500_000.0,
            apr=12.5,
        )
        candidate_forbidden = PoolCandidate(
            pool_id="MEME-SHIB-99",
            platform="sushiswap",
            chain="polygon",
            symbols="MEME-SHIB",
            tvl=500_000.0,
            apr=99.0,
        )

        candidates = [candidate_ok, candidate_forbidden]
        selected = engine.select_candidates(candidates)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].symbols, "USDC-WETH")

    def test_rebalancing_threshold_enforcement(self) -> None:
        """Vérifier le respect des seuils de rééquilibrage configurés dans la stratégie."""
        params_strategie = {
            "mode_execution": "simulation",
            "rebalance": {
                "enabled": True,
                "threshold_pct": 0.50,  # Seuil très élevé à 50%
            },
        }

        # Allocation proche de l'équilibre
        allocation_actuelle = {"Prudent": 60.0, "Modere": 30.0, "Risque": 10.0}

        plan = generer_plan_reequilibrage_contexte(
            context="neutre",
            profil_effectif="prudent",
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=100.0,
            signaux_normalises=[],
            params_strategie=params_strategie,
            run_id="test_rebalance_1",
            journal_path="data/logs/test_journal_strategy.jsonl",
        )

        safety = plan.get("safety", {})
        self.assertIsNotNone(safety.get("motif_annulation"))
        self.assertIn("inférieurs au seuil", safety.get("motif_annulation", ""))

    def test_hot_reload_dynamic_config(self) -> None:
        """Vérifier le rechargement dynamique à chaud d'une configuration sans crash."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Écriture d'une première config temporaire validée V6
            cfg_initial = load_strategy_config(self.config_v6_path)
            cfg_initial["profile_default"] = "modere"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cfg_initial, f)

            engine = StrategyEngine(config_path=tmp_path, dry_run=True)
            self.assertEqual(engine.profile, "modere")

            # Modification dynamique à chaud de la configuration
            cfg_initial["profile_default"] = "agressif"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cfg_initial, f)

            # Execution d'un cycle run() qui doit recharger la config à chaud
            result = engine.run(pools=[])
            self.assertEqual(result.get("profile"), "agressif")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
