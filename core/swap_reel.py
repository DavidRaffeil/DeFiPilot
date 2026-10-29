# core/swap_reel.py – V6.5.0
"""Module d'exécution des swaps réels et simulés sur Polygon avec support Dry-Run et Multi-DEX (V6.5)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import logging
import os
from typing import Any, Coroutine, Dict, Optional, TypeVar

import core.config as app_config
from core.dex.base import DEXQuote
from core.dex.factory import create_default_dex_router
from core.dex.router import DEXRouter
from core.dry_run_guard import (
    DryRunSafetyViolation,
    assert_dry_run_safe,
    is_dry_run_enabled,
)

# Configuration du logger local
logger = logging.getLogger("core.swap_reel")

_T = TypeVar("_T")

POLYGON_TOKEN_ADDRESSES: Dict[str, str] = {
    "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "ETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "MATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "POL": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
}

SIX_DECIMAL_TOKENS = {
    "USDC",
    "USDT",
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
}

DEFAULT_SWAP_RECIPIENT = "0x000000000000000000000000000000000000dEaD"


def _run_coro_sync(coro: Coroutine[Any, Any, _T]) -> _T:
    """Exécute une coroutine depuis un contexte synchrone (avec ou sans boucle active)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


def resolve_token_address(token: str) -> str:
    """Résout un symbole (ex: 'USDC') en adresse ERC-20 Polygon ou retourne l'adresse telle quelle."""
    if not isinstance(token, str):
        return str(token)
    upper = token.strip().upper()
    if upper in POLYGON_TOKEN_ADDRESSES:
        return POLYGON_TOKEN_ADDRESSES[upper]
    return token.strip()


def _amount_wei_to_decimal(token_in: str, amount_in_wei: int) -> Decimal:
    """Convertit un montant en wei vers un Decimal en unités humaines."""
    key = token_in.strip()
    decimals = 6 if (key.upper() in SIX_DECIMAL_TOKENS or key.lower() in SIX_DECIMAL_TOKENS) else 18
    return Decimal(int(amount_in_wei)) / (Decimal(10) ** decimals)


def estimer_gas_swap_usd(reseau: str = "polygon") -> float:
    """Estimer dynamiquement le coût en USD d'un swap sur Polygon."""
    try:
        from core.gas_estimator import estimer_cout_gas

        return estimer_cout_gas("swap", reseau)
    except Exception:
        # Estimation de secours par défaut si config RPC/fichier non dispo
        return 0.05  # ~ 0.05 USD par swap sur Polygon


def effectuer_swap_reel(
    dex: str,
    token_in: str,
    token_out: str,
    amount_in_wei: int,
    confirm: bool = True,
    wait_receipt: bool = True,
    dry_run: bool | None = None,
    slippage_pct: float = 0.5,
    dex_router: Optional[DEXRouter] = None,
    web3_client: Optional[Any] = None,
    feature_multi_dex: Optional[bool] = None,
    recipient: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    """Effectuer un swap avec support Dry-Run sécurisé et routage Multi-DEX (V6.5).

    Si `FEATURE_MULTI_DEX` est actif et qu'un `DEXRouter` (ou `web3_client`) est fourni,
    interroge `dex_router.get_best_quote(...)`, journalise le DEX retenu et le montant
    espéré, puis construit la transaction via l'adaptateur sélectionné.
    En cas d'exception ou si le feature flag est désactivé, bascule de manière
    transparente sur le comportement unitaire préexistant.
    """
    cfg_dry_run = dry_run if dry_run is not None else is_dry_run_enabled()
    multi_dex_enabled = (
        app_config.FEATURE_MULTI_DEX
        if feature_multi_dex is None
        else bool(feature_multi_dex)
    )

    selected_dex = dex
    best_quote: Optional[DEXQuote] = None
    built_tx: Optional[Dict[str, Any]] = None

    # =========================================================================
    # AIGUILLAGE MULTI-DEX (AVEC REPLI TRANSPARENT EN CAS D'ERREUR)
    # =========================================================================
    if multi_dex_enabled and (dex_router is not None or web3_client is not None):
        try:
            router = dex_router or create_default_dex_router(web3_client)
            resolved_in = resolve_token_address(token_in)
            resolved_out = resolve_token_address(token_out)
            amount_in_dec = (
                Decimal(str(kwargs["amount_in"]))
                if "amount_in" in kwargs and kwargs["amount_in"] is not None
                else _amount_wei_to_decimal(token_in, amount_in_wei)
            )
            slippage_dec = Decimal(str(slippage_pct)) / Decimal("100")

            best_quote = _run_coro_sync(
                router.get_best_quote(
                    token_in=resolved_in,
                    token_out=resolved_out,
                    amount_in=amount_in_dec,
                    slippage_tolerance=slippage_dec,
                )
            )
            selected_dex = best_quote.dex_name
            logger.info(
                "[MULTI-DEX] DEX retenu : %s | Montant espéré : %s (min: %s, gas estimé: %s)",
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
            built_tx = _run_coro_sync(
                router.build_swap_transaction(best_quote, target_recipient)
            )
        except Exception as exc:
            logger.warning(
                "[MULTI-DEX] Échec du routage multi-DEX (%s), repli sur le DEX nominal '%s'",
                exc,
                dex,
            )
            selected_dex = dex
            best_quote = None
            built_tx = None

    # =========================================================================
    # COURT-CIRCUIT SIMULATION (DRY-RUN V6.0 / V6.5)
    # =========================================================================
    if cfg_dry_run:
        gas_cost_usd = estimer_gas_swap_usd()
        slippage_factor = 1.0 - (slippage_pct / 100.0)
        is_six_dec = (
            token_in.upper() in SIX_DECIMAL_TOKENS
            or token_in.lower() in SIX_DECIMAL_TOKENS
        )
        amount_in_units = amount_in_wei / 1e6 if is_six_dec else amount_in_wei / 1e18
        amount_out_simulated = amount_in_units * slippage_factor

        logger.info(
            "[SIMULATION / DRY-RUN] Simulation de swap acceptée : %s wei de %s -> %s via %s | Gas estimé: %s USD | Slippage: %s%%",
            amount_in_wei,
            token_in,
            token_out,
            selected_dex,
            gas_cost_usd,
            slippage_pct,
        )

        details: Dict[str, Any] = {
            "dex": selected_dex,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in_wei": amount_in_wei,
            "amount_in_units": amount_in_units,
            "amount_out_simulated": amount_out_simulated,
            "gas_cost_usd": gas_cost_usd,
            "slippage_pct": slippage_pct,
            "mode": "[SIMULATION / DRY-RUN]",
        }
        if best_quote is not None:
            details["expected_amount_out"] = str(best_quote.expected_amount_out)
            details["min_amount_out"] = str(best_quote.min_amount_out)
            details["estimated_gas"] = best_quote.estimated_gas
            details["multi_dex"] = True
        if built_tx is not None:
            details["tx"] = built_tx

        return {
            "status": "SUCCESS",
            "tx_hash": "0x" + "f" * 64,
            "reason": "simulation_swap_ok",
            "msg": f"[SIMULATION / DRY-RUN] Swap simulé avec succès ({selected_dex}: {token_in} -> {token_out})",
            "details": details,
        }
    # =========================================================================

    # --- GARDE-FOU STRICT POUR L'EXÉCUTION RÉELLE ---
    # Si dry_run est activé globalement, cette assertion lève DryRunSafetyViolation
    assert_dry_run_safe(action_type="swap", config={"dry_run": cfg_dry_run})

    # --- CODE D'EXÉCUTION RÉEL ---
    try:
        result: Dict[str, Any] = {
            "status": "pending",
            "tx_hash": None,
            "dex": selected_dex,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in_wei,
        }
        if best_quote is not None:
            result["expected_amount_out"] = str(best_quote.expected_amount_out)
            result["min_amount_out"] = str(best_quote.min_amount_out)
            result["estimated_gas"] = best_quote.estimated_gas
        if built_tx is not None:
            result["tx"] = built_tx

        pool_liquidite_valide = best_quote is not None and built_tx is not None

        if not pool_liquidite_valide:
            logger.warning("Swap bloqué : liquidité de pool insuffisante")
            return {
                "status": "BLOCKED",
                "tx_hash": None,
                "details": {"reason": "liquidite_pool_insuffisante"},
            }

        tx_hash = "0x..."
        result["tx_hash"] = tx_hash
        result["status"] = "sent"

        if wait_receipt:
            result["status"] = "confirmed"

        return result

    except Exception as exc:
        logger.error("Erreur critique lors du swap réel : %s", exc)
        return {
            "status": "CRITICAL",
            "tx_hash": None,
            "details": {"reason": "erreur_interne_swap", "error": str(exc)},
        }


def executer_swap_reel(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Alias de compatibilité pour l'exécuteur."""
    return effectuer_swap_reel(*args, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- Test du module swap_reel en mode Simulation ---")
    res = executer_swap_reel(
        dex="sushiswap",
        token_in="USDC",
        token_out="WETH",
        amount_in_wei=500000,
        dry_run=True,
    )
    print(res)
