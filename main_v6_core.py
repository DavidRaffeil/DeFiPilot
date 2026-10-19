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
import os
from pathlib import Path
import sys
from decimal import ROUND_DOWN, Decimal
from typing import Any, Callable, Dict, Mapping, Optional

from core.capital.compounding import TimeDecayCompounder
from core.capital.profit_sweeper import ProfitSweeper
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


_USDC_POLYGON = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
_USDC_DECIMALS = 6


class CapitalActionError(RuntimeError):
    """Action de capital refusée ou impossible (la réserve ne doit pas être modifiée)."""


def is_valid_wallet_address(address: Optional[str]) -> bool:
    """Adresse EVM valide : `0x` + 40 caractères hexadécimaux (42 au total)."""
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        return False
    try:
        int(address[2:], 16)
    except ValueError:
        return False
    return True


def build_capital_actions(
    dry_run: Optional[bool] = None,
    env: Optional[Mapping[str, str]] = None,
    transfer_executor: Optional[Callable[[Dict[str, Any]], Any]] = None,
    liquidity_executor: Optional[Callable[[str, Decimal], Any]] = None,
    state_getter: Optional[Callable[[], Dict[str, Any]]] = None,
    state_setter: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> tuple[Callable[[str, Decimal], Dict[str, Any]], Callable[[Decimal], Dict[str, Any]]]:
    """Construire `(reinvest_action, secure_action)` pour CapitalCycleManager.

    - `dry_run=None` : lit le verrou global à chaque appel (`is_dry_run_enabled`).
    - `transfer_executor(descriptor)` : envoie réellement le transfert ERC-20.
    - `liquidity_executor(pool_id, amount)` : module d'exécution de liquidité V6.
    En mode réel, l'absence d'exécuteur lève `CapitalActionError` (rien n'est envoyé).
    """
    logger = logging.getLogger(_LOGGER_NAME)

    def _is_dry() -> bool:
        return is_dry_run_enabled() if dry_run is None else bool(dry_run)

    def _get_state() -> Dict[str, Any]:
        if state_getter is not None:
            return state_getter()
        from core.state_manager import get_state
        return get_state()

    def _set_state(state: Dict[str, Any]) -> Any:
        if state_setter is not None:
            return state_setter(state)
        from core.state_manager import update_state
        return update_state(state)

    def secure_action(amount: Decimal) -> Dict[str, Any]:
        if _is_dry():
            logger.info(
                "[PROFIT_SWEEPER] [SIMULATION] Balayage sécurisé de %s USDC vers la réserve "
                "externe (aucun transfert on-chain)", amount,
            )
            return {"status": "simulated", "amount": amount}

        environ = os.environ if env is None else env
        address = environ.get("RESERVE_WALLET_ADDRESS") or environ.get("SAFE_WALLET_ADDRESS")
        if not is_valid_wallet_address(address):
            logger.critical(
                "[SECURITY] Balayage annulé : RESERVE_WALLET_ADDRESS non définie ou invalide"
            )
            raise CapitalActionError(
                "Balayage annulé : RESERVE_WALLET_ADDRESS non définie ou invalide"
            )

        try:
            from web3 import Web3
            address = Web3.to_checksum_address(address)
        except ImportError:
            pass
        except ValueError as exc:
            logger.critical("[SECURITY] Balayage annulé : adresse de réserve invalide (%s)", exc)
            raise CapitalActionError("Balayage annulé : adresse de réserve invalide") from exc

        descriptor = {
            "kind": "erc20_transfer",
            "token": _USDC_POLYGON,
            "to": address,
            "amount": amount,
            "amount_raw": int(amount * (10 ** _USDC_DECIMALS)),
        }
        if transfer_executor is None:
            logger.critical(
                "[SECURITY] Balayage annulé : aucun exécuteur de transfert ERC-20 configuré"
            )
            raise CapitalActionError("Aucun exécuteur de transfert ERC-20 configuré")
        logger.info("[PROFIT_SWEEPER] Transfert ERC-20 de %s USDC vers %s", amount, address)
        result = transfer_executor(descriptor)
        return {"status": "executed", "amount": amount, "to": address, "result": result}

    def reinvest_action(pool_id: str, reinvest_amount: Decimal) -> Dict[str, Any]:
        if _is_dry():
            logger.info(
                "[COMPOUNDING] [SIMULATION] Réinvestissement de %s dans la pool %s",
                reinvest_amount, pool_id,
            )
            state = dict(_get_state())
            positions = dict(state.get("positions_simulees") or {})
            previous = Decimal(str(positions.get(pool_id, "0")))
            positions[pool_id] = str(previous + reinvest_amount)  # str : JSON sans perte
            state["positions_simulees"] = positions
            _set_state(state)
            return {"status": "simulated", "pool_id": pool_id, "amount": reinvest_amount}

        if liquidity_executor is None:
            logger.critical(
                "[COMPOUNDING] Réinvestissement réel annulé : aucun module de liquidité configuré "
                "(pool %s)", pool_id,
            )
            raise CapitalActionError("Aucun module d'exécution de liquidité configuré")
        result = liquidity_executor(pool_id, reinvest_amount)
        return {"status": "executed", "pool_id": pool_id, "amount": reinvest_amount, "result": result}

    return reinvest_action, secure_action


class CapitalCycleManager:
    """Cycle de capital : compounding dégressif, réserve interne, balayage par palier.

    1. TimeDecayCompounder répartit 100 % du profit brut (réinvesti / sécurisé).
    2. La part réinvestie appelle `reinvest_action(pool_id, reinvest_amount)`.
    3. La part sécurisée alimente `accumulated_reserve` (aucune transaction).
    4. ProfitSweeper surveille la réserve : dès que le seuil est atteint,
       `secure_action(amount)` est appelé et la réserve est décrémentée du montant
       balayé (total si sweep_pct = 1, partiel sinon).

    Si `compounding` est absent ou désactivé : réinvestissement classique à 100 %.
    Sans section `profit_sweeper` (ou désactivée) : la réserve s'accumule sans sweep.
    """

    def __init__(
        self,
        strategy_cfg: Optional[Mapping[str, Any]] = None,
        reinvest_action: Optional[Callable[[str, Decimal], Any]] = None,
        secure_action: Optional[Callable[[Decimal], Any]] = None,
    ) -> None:
        cfg = strategy_cfg or {}
        comp_cfg = cfg.get("compounding")
        self.compounder: Optional[TimeDecayCompounder] = (
            TimeDecayCompounder(comp_cfg) if isinstance(comp_cfg, Mapping) else None
        )
        self._reinvest_action = reinvest_action
        self._secure_action = secure_action

        sweep_cfg = cfg.get("profit_sweeper")
        self.sweeper: Optional[ProfitSweeper] = None
        if isinstance(sweep_cfg, Mapping):
            # L'exécution réelle est portée par le callback `secure_action`
            # (le verrou dry-run s'applique à ce niveau).
            self.sweeper = ProfitSweeper(
                sweep_cfg,
                dry_run=False,
                executor=lambda amount, _asset: self._do_secure(amount),
            )

        self.reinvested_total = Decimal("0")
        self.pending_reinvest = Decimal("0")
        self.accumulated_reserve = Decimal("0")
        self.swept_total = Decimal("0")
        self._logger = logging.getLogger(_LOGGER_NAME)

    def _do_secure(self, amount: Decimal) -> None:
        if self._secure_action is not None:
            self._secure_action(amount)

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
            try:
                if self._reinvest_action is not None:
                    self._reinvest_action(pool_id, reinvest)
                self.reinvested_total += reinvest
            except Exception as exc:
                self.pending_reinvest += reinvest
                self._logger.critical(
                    "[COMPOUNDING] Réinvestissement échoué pool=%s montant=%s : %s (en attente=%s)",
                    pool_id, reinvest, exc, self.pending_reinvest,
                )
        if secured > 0:
            self.accumulated_reserve += secured

        swept = self._sweep_if_needed()

        return {
            "rate": rate,
            "reinvest_amount": reinvest,
            "secured_amount": secured,
            "swept_amount": swept,
            "accumulated_reserve": self.accumulated_reserve,
        }

    def _sweep_if_needed(self) -> Decimal:
        """Balayer la réserve si le seuil est atteint ; retourne le montant balayé."""
        zero = Decimal("0")
        if self.sweeper is None:
            return zero

        # La réserve est du profit déjà isolé : référence de capital = 0.
        try:
            result = self.sweeper.evaluate(self.accumulated_reserve, zero)
        except Exception as exc:
            # Réserve intacte : le transfert n'a pas eu lieu.
            self._logger.critical(
                "[PROFIT_SWEEPER] Sweep échoué, réserve inchangée=%s : %s",
                self.accumulated_reserve, exc,
            )
            return zero
        if not (result.triggered and result.executed):
            self._logger.info(
                "[PROFIT_SWEEPER] pas de sweep (%s) reserve=%s seuil=%s",
                result.reason, self.accumulated_reserve,
                self.sweeper.config.profit_threshold_usd,
            )
            return zero

        self.accumulated_reserve -= result.amount
        self.swept_total += result.amount
        self._logger.info(
            "[PROFIT_SWEEPER] sweep=%s %s reserve_restante=%s",
            result.amount, result.target_asset, self.accumulated_reserve,
        )
        return result.amount


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