"""Tests for Component 1 — Live Data Ingestion (Phase 2)."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from src.components.data_ingestion import (
    DataIncompleteError,
    SourceChronologyError,
    SourceTimebaseError,
    compute_session_levels,
    detect_equal_levels,
    filter_closed_candles,
    infer_latest_closed_m15_timestamp,
    ingest_live_data,
    repair_malformed_m15_ohlc_from_ticks,
    repair_malformed_ohlc_from_ticks,
    _previous_weekday,
)
from src.mt5.mt5_mock import MockMT5
from src.research_infra.completed_bar_witness import (
    COMPLETION_SEMANTICS,
    ROW_WITNESS_FIELD,
    WITNESS_TYPE,
)


def _make_m15_candle(dt_str: str, o=2650.0, h=2655.0, l=2645.0, c=2652.0) -> dict:
    return {"time": dt_str, "open": o, "high": h, "low": l, "close": c, "volume": 100}


def _make_candles(count: int, base_time: str = "2026-04-01T00:00:00+00:00") -> list[dict]:
    """Generate *count* dummy candles starting from *base_time*."""
    from datetime import timedelta
    dt = datetime.fromisoformat(base_time)
    candles = []
    for i in range(count):
        t = dt + timedelta(minutes=15 * i)
        candles.append({
            "time": t.isoformat(),
            "open": 2650.0 + i * 0.1,
            "high": 2655.0 + i * 0.1,
            "low": 2645.0 + i * 0.1,
            "close": 2652.0 + i * 0.1,
            "volume": 100,
        })
    return candles


class TestComputeSessionLevels:
    def test_asian_hl_computation(self):
        # Asian candle (02:00 UTC on target date)
        candles = [
            _make_m15_candle("2026-04-01T02:00:00+00:00", h=2660.0, l=2640.0),
            _make_m15_candle("2026-04-01T05:00:00+00:00", h=2670.0, l=2635.0),
        ]
        result = compute_session_levels(candles, date(2026, 4, 1))
        assert result["asian_high"] == 2670.0
        assert result["asian_low"] == 2635.0

    def test_pdh_pdl_from_previous_day(self):
        candles = [
            # Previous day candle (Wednesday March 31)
            _make_m15_candle("2026-03-31T10:00:00+00:00", h=2680.0, l=2620.0),
            _make_m15_candle("2026-03-31T14:00:00+00:00", h=2690.0, l=2615.0),
            # Today's Asian candle
            _make_m15_candle("2026-04-01T03:00:00+00:00", h=2650.0, l=2640.0),
        ]
        result = compute_session_levels(candles, date(2026, 4, 1))
        assert result["pdh"] == 2690.0
        assert result["pdl"] == 2615.0

    def test_no_candles_returns_zeros(self):
        result = compute_session_levels([], date(2026, 4, 1))
        assert result["asian_high"] == 0.0
        assert result["pdh"] == 0.0

    def test_initial_session_levels_are_none(self):
        result = compute_session_levels([], date(2026, 4, 1))
        assert result["session_high"] is None
        assert result["london_high"] is None


class TestPreviousWeekday:
    def test_monday_returns_friday(self):
        assert _previous_weekday(date(2026, 4, 6)) == date(2026, 4, 3)  # Mon -> Fri

    def test_tuesday_returns_monday(self):
        assert _previous_weekday(date(2026, 4, 7)) == date(2026, 4, 6)  # Tue -> Mon

    def test_sunday_returns_friday(self):
        assert _previous_weekday(date(2026, 4, 5)) == date(2026, 4, 3)  # Sun -> Fri


class TestDetectEqualLevels:
    @staticmethod
    def _legacy_detect_equal_levels(candles, side, tolerance=2.50):
        key = "high" if side == "high" else "low"
        levels = []
        used = set()
        for i in range(len(candles)):
            if i in used:
                continue
            price_i = candles[i][key]
            group = [i]
            for j in range(i + 1, len(candles)):
                if j in used:
                    continue
                if abs(candles[j][key] - price_i) <= tolerance:
                    group.append(j)
            if len(group) >= 2:
                avg_price = sum(candles[k][key] for k in group) / len(group)
                levels.append({
                    "price": round(avg_price, 2),
                    "count": len(group),
                    "candle_indices": group,
                })
                used.update(group)
        return levels

    def test_finds_equal_highs(self):
        candles = [
            {"high": 2650.0, "low": 2640.0},
            {"high": 2651.0, "low": 2638.0},  # Within 2.50 tolerance of first
            {"high": 2700.0, "low": 2690.0},  # Not close
        ]
        result = detect_equal_levels(candles, "high", tolerance=2.50)
        assert len(result) == 1
        assert result[0]["count"] == 2
        assert 0 in result[0]["candle_indices"]
        assert 1 in result[0]["candle_indices"]

    def test_no_equal_levels(self):
        candles = [
            {"high": 2650.0, "low": 2640.0},
            {"high": 2700.0, "low": 2690.0},
        ]
        result = detect_equal_levels(candles, "high", tolerance=2.50)
        assert len(result) == 0

    def test_bucketed_detector_preserves_legacy_greedy_grouping(self):
        candles = [
            {"high": 100.0, "low": 90.0},
            {"high": 101.0, "low": 90.5},
            {"high": 102.4, "low": 89.0},
            {"high": 103.0, "low": 88.9},
            {"high": 105.2, "low": 86.2},
            {"high": 106.1, "low": 85.7},
            {"high": 108.9, "low": 83.2},
            {"high": 111.2, "low": 80.1},
        ]
        expected = self._legacy_detect_equal_levels(candles, "high", tolerance=2.50)
        assert detect_equal_levels(candles, "high", tolerance=2.50) == expected


class TestIngestLiveData:
    def _setup_mt5_with_candles(self) -> MockMT5:
        mt5 = MockMT5()
        mt5.connect()
        # Set sufficient candles for each timeframe
        from src.components.data_ingestion import TF_MAP, DEFAULT_LOOKBACKS
        for tf_name, tf_const in TF_MAP.items():
            count = DEFAULT_LOOKBACKS[tf_name]
            candles = _make_candles(count)
            mt5.set_candles(tf_const, candles)
        return mt5

    def test_ingest_returns_correct_structure(self):
        mt5 = self._setup_mt5_with_candles()
        config = {
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)

        # Check all required keys exist
        assert "timestamp_utc" in result
        assert "candles" in result
        assert "session_levels" in result
        assert "equal_highs_H4" in result
        assert "equal_lows_H4" in result
        assert "equal_highs_H1" in result
        assert "equal_lows_H1" in result
        assert "spread_cents" in result
        assert "data_quality" in result
        assert "high_impact_events" in result

        # Check candles have all timeframes
        for tf in ("D1", "H4", "H1", "M15"):
            assert tf in result["candles"]
            assert len(result["candles"][tf]) > 0

    def test_data_quality_fields(self):
        mt5 = self._setup_mt5_with_candles()
        config = {
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)
        dq = result["data_quality"]
        assert dq["all_timeframes_complete"] is True
        assert dq["mt5_connected"] is True
        assert "timestamp_utc" in dq

    def test_insufficient_candles_raises(self):
        mt5 = MockMT5()
        mt5.connect()
        # Only set a few candles for D1
        mt5.set_candles(1440, [_make_m15_candle("2026-04-01T00:00:00+00:00")] * 5)
        config = {
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        with pytest.raises(DataIncompleteError, match="Insufficient D1 candles"):
            ingest_live_data(mt5, config)

    def test_spread_included(self):
        mt5 = self._setup_mt5_with_candles()
        mt5.set_tick(2650.00, 2650.20)
        config = {
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)
        assert result["spread_cents"] == pytest.approx(20.0, abs=0.1)

    def test_infers_latest_closed_m15_when_new_bar_is_in_progress(self):
        candles = [
            _make_m15_candle("2026-05-01T13:00:00+00:00"),
            _make_m15_candle("2026-05-01T13:15:00+00:00"),
        ]

        result = infer_latest_closed_m15_timestamp(
            candles,
            now_utc=datetime(2026, 5, 1, 13, 20, 5, tzinfo=timezone.utc),
        )

        assert result["candle_open_utc"] == "2026-05-01T13:00:00+00:00"
        assert result["candle_close_utc"] == "2026-05-01T13:15:00+00:00"
        assert result["candle_timestamp_source"] == "latest_closed_m15_bar"
        assert result["candle_close_lag_seconds"] == 305.0

    def test_filter_closed_candles_removes_current_malformed_forming_bar(self):
        closed = _make_m15_candle(
            "2026-06-01T20:45:00+00:00",
            o=71586.90,
            h=71604.40,
            l=71584.00,
            c=71603.55,
        )
        malformed_forming = _make_m15_candle(
            "2026-06-01T21:00:00+00:00",
            o=71441.16,
            h=71442.24,
            l=592.19,
            c=592.86,
        )

        result = filter_closed_candles(
            [closed, malformed_forming],
            "M15",
            now_utc=datetime(2026, 6, 1, 21, 7, tzinfo=timezone.utc),
        )

        assert result == [closed]

    def test_truth_closed_bar_requires_aware_adjacent_successor_witness(self):
        row = _make_m15_candle("2026-06-01T20:45:00+00:00")
        row[ROW_WITNESS_FIELD] = {
            "witness_type": WITNESS_TYPE,
            "completion_semantics": COMPLETION_SEMANTICS,
            "timeframe": "M15",
            "predecessor_source_ordinal": 41,
            "successor_source_ordinal": 42,
            "predecessor_open_utc": "2026-06-01T20:45:00+00:00",
            "successor_open_utc": "2026-06-01T21:00:00+00:00",
            "successor_market_values_consumed": False,
        }

        assert filter_closed_candles(
            [row],
            "M15",
            now_utc=datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
            require_aware_utc=True,
            future_tolerance_seconds=0.0,
            reject_future_rows=True,
            require_completion_witness=True,
        ) == [row]

        with pytest.raises(
            SourceChronologyError,
            match="completion_witness_adjacency_invalid",
        ):
            filter_closed_candles(
                [row],
                "M15",
                now_utc=datetime(
                    2026, 6, 1, 20, 59, 59, 999999, tzinfo=timezone.utc
                ),
                require_aware_utc=True,
                future_tolerance_seconds=0.0,
                reject_future_rows=True,
                require_completion_witness=True,
            )

    def test_truth_closed_bar_refuses_naive_and_unwitnessed_terminal_rows(self):
        naive = _make_m15_candle("2026-06-01T20:45:00")
        with pytest.raises(SourceTimebaseError, match="M15_row_0_time_naive"):
            filter_closed_candles(
                [naive],
                "M15",
                now_utc=datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
                require_aware_utc=True,
                require_completion_witness=True,
            )

        aware = _make_m15_candle("2026-06-01T20:45:00+00:00")
        with pytest.raises(
            SourceChronologyError, match="completion_witness_missing"
        ):
            filter_closed_candles(
                [aware],
                "M15",
                now_utc=datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
                require_aware_utc=True,
                require_completion_witness=True,
            )

        # Engineering/default behavior remains the historical nominal-close path.
        assert filter_closed_candles(
            [aware],
            "M15",
            now_utc=datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
        ) == [aware]

    def test_ingest_trims_unclosed_bars_before_market_state_inputs(self):
        from src.components import data_ingestion as di
        from src.components.data_ingestion import DEFAULT_LOOKBACKS, TF_MAP, TF_MINUTES

        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = datetime(2026, 6, 1, 21, 7, tzinfo=timezone.utc)
                return value if tz is None else value.astimezone(tz)

        def _tf_candles(total: int, minutes: int, last_open: datetime) -> list[dict]:
            first_open = last_open - timedelta(minutes=minutes * (total - 1))
            rows = []
            for idx in range(total):
                t = first_open + timedelta(minutes=minutes * idx)
                rows.append(
                    {
                        "time": t.isoformat(),
                        "open": 100.0 + idx,
                        "high": 101.0 + idx,
                        "low": 99.0 + idx,
                        "close": 100.5 + idx,
                        "volume": 100,
                    }
                )
            return rows

        mt5 = MockMT5()
        mt5.connect()
        last_open_by_tf = {
            "D1": datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
            "H4": datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
            "H1": datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
            "M15": datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
        }
        for tf_name, tf_const in TF_MAP.items():
            count = DEFAULT_LOOKBACKS[tf_name]
            candles = _tf_candles(count + 1, TF_MINUTES[tf_name], last_open_by_tf[tf_name])
            if tf_name == "M15":
                candles[-1].update(
                    {"open": 71441.16, "high": 71442.24, "low": 592.19, "close": 592.86}
                )
            mt5.set_candles(tf_const, candles)

        config = {
            "market": {"symbol": "BTCUSD"},
            "data": {"lookback": DEFAULT_LOOKBACKS},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        with patch.object(di, "datetime", FixedDatetime):
            result = ingest_live_data(mt5, config)

        assert result["candles"]["M15"][-1]["time"] == "2026-06-01T20:45:00+00:00"
        assert result["candles"]["M15"][-1]["close"] != 592.86
        for tf_name in ("D1", "H4", "H1", "M15"):
            stats = result["data_quality"]["closed_bar_filter"][tf_name]
            assert stats["removed_unclosed_count"] == 1
            assert len(result["candles"][tf_name]) == DEFAULT_LOOKBACKS[tf_name] - 1

    def test_closed_malformed_m15_bar_repairs_from_tick_parquet(self, monkeypatch):
        pd = pytest.importorskip("pandas")
        from src.components import data_ingestion as di

        previous = _make_m15_candle(
            "2026-06-01T20:45:00+00:00",
            o=71586.90,
            h=71604.40,
            l=71584.00,
            c=71603.55,
        )
        malformed_closed = _make_m15_candle(
            "2026-06-01T21:00:00+00:00",
            o=71441.16,
            h=71442.24,
            l=592.06,
            c=592.86,
        )
        tick_rows = pd.DataFrame(
            {
                "bid": [71441.16, 71340.0, 71172.5, 71210.25],
                "ask": [71465.0, 71364.0, 71196.5, 71234.25],
            }
        )

        calls = []

        def fake_reader(symbol, bar_open, bar_close, ticks_root=None):
            calls.append((symbol, bar_open, bar_close, ticks_root))
            return tick_rows

        monkeypatch.setattr(di, "_tick_read_ticks_for_bar", fake_reader)
        monkeypatch.setattr(di, "_TICKS_ROOT", di._TICKS_ROOT or "data/ticks")

        repaired, report = repair_malformed_m15_ohlc_from_ticks(
            [previous, malformed_closed],
            "BTCUSD",
            {
                "gtos_vnext_runtime": {
                    "moonshot_broader_origin_max_interbar_price_jump_ratio": 0.35
                }
            },
        )

        assert calls
        assert report["repaired_count"] == 1
        assert report["failed_count"] == 0
        assert repaired[-1]["open"] == 71441.16
        assert repaired[-1]["high"] == 71441.16
        assert repaired[-1]["low"] == 71172.5
        assert repaired[-1]["close"] == 71210.25
        assert repaired[-1]["volume"] == 4
        assert repaired[-1]["ohlc_source_repair"]["status"] == "repaired_from_local_tick_parquet"
        assert repaired[-1]["ohlc_source_repair"]["reason"] == "m15_interbar_price_jump_exceeds_threshold"

    def test_malformed_m1_bar_repairs_from_tick_anchor(self, monkeypatch):
        pd = pytest.importorskip("pandas")
        from src.components import data_ingestion as di

        malformed_m1 = {
            "time": "2026-06-01T21:33:00+00:00",
            "open": 6764.75,
            "high": 6765.10,
            "low": 6764.73,
            "close": 6764.77,
            "volume": 100,
        }
        tick_rows = pd.DataFrame({"bid": [1995.20, 1995.45, 1994.90, 1995.05]})
        monkeypatch.setattr(di, "_tick_read_ticks_for_bar", lambda *args, **kwargs: tick_rows)
        monkeypatch.setattr(di, "_TICKS_ROOT", di._TICKS_ROOT or "data/ticks")

        repaired, report = repair_malformed_ohlc_from_ticks(
            [malformed_m1],
            "ETHUSD",
            "M1",
            {
                "gtos_vnext_runtime": {
                    "moonshot_broader_origin_max_interbar_price_jump_ratio": 0.35
                }
            },
            anchor_price=1995.22,
        )

        assert report["repaired_count"] == 1
        assert repaired[0]["high"] == 1995.45
        assert repaired[0]["low"] == 1994.90
        assert repaired[0]["close"] == 1995.05
        assert repaired[0]["ohlc_source_repair"]["reason"] == "m1_anchor_price_jump_exceeds_threshold"

    def test_ingest_repairs_closed_malformed_m15_before_source_quality_gate(self, monkeypatch):
        pd = pytest.importorskip("pandas")
        from src.components import data_ingestion as di
        from src.components.broader_origin_generators import evaluate_m15_ohlc_source_quality
        from src.components.data_ingestion import DEFAULT_LOOKBACKS, TF_MAP, TF_MINUTES

        class FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = datetime(2026, 6, 1, 21, 16, tzinfo=timezone.utc)
                return value if tz is None else value.astimezone(tz)

        def _tf_candles(total: int, minutes: int, last_open: datetime) -> list[dict]:
            first_open = last_open - timedelta(minutes=minutes * (total - 1))
            rows = []
            for idx in range(total):
                t = first_open + timedelta(minutes=minutes * idx)
                base = 71400.0 + idx * 0.25
                rows.append(
                    {
                        "time": t.isoformat(),
                        "open": base,
                        "high": base + 10.0,
                        "low": base - 10.0,
                        "close": base + 1.0,
                        "volume": 100,
                    }
                )
            return rows

        mt5 = MockMT5()
        mt5.connect()
        last_open_by_tf = {
            "D1": datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
            "H4": datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc),
            "H1": datetime(2026, 6, 1, 21, 0, tzinfo=timezone.utc),
            "M15": datetime(2026, 6, 1, 21, 15, tzinfo=timezone.utc),
        }
        for tf_name, tf_const in TF_MAP.items():
            candles = _tf_candles(
                DEFAULT_LOOKBACKS[tf_name] + 1,
                TF_MINUTES[tf_name],
                last_open_by_tf[tf_name],
            )
            if tf_name == "M15":
                candles[-2].update(
                    {"open": 71441.16, "high": 71442.24, "low": 592.06, "close": 592.86}
                )
            mt5.set_candles(tf_const, candles)

        tick_rows = pd.DataFrame({"bid": [71441.16, 71340.0, 71172.5, 71210.25]})
        monkeypatch.setattr(di, "_tick_read_ticks_for_bar", lambda *args, **kwargs: tick_rows)
        monkeypatch.setattr(di, "_TICKS_ROOT", di._TICKS_ROOT or "data/ticks")

        config = {
            "market": {"symbol": "BTCUSD"},
            "data": {"lookback": DEFAULT_LOOKBACKS},
            "model_a": {"equal_level_tolerance": 2.50},
            "gtos_vnext_runtime": {
                "moonshot_broader_origin_max_interbar_price_jump_ratio": 0.35
            },
        }
        with patch.object(di, "datetime", FixedDatetime):
            result = ingest_live_data(mt5, config)

        latest = result["candles"]["M15"][-1]
        assert latest["time"] == "2026-06-01T21:00:00+00:00"
        assert latest["close"] == 71210.25
        assert latest["ohlc_source_repair"]["status"] == "repaired_from_local_tick_parquet"
        repair = result["data_quality"]["closed_bar_filter"]["M15"]["ohlc_repair"]
        assert repair["repaired_count"] == 1
        quality = evaluate_m15_ohlc_source_quality(result, config=config)
        assert quality["status"] == "OK"


class TestIngestLiveDataSymbol:
    """Regression guard for the empty-``symbol`` bug (session 38)."""

    def _setup_mt5(self):
        from src.components.data_ingestion import TF_MAP, DEFAULT_LOOKBACKS
        mt5 = MockMT5()
        mt5.connect()
        for tf_name, tf_const in TF_MAP.items():
            count = DEFAULT_LOOKBACKS[tf_name]
            mt5.set_candles(tf_const, _make_candles(count))
        return mt5

    def _base_config(self, market: dict) -> dict:
        return {
            "market": market,
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }

    def test_symbol_matches_market_symbol(self):
        """raw_data['symbol'] mirrors config['market']['symbol']."""
        mt5 = self._setup_mt5()
        config = self._base_config({"symbol": "XAUUSD"})
        result = ingest_live_data(mt5, config)
        assert "symbol" in result, (
            "raw_data must carry a 'symbol' key — downstream shadow logger + "
            "XAUUSD session-ATR gate depend on it"
        )
        assert result["symbol"] == "XAUUSD"

    def test_symbol_canonical_not_broker(self):
        """When canonical != broker, raw_data['symbol'] stores the CANONICAL.

        market_state.compute_market_state compares ``symbol == 'XAUUSD'`` —
        a canonical check. Shadow logger classification wants a normalized
        instrument label. The broker alias (US30.cash) is only used for
        MT5 API calls.
        """
        mt5 = self._setup_mt5()
        config = self._base_config({"symbol": "US30_cash", "mt5_symbol": "US30.cash"})
        result = ingest_live_data(mt5, config)
        assert result["symbol"] == "US30_cash"

    def test_symbol_defaults_when_market_missing(self):
        """Matches the pre-fix mt5_symbol fallback: ``"XAUUSD"`` default.

        If market section is missing entirely, the legacy mt5_symbol
        fallback is ``"XAUUSD"``. The canonical symbol resolution MUST
        mirror that same fallback to avoid introducing new failure
        modes on misconfigured callers (tests, CLI one-shots).
        """
        mt5 = self._setup_mt5()
        # No "market" key at all.
        config = {
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)
        # Default fallback: same string the pre-fix mt5_symbol lookup used.
        assert result["symbol"] == "XAUUSD"

    def test_symbol_present_for_every_instrument(self):
        """Full fleet — no silent empty-string regression."""
        mt5 = self._setup_mt5()
        for sym in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
            config = self._base_config({"symbol": sym})
            result = ingest_live_data(mt5, config)
            assert result["symbol"] == sym, f"{sym} did not survive ingest"

    def test_symbol_not_empty_string(self):
        """The exact production-bug regression: NEVER emit ``symbol=""``."""
        mt5 = self._setup_mt5()
        config = self._base_config({"symbol": "XAUUSD"})
        result = ingest_live_data(mt5, config)
        assert result["symbol"] != "", (
            "ingest_live_data produced empty symbol — this is the session-38 "
            "production bug that zeroed every shadow_logs row + silently "
            "disabled the XAUUSD session-ATR path"
        )


class TestTickFeaturesMerge:
    """Verify the additive ``tick_features`` block. The merge must:

    1. Always produce a ``tick_features`` key on raw_data (None or dict).
    2. Default to None when no parquet data + no daemon running.
    3. Honor the ``tick_features.enabled = false`` config opt-out.
    4. Never raise — fail-open is the contract.
    """

    def _setup_mt5(self):
        from src.components.data_ingestion import TF_MAP, DEFAULT_LOOKBACKS
        mt5 = MockMT5()
        mt5.connect()
        for tf_name, tf_const in TF_MAP.items():
            count = DEFAULT_LOOKBACKS[tf_name]
            mt5.set_candles(tf_const, _make_candles(count))
        return mt5

    def test_tick_features_key_always_present(self):
        mt5 = self._setup_mt5()
        config = {
            "market": {"symbol": "XAUUSD"},
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)
        assert "tick_features" in result

    def test_tick_features_none_when_no_data(self):
        """Fail-open path: missing tick parquet → tick_features = None."""
        mt5 = self._setup_mt5()
        config = {
            "market": {"symbol": "GBPJPY"},  # no parquet exists for this symbol
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        result = ingest_live_data(mt5, config)
        assert result["tick_features"] is None

    def test_tick_features_disabled_via_config(self):
        mt5 = self._setup_mt5()
        config = {
            "market": {"symbol": "XAUUSD"},
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
            "tick_features": {"enabled": False},
        }
        result = ingest_live_data(mt5, config)
        assert result["tick_features"] is None

    def test_tick_features_does_not_break_pipeline(self):
        """Catastrophic test: even if the extractor explodes, ingest_live_data
        must not raise — the tick layer is observational and downstream-additive.
        """
        mt5 = self._setup_mt5()
        config = {
            "market": {"symbol": "XAUUSD"},
            "data": {"lookback": {"D1": 30, "H4": 80, "H1": 168, "M15": 672}},
            "model_a": {"equal_level_tolerance": 2.50},
        }
        # Force-mutate the helper so it raises; the wrapper should swallow it.
        from unittest.mock import patch

        def _boom(*args, **kwargs):
            raise RuntimeError("simulated tick-extractor failure")

        with patch("src.components.data_ingestion._tick_compute_for_bar",
                    side_effect=_boom):
            result = ingest_live_data(mt5, config)
        assert result["tick_features"] is None
        # And every other field still populated.
        assert "candles" in result
        assert "session_levels" in result
