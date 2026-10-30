# core/swap_reel.py – V6.5.0
"""Module d'exécution des swaps réels et simulés sur Polygon avec support Dry-Run et Multi-DEX (V6.5)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import logging
import os
from typing import Any, Coroutine, Dict, List, Optional, TypeVar

from web3 import Web3

import core.config as app_config
from core.dex.base import DEXQuote
from core.dex.factory import create_default_dex_router
from core.dex.quickswap import QuickswapAdapter
from core.dex.router import DEXRouter
from core.dex.sushiswap import SushiswapAdapter
from core.dex.uniswap_v3 import UniswapV3Adapter
from core.dry_run_guard import (
    DryRunSafetyViolation,
    assert_dry_run_safe,
    is_dry_run_enabled,
)
from core.execution.gas_estimator import GasEstimator
from core.execution.gas_tank import GasCriticalError, GasTankManager
from core.execution.rpc_manager import RPCManager
from core.real_wallet import get_private_key, get_wallet_address

# Configuration du logger local
logger = logging.getLogger("core.swap_reel")

_T = TypeVar("_T")

POLYGON_CHAIN_ID = 137

POLYGON_TOKEN_ADDRESSES: Dict[str, str] = {
    "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "ETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "MATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "POL": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "WPOL": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
}

SIX_DECIMAL_TOKENS = {
    "USDC",
    "USDT",
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
}

EIGHT_DECIMAL_TOKENS = {
    "WBTC",
    "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6",
}

DEFAULT_SWAP_RECIPIENT = "0x000000000000000000000000000000000000dEaD"

ERC20_APPROVE_ABI: List[Dict[str, Any]] = [
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


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


def _get_token_decimals(token: str) -> int:
    """Retourne le nombre de décimales d'un token (6 pour USDC/USDT, 18 pour POL/WPOL/WETH, etc.)."""
    key = token.strip()
    if key.upper() in SIX_DECIMAL_TOKENS or key.lower() in SIX_DECIMAL_TOKENS:
        return 6
    return 18


def _amount_wei_to_decimal(token_in: str, amount_in_wei: int) -> Decimal:
    """Convertit un montant en wei vers un Decimal en unités humaines."""
    decimals = _get_token_decimals(token_in)
    return Decimal(int(amount_in_wei)) / (Decimal(10) ** decimals)


def _decimal_to_amount_wei(token: str, amount: float | Decimal) -> int:
    """Convertit un montant en unités humaines (float ou Decimal) vers des unités atomiques (wei)."""
    decimals = _get_token_decimals(token)
    dec_val = Decimal(str(amount))
    return int(round(dec_val * (Decimal(10) ** decimals)))


def _format_tx_hash(tx_hash_bytes: Any) -> str:
    """Formate un hash de transaction en chaîne hexadécimale préfixée par 0x."""
    if isinstance(tx_hash_bytes, (bytes, bytearray)):
        return f"0x{tx_hash_bytes.hex()}"
    if hasattr(tx_hash_bytes, "hex") and callable(tx_hash_bytes.hex):
        hex_str = tx_hash_bytes.hex()
        return hex_str if hex_str.startswith("0x") else f"0x{hex_str}"
    val = str(tx_hash_bytes)
    return val if val.startswith("0x") else f"0x{val}"


def _build_default_rpc_manager() -> RPCManager:
    """Construit un RPCManager avec les URLs de l'environnement et des fallbacks publics."""
    rpc_urls = [
        url
        for url in [
            os.getenv("DEFIPILOT_RPC_URL"),
            os.getenv("POLYGON_RPC_URL"),
            os.getenv("RPC_URL"),
            "https://polygon-bor-rpc.publicnode.com",
            "https://1rpc.io/matic",
        ]
        if url
    ]
    unique_rpc_urls = list(dict.fromkeys(rpc_urls))
    return RPCManager(rpc_urls=unique_rpc_urls)


def _create_single_dex_adapter(dex_name: str, web3_client: Any) -> Any:
    """Crée l'adaptateur unitaire correspondant au nom du DEX pour le mode fallback."""
    norm = (dex_name or "sushiswap").strip().lower()
    if norm in {"quickswap", "quickswap_v3"}:
        return QuickswapAdapter(web3=web3_client)
    if norm in {"uniswap", "uniswap_v3"}:
        return UniswapV3Adapter(web3=web3_client)
    return SushiswapAdapter(web3=web3_client)


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
    prebuilt_quote: Optional[DEXQuote] = None,
    prebuilt_tx: Optional[Dict[str, Any]] = None,
    rpc_manager: Optional[RPCManager] = None,
    gas_estimator: Optional[GasEstimator] = None,
    gas_tank: Optional[GasTankManager] = None,
    max_gas_price_gwei: float = 650.0,
    min_priority_fee_gwei: float = 30.0,
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
    best_quote: Optional[DEXQuote] = prebuilt_quote
    built_tx: Optional[Dict[str, Any]] = prebuilt_tx

    if best_quote is not None:
        selected_dex = best_quote.dex_name

    # En mode réel (dry_run=False), auto-initialisation du RPCManager / Web3 si nécessaire
    active_w3 = web3_client
    active_rpc_manager = rpc_manager
    if not cfg_dry_run and active_w3 is None and built_tx is None and dex_router is None:
        try:
            if active_rpc_manager is None:
                active_rpc_manager = _build_default_rpc_manager()
            active_w3 = active_rpc_manager.get_web3()
        except Exception as exc:
            logger.warning(
                "Impossible d'auto-initialiser Web3 via RPCManager (%s)", exc
            )

    # =========================================================================
    # CONTRÔLE ET RAVITAILLEMENT DU GAS TANK (PRÉ-SWAP V6.6)
    # =========================================================================
    gas_tank_refuel_info: Optional[Dict[str, Any]] = None
    skip_gas_tank_check = bool(kwargs.pop("_skip_gas_tank_check", False))
    active_gas_tank = gas_tank
    if (
        not skip_gas_tank_check
        and active_gas_tank is None
        and (active_w3 is not None or active_rpc_manager is not None)
    ):
        has_real_balance = False
        if active_w3 is not None and hasattr(active_w3, "eth"):
            try:
                bal_candidate = active_w3.eth.get_balance(DEFAULT_SWAP_RECIPIENT)
                has_real_balance = isinstance(bal_candidate, (int, float, Decimal))
            except Exception:
                has_real_balance = False
        if has_real_balance:
            wallet_candidate = (
                recipient
                or get_wallet_address()
                or os.environ.get("WALLET_ADDRESS")
                or DEFAULT_SWAP_RECIPIENT
            )
            active_gas_tank = GasTankManager(
                web3_client=active_w3 or active_rpc_manager,
                wallet_address=wallet_candidate,
                dry_run=cfg_dry_run,
            )

    if active_gas_tank is not None and not skip_gas_tank_check:
        gas_tank_refuel_info = active_gas_tank.check_and_refuel()
        if gas_tank_refuel_info.get("action") in {"unwrap", "simulated_unwrap"}:
            logger.info(
                "[GAS TANK] Ravitaillement pré-swap exécuté : status=%s, action=%s, montant=%s POL, tx_hash=%s",
                gas_tank_refuel_info.get("status"),
                gas_tank_refuel_info.get("action"),
                gas_tank_refuel_info.get("amount_unwrapped"),
                gas_tank_refuel_info.get("tx_hash"),
            )

        # Contrôle critique bloquant (en mode dry_run, un simulated_unwrap comble virtuellement le déficit)
        simulated_refuel_done = (
            cfg_dry_run
            and gas_tank_refuel_info.get("action") == "simulated_unwrap"
        )
        if not simulated_refuel_done and active_gas_tank.is_gas_critical():
            crit_msg = (
                f"[GAS CRITICAL] Swap interrompu : réserve de POL natif sous le seuil critique "
                f"({gas_tank_refuel_info.get('native_pol')} POL <= {active_gas_tank.critical_gas_threshold} POL) "
                f"et ravitaillement WPOL impossible."
            )
            logger.critical(crit_msg)
            return {
                "status": "BLOCKED",
                "tx_hash": None,
                "reason": "gas_critical",
                "msg": crit_msg,
                "details": {
                    "reason": "gas_critical",
                    "error": crit_msg,
                    "gas_tank": gas_tank_refuel_info,
                },
            }

    # =========================================================================
    # AIGUILLAGE MULTI-DEX (AVEC REPLI TRANSPARENT EN CAS D'ERREUR)
    # =========================================================================
    if (
        best_quote is None
        and built_tx is None
        and multi_dex_enabled
        and (dex_router is not None or active_w3 is not None)
    ):
        try:
            router = dex_router or create_default_dex_router(active_w3)
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
                or get_wallet_address()
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
        if gas_tank_refuel_info is not None:
            details["gas_tank"] = gas_tank_refuel_info

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
        # 1. Fallback mono-DEX si FEATURE_MULTI_DEX=False ou si le routeur a échoué
        if built_tx is None and active_w3 is not None:
            try:
                single_adapter = _create_single_dex_adapter(selected_dex, active_w3)
                resolved_in = resolve_token_address(token_in)
                resolved_out = resolve_token_address(token_out)
                amount_in_dec = (
                    Decimal(str(kwargs["amount_in"]))
                    if "amount_in" in kwargs and kwargs["amount_in"] is not None
                    else _amount_wei_to_decimal(token_in, amount_in_wei)
                )
                slippage_dec = Decimal(str(slippage_pct)) / Decimal("100")
                best_quote = _run_coro_sync(
                    single_adapter.get_quote(
                        token_in=resolved_in,
                        token_out=resolved_out,
                        amount_in=amount_in_dec,
                        slippage_tolerance=slippage_dec,
                    )
                )
                selected_dex = best_quote.dex_name
                target_recipient = (
                    recipient
                    or get_wallet_address()
                    or os.environ.get("WALLET_ADDRESS")
                    or DEFAULT_SWAP_RECIPIENT
                )
                built_tx = _run_coro_sync(
                    single_adapter.build_swap_transaction(best_quote, target_recipient)
                )
            except Exception as fallback_exc:
                logger.warning(
                    "Échec de construction de la transaction fallback sur '%s' : %s",
                    selected_dex,
                    fallback_exc,
                )

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
        if gas_tank_refuel_info is not None:
            result["gas_tank"] = gas_tank_refuel_info

        pool_liquidite_valide = built_tx is not None

        if not pool_liquidite_valide:
            logger.warning("Swap bloqué : liquidité de pool insuffisante")
            return {
                "status": "BLOCKED",
                "tx_hash": None,
                "details": {"reason": "liquidite_pool_insuffisante"},
            }

        if not confirm:
            result["status"] = "awaiting_confirmation"
            return result

        # Si aucun client Web3 n'est disponible pour diffuser on-chain
        if active_w3 is None:
            if active_rpc_manager is None:
                active_rpc_manager = _build_default_rpc_manager()
            active_w3 = active_rpc_manager.get_web3()

        wallet_raw = recipient or get_wallet_address() or os.environ.get("WALLET_ADDRESS")
        if not wallet_raw:
            raise ValueError("Adresse du wallet introuvable pour l'exécution réelle.")
        wallet_address = Web3.to_checksum_address(wallet_raw)

        private_key = kwargs.get("private_key") or get_private_key()
        if not private_key:
            raise ValueError("Clé privée introuvable pour signer la transaction réelle.")

        active_gas_estimator = gas_estimator or GasEstimator(
            active_w3,
            min_priority_fee_gwei=min_priority_fee_gwei,
            max_gas_price_gwei=max_gas_price_gwei,
        )

        target_router = Web3.to_checksum_address(built_tx["to"])
        resolved_token_in = Web3.to_checksum_address(resolve_token_address(token_in))

        # 2. Contrôle de l'allowance ERC-20 et Approve conditionnel
        token_contract = active_w3.eth.contract(
            address=resolved_token_in, abi=ERC20_APPROVE_ABI
        )
        current_allowance = int(
            token_contract.functions.allowance(wallet_address, target_router).call()
        )
        raw_amount_in = int(amount_in_wei)

        approve_tx_hash: Optional[str] = None
        if current_allowance < raw_amount_in:
            logger.info(
                "[SWAP RÉEL] Allowance insuffisante (%s < %s), envoi d'un Approve vers %s...",
                current_allowance,
                raw_amount_in,
                target_router,
            )
            fees_approve = active_gas_estimator.estimate_eip1559_fees()
            nonce_approve = active_w3.eth.get_transaction_count(wallet_address, "pending")
            approve_tx = token_contract.functions.approve(
                target_router,
                raw_amount_in,
            ).build_transaction(
                {
                    "from": wallet_address,
                    "nonce": nonce_approve,
                    "maxFeePerGas": fees_approve["maxFeePerGas"],
                    "maxPriorityFeePerGas": fees_approve["maxPriorityFeePerGas"],
                    "chainId": POLYGON_CHAIN_ID,
                }
            )
            try:
                gas_est_approve = active_w3.eth.estimate_gas(approve_tx)
                approve_tx["gas"] = int(gas_est_approve * 1.25)
            except Exception:
                approve_tx["gas"] = 80000

            signed_approve = active_w3.eth.account.sign_transaction(
                approve_tx, private_key
            )
            raw_approve_bytes = getattr(
                signed_approve,
                "raw_transaction",
                getattr(signed_approve, "rawTransaction", None),
            )
            tx_approve_raw = active_w3.eth.send_raw_transaction(raw_approve_bytes)
            approve_tx_hash = _format_tx_hash(tx_approve_raw)
            result["approve_tx_hash"] = approve_tx_hash

            if wait_receipt:
                approve_receipt = active_w3.eth.wait_for_transaction_receipt(
                    tx_approve_raw, timeout=120
                )
                receipt_status = (
                    approve_receipt.get("status")
                    if isinstance(approve_receipt, dict)
                    else getattr(approve_receipt, "status", 1)
                )
                if receipt_status != 1:
                    raise RuntimeError(
                        f"Échec de la transaction d'approbation ({approve_tx_hash})."
                    )

        # 3. Construction finale, signature et émission du Swap EIP-1559
        fees_swap = active_gas_estimator.estimate_eip1559_fees()
        nonce_swap = active_w3.eth.get_transaction_count(wallet_address, "pending")

        final_swap_tx: Dict[str, Any] = {
            "from": wallet_address,
            "to": target_router,
            "data": built_tx["data"],
            "value": built_tx.get("value", 0),
            "nonce": nonce_swap,
            "maxFeePerGas": fees_swap["maxFeePerGas"],
            "maxPriorityFeePerGas": fees_swap["maxPriorityFeePerGas"],
            "chainId": built_tx.get("chainId", POLYGON_CHAIN_ID),
        }

        fallback_gas = (
            best_quote.estimated_gas
            if best_quote is not None
            else int(built_tx.get("gas", 200000))
        )
        try:
            est_gas = active_w3.eth.estimate_gas(final_swap_tx)
            final_swap_tx["gas"] = int(est_gas * 1.30)
        except Exception as exc:
            logger.warning(
                "Estimation gas échouée (%s), application valeur DEX : %s",
                exc,
                fallback_gas,
            )
            final_swap_tx["gas"] = int(fallback_gas * 1.25)

        signed_swap = active_w3.eth.account.sign_transaction(final_swap_tx, private_key)
        raw_swap_bytes = getattr(
            signed_swap,
            "raw_transaction",
            getattr(signed_swap, "rawTransaction", None),
        )
        tx_swap_raw = active_w3.eth.send_raw_transaction(raw_swap_bytes)
        tx_hash = _format_tx_hash(tx_swap_raw)

        result["tx_hash"] = tx_hash
        result["status"] = "sent"

        if wait_receipt:
            receipt = active_w3.eth.wait_for_transaction_receipt(
                tx_swap_raw, timeout=120
            )
            receipt_status = (
                receipt.get("status")
                if isinstance(receipt, dict)
                else getattr(receipt, "status", 1)
            )
            if receipt_status != 1:
                raise RuntimeError(
                    f"Transaction de swap rejetée on-chain (status={receipt_status}, tx={tx_hash})"
                )
            result["status"] = "confirmed"
            block_num = (
                receipt.get("blockNumber")
                if isinstance(receipt, dict)
                else getattr(receipt, "blockNumber", None)
            )
            gas_used = (
                receipt.get("gasUsed")
                if isinstance(receipt, dict)
                else getattr(receipt, "gasUsed", None)
            )
            if block_num is not None:
                result["block_number"] = block_num
            if gas_used is not None:
                result["gas_used"] = gas_used

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
