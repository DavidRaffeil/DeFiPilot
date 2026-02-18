# main_v6_core.py – V6.0
"""Coeur d'exécution DeFiPilot V6.0.

Ce module centralise la logique de démarrage (détection de mode,
initialisation du logging, routage GUI/CLI/Simulation) sans dépendre
d'un launcher externe.
"""

from __future__ import annotations

from pathlib import Path
import importlib
import logging
import sys
from typing import Callable, Optional

APP_VERSION: str = "V6.0"
_LOGGER_NAME = "DeFiPilot.V6Core"


def get_project_root() -> Path:
    """Retourner le dossier projet (répertoire du fichier courant)."""
    return Path(__file__).resolve().parent


def setup_logging(log_filename: str = "main_v6_core.log") -> None:
    """Configurer le logging global vers un fichier et la sortie standard."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Éviter la duplication des handlers en cas d'appels répétés.
    if root_logger.handlers:
        root_logger.handlers.clear()

    log_dir = get_project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_filename

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    logging.getLogger(_LOGGER_NAME).info("Logging initialisé. Fichier: %s", log_file)


def detect_mode(argv: list[str]) -> str:
    """Déterminer le mode d'exécution à partir des arguments CLI."""
    if "--help" in argv or "-h" in argv:
        return "help"
    if "--gui" in argv:
        return "gui"
    if "--simulate" in argv:
        return "simulate"
    if "--cli" in argv:
        return "cli"
    return "gui"


def print_help() -> None:
    """Afficher l'aide des modes disponibles."""
    print("DeFiPilot V6.0")
    print("Modes disponibles :")
    print("--gui")
    print("--cli")
    print("--simulate")
    print("--help")


def run_gui() -> int:
    """Lancer l'interface graphique si disponible."""
    logger = logging.getLogger(_LOGGER_NAME)
    try:
        from gui.main_window import MainWindow

        app = MainWindow()
        app.mainloop()
        return 0
    except ImportError:
        print("Interface graphique indisponible : module GUI introuvable.")
        return 2
    except Exception:
        logger.exception("Erreur inattendue lors du lancement de l'interface graphique.")
        print("Une erreur inattendue est survenue lors du lancement de l'interface graphique.")
        return 1


def _resolve_callable(module_name: str, func_names: list[str]) -> Optional[Callable[..., object]]:
    """Résoudre la première fonction disponible dans un module cible."""
    module = importlib.import_module(module_name)
    for func_name in func_names:
        candidate = getattr(module, func_name, None)
        if callable(candidate):
            return candidate
    return None


def run_cli(argv: list[str]) -> int:
    """Exécuter le pipeline CLI V6 si disponible."""
    logger = logging.getLogger(_LOGGER_NAME)
    try:
        cli_func = _resolve_callable("core.cli", ["run_cli", "main_cli"])
        if cli_func is None:
            print("CLI V6 indisponible : aucune fonction d'entrée compatible trouvée.")
            return 2

        result = cli_func(argv)
        if isinstance(result, int):
            return 0 if result == 0 else 1
        return 0
    except (ImportError, AttributeError):
        print("CLI V6 indisponible : composant manquant.")
        return 2
    except Exception:
        logger.exception("Erreur inattendue pendant l'exécution du mode CLI.")
        print("Une erreur inattendue est survenue pendant l'exécution du mode CLI.")
        return 1


def run_simulation(argv: list[str]) -> int:
    """Exécuter la simulation V6 si disponible."""
    logger = logging.getLogger(_LOGGER_NAME)
    try:
        simulation_func = _resolve_callable("core.simulation", ["run_simulation", "main_simulation"])
        if simulation_func is None:
            print("Simulation V6 indisponible")
            return 2

        result = simulation_func(argv)
        if isinstance(result, int):
            return 0 if result == 0 else 1
        return 0
    except (ImportError, AttributeError):
        print("Simulation V6 indisponible")
        return 2
    except Exception:
        logger.exception("Erreur inattendue pendant l'exécution de la simulation.")
        print("Une erreur inattendue est survenue pendant l'exécution de la simulation.")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée principal pour router vers le mode demandé."""
    args = sys.argv[1:] if argv is None else argv
    setup_logging()

    mode = detect_mode(args)
    logger = logging.getLogger(_LOGGER_NAME)
    logger.info("Mode détecté : %s", mode)

    if mode == "help":
        print_help()
        return 0
    if mode == "gui":
        return run_gui()
    if mode == "cli":
        return run_cli(args)
    if mode == "simulate":
        return run_simulation(args)

    logger.warning("Mode inattendu '%s', bascule vers GUI.", mode)
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
