# core/market_signals_adapter.py – V4.0.4

"""
Adaptateur simple pour relier market_signals au moteur de stratégie.

Rôle:
- Charger les paramètres depuis un `cfg` injecté (pas d'import de core.config ici).
- Détecter le contexte de marché via detect_market_context(...).
- Mapper la policy correspondante via get_allocation_policy_for_context(...).
- Journaliser la décision en JSONL pour traçabilité.
- Retourner (decision, policy) afin que l'appelant ajuste ses allocations.

Contrats:
- Aucune dépendance web.
- Bibliothèque standard + import de core.market_signals uniquement.
- Commentaires/docstrings en français.
"""

from typing import Optional, Tuple, Dict, Any
from core.market_signals import (
    MarketParams,
    MarketDecision,
    load_params_from_config,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
)


def calculer_contexte_et_policy(
    pools_stats: list[dict],
    cfg: dict,
    last_context: Optional[str] = None,
    run_id: Optional[str] = None,
    version: str = "V4.0.4",
    journal_path: str = "journal_signaux.jsonl",
) -> Tuple[MarketDecision, Dict[str, float]]:
    """
    Calcule la décision de contexte de marché et renvoie la policy d'allocation correspondante.

    Args:
        pools_stats: liste de dicts contenant au minimum:
            - "apr_change_pct": float|None
            - "tvl_change_pct": float|None
        cfg: dictionnaire de configuration global contenant au moins:
            - "MARKET_SIGNALS": {...}
            - "ALLOCATION_POLICIES": {"bull": {...}, "flat": {...}, "bear": {...}}
        last_context: contexte précédent ("bull"|"flat"|"bear"|None) pour stabiliser les bascules si cooldown actif.
        run_id: identifiant optionnel pour tracer l'exécution dans le journal.
        version: version logique de l'exécution (ex: tag de release).
        journal_path: chemin du JSONL de journalisation.

    Returns:
        (decision, policy) où:
            - decision: MarketDecision (context, score, indicators, reason)
            - policy: dict normalisé {"risque": x, "modéré": y, "prudent": z} (somme=1.0)

    Raises:
        KeyError/ValueError si la configuration de policy est manquante ou invalide.
    """
    # 1) Charger les paramètres de signaux depuis cfg
    params: MarketParams = load_params_from_config(cfg)

    # 2) Détecter le contexte de marché
    decision: MarketDecision = detect_market_context(
        pools_stats=pools_stats,
        params=params,
        last_context=last_context,
    )

    # 3) Récupérer la policy associée
    policies_cfg: Dict[str, Any] = cfg.get("ALLOCATION_POLICIES", {})
    policy: Dict[str, float] = get_allocation_policy_for_context(decision.context, policies_cfg)

    # 4) Journaliser la décision (append JSONL)
    journaliser_signaux(decision, run_id=run_id, version=version, path_jsonl=journal_path)

    return decision, policy