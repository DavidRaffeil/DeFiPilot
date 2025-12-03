# core/allocation_policy.py – V5.2.0
from __future__ import annotations

from typing import Dict, Mapping
import logging

from core.allocation_model import SUPPORTED_PROFILES, normaliser_profil


PolicyParProfil = Dict[str, float]
"""
Représente une policy d'allocation pour un contexte donné :
mapping profil -> pourcentage cible (0.0–1.0).
"""

PolicyParContexte = Mapping[str, Mapping[str, float]]
"""
Représente la configuration des policies :
mapping contexte -> (mapping profil -> pourcentage cible).
"""


logger = logging.getLogger(__name__)


def _selectionner_policy_brute(
    contexte: str,
    policy_par_contexte: PolicyParContexte,
) -> Mapping[str, float] | None:
    """
    Sélectionne la policy brute à partir d'un label de contexte.

    - Tente d'abord une recherche directe avec la clé fournie.
    - Ensuite, utilise une version normalisée en minuscules/strip.
    - En cas d'absence, renvoie None.
    """
    ctx = contexte.strip()
    if ctx in policy_par_contexte:
        logger.debug("Policy trouvée pour le contexte exact '%s'", ctx)
        return policy_par_contexte[ctx]

    ctx_fold = ctx.casefold()
    for cle, policy in policy_par_contexte.items():
        if cle.casefold() == ctx_fold:
            logger.debug(
                "Policy trouvée pour le contexte normalisé '%s' (clé source: '%s')",
                ctx_fold,
                cle,
            )
            return policy

    logger.info("Aucune policy trouvée pour le contexte '%s'", contexte)
    return None


def extraire_policy_pour_contexte(
    contexte: str,
    policy_par_contexte: PolicyParContexte,
) -> PolicyParProfil:
    """
    Extrait et normalise la policy d'allocation pour un contexte donné.

    - contexte : label de contexte (ex: "favorable", "neutre", "defavorable").
    - policy_par_contexte : configuration globale des policies.

    La fonction :
    - tente de sélectionner la sous-policy brute pour ce contexte ;
    - si aucune policy n'est trouvée, essaie un fallback sur "neutre" ;
    - si toujours rien, renvoie une policy vide puis complète avec 0.0 ;
    - normalise les noms de profils via `normaliser_profil` ;
    - tente de caster les valeurs en float (remplace par 0.0 en cas d'erreur) ;
    - fusionne les éventuels doublons de profils normalisés en sommant les valeurs ;
    - garantit que tous les profils de SUPPORTED_PROFILES existent dans le résultat.
    """
    policy_brute = _selectionner_policy_brute(contexte, policy_par_contexte)
    if policy_brute is None:
        logger.info(
            "Fallback sur le contexte neutre faute de policy pour '%s'", contexte
        )
        policy_brute = _selectionner_policy_brute("neutre", policy_par_contexte)

    if policy_brute is None:
        logger.warning("Aucune policy disponible, utilisation d'une policy vide")
        policy_brute = {}

    resultat: PolicyParProfil = {}

    for profil_brut, valeur in policy_brute.items():
        profil_normalise = normaliser_profil(str(profil_brut)) or str(profil_brut)
        try:
            valeur_float = float(valeur)
        except (TypeError, ValueError):
            logger.warning(
                "Valeur invalide pour le profil '%s': %r (remplacement par 0.0)",
                profil_brut,
                valeur,
            )
            valeur_float = 0.0

        resultat[profil_normalise] = resultat.get(profil_normalise, 0.0) + valeur_float
        logger.debug(
            "Profil '%s' (normalisé depuis '%s') => %.3f",
            profil_normalise,
            profil_brut,
            resultat[profil_normalise],
        )

    for profil in SUPPORTED_PROFILES:
        resultat.setdefault(profil, 0.0)

    return resultat


__all__ = [
    "PolicyParProfil",
    "PolicyParContexte",
    "extraire_policy_pour_contexte",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    policies = {
        "favorable": {"Prudent": 0.2, "Modéré": 0.5, "Risque": 0.3},
        "neutre": {"prudent": 0.4, "modere": 0.4, "risque": 0.2},
    }

    for ctx in ("favorable", "neutre", "defavorable"):
        print(f"\nContexte: {ctx}")
        policy = extraire_policy_pour_contexte(ctx, policies)
        for profil, pct in policy.items():
            print(f"- {profil}: {pct:.3f}")