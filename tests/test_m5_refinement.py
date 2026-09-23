"""Tests for M5 Entry Refinement module."""

import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.components.m5_refinement import (
    _zone_has_swing_candidate,
    clamp_m5_sl_to_ob_boundary,
    format_m5_candles,
    refine_entry_m5,
    apply_m5_overrides,
    M5_SYSTEM_PROMPT,
    M5_USER_TEMPLATE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0, rr=1.5, kz="london"):
    """Build a minimal PrimaryAnalysisOutput-like object."""
    tp1 = entry + (entry - sl) * rr if direction == "LONG" else entry - (sl - entry) * rr
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        take_profit_1=tp1,
        take_profit_2=0.0,
        take_profit_3=0.0,
        risk_reward_ratio=rr,
        position_size_lots=0.01,
        _m15_atr=0,  # Will be set by orchestrator
    )
    return SimpleNamespace(
        trade_parameters=tp,
        kill_zone=kz,
        reasoning=SimpleNamespace(setup_grade="A+"),
    )


def _mock_m5_candles(n=36, base_price=3990.0):
    """Generate n mock M5 candles."""
    candles = []
    price = base_price
    for i in range(n):
        o = price
        h = price + 1.5
        l = price - 1.0
        c = price + 0.5
        candles.append({
            "time": f"2025-03-25T07:{i*5:02d}:00Z",
            "open": round(o, 2),
            "high": round(h, 2),
            "low": round(l, 2),
            "close": round(c, 2),
            "volume": 500,
        })
        price = c
    return candles


def _mock_llm_response(json_obj):
    """Build a mock LLMResponse."""
    return SimpleNamespace(text=json.dumps(json_obj))


def _mock_llm_backend(response_json):
    """Build a mock LLMBackend that returns a fixed response."""
    backend = MagicMock()
    backend.call.return_value = _mock_llm_response(response_json)
    return backend


def _m5_config(enabled=True, sl_floor=10.0, quality_gate=None):
    return {
        "enabled": enabled,
        "sl_floor": sl_floor,
        "quality_gate": quality_gate or ["HIGH", "MEDIUM"],
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
    }


# ---------------------------------------------------------------------------
# Test: M5 candle formatting
# ---------------------------------------------------------------------------

class TestFormatM5Candles:
    def test_basic_formatting(self):
        candles = _mock_m5_candles(3, base_price=4000.0)
        result = format_m5_candles(candles)
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "[BULL]" in lines[0] or "[BEAR]" in lines[0] or "[DOJI]" in lines[0]
        assert "← CURRENT" in lines[-1]
        assert "← CURRENT" not in lines[0]

    def test_includes_ohlc(self):
        candles = [{"time": "2025-01-01T07:00:00Z", "open": 4000.0,
                    "high": 4005.0, "low": 3998.0, "close": 4003.0, "volume": 100}]
        result = format_m5_candles(candles)
        assert "O:4000.00" in result
        assert "H:4005.00" in result
        assert "L:3998.00" in result
        assert "C:4003.00" in result


# ---------------------------------------------------------------------------
# Test: M5 refinement — HIGH quality
# ---------------------------------------------------------------------------

class TestRefineEntryM5:
    def test_high_quality_refinement(self):
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED",
            "m5_quality": "HIGH",
            "m5_sl": 3990.0,
            "m5_sl_distance": 10.0,
            "m5_structure": "bos",
            "reasoning": "Clean M5 BOS with displacement.",
        }
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)

        assert result["applied"] is True
        ov = result["overrides"]
        assert ov["stop_loss"] == 3990.0  # entry(4000) - 10
        assert ov["take_profit_1"] == 4015.0  # entry(4000) + 1.5*10
        assert ov["risk_reward_ratio"] == 1.5
        assert ov["m5_quality"] == "HIGH"
        assert ov["m5_refined"] is True
        assert ov["m5_floor_applied"] is False  # raw=10 >= floor=10

    def test_low_quality_fallback(self):
        analysis = _mock_analysis()
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "LOW",
                    "m5_sl": 3995.0, "m5_sl_distance": 5.0,
                    "m5_structure": None, "reasoning": "No clear structure."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False

    def test_no_refinement_response(self):
        analysis = _mock_analysis()
        candles = _mock_m5_candles(36)
        response = {"decision": "NO_REFINEMENT", "m5_quality": "LOW",
                    "m5_sl": None, "m5_sl_distance": None,
                    "m5_structure": None, "reasoning": "No M5 structure."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False

    def test_sl_out_of_range_rejected(self):
        """M5 SL above entry for LONG → rejected."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 4005.0, "m5_sl_distance": 5.0,
                    "m5_structure": "bos", "reasoning": "Bad SL."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False

    def test_sl_below_m15_sl_rejected(self):
        """M5 SL below M15 SL for LONG → rejected."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 3950.0, "m5_sl_distance": 50.0,
                    "m5_structure": "bos", "reasoning": "Too wide."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False

    def test_sl_floor_enforcement(self):
        """Raw M5 distance $5 < floor $10 → widened to $10."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 3995.0, "m5_sl_distance": 5.0,
                    "m5_structure": "bos", "reasoning": "Tight M5 swing."}
        backend = _mock_llm_backend(response)
        config = _m5_config(sl_floor=10.0)

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is True
        assert result["overrides"]["sl_distance"] == 10.0
        assert result["overrides"]["stop_loss"] == 3990.0
        assert result["overrides"]["m5_floor_applied"] is True

    def test_atr_floor_overrides_m5(self):
        """ATR = $10, 1.5*ATR = $15 > M5 floor $10 → final = $15."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        analysis.trade_parameters._m15_atr = 10.0  # 1.5*10 = 15
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 3992.0, "m5_sl_distance": 8.0,
                    "m5_structure": "bos", "reasoning": "M5 swing found."}
        backend = _mock_llm_backend(response)
        config = _m5_config(sl_floor=10.0)

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is True
        assert result["overrides"]["sl_distance"] == 15.0  # 1.5 * ATR
        assert result["overrides"]["stop_loss"] == 3985.0
        assert result["overrides"]["take_profit_1"] == 4022.5  # 4000 + 1.5*15

    def test_api_failure_fallback(self):
        analysis = _mock_analysis()
        candles = _mock_m5_candles(36)
        backend = MagicMock()
        backend.call.side_effect = RuntimeError("API timeout")
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "API_ERROR"

    def test_config_disabled(self):
        analysis = _mock_analysis()
        candles = _mock_m5_candles(36)
        backend = MagicMock()
        config = _m5_config(enabled=False)

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "DISABLED"
        backend.call.assert_not_called()

    def test_insufficient_candles(self):
        analysis = _mock_analysis()
        candles = _mock_m5_candles(5)  # Less than 12
        backend = MagicMock()
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "NO_DATA"
        backend.call.assert_not_called()

    def test_none_candles(self):
        analysis = _mock_analysis()
        backend = MagicMock()
        config = _m5_config()

        result = refine_entry_m5(analysis, None, config, backend)
        assert result["applied"] is False
        backend.call.assert_not_called()

    def test_short_direction(self):
        """SHORT trade: M5 SL above entry, TP below entry."""
        analysis = _mock_analysis(direction="SHORT", entry=4000.0, sl=4040.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 4012.0, "m5_sl_distance": 12.0,
                    "m5_structure": "bos", "reasoning": "Bearish BOS."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is True
        assert result["overrides"]["stop_loss"] == 4012.0  # 4000 + 12
        assert result["overrides"]["take_profit_1"] == 3982.0  # 4000 - 1.5*12

    def test_tp_exactly_1_5r(self):
        """TP is always exactly 1.5× floored SL distance."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "MEDIUM",
                    "m5_sl": 3988.0, "m5_sl_distance": 12.0,
                    "m5_structure": "higher_low", "reasoning": "M5 HL."}
        backend = _mock_llm_backend(response)
        config = _m5_config(sl_floor=10.0)

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is True
        sl_dist = result["overrides"]["sl_distance"]
        expected_tp = 4000.0 + 1.5 * sl_dist
        assert result["overrides"]["take_profit_1"] == expected_tp

    def test_raw_sl_too_tight_rejected(self):
        """M5 SL distance < $3 → rejected as unrealistic."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 3998.0, "m5_sl_distance": 2.0,
                    "m5_structure": "bos", "reasoning": "Very tight."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "SL_TOO_TIGHT"

    def test_markdown_fenced_json_parsed(self):
        """Response wrapped in ```json ... ``` is parsed correctly."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        json_body = json.dumps({
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 3990.0, "m5_sl_distance": 10.0,
            "m5_structure": "bos", "reasoning": "Clean."
        })
        raw = f"```json\n{json_body}\n```"
        backend = MagicMock()
        backend.call.return_value = SimpleNamespace(text=raw)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)
        assert result["applied"] is True


# ---------------------------------------------------------------------------
# Test: _zone_has_swing_candidate (deterministic pre-check)
# ---------------------------------------------------------------------------


def _candle(low, high, ts="2025-03-25T07:00:00Z"):
    """Minimal candle helper."""
    return {"time": ts, "open": low, "high": high, "low": low, "close": high, "volume": 1}


class TestZoneHasSwingCandidate:
    def test_long_at_least_one_low_in_zone(self):
        """LONG: any candle with low in (m15_sl, entry) → True."""
        candles = [_candle(low=215.50, high=215.55)]  # 215.434 < 215.50 < 215.701
        assert _zone_has_swing_candidate("LONG", entry=215.701, m15_sl=215.434,
                                          m5_candles=candles) is True

    def test_long_no_low_in_zone_all_above_entry(self):
        """GBPJPY 2026-04-29 scenario: every candle low sits ABOVE entry → False.

        Reproduces the late-cycle case where price has trended past the M15
        entry and the 3h M5 lookback no longer overlaps the (m15_sl, entry)
        zone. Without this gate the AI was being asked to find a swing low
        that demonstrably cannot exist in the data — every emit then tripped
        the SL_OUT_OF_RANGE guard, producing per-cycle WARNING noise (14 hits
        on GBPJPY 13:15-15:30 UTC) and wasted Sonnet round-trips.
        """
        # All candles trading 215.78-215.85 — entirely above the 215.701 entry
        candles = [_candle(low=215.78 + i * 0.01, high=215.85 + i * 0.01) for i in range(36)]
        assert _zone_has_swing_candidate("LONG", entry=215.701, m15_sl=215.434,
                                          m5_candles=candles) is False

    def test_long_no_low_in_zone_all_below_m15_sl(self):
        """LONG: every candle low BELOW M15 SL → False (no swing candidate possible)."""
        candles = [_candle(low=215.20, high=215.30) for _ in range(36)]
        assert _zone_has_swing_candidate("LONG", entry=215.701, m15_sl=215.434,
                                          m5_candles=candles) is False

    def test_long_low_at_zone_boundary_excluded(self):
        """Boundary check: low equal to m15_sl or entry is NOT in the zone (strict)."""
        candles = [
            _candle(low=215.434, high=215.50),  # low == m15_sl
            _candle(low=215.701, high=215.80),  # low == entry
        ]
        assert _zone_has_swing_candidate("LONG", entry=215.701, m15_sl=215.434,
                                          m5_candles=candles) is False

    def test_short_at_least_one_high_in_zone(self):
        """SHORT: any candle with high in (entry, m15_sl) → True."""
        candles = [_candle(low=4001.0, high=4015.0)]  # 4000 < 4015 < 4040
        assert _zone_has_swing_candidate("SHORT", entry=4000.0, m15_sl=4040.0,
                                          m5_candles=candles) is True

    def test_short_no_high_in_zone_all_below_entry(self):
        """SHORT: every candle high BELOW entry → False."""
        candles = [_candle(low=3990.0, high=3998.0) for _ in range(36)]
        assert _zone_has_swing_candidate("SHORT", entry=4000.0, m15_sl=4040.0,
                                          m5_candles=candles) is False

    def test_short_no_high_in_zone_all_above_m15_sl(self):
        """SHORT: every candle high ABOVE M15 SL → False."""
        candles = [_candle(low=4042.0, high=4050.0) for _ in range(36)]
        assert _zone_has_swing_candidate("SHORT", entry=4000.0, m15_sl=4040.0,
                                          m5_candles=candles) is False

    def test_empty_candles_returns_false(self):
        assert _zone_has_swing_candidate("LONG", entry=4000, m15_sl=3960,
                                          m5_candles=[]) is False

    def test_none_candles_returns_false(self):
        assert _zone_has_swing_candidate("LONG", entry=4000, m15_sl=3960,
                                          m5_candles=None) is False


class TestRefineEntryM5ZoneSkip:
    """`refine_entry_m5` must short-circuit when the pre-check fails — no API call."""

    def test_skip_no_zone_structure_long(self):
        """LONG with all M5 candles above entry → NO_ZONE_STRUCTURE, AI not called.

        This is the GBPJPY 2026-04-29 NY scenario: every CANDIDATE in the
        13:15-15:30 UTC window had entry=215.701 but the 3h M5 lookback was
        entirely above ~215.78. Pre-FA: 14 wasted API calls + 14 WARNINGs.
        Post-FA: zero API calls, zero WARNINGs, M15 SL preserved.
        """
        analysis = _mock_analysis(direction="LONG", entry=215.701, sl=215.434)
        candles = [_candle(low=215.78 + i * 0.01, high=215.85 + i * 0.01) for i in range(36)]
        backend = MagicMock()
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)

        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "NO_ZONE_STRUCTURE"
        backend.call.assert_not_called()

    def test_skip_no_zone_structure_short(self):
        """SHORT mirror: all candle highs below entry → NO_ZONE_STRUCTURE, AI not called."""
        analysis = _mock_analysis(direction="SHORT", entry=4000.0, sl=4040.0)
        candles = [_candle(low=3980.0 - i * 0.5, high=3990.0 - i * 0.5) for i in range(36)]
        backend = MagicMock()
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)

        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "NO_ZONE_STRUCTURE"
        backend.call.assert_not_called()

    def test_pre_check_passes_ai_still_called(self):
        """At least one candle low in zone → AI is invoked normally (no regression on
        the standard happy path, including the fallback paths that follow it)."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        # _mock_m5_candles has lows in (3960, 4000) for many indices — pre-check passes
        candles = _mock_m5_candles(36)
        response = {"decision": "REFINED", "m5_quality": "HIGH",
                    "m5_sl": 3990.0, "m5_sl_distance": 10.0,
                    "m5_structure": "bos", "reasoning": "Clean BOS in zone."}
        backend = _mock_llm_backend(response)
        config = _m5_config()

        result = refine_entry_m5(analysis, candles, config, backend)

        assert result["applied"] is True
        backend.call.assert_called_once()


# ---------------------------------------------------------------------------
# Test: apply_m5_overrides
# ---------------------------------------------------------------------------

class TestApplyM5Overrides:
    def test_overrides_applied(self):
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        overrides = {
            "stop_loss": 3990.0,
            "take_profit_1": 4015.0,
            "risk_reward_ratio": 1.5,
        }
        apply_m5_overrides(analysis, overrides)

        assert analysis.trade_parameters.stop_loss == 3990.0
        assert analysis.trade_parameters.take_profit_1 == 4015.0
        assert analysis.trade_parameters.risk_reward_ratio == 1.5
        # Originals preserved
        assert analysis.trade_parameters._m15_original_sl == 3960.0

    def test_none_trade_params_no_crash(self):
        analysis = SimpleNamespace(trade_parameters=None)
        apply_m5_overrides(analysis, {"stop_loss": 100})
        assert analysis.trade_parameters is None


# ---------------------------------------------------------------------------
# Test: Integration — M5 override before Gate 1
# ---------------------------------------------------------------------------

class TestM5IntegrationWithPermissions:
    def test_m5_sl_passes_gate1(self):
        """M5 SL $10 passes Gate 1's $5 minimum and ATR check."""
        from src.components.permissions import check_permissions
        from src.mt5.mt5_mock import MockMT5

        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        # Add daily_bias to reasoning (required by Gate 1)
        analysis.reasoning.daily_bias = SimpleNamespace(direction="bullish")
        # Apply M5 overrides
        overrides = {
            "stop_loss": 3990.0,       # $10 distance
            "take_profit_1": 4015.0,   # 1.5 × $10
            "risk_reward_ratio": 1.5,
        }
        apply_m5_overrides(analysis, overrides)

        mso = SimpleNamespace(timeframes={"M15": SimpleNamespace(atr_14=5.0)})
        mt5 = MockMT5(); mt5.connect()
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}

        denial = check_permissions(analysis, mso, state, mt5)
        assert denial is None  # Should pass all gates


# ---------------------------------------------------------------------------
# OB boundary clamp — unit tests (pure function, no LLM)
# ---------------------------------------------------------------------------


def _mock_ob(low, high, ob_type="bullish", mitigated=False):
    """Build a minimal H1 OB-like object."""
    return SimpleNamespace(low=low, high=high, type=ob_type, mitigated=mitigated)


def _mock_mso(m15_atr=10.0, h1_obs=None):
    """Build a minimal MSO exposing H1 order_blocks + M15 ATR.

    When ``h1_obs`` is None, constructs an empty list.
    """
    h1_obs = h1_obs or []
    return SimpleNamespace(
        timeframes={
            "M15": SimpleNamespace(atr_14=m15_atr),
            "H1": SimpleNamespace(order_blocks=h1_obs),
        },
    )


def _full_config(buffer_atr=0.5):
    """Build a minimal full config matching the keys m5_refinement reads."""
    return {
        "gate1": {"ob_retest_sl_min_buffer_atr": buffer_atr},
        "verification": {"ob_price_tolerance_pct": 0.002},
    }


class TestClampPureFunction:
    """Pure-function tests on ``clamp_m5_sl_to_ob_boundary`` — no LLM path."""

    def test_long_m5_sl_below_ob_boundary_passes_through(self):
        ob = _mock_ob(low=4000.0, high=4010.0)
        # LONG entry at 4005, pre-M5 SL 3990, M5 proposes 3995 which is BELOW
        # ob.low - buffer(2) = 3998 → no clamp.
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=3995.0, entry=4005.0, pre_m5_sl=3990.0,
            direction="LONG", matched_ob=ob, buffer=2.0,
        )
        assert result["clamped"] is False
        assert result["feasible"] is True
        assert result["clamped_sl"] == 3995.0
        assert result["ob_boundary"] == 4000.0
        assert result["applied_buffer"] == 2.0

    def test_long_m5_sl_inside_ob_clamped_to_boundary_minus_buffer(self):
        ob = _mock_ob(low=4000.0, high=4010.0)
        # M5 proposes 4005 (inside OB). Must clamp down to ob.low - buffer = 3998.
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4005.0, entry=4008.0, pre_m5_sl=3990.0,
            direction="LONG", matched_ob=ob, buffer=2.0,
        )
        assert result["clamped"] is True
        assert result["feasible"] is True
        assert result["clamped_sl"] == 3998.0  # 4000 - 2
        assert result["ob_boundary"] == 4000.0

    def test_short_m5_sl_above_ob_boundary_passes_through(self):
        ob = _mock_ob(low=4000.0, high=4010.0, ob_type="bearish")
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4015.0, entry=4005.0, pre_m5_sl=4020.0,
            direction="SHORT", matched_ob=ob, buffer=2.0,
        )
        assert result["clamped"] is False
        assert result["feasible"] is True
        assert result["clamped_sl"] == 4015.0

    def test_short_m5_sl_inside_ob_clamped_to_boundary_plus_buffer(self):
        ob = _mock_ob(low=4000.0, high=4010.0, ob_type="bearish")
        # M5 proposes 4007 (inside OB). Must clamp up to ob.high + buffer = 4012.
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4007.0, entry=4005.0, pre_m5_sl=4020.0,
            direction="SHORT", matched_ob=ob, buffer=2.0,
        )
        assert result["clamped"] is True
        assert result["feasible"] is True
        assert result["clamped_sl"] == 4012.0  # 4010 + 2
        assert result["ob_boundary"] == 4010.0

    def test_long_no_matched_ob_is_noop(self):
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=3995.0, entry=4000.0, pre_m5_sl=3980.0,
            direction="LONG", matched_ob=None, buffer=2.0,
        )
        assert result["clamped"] is False
        assert result["feasible"] is True
        assert result["clamped_sl"] == 3995.0

    def test_long_clamp_infeasible_when_target_at_or_below_pre_m5_sl(self):
        """If ob.low - buffer <= pre_m5_sl, clamp gives no tightening room."""
        ob = _mock_ob(low=4000.0, high=4010.0)
        # pre-M5 SL 3998 == target (4000 - 2). No tightening room.
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4005.0, entry=4008.0, pre_m5_sl=3998.0,
            direction="LONG", matched_ob=ob, buffer=2.0,
        )
        assert result["feasible"] is False
        assert result["clamped"] is False
        assert result["reason"] == "clamped_sl_not_tighter_than_pre_m5_sl"

    def test_long_clamp_infeasible_when_target_above_entry(self):
        """Degenerate: ob.low - buffer is above entry. Would produce an
        SL above entry for LONG — not a valid trade SL. Must fall back."""
        ob = _mock_ob(low=4010.0, high=4020.0)
        # entry 4005 below ob.low 4010, buffer 2 → target 4008 > entry.
        # Also need m5_sl inside OB to hit the clamp branch (not the
        # 'm5_sl < target' fast path). m5_sl=4015 inside OB, above entry.
        # But first guardrail would reject (m5_sl > entry) — the pure
        # clamp function does not enforce that; let's use m5_sl=4009
        # which is >= target so clamp fires.
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4009.0, entry=4005.0, pre_m5_sl=3990.0,
            direction="LONG", matched_ob=ob, buffer=2.0,
        )
        assert result["feasible"] is False
        assert result["reason"] == "ob_boundary_minus_buffer_above_entry"

    def test_short_clamp_infeasible_when_target_at_or_above_pre_m5_sl(self):
        ob = _mock_ob(low=4000.0, high=4010.0, ob_type="bearish")
        # target = 4012, pre-M5 SL = 4012 → infeasible
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4007.0, entry=4005.0, pre_m5_sl=4012.0,
            direction="SHORT", matched_ob=ob, buffer=2.0,
        )
        assert result["feasible"] is False
        assert result["clamped"] is False

    def test_zero_buffer_still_clamps_when_inside_ob(self):
        """With buffer=0, clamp to exactly ob.low for LONG (strictly tighter
        than M5 inside OB, but at the boundary)."""
        ob = _mock_ob(low=4000.0, high=4010.0)
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4005.0, entry=4008.0, pre_m5_sl=3990.0,
            direction="LONG", matched_ob=ob, buffer=0.0,
        )
        assert result["clamped"] is True
        assert result["clamped_sl"] == 4000.0

    def test_negative_buffer_coerced_to_zero(self):
        ob = _mock_ob(low=4000.0, high=4010.0)
        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=4005.0, entry=4008.0, pre_m5_sl=3990.0,
            direction="LONG", matched_ob=ob, buffer=-5.0,
        )
        assert result["applied_buffer"] == 0.0
        assert result["clamped_sl"] == 4000.0


# ---------------------------------------------------------------------------
# OB boundary clamp — integration tests via refine_entry_m5
# ---------------------------------------------------------------------------


class TestClampViaRefineEntry:
    """End-to-end clamp behavior through the full refine_entry_m5 flow."""

    def _make_config_with_full(self, sl_floor=10.0, buffer_atr=0.5,
                                 quality_gate=None, m15_atr_for_prompt=True):
        cfg = _m5_config(sl_floor=sl_floor, quality_gate=quality_gate)
        cfg["_full_config"] = _full_config(buffer_atr=buffer_atr)
        return cfg

    def test_m5_looser_sl_passes_through(self):
        """M5 proposes a LOOSER SL (further from entry than M15). Pre-existing
        guardrail rejects this with SL_OUT_OF_RANGE — clamp does not engage.

        Note: The task brief describes a future where LOOSER M5 SLs are allowed
        (no clamp needed). This test documents the *current* guardrail which
        this PR does not change. Flagged for follow-up.
        """
        analysis = _mock_analysis(direction="LONG", entry=4005.0, sl=3990.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 3985.0, "m5_sl_distance": 20.0,  # LOOSER than M15 SL
            "m5_structure": "bos", "reasoning": "Wider M5 structure.",
        }
        backend = _mock_llm_backend(response)
        cfg = self._make_config_with_full()
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)
        # Pre-existing guardrail fires: SL below M15 SL → SL_OUT_OF_RANGE.
        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "SL_OUT_OF_RANGE"

    def test_m5_tighter_sl_outside_ob_passes_through(self):
        """M5 proposes a tighter SL that is ALREADY below ob.low - buffer.
        Clamp should not engage; refinement applies as-is."""
        analysis = _mock_analysis(direction="LONG", entry=4005.0, sl=3990.0)
        candles = _mock_m5_candles(36)
        # ob.low=4000, buffer=0.5 * 5 ATR = 2.5, target=3997.5. M5 SL=3995 < target.
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 3995.0, "m5_sl_distance": 10.0,
            "m5_structure": "bos", "reasoning": "M5 swing below OB.",
        }
        backend = _mock_llm_backend(response)
        cfg = self._make_config_with_full(buffer_atr=0.5, sl_floor=0.0)
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)
        assert result["applied"] is True
        ov = result["overrides"]
        assert ov["stop_loss"] == 3995.0  # unchanged from M5 proposal
        assert ov["m5_ob_clamp_applied"] is False

    def test_m5_tighter_sl_inside_ob_clamped_long(self):
        """M5 proposes tighter SL INSIDE the OB → clamp to ob.low - buffer."""
        analysis = _mock_analysis(direction="LONG", entry=4008.0, sl=3990.0)
        candles = _mock_m5_candles(36)
        # M5 SL=4005 is inside OB [4000, 4010]. buffer=0.5*5=2.5, target=3997.5.
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 4005.0, "m5_sl_distance": 3.0,
            "m5_structure": "bos", "reasoning": "M5 swing inside OB.",
        }
        backend = _mock_llm_backend(response)
        # Disable ATR floor + $ floor so clamped value is not re-widened.
        cfg = self._make_config_with_full(buffer_atr=0.5, sl_floor=0.0)
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)
        assert result["applied"] is True
        ov = result["overrides"]
        # Clamped SL = ob.low - buffer = 4000 - 2.5 = 3997.5, rounded to 2dp.
        assert ov["stop_loss"] == 3997.50
        assert ov["m5_ob_clamp_applied"] is True
        assert ov["m5_ob_pre_clamp_sl"] == 4005.0
        assert ov["m5_ob_boundary"] == 4000.0
        assert ov["m5_ob_clamp_buffer"] == pytest.approx(2.5)

    def test_m5_tighter_sl_inside_ob_clamped_short(self):
        """SHORT: M5 proposes tighter SL INSIDE the OB → clamp to ob.high + buffer."""
        analysis = _mock_analysis(direction="SHORT", entry=4002.0, sl=4020.0)
        candles = _mock_m5_candles(36)
        # M5 SL=4007 is inside bearish OB [4005, 4010]. buffer=0.5*5=2.5, target=4012.5.
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 4007.0, "m5_sl_distance": 5.0,
            "m5_structure": "bos", "reasoning": "M5 swing inside bearish OB.",
        }
        backend = _mock_llm_backend(response)
        cfg = self._make_config_with_full(buffer_atr=0.5, sl_floor=0.0)
        ob = _mock_ob(low=4005.0, high=4010.0, ob_type="bearish")
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)
        assert result["applied"] is True
        ov = result["overrides"]
        # Clamped SL = ob.high + buffer = 4010 + 2.5 = 4012.5
        assert ov["stop_loss"] == 4012.50
        assert ov["m5_ob_clamp_applied"] is True
        assert ov["m5_ob_pre_clamp_sl"] == 4007.0
        assert ov["m5_ob_boundary"] == 4010.0

    def test_m5_geometrically_wrong_sl_rejected(self, caplog):
        """LONG with m5_sl > entry → rejected with WARNING. Pre-M5 (M15) SL
        preserved on caller side (refinement not applied)."""
        analysis = _mock_analysis(direction="LONG", entry=4005.0, sl=3990.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 4010.0, "m5_sl_distance": 5.0,  # ABOVE entry
            "m5_structure": "bos", "reasoning": "Bad SL above entry.",
        }
        backend = _mock_llm_backend(response)
        cfg = self._make_config_with_full()
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        with caplog.at_level(logging.WARNING,
                             logger="src.components.m5_refinement"):
            result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)

        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "SL_OUT_OF_RANGE"
        # WARNING emitted
        assert any("outside valid range" in rec.message
                   for rec in caplog.records
                   if rec.levelno == logging.WARNING)

    def test_clamp_infeasible_falls_back_to_m15_sl(self):
        """Clamp target <= pre-M5 SL → no tightening room → refinement skipped,
        CANDIDATE retains M15 SL (caller-side behavior)."""
        # pre-M5 SL at 3998, ob.low - buffer = 4000 - 2.5 = 3997.5 which is BELOW
        # pre_m5_sl. Actually 3997.5 < 3998, so target IS tighter? Let me flip:
        # Set pre-M5 SL to 3997 so target 3997.5 is WORSE → infeasible.
        analysis = _mock_analysis(direction="LONG", entry=4005.0, sl=3997.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 4002.0, "m5_sl_distance": 3.0,  # inside OB
            "m5_structure": "bos", "reasoning": "Inside OB.",
        }
        backend = _mock_llm_backend(response)
        cfg = self._make_config_with_full(buffer_atr=0.5, sl_floor=0.0)
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)
        # buffer 2.5, target 3997.5. pre_m5_sl 3997 < 3997.5 so target tighter.
        # Actually feasible. Need target >= pre_m5_sl to be infeasible.
        # Adjust pre_m5_sl to 3997.5 exactly:
        analysis2 = _mock_analysis(direction="LONG", entry=4005.0, sl=3997.5)
        result2 = refine_entry_m5(analysis2, candles, cfg, backend, mso=mso)
        assert result2["applied"] is False
        assert result2["m5_result"]["decision"] == "CLAMP_INFEASIBLE"
        assert result2["m5_result"]["clamp_reason"] == "clamped_sl_not_tighter_than_pre_m5_sl"

    def test_clamp_uses_configured_buffer(self):
        """Changing gate1.ob_retest_sl_min_buffer_atr changes the clamp target."""
        analysis = _mock_analysis(direction="LONG", entry=4008.0, sl=3990.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 4005.0, "m5_sl_distance": 3.0,
            "m5_structure": "bos", "reasoning": "Inside OB.",
        }
        backend = _mock_llm_backend(response)
        ob = _mock_ob(low=4000.0, high=4010.0)
        mso = _mock_mso(m15_atr=5.0, h1_obs=[ob])

        # buffer_atr=0.5 → buffer=2.5 → target=3997.5
        cfg_half = self._make_config_with_full(buffer_atr=0.5, sl_floor=0.0)
        r1 = refine_entry_m5(analysis, candles, cfg_half, backend, mso=mso)
        assert r1["applied"] is True
        assert r1["overrides"]["stop_loss"] == 3997.50

        # buffer_atr=1.0 → buffer=5.0 → target=3995.0
        cfg_full = self._make_config_with_full(buffer_atr=1.0, sl_floor=0.0)
        r2 = refine_entry_m5(analysis, candles, cfg_full, backend, mso=mso)
        assert r2["applied"] is True
        assert r2["overrides"]["stop_loss"] == 3995.00

    def test_clamp_no_mso_is_noop(self):
        """When mso=None (back-compat), clamp does nothing and refinement
        behaves exactly as before. Regression guard for legacy callers."""
        analysis = _mock_analysis(direction="LONG", entry=4000.0, sl=3960.0)
        candles = _mock_m5_candles(36)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": 3990.0, "m5_sl_distance": 10.0,
            "m5_structure": "bos", "reasoning": "Clean BOS.",
        }
        backend = _mock_llm_backend(response)
        cfg = _m5_config()  # no _full_config attached

        result = refine_entry_m5(analysis, candles, cfg, backend)  # mso omitted
        assert result["applied"] is True
        assert result["overrides"]["stop_loss"] == 3990.0
        assert result["overrides"]["m5_ob_clamp_applied"] is False


# ---------------------------------------------------------------------------
# Counterfactual regression: Thursday 2026-04-23 US30 NY 13:46
# ---------------------------------------------------------------------------


class TestThursdayUS30Counterfactual:
    """Regression anchor for the Thursday 2026-04-23 US30 NY 13:46 event.

    Original AI SL = 49046.27 (valid, below H1 OB low 49155.31).
    M5 refinement tightened to 49219.75 → INSIDE the OB zone.
    L2 re-check emitted REJECTED_L2_POST_M5, destroying a valid CANDIDATE.

    With the clamp, the M5-refined SL is clamped to ob.low - buffer so the
    L2 re-check PASSES and the CANDIDATE is preserved.

    Evidence: research/thursday_2026-04-23_analysis/US30_analysis.md §2.
    """

    # Inputs reconstructed from the incident
    OB_LOW = 49155.31
    OB_HIGH = 49205.20   # representative; exact value not critical for the clamp
    AI_ORIGINAL_SL = 49046.27
    M5_PROPOSED_SL = 49219.75   # inside [ob.low, ob.high]
    # Approximation of the US30 entry price just below OB (typical retest entry)
    ENTRY = 49230.00
    M15_ATR = 32.0              # representative US30 M15 ATR magnitude
    BUFFER_ATR = 0.5

    def test_clamp_keeps_sl_valid_and_below_ob_low_minus_buffer(self):
        """Pure-function counterfactual: clamp produces SL below ob.low - buffer."""
        ob = _mock_ob(low=self.OB_LOW, high=self.OB_HIGH)
        buffer = self.BUFFER_ATR * self.M15_ATR  # 16.0

        result = clamp_m5_sl_to_ob_boundary(
            m5_sl=self.M5_PROPOSED_SL,
            entry=self.ENTRY,
            pre_m5_sl=self.AI_ORIGINAL_SL,
            direction="LONG",
            matched_ob=ob,
            buffer=buffer,
        )
        assert result["feasible"] is True
        assert result["clamped"] is True
        # Clamped SL must be strictly below ob.low - buffer (valid LONG SL)
        expected = self.OB_LOW - buffer
        assert result["clamped_sl"] == pytest.approx(expected)
        assert result["clamped_sl"] <= self.OB_LOW - buffer
        assert result["clamped_sl"] < self.OB_LOW
        # Clamped SL tighter than original AI SL
        assert result["clamped_sl"] > self.AI_ORIGINAL_SL

    def test_refine_entry_m5_thursday_us30_13_46_counterfactual(self):
        """End-to-end: MSO + M5-proposed SL fed through refine_entry_m5.
        The CANDIDATE remains valid (refinement applied, SL below OB low)."""
        analysis = _mock_analysis(
            direction="LONG", entry=self.ENTRY, sl=self.AI_ORIGINAL_SL,
        )
        candles = _mock_m5_candles(36, base_price=self.ENTRY - 5)
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": self.M5_PROPOSED_SL,
            "m5_sl_distance": self.ENTRY - self.M5_PROPOSED_SL,
            "m5_structure": "bos",
            "reasoning": "Counterfactual replay of Thursday 2026-04-23 US30 NY 13:46.",
        }
        backend = _mock_llm_backend(response)

        cfg = _m5_config(sl_floor=0.0)   # disable floor so clamp value sticks
        cfg["_full_config"] = _full_config(buffer_atr=self.BUFFER_ATR)

        ob = _mock_ob(low=self.OB_LOW, high=self.OB_HIGH)
        mso = _mock_mso(m15_atr=self.M15_ATR, h1_obs=[ob])

        result = refine_entry_m5(analysis, candles, cfg, backend, mso=mso)

        assert result["applied"] is True, (
            "Thursday US30 counterfactual: refinement should apply "
            "(original AI SL was valid; clamp preserves that validity)"
        )
        ov = result["overrides"]
        assert ov["m5_ob_clamp_applied"] is True
        buffer = self.BUFFER_ATR * self.M15_ATR
        # Final SL must be below ob.low - buffer (would PASS sl_beyond_ob)
        assert ov["stop_loss"] <= self.OB_LOW - buffer + 0.01  # round tolerance
        assert ov["stop_loss"] < self.OB_LOW
        # AND tighter than the original AI SL (M5 still did something useful)
        assert ov["stop_loss"] > self.AI_ORIGINAL_SL


# ---------------------------------------------------------------------------
# WARN message precision — per-instrument price_format in SL_OUT_OF_RANGE warns
# ---------------------------------------------------------------------------


class TestSlOutOfRangeWarnPrecision:
    """Guards against cosmetic FX truncation in the SL_OUT_OF_RANGE WARN.

    Before the fix, `$%.2f` truncated 5dp FX prices (USDJPY 154.32145 →
    "$154.32", GBPUSD 1.27431 → "$1.27"). The fix resolves precision from
    `_full_config.prompt.price_format` matching the per-instrument config
    in agent_config.yaml (XAUUSD/US30 = .2f, USDJPY/GBPJPY = .3f,
    GBPUSD/EURUSD = .5f).
    """

    def _cfg(self, price_format: str) -> dict:
        cfg = _m5_config(sl_floor=0.0)
        cfg["_full_config"] = {
            "gate1": {"ob_retest_sl_min_buffer_atr": 0.5},
            "verification": {"ob_price_tolerance_pct": 0.002},
            "prompt": {"price_format": price_format},
        }
        return cfg

    def _run_and_capture_warn(self, entry, sl, bad_m5_sl, cfg, caplog,
                              direction="LONG"):
        analysis = _mock_analysis(direction=direction, entry=entry, sl=sl)
        # Build candles with at least one low (LONG) / high (SHORT) inside the
        # setup zone so the deterministic pre-check passes and execution reaches
        # the SL_OUT_OF_RANGE branch under test. (The shared `_mock_m5_candles`
        # helper uses XAUUSD-scale $1.5 increments which fall outside FX
        # zone widths.) The candle must also satisfy len >= 12 (NO_DATA gate).
        zone_low = sl if direction == "LONG" else entry
        zone_high = entry if direction == "LONG" else sl
        mid = (zone_low + zone_high) / 2.0
        in_zone_candle = _candle(low=mid, high=mid)
        candles = [in_zone_candle for _ in range(36)]
        response = {
            "decision": "REFINED", "m5_quality": "HIGH",
            "m5_sl": bad_m5_sl, "m5_sl_distance": abs(entry - bad_m5_sl),
            "m5_structure": "bos",
            "reasoning": "Forces SL_OUT_OF_RANGE path.",
        }
        backend = _mock_llm_backend(response)

        with caplog.at_level(logging.WARNING,
                             logger="src.components.m5_refinement"):
            result = refine_entry_m5(analysis, candles, cfg, backend, mso=None)

        assert result["applied"] is False
        assert result["m5_result"]["decision"] == "SL_OUT_OF_RANGE"
        warns = [rec.message for rec in caplog.records
                 if rec.levelno == logging.WARNING
                 and "outside valid range" in rec.message]
        assert len(warns) == 1, f"expected exactly 1 SL_OUT_OF_RANGE warn, got {warns}"
        return warns[0]

    def test_xauusd_warn_uses_2dp(self, caplog):
        """XAUUSD (price_format='.2f'): gold-style 2dp precision.

        Warn format: "M5 SL $<m5_sl> outside valid range [<lo>, <hi>]".
        For LONG, lo=M15 sl, hi=entry. The `$` sigil only prefixes m5_sl.
        """
        cfg = self._cfg(".2f")
        # LONG: bad_m5_sl >= entry triggers SL_OUT_OF_RANGE.
        msg = self._run_and_capture_warn(
            entry=2345.67, sl=2340.00, bad_m5_sl=2350.00, cfg=cfg, caplog=caplog,
        )
        assert "$2350.00" in msg   # m5_sl with $ prefix
        assert "[2340.00, 2345.67]" in msg   # [M15 sl, entry]
        # Ensure NOT truncated to integer and not widened to 3dp.
        assert "2345.670" not in msg
        assert "2350.000" not in msg

    def test_usdjpy_warn_uses_3dp(self, caplog):
        """USDJPY (price_format='.3f'): JPY-pair 3dp. Pre-fix showed 2dp ("$154.45").

        USDJPY quotes are stored with broker-side 3dp (e.g. 154.325);
        agent_config.yaml sets price_format='.3f'. The warn MUST preserve
        the 3rd decimal so operators can reconcile against MT5 logs.
        """
        cfg = self._cfg(".3f")
        # LONG: m5_sl >= entry.
        msg = self._run_and_capture_warn(
            entry=154.321, sl=154.100, bad_m5_sl=154.455, cfg=cfg, caplog=caplog,
        )
        assert "$154.455" in msg    # m5_sl with full 3dp precision
        assert "[154.100, 154.321]" in msg   # 3dp for entry + M15 sl
        # Would have failed pre-fix: "$154.45" truncates the 3rd decimal.
        assert "$154.45 " not in msg
        assert "$154.45," not in msg
        # Not widened beyond 3dp.
        assert "154.4550" not in msg

    def test_gbpusd_warn_uses_5dp(self, caplog):
        """GBPUSD (price_format='.5f'): 5dp FX precision.

        Pre-fix, GBPUSD 1.27431 truncated to "$1.27" — catastrophic for
        reconciliation (1.27 vs 1.27431 is a 431-pip difference in display).
        """
        cfg = self._cfg(".5f")
        # SHORT: m5_sl <= entry triggers SL_OUT_OF_RANGE (for SHORT valid
        # range is entry < m5_sl <= sl where sl > entry). Warn shows
        # [entry, sl] for SHORT.
        msg = self._run_and_capture_warn(
            entry=1.27431, sl=1.27900, bad_m5_sl=1.27200, cfg=cfg, caplog=caplog,
            direction="SHORT",
        )
        assert "$1.27200" in msg    # m5_sl with full 5dp precision
        assert "[1.27431, 1.27900]" in msg   # 5dp for entry + M15 sl
        # Would have failed pre-fix: "$1.27" truncates 3 significant digits.
        assert "$1.27 " not in msg
        assert "$1.27," not in msg
        # Not widened beyond 5dp.
        assert "1.272000" not in msg

    def test_missing_price_format_defaults_to_2dp(self, caplog):
        """Back-compat: when _full_config is missing or lacks prompt.price_format,
        warn falls back to 2dp — matches the pre-fix default."""
        # No _full_config at all → isinstance(None, dict) is False → fallback.
        cfg = _m5_config(sl_floor=0.0)
        # Omit _full_config entirely.
        msg = self._run_and_capture_warn(
            entry=2345.67, sl=2340.00, bad_m5_sl=2350.00, cfg=cfg, caplog=caplog,
        )
        assert "$2350.00" in msg   # 2dp default preserved (pre-fix behavior)
        assert "2350.000" not in msg
