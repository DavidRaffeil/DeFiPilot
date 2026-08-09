"""
Tests unitaires pour le module RPCManager (core/execution/rpc_manager.py).
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from core.execution.rpc_manager import RPCManager


def test_rpc_manager_init():
    """Teste l'initialisation correcte du RPCManager avec des URLs et paramètres."""
    urls = ["https://polygon-rpc.com", "https://rpc-mainnet.matic.quiknode.pro"]
    manager = RPCManager(urls, timeout=5.0, quarantine_time=120.0)

    assert manager.rpc_urls == urls
    assert manager.timeout == 5.0
    assert manager.quarantine_time == 120.0
    assert len(manager.quarantined_rpcs) == 0

    # Test levée d'erreur si liste vide
    with pytest.raises(ValueError, match="rpc_urls ne peut pas être vide"):
        RPCManager([])


def test_rpc_manager_quarantine():
    """Teste la mise en quarantaine d'un RPC défaillant lors de get_web3()."""
    urls = ["https://rpc1.example.com", "https://rpc2.example.com"]
    manager = RPCManager(urls, timeout=2.0, quarantine_time=0.2)

    mock_w3_1 = MagicMock()
    mock_w3_1.is_connected.return_value = False
    mock_w3_1.provider.endpoint_uri = urls[0]

    mock_w3_2 = MagicMock()
    mock_w3_2.is_connected.return_value = True
    mock_w3_2.provider.endpoint_uri = urls[1]

    def mock_web3_constructor(provider):
        endpoint = getattr(provider, "endpoint_uri", None)
        if endpoint == urls[0]:
            return mock_w3_1
        return mock_w3_2

    with patch("core.execution.rpc_manager.Web3") as mock_web3_cls:
        mock_web3_cls.HTTPProvider.side_effect = lambda url, **kwargs: MagicMock(endpoint_uri=url)
        mock_web3_cls.side_effect = mock_web3_constructor

        w3 = manager.get_web3()
        # Le premier RPC ayant échoué à is_connected(), w3 doit provenir du 2ème RPC
        assert w3.provider.endpoint_uri == urls[1]
        assert manager.is_quarantined(urls[0]) is True
        assert manager.is_quarantined(urls[1]) is False

        # Attendre l'expiration de la quarantaine (0.2s)
        time.sleep(0.25)
        assert manager.is_quarantined(urls[0]) is False


def test_rpc_manager_failover_execute_call():
    """Teste le basculement transparent (failover) du RPC 1 vers le RPC 2 lors d'un appel."""
    urls = ["https://rpc1.example.com", "https://rpc2.example.com"]
    manager = RPCManager(urls, timeout=2.0, quarantine_time=300.0)

    mock_w3_1 = MagicMock()
    mock_w3_1.is_connected.return_value = True
    mock_w3_1.provider.endpoint_uri = urls[0]
    # Le RPC 1 lève une exception HTTP/Timeout lors de l'appel get_block_number
    mock_w3_1.eth.get_block_number.side_effect = TimeoutError("RPC 1 timeout during call")

    mock_w3_2 = MagicMock()
    mock_w3_2.is_connected.return_value = True
    mock_w3_2.provider.endpoint_uri = urls[1]
    mock_w3_2.eth.get_block_number.return_value = 999999

    def mock_web3_constructor(provider):
        endpoint = getattr(provider, "endpoint_uri", None)
        if endpoint == urls[0]:
            return mock_w3_1
        return mock_w3_2

    with patch("core.execution.rpc_manager.Web3") as mock_web3_cls:
        mock_web3_cls.HTTPProvider.side_effect = lambda url, **kwargs: MagicMock(endpoint_uri=url)
        mock_web3_cls.side_effect = mock_web3_constructor

        block_number = manager.execute_call("eth.get_block_number")

        # Résultat obtenu de façon transparente depuis le RPC 2
        assert block_number == 999999
        # Le RPC 1 a été mis en quarantaine après l'erreur
        assert manager.is_quarantined(urls[0]) is True
        assert manager.is_quarantined(urls[1]) is False


def test_rpc_manager_all_rpcs_failed():
    """Teste la levée de RuntimeError lorsque tous les RPCs sont indisponibles."""
    urls = ["https://rpc1.example.com", "https://rpc2.example.com"]
    manager = RPCManager(urls, timeout=2.0, quarantine_time=300.0)

    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = False

    with patch("core.execution.rpc_manager.Web3") as mock_web3_cls:
        mock_web3_cls.HTTPProvider.side_effect = lambda url, **kwargs: MagicMock(endpoint_uri=url)
        mock_web3_cls.return_value = mock_w3

        with pytest.raises(RuntimeError, match="Aucun RPC Polygon disponible"):
            manager.get_web3()


def test_rpc_manager_execute_call_with_callable():
    """Teste execute_call avec une fonction lambda/callable."""
    urls = ["https://rpc1.example.com"]
    manager = RPCManager(urls)

    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 137

    with patch("core.execution.rpc_manager.Web3") as mock_web3_cls:
        mock_web3_cls.HTTPProvider.side_effect = lambda url, **kwargs: MagicMock(endpoint_uri=url)
        mock_web3_cls.return_value = mock_w3

        chain_id = manager.execute_call(lambda w3: w3.eth.chain_id)
        assert chain_id == 137
