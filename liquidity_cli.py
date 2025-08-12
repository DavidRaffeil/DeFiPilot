# liquidity_cli.py – V3.8
# Fichier NOUVEAU – CLI dry-run pour l'ajout de liquidité (aucune transaction réelle)
# Mise à jour : support --real, --slippage-bps, --deadline-mins, --router (dry-run par défaut)

import argparse
import json
import sys
import logging
from typing import Dict, Any, Optional

try:
    from core.liquidity_real import ajouter_liquidite_reelle
except ImportError as exc:  # pragma: no cover
    print(f"Impossible d'importer ajouter_liquidite_reelle: {exc}", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)


def _build_pool(args: argparse.Namespace) -> Dict[str, Any]:
    """Construit la structure de pool à partir des arguments."""
    if args.pool_json:
        try:
            return json.loads(args.pool_json)
        except json.JSONDecodeError as exc:
            logger.error("JSON invalide fourni pour --pool-json: %s", exc)
            sys.exit(2)
    return {
        "platform": args.platform,
        "tokenA_symbol": args.tokenA,
        "tokenB_symbol": args.tokenB,
        "symbol": f"{args.tokenA}-{args.tokenB}",
    }


def _parse_arguments(argv: Optional[list[str]]) -> argparse.Namespace:
    """Définit et analyse les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="CLI pour l'ajout de liquidité (dry-run par défaut)"
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser(
        "add_liquidity", help="Ajoute de la liquidité sur un pool (dry-run par défaut)"
    )
    # Arguments conditionnels : requis seulement si --pool-json est absent
    add_parser.add_argument("--platform", type=str, help="Plateforme DeFi ciblée")
    add_parser.add_argument("--tokenA", type=str, help="Symbole du premier token")
    add_parser.add_argument("--tokenB", type=str, help="Symbole du second token")

    add_parser.add_argument("--amountA", required=True, type=float, help="Montant du premier token")
    add_parser.add_argument("--amountB", required=True, type=float, help="Montant du second token")
    add_parser.add_argument("--dest", type=str, default=None, help="Adresse destinataire des LP tokens")
    add_parser.add_argument("--pool-json", type=str, default=None, help="JSON décrivant le pool")

    # Flags mode réel
    add_parser.add_argument("--real", action="store_true", help="Exécute réellement l'ajout de liquidité")
    add_parser.add_argument("--slippage-bps", type=int, default=100, help="Slippage maximal (basis points)")
    add_parser.add_argument("--deadline-mins", type=int, default=20, help="Deadline de la transaction (minutes)")
    add_parser.add_argument("--router", type=str, default=None, help="Adresse du routeur à utiliser (override)")

    args = parser.parse_args(argv)

    if args.command == "add_liquidity" and not args.pool_json:
        if not all([args.platform, args.tokenA, args.tokenB]):
            parser.error("--platform, --tokenA et --tokenB sont requis si --pool-json est absent")

    return args


def main(argv: Optional[list[str]] = None) -> int:
    """Point d'entrée principal."""
    args = _parse_arguments(argv)

    if args.command != "add_liquidity":
        logger.error("Commande non fournie ou invalide")
        return 2

    if args.amountA <= 0 or args.amountB <= 0:
        logger.error("Les montants doivent être > 0")
        return 2

    pool = _build_pool(args)

    try:
        result: Any = ajouter_liquidite_reelle(
            pool,
            args.amountA,
            args.amountB,
            dry_run=(not args.real),
            destinataire=args.dest,
            slippage_bps=args.slippage_bps,
            deadline_mins=args.deadline_mins,
            router_override=args.router,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Erreur lors de l'ajout de liquidité")
        print(f"Erreur lors de l'ajout de liquidité: {exc}", file=sys.stderr)
        return 1

    tx_hash: Optional[str] = None
    gas_used: Optional[int] = None
    if isinstance(result, dict):
        success = bool(result.get("success"))
        message = str(result.get("message", ""))
        tx_hash = result.get("tx_hash")
        gas_used = result.get("gas_used")
    elif isinstance(result, tuple) and len(result) >= 2:
        success = bool(result[0])
        message = str(result[1])
    else:
        success = bool(result)
        message = ""

    summary = {
        "success": success,
        "platform": pool.get("platform"),
        "tokenA": pool.get("tokenA_symbol"),
        "tokenB": pool.get("tokenB_symbol"),
        "amountA": args.amountA,
        "amountB": args.amountB,
        "message": message,
    }
    if tx_hash is not None:
        summary["tx_hash"] = tx_hash
    if gas_used is not None:
        summary["gas_used"] = gas_used

    print(json.dumps(summary, ensure_ascii=False))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
