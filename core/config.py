# core/config.py – V6.5
import json
import os
from pathlib import Path

# === Chargement configuration utilisateur ===
def charger_config():
    """
    Charge la configuration depuis config.json si présent.
    Sinon retourne les valeurs par défaut.
    """
    chemin = Path("config.json")
    if chemin.is_file():
        with chemin.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Valeurs par défaut si config.json absent
    return {
        "profil_defaut": "modere",
        "dry_run": True,
    }

# === Profils d’investissement ===
PROFILS = {
    "prudent": {
        "apr": 0.2,
        "tvl": 0.8,
        "historique_max_bonus": 0.10,
        "historique_max_malus": -0.05,
        "poids_slippage": 0.5,
    },
    "modere": {
        "apr": 0.5,
        "tvl": 0.5,
        "historique_max_bonus": 0.20,
        "historique_max_malus": -0.10,
        "poids_slippage": 0.3,
    },
    "dynamique": {
        "apr": 0.7,
        "tvl": 0.3,
        "historique_max_bonus": 0.25,
        "historique_max_malus": -0.15,
        "poids_slippage": 0.2,
    },
    "agressif": {
        "apr": 0.8,
        "tvl": 0.2,
        "historique_max_bonus": 0.30,
        "historique_max_malus": -0.20,
        "poids_slippage": 0.1,
    },
}

# === Chargement unique de la configuration ===
_config = charger_config()

# Variables globales exportées
PROFIL_ACTIF = _config.get("profil_defaut", "modere")
SWAP_REEL = not _config.get("dry_run", True)

# Activation IA – pondération dynamique (désactivée en V3.3)
AI_PONDERATION_ACTIVE = False

# Feature flag Multi-DEX (V6.5) : activé par défaut
FEATURE_MULTI_DEX: bool = bool(_config.get("feature_multi_dex", True))


# === Gestion du réservoir de carburant (GasTank - Phase 4 / V6.6) ===
def _read_env_float(var_name: str, default: float) -> float:
    raw = os.getenv(var_name)
    if raw is not None and raw.strip() != "":
        try:
            return float(raw.strip())
        except ValueError:
            pass
    return float(default)


def _read_env_bool(var_name: str, default: bool) -> bool:
    raw = os.getenv(var_name)
    if raw is not None and raw.strip() != "":
        norm = raw.strip().lower()
        if norm in {"1", "true", "yes", "on", "oui"}:
            return True
        if norm in {"0", "false", "no", "off", "non"}:
            return False
    return bool(default)


def get_gas_tank_config() -> dict:
    """Charge dynamiquement les paramètres du GasTank depuis l'environnement ou les défauts."""
    return {
        "min_pol_reserve": _read_env_float(
            "GAS_MIN_POL_RESERVE", _config.get("gas_min_pol_reserve", 5.0)
        ),
        "target_pol_reserve": _read_env_float(
            "GAS_TARGET_POL_RESERVE", _config.get("gas_target_pol_reserve", 10.0)
        ),
        "critical_gas_threshold": _read_env_float(
            "GAS_CRITICAL_THRESHOLD", _config.get("gas_critical_threshold", 1.0)
        ),
        "max_pol_reserve": _read_env_float(
            "GAS_MAX_POL_RESERVE", _config.get("gas_max_pol_reserve", 25.0)
        ),
        "auto_wrap_enabled": _read_env_bool(
            "GAS_AUTO_WRAP_ENABLED", _config.get("gas_auto_wrap_enabled", True)
        ),
    }


_gas_cfg = get_gas_tank_config()
GAS_MIN_POL_RESERVE: float = _gas_cfg["min_pol_reserve"]
GAS_TARGET_POL_RESERVE: float = _gas_cfg["target_pol_reserve"]
GAS_CRITICAL_THRESHOLD: float = _gas_cfg["critical_gas_threshold"]
GAS_MAX_POL_RESERVE: float = _gas_cfg["max_pol_reserve"]
GAS_AUTO_WRAP_ENABLED: bool = _gas_cfg["auto_wrap_enabled"]

# Journaux spécifiques à l’ajout de liquidité (V3.8)
JOURNAL_LIQUIDITY_CSV = "logs/liquidity.csv"
JOURNAL_LIQUIDITY_JSONL = "logs/liquidity.jsonl"
