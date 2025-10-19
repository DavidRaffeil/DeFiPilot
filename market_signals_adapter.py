from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING

from core.market_signals import (
    load_params_from_config,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
)

if TYPE_CHECKING:
    from core.market_signals import MarketParams, MarketDecision


def calculer_contexte_et_policy(
    pools_stats: list[dict],
    cfg: dict,
    last_context: Optional[str] = None,
    run_id: Optional[str] = None,
    version: str = "V4.0.4",
    journal_path: str = "journal_signaux.jsonl",
) -> Tuple["MarketDecision", Dict[str, Any]]:
    """
    Calcule le contexte de marché et la politique d'allocation associée.
    Étapes :
    1) Charger les paramètres depuis cfg.
    2) Détecter le contexte (favorable / neutre / défavorable).
    3) Récupérer la policy correspondante.
    4) Journaliser la décision complète.
    5) Retourner (decision, policy).
    """

    # Validations élémentaires
    assert isinstance(pools_stats, list), "pools_stats doit être une liste de dictionnaires"
    assert isinstance(cfg, dict), "cfg doit être un dictionnaire"
    if last_context is not None:
        assert isinstance(last_context, str), "last_context doit être une chaîne ou None"
    if run_id is not None:
        assert isinstance(run_id, str), "run_id doit être une chaîne ou None"
    assert isinstance(version, str), "version doit être une chaîne"
    assert isinstance(journal_path, str), "journal_path doit être une chaîne"

    # Pipeline
    params: "MarketParams" = load_params_from_config(cfg)
    decision: "MarketDecision" = detect_market_context(
        pools_stats,
        params,
        last_context=last_context,
    )
    policy: Dict[str, Any] = get_allocation_policy_for_context(decision.context)

    # Journalisation
    journaliser_signaux(
        decision=decision,
        params=params,
        policy=policy,
        run_id=run_id,
        version=version,
        journal_path=journal_path,
    )

    return decision, policy