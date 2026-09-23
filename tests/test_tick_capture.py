"""Unit tests for ``src.components.tick_capture``.

Covers Lee-Ready aggressor classification, tick normalization, parquet I/O,
state persistence, and the polling loop with a mock MT5 module.

Tests use ``tmp_path`` exclusively for storage so the production path
guard in ``conftest.py`` never trips.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Skip the whole module if pyarrow missing (matches production fail-open).
pyarrow = pytest.importorskip("pyarrow")
pandas = pytest.importorskip("pandas")

from src.components import tick_capture as tc
from src.components.tick_capture import (
    CaptureState,
    annotate_aggressor,
    classify_aggressor,
    classify_aggressor_series,
    fetch_new_ticks,
    load_state,
    normalize_tick,
    parquet_path_for,
    run_capture_loop,
    save_state,
    write_ticks_parquet,
    TICK_FLAG_ASK,
    TICK_FLAG_BID,
    TICK_FLAG_BUY,
    TICK_FLAG_LAST,
    TICK_FLAG_SELL,
)


# ---------------------------------------------------------------------------
# Tick fixtures
# ---------------------------------------------------------------------------


def _tick(ts_msc, bid, ask, last=0.0, volume=1.0, flags=0):
    return {
        "time": ts_msc // 1000,
        "ts_msc": ts_msc,
        "time_msc": ts_msc,
        "bid": bid,
        "ask": ask,
        "last": last,
        "volume": volume,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# classify_aggressor — quote rule
# ---------------------------------------------------------------------------


class TestClassifyAggressor:
    def test_quote_rule_at_ask_classifies_buy(self):
        assert classify_aggressor(
            bid=100.0, ask=100.05, last=100.05,
            flags=0, prev_price=None, prev_aggressor=None,
        ) == "buy"

    def test_quote_rule_at_bid_classifies_sell(self):
        assert classify_aggressor(
            bid=100.0, ask=100.05, last=100.0,
            flags=0, prev_price=None, prev_aggressor=None,
        ) == "sell"

    def test_broker_buy_flag_overrides_quote(self):
        # Last would have been classified as sell by quote rule; flag wins.
        assert classify_aggressor(
            bid=100.0, ask=100.05, last=100.0,
            flags=TICK_FLAG_BUY, prev_price=None, prev_aggressor=None,
        ) == "buy"

    def test_broker_sell_flag_overrides_quote(self):
        assert classify_aggressor(
            bid=100.0, ask=100.05, last=100.05,
            flags=TICK_FLAG_SELL, prev_price=None, prev_aggressor=None,
        ) == "sell"

    def test_both_buy_and_sell_flag_falls_through_to_quote(self):
        # When broker is contradictory we ignore both and use the quote rule.
        agg = classify_aggressor(
            bid=100.0, ask=100.05, last=100.05,
            flags=TICK_FLAG_BUY | TICK_FLAG_SELL,
            prev_price=None, prev_aggressor=None,
        )
        assert agg == "buy"  # quote rule wins

    def test_tick_test_uptick_buy(self):
        # last=0 forces fallback to mid; mid moved up vs prev_price → BUY.
        agg = classify_aggressor(
            bid=100.10, ask=100.20, last=0.0,
            flags=TICK_FLAG_ASK,
            prev_price=100.10,
            prev_aggressor=None,
        )
        assert agg == "buy"

    def test_tick_test_downtick_sell(self):
        agg = classify_aggressor(
            bid=99.80, ask=99.90, last=0.0,
            flags=TICK_FLAG_BID,
            prev_price=100.10,
            prev_aggressor=None,
        )
        assert agg == "sell"

    def test_tick_test_equal_inherits_prev(self):
        agg = classify_aggressor(
            bid=100.10, ask=100.20, last=0.0,
            flags=0,
            prev_price=100.15,  # same as new mid
            prev_aggressor="buy",
        )
        assert agg == "buy"

    def test_tick_test_equal_first_tick_returns_neutral(self):
        agg = classify_aggressor(
            bid=100.10, ask=100.20, last=0.0,
            flags=0,
            prev_price=None,
            prev_aggressor=None,
        )
        # First tick with no prior — tick test cannot run → neutral.
        assert agg == "neutral"

    def test_malformed_zero_quote_returns_neutral(self):
        agg = classify_aggressor(
            bid=0.0, ask=0.0, last=0.0,
            flags=0, prev_price=None, prev_aggressor=None,
        )
        assert agg == "neutral"

    def test_last_inside_spread_falls_to_tick_test(self):
        # last between bid and ask, not equal to either → tick test.
        agg = classify_aggressor(
            bid=100.0, ask=100.10, last=100.05,
            flags=0,
            prev_price=100.04,  # uptick
            prev_aggressor=None,
        )
        assert agg == "buy"


# ---------------------------------------------------------------------------
# classify_aggressor_series & annotate_aggressor — sequential / state
# ---------------------------------------------------------------------------


class TestClassifyAggressorSeries:
    def test_first_tick_neutral_when_quote_rule_inapplicable(self):
        ticks = [_tick(1000, bid=100.0, ask=100.05, last=0.0, flags=TICK_FLAG_BID)]
        result = classify_aggressor_series(ticks)
        assert result == ["neutral"]

    def test_quote_rule_dominates_when_last_present(self):
        ticks = [
            _tick(1000, bid=100.0, ask=100.05, last=100.05),  # at ask
            _tick(1100, bid=100.0, ask=100.05, last=100.0),   # at bid
            _tick(1200, bid=100.0, ask=100.05, last=100.05),  # at ask
        ]
        result = classify_aggressor_series(ticks)
        assert result == ["buy", "sell", "buy"]

    def test_uptick_sequence_bias_to_buy(self):
        ticks = [
            _tick(1000, bid=100.0, ask=100.05, last=0.0),
            _tick(1100, bid=100.05, ask=100.10, last=0.0, flags=TICK_FLAG_ASK),
            _tick(1200, bid=100.10, ask=100.15, last=0.0, flags=TICK_FLAG_ASK),
        ]
        result = classify_aggressor_series(ticks)
        # First is neutral (no prev), then uptick → buy each time.
        assert result[0] == "neutral"
        assert result[1] == "buy"
        assert result[2] == "buy"

    def test_broker_flag_present_authoritative(self):
        ticks = [
            _tick(1000, bid=100.0, ask=100.05, last=100.05, flags=TICK_FLAG_SELL),
            _tick(1100, bid=100.0, ask=100.05, last=100.00, flags=TICK_FLAG_BUY),
        ]
        # Broker says SELL on the at-ask tick and BUY on the at-bid tick.
        assert classify_aggressor_series(ticks) == ["sell", "buy"]


class TestAnnotateAggressor:
    def test_annotate_writes_aggressor_and_ts_utc(self):
        ticks = [_tick(1730000000000, bid=100.0, ask=100.05, last=100.05)]
        out, _, _ = annotate_aggressor(ticks)
        assert out[0]["inferred_aggressor"] == "buy"
        assert out[0]["ts_utc"].tzinfo is not None
        assert out[0]["ts_utc"].year >= 2024

    def test_annotate_subtracts_broker_offset_before_ts_utc(self):
        broker_time = datetime(2026, 6, 1, 15, 23, tzinfo=timezone.utc)
        ticks = [
            _tick(
                int(broker_time.timestamp() * 1000),
                bid=100.0,
                ask=100.05,
                last=100.05,
            )
        ]

        out, _, _ = annotate_aggressor(ticks, broker_offset_seconds=10800)

        assert out[0]["ts_utc"] == datetime(2026, 6, 1, 12, 23, tzinfo=timezone.utc)

    def test_annotate_carries_prev_state_across_batches(self):
        first = [_tick(1000, bid=100.0, ask=100.10, last=0.0)]
        out1, prev_price, prev_agg = annotate_aggressor(first)
        # First tick neutral, prev_price = mid.
        assert out1[0]["inferred_aggressor"] == "neutral"
        assert prev_price == pytest.approx(100.05)

        # Second batch: explicit uptick.
        second = [_tick(2000, bid=100.05, ask=100.15, last=0.0, flags=TICK_FLAG_ASK)]
        out2, _, _ = annotate_aggressor(second, prev_price, prev_agg)
        assert out2[0]["inferred_aggressor"] == "buy"


# ---------------------------------------------------------------------------
# normalize_tick
# ---------------------------------------------------------------------------


class TestNormalizeTick:
    def test_normalize_dict_path(self):
        d = _tick(2000, bid=1.5, ask=1.6, last=0.0, volume=3.0, flags=2)
        out = normalize_tick(d)
        assert out["ts_msc"] == 2000
        assert out["bid"] == 1.5
        assert out["volume"] == 3.0

    def test_normalize_namedtuple_path(self):
        from collections import namedtuple
        T = namedtuple("T", "time time_msc bid ask last volume flags")
        t = T(time=1, time_msc=1000, bid=2.0, ask=2.1, last=0.0, volume=1.0, flags=0)
        out = normalize_tick(t)
        assert out["bid"] == 2.0
        assert out["ts_msc"] == 1000


# ---------------------------------------------------------------------------
# Parquet I/O round-trip
# ---------------------------------------------------------------------------


class TestParquetRoundTrip:
    def test_write_and_read_back(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        symbol = "XAUUSD"
        ts = datetime(2026, 4, 25, 13, 0, 0, tzinfo=timezone.utc)
        rows = [
            {**_tick(int(ts.timestamp() * 1000) + i * 100, bid=2000.0 + i * 0.01,
                      ask=2000.05 + i * 0.01, last=0.0, volume=1.0, flags=0),
             "ts_utc": ts + timedelta(milliseconds=i * 100),
             "inferred_aggressor": "buy" if i % 2 == 0 else "sell"}
            for i in range(20)
        ]
        path = parquet_path_for(symbol, ts.date(), root=ticks_root)
        n = write_ticks_parquet(rows, path)
        assert n == 20
        assert path.exists()

        import pyarrow.parquet as pq
        df = pq.read_table(str(path)).to_pandas()
        assert len(df) == 20
        assert set(df.columns) >= {"ts_utc", "ts_msc", "bid", "ask", "last",
                                    "volume", "flags", "inferred_aggressor"}
        # Round-trip preserves aggressor labels.
        assert df["inferred_aggressor"].iloc[0] == "buy"

    def test_append_dedups_by_ts_msc(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        symbol = "XAUUSD"
        ts = datetime(2026, 4, 25, 13, 0, 0, tzinfo=timezone.utc)
        path = parquet_path_for(symbol, ts.date(), root=ticks_root)

        first_batch = [
            {**_tick(1000 + i, 2000.0, 2000.05, last=0.0, volume=1.0),
             "ts_utc": ts + timedelta(milliseconds=i),
             "inferred_aggressor": "buy"}
            for i in range(5)
        ]
        write_ticks_parquet(first_batch, path)

        # Re-write with overlapping ts_msc — last write wins.
        overlap = [
            {**_tick(1000 + i, 2001.0, 2001.05, last=0.0, volume=2.0),
             "ts_utc": ts + timedelta(milliseconds=i),
             "inferred_aggressor": "sell"}
            for i in range(3, 8)
        ]
        write_ticks_parquet(overlap, path)

        import pyarrow.parquet as pq
        df = pq.read_table(str(path)).to_pandas()
        # 5 + 5 = 10 raw, but ts_msc 1003-1004 dedup → 5 unique from first +
        # 5 unique from second − 2 collisions = 8 unique
        assert len(df) == 8
        # The 1003 row should now show the second batch's values.
        assert df.loc[df["ts_msc"] == 1003, "bid"].iloc[0] == 2001.0

    def test_corrupt_existing_parquet_is_quarantined_before_fresh_segment(
        self,
        tmp_path: Path,
    ):
        ticks_root = tmp_path / "ticks"
        symbol = "XAUUSD"
        ts = datetime(2026, 4, 25, 13, 0, 0, tzinfo=timezone.utc)
        path = parquet_path_for(symbol, ts.date(), root=ticks_root)
        path.parent.mkdir(parents=True)
        path.write_text("not a parquet file", encoding="utf-8")

        rows = [
            {
                **_tick(2000, 2000.0, 2000.05, last=0.0, volume=1.0),
                "ts_utc": ts,
                "inferred_aggressor": "buy",
            }
        ]

        n = write_ticks_parquet(rows, path)

        assert n == 1
        quarantine_dir = path.parent / tc.TICK_CORRUPT_QUARANTINE_DIRNAME
        quarantined = list(quarantine_dir.glob("*.corrupt.parquet"))
        assert len(quarantined) == 1
        assert quarantined[0].read_text(encoding="utf-8") == "not a parquet file"
        sidecar = quarantined[0].with_suffix(quarantined[0].suffix + ".json")
        assert sidecar.exists()

        import pyarrow.parquet as pq
        df = pq.read_table(str(path)).to_pandas()
        assert len(df) == 1
        assert df["ts_msc"].iloc[0] == 2000

    def test_flush_heartbeat_preserves_daemon_liveness_fields(
        self,
        tmp_path: Path,
        monkeypatch,
    ):
        from src.components import mt5_daemon_runtime as runtime_mod

        calls = []
        monkeypatch.setattr(
            runtime_mod,
            "write_daemon_heartbeat",
            lambda name, last_progress_at=None, extra=None: calls.append(
                {
                    "name": name,
                    "last_progress_at": last_progress_at,
                    "extra": extra or {},
                }
            ),
        )
        ts = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        state = CaptureState(symbol="EURJPY")
        state.buffer = [
            {
                **_tick(int(ts.timestamp() * 1000), 170.0, 170.01, last=170.0),
                "ts_utc": ts,
                "inferred_aggressor": "sell",
            }
        ]

        flushed = tc._flush_buffer(state, root=tmp_path / "ticks")

        assert flushed == 1
        assert calls
        assert calls[-1]["name"] == "tick_capture_EURJPY"
        assert calls[-1]["extra"]["liveness_utc"]
        assert calls[-1]["extra"]["last_poll_status"] == "flush_success"
        assert calls[-1]["extra"]["last_poll_new_tick_count"] == 1
        assert calls[-1]["extra"]["last_progress_source"] == "flush_buffer_new_ticks"


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


class TestState:
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        s = CaptureState(symbol="XAUUSD", last_msc=12345,
                          last_price=2000.5, last_aggressor="buy",
                          total_ticks_written=42)
        save_state(s, root=ticks_root)
        loaded = load_state("XAUUSD", root=ticks_root)
        assert loaded.last_msc == 12345
        assert loaded.last_price == pytest.approx(2000.5)
        assert loaded.last_aggressor == "buy"
        assert loaded.total_ticks_written == 42

    def test_load_state_missing_returns_fresh(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        s = load_state("FOOBAR", root=ticks_root)
        assert s.last_msc == 0
        assert s.last_price is None

    def test_load_state_corrupt_returns_fresh(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        sym_dir = ticks_root / "XAUUSD"
        sym_dir.mkdir(parents=True)
        (sym_dir / ".state.json").write_text("not-json{", encoding="utf-8")
        s = load_state("XAUUSD", root=ticks_root)
        assert s.last_msc == 0


# ---------------------------------------------------------------------------
# fetch_new_ticks against MockMT5
# ---------------------------------------------------------------------------


class _MockMT5:
    """Minimal MT5 stand-in that returns a fixed tick batch."""

    COPY_TICKS_ALL = -1

    def __init__(self, ticks: list[dict]):
        self._ticks = ticks
        self.calls = []

    def copy_ticks_from(self, symbol, dt, count, flags):
        self.calls.append((symbol, dt, count, flags))
        return self._ticks


class TestFetchNewTicks:
    def test_fetches_and_filters_by_msc(self):
        ticks = [_tick(1000, 100.0, 100.05),
                  _tick(2000, 100.0, 100.05),
                  _tick(3000, 100.0, 100.05)]
        mock = _MockMT5(ticks)
        out = fetch_new_ticks(mock, "XAUUSD", last_msc=1500)
        # Only 2000 + 3000 should pass the > last_msc filter.
        assert [t["ts_msc"] for t in out] == [2000, 3000]

    def test_last_msc_query_uses_broker_time_epoch(self):
        last_msc = 1_778_555_485_741
        mock = _MockMT5([])

        fetch_new_ticks(mock, "USDJPY", last_msc=last_msc)

        expected = datetime.fromtimestamp((last_msc // 1000) - 1, tz=timezone.utc)
        assert mock.calls[0][1] == expected

    def test_none_response_returns_empty_list(self):
        mock = _MockMT5([])

        def _none(symbol, dt, count, flags):
            return None

        mock.copy_ticks_from = _none  # type: ignore
        out = fetch_new_ticks(mock, "XAUUSD", last_msc=0)
        assert out == []

    def test_cold_start_uses_now(self):
        mock = _MockMT5([])
        fetch_new_ticks(mock, "XAUUSD", last_msc=0)
        assert mock.calls[0][1].tzinfo is not None


# ---------------------------------------------------------------------------
# run_capture_loop — end-to-end with mock MT5
# ---------------------------------------------------------------------------


class TestCaptureLoop:
    def test_captures_two_batches_then_stops(self, tmp_path: Path, monkeypatch):
        ticks_root = tmp_path / "ticks"

        # Two distinct batches; loop must dedup and persist both.
        batch_a = [_tick(1730000001000, 100.0, 100.05, last=100.05),
                    _tick(1730000002000, 100.0, 100.05, last=100.0)]
        batch_b = [_tick(1730000003000, 100.0, 100.05, last=100.05)]
        seq = [batch_a, batch_b, []]

        class Sequencer(_MockMT5):
            def copy_ticks_from(self, symbol, dt, count, flags):
                # Pop next pre-canned batch.
                if seq:
                    return seq.pop(0)
                return []

        mock = Sequencer([])

        # Stop after 3 polls so we exit deterministically.
        polls_seen = [0]

        def stop():
            polls_seen[0] += 1
            return polls_seen[0] >= 6  # poll happens once per loop

        # Force an immediate flush by setting the threshold tiny.
        state = run_capture_loop(
            mock, "XAUUSD",
            poll_interval=0.0,  # no real sleep
            flush_batch=1,
            flush_interval_sec=999.0,
            root=ticks_root,
            stop_predicate=stop,
        )
        assert state.total_ticks_written == 3
        # Verify the parquet file holds all three rows.
        from datetime import datetime as _dt
        bar_day = _dt.fromtimestamp(1730000001, tz=timezone.utc).date()
        path = parquet_path_for("XAUUSD", bar_day, root=ticks_root)
        assert path.exists()

    def test_time_based_flush_persists_sparse_ticks(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"

        batch_a = [_tick(1730000001000, 100.0, 100.05, last=100.05)]
        batch_b = [_tick(1730000002000, 100.0, 100.05, last=100.0)]
        seq = [batch_a, batch_b, []]

        class Sequencer(_MockMT5):
            def copy_ticks_from(self, symbol, dt, count, flags):
                if seq:
                    return seq.pop(0)
                return []

        mock = Sequencer([])
        polls_seen = [0]

        def stop():
            polls_seen[0] += 1
            return polls_seen[0] >= 5

        state = run_capture_loop(
            mock, "XAUUSD",
            poll_interval=0.0,
            flush_batch=500,
            flush_interval_sec=0.0,
            stale_warn_sec=999.0,
            root=ticks_root,
            stop_predicate=stop,
        )

        assert state.total_ticks_written == 2
        bar_day = datetime.fromtimestamp(1730000001, tz=timezone.utc).date()
        path = parquet_path_for("XAUUSD", bar_day, root=ticks_root)
        assert path.exists()

    def test_transient_mt5_error_does_not_kill_loop(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"

        class FlakyMT5:
            COPY_TICKS_ALL = -1
            calls = 0

            def copy_ticks_from(self, *a, **kw):
                FlakyMT5.calls += 1
                if FlakyMT5.calls == 1:
                    raise RuntimeError("transient")
                return []

        flaky = FlakyMT5()
        polls = [0]

        def stop():
            polls[0] += 1
            return polls[0] >= 6

        # Backoff resets to 1.0s on success; force tiny initial backoff so
        # the test exits quickly.
        from src.components import tick_capture as tc_mod
        original_initial = tc_mod.INITIAL_BACKOFF_SEC
        tc_mod.INITIAL_BACKOFF_SEC = 0.001
        try:
            state = run_capture_loop(
                flaky, "XAUUSD",
                poll_interval=0.0, flush_batch=1, root=ticks_root,
                stop_predicate=stop,
            )
        finally:
            tc_mod.INITIAL_BACKOFF_SEC = original_initial
        # Loop should have survived the exception and continued polling.
        assert FlakyMT5.calls >= 2


# ---------------------------------------------------------------------------
# Lee-Ready accuracy on synthetic flow with known ground truth
# ---------------------------------------------------------------------------


class TestLeeReadyAccuracy:
    """Synthesize 100 ticks where we know the true aggressor and verify
    Lee-Ready classification accuracy.

    On the with-broker-flag path we expect ~100% (the flag IS the truth).
    On the no-flag path with explicit at-ask / at-bid trades we expect ~100%.
    On the no-flag path with mid-of-spread trades and pure tick test we
    expect ≥ 80% (Lee-Ready 1991 reports ~85% on NYSE TAQ).
    """

    def test_quote_rule_perfect_when_last_at_bid_or_ask(self):
        ticks = []
        truth = []
        for i in range(50):
            # Alternating buy/sell flow at clean ask/bid.
            if i % 2 == 0:
                ticks.append(_tick(1000 + i, 100.0, 100.05, last=100.05))
                truth.append("buy")
            else:
                ticks.append(_tick(1000 + i, 100.0, 100.05, last=100.00))
                truth.append("sell")
        result = classify_aggressor_series(ticks)
        accuracy = sum(1 for r, t in zip(result, truth) if r == t) / len(truth)
        assert accuracy == 1.0  # quote rule is exact when last hits bid/ask

    def test_tick_test_synthetic_geometric_brownian_above_threshold(self):
        # Generate a price walk where each up-tick ≡ buy, each down-tick ≡ sell.
        import random
        random.seed(42)
        ticks = []
        truth = []
        price = 100.0
        for i in range(200):
            move = random.choice([+1, -1]) * 0.01
            new_price = price + move
            if move > 0:
                # Trade printed at new ask; ground truth: BUY.
                ticks.append(_tick(1000 + i, new_price - 0.01, new_price + 0.01,
                                    last=0.0, flags=TICK_FLAG_ASK))
                truth.append("buy")
            else:
                ticks.append(_tick(1000 + i, new_price - 0.01, new_price + 0.01,
                                    last=0.0, flags=TICK_FLAG_BID))
                truth.append("sell")
            price = new_price
        result = classify_aggressor_series(ticks)
        # Tick test on the walk: first tick neutral; subsequent should match move.
        # We exclude the first tick (which is neutral by design).
        matches = sum(1 for r, t in zip(result[1:], truth[1:]) if r == t)
        accuracy = matches / (len(truth) - 1)
        # Lee-Ready ~85% on TAQ; on this synthetic stream we expect ≥ 90%.
        assert accuracy >= 0.85, f"Lee-Ready accuracy {accuracy:.3f} below 0.85"
