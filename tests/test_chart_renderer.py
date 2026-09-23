"""Tests for chart renderer."""

from __future__ import annotations

import pytest

from src.utils.chart_renderer import render_chart, chart_to_base64


def _make_candles(n=30, base=2600.0, step=1.5):
    """Generate synthetic uptrend candles."""
    candles = []
    price = base
    for i in range(n):
        o = price
        c = price + step * (1 if i % 3 != 2 else -0.5)
        h = max(o, c) + abs(step) * 0.3
        l = min(o, c) - abs(step) * 0.2
        candles.append({
            "time": f"2025-10-01T{7 + i // 4:02d}:{(i % 4) * 15:02d}:00Z",
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
        })
        price = c
    return candles


class TestRenderBasicChart:
    def test_render_returns_png(self):
        candles = _make_candles()
        result = render_chart(m15_candles=candles, kill_zone="london", current_price=candles[-1]["close"])
        assert result[:4] == b'\x89PNG'
        assert len(result) < 500_000

    def test_render_with_annotations(self):
        candles = _make_candles()
        result = render_chart(
            m15_candles=candles,
            order_blocks=[{"type": "bullish", "high": 2605.0, "low": 2600.0, "causing_event_type": "CHoCH"}],
            structure_breaks=[{"type": "CHoCH", "direction": "bullish", "level_broken": 2610.0}],
            session_levels={"asian_high": 2615.0, "asian_low": 2595.0, "pdh": 2620.0, "pdl": 2590.0},
            premium_discount={"equilibrium_50": 2607.0, "fib_62": 2604.0, "fib_79": 2601.0},
            kill_zone="london",
            current_price=2612.0,
        )
        assert result[:4] == b'\x89PNG'

    def test_render_empty_annotations(self):
        candles = _make_candles()
        result = render_chart(m15_candles=candles, kill_zone="ny", current_price=2610.0)
        assert result[:4] == b'\x89PNG'

    def test_chart_to_base64(self):
        candles = _make_candles(5)
        png = render_chart(m15_candles=candles, kill_zone="london", current_price=2605.0)
        b64 = chart_to_base64(png)
        assert isinstance(b64, str)
        assert len(b64) > 100

    def test_render_raises_on_empty_candles(self):
        with pytest.raises(ValueError):
            render_chart(m15_candles=[], kill_zone="london")
