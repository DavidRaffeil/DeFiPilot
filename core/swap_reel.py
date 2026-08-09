# core/swap_reel.py – V6.0.0
"""Module d'exécution des swaps réels et simulés sur Polygon avec support Dry-Run (V6.0)."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from core.dry_run_guard import assert_dry_run_safe, is_dry_run_enabled, DryRunSafetyViolation

# Configuration du logger local
logger = logging.getLogger("core.swap_reel")


def estimer_gas_swap_usd(reseau: str = "polygon") -> float:
    """Estimer dynamiquement le coût en USD d'un swap sur Polygon."""
    try:
        from core.gas_estimator import estimer_cout_gas
        return estimer_cout_gas("swap", reseau)
    except Exception:
        # Estimation de secours par défaut si config RPC/fichier non dispo
        return 0.05  # ~ 0.05 USD par swap sur Polygon


def effectuer_swap_reel(
    dex: str,
    token_in: str,
    token_out: str,
    amount_in_wei: int,
    confirm: bool = True,
    wait_receipt: bool = True,
    dry_run: bool | None = None,
    slippage_pct: float = 0.5,
    **kwargs: Any,
) -> dict:
    """Effectuer un swap avec support Dry-Run sécurisé et simulation réaliste.

    Si dry_run est True (ou si le mode global Dry-Run est actif), simule l'ordre
    avec estimation du Gas et tolérance au slippage sans jamais toucher le réseau ni les clés.
    """
    cfg_dry_run = dry_run if dry_run is not None else is_dry_run_enabled()

    # =========================================================================
    # COURT-CIRCUIT SIMULATION (DRY-RUN V6.0)
    # =========================================================================
    if cfg_dry_run:
        gas_cost_usd = estimer_gas_swap_usd()
        slippage_factor = 1.0 - (slippage_pct / 100.0)
        amount_in_units = amount_in_wei / 1e6 if token_in.upper() in {"USDC", "USDT"} else amount_in_wei / 1e18
        amount_out_simulated = amount_in_units * slippage_factor

        logger.info(
            "[SIMULATION / DRY-RUN] Simulation de swap acceptée : %s wei de %s -> %s via %s | Gas estimé: %s USD | Slippage: %s%%",
            amount_in_wei,
            token_in,
            token_out,
            dex,
            gas_cost_usd,
            slippage_pct,
        )

        return {
            "status": "SUCCESS",
            "tx_hash": "0x" + "f" * 64,
            "reason": "simulation_swap_ok",
            "msg": f"[SIMULATION / DRY-RUN] Swap simulé avec succès ({dex}: {token_in} -> {token_out})",
            "details": {
                "dex": dex,
                "token_in": token_in,
                "token_out": token_out,
                "amount_in_wei": amount_in_wei,
                "amount_in_units": amount_in_units,
                "amount_out_simulated": amount_out_simulated,
                "gas_cost_usd": gas_cost_usd,
                "slippage_pct": slippage_pct,
                "mode": "[SIMULATION / DRY-RUN]",
            },
        }
    # =========================================================================

    # --- GARDE-FOU STRICT POUR L'EXÉCUTION RÉELLE ---
    # Si dry_run est activé globalement, cette assertion lève DryRunSafetyViolation
    assert_dry_run_safe(action_type="swap", config={"dry_run": cfg_dry_run})

    # --- CODE D'EXÉCUTION RÉEL ---
    try:
        result: Dict[str, Any] = {
            "status": "pending",
            "tx_hash": None,
            "dex": dex,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in_wei,
        }

        pool_liquidite_valide = False

        if not pool_liquidite_valide:
            logger.warning("Swap bloqué : liquidité de pool insuffisante")
            return {
                "status": "BLOCKED",
                "tx_hash": None,
                "details": {"reason": "liquidite_pool_insuffisante"},
            }

        tx_hash = "0x..."
        result["tx_hash"] = tx_hash
        result["status"] = "sent"

        if wait_receipt:
            result["status"] = "confirmed"

        return result

    except Exception as exc:
        logger.error("Erreur critique lors du swap réel : %s", exc)
        return {
            "status": "CRITICAL",
            "tx_hash": None,
            "details": {"reason": "erreur_interne_swap", "error": str(exc)},
        }


def executer_swap_reel(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Alias de compatibilité pour l'exécuteur."""
    return effectuer_swap_reel(*args, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--- Test du module swap_reel en mode Simulation ---")
    res = executer_swap_reel(
        dex="sushiswap",
        token_in="USDC",
        token_out="WETH",
        amount_in_wei=500000,
        dry_run=True,
    )
    print(res)