# liquidity_real_tx_v6_candidate_v3_fixed.py – DeFiPilot V6.0
from __future__ import annotations

import json
import logging
import os
import time
from decimal import Decimal, InvalidOperation, ROUND_DOWN, getcontext
from pathlib import Path
from typing import Any, Optional

from web3 import Web3
from web3.exceptions import ABIFunctionNotFound, ContractLogicError

from core.real_wallet import get_private_key, get_wallet_address

logger = logging.getLogger(__name__)

getcontext().prec = 50

SUSHISWAP_V2_FACTORY_POLYGON = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def _result(
    *,
    success: bool,
    tx_hash: Optional[str],
    status: str,
    amount_a: Optional[str],
    amount_b: Optional[str],
    gas_used: Optional[int],
    message: str,
    lp_tokens: Optional[str],
    error: Optional[str],
) -> dict[str, Any]:
    return {
        "success": success,
        "tx_hash": tx_hash,
        "status": status,
        "amount_a": amount_a,
        "amount_b": amount_b,
        "gas_used": gas_used,
        "message": message,
        "lp_tokens": lp_tokens,
        "error": error,
    }


def _load_abi_file(filename: str) -> list[dict[str, Any]]:
    base = Path(__file__).resolve()
    candidates = [
        base.parent / "abis" / filename,
        base.parent / "abi" / filename,
        base.parents[1] / "abis" / filename,
        base.parents[1] / "abi" / filename,
    ]

    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get("abi"), list):
            return data["abi"]
        if isinstance(data, list):
            return data
        raise ValueError(f"Format ABI invalide dans {path}: attendu liste ou dict avec clé 'abi'.")

    searched = "\n- ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Fichier ABI introuvable: {filename}. Emplacements testés:\n- {searched}"
    )


def _to_decimal(value: Optional[float | str | Decimal], field_name: str) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        converted = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Montant invalide pour {field_name}: {value}") from exc
    if converted.is_nan() or converted.is_infinite():
        raise ValueError(f"Montant invalide pour {field_name}: {value}")
    return converted


def _to_wei(amount: Decimal, decimals: int) -> int:
    factor = Decimal(10) ** decimals
    wei_value = (amount * factor).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return int(wei_value)


def _safe_call_bool_connected(w3: Web3) -> bool:
    if hasattr(w3, "is_connected"):
        return bool(w3.is_connected())
    return bool(w3.isConnected())


def _approve_if_needed(
    *,
    w3: Web3,
    token_contract: Any,
    token_symbol: str,
    wallet: str,
    router: str,
    required_amount: int,
    private_key: str,
) -> None:
    allowance = int(token_contract.functions.allowance(wallet, router).call())
    if allowance >= required_amount:
        logger.info("Allowance suffisante pour %s.", token_symbol)
        return

    logger.info("Allowance insuffisante pour %s, envoi d'un approve.", token_symbol)
    nonce = int(w3.eth.get_transaction_count(wallet))
    try:
        gas_price = int(w3.eth.gas_price)
    except Exception:
        gas_price = int(30 * 10**9)

    approve_tx = token_contract.functions.approve(router, required_amount).build_transaction(
        {
            "from": wallet,
            "nonce": nonce,
            "chainId": int(w3.eth.chain_id),
            "gasPrice": gas_price,
        }
    )

    try:
        approve_tx["gas"] = int(w3.eth.estimate_gas(approve_tx))
    except Exception:
        approve_tx["gas"] = 120000

    signed = w3.eth.account.sign_transaction(approve_tx, private_key)
    raw = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if int(receipt.status) != 1:
        raise RuntimeError(f"Approve échoué pour {token_symbol} (status={receipt.status}).")


def ajouter_liquidite_reelle(
    *,
    pool: dict[str, Any],
    amount_a: Optional[float | str | Decimal],
    amount_b: Optional[float | str | Decimal] = None,
    wallet_name: Optional[str] = None,
    slippage_bps: int = 50,
    deadline_minutes: int = 20,
    dry_run: bool = False,
) -> dict[str, Any]:
    amount_a_str: Optional[str] = None
    amount_b_str: Optional[str] = None

    required_keys = [
        "platform",
        "chain",
        "router_address",
        "tokenA_symbol",
        "tokenB_symbol",
        "tokenA_address",
        "tokenB_address",
    ]
    for key in required_keys:
        if key not in pool:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=amount_a_str,
                amount_b=amount_b_str,
                gas_used=None,
                message=f"Clé manquante dans pool: {key}",
                lp_tokens=None,
                error=f"pool_missing_key:{key}",
            )

    platform = str(pool["platform"]).strip().lower()
    chain = str(pool["chain"]).strip().lower()
    if platform != "sushiswap" or chain != "polygon":
        return _result(
            success=False,
            tx_hash=None,
            status="error",
            amount_a=amount_a_str,
            amount_b=amount_b_str,
            gas_used=None,
            message="Contexte non supporté: uniquement SushiSwap V2 sur Polygon.",
            lp_tokens=None,
            error="unsupported_context",
        )

    try:
        raw_a = _to_decimal(amount_a, "amount_a")
        raw_b = _to_decimal(amount_b, "amount_b")
        if (raw_a is None or raw_a <= 0) and (raw_b is None or raw_b <= 0):
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Au moins un montant strictement positif est requis.",
                lp_tokens=None,
                error="invalid_amounts",
            )

        rpc_url = (
            os.getenv("POLYGON_RPC_URL")
            or os.getenv("RPC_POLYGON")
            or os.getenv("WEB3_RPC_URL")
            or os.getenv("RPC_URL")
        )
        if not rpc_url:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="URL RPC Polygon introuvable dans l'environnement.",
                lp_tokens=None,
                error="missing_rpc_url",
            )

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not _safe_call_bool_connected(w3):
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Connexion Web3 impossible sur Polygon.",
                lp_tokens=None,
                error="web3_not_connected",
            )

        wallet_address = get_wallet_address(wallet_name)
        if not wallet_address:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Adresse wallet introuvable.",
                lp_tokens=None,
                error="missing_wallet_address",
            )

        private_key = get_private_key(wallet_name)
        if not dry_run and not private_key:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Clé privée introuvable pour un envoi réel.",
                lp_tokens=None,
                error="missing_private_key",
            )

        wallet_cs = Web3.to_checksum_address(wallet_address)
        token_a_cs = Web3.to_checksum_address(str(pool["tokenA_address"]))
        token_b_cs = Web3.to_checksum_address(str(pool["tokenB_address"]))
        router_cs = Web3.to_checksum_address(str(pool["router_address"]))
        factory_cs = Web3.to_checksum_address(SUSHISWAP_V2_FACTORY_POLYGON)

        factory_abi = _load_abi_file("uniswap_v2_factory.json")
        pair_abi = _load_abi_file("uniswap_v2_pair.json")
        router_abi = _load_abi_file("uniswap_v2_router.json")
        erc20_abi = _load_abi_file("erc20.json")

        factory_contract = w3.eth.contract(address=factory_cs, abi=factory_abi)
        pair_address = factory_contract.functions.getPair(token_a_cs, token_b_cs).call()
        if str(pair_address).lower() == ZERO_ADDRESS.lower():
            logger.error("Pair inexistante sur SushiSwap V2 Polygon pour les tokens demandés.")
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Pair SushiSwap introuvable pour tokenA/tokenB.",
                lp_tokens=None,
                error="pair_not_found",
            )

        pair_cs = Web3.to_checksum_address(pair_address)
        logger.info("Pair détectée: %s", pair_cs)

        pair_contract = w3.eth.contract(address=pair_cs, abi=pair_abi)
        token0 = Web3.to_checksum_address(pair_contract.functions.token0().call())
        token1 = Web3.to_checksum_address(pair_contract.functions.token1().call())
        logger.info("token0/token1 lus: %s / %s", token0, token1)

        reserve0_raw, reserve1_raw, _ = pair_contract.functions.getReserves().call()
        reserve0 = Decimal(int(reserve0_raw))
        reserve1 = Decimal(int(reserve1_raw))
        logger.info("Réserves lues: reserve0=%s, reserve1=%s", reserve0, reserve1)

        if reserve0 <= 0 or reserve1 <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Pool invalide: réserves brutes nulles ou négatives.",
                lp_tokens=None,
                error="invalid_raw_reserves",
            )

        token_a_low = token_a_cs.lower()
        token_b_low = token_b_cs.lower()
        if token0.lower() == token_a_low and token1.lower() == token_b_low:
            reserve_a = reserve0
            reserve_b = reserve1
        elif token0.lower() == token_b_low and token1.lower() == token_a_low:
            reserve_a = reserve1
            reserve_b = reserve0
        else:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Incohérence pair: tokenA/tokenB ne correspondent pas à token0/token1.",
                lp_tokens=None,
                error="pair_token_mismatch",
            )

        token_a_contract = w3.eth.contract(address=token_a_cs, abi=erc20_abi)
        token_b_contract = w3.eth.contract(address=token_b_cs, abi=erc20_abi)
        router_contract = w3.eth.contract(address=router_cs, abi=router_abi)

        decimals_a = int(token_a_contract.functions.decimals().call())
        decimals_b = int(token_b_contract.functions.decimals().call())

        logger.info("Réserves réordonnées: reserveA=%s, reserveB=%s", reserve_a, reserve_b)

        if reserve_a <= 0 or reserve_b <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Pool invalide: reserveA ou reserveB nulle/négative.",
                lp_tokens=None,
                error="invalid_ordered_reserves",
            )

        reserve_a_human = Decimal(reserve_a) / (Decimal(10) ** decimals_a)
        reserve_b_human = Decimal(reserve_b) / (Decimal(10) ** decimals_b)
        logger.info(
            "Réserves normalisées: reserveA=%s, reserveB=%s",
            reserve_a_human,
            reserve_b_human,
        )

        if reserve_a_human <= 0 or reserve_b_human <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Pool invalide: réserves normalisées nulles/négatives.",
                lp_tokens=None,
                error="invalid_normalized_reserves",
            )

        ratio = reserve_b_human / reserve_a_human
        logger.info("Ratio calculé (B/A): %s", ratio)

        if ratio <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Ratio de pool invalide (<= 0).",
                lp_tokens=None,
                error="invalid_ratio",
            )
        if ratio < Decimal("0.000001") or ratio > Decimal("1000000"):
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Ratio de pool aberrant hors bornes de sécurité.",
                lp_tokens=None,
                error="aberrant_ratio",
            )

        if raw_a is not None and raw_a > 0 and (raw_b is None or raw_b <= 0):
            calc_b = raw_a * ratio
            calc_a = raw_a
        elif raw_b is not None and raw_b > 0 and (raw_a is None or raw_a <= 0):
            calc_a = raw_b / ratio
            calc_b = raw_b
        else:
            calc_a = raw_a if raw_a is not None else Decimal("0")
            calc_b = raw_b if raw_b is not None else Decimal("0")

        if calc_a <= 0 or calc_b <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Montants calculés invalides (<= 0).",
                lp_tokens=None,
                error="invalid_calculated_amounts",
            )

        amount_a_wei = _to_wei(calc_a, decimals_a)
        amount_b_wei = _to_wei(calc_b, decimals_b)

        if amount_a_wei <= 0 or amount_b_wei <= 0:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=None,
                amount_b=None,
                gas_used=None,
                message="Conversion en wei invalide (<= 0).",
                lp_tokens=None,
                error="invalid_wei_amounts",
            )

        amount_a_str = format(calc_a.normalize(), "f")
        amount_b_str = format(calc_b.normalize(), "f")

        balance_a = int(token_a_contract.functions.balanceOf(wallet_cs).call())
        balance_b = int(token_b_contract.functions.balanceOf(wallet_cs).call())
        if balance_a < amount_a_wei or balance_b < amount_b_wei:
            return _result(
                success=False,
                tx_hash=None,
                status="error",
                amount_a=amount_a_str,
                amount_b=amount_b_str,
                gas_used=None,
                message="Soldes insuffisants pour l'ajout de liquidité.",
                lp_tokens=None,
                error="insufficient_balance",
            )
        logger.info("Soldes vérifiés pour tokenA/tokenB.")

        if dry_run:
            return _result(
                success=True,
                tx_hash=None,
                status="dry_run",
                amount_a=amount_a_str,
                amount_b=amount_b_str,
                gas_used=None,
                message="Dry-run validé: calculs et vérifications effectués, aucune transaction envoyée.",
                lp_tokens=None,
                error=None,
            )

        assert private_key is not None

        _approve_if_needed(
            w3=w3,
            token_contract=token_a_contract,
            token_symbol=str(pool["tokenA_symbol"]),
            wallet=wallet_cs,
            router=router_cs,
            required_amount=amount_a_wei,
            private_key=private_key,
        )
        _approve_if_needed(
            w3=w3,
            token_contract=token_b_contract,
            token_symbol=str(pool["tokenB_symbol"]),
            wallet=wallet_cs,
            router=router_cs,
            required_amount=amount_b_wei,
            private_key=private_key,
        )

        amount_a_min_wei = amount_a_wei * (10000 - int(slippage_bps)) // 10000
        amount_b_min_wei = amount_b_wei * (10000 - int(slippage_bps)) // 10000
        deadline_ts = int(time.time()) + int(deadline_minutes) * 60

        nonce = int(w3.eth.get_transaction_count(wallet_cs))
        try:
            gas_price = int(w3.eth.gas_price)
        except Exception:
            gas_price = int(30 * 10**9)

        tx = router_contract.functions.addLiquidity(
            token_a_cs,
            token_b_cs,
            amount_a_wei,
            amount_b_wei,
            amount_a_min_wei,
            amount_b_min_wei,
            wallet_cs,
            deadline_ts,
        ).build_transaction(
            {
                "from": wallet_cs,
                "nonce": nonce,
                "chainId": int(w3.eth.chain_id),
                "gasPrice": gas_price,
            }
        )
        logger.info("Transaction addLiquidity construite.")

        try:
            tx["gas"] = int(w3.eth.estimate_gas(tx))
        except Exception:
            tx["gas"] = 600000

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction")
        tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = tx_hash_bytes.hex()
        logger.info("Transaction envoyée: %s", tx_hash_hex)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes)
        logger.info("Transaction confirmée avec status=%s", receipt.status)
        if int(receipt.status) != 1:
            return _result(
                success=False,
                tx_hash=tx_hash_hex,
                status="failed",
                amount_a=amount_a_str,
                amount_b=amount_b_str,
                gas_used=int(receipt.gasUsed),
                message="Transaction addLiquidity échouée (status != 1).",
                lp_tokens=None,
                error="add_liquidity_failed",
            )

        lp_tokens: Optional[str] = None
        try:
            lp_balance = int(pair_contract.functions.balanceOf(wallet_cs).call())
            lp_decimals = int(pair_contract.functions.decimals().call())
            lp_human = Decimal(lp_balance) / (Decimal(10) ** lp_decimals)
            lp_tokens = format(lp_human.normalize(), "f")
        except Exception:
            lp_tokens = None

        return _result(
            success=True,
            tx_hash=tx_hash_hex,
            status="success",
            amount_a=amount_a_str,
            amount_b=amount_b_str,
            gas_used=int(receipt.gasUsed),
            message="Ajout de liquidité confirmé.",
            lp_tokens=lp_tokens,
            error=None,
        )

    except (ValueError, ABIFunctionNotFound, ContractLogicError, FileNotFoundError) as exc:
        return _result(
            success=False,
            tx_hash=None,
            status="error",
            amount_a=amount_a_str,
            amount_b=amount_b_str,
            gas_used=None,
            message=f"Erreur lors de l'ajout de liquidité: {exc}",
            lp_tokens=None,
            error=str(exc),
        )
    except Exception as exc:
        return _result(
            success=False,
            tx_hash=None,
            status="error",
            amount_a=amount_a_str,
            amount_b=amount_b_str,
            gas_used=None,
            message="Erreur inattendue lors de l'ajout de liquidité.",
            lp_tokens=None,
            error=str(exc),
        )


def add_liquidity_real_safe(
    pool: dict[str, Any],
    amountA: Optional[float | str | Decimal],
    amountB: Optional[float | str | Decimal] = None,
    *,
    slippage_bps: int = 50,
    deadline: int = 20,
    dry_run: bool = False,
) -> dict[str, Any]:
    wallet_name = (pool.get("wallet_name") or pool.get("wallet")) if isinstance(pool, dict) else None
    return ajouter_liquidite_reelle(
        pool=pool,
        amount_a=amountA,
        amount_b=amountB,
        wallet_name=wallet_name,
        slippage_bps=slippage_bps,
        deadline_minutes=deadline,
        dry_run=dry_run,
    )
