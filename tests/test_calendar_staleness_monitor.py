"""Tests for the economic-calendar staleness monitor (Issue #15, 2026-04-28).

The monitor is a Telegram alerting wrapper around mtime / ``updated_at``
inspection. It does NOT auto-fetch — calendar is operator-maintained per
CLAUDE.md (no API call that costs money or requires sign-up). The monitor
fires Telegram once-per-day max (cooldown) when either ``data/news_calendar.json``
or ``data/economic_calendar.csv`` is older than ``STALENESS_THRESHOLD_DAYS``
(default 7d).

Tests use ``tmp_path`` exclusively + module-ref monkeypatch (canon).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# Load the script as a module (not on sys.path under a clean install).
_HERE = Path(__file__).resolve().parent
_SCRIPT_PATH = _HERE.parent / "scripts" / "refresh_economic_calendar.py"
_spec = importlib.util.spec_from_file_location(
    "refresh_economic_calendar", _SCRIPT_PATH
)
ces = importlib.util.module_from_spec(_spec)
sys.modules["refresh_economic_calendar"] = ces
_spec.loader.exec_module(ces)


# ---------------------------------------------------------------------------
# 1 — _file_age_days: prefers JSON updated_at over mtime
# ---------------------------------------------------------------------------


class TestFileAgeDays:
    def test_returns_none_for_missing_file(self, tmp_path):
        age = ces._file_age_days(tmp_path / "ghost.json")
        assert age is None

    def test_json_uses_updated_at_field_over_mtime(self, tmp_path):
        """An operator who ``touch``-es the file must NOT silence the
        monitor — the embedded ``updated_at`` is the source of truth."""
        path = tmp_path / "news_calendar.json"
        # File was "actually" updated 30 days ago
        old_dt = datetime(2026, 3, 29, 12, 0, 0, tzinfo=timezone.utc)
        path.write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        # But mtime is fresh
        now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
        age = ces._file_age_days(path, now=now)
        # Must report ~30d based on updated_at, NOT 0
        assert age is not None and 29.0 < age < 31.0, (
            f"Expected age ~30d from updated_at; got {age}"
        )

    def test_json_falls_back_to_mtime_without_updated_at(self, tmp_path):
        path = tmp_path / "news_calendar.json"
        path.write_text(json.dumps({"events": []}), encoding="utf-8")
        # Stamp mtime 10 days ago
        old = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
        os.utime(path, (old, old))
        age = ces._file_age_days(path)
        assert age is not None and 9.0 < age < 11.0

    def test_csv_uses_mtime(self, tmp_path):
        path = tmp_path / "economic_calendar.csv"
        path.write_text("date,time_utc,event,impact,currency\n", encoding="utf-8")
        old = (datetime.now(timezone.utc) - timedelta(days=15)).timestamp()
        os.utime(path, (old, old))
        age = ces._file_age_days(path)
        assert age is not None and 14.0 < age < 16.0


# ---------------------------------------------------------------------------
# 2 — collect_stale_files
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_paths(tmp_path, monkeypatch):
    """Redirect both calendar paths under tmp_path."""
    json_path = tmp_path / "news_calendar.json"
    csv_path = tmp_path / "economic_calendar.csv"
    state_path = tmp_path / "calendar_staleness_state.json"
    monkeypatch.setattr(ces, "JSON_CALENDAR_PATH", json_path)
    monkeypatch.setattr(ces, "CSV_CALENDAR_PATH", csv_path)
    monkeypatch.setattr(ces, "STATE_FILE", state_path)
    return {"json": json_path, "csv": csv_path, "state": state_path}


class TestCollectStaleFiles:
    def test_both_fresh_returns_empty(self, patched_paths):
        # JSON: updated 1 day ago
        recent = datetime.now(timezone.utc) - timedelta(days=1)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": recent.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        # CSV: mtime 1 day ago
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")
        old = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        os.utime(patched_paths["csv"], (old, old))

        stale = ces.collect_stale_files(threshold_days=7)
        assert stale == []

    def test_one_stale_returns_one_entry(self, patched_paths):
        # JSON stale (10d), CSV fresh (1d)
        old_dt = datetime.now(timezone.utc) - timedelta(days=10)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")
        old = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        os.utime(patched_paths["csv"], (old, old))

        stale = ces.collect_stale_files(threshold_days=7)
        assert len(stale) == 1
        assert stale[0]["label"] == "json"

    def test_missing_file_reported_as_stale(self, patched_paths):
        """If JSON is absent entirely (operator deleted it), the monitor
        must surface that — fail-loud rather than silently ignore."""
        # Don't create either file
        stale = ces.collect_stale_files(threshold_days=7)
        labels = sorted(e["label"] for e in stale)
        assert labels == ["csv", "json"]
        for entry in stale:
            assert entry["reason"] == "missing"
            assert entry["age_days"] is None

    def test_both_stale_returns_two_entries(self, patched_paths):
        old_dt = datetime.now(timezone.utc) - timedelta(days=22)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")
        old_epoch = (datetime.now(timezone.utc) - timedelta(days=24)).timestamp()
        os.utime(patched_paths["csv"], (old_epoch, old_epoch))

        stale = ces.collect_stale_files(threshold_days=7)
        assert len(stale) == 2


# ---------------------------------------------------------------------------
# 3 — Cooldown
# ---------------------------------------------------------------------------


class TestCooldown:
    def test_no_state_means_not_in_cooldown(self):
        assert ces._in_cooldown({}) is False

    def test_recent_alert_in_cooldown(self):
        recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert ces._in_cooldown({"last_alert_utc": recent}) is True

    def test_old_alert_not_in_cooldown(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        assert ces._in_cooldown({"last_alert_utc": old}) is False

    def test_malformed_timestamp_not_in_cooldown(self):
        assert ces._in_cooldown({"last_alert_utc": "garbage"}) is False


# ---------------------------------------------------------------------------
# 4 — main() exit codes
# ---------------------------------------------------------------------------


class TestMainExitCodes:
    def test_main_returns_zero_when_fresh(self, patched_paths, monkeypatch):
        # Both fresh
        recent = datetime.now(timezone.utc) - timedelta(days=1)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": recent.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")
        old = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        os.utime(patched_paths["csv"], (old, old))

        rc = ces.main()
        assert rc == 0

    def test_main_returns_one_when_stale_no_telegram_creds(
        self, patched_paths, monkeypatch
    ):
        # Force stale
        old_dt = datetime.now(timezone.utc) - timedelta(days=20)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")
        old = (datetime.now(timezone.utc) - timedelta(days=20)).timestamp()
        os.utime(patched_paths["csv"], (old, old))

        # Strip env so credentials are missing
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

        rc = ces.main()
        assert rc == 1

    def test_main_returns_zero_when_in_cooldown(
        self, patched_paths, monkeypatch
    ):
        # Stale files
        old_dt = datetime.now(timezone.utc) - timedelta(days=20)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")

        # Pre-populate cooldown state
        recent_alert = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        patched_paths["state"].write_text(
            json.dumps({"last_alert_utc": recent_alert}), encoding="utf-8"
        )

        rc = ces.main()
        assert rc == 0

    def test_main_returns_zero_when_alert_enqueued(
        self, patched_paths, monkeypatch
    ):
        """2026-04-29 fix: dispatch goes through ``enqueue_alert`` (which
        wraps ``src.notifications.notify_alert`` → notification queue),
        not direct urllib. Stub at the new entry point."""
        # Stale files
        old_dt = datetime.now(timezone.utc) - timedelta(days=20)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")

        # Creds present (the script gates on env presence before enqueueing).
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake")

        captured = {"text": None}

        def fake_enqueue(text):
            captured["text"] = text
            return True

        monkeypatch.setattr(ces, "enqueue_alert", fake_enqueue)

        rc = ces.main()
        assert rc == 0
        assert captured["text"] is not None
        # Alert text should mention filename + age
        assert "news_calendar.json" in captured["text"]
        assert "STALE" in captured["text"]
        # State file should now hold a fresh last_alert_utc
        state = json.loads(patched_paths["state"].read_text(encoding="utf-8"))
        assert "last_alert_utc" in state

    def test_main_returns_two_when_enqueue_fails(
        self, patched_paths, monkeypatch
    ):
        """If the queue subsystem is unavailable (import error, disk error)
        ``enqueue_alert`` returns False and ``main()`` exits 2 so the
        watchdog retries on the next tick. Importantly the cooldown state
        is NOT persisted on enqueue failure — otherwise a transient queue
        outage would silence the alerter for 24h."""
        # Stale files
        old_dt = datetime.now(timezone.utc) - timedelta(days=20)
        patched_paths["json"].write_text(json.dumps({
            "updated_at": old_dt.isoformat().replace("+00:00", "Z"),
            "events": [],
        }), encoding="utf-8")
        patched_paths["csv"].write_text("a,b\n", encoding="utf-8")

        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake")

        monkeypatch.setattr(ces, "enqueue_alert", lambda _text: False)

        rc = ces.main()
        assert rc == 2
        # State must NOT be written — next tick should retry, not be silenced.
        assert not patched_paths["state"].exists()


# ---------------------------------------------------------------------------
# 5 — Alert message structure
# ---------------------------------------------------------------------------


class TestBuildAlertMessage:
    def test_message_includes_filename_and_age(self):
        stale = [{
            "label": "json",
            "path": "/data/news_calendar.json",
            "age_days": 22.5,
            "reason": "age 22.5d > threshold 7d",
        }]
        msg = ces.build_alert_message(stale)
        assert "GTOS" in msg and "STALE" in msg
        assert "news_calendar.json" in msg
        assert "22.5d" in msg

    def test_message_handles_missing_file(self):
        stale = [{
            "label": "json",
            "path": "/data/news_calendar.json",
            "age_days": None,
            "reason": "missing",
        }]
        msg = ces.build_alert_message(stale)
        assert "MISSING" in msg

    def test_message_includes_refresh_procedure(self):
        stale = [{
            "label": "csv",
            "path": "/data/economic_calendar.csv",
            "age_days": 10.0,
            "reason": "age 10.0d > threshold 7d",
        }]
        msg = ces.build_alert_message(stale)
        assert "forexfactory" in msg.lower()


# ---------------------------------------------------------------------------
# 6 — enqueue_alert wrapper (2026-04-29 fix)
# ---------------------------------------------------------------------------


class TestEnqueueAlert:
    """The 2026-04-29 fix swapped direct urllib Telegram dispatch for a
    wrapper around ``src.notifications.notify_alert`` so the alert goes
    through the persistent notification queue (HIGH priority). The queue's
    transport is the only path that bypasses the host's self-signed-cert
    SSL chain issue and persists the message across process exit.

    These tests verify the wrapper's contract:
    - Returns True iff the underlying call succeeds
    - Returns False (does NOT raise) on import errors, transport errors
    - Forwards the text unchanged to ``notify_alert``
    """

    def test_returns_true_on_successful_notify(self, monkeypatch):
        captured = {"text": None}

        def fake_notify_alert(text):
            captured["text"] = text

        # Inject a stub ``src.notifications`` module so the lazy import
        # inside ``enqueue_alert`` finds our stub instead of the real one.
        import types
        fake_module = types.ModuleType("src.notifications")
        fake_module.notify_alert = fake_notify_alert
        monkeypatch.setitem(sys.modules, "src.notifications", fake_module)

        ok = ces.enqueue_alert("STALE test alert")
        assert ok is True
        assert captured["text"] == "STALE test alert"

    def test_returns_false_when_import_fails(self, monkeypatch):
        # Force the lazy import to fail. The cleanest way: install an
        # importable shim that raises on attribute access.
        import types
        broken = types.ModuleType("src.notifications")
        # Don't set notify_alert — AttributeError on import-time `from … import`.
        monkeypatch.setitem(sys.modules, "src.notifications", broken)

        ok = ces.enqueue_alert("ignored")
        # Either the import bottoms out with ImportError or attribute lookup
        # fails; in either case enqueue_alert must return False, never raise.
        assert ok is False

    def test_returns_false_when_notify_alert_raises(self, monkeypatch):
        import types

        def fake_notify_alert(_text):
            raise RuntimeError("queue subsystem on fire")

        fake_module = types.ModuleType("src.notifications")
        fake_module.notify_alert = fake_notify_alert
        monkeypatch.setitem(sys.modules, "src.notifications", fake_module)

        ok = ces.enqueue_alert("ignored")
        assert ok is False
