# core/liquidity_real.py – V3.8
# Fichier NOUVEAU – Dry-run de l'ajout de liquidité (aucune transaction réelle)

import logging
import csv
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("core.liquidity_real")
if not logger.handlers:
    logger.setLevel(logging.INFO)
logger.debug("Module core.liquidity_real initialisé (dry-run V3.8)")

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
    """Ajoute une ligne au journal CSV."""
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
                ]
            )
    except Exception as exc:  # pragma: no cover - la journalisation ne doit pas planter
        logger.error("Erreur journalisation CSV: %s", exc)


def ajouter_liquidite_reelle(
    pool: Dict[str, Any],
    montant_tokenA: float,
    montant_tokenB: float,
    dry_run: bool = True,
    destinataire: Optional[str] = None,
) -> Dict[str, Any]:
    """Simule l'ajout de liquidité réelle (sans transaction)."""
    logger.info(
        "Paramètres reçus: pool=%s, montant_tokenA=%s, montant_tokenB=%s, dry_run=%s, destinataire=%s",
        pool,
        montant_tokenA,
        montant_tokenB,
        dry_run,
        destinataire,
    )

    plateforme = pool.get("platform")
    tokenA = pool.get("tokenA_symbol")
    tokenB = pool.get("tokenB_symbol")
    tokenA_addr = pool.get("tokenA_address")
    tokenB_addr = pool.get("tokenB_address")
    router = pool.get("router_address")
    chain = pool.get("chain")

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

    if not dry_run:
        logger.warning("dry_run=False demandé, force à True (simulation uniquement)")

    logger.info("Simulation approval de %s (%s)", tokenA, tokenA_addr)
    logger.info("Simulation approval de %s (%s)", tokenB, tokenB_addr)
    logger.info("Simulation appel du routeur %s sur %s", router, chain)

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
        "message": message,
        "dry_run": True,
    }
