"""
Module de configuration global (`config.py`) de DeFiPilot V6.6.
Réexporte les constantes de `core.config` et lit dynamiquement les variables
d'environnement du GasTank.
"""

from __future__ import annotations

import core.config as _core_config
from core.config import (
    AI_PONDERATION_ACTIVE,
    FEATURE_MULTI_DEX,
    JOURNAL_LIQUIDITY_CSV,
    JOURNAL_LIQUIDITY_JSONL,
    PROFIL_ACTIF,
    PROFILS,
    SWAP_REEL,
    _read_env_bool,
    _read_env_float,
    charger_config,
    get_gas_tank_config,
)

GAS_MIN_POL_RESERVE: float = _read_env_float(
    "GAS_MIN_POL_RESERVE", _core_config.GAS_MIN_POL_RESERVE
)
GAS_TARGET_POL_RESERVE: float = _read_env_float(
    "GAS_TARGET_POL_RESERVE", _core_config.GAS_TARGET_POL_RESERVE
)
GAS_CRITICAL_THRESHOLD: float = _read_env_float(
    "GAS_CRITICAL_THRESHOLD", _core_config.GAS_CRITICAL_THRESHOLD
)
GAS_MAX_POL_RESERVE: float = _read_env_float(
    "GAS_MAX_POL_RESERVE", _core_config.GAS_MAX_POL_RESERVE
)
GAS_AUTO_WRAP_ENABLED: bool = _read_env_bool(
    "GAS_AUTO_WRAP_ENABLED", _core_config.GAS_AUTO_WRAP_ENABLED
)

__all__ = [
    "AI_PONDERATION_ACTIVE",
    "FEATURE_MULTI_DEX",
    "GAS_AUTO_WRAP_ENABLED",
    "GAS_CRITICAL_THRESHOLD",
    "GAS_MAX_POL_RESERVE",
    "GAS_MIN_POL_RESERVE",
    "GAS_TARGET_POL_RESERVE",
    "JOURNAL_LIQUIDITY_CSV",
    "JOURNAL_LIQUIDITY_JSONL",
    "PROFIL_ACTIF",
    "PROFILS",
    "SWAP_REEL",
    "charger_config",
    "get_gas_tank_config",
]
