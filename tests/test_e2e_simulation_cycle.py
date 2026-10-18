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


class TestCapitalCycleCompounding(unittest.TestCase):
    DAY = 86400
    T0 = 1_700_000_000

    def _manager(self, cfg=None):
        import main_v6_core
        self.reinvested, self.secured = [], []
        return main_v6_core.CapitalCycleManager(
            main_v6_core.load_strategy_config() if cfg is None else cfg,
            reinvest_action=lambda amt, pool: self.reinvested.append((amt, pool)),
            secure_action=lambda amt: self.secured.append(amt),
        )

    def test_cycle_routes_allocation_and_logs(self) -> None:
        from decimal import Decimal

        mgr = self._manager()
        self.assertTrue(mgr.compounder.enabled)
        with self.assertLogs("DeFiPilot.V6Core", level="INFO") as cap:
            r0 = mgr.process_profit("100", self.T0, "poolA")
            r5 = mgr.process_profit(Decimal("100"), self.T0 + 5 * self.DAY, "poolA")
        self.assertEqual(r0["reinvest_amount"], Decimal("100.000000"))
        self.assertEqual(r5["rate"], Decimal("0.75"))
        self.assertEqual(r5["reinvest_amount"], Decimal("75.000000"))
        self.assertEqual(r5["secured_amount"], Decimal("25.000000"))
        for v in r5.values():
            self.assertIsInstance(v, Decimal)
        self.assertEqual(self.reinvested[-1], (Decimal("75.000000"), "poolA"))
        self.assertEqual(self.secured, [Decimal("25.000000")])
        self.assertEqual(mgr.secured_reserve, Decimal("25.000000"))
        self.assertTrue(any("pool=poolA jours=5 taux=0.75" in m for m in cap.output))

    def test_pool_change_resets(self) -> None:
        from decimal import Decimal

        mgr = self._manager()
        mgr.process_profit("10", self.T0, "poolA")
        r = mgr.process_profit("10", self.T0 + 9 * self.DAY, "poolB")
        self.assertEqual(r["rate"], Decimal("1.0"))
        self.assertEqual(r["secured_amount"], Decimal("0"))

    def test_disabled_or_missing_config_is_classic(self) -> None:
        from decimal import Decimal

        for cfg in ({}, {"compounding": {"enabled": False}}):
            mgr = self._manager(cfg)
            r = mgr.process_profit("100", self.T0 + 30 * self.DAY, "poolA")
            self.assertEqual(r["reinvest_amount"], Decimal("100.000000"))
            self.assertEqual(r["secured_amount"], Decimal("0"))
            self.assertEqual(self.secured, [])


if __name__ == "__main__":
    unittest.main()
