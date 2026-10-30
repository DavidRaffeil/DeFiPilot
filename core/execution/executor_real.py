"""
Module de pont d'exécution réelle et simulée (`core/execution/executor_real.py`) pour DeFiPilot V6.6.
Expose `RealExecutor`, `executer_action_reelle`, `GasCriticalError` et `GasTankManager`.
"""

from __future__ import annotations

from core.execution.gas_tank import GasCriticalError, GasTankManager
from core.executor_real import (
    ALLOWED_STATUSES,
    RealExecutor,
    _normalize_verdict,
    _resolve_gas_tank,
    _resolve_multi_dex_swap,
    executer_action_reelle,
)

__all__ = [
    "ALLOWED_STATUSES",
    "GasCriticalError",
    "GasTankManager",
    "RealExecutor",
    "_normalize_verdict",
    "_resolve_gas_tank",
    "_resolve_multi_dex_swap",
    "executer_action_reelle",
]
