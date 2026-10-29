# core/dex/uniswap_v3.py – V6.5.0
"""
Adaptateur Uniswap V3 (Polygon Mainnet) : cotation via QuoterV2 et
encodage des swaps via SwapRouter02 (exactInputSingle).

Les tokens sont identifiés par leur adresse ERC-20. Tous les montants exposés
sont des Decimal (unités humaines) ; les montants on-chain (entiers) sont
conservés dans `raw_quote_data`.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple

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

QUOTER_V2_ADDRESS: str = "0x61fFE014bA17989E743c5F6cB21bF9697547B21e"
SWAP_ROUTER_02_ADDRESS: str = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
SUPPORTED_FEE_TIERS: Tuple[int, ...] = (100, 500, 3000, 10000)

# Surcoût de gas du routeur (transferts, wrap, appel) ajouté au gas du pool
ROUTER_GAS_OVERHEAD: int = 50_000

QUOTER_V2_ABI: List[Dict[str, Any]] = [
    {
        "name": "quoteExactInputSingle",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
    }
]

SWAP_ROUTER_02_ABI: List[Dict[str, Any]] = [
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
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    }
]

class UniswapV3Adapter(BaseDEXAdapter):
    """
    Adaptateur Uniswap V3.

    Args:
        web3: instance Web3 connectée à Polygon.
        quoter_contract / router_contract: contrats injectables (tests).
        token_decimals: cache optionnel {adresse: decimals}, évite les appels RPC.
    """

    def __init__(
        self,
        web3: Web3,
        quoter_contract: Optional[Any] = None,
        router_contract: Optional[Any] = None,
        token_decimals: Optional[Mapping[str, int]] = None,
    ) -> None:
        self._web3 = web3
        self._quoter = quoter_contract or web3.eth.contract(
            address=Web3.to_checksum_address(QUOTER_V2_ADDRESS), abi=QUOTER_V2_ABI
        )
        self._router = router_contract or web3.eth.contract(
            address=Web3.to_checksum_address(SWAP_ROUTER_02_ADDRESS),
            abi=SWAP_ROUTER_02_ABI,
        )
        self._decimals: Dict[str, int] = {
            Web3.to_checksum_address(k): int(v)
            for k, v in (token_decimals or {}).items()
        }

    @property
    def name(self) -> str:
        return "uniswap_v3"

    # ------------------------------------------------------------------ utils
    def _get_decimals(self, token: str) -> int:
        if token not in self._decimals:
            erc20 = self._web3.eth.contract(address=token, abi=ERC20_DECIMALS_ABI)
            self._decimals[token] = int(erc20.functions.decimals().call())
        return self._decimals[token]

    def _quote_single(
        self, token_in: str, token_out: str, amount_in_raw: int, fee: int
    ) -> Tuple[int, int]:
        """Appelle le QuoterV2 pour un palier. Retourne (amountOut, gasEstimate)."""
        result = self._quoter.functions.quoteExactInputSingle(
            (token_in, token_out, amount_in_raw, fee, 0)
        ).call()
        return int(result[0]), int(result[3])

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

        # Meilleur palier = amountOut maximal parmi ceux qui répondent
        best: Optional[Tuple[int, int, int]] = None  # (out, gas, fee)
        errors: List[str] = []
        for fee in SUPPORTED_FEE_TIERS:
            try:
                out_raw, gas = self._quote_single(t_in, t_out, amount_in_raw, fee)
            except Exception as exc:  # revert = pool inexistant / liquidité insuffisante
                errors.append(f"fee={fee}: {exc}")
                continue
            if out_raw <= 0:
                errors.append(f"fee={fee}: sortie nulle")
                continue
            if best is None or out_raw > best[0]:
                best = (out_raw, gas, fee)

        if best is None:
            raise DEXQuoteError(
                "Aucun pool Uniswap V3 avec liquidité suffisante pour "
                f"{t_in} -> {t_out} ({'; '.join(errors)})"
            )
        out_raw, gas, fee = best

        min_out_raw = apply_slippage_raw(out_raw, slippage)

        impact, impact_estimated = self._price_impact(
            t_in, t_out, fee, amount_in_raw, out_raw
        )

        return DEXQuote(
            dex_name=self.name,
            token_in=t_in,
            token_out=t_out,
            amount_in=amount_in,
            expected_amount_out=from_raw_units(out_raw, dec_out),
            min_amount_out=from_raw_units(min_out_raw, dec_out),
            price_impact_pct=impact,
            estimated_gas=gas + ROUTER_GAS_OVERHEAD,
            raw_quote_data={
                "fee": fee,
                "amount_in_raw": amount_in_raw,
                "expected_amount_out_raw": out_raw,
                "min_amount_out_raw": min_out_raw,
                "sqrt_price_limit_x96": 0,
                "price_impact_estimated": impact_estimated,
            },
        )

    def _price_impact(
        self, t_in: str, t_out: str, fee: int, amount_in_raw: int, out_raw: int
    ) -> Tuple[Decimal, bool]:
        """
        Impact de prix (%) vs. un prix de référence obtenu avec une fraction
        d'amount_in sur le même palier (les frais s'annulent dans le ratio).
        Retourne (impact, estimé). Si la référence est indisponible : (0, False).
        """
        ref_in = amount_in_raw // REFERENCE_DIVISOR
        if ref_in <= 0:
            return Decimal(0), False
        try:
            ref_out, _ = self._quote_single(t_in, t_out, ref_in, fee)
        except Exception:
            return Decimal(0), False
        if ref_out <= 0:
            return Decimal(0), False
        impact = compute_price_impact_pct(amount_in_raw, out_raw, ref_in, ref_out)
        return impact, True

    # ------------------------------------------------- build_swap_transaction
    async def build_swap_transaction(self, quote: DEXQuote, recipient: str) -> dict:
        if not isinstance(quote, DEXQuote) or quote.dex_name != self.name:
            raise DEXTransactionError("La cotation n'appartient pas à uniswap_v3")
        if not isinstance(recipient, str) or not Web3.is_address(recipient):
            raise DEXTransactionError(f"recipient invalide : {recipient!r}")

        data = quote.raw_quote_data
        try:
            params = (
                Web3.to_checksum_address(quote.token_in),
                Web3.to_checksum_address(quote.token_out),
                int(data["fee"]),
                Web3.to_checksum_address(recipient),
                int(data["amount_in_raw"]),
                int(data["min_amount_out_raw"]),
                int(data["sqrt_price_limit_x96"]),
            )
        except KeyError as exc:
            raise DEXTransactionError(f"raw_quote_data incomplet : {exc}") from exc

        if params[2] not in SUPPORTED_FEE_TIERS:
            raise DEXTransactionError(f"Palier de frais non supporté : {params[2]}")

        try:
            calldata = self._router.encode_abi("exactInputSingle", args=[params])
        except Exception as exc:
            raise DEXTransactionError(f"Encodage exactInputSingle impossible : {exc}") from exc

        return {
            "to": Web3.to_checksum_address(SWAP_ROUTER_02_ADDRESS),
            "data": calldata,
            "value": 0,
            "chainId": CHAIN_ID_POLYGON,
            "gas": quote.estimated_gas,
        }
