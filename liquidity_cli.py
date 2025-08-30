# liquidity_cli.py — Patch 3/5 (garde-fous exécution réelle) – V3.8.1
# ✅ FICHIER COMPLET
# Ce fichier contient maintenant l'intégralité du patch 3/5 :
# - Ajout des flags CLI (--send et --confirm)
# - Fonction validate_real_execution()
# - Documentation d'intégration et messages utilisateurs

from __future__ import annotations
import os, sys
from typing import Optional
import argparse

# Création du parser principal
parser = argparse.ArgumentParser(description="Outil de gestion de liquidité DeFiPilot")
subparsers = parser.add_subparsers(dest="command")

# Sous-commande add_liquidity
add_liq_parser = subparsers.add_parser("add_liquidity", help="Ajouter de la liquidité")
add_liq_parser.add_argument("--amountA", type=float, required=True, help="Montant du token A")
add_liq_parser.add_argument("--amountB", type=float, required=True, help="Montant du token B")
add_liq_parser.add_argument("--dry-run", action="store_true", help="Mode simulation, pas d'envoi réel")
add_liq_parser.add_argument("--send", action="store_true", help="Exécute EN RÉEL (sinon dry-run)")
add_liq_parser.add_argument("--confirm", type=str, default="", help="Texte de confirmation explicite. Exiger 'ADD_LIQUIDITY'")

# Fonction pour vérifier les variables d'environnement
def _env_var_present(*names: str) -> bool:
    for n in names:
        v = os.getenv(n)
        if v and v.strip():
            return True
    return False

# Fonction de validation avant envoi réel
def validate_real_execution(*, is_dry_run: bool, send_flag: bool, confirm_text: str,
                            expected_confirm: str = "ADD_LIQUIDITY",
                            chain_hint: Optional[str] = None) -> None:
    if is_dry_run:
        return

    if not send_flag:
        print("Refusé: exécution réelle sans --send.\nAjoutez --send pour autoriser l'envoi.", file=sys.stderr)
        raise SystemExit(2)

    if confirm_text != expected_confirm:
        print(f"Refusé: confirmation invalide. Attendu: {expected_confirm!r}.\nUtilisez: --confirm \"{expected_confirm}\"", file=sys.stderr)
        raise SystemExit(2)

    has_rpc = _env_var_present("POLYGON_RPC_URL", "RPC_POLYGON", "RPC_URL", "RPC")
    if not has_rpc:
        hint = f" pour la chaîne {chain_hint}" if chain_hint else ""
        print(f"Refusé: aucune variable RPC détectée{hint}. Définissez-la dans .env", file=sys.stderr)
        raise SystemExit(2)

    if not _env_var_present("PRIVATE_KEY", "WALLET_PRIVATE_KEY"):
        print("Refusé: aucune PRIVATE_KEY détectée dans .env.", file=sys.stderr)
        raise SystemExit(2)

# Exemple d'utilisation (à placer dans la fonction qui gère add_liquidity)
def execute_add_liquidity(args):
    validate_real_execution(
        is_dry_run=args.dry_run,
        send_flag=args.send,
        confirm_text=args.confirm,
        expected_confirm="ADD_LIQUIDITY",
        chain_hint="polygon"
    )
    if args.dry_run:
        print("[DRY-RUN] Ajout de liquidité simulé.")
    else:
        print("[RÉEL] Ajout de liquidité lancé.")

# Main
def main():
    args = parser.parse_args()
    if args.command == "add_liquidity":
        execute_add_liquidity(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
