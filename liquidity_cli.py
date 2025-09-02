# liquidity_cli.py – V3.8 R10-CLI-Real-Exec
"""
DeFiPilot — CLI d'ajout de liquidité (R10)
FR: Exécution réelle activée avec confirmation explicite. Dry-run inchangé.
EN: Real execution enabled behind explicit confirmation. Dry-run unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

# ------------------------------ Imports -------------------------------------
# Dry-run exact import (keep alias for CLI coherence)
from core.liquidity_dryrun import simuler_ajout_liquidite as add_liquidity_dryrun
# Journalisation CSV (alias conservé pour compatibilité interne)
from core.journal import enregistrer_liquidity_csv as enregistrer_liquidite_dryrun

# Real execution wrapper — optional depending on repo state
try:
    from core.liquidity_real_tx import add_liquidity_real_safe  # type: ignore
except Exception:  # module may not exist yet; keep CLI usable
    add_liquidity_real_safe = None  # type: ignore


# ------------------------------ Helpers ------------------------------------

def _parse_pool_json(raw: str) -> Dict[str, Any]:
    """Parse et valide un objet JSON décrivant la pool."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"pool-json invalide: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("pool-json doit être un objet JSON")
    return data


# ------------------------------ Commands -----------------------------------

def cmd_selftest(_: argparse.Namespace) -> int:
    ok_dry = callable(add_liquidity_dryrun)
    ok_real = (add_liquidity_real_safe is not None)
    if ok_dry and ok_real:
        print("[V3.8] ✅ Imports OK: add_liquidity_dryrun & add_liquidity_real_safe")
        return 0
    if ok_dry and not ok_real:
        print("[V3.8] ⚠️ Import dry-run OK ; import real optionnel absent (normal si module non présent)")
        return 0
    print("[V3.8] ❌ Import dry-run manquant")
    return 2


def cmd_add_liquidity(args: argparse.Namespace) -> int:
    # Exclusivité des modes
    if args.dry_run and args.real:
        print("[V3.8] ⚠️ Conflit: --dry-run et --real ne peuvent pas être utilisés ensemble")
        return 2

    # Validations de base
    if args.amountA <= 0 or args.amountB <= 0:
        print("[V3.8] ⚠️ Échec: amountA et amountB doivent être > 0")
        return 2
    if args.slippage_bps < 0:
        print("[V3.8] ⚠️ Échec: slippage-bps doit être >= 0")
        return 2

    # Parse du JSON de pool
    try:
        pool = _parse_pool_json(args.pool_json)
    except ValueError as exc:
        print(f"[V3.8] ⚠️ Erreur parsing pool: {exc}")
        return 2

    # Mode DRY-RUN (par défaut si --real n'est pas fourni)
    if args.dry_run or not args.real:
        try:
            res = add_liquidity_dryrun(
                pool=pool,
                amountA=float(args.amountA),
                amountB=float(args.amountB),
                slippage_bps=int(args.slippage_bps),
            )
        except Exception as exc:
            print(f"[V3.8] ❌ Dry-run a échoué: {exc}")
            return 1
        # Journalisation best-effort
        try:
            enregistrer_liquidite_dryrun(res)
        except Exception as jexc:
            print(f"[V3.8] ⚠️ Journalisation dry-run échouée: {jexc}")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    # Mode RÉEL (exécution effective)
    # Vérifications préalables
    if add_liquidity_real_safe is None:
        print("[V3.8] ❌ Mode réel indisponible: add_liquidity_real_safe introuvable")
        return 2
    if args.confirm != "ADD_LIQUIDITY":
        print('[V3.8] ⚠️ Sécurité: utilisez --confirm "ADD_LIQUIDITY" avec --real')
        return 2

    # Appel protégé
    try:
        res_real = add_liquidity_real_safe(
            pool=pool,
            amountA=float(args.amountA),
            amountB=float(args.amountB),
            slippage_bps=int(args.slippage_bps),
        )
    except Exception as exc:
        print(f"[V3.8] ❌ Échec mode réel: {exc}")
        return 1

    # Affichage brut du dict renvoyé par le wrapper (ne pas inventer de champs)
    print(json.dumps(res_real, ensure_ascii=False, indent=2))
    return 0


# ------------------------------ Parser -------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="liquidity_cli",
        description="DeFiPilot — CLI add_liquidity (V3.8 R10-CLI-Real-Exec)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="DeFiPilot liquidity CLI V3.8 R10-CLI-Real-Exec",
    )

    subparsers = parser.add_subparsers(dest="command")

    # selftest
    p_self = subparsers.add_parser("selftest", help="Vérifie les imports (dry-run & real)")
    p_self.set_defaults(func=cmd_selftest)

    # add_liquidity
    p_add = subparsers.add_parser("add_liquidity", help="Ajouter de la liquidité")
    mode = p_add.add_mutually_exclusive_group(required=False)
    mode.add_argument("--dry-run", action="store_true", help="Simulation sans envoi (par défaut)")
    mode.add_argument("--real", action="store_true", help="Transaction réelle (confirm requise)")
    p_add.add_argument("--amountA", type=float, required=True, help="Montant token A")
    p_add.add_argument("--amountB", type=float, required=True, help="Montant token B")
    p_add.add_argument("--slippage-bps", type=int, default=50, help="Tolérance slippage en bps (50 = 0.5%)")
    p_add.add_argument("--pool-json", type=str, required=True, help="Objet JSON décrivant la pool")
    p_add.add_argument("--confirm", type=str, default="", help="Confirmation explicite pour le mode réel")
    p_add.set_defaults(func=cmd_add_liquidity)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
