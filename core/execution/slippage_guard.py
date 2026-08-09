"""
Module de gestion du slippage et des deadlines d'exécution (SlippageGuard) pour DeFiPilot.
Calcule les montants minimums attendus (amount_out_min) et les timestamps d'expiration (deadline).
"""

import logging
import time
from typing import Optional, Union


class SlippageGuard:
    """
    Gestionnaire de sécurité pour le contrôle du slippage et des délais de validité des transactions DEX.
    """

    def __init__(
        self,
        max_allowed_slippage_pct: float = 3.0,
        default_ttl_seconds: int = 180,
    ):
        """
        Initialise le SlippageGuard.

        :param max_allowed_slippage_pct: Pourcentage maximal de slippage toléré (ex: 3.0%).
        :param default_ttl_seconds: Durée de vie par défaut des transactions en secondes (ex: 180s = 3 min).
        """
        self.max_allowed_slippage_pct = float(max_allowed_slippage_pct)
        self.default_ttl_seconds = int(default_ttl_seconds)
        self.logger = logging.getLogger("DeFiPilot.SlippageGuard")

    def calculate_min_amount_out(
        self,
        amount_out_expected: Union[float, int],
        max_slippage_pct: float,
    ) -> Union[float, int]:
        """
        Calcule le montant minimum acceptable (amount_out_min) en appliquant le pourcentage de slippage.

        :param amount_out_expected: Montant attendu en sortie.
        :param max_slippage_pct: Pourcentage de slippage toléré (ex: 0.5 pour 0.5%).
        :return: Montant minimum garanti.
        :raises ValueError: Si max_slippage_pct est négatif ou dépasse max_allowed_slippage_pct (ex: 3.0%).
        """
        if max_slippage_pct < 0.0:
            raise ValueError("Le pourcentage de slippage ne peut pas être négatif.")

        if max_slippage_pct > self.max_allowed_slippage_pct:
            raise ValueError(
                f"Slippage demandé ({max_slippage_pct}%) dépasse le plafond de sécurité maximal autorisé "
                f"({self.max_allowed_slippage_pct}%)."
            )

        factor = 1.0 - (max_slippage_pct / 100.0)

        if isinstance(amount_out_expected, int):
            min_amount = int(amount_out_expected * factor)
        else:
            min_amount = float(amount_out_expected * factor)

        self.logger.debug(
            f"Slippage calculé : attendu={amount_out_expected}, slippage={max_slippage_pct}%, "
            f"minimum={min_amount}"
        )

        return min_amount

    def calculate_deadline(self, ttl_seconds: Optional[int] = None) -> int:
        """
        Calcule le timestamp Unix d'expiration (deadline) pour une transaction.

        :param ttl_seconds: Temps de validité en secondes. Si None, utilise default_ttl_seconds (180s).
        :return: Timestamp Unix entier (secondes).
        """
        ttl = self.default_ttl_seconds if ttl_seconds is None else int(ttl_seconds)
        if ttl <= 0:
            raise ValueError("ttl_seconds doit être strictement positif.")

        deadline = int(time.time()) + ttl
        self.logger.debug(f"Deadline calculée : {deadline} (TTL: {ttl}s)")
        return deadline

    @staticmethod
    def to_raw_amount(amount: float, decimals: int = 18) -> int:
        """
        Convertit un montant lisible (ex: 100.5 USDC) en unités atomiques / Wei (int).

        :param amount: Montant en unités lisibles.
        :param decimals: Nombre de décimales du token (ex: 6 pour USDC/USDT, 18 pour POL/ETH).
        :return: Montant sous forme d'entier atomique.
        """
        return int(round(amount * (10**decimals)))

    @staticmethod
    def from_raw_amount(raw_amount: int, decimals: int = 18) -> float:
        """
        Convertit des unités atomiques / Wei (int) en un montant lisible (float).

        :param raw_amount: Montant sous forme d'entier atomique.
        :param decimals: Nombre de décimales du token.
        :return: Montant sous forme de float.
        """
        return float(raw_amount) / (10**decimals)

    def calculate_min_amount_out_raw(
        self,
        amount_out_expected: float,
        max_slippage_pct: float,
        decimals: int = 18,
    ) -> int:
        """
        Calcule le amount_out_min directement en unités atomiques entières (pour les contrats Web3).

        :param amount_out_expected: Montant attendu en unités lisibles (ex: 100.0 USDC).
        :param max_slippage_pct: Pourcentage de slippage toléré (ex: 0.5%).
        :param decimals: Décimales du token.
        :return: Montant minimum en unités atomiques entières (int).
        """
        raw_expected = self.to_raw_amount(amount_out_expected, decimals)
        min_raw = self.calculate_min_amount_out(raw_expected, max_slippage_pct)
        return int(min_raw)
