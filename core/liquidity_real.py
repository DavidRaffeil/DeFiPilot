# core/liquidity_real.py – V3.8
# Fichier NOUVEAU – Ajout de liquidité (dry-run ou réel Uniswap/Sushiswap V2)

import csv
import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from web3 import Web3

from core.real_wallet import get_wallet_address, get_private_key, get_web3

logger = logging.getLogger("core.liquidity_real")
if not logger.handlers:
    logger.setLevel(logging.INFO)
logger.debug("Module core.liquidity_real initialisé (V3.8)")

_LOG_FILE = "journal_liquidite.csv"
_HEADERS = [
    "date",
    "plateforme",
    "tokenA",
    "montantA",
    "tokenB",
    "montantB",
    "destinataire",
    "statut",         # 'success' / 'erreur'
    "message",
    "tx_hash",
    "gas_used",
    "status",         # statut receipt EVM (1/0)
    "slippage_bps",
    "deadline_min",
]

def _journaliser(
    date: str,
    plateforme: Any,
    tokenA: Any,
    montantA: float,
    tokenB: Any,
    montantB: float,
    destinataire: Optional[str],
    statut: str,
    message: str,
    tx_hash: Optional[str],
    gas_used: Optional[int],
    status: Optional[str],
    slippage_bps: int,
    deadline_min: int,
) -> None:
    """Ajoute une ligne au journal CSV (ne doit jamais faire planter l'app)."""
    try:
        existe = True
        try:
            with open(_LOG_FILE, "r", encoding="utf-8"):
                pass
        except FileNotFoundError:
            existe = False

        with open(_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow(_HEADERS)
            writer.writerow(
                [
                    date,
                    plateforme,
                    tokenA,
                    montantA,
                    tokenB,
                    montantB,
                    destinataire or "",
                    statut,
                    message,
                    tx_hash or "",
                    gas_used if gas_used is not None else "",
                    status or "",
                    slippage_bps,
                    deadline_min,
                ]
            )
    except Exception as exc:  # pragma: no cover
        logger.error("Erreur journalisation CSV: %s", exc)


# ABIs minimales
ERC20_ABI_MIN = [
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
]

ROUTER_V2_ABI = [
    {
        "name": "addLiquidity",
        "outputs": [
            {"name": "amountA", "type": "uint256"},
            {"name": "amountB", "type": "uint256"},
            {"name": "liquidity", "type": "uint256"},
        ],
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"},
            {"name": "amountADesired", "type": "uint256"},
            {"name": "amountBDesired", "type": "uint256"},
            {"name": "amountAMin", "type": "uint256"},
            {"name": "amountBMin", "type": "uint256"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def _iso_utc() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def ajouter_liquidite_reelle(
    pool: Dict[str, Any],
    montant_tokenA: float,
    montant_tokenB: float,
    dry_run: bool = True,
    destinataire: Optional[str] = None,
    slippage_bps: int = 100,
    deadline_mins: int = 20,
    router_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ajoute de la liquidité sur un DEX Uniswap/Sushiswap V2.
    - dry_run=True : simulation (aucune transaction)
    - dry_run=False : envoi réel (approve + addLiquidity)
    """
    logger.info(
        "Paramètres reçus: pool=%s, montant_tokenA=%s, montant_tokenB=%s, dry_run=%s, destinataire=%s",
        pool, montant_tokenA, montant_tokenB, dry_run, destinataire,
    )

    plateforme = pool.get("platform")
    tokenA = pool.get("tokenA_symbol")
    tokenB = pool.get("tokenB_symbol")
    tokenA_addr = pool.get("tokenA_address")
    tokenB_addr = pool.get("tokenB_address")
    chain = pool.get("chain")
    router = router_override or pool.get("router_address")

    # Validation montants
    if montant_tokenA <= 0 or montant_tokenB <= 0:
        message = "Montants tokenA et tokenB doivent être > 0"
        logger.error(message)
        _journaliser(
            _iso_utc(),
            plateforme,
            tokenA,
            montant_tokenA,
            tokenB,
            montant_tokenB,
            destinataire,
            "erreur",
            message,
            None,
            None,
            None,
            slippage_bps,
            deadline_mins,
        )
        return {
            "success": False,
            "platform": plateforme,
            "tokenA": tokenA,
            "tokenB": tokenB,
            "montantA": montant_tokenA,
            "montantB": montant_tokenB,
            "message": message,
            "dry_run": dry_run,
        }

    # MODE DRY-RUN (inchangé)
    if dry_run:
        logger.info("Simulation approval de %s (%s)", tokenA, tokenA_addr)
        logger.info("Simulation approval de %s (%s)", tokenB, tokenB_addr)
        logger.info("Simulation appel du routeur %s sur %s", router, chain)

        message = "Simulation d'ajout de liquidité effectuée"
        _journaliser(
            _iso_utc(),
            plateforme,
            tokenA,
            montant_tokenA,
            tokenB,
            montant_tokenB,
            destinataire,
            "success",
            message,
            None,
            None,
            None,
            slippage_bps,
            deadline_mins,
        )
        return {
            "success": True,
            "platform": plateforme,
            "tokenA": tokenA,
            "tokenB": tokenB,
            "montantA": montant_tokenA,
            "montantB": montant_tokenB,
            "message": message,
            "dry_run": True,
        }

    # MODE RÉEL
    try:
        w3 = get_web3()
        wallet_address = get_wallet_address()
        private_key = get_private_key()

        if not w3 or not wallet_address or not private_key:
            raise RuntimeError("Wallet ou connexion Web3 introuvable")
        if not router:
            raise RuntimeError("Adresse router manquante")
        if not tokenA_addr or not tokenB_addr:
            raise RuntimeError("Adresse tokenA/tokenB manquante")

        tokenA_c = w3.eth.contract(
            address=Web3.to_checksum_address(tokenA_addr), abi=ERC20_ABI_MIN
        )
        tokenB_c = w3.eth.contract(
            address=Web3.to_checksum_address(tokenB_addr), abi=ERC20_ABI_MIN
        )
        router_c = w3.eth.contract(
            address=Web3.to_checksum_address(router), abi=ROUTER_V2_ABI
        )

        # Décimales et montants
        decimalsA = tokenA_c.functions.decimals().call()
        decimalsB = tokenB_c.functions.decimals().call()
        amountA = int(Decimal(str(montant_tokenA)) * (10 ** decimalsA))
        amountB = int(Decimal(str(montant_tokenB)) * (10 ** decimalsB))

        # Slippage et deadline
        slippage_factor = Decimal(10000 - slippage_bps) / Decimal(10000)
        amountAMin = int(Decimal(amountA) * slippage_factor)
        amountBMin = int(Decimal(amountB) * slippage_factor)
        deadline = int(time.time()) + 60 * deadline_mins

        # Prépare environnement tx
        nonce = w3.eth.get_transaction_count(wallet_address)
        gas_price = w3.eth.gas_price

        # Approvals si nécessaire
        for contract, raw_amount in ((tokenA_c, amountA), (tokenB_c, amountB)):
            allowance = contract.functions.allowance(wallet_address, router).call()
            if allowance < raw_amount:
                tx = contract.functions.approve(router, raw_amount).build_transaction(
                    {
                        "from": wallet_address,
                        "gasPrice": gas_price,
                        "nonce": nonce,
                        "chainId": w3.eth.chain_id,
                    }
                )
                gas_est = w3.eth.estimate_gas(tx)
                tx["gas"] = int(gas_est * 1.2)
                signed = w3.eth.account.sign_transaction(tx, private_key)
                txh = w3.eth.send_raw_transaction(signed.rawTransaction)
                w3.eth.wait_for_transaction_receipt(txh)
                nonce += 1

        # addLiquidity
        tx = router_c.functions.addLiquidity(
            Web3.to_checksum_address(tokenA_addr),
            Web3.to_checksum_address(tokenB_addr),
            amountA,
            amountB,
            amountAMin,
            amountBMin,
            destinataire or wallet_address,
            deadline,
        ).build_transaction(
            {
                "from": wallet_address,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": w3.eth.chain_id,
            }
        )
        gas_est = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_est * 1.2)

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        status_str = str(receipt.status)
        gas_used = receipt.gasUsed

        message = "Transaction confirmée"
        _journaliser(
            _iso_utc(),
            plateforme,
            tokenA,
            montant_tokenA,
            tokenB,
            montant_tokenB,
            destinataire,
            "success",
            message,
            tx_hash.hex(),
            gas_used,
            status_str,
            slippage_bps,
            deadline_mins,
        )
        return {
            "success": True,
            "platform": plateforme,
            "tokenA": tokenA,
            "tokenB": tokenB,
            "montantA": montant_tokenA,
            "montantB": montant_tokenB,
            "message": message,
            "tx_hash": tx_hash.hex(),
            "gas_used": gas_used,
            "dry_run": False,
        }

    except Exception as exc:  # pragma: no cover
        message = f"Echec ajout liquidité: {exc}"
        logger.error(message)
        _journaliser(
            _iso_utc(),
            plateforme,
            tokenA,
            montant_tokenA,
            tokenB,
            montant_tokenB,
            destinataire,
            "erreur",
            message,
            None,
            None,
            None,
            slippage_bps,
            deadline_mins,
        )
        return {
            "success": False,
            "platform": plateforme,
            "tokenA": tokenA,
            "tokenB": tokenB,
            "montantA": montant_tokenA,
            "montantB": montant_tokenB,
            "message": message,
            "dry_run": False,
        }
