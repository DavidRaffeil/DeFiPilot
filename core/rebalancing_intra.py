# core/rebalancing_intra.py — V4.6.1
"""Module de transformation d'un plan de rééquilibrage catégoriel en ajustements théoriques par pool."""

from typing import Any, Dict, List


def _as_float(value: Any) -> float:
    """Convertit une valeur vers un flottant sans lever d'exception en cas d'erreur."""

    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _filtrer_pools_par_categorie(etat_pools: List[Dict[str, Any]], categorie: str) -> List[Dict[str, Any]]:
    """Retourne une copie superficielle des pools appartenant à la catégorie demandée."""

    return [dict(pool) for pool in etat_pools if pool.get("categorie") == categorie]


def _calculer_poids(pools: List[Dict[str, Any]]) -> List[float]:
    """Calcule les poids relatifs pour une liste de pools en s'appuyant sur les scores tronqués à zéro."""

    scores = [max(_as_float(pool.get("score")), 0.0) for pool in pools]
    total = sum(scores)
    if not pools:
        return []
    if total > 0.0:
        return [score / total for score in scores]
    poids_uniforme = 1.0 / len(pools)
    return [poids_uniforme for _ in pools]


def repartir_delta_intra_categorie(
    etat_pools: List[Dict[str, Any]],
    categorie: str,
    action: str,
    montant_usd: float,
) -> List[Dict[str, Any]]:
    """Répartit un ajustement intra-catégorie entre les pools concernées.

    Paramètres
    ----------
    etat_pools : liste de dictionnaires décrivant les pools simulées, dont les clés utilisées sont
        "pool_id", "categorie", "montant_usd" et "score".
    categorie : catégorie cible pour l'ajustement.
    action : type d'ajustement, doit valoir "augmenter" ou "reduire".
    montant_usd : montant positif associé à l'action de la catégorie.

    Retours
    -------
    Une liste de dictionnaires représentant des deltas par pool contenant "pool_id", "categorie",
    "delta_usd", "source" et "meta". Le champ "meta" inclut "action_categorie", "montant_categorie"
    et "poids_relatif".

    Notes
    -----
    Les poids relatifs utilisent les scores tronqués à zéro. Si la somme des scores est nulle, une
    répartition uniforme est appliquée. Pour une action de réduction, un delta ne peut pas dépasser le
    montant investi courant d'une pool et un bornage est alors appliqué, ce qui peut induire un écart
    entre la somme finale des deltas et le montant demandé.
    """

    if montant_usd <= 0.0:
        return []
    action_normalisee = action.lower()
    if action_normalisee not in {"augmenter", "reduire"}:
        raise ValueError("Action attendue: 'augmenter' ou 'reduire'.")
    pools_categorie = _filtrer_pools_par_categorie(etat_pools, categorie)
    if not pools_categorie:
        return []
    poids = _calculer_poids(pools_categorie)
    resultats: List[Dict[str, Any]] = []
    bornage_effectue = False
    for index, pool in enumerate(pools_categorie):
        poids_relatif = poids[index]
        delta = montant_usd * poids_relatif
        if action_normalisee == "reduire":
            delta = -delta
            montant_actuel = max(_as_float(pool.get("montant_usd")), 0.0)
            if abs(delta) > montant_actuel:
                delta = -montant_actuel
                bornage_effectue = True
        resultats.append(
            {
                "pool_id": pool.get("pool_id"),
                "categorie": pool.get("categorie"),
                "delta_usd": delta,
                "source": "rebalancing_intra_categorie",
                "meta": {
                    "action_categorie": action_normalisee,
                    "montant_categorie": montant_usd,
                    "poids_relatif": poids_relatif,
                },
            }
        )
    if resultats and action_normalisee == "augmenter":
        total_delta = sum(item["delta_usd"] for item in resultats)
        difference = montant_usd - total_delta
        resultats[-1]["delta_usd"] += difference
    if resultats and action_normalisee == "reduire" and not bornage_effectue:
        total_delta = sum(item["delta_usd"] for item in resultats)
        difference = -montant_usd - total_delta
        resultats[-1]["delta_usd"] += difference
    return resultats


def generer_actions_pools_depuis_plan(
    etat_pools: List[Dict[str, Any]],
    plan: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Transforme un plan de rééquilibrage catégoriel en liste d'actions par pool.

    Paramètres
    ----------
    etat_pools : liste de dictionnaires représentant l'état simulé des pools.
    plan : dictionnaire contenant une clé "actions" listant des ajustements catégoriels de la forme
        {"action": str, "categorie": str, "montant_usd": float}.

    Retours
    -------
    Une liste concaténée de dictionnaires issus de l'appel à `repartir_delta_intra_categorie` pour
    chacune des actions valides du plan. Les actions dont le montant est nul ou négatif sont ignorées,
    tout comme celles visant une catégorie sans pool correspondante.
    """

    actions_plan = plan.get("actions", [])
    resultats: List[Dict[str, Any]] = []
    for action_plan in actions_plan:
        montant = _as_float(action_plan.get("montant_usd"))
        if montant <= 0.0:
            continue
        categorie = action_plan.get("categorie")
        action_type = action_plan.get("action", "")
        if not isinstance(categorie, str) or not isinstance(action_type, str):
            continue
        resultats.extend(
            repartir_delta_intra_categorie(
                etat_pools=etat_pools,
                categorie=categorie,
                action=action_type,
                montant_usd=montant,
            )
        )
    return resultats