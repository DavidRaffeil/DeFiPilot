from decimal import Decimal
import logging

import pytest

from main_v6_core import CapitalCycleManager

DAY = 86400
T0 = 1_700_000_000
D = Decimal


def cfg(threshold="5.0", sweep_pct="1.0", decay="0.05", sweeper=True):
    c = {"compounding": {"enabled": True, "initial_reinvest_pct": 1.0,
                         "daily_decay_pct": decay, "min_reinvest_pct": 0.20}}
    if sweeper:
        c["profit_sweeper"] = {"enabled": True, "profit_threshold_usd": threshold,
                               "sweep_pct": sweep_pct, "target_asset": "USDC"}
    return c


@pytest.fixture
def calls():
    return {"reinvest": [], "secure": []}


def make(calls, **kw):
    return CapitalCycleManager(
        cfg(**kw),
        reinvest_action=lambda pool, amt: calls["reinvest"].append((pool, amt)),
        secure_action=lambda amt: calls["secure"].append(amt),
    )


def test_accumulation_below_threshold_no_sweep(calls):
    m = make(calls, threshold="5.0")
    m.process_profit("10", T0, "A")                      # 100 % reinvesti
    r = m.process_profit("10", T0 + 2 * DAY, "A")        # 0.90 -> 1 en reserve
    assert r["secured_amount"] == D("1.000000")
    assert r["swept_amount"] == D("0")
    assert m.accumulated_reserve == D("1.000000")
    assert calls["secure"] == []
    assert calls["reinvest"] == [("A", D("10.000000")), ("A", D("9.000000"))]


def test_threshold_reached_total_sweep(calls):
    m = make(calls, threshold="5.0", sweep_pct="1.0")
    m.process_profit("100", T0, "A")
    m.process_profit("10", T0 + 10 * DAY, "A")           # 0.50 -> reserve 5.0
    assert calls["secure"] == [D("5.000000")]
    assert m.accumulated_reserve == D("0.000000")
    assert m.swept_total == D("5.000000")


def test_threshold_exceeded_partial_sweep_keeps_remainder(calls):
    m = make(calls, threshold="5.0", sweep_pct="0.5")
    m.process_profit("100", T0, "A")
    r = m.process_profit("20", T0 + 10 * DAY, "A")       # reserve 10 -> sweep 5
    assert r["swept_amount"] == D("5.000000")
    assert calls["secure"] == [D("5.000000")]
    assert m.accumulated_reserve == D("5.000000")


def test_reserve_accumulates_then_sweeps_across_cycles(calls):
    m = make(calls, threshold="2.0", sweep_pct="1.0")
    m.process_profit("10", T0, "A")
    m.process_profit("10", T0 + 10 * DAY, "A")           # +5.0 -> sweep 5
    assert calls["secure"] == [D("5.000000")]
    m.process_profit("1", T0 + 20 * DAY, "A")            # 0.2 rate floor... +0.8
    assert m.accumulated_reserve == D("0.800000")
    assert len(calls["secure"]) == 1


def test_rounding_down_and_conservation(calls):
    m = make(calls, threshold="100", sweep_pct="1.0")
    m.process_profit("1", T0, "A")
    profit = D("0.333333")
    r = m.process_profit(profit, T0 + 3 * DAY, "A")      # 0.85
    assert r["reinvest_amount"] == D("0.283333")         # 0.28333305 arrondi bas
    assert r["reinvest_amount"] + r["secured_amount"] == profit
    assert m.accumulated_reserve == r["secured_amount"]
    for v in r.values():
        assert isinstance(v, Decimal)


def test_pool_change_resets_and_reserve_persists(calls):
    m = make(calls, threshold="100")
    m.process_profit("10", T0, "A")
    m.process_profit("10", T0 + 10 * DAY, "A")           # reserve 5
    r = m.process_profit("10", T0 + 10 * DAY, "B")       # reset -> 100 %
    assert r["rate"] == D("1.0")
    assert m.accumulated_reserve == D("5.000000")
    assert calls["reinvest"][-1] == ("B", D("10.000000"))


def test_no_sweeper_config_accumulates_only(calls):
    m = make(calls, sweeper=False)
    m.process_profit("10", T0, "A")
    m.process_profit("10", T0 + 10 * DAY, "A")
    assert calls["secure"] == []
    assert m.accumulated_reserve == D("5.000000")


def test_logs_prefixes(calls, caplog):
    m = make(calls, threshold="5.0", sweep_pct="1.0")
    with caplog.at_level(logging.INFO, logger="DeFiPilot.V6Core"):
        m.process_profit("100", T0, "A")
        m.process_profit("10", T0 + 10 * DAY, "A")
    text = "\n".join(caplog.messages)
    assert "[COMPOUNDING] pool=A jours=10 taux=0.50" in text
    assert "[PROFIT_SWEEPER] pas de sweep" in text      # 1er cycle : reserve 0
    assert "[PROFIT_SWEEPER] sweep=5.000000 USDC reserve_restante=0.000000" in text
