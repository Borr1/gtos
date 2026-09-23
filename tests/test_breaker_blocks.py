"""Tests for breaker block detection (Change 2)."""

from src.components.market_state import (
    identify_order_blocks,
    identify_breaker_blocks,
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    _build_timeframe_state,
)
from src.models.market_state_models import BreakerBlock, OrderBlock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_candle(i, open_, high, low, close, time="2026-01-01T08:00"):
    return {
        "time": time,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


def _bearish_ob_then_break_up():
    """Scenario: bearish OB forms, then gets broken to the upside → bullish breaker.

    Candle sequence:
    0-4: Setup swings for bearish structure
    5: Bearish candle (future OB)
    6: BOS down (breaks low)
    7-8: Price returns UP and breaks through OB (mitigates it)
    9-10: Price pulls back toward the breaker zone
    """
    candles = [
        # Setup: establish some structure
        _make_candle(0, 2660, 2665, 2658, 2663, "2026-01-01T00:00"),
        _make_candle(1, 2663, 2668, 2660, 2661, "2026-01-01T01:00"),
        _make_candle(2, 2661, 2664, 2656, 2657, "2026-01-01T02:00"),
        _make_candle(3, 2657, 2662, 2654, 2660, "2026-01-01T03:00"),
        _make_candle(4, 2660, 2665, 2658, 2659, "2026-01-01T04:00"),
        # 5: Bearish candle = potential OB for bearish break
        _make_candle(5, 2662, 2664, 2655, 2656, "2026-01-01T05:00"),
        # 6: Strong bearish displacement - BOS down (breaks below swing low at ~2654)
        _make_candle(6, 2656, 2656, 2648, 2649, "2026-01-01T06:00"),
        # 7-8: Price reverses UP, breaks through the bearish OB zone (2664-2655)
        _make_candle(7, 2649, 2658, 2648, 2657, "2026-01-01T07:00"),
        _make_candle(8, 2657, 2670, 2656, 2668, "2026-01-01T08:00"),  # Body above OB high (2664)
        # 9: Price pulls back toward the breaker zone
        _make_candle(9, 2668, 2669, 2660, 2662, "2026-01-01T09:00"),
        # 10: Further continuation
        _make_candle(10, 2662, 2675, 2661, 2673, "2026-01-01T10:00"),
    ]
    return candles


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBreakerBlockDetection:
    def test_no_breakers_when_no_mitigated_obs(self):
        """Unmitigated OBs should produce no breaker blocks."""
        obs = [
            OrderBlock(
                type="bullish", high=2660, low=2655,
                open=2658, close=2656,
                formation_index=5, formation_time="2026-01-01T05:00",
                causing_bos_index=6, mitigated=False,
            ),
        ]
        candles = [_make_candle(i, 2650, 2655, 2645, 2650) for i in range(20)]
        breakers = identify_breaker_blocks(candles, obs)
        assert len(breakers) == 0

    def test_mitigated_bearish_ob_creates_bullish_breaker(self):
        """A mitigated bearish OB should flip to a bullish breaker."""
        # Bearish OB zone: high=2664, low=2655
        # Mitigated when price body closes above 2664
        candles = [
            _make_candle(0, 2660, 2665, 2658, 2663, "2026-01-01T00:00"),
            _make_candle(1, 2663, 2668, 2660, 2661, "2026-01-01T01:00"),
            _make_candle(2, 2661, 2664, 2656, 2657, "2026-01-01T02:00"),
            _make_candle(3, 2657, 2662, 2654, 2660, "2026-01-01T03:00"),
            _make_candle(4, 2660, 2665, 2658, 2659, "2026-01-01T04:00"),
            # 5: Bullish candle = bearish OB source
            _make_candle(5, 2656, 2664, 2655, 2662, "2026-01-01T05:00"),
            # 6: BOS down
            _make_candle(6, 2662, 2662, 2648, 2649, "2026-01-01T06:00"),
            # 7: Price body closes above OB high (2664) → mitigates the bearish OB
            _make_candle(7, 2649, 2670, 2648, 2668, "2026-01-01T07:00"),
            _make_candle(8, 2668, 2675, 2665, 2673, "2026-01-01T08:00"),
        ]

        obs = [
            OrderBlock(
                type="bearish", high=2664, low=2655,
                open=2656, close=2662,
                formation_index=5, formation_time="2026-01-01T05:00",
                causing_bos_index=6, mitigated=True,
                causing_event_type="BOS",
            ),
        ]

        breakers = identify_breaker_blocks(candles, obs)
        assert len(breakers) == 1
        bb = breakers[0]
        assert bb.direction == "bullish"
        assert bb.original_ob_direction == "bearish"
        assert bb.zone_high == 2664
        assert bb.zone_low == 2655
        assert bb.causing_event == "BOS"

    def test_mitigated_bullish_ob_creates_bearish_breaker(self):
        """A mitigated bullish OB should flip to a bearish breaker."""
        candles = [
            _make_candle(0, 2660, 2665, 2658, 2663, "2026-01-01T00:00"),
            _make_candle(1, 2663, 2668, 2660, 2661, "2026-01-01T01:00"),
            _make_candle(2, 2661, 2664, 2656, 2657, "2026-01-01T02:00"),
            _make_candle(3, 2657, 2662, 2654, 2660, "2026-01-01T03:00"),
            _make_candle(4, 2660, 2665, 2658, 2659, "2026-01-01T04:00"),
            # 5: Bearish candle = bullish OB source
            _make_candle(5, 2662, 2663, 2655, 2656, "2026-01-01T05:00"),
            # 6: BOS up
            _make_candle(6, 2656, 2672, 2655, 2670, "2026-01-01T06:00"),
            # 7: Price body closes below OB low (2655) → mitigates the bullish OB
            _make_candle(7, 2670, 2671, 2650, 2652, "2026-01-01T07:00"),
            _make_candle(8, 2652, 2653, 2645, 2647, "2026-01-01T08:00"),
        ]

        obs = [
            OrderBlock(
                type="bullish", high=2663, low=2655,
                open=2662, close=2656,
                formation_index=5, formation_time="2026-01-01T05:00",
                causing_bos_index=6, mitigated=True,
                causing_event_type="CHoCH",
            ),
        ]

        breakers = identify_breaker_blocks(candles, obs)
        assert len(breakers) == 1
        bb = breakers[0]
        assert bb.direction == "bearish"
        assert bb.original_ob_direction == "bullish"
        assert bb.causing_event == "CHoCH"

    def test_retested_breaker_marked(self):
        """If price returns to the breaker zone, is_retested should be True."""
        candles = [
            _make_candle(0, 2660, 2665, 2658, 2663, "2026-01-01T00:00"),
            _make_candle(1, 2663, 2668, 2660, 2661, "2026-01-01T01:00"),
            _make_candle(2, 2661, 2664, 2656, 2657, "2026-01-01T02:00"),
            _make_candle(3, 2657, 2662, 2654, 2660, "2026-01-01T03:00"),
            _make_candle(4, 2660, 2665, 2658, 2659, "2026-01-01T04:00"),
            _make_candle(5, 2656, 2664, 2655, 2662, "2026-01-01T05:00"),
            _make_candle(6, 2662, 2662, 2648, 2649, "2026-01-01T06:00"),
            # 7: Mitigates bearish OB (body above 2664)
            _make_candle(7, 2649, 2670, 2648, 2668, "2026-01-01T07:00"),
            # 8-9: Price pulls back INTO the breaker zone (2655-2664) → retest
            _make_candle(8, 2668, 2669, 2656, 2658, "2026-01-01T08:00"),
            _make_candle(9, 2658, 2672, 2657, 2670, "2026-01-01T09:00"),
        ]

        obs = [
            OrderBlock(
                type="bearish", high=2664, low=2655,
                open=2656, close=2662,
                formation_index=5, formation_time="2026-01-01T05:00",
                causing_bos_index=6, mitigated=True,
            ),
        ]

        breakers = identify_breaker_blocks(candles, obs)
        assert len(breakers) == 1
        assert breakers[0].is_retested is True


class TestBreakerBlockInMSO:
    def test_breaker_blocks_in_timeframe_state(self):
        """Verify breaker_blocks field appears in TimeframeState output."""
        # Use enough candles to produce swings/structure/breaks
        candles = []
        # Generate a trending-then-reversing sequence
        base = 2650
        for i in range(30):
            o = base + i * 0.5
            h = o + 2
            l = o - 1
            c = o + 1
            candles.append(_make_candle(i, o, h, l, c, f"2026-01-01T{i:02d}:00"))

        ts = _build_timeframe_state(candles, min_bars=2, fvg_min_gap=1.0)
        # breaker_blocks field should exist (may be empty if no mitigated OBs)
        assert hasattr(ts, "breaker_blocks")
        assert isinstance(ts.breaker_blocks, list)


class TestPromptIncludesBreaker:
    def test_system_prompt_mentions_breaker(self):
        """T7 C-gate prompt removed breaker block framework.
        Breaker blocks still exist in market state data but are not
        part of the evaluation decision anymore."""
        from src.prompts.primary_analyzer_prompt import SYSTEM_PROMPT
        # T7 removed breaker block from the decision prompt
        assert "BREAKER BLOCK RETEST" not in SYSTEM_PROMPT
        assert "BR1" not in SYSTEM_PROMPT
        # Core C-gate elements present instead
        assert "C1" in SYSTEM_PROMPT
        assert "C2" in SYSTEM_PROMPT

    def test_dynamic_context_includes_breaker_blocks(self):
        """Verify breaker blocks are rendered in dynamic context."""
        from src.prompts.primary_analyzer_prompt import build_dynamic_context
        from types import SimpleNamespace

        # Mock MSO with breaker blocks in H1
        mso_dict = {
            "timestamp_utc": "2026-01-01T08:00:00Z",
            "session_levels": {"session_high": 2670, "session_low": 2650, "london_high": 2668, "london_low": 2652},
            "detected_sweeps": [],
            "timeframes": {
                "H1": {
                    "structure": {"direction": "bullish", "protected_swing": None, "swing_sequence": []},
                    "structure_events": [],
                    "order_blocks": [],
                    "breaker_blocks": [{
                        "direction": "bullish",
                        "zone_high": 2664.0,
                        "zone_low": 2655.0,
                        "original_ob_direction": "bearish",
                        "formation_time": "2026-01-01T05:00",
                        "mitigation_time": "2026-01-01T07:00",
                        "causing_event": "BOS",
                        "is_retested": False,
                        "timeframe": "H1",
                    }],
                    "fair_value_gaps": [],
                    "premium_discount": None,
                    "avg_candle_body": 3.5,
                    "atr_14": 8.2,
                    "swings": [],
                },
                "M15": {
                    "structure": {"direction": "bullish", "protected_swing": None, "swing_sequence": []},
                    "structure_events": [],
                    "order_blocks": [],
                    "breaker_blocks": [],
                    "fair_value_gaps": [],
                    "premium_discount": None,
                    "avg_candle_body": 2.0,
                    "atr_14": 4.5,
                    "swings": [],
                },
            },
        }
        output = build_dynamic_context(mso_dict)
        assert "Breaker Block" in output or "breaker" in output.lower()
        assert "2664" in output
        assert "2655" in output


class TestSafetyAcceptsBreakerRetest:
    def test_breaker_retest_framework_accepted(self):
        """Verify PrimaryAnalysisOutput accepts breaker_retest framework."""
        from src.models.analysis_models import PrimaryAnalysisOutput

        data = {
            "timestamp_utc": "2026-01-01T08:00:00Z",
            "model_used": "test",
            "decision": "CANDIDATE",
            "confidence_score": 75,
            "framework": "breaker_retest",
            "kill_zone": "london",
            "reasoning": {
                "daily_bias": {"direction": "bullish", "confidence": "high", "explanation": "test"},
                "h4_alignment": {"aligned": True, "explanation": "test"},
                "h1_setup": {"poi_identified": True, "poi_type": "OB", "explanation": "test"},
                "liquidity_sweep": {"detected": False, "explanation": "test"},
                "m15_confirmation": {"choch_detected": True, "displacement_quality": "strong", "explanation": "test"},
                "setup_grade": "A",
                "overall_reasoning": "test",
            },
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 2660.0,
                "stop_loss": 2650.0,
                "take_profit_1": 2685.0,
                "risk_reward_ratio": 2.5,
            },
        }
        pa = PrimaryAnalysisOutput.model_validate(data)
        assert pa.framework == "breaker_retest"
