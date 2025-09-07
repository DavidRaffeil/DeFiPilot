# liquidity_cli.py – V3.8.2-CLI
"""DeFiPilot — CLI add_liquidity (dry-run ou réel via wrapper)

Usage (dry-run):
  python liquidity_cli.py add_liquidity \
    --dry-run \
    --amountA 10 \
    --amountB 0.01 \
    --slippage-bps 50 \
    --deadline 15 \
    --pool-json '{"platform":"sushiswap","chain":"polygon","tokenA_symbol":"USDC","tokenB_symbol":"WETH","decimalsA":6,"decimalsB":18}'

Usage (réel placeholder via wrapper):
  python liquidity_cli.py add_liquidity \
    --real \
    --amountA 0.50 \
    --amountB 0.00012 \
    --slippage-bps 50 \
    --deadline 15 \
    --pool-json '{"platform":"sushiswap","chain":"polygon","tokenA_symbol":"USDC","tokenB_symbol":"WETH","decimalsA":6,"decimalsB":18}'
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, List

# Dry-run
from core.liquidity_dryrun import simuler_ajout_liquidite
from core.journal import enregistrer_liquidite_dryrun

# Journalisation optionnelle (CSV/JSONL) — tolérant si absent ou renommé
try:
    from core.journal import enregistrer_liquidity_csv, enregistrer_liquidity_jsonl  # type: ignore
except Exception:  # pragma: no cover
    def enregistrer_liquidity_csv(*args: Any, **kwargs: Any) -> None:  # type: ignore
        pass
    def enregistrer_liquidity_jsonl(*args: Any, **kwargs: Any) -> None:  # type: ignore
        pass

# Wrapper réel moderne (pool en 1er)
try:
    from core.liquidity_real_tx import add_liquidity_real_safe  # type: ignore
except Exception:  # pragma: no cover
    add_liquidity_real_safe = None  # type: ignore


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _decimalize(value: str | float | int) -> Decimal:
    return Decimal(str(value))


def _load_pool_json(content: str) -> Dict[str, Any]:
    """Accepte soit un chemin de fichier JSON, soit une chaîne JSON inline."""
    p = Path(content)
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(content)


def _print_result(title: str, res: Any) -> None:
    print(f"\n—— {title} ——")
    try:
        print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    except Exception:
        print(res)


def _log_add_liquidity(
    platform: str,
    chain: str,
    tokenA_symbol: str,
    tokenB_symbol: str,
    amountA: Decimal,
    amountB: Decimal,
) -> None:
    ligne = {
        "platform": platform,
        "chain": chain,
        "tokenA": tokenA_symbol,
        "tokenB": tokenB_symbol,
        "amountA": float(amountA),
        "amountB": float(amountB),
    }
    try:
        enregistrer_liquidity_csv(ligne)
    except Exception:
        pass
    try:
        enregistrer_liquidity_jsonl(ligne)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Implémentations commandes
# ---------------------------------------------------------------------------

def add_liquidity_dryrun(
    pool: Dict[str, Any],
    amountA: Decimal,
    amountB: Decimal,
    slippage_bps: int,
) -> Dict[str, Any]:
    res = simuler_ajout_liquidite(
        pool=pool,
        amountA=float(amountA),
        amountB=float(amountB),
        slippage_bps=int(slippage_bps),
    )
    try:
        enregistrer_liquidite_dryrun(res)
    finally:
        pass
    return res


def run_add_liquidity(args: argparse.Namespace) -> int:
    # Lecture/validation des arguments
    mode_real = bool(args.real)
    try:
        amountA = _decimalize(args.amountA)
        amountB = _decimalize(args.amountB)
        slippage_bps = int(args.slippage_bps)
        deadline_minutes = int(args.deadline)
        deadline_seconds = deadline_minutes * 60
        pool = _load_pool_json(args.pool_json)
    except Exception as e:
        print(f"⛔ Args invalides: {e}")
        return 2

    platform = pool.get("platform", "?")
    chain = pool.get("chain", "?")
    tokenA_symbol = pool.get("tokenA_symbol", "?")
    tokenB_symbol = pool.get("tokenB_symbol", "?")

    print("================ DeFiPilot CLI ================")
    print(f"Mode: {'RÉEL' if mode_real else 'SIMULATION'}")
    print(f"Plateforme: {platform} | Réseau: {chain} | Paire: {tokenA_symbol}/{tokenB_symbol}")

    # Mode dry-run inchangé
    if not mode_real:
        try:
            result = add_liquidity_dryrun(
                pool=pool,
                amountA=amountA,
                amountB=amountB,
                slippage_bps=slippage_bps,
            )
            _print_result("Résultat (dry-run)", result)
            return 0
        except Exception as e:
            print(f"⛔ Dry-run échoué: {e}")
            return 1

    # Mode réel — via wrapper moderne (pool en 1er)
    try:
        if add_liquidity_real_safe is None:
            raise RuntimeError("add_liquidity_real_safe indisponible")
        res = add_liquidity_real_safe(
            pool=pool,
            amountA=float(amountA),
            amountB=float(amountB),
            slippage_bps=slippage_bps,
            deadline=deadline_seconds,
            dry_run=False,
        )
        success = False
        if hasattr(res, "ok"):
            success = bool(res.ok)
        elif isinstance(res, dict):
            success = bool(res.get("success"))
        if success:
            _log_add_liquidity(
                platform,
                chain,
                tokenA_symbol,
                tokenB_symbol,
                amountA,
                amountB,
            )
        _print_result("Résultat (réel)", res)
        return 0 if success else 2
    except Exception as e:
        print(f"⛔ Opération échouée: {e}")
        return 1


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="liquidity_cli",
        description="DeFiPilot — CLI add_liquidity (V3.8.2)",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add_liquidity", help="Ajouter de la liquidité")
    mx = add_parser.add_mutually_exclusive_group(required=True)
    mx.add_argument("--dry-run", action="store_true", help="Simulation sans envoi")
    mx.add_argument("--real", action="store_true", help="Transaction réelle")

    add_parser.add_argument("--amountA", type=float, required=True, help="Montant token A")
    add_parser.add_argument("--amountB", type=float, required=True, help="Montant token B")
    add_parser.add_argument("--slippage-bps", type=int, default=50, help="Tolérance slippage en basis points (50 = 0.5%)")
    add_parser.add_argument("--deadline", type=int, default=20, help="Deadline en minutes")
    add_parser.add_argument("--pool-json", type=str, required=True, help="Objet JSON décrivant la pool ou chemin de fichier JSON")

    add_parser.set_defaults(func=run_add_liquidity)
    return parser


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

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
