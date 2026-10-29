"""
Tests d'intégration E2E du cycle complet Multi-DEX en mode simulation / dry-run (V6.5).

Valide la chaîne complète depuis la prise de décision de `StrategyEngine.run()`
jusqu'à la préparation et la simulation de l'action de swap via `DEXRouter`
avec les 3 adaptateurs Polygon (Uniswap V3, QuickSwap V3, SushiSwap V2),
sans aucun appel réseau externe ni broadcast RPC.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
import logging
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest
from web3 import Web3
from web3.exceptions import ContractLogicError

from core.dex import (
    BaseDEXAdapter,
    DEXQuote,
    DEXQuoteError,
    DEXRouter,
    QuickswapAdapter,
    SushiswapAdapter,
    UniswapV3Adapter,
)
from core.dex.quickswap import (
    SWAP_ROUTER_ABI as QUICKSWAP_ROUTER_ABI,
    SWAP_ROUTER_ADDRESS as QUICKSWAP_ROUTER_ADDRESS,
)
from core.dex.sushiswap import (
    ROUTER_ABI as SUSHISWAP_ROUTER_ABI,
    ROUTER_ADDRESS as SUSHISWAP_ROUTER_ADDRESS,
)
from core.dex.uniswap_v3 import (
    SWAP_ROUTER_02_ABI as UNISWAP_ROUTER_ABI,
    SWAP_ROUTER_02_ADDRESS as UNISWAP_ROUTER_ADDRESS,
)
from core.dry_run_guard import is_dry_run_enabled, set_dry_run_mode
from core.strategy_context import StrategyContext
from core.strategy_engine import PoolCandidate, StrategyEngine

STRATEGY_CFG_PATH = "config/strategy_v6_0.json"
USDC_ADDRESS = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
WETH_ADDRESS = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
DECIMALS_MAP = {USDC_ADDRESS: 6, WETH_ADDRESS: 18}


class MockPolygonDEXAdapter(BaseDEXAdapter):
    """Adaptateur DEX mocké simulant Uniswap V3, QuickSwap ou SushiSwap."""

    def __init__(
        self,
        dex_name: str,
        router_address: str,
        expected_amount_out: Decimal = Decimal("0.00025"),
        estimated_gas: int = 180_000,
        delay_seconds: float = 0.0,
        error_to_raise: Optional[BaseException] = None,
        web3_spy: Optional[MagicMock] = None,
    ) -> None:
        self._name = dex_name
        self._router_address = Web3.to_checksum_address(router_address)
        self._expected_out = expected_amount_out
        self._gas = estimated_gas
        self._delay = delay_seconds
        self._error = error_to_raise
        self._web3_spy = web3_spy or MagicMock()
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

        min_out = self._expected_out * (Decimal("1") - slippage_tolerance)
        return DEXQuote(
            dex_name=self._name,
            token_in=Web3.to_checksum_address(token_in),
            token_out=Web3.to_checksum_address(token_out),
            amount_in=amount_in,
            expected_amount_out=self._expected_out,
            min_amount_out=min_out,
            price_impact_pct=Decimal("0.04"),
            estimated_gas=self._gas,
            raw_quote_data={
                "router": self._router_address,
                "amount_in_raw": int(amount_in * Decimal(10**6)),
            },
        )

    async def build_swap_transaction(
        self, quote: DEXQuote, recipient: str
    ) -> dict[str, Any]:
        self.tx_calls.append((quote, recipient))
        return {
            "to": self._router_address,
            "data": f"0xcalldata_{self._name}",
            "value": 0,
            "chainId": 137,
            "gas": quote.estimated_gas,
        }


def _candidate_pools() -> list[PoolCandidate]:
    return [
        PoolCandidate(
            pool_id="USDC-WETH",
            platform="quickswap",
            chain="polygon",
            symbols="USDC-WETH",
            tvl=1_200_000.0,
            apr=18.5,
            score=0.92,
        ),
        PoolCandidate(
            pool_id="USDC-USDT",
            platform="uniswap_v3",
            chain="polygon",
            symbols="USDC-USDT",
            tvl=850_000.0,
            apr=6.2,
            score=0.65,
        ),
    ]


# ------------------------------------------------------------------ Scénario 1 : Cycle E2E nominal (3 DEX répondent)


def test_e2e_multi_dex_nominal_cycle_selects_best_output_and_no_rpc_broadcast(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Cycle E2E complet :
    - 3 adaptateurs (Uniswap V3, QuickSwap, SushiSwap) retournent des cotations différenciées.
    - QuickSwap offre le meilleur expected_amount_out (0.000275 WETH pour 0.5 USDC).
    - Vérifie la sélection de QuickSwap, la présence des logs, la construction de la tx
      et l'absence totale de diffusion RPC (dry-run).
    """
    set_dry_run_mode(True)
    assert is_dry_run_enabled() is True

    web3_spy = MagicMock()

    uniswap_mock = MockPolygonDEXAdapter(
        dex_name="uniswap_v3",
        router_address=UNISWAP_ROUTER_ADDRESS,
        expected_amount_out=Decimal("0.000260"),
        estimated_gas=185_000,
        web3_spy=web3_spy,
    )
    quickswap_mock = MockPolygonDEXAdapter(
        dex_name="quickswap",
        router_address=QUICKSWAP_ROUTER_ADDRESS,
        expected_amount_out=Decimal("0.000275"),  # Meilleur output net
        estimated_gas=250_000,
        web3_spy=web3_spy,
    )
    sushiswap_mock = MockPolygonDEXAdapter(
        dex_name="sushiswap",
        router_address=SUSHISWAP_ROUTER_ADDRESS,
        expected_amount_out=Decimal("0.000252"),
        estimated_gas=150_000,
        web3_spy=web3_spy,
    )

    router = DEXRouter([uniswap_mock, quickswap_mock, sushiswap_mock], default_timeout=2.0)

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        dex_router=router,
        web3_client=web3_spy,
        feature_multi_dex=True,
    )

    context = StrategyContext(
        timestamp="2026-10-29T14:00:00Z",
        label="favorable",
        ai_score=0.85,
        confiance=0.9,
        resume="Marché haussier favorable",
        metrics={"volatility": 0.12},
        nb_signaux=10,
    )

    with (
        patch(
            "core.strategy_engine.lire_soldes_depuis_env",
            return_value={"USDC": 100.0, "native": 5.0},
        ),
        caplog.at_level(logging.INFO, logger="core.strategy_engine"),
    ):
        plan = engine.run(pools=_candidate_pools(), context=context)

    # 1. Validation de la décision stratégique
    assert plan["dry_run"] is True
    assert len(plan["candidates"]) == 1
    assert plan["candidates"][0]["pool_id"] == "USDC-WETH"
    assert len(plan["allocations"]) == 1

    # 2. Validation des actions préparées et du choix du meilleur DEX
    actions = plan["actions"]
    assert len(actions) == 3
    swap_action = actions[0]
    assert swap_action["kind"] == "swap"
    assert swap_action["dry_run"] is True

    swap_params = swap_action["params"]
    assert swap_params["tokenA"] == "USDC"
    assert swap_params["tokenB"] == "WETH"
    assert swap_params["dex"] == "quickswap"
    assert swap_params["expected_amount_out"] == "0.000275"

    # 3. Validation de la transaction construite uniquement par l'adaptateur gagnant
    assert len(uniswap_mock.quote_calls) == 1
    assert len(quickswap_mock.quote_calls) == 1
    assert len(sushiswap_mock.quote_calls) == 1

    assert len(quickswap_mock.tx_calls) == 1
    assert len(uniswap_mock.tx_calls) == 0
    assert len(sushiswap_mock.tx_calls) == 0

    built_tx = swap_params["tx"]
    assert built_tx["to"] == Web3.to_checksum_address(QUICKSWAP_ROUTER_ADDRESS)
    assert built_tx["data"] == "0xcalldata_quickswap"
    assert built_tx["chainId"] == 137
    assert built_tx["gas"] == 250_000

    # 4. Validation des logs d'arbitrage et de sélection du DEX
    assert any(
        "[MULTI-DEX]" in record.message
        and "quickswap" in record.message
        and "0.000275" in record.message
        for record in caplog.records
    )

    # 5. Validation de l'exécution Dry-Run : zéro broadcast RPC
    exec_output = plan["execution_output"]
    assert exec_output["status"] == "executed"
    swap_exec_result = exec_output["results"][0]
    assert swap_exec_result["status"] == "EXECUTED"
    assert swap_exec_result["tx_hash"] is None
    assert swap_exec_result["details"]["mode"] == "[SIMULATION / DRY-RUN]"
    assert swap_exec_result["details"]["dex"] == "quickswap"
    assert swap_exec_result["details"]["tx"] == built_tx

    web3_spy.eth.send_raw_transaction.assert_not_called()
    web3_spy.eth.send_transaction.assert_not_called()


# ------------------------------------------------------------------ Scénario 2 : 2 DEX échouent (timeout + RPC error), le 3e réussit


def test_e2e_multi_dex_resilience_two_dexes_fail_third_succeeds(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Scénario de résilience E2E :
    - Uniswap V3 échoue par timeout.
    - QuickSwap échoue par erreur RPC / revert (DEXQuoteError).
    - SushiSwap répond normalement et sa cotation est retenue pour construire le swap.
    """
    set_dry_run_mode(True)
    web3_spy = MagicMock()

    uniswap_timeout = MockPolygonDEXAdapter(
        dex_name="uniswap_v3",
        router_address=UNISWAP_ROUTER_ADDRESS,
        delay_seconds=0.5,  # Dépassera le timeout de 0.05s
        web3_spy=web3_spy,
    )
    quickswap_rpc_err = MockPolygonDEXAdapter(
        dex_name="quickswap",
        router_address=QUICKSWAP_ROUTER_ADDRESS,
        error_to_raise=DEXQuoteError("RPC connection reset by peer"),
        web3_spy=web3_spy,
    )
    sushiswap_ok = MockPolygonDEXAdapter(
        dex_name="sushiswap",
        router_address=SUSHISWAP_ROUTER_ADDRESS,
        expected_amount_out=Decimal("0.000248"),
        estimated_gas=150_000,
        web3_spy=web3_spy,
    )

    router = DEXRouter(
        [uniswap_timeout, quickswap_rpc_err, sushiswap_ok],
        default_timeout=0.05,
    )

    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        dex_router=router,
        web3_client=web3_spy,
        feature_multi_dex=True,
    )

    with (
        patch(
            "core.strategy_engine.lire_soldes_depuis_env",
            return_value={"USDC": 100.0, "native": 5.0},
        ),
        caplog.at_level(logging.INFO, logger="core.strategy_engine"),
    ):
        plan = engine.run(pools=_candidate_pools())

    swap_action = plan["actions"][0]
    swap_params = swap_action["params"]

    # Le seul DEX survivant (sushiswap) est retenu
    assert swap_params["dex"] == "sushiswap"
    assert swap_params["expected_amount_out"] == "0.000248"
    assert swap_params["tx"]["to"] == Web3.to_checksum_address(SUSHISWAP_ROUTER_ADDRESS)

    assert len(sushiswap_ok.tx_calls) == 1
    assert len(uniswap_timeout.tx_calls) == 0
    assert len(quickswap_rpc_err.tx_calls) == 0

    assert any(
        "sushiswap" in record.message and "0.000248" in record.message
        for record in caplog.records
    )

    # Aucun envoi on-chain
    web3_spy.eth.send_raw_transaction.assert_not_called()
    web3_spy.eth.send_transaction.assert_not_called()


# ------------------------------------------------------------------ Scénario 3 : Adaptateurs réels (ABI encoding) avec contrats Quoter mockés


def test_e2e_multi_dex_with_real_adapter_instances_and_abi_encoding() -> None:
    """
    Vérifie le cycle E2E avec les véritables classes `UniswapV3Adapter`,
    `QuickswapAdapter` et `SushiswapAdapter` (encodage ABI réel hors-ligne,
    contrats de cotation mockés).
    """
    set_dry_run_mode(True)
    offline_w3 = Web3()
    web3_spy = MagicMock()

    # 1. Uniswap V3 : retourne 0.000270 WETH sur le palier 500 (meilleur)
    uni_quoter = MagicMock()

    def _uni_quote(params: tuple[Any, ...]) -> MagicMock:
        call = MagicMock()
        if params[3] == 500:
            # amount_in = 500_000 (0.5 USDC) -> 270_000_000_000_000 wei (0.00027 WETH)
            call.call.return_value = (params[2] * 540 * 10**6, 0, 1, 110_000)
        else:
            call.call.side_effect = ContractLogicError("execution reverted")
        return call

    uni_quoter.functions.quoteExactInputSingle.side_effect = _uni_quote
    uni_router = offline_w3.eth.contract(
        address=Web3.to_checksum_address(UNISWAP_ROUTER_ADDRESS),
        abi=UNISWAP_ROUTER_ABI,
    )
    uniswap_adapter = UniswapV3Adapter(
        web3=web3_spy,
        quoter_contract=uni_quoter,
        router_contract=uni_router,
        token_decimals=DECIMALS_MAP,
    )

    # 2. QuickSwap V3 : retourne 0.000255 WETH
    quick_quoter = MagicMock()

    def _quick_quote(t_in: str, t_out: str, amount_in: int, limit: int) -> MagicMock:
        call = MagicMock()
        call.call.return_value = (amount_in * 510 * 10**6, 100)
        return call

    quick_quoter.functions.quoteExactInputSingle.side_effect = _quick_quote
    quick_router = offline_w3.eth.contract(
        address=Web3.to_checksum_address(QUICKSWAP_ROUTER_ADDRESS),
        abi=QUICKSWAP_ROUTER_ABI,
    )
    quickswap_adapter = QuickswapAdapter(
        web3=web3_spy,
        quoter_contract=quick_quoter,
        router_contract=quick_router,
        token_decimals=DECIMALS_MAP,
    )

    # 3. SushiSwap V2 : retourne 0.000240 WETH
    sushi_router_mock = MagicMock()

    def _sushi_amounts_out(amount_in: int, path: list[str]) -> MagicMock:
        call = MagicMock()
        call.call.return_value = [amount_in, amount_in * 480 * 10**6]
        return call

    sushi_router_mock.functions.getAmountsOut.side_effect = _sushi_amounts_out
    real_sushi_router = offline_w3.eth.contract(
        address=Web3.to_checksum_address(SUSHISWAP_ROUTER_ADDRESS),
        abi=SUSHISWAP_ROUTER_ABI,
    )
    sushi_router_mock.encode_abi.side_effect = real_sushi_router.encode_abi
    sushiswap_adapter = SushiswapAdapter(
        web3=web3_spy,
        router_contract=sushi_router_mock,
        token_decimals=DECIMALS_MAP,
    )

    router = DEXRouter([uniswap_adapter, quickswap_adapter, sushiswap_adapter])
    engine = StrategyEngine(
        config_path=STRATEGY_CFG_PATH,
        dry_run=True,
        dex_router=router,
        web3_client=web3_spy,
        feature_multi_dex=True,
    )

    with patch(
        "core.strategy_engine.lire_soldes_depuis_env",
        return_value={"USDC": 100.0, "native": 5.0},
    ):
        plan = engine.run(pools=_candidate_pools())

    swap_params = plan["actions"][0]["params"]
    assert swap_params["dex"] == "uniswap_v3"
    assert Decimal(swap_params["expected_amount_out"]) == Decimal("0.00027")

    tx = swap_params["tx"]
    assert tx["to"] == Web3.to_checksum_address(UNISWAP_ROUTER_ADDRESS)
    assert tx["chainId"] == 137
    assert tx["value"] == 0
    assert isinstance(tx["data"], str) and tx["data"].startswith("0x")
    assert len(tx["data"]) > 10

    web3_spy.eth.send_raw_transaction.assert_not_called()
    web3_spy.eth.send_transaction.assert_not_called()
