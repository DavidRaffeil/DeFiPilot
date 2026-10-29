#!/usr/bin/env python3
# core/executor_real.py — V6.5.0
"""Import-safe executor for real actions with Multi-DEX routing support (V6.5)."""

from __future__ import annotations

from decimal import Decimal
import logging
import os
from typing import Any, Dict, Optional

import core.config as app_config
from core.dex.base import DEXQuote
from core.dex.factory import create_default_dex_router
from core.dex.router import DEXRouter
from core.dry_run_guard import DryRunSafetyViolation, is_dry_run_enabled
from core.swap_reel import (
    DEFAULT_SWAP_RECIPIENT,
    _run_coro_sync,
    executer_swap_reel,
    resolve_token_address,
)

logger = logging.getLogger("core.executor_real")

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


def _resolve_multi_dex_swap(
    token_in: str,
    token_out: str,
    amount_in: float | Decimal,
    slippage_pct: float = 0.5,
    dex_router: Optional[DEXRouter] = None,
    web3_client: Optional[Any] = None,
    feature_multi_dex: Optional[bool] = None,
    recipient: Optional[str] = None,
    default_dex: str = "sushiswap",
) -> tuple[str, Optional[DEXQuote], Optional[Dict[str, Any]]]:
    """
    Tente d'obtenir la meilleure route via `DEXRouter` et de construire la transaction.
    En cas d'inactivité du flag ou d'erreur, retourne `(default_dex, None, None)`.
    """
    enabled = (
        app_config.FEATURE_MULTI_DEX
        if feature_multi_dex is None
        else bool(feature_multi_dex)
    )
    if not enabled or (dex_router is None and web3_client is None):
        return default_dex, None, None

    try:
        router = dex_router or create_default_dex_router(web3_client)
        t_in = resolve_token_address(token_in)
        t_out = resolve_token_address(token_out)
        amt_dec = Decimal(str(amount_in))
        slip_dec = Decimal(str(slippage_pct)) / Decimal("100")

        best_quote = _run_coro_sync(
            router.get_best_quote(
                token_in=t_in,
                token_out=t_out,
                amount_in=amt_dec,
                slippage_tolerance=slip_dec,
            )
        )
        logger.info(
            "[MULTI-DEX] DEX retenu : %s | Montant espéré : %s (min: %s, gas: %s)",
            best_quote.dex_name,
            best_quote.expected_amount_out,
            best_quote.min_amount_out,
            best_quote.estimated_gas,
        )
        target_recipient = (
            recipient
            or os.environ.get("WALLET_ADDRESS")
            or DEFAULT_SWAP_RECIPIENT
        )
        tx = _run_coro_sync(
            router.build_swap_transaction(best_quote, target_recipient)
        )
        return best_quote.dex_name, best_quote, tx
    except Exception as exc:
        logger.warning(
            "[MULTI-DEX] Échec du routage multi-DEX (%s), repli sur '%s'",
            exc,
            default_dex,
        )
        return default_dex, None, None


def executer_action_reelle(
    action: dict,
    run_id: str,
    dex_router: Optional[DEXRouter] = None,
    web3_client: Optional[Any] = None,
    feature_multi_dex: Optional[bool] = None,
) -> dict:
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
            params = action.get("params", {})
            TOKENS = {
                "USDC": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
                "ETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            }

            raw_token_a = params.get("tokenA", "USDC")
            raw_token_b = params.get("tokenB", "ETH")
            tokenA = TOKENS.get(raw_token_a, resolve_token_address(str(raw_token_a)))
            tokenB = TOKENS.get(raw_token_b, resolve_token_address(str(raw_token_b)))
            amount_a = params.get("amountA", 0)
            slippage_pct = float(params.get("max_slippage_pct", 0.5))
            default_dex = str(params.get("dex") or "sushiswap")

            already_routed = (
                "dex" in params
                and "expected_amount_out" in params
                and "tx" in params
            )
            if already_routed:
                selected_dex = str(params["dex"])
                best_quote = None
                built_tx = params["tx"]
            else:
                selected_dex, best_quote, built_tx = _resolve_multi_dex_swap(
                    token_in=tokenA,
                    token_out=tokenB,
                    amount_in=amount_a,
                    slippage_pct=slippage_pct,
                    dex_router=dex_router,
                    web3_client=web3_client,
                    feature_multi_dex=feature_multi_dex,
                    recipient=params.get("recipient"),
                    default_dex=default_dex,
                )

            is_dry = action.get("dry_run") is True or is_dry_run_enabled()
            if is_dry:
                sim_details: Dict[str, Any] = {
                    "status": "SUCCESS",
                    "reason": "simulation_swap_ok",
                    "mode": "[SIMULATION / DRY-RUN]",
                    "dex": selected_dex,
                }
                if best_quote is not None:
                    sim_details["expected_amount_out"] = str(
                        best_quote.expected_amount_out
                    )
                    sim_details["min_amount_out"] = str(best_quote.min_amount_out)
                    sim_details["estimated_gas"] = best_quote.estimated_gas
                    sim_details["multi_dex"] = True
                elif already_routed:
                    sim_details["expected_amount_out"] = str(
                        params["expected_amount_out"]
                    )
                    if "min_amount_out" in params:
                        sim_details["min_amount_out"] = str(params["min_amount_out"])
                    if "estimated_gas" in params:
                        sim_details["estimated_gas"] = params["estimated_gas"]
                    sim_details["multi_dex"] = True
                if built_tx is not None:
                    sim_details["tx"] = built_tx
                elif "tx" in params:
                    sim_details["tx"] = params["tx"]

                return {
                    "status": "EXECUTED",
                    "tx_hash": None,
                    "details": sim_details,
                }

            try:
                result = executer_swap_reel(
                    dex=selected_dex,
                    token_in=tokenA,
                    token_out=tokenB,
                    amount_in_wei=int(float(amount_a) * 10**6),
                    confirm=True,
                    dry_run=is_dry,
                    slippage_pct=slippage_pct,
                    dex_router=dex_router if best_quote is None else None,
                    web3_client=web3_client if best_quote is None else None,
                    feature_multi_dex=(
                        False if best_quote is not None else feature_multi_dex
                    ),
                )
                if best_quote is not None:
                    result["dex"] = selected_dex
                    result["expected_amount_out"] = str(best_quote.expected_amount_out)
                    result["min_amount_out"] = str(best_quote.min_amount_out)
                    result["estimated_gas"] = best_quote.estimated_gas
                if built_tx is not None:
                    result["tx"] = built_tx

                return {
                    "status": "EXECUTED",
                    "tx_hash": result.get("tx_hash"),
                    "details": result,
                }
            except DryRunSafetyViolation as e:
                return {
                    "status": "BLOCKED",
                    "tx_hash": None,
                    "details": {
                        "status": "BLOCKED",
                        "reason": "dry_run_safety_violation",
                        "error": str(e),
                    },
                }
            except Exception as e:
                return {
                    "status": "BLOCKED",
                    "tx_hash": None,
                    "details": {
                        "status": "BLOCKED",
                        "reason": "erreur_swap_reel",
                        "error": str(e),
                    },
                }

        # Pour add_liquidity, stake, etc. (actuellement non raccordés en réel)
        return {
            "status": "EXECUTED",
            "tx_hash": None,
            "details": verdict.get("details", {"reason": "guardrails_ok"}),
        }

    return _normalize_verdict(verdict)
