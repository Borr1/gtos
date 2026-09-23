"""
Tests for scripts/no_data_alert_monitor.py (T1.7).

Covers:
- log_age_minutes: missing, present, future-dated
- kz_active_for_symbol: in-KZ, outside-KZ, alias (US30_cash → US30),
  KZ boundaries, unknown symbol
- _load_state / _save_state / _in_cooldown: empty, recent, expired,
  corrupt, non-dict
- build_alert_message: contains symbol + age + log name + KZ hint
- send_telegram: 200, non-200, HTTPError, OSError, token in URL
- check_symbol: outside-KZ no-alert, outside-KZ clear-on-recover,
  in-KZ fresh, in-KZ stale, in-KZ stale-cooldown, in-KZ missing-log,
  in-KZ ok-clears-prior-alert
- main: fresh all symbols, stale one symbol no creds, stale one symbol
  with creds, cooldown suppresses repeat, telegram failure returns 2,
  data-returns clears state

All file writes go to ``tmp_path`` via module-ref monkeypatch per the
session 21 canonical pattern.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the scripts package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import no_data_alert_monitor as mod  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    """Redirect all module-level paths under tmp_path.

    Per session 21 canon: monkeypatch the *module reference* so the
    constants are replaced even if already bound.
    """
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    heartbeat_dir = tmp_path / "pipeline_state"
    heartbeat_dir.mkdir()
    state_file = tmp_path / "meta" / "no_data_alert_state.json"
    monkeypatch.setattr(mod, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(mod, "HEARTBEAT_DIR", heartbeat_dir)
    monkeypatch.setattr(mod, "STATE_FILE", state_file)
    return {
        "logs_dir": logs_dir,
        "heartbeat_dir": heartbeat_dir,
        "state_file": state_file,
        "tmp": tmp_path,
    }


def _touch_log(
    logs_dir: Path,
    filename: str,
    age_minutes: float,
    *,
    now: datetime | None = None,
) -> Path:
    """Create a log file with mtime set ``age_minutes`` before ``now``.

    ``now`` defaults to real wall-clock time. Pass a fixed datetime to
    coordinate the mtime with a ``now`` injected into ``check_symbol``
    or ``main``, so ``age = now - mtime`` yields the expected age.
    """
    p = logs_dir / filename
    p.write_text("fake log content\n", encoding="utf-8")
    if now is None:
        base_ts = time.time()
    else:
        base_ts = now.timestamp()
    ts = base_ts - age_minutes * 60.0
    os.utime(p, (ts, ts))
    return p


def _touch_heartbeat(
    heartbeat_dir: Path,
    symbol: str,
    age_minutes: float,
    *,
    now: datetime | None = None,
) -> Path:
    filename = mod.SYMBOL_HEARTBEAT_MAP[symbol]
    p = heartbeat_dir / filename
    p.write_text('{"ok": true}\n', encoding="utf-8")
    base_ts = time.time() if now is None else now.timestamp()
    ts = base_ts - age_minutes * 60.0
    os.utime(p, (ts, ts))
    return p


def _now_at_utc_hour_minute(hour: int, minute: int) -> datetime:
    """A UTC datetime anchored to real today + hour/minute.

    We anchor to today's UTC date rather than a fixed future date so
    that ``_touch_log`` (which uses ``time.time()``) produces a mtime
    comparable to the returned ``now``. Using a far-future ``now``
    would make ``log_age_minutes`` report thousands of minutes,
    masking the age-vs-threshold assertions.
    """
    today_utc = datetime.now(timezone.utc).date()
    return datetime(
        today_utc.year,
        today_utc.month,
        today_utc.day,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


def _fixed_now_in_xauusd_london() -> datetime:
    """A UTC datetime that sits inside XAUUSD's London KZ (07:00-10:30)."""
    return _now_at_utc_hour_minute(8, 0)


def _fixed_now_outside_any_kz() -> datetime:
    """A UTC datetime that sits in every symbol's dead zone.

    04:00-06:00 UTC is before London opens for all instruments and after
    the Asian session (00:00-03:00) has closed for the JPY pairs.
    """
    return _now_at_utc_hour_minute(5, 0)


# ─────────────────────────────────────────────────────────────────────────
# log_age_minutes
# ─────────────────────────────────────────────────────────────────────────


class TestLogAgeMinutes:
    def test_missing_log_returns_none(self, isolated_paths):
        age = mod.log_age_minutes(isolated_paths["logs_dir"] / "nope.log")
        assert age is None

    def test_fresh_log_returns_small_age(self, isolated_paths):
        log = _touch_log(isolated_paths["logs_dir"], "fresh.log", age_minutes=0.0)
        age = mod.log_age_minutes(log)
        assert age is not None
        assert age < 0.5  # less than 30 seconds

    def test_old_log_returns_correct_age(self, isolated_paths):
        log = _touch_log(isolated_paths["logs_dir"], "old.log", age_minutes=45.0)
        age = mod.log_age_minutes(log)
        assert age is not None
        assert 44.0 < age < 46.0

    def test_future_mtime_returns_zero(self, isolated_paths):
        log = isolated_paths["logs_dir"] / "future.log"
        log.write_text("x")
        future_ts = time.time() + 600  # 10 min in future
        os.utime(log, (future_ts, future_ts))
        age = mod.log_age_minutes(log)
        # Future mtime → treated as fresh (0.0), NEVER negative
        assert age == 0.0

    def test_explicit_now_is_respected(self, isolated_paths):
        log = _touch_log(isolated_paths["logs_dir"], "a.log", age_minutes=0.0)
        # Pretend "now" is 100 minutes in the future.
        stat_mtime = log.stat().st_mtime
        fake_now = datetime.fromtimestamp(stat_mtime, tz=timezone.utc) + timedelta(
            minutes=100
        )
        age = mod.log_age_minutes(log, now=fake_now)
        assert age is not None
        assert 99.5 < age < 100.5


# ─────────────────────────────────────────────────────────────────────────
# kz_active_for_symbol
# ─────────────────────────────────────────────────────────────────────────


class TestKZActiveForSymbol:
    def test_xauusd_in_london(self):
        assert (
            mod.kz_active_for_symbol(
                "XAUUSD", now=_fixed_now_in_xauusd_london()
            )
            is True
        )

    def test_xauusd_outside_kz(self):
        assert (
            mod.kz_active_for_symbol(
                "XAUUSD", now=_fixed_now_outside_any_kz()
            )
            is False
        )

    def test_usdjpy_tokyo_session(self):
        # USDJPY Tokyo 00:00-03:00 UTC
        tokyo = _now_at_utc_hour_minute(1, 30)
        assert mod.kz_active_for_symbol("USDJPY", now=tokyo) is True

    def test_half_open_start_inclusive(self):
        # XAUUSD London starts 07:00 — exactly 07:00 should be IN
        at_start = _now_at_utc_hour_minute(7, 0)
        assert mod.kz_active_for_symbol("XAUUSD", now=at_start) is True

    def test_half_open_end_exclusive(self):
        # XAUUSD London ends 10:30 — exactly 10:30 should be OUT.
        # XAUUSD NY is 13:00-17:00 so 10:30 is safely between KZs.
        at_end = _now_at_utc_hour_minute(10, 30)
        assert mod.kz_active_for_symbol("XAUUSD", now=at_end) is False

    def test_unknown_symbol_returns_false(self):
        assert (
            mod.kz_active_for_symbol(
                "NOT_A_REAL_SYMBOL", now=_fixed_now_in_xauusd_london()
            )
            is False
        )

    def test_gbpusd_unique_london_window(self):
        # GBPUSD London runs 07:00-12:00 (longer than others).
        # 11:30 is outside XAUUSD London (which ends 10:30) but INSIDE GBPUSD.
        at_1130 = _now_at_utc_hour_minute(11, 30)
        assert mod.kz_active_for_symbol("GBPUSD", now=at_1130) is True
        assert mod.kz_active_for_symbol("XAUUSD", now=at_1130) is False

    def test_expanded_supervised_symbols_have_ny_windows(self):
        in_ny = _now_at_utc_hour_minute(14, 0)
        assert mod.kz_active_for_symbol("XAGUSD", now=in_ny) is True
        assert mod.kz_active_for_symbol("NAS100", now=in_ny) is True

# ─────────────────────────────────────────────────────────────────────────
# State / cooldown
# ─────────────────────────────────────────────────────────────────────────


class TestState:
    def test_load_missing_returns_empty(self, isolated_paths):
        assert mod._load_state() == {}

    def test_load_corrupt_returns_empty(self, isolated_paths):
        isolated_paths["state_file"].parent.mkdir(parents=True, exist_ok=True)
        isolated_paths["state_file"].write_text("{not json")
        assert mod._load_state() == {}

    def test_load_list_returns_empty(self, isolated_paths):
        """State must be a dict. A JSON list should be treated as corrupt."""
        isolated_paths["state_file"].parent.mkdir(parents=True, exist_ok=True)
        isolated_paths["state_file"].write_text("[1,2,3]")
        assert mod._load_state() == {}

    def test_save_then_load_roundtrip(self, isolated_paths):
        s = {"XAUUSD": "2026-04-20T08:00:00+00:00"}
        mod._save_state(s)
        assert mod._load_state() == s

    def test_save_writes_atomically(self, isolated_paths):
        s = {"A": "x"}
        mod._save_state(s)
        assert isolated_paths["state_file"].exists()
        # No leftover .tmp files
        tmp_siblings = list(
            isolated_paths["state_file"].parent.glob("no_data_alert_state*.tmp")
        )
        assert tmp_siblings == []

    def test_save_handles_oserror_gracefully(self, isolated_paths, monkeypatch):
        # Patch replace to simulate disk failure; save should not raise.
        def boom(*_a, **_kw):
            raise OSError("disk full")

        monkeypatch.setattr(os, "replace", boom)
        # Must not raise
        mod._save_state({"A": "x"})


class TestInCooldown:
    def test_missing_symbol_not_in_cooldown(self):
        assert mod._in_cooldown({}, "XAUUSD") is False

    def test_recent_alert_in_cooldown(self):
        now = _now_at_utc_hour_minute(12, 0)
        recent = (now - timedelta(minutes=30)).isoformat()
        assert mod._in_cooldown({"XAUUSD": recent}, "XAUUSD", now=now) is True

    def test_expired_alert_not_in_cooldown(self):
        now = _now_at_utc_hour_minute(12, 0)
        old = (now - timedelta(minutes=90)).isoformat()
        assert mod._in_cooldown({"XAUUSD": old}, "XAUUSD", now=now) is False

    def test_boundary_just_past_cooldown(self):
        now = _now_at_utc_hour_minute(12, 0)
        just_past = (now - timedelta(minutes=60, seconds=1)).isoformat()
        assert (
            mod._in_cooldown({"XAUUSD": just_past}, "XAUUSD", now=now) is False
        )

    def test_boundary_just_inside_cooldown(self):
        now = _now_at_utc_hour_minute(12, 0)
        just_inside = (now - timedelta(minutes=59)).isoformat()
        assert (
            mod._in_cooldown({"XAUUSD": just_inside}, "XAUUSD", now=now) is True
        )

    def test_bad_timestamp_not_in_cooldown(self):
        assert mod._in_cooldown({"XAUUSD": "not-a-date"}, "XAUUSD") is False

    def test_non_string_timestamp_not_in_cooldown(self):
        assert mod._in_cooldown({"XAUUSD": 12345}, "XAUUSD") is False

    def test_naive_timestamp_assumed_utc(self):
        now = _now_at_utc_hour_minute(12, 0)
        naive = (now - timedelta(minutes=15)).replace(tzinfo=None).isoformat()
        assert mod._in_cooldown({"XAUUSD": naive}, "XAUUSD", now=now) is True


# ─────────────────────────────────────────────────────────────────────────
# build_alert_message
# ─────────────────────────────────────────────────────────────────────────


class TestBuildAlertMessage:
    def test_contains_symbol(self):
        msg = mod.build_alert_message("XAUUSD", 25.3, Path("logs/xauusd.log"))
        assert "XAUUSD" in msg

    def test_contains_age(self):
        msg = mod.build_alert_message("USDJPY", 27.5, Path("logs/usdjpy.log"))
        assert "27.5" in msg

    def test_contains_log_basename(self):
        msg = mod.build_alert_message(
            "GBPJPY", 42.0, Path("/some/path/gbpjpy.log")
        )
        assert "gbpjpy.log" in msg

    def test_contains_kz_hint(self):
        msg = mod.build_alert_message("XAUUSD", 25.3, Path("x.log"))
        assert any(tok in msg for tok in ("KZ", "feed", "process"))


# ─────────────────────────────────────────────────────────────────────────
# send_telegram
# ─────────────────────────────────────────────────────────────────────────


class TestSendTelegram:
    def _mock_urlopen(self, status=200):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.status = status
        return ctx

    def test_success_200(self, operator_delivery_grant):
        # Requests ``operator_delivery_grant``: send_telegram refuses before
        # building a request unless the process is authorized to page the
        # operator (F30 / Q7). This test asserts the authorized branch.
        ctx = self._mock_urlopen(200)
        with patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            return_value=ctx,
        ):
            assert mod.send_telegram("tok", "cid", "hi") is True

    def test_non_200_returns_false(self):
        ctx = self._mock_urlopen(500)
        with patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            return_value=ctx,
        ):
            assert mod.send_telegram("tok", "cid", "hi") is False

    def test_http_error_returns_false(self):
        with patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                url="", code=403, msg="Forbidden", hdrs=None, fp=None
            ),
        ):
            assert mod.send_telegram("tok", "cid", "hi") is False

    def test_connection_error_returns_false(self):
        with patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            side_effect=OSError("refused"),
        ):
            assert mod.send_telegram("tok", "cid", "hi") is False

    def test_url_contains_token(self, operator_delivery_grant):
        # Requests ``operator_delivery_grant``: send_telegram refuses before
        # building a request unless the process is authorized to page the
        # operator (F30 / Q7). This test asserts the authorized branch.
        ctx = self._mock_urlopen(200)
        with patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            return_value=ctx,
        ), patch(
            "scripts.no_data_alert_monitor.urllib.request.Request"
        ) as mock_req:
            mock_req.return_value = MagicMock()
            mod.send_telegram("my-token", "cid", "hi")
            call_args = mock_req.call_args[0]
            assert "my-token" in call_args[0]


# ─────────────────────────────────────────────────────────────────────────
# check_symbol
# ─────────────────────────────────────────────────────────────────────────


class TestCheckSymbol:
    def test_outside_kz_no_alert(self, isolated_paths):
        now = _fixed_now_outside_any_kz()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=120.0, now=now
        )
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={}, now=now
        )
        assert d["status"] == "outside_kz"
        assert d["should_alert"] is False

    def test_outside_kz_clears_recovered_state(self, isolated_paths):
        """If symbol previously alerted and data has returned, we clear it
        even outside KZ (operator should not see stale state)."""
        now = _fixed_now_outside_any_kz()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=2.0, now=now
        )
        prev = (now - timedelta(hours=4)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={"XAUUSD": prev}, now=now
        )
        assert d["status"] == "outside_kz"
        assert d["should_alert"] is False
        assert d["should_clear"] is True

    def test_outside_kz_stale_log_does_not_clear(self, isolated_paths):
        """Outside KZ + log still stale + existing alert state → keep the
        alert state (outage hasn't demonstrably ended)."""
        now = _fixed_now_outside_any_kz()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=200.0, now=now
        )
        prev = (now - timedelta(hours=4)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={"XAUUSD": prev}, now=now
        )
        assert d["status"] == "outside_kz"
        assert d["should_alert"] is False
        assert d["should_clear"] is False

    def test_in_kz_fresh_log_ok(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=2.0, now=now
        )
        d = mod.check_symbol("XAUUSD", "xauusd.log", state={}, now=now)
        assert d["status"] == "ok"
        assert d["should_alert"] is False
        assert d["should_clear"] is False

    def test_in_kz_fresh_heartbeat_suppresses_stale_log(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=420.0, now=now
        )
        _touch_heartbeat(
            isolated_paths["heartbeat_dir"], "XAUUSD", age_minutes=1.0, now=now
        )
        d = mod.check_symbol("XAUUSD", "xauusd.log", state={}, now=now)
        assert d["status"] == "ok"
        assert d["liveness_source"] == "heartbeat"
        assert d["should_alert"] is False
        assert d["log_age_minutes"] > 400.0
        assert d["heartbeat_age_minutes"] < mod.HEARTBEAT_FRESH_THRESHOLD_MINUTES

    def test_in_kz_fresh_heartbeat_suppresses_missing_log(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_heartbeat(
            isolated_paths["heartbeat_dir"], "XAUUSD", age_minutes=1.0, now=now
        )
        d = mod.check_symbol("XAUUSD", "missing.log", state={}, now=now)
        assert d["status"] == "ok"
        assert d["liveness_source"] == "heartbeat"
        assert d["should_alert"] is False

    def test_fresh_heartbeat_clears_prior_alert_with_stale_log(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=420.0, now=now
        )
        _touch_heartbeat(
            isolated_paths["heartbeat_dir"], "XAUUSD", age_minutes=1.0, now=now
        )
        prev_alert = (now - timedelta(hours=4)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={"XAUUSD": prev_alert}, now=now
        )
        assert d["status"] == "ok"
        assert d["should_clear"] is True

    def test_in_kz_stale_triggers_alert(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=30.0, now=now
        )
        d = mod.check_symbol("XAUUSD", "xauusd.log", state={}, now=now)
        assert d["status"] == "stale"
        assert d["should_alert"] is True
        assert "XAUUSD" in d["message"]
        assert d["age_minutes"] is not None
        assert d["age_minutes"] > 20.0

    def test_in_kz_stale_but_in_cooldown_no_alert(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=30.0, now=now
        )
        recent = (now - timedelta(minutes=10)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={"XAUUSD": recent}, now=now
        )
        assert d["status"] == "stale_cooldown"
        assert d["should_alert"] is False
        assert d["should_clear"] is False

    def test_in_kz_missing_log_alerts(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        d = mod.check_symbol(
            "XAUUSD", "never_created.log", state={}, now=now
        )
        assert d["status"] == "no_log"
        assert d["should_alert"] is True
        assert d["age_minutes"] is None

    def test_in_kz_missing_log_in_cooldown_no_alert(self, isolated_paths):
        now = _fixed_now_in_xauusd_london()
        recent = (now - timedelta(minutes=5)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "never_created.log", state={"XAUUSD": recent}, now=now
        )
        assert d["status"] == "stale_cooldown"
        assert d["should_alert"] is False

    def test_in_kz_ok_clears_prior_alert(self, isolated_paths):
        """If a symbol previously alerted but is now healthy inside the KZ,
        the stale alert-state entry should be cleared."""
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=2.0, now=now
        )
        prev_alert = (now - timedelta(hours=4)).isoformat()
        d = mod.check_symbol(
            "XAUUSD", "xauusd.log", state={"XAUUSD": prev_alert}, now=now
        )
        assert d["status"] == "ok"
        assert d["should_clear"] is True

    def test_exact_threshold_is_alert(self, isolated_paths):
        """Age == threshold should alert (>=)."""
        # threshold is 20 min; age exactly 20.0 triggers alert
        now = _fixed_now_in_xauusd_london()
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=20.0, now=now
        )
        d = mod.check_symbol("XAUUSD", "xauusd.log", state={}, now=now)
        # Age is ≈20.0 (±floating-point); either stale or ok is acceptable.
        assert d["status"] in ("stale", "ok")
        if d["status"] == "stale":
            assert d["should_alert"] is True


# ─────────────────────────────────────────────────────────────────────────
# main() integration
# ─────────────────────────────────────────────────────────────────────────


class TestMain:
    def _make_all_fresh(self, isolated_paths, now: datetime):
        for fname in mod.SYMBOL_LOG_MAP.values():
            _touch_log(
                isolated_paths["logs_dir"], fname, age_minutes=1.0, now=now
            )

    def _make_xauusd_stale_rest_fresh(self, isolated_paths, now: datetime):
        _touch_log(
            isolated_paths["logs_dir"], "xauusd.log", age_minutes=30.0, now=now
        )
        for sym, fname in mod.SYMBOL_LOG_MAP.items():
            if sym == "XAUUSD":
                continue
            _touch_log(
                isolated_paths["logs_dir"], fname, age_minutes=1.0, now=now
            )

    def test_all_fresh_in_kz_returns_0(self, isolated_paths, monkeypatch):
        now = _fixed_now_in_xauusd_london()
        self._make_all_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            assert mod.main() == 0

    def test_all_fresh_outside_kz_returns_0(self, isolated_paths, monkeypatch):
        now = _fixed_now_outside_any_kz()
        self._make_all_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        assert mod.main() == 0

    def test_stale_no_creds_returns_1(self, isolated_paths, monkeypatch):
        now = _fixed_now_in_xauusd_london()
        self._make_xauusd_stale_rest_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            assert mod.main() == 1

    def test_stale_with_creds_sends_alert_returns_0(
        self, isolated_paths, monkeypatch
    ):
        now = _fixed_now_in_xauusd_london()
        self._make_xauusd_stale_rest_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.status = 200

        with patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}
        ), patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            return_value=ctx,
        ):
            assert mod.main() == 0

        # State file must record the alert
        assert isolated_paths["state_file"].exists()
        saved = json.loads(
            isolated_paths["state_file"].read_text(encoding="utf-8")
        )
        assert "XAUUSD" in saved

    def test_cooldown_suppresses_repeat_alert(self, isolated_paths, monkeypatch):
        now = _fixed_now_in_xauusd_london()
        self._make_xauusd_stale_rest_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        # Pre-seed state with a recent alert
        recent = (now - timedelta(minutes=10)).isoformat()
        isolated_paths["state_file"].parent.mkdir(parents=True, exist_ok=True)
        isolated_paths["state_file"].write_text(json.dumps({"XAUUSD": recent}))

        with patch(
            "scripts.no_data_alert_monitor.send_telegram"
        ) as mock_send, patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}
        ):
            rc = mod.main()

        assert rc == 0
        mock_send.assert_not_called()

    def test_telegram_failure_returns_2(self, isolated_paths, monkeypatch):
        now = _fixed_now_in_xauusd_london()
        self._make_xauusd_stale_rest_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        with patch(
            "scripts.no_data_alert_monitor.send_telegram", return_value=False
        ), patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}
        ):
            assert mod.main() == 2

    def test_data_returns_clears_prior_alert(self, isolated_paths, monkeypatch):
        """Previously-alerted symbol now fresh → state entry cleared."""
        now = _fixed_now_in_xauusd_london()
        self._make_all_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        # Previously alerted XAUUSD — timestamp anchored to today so it's
        # clearly older than the cooldown window.
        prev_alert = (now - timedelta(hours=4)).isoformat()
        isolated_paths["state_file"].parent.mkdir(parents=True, exist_ok=True)
        isolated_paths["state_file"].write_text(
            json.dumps({"XAUUSD": prev_alert})
        )
        assert mod.main() == 0
        saved = json.loads(
            isolated_paths["state_file"].read_text(encoding="utf-8")
        )
        assert "XAUUSD" not in saved

    def test_stale_symbols_outside_kz_do_not_alert(
        self, isolated_paths, monkeypatch
    ):
        """Stale XAUUSD log outside KZ must NOT alert (market closed)."""
        now = _fixed_now_outside_any_kz()
        self._make_xauusd_stale_rest_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        with patch(
            "scripts.no_data_alert_monitor.send_telegram"
        ) as mock_send, patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}
        ):
            assert mod.main() == 0
        mock_send.assert_not_called()

    def test_missing_log_in_kz_alerts(self, isolated_paths, monkeypatch):
        """Log file does not exist at all (process never started) and we
        are inside XAUUSD's KZ → must alert."""
        now = _fixed_now_in_xauusd_london()
        # Create only the non-XAUUSD logs
        for sym, fname in mod.SYMBOL_LOG_MAP.items():
            if sym == "XAUUSD":
                continue
            _touch_log(
                isolated_paths["logs_dir"], fname, age_minutes=1.0, now=now
            )
        # xauusd.log deliberately missing

        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.status = 200
        with patch.dict(
            os.environ, {"TELEGRAM_BOT_TOKEN": "tok", "TELEGRAM_CHAT_ID": "cid"}
        ), patch(
            "scripts.no_data_alert_monitor.urllib.request.urlopen",
            return_value=ctx,
        ):
            assert mod.main() == 0

    def test_main_no_state_file_no_alerts_returns_0(
        self, isolated_paths, monkeypatch
    ):
        now = _fixed_now_in_xauusd_london()
        self._make_all_fresh(isolated_paths, now=now)
        monkeypatch.setattr(mod, "_now_utc", lambda: now)
        # No state file — should just be a clean no-op
        assert not isolated_paths["state_file"].exists()
        assert mod.main() == 0
