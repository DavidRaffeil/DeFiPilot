# liquidity_cli.py – V3.8 R9-CLI-2
"""DeFiPilot – CLI pour simuler un ajout de liquidité (dry-run seulement).

Exemples d'usage :
    python liquidity_cli.py add_liquidity --amountA 10 --amountB 0.01
    python liquidity_cli.py add_liquidity --amountA 0.5 --amountB 0.00012 --slippage-bps 50 --deadline 15
    python liquidity_cli.py add_liquidity --amountA 1 --amountB 0.001 --pool-json '{"platform":"sushiswap","chain":"polygon","router_address":"0x...","tokenA_symbol":"USDC","tokenB_symbol":"WETH","tokenA_address":"0x...","tokenB_address":"0x..."}'

Note : cette étape R9-CLI-2 gère UNIQUEMENT le dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional, List

# Import dry-run EXACT (exigé par R9-CLI-2)
from core.liquidity_dryrun import ajouter_liquidite_dryrun as add_liquidity_dryrun

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
    """Parse un JSON inline ou depuis un fichier ; retourne DEFAULT_POOL si absent.
    Lève ValueError si le contenu fourni est invalide.
    """
    if not value:
        return dict(DEFAULT_POOL)
    try:
        # JSON inline ?
        v = value.strip()
        if v.startswith("{"):
            return json.loads(v)
        # Sinon, chemin de fichier
        with open(v, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        raise ValueError(f"pool-json invalide: {exc}") from exc


def print_json(title: str, payload: Any) -> None:
    print(f"\n—— {title} ——")
    try:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    except Exception:
        print(str(payload))


# ---------------------------------------------------------------------------
# Commande: add_liquidity (dry-run)
# ---------------------------------------------------------------------------

def run_add_liquidity_dryrun(args: argparse.Namespace) -> int:
    # Lecture/validation des arguments
    try:
        amountA = float(args.amountA)
        amountB = float(args.amountB)
        if amountA <= 0 or amountB <= 0:
            raise ValueError("amountA et amountB doivent être > 0")
        slippage_bps = int(args.slippage_bps)
        # deadline conservée pour compat future, non utilisée par le dry-run
        _deadline_minutes = int(args.deadline)
        pool = parse_pool_json(args.pool_json)
    except Exception as exc:
        print_json("Args invalides", {"ok": False, "error": str(exc)})
        return 2

    # Appel du dry-run (respect strict de la signature)
    try:
        result = add_liquidity_dryrun(
            pool=pool,
            amountA=amountA,
            amountB=amountB,
            slippage_bps=slippage_bps,
        )
    except Exception as exc:
        print_json("Dry-run échoué", {"ok": False, "error": str(exc)})
        return 1

    # Sortie utilisateur
    print_json("Résultat (dry-run)", result)

    # Code de sortie basé sur clés usuelles
    ok = True
    if isinstance(result, dict):
        ok = bool(result.get("ok", result.get("success", True)))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="liquidity_cli", description="CLI DeFiPilot (dry-run)")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add_liquidity", help="Simule un ajout de liquidité (dry-run)")
    add_p.add_argument("--amountA", type=float, required=True, help="Montant du token A")
    add_p.add_argument("--amountB", type=float, required=True, help="Montant du token B")
    add_p.add_argument("--slippage-bps", type=int, default=50, help="Tolérance de slippage en basis points")
    add_p.add_argument("--deadline", type=int, default=15, help="Deadline en minutes (compat)")
    add_p.add_argument("--pool-json", type=str, help="Objet JSON inline ou chemin vers fichier JSON pour la pool")
    add_p.set_defaults(func=run_add_liquidity_dryrun)

    return parser


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
