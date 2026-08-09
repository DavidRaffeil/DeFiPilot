#!/usr/bin/env python3
# core/executor_real.py — V6.0.0
"""Import-safe executor for real actions (V6.0)."""

from __future__ import annotations

from typing import Any, Dict
from core.swap_reel import executer_swap_reel
from core.dry_run_guard import is_dry_run_enabled, DryRunSafetyViolation

ALLOWED_STATUSES = {"EXECUTED", "BLOCKED", "CRITICAL"}


def _normalize_verdict(verdict: Any) -> Dict[str, Any]:
    """Normalise le verdict reçu des guardrails pour garantir la conformité."""
    status = "BLOCKED"
    details: Dict[str, Any] = {}

    if isinstance(verdict, dict):
        raw_status = verdict.get("status") or verdict.get("verdict")
        if isinstance(raw_status, str) and raw_status in ALLOWED_STATUSES:
            status = raw_status
        elif "allowed" in verdict:
            status = "EXECUTED" if bool(verdict.get("allowed")) else "BLOCKED"
        elif "blocked" in verdict:
            status = "BLOCKED" if bool(verdict.get("blocked")) else "EXECUTED"

        raw_details = verdict.get("details")
        if isinstance(raw_details, dict):
            details = dict(raw_details)
    elif isinstance(verdict, bool):
        status = "EXECUTED" if verdict else "BLOCKED"
    else:
        status = "BLOCKED"

    if not details:
        details = {"reason": "guardrails_no_verdict"}

    return {"status": status, "tx_hash": None, "details": details}


def executer_action_reelle(action: dict, run_id: str) -> dict:
    """Execute a real action through guardrails or mock it if dry_run is True."""
    try:
        from core.guardrails import verifier_action_reelle
    except Exception as err:
        return {
            "status": "BLOCKED",
            "tx_hash": None,
            "details": {"reason": "guardrails_unavailable", "error": str(err)},
        }

    try:
        verdict = verifier_action_reelle(action, run_id)
    except Exception as exc:
        return {
            "status": "CRITICAL",
            "tx_hash": None,
            "details": {"reason": "guardrails_error", "error": str(exc)},
        }

    # Si le filtre de sécurité (guardrails) donne son feu vert
    if verdict.get("status") == "EXECUTED":
        kind = action.get("kind")
        
        if kind == "swap":
            is_dry = action.get("dry_run") is True or is_dry_run_enabled()
            if is_dry:
                return {
                    "status": "EXECUTED",
                    "tx_hash": None,
                    "details": {"status": "SUCCESS", "reason": "simulation_swap_ok", "mode": "[SIMULATION / DRY-RUN]"}
                }
            
            params = action.get("params", {})
            TOKENS = {
                "USDC": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
                "ETH":  "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
            }

            tokenA = TOKENS.get(params.get("tokenA"), params.get("tokenA"))
            tokenB = TOKENS.get(params.get("tokenB"), params.get("tokenB"))

            try:
                result = executer_swap_reel(
                    dex="sushiswap",
                    token_in=tokenA,
                    token_out=tokenB,
                    amount_in_wei=int(params.get("amountA", 0) * 10**6),
                    confirm=True,
                    dry_run=is_dry
                )
                return {
                    "status": "EXECUTED",
                    "tx_hash": result.get("tx_hash"),
                    "details": result
                }
            except DryRunSafetyViolation as e:
                return {
                    "status": "BLOCKED",
                    "tx_hash": None,
                    "details": {"status": "BLOCKED", "reason": "dry_run_safety_violation", "error": str(e)}
                }
            except Exception as e:
                return {
                    "status": "BLOCKED",
                    "tx_hash": None,
                    "details": {"status": "BLOCKED", "reason": "erreur_swap_reel", "error": str(e)}
                }
        
        # Pour add_liquidity, stake, etc. (actuellement non raccordés en réel)
        return {
            "status": "EXECUTED",
            "tx_hash": None,
            "details": verdict.get("details", {"reason": "guardrails_ok"})
        }

    return _normalize_verdict(verdict)
