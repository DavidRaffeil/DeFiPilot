# farming_cli.py – V3.9.11
"""CLI DeFiPilot pour les opérations de farming (Polygon, SushiSwap MiniChef V2).

Cette version V3.9.11 active le mode RÉEL pour la sous-commande ``unstake``
avec les mêmes garde-fous de sécurité que ``harvest``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from typing import Any, Dict, Optional

# Imports optionnels (Web3 peut être absent de l'environnement)
try:  # pragma: no cover - environnement sans Web3
    from web3 import Web3  # type: ignore
    from web3.contract.contract import Contract  # type: ignore
    from web3.exceptions import ContractLogicError  # type: ignore
    from web3.middleware import geth_poa_middleware  # type: ignore
except Exception:  # pragma: no cover - fallback si web3 indisponible
    Web3 = None  # type: ignore
    Contract = Any  # type: ignore
    ContractLogicError = Exception  # type: ignore
    geth_poa_middleware = None  # type: ignore

try:  # pragma: no cover - eth-account optionnel
    from eth_account import Account  # type: ignore
except Exception:  # pragma: no cover
    Account = None  # type: ignore

from core.journal_farming import enregistrer_farming

VERSION = "V3.9.11"
DEFAULT_PLATFORM = "sushiswap"
DEFAULT_CHAIN = "polygon"
DEFAULT_CHAIN_ID = 137
DEFAULT_LP_DECIMALS = 18
_DECIMAL_CONTEXT = getcontext().copy()
_DECIMAL_CONTEXT.prec = 78

_MINICHEF_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "address", "name": "_to", "type": "address"},
        ],
        "name": "harvest",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_pid", "type": "uint256"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
            {"internalType": "address", "name": "_to", "type": "address"},
        ],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass
class GlobalOptions:  # V3.9.11
    rpc_url: Optional[str]
    wallet_address: Optional[str]
    private_key: Optional[str]
    minichef: Optional[str]
    run_id: str
    platform: str
    chain: str
    lp_decimals: int
    chain_id: int


def _now_iso() -> str:  # V3.9.11
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _resolve_env_private_key() -> Optional[str]:  # V3.9.11
    return os.getenv("PRIVATE_KEY") or os.getenv("WALLET_PRIVATE_KEY")


def _resolve_env_wallet() -> Optional[str]:  # V3.9.11
    return os.getenv("WALLET_ADDRESS") or os.getenv("ADDRESS")


def _resolve_env_rpc_url() -> Optional[str]:  # V3.9.11
    return (
        os.getenv("POLYGON_RPC_URL")
        or os.getenv("RPC_POLYGON")
        or os.getenv("WEB3_RPC_URL")
        or os.getenv("RPC_URL")
    )


def _is_valid_address(addr: Optional[str]) -> bool:  # V3.9.11
    if not addr:
        return False
    if Web3 is None:
        return addr.startswith("0x") and len(addr) == 42
    try:
        return bool(Web3.isAddress(addr))
    except Exception:  # pragma: no cover
        return addr.startswith("0x") and len(addr) == 42


def _to_checksum(addr: str, w3: Optional[Any]) -> str:  # V3.9.11
    if not addr:
        raise ValueError("Adresse manquante")
    if w3 is not None:
        try:
            return w3.to_checksum_address(addr)
        except Exception as exc:  # pragma: no cover
            raise ValueError(f"Adresse invalide: {addr}") from exc
    if not _is_valid_address(addr):
        raise ValueError(f"Adresse invalide: {addr}")
    return addr


def _connect_web3(rpc_url: Optional[str]) -> Optional[Any]:  # V3.9.11
    if Web3 is None or not rpc_url:
        return None
    try:
        provider = Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60})  # type: ignore[attr-defined]
        w3 = Web3(provider)  # type: ignore[call-arg]
        if geth_poa_middleware is not None:
            try:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except Exception:  # pragma: no cover
                pass
        try:
            is_connected = bool(w3.is_connected())
        except Exception:  # pragma: no cover
            is_connected = bool(w3.isConnected())
        if not is_connected:
            return None
        return w3
    except Exception:  # pragma: no cover
        return None


def _get_minichef_contract(w3: Any, address: str) -> Contract:  # V3.9.11
    return w3.eth.contract(address=address, abi=_MINICHEF_ABI)


def _format_wei_to_native(value: int) -> float:  # V3.9.11
    if value is None:
        return 0.0
    return float(Decimal(value) / Decimal(10 ** 18))


def _apply_gas_buffer(gas_estimate: int) -> int:  # V3.9.11
    if gas_estimate <= 0:
        return 0
    buffered = int(gas_estimate * 1.2)
    fallback = gas_estimate + 5000
    return max(buffered, fallback)


def _format_amount_to_wei(amount: float, decimals: int) -> int:  # V3.9.11
    try:
        quant = Decimal(str(amount)).scaleb(decimals)
        if quant < 0:
            raise ValueError("Le montant doit être positif")
        return int(quant.to_integral_value(rounding=_DECIMAL_CONTEXT.rounding))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Montant invalide: {amount}") from exc


def _build_log_payload(  # V3.9.11
    opts: GlobalOptions,
    action: str,
    pid: Optional[int],
    amount_requested: Optional[float],
    amount_effective: Optional[float],
    tx_status: str,
    tx_hash: Optional[str],
    gas_used: Optional[int],
    effective_gas_price: Optional[int],
    tx_cost_native: Optional[float],
    balances_after: Optional[Dict[str, Any]],
    dry_run: bool,
) -> Dict[str, Any]:
    return {
        "date": _now_iso(),
        "run_id": opts.run_id,
        "platform": opts.platform,
        "chain": opts.chain,
        "wallet": opts.wallet_address or "",
        "action": action,
        "pool_id": pid,
        "lp_token": None,
        "lp_decimals": opts.lp_decimals,
        "amount_lp_requested": amount_requested,
        "amount_lp_effectif": amount_effective,
        "rewards_token": None,
        "rewards_amount": None,
        "tx_status": tx_status,
        "tx_hash": tx_hash,
        "gas_used": gas_used,
        "effective_gas_price": effective_gas_price,
        "tx_cost_native": tx_cost_native,
        "balances_after_json": balances_after,
        "dry_run": dry_run,
        "notes": f"farming_cli.py {VERSION}",
        "version": VERSION,
    }


def parse_global_options(args: argparse.Namespace) -> GlobalOptions:  # V3.9.11
    rpc_url = args.rpc_url or _resolve_env_rpc_url()
    wallet_address = args.wallet_address or _resolve_env_wallet()
    private_key = args.private_key or _resolve_env_private_key()
    minichef = args.minichef
    run_id = args.run_id or f"cli-{int(time.time())}"
    platform = args.platform or DEFAULT_PLATFORM
    chain = args.chain or DEFAULT_CHAIN
    lp_decimals = int(args.lp_decimals or DEFAULT_LP_DECIMALS)
    chain_id = int(args.chain_id or DEFAULT_CHAIN_ID)
    return GlobalOptions(
        rpc_url=rpc_url,
        wallet_address=wallet_address,
        private_key=private_key,
        minichef=minichef,
        run_id=run_id,
        platform=platform,
        chain=chain,
        lp_decimals=lp_decimals,
        chain_id=chain_id,
    )


def _print_summary(action: str, opts: GlobalOptions, pid: int, amount: Optional[float]) -> None:  # V3.9.11
    print("────────────────────────────────────────")
    print(f"Action : {action}")
    print(f"MiniChef : {opts.minichef or 'inconnu'}")
    print(f"PID : {pid}")
    print(f"Wallet : {opts.wallet_address or 'non défini'}")
    if amount is not None:
        print(f"Montant LP : {amount}")
    print("────────────────────────────────────────")


def _handle_harvest(args: argparse.Namespace, opts: GlobalOptions) -> int:  # V3.9.11
    pid = int(args.pid)
    _print_summary("harvest", opts, pid, None)

    dry_run = bool(args.dry_run)
    web3_available = Web3 is not None
    private_key = opts.private_key
    wallet = opts.wallet_address
    minichef = opts.minichef
    rpc_url = opts.rpc_url

    reason_for_dry_run = None
    if not dry_run:
        if not args.confirm:
            reason_for_dry_run = "Ajoutez --confirm pour exécuter en réel."
        elif not private_key:
            reason_for_dry_run = "Clé privée introuvable (argument ou PRIVATE_KEY)."
        elif not wallet or not _is_valid_address(wallet):
            reason_for_dry_run = "Adresse wallet invalide."
        elif not minichef or not _is_valid_address(minichef):
            reason_for_dry_run = "Adresse MiniChef invalide."
        elif not rpc_url:
            reason_for_dry_run = "Aucune URL RPC disponible."
        elif not web3_available:
            reason_for_dry_run = "Bibliothèque web3 indisponible : exécution en simulation."

    if reason_for_dry_run is not None:
        dry_run = True
        print(f"ℹ️  Mode simulation forcé : {reason_for_dry_run}")

    if dry_run:
        print("✅ Action simulée : récolte des récompenses non envoyée.")
        payload = _build_log_payload(
            opts,
            action="harvest",
            pid=pid,
            amount_requested=None,
            amount_effective=None,
            tx_status="dry-run",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"simulated": True},
            dry_run=True,
        )
        enregistrer_farming(**payload)
        return 0

    w3 = _connect_web3(rpc_url)
    if w3 is None:
        print("❌ Impossible de se connecter au RPC. Bascule en simulation.")
        payload = _build_log_payload(
            opts,
            action="harvest",
            pid=pid,
            amount_requested=None,
            amount_effective=None,
            tx_status="dry-run",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"simulated": True},
            dry_run=True,
        )
        enregistrer_farming(**payload)
        return 1

    try:
        wallet_checksum = _to_checksum(wallet, w3)
        minichef_checksum = _to_checksum(minichef, w3)
        contract = _get_minichef_contract(w3, minichef_checksum)
        function = contract.functions.harvest(pid, wallet_checksum)
        gas_price = int(args.gas_price or w3.eth.gas_price)
        gas_estimate = function.estimate_gas({"from": wallet_checksum})
        gas_limit = _apply_gas_buffer(gas_estimate)
        nonce = w3.eth.get_transaction_count(wallet_checksum)
        tx_data = function.build_transaction(
            {
                "from": wallet_checksum,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": opts.chain_id,
            }
        )
        if Account is None:
            raise RuntimeError("Module eth-account indisponible")
        signed_tx = Account.from_key(private_key).sign_transaction(tx_data)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"⏳ Transaction envoyée : {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        status = receipt.status
        gas_used = receipt.gasUsed
        effective_gas_price = getattr(receipt, "effectiveGasPrice", gas_price)
        tx_cost_native = _format_wei_to_native(gas_used * effective_gas_price)
        if status == 1:
            print("✅ Récolte confirmée.")
        else:
            print("⚠️ Transaction retournée avec un statut d'échec.")
        print(f"Hash        : {tx_hash.hex()}")
        print(f"Gas utilisé : {gas_used}")
        print(f"Gas effectif: {effective_gas_price}")
        print(f"Coût MATIC  : {tx_cost_native}")

        payload = _build_log_payload(
            opts,
            action="harvest",
            pid=pid,
            amount_requested=None,
            amount_effective=None,
            tx_status="success" if status == 1 else "error",
            tx_hash=tx_hash.hex(),
            gas_used=gas_used,
            effective_gas_price=effective_gas_price,
            tx_cost_native=tx_cost_native,
            balances_after={"tx_status": status},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 0 if status == 1 else 2
    except ContractLogicError as exc:  # pragma: no cover - dépend du RPC
        print(f"❌ Erreur logique du contrat : {exc}")
        payload = _build_log_payload(
            opts,
            action="harvest",
            pid=pid,
            amount_requested=None,
            amount_effective=None,
            tx_status="error",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"error": str(exc)},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 2
    except Exception as exc:  # pragma: no cover - gestion générique
        print(f"❌ Échec de la récolte réelle : {exc}")
        payload = _build_log_payload(
            opts,
            action="harvest",
            pid=pid,
            amount_requested=None,
            amount_effective=None,
            tx_status="error",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"error": str(exc)},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 2


def _handle_unstake(args: argparse.Namespace, opts: GlobalOptions) -> int:  # V3.9.11
    pid = int(args.pid)
    amount = float(args.amount)
    try:
        amount_wei = _format_amount_to_wei(amount, opts.lp_decimals)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2

    _print_summary("unstake", opts, pid, amount)

    dry_run_requested = bool(args.dry_run)
    dry_run = dry_run_requested

    web3_available = Web3 is not None
    private_key = opts.private_key
    wallet = opts.wallet_address
    minichef = opts.minichef
    rpc_url = opts.rpc_url

    reason_for_dry_run = None
    if not dry_run:
        if not args.confirm:
            reason_for_dry_run = "Ajoutez --confirm pour exécuter en réel."
        elif not private_key:
            reason_for_dry_run = "Clé privée introuvable (argument ou PRIVATE_KEY)."
        elif not wallet or not _is_valid_address(wallet):
            reason_for_dry_run = "Adresse wallet invalide."
        elif not minichef or not _is_valid_address(minichef):
            reason_for_dry_run = "Adresse MiniChef invalide."
        elif pid < 0:
            reason_for_dry_run = "PID invalide."
        elif amount_wei <= 0:
            reason_for_dry_run = "Le montant doit être supérieur à zéro."
        elif not rpc_url:
            reason_for_dry_run = "Aucune URL RPC disponible."
        elif not web3_available:
            reason_for_dry_run = "Bibliothèque web3 indisponible : exécution en simulation."

    if reason_for_dry_run:
        dry_run = True
        print(f"ℹ️  Mode simulation forcé : {reason_for_dry_run}")

    if dry_run:
        print("✅ Action simulée : retrait non envoyé.")
        payload = _build_log_payload(
            opts,
            action="unstake",
            pid=pid,
            amount_requested=amount,
            amount_effective=None,
            tx_status="dry-run",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"simulated_amount": amount},
            dry_run=True,
        )
        enregistrer_farming(**payload)
        return 0

    w3 = _connect_web3(rpc_url)
    if w3 is None:
        print("❌ Impossible de se connecter au RPC. Bascule en simulation.")
        payload = _build_log_payload(
            opts,
            action="unstake",
            pid=pid,
            amount_requested=amount,
            amount_effective=None,
            tx_status="dry-run",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"simulated_amount": amount},
            dry_run=True,
        )
        enregistrer_farming(**payload)
        return 1

    try:
        wallet_checksum = _to_checksum(wallet, w3)
        minichef_checksum = _to_checksum(minichef, w3)
        contract = _get_minichef_contract(w3, minichef_checksum)
        function = contract.functions.withdraw(pid, amount_wei, wallet_checksum)
        gas_price = int(args.gas_price or w3.eth.gas_price)
        gas_estimate = function.estimate_gas({"from": wallet_checksum})
        gas_limit = _apply_gas_buffer(gas_estimate)
        nonce = w3.eth.get_transaction_count(wallet_checksum)
        tx_data = function.build_transaction(
            {
                "from": wallet_checksum,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": opts.chain_id,
            }
        )
        if Account is None:
            raise RuntimeError("Module eth-account indisponible")
        signed_tx = Account.from_key(private_key).sign_transaction(tx_data)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"⏳ Transaction envoyée : {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        status = receipt.status
        gas_used = receipt.gasUsed
        effective_gas_price = getattr(receipt, "effectiveGasPrice", gas_price)
        tx_cost_native = _format_wei_to_native(gas_used * effective_gas_price)
        if status == 1:
            print("✅ Retrait confirmé.")
        else:
            print("⚠️ Transaction retournée avec un statut d'échec.")
        print(f"Hash        : {tx_hash.hex()}")
        print(f"Gas utilisé : {gas_used}")
        print(f"Gas effectif: {effective_gas_price}")
        print(f"Coût MATIC  : {tx_cost_native}")

        payload = _build_log_payload(
            opts,
            action="unstake",
            pid=pid,
            amount_requested=amount,
            amount_effective=float(Decimal(amount_wei) / Decimal(10 ** opts.lp_decimals)),
            tx_status="success" if status == 1 else "error",
            tx_hash=tx_hash.hex(),
            gas_used=gas_used,
            effective_gas_price=effective_gas_price,
            tx_cost_native=tx_cost_native,
            balances_after={"amount_wei": str(amount_wei), "tx_status": status},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 0 if status == 1 else 2
    except ContractLogicError as exc:  # pragma: no cover - dépend du RPC
        print(f"❌ Erreur logique du contrat : {exc}")
        payload = _build_log_payload(
            opts,
            action="unstake",
            pid=pid,
            amount_requested=amount,
            amount_effective=None,
            tx_status="error",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"error": str(exc)},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 2
    except Exception as exc:  # pragma: no cover - gestion générique
        print(f"❌ Échec du retrait réel : {exc}")
        payload = _build_log_payload(
            opts,
            action="unstake",
            pid=pid,
            amount_requested=amount,
            amount_effective=None,
            tx_status="error",
            tx_hash=None,
            gas_used=None,
            effective_gas_price=None,
            tx_cost_native=None,
            balances_after={"error": str(exc)},
            dry_run=False,
        )
        enregistrer_farming(**payload)
        return 2


def _handle_stake(args: argparse.Namespace, opts: GlobalOptions) -> int:  # V3.9.11
    pid = int(args.pid)
    amount = float(args.amount)
    _print_summary("stake", opts, pid, amount)
    print("✅ Action simulée : le stake reste en mode simulation dans cette version.")
    payload = _build_log_payload(
        opts,
        action="stake",
        pid=pid,
        amount_requested=amount,
        amount_effective=None,
        tx_status="dry-run",
        tx_hash=None,
        gas_used=None,
        effective_gas_price=None,
        tx_cost_native=None,
        balances_after={"simulated_amount": amount},
        dry_run=True,
    )
    enregistrer_farming(**payload)
    return 0


def build_parser() -> argparse.ArgumentParser:  # V3.9.11
    parser = argparse.ArgumentParser(
        prog="farming_cli.py",
        description="DeFiPilot – Farming SushiSwap MiniChef V2 (Polygon)",
    )

    parser.add_argument("--rpc-url", dest="rpc_url", help="URL RPC Polygon")
    parser.add_argument(
        "--wallet-address",
        dest="wallet_address",
        help="Adresse checksum du wallet utilisateur",
    )
    parser.add_argument(
        "--private-key",
        dest="private_key",
        help="Clé privée associée au wallet (ou utilisez PRIVATE_KEY)",
    )
    parser.add_argument(
        "--minichef",
        dest="minichef",
        required=True,
        help="Adresse du contrat MiniChefV2",
    )
    parser.add_argument("--run-id", dest="run_id", help="Identifiant de run pour le journal")
    parser.add_argument(
        "--platform",
        dest="platform",
        default=DEFAULT_PLATFORM,
        help="Plateforme utilisée (défaut: sushiswap)",
    )
    parser.add_argument(
        "--chain",
        dest="chain",
        default=DEFAULT_CHAIN,
        help="Nom de la chaîne (défaut: polygon)",
    )
    parser.add_argument(
        "--lp-decimals",
        dest="lp_decimals",
        type=int,
        default=DEFAULT_LP_DECIMALS,
        help="Décimales du token LP (défaut: 18)",
    )
    parser.add_argument(
        "--chain-id",
        dest="chain_id",
        type=int,
        default=DEFAULT_CHAIN_ID,
        help="Chain ID EVM (défaut: 137 pour Polygon)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    harvest_parser = subparsers.add_parser("harvest", help="Récolter les récompenses")
    harvest_parser.add_argument("--pid", type=int, required=True, help="Identifiant du pool")
    harvest_parser.add_argument("--dry-run", action="store_true", help="Simulation sans envoi")
    harvest_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirme l'exécution réelle",
    )
    harvest_parser.add_argument(
        "--gas-price",
        type=int,
        dest="gas_price",
        help="Gas price en wei (optionnel)",
    )

    unstake_parser = subparsers.add_parser("unstake", help="Retirer des LP du pool")
    unstake_parser.add_argument("--pid", type=int, required=True, help="Identifiant du pool")
    unstake_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Montant LP à retirer (format utilisateur)",
    )
    unstake_parser.add_argument("--dry-run", action="store_true", help="Simulation sans envoi")
    unstake_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirme l'exécution réelle",
    )
    unstake_parser.add_argument(
        "--gas-price",
        type=int,
        dest="gas_price",
        help="Gas price en wei (optionnel)",
    )

    stake_parser = subparsers.add_parser("stake", help="Déposer des LP (simulation)")
    stake_parser.add_argument("--pid", type=int, required=True, help="Identifiant du pool")
    stake_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Montant LP à déposer (simulation)",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:  # V3.9.11
    parser = build_parser()
    args = parser.parse_args(argv)
    opts = parse_global_options(args)

    if args.command == "harvest":
        return _handle_harvest(args, opts)
    if args.command == "unstake":
        return _handle_unstake(args, opts)
    if args.command == "stake":
        return _handle_stake(args, opts)

    print("Commande inconnue.")
    return 2


if __name__ == "__main__":  # V3.9.11
    sys.exit(main())

# Tests manuels recommandés :
# A) Dry-run :
#    python farming_cli.py --rpc-url https://polygon-rpc.com \
#      --wallet-address 0x... --minichef 0x... \
#      unstake --pid 1 --amount 1e-12 --dry-run
# B) Réel sans --confirm :
#    python farming_cli.py --rpc-url https://polygon-rpc.com \
#      --wallet-address 0x... --private-key "$PRIVATE_KEY" --minichef 0x... \
#      unstake --pid 1 --amount 1e-12
# C) Réel avec --confirm :
#    python farming_cli.py --rpc-url https://polygon-rpc.com \
#      --wallet-address 0x... --private-key "$PRIVATE_KEY" --minichef 0x... \
#      unstake --pid 1 --amount 1e-12 --confirm