"""Tests for ``src.safety.heartbeat_monitor`` (T1.1, session 28).

Canonical patterns (per session 21 canon):
- All writes redirect to ``tmp_path`` via module-ref monkeypatch on
  ``_mod.HEARTBEAT_PATH`` / ``_mod.EVENTS_LOG_PATH`` / ``_mod.THROTTLE_STATE_PATH``.
- MT5 is a ``MagicMock``-spec object — never the real ``MetaTrader5`` module.
- Telegram is never exercised over the wire; ``telegram_sender`` is substituted
  for a stub, and the CANCEL-listener is tested with a deterministic
  ``cancel_poller`` callable rather than HTTP mocking.

The production-path write guard installed by ``tests/conftest.py`` will raise
``ProductionWriteError`` if any test leaks a write into ``pipeline_state/``
or ``shadow_logs/``. If a new assertion fires the guard, the test is at
fault, not the module under test — redirect via monkeypatch.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from unittest.mock import MagicMock

import pytest

from src.safety import heartbeat_monitor as _mod


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    """Redirect every module-level production path under ``tmp_path``.

    This is the canonical shape from ``tests/test_ob_continuation_monitor.py``
    — monkeypatch module attributes (NOT ``from X import Y`` rebinds) so all
    call sites inside the module pick up the redirect.
    """
    hb_dir = tmp_path / "pipeline_state"
    hb = hb_dir / "heartbeat.json"
    ev = tmp_path / "shadow_logs" / "heartbeat_flatten_events.jsonl"
    th = tmp_path / "shadow_logs" / "heartbeat_throttle_state.json"
    cfg = tmp_path / "config" / "agent_config.yaml"

    monkeypatch.setattr(_mod, "HEARTBEAT_DIR", hb_dir)
    monkeypatch.setattr(_mod, "HEARTBEAT_PATH", hb)
    monkeypatch.setattr(_mod, "EVENTS_LOG_PATH", ev)
    monkeypatch.setattr(_mod, "THROTTLE_STATE_PATH", th)
    monkeypatch.setattr(_mod, "CONFIG_PATH", cfg)

    return SimpleNamespace(
        root=tmp_path,
        heartbeat_dir=hb_dir,
        heartbeat=hb,
        events=ev,
        throttle=th,
        config=cfg,
    )


def _write_heartbeat_file(path: Path, ts: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"utc": ts.isoformat(), "pid": 12345}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _config_log_only() -> dict:
    """Base config with ``flatten_enabled=false`` (ships-default)."""
    return {
        "heartbeat": {
            "flatten_enabled": False,
            "write_interval_seconds": 30,
            "miss_threshold": 3,
            "telegram_countdown_seconds": 30,
            "telegram_throttle_minutes": 60,
        }
    }


def _config_enabled() -> dict:
    cfg = _config_log_only()
    cfg["heartbeat"]["flatten_enabled"] = True
    # Small countdown so tests run fast even without mocked sleep.
    cfg["heartbeat"]["telegram_countdown_seconds"] = 1
    return cfg


def _in_kz_datetime() -> datetime:
    """UTC time inside XAUUSD London KZ (07:30 UTC Monday 2026-04-20)."""
    return datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)


def _outside_kz_datetime() -> datetime:
    """UTC time outside every current live instrument KZ.

    The 24-symbol surface includes BTCUSD/ETHUSD 00:00-23:59 UTC windows, so
    the clean all-market gap is the half-open 23:59 minute.
    """
    return datetime(2026, 4, 20, 23, 59, tzinfo=timezone.utc)


# =============================================================================
# read_heartbeat_age_seconds — basic age computation
# =============================================================================


class TestReadHeartbeatAge:
    def test_missing_file_returns_none(self, isolated_paths):
        # File does not exist → miss (None)
        assert _mod.read_heartbeat_age_seconds() is None

    def test_fresh_heartbeat_age_near_zero(self, isolated_paths):
        now = datetime.now(timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, now)
        age = _mod.read_heartbeat_age_seconds(now=now)
        assert age is not None
        assert 0.0 <= age < 1.0

    def test_heartbeat_age_matches_delta(self, isolated_paths):
        ts = datetime(2026, 4, 20, 7, 0, 0, tzinfo=timezone.utc)
        now = ts + timedelta(seconds=45)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        age = _mod.read_heartbeat_age_seconds(now=now)
        assert age == pytest.approx(45.0, abs=0.01)

    def test_malformed_json_returns_none(self, isolated_paths):
        isolated_paths.heartbeat.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.heartbeat.write_text("{not valid json", encoding="utf-8")
        assert _mod.read_heartbeat_age_seconds() is None

    def test_missing_utc_key_returns_none(self, isolated_paths):
        isolated_paths.heartbeat.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.heartbeat.write_text(
            json.dumps({"pid": 1}), encoding="utf-8"
        )
        assert _mod.read_heartbeat_age_seconds() is None

    def test_future_dated_heartbeat_returns_none(self, isolated_paths):
        """Clock-drift safety — future timestamps are treated as malformed."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        future = now + timedelta(minutes=5)
        _write_heartbeat_file(isolated_paths.heartbeat, future)
        assert _mod.read_heartbeat_age_seconds(now=now) is None

    def test_non_string_utc_returns_none(self, isolated_paths):
        isolated_paths.heartbeat.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.heartbeat.write_text(
            json.dumps({"utc": 12345}), encoding="utf-8"
        )
        assert _mod.read_heartbeat_age_seconds() is None


# =============================================================================
# is_miss — miss detection rule
# =============================================================================


class TestIsMiss:
    def test_none_age_is_miss(self):
        """Missing/malformed heartbeat counts as miss."""
        assert _mod.is_miss(None) is True

    def test_age_zero_is_not_miss(self):
        assert _mod.is_miss(0.0) is False

    def test_age_45s_under_90s_threshold_not_miss(self):
        # 30s write interval × 3 miss threshold = 90s
        assert _mod.is_miss(45.0) is False

    def test_age_89s_just_under_threshold_not_miss(self):
        assert _mod.is_miss(89.0) is False

    def test_age_90s_at_threshold_is_miss(self):
        """Boundary inclusive on the miss side."""
        assert _mod.is_miss(90.0) is True

    def test_age_95s_above_threshold_is_miss(self):
        assert _mod.is_miss(95.0) is True

    def test_custom_write_interval(self):
        # write_interval=10s × miss_threshold=3 = 30s
        assert _mod.is_miss(25.0, write_interval_seconds=10) is False
        assert _mod.is_miss(30.0, write_interval_seconds=10) is True


# =============================================================================
# any_kill_zone_active — market-hours gate
# =============================================================================


class TestKillZoneGate:
    def test_xauusd_london_active_0700(self):
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        assert _mod.any_kill_zone_active(now=now) is True

    def test_xauusd_london_end_inclusive(self):
        # 10:29 UTC is inside XAUUSD London (ends 10:30 half-open)
        now = datetime(2026, 4, 20, 10, 29, tzinfo=timezone.utc)
        assert _mod.any_kill_zone_active(now=now) is True

    def test_at_exact_end_not_active(self):
        # BTCUSD/ETHUSD end at the half-open 23:59 boundary; no other current
        # live instrument has a KZ covering that minute.
        now = datetime(2026, 4, 20, 23, 59, tzinfo=timezone.utc)
        assert _mod.any_kill_zone_active(now=now) is False

    def test_dead_zone_0500_utc(self):
        assert _mod.any_kill_zone_active(now=_outside_kz_datetime()) is False

    def test_usdjpy_tokyo_active_0100(self):
        now = datetime(2026, 4, 20, 1, 0, tzinfo=timezone.utc)
        assert _mod.any_kill_zone_active(now=now) is True


# =============================================================================
# Tick state machine — fundamental transitions
# =============================================================================


class TestTickFreshHeartbeat:
    """Fresh heartbeat path — miss counter stays at 0."""

    def test_fresh_heartbeat_no_trigger_no_miss(self, isolated_paths):
        """Test 1: fresh heartbeat (age≈0) → no miss, no trigger."""
        now = datetime.now(timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, now)
        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "FRESH"
        assert state.miss_count == 0
        assert state.trigger_candidate_count == 0

    def test_heartbeat_age_45s_no_miss(self, isolated_paths):
        """Test 2: heartbeat age=45s → below 90s threshold → no miss."""
        ts = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now = ts + timedelta(seconds=45)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "FRESH"
        assert state.miss_count == 0


class TestTickMissProgression:
    """Consecutive miss counting."""

    def test_first_miss_increments_counter(self, isolated_paths):
        """Test 3: heartbeat age=95s first reading → miss, counter=1."""
        ts = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now = ts + timedelta(seconds=95)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert state.miss_count == 1
        assert state.trigger_candidate_count == 0

    def test_two_consecutive_misses_no_trigger(self, isolated_paths):
        """Test 4: 2 consecutive misses → no trigger, counter=2."""
        ts = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now = ts + timedelta(seconds=95)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        state = _mod.MonitorState()
        _mod.tick(state, config=_config_log_only(), now=now)
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert state.miss_count == 2
        assert state.trigger_candidate_count == 0

    def test_three_consecutive_misses_trigger_candidate(self, isolated_paths):
        """Test 5: 3 consecutive misses → TRIGGER_CANDIDATE event."""
        ts = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now = ts + timedelta(seconds=95)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        state = _mod.MonitorState()
        _mod.tick(state, config=_config_log_only(), now=now)
        _mod.tick(state, config=_config_log_only(), now=now)
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "TRIGGER_CANDIDATE"
        assert state.trigger_candidate_count == 1
        assert state.miss_count == 0  # counter reset after trigger candidate
        events = _read_events(isolated_paths.events)
        assert any(e["event_type"] == "TRIGGER_CANDIDATE" for e in events)


# =============================================================================
# Tick — full trigger path (3 × trigger_candidate)
# =============================================================================


class TestFullTriggerPath:
    """Tests 6-8: full trigger sequence with/without gates."""

    def _drive_to_nine_misses(
        self,
        state: _mod.MonitorState,
        *,
        config: dict,
        now: datetime,
        mt5_module=None,
        cancel_poller=None,
        telegram_sender=None,
    ) -> dict:
        """Run 9 misses (= 3 trigger candidates) and return the 9th result."""
        result: dict = {}
        for _ in range(9):
            result = _mod.tick(
                state,
                config=config,
                now=now,
                mt5_module=mt5_module,
                cancel_poller=cancel_poller,
                telegram_sender=telegram_sender or (lambda _: True),
                sleep_fn=lambda _s: None,
            )
        return result

    def test_enabled_and_in_kz_triggers_flatten(self, isolated_paths, monkeypatch):
        """Test 6: 3x trigger + flatten_enabled + in_KZ → flatten fires.

        mt5.positions_get returns 2 mock positions; mt5.order_send succeeds
        (retcode=TRADE_RETCODE_DONE). Expect both closed, FLATTENED event.
        """
        ts = _in_kz_datetime() - timedelta(seconds=1000)
        now = _in_kz_datetime()
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        pos_a = SimpleNamespace(
            ticket=111, symbol="XAUUSD", type=0, volume=0.1, magic=20260401,
        )
        pos_b = SimpleNamespace(
            ticket=222, symbol="US30", type=1, volume=0.5, magic=20260401,
        )
        order_result = SimpleNamespace(retcode=_mod.TRADE_RETCODE_DONE, comment="OK")
        mt5 = MagicMock()
        mt5.positions_get.return_value = [pos_a, pos_b]
        mt5.order_send.return_value = order_result

        # Cancel poller returns False indefinitely → no cancel
        cancel_poller = MagicMock(return_value=(False, 0))
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        result = self._drive_to_nine_misses(
            state,
            config=_config_enabled(),
            now=now,
            mt5_module=mt5,
            cancel_poller=cancel_poller,
            telegram_sender=telegram_stub,
        )

        assert result["event"] == "FLATTENED"
        assert result["action"] == "flatten"
        assert result["details"]["attempted"] == 2
        assert len(result["details"]["closed"]) == 2
        assert not result["details"]["failed"]
        # Both order_sends were called
        assert mt5.order_send.call_count == 2
        # Telegram pre-flatten alert was sent
        assert telegram_stub.call_count >= 1
        # Event log contains ARMED + COUNTDOWN_START + FLATTENED
        events = _read_events(isolated_paths.events)
        event_types = [e["event_type"] for e in events]
        assert "ARMED" in event_types
        assert "COUNTDOWN_START" in event_types
        assert "FLATTENED" in event_types

    def test_disabled_feature_logs_only_no_mt5(self, isolated_paths):
        """Test 7: 3x trigger + flatten_enabled=false → log-only, no MT5 call."""
        ts = _in_kz_datetime() - timedelta(seconds=1000)
        now = _in_kz_datetime()
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        mt5 = MagicMock()
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        result = self._drive_to_nine_misses(
            state,
            config=_config_log_only(),
            now=now,
            mt5_module=mt5,
            telegram_sender=telegram_stub,
        )

        assert result["event"] == "FEATURE_DISABLED"
        assert result["action"] == "none"
        # No MT5 calls at all — feature is off
        mt5.order_send.assert_not_called()
        mt5.positions_get.assert_not_called()
        # No Telegram either — log-only mode is silent
        telegram_stub.assert_not_called()
        events = _read_events(isolated_paths.events)
        event_types = [e["event_type"] for e in events]
        assert "FEATURE_DISABLED" in event_types
        assert "ARMED" not in event_types

    def test_outside_kz_logs_only_no_mt5(self, isolated_paths):
        """Test 8: 3x trigger + enabled + outside all KZs → log-only."""
        now = _outside_kz_datetime()
        ts = now - timedelta(seconds=1000)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        mt5 = MagicMock()
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        result = self._drive_to_nine_misses(
            state,
            config=_config_enabled(),
            now=now,
            mt5_module=mt5,
            telegram_sender=telegram_stub,
        )

        assert result["event"] == "OUTSIDE_KZ"
        mt5.order_send.assert_not_called()
        mt5.positions_get.assert_not_called()
        telegram_stub.assert_not_called()
        events = _read_events(isolated_paths.events)
        assert "OUTSIDE_KZ" in [e["event_type"] for e in events]


# =============================================================================
# Counter reset on fresh heartbeat mid-sequence
# =============================================================================


class TestCounterReset:
    """Test 9: fresh heartbeat mid-sequence resets both counters."""

    def test_fresh_heartbeat_resets_miss_counter(self, isolated_paths):
        # First: accumulate 2 misses
        ts_stale = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now_stale = ts_stale + timedelta(seconds=95)
        _write_heartbeat_file(isolated_paths.heartbeat, ts_stale)
        state = _mod.MonitorState()
        _mod.tick(state, config=_config_log_only(), now=now_stale)
        _mod.tick(state, config=_config_log_only(), now=now_stale)
        assert state.miss_count == 2

        # Then: write a fresh heartbeat → counters reset
        ts_fresh = datetime(2026, 4, 20, 7, 2, tzinfo=timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, ts_fresh)
        result = _mod.tick(state, config=_config_log_only(), now=ts_fresh)
        assert result["event"] == "RESET"
        assert state.miss_count == 0
        assert state.trigger_candidate_count == 0

    def test_fresh_heartbeat_resets_trigger_candidate_counter(self, isolated_paths):
        # Drive to 1 trigger candidate (3 misses)
        ts = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        now_stale = ts + timedelta(seconds=95)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)
        state = _mod.MonitorState()
        for _ in range(3):
            _mod.tick(state, config=_config_log_only(), now=now_stale)
        assert state.trigger_candidate_count == 1

        # Fresh heartbeat → both reset
        ts_fresh = datetime(2026, 4, 20, 7, 2, tzinfo=timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, ts_fresh)
        _mod.tick(state, config=_config_log_only(), now=ts_fresh)
        assert state.miss_count == 0
        assert state.trigger_candidate_count == 0


# =============================================================================
# MT5 order_send retry logic
# =============================================================================


class TestMt5RetryBehavior:
    """Test 10: order_send failure → retry 3x with backoff."""

    def test_order_send_fails_retries_three_times(self, isolated_paths):
        pos = SimpleNamespace(
            ticket=999, symbol="XAUUSD", type=0, volume=0.1, magic=20260401,
        )
        mt5 = MagicMock()
        mt5.positions_get.return_value = [pos]
        # All 3 attempts fail with a non-success retcode
        mt5.order_send.return_value = SimpleNamespace(
            retcode=10004, comment="REQUOTE",
        )

        sleep_calls: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        result = _mod.flatten_open_positions(
            mt5,
            retry_attempts=3,
            retry_backoff_seconds=5.0,
            sleep_fn=fake_sleep,
        )

        # 3 attempts per position → 3 order_send calls
        assert mt5.order_send.call_count == 3
        # Backoff between attempts = 2 sleeps of 5s (no sleep after last attempt)
        assert sleep_calls == [5.0, 5.0]
        # Failed list contains the position
        assert len(result["failed"]) == 1
        assert result["failed"][0]["ticket"] == 999
        assert not result["closed"]
        # RETRY_1, RETRY_2, RETRY_3 events plus a FLATTEN_FAILED terminal
        events = _read_events(isolated_paths.events)
        event_types = [e["event_type"] for e in events]
        assert "RETRY_1" in event_types
        assert "RETRY_2" in event_types
        assert "RETRY_3" in event_types
        assert "FLATTEN_FAILED" in event_types

    def test_order_send_succeeds_on_second_attempt(self, isolated_paths):
        pos = SimpleNamespace(
            ticket=800, symbol="XAUUSD", type=0, volume=0.1, magic=20260401,
        )
        mt5 = MagicMock()
        mt5.positions_get.return_value = [pos]
        # First fails, second succeeds
        mt5.order_send.side_effect = [
            SimpleNamespace(retcode=10004, comment="REQUOTE"),
            SimpleNamespace(retcode=_mod.TRADE_RETCODE_DONE, comment="OK"),
        ]

        sleep_calls: list[float] = []

        result = _mod.flatten_open_positions(
            mt5,
            retry_attempts=3,
            retry_backoff_seconds=2.0,
            sleep_fn=sleep_calls.append,
        )
        assert mt5.order_send.call_count == 2
        assert len(sleep_calls) == 1  # one backoff between attempts
        assert len(result["closed"]) == 1
        assert not result["failed"]

    def test_order_send_returns_none_treated_as_failure(self, isolated_paths):
        pos = SimpleNamespace(
            ticket=501, symbol="XAUUSD", type=0, volume=0.1, magic=20260401,
        )
        mt5 = MagicMock()
        mt5.positions_get.return_value = [pos]
        mt5.order_send.return_value = None  # defensive — some MT5 error paths

        result = _mod.flatten_open_positions(
            mt5,
            retry_attempts=2,
            retry_backoff_seconds=0.01,
            sleep_fn=lambda _s: None,
        )
        assert len(result["failed"]) == 1
        assert result["failed"][0]["reason"] == "order_send_returned_none"

    def test_order_send_exception_treated_as_failure(self, isolated_paths):
        pos = SimpleNamespace(
            ticket=502, symbol="XAUUSD", type=0, volume=0.1, magic=20260401,
        )
        mt5 = MagicMock()
        mt5.positions_get.return_value = [pos]
        mt5.order_send.side_effect = RuntimeError("connection lost")

        result = _mod.flatten_open_positions(
            mt5,
            retry_attempts=2,
            retry_backoff_seconds=0.01,
            sleep_fn=lambda _s: None,
        )
        assert len(result["failed"]) == 1
        assert result["failed"][0]["reason"] == "exception"


# =============================================================================
# Telegram CANCEL during countdown
# =============================================================================


class TestCancelDuringCountdown:
    """Test 11: CANCEL during 30s countdown → flatten aborted."""

    def test_cancel_short_circuits_countdown(self, isolated_paths):
        now = _in_kz_datetime()
        ts = now - timedelta(seconds=1000)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        mt5 = MagicMock()
        # Cancel poller returns True on first call → flatten aborted
        cancel_poller = MagicMock(return_value=(True, 42))
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        # Drive 9 misses (= 3 trigger candidates)
        result: dict = {}
        for _ in range(9):
            result = _mod.tick(
                state,
                config=_config_enabled(),
                now=now,
                mt5_module=mt5,
                cancel_poller=cancel_poller,
                telegram_sender=telegram_stub,
                sleep_fn=lambda _s: None,
            )

        assert result["event"] == "CANCELLED"
        assert result["action"] == "cancelled"
        # MT5 was never called — flatten skipped
        mt5.order_send.assert_not_called()
        # Telegram was called twice: pre-flatten + post-cancel ack
        assert telegram_stub.call_count == 2
        events = _read_events(isolated_paths.events)
        event_types = [e["event_type"] for e in events]
        assert "CANCELLED" in event_types
        assert "FLATTENED" not in event_types

    def test_run_countdown_no_cancel_returns_false(self, isolated_paths):
        # Poller always returns False → countdown runs to completion
        poller = MagicMock(return_value=(False, 0))
        sleeps: list[float] = []
        result = _mod.run_countdown_with_cancel_listener(
            countdown_seconds=5,
            poll_interval_seconds=1.0,
            sleep_fn=sleeps.append,
            cancel_poller=poller,
        )
        assert result is False
        # Total sleep time ≈ countdown duration
        assert sum(sleeps) == pytest.approx(5.0, abs=0.1)


# =============================================================================
# Throttle window
# =============================================================================


class TestThrottle:
    """Test 12: second alarm within 60-min throttle window → THROTTLED."""

    def test_throttle_blocks_second_alarm(self, isolated_paths):
        now = _in_kz_datetime()
        ts = now - timedelta(seconds=1000)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        # Mark an alert as having fired 30 min ago (inside 60-min throttle)
        _mod.mark_alert_fired(now=now - timedelta(minutes=30))
        assert _mod.in_throttle_window(now=now) is True

        mt5 = MagicMock()
        cancel_poller = MagicMock(return_value=(False, 0))
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        result: dict = {}
        for _ in range(9):
            result = _mod.tick(
                state,
                config=_config_enabled(),
                now=now,
                mt5_module=mt5,
                cancel_poller=cancel_poller,
                telegram_sender=telegram_stub,
                sleep_fn=lambda _s: None,
            )

        assert result["event"] == "THROTTLED"
        mt5.order_send.assert_not_called()
        telegram_stub.assert_not_called()
        events = _read_events(isolated_paths.events)
        assert "THROTTLED" in [e["event_type"] for e in events]

    def test_throttle_expires_after_window(self, isolated_paths):
        now = _in_kz_datetime()
        # Alert fired 61 min ago — throttle has expired
        _mod.mark_alert_fired(now=now - timedelta(minutes=61))
        assert _mod.in_throttle_window(now=now) is False

    def test_throttle_respects_config_window(self, isolated_paths):
        now = _in_kz_datetime()
        _mod.mark_alert_fired(now=now - timedelta(minutes=10))
        # With 5-min throttle, 10-min-ago alert is past
        assert _mod.in_throttle_window(now=now, throttle_minutes=5) is False
        # With 30-min throttle, 10-min-ago alert is active
        assert _mod.in_throttle_window(now=now, throttle_minutes=30) is True

    def test_throttle_empty_state_not_in_window(self, isolated_paths):
        assert _mod.in_throttle_window() is False

    def test_throttle_bad_timestamp_not_in_window(self, isolated_paths):
        isolated_paths.throttle.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.throttle.write_text(
            json.dumps({"last_alert_utc": "not-a-date"}), encoding="utf-8"
        )
        assert _mod.in_throttle_window() is False


# =============================================================================
# Missing / malformed / future-dated heartbeat treated as miss
# =============================================================================


class TestMissingMalformedFuture:
    """Tests 13-15: missing, malformed, and future-dated heartbeats."""

    def test_missing_file_counts_as_miss(self, isolated_paths):
        """Test 13: missing heartbeat file → miss."""
        # File does not exist
        state = _mod.MonitorState()
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert state.miss_count == 1

    def test_malformed_json_counts_as_miss(self, isolated_paths):
        """Test 14: malformed JSON → miss."""
        isolated_paths.heartbeat.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.heartbeat.write_text(
            "{bad json no close brace", encoding="utf-8"
        )
        state = _mod.MonitorState()
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert state.miss_count == 1

    def test_future_dated_heartbeat_counts_as_miss(self, isolated_paths):
        """Test 15: future-dated heartbeat (clock drift) → miss."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        future_ts = now + timedelta(minutes=5)
        _write_heartbeat_file(isolated_paths.heartbeat, future_ts)
        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert state.miss_count == 1


# =============================================================================
# write_heartbeat (producer side)
# =============================================================================


class TestWriteHeartbeat:
    def test_write_creates_parent_dir(self, isolated_paths):
        # pipeline_state/ dir does not yet exist
        assert not isolated_paths.heartbeat.parent.exists()
        ok = _mod.write_heartbeat(heartbeat_path=isolated_paths.heartbeat)
        assert ok is True
        assert isolated_paths.heartbeat.exists()

    def test_write_payload_has_utc_and_pid(self, isolated_paths):
        _mod.write_heartbeat(heartbeat_path=isolated_paths.heartbeat)
        data = json.loads(isolated_paths.heartbeat.read_text(encoding="utf-8"))
        assert "utc" in data
        assert "pid" in data
        # Parseable ISO timestamp
        ts = datetime.fromisoformat(data["utc"])
        assert ts.tzinfo is not None

    def test_write_extra_fields_merged(self, isolated_paths):
        _mod.write_heartbeat(
            heartbeat_path=isolated_paths.heartbeat,
            extra={"symbol": "XAUUSD"},
        )
        data = json.loads(isolated_paths.heartbeat.read_text(encoding="utf-8"))
        assert data["symbol"] == "XAUUSD"

    def test_write_io_failure_returns_false_no_raise(self, isolated_paths, monkeypatch):
        """Best-effort guarantee: never raises, returns False on IO error."""

        # Force an IO error by pointing at an impossible path that won't be
        # caught by conftest guards (we're already under tmp_path).
        class _BadPath:
            parent = Path("/___definitely_not_a_real_root/a/b")

            def with_suffix(self, _suffix):
                raise OSError("synthetic IO error")

        # Instead: call with a path whose parent is a file (mkdir fails).
        blocker = isolated_paths.root / "blocker_file"
        blocker.write_text("not a directory", encoding="utf-8")
        blocked_path = blocker / "heartbeat.json"
        ok = _mod.write_heartbeat(heartbeat_path=blocked_path)
        assert ok is False  # Returned False, did not raise


# =============================================================================
# Event logging
# =============================================================================


class TestEventLog:
    def test_log_event_appends_json_line(self, isolated_paths):
        _mod.log_event("TRIGGER_CANDIDATE", details={"age": 95.0})
        entries = _read_events(isolated_paths.events)
        assert len(entries) == 1
        assert entries[0]["event_type"] == "TRIGGER_CANDIDATE"
        assert entries[0]["age"] == 95.0
        assert "timestamp" in entries[0]

    def test_log_event_appends_across_calls(self, isolated_paths):
        _mod.log_event("A")
        _mod.log_event("B")
        _mod.log_event("C")
        entries = _read_events(isolated_paths.events)
        assert [e["event_type"] for e in entries] == ["A", "B", "C"]

    def test_log_event_never_raises(self, isolated_paths, monkeypatch):
        """Log failure must not propagate — safety-critical path."""
        # Block write by making the parent a file
        blocker = isolated_paths.root / "cant_be_dir"
        blocker.write_text("x", encoding="utf-8")
        bad_path = blocker / "events.jsonl"
        # Does not raise
        _mod.log_event("X", events_path=bad_path)


# =============================================================================
# Cancel poller (Telegram getUpdates path)
# =============================================================================


class TestCancelPollerLogic:
    """Verify CANCEL detection / update_id threading without hitting network."""

    def test_no_token_returns_false_unchanged_since(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        cancelled, new_since = _mod.poll_telegram_for_cancel(since_update_id=10)
        assert cancelled is False
        assert new_since == 10

    def test_cancel_message_detected(self, monkeypatch):
        """With a fake urlopen, a CANCEL message is surfaced."""
        fake_payload = {
            "ok": True,
            "result": [
                {"update_id": 5, "message": {"text": "cancel"}},
                {"update_id": 6, "message": {"text": "hello"}},
            ],
        }

        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def read(self):
                return json.dumps(fake_payload).encode("utf-8")

        def _fake_urlopen(_url, timeout=None):  # noqa: ARG001
            return _FakeResp()

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "faketoken")
        monkeypatch.setattr(
            _mod.urllib.request, "urlopen", _fake_urlopen,
        )
        cancelled, new_since = _mod.poll_telegram_for_cancel(since_update_id=0)
        assert cancelled is True
        assert new_since == 6

    def test_non_ok_response_returns_false(self, monkeypatch):
        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return None

            def read(self):
                return b'{"ok": false, "result": []}'

        def _fake_urlopen(_url, timeout=None):  # noqa: ARG001
            return _FakeResp()

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "faketoken")
        monkeypatch.setattr(_mod.urllib.request, "urlopen", _fake_urlopen)
        cancelled, new_since = _mod.poll_telegram_for_cancel(since_update_id=3)
        assert cancelled is False
        assert new_since == 3

    def test_http_error_returns_false(self, monkeypatch):
        def _raise(*_args, **_kwargs):
            raise _mod.urllib.error.URLError("boom")

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "faketoken")
        monkeypatch.setattr(_mod.urllib.request, "urlopen", _raise)
        cancelled, new_since = _mod.poll_telegram_for_cancel(since_update_id=7)
        assert cancelled is False
        assert new_since == 7


# =============================================================================
# Kill-zone coverage — spot-check each instrument has at least one window
# =============================================================================


class TestKillZoneCoverage:
    """Sanity: each tracked instrument has at least one KZ entry."""

    def test_xauusd_in_zones(self):
        instruments = {sym for sym, _s, _e in _mod.KILL_ZONES_UTC}
        assert "XAUUSD" in instruments

    def test_all_supervised_orchestrator_instruments_covered(self):
        instruments = {sym for sym, _s, _e in _mod.KILL_ZONES_UTC}
        for expected in (
            "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP",
            "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225",
            "NAS100", "NZDUSD", "SPX500", "UK100", "UKOIL_cash",
            "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash",
            "XAGUSD", "XAUUSD",
        ):
            assert expected in instruments, f"missing KZ for {expected}"


# =============================================================================
# No-mt5 fallback (safety: even with flatten_enabled=true, missing MT5 is safe)
# =============================================================================


class TestNoMt5Fallback:
    def test_enabled_without_mt5_logs_flatten_failed(self, isolated_paths):
        """If MT5 module is None but feature enabled + in-KZ, log FLATTEN_FAILED
        and set throttle so we don't spin."""
        now = _in_kz_datetime()
        ts = now - timedelta(seconds=1000)
        _write_heartbeat_file(isolated_paths.heartbeat, ts)

        cancel_poller = MagicMock(return_value=(False, 0))
        telegram_stub = MagicMock(return_value=True)

        state = _mod.MonitorState()
        result: dict = {}
        for _ in range(9):
            result = _mod.tick(
                state,
                config=_config_enabled(),
                now=now,
                mt5_module=None,  # no MT5
                cancel_poller=cancel_poller,
                telegram_sender=telegram_stub,
                sleep_fn=lambda _s: None,
            )
        assert result["event"] == "FLATTEN_FAILED"
        # Throttle state is set so we don't re-fire immediately
        assert _mod.in_throttle_window(now=now) is True


# =============================================================================
# Load-config resilience
# =============================================================================


class TestLoadConfig:
    def test_missing_config_returns_empty(self, isolated_paths):
        # Config path does not exist
        assert _mod.load_config() == {}

    def test_malformed_yaml_returns_empty(self, isolated_paths):
        isolated_paths.config.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.config.write_text(
            "heartbeat:\n  flatten_enabled: [", encoding="utf-8"
        )
        assert _mod.load_config() == {}

    def test_valid_yaml_returns_parsed(self, isolated_paths):
        isolated_paths.config.parent.mkdir(parents=True, exist_ok=True)
        isolated_paths.config.write_text(
            "heartbeat:\n  flatten_enabled: true\n  miss_threshold: 5\n",
            encoding="utf-8",
        )
        cfg = _mod.load_config()
        assert cfg["heartbeat"]["flatten_enabled"] is True
        assert cfg["heartbeat"]["miss_threshold"] == 5


# =============================================================================
# Per-symbol heartbeat architecture (April 2026)
#
# These tests cover the silent-fleet-degradation fix: a single shared
# heartbeat.json file hides the case where 6 of 7 orchestrators die and
# the 7th keeps writing (last-writer-wins masks the dead majority). Per-
# symbol files + read-oldest-age across the fleet defeats that pattern.
# =============================================================================


def _write_per_symbol_heartbeat(hb_dir: Path, symbol: str, ts: datetime) -> Path:
    """Write a heartbeat_{SYMBOL}.json file. Returns the path written."""
    hb_dir.mkdir(parents=True, exist_ok=True)
    target = hb_dir / f"heartbeat_{symbol}.json"
    payload = {"utc": ts.isoformat(), "pid": 12345, "symbol": symbol}
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


class TestPerSymbolPathDerivation:
    """``per_symbol_heartbeat_path`` + sanitization."""

    def test_normal_symbol_path(self, isolated_paths):
        path = _mod.per_symbol_heartbeat_path("XAUUSD")
        assert path == isolated_paths.heartbeat_dir / "heartbeat_XAUUSD.json"

    def test_symbol_with_underscore(self, isolated_paths):
        # US30_cash is the redacted_account-overridden form
        path = _mod.per_symbol_heartbeat_path("US30_cash")
        assert path.name == "heartbeat_US30_cash.json"

    def test_symbol_path_traversal_sanitized(self, isolated_paths):
        # Defensive: a malformed symbol must not escape the dir
        path = _mod.per_symbol_heartbeat_path("../../etc/passwd")
        assert path.parent == isolated_paths.heartbeat_dir
        # The slashes / dots are scrubbed to underscores
        assert "/" not in path.name
        assert ".." not in path.name

    def test_empty_symbol_yields_empty_suffix(self, isolated_paths):
        # Edge case: empty string sanitizes to empty, so file is "heartbeat_.json"
        path = _mod.per_symbol_heartbeat_path("")
        assert path.name == "heartbeat_.json"


class TestPerSymbolWrite:
    """Component 1: 7 orchestrators write 7 distinct files."""

    def test_seven_orchestrators_write_seven_files(self, isolated_paths):
        symbols = [
            "XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100",
        ]
        for sym in symbols:
            ok = _mod.write_heartbeat(extra={"symbol": sym})
            assert ok is True

        # 7 distinct files now exist
        files = sorted(isolated_paths.heartbeat_dir.glob("heartbeat_*.json"))
        assert len(files) == 7
        names = {f.name for f in files}
        for sym in symbols:
            assert f"heartbeat_{sym}.json" in names

        # Each file's payload reflects the symbol that wrote it
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            assert data["symbol"] in symbols
            # Filename matches embedded symbol
            assert f.name == f"heartbeat_{data['symbol']}.json"

    def test_write_with_symbol_does_not_touch_legacy(self, isolated_paths):
        _mod.write_heartbeat(extra={"symbol": "XAUUSD"})
        # Per-symbol file written
        assert (isolated_paths.heartbeat_dir / "heartbeat_XAUUSD.json").exists()
        # Legacy file NOT written (scoped writers stay in their lane)
        assert not isolated_paths.heartbeat.exists()

    def test_write_without_symbol_falls_back_to_legacy_with_warning(
        self, isolated_paths, caplog,
    ):
        import logging as _stdlib_logging
        with caplog.at_level(_stdlib_logging.WARNING, logger=_mod.logger.name):
            ok = _mod.write_heartbeat(extra=None)
        assert ok is True
        # Legacy file written
        assert isolated_paths.heartbeat.exists()
        # WARNING surfaced about missing symbol
        assert any(
            "missing symbol" in rec.message
            for rec in caplog.records
            if rec.levelno >= _stdlib_logging.WARNING
        )

    def test_explicit_heartbeat_path_overrides_symbol_routing(self, isolated_paths):
        custom = isolated_paths.root / "custom_hb.json"
        ok = _mod.write_heartbeat(
            heartbeat_path=custom, extra={"symbol": "XAUUSD"},
        )
        assert ok is True
        assert custom.exists()
        # Per-symbol file NOT created — explicit override won
        assert not (isolated_paths.heartbeat_dir / "heartbeat_XAUUSD.json").exists()


class TestDiscoverHeartbeatPaths:
    """Component 1: monitor's read logic — prefer per-symbol files, fall back."""

    def test_no_files_returns_empty_list(self, isolated_paths):
        # heartbeat dir doesn't exist yet
        assert _mod.discover_heartbeat_paths() == []

    def test_only_per_symbol_files_returned(self, isolated_paths):
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        for sym in ("XAUUSD", "US30", "USDJPY"):
            _write_per_symbol_heartbeat(isolated_paths.heartbeat_dir, sym, now)

        paths = _mod.discover_heartbeat_paths()
        assert len(paths) == 3
        names = sorted(p.name for p in paths)
        assert names == [
            "heartbeat_US30.json",
            "heartbeat_USDJPY.json",
            "heartbeat_XAUUSD.json",
        ]

    def test_legacy_excluded_from_per_symbol_glob(self, isolated_paths):
        """Per-symbol files coexist with legacy heartbeat.json — legacy is excluded
        when per-symbol files are present."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        # Legacy file present
        _write_heartbeat_file(isolated_paths.heartbeat, now)
        # Per-symbol file present
        _write_per_symbol_heartbeat(isolated_paths.heartbeat_dir, "XAUUSD", now)

        paths = _mod.discover_heartbeat_paths()
        # Only the per-symbol file is returned — legacy is suppressed
        assert len(paths) == 1
        assert paths[0].name == "heartbeat_XAUUSD.json"

    def test_legacy_fallback_when_no_per_symbol(self, isolated_paths):
        """Component 3 migration safety: legacy file is read if no per-symbol
        files exist (handles half-deployed state)."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, now)

        paths = _mod.discover_heartbeat_paths()
        assert len(paths) == 1
        assert paths[0] == isolated_paths.heartbeat

    def test_alphabetical_order_stable(self, isolated_paths):
        """Reproducible breakdown ordering for events log."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        for sym in ("ZZZ", "AAA", "MMM"):
            _write_per_symbol_heartbeat(isolated_paths.heartbeat_dir, sym, now)

        paths = _mod.discover_heartbeat_paths()
        names = [p.name for p in paths]
        assert names == [
            "heartbeat_AAA.json",
            "heartbeat_MMM.json",
            "heartbeat_ZZZ.json",
        ]


class TestReadOldestHeartbeatAge:
    """Component 1: aggregates oldest age across all files."""

    def test_no_files_returns_none_age_empty_breakdown(self, isolated_paths):
        age, breakdown = _mod.read_oldest_heartbeat_age_seconds()
        assert age is None
        assert breakdown == {}

    def test_all_fresh_returns_max_age(self, isolated_paths):
        # Two fresh files, ages 10s and 30s. Oldest = 30s.
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD",
            now - timedelta(seconds=10),
        )
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "US30",
            now - timedelta(seconds=30),
        )

        age, breakdown = _mod.read_oldest_heartbeat_age_seconds(now=now)
        assert age == pytest.approx(30.0, abs=0.01)
        assert set(breakdown.keys()) == {
            "heartbeat_XAUUSD.json", "heartbeat_US30.json",
        }
        assert breakdown["heartbeat_XAUUSD.json"] == pytest.approx(10.0, abs=0.01)
        assert breakdown["heartbeat_US30.json"] == pytest.approx(30.0, abs=0.01)

    def test_one_silent_orchestrator_dominates_oldest(self, isolated_paths):
        """The KEY test: 6 fresh + 1 stale → oldest reflects the stale one,
        not the 6 fresh ones masking it."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        # 6 fresh orchestrators, 5 second age
        for sym in ("US30", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100"):
            _write_per_symbol_heartbeat(
                isolated_paths.heartbeat_dir, sym, now - timedelta(seconds=5),
            )
        # 1 silent orchestrator, 600 second age (way past 90s threshold)
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=600),
        )

        age, breakdown = _mod.read_oldest_heartbeat_age_seconds(now=now)
        assert age == pytest.approx(600.0, abs=0.01)
        # The XAUUSD file is the stalest in the breakdown
        assert breakdown["heartbeat_XAUUSD.json"] == pytest.approx(600.0, abs=0.01)
        assert _mod.is_miss(age) is True  # would trigger MISS path in tick()

    def test_one_corrupt_file_returns_none_age(self, isolated_paths):
        """Failure isolation, partial: a corrupt file forces None aggregate
        but the breakdown still records the OTHER files' ages — visibility
        is not lost when one file goes bad."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        # 2 healthy
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=5),
        )
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "US30", now - timedelta(seconds=15),
        )
        # 1 corrupt
        bad = isolated_paths.heartbeat_dir / "heartbeat_USDJPY.json"
        bad.write_text("{not valid json", encoding="utf-8")

        age, breakdown = _mod.read_oldest_heartbeat_age_seconds(now=now)
        # Aggregate is None — corrupt file forces a miss
        assert age is None
        # Breakdown still has all three entries (failure isolation)
        assert len(breakdown) == 3
        assert breakdown["heartbeat_USDJPY.json"] is None
        assert breakdown["heartbeat_XAUUSD.json"] == pytest.approx(5.0, abs=0.01)
        assert breakdown["heartbeat_US30.json"] == pytest.approx(15.0, abs=0.01)

    def test_corrupt_file_does_not_poison_others_read(self, isolated_paths):
        """Failure isolation, structural: a corrupt file does NOT raise out of
        the multi-file reader. Each file is read in its own try/except."""
        now = datetime(2026, 4, 20, 7, 0, tzinfo=timezone.utc)
        # 2 corrupt + 1 healthy
        bad1 = isolated_paths.heartbeat_dir / "heartbeat_AAA.json"
        bad1.parent.mkdir(parents=True, exist_ok=True)
        bad1.write_text("not json at all", encoding="utf-8")
        bad2 = isolated_paths.heartbeat_dir / "heartbeat_BBB.json"
        bad2.write_text(json.dumps({"pid": 1}), encoding="utf-8")  # missing utc
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=5),
        )

        # Should not raise; should report the healthy file plus None for bad
        age, breakdown = _mod.read_oldest_heartbeat_age_seconds(now=now)
        assert age is None  # forced miss because of corrupt entries
        assert breakdown["heartbeat_XAUUSD.json"] == pytest.approx(5.0, abs=0.01)
        assert breakdown["heartbeat_AAA.json"] is None
        assert breakdown["heartbeat_BBB.json"] is None


class TestTickFleetWide:
    """Component 1 + tick() integration: silent-fleet-degradation detection."""

    def test_one_orchestrator_silent_six_fresh_fires_miss(self, isolated_paths):
        """The Apr 24-25 silent-fleet pattern: 6 of 7 happy, 1 silent → MISS."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        # 6 fresh
        for sym in ("US30", "USDJPY", "GBPJPY", "GBPUSD", "XAGUSD", "NAS100"):
            _write_per_symbol_heartbeat(
                isolated_paths.heartbeat_dir, sym, now - timedelta(seconds=5),
            )
        # XAUUSD silent for 600s
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=600),
        )

        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        # 600s > 90s threshold → MISS event (pre-trigger)
        assert result["event"] == "MISS"
        assert result["age_seconds"] == pytest.approx(600.0, abs=0.01)
        assert result["stalest_file"] == "heartbeat_XAUUSD.json"
        # Per-file breakdown is in the result for triage
        assert len(result["per_file_ages"]) == 7
        assert result["per_file_ages"]["heartbeat_XAUUSD.json"] == pytest.approx(
            600.0, abs=0.01,
        )
        # Fresh ones in breakdown too
        assert result["per_file_ages"]["heartbeat_US30.json"] == pytest.approx(
            5.0, abs=0.01,
        )

    def test_all_fresh_no_miss(self, isolated_paths):
        """Healthy fleet → FRESH event."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        for sym in ("XAUUSD", "US30", "USDJPY"):
            _write_per_symbol_heartbeat(
                isolated_paths.heartbeat_dir, sym, now - timedelta(seconds=5),
            )

        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "FRESH"
        # stalest_file is the oldest of the fresh ones (5s ago)
        # All 3 are equally fresh, but breakdown still populated
        assert len(result["per_file_ages"]) == 3

    def test_trigger_candidate_event_includes_breakdown(self, isolated_paths):
        """When TRIGGER_CANDIDATE is logged, the events file captures the
        per-symbol breakdown so an operator can identify the silent symbol."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        # Stale file → 3 misses → TRIGGER_CANDIDATE
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=600),
        )
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "US30", now - timedelta(seconds=5),
        )

        state = _mod.MonitorState()
        result = None
        for _ in range(3):
            result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "TRIGGER_CANDIDATE"

        events = _read_events(isolated_paths.events)
        tc_events = [e for e in events if e["event_type"] == "TRIGGER_CANDIDATE"]
        assert len(tc_events) == 1
        # The TC event details include the per-file breakdown so an operator
        # scanning the cascade log can see which orchestrator went dark.
        assert tc_events[0]["stalest_file"] == "heartbeat_XAUUSD.json"
        assert "per_file_ages" in tc_events[0]
        assert (
            tc_events[0]["per_file_ages"]["heartbeat_XAUUSD.json"]
            == pytest.approx(600.0, abs=0.01)
        )


class TestMigrationFallback:
    """Component 3: migration plan — monitor reads legacy heartbeat.json
    when no per-symbol files exist (half-deployed state safety)."""

    def test_legacy_only_state_reads_legacy(self, isolated_paths):
        """During migration: if no per-symbol files exist but legacy does,
        monitor falls back to legacy."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        # Only legacy file present (pre-migration state, or fallback writer fired)
        _write_heartbeat_file(isolated_paths.heartbeat, now - timedelta(seconds=5))

        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        # Legacy fresh → FRESH event
        assert result["event"] == "FRESH"
        assert "heartbeat.json" in result["per_file_ages"]
        assert result["per_file_ages"]["heartbeat.json"] == pytest.approx(
            5.0, abs=0.01,
        )

    def test_legacy_only_stale_fires_miss(self, isolated_paths):
        """Legacy fallback path is functional, not just silently swallowed."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        _write_heartbeat_file(isolated_paths.heartbeat, now - timedelta(seconds=600))

        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        assert result["event"] == "MISS"
        assert result["stalest_file"] == "heartbeat.json"

    def test_per_symbol_files_suppress_legacy_fallback(self, isolated_paths):
        """Once any per-symbol file exists, legacy is no longer consulted —
        otherwise a stale legacy file would corrupt the fleet read."""
        now = datetime(2026, 4, 20, 7, 30, tzinfo=timezone.utc)
        # Stale legacy (600s ago) + fresh per-symbol (5s ago)
        _write_heartbeat_file(isolated_paths.heartbeat, now - timedelta(seconds=600))
        _write_per_symbol_heartbeat(
            isolated_paths.heartbeat_dir, "XAUUSD", now - timedelta(seconds=5),
        )

        state = _mod.MonitorState()
        result = _mod.tick(state, config=_config_log_only(), now=now)
        # Per-symbol fresh wins; legacy ignored
        assert result["event"] == "FRESH"
        assert "heartbeat.json" not in result["per_file_ages"]
        assert "heartbeat_XAUUSD.json" in result["per_file_ages"]


class TestLogPromotion:
    """Component 2: best-effort write failures log at WARNING (was DEBUG)."""

    def test_write_heartbeat_failure_logs_warning(
        self, isolated_paths, caplog, monkeypatch,
    ):
        import logging as _stdlib_logging
        # Force a write failure: monkeypatch os.replace to raise
        def _bad_replace(*_a, **_k):
            raise OSError("synthetic IO failure")

        monkeypatch.setattr(_mod.os, "replace", _bad_replace)

        with caplog.at_level(_stdlib_logging.WARNING, logger=_mod.logger.name):
            ok = _mod.write_heartbeat(extra={"symbol": "XAUUSD"})
        assert ok is False
        # WARNING surfaced (was DEBUG before promotion)
        warning_records = [
            rec for rec in caplog.records
            if rec.levelno >= _stdlib_logging.WARNING
            and "heartbeat write failed" in rec.message
        ]
        assert len(warning_records) >= 1

    def test_log_event_failure_logs_warning(
        self, isolated_paths, caplog,
    ):
        import logging as _stdlib_logging
        # Block log_event by making the events parent dir a file
        blocker = isolated_paths.root / "block_events_dir"
        blocker.write_text("not a dir", encoding="utf-8")
        bad_events = blocker / "events.jsonl"

        with caplog.at_level(_stdlib_logging.WARNING, logger=_mod.logger.name):
            _mod.log_event("X", events_path=bad_events)

        warning_records = [
            rec for rec in caplog.records
            if rec.levelno >= _stdlib_logging.WARNING
            and "event log failed" in rec.message
        ]
        assert len(warning_records) >= 1

    def test_throttle_save_failure_logs_warning(
        self, isolated_paths, caplog,
    ):
        import logging as _stdlib_logging
        # Block throttle save by making the parent path a file
        blocker = isolated_paths.root / "block_throttle_dir"
        blocker.write_text("not a dir", encoding="utf-8")
        bad_throttle = blocker / "throttle.json"

        with caplog.at_level(_stdlib_logging.WARNING, logger=_mod.logger.name):
            _mod._save_throttle_state(
                {"last_alert_utc": "2026-04-20T07:00:00+00:00"},
                path=bad_throttle,
            )

        warning_records = [
            rec for rec in caplog.records
            if rec.levelno >= _stdlib_logging.WARNING
            and "throttle state save failed" in rec.message
        ]
        assert len(warning_records) >= 1


class TestStalestSymbolLabel:
    """Helper: ``_stalest_symbol_label`` picks the worst entry."""

    def test_none_age_wins_over_high_age(self):
        # A None entry is worse than any readable age
        breakdown = {
            "heartbeat_AAA.json": 600.0,
            "heartbeat_BBB.json": None,
            "heartbeat_CCC.json": 5.0,
        }
        assert _mod._stalest_symbol_label(breakdown) == "heartbeat_BBB.json"

    def test_max_age_wins_when_all_readable(self):
        breakdown = {
            "heartbeat_AAA.json": 5.0,
            "heartbeat_BBB.json": 600.0,
            "heartbeat_CCC.json": 100.0,
        }
        assert _mod._stalest_symbol_label(breakdown) == "heartbeat_BBB.json"

    def test_empty_breakdown_returns_none(self):
        assert _mod._stalest_symbol_label({}) is None

    def test_all_none_returns_first_alpha(self):
        breakdown = {
            "heartbeat_BBB.json": None,
            "heartbeat_AAA.json": None,
        }
        # Sorted by name when all None
        assert _mod._stalest_symbol_label(breakdown) == "heartbeat_AAA.json"
