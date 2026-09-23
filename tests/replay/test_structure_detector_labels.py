"""Structure detector label-distribution tests.

``src.components.market_state.identify_structure`` classifies a swing
sequence as bullish / bearish / transitional / insufficient_data. For a
30-day mixed-regime window (2026-Q1 had both up and down moves across 5
instruments) we expect a mix, not a single dominant label.

Known bug (xfail): on current HEAD ``identify_structure`` produces 100%
bullish across 168-bar H1 windows on XAUUSD and GBPUSD. Root cause:
``recent_pairs`` is pinned at 3 and the bullish branch fires whenever 3+
HHs and 3+ HLs appear anywhere in the window — even when the recent
sequence is clearly bearish. See the synthetic fixtures below for the
minimal reproduction. Once fixed, drop the xfail marker.

Why this is an F2-prototype-critical test
-----------------------------------------
F2 (multi-TF reversal prototype) depends on correct structure direction
at the H1/H4 level. A 100%-bullish bias poisons every downstream F2 gate.
This test is the canary that catches that bug class.

Cost: ~1 sec per symbol. Uses ``data/historical_2026/{symbol}_H1.csv``.
"""
from __future__ import annotations

from collections import Counter

import pytest

from src.components.market_state import (
    detect_swings,
    identify_structure,
    identify_structure_v2,
)
from src.models.market_state_models import Swing


pytestmark = pytest.mark.replay


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------


# Any label above this fraction is deemed dominant → fail the distribution check.
DOMINANCE_MAX = 0.90


class TestStructureDetectorLabels:
    """Distribution + targeted synthetic checks for identify_structure."""

    @pytest.mark.xfail(
        reason=(
            "Known bug: identify_structure returns 100% bullish on 168-bar "
            "H1 windows across all instruments because the bullish branch "
            "fires whenever ANY 3 HHs + 3 HLs exist in the window — it does "
            "NOT weight by recency. Even the XAUUSD 2026-03-11 → 2026-03-20 "
            "window (which spans a -21% drawdown) contains 8 HHs + 9 HLs "
            "alongside 12 LHs + 12 LLs, so the bullish branch wins. "
            "Expected fix: change ``recent_pairs`` selection to use only "
            "the last N pair transitions, not the total count. Once fixed, "
            "drop this xfail and reference the fix ADR in the commit message."
        ),
        strict=True,
    )
    def test_label_distribution_not_100_percent_one_direction(self, h1_windows):
        """No single label should dominate above 90% of rolling H1 windows.

        30-day window × 5 symbols × rolling 168-bar = ~65 windows per
        symbol. 2026-Q1 had visible bearish stretches on every instrument
        (see XAUUSD D1 swings 2026-03-10 → 2026-03-23 low of 4098.74 from
        5238.35 high — a -21% drawdown). A correctly-labeling detector
        should produce a non-trivial bearish / transitional count.
        """
        aggregate: Counter = Counter()
        per_symbol: dict[str, Counter] = {}

        for symbol in ("XAUUSD", "GBPUSD", "USDJPY", "GBPJPY", "US30_cash"):
            labels: list[str] = []
            for window in h1_windows(symbol, window=168, step=24):
                swings = detect_swings(window)
                labels.append(identify_structure(swings).direction)
            if not labels:
                continue
            counter = Counter(labels)
            per_symbol[symbol] = counter
            aggregate.update(counter)

        total = sum(aggregate.values())
        print(f"\n[structure_labels/aggregate] total={total} {dict(aggregate)}")
        for sym, counter in per_symbol.items():
            print(f"  {sym}: {dict(counter)}")

        if total == 0:
            pytest.skip("No H1 historical data loaded — check data/historical_2026/")

        for label in ("bullish", "bearish"):
            fraction = aggregate.get(label, 0) / total
            assert fraction < DOMINANCE_MAX, (
                f"Label '{label}' dominates: {fraction:.1%} of {total} windows "
                f"exceeds {DOMINANCE_MAX:.0%} threshold. See per-symbol "
                "breakdown above — structure detector is likely biased."
            )

    def test_synthetic_pure_uptrend_labeled_bullish(self):
        """HH/HL sequence must produce ``bullish`` direction."""
        swings = [
            Swing(index=0, type="low", price=100.0, time="2026-01-01T00:00:00"),
            Swing(index=1, type="high", price=110.0, time="2026-01-01T04:00:00"),
            Swing(index=2, type="low", price=105.0, time="2026-01-01T08:00:00"),
            Swing(index=3, type="high", price=115.0, time="2026-01-01T12:00:00"),
            Swing(index=4, type="low", price=108.0, time="2026-01-01T16:00:00"),
            Swing(index=5, type="high", price=120.0, time="2026-01-01T20:00:00"),
            Swing(index=6, type="low", price=112.0, time="2026-01-02T00:00:00"),
            Swing(index=7, type="high", price=125.0, time="2026-01-02T04:00:00"),
        ]
        result = identify_structure(swings)
        assert result.direction == "bullish", (
            f"Pure uptrend should be bullish, got {result.direction}. "
            f"hh={result.hh_count} hl={result.hl_count}"
        )

    def test_synthetic_pure_downtrend_labeled_bearish(self):
        """LH/LL sequence must produce ``bearish`` direction.

        A fully synthetic pure downtrend has zero HH/HL, so the first
        branch (``hh >= 3 and hl >= 3``) cannot match and the bearish
        branch fires correctly. The real-data bug (``test_label_distribution``
        below) is a distinct issue: on REAL windows of 168 H1 bars even
        bearish stretches contain >=3 HHs + >=3 HLs somewhere, so the
        bullish branch always wins. This synthetic test catches the
        narrower case where HH/HL are absent.
        """
        swings = [
            Swing(index=0, type="high", price=125.0, time="2026-01-01T00:00:00"),
            Swing(index=1, type="low", price=115.0, time="2026-01-01T04:00:00"),
            Swing(index=2, type="high", price=120.0, time="2026-01-01T08:00:00"),
            Swing(index=3, type="low", price=110.0, time="2026-01-01T12:00:00"),
            Swing(index=4, type="high", price=114.0, time="2026-01-01T16:00:00"),
            Swing(index=5, type="low", price=104.0, time="2026-01-01T20:00:00"),
            Swing(index=6, type="high", price=108.0, time="2026-01-02T00:00:00"),
            Swing(index=7, type="low", price=98.0, time="2026-01-02T04:00:00"),
        ]
        result = identify_structure(swings)
        assert result.direction == "bearish", (
            f"Pure downtrend should be bearish, got {result.direction}. "
            f"ll={result.ll_count} lh={result.lh_count} "
            f"hh={result.hh_count} hl={result.hl_count}"
        )

    def test_synthetic_insufficient_data(self):
        """Fewer than 2 highs+lows should produce ``insufficient_data``."""
        swings = [
            Swing(index=0, type="low", price=100.0, time="2026-01-01T00:00:00"),
            Swing(index=1, type="high", price=110.0, time="2026-01-01T04:00:00"),
        ]
        result = identify_structure(swings)
        # Need ≥2 of each — with only 1 high and 1 low we expect insufficient.
        assert result.direction == "insufficient_data"

    def test_v2_label_distribution_no_direction_dominates(self, h1_windows):
        """F2.1 sibling: identify_structure_v2 label distribution.

        Under ADR-004 Option D (net-score classifier), 30-day rolling
        H1 windows across 5 instruments must NOT produce any single
        direction above 90% (aggregate) — the v1 failure mode this
        suite is the canary for.

        Unlike the v1 test above (strict xfail on known bug), this
        sibling asserts the PASS condition on v2 directly. Once v2 is
        wired into the production path (F2.3), the v1 xfail test can
        be removed in favour of this one.
        """
        aggregate: Counter = Counter()
        per_symbol: dict[str, Counter] = {}

        for symbol in ("XAUUSD", "GBPUSD", "USDJPY", "GBPJPY", "US30_cash"):
            labels: list[str] = []
            for window in h1_windows(symbol, window=168, step=24):
                swings = detect_swings(window)
                labels.append(identify_structure_v2(swings).direction)
            if not labels:
                continue
            counter = Counter(labels)
            per_symbol[symbol] = counter
            aggregate.update(counter)

        total = sum(aggregate.values())
        print(f"\n[structure_labels_v2/aggregate] total={total} {dict(aggregate)}")
        for sym, counter in per_symbol.items():
            print(f"  v2 {sym}: {dict(counter)}")

        if total == 0:
            pytest.skip("No H1 historical data loaded — check data/historical_2026/")

        for label in ("bullish", "bearish", "transitional"):
            fraction = aggregate.get(label, 0) / total
            assert fraction < DOMINANCE_MAX, (
                f"v2 label '{label}' dominates: {fraction:.1%} of {total} "
                f"windows exceeds {DOMINANCE_MAX:.0%} threshold. See "
                "per-symbol breakdown above — v2 detector regressed."
            )
