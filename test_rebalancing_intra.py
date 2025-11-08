# test_rebalancing_intra.py — V4.6.1
from typing import Any, Dict, List

from core.rebalancing_intra import generer_actions_pools_depuis_plan


def scenario_nominal() -> None:
    print("=== SCÉNARIO 1 : nominal ===")
    etat_pools: List[Dict[str, Any]] = [
        {"pool_id": "R1", "categorie": "Risque", "montant_usd": 300.0, "score": 0.6},
        {"pool_id": "R2", "categorie": "Risque", "montant_usd": 100.0, "score": 0.4},
        {"pool_id": "P1", "categorie": "Prudent", "montant_usd": 150.0, "score": 0.5},
    ]

    plan: Dict[str, Any] = {
        "allocation_cible": {"Risque": 0.6, "Modere": 0.3, "Prudent": 0.1},
        "actions": [
            {"action": "augmenter", "categorie": "Risque", "montant_usd": 200.0},
            {"action": "reduire", "categorie": "Prudent", "montant_usd": 90.0},
        ],
    }

    actions = generer_actions_pools_depuis_plan(etat_pools, plan)

    for a in actions:
        print(a)

    total_risque = sum(a["delta_usd"] for a in actions if a.get("categorie") == "Risque")
    total_prudent = sum(a["delta_usd"] for a in actions if a.get("categorie") == "Prudent")

    print("Total Risque :", total_risque)
    print("Total Prudent :", total_prudent)
    print()


def scenario_bornage() -> None:
    print("=== SCÉNARIO 2 : bornage réduction ===")
    etat_pools: List[Dict[str, Any]] = [
        {"pool_id": "P1", "categorie": "Prudent", "montant_usd": 50.0, "score": 0.5},
        {"pool_id": "P2", "categorie": "Prudent", "montant_usd": 20.0, "score": 0.5},
    ]

    plan: Dict[str, Any] = {
        "allocation_cible": {"Risque": 0.6, "Modere": 0.3, "Prudent": 0.1},
        "actions": [
            {"action": "reduire", "categorie": "Prudent", "montant_usd": 200.0},
        ],
    }

    actions = generer_actions_pools_depuis_plan(etat_pools, plan)

    for a in actions:
        print(a)

    total_prudent = sum(a["delta_usd"] for a in actions if a.get("categorie") == "Prudent")
    montant_total_actuel = sum(p["montant_usd"] for p in etat_pools if p["categorie"] == "Prudent")

    print("Total Prudent (delta)      :", total_prudent)
    print("Montant actuel total Prdnt :", montant_total_actuel)
    print("Montant final théorique    :", montant_total_actuel + total_prudent)
    print()


def main() -> None:
    scenario_nominal()
    scenario_bornage()


if __name__ == "__main__":
    main()
