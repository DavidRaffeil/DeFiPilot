"""
Module d'estimation dynamique du Gas EIP-1559 (GasEstimator) pour DeFiPilot.
Calcul des frais maxFeePerGas et maxPriorityFeePerGas avec garde-fou de sécurité.
"""

import logging
from typing import Any, Dict
from web3 import Web3


class GasPriceTooHighError(Exception):
    """Exception levée lorsque le coût de gas estimé dépasse le garde-fou de sécurité."""

    pass


class GasEstimator:
    """
    Gestionnaire d'estimation dynamique des frais de gas EIP-1559 pour Polygon / Ethereum.
    """

    def __init__(
        self,
        rpc_manager_or_web3: Any,
        min_priority_fee_gwei: float = 30.0,
        max_gas_price_gwei: float = 300.0,
    ):
        """
        Initialise le GasEstimator.

        :param rpc_manager_or_web3: Instance de RPCManager ou de Web3.
        :param min_priority_fee_gwei: Pourboire minimum garanti en Gwei (défaut: 30 Gwei sur Polygon).
        :param max_gas_price_gwei: Coût maximal toléré en Gwei avant déclenchement de la sécurité.
        """
        self.provider = rpc_manager_or_web3
        self.min_priority_fee_gwei = float(min_priority_fee_gwei)
        self.max_gas_price_gwei = float(max_gas_price_gwei)
        self.logger = logging.getLogger("DeFiPilot.GasEstimator")

    @staticmethod
    def gwei_to_wei(gwei_val: float) -> int:
        """Convertit une valeur en Gwei vers des Wei."""
        return int(Web3.to_wei(gwei_val, "gwei"))

    @staticmethod
    def wei_to_gwei(wei_val: int) -> float:
        """Convertit une valeur en Wei vers des Gwei."""
        return float(Web3.from_wei(wei_val, "gwei"))

    def _call_web3_method(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Appelle une méthode Web3 directement ou via RPCManager (execute_call/get_web3)."""
        # Si le provider a l'attribut eth (Web3 direct ou mock Web3), privilégier l'accès direct
        if hasattr(self.provider, "eth"):
            parts = method_name.split(".")
            target = self.provider
            for part in parts:
                target = getattr(target, part)
            return target(*args, **kwargs) if callable(target) else target
        # Sinon, s'il s'agit d'un RPCManager ou wrapper proposant execute_call
        elif hasattr(self.provider, "execute_call"):
            return self.provider.execute_call(method_name, *args, **kwargs)
        elif hasattr(self.provider, "get_web3"):
            w3 = self.provider.get_web3()
            parts = method_name.split(".")
            target = w3
            for part in parts:
                target = getattr(target, part)
            return target(*args, **kwargs) if callable(target) else target
        else:
            parts = method_name.split(".")
            target = self.provider
            for part in parts:
                target = getattr(target, part)
            return target(*args, **kwargs) if callable(target) else target

    def estimate_eip1559_fees(self) -> Dict[str, Any]:
        """
        Estime les frais EIP-1559 dynamiques.

        - Récupère le dernier bloc pour extraire baseFeePerGas.
        - Obtient maxPriorityFeePerGas (avec minimum de sécurité min_priority_fee_gwei).
        - Calcule maxFeePerGas = (2 * baseFeePerGas) + maxPriorityFeePerGas.
        - Applique le garde-fou max_gas_price_gwei et lève GasPriceTooHighError si dépassé.

        :return: Dict contenant les valeurs en Wei (maxFeePerGas, maxPriorityFeePerGas, baseFeePerGas)
                 ainsi qu'en Gwei.
        """
        block = self._call_web3_method("eth.get_block", "latest")

        base_fee_per_gas = (
            block.get("baseFeePerGas")
            if isinstance(block, dict)
            else getattr(block, "baseFeePerGas", None)
        )

        if base_fee_per_gas is None:
            raise ValueError(
                "Impossible d'extraire 'baseFeePerGas' du dernier bloc. Le réseau supporte-t-il EIP-1559 ?"
            )

        base_fee_per_gas = int(base_fee_per_gas)

        suggested_priority_fee_wei = 0
        try:
            suggested = self._call_web3_method("eth.max_priority_fee")
            if suggested is not None:
                suggested_priority_fee_wei = int(suggested)
        except Exception as exc:
            self.logger.debug(
                f"eth.max_priority_fee non disponible, utilisation du minimum par défaut: {exc}"
            )

        min_priority_fee_wei = self.gwei_to_wei(self.min_priority_fee_gwei)
        max_priority_fee_per_gas = max(suggested_priority_fee_wei, min_priority_fee_wei)

        # Formule EIP-1559 : maxFeePerGas = (2 * baseFeePerGas) + maxPriorityFeePerGas
        max_fee_per_gas = (2 * base_fee_per_gas) + max_priority_fee_per_gas

        max_fee_gwei = self.wei_to_gwei(max_fee_per_gas)

        if max_fee_gwei > self.max_gas_price_gwei:
            error_msg = (
                f"Garde-fou activé : les frais de gas estimés ({max_fee_gwei:.2f} Gwei) "
                f"dépassent le plafond de sécurité toléré ({self.max_gas_price_gwei} Gwei)."
            )
            self.logger.error(error_msg)
            raise GasPriceTooHighError(error_msg)

        result = {
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "baseFeePerGas": base_fee_per_gas,
            "maxFeePerGas_gwei": round(max_fee_gwei, 4),
            "maxPriorityFeePerGas_gwei": round(self.wei_to_gwei(max_priority_fee_per_gas), 4),
            "baseFeePerGas_gwei": round(self.wei_to_gwei(base_fee_per_gas), 4),
        }

        self.logger.info(
            f"Frais EIP-1559 estimés : BaseFee={result['baseFeePerGas_gwei']} Gwei, "
            f"PriorityFee={result['maxPriorityFeePerGas_gwei']} Gwei, "
            f"MaxFee={result['maxFeePerGas_gwei']} Gwei."
        )

        return result
