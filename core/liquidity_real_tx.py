# core/liquidity_real_tx.py – V3.8.18 (journal enrichi, schéma V3.8 corrigé)
"""Transactions d'ajout de liquidité (réel) + journalisation CSV/JSONL.

Règles respectées:
- Fichier complet, prêt à coller tel quel.
- En-tête de version présent.
- Pas de changement de signatures publiques existantes.
- Journalisation corrigée : tout est écrit au format V3.8 CSV/JSONL, succès ou erreur.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from web3 import Web3
from web3.exceptions import ContractLogicError, ABIFunctionNotFound

from core.real_wallet import get_wallet_address, get_private_key
from core.journal import enregistrer_liquidity_csv, enregistrer_liquidity_jsonl

logger = logging.getLogger(__name__)

# Dossier ABI relatif à ce fichier (fonctionne sous Windows/Linux)
ABI_DIR = Path(__file__).resolve().parent / "abis"


# =====================
# Helpers utilitaires
# =====================

def _load_abi(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_checksum(w3: Web3, addr: str) -> str:
    return Web3.to_checksum_address(addr)


def _now_ts() -> int:
    return int(time.time())


def _to_wei(amount: float, decimals: int) -> int:
    if amount is None:
        return 0
    if decimals == 18:
        return int(amount * 10**18)
    return int(round(amount * (10 ** decimals)))


def _from_wei(amount_wei: int, decimals: int) -> float:
    if amount_wei is None:
        return 0.0
    if decimals == 18:
        return amount_wei / 10**18
    return amount_wei / float(10 ** decimals)


def _load_factory_abi() -> dict:
    factory_path_candidates = [
        ABI_DIR / "uniswap_v2_factory.json",
        ABI_DIR / "factory.json",
    ]
    for p in factory_path_candidates:
        if p.exists():
            return _load_abi(p)
    return {
        "abi": [
            {
                "name": "getPair",
                "type": "function",
                "stateMutability": "view",
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                ],
                "outputs": [{"name": "pair", "type": "address"}],
            }
        ]
    }["abi"]


def _get_factory_address(platform: str, chain: str) -> Optional[str]:
    platform = (platform or "").lower()
    chain = (chain or "").lower()
    if platform == "sushiswap" and chain == "polygon":
        return "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    return None


# =====================
# Cœur métier
# =====================

def ajouter_liquidite_reelle(
    *,
    pool: dict,
    amountA: float,
    amountB: float,
    wallet_name: Optional[str] = None,
    slippage: float = 0.005,
    deadline: int = 20,
    dry_run: bool = False,
) -> dict:
    required = [
        "platform",
        "chain",
        "router_address",
        "tokenA_symbol",
        "tokenB_symbol",
        "tokenA_address",
        "tokenB_address",
    ]
    for key in required:
        if key not in pool:
            err = f"pool missing key: {key}"
            logger.error("[V3.8.18] ⚠️ %s", err)
            return {"success": False, "tx_hash": None, "lp_tokens": None, "error": err}

    platform = pool["platform"]
    chain = pool["chain"]
    router_address = pool["router_address"]
    tokenA_symbol = pool["tokenA_symbol"]
    tokenB_symbol = pool["tokenB_symbol"]
    tokenA_address = pool["tokenA_address"]
    tokenB_address = pool["tokenB_address"]

    amountAMin = amountA * (1 - slippage)
    amountBMin = amountB * (1 - slippage)
    deadline_ts = (
        _now_ts() + int(deadline) * 60
        if (deadline is not None and int(deadline) < 10_000_000_000)
        else (int(deadline) if deadline is not None else _now_ts() + 20 * 60)
    )

    success: bool = False
    tx_hash_str: Optional[str] = None
    lp_tokens_received: Optional[float] = None
    error_msg: Optional[str] = None
    tx_status: str = "skipped(dry_run)" if dry_run else "not_sent"
    gas_used: Optional[int] = None
    receipt = None

    wallet = get_wallet_address(wallet_name)
    if wallet is None:
        error_msg = "wallet introuvable"
        logger.error("[V3.8.18] ⚠️ %s", error_msg)
    else:
        try:
            rpc_url = None
            if str(chain).lower() == "polygon":
                rpc_url = (
                    os.getenv("POLYGON_RPC_URL")
                    or os.getenv("RPC_POLYGON")
                    or os.getenv("WEB3_RPC_URL")
                    or os.getenv("RPC_URL")
                )
            if not rpc_url:
                raise RuntimeError("RPC non configuré")

            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not (
                (getattr(w3, "is_connected", None) and w3.is_connected())
                or (getattr(w3, "isConnected", None) and w3.isConnected())
            ):
                raise RuntimeError("Web3 non connecté")

            wallet_cs = _to_checksum(w3, wallet)
            tokenA_cs = _to_checksum(w3, tokenA_address)
            tokenB_cs = _to_checksum(w3, tokenB_address)
            router_cs = _to_checksum(w3, router_address)

            erc20_path = ABI_DIR / "erc20.json"
            router_path = ABI_DIR / "uniswap_v2_router.json"
            erc20_abi = _load_abi(erc20_path)
            router_abi = _load_abi(router_path)

            router_contract = w3.eth.contract(address=router_cs, abi=router_abi)

            tokenA_contract = w3.eth.contract(address=tokenA_cs, abi=erc20_abi)
            tokenB_contract = w3.eth.contract(address=tokenB_cs, abi=erc20_abi)
            decA = tokenA_contract.functions.decimals().call()
            decB = tokenB_contract.functions.decimals().call()

            amountA_wei = _to_wei(amountA, decA)
            amountB_wei = _to_wei(amountB, decB)
            amountA_min_wei = _to_wei(amountAMin, decA)
            amountB_min_wei = _to_wei(amountBMin, decB)

            try:
                gas_price = w3.eth.gas_price
            except Exception:
                gas_price = int(30 * 1e9)

            nonce = w3.eth.get_transaction_count(wallet_cs)
            private_key = get_private_key(wallet_name)
            if not private_key:
                raise RuntimeError("private key introuvable")

            if dry_run:
                tx_status = "skipped(dry_run)"
                logger.info(
                    "[V3.8.18] DRY-RUN addLiquidity %s/%s A=%s B=%s slippage=%s",
                    tokenA_symbol, tokenB_symbol, amountA, amountB, slippage,
                )
            else:
                tx = router_contract.functions.addLiquidity(
                    tokenA_cs,
                    tokenB_cs,
                    amountA_wei,
                    amountB_wei,
                    amountA_min_wei,
                    amountB_min_wei,
                    wallet_cs,
                    deadline_ts,
                ).build_transaction({
                    "from": wallet_cs,
                    "gasPrice": gas_price,
                    "nonce": nonce,
                    "chainId": w3.eth.chain_id,
                })
                try:
                    tx["gas"] = w3.eth.estimate_gas(tx)
                except Exception:
                    tx["gas"] = 600000
                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                success = (receipt.status == 1)
                tx_hash_str = tx_hash.hex()
                tx_status = "success" if success else "failed"
                gas_used = getattr(receipt, "gasUsed", None)
                logger.info("[V3.8.18] ✅ Tx envoyée: %s", tx_hash_str)

                lp_tokens_received = None
                transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)").hex()
                zero_topic = "0x" + "0" * 64
                wallet_topic = "0x" + wallet_cs[2:].lower().rjust(64, "0")
                try:
                    for log in receipt.logs:
                        try:
                            if (
                                log.topics[0].hex().lower() == transfer_topic.lower()
                                and log.topics[1].hex().lower() == zero_topic
                                and log.topics[2].hex().lower() == wallet_topic
                                and log.address.lower() not in [tokenA_cs.lower(), tokenB_cs.lower()]
                            ):
                                amount_lp = int(log.data, 16)
                                try:
                                    lp_token_cs = _to_checksum(w3, log.address)
                                    lp_contract = w3.eth.contract(address=lp_token_cs, abi=erc20_abi)
                                    decLP = lp_contract.functions.decimals().call()
                                except Exception:
                                    decLP = 18
                                lp_tokens_received = _from_wei(amount_lp, decLP)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

                if lp_tokens_received is None:
                    try:
                        factory_addr = _get_factory_address(platform, chain)
                        if factory_addr:
                            pair_addr = w3.eth.contract(
                                address=_to_checksum(w3, factory_addr),
                                abi=_load_factory_abi(),
                            ).functions.getPair(tokenA_cs, tokenB_cs).call()
                            if int(pair_addr, 16) != 0:
                                lp_cs = _to_checksum(w3, pair_addr)
                                lp_contract = w3.eth.contract(address=lp_cs, abi=erc20_abi)
                                try:
                                    decLP = lp_contract.functions.decimals().call()
                                except Exception:
                                    decLP = 18
                                bal = lp_contract.functions.balanceOf(wallet_cs).call()
                                lp_tokens_received = _from_wei(bal, decLP)
                    except Exception:
                        pass

        except ContractLogicError as exc:
            error_msg = str(exc)
            tx_status = "contract_error"
        except ABIFunctionNotFound as exc:
            error_msg = str(exc)
            tx_status = "abi_error"
        except Exception as exc:
            error_msg = str(exc)
            tx_status = "error"

    # =====================
    # Journalisation standard (schéma V3.8)
    # =====================
    try:
        run_id = os.environ.get("RUN_ID") or os.urandom(8).hex()
        slippage_bps = int(round(slippage * 10000))
        slippage_pct = round(slippage_bps / 100.0, 4)

        effective_gas_price = getattr(receipt, "effectiveGasPrice", None) if receipt else None
        tx_cost_native = None
        if gas_used is not None and effective_gas_price is not None:
            tx_cost_native = (gas_used * effective_gas_price) / 1e18

        data_v38 = {
            "date": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "platform": platform,
            "chain": chain,
            "tokenA": tokenA_symbol,
            "tokenB": tokenB_symbol,
            "amountA": amountA,
            "amountB": amountB,
            "amountA_effectif": amountA,
            "amountB_effectif": amountB,
            "lp_tokens_estimes": lp_tokens_received,
            "slippage_applique_pct": slippage_pct,
            "ratio_contraint": "none",
            "details": "OK" if tx_status == "success" else (error_msg or tx_status or "error"),
            "gas_used": gas_used,
            "effective_gas_price": effective_gas_price,
            "tx_cost_native": tx_cost_native,
            "tx_status": tx_status,
            "balance_USDC_after": None,
            "balance_WETH_after": None,
            "slippage_bps": slippage_bps,
        }

        enregistrer_liquidity_csv(**data_v38)
        enregistrer_liquidity_jsonl(**data_v38)
    except Exception as log_exc:
        logger.error("[V3.8.18] ⚠️ Journalisation standard échouée: %s", log_exc)

    logger.info(
        "[V3.8.18] Résumé: platform=%s, pair=%s-%s, amountA=%s, amountB=%s, slippage=%s, dry_run=%s, tx=%s, lp=%s",
        platform, tokenA_symbol, tokenB_symbol, amountA, amountB, slippage, dry_run, tx_hash_str, lp_tokens_received,
    )

    return {"success": success, "tx_hash": tx_hash_str, "lp_tokens": lp_tokens_received, "error": error_msg}


def add_liquidity_real_safe(
    pool: dict,
    amountA: float,
    amountB: float,
    *,
    slippage_bps: int = 50,
    deadline: int = 20,
    dry_run: bool = False,
) -> dict:
    required = ["platform", "chain", "tokenA_symbol", "tokenB_symbol"]
    for key in required:
        if key not in pool:
            err = f"pool missing key: {key}"
            logger.error("[V3.8.18] ⚠️ %s", err)
            return {"success": False, "tx_hash": None, "lp_tokens": None, "error": err}

    slippage = slippage_bps / 10000.0
    wallet_name = pool.get("wallet_name") or pool.get("wallet") or None

    return ajouter_liquidite_reelle(
        pool=pool,
        amountA=amountA,
        amountB=amountB,
        wallet_name=wallet_name,
        slippage=slippage,
        deadline=deadline,
        dry_run=dry_run,
    )
