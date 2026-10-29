"""
Tests unitaires pour la factory d'initialisation du DEXRouter (core/dex/factory.py).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from web3 import Web3

import core.dex as dex_pkg
from core.dex import (
    DEXError,
    DEXRouter,
    QuickswapAdapter,
    SushiswapAdapter,
    UniswapV3Adapter,
    UnsupportedChainError,
    create_default_dex_router,
)
from core.dex.quickswap import (
    QUOTER_ADDRESS as QUICKSWAP_QUOTER_ADDRESS,
    SWAP_ROUTER_ADDRESS as QUICKSWAP_ROUTER_ADDRESS,
)
from core.dex.sushiswap import ROUTER_ADDRESS as SUSHISWAP_ROUTER_ADDRESS
from core.dex.uniswap_v3 import (
    QUOTER_V2_ADDRESS as UNISWAP_QUOTER_ADDRESS,
    SWAP_ROUTER_02_ADDRESS as UNISWAP_ROUTER_ADDRESS,
)


def test_package_export_create_default_dex_router() -> None:
    assert dex_pkg.create_default_dex_router is create_default_dex_router
    assert "create_default_dex_router" in dex_pkg.__all__
    assert "UniswapV3Adapter" in dex_pkg.__all__


def test_create_default_dex_router_instantiates_three_polygon_adapters() -> None:
    mock_web3 = MagicMock()

    router = create_default_dex_router(mock_web3)

    assert isinstance(router, DEXRouter)
    assert router.default_timeout == 3.0

    adapters = router.adapters
    assert len(adapters) == 3

    adapter_types = [type(a) for a in adapters]
    assert adapter_types == [UniswapV3Adapter, QuickswapAdapter, SushiswapAdapter]

    adapter_names = [a.name for a in adapters]
    assert adapter_names == ["uniswap_v3", "quickswap", "sushiswap"]

    # Vérifie que les 5 contrats Polygon officiels ont été instanciés via web3.eth.contract
    called_addresses = [
        call.kwargs.get("address")
        for call in mock_web3.eth.contract.call_args_list
    ]
    expected_addresses = [
        Web3.to_checksum_address(UNISWAP_QUOTER_ADDRESS),
        Web3.to_checksum_address(UNISWAP_ROUTER_ADDRESS),
        Web3.to_checksum_address(QUICKSWAP_QUOTER_ADDRESS),
        Web3.to_checksum_address(QUICKSWAP_ROUTER_ADDRESS),
        Web3.to_checksum_address(SUSHISWAP_ROUTER_ADDRESS),
    ]
    assert called_addresses == expected_addresses


def test_create_default_dex_router_custom_timeout() -> None:
    mock_web3 = MagicMock()

    router = create_default_dex_router(mock_web3, chain_id=137, timeout=5.5)

    assert isinstance(router, DEXRouter)
    assert router.default_timeout == 5.5
    assert len(router.adapters) == 3


@pytest.mark.parametrize("unsupported_chain_id", [1, 10, 56, 42161, 80002, 0, -1])
def test_create_default_dex_router_rejects_unsupported_chain_id(
    unsupported_chain_id: int,
) -> None:
    mock_web3 = MagicMock()

    with pytest.raises((ValueError, DEXError, UnsupportedChainError)) as exc_info:
        create_default_dex_router(mock_web3, chain_id=unsupported_chain_id)

    assert str(unsupported_chain_id) in str(exc_info.value)
    assert "137" in str(exc_info.value)


def test_create_default_dex_router_rejects_invalid_inputs() -> None:
    mock_web3 = MagicMock()

    with pytest.raises(ValueError, match="web3_client"):
        create_default_dex_router(None)

    with pytest.raises(ValueError):
        create_default_dex_router(mock_web3, chain_id=True)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        create_default_dex_router(mock_web3, chain_id="137")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        create_default_dex_router(mock_web3, chain_id=137, timeout=0)
