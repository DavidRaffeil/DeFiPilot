"""
Tests unitaires dédiés pour le module GasTankManager (`core/execution/gas_tank.py`).
Phase 4 : Gestion Automatisée du Carburant et Wrapping Natif (WPOL ⇄ POL) sur Polygon Mainnet.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3

from core.dry_run_guard import set_dry_run_mode
from core.execution.gas_tank import (
    DEFAULT_WPOL_ADDRESS,
    WPOL_MINIMAL_ABI,
    GasTankManager,
)
from core.execution.rpc_manager import RPCManager

TEST_WALLET = "0x1111111111111111111111111111111111111111"
TEST_PK = "0x" + "a" * 64
EXPECTED_TX_HASH = "0x" + "b" * 64


def _build_mock_web3(native_pol: float = 12.0, wpol: float = 25.0) -> MagicMock:
    """Construit un client Web3 entièrement mocké avec soldes POL et WPOL configurables."""
    w3 = MagicMock()
    w3.eth.chain_id = 137
    w3.eth.gas_price = 35_000_000_000
    w3.eth.get_transaction_count.return_value = 7
    w3.eth.estimate_gas.return_value = 45_000
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

    signed_mock = MagicMock()
    signed_mock.raw_transaction = b"\xde\xad\xbe\xef"
    w3.eth.account.sign_transaction.return_value = signed_mock
    w3.eth.send_raw_transaction.return_value = bytes.fromhex("b" * 64)

    return w3


# ==============================================================================
# 1. Initialisation et lecture des soldes mockés
# ==============================================================================


def test_initialization_defaults_and_wpol_abi():
    """Vérifie l'initialisation par défaut et la présence de l'ABI minimale WPOL."""
    w3 = _build_mock_web3()
    manager = GasTankManager(web3_client=w3, wallet_address=TEST_WALLET.lower())

    assert manager.wallet_address == Web3.to_checksum_address(TEST_WALLET)
    assert manager.wpol_address == DEFAULT_WPOL_ADDRESS
    assert manager.min_pol_reserve == 5.0
    assert manager.target_pol_reserve == 10.0
    assert manager.critical_gas_threshold == 1.0
    assert manager.max_pol_reserve == 25.0
    assert manager.auto_wrap_enabled is True
    assert manager.dry_run is True

    abi_fn_names = {entry["name"] for entry in WPOL_MINIMAL_ABI}
    assert {"deposit", "withdraw", "balanceOf"}.issubset(abi_fn_names)


def test_get_balances_conversion_18_decimals():
    """Teste la lecture des soldes mockés et la conversion exacte depuis 18 décimales (Wei)."""
    w3 = _build_mock_web3(native_pol=7.5, wpol=42.125)
    manager = GasTankManager(web3_client=w3, wallet_address=TEST_WALLET)

    balances = manager.get_balances()

    assert balances == {"native_pol": 7.5, "wpol": 42.125}
    w3.eth.get_balance.assert_called_once_with(Web3.to_checksum_address(TEST_WALLET))
    w3.eth.contract.assert_called_once_with(
        address=DEFAULT_WPOL_ADDRESS, abi=WPOL_MINIMAL_ABI
    )


def test_get_balances_with_rpc_manager_wrapper():
    """Vérifie que `get_balances()` fonctionne également avec un wrapper `RPCManager`."""
    mock_rpc = MagicMock(spec=RPCManager)
    w3 = _build_mock_web3(native_pol=6.25, wpol=15.75)

    def _side_effect(method_or_fn, *args, **kwargs):
        if method_or_fn == "eth.get_balance":
            return w3.eth.get_balance(*args, **kwargs)
        if callable(method_or_fn):
            return method_or_fn(w3)
        raise AssertionError(f"Appel inattendu: {method_or_fn}")

    mock_rpc.execute_call.side_effect = _side_effect
    manager = GasTankManager(web3_client=mock_rpc, wallet_address=TEST_WALLET)

    assert manager.get_balances() == {"native_pol": 6.25, "wpol": 15.75}


# ==============================================================================
# 2. Comportement quand le solde est nominal (aucune action requise)
# ==============================================================================


def test_check_and_refuel_nominal_balance():
    """Vérifie qu'aucun unwrap n'est déclenché lorsque `native_pol >= min_pol_reserve`."""
    w3 = _build_mock_web3(native_pol=8.0, wpol=20.0)
    manager = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        dry_run=False,
    )

    with patch.object(manager, "unwrap") as mock_unwrap:
        result = manager.check_and_refuel()
        mock_unwrap.assert_not_called()

    assert result["status"] == "NOMINAL"
    assert result["action"] == "none"
    assert result["native_pol"] == 8.0
    assert result["wpol"] == 20.0
    assert result["deficit"] == 0.0
    assert result["amount_unwrapped"] == 0.0
    assert result["tx_hash"] is None
    assert result["is_critical"] is False


def test_check_and_refuel_exact_boundary_min_reserve():
    """Lorsque `native_pol == min_pol_reserve` (5.0 POL), le solde est considéré nominal."""
    w3 = _build_mock_web3(native_pol=5.0, wpol=20.0)
    manager = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        dry_run=False,
    )

    result = manager.check_and_refuel()
    assert result["status"] == "NOMINAL"
    assert result["action"] == "none"
    assert result["deficit"] == 0.0


# ==============================================================================
# 3. Unwrap automatique quand native_pol < min_pol_reserve
# ==============================================================================


def test_auto_unwrap_when_native_pol_below_min_reserve():
    """
    Teste le déclenchement de l'unwrap automatique et le calcul exact du déficit
    (`deficit = target_pol_reserve - native_pol`) en mode réel (`dry_run=False`).
    """
    set_dry_run_mode(False)
    try:
        # native_pol = 3.2 POL < 5.0 POL -> deficit = 10.0 - 3.2 = 6.8 POL
        w3 = _build_mock_web3(native_pol=3.2, wpol=15.0)
        manager = GasTankManager(
            web3_client=w3,
            wallet_address=TEST_WALLET,
            min_pol_reserve=5.0,
            target_pol_reserve=10.0,
            dry_run=False,
            private_key=TEST_PK,
        )

        result = manager.check_and_refuel()

        assert result["status"] == "REFUELED"
        assert result["action"] == "unwrap"
        assert result["deficit"] == pytest.approx(6.8)
        assert result["amount_unwrapped"] == pytest.approx(6.8)
        assert result["tx_hash"] == EXPECTED_TX_HASH

        expected_wei = Web3.to_wei("6.8", "ether")
        wpol_contract = w3.eth.contract.return_value
        wpol_contract.functions.withdraw.assert_called_once_with(expected_wei)
        w3.eth.account.sign_transaction.assert_called_once()
        w3.eth.send_raw_transaction.assert_called_once()
    finally:
        set_dry_run_mode(True)


def test_wrap_real_mode_calls_deposit_with_value_wei():
    """Teste l'appel direct à `wrap(amount)` qui invoque `deposit()` avec `value = amount_wei`."""
    set_dry_run_mode(False)
    try:
        w3 = _build_mock_web3(native_pol=25.0, wpol=5.0)
        manager = GasTankManager(
            web3_client=w3,
            wallet_address=TEST_WALLET,
            dry_run=False,
            private_key=TEST_PK,
        )

        tx_hash = manager.wrap(4.5)

        assert tx_hash == EXPECTED_TX_HASH
        wpol_contract = w3.eth.contract.return_value
        wpol_contract.functions.deposit.assert_called_once_with()
        build_tx_call = (
            wpol_contract.functions.deposit.return_value.build_transaction.call_args
        )
        tx_params = build_tx_call.args[0]
        assert tx_params["value"] == Web3.to_wei("4.5", "ether")
        assert tx_params["from"] == Web3.to_checksum_address(TEST_WALLET)
    finally:
        set_dry_run_mode(True)


# ==============================================================================
# 4. Comportement quand le solde WPOL est insuffisant pour combler le déficit
# ==============================================================================


def test_insufficient_wpol_balance_prevents_unwrap():
    """Vérifie que l'unwrap n'est pas appelé si le solde WPOL est inférieur au déficit requis."""
    # native_pol = 2.5 (< 5.0) -> deficit = 7.5 POL, mais wpol = 4.0 (< 7.5)
    w3 = _build_mock_web3(native_pol=2.5, wpol=4.0)
    manager = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        critical_gas_threshold=1.0,
        dry_run=False,
        private_key=TEST_PK,
    )

    with patch.object(manager, "unwrap") as mock_unwrap:
        result = manager.check_and_refuel()
        mock_unwrap.assert_not_called()

    assert result["status"] == "INSUFFICIENT_WPOL"
    assert result["action"] == "none"
    assert result["deficit"] == pytest.approx(7.5)
    assert result["amount_unwrapped"] == 0.0
    assert result["tx_hash"] is None
    assert result["is_critical"] is False
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()


# ==============================================================================
# 5. Verrouillage critique (is_gas_critical == True)
# ==============================================================================


def test_is_gas_critical_threshold_detection():
    """Teste `is_gas_critical()` sous le seuil critique, sur la frontière exacte, et au-dessus."""
    # Sous le seuil critique (0.4 POL <= 1.0 POL)
    w3_low = _build_mock_web3(native_pol=0.4, wpol=0.0)
    manager_low = GasTankManager(
        web3_client=w3_low,
        wallet_address=TEST_WALLET,
        critical_gas_threshold=1.0,
    )
    assert manager_low.is_gas_critical() is True

    # Exactement égal au seuil critique (1.0 POL <= 1.0 POL)
    w3_boundary = _build_mock_web3(native_pol=1.0, wpol=0.0)
    manager_boundary = GasTankManager(
        web3_client=w3_boundary,
        wallet_address=TEST_WALLET,
        critical_gas_threshold=1.0,
    )
    assert manager_boundary.is_gas_critical() is True

    # Au-dessus du seuil critique (1.01 POL > 1.0 POL)
    w3_safe = _build_mock_web3(native_pol=1.01, wpol=0.0)
    manager_safe = GasTankManager(
        web3_client=w3_safe,
        wallet_address=TEST_WALLET,
        critical_gas_threshold=1.0,
    )
    assert manager_safe.is_gas_critical() is False


# ==============================================================================
# 6. Respect strict du mode dry_run=True (aucune signature ni transaction générée)
# ==============================================================================


def test_dry_run_strict_no_signature_or_transaction(caplog):
    """
    Vérifie qu'en mode `dry_run=True`, `check_and_refuel()`, `wrap()` et `unwrap()`
    journalisent l'action simulée mais ne construisent, ne signent et n'envoient aucune transaction.
    """
    w3 = _build_mock_web3(native_pol=2.0, wpol=20.0)
    manager = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        min_pol_reserve=5.0,
        target_pol_reserve=10.0,
        dry_run=True,
    )

    with caplog.at_level(logging.INFO, logger="DeFiPilot.GasTankManager"):
        refuel_res = manager.check_and_refuel()
        wrap_res = manager.wrap(3.0)
        unwrap_res = manager.unwrap(2.0)

    assert refuel_res["status"] == "SIMULATED_REFUEL"
    assert refuel_res["action"] == "simulated_unwrap"
    assert refuel_res["deficit"] == pytest.approx(8.0)
    assert refuel_res["amount_unwrapped"] == pytest.approx(8.0)
    assert refuel_res["tx_hash"] is None
    assert refuel_res["dry_run"] is True

    assert wrap_res is None
    assert unwrap_res is None

    # Aucune opération de construction, signature ou diffusion on-chain ne doit avoir lieu
    wpol_contract = w3.eth.contract.return_value
    wpol_contract.functions.deposit.assert_not_called()
    wpol_contract.functions.withdraw.assert_not_called()
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()

    assert "[SIMULATION / DRY-RUN]" in caplog.text


# ==============================================================================
# 7. Cas limites (montants négatifs, zéro, conversion en Wei / 18 décimales)
# ==============================================================================


def test_edge_cases_negative_and_zero_amounts():
    """Teste les cas limites : montants négatifs, montants nuls, conversions 18 décimales et paramètres invalides."""
    w3 = _build_mock_web3(native_pol=10.0, wpol=10.0)
    manager = GasTankManager(web3_client=w3, wallet_address=TEST_WALLET, dry_run=False)

    # Montants négatifs -> ValueError
    with pytest.raises(ValueError, match="négatif"):
        manager.wrap(-1.0)
    with pytest.raises(ValueError, match="négatif"):
        manager.unwrap(-0.0001)
    with pytest.raises(ValueError, match="négatif"):
        GasTankManager.to_wei(-5)
    with pytest.raises(ValueError, match="négatif"):
        GasTankManager.from_wei(-100)

    # Montant zéro -> retourne None sans appeler le contrat ni signer
    assert manager.wrap(0) is None
    assert manager.wrap(0.0) is None
    assert manager.unwrap(0) is None
    assert manager.unwrap(0.0) is None
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()

    # Précision de conversion 18 décimales (1 wei et valeurs fractionnaires)
    assert GasTankManager.to_wei(0) == 0
    assert GasTankManager.from_wei(0) == 0.0
    assert GasTankManager.to_wei(1.5) == 1_500_000_000_000_000_000
    assert GasTankManager.from_wei(1_500_000_000_000_000_000) == 1.5
    assert GasTankManager.to_wei("0.000000000000000001") == 1

    # Validation des paramètres du constructeur
    with pytest.raises(ValueError, match="web3_client"):
        GasTankManager(web3_client=None, wallet_address=TEST_WALLET)
    with pytest.raises(ValueError, match="wallet_address"):
        GasTankManager(web3_client=w3, wallet_address="")
    with pytest.raises(ValueError, match="négatifs"):
        GasTankManager(web3_client=w3, wallet_address=TEST_WALLET, min_pol_reserve=-1.0)
    with pytest.raises(ValueError, match="target_pol_reserve"):
        GasTankManager(
            web3_client=w3,
            wallet_address=TEST_WALLET,
            min_pol_reserve=10.0,
            target_pol_reserve=5.0,
        )
    with pytest.raises(ValueError, match="max_pol_reserve"):
        GasTankManager(
            web3_client=w3,
            wallet_address=TEST_WALLET,
            min_pol_reserve=5.0,
            target_pol_reserve=10.0,
            max_pol_reserve=8.0,
        )


# ==============================================================================
# 8. Auto-wrap du surplus de gas (check_and_sweep_excess_gas)
# ==============================================================================


def test_check_and_sweep_excess_gas_nominal_no_action():
    """Lorsque `native_pol <= max_pol_reserve` (ex: 18.0 <= 25.0), aucun wrap n'est déclenché."""
    w3 = _build_mock_web3(native_pol=18.0, wpol=10.0)
    manager = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        target_pol_reserve=10.0,
        max_pol_reserve=25.0,
        auto_wrap_enabled=True,
        dry_run=False,
    )

    with patch.object(manager, "wrap") as mock_wrap:
        res = manager.check_and_sweep_excess_gas()
        mock_wrap.assert_not_called()

    assert res["action"] == "NONE"
    assert res["amount"] == 0.0
    assert res["tx_hash"] is None


def test_check_and_sweep_excess_gas_real_wrap_triggered():
    """
    Lorsque `auto_wrap_enabled=True` et `native_pol > max_pol_reserve` (ex: 32.5 > 25.0),
    calcule `excess = 32.5 - 10.0 = 22.5 POL` et déclenche `wrap(22.5)`.
    """
    set_dry_run_mode(False)
    try:
        w3 = _build_mock_web3(native_pol=32.5, wpol=5.0)
        manager = GasTankManager(
            web3_client=w3,
            wallet_address=TEST_WALLET,
            target_pol_reserve=10.0,
            max_pol_reserve=25.0,
            auto_wrap_enabled=True,
            dry_run=False,
            private_key=TEST_PK,
        )

        res = manager.check_and_sweep_excess_gas()

        assert res["action"] == "WRAPPED_EXCESS"
        assert res["status"] == "WRAPPED"
        assert res["amount"] == pytest.approx(22.5)
        assert res["tx_hash"] == EXPECTED_TX_HASH

        wpol_contract = w3.eth.contract.return_value
        wpol_contract.functions.deposit.assert_called_once_with()
        tx_params = (
            wpol_contract.functions.deposit.return_value.build_transaction.call_args.args[0]
        )
        assert tx_params["value"] == Web3.to_wei("22.5", "ether")
        w3.eth.account.sign_transaction.assert_called_once()
        w3.eth.send_raw_transaction.assert_called_once()
    finally:
        set_dry_run_mode(True)


def test_check_and_sweep_excess_gas_dry_run_and_disabled():
    """Teste `check_and_sweep_excess_gas()` en mode `dry_run=True` et lorsque `auto_wrap_enabled=False`."""
    w3 = _build_mock_web3(native_pol=40.0, wpol=5.0)

    # 1. Mode dry_run=True : action WRAPPED_EXCESS simulée, zéro signature/tx
    manager_dry = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        target_pol_reserve=10.0,
        max_pol_reserve=25.0,
        auto_wrap_enabled=True,
        dry_run=True,
    )
    res_dry = manager_dry.check_and_sweep_excess_gas()
    assert res_dry["action"] == "WRAPPED_EXCESS"
    assert res_dry["status"] == "SIMULATED_WRAP"
    assert res_dry["amount"] == pytest.approx(30.0)
    assert res_dry["tx_hash"] is None
    w3.eth.account.sign_transaction.assert_not_called()
    w3.eth.send_raw_transaction.assert_not_called()

    # 2. Mode auto_wrap_enabled=False : action NONE même si native_pol > max_pol_reserve
    manager_disabled = GasTankManager(
        web3_client=w3,
        wallet_address=TEST_WALLET,
        target_pol_reserve=10.0,
        max_pol_reserve=25.0,
        auto_wrap_enabled=False,
        dry_run=False,
    )
    res_disabled = manager_disabled.check_and_sweep_excess_gas()
    assert res_disabled["action"] == "NONE"
    assert res_disabled["status"] == "DISABLED"
    assert res_disabled["amount"] == 0.0

