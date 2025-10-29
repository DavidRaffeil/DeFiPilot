# core/market_signals_adapter.py — V4.2.0
"""
Adaptateur entre les signaux de marché et le moteur de stratégie.

Objectifs V4.2 :
- Rester compatible avec l'existant (signatures publiques inchangées).
- Tirer parti des métriques avancées ajoutées dans ``core.market_signals``.
- Support *optionnel* d'une policy d'allocation fournie par la config
  (mapping bull/flat/bear ou directement favorable/neutre/defavorable).
- Journal JSONL compatible GUI (écrit metrics_locales + metrics côté market_signals).

Contraintes :
- Aucune dépendance web.
- Bibliothèque standard + import de core.market_signals uniquement.
- Commentaires/docstrings en français.
"""

from __future__ import annotations

from typing import Optional, Tuple, Dict, Any, Mapping

from core.market_signals import (
    MarketParams,
    MarketDecision,
    load_params_from_config,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
)

# Mapping optionnel pour compat "bull/flat/bear" -> contexte V4.x
_CONTEXT_ALIAS: Mapping[str, str] = {
    "bull": "favorable",
    "flat": "neutre",
    "bear": "defavorable",
}


def _policy_from_cfg(context: str, cfg: Mapping[str, Any]) -> Optional[Dict[str, float]]:
    """Retourne une policy depuis la config si disponible et valide.

    La config peut fournir un bloc :
        ALLOCATION_POLICIES = {
            "bull": {"risque": 0.6, "modéré": 0.3, "prudent": 0.1},
            "flat": {...},
            "bear": {...}
        }
    ou directement :
        ALLOCATION_POLICIES = {
            "favorable": {...},
            "neutre": {...},
            "defavorable": {...}
        }
    """
    policies_cfg = cfg.get("ALLOCATION_POLICIES") if isinstance(cfg, Mapping) else None
    if not isinstance(policies_cfg, Mapping):
        return None

    # Tentative 1 : clés déjà au format contexte V4.x
    if context in policies_cfg:
        policy = policies_cfg[context]
    else:
        # Tentative 2 : alias bull/flat/bear
        # ex: context="favorable" -> alias_key="bull"
        alias_key = next((k for k, v in _CONTEXT_ALIAS.items() if v == context), None)
        if alias_key and alias_key in policies_cfg:
            policy = policies_cfg[alias_key]
        else:
            return None

    if not isinstance(policy, Mapping):
        return None

    p = {str(k): float(v) for k, v in policy.items() if k in ("risque", "modéré", "prudent")}
    total = sum(p.values())
    if total <= 0:
        return None
    # Normalise légèrement si nécessaire (tolérance petite dérive)
    if abs(total - 1.0) > 1e-9:
        p = {k: v / total for k, v in p.items()}
    return p


def calculer_contexte_et_policy(
    pools_stats: list[dict],
    cfg: dict,
    last_context: Optional[str] = None,
    run_id: Optional[str] = None,
    version: str = "V4.2.0",
    journal_path: str = "journal_signaux.jsonl",
) -> Tuple[MarketDecision, Dict[str, float]]:
    """
    Calcule la décision de contexte de marché et renvoie la policy d'allocation correspondante.

    Args:
        pools_stats: liste de dicts de stats de pools.
        cfg: configuration globale (peut contenir market_params et/ou ALLOCATION_POLICIES).
        last_context: contexte précédent pour information.
        run_id: identifiant optionnel pour traçabilité.
        version: version logique de l'exécution (ex: tag de release).
        journal_path: chemin du JSONL de journalisation.

    Returns:
        (decision, policy)
    """
    # 1) Charger les paramètres de signaux depuis cfg
    params: MarketParams = load_params_from_config(cfg)

    # 2) Détecter le contexte de marché
    decision: MarketDecision = detect_market_context(
        pools_stats=pools_stats,
        params=params,
        last_context=last_context,
    )

    # 3) Récupérer la policy associée : priorité à la config si valide, sinon valeurs par défaut
    policy = _policy_from_cfg(decision.context, cfg) or get_allocation_policy_for_context(decision.context)

    # 4) Journaliser la décision + policy
    journaliser_signaux(
        decision,
        policy,
        run_id=run_id,
        version=version,
        journal_path=journal_path,
    )

    return decision, policy
