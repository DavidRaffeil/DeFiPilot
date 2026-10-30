# core/strategy_engine.py – V6.5
"""Moteur de stratégie DeFiPilot V6.0 / V6.5.

Centralise l'analyse des opportunités (DeFiLlama), le calcul du score
effectif selon le profil de risque et le contexte IA, et génère le plan d'action
avec support optionnel du routage Multi-DEX (DEXRouter).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Protocol

import core.config as app_config
from core.defi_sources.defillama import recuperer_pools
from core.dex.factory import create_default_dex_router
from core.dex.router import DEXRouter
from core.execution.gas_tank import GasTankManager
from core.real_wallet import get_wallet_address
from core.swap_reel import (
    DEFAULT_SWAP_RECIPIENT,
    _run_coro_sync,
    resolve_token_address,
)
from core.wallet_reader import lire_soldes_depuis_env, verifier_fonds_disponibles
from .strategy_context import StrategyContext

_module_logger = logging.getLogger("core.strategy_engine")


class MarketState(Enum):
    FAVORABLE = "FAVORABLE"
    NEUTRE = "NEUTRE"
    DEFAVORABLE = "DEFAVORABLE"


@dataclass
class PoolCandidate:
    pool_id: str
    platform: str
    chain: str
    symbols: str
    tvl: float
    apr: float
    score: Optional[float] = None
    metadata: Dict[str, Any] | None = None


@dataclass
class Allocation:
    pool_id: str
    target_pct: float
    risk_level: str
    notes: str = ""


@dataclass
class Action:
    kind: str
    params: Dict[str, Any]
    dry_run: bool = True


@dataclass
class PortfolioSnapshot:
    balances: Dict[str, float]
    allowances: Dict[str, float]
    timestamp: float


class MarketWatcher(Protocol):
    def read_state(self) -> MarketState:
        ...


class PoolSource(Protocol):
    def list_pools(self) -> List[PoolCandidate]:
        ...


class Executor(Protocol):
    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        ...


class _DefaultMarketWatcher:
    def read_state(self) -> MarketState:
        return MarketState.NEUTRE


class _DefaultPoolSource:
    def __init__(self, min_tvl: float = 100000) -> None:
        self.min_tvl = float(min_tvl)

    def list_pools(self) -> List[PoolCandidate]:
        raw_pools = recuperer_pools()
        pools = []
        for p in raw_pools:
            tvl = float(p.get("tvl", p.get("tvl_usd", 0)))
            if tvl < self.min_tvl:
                continue

            pools.append(
                PoolCandidate(
                    pool_id=str(p.get("pool_id", p.get("nom", ""))),
                    platform=str(p.get("platform", p.get("plateforme", ""))),
                    chain=str(p.get("chain", "unknown")),
                    symbols=str(p.get("symbols", p.get("nom", ""))),
                    tvl=tvl,
                    apr=float(p.get("apr", 0)),
                )
            )
        return pools


class _DefaultExecutor:
    def __init__(
        self,
        dex_router: Optional[DEXRouter] = None,
        web3_client: Optional[Any] = None,
        feature_multi_dex: Optional[bool] = None,
    ) -> None:
        self.dex_router = dex_router
        self.web3_client = web3_client
        self.feature_multi_dex = feature_multi_dex

    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        from core.executor_real import executer_action_reelle

        results = []
        for action in actions:
            result = executer_action_reelle(
                {"kind": action.kind, "params": action.params, "dry_run": action.dry_run},
                run_id="defipilot_run",
                dex_router=self.dex_router,
                web3_client=self.web3_client,
                feature_multi_dex=self.feature_multi_dex,
            )
            results.append(result)
        return {"status": "executed", "executed": True, "results": results}


class StrategyEngine:
    """Moteur de stratégie DeFiPilot V6.0 / V6.5."""

    def __init__(
        self,
        config_path: str | Path,
        dry_run: bool = True,
        logger: Optional[Any] = None,
        dex_router: Optional[DEXRouter] = None,
        web3_client: Optional[Any] = None,
        feature_multi_dex: Optional[bool] = None,
        gas_tank: Optional[GasTankManager] = None,
        wallet_address: Optional[str] = None,
    ) -> None:
        self.config_path = Path(config_path)
        self.dry_run = dry_run
        self.logger = logger
        self.web3_client = web3_client
        self._feature_multi_dex_override = feature_multi_dex
        self.market_watcher: MarketWatcher = _DefaultMarketWatcher()

        self.cfg = self.load_config()

        self.gas_tank: Optional[GasTankManager] = gas_tank
        if self.gas_tank is None and self.web3_client is not None:
            has_numeric_balance = False
            if hasattr(self.web3_client, "eth"):
                try:
                    probe = (
                        wallet_address
                        or get_wallet_address()
                        or os.environ.get("WALLET_ADDRESS")
                        or DEFAULT_SWAP_RECIPIENT
                    )
                    bal = self.web3_client.eth.get_balance(probe)
                    has_numeric_balance = isinstance(bal, (int, float, Decimal))
                except Exception:
                    has_numeric_balance = False
            elif hasattr(self.web3_client, "execute_call"):
                has_numeric_balance = True

            if has_numeric_balance:
                target_wallet = (
                    wallet_address
                    or get_wallet_address()
                    or os.environ.get("WALLET_ADDRESS")
                    or DEFAULT_SWAP_RECIPIENT
                )
                self.gas_tank = GasTankManager(
                    web3_client=self.web3_client,
                    wallet_address=target_wallet,
                    dry_run=self.dry_run,
                )

        self.dex_router: Optional[DEXRouter] = dex_router
        if self.dex_router is None and self.is_multi_dex_enabled() and self.web3_client is not None:
            try:
                self.dex_router = create_default_dex_router(self.web3_client)
            except Exception as exc:
                self._log_warn(
                    f"[MULTI-DEX] Impossible d'initialiser le DEXRouter par défaut : {exc}"
                )
                self.dex_router = None

        self.executor: Executor = _DefaultExecutor(
            dex_router=self.dex_router,
            web3_client=self.web3_client,
            feature_multi_dex=self._feature_multi_dex_override,
        )

        min_tvl = self.cfg.get("market_guardrails", {}).get("min_tvl_usd", 100000)
        self.pool_source: PoolSource = _DefaultPoolSource(min_tvl=min_tvl)
        self.profile = self.cfg.get("profile_default", "prudent")
        self._log_info(f"StrategyEngine V6.0 initialisé avec le profil '{self.profile}'")

    def is_multi_dex_enabled(self) -> bool:
        """Indique si le routage Multi-DEX est actif."""
        if self._feature_multi_dex_override is not None:
            return bool(self._feature_multi_dex_override)
        if isinstance(getattr(self, "cfg", None), dict) and "feature_multi_dex" in self.cfg:
            return bool(self.cfg["feature_multi_dex"])
        return bool(app_config.FEATURE_MULTI_DEX)

    def load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Fichier de configuration introuvable: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON de configuration invalide: {exc}") from exc
        return data

    def validate_config(self) -> None:
        profile_default = self.cfg.get("profile_default")
        if profile_default not in {"prudent", "modere", "agressif"}:
            raise ValueError("profile_default doit être 'prudent', 'modere' ou 'agressif'")

        allocations = self.cfg.get("allocations")
        if not isinstance(allocations, dict):
            raise ValueError("La section 'allocations' doit être un objet")

        max_concurrent = allocations.get("max_concurrent")
        if not isinstance(max_concurrent, int) or max_concurrent < 1:
            raise ValueError("allocations.max_concurrent doit être un entier >= 1")

        min_pct = allocations.get("min_pct")
        max_pct = allocations.get("max_pct")
        if not isinstance(min_pct, (int, float)) or not 0 <= min_pct <= 1:
            raise ValueError("allocations.min_pct doit être entre 0 et 1")
        if not isinstance(max_pct, (int, float)) or not 0 <= max_pct <= 1:
            raise ValueError("allocations.max_pct doit être entre 0 et 1")
        if min_pct > max_pct:
            raise ValueError("allocations.min_pct doit être <= allocations.max_pct")

        rebalance = self.cfg.get("rebalance")
        if not isinstance(rebalance, dict):
            raise ValueError("La section 'rebalance' doit être un objet")

    def snapshot_portfolio(self) -> PortfolioSnapshot:
        balances = {"USDC": 0.0, "WETH": 0.0, "POL": 0.0}
        allowances = {"USDC": 0.0, "WETH": 0.0, "POL": 0.0}
        snapshot = PortfolioSnapshot(balances=balances, allowances=allowances, timestamp=time.time())
        return snapshot

    def detect_market_state(self) -> MarketState:
        override = self.cfg.get("market_state_override")
        if isinstance(override, str):
            try:
                market = MarketState[override]
                self._log_info(f"Utilisation de l'état de marché forcé : {market.value}")
                return market
            except KeyError:
                self._log_warn(f"Override de marché invalide '{override}', repli sur l'observateur")
        state = self.market_watcher.read_state()
        return state

    def _compute_effective_score(
        self,
        pool: PoolCandidate,
        context: Optional[StrategyContext],
    ) -> float:
        if pool.score is not None:
            return float(pool.score)

        base_apr = float(pool.apr)
        base_tvl = float(pool.tvl)
        tvl_factor = base_tvl / 1e9 if base_tvl > 0 else 0.0

        if context is None:
            return base_apr + tvl_factor

        label = context.label
        if label == "favorable":
            return base_apr * 1.0 + tvl_factor * 0.5
        if label == "defavorable":
            return base_apr * 0.6 + tvl_factor * 0.4
        return base_apr * 0.8 + tvl_factor * 0.2

    def select_candidates(
        self,
        pools: List[PoolCandidate],
        context: Optional[StrategyContext] = None,
    ) -> List[PoolCandidate]:
        max_concurrent = self.cfg.get("allocations", {}).get("max_concurrent", 1)
        if not pools:
            self._log_warn("Aucune pool fournie ; sélection vide")
            return []

        # Filtrage par la liste blanche des paires de trading si configurée
        trading_pairs = self.cfg.get("trading_pairs")
        if isinstance(trading_pairs, list) and trading_pairs:
            allowed_norm = {p.upper().replace("/", "-").replace("_", "-") for p in trading_pairs}
            filtered_pools = []
            for p in pools:
                sym_norm = p.symbols.upper().replace("/", "-").replace("_", "-")
                pid_norm = p.pool_id.upper().replace("/", "-").replace("_", "-")
                if any(pair in sym_norm or pair in pid_norm or sym_norm in pair for pair in allowed_norm):
                    filtered_pools.append(p)
            pools = filtered_pools
            if not pools:
                self._log_warn("Aucune pool ne correspond à la liste blanche trading_pairs")
                return []

        if any(pool.score is not None for pool in pools):
            sorted_pools = sorted(
                pools,
                key=lambda p: (p.score if p.score is not None else float("-inf"), p.apr, p.tvl),
                reverse=True,
            )
        else:
            sorted_pools = sorted(
                pools,
                key=lambda p: self._compute_effective_score(p, context),
                reverse=True,
            )

        selected = sorted_pools[:max_concurrent]
        self._log_info(f"Sélection de {len(selected)} pools candidates (filtrées par trading_pairs)")
        return selected

    def _compute_exposure_factor(self, context: Optional[StrategyContext]) -> float:
        if context is None:
            return 1.0

        label = getattr(context, "label", "neutre") or "neutre"
        label = label.lower()
        if label not in {"favorable", "neutre", "defavorable"}:
            label = "neutre"

        exposure_table: Dict[str, Dict[str, float]] = {
            "prudent": {"favorable": 1.0, "neutre": 0.9, "defavorable": 0.7},
            "modere": {"favorable": 1.0, "neutre": 1.0, "defavorable": 0.8},
            "agressif": {"favorable": 1.1, "neutre": 1.0, "defavorable": 0.9},
        }

        profile_table = exposure_table.get(self.profile)
        if profile_table is None:
            return 1.0
        return profile_table.get(label, 1.0)

    def compute_allocations(
        self,
        candidates: List[PoolCandidate],
        market: MarketState,
        context: Optional[StrategyContext] = None,
    ) -> List[Allocation]:
        if not candidates:
            return []

        allocations_cfg = self.cfg["allocations"]
        min_pct = float(allocations_cfg["min_pct"])
        max_pct = float(allocations_cfg["max_pct"])
        n = len(candidates)

        uniform_share = 1.0 / n if n else 0.0
        base_share = max(min(uniform_share, max_pct), min_pct)

        allocations: List[Allocation] = []
        for candidate in candidates:
            allocations.append(
                Allocation(
                    pool_id=candidate.pool_id,
                    target_pct=base_share,
                    risk_level=self.profile,
                )
            )

        total = sum(a.target_pct for a in allocations)
        if total > 1.0:
            for allocation in allocations:
                allocation.target_pct /= total

        # Ajustement barrières de sécurité marché
        guardrails = self.cfg.get("market_guardrails", {})
        market_guard = guardrails.get(market.value) or guardrails.get(market.name)
        risk_caps: Dict[str, float] = {}
        if isinstance(market_guard, dict):
            caps = market_guard.get("risk_caps")
            if isinstance(caps, dict):
                risk_caps = {str(k): float(v) for k, v in caps.items() if isinstance(v, (int, float))}

        adjusted = False
        for allocation in allocations:
            cap = risk_caps.get(allocation.risk_level)
            if cap is not None and allocation.target_pct > cap:
                allocation.target_pct = cap
                adjusted = True

        if adjusted:
            total_after = sum(a.target_pct for a in allocations)
            if total_after > 1.0 and total_after > 0:
                for allocation in allocations:
                    allocation.target_pct /= total_after

        exposure_factor = self._compute_exposure_factor(context)
        if exposure_factor != 1.0:
            for allocation in allocations:
                allocation.target_pct *= exposure_factor

            total_after = sum(a.target_pct for a in allocations)
            if total_after > 1.0 and total_after > 0:
                for allocation in allocations:
                    allocation.target_pct /= total_after

        return allocations

    def prepare_swap_action(
        self,
        token_a: str,
        token_b: str,
        swap_amount: float | Decimal,
        max_slippage: float = 1.0,
        dry_run: bool = True,
        recipient: Optional[str] = None,
    ) -> Action:
        """
        Prépare une action de swap.

        Si `FEATURE_MULTI_DEX` est actif et que `dex_router` est disponible :
        - interroge `dex_router.get_best_quote(...)`
        - journalise le DEX retenu et le montant espéré
        - construit la transaction avec l'adaptateur sélectionné.
        En cas d'exception ou si le feature flag est désactivé, bascule de manière
        transparente sur le comportement unitaire préexistant.
        """
        params: Dict[str, Any] = {
            "tokenA": token_a,
            "tokenB": token_b,
            "amountA": float(swap_amount),
            "max_slippage_pct": max_slippage,
        }

        if self.is_multi_dex_enabled() and self.dex_router is not None:
            try:
                token_in_addr = resolve_token_address(token_a)
                token_out_addr = resolve_token_address(token_b)
                amount_in_dec = Decimal(str(swap_amount))
                slippage_dec = Decimal(str(max_slippage)) / Decimal("100")

                best_quote = _run_coro_sync(
                    self.dex_router.get_best_quote(
                        token_in=token_in_addr,
                        token_out=token_out_addr,
                        amount_in=amount_in_dec,
                        slippage_tolerance=slippage_dec,
                    )
                )
                log_msg = (
                    f"[MULTI-DEX] DEX retenu : {best_quote.dex_name} | "
                    f"Montant espéré : {best_quote.expected_amount_out} {token_b} "
                    f"(min: {best_quote.min_amount_out}, gas: {best_quote.estimated_gas})"
                )
                self._log_info(log_msg)
                _module_logger.info(log_msg)

                target_recipient = (
                    recipient
                    or os.environ.get("WALLET_ADDRESS")
                    or DEFAULT_SWAP_RECIPIENT
                )
                tx = _run_coro_sync(
                    self.dex_router.build_swap_transaction(best_quote, target_recipient)
                )

                params["dex"] = best_quote.dex_name
                params["expected_amount_out"] = str(best_quote.expected_amount_out)
                params["min_amount_out"] = str(best_quote.min_amount_out)
                params["estimated_gas"] = best_quote.estimated_gas
                params["tx"] = tx
            except Exception as exc:
                warn_msg = (
                    f"[MULTI-DEX] Échec du routage multi-DEX ({exc}), "
                    "repli sur le comportement de swap unitaire par défaut"
                )
                self._log_warn(warn_msg)
                _module_logger.warning(warn_msg)

        return Action(kind="swap", params=params, dry_run=dry_run)

    def build_actions(self, allocs: List[Allocation], snapshot: PortfolioSnapshot) -> List[Action]:
        actions: List[Action] = []
        max_slippage = float(self.cfg.get("max_slippage_pct", 1.0))
        for allocation in allocs:
            invest_amount = float(self.cfg.get("capital_initial_usdc", 5.0))
            if invest_amount < 0.5:
                self._log_warn("Capital trop faible pour investir")
                return []

            swap_amount = invest_amount / 2
            tokens = allocation.pool_id.split("-")
            if len(tokens) != 2:
                continue

            token_a, token_b = tokens[0], tokens[1]
            besoins = {token_a: swap_amount, "native": 0.01}

            soldes = lire_soldes_depuis_env(
                tokens={
                    "USDC": {
                        "address": "0x3c499c542cEF5E3811e1192ce70d8cc03d5c3359",
                        "decimals": 6,
                    }
                }
            )

            ok, token_manquant = verifier_fonds_disponibles(soldes, besoins)
            if not ok:
                self._log_warn(f"Fonds insuffisants pour {token_manquant}")
                continue

            swap_action = self.prepare_swap_action(
                token_a=token_a,
                token_b=token_b,
                swap_amount=swap_amount,
                max_slippage=max_slippage,
                dry_run=True,
            )
            actions.append(swap_action)
            actions.append(
                Action(
                    kind="add_liquidity",
                    params={
                        "tokenA": token_a,
                        "tokenB": token_b,
                        "amountA": swap_amount,
                        "amountB": 0.0,
                    },
                    dry_run=True,
                )
            )
            actions.append(
                Action(
                    kind="stake",
                    params={"pool_id": allocation.pool_id, "amount_lp": invest_amount},
                    dry_run=True,
                )
            )

        return actions

    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        return self.executor.execute(actions)

    def run(
        self,
        pools: Optional[List[PoolCandidate]] = None,
        context: Optional[StrategyContext] = None,
    ) -> Dict[str, Any]:
        """Orchestration V6.0 sans plantage si liste vide et rechargement dynamique."""
        self.cfg = self.load_config()
        self.validate_config()
        self.profile = self.cfg.get("profile_default", "prudent")
        snapshot = self.snapshot_portfolio()

        market = self.detect_market_state()

        # =====================================================================
        # CONTRÔLE DE CARBURANT PRÉ-CYCLE (GasTank - Phase 4 / V6.6)
        # =====================================================================
        gas_refuel_status: Optional[Dict[str, Any]] = None
        if self.gas_tank is not None:
            try:
                gas_refuel_status = self.gas_tank.check_and_refuel()
            except Exception as exc:
                self._log_warn(f"[GAS TANK] Échec de check_and_refuel pré-cycle : {exc}")

            simulated_refuel_ok = (
                self.dry_run
                and isinstance(gas_refuel_status, dict)
                and gas_refuel_status.get("action") == "simulated_unwrap"
            )
            if not simulated_refuel_ok and self.gas_tank.is_gas_critical():
                warn_msg = (
                    "[GAS CRITICAL] Solde de gas natif (POL) sous le seuil critique : "
                    "suspension de la génération de nouveaux signaux d'action pour ce cycle."
                )
                self._log_warn(warn_msg)
                _module_logger.warning(warn_msg)
                return {
                    "profile": self.profile,
                    "market": market.value,
                    "status": "suspended_gas_critical",
                    "reason": "gas_critical",
                    "actions": [],
                    "dry_run": self.dry_run,
                    "gas_refuel": gas_refuel_status,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                }

        pool_list = pools if pools is not None else self.pool_source.list_pools()
        candidates = self.select_candidates(pool_list, context=context)

        # FIX DU BUG CRITIQUE : Retour propre si aucune pool
        if not candidates:
            self._log_warn("Aucune pool candidate valide, arrêt propre du cycle.")
            return {
                "profile": self.profile,
                "market": market.value,
                "status": "stopped_no_candidates",
                "actions": [],
                "dry_run": self.dry_run,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

        allocations = self.compute_allocations(candidates, market, context=context)
        actions = self.build_actions(allocations, snapshot)

        # Si on n'est pas en dry_run global, on bascule les actions en réel
        if not self.dry_run:
            for action in actions:
                action.dry_run = False

        execution_result = self.execute(actions)

        # =====================================================================
        # GESTION DU SURPLUS DE GAS EN FIN DE CYCLE (Auto-Wrap POL -> WPOL)
        # =====================================================================
        excess_gas_sweep: Optional[Dict[str, Any]] = None
        if self.gas_tank is not None:
            try:
                excess_gas_sweep = self.gas_tank.check_and_sweep_excess_gas()
                if excess_gas_sweep.get("action") == "WRAPPED_EXCESS":
                    sweep_msg = (
                        f"[GAS TANK] Excédent de POL converti en WPOL en fin de cycle : "
                        f"amount={excess_gas_sweep.get('amount')} POL (tx={excess_gas_sweep.get('tx_hash')})"
                    )
                    self._log_info(sweep_msg)
                    _module_logger.info(sweep_msg)
            except Exception as exc:
                self._log_warn(
                    f"[GAS TANK] Échec de check_and_sweep_excess_gas en fin de cycle : {exc}"
                )

        result: Dict[str, Any] = {
            "profile": self.profile,
            "market": market.value,
            "snapshot": {
                "balances": snapshot.balances,
                "allowances": snapshot.allowances,
                "timestamp": snapshot.timestamp,
            },
            "candidates": [candidate.__dict__ for candidate in candidates],
            "allocations": [allocation.__dict__ for allocation in allocations],
            "actions": [
                {"kind": action.kind, "params": action.params, "dry_run": action.dry_run}
                for action in actions
            ],
            "execution_output": execution_result,
            "dry_run": self.dry_run,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "context": {
                "label": context.label,
                "ai_score": context.ai_score,
                "confiance": context.confiance,
            }
            if context is not None
            else None,
        }
        if gas_refuel_status is not None:
            result["gas_refuel"] = gas_refuel_status
        if excess_gas_sweep is not None:
            result["excess_gas_sweep"] = excess_gas_sweep
        self._log_info("Cycle d'exécution StrategyEngine terminé.")
        return result

    def _log_info(self, message: str) -> None:
        if self.logger and hasattr(self.logger, "info"):
            self.logger.info(message)
        else:
            print(f"[INFO] {message}")

    def _log_warn(self, message: str) -> None:
        if self.logger and hasattr(self.logger, "warning"):
            self.logger.warning(message)
        else:
            print(f"[WARN] {message}")


if __name__ == "__main__":
    try:
        # Cible le fichier V6 par défaut pour les tests
        engine = StrategyEngine(config_path="config/strategy_v6_0.json", dry_run=True)
        plan = engine.run()
        print(json.dumps(plan, indent=2))
    except FileNotFoundError as err:
        print(f"Configuration introuvable : {err}")
    except ValueError as err:
        print(f"Configuration invalide : {err}")
