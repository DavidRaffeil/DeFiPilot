# farming_cli.py – V3.9.6
"""CLI DeFiPilot pour les opérations de farming LP (staking/harvest/unstake).

Cette version V3.9.6 applique le hotfix demandé :
- fallback automatique sur --pid lorsque --pool-id est absent;
- même fallback utilisé lors de la journalisation d'une erreur.

La logique métier des commandes stake/harvest/unstake reste strictement
identique à la V3.9.5 :
- le mode dry-run simule une transaction réussie et écrit un journal « success »;
- le mode réel n'est pas supporté et retourne une erreur journalisée.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.journal_farming import enregistrer_farming

VERSION = "V3.9.6"
_logger = logging.getLogger("farming_cli")


def _print_json(payload: Dict[str, Any]) -> None:
    """Affiche proprement un dictionnaire JSON."""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_ctx_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    dry_run_flag = bool(getattr(args, "dry_run", False) or getattr(args, "dryrun", False))
    balances_raw = getattr(args, "balances_after_json", "")
    balances_value: Any
    if isinstance(balances_raw, dict):
        balances_value = balances_raw
    elif isinstance(balances_raw, str) and balances_raw.strip():
        try:
            balances_value = json.loads(balances_raw)
        except json.JSONDecodeError:
            balances_value = {}
    else:
        balances_value = {}

    ctx: Dict[str, Any] = {
        "command": getattr(args, "command", ""),
        "dry_run": dry_run_flag,
        "pid": getattr(args, "pid", ""),
        "platform": getattr(args, "platform", ""),
        "chain": getattr(args, "chain", ""),
        "wallet": getattr(args, "wallet", ""),
        "run_id": getattr(args, "run_id", "cli"),
        "lp_token": getattr(args, "lp_token", ""),
        "lp_decimals": getattr(args, "lp_decimals", None),
        "amount_lp_requested": getattr(args, "amount_lp_requested", None),
        "amount_lp_effectif": getattr(args, "amount_lp_effectif", None),
        "rewards_token": getattr(args, "rewards_token", ""),
        "rewards_amount": getattr(args, "rewards_amount", None),
        "tx_hash": getattr(args, "tx_hash", ""),
        "gas_used": getattr(args, "gas_used", None),
        "effective_gas_price": getattr(args, "effective_gas_price", None),
        "tx_cost_native": getattr(args, "tx_cost_native", None),
        "balances_after_json": balances_value,
        "notes": getattr(args, "notes", ""),
        "version": VERSION,
        "dryrun": getattr(args, "dryrun", dry_run_flag),
    }
    ctx["pool_id"] = (getattr(args, "pool_id", "") or getattr(args, "pid", ""))
    return ctx


def _safe_journal_error(ctx: Dict[str, Any], err: Exception, tb: str) -> None:
    try:
        values: Dict[str, Any] = {
            "date": ctx.get("date", _utc_now()),
            "run_id": ctx.get("run_id", "cli"),
            "platform": ctx.get("platform", ""),
            "chain": ctx.get("chain", ""),
            "wallet": ctx.get("wallet", ""),
            "action": ctx.get("command", ""),
            "pool_id": (ctx.get("pool_id") or ctx.get("pid", "")),
            "lp_token": ctx.get("lp_token"),
            "lp_decimals": ctx.get("lp_decimals"),
            "amount_lp_requested": ctx.get("amount_lp_requested"),
            "amount_lp_effectif": ctx.get("amount_lp_effectif"),
            "rewards_token": ctx.get("rewards_token"),
            "rewards_amount": ctx.get("rewards_amount"),
            "tx_status": "error",
            "tx_hash": ctx.get("tx_hash", ""),
            "gas_used": ctx.get("gas_used"),
            "effective_gas_price": ctx.get("effective_gas_price"),
            "tx_cost_native": ctx.get("tx_cost_native"),
            "balances_after_json": ctx.get("balances_after_json", {}),
            "dry_run": ctx.get("dry_run", ctx.get("dryrun", True)),
            "notes": f"{err} | {tb}".replace("\n", " "),
            "version": ctx.get("version", VERSION),
        }
        enregistrer_farming(**values)
    except Exception as journal_exc:  # pragma: no cover
        _logger.exception("Impossible d'écrire le journal d'erreur: %s", journal_exc)


def _safe_journal_success(ctx: Dict[str, Any], result: Dict[str, Any]) -> None:
    try:
        values: Dict[str, Any] = {
            "date": ctx.get("date", _utc_now()),
            "run_id": ctx.get("run_id", "cli"),
            "platform": ctx.get("platform", ""),
            "chain": ctx.get("chain", ""),
            "wallet": ctx.get("wallet", ""),
            "action": ctx.get("command", ""),
            "pool_id": ctx.get("pool_id"),
            "lp_token": ctx.get("lp_token"),
            "lp_decimals": ctx.get("lp_decimals"),
            "amount_lp_requested": ctx.get("amount_lp_requested"),
            "amount_lp_effectif": result.get(
                "amount_lp_effectif", ctx.get("amount_lp_effectif")
            ),
            "rewards_token": ctx.get("rewards_token"),
            "rewards_amount": result.get("rewards_amount", ctx.get("rewards_amount")),
            "tx_status": result.get("tx_status", "success"),
            "tx_hash": result.get("tx_hash", ctx.get("tx_hash", "")),
            "gas_used": result.get("gas_used", ctx.get("gas_used")),
            "effective_gas_price": result.get(
                "effective_gas_price", ctx.get("effective_gas_price")
            ),
            "tx_cost_native": result.get("tx_cost_native", ctx.get("tx_cost_native")),
            "balances_after_json": result.get(
                "balances_after_json", ctx.get("balances_after_json", {})
            ),
            "dry_run": ctx.get("dry_run", ctx.get("dryrun", True)),
            "notes": result.get("notes", ctx.get("notes", "")),
            "version": ctx.get("version", VERSION),
        }
        enregistrer_farming(**values)
    except Exception as journal_exc:  # pragma: no cover
        _logger.exception("Impossible d'écrire le journal succès: %s", journal_exc)


def _execute_action(action: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    dry_run = ctx.get("dry_run", True)
    if dry_run:
        amount = ctx.get("amount_lp_requested") or 0.0
        return {
            "tx_status": "success",
            "tx_hash": f"dry-run-{action}",
            "amount_lp_effectif": amount,
            "rewards_amount": 0.0,
            "balances_after_json": ctx.get("balances_after_json", {}),
            "notes": "Simulation dry-run effectuée.",
        }
    raise RuntimeError(
        "Mode réel non supporté: veuillez utiliser --dry-run pour simuler l'action."
    )


def stake(args: argparse.Namespace) -> int:
    ctx = _build_ctx_from_args(args)
    ctx["command"] = "stake"
    try:
        result = _execute_action("stake", ctx)
        _safe_journal_success(ctx, result)
        _print_json({"ok": True, "action": "stake", "result": result})
        return 0
    except Exception as err:  # pragma: no cover - erreurs gérées dynamiquement
        tb = traceback.format_exc()
        _safe_journal_error(ctx, err, tb)
        _print_json({"ok": False, "action": "stake", "error": str(err)})
        return 1


def harvest(args: argparse.Namespace) -> int:
    ctx = _build_ctx_from_args(args)
    ctx["command"] = "harvest"
    try:
        result = _execute_action("harvest", ctx)
        _safe_journal_success(ctx, result)
        _print_json({"ok": True, "action": "harvest", "result": result})
        return 0
    except Exception as err:  # pragma: no cover
        tb = traceback.format_exc()
        _safe_journal_error(ctx, err, tb)
        _print_json({"ok": False, "action": "harvest", "error": str(err)})
        return 1


def unstake(args: argparse.Namespace) -> int:
    ctx = _build_ctx_from_args(args)
    ctx["command"] = "unstake"
    try:
        result = _execute_action("unstake", ctx)
        _safe_journal_success(ctx, result)
        _print_json({"ok": True, "action": "unstake", "result": result})
        return 0
    except Exception as err:  # pragma: no cover
        tb = traceback.format_exc()
        _safe_journal_error(ctx, err, tb)
        _print_json({"ok": False, "action": "unstake", "error": str(err)})
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="farming_cli.py",
        description="DeFiPilot – CLI pour le farming (stake/harvest/unstake)",
    )
    parser.add_argument("--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--pool-id", dest="pool_id", default="")
        subparser.add_argument("--pid", dest="pid", default="")
        subparser.add_argument("--platform", default="")
        subparser.add_argument("--chain", default="")
        subparser.add_argument("--wallet", default="")
        subparser.add_argument("--run-id", dest="run_id", default="cli")
        subparser.add_argument("--lp-token", dest="lp_token", default="")
        subparser.add_argument("--lp-decimals", dest="lp_decimals", type=int, default=None)
        subparser.add_argument(
            "--amount-lp-requested",
            dest="amount_lp_requested",
            type=float,
            default=None,
        )
        subparser.add_argument(
            "--rewards-token",
            dest="rewards_token",
            default="",
        )
        subparser.add_argument(
            "--balances-json",
            dest="balances_after_json",
            default="",
            help="JSON des soldes post-transaction",
        )
        subparser.add_argument("--notes", default="")
        subparser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Exécuter en mode simulation",
        )
        subparser.add_argument(
            "--dryrun",
            dest="dryrun",
            action="store_true",
            help="Alias historique de --dry-run",
        )

    stake_parser = subparsers.add_parser("stake", help="Staker des LP tokens")
    _add_common_arguments(stake_parser)

    harvest_parser = subparsers.add_parser("harvest", help="Récolter les récompenses")
    _add_common_arguments(harvest_parser)

    unstake_parser = subparsers.add_parser("unstake", help="Retirer les LP tokens")
    _add_common_arguments(unstake_parser)

    return parser


def run_cli(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command_map = {
        "stake": stake,
        "harvest": harvest,
        "unstake": unstake,
    }
    handler = command_map[args.command]
    return handler(args)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    return run_cli(argv)


if __name__ == "__main__":
    sys.exit(main())