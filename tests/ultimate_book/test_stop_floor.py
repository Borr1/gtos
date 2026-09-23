"""Identity tests for the shared legacy stop-floor expression.

This change centralizes an expression already present in exactly three generators. It does
not authorize the proposed floor on any additional sleeve and makes no economic/full-flow
claim. Historical P3 receipts remain mechanism-only comparators pending a fresh raw DAG.
"""

from __future__ import annotations

import random
from decimal import Decimal
from fractions import Fraction

import pytest

from src.components.ultimate_book.sleeves import asia_pdl_fade
from src.components.ultimate_book.sleeves import liq_asia_up_low_metal
from src.components.ultimate_book.sleeves import metals
from src.components.ultimate_book.sleeves import metals_ob_micro
from src.components.ultimate_book.sleeves import orb_crypto_london
from src.components.ultimate_book.sleeves import structural_retest
from src.components.ultimate_book.sleeves import vol_squeeze
from src.components.ultimate_book.sleeves._stop_floor import (
    DEFAULT_ATR_STOP_FLOOR,
    floor_stop,
)


def test_floor_stop_is_the_exact_legacy_expression_over_finite_floats():
    rng = random.Random(20260808)
    for _ in range(100_000):
        raw = rng.uniform(-1_000_000.0, 1_000_000.0)
        atr = rng.uniform(-1_000.0, 1_000.0)
        floor_atr = rng.uniform(-5.0, 5.0)
        assert floor_stop(raw, atr, floor_atr) == max(raw, floor_atr * atr)


@pytest.mark.parametrize(
    ("raw", "atr", "floor_atr"),
    [
        (0, 2, 1),
        (-10, 2, 1),
        (-10, 2, 0),
        (Fraction(-7, 3), Fraction(5, 2), Fraction(1, 4)),
        (Decimal("-2.125"), Decimal("10.0"), Decimal("0.25")),
        (Decimal("2.125"), Decimal("10.0"), Decimal("0.25")),
    ],
)
def test_zero_negative_and_non_float_operands_preserve_value_and_type(raw, atr, floor_atr):
    expected = max(raw, floor_atr * atr)
    got = floor_stop(raw, atr, floor_atr)
    assert got == expected
    assert type(got) is type(expected)


def test_only_the_three_legacy_callers_share_the_existing_constant():
    assert DEFAULT_ATR_STOP_FLOOR == 0.25
    assert metals.ATR_STOP_FLOOR == DEFAULT_ATR_STOP_FLOOR
    assert metals_ob_micro.ATR_STOP_FLOOR == DEFAULT_ATR_STOP_FLOOR
    assert structural_retest.ATR_STOP_FLOOR == DEFAULT_ATR_STOP_FLOOR

    # These proposals require fresh full-DAG authority; this identity refactor does not arm
    # them by quietly adding a module-level policy constant.
    for module in (
        asia_pdl_fade,
        liq_asia_up_low_metal,
        orb_crypto_london,
        vol_squeeze,
    ):
        assert not hasattr(module, "ATR_STOP_FLOOR")


def test_regime_spine_keeps_resolving_the_legacy_metals_exports():
    from src.research_infra.regime_spine import state

    assert state.ATR_STOP_FLOOR == DEFAULT_ATR_STOP_FLOOR
    assert state.STOP_BUF == metals.STOP_BUF


def test_metals_expression_is_bit_identical_for_both_directions():
    rng = random.Random(31337)
    for _ in range(50_000):
        atr = rng.uniform(1e-12, 100.0)
        close = rng.uniform(-10_000.0, 10_000.0)
        low = close - rng.uniform(0.0, 100.0)
        high = close + rng.uniform(0.0, 100.0)
        gap_bottom = close - rng.uniform(0.0, 100.0)
        gap_top = close + rng.uniform(0.0, 100.0)

        long_raw = (close - min(low, gap_bottom)) + metals.STOP_BUF * atr
        short_raw = (max(high, gap_top) - close) + metals.STOP_BUF * atr
        assert floor_stop(long_raw, atr, metals.ATR_STOP_FLOOR) == max(
            long_raw, metals.ATR_STOP_FLOOR * atr
        )
        assert floor_stop(short_raw, atr, metals.ATR_STOP_FLOOR) == max(
            short_raw, metals.ATR_STOP_FLOOR * atr
        )
