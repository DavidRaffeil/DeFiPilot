"""
Tests unitaires et d'intégration pour la configuration centrale du GasTank (`config.py` / `core/config.py`)
et son branchement dans la boucle décisionnelle de `StrategyEngine` (`core/strategy_engine.py`).
Phase 4 - v6.6.0-dev.
"""

from __future__ import annotations

import importlib
import logging
import os
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

import config as root_config
import core.config as core_config
from core.execution.gas_tank import GasTankManager
from core.strategy_engine import PoolCandidate, StrategyEngine

STRATEGY_CFG_PATH = "config/strategy_v6_0.json"
TEST_WALLET = "0xe4C8e186697e2FBa2fA43Ec6B020B203bDb87812"


def _sample_pools() -> List[PoolCandidate]:
    return [
        PoolCandidate(
            pool_id="USDC-WETH",
            platform="quickswap",
            chain="polygon",
            symbols="USDC-WETH",
            tvl=1_500_000.0,
            apr=22.0,
            score=0.95,
        )
    ]


def _build_mock_web3(native_pol: float = 12.0, wpol: float = 20.0) -> MagicMock:
    w3 = MagicMock()
    w3.eth.chain_id = 137
    w3.eth.gas_price = 30 * 10**9
    w3.eth.get_balance.return_value = int(Web3.to_wei(str(native_pol), "ether"))
    wpol_contract = MagicMock()
    wpol_contract.functions.balanceOf.return_value.call.return_value = int(
        Web3.to_wei(str(wpol), "ether")
    )
    wpol_contract.functions.deposit.return_value.build_transaction.side_effect = (
        lambda params: {"fn": "deposit", **params}
    )
    wpol_contract.functions.withdraw.side_effect = lambda wad: MagicMock(
        build_transaction=MagicMock(
            side_effect=lambda params: {"fn": "withdraw", "wad": wad, **params}
        )
    )
    w3.eth.contract.return_value = wpol_contract
    return w3


# ==============================================================================
# 1. Configuration centrale (config.py / core.config) & variables d'environnement
# ==============================================================================


def test_config_default_gas_tank_constants():
    """Vérifie la présence et les valeurs par défaut des constantes GasTank dans config.py et core.config."""
    for mod in (root_config, core_config):
        assert mod.GAS_MIN_POL_RESERVE == 5.0
        assert mod.GAS_TARGET_POL_RESERVE == 10.0
        assert mod.GAS_CRITICAL_THRESHOLD == 1.0
        assert mod.GAS_MAX_POL_RESERVE == 25.0
        assert mod.GAS_AUTO_WRAP_ENABLED is True


def test_config_reads_gas_variables_from_environment():
    """Valide la lecture dynamique des variables d'environnement GasTank."""
    env_overrides = {
        "GAS_MIN_POL_RESERVE": "6.5",
        "GAS_TARGET_POL_RESERVE": "14.0",
        "GAS_CRITICAL_THRESHOLD": "1.5",
        "GAS_MAX_POL_RESERVE": "35.0",
        "GAS_AUTO_WRAP_ENABLED": "false",
    }
    with patch.dict(os.environ, env_overrides, clear=False):
        importlib.reload(core_config)
        importlib.reload(root_config)

        assert root_config.GAS_MIN_POL_RESERVE == 6.5
        assert root_config.GAS_TARGET_POL_RESERVE == 14.0
        assert root_config.GAS_CRITICAL_THRESHOLD == 1.5
        assert root_config.GAS_MAX_POL_RESERVE == 35.0
        assert root_config.GAS_AUTO_WRAP_ENABLED is False

        w3 = _build_mock_web3()
        tank = GasTankManager(web3_client=w3, wallet_address=TEST_WALLET)
        assert tank.min_pol_reserve == 6.5
        assert tank.target_pol_reserve == 14.0
        assert tank.critical_gas_threshold == 1.5
        assert tank.max_pol_reserve == 35.0
        assert tank.auto_wrap_enabled is False

    # Restauration des valeurs par défaut après le test
    importlib.reload(core_config)
    importlib.reload(root_config)


# ==============================================================================
# 2. Comportement de StrategyEngine face à un gas critique (suspension du cycle)
# ==============================================================================


def test_strategy_engine_suspends_cycle_when_gas_critical(caplog):
    """
    Lorsque `gas_tank.is_gas_critical()` est True (et qu'aucun WPOL ne permet de recharger),
    `StrategyEngine.run()` journalise un avertissement et suspend la génération de nouveaux
    signaux d'action (`actions == []`, `status == "suspended_gas_critical"`).
    """
    # Solde POL critique (0.3 POL <= 1.0 POL) et 0 WPOL en réserve
    w3 = _build_mock_web3(native_pol=0.3, wpol=0.0)
    gas_tank = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        critical_gas_threshold=1.0,
        dry_run=True,
    )

    mock_logger = MagicMock()
    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        logger=mock_logger,
        gas_tank=gas_tank,
        feature_multi_dex=False,
    )

    with caplog.at_level(logging.WARNING, logger="core.strategy_engine"):
        plan = engine.run(pools=_sample_pools())

    assert plan["status"] == "suspended_gas_critical"
    assert plan["reason"] == "gas_critical"
    assert plan["actions"] == []
    assert plan["gas_refuel"]["status"] == "INSUFFICIENT_WPOL"
    assert plan["gas_refuel"]["is_critical"] is True

    mock_logger.warning.assert_called()
    assert any("GAS CRITICAL" in rec.message for rec in caplog.records)


# ==============================================================================
# 3. Fin de cycle StrategyEngine : auto-wrap du surplus de gas (POL -> WPOL)
# ==============================================================================


def test_strategy_engine_sweeps_excess_gas_at_end_of_cycle(caplog):
    """
    En fin de cycle décisionnel `StrategyEngine.run()`, si `native_pol > max_pol_reserve`
    (ex: 30.0 POL > 25.0 POL), `check_and_sweep_excess_gas()` convertit l'excédent
    (30.0 - 10.0 = 20.0 POL) en WPOL et attache le résumé dans `plan["excess_gas_sweep"]`.
    """
    w3 = _build_mock_web3(native_pol=30.0, wpol=5.0)
    gas_tank = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        max_pol_reserve=25.0,
        auto_wrap_enabled=True,
        dry_run=True,
    )

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        gas_tank=gas_tank,
        feature_multi_dex=False,
    )

    with (
        patch(
            "core.strategy_engine.lire_soldes_depuis_env",
            return_value={"USDC": 100.0, "native": 30.0},
        ),
        caplog.at_level(logging.INFO, logger="core.strategy_engine"),
    ):
        plan = engine.run(pools=_sample_pools())

    assert len(plan["actions"]) == 3
    assert "excess_gas_sweep" in plan
    sweep = plan["excess_gas_sweep"]
    assert sweep["action"] == "WRAPPED_EXCESS"
    assert sweep["status"] == "SIMULATED_WRAP"
    assert sweep["amount"] == pytest.approx(20.0)
    assert sweep["tx_hash"] is None
    assert any("Excédent de POL converti en WPOL" in rec.message for rec in caplog.records)
