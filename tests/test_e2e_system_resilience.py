# tests/test_e2e_system_resilience.py – V6.0.0
"""Tests d'intégration E2E pour la validation globale de la stabilité et résilience système (Étape 3.3)."""

import json
import os
from pathlib import Path
import unittest

from core.dry_run_guard import is_dry_run_enabled, set_dry_run_mode
from core.state_manager import load_state, save_state
from core.system_health import verifier_sante_daemon
import journal_daemon_v6_secure


class TestE2ESystemResilience(unittest.TestCase):
    def setUp(self) -> None:
        set_dry_run_mode(True)
        self.pools_path = "test_pools.json"
        self.cfg_path = "config/strategy_v6_0.json"
        self.state_path = Path("data/state.json")
        self.bak_path = Path("data/state.json.bak")
        self.health_path = Path("data/health.json")
        self.strategy_log_path = Path("data/logs/journal_strategie.jsonl")

    def test_daemon_crash_recovery_and_resilience_flow(self) -> None:
        """Simuler un cycle complet d'exécution, crash/corruption d'état, et redémarrage résilient."""
        self.assertTrue(is_dry_run_enabled())

        # 1. Premier cycle d'exécution (3 itérations)
        argv_run1 = [
            "--pools", self.pools_path,
            "--cfg", self.cfg_path,
            "--interval", "1",
            "--max-loops", "3",
        ]
        exit_code1 = journal_daemon_v6_secure.main(argv_run1)
        self.assertEqual(exit_code1, 0)

        # Vérification des artéfacts de l'exécution 1
        self.assertTrue(self.state_path.exists())
        self.assertTrue(self.health_path.exists())

        # Sauvegarde d'un état sain personnalisé pour tester la résilience au crash
        etat_initial = load_state(path=self.state_path)
        etat_initial["test_resilience_id"] = "resilience_valid_123"
        save_state(state=etat_initial, path=self.state_path)
        save_state(state=etat_initial, path=self.state_path)
        self.assertTrue(self.bak_path.exists())

        # 2. Simulation d'un crash intempestif avec corruption du fichier principal state.json
        with open(self.state_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID_JSON_DATA_CORRUPTED_ON_CRASH ")

        # 3. Deuxième cycle d'exécution (3 itérations) : redémarrage après crash
        argv_run2 = [
            "--pools", self.pools_path,
            "--cfg", self.cfg_path,
            "--interval", "1",
            "--max-loops", "3",
        ]
        exit_code2 = journal_daemon_v6_secure.main(argv_run2)
        self.assertEqual(exit_code2, 0)

        # 4. Vérification de la restauration transparente depuis state.json.bak
        etat_apres_restart = load_state(path=self.state_path)
        self.assertIsNotNone(etat_apres_restart)
        self.assertEqual(etat_apres_restart.get("test_resilience_id"), "resilience_valid_123")

        # 5. Vérification du bilan de santé (Heartbeat)
        res_sante = verifier_sante_daemon(health_path=self.health_path, max_lag_seconds=30.0)
        self.assertTrue(res_sante["healthy"])
        self.assertEqual(res_sante["status"], "HEALTHY")

        # 6. Vérification de la journalisation avec tag [SIMULATION / DRY-RUN]
        self.assertTrue(self.strategy_log_path.exists())
        with self.strategy_log_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            self.assertGreaterEqual(len(lines), 6)
            derniere = json.loads(lines[-1])
            self.assertEqual(derniere.get("tag"), "[SIMULATION / DRY-RUN]")


if __name__ == "__main__":
    unittest.main()
