# core/dex/quickswap.py – V6.5.0
"""
Adaptateur QuickSwap V3 (Algebra, Polygon Mainnet) : cotation via le Quoter
et encodage des swaps via le SwapRouter (exactInputSingle avec deadline).

Les tokens sont identifiés par leur adresse ERC-20. Montants métier en Decimal,
valeurs on-chain en entiers (conservées dans `raw_quote_data`).
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from web3 import Web3

from core.dex.base import BaseDEXAdapter, DEXQuote
from core.dex.exceptions import DEXQuoteError, DEXTransactionError
from core.dex.utils import (
    CHAIN_ID_POLYGON,
    ERC20_DECIMALS_ABI,
    REFERENCE_DIVISOR,
    apply_slippage_raw,
    compute_price_impact_pct,
    from_raw_units,
    to_raw_units,
    validate_quote_inputs,
)

QUOTER_ADDRESS: str = "0xa15F52d4393694b4d17275d3c015bcf026f63a47"
SWAP_ROUTER_ADDRESS: str = "0xf5b509bB0909a69B1c207E495f687a596C168E12"

# Le Quoter Algebra ne renvoie pas d'estimation de gas : valeur forfaitaire
DEFAULT_SWAP_GAS: int = 250_000
# Validité par défaut de la transaction (secondes)
DEFAULT_DEADLINE_SECONDS: int = 1200

QUOTER_ABI: List[Dict[str, Any]] = [
    {
        "name": "quoteExactInputSingle",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "limitSqrtPrice", "type": "uint160"},
        ],
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "fee", "type": "uint16"},
        ],
    }
]

SWAP_ROUTER_ABI: List[Dict[str, Any]] = [
    {
        "name": "exactInputSingle",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "limitSqrtPrice", "type": "uint160"},
                ],
            }
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    }
]


class QuickswapAdapter(BaseDEXAdapter):
    """
    Adaptateur QuickSwap V3 (Algebra).

    Args:
        web3: instance Web3 connectée à Polygon.
        quoter_contract / router_contract: contrats injectables (tests).
        token_decimals: cache optionnel {adresse: decimals}.
        deadline_seconds: validité de la transaction construite.
        clock: source de temps (secondes epoch), injectable pour les tests.
    """

    def __init__(
        self,
        web3: Web3,
        quoter_contract: Optional[Any] = None,
        router_contract: Optional[Any] = None,
        token_decimals: Optional[Mapping[str, int]] = None,
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if deadline_seconds <= 0:
            raise ValueError("deadline_seconds doit être strictement positif")
        self._web3 = web3
        self._quoter = quoter_contract or web3.eth.contract(
            address=Web3.to_checksum_address(QUOTER_ADDRESS), abi=QUOTER_ABI
        )
        self._router = router_contract or web3.eth.contract(
            address=Web3.to_checksum_address(SWAP_ROUTER_ADDRESS), abi=SWAP_ROUTER_ABI
        )
        self._decimals: Dict[str, int] = {
            Web3.to_checksum_address(k): int(v)
            for k, v in (token_decimals or {}).items()
        }
        self._deadline_seconds = deadline_seconds
        self._clock = clock

    @property
    def name(self) -> str:
        return "quickswap"

    # ------------------------------------------------------------------ utils
    def _get_decimals(self, token: str) -> int:
        if token not in self._decimals:
            erc20 = self._web3.eth.contract(address=token, abi=ERC20_DECIMALS_ABI)
            self._decimals[token] = int(erc20.functions.decimals().call())
        return self._decimals[token]

    def _quote_single(
        self, token_in: str, token_out: str, amount_in_raw: int
    ) -> Tuple[int, int]:
        """Appelle le Quoter Algebra. Retourne (amountOut, fee)."""
        result = self._quoter.functions.quoteExactInputSingle(
            token_in, token_out, amount_in_raw, 0
        ).call()
        return int(result[0]), int(result[1])

    # -------------------------------------------------------------- get_quote
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_tolerance: Decimal,
    ) -> DEXQuote:
        t_in, t_out = validate_quote_inputs(
            token_in, token_out, amount_in, slippage_tolerance
        )

        return await asyncio.to_thread(
            self._get_quote_sync, t_in, t_out, amount_in, slippage_tolerance
        )

    def _get_quote_sync(
        self, t_in: str, t_out: str, amount_in: Decimal, slippage: Decimal
    ) -> DEXQuote:
        try:
            dec_in = self._get_decimals(t_in)
            dec_out = self._get_decimals(t_out)
        except Exception as exc:
            raise DEXQuoteError(f"Lecture des decimals impossible : {exc}") from exc

        amount_in_raw = to_raw_units(amount_in, dec_in)
        if amount_in_raw <= 0:
            raise DEXQuoteError("amount_in trop faible (0 après conversion on-chain)")

        try:
            out_raw, fee = self._quote_single(t_in, t_out, amount_in_raw)
        except Exception as exc:  # revert = pool inexistant / liquidité insuffisante
            raise DEXQuoteError(
                f"Quoter QuickSwap en échec pour {t_in} -> {t_out} : {exc}"
            ) from exc
        if out_raw <= 0:
            raise DEXQuoteError(
                f"Montant de sortie nul pour {t_in} -> {t_out} (liquidité insuffisante)"
            )

        min_out_raw = apply_slippage_raw(out_raw, slippage)

        impact, impact_estimated = self._price_impact(
            t_in, t_out, amount_in_raw, out_raw
        )

        return DEXQuote(
            dex_name=self.name,
            token_in=t_in,
            token_out=t_out,
            amount_in=amount_in,
            expected_amount_out=from_raw_units(out_raw, dec_out),
            min_amount_out=from_raw_units(min_out_raw, dec_out),
            price_impact_pct=impact,
            estimated_gas=DEFAULT_SWAP_GAS,
            raw_quote_data={
                "fee": fee,
                "amount_in_raw": amount_in_raw,
                "expected_amount_out_raw": out_raw,
                "min_amount_out_raw": min_out_raw,
                "limit_sqrt_price": 0,
                "price_impact_estimated": impact_estimated,
            },
        )

    def _price_impact(
        self, t_in: str, t_out: str, amount_in_raw: int, out_raw: int
    ) -> Tuple[Decimal, bool]:
        """
        Impact de prix (%) vs. un prix de référence obtenu avec 1/1000 d'amount_in.
        Retourne (impact, estimé). Si la référence est indisponible : (0, False).
        """
        ref_in = amount_in_raw // REFERENCE_DIVISOR
        if ref_in <= 0:
            return Decimal(0), False
        try:
            ref_out, _ = self._quote_single(t_in, t_out, ref_in)
        except Exception:
            return Decimal(0), False
        if ref_out <= 0:
            return Decimal(0), False
        impact = compute_price_impact_pct(amount_in_raw, out_raw, ref_in, ref_out)
        return impact, True

    # ------------------------------------------------- build_swap_transaction
    async def build_swap_transaction(self, quote: DEXQuote, recipient: str) -> dict:
        if not isinstance(quote, DEXQuote) or quote.dex_name != self.name:
            raise DEXTransactionError("La cotation n'appartient pas à quickswap")
        if not isinstance(recipient, str) or not Web3.is_address(recipient):
            raise DEXTransactionError(f"recipient invalide : {recipient!r}")

        data = quote.raw_quote_data
        deadline = int(self._clock()) + self._deadline_seconds
        try:
            params = (
                Web3.to_checksum_address(quote.token_in),
                Web3.to_checksum_address(quote.token_out),
                Web3.to_checksum_address(recipient),
                deadline,
                int(data["amount_in_raw"]),
                int(data["min_amount_out_raw"]),
                int(data["limit_sqrt_price"]),
            )
        except KeyError as exc:
            raise DEXTransactionError(f"raw_quote_data incomplet : {exc}") from exc

        try:
            calldata = self._router.encode_abi("exactInputSingle", args=[params])
        except Exception as exc:
            raise DEXTransactionError(
                f"Encodage exactInputSingle impossible : {exc}"
            ) from exc

        return {
            "to": Web3.to_checksum_address(SWAP_ROUTER_ADDRESS),
            "data": calldata,
            "value": 0,
            "chainId": CHAIN_ID_POLYGON,
            "gas": quote.estimated_gas,
        }
