"""
Tests unitaires pour l'adaptateur QuickSwap V3 (core/dex/quickswap.py).
Contrats Web3 entièrement mockés (aucun accès réseau).
"""

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError

import core.dex as dex_pkg
from core.dex import DEXQuoteError
from core.dex.base import BaseDEXAdapter, DEXQuote
from core.dex.exceptions import DEXTransactionError
from core.dex.quickswap import (
    DEFAULT_SWAP_GAS,
    QUOTER_ADDRESS,
    SWAP_ROUTER_ABI,
    SWAP_ROUTER_ADDRESS,
    QuickswapAdapter,
)

USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
RECIPIENT = "0x000000000000000000000000000000000000dEaD"
DECIMALS = {USDC: 6, WETH: 18}
NOW = 1_700_000_000


def _make_quoter(handler):
    """handler(tokenIn, tokenOut, amountIn, limit) -> (amountOut, fee) ou lève."""
    quoter = MagicMock()

    def _fn(*args):
        call = MagicMock()
        call.call.side_effect = lambda: handler(*args)
        return call

    quoter.functions.quoteExactInputSingle.side_effect = _fn
    return quoter


def _constant_price(t_in, t_out, amount_in, limit):
    # 100 USDC (1e8) -> 0.05 WETH (5e16) ; prix constant
    return (amount_in * 5 * 10**8, 100)


def _adapter(handler=_constant_price, router=None):
    return QuickswapAdapter(
        web3=MagicMock(),
        quoter_contract=_make_quoter(handler),
        router_contract=router or MagicMock(),
        token_decimals=DECIMALS,
        deadline_seconds=1200,
        clock=lambda: NOW,
    )


def _get_quote(adapter, amount="100", slippage="0.005"):
    return asyncio.run(
        adapter.get_quote(USDC, WETH, Decimal(amount), Decimal(slippage))
    )


def test_constants_name_and_export():
    assert QUOTER_ADDRESS == "0xa15F52d4393694b4d17275d3c015bcf026f63a47"
    assert SWAP_ROUTER_ADDRESS == "0xf5b509bB0909a69B1c207E495f687a596C168E12"
    adapter = _adapter()
    assert adapter.name == "quickswap"
    assert isinstance(adapter, BaseDEXAdapter)
    assert dex_pkg.QuickswapAdapter is QuickswapAdapter
    assert "QuickswapAdapter" in dex_pkg.__all__


def test_quote_nominal_and_slippage():
    quote = _get_quote(_adapter(), "100", "0.005")

    assert isinstance(quote, DEXQuote)
    assert quote.dex_name == "quickswap"
    assert quote.amount_in == Decimal("100")
    assert quote.expected_amount_out == Decimal("0.05")
    assert quote.min_amount_out == Decimal("0.04975")  # 0.05 * (1 - 0.005)
    assert quote.estimated_gas == DEFAULT_SWAP_GAS
    raw = quote.raw_quote_data
    assert raw["amount_in_raw"] == 100 * 10**6
    assert raw["expected_amount_out_raw"] == 5 * 10**16
    assert raw["min_amount_out_raw"] == 4975 * 10**13
    assert raw["fee"] == 100
    assert raw["price_impact_estimated"] is True
    assert quote.price_impact_pct == Decimal("0")
    for value in (quote.expected_amount_out, quote.min_amount_out, quote.price_impact_pct):
        assert isinstance(value, Decimal)


def test_quote_zero_slippage():
    quote = _get_quote(_adapter(), "10", "0")
    assert quote.min_amount_out == quote.expected_amount_out


def test_quote_price_impact_positive():
    def handler(t_in, t_out, amount_in, limit):
        rate = 100 if amount_in <= 100 * 10**6 // 1000 else 98  # -2 % sur le gros montant
        return (amount_in * rate * 10**6, 100)

    quote = _get_quote(_adapter(handler), "100")
    assert quote.price_impact_pct == Decimal("2")


def test_quote_impact_fallback_when_reference_fails():
    def handler(t_in, t_out, amount_in, limit):
        if amount_in < 100 * 10**6:
            raise ContractLogicError("reverted")
        return (amount_in * 5 * 10**8, 100)

    quote = _get_quote(_adapter(handler), "100")
    assert quote.price_impact_pct == Decimal("0")
    assert quote.raw_quote_data["price_impact_estimated"] is False


def test_quote_quoter_called_with_algebra_signature():
    adapter = _adapter()
    _get_quote(adapter, "100")
    first_call = adapter._quoter.functions.quoteExactInputSingle.call_args_list[0]
    assert first_call.args == (USDC, WETH, 100 * 10**6, 0)


def test_quote_failure_revert():
    def handler(*args):
        raise ContractLogicError("execution reverted")

    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(handler))


def test_quote_failure_zero_output():
    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(lambda *a: (0, 100)))


def test_quote_failure_rpc_error():
    def handler(*args):
        raise ConnectionError("rpc down")

    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(handler))


def test_quote_input_validation():
    adapter = _adapter()
    with pytest.raises(DEXQuoteError):
        asyncio.run(adapter.get_quote(USDC, WETH, 1.5, Decimal("0.01")))
    with pytest.raises(DEXQuoteError):
        asyncio.run(adapter.get_quote(USDC, WETH, Decimal("0"), Decimal("0.01")))
    with pytest.raises(DEXQuoteError):
        asyncio.run(adapter.get_quote(USDC, WETH, Decimal("1"), Decimal("1")))
    with pytest.raises(DEXQuoteError):
        asyncio.run(adapter.get_quote("nope", WETH, Decimal("1"), Decimal("0.01")))
    with pytest.raises(DEXQuoteError):
        asyncio.run(adapter.get_quote(USDC, USDC, Decimal("1"), Decimal("0.01")))


def test_decimals_resolved_via_erc20_when_not_cached():
    web3 = MagicMock()
    erc20 = MagicMock()
    erc20.functions.decimals.return_value.call.side_effect = [6, 18]
    web3.eth.contract.return_value = erc20
    adapter = QuickswapAdapter(
        web3=web3,
        quoter_contract=_make_quoter(_constant_price),
        router_contract=MagicMock(),
    )
    quote = _get_quote(adapter, "1")
    assert quote.expected_amount_out > 0
    assert erc20.functions.decimals.return_value.call.call_count == 2


def test_build_swap_transaction_with_mocked_router():
    router = MagicMock()
    router.encode_abi.return_value = "0xdeadbeef"
    adapter = _adapter(router=router)
    quote = _get_quote(adapter, "100", "0.005")

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    assert tx == {
        "to": SWAP_ROUTER_ADDRESS,
        "data": "0xdeadbeef",
        "value": 0,
        "chainId": 137,
        "gas": DEFAULT_SWAP_GAS,
    }
    assert router.encode_abi.call_args.args == ("exactInputSingle",)
    params = router.encode_abi.call_args.kwargs["args"][0]
    assert params == (
        USDC,
        WETH,
        RECIPIENT,
        NOW + 1200,
        100 * 10**6,
        4975 * 10**13,
        0,
    )


def test_build_swap_transaction_real_abi_encoding():
    """Encodage ABI réel (offline) : sélecteur Algebra exactInputSingle."""
    router = Web3().eth.contract(
        address=Web3.to_checksum_address(SWAP_ROUTER_ADDRESS), abi=SWAP_ROUTER_ABI
    )
    adapter = _adapter(router=router)
    quote = _get_quote(adapter)

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    selector = Web3.keccak(
        text="exactInputSingle((address,address,address,uint256,uint256,uint256,uint160))"
    )[:4].hex()
    assert tx["data"].lower().removeprefix("0x").startswith(selector.removeprefix("0x"))


def test_build_swap_transaction_rejects_bad_input():
    adapter = _adapter()
    quote = _get_quote(adapter)
    with pytest.raises(DEXTransactionError):
        asyncio.run(adapter.build_swap_transaction(quote, "not-an-address"))

    foreign = DEXQuote(
        dex_name="other",
        token_in=USDC,
        token_out=WETH,
        amount_in=Decimal("1"),
        expected_amount_out=Decimal("1"),
        min_amount_out=Decimal("1"),
        price_impact_pct=Decimal("0"),
        estimated_gas=1,
    )
    with pytest.raises(DEXTransactionError):
        asyncio.run(adapter.build_swap_transaction(foreign, RECIPIENT))


def test_invalid_deadline_rejected():
    with pytest.raises(ValueError):
        QuickswapAdapter(
            web3=MagicMock(),
            quoter_contract=MagicMock(),
            router_contract=MagicMock(),
            deadline_seconds=0,
        )
