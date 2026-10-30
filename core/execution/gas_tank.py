"""
Module de gestion automatisée du réservoir de carburant (Gas Tank) et du wrapping
natif (WPOL ⇄ POL) sur Polygon Mainnet pour DeFiPilot (Phase 4 - v6.6.0).
"""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from web3 import Web3

import core.config as app_config
from core.dry_run_guard import assert_dry_run_safe
from core.real_wallet import get_private_key

POLYGON_CHAIN_ID = 137
DEFAULT_WPOL_ADDRESS = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
DEFAULT_GAS_LIMIT = 60_000
DEFAULT_GAS_PRICE_WEI = 30_000_000_000  # 30 Gwei


class GasCriticalError(RuntimeError):
    """Exception levée lorsque le solde de gas natif (POL) est critique et bloque toute exécution."""

    def __init__(self, message: str = "Solde POL natif sous le seuil critique bloquant.") -> None:
        super().__init__(message)
        self.message = message


WPOL_MINIMAL_ABI: List[Dict[str, Any]] = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


class GasTankManager:
    """
    Gestionnaire automatisé du réservoir de gas natif (POL) et du token enveloppé (WPOL)
    sur Polygon Mainnet.

    Assure la surveillance des seuils (réserve minimale, cible de recharge, seuil critique)
    et déclenche les opérations de wrapping (`deposit`) et d'unwrapping (`withdraw`)
    dans le strict respect du mode `dry_run`.
    """

    WPOL_ABI = WPOL_MINIMAL_ABI

    def __init__(
        self,
        web3_client: Any,
        wallet_address: str,
        wpol_address: str = DEFAULT_WPOL_ADDRESS,
        min_pol_reserve: Optional[float] = None,
        target_pol_reserve: Optional[float] = None,
        critical_gas_threshold: Optional[float] = None,
        max_pol_reserve: Optional[float] = None,
        auto_wrap_enabled: Optional[bool] = None,
        dry_run: bool = True,
        private_key: Optional[str] = None,
    ) -> None:
        """
        Initialise le GasTankManager.

        :param web3_client: Instance Web3 ou wrapper RPCManager existant du projet.
        :param wallet_address: Adresse publique du portefeuille.
        :param wpol_address: Adresse du contrat WPOL sur Polygon Mainnet.
        :param min_pol_reserve: Seuil bas en POL natif déclenchant la recharge (défaut: config / 5.0 POL).
        :param target_pol_reserve: Cible de recharge en POL natif (défaut: config / 10.0 POL).
        :param critical_gas_threshold: Seuil critique bloquant (défaut: config / 1.0 POL).
        :param max_pol_reserve: Seuil haut en POL natif au-delà duquel l'excédent est enveloppé en WPOL (défaut: config / 25.0 POL).
        :param auto_wrap_enabled: Active ou désactive l'auto-wrap de l'excédent (défaut: config / True).
        :param dry_run: Booléen activant le mode simulation (aucune transaction on-chain).
        :param private_key: Clé privée optionnelle pour la signature en mode réel.
        """
        if web3_client is None:
            raise ValueError("web3_client ne peut pas être None.")
        if not wallet_address or not str(wallet_address).strip():
            raise ValueError("wallet_address ne peut pas être vide.")

        min_res = float(
            app_config.GAS_MIN_POL_RESERVE
            if min_pol_reserve is None
            else min_pol_reserve
        )
        target_res = float(
            app_config.GAS_TARGET_POL_RESERVE
            if target_pol_reserve is None
            else target_pol_reserve
        )
        crit_thresh = float(
            app_config.GAS_CRITICAL_THRESHOLD
            if critical_gas_threshold is None
            else critical_gas_threshold
        )
        max_res = float(
            app_config.GAS_MAX_POL_RESERVE
            if max_pol_reserve is None
            else max_pol_reserve
        )
        auto_wrap = (
            bool(app_config.GAS_AUTO_WRAP_ENABLED)
            if auto_wrap_enabled is None
            else bool(auto_wrap_enabled)
        )

        if min_res < 0 or target_res < 0 or crit_thresh < 0 or max_res < 0:
            raise ValueError("Les seuils de gas ne peuvent pas être négatifs.")
        if target_res < min_res:
            raise ValueError(
                "target_pol_reserve doit être supérieur ou égal à min_pol_reserve."
            )
        if max_res < target_res:
            raise ValueError(
                "max_pol_reserve doit être supérieur ou égal à target_pol_reserve."
            )

        self.web3_client = web3_client
        self.wallet_address = self._to_checksum(wallet_address)
        self.wpol_address = self._to_checksum(wpol_address or DEFAULT_WPOL_ADDRESS)
        self.min_pol_reserve = min_res
        self.target_pol_reserve = target_res
        self.critical_gas_threshold = crit_thresh
        self.max_pol_reserve = max_res
        self.auto_wrap_enabled = auto_wrap
        self.dry_run = bool(dry_run)
        self._private_key = private_key
        self.logger = logging.getLogger("DeFiPilot.GasTankManager")

        self.logger.info(
            "GasTankManager initialisé (wallet=%s, wpol=%s, min=%.2f POL, target=%.2f POL, "
            "max=%.2f POL, critical=%.2f POL, auto_wrap=%s, dry_run=%s).",
            self.wallet_address,
            self.wpol_address,
            self.min_pol_reserve,
            self.target_pol_reserve,
            self.max_pol_reserve,
            self.critical_gas_threshold,
            self.auto_wrap_enabled,
            self.dry_run,
        )

    @staticmethod
    def _to_checksum(address: str) -> str:
        """Convertit une adresse en format EIP-55 checksum si valide, sinon nettoie la chaîne."""
        addr_str = str(address).strip()
        try:
            return Web3.to_checksum_address(addr_str)
        except Exception:
            return addr_str

    @staticmethod
    def to_wei(amount: float | int | Decimal) -> int:
        """
        Convertit un montant en unités lisibles (POL/WPOL, 18 décimales) vers des Wei (int).
        Lève ValueError si le montant est négatif.
        """
        if amount is None:
            raise ValueError("Le montant ne peut pas être None.")
        dec_amount = Decimal(str(amount))
        if dec_amount < 0:
            raise ValueError("Le montant ne peut pas être négatif.")
        if dec_amount == 0:
            return 0
        return int(Web3.to_wei(dec_amount, "ether"))

    @staticmethod
    def from_wei(amount_wei: int) -> float:
        """
        Convertit un montant en Wei (int) vers des unités lisibles (float, 18 décimales).
        """
        if amount_wei is None:
            return 0.0
        raw = int(amount_wei)
        if raw < 0:
            raise ValueError("Le montant en Wei ne peut pas être négatif.")
        if raw == 0:
            return 0.0
        return float(Web3.from_wei(raw, "ether"))

    def _get_w3(self) -> Any:
        """Résout l'instance Web3 sous-jacente depuis `web3_client` (Web3 direct ou RPCManager)."""
        if hasattr(self.web3_client, "eth"):
            return self.web3_client
        if hasattr(self.web3_client, "get_web3"):
            return self.web3_client.get_web3()
        return self.web3_client

    def _get_wpol_contract(self, w3: Optional[Any] = None) -> Any:
        """Instancie le contrat WPOL avec l'ABI minimale."""
        active_w3 = w3 or self._get_w3()
        return active_w3.eth.contract(address=self.wpol_address, abi=self.WPOL_ABI)

    @staticmethod
    def _format_tx_hash(tx_hash_raw: Any) -> str:
        """Normalise un hash de transaction en chaîne hexadécimale préfixée par '0x'."""
        if isinstance(tx_hash_raw, (bytes, bytearray)):
            hex_str = tx_hash_raw.hex()
            return hex_str if hex_str.startswith("0x") else f"0x{hex_str}"
        if hasattr(tx_hash_raw, "hex") and callable(tx_hash_raw.hex):
            hex_str = tx_hash_raw.hex()
            return hex_str if hex_str.startswith("0x") else f"0x{hex_str}"
        val = str(tx_hash_raw)
        return val if val.startswith("0x") else f"0x{val}"

    def get_balances(self) -> Dict[str, float]:
        """
        Interroge les soldes on-chain du portefeuille en POL natif et en WPOL.

        :return: Dictionnaire `{"native_pol": float, "wpol": float}` converti en unités lisibles (18 décimales).
        """
        if hasattr(self.web3_client, "eth"):
            w3 = self.web3_client
            native_wei = w3.eth.get_balance(self.wallet_address)
            contract = self._get_wpol_contract(w3)
            wpol_wei = contract.functions.balanceOf(self.wallet_address).call()
        elif hasattr(self.web3_client, "execute_call"):
            native_wei = self.web3_client.execute_call(
                "eth.get_balance", self.wallet_address
            )
            wpol_wei = self.web3_client.execute_call(
                lambda w3_inst: w3_inst.eth.contract(
                    address=self.wpol_address, abi=self.WPOL_ABI
                )
                .functions.balanceOf(self.wallet_address)
                .call()
            )
        else:
            w3 = self._get_w3()
            native_wei = w3.eth.get_balance(self.wallet_address)
            contract = self._get_wpol_contract(w3)
            wpol_wei = contract.functions.balanceOf(self.wallet_address).call()

        native_pol = self.from_wei(native_wei)
        wpol = self.from_wei(wpol_wei)

        self.logger.debug(
            "Soldes GasTank (%s) : native_pol=%.6f POL, wpol=%.6f WPOL.",
            self.wallet_address,
            native_pol,
            wpol,
        )
        return {"native_pol": native_pol, "wpol": wpol}

    def is_gas_critical(self) -> bool:
        """
        Vérifie si le solde en POL natif est inférieur ou égal au seuil critique bloquant.

        :return: True si `native_pol <= critical_gas_threshold`, False sinon.
        """
        balances = self.get_balances()
        native_pol = balances["native_pol"]
        is_crit = native_pol <= self.critical_gas_threshold
        if is_crit:
            self.logger.critical(
                "[GAS CRITICAL] Solde POL natif critique : %.6f POL <= seuil critique %.6f POL !",
                native_pol,
                self.critical_gas_threshold,
            )
        return is_crit

    def _build_tx_params(self, w3: Any, value_wei: int = 0) -> Dict[str, Any]:
        """Construit les paramètres standards de transaction (nonce, chainId, gas, frais)."""
        try:
            nonce = int(w3.eth.get_transaction_count(self.wallet_address, "pending"))
        except TypeError:
            nonce = int(w3.eth.get_transaction_count(self.wallet_address))
        except Exception:
            nonce = 0

        try:
            chain_id_raw = getattr(w3.eth, "chain_id", POLYGON_CHAIN_ID)
            chain_id = int(chain_id_raw) if isinstance(chain_id_raw, int) else POLYGON_CHAIN_ID
        except Exception:
            chain_id = POLYGON_CHAIN_ID

        tx_params: Dict[str, Any] = {
            "from": self.wallet_address,
            "value": int(value_wei),
            "nonce": nonce,
            "chainId": chain_id,
            "gas": DEFAULT_GAS_LIMIT,
        }

        try:
            gas_price = getattr(w3.eth, "gas_price", None)
            if isinstance(gas_price, int) and gas_price > 0:
                tx_params["gasPrice"] = gas_price
            else:
                tx_params["gasPrice"] = DEFAULT_GAS_PRICE_WEI
        except Exception:
            tx_params["gasPrice"] = DEFAULT_GAS_PRICE_WEI

        return tx_params

    def _execute_contract_tx(
        self,
        action_name: str,
        contract_fn: Any,
        value_wei: int = 0,
    ) -> str:
        """Construit, signe et diffuse une transaction de contrat WPOL en mode réel."""
        assert_dry_run_safe(action_type=action_name, config={"dry_run": self.dry_run})

        w3 = self._get_w3()
        tx_params = self._build_tx_params(w3, value_wei=value_wei)

        tx = contract_fn.build_transaction(tx_params)
        try:
            estimated = w3.eth.estimate_gas(tx)
            if isinstance(estimated, int) and estimated > 0:
                tx["gas"] = int(estimated * 1.2)
        except Exception:
            pass

        private_key = self._private_key or get_private_key()
        if not private_key:
            raise ValueError(
                f"Clé privée introuvable pour signer la transaction '{action_name}'."
            )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_tx = getattr(
            signed_tx,
            "raw_transaction",
            getattr(signed_tx, "rawTransaction", None),
        )
        tx_hash_raw = w3.eth.send_raw_transaction(raw_tx)
        tx_hash = self._format_tx_hash(tx_hash_raw)

        self.logger.info(
            "[GAS TANK] Transaction %s envoyée avec succès : tx_hash=%s",
            action_name,
            tx_hash,
        )
        return tx_hash

    def wrap(self, amount: float) -> Optional[str]:
        """
        Convertit du POL natif en WPOL en appelant `deposit()` avec `value = amount_wei`.

        :param amount: Montant de POL à envelopper (en unités lisibles).
        :return: Hash de transaction (str) en mode réel, ou None en mode `dry_run` (ou si montant == 0).
        :raises ValueError: Si le montant est négatif ou invalide.
        """
        amount_wei = self.to_wei(amount)
        if amount_wei == 0:
            self.logger.warning(
                "[GAS TANK] Ignoré : appel wrap(0) avec un montant nul."
            )
            return None

        if self.dry_run:
            self.logger.info(
                "[SIMULATION / DRY-RUN] Wrap simulé : %.6f POL (%d wei) -> WPOL via deposit().",
                float(amount),
                amount_wei,
            )
            return None

        w3 = self._get_w3()
        contract = self._get_wpol_contract(w3)
        deposit_fn = contract.functions.deposit()
        return self._execute_contract_tx(
            action_name="wrap_pol",
            contract_fn=deposit_fn,
            value_wei=amount_wei,
        )

    def unwrap(self, amount: float) -> Optional[str]:
        """
        Convertit du WPOL en POL natif en appelant `withdraw(amount_wei)`.

        :param amount: Montant de WPOL à désenvelopper (en unités lisibles).
        :return: Hash de transaction (str) en mode réel, ou None en mode `dry_run` (ou si montant == 0).
        :raises ValueError: Si le montant est négatif ou invalide.
        """
        amount_wei = self.to_wei(amount)
        if amount_wei == 0:
            self.logger.warning(
                "[GAS TANK] Ignoré : appel unwrap(0) avec un montant nul."
            )
            return None

        if self.dry_run:
            self.logger.info(
                "[SIMULATION / DRY-RUN] Unwrap simulé : %.6f WPOL (%d wei) -> POL via withdraw(%d).",
                float(amount),
                amount_wei,
                amount_wei,
            )
            return None

        w3 = self._get_w3()
        contract = self._get_wpol_contract(w3)
        withdraw_fn = contract.functions.withdraw(amount_wei)
        return self._execute_contract_tx(
            action_name="unwrap_wpol",
            contract_fn=withdraw_fn,
            value_wei=0,
        )

    def check_and_refuel(self) -> Dict[str, Any]:
        """
        Vérifie le niveau du réservoir de POL natif et déclenche un rechargement
        automatique depuis la réserve WPOL si `native_pol < min_pol_reserve`.

        :return: Dictionnaire détaillant le statut, l'action entreprise, les montants et le tx_hash.
        """
        balances = self.get_balances()
        native_pol = balances["native_pol"]
        wpol_balance = balances["wpol"]

        if native_pol >= self.min_pol_reserve:
            self.logger.info(
                "[GAS TANK] Niveau de POL nominal (%.4f POL >= min %.4f POL). Aucune action requise.",
                native_pol,
                self.min_pol_reserve,
            )
            return {
                "status": "NOMINAL",
                "action": "none",
                "native_pol": native_pol,
                "wpol": wpol_balance,
                "deficit": 0.0,
                "amount_unwrapped": 0.0,
                "tx_hash": None,
                "dry_run": self.dry_run,
                "is_critical": native_pol <= self.critical_gas_threshold,
            }

        # Calcul précis en Decimal pour éviter les artefacts de virgule flottante (ex: 10.0 - 3.2 = 6.8)
        deficit_dec = Decimal(str(self.target_pol_reserve)) - Decimal(str(native_pol))
        deficit = float(deficit_dec)

        self.logger.warning(
            "[GAS TANK] Réserve POL basse (%.4f POL < min %.4f POL). Déficit à combler : %.4f POL (cible: %.4f POL).",
            native_pol,
            self.min_pol_reserve,
            deficit,
            self.target_pol_reserve,
        )

        if wpol_balance < deficit:
            is_crit = native_pol <= self.critical_gas_threshold
            self.logger.error(
                "[GAS TANK] Solde WPOL insuffisant (%.4f WPOL disponibles < %.4f WPOL requis) "
                "pour recharger le réservoir de POL (critique=%s).",
                wpol_balance,
                deficit,
                is_crit,
            )
            return {
                "status": "INSUFFICIENT_WPOL",
                "action": "none",
                "native_pol": native_pol,
                "wpol": wpol_balance,
                "deficit": deficit,
                "amount_unwrapped": 0.0,
                "tx_hash": None,
                "dry_run": self.dry_run,
                "is_critical": is_crit,
            }

        tx_hash = self.unwrap(deficit)
        status = "SIMULATED_REFUEL" if self.dry_run else "REFUELED"
        action = "simulated_unwrap" if self.dry_run else "unwrap"

        self.logger.info(
            "[GAS TANK] Recharge terminée : status=%s, action=%s, montant=%.4f POL, tx_hash=%s.",
            status,
            action,
            deficit,
            tx_hash,
        )

        return {
            "status": status,
            "action": action,
            "native_pol": native_pol,
            "wpol": wpol_balance,
            "deficit": deficit,
            "amount_unwrapped": deficit,
            "tx_hash": tx_hash,
            "dry_run": self.dry_run,
            "is_critical": False,
        }

    def check_and_sweep_excess_gas(self) -> Dict[str, Any]:
        """
        Vérifie si le solde de POL natif dépasse `max_pol_reserve` et convertit
        automatiquement l'excédent (`native_pol - target_pol_reserve`) en WPOL
        lorsque `auto_wrap_enabled` est True.

        :return: Dictionnaire de statut (`{"action": "WRAPPED_EXCESS" | "NONE", "amount": float, ...}`).
        """
        balances = self.get_balances()
        native_pol = balances["native_pol"]
        wpol_balance = balances["wpol"]

        if not self.auto_wrap_enabled:
            self.logger.debug(
                "[GAS TANK] Auto-wrap désactivé (native_pol=%.4f POL). Aucune action entreprise.",
                native_pol,
            )
            return {
                "status": "DISABLED",
                "action": "NONE",
                "amount": 0.0,
                "excess": 0.0,
                "native_pol": native_pol,
                "wpol": wpol_balance,
                "tx_hash": None,
                "dry_run": self.dry_run,
            }

        if native_pol <= self.max_pol_reserve:
            self.logger.debug(
                "[GAS TANK] Pas d'excédent de POL natif (%.4f POL <= max %.4f POL).",
                native_pol,
                self.max_pol_reserve,
            )
            return {
                "status": "NOMINAL",
                "action": "NONE",
                "amount": 0.0,
                "excess": 0.0,
                "native_pol": native_pol,
                "wpol": wpol_balance,
                "tx_hash": None,
                "dry_run": self.dry_run,
            }

        excess_dec = Decimal(str(native_pol)) - Decimal(str(self.target_pol_reserve))
        excess = float(excess_dec)

        self.logger.info(
            "[GAS TANK] Excédent de POL détecté (%.4f POL > max %.4f POL). "
            "Conversion de %.4f POL vers WPOL (cible: %.4f POL).",
            native_pol,
            self.max_pol_reserve,
            excess,
            self.target_pol_reserve,
        )

        tx_hash = self.wrap(excess)
        status = "SIMULATED_WRAP" if self.dry_run else "WRAPPED"

        return {
            "status": status,
            "action": "WRAPPED_EXCESS",
            "amount": excess,
            "excess": excess,
            "native_pol": native_pol,
            "wpol": wpol_balance,
            "tx_hash": tx_hash,
            "dry_run": self.dry_run,
        }

