"""Tests for T2.8 daily-loss stop + dormant-state marker.

Covers:
- ``src/safety/dormant_state.py`` — write/read/stale-clear lifecycle
- ``permissions.py`` Gate 3 — denies when today's marker is present
- ``orchestrator._check_and_trigger_daily_loss_stop`` — MTM threshold
  trigger, idempotency, pending-limit cancel, Telegram alert fire-and-forget

All dormant-state writes go through a tmp_path-redirected
``DORMANT_STATE_PATH`` module constant — the canonical ``tmp_path`` +
module-ref monkeypatch isolation pattern. No test ever touches the
production ``pipeline_state/dormant_state.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo
from src.mt5.mt5_mock import MockMT5
from src.safety import dormant_state as _ds


# --------------------------------------------------------------------------
# Autouse fixtures — dormant path isolation
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_dormant_path(tmp_path, monkeypatch):
    """Redirect the module's DORMANT_STATE_PATH to a per-test tmp file.

    This is the canonical ``tmp_path`` + module-ref monkeypatch pattern
    called out in ``tests/conftest.py`` Layer 1. Without it, any of the
    write_dormant_state calls below would litter production state.
    """
    path = tmp_path / "dormant_state.json"
    monkeypatch.setattr(_ds, "DORMANT_STATE_PATH", path)
    yield path


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _yesterday_str() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _write_raw_marker(path: Path, *, dormant_until_utc_day: str,
                      **extra) -> None:
    """Write a dormant marker directly (bypasses ``write_dormant_state``).

    Used when we want to simulate a stale marker from a previous day or a
    partial-write without the helper's side-effects.
    """
    record = {
        "dormant_until_utc_day": dormant_until_utc_day,
        "triggered_at_utc": "2026-04-21T14:07:12Z",
        "trigger_reason": "daily_loss_stop",
        "equity_at_trigger": 96120.31,
        "daily_pnl_pct_at_trigger": -4.05,
        "max_daily_loss_pct": 4.0,
        "symbol": "XAUUSD",
    }
    record.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(record, f)


# --------------------------------------------------------------------------
# dormant_state module — write / read / stale-clear
# --------------------------------------------------------------------------

class TestDormantStateModule:
    def test_write_and_read_round_trip(self, _isolate_dormant_path):
        record = _ds.write_dormant_state(
            trigger_reason="daily_loss_stop",
            equity_at_trigger=96120.31,
            daily_pnl_pct_at_trigger=-4.05,
            max_daily_loss_pct=4.0,
            symbol="XAUUSD",
        )
        assert _isolate_dormant_path.exists()
        loaded = _ds.load_dormant_state()
        assert loaded is not None
        assert loaded["dormant_until_utc_day"] == _today_str()
        assert loaded["trigger_reason"] == "daily_loss_stop"
        assert loaded["equity_at_trigger"] == 96120.31
        assert loaded["daily_pnl_pct_at_trigger"] == -4.05
        assert loaded["max_daily_loss_pct"] == 4.0
        assert loaded["symbol"] == "XAUUSD"
        # Round-trip matches the return value.
        assert loaded == record

    def test_is_dormant_today_true_when_written_today(self):
        _ds.write_dormant_state(
            trigger_reason="daily_loss_stop",
            equity_at_trigger=96000.0,
            daily_pnl_pct_at_trigger=-4.1,
            max_daily_loss_pct=4.0,
            symbol="XAUUSD",
        )
        assert _ds.is_dormant_today() is True

    def test_is_dormant_today_false_when_missing(self):
        assert _ds.is_dormant_today() is False

    def test_is_dormant_today_false_when_stale(self, _isolate_dormant_path):
        _write_raw_marker(_isolate_dormant_path,
                          dormant_until_utc_day=_yesterday_str())
        # Stale marker (yesterday's) must NOT be treated as dormant —
        # otherwise a mid-day restart would get stuck in last day's state.
        assert _ds.is_dormant_today() is False

    def test_clear_if_stale_removes_yesterday_marker(self, _isolate_dormant_path):
        _write_raw_marker(_isolate_dormant_path,
                          dormant_until_utc_day=_yesterday_str())
        assert _isolate_dormant_path.exists()
        cleared = _ds.clear_if_stale()
        assert cleared is True
        assert not _isolate_dormant_path.exists()

    def test_clear_if_stale_preserves_today_marker(self, _isolate_dormant_path):
        """Mid-day restart case: marker is for today → must NOT be cleared."""
        _ds.write_dormant_state(
            trigger_reason="daily_loss_stop",
            equity_at_trigger=96000.0,
            daily_pnl_pct_at_trigger=-4.1,
            max_daily_loss_pct=4.0,
            symbol="XAUUSD",
        )
        cleared = _ds.clear_if_stale()
        assert cleared is False
        assert _isolate_dormant_path.exists()

    def test_clear_if_stale_noop_when_no_marker(self):
        assert _ds.clear_if_stale() is False

    def test_load_returns_none_on_malformed_json(self, _isolate_dormant_path):
        _isolate_dormant_path.parent.mkdir(parents=True, exist_ok=True)
        _isolate_dormant_path.write_text("{not valid json")
        # Must not raise; treat as absent.
        assert _ds.load_dormant_state() is None
        assert _ds.is_dormant_today() is False

    def test_clear_dormant_state_unconditional(self, _isolate_dormant_path):
        _ds.write_dormant_state(
            trigger_reason="daily_loss_stop",
            equity_at_trigger=96000.0,
            daily_pnl_pct_at_trigger=-4.1,
            max_daily_loss_pct=4.0,
            symbol="XAUUSD",
        )
        _ds.clear_dormant_state()
        assert not _isolate_dormant_path.exists()


# --------------------------------------------------------------------------
# Gate 3 integration — permissions denies with active marker
# --------------------------------------------------------------------------

def _mock_pa(grade: str = "A+"):
    """Build a minimal PrimaryAnalysisOutput-like object.

    Mirrors ``tests/test_permissions.py::_mock_pa`` — Gate 1 reads
    ``reasoning.setup_grade`` + ``trade_parameters`` off attribute paths,
    not dict keys.
    """
    tp = SimpleNamespace(
        direction="LONG",
        entry_price=2650.0,
        stop_loss=2640.0,
        risk_reward_ratio=1.5,
        take_profit_1=2665.0,
    )
    reasoning = SimpleNamespace(
        setup_grade=grade,
        daily_bias=SimpleNamespace(direction="bullish"),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp)


def _mock_mso():
    return SimpleNamespace(m15_atr=3.0)


class TestPermissionsDormantGate:
    """Gate 3 must block with reason=daily_loss_stop_dormant when marker set."""

    def _base_state(self):
        return {
            "daily_pnl_pct": 0.0,       # MTM not breached directly
            "trades_today": 0,
            "current_kill_zone": "london",
            "trades_london": 0,
            "losses_today": 0,
        }

    def _isolate_concurrent_cache(self):
        """Concurrent-cap cache is module-level and leaks across tests if
        other tests also ran in the same process. Clear it here too."""
        from src.components import concurrent_tracker as _ct
        _ct.reset_cache()

    def test_denies_when_marker_is_today(self):
        from src.components.permissions import check_permissions
        self._isolate_concurrent_cache()

        _ds.write_dormant_state(
            trigger_reason="daily_loss_stop",
            equity_at_trigger=96000.0,
            daily_pnl_pct_at_trigger=-4.1,
            max_daily_loss_pct=4.0,
            symbol="XAUUSD",
        )

        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        denial = check_permissions(
            _mock_pa(), _mock_mso(), self._base_state(), mt5,
            symbol="XAUUSD",
        )
        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "daily_loss_stop_dormant"
        assert denial.details["dormant_until_utc_day"] == _today_str()
        assert denial.details["symbol"] == "XAUUSD"

    def test_passes_when_marker_is_stale(self, _isolate_dormant_path):
        from src.components.permissions import check_permissions
        self._isolate_concurrent_cache()

        _write_raw_marker(_isolate_dormant_path,
                          dormant_until_utc_day=_yesterday_str())

        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        denial = check_permissions(
            _mock_pa(), _mock_mso(), self._base_state(), mt5,
            symbol="XAUUSD",
        )
        # Stale marker should not gate.
        assert denial is None or denial.reason != "daily_loss_stop_dormant"

    def test_passes_when_no_marker(self):
        from src.components.permissions import check_permissions
        self._isolate_concurrent_cache()

        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)

        denial = check_permissions(
            _mock_pa(), _mock_mso(), self._base_state(), mt5,
            symbol="XAUUSD",
        )
        assert denial is None


# --------------------------------------------------------------------------
# Orchestrator trigger — MTM threshold + idempotency
# --------------------------------------------------------------------------

class _StubExecution:
    """Minimal execution stub tracking cancel_limit_intent calls."""

    def __init__(self, pending_intent=None):
        self.pending_intent = pending_intent
        self.cancel_calls: list[str] = []

    def cancel_limit_intent(self, reason: str) -> None:
        self.cancel_calls.append(reason)
        self.pending_intent = None


class _PendingIntentStub:
    """Stand-in for execution.pending_intent — presence is what matters."""

    trade_id = "XAUUSD_20260421_london_0700"


class _StubOrchestrator:
    """Lightweight orchestrator facsimile with just what the trigger needs.

    We deliberately avoid constructing a real ``Orchestrator`` to keep this
    test focused on ``_check_and_trigger_daily_loss_stop`` behavior. The
    method only reads:
      - ``self.config``
      - ``self.session_state``
      - ``self.mt5`` (equity query)
      - ``self.execution`` (pending cancel)
      - ``self._symbol``
      - ``self._log_candle`` (side-effect only)
    """

    def __init__(self, *, config, session_state, mt5, execution, symbol):
        self.config = config
        self.session_state = session_state
        self.mt5 = mt5
        self.execution = execution
        self._symbol = symbol
        self._pending_trade_record_path = "/tmp/ignored"
        self.log_candle_calls: list[tuple[str, str, str]] = []

    def _log_candle(self, state: str, reason: str, kill_zone: str) -> None:
        self.log_candle_calls.append((state, reason, kill_zone))

    # Bind the real method we are testing
    from src.components.orchestrator import SessionOrchestrator as _RealOrch  # type: ignore[assignment]
    _check_and_trigger_daily_loss_stop = (
        _RealOrch._check_and_trigger_daily_loss_stop  # type: ignore[attr-defined]
    )


class TestOrchestratorTrigger:
    def _make_stub(self, *, pnl_pct: float, cap_pct: float = 4.0,
                   equity: float = 95900.0, pending: bool = True) -> _StubOrchestrator:
        mt5 = MockMT5()
        mt5.connect()
        # Force deposit to the equity value we want to see. MockMT5's
        # get_account_equity reads from its internal balance + unrealized.
        # Simplest path: patch the method.
        mt5.get_account_equity = lambda: equity  # type: ignore[assignment]

        execution = _StubExecution(pending_intent=_PendingIntentStub() if pending else None)
        config = {"risk": {"max_daily_loss_pct": cap_pct}}
        session_state = {"daily_pnl_pct": pnl_pct}
        return _StubOrchestrator(
            config=config, session_state=session_state,
            mt5=mt5, execution=execution, symbol="XAUUSD",
        )

    def test_no_trigger_when_pnl_above_cap(self, _isolate_dormant_path):
        stub = self._make_stub(pnl_pct=-2.0, cap_pct=4.0)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is False
        assert not _isolate_dormant_path.exists()

    def test_trigger_at_exact_threshold(self, _isolate_dormant_path):
        """``<= -cap_pct`` — exact threshold fires."""
        stub = self._make_stub(pnl_pct=-4.0, cap_pct=4.0)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        assert _isolate_dormant_path.exists()

    def test_trigger_past_threshold_writes_marker(self, _isolate_dormant_path):
        stub = self._make_stub(pnl_pct=-4.1, cap_pct=4.0, equity=95900.0)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        loaded = _ds.load_dormant_state()
        assert loaded is not None
        assert loaded["trigger_reason"] == "daily_loss_stop"
        assert loaded["symbol"] == "XAUUSD"
        assert loaded["max_daily_loss_pct"] == 4.0
        assert loaded["equity_at_trigger"] == 95900.0
        assert loaded["daily_pnl_pct_at_trigger"] == -4.1
        assert loaded["dormant_until_utc_day"] == _today_str()

    def test_trigger_cancels_pending_limit(self):
        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0, pending=True)
        stub._check_and_trigger_daily_loss_stop("london")
        assert "daily_loss_stop" in stub.execution.cancel_calls

    def test_trigger_clears_all_persisted_pending_intent_files(
        self, tmp_path, monkeypatch,
    ):
        from src.components import execution as _exec_mod

        meta = tmp_path / "meta"
        meta.mkdir()
        current = meta / "pending_intent_XAUUSD.pkl"
        other_symbol = meta / "pending_intent_USDJPY.pkl"
        tmp_file = meta / "pending_intent_US30_cash.123.tmp"
        current.write_bytes(b"current")
        other_symbol.write_bytes(b"other")
        tmp_file.write_bytes(b"tmp")
        monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(meta))

        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0, pending=True)
        assert stub._check_and_trigger_daily_loss_stop("london") is True

        assert not current.exists()
        assert not other_symbol.exists()
        # The global cleanup only removes committed intent files. Orphan tmp
        # cleanup remains the startup loader's job.
        assert tmp_file.exists()

    def test_trigger_noop_cancel_when_no_pending(self):
        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0, pending=False)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        # No pending intent → cancel not called.
        assert stub.execution.cancel_calls == []

    def test_trigger_logs_daily_loss_stop_candle(self):
        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0)
        stub._check_and_trigger_daily_loss_stop("london")
        states = [call[0] for call in stub.log_candle_calls]
        assert "DAILY_LOSS_STOP" in states

    def test_trigger_is_idempotent(self, _isolate_dormant_path):
        """Second call same day with marker already present is a no-op."""
        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0, pending=True)
        assert stub._check_and_trigger_daily_loss_stop("london") is True
        # State still shows -4.5%; second call sees marker and returns False.
        assert stub._check_and_trigger_daily_loss_stop("london") is False
        # cancel should have fired only once.
        assert stub.execution.cancel_calls.count("daily_loss_stop") == 1

    def test_trigger_respects_cap_override(self, _isolate_dormant_path):
        """A profile pinning cap_pct=2.0 must trigger at -2.1% instead of -4%."""
        stub = self._make_stub(pnl_pct=-2.1, cap_pct=2.0)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True

    def test_trigger_skipped_when_cap_invalid(self, _isolate_dormant_path):
        """Non-positive cap disables the stop (fail-open to Gate 3)."""
        stub = self._make_stub(pnl_pct=-10.0, cap_pct=0.0)
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is False
        assert not _isolate_dormant_path.exists()

    def test_trigger_survives_cancel_exception(self, _isolate_dormant_path):
        """A pending-cancel raise must not prevent the marker from being
        persisted — the dormant marker is the authoritative signal."""
        stub = self._make_stub(pnl_pct=-4.5, cap_pct=4.0, pending=True)

        def _boom(reason):
            raise RuntimeError("simulated cancel failure")

        stub.execution.cancel_limit_intent = _boom  # type: ignore[assignment]
        fired = stub._check_and_trigger_daily_loss_stop("london")
        assert fired is True
        assert _isolate_dormant_path.exists()

    def test_dormant_gate_helper_cancels_local_in_memory_pending_intent(self):
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.execution = _StubExecution(pending_intent=_PendingIntentStub())
        cleared_records = []
        orch._clear_pending_trade_record = (  # type: ignore[attr-defined]
            lambda trade_id, reason: cleared_records.append((trade_id, reason))
        )

        canceled = orch._cancel_local_pending_intent_for_dormant(
            reason="daily_loss_stop_dormant",
        )

        assert canceled is True
        assert orch.execution.pending_intent is None
        assert orch.execution.cancel_calls == ["daily_loss_stop_dormant"]
        assert cleared_records == [
            ("XAUUSD_20260421_london_0700", "daily_loss_stop_dormant")
        ]


# --------------------------------------------------------------------------
# Bug #25 regression — equity=0 transient must NOT trigger daily-loss-stop
# --------------------------------------------------------------------------
#
# Background (2026-04-27 10:45 UTC GBPUSD orchestrator)
# -----------------------------------------------------
# ``mt5.account_info()`` transiently returned None under load. The
# ``RealMT5.get_account_equity`` wrapper substituted 0.0 (its fail-safe).
# Pre-fix orchestrator computed ``daily_pnl_pct = (0 - 100000) / 100000 *
# 100 = -100%``; ``_check_and_trigger_daily_loss_stop`` saw -100% > -4%
# cap and wrote the dormant marker. Real account equity at the time was
# $99,995.02; the symbol was blocked from trading until manual cleanup.
#
# Fix (commit ef459e6)
# --------------------
# ``src/safety/equity_guard.py`` adds two layers:
#   1. ``safe_read_equity`` returns None (with anomaly log) on equity<=0.
#   2. ``EquityFilter`` rolling-median-of-5 absorbs single-tick outliers
#      and returns ``None`` consensus until a valid read arrives.
# ``_update_daily_pnl`` skips the P&L update when the filter returns
# ``None``, so ``daily_pnl_pct`` is never tainted by the bad read.
# ``_check_and_trigger_daily_loss_stop`` then sees the prior good
# ``daily_pnl_pct`` (or 0 for first call) and does NOT fire.


class _EquityScriptedMT5:
    """MT5 stub whose ``get_account_equity`` returns a scripted sequence.

    First read returns the configured ``transient_value`` (typically 0
    to reproduce bug #25); subsequent reads return ``healthy_value``.
    Mirrors the live failure-then-recovery cadence.
    """

    def __init__(self, *, transient_value: float = 0.0,
                 healthy_value: float = 99_995.02,
                 transient_count: int = 1):
        self._calls = 0
        self._transient_count = transient_count
        self._transient_value = transient_value
        self._healthy_value = healthy_value
        # No live deal data — Bug #25 is independent of trade history.
        self._deals: list[dict] = []

    def get_account_equity(self) -> float:
        self._calls += 1
        if self._calls <= self._transient_count:
            return self._transient_value
        return self._healthy_value

    def get_account_balance(self) -> float:
        return self._healthy_value

    def get_history_deals(self, from_date, to_date, symbol=None):  # noqa: ARG002
        return list(self._deals)


class _Bug25Orchestrator:
    """Lightweight orchestrator wrapper that binds the real bug #25
    methods (``_update_daily_pnl`` + ``_check_and_trigger_daily_loss_stop``)
    onto a hand-built session_state. Keeps the test surgical: we exercise
    the real production code path without instantiating the full
    ``SessionOrchestrator``.
    """

    def __init__(self, *, mt5, symbol="GBPUSD", start_equity=100_000.0,
                 cap_pct=4.0):
        from src.components.orchestrator import SessionOrchestrator as _Orch
        from src.safety.equity_guard import EquityFilter

        self.config = {"risk": {"max_daily_loss_pct": cap_pct}}
        self.session_state = {
            "daily_pnl_pct": 0.0,
            "start_equity": start_equity,
            "start_balance": start_equity,
            "consecutive_losses": 0,
            "losses_today": 0,
        }
        self.mt5 = mt5
        self.execution = _StubExecution(pending_intent=None)
        self._symbol = symbol
        self._equity_filter = EquityFilter(symbol=symbol)
        self.log_candle_calls: list[tuple[str, str, str]] = []
        self._pending_trade_record_path = None

        # Bind production methods.
        self._update_daily_pnl = _Orch._update_daily_pnl.__get__(self)  # type: ignore[attr-defined]
        self._check_and_trigger_daily_loss_stop = (
            _Orch._check_and_trigger_daily_loss_stop.__get__(self)  # type: ignore[attr-defined]
        )

    def _log_candle(self, state: str, reason: str, kill_zone: str) -> None:
        self.log_candle_calls.append((state, reason, kill_zone))


class TestBug25EquityZeroNotTriggering:
    """Regression: an equity=0 transient read must NOT cross the
    daily-loss-stop threshold; the dormant marker must NOT be written;
    the anomaly must be recorded for production quantification.
    """

    @pytest.fixture(autouse=True)
    def _isolate_anomaly_log(self, tmp_path, monkeypatch):
        """Redirect EQUITY_ANOMALY_LOG_PATH to a per-test tmp file."""
        from src.safety import equity_guard as _eg
        path = tmp_path / "equity_read_anomalies.jsonl"
        monkeypatch.setattr(_eg, "EQUITY_ANOMALY_LOG_PATH", path)
        return path

    def test_equity_zero_transient_does_not_trigger_daily_loss_stop(
        self, _isolate_dormant_path, _isolate_anomaly_log,
    ):
        """The exact bug #25 incident: first read returns 0, then real
        equity. Daily-loss-stop must NOT fire; dormant marker must not
        be written; anomaly must be logged.
        """
        mt5 = _EquityScriptedMT5(transient_value=0.0, healthy_value=99_995.02)
        orch = _Bug25Orchestrator(mt5=mt5)

        # First update — transient equity=0. Filter consensus stays None,
        # session_state.daily_pnl_pct unchanged at 0.0 (no taint).
        orch._update_daily_pnl()
        assert orch.session_state["daily_pnl_pct"] == 0.0, (
            "Equity=0 transient must not pollute daily_pnl_pct"
        )

        # Trigger check on the same tick the bad read happened.
        fired = orch._check_and_trigger_daily_loss_stop("london")
        assert fired is False, (
            "Daily-loss-stop must NOT fire on a transient equity=0 read"
        )
        assert not _isolate_dormant_path.exists(), (
            "Dormant marker must NOT be written on a transient equity=0 read"
        )

        # The anomaly must be recorded for production quantification.
        assert _isolate_anomaly_log.exists()
        rows = _isolate_anomaly_log.read_text(encoding="utf-8").strip().splitlines()
        assert len(rows) >= 1
        record = json.loads(rows[0])
        assert record["kind"] == "zero"
        assert record["symbol"] == "GBPUSD"
        assert record["raw_value"] == 0

        # Recovery: next tick has a healthy equity. Filter accepts it, and
        # daily_pnl_pct now reflects (99995.02 - 100000)/100000 = -0.005%.
        orch._update_daily_pnl()
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(
            -0.00498, abs=1e-4,
        ), "Filter must recover when reads return to normal"
        # Still no daily-loss trigger after recovery (well within -4% cap).
        fired2 = orch._check_and_trigger_daily_loss_stop("london")
        assert fired2 is False
        assert not _isolate_dormant_path.exists()

    def test_real_minus_4pct_loss_still_triggers_after_transient_recovery(
        self, _isolate_dormant_path,
    ):
        """Sanity: the fix MUST NOT mask a real -4% loss. After the
        transient resolves to a real -4.5% equity, daily-loss-stop fires
        normally.
        """
        # First reads = 0 (transient); subsequent reads = $95,500
        # (-4.5% from $100k). Use transient_count=1 so the first
        # _update_daily_pnl skips and the second registers the real loss.
        mt5 = _EquityScriptedMT5(
            transient_value=0.0,
            healthy_value=95_500.0,
            transient_count=1,
        )
        orch = _Bug25Orchestrator(mt5=mt5)

        # First tick — transient zero, no pnl movement, no fire.
        orch._update_daily_pnl()
        assert orch._check_and_trigger_daily_loss_stop("london") is False
        assert not _isolate_dormant_path.exists()

        # Second tick — real -4.5% loss reads through. Filter accepts it.
        orch._update_daily_pnl()
        assert orch.session_state["daily_pnl_pct"] == pytest.approx(-4.5, abs=0.01)
        fired = orch._check_and_trigger_daily_loss_stop("london")
        assert fired is True, (
            "A REAL -4.5% loss must still trigger daily-loss-stop"
        )
        assert _isolate_dormant_path.exists()

        loaded = _ds.load_dormant_state()
        assert loaded is not None
        assert loaded["daily_pnl_pct_at_trigger"] == pytest.approx(-4.5, abs=0.01)
        assert loaded["equity_at_trigger"] == pytest.approx(95_500.0, abs=0.01)

    def test_repeated_zero_reads_continue_skipping_pnl_update(
        self, _isolate_dormant_path,
    ):
        """If MT5 returns equity=0 for multiple consecutive ticks, the
        filter never accumulates a valid read; daily_pnl_pct stays
        untouched and daily-loss-stop never fires off the bad data.
        """
        mt5 = _EquityScriptedMT5(
            transient_value=0.0,
            healthy_value=99_995.02,
            transient_count=10,  # 10 consecutive bad reads
        )
        orch = _Bug25Orchestrator(mt5=mt5)

        for _ in range(5):
            orch._update_daily_pnl()
            fired = orch._check_and_trigger_daily_loss_stop("london")
            assert fired is False
        assert orch.session_state["daily_pnl_pct"] == 0.0
        assert not _isolate_dormant_path.exists()
