# core/scoring.py — V5.5.0

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from core import historique
from core.scoring_adjuster import ajuster_score_pool
from core.signals_normalizer import SignalNormalise


PROFILS: Dict[str, Dict[str, float]] = {
    "prudent": {"apr": 0.2, "tvl": 0.8, "historique_max_bonus": 0.10, "historique_max_malus": -0.05},
    "modere": {"apr": 0.3, "tvl": 0.7, "historique_max_bonus": 0.15, "historique_max_malus": -0.10},
    "equilibre": {"apr": 0.5, "tvl": 0.5, "historique_max_bonus": 0.20, "historique_max_malus": -0.10},
    "dynamique": {"apr": 0.7, "tvl": 0.3, "historique_max_bonus": 0.25, "historique_max_malus": -0.15},
    "agressif": {"apr": 0.8, "tvl": 0.2, "historique_max_bonus": 0.30, "historique_max_malus": -0.20},
}


def charger_ponderations(profil_nom: str) -> Dict[str, float]:
    return PROFILS.get(profil_nom, PROFILS["modere"])


def charger_profil_utilisateur() -> Dict[str, Any]:
    profil_nom = "modere"
    base = PROFILS.get(profil_nom, PROFILS["modere"])
    return {
        "nom": profil_nom,
        "ponderations": {"apr": base["apr"], "tvl": base["tvl"]},
        "historique_max_bonus": base["historique_max_bonus"],
        "historique_max_malus": base["historique_max_malus"],
    }


def calculer_score_pool(
    pool: Dict[str, Any],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
    signaux: Optional[List[SignalNormalise]] = None,
    contexte: str = "",
    mode_v5_5: Optional[str] = None,
    strategy_cfg: Optional[Mapping[str, Any]] = None,
) -> float:
    apr = pool.get("apr", 0)
    tvl = pool.get("tvl_usd", 0)

    try:
        apr_f = float(apr)
    except (TypeError, ValueError):
        apr_f = 0.0

    try:
        tvl_f = float(tvl)
    except (TypeError, ValueError):
        tvl_f = 0.0

    score = (apr_f * float(ponderations.get("apr", 0.0))) + (tvl_f * float(ponderations.get("tvl", 0.0)))

    nom_pool = f"{pool.get('plateforme')} | {pool.get('nom')}"
    bonus = historique.calculer_bonus(
        historique_pools,
        nom_pool,
        max_bonus=float(profil.get("historique_max_bonus", 0.15)),
        max_malus=float(profil.get("historique_max_malus", -0.10)),
    )
    score *= (1 + float(bonus))

    signaux_effectifs: List[SignalNormalise] = signaux if isinstance(signaux, list) else []
    score_final = ajuster_score_pool(
        pool=pool,
        score_initial=float(score),
        signaux=signaux_effectifs,
        contexte=contexte or "",
        retourner_details=False,
        mode_v5_5=mode_v5_5,
        strategy_cfg=strategy_cfg,
    )

    try:
        return round(float(score_final), 2)
    except Exception:
        return 0.0


def calculer_scores(
    pools: List[Dict[str, Any]],
    ponderations: Mapping[str, float],
    historique_pools: Any,
    profil: Mapping[str, Any],
    signaux: Optional[List[SignalNormalise]] = None,
    contexte: str = "",
    mode_v5_5: Optional[str] = None,
    strategy_cfg: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    for pool in pools:
        pool["score"] = calculer_score_pool(
            pool=pool,
            ponderations=ponderations,
            historique_pools=historique_pools,
            profil=profil,
            signaux=signaux,
            contexte=contexte,
            mode_v5_5=mode_v5_5,
            strategy_cfg=strategy_cfg,
        )
    return pools


def calculer_scores_et_gains(
    pools: List[Dict[str, Any]],
    profil: Mapping[str, Any],
    solde: float,
    historique_pools: Any,
    signaux: Optional[List[SignalNormalise]] = None,
    contexte: str = "",
    mode_v5_5: Optional[str] = None,
    strategy_cfg: Optional[Mapping[str, Any]] = None,
) -> Tuple[List[Tuple[str, Any, float]], float]:
    ponderations = profil.get("ponderations", {})
    pools = calculer_scores(
        pools=pools,
        ponderations=ponderations,
        historique_pools=historique_pools,
        profil=profil,
        signaux=signaux,
        contexte=contexte,
        mode_v5_5=mode_v5_5,
        strategy_cfg=strategy_cfg,
    )

    pools_tries = sorted(pools, key=lambda p: p.get("score", 0), reverse=True)

    top3 = pools_tries[:3]
    resultats: List[Tuple[str, Any, float]] = []
    gain_total = 0.0

    try:
        solde_f = float(solde)
    except (TypeError, ValueError):
        solde_f = 0.0

    for pool in top3:
        apr = pool.get("apr", 0)
        try:
            apr_f = float(apr)
        except (TypeError, ValueError):
            apr_f = 0.0

        nom = f"{pool.get('plateforme')} | {pool.get('nom')}"
        gain = round((solde_f * apr_f / 100.0) / 365.0, 2)
        resultats.append((nom, apr, gain))
        gain_total += float(gain)

    return resultats, round(gain_total, 2)
