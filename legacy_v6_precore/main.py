# main.py – V6.0
"""
Point d'entrée principal pour DeFiPilot V6.0.

Rôle de ce fichier :
- Initialiser le logging de base.
- Analyser les arguments de la ligne de commande.
- Valider l'environnement réel AVANT toute exécution.
- Déléguer l'exécution au bon "runner" (GUI ou CLI).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import List, Optional

from core.env_validator import valider_environnement_reel

APP_VERSION = "V6.0"


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def get_project_root() -> str:
    """Retourne le chemin racine supposé du projet (dossier de ce fichier)."""
    return os.path.dirname(os.path.abspath(__file__))


def setup_logging() -> None:
    """Configure un logging simple vers la console et, si possible, vers un fichier."""
    root = get_project_root()
    logs_dir = os.path.join(root, "data", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "main_v6.log")

    log_format = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    console_handler = logging.StreamHandler()

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=datefmt,
        handlers=[file_handler, console_handler],
    )


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """Point d'entrée principal V6.0."""

    if argv is None:
        argv = sys.argv

    setup_logging()
    logger = logging.getLogger("DeFiPilot.Main")

    mode_execution = os.getenv("MODE_EXECUTION", "").strip()
    rpc_url = os.getenv("RPC_URL", "").strip()
    wallet_address = os.getenv("WALLET_ADDRESS", "").strip()
    private_key = os.getenv("PRIVATE_KEY", "").strip()
    journal_execution_path = os.getenv("JOURNAL_EXECUTION_PATH", "").strip()

    expected_chain_id_raw = os.getenv("EXPECTED_CHAIN_ID", "").strip()
    try:
        expected_chain_id = int(expected_chain_id_raw)
    except (TypeError, ValueError):
        expected_chain_id = -1

    strategy_config_path = os.getenv("STRATEGY_CONFIG_PATH", "strategy_config.json")
    if os.path.exists(strategy_config_path):
        with open(strategy_config_path, "r", encoding="utf-8") as strategy_file:
            strategy_config = json.load(strategy_file)
    else:
        strategy_config = {}

    limites = strategy_config.get("limites", {})

    # -------------------------------------------------------------------
    # Validation environnement réel (BLOQUANTE)
    # -------------------------------------------------------------------

    retour = valider_environnement_reel(
        mode_execution=mode_execution,
        rpc_url=rpc_url,
        expected_chain_id=expected_chain_id,
        wallet_address=wallet_address,
        private_key=private_key,
        limites=limites,
        journal_execution_path=journal_execution_path,
    )

    if retour.get("status") == "ENV_INVALID":
        errors = retour.get("errors", [])
        raise RuntimeError(
            "Environnement réel invalide, arrêt du lancement. Détails: "
            + "; ".join(errors)
        )

    # -------------------------------------------------------------------
    # Routage mode GUI / CLI (inchangé)
    # -------------------------------------------------------------------

    from run_defipilot_v6 import detect_mode, run_cli, run_gui, print_help

    mode = detect_mode(argv)
    logger.info("DeFiPilot %s – mode détecté : %s", APP_VERSION, mode)

    if mode == "help":
        print_help()
        return 0

    if mode == "gui":
        return run_gui()

    if mode in ("cli", "simulate"):
        return run_cli(mode, argv)

    logger.info("Mode par défaut : tentative GUI puis fallback CLI")
    gui_status = run_gui()
    if gui_status == 0:
        return 0

    logger.info("GUI indisponible, bascule CLI")
    return run_cli("cli", argv)


if __name__ == "__main__":
    sys.exit(main())