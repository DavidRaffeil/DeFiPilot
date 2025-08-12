# liquidity_cli.py – V3.8
# Fichier NOUVEAU – CLI dry-run pour l'ajout de liquidité (aucune transaction réelle)
# Mise à jour : arguments conditionnels quand --pool-json est fourni (dry-run)

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
    parser = argparse.ArgumentParser(description="CLI dry-run pour l'ajout de liquidité")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser(
        "add_liquidity", help="Simule l'ajout de liquidité (dry-run)"
    )
    # Ces trois arguments sont conditionnels (obligatoires seulement si --pool-json est absent)
    add_parser.add_argument("--platform", type=str, help="Plateforme DeFi ciblée")
    add_parser.add_argument("--tokenA", type=str, help="Symbole du premier token")
    add_parser.add_argument("--tokenB", type=str, help="Symbole du second token")

    add_parser.add_argument("--amountA", required=True, type=float, help="Montant du premier token")
    add_parser.add_argument("--amountB", required=True, type=float, help="Montant du second token")
    add_parser.add_argument("--dest", type=str, default=None, help="Adresse destinataire des LP tokens")
    add_parser.add_argument("--pool-json", type=str, default=None, help="JSON décrivant le pool")

    args = parser.parse_args(argv)

    if args.command == "add_liquidity":
        # Si pas de --pool-json, alors platform/tokenA/tokenB doivent être fournis
        if not args.pool_json:
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
            dry_run=True,
            destinataire=args.dest,
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Erreur lors de l'ajout de liquidité")
        print(f"Erreur lors de l'ajout de liquidité: {exc}", file=sys.stderr)
        return 1

    if isinstance(result, dict):
        success = bool(result.get("success"))
        message = str(result.get("message", ""))
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
    print(json.dumps(summary, ensure_ascii=False))

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
