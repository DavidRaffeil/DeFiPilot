# core/capital/compounding.py – Phase 2.2 : Gain composé dégressif temporel
"""Taux de réinvestissement dégressif selon le temps passé dans une pool.

Jour 0 : taux initial (agressif). Chaque jour entier écoulé retire
`daily_decay_pct`, avec un plancher `min_reinvest_pct`. Un changement de
`pool_id` remet l'horloge à zéro. Module pur, uniquement des Decimal.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from typing import Any, Dict, Mapping, Optional

_QUANT = Decimal("0.000001")
_SECONDS_PER_DAY = Decimal("86400")


def _dec(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


@dataclass(frozen=True)
class CompoundingConfig:
    enabled: bool = True
    initial_reinvest_pct: Decimal = Decimal("1.0")
    daily_decay_pct: Decimal = Decimal("0.05")
    min_reinvest_pct: Decimal = Decimal("0.20")

    @classmethod
    def from_mapping(cls, cfg: Mapping[str, Any]) -> "CompoundingConfig":
        initial = _dec(cfg.get("initial_reinvest_pct", "1.0"))
        decay = _dec(cfg.get("daily_decay_pct", "0.05"))
        floor = _dec(cfg.get("min_reinvest_pct", "0.20"))
        one = Decimal("1")
        if not (Decimal("0") <= floor <= initial <= one):
            raise ValueError("Il faut 0 <= min_reinvest_pct <= initial_reinvest_pct <= 1")
        if decay < 0:
            raise ValueError("daily_decay_pct doit être >= 0")
        return cls(
            enabled=bool(cfg.get("enabled", True)),
            initial_reinvest_pct=initial,
            daily_decay_pct=decay,
            min_reinvest_pct=floor,
        )


class TimeDecayCompounder:
    """Calcule le taux de réinvestissement et la répartition du profit."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.config = CompoundingConfig.from_mapping(config)
        self.pool_id: Optional[str] = None
        self.entry_timestamp: Optional[Decimal] = None

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def get_reinvestment_rate(self, current_timestamp: Any, pool_id: str) -> Decimal:
        cfg = self.config
        now = _dec(current_timestamp)

        if pool_id != self.pool_id or self.entry_timestamp is None:
            self.pool_id = pool_id
            self.entry_timestamp = now
            return cfg.initial_reinvest_pct

        elapsed = now - self.entry_timestamp
        days = max(0, int(elapsed / _SECONDS_PER_DAY))
        rate = cfg.initial_reinvest_pct - (Decimal(days) * cfg.daily_decay_pct)
        return max(cfg.min_reinvest_pct, rate)

    def calculate_allocation(
        self, profit_amount: Any, current_timestamp: Any, pool_id: str
    ) -> Dict[str, Decimal]:
        profit = _dec(profit_amount)
        rate = self.get_reinvestment_rate(current_timestamp, pool_id)
        reinvest = (profit * rate).quantize(_QUANT, rounding=ROUND_DOWN)
        return {
            "rate": rate,
            "reinvest_amount": reinvest,
            "secured_amount": profit - reinvest,
        }
