# core/rebalancing_simulator.py – V5.2.0
from __future__ import annotations

from typing import List, TypedDict
import logging

from core.allocation_model import MultiProfileAllocationState, SUPPORTED_PROFILES

logger = logging.getLogger(__name__)

# Utilisé pour signaler explicitement la dépendance et éviter les avertissements d'import.
_SUPPORTED_PROFILES_REFERENCE = SUPPORTED_PROFILES


class RebalanceAction(TypedDict):
    """
    Représente un transfert théorique de montant entre deux profils.
    """

    from_profil: str
    to_profil: str
    montant_usd: float


class RebalancePlan(TypedDict):
    """
    Plan complet de rééquilibrage pour un état d'allocation donné.
    """

    contexte: str
    total_a_deplacer_usd: float
    actions: List[RebalanceAction]


def _valider_etat(etat: MultiProfileAllocationState | None) -> bool:
    """
    Vérifie que l'état fournit bien une structure minimale.
    Retourne False et loggue un avertissement en cas d'anomalie.
    """

    if etat is None:
        logger.warning("Etat d'allocation absent : plan vide retourné.")
        return False
    if not isinstance(etat, dict):
        logger.warning("Etat d'allocation invalide (doit être un dictionnaire) : plan vide retourné.")
        return False
    return True


def calculer_plan_reequilibrage(
    etat: MultiProfileAllocationState,
    seuil_min: float = 0.0,
) -> RebalancePlan:
    """
    Calcule un plan de rééquilibrage entre profils à partir d'un état d'allocation.

    - etat : MultiProfileAllocationState issu de core.allocation_model.construire_etat_allocation.
    - seuil_min : seuil en USD en dessous duquel un écart est considéré comme négligeable.

    Logique :
    - Identifie les profils en SURPLUS (écart < -seuil_min) et en DÉFICIT (écart > seuil_min),
      où l'écart est défini comme montant_cible_usd - montant_actuel_usd.
    - Génère une liste d'actions RebalanceAction en transférant des montants depuis les
      profils en surplus vers ceux en déficit.
    - Chaque action a un montant_usd = min(|écart_surplus|, écart_deficit).
    - Met à jour les écarts locaux utilisés pour la construction du plan jusqu'à ce que
      l'un des deux (surplus ou déficit) soit épuisé (tous < seuil_min en valeur absolue).
    - Calcule total_a_deplacer_usd comme la somme des montants_usd de toutes les actions.
    """

    if not _valider_etat(etat):
        return {
            "contexte": "",
            "total_a_deplacer_usd": 0.0,
            "actions": [],
        }

    contexte = etat.get("contexte", "")
    allocations = etat.get("allocations", {})

    if not isinstance(allocations, dict) or not allocations:
        logger.warning("Aucune allocation fournie : plan vide retourné.")
        return {
            "contexte": contexte,
            "total_a_deplacer_usd": 0.0,
            "actions": [],
        }

    surplus: List[list] = []
    deficits: List[list] = []

    for profil in sorted(allocations):
        allocation = allocations.get(profil) or {}
        montant_cible = float(allocation.get("montant_cible_usd", 0.0))
        montant_actuel = float(allocation.get("montant_actuel_usd", 0.0))
        ecart = montant_cible - montant_actuel

        if ecart < -seuil_min:
            surplus.append([profil, ecart])
        elif ecart > seuil_min:
            deficits.append([profil, ecart])

    actions: List[RebalanceAction] = []

    i_surplus = 0
    i_deficit = 0

    while i_surplus < len(surplus) and i_deficit < len(deficits):
        profil_surplus, ecart_surplus = surplus[i_surplus]
        profil_deficit, ecart_deficit = deficits[i_deficit]

        manque = ecart_deficit
        dispo = -ecart_surplus
        montant = min(manque, dispo)

        if montant <= seuil_min:
            if ecart_surplus >= -seuil_min:
                i_surplus += 1
            if ecart_deficit <= seuil_min:
                i_deficit += 1
            if montant <= seuil_min and (ecart_surplus < -seuil_min and ecart_deficit > seuil_min):
                # Sécurité : évite une boucle infinie si seuil_min est mal réglé.
                break
            continue

        actions.append(
            RebalanceAction(
                from_profil=profil_surplus,
                to_profil=profil_deficit,
                montant_usd=montant,
            )
        )

        ecart_surplus += montant
        ecart_deficit -= montant

        surplus[i_surplus][1] = ecart_surplus
        deficits[i_deficit][1] = ecart_deficit

        if ecart_surplus >= -seuil_min:
            i_surplus += 1
        if ecart_deficit <= seuil_min:
            i_deficit += 1

    total_a_deplacer = sum(action["montant_usd"] for action in actions)

    return {
        "contexte": contexte,
        "total_a_deplacer_usd": total_a_deplacer,
        "actions": actions,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    from core.allocation_model import construire_etat_allocation

    etat = construire_etat_allocation(
        total_portefeuille_usd=10000.0,
        allocation_actuelle_usd={"Prudent": 5000.0, "Modere": 3000.0, "Risque": 2000.0},
        policy_cible={"Prudent": 0.4, "Modere": 0.4, "Risque": 0.2},
        contexte="neutre",
    )

    plan = calculer_plan_reequilibrage(etat, seuil_min=1.0)
    print("Contexte:", plan["contexte"])
    print("Total à déplacer (USD):", plan["total_a_deplacer_usd"])
    print("Actions :")
    for action in plan["actions"]:
        print(
            f"- {action['from_profil']} -> {action['to_profil']}: "
            f"{action['montant_usd']:.2f} USD"
        )


__all__ = [
    "RebalanceAction",
    "RebalancePlan",
    "calculer_plan_reequilibrage",
]