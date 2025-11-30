# main.py – V5.0
"""
Point d'entrée principal pour DeFiPilot V5.0.

Rôle de ce fichier :
- Initialiser le logging de base.
- Analyser les arguments de la ligne de commande.
- Déléguer l'exécution au bon "runner" (GUI ou CLI) si disponible.
- Fournir des messages d'erreur clairs sans casser le projet.

Ce main est volontairement léger pour éviter les régressions :
la logique "métier" reste dans les autres modules (run_defipilot,
GUI, etc.).
"""

from __future__ import annotations

import logging
import os
import sys
from typing import List, Optional, Callable, Any


APP_VERSION = "V5.0"


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
    log_file = os.path.join(logs_dir, "main_v5.log")

    log_format = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Handler fichier
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=datefmt))

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=datefmt))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        force=True,
    )

    logging.getLogger(__name__).info("DeFiPilot %s – logging initialisé.", APP_VERSION)


# ---------------------------------------------------------------------------
# Détection du mode
# ---------------------------------------------------------------------------

def detect_mode(argv: List[str]) -> str:
    """
    Détermine le mode d'exécution à partir des arguments.

    Modes possibles :
    - 'gui'      : lance l'interface graphique (si disponible)
    - 'cli'      : lance le moteur CLI principal (si disponible)
    - 'simulate' : mode simulation (alias spécialisé de 'cli')
    - 'help'     : affiche l'aide
    - défaut     : 'gui' si disponible, sinon 'cli'
    """
    if len(argv) < 2:
        return "default"

    arg = argv[1].lower().strip()
    if arg in ("gui", "g"):
        return "gui"
    if arg in ("cli", "c"):
        return "cli"
    if arg in ("simulate", "sim"):
        return "simulate"
    if arg in ("help", "-h", "--help"):
        return "help"

    # Argument inconnu → on considère que c'est du CLI avec arguments
    return "cli"


def print_help() -> None:
    """Affiche une aide rapide sur les modes possibles."""
    msg = f"""
DeFiPilot {APP_VERSION} – Point d'entrée principal

Usage :
    python main.py [mode] [options]

Modes :
    gui, g         Lance l'interface graphique (si disponible).
    cli, c         Lance le mode CLI principal (run_defipilot, etc.).
    simulate, sim  Lance une simulation si supportée par le runner CLI.
    help, -h       Affiche cette aide.

Sans argument :
    - tente de lancer la GUI si elle est disponible ;
    - sinon bascule automatiquement en mode CLI.
"""
    print(msg.strip())


# ---------------------------------------------------------------------------
# Lancement GUI
# ---------------------------------------------------------------------------

def run_gui() -> int:
    """
    Tente de lancer l'interface graphique principale.

    - Essaie d'importer `gui.main_window`.
    - Cherche une fonction `run()` ou `main()` dans ce module.
    - Si rien n'est trouvé, loggue un message et retourne un code d'erreur doux.
    """
    logger = logging.getLogger("DeFiPilot.GUI")

    try:
        import gui.main_window as gui_main  # type: ignore[import]
    except Exception as exc:  # ImportError, ModuleNotFoundError, etc.
        logger.error("Impossible d'importer gui.main_window : %s", exc)
        logger.info("Astuce : vérifie que le dossier 'gui' est bien à la racine du projet.")
        return 1

    # On essaye d'appeler une fonction de lancement "standard"
    launch_func: Optional[Callable[[], Any]] = None

    if hasattr(gui_main, "run") and callable(getattr(gui_main, "run")):
        launch_func = getattr(gui_main, "run")
        logger.info("Lancement de l'interface graphique via gui.main_window.run()")
    elif hasattr(gui_main, "main") and callable(getattr(gui_main, "main")):
        launch_func = getattr(gui_main, "main")
        logger.info("Lancement de l'interface graphique via gui.main_window.main()")
    else:
        logger.error(
            "Le module gui.main_window ne définit ni 'run()' ni 'main()'. "
            "Merci d'ajouter une de ces fonctions pour lancer la GUI."
        )
        return 1

    try:
        launch_func()
    except Exception as exc:  # pragma: no cover - protection runtime
        logger.exception("Erreur lors de l'exécution de la GUI : %s", exc)
        return 1

    return 0


# ---------------------------------------------------------------------------
# Lancement CLI
# ---------------------------------------------------------------------------

def run_cli(mode: str, argv: List[str]) -> int:
    """
    Tente de lancer le runner CLI principal.

    Stratégie :
    - Essaye d'importer `run_defipilot`.
      - Si ce module contient une fonction `run()` ou `main(argv)`, on l'utilise.
    - Sinon, loggue un message d'information et sort proprement.

    Le paramètre `mode` permet éventuellement de transmettre une intention
    spéciale ('simulate', etc.) au runner, si celui-ci la supporte.
    """
    logger = logging.getLogger("DeFiPilot.CLI")

    try:
        import run_defipilot  # type: ignore[import]
    except Exception as exc:  # ImportError, ModuleNotFoundError, etc.
        logger.error("Impossible d'importer run_defipilot : %s", exc)
        logger.info(
            "Si tu utilises un autre script CLI (start_defipilot.py, simulateur_*.py, etc.), "
            "tu peux l'appeler directement en attendant d'unifier les entrées."
        )
        return 1

    # On essaie de détecter une fonction de lancement dans run_defipilot
    func_with_argv: Optional[Callable[[List[str], str], Any]] = None
    func_simple: Optional[Callable[[], Any]] = None

    # Stratégie flexible : plusieurs signatures possibles
    if hasattr(run_defipilot, "main"):
        candidate = getattr(run_defipilot, "main")
        if callable(candidate):
            func_with_argv = candidate  # on tentera main(argv, mode) puis main()
    if hasattr(run_defipilot, "run") and callable(getattr(run_defipilot, "run")):
        func_simple = getattr(run_defipilot, "run")

    if func_with_argv is None and func_simple is None:
        logger.error(
            "Le module run_defipilot ne définit ni fonction main() exploitable "
            "ni fonction run(). Merci d'ajouter un point d'entrée."
        )
        return 1

    logger.info("Lancement du mode CLI (mode='%s') via run_defipilot", mode)

    try:
        # On essaye d'abord main(argv, mode), puis main(argv), puis main()
        if func_with_argv is not None:
            try:
                # type: ignore[arg-type]
                func_with_argv(argv, mode)  # type: ignore[misc]
            except TypeError:
                try:
                    func_with_argv(argv)  # type: ignore[misc]
                except TypeError:
                    func_with_argv()  # type: ignore[misc]
        elif func_simple is not None:
            func_simple()
    except Exception as exc:  # pragma: no cover - protection runtime
        logger.exception("Erreur lors de l'exécution du runner CLI : %s", exc)
        return 1

    return 0


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """
    Point d'entrée principal.

    - Initialise le logging.
    - Détecte le mode d'exécution.
    - Route vers GUI ou CLI.
    """
    if argv is None:
        argv = sys.argv

    setup_logging()
    logger = logging.getLogger("DeFiPilot.Main")

    mode = detect_mode(argv)
    logger.info("DeFiPilot %s – mode détecté : %s", APP_VERSION, mode)

    if mode == "help":
        print_help()
        return 0

    if mode == "gui":
        return run_gui()

    if mode in ("cli", "simulate"):
        # Le mode "simulate" est géré à l'intérieur de run_cli via le paramètre `mode`.
        return run_cli(mode, argv)

    # Mode par défaut : on tente la GUI, puis on retombe sur le CLI si la GUI n'est pas dispo
    logger.info("Mode par défaut : tentative de lancement GUI, puis fallback CLI.")
    gui_status = run_gui()
    if gui_status == 0:
        return 0

    logger.info("GUI indisponible ou en erreur, bascule vers le mode CLI.")
    return run_cli("cli", argv)


if __name__ == "__main__":
    sys.exit(main())
