#!/usr/bin/env python3
# test_swap_reel_cli.py - V3.7

import argparse
import json
import sys

from core.swap_reel import effectuer_swap_reel


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DeFiPilot – Swap réel (Polygon, SushiSwap V2)"
    )
    parser.add_argument("--dex", default="sushiswap_v2")
    parser.add_argument("--token-in", required=True, help="Adresse checksum du token entrant")
    parser.add_argument("--token-out", required=True, help="Adresse checksum du token sortant")
    parser.add_argument("--amount-in-wei", type=int, required=True, help="Montant entrant en wei du token_in")
    parser.add_argument("--slippage-bps", type=int, default=50, help="Slippage en basis points (50 = 0.50%)")
    parser.add_argument("--confirm", action="store_true", default=False, help="Exécuter réellement la transaction")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Ne pas envoyer, juste prévisualiser")
    args = parser.parse_args()

    try:
        result = effectuer_swap_reel(
            dex=args.dex,
            token_in=args.token_in,
            token_out=args.token_out,
            amount_in_wei=args.amount_in_wei,
            slippage_bps=args.slippage_bps,
            require_confirmation=not args.confirm,
            confirm=args.confirm,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        status = result.get("status", "")
        if status == "awaiting_confirmation":
            print("En attente de confirmation…")
            return 0
        if status == "error":
            print("Erreur lors du swap.")
            return 2
        print("Swap exécuté avec succès.")
        return 0
    except Exception as exc:  # pragma: no cover - generic CLI exception handler
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
