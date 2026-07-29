# run_defipilot_v6.py – V6.0

"""Launcher officiel DeFiPilot V6.0."""

from __future__ import annotations

import sys


def main() -> int:
    """Point d'entrée unique qui délègue au core d'exécution."""
    try:
        from main_v6_core import main as core_main

        return int(core_main(sys.argv[1:]))
    except Exception as exc:
        print(f"Erreur inattendue lors du lancement de DeFiPilot V6.0 : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())