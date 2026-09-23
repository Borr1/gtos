"""ADR-006 — per-instrument synthetic E2E tests for the SL geometry fix.

These tests build a tight-FX-style synthetic ``MarketStateObject`` with
exactly one matched H1 OB, plus an AI-style ``PrimaryAnalysisOutput`` with
varying SL geometry, and run them through ``verify_candidate``. They exist
to confirm that:

1. Tight-FX (5dp) SL placed 1-tick beyond OB → PASS under per-instrument
   8-tick floor (no quantization rejection).
2. With strict-< rollback (``sl_beyond_ob_tick_floor: 0``), the same row
   still PASSES when SL is strictly below.
3. Boundary case: SL == OB.low → FAIL with the new message format ("does
   not clear ... by floor"), distinct from the legacy "NOT below" string.

The tests cover a representative tight-FX instrument (EURUSD, 5dp), GBPUSD
(another 5dp pair), USDJPY (3dp bridge case), UK100 (1dp index, broad
scale), plus XAUUSD (2dp baseline regression).

Coverage target per ADR-006 §C: every instrument with sl_beyond_ob mass +
active live (XAUUSD, USDJPY, US30, GBPJPY) — UK100 and EURUSD added for
the tight-FX class because they are the canonical bug-class repro.
"""

from __future__ import annotations

import pytest

from src.components.verification import verify_candidate
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
    DataQuality,
    MarketStateObject,
    OrderBlock,
    SessionLevels,
    StructureAnalysis,
    StructureEvent,
    TimeframeState,
)


# ---------------------------------------------------------------------------
# Per-instrument fixture matrix
# ---------------------------------------------------------------------------

INSTRUMENT_FIXTURES = {
    "EURUSD": {
        "tick": 0.00001,
        "ob_low": 1.19000,
        "ob_high": 1.19100,
        "entry": 1.19010,
        "tp1_long": 1.19200,
        "atr": 0.0010,
        "floor_ticks": 8,
        "ob_atr_mult": 0.50,
        "min_ticks": 8,
        "price_format": ".5f",
    },
    "GBPUSD": {
        "tick": 0.00001,
        "ob_low": 1.30000,
        "ob_high": 1.30100,
        "entry": 1.30010,
        "tp1_long": 1.30200,
        "atr": 0.0010,
        "floor_ticks": 8,
        "ob_atr_mult": 0.50,
        "min_ticks": 8,
        "price_format": ".5f",
    },
    "USDJPY": {
        "tick": 0.001,
        "ob_low": 150.500,
        "ob_high": 150.800,
        "entry": 150.520,
        "tp1_long": 151.000,
        "atr": 0.300,
        "floor_ticks": 5,
        "ob_atr_mult": 0.30,
        "min_ticks": 5,
        "price_format": ".3f",
    },
    "UK100": {
        "tick": 0.10,
        "ob_low": 8000.0,
        "ob_high": 8005.0,
        "entry": 8001.0,
        "tp1_long": 8015.0,
        "atr": 5.0,
        "floor_ticks": 1,
        "ob_atr_mult": 0.25,
        "min_ticks": 5,
        "price_format": ".1f",
    },
    "XAUUSD": {
        "tick": 0.01,
        "ob_low": 2300.20,
        "ob_high": 2302.00,
        "entry": 2300.50,
        "tp1_long": 2305.00,
        "atr": 4.0,
        "floor_ticks": 1,
        "ob_atr_mult": 0.25,
        "min_ticks": 5,
        "price_format": ".2f",
    },
}


def _build_config(fixture: dict, *, floor_override: int | None = None) -> dict:
    """Build the merged config that ``verify_candidate`` would receive in
    production for the given instrument fixture."""
    floor = floor_override if floor_override is not None else fixture["floor_ticks"]
    return {
        "verification": {
            "enabled": True,
            "ob_price_tolerance_pct": 0.002,
            "sl_beyond_ob_tick_floor": floor,
            "sl_beyond_ob_tolerance_enabled": True,
        },
        "market": {
            "symbol": "EURUSD",  # placeholder; tests do not consult this
            "tick_size": fixture["tick"],
        },
        "risk": {
            "sl_buffer_atr_multiplier": fixture["ob_atr_mult"],
            "sl_buffer_breaker_atr_multiplier": 0.5,
            "sl_buffer_min_ticks": fixture["min_ticks"],
        },
        "prompt": {"price_format": fixture["price_format"]},
        "model_a": {
            "enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
        },
    }


def _build_mso(fixture: dict, direction: str = "LONG") -> MarketStateObject:
    """Build a synthetic MSO with one unmitigated H1 OB matching fixture.

    Pattern mirrors ``tests/test_verification.py::_make_mso`` so the
    pydantic schema is satisfied without surprising the L2 path.
    """
    structure_dir = "bullish" if direction == "LONG" else "bearish"
    ob = OrderBlock(
        type=structure_dir,
        low=fixture["ob_low"],
        high=fixture["ob_high"],
        open=fixture["ob_low"],
        close=fixture["ob_high"],
        formation_index=10,
        formation_time="2026-04-27T08:00:00+00:00",
        causing_bos_index=11,
        mitigated=False,
        causing_event_type="BOS",
        touch_count=1,
    )
    bos_event = StructureEvent(
        type="BOS",
        direction=structure_dir,
        level_broken=fixture["ob_high"] + fixture["tick"] * 5,
        close_price=fixture["ob_high"] + fixture["tick"] * 6,
        candle_index=11,
        time="2026-04-27T07:00:00+00:00",
        displacement_present=True,
        displacement_ratio=2.5,
    )

    h1 = TimeframeState(
        structure=StructureAnalysis(direction=structure_dir),
        structure_events=[bos_event],
        order_blocks=[ob],
        avg_candle_body=fixture["atr"] / 2,
        atr_14=fixture["atr"],
    )
    # M15: include the same BOS event so M15 CHoCH check passes (it scans
    # H1 events from MSO via _check_m15_choch).
    m15 = TimeframeState(
        structure=StructureAnalysis(direction=structure_dir),
        structure_events=[bos_event],
        avg_candle_body=fixture["atr"] / 8,
        atr_14=fixture["atr"] / 4,
    )
    h4 = TimeframeState(
        structure=StructureAnalysis(direction=structure_dir),
        avg_candle_body=fixture["atr"],
        atr_14=fixture["atr"] * 2,
    )
    d1 = TimeframeState(
        structure=StructureAnalysis(direction=structure_dir),
        avg_candle_body=fixture["atr"] * 2,
        atr_14=fixture["atr"] * 4,
    )

    return MarketStateObject(
        timestamp_utc="2026-04-27T08:00:00+00:00",
        timeframes={"M15": m15, "H1": h1, "H4": h4, "D1": d1},
        session_levels=SessionLevels(
            asian_high=fixture["ob_high"] + fixture["tick"] * 100,
            asian_low=fixture["ob_low"] - fixture["tick"] * 100,
            pdh=fixture["ob_high"] + fixture["tick"] * 200,
            pdl=fixture["ob_low"] - fixture["tick"] * 200,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True,
            spread_normal=True,
            mt5_connected=True,
            timestamp_utc="2026-04-27T08:00:00+00:00",
        ),
    )


def _build_pa(fixture: dict, sl: float, *, direction: str = "LONG") -> PrimaryAnalysisOutput:
    """Build a CANDIDATE analysis with the OB-matching POI and the given SL."""
    if direction == "LONG":
        # Entry is OB high (top of demand zone for retest), TP1 is fixture's tp1_long.
        entry = fixture["ob_high"]
        tp1 = fixture["tp1_long"]
        poi = (fixture["ob_low"] + fixture["ob_high"]) / 2
    else:
        entry = fixture["ob_low"]
        # Mirror SHORT TP geometry from entry
        tp1 = entry - 5 * fixture["tick"]
        poi = (fixture["ob_low"] + fixture["ob_high"]) / 2

    rr = abs(tp1 - entry) / max(abs(entry - sl), fixture["tick"])

    return PrimaryAnalysisOutput(
        timestamp_utc="2026-04-27T08:00:00+00:00",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework="ob_retest",
        kill_zone="ny",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(
                direction="bullish" if direction == "LONG" else "bearish",
                confidence="high",
            ),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type="OB",
                poi_price_level=poi,
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
            risk_reward_ratio=rr,
        ),
    )


def _sl_check(checks):
    """Pull the sl_beyond_ob VerificationCheck out of the result list."""
    return next(c for c in checks if c.name == "sl_beyond_ob")


# ---------------------------------------------------------------------------
# E2E case A — SL exactly floor_ticks below OB.low → PASS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("instrument", list(INSTRUMENT_FIXTURES.keys()))
def test_sl_floor_clearance_passes(instrument):
    """SL placed exactly floor_ticks below OB.low → sl_beyond_ob PASS."""
    fix = INSTRUMENT_FIXTURES[instrument]
    config = _build_config(fix)
    sl = fix["ob_low"] - fix["tick"] * fix["floor_ticks"]

    mso = _build_mso(fix)
    pa = _build_pa(fix, sl=sl)
    result = verify_candidate(pa, mso, config)

    sl_chk = _sl_check(result.checks)
    assert sl_chk.status == "PASS", (
        f"{instrument}: SL {sl} should clear OB low "
        f"{fix['ob_low']} by {fix['floor_ticks']} ticks. detail={sl_chk.detail}"
    )


# ---------------------------------------------------------------------------
# E2E case B — Strict-< rollback still passes when SL is strictly below
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("instrument", list(INSTRUMENT_FIXTURES.keys()))
def test_strict_rollback_still_passes_for_clear_sl(instrument):
    """With ``sl_beyond_ob_tick_floor: 0`` (strict-< rollback), an SL
    that is two ticks below OB.low (well clear of any 1-ULP edge) MUST
    still PASS — the rollback flag should not over-restrict.
    """
    fix = INSTRUMENT_FIXTURES[instrument]
    config = _build_config(fix, floor_override=0)
    sl = fix["ob_low"] - fix["tick"] * 2

    mso = _build_mso(fix)
    pa = _build_pa(fix, sl=sl)
    result = verify_candidate(pa, mso, config)

    sl_chk = _sl_check(result.checks)
    assert sl_chk.status == "PASS", (
        f"{instrument}: floor=0 + SL clear of OB.low should PASS. "
        f"detail={sl_chk.detail}"
    )


# ---------------------------------------------------------------------------
# E2E case C — SL exactly at OB.low → FAIL with new message format
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("instrument", list(INSTRUMENT_FIXTURES.keys()))
def test_sl_at_boundary_fails_with_new_message(instrument):
    """SL == OB.low → FAIL. Message format MUST be the ADR-006 string
    ("does not clear ... by floor"), not the legacy "NOT below" string.
    """
    fix = INSTRUMENT_FIXTURES[instrument]
    config = _build_config(fix)

    mso = _build_mso(fix)
    pa = _build_pa(fix, sl=fix["ob_low"])
    result = verify_candidate(pa, mso, config)

    sl_chk = _sl_check(result.checks)
    assert sl_chk.status == "FAIL"
    assert "does not clear" in sl_chk.detail, (
        f"{instrument}: expected new ADR-006 reason format, got: {sl_chk.detail}"
    )
    # Legacy phrasing must not appear
    assert "NOT below" not in sl_chk.detail
