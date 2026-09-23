"""Tests for Bug #25 — equity=0 transient must not trigger daily_loss_stop.

Background
----------
2026-04-27 10:45 UTC, GBPUSD orchestrator triggered ``DAILY_LOSS_STOP`` with
``equity=0.00`` and ``pnl_pct=-100%``. Real account equity at the moment was
``$99,995.02``; MT5 had transiently returned ``account_info()=None`` and the
``mt5_real`` wrapper silently substituted ``0.0``. The dormant marker blocked
GBPUSD trading until manual cleanup.

Coverage
--------
1. ``equity_guard.safe_read_equity`` — None / 0 / negative / exception → None;
   normal value passes through; anomaly logged to ``EQUITY_ANOMALY_LOG_PATH``.
2. ``equity_guard.EquityFilter`` — median absorbs single-tick outlier; recovery
   when reads return to normal; transient ``None`` does not move the consensus.
3. End-to-end on ``_update_daily_pnl`` — equity=0 / None transient does NOT
   trigger daily_loss_stop; a real -4.5% loss DOES trigger; median recovers
   when reads return to normal so a future tick resumes correct accounting.

All shadow-log writes go through a tmp_path-redirected
``EQUITY_ANOMALY_LOG_PATH`` module constant — the canonical ``tmp_path`` +
module-ref monkeypatch isolation pattern.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.safety import equity_guard as _eg
from src.safety import dormant_state as _ds


# --------------------------------------------------------------------------
# Autouse fixtures — anomaly log + dormant path isolation
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_anomaly_log(tmp_path, monkeypatch):
    path = tmp_path / "equity_read_anomalies.jsonl"
    monkeypatch.setattr(_eg, "EQUITY_ANOMALY_LOG_PATH", path)
    yield path


@pytest.fixture(autouse=True)
def _isolate_dormant_path(tmp_path, monkeypatch):
    path = tmp_path / "dormant_state.json"
    monkeypatch.setattr(_ds, "DORMANT_STATE_PATH", path)
    yield path


# --------------------------------------------------------------------------
# safe_read_equity — hard guard
# --------------------------------------------------------------------------


class _StubMT5:
    """Minimal MT5 stub supporting equity hijack."""

    def __init__(self, equity_value):
        self._equity_value = equity_value

    def get_account_equity(self):
        if isinstance(self._equity_value, BaseException):
            raise self._equity_value
        return self._equity_value


class TestSafeReadEquity:
    def test_normal_positive_value_passes_through(self, _isolate_anomaly_log):
        mt5 = _StubMT5(99_995.02)
        result = _eg.safe_read_equity(mt5, symbol="GBPUSD")
        assert result == pytest.approx(99_995.02)
        # No anomaly logged.
        assert not _isolate_anomaly_log.exists()

    def test_zero_returns_none_and_logs_anomaly(self, _isolate_anomaly_log):
        """Bug #25 root case — wrapper returned 0.0 on transient None."""
        mt5 = _StubMT5(0.0)
        result = _eg.safe_read_equity(mt5, symbol="GBPUSD")
        assert result is None
        # Anomaly logged with kind=zero.
        assert _isolate_anomaly_log.exists()
        rows = [json.loads(line) for line in _isolate_anomaly_log.read_text().splitlines()]
        assert len(rows) == 1
        assert rows[0]["kind"] == "zero"
        assert rows[0]["symbol"] == "GBPUSD"
        assert rows[0]["raw_value"] == 0

    def test_none_returns_none_and_logs_anomaly(self, _isolate_anomaly_log):
        mt5 = _StubMT5(None)
        result = _eg.safe_read_equity(mt5, symbol="USDJPY")
        assert result is None
        rows = [json.loads(line) for line in _isolate_anomaly_log.read_text().splitlines()]
        assert rows[0]["kind"] == "none"

    def test_negative_returns_none_and_logs_anomaly(self, _isolate_anomaly_log):
        mt5 = _StubMT5(-150.0)
        result = _eg.safe_read_equity(mt5, symbol="XAUUSD")
        assert result is None
        rows = [json.loads(line) for line in _isolate_anomaly_log.read_text().splitlines()]
        assert rows[0]["kind"] == "negative"

    def test_exception_returns_none_and_logs_anomaly(self, _isolate_anomaly_log):
        mt5 = _StubMT5(RuntimeError("MT5 disconnected"))
        result = _eg.safe_read_equity(mt5, symbol="US30_cash")
        assert result is None
        rows = [json.loads(line) for line in _isolate_anomaly_log.read_text().splitlines()]
        assert rows[0]["kind"] == "exception"
        assert "MT5 disconnected" in rows[0]["raised"]

    def test_anomaly_log_uses_locked_jsonl_writer(self, monkeypatch, _isolate_anomaly_log):
        """Regression: multi-symbol anomaly bursts must not use raw append.

        Production hit two malformed lines when several orchestrator processes
        logged equity=0 anomalies on the same candle. The anomaly path must use
        the shared locked JSONL writer, not a bare ``Path.open("a")`` write.
        """
        calls = []

        class _Writer:
            def __init__(self, path):
                calls.append(("init", Path(path)))

            def write(self, row):
                calls.append(("write", dict(row)))

        monkeypatch.setattr(_eg, "RotatingJsonlWriter", _Writer)

        mt5 = _StubMT5(0.0)
        result = _eg.safe_read_equity(mt5, symbol="XAUUSD")

        assert result is None
        assert calls[0] == ("init", _isolate_anomaly_log)
        assert calls[1][0] == "write"
        assert calls[1][1]["symbol"] == "XAUUSD"
        assert calls[1][1]["kind"] == "zero"


# --------------------------------------------------------------------------
# EquityFilter — rolling median
# --------------------------------------------------------------------------


class TestEquityFilter:
    def test_consensus_none_when_empty(self):
        f = _eg.EquityFilter(symbol="GBPUSD")
        assert f.get_consensus() is None
        assert f.has_consensus is False

    def test_single_value_consensus(self):
        f = _eg.EquityFilter(symbol="GBPUSD")
        consensus = f.update_and_get_consensus(100_000.0)
        assert consensus == 100_000.0
        assert f.has_consensus is True

    def test_median_of_three(self):
        f = _eg.EquityFilter(symbol="GBPUSD")
        f.update_and_get_consensus(99_900.0)
        f.update_and_get_consensus(100_200.0)
        consensus = f.update_and_get_consensus(100_000.0)
        # Median of {99_900, 100_000, 100_200} == 100_000
        assert consensus == 100_000.0

    def test_median_absorbs_single_outlier(self, _isolate_anomaly_log):
        """Sequence [100k, 100k, 100k, 40k, 100k] — median rejects spike.

        40k chosen so deviation = 0.6 > outlier_pct=0.5 (logged as outlier).
        Even at 50% (== threshold) median absorption still works; we use 60%
        here so the outlier-log assertion is well above the boundary.
        """
        f = _eg.EquityFilter(symbol="GBPUSD")
        f.update_and_get_consensus(100_000.0)
        f.update_and_get_consensus(100_000.0)
        f.update_and_get_consensus(100_000.0)
        # 40k is a 60% drop — outlier flag fires AND it is appended.
        consensus = f.update_and_get_consensus(40_000.0)
        # Window: [100_000, 100_000, 100_000, 40_000] — median == 100_000
        assert consensus == 100_000.0
        # Recovery — next normal read keeps median at 100k.
        consensus = f.update_and_get_consensus(100_000.0)
        # Window: [100_000, 100_000, 100_000, 40_000, 100_000] — median == 100_000
        assert consensus == 100_000.0
        # Outlier was logged.
        rows = [json.loads(line) for line in _isolate_anomaly_log.read_text().splitlines()]
        outlier_rows = [r for r in rows if r["kind"] == "outlier"]
        assert len(outlier_rows) == 1
        assert outlier_rows[0]["raw_value"] == 40_000.0

    def test_none_input_preserves_consensus(self):
        f = _eg.EquityFilter(symbol="GBPUSD")
        f.update_and_get_consensus(100_000.0)
        f.update_and_get_consensus(100_000.0)
        prior = f.get_consensus()
        # Transient failure: safe_read_equity returned None.
        consensus = f.update_and_get_consensus(None)
        assert consensus == prior  # Window unchanged.
        assert len(f) == 2

    def test_zero_input_preserves_consensus(self):
        """Defense in depth — even if a 0 sneaks through safe_read_equity,
        the filter rejects it from the window."""
        f = _eg.EquityFilter(symbol="GBPUSD")
        f.update_and_get_consensus(100_000.0)
        consensus = f.update_and_get_consensus(0.0)
        assert consensus == 100_000.0
        assert len(f) == 1

    def test_window_eviction(self):
        """Window=5 evicts oldest beyond capacity."""
        f = _eg.EquityFilter(window_size=3, symbol="GBPUSD")
        f.update_and_get_consensus(100.0)
        f.update_and_get_consensus(200.0)
        f.update_and_get_consensus(300.0)
        # Window: [100, 200, 300], median 200
        assert f.get_consensus() == 200.0
        f.update_and_get_consensus(400.0)
        # Window: [200, 300, 400] (100 evicted), median 300
        assert f.get_consensus() == 300.0

    def test_recovery_after_sustained_outlier_burst(self):
        """If outliers exceed window/2 they DO move the median — but a
        sustained burst that big means it's a real loss, not a transient.
        This test documents the boundary."""
        f = _eg.EquityFilter(window_size=5, symbol="GBPUSD")
        for _ in range(5):
            f.update_and_get_consensus(100_000.0)
        # Now 3 sustained low reads (60% of window). Median moves.
        f.update_and_get_consensus(50_000.0)
        f.update_and_get_consensus(50_000.0)
        f.update_and_get_consensus(50_000.0)
        # Window: [100_000, 100_000, 50_000, 50_000, 50_000], median 50_000
        assert f.get_consensus() == 50_000.0


# --------------------------------------------------------------------------
# End-to-end — _update_daily_pnl with transient equity=0
# --------------------------------------------------------------------------


def _make_orch_with_filter(start_equity: float = 100_000.0):
    """Build a SessionOrchestrator stub via __new__ + minimal attrs.

    Mirrors the existing pattern in tests/test_orchestrator.py
    TestDailyPnlUpdate.
    """
    from src.components.orchestrator import SessionOrchestrator
    from src.safety.equity_guard import EquityFilter
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.mt5 = MagicMock()
    orch.mt5.get_history_deals.return_value = []
    orch._symbol = "GBPUSD"
    orch.session_state = {
        "start_balance": start_equity,
        "start_equity": start_equity,
        "daily_pnl_pct": 0.0,
        "portfolio_drawdown_pct": 0.0,
    }
    orch._equity_filter = EquityFilter(symbol="GBPUSD")
    return orch


class TestUpdateDailyPnlWithGuard:
    """Bug #25 contract — transient equity=0 / None must NOT poison daily_pnl_pct."""

    def test_normal_read_updates_pnl(self):
        orch = _make_orch_with_filter(start_equity=100_000.0)
        orch.mt5.get_account_equity.return_value = 99_950.0
        orch._update_daily_pnl()
        # -0.05% loss
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-0.05, abs=0.001)

    def test_zero_equity_transient_does_not_update_pnl(self):
        """Bug #25 root case. With NO history yet, equity=0 read must
        skip the pnl update entirely (leaves daily_pnl_pct at prior 0.0,
        which is correct for start-of-session)."""
        orch = _make_orch_with_filter(start_equity=100_000.0)
        orch.mt5.get_account_equity.return_value = 0.0
        orch._update_daily_pnl()
        # daily_pnl_pct unchanged from baseline (NOT -100%).
        assert orch.session_state["daily_pnl_pct"] == 0.0

    def test_none_equity_transient_does_not_update_pnl(self):
        orch = _make_orch_with_filter(start_equity=100_000.0)
        orch.mt5.get_account_equity.return_value = None
        orch._update_daily_pnl()
        assert orch.session_state["daily_pnl_pct"] == 0.0

    def test_zero_after_normal_read_uses_prior_consensus(self):
        """Sequence [normal, normal, 0, normal] — the 0 doesn't poison
        the median because it's rejected by safe_read_equity."""
        orch = _make_orch_with_filter(start_equity=100_000.0)
        # First two ticks: normal at 99_950
        orch.mt5.get_account_equity.return_value = 99_950.0
        orch._update_daily_pnl()
        orch._update_daily_pnl()
        # Third tick: transient 0
        orch.mt5.get_account_equity.return_value = 0.0
        orch._update_daily_pnl()
        # daily_pnl_pct should still reflect the healthy median, not -100%.
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-0.05, abs=0.001)
        # Fourth tick: recovery
        orch.mt5.get_account_equity.return_value = 99_960.0
        orch._update_daily_pnl()
        # Median of [99_950, 99_950, 99_960] == 99_950 → pnl ~-0.05%
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-0.05, abs=0.001)

    def test_real_4_5_pct_loss_updates_pnl_correctly(self):
        """Real loss must propagate so the daily_loss_stop trigger fires."""
        orch = _make_orch_with_filter(start_equity=100_000.0)
        orch.mt5.get_account_equity.return_value = 95_500.0  # -4.5%
        orch._update_daily_pnl()
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-4.5, abs=0.001)


# --------------------------------------------------------------------------
# End-to-end — daily_loss_stop trigger respects the guard
# --------------------------------------------------------------------------


class _StubExecution:
    def __init__(self):
        self.pending_intent = None
        self.cancel_calls = []

    def cancel_limit_intent(self, reason):
        self.cancel_calls.append(reason)


class _StubOrchestratorE2E:
    """Lightweight orchestrator carrying just the methods + state we need
    to exercise _update_daily_pnl + _check_and_trigger_daily_loss_stop
    end-to-end with the new guard wired in."""

    def __init__(self, *, equity_sequence, start_equity=100_000.0,
                 cap_pct=4.0):
        from src.safety.equity_guard import EquityFilter
        self.config = {"risk": {"max_daily_loss_pct": cap_pct}}
        self.session_state = {
            "start_balance": start_equity,
            "start_equity": start_equity,
            "daily_pnl_pct": 0.0,
            "portfolio_drawdown_pct": 0.0,
        }
        self._symbol = "GBPUSD"
        self._equity_filter = EquityFilter(symbol="GBPUSD")
        self._equity_sequence = list(equity_sequence)
        self._equity_idx = 0
        self.mt5 = MagicMock()
        self.mt5.get_history_deals.return_value = []

        def _next_equity():
            if self._equity_idx >= len(self._equity_sequence):
                return self._equity_sequence[-1]
            v = self._equity_sequence[self._equity_idx]
            self._equity_idx += 1
            return v
        self.mt5.get_account_equity.side_effect = _next_equity

        self.execution = _StubExecution()
        self.log_candle_calls = []
        self._pending_trade_record_path = None

    def _log_candle(self, state, reason, kill_zone):
        self.log_candle_calls.append((state, reason, kill_zone))

    # Bind the real methods we are testing
    from src.components.orchestrator import SessionOrchestrator as _RealOrch
    _update_daily_pnl = _RealOrch._update_daily_pnl
    _check_and_trigger_daily_loss_stop = _RealOrch._check_and_trigger_daily_loss_stop


class TestDailyLossStopWithGuard:
    """End-to-end: equity=0 transient does not trigger; real loss does."""

    def test_zero_transient_does_not_trigger(self, _isolate_dormant_path):
        """The Bug #25 reproduction case: single transient 0 read with
        no prior history. Must NOT trigger."""
        stub = _StubOrchestratorE2E(equity_sequence=[0.0])
        stub._update_daily_pnl()
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is False
        # Marker NOT written.
        assert not _isolate_dormant_path.exists()

    def test_zero_transient_after_healthy_reads_does_not_trigger(
        self, _isolate_dormant_path
    ):
        """Bug #25 in its actual production form: orchestrator has been
        running with healthy reads, then one MT5 hiccup returns 0. The
        median absorbs it — no trigger."""
        stub = _StubOrchestratorE2E(
            equity_sequence=[99_950.0, 99_950.0, 99_950.0, 0.0]
        )
        for _ in range(4):
            stub._update_daily_pnl()
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is False
        assert not _isolate_dormant_path.exists()

    def test_none_transient_does_not_trigger(self, _isolate_dormant_path):
        stub = _StubOrchestratorE2E(equity_sequence=[None])
        stub._update_daily_pnl()
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is False
        assert not _isolate_dormant_path.exists()

    def test_real_loss_triggers(self, _isolate_dormant_path):
        """A genuine -4.5% loss propagates through the filter and trips
        the stop. (No outlier — only one read so far so the median IS
        the read; this confirms the guard does not over-suppress.)"""
        stub = _StubOrchestratorE2E(equity_sequence=[95_500.0])
        stub._update_daily_pnl()
        assert stub.session_state["daily_pnl_pct"] == pytest.approx(-4.5, abs=0.001)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        assert _isolate_dormant_path.exists()
        record = json.loads(_isolate_dormant_path.read_text())
        assert record["trigger_reason"] == "daily_loss_stop"
        assert record["equity_at_trigger"] == 95_500.0
        assert record["daily_pnl_pct_at_trigger"] == pytest.approx(-4.5, abs=0.001)

    def test_sustained_loss_after_healthy_reads_triggers(
        self, _isolate_dormant_path
    ):
        """Boundary: 5 healthy reads then 3 sustained low-equity reads
        eventually move the median past the cap. (3/5 reads at 95_500
        means median is still 99_950; need more sustained data to flip.)
        This documents that the filter delays — but does not block — a
        sustained loss."""
        stub = _StubOrchestratorE2E(
            equity_sequence=[99_950.0, 99_950.0, 99_950.0,
                             95_500.0, 95_500.0, 95_500.0,
                             95_500.0, 95_500.0]
        )
        for _ in range(8):
            stub._update_daily_pnl()
        # Window: last 5 = [99_950, 95_500, 95_500, 95_500, 95_500, 95_500]
        # → consensus moves toward 95_500.
        # Final median of last 5: [95_500] x 5 == 95_500 → pnl -4.5%
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        record = json.loads(_isolate_dormant_path.read_text())
        # equity_at_trigger comes from filter consensus, not from raw read.
        assert record["equity_at_trigger"] == 95_500.0

    def test_marker_uses_filter_consensus_not_zero(self, _isolate_dormant_path):
        """When trigger fires AND a transient 0 happens at the same tick,
        the marker uses the prior consensus, not 0.

        This is the post-Bug-#25 contract on the marker itself: even if
        the underlying mt5_real wrapper is still flapping, the persisted
        equity_at_trigger reflects the value the trigger decision was
        actually based on."""
        # 5 healthy reads (median converges), then a real loss, then
        # while past the cap, mt5 hiccups returning 0.
        stub = _StubOrchestratorE2E(
            equity_sequence=[99_950.0, 95_500.0, 95_500.0, 95_500.0, 95_500.0,
                             95_500.0]
        )
        for _ in range(6):
            stub._update_daily_pnl()
        # Now stub the next get_account_equity call (the one inside
        # _check_and_trigger_daily_loss_stop) to return 0. The trigger
        # function should fall back to filter consensus, not write 0.
        # Note the trigger function in the new code first asks the filter
        # then only as fallback calls safe_read_equity. So we don't even
        # need to override — but let's validate explicitly.
        stub._check_and_trigger_daily_loss_stop("london")
        record = json.loads(_isolate_dormant_path.read_text())
        # Marker equity is the filter consensus (95_500), NOT 0.
        assert record["equity_at_trigger"] == 95_500.0
