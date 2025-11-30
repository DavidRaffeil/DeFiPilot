# rebalancing_cli.py — V4.6.4
from __future__ import annotations

import argparse
import json
from pathlib import Path
from pprint import pprint
from sys import exit

from core.rebalancing import calculer_plan_rebalancing
from core.journal import journaliser_rebalancing


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculer un plan de rééquilibrage à partir des derniers signaux."
    )
    parser.add_argument(
        "--signaux",
        required=True,
        help="Chemin vers le journal JSONL des signaux de marché",
    )
    parser.add_argument(
        "--portefeuille",
        required=True,
        help="Chemin vers le snapshot JSON de l'état du portefeuille",
    )
    parser.add_argument(
        "--journal",
        required=True,
        help="Chemin du journal JSONL où enregistrer le plan de rééquilibrage",
    )
    return parser.parse_args()


def verifier_entree(path: Path, description: str) -> Path:
    if not path.exists():
        print(f"Erreur : {description} introuvable à l'emplacement {path}.")
        exit(1)
    if not path.is_file():
        print(f"Erreur : {description} n'est pas un fichier : {path}.")
        exit(1)
    return path


def lire_dernier_signal(path: Path) -> dict:
    dernier = None
    try:
        with path.open("r", encoding="utf-8") as flux:
            for ligne in flux:
                ligne = ligne.strip()
                if not ligne:
                    continue
                dernier = ligne
    except OSError as exc:
        print(f"Erreur lors de la lecture des signaux : {exc}")
        exit(1)

    if dernier is None:
        print("Erreur : aucun signal disponible dans le journal fourni.")
        exit(1)

    try:
        return json.loads(dernier)
    except json.JSONDecodeError as exc:
        print(f"Erreur : impossible de décoder le dernier signal JSON ({exc}).")
        exit(1)


def charger_portefeuille(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as flux:
            return json.load(flux)
    except OSError as exc:
        print(f"Erreur lors de la lecture du portefeuille : {exc}")
        exit(1)
    except json.JSONDecodeError as exc:
        print(f"Erreur : le fichier portefeuille n'est pas un JSON valide ({exc}).")
        exit(1)


def _format_montant(montant: float | None, devise: str | None) -> str | None:
    if montant is None:
        return None
    try:
        valeur = float(montant)
    except (TypeError, ValueError):
        return None

    montant_formate = f"{valeur:,.2f}".replace(",", " ")
    if devise:
        return f"{montant_formate} {devise}"
    return montant_formate


def _extraire_total(plan: dict) -> tuple[float | None, str | None]:
    """Extrait un total et une devise potentielle depuis le plan."""
    if not isinstance(plan, dict):
        return None, None

    # Cas principal DeFiPilot : valeur_totale_usd
    valeur_totale = plan.get("valeur_totale_usd")
    if isinstance(valeur_totale, (int, float)):
        return float(valeur_totale), "USD"

    # Fallback : anciennes clés génériques éventuelles
    devise = plan.get("devise") or plan.get("currency")
    for cle in ("total", "total_value", "valeur_totale", "montant_total", "sum", "value"):
        brut = plan.get(cle)
        if isinstance(brut, (int, float)):
            return float(brut), devise

    if isinstance(plan.get("total_usd"), (int, float)):
        return float(plan["total_usd"]), "USD"

    return None, devise


def _extraire_actions(plan: dict) -> list[str]:
    """Construit une liste lisible des actions de rééquilibrage."""
    actions = plan.get("actions")
    if not isinstance(actions, list):
        return []

    resultat: list[str] = []
    for entree in actions:
        if not isinstance(entree, dict):
            continue

        # type d'action : priorités action > type > operation
        type_action = None
        for cle in ("action", "type", "operation"):
            valeur = entree.get(cle)
            if isinstance(valeur, str) and valeur.strip():
                type_action = valeur.strip()
                break

        # cible : priorités categorie > cible > asset > allocation
        cible = None
        for cle in ("categorie", "cible", "asset", "allocation"):
            valeur = entree.get(cle)
            if isinstance(valeur, str) and valeur.strip():
                cible = valeur.strip()
                break

        # montant : priorités montant_usd > montant > amount
        montant = None
        devise = None
        for cle_montant, devise_forcee in (("montant_usd", "USD"), ("montant", None), ("amount", None)):
            if cle_montant in entree:
                brut = entree.get(cle_montant)
                try:
                    montant = float(brut)
                except (TypeError, ValueError):
                    montant = None
                else:
                    devise = devise_forcee or entree.get("devise") or entree.get("currency")
                break

        montant_formate = _format_montant(montant, devise)

        morceaux = [m for m in (type_action, cible, montant_formate) if m]
        if morceaux:
            resultat.append(" ".join(morceaux))

    return resultat


def afficher_resume(plan: dict, journal_path: Path) -> None:
    """Affiche un résumé lisible du plan de rééquilibrage."""
    print("=== Plan de rééquilibrage généré ===")

    contexte = plan.get("context") or plan.get("contexte") or plan.get("market_context")
    if isinstance(contexte, str) and contexte.strip():
        print(f"Contexte : {contexte.strip()}")

    total, devise = _extraire_total(plan)
    montant_formate = _format_montant(total, devise)
    if montant_formate:
        print(f"Total   : {montant_formate}")

    actions_formatees = _extraire_actions(plan)
    print(f"Actions : {len(actions_formatees)}")
    for action in actions_formatees:
        print(f"- {action}")

    print(f"Plan enregistré dans : {journal_path}")
    print("===================================")

    print("\nDétails du plan :")
    pprint(plan)


def main() -> None:
    args = parse_arguments()

    chemin_signaux = verifier_entree(Path(args.signaux), "journal de signaux")
    chemin_portefeuille = verifier_entree(Path(args.portefeuille), "snapshot de portefeuille")
    journal_path = Path(args.journal)

    dernier_signal = lire_dernier_signal(chemin_signaux)
    etat_portefeuille = charger_portefeuille(chemin_portefeuille)

    try:
        plan = calculer_plan_rebalancing(dernier_signal, etat_portefeuille)
    except Exception as exc:  # noqa: BLE001
        print(f"Erreur lors du calcul du plan de rééquilibrage : {exc}")
        exit(1)

    try:
        journaliser_rebalancing(plan, journal_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Erreur lors de l'enregistrement du plan : {exc}")
        exit(1)

    afficher_resume(plan, journal_path)


if __name__ == "__main__":
    main()
