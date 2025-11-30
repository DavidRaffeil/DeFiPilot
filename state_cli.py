# state_cli.py — V4.7.0
"""Interface CLI pour interagir avec l'état persistant de DeFiPilot."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Callable

from core.state_manager import load_state, update_state, set_balances, save_state


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Outil CLI pour inspecter et modifier l'état persistant de DeFiPilot.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser(
        "show", help="Afficher l'état complet au format JSON."
    )
    show_parser.set_defaults(func=_handle_show)

    meta_parser = subparsers.add_parser(
        "set-meta",
        help="Définir ou mettre à jour une entrée dans la section metadata.",
    )
    meta_parser.add_argument("key", help="Nom de la clé metadata à mettre à jour.")
    meta_parser.add_argument(
        "value", help="Valeur à attribuer à la clé metadata spécifiée."
    )
    meta_parser.set_defaults(func=_handle_set_meta)

    balance_parser = subparsers.add_parser(
        "set-balance",
        help="Définir ou mettre à jour le solde associé à un token donné.",
    )
    balance_parser.add_argument(
        "token", help="Symbole du token dont le solde doit être mis à jour."
    )
    balance_parser.add_argument(
        "amount",
        help="Montant numérique (float) à enregistrer pour le token spécifié.",
    )
    balance_parser.set_defaults(func=_handle_set_balance)

    return parser


def _handle_show(args: argparse.Namespace) -> int:
    del args  # Argparse imposant la signature, mais non utilisé ici.
    try:
        state = load_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover - gestion d'erreur générale
        print(
            f"Erreur lors de l'affichage de l'état : {exc}",
            file=sys.stderr,
        )
        return 1


def _handle_set_meta(args: argparse.Namespace) -> int:
    try:
        state = load_state() or {}
        metadata = state.get("metadata") if isinstance(state, dict) else None
        if not isinstance(metadata, dict):
            metadata = {}
        metadata[args.key] = args.value
        update_state({"metadata": metadata})
        save_state()
        print(f"Metadata mise à jour : {args.key}={args.value}")
        return 0
    except Exception as exc:  # pragma: no cover - gestion d'erreur générale
        print(
            f"Erreur lors de la mise à jour des métadonnées : {exc}",
            file=sys.stderr,
        )
        return 1


def _handle_set_balance(args: argparse.Namespace) -> int:
    try:
        amount = float(args.amount)
    except (TypeError, ValueError) as exc:
        print(
            f"Montant invalide '{args.amount}' : {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        state = load_state() or {}
        balances = state.get("balances") if isinstance(state, dict) else None
        if not isinstance(balances, dict):
            balances = {}
        balances[args.token] = amount
        set_balances(balances)
        save_state()
        print(f"Solde mis à jour : {args.token}={amount}")
        return 0
    except Exception as exc:  # pragma: no cover - gestion d'erreur générale
        print(
            f"Erreur lors de la mise à jour du solde : {exc}",
            file=sys.stderr,
        )
        return 1


def main(argv: list[str] | None = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(arguments)

    handler: Callable[[argparse.Namespace], int] = getattr(args, "func")
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())