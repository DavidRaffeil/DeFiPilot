#!/usr/bin/env python3
# swap_cli.py - V3.7
"""
DeFiPilot — CLI de swap réel (Polygon, SushiSwap V2)

FR : Lance un swap réel via la fonction `effectuer_swap_reel` (slippage, approve auto, confirmation).
EN : Run a real swap via `effectuer_swap_reel` (slippage, auto-approve, confirmation).

Exemples :
  Dry-run (aucun envoi) :
    python swap_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --dry-run

  Envoi réel (confirmation explicite) :
    python swap_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --confirm
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

try:
    from core.swap_reel import effectuer_swap_reel
except Exception as exc:  # pragma: no cover - import fallback
    effectuer_swap_reel = None  # type: ignore

def main(argv: list[str] | None = None) -> int:
    if effectuer_swap_reel is None:
        print(json.dumps({"status": "error", "error": "effectuer_swap_reel indisponible"}, ensure_ascii=False))
        return 1

    p = argparse.ArgumentParser(description="DeFiPilot – Swap réel (Polygon, SushiSwap V2)")
    p.add_argument("--dex", default="sushiswap_v2")
    p.add_argument("--token-in", required=True, help="Adresse checksum du token entrant")
    p.add_argument("--token-out", required=True, help="Adresse checksum du token sortant")
    p.add_argument("--amount-in-wei", type=int, required=True, help="Montant entrant en wei du token_in")
    p.add_argument("--slippage-bps", type=int, default=50, help="Slippage en basis points (50 = 0.50%)")
    p.add_argument("--confirm", action="store_true", default=False, help="Exécuter réellement la transaction")
    p.add_argument("--dry-run", action="store_true", default=False, help="Ne pas envoyer, juste prévisualiser")
    args = p.parse_args(argv)

    try:
        result: dict[str, Any] = effectuer_swap_reel(
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
        if status == "error":
            return 2
        return 0
    except Exception as exc:  # pragma: no cover - generic CLI exception handler
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1

if __name__ == "__main__":
    sys.exit(main())