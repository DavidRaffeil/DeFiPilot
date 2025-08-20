# liquidity_cli.py – V3.8 (corrigé final, cohérent avec liquidity_dryrun)
"""CLI DeFiPilot — Ajout de liquidité (dry-run ou réel placeholder)

Usage (dry-run):
    python liquidity_cli.py add_liquidity \
        --dry-run \
        --amountA 10 \
        --amountB 0.01 \
        --slippage-bps 50 \
        --pool-json '{"platform":"sushiswap","chain":"polygon","tokenA_symbol":"USDC","tokenB_symbol":"WETH","reservesA":1000000,"reservesB":1000,"decimalsA":6,"decimalsB":18,"totalSupplyLP":50000}'

Notes:
- Le mode réel est un placeholder en V3.8.
- STDLib uniquement. Aucune dépendance externe.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Dict, Optional, List

from core.liquidity_dryrun import simuler_ajout_liquidite
from core.journal import enregistrer_liquidite_dryrun


def _parse_pool_json(s: str) -> Dict[str, Any]:
    try:
        data = json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"pool-json invalide: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("pool-json doit être un objet JSON")
    return data


def cmd_add_liquidity(args: argparse.Namespace) -> int:
    dry_run = True if (args.dry_run or not args.real) else False

    if args.amountA <= 0 or args.amountB <= 0:
        print("[V3.8] ⚠️ Échec: amountA et amountB doivent être > 0")
        return 2
    if args.slippage_bps < 0:
        print("[V3.8] ⚠️ Échec: slippage-bps doit être >= 0")
        return 2

    try:
        pool = _parse_pool_json(args.pool_json)
    except ValueError as e:
        print(f"[V3.8] ⚠️ Erreur parsing pool: {e}")
        return 2

    if dry_run:
        res = simuler_ajout_liquidite(
            pool=pool,
            amountA=float(args.amountA),
            amountB=float(args.amountB),
            slippage_bps=int(args.slippage_bps),
        )
        enregistrer_liquidite_dryrun(res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if not dry_run and args.confirm != "ADD_LIQUIDITY":
        print('[V3.8] ⚠️ Sécurité: utilisez --confirm "ADD_LIQUIDITY" avec --real')
        return 2

    print("[V3.8] Mode réel non encore implémenté dans cette version")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="liquidity_cli",
        description="DeFiPilot — CLI add_liquidity (V3.8)"
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add_liquidity", help="Ajouter de la liquidité")
    mx = add_parser.add_mutually_exclusive_group(required=True)
    mx.add_argument("--dry-run", action="store_true", help="Simulation sans envoi")
    mx.add_argument("--real", action="store_true", help="Transaction réelle")

    add_parser.add_argument("--amountA", type=float, required=True, help="Montant token A")
    add_parser.add_argument("--amountB", type=float, required=True, help="Montant token B")
    add_parser.add_argument("--pool-json", type=str, required=True, help="Objet JSON décrivant la pool")
    add_parser.add_argument("--slippage-bps", type=int, default=50, help="Tolérance slippage en basis points (50 = 0.5%)")
    add_parser.add_argument("--confirm", type=str, default="", help="Confirmation explicite en mode réel")

    add_parser.set_defaults(func=cmd_add_liquidity)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
