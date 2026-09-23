"""Tests for cross-instrument context (XAUUSD D1 direction + Asian range)."""

import pytest
import yaml
from pathlib import Path

from src.utils.cross_instrument import get_xauusd_d1_direction, get_asian_range_pct
from src.prompts.primary_analyzer_prompt import (
    build_system_prompt,
    build_user_message,
    format_cross_instrument_context,
)


# ── Fixtures ──────────────────────────────────────────────────────────

def _make_d1_candles(prices: list[tuple[float, float]], start_date="2025-01-01"):
    """Build D1 candle dicts from (low, high) pairs — enough for swing detection."""
    from datetime import date, timedelta
    candles = []
    d = date.fromisoformat(start_date)
    for i, (lo, hi) in enumerate(prices):
        o = (lo + hi) / 2
        c = (lo + hi) / 2 + 0.1  # slight bullish bias
        candles.append({
            "time": d.isoformat(),
            "open": o,
            "high": hi,
            "low": lo,
            "close": c,
            "volume": 1000,
        })
        d += timedelta(days=1)
    return candles


def _make_bullish_d1(n=20):
    """Generate 20 candles with clear HH/HL sequence (bullish).

    Creates a zigzag pattern: rally → pullback → higher rally → higher pullback.
    This produces detectable swing highs and swing lows via 2-bar pivot.
    """
    candles = []
    # Generate a zigzag that trends up
    # Pattern: 3 candles up, 2 candles down (higher low), repeat
    phase_prices = []
    base = 2000
    for cycle in range(4):
        # 3 candles up
        for j in range(3):
            p = base + cycle * 30 + j * 10
            phase_prices.append((p - 3, p + 12))
        # 2 candles down (pullback — but higher low than previous pullback)
        peak = base + cycle * 30 + 20
        for j in range(2):
            p = peak - (j + 1) * 8
            phase_prices.append((p - 3, p + 5))
    return _make_d1_candles(phase_prices[:n])


def _make_bearish_d1(n=20):
    """Generate 20 candles with clear LH/LL sequence (bearish)."""
    candles = []
    phase_prices = []
    base = 2500
    for cycle in range(4):
        # 3 candles down
        for j in range(3):
            p = base - cycle * 30 - j * 10
            phase_prices.append((p - 12, p + 3))
        # 2 candles up (pullback — but lower high than previous pullback)
        trough = base - cycle * 30 - 20
        for j in range(2):
            p = trough + (j + 1) * 8
            phase_prices.append((p - 5, p + 3))
    return _make_d1_candles(phase_prices[:n])


def _make_ranging_d1(n=20):
    """Generate 20 candles that oscillate without clear direction."""
    candles = []
    for i in range(n):
        base = 2200 + (10 if i % 2 == 0 else -10)
        candles.append((base - 8, base + 8))
    return _make_d1_candles(candles)


def _make_m15_candles(trade_date: str, asian_high: float, asian_low: float):
    """Generate M15 candles for the Asian session (00:00-06:45)."""
    candles = []
    hours = range(0, 7)  # 00:00 to 06:00
    for h in hours:
        for m in (0, 15, 30, 45):
            if h == 6 and m > 45:
                break
            t = f"{trade_date}T{h:02d}:{m:02d}:00Z"
            spread = asian_high - asian_low
            mid = (asian_high + asian_low) / 2
            # Vary prices within the range
            candles.append({
                "time": t,
                "open": mid - 0.0001,
                "high": asian_high - spread * 0.1,
                "low": asian_low + spread * 0.1,
                "close": mid + 0.0001,
                "volume": 100,
            })
    # Ensure at least one candle touches the extremes
    candles[0]["high"] = asian_high
    candles[-1]["low"] = asian_low
    return candles


def _load_gbpusd_config():
    """Load the actual GBPUSD config for testing."""
    config_path = Path(__file__).parent.parent / "config" / "agent_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    from src.utils.config import apply_instrument_overrides
    return apply_instrument_overrides(config, "GBPUSD")


def _load_gold_config():
    """Load the actual gold config for testing."""
    config_path = Path(__file__).parent.parent / "config" / "agent_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    from src.utils.config import apply_instrument_overrides
    return apply_instrument_overrides(config)


# ── Test get_xauusd_d1_direction ──────────────────────────────────────

class TestXauusdD1Direction:

    def test_bullish_detection(self):
        """Bullish: latest close > previous close."""
        candles = _make_d1_candles([(2000, 2010), (2005, 2015)], "2025-01-01")
        # candle 0: close ~2005.1, candle 1: close ~2010.1 → bullish
        result = get_xauusd_d1_direction("2025-01-02", candles)
        assert result == "bullish"

    def test_bearish_detection(self):
        """Bearish: latest close < previous close."""
        candles = _make_d1_candles([(2010, 2020), (2000, 2010)], "2025-01-01")
        # candle 0: close ~2015.1, candle 1: close ~2005.1 → bearish
        result = get_xauusd_d1_direction("2025-01-02", candles)
        assert result == "bearish"

    def test_unavailable_on_empty_data(self):
        result = get_xauusd_d1_direction("2025-01-20", [])
        assert result == "unavailable"

    def test_unavailable_on_single_candle(self):
        candles = _make_d1_candles([(2000, 2010)], "2025-01-01")
        result = get_xauusd_d1_direction("2025-01-01", candles)
        assert result == "unavailable"

    def test_date_filtering(self):
        """Only candles up to trade_date should be considered."""
        candles = _make_d1_candles(
            [(2000, 2010), (2005, 2015), (2000, 2008)],  # up then down
            "2025-01-01",
        )
        # At 2025-01-02, only first 2 candles visible → bullish
        result = get_xauusd_d1_direction("2025-01-02", candles)
        assert result == "bullish"
        # At 2025-01-03, all 3 visible → bearish (last close < previous close)
        result = get_xauusd_d1_direction("2025-01-03", candles)
        assert result == "bearish"

    def test_with_real_data(self):
        """Test with actual XAUUSD D1 CSV if available."""
        csv_path = Path(__file__).parent.parent / "data" / "XAUUSD_D1.csv"
        if not csv_path.exists():
            pytest.skip("XAUUSD_D1.csv not available")
        from scripts.historical_data_loader import parse_tradingview_csv
        candles = parse_tradingview_csv(csv_path)
        mid_date = candles[len(candles) // 2]["time"][:10]
        result = get_xauusd_d1_direction(mid_date, candles)
        assert result in ("bullish", "bearish", "unavailable")


# ── Test get_asian_range_pct ──────────────────────────────────────────

class TestAsianRangePct:

    def test_basic_calculation(self):
        trade_date = "2025-03-10"
        m15 = _make_m15_candles(trade_date, asian_high=1.2700, asian_low=1.2650)
        # D1 candles for ADR: 14 days with range of 0.0100 each
        d1 = []
        for i in range(20):
            d1.append({
                "time": f"2025-03-{i+1:02d}" if i < 9 else f"2025-03-{i+1:02d}",
                "open": 1.2600,
                "high": 1.2700,
                "low": 1.2600,
                "close": 1.2650,
                "volume": 1000,
            })
        # Fix dates properly
        from datetime import date, timedelta
        d = date(2025, 2, 15)
        for i in range(len(d1)):
            d1[i]["time"] = (d + timedelta(days=i)).isoformat()

        result = get_asian_range_pct(trade_date, m15, d1)
        assert result is not None
        assert result["asian_range"] > 0
        assert result["adr_14"] > 0
        assert result["pct_of_adr"] > 0
        assert result["category"] in ("narrow", "moderate", "wide")

    def test_narrow_range(self):
        trade_date = "2025-03-10"
        # Narrow Asian range: 0.0010 on ADR of 0.010 = 10%
        m15 = _make_m15_candles(trade_date, asian_high=1.2655, asian_low=1.2645)
        from datetime import date, timedelta
        d1 = []
        d = date(2025, 2, 15)
        for i in range(20):
            d1.append({
                "time": (d + timedelta(days=i)).isoformat(),
                "open": 1.2600, "high": 1.2700, "low": 1.2600, "close": 1.2650,
                "volume": 1000,
            })
        result = get_asian_range_pct(trade_date, m15, d1)
        assert result is not None
        assert result["category"] == "narrow"

    def test_none_on_missing_m15(self):
        result = get_asian_range_pct("2025-03-10", [], [])
        assert result is None

    def test_none_on_insufficient_d1(self):
        trade_date = "2025-03-10"
        m15 = _make_m15_candles(trade_date, asian_high=1.2700, asian_low=1.2650)
        d1 = [{"time": "2025-03-09", "open": 1.26, "high": 1.27, "low": 1.26, "close": 1.265, "volume": 100}]
        result = get_asian_range_pct(trade_date, m15, d1)
        assert result is None


# ── Test format_cross_instrument_context ──────────────────────────────

class TestFormatCrossInstrumentContext:

    def test_gbpusd_context_generated(self):
        config = _load_gbpusd_config()
        # Ensure feature is enabled for this test regardless of live config state
        config.setdefault("cross_instrument_context", {})["enabled"] = True
        asian_info = {
            "asian_range": 0.00050,
            "adr_14": 0.01000,
            "pct_of_adr": 50.0,
            "category": "moderate",
        }
        result = format_cross_instrument_context("bullish", asian_info, config)
        assert "## Cross-Instrument & Volatility Context" in result
        assert "XAUUSD D1 structure: bullish" in result
        assert "dollar weakness" in result
        assert "50% of ADR" in result
        assert "DECISION GUIDANCE" in result

    def test_gold_context_not_generated(self):
        config = _load_gold_config()
        result = format_cross_instrument_context("bullish", None, config)
        assert result == ""

    def test_unavailable_xau_with_asian(self):
        config = _load_gbpusd_config()
        config.setdefault("cross_instrument_context", {})["enabled"] = True
        asian_info = {"asian_range": 0.0005, "adr_14": 0.01, "pct_of_adr": 50.0, "category": "moderate"}
        result = format_cross_instrument_context("unavailable", asian_info, config)
        assert "Asian session range" in result
        # The XAU D1 direction line should NOT appear when unavailable
        assert "XAUUSD D1 structure: unavailable" not in result

    def test_both_unavailable_returns_empty(self):
        config = _load_gbpusd_config()
        result = format_cross_instrument_context("unavailable", None, config)
        assert result == ""

    def test_disabled_config_returns_empty(self):
        config = {"cross_instrument_context": {"enabled": False}}
        result = format_cross_instrument_context("bullish", None, config)
        assert result == ""


# ── Test correlation gate (B.1, ADR-006 follow-up) ────────────────────

class TestCorrelationGate:
    """B.1 fix — XAU-anchored block silently passes for low-|corr| candidates.

    The gate fires only when ``candidate_symbol`` is provided. Backward-compat
    callers without candidate_symbol see no gate (existing test class above
    asserts this implicitly). Threshold defaults to 0.4 from
    ``cross_instrument_context.correlation_gate_threshold``.
    """

    def _config(self, threshold: float | None = None, market_symbol: str | None = None) -> dict:
        cfg = {
            "cross_instrument_context": {
                "enabled": True,
                "reference_instrument": "XAUUSD",
                "reference_timeframe": "D1",
                "dollar_direction_map": {
                    "bullish": "weakness",
                    "bearish": "strength",
                    "unclear": "mixed",
                    "unavailable": "unknown",
                },
            },
        }
        if market_symbol is not None:
            cfg["market"] = {"symbol": market_symbol}
        if threshold is not None:
            cfg["cross_instrument_context"]["correlation_gate_threshold"] = threshold
        return cfg

    def test_xauusd_skips_gate(self):
        """XAUUSD itself (the reference) bypasses the gate — block emits."""
        config = self._config()
        result = format_cross_instrument_context(
            "bullish", None, config, candidate_symbol="XAUUSD",
        )
        assert "## Cross-Instrument & Volatility Context" in result
        assert "XAUUSD D1 structure: bullish" in result

    def test_xagusd_passes_gate(self):
        """XAGUSD |corr|=0.799 to XAUUSD — well above 0.4; block emits."""
        config = self._config()
        result = format_cross_instrument_context(
            "bullish", None, config, candidate_symbol="XAGUSD",
        )
        assert "## Cross-Instrument & Volatility Context" in result
        assert "XAUUSD D1 structure: bullish" in result

    def test_us30_blocked_by_gate(self):
        """US30 |corr|=0.346 to XAUUSD — below 0.4; block suppressed."""
        config = self._config()
        # Try both broker naming conventions — alias resolves US30 → US30_cash.
        for symbol in ("US30", "US30_cash"):
            result = format_cross_instrument_context(
                "bullish", None, config, candidate_symbol=symbol,
            )
            assert result == "", (
                f"Expected empty string for {symbol} (|corr|=0.346 < 0.4), got: "
                f"{result[:120]!r}"
            )

    def test_config_market_symbol_blocks_omitted_candidate_symbol(self):
        """Direct prompt callers cannot bypass B.1 by omitting candidate_symbol."""
        config = self._config(market_symbol="US30")
        result = format_cross_instrument_context("bullish", None, config)
        assert result == ""

    def test_config_market_symbol_allows_high_correlation_symbol(self):
        """Config fallback still permits high-|corr| instruments through."""
        config = self._config(market_symbol="XAGUSD")
        result = format_cross_instrument_context("bullish", None, config)
        assert "## Cross-Instrument & Volatility Context" in result
        assert "XAUUSD D1 structure: bullish" in result

    def test_threshold_config_override(self):
        """Raising threshold to 0.5 re-blocks tight-FX (EURUSD/GBPUSD ~0.41)."""
        # At default 0.4: EURUSD (|r|=0.41) and GBPUSD (|r|=0.419) pass.
        config_default = self._config()
        result_eur_default = format_cross_instrument_context(
            "bullish", None, config_default, candidate_symbol="EURUSD",
        )
        result_gbp_default = format_cross_instrument_context(
            "bullish", None, config_default, candidate_symbol="GBPUSD",
        )
        assert "## Cross-Instrument & Volatility Context" in result_eur_default
        assert "## Cross-Instrument & Volatility Context" in result_gbp_default

        # At 0.5: both fall below; block suppressed.
        config_strict = self._config(threshold=0.5)
        result_eur_strict = format_cross_instrument_context(
            "bullish", None, config_strict, candidate_symbol="EURUSD",
        )
        result_gbp_strict = format_cross_instrument_context(
            "bullish", None, config_strict, candidate_symbol="GBPUSD",
        )
        assert result_eur_strict == ""
        assert result_gbp_strict == ""

    def test_unknown_symbol_fails_closed(self):
        """Symbol not in correlation matrix → block suppressed (fail-closed)."""
        config = self._config()
        result = format_cross_instrument_context(
            "bullish", None, config, candidate_symbol="XYZUNKNOWN",
        )
        assert result == ""

    def test_no_candidate_symbol_keeps_legacy_behavior(self):
        """Backward compat — when candidate_symbol omitted, gate is dormant."""
        config = self._config()
        result = format_cross_instrument_context("bullish", None, config)
        # Block should emit because gate did not fire (no candidate provided).
        assert "## Cross-Instrument & Volatility Context" in result


# ── Test prompt integration ───────────────────────────────────────────

class TestPromptIntegration:

    def test_h1_poi_guardrail_in_prompt(self):
        """T7 C-gate prompt: H1 structural bias is checked via C1 gate.
        poi_identified is still enforced by verification.py (L2 check 3)."""
        config = _load_gold_config()
        sp = build_system_prompt(config)
        # C1 checks H1 directional bias
        assert "C1" in sp
        assert "H1" in sp
        assert "NO_TRADE" in sp

    def test_h1_poi_and_m15_rules_coexist(self):
        """T7 C-gate prompt: H1 (C1) and M15 (C2) gates coexist."""
        config = _load_gold_config()
        sp = build_system_prompt(config)
        assert "C1" in sp  # H1 bias gate
        assert "C2" in sp  # M15 non-opposition gate
        assert "M15" in sp

    def test_cross_instrument_in_gbpusd_user_message(self):
        """Cross-instrument context appears in GBPUSD user message."""
        from types import SimpleNamespace
        mso = SimpleNamespace(
            timestamp_utc="2025-03-10T07:30:00Z",
            model_dump=lambda mode="json": {
                "timestamp_utc": "2025-03-10T07:30:00Z",
                "session_levels": {"asian_high": 1.27, "asian_low": 1.26, "pdh": 1.28, "pdl": 1.25},
                "liquidity_pools": [], "timeframes": {"H1": {}, "M15": {}},
                "detected_sweeps": [], "data_quality": {},
            },
        )
        ci_text = "## Cross-Instrument & Volatility Context\nXAUUSD D1 structure: bullish"
        msg = build_user_message(
            mso, {}, "2025-03-10T07:30:00Z", "london",
            cross_instrument_context=ci_text,
        )
        assert "Cross-Instrument" in msg
        assert "XAUUSD D1 structure: bullish" in msg

    def test_no_cross_instrument_in_gold_user_message(self):
        """Gold prompt should NOT have cross-instrument context."""
        from types import SimpleNamespace
        mso = SimpleNamespace(
            timestamp_utc="2025-03-10T07:30:00Z",
            model_dump=lambda mode="json": {
                "timestamp_utc": "2025-03-10T07:30:00Z",
                "session_levels": {"asian_high": 2950, "asian_low": 2940, "pdh": 2960, "pdl": 2930},
                "liquidity_pools": [], "timeframes": {"H1": {}, "M15": {}},
                "detected_sweeps": [], "data_quality": {},
            },
        )
        # No cross_instrument_context passed = no section in output
        msg = build_user_message(mso, {}, "2025-03-10T07:30:00Z", "london")
        assert "Cross-Instrument" not in msg

    def test_cross_instrument_context_param_empty_string(self):
        """Empty string cross_instrument_context should not inject anything."""
        from types import SimpleNamespace
        mso = SimpleNamespace(
            timestamp_utc="2025-03-10T07:30:00Z",
            model_dump=lambda mode="json": {
                "timestamp_utc": "2025-03-10T07:30:00Z",
                "session_levels": {"asian_high": 1.27, "asian_low": 1.26, "pdh": 1.28, "pdl": 1.25},
                "liquidity_pools": [], "timeframes": {"H1": {}, "M15": {}},
                "detected_sweeps": [], "data_quality": {},
            },
        )
        msg = build_user_message(
            mso, {}, "2025-03-10T07:30:00Z", "london",
            cross_instrument_context="",
        )
        assert "Cross-Instrument" not in msg
