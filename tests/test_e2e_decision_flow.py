# tests/test_e2e_decision_flow.py – V6.0.0
"""Tests d'intégration E2E pour la validation globale du moteur de décision (Étape 2.3)."""

import json
from pathlib import Path
import unittest

from core.dry_run_guard import is_dry_run_enabled, set_dry_run_mode
from core.market_signals_adapter import calculer_contexte_et_policy
from core.rebalancing import generer_plan_reequilibrage_contexte
from core.scoring import PROFILS, charger_ponderations
import journal_daemon_v6_secure


class TestE2EDecisionFlow(unittest.TestCase):
    def setUp(self) -> None:
        set_dry_run_mode(True)
        self.pools_path = Path("test_pools.json")
        self.cfg_path = Path("config/strategy_v6_0.json")
        self.journal_path = Path("data/logs/journal_strategie.jsonl")

    def test_complete_decision_pipeline(self) -> None:
        """Tester l'intégralité du pipeline décisionnel de bout en bout."""
        self.assertTrue(is_dry_run_enabled())

        # 1. Chargement des signaux de marché
        signaux = journal_daemon_v6_secure._charger_signaux_normalises(limit=50)
        self.assertIsInstance(signaux, list)
        self.assertGreater(len(signaux), 0)

        # 2. Lecture de la configuration V6.0
        config = journal_daemon_v6_secure._read_json(self.cfg_path)
        self.assertIsInstance(config, dict)

        # 3. Évaluation du contexte et de la policy
        decision, profil_effectif = calculer_contexte_et_policy(signaux, config)
        self.assertIsNotNone(decision)
        self.assertIsNotNone(profil_effectif)

        # 4. Chargement et scoring multi-facteurs des pools
        pools_data = journal_daemon_v6_secure._read_json(self.pools_path)
        pools_stats = pools_data.get("pools", []) if isinstance(pools_data, dict) else []
        self.assertGreater(len(pools_stats), 0)

        scoring_info = journal_daemon_v6_secure._calculer_scoring_pools(
            pools_stats=pools_stats,
            profil_nom=profil_effectif,
            solde_total_usd=5000.0,
            historique_pools={},
        )
        self.assertIsNotNone(scoring_info)
        self.assertIn("profil", scoring_info)
        self.assertIn("resultats_top3", scoring_info)
        self.assertIn("gain_total_journalier_usd", scoring_info)

        # 5. Génération du plan de rééquilibrage avec arbitrage de rentabilité nette
        allocation_actuelle = {"Prudent": 3500.0, "Modere": 1000.0, "Risque": 500.0}
        params_strategie = dict(config)

        plan = generer_plan_reequilibrage_contexte(
            context=decision.context,
            profil_effectif=profil_effectif,
            allocation_actuelle_usd=allocation_actuelle,
            total_usd=5000.0,
            signaux_normalises=signaux,
            params_strategie=params_strategie,
            run_id="run_e2e_flow_test",
            journal_path=str(self.journal_path),
        )

        self.assertIsInstance(plan, dict)
        self.assertEqual(plan.get("tag"), "[SIMULATION / DRY-RUN]")
        self.assertIn("actions", plan)
        self.assertIn("safety", plan)

        # 6. Vérification du fichier de journalisation
        self.assertTrue(self.journal_path.exists())
        with self.journal_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            self.assertGreater(len(lines), 0)
            derniere_entree = json.loads(lines[-1])
            self.assertIn("tag", derniere_entree)
            self.assertEqual(derniere_entree.get("tag"), "[SIMULATION / DRY-RUN]")


if __name__ == "__main__":
    unittest.main()
