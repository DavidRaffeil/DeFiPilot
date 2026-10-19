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


# --------------------------------------------------------------------------
# Callbacks concrets (build_capital_actions)
# --------------------------------------------------------------------------
from main_v6_core import CapitalActionError, build_capital_actions  # noqa: E402

VALID_ADDR = "0x" + "ab" * 20


class FakeState:
    def __init__(self):
        self.data = {}

    def get(self):
        return dict(self.data)

    def set(self, new):
        self.data = dict(new)


def test_secure_action_simulation_logs_and_no_web3(caplog):
    transfer = []
    _, secure = build_capital_actions(dry_run=True, env={},
                                      transfer_executor=lambda d: transfer.append(d))
    with caplog.at_level(logging.INFO, logger="DeFiPilot.V6Core"):
        res = secure(D("12.500000"))
    assert res == {"status": "simulated", "amount": D("12.500000")}
    assert transfer == []
    assert ("[PROFIT_SWEEPER] [SIMULATION] Balayage sécurisé de 12.500000 USDC vers la "
            "réserve externe (aucun transfert on-chain)") in caplog.text


@pytest.mark.parametrize("env", [
    {},
    {"RESERVE_WALLET_ADDRESS": "0x123"},
    {"RESERVE_WALLET_ADDRESS": "ab" * 21},
    {"RESERVE_WALLET_ADDRESS": "0x" + "zz" * 20},
    {"SAFE_WALLET_ADDRESS": "invalide"},
])
def test_secure_action_real_refuses_missing_or_invalid_address(env, caplog):
    transfer = []
    _, secure = build_capital_actions(dry_run=False, env=env,
                                      transfer_executor=lambda d: transfer.append(d))
    with caplog.at_level(logging.CRITICAL, logger="DeFiPilot.V6Core"):
        with pytest.raises(CapitalActionError):
            secure(D("5"))
    assert transfer == []
    assert "[SECURITY] Balayage annulé : RESERVE_WALLET_ADDRESS non définie ou invalide" in caplog.text


def test_secure_action_real_valid_address_and_safe_fallback():
    sent = []
    _, secure = build_capital_actions(
        dry_run=False, env={"SAFE_WALLET_ADDRESS": VALID_ADDR},
        transfer_executor=lambda d: sent.append(d) or "0xhash")
    res = secure(D("5.250000"))
    assert res["status"] == "executed"
    assert len(sent) == 1
    assert sent[0]["amount_raw"] == 5_250_000
    assert sent[0]["to"].lower() == VALID_ADDR


def test_reserve_wallet_has_priority_over_safe():
    sent = []
    other = "0x" + "cd" * 20
    _, secure = build_capital_actions(
        dry_run=False, env={"RESERVE_WALLET_ADDRESS": other, "SAFE_WALLET_ADDRESS": VALID_ADDR},
        transfer_executor=lambda d: sent.append(d))
    secure(D("1"))
    assert sent[0]["to"].lower() == other


def test_reinvest_action_simulation_signature_log_and_state(caplog):
    st = FakeState()
    liq = []
    reinvest, _ = build_capital_actions(dry_run=True, state_getter=st.get, state_setter=st.set,
                                        liquidity_executor=lambda *a: liq.append(a))
    with caplog.at_level(logging.INFO, logger="DeFiPilot.V6Core"):
        res = reinvest("poolA", D("10.000000"))
        reinvest("poolA", D("2.500000"))
    assert res == {"status": "simulated", "pool_id": "poolA", "amount": D("10.000000")}
    assert "[COMPOUNDING] [SIMULATION] Réinvestissement de 10.000000 dans la pool poolA" in caplog.text
    assert st.data["positions_simulees"] == {"poolA": "12.500000"}
    assert liq == []


def test_reinvest_action_real_routes_to_liquidity_executor():
    liq = []
    reinvest, _ = build_capital_actions(dry_run=False,
                                        liquidity_executor=lambda p, a: liq.append((p, a)))
    assert reinvest("poolB", D("3"))["status"] == "executed"
    assert liq == [("poolB", D("3"))]


def test_reinvest_action_real_without_executor_refuses():
    reinvest, _ = build_capital_actions(dry_run=False)
    with pytest.raises(CapitalActionError):
        reinvest("poolB", D("3"))


def test_manager_end_to_end_simulation_with_concrete_actions():
    st = FakeState()
    reinvest, secure = build_capital_actions(dry_run=True, state_getter=st.get, state_setter=st.set)
    m = CapitalCycleManager(cfg(threshold="5.0", sweep_pct="1.0"), reinvest, secure)
    m.process_profit("100", T0, "A")
    m.process_profit("10", T0 + 10 * DAY, "A")
    assert st.data["positions_simulees"] == {"A": "105.000000"}
    assert m.accumulated_reserve == D("0.000000")
    assert m.swept_total == D("5.000000")


def test_manager_keeps_reserve_when_real_sweep_refused():
    reinvest, secure = build_capital_actions(dry_run=False, env={},
                                             liquidity_executor=lambda p, a: None)
    m = CapitalCycleManager(cfg(threshold="5.0", sweep_pct="1.0"), reinvest, secure)
    m.process_profit("100", T0, "A")
    r = m.process_profit("10", T0 + 10 * DAY, "A")
    assert r["swept_amount"] == D("0")
    assert m.accumulated_reserve == D("5.000000")
    assert m.swept_total == D("0")

