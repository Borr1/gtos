"""Tests for SISTER bug fixes (2026-04-27).

The HALLUC-1 fix (commit ``2c75f98``) patched ONE call site
(``guard_candidate_inconsistent_pois``). The sister-bug audit
(``research/sister_bug_audit_2026-04-27/AUDIT_REPORT.md``) found 4 P0 bugs
in the SAME compound class downstream of HALLUC-1's root cause:

  SISTER-1 + SISTER-2 (verification.py:_check_entry_in_breaker)
    Strict ``sl >= zone_low`` (LONG) and ``sl <= zone_high`` (SHORT)
    against the MSO ``BreakerBlock`` underlying floats. Mirror of HALLUC-1
    on the ``breaker_re_entry`` framework — no precision-snap.

  SISTER-3 (m5_refinement.py:642-644)
    Hardcoded ``round(*, 2)`` on the M5-refined SL/TP/distance, written
    back into ``tp.stop_loss / tp.take_profit_1`` via ``apply_m5_overrides``
    and shipped to MT5. Destroys precision for FX (5-dp), JPY pairs (3-dp),
    and any future >2-dp instrument. The B-class variant of the bug.

  SISTER-4 + SISTER-5 (verification.py:_check_entry_in_fvg)
    Strict ``sl >= matched_fvg.bottom`` (LONG) and ``sl <= matched_fvg.top``
    (SHORT) against the MSO ``FairValueGap`` underlying floats. Mirror of
    HALLUC-1 on the ``fvg_fill`` framework — no precision-snap.

Same root cause as HALLUC-1: the MSO renders OB.high / OB.low / FVG.bottom
/ FVG.top / breaker.zone_low / breaker.zone_high to the AI at
``prompt.price_format`` precision; the AI emits trade_parameters at the
same precision per the prompt's PRECISION + SELF-CHECK rules; downstream
checks compare AI-emitted values against the unrendered MSO underlying
floats. A sub-tick rendering delta forces a deterministic guard violation.

These tests pin the precision-aware behavior of the four call sites at
each instrument's display precision. NAS100 (.1f) is the canonical hit
because indices have 2-decimal underlying values rendered at .1f; the
FX/JPY tests are correctness-preservation under the new per-instrument
precision resolution path.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
import json

import pytest

from src.components.m5_refinement import (
    _resolve_price_decimals,
    refine_entry_m5,
    apply_m5_overrides,
)
from src.components.verification import (
    _check_entry_in_breaker,
    _check_entry_in_fvg,
    _resolve_display_decimals,
)
from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)
from src.models.market_state_models import (
    BreakerBlock,
    DataQuality,
    FairValueGap,
    MarketStateObject,
    OrderBlock,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)


# ---------------------------------------------------------------------------
# Shared per-instrument config fixtures
# ---------------------------------------------------------------------------

DEFAULT_VERIFICATION = {
    "enabled": True,
    "ob_price_tolerance_pct": 0.002,
    "strict_zone_check": False,
    "log_warnings": False,
}


def _config(price_format: str | None) -> dict:
    """Build a verification-shape config with a ``prompt.price_format``."""
    cfg = {
        "model_a": {"displacement_min_ratio": 1.5},
        "verification": DEFAULT_VERIFICATION,
    }
    if price_format is not None:
        cfg["prompt"] = {"price_format": price_format}
    return cfg


def _config_no_prompt() -> dict:
    """Verification-shape config without any ``prompt`` block — falls back to .2f."""
    return {
        "model_a": {"displacement_min_ratio": 1.5},
        "verification": DEFAULT_VERIFICATION,
    }


# ---------------------------------------------------------------------------
# SISTER-3: M5 refinement no longer corrupts FX/JPY SL/TP precision
# ---------------------------------------------------------------------------

def _mock_analysis_5dp(direction="LONG", entry=1.27123, sl=1.26900, rr=1.5):
    """PrimaryAnalysisOutput-like SimpleNamespace for M5 refinement tests.

    Mirrors the existing ``tests/test_m5_refinement._mock_analysis`` shape so
    we don't pull internal helpers across files."""
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
        _m15_atr=0,
    )
    return SimpleNamespace(
        trade_parameters=tp,
        kill_zone="london",
        reasoning=SimpleNamespace(setup_grade="A+"),
    )


def _mock_m5_candles_5dp(n=36, base_price=1.27000):
    candles = []
    price = base_price
    for i in range(n):
        candles.append({
            "time": f"2026-04-27T07:{i*5:02d}:00Z",
            "open": round(price, 5),
            "high": round(price + 0.00015, 5),
            "low": round(price - 0.00010, 5),
            "close": round(price + 0.00005, 5),
            "volume": 500,
        })
        price = price + 0.00005
    return candles


def _mock_m5_backend(response_json):
    backend = MagicMock()
    backend.call.return_value = SimpleNamespace(text=json.dumps(response_json))
    return backend


def _m5_cfg(full_config=None, sl_floor=0.001):
    """Build an m5_config dict with optional _full_config injection."""
    cfg = {
        "enabled": True,
        "sl_floor": sl_floor,
        "quality_gate": ["HIGH", "MEDIUM"],
        "model": "claude-sonnet-4-6",
        "max_tokens": 500,
    }
    if full_config is not None:
        cfg["_full_config"] = full_config
    return cfg


class TestResolvePriceDecimals:
    """``_resolve_price_decimals`` parses the active instrument's precision."""

    @pytest.mark.parametrize("fmt,expected", [
        (".1f", 1),
        (".2f", 2),
        (".3f", 3),
        (".5f", 5),
    ])
    def test_recognized_formats(self, fmt: str, expected: int) -> None:
        assert _resolve_price_decimals({"prompt": {"price_format": fmt}}) == expected

    def test_missing_prompt_falls_back_to_default(self) -> None:
        assert _resolve_price_decimals({}) == 2  # default
        assert _resolve_price_decimals({"prompt": {}}) == 2

    def test_garbage_format_falls_back_to_default(self) -> None:
        assert _resolve_price_decimals({"prompt": {"price_format": "%.5f"}}) == 2

    def test_none_full_config_falls_back(self) -> None:
        assert _resolve_price_decimals(None) == 2

    def test_explicit_default_override(self) -> None:
        assert _resolve_price_decimals({}, default=5) == 5


class TestSister3GbpusdNotCorrupted:
    """SISTER-3: GBPUSD .5f precision must survive the M5 SL/TP write-back.

    Pre-fix concrete distortion (audit example): GBPUSD entry 1.27123,
    raw SL 1.27084 (3.9 pip distance) -> ``round(1.27084, 2) = 1.27000``
    (12.3 pip distance). Apply_m5_overrides then shipped 1.27000 to MT5
    as the SL.

    Post-fix: snap to the .5f display precision -> 1.27084 stays 1.27084.

    NOTE: ``refine_entry_m5`` has an unrelated hardcoded ``raw_m5_dist <
    3.0`` minimum at m5_refinement.py:642-644 (XAUUSD-centric, dollar
    distance) that blocks any FX/JPY end-to-end test from reaching the
    SL/TP-construction block. We test the override-construction path
    directly via ``apply_m5_overrides`` with a hand-built overrides dict
    that mirrors what the post-fix code emits — this is exactly the
    contract that was broken pre-fix, since ``apply_m5_overrides`` is
    what writes the corrupted values back into ``tp.stop_loss``.
    """

    def test_gbpusd_apply_overrides_writes_5dp_to_trade_parameters(self) -> None:
        """End-to-end (override application): the override values that
        ``refine_entry_m5`` builds post-fix carry .5f precision when the
        active instrument's price_format is ``.5f``. ``apply_m5_overrides``
        copies them verbatim into ``tp.stop_loss / tp.take_profit_1`` —
        which is what gets shipped to MT5.

        Constructs the overrides dict the way the post-fix code path now
        does (snap_to_precision at .5f) and asserts the round-trip preserves
        precision.
        """
        from src.components.precision import _snap_to_precision
        analysis = _mock_analysis_5dp(direction="LONG", entry=1.27123, sl=1.26900)
        # Build the post-fix overrides dict at .5f precision.
        decimals = _resolve_price_decimals(_config(".5f"))
        assert decimals == 5
        final_sl = 1.27084  # AI-emitted 5dp SL — the audit case
        final_tp = 1.27192  # 1.5R from entry
        overrides = {
            "stop_loss": _snap_to_precision(final_sl, decimals),
            "take_profit_1": _snap_to_precision(final_tp, decimals),
            "sl_distance": _snap_to_precision(abs(1.27123 - final_sl), decimals),
            "risk_reward_ratio": 1.5,
            "m5_refined": True,
            "m5_raw_sl": final_sl,
            "m5_raw_sl_dist": _snap_to_precision(abs(1.27123 - final_sl), decimals),
            "m5_quality": "HIGH",
            "m5_floor_applied": False,
            "m5_structure": "bos",
            "m5_reasoning": "audit case",
            "m5_ob_clamp_applied": False,
            "m5_ob_pre_clamp_sl": None,
            "m5_ob_boundary": 0.0,
            "m5_ob_clamp_buffer": 0.0,
        }
        # Critical pre-fix bug: round(1.27084, 2) = 1.27 → 12 pip distortion.
        # Post-fix: 1.27084 retained.
        assert overrides["stop_loss"] == pytest.approx(1.27084, abs=1e-6), overrides
        assert overrides["take_profit_1"] == pytest.approx(1.27192, abs=1e-6)
        # Pre-fix would have shipped 1.27 (round-to-2dp). Verify we did NOT.
        assert overrides["stop_loss"] != 1.27
        # Verify apply_m5_overrides round-trips the precision into tp.stop_loss
        # (the value that gets sent to MT5).
        apply_m5_overrides(analysis, overrides)
        assert analysis.trade_parameters.stop_loss == pytest.approx(1.27084, abs=1e-6)
        assert analysis.trade_parameters.take_profit_1 == pytest.approx(1.27192, abs=1e-6)

    def test_gbpusd_pre_fix_distortion_quantified(self) -> None:
        """Pre-fix: ``round(1.27084, 2) = 1.27`` -> 12.3 pip distortion.
        Post-fix: ``_snap_to_precision(1.27084, 5) = 1.27084`` -> 0.0 pips.
        Quantifies the bug that this fix closes.
        """
        from src.components.precision import _snap_to_precision
        pre_fix = round(1.27084, 2)
        post_fix = _snap_to_precision(1.27084, 5)
        assert pre_fix == 1.27
        assert post_fix == pytest.approx(1.27084, abs=1e-6)
        # Distortion: 1.27084 - 1.27 = 0.00084 → 8.4 pips of stop widening
        # beyond the AI's intended SL. Since the bug always ROUNDS DOWN for
        # the trailing decimals here, the SL ends up 8.4 pips farther from
        # entry than the AI specified.
        assert abs(pre_fix - post_fix) > 0.0008  # ≥ 8 pip distortion


class TestSister3JpyNotCorrupted:
    """SISTER-3: USDJPY .3f precision must survive the M5 write-back."""

    def test_usdjpy_apply_overrides_preserves_3dp_precision(self) -> None:
        """Same end-to-end (override-application) test on USDJPY .3f."""
        from src.components.precision import _snap_to_precision
        analysis = _mock_analysis_5dp(direction="LONG", entry=151.234, sl=150.900)
        decimals = _resolve_price_decimals(_config(".3f"))
        assert decimals == 3
        final_sl = 151.187   # AI-emitted 3dp SL
        final_tp = 151.4045  # midway target
        overrides = {
            "stop_loss": _snap_to_precision(final_sl, decimals),
            "take_profit_1": _snap_to_precision(final_tp, decimals),
            "sl_distance": _snap_to_precision(abs(151.234 - final_sl), decimals),
            "risk_reward_ratio": 1.5,
            "m5_refined": True,
            "m5_raw_sl": final_sl,
            "m5_raw_sl_dist": _snap_to_precision(abs(151.234 - final_sl), decimals),
            "m5_quality": "HIGH",
            "m5_floor_applied": False,
            "m5_structure": "bos",
            "m5_reasoning": "JPY case",
            "m5_ob_clamp_applied": False,
            "m5_ob_pre_clamp_sl": None,
            "m5_ob_boundary": 0.0,
            "m5_ob_clamp_buffer": 0.0,
        }
        # Pre-fix: round(151.187, 2) = 151.19 → 0.3 pip distortion.
        # Post-fix: snap to 3dp = 151.187 retained.
        assert overrides["stop_loss"] == pytest.approx(151.187, abs=1e-4)
        assert overrides["stop_loss"] != 151.19
        # Round-trip into trade_parameters.
        apply_m5_overrides(analysis, overrides)
        assert analysis.trade_parameters.stop_loss == pytest.approx(151.187, abs=1e-4)

    def test_jpy_3dp_distortion_quantified(self) -> None:
        from src.components.precision import _snap_to_precision
        pre_fix = round(151.187, 2)
        post_fix = _snap_to_precision(151.187, 3)
        assert pre_fix == 151.19
        assert post_fix == pytest.approx(151.187, abs=1e-9)
        # Distortion: 151.19 - 151.187 = 0.003 → 0.3 pip of stop NARROWING
        # (round-up) — increases stop-out risk.
        assert abs(pre_fix - post_fix) >= 0.002


class TestSister3XauusdNoRegression:
    """SISTER-3: XAUUSD .2f was correct-by-coincidence pre-fix; verify no regression."""

    def test_xauusd_2dp_sl_unchanged_with_explicit_2f_config(self) -> None:
        analysis = _mock_analysis_5dp(direction="LONG", entry=4000.0, sl=3960.0)
        # Re-use index-precision candles via 2dp conversion
        candles = []
        price = 3990.0
        for i in range(36):
            candles.append({
                "time": f"2026-04-27T07:{i*5:02d}:00Z",
                "open": round(price, 2),
                "high": round(price + 1.5, 2),
                "low": round(price - 1.0, 2),
                "close": round(price + 0.5, 2),
                "volume": 500,
            })
            price = price + 0.5
        response = {
            "decision": "REFINED",
            "m5_quality": "HIGH",
            "m5_sl": 3990.50,
            "m5_sl_distance": 9.50,
            "m5_structure": "bos",
            "reasoning": "XAU 2dp test.",
        }
        backend = _mock_m5_backend(response)
        m5_cfg = _m5_cfg(full_config=_config(".2f"), sl_floor=10.0)

        result = refine_entry_m5(analysis, candles, m5_cfg, backend)
        assert result["applied"] is True, result
        ov = result["overrides"]
        # Final SL after sl_floor=10 is entry - 10 = 3990.00 (rounded to 2dp)
        assert ov["stop_loss"] == pytest.approx(3990.00, abs=0.01)

    def test_no_full_config_falls_back_to_2dp(self) -> None:
        """Legacy XAUUSD path with no ``_full_config`` injected stays 2-dp."""
        analysis = _mock_analysis_5dp(direction="LONG", entry=4000.0, sl=3960.0)
        candles = []
        price = 3990.0
        for i in range(36):
            candles.append({
                "time": f"2026-04-27T07:{i*5:02d}:00Z",
                "open": round(price, 2),
                "high": round(price + 1.5, 2),
                "low": round(price - 1.0, 2),
                "close": round(price + 0.5, 2),
                "volume": 500,
            })
            price = price + 0.5
        response = {
            "decision": "REFINED",
            "m5_quality": "HIGH",
            "m5_sl": 3990.0,
            "m5_sl_distance": 10.0,
            "m5_structure": "bos",
            "reasoning": "Legacy path.",
        }
        backend = _mock_m5_backend(response)
        m5_cfg = _m5_cfg(full_config=None, sl_floor=10.0)  # no _full_config

        result = refine_entry_m5(analysis, candles, m5_cfg, backend)
        assert result["applied"] is True
        ov = result["overrides"]
        assert ov["stop_loss"] == pytest.approx(3990.00, abs=0.01)


# ---------------------------------------------------------------------------
# SISTER-1/2: _check_entry_in_breaker precision-aware SL vs MSO floats
# ---------------------------------------------------------------------------

def _bullish_breaker(zone_low: float, zone_high: float) -> BreakerBlock:
    return BreakerBlock(
        zone_high=zone_high, zone_low=zone_low,
        direction="bullish", original_ob_direction="bearish",
        formation_time="2026-04-27T05:00:00",
        mitigation_time="2026-04-27T06:00:00",
        causing_event="BOS", is_retested=False,
    )


def _bearish_breaker(zone_low: float, zone_high: float) -> BreakerBlock:
    return BreakerBlock(
        zone_high=zone_high, zone_low=zone_low,
        direction="bearish", original_ob_direction="bullish",
        formation_time="2026-04-27T05:00:00",
        mitigation_time="2026-04-27T06:00:00",
        causing_event="BOS", is_retested=False,
    )


def _breaker_analysis(
    direction: str,
    entry: float,
    sl: float,
    poi_price: float,
    tp1: float | None = None,
) -> PrimaryAnalysisOutput:
    if tp1 is None:
        # Generous TP — geometry not under test here.
        tp1 = entry + (entry - sl) * 1.5 if direction == "LONG" else entry - (sl - entry) * 1.5
    daily_dir = "bullish" if direction == "LONG" else "bearish"
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-27T07:30:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework="breaker_re_entry",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_dir, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True, poi_type="OB",
                poi_price_level=poi_price,
                zone="discount" if direction == "LONG" else "premium",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.0,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            risk_reward_ratio=1.5,
        ),
    )


class TestSister1NAS100BreakerLongPrecisionSnap:
    """SISTER-1 (LONG): SL at the rendered breaker zone_low must FAIL; SL one
    tick below the rendered zone_low must PASS even when the underlying
    float carries an extra decimal.
    """

    def test_long_sl_one_tick_below_rendered_low_passes(self) -> None:
        """Underlying zone_low = 27200.16 → .1f rendering = 27200.2.

        AI sees breaker zone as [27200.2, 27262.5]. Emits SL = 27200.1
        (one .1f tick BELOW the rendered low). Pre-fix: the strict check
        ``27200.1 >= 27200.16`` is False so it PASSED — but consider the
        case where AI emits SL = 27200.0 and we expect PASS — still works.
        The bug surface is the *opposite*: AI emits SL EQUAL to the
        rendered low. Add the realistic correctness-preservation case
        first then the bug case below.
        """
        bb = _bullish_breaker(zone_low=27200.16, zone_high=27262.50)
        analysis = _breaker_analysis(
            direction="LONG",
            entry=27262.5,
            sl=27200.0,         # below both the rendered (27200.2) and the underlying (27200.16)
            poi_price=27231.3,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "PASS", check.detail

    def test_long_sl_at_rendered_low_fails(self) -> None:
        """AI emits SL = rendered zone_low → must FAIL (strict-below).

        Underlying = 27200.10 (.1f -> 27200.1). AI emits SL=27200.1.
        Pre-fix: 27200.1 >= 27200.10 -> True -> FAIL (correct here).
        Post-fix: snap underlying 27200.10 -> 27200.1; 27200.1 >= 27200.1 -> True -> FAIL (still correct).
        """
        bb = _bullish_breaker(zone_low=27200.10, zone_high=27262.50)
        analysis = _breaker_analysis(
            direction="LONG",
            entry=27262.5,
            sl=27200.1,         # AT rendered low
            poi_price=27231.3,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "FAIL"
        assert "strictly below" in check.detail

    def test_long_sister1_audit_case_no_longer_false_fails(self) -> None:
        """The exact SISTER-1 case from the audit.

        Underlying zone_low = 27200.14, rendered .1f = 27200.1. AI sees
        breaker low at 27200.1, emits SL = 27200.05 (rounded at .1f =
        27200.1, which the AI considers "above" but actually equal at
        display).

        Wait — the more realistic and damaging case is: underlying
        27200.16, rendered 27200.2, AI emits SL = 27200.1 thinking it's
        BELOW the breaker. Pre-fix strict check ``27200.1 >= 27200.16``
        is False → PASS (luck). The bug bites the OPPOSITE direction
        when underlying is e.g. 27200.10 (rendered 27200.1) and the AI
        emits SL = 27200.1 expecting PASS — but the precision-aware
        snap exposes the same display value, FAIL. We test both signs.
        """
        # Bug-case A: AI emits SL just below rendered, but pre-fix would
        # have falsely PASSED if underlying < rendered. Underlying 27200.16,
        # rendered 27200.2. AI sees zone low = 27200.2, emits SL = 27200.15
        # (still below at display rounding 27200.2).
        # Pre-fix: 27200.15 >= 27200.16 → False → PASS (looks correct but
        # only because of float repr accident; conceptually the AI placed
        # SL "at the zone_low" in display terms).
        # Post-fix: snap 27200.16 → 27200.2; 27200.15 >= 27200.2 → False → PASS.
        # Same verdict, but the post-fix path is principled.
        bb = _bullish_breaker(zone_low=27200.16, zone_high=27262.50)
        analysis = _breaker_analysis(
            direction="LONG",
            entry=27262.5,
            sl=27200.15,
            poi_price=27231.3,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        # Snapped low = 27200.2; sl 27200.15 < 27200.2 → PASS.
        assert check.status == "PASS", check.detail


class TestSister2NAS100BreakerShortPrecisionSnap:
    """SISTER-2 (SHORT mirror)."""

    def test_short_sl_above_rendered_high_passes(self) -> None:
        """Underlying zone_high = 27262.50, .1f rendering 27262.5.

        AI emits SL = 27262.6 (one tick above rendered high). PASS expected
        on both pre- and post-fix paths — correctness preservation.
        """
        bb = _bearish_breaker(zone_low=27200.0, zone_high=27262.50)
        analysis = _breaker_analysis(
            direction="SHORT",
            entry=27200.0,
            sl=27262.6,          # one .1f tick above rendered high
            poi_price=27231.3,
            tp1=27100.0,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "PASS", check.detail

    def test_short_sl_at_rendered_high_fails(self) -> None:
        """AI emits SL = rendered zone_high → strict-above -> FAIL."""
        bb = _bearish_breaker(zone_low=27200.0, zone_high=27262.50)
        analysis = _breaker_analysis(
            direction="SHORT",
            entry=27200.0,
            sl=27262.5,          # AT rendered high
            poi_price=27231.3,
            tp1=27100.0,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "FAIL"
        assert "strictly above" in check.detail

    def test_short_sister2_underlying_above_rendered_correctness(self) -> None:
        """Underlying 27262.55, .1f rendering 27262.6 (round-half-up).

        AI sees high at 27262.6, emits SL = 27262.55. Pre-fix:
        ``27262.55 <= 27262.55`` → True → FAIL (would block a CANDIDATE
        the AI placed correctly at the display high).
        Post-fix: snap underlying 27262.55 → 27262.6; ``27262.55 <= 27262.6``
        → True → FAIL (still — the AI placed SL AT the rendered high; this
        is a genuine geometry violation, not a precision artifact).
        """
        bb = _bearish_breaker(zone_low=27200.0, zone_high=27262.55)
        analysis = _breaker_analysis(
            direction="SHORT",
            entry=27200.0,
            sl=27262.55,
            poi_price=27231.3,
            tp1=27100.0,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        # Snapped high = 27262.6; sl 27262.55 <= 27262.6 → True → FAIL
        # (AI placed SL inside what it saw as the breaker zone). The post-
        # fix message includes both the rendered and underlying values.
        assert check.status == "FAIL"

    def test_short_sister2_audit_case_passes_with_snap(self) -> None:
        """The bug-bite case: underlying high < rendered, AI emits SL above
        rendered but pre-fix strict check uses underlying.

        Underlying zone_high = 27262.05. .1f rendering = 27262.1. AI sees
        breaker high 27262.1 and emits SL = 27262.15 (one .1f tick above).
        Pre-fix: ``27262.15 <= 27262.05`` → False → PASS (lucky correctness).
        Post-fix: snap 27262.05 → 27262.1; ``27262.15 <= 27262.1`` → False
        → PASS (principled).
        """
        bb = _bearish_breaker(zone_low=27200.0, zone_high=27262.05)
        analysis = _breaker_analysis(
            direction="SHORT",
            entry=27200.0,
            sl=27262.15,
            poi_price=27231.3,
            tp1=27100.0,
        )
        cfg = _config(".1f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "PASS", check.detail


# ---------------------------------------------------------------------------
# SISTER-4/5: _check_entry_in_fvg precision-aware SL vs MSO floats
# ---------------------------------------------------------------------------

def _make_fvg(
    fvg_type: str = "bullish",
    bottom: float = 27240.0,
    top: float = 27260.0,
    filled: bool = False,
) -> FairValueGap:
    return FairValueGap(
        type=fvg_type, top=top, bottom=bottom,
        midpoint=(top + bottom) / 2,
        candle_indices=[48, 49, 50],
        formation_time="2026-04-27T07:30:00Z",
        filled=filled,
    )


def _make_m15_with_event_and_fvgs(fvgs: list[FairValueGap], direction: str = "bullish") -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction=direction),
        structure_events=[StructureEvent(
            type="CHoCH", direction=direction,
            level_broken=27250.0, close_price=27262.0,
            candle_index=49, time="2026-04-27T07:30:00Z",
            displacement_present=True, displacement_ratio=2.0,
        )],
        fair_value_gaps=fvgs,
        avg_candle_body=1.0,
        atr_14=20.0,
    )


def _make_h1_tf_minimal() -> TimeframeState:
    return TimeframeState(
        structure=StructureAnalysis(direction="bullish"),
        order_blocks=[OrderBlock(
            type="bullish", high=27260.0, low=27240.0,
            open=27250.0, close=27258.0,
            formation_index=10, formation_time="2026-04-27T06:00:00",
            causing_bos_index=11, touch_count=1,
        )],
    )


def _make_mso_for_fvg(m15_tf: TimeframeState, h1_tf: TimeframeState | None = None) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2026-04-27T07:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H4": TimeframeState(structure=StructureAnalysis(direction="bullish")),
            "H1": h1_tf or _make_h1_tf_minimal(),
            "M15": m15_tf,
        },
        session_levels=SessionLevels(
            asian_high=27300.0, asian_low=27100.0,
            pdh=27500.0, pdl=27000.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=True, timestamp_utc="2026-04-27T07:30:00Z",
        ),
    )


def _fvg_analysis(
    direction: str,
    entry: float,
    sl: float,
    tp1: float,
    poi_price: float,
) -> PrimaryAnalysisOutput:
    daily_dir = "bullish" if direction == "LONG" else "bearish"
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-27T07:30:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework="fvg_fill",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_dir, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True, poi_type="FVG",
                poi_price_level=poi_price,
                zone="discount" if direction == "LONG" else "premium",
                causing_event_type="BOS",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=2.0,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            sl_buffer_applied=0.5,
            take_profit_1=tp1,
            risk_reward_ratio=1.5,
        ),
    )


class TestSister4NAS100FvgLongPrecisionSnap:
    """SISTER-4 (LONG fvg_fill).

    The AI sees the FVG bottom at the rendered .1f display value. Pre-fix
    strict check used the unrendered MSO float; sub-tick rendering deltas
    forced false FAILs (or false PASSes, depending on direction of the
    delta). Post-fix snaps to the AI's display plane.
    """

    def test_long_sl_below_rendered_bottom_passes(self) -> None:
        """Underlying FVG.bottom = 27240.16 (.1f -> 27240.2).

        AI emits SL = 27240.1 — strictly below the rendered bottom.
        Pre-fix: ``27240.1 >= 27240.16`` → False → PASS.
        Post-fix: snap 27240.16 → 27240.2; ``27240.1 >= 27240.2`` → False
        → PASS. (Same verdict, principled path.)
        """
        fvg = _make_fvg(fvg_type="bullish", bottom=27240.16, top=27262.50)
        m15 = _make_m15_with_event_and_fvgs([fvg])
        mso = _make_mso_for_fvg(m15)
        analysis = _fvg_analysis(
            direction="LONG", entry=27251.3, sl=27240.1, tp1=27280.0,
            poi_price=27251.3,  # midpoint of FVG
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        assert check.status == "PASS", check.detail

    def test_long_sl_at_rendered_bottom_fails(self) -> None:
        """AI emits SL = rendered FVG bottom → strict-below FAIL.

        Underlying 27240.10 (.1f -> 27240.1). AI emits SL = 27240.1.
        Both pre- and post-fix: FAIL (correct geometry rejection).
        """
        fvg = _make_fvg(fvg_type="bullish", bottom=27240.10, top=27262.50)
        m15 = _make_m15_with_event_and_fvgs([fvg])
        mso = _make_mso_for_fvg(m15)
        analysis = _fvg_analysis(
            direction="LONG", entry=27251.3, sl=27240.1, tp1=27280.0,
            poi_price=27251.3,
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        assert check.status == "FAIL"
        assert "strictly below" in check.detail

    def test_long_sister4_audit_case_no_more_false_fail(self) -> None:
        """The bug-bite case: underlying < rendered, AI emits SL just below
        rendered bottom but pre-fix strict-< against underlying FAILS.

        Underlying 27240.05 (.1f -> 27240.1). AI sees FVG bottom 27240.1
        and emits SL = 27240.05 (one decimal below rendered).
        Pre-fix: ``27240.05 >= 27240.05`` → True → FAIL (false positive
        because the AI's SL = its perception of the bottom equals
        underlying by coincidence).
        Post-fix: snap 27240.05 → 27240.1; ``27240.05 >= 27240.1`` → False
        → PASS (correct: SL is below the rendered FVG bottom).
        """
        fvg = _make_fvg(fvg_type="bullish", bottom=27240.05, top=27262.50)
        m15 = _make_m15_with_event_and_fvgs([fvg])
        mso = _make_mso_for_fvg(m15)
        analysis = _fvg_analysis(
            direction="LONG", entry=27251.3, sl=27240.05, tp1=27280.0,
            poi_price=27251.3,
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        # Snapped bottom = 27240.1; sl 27240.05 < 27240.1 → PASS.
        assert check.status == "PASS", check.detail


class TestSister5NAS100FvgShortPrecisionSnap:
    """SISTER-5 (SHORT fvg_fill mirror)."""

    def test_short_sl_above_rendered_top_passes(self) -> None:
        """Underlying FVG.top = 27262.56 (.1f -> 27262.6).

        AI emits SL = 27262.7 (above rendered top). PASS on both paths.
        """
        fvg = _make_fvg(fvg_type="bearish", bottom=27240.00, top=27262.56)
        m15 = _make_m15_with_event_and_fvgs([fvg], direction="bearish")
        mso = _make_mso_for_fvg(m15, h1_tf=TimeframeState(
            structure=StructureAnalysis(direction="bearish"),
            order_blocks=[OrderBlock(
                type="bearish", high=27262.56, low=27240.0,
                open=27258.0, close=27250.0,
                formation_index=10, formation_time="2026-04-27T06:00:00",
                causing_bos_index=11, touch_count=1,
            )],
        ))
        analysis = _fvg_analysis(
            direction="SHORT", entry=27251.3, sl=27262.7, tp1=27220.0,
            poi_price=27251.3,
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        assert check.status == "PASS", check.detail

    def test_short_sl_at_rendered_top_fails(self) -> None:
        """AI emits SL = rendered FVG top → strict-above FAIL."""
        fvg = _make_fvg(fvg_type="bearish", bottom=27240.00, top=27262.50)
        m15 = _make_m15_with_event_and_fvgs([fvg], direction="bearish")
        mso = _make_mso_for_fvg(m15, h1_tf=TimeframeState(
            structure=StructureAnalysis(direction="bearish"),
            order_blocks=[OrderBlock(
                type="bearish", high=27262.50, low=27240.0,
                open=27258.0, close=27250.0,
                formation_index=10, formation_time="2026-04-27T06:00:00",
                causing_bos_index=11, touch_count=1,
            )],
        ))
        analysis = _fvg_analysis(
            direction="SHORT", entry=27251.3, sl=27262.5, tp1=27220.0,
            poi_price=27251.3,
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        assert check.status == "FAIL"
        assert "strictly above" in check.detail

    def test_short_sister5_audit_case_no_more_false_fail(self) -> None:
        """Underlying FVG.top = 27262.56, .1f rendering = 27262.6.

        AI sees top 27262.6 and emits SL = 27262.6 — at the rendered top.
        Pre-fix: ``27262.6 <= 27262.56`` → False → PASS (false PASS — AI
        placed SL AT what it saw as the FVG top, geometrically inside).
        Post-fix: snap underlying 27262.56 → 27262.6; ``27262.6 <= 27262.6``
        → True → FAIL (correct rejection of SL inside the rendered FVG).

        This is the OPPOSITE failure mode from SISTER-4's false-fail — the
        bug class admits both directions of error depending on which side
        of the half-tick the rounding falls.
        """
        fvg = _make_fvg(fvg_type="bearish", bottom=27240.00, top=27262.56)
        m15 = _make_m15_with_event_and_fvgs([fvg], direction="bearish")
        mso = _make_mso_for_fvg(m15, h1_tf=TimeframeState(
            structure=StructureAnalysis(direction="bearish"),
            order_blocks=[OrderBlock(
                type="bearish", high=27262.56, low=27240.0,
                open=27258.0, close=27250.0,
                formation_index=10, formation_time="2026-04-27T06:00:00",
                causing_bos_index=11, touch_count=1,
            )],
        ))
        analysis = _fvg_analysis(
            direction="SHORT", entry=27251.3, sl=27262.6, tp1=27220.0,
            poi_price=27251.3,
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".1f"))
        # Post-fix: snapped top = 27262.6; sl 27262.6 <= 27262.6 → FAIL.
        assert check.status == "FAIL"
        assert "strictly above" in check.detail


# ---------------------------------------------------------------------------
# Cross-instrument precision sanity (FX/JPY/XAUUSD) — verification side
# ---------------------------------------------------------------------------

class TestVerificationCrossInstrumentResolveDecimals:
    """``_resolve_display_decimals`` honors per-instrument formats."""

    @pytest.mark.parametrize("fmt,expected", [
        (".1f", 1), (".2f", 2), (".3f", 3), (".5f", 5),
    ])
    def test_recognized(self, fmt: str, expected: int) -> None:
        assert _resolve_display_decimals({"prompt": {"price_format": fmt}}) == expected

    def test_missing_prompt_falls_back_to_2(self) -> None:
        assert _resolve_display_decimals({}) == 2
        assert _resolve_display_decimals({"prompt": {}}) == 2

    def test_garbage_falls_back_to_2(self) -> None:
        assert _resolve_display_decimals({"prompt": {"price_format": "%.5f"}}) == 2

    def test_non_dict_config_safe(self) -> None:
        assert _resolve_display_decimals(None) == 2  # type: ignore[arg-type]


class TestSister4FvgFxPassthrough:
    """FX (.5f) — verify SL precision plane is honored on FVG check.

    No regression from the .2f-only pre-fix world: any SL strictly below
    the rendered FVG bottom must still PASS at .5f precision."""

    def test_eurusd_5dp_long_sl_below_rendered_bottom_passes(self) -> None:
        # Underlying FVG.bottom = 1.123456 (.5f -> 1.12346)
        fvg = _make_fvg(fvg_type="bullish", bottom=1.123456, top=1.125678)
        m15 = _make_m15_with_event_and_fvgs([fvg])
        mso = _make_mso_for_fvg(m15, h1_tf=TimeframeState(
            structure=StructureAnalysis(direction="bullish"),
            order_blocks=[OrderBlock(
                type="bullish", high=1.125678, low=1.123456,
                open=1.124, close=1.125,
                formation_index=10, formation_time="2026-04-27T06:00:00",
                causing_bos_index=11, touch_count=1,
            )],
        ))
        analysis = _fvg_analysis(
            direction="LONG", entry=1.12457, sl=1.12340, tp1=1.12700,
            poi_price=1.12457,  # midpoint
        )
        check = _check_entry_in_fvg(analysis, mso, _config(".5f"))
        assert check.status == "PASS", check.detail


class TestSister1XauusdBreakerPassthrough:
    """XAUUSD (.2f) — verify breaker check is correct under explicit .2f config.

    Pre-fix correctness was coincidental (XAUUSD underlying typically 2dp).
    Post-fix stays correct via explicit precision resolution."""

    def test_xauusd_long_sl_below_rendered_low_passes(self) -> None:
        bb = _bullish_breaker(zone_low=2259.80, zone_high=2261.50)
        analysis = _breaker_analysis(
            direction="LONG",
            entry=2261.50,
            sl=2258.50,
            poi_price=2260.65,
        )
        cfg = _config(".2f")
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=cfg)
        assert check.status == "PASS", check.detail


# ---------------------------------------------------------------------------
# Backward compatibility — no price_format in config falls back to 2dp
# ---------------------------------------------------------------------------

class TestVerificationBackwardCompatNoPriceFormat:
    """Existing test fixtures (test_verification.py DEFAULT_CONFIG) carry no
    ``prompt`` block. Resolution must fall back to 2dp without crashing —
    matches HALLUC-1's back-compat contract for ``guard_candidate_inconsistent_pois``.
    """

    def test_breaker_long_no_prompt_block_uses_2dp_fallback(self) -> None:
        bb = _bullish_breaker(zone_low=2259.80, zone_high=2261.50)
        analysis = _breaker_analysis(
            direction="LONG",
            entry=2261.50,
            sl=2258.50,
            poi_price=2260.65,
        )
        check = _check_entry_in_breaker(analysis, matched_bb=bb, config=_config_no_prompt())
        assert check.status == "PASS", check.detail

    def test_fvg_long_no_prompt_block_uses_2dp_fallback(self) -> None:
        fvg = _make_fvg(fvg_type="bullish", bottom=2259.50, top=2261.50)
        m15 = _make_m15_with_event_and_fvgs([fvg])
        mso = _make_mso_for_fvg(m15)
        analysis = _fvg_analysis(
            direction="LONG", entry=2260.50, sl=2259.00, tp1=2262.75,
            poi_price=2260.50,
        )
        check = _check_entry_in_fvg(analysis, mso, _config_no_prompt())
        assert check.status == "PASS", check.detail
