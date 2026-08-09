# core/scoring.py – Version V6.0 Multi-Facteurs
"""Module de calcul de score multi-critères des pools DeFi (V6.0).

Cette version combine de manière déterministe :
- Rendement (APR/APY) avec pénalité sur les taux excessifs/anormaux (> 1000%),
- Liquidité (TVL échelle logarithmique + tendance de croissance TVL),
- Volume 24h & turnover Volume/TVL (avec imputation si manquant),
- Facteur de risque / volatilité de la paire,
- Bonus/malus basé sur l'historique des performances.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

from core import historique


# Pondérations multi-facteurs par profil de risque
PROFILS: dict[str, dict[str, float]] = {
    "prudent": {
        "apr": 0.20,
        "tvl": 0.50,
        "volume": 0.20,
        "risk": 0.10,
        "historique_max_bonus": 0.10,
        "historique_max_malus": -0.05,
    },
    "modere": {
        "apr": 0.35,
        "tvl": 0.35,
        "volume": 0.20,
        "risk": 0.10,
        "historique_max_bonus": 0.15,
        "historique_max_malus": -0.10,
    },
    "equilibre": {
        "apr": 0.45,
        "tvl": 0.30,
        "volume": 0.15,
        "risk": 0.10,
        "historique_max_bonus": 0.20,
        "historique_max_malus": -0.10,
    },
    "dynamique": {
        "apr": 0.60,
        "tvl": 0.20,
        "volume": 0.10,
        "risk": 0.10,
        "historique_max_bonus": 0.25,
        "historique_max_malus": -0.15,
    },
    "agressif": {
        "apr": 0.75,
        "tvl": 0.10,
        "volume": 0.10,
        "risk": 0.05,
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


def _extraire_valeur_cle(pool: Mapping[str, Any], cles: list[str], default: float = 0.0) -> float:
    """Extraire la première valeur numérique trouvée pour une liste de clés alternatives."""
    if not isinstance(pool, Mapping):
        return default
    for cle in cles:
        valeur = pool.get(cle)
        if isinstance(valeur, (int, float)):
            return float(valeur)
        if isinstance(valeur, str):
            try:
                return float(valeur.strip().replace("%", ""))
            except ValueError:
                pass
    return default


def _normaliser_apr(apr_raw: float) -> float:
    """Normaliser le rendement (APR/APY).

    - Convertit le décimal en pourcentage si apr <= 5.0 (ex. 0.05 -> 5%, 2.5 -> 250%).
    - Applique une pénalité progressive sur les APRs excessifs/anormaux (> 1000%).
    """
    if apr_raw <= 0:
        return 0.0
    apr = apr_raw * 100.0 if apr_raw <= 5.0 else apr_raw

    if apr > 1000.0:
        score = 100.0 - min(50.0, (apr - 1000.0) / 100.0)
    else:
        score = min(100.0, apr)
    return max(0.0, score)


def _normaliser_tvl(tvl_usd: float, tvl_trend: float = 0.0) -> float:
    """Normaliser la TVL avec échelle logarithmique et tendance.

    Log10(max(1, TVL)) * 12.5 (1M TVL -> 75, 10M TVL -> 87.5, 100M TVL -> 100).
    """
    if tvl_usd <= 0:
        return 0.0
    score_base = min(100.0, math.log10(max(1.0, tvl_usd)) * 12.5)
    facteur_tendance = 1.0 + max(-0.10, min(0.10, tvl_trend))
    return max(0.0, min(100.0, score_base * facteur_tendance))


def _normaliser_volume(volume_24h: float, tvl_usd: float) -> float:
    """Normaliser le volume 24h avec imputation si manquant."""
    if volume_24h <= 0:
        # Imputation automatique : volume estimé à 10% de la TVL
        volume_24h = max(0.0, tvl_usd * 0.10)

    if volume_24h <= 0:
        return 0.0

    score_base = min(100.0, math.log10(max(1.0, volume_24h)) * 15.0)
    return max(0.0, score_base)


def _normaliser_risque(risk_val: float, apr_raw: float) -> float:
    """Normaliser la note de risque/volatilité (0.0 = ultra sûr, 1.0 = très risqué)."""
    if risk_val <= 0 and apr_raw > 0:
        apr_pct = apr_raw * 100.0 if apr_raw <= 1.0 else apr_raw
        risk_val = min(1.0, max(0.05, apr_pct / 200.0))
    elif risk_val <= 0:
        risk_val = 0.20

    score_secu = max(0.0, 100.0 * (1.0 - min(1.0, risk_val)))
    return score_secu


def _extraire_pool_id(pool: Mapping[str, Any] | None) -> str:
    """Extrait un identifiant stable et hashable pour une pool."""
    if not isinstance(pool, Mapping):
        return ""

    for cle in ("pool_id", "id", "address", "pool", "nom", "name", "symbols", "pair"):
        valeur = pool.get(cle)
        if isinstance(valeur, str) and valeur.strip():
            return valeur.strip()
        if valeur is not None and not isinstance(valeur, (dict, list)):
            valeur_str = str(valeur).strip()
            if valeur_str:
                return valeur_str

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
    """Retourne les pondérations associées à un profil de risque."""
    return PROFILS.get(profil_nom, PROFILS["modere"])


def charger_profil_utilisateur() -> dict[str, Any]:
    """Construit un profil utilisateur par défaut compatible avec le scoring."""
    profil_nom = "modere"
    base = PROFILS.get(profil_nom, PROFILS["modere"])
    return {
        "nom": profil_nom,
        "ponderations": {
            "apr": base["apr"],
            "tvl": base["tvl"],
            "volume": base.get("volume", 0.20),
            "risk": base.get("risk", 0.10),
        },
        "historique_max_bonus": base["historique_max_bonus"],
        "historique_max_malus": base["historique_max_malus"],
    }


def calculer_score_pool(
    pool: Mapping[str, Any],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
) -> float:
    """Calcule le score multi-facteurs d'une pool (APR, TVL, Volume, Risque, Historique)."""
    apr_raw = _extraire_valeur_cle(pool, ["apr", "apy", "rendement", "apr_pct"], default=0.0)
    tvl_raw = _extraire_valeur_cle(pool, ["tvl_usd", "tvl", "liquidity", "tvlUSD"], default=0.0)
    vol_raw = _extraire_valeur_cle(pool, ["volume_24h", "volume", "volume_usd", "volume24h"], default=0.0)
    trend_raw = _extraire_valeur_cle(pool, ["tvl_trend", "tvl_growth", "tvl_change_pct"], default=0.0)
    risk_raw = _extraire_valeur_cle(pool, ["risk_score", "volatilite", "volatility", "risk_level"], default=0.0)

    poids_apr = float(ponderations.get("apr", 0.35))
    poids_tvl = float(ponderations.get("tvl", 0.35))
    poids_vol = float(ponderations.get("volume", 0.20))
    poids_risk = float(ponderations.get("risk", 0.10))

    s_apr = _normaliser_apr(apr_raw)
    s_tvl = _normaliser_tvl(tvl_raw, trend_raw)
    s_vol = _normaliser_volume(vol_raw, tvl_raw)
    s_risk = _normaliser_risque(risk_raw, apr_raw)

    score_brut = (s_apr * poids_apr) + (s_tvl * poids_tvl) + (s_vol * poids_vol) + (s_risk * poids_risk)

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
    except Exception as exc:
        print(f"[WARN] Bonus historique ignoré pour {pool_id} : {exc}")
        bonus = 0.0

    score_final = score_brut * (1.0 + float(bonus))
    return round(score_final, 2)


def calculer_scores(
    pools: Iterable[Mapping[str, Any]],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Ajoute un score multi-facteurs à chaque pool et retourne la liste filtrée."""
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
    """Calcule le top 3 des pools et les gains estimés pour un solde donné."""
    ponderations = profil.get("ponderations") or {
        "apr": PROFILS["modere"]["apr"],
        "tvl": PROFILS["modere"]["tvl"],
        "volume": PROFILS["modere"]["volume"],
        "risk": PROFILS["modere"]["risk"],
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
        apr_pct = apr * 100.0 if apr <= 1.0 else apr
        nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
        gain = round((solde * apr_pct / 100.0) / 365.0, 2)
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
