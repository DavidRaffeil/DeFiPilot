# core/allocation_model.py – V5.2.1
from __future__ import annotations

from typing import Dict, Mapping, TypedDict

# Profils supportés dans DeFiPilot (noms canoniques)
SUPPORTED_PROFILES: tuple[str, ...] = ("Prudent", "Modere", "Risque")


class ProfileAllocationState(TypedDict):
    """
    Représente l'état d'allocation pour un profil donné.
    Toutes les valeurs sont exprimées en USD.
    """

    profil: str
    montant_actuel_usd: float
    montant_cible_usd: float
    ecart_usd: float


class MultiProfileAllocationState(TypedDict):
    """
    Représente l'état global d'allocation multi-profils pour un portefeuille.
    """

    contexte: str
    total_portefeuille_usd: float
    policy_cible: Dict[str, float]
    allocations: Dict[str, ProfileAllocationState]


# ---------------------------------------------------------------------------
# Fonctions utilitaires
# ---------------------------------------------------------------------------


def normaliser_profil(nom: str) -> str:
    """
    Normalise le nom d'un profil (gestion basique de casse et aliases simples).

    Cette fonction reste volontairement tolérante :
    - Supprime les espaces superflus en début et fin.
    - Gère quelques alias accentués ou en minuscule.
    - En cas de nom inconnu, renvoie le nom fourni sans lever d'exception.
    """

    brut = nom.strip()
    if not brut:
        return ""

    base = brut.casefold()
    base_sans_accent = (
        base.replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("ö", "o")
    )

    alias_map = {
        "prudent": "Prudent",
        "prud": "Prudent",
        "modere": "Modere",
        "modéré": "Modere",
        "moderé": "Modere",
        "modérée": "Modere",
        "moderate": "Modere",
        "risque": "Risque",
        "risky": "Risque",
    }

    if base in alias_map:
        return alias_map[base]
    if base_sans_accent in alias_map:
        return alias_map[base_sans_accent]

    for profil in SUPPORTED_PROFILES:
        if base == profil.casefold() or base_sans_accent == profil.casefold():
            return profil

    return brut


def allocation_vide(total: float = 0.0, contexte: str = "neutre") -> MultiProfileAllocationState:
    """
    Construit un état d'allocation vide pour tous les profils supportés.

    - total: montant total du portefeuille en USD.
    - contexte: label de contexte (par défaut "neutre").
    Toutes les allocations sont mises à 0.0, la policy cible est vide ({}).
    """

    allocations: Dict[str, ProfileAllocationState] = {}
    for profil in SUPPORTED_PROFILES:
        allocations[profil] = {
            "profil": profil,
            "montant_actuel_usd": 0.0,
            "montant_cible_usd": 0.0,
            "ecart_usd": 0.0,
        }

    return {
        "contexte": contexte,
        "total_portefeuille_usd": float(total),
        "policy_cible": {},
        "allocations": allocations,
    }


def _normaliser_mapping(montants: Mapping[str, float]) -> Dict[str, float]:
    """Normalise un mapping profil -> valeur en appliquant normaliser_profil."""

    resultat: Dict[str, float] = {}
    for brut, valeur in montants.items():
        profil = normaliser_profil(str(brut))
        try:
            valeur_float = float(valeur)
        except (TypeError, ValueError):
            valeur_float = 0.0

        if profil in resultat:
            resultat[profil] += valeur_float
        else:
            resultat[profil] = valeur_float

    return resultat


def construire_etat_allocation(
    total_portefeuille_usd: float,
    allocation_actuelle_usd: Mapping[str, float],
    policy_cible: Mapping[str, float],
    contexte: str,
) -> MultiProfileAllocationState:
    """
    Construit un état d'allocation complet à partir des paramètres fournis.

    La fonction :
    - normalise les noms de profils (via normaliser_profil),
    - garantit que tous les profils de SUPPORTED_PROFILES sont présents,
    - calcule montant_cible_usd = total_portefeuille_usd * pourcentage_cible,
    - calcule ecart_usd = montant_cible_usd - montant_actuel_usd,
    - retourne une structure MultiProfileAllocationState prête à être sérialisée.

    Notes :
    - Si total_portefeuille_usd <= 0, tous les montants cibles sont mis à 0.0.
    - La policy n'est pas renormalisée : les pourcentages sont utilisés tels quels.
    """

    total = float(total_portefeuille_usd)
    allocation_norm = _normaliser_mapping(allocation_actuelle_usd)
    policy_norm = _normaliser_mapping(policy_cible)

    profils_present = set(SUPPORTED_PROFILES) | set(allocation_norm.keys()) | set(policy_norm.keys())

    allocations: Dict[str, ProfileAllocationState] = {}
    for profil in sorted(
        profils_present,
        key=lambda p: SUPPORTED_PROFILES.index(p) if p in SUPPORTED_PROFILES else p,
    ):
        montant_actuel = float(allocation_norm.get(profil, 0.0))
        pourcentage_cible = float(policy_norm.get(profil, 0.0))

        montant_cible = 0.0 if total <= 0 else total * pourcentage_cible
        ecart = montant_cible - montant_actuel

        allocations[profil] = {
            "profil": profil,
            "montant_actuel_usd": montant_actuel,
            "montant_cible_usd": montant_cible,
            "ecart_usd": ecart,
        }

    return {
        "contexte": contexte,
        "total_portefeuille_usd": total,
        "policy_cible": {profil: float(policy_norm.get(profil, 0.0)) for profil in allocations},
        "allocations": allocations,
    }


def get_allocation_pour_profil(
    etat: MultiProfileAllocationState,
    profil: str,
) -> ProfileAllocationState:
    """
    Retourne l'allocation détaillée pour un profil donné à partir d'un état global.

    - profil : nom du profil (peut être en casse libre, la fonction utilise normaliser_profil).
    - Si le profil n'existe pas encore dans l'état, une structure avec des montants à 0.0 est renvoyée.
    """

    profil_normalise = normaliser_profil(profil)
    allocations = etat.get("allocations", {})
    if profil_normalise in allocations:
        return allocations[profil_normalise]

    # Profil absent : on renvoie une structure cohérente avec des montants nuls
    return {
        "profil": profil_normalise,
        "montant_actuel_usd": 0.0,
        "montant_cible_usd": 0.0,
        "ecart_usd": 0.0,
    }


__all__ = [
    "SUPPORTED_PROFILES",
    "ProfileAllocationState",
    "MultiProfileAllocationState",
    "normaliser_profil",
    "allocation_vide",
    "construire_etat_allocation",
    "get_allocation_pour_profil",
]


if __name__ == "__main__":
    # petit test manuel (sans dépendance au reste du projet)
    etat = construire_etat_allocation(
        total_portefeuille_usd=10000,
        allocation_actuelle_usd={"prudent": 3200, "Modéré": 2800},
        policy_cible={"Prudent": 0.35, "Modere": 0.45, "Risque": 0.20},
        contexte="neutre",
    )

    print("Etat complet :")
    for profil, donnees in etat["allocations"].items():
        print(
            f"- {profil}: "
            f"actuel={donnees['montant_actuel_usd']:.2f} USD, "
            f"cible={donnees['montant_cible_usd']:.2f} USD, "
            f"écart={donnees['ecart_usd']:.2f} USD"
        )

    print("\nAllocation Modere :", get_allocation_pour_profil(etat, "modéré"))
    print("Allocation Inconnu :", get_allocation_pour_profil(etat, "Inconnu"))
