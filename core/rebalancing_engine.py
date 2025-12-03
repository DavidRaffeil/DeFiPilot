# core/rebalancing_engine.py – V5.2.0
from __future__ import annotations

from typing import Any, Mapping
import logging

from core.strategy_snapshot import lire_dernier_snapshot
from core.allocation_reader import AllocationParProfil, lire_allocation_actuelle_usd
from core.allocation_policy import PolicyParContexte, extraire_policy_pour_contexte
from core.allocation_model import MultiProfileAllocationState, construire_etat_allocation
from core.rebalancing_simulator import RebalancePlan, calculer_plan_reequilibrage

logger = logging.getLogger(__name__)


def _detecter_contexte_snapshot(snapshot: Mapping[str, Any] | None) -> str:
    """
    Tente d'extraire un label de contexte à partir d'un snapshot.

    Clés potentiellement utilisées (dans l'ordre) :
    - "context"
    - "contexte"
    - "context_label"

    Si aucune n'est disponible ou exploitable, retourne "neutre".
    """
    if not isinstance(snapshot, Mapping):
        return "neutre"

    for cle in ("context", "contexte", "context_label"):
        valeur = snapshot.get(cle)
        if valeur:
            return str(valeur)

    return "neutre"


def _detecter_total_portefeuille(
    snapshot: Mapping[str, Any] | None,
    allocation: AllocationParProfil,
) -> float:
    """
    Détermine un montant total de portefeuille en USD.

    Stratégie :
    - Tente d'abord de lire une clé "solde_reference_usd" dans le snapshot.
    - Si non disponible ou non numérique, utilise la somme des montants de `allocation`.
    """
    if isinstance(snapshot, Mapping) and "solde_reference_usd" in snapshot:
        try:
            valeur = float(snapshot["solde_reference_usd"])
            return valeur
        except (TypeError, ValueError):
            logger.debug("Clé solde_reference_usd non exploitable dans le snapshot", exc_info=True)

    return float(sum(allocation.values()))


def preparer_plan_reequilibrage_depuis_snapshot(
    policy_par_contexte: PolicyParContexte,
    seuil_min: float = 0.0,
) -> RebalancePlan:
    """
    Prépare un plan de rééquilibrage à partir du dernier snapshot et de la policy.

    Étapes :
    - Lit le dernier snapshot via `lire_dernier_snapshot()`.
    - Lit l'allocation actuelle du portefeuille via `lire_allocation_actuelle_usd()`.
    - Détecte le contexte de marché à partir du snapshot.
    - Extrait la policy d'allocation cible pour ce contexte.
    - Détermine un total de portefeuille en USD (snapshot ou somme de l'allocation).
    - Construit un MultiProfileAllocationState via `construire_etat_allocation`.
    - Calcule un RebalancePlan via `calculer_plan_reequilibrage`.
    - Retourne ce plan.

    En cas de problème majeur (snapshot illisible, policy vide, etc.), retourne
    un plan cohérent mais vide (total_a_deplacer_usd = 0.0, actions = []).
    """
    contexte = "neutre"
    try:
        snapshot = lire_dernier_snapshot()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Impossible de lire le dernier snapshot : %s", exc)
        snapshot = {}

    allocation = lire_allocation_actuelle_usd()
    contexte = _detecter_contexte_snapshot(snapshot)

    if not policy_par_contexte:
        logger.warning("Policy par contexte vide, retour d'un plan vide")
        return RebalancePlan(
            contexte=contexte,
            total_a_deplacer_usd=0.0,
            actions=[],
        )

    policy = extraire_policy_pour_contexte(contexte, policy_par_contexte)
    if not policy:
        logger.warning("Policy introuvable pour le contexte %s, retour d'un plan vide", contexte)
        return RebalancePlan(
            contexte=contexte,
            total_a_deplacer_usd=0.0,
            actions=[],
        )

    if all((isinstance(v, (int, float)) and float(v) == 0.0) for v in policy.values()):
        logger.info("Policy pour le contexte %s est entièrement à 0.0", contexte)

    total_portefeuille = _detecter_total_portefeuille(snapshot, allocation)

    try:
        etat: MultiProfileAllocationState = construire_etat_allocation(
            total_portefeuille,
            allocation,
            policy,
            contexte,
        )
        plan = calculer_plan_reequilibrage(etat, seuil_min=seuil_min)
        return plan
    except Exception as exc:  # noqa: BLE001
        logger.warning("Erreur lors de la préparation du plan de rééquilibrage : %s", exc)
        return RebalancePlan(
            contexte=contexte,
            total_a_deplacer_usd=0.0,
            actions=[],
        )


__all__ = [
    "preparer_plan_reequilibrage_depuis_snapshot",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Exemple de policy simple pour test manuel
    policies = {
        "favorable": {"Prudent": 0.2, "Modere": 0.5, "Risque": 0.3},
        "neutre": {"Prudent": 0.4, "Modere": 0.4, "Risque": 0.2},
    }

    plan = preparer_plan_reequilibrage_depuis_snapshot(
        policy_par_contexte=policies,
        seuil_min=1.0,
    )

    print("Contexte :", plan["contexte"])
    print("Total à déplacer (USD) :", plan["total_a_deplacer_usd"])
    print("Actions :")
    for action in plan["actions"]:
        print(
            f"- {action['from_profil']} -> {action['to_profil']}: "
            f"{action['montant_usd']:.2f} USD"
        )