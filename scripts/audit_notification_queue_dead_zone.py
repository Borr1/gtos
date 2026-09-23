#!/usr/bin/env python3
"""Backfill and audit LTO-037 notification queue dead-zone status."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.notification_queue_dead_zone_status import (  # noqa: E402
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_status_row,
    default_lock_path,
    default_queue_path,
)


DEFAULT_OUTPUT = Path("shadow_logs/notification_queue_dead_zone_status.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO037_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def append_jsonl_once(path: Path, row: dict[str, Any]) -> bool:
    existing = {str(item.get("row_key")) for item in read_jsonl(path) if item.get("row_key")}
    if str(row.get("row_key")) in existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def build_report(row: dict[str, Any], *, output_path: Path, appended: bool) -> dict[str, Any]:
    action_required = row.get("notification_queue_status") == ACTION_REQUIRED
    return {
        "schema_version": "lto037_notification_queue_dead_zone_status_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_required else "OK_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "status_rows_available": len(read_jsonl(output_path)),
            "status_rows_appended_this_run": 1 if appended else 0,
            "action_required": 1 if action_required else 0,
            "pending_alert_count": row.get("pending_alert_count"),
            "queue_row_count": row.get("queue_row_count"),
            "terminal_marker_count": row.get("terminal_marker_count"),
        },
        "notification_queue_status": row.get("notification_queue_status"),
        "worker_status": row.get("worker_status"),
        "queue_status": row.get("queue_status"),
        "dead_zone_active": row.get("dead_zone_active"),
        "expected_worker_policy": row.get("expected_worker_policy"),
        "watchdog_local_time": row.get("watchdog_local_time"),
        "watchdog_local_day": row.get("watchdog_local_day"),
        "queue_file_status": row.get("queue_file_status"),
        "lock_status": row.get("lock_status"),
        "lock_pid_alive": row.get("lock_pid_alive"),
        "action_required_codes": row.get("action_required_codes") or [],
        "row": row,
        "claim_boundary": row.get("claim_boundary"),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# LTO-037 Notification Queue Dead-Zone Status - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Status",
        "",
        f"- Notification queue status: `{report['notification_queue_status']}`",
        f"- Worker status: `{report['worker_status']}`",
        f"- Queue status: `{report['queue_status']}`",
        f"- Dead-zone active: `{report['dead_zone_active']}`",
        f"- Expected worker policy: `{report['expected_worker_policy']}`",
        f"- Watchdog local time: `{report['watchdog_local_time']}`",
        f"- Watchdog local day: `{report['watchdog_local_day']}`",
        f"- Queue file status: `{report['queue_file_status']}`",
        f"- Lock status: `{report['lock_status']}`",
        f"- Lock PID alive: `{report['lock_pid_alive']}`",
        f"- Action-required codes: `{report['action_required_codes']}`",
        "",
        "## Counts",
        "",
        f"- Status rows available: `{report['counts']['status_rows_available']}`",
        f"- Status rows appended this run: `{report['counts']['status_rows_appended_this_run']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        f"- Pending alerts: `{report['counts']['pending_alert_count']}`",
        f"- Queue rows: `{report['counts']['queue_row_count']}`",
        f"- Terminal markers: `{report['counts']['terminal_marker_count']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"] or "",
        "",
        "## Safety Counters",
        "",
        f"- no_ai_calls: `{report['no_ai_calls']}`",
        f"- no_canary_required: `{report['no_canary_required']}`",
        f"- no_execution: `{report['no_execution']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--date", default=None, help="Target date to audit (YYYY-MM-DD). Defaults to now UTC.")
    parser.add_argument("--now-utc", default=None, help="Override audit clock for tests/replay.")
    parser.add_argument("--queue-path", type=Path, default=default_queue_path())
    parser.add_argument("--lock-path", type=Path, default=default_lock_path())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    now = datetime.fromisoformat(args.now_utc.replace("Z", "+00:00")) if args.now_utc else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    target = date.fromisoformat(args.date) if args.date else now.date()
    output = args.output if args.output.is_absolute() else args.root / args.output
    report_json = args.report_json if args.report_json.is_absolute() else args.root / args.report_json
    report_md = args.report_md if args.report_md.is_absolute() else args.root / args.report_md

    row = build_status_row(
        root=args.root,
        now_utc=now,
        target_date=target,
        queue_path=args.queue_path,
        lock_path=args.lock_path,
        generated_at_utc=now.isoformat(),
    )
    appended = append_jsonl_once(output, row)
    report = build_report(row, output_path=output, appended=appended)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "worker_status": report["worker_status"],
                "queue_status": report["queue_status"],
                "dead_zone_active": report["dead_zone_active"],
                "status_rows_appended": 1 if appended else 0,
                "status_rows_available": report["counts"]["status_rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
