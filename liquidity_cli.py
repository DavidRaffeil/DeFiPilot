# liquidity_cli.py – V3.8 R9-CLI-3
"""DeFiPilot — CLI add_liquidity (dry-run ou réel via wrapper)

Exemples d'usage :
  # Dry-run
  python liquidity_cli.py add_liquidity --dry-run --amountA 10 --amountB 0.01
  # Réel (wrapper simple)
  python liquidity_cli.py add_liquidity --real --amountA 0.50 --amountB 0.00012 --slippage-bps 50 --deadline 15 \
    --pool-json '{"platform":"sushiswap","chain":"polygon","router_address":"0x...","tokenA_symbol":"USDC","tokenB_symbol":"WETH","tokenA_address":"0x...","tokenB_address":"0x..."}'

Note : cette étape R9-CLI-3 conserve le dry-run intact et ajoute un mode réel simple s'appuyant sur add_liquidity_real_safe.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional, List

# Import dry-run EXACT (exigé)
from core.liquidity_dryrun import ajouter_liquidite_dryrun as add_liquidity_dryrun

# Import wrapper réel (tolérant si absent)
try:
    from core.liquidity_real_tx import add_liquidity_real_safe  # type: ignore
except Exception:  # pragma: no cover
    add_liquidity_real_safe = None  # type: ignore

# Pool par défaut si --pool-json non fourni (placeholders sûrs)
DEFAULT_POOL: Dict[str, Any] = {
    "platform": "sushiswap",
    "chain": "polygon",
    "router_address": "0x0000000000000000000000000000000000000000",
    "tokenA_symbol": "USDC",
    "tokenB_symbol": "WETH",
    "tokenA_address": "0x0000000000000000000000000000000000000000",
    "tokenB_address": "0x0000000000000000000000000000000000000000",
}


def parse_pool_json(value: Optional[str]) -> Dict[str, Any]:
    """Parse un JSON inline ou depuis un fichier ; retourne DEFAULT_POOL si absent."""
    if not value:
        return dict(DEFAULT_POOL)
    try:
        v = value.strip()
        if v.startswith("{"):
            return json.loads(v)
        with open(v, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        raise ValueError(f"pool-json invalide: {exc}") from exc


def print_json(title: str, payload: Any) -> None:
    print(f"\\n—— {title} ——")
    try:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    except Exception:
        print(str(payload))


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

def run_add_liquidity_dryrun(args: argparse.Namespace) -> int:
    try:
        amountA = float(args.amountA)
        amountB = float(args.amountB)
        if amountA <= 0 or amountB <= 0:
            raise ValueError("amountA et amountB doivent être > 0")
        slippage_bps = int(args.slippage_bps)
        _ = int(args.deadline)
        pool = parse_pool_json(args.pool_json)
    except Exception as exc:
        print_json("Args invalides", {"ok": False, "error": str(exc)})
        return 2
    try:
        result = add_liquidity_dryrun(pool=pool, amountA=amountA, amountB=amountB, slippage_bps=slippage_bps)
    except Exception as exc:
        print_json("Dry-run échoué", {"ok": False, "error": str(exc)})
        return 1
    print_json("Résultat (dry-run)", result)
    ok = True
    if isinstance(result, dict):
        ok = bool(result.get("ok", result.get("success", True)))
    return 0 if ok else 1


def run_add_liquidity_real(args: argparse.Namespace) -> int:
    try:
        amountA = float(args.amountA)
        amountB = float(args.amountB)
        if amountA <= 0 or amountB <= 0:
            raise ValueError("amountA et amountB doivent être > 0")
        slippage_bps = int(args.slippage_bps)
        deadline_minutes = int(args.deadline)
        pool = parse_pool_json(args.pool_json)
    except Exception as exc:
        print_json("Args invalides", {"ok": False, "error": str(exc)})
        return 2
    if add_liquidity_real_safe is None:
        print_json("Erreur", {"ok": False, "error": "add_liquidity_real_safe indisponible"})
        return 1
    try:
        res = add_liquidity_real_safe(pool, amountA, amountB)
    except Exception as exc:
        print_json("Opération échouée", {"ok": False, "error": str(exc)})
        return 1
    print_json("Résultat (réel)", res)
    success = True
    if hasattr(res, "ok"):
        success = bool(getattr(res, "ok"))
    elif isinstance(res, dict):
        success = bool(res.get("ok", res.get("success", True)))
    else:
        success = bool(res)
    return 0 if success else 2


def run_add_liquidity(args: argparse.Namespace) -> int:
    if getattr(args, "real", False):
        return run_add_liquidity_real(args)
    return run_add_liquidity_dryrun(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liquidity_cli", description="DeFiPilot — CLI add_liquidity (V3.8 R9-CLI-3)")
    subparsers = parser.add_subparsers(dest="command")
    add_parser = subparsers.add_parser("add_liquidity", help="Ajouter de la liquidité (dry-run ou réel)")
    mx = add_parser.add_mutually_exclusive_group(required=True)
    mx.add_argument("--dry-run", action="store_true", help="Simulation sans envoi")
    mx.add_argument("--real", action="store_true", help="Transaction réelle via wrapper")
    add_parser.add_argument("--amountA", type=float, required=True, help="Montant token A")
    add_parser.add_argument("--amountB", type=float, required=True, help="Montant token B")
    add_parser.add_argument("--slippage-bps", type=int, default=50, help="Tolérance slippage en basis points (50 = 0.5%)")
    add_parser.add_argument("--deadline", type=int, default=15, help="Deadline en minutes")
    add_parser.add_argument("--pool-json", type=str, help="Objet JSON décrivant la pool ou chemin de fichier JSON")
    add_parser.set_defaults(func=run_add_liquidity)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
