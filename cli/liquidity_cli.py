# liquidity_cli.py – V3.8.19
"""CLI DeFiPilot pour ajouter de la liquidité (dry-run ou réel).

Correctifs V3.8.19 :
- Appel dry-run : suppression du paramètre `dry_run` passé à `ajouter_liquidite_dryrun()`.
- Correction de la création du sous-parseur (utilisation de `add_parser` au lieu de `add_parsedocumenter`).
- Messages d'erreur JSON uniformes.

Rappels:
- Importer les fonctions EXACTES depuis les modules existants du dépôt.
- Respect strict des noms/signatures et de la casse.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any, Dict

# Imports EXACTS (ne pas modifier les chemins/noms)
from core.execution.liquidity_dryrun import (
    ajouter_liquidite_dryrun as add_liquidity_dryrun,
)
from core.execution.liquidity_real_tx import (
    add_liquidity_real_safe,
)


def _print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="liquidity_cli.py",
        description="DeFiPilot – CLI d'ajout de liquidité (dry-run / réel)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add_liquidity",
        help="Ajouter de la liquidité (dry-run ou réel)",
    )

    add_parser.add_argument(
        "--amountA",
        type=float,
        required=True,
        help="Montant du token A (ex: USDC)",
    )
    add_parser.add_argument(
        "--amountB",
        type=float,
        required=True,
        help="Montant du token B (ex: WETH)",
    )
    add_parser.add_argument(
        "--slippage-bps",
        type=int,
        default=50,
        help="Slippage toléré en basis points (par défaut: 50 = 0,50%)",
    )
    add_parser.add_argument(
        "--deadline",
        type=int,
        default=20,
        help="Deadline (minutes) avant expiration (par défaut: 20)",
    )
    add_parser.add_argument(
        "--pool-json",
        type=str,
        required=True,
        help=(
            "JSON décrivant la pool. Ex: '{""platform"":""sushiswap"",""chain"":""polygon"","
            '""tokenA_symbol"":""USDC"",""tokenB_symbol"":""WETH""}'
        ),
    )

    mode = add_parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Exécuter en simulation (aucune transaction réelle)",
    )
    mode.add_argument(
        "--real",
        action="store_true",
        help="Exécuter en mode réel (envoi de transaction)",
    )

    return parser


def cmd_add_liquidity(args: argparse.Namespace) -> int:
    try:
        pool = json.loads(args.pool_json)
    except Exception as e:  # JSON invalide
        _print_json({
            "ok": False,
            "error": f"pool-json invalide: {e}",
        })
        return 2

    amountA = float(args.amountA)
    amountB = float(args.amountB)
    slippage_bps = int(args.slippage_bps)
    deadline = int(args.deadline)

    try:
        if args.dry_run or not args.real:
            # —— MODE DRY-RUN ——
            # ⚠️ Ne PAS passer 'dry_run' ici : la fonction n'accepte pas ce paramètre
            result = add_liquidity_dryrun(
                pool,
                amountA,
                amountB,
                slippage_bps=slippage_bps,
            )
            # Normaliser la sortie
            out = {
                "ok": bool(result.get("success", True)),
                **result,
            }
            _print_json(out)
            return 0 if out.get("ok") else 1
        else:
            # —— MODE RÉEL ——
            result = add_liquidity_real_safe(
                pool,
                amountA,
                amountB,
                slippage_bps=slippage_bps,
                deadline=deadline,
                dry_run=False,
            )
            out = {
                "ok": bool(result.get("success", False)),
                **result,
            }
            _print_json(out)
            return 0 if out.get("ok") else 1

    except Exception as e:
        # Erreur générique : renvoyer le message attendu par les scripts appelants
        _print_json({
            "ok": False,
            "error": f"Erreur lors de l'exécution: {e}",
            "trace": traceback.format_exc(),
        })
        return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add_liquidity":
        return cmd_add_liquidity(args)

    # Commande inconnue (ne devrait pas arriver car `required=True`)
    _print_json({"ok": False, "error": "Commande inconnue"})
    return 2


if __name__ == "__main__":
    sys.exit(main())
