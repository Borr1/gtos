"""Tests for ``src/utils/notification_queue.py`` — PersistentNotificationQueue.

Covers:

1. Enqueue: row appended atomically; alert_id returned.
2. Dedup: same alert_id enqueued twice → second is no-op.
3. Disk-format round-trip: enqueue rows + marker rows readable.
4. Crash safety: pending rows survive process restart (recover from disk).
5. Retry policy — HIGH: exponential backoff, max retries → FAILED.
6. Retry policy — CRITICAL: indefinite retry, age-out at 24h → EXPIRED.
7. Priority routing — LOW: fire-and-forget, no persistence.
8. Compaction: ≥100 markers triggers rewrite, file shrinks.
9. Daily compaction: UTC-midnight crossing rewrites if any markers.
10. Concurrent enqueue: 2 threads, no row corruption.
11. Transport failure → backoff timer respected (no immediate retry).
12. Recovery skips terminal alert_ids (already DELIVERED in prior session).
13. format_telegram_alert + sprt_halt CRITICAL routing wires correctly.
14. notify_alert routes through queue at HIGH level (smoke test).
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils import notification_queue
from src.utils.notification_queue import (
    Level,
    PersistentNotificationQueue,
    _alert_id_for,
    _Entry,
)


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


class _StubClock:
    def __init__(self, dt: datetime) -> None:
        self.dt = dt

    def __call__(self) -> datetime:
        return self.dt

    def advance(self, seconds: int) -> None:
        self.dt = self.dt + timedelta(seconds=seconds)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# 1. Enqueue
# ---------------------------------------------------------------------------


def test_enqueue_appends_row_to_queue_file(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    sent = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda msg: sent.append(msg) or False,  # never delivers
    )
    aid = q.send("hello", level=Level.HIGH)
    assert aid != ""
    rows = _read_jsonl(qpath)
    assert len(rows) == 1
    assert rows[0]["message"] == "hello"
    assert rows[0]["level"] == "HIGH"
    assert rows[0]["alert_id"] == aid


# ---------------------------------------------------------------------------
# 2. Dedup
# ---------------------------------------------------------------------------


def test_dedup_same_alert_id(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda _: False,
    )
    aid1 = q.send("dup", level=Level.HIGH, alert_id="fixed-id")
    aid2 = q.send("dup", level=Level.HIGH, alert_id="fixed-id")
    assert aid1 == aid2 == "fixed-id"
    rows = _read_jsonl(qpath)
    # Only the first enqueue row hits disk.
    enqueue_rows = [r for r in rows if "marker" not in r]
    assert len(enqueue_rows) == 1


# ---------------------------------------------------------------------------
# 3. Disk-format round-trip
# ---------------------------------------------------------------------------


def test_marker_row_written_on_delivery(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    sent = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda msg: sent.append(msg) or True,  # immediate success
    )
    aid = q.send("payload", level=Level.HIGH)
    delivered = q.flush()
    assert delivered == 1
    assert sent == ["payload"]
    rows = _read_jsonl(qpath)
    markers = [r for r in rows if r.get("marker") == "DELIVERED"]
    assert len(markers) == 1
    assert markers[0]["alert_id"] == aid


# ---------------------------------------------------------------------------
# 4. Crash safety / restart recovery
# ---------------------------------------------------------------------------


def test_pending_alerts_survive_restart(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    # Session 1: enqueue 2 alerts, never deliver.
    q1 = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda _: False,
    )
    q1.send("alpha", level=Level.HIGH)
    q1.send("beta", level=Level.CRITICAL)

    # Simulate process exit + restart.
    del q1
    delivered = []
    q2 = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: delivered.append(m) or True,  # delivers now
    )
    # Recover loads pending rows on first .start() (or via _recover_from_disk
    # at flush time when start was never called → load via the public path).
    q2._recover_from_disk()
    assert q2.pending_count() == 2
    n = q2.flush()
    assert n == 2
    assert set(delivered) == {"alpha", "beta"}


def test_recovery_skips_already_delivered(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    sent = []
    q1 = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
    )
    aid = q1.send("once", level=Level.HIGH)
    q1.flush()
    assert sent == ["once"]

    # Restart. Recovery should NOT replay already-delivered alerts.
    del q1
    sent2 = []
    q2 = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent2.append(m) or True,
    )
    q2._recover_from_disk()
    assert q2.pending_count() == 0
    q2.flush()
    assert sent2 == []


# ---------------------------------------------------------------------------
# 5. HIGH retry policy
# ---------------------------------------------------------------------------


def test_high_retry_exponential_backoff_then_fail(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    clock = _StubClock(datetime(2026, 4, 26, 12, 0, 0, tzinfo=timezone.utc))
    attempts = []

    def transport(msg: str) -> bool:
        attempts.append((msg, clock.dt.isoformat()))
        return False  # always fails

    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=transport,
        clock=clock,
        high_max_retries=3,           # custom: 3 retries → FAILED
    )
    q.send("hi", level=Level.HIGH)

    # First flush: immediate attempt (retry_count=0 → 1).
    assert q.flush() == 0  # delivered=0, but the in-memory entry advances.
    assert len(attempts) == 1

    # Second flush BEFORE backoff window → no retry.
    clock.advance(2)  # backoff[0]=5s, so 2s later still in cooldown.
    assert q.flush() == 0
    assert len(attempts) == 1

    # Advance past 5s window.
    clock.advance(10)
    assert q.flush() == 0
    assert len(attempts) == 2

    # Third retry after 30s.
    clock.advance(40)
    assert q.flush() == 0
    assert len(attempts) == 3

    # After max retries, the entry is marked FAILED.
    clock.advance(120 + 10)  # past backoff[2]=120s
    q.flush()
    assert q.pending_count() == 0
    rows = _read_jsonl(qpath)
    failures = [r for r in rows if r.get("marker") == "FAILED"]
    assert len(failures) == 1


# ---------------------------------------------------------------------------
# 6. CRITICAL retry policy + age-out
# ---------------------------------------------------------------------------


def test_critical_retries_indefinitely_then_age_out(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    clock = _StubClock(datetime(2026, 4, 26, 12, 0, 0, tzinfo=timezone.utc))
    attempts = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: attempts.append(m) or False,
        clock=clock,
        critical_age_out_seconds=10 * 24 * 3600,  # 10-day window for retry test
    )
    q.send("CRITICAL ALERT", level=Level.CRITICAL)

    # Crank the clock past saturated backoff (1h) repeatedly. CRITICAL's
    # ladder saturates at 3600s, so 3700s between flushes guarantees a
    # retry every loop.
    for _ in range(10):
        q.flush()
        clock.advance(3700)
    # CRITICAL retried far beyond HIGH's max (5).
    assert len(attempts) > 5
    assert q.pending_count() == 1

    # Now jump past the 10-day age-out window.
    clock.advance(11 * 24 * 3600)
    q.flush()
    rows = _read_jsonl(qpath)
    expired = [r for r in rows if r.get("marker") == "EXPIRED"]
    assert len(expired) == 1
    assert q.pending_count() == 0


# ---------------------------------------------------------------------------
# 7. LOW priority — fire-and-forget
# ---------------------------------------------------------------------------


def test_low_priority_no_persistence(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    sent = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
    )
    aid = q.send("BE update", level=Level.LOW)
    # LOW returns empty alert_id (no persistence).
    assert aid == ""
    assert sent == ["BE update"]
    # Queue file may not even exist.
    assert not qpath.exists() or _read_jsonl(qpath) == []


def test_low_priority_failure_silently_dropped(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda _: False,
    )
    # Failure is swallowed — no exception, no persistence.
    q.send("BE", level=Level.LOW)
    assert q.pending_count() == 0


# ---------------------------------------------------------------------------
# 8. Compaction
# ---------------------------------------------------------------------------


def test_compaction_after_markers_threshold(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    sent = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
        compact_after_markers=5,    # tiny threshold for fast test
    )
    for i in range(10):
        q.send(f"msg-{i}", level=Level.HIGH)
        q.flush()
    # Force the daily-compaction probe (the marker-based threshold runs
    # inside _maybe_compact too).
    q._maybe_compact()
    rows = _read_jsonl(qpath)
    # After compaction, marker rows are gone; only pending (= 0 in this
    # case) remain. So the file should be empty or near-empty.
    assert len(rows) == 0 or all("marker" not in r for r in rows)


# ---------------------------------------------------------------------------
# 9. Daily compaction (UTC midnight crossing)
# ---------------------------------------------------------------------------


def test_daily_compaction_on_utc_midnight_crossing(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    clock = _StubClock(datetime(2026, 4, 25, 23, 59, 30, tzinfo=timezone.utc))
    sent = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
        compact_after_markers=10000,   # very high to isolate daily trigger
        clock=clock,
    )
    # Day 1: deliver some alerts.
    for i in range(3):
        q.send(f"day1-{i}", level=Level.HIGH)
        q.flush()
    assert len(sent) == 3
    pre_size = qpath.stat().st_size

    # Cross UTC midnight + run a poll iteration.
    clock.dt = datetime(2026, 4, 26, 0, 0, 5, tzinfo=timezone.utc)
    q._maybe_compact()
    post_size = qpath.stat().st_size if qpath.exists() else 0
    # Daily compaction should have shrunk (or zeroed) the file.
    assert post_size < pre_size


# ---------------------------------------------------------------------------
# 10. Concurrent enqueue safety
# ---------------------------------------------------------------------------


def test_concurrent_enqueue_no_row_corruption(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda _: False,
    )
    N_THREADS = 4
    N_PER = 25
    barrier = threading.Barrier(N_THREADS)

    def _worker(tid: int):
        barrier.wait()
        for i in range(N_PER):
            q.send(f"t{tid}-i{i}", level=Level.HIGH, alert_id=f"t{tid}-i{i}")

    threads = [threading.Thread(target=_worker, args=(t,)) for t in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    # Every line in the queue file must be valid JSON.
    rows = _read_jsonl(qpath)
    enqueue_rows = [r for r in rows if "marker" not in r]
    # 4 threads × 25 unique alert_ids = 100 unique enqueue rows.
    assert len(enqueue_rows) == N_THREADS * N_PER
    assert q.pending_count() == N_THREADS * N_PER


# ---------------------------------------------------------------------------
# 11. Backoff timer respected
# ---------------------------------------------------------------------------


def test_failed_attempt_respects_backoff_timer(tmp_path):
    qpath = tmp_path / "queue.jsonl"
    clock = _StubClock(datetime(2026, 4, 26, 12, 0, 0, tzinfo=timezone.utc))
    attempts = []
    q = PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: attempts.append(m) or False,
        clock=clock,
    )
    q.send("retry-me", level=Level.HIGH)
    # First attempt: fails immediately.
    q.flush()
    assert len(attempts) == 1
    # Try multiple flushes within backoff window — no new attempts.
    for _ in range(5):
        q.flush()
    assert len(attempts) == 1
    # Advance past 5s backoff → next attempt fires.
    clock.advance(6)
    q.flush()
    assert len(attempts) == 2


# ---------------------------------------------------------------------------
# 12. Module helpers
# ---------------------------------------------------------------------------


def test_alert_id_is_deterministic_for_same_inputs():
    aid1 = _alert_id_for("hello", "2026-04-26T12:00:00+00:00")
    aid2 = _alert_id_for("hello", "2026-04-26T12:00:00+00:00")
    aid3 = _alert_id_for("hello", "2026-04-26T12:00:01+00:00")
    assert aid1 == aid2
    assert aid1 != aid3


# ---------------------------------------------------------------------------
# 13. Singleton + integration with notify_alert / format_telegram_alert
# ---------------------------------------------------------------------------


def test_module_send_uses_singleton(tmp_path, monkeypatch):
    qpath = tmp_path / "queue.jsonl"
    sent = []

    # Reset BEFORE patching so the singleton picks up the new defaults.
    notification_queue._reset_singleton_for_tests()
    monkeypatch.setattr(
        notification_queue,
        "_DEFAULT_QUEUE_PATH",
        str(qpath),
    )
    # Install a tmp_path-bound singleton manually so the constructor sees
    # the test path (the lazy ``get_default_queue`` reads
    # ``_DEFAULT_QUEUE_PATH`` at construction time, which is what we want
    # but only after the monkeypatch has applied).
    notification_queue._SINGLETON = notification_queue.PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
    )
    aid = notification_queue.send("singleton test", level=Level.HIGH)
    assert aid != ""
    q = notification_queue.get_default_queue()
    q.flush()
    q.stop()
    assert sent == ["singleton test"]
    notification_queue._reset_singleton_for_tests()


# ---------------------------------------------------------------------------
# 14. Notify_alert wiring through queue
# ---------------------------------------------------------------------------


def test_configure_from_config_overrides_defaults(tmp_path, monkeypatch):
    """``configure_from_config`` mutates module defaults + clears singleton."""
    from src.utils import notification_queue as nq_mod

    # Stash + reset baseline.
    qpath = tmp_path / "redacted_account_live_bee34003" / "notification_queue.jsonl"
    nq_mod._reset_singleton_for_tests()
    monkeypatch.setattr(nq_mod, "_DEFAULT_QUEUE_PATH", "pipeline_state/notification_queue.jsonl")
    monkeypatch.setattr(nq_mod, "_DEFAULT_QUEUE_PATH_CONFIGURED", False)
    monkeypatch.setattr(nq_mod, "_POLL_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(nq_mod, "_CRITICAL_AGE_OUT_SECONDS", 86400)
    monkeypatch.setattr(nq_mod, "_HIGH_MAX_RETRIES", 5)
    monkeypatch.setattr(nq_mod, "_COMPACT_AFTER_MARKERS", 100)

    nq_mod.configure_from_config(
        {
            "notification_queue": {
                "queue_path": str(qpath),
                "poll_interval_seconds": 10,
                "critical_age_out_seconds": 3600,
                "high_max_retries": 3,
                "compact_after_markers": 50,
            }
        }
    )
    assert nq_mod._DEFAULT_QUEUE_PATH == str(qpath)
    assert nq_mod._DEFAULT_QUEUE_PATH_CONFIGURED is True
    assert nq_mod._POLL_INTERVAL_SECONDS == 10
    assert nq_mod._CRITICAL_AGE_OUT_SECONDS == 3600
    assert nq_mod._HIGH_MAX_RETRIES == 3
    assert nq_mod._COMPACT_AFTER_MARKERS == 50
    q = nq_mod.get_default_queue()
    assert q.queue_path == qpath
    assert q.poll_interval_seconds == 10
    assert q.critical_age_out_seconds == 3600
    assert q.high_max_retries == 3
    assert q.compact_after_markers == 50
    nq_mod._reset_singleton_for_tests()


def test_default_queue_path_uses_environment_until_profile_config_loads(tmp_path, monkeypatch):
    from src.utils import notification_queue as nq_mod

    qpath = tmp_path / "operator_profile" / "notification_queue.jsonl"
    nq_mod._reset_singleton_for_tests()
    monkeypatch.setattr(nq_mod, "_DEFAULT_QUEUE_PATH", "pipeline_state/notification_queue.jsonl")
    monkeypatch.setattr(nq_mod, "_DEFAULT_QUEUE_PATH_CONFIGURED", False)
    monkeypatch.setenv("GTOS_NOTIFICATION_QUEUE_PATH", str(qpath))

    q = nq_mod.get_default_queue()
    assert q.queue_path == qpath
    nq_mod._reset_singleton_for_tests()


def test_worker_lock_path_scopes_runtime_namespace():
    default_lock = notification_queue._worker_lock_path()
    redacted_account_lock = notification_queue._worker_lock_path("redacted_account_live_bee34003")
    ftmo_lock = notification_queue._worker_lock_path("operator_profile")

    assert default_lock.name == ".notification_queue_worker.lock"
    assert redacted_account_lock.name == ".notification_queue_worker_redacted_account_live_bee34003.lock"
    assert ftmo_lock.name == ".notification_queue_worker_operator_profile.lock"
    assert redacted_account_lock != ftmo_lock


def test_dead_zone_status_defaults_follow_account_environment(monkeypatch):
    from src.research_infra import notification_queue_dead_zone_status as dz

    monkeypatch.setenv(
        "GTOS_NOTIFICATION_QUEUE_PATH",
        "pipeline_state/operator_profile/notification_queue.jsonl",
    )
    monkeypatch.setenv("GTOS_RUNTIME_NAMESPACE", "operator_profile")

    assert dz.default_queue_path() == Path(
        "pipeline_state/operator_profile/notification_queue.jsonl"
    )
    assert dz.default_lock_path() == Path(
        "knowledge_base/meta/.notification_queue_worker_operator_profile.lock"
    )


def test_configure_from_config_handles_missing(monkeypatch):
    from src.utils import notification_queue as nq_mod

    monkeypatch.setattr(nq_mod, "_POLL_INTERVAL_SECONDS", 30)
    nq_mod.configure_from_config(None)
    assert nq_mod._POLL_INTERVAL_SECONDS == 30
    nq_mod.configure_from_config({})
    assert nq_mod._POLL_INTERVAL_SECONDS == 30
    nq_mod.configure_from_config({"notification_queue": "not-a-dict"})
    assert nq_mod._POLL_INTERVAL_SECONDS == 30


def test_notify_alert_routes_through_queue(tmp_path, monkeypatch, caplog):
    """src/notifications.notify_alert(text) enqueues at HIGH via the queue."""
    import logging
    import src.notifications as notif

    monkeypatch.delenv("GTOS_ALERT_LABEL", raising=False)
    qpath = tmp_path / "queue.jsonl"
    sent = []
    notification_queue._reset_singleton_for_tests()
    monkeypatch.setattr(
        notification_queue, "_DEFAULT_QUEUE_PATH", str(qpath)
    )
    # Install singleton bound to the tmp_path queue + a fake transport
    # before any caller invokes ``send``.
    test_q = notification_queue.PersistentNotificationQueue(
        queue_path=qpath,
        transport=lambda m: sent.append(m) or True,
    )
    notification_queue._SINGLETON = test_q

    with caplog.at_level(logging.DEBUG):
        notif.notify_alert("daily loss stop hit")
    # Drain pending so the DELIVERED marker is written.
    # NOTE: pull the singleton fresh — earlier-test daemons may have
    # rebound it between our assignment and the `notify_alert` call. We
    # assert in-memory pending was added (the source of truth) instead
    # of reading the disk file (which a poll loop could have compacted).
    q = notification_queue.get_default_queue()
    q.flush()
    q.stop()

    # If notify_alert hit the fallback path, surface the warning to make
    # the failure cause obvious — instead of an opaque "len(enqueue) != 1".
    fallback_msgs = [
        r.getMessage() for r in caplog.records
        if "queue dispatch failed" in r.getMessage()
    ]
    assert not fallback_msgs, (
        f"notify_alert fell back to fire-and-forget: {fallback_msgs}"
    )

    # The alert reached the singleton's transport (post-flush).
    assert len(sent) == 1, f"transport not called; sent={sent}"
    assert "daily loss stop hit" in sent[0]
    assert sent[0].startswith("\u26A0\uFE0F SYSTEM ALERT\n")

    notification_queue._reset_singleton_for_tests()


def test_notify_alert_and_critical_apply_optional_operator_label(monkeypatch):
    """Parallel F5 system alerts carry the wrapper's unmistakable experiment label."""
    import src.notifications as notif

    sent = []
    monkeypatch.setenv("GTOS_ALERT_LABEL", "F5 $10 TEST - FTMO")
    monkeypatch.setattr(
        notification_queue,
        "send",
        lambda message, *, level, alert_id=None: sent.append((message, level)) or True,
    )

    notif.notify_alert("MT5 reconnected after a drop")
    notif.notify_critical("placement paused")

    assert sent[0][0].startswith("[F5 $10 TEST - FTMO] \u26A0\uFE0F SYSTEM ALERT\n")
    assert sent[1][0].startswith("[F5 $10 TEST - FTMO] \U0001F6A8 CRITICAL\n")
    assert sent[0][1] is notification_queue.Level.HIGH
    assert sent[1][1] is notification_queue.Level.CRITICAL


def test_notify_alert_fallback_preserves_optional_operator_label(monkeypatch):
    """A queue failure must not strip the F5 label from the fire-and-forget fallback."""
    import src.notifications as notif

    fallback = []
    monkeypatch.setenv("GTOS_ALERT_LABEL", "F5 $10 TEST - FTMO")
    monkeypatch.setattr(
        notification_queue,
        "send",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("queue offline")),
    )
    monkeypatch.setattr(notif, "_send_async", lambda message: fallback.append(message))

    notif.notify_alert("MT5 connection lost")

    assert fallback == [
        "[F5 $10 TEST - FTMO] \u26A0\uFE0F SYSTEM ALERT\nMT5 connection lost"
    ]


def test_notify_critical_without_operator_label_preserves_production_format(monkeypatch):
    """With no process label, armed-book critical formatting stays byte-identical."""
    import src.notifications as notif

    sent = []
    monkeypatch.delenv("GTOS_ALERT_LABEL", raising=False)
    monkeypatch.setattr(
        notification_queue,
        "send",
        lambda message, *, level, alert_id=None: sent.append((message, level)) or True,
    )

    notif.notify_critical("placement paused")

    assert sent == [("\U0001F6A8 CRITICAL\nplacement paused", notification_queue.Level.CRITICAL)]


# ---------------------------------------------------------------------------
# 15. CLI: --drain-once + worker dispatcher (2026-04-28)
# ---------------------------------------------------------------------------


def test_cli_drain_once_processes_pending_rows(tmp_path):
    """``--drain-once`` flushes rows that the lazy daemon never drained.

    Reproduces the 2026-04-28 00:02 UTC live failure: cron-script enqueued
    HIGH alerts sit on disk with retry_count=0 because no long-lived
    process is running the daemon poller. Operator runs ``--drain-once``
    to deliver them.
    """
    qpath = tmp_path / "queue.jsonl"
    rows = [
        {
            "alert_id": "stuck-aaa",
            "level": "HIGH",
            "message": "stuck alert A",
            "ts_utc": "2026-04-28T00:02:28+00:00",
            "retry_count": 0,
            "last_attempt_utc": None,
        },
        {
            "alert_id": "stuck-bbb",
            "level": "HIGH",
            "message": "stuck alert B",
            "ts_utc": "2026-04-28T00:02:28+00:00",
            "retry_count": 0,
            "last_attempt_utc": None,
        },
    ]
    qpath.parent.mkdir(parents=True, exist_ok=True)
    with qpath.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    sent = []
    # Patch the module's default transport so the test doesn't hit Telegram.
    with patch.object(
        notification_queue, "_default_transport",
        lambda msg: sent.append(msg) or True,
    ):
        delivered = notification_queue._drain_once_cli(str(qpath))

    assert delivered == 2
    assert set(sent) == {"stuck alert A", "stuck alert B"}

    final_rows = _read_jsonl(qpath)
    delivered_ids = {
        r["alert_id"] for r in final_rows if r.get("marker") == "DELIVERED"
    }
    assert delivered_ids == {"stuck-aaa", "stuck-bbb"}


def test_cli_main_dispatcher_routes_drain_once(
    tmp_path, monkeypatch, operator_delivery_grant
):
    """``main(['--drain-once', '--queue-path', P])`` returns 0 on success.

    Requests ``operator_delivery_grant`` because ``main()`` authorizes the
    process for operator delivery — correct behaviour for the CLI that
    ``scripts/watchdog.ps1`` runs as the live drain worker (F30 / Q7). The
    fixture restores the grant state afterwards so it does not leak into later
    tests.
    """
    monkeypatch.chdir(tmp_path)
    qpath = tmp_path / "queue.jsonl"
    qpath.write_text(
        json.dumps({
            "alert_id": "main-cli-x",
            "level": "HIGH",
            "message": "drain via main",
            "ts_utc": "2026-04-28T00:00:00+00:00",
            "retry_count": 0,
            "last_attempt_utc": None,
        }) + "\n",
        encoding="utf-8",
    )
    sent = []
    with patch.object(
        notification_queue, "_default_transport",
        lambda m: sent.append(m) or True,
    ):
        rc = notification_queue.main([
            "--drain-once", "--queue-path", str(qpath),
        ])
    assert rc == 0
    assert sent == ["drain via main"]


def test_cli_main_dispatcher_requires_mode():
    """argparse mutually-exclusive group rejects calls without a mode."""
    with pytest.raises(SystemExit) as exc:
        notification_queue.main([])
    assert exc.value.code != 0


def test_drain_once_handles_missing_queue(tmp_path):
    """Drain-once on a non-existent queue path returns 0 cleanly."""
    qpath = tmp_path / "doesnotexist.jsonl"
    delivered = notification_queue._drain_once_cli(str(qpath))
    assert delivered == 0


def test_drain_once_respects_existing_markers(tmp_path):
    """Drain-once skips rows already terminal-marked from prior sessions."""
    qpath = tmp_path / "queue.jsonl"
    rows = [
        {"alert_id": "x1", "level": "HIGH", "message": "A",
         "ts_utc": "2026-04-28T00:00:00+00:00", "retry_count": 0,
         "last_attempt_utc": None},
        {"alert_id": "x1", "marker": "DELIVERED"},
        {"alert_id": "x2", "level": "HIGH", "message": "B",
         "ts_utc": "2026-04-28T00:00:00+00:00", "retry_count": 0,
         "last_attempt_utc": None},
    ]
    with qpath.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    sent = []
    with patch.object(
        notification_queue, "_default_transport",
        lambda m: sent.append(m) or True,
    ):
        delivered = notification_queue._drain_once_cli(str(qpath))
    assert delivered == 1
    assert sent == ["B"]
