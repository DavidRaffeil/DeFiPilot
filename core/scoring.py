# core/scoring.py – V5.1.0
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.simulateur_logique import simuler_gains
from core.config import charger_config, PROFILS
from core.scoring_adjuster import ajuster_score_pool
from core.signals_normalizer import SignalNormalise
from core.strategy_context import StrategyContext, ContextLabel

LOGGER = logging.getLogger(__name__)
AI_PONDERATION_ACTIVE = True  # flag conservé pour la suite


def charger_profil_utilisateur() -> Dict[str, float]:
    """Charge et retourne les pondérations du profil utilisateur actif."""
    config = charger_config()
    nom_profil = config.get("profil_defaut", "modere")

    if nom_profil not in PROFILS:
        LOGGER.warning(
            "Profil utilisateur '%s' introuvable, utilisation du profil 'modere'.",
            nom_profil,
        )
        nom_profil = "modere"

    profil = PROFILS.get(nom_profil)
    if profil is None:
        LOGGER.warning(
            "Profil 'modere' introuvable dans la configuration, retour d'un profil vide.",
        )
        return {}

    return profil


def _normaliser_contexte(
    contexte: Optional[StrategyContext | ContextLabel | str],
) -> Tuple[Optional[str], str]:
    """Normalise le contexte sous forme de label texte et retourne son type."""

    # Cas 1 : contexte complet de stratégie
    if isinstance(contexte, StrategyContext):
        return contexte.label, "StrategyContext"

    # Cas 2 : label déjà sous forme de chaîne ("favorable", "neutre", etc.)
    if isinstance(contexte, str):
        label = contexte.strip().lower()
        return (label or None), "str"

    # Cas 3 : aucun contexte ou type inattendu
    if contexte is None:
        return None, "None"

    return None, type(contexte).__name__


def calculer_scores_et_gains(
    pools: List[Dict[str, Any]],
    profil_data: Dict[str, float],
    solde: float,
    historique_pools: Optional[Dict[str, Dict[str, Any]]] = None,
    signaux: Optional[List[SignalNormalise]] = None,
    contexte: Optional[StrategyContext | ContextLabel | str] = None,
) -> Tuple[List[Tuple[Dict[str, Any], float]], float]:
    """Calcule les scores des pools avec ajustement dynamique et gains simulés.

    - Calcule un score de base pondéré par le profil (APR / TVL).
    - Applique un bonus historique éventuel (en %).
    - Ajuste le score via les signaux/contextes si l'IA est active.
    - Simule un gain journalier par pool via ``simuler_gains`` et cumule ``gain_total``.
    """

    contexte_label, contexte_type = _normaliser_contexte(contexte)
    LOGGER.debug(
        "Calcul des scores pour %s pool(s) avec contexte %s (label=%s).",
        len(pools),
        contexte_type,
        contexte_label,
    )

    resultats: List[Tuple[Dict[str, Any], float]] = []
    gain_total = 0.0

    profil_apr = float(profil_data.get("apr", 0.0))
    profil_tvl = float(profil_data.get("tvl", 0.0))

    for pool in pools:
        nom_pool = pool.get("nom") or pool.get("id") or "pool_inconnu"
        apr = float(pool.get("apr", 0.0) or 0.0)
        tvl = float(pool.get("tvl_usd", 0.0) or 0.0)

        # 1) Score de base pondéré par le profil
        score_base = (apr * profil_apr) + (tvl * profil_tvl)

        # 2) Bonus historique éventuel (en %)
        bonus = 0.0
        if isinstance(historique_pools, dict) and nom_pool in historique_pools:
            try:
                bonus = float(historique_pools[nom_pool].get("bonus", 0.0) or 0.0)
            except (TypeError, ValueError):
                bonus = 0.0

        score_final_base = score_base * (1 + bonus / 100.0)
        LOGGER.debug(
            "Pool %s: score_base=%.4f, bonus=%.2f%%, score_final_base=%.4f",
            nom_pool,
            score_base,
            bonus,
            score_final_base,
        )

        # 3) Ajustement dynamique via IA / signaux, si activé
        score_final = score_final_base
        if AI_PONDERATION_ACTIVE and signaux and contexte_label:
            try:
                score_final = ajuster_score_pool(
                    pool=pool,
                    score_initial=score_final_base,
                    signaux=signaux,
                    contexte=contexte_label,
                    retourner_details=False,
                )
                LOGGER.debug(
                    "Pool %s: score ajusté via IA de %.4f à %.4f (contexte=%s).",
                    nom_pool,
                    score_final_base,
                    score_final,
                    contexte_label,
                )
            except Exception as exc:  # pragma: no cover - sécurité runtime
                LOGGER.warning(
                    "Ajustement du score impossible pour le pool %s: %s",
                    nom_pool,
                    exc,
                )
                score_final = score_final_base

        # 4) Simulation de gains journaliers pour la pool
        try:
            gain_texte, gain_valeur = simuler_gains(pool)
            pool["gain_simule"] = gain_valeur
            gain_total += float(gain_valeur or 0.0)
        except Exception as exc:  # pragma: no cover - sécurité runtime
            LOGGER.warning(
                "Simulation de gains impossible pour le pool %s: %s",
                nom_pool,
                exc,
            )

        # 5) Arrondi du score final et ajout au résultat
        pool["score"] = round(score_final, 2)
        resultats.append((pool, pool["score"]))

    return resultats, gain_total
