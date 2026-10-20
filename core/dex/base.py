# core/dex/base.py – V6.5.0
"""
Interface abstraite et modèles de données pour les adaptateurs DEX (Multi-DEX).

Aucun float n'est autorisé pour les montants : tout est en Decimal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping


def _deep_freeze(value: Any) -> Any:
    """Copie récursive en lecture seule : dict -> MappingProxyType, list/set -> tuple/frozenset."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: _deep_freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_deep_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class DEXQuote:
    """
    Cotation immuable d'un swap sur un DEX donné.

    `raw_quote_data` contient les données spécifiques au protocole
    nécessaires à l'exécution ultérieure (route, fee tier, deadline, ...).
    Il est copié puis figé (lecture seule, récursif) à la construction.
    """

    dex_name: str
    token_in: str
    token_out: str
    amount_in: Decimal
    expected_amount_out: Decimal
    min_amount_out: Decimal
    price_impact_pct: Decimal
    estimated_gas: int
    raw_quote_data: Mapping[str, Any] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        for name in ("dex_name", "token_in", "token_out"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"{name} doit être de type str")

        for name in (
            "amount_in",
            "expected_amount_out",
            "min_amount_out",
            "price_impact_pct",
        ):
            value = getattr(self, name)
            if isinstance(value, float) or not isinstance(value, Decimal):
                raise TypeError(f"{name} doit être de type Decimal (float interdit)")
            if not value.is_finite():
                raise ValueError(f"{name} doit être fini")

        # bool est une sous-classe de int : on l'exclut explicitement
        if isinstance(self.estimated_gas, bool) or not isinstance(self.estimated_gas, int):
            raise TypeError("estimated_gas doit être de type int")
        if not isinstance(self.raw_quote_data, Mapping):
            raise TypeError("raw_quote_data doit être un dict (Mapping)")

        if not self.dex_name:
            raise ValueError("dex_name ne peut pas être vide")
        if self.amount_in <= 0:
            raise ValueError("amount_in doit être strictement positif")
        if self.expected_amount_out < 0:
            raise ValueError("expected_amount_out ne peut pas être négatif")
        if self.min_amount_out < 0:
            raise ValueError("min_amount_out ne peut pas être négatif")
        if self.min_amount_out > self.expected_amount_out:
            raise ValueError("min_amount_out ne peut pas dépasser expected_amount_out")
        if self.estimated_gas < 0:
            raise ValueError("estimated_gas ne peut pas être négatif")

        # Copie figée : l'appelant ne peut plus muter la cotation via son dict d'origine
        object.__setattr__(self, "raw_quote_data", _deep_freeze(self.raw_quote_data))


class BaseDEXAdapter(ABC):
    """Contrat commun à tous les adaptateurs DEX."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom unique du DEX (ex. 'quickswap')."""

    @abstractmethod
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal,
    ) -> DEXQuote:
        """Retourne une cotation pour le swap demandé."""

    @abstractmethod
    async def build_swap_transaction(self, quote: DEXQuote, recipient: str) -> dict:
        """Construit la transaction (non signée) correspondant à la cotation."""
