"""Tests for the Time-in-Trade Shadow Logger (T5.4, observation-only).

Validates:
- All 4 checkpoints populated for a LONG trade that stays open past 240min.
- A SHORT trade closed at 45min records only the 30min checkpoint, with the
  60/120/240 checkpoints null and marked `closed_before: true`.
- A bar-fetch failure skips the row (returns None) and does not raise.
- Orchestrator _finalize_exit wiring: the hook fires and writes a JSONL row.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.components.time_in_trade_shadow_logger import (
    CHECKPOINTS_MINUTES,
    compute_time_in_trade_hypotheticals,
    write_time_in_trade_shadow_log,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_m15_bars(entry_time: datetime,
                   *,
                   prices_by_minute: dict[int, float]) -> list[dict]:
    """Synthesize M15 bars. Each key is the minute offset from entry_time
    (bar OPEN time); close = prices_by_minute[minute]."""
    bars: list[dict] = []
    for minute, close_price in sorted(prices_by_minute.items()):
        bar_time = entry_time + timedelta(minutes=minute)
        bars.append({
            "time": bar_time.isoformat(),
            "open": close_price,
            "high": close_price,
            "low": close_price,
            "close": close_price,
            "volume": 100,
        })
    return bars


ENTRY_TIME = datetime(2026, 4, 15, 7, 30, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Test 1 — LONG trade, all 4 checkpoints hit
# ---------------------------------------------------------------------------

class TestLongAllCheckpointsHit:
    def test_long_all_four_checkpoints(self):
        # LONG entry=3000, SL=2990 (sl_distance=10). M15 bars across 240 min.
        # prices: +0.5R at 30min, +1.0R at 60min, +2.0R at 120min, +3.0R at 240min
        bars = _make_m15_bars(ENTRY_TIME, prices_by_minute={
            30: 3005.0,   # +0.5R
            60: 3010.0,   # +1.0R
            120: 3020.0,  # +2.0R
            240: 3030.0,  # +3.0R
        })

        result = compute_time_in_trade_hypotheticals(
            trade_id="t_long_001",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=300),  # closed after 240min
            entry_price=3000.0,
            sl_distance=10.0,
            actual_close_r=3.5,
            bar_fetcher=lambda a, b: bars,
        )

        assert result is not None
        assert result["trade_id"] == "t_long_001"
        assert result["direction"] == "LONG"
        assert result["actual_close_r"] == 3.5
        # All 4 checkpoints populated
        assert result["hypothetical_30min_r"] == 0.5
        assert result["hypothetical_60min_r"] == 1.0
        assert result["hypothetical_120min_r"] == 2.0
        assert result["hypothetical_240min_r"] == 3.0
        # None marked closed_before
        for mins in CHECKPOINTS_MINUTES:
            rec = result[f"hypothetical_{mins}min"]
            assert rec["closed_before"] is False
            assert rec["bar_close_price"] is not None

    def test_bar_close_price_audit_trail_present(self):
        bars = _make_m15_bars(ENTRY_TIME, prices_by_minute={
            30: 3005.0, 60: 3010.0, 120: 3020.0, 240: 3030.0,
        })
        result = compute_time_in_trade_hypotheticals(
            trade_id="t_audit_001",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=300),
            entry_price=3000.0,
            sl_distance=10.0,
            actual_close_r=3.5,
            bar_fetcher=lambda a, b: bars,
        )
        assert result["hypothetical_30min"]["bar_close_price"] == 3005.0
        assert result["hypothetical_240min"]["bar_close_price"] == 3030.0


# ---------------------------------------------------------------------------
# Test 2 — SHORT trade, closed at 45 minutes
# ---------------------------------------------------------------------------

class TestShortClosedEarly:
    def test_short_closed_at_45min(self):
        # SHORT entry=195.00, SL=195.50 (sl_distance=0.50). Close at 45min.
        # Only the 30min bar matters for the one checkpoint that's hit.
        # Price at 30min = 194.50 (+1.0R for SHORT)
        bars = _make_m15_bars(ENTRY_TIME, prices_by_minute={
            30: 194.50,  # +1.0R for SHORT
        })

        result = compute_time_in_trade_hypotheticals(
            trade_id="t_short_045",
            symbol="USDJPY",
            direction="SHORT",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=45),
            entry_price=195.00,
            sl_distance=0.50,
            actual_close_r=1.2,
            bar_fetcher=lambda a, b: bars,
        )

        assert result is not None

        # 30min checkpoint populated
        cp30 = result["hypothetical_30min"]
        assert cp30["closed_before"] is False
        assert cp30["bar_close_price"] == 194.50
        assert result["hypothetical_30min_r"] == 1.0

        # 60/120/240 checkpoints null and closed_before=true
        for mins in (60, 120, 240):
            cp = result[f"hypothetical_{mins}min"]
            assert cp["closed_before"] is True, f"{mins} min should be closed_before"
            assert cp["r"] is None
            assert cp["bar_close_price"] is None
            assert result[f"hypothetical_{mins}min_r"] is None


# ---------------------------------------------------------------------------
# Test 3 — Bar fetch failure is absorbed, no crash, no propagation
# ---------------------------------------------------------------------------

class TestBarFetchFailure:
    def test_bar_fetcher_returns_none_skips_row(self):
        # Bar fetcher returns None. Trade closed AFTER earliest checkpoint,
        # so "no bars" should yield None-r checkpoints but not a skipped row.
        result = compute_time_in_trade_hypotheticals(
            trade_id="t_nobars_001",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=120),
            entry_price=3000.0,
            sl_distance=10.0,
            actual_close_r=-0.5,
            bar_fetcher=lambda a, b: None,
        )

        # Row is returned with null checkpoints (no exception)
        assert result is not None
        assert result["hypothetical_30min_r"] is None
        assert result["hypothetical_60min_r"] is None
        # 240min is closed_before (trade closed at 120)
        assert result["hypothetical_240min"]["closed_before"] is True

    def test_bar_fetcher_raises_is_absorbed(self):
        # A raising fetcher should be caught inside the logger; no exception
        # propagates to the caller.
        def raising_fetcher(a, b):
            raise RuntimeError("MT5 disconnected")

        # compute_time_in_trade_hypotheticals catches everything and returns None.
        result = compute_time_in_trade_hypotheticals(
            trade_id="t_raise_001",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=120),
            entry_price=3000.0,
            sl_distance=10.0,
            actual_close_r=-0.5,
            bar_fetcher=raising_fetcher,
        )
        assert result is None

    def test_invalid_sl_distance_returns_none(self):
        result = compute_time_in_trade_hypotheticals(
            trade_id="t_badsl",
            symbol="XAUUSD",
            direction="LONG",
            entry_time=ENTRY_TIME,
            close_time=ENTRY_TIME + timedelta(minutes=120),
            entry_price=3000.0,
            sl_distance=0.0,
            actual_close_r=0.0,
            bar_fetcher=lambda a, b: [],
        )
        assert result is None

    def test_write_survives_bad_path(self, tmp_path, caplog):
        # write_* should never raise even on bad path scenarios.
        # We pass an entry and then try to write to a path whose parent
        # creation would succeed — just ensure no exception.
        log_path = str(tmp_path / "nested" / "dir" / "time_in_trade.jsonl")
        write_time_in_trade_shadow_log({"trade_id": "t_write_ok"}, log_path=log_path)
        assert Path(log_path).exists()


# ---------------------------------------------------------------------------
# Log output format
# ---------------------------------------------------------------------------

class TestShadowLogOutput:
    def test_writes_valid_jsonl(self, tmp_path):
        log_path = str(tmp_path / "time_in_trade.jsonl")
        entry = {
            "trade_id": "t_fmt_001",
            "symbol": "XAUUSD",
            "direction": "LONG",
            "actual_close_r": 1.5,
            "hypothetical_30min_r": 0.5,
            "hypothetical_60min_r": 1.0,
            "hypothetical_120min_r": 1.8,
            "hypothetical_240min_r": 2.1,
        }
        write_time_in_trade_shadow_log(entry, log_path=log_path)

        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["trade_id"] == "t_fmt_001"
        assert parsed["hypothetical_60min_r"] == 1.0

    def test_append_multiple_rows(self, tmp_path):
        log_path = str(tmp_path / "time_in_trade.jsonl")
        for i in range(3):
            write_time_in_trade_shadow_log({"trade_id": f"t_{i}"}, log_path=log_path)
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# Test 4 — Orchestrator wiring: the hook fires and writes a row
# ---------------------------------------------------------------------------

class TestOrchestratorWiring:
    """Verify _finalize_exit invokes the time-in-trade logger end-to-end."""

    def test_finalize_exit_writes_time_in_trade_row(self, tmp_path, monkeypatch):
        from src.components.orchestrator import SessionOrchestrator
        from src.components import orchestrator as orch_mod
        from src.components.sprt_monitor import SPRTMonitor, SPRTResult, CUSUMResult

        # Redirect shadow log output to tmp_path by monkeypatching the writer
        # on the orchestrator module (canonical module-ref pattern).
        shadow_log = tmp_path / "time_in_trade.jsonl"
        original_writer = orch_mod.write_time_in_trade_shadow_log
        monkeypatch.setattr(
            orch_mod,
            "write_time_in_trade_shadow_log",
            lambda entry: original_writer(entry, log_path=str(shadow_log)),
        )

        # Build a minimal orchestrator without triggering __init__.
        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._mt5_symbol = "XAUUSD"
        entry_t = datetime(2026, 4, 15, 7, 30, tzinfo=timezone.utc)
        orch._trade_entry_time = entry_t
        orch._trade_entry_price = 3000.0
        orch._trade_direction = "LONG"
        orch._trade_sl_distance = 10.0
        orch._last_tick_price = 3015.0  # +1.5R
        orch._mfe_price = 3020.0
        orch._mae_price = 2998.0
        orch._be_shadow_tracker = None
        orch._partial_close_shadow_tracker = None
        orch._active_trade_record = {
            "trade_id": "wire_001",
            "decision_pipeline": {},
        }
        orch.config = {"trade_capture": {"base_path": str(tmp_path)}}

        # Stub MT5 that returns M15 bars covering 30/60/120/240 min.
        bars = _make_m15_bars(entry_t, prices_by_minute={
            30: 3005.0, 60: 3010.0, 120: 3014.0, 240: 3015.0,
        })
        mt5 = MagicMock()
        mt5.get_candles_range.return_value = bars
        orch.mt5 = mt5

        # SPRT stub so _finalize_exit does not hit real state.
        mock_sprt = MagicMock(spec=SPRTMonitor)
        mock_sprt.update_all.return_value = (
            SPRTResult("XAUUSD", "CONTINUE", 0.6, 2.77, -1.56, 1, 1, 0),
            CUSUMResult("XAUUSD", False, False, 0.1, 0.0),
        )
        orch._sprt_monitor = mock_sprt

        trade_snapshot = SimpleNamespace(
            partial_close_events=[],
            initial_volume=0.1,
        )

        with patch("src.components.orchestrator.update_exit"), \
             patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.notify_trade_closed"):
            orch._finalize_exit(trade_snapshot, "tp1_hit")

        # A row should have been written.
        assert shadow_log.exists(), "time_in_trade.jsonl was not created by the hook"
        with open(shadow_log) as f:
            lines = f.readlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["trade_id"] == "wire_001"
        assert parsed["symbol"] == "XAUUSD"
        assert parsed["direction"] == "LONG"
        assert parsed["hypothetical_30min_r"] == 0.5
        assert parsed["hypothetical_60min_r"] == 1.0
        # Audit-trail bar prices present
        assert parsed["hypothetical_30min"]["bar_close_price"] == 3005.0

    def test_finalize_exit_absorbs_fetch_failure(self, tmp_path, monkeypatch):
        """Bar fetch raising must not crash _finalize_exit."""
        from src.components.orchestrator import SessionOrchestrator
        from src.components import orchestrator as orch_mod
        from src.components.sprt_monitor import SPRTMonitor, SPRTResult, CUSUMResult

        shadow_log = tmp_path / "time_in_trade.jsonl"
        original_writer = orch_mod.write_time_in_trade_shadow_log
        monkeypatch.setattr(
            orch_mod,
            "write_time_in_trade_shadow_log",
            lambda entry: original_writer(entry, log_path=str(shadow_log)),
        )

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAUUSD"
        orch._mt5_symbol = "XAUUSD"
        orch._trade_entry_time = datetime(2026, 4, 15, 7, 30, tzinfo=timezone.utc)
        orch._trade_entry_price = 3000.0
        orch._trade_direction = "LONG"
        orch._trade_sl_distance = 10.0
        orch._last_tick_price = 2990.0
        orch._mfe_price = 3005.0
        orch._mae_price = 2988.0
        orch._be_shadow_tracker = None
        orch._partial_close_shadow_tracker = None
        orch._active_trade_record = {"trade_id": "wire_raise", "decision_pipeline": {}}
        orch.config = {"trade_capture": {"base_path": str(tmp_path)}}

        mt5 = MagicMock()
        mt5.get_candles_range.side_effect = RuntimeError("mt5 down")
        orch.mt5 = mt5

        mock_sprt = MagicMock(spec=SPRTMonitor)
        mock_sprt.update_all.return_value = (
            SPRTResult("XAUUSD", "CONTINUE", 0.4, 2.77, -1.56, 0, 0, 1),
            CUSUMResult("XAUUSD", False, False, 0.05, 0.0),
        )
        orch._sprt_monitor = mock_sprt

        trade_snapshot = SimpleNamespace(partial_close_events=[], initial_volume=0.1)

        with patch("src.components.orchestrator.update_exit"), \
             patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.notify_trade_closed"):
            # Must not raise
            orch._finalize_exit(trade_snapshot, "sl_hit")

    def test_finalize_exit_uses_immutable_execution_sl_distance_after_be_recovery(
        self, tmp_path
    ):
        """Recovered BE-managed exits must not use BE stop distance as 1R."""
        from src.components.orchestrator import SessionOrchestrator
        from src.components.sprt_monitor import SPRTMonitor, SPRTResult, CUSUMResult

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch._symbol = "XAGUSD"
        orch._mt5_symbol = "XAGUSD"
        entry_t = datetime(2026, 6, 2, 13, 19, tzinfo=timezone.utc)
        orch._trade_entry_time = entry_t
        orch._trade_entry_price = 76.02000000000001
        orch._trade_direction = "SHORT"
        orch._trade_sl_distance = 1.4210854715202004e-14
        orch._last_tick_price = 75.857
        orch._mfe_price = 75.857
        orch._mae_price = 76.02000000000001
        orch._be_shadow_tracker = None
        orch._partial_close_shadow_tracker = None
        orch._trailing_stop_shadow_tracker = None
        orch.config = {"trade_capture": {"base_path": str(tmp_path)}}
        orch._active_trade_record = {
            "trade_id": "XAGUSD_2026-06-02_ny_1315_broadorigin_85463db3c029fc05591cb4ba",
            "metadata": {
                "trade_id": "XAGUSD_2026-06-02_ny_1315_broadorigin_85463db3c029fc05591cb4ba"
            },
            "execution": {
                "entry_price": 76.02000000000001,
                "stop_loss": 76.593,
                "sl_distance": 0.5570000000000022,
            },
            "decision_pipeline": {},
            "instrumentation": {
                "gtos_vnext_recovered_partial_close_events": [
                    {
                        "type": "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
                        "price": 75.343,
                        "volume_closed": 0.04,
                        "initial_volume": 0.08,
                        "mt5_order_id": 242603665,
                        "r_at_close": 47639639808279.0,
                    }
                ]
            },
        }

        mt5 = MagicMock()
        mt5.get_candles_range.return_value = []
        orch.mt5 = mt5
        mock_sprt = MagicMock(spec=SPRTMonitor)
        mock_sprt.update_all.return_value = (
            SPRTResult("XAGUSD", "CONTINUE", 0.6, 2.77, -1.56, 1, 1, 0),
            CUSUMResult("XAGUSD", False, False, 0.1, 0.0),
        )
        orch._sprt_monitor = mock_sprt

        trade_snapshot = SimpleNamespace(
            ticket=242557352,
            entry_price=76.02000000000001,
            stop_loss=76.02,
            direction="SHORT",
            initial_volume=0.08,
            partial_close_events=[
                {
                    "type": "TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER",
                    "price": 75.343,
                    "volume_closed": 0.04,
                    "initial_volume": 0.08,
                    "mt5_order_id": 242603665,
                    "r_at_close": 47639639808279.0,
                },
                {
                    "type": "TP2_FINAL_TARGET_VNEXT_PARTIAL_BE_RUNNER",
                    "price": 75.857,
                    "volume_closed": 0.04,
                    "initial_volume": 0.08,
                    "mt5_order_id": 242615578,
                    "r_at_close": 11470105300960.0,
                },
            ],
        )

        captured: dict = {}

        def _capture_update_exit(_record, exit_data):
            captured.update(exit_data)

        with patch("src.components.orchestrator.update_exit", _capture_update_exit), \
             patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.notify_trade_closed"), \
             patch("src.components.orchestrator.update_proximity_outcome"):
            orch._finalize_exit(
                trade_snapshot,
                "tp2_final_target_vnext_partial_be_runner",
            )

        assert captured["r_denominator_source"] == "execution.entry_stop_distance"
        assert captured["r_sl_distance"] == pytest.approx(0.573)
        assert captured["actual_r"] == pytest.approx(0.7330, abs=0.0001)
        assert len(captured["partial_closes"]) == 2
        assert captured["partial_closes"][0]["r_at_close"] == pytest.approx(1.1815, abs=0.0001)
        assert captured["partial_closes"][1]["r_at_close"] == pytest.approx(0.2845, abs=0.0001)
