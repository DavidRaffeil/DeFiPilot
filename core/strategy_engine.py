# strategy_engine.py – V4.0.1
"""Squelette du moteur de stratégie / Strategy engine skeleton.

FR: Version squelette en mode simulation (dry-run) sans dépendances internes.
EN: Skeleton version operating in dry-run only with no internal dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Any
import json
import time
from datetime import datetime


class MarketState(Enum):
    """FR: États de marché simplifiés. EN: Simplified market states."""

    FAVORABLE = "FAVORABLE"
    NEUTRE = "NEUTRE"
    DEFAVORABLE = "DEFAVORABLE"


@dataclass
class PoolCandidate:
    """FR: Candidat de pool issu des sources. EN: Pool candidate from sources."""

    pool_id: str
    platform: str
    chain: str
    symbols: str
    tvl: float
    apr: float
    score: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class Allocation:
    """FR: Allocation cible vers un pool. EN: Target allocation for a pool."""

    pool_id: str
    target_pct: float
    risk_level: str
    notes: str = ""


@dataclass
class Action:
    """FR: Action simulée du plan. EN: Simulated plan action."""

    kind: str
    params: Dict[str, Any]
    dry_run: bool = True


@dataclass
class PortfolioSnapshot:
    """FR: Instantané de portefeuille. EN: Portfolio snapshot."""

    balances: Dict[str, float]
    allowances: Dict[str, float]
    timestamp: float


class MarketWatcher(Protocol):
    """FR: Interface pour lire l'état du marché. EN: Market state reader interface."""

    def read_state(self) -> MarketState:
        """FR: Retourne l'état de marché courant. EN: Return the current market state."""
        ...


class PoolSource(Protocol):
    """FR: Interface pour lister les pools. EN: Pool listing interface."""

    def list_pools(self) -> List[PoolCandidate]:
        """FR: Liste des pools disponibles. EN: List available pools."""
        ...


class Executor(Protocol):
    """FR: Interface d'exécution. EN: Execution interface."""

    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        """FR: Exécute une séquence d'actions. EN: Execute a sequence of actions."""
        ...


class _DefaultMarketWatcher:
    """FR: Observateur neutre. EN: Neutral watcher."""

    def read_state(self) -> MarketState:
        """FR: Retourne NEUTRE. EN: Return NEUTRE."""
        return MarketState.NEUTRE


class _DefaultPoolSource:
    """FR: Source de pools vide. EN: Empty pool source."""

    def list_pools(self) -> List[PoolCandidate]:
        """FR: Aucun pool disponible. EN: No pool available."""
        return []


class _DefaultExecutor:
    """FR: Exécuteur simulation. EN: Dry-run executor."""

    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        """FR: Retourne un rapport simulé. EN: Return a simulated report."""
        return {"status": "dry-run", "executed": False, "actions": actions}


class StrategyEngine:
    """FR: Moteur de stratégie minimal orienté dry-run.
    EN: Minimal dry-run oriented strategy engine."""

    def __init__(
        self,
        config_path: str | Path,
        dry_run: bool = True,
        logger: Optional[Any] = None,
    ) -> None:
        """FR: Initialise le moteur avec config JSON. EN: Initialize engine with JSON config."""
        self.config_path = Path(config_path)
        self.dry_run = dry_run
        self.logger = logger
        self.market_watcher: MarketWatcher = _DefaultMarketWatcher()
        self.pool_source: PoolSource = _DefaultPoolSource()
        self.executor: Executor = _DefaultExecutor()
        self.cfg = self.load_config()
        self.profile = self.cfg.get("profile_default", "prudent")
        self._log_info(f"StrategyEngine initialized with profile '{self.profile}'")

    def load_config(self) -> Dict[str, Any]:
        """FR: Charge la configuration JSON. EN: Load JSON configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON configuration: {exc}") from exc
        return data

    def validate_config(self) -> None:
        """FR: Valide les champs essentiels. EN: Validate essential fields."""
        profile_default = self.cfg.get("profile_default")
        if profile_default not in {"prudent", "modere", "agressif"}:
            raise ValueError("profile_default must be one of {'prudent', 'modere', 'agressif'}")

        allocations = self.cfg.get("allocations")
        if not isinstance(allocations, dict):
            raise ValueError("allocations section must be provided as an object")

        max_concurrent = allocations.get("max_concurrent")
        if not isinstance(max_concurrent, int) or max_concurrent < 1:
            raise ValueError("allocations.max_concurrent must be an integer >= 1")

        min_pct = allocations.get("min_pct")
        max_pct = allocations.get("max_pct")
        if not isinstance(min_pct, (int, float)) or not 0 <= min_pct <= 1:
            raise ValueError("allocations.min_pct must be between 0 and 1")
        if not isinstance(max_pct, (int, float)) or not 0 <= max_pct <= 1:
            raise ValueError("allocations.max_pct must be between 0 and 1")
        if min_pct > max_pct:
            raise ValueError("allocations.min_pct must be <= allocations.max_pct")

        rebalance = self.cfg.get("rebalance")
        if not isinstance(rebalance, dict):
            raise ValueError("rebalance section must be provided as an object")

        threshold_pct = rebalance.get("threshold_pct")
        if not isinstance(threshold_pct, (int, float)) or not 0 <= threshold_pct <= 1:
            raise ValueError("rebalance.threshold_pct must be between 0 and 1")

        cooldown_minutes = rebalance.get("cooldown_minutes")
        if not isinstance(cooldown_minutes, (int, float)) or cooldown_minutes < 0:
            raise ValueError("rebalance.cooldown_minutes must be >= 0")

        market_guardrails = self.cfg.get("market_guardrails")
        if not isinstance(market_guardrails, dict):
            raise ValueError("market_guardrails section must be provided as an object")

    def snapshot_portfolio(self) -> PortfolioSnapshot:
        """FR: Retourne un snapshot neutre. EN: Return neutral snapshot."""
        balances = {"USDC": 0.0, "WETH": 0.0, "POL": 0.0}
        allowances = {"USDC": 0.0, "WETH": 0.0, "POL": 0.0}
        snapshot = PortfolioSnapshot(balances=balances, allowances=allowances, timestamp=time.time())
        self._log_info("Generated placeholder portfolio snapshot")
        return snapshot

    def detect_market_state(self) -> MarketState:
        """FR: Détecte l'état de marché. EN: Detect market state."""
        override = self.cfg.get("market_state_override")
        if isinstance(override, str):
            try:
                market = MarketState[override]
                self._log_info(f"Using market state override: {market.value}")
                return market
            except KeyError:
                self._log_warn(f"Invalid market_state_override '{override}', falling back")
        state = self.market_watcher.read_state()
        self._log_info(f"Detected market state: {state.value}")
        return state

    def select_candidates(self, pools: List[PoolCandidate]) -> List[PoolCandidate]:
        """FR: Sélectionne les meilleurs pools. EN: Select top pool candidates."""
        max_concurrent = self.cfg["allocations"]["max_concurrent"]
        if not pools:
            self._log_warn("No pools provided; selection empty")
            return []
        if any(pool.score is not None for pool in pools):
            sorted_pools = sorted(
                pools,
                key=lambda p: (p.score if p.score is not None else float("-inf"), p.apr, p.tvl),
                reverse=True,
            )
        else:
            sorted_pools = sorted(pools, key=lambda p: (p.apr, p.tvl), reverse=True)
        selected = sorted_pools[:max_concurrent]
        self._log_info(f"Selected {len(selected)} pool candidates")
        return selected

    def compute_allocations(self, candidates: List[PoolCandidate], market: MarketState) -> List[Allocation]:
        """FR: Calcule les allocations cibles. EN: Compute target allocations."""
        if not candidates:
            self._log_warn("No candidates to allocate")
            return []

        allocations_cfg = self.cfg["allocations"]
        min_pct = float(allocations_cfg["min_pct"])
        max_pct = float(allocations_cfg["max_pct"])
        n = len(candidates)
        if n == 0:
            return []

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

        guardrails = self.cfg.get("market_guardrails", {})
        guard_key = market.value
        market_guard = guardrails.get(guard_key) or guardrails.get(market.name)
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

        return allocations

    def build_actions(self, allocs: List[Allocation], snapshot: PortfolioSnapshot) -> List[Action]:
        """FR: Construit une séquence d'actions dry-run. EN: Build dry-run action plan."""
        actions: List[Action] = []
        for allocation in allocs:
            token_a = "USDC"
            token_b = f"LP-{allocation.pool_id}"
            actions.append(
                Action(
                    kind="swap",
                    params={"tokenA": token_a, "tokenB": token_b, "amountA": 0.0},
                    dry_run=True,
                )
            )
            actions.append(
                Action(
                    kind="add_liquidity",
                    params={"tokenA": token_a, "tokenB": token_b, "amountA": 0.0, "amountB": 0.0},
                    dry_run=True,
                )
            )
            actions.append(
                Action(
                    kind="stake",
                    params={"pool_id": allocation.pool_id, "amount_lp": 0.0},
                    dry_run=True,
                )
            )
        self._log_info(f"Built {len(actions)} planned actions")
        return actions

    def execute(self, actions: List[Action]) -> Dict[str, Any]:
        """FR: Exécute via l'executor. EN: Execute through executor."""
        return self.executor.execute(actions)

    def run(self, pools: Optional[List[PoolCandidate]] = None) -> Dict[str, Any]:
        """FR: Orchestration complète. EN: Full orchestration."""
        self.validate_config()
        snapshot = self.snapshot_portfolio()
        market = self.detect_market_state()
        pool_list = pools if pools is not None else self.pool_source.list_pools()
        candidates = self.select_candidates(pool_list)
        allocations = self.compute_allocations(candidates, market)
        actions = self.build_actions(allocations, snapshot)

        for action in actions:
            action.dry_run = self.dry_run

        if not self.dry_run:
            self.execute(actions)

        result = {
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
                {"kind": action.kind, "params": action.params, "dry_run": action.dry_run} for action in actions
            ],
            "dry_run": self.dry_run,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        self._log_info("Strategy run completed")
        return result

    def _log_info(self, message: str) -> None:
        """FR: Log niveau info. EN: Info level logging."""
        if self.logger and hasattr(self.logger, "info"):
            self.logger.info(message)
        else:
            print(f"[INFO] {message}")

    def _log_warn(self, message: str) -> None:
        """FR: Log niveau avertissement. EN: Warning level logging."""
        if self.logger and hasattr(self.logger, "warning"):
            self.logger.warning(message)
        else:
            print(f"[WARN] {message}")


if __name__ == "__main__":
    try:
        engine = StrategyEngine(config_path="strategy_config.json", dry_run=True)
        plan = engine.run()
        print(json.dumps(plan, indent=2))
    except FileNotFoundError as err:
        print(f"Configuration introuvable / not found: {err}")
    except ValueError as err:
        print(f"Configuration invalide / invalid: {err}")