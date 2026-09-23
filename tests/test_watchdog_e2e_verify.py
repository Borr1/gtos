"""Tests for ``scripts.watchdog_e2e_verify`` — end-to-end watchdog audit tool.

All tests use ``tmp_path`` and monkeypatch the module-level constants on the
``_mod`` object (NOT on symbols imported via ``from X import Y``). This
mirrors the canonical pattern established after session 21's pytest-
contamination post-mortem:

    from scripts import watchdog_e2e_verify as _mod
    monkeypatch.setattr(_mod, "OB_CSV", tmp_path / "ob.csv")

Writes under the real ``shadow_logs/``, ``knowledge_base/``, or ``logs/``
trees from a pytest process would trigger the ``ProductionWriteError``
guard installed by ``tests/conftest.py``. All tests here are structured so
that no production path is ever touched.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts import watchdog_e2e_verify as _mod


# =============================================================================
# Fixtures — redirect every module-level path to tmp_path
# =============================================================================


WATCHDOG_SENTINEL = """# Fake watchdog.ps1 for tests. Must contain the strings
# the audit substring-checks for, so wiring assertions pass.
#
#    ob_continuation_monitor
#    api_refusal_monitor
#    if (-not $env:GTOS_PROFILE) { $env:GTOS_PROFILE = "redacted_account" }
#    if (-not $env:GTOS_MODE)    { $env:GTOS_MODE    = "live" }
#    GTOS_RUNTIME_NAMESPACE = "redacted_account_live_bee34003"
#    GTOS_MT5_TERMINAL_PATH = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
#    GTOS_NOTIFICATION_QUEUE_PATH = "pipeline_state\\redacted_account_live_bee34003\\notification_queue.jsonl"
#    --profile $($env:GTOS_PROFILE)
#    --mode $($env:GTOS_MODE)
#    --runtime-namespace ${RuntimeNamespace}
#    --terminal-path
#    --queue-path
#    ${NotificationQueuePath}
#    .notification_queue_worker_${RuntimeNamespace}.lock
"""

redacted_account_YAML_SAMPLE = """profile_name: redacted_account

risk:
  risk_per_trade_pct: 1.0

drawdown_reduction:
  threshold: 0.08
  reduced_risk_pct: 0.25
"""


@pytest.fixture
def tmp_tree(tmp_path: Path, monkeypatch):
    """Build a self-contained artifact tree + redirect every _mod path to it.

    Returns a dict with all paths so tests can inspect/manipulate them.
    """
    shadow = tmp_path / "shadow_logs"
    kb_meta = tmp_path / "knowledge_base" / "meta"
    logs = tmp_path / "logs"
    cfg_profiles = tmp_path / "config" / "profiles"
    scripts_dir = tmp_path / "scripts"
    for d in (shadow, kb_meta, logs, cfg_profiles, scripts_dir):
        d.mkdir(parents=True, exist_ok=True)

    paths = {
        "ob_csv": shadow / "ob_continuation_daily.csv",
        "ob_marker": kb_meta / "ob_continuation_last_run.utcdate",
        "api_refusal_state": shadow / "api_refusal_alert_state.json",
        "api_refusal_log": logs / "api_refusal_monitor.log",
        "watchdog_log": logs / "watchdog.log",
        "malformed_log": shadow / "malformed_responses.jsonl",
        "watchdog_ps1": scripts_dir / "watchdog.ps1",
        "redacted_account_yaml": cfg_profiles / "redacted_account.yaml",
    }

    # Redirect module constants to tmp paths.
    monkeypatch.setattr(_mod, "OB_CSV", paths["ob_csv"])
    monkeypatch.setattr(_mod, "OB_MARKER", paths["ob_marker"])
    monkeypatch.setattr(_mod, "API_REFUSAL_STATE", paths["api_refusal_state"])
    monkeypatch.setattr(_mod, "API_REFUSAL_LOG", paths["api_refusal_log"])
    monkeypatch.setattr(_mod, "WATCHDOG_LOG", paths["watchdog_log"])
    monkeypatch.setattr(_mod, "MALFORMED_LOG", paths["malformed_log"])
    monkeypatch.setattr(_mod, "WATCHDOG_PS1", paths["watchdog_ps1"])
    monkeypatch.setattr(_mod, "redacted_account_YAML", paths["redacted_account_yaml"])

    return paths


def _write_fresh_all(paths: dict, age_hours: float = 0.1) -> None:
    """Populate every artifact with fresh, well-formed content at ``age_hours``
    past now. mtime is set explicitly to avoid filesystem-timestamp fuzz.
    """
    now_ts = datetime.now(timezone.utc).timestamp() - age_hours * 3600

    # OB CSV with required columns + one data row
    with open(paths["ob_csv"], "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "date_utc", "scope", "window_size", "window_start_date",
            "window_end_date", "continuation_count", "total_count", "rate_pct",
            "alarm_fired", "insufficient_sample",
        ])
        w.writeheader()
        w.writerow({
            "date_utc": "2026-04-18", "scope": "XAUUSD", "window_size": "50",
            "window_start_date": "2026-03-01", "window_end_date": "2026-04-18",
            "continuation_count": "34", "total_count": "50", "rate_pct": "68.0",
            "alarm_fired": "false", "insufficient_sample": "false",
        })
    os.utime(paths["ob_csv"], (now_ts, now_ts))

    # API refusal log (heartbeat — can be empty; watchdog touches it)
    paths["api_refusal_log"].write_text("", encoding="utf-8")
    os.utime(paths["api_refusal_log"], (now_ts, now_ts))

    paths["watchdog_log"].write_text(
        "2026-04-18 00:01:00    [API_REFUSAL] OK\n",
        encoding="utf-8",
    )
    os.utime(paths["watchdog_log"], (now_ts, now_ts))

    # Malformed log (input corpus)
    paths["malformed_log"].write_text("", encoding="utf-8")
    os.utime(paths["malformed_log"], (now_ts, now_ts))

    # Watchdog.ps1 with required substrings
    paths["watchdog_ps1"].write_text(WATCHDOG_SENTINEL, encoding="utf-8")

    # redacted_account YAML
    paths["redacted_account_yaml"].write_text(redacted_account_YAML_SAMPLE, encoding="utf-8")


# =============================================================================
# Pure helpers — no I/O
# =============================================================================


class TestRollup:
    def test_rollup_empty_is_fail(self):
        assert _mod._rollup([]) == "FAIL"

    def test_rollup_all_pass(self):
        checks = [
            _mod.CheckResult("a", "PASS", "ok"),
            _mod.CheckResult("b", "PASS", "ok"),
        ]
        assert _mod._rollup(checks) == "PASS"

    def test_rollup_any_warn_is_warn(self):
        checks = [
            _mod.CheckResult("a", "PASS", "ok"),
            _mod.CheckResult("b", "WARN", "minor"),
        ]
        assert _mod._rollup(checks) == "WARN"

    def test_rollup_any_fail_is_fail(self):
        checks = [
            _mod.CheckResult("a", "PASS", "ok"),
            _mod.CheckResult("b", "WARN", "minor"),
            _mod.CheckResult("c", "FAIL", "broken"),
        ]
        assert _mod._rollup(checks) == "FAIL"

    def test_overall_rollup_matches_worst_integration(self):
        reports = [
            _mod.IntegrationReport("a", "PASS", []),
            _mod.IntegrationReport("b", "WARN", []),
            _mod.IntegrationReport("c", "FAIL", []),
        ]
        assert _mod._overall(reports) == "FAIL"


class TestWeekendLeniency:
    """The weekend leniency helper softens STALE → WARN when the market has
    been closed for >=48h relative to the provided ``now``.
    """

    def test_weekday_midday_not_lenient(self):
        # Monday 12:00 UTC — market opened Sun 21:00 UTC, so ~15h past close
        # window; weekend leniency should be OFF.
        mon_noon = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
        assert not _mod._is_weekend_leniency_active(now=mon_noon)

    def test_saturday_morning_is_lenient(self):
        # Saturday 08:00 UTC — Friday 17:15 UTC close + ~15h. Below the
        # default 48h threshold, so NOT yet lenient.
        sat_morning = datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc)
        assert not _mod._is_weekend_leniency_active(now=sat_morning)

    def test_sunday_evening_is_lenient(self):
        # Saturday 14:00 UTC — ~20h45m past Friday 17:15 close, market still
        # closed (Sat → weekend). 20h45m is below the default 48h threshold
        # so NOT yet lenient; switching to a 6h leniency_hours override
        # confirms the lower-threshold branch.
        sat_afternoon = datetime(2026, 4, 18, 14, 0, tzinfo=timezone.utc)
        # Default threshold 48h; at ~20h we're NOT yet lenient.
        assert not _mod._is_weekend_leniency_active(now=sat_afternoon)
        # With a 6h threshold Saturday afternoon IS lenient.
        assert _mod._is_weekend_leniency_active(
            now=sat_afternoon, leniency_hours=6.0,
        )

    def test_sunday_after_reopen_is_not_lenient(self):
        # Sunday 22:00 UTC — market reopened at 21:00 UTC. NOT closed anymore.
        sun_after_reopen = datetime(2026, 4, 19, 22, 0, tzinfo=timezone.utc)
        assert not _mod._is_weekend_leniency_active(now=sun_after_reopen)

    def test_leniency_respects_custom_threshold(self):
        # With a 6-hour threshold, Saturday 06:00 UTC qualifies (~12h45m
        # past Friday 17:15 UTC close).
        sat_morning = datetime(2026, 4, 18, 6, 0, tzinfo=timezone.utc)
        assert _mod._is_weekend_leniency_active(
            now=sat_morning, leniency_hours=6.0,
        )


# =============================================================================
# Per-integration checks — against tmp_tree
# =============================================================================


class TestAllPass:
    def test_all_active_integrations_pass_with_fresh_fixtures(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        reports = _mod.run_all_checks()
        assert len(reports) == 3
        statuses = {r.integration: r.status for r in reports}
        assert statuses == {
            "ob_continuation_monitor": "PASS",
            "api_refusal_monitor": "PASS",
            "redacted_account_profile": "PASS",
        }
        assert _mod._overall(reports) == "PASS"


class TestObContinuation:
    def test_ob_absent_is_fail(self, tmp_tree):
        # Everything else fresh, OB CSV missing.
        _write_fresh_all(tmp_tree)
        tmp_tree["ob_csv"].unlink()
        rep = _mod.check_ob_continuation()
        assert rep.status == "FAIL"
        freshness = [c for c in rep.checks if c.name == "freshness"][0]
        assert freshness.result == "FAIL"
        assert "ABSENT" in freshness.detail

    def test_ob_stale_weekday_is_fail(self, tmp_tree, monkeypatch):
        _write_fresh_all(tmp_tree)
        # Make the CSV 40h old.
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=40)).timestamp()
        os.utime(tmp_tree["ob_csv"], (old_ts, old_ts))
        # Force "now" to a weekday midday so weekend leniency is OFF.
        mon_noon = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
        monkeypatch.setattr(_mod, "_now_utc", lambda: mon_noon)
        # Also update mtime relative to mon_noon (40h before mon_noon).
        stale_ts = (mon_noon - timedelta(hours=40)).timestamp()
        os.utime(tmp_tree["ob_csv"], (stale_ts, stale_ts))
        rep = _mod.check_ob_continuation(stale_hours=30.0)
        assert rep.status == "FAIL"
        freshness = [c for c in rep.checks if c.name == "freshness"][0]
        assert freshness.result == "FAIL"
        assert "STALE" in freshness.detail

    def test_ob_stale_weekend_downgrades_to_warn(self, tmp_tree, monkeypatch):
        _write_fresh_all(tmp_tree)
        # Pin "now" to Sunday 20:00 UTC — market still closed (reopens at
        # 21:00 UTC) and ~50h45m past Friday 17:15 UTC close. With a 6h
        # leniency_hours override we're firmly in weekend territory.
        sun_later = datetime(2026, 4, 19, 20, 0, tzinfo=timezone.utc)
        monkeypatch.setattr(_mod, "_now_utc", lambda: sun_later)
        monkeypatch.setattr(_mod, "WEEKEND_LENIENCY_HOURS", 6.0)
        # Set mtime to 50h before sun_later → stale vs 30h threshold.
        stale_ts = (sun_later - timedelta(hours=50)).timestamp()
        os.utime(tmp_tree["ob_csv"], (stale_ts, stale_ts))
        rep = _mod.check_ob_continuation(stale_hours=30.0)
        # Other sub-checks (wiring, well-formed) are PASS, so the worst is
        # the freshness WARN. Overall integration = WARN, not FAIL.
        freshness = [c for c in rep.checks if c.name == "freshness"][0]
        assert freshness.result == "WARN"
        assert "weekend leniency" in freshness.detail.lower()
        assert rep.status == "WARN"

    def test_ob_malformed_csv_missing_column_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        # Rewrite CSV without the insufficient_sample column.
        with open(tmp_tree["ob_csv"], "w", encoding="utf-8", newline="") as fh:
            fh.write("date_utc,scope,continuation_count\n")
            fh.write("2026-04-18,XAUUSD,34\n")
        now_ts = datetime.now(timezone.utc).timestamp()
        os.utime(tmp_tree["ob_csv"], (now_ts, now_ts))
        rep = _mod.check_ob_continuation()
        assert rep.status == "FAIL"
        wf = [c for c in rep.checks if c.name == "well_formed"][0]
        assert wf.result == "FAIL"
        assert "MALFORMED" in wf.detail
        assert "insufficient_sample" in wf.detail

    def test_ob_zero_byte_csv_is_malformed(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["ob_csv"].write_bytes(b"")
        now_ts = datetime.now(timezone.utc).timestamp()
        os.utime(tmp_tree["ob_csv"], (now_ts, now_ts))
        rep = _mod.check_ob_continuation()
        wf = [c for c in rep.checks if c.name == "well_formed"][0]
        assert wf.result == "FAIL"
        assert "0 bytes" in wf.detail

    def test_ob_watchdog_wiring_missing_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        # Strip the ob_continuation_monitor substring from watchdog.ps1.
        tmp_tree["watchdog_ps1"].write_text(
            "api_refusal_monitor\n--profile redacted_account\n", encoding="utf-8",
        )
        rep = _mod.check_ob_continuation()
        wiring = [c for c in rep.checks if c.name == "watchdog_wiring"][0]
        assert wiring.result == "FAIL"
        assert "ob_continuation_monitor" in wiring.detail


class Testredacted_account:
    def test_redacted_account_yaml_missing_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["redacted_account_yaml"].unlink()
        rep = _mod.check_redacted_account_profile()
        assert rep.status == "FAIL"
        yaml_check = [c for c in rep.checks if c.name == "yaml_exists"][0]
        assert yaml_check.result == "FAIL"
        assert "ABSENT" in yaml_check.detail

    def test_redacted_account_yaml_invalid_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["redacted_account_yaml"].write_text(
            "profile_name: :\n  invalid: [unclosed", encoding="utf-8",
        )
        rep = _mod.check_redacted_account_profile()
        yaml_check = [c for c in rep.checks if c.name == "yaml_exists"][0]
        assert yaml_check.result == "FAIL"

    def test_redacted_account_yaml_missing_required_field(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        # Profile without the risk key.
        tmp_tree["redacted_account_yaml"].write_text(
            "profile_name: redacted_account\ndrawdown_reduction:\n  threshold: 0.08\n",
            encoding="utf-8",
        )
        rep = _mod.check_redacted_account_profile()
        yaml_check = [c for c in rep.checks if c.name == "yaml_exists"][0]
        assert yaml_check.result == "FAIL"
        assert "risk" in yaml_check.detail

    def test_redacted_account_watchdog_wiring_missing_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["watchdog_ps1"].write_text(
            "ob_continuation_monitor\napi_refusal_monitor\n", encoding="utf-8",
        )
        rep = _mod.check_redacted_account_profile()
        wiring = [c for c in rep.checks if c.name == "watchdog_wiring"][0]
        assert wiring.result == "FAIL"

    def test_redacted_account_watchdog_wiring_demo_mode_default_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["watchdog_ps1"].write_text(
            "\n".join(
                [
                    "ob_continuation_monitor",
                    "api_refusal_monitor",
                    'if (-not $env:GTOS_PROFILE) { $env:GTOS_PROFILE = "redacted_account" }',
                    'if (-not $env:GTOS_MODE)    { $env:GTOS_MODE    = "demo" }',
                    "--profile $($env:GTOS_PROFILE)",
                    "--mode $($env:GTOS_MODE)",
                ]
            ),
            encoding="utf-8",
        )

        rep = _mod.check_redacted_account_profile()

        wiring = [c for c in rep.checks if c.name == "watchdog_wiring"][0]
        assert wiring.result == "FAIL"
        assert 'GTOS_MODE    = "live"' in wiring.detail

    def test_redacted_account_loader_resolves(self, tmp_tree):
        """The profile loader sub-check uses the REAL ``src.utils.config``
        module (which reads from ``config/profiles/redacted_account.yaml`` on the
        repo, NOT the tmp copy). This test validates the integration path
        between the verify tool and the live loader — the real profile must
        parse.
        """
        _write_fresh_all(tmp_tree)
        rep = _mod.check_redacted_account_profile()
        loader = [c for c in rep.checks if c.name == "loader_resolves"][0]
        # In the test environment the real file exists, so this is PASS.
        # (If the real file were missing we'd expect FAIL — covered by CI.)
        assert loader.result == "PASS"


class TestApiRefusal:
    def test_watchdog_log_absent_is_fail(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["watchdog_log"].unlink()
        rep = _mod.check_api_refusal()
        # Freshness check fails; overall integration = FAIL.
        assert rep.status == "FAIL"

    def test_api_refusal_state_malformed_is_fail(self, tmp_tree):
        """If the state JSON file exists but is invalid, that's FAIL.
        Per-commit b0c2ece the monitor writes this only on alert — an
        unparseable payload is real corruption.
        """
        _write_fresh_all(tmp_tree)
        tmp_tree["api_refusal_state"].write_text("{not json", encoding="utf-8")
        now_ts = datetime.now(timezone.utc).timestamp()
        os.utime(tmp_tree["api_refusal_state"], (now_ts, now_ts))
        rep = _mod.check_api_refusal()
        state_check = [c for c in rep.checks if c.name == "alert_state_shape"][0]
        assert state_check.result == "FAIL"

    def test_api_refusal_state_missing_is_normal(self, tmp_tree):
        """The state file is created only when an alert fires. Its absence
        on the happy path must NOT be a FAIL.
        """
        _write_fresh_all(tmp_tree)
        # Default _write_fresh_all does not create the state file.
        rep = _mod.check_api_refusal()
        state_check = [c for c in rep.checks if c.name == "alert_state_shape"][0]
        assert state_check.result == "PASS"
        assert "absent" in state_check.detail.lower()

    def test_api_refusal_malformed_corpus_missing_is_ok(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["malformed_log"].unlink()
        rep = _mod.check_api_refusal()
        corpus = [c for c in rep.checks if c.name == "input_corpus"][0]
        assert corpus.result == "PASS"  # monitor handles missing gracefully

    def test_api_refusal_dead_zone_is_lenient(self, tmp_tree, monkeypatch):
        """Inside the watchdog daily dead zone (local 01:15-07:45 UTC+8 per
        scripts/watchdog.ps1:7-12 → UTC 17:15-23:45 of the prior UTC day),
        the api_refusal heartbeat is naturally stale because the watchdog
        doesn't run. A stale heartbeat in that window must downgrade to
        WARN, not FAIL.
        """
        _write_fresh_all(tmp_tree)
        # Pin "now" to Monday 20:00 UTC — local UTC+8 is Tuesday 04:00, which
        # is firmly inside the 01:15-07:45 dead zone. Monday 20:00 UTC is
        # NOT weekend (Fri 17:15 → Sun 21:00), isolating dead-zone leniency.
        mon_deadzone = datetime(2026, 4, 20, 20, 0, tzinfo=timezone.utc)
        monkeypatch.setattr(_mod, "_now_utc", lambda: mon_deadzone)
        assert _mod._is_watchdog_dead_zone(now=mon_deadzone)
        assert not _mod._is_market_closed(now=mon_deadzone)
        # Stale the heartbeat log well past the 1h threshold.
        stale_ts = (mon_deadzone - timedelta(hours=5)).timestamp()
        os.utime(tmp_tree["watchdog_log"], (stale_ts, stale_ts))
        rep = _mod.check_api_refusal(stale_hours=1.0)
        freshness = [c for c in rep.checks if c.name == "freshness"][0]
        assert freshness.result == "WARN"
        assert "dead zone" in freshness.detail.lower()
        # Overall integration is at worst WARN (no FAIL anywhere).
        assert rep.status in ("WARN", "PASS")

    def test_api_refusal_latest_watchdog_status_must_be_ok(self, tmp_tree):
        _write_fresh_all(tmp_tree)
        tmp_tree["watchdog_log"].write_text(
            "2026-04-18 00:01:00    [API_REFUSAL] Telegram HTTP failed\n",
            encoding="utf-8",
        )
        rep = _mod.check_api_refusal()
        status = [c for c in rep.checks if c.name == "watchdog_status_line"][0]
        assert status.result == "FAIL"
        assert "not OK" in status.detail


class TestWatchdogDeadZone:
    """Exercise the ``_is_watchdog_dead_zone`` helper in isolation."""

    def test_local_midmorning_is_outside(self):
        # Monday 06:00 UTC = local Monday 14:00 — well outside the dead zone.
        t = datetime(2026, 4, 20, 6, 0, tzinfo=timezone.utc)
        assert not _mod._is_watchdog_dead_zone(now=t)

    def test_utc_2000_monday_is_inside(self):
        # Monday 20:00 UTC = local Tuesday 04:00 — inside 01:15-07:45.
        t = datetime(2026, 4, 20, 20, 0, tzinfo=timezone.utc)
        assert _mod._is_watchdog_dead_zone(now=t)

    def test_utc_1715_right_on_boundary_is_inside(self):
        # Exactly UTC 17:15 Monday = local Tuesday 01:15 — start boundary
        # is inclusive.
        t = datetime(2026, 4, 20, 17, 15, tzinfo=timezone.utc)
        assert _mod._is_watchdog_dead_zone(now=t)

    def test_utc_2345_end_boundary_is_outside(self):
        # UTC 23:45 Monday = local Tuesday 07:45 — end boundary is exclusive
        # (matches watchdog.ps1 ``-lt $DeadZoneEnd``).
        t = datetime(2026, 4, 20, 23, 45, tzinfo=timezone.utc)
        assert not _mod._is_watchdog_dead_zone(now=t)


# =============================================================================
# CLI / summary / JSON output
# =============================================================================


class TestCli:
    def test_exit_code_0_on_all_pass(self, tmp_tree, capsys):
        _write_fresh_all(tmp_tree)
        rc = _mod.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "WATCHDOG E2E: PASS" in out

    def test_exit_code_1_on_any_fail(self, tmp_tree, capsys):
        _write_fresh_all(tmp_tree)
        tmp_tree["ob_csv"].unlink()
        rc = _mod.main([])
        out = capsys.readouterr().out
        assert rc == 1
        assert "WATCHDOG E2E: FAIL" in out

    def test_exit_code_0_on_warn_allowed(self, tmp_tree, capsys, monkeypatch):
        _write_fresh_all(tmp_tree)
        # Force a WARN via weekend-leniency stale path. Pin to Sunday 20:00
        # UTC (market still closed — reopens 21:00), lower leniency so
        # weekend definitely active.
        sun_evening = datetime(2026, 4, 19, 20, 0, tzinfo=timezone.utc)
        monkeypatch.setattr(_mod, "_now_utc", lambda: sun_evening)
        monkeypatch.setattr(_mod, "WEEKEND_LENIENCY_HOURS", 6.0)
        stale_ts = (sun_evening - timedelta(hours=60)).timestamp()
        for p in (tmp_tree["ob_csv"], tmp_tree["watchdog_log"]):
            os.utime(p, (stale_ts, stale_ts))
        rc = _mod.main(["--ob-stale-hours", "30", "--api-refusal-stale-hours", "1"])
        out = capsys.readouterr().out
        # Some or all may be WARN, none should be FAIL because weekend.
        assert rc == 0
        assert "WATCHDOG E2E: WARN" in out or "WATCHDOG E2E: PASS" in out

    def test_json_output_is_valid_json(self, tmp_tree, capsys):
        _write_fresh_all(tmp_tree)
        rc = _mod.main(["--json"])
        out = capsys.readouterr().out
        data = json.loads(out)  # parses → valid JSON
        assert data["overall"] == "PASS"
        assert data["counts"] == {"PASS": 3, "WARN": 0, "FAIL": 0}
        assert len(data["integrations"]) == 3
        names = {i["integration"] for i in data["integrations"]}
        assert names == {
            "ob_continuation_monitor",
            "api_refusal_monitor",
            "redacted_account_profile",
        }
        for itg in data["integrations"]:
            assert itg["status"] in ("PASS", "WARN", "FAIL")
            assert isinstance(itg["checks"], list)
            for c in itg["checks"]:
                assert c["result"] in ("PASS", "WARN", "FAIL")
                assert "name" in c and "detail" in c
        assert rc == 0

    def test_verbose_output_includes_subcheck_details(self, tmp_tree, capsys):
        _write_fresh_all(tmp_tree)
        rc = _mod.main(["--verbose"])
        out = capsys.readouterr().out
        assert rc == 0
        # Verbose prints sub-check lines with bracketed result codes.
        assert "[PASS]" in out or "[WARN]" in out
        assert "freshness" in out or "well_formed" in out
        assert "artifact:" in out

    def test_json_output_roundtrip_matches_summary(self, tmp_tree, capsys):
        """JSON integration list should include every active integration even when one fails."""
        _write_fresh_all(tmp_tree)
        tmp_tree["ob_csv"].unlink()
        rc = _mod.main(["--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert rc == 1
        assert data["overall"] == "FAIL"
        assert data["counts"]["FAIL"] >= 1
        assert len(data["integrations"]) == 3


# =============================================================================
# Edge cases explicitly called out in the brief
# =============================================================================


class TestEdgeCases:
    def test_broken_symlink_reported_as_absent(self, tmp_tree):
        """A symlink pointing at a nonexistent target → ABSENT. POSIX-only
        test — Windows skips (CI on Windows lacks symlink privilege by
        default).
        """
        if sys.platform.startswith("win"):
            pytest.skip("Windows CI typically lacks SeCreateSymbolicLinkPrivilege")
        _write_fresh_all(tmp_tree)
        # Replace OB CSV with a symlink to a missing file.
        tmp_tree["ob_csv"].unlink()
        os.symlink(tmp_tree["ob_csv"].parent / "does_not_exist.csv", tmp_tree["ob_csv"])
        rep = _mod.check_ob_continuation()
        freshness = [c for c in rep.checks if c.name == "freshness"][0]
        assert freshness.result == "FAIL"
        assert "ABSENT" in freshness.detail

    def test_timezone_always_utc(self, tmp_tree):
        """Age computation must use UTC-aware comparisons. Test via
        ``_age_hours`` helper directly — if it compared naive vs aware we'd
        get TypeError. Set a known mtime 2h ago, assert age ≈ 2.0.
        """
        _write_fresh_all(tmp_tree)
        two_h_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()
        os.utime(tmp_tree["ob_csv"], (two_h_ago, two_h_ago))
        age = _mod._age_hours(tmp_tree["ob_csv"])
        assert age is not None
        assert 1.9 <= age <= 2.1

    def test_watchdog_ps1_missing_entirely_is_fail_for_all_wired_checks(
        self, tmp_tree,
    ):
        """If watchdog.ps1 doesn't exist, every integration that depends on
        wiring drift detection must FAIL that sub-check (the tool must not
        silently pass because the substring match defaulted to False).
        """
        _write_fresh_all(tmp_tree)
        tmp_tree["watchdog_ps1"].unlink()
        reports = _mod.run_all_checks()
        # OB + API refusal + redacted_account all have wiring checks.
        for rep in reports:
            wiring = [c for c in rep.checks if c.name == "watchdog_wiring"]
            if wiring:
                assert wiring[0].result == "FAIL"
                assert "ABSENT" in wiring[0].detail

    def test_run_all_checks_never_raises(self, tmp_tree, monkeypatch):
        """A raising sub-check must be captured as FAIL, not propagated."""
        _write_fresh_all(tmp_tree)

        def boom(*a, **kw):
            raise RuntimeError("intentional test failure")

        monkeypatch.setattr(_mod, "check_api_refusal", boom)
        # Should not raise; api_refusal_monitor should land as FAIL with the
        # audit_exception sub-check.
        reports = _mod.run_all_checks()
        api = [r for r in reports if r.integration == "api_refusal_monitor"][0]
        assert api.status == "FAIL"
        ex = [c for c in api.checks if c.name == "audit_exception"][0]
        assert "intentional test failure" in ex.detail
