"""
Test d'intégration de bout en bout (E2E) du cycle de vie complet du GasTankManager
(`tests/e2e/test_e2e_gas_tank_lifecycle.py` - Phase 4 / v6.6.0-dev).

Simule deux cycles consécutifs de `StrategyEngine.run()` en mode `dry_run=True` :
- Cycle 1 : Solde initial bas (2.5 POL < min 5.0 POL) -> déclenchement automatique
  du refuel (unwrap simulé de 7.5 WPOL vers POL) -> exécution nominale de la stratégie.
- Cycle 2 : Solde après swap supérieur au plafond max (32.0 POL > max 25.0 POL) ->
  exécution nominale puis sweep de l'excédent (wrap simulé de 22.0 POL vers WPOL) en fin de cycle.
"""

from __future__ import annotations

import logging
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

from core.dry_run_guard import set_dry_run_mode
from core.execution.gas_tank import GasTankManager
from core.strategy_context import StrategyContext
from core.strategy_engine import PoolCandidate, StrategyEngine

STRATEGY_CFG_PATH = "config/strategy_v6_0.json"
WALLET_ADDRESS = "0xe4C8e186697e2FBa2fA43Ec6B020B203bDb87812"


def _candidate_pools() -> List[PoolCandidate]:
    return [
        PoolCandidate(
            pool_id="USDC-WETH",
            platform="quickswap",
            chain="polygon",
            symbols="USDC-WETH",
            tvl=1_450_000.0,
            apr=19.8,
            score=0.93,
        ),
        PoolCandidate(
            pool_id="USDC-USDT",
            platform="uniswap_v3",
            chain="polygon",
            symbols="USDC-USDT",
            tvl=920_000.0,
            apr=7.5,
            score=0.68,
        ),
    ]


def _build_stateful_mock_web3(state: Dict[str, float]) -> MagicMock:
    """
    Construit un client Web3 mocké lisant dynamiquement `state["native_pol"]` et `state["wpol"]`
    sans émettre aucune transaction réseau.
    """
    w3 = MagicMock()
    w3.eth.chain_id = 137
    w3.eth.gas_price = 30 * 10**9

    w3.eth.get_balance.side_effect = lambda _addr: int(
        Web3.to_wei(str(state["native_pol"]), "ether")
    )

    wpol_contract = MagicMock()
    wpol_contract.functions.balanceOf.return_value.call.side_effect = lambda: int(
        Web3.to_wei(str(state["wpol"]), "ether")
    )
    w3.eth.contract.return_value = wpol_contract

    return w3


def test_e2e_gas_tank_full_lifecycle_refuel_then_sweep_excess(caplog):
    """
    Scénario E2E complet en deux cycles :
    - Cycle 1 : `native_pol = 2.5 POL` (< `min_pol_reserve = 5.0 POL`), `wpol = 20.0 WPOL`
      -> `check_and_refuel()` déclenche un unwrap simulé de `7.5 WPOL` (`SIMULATED_REFUEL`),
      puis le cycle de stratégie s'exécute nominalement (swap + add_liquidity + stake) sans sweep final.
    - Cycle 2 : `native_pol = 32.0 POL` (> `max_pol_reserve = 25.0 POL`), `wpol = 12.5 WPOL`
      -> `check_and_refuel()` est nominal (`NOMINAL`), le cycle de stratégie s'exécute, puis
      `check_and_sweep_excess_gas()` convertit l'excédent de `22.0 POL` (`32.0 - 10.0`) en WPOL
      (`WRAPPED_EXCESS` / `SIMULATED_WRAP`).
    """
    set_dry_run_mode(True)

    # État initial pour le Cycle 1 : solde natif bas (2.5 POL), réserve WPOL suffisante (20.0 WPOL)
    wallet_state: Dict[str, float] = {"native_pol": 2.5, "wpol": 20.0}
    w3 = _build_stateful_mock_web3(wallet_state)

    gas_tank = GasTankManager(
        web3_client=w3,
        wallet_address=WALLET_ADDRESS,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        critical_gas_threshold=1.0,
        max_pol_reserve=25.0,
        auto_wrap_enabled=True,
        dry_run=True,
    )

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        web3_client=w3,
        gas_tank=gas_tank,
        wallet_address=WALLET_ADDRESS,
        feature_multi_dex=False,
    )

    context = StrategyContext(
        timestamp="2026-10-30T19:30:00Z",
        label="favorable",
        ai_score=0.88,
        confiance=0.92,
        resume="Conditions de marché favorables",
        metrics={"volatility": 0.10},
        nb_signaux=8,
    )

    # =========================================================================
    # CYCLE 1 : Solde initial bas (2.5 POL) -> Refuel automatique -> Exécution
    # =========================================================================
    with (
        patch(
            "core.strategy_engine.lire_soldes_depuis_env",
            return_value={"USDC": 100.0, "native": 2.5},
        ),
        caplog.at_level(logging.INFO),
    ):
        plan_cycle_1 = engine.run(pools=_candidate_pools(), context=context)

    # 1. Vérification du refuel pré-cycle au Cycle 1
    assert "gas_refuel" in plan_cycle_1
    refuel_c1 = plan_cycle_1["gas_refuel"]
    assert refuel_c1["status"] == "SIMULATED_REFUEL"
    assert refuel_c1["action"] == "simulated_unwrap"
    assert refuel_c1["native_pol"] == pytest.approx(2.5)
    assert refuel_c1["deficit"] == pytest.approx(7.5)
    assert refuel_c1["amount_unwrapped"] == pytest.approx(7.5)
    assert refuel_c1["tx_hash"] is None
    assert refuel_c1["dry_run"] is True

    # 2. Vérification de l'exécution nominale de la stratégie au Cycle 1
    assert len(plan_cycle_1["actions"]) == 3
    assert [a["kind"] for a in plan_cycle_1["actions"]] == [
        "swap",
        "add_liquidity",
        "stake",
    ]
    assert plan_cycle_1["execution_output"]["status"] == "executed"
    assert plan_cycle_1["execution_output"]["results"][0]["status"] == "EXECUTED"

    # 3. En fin de Cycle 1, le solde (2.5 POL simulé) n'excède pas max_pol_reserve (25.0 POL)
    sweep_c1 = plan_cycle_1["excess_gas_sweep"]
    assert sweep_c1["action"] == "NONE"
    assert sweep_c1["amount"] == 0.0

    # =========================================================================
    # CYCLE 2 : Solde après swap supérieur au plafond (32.0 POL > 25.0 POL) -> Sweep
    # =========================================================================
    wallet_state["native_pol"] = 32.0
    wallet_state["wpol"] = 12.5

    with (
        patch(
            "core.strategy_engine.lire_soldes_depuis_env",
            return_value={"USDC": 100.0, "native": 32.0},
        ),
        caplog.at_level(logging.INFO),
    ):
        plan_cycle_2 = engine.run(pools=_candidate_pools(), context=context)

    # 1. En début de Cycle 2, le solde POL est nominal (32.0 >= 5.0) : aucun refuel requis
    refuel_c2 = plan_cycle_2["gas_refuel"]
    assert refuel_c2["status"] == "NOMINAL"
    assert refuel_c2["action"] == "none"
    assert refuel_c2["deficit"] == 0.0
    assert refuel_c2["amount_unwrapped"] == 0.0

    # 2. Exécution nominale de la stratégie au Cycle 2
    assert len(plan_cycle_2["actions"]) == 3
    assert plan_cycle_2["execution_output"]["status"] == "executed"

    # 3. En fin de Cycle 2, l'excédent (32.0 - 10.0 = 22.0 POL) est converti en WPOL (wrap simulé)
    sweep_c2 = plan_cycle_2["excess_gas_sweep"]
    assert sweep_c2["action"] == "WRAPPED_EXCESS"
    assert sweep_c2["status"] == "SIMULATED_WRAP"
    assert sweep_c2["native_pol"] == pytest.approx(32.0)
    assert sweep_c2["amount"] == pytest.approx(22.0)
    assert sweep_c2["excess"] == pytest.approx(22.0)
    assert sweep_c2["tx_hash"] is None
    assert sweep_c2["dry_run"] is True

    # 4. Garantie stricte Dry-Run sur l'ensemble des 2 cycles : zéro signature ni transaction réseau
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()
