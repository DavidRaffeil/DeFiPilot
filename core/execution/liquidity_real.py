# core/liquidity_real.py – V3.8
# Fichier NOUVEAU — Dry-run de l'ajout de liquidité (aucune transaction réelle)
# Objectif : normaliser et consigner les adresses (router, wallet, tokens) au format checksum
# Remarque : ce module NE réalise AUCUNE interaction on-chain. Il prépare les journaux et les logs.

from __future__ import annotations

import logging
import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional

from web3 import Web3
from core.real_wallet import get_wallet_address

# -------------------------------------------------------------
# Logger
# -------------------------------------------------------------
logger = logging.getLogger("core.liquidity_real")
if not logger.handlers:
    logger.setLevel(logging.INFO)
logger.debug("Module core.liquidity_real initialisé (dry-run V3.8)")

# -------------------------------------------------------------
# Journal CSV
# -------------------------------------------------------------
_LOG_FILE = "journal_liquidite.csv"
_HEADERS = [
    "date",
    "plateforme",
    "tokenA",
    "montantA",
    "tokenB",
    "montantB",
    "destinataire",
    "statut",
    "message",
]


def _ensure_csv_headers(path: str) -> None:
    """Crée le fichier CSV avec en-têtes s'il n'existe pas."""
    if not os.path.exists(path):
        with open(path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_HEADERS)
            writer.writeheader()


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
) -> None:
    """Écrit une ligne dans le journal CSV."""
    try:
        _ensure_csv_headers(_LOG_FILE)
        with open(_LOG_FILE, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_HEADERS)
            writer.writerow(
                {
                    "date": date,
                    "plateforme": plateforme,
                    "tokenA": tokenA,
                    "montantA": montantA,
                    "tokenB": tokenB,
                    "montantB": montantB,
                    "destinataire": destinataire or "",
                    "statut": statut,
                    "message": message,
                }
            )
    except Exception as e:
        logger.error("Échec de journalisation CSV: %s", e)


# -------------------------------------------------------------
# API publique
# -------------------------------------------------------------

def ajouter_liquidite_reelle(
    pool: Dict[str, Any],
    montant_tokenA: float,
    montant_tokenB: float,
    dry_run: bool = True,
    destinataire: Optional[str] = None,
    slippage_bps: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Simule l'ajout de liquidité réelle (dry-run, aucune transaction).

    Note : paramètres additionnels pris en charge sans effet en dry-run :
    - slippage_bps (int | None): ignoré ici, seulement journalisé.
    - **kwargs : acceptés pour compatibilité CLI (deadline, auto_approve, etc.).

    Paramètres
    ----------
    pool : dict
        { platform, tokenA_symbol, tokenB_symbol, tokenA_address, tokenB_address, router_address, chain }
    montant_tokenA : float
    montant_tokenB : float
    dry_run : bool
        Toujours True dans cette version (simulation uniquement). Si False est fourni, on le force à True.
    destinataire : str | None
        Adresse de réception des LP. Si None, utilise l'adresse du wallet actif.
    """
    logger.info(
        "Paramètres reçus: pool=%s, montant_tokenA=%s, montant_tokenB=%s, dry_run=%s, destinataire=%s, slippage_bps=%s, extras=%s",
        pool,
        montant_tokenA,
        montant_tokenB,
        dry_run,
        destinataire,
        slippage_bps,
        kwargs,
    )

    # Lecture basique du pool
    plateforme = pool.get("platform")
    tokenA = pool.get("tokenA_symbol")
    tokenB = pool.get("tokenB_symbol")
    tokenA_addr_raw = pool.get("tokenA_address")
    tokenB_addr_raw = pool.get("tokenB_address")
    router_raw = pool.get("router_address")
    chain = pool.get("chain")

    # Normalisation checksum (affichage/log CSV uniquement dans ce module)
    router_checksum = Web3.to_checksum_address(router_raw) if router_raw else None
    tokenA_addr = Web3.to_checksum_address(tokenA_addr_raw) if tokenA_addr_raw else None
    tokenB_addr = Web3.to_checksum_address(tokenB_addr_raw) if tokenB_addr_raw else None

    # Wallet / destinataire (checksum même en dry-run pour des logs propres)
    wallet_address = get_wallet_address()
    wallet_checksum: Optional[str] = (
        Web3.to_checksum_address(wallet_address) if wallet_address else None
    )

    if destinataire:
        try:
            destinataire = Web3.to_checksum_address(destinataire)
        except Exception:
            logger.warning("Destinataire fourni invalide, utilisation du wallet actif")
            destinataire = wallet_checksum
    else:
        destinataire = wallet_checksum

    # Validation des montants
    if montant_tokenA <= 0 or montant_tokenB <= 0:
        message = "Montants tokenA et tokenB doivent être > 0"
        logger.error(message)
        _journaliser(
            datetime.utcnow().isoformat(),
            plateforme,
            tokenA,
            montant_tokenA,
            tokenB,
            montant_tokenB,
            destinataire,
            "erreur",
            message,
        )
        return {
            "success": False,
            "platform": plateforme,
            "tokenA": tokenA,
            "tokenB": tokenB,
            "montantA": montant_tokenA,
            "montantB": montant_tokenB,
            "message": message,
            "dry_run": True,
        }

    # Force dry-run (cette version ne doit jamais envoyer de tx)
    if not dry_run:
        logger.warning("dry_run=False demandé, force à True (simulation uniquement)")
        dry_run = True

    # Logs de simulation (approvals puis appel routeur)
    logger.info("Simulation approval de %s (%s) vers router %s", tokenA, tokenA_addr, router_checksum)
    logger.info("Simulation approval de %s (%s) vers router %s", tokenB, tokenB_addr, router_checksum)
    logger.info("Simulation appel du routeur %s sur %s, destinataire %s", router_checksum, chain, destinataire)

    message = "Simulation d'ajout de liquidité effectuée"
    _journaliser(
        datetime.utcnow().isoformat(),
        plateforme,
        tokenA,
        montant_tokenA,
        tokenB,
        montant_tokenB,
        destinataire,
        "success",
        message,
    )

    return {
        "success": True,
        "platform": plateforme,
        "tokenA": tokenA,
        "tokenB": tokenB,
        "montantA": montant_tokenA,
        "montantB": montant_tokenB,
        "router": router_checksum,
        "destinataire": destinataire,
        "message": message,
        "dry_run": True,
    }
