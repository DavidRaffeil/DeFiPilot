# launch_controlpilot.py — V4.4.1
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from control.control_pilot import ControlPilot

"""Script de lancement de ControlPilot en mode observateur.

Il utilise par défaut les journaux journal_signaux.jsonl et journal_control.jsonl situés à la racine du projet
et expose des options en ligne de commande pour ajuster les paramètres d'exécution.
"""

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lance ControlPilot en mode observateur avec des paramètres personnalisables.")
    parser.add_argument("--input", type=str, default="journal_signaux.jsonl", help="Chemin du journal d'entrée contenant les signaux.")
    parser.add_argument("--output", type=str, default="journal_control.jsonl", help="Chemin du journal de sortie pour le suivi.")
    parser.add_argument("--interval", type=int, default=60, help="Intervalle en secondes entre deux analyses successives.")
    parser.add_argument("--max-events", type=int, default=100, help="Nombre maximal d'événements traités par passage.")
    parser.add_argument("--once", action="store_true", help="Exécute une seule analyse au lieu d'une boucle continue.")
    return parser


def run_from_args(argv: Optional[list[str]] = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(arguments)
    input_path = Path(args.input)
    output_path = Path(args.output)
    control = ControlPilot(input_path=input_path, output_path=output_path, max_events=args.max_events)
    if args.once:
        control.run_once()
    else:
        control.run_loop(interval_seconds=args.interval)
    return 0


if __name__ == "__main__":
    sys.exit(run_from_args())