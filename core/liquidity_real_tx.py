# core/liquidity_real_tx.py – V3.8.1
# Patch 1/5 — EIP-1559 + capture gas_used/effectiveGasPrice/tx_cost
# Fix PoA: injection automatique du middleware pour les chaînes de type PoA (Polygon, BSC, ...)
#
# FR: Transactions type-2 (EIP-1559) avec métriques de gas. Aucune modification
#     de la logique métier validée; uniquement la gestion des frais + stats.
# EN: Type-2 (EIP-1559) txs with gas metrics. No business-logic change; only
#     fee handling + metrics.

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from web3 import Web3
from web3.exceptions import ContractLogicError, ExtraDataLengthError

# Middleware PoA (compat v5/v6 de web3.py)
try:  # v5
    from web3.middleware import geth_poa_middleware  # type: ignore
except Exception:  # pragma: no cover
    geth_poa_middleware = None  # type: ignore
try:  # v6
    from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware  # type: ignore
except Exception:  # pragma: no cover
    ExtraDataToPOAMiddleware = None  # type: ignore


# ==================
# ABIs minimales
# ==================
ERC20_ABI = [
    {"name": "approve", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "outputs": [{"name": "", "type": "bool"}]},
    {"name": "allowance", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "balanceOf", "type": "function", "stateMutability": "view",
     "inputs": [{"name": "account", "type": "address"}],
     "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "decimals", "type": "function", "stateMutability": "view", "inputs": [],
     "outputs": [{"name": "", "type": "uint8"}]},
    {"name": "symbol", "type": "function", "stateMutability": "view", "inputs": [],
     "outputs": [{"name": "", "type": "string"}]},
]

ROUTER_ABI = [
    {"name": "addLiquidity", "type": "function", "stateMutability": "nonpayable",
     "inputs": [
        {"name": "tokenA", "type": "address"},
        {"name": "tokenB", "type": "address"},
        {"name": "amountADesired", "type": "uint256"},
        {"name": "amountBDesired", "type": "uint256"},
        {"name": "amountAMin", "type": "uint256"},
        {"name": "amountBMin", "type": "uint256"},
        {"name": "to", "type": "address"},
        {"name": "deadline", "type": "uint256"}
     ],
     "outputs": [
        {"name": "amountA", "type": "uint256"},
        {"name": "amountB", "type": "uint256"},
        {"name": "liquidity", "type": "uint256"}
     ]},
    {"name": "removeLiquidity", "type": "function", "stateMutability": "nonpayable",
     "inputs": [
        {"name": "tokenA", "type": "address"},
        {"name": "tokenB", "type": "address"},
        {"name": "liquidity", "type": "uint256"},
        {"name": "amountAMin", "type": "uint256"},
        {"name": "amountBMin", "type": "uint256"},
        {"name": "to", "type": "address"},
        {"name": "deadline", "type": "uint256"}
     ],
     "outputs": [
        {"name": "amountA", "type": "uint256"},
        {"name": "amountB", "type": "uint256"}
     ]},
]


# ==========================
# Helpers (PoA + EIP-1559)
# ==========================

def _inject_poa_if_needed(w3: Web3) -> None:
    """Tente un get_block; si ExtraDataLengthError, injecte un middleware PoA et réessaie."""
    try:
        w3.eth.get_block("latest")
        return
    except ExtraDataLengthError:
        pass

    # Injecte le middleware adéquat selon la version de web3
    if geth_poa_middleware is not None:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    elif ExtraDataToPOAMiddleware is not None:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    else:
        # Aucun middleware dispo — on relancera l'erreur au prochain appel
        return

    # Vérification post-injection
    w3.eth.get_block("latest")


def _erc20(w3: Web3, addr: str):
    return w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)


def _router(w3: Web3, addr: str):
    return w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ROUTER_ABI)


def _eip1559_fees(w3: Web3,
                  max_fee_gwei: Optional[float] = None,
                  priority_fee_gwei: Optional[float] = None) -> Dict[str, int]:
    """Calcule des frais EIP-1559. Permet overrides via env:
    - MAX_FEE_GWEI
    - PRIORITY_FEE_GWEI
    Politique par défaut: priority = 30 gwei, maxFee = 2*baseFee + priority.
    """
    # PoA first (Polygon)
    _inject_poa_if_needed(w3)

    env_max = os.getenv("MAX_FEE_GWEI")
    env_tip = os.getenv("PRIORITY_FEE_GWEI")
    try:
        if env_max is not None:
            max_fee_gwei = float(env_max)
    except ValueError:
        pass
    try:
        if env_tip is not None:
            priority_fee_gwei = float(env_tip)
    except ValueError:
        pass

    latest = w3.eth.get_block("latest")
    base_fee = latest.get("baseFeePerGas", None)

    if priority_fee_gwei is None:
        priority_fee_gwei = 30.0  # défaut sécurité sur Polygon

    if base_fee is None:
        # Fallback (chaîne legacy): approx 2x tip
        max_fee = w3.to_wei(priority_fee_gwei, "gwei") * 2
    else:
        if max_fee_gwei is None:
            max_fee = 2 * base_fee + w3.to_wei(priority_fee_gwei, "gwei")
        else:
            max_fee = w3.to_wei(max_fee_gwei, "gwei")

    return {
        "maxFeePerGas": int(max_fee),
        "maxPriorityFeePerGas": int(w3.to_wei(priority_fee_gwei, "gwei")),
    }


def _tx_cost_stats(w3: Web3, receipt) -> Dict[str, Any]:
    gas_used = int(receipt.gasUsed)
    eff_price = getattr(receipt, "effectiveGasPrice", None)
    if eff_price is None:
        if isinstance(receipt, dict):
            eff_price = receipt.get("effectiveGasPrice", None)
    if eff_price is None:
        try:
            tx = w3.eth.get_transaction(receipt.transactionHash)
            eff_price = tx.get("gasPrice", 0)
        except Exception:
            eff_price = 0
    total_cost_wei = gas_used * int(eff_price)
    return {
        "gas_used": gas_used,
        "effective_gas_price": int(eff_price),
        "tx_cost_wei": int(total_cost_wei),
        "tx_cost_native": float(w3.from_wei(total_cost_wei, "ether")),  # MATIC sur Polygon
    }


# ======================
# Public API (real mode)
# ======================

@dataclass
class TxResult:
    ok: bool
    tx_hash: str
    status: int
    details: Dict[str, Any]


def approve_if_needed(w3: Web3, *,
                      token: str,
                      owner: str,
                      spender: str,
                      amount: int,
                      chain_id: int,
                      private_key: str,
                      nonce: Optional[int] = None,
                      fees: Optional[Dict[str, int]] = None) -> Optional[TxResult]:
    """Approve exact amount si l'allowance actuelle < amount. Retourne TxResult si tx envoyée, sinon None."""
    _inject_poa_if_needed(w3)
    t = _erc20(w3, token)
    allowance = t.functions.allowance(owner, spender).call()
    if allowance >= amount:
        return None

    if nonce is None:
        nonce = w3.eth.get_transaction_count(owner)
    if fees is None:
        fees = _eip1559_fees(w3)

    tx = t.functions.approve(spender, amount).build_transaction({
        "from": owner,
        "nonce": nonce,
        "chainId": chain_id,
        **fees,
        "type": 2,
    })
    gas_est = t.functions.approve(spender, amount).estimate_gas({"from": owner})
    tx["gas"] = int(gas_est * 1.2)

    signed = w3.eth.account.sign_transaction(tx, private_key)
    h = w3.eth.send_raw_transaction(signed.rawTransaction)
    rcpt = w3.eth.wait_for_transaction_receipt(h)
    stats = _tx_cost_stats(w3, rcpt)
    return TxResult(ok=rcpt.status == 1, tx_hash=h.hex(), status=rcpt.status, details=stats)


def add_liquidity_real(w3: Web3, *,
                       router_addr: str,
                       tokenA: str,
                       tokenB: str,
                       amountADesired: int,
                       amountBDesired: int,
                       amountAMin: int,
                       amountBMin: int,
                       to_addr: str,
                       chain_id: int,
                       private_key: str,
                       deadline_sec: Optional[int] = None) -> TxResult:
    """Envoie router.addLiquidity(...) en EIP-1559. Retourne TxResult avec métriques gas dans details."""
    _inject_poa_if_needed(w3)
    if deadline_sec is None:
        deadline_sec = int(time.time()) + 15 * 60

    owner = to_addr
    router = _router(w3, router_addr)

    nonce = w3.eth.get_transaction_count(owner)
    fees = _eip1559_fees(w3)

    r1 = approve_if_needed(w3, token=tokenA, owner=owner, spender=router.address,
                           amount=amountADesired, chain_id=chain_id, private_key=private_key,
                           nonce=nonce, fees=fees)
    if r1 is not None:
        if not r1.ok:
            return r1
        nonce += 1

    r2 = approve_if_needed(w3, token=tokenB, owner=owner, spender=router.address,
                           amount=amountBDesired, chain_id=chain_id, private_key=private_key,
                           nonce=nonce, fees=fees)
    if r2 is not None:
        if not r2.ok:
            return r2
        nonce += 1

    try:
        tx = router.functions.addLiquidity(
            Web3.to_checksum_address(tokenA),
            Web3.to_checksum_address(tokenB),
            int(amountADesired),
            int(amountBDesired),
            int(amountAMin),
            int(amountBMin),
            Web3.to_checksum_address(to_addr),
            int(deadline_sec)
        ).build_transaction({
            "from": owner,
            "nonce": nonce,
            "chainId": chain_id,
            **fees,
            "type": 2,
        })
        gas_est = router.functions.addLiquidity(
            Web3.to_checksum_address(tokenA),
            Web3.to_checksum_address(tokenB),
            int(amountADesired),
            int(amountBDesired),
            int(amountAMin),
            int(amountBMin),
            Web3.to_checksum_address(to_addr),
            int(deadline_sec)
        ).estimate_gas({"from": owner})
        tx["gas"] = int(gas_est * 1.2)

        signed = w3.eth.account.sign_transaction(tx, private_key)
        h = w3.eth.send_raw_transaction(signed.rawTransaction)
        rcpt = w3.eth.wait_for_transaction_receipt(h)
        stats = _tx_cost_stats(w3, rcpt)
        return TxResult(ok=rcpt.status == 1, tx_hash=h.hex(), status=rcpt.status, details=stats)

    except ContractLogicError as e:
        return TxResult(ok=False, tx_hash="", status=0, details={"error": f"ContractLogicError: {e}"})
    except Exception as e:
        return TxResult(ok=False, tx_hash="", status=0, details={"error": f"Exception: {e}"})


def remove_liquidity_real(w3: Web3, *,
                           router_addr: str,
                           tokenA: str,
                           tokenB: str,
                           liquidity_amount: int,
                           amountAMin: int,
                           amountBMin: int,
                           to_addr: str,
                           chain_id: int,
                           private_key: str,
                           lp_token_addr: Optional[str] = None,
                           deadline_sec: Optional[int] = None) -> TxResult:
    """removeLiquidity en EIP-1559. Si lp_token_addr est fourni, on assure un approve exact avant."""
    _inject_poa_if_needed(w3)
    if deadline_sec is None:
        deadline_sec = int(time.time()) + 15 * 60

    owner = to_addr
    router = _router(w3, router_addr)

    nonce = w3.eth.get_transaction_count(owner)
    fees = _eip1559_fees(w3)

    if lp_token_addr:
        r = approve_if_needed(w3, token=lp_token_addr, owner=owner, spender=router.address,
                              amount=int(liquidity_amount), chain_id=chain_id, private_key=private_key,
                              nonce=nonce, fees=fees)
        if r is not None:
            if not r.ok:
                return r
            nonce += 1

    try:
        tx = router.functions.removeLiquidity(
            Web3.to_checksum_address(tokenA),
            Web3.to_checksum_address(tokenB),
            int(liquidity_amount),
            int(amountAMin),
            int(amountBMin),
            Web3.to_checksum_address(to_addr),
            int(deadline_sec)
        ).build_transaction({
            "from": owner,
            "nonce": nonce,
            "chainId": chain_id,
            **fees,
            "type": 2,
        })
        gas_est = router.functions.removeLiquidity(
            Web3.to_checksum_address(tokenA),
            Web3.to_checksum_address(tokenB),
            int(liquidity_amount),
            int(amountAMin),
            int(amountBMin),
            Web3.to_checksum_address(to_addr),
            int(deadline_sec)
        ).estimate_gas({"from": owner})
        tx["gas"] = int(gas_est * 1.2)

        signed = w3.eth.account.sign_transaction(tx, private_key)
        h = w3.eth.send_raw_transaction(signed.rawTransaction)
        rcpt = w3.eth.wait_for_transaction_receipt(h)
        stats = _tx_cost_stats(w3, rcpt)
        return TxResult(ok=rcpt.status == 1, tx_hash=h.hex(), status=rcpt.status, details=stats)

    except ContractLogicError as e:
        return TxResult(ok=False, tx_hash="", status=0, details={"error": f"ContractLogicError: {e}"})
    except Exception as e:
        return TxResult(ok=False, tx_hash="", status=0, details={"error": f"Exception: {e}"})


# ======================
# Notes d'utilisation
# ======================
# - Les fonctions add_liquidity_real/remove_liquidity_real retournent un TxResult
#   avec: ok/status/tx_hash + details(gas_used, effective_gas_price, tx_cost_native...)
# - Patch 2/5 enrichira les journaux CSV/JSONL pour intégrer ces champs.
