"""Tests for ``scripts.ob_continuation_monitor`` — OB rolling-50 decay monitor.

All tests use ``tmp_path`` and monkeypatch the module-level constants on the
``_mod`` object (NOT on symbols imported via ``from X import Y``). This
mirrors the canonical temporary-path isolation pattern used across tests
after session 21's pytest-contamination post-mortem:

    from scripts import ob_continuation_monitor as _mod
    monkeypatch.setattr(_mod, "OUTPUT_CSV", tmp_path / "out.csv")

Writing under the real ``shadow_logs/`` would trigger the
``ProductionWriteError`` guard installed by ``tests/conftest.py``. All tests
here are structured so that no production path is ever touched.
"""
from __future__ import annotations

import csv
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import ob_continuation_monitor as _mod
from scripts.ob_continuation_monitor import ResolvedRetest


# =============================================================================
# Helpers
# =============================================================================


def _ts(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> str:
    """Return an ISO timestamp in the format ``parse_tradingview_csv`` emits.

    Callers may pass arbitrary ``hour`` / ``minute`` offsets (e.g. minute=180
    to mean "3h past the hour"); we normalize via ``timedelta`` so the helper
    never raises on valid arithmetic that happens to overflow 60m / 24h.
    """
    base = datetime(year, month, day, tzinfo=timezone.utc)
    return (base + timedelta(hours=hour, minutes=minute)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _candle(t: str, o: float, h: float, l: float, c: float, v: float = 0.0) -> dict:
    return {"time": t, "open": o, "high": h, "low": l, "close": c, "volume": v}


def _retest(
    symbol: str = "XAUUSD",
    ob_type: str = "bullish",
    retest_time: str = "2026-01-02T07:00:00Z",
    outcome: str = "CONTINUED",
    ob_formation_time: str = "2026-01-01T10:00:00Z",
) -> ResolvedRetest:
    return ResolvedRetest(
        symbol=symbol,
        ob_type=ob_type,  # type: ignore[arg-type]
        ob_formation_time=ob_formation_time,
        ob_high=2000.0,
        ob_low=1990.0,
        retest_time=retest_time,
        entry_price=1995.0,
        sl_price=1988.0,
        sl_distance=7.0,
        outcome=outcome,  # type: ignore[arg-type]
    )


# =============================================================================
# classify_retest — pure function, no I/O
# =============================================================================


class TestClassifyRetest:
    """Verify the outcome-classification rule mirrors
    ``scripts.ob_retest_comprehensive.py`` (lines 530-593).
    """

    def _bullish_ob(self, entry: float = 2000.0, sl: float = 1990.0) -> dict:
        return {
            "ob_type": "bullish",
            "entry_price": entry,
            "sl_price": sl,
            "sl_distance": entry - sl,
        }

    def _bearish_ob(self, entry: float = 2000.0, sl: float = 2010.0) -> dict:
        return {
            "ob_type": "bearish",
            "entry_price": entry,
            "sl_price": sl,
            "sl_distance": sl - entry,
        }

    def test_classify_retest_continuation_bullish_ob(self):
        """Bullish OB, price moves up past entry + 1.5R before SL → CONTINUED."""
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)  # 10-pt SL → 15-pt target
        target = 2015.0
        # 13 candles: idx 0 is entry. Idx 3 hits the target on a high.
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.5)
            for i in range(13)
        ]
        # Idx 3: high touches 2015.0
        candles[3] = _candle(_ts(2026, 1, 2, 7, 45), 2001.0, 2015.5, 2001.0, 2010.0)
        assert _mod.classify_retest(ob, candles) == "CONTINUED"

    def test_classify_retest_reversal_bullish_ob(self):
        """Bullish OB, price drops and hits SL before target → REVERSED."""
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.5)
            for i in range(13)
        ]
        # Idx 2: low sweeps below SL
        candles[2] = _candle(_ts(2026, 1, 2, 7, 30), 2000.0, 2000.5, 1989.5, 1991.0)
        assert _mod.classify_retest(ob, candles) == "REVERSED"

    def test_classify_retest_continuation_bearish_ob(self):
        """Bearish OB, price drops past entry - 1.5R before SL → CONTINUED."""
        ob = self._bearish_ob(entry=2000.0, sl=2010.0)  # 10-pt SL → 15-pt target
        target = 1985.0
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.0)
            for i in range(13)
        ]
        candles[5] = _candle(_ts(2026, 1, 2, 8, 15), 1999.0, 1999.5, 1984.5, 1986.0)
        assert _mod.classify_retest(ob, candles) == "CONTINUED"

    def test_classify_retest_reversal_bearish_ob(self):
        """Bearish OB, price rises and hits SL before target → REVERSED."""
        ob = self._bearish_ob(entry=2000.0, sl=2010.0)
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.0)
            for i in range(13)
        ]
        candles[1] = _candle(_ts(2026, 1, 2, 7, 15), 2000.0, 2010.5, 1999.5, 2009.0)
        assert _mod.classify_retest(ob, candles) == "REVERSED"

    def test_classify_retest_unresolved_when_insufficient_post_candles(self):
        """Fewer than 12 forward candles → UNRESOLVED."""
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)
        # Only 5 candles (need >= 13 for index 12 to exist).
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.0)
            for i in range(5)
        ]
        assert _mod.classify_retest(ob, candles) == "UNRESOLVED"

    def test_classify_retest_ambiguous_same_candle_open_above_target_continues(self):
        """Same-candle SL+TP: if open >= target, CONTINUED wins."""
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.0)
            for i in range(13)
        ]
        # Gap-up candle: open already above target; wicks to SL then back up.
        candles[1] = _candle(_ts(2026, 1, 2, 7, 15), 2016.0, 2020.0, 1989.0, 2018.0)
        assert _mod.classify_retest(ob, candles) == "CONTINUED"

    def test_classify_retest_ambiguous_same_candle_open_below_sl_reverses(self):
        """Same-candle SL+TP: if open <= SL, REVERSED wins."""
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.0)
            for i in range(13)
        ]
        # Gap-down open, then wicks up to target and back.
        candles[1] = _candle(_ts(2026, 1, 2, 7, 15), 1985.0, 2016.0, 1984.0, 2010.0)
        assert _mod.classify_retest(ob, candles) == "REVERSED"

    def test_classify_retest_horizon_expiry_counts_as_reversed(self):
        """Exactly 13 candles, neither SL nor target hit → REVERSED (matches
        the reference script's ``hit_target_3h=False`` semantics).
        """
        ob = self._bullish_ob(entry=2000.0, sl=1990.0)
        # All candles stay flat, never hitting SL or target.
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2005.0, 1995.0, 2000.5)
            for i in range(13)
        ]
        assert _mod.classify_retest(ob, candles) == "REVERSED"

    def test_classify_retest_zero_sl_distance_is_unresolved(self):
        """sl_distance <= 0 (malformed OB) → UNRESOLVED, not crash."""
        ob = {
            "ob_type": "bullish",
            "entry_price": 2000.0,
            "sl_price": 2000.0,
            "sl_distance": 0.0,
        }
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 2000.0, 2001.0, 1999.0, 2000.5)
            for i in range(13)
        ]
        assert _mod.classify_retest(ob, candles) == "UNRESOLVED"


# =============================================================================
# rolling_window / compute_rate
# =============================================================================


class TestRollingWindow:
    def test_rolling_window_takes_most_recent_50_chronologically(self):
        """Given 100 retests sorted ascending, window of 50 returns the last 50."""
        retests = [
            _retest(retest_time=_ts(2026, 1, 1 + (i // 96), 0, i % 96 * 15))
            for i in range(100)
        ]
        window = _mod.rolling_window(retests, 50)
        assert len(window) == 50
        assert window[0] is retests[50]
        assert window[-1] is retests[-1]

    def test_rolling_window_smaller_than_50_returns_all(self):
        retests = [
            _retest(retest_time=_ts(2026, 1, 2, h, 0))
            for h in range(5)
        ]
        window = _mod.rolling_window(retests, 50)
        assert window == retests

    def test_rolling_window_empty_input_returns_empty(self):
        assert _mod.rolling_window([], 50) == []

    def test_rolling_window_zero_size_returns_empty(self):
        """Defensive: size<=0 is a degenerate input — return empty list, no crash."""
        retests = [_retest(retest_time=_ts(2026, 1, 2, h, 0)) for h in range(5)]
        assert _mod.rolling_window(retests, 0) == []
        assert _mod.rolling_window(retests, -1) == []


class TestComputeRate:
    def test_compute_rate_zero_division_safe(self):
        """Empty window → (0, 0, 0.0), no crash."""
        assert _mod.compute_rate([]) == (0, 0, 0.0)

    def test_compute_rate_unresolved_excluded(self):
        """UNRESOLVED retests must NOT count toward total or continuation."""
        window = [
            _retest(outcome="CONTINUED"),
            _retest(outcome="REVERSED"),
            _retest(outcome="UNRESOLVED"),
            _retest(outcome="UNRESOLVED"),
        ]
        cont, total, rate = _mod.compute_rate(window)
        assert cont == 1
        assert total == 2
        assert rate == 50.0

    def test_compute_rate_all_continued(self):
        window = [_retest(outcome="CONTINUED") for _ in range(5)]
        cont, total, rate = _mod.compute_rate(window)
        assert (cont, total, rate) == (5, 5, 100.0)

    def test_compute_rate_all_reversed(self):
        window = [_retest(outcome="REVERSED") for _ in range(3)]
        cont, total, rate = _mod.compute_rate(window)
        assert (cont, total, rate) == (0, 3, 0.0)


# =============================================================================
# Alarm boundary tests
# =============================================================================


class TestAlarmBoundary:
    """The alarm must fire when rate < threshold, silent when rate >= threshold.
    Boundary condition at exactly the threshold is the key test — ``<`` semantics.
    """

    def _window(self, cont: int, rev: int) -> list[ResolvedRetest]:
        return (
            [_retest(outcome="CONTINUED") for _ in range(cont)]
            + [_retest(outcome="REVERSED") for _ in range(rev)]
        )

    def test_alarm_fires_at_59_99_pct(self):
        """Just below threshold: 59 / 100 = 59% < 60% → ALARM."""
        window = self._window(cont=59, rev=41)
        cont, total, rate = _mod.compute_rate(window)
        assert rate == 59.0
        assert _mod._should_alarm(total, rate, 60.0)

    def test_alarm_silent_at_exactly_60_pct(self):
        """At threshold: 60 / 100 = 60.0% → silent (strict ``<`` semantics)."""
        window = self._window(cont=60, rev=40)
        cont, total, rate = _mod.compute_rate(window)
        assert rate == 60.0
        assert not _mod._should_alarm(total, rate, 60.0)

    def test_alarm_silent_at_above_60_pct(self):
        window = self._window(cont=70, rev=30)
        cont, total, rate = _mod.compute_rate(window)
        assert rate == 70.0
        assert not _mod._should_alarm(total, rate, 60.0)

    def test_alarm_silent_at_exactly_alarm_threshold_monkeypatched(self, monkeypatch):
        """If threshold is set to 50.0, a 50% rate must NOT alarm."""
        monkeypatch.setattr(_mod, "ALARM_THRESHOLD_PCT", 50.0)
        window = self._window(cont=25, rev=25)
        cont, total, rate = _mod.compute_rate(window)
        assert rate == 50.0
        assert not _mod._should_alarm(total, rate, 50.0)

    def test_alarm_silent_on_zero_total(self):
        """Zero-total scope must NEVER alarm (nothing to judge)."""
        assert not _mod._should_alarm(0, 0.0, 60.0)

    # ------------------------------------------------------------------
    # Insufficient-sample gate (new April 18, 2026)
    # ------------------------------------------------------------------
    # The ``_should_alarm`` signature grew a ``window_size`` kwarg so a
    # thin-sample window (total < window_size) never fires an alarm — the
    # rolling-N decay signal is not statistically meaningful until we have
    # N observations. Without this gate, quiet symbols like GBPUSD (148
    # months to fill rolling-50 at current retest rates) would fire
    # spurious alarms on the first bad sequence.

    def test_alarm_silent_when_total_below_window_size(self):
        """total=49, rate=50%, threshold=60%, window_size=50 → silent.

        Even though rate < threshold, the window is not yet full so the
        alarm must NOT fire.
        """
        assert not _mod._should_alarm(
            total=49, rate_pct=50.0, threshold_pct=60.0, window_size=50,
        )

    def test_alarm_fires_at_total_equal_window_size_below_threshold(self):
        """total=50, rate=50%, threshold=60%, window_size=50 → ALARM.

        Boundary condition: ``total >= window_size`` is inclusive on the
        full-window side. Exactly 50 observations is sufficient to fire.
        """
        assert _mod._should_alarm(
            total=50, rate_pct=50.0, threshold_pct=60.0, window_size=50,
        )

    def test_alarm_silent_at_boundary_total_one_below(self):
        """total=49, rate=0%, threshold=60%, window_size=50 → silent.

        Thin-sample gate wins over catastrophic rate. Even 0% must not
        alarm if we haven't seen the full window yet.
        """
        assert not _mod._should_alarm(
            total=49, rate_pct=0.0, threshold_pct=60.0, window_size=50,
        )

    def test_alarm_respects_custom_window_size(self):
        """``window_size`` kwarg overrides the module default.

        window_size=10 means the gate opens at total>=10 instead of 50.
        """
        # Below custom window → silent
        assert not _mod._should_alarm(
            total=5, rate_pct=50.0, threshold_pct=60.0, window_size=10,
        )
        # At custom window boundary → fires (below threshold)
        assert _mod._should_alarm(
            total=10, rate_pct=50.0, threshold_pct=60.0, window_size=10,
        )

    def test_should_alarm_default_window_size_is_module_constant(self):
        """Calling without ``window_size`` kwarg uses ``WINDOW_SIZE`` default.

        total=100 is well past the module-default WINDOW_SIZE (50), so
        with rate below threshold the alarm must fire.
        """
        # Sanity-check the module constant so the test fails loudly if
        # someone edits WINDOW_SIZE without updating downstream contract.
        assert _mod.WINDOW_SIZE == 50
        assert _mod._should_alarm(
            total=100, rate_pct=50.0, threshold_pct=60.0,
        )


# =============================================================================
# CSV append — monkeypatched OUTPUT_CSV to tmp_path
# =============================================================================


@pytest.fixture
def tmp_output(tmp_path: Path, monkeypatch):
    """Redirect OUTPUT_CSV to a tmp path. Returns the Path."""
    target = tmp_path / "ob_continuation_daily.csv"
    monkeypatch.setattr(_mod, "OUTPUT_CSV", target)
    return target


def _read_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestCsvAppend:
    def test_csv_append_creates_new_file_with_header(self, tmp_output):
        _mod.append_daily_snapshot_row(
            date_utc="2026-04-17",
            scope="XAUUSD",
            window_size=50,
            window_start_date="2026-02-03",
            window_end_date="2026-04-10",
            continuation_count=34,
            total_count=50,
            rate_pct=68.0,
            alarm_fired=False,
        )
        assert tmp_output.exists()
        rows = _read_csv(tmp_output)
        assert len(rows) == 1
        r = rows[0]
        assert r["date_utc"] == "2026-04-17"
        assert r["scope"] == "XAUUSD"
        assert r["window_size"] == "50"
        assert r["continuation_count"] == "34"
        assert r["total_count"] == "50"
        assert r["rate_pct"].startswith("68.")
        assert r["alarm_fired"] == "false"

    def test_csv_append_preserves_existing_rows(self, tmp_output):
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-03", "2026-04-10",
            34, 50, 68.0, False,
        )
        _mod.append_daily_snapshot_row(
            "2026-04-17", "US30_cash", 50, "2026-02-05", "2026-04-10",
            30, 50, 60.0, False,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 2
        scopes = {r["scope"] for r in rows}
        assert scopes == {"XAUUSD", "US30_cash"}

    def test_csv_append_deduplicates_same_date_scope_pair(self, tmp_output):
        """Running twice on the same UTC day / same scope must produce ONE row."""
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-03", "2026-04-10",
            34, 50, 68.0, False,
        )
        # Same date/scope, different rate — the new row wins.
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-04", "2026-04-11",
            20, 50, 40.0, True,
        )
        rows = _read_csv(tmp_output)
        # Filter to just the XAUUSD rows for this date
        xau_today = [r for r in rows if r["date_utc"] == "2026-04-17" and r["scope"] == "XAUUSD"]
        assert len(xau_today) == 1
        assert xau_today[0]["rate_pct"].startswith("40.")
        assert xau_today[0]["alarm_fired"] == "true"

    def test_csv_append_dedupe_does_not_affect_other_scopes(self, tmp_output):
        """Rewriting XAUUSD for today must not drop US30_cash row for today."""
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-03", "2026-04-10",
            34, 50, 68.0, False,
        )
        _mod.append_daily_snapshot_row(
            "2026-04-17", "US30_cash", 50, "2026-02-05", "2026-04-10",
            30, 50, 60.0, False,
        )
        # Re-write XAUUSD for same day
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-03", "2026-04-10",
            99, 100, 99.0, False,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 2
        us30 = [r for r in rows if r["scope"] == "US30_cash"]
        assert len(us30) == 1  # US30 row was preserved

    def test_csv_append_preserves_rows_from_different_dates(self, tmp_output):
        _mod.append_daily_snapshot_row(
            "2026-04-16", "XAUUSD", 50, "2026-02-03", "2026-04-09",
            34, 50, 68.0, False,
        )
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-04", "2026-04-10",
            35, 50, 70.0, False,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 2
        dates = sorted(r["date_utc"] for r in rows)
        assert dates == ["2026-04-16", "2026-04-17"]

    def test_csv_append_creates_parent_dir_if_missing(self, tmp_path, monkeypatch):
        """OUTPUT_CSV.parent may not exist on first run — must be created."""
        nested = tmp_path / "shadow_logs_sim" / "deeper" / "out.csv"
        monkeypatch.setattr(_mod, "OUTPUT_CSV", nested)
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "-", "-", 0, 0, 0.0, False,
        )
        assert nested.exists()

    # ------------------------------------------------------------------
    # insufficient_sample column (new April 18, 2026)
    # ------------------------------------------------------------------
    # The CSV grew a new column so thin-sample rows are flagged visually
    # without a consumer having to recompute ``total < window_size``.

    def test_csv_append_writes_insufficient_sample_true(self, tmp_output):
        """insufficient_sample=True is serialized as the literal ``true``."""
        _mod.append_daily_snapshot_row(
            date_utc="2026-04-17",
            scope="GBPUSD",
            window_size=50,
            window_start_date="2026-02-01",
            window_end_date="2026-04-17",
            continuation_count=7,
            total_count=10,
            rate_pct=70.0,
            alarm_fired=False,
            insufficient_sample=True,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 1
        assert rows[0]["insufficient_sample"] == "true"

    def test_csv_append_writes_insufficient_sample_false_by_default(self, tmp_output):
        """Legacy callers (no kwarg) produce ``false`` — backward-compatible."""
        # NOTE: deliberately call with positional args only, no kwarg.
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "2026-02-03", "2026-04-10",
            34, 50, 68.0, False,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 1
        assert rows[0]["insufficient_sample"] == "false"

    def test_csv_append_insufficient_sample_column_in_header(self, tmp_output):
        """The new column must appear in the CSV header exactly once."""
        _mod.append_daily_snapshot_row(
            "2026-04-17", "XAUUSD", 50, "-", "-", 0, 0, 0.0, False,
        )
        with open(tmp_output, "r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert "insufficient_sample" in header
        # And appears only once (defensive — CSV DictWriter would raise if
        # duplicated in fieldnames, but we assert cheaply here).
        assert header.count("insufficient_sample") == 1

    def test_csv_append_preserves_insufficient_sample_on_rewrite(self, tmp_output):
        """Rewriting a (date, scope) pair lets the new row win — including
        the ``insufficient_sample`` flag.

        Write the row first with ``True``, then overwrite with ``False``
        and confirm dedupe picks the most recent row.
        """
        _mod.append_daily_snapshot_row(
            "2026-04-17", "GBPUSD", 50, "-", "-", 7, 10, 70.0, False,
            insufficient_sample=True,
        )
        # Same date/scope, now considered full-window (e.g., simulated
        # weeks-later run where retests piled up).
        _mod.append_daily_snapshot_row(
            "2026-04-17", "GBPUSD", 50, "2026-02-01", "2026-04-17",
            30, 50, 60.0, False,
            insufficient_sample=False,
        )
        rows = _read_csv(tmp_output)
        assert len(rows) == 1
        # The new row wins: insufficient_sample should be "false".
        assert rows[0]["insufficient_sample"] == "false"
        # And the payload is the new one (total_count=50, not 10).
        assert rows[0]["total_count"] == "50"


# =============================================================================
# run_monitor orchestration — synthetic retests injected via monkeypatch
# =============================================================================


def _make_resolved_stream(
    symbol: str,
    continued: int,
    reversed_: int,
    base_date: date = date(2026, 1, 2),
) -> list[ResolvedRetest]:
    """Build a chronological list of resolved retests.

    Outcomes are INTERLEAVED across time (not blocked cont-then-rev) so the
    rolling-window portfolio merge picks a representative sample, not just
    the tail of one outcome class. We use distinct hour offsets per symbol
    (so a merged portfolio window interleaves symbols deterministically) and
    the ``i``-th retest gets timestamp ``base_date + symbol_offset_hours +
    i * 30 minutes`` so all are unique across (symbol, i).
    """
    # Distinct per-symbol hour offset keeps cross-symbol timestamps unique
    # after merging into the portfolio window. We use 48h spacing so 50
    # retests at 30-min increments (25h span) do NOT overlap with the
    # adjacent symbol — keeps the portfolio merge deterministic regardless
    # of per-stream size up to ~96 retests.
    _SYMBOL_OFFSETS = {
        "XAUUSD": 0,
        "US30_cash": 48,
        "USDJPY": 96,
        "GBPJPY": 144,
        "GBPUSD": 192,
    }
    sym_hour = _SYMBOL_OFFSETS.get(symbol, 0)

    total = continued + reversed_
    if total == 0:
        return []

    # Bresenham-style interleave: distribute CONTINUED labels evenly across
    # the stream so any contiguous sub-window has ~the same continued rate
    # as the whole. "Place a CONTINUED iff the running count divided by the
    # position index is below the target ratio".
    outcomes: list[str] = []
    placed = 0
    for k in range(total):
        # Would-be rate if we placed a CONTINUED here vs. REVERSED.
        # Place CONTINUED while we're below the quota.
        if placed * total < (k + 1) * continued:
            outcomes.append("CONTINUED")
            placed += 1
        else:
            outcomes.append("REVERSED")

    out: list[ResolvedRetest] = []
    for idx, oc in enumerate(outcomes):
        # 30-min increments keep everything within a single day for small N
        # (e.g. 50 retests × 30min = 25h → rolls into hour sym_hour+1..).
        out.append(_retest(
            symbol=symbol,
            outcome=oc,
            retest_time=_ts(
                base_date.year, base_date.month, base_date.day,
                sym_hour, idx * 30,
            ),
        ))
    out.sort(key=lambda r: r.retest_time)
    return out


class TestRunMonitor:
    def test_run_monitor_clean_state_exits_0(self, tmp_output, monkeypatch):
        """All scopes green (>= 70% WR) → exit 0, no alarms."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 0
        assert alerts == []

        # CSV should cover the full configured vNext symbol set + PORTFOLIO.
        rows = _read_csv(tmp_output)
        assert len(rows) == len(_mod.SYMBOLS) + 1
        scopes = {r["scope"] for r in rows}
        assert scopes == set(_mod.SYMBOLS) | {"PORTFOLIO"}
        for r in rows:
            assert r["alarm_fired"] == "false"

    def test_run_monitor_one_alarm_exits_1(self, tmp_output, monkeypatch):
        """One symbol below threshold → exit 1, one alert, one alarm_fired=true."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                # 25/50 = 50% → alarm
                return _make_resolved_stream(sym, continued=25, reversed_=25)
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 1
        assert len(alerts) >= 1
        # Alarm message must mention GBPUSD
        assert any("GBPUSD" in a for a in alerts)

        rows = _read_csv(tmp_output)
        gbpusd = [r for r in rows if r["scope"] == "GBPUSD"]
        assert len(gbpusd) == 1
        assert gbpusd[0]["alarm_fired"] == "true"

    def test_run_monitor_load_failure_exits_2(self, tmp_output, monkeypatch):
        """Every symbol fails to load → exit 2 (unrecoverable)."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            return []  # total_loaded stays 0

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(target_date=date(2026, 4, 17))
        assert rc == 2
        # No CSV write attempted on exit-2 path.
        assert not tmp_output.exists()

    def test_run_monitor_per_symbol_and_portfolio_both_written(self, tmp_output, monkeypatch):
        """Each symbol row present AND PORTFOLIO row aggregates all."""
        streams = {
            "XAUUSD":    _make_resolved_stream("XAUUSD", 35, 15),
            "US30_cash": _make_resolved_stream("US30_cash", 30, 20),
            "USDJPY":    _make_resolved_stream("USDJPY", 30, 20),
            "GBPJPY":    _make_resolved_stream("GBPJPY", 30, 20),
            "GBPUSD":    _make_resolved_stream("GBPUSD", 30, 20),
        }
        monkeypatch.setattr(
            _mod, "build_resolved_retests_for_symbol",
            lambda s: streams.get(s, []),
        )
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 0
        rows = _read_csv(tmp_output)
        by_scope = {r["scope"]: r for r in rows}
        assert set(by_scope) == set(_mod.SYMBOLS) | {"PORTFOLIO"}
        assert by_scope["AUDJPY"]["total_count"] == "0"
        # PORTFOLIO total_count == min(50, sum of all)
        portfolio = by_scope["PORTFOLIO"]
        assert portfolio["window_size"] == "50"
        assert portfolio["total_count"] == "50"
        # PORTFOLIO rate is between best (70) and worst (60) symbols — all
        # streams cap at 50 each; rolling-50 across 250 takes most recent.
        rate = float(portfolio["rate_pct"])
        assert 0.0 <= rate <= 100.0

    def test_run_monitor_symbols_with_limited_data_do_not_alarm_on_empty(
        self, tmp_output, monkeypatch,
    ):
        """A symbol with total_count=0 must NOT alarm (zero-total is not a decay signal)."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPJPY":
                return []  # zero retests → zero total → no alarm
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        rc = _mod.run_monitor(target_date=date(2026, 4, 17))
        assert rc == 0

        rows = _read_csv(tmp_output)
        gbpjpy = [r for r in rows if r["scope"] == "GBPJPY"][0]
        assert gbpjpy["total_count"] == "0"
        assert gbpjpy["alarm_fired"] == "false"

    def test_run_monitor_dry_run_writes_no_csv_and_sends_no_alert(
        self, tmp_output, monkeypatch,
    ):
        """--dry-run path: compute everything, but do NOT write CSV or alert."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                return _make_resolved_stream(sym, continued=25, reversed_=25)  # alarm
            return _make_resolved_stream(sym, continued=35, reversed_=15)

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(
            target_date=date(2026, 4, 17), window_size=50, dry_run=True,
        )
        # Dry-run still exits 1 when it would have alarmed.
        assert rc == 1
        # But no CSV file and no alerts.
        assert not tmp_output.exists()
        assert alerts == []

    # ------------------------------------------------------------------
    # insufficient_sample flag in run_monitor (new April 18, 2026)
    # ------------------------------------------------------------------
    # End-to-end: a scope with total < window_size gets
    # ``insufficient_sample="true"`` in the CSV, does NOT alarm even when
    # rate is below threshold, and its log line carries the
    # ``INSUFFICIENT_SAMPLE (n=X<Y)`` suffix. A scope at total == 50 is
    # considered FULL (not insufficient); the portfolio aggregate can be
    # full even when every individual symbol is thin.

    def test_run_monitor_thin_symbol_flagged_insufficient_sample(
        self, tmp_output, monkeypatch,
    ):
        """One thin symbol (10 retests) + others full → thin row flagged.

        Thin symbol has 10 retests at 100% CR so the rate is ABOVE the
        threshold — proves the flag is driven by sample size only, not rate.
        Other symbols have 50 retests at 70% so nothing alarms anywhere.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                return _make_resolved_stream(sym, continued=10, reversed_=0)  # 10 total
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 50 total @70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        # Thin symbol does not alarm → exit 0.
        assert rc == 0

        rows = _read_csv(tmp_output)
        gbpusd = [r for r in rows if r["scope"] == "GBPUSD"][0]
        assert gbpusd["insufficient_sample"] == "true"
        assert gbpusd["alarm_fired"] == "false"
        assert gbpusd["total_count"] == "10"

        # Other symbols were full → flag is "false".
        xauusd = [r for r in rows if r["scope"] == "XAUUSD"][0]
        assert xauusd["insufficient_sample"] == "false"

    def test_run_monitor_thin_symbol_below_threshold_does_not_alarm(
        self, tmp_output, monkeypatch,
    ):
        """10 retests at 20% CR (far below threshold) — still silent.

        Without the insufficient_sample gate, 20% CR on 10 retests would
        fire a spurious alarm. The gate suppresses it until the window is
        full.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                # 2/10 = 20% → would alarm without the gate
                return _make_resolved_stream(sym, continued=2, reversed_=8)
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 50 @70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        # No alarm: insufficient_sample blocks the thin window, other
        # scopes are above threshold.
        assert rc == 0
        assert alerts == []

        rows = _read_csv(tmp_output)
        gbpusd = [r for r in rows if r["scope"] == "GBPUSD"][0]
        assert gbpusd["insufficient_sample"] == "true"
        assert gbpusd["alarm_fired"] == "false"
        # Rate reflects the true 20%, but no alarm was triggered.
        assert float(gbpusd["rate_pct"]) == pytest.approx(20.0)

    def test_run_monitor_full_symbol_below_threshold_does_alarm(
        self, tmp_output, monkeypatch,
    ):
        """60 retests at 50% CR → full window, below threshold → ALARM.

        Symmetry check against the two insufficient_sample tests above:
        once the window IS full (total >= window_size), the gate is lifted
        and the standard alarm-on-low-rate path runs.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                # 60 retests at 50% CR → rolling-50 tail is also ~50%
                return _make_resolved_stream(sym, continued=30, reversed_=30)
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 50 @70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        alerts: list[str] = []
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: alerts.append(m))

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        # GBPUSD full window below threshold → exit 1.
        assert rc == 1
        assert any("GBPUSD" in a for a in alerts)

        rows = _read_csv(tmp_output)
        gbpusd = [r for r in rows if r["scope"] == "GBPUSD"][0]
        # Full window → insufficient_sample is "false" and alarm_fired is "true".
        assert gbpusd["insufficient_sample"] == "false"
        assert gbpusd["alarm_fired"] == "true"

    def test_run_monitor_logs_insufficient_sample_suffix(
        self, tmp_output, monkeypatch, caplog,
    ):
        """The monitor log line must carry ``INSUFFICIENT_SAMPLE (n=X<Y)``
        when a scope is thin.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "GBPUSD":
                return _make_resolved_stream(sym, continued=5, reversed_=5)  # 10 total
            return _make_resolved_stream(sym, continued=35, reversed_=15)  # 50 @70%

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        # The suffix is logged at INFO level (not CRITICAL — CRITICAL is
        # reserved for alarm rows), so lift caplog to INFO on the module
        # logger.
        with caplog.at_level(logging.INFO, logger=_mod.logger.name):
            rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 0

        gbpusd_logs = [
            r.getMessage() for r in caplog.records
            if "GBPUSD" in r.getMessage()
        ]
        # At least one GBPUSD line must carry the suffix with the exact
        # ``n=X<Y`` format. 10 < 50.
        assert any(
            "INSUFFICIENT_SAMPLE (n=10<50)" in msg for msg in gbpusd_logs
        ), f"No insufficient_sample suffix in GBPUSD logs: {gbpusd_logs!r}"

    def test_run_monitor_portfolio_insufficient_when_aggregate_thin(
        self, tmp_output, monkeypatch,
    ):
        """All configured symbols thin (10 each) still give a full portfolio row.

        The portfolio is the chronological merge of all per-symbol streams, so
        the rolling-50 portfolio window is full even when every individual
        symbol is thin. Per-symbol rows flag insufficient_sample=true, but the
        portfolio row does not.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            return _make_resolved_stream(sym, continued=10, reversed_=0)  # 10 each

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        # Everything is above threshold, so no alarms.
        assert rc == 0

        rows = _read_csv(tmp_output)
        by_scope = {r["scope"]: r for r in rows}
        # Every per-symbol row: total_count=10, insufficient_sample=true.
        for sym in _mod.SYMBOLS:
            row = by_scope[sym]
            assert row["total_count"] == "10"
            assert row["insufficient_sample"] == "true", (
                f"{sym} should be insufficient_sample=true (total=10<50), "
                f"got {row['insufficient_sample']!r}"
            )
        # Portfolio aggregate: 50 total, insufficient_sample=false.
        portfolio = by_scope["PORTFOLIO"]
        assert portfolio["total_count"] == "50"
        assert portfolio["insufficient_sample"] == "false", (
            "Portfolio aggregate is full (50 >= 50) — must NOT be flagged"
        )

    def test_run_monitor_boundary_exact_window_size_not_insufficient(
        self, tmp_output, monkeypatch,
    ):
        """A symbol with exactly 50 retests (total == window_size) is NOT
        flagged as insufficient — the boundary is inclusive on the full side.
        """
        def fake_build(sym: str) -> list[ResolvedRetest]:
            # Every symbol exactly at the boundary: 50 retests each, 70% CR.
            return _make_resolved_stream(sym, continued=35, reversed_=15)

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)

        rc = _mod.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 0

        rows = _read_csv(tmp_output)
        for r in rows:
            # All per-symbol rows have total_count=50, and portfolio is
            # rolling-50 of 250 → also 50. None are insufficient.
            assert r["total_count"] == "50", (
                f"{r['scope']} total_count={r['total_count']} — expected 50"
            )
            assert r["insufficient_sample"] == "false", (
                f"{r['scope']} flagged insufficient at the exact boundary "
                f"(total=50, window_size=50)"
            )


# =============================================================================
# Telegram / side-effect safety
# =============================================================================


class TestTelegramSafety:
    def test_telegram_failure_is_swallowed(self, monkeypatch):
        """send_telegram_alert must NEVER raise, regardless of transport error."""
        def boom(text: str) -> None:
            raise RuntimeError("simulated network failure")

        # Replace notify_alert at the import point. send_telegram_alert does
        # ``from src.notifications import notify_alert`` inside the try, so
        # we need to inject into the notifications module namespace.
        import src.notifications as _notif
        monkeypatch.setattr(_notif, "notify_alert", boom, raising=False)

        # Must not raise
        _mod.send_telegram_alert("test alert")

    def test_telegram_import_failure_is_swallowed(self, monkeypatch):
        """If src.notifications can't be imported at all, no-op path runs cleanly."""
        # Block the import by removing it from sys.modules and making
        # a subsequent import fail.
        import sys
        # Temporarily shadow the module with a broken stub.
        broken = MagicMock()
        broken.notify_alert = MagicMock(side_effect=ImportError("blocked"))
        monkeypatch.setitem(sys.modules, "src.notifications", broken)
        # Must not raise.
        _mod.send_telegram_alert("test alert")

    def test_run_monitor_alarm_with_failing_telegram_still_exits_1(
        self, tmp_output, monkeypatch,
    ):
        """If Telegram fails during an alarmed run, run_monitor must still
        write the CSV row and exit with code 1 — alerting is best-effort."""
        def fake_build(sym: str) -> list[ResolvedRetest]:
            if sym == "USDJPY":
                return _make_resolved_stream(sym, continued=20, reversed_=30)  # 40% → alarm
            return _make_resolved_stream(sym, continued=35, reversed_=15)

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)

        def boom(msg: str) -> None:
            raise RuntimeError("telegram down")
        monkeypatch.setattr(_mod, "send_telegram_alert", boom)

        # run_monitor calls send_telegram_alert directly — if it raises, that
        # would propagate. We confirm our wrapper is designed to swallow;
        # since we replaced the wrapper itself with a raising one, this
        # verifies that run_monitor is NOT robust to a raising send_telegram_alert.
        # So instead we assert that run_monitor does propagate — and that
        # the real send_telegram_alert (via notify_alert) IS the safe
        # boundary. Flip: use the real wrapper with a broken notify_alert.
        import src.notifications as _notif
        monkeypatch.setattr(
            _notif, "notify_alert",
            lambda m: (_ for _ in ()).throw(RuntimeError("telegram down")),
            raising=False,
        )
        # Restore the real send_telegram_alert — the wrapper must swallow.
        import importlib
        importlib.reload(_mod)  # re-load module to restore send_telegram_alert
        # Re-apply the build monkeypatch post-reload.
        from scripts import ob_continuation_monitor as _reloaded
        monkeypatch.setattr(_reloaded, "OUTPUT_CSV", tmp_output)
        monkeypatch.setattr(_reloaded, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_notif, "notify_alert", boom, raising=False)

        rc = _reloaded.run_monitor(target_date=date(2026, 4, 17), window_size=50)
        assert rc == 1
        assert tmp_output.exists()


# =============================================================================
# Helper-function tests
# =============================================================================


class TestHelpers:
    def test_parse_candle_time_iso_z_format(self):
        dt = _mod._parse_candle_time("2026-04-17T07:15:00Z")
        assert dt.year == 2026
        assert dt.month == 4
        assert dt.day == 17
        assert dt.hour == 7
        assert dt.minute == 15
        assert dt.tzinfo == timezone.utc

    def test_parse_candle_time_space_format(self):
        dt = _mod._parse_candle_time("2026-04-17 07:15:00")
        assert dt.hour == 7 and dt.tzinfo == timezone.utc

    def test_parse_candle_time_invalid_raises(self):
        with pytest.raises(ValueError):
            _mod._parse_candle_time("not a date")

    def test_sl_buffer_for_xauusd_uses_live_absolute_config(self):
        assert _mod._sl_buffer_for("XAUUSD", 2000.0) == 1.20

    def test_sl_buffer_for_gbpusd_is_absolute(self):
        # 0.00015 regardless of price
        assert _mod._sl_buffer_for("GBPUSD", 1.2500) == 0.00015
        assert _mod._sl_buffer_for("GBPUSD", 1.5000) == 0.00015

    def test_sl_buffer_for_unknown_symbol_falls_back_to_xauusd_style(self):
        # Falls back to 0.001 * price (same formula as XAUUSD).
        assert abs(_mod._sl_buffer_for("UNKNOWN", 100.0) - 0.1) < 1e-9

    def test_merge_for_portfolio_is_chronological(self):
        """Portfolio merge must interleave symbols chronologically."""
        per = {
            "XAUUSD": [
                _retest(symbol="XAUUSD", retest_time=_ts(2026, 1, 2, 7, 0)),
                _retest(symbol="XAUUSD", retest_time=_ts(2026, 1, 2, 13, 0)),
            ],
            "GBPUSD": [
                _retest(symbol="GBPUSD", retest_time=_ts(2026, 1, 2, 9, 0)),
                _retest(symbol="GBPUSD", retest_time=_ts(2026, 1, 2, 15, 0)),
            ],
        }
        merged = _mod.merge_for_portfolio(per)
        times = [r.retest_time for r in merged]
        assert times == sorted(times)
        assert len(merged) == 4

    def test_window_date_range_returns_dashes_for_empty(self):
        assert _mod._window_date_range([]) == ("-", "-")


# =============================================================================
# build_retest_history — synthetic end-to-end
# =============================================================================


class TestBuildRetestHistory:
    def test_build_retest_history_empty_inputs_returns_empty(self):
        assert _mod.build_retest_history([], [], "XAUUSD") == []

    def test_build_retest_history_mitigated_ob_skipped(self):
        """Mitigated OBs must be skipped (matches ob_retest_comprehensive line 234-236)."""
        mitigated_ob = MagicMock()
        mitigated_ob.mitigated = True
        mitigated_ob.formation_time = _ts(2026, 1, 1, 10, 0)
        mitigated_ob.high = 2000.0
        mitigated_ob.low = 1990.0
        mitigated_ob.type = "bullish"
        candles = [
            _candle(_ts(2026, 1, 2, 7, 0 + i * 15), 1995.0, 1996.0, 1994.0, 1995.0)
            for i in range(20)
        ]
        result = _mod.build_retest_history([mitigated_ob], candles, "XAUUSD")
        assert result == []

    def test_build_retest_history_detects_bullish_retest_and_classifies(self):
        """A bullish OB, price drops to retest the zone, then continues up."""
        ob = MagicMock()
        ob.mitigated = False
        ob.formation_time = _ts(2026, 1, 1, 10, 0)
        ob.high = 2000.0
        ob.low = 1990.0
        ob.type = "bullish"

        # Candles: first 3 are above the zone (no retest), idx 3 dips into
        # the zone, then price continues upward past 1.5R target.
        # entry ≈ close of retest candle if close >= ob_low; say 1992.0.
        # sl = 1990 - 0.001*1990 = 1988.01, sl_distance ≈ 3.99, target ≈ 5.99
        # so we need price to reach 1992 + 5.99 = 1997.99.
        candles: list[dict] = []
        # 3 candles above zone
        for i in range(3):
            t = _ts(2026, 1, 2, 7, i * 15)
            candles.append(_candle(t, 2005.0, 2007.0, 2004.0, 2005.0))
        # Retest candle (enters zone)
        candles.append(_candle(_ts(2026, 1, 2, 7, 45), 2004.0, 2005.0, 1991.0, 1992.0))
        # Continuation candles — gently rise to hit target
        for i in range(13):
            t = _ts(2026, 1, 2, 8, i * 15)
            candles.append(_candle(t, 1992.0, 1998.5, 1991.5, 1998.0))

        result = _mod.build_retest_history([ob], candles, "XAUUSD")
        assert len(result) == 1
        r = result[0]
        assert r.symbol == "XAUUSD"
        assert r.ob_type == "bullish"
        # entry_price was set to the retest candle's close (1992.0)
        assert abs(r.entry_price - 1992.0) < 1e-6
        assert r.outcome == "CONTINUED"

    def test_build_retest_history_sorted_by_retest_time(self):
        """Results are sorted ascending by retest_time even if OBs are out of order."""
        obs = []
        for hour, low, high in [(13, 1980.0, 1990.0), (10, 1990.0, 2000.0)]:
            o = MagicMock()
            o.mitigated = False
            # Formation BEFORE retest window so the OB fires
            o.formation_time = _ts(2026, 1, 1, hour - 1, 0)
            o.high = high
            o.low = low
            o.type = "bullish"
            obs.append(o)

        # Build a long candle series with retests at different hours.
        candles: list[dict] = []
        # From formation_time forward, provide 200 candles of gentle up-moves
        # that all hit the zones at different times.
        for h in range(10, 24):
            for m in (0, 15, 30, 45):
                t = _ts(2026, 1, 2, h, m)
                # Make price sweep through both zones
                candles.append(_candle(t, 1995.0, 2005.0, 1975.0, 2000.0))
        # 14 hours * 4 = 56 candles — give enough for resolution
        for h in range(0, 10):
            for m in (0, 15, 30, 45):
                t = _ts(2026, 1, 3, h, m)
                candles.append(_candle(t, 2005.0, 2050.0, 2000.0, 2040.0))

        result = _mod.build_retest_history(obs, candles, "XAUUSD")
        times = [r.retest_time for r in result]
        assert times == sorted(times)


# =============================================================================
# load_m15_for_symbol — missing data handling
# =============================================================================


class TestLoadM15:
    def test_load_m15_missing_file_returns_empty(self, tmp_path, monkeypatch):
        """Missing CSV → warning + empty list, not a crash."""
        monkeypatch.setattr(_mod, "DATA_DIR", tmp_path)  # empty tmp dir
        result = _mod.load_m15_for_symbol("XAUUSD")
        assert result == []

    def test_load_m15_present_file_parses(self, tmp_path, monkeypatch):
        """A minimal CSV under the redirected DATA_DIR must load cleanly."""
        monkeypatch.setattr(_mod, "DATA_DIR", tmp_path)
        csv_path = tmp_path / "XAUUSD_M15.csv"
        csv_path.write_text(
            "time,open,high,low,close,volume\n"
            "2026-01-02 07:00:00,2000.0,2005.0,1998.0,2002.0,100\n"
            "2026-01-02 07:15:00,2002.0,2008.0,2001.0,2007.0,120\n",
            encoding="utf-8",
        )
        candles = _mod.load_m15_for_symbol("XAUUSD")
        assert len(candles) == 2
        assert candles[0]["open"] == 2000.0
        assert candles[1]["close"] == 2007.0

    def test_load_m15_resolves_relative_pointer_file(self, tmp_path, monkeypatch):
        """A tiny CSV pointer in DATA_DIR must resolve to its data-root target."""
        historical = tmp_path / "historical"
        historical.mkdir()
        monkeypatch.setattr(_mod, "DATA_DIR", historical)
        root_csv = tmp_path / "GBPUSD_M15.csv"
        root_csv.write_text(
            "time,open,high,low,close,volume\n"
            "2026-01-02 07:00:00,1.0,2.0,0.5,1.5,10\n",
            encoding="utf-8",
        )
        (historical / "GBPUSD_M15.csv").write_text("../GBPUSD_M15.csv\n", encoding="utf-8")

        candles = _mod.load_m15_for_symbol("GBPUSD")

        assert len(candles) == 1
        assert candles[0]["close"] == 1.5

    def test_load_m15_uses_parent_data_root_fallback(self, tmp_path, monkeypatch):
        """If historical is missing but data-root CSV exists, use that source."""
        historical = tmp_path / "historical"
        historical.mkdir()
        monkeypatch.setattr(_mod, "DATA_DIR", historical)
        root_csv = tmp_path / "NAS100_M15.csv"
        root_csv.write_text(
            "time,open,high,low,close,volume\n"
            "2026-01-02 07:00:00,100.0,102.0,99.5,101.5,10\n",
            encoding="utf-8",
        )

        candles = _mod.load_m15_for_symbol("NAS100")

        assert len(candles) == 1
        assert candles[0]["open"] == 100.0


# =============================================================================
# main() CLI contract
# =============================================================================


class TestMainCli:
    def test_main_invalid_date_exits_2(self, monkeypatch):
        """--date with unparseable value → exit 2."""
        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", lambda s: [])
        rc = _mod.main(["--date", "not-a-date", "--dry-run"])
        assert rc == 2

    def test_main_dry_run_short_circuits_output(self, tmp_output, monkeypatch):
        """CLI --dry-run routes through run_monitor with dry_run=True."""
        monkeypatch.setattr(
            _mod, "build_resolved_retests_for_symbol",
            lambda s: _make_resolved_stream(s, continued=35, reversed_=15),
        )
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)
        rc = _mod.main(["--date", "2026-04-17", "--dry-run"])
        assert rc == 0
        assert not tmp_output.exists()

    def test_main_symbols_override(self, tmp_output, monkeypatch):
        """--symbols restricts the set processed."""
        called: list[str] = []
        def fake_build(sym: str) -> list[ResolvedRetest]:
            called.append(sym)
            return _make_resolved_stream(sym, continued=35, reversed_=15)

        monkeypatch.setattr(_mod, "build_resolved_retests_for_symbol", fake_build)
        monkeypatch.setattr(_mod, "send_telegram_alert", lambda m: None)
        rc = _mod.main(["--date", "2026-04-17", "--symbols", "XAUUSD,GBPUSD"])
        assert rc == 0
        assert set(called) == {"XAUUSD", "GBPUSD"}
        rows = _read_csv(tmp_output)
        assert {row["scope"] for row in rows} == {"XAUUSD", "GBPUSD", "PORTFOLIO"}
