"""
Tests unitaires d'intégration du DEXRouter dans le flux de swap et de stratégie (V6.5).
Couvre le feature flag FEATURE_MULTI_DEX (actif / inactif) ainsi que le repli (fallback).
"""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

import core.config as app_config
from core.dex import (
    BaseDEXAdapter,
    DEXQuote,
    DEXRouter,
    NoValidRouteError,
)
from core.dry_run_guard import set_dry_run_mode
from core.executor_real import executer_action_reelle
from core.strategy_engine import (
    Allocation,
    PortfolioSnapshot,
    StrategyEngine,
)
from core.swap_reel import effectuer_swap_reel

TOKEN_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
TOKEN_WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
STRATEGY_CFG_PATH = "config/strategy_v6_0.json"


class StubDEXAdapter(BaseDEXAdapter):
    """Adaptateur DEX léger pour tester l'intégration du routeur."""

    def __init__(
        self,
        dex_name: str,
        expected_out: Decimal = Decimal("0.0525"),
        estimated_gas: int = 160_000,
        error: Optional[Exception] = None,
    ) -> None:
        self._name = dex_name
        self._expected_out = expected_out
        self._gas = estimated_gas
        self._error = error
        self.quote_calls: int = 0
        self.tx_calls: int = 0

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
        self.quote_calls += 1
        if self._error is not None:
            raise self._error
        min_out = self._expected_out * (Decimal("1") - slippage_tolerance)
        return DEXQuote(
            dex_name=self._name,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            expected_amount_out=self._expected_out,
            min_amount_out=min_out,
            price_impact_pct=Decimal("0.05"),
            estimated_gas=self._gas,
            raw_quote_data={"dex": self._name},
        )

    async def build_swap_transaction(
        self, quote: DEXQuote, recipient: str
    ) -> dict[str, Any]:
        self.tx_calls += 1
        return {
            "to": f"0xRouter_{self._name}",
            "data": "0xabcdef",
            "value": 0,
            "chainId": 137,
            "gas": quote.estimated_gas,
            "recipient": recipient,
        }


# ------------------------------------------------------------------ 1. Config


def test_config_feature_multi_dex_default_true() -> None:
    assert hasattr(app_config, "FEATURE_MULTI_DEX")
    assert isinstance(app_config.FEATURE_MULTI_DEX, bool)
    assert app_config.FEATURE_MULTI_DEX is True


# ------------------------------------------------------------------ 2. StrategyEngine


def test_strategy_engine_auto_creates_default_router_when_web3_provided() -> None:
    mock_web3 = MagicMock()
    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        web3_client=mock_web3,
        feature_multi_dex=True,
    )
    assert isinstance(engine.dex_router, DEXRouter)
    assert [a.name for a in engine.dex_router.adapters] == [
        "uniswap_v3",
        "quickswap",
        "sushiswap",
    ]


def test_strategy_engine_does_not_create_router_when_flag_disabled() -> None:
    mock_web3 = MagicMock()
    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        web3_client=mock_web3,
        feature_multi_dex=False,
    )
    assert engine.dex_router is None


def test_strategy_engine_prepare_swap_with_multi_dex_enabled_logs_and_builds_tx(
    caplog: pytest.LogCaptureFixture,
) -> None:
    a_quick = StubDEXAdapter("quickswap", expected_out=Decimal("0.0510"), estimated_gas=220_000)
    a_uni = StubDEXAdapter("uniswap_v3", expected_out=Decimal("0.0545"), estimated_gas=180_000)
    router = DEXRouter([a_quick, a_uni])

    mock_logger = MagicMock()
    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        logger=mock_logger,
        dex_router=router,
        feature_multi_dex=True,
    )

    with caplog.at_level(logging.INFO, logger="core.strategy_engine"):
        action = engine.prepare_swap_action(
            token_a="USDC",
            token_b="WETH",
            swap_amount=50.0,
            max_slippage=0.5,
            dry_run=True,
        )

    assert action.kind == "swap"
    assert action.params["tokenA"] == "USDC"
    assert action.params["tokenB"] == "WETH"
    assert action.params["amountA"] == 50.0
    assert action.params["dex"] == "uniswap_v3"
    assert action.params["expected_amount_out"] == "0.0545"
    assert action.params["tx"]["to"] == "0xRouter_uniswap_v3"
    assert a_uni.quote_calls == 1
    assert a_uni.tx_calls == 1
    assert a_quick.quote_calls == 1
    assert a_quick.tx_calls == 0

    # Vérifie que le log mentionne le DEX retenu et le montant espéré
    assert any(
        "uniswap_v3" in record.message and "0.0545" in record.message
        for record in caplog.records
    )


def test_strategy_engine_prepare_swap_with_flag_disabled_bypasses_router() -> None:
    a_uni = StubDEXAdapter("uniswap_v3", expected_out=Decimal("0.0545"))
    router = DEXRouter([a_uni])

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        dex_router=router,
        feature_multi_dex=False,
    )

    action = engine.prepare_swap_action(
        token_a="USDC",
        token_b="WETH",
        swap_amount=50.0,
        max_slippage=0.5,
        dry_run=True,
    )

    assert action.kind == "swap"
    assert "dex" not in action.params
    assert "tx" not in action.params
    assert a_uni.quote_calls == 0
    assert a_uni.tx_calls == 0


def test_strategy_engine_fallback_when_router_fails_does_not_interrupt_cycle() -> None:
    failing_adapter = StubDEXAdapter(
        "quickswap",
        error=NoValidRouteError("Aucune liquidité disponible"),
    )
    router = DEXRouter([failing_adapter])

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        dex_router=router,
        feature_multi_dex=True,
    )

    with patch(
        "core.strategy_engine.lire_soldes_depuis_env",
        return_value={"USDC": 100.0, "native": 1.0},
    ):
        allocs = [Allocation(pool_id="USDC-WETH", target_pct=1.0, risk_level="prudent")]
        snapshot = PortfolioSnapshot(
            balances={"USDC": 100.0}, allowances={}, timestamp=1700000000.0
        )
        actions = engine.build_actions(allocs, snapshot)

    assert len(actions) == 3
    swap_action = actions[0]
    assert swap_action.kind == "swap"
    assert swap_action.params["tokenA"] == "USDC"
    assert swap_action.params["tokenB"] == "WETH"
    # Le repli unitaire garde les paramètres nominaux sans lever d'exception
    assert "dex" not in swap_action.params
    assert failing_adapter.quote_calls == 1


# ------------------------------------------------------------------ 3. swap_reel & executor_real


def test_swap_reel_multi_dex_enabled_selects_best_dex_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    set_dry_run_mode(True)
    a_sushi = StubDEXAdapter("sushiswap", expected_out=Decimal("0.0490"))
    a_quick = StubDEXAdapter("quickswap", expected_out=Decimal("0.0530"))
    router = DEXRouter([a_sushi, a_quick])

    with caplog.at_level(logging.INFO, logger="core.swap_reel"):
        res = effectuer_swap_reel(
            dex="sushiswap",
            token_in="USDC",
            token_out="WETH",
            amount_in_wei=100_000_000,
            dry_run=True,
            dex_router=router,
            feature_multi_dex=True,
        )

    assert res["status"] == "SUCCESS"
    details = res["details"]
    assert details["dex"] == "quickswap"
    assert details["expected_amount_out"] == "0.0530"
    assert details["tx"]["to"] == "0xRouter_quickswap"
    assert a_quick.tx_calls == 1
    assert a_sushi.tx_calls == 0
    assert any(
        "quickswap" in record.message and "0.0530" in record.message
        for record in caplog.records
    )


def test_swap_reel_multi_dex_disabled_uses_nominal_dex() -> None:
    set_dry_run_mode(True)
    a_quick = StubDEXAdapter("quickswap", expected_out=Decimal("0.0530"))
    router = DEXRouter([a_quick])

    res = effectuer_swap_reel(
        dex="sushiswap",
        token_in="USDC",
        token_out="WETH",
        amount_in_wei=100_000_000,
        dry_run=True,
        dex_router=router,
        feature_multi_dex=False,
    )

    assert res["status"] == "SUCCESS"
    assert res["details"]["dex"] == "sushiswap"
    assert "tx" not in res["details"]
    assert a_quick.quote_calls == 0


def test_swap_reel_fallback_when_router_raises_error() -> None:
    set_dry_run_mode(True)
    failing_adapter = StubDEXAdapter(
        "quickswap", error=RuntimeError("RPC timeout")
    )
    router = DEXRouter([failing_adapter])

    res = effectuer_swap_reel(
        dex="sushiswap",
        token_in="USDC",
        token_out="WETH",
        amount_in_wei=100_000_000,
        dry_run=True,
        dex_router=router,
        feature_multi_dex=True,
    )

    assert res["status"] == "SUCCESS"
    assert res["details"]["dex"] == "sushiswap"
    assert "tx" not in res["details"]
    assert failing_adapter.quote_calls == 1


def test_executor_real_with_multi_dex_and_fallback() -> None:
    set_dry_run_mode(True)
    a_uni = StubDEXAdapter("uniswap_v3", expected_out=Decimal("0.0260"))
    router_ok = DEXRouter([a_uni])

    action = {
        "kind": "swap",
        "dry_run": True,
        "params": {"tokenA": "USDC", "tokenB": "ETH", "amountA": 50.0},
    }

    with patch(
        "core.guardrails.verifier_action_reelle",
        return_value={"status": "EXECUTED", "details": {"reason": "ok"}},
    ):
        # 1. Flag actif -> routeur sélectionne uniswap_v3
        res_ok = executer_action_reelle(
            action,
            run_id="run_multi_dex_ok",
            dex_router=router_ok,
            feature_multi_dex=True,
        )
        assert res_ok["status"] == "EXECUTED"
        assert res_ok["details"]["dex"] == "uniswap_v3"
        assert res_ok["details"]["expected_amount_out"] == "0.0260"
        assert res_ok["details"]["tx"]["to"] == "0xRouter_uniswap_v3"

        # 2. Flag inactif -> repli sur sushiswap sans interroger le routeur
        res_off = executer_action_reelle(
            action,
            run_id="run_multi_dex_off",
            dex_router=router_ok,
            feature_multi_dex=False,
        )
        assert res_off["status"] == "EXECUTED"
        assert res_off["details"]["dex"] == "sushiswap"
        assert a_uni.quote_calls == 1  # pas d'appel supplémentaire

        # 3. Routeur en échec -> repli transparent sur sushiswap
        router_fail = DEXRouter(
            [StubDEXAdapter("quickswap", error=NoValidRouteError("aucun pool"))]
        )
        res_fallback = executer_action_reelle(
            action,
            run_id="run_multi_dex_fallback",
            dex_router=router_fail,
            feature_multi_dex=True,
        )
        assert res_fallback["status"] == "EXECUTED"
        assert res_fallback["details"]["dex"] == "sushiswap"
