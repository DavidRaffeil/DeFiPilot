# core/dex/exceptions.py – V6.5.0
"""Exceptions typées du module DEX."""

from __future__ import annotations


class DEXError(Exception):
    """Erreur de base pour tous les adaptateurs DEX."""


class DEXQuoteError(DEXError):
    """Impossible d'obtenir une cotation (pool introuvable, liquidité insuffisante, échec RPC...)."""


class DEXTransactionError(DEXError):
    """Impossible de construire la transaction de swap."""


class NoValidRouteError(DEXError):
    """Aucune route valide n'a pu être obtenue auprès des adaptateurs DEX."""

