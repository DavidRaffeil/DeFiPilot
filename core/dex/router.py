# core/dex/router.py – V6.5.0
"""
Routeur et comparateur multi-DEX (DEXRouter).

Interroge plusieurs adaptateurs DEX en parallèle, isole les pannes ou timeouts
individuels, et sélectionne la meilleure route selon `expected_amount_out`
(puis `estimated_gas` le plus faible en cas d'égalité stricte).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from core.dex.base import BaseDEXAdapter, DEXQuote
from core.dex.exceptions import DEXError, DEXTransactionError, NoValidRouteError


@dataclass
class RouteComparisonResult:
    """Résultat d'une comparaison de cotations multi-DEX."""

    best_quote: DEXQuote
    all_quotes: list[DEXQuote] = field(default_factory=list)
    failed_dexes: dict[str, str] = field(default_factory=dict)


class DEXRouter:
    """
    Agrégateur / comparateur de routes multi-DEX.

    Args:
        adapters: liste des adaptateurs DEX à interroger.
        default_timeout: délai maximum (en secondes) accordé à chaque adaptateur
            lors d'une demande de cotation.
    """

    def __init__(
        self,
        adapters: list[BaseDEXAdapter],
        default_timeout: float = 3.0,
    ) -> None:
        if not isinstance(adapters, list) or not adapters:
            raise ValueError("adapters doit être une liste non vide d'adaptateurs DEX")
        for adapter in adapters:
            if not isinstance(adapter, BaseDEXAdapter):
                raise TypeError(
                    f"Chaque adaptateur doit hériter de BaseDEXAdapter, reçu : {type(adapter)!r}"
                )
        if (
            isinstance(default_timeout, bool)
            or not isinstance(default_timeout, (int, float))
            or default_timeout <= 0
        ):
            raise ValueError("default_timeout doit être un nombre strictement positif")

        self._adapters: list[BaseDEXAdapter] = list(adapters)
        self._adapters_by_name: dict[str, BaseDEXAdapter] = {}
        for adapter in self._adapters:
            if adapter.name in self._adapters_by_name:
                raise ValueError(f"Adaptateur DEX en doublon : {adapter.name!r}")
            self._adapters_by_name[adapter.name] = adapter

        self._default_timeout: float = float(default_timeout)

    @property
    def adapters(self) -> list[BaseDEXAdapter]:
        """Retourne la copie de la liste des adaptateurs enregistrés."""
        return list(self._adapters)

    @property
    def default_timeout(self) -> float:
        """Timeout par défaut (en secondes) pour chaque cotation."""
        return self._default_timeout

    async def get_quotes(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal,
    ) -> RouteComparisonResult:
        """
        Interroge tous les adaptateurs DEX en parallèle et compare leurs cotations.

        Raises:
            NoValidRouteError: si aucun adaptateur ne retourne de cotation valide.
        """
        tasks = [
            asyncio.wait_for(
                adapter.get_quote(
                    token_in=token_in,
                    token_out=token_out,
                    amount_in=amount_in,
                    slippage_tolerance=slippage_tolerance,
                ),
                timeout=self._default_timeout,
            )
            for adapter in self._adapters
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_quotes: list[DEXQuote] = []
        failed_dexes: dict[str, str] = {}

        for adapter, result in zip(self._adapters, results, strict=True):
            if isinstance(result, BaseException):
                if isinstance(result, asyncio.CancelledError):
                    raise result
                error_msg = str(result).strip()
                if not error_msg:
                    if isinstance(result, TimeoutError):
                        error_msg = f"Timeout après {self._default_timeout}s"
                    else:
                        error_msg = result.__class__.__name__
                failed_dexes[adapter.name] = error_msg
            elif isinstance(result, DEXQuote):
                valid_quotes.append(result)
            else:
                failed_dexes[adapter.name] = (
                    f"Réponse invalide de type {type(result).__name__}"
                )

        if not valid_quotes:
            raise NoValidRouteError(
                f"Aucune route valide pour {token_in} -> {token_out}. "
                f"Échecs : {failed_dexes}"
            )

        best_quote = max(
            valid_quotes,
            key=lambda q: (q.expected_amount_out, -q.estimated_gas),
        )

        return RouteComparisonResult(
            best_quote=best_quote,
            all_quotes=valid_quotes,
            failed_dexes=failed_dexes,
        )

    async def get_best_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal,
    ) -> DEXQuote:
        """Retourne directement la meilleure cotation disponible."""
        comparison = await self.get_quotes(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            slippage_tolerance=slippage_tolerance,
        )
        return comparison.best_quote

    async def build_swap_transaction(
        self, quote: DEXQuote, recipient: str
    ) -> dict[str, Any]:
        """
        Délègue la construction de la transaction de swap à l'adaptateur
        ayant émis la cotation.
        """
        if not isinstance(quote, DEXQuote):
            raise DEXTransactionError("quote doit être une instance de DEXQuote")

        adapter = self._adapters_by_name.get(quote.dex_name)
        if adapter is None:
            raise DEXTransactionError(
                f"Aucun adaptateur enregistré pour le DEX {quote.dex_name!r}"
            )

        return await adapter.build_swap_transaction(quote, recipient)


__all__ = [
    "DEXError",
    "DEXRouter",
    "NoValidRouteError",
    "RouteComparisonResult",
]
