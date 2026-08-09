"""
Module de gestion des RPC redondants (RPCManager) pour DeFiPilot.
Fournit la classe RPCManager pour gérer le basculement automatique (failover)
et la mise en quarantaine des endpoints RPC Polygon défaillants.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
from web3 import Web3


class RPCManager:
    """
    Gestionnaire de RPCs Polygon redondants avec failover automatique et quarantaine.
    """

    def __init__(
        self,
        rpc_urls: List[str],
        timeout: float = 10.0,
        quarantine_time: float = 300.0,
    ):
        """
        Initialise le RPCManager.

        :param rpc_urls: Liste d'URLs RPC Polygon.
        :param timeout: Timeout paramétrable pour les requêtes HTTP (en secondes).
        :param quarantine_time: Temps de quarantaine par défaut pour un RPC défaillant (en secondes).
        """
        if not rpc_urls:
            raise ValueError("rpc_urls ne peut pas être vide.")

        self.rpc_urls: List[str] = list(rpc_urls)
        self.timeout: float = float(timeout)
        self.quarantine_time: float = float(quarantine_time)
        self.quarantined_rpcs: Dict[str, float] = {}
        self.current_index: int = 0
        self.logger = logging.getLogger("DeFiPilot.RPCManager")

        self.logger.info(
            f"RPCManager initialisé avec {len(self.rpc_urls)} RPC(s). "
            f"Timeout: {self.timeout}s, Quarantaine: {self.quarantine_time}s."
        )

    def is_quarantined(self, url: str) -> bool:
        """
        Vérifie si une URL RPC est actuellement en quarantaine.
        Levée automatique de la quarantaine si le délai est écoulé.
        """
        if url in self.quarantined_rpcs:
            quarantine_start = self.quarantined_rpcs[url]
            if time.time() - quarantine_start < self.quarantine_time:
                return True
            else:
                del self.quarantined_rpcs[url]
                self.logger.info(
                    f"Quarantaine expirée pour le RPC {url}. Réintégration dans le pool."
                )
                return False
        return False

    def quarantine_rpc(self, url: str, reason: str = "") -> None:
        """
        Place un RPC défaillant en quarantaine pour la durée configurée.
        """
        self.quarantined_rpcs[url] = time.time()
        self.logger.warning(
            f"RPC mis en quarantaine ({url}) pour {self.quarantine_time}s. Raison: {reason}"
        )

    def clear_quarantine(self, url: Optional[str] = None) -> None:
        """
        Réinitialise la quarantaine pour une URL donnée ou pour toutes les URLs.
        """
        if url:
            if url in self.quarantined_rpcs:
                del self.quarantined_rpcs[url]
                self.logger.info(f"Quarantaine réinitialisée pour le RPC {url}.")
        else:
            self.quarantined_rpcs.clear()
            self.logger.info("Quarantaine réinitialisée pour tous les RPCs.")

    def get_web3(self) -> Web3:
        """
        Retourne une instance Web3 valide.
        Si un RPC est en quarantaine ou échoue (timeout/erreur HTTP/déconnexion),
        passe automatiquement au suivant dans la liste.
        """
        num_rpcs = len(self.rpc_urls)
        start_index = self.current_index

        for i in range(num_rpcs):
            index = (start_index + i) % num_rpcs
            url = self.rpc_urls[index]

            if self.is_quarantined(url):
                self.logger.debug(f"RPC {url} ignoré car actuellement en quarantaine.")
                continue

            try:
                provider = Web3.HTTPProvider(url, request_kwargs={"timeout": self.timeout})
                w3 = Web3(provider)
                if w3.is_connected():
                    self.current_index = index
                    self.logger.debug(f"Connexion Web3 réussie via le RPC: {url}")
                    return w3
                else:
                    self.quarantine_rpc(url, reason="w3.is_connected() a retourné False.")
            except Exception as exc:
                self.quarantine_rpc(url, reason=f"Erreur lors de la connexion Web3: {exc}")

        self.logger.error("Aucun RPC Polygon disponible (tous hors service ou en quarantaine).")
        raise RuntimeError("Aucun RPC Polygon disponible (tous hors service ou en quarantaine).")

    def execute_call(self, func_name: Union[str, Callable], *args: Any, **kwargs: Any) -> Any:
        """
        Wrapper sécurisé pour exécuter une méthode Web3 avec retry et failover automatique
        sur un RPC secondaire ou de fallback.
        """
        last_exception: Optional[Exception] = None
        num_rpcs = len(self.rpc_urls)

        for attempt in range(num_rpcs):
            current_url: Optional[str] = None
            try:
                w3 = self.get_web3()
                current_url = getattr(w3.provider, "endpoint_uri", self.rpc_urls[self.current_index])

                if callable(func_name):
                    try:
                        return func_name(w3, *args, **kwargs)
                    except TypeError:
                        return func_name(*args, **kwargs)
                elif isinstance(func_name, str):
                    if "." in func_name:
                        parts = func_name.split(".")
                        target: Any = w3
                        for part in parts:
                            target = getattr(target, part)
                    else:
                        if hasattr(w3.eth, func_name):
                            target = getattr(w3.eth, func_name)
                        elif hasattr(w3, func_name):
                            target = getattr(w3, func_name)
                        else:
                            raise AttributeError(
                                f"Méthode '{func_name}' non trouvée sur Web3 ou Web3.eth."
                            )

                    if callable(target):
                        return target(*args, **kwargs)
                    return target
                else:
                    raise ValueError(
                        "func_name doit être un nom de méthode (str) ou une fonction (callable)."
                    )

            except RuntimeError as exc:
                if "Aucun RPC Polygon disponible" in str(exc):
                    raise
                last_exception = exc
                if current_url:
                    self.quarantine_rpc(
                        current_url, reason=f"Erreur d'exécution '{func_name}': {exc}"
                    )
                self.logger.warning(
                    f"Échec de l'appel '{func_name}' sur le RPC {current_url}: {exc}. Failover..."
                )
                self.current_index = (self.current_index + 1) % num_rpcs
            except (AttributeError, ValueError) as exc:
                raise
            except Exception as exc:
                last_exception = exc
                if current_url:
                    self.quarantine_rpc(
                        current_url, reason=f"Erreur d'exécution '{func_name}': {exc}"
                    )
                else:
                    self.quarantine_rpc(
                        self.rpc_urls[self.current_index],
                        reason=f"Erreur d'exécution '{func_name}': {exc}",
                    )
                self.logger.warning(
                    f"Échec de l'appel '{func_name}': {exc}. Failover vers le RPC suivant..."
                )
                self.current_index = (self.current_index + 1) % num_rpcs

        raise RuntimeError(
            f"Échec de l'exécution de '{func_name}' sur tous les RPCs disponibles. "
            f"Dernière erreur: {last_exception}"
        ) from last_exception
