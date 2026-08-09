# core/strategy_config.py — V6.0.0
"""Outils utilitaires pour charger et valider la configuration de stratégie (V6.0)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_strategy_config(path: str | Path = "config/strategy_v6_0.json") -> Dict[str, Any]:
    """Charger et valider le fichier de configuration de stratégie.

    Args:
        path: Chemin vers le fichier JSON, en chaîne de caractères ou objet :class:`Path`.

    Returns:
        Le dictionnaire Python issu du JSON validé.

    Raises:
        FileNotFoundError: Si le fichier de configuration est introuvable.
        ValueError: Si le fichier contient un JSON invalide ou si la validation échoue.
    """

    config_path = Path(path)

    # Si le chemin par défaut V6 n'existe pas, tenter fallback V5.5
    if not config_path.exists() and str(path) == "config/strategy_v6_0.json":
        fallback_path = Path("config/strategy_v5_5.json")
        if fallback_path.exists():
            config_path = fallback_path

    try:
        content = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Fichier de configuration introuvable: {config_path}"
        ) from exc

    try:
        config_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON de configuration invalide dans {config_path}: {exc.msg}"
        ) from exc

    validate_strategy_config(config_data)
    logger.info("Configuration de stratégie chargée avec succès depuis %s", config_path)
    return config_data


def validate_strategy_config(cfg: Dict[str, Any]) -> None:
    """Valider la structure et la version de la configuration de stratégie.

    Prend en charge les schémas V6.0 et V5.5.
    """
    version = str(cfg.get("version", ""))

    if version in {"6.0", "6.0.0"}:
        required_v6_keys = [
            "version",
            "mode_execution",
            "allocations",
            "rebalance",
            "market_guardrails",
        ]
        missing_keys = [key for key in required_v6_keys if key not in cfg]
        if missing_keys:
            raise ValueError(f"Clés de configuration V6 manquantes: {', '.join(missing_keys)}")
        return

    if version == "5.5.0":
        required_v5_keys = [
            "version",
            "meta",
            "global",
            "modes",
            "triggers",
            "mode_engine",
            "portfolio_actions",
            "scoring_overrides",
            "safety",
        ]
        missing_keys = [key for key in required_v5_keys if key not in cfg]
        if missing_keys:
            raise ValueError(f"Clés de configuration V5.5 manquantes: {', '.join(missing_keys)}")
        return

    raise ValueError(f"Version de configuration inattendue: {version!r} (attendu '6.0' ou '5.5.0')")