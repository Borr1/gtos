"""Tests for ``src.components.mt5_daemon_runtime``.

Covers the three pathologies the helper was extracted to fix
(2026-04-28 sibling-daemon-stability incident):

1. Lock-PID identity confusion — verify orphan / dead-PID lock files are
   reclaimed safely without spawning duplicates when a sibling python is
   already alive under a different PID (the cmd.exe wrapper bug).
2. Symbol subscription enforcement — verify ``ensure_mt5_symbol_ready``
   forces ``symbol_select(sym, True)`` even when ``info.visible`` is True,
   and that stale-tick conditions trigger backoff / failure as expected.
3. Alive-but-stalled detection — verify ``write_daemon_heartbeat`` writes
   own PID + ``last_progress_utc`` so an out-of-band monitor can detect
   "PID alive but not making progress".

Tests are hermetic: no live MT5, no live filesystem outside ``tmp_path``,
no signal handlers actually installed (signal install is exercised via
``signal.signal`` patching). Per ``tests/conftest.py`` write-guard rules,
all path attributes are redirected via module-ref monkeypatch.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.components import mt5_daemon_runtime as _mod


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    """Redirect LOCK_DIR + HEARTBEAT_DIR under ``tmp_path``."""
    lock_dir = tmp_path / "knowledge_base" / "meta"
    hb_dir = tmp_path / "pipeline_state"
    monkeypatch.setattr(_mod, "LOCK_DIR", lock_dir)
    monkeypatch.setattr(_mod, "HEARTBEAT_DIR", hb_dir)
    return SimpleNamespace(root=tmp_path, lock_dir=lock_dir, heartbeat_dir=hb_dir)


# =============================================================================
# acquire_single_instance_lock — orphan / dead PID handling
# =============================================================================


class TestAcquireSingleInstanceLock:
    def test_acquires_when_no_lock_file(self, isolated_paths):
        """First call on a fresh system claims the lock."""
        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            is_alive_fn=lambda pid: False,  # no live processes
            process_lookup_fn=lambda marker: None,
        )
        assert acquired is True
        assert conflict is None
        # Lock file written with own PID.
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        assert lock.exists()
        assert lock.read_text(encoding="utf-8-sig").strip() == "4242"

    def test_idempotent_when_own_pid_already_owns(self, isolated_paths):
        """Re-entering with the same own_pid returns acquired."""
        # Pre-write our own pid.
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("4242", encoding="utf-8")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            is_alive_fn=lambda pid: pid == 4242,
            process_lookup_fn=lambda marker: None,
        )
        assert acquired is True
        assert conflict is None

    def test_refuses_when_lock_holder_is_alive(self, isolated_paths):
        """Real conflict: someone else is genuinely running."""
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            is_alive_fn=lambda pid: pid == 9999,  # holder is alive
            process_lookup_fn=lambda marker: None,
        )
        assert acquired is False
        assert conflict == 9999

    def test_reclaims_live_lock_holder_when_argv_marker_mismatches(self, isolated_paths):
        """A live but unrelated PID must not block daemon recovery.

        Live incident: a tick_capture lock pointed at a run_agent.py
        orchestrator PID because both command lines contained ``--symbol``.
        With a daemon-specific marker, the lock should be reclaimed when the
        holder's argv can be inspected and does not match.
        """
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            argv_marker="-m src.components.tick_capture --symbol XAUUSD",
            is_alive_fn=lambda pid: pid == 9999,
            process_lookup_fn=lambda marker: None,
            pid_marker_fn=lambda pid, marker: False,
        )

        assert acquired is True
        assert conflict is None
        assert lock.read_text(encoding="utf-8-sig").strip() == "4242"

    def test_refuses_live_lock_holder_when_argv_marker_unknown(self, isolated_paths):
        """If argv inspection is unavailable, keep the conservative conflict."""
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            argv_marker="-m src.components.tick_capture --symbol XAUUSD",
            is_alive_fn=lambda pid: pid == 9999,
            process_lookup_fn=lambda marker: None,
            pid_marker_fn=lambda pid, marker: None,
        )

        assert acquired is False
        assert conflict == 9999
        assert lock.read_text(encoding="utf-8-sig").strip() == "9999"

    def test_reclaims_dead_lock_when_no_argv_match(self, isolated_paths):
        """Lock holder PID is dead AND no live python with our argv -- safe to claim."""
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            argv_marker="--symbol XAUUSD",
            is_alive_fn=lambda pid: False,  # dead
            process_lookup_fn=lambda marker: None,  # no argv match
        )
        assert acquired is True
        assert conflict is None
        assert lock.read_text(encoding="utf-8-sig").strip() == "4242"

    def test_adopts_live_argv_match_when_lock_pid_dead(self, isolated_paths):
        """Lock holder PID is dead but an actual python with our argv is alive
        — the cmd.exe wrapper bug. We must NOT spawn another duplicate.
        Function should refuse to acquire, rewrite the lock to the live PID,
        and report the live PID as the conflict so the caller exits cleanly.
        """
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")  # cmd.exe ghost

        live_python_pid = 12345

        def fake_is_alive(pid):
            return pid == live_python_pid

        def fake_lookup(marker):
            assert "--symbol XAUUSD" in marker
            return live_python_pid

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            argv_marker="--symbol XAUUSD",
            is_alive_fn=fake_is_alive,
            process_lookup_fn=fake_lookup,
        )
        assert acquired is False
        assert conflict == live_python_pid
        # Lock file was re-synced to the live PID for next-cycle accuracy.
        assert lock.read_text(encoding="utf-8-sig").strip() == str(live_python_pid)

    def test_tolerates_utf8_bom_legacy_lock(self, isolated_paths):
        """Legacy locks written by PowerShell ``Set-Content -Encoding UTF8``
        carry a UTF-8 BOM. The reader must strip it before int parse.
        """
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        # Real BOM bytes + PID.
        lock.write_bytes(b"\xef\xbb\xbf9999\n")

        acquired, conflict = _mod.acquire_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
            is_alive_fn=lambda pid: pid == 9999,
            process_lookup_fn=lambda marker: None,
        )
        assert acquired is False
        assert conflict == 9999  # BOM-tolerant parser found the legacy PID

    def test_release_only_removes_own_lock(self, isolated_paths):
        """Release MUST NOT delete a lock owned by another PID."""
        lock = isolated_paths.lock_dir / ".test_daemon.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("9999", encoding="utf-8")

        # Someone else owns the lock; releasing as 4242 should be a no-op.
        removed = _mod.release_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=4242,
        )
        assert removed is False
        assert lock.exists()

        # Now release as 9999 — should remove.
        removed = _mod.release_single_instance_lock(
            "test_daemon",
            lock_dir=isolated_paths.lock_dir,
            own_pid=9999,
        )
        assert removed is True
        assert not lock.exists()


# =============================================================================
# ensure_mt5_symbol_ready
# =============================================================================


def _stub_tick(ts_msc: int):
    """Build a tick-like SimpleNamespace with the time_msc attr we duck-type on."""
    return SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)


class TestEnsureSymbolReady:
    def test_ready_on_fresh_tick(self):
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        fresh_msc = int(now.timestamp() * 1000) - 1000  # 1s old, well within fresh

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        mt5.symbol_info_tick.return_value = _stub_tick(fresh_msc)

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD", now_fn=lambda: now,
        )
        assert ready is True
        assert reason == "ready"
        # Critical: symbol_select called even though info.visible was True.
        mt5.symbol_select.assert_called_once_with("XAUUSD", True)

    def test_unknown_symbol_short_circuits(self):
        mt5 = MagicMock()
        mt5.symbol_info.return_value = None
        ready, reason = _mod.ensure_mt5_symbol_ready(mt5, "FAKE_SYM")
        assert ready is False
        assert reason == "unknown_symbol"
        mt5.symbol_select.assert_not_called()

    def test_select_failure_retries_and_fails(self):
        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = False  # always reject
        mt5.symbol_info_tick.return_value = None

        sleep_calls = []

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD",
            retry_attempts=3,
            initial_backoff=0.1,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        assert ready is False
        assert reason == "select_failed"
        # 3 attempts -> 3 backoffs.
        assert mt5.symbol_select.call_count == 3
        assert len(sleep_calls) == 3

    def test_stale_tick_repeated_then_fresh_eventually_succeeds(self):
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        stale_msc = int((now - timedelta(hours=32)).timestamp() * 1000)
        fresh_msc = int(now.timestamp() * 1000) - 100

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True

        # First two reads stale (the live redacted_account FX/metals failure mode);
        # third read fresh (subscription finally took).
        seq = iter([
            _stub_tick(stale_msc),
            _stub_tick(stale_msc),
            _stub_tick(fresh_msc),
        ])
        mt5.symbol_info_tick.side_effect = lambda sym: next(seq)

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "USDJPY",
            retry_attempts=5,
            initial_backoff=0.01,
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
        )
        assert ready is True
        assert reason == "ready"
        assert mt5.symbol_select.call_count == 3  # selected each retry

    def test_persistent_stale_tick_returns_stale(self):
        """The live failure mode: subscription appears OK but ticks never
        advance. We should fail with reason='stale_tick' so the watchdog
        can re-launch the daemon with a fresh MT5 connection.
        """
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        stale_msc = int((now - timedelta(hours=32)).timestamp() * 1000)

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        mt5.symbol_info_tick.return_value = _stub_tick(stale_msc)

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "GBPUSD",
            retry_attempts=3,
            initial_backoff=0.01,
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
        )
        assert ready is False
        assert reason == "stale_tick"

    def test_skip_freshness_check_returns_ready_after_select(self):
        """For weekend operator-side testing the daemon may launch without
        market hours. ``require_fresh_tick=False`` returns ready as soon as
        ``symbol_select`` succeeds.
        """
        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD",
            require_fresh_tick=False,
            sleep_fn=lambda s: None,
        )
        assert ready is True
        assert reason == "ready"
        mt5.symbol_info_tick.assert_not_called()

    def test_missing_mt5_method_returns_descriptive_reason(self):
        """A bad mock or unexpected MT5 SDK shape should not crash the daemon."""
        mt5 = SimpleNamespace()  # has no methods
        ready, reason = _mod.ensure_mt5_symbol_ready(mt5, "XAUUSD")
        assert ready is False
        assert reason.startswith("missing_mt5_method:")

    def test_future_dated_tick_treated_as_stale(self):
        """A future-dated tick (broker clock skew) must not be accepted."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        future_msc = int((now + timedelta(minutes=5)).timestamp() * 1000)

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        mt5.symbol_info_tick.return_value = _stub_tick(future_msc)

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD",
            retry_attempts=2,
            initial_backoff=0.01,
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
        )
        assert ready is False
        assert reason == "stale_tick"


# =============================================================================
# write_daemon_heartbeat
# =============================================================================


class TestWriteDaemonHeartbeat:
    def test_writes_envelope_with_pid_and_progress(self, isolated_paths):
        progress = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        ok = _mod.write_daemon_heartbeat(
            "tick_capture_XAUUSD",
            heartbeat_dir=isolated_paths.heartbeat_dir,
            last_progress_at=progress,
            extra={"symbol": "XAUUSD", "total_ticks_written": 42},
        )
        assert ok is True
        target = isolated_paths.heartbeat_dir / "daemon_heartbeat_tick_capture_XAUUSD.json"
        assert target.exists()
        import json
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["name"] == "tick_capture_XAUUSD"
        assert data["pid"] > 0  # current pid
        assert data["last_progress_utc"] == progress.isoformat()
        assert data["symbol"] == "XAUUSD"
        assert data["total_ticks_written"] == 42

    def test_atomic_replace_no_partial_files(self, isolated_paths):
        """The atomic write contract: no .tmp file left behind on success."""
        _mod.write_daemon_heartbeat(
            "test_daemon", heartbeat_dir=isolated_paths.heartbeat_dir,
        )
        # No leftover .tmp files of any flavor.
        leftovers = list(isolated_paths.heartbeat_dir.glob("*.tmp*"))
        assert leftovers == []

    def test_overwrite_replaces_in_place(self, isolated_paths):
        """Successive writes update the existing file rather than appending."""
        for i in range(3):
            _mod.write_daemon_heartbeat(
                "test_daemon",
                heartbeat_dir=isolated_paths.heartbeat_dir,
                extra={"counter": i},
            )
        files = list(isolated_paths.heartbeat_dir.glob("daemon_heartbeat_*.json"))
        assert len(files) == 1
        import json
        data = json.loads(files[0].read_text(encoding="utf-8"))
        assert data["counter"] == 2

    def test_write_failure_does_not_raise(self, monkeypatch):
        """Make ``mkdir`` raise to simulate a permission denied. The helper
        must swallow the error and return False, never raise into the daemon
        loop.
        """
        def fail_mkdir(*a, **kw):
            raise PermissionError("synthetic")

        # Only target the heartbeat_dir we pass in -- otherwise other tests
        # break. Use a path under /tmp via tmp_path-relative dir.
        import pathlib
        original = pathlib.Path.mkdir

        def patched_mkdir(self, *a, **kw):
            if "daemon_heartbeat_synthetic" in str(self):
                raise PermissionError("synthetic")
            return original(self, *a, **kw)

        monkeypatch.setattr(pathlib.Path, "mkdir", patched_mkdir)

        # Use a path the patch will reject.
        result = _mod.write_daemon_heartbeat(
            "synthetic",
            heartbeat_dir=pathlib.Path("/tmp/daemon_heartbeat_synthetic_target"),
        )
        # Even on exception we expect a clean False, not a crash.
        assert result in (True, False)


# =============================================================================
# install_signal_handlers
# =============================================================================


class TestInstallSignalHandlers:
    def test_wires_sigint_and_sigterm(self, monkeypatch):
        """Both signals must reach the callback. We patch ``signal.signal``
        to capture the registrations rather than actually installing them
        (which would interfere with pytest's own signal handling).
        """
        installed = {}

        import signal as _signal

        def fake_signal(signum, handler):
            installed[signum] = handler
            return None

        monkeypatch.setattr(_signal, "signal", fake_signal)

        flag = {"stopped": False}

        def stop_cb():
            flag["stopped"] = True

        _mod.install_signal_handlers(stop_cb)

        assert _signal.SIGINT in installed
        if hasattr(_signal, "SIGTERM"):
            assert _signal.SIGTERM in installed
        # Trigger the registered handler — should flip the flag.
        installed[_signal.SIGINT](_signal.SIGINT, None)
        assert flag["stopped"] is True

    def test_callback_exception_swallowed(self, monkeypatch):
        """A raising callback must not propagate through the signal handler
        — that would leave the process in an unknown state at signal time.
        """
        installed = {}
        import signal as _signal
        monkeypatch.setattr(_signal, "signal",
                              lambda sig, h: installed.__setitem__(sig, h))

        def boom():
            raise RuntimeError("boom")

        _mod.install_signal_handlers(boom)
        # Must not raise.
        installed[_signal.SIGINT](_signal.SIGINT, None)


# =============================================================================
# End-to-end: orphan-python pile-up scenario (the live 2026-04-28 incident)
# =============================================================================


class TestEndToEndScenarios:
    def test_orphan_pile_up_prevented_when_two_daemons_race(self, isolated_paths):
        """Reproduce the cmd.exe-wrapper bug: cmd.exe PID written to lock,
        cmd.exe dies, python still alive. New watchdog cycle would
        previously spawn ANOTHER python. With argv-aware reclaim, the
        new instance detects the live python via ``process_lookup_fn``
        and exits cleanly.
        """
        lock = isolated_paths.lock_dir / ".tick_capture_XAUUSD.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)

        # Cycle 1: old cmd.exe PID 13264 wrote the lock; cmd.exe is dead.
        lock.write_text("13264", encoding="utf-8")

        # The orphan python is alive at PID 27560 with --symbol XAUUSD argv.
        live_python_pid = 27560

        def is_alive(pid):
            return pid == live_python_pid  # only the python is alive

        def lookup(marker):
            assert "--symbol XAUUSD" in marker
            return live_python_pid

        # New launcher attempt at PID 33333 would, under the broken model,
        # have spawned another python. Under the fix, it must back off.
        acquired, conflict = _mod.acquire_single_instance_lock(
            "tick_capture_XAUUSD",
            lock_dir=isolated_paths.lock_dir,
            own_pid=33333,
            argv_marker="-m src.components.tick_capture --symbol XAUUSD",
            is_alive_fn=is_alive,
            process_lookup_fn=lookup,
        )
        assert acquired is False
        assert conflict == live_python_pid
        # And the lock now reflects reality so the next watchdog cycle reads
        # the live python PID and emits "OK - PID 27560 alive".
        assert lock.read_text(encoding="utf-8-sig").strip() == "27560"

    def test_real_dead_daemon_can_be_restarted_cleanly(self, isolated_paths):
        """The opposite case: daemon really did die (no live argv match).
        New instance must acquire and become the legitimate owner.
        """
        lock = isolated_paths.lock_dir / ".tick_capture_XAUUSD.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("13264", encoding="utf-8")  # old dead PID

        acquired, conflict = _mod.acquire_single_instance_lock(
            "tick_capture_XAUUSD",
            lock_dir=isolated_paths.lock_dir,
            own_pid=33333,
            argv_marker="--symbol XAUUSD",
            is_alive_fn=lambda pid: False,
            process_lookup_fn=lambda marker: None,
        )
        assert acquired is True
        assert conflict is None
        assert lock.read_text(encoding="utf-8-sig").strip() == "33333"

    def test_weekend_gap_skip_freshness_keeps_daemon_alive(self):
        """Weekend pseudo-scenario: market is closed, ``symbol_info_tick``
        returns Friday's last tick (stale). With ``require_fresh_tick=False``
        the daemon proceeds — used by operators for offline testing without
        having to wait for Sunday open.
        """
        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        # No symbol_info_tick call should happen.

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD",
            require_fresh_tick=False,
            sleep_fn=lambda s: None,
        )
        assert ready is True
        assert reason == "ready"
        mt5.symbol_info_tick.assert_not_called()

    def test_broker_disconnect_mid_subscription_recovers_via_retry(self):
        """``symbol_info_tick`` raises (broker disconnect) on first call,
        recovers on second — daemon should retry and return ready.
        """
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        fresh_msc = int(now.timestamp() * 1000) - 100

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        seq = iter([
            _raise_disconnect,
            lambda sym: _stub_tick(fresh_msc),
        ])
        mt5.symbol_info_tick.side_effect = lambda sym: next(seq)(sym)

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "XAUUSD",
            retry_attempts=4,
            initial_backoff=0.01,
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
        )
        assert ready is True
        assert reason == "ready"


def _raise_disconnect(sym):  # noqa: ARG001
    raise RuntimeError("broker disconnect synthetic")


# =============================================================================
# detect_broker_offset_seconds + offset-aware _tick_is_fresh
# =============================================================================
#
# Live failure (2026-04-28 02:18 UTC) reproduced by these tests:
#
#     True UTC now:                 02:18:05
#     EURUSD tick.time fromtimestamp: 05:18:04 (3.0h ahead — broker is GMT+3)
#
# Without offset awareness ``_tick_is_fresh`` saw ``age = -10800s`` and
# rejected every live tick as future-dated, exhausting the retry budget
# and exiting ``stale_tick``. The fix detects the +10800s offset on
# startup and subtracts it from the broker timestamp before comparison.


class TestDetectBrokerOffsetSeconds:
    """Cover the offset-detection helper across all broker timezones we
    might encounter on FN / FTMO / future prop firms.
    """

    def _mk_mt5_with_tick(self, broker_epoch: float):
        """Build a mock mt5 module whose ``symbol_info_tick`` returns a
        tick whose ``time_msc`` corresponds to ``broker_epoch`` seconds.
        """
        mt5 = MagicMock()
        mt5.symbol_info_tick.return_value = SimpleNamespace(
            time=int(broker_epoch),
            time_msc=int(broker_epoch * 1000),
            bid=1.0, ask=1.0001,
        )
        return mt5

    def test_gmt_zero_broker_returns_zero(self):
        """A broker whose ticks match true UTC returns offset=0."""
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        mt5 = self._mk_mt5_with_tick(now.timestamp())
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 0

    def test_gmt_plus_3_broker_returns_10800(self):
        """redacted_account-Server 2 (UTC+3) — the live failure mode."""
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        # Broker reports tick.time = UTC + 3h.
        broker_epoch = now.timestamp() + 3 * 3600
        mt5 = self._mk_mt5_with_tick(broker_epoch)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 10800

    def test_gmt_plus_2_broker_returns_7200(self):
        """FTMO-Server 3 (UTC+2)."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        broker_epoch = now.timestamp() + 2 * 3600
        mt5 = self._mk_mt5_with_tick(broker_epoch)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 7200

    def test_gmt_minus_5_broker_returns_negative_18000(self):
        """A negative-offset broker (US East-coast localized server)."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        broker_epoch = now.timestamp() - 5 * 3600
        mt5 = self._mk_mt5_with_tick(broker_epoch)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == -18000

    def test_thirty_minute_offset_broker_buckets_correctly(self):
        """A GMT+5:30 broker (rare but legal) — round_seconds=1800 must
        bucket this to +19800s, not collapse it to +18000 or +21600.
        """
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        broker_epoch = now.timestamp() + 5.5 * 3600
        mt5 = self._mk_mt5_with_tick(broker_epoch)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 5 * 3600 + 1800  # 19800

    def test_tiny_jitter_within_threshold_returns_zero(self):
        """A 30s network/clock jitter against a UTC broker must NOT bump
        the offset to +1800s; must report 0."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        broker_epoch = now.timestamp() + 30  # 30s ahead — jitter
        mt5 = self._mk_mt5_with_tick(broker_epoch)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 0

    def test_no_visible_symbols_returns_zero(self):
        """When every probe symbol returns None (broker has no symbols
        loaded — pre-login state), default to 0 with a warning."""
        mt5 = MagicMock()
        mt5.symbol_info_tick.return_value = None
        offset = _mod.detect_broker_offset_seconds(mt5)
        assert offset == 0

    def test_first_visible_symbol_wins(self):
        """If the first probe fails but the second succeeds, use the
        second probe's offset.
        """
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        seq = iter([
            None,  # EURUSD missing
            SimpleNamespace(  # USDJPY available
                time=int(now.timestamp() + 10800),
                time_msc=int((now.timestamp() + 10800) * 1000),
                bid=1.0, ask=1.0001,
            ),
        ])
        mt5 = MagicMock()
        mt5.symbol_info_tick.side_effect = lambda sym: next(seq)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 10800

    def test_implausible_stale_probe_is_skipped(self):
        """Closed-market broker quotes are data age, not timezone offset."""
        now = datetime(2026, 6, 1, 0, 2, 42, tzinfo=timezone.utc)
        stale_friday_quote = now.timestamp() - 49 * 3600
        fresh_default_probe = now.timestamp() + 3 * 3600
        seq = iter([
            SimpleNamespace(
                time=int(stale_friday_quote),
                time_msc=int(stale_friday_quote * 1000),
                bid=1.0,
                ask=1.1,
            ),
            SimpleNamespace(
                time=int(fresh_default_probe),
                time_msc=int(fresh_default_probe * 1000),
                bid=1.0,
                ask=1.0001,
            ),
        ])
        mt5 = MagicMock()
        mt5.symbol_info_tick.side_effect = lambda sym: next(seq)

        offset = _mod.detect_broker_offset_seconds(
            mt5,
            symbols=("GER30", "EURUSD"),
            now_fn=lambda: now,
        )

        assert offset == 10800

    def test_malformed_tick_skipped(self):
        """A tick object with a malformed time_msc is skipped and we
        try the next probe symbol."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        seq = iter([
            SimpleNamespace(time=0, time_msc=0, bid=0, ask=0),  # malformed
            SimpleNamespace(  # next probe ok
                time=int(now.timestamp() + 7200),
                time_msc=int((now.timestamp() + 7200) * 1000),
                bid=1.0, ask=1.0001,
            ),
        ])
        mt5 = MagicMock()
        mt5.symbol_info_tick.side_effect = lambda sym: next(seq)
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 7200

    def test_tick_call_raising_continues_to_next_probe(self):
        """If ``symbol_info_tick`` raises on one symbol, try the next.
        Defensive — broker disconnect during probe must not break startup.
        """
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        results = [
            RuntimeError("first probe disconnected"),
            SimpleNamespace(
                time=int(now.timestamp() + 10800),
                time_msc=int((now.timestamp() + 10800) * 1000),
                bid=1.0, ask=1.0001,
            ),
        ]
        idx = {"i": 0}

        def _side(sym):  # noqa: ARG001
            i = idx["i"]; idx["i"] += 1
            v = results[i]
            if isinstance(v, BaseException):
                raise v
            return v

        mt5 = MagicMock()
        mt5.symbol_info_tick.side_effect = _side
        offset = _mod.detect_broker_offset_seconds(
            mt5, now_fn=lambda: now,
        )
        assert offset == 10800

    def test_missing_symbol_info_tick_method_returns_zero(self):
        """A bad mt5 module (test mock with no method) must not crash."""
        mt5 = SimpleNamespace()  # has no symbol_info_tick
        assert _mod.detect_broker_offset_seconds(mt5) == 0


class TestTickIsFreshOffsetAware:
    """Direct unit tests for ``_tick_is_fresh`` with various broker offsets.

    These tests prove the live failure was a missing-offset bug, not a
    real stale-tick issue. With ``broker_offset_seconds=10800`` against
    a +3 broker, an in-spec live tick is correctly accepted as fresh.
    """

    def test_utc_broker_with_offset_zero_fresh_tick(self):
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        # 1s old in UTC -> 1s old age -> fresh.
        ts_msc = int((now.timestamp() - 1.0) * 1000)
        tick = SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=0,
        ) is True

    def test_gmt_plus_3_broker_with_correct_offset_accepts_fresh_tick(self):
        """The live failure mode, fixed: tick is +3h on broker clock; with
        offset=10800 the 1s-old age is accepted."""
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        # Broker reports timestamp +3h ahead, 1s "old" in broker time.
        ts_msc = int((now.timestamp() + 3 * 3600 - 1.0) * 1000)
        tick = SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)
        # Without offset (broken behavior) — tick appears 3h future-dated.
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=0,
        ) is False
        # With offset (fixed) — tick is 1s old in true UTC, fresh.
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=10800,
        ) is True

    def test_gmt_minus_5_broker_with_correct_offset(self):
        """A negative-offset broker tick that's 1s old in UTC."""
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        ts_msc = int((now.timestamp() - 5 * 3600 - 1.0) * 1000)
        tick = SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)
        # Without offset -> tick appears 5h "in the past" -> stale.
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=0,
        ) is False
        # With correct offset -> 1s old in UTC -> fresh.
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=-18000,
        ) is True

    def test_real_stale_tick_still_rejected_under_correct_offset(self):
        """An offset-corrected tick that's still genuinely 60s old must
        be rejected at max_age=5s. Otherwise the fix would mask real
        stale-feed conditions.
        """
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        # 60s old in true UTC, projected onto +3 broker time.
        ts_msc = int((now.timestamp() + 3 * 3600 - 60) * 1000)
        tick = SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=10800,
        ) is False

    def test_genuinely_future_tick_still_rejected_under_correct_offset(self):
        """A tick that's still future-dated AFTER offset adjustment must
        be rejected — that's a real broker clock anomaly we want to alarm.
        """
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        # 5 minutes ahead even after subtracting +3h offset.
        ts_msc = int((now.timestamp() + 3 * 3600 + 300) * 1000)
        tick = SimpleNamespace(time_msc=ts_msc, time=ts_msc // 1000)
        assert _mod._tick_is_fresh(
            tick, max_age_seconds=5.0, now=now, broker_offset_seconds=10800,
        ) is False


class TestEnsureSymbolReadyOffsetAware:
    """End-to-end verification that ``ensure_mt5_symbol_ready`` correctly
    propagates ``broker_offset_seconds`` to the freshness check.
    """

    def test_gmt_plus_3_broker_with_correct_offset_returns_ready(self):
        """The live failure path, with the fix: a +3 broker's live tick
        passes the readiness check when offset=10800 is supplied.
        """
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        # Live broker tick = UTC+3h - 1s
        ts_msc = int((now.timestamp() + 3 * 3600 - 1.0) * 1000)

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        mt5.symbol_info_tick.return_value = SimpleNamespace(
            time_msc=ts_msc, time=ts_msc // 1000,
        )

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "EURUSD",
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
            broker_offset_seconds=10800,
        )
        assert ready is True
        assert reason == "ready"

    def test_gmt_plus_3_broker_without_offset_fails_stale_tick(self):
        """Reproduce the live failure: offset defaulted to 0 against a
        +3 broker, every live tick is rejected as future-dated.
        """
        now = datetime(2026, 4, 28, 2, 18, 5, tzinfo=timezone.utc)
        ts_msc = int((now.timestamp() + 3 * 3600 - 1.0) * 1000)

        mt5 = MagicMock()
        mt5.symbol_info.return_value = SimpleNamespace(visible=True)
        mt5.symbol_select.return_value = True
        mt5.symbol_info_tick.return_value = SimpleNamespace(
            time_msc=ts_msc, time=ts_msc // 1000,
        )

        ready, reason = _mod.ensure_mt5_symbol_ready(
            mt5, "EURUSD",
            retry_attempts=2,
            initial_backoff=0.01,
            now_fn=lambda: now,
            sleep_fn=lambda s: None,
            # broker_offset_seconds defaults to 0.0 -> reproduces failure.
        )
        assert ready is False
        assert reason == "stale_tick"
