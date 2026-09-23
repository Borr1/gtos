"""Exact commission comparisons for one account's closed round turns."""

from __future__ import annotations

import pytest

from src.costs.account_deals import fit_symbol_commission


def _turn(symbol: str, position_id: int, volume: float, price: float, commission: float):
    deals = []
    for entry, kind in ((0, 0), (1, 1)):
        deals.append({
            "symbol": symbol,
            "type": kind,
            "entry": entry,
            "volume": volume,
            "price": price,
            "commission": commission,
            "position_id": position_id,
        })
    return deals


def test_exact_zero_commission_is_kind_zero():
    fitted = fit_symbol_commission(
        _turn("GBPUSD", 11, 1.0, 1.0, 0.0),
        "GBPUSD",
        100000.0,
    )
    assert fitted["status"] == "captured"
    assert fitted["kind"] == "zero"
    assert fitted["value"] == 0


def test_dispersion_uses_max_equal_min():
    """The same per-lot charge at two prices is flat because max == min."""

    deals = _turn("XAUUSD", 11, 1.0, 1000.0, -5.0) + _turn("XAUUSD", 19, 1.0, 2000.0, -5.0)
    fitted = fit_symbol_commission(deals, "XAUUSD", 100.0)
    assert fitted["kind"] == "per_lot"
    assert fitted["value"] == pytest.approx(10.0)
    assert fitted["n_round_turns"] == 2
    assert fitted["charge_side"] == "both_sides"
