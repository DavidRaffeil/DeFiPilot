# core/allocation_reader.py – V5.2.1
"""Lecteur d'allocation courante par profil à partir du dernier snapshot."""

from __future__ import annotations

from typing import Dict, Mapping
import logging

from core.allocation_model import SUPPORTED_PROFILES, normaliser_profil
from core.strategy_snapshot import lire_dernier_snapshot

AllocationParProfil = Dict[str, float]
"""
Représente un mapping profil -> montant en USD.
Les clés attendues sont généralement celles de SUPPORTED_PROFILES.
"""

logger = logging.getLogger(__name__)


def _allocation_vide() -> AllocationParProfil:
    """Construit une allocation nulle pour tous les profils supportés."""
    return {profil: 0.0 for profil in SUPPORTED_PROFILES}


def _normaliser_allocation_brute(
    allocation_brute: Mapping[str, float] | None,
) -> AllocationParProfil:
    """
    Convertit une allocation brute (issue du snapshot) en mapping propre profil -> float.

    - Si allocation_brute est None ou n'est pas un mapping, renvoie un dict avec tous
      les profils de SUPPORTED_PROFILES initialisés à 0.0.
    - Tente de caster chaque valeur en float, remplace par 0.0 en cas d'erreur.
    - Ne supprime pas les clés inconnues, mais garantit toujours au moins
      les profils définis dans SUPPORTED_PROFILES.
    """

    if not isinstance(allocation_brute, Mapping):
        return _allocation_vide()

    resultat: AllocationParProfil = {}

    for profil_brut, valeur in allocation_brute.items():
        profil_normalise = normaliser_profil(str(profil_brut)) or str(profil_brut)
        try:
            montant = float(valeur)
        except (TypeError, ValueError):
            montant = 0.0

        if profil_normalise in resultat:
            resultat[profil_normalise] += montant
        else:
            resultat[profil_normalise] = montant

    for profil in SUPPORTED_PROFILES:
        resultat.setdefault(profil, 0.0)

    return resultat


def lire_allocation_actuelle_usd() -> AllocationParProfil:
    """
    Lit l'allocation actuelle du portefeuille par profil à partir du dernier snapshot.

    Source de vérité :
    - core.strategy_snapshot.lire_dernier_snapshot()
    - clé attendue dans le snapshot : "allocation_actuelle_usd"

    Comportement :
    - Si le snapshot est introuvable, invalide ou ne contient pas de clé exploitable,
      retourne un mapping avec tous les profils de SUPPORTED_PROFILES à 0.0.
    - En cas d'exception, log un message au niveau WARNING et retourne aussi une
      allocation à 0.0 pour tous les profils.
    """

    try:
        snapshot = lire_dernier_snapshot()
        if not isinstance(snapshot, Mapping):
            return _allocation_vide()

        allocation_brute = snapshot.get("allocation_actuelle_usd")
        return _normaliser_allocation_brute(allocation_brute)
    except Exception as exc:  # pragma: no cover - sécurité large
        logger.warning("Impossible de lire l'allocation actuelle : %s", exc)
        return _allocation_vide()


__all__ = [
    "AllocationParProfil",
    "lire_allocation_actuelle_usd",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    allocation = lire_allocation_actuelle_usd()
    print("Allocation actuelle par profil :")
    for profil, montant in allocation.items():
        print(f"- {profil}: {montant:.2f} USD")
