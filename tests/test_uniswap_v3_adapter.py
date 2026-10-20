"""
Tests unitaires pour l'adaptateur Uniswap V3 (core/dex/uniswap_v3.py).
Contrats Web3 entièrement mockés (aucun accès réseau).
"""

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError

from core.dex import DEXQuoteError
from core.dex.base import BaseDEXAdapter, DEXQuote
from core.dex.exceptions import DEXTransactionError
from core.dex.uniswap_v3 import (
    QUOTER_V2_ADDRESS,
    ROUTER_GAS_OVERHEAD,
    SUPPORTED_FEE_TIERS,
    SWAP_ROUTER_02_ABI,
    SWAP_ROUTER_02_ADDRESS,
    UniswapV3Adapter,
)

USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
RECIPIENT = "0x000000000000000000000000000000000000dEaD"
DECIMALS = {USDC: 6, WETH: 18}


def _make_quoter(handler):
    """handler(params_tuple) -> (out, sqrtAfter, ticks, gas) ou lève une exception."""
    quoter = MagicMock()

    def _fn(params):
        call = MagicMock()
        call.call.side_effect = lambda: handler(params)
        return call

    quoter.functions.quoteExactInputSingle.side_effect = _fn
    return quoter


def _only_fee_500(params):
    if params[3] == 500:
        return (params[2] * 5 * 10**8, 0, 1, 100_000)
    raise ContractLogicError("execution reverted")


def _adapter(handler, router=None):
    return UniswapV3Adapter(
        web3=MagicMock(),
        quoter_contract=_make_quoter(handler),
        router_contract=router or MagicMock(),
        token_decimals=DECIMALS,
    )


def _get_quote(adapter, amount="100", slippage="0.005"):
    return asyncio.run(
        adapter.get_quote(USDC, WETH, Decimal(amount), Decimal(slippage))
    )


def test_constants_and_name():
    assert QUOTER_V2_ADDRESS == "0x61fFE014bA17989E743c5F6cB21bF9697547B21e"
    assert SWAP_ROUTER_02_ADDRESS == "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
    assert SUPPORTED_FEE_TIERS == (100, 500, 3000, 10000)
    adapter = _adapter(lambda p: (1, 0, 0, 0))
    assert adapter.name == "uniswap_v3"
    assert isinstance(adapter, BaseDEXAdapter)


def test_quote_slippage_and_scaling():
    # 100 USDC -> 0.05 WETH sur le palier 500 uniquement
    def handler(params):
        if params[3] == 500:
            amount_in = params[2]
            # prix constant : 100 USDC (1e8) -> 0.05 WETH (5e16)
            return (amount_in * 5 * 10**8, 0, 1, 100_000)
        raise ContractLogicError("execution reverted")

    quote = _get_quote(_adapter(handler), "100", "0.005")

    assert isinstance(quote, DEXQuote)
    assert quote.dex_name == "uniswap_v3"
    assert quote.amount_in == Decimal("100")
    assert quote.expected_amount_out == Decimal("0.05")
    # 0.05 * (1 - 0.005) = 0.04975
    assert quote.min_amount_out == Decimal("0.04975")
    assert quote.estimated_gas == 100_000 + ROUTER_GAS_OVERHEAD
    assert quote.raw_quote_data["fee"] == 500
    assert quote.raw_quote_data["amount_in_raw"] == 100 * 10**6
    assert quote.raw_quote_data["expected_amount_out_raw"] == 5 * 10**16
    assert quote.raw_quote_data["min_amount_out_raw"] == 4975 * 10**13
    # prix constant -> impact nul, mais estimé
    assert quote.price_impact_pct == Decimal("0")
    assert quote.raw_quote_data["price_impact_estimated"] is True
    for value in (quote.expected_amount_out, quote.min_amount_out, quote.price_impact_pct):
        assert isinstance(value, Decimal)


def test_quote_zero_slippage_min_equals_expected():
    quote = _get_quote(_adapter(lambda p: (p[2] * 10**9, 0, 1, 1)), "10", "0")
    assert quote.min_amount_out == quote.expected_amount_out


def test_quote_selects_best_fee_tier():
    outs = {100: 10, 500: 30, 3000: 20, 10000: 5}

    def handler(params):
        return (params[2] * outs[params[3]] * 10**3, 0, 1, 1)

    quote = _get_quote(_adapter(handler))
    assert quote.raw_quote_data["fee"] == 500


def test_quote_price_impact_positive_when_price_degrades():
    def handler(params):
        amount_in = params[2]
        # impact : le gros montant obtient un prix 2 % pire que le petit
        rate = 100 if amount_in <= 100 * 10**6 // 1000 else 98
        return (amount_in * rate * 10**6, 0, 1, 1)

    quote = _get_quote(_adapter(handler), "100")
    assert quote.price_impact_pct == Decimal("2")


def test_quote_failure_all_pools_revert():
    def handler(params):
        raise ContractLogicError("execution reverted")

    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(handler))


def test_quote_failure_zero_liquidity_output():
    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(lambda p: (0, 0, 0, 0)))


def test_quote_failure_rpc_error_wrapped():
    def handler(params):
        raise ConnectionError("rpc down")

    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(handler))


def test_quote_input_validation():
    adapter = _adapter(lambda p: (1, 0, 0, 0))
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
    adapter = UniswapV3Adapter(
        web3=web3,
        quoter_contract=_make_quoter(lambda p: (p[2] * 10**9, 0, 1, 1)),
        router_contract=MagicMock(),
    )
    quote = _get_quote(adapter, "1")
    assert quote.expected_amount_out > 0
    assert erc20.functions.decimals.return_value.call.call_count == 2


def test_build_swap_transaction_with_mocked_router():
    router = MagicMock()
    router.encode_abi.return_value = "0xdeadbeef"
    adapter = _adapter(_only_fee_500, router=router)
    quote = _get_quote(adapter, "100", "0.005")

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    assert tx["to"] == SWAP_ROUTER_02_ADDRESS
    assert tx["data"] == "0xdeadbeef"
    assert tx["value"] == 0
    assert tx["chainId"] == 137
    assert tx["gas"] == quote.estimated_gas
    (fn_name,), kwargs = router.encode_abi.call_args.args, router.encode_abi.call_args.kwargs
    assert fn_name == "exactInputSingle"
    params = kwargs["args"][0]
    assert params == (
        USDC,
        WETH,
        500,
        RECIPIENT,
        100 * 10**6,
        4975 * 10**13,
        0,
    )


def test_build_swap_transaction_real_abi_encoding():
    """Encodage ABI réel (offline) pour garantir le sélecteur exactInputSingle."""
    router = Web3().eth.contract(
        address=Web3.to_checksum_address(SWAP_ROUTER_02_ADDRESS),
        abi=SWAP_ROUTER_02_ABI,
    )
    adapter = _adapter(lambda p: (p[2] * 5 * 10**8, 0, 1, 100_000), router=router)
    quote = _get_quote(adapter, "100", "0.005")

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    selector = Web3.keccak(
        text="exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))"
    )[:4].hex()
    assert tx["data"].lower().removeprefix("0x").startswith(selector.removeprefix("0x"))


def test_build_swap_transaction_rejects_bad_input():
    adapter = _adapter(lambda p: (p[2] * 5 * 10**8, 0, 1, 1))
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
