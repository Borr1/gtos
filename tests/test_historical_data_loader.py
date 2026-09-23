"""Tests for the historical backtest data loader — symbol-propagation fix.

See ``scripts/historical_data_loader.py::build_raw_data``. The live path
(``data_ingestion.ingest_live_data``) and the sim/backtest path
(``build_raw_data``) must produce a ``raw_data`` dict with the same schema
— in particular, both must carry a canonical ``"symbol"`` field so the
downstream MSO shadow logger and the ``market_state`` XAUUSD
session-ATR gate classify rows correctly.

Regression context: pre-fix, ``build_raw_data`` silently dropped the
symbol, which — together with the identical gap in ``ingest_live_data`` —
wrote ``symbol=""`` on every row of
``shadow_logs/structure_detector_divergences.jsonl`` and disabled the
XAUUSD-only session-ATR branch of ``compute_market_state`` across the
entire live fleet history.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from scripts.historical_data_loader import (
    build_raw_data,
    replay_kill_zone,
    replay_london_open,
    replay_ny_open,
)


def _make_candles(count: int, base: datetime) -> list[dict]:
    out = []
    for i in range(count):
        t = base + timedelta(minutes=15 * i)
        out.append({
            "time": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "open": 2650.0 + 0.1 * i,
            "high": 2655.0 + 0.1 * i,
            "low": 2645.0 + 0.1 * i,
            "close": 2652.0 + 0.1 * i,
            "volume": 100.0,
        })
    return out


def _all_candles_fixture() -> dict[str, list[dict]]:
    """Build enough candles across timeframes for build_raw_data slicing."""
    base_m15 = datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc)
    base_h1 = datetime(2026, 3, 24, 0, 0, tzinfo=timezone.utc)
    base_h4 = datetime(2026, 3, 17, 0, 0, tzinfo=timezone.utc)
    base_d1 = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)
    return {
        "M15": _make_candles(700, base_m15),
        "H1": _make_candles(180, base_h1),
        "H4": _make_candles(90, base_h4),
        "D1": _make_candles(40, base_d1),
    }


_SESSION_LEVELS = {
    "asian_high": 2660.0,
    "asian_low": 2640.0,
    "pdh": 2670.0,
    "pdl": 2635.0,
    "session_high": None,
    "session_low": None,
    "london_high": None,
    "london_low": None,
}


class TestBuildRawDataSymbol:
    """``build_raw_data`` must carry the CANONICAL symbol through to the
    returned dict so downstream consumers (market_state.compute_market_state
    + structure_detector_shadow_logger) classify correctly.
    """

    def test_symbol_populated_when_passed(self):
        all_candles = _all_candles_fixture()
        result = build_raw_data(
            all_candles,
            date(2026, 4, 1),
            "2026-04-01T07:15:00Z",
            _SESSION_LEVELS,
            symbol="XAUUSD",
        )
        assert "symbol" in result
        assert result["symbol"] == "XAUUSD"

    def test_symbol_canonical_not_broker(self):
        """US30_cash canonical, NOT US30.cash broker alias."""
        all_candles = _all_candles_fixture()
        result = build_raw_data(
            all_candles,
            date(2026, 4, 1),
            "2026-04-01T07:15:00Z",
            _SESSION_LEVELS,
            symbol="US30_cash",
        )
        assert result["symbol"] == "US30_cash"

    def test_symbol_every_instrument(self):
        all_candles = _all_candles_fixture()
        for sym in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
            result = build_raw_data(
                all_candles,
                date(2026, 4, 1),
                "2026-04-01T07:15:00Z",
                _SESSION_LEVELS,
                symbol=sym,
            )
            assert result["symbol"] == sym, f"{sym} did not survive build_raw_data"

    def test_symbol_defaults_to_empty_when_omitted(self):
        """Legacy callers that don't pass symbol still get a present key.

        Emitting ``""`` rather than omitting the key preserves a stable
        contract: downstream ``raw_data.get("symbol", "")`` behaves
        identically whether the caller threads symbol or not. Migration
        to explicit-symbol callers is incremental; this guarantees we
        don't KeyError on an un-migrated path.
        """
        all_candles = _all_candles_fixture()
        result = build_raw_data(
            all_candles,
            date(2026, 4, 1),
            "2026-04-01T07:15:00Z",
            _SESSION_LEVELS,
        )
        assert "symbol" in result
        assert result["symbol"] == ""

    def test_schema_matches_live_ingest(self):
        """Sanity: every key live ingest emits must also be in sim output.

        Reading ``src/components/data_ingestion.py::ingest_live_data``
        lines 92-113 reveals the live schema. This test freezes the two
        paths to a shared contract so a future gap won't silently recur.
        """
        all_candles = _all_candles_fixture()
        result = build_raw_data(
            all_candles,
            date(2026, 4, 1),
            "2026-04-01T07:15:00Z",
            _SESSION_LEVELS,
            symbol="XAUUSD",
        )
        expected_keys = {
            "symbol",
            "timestamp_utc",
            "candles",
            "session_levels",
            "equal_highs_H4",
            "equal_lows_H4",
            "equal_highs_H1",
            "equal_lows_H1",
            "spread_cents",
            "high_impact_events",
            "data_quality",
        }
        missing = expected_keys - set(result.keys())
        assert not missing, f"build_raw_data is missing expected keys: {missing}"


class TestReplayFunctionsPropagateSymbol:
    """``replay_london_open``, ``replay_ny_open``, ``replay_kill_zone`` must
    thread the symbol kwarg through to each yielded ``raw_data`` dict.
    """

    def test_replay_kill_zone_propagates_symbol(self):
        all_candles = _all_candles_fixture()
        # Use a target date that falls inside the M15 fixture range.
        out = list(replay_kill_zone(
            "2026-04-01", all_candles,
            kz_start="07:00", kz_end="09:30",
            symbol="XAUUSD",
        ))
        assert len(out) > 0
        for r in out:
            assert r["symbol"] == "XAUUSD"

    def test_replay_london_open_propagates_symbol(self):
        all_candles = _all_candles_fixture()
        out = list(replay_london_open(
            "2026-04-01", all_candles, symbol="USDJPY",
        ))
        assert len(out) > 0
        for r in out:
            assert r["symbol"] == "USDJPY"

    def test_replay_ny_open_propagates_symbol(self):
        all_candles = _all_candles_fixture()
        out = list(replay_ny_open(
            "2026-04-01", all_candles, symbol="GBPJPY",
        ))
        assert len(out) > 0
        for r in out:
            assert r["symbol"] == "GBPJPY"

    def test_replay_kill_zone_default_symbol_empty(self):
        """No symbol kwarg -> empty string (legacy behavior preserved)."""
        all_candles = _all_candles_fixture()
        out = list(replay_kill_zone(
            "2026-04-01", all_candles,
            kz_start="07:00", kz_end="09:30",
        ))
        assert len(out) > 0
        for r in out:
            assert r["symbol"] == ""
