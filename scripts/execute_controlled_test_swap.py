#!/usr/bin/env python3
"""
scripts/execute_controlled_test_swap.py
Script de swap réel minimal et encadré (Phase 1.4 - Étape 3).

Réalise un échange contrôlé de 1.0 USDC vers POL sur Polygon via QuickSwap Router
en s'appuyant strictement sur le socle d'exécution V6 :
- core/execution/rpc_manager.py
- core/execution/gas_estimator.py
- core/execution/slippage_guard.py
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Assurer la présence de la racine du projet dans sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from web3 import Web3

from core.execution.gas_estimator import GasEstimator, GasPriceTooHighError
from core.execution.rpc_manager import RPCManager
from core.execution.slippage_guard import SlippageGuard
from core.real_wallet import get_private_key, get_wallet_address

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DeFiPilot.ControlledTestSwap")

# Constantes officielles Polygon Mainnet
POLYGON_CHAIN_ID = 137
USDC_ADDRESS = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")  # Native Circle USDC
WPOL_ADDRESS = Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")  # Wrapped POL (ex-WMATIC)
QUICKSWAP_ROUTER_ADDRESS = Web3.to_checksum_address("0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff")

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
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
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]

ROUTER_ABI = [
    {
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "swapExactTokensForETH",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def _format_tx_hash(raw_hash: Any) -> str:
    h = raw_hash.hex() if hasattr(raw_hash, "hex") else str(raw_hash)
    if not h.startswith("0x"):
        h = "0x" + h
    return h


def call_with_retry(fn_callable: Any, max_retries: int = 3, delay: float = 1.0) -> Any:
    last_err = None
    for attempt in range(max_retries):
        try:
            return fn_callable()
        except Exception as exc:
            last_err = exc
            if attempt < max_retries - 1:
                logger.warning(f"Appel RPC en échec ({exc}). Nouvel essai ({attempt + 1}/{max_retries})...")
                time.sleep(delay)
    raise last_err


def execute_swap(
    amount_usdc: float = 1.0,
    slippage_pct: float = 1.0,
    min_priority_fee_gwei: float = 30.0,
    max_gas_price_gwei: float = 600.0,
    confirm: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    load_dotenv()

    print("=" * 65)
    print("  DeFiPilot V6.1 - Exécution d'un Swap Contrôlé (Phase 1.4)")
    print("=" * 65)

    mode_label = "REEL (BROADCAST ON-CHAIN)" if confirm and not dry_run else "SIMULATION / PREVIEW"
    print(f" Mode d'exécution     : {mode_label}")
    print(f" Token In             : USDC ({USDC_ADDRESS})")
    print(f" Token Out            : POL natif (via WPOL {WPOL_ADDRESS})")
    print(f" DEX Routeur          : QuickSwap V2 ({QUICKSWAP_ROUTER_ADDRESS})")
    print(f" Montant In           : {amount_usdc:.2f} USDC")
    print(f" Slippage max toléré  : {slippage_pct:.1f} % (plafond absolu 3.0 %)")
    print(f" Garde-fous Gas       : Plancher {min_priority_fee_gwei} Gwei | Plafond {max_gas_price_gwei} Gwei")
    print("-" * 65)

    # 1. Résolution du wallet et de la clé privée
    wallet_raw = get_wallet_address()
    if not wallet_raw:
        logger.error("Aucune adresse de wallet configurée dans .env (WALLET_ADDRESS).")
        sys.exit(1)
    wallet_address = Web3.to_checksum_address(wallet_raw)
    print(f" Portefeuille         : {wallet_address}")

    private_key = None
    if confirm and not dry_run:
        private_key = get_private_key()
        if not private_key:
            logger.error("Clé privée introuvable dans .env (PRIVATE_KEY). Action réelle impossible.")
            sys.exit(1)

    # 2. Initialisation du RPCManager
    rpc_urls = [
        url
        for url in [
            os.getenv("POLYGON_RPC_URL"),
            os.getenv("RPC_URL"),
            "https://polygon-bor-rpc.publicnode.com",
            "https://1rpc.io/matic",
        ]
        if url
    ]
    # Déduplication tout en conservant l'ordre
    unique_rpc_urls = list(dict.fromkeys(rpc_urls))
    rpc_manager = RPCManager(unique_rpc_urls, timeout=12.0, quarantine_time=120.0)
    w3 = rpc_manager.get_web3()
    active_endpoint = getattr(w3.provider, "endpoint_uri", "inconnu")

    chain_id = w3.eth.chain_id
    if chain_id != POLYGON_CHAIN_ID:
        logger.error(f"Chaîne connectée invalide : ID {chain_id} (attendu: {POLYGON_CHAIN_ID} Polygon).")
        sys.exit(1)
    print(f" Connexion RPC        : OK (Chain ID {chain_id} via {active_endpoint})")

    # 3. Initialisation des garde-fous : GasEstimator et SlippageGuard
    gas_estimator = GasEstimator(
        rpc_manager_or_web3=rpc_manager,
        min_priority_fee_gwei=min_priority_fee_gwei,
        max_gas_price_gwei=max_gas_price_gwei,
    )
    slippage_guard = SlippageGuard(
        max_allowed_slippage_pct=3.0,
        default_ttl_seconds=180,
    )

    # 4. Vérification des soldes préalables
    usdc_contract = w3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    router_contract = w3.eth.contract(address=QUICKSWAP_ROUTER_ADDRESS, abi=ROUTER_ABI)

    pol_balance_wei = w3.eth.get_balance(wallet_address)
    pol_balance = float(w3.from_wei(pol_balance_wei, "ether"))

    raw_usdc_balance = usdc_contract.functions.balanceOf(wallet_address).call()
    usdc_decimals = usdc_contract.functions.decimals().call()
    usdc_balance = raw_usdc_balance / (10 ** usdc_decimals)

    print(f" Solde POL initial    : {pol_balance:.4f} POL")
    print(f" Solde USDC initial   : {usdc_balance:.2f} USDC")

    if pol_balance < 0.5:
        logger.error("Solde POL trop bas (< 0.5 POL) pour couvrir les frais de gaz.")
        sys.exit(1)

    if usdc_balance < amount_usdc:
        logger.error(f"Solde USDC insuffisant ({usdc_balance:.2f} < {amount_usdc} USDC demandé).")
        sys.exit(1)

    raw_amount_in = int(round(amount_usdc * (10 ** usdc_decimals)))

    # 5. Vérification & Exécution de l'Allowance / Approve
    print("-" * 65)
    print(" [Étape 1/3] Vérification de l'allowance USDC pour QuickSwap Router...")
    current_allowance = usdc_contract.functions.allowance(wallet_address, QUICKSWAP_ROUTER_ADDRESS).call()
    print(f" Allowance actuelle   : {current_allowance / (10 ** usdc_decimals):.2f} USDC ({current_allowance} unités)")

    approve_tx_hash = None
    if current_allowance < raw_amount_in:
        print(f" ⚠️  Allowance insuffisante. Une transaction 'approve' de {amount_usdc} USDC est requise.")
        if not confirm or dry_run:
            print(" [SIMULATION] Transaction 'approve' simulée avec succès.")
        else:
            print(" 🚀 Émission de la transaction 'approve' EIP-1559...")
            fees = gas_estimator.estimate_eip1559_fees()
            nonce = w3.eth.get_transaction_count(wallet_address)

            approve_tx = usdc_contract.functions.approve(
                QUICKSWAP_ROUTER_ADDRESS,
                raw_amount_in,
            ).build_transaction({
                "from": wallet_address,
                "nonce": nonce,
                "maxFeePerGas": fees["maxFeePerGas"],
                "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
                "chainId": POLYGON_CHAIN_ID,
            })

            try:
                approve_gas_est = w3.eth.estimate_gas(approve_tx)
                approve_tx["gas"] = int(approve_gas_est * 1.25)
            except Exception:
                approve_tx["gas"] = 80000

            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
            approve_raw_bytes = getattr(signed_approve, "raw_transaction", getattr(signed_approve, "rawTransaction", None))
            approve_tx_raw = w3.eth.send_raw_transaction(approve_raw_bytes)
            approve_tx_hash = _format_tx_hash(approve_tx_raw)
            print(f" Tx Approve diffusée : {approve_tx_hash}")
            print(f" Suivi Polygonscan    : https://polygonscan.com/tx/{approve_tx_hash}")
            print(" En attente de minage du bloc...")
            approve_receipt = w3.eth.wait_for_transaction_receipt(approve_tx_raw, timeout=120)

            if approve_receipt.status != 1:
                logger.error(f"Échec du minage de la transaction approve (status={approve_receipt.status}).")
                sys.exit(1)
            print(" ✅ Approve confirmé dans le bloc.")
    else:
        print(" ✅ Allowance USDC déjà suffisante.")

    # 6. Cotation & Contrôle du Slippage
    print("-" * 65)
    print(" [Étape 2/3] Calcul de la cotation et garde-fou Slippage...")
    path = [USDC_ADDRESS, WPOL_ADDRESS]
    amounts_out = call_with_retry(lambda: router_contract.functions.getAmountsOut(raw_amount_in, path).call())
    expected_amount_out_wei = amounts_out[1]
    expected_pol = float(w3.from_wei(expected_amount_out_wei, "ether"))

    min_amount_out_wei = slippage_guard.calculate_min_amount_out(
        expected_amount_out_wei,
        max_slippage_pct=slippage_pct,
    )
    min_pol = float(w3.from_wei(min_amount_out_wei, "ether"))
    deadline = slippage_guard.calculate_deadline(ttl_seconds=180)

    print(f" POL attendu (quote)  : {expected_pol:.6f} POL (taux ~ {expected_pol / amount_usdc:.4f} POL/USDC)")
    print(f" POL minimum garanti  : {min_pol:.6f} POL (slippage {slippage_pct:.1f} %)")
    print(f" Deadline Unix        : {deadline} (TTL 180s)")

    # 7. Estimation Gas EIP-1559 & Garde-fous
    print("-" * 65)
    print(" [Étape 3/3] Estimation des frais de gaz EIP-1559 & émission du swap...")
    try:
        fees = gas_estimator.estimate_eip1559_fees()
    except GasPriceTooHighError as err:
        logger.error(f"Arrêt de sécurité par GasEstimator : {err}")
        sys.exit(1)

    print(f" BaseFee réseau       : {fees['baseFeePerGas_gwei']} Gwei")
    print(f" MaxPriorityFeePerGas : {fees['maxPriorityFeePerGas_gwei']} Gwei (>= {min_priority_fee_gwei} Gwei)")
    print(f" MaxFeePerGas calculé : {fees['maxFeePerGas_gwei']} Gwei (<= {max_gas_price_gwei} Gwei)")

    swap_tx_hash = None
    if not confirm or dry_run:
        print("-" * 65)
        print(" [MODE SIMULATION] Toutes les vérifications de sécurité ont réussi.")
        print(" Pour diffuser la transaction réelle sur Polygon Mainnet, exécutez :")
        print("   ./venv/bin/python scripts/execute_controlled_test_swap.py --confirm")
        print("=" * 65)
        return {
            "status": "SIMULATED_OK",
            "approve_tx_hash": approve_tx_hash,
            "swap_tx_hash": None,
            "expected_pol": expected_pol,
            "min_pol": min_pol,
            "fees": fees,
        }

    # 8. Émission de la transaction réelle de swap
    print(" 🚀 Émission de la transaction de swap sur QuickSwap...")
    nonce = w3.eth.get_transaction_count(wallet_address)

    swap_tx = router_contract.functions.swapExactTokensForETH(
        raw_amount_in,
        min_amount_out_wei,
        path,
        wallet_address,
        deadline,
    ).build_transaction({
        "from": wallet_address,
        "nonce": nonce,
        "maxFeePerGas": fees["maxFeePerGas"],
        "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
        "chainId": POLYGON_CHAIN_ID,
    })

    try:
        gas_estimate = w3.eth.estimate_gas(swap_tx)
        swap_tx["gas"] = int(gas_estimate * 1.25)
    except Exception as exc:
        logger.warning(f"estimate_gas n'a pas pu s'exécuter ({exc}), utilisation du gaz par défaut 220000.")
        swap_tx["gas"] = 220000

    signed_swap = w3.eth.account.sign_transaction(swap_tx, private_key)
    swap_raw_bytes = getattr(signed_swap, "raw_transaction", getattr(signed_swap, "rawTransaction", None))
    swap_tx_raw = w3.eth.send_raw_transaction(swap_raw_bytes)
    swap_tx_hash = _format_tx_hash(swap_tx_raw)

    print("=" * 65)
    print(f" 🌟 Transaction de SWAP diffusée avec succès !")
    print(f" Hash de transaction  : {swap_tx_hash}")
    print(f" Lien Polygonscan     : https://polygonscan.com/tx/{swap_tx_hash}")
    print(" Attente de confirmation on-chain...")

    receipt = w3.eth.wait_for_transaction_receipt(swap_tx_raw, timeout=180)
    print("=" * 65)

    if receipt.status != 1:
        logger.error(f"❌ La transaction de swap a échoué on-chain (status={receipt.status}).")
        sys.exit(1)

    effective_gas_price_gwei = float(w3.from_wei(receipt.effectiveGasPrice, "gwei"))
    cost_pol = float(w3.from_wei(receipt.gasUsed * receipt.effectiveGasPrice, "ether"))

    print(f" ✅ TRANSACTION CONFIRMÉE DANS LE BLOC {receipt.blockNumber} !")
    print(f" Gaz consommé         : {receipt.gasUsed} unités")
    print(f" Prix effectif du gaz : {effective_gas_price_gwei:.2f} Gwei")
    print(f" Coût réel du gaz     : {cost_pol:.6f} POL (~{cost_pol * 0.10:.4f} USD)")

    # 9. Soldes finaux
    final_pol_balance = float(w3.from_wei(call_with_retry(lambda: w3.eth.get_balance(wallet_address)), "ether"))
    final_raw_usdc = call_with_retry(lambda: usdc_contract.functions.balanceOf(wallet_address).call())
    final_usdc_balance = final_raw_usdc / (10 ** usdc_decimals)

    delta_pol = final_pol_balance - pol_balance
    delta_usdc = final_usdc_balance - usdc_balance

    print("-" * 65)
    print(f" Nouveau solde POL    : {final_pol_balance:.4f} POL ({delta_pol:+.4f} POL)")
    print(f" Nouveau solde USDC   : {final_usdc_balance:.2f} USDC ({delta_usdc:+.2f} USDC)")
    print("=" * 65)

    return {
        "status": "SUCCESS",
        "approve_tx_hash": approve_tx_hash,
        "swap_tx_hash": swap_tx_hash,
        "polygonscan_url": f"https://polygonscan.com/tx/{swap_tx_hash}",
        "block_number": receipt.blockNumber,
        "gas_used": receipt.gasUsed,
        "effective_gas_price_gwei": effective_gas_price_gwei,
        "cost_pol": cost_pol,
        "final_pol_balance": final_pol_balance,
        "final_usdc_balance": final_usdc_balance,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DeFiPilot - Swap réel minimal et encadré (Phase 1.4 - USDC -> POL)"
    )
    parser.add_argument(
        "--amount-usdc",
        type=float,
        default=1.0,
        help="Montant d'USDC à échanger (défaut: 1.0 USDC)",
    )
    parser.add_argument(
        "--slippage-pct",
        type=float,
        default=1.0,
        help="Pourcentage de slippage maximal toléré (défaut: 1.0 %)",
    )
    parser.add_argument(
        "--min-priority-fee-gwei",
        type=float,
        default=30.0,
        help="Plancher minimal de pourboire en Gwei (défaut: 30.0 Gwei)",
    )
    parser.add_argument(
        "--max-gas-price-gwei",
        type=float,
        default=600.0,
        help="Plafond de sécurité maximal pour maxFeePerGas (défaut: 600.0 Gwei)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirmer et exécuter réellement la transaction sur le réseau Polygon",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exécuter en mode simulation / lecture seule sans diffuser de transaction",
    )

    args = parser.parse_args()

    execute_swap(
        amount_usdc=args.amount_usdc,
        slippage_pct=args.slippage_pct,
        min_priority_fee_gwei=args.min_priority_fee_gwei,
        max_gas_price_gwei=args.max_gas_price_gwei,
        confirm=args.confirm,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
