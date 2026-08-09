# tests/test_e2e_simulation_cycle.py – V6.0.0
"""Tests d'intégration E2E pour la validation de la simulation complète (Étape 1.3)."""

import json
import os
from pathlib import Path
import unittest

from core.dry_run_guard import is_dry_run_enabled, set_dry_run_mode
from core.simulateur_wallet import charger_solde, mettre_a_jour_solde
from core.state_manager import get_state
import journal_daemon_v6_secure


class TestE2ESimulationCycle(unittest.TestCase):
    def setUp(self) -> None:
        set_dry_run_mode(True)
        mettre_a_jour_solde(5000.0)
        self.pools_path = "test_pools.json"
        self.cfg_path = "config/strategy_v6_0.json"
        self.strategy_log_path = Path("data/logs/journal_strategie.jsonl")

    def test_e2e_multi_loop_simulation(self) -> None:
        """Exécuter un cycle complet de simulation sur 5 itérations et valider les artéfacts."""
        self.assertTrue(is_dry_run_enabled())
        solde_initial = charger_solde()
        self.assertGreater(solde_initial, 0.0)

        # Lancement de 5 itérations du journaliseur continu en mode simulation
        argv = [
            "--pools", self.pools_path,
            "--cfg", self.cfg_path,
            "--interval", "1",
            "--max-loops", "5",
        ]

        exit_code = journal_daemon_v6_secure.main(argv)
        self.assertEqual(exit_code, 0)

        # 1. Vérification de l'existence du journal de stratégie
        self.assertTrue(self.strategy_log_path.exists())

        # 2. Vérification que chaque entrée journalisée contient la mention [SIMULATION / DRY-RUN]
        with self.strategy_log_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            self.assertGreaterEqual(len(lines), 5)
            for line in lines[-5:]:
                entry = json.loads(line)
                self.assertEqual(entry.get("tag"), "[SIMULATION / DRY-RUN]")
                self.assertIn("run_id", entry)
                self.assertIn("profil", entry)

        # 3. Vérification de l'état du solde virtuel et de sa persistance
        solde_final = charger_solde()
        self.assertGreater(solde_final, 0.0)
        self.assertTrue(os.path.exists("data/wallet_simule.json"))

        # 4. Vérification de la persistance de l'état via state_manager
        etat = get_state()
        self.assertIsNotNone(etat)
        self.assertIn("dernier_scoring_pools", etat)
        self.assertIn("allocation_simulee_apres_reequilibrage", etat)


if __name__ == "__main__":
    unittest.main()
