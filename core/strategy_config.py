# core/strategy_config.py — V5.5.0
"""Outils utilitaires pour charger et valider la configuration de stratégie.

Ce module se limite à la lecture et à la vérification de la structure du
fichier de configuration, sans implémenter de logique métier.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_strategy_config(path: str | Path = "config/strategy_v5_5.json") -> Dict[str, Any]:
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

    Args:
        cfg: Dictionnaire représentant la configuration à valider.

    Raises:
        ValueError: Si des clés obligatoires manquent ou si la version est incorrecte.
    """

    required_keys = [
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

    missing_keys = [key for key in required_keys if key not in cfg]
    if missing_keys:
        raise ValueError(
            f"Clés de configuration manquantes: {', '.join(missing_keys)}"
        )

    version = cfg.get("version")
    if version != "5.5.0":
        raise ValueError(
            f"Version de configuration inattendue: {version!r} (attendu '5.5.0')"
        )