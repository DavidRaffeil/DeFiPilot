# core/liquidity_real_tx.py – V3.8

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from web3 import Web3
from web3.exceptions import ContractLogicError

from core.real_wallet import get_wallet_address, get_private_key
from core.journal import enregistrer_liquidity_csv, enregistrer_liquidity_jsonl

logger = logging.getLogger(__name__)

# Dossier ABI relatif à ce fichier (fonctionne sous Windows/Linux)
ABI_DIR = Path(__file__).resolve().parent / "abis"


def _load_abi(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_checksum(w3: Web3, addr: str) -> str:
    return Web3.to_checksum_address(addr)


def _now_ts() -> int:
    return int(time.time())


def _to_wei(amount: float, decimals: int) -> int:
    return int(amount * (10 ** decimals))


def _from_wei(amount: int, decimals: int) -> float:
    return amount / float(10 ** decimals)


def ajouter_liquidite_reelle(
    pool: dict,
    amountA: float,
    amountB: float,
    wallet_name: str,
    slippage: float = 0.005,
    deadline: Optional[int] = None,
    dry_run: bool = False
) -> dict:
    """
    Ajoute de la liquidité (réelle si dry_run=False, sinon simulation) sur une pool UniswapV2-like.
    Retourne un dict standardisé:
    { "success": bool, "tx_hash": str|None, "lp_tokens": float|None, "error": str|None }
    """
    logger.info(
        "[V3.8] 🔧 Params: pool=%s amountA=%s amountB=%s wallet=%s slippage=%s dry_run=%s",
        pool,
        amountA,
        amountB,
        wallet_name,
        slippage,
        dry_run,
    )

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
            logger.error("[V3.8] ⚠️ Échec: %s", err)
            ligne = {
                "date_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "version": "V3.8",
                "chain": pool.get("chain"),
                "platform": pool.get("platform"),
                "router": pool.get("router_address"),
                "tokenA": pool.get("tokenA_symbol"),
                "tokenB": pool.get("tokenB_symbol"),
                "amountA_in": amountA,
                "amountB_in": amountB,
                "amountAMin": amountA * (1 - slippage),
                "amountBMin": amountB * (1 - slippage),
                "slippage": slippage,
                "deadline_ts": deadline,
                "dry_run": dry_run,
                "approvals_done": "none",
                "tx_hash": None,
                "tx_status": "error",
                "gas_used": None,
                "lp_tokens_received": None,
                "wallet": get_wallet_address(wallet_name),
                "error": err,
            }
            try:
                enregistrer_liquidity_csv(ligne)
                enregistrer_liquidity_jsonl(ligne)
            finally:
                pass
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
    deadline_ts = deadline if deadline is not None else _now_ts() + 20 * 60

    success = False
    tx_hash_str: Optional[str] = None
    lp_tokens_received: Optional[float] = None
    error_msg: Optional[str] = None
    tx_status: str = "skipped(dry_run)" if dry_run else "not_sent"
    gas_used: Optional[int] = None
    approvals_done = "none"

    wallet = get_wallet_address(wallet_name)
    if wallet is None:
        error_msg = "wallet introuvable"
        logger.error("[V3.8] ⚠️ Échec: %s", error_msg)
    else:
        try:
            rpc_url = None
            if chain.lower() == "polygon":
                rpc_url = os.getenv("POLYGON_RPC_URL") or os.getenv("RPC_POLYGON")
            if not rpc_url:
                raise RuntimeError("RPC non configuré")

            w3 = Web3(Web3.HTTPProvider(rpc_url))
            # web3.py v6: is_connected(); v5: isConnected()
            if not (getattr(w3, "is_connected", None) and w3.is_connected()) and not (getattr(w3, "isConnected", None) and w3.isConnected()):
                raise RuntimeError("Web3 non connecté")

            wallet_cs = _to_checksum(w3, wallet)
            tokenA_cs = _to_checksum(w3, tokenA_address)
            tokenB_cs = _to_checksum(w3, tokenB_address)
            router_cs = _to_checksum(w3, router_address)

            erc20_abi = _load_abi(ABI_DIR / "erc20.json")
            router_abi = _load_abi(ABI_DIR / "uniswap_v2_router.json")

            tokenA_contract = w3.eth.contract(address=tokenA_cs, abi=erc20_abi)
            tokenB_contract = w3.eth.contract(address=tokenB_cs, abi=erc20_abi)
            router_contract = w3.eth.contract(address=router_cs, abi=router_abi)

            decA = tokenA_contract.functions.decimals().call()
            decB = tokenB_contract.functions.decimals().call()

            amountA_wei = _to_wei(amountA, decA)
            amountB_wei = _to_wei(amountB, decB)
            amountAMin_wei = _to_wei(amountAMin, decA)
            amountBMin_wei = _to_wei(amountBMin, decB)

            if dry_run:
                lp_tokens_received = 0.0
                logger.info("[V3.8] 🪙 AddLiquidity dry-run")
                success = True
            else:
                private_key = get_private_key(wallet_name)
                if not private_key:
                    raise RuntimeError("clé privée introuvable")

                nonce = w3.eth.get_transaction_count(wallet_cs)
                gas_price = w3.eth.gas_price

                approvals = []
                allowanceA = tokenA_contract.functions.allowance(wallet_cs, router_cs).call()
                if allowanceA < amountA_wei:
                    tx = tokenA_contract.functions.approve(router_cs, amountA_wei).build_transaction({
                        "from": wallet_cs,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                        "chainId": w3.eth.chain_id,
                    })
                    tx["gas"] = w3.eth.estimate_gas(tx)
                    signed = w3.eth.account.sign_transaction(tx, private_key)
                    h = w3.eth.send_raw_transaction(signed.rawTransaction)
                    w3.eth.wait_for_transaction_receipt(h)
                    nonce += 1
                    approvals.append("A")
                allowanceB = tokenB_contract.functions.allowance(wallet_cs, router_cs).call()
                if allowanceB < amountB_wei:
                    tx = tokenB_contract.functions.approve(router_cs, amountB_wei).build_transaction({
                        "from": wallet_cs,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                        "chainId": w3.eth.chain_id,
                    })
                    tx["gas"] = w3.eth.estimate_gas(tx)
                    signed = w3.eth.account.sign_transaction(tx, private_key)
                    h = w3.eth.send_raw_transaction(signed.rawTransaction)
                    w3.eth.wait_for_transaction_receipt(h)
                    nonce += 1
                    approvals.append("B")
                if approvals:
                    approvals_done = "+".join(approvals)
                logger.info("[V3.8] 🧱 Approvals: %s", approvals_done)

                tx = router_contract.functions.addLiquidity(
                    tokenA_cs,
                    tokenB_cs,
                    amountA_wei,
                    amountB_wei,
                    amountAMin_wei,
                    amountBMin_wei,
                    wallet_cs,
                    deadline_ts,
                ).build_transaction({
                    "from": wallet_cs,
                    "gasPrice": gas_price,
                    "nonce": nonce,
                    "chainId": w3.eth.chain_id,
                })
                tx["gas"] = w3.eth.estimate_gas(tx)
                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                tx_hash_str = tx_hash.hex()
                gas_used = receipt.gasUsed
                tx_status = "success" if receipt.status == 1 else "failed"
                logger.info("[V3.8] ✅ Tx sent: %s", tx_hash_str)

                transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)").hex()
                zero_topic = "0x" + "0" * 64
                wallet_topic = "0x" + wallet_cs[2:].lower().rjust(64, "0")
                for log in receipt.logs:
                    try:
                        if (
                            log.topics[0].hex() == transfer_topic
                            and log.topics[1].hex() == zero_topic
                            and log.topics[2].hex().lower() == wallet_topic
                            and log.address.lower() not in [tokenA_cs.lower(), tokenB_cs.lower()]
                        ):
                            amount_lp = int(log.data, 16)
                            lp_tokens_received = _from_wei(amount_lp, 18)  # LP souvent 18 décimales
                            break
                    except Exception:
                        continue
                success = receipt.status == 1
        except ContractLogicError as exc:
            error_msg = str(exc)
            tx_status = "contract_error"
            logger.error("[V3.8] ⚠️ Échec: %s", error_msg)
        except FileNotFoundError as exc:
            error_msg = str(exc)
            tx_status = "error"
            logger.error("[V3.8] ⚠️ Échec: %s", error_msg)
        except Exception as exc:
            error_msg = str(exc)
            tx_status = "error"
            logger.error("[V3.8] ⚠️ Échec: %s", error_msg)

    ligne = {
        "date_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": "V3.8",
        "chain": chain,
        "platform": platform,
        "router": router_address,
        "tokenA": tokenA_symbol,
        "tokenB": tokenB_symbol,
        "amountA_in": amountA,
        "amountB_in": amountB,
        "amountAMin": amountAMin,
        "amountBMin": amountBMin,
        "slippage": slippage,
        "deadline_ts": deadline_ts,
        "dry_run": dry_run,
        "approvals_done": approvals_done,
        "tx_hash": tx_hash_str,
        "tx_status": tx_status,
        "gas_used": gas_used,
        "lp_tokens_received": lp_tokens_received,
        "wallet": wallet,
        "error": error_msg,
    }
    try:
        enregistrer_liquidity_csv(ligne)
        enregistrer_liquidity_jsonl(ligne)
    finally:
        pass

    logger.info(
        "[V3.8] Résumé: platform=%s, pair=%s-%s, amountA=%s, amountB=%s, slippage=%s, dry_run=%s, tx=%s, lp=%s",
        platform,
        tokenA_symbol,
        tokenB_symbol,
        amountA,
        amountB,
        slippage,
        dry_run,
        tx_hash_str,
        lp_tokens_received,
    )

    return {
        "success": success,
        "tx_hash": tx_hash_str,
        "lp_tokens": lp_tokens_received,
        "error": error_msg,
    }
