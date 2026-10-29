# core/dex/utils.py – V6.5.0
"""
Helpers et constantes partagés par les adaptateurs DEX.

Montants métier en Decimal, valeurs on-chain en entiers. Aucun float.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, localcontext
from typing import Any, Dict, List, Tuple

from web3 import Web3

from core.dex.exceptions import DEXQuoteError

CHAIN_ID_POLYGON: int = 137

# Précision suffisante pour les uint256 (78 chiffres)
DECIMAL_PREC: int = 80
# Fraction d'amount_in utilisée pour la cotation de référence (impact de prix)
REFERENCE_DIVISOR: int = 1000

ERC20_DECIMALS_ABI: List[Dict[str, Any]] = [
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    }
]


def to_raw_units(amount: Decimal, decimals: int) -> int:
    """Convertit un montant humain en entier on-chain (arrondi vers le bas)."""
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PREC
        return int(amount.scaleb(decimals).to_integral_value(rounding=ROUND_DOWN))


def from_raw_units(raw_amount: int, decimals: int) -> Decimal:
    """Convertit un entier on-chain en montant humain."""
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PREC
        return Decimal(raw_amount).scaleb(-decimals)


def apply_slippage_raw(expected_out_raw: int, slippage_tolerance: Decimal) -> int:
    """Montant minimum on-chain : expected * (1 - slippage), arrondi vers le bas."""
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PREC
        return int(
            (Decimal(expected_out_raw) * (Decimal(1) - slippage_tolerance))
            .to_integral_value(rounding=ROUND_DOWN)
        )


def compute_price_impact_pct(
    amount_in_raw: int, out_raw: int, ref_in_raw: int, ref_out_raw: int
) -> Decimal:
    """
    Impact de prix (%) : écart entre le prix d'exécution (out/in) et le prix de
    référence obtenu sur un petit montant (ref_out/ref_in). Jamais négatif.
    """
    if amount_in_raw <= 0 or ref_in_raw <= 0 or ref_out_raw <= 0:
        raise ValueError("montants de référence invalides")
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PREC
        exec_price = Decimal(out_raw) / Decimal(amount_in_raw)
        ref_price = Decimal(ref_out_raw) / Decimal(ref_in_raw)
        impact = (Decimal(1) - exec_price / ref_price) * Decimal(100)
    return max(impact, Decimal(0))


def validate_quote_inputs(
    token_in: str, token_out: str, amount_in: Decimal, slippage_tolerance: Decimal
) -> Tuple[str, str]:
    """Valide les entrées de get_quote. Retourne les adresses checksum (in, out)."""
    if isinstance(amount_in, float) or not isinstance(amount_in, Decimal):
        raise DEXQuoteError("amount_in doit être un Decimal")
    if isinstance(slippage_tolerance, float) or not isinstance(
        slippage_tolerance, Decimal
    ):
        raise DEXQuoteError("slippage_tolerance doit être un Decimal")
    if not amount_in.is_finite() or amount_in <= 0:
        raise DEXQuoteError("amount_in doit être strictement positif")
    if not slippage_tolerance.is_finite() or not (
        Decimal(0) <= slippage_tolerance < Decimal(1)
    ):
        raise DEXQuoteError("slippage_tolerance doit être dans [0, 1[")

    addresses = []
    for label, address in (("token_in", token_in), ("token_out", token_out)):
        if not isinstance(address, str) or not Web3.is_address(address):
            raise DEXQuoteError(f"{label} invalide : {address!r}")
        addresses.append(Web3.to_checksum_address(address))
    if addresses[0] == addresses[1]:
        raise DEXQuoteError("token_in et token_out sont identiques")
    return addresses[0], addresses[1]
