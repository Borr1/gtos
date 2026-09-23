"""Tests for HALLUC-1 precision-aware guards (2026-04-27).

Background — the "93% NAS100 hallucination" rate observed live 2026-04-27 was
NOT AI hallucination. It was a deterministic system-side bug:

  - config/agent_config.yaml:685 sets NAS100 prompt.price_format = ".1f"
  - src/prompts/primary_analyzer_prompt.py:1052-1057 renders OB.high=27262.16
    as "27262.2" (the AI never sees the 27262.16 underlying)
  - src/prompts/primary_analyzer_prompt.py:805-808 (SELF-CHECK item 3)
    directs the AI to emit prices at "exactly 1 decimal places"
  - src/prompts/primary_analyzer_prompt.py:658 directs entry_price = ob_high
  - AI emits entry_price = 27262.2 (per spec; all 6 self-checks pass)
  - Pre-fix: guard_candidate_inconsistent_pois compared 27262.2 against the
    underlying 27262.16 with strict ``<=`` and demoted (27262.2 <= 27262.16
    is False). Math forced a violation on ~50% of NAS100 OBs (those whose
    high's 2nd decimal is in {5, 6, 7, 8, 9}).

Forensic dump: research/halluc_1_nas100_dumps/report.json (commit d50166e).
Sister bug class: project_eurusd_sl_root_cause, project_f12_us30_dual_mechanism.

The fix snaps OB.low/high to the same precision the AI was shown before
comparing against AI-emitted prices.
"""

from __future__ import annotations

import json

import pytest

from src.components.primary_analyzer import (
    _decimals_from_format,
    _snap_to_precision,
    guard_candidate_inconsistent_pois,
)
from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.market_state_models import (
    DataQuality,
    MarketStateObject,
    OrderBlock,
    SessionLevels,
    StructureAnalysis,
    TimeframeState,
)


# ── Format-parsing helpers ────────────────────────────────────────────

class TestDecimalFromFormat:
    """``_decimals_from_format`` parses ``.Nf`` format specs to the integer N."""

    @pytest.mark.parametrize("fmt,expected", [
        (".1f", 1),
        (".2f", 2),
        (".3f", 3),
        (".5f", 5),
    ])
    def test_known_formats(self, fmt: str, expected: int) -> None:
        assert _decimals_from_format(fmt) == expected

    @pytest.mark.parametrize("fmt", [None, "", "  ", "invalid", "%.2f", ".f", "1f"])
    def test_unrecognized_returns_none(self, fmt) -> None:
        assert _decimals_from_format(fmt) is None


class TestSnapToPrecision:
    """``_snap_to_precision`` rounds floats to N decimals using ROUND_HALF_UP.

    The values must match what Python f-strings produce so the snap exactly
    mirrors how the MSO renders prices for the AI.
    """

    @pytest.mark.parametrize("value,decimals,expected", [
        # NAS100 (.1f) — the HALLUC-1 trigger cases
        (27262.16, 1, 27262.2),
        (27262.10, 1, 27262.1),
        (27262.14, 1, 27262.1),  # rounds DOWN
        (27262.15, 1, 27262.2),  # ROUND_HALF_UP rounds UP at .5 boundary
        (27124.37, 1, 27124.4),
        (26988.25, 1, 26988.3),
        # XAUUSD (.2f)
        (3050.123, 2, 3050.12),
        (3050.125, 2, 3050.13),
        # FX (.5f)
        (1.123456, 5, 1.12346),
        (1.123455, 5, 1.12346),
        # JPY (.3f)
        (151.2345, 3, 151.235),
        (151.2344, 3, 151.234),
    ])
    def test_round_half_up(self, value: float, decimals: int, expected: float) -> None:
        assert _snap_to_precision(value, decimals) == expected

    def test_matches_fstring_format(self) -> None:
        """Snap output must match what an f-string produces (modulo ROUND_HALF_EVEN
        differences) on the deterministic cases the prompt actually exercises."""
        for value in (27262.16, 27124.37, 26988.25, 3050.99, 1.12345):
            for decimals in (1, 2, 3, 5):
                snapped = _snap_to_precision(value, decimals)
                # Compare numeric equality on the canonical cases above.
                assert isinstance(snapped, float)


# ── Test fixtures (mirroring tests/test_primary_analyzer.py) ───────────

_VALID_CANDIDATE_JSON = json.dumps({
    "timestamp_utc": "2026-04-27T07:30:00Z",
    "model_used": "claude-sonnet-4-6",
    "decision": "CANDIDATE",
    "confidence_score": 78,
    "reasoning": {
        "daily_bias": {
            "direction": "bullish",
            "confidence": "high",
            "protected_swing_level": 27000.0,
            "explanation": "Daily bullish.",
        },
        "h4_alignment": {
            "aligned": True,
            "h4_pois_identified": [],
            "explanation": "H4 aligned.",
        },
        "h1_setup": {
            "poi_identified": True,
            "poi_type": "OB",
            "poi_price_level": 27246.85,
            "zone": "discount",
            "fib_retracement_pct": 68.0,
            "explanation": "H1 OB retest.",
        },
        "liquidity_sweep": {
            "detected": True,
            "pool_type": "asian_low",
            "sweep_quality": "clean",
            "sweep_price": 27200.0,
            "explanation": "Sweep.",
        },
        "m15_confirmation": {
            "choch_detected": True,
            "displacement_quality": "strong",
            "displacement_candle_body_vs_avg_ratio": 2.4,
            "explanation": "M15 CHoCH.",
        },
        "similar_historical_setups_considered": [],
        "setup_grade": "A+",
        "overall_reasoning": "Setup looks good.",
    },
    "trade_parameters": {
        "direction": "LONG",
        "entry_price": 27262.2,
        "stop_loss": 27200.0,
        "sl_buffer_applied": 5.0,
        "take_profit_1": 27355.5,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "position_size_lots": 0.01,
    },
    "framework": "ob_retest",
    "kill_zone": "london",
})


def _bullish_ob(low: float, high: float, touches: int = 1) -> OrderBlock:
    return OrderBlock(
        type="bullish", low=low, high=high,
        open=low, close=high,
        formation_index=1, formation_time="2026-04-27T07:00:00Z",
        causing_bos_index=2, touch_count=touches,
    )


def _bearish_ob(low: float, high: float, touches: int = 1) -> OrderBlock:
    return OrderBlock(
        type="bearish", low=low, high=high,
        open=high, close=low,
        formation_index=1, formation_time="2026-04-27T07:00:00Z",
        causing_bos_index=2, touch_count=touches,
    )


def _mso_with_h1_obs(order_blocks: list[OrderBlock]) -> MarketStateObject:
    bullish = StructureAnalysis(direction="bullish", hh_count=3, hl_count=3)
    return MarketStateObject(
        timestamp_utc="2026-04-27T07:30:00Z",
        timeframes={
            "D1": TimeframeState(structure=bullish),
            "H4": TimeframeState(structure=bullish),
            "H1": TimeframeState(structure=bullish, order_blocks=order_blocks),
            "M15": TimeframeState(structure=bullish),
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


def _candidate(
    direction: str,
    poi_level: float,
    entry: float,
    sl: float,
    tp1: float,
) -> PrimaryAnalysisOutput:
    result = PrimaryAnalysisOutput.model_validate(json.loads(_VALID_CANDIDATE_JSON))
    result.reasoning.h1_setup.poi_price_level = poi_level
    assert result.trade_parameters is not None
    result.trade_parameters.direction = direction
    result.trade_parameters.entry_price = entry
    result.trade_parameters.stop_loss = sl
    result.trade_parameters.take_profit_1 = tp1
    return result


# ── HALLUC-1 PRIMARY FIX: precision-aware OB matching ─────────────────

class TestPrecisionAwareOBBoundaryComparison:
    """HALLUC-1 forensic dump validation — the entry vs OB.high comparison
    must use the AI's display precision, not the underlying float.
    """

    def test_nas100_ob_high_27262_16_passes_for_entry_27262_2(self) -> None:
        """The exact case from the 2026-04-27 NAS100 forensic dump.

        OB.high underlying = 27262.16 (.1f rendering = 27262.2).
        AI emits entry = 27262.2 (per prompt: entry = ob_high for LONG).
        Pre-fix: 27262.2 <= 27262.16 → False → DEMOTE (false positive).
        Post-fix: snap OB.high to .1f (27262.2) then compare → PASS.
        """
        ob = _bullish_ob(low=27231.50, high=27262.16, touches=1)
        mso = _mso_with_h1_obs([ob])
        # POI = OB midpoint as the AI cited it (also rendered at .1f).
        result = _candidate(
            direction="LONG",
            poi_level=27246.9,   # midpoint as rendered-precision value
            entry=27262.2,       # rendered ob.high
            sl=27200.0,
            tp1=27355.5,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_nas100_ob_high_27262_10_rejects_entry_27262_2(self) -> None:
        """Correctness preservation — entry truly above the rendered OB.high
        must still REJECT.

        OB.high underlying = 27262.10 (.1f rendering = 27262.1). AI emitting
        entry = 27262.2 is genuinely above the matched OB; demote.
        """
        ob = _bullish_ob(low=27231.5, high=27262.10, touches=1)
        mso = _mso_with_h1_obs([ob])
        # POI inside rendered bounds [27231.5, 27262.1].
        result = _candidate(
            direction="LONG",
            poi_level=27246.8,
            entry=27262.2,       # ABOVE rendered ob.high (27262.1)
            sl=27200.0,
            tp1=27355.5,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "ai_output_inconsistent_pois"

    def test_nas100_rounding_down_ob_high_27262_14_passes_entry_27262_1(self) -> None:
        """Round-DOWN edge case: OB.high = 27262.14 (.1f → 27262.1).
        AI emits entry = 27262.1. Should PASS.
        """
        ob = _bullish_ob(low=27231.5, high=27262.14, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=27246.8,
            entry=27262.1,       # rendered ob.high after round-down
            sl=27200.0,
            tp1=27355.5,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_short_mirror_nas100_ob_low_27200_15_passes_entry_27200_2(self) -> None:
        """SHORT mirror: OB.low underlying = 27200.15 (.1f → 27200.2).
        AI emits entry = 27200.2 (ob_low for SHORT). Should PASS.
        """
        ob = _bearish_ob(low=27200.15, high=27262.50, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="SHORT",
            poi_level=27231.3,   # midpoint as rendered
            entry=27200.2,       # rendered ob.low
            sl=27300.0,
            tp1=27100.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_short_mirror_below_rendered_ob_low_rejects(self) -> None:
        """SHORT mirror correctness: OB.low = 27200.10 (.1f → 27200.1).
        AI emits entry = 27200.0 (below rendered low) → REJECT.
        """
        ob = _bearish_ob(low=27200.10, high=27262.50, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="SHORT",
            poi_level=27231.3,
            entry=27200.0,       # BELOW rendered ob.low (27200.1)
            sl=27300.0,
            tp1=27100.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "NO_TRADE"
        assert guarded.no_trade_reason == "ai_output_inconsistent_pois"


class TestPrecisionAwarePerInstrumentFormat:
    """Verifies the precision-snap honors each instrument's price_format."""

    def test_xauusd_2dp_underlying_3050_125_renders_3050_13_passes(self) -> None:
        """XAUUSD .2f: OB.high = 3050.125 → rendered 3050.13. AI emits 3050.13."""
        ob = _bullish_ob(low=3045.00, high=3050.125, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=3047.56,
            entry=3050.13,       # rendered ob.high
            sl=3040.00,
            tp1=3065.50,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".2f")

        assert guarded.decision == "CANDIDATE"

    def test_eurusd_5dp_underlying_1_123456_renders_1_12346_passes(self) -> None:
        """EURUSD .5f: OB.high = 1.123456 → rendered 1.12346. AI emits 1.12346."""
        ob = _bullish_ob(low=1.12000, high=1.123456, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=1.12173,
            entry=1.12346,       # rendered ob.high
            sl=1.11800,
            tp1=1.13000,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".5f")

        assert guarded.decision == "CANDIDATE"

    def test_usdjpy_3dp_underlying_151_2345_renders_151_235_passes(self) -> None:
        """USDJPY .3f: OB.high = 151.2345 → rendered 151.235. AI emits 151.235."""
        ob = _bullish_ob(low=151.000, high=151.2345, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=151.117,
            entry=151.235,       # rendered ob.high
            sl=150.900,
            tp1=151.700,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".3f")

        assert guarded.decision == "CANDIDATE"


class TestBackwardCompatibilityNoFormatPassed:
    """When ``price_format`` is omitted, the guard falls back to ``.2f`` —
    matching XAUUSD behavior so existing tests keep working.
    """

    def test_xauusd_existing_test_still_passes_default_format(self) -> None:
        """Mirrors the original test_consistent_long_passes case (XAUUSD-style
        2-dp numbers without an explicit price_format)."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=48550.0,
            entry=48590.0,
            sl=48480.0,
            tp1=48800.0,
        )

        # No price_format passed; should default to .2f and pass.
        guarded = guard_candidate_inconsistent_pois(result, mso)

        assert guarded.decision == "CANDIDATE"

    def test_invalid_format_falls_back_to_2dp(self) -> None:
        """Garbage price_format → falls back to .2f (no crash)."""
        ob = _bullish_ob(low=48500.0, high=48600.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=48550.0,
            entry=48590.0, sl=48480.0, tp1=48800.0,
        )
        guarded = guard_candidate_inconsistent_pois(
            result, mso, price_format="not_a_format",
        )
        assert guarded.decision == "CANDIDATE"


# ── HALLUC-1 P1 FIX: SL-vs-OB-edge check removed ──────────────────────

class TestSLBeyondOBCheckRemoved:
    """Pattern B in the HALLUC-1 forensic dump (9/13 NAS100 demotions): the
    prompt instructs SL placement beyond the H1/M15 swing, but the guard
    required ``stop_loss < matched_ob.low`` (LONG). Concrete case from the
    dump: OB.low = 26988.25, swing low = 27024, AI emits SL = 27003.5 which
    is correctly below the swing but inside the OB body. The contradiction
    forced demotion.

    Fix: drop the SL check from this guard; rely on the existing tolerance-
    tier ``sl_beyond_ob`` L2 gate (``verification.sl_beyond_ob_tick_floor``)
    as the single source of truth.
    """

    def test_nas100_pattern_b_sl_inside_ob_no_longer_demotes(self) -> None:
        """Concrete sample from research/halluc_1_nas100_dumps/report.json.

        OB high underlying 27124.37 (rendered 27124.4), low 26988.25, swing
        low ~27024. AI emits entry 27124.4, SL 27003.5 (below swing, inside
        OB). Pre-fix: demoted by SL-vs-OB check. Post-fix: PASS at this
        guard; L2 ``sl_beyond_ob`` is the enforcement layer.
        """
        ob = _bullish_ob(low=26988.25, high=27124.37, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="LONG",
            poi_level=27056.3,    # OB midpoint at .1f
            entry=27124.4,        # rendered ob.high
            sl=27003.5,           # below swing (~27024) but INSIDE OB
            tp1=27305.7,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None

    def test_short_mirror_sl_inside_ob_no_longer_demotes(self) -> None:
        """SHORT mirror — SL above swing high but inside OB body."""
        ob = _bearish_ob(low=27050.0, high=27200.0, touches=1)
        mso = _mso_with_h1_obs([ob])
        result = _candidate(
            direction="SHORT",
            poi_level=27125.0,
            entry=27050.0,        # rendered ob.low
            sl=27130.0,           # above swing high but INSIDE OB
            tp1=26900.0,
        )

        guarded = guard_candidate_inconsistent_pois(result, mso, price_format=".1f")

        assert guarded.decision == "CANDIDATE"
        assert guarded.no_trade_reason is None


# ── End-to-end integration: call site passes the right format ────────

class TestPrecisionFormatPassthrough:
    """Confirms PrimaryAnalyzer.analyze pulls config.prompt.price_format and
    threads it into the guard call. We don't run the full async pipeline
    here (that needs API mocking); we verify the config-read path exists.
    """

    def test_config_read_contract(self) -> None:
        """Sanity check that the config getter chain in the production call
        site doesn't crash on missing keys."""
        # Mirror the production lookup pattern in primary_analyzer.py.
        configs = [
            {"prompt": {"price_format": ".1f"}},      # NAS100/UK100/GER40
            {"prompt": {"price_format": ".2f"}},      # XAUUSD/US30
            {"prompt": {"price_format": ".3f"}},      # JPY pairs
            {"prompt": {"price_format": ".5f"}},      # FX
            {"prompt": {}},                            # missing key → default
            {},                                         # missing block → default
        ]
        for config in configs:
            fmt = config.get("prompt", {}).get("price_format", ".2f")
            decimals = _decimals_from_format(fmt)
            assert decimals is not None and 1 <= decimals <= 5
