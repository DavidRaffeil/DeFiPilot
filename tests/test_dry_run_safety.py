# tests/test_dry_run_safety.py – V6.0.0
"""Tests unitaires de validation et hardening du mode Simulation / Dry-Run (Étape 1.1)."""

import os
import unittest
from unittest.mock import patch

from core.dry_run_guard import (
    DryRunSafetyViolation,
    assert_dry_run_safe,
    is_dry_run_enabled,
    set_dry_run_mode,
)
from core.execution.liquidity_real_tx import ajouter_liquidite_reelle
from core.executor_real import executer_action_reelle
from core.simulateur_wallet import appliquer_ordre_simule, charger_solde, mettre_a_jour_solde
from core.swap_reel import effectuer_swap_reel, executer_swap_reel


class TestDryRunSafety(unittest.TestCase):
    def setUp(self) -> None:
        # Activer le mode Dry-Run par défaut avant chaque test
        set_dry_run_mode(True)
        # Réinitialiser un solde virtuel connu pour les tests
        mettre_a_jour_solde(1000.0)

    def test_dry_run_safety_lock_blocks_signing_and_sending(self) -> None:
        """Vérifier que assert_dry_run_safe lève DryRunSafetyViolation en mode Dry-Run."""
        set_dry_run_mode(True)
        self.assertTrue(is_dry_run_enabled())

        with self.assertRaises(DryRunSafetyViolation) as ctx:
            assert_dry_run_safe("transaction_test")

        self.assertIn("SAFETY LOCK BLOCKED", str(ctx.exception))
        self.assertIn("[SIMULATION / DRY-RUN]", str(ctx.exception))

    def test_no_private_key_solicited_in_dry_run(self) -> None:
        """Vérifier qu'aucune clé privée n'est sollicitée ni requise en mode Dry-Run."""
        set_dry_run_mode(True)

        pool = {
            "platform": "sushiswap",
            "chain": "polygon",
            "router_address": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
            "tokenA_symbol": "USDC",
            "tokenB_symbol": "WETH",
            "tokenA_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "tokenB_address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        }

        # Avec une clé privée absente, l'exécution en dry_run=True doit réussir la simulation sans erreur de clé
        with patch.dict(os.environ, {}, clear=True):
            res_swap = effectuer_swap_reel(
                dex="sushiswap",
                token_in="USDC",
                token_out="WETH",
                amount_in_wei=5000000,
                dry_run=True,
            )
            self.assertEqual(res_swap.get("status"), "SUCCESS")
            self.assertIn("[SIMULATION / DRY-RUN]", res_swap.get("msg", ""))

            res_liq = ajouter_liquidite_reelle(
                pool=pool,
                amountA=10.0,
                amountB=0.005,
                dry_run=True,
            )
            self.assertFalse(res_liq.get("success"))  # arrêt propre car RPC non connecté
            self.assertNotEqual(res_liq.get("error"), "private key introuvable")

    def test_realistic_simulation_gas_and_slippage(self) -> None:
        """Vérifier l'estimation dynamique du Gas et l'application du slippage."""
        res = effectuer_swap_reel(
            dex="sushiswap",
            token_in="USDC",
            token_out="WETH",
            amount_in_wei=100_000_000,  # 100 USDC
            slippage_pct=0.5,
            dry_run=True,
        )

        self.assertEqual(res.get("status"), "SUCCESS")
        details = res.get("details", {})
        self.assertEqual(details.get("slippage_pct"), 0.5)
        self.assertGreater(details.get("gas_cost_usd", 0.0), 0.0)
        self.assertEqual(details.get("amount_in_units"), 100.0)
        self.assertEqual(details.get("amount_out_simulated"), 99.5)  # 100 * (1 - 0.005)

    def test_virtual_balance_updates(self) -> None:
        """Vérifier la mise à jour cohérente des soldes virtuels après déduction gas + slippage."""
        solde_initial = charger_solde()
        res_update = appliquer_ordre_simule(
            montant_usd=100.0,
            gas_usd=0.05,
            slippage_pct=0.5,
        )

        solde_final = charger_solde()
        perte_attendue = 0.05 + (100.0 * 0.005)  # 0.05 + 0.5 = 0.55 USD
        self.assertAlmostEqual(solde_final, solde_initial - perte_attendue, places=2)
        self.assertEqual(res_update.get("tag"), "[SIMULATION / DRY-RUN]")

    def test_executor_real_safety_and_tagging(self) -> None:
        """Vérifier le comportement de executor_real avec le flag dry_run."""
        action = {
            "kind": "swap",
            "dry_run": True,
            "params": {"tokenA": "USDC", "tokenB": "ETH", "amountA": 10.0},
        }
        res = executer_action_reelle(action, run_id="test_run_123")
        self.assertEqual(res.get("status"), "EXECUTED")
        self.assertIn("[SIMULATION / DRY-RUN]", res.get("details", {}).get("mode", ""))


if __name__ == "__main__":
    unittest.main()
