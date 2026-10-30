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
from core.execution.gas_tank import GasCriticalError, GasTankManager
from core.real_wallet import get_wallet_address
from core.swap_reel import (
    DEFAULT_SWAP_RECIPIENT,
    _decimal_to_amount_wei,
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


def _resolve_gas_tank(
    gas_tank: Optional[GasTankManager],
    web3_client: Optional[Any],
    rpc_manager: Optional[Any],
    wallet_address: Optional[str],
    dry_run: bool,
) -> Optional[GasTankManager]:
    """Résout ou instancie un `GasTankManager` si un client Web3 / RPC valide est fourni."""
    if gas_tank is not None:
        return gas_tank

    client = web3_client or rpc_manager
    if client is None:
        return None

    # Vérifie que le client Web3/RPC expose des soldes numériques exploitables
    # (évite de perturber les tests historiques où `web3_client = MagicMock()` générique).
    has_numeric_balances = False
    if hasattr(client, "eth"):
        try:
            probe_addr = (
                wallet_address
                or get_wallet_address()
                or os.environ.get("WALLET_ADDRESS")
                or DEFAULT_SWAP_RECIPIENT
            )
            bal = client.eth.get_balance(probe_addr)
            has_numeric_balances = isinstance(bal, (int, float, Decimal))
        except Exception:
            has_numeric_balances = False
    elif hasattr(client, "execute_call"):
        has_numeric_balances = True

    if not has_numeric_balances:
        return None

    target_wallet = (
        wallet_address
        or get_wallet_address()
        or os.environ.get("WALLET_ADDRESS")
        or DEFAULT_SWAP_RECIPIENT
    )
    return GasTankManager(
        web3_client=client,
        wallet_address=target_wallet,
        dry_run=dry_run,
    )


def executer_action_reelle(
    action: dict,
    run_id: str,
    dex_router: Optional[DEXRouter] = None,
    web3_client: Optional[Any] = None,
    feature_multi_dex: Optional[bool] = None,
    gas_tank: Optional[GasTankManager] = None,
    rpc_manager: Optional[Any] = None,
    wallet_address: Optional[str] = None,
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
            is_dry = action.get("dry_run") is True or is_dry_run_enabled()

            # =================================================================
            # ÉTAPE PRÉ-SWAP : CONTRÔLE & RAVITAILLEMENT DU GAS TANK (V6.6)
            # =================================================================
            active_gas_tank = _resolve_gas_tank(
                gas_tank=gas_tank,
                web3_client=web3_client,
                rpc_manager=rpc_manager,
                wallet_address=wallet_address or params.get("recipient"),
                dry_run=is_dry,
            )
            gas_tank_refuel_info: Optional[Dict[str, Any]] = None

            if active_gas_tank is not None:
                try:
                    gas_tank_refuel_info = active_gas_tank.check_and_refuel()
                    if gas_tank_refuel_info.get("action") in {
                        "unwrap",
                        "simulated_unwrap",
                    }:
                        logger.info(
                            "[GAS TANK] Ravitaillement pré-swap effectué : status=%s, action=%s, "
                            "montant=%s POL, tx_hash=%s",
                            gas_tank_refuel_info.get("status"),
                            gas_tank_refuel_info.get("action"),
                            gas_tank_refuel_info.get("amount_unwrapped"),
                            gas_tank_refuel_info.get("tx_hash"),
                        )

                    # Contrôle critique bloquant (en mode dry_run, un simulated_unwrap comble virtuellement le déficit)
                    simulated_refuel_done = (
                        is_dry
                        and gas_tank_refuel_info.get("action") == "simulated_unwrap"
                    )
                    if not simulated_refuel_done and active_gas_tank.is_gas_critical():
                        crit_msg = (
                            f"[GAS CRITICAL] Swap bloqué préventivement : réserve POL natif critique "
                            f"({gas_tank_refuel_info.get('native_pol')} POL <= "
                            f"{active_gas_tank.critical_gas_threshold} POL) et WPOL insuffisant."
                        )
                        logger.critical(crit_msg)
                        raise GasCriticalError(crit_msg)
                except GasCriticalError as crit_err:
                    return {
                        "status": "BLOCKED",
                        "tx_hash": None,
                        "details": {
                            "status": "BLOCKED",
                            "reason": "gas_critical",
                            "error": str(crit_err),
                            "gas_tank": gas_tank_refuel_info,
                        },
                    }

            raw_token_a = str(params.get("tokenA", "USDC"))
            raw_token_b = str(params.get("tokenB", "ETH"))
            tokenA = resolve_token_address(raw_token_a)
            tokenB = resolve_token_address(raw_token_b)
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

            if is_dry:
                sim_details: Dict[str, Any] = {
                    "status": "SUCCESS",
                    "reason": "simulation_swap_ok",
                    "mode": "[SIMULATION / DRY-RUN]",
                    "dex": selected_dex,
                }
                if gas_tank_refuel_info is not None:
                    sim_details["gas_tank"] = gas_tank_refuel_info
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
                amount_in_wei = _decimal_to_amount_wei(raw_token_a, amount_a)
                # NB: _skip_gas_tank_check=True car le contrôle/ravitaillement pré-swap vient d'être exécuté ci-dessus
                result = executer_swap_reel(
                    dex=selected_dex,
                    token_in=tokenA,
                    token_out=tokenB,
                    amount_in_wei=amount_in_wei,
                    confirm=True,
                    dry_run=is_dry,
                    slippage_pct=slippage_pct,
                    dex_router=dex_router,
                    web3_client=web3_client,
                    feature_multi_dex=feature_multi_dex,
                    prebuilt_quote=best_quote,
                    prebuilt_tx=built_tx,
                    recipient=params.get("recipient"),
                    amount_in=amount_a,
                    _skip_gas_tank_check=True,
                )
                if gas_tank_refuel_info is not None:
                    result["gas_tank"] = gas_tank_refuel_info
                if best_quote is not None:
                    result["dex"] = selected_dex
                    result["expected_amount_out"] = str(best_quote.expected_amount_out)
                    result["min_amount_out"] = str(best_quote.min_amount_out)
                    result["estimated_gas"] = best_quote.estimated_gas
                elif already_routed:
                    result["dex"] = selected_dex
                    result["expected_amount_out"] = str(params["expected_amount_out"])
                    if "min_amount_out" in params:
                        result["min_amount_out"] = str(params["min_amount_out"])
                    if "estimated_gas" in params:
                        result["estimated_gas"] = params["estimated_gas"]
                if built_tx is not None:
                    result["tx"] = built_tx

                swap_status = result.get("status")
                if swap_status in {"BLOCKED", "CRITICAL"}:
                    return {
                        "status": swap_status,
                        "tx_hash": None,
                        "details": result,
                    }

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


class RealExecutor:
    """
    Exécuteur orienté objet (V6.6) intégrant `GasTankManager`, `DEXRouter` et `DryRunGuard`
    dans le pipeline de pré-exécution des swaps réels et simulés.
    """

    def __init__(
        self,
        web3_client: Optional[Any] = None,
        rpc_manager: Optional[Any] = None,
        wallet_address: Optional[str] = None,
        dry_run: Optional[bool] = None,
        gas_tank: Optional[GasTankManager] = None,
        dex_router: Optional[DEXRouter] = None,
        feature_multi_dex: Optional[bool] = None,
        min_pol_reserve: float = 5.0,
        target_pol_reserve: float = 10.0,
        critical_gas_threshold: float = 1.0,
        private_key: Optional[str] = None,
    ) -> None:
        self.web3_client = web3_client
        self.rpc_manager = rpc_manager
        self.dry_run = is_dry_run_enabled() if dry_run is None else bool(dry_run)
        self.wallet_address = (
            wallet_address
            or get_wallet_address()
            or os.environ.get("WALLET_ADDRESS")
            or DEFAULT_SWAP_RECIPIENT
        )
        self.dex_router = dex_router
        self.feature_multi_dex = feature_multi_dex

        client = self.web3_client or self.rpc_manager
        if gas_tank is not None:
            self.gas_tank: Optional[GasTankManager] = gas_tank
        elif client is not None:
            self.gas_tank = GasTankManager(
                web3_client=client,
                wallet_address=self.wallet_address,
                min_pol_reserve=min_pol_reserve,
                target_pol_reserve=target_pol_reserve,
                critical_gas_threshold=critical_gas_threshold,
                dry_run=self.dry_run,
                private_key=private_key,
            )
        else:
            self.gas_tank = None

    def pre_swap_gas_check(self) -> Optional[Dict[str, Any]]:
        """
        Exécute le contrôle de pré-swap sur le réservoir de carburant :
        1. Appelle `gas_tank.check_and_refuel()` et journalise toute action de ravitaillement.
        2. Appelle `gas_tank.is_gas_critical()` et lève `GasCriticalError` si le solde est critique.
        """
        if self.gas_tank is None:
            return None

        refuel_info = self.gas_tank.check_and_refuel()
        if refuel_info.get("action") in {"unwrap", "simulated_unwrap"}:
            logger.info(
                "[GAS TANK] Ravitaillement pré-swap exécuté : status=%s, action=%s, montant=%s POL, tx_hash=%s",
                refuel_info.get("status"),
                refuel_info.get("action"),
                refuel_info.get("amount_unwrapped"),
                refuel_info.get("tx_hash"),
            )

        simulated_refuel_done = (
            self.dry_run and refuel_info.get("action") == "simulated_unwrap"
        )
        if not simulated_refuel_done and self.gas_tank.is_gas_critical():
            crit_msg = (
                f"[GAS CRITICAL] Swap interrompu : solde POL natif critique "
                f"({refuel_info.get('native_pol')} POL <= {self.gas_tank.critical_gas_threshold} POL)."
            )
            logger.critical(crit_msg)
            raise GasCriticalError(crit_msg)

        return refuel_info

    def execute_action(self, action: dict, run_id: str = "defipilot_run") -> dict:
        """Exécute une action unitaire en injectant le `GasTankManager` configuré."""
        action_copy = dict(action)
        if "dry_run" not in action_copy:
            action_copy["dry_run"] = self.dry_run
        return executer_action_reelle(
            action=action_copy,
            run_id=run_id,
            dex_router=self.dex_router,
            web3_client=self.web3_client,
            feature_multi_dex=self.feature_multi_dex,
            gas_tank=self.gas_tank,
            rpc_manager=self.rpc_manager,
            wallet_address=self.wallet_address,
        )
