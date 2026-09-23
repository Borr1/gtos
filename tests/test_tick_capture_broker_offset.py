"""Tests for the broker-offset-aware ts_utc convention in tick_capture
(Issue #16, 2026-04-28).

Background
----------
Agent B's broker-offset fix (commit 5c66ee8) made ``tick.time_msc`` be
broker time (UTC+3 on redacted_account-Server 2). The parquet writer's
``ts_utc`` column was derived as
    ``datetime.fromtimestamp(ts_msc/1000, tz=timezone.utc)``
which mis-labelled broker-localized seconds as UTC. The orchestrator's
``tick_features._read_ticks_for_bar`` then computed
    ``df['ts_utc'] >= bar_open_ts``
in true UTC and missed every row by exactly ``broker_offset_seconds``.

Fix: ``annotate_aggressor`` now accepts ``broker_offset_seconds`` and
SUBTRACTS it before constructing the ``ts_utc`` datetime. The ``ts_msc``
column is preserved unchanged (broker time, dedup key).

Tests use ``tmp_path`` exclusively (canon).
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

pyarrow = pytest.importorskip("pyarrow")
pandas = pytest.importorskip("pandas")

import pandas as pd
import pyarrow.parquet as pq

from src.components import tick_capture as tc
from src.components import tick_features as tf
from src.components.tick_capture import (
    CaptureState,
    annotate_aggressor,
    run_capture_loop,
    write_ticks_parquet,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _broker_tick(true_utc_dt: datetime, broker_offset_s: int,
                  bid: float = 100.0, ask: float = 100.05) -> dict:
    """Build a tick dict as MT5 would deliver it on a +offset broker.

    The MT5 SDK reports ``time_msc`` in broker server time. So a tick that
    REALLY happened at ``true_utc_dt`` arrives with ``time_msc`` =
    ``(true_utc_epoch + broker_offset_s) * 1000``.
    """
    broker_epoch = true_utc_dt.timestamp() + broker_offset_s
    ts_msc = int(broker_epoch * 1000)
    return {
        "time": ts_msc // 1000,
        "ts_msc": ts_msc,
        "time_msc": ts_msc,
        "bid": bid,
        "ask": ask,
        "last": 0.0,
        "volume": 1.0,
        "flags": 0,
    }


# ---------------------------------------------------------------------------
# 1 — annotate_aggressor offset arithmetic
# ---------------------------------------------------------------------------


class TestAnnotateAggressorBrokerOffset:
    def test_zero_offset_preserves_legacy_behavior(self):
        """Default ``broker_offset_seconds=0`` reproduces the old datetime."""
        true_utc = datetime(2026, 4, 28, 14, 30, 0, tzinfo=timezone.utc)
        tick = _broker_tick(true_utc, broker_offset_s=0)
        out, _, _ = annotate_aggressor([tick])
        assert out[0]["ts_utc"] == true_utc

    def test_plus_three_broker_corrected_to_true_utc(self):
        """A redacted_account-Server-2-shaped tick (UTC+3) MUST land at true UTC."""
        true_utc = datetime(2026, 4, 28, 14, 30, 0, tzinfo=timezone.utc)
        broker_offset = 10800  # +3h
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)
        out, _, _ = annotate_aggressor([tick], broker_offset_seconds=broker_offset)
        assert out[0]["ts_utc"] == true_utc, (
            f"Expected true UTC {true_utc.isoformat()}; "
            f"got {out[0]['ts_utc'].isoformat()}"
        )

    def test_plus_two_broker_corrected_to_true_utc(self):
        """FTMO-Server-3 shape (UTC+2) — verify the math is general."""
        true_utc = datetime(2026, 4, 28, 7, 0, 0, tzinfo=timezone.utc)
        broker_offset = 7200  # +2h
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)
        out, _, _ = annotate_aggressor([tick], broker_offset_seconds=broker_offset)
        assert out[0]["ts_utc"] == true_utc

    def test_negative_offset_clamped_to_epoch(self):
        """A misconfigured offset that pushes ts_utc below 0 clamps to epoch
        (1970-01-01). On Windows ``fromtimestamp`` raises on negative input;
        the guard returns a deterministic fail-open value instead."""
        # Hand-build a tick whose ts_msc is 30 minutes into the broker epoch
        # paired with a +1h offset. Naively ``ts_msc/1000 - 3600`` = -1800.
        tick = {
            "time": 1800,
            "ts_msc": 1800 * 1000,
            "time_msc": 1800 * 1000,
            "bid": 100.0,
            "ask": 100.05,
            "last": 0.0,
            "volume": 1.0,
            "flags": 0,
        }
        out, _, _ = annotate_aggressor([tick], broker_offset_seconds=3600)
        assert out[0]["ts_utc"] == datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_ts_msc_preserved_as_broker_time(self):
        """The ``ts_msc`` dedup key must remain broker time (downstream
        consumers rely on raw broker time as the dedup primitive)."""
        true_utc = datetime(2026, 4, 28, 14, 30, 0, tzinfo=timezone.utc)
        broker_offset = 10800
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)
        original_ts_msc = tick["ts_msc"]
        out, _, _ = annotate_aggressor([tick], broker_offset_seconds=broker_offset)
        assert out[0]["ts_msc"] == original_ts_msc, (
            "ts_msc must NOT be touched by the offset correction"
        )


# ---------------------------------------------------------------------------
# 2 — Round-trip through parquet + tick_features lookup hits
# ---------------------------------------------------------------------------


class TestParquetLookupFindsRowsAfterOffsetFix:
    """The bug surfaced as: orchestrator looks up parquet at TRUE UTC but
    parquet stored broker-time-as-UTC -> lookup misses every row.

    With the fix, the orchestrator's bar-window lookup MUST find the rows
    that were written under true UTC."""

    def test_orchestrator_lookup_finds_row_after_fix(self, tmp_path):
        """End-to-end: simulate broker tick, annotate with offset, write
        parquet, then run the orchestrator's lookup at TRUE UTC."""
        ticks_root = tmp_path / "ticks"

        # A tick that REALLY happened mid-bar at 14:30:30 UTC on a +3 broker.
        true_utc = datetime(2026, 4, 28, 14, 30, 30, tzinfo=timezone.utc)
        broker_offset = 10800  # +3h
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)

        annotated, _, _ = annotate_aggressor(
            [tick], broker_offset_seconds=broker_offset
        )
        out_path = ticks_root / "XAUUSD" / "2026-04-28.parquet"
        write_ticks_parquet(annotated, out_path)

        # Now the orchestrator looks up bar [14:30, 14:45) in TRUE UTC.
        bar_open = datetime(2026, 4, 28, 14, 30, 0, tzinfo=timezone.utc)
        bar_close = datetime(2026, 4, 28, 14, 45, 0, tzinfo=timezone.utc)
        df = tf._read_ticks_for_bar("XAUUSD", bar_open, bar_close,
                                       ticks_root=ticks_root)
        assert df is not None and not df.empty, (
            "Lookup at TRUE UTC must HIT the parquet row written under "
            "broker offset correction"
        )
        assert len(df) == 1

    def test_orchestrator_lookup_misses_without_offset_fix(self, tmp_path):
        """Diagnostic counter-test: WITHOUT the offset correction, the
        same lookup misses by exactly the offset (3h on FN-Server-2).

        This is the bug we just fixed — proves the test catches regressions
        if someone reverts the fix."""
        ticks_root = tmp_path / "ticks"

        true_utc = datetime(2026, 4, 28, 14, 30, 30, tzinfo=timezone.utc)
        broker_offset = 10800
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)

        # Annotate WITHOUT the fix (offset=0 = pre-fix behavior)
        annotated, _, _ = annotate_aggressor([tick], broker_offset_seconds=0)
        out_path = ticks_root / "XAUUSD_BROKEN" / "2026-04-28.parquet"
        write_ticks_parquet(annotated, out_path)

        # Lookup at TRUE UTC misses by 3h
        bar_open = datetime(2026, 4, 28, 14, 30, 0, tzinfo=timezone.utc)
        bar_close = datetime(2026, 4, 28, 14, 45, 0, tzinfo=timezone.utc)
        df = tf._read_ticks_for_bar("XAUUSD_BROKEN", bar_open, bar_close,
                                       ticks_root=ticks_root)
        # Pre-fix behavior: row stored at 17:30:30 ts_utc, lookup window
        # 14:30-14:45 -> empty result.
        assert df is None or df.empty, (
            "Pre-fix annotate_aggressor SHOULD miss the lookup. If this "
            "assertion fires the test no longer guards against the bug."
        )


# ---------------------------------------------------------------------------
# 3 — run_capture_loop forwards the offset to annotate_aggressor
# ---------------------------------------------------------------------------


class _FakeMT5:
    """Minimal mock that surfaces a single batch of broker-time ticks."""
    COPY_TICKS_ALL = 0xFFFFFFFF

    def __init__(self, ticks: list[dict]):
        self._ticks = ticks
        self._returned = False

    def copy_ticks_from(self, symbol, dt, count, flags):  # noqa: ARG002
        if self._returned:
            return []
        self._returned = True
        return list(self._ticks)


class TestRunCaptureLoopForwardsOffset:
    """The end-to-end daemon path must thread broker_offset_seconds from
    main() through run_capture_loop into annotate_aggressor."""

    def test_loop_writes_true_utc_when_offset_passed(self, tmp_path):
        ticks_root = tmp_path / "ticks"

        true_utc = datetime(2026, 4, 28, 14, 30, 30, tzinfo=timezone.utc)
        broker_offset = 10800
        tick = _broker_tick(true_utc, broker_offset_s=broker_offset)

        mock = _FakeMT5([tick])
        # Stop after one poll (we only return ticks once).
        stop_after = {"polls": 0}

        def stop():
            stop_after["polls"] += 1
            # Stop after the second poll (first delivers ticks, second
            # would get none and we want to flush + persist before exit).
            return stop_after["polls"] >= 3

        run_capture_loop(
            mock, "XAUUSD",
            poll_interval=0.01,
            flush_batch=1,           # flush each tick immediately
            stale_warn_sec=999.0,
            root=ticks_root,
            stop_predicate=stop,
            broker_offset_seconds=broker_offset,
        )

        # Verify the parquet file holds true UTC, not broker time.
        out_path = ticks_root / "XAUUSD" / "2026-04-28.parquet"
        assert out_path.exists(), "tick_capture loop did not flush parquet"
        df = pq.read_table(str(out_path)).to_pandas()
        assert len(df) == 1
        # ts_utc column should match true UTC (within ms tolerance)
        ts = pd.to_datetime(df["ts_utc"].iloc[0], utc=True)
        assert ts.to_pydatetime().replace(tzinfo=timezone.utc) == true_utc, (
            f"Loop should write TRUE UTC; got {ts}, expected {true_utc}"
        )

    def test_loop_default_offset_zero_preserves_legacy(self, tmp_path):
        """No offset passed -> behavior identical to pre-fix code."""
        ticks_root = tmp_path / "ticks"

        # On a "UTC broker" (offset 0), the tick's broker time IS UTC, so
        # passing no offset must give the same datetime back.
        true_utc = datetime(2026, 4, 28, 14, 30, 30, tzinfo=timezone.utc)
        tick = _broker_tick(true_utc, broker_offset_s=0)

        mock = _FakeMT5([tick])
        stop_after = {"polls": 0}

        def stop():
            stop_after["polls"] += 1
            return stop_after["polls"] >= 3

        run_capture_loop(
            mock, "XAUUSD",
            poll_interval=0.01,
            flush_batch=1,
            stale_warn_sec=999.0,
            root=ticks_root,
            stop_predicate=stop,
            # broker_offset_seconds defaults to 0
        )

        out_path = ticks_root / "XAUUSD" / "2026-04-28.parquet"
        assert out_path.exists()
        df = pq.read_table(str(out_path)).to_pandas()
        ts = pd.to_datetime(df["ts_utc"].iloc[0], utc=True)
        assert ts.to_pydatetime().replace(tzinfo=timezone.utc) == true_utc
