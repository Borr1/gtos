from __future__ import annotations

import json
from datetime import datetime, timezone

from src.research_infra.notification_queue_dead_zone_status import (
    ACTION_REQUIRED,
    QUEUE_EMPTY,
    QUEUE_PENDING,
    RUNNING,
    STOPPED_EXPECTED_DEAD_ZONE,
    STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW,
    build_status_row,
    is_watchdog_dead_zone,
    queue_pending_summary,
)


def _write_lock(root, pid: int = 12345) -> None:
    lock_path = root / "knowledge_base" / "meta" / ".notification_queue_worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(pid), encoding="utf-8")


def _write_queue(root, rows: list[dict]) -> None:
    queue_path = root / "pipeline_state" / "notification_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_dead_zone_policy_matches_watchdog_local_utc8_window():
    assert is_watchdog_dead_zone(datetime(2026, 5, 4, 18, 0, tzinfo=timezone.utc))
    assert not is_watchdog_dead_zone(datetime(2026, 5, 5, 2, 0, tzinfo=timezone.utc))
    assert is_watchdog_dead_zone(datetime(2026, 5, 3, 8, 0, tzinfo=timezone.utc))


def test_active_window_running_worker_and_empty_queue(tmp_path):
    _write_lock(tmp_path, 222)
    _write_queue(tmp_path, [])

    row = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 5, 2, 0, tzinfo=timezone.utc),
        process_alive=lambda pid: pid == 222,
    )

    assert row["worker_status"] == RUNNING
    assert row["queue_status"] == QUEUE_EMPTY
    assert row["expected_worker_policy"] == "RUNNING_REQUIRED_DURING_ACTIVE_WINDOW"
    assert row["notification_queue_status"] != ACTION_REQUIRED
    assert row["action_required_codes"] == []


def test_dead_zone_missing_worker_is_expected_cleanup(tmp_path):
    row = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 4, 18, 0, tzinfo=timezone.utc),
        process_alive=lambda pid: False,
    )

    assert row["dead_zone_active"] is True
    assert row["worker_status"] == STOPPED_EXPECTED_DEAD_ZONE
    assert row["expected_worker_policy"] == "STOPPED_ALLOWED_DURING_DEAD_ZONE_CLEANUP"
    assert row["notification_queue_status"] != ACTION_REQUIRED


def test_active_window_missing_worker_requires_action(tmp_path):
    row = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 5, 2, 0, tzinfo=timezone.utc),
        process_alive=lambda pid: False,
    )

    assert row["dead_zone_active"] is False
    assert row["worker_status"] == STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW
    assert row["notification_queue_status"] == ACTION_REQUIRED
    assert "WORKER_STOPPED_DURING_ACTIVE_WINDOW" in row["action_required_codes"]


def test_queue_pending_and_terminal_marker_resolution(tmp_path):
    queue_path = tmp_path / "pipeline_state" / "notification_queue.jsonl"
    _write_queue(
        tmp_path,
        [
            {"alert_id": "a", "ts_utc": "2026-05-05T01:00:00+00:00", "message": "a"},
            {"alert_id": "b", "ts_utc": "2026-05-05T01:01:00+00:00", "message": "b"},
            {"alert_id": "a", "marker": "DELIVERED"},
        ],
    )

    summary = queue_pending_summary(queue_path)

    assert summary["queue_status"] == QUEUE_PENDING
    assert summary["pending_alert_count"] == 1
    assert summary["terminal_marker_count"] == 1


def test_row_key_is_stable_when_only_clock_changes(tmp_path):
    _write_lock(tmp_path, 222)
    row_1 = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 5, 2, 0, tzinfo=timezone.utc),
        process_alive=lambda pid: pid == 222,
        generated_at_utc="2026-05-05T02:00:00+00:00",
    )
    row_2 = build_status_row(
        root=tmp_path,
        now_utc=datetime(2026, 5, 5, 2, 30, tzinfo=timezone.utc),
        process_alive=lambda pid: pid == 222,
        generated_at_utc="2026-05-05T02:30:00+00:00",
    )

    assert row_1["row_key"] == row_2["row_key"]
    assert row_1["checked_at_utc"] != row_2["checked_at_utc"]
