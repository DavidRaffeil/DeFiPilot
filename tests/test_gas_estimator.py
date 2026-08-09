"""
Tests unitaires pour le module GasEstimator (core/execution/gas_estimator.py).
"""

from unittest.mock import MagicMock
import pytest
from web3 import Web3

from core.execution.gas_estimator import GasEstimator, GasPriceTooHighError
from core.execution.rpc_manager import RPCManager


def test_unit_conversions():
    """Teste les méthodes utilitaires de conversion Gwei <-> Wei."""
    gwei_val = 50.0
    wei_val = GasEstimator.gwei_to_wei(gwei_val)
    assert wei_val == 50_000_000_000
    assert GasEstimator.wei_to_gwei(wei_val) == 50.0


def test_estimate_eip1559_fees_success():
    """Teste le calcul EIP-1559 standard avec des valeurs mockées."""
    mock_w3 = MagicMock()
    # baseFeePerGas = 50 Gwei
    base_fee_wei = Web3.to_wei(50, "gwei")
    mock_w3.eth.get_block.return_value = {"baseFeePerGas": base_fee_wei}
    # max_priority_fee = 35 Gwei (supérieur au minimum de 30 Gwei)
    mock_w3.eth.max_priority_fee = Web3.to_wei(35, "gwei")

    estimator = GasEstimator(mock_w3, min_priority_fee_gwei=30.0, max_gas_price_gwei=300.0)
    fees = estimator.estimate_eip1559_fees()

    # maxPriorityFee = 35 Gwei
    assert fees["maxPriorityFeePerGas_gwei"] == 35.0
    # baseFee = 50 Gwei
    assert fees["baseFeePerGas_gwei"] == 50.0
    # maxFeePerGas = (2 * 50) + 35 = 135 Gwei
    assert fees["maxFeePerGas_gwei"] == 135.0
    assert fees["maxFeePerGas"] == Web3.to_wei(135, "gwei")


def test_min_priority_fee_enforcement():
    """Teste que le pourboire minimal (ex: 30 Gwei) est appliqué si le réseau suggère moins."""
    mock_w3 = MagicMock()
    base_fee_wei = Web3.to_wei(40, "gwei")
    mock_w3.eth.get_block.return_value = {"baseFeePerGas": base_fee_wei}
    # Le réseau suggère 10 Gwei (< 30 Gwei min)
    mock_w3.eth.max_priority_fee = Web3.to_wei(10, "gwei")

    estimator = GasEstimator(mock_w3, min_priority_fee_gwei=30.0, max_gas_price_gwei=300.0)
    fees = estimator.estimate_eip1559_fees()

    # Priority fee doit être relevé au plancher de 30 Gwei
    assert fees["maxPriorityFeePerGas_gwei"] == 30.0
    # maxFee = (2 * 40) + 30 = 110 Gwei
    assert fees["maxFeePerGas_gwei"] == 110.0


def test_gas_price_too_high_guardrail():
    """Teste le déclenchement de l'exception de sécurité GasPriceTooHighError."""
    mock_w3 = MagicMock()
    # baseFee = 150 Gwei -> maxFee = (2 * 150) + 40 = 340 Gwei (> 300 Gwei limit)
    base_fee_wei = Web3.to_wei(150, "gwei")
    mock_w3.eth.get_block.return_value = {"baseFeePerGas": base_fee_wei}
    mock_w3.eth.max_priority_fee = Web3.to_wei(40, "gwei")

    estimator = GasEstimator(mock_w3, min_priority_fee_gwei=30.0, max_gas_price_gwei=300.0)

    with pytest.raises(GasPriceTooHighError, match="Garde-fou activé"):
        estimator.estimate_eip1559_fees()


def test_integration_with_rpc_manager():
    """Teste l'intégration entre GasEstimator et RPCManager."""
    mock_rpc_manager = MagicMock(spec=RPCManager)
    base_fee_wei = Web3.to_wei(20, "gwei")
    mock_rpc_manager.execute_call.side_effect = lambda method, *args, **kwargs: (
        {"baseFeePerGas": base_fee_wei} if method == "eth.get_block" else Web3.to_wei(30, "gwei")
    )

    estimator = GasEstimator(mock_rpc_manager, min_priority_fee_gwei=30.0, max_gas_price_gwei=300.0)
    fees = estimator.estimate_eip1559_fees()

    # maxFee = (2 * 20) + 30 = 70 Gwei
    assert fees["maxFeePerGas_gwei"] == 70.0
    assert fees["baseFeePerGas_gwei"] == 20.0
    assert fees["maxPriorityFeePerGas_gwei"] == 30.0
