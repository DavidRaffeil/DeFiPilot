import json
from decimal import Decimal
from pathlib import Path

import pytest

from core.capital.profit_sweeper import ProfitSweeper

CFG = {"enabled": True, "profit_threshold_usd": 10.0, "sweep_pct": 0.5, "target_asset": "USDC"}


def test_no_sweep_below_threshold():
    r = ProfitSweeper(CFG, dry_run=False, executor=lambda *a: pytest.fail("ordre")).evaluate(105, 100)
    assert not r.triggered and r.amount == 0 and r.reason == "below_threshold"


def test_no_sweep_on_loss_or_flat():
    s = ProfitSweeper(CFG, dry_run=False, executor=lambda *a: pytest.fail("ordre"))
    assert not s.evaluate(90, 100).triggered
    assert s.evaluate(90, 100).reason == "no_profit"
    assert not s.evaluate(100, 100).triggered


def test_exact_amount_above_threshold():
    r = ProfitSweeper(CFG).evaluate("130.50", "100")
    assert r.triggered
    assert r.net_profit == Decimal("30.50")
    assert r.amount == Decimal("15.25")
    assert r.target_asset == "USDC"


def test_threshold_boundary_triggers():
    assert ProfitSweeper(CFG).evaluate(110, 100).amount == Decimal("5")


def test_amount_rounded_down():
    cfg = dict(CFG, sweep_pct=0.3333, profit_threshold_usd=0)
    assert ProfitSweeper(cfg).evaluate("100.000001", 100).amount == Decimal("0")


def test_dry_run_does_not_execute():
    calls = []
    r = ProfitSweeper(CFG, dry_run=True, executor=lambda *a: calls.append(a)).evaluate(150, 100)
    assert r.triggered and r.dry_run and not r.executed and r.amount == Decimal("25")
    assert calls == []


def test_dry_run_default_is_safe():
    calls = []
    ProfitSweeper(CFG, executor=lambda *a: calls.append(a)).evaluate(150, 100)
    assert calls == []


def test_real_mode_executes_exact_amount():
    calls = []
    r = ProfitSweeper(CFG, dry_run=False, executor=lambda a, t: calls.append((a, t))).evaluate(150, 100)
    assert r.executed and calls == [(Decimal("25"), "USDC")]


def test_disabled():
    assert not ProfitSweeper(dict(CFG, enabled=False)).evaluate(500, 100).triggered


def test_invalid_pct():
    with pytest.raises(ValueError):
        ProfitSweeper(dict(CFG, sweep_pct=1.5))


def test_strategy_config_contains_sweeper():
    path = Path(__file__).resolve().parent.parent / "config" / "strategy_v6_0.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    ProfitSweeper(cfg["profit_sweeper"], dry_run=cfg["dry_run"])
