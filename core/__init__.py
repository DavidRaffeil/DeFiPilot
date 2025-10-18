# __init__.py – V4.0.4 (package core)

"""
Package 'core' simplifié pour la branche stratégie de marché (V4.0.x).
Ce fichier rend 'core' importable sans dépendances inutiles.
Aucune logique métier, aucun import croisé, pas d'effets de bord.
"""

from __future__ import annotations

__all__ = [
    "market_signals",
    "market_signals_adapter",
]
