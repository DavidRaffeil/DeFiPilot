"""
Tests unitaires pour le module SlippageGuard (core/execution/slippage_guard.py).
"""

import time
import pytest
from core.execution.slippage_guard import SlippageGuard


def test_calculate_min_amount_out_exact():
    """Teste le calcul exact du montant minimal après slippage."""
    guard = SlippageGuard(max_allowed_slippage_pct=3.0)

    # 100 USDC à 0.5% slippage -> 99.5 USDC
    min_out = guard.calculate_min_amount_out(100.0, 0.5)
    assert min_out == pytest.approx(99.5)

    # 1000 entiers (Wei) à 1.0% slippage -> 990
    min_out_int = guard.calculate_min_amount_out(1000, 1.0)
    assert min_out_int == 990
    assert isinstance(min_out_int, int)

    # 50.0 à 0.1% slippage -> 49.95
    min_out_small = guard.calculate_min_amount_out(50.0, 0.1)
    assert min_out_small == pytest.approx(49.95)


def test_rejection_excessive_slippage():
    """Teste le rejet des pourcentages de slippage abusifs (> 3.0%) ou négatifs."""
    guard = SlippageGuard(max_allowed_slippage_pct=3.0)

    # Slippage > 3.0%
    with pytest.raises(ValueError, match="dépasse le plafond"):
        guard.calculate_min_amount_out(100.0, 3.5)

    # Slippage négatif
    with pytest.raises(ValueError, match="négatif"):
        guard.calculate_min_amount_out(100.0, -0.5)


def test_calculate_deadline_validity():
    """Teste le calcul valide et futuriste du timestamp de deadline."""
    guard = SlippageGuard(default_ttl_seconds=180)

    now = int(time.time())
    deadline_default = guard.calculate_deadline()

    # Doit être entre now + 179s et now + 185s
    assert deadline_default >= now + 179
    assert deadline_default <= now + 185

    # TTL sur-mesure (300s)
    deadline_custom = guard.calculate_deadline(ttl_seconds=300)
    assert deadline_custom >= now + 299
    assert deadline_custom <= now + 305

    # TTL invalide
    with pytest.raises(ValueError, match="positif"):
        guard.calculate_deadline(ttl_seconds=0)


def test_decimal_conversions():
    """Teste les utilitaires de conversion pour les décimales des tokens."""
    # 6 decimals (USDC/USDT)
    raw_usdc = SlippageGuard.to_raw_amount(100.5, 6)
    assert raw_usdc == 100_500_000
    assert SlippageGuard.from_raw_amount(raw_usdc, 6) == 100.5

    # 18 decimals (POL/ETH/wETH)
    raw_eth = SlippageGuard.to_raw_amount(1.5, 18)
    assert raw_eth == 1_500_000_000_000_000_000
    assert SlippageGuard.from_raw_amount(raw_eth, 18) == 1.5


def test_calculate_min_amount_out_raw():
    """Teste le calcul direct du amount_out_min en unités atomiques entières."""
    guard = SlippageGuard(max_allowed_slippage_pct=3.0)

    # 100 USDC (6 decimals) avec 0.5% slippage -> 99.5 USDC = 99_500_000 int
    min_raw = guard.calculate_min_amount_out_raw(100.0, 0.5, decimals=6)
    assert min_raw == 99_500_000
    assert isinstance(min_raw, int)
