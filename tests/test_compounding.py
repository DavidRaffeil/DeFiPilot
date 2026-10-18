from decimal import Decimal

import pytest

from core.capital.compounding import TimeDecayCompounder

DAY = 86400
CFG = {
    "enabled": True,
    "initial_reinvest_pct": 1.0,
    "daily_decay_pct": 0.05,
    "min_reinvest_pct": 0.20,
}
T0 = 1_700_000_000


@pytest.fixture
def comp():
    return TimeDecayCompounder(CFG)


def test_day_zero_full_rate(comp):
    assert comp.get_reinvestment_rate(T0, "poolA") == Decimal("1.0")
    assert comp.get_reinvestment_rate(T0 + DAY - 1, "poolA") == Decimal("1.0")


@pytest.mark.parametrize("days,expected", [
    (1, "0.95"), (2, "0.90"), (7, "0.65"), (10, "0.50"), (15, "0.25"),
])
def test_day_n_decay(comp, days, expected):
    comp.get_reinvestment_rate(T0, "poolA")
    assert comp.get_reinvestment_rate(T0 + days * DAY + 100, "poolA") == Decimal(expected)


def test_floor_reached_and_held(comp):
    comp.get_reinvestment_rate(T0, "poolA")
    for days in (16, 20, 100, 1000):
        assert comp.get_reinvestment_rate(T0 + days * DAY, "poolA") == Decimal("0.20")


def test_pool_change_resets_clock(comp):
    comp.get_reinvestment_rate(T0, "poolA")
    assert comp.get_reinvestment_rate(T0 + 10 * DAY, "poolA") == Decimal("0.50")
    assert comp.get_reinvestment_rate(T0 + 10 * DAY, "poolB") == Decimal("1.0")
    assert comp.entry_timestamp == Decimal(T0 + 10 * DAY)
    assert comp.pool_id == "poolB"
    assert comp.get_reinvestment_rate(T0 + 12 * DAY, "poolB") == Decimal("0.90")
    # retour sur A = nouvelle position
    assert comp.get_reinvestment_rate(T0 + 12 * DAY, "poolA") == Decimal("1.0")


def test_decimal_types_no_float_error(comp):
    comp.get_reinvestment_rate(T0, "poolA")
    rate = comp.get_reinvestment_rate(T0 + 3 * DAY, "poolA")
    assert isinstance(rate, Decimal)
    assert rate == Decimal("0.85")  # exact, pas 0.8500000000000001
    alloc = comp.calculate_allocation(Decimal("100"), T0 + 3 * DAY, "poolA")
    assert all(isinstance(alloc[k], Decimal) for k in alloc)


def test_allocation_split(comp):
    a = comp.calculate_allocation("100", T0, "poolA")
    assert a["reinvest_amount"] == Decimal("100.000000")
    assert a["secured_amount"] == Decimal("0")
    a = comp.calculate_allocation("100", T0 + 5 * DAY, "poolA")
    assert a["reinvest_amount"] == Decimal("75.000000")
    assert a["secured_amount"] == Decimal("25.000000")


def test_rounding_down_and_conservation(comp):
    comp.get_reinvestment_rate(T0, "poolA")
    profit = Decimal("0.123457")
    a = comp.calculate_allocation(profit, T0 + 1 * DAY, "poolA")  # 0.95
    # 0.123457 * 0.95 = 0.11728415 -> 0.117284 (arrondi bas)
    assert a["reinvest_amount"] == Decimal("0.117284")
    assert a["secured_amount"] == profit - Decimal("0.117284")
    assert a["reinvest_amount"] + a["secured_amount"] == profit


def test_zero_profit(comp):
    a = comp.calculate_allocation(0, T0, "poolA")
    assert a["reinvest_amount"] == 0 and a["secured_amount"] == 0


def test_invalid_config():
    with pytest.raises(ValueError):
        TimeDecayCompounder({**CFG, "min_reinvest_pct": 1.5})
    with pytest.raises(ValueError):
        TimeDecayCompounder({**CFG, "daily_decay_pct": -0.1})
