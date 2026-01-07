# core/executor_real.py – V6.0
"""
Point UNIQUE d’exécution réelle V6.0.
- Applique les guardrails avant toute action on-chain.
- Délègue l’exécution aux drivers réels existants (swap, liquidity).
- Ne décide jamais de la stratégie.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.guardrails import verifier_action_reelle
from core.swap_reel import effectuer_swap_reel


def _response(
    *,
    status: str,
    action: Dict[str, Any],
    verdict_guardrails: Dict[str, Any],
    tx_hash: Optional[str],
    details: Optional[Dict[str, Any]],
    run_id: str,
) -> Dict[str, Any]:
    return {
        "status": status,
        "action": action,
        "verdict_guardrails": verdict_guardrails,
        "tx_hash": tx_hash,
        "details": details or {},
        "run_id": run_id,
    }


def _critical(
    action: Dict[str, Any],
    verdict_guardrails: Optional[Dict[str, Any]],
    details: Dict[str, Any],
    run_id: str,
) -> Dict[str, Any]:
    return _response(
        status="CRITICAL",
        action=action,
        verdict_guardrails=verdict_guardrails or {},
        tx_hash=None,
        details=details,
        run_id=run_id,
    )


def _is_dict(value: Any) -> bool:
    return isinstance(value, dict)


# Fonction publique unique
# ---------------------------------------------------------------------------

def executer_action_reelle(
    action: dict,
    exposition: dict,
    limites: dict,
    *,
    mode_execution: str,
    mode_global: str,
    exits: dict,
    run_id: str,
) -> dict:
    """
    Exécute une action réelle après validation des guardrails.

    Retour structuré:
    status, action, verdict_guardrails, tx_hash, details, run_id.
    """
    try:
        # 1) Validation minimale des paramètres
        if not all(
            [
                _is_dict(action),
                _is_dict(exposition),
                _is_dict(limites),
                _is_dict(exits),
                isinstance(mode_execution, str),
                isinstance(mode_global, str),
                isinstance(run_id, str),
            ]
        ):
            return _critical(
                action=action if _is_dict(action) else {},
                verdict_guardrails={},
                details={"reason": "invalid_parameters"},
                run_id=run_id if isinstance(run_id, str) else "",
            )

        if "type" not in action or not isinstance(action.get("type"), str):
            return _critical(
                action=action,
                verdict_guardrails={},
                details={"reason": "missing_action_type"},
                run_id=run_id,
            )

        # 2) Appel guardrails
        verdict_guardrails = verifier_action_reelle(
            mode_execution,
            mode_global,
            exits,
            action,
            exposition,
            limites,
        )

        if not _is_dict(verdict_guardrails):
            return _critical(
                action=action,
                verdict_guardrails={},
                details={"reason": "invalid_guardrails_verdict"},
                run_id=run_id,
            )

        # 3) Analyse du verdict guardrails
        guard_status = verdict_guardrails.get("status")
        if guard_status == "BLOQUE":
            return _response(
                status="BLOCKED",
                action=action,
                verdict_guardrails=verdict_guardrails,
                tx_hash=None,
                details={"reason": "guardrails_blocked"},
                run_id=run_id,
            )

        if guard_status == "BLOQUE_CRITIQUE":
            return _critical(
                action=action,
                verdict_guardrails=verdict_guardrails,
                details={"reason": "guardrails_critical"},
                run_id=run_id,
            )

        if guard_status != "AUTORISE":
            return _critical(
                action=action,
                verdict_guardrails=verdict_guardrails,
                details={"reason": "guardrails_unknown_status", "status": guard_status},
                run_id=run_id,
            )

        # 4) Dispatch d’exécution (V6.0 initial)
        action_type = action.get("type")
        if action_type == "swap":
            params = action.get("params")
            if not _is_dict(params):
                return _critical(
                    action=action,
                    verdict_guardrails=verdict_guardrails,
                    details={"reason": "missing_swap_params"},
                    run_id=run_id,
                )

            swap_result = effectuer_swap_reel(**params)
            tx_hash = None
            details: Dict[str, Any] = {"swap_result": swap_result}
            if _is_dict(swap_result):
                tx_hash = swap_result.get("tx_hash")

            return _response(
                status="EXECUTED",
                action=action,
                verdict_guardrails=verdict_guardrails,
                tx_hash=tx_hash,
                details=details,
                run_id=run_id,
            )

        return _critical(
            action=action,
            verdict_guardrails=verdict_guardrails,
            details={"reason": "unknown_action_type", "type": action_type},
            run_id=run_id,
        )

    except Exception as exc:
        return _critical(
            action=action if _is_dict(action) else {},
            verdict_guardrails={},
            details={"reason": "exception", "error": str(exc)},
            run_id=run_id if isinstance(run_id, str) else "",
        )