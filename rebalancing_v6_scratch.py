from __future__ import annotations

CATEGORIES: tuple[str, str, str] = ("Prudent", "Modere", "Risque")

ALLOCATION_MATRIX: dict[str, dict[str, dict[str, float]]] = {
    "prudent": {
        "defavorable": {"Prudent": 0.70, "Modere": 0.20, "Risque": 0.10},
        "neutre": {"Prudent": 0.60, "Modere": 0.25, "Risque": 0.15},
        "favorable": {"Prudent": 0.50, "Modere": 0.30, "Risque": 0.20},
    },
    "modere": {
        "defavorable": {"Prudent": 0.50, "Modere": 0.30, "Risque": 0.20},
        "neutre": {"Prudent": 0.40, "Modere": 0.35, "Risque": 0.25},
        "favorable": {"Prudent": 0.30, "Modere": 0.40, "Risque": 0.30},
    },
    "risque": {
        "defavorable": {"Prudent": 0.35, "Modere": 0.35, "Risque": 0.30},
        "neutre": {"Prudent": 0.25, "Modere": 0.35, "Risque": 0.40},
        "favorable": {"Prudent": 0.15, "Modere": 0.30, "Risque": 0.55},
    },
}


def generer_plan_rebalancement(
    *,
    allocation_actuelle_usd: dict[str, float],
    profil: str,
    contexte: str,
    total_usd: float,
) -> dict:
    profil_normalise: str = profil.strip().lower()
    contexte_normalise: str = contexte.strip().lower()

    ratios_cibles: dict[str, float] = ALLOCATION_MATRIX[profil_normalise][contexte_normalise]
    allocation_cible_usd: dict[str, float] = {
        categorie: total_usd * ratios_cibles[categorie] for categorie in CATEGORIES
    }

    actions: list[dict[str, str | float]] = []
    for categorie in CATEGORIES:
        actuel: float = allocation_actuelle_usd.get(categorie, 0.0)
        cible: float = allocation_cible_usd[categorie]
        delta: float = cible - actuel
        if delta == 0.0:
            continue
        actions.append(
            {
                "categorie": categorie,
                "action": "augmenter" if delta > 0 else "reduire",
                "montant_usd": abs(delta),
            }
        )

    return {
        "profil": profil_normalise,
        "contexte": contexte_normalise,
        "total_usd": total_usd,
        "allocation_actuelle_usd": allocation_actuelle_usd,
        "allocation_cible_usd": allocation_cible_usd,
        "actions": actions,
    }


if __name__ == "__main__":
    exemple_allocation: dict[str, float] = {
        "Prudent": 4500.0,
        "Modere": 3000.0,
        "Risque": 2500.0,
    }
    plan: dict = generer_plan_rebalancement(
        allocation_actuelle_usd=exemple_allocation,
        profil="Modere",
        contexte="Neutre",
        total_usd=10000.0,
    )
    print(plan)