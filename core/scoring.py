# core/scoring.py – Version V1.8 avec bonus historique
"""Module de calcul de score des pools DeFi.

Cette version combine APR, TVL et un bonus/malus basé sur l'historique.
Elle est utilisée comme base pour les versions ultérieures (V5.x / V6.x).

Fonctions principales
---------------------
- charger_ponderations(profil_nom): retourne les pondérations APR/TVL d'un profil.
- charger_profil_utilisateur(): construit un profil utilisateur par défaut.
- calculer_score_pool(): calcule le score d'une pool.
- calculer_scores(): applique le scoring à une liste de pools.
- calculer_scores_et_gains(): renvoie le top 3 et un estimateur de gains.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core import historique


# Pondérations de base par profil de risque
PROFILS: dict[str, dict[str, float]] = {
    "prudent": {
        "apr": 0.2,
        "tvl": 0.8,
        "historique_max_bonus": 0.10,
        "historique_max_malus": -0.05,
    },
    "modere": {
        "apr": 0.3,
        "tvl": 0.7,
        "historique_max_bonus": 0.15,
        "historique_max_malus": -0.10,
    },
    "equilibre": {
        "apr": 0.5,
        "tvl": 0.5,
        "historique_max_bonus": 0.20,
        "historique_max_malus": -0.10,
    },
    "dynamique": {
        "apr": 0.7,
        "tvl": 0.3,
        "historique_max_bonus": 0.25,
        "historique_max_malus": -0.15,
    },
    "agressif": {
        "apr": 0.8,
        "tvl": 0.2,
        "historique_max_bonus": 0.30,
        "historique_max_malus": -0.20,
    },
}


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convertit une valeur en float, avec valeur par défaut en cas d'échec."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extraire_pool_id(pool: Mapping[str, Any] | None) -> str:
    """Extrait un identifiant stable et hashable pour une pool.

    On privilégie les champs explicites (pool_id, id, address).
    À défaut, on reconstruit un identifiant à partir de
    (plateforme, chaîne, token0, token1, nom).
    """

    if not isinstance(pool, Mapping):
        return ""

    # 1) Identifiant explicite si disponible
    for cle in ("pool_id", "id", "address"):
        valeur = pool.get(cle)
        if isinstance(valeur, str) and valeur.strip():
            return valeur.strip()
        if valeur is not None:
            valeur_str = str(valeur).strip()
            if valeur_str:
                return valeur_str

    # 2) Construction à partir des métadonnées de la pool
    plateforme = pool.get("plateforme") or pool.get("platform")
    chaine = pool.get("chaine") or pool.get("chain")
    token0 = pool.get("token0") or pool.get("token_a") or pool.get("asset0")
    token1 = pool.get("token1") or pool.get("token_b") or pool.get("asset1")
    nom = pool.get("nom") or pool.get("name")

    elements = [plateforme, chaine, token0, token1, nom]
    elements_norm = [str(el).strip() for el in elements if el is not None and str(el).strip()]
    if not elements_norm:
        return ""
    return "|".join(elements_norm)


def charger_ponderations(profil_nom: str) -> Mapping[str, float]:
    """Retourne les pondérations associées à un profil de risque.

    Si le profil n'existe pas, on renvoie le profil "modere".
    """

    return PROFILS.get(profil_nom, PROFILS["modere"])


def charger_profil_utilisateur() -> dict[str, Any]:
    """Construit un profil utilisateur par défaut compatible avec le scoring."""

    profil_nom = "modere"
    base = PROFILS.get(profil_nom, PROFILS["modere"])
    return {
        "nom": profil_nom,
        "ponderations": {"apr": base["apr"], "tvl": base["tvl"]},
        "historique_max_bonus": base["historique_max_bonus"],
        "historique_max_malus": base["historique_max_malus"],
    }


def calculer_score_pool(
    pool: Mapping[str, Any],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
) -> float:
    """Calcule le score d'une pool en combinant APR, TVL et historique.

    - `ponderations["apr"]` et `ponderations["tvl"]` pondèrent respectivement APR et TVL.
    - `historique_pools` est transmis au module `historique` pour calculer un bonus/malus.
    - `profil` contient `historique_max_bonus` et `historique_max_malus`.
    """

    apr = _to_float(pool.get("apr"))
    tvl = _to_float(pool.get("tvl_usd"))

    poids_apr = float(ponderations.get("apr", 0.0))
    poids_tvl = float(ponderations.get("tvl", 0.0))

    score = apr * poids_apr + tvl * poids_tvl

    # Identifiant pour l'historique : on essaie d'abord l'ID technique, sinon un nom lisible
    pool_id = _extraire_pool_id(pool)
    if not pool_id:
        pool_id = f"{pool.get('plateforme')} | {pool.get('nom')}"

    try:
        bonus = historique.calculer_bonus(
            historique_pools,
            pool_id,
            max_bonus=float(profil.get("historique_max_bonus", 0.15)),
            max_malus=float(profil.get("historique_max_malus", -0.10)),
        )
    except Exception as exc:  # défense : ne jamais casser tout le scoring pour un bug d'historique
        print(f"[WARN] Bonus historique ignoré pour {pool_id} : {exc}")
        bonus = 0.0

    score *= 1.0 + float(bonus)
    return round(score, 2)


def calculer_scores(
    pools: Iterable[Mapping[str, Any]],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Ajoute un score à chaque pool et retourne la liste filtrée.

    - Ignorer les pools sans identifiant exploitable (warning).
    - En cas d'erreur sur une pool, on loggue et on continue.
    """

    pools_valides: list[dict[str, Any]] = []

    for pool in pools:
        if not isinstance(pool, Mapping):
            print("[WARN] Pool ignorée : objet non mappable.")
            continue

        pool_id = _extraire_pool_id(pool)
        if not pool_id:
            print("[WARN] Pool ignorée : identifiant introuvable.")
            continue

        try:
            score = calculer_score_pool(pool, ponderations, historique_pools, profil)
        except Exception as exc:
            print(f"[WARN] Échec scoring pool {pool_id} : {exc}")
            continue

        # On travaille sur une copie pour éviter de modifier l'objet d'origine si ce n'est pas un dict
        pool_dict = dict(pool)
        pool_dict["score"] = score
        pools_valides.append(pool_dict)

    return pools_valides


def calculer_scores_et_gains(
    pools: Iterable[Mapping[str, Any]],
    profil: Mapping[str, Any],
    solde: float,
    historique_pools: Any,
) -> tuple[list[tuple[str, float, float]], float]:
    """Calcule le top 3 des pools et les gains estimés pour un solde donné.

    Retourne :
    - une liste de tuples (nom_pool, apr, gain_journalier)
    - le gain total journalier sur le top 3
    """

    ponderations = profil.get("ponderations") or {
        "apr": PROFILS["modere"]["apr"],
        "tvl": PROFILS["modere"]["tvl"],
    }

    pools_scored = calculer_scores(pools, ponderations, historique_pools, profil)
    pools_tries = sorted(pools_scored, key=lambda p: p.get("score", 0.0), reverse=True)

    top3 = pools_tries[:3]
    resultats: list[tuple[str, float, float]] = []
    gain_total = 0.0

    for pool in top3:
        pool_id = _extraire_pool_id(pool)
        if not pool_id:
            print("[WARN] Pool ignorée dans le top3 : identifiant introuvable.")
            continue

        apr = _to_float(pool.get("apr"))
        nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
        gain = round((solde * apr / 100.0) / 365.0, 2)  # estimation de gain journalier
        resultats.append((nom, apr, gain))
        gain_total += gain

    return resultats, round(gain_total, 2)


__all__ = [
    "PROFILS",
    "charger_ponderations",
    "charger_profil_utilisateur",
    "calculer_score_pool",
    "calculer_scores",
    "calculer_scores_et_gains",
]
