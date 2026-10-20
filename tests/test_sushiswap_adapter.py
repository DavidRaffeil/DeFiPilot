"""
Tests unitaires pour l'adaptateur SushiSwap V2 (core/dex/sushiswap.py) et
pour les helpers partagés (core/dex/utils.py). Router Web3 entièrement mocké.
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
from core.dex.sushiswap import (
    DEFAULT_SWAP_GAS,
    ROUTER_ABI,
    ROUTER_ADDRESS,
    SushiswapAdapter,
)
from core.dex.utils import (
    apply_slippage_raw,
    compute_price_impact_pct,
    from_raw_units,
    to_raw_units,
)

USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
RECIPIENT = "0x000000000000000000000000000000000000dEaD"
DECIMALS = {USDC: 6, WETH: 18}
NOW = 1_700_000_000


def _make_router(handler):
    """handler(amountIn, path) -> [in, out] ou lève une exception."""
    router = MagicMock()

    def _fn(amount_in, path):
        call = MagicMock()
        call.call.side_effect = lambda: handler(amount_in, path)
        return call

    router.functions.getAmountsOut.side_effect = _fn
    return router


def _constant_price(amount_in, path):
    # 100 USDC (1e8) -> 0.05 WETH (5e16) ; prix constant
    return [amount_in, amount_in * 5 * 10**8]


def _adapter(handler=_constant_price, router=None):
    return SushiswapAdapter(
        web3=MagicMock(),
        router_contract=router or _make_router(handler),
        token_decimals=DECIMALS,
        deadline_seconds=1200,
        clock=lambda: NOW,
    )


def _get_quote(adapter, amount="100", slippage="0.005"):
    return asyncio.run(
        adapter.get_quote(USDC, WETH, Decimal(amount), Decimal(slippage))
    )


# ------------------------------------------------------------------- utils
def test_utils_conversions():
    assert to_raw_units(Decimal("1.5"), 6) == 1_500_000
    assert to_raw_units(Decimal("0.0000019"), 6) == 1  # arrondi vers le bas
    assert from_raw_units(1_500_000, 6) == Decimal("1.5")
    assert from_raw_units(5 * 10**16, 18) == Decimal("0.05")
    big = 2**255
    assert to_raw_units(from_raw_units(big, 18), 18) == big  # aucune perte


def test_utils_slippage_and_impact():
    assert apply_slippage_raw(1000, Decimal("0.005")) == 995
    assert apply_slippage_raw(1000, Decimal("0")) == 1000
    assert apply_slippage_raw(999, Decimal("0.005")) == 994  # arrondi bas
    assert compute_price_impact_pct(1000, 980, 1, 1) == Decimal("2")
    assert compute_price_impact_pct(1000, 1000, 1, 1) == Decimal("0")
    assert compute_price_impact_pct(1000, 1100, 1, 1) == Decimal("0")  # jamais < 0
    with pytest.raises(ValueError):
        compute_price_impact_pct(1000, 1000, 0, 1)


def test_no_cross_private_imports():
    import core.dex.quickswap as q
    import core.dex.uniswap_v3 as u

    for module in (q, u):
        assert not hasattr(module, "_to_raw")
        assert not hasattr(module, "_from_raw")


# ----------------------------------------------------------------- adapter
def test_constants_name_and_export():
    assert ROUTER_ADDRESS == "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
    adapter = _adapter()
    assert adapter.name == "sushiswap"
    assert isinstance(adapter, BaseDEXAdapter)
    assert dex_pkg.SushiswapAdapter is SushiswapAdapter
    assert "SushiswapAdapter" in dex_pkg.__all__


def test_quote_nominal_and_slippage():
    quote = _get_quote(_adapter(), "100", "0.005")

    assert isinstance(quote, DEXQuote)
    assert quote.dex_name == "sushiswap"
    assert quote.amount_in == Decimal("100")
    assert quote.expected_amount_out == Decimal("0.05")
    assert quote.min_amount_out == Decimal("0.04975")
    assert quote.estimated_gas == DEFAULT_SWAP_GAS == 150_000
    raw = quote.raw_quote_data
    assert raw["path"] == (USDC, WETH)
    assert raw["amount_in_raw"] == 100 * 10**6
    assert raw["expected_amount_out_raw"] == 5 * 10**16
    assert raw["min_amount_out_raw"] == 4975 * 10**13
    assert raw["price_impact_estimated"] is True
    assert quote.price_impact_pct == Decimal("0")
    for value in (quote.expected_amount_out, quote.min_amount_out, quote.price_impact_pct):
        assert isinstance(value, Decimal)


def test_quote_uses_direct_path():
    adapter = _adapter()
    _get_quote(adapter)
    first = adapter._router.functions.getAmountsOut.call_args_list[0]
    assert first.args == (100 * 10**6, [USDC, WETH])


def test_quote_price_impact_positive():
    def handler(amount_in, path):
        rate = 100 if amount_in <= 100 * 10**6 // 1000 else 98
        return [amount_in, amount_in * rate * 10**6]

    quote = _get_quote(_adapter(handler), "100")
    assert quote.price_impact_pct == Decimal("2")


def test_quote_impact_fallback_when_reference_fails():
    def handler(amount_in, path):
        if amount_in < 100 * 10**6:
            raise ContractLogicError("reverted")
        return [amount_in, amount_in * 5 * 10**8]

    quote = _get_quote(_adapter(handler), "100")
    assert quote.price_impact_pct == Decimal("0")
    assert quote.raw_quote_data["price_impact_estimated"] is False


def test_quote_failure_pool_does_not_exist():
    def handler(amount_in, path):
        raise ContractLogicError("execution reverted")

    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(handler))


def test_quote_failure_insufficient_reserves_zero_output():
    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(lambda a, p: [a, 0]))


def test_quote_failure_malformed_response():
    with pytest.raises(DEXQuoteError):
        _get_quote(_adapter(lambda a, p: [a]))


def test_quote_failure_rpc_error():
    def handler(amount_in, path):
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


def test_build_swap_transaction_with_mocked_router():
    router = _make_router(_constant_price)
    router.encode_abi.return_value = "0xdeadbeef"
    adapter = _adapter(router=router)
    quote = _get_quote(adapter, "100", "0.005")

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    assert tx == {
        "to": ROUTER_ADDRESS,
        "data": "0xdeadbeef",
        "value": 0,
        "chainId": 137,
        "gas": 150_000,
    }
    assert router.encode_abi.call_args.args == ("swapExactTokensForTokens",)
    assert router.encode_abi.call_args.kwargs["args"] == [
        100 * 10**6,
        4975 * 10**13,
        [USDC, WETH],
        RECIPIENT,
        NOW + 1200,
    ]


def test_build_swap_transaction_real_abi_encoding_and_custom_deadline():
    router = Web3().eth.contract(
        address=Web3.to_checksum_address(ROUTER_ADDRESS), abi=ROUTER_ABI
    )
    # La cotation vient d'un adaptateur mocké ; l'encodage utilise l'ABI réelle (offline)
    quote = _get_quote(_adapter())
    adapter = SushiswapAdapter(
        web3=MagicMock(),
        router_contract=router,
        token_decimals=DECIMALS,
        deadline_seconds=60,
        clock=lambda: NOW,
    )

    tx = asyncio.run(adapter.build_swap_transaction(quote, RECIPIENT))

    selector = Web3.keccak(
        text="swapExactTokensForTokens(uint256,uint256,address[],address,uint256)"
    )[:4].hex()
    data = tx["data"].lower().removeprefix("0x")
    assert data.startswith(selector.removeprefix("0x"))
    # tête ABI : amountIn, amountOutMin, offset(path), to, deadline (path en queue)
    head = data[8:]
    assert int(head[4 * 64 : 5 * 64], 16) == NOW + 60


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
        SushiswapAdapter(web3=MagicMock(), router_contract=MagicMock(), deadline_seconds=0)
