from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.research_infra.session_volatility_sweep_status import (
    ACTION_REQUIRED,
    COMPLETE,
    SESSION_VOL_CSV,
    SWEEP_CSV,
    append_missing_no_event_rows,
    build_status_rows,
)


def _read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_no_event_backfill_writes_expected_csv_rows(tmp_path):
    written = append_missing_no_event_rows(tmp_path, date(2026, 5, 4))

    assert written == {"session_volatility_log.csv": 3, "sweep_divergence_log.csv": 2}
    session_rows = _read_csv(tmp_path / SESSION_VOL_CSV)
    sweep_rows = _read_csv(tmp_path / SWEEP_CSV)

    assert {(row["instrument"], row["session"]) for row in session_rows} == {
        ("XAUUSD", "london"),
        ("NAS100", "london"),
        ("XAGUSD", "london"),
    }
    assert all(row["pattern"] == "NO_EVENT_IN_WINDOW_OR_MONITOR_NOT_TRIGGERED" for row in session_rows)
    assert {(row["instrument"], row["session"]) for row in sweep_rows} == {
        ("US30", "london"),
        ("XAUUSD", "london"),
    }
    assert all(row["outcome"] == "NO_EVENT_IN_WINDOW_OR_MONITOR_NOT_TRIGGERED" for row in sweep_rows)


def test_no_event_backfill_is_idempotent(tmp_path):
    append_missing_no_event_rows(tmp_path, date(2026, 5, 4))

    written = append_missing_no_event_rows(tmp_path, date(2026, 5, 4))

    assert written == {"session_volatility_log.csv": 0, "sweep_divergence_log.csv": 0}


def test_status_rows_separate_no_event_from_missing(tmp_path):
    append_missing_no_event_rows(tmp_path, date(2026, 5, 4))

    rows = build_status_rows(
        root=tmp_path,
        target_date=date(2026, 5, 4),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert [row["coverage_status"] for row in rows] == [COMPLETE, COMPLETE]
    assert sum(row["no_event_row_count"] for row in rows) == 5
    assert sum(row["event_row_count"] for row in rows) == 0
    assert all(row["action_required_codes"] == [] for row in rows)
    assert all(row["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)


def test_status_rows_flag_missing_symbol_session_coverage(tmp_path):
    append_missing_no_event_rows(tmp_path, date(2026, 5, 4))
    session_path = tmp_path / SESSION_VOL_CSV
    rows = _read_csv(session_path)
    rows = [row for row in rows if row["instrument"] != "NAS100"]
    with session_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    status_rows = build_status_rows(
        root=tmp_path,
        target_date=date(2026, 5, 4),
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    session_status = [row for row in status_rows if row["source_name"] == "session_volatility"][0]
    assert session_status["coverage_status"] == ACTION_REQUIRED
    assert "MISSING_EXPECTED_SYMBOL_SESSION_ROWS" in session_status["action_required_codes"]
    assert session_status["missing_symbol_sessions"] == [{"instrument": "NAS100", "session": "london"}]


def test_watchdog_has_lto022_status_hook():
    text = Path("scripts/watchdog.ps1").read_text(encoding="utf-8", errors="replace")

    assert "audit_session_volatility_sweep_status.py" in text
    assert "session_volatility_sweep_status_last_run.utcdate" in text
    assert "[SESSION_VOL_SWEEP] OK" in text
