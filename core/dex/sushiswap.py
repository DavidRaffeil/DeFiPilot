# core/dex/sushiswap.py – V6.5.0
"""
Adaptateur SushiSwap V2 (AMM classique, Polygon Mainnet) : cotation via
`getAmountsOut` du Router et encodage de `swapExactTokensForTokens`.

Seule la paire directe [token_in, token_out] est supportée. Montants métier en
Decimal, valeurs on-chain en entiers (conservées dans `raw_quote_data`).
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import Any, Callable, Dict, List, Mapping, Optional

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

ROUTER_ADDRESS: str = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"

# Gas forfaitaire d'un swap V2 direct
DEFAULT_SWAP_GAS: int = 150_000
# Validité par défaut de la transaction (secondes)
DEFAULT_DEADLINE_SECONDS: int = 1200

ROUTER_ABI: List[Dict[str, Any]] = [
    {
        "name": "getAmountsOut",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
    },
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
    },
]


class SushiswapAdapter(BaseDEXAdapter):
    """
    Adaptateur SushiSwap V2.

    Args:
        web3: instance Web3 connectée à Polygon.
        router_contract: contrat Router injectable (tests).
        token_decimals: cache optionnel {adresse: decimals}.
        deadline_seconds: validité de la transaction construite.
        clock: source de temps (secondes epoch), injectable pour les tests.
    """

    def __init__(
        self,
        web3: Web3,
        router_contract: Optional[Any] = None,
        token_decimals: Optional[Mapping[str, int]] = None,
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if deadline_seconds <= 0:
            raise ValueError("deadline_seconds doit être strictement positif")
        self._web3 = web3
        self._router = router_contract or web3.eth.contract(
            address=Web3.to_checksum_address(ROUTER_ADDRESS), abi=ROUTER_ABI
        )
        self._decimals: Dict[str, int] = {
            Web3.to_checksum_address(k): int(v)
            for k, v in (token_decimals or {}).items()
        }
        self._deadline_seconds = deadline_seconds
        self._clock = clock

    @property
    def name(self) -> str:
        return "sushiswap"

    # ------------------------------------------------------------------ utils
    def _get_decimals(self, token: str) -> int:
        if token not in self._decimals:
            erc20 = self._web3.eth.contract(address=token, abi=ERC20_DECIMALS_ABI)
            self._decimals[token] = int(erc20.functions.decimals().call())
        return self._decimals[token]

    def _amount_out(self, token_in: str, token_out: str, amount_in_raw: int) -> int:
        """Appelle getAmountsOut sur la paire directe. Retourne le montant de sortie."""
        amounts = self._router.functions.getAmountsOut(
            amount_in_raw, [token_in, token_out]
        ).call()
        if not isinstance(amounts, (list, tuple)) or len(amounts) != 2:
            raise ValueError(f"réponse getAmountsOut inattendue : {amounts!r}")
        return int(amounts[-1])

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
            out_raw = self._amount_out(t_in, t_out, amount_in_raw)
        except Exception as exc:  # revert = pool inexistant / réserves insuffisantes
            raise DEXQuoteError(
                f"getAmountsOut SushiSwap en échec pour {t_in} -> {t_out} : {exc}"
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
                "path": [t_in, t_out],
                "amount_in_raw": amount_in_raw,
                "expected_amount_out_raw": out_raw,
                "min_amount_out_raw": min_out_raw,
                "price_impact_estimated": impact_estimated,
            },
        )

    def _price_impact(
        self, t_in: str, t_out: str, amount_in_raw: int, out_raw: int
    ) -> tuple[Decimal, bool]:
        """
        Impact de prix (%) vs. un prix de référence obtenu avec 1/1000 d'amount_in
        (les frais de 0,3 % s'annulent dans le ratio).
        Retourne (impact, estimé). Si la référence est indisponible : (0, False).
        """
        ref_in = amount_in_raw // REFERENCE_DIVISOR
        if ref_in <= 0:
            return Decimal(0), False
        try:
            ref_out = self._amount_out(t_in, t_out, ref_in)
        except Exception:
            return Decimal(0), False
        if ref_out <= 0:
            return Decimal(0), False
        impact = compute_price_impact_pct(amount_in_raw, out_raw, ref_in, ref_out)
        return impact, True

    # ------------------------------------------------- build_swap_transaction
    async def build_swap_transaction(self, quote: DEXQuote, recipient: str) -> dict:
        if not isinstance(quote, DEXQuote) or quote.dex_name != self.name:
            raise DEXTransactionError("La cotation n'appartient pas à sushiswap")
        if not isinstance(recipient, str) or not Web3.is_address(recipient):
            raise DEXTransactionError(f"recipient invalide : {recipient!r}")

        data = quote.raw_quote_data
        deadline = int(self._clock()) + self._deadline_seconds
        try:
            args = [
                int(data["amount_in_raw"]),
                int(data["min_amount_out_raw"]),
                [Web3.to_checksum_address(a) for a in data["path"]],
                Web3.to_checksum_address(recipient),
                deadline,
            ]
        except KeyError as exc:
            raise DEXTransactionError(f"raw_quote_data incomplet : {exc}") from exc

        try:
            calldata = self._router.encode_abi("swapExactTokensForTokens", args=args)
        except Exception as exc:
            raise DEXTransactionError(
                f"Encodage swapExactTokensForTokens impossible : {exc}"
            ) from exc

        return {
            "to": Web3.to_checksum_address(ROUTER_ADDRESS),
            "data": calldata,
            "value": 0,
            "chainId": CHAIN_ID_POLYGON,
            "gas": quote.estimated_gas,
        }
