"""Session-volatility and sweep-divergence status helpers for LTO-022.

This module is research/tooling only. It makes the H25/H16 CSV lanes auditable
by recording whether expected symbol/session rows are present, whether they are
event rows or explicit no-event rows, and when the source files last changed.
It does not call MT5, AI, canaries, broker orders, or paid data sources.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "session_volatility_sweep_status_v1"
CLASSIFIER_VERSION = "session_volatility_sweep_status_classifier_v1"
COMPLETE = "SESSION_VOL_SWEEP_COVERAGE_COMPLETE"
ACTION_REQUIRED = "SESSION_VOL_SWEEP_ACTION_REQUIRED"

SESSION_VOL_CSV = Path("shadow_logs/session_volatility_log.csv")
SWEEP_CSV = Path("shadow_logs/sweep_divergence_log.csv")

SESSION_VOL_FIELDNAMES = [
    "date",
    "instrument",
    "session",
    "w1_avg_range",
    "w2_avg_range",
    "w3_avg_range",
    "pattern",
    "candle_count",
]
SWEEP_FIELDNAMES = [
    "date",
    "instrument",
    "session",
    "sweep_direction",
    "sweep_extreme",
    "reference_level",
    "outcome",
]

SESSION_VOL_EXPECTED = (
    {"instrument": "XAUUSD", "session": "london"},
    {"instrument": "NAS100", "session": "london"},
    {"instrument": "XAGUSD", "session": "london"},
)
SWEEP_EXPECTED = (
    {"instrument": "US30", "session": "london"},
    {"instrument": "XAUUSD", "session": "london"},
)

NO_EVENT_TEXT = "NO_EVENT_IN_WINDOW_OR_MONITOR_NOT_TRIGGERED"


def target_previous_utc_date(now_utc: datetime | None = None) -> date:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now.astimezone(timezone.utc) - timedelta(days=1)).date()


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def append_missing_no_event_rows(root: Path, target_date: date) -> dict[str, int]:
    """Append explicit no-event CSV rows for missing expected coverage keys."""
    written = {"session_volatility_log.csv": 0, "sweep_divergence_log.csv": 0}
    date_text = target_date.isoformat()

    session_path = root / SESSION_VOL_CSV
    session_rows = _read_csv_rows(session_path)
    session_keys = {
        (row.get("date", ""), row.get("instrument", ""), row.get("session", ""))
        for row in session_rows
    }
    missing_session = []
    for expected in SESSION_VOL_EXPECTED:
        key = (date_text, expected["instrument"], expected["session"])
        if key not in session_keys:
            missing_session.append(
                {
                    "date": date_text,
                    "instrument": expected["instrument"],
                    "session": expected["session"],
                    "w1_avg_range": "",
                    "w2_avg_range": "",
                    "w3_avg_range": "",
                    "pattern": NO_EVENT_TEXT,
                    "candle_count": 0,
                }
            )
    written["session_volatility_log.csv"] = _write_csv_rows(
        session_path, missing_session, SESSION_VOL_FIELDNAMES
    )

    sweep_path = root / SWEEP_CSV
    sweep_rows = _read_csv_rows(sweep_path)
    sweep_keys = {
        (row.get("date", ""), row.get("instrument", ""), row.get("session", ""))
        for row in sweep_rows
    }
    missing_sweep = []
    for expected in SWEEP_EXPECTED:
        key = (date_text, expected["instrument"], expected["session"])
        if key not in sweep_keys:
            missing_sweep.append(
                {
                    "date": date_text,
                    "instrument": expected["instrument"],
                    "session": expected["session"],
                    "sweep_direction": "NO_EVENT_IN_WINDOW",
                    "sweep_extreme": "",
                    "reference_level": "",
                    "outcome": NO_EVENT_TEXT,
                }
            )
    written["sweep_divergence_log.csv"] = _write_csv_rows(
        sweep_path, missing_sweep, SWEEP_FIELDNAMES
    )
    return written


def _source_file_status(path: Path) -> tuple[str, str | None, int, list[str]]:
    if not path.exists():
        return "SOURCE_FILE_MISSING", None, 0, []
    latest = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    rows = _read_csv_rows(path)
    headers: list[str] = []
    if path.stat().st_size > 0:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []
    if path.stat().st_size == 0:
        return "SOURCE_FILE_EMPTY", latest, 0, headers
    return "SOURCE_FILE_PRESENT", latest, len(rows), headers


def build_status_row(
    *,
    root: Path,
    source_name: str,
    source_path: Path,
    target_date: date,
    expected_rows: tuple[dict[str, str], ...],
    row_status_field: str,
    row_no_event_value: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    resolved_path = root / source_path
    rows = _read_csv_rows(resolved_path)
    date_text = target_date.isoformat()
    matching = [row for row in rows if row.get("date") == date_text]
    keys_present = {
        (row.get("instrument", ""), row.get("session", ""))
        for row in matching
    }
    expected_keys = {
        (row["instrument"], row["session"])
        for row in expected_rows
    }
    missing_keys = sorted(expected_keys - keys_present)
    covered_rows = [
        row
        for row in matching
        if (row.get("instrument", ""), row.get("session", "")) in expected_keys
    ]
    event_rows = [
        row
        for row in covered_rows
        if str(row.get(row_status_field) or "") != row_no_event_value
    ]
    no_event_rows = [
        row
        for row in covered_rows
        if str(row.get(row_status_field) or "") == row_no_event_value
    ]
    source_status, latest_run_time, source_row_count, headers = _source_file_status(resolved_path)
    action_required: list[str] = []
    if source_status != "SOURCE_FILE_PRESENT":
        action_required.append(source_status)
    if missing_keys:
        action_required.append("MISSING_EXPECTED_SYMBOL_SESSION_ROWS")
    coverage_status = ACTION_REQUIRED if action_required else COMPLETE
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        source_name,
        date_text,
        source_status,
        latest_run_time,
        source_row_count,
        sorted(keys_present),
        missing_keys,
        len(event_rows),
        len(no_event_rows),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("session_vol_sweep_status", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-022",
        "follow_id": "LIVE-FOLLOW-019",
        "source_name": source_name,
        "source_path": str(source_path),
        "source_file_status": source_status,
        "source_headers": headers,
        "source_row_count": source_row_count,
        "target_date": date_text,
        "latest_run_time_utc": latest_run_time,
        "expected_symbol_sessions": [dict(row) for row in expected_rows],
        "covered_symbol_sessions": [
            {"instrument": instrument, "session": session}
            for instrument, session in sorted(keys_present & expected_keys)
        ],
        "missing_symbol_sessions": [
            {"instrument": instrument, "session": session}
            for instrument, session in missing_keys
        ],
        "coverage_status": coverage_status,
        "event_row_count": len(event_rows),
        "no_event_row_count": len(no_event_rows),
        "action_required_codes": sorted(set(action_required)),
        "cadence_policy": "WATCHDOG_OR_DAILY_CHECKLIST_ONCE_PER_UTC_DAY",
        "watchdog_marker": "session_volatility_sweep_status_last_run.utcdate",
        "no_event_status_value": row_no_event_value,
        "claim_boundary": (
            "No-event rows prove the monitor lane is explicit for the target "
            "symbol/session/date. They are not strategy validation rows."
        ),
        "evidence_class": "MONITOR_CADENCE_STATUS",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_status_rows(
    *,
    root: Path,
    target_date: date,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    return [
        build_status_row(
            root=root,
            source_name="session_volatility",
            source_path=SESSION_VOL_CSV,
            target_date=target_date,
            expected_rows=SESSION_VOL_EXPECTED,
            row_status_field="pattern",
            row_no_event_value=NO_EVENT_TEXT,
            generated_at_utc=generated_at_utc,
        ),
        build_status_row(
            root=root,
            source_name="sweep_divergence",
            source_path=SWEEP_CSV,
            target_date=target_date,
            expected_rows=SWEEP_EXPECTED,
            row_status_field="outcome",
            row_no_event_value=NO_EVENT_TEXT,
            generated_at_utc=generated_at_utc,
        ),
    ]


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = Counter(str(row.get("coverage_status") or "UNKNOWN") for row in rows)
    sources = Counter(str(row.get("source_name") or "UNKNOWN") for row in rows)
    source_status = Counter(str(row.get("source_file_status") or "UNKNOWN") for row in rows)
    actions: Counter[str] = Counter()
    for row in rows:
        actions.update(row.get("action_required_codes") or [])
    return {
        "rows": len(rows),
        "coverage_status_counts": dict(coverage),
        "source_counts": dict(sources),
        "source_file_status_counts": dict(source_status),
        "event_row_total": sum(int(row.get("event_row_count") or 0) for row in rows),
        "no_event_row_total": sum(int(row.get("no_event_row_count") or 0) for row in rows),
        "action_required_code_counts": dict(actions),
    }
