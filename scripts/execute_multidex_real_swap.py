#!/usr/bin/env python3
"""
scripts/execute_multidex_real_swap.py
Exécution d'un micro-swap réel de validation (Jalon 3.2)
avec routage Multi-DEX actif (FEATURE_MULTI_DEX=True).
"""

from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Chargement sécurisé du fichier .env
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

from web3 import Web3

from core.dex.factory import create_default_dex_router
from core.execution.gas_estimator import GasEstimator, GasPriceTooHighError
from core.execution.rpc_manager import RPCManager
from core.execution.slippage_guard import SlippageGuard
from core.real_wallet import get_private_key, get_wallet_address
from core.swap_reel import resolve_token_address
from core.wallet_reader import lire_solde_erc20, lire_solde_native

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DeFiPilot.MultiDEXSwap")

POLYGON_CHAIN_ID = 137

ERC20_APPROVE_ABI = [
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


def _format_tx_hash(tx_hash_bytes: Any) -> str:
    if isinstance(tx_hash_bytes, (bytes, bytearray)):
        return f"0x{tx_hash_bytes.hex()}"
    val = str(tx_hash_bytes)
    return val if val.startswith("0x") else f"0x{val}"


async def run_multidex_swap(
    amount_usdc: float,
    max_slippage_pct: float,
    live: bool,
    max_gas_gwei: float = 600.0,
    auto_yes: bool = False,
):
    print("=" * 70)
    print(" 🚀 DEFIPILOT V6.5.0 — MICRO-SWAP RÉEL MULTI-DEX (JALON 3.2)")
    print(f" Mode : {'🔴 EN DIRECT (TRANSACTIONS RÉELLES ON-CHAIN)' if live else '🟡 SIMULATION (DRY-RUN)'}")
    print("=" * 70)

    # 1. Connexion Web3
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
    rpc_manager = RPCManager(rpc_urls=unique_rpc_urls)
    w3 = rpc_manager.get_web3()
    chain_id = w3.eth.chain_id
    if chain_id != POLYGON_CHAIN_ID:
        logger.error(f"Mauvais réseau connecté : {chain_id} (attendu : {POLYGON_CHAIN_ID})")
        sys.exit(1)

    wallet_address = Web3.to_checksum_address(get_wallet_address())
    private_key = get_private_key() if live else None

    gas_estimator = GasEstimator(w3, max_gas_price_gwei=max_gas_gwei, min_priority_fee_gwei=30.0)
    slippage_guard = SlippageGuard(max_allowed_slippage_pct=max_slippage_pct)

    # 2. Vérification des soldes
    pol_bal = lire_solde_native(w3, wallet_address)
    usdc_addr = Web3.to_checksum_address(resolve_token_address("USDC"))
    pol_addr = Web3.to_checksum_address(resolve_token_address("POL"))
    wpol_addr = Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")

    res_usdc = lire_solde_erc20(w3, usdc_addr, wallet_address)
    if not res_usdc:
        logger.error("Impossible de lire le solde USDC.")
        sys.exit(1)
    raw_usdc_balance, usdc_decimals = res_usdc
    usdc_balance = raw_usdc_balance / (10 ** usdc_decimals)

    res_wpol = lire_solde_erc20(w3, wpol_addr, wallet_address)
    wpol_balance = (res_wpol[0] / (10 ** res_wpol[1])) if res_wpol else 0.0

    print(f" Wallet actif    : {wallet_address}")
    print(f" Solde POL natif : {pol_bal:.4f} POL")
    print(f" Solde WPOL      : {wpol_balance:.6f} WPOL")
    print(f" Solde USDC      : {usdc_balance:.6f} USDC")
    print(f" Montant swap    : {amount_usdc:.2f} USDC -> POL/WPOL")
    print("-" * 70)

    if pol_bal < 0.5:
        logger.error("Solde POL insuffisant pour le gaz (< 0.5 POL).")
        sys.exit(1)
    if usdc_balance < amount_usdc:
        logger.error(f"Solde USDC insuffisant ({usdc_balance:.2f} < {amount_usdc}).")
        sys.exit(1)

    # 3. Requête Multi-DEX
    print(" [Étape 1/4] Interrogation du routeur Multi-DEX...")
    router = create_default_dex_router(w3, timeout=8.0)
    comparison = await router.get_quotes(
        token_in=usdc_addr,
        token_out=pol_addr,
        amount_in=Decimal(str(amount_usdc)),
        slippage_tolerance=Decimal(str(max_slippage_pct)) / Decimal("100"),
    )

    if not comparison.best_quote:
        logger.error("Aucune cotation valide reçue de la part des DEX.")
        sys.exit(1)

    best = comparison.best_quote
    print(f" 🏆 Meilleure route sélectionnée : {best.dex_name.upper()}")
    print(f"    - POL espéré                : {best.expected_amount_out:.6f} POL")
    print(f"    - POL minimum garanti       : {best.min_amount_out:.6f} POL (slippage: {max_slippage_pct}%)")
    print(f"    - Gas estimé DEX            : {best.estimated_gas}")

    # 4. Construction de la transaction de swap
    print("-" * 70)
    print(" [Étape 2/4] Préparation de la transaction de swap...")
    swap_tx_blueprint = await router.build_swap_transaction(best, recipient=wallet_address)
    target_router = Web3.to_checksum_address(swap_tx_blueprint["to"])
    print(f" Contrat cible (Router {best.dex_name}) : {target_router}")

    usdc_contract = w3.eth.contract(address=usdc_addr, abi=ERC20_APPROVE_ABI)
    current_allowance = usdc_contract.functions.allowance(wallet_address, target_router).call()
    raw_amount_in = int(round(amount_usdc * (10 ** usdc_decimals)))

    if live:
        preview_fees = gas_estimator.estimate_eip1559_fees()
        allowance_needed = current_allowance < raw_amount_in
        print("-" * 70)
        print(" ⚠️  RÉCAPITULATIF AVANT EXÉCUTION RÉELLE (MAINNET) :")
        print(f"    - Wallet source           : {wallet_address}")
        print(f"    - Montant en entrée       : {amount_usdc:.2f} USDC")
        print(f"    - Montant minimum garanti : {best.min_amount_out:.6f} POL")
        print(f"    - DEX sélectionné         : {best.dex_name.upper()} ({target_router})")
        print(
            f"    - Frais estimés           : MaxFee={preview_fees['maxFeePerGas_gwei']} Gwei "
            f"| PriorityFee={preview_fees['maxPriorityFeePerGas_gwei']} Gwei "
            f"| Gas estimé={best.estimated_gas}"
        )
        print(
            f"    - Allowance requise       : {'OUI (' + str(amount_usdc) + ' USDC)' if allowance_needed else 'NON (déjà suffisante)'}"
        )
        print("-" * 70)
        if auto_yes:
            print(" ✅ Confirmation automatique activée (--yes). Poursuite de l'exécution réelle...")
        else:
            try:
                user_confirm = input(
                    "Confirmer l'émission des transactions réelles sur Polygon Mainnet ? (tapez 'OUI') : "
                )
            except EOFError:
                user_confirm = ""
            if user_confirm.strip() != "OUI":
                print(" 🛑 Opération annulée par l'utilisateur. Aucune transaction n'a été signée.")
                sys.exit(0)

    # 5. Gestion de l'Approve USDC
    print("-" * 70)
    print(f" [Étape 3/4] Contrôle de l'allowance USDC pour {best.dex_name}...")
    print(f" Allowance actuelle : {current_allowance / (10 ** usdc_decimals):.4f} USDC (requis : {amount_usdc} USDC)")

    if current_allowance < raw_amount_in:
        print(f" ⚠️ Allowance requise. Autorisation de {amount_usdc} USDC...")
        if not live:
            print(" [SIMULATION] Approve simulé avec succès.")
        else:
            fees = gas_estimator.estimate_eip1559_fees()
            nonce = w3.eth.get_transaction_count(wallet_address, "pending")
            approve_tx = usdc_contract.functions.approve(
                target_router,
                raw_amount_in,
            ).build_transaction({
                "from": wallet_address,
                "nonce": nonce,
                "maxFeePerGas": fees["maxFeePerGas"],
                "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
                "chainId": POLYGON_CHAIN_ID,
            })
            try:
                gas_est = w3.eth.estimate_gas(approve_tx)
                approve_tx["gas"] = int(gas_est * 1.25)
            except Exception:
                approve_tx["gas"] = 80000

            signed_approve = w3.eth.account.sign_transaction(approve_tx, private_key)
            raw_bytes = getattr(signed_approve, "raw_transaction", getattr(signed_approve, "rawTransaction", None))
            tx_hash_raw = w3.eth.send_raw_transaction(raw_bytes)
            app_hash = _format_tx_hash(tx_hash_raw)
            print(f" 📡 Tx Approve envoyée : {app_hash}")
            print(f" Suivi : https://polygonscan.com/tx/{app_hash}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash_raw, timeout=120)
            if receipt.status != 1:
                logger.error("Échec de la transaction d'approbation.")
                sys.exit(1)
            print(" ✅ Approve validé on-chain.")
    else:
        print(" ✅ Allowance déjà suffisante.")

    # 6. Émission du Swap
    print("-" * 70)
    print(" [Étape 4/4] Émission de la transaction de swap...")
    if not live:
        print(" [SIMULATION] Swap Multi-DEX validé en simulation.")
        print("=" * 70)
        return

    fees = gas_estimator.estimate_eip1559_fees()
    nonce = w3.eth.get_transaction_count(wallet_address, "pending")

    final_swap_tx = {
        "from": wallet_address,
        "to": target_router,
        "data": swap_tx_blueprint["data"],
        "value": swap_tx_blueprint.get("value", 0),
        "nonce": nonce,
        "maxFeePerGas": fees["maxFeePerGas"],
        "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
        "chainId": POLYGON_CHAIN_ID,
    }

    try:
        est_gas = w3.eth.estimate_gas(final_swap_tx)
        final_swap_tx["gas"] = int(est_gas * 1.30)
    except Exception as exc:
        logger.warning(f"Estimation gas échouée ({exc}), application valeur DEX : {best.estimated_gas}")
        final_swap_tx["gas"] = int(best.estimated_gas * 1.25)

    print(f" Paramètres EIP-1559 : MaxFee={fees['maxFeePerGas_gwei']} Gwei | PriorityFee={fees['maxPriorityFeePerGas_gwei']} Gwei | GasLimit={final_swap_tx['gas']}")
    signed_swap = w3.eth.account.sign_transaction(final_swap_tx, private_key)
    raw_swap_bytes = getattr(signed_swap, "raw_transaction", getattr(signed_swap, "rawTransaction", None))
    tx_swap_hash_raw = w3.eth.send_raw_transaction(raw_swap_bytes)
    swap_hash = _format_tx_hash(tx_swap_hash_raw)

    print(f" 🚀 TRANSACTION DE SWAP DIFFUSÉE : {swap_hash}")
    print(f" 🔗 Polygonscan : https://polygonscan.com/tx/{swap_hash}")
    print(" ⏳ Attente de minage du bloc...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_swap_hash_raw, timeout=120)
    if receipt.status == 1:
        print("=" * 70)
        print(" 🎯 SWAP CONFIRMÉ AVEC SUCCÈS DANS LE BLOC !")
        print(f" Bloc n° : {receipt.blockNumber} | Gas consommé : {receipt.gasUsed}")
        print("=" * 70)
        time.sleep(2)
        new_pol = lire_solde_native(w3, wallet_address)
        new_res = lire_solde_erc20(w3, usdc_addr, wallet_address)
        new_usdc = new_res[0] / (10 ** new_res[1]) if new_res else 0.0
        new_res_wpol = lire_solde_erc20(w3, wpol_addr, wallet_address)
        new_wpol = new_res_wpol[0] / (10 ** new_res_wpol[1]) if new_res_wpol else 0.0
        print(
            f" Solde USDC       : initial={usdc_balance:.6f} | final={new_usdc:.6f} USDC "
            f"(delta: {new_usdc - usdc_balance:+.6f})"
        )
        print(
            f" Solde POL natif  : initial={pol_bal:.4f} | final={new_pol:.4f} POL "
            f"(delta gaz: {new_pol - pol_bal:+.4f})"
        )
        print(
            f" Solde WPOL ERC20 : initial={wpol_balance:.6f} | final={new_wpol:.6f} WPOL "
            f"(delta reçu: {new_wpol - wpol_balance:+.6f})"
        )
    else:
        logger.error(f"Transaction rejetée on-chain (status={receipt.status})")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Micro-swap réel Multi-DEX DeFiPilot (Jalon 3.2)")
    parser.add_argument("--amount", type=float, default=1.0, help="Montant USDC à échanger (défaut: 1.0)")
    parser.add_argument("--slippage", type=float, default=1.0, help="Slippage max toléré en %% (défaut: 1.0)")
    parser.add_argument("--max-gas-gwei", type=float, default=600.0, help="Plafond max de gas en Gwei (défaut: 600.0)")
    parser.add_argument("--live", action="store_true", default=False, help="Exécuter la transaction réelle on-chain")
    parser.add_argument("--yes", action="store_true", default=False, help="Confirmer automatiquement sans saisie interactive")
    args = parser.parse_args()

    asyncio.run(run_multidex_swap(args.amount, args.slippage, args.live, args.max_gas_gwei, args.yes))


if __name__ == "__main__":
    main()
