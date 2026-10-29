"""
Tests unitaires pour l'interface DEX de base (core/dex/base.py).
"""

import asyncio
from dataclasses import FrozenInstanceError
from decimal import Decimal
from types import MappingProxyType

import pytest

import core.dex as dex_pkg
from core.dex.base import BaseDEXAdapter, DEXQuote


def _make_quote(**overrides) -> DEXQuote:
    params = dict(
        dex_name="dummy",
        token_in="USDC",
        token_out="WETH",
        amount_in=Decimal("100"),
        expected_amount_out=Decimal("0.05"),
        min_amount_out=Decimal("0.0495"),
        price_impact_pct=Decimal("0.1"),
        estimated_gas=150000,
        raw_quote_data={"path": ["USDC", "WETH"]},
    )
    params.update(overrides)
    return DEXQuote(**params)


def test_quote_instantiation():
    q = _make_quote()
    assert q.dex_name == "dummy"
    assert q.amount_in == Decimal("100")
    assert q.estimated_gas == 150000
    assert q.raw_quote_data == {"path": ("USDC", "WETH")}


def test_package_exports():
    assert dex_pkg.BaseDEXAdapter is BaseDEXAdapter
    assert dex_pkg.DEXQuote is DEXQuote
    assert {"BaseDEXAdapter", "DEXQuote"} <= set(dex_pkg.__all__)


def test_raw_quote_data_is_read_only():
    q = _make_quote(raw_quote_data={"a": 1, "nested": {"b": [1, 2]}})
    assert isinstance(q.raw_quote_data, MappingProxyType)
    with pytest.raises(TypeError):
        q.raw_quote_data["a"] = 2
    with pytest.raises(TypeError):
        q.raw_quote_data["nested"]["b"] = 0
    assert q.raw_quote_data["nested"]["b"] == (1, 2)  # liste -> tuple


def test_raw_quote_data_isolated_from_source_dict():
    source = {"a": 1, "l": [1]}
    q = _make_quote(raw_quote_data=source)
    source["a"] = 99
    source["l"].append(2)
    assert q.raw_quote_data["a"] == 1
    assert q.raw_quote_data["l"] == (1,)


def test_quote_is_immutable():
    q = _make_quote()
    with pytest.raises(FrozenInstanceError):
        q.amount_in = Decimal("1")


@pytest.mark.parametrize(
    "field_name",
    ["amount_in", "expected_amount_out", "min_amount_out", "price_impact_pct"],
)
def test_quote_rejects_float_amounts(field_name):
    with pytest.raises(TypeError):
        _make_quote(**{field_name: 1.0})


def test_quote_rejects_bad_types():
    with pytest.raises(TypeError):
        _make_quote(estimated_gas="150000")
    with pytest.raises(TypeError):
        _make_quote(estimated_gas=True)
    with pytest.raises(TypeError):
        _make_quote(raw_quote_data=[])
    with pytest.raises(TypeError):
        _make_quote(dex_name=None)


def test_quote_coherence():
    with pytest.raises(ValueError):
        _make_quote(amount_in=Decimal("0"))
    with pytest.raises(ValueError):
        _make_quote(min_amount_out=Decimal("1"))  # > expected
    with pytest.raises(ValueError):
        _make_quote(expected_amount_out=Decimal("-1"), min_amount_out=Decimal("-2"))
    with pytest.raises(ValueError):
        _make_quote(estimated_gas=-1)
    with pytest.raises(ValueError):
        _make_quote(amount_in=Decimal("NaN"))
    with pytest.raises(ValueError):
        _make_quote(dex_name="")


def test_abstract_base_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseDEXAdapter()


def test_incomplete_subclass_raises_type_error():
    class Incomplete(BaseDEXAdapter):
        @property
        def name(self) -> str:
            return "incomplete"

    with pytest.raises(TypeError):
        Incomplete()


class DummyAdapter(BaseDEXAdapter):
    @property
    def name(self) -> str:
        return "dummy"

    async def get_quote(self, token_in, token_out, amount_in, slippage_tolerance):
        expected = amount_in / Decimal("2000")
        return DEXQuote(
            dex_name=self.name,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            expected_amount_out=expected,
            min_amount_out=expected * (Decimal("1") - slippage_tolerance),
            price_impact_pct=Decimal("0.1"),
            estimated_gas=120000,
            raw_quote_data={"router": "0xRouter"},
        )

    async def build_swap_transaction(self, quote, recipient):
        return {
            "to": quote.raw_quote_data["router"],
            "recipient": recipient,
            "min_out": quote.min_amount_out,
        }


def test_dummy_adapter_contract():
    adapter = DummyAdapter()
    assert isinstance(adapter, BaseDEXAdapter)
    assert adapter.name == "dummy"

    quote = asyncio.run(
        adapter.get_quote("USDC", "WETH", Decimal("100"), Decimal("0.01"))
    )
    assert isinstance(quote, DEXQuote)
    assert quote.expected_amount_out == Decimal("0.05")
    assert quote.min_amount_out == Decimal("0.0495")

    tx = asyncio.run(adapter.build_swap_transaction(quote, "0xabc"))
    assert tx["to"] == "0xRouter"
    assert tx["recipient"] == "0xabc"
