# core/dry_run_guard.py – V6.0.0
"""Garde-fou d'exécution (Safety Lock) pour le mode Dry-Run / Simulation.

Ce module garantit qu'aucune transaction réelle ne peut être signée ni envoyée
sur le réseau lorsque le mode Dry-Run / Simulation est actif.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

logger = logging.getLogger(__name__)

# Par défaut, le mode dry_run est ACTIVÉ pour des raisons de sécurité.
_DRY_RUN_GLOBAL: bool = True


class DryRunSafetyViolation(RuntimeError):
    """Exception levée lorsqu'une action réelle est tentée en mode Dry-Run."""

    def __init__(self, message: str = "Tentative d'exécution d'une action réelle en mode Dry-Run / Simulation.") -> None:
        super().__init__(message)
        self.message = message


def set_dry_run_mode(enabled: bool) -> None:
    """Activer ou désactiver globalement le verrou Dry-Run."""
    global _DRY_RUN_GLOBAL
    _DRY_RUN_GLOBAL = bool(enabled)
    logger.info("[SAFETY LOCK] Mode Dry-Run global défini sur : %s", _DRY_RUN_GLOBAL)


def get_dry_run_mode() -> bool:
    """Obtenir l'état du verrou Dry-Run global."""
    return _DRY_RUN_GLOBAL


def is_dry_run_enabled(config: Mapping[str, Any] | None = None) -> bool:
    """Déterminer si le mode Dry-Run est actif.

    Vérifie la configuration fournie (clé `dry_run` ou `mode_execution`),
    sinon retombe sur le statut global `_DRY_RUN_GLOBAL`.
    """
    if config is not None and isinstance(config, Mapping):
        if "dry_run" in config:
            return bool(config.get("dry_run"))
        if "mode_execution" in config:
            mode = str(config.get("mode_execution")).lower()
            return mode in {"simulation", "dry_run", "dryrun", "test", "simu"}

    return _DRY_RUN_GLOBAL


def assert_dry_run_safe(action_type: str = "transaction", config: Mapping[str, Any] | None = None) -> None:
    """Vérifier que l'opération demandée n'enfreint pas le mode Dry-Run.

    Si dry_run est actif, lève une DryRunSafetyViolation sans faire planter brutalement
    l'ensemble du processus (l'exception doit être capturée au niveau supérieur).
    """
    if is_dry_run_enabled(config):
        err_msg = (
            f"[SAFETY LOCK BLOCKED] [SIMULATION / DRY-RUN] Tentative de signature ou d'envoi "
            f"de transaction réelle bloquée pour l'action '{action_type}' car le mode Dry-Run est actif."
        )
        logger.critical(err_msg)
        raise DryRunSafetyViolation(err_msg)
