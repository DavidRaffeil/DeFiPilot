"""
Tests unitaires pour le routeur / comparateur multi-DEX (core/dex/router.py).
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Callable, Optional

import pytest

import core.dex as dex_pkg
from core.dex import (
    BaseDEXAdapter,
    DEXError,
    DEXQuote,
    DEXQuoteError,
    DEXRouter,
    DEXTransactionError,
    NoValidRouteError,
    RouteComparisonResult,
)

TOKEN_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
TOKEN_WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
RECIPIENT = "0x1111111111111111111111111111111111111111"


def _make_quote(
    dex_name: str = "quickswap",
    expected_amount_out: Decimal = Decimal("0.05"),
    estimated_gas: int = 200_000,
    amount_in: Decimal = Decimal("100"),
    slippage_tolerance: Decimal = Decimal("0.005"),
    raw_quote_data: Optional[dict[str, Any]] = None,
) -> DEXQuote:
    min_out = expected_amount_out * (Decimal("1") - slippage_tolerance)
    return DEXQuote(
        dex_name=dex_name,
        token_in=TOKEN_USDC,
        token_out=TOKEN_WETH,
        amount_in=amount_in,
        expected_amount_out=expected_amount_out,
        min_amount_out=min_out,
        price_impact_pct=Decimal("0.05"),
        estimated_gas=estimated_gas,
        raw_quote_data=raw_quote_data or {"dex": dex_name},
    )


class MockDEXAdapter(BaseDEXAdapter):
    """Adaptateur DEX simulé pour les tests du routeur."""

    def __init__(
        self,
        dex_name: str,
        quote_to_return: Optional[DEXQuote] = None,
        error_to_raise: Optional[BaseException] = None,
        delay_seconds: float = 0.0,
        tx_builder: Optional[Callable[[DEXQuote, str], dict[str, Any]]] = None,
    ) -> None:
        self._name = dex_name
        self._quote = quote_to_return
        self._error = error_to_raise
        self._delay = delay_seconds
        self._tx_builder = tx_builder
        self.quote_calls: list[tuple[str, str, Decimal, Decimal]] = []
        self.tx_calls: list[tuple[DEXQuote, str]] = []

    @property
    def name(self) -> str:
        return self._name

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal,
    ) -> DEXQuote:
        self.quote_calls.append((token_in, token_out, amount_in, slippage_tolerance))
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        if self._error is not None:
            raise self._error
        assert self._quote is not None
        return self._quote

    async def build_swap_transaction(
        self, quote: DEXQuote, recipient: str
    ) -> dict[str, Any]:
        self.tx_calls.append((quote, recipient))
        if self._tx_builder is not None:
            return self._tx_builder(quote, recipient)
        return {
            "dex": self.name,
            "to": f"0xRouter_{self.name}",
            "recipient": recipient,
            "min_amount_out": str(quote.min_amount_out),
            "gas": quote.estimated_gas,
        }


# ------------------------------------------------------------------ exports & init


def test_package_exports() -> None:
    assert dex_pkg.DEXRouter is DEXRouter
    assert dex_pkg.RouteComparisonResult is RouteComparisonResult
    assert dex_pkg.NoValidRouteError is NoValidRouteError
    assert issubclass(NoValidRouteError, DEXError)
    assert {
        "DEXRouter",
        "RouteComparisonResult",
        "NoValidRouteError",
    } <= set(dex_pkg.__all__)


def test_router_init_validation() -> None:
    adapter = MockDEXAdapter("quickswap", _make_quote("quickswap"))
    router = DEXRouter([adapter], default_timeout=2.5)
    assert router.default_timeout == 2.5
    assert router.adapters == [adapter]

    with pytest.raises(ValueError, match="liste non vide"):
        DEXRouter([])

    with pytest.raises(TypeError, match="BaseDEXAdapter"):
        DEXRouter(["not_an_adapter"])  # type: ignore[list-item]

    with pytest.raises(ValueError, match="doublon"):
        DEXRouter([adapter, MockDEXAdapter("quickswap", _make_quote("quickswap"))])

    with pytest.raises(ValueError, match="strictement positif"):
        DEXRouter([adapter], default_timeout=0)

    with pytest.raises(ValueError, match="strictement positif"):
        DEXRouter([adapter], default_timeout=-1.0)

    with pytest.raises(ValueError, match="strictement positif"):
        DEXRouter([adapter], default_timeout=True)  # type: ignore[arg-type]


# ------------------------------------------------------------------ cas nominal


def test_get_quotes_selects_highest_expected_output() -> None:
    q_quick = _make_quote("quickswap", expected_amount_out=Decimal("0.0510"), estimated_gas=250_000)
    q_sushi = _make_quote("sushiswap", expected_amount_out=Decimal("0.0525"), estimated_gas=280_000)
    q_uni = _make_quote("uniswap_v3", expected_amount_out=Decimal("0.0498"), estimated_gas=180_000)

    a_quick = MockDEXAdapter("quickswap", quote_to_return=q_quick)
    a_sushi = MockDEXAdapter("sushiswap", quote_to_return=q_sushi)
    a_uni = MockDEXAdapter("uniswap_v3", quote_to_return=q_uni)

    router = DEXRouter([a_quick, a_sushi, a_uni])
    result = asyncio.run(
        router.get_quotes(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
    )

    assert isinstance(result, RouteComparisonResult)
    assert result.best_quote == q_sushi
    assert result.best_quote.dex_name == "sushiswap"
    assert result.all_quotes == [q_quick, q_sushi, q_uni]
    assert result.failed_dexes == {}

    for adapter in (a_quick, a_sushi, a_uni):
        assert adapter.quote_calls == [
            (TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
        ]


def test_get_best_quote_helper_returns_best_quote_directly() -> None:
    q_quick = _make_quote("quickswap", expected_amount_out=Decimal("0.0550"))
    q_sushi = _make_quote("sushiswap", expected_amount_out=Decimal("0.0530"))

    router = DEXRouter(
        [
            MockDEXAdapter("quickswap", quote_to_return=q_quick),
            MockDEXAdapter("sushiswap", quote_to_return=q_sushi),
        ]
    )

    best = asyncio.run(
        router.get_best_quote(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
    )
    assert best == q_quick


# ------------------------------------------------------------------ égalité output -> gas


def test_get_quotes_tie_breaker_selects_lowest_estimated_gas() -> None:
    same_output = Decimal("0.050000000000000000")
    q_high_gas = _make_quote("quickswap", expected_amount_out=same_output, estimated_gas=250_000)
    q_low_gas = _make_quote("sushiswap", expected_amount_out=same_output, estimated_gas=145_000)
    q_mid_gas = _make_quote("uniswap_v3", expected_amount_out=same_output, estimated_gas=190_000)

    router = DEXRouter(
        [
            MockDEXAdapter("quickswap", quote_to_return=q_high_gas),
            MockDEXAdapter("sushiswap", quote_to_return=q_low_gas),
            MockDEXAdapter("uniswap_v3", quote_to_return=q_mid_gas),
        ]
    )

    result = asyncio.run(
        router.get_quotes(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
    )

    assert result.best_quote == q_low_gas
    assert result.best_quote.dex_name == "sushiswap"
    assert result.best_quote.estimated_gas == 145_000


# ------------------------------------------------------------------ pannes partielles


def test_partial_failure_dex_quote_error_isolated() -> None:
    q_quick = _make_quote("quickswap", expected_amount_out=Decimal("0.0510"))
    q_uni = _make_quote("uniswap_v3", expected_amount_out=Decimal("0.0520"))

    a_quick = MockDEXAdapter("quickswap", quote_to_return=q_quick)
    a_sushi = MockDEXAdapter(
        "sushiswap",
        error_to_raise=DEXQuoteError("Pool introuvable pour cette paire"),
    )
    a_uni = MockDEXAdapter("uniswap_v3", quote_to_return=q_uni)

    router = DEXRouter([a_quick, a_sushi, a_uni])
    result = asyncio.run(
        router.get_quotes(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
    )

    assert result.best_quote == q_uni
    assert result.all_quotes == [q_quick, q_uni]
    assert "sushiswap" in result.failed_dexes
    assert "Pool introuvable" in result.failed_dexes["sushiswap"]


def test_partial_failure_timeout_isolated() -> None:
    q_quick = _make_quote("quickswap", expected_amount_out=Decimal("0.0510"))

    a_quick = MockDEXAdapter("quickswap", quote_to_return=q_quick, delay_seconds=0.01)
    a_slow = MockDEXAdapter("sushiswap", quote_to_return=q_quick, delay_seconds=0.5)

    router = DEXRouter([a_quick, a_slow], default_timeout=0.05)
    result = asyncio.run(
        router.get_quotes(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
    )

    assert result.best_quote == q_quick
    assert result.all_quotes == [q_quick]
    assert set(result.failed_dexes.keys()) == {"sushiswap"}
    assert "Timeout" in result.failed_dexes["sushiswap"]


# ------------------------------------------------------------------ échec total


def test_total_failure_all_dexes_error_raises_no_valid_route_error() -> None:
    a_quick = MockDEXAdapter(
        "quickswap",
        error_to_raise=DEXQuoteError("Liquidité insuffisante sur QuickSwap"),
    )
    a_sushi = MockDEXAdapter(
        "sushiswap",
        error_to_raise=RuntimeError("RPC HTTP 503 Service Unavailable"),
    )

    router = DEXRouter([a_quick, a_sushi])

    with pytest.raises(NoValidRouteError) as exc_info:
        asyncio.run(
            router.get_quotes(TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005"))
        )

    msg = str(exc_info.value)
    assert "quickswap" in msg
    assert "sushiswap" in msg


def test_total_failure_all_dexes_timeout_raises_no_valid_route_error() -> None:
    q_dummy = _make_quote("quickswap")
    a_quick = MockDEXAdapter("quickswap", quote_to_return=q_dummy, delay_seconds=0.5)
    a_sushi = MockDEXAdapter("sushiswap", quote_to_return=q_dummy, delay_seconds=0.5)

    router = DEXRouter([a_quick, a_sushi], default_timeout=0.03)

    with pytest.raises(NoValidRouteError) as exc_info:
        asyncio.run(
            router.get_best_quote(
                TOKEN_USDC, TOKEN_WETH, Decimal("100"), Decimal("0.005")
            )
        )

    assert "Timeout" in str(exc_info.value)


# ------------------------------------------------------------------ build_swap_transaction


def test_build_swap_transaction_delegates_to_matching_adapter() -> None:
    q_quick = _make_quote("quickswap", expected_amount_out=Decimal("0.0510"))
    q_sushi = _make_quote("sushiswap", expected_amount_out=Decimal("0.0525"))

    a_quick = MockDEXAdapter("quickswap", quote_to_return=q_quick)
    a_sushi = MockDEXAdapter("sushiswap", quote_to_return=q_sushi)

    router = DEXRouter([a_quick, a_sushi])

    tx = asyncio.run(router.build_swap_transaction(q_sushi, RECIPIENT))

    assert tx["dex"] == "sushiswap"
    assert tx["to"] == "0xRouter_sushiswap"
    assert tx["recipient"] == RECIPIENT
    assert a_sushi.tx_calls == [(q_sushi, RECIPIENT)]
    assert a_quick.tx_calls == []


def test_build_swap_transaction_unknown_dex_raises_error() -> None:
    q_quick = _make_quote("quickswap")
    q_unknown = _make_quote("balancer")

    router = DEXRouter([MockDEXAdapter("quickswap", quote_to_return=q_quick)])

    with pytest.raises(DEXTransactionError, match="balancer"):
        asyncio.run(router.build_swap_transaction(q_unknown, RECIPIENT))

    with pytest.raises(DEXTransactionError, match="DEXQuote"):
        asyncio.run(router.build_swap_transaction("invalid", RECIPIENT))  # type: ignore[arg-type]
