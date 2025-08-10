# core/swap_reel.py - V3.7
"""
Swap réel sur DEX Polygon (SushiSwap V2) — DeFiPilot
FR: API pour exécuter un swap réel (slippage, approve auto, confirmation, journalisation CSV).
EN: API to perform a real swap (slippage, auto-approve, confirmation, CSV logging).
"""

from __future__ import annotations

import os
import time
import math
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.exceptions import ContractLogicError

from core.real_wallet import get_wallet_address, get_private_key
from core.journal_swaps import log_swap_event  # journalisation CSV

# get_polygon_rpc_url est optionnel
try:
    from core.env import get_polygon_rpc_url  # type: ignore
except Exception:  # pragma: no cover
    get_polygon_rpc_url = None  # type: ignore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Router SushiSwap V2 (Polygon)
SUSHISWAP_V2_ROUTER = "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506"

# DEX supportés → adresse du router
DEX_ROUTER_ADDRESSES: Dict[str, str] = {
    "sushiswap_v2": SUSHISWAP_V2_ROUTER,
}

# ABI minimal ERC-20
ERC20_ABI: List[Dict[str, Any]] = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
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
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]

# ABI minimal Router V2
ROUTER_V2_ABI: List[Dict[str, Any]] = [
    {
        "name": "getAmountsOut",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "", "type": "uint256[]"}],
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    """ISO 8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()

def _get_web3() -> Web3:
    """FR: Retourne une instance Web3 connectée à Polygon. / EN: Return Polygon Web3."""
    rpc_url: Optional[str] = None
    if callable(get_polygon_rpc_url):
        try:
            rpc_url = get_polygon_rpc_url()  # type: ignore[misc]
        except Exception:
            rpc_url = None
    if not rpc_url:
        rpc_url = os.getenv("POLYGON_RPC_URL")

    if not rpc_url:
        raise RuntimeError(
            "URL RPC Polygon introuvable (core.env.get_polygon_rpc_url() ou POLYGON_RPC_URL)."
        )

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError("Web3 non connecté à Polygon (RPC invalide/HS).")
    return w3


def _erc20(w3: Web3, address: str):
    """FR: Contrat ERC-20 minimal. / EN: Minimal ERC-20 contract."""
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=ERC20_ABI)


def _router_sushiswap_v2(w3: Web3, address: str):
    """FR: Contrat router SushiSwap V2. / EN: SushiSwap V2 router contract."""
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=ROUTER_V2_ABI)


def _ensure_allowance(
    w3: Web3,
    token_contract,
    owner: str,
    spender: str,
    required_amount: int,
    gas_price_wei: int,
    nonce: int,
    wait_receipt: bool,
    private_key: str,
) -> int:
    """FR: Envoie approve si nécessaire. / EN: Send approve if needed."""
    current_allowance = token_contract.functions.allowance(owner, spender).call()
    if current_allowance >= required_amount:
        return nonce

    logger.info("Allowance insuffisante → approve… / Allowance too low → approve…")
    approve_tx = token_contract.functions.approve(spender, required_amount).build_transaction(
        {
            "from": owner,
            "gasPrice": gas_price_wei,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }
    )
    gas_est = w3.eth.estimate_gas(approve_tx)
    approve_tx["gas"] = math.floor(gas_est * 1.15)

    signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_approve.rawTransaction)
    logger.info("Approve tx envoyée: %s", tx_hash.hex())

    if wait_receipt:
        w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Approve confirmée")

    # log approve as an info event (optional)
    try:
        log_swap_event(
            {
                "network": "polygon",
                "dex": "sushiswap_v2",
                "path": [],  # not a swap, just approve
                "amount_in_wei": 0,
                "amount_out_min_wei": 0,
                "slippage_bps": 0,
                "recipient": owner,
                "tx_hash": tx_hash.hex(),
            },
            status="approve_sent",
            timestamp_iso=_utc_now_iso(),
        )
    except Exception:
        pass

    return nonce + 1

# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def effectuer_swap_reel(
    dex: str,
    token_in: str,
    token_out: str,
    amount_in_wei: int,
    *,
    slippage_bps: int = 50,
    recipient: Optional[str] = None,
    path: Optional[List[str]] = None,
    require_confirmation: bool = True,
    confirm: bool = False,
    wait_receipt: bool = True,
    gas_price_wei: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    FR: Swap réel via DEX (SushiSwap V2). EN: Real swap via DEX (SushiSwap V2).

    Retourne un dict: dex, tx_hash (ou None), status, amount_in_wei, amount_out_min_wei,
    slippage_bps, path, recipient, network="polygon".
    """
    if dex not in DEX_ROUTER_ADDRESSES:
        if dex == "uniswap_v3":
            raise NotImplementedError("DEX 'uniswap_v3' non implémenté / not implemented")
        raise NotImplementedError(f"DEX non supporté / unsupported DEX: {dex}")

    # Connexion & wallet
    w3 = _get_web3()
    wallet_address = get_wallet_address()
    if not wallet_address:
        raise RuntimeError("Adresse wallet introuvable / wallet address not found")
    recipient_address = Web3.to_checksum_address(recipient or wallet_address)

    private_key = get_private_key()
    if not private_key:
        raise RuntimeError("Clé privée introuvable / private key not found")

    # Normalisation adresses & path
    token_in = Web3.to_checksum_address(token_in)
    token_out = Web3.to_checksum_address(token_out)
    path = [Web3.to_checksum_address(a) for a in (path or [token_in, token_out])]

    # Router (checksum)
    router_address = DEX_ROUTER_ADDRESSES[dex]
    router_checksum = Web3.to_checksum_address(router_address)
    router = _router_sushiswap_v2(w3, router_checksum)
    token_in_contract = _erc20(w3, token_in)

    # Slippage → amountOutMin
    try:
        amounts: List[int] = router.functions.getAmountsOut(int(amount_in_wei), path).call()
        amount_out_min = math.floor(amounts[-1] * (10000 - slippage_bps) / 10000)
    except Exception as exc:
        logger.error("Échec getAmountsOut: %s", exc)
        raise

    preview: Dict[str, Any] = {
        "dex": dex,
        "tx_hash": None,
        "status": "dry_run" if dry_run else "awaiting_confirmation",
        "amount_in_wei": int(amount_in_wei),
        "amount_out_min_wei": int(amount_out_min),
        "slippage_bps": int(slippage_bps),
        "path": path,
        "recipient": recipient_address,
        "network": "polygon",
    }

    # Journalisation: dry_run ou awaiting_confirmation
    try:
        log_swap_event(
            preview,
            status=preview["status"],
            timestamp_iso=_utc_now_iso(),
        )
    except Exception:
        pass

    # Dry-run / confirmation
    if dry_run:
        preview["dry_run"] = True
        return preview
    if require_confirmation and not confirm:
        return preview

    gas_price = int(gas_price_wei or w3.eth.gas_price)
    nonce = w3.eth.get_transaction_count(wallet_address)

    # Approve si nécessaire (spender = router_checksum)
    nonce = _ensure_allowance(
        w3=w3,
        token_contract=token_in_contract,
        owner=wallet_address,
        spender=router_checksum,
        required_amount=int(amount_in_wei),
        gas_price_wei=gas_price,
        nonce=nonce,
        wait_receipt=wait_receipt,
        private_key=private_key,
    )

    # Build swap tx
    deadline = int(time.time()) + 15 * 60
    tx = router.functions.swapExactTokensForTokens(
        int(amount_in_wei),
        int(amount_out_min),
        path,
        recipient_address,
        int(deadline),
    ).build_transaction(
        {
            "from": wallet_address,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }
    )

    gas_est = w3.eth.estimate_gas(tx)
    tx["gas"] = math.floor(gas_est * 1.15)

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    result = dict(preview)
    result["tx_hash"] = tx_hash.hex()
    result["status"] = "sent"

    # Journalisation: sent
    try:
        log_swap_event(result, status="sent", timestamp_iso=_utc_now_iso())
    except Exception:
        pass

    if wait_receipt:
        w3.eth.wait_for_transaction_receipt(tx_hash)
        result["status"] = "confirmed"
        # Journalisation: confirmed
        try:
            log_swap_event(result, status="confirmed", timestamp_iso=_utc_now_iso())
        except Exception:
            pass

    return result


def executer_swap_reel(*args, **kwargs) -> Dict[str, Any]:
    """Alias compat."""
    return effectuer_swap_reel(*args, **kwargs)


# ---------------------------------------------------------------------------
# Test local (dry-run)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        token_in_ex = Web3.to_checksum_address("0x0000000000000000000000000000000000000001")
        token_out_ex = Web3.to_checksum_address("0x0000000000000000000000000000000000000002")
        apercu = effectuer_swap_reel(
            "sushiswap_v2",
            token_in_ex,
            token_out_ex,
            amount_in_wei=1230000,
            slippage_bps=50,
            require_confirmation=True,
            confirm=False,
            dry_run=True,
        )
        print(apercu)
    except Exception as e:
        logger.error("Erreur test dry-run: %s", e)
