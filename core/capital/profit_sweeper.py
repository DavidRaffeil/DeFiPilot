# core/capital/profit_sweeper.py – Phase 2.1 : Sécurisation automatique des gains
"""Détecte un profit net et calcule la part à isoler vers un stablecoin safe-haven.

Le module est pur (aucune I/O réseau). En mode dry-run, il ne produit qu'un plan
simulé ; un ordre réel n'est transmis à l'exécuteur injecté que si dry-run est
désactivé explicitement.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Any, Callable, Mapping, Optional

logger = logging.getLogger(__name__)

_CENT = Decimal("0.000001")


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


@dataclass(frozen=True)
class SweepConfig:
    enabled: bool = True
    profit_threshold_usd: Decimal = Decimal("1.0")
    sweep_pct: Decimal = Decimal("0.5")  # fraction du profit net (0 < x <= 1)
    target_asset: str = "USDC"

    @classmethod
    def from_mapping(cls, cfg: Mapping[str, Any]) -> "SweepConfig":
        sweep_pct = _dec(cfg.get("sweep_pct", "0.5"))
        threshold = _dec(cfg.get("profit_threshold_usd", "1.0"))
        if not (Decimal("0") < sweep_pct <= Decimal("1")):
            raise ValueError("sweep_pct doit être dans ]0, 1]")
        if threshold < 0:
            raise ValueError("profit_threshold_usd doit être >= 0")
        return cls(
            enabled=bool(cfg.get("enabled", True)),
            profit_threshold_usd=threshold,
            sweep_pct=sweep_pct,
            target_asset=str(cfg.get("target_asset", "USDC")),
        )


@dataclass(frozen=True)
class SweepResult:
    triggered: bool
    net_profit: Decimal
    amount: Decimal
    target_asset: str
    dry_run: bool
    executed: bool
    reason: str


class ProfitSweeper:
    """Calcule et (hors dry-run) délègue le prélèvement des gains."""

    def __init__(
        self,
        config: Mapping[str, Any],
        dry_run: bool = True,
        executor: Optional[Callable[[Decimal, str], Any]] = None,
    ) -> None:
        self.config = SweepConfig.from_mapping(config)
        self.dry_run = bool(dry_run)  # sécurisé par défaut
        self._executor = executor

    def net_profit(self, current_value: Any, reference_capital: Any) -> Decimal:
        return _dec(current_value) - _dec(reference_capital)

    def compute_sweep_amount(self, net_profit: Decimal) -> Decimal:
        return (net_profit * self.config.sweep_pct).quantize(_CENT, rounding=ROUND_DOWN)

    def evaluate(self, current_value: Any, reference_capital: Any) -> SweepResult:
        cfg = self.config
        profit = self.net_profit(current_value, reference_capital)

        def skip(reason: str) -> SweepResult:
            return SweepResult(False, profit, Decimal("0"), cfg.target_asset,
                               self.dry_run, False, reason)

        if not cfg.enabled:
            return skip("disabled")
        if profit <= 0:
            return skip("no_profit")
        if profit < cfg.profit_threshold_usd:
            return skip("below_threshold")

        amount = self.compute_sweep_amount(profit)
        if amount <= 0:
            return skip("amount_zero")

        if self.dry_run:
            logger.info("[DRY-RUN] Sweep simulé de %s %s (profit net %s)",
                        amount, cfg.target_asset, profit)
            return SweepResult(True, profit, amount, cfg.target_asset, True, False, "dry_run")

        if self._executor is None:
            logger.warning("Sweep réel demandé sans exécuteur : aucun ordre envoyé.")
            return SweepResult(True, profit, amount, cfg.target_asset, False, False, "no_executor")

        self._executor(amount, cfg.target_asset)
        return SweepResult(True, profit, amount, cfg.target_asset, False, True, "executed")
