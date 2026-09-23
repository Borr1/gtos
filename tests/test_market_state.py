"""Tests for Component 2 — Market State Analyzer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components.market_state import (
    _count_touches,
    avg_candle_body,
    calculate_atr,
    calculate_premium_discount,
    compute_clv,
    compute_bvc,
    compute_market_state,
    compute_session_atr,
    detect_structure_breaks,
    detect_sweeps,
    detect_swings,
    identify_fvgs,
    identify_order_blocks,
    identify_structure,
)
from src.models.market_state_models import OrderBlock
from src.models.market_state_models import (
    LiquidityPool,
    MarketStateObject,
    StructureEvent,
    Swing,
    StructureAnalysis,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def bullish_candles():
    return json.loads((FIXTURES / "sample_bullish_candles.json").read_text())


@pytest.fixture
def bearish_candles():
    return json.loads((FIXTURES / "sample_bearish_candles.json").read_text())


@pytest.fixture
def ranging_candles():
    return json.loads((FIXTURES / "sample_ranging_candles.json").read_text())


@pytest.fixture
def sweep_candles():
    return json.loads((FIXTURES / "sample_sweep_candles.json").read_text())


# -----------------------------------------------------------------------
# detect_swings
# -----------------------------------------------------------------------

class TestDetectSwings:

    def test_detect_swings_bullish(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        highs = [s for s in swings if s.type == "high"]
        lows = [s for s in swings if s.type == "low"]
        assert len(highs) >= 4
        assert len(lows) >= 4
        # Verify sorted by index
        assert all(swings[i].index <= swings[i + 1].index for i in range(len(swings) - 1))

    def test_detect_swings_bearish(self, bearish_candles):
        swings = detect_swings(bearish_candles, min_bars=2)
        highs = [s for s in swings if s.type == "high"]
        lows = [s for s in swings if s.type == "low"]
        assert len(highs) >= 3
        assert len(lows) >= 3

    def test_swing_high_is_local_maximum(self, bullish_candles):
        """Every swing high must be strictly > its min_bars neighbors on each side."""
        swings = detect_swings(bullish_candles, min_bars=2)
        for s in swings:
            if s.type == "high":
                for j in range(1, 3):
                    assert s.price > bullish_candles[s.index - j]["high"]
                    assert s.price > bullish_candles[s.index + j]["high"]

    def test_swing_low_is_local_minimum(self, bullish_candles):
        """Every swing low must be strictly < its min_bars neighbors on each side."""
        swings = detect_swings(bullish_candles, min_bars=2)
        for s in swings:
            if s.type == "low":
                for j in range(1, 3):
                    assert s.price < bullish_candles[s.index - j]["low"]
                    assert s.price < bullish_candles[s.index + j]["low"]

    def test_empty_candles(self):
        assert detect_swings([], min_bars=2) == []

    def test_too_few_candles(self):
        candles = [{"high": 10, "low": 5, "open": 7, "close": 8, "time": "t"}] * 4
        assert detect_swings(candles, min_bars=2) == []


# -----------------------------------------------------------------------
# identify_structure
# -----------------------------------------------------------------------

class TestIdentifyStructure:

    def test_identify_structure_bullish(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "bullish"
        assert struct.hh_count >= 3
        assert struct.hl_count >= 3
        assert struct.ll_count == 0

    def test_identify_structure_bearish(self, bearish_candles):
        swings = detect_swings(bearish_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "bearish"
        assert struct.lh_count >= 2
        assert struct.ll_count >= 2
        assert struct.hh_count == 0

    def test_identify_structure_transitional(self, ranging_candles):
        swings = detect_swings(ranging_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "transitional"
        # Should have a mix of HH and LH
        assert struct.hh_count >= 1
        assert struct.lh_count >= 1

    def test_insufficient_data(self):
        """Fewer than 2 highs or 2 lows → insufficient_data."""
        swings = [Swing(index=5, type="high", price=100.0, time="t")]
        struct = identify_structure(swings)
        assert struct.direction == "insufficient_data"

    def test_protected_swing_bullish(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "bullish"
        # Protected swing is the last HL (i.e. the last swing low)
        lows = [s for s in swings if s.type == "low"]
        assert struct.protected_swing is not None
        assert struct.protected_swing.index == lows[-1].index
        assert struct.protected_swing.type == "low"

    def test_protected_swing_bearish(self, bearish_candles):
        swings = detect_swings(bearish_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "bearish"
        # Protected swing is the last LH (i.e. the last swing high)
        highs = [s for s in swings if s.type == "high"]
        assert struct.protected_swing is not None
        assert struct.protected_swing.index == highs[-1].index
        assert struct.protected_swing.type == "high"

    def test_swing_sequence_labels(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        assert len(struct.swing_sequence) == len(swings)
        # All later highs should be HH in bullish
        high_labels = [l for l in struct.swing_sequence if l in ("HH", "LH", "H", "EH")]
        assert "HH" in high_labels


# -----------------------------------------------------------------------
# detect_structure_breaks (BOS / CHoCH)
# -----------------------------------------------------------------------

class TestStructureBreaks:

    def test_detect_bos(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        bos_events = [e for e in events if e.type == "BOS"]
        assert len(bos_events) >= 1
        # All bullish BOS in a bullish structure
        for ev in bos_events:
            assert ev.direction == "bullish"
            # The close must be above the broken level
            assert ev.close_price > ev.level_broken

    def test_bos_has_displacement_info(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        bos_events = [e for e in events if e.type == "BOS"]
        # At least one BOS should have displacement
        assert any(e.displacement_present for e in bos_events)
        for ev in bos_events:
            assert ev.displacement_ratio >= 0

    def test_detect_choch(self, bullish_candles):
        """In bullish structure, a CHoCH fires when close < protected swing (HL).

        This will only happen if there are candles after the protected swing
        that close below it.  Our bullish fixture is purely bullish, so CHoCH
        should NOT fire (no breakdown).  We test CHoCH explicitly with a
        constructed scenario below.
        """
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        choch_events = [e for e in events if e.type == "CHoCH"]
        # Pure bullish fixture — no candle after the last HL breaks below it
        assert len(choch_events) == 0

    def test_choch_detection_synthetic(self):
        """Construct a bullish structure that ends with a CHoCH breakdown."""
        # A simple 15-candle sequence: up, HL, up(HH), then break below HL
        candles = [
            {"time": "t0",  "open": 100, "close": 102, "high": 103, "low": 99},
            {"time": "t1",  "open": 102, "close": 104, "high": 105, "low": 101},
            {"time": "t2",  "open": 104, "close": 106, "high": 107, "low": 103},
            # swing high idx=2
            {"time": "t3",  "open": 106, "close": 108, "high": 110, "low": 105},
            # swing high idx=3
            {"time": "t4",  "open": 108, "close": 106, "high": 109, "low": 105},
            {"time": "t5",  "open": 106, "close": 104, "high": 107, "low": 103},
            {"time": "t6",  "open": 104, "close": 102, "high": 105, "low": 101},
            # swing low idx=6 (potential protected HL)
            {"time": "t7",  "open": 102, "close": 103, "high": 104, "low": 100},
            {"time": "t8",  "open": 103, "close": 106, "high": 107, "low": 102},
            {"time": "t9",  "open": 106, "close": 109, "high": 111, "low": 105},
            # swing high idx=9 (HH)
            {"time": "t10", "open": 109, "close": 112, "high": 114, "low": 108},
            {"time": "t11", "open": 112, "close": 108, "high": 113, "low": 107},
            {"time": "t12", "open": 108, "close": 105, "high": 109, "low": 104},
            # swing low idx=12 (HL — protected swing)
            {"time": "t13", "open": 105, "close": 106, "high": 107, "low": 103},
            {"time": "t14", "open": 106, "close": 98,  "high": 107, "low": 97},
            # CHoCH: close=98 < protected HL price
        ]
        swings = detect_swings(candles, min_bars=1)
        struct = identify_structure(swings)
        if struct.direction != "bullish":
            # Force bullish structure for this test
            lows = [s for s in swings if s.type == "low"]
            struct = StructureAnalysis(
                direction="bullish",
                protected_swing=lows[-1] if lows else None,
                hh_count=2, hl_count=2, lh_count=0, ll_count=0,
            )
        events = detect_structure_breaks(candles, swings, struct)
        choch_events = [e for e in events if e.type == "CHoCH"]
        assert len(choch_events) >= 1
        assert choch_events[0].direction == "bearish"

    def test_no_events_on_insufficient_data(self):
        candles = [{"time": "t", "open": 10, "close": 11, "high": 12, "low": 9}]
        struct = StructureAnalysis(direction="insufficient_data")
        events = detect_structure_breaks(candles, [], struct)
        assert events == []


# -----------------------------------------------------------------------
# identify_order_blocks
# -----------------------------------------------------------------------

class TestOrderBlocks:

    def test_identify_order_blocks(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        obs = identify_order_blocks(bullish_candles, events)
        assert len(obs) >= 1
        for ob in obs:
            assert ob.type == "bullish"
            # The OB candle should be bearish (close < open)
            c = bullish_candles[ob.formation_index]
            assert c["close"] < c["open"]
            assert ob.causing_bos_index > ob.formation_index

    def test_ob_mitigated_check(self, bullish_candles):
        """At least one OB should remain unmitigated if price hasn't returned."""
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        obs = identify_order_blocks(bullish_candles, events)
        # Check that mitigated flag is set correctly
        for ob in obs:
            if ob.mitigated:
                # Some candle after the BOS went back to the OB high
                found = any(
                    bullish_candles[k]["low"] <= ob.high
                    for k in range(ob.causing_bos_index + 1, len(bullish_candles))
                )
                assert found
            else:
                found = any(
                    bullish_candles[k]["low"] <= ob.high
                    for k in range(ob.causing_bos_index + 1, len(bullish_candles))
                )
                assert not found

    def test_no_obs_without_bos(self):
        """No BOS events → no order blocks."""
        candles = [{"time": "t", "open": 10, "close": 11, "high": 12, "low": 9}] * 5
        obs = identify_order_blocks(candles, [])
        assert obs == []

    def test_choch_produces_order_block(self):
        """A CHoCH event should also produce an order block."""
        candles = [
            {"time": "t0", "open": 100, "close": 102, "high": 103, "low": 99},
            {"time": "t1", "open": 102, "close": 104, "high": 105, "low": 101},
            {"time": "t2", "open": 104, "close": 102, "high": 105, "low": 101},  # bearish candle
            {"time": "t3", "open": 102, "close": 106, "high": 107, "low": 101},
            {"time": "t4", "open": 106, "close": 108, "high": 109, "low": 105},  # CHoCH candle
            {"time": "t5", "open": 108, "close": 110, "high": 111, "low": 107},
        ]
        choch = StructureEvent(
            type="CHoCH", direction="bullish",
            level_broken=105.0, close_price=108.0,
            candle_index=4, time="t4",
            displacement_present=True, displacement_ratio=2.0,
        )
        obs = identify_order_blocks(candles, [choch])
        assert len(obs) == 1
        assert obs[0].type == "bullish"
        assert obs[0].causing_event_type == "CHoCH"
        assert obs[0].formation_index == 2  # the bearish candle before the break

    def test_causing_event_type_bos(self, bullish_candles):
        """BOS-based OBs should have causing_event_type='BOS'."""
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        events = detect_structure_breaks(bullish_candles, swings, struct)
        obs = identify_order_blocks(bullish_candles, events)
        for ob in obs:
            if any(e.type == "BOS" and e.candle_index == ob.causing_bos_index for e in events):
                assert ob.causing_event_type == "BOS"

    def test_deduplication_choch_then_bos(self):
        """If CHoCH and BOS produce OB from the same formation candle, only one OB kept."""
        candles = [
            {"time": "t0", "open": 100, "close": 102, "high": 103, "low": 99},
            {"time": "t1", "open": 102, "close": 100, "high": 103, "low": 99},  # bearish — OB candidate
            {"time": "t2", "open": 100, "close": 104, "high": 105, "low": 99},  # CHoCH break
            {"time": "t3", "open": 104, "close": 106, "high": 107, "low": 103},  # BOS break
            {"time": "t4", "open": 106, "close": 108, "high": 109, "low": 105},
        ]
        choch = StructureEvent(
            type="CHoCH", direction="bullish",
            level_broken=103.0, close_price=104.0,
            candle_index=2, time="t2",
        )
        bos = StructureEvent(
            type="BOS", direction="bullish",
            level_broken=105.0, close_price=106.0,
            candle_index=3, time="t3",
        )
        obs = identify_order_blocks(candles, [choch, bos])
        # Both events would find candle idx=1 as the OB, but dedup keeps only one
        assert len(obs) == 1
        assert obs[0].causing_event_type == "CHoCH"  # CHoCH came first


# -----------------------------------------------------------------------
# _count_touches — multi-touch tracking for OB zone freshness gate
# -----------------------------------------------------------------------

class TestCountTouches:
    """Touch = candle AFTER formation with candle.high >= OB.low AND
    candle.low <= OB.high. Formation candle is EXCLUDED."""

    def _ob(self, formation_index=0, high=110.0, low=100.0):
        return OrderBlock(
            type="bullish", high=high, low=low,
            open=(high + low) / 2, close=(high + low) / 2,
            formation_index=formation_index, formation_time="t",
            causing_bos_index=formation_index + 1, mitigated=False,
        )

    def test_touch_count_zero_candles_no_touches(self):
        """Empty candle list after formation -> 0 touches."""
        ob = self._ob(formation_index=0)
        # Only the formation candle present; nothing after it
        candles = [{"time": "t0", "open": 105, "close": 105, "high": 110, "low": 100}]
        assert _count_touches(ob, candles) == 0

    def test_touch_count_zero_candles_empty_list(self):
        """Edge: truly empty candle list -> 0 touches."""
        ob = self._ob(formation_index=0)
        assert _count_touches(ob, []) == 0

    def test_touch_count_increments_on_range_overlap(self):
        """Each candle whose range overlaps the zone counts as +1."""
        ob = self._ob(formation_index=0, high=110.0, low=100.0)
        candles = [
            {"time": "t0", "open": 105, "close": 105, "high": 110, "low": 100},  # formation (excluded)
            {"time": "t1", "open": 120, "close": 121, "high": 122, "low": 118},  # above zone — no overlap
            {"time": "t2", "open": 115, "close": 112, "high": 115, "low": 109},  # low=109 < high=110 — overlap
            {"time": "t3", "open": 108, "close": 107, "high": 109, "low": 102},  # fully inside — overlap
            {"time": "t4", "open": 95,  "close": 94,  "high": 99,  "low": 90},   # below zone — no overlap
            {"time": "t5", "open": 99,  "close": 101, "high": 101, "low": 98},   # straddles low — overlap
        ]
        # Expected overlaps at indices 2, 3, 5 — three touches
        assert _count_touches(ob, candles) == 3

    def test_touch_count_excludes_formation_candle(self):
        """The formation candle itself is NOT counted even though it overlaps."""
        ob = self._ob(formation_index=1, high=110.0, low=100.0)
        candles = [
            {"time": "t0", "open": 90, "close": 91, "high": 92, "low": 89},     # before formation, ignored
            {"time": "t1", "open": 105, "close": 103, "high": 108, "low": 102}, # formation candle (inside zone) — MUST be excluded
            {"time": "t2", "open": 95, "close": 94, "high": 96, "low": 92},     # below zone — no overlap
        ]
        # If formation was counted -> 1. Expect 0.
        assert _count_touches(ob, candles) == 0

    def test_touch_count_wick_touch_counts(self):
        """A candle that touches the zone only with its wick (body outside) still counts."""
        ob = self._ob(formation_index=0, high=110.0, low=100.0)
        candles = [
            {"time": "t0", "open": 105, "close": 105, "high": 110, "low": 100},  # formation (excluded)
            # Body fully above zone, but wick low=100.5 dips into the zone.
            {"time": "t1", "open": 115, "close": 118, "high": 119, "low": 100.5},
            # Body fully below zone, but wick high=100.0 just touches OB low (inclusive boundary).
            {"time": "t2", "open": 90, "close": 92, "high": 100.0, "low": 85},
        ]
        assert _count_touches(ob, candles) == 2

    def test_populated_by_build_timeframe_state(self):
        """End-to-end: OBs emitted via compute_market_state should have touch_count populated.

        Hand-constructed H1 candles that produce a bullish OB (bearish candle
        before a bullish BOS), followed by candles that revisit the zone.
        """
        from src.components.market_state import _build_timeframe_state

        candles = [
            {"time": "t00", "open": 100, "close": 99,  "high": 101, "low": 98},
            {"time": "t01", "open": 99,  "close": 101, "high": 102, "low": 98},
            {"time": "t02", "open": 101, "close": 103, "high": 104, "low": 100},
            {"time": "t03", "open": 103, "close": 105, "high": 106, "low": 102},
            {"time": "t04", "open": 105, "close": 107, "high": 108, "low": 104},
            {"time": "t05", "open": 107, "close": 105, "high": 108, "low": 104},  # pullback low
            {"time": "t06", "open": 105, "close": 103, "high": 105, "low": 102},  # bearish — OB candidate
            {"time": "t07", "open": 103, "close": 107, "high": 108, "low": 103},  # impulse up
            {"time": "t08", "open": 107, "close": 110, "high": 111, "low": 106},  # BOS break above prior high
            {"time": "t09", "open": 110, "close": 108, "high": 112, "low": 107},
            {"time": "t10", "open": 108, "close": 104, "high": 109, "low": 103},  # retest into OB [102-105]
            {"time": "t11", "open": 104, "close": 106, "high": 107, "low": 103},  # another retest
            {"time": "t12", "open": 106, "close": 109, "high": 110, "low": 105},
        ]
        tf = _build_timeframe_state(candles, min_bars=2, fvg_min_gap=0.0, tf_name="H1")
        # May or may not produce an OB depending on structure; when it does,
        # every OB must have touch_count populated (>=0) and equal to our
        # independent recount. That's the invariant we test.
        for ob in tf.order_blocks:
            expected = _count_touches(ob, candles)
            assert ob.touch_count == expected
            assert ob.touch_count >= 0


# -----------------------------------------------------------------------
# identify_fvgs
# -----------------------------------------------------------------------

class TestFVGs:

    def test_identify_fvgs(self, bullish_candles):
        fvgs = identify_fvgs(bullish_candles, min_gap_size=1.0)
        assert len(fvgs) >= 1
        bullish_fvgs = [f for f in fvgs if f.type == "bullish"]
        assert len(bullish_fvgs) >= 1
        for fvg in bullish_fvgs:
            # top > bottom
            assert fvg.top > fvg.bottom
            gap = fvg.top - fvg.bottom
            assert gap >= 1.0
            # midpoint is average
            assert abs(fvg.midpoint - (fvg.top + fvg.bottom) / 2) < 0.01

    def test_fvg_filled_check(self, bullish_candles):
        """Verify filled flag correctness."""
        fvgs = identify_fvgs(bullish_candles, min_gap_size=1.0)
        for fvg in fvgs:
            if fvg.type == "bullish" and fvg.filled:
                # Some candle after the FVG came back down to the bottom
                last_idx = fvg.candle_indices[-1]
                went_back = any(
                    bullish_candles[k]["low"] <= fvg.bottom
                    for k in range(last_idx + 1, len(bullish_candles))
                )
                assert went_back

    def test_no_fvg_small_gap(self):
        """If min_gap_size is huge, no FVGs should be detected."""
        candles = [
            {"time": "t0", "open": 100, "close": 101, "high": 102, "low": 99},
            {"time": "t1", "open": 101, "close": 102, "high": 103, "low": 100},
            {"time": "t2", "open": 102, "close": 103, "high": 104, "low": 101},
        ]
        fvgs = identify_fvgs(candles, min_gap_size=100.0)
        assert fvgs == []

    def test_bearish_fvg(self, bullish_candles):
        """Even in bullish data, there can be bearish FVGs during pullbacks."""
        fvgs = identify_fvgs(bullish_candles, min_gap_size=1.0)
        bearish_fvgs = [f for f in fvgs if f.type == "bearish"]
        # Our bullish fixture has pullbacks, expect some bearish FVGs
        for fvg in bearish_fvgs:
            assert fvg.top > fvg.bottom

    def test_fvg_poi_identity_is_stable_while_predecision_state_advances(self):
        formation = [
            {
                "time": "2026-05-14T00:00:00+00:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
            },
            {
                "time": "2026-05-14T00:15:00+00:00",
                "open": 100.0,
                "high": 104.0,
                "low": 100.0,
                "close": 103.5,
            },
            {
                "time": "2026-05-14T00:30:00+00:00",
                "open": 103.5,
                "high": 105.0,
                "low": 103.0,
                "close": 104.0,
            },
        ]
        partial_touch = {
            "time": "2026-05-14T00:45:00+00:00",
            "open": 104.0,
            "high": 104.2,
            "low": 102.0,
            "close": 103.0,
        }
        fill_and_invalidate = {
            "time": "2026-05-14T01:00:00+00:00",
            "open": 103.0,
            "high": 103.1,
            "low": 100.5,
            "close": 100.8,
        }

        initial = identify_fvgs(
            formation,
            min_gap_size=1.0,
            symbol="US30_CASH",
            timeframe="M15",
        )[0]
        touched = identify_fvgs(
            [*formation, partial_touch],
            min_gap_size=1.0,
            symbol="US30_CASH",
            timeframe="M15",
        )[0]
        terminal = identify_fvgs(
            [*formation, partial_touch, fill_and_invalidate],
            min_gap_size=1.0,
            symbol="US30_CASH",
            timeframe="M15",
        )[0]

        assert initial.poi_id == touched.poi_id == terminal.poi_id
        assert initial.created_at_utc == "2026-05-14T00:45:00+00:00"
        assert initial.state_asof_utc == initial.created_at_utc
        assert [initial.touch_count, touched.touch_count, terminal.touch_count] == [0, 1, 2]
        assert initial.mitigation_status == "untouched"
        assert touched.mitigation_status == "partially_mitigated"
        assert terminal.mitigation_status == "partially_mitigated"
        assert terminal.filled is False
        assert terminal.invalidated is True
        assert terminal.overlap_bar_count == 2
        assert terminal.touch_episode_count == 1
        assert terminal.terminal_frozen is True
        assert terminal.terminal_reason == "bullish_fvg_close_below_far_boundary"
        assert len(
            {
                initial.poi_state_hash_sha256,
                touched.poi_state_hash_sha256,
                terminal.poi_state_hash_sha256,
            }
        ) == 3
        assert all(
            fvg.poi_state_contract_status == "valid_predecision_poi_state"
            for fvg in (initial, touched, terminal)
        )

        post_terminal = identify_fvgs(
            [
                *formation,
                partial_touch,
                fill_and_invalidate,
                {
                    "time": "2026-05-14T01:15:00+00:00",
                    "open": 100.8,
                    "high": 103.5,
                    "low": 100.0,
                    "close": 102.5,
                },
            ],
            min_gap_size=1.0,
            symbol="US30_CASH",
            timeframe="M15",
        )[0]
        assert post_terminal.poi_id == terminal.poi_id
        assert post_terminal.overlap_bar_count == terminal.overlap_bar_count
        assert post_terminal.touch_episode_count == terminal.touch_episode_count
        assert post_terminal.max_mitigation_fraction == terminal.max_mitigation_fraction
        assert post_terminal.terminal_time_utc == terminal.terminal_time_utc
        assert post_terminal.terminal_reason == terminal.terminal_reason


# -----------------------------------------------------------------------
# calculate_premium_discount
# -----------------------------------------------------------------------

class TestPremiumDiscount:

    def test_premium_discount_calculation(self, bullish_candles):
        swings = detect_swings(bullish_candles, min_bars=2)
        struct = identify_structure(swings)
        pd = calculate_premium_discount(swings, struct)
        assert pd is not None
        assert pd.impulse_high > pd.impulse_low
        # equilibrium is midpoint
        expected_eq = (pd.impulse_high + pd.impulse_low) / 2
        assert abs(pd.equilibrium_50 - expected_eq) < 0.01
        # Fib 62 is between eq and low
        assert pd.fib_62 < pd.equilibrium_50
        assert pd.fib_62 > pd.impulse_low
        # Fib 79 is between fib_62 and low
        assert pd.fib_79 < pd.fib_62
        assert pd.fib_79 > pd.impulse_low
        # OTE zone
        assert pd.ote_zone.top == pd.fib_62
        assert pd.ote_zone.bottom == pd.fib_79
        # Premium zone is above equilibrium
        assert pd.premium_zone.bottom == pd.equilibrium_50
        assert pd.premium_zone.top == pd.impulse_high
        # Discount zone is below equilibrium
        assert pd.discount_zone.top == pd.equilibrium_50
        assert pd.discount_zone.bottom == pd.impulse_low

    def test_premium_discount_bearish(self, bearish_candles):
        swings = detect_swings(bearish_candles, min_bars=2)
        struct = identify_structure(swings)
        pd = calculate_premium_discount(swings, struct)
        assert pd is not None
        assert pd.impulse_high > pd.impulse_low
        # For bearish: fib_62 and fib_79 are retracement *up* from the low
        assert pd.fib_62 > pd.equilibrium_50
        assert pd.fib_79 > pd.fib_62

    def test_returns_none_transitional(self, ranging_candles):
        swings = detect_swings(ranging_candles, min_bars=2)
        struct = identify_structure(swings)
        assert struct.direction == "transitional"
        pd = calculate_premium_discount(swings, struct)
        assert pd is None

    def test_returns_none_no_swings(self):
        struct = StructureAnalysis(direction="bullish")
        pd = calculate_premium_discount([], struct)
        assert pd is None


# -----------------------------------------------------------------------
# detect_sweeps
# -----------------------------------------------------------------------

class TestSweeps:

    def test_detect_sweep(self, sweep_candles):
        pool_low = LiquidityPool(type="asian_low", price=3042.00, side="low")
        sweeps = detect_sweeps(sweep_candles, [pool_low])
        sweep_events = [s for s in sweeps if s.sweep_type == "sweep"]
        assert len(sweep_events) >= 1
        # The sweep candle wicked below the pool but body stayed above
        for s in sweep_events:
            assert s.wick_extreme < pool_low.price
            assert min(sweep_candles[s.candle_index]["open"],
                       sweep_candles[s.candle_index]["close"]) > pool_low.price

    def test_detect_run(self, sweep_candles):
        pool_high = LiquidityPool(type="session_high", price=3052.00, side="high")
        sweeps = detect_sweeps(sweep_candles, [pool_high])
        run_events = [s for s in sweeps if s.sweep_type == "run"]
        assert len(run_events) >= 1
        for s in run_events:
            assert sweep_candles[s.candle_index]["close"] > pool_high.price

    def test_no_sweeps_far_away_pool(self, sweep_candles):
        pool = LiquidityPool(type="pdh", price=9999.00, side="high")
        sweeps = detect_sweeps(sweep_candles, [pool])
        assert sweeps == []


# -----------------------------------------------------------------------
# avg_candle_body
# -----------------------------------------------------------------------

class TestAvgCandleBody:

    def test_avg_candle_body(self):
        candles = [
            {"open": 100, "close": 104},  # body = 4
            {"open": 106, "close": 102},  # body = 4
            {"open": 103, "close": 107},  # body = 4
        ]
        result = avg_candle_body(candles, period=3)
        assert abs(result - 4.0) < 0.01

    def test_avg_candle_body_period_larger_than_data(self):
        candles = [{"open": 10, "close": 12}]  # body = 2
        result = avg_candle_body(candles, period=20)
        assert abs(result - 2.0) < 0.01

    def test_avg_candle_body_empty(self):
        assert avg_candle_body([], period=20) == 0.0

    def test_avg_candle_body_on_fixture(self, bullish_candles):
        result = avg_candle_body(bullish_candles, period=20)
        # Gold M15 bodies should be in the $1-$10 range
        assert 0.5 < result < 15.0


# -----------------------------------------------------------------------
# compute_market_state (integration)
# -----------------------------------------------------------------------

class TestComputeMarketState:

    def test_compute_market_state_integration(self, bullish_candles, tmp_path, monkeypatch):
        """Full pipeline: raw candles → MarketStateObject."""
        # Monkey-patch KNOWLEDGE_BASE_DIR so write goes to tmp
        import src.utils.file_io as fio
        monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
        # Also patch via the market_state module's reference to ensure it picks up the patched value
        import src.components.market_state as ms_mod
        original_write = ms_mod.write_pipeline
        def _patched_write(filename, data):
            from src.utils.file_io import atomic_write
            filepath = tmp_path / "pipeline_state" / filename
            atomic_write(filepath, data)
        monkeypatch.setattr(ms_mod, "write_pipeline", _patched_write)
        (tmp_path / "pipeline_state").mkdir()

        raw_data = {
            "timestamp_utc": "2026-03-28T07:15:00Z",
            "candles": {
                "D1": bullish_candles[:30],
                "H4": bullish_candles[:40],
                "H1": bullish_candles,
                "M15": bullish_candles,
            },
            "session_levels": {
                "asian_high": 3045.20,
                "asian_low": 3038.50,
                "pdh": 3052.80,
                "pdl": 3030.10,
                "session_high": 3046.00,
                "session_low": 3039.75,
            },
            "equal_highs_H4": [],
            "equal_lows_H4": [],
            "equal_highs_H1": [],
            "equal_lows_H1": [],
            "spread_cents": 18.5,
            "high_impact_events": [],
            "data_quality": {
                "all_timeframes_complete": True,
                "spread_normal": True,
                "mt5_connected": True,
                "timestamp_utc": "2026-03-28T07:15:00Z",
            },
        }

        config = {
            "data": {
                "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0},
            }
        }

        mso = compute_market_state(raw_data, config)

        # Type check
        assert isinstance(mso, MarketStateObject)
        assert mso.timestamp_utc == "2026-03-28T07:15:00Z"

        # All four timeframes present
        for tf in ("D1", "H4", "H1", "M15"):
            assert tf in mso.timeframes

        # M15 should have bullish structure
        m15 = mso.timeframes["M15"]
        assert m15.structure.direction == "bullish"
        assert len(m15.swings) >= 4
        assert len(m15.structure_events) >= 1
        assert m15.avg_candle_body > 0

        # Session levels
        assert mso.session_levels.asian_high == 3045.20
        assert mso.session_levels.pdl == 3030.10

        # Data quality
        assert mso.data_quality.all_timeframes_complete is True
        assert mso.spread_cents == 18.5

        # Liquidity pools built
        assert len(mso.liquidity_pools) >= 4  # asian_high/low + pdh/pdl

        # Pipeline file written
        assert (tmp_path / "pipeline_state" / "02_market_state.json").exists()

    def test_compute_handles_empty_candles(self, tmp_path, monkeypatch):
        import src.utils.file_io as fio
        monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
        (tmp_path / "pipeline_state").mkdir()

        raw_data = {
            "timestamp_utc": "2026-03-28T07:15:00Z",
            "candles": {},
            "session_levels": {
                "asian_high": 0, "asian_low": 0,
                "pdh": 0, "pdl": 0,
            },
            "data_quality": {
                "all_timeframes_complete": False,
                "spread_normal": False,
                "mt5_connected": False,
                "timestamp_utc": "2026-03-28T07:15:00Z",
            },
        }
        config = {"data": {}}
        mso = compute_market_state(raw_data, config)
        for tf in ("D1", "H4", "H1", "M15"):
            assert mso.timeframes[tf].structure.direction == "insufficient_data"


# -----------------------------------------------------------------------
# compute_clv (I1 feature engineering)
# -----------------------------------------------------------------------

class TestCLV:

    def test_close_at_high(self):
        candle = {"high": 110.0, "low": 100.0, "close": 110.0, "open": 105.0}
        assert compute_clv(candle) == pytest.approx(1.0)

    def test_close_at_low(self):
        candle = {"high": 110.0, "low": 100.0, "close": 100.0, "open": 105.0}
        assert compute_clv(candle) == pytest.approx(-1.0)

    def test_close_at_midpoint(self):
        candle = {"high": 110.0, "low": 100.0, "close": 105.0, "open": 104.0}
        assert compute_clv(candle) == pytest.approx(0.0)

    def test_doji_high_equals_low(self):
        candle = {"high": 105.0, "low": 105.0, "close": 105.0, "open": 105.0}
        assert compute_clv(candle) == 0.0

    def test_range_within_minus1_plus1(self, bullish_candles):
        for c in bullish_candles:
            clv = compute_clv(c)
            assert -1.0 <= clv <= 1.0

    def test_bullish_candle_positive_clv(self):
        # Candle closing near top of its range → positive CLV
        candle = {"high": 110.0, "low": 100.0, "close": 108.0, "open": 101.0}
        assert compute_clv(candle) > 0

    def test_bearish_candle_negative_clv(self):
        # Candle closing near bottom of its range → negative CLV
        candle = {"high": 110.0, "low": 100.0, "close": 102.0, "open": 109.0}
        assert compute_clv(candle) < 0


# -----------------------------------------------------------------------
# compute_bvc (I1 feature engineering)
# -----------------------------------------------------------------------

class TestBVC:

    def test_large_bullish_bar_high_buy_fraction(self):
        candle = {"open": 100.0, "close": 110.0, "high": 111.0, "low": 99.0, "volume": 1000}
        result = compute_bvc(candle, atr_14=5.0)
        assert result > 0.8

    def test_large_bearish_bar_low_buy_fraction(self):
        candle = {"open": 110.0, "close": 100.0, "high": 111.0, "low": 99.0, "volume": 1000}
        result = compute_bvc(candle, atr_14=5.0)
        assert result < 0.2

    def test_doji_neutral_buy_fraction(self):
        candle = {"open": 105.0, "close": 105.0, "high": 110.0, "low": 100.0, "volume": 500}
        result = compute_bvc(candle, atr_14=5.0)
        assert abs(result - 0.5) < 0.01

    def test_zero_volume_returns_half(self):
        candle = {"open": 100.0, "close": 105.0, "high": 106.0, "low": 99.0, "volume": 0}
        assert compute_bvc(candle, atr_14=5.0) == 0.5

    def test_zero_atr_returns_half(self):
        candle = {"open": 100.0, "close": 105.0, "high": 106.0, "low": 99.0, "volume": 500}
        assert compute_bvc(candle, atr_14=0.0) == 0.5

    def test_missing_volume_returns_half(self):
        candle = {"open": 100.0, "close": 105.0, "high": 106.0, "low": 99.0}
        assert compute_bvc(candle, atr_14=5.0) == 0.5

    def test_result_in_zero_one_range(self, bullish_candles):
        atr = calculate_atr(bullish_candles, period=14)
        for c in bullish_candles:
            result = compute_bvc(c, atr)
            assert 0.0 <= result <= 1.0


# -----------------------------------------------------------------------
# compute_session_atr (I1 feature engineering — XAUUSD gold sessions)
# -----------------------------------------------------------------------

def _make_session_candles(n: int, hour: int, base_price: float = 3050.0) -> list[dict]:
    """Helper: synthesise n candles all timestamped in the given UTC hour."""
    candles = []
    for i in range(n):
        o = base_price + i * 0.5
        c = o + 1.0
        candles.append({
            "time": f"2026-04-10T{hour:02d}:{i % 60:02d}:00Z",
            "open": o, "close": c,
            "high": c + 0.5, "low": o - 0.5,
            "volume": 500,
        })
    return candles


class TestSessionATR:

    def test_returns_none_insufficient_data(self):
        candles = _make_session_candles(10, hour=8)  # fewer than period+1
        result = compute_session_atr(candles, start_hour=7, end_hour=11)
        assert result is None

    def test_computes_atr_for_session_candles(self):
        # 20 London-hour candles should produce a valid ATR
        candles = _make_session_candles(20, hour=8)
        result = compute_session_atr(candles, start_hour=7, end_hour=11)
        assert result is not None
        assert result > 0

    def test_filters_out_of_session_candles(self):
        london = _make_session_candles(20, hour=8, base_price=3050.0)
        asian = _make_session_candles(20, hour=1, base_price=10000.0)  # extreme prices
        mixed = london + asian
        result_mixed = compute_session_atr(mixed, start_hour=7, end_hour=11)
        result_london = compute_session_atr(london, start_hour=7, end_hour=11)
        # Asian candles should be ignored — results must be identical
        assert result_mixed == pytest.approx(result_london)

    def test_synthetic_time_strings_ignored(self):
        candles = [{"time": "t0", "open": 100, "close": 101, "high": 102, "low": 99}] * 20
        result = compute_session_atr(candles, start_hour=7, end_hour=11)
        assert result is None

    def test_midnight_wrap_session(self):
        # Asian session 22:00-03:00 (wraps midnight)
        late = _make_session_candles(20, hour=22)
        early = _make_session_candles(20, hour=1)
        candles = late + early
        result = compute_session_atr(candles, start_hour=22, end_hour=3)
        assert result is not None
        assert result > 0


# -----------------------------------------------------------------------
# CLV/BVC fields wired into TimeframeState via _build_timeframe_state
# -----------------------------------------------------------------------

class TestFlowFeaturesInMSO:

    def test_clv_present_after_compute_market_state(self, bullish_candles, tmp_path, monkeypatch):
        import src.utils.file_io as fio
        import src.components.market_state as ms_mod
        monkeypatch.setattr(fio, "KNOWLEDGE_BASE_DIR", tmp_path)
        monkeypatch.setattr(ms_mod, "write_pipeline", lambda f, d: None)

        raw_data = {
            "timestamp_utc": "2026-03-28T07:15:00Z",
            "candles": {"D1": bullish_candles[:20], "H4": bullish_candles[:30],
                        "H1": bullish_candles, "M15": bullish_candles},
            "session_levels": {"asian_high": 3045.0, "asian_low": 3038.0,
                               "pdh": 3052.0, "pdl": 3030.0},
            "data_quality": {"all_timeframes_complete": True, "spread_normal": True,
                             "mt5_connected": True, "timestamp_utc": "2026-03-28T07:15:00Z"},
        }
        config = {"data": {"swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                           "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0}}}
        mso = compute_market_state(raw_data, config)

        m15 = mso.timeframes["M15"]
        assert m15.clv_current is not None
        assert -1.0 <= m15.clv_current <= 1.0
        assert m15.clv_avg_5 is not None
        assert m15.bvc_buy_fraction is not None
        assert 0.0 <= m15.bvc_buy_fraction <= 1.0
        assert m15.net_flow_5 is not None

    def test_session_atr_xauusd_london(self, bullish_candles, monkeypatch):
        """XAUUSD with London-hour timestamp → session ATR populated."""
        import src.components.market_state as ms_mod
        monkeypatch.setattr(ms_mod, "write_pipeline", lambda f, d: None)

        # Give candles London-hour timestamps so session filter finds them
        london_candles = []
        for i, c in enumerate(bullish_candles):
            london_candles.append({**c, "time": f"2026-04-10T08:{i % 60:02d}:00Z"})

        raw_data = {
            "timestamp_utc": "2026-04-10T08:15:00Z",
            "symbol": "XAUUSD",
            "candles": {"D1": london_candles[:20], "H4": london_candles[:30],
                        "H1": london_candles, "M15": london_candles},
            "session_levels": {"asian_high": 3045.0, "asian_low": 3038.0,
                               "pdh": 3052.0, "pdl": 3030.0},
            "data_quality": {"all_timeframes_complete": True, "spread_normal": True,
                             "mt5_connected": True, "timestamp_utc": "2026-04-10T08:15:00Z"},
        }
        config = {"data": {"swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                           "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0}}}
        mso = compute_market_state(raw_data, config)

        m15 = mso.timeframes["M15"]
        assert m15.atr_session is not None
        assert m15.atr_session > 0
        assert m15.session_vol_ratio is not None

    def test_session_atr_not_set_for_non_xauusd(self, bullish_candles, monkeypatch):
        import src.components.market_state as ms_mod
        monkeypatch.setattr(ms_mod, "write_pipeline", lambda f, d: None)

        raw_data = {
            "timestamp_utc": "2026-04-10T08:15:00Z",
            "symbol": "US30",
            "candles": {"D1": bullish_candles[:20], "H4": bullish_candles[:30],
                        "H1": bullish_candles, "M15": bullish_candles},
            "session_levels": {"asian_high": 38000.0, "asian_low": 37900.0,
                               "pdh": 38100.0, "pdl": 37800.0},
            "data_quality": {"all_timeframes_complete": True, "spread_normal": True,
                             "mt5_connected": True, "timestamp_utc": "2026-04-10T08:15:00Z"},
        }
        config = {"data": {"swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
                           "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0}}}
        mso = compute_market_state(raw_data, config)
        assert mso.timeframes["M15"].atr_session is None
        assert mso.timeframes["M15"].session_vol_ratio is None

    def test_session_atr_regression_empty_symbol_disables_xauusd_branch(
        self, bullish_candles, monkeypatch,
    ):
        """Session-38 regression forensics: 18/18 live XAUUSD candidate_features
        rows had ``mso_m15_session_vol_ratio = None`` because the upstream
        ``raw_data`` dropped ``symbol`` and this gate saw ``""``.

        Locks the pre-fix + post-fix contract:
          * symbol missing entirely -> session ATR is None (legacy behavior).
          * symbol present + XAUUSD -> session ATR populated (post-fix).
        """
        import src.components.market_state as ms_mod
        monkeypatch.setattr(ms_mod, "write_pipeline", lambda f, d: None)

        # London-hour timestamps so the session-ATR filter finds candles.
        london_candles = []
        for i, c in enumerate(bullish_candles):
            london_candles.append({**c, "time": f"2026-04-10T08:{i % 60:02d}:00Z"})

        # Case 1: symbol key ABSENT (pre-fix live raw_data shape). Gate sees
        # the default "" and the XAUUSD branch does NOT fire.
        raw_no_symbol = {
            "timestamp_utc": "2026-04-10T08:15:00Z",
            # no "symbol" key at all
            "candles": {"D1": london_candles[:20], "H4": london_candles[:30],
                        "H1": london_candles, "M15": london_candles},
            "session_levels": {"asian_high": 3045.0, "asian_low": 3038.0,
                               "pdh": 3052.0, "pdl": 3030.0},
            "data_quality": {"all_timeframes_complete": True, "spread_normal": True,
                             "mt5_connected": True,
                             "timestamp_utc": "2026-04-10T08:15:00Z"},
        }
        # Case 2: symbol key PRESENT and equal to "" (simulates the exact
        # shape ingest_live_data emitted pre-fix if it had emitted the key).
        raw_empty_symbol = {**raw_no_symbol, "symbol": ""}
        # Case 3: symbol key PRESENT and canonical XAUUSD (post-fix shape).
        raw_xauusd = {**raw_no_symbol, "symbol": "XAUUSD"}

        config = {"data": {
            "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
            "fvg_min_gap": {"D1": 5.0, "H4": 3.0, "H1": 2.0, "M15": 1.0},
        }}

        mso_no_sym = compute_market_state(raw_no_symbol, config)
        mso_empty = compute_market_state(raw_empty_symbol, config)
        mso_xauusd = compute_market_state(raw_xauusd, config)

        # Pre-fix shapes: XAUUSD branch skipped.
        assert mso_no_sym.timeframes["M15"].atr_session is None
        assert mso_no_sym.timeframes["M15"].session_vol_ratio is None
        assert mso_empty.timeframes["M15"].atr_session is None
        assert mso_empty.timeframes["M15"].session_vol_ratio is None

        # Post-fix shape: XAUUSD branch fires.
        assert mso_xauusd.timeframes["M15"].atr_session is not None
        assert mso_xauusd.timeframes["M15"].atr_session > 0
        assert mso_xauusd.timeframes["M15"].session_vol_ratio is not None
