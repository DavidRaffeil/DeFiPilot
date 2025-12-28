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

    if isinstance(contexte, StrategyContext):
        return contexte.label, "StrategyContext"

    if isinstance(contexte, str):
        label = contexte.strip().lower()
        return (label or None), "str"

    if contexte is None:
        return None, "None"

    return None, type(contexte).__name__


def _extraire_contexte_normalise(
    signaux_normalises: Optional[List[Dict[str, Any]]],
) -> Tuple[Optional[str], Optional[float]]:
    """Extrait le label de contexte et le score IA du premier signal normalisé.

    Retourne (None, None) si :
    - la liste est vide ou None,
    - le premier élément est mal formé,
    - le flag IA est désactivé.
    """

    if not AI_PONDERATION_ACTIVE:
        return None, None

    if not signaux_normalises:
        return None, None

    premier_signal = signaux_normalises[0]
    if not isinstance(premier_signal, dict):
        return None, None

    contexte_brut = premier_signal.get("context_label")
    contexte_label = str(contexte_brut).strip().lower() if contexte_brut else None

    ai_score_brut = premier_signal.get("ai_score")
    try:
        ai_score = float(ai_score_brut) if ai_score_brut is not None else None
    except (TypeError, ValueError):
        ai_score = None


    return contexte_label or None, ai_score


def _calculer_facteur_contexte(
    context_label: Optional[str],
    ai_score: Optional[float],
) -> float:
    """Calcule un facteur multiplicatif de contexte bull/flat/bear/ai.

    Le facteur est borné dans [0.8, 1.2] pour éviter des effets extrêmes.
    """

    label = (context_label or "").strip().lower()
    if label == "bull":
        facteur = 1.10
    elif label == "bear":
        facteur = 0.90
    else:
        facteur = 1.00

    if ai_score is not None:
        try:
            modulation = 0.9 + 0.2 * float(ai_score)
            facteur *= modulation
        except (TypeError, ValueError):
            pass

    facteur_min, facteur_max = 0.8, 1.2
    facteur = max(facteur_min, min(facteur, facteur_max))
    return facteur


def calculer_scores_et_gains(
    pools: List[Dict[str, Any]],
    profil_data: Dict[str, float],
    solde: float,
    historique_pools: Optional[Dict[str, Dict[str, Any]]] = None,
    signaux: Optional[List[SignalNormalise]] = None,
    contexte: Optional[StrategyContext | ContextLabel | str] = None,
    signaux_normalises: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Tuple[Dict[str, Any], float]], float]:
    """Calcule les scores des pools avec ajustement dynamique et gains simulés.

    - Calcule un score de base pondéré par le profil (APR / TVL).
    - Applique un bonus historique éventuel (en %).
    - Ajuste le score via les signaux/contextes si l'IA est active.
    - Applique un facteur de contexte issu des signaux normalisés (optionnel).
    - Simule un gain journalier par pool via ``simuler_gains`` et cumule ``gain_total``.
    """

    contexte_label, contexte_type = _normaliser_contexte(contexte)
    LOGGER.debug(
        "Calcul des scores pour %s pool(s) avec contexte %s (label=%s).",
        len(pools),
        contexte_type,
        contexte_label,
    )

    contexte_signaux_label, contexte_ai_score = _extraire_contexte_normalise(
        signaux_normalises
    )

    resultats: List[Tuple[Dict[str, Any], float]] = []
    gain_total = 0.0

    profil_apr = float(profil_data.get("apr", 0.0))
    profil_tvl = float(profil_data.get("tvl", 0.0))

    for pool in pools:
        nom_pool = pool.get("nom") or pool.get("id") or "pool_inconnu"
        apr = float(pool.get("apr", 0.0) or 0.0)
        tvl = float(pool.get("tvl_usd", 0.0) or 0.0)

        score_base = (apr * profil_apr) + (tvl * profil_tvl)

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
            except Exception as exc:
                LOGGER.warning(
                    "Ajustement du score impossible pour le pool %s: %s",
                    nom_pool,
                    exc,
                )
                score_final = score_final_base

        if AI_PONDERATION_ACTIVE and signaux_normalises:
            facteur_contexte = _calculer_facteur_contexte(
                context_label=contexte_signaux_label,
                ai_score=contexte_ai_score,
            )
            score_apres_facteur = score_final * facteur_contexte
            LOGGER.debug(
                "Pool %s: facteur_contexte=%.3f, score ajusté de %.4f à %.4f",
                nom_pool,
                facteur_contexte,
                score_final,
                score_apres_facteur,
            )
            score_final = score_apres_facteur

        try:
            gain_texte, gain_valeur = simuler_gains(pool)
