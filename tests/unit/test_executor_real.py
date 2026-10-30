"""
Tests unitaires et d'intégration de l'exécuteur (`core/execution/executor_real.py` / `core/executor_real.py`)
et du pipeline de pré-swap `GasTankManager` (Phase 4 - v6.6.0-dev).

Couvre les 4 scénarios obligatoires :
- Cas 1 : Exécution nominale avec réserve de gas suffisante (swap exécuté).
- Cas 2 : Réserve basse mais WPOL disponible -> `check_and_refuel()` déclenché puis swap exécuté.
- Cas 3 : Réserve critique sans WPOL de secours -> blocage préventif du swap (aucune transaction envoyée).
- Cas 4 : Respect strict du mode `dry_run=True` lors du refuel et du swap.
"""

from __future__ import annotations

import logging
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

from core.dry_run_guard import set_dry_run_mode
from core.execution.executor_real import (
    GasCriticalError,
    GasTankManager,
    RealExecutor,
    executer_action_reelle,
)
from core.swap_reel import effectuer_swap_reel

WALLET_ADDR = "0xe4C8e186697e2FBa2fA43Ec6B020B203bDb87812"
ROUTER_ADDR = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
PRIVATE_KEY_HEX = "0x" + "11" * 32


def _build_pre_swap_web3(
    native_pol_balances: List[float] | float,
    wpol_balance: float = 20.0,
    allowance_wei: int = 10**18,
) -> MagicMock:
    """
    Construit un client Web3 mocké supportant simultanément :
    - `GasTankManager` (solde natif `get_balance` et `WPOL.balanceOf` / `withdraw`)
    - `swap_reel` (allowance ERC-20, frais EIP-1559 `get_block`, signature et envoi).
    """
    w3 = MagicMock()
    w3.eth.chain_id = 137
    w3.eth.gas_price = 30 * 10**9
    w3.eth.get_block.return_value = {"baseFeePerGas": 40 * 10**9}
    w3.eth.max_priority_fee = 30 * 10**9
    w3.eth.get_transaction_count.side_effect = [10, 11, 12, 13]
    w3.eth.estimate_gas.return_value = 120_000

    if isinstance(native_pol_balances, (int, float)):
        w3.eth.get_balance.return_value = int(
            Web3.to_wei(str(native_pol_balances), "ether")
        )
    else:
        w3.eth.get_balance.side_effect = [
            int(Web3.to_wei(str(val), "ether")) for val in native_pol_balances
        ]

    def _contract_factory(address: str, abi: Any) -> MagicMock:
        contract = MagicMock()
        # Contrat WPOL (balanceOf / withdraw / deposit)
        contract.functions.balanceOf.return_value.call.return_value = int(
            Web3.to_wei(str(wpol_balance), "ether")
        )
        contract.functions.withdraw.side_effect = lambda wad: MagicMock(
            build_transaction=MagicMock(
                side_effect=lambda params: {"fn": "withdraw", "wad": wad, **params}
            )
        )
        # Contrat ERC-20 générique pour swap_reel (allowance / approve)
        contract.functions.allowance.return_value.call.return_value = allowance_wei
        contract.functions.approve.return_value.build_transaction.return_value = {
            "to": address,
            "data": "0x095ea7b3",
        }
        return contract

    w3.eth.contract.side_effect = _contract_factory

    signed_tx_1 = MagicMock()
    signed_tx_1.raw_transaction = b"\xaa" * 32
    signed_tx_2 = MagicMock()
    signed_tx_2.raw_transaction = b"\xbb" * 32
    w3.eth.account.sign_transaction.side_effect = [signed_tx_1, signed_tx_2]

    w3.eth.send_raw_transaction.side_effect = [
        bytes.fromhex("aa" * 32),
        bytes.fromhex("bb" * 32),
    ]

    receipt_ok = MagicMock()
    receipt_ok.status = 1
    receipt_ok.blockNumber = 96_500_000
    receipt_ok.gasUsed = 140_000
    w3.eth.wait_for_transaction_receipt.return_value = receipt_ok

    return w3


def _swap_action(dry_run: bool = False) -> dict:
    return {
        "kind": "swap",
        "dry_run": dry_run,
        "params": {
            "tokenA": "USDC",
            "tokenB": "WETH",
            "amountA": 10.0,
            "max_slippage_pct": 0.5,
            "dex": "sushiswap",
            "expected_amount_out": "0.005",
            "min_amount_out": "0.004975",
            "estimated_gas": 150_000,
            "recipient": WALLET_ADDR,
            "tx": {
                "to": ROUTER_ADDR,
                "data": "0x38ed1739abcdef",
                "value": 0,
                "chainId": 137,
                "gas": 150_000,
            },
        },
    }


# ==============================================================================
# Cas 1 : Exécution nominale avec réserve de gas suffisante (swap exécuté)
# ==============================================================================


def test_case_1_nominal_gas_reserve_executes_swap_without_refuel():
    """
    Cas 1 : Lorsque `native_pol >= min_pol_reserve` (ex: 12.0 POL >= 5.0 POL),
    `check_and_refuel()` retourne `NOMINAL`, aucun unwrap n'est envoyé, et le swap réel s'exécute.
    """
    set_dry_run_mode(False)
    try:
        w3 = _build_pre_swap_web3(native_pol_balances=12.0, wpol_balance=20.0)
        executor = RealExecutor(
            web3_client=w3,
            wallet_address=WALLET_ADDR,
            dry_run=False,
            private_key=PRIVATE_KEY_HEX,
        )

        with (
            patch(
                "core.guardrails.verifier_action_reelle",
                return_value={"status": "EXECUTED", "details": {"reason": "ok"}},
            ),
            patch(
                "core.swap_reel.get_wallet_address",
                return_value=WALLET_ADDR,
            ),
            patch(
                "core.swap_reel.get_private_key",
                return_value=PRIVATE_KEY_HEX,
            ),
            patch.object(
                executor.gas_tank, "unwrap", wraps=executor.gas_tank.unwrap
            ) as spy_unwrap,
        ):
            res = executor.execute_action(_swap_action(dry_run=False), run_id="run_case_1")

        assert res["status"] == "EXECUTED"
        assert res["tx_hash"] == "0x" + "aa" * 32
        assert res["details"]["status"] == "confirmed"
        assert res["details"]["gas_tank"]["status"] == "NOMINAL"
        assert res["details"]["gas_tank"]["action"] == "none"

        spy_unwrap.assert_not_called()
        # Une seule transaction envoyée on-chain : le swap lui-même
        assert w3.eth.send_raw_transaction.call_count == 1
    finally:
        set_dry_run_mode(True)


# ==============================================================================
# Cas 2 : Réserve basse mais WPOL disponible -> check_and_refuel() déclenché puis swap exécuté
# ==============================================================================


def test_case_2_low_gas_reserve_triggers_refuel_then_executes_swap(caplog):
    """
    Cas 2 : Lorsque `native_pol < min_pol_reserve` (ex: 2.5 POL < 5.0 POL) mais que le solde
    WPOL est suffisant (20.0 WPOL >= déficit 7.5 POL) :
    1. `check_and_refuel()` déclenche `unwrap(7.5)` (1ère tx on-chain : `0xaa...`).
    2. Le ravitaillement est journalisé.
    3. Le swap est ensuite signé et diffusé (2ème tx on-chain : `0xbb...`).
    """
    set_dry_run_mode(False)
    try:
        # 1er appel get_balance (check_and_refuel) = 2.5 POL ; après refuel = 10.0 POL
        w3 = _build_pre_swap_web3(
            native_pol_balances=[2.5, 10.0],
            wpol_balance=20.0,
        )
        executor = RealExecutor(
            web3_client=w3,
            wallet_address=WALLET_ADDR,
            dry_run=False,
            min_pol_reserve=5.0,
            target_pol_reserve=10.0,
            critical_gas_threshold=1.0,
            private_key=PRIVATE_KEY_HEX,
        )

        with (
            patch(
                "core.guardrails.verifier_action_reelle",
                return_value={"status": "EXECUTED", "details": {"reason": "ok"}},
            ),
            patch(
                "core.swap_reel.get_wallet_address",
                return_value=WALLET_ADDR,
            ),
            patch(
                "core.swap_reel.get_private_key",
                return_value=PRIVATE_KEY_HEX,
            ),
            caplog.at_level(logging.INFO),
        ):
            res = executor.execute_action(_swap_action(dry_run=False), run_id="run_case_2")

        assert res["status"] == "EXECUTED"
        # 1ère tx = unwrap (0xaa...), 2ème tx = swap (0xbb...)
        assert res["tx_hash"] == "0x" + "bb" * 32
        gas_tank_details = res["details"]["gas_tank"]
        assert gas_tank_details["status"] == "REFUELED"
        assert gas_tank_details["action"] == "unwrap"
        assert gas_tank_details["amount_unwrapped"] == pytest.approx(7.5)
        assert gas_tank_details["tx_hash"] == "0x" + "aa" * 32

        assert w3.eth.send_raw_transaction.call_count == 2
        assert any("Ravitaillement pré-swap" in rec.message for rec in caplog.records)
    finally:
        set_dry_run_mode(True)


# ==============================================================================
# Cas 3 : Réserve critique sans WPOL de secours -> blocage préventif du swap
# ==============================================================================


def test_case_3_critical_gas_without_wpol_blocks_swap_with_no_tx():
    """
    Cas 3 : Lorsque `native_pol <= critical_gas_threshold` (ex: 0.4 POL <= 1.0 POL)
    et que le solde WPOL est insuffisant (ex: 1.0 WPOL < déficit 9.6 POL) :
    - `check_and_refuel()` retourne `INSUFFICIENT_WPOL`.
    - `is_gas_critical()` retourne `True`.
    - Le swap est immédiatement bloqué (`status == "BLOCKED"`, `reason == "gas_critical"`).
    - Aucune signature ni transaction on-chain n'est émise.
    """
    set_dry_run_mode(False)
    try:
        w3 = _build_pre_swap_web3(native_pol_balances=0.4, wpol_balance=1.0)
        executor = RealExecutor(
            web3_client=w3,
            wallet_address=WALLET_ADDR,
            dry_run=False,
            min_pol_reserve=5.0,
            target_pol_reserve=10.0,
            critical_gas_threshold=1.0,
            private_key=PRIVATE_KEY_HEX,
        )

        # Vérifie que `pre_swap_gas_check()` lève explicitement `GasCriticalError`
        with pytest.raises(GasCriticalError, match="GAS CRITICAL"):
            executor.pre_swap_gas_check()

        # Et vérifie que `execute_action` / `executer_action_reelle` retourne un blocage sécurisé
        with patch(
            "core.guardrails.verifier_action_reelle",
            return_value={"status": "EXECUTED", "details": {"reason": "ok"}},
        ):
            res = executor.execute_action(_swap_action(dry_run=False), run_id="run_case_3")

        assert res["status"] == "BLOCKED"
        assert res["tx_hash"] is None
        assert res["details"]["reason"] == "gas_critical"
        assert res["details"]["gas_tank"]["status"] == "INSUFFICIENT_WPOL"
        assert res["details"]["gas_tank"]["is_critical"] is True

        # Aucune signature ni envoi de transaction (ni unwrap, ni approve, ni swap)
        w3.eth.account.sign_transaction.assert_not_called()
        w3.eth.send_raw_transaction.assert_not_called()
    finally:
        set_dry_run_mode(True)


def test_case_3_direct_swap_reel_blocked_when_gas_critical():
    """Vérifie également le blocage critique en appel direct à `effectuer_swap_reel`."""
    set_dry_run_mode(False)
    try:
        w3 = _build_pre_swap_web3(native_pol_balances=0.2, wpol_balance=0.0)
        gas_tank = GasTankManager(
            web3_client=w3,
            wallet_address=WALLET_ADDR,
            dry_run=False,
        )

        res = effectuer_swap_reel(
            dex="sushiswap",
            token_in="USDC",
            token_out="WETH",
            amount_in_wei=10_000_000,
            dry_run=False,
            web3_client=w3,
            gas_tank=gas_tank,
        )

        assert res["status"] == "BLOCKED"
        assert res["tx_hash"] is None
        assert res["details"]["reason"] == "gas_critical"
        w3.eth.account.sign_transaction.assert_not_called()
        w3.eth.send_raw_transaction.assert_not_called()
    finally:
        set_dry_run_mode(True)


# ==============================================================================
# Cas 4 : Respect strict du mode dry_run=True lors du refuel et du swap
# ==============================================================================


def test_case_4_strict_dry_run_during_refuel_and_swap(caplog):
    """
    Cas 4 : En mode `dry_run=True` avec une réserve POL basse (2.0 POL < 5.0 POL) et WPOL disponible :
    - `check_and_refuel()` simule l'unwrap de 8.0 WPOL (`SIMULATED_REFUEL`, `tx_hash=None`).
    - Le swap est exécuté en mode simulation (`[SIMULATION / DRY-RUN]`, `tx_hash=None`).
    - Aucune signature (`sign_transaction`) ni transaction (`send_raw_transaction`) n'est générée.
    """
    set_dry_run_mode(True)
    w3 = _build_pre_swap_web3(native_pol_balances=2.0, wpol_balance=25.0)
    executor = RealExecutor(
        web3_client=w3,
        wallet_address=WALLET_ADDR,
        dry_run=True,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        critical_gas_threshold=1.0,
    )

    with (
        patch(
            "core.guardrails.verifier_action_reelle",
            return_value={"status": "EXECUTED", "details": {"reason": "ok"}},
        ),
        caplog.at_level(logging.INFO),
    ):
        res = executor.execute_action(_swap_action(dry_run=True), run_id="run_case_4")

    assert res["status"] == "EXECUTED"
    assert res["tx_hash"] is None
    details = res["details"]
    assert details["mode"] == "[SIMULATION / DRY-RUN]"
    assert details["gas_tank"]["status"] == "SIMULATED_REFUEL"
    assert details["gas_tank"]["action"] == "simulated_unwrap"
    assert details["gas_tank"]["amount_unwrapped"] == pytest.approx(8.0)
    assert details["gas_tank"]["tx_hash"] is None
    assert details["gas_tank"]["dry_run"] is True

    # Zéro signature et zéro transaction envoyée sur le réseau
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()
    assert "[SIMULATION / DRY-RUN]" in caplog.text
