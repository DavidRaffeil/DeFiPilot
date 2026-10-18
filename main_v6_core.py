# main_v6_core.py – V6.0
"""Coeur d'exécution DeFiPilot V6.0.

Ce module centralise la logique de démarrage (détection de mode,
initialisation du logging, verrou de sécurité Dry-Run, routage GUI/CLI/Simulation)
sans dépendre d'un launcher externe.
"""

from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
import sys
from decimal import ROUND_DOWN, Decimal
from typing import Any, Callable, Dict, Mapping, Optional

from core.capital.compounding import TimeDecayCompounder
from core.dry_run_guard import (
    DryRunSafetyViolation,
    is_dry_run_enabled,
    set_dry_run_mode,
)

APP_VERSION: str = "V6.0"
_LOGGER_NAME = "DeFiPilot.V6Core"


def get_project_root() -> Path:
    """Retourner le dossier projet (répertoire du fichier courant)."""
    return Path(__file__).resolve().parent


def load_strategy_config() -> Dict[str, Any]:
    """Charger la configuration de stratégie V6.0 si disponible."""
    cfg_path = get_project_root() / "config" / "strategy_v6_0.json"
    if not cfg_path.exists():
        return {}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logging.getLogger(_LOGGER_NAME).warning(
            "Impossible de charger strategy_v6_0.json: %s", exc
        )
        return {}


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


def is_dry_run_requested(argv: list[str]) -> bool:
    """Indiquer si le drapeau --dry-run est présent dans les arguments CLI."""
    return "--dry-run" in argv


def detect_mode(argv: list[str]) -> str:
    """Déterminer le mode d'exécution à partir des arguments CLI.

    Le drapeau --dry-run n'est pas un mode : il se combine avec n'importe quel
    mode (voir is_dry_run_requested) et ne modifie pas le mode détecté.
    """
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
    print("Options :")
    print("--dry-run  (force le verrou de sécurité, combinable avec les modes)")


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


_QUANT = Decimal("0.000001")


class CapitalCycleManager:
    """Répartit les profits récoltés entre réinvestissement et réserve sécurisée.

    Si la section `compounding` est absente ou désactivée, comportement classique :
    100 % du profit est réinvesti, sans dégressivité.
    """

    def __init__(
        self,
        strategy_cfg: Optional[Mapping[str, Any]] = None,
        reinvest_action: Optional[Callable[[Decimal, str], Any]] = None,
        secure_action: Optional[Callable[[Decimal], Any]] = None,
    ) -> None:
        cfg = strategy_cfg or {}
        comp_cfg = cfg.get("compounding")
        self.compounder: Optional[TimeDecayCompounder] = (
            TimeDecayCompounder(comp_cfg) if isinstance(comp_cfg, Mapping) else None
        )
        self._reinvest_action = reinvest_action
        self._secure_action = secure_action
        self.reinvested_total = Decimal("0")
        self.secured_reserve = Decimal("0")
        self._logger = logging.getLogger(_LOGGER_NAME)

    def process_profit(
        self, profit_amount: Any, current_timestamp: Any, pool_id: str
    ) -> Dict[str, Decimal]:
        profit = profit_amount if isinstance(profit_amount, Decimal) else Decimal(str(profit_amount))

        if self.compounder is not None and self.compounder.enabled:
            alloc = self.compounder.calculate_allocation(profit, current_timestamp, pool_id)
            reinvest, secured, rate = (
                alloc["reinvest_amount"], alloc["secured_amount"], alloc["rate"],
            )
            days = int(
                max(Decimal(0), Decimal(str(current_timestamp)) - self.compounder.entry_timestamp)
                / Decimal(86400)
            )
            self._logger.info(
                "[COMPOUNDING] pool=%s jours=%d taux=%s reinvest=%s secured=%s",
                pool_id, days, rate, reinvest, secured,
            )
        else:
            reinvest = profit.quantize(_QUANT, rounding=ROUND_DOWN)
            secured = profit - reinvest
            rate = Decimal("1")
            self._logger.info(
                "[COMPOUNDING] désactivé : réinvestissement classique pool=%s reinvest=%s",
                pool_id, reinvest,
            )

        if reinvest > 0:
            self.reinvested_total += reinvest
            if self._reinvest_action is not None:
                self._reinvest_action(reinvest, pool_id)
        if secured > 0:
            self.secured_reserve += secured
            if self._secure_action is not None:
                self._secure_action(secured)

        return {"rate": rate, "reinvest_amount": reinvest, "secured_amount": secured}


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
    except DryRunSafetyViolation as exc:
        logger.critical(
            "[SIMULATION / DRY-RUN] [SAFETY LOCK] Tentative d'action réelle bloquée en mode simulation : %s",
            exc,
        )
        print(f"[SIMULATION / DRY-RUN] [SAFETY LOCK BLOCKED] {exc}")
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
            print("[SIMULATION / DRY-RUN] Simulation V6 indisponible")
            return 2

        result = simulation_func(argv)
        if isinstance(result, int):
            return 0 if result == 0 else 1
        return 0
    except DryRunSafetyViolation as exc:
        logger.critical(
            "[SIMULATION / DRY-RUN] [SAFETY LOCK] Tentative d'action réelle bloquée en simulation : %s",
            exc,
        )
        print(f"[SIMULATION / DRY-RUN] [SAFETY LOCK BLOCKED] {exc}")
        return 0
    except (ImportError, AttributeError):
        print("[SIMULATION / DRY-RUN] Simulation V6 indisponible")
        return 2
    except Exception:
        logger.exception("Erreur inattendue pendant l'exécution de la simulation.")
        print("[SIMULATION / DRY-RUN] Une erreur inattendue est survenue pendant l'exécution de la simulation.")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée principal pour router vers le mode demandé."""
    args = sys.argv[1:] if argv is None else argv
    setup_logging()

    logger = logging.getLogger(_LOGGER_NAME)
    strategy_cfg = load_strategy_config()

    mode = detect_mode(args)
    logger.info("Mode détecté : %s", mode)

    # Activer le verrou Dry-Run : drapeau --dry-run (prioritaire, quoi qu'il arrive),
    # mode simulation, ou configuration dans strategy_v6_0.json
    if is_dry_run_requested(args):
        set_dry_run_mode(True)
        logger.info("[SIMULATION / DRY-RUN] Drapeau --dry-run détecté : verrou forcé, ignore la configuration.")
        logger.info("[SIMULATION / DRY-RUN] Garde-fou (Safety Lock) actif : toute transaction réelle est verrouillée.")
    elif mode == "simulate" or is_dry_run_enabled(strategy_cfg):
        set_dry_run_mode(True)
        logger.info("[SIMULATION / DRY-RUN] Garde-fou (Safety Lock) actif : toute transaction réelle est verrouillée.")

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