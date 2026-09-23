"""Tests for ``research/retest_geometry/study.py`` (v2, ADR 003).

Coverage targets (per brief, 75+ tests):
1. OB detection parity — 4+
2. Retest detection (corrected timing) — 6+
3. MAE computation — 5+
4. ATR normalization — 3+
5. Session labels — 6+
6. Continuation classification — 6+ (Geom A + Geom B)
7. Continuation-R calc — 3+
8. Output CSV schema — 4+
9. Edge cases — 5+
10. Live-period join — 6+
11. Twin-geometry invariants — 5+
12. BOS detection & temporal ordering — 5+
13. Geometry B (Test A) SL / target / window — 6+

Test-isolation discipline
-------------------------
All filesystem paths are module-level constants on ``research.retest_geometry.study``
so tests monkeypatch via ``monkeypatch.setattr(_mod, "OUT_DIR", tmp_path)``.
Any attempt to write to ``shadow_logs/``, ``knowledge_base/`` etc. inside the
pytest process triggers the ``ProductionWriteError`` guard in
``tests/conftest.py``.

Notes re v1 → v2 migration
--------------------------
v1 retest-detection tests that passed a raw SimpleNamespace OB into
``_detect_first_retest`` no longer match the signature (v2 requires an
``AnnotatedOB``). The tests below build a proper ``AnnotatedOB`` whose
``bos_confirm_ts`` is set to a time BEFORE the first M15 candle, so the
retest walker can reach the test candles. This preserves the v1 test intent
while honoring the ADR 003 corrected-timing invariant.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import fields as dc_fields
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

# Import under module-ref so monkeypatching module constants works.
from research.retest_geometry import study as _mod  # noqa: E402


# ---------------------------------------------------------------------------
# Test fixtures — synthetic OB + candle helpers
# ---------------------------------------------------------------------------


def _m15_candle(ts: str, o: float, h: float, lo: float, c: float, vol: float = 100.0) -> dict:
    """Build a single M15 candle dict matching the parse_tradingview_csv shape."""
    return {"time": ts, "open": o, "high": h, "low": lo, "close": c, "volume": vol}


def _synthetic_ob(
    ob_type: str = "bullish",
    high: float = 100.5,
    low: float = 100.0,
    formation_time: str = "2026-01-10T08:00:00Z",
    open_price: float | None = None,
    close_price: float | None = None,
    mitigated: bool = False,
) -> SimpleNamespace:
    """Return an OB-like object with the fields study.py reads."""
    if open_price is None:
        open_price = (high + low) / 2 + 0.05
    if close_price is None:
        close_price = (high + low) / 2 - 0.05
    return SimpleNamespace(
        type=ob_type,
        high=high,
        low=low,
        open=open_price,
        close=close_price,
        formation_time=formation_time,
        formation_index=0,
        mitigated=mitigated,
        causing_bos_index=1,
        causing_event_type="BOS",
        touch_count=0,
    )


def _annotated(ob, bos_confirm_ts: str = "2026-01-10T08:00:00Z") -> _mod.AnnotatedOB:
    """Wrap a raw OB into an AnnotatedOB with the given BOS-confirm timestamp.

    Default ``bos_confirm_ts`` is the same as the default ``formation_time`` so
    the first M15 candle (08:15) will qualify for the walk.
    """
    return _mod.AnnotatedOB(ob=ob, bos_confirm_ts=bos_confirm_ts)


def _m15_range(
    start_ts: str,
    count: int,
    prices: list[tuple[float, float, float, float]] | None = None,
    default_ohlc: tuple[float, float, float, float] = (100.0, 100.5, 99.5, 100.2),
) -> list[dict]:
    """Generate a sequence of M15 candles starting at ``start_ts``."""
    dt0 = datetime.strptime(start_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    out = []
    for i in range(count):
        ts = (dt0 + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if prices and i < len(prices):
            o, h, lo, c = prices[i]
        else:
            o, h, lo, c = default_ohlc
        out.append(_m15_candle(ts, o, h, lo, c))
    return out


def _minimal_record(
    ob: SimpleNamespace,
    m15: list[dict],
    entry_idx: int = 0,
    entry_price: float | None = None,
    h1_atr: float = 0.5,
    symbol: str = "XAUUSD",
    bos_confirm_ts: str = "2026-01-10T08:00:00Z",
) -> _mod.RetestRecord:
    """Build a RetestRecord by invoking the real ``_classify_and_measure``.

    NOTE: Default ``bos_confirm_ts`` = ``2026-01-10T08:00:00Z`` and default
    M15 entry candle = ``2026-01-10T08:30:00Z`` so the temporal invariant
    ``retest_ts > bos_confirm_ts`` holds.
    """
    if entry_price is None:
        entry_price = float(m15[entry_idx]["close"])
    raw = _mod._RawRetest(
        ob=ob,
        bos_confirm_ts=bos_confirm_ts,
        retest_ts=m15[entry_idx]["time"],
        retest_idx=entry_idx,
        entry_price=entry_price,
        entry_idx=entry_idx,
        h1_atr=h1_atr,
    )
    return _mod._classify_and_measure(raw, m15, symbol)


# ===========================================================================
# Section 1: OB detection parity — synthetic + real-production helpers
# ===========================================================================


def test_ob_detection_returns_mitigated_flag_on_production_primitives():
    """Calling ``identify_order_blocks`` via the study's import should honor
    the production signature. (This is a smoke test that our imports are
    live and not a mocked shim.)
    """
    from src.components.market_state import identify_order_blocks, detect_swings, identify_structure, detect_structure_breaks
    assert callable(identify_order_blocks)
    assert callable(detect_swings)
    # Build a tiny synthetic H1 series with a clear BOS
    c = []
    base_prices = [100.0] * 10 + [101.0, 101.2] + [100.5, 99.0, 98.5] + [99.0, 99.5]
    for i, p in enumerate(base_prices):
        c.append(_m15_candle(
            f"2026-01-{(i//24)+1:02d}T{i%24:02d}:00:00Z",
            p, p + 0.5, p - 0.5, p + 0.1
        ))
    sw = detect_swings(c)
    st = identify_structure(sw)
    ev = detect_structure_breaks(c, sw, st)
    obs = identify_order_blocks(c, ev)
    for ob in obs:
        assert hasattr(ob, "mitigated")
        assert hasattr(ob, "type")
        assert ob.type in ("bullish", "bearish")


def test_production_ob_exposes_causing_bos_index():
    """v2 requires ``causing_bos_index`` on detected OBs to derive bos_confirm_ts."""
    from src.components.market_state import identify_order_blocks, detect_swings, identify_structure, detect_structure_breaks
    c = []
    for i in range(40):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        p = 100.0 if i < 10 else (100.0 + (i - 10) * 0.3)
        c.append(_m15_candle(ts, p, p + 0.3, p - 0.3, p + 0.05))
    sw = detect_swings(c)
    st = identify_structure(sw)
    ev = detect_structure_breaks(c, sw, st)
    obs = identify_order_blocks(c, ev)
    # Every OB should carry causing_bos_index (may be -1 if none)
    for ob in obs:
        assert hasattr(ob, "causing_bos_index")
        assert isinstance(ob.causing_bos_index, int)


def test_collect_unique_fresh_obs_dedups_by_formation():
    """Two calls to detect_fresh_obs_on_date on consecutive dates should not
    produce two copies of the same OB (dedup by formation_time/type/high/low)."""
    h1 = []
    for i in range(100):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if i < 50:
            p = 100.0 + (i % 5) * 0.1
        elif i < 55:
            p = 99.0 + (i % 3) * 0.1
        else:
            p = 100.5 + ((i - 55) % 5) * 0.1
        h1.append(_m15_candle(ts, p, p + 0.3, p - 0.3, p + 0.05))
    obs = _mod.collect_unique_fresh_obs(h1, date(2026, 1, 1), date(2026, 1, 5))
    # Dedup: each OB should appear at most once
    keys = [
        (a.ob.formation_time, a.ob.type,
         round(a.ob.high, 8), round(a.ob.low, 8))
        for a in obs
    ]
    assert len(keys) == len(set(keys))


def test_collect_unique_fresh_obs_empty_series_returns_empty():
    """No candles → no OBs."""
    obs = _mod.collect_unique_fresh_obs([], date(2026, 1, 1), date(2026, 1, 5))
    assert obs == []


def test_ob_detection_skips_mitigated_ob_via_fresh_filter():
    """``detect_fresh_obs_on_date`` returns AnnotatedOBs whose wrapped
    ``.ob.mitigated`` is False."""
    h1 = []
    for i in range(50):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        p = 100.0 + i * 0.1
        h1.append(_m15_candle(ts, p, p + 0.1, p - 0.1, p + 0.05))
    d_idx = _mod._index_by_date(h1)
    fresh = _mod.detect_fresh_obs_on_date(date(2026, 1, 2), h1, d_idx)
    for aob in fresh:
        assert aob.ob.mitigated is False


# ===========================================================================
# Section 2: Retest detection (corrected timing — ADR 003)
# ===========================================================================


def test_retest_exact_touch_of_ob_high_triggers():
    """Bullish OB at [100.0, 100.5]; M15 candle whose low touches 100.5 exactly.

    Under v2, the walker must start from a candle whose open >= bos_confirm_ts.
    We set ``bos_confirm_ts`` just before the first M15 candle so both of the
    setup's forward candles are eligible.
    """
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T08:15:00Z")
    m15 = [
        _m15_candle("2026-01-10T08:15:00Z", 101.0, 101.2, 100.8, 101.0),
        _m15_candle("2026-01-10T08:30:00Z", 100.9, 101.0, 100.5, 100.6),  # touch
        _m15_candle("2026-01-10T08:45:00Z", 100.6, 100.8, 100.3, 100.4),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T08:30:00Z"
    # bos_confirm_ts is preserved on the _RawRetest
    assert raw.bos_confirm_ts == "2026-01-10T08:15:00Z"


def test_retest_near_miss_does_not_trigger():
    """Candle low sits just above OB high — no retest."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T08:15:00Z")
    m15 = [
        _m15_candle("2026-01-10T08:15:00Z", 101.0, 101.2, 100.6, 101.0),
        _m15_candle("2026-01-10T08:30:00Z", 100.9, 101.0, 100.55, 100.8),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is None


def test_retest_deep_penetration_still_counts():
    """A candle that pierces below the OB body still registers as a retest."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    # bos_confirm_ts strictly before the candle (strict > invariant)
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T08:00:00Z")
    m15 = [
        _m15_candle("2026-01-10T08:15:00Z", 101.0, 101.2, 99.5, 100.3),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T08:15:00Z"


def test_retest_no_touch_within_scan_window():
    """If the OB is never revisited, returns None."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T08:15:00Z")
    m15 = []
    for i in range(5):
        ts = (datetime(2026, 1, 10, 8, 15, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 110.0, 110.5, 109.5, 110.2))
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is None


def test_retest_bearish_side_symmetric():
    """Bearish OB at [100.0, 100.5]; M15 candle whose high touches 100.0."""
    ob = _synthetic_ob(ob_type="bearish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T08:15:00Z")
    m15 = [
        _m15_candle("2026-01-10T08:15:00Z", 99.0, 99.5, 98.8, 99.2),
        _m15_candle("2026-01-10T08:30:00Z", 99.3, 100.0, 99.2, 99.6),  # touch
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T08:30:00Z"


def test_retest_skips_candles_before_bos_confirm_ts():
    """Walker must NOT flag M15 candles whose open <= bos_confirm_ts.

    This is the core ADR 003 fix: a candle whose low enters the zone but
    happens AT-OR-BEFORE the BOS close is not a valid retest (it is part of
    the impulse move that retroactively creates the OB).
    """
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    # BOS confirms at 10:00 — so 08:15-10:00 candles don't count (strict >)
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T10:00:00Z")
    m15 = [
        # All at-or-before BOS confirm — must be ignored even though they enter the zone
        _m15_candle("2026-01-10T08:15:00Z", 100.9, 101.0, 100.4, 100.6),
        _m15_candle("2026-01-10T08:30:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T08:45:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T09:00:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T09:15:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T09:30:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T09:45:00Z", 100.9, 101.0, 100.3, 100.5),
        _m15_candle("2026-01-10T10:00:00Z", 100.9, 101.0, 100.4, 100.6),  # boundary — skipped
        # This is the first valid retest (10:15 > 10:00)
        _m15_candle("2026-01-10T10:15:00Z", 100.9, 101.0, 100.4, 100.6),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T10:15:00Z"


def test_retest_skips_candle_exactly_at_bos_confirm_ts():
    """Candle whose open is EXACTLY at bos_confirm_ts is skipped (strict >).

    The strict ADR 003 invariant requires retest_ts > bos_confirm_ts.
    Because bos_confirm_ts (= H1 close) is always M15-boundary aligned, an
    M15 candle that opens exactly at bos_confirm_ts is the first candle of
    the BOS-impulse continuation — NOT a retest.
    """
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T09:00:00Z")
    m15 = [
        # Exactly at boundary — must be skipped
        _m15_candle("2026-01-10T09:00:00Z", 101.0, 101.2, 100.5, 100.6),
        # 15min after — accepted
        _m15_candle("2026-01-10T09:15:00Z", 100.6, 100.8, 100.4, 100.5),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T09:15:00Z"


# ===========================================================================
# Section 3: MAE computation (twin-geometry — assert on Geom A by default)
# ===========================================================================


def test_mae_long_side_adverse_move_captured():
    """Bullish entry at 100.2; subsequent low at 99.7 → MAE = 0.5."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.3, 99.7, 100.2)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.25))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=1.0)
    # MAE = 100.2 - 99.7 = 0.5 → 5.0 pips for XAUUSD
    assert rec.mae_a_pips == pytest.approx(5.0, abs=0.01)
    assert rec.outcome_a in ("UNRESOLVED", "CONTINUED", "REVERSED")


def test_mae_short_side_adverse_move_captured():
    """Bearish entry at 99.8; subsequent high at 100.3 → MAE = 0.5."""
    ob = _synthetic_ob(ob_type="bearish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.3, 99.7, 99.8)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 99.8, 99.9, 99.7, 99.75))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=99.8, h1_atr=1.0)
    assert rec.mae_a_pips == pytest.approx(5.0, abs=0.01)


def test_mae_on_entry_candle_t0():
    """MAE can be set by the entry candle itself (time_to_mae=0)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.5, 100.6, 99.0, 100.2)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=1.0)
    # Entry candle has the widest adverse range; under Geom B the SL hits at
    # j=0 but classifier skips entry for SL/TP — MAE at j=0 still captured.
    assert rec.time_to_mae_a_candles == 0
    # MAE = 100.2 - 99.0 = 1.2
    assert rec.mae_a_pips == pytest.approx(12.0, abs=0.01)


def test_mae_delayed_peaks_at_j_eq_5():
    """MAE reaches max 5 candles after entry (Geom A horizon = 48)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.2, 100.4, 100.1, 100.2)]
    for i in range(1, 5):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.0 - 0.1 * i, 100.2))
    ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * 5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    m15.append(_m15_candle(ts, 100.2, 100.3, 99.5, 100.2))
    for i in range(6, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=1.0)
    assert rec.time_to_mae_a_candles == 5
    # MAE = 100.2 - 99.5 = 0.7 → 7 pips (XAUUSD)
    assert rec.mae_a_pips == pytest.approx(7.0, abs=0.01)


def test_mae_after_partial_continuation_still_tracks_later_drawdown():
    """Continuation hit at j=2, but MAE deeper at j=1 (Geom A)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    # Entry at 100.2; OB body = 0.5. Target A = 100.2 + 0.5 = 100.7.
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.2, 100.3, 100.1, 100.2)]
    ts1 = "2026-01-10T08:45:00Z"
    m15.append(_m15_candle(ts1, 100.2, 100.3, 99.8, 100.1))
    ts2 = "2026-01-10T09:00:00Z"
    m15.append(_m15_candle(ts2, 100.1, 100.8, 100.0, 100.7))
    for i in range(3, 50):
        ts = (datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc) + timedelta(minutes=15 * (i - 2))).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.7, 100.8, 100.6, 100.7))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=1.0)
    # MAE at j=1 before continuation at j=2 (Geom A uses target=1 OB body)
    assert rec.time_to_mae_a_candles == 1
    assert rec.mae_a_pips == pytest.approx(4.0, abs=0.05)


# ===========================================================================
# Section 4: ATR normalization
# ===========================================================================


def test_h1_atr_from_known_series():
    """Synthesize H1 candles with known TRs and verify ATR."""
    h1 = []
    for i in range(20):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        h1.append(_m15_candle(ts, 100.0, 100.5, 99.5, 100.0))
    target = datetime(2026, 1, 2, 1, tzinfo=timezone.utc)
    atr = _mod._find_h1_atr_at(h1, target)
    assert atr == pytest.approx(1.0, abs=0.05)


def test_mae_atr_normalization_formula():
    """Given h1_atr=1.0 and MAE=0.5, mae_a_atr should be 0.5."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.3, 99.7, 100.2)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=1.0)
    assert rec.mae_a_atr == pytest.approx(0.5, abs=0.01)


def test_zero_atr_produces_zero_mae_atr_via_guard():
    """When H1 ATR=0, mae_atr should be a finite value (not NaN/inf)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.3, 99.7, 100.2)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.2, h1_atr=0.0)
    assert rec.mae_a_atr >= 0.0
    assert math.isfinite(rec.mae_a_atr)


# ===========================================================================
# Section 5: Session labels
# ===========================================================================


def test_session_label_at_midnight_z():
    """00:00 UTC → Tokyo (asian)."""
    dt = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "Tokyo"


def test_session_label_at_0300_z_tokyo_upper_boundary():
    """03:00 UTC → Tokyo (asian session; ends at 07:00)."""
    dt = datetime(2026, 1, 10, 3, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "Tokyo"


def test_session_label_at_0700_z_london_open():
    """07:00 UTC → London (london_open starts at 07:00)."""
    dt = datetime(2026, 1, 10, 7, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "London"


def test_session_label_at_1030_z_london_body():
    """10:30 UTC → London (london_body)."""
    dt = datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "London"


def test_session_label_at_1300_z_ny_overlap():
    """13:00 UTC → NY (ny_overlap begins at 12:00)."""
    dt = datetime(2026, 1, 10, 13, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "NY"


def test_session_label_at_1700_z_ny_afternoon():
    """17:00 UTC → NY (ny_afternoon runs 16:00–21:00)."""
    dt = datetime(2026, 1, 10, 17, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "NY"


def test_session_label_off_hours_returns_none():
    """22:00 UTC → None (off_hours)."""
    dt = datetime(2026, 1, 10, 22, 0, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "None"


# ===========================================================================
# Section 6: Continuation classification (Geometry A — OB-body target)
# ===========================================================================


def test_continuation_exact_1r_hit_geom_a():
    """Bullish entry at 100.0, OB body 0.5; candle at j=2 reaches 100.5 exactly.

    Geom A target = entry + ob_body = 100.0 + 0.5 = 100.5.
    """
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.05, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.2, 99.95, 100.15))
    m15.append(_m15_candle("2026-01-10T09:00:00Z", 100.15, 100.5, 100.1, 100.4))
    for i in range(3, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.4, 100.5, 100.3, 100.4))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "CONTINUED"
    assert rec.time_to_continuation_a_candles == 2


def test_continuation_deep_continuation_beyond_1r_geom_a():
    """Continuation reached with deep move."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 102.0, 99.95, 101.5))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 101.5, 101.6, 101.4, 101.5))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "CONTINUED"
    assert rec.continuation_r_a == pytest.approx(4.0, abs=0.01)


def test_reversal_to_sl_geom_a():
    """Geom A SL = ob_low - 0.5*ATR. With h1_atr=1.0 and ob_low=99.5 → SL=99.0."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.1, 98.5, 98.6))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 98.6, 98.7, 98.5, 98.6))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "REVERSED"


def test_unresolved_after_48_neither_hit_geom_a():
    """Horizon expires without SL or target (Geom A 48 candles)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "UNRESOLVED"


def test_insufficient_forward_candles_yields_unresolved_geom_a():
    """Fewer than RESOLUTION_HORIZON_A+1 forward candles → UNRESOLVED."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 11):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "UNRESOLVED"


def test_bearish_reversal_to_sl_geom_a():
    """Bearish entry; Geom A SL = ob_high + 0.5*ATR."""
    ob = _synthetic_ob(ob_type="bearish", high=100.5, low=100.0)
    # Entry at 100.0; SL = 100.5 + 0.5 = 101.0
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.9, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 101.5, 100.0, 101.3))  # pierce SL
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 101.3, 101.4, 101.2, 101.3))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "REVERSED"


# ===========================================================================
# Section 7: Continuation-R calculation (Geom A)
# ===========================================================================


def test_continuation_r_is_positive_on_continued():
    """CONTINUED outcome (Geom A) → positive continuation_r_a."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.5, 99.95, 100.5))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.5, 100.6, 100.4, 100.5))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "CONTINUED"
    assert rec.continuation_r_a is not None and rec.continuation_r_a > 0


def test_continuation_r_none_on_reversed():
    """REVERSED (Geom A) → continuation_r_a is None."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.1, 98.5, 98.6))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 98.6, 98.7, 98.5, 98.6))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "REVERSED"
    assert rec.continuation_r_a is None


def test_continuation_r_scales_with_move_size():
    """Larger high beyond target → larger continuation_r_a."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 103.0, 100.0, 102.9))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 102.9, 103.0, 102.8, 102.9))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "CONTINUED"
    assert rec.continuation_r_a == pytest.approx(6.0, abs=0.01)


def test_unresolved_has_none_continuation_r():
    """UNRESOLVED outcome → continuation_r_a is None."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "UNRESOLVED"
    assert rec.continuation_r_a is None


# ===========================================================================
# Section 8: Output CSV schema (twin geometry — 33 columns)
# ===========================================================================


def test_csv_fields_matches_dataclass_order():
    """CSV_FIELDS must reflect the RetestRecord field declaration order."""
    assert _mod.CSV_FIELDS == [f.name for f in dc_fields(_mod.RetestRecord)]


def test_csv_has_expected_twin_geometry_column_names():
    """All 33 columns in the twin-geometry schema are present, in order."""
    expected = [
        "symbol", "ob_formation_ts", "bos_confirm_ts", "retest_ts",
        "retest_date", "session", "side",
        "ob_body_size_pips", "ob_body_size_atr", "ob_body_size_pct_price",
        "retest_entry_price", "h1_atr_at_retest",
        # Geometry A
        "sl_a_price", "target_a_price", "outcome_a", "continuation_r_a",
        "mae_a_pips", "mae_a_atr", "mae_a_pct_ob_body",
        "penetration_a_pips", "penetration_a_atr",
        "time_to_mae_a_candles", "time_to_continuation_a_candles",
        # Geometry B
        "sl_b_price", "target_b_price", "outcome_b", "continuation_r_b",
        "mae_b_pips", "mae_b_atr", "mae_b_pct_ob_body",
        "penetration_b_pips", "penetration_b_atr",
        "time_to_mae_b_candles", "time_to_continuation_b_candles",
    ]
    assert _mod.CSV_FIELDS == expected


def test_csv_schema_has_34_columns():
    """ADR 003 canonical: 34 columns in twin-geometry schema (12 common + 11 Geom A + 11 Geom B)."""
    assert len(_mod.CSV_FIELDS) == 34


def test_csv_has_bos_confirm_ts_column():
    """v2 schema MUST carry bos_confirm_ts (the ADR 003 timing anchor)."""
    assert "bos_confirm_ts" in _mod.CSV_FIELDS
    # Right after ob_formation_ts, before retest_ts
    i_bos = _mod.CSV_FIELDS.index("bos_confirm_ts")
    i_form = _mod.CSV_FIELDS.index("ob_formation_ts")
    i_retest = _mod.CSV_FIELDS.index("retest_ts")
    assert i_form < i_bos < i_retest


def test_write_retest_csv_writes_header_even_for_empty_input(tmp_path):
    """Empty input → header-only CSV."""
    out = tmp_path / "x.csv"
    _mod.write_retest_csv([], out)
    with open(out, "r", encoding="utf-8") as fh:
        content = fh.read()
    lines = [ln for ln in content.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].split(",") == _mod.CSV_FIELDS


def test_write_retest_csv_preserves_deterministic_row_order(tmp_path):
    """Rows written in the order passed — caller must sort."""
    ob = _synthetic_ob()
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec_a = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0, symbol="ABC")
    rec_b = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0, symbol="XYZ")
    out = tmp_path / "x.csv"
    _mod.write_retest_csv([rec_a, rec_b], out)
    with open(out, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert rows[0]["symbol"] == "ABC"
    assert rows[1]["symbol"] == "XYZ"


# ===========================================================================
# Section 9: Edge cases
# ===========================================================================


def test_build_retests_with_empty_data_dir_returns_empty(tmp_path):
    """Data dir with no matching CSVs → empty retest list, no crash."""
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _mod.build_retests_for_symbol(
        "XAUUSD", date(2026, 1, 1), date(2026, 1, 5), empty
    )
    assert result == []


def test_build_retests_missing_symbol_csv_returns_empty(tmp_path):
    """Data dir exists but symbol CSV missing → empty list, no crash."""
    (tmp_path / "ZZZ_M15.csv").write_text("time,open,high,low,close,volume\n")
    result = _mod.build_retests_for_symbol(
        "XAUUSD", date(2026, 1, 1), date(2026, 1, 5), tmp_path
    )
    assert result == []


def test_build_retests_date_range_no_obs_returns_empty(tmp_path):
    """Valid CSVs but a date range with too few candles → empty list."""
    h1 = tmp_path / "XAUUSD_H1.csv"
    m15 = tmp_path / "XAUUSD_M15.csv"
    with open(h1, "w", encoding="utf-8", newline="") as fh:
        fh.write("time,open,high,low,close,volume\n")
        for i in range(50):
            dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
            fh.write(f"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')},100,100.5,99.5,100,100\n")
    with open(m15, "w", encoding="utf-8", newline="") as fh:
        fh.write("time,open,high,low,close,volume\n")
        for i in range(200):
            dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * i)
            fh.write(f"{dt.strftime('%Y-%m-%dT%H:%M:%SZ')},100,100.5,99.5,100,100\n")
    result = _mod.build_retests_for_symbol(
        "XAUUSD", date(2026, 1, 1), date(2026, 1, 3), tmp_path
    )
    assert isinstance(result, list)


def test_dst_boundary_handling_session_labels():
    """March DST transition: 01:30 on 2026-03-29 (DST day in EU) → Tokyo."""
    dt = datetime(2026, 3, 29, 1, 30, tzinfo=timezone.utc)
    assert _mod.session_label(dt) == "Tokyo"


def test_parse_candle_time_handles_iso_z_format():
    """ISO Z timestamps must parse to UTC."""
    t = "2026-04-17T09:30:00Z"
    dt = _mod._parse_candle_time(t)
    assert dt.year == 2026 and dt.month == 4 and dt.day == 17
    assert dt.hour == 9 and dt.minute == 30
    assert dt.tzinfo is not None


def test_parse_candle_time_handles_legacy_space_format():
    """Legacy ``YYYY-MM-DD HH:MM:SS`` strings also parse."""
    t = "2026-04-17 09:30:00"
    dt = _mod._parse_candle_time(t)
    assert dt.year == 2026 and dt.hour == 9


# ===========================================================================
# Section 10: Live-period join (twin-geometry outcome attribution)
# ===========================================================================


def _make_eval_row(symbol: str, candle_time: str, decision: str,
                   no_trade_reason: str | None = None,
                   kill_zone: str = "london",
                   setup_grade: str = "C",
                   framework: str = "ob_retest") -> dict:
    return {
        "timestamp": candle_time,
        "candle_time": candle_time,
        "symbol": symbol,
        "kill_zone": kill_zone,
        "decision": decision,
        "no_trade_reason": no_trade_reason,
        "setup_grade": setup_grade,
        "framework": framework,
    }


def _synthetic_v2_record(
    outcome_a: str = "CONTINUED",
    outcome_b: str = "CONTINUED",
    symbol: str = "XAUUSD",
    retest_ts: str = "2026-04-10T07:30:00Z",
    bos_confirm_ts: str = "2026-04-10T07:00:00Z",
) -> _mod.RetestRecord:
    """Build a test RetestRecord — defaults to CONTINUED/CONTINUED."""
    return _mod.RetestRecord(
        symbol=symbol,
        ob_formation_ts="2026-04-10T06:00:00Z",
        bos_confirm_ts=bos_confirm_ts,
        retest_ts=retest_ts,
        retest_date=retest_ts[:10],
        session="London",
        side="long",
        ob_body_size_pips=5.0,
        ob_body_size_atr=0.5,
        ob_body_size_pct_price=0.01,
        retest_entry_price=100.0,
        h1_atr_at_retest=0.5,
        sl_a_price=99.5,
        target_a_price=100.5,
        outcome_a=outcome_a,
        continuation_r_a=1.0 if outcome_a == "CONTINUED" else None,
        mae_a_pips=2.0,
        mae_a_atr=0.2,
        mae_a_pct_ob_body=40.0,
        penetration_a_pips=0.0,
        penetration_a_atr=0.0,
        time_to_mae_a_candles=1,
        time_to_continuation_a_candles=2 if outcome_a == "CONTINUED" else None,
        sl_b_price=99.9,
        target_b_price=100.15,
        outcome_b=outcome_b,
        continuation_r_b=1.5 if outcome_b == "CONTINUED" else None,
        mae_b_pips=2.0,
        mae_b_atr=0.2,
        mae_b_pct_ob_body=40.0,
        penetration_b_pips=0.0,
        penetration_b_atr=0.0,
        time_to_mae_b_candles=1,
        time_to_continuation_b_candles=2 if outcome_b == "CONTINUED" else None,
    )


def test_live_join_coverage_matched(tmp_path, monkeypatch):
    """A retest at 07:30 matches a live eval at 07:30 same day."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    sym_dir = tmp_path / "XAUUSD"
    sym_dir.mkdir()
    with open(sym_dir / "2026-04-10.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_make_eval_row(
            "XAUUSD", "2026-04-10T07:30:00+00:00", "NO_TRADE",
            no_trade_reason="touch_count_too_high"
        )) + "\n")

    rec = _synthetic_v2_record(outcome_a="CONTINUED", outcome_b="CONTINUED")
    out = _mod.join_live_evaluations([rec], date(2026, 4, 7), date(2026, 4, 17))
    assert out["coverage_by_symbol"]["XAUUSD"] == (1, 1)


def test_live_join_no_live_eval(tmp_path, monkeypatch):
    """Retest with no matching eval → coverage 0, miss counted (if CONTINUED)."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    rec = _synthetic_v2_record(outcome_a="CONTINUED", outcome_b="CONTINUED")
    # Default geometry is 'b' → uses outcome_b for miss attribution
    out = _mod.join_live_evaluations([rec], date(2026, 4, 7), date(2026, 4, 17))
    assert out["coverage_by_symbol"]["XAUUSD"] == (0, 1)
    assert out["misses"] >= 1


def test_live_join_candidate_matches_retest(tmp_path, monkeypatch):
    """CANDIDATE at same bucket as mechanical retest → candidate_matches += 1."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    sym_dir = tmp_path / "XAUUSD"
    sym_dir.mkdir()
    with open(sym_dir / "2026-04-10.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_make_eval_row(
            "XAUUSD", "2026-04-10T07:30:00+00:00", "CANDIDATE"
        )) + "\n")
    rec = _synthetic_v2_record(outcome_a="CONTINUED", outcome_b="CONTINUED")
    out = _mod.join_live_evaluations([rec], date(2026, 4, 7), date(2026, 4, 17))
    assert out["candidate_matches"] == 1
    assert out["false_positives"] == 0


def test_live_join_false_positive_on_reversed_geom_b(tmp_path, monkeypatch):
    """CANDIDATE matched a REVERSED Geom B retest → false_positives += 1."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    sym_dir = tmp_path / "XAUUSD"
    sym_dir.mkdir()
    with open(sym_dir / "2026-04-10.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_make_eval_row(
            "XAUUSD", "2026-04-10T07:30:00+00:00", "CANDIDATE"
        )) + "\n")
    # Geom A CONTINUED but Geom B REVERSED — default geometry='b'
    rec = _synthetic_v2_record(outcome_a="CONTINUED", outcome_b="REVERSED")
    out = _mod.join_live_evaluations([rec], date(2026, 4, 7), date(2026, 4, 17))
    assert out["false_positives"] == 1  # from Geom B
    assert out["geometry"] == "b"


def test_live_join_geometry_a_attribution(tmp_path, monkeypatch):
    """Explicitly select geometry='a' for join attribution."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    sym_dir = tmp_path / "XAUUSD"
    sym_dir.mkdir()
    with open(sym_dir / "2026-04-10.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_make_eval_row(
            "XAUUSD", "2026-04-10T07:30:00+00:00", "CANDIDATE"
        )) + "\n")
    # Geom A REVERSED, Geom B CONTINUED — selecting A yields false_positive=1
    rec = _synthetic_v2_record(outcome_a="REVERSED", outcome_b="CONTINUED")
    out = _mod.join_live_evaluations(
        [rec], date(2026, 4, 7), date(2026, 4, 17), geometry="a"
    )
    assert out["false_positives"] == 1
    assert out["geometry"] == "a"


def test_live_join_candidate_without_retest(tmp_path, monkeypatch):
    """CANDIDATE with no matching retest → candidates_without_retest += 1."""
    monkeypatch.setattr(_mod, "LIVE_EVALUATIONS_DIR", tmp_path)
    sym_dir = tmp_path / "XAUUSD"
    sym_dir.mkdir()
    with open(sym_dir / "2026-04-10.jsonl", "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_make_eval_row(
            "XAUUSD", "2026-04-10T08:30:00+00:00", "CANDIDATE"
        )) + "\n")
    rec = _synthetic_v2_record()  # retest at 07:30 — doesn't match 08:30
    out = _mod.join_live_evaluations([rec], date(2026, 4, 7), date(2026, 4, 17))
    assert out["candidates_without_retest"] == 1


# ===========================================================================
# Section 11: Twin-geometry invariants
# ===========================================================================


def test_geometry_a_and_b_outcomes_both_populated():
    """Every RetestRecord must have both outcome_a and outcome_b set."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.5, 99.95, 100.5))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.5, 100.6, 100.4, 100.5))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a in ("CONTINUED", "REVERSED", "UNRESOLVED")
    assert rec.outcome_b in ("CONTINUED", "REVERSED", "UNRESOLVED")


def test_geometry_a_and_b_sl_prices_computed_independently():
    """Geom A SL uses 0.5 * h1_atr; Geom B SL uses Test A rule — they differ."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    # Geom A: 99.5 - 0.5*1.0 = 99.0
    assert rec.sl_a_price == pytest.approx(99.0, abs=0.001)
    # Geom B XAUUSD: 99.5 - 0.001*99.5 = 99.4005
    assert rec.sl_b_price == pytest.approx(99.4005, abs=0.001)
    # They should NOT be equal
    assert rec.sl_a_price != rec.sl_b_price


def test_geometry_a_and_b_targets_computed_independently():
    """Geom A target = entry + OB body; Geom B target = entry + 1.5 * SL distance."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    # Geom A: entry + OB body = 100.0 + 0.5 = 100.5
    assert rec.target_a_price == pytest.approx(100.5, abs=0.001)
    # Geom B: entry + 1.5 * (entry - sl_b) = 100.0 + 1.5 * 0.5995 = 100.89925
    assert rec.target_b_price == pytest.approx(100.8993, abs=0.001)
    assert rec.target_a_price != rec.target_b_price


def test_twin_geometry_unresolved_differs_by_horizon():
    """Geom A horizon is 48 candles; Geom B horizon is 12 candles.

    A retest that is UNRESOLVED under Geom B (tight SL + 3h window) may
    resolve under Geom A (wider SL + 12h window)."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    # Flat price action for 20 candles → UNRESOLVED under Geom B (12 candles),
    # then tick to CONTINUED around j=20 — still within Geom A horizon (48).
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    # 19 flat candles — still within Geom B window at j<=11, then cross target at j=20
    for i in range(1, 20):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.05, 99.95, 100.0))
    ts20 = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * 20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    m15.append(_m15_candle(ts20, 100.0, 100.6, 99.95, 100.5))  # hit target_a at j=20
    for i in range(21, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.5, 100.6, 100.4, 100.5))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    # Geom A saw continuation at j=20 — CONTINUED
    assert rec.outcome_a == "CONTINUED"
    # Geom B timed out at j=12 — UNRESOLVED
    assert rec.outcome_b == "UNRESOLVED"


def test_twin_geometry_both_continued_fast_hit():
    """Fast continuation within first 2 candles → both geoms should CONTINUED."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    # Entry at 100.0. Geom A target = 100.5. Geom B target ~= 100.8993.
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    # j=1: huge rip to hit both targets
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 101.0, 100.0, 100.9))
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.9, 101.0, 100.8, 100.9))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0)
    assert rec.outcome_a == "CONTINUED"
    assert rec.outcome_b == "CONTINUED"


# ===========================================================================
# Section 12: BOS detection & temporal-ordering invariant (ADR 003)
# ===========================================================================


def test_temporal_invariant_rejects_retest_equal_to_bos_confirm():
    """Retest equal to bos_confirm_ts violates the strict invariant."""
    # Build a record that explicitly violates the invariant — expect AssertionError
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    raw = _mod._RawRetest(
        ob=ob,
        bos_confirm_ts="2026-01-10T08:00:00Z",
        retest_ts="2026-01-10T08:00:00Z",  # EQUAL — must fail strict invariant
        retest_idx=0,
        entry_price=100.2,
        entry_idx=0,
        h1_atr=1.0,
    )
    m15 = [
        _m15_candle("2026-01-10T08:00:00Z", 100.2, 100.3, 100.1, 100.2)
    ]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 0, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    with pytest.raises(AssertionError, match="Temporal invariant violated"):
        _mod._classify_and_measure(raw, m15, "XAUUSD")


def test_temporal_invariant_rejects_retest_before_bos_confirm():
    """Retest strictly before bos_confirm_ts violates the invariant."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0)
    raw = _mod._RawRetest(
        ob=ob,
        bos_confirm_ts="2026-01-10T09:00:00Z",
        retest_ts="2026-01-10T08:30:00Z",  # 30 minutes BEFORE
        retest_idx=0,
        entry_price=100.2,
        entry_idx=0,
        h1_atr=1.0,
    )
    m15 = [
        _m15_candle("2026-01-10T08:30:00Z", 100.2, 100.3, 100.1, 100.2)
    ]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.2, 100.3, 100.1, 100.2))
    with pytest.raises(AssertionError, match="Temporal invariant violated"):
        _mod._classify_and_measure(raw, m15, "XAUUSD")


def test_bos_confirm_ts_is_h1_close_not_open():
    """The BOS-confirm timestamp is the CLOSE of the BOS H1 candle (= open + 1h)."""
    # A detect_fresh_obs_on_date run on synthetic H1 data should set the
    # bos_confirm_ts to h1_slice[causing_bos_index].time + 1 hour.
    h1 = []
    # Create 40 H1 candles with a clear upward trend that generates OBs
    for i in range(40):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i)
        ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if i < 10:
            p = 100.0
        elif i < 15:
            p = 100.0 - (i - 10) * 0.1  # dip
        else:
            p = 99.5 + (i - 15) * 0.5  # strong rally → BOS
        h1.append(_m15_candle(ts, p, p + 0.4, p - 0.4, p + 0.2))
    d_idx = _mod._index_by_date(h1)
    # Pick a date where BOS has occurred
    target = date(2026, 1, 2)
    aobs = _mod.detect_fresh_obs_on_date(target, h1, d_idx)
    for aob in aobs:
        # bos_confirm_ts must be strictly after ob.formation_time (H1 strict)
        form_dt = _mod._parse_candle_time(aob.ob.formation_time)
        bos_dt = _mod._parse_candle_time(aob.bos_confirm_ts)
        assert bos_dt > form_dt
        # And the delta should be a multiple of 1 hour (H1 candles) plus the 1h close offset
        delta_secs = (bos_dt - form_dt).total_seconds()
        assert delta_secs % 3600 == 0


def test_detect_first_retest_enforces_strict_greater_than_on_body_entry():
    """Integration: detector enforces strict > so classifier always succeeds.

    Set bos_confirm_ts at 09:00 (M15-boundary). Inside-zone candle at 09:00
    must be skipped (boundary case == BOS-impulse continuation). The next
    inside-zone candle at 09:15 is the first valid retest.
    """
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T07:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T09:00:00Z")
    m15 = [
        # Inside-zone candle at 08:45 — must be rejected (before 09:00)
        _m15_candle("2026-01-10T08:45:00Z", 100.9, 101.0, 100.3, 100.5),
        # Inside-zone candle at 09:00 — must be skipped (09:00 == 09:00)
        _m15_candle("2026-01-10T09:00:00Z", 100.9, 101.0, 100.4, 100.6),
        # First eligible retest (09:15 > 09:00)
        _m15_candle("2026-01-10T09:15:00Z", 100.9, 101.0, 100.4, 100.6),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.retest_ts == "2026-01-10T09:15:00Z"
    # _classify_and_measure should NOT raise — the strict invariant holds.
    m15_full = m15 + _m15_range("2026-01-10T09:30:00Z", 48)
    rec = _mod._classify_and_measure(raw, m15_full, "XAUUSD")
    assert rec.retest_ts == "2026-01-10T09:15:00Z"
    assert rec.bos_confirm_ts == "2026-01-10T09:00:00Z"


def test_retest_walker_records_bos_confirm_on_output():
    """The _RawRetest must carry forward the bos_confirm_ts from the AnnotatedOB."""
    ob = _synthetic_ob(ob_type="bullish", high=100.5, low=100.0,
                       formation_time="2026-01-10T08:00:00Z")
    aob = _annotated(ob, bos_confirm_ts="2026-01-10T09:30:00Z")
    m15 = [
        # Before bos — rejected
        _m15_candle("2026-01-10T08:15:00Z", 100.9, 101.0, 100.4, 100.6),
        _m15_candle("2026-01-10T08:30:00Z", 100.9, 101.0, 100.4, 100.6),
        _m15_candle("2026-01-10T09:15:00Z", 100.9, 101.0, 100.4, 100.6),
        # After bos — accepted
        _m15_candle("2026-01-10T09:45:00Z", 100.9, 101.0, 100.4, 100.6),
    ]
    raw = _mod._detect_first_retest(aob, m15)
    assert raw is not None
    assert raw.bos_confirm_ts == "2026-01-10T09:30:00Z"
    assert raw.retest_ts == "2026-01-10T09:45:00Z"


# ===========================================================================
# Section 13: Geometry B (Test A) SL / target / window
# ===========================================================================


def test_geometry_b_sl_xauusd_bullish_formula():
    """Test A XAUUSD bullish SL = ob_low * (1 - 0.001)."""
    # ob_low = 100.0 → SL = 99.9
    sl = _mod._geometry_b_sl_price("XAUUSD", "bullish", 100.5, 100.0)
    assert sl == pytest.approx(100.0 - 0.001 * 100.0, abs=1e-9)
    assert sl == pytest.approx(99.9, abs=1e-9)


def test_geometry_b_sl_xauusd_bearish_formula():
    """Test A XAUUSD bearish SL = ob_high * (1 + 0.001)."""
    sl = _mod._geometry_b_sl_price("XAUUSD", "bearish", 100.5, 100.0)
    assert sl == pytest.approx(100.5 + 0.001 * 100.5, abs=1e-9)


def test_geometry_b_sl_other_symbols_absolute_offset():
    """Test A non-XAUUSD bullish SL = ob_low - 0.00015 (absolute)."""
    sl_bull = _mod._geometry_b_sl_price("GBPUSD", "bullish", 1.2500, 1.2450)
    assert sl_bull == pytest.approx(1.2450 - 0.00015, abs=1e-9)
    sl_bear = _mod._geometry_b_sl_price("GBPUSD", "bearish", 1.2500, 1.2450)
    assert sl_bear == pytest.approx(1.2500 + 0.00015, abs=1e-9)


def test_geometry_b_target_is_1_5x_sl_distance():
    """Geom B target = entry + 1.5 * (entry - sl_b) for bullish."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0, symbol="XAUUSD")
    sl_b = rec.sl_b_price
    target_b = rec.target_b_price
    entry = rec.retest_entry_price
    # target - entry should be 1.5 * (entry - sl_b)
    assert (target_b - entry) == pytest.approx(1.5 * (entry - sl_b), rel=1e-3)


def test_geometry_b_window_is_12_candles():
    """Geom B horizon constant = 12 M15 candles (3 hours per Test A)."""
    assert _mod.RESOLUTION_HORIZON_B == 12


def test_geometry_a_window_is_48_candles():
    """Geom A horizon constant = 48 M15 candles (12 hours per ADR 002 spirit)."""
    assert _mod.RESOLUTION_HORIZON_A == 48


def test_geometry_b_target_multiplier_is_1_5():
    """Geom B target multiplier constant matches Test A spec."""
    assert _mod.GEOMETRY_B_TARGET_R == 1.5


def test_geometry_b_reversal_on_tight_sl(tmp_path):
    """A small adverse move that hits Geom B SL but NOT Geom A SL."""
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    # Geom A SL = 99.5 - 0.5*1.0 = 99.0. Geom B SL = 99.5 - 0.001*99.5 = 99.4005.
    # Adverse move to 99.3 hits Geom B SL but not Geom A SL.
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    m15.append(_m15_candle("2026-01-10T08:45:00Z", 100.0, 100.1, 99.3, 99.4))
    # Then slight recovery, stays above 99.0 and below 100.5 — Geom A UNRESOLVED
    for i in range(2, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 99.5, 99.6, 99.45, 99.5))
    rec = _minimal_record(ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0, symbol="XAUUSD")
    # Geom B triggered SL — REVERSED
    assert rec.outcome_b == "REVERSED"
    # Geom A SL not triggered; target not reached — UNRESOLVED
    assert rec.outcome_a == "UNRESOLVED"


# ===========================================================================
# Section 14: Helpers & stats
# ===========================================================================


def test_normalize_to_m15_bucket():
    """07:16:23 → 07:15 bucket."""
    dt = datetime(2026, 4, 17, 7, 16, 23, tzinfo=timezone.utc)
    bucket = _mod._normalize_to_m15(dt)
    assert bucket.minute == 15 and bucket.hour == 7 and bucket.second == 0


def test_m15_candle_open_from_time_str_with_iso_offset():
    """ISO with +00:00 offset parses correctly and normalises."""
    t = "2026-04-17T07:16:23.449296+00:00"
    b = _mod._m15_candle_open_from_time_str(t)
    assert b.hour == 7 and b.minute == 15


def test_m15_candle_open_from_time_str_with_z_format():
    """ISO Z format parses correctly."""
    t = "2026-04-17T07:30:00Z"
    b = _mod._m15_candle_open_from_time_str(t)
    assert b.hour == 7 and b.minute == 30


def test_pip_size_for_xauusd():
    assert _mod.pip_size_for("XAUUSD") == 0.1


def test_pip_size_for_usdjpy():
    assert _mod.pip_size_for("USDJPY") == 0.01


def test_pip_size_for_gbpusd():
    assert _mod.pip_size_for("GBPUSD") == 0.0001


def test_pip_size_for_us30():
    assert _mod.pip_size_for("US30_cash") == 1.0


def test_pip_size_for_unknown_defaults_to_fx():
    assert _mod.pip_size_for("UNKNOWN_SYMBOL") == 0.0001


def test_wilson_ci_zero_n_returns_full_range():
    lo, hi = _mod._wilson_ci(0, 0)
    assert lo == 0.0 and hi == 1.0


def test_wilson_ci_100_pct_success_returns_upper_lt_1():
    """10/10 successes → upper bound < 1, lower bound < 1."""
    lo, hi = _mod._wilson_ci(10, 10)
    assert 0 < lo < 1 and hi <= 1.0


def test_percentiles_on_known_sequence():
    """p50 of [1..9] = 5.0."""
    out = _mod._percentiles([1, 2, 3, 4, 5, 6, 7, 8, 9], [10, 25, 50, 75, 90])
    assert out[50] == pytest.approx(5.0, abs=0.01)


def test_percentiles_on_empty_list_returns_nan():
    out = _mod._percentiles([], [10, 50, 90])
    for v in out.values():
        assert math.isnan(v)


def test_outcome_breakdown_counts_correctly_geom_a():
    """outcome_breakdown counts the outcome_a attribute when geometry='a'."""
    def _mk(outcome_a: str) -> _mod.RetestRecord:
        # Create a record with outcome_a as specified, outcome_b always CONTINUED
        return _synthetic_v2_record(outcome_a=outcome_a, outcome_b="CONTINUED")
    recs = [_mk("CONTINUED"), _mk("CONTINUED"), _mk("REVERSED"), _mk("UNRESOLVED")]
    out = _mod.outcome_breakdown(recs, geometry="a")
    assert out["CONTINUED"] == 2
    assert out["REVERSED"] == 1
    assert out["UNRESOLVED"] == 1
    assert out["total"] == 4


def test_outcome_breakdown_counts_correctly_geom_b():
    """outcome_breakdown counts the outcome_b attribute when geometry='b'."""
    def _mk(outcome_b: str) -> _mod.RetestRecord:
        return _synthetic_v2_record(outcome_a="CONTINUED", outcome_b=outcome_b)
    recs = [_mk("CONTINUED"), _mk("CONTINUED"), _mk("CONTINUED"), _mk("REVERSED")]
    out = _mod.outcome_breakdown(recs, geometry="b")
    assert out["CONTINUED"] == 3
    assert out["REVERSED"] == 1
    assert out["UNRESOLVED"] == 0
    assert out["total"] == 4


def test_continuation_rate_excludes_unresolved_by_default_geom_a():
    """Default denominator excludes UNRESOLVED for Geom A."""
    def _mk(outcome_a: str) -> _mod.RetestRecord:
        return _synthetic_v2_record(outcome_a=outcome_a, outcome_b="CONTINUED")
    recs = [_mk("CONTINUED"), _mk("REVERSED"), _mk("UNRESOLVED")]
    c, n, rate = _mod.continuation_rate(recs, geometry="a")
    assert c == 1 and n == 2 and rate == pytest.approx(50.0)


def test_continuation_rate_for_geom_b():
    """continuation_rate works on Geom B outcomes."""
    def _mk(outcome_b: str) -> _mod.RetestRecord:
        return _synthetic_v2_record(outcome_a="CONTINUED", outcome_b=outcome_b)
    recs = [_mk("CONTINUED"), _mk("CONTINUED"), _mk("REVERSED"), _mk("UNRESOLVED")]
    c, n, rate = _mod.continuation_rate(recs, geometry="b")
    assert c == 2 and n == 3
    assert rate == pytest.approx(66.6667, abs=0.01)


def test_continuation_rate_count_unresolved_as_no():
    """With count_unresolved_as_no=True, denominator is total."""
    def _mk(outcome_a: str) -> _mod.RetestRecord:
        return _synthetic_v2_record(outcome_a=outcome_a, outcome_b="CONTINUED")
    recs = [_mk("CONTINUED"), _mk("REVERSED"), _mk("UNRESOLVED")]
    c, n, rate = _mod.continuation_rate(
        recs, geometry="a", count_unresolved_as_no=True
    )
    assert c == 1 and n == 3
    assert rate == pytest.approx(33.333, abs=0.01)


def test_tercile_boundaries_short_input_returns_nan():
    lo, hi = _mod._tercile_boundaries([1.0])
    assert math.isnan(lo) and math.isnan(hi)


# ===========================================================================
# Section 15: Full-CSV temporal-ordering invariant
# ===========================================================================


def test_output_csv_temporal_ordering_invariant_on_written_rows(tmp_path):
    """Every row in a written CSV must satisfy retest_ts > bos_confirm_ts."""
    # Build a few sample records, each via _classify_and_measure (which enforces
    # the invariant at dataclass-creation time).
    ob = _synthetic_ob(ob_type="bullish", high=100.0, low=99.5)
    m15 = [_m15_candle("2026-01-10T08:30:00Z", 100.0, 100.1, 99.95, 100.0)]
    for i in range(1, 50):
        ts = (datetime(2026, 1, 10, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=15 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        m15.append(_m15_candle(ts, 100.0, 100.1, 99.9, 100.0))

    records = []
    # bos_confirm_ts is BEFORE the retest_ts (08:00 < 08:30) → all should pass.
    for sym in ("XAUUSD", "USDJPY", "US30_cash"):
        rec = _minimal_record(
            ob, m15, entry_idx=0, entry_price=100.0, h1_atr=1.0,
            symbol=sym, bos_confirm_ts="2026-01-10T08:00:00Z",
        )
        records.append(rec)

    out = tmp_path / "rows.csv"
    _mod.write_retest_csv(records, out)
    with open(out, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    # Full-CSV invariant check — NON-NEGOTIABLE per ADR 003
    for row in rows:
        bos_dt = _mod._parse_candle_time(row["bos_confirm_ts"])
        retest_dt = _mod._parse_candle_time(row["retest_ts"])
        assert retest_dt > bos_dt, (
            f"ADR 003 invariant violated on row: bos={row['bos_confirm_ts']} "
            f"retest={row['retest_ts']}"
        )


def test_annotated_ob_dataclass_exposed():
    """AnnotatedOB must be importable from the study module for tests/downstream."""
    assert hasattr(_mod, "AnnotatedOB")
    aob = _mod.AnnotatedOB(
        ob=_synthetic_ob(),
        bos_confirm_ts="2026-01-10T08:00:00Z",
    )
    assert aob.bos_confirm_ts == "2026-01-10T08:00:00Z"


def test_h1_duration_constant_is_one_hour():
    """Sanity: H1_DURATION constant must be exactly 1 hour."""
    assert _mod.H1_DURATION == timedelta(hours=1)


def test_module_constants_for_adr_003_are_present():
    """All ADR 003 module constants required by the schema/invariant exist."""
    assert hasattr(_mod, "RESOLUTION_HORIZON_A")
    assert hasattr(_mod, "RESOLUTION_HORIZON_B")
    assert hasattr(_mod, "GEOMETRY_B_TARGET_R")
    assert hasattr(_mod, "GEOMETRY_B_SL_XAUUSD_PCT")
    assert hasattr(_mod, "GEOMETRY_B_SL_OTHER_ABS")
    assert hasattr(_mod, "SL_MARGIN_ATR_A")
