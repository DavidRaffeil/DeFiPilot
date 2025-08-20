# core/liquidity_dryrun.py – V3.8
from __future__ import annotations

from uuid import uuid4
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any, Dict, Optional, Tuple

# Précision suffisante pour nos calculs hors-chaîne
getcontext().prec = 28


# ----------------------------- Utilitaires internes -----------------------------

def _validate_pool(pool: Dict[str, Any]) -> None:
    if not isinstance(pool, dict):
        raise ValueError("pool doit être un dictionnaire")

    for key in ("platform", "chain", "tokenA_symbol", "tokenB_symbol"):
        value = pool.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"pool['{key}'] doit être une chaîne non vide")

    for dec_key, default in (("decimalsA", 6), ("decimalsB", 18)):
        dec_val = pool.get(dec_key, default)
        if not isinstance(dec_val, int) or dec_val < 0:
            raise ValueError(f"pool['{dec_key}'] doit être un entier positif")

    for opt_key in ("reservesA", "reservesB", "totalSupplyLP"):
        if opt_key in pool:
            val = pool[opt_key]
            if not isinstance(val, (int, float)) or val < 0:
                raise ValueError(f"pool['{opt_key}'] doit être un nombre positif")


def _to_decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def _round(value: Decimal, quant: str) -> float:
    return float(value.quantize(Decimal(quant), rounding=ROUND_HALF_UP))


def _apply_slippage(amount: Decimal, slippage_pct: Decimal) -> Decimal:
    # slippage_pct est en pourcentage (ex: 0.5 pour 0.5%)
    return amount * (Decimal("1") - slippage_pct / Decimal("100"))


def _enforce_ratio(
    amountA: Decimal,
    amountB: Decimal,
    resA: Optional[Decimal],
    resB: Optional[Decimal],
) -> Tuple[Decimal, Decimal, str]:
    ratio_contraint = "none"
    if resA is not None and resB is not None and resA > 0 and resB > 0:
        r = resA / resB
        amountA_needed = amountB * r
        amountB_needed = amountA / r

        if amountA < amountA_needed:
            amountB = amountA / r
            ratio_contraint = "A"
        elif amountB < amountB_needed:
            amountA = amountB * r
            ratio_contraint = "B"
    return amountA, amountB, ratio_contraint


def _estimate_lp(
    amountA_eff: Decimal,
    amountB_eff: Decimal,
    resA: Optional[Decimal],
    resB: Optional[Decimal],
    total_lp: Optional[Decimal],
) -> Tuple[Decimal, str]:
    # Cas 1 : réserves et total LP connus → estimation absolue
    if (
        resA is not None
        and resB is not None
        and total_lp is not None
        and resA > 0
        and resB > 0
        and total_lp > 0
    ):
        liquidityA = amountA_eff * total_lp / resA
        liquidityB = amountB_eff * total_lp / resB
        return min(liquidityA, liquidityB), "OK"

    # Cas 2 : réserves connues sans total LP → fraction des parts
    if resA is not None and resB is not None and resA > 0 and resB > 0:
        fractionA = amountA_eff / resA
        fractionB = amountB_eff / resB
        return min(fractionA, fractionB), "approx_fraction"

    # Cas 3 : bootstrap sans réserves → racine du produit
    lp = (amountA_eff * amountB_eff).sqrt()
    return lp, "approx_bootstrap"


# -------------------------------- Fonction publique --------------------------------

def simuler_ajout_liquidite(
    pool: Dict[str, Any],
    amountA: float,
    amountB: float,
    slippage_bps: int = 50,
) -> Dict[str, Any]:
    """Simule un ajout de liquidité (dry-run) sans appel réseau.

    Args:
        pool: Dictionnaire décrivant la pool (plateforme, chaîne, symboles, réserves…)
        amountA: Montant du token A (unités humaines)
        amountB: Montant du token B (unités humaines)
        slippage_bps: Tolérance de slippage en basis points (50 = 0.5%)
    """
    if amountA <= 0 or amountB <= 0:
        raise ValueError("Les montants doivent être strictement positifs")
    if slippage_bps < 0:
        raise ValueError("slippage_bps doit être >= 0")

    _validate_pool(pool)

    resA = _to_decimal(pool["reservesA"]) if "reservesA" in pool else None
    resB = _to_decimal(pool["reservesB"]) if "reservesB" in pool else None
    total_lp = _to_decimal(pool["totalSupplyLP"]) if "totalSupplyLP" in pool else None

    amtA = _to_decimal(amountA)
    amtB = _to_decimal(amountB)
    # Convertit bps → % (ex: 50 bps = 0.5)
    slippage_pct = _to_decimal(slippage_bps) / Decimal("100")

    amtA_eff = _apply_slippage(amtA, slippage_pct)
    amtB_eff = _apply_slippage(amtB, slippage_pct)

    amtA_eff, amtB_eff, ratio_contraint = _enforce_ratio(amtA_eff, amtB_eff, resA, resB)

    lp_estime, detail = _estimate_lp(amtA_eff, amtB_eff, resA, resB, total_lp)

    # ID de run utile pour tracer la simulation
    run_id = str(uuid4())

    return {
        "run_id": run_id,
        "platform": pool["platform"],
        "chain": pool["chain"],
        "tokenA_symbol": pool["tokenA_symbol"],
        "tokenB_symbol": pool["tokenB_symbol"],
        "amountA": float(amountA),
        "amountB": float(amountB),
        "amountA_effectif": _round(amtA_eff, "0.000001"),
        "amountB_effectif": _round(amtB_eff, "0.000001"),
        "lp_tokens_estimes": _round(lp_estime, "0.00000001"),
        "slippage_applique_pct": float(slippage_pct),
        "ratio_contraint": ratio_contraint,
        "details": detail,
    }


if __name__ == "__main__":
    exemple_pool = {
        "platform": "sushiswap",
        "chain": "polygon",
        "tokenA_symbol": "USDC",
        "tokenB_symbol": "WETH",
        "reservesA": 1_000_000.0,
        "reservesB": 1_000.0,
        "decimalsA": 6,
        "decimalsB": 18,
        "totalSupplyLP": 50_000.0,
    }
    result = simuler_ajout_liquidite(exemple_pool, 10.0, 0.01, slippage_bps=50)
    print(result)
