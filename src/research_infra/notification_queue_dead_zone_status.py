"""Notification queue dead-zone status helpers for LTO-037.

Research/tooling only. This module classifies the notification queue worker
against the same UTC+8 dead-zone policy used by ``scripts/watchdog.ps1`` so
operator reports can distinguish expected off-hours cleanup from a missing
worker during active windows. It does not start workers, send Telegram alerts,
touch MT5, run AI, run canaries, place orders, or fetch paid data.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "notification_queue_dead_zone_status_v1"
CLASSIFIER_VERSION = "notification_queue_dead_zone_classifier_v1"

RUNNING = "RUNNING"
STOPPED_EXPECTED_DEAD_ZONE = "STOPPED_EXPECTED_DEAD_ZONE"
STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW = "STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW"
QUEUE_EMPTY = "QUEUE_EMPTY"
QUEUE_PENDING = "QUEUE_PENDING"
ACTION_REQUIRED = "NOTIFICATION_QUEUE_ACTION_REQUIRED"

DEFAULT_QUEUE_PATH = Path("pipeline_state/notification_queue.jsonl")
DEFAULT_LOCK_PATH = Path("knowledge_base/meta/.notification_queue_worker.lock")
WATCHDOG_LOCAL_TZ = timezone(timedelta(hours=8), name="UTC+08")
DEAD_ZONE_START_MINUTE = 1 * 60 + 15
DEAD_ZONE_END_MINUTE = 7 * 60 + 45
TERMINAL_MARKERS = {"DELIVERED", "EXPIRED", "FAILED"}


def default_queue_path() -> Path:
    configured = os.environ.get("GTOS_NOTIFICATION_QUEUE_PATH")
    if configured and configured.strip():
        return Path(configured.strip())
    return DEFAULT_QUEUE_PATH


def default_lock_path() -> Path:
    namespace = (os.environ.get("GTOS_RUNTIME_NAMESPACE") or "").strip()
    if namespace:
        return Path(f"knowledge_base/meta/.notification_queue_worker_{namespace}.lock")
    return DEFAULT_LOCK_PATH


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def coerce_utc(value: datetime | None) -> datetime:
    now = value or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def is_watchdog_dead_zone(now_utc: datetime | None = None) -> bool:
    """Mirror ``scripts/watchdog.ps1`` ``Test-TradingHours`` off-hours policy."""

    now = coerce_utc(now_utc)
    local = now.astimezone(WATCHDOG_LOCAL_TZ)
    minutes = local.hour * 60 + local.minute
    weekday = local.weekday()  # Monday=0, Saturday=5, Sunday=6.
    if weekday == 6:
        return True
    if weekday == 5 and minutes >= DEAD_ZONE_START_MINUTE:
        return True
    return DEAD_ZONE_START_MINUTE <= minutes < DEAD_ZONE_END_MINUTE


def watchdog_local_context(now_utc: datetime | None = None) -> dict[str, Any]:
    now = coerce_utc(now_utc)
    local = now.astimezone(WATCHDOG_LOCAL_TZ)
    return {
        "local_time": local.isoformat(),
        "local_day": local.strftime("%A"),
        "dead_zone_active": is_watchdog_dead_zone(now),
        "dead_zone_window_local": "01:15-07:45 UTC+8 weekdays; Sunday all day; Saturday after 01:15",
    }


def read_lock_pid(path: Path) -> tuple[int | None, str]:
    if not path.exists():
        return None, "LOCK_MISSING"
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace").strip()
    except OSError as exc:
        return None, f"LOCK_UNREADABLE:{type(exc).__name__}"
    if not text:
        return None, "LOCK_EMPTY"
    try:
        pid = int(text)
    except ValueError:
        return None, "LOCK_MALFORMED_PID"
    if pid <= 0:
        return None, "LOCK_MALFORMED_PID"
    return pid, "LOCK_PRESENT"


def _windows_pid_alive(pid: int) -> bool:
    import ctypes

    process_query_limited_information = 0x1000
    still_active = 259
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def default_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def queue_pending_summary(path: Path) -> dict[str, Any]:
    enqueue_ids: set[str] = set()
    terminal_ids: set[str] = set()
    malformed_rows = 0
    total_rows = 0
    latest_ts: datetime | None = None

    if not path.exists():
        return {
            "queue_file_exists": False,
            "queue_file_status": "QUEUE_FILE_MISSING",
            "queue_row_count": 0,
            "enqueue_row_count": 0,
            "terminal_marker_count": 0,
            "malformed_row_count": 0,
            "pending_alert_count": 0,
            "queue_status": QUEUE_EMPTY,
            "latest_enqueue_ts_utc": None,
        }

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return {
            "queue_file_exists": True,
            "queue_file_status": f"QUEUE_FILE_UNREADABLE:{type(exc).__name__}",
            "queue_row_count": 0,
            "enqueue_row_count": 0,
            "terminal_marker_count": 0,
            "malformed_row_count": 1,
            "pending_alert_count": 0,
            "queue_status": QUEUE_EMPTY,
            "latest_enqueue_ts_utc": None,
        }

    for line in lines:
        text = line.strip()
        if not text:
            continue
        total_rows += 1
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            malformed_rows += 1
            continue
        if not isinstance(row, dict):
            malformed_rows += 1
            continue
        alert_id = row.get("alert_id")
        if not isinstance(alert_id, str) or not alert_id:
            malformed_rows += 1
            continue
        marker = row.get("marker")
        if marker in TERMINAL_MARKERS:
            terminal_ids.add(alert_id)
            continue
        enqueue_ids.add(alert_id)
        row_ts = parse_utc(row.get("ts_utc"))
        if row_ts and (latest_ts is None or row_ts > latest_ts):
            latest_ts = row_ts

    pending_ids = sorted(enqueue_ids - terminal_ids)
    return {
        "queue_file_exists": True,
        "queue_file_status": "QUEUE_FILE_PRESENT",
        "queue_row_count": total_rows,
        "enqueue_row_count": len(enqueue_ids),
        "terminal_marker_count": len(terminal_ids),
        "malformed_row_count": malformed_rows,
        "pending_alert_count": len(pending_ids),
        "queue_status": QUEUE_PENDING if pending_ids else QUEUE_EMPTY,
        "latest_enqueue_ts_utc": latest_ts.isoformat() if latest_ts else None,
    }


def classify_worker(
    *,
    lock_path: Path,
    now_utc: datetime | None = None,
    process_alive: Callable[[int], bool] | None = None,
) -> dict[str, Any]:
    now = coerce_utc(now_utc)
    dead_zone_active = is_watchdog_dead_zone(now)
    pid, lock_status = read_lock_pid(lock_path)
    alive = bool(pid and (process_alive or default_process_alive)(pid))

    if alive:
        worker_status = RUNNING
    elif dead_zone_active:
        worker_status = STOPPED_EXPECTED_DEAD_ZONE
    else:
        worker_status = STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW

    return {
        "worker_status": worker_status,
        "lock_file_exists": lock_path.exists(),
        "lock_status": lock_status,
        "lock_pid": pid,
        "lock_pid_alive": alive,
        **watchdog_local_context(now),
    }


def build_status_row(
    *,
    root: Path,
    now_utc: datetime | None = None,
    target_date: date | None = None,
    queue_path: Path | None = None,
    lock_path: Path | None = None,
    process_alive: Callable[[int], bool] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    now = coerce_utc(now_utc)
    target = target_date or now.date()
    generated = generated_at_utc or now.isoformat()
    queue_path = queue_path or default_queue_path()
    lock_path = lock_path or default_lock_path()
    q_path = queue_path if queue_path.is_absolute() else root / queue_path
    l_path = lock_path if lock_path.is_absolute() else root / lock_path

    queue = queue_pending_summary(q_path)
    worker = classify_worker(lock_path=l_path, now_utc=now, process_alive=process_alive)

    action_required: list[str] = []
    if worker["worker_status"] == STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW:
        action_required.append("WORKER_STOPPED_DURING_ACTIVE_WINDOW")
    if queue["queue_status"] == QUEUE_PENDING and worker["worker_status"] == STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW:
        action_required.append("PENDING_QUEUE_WITHOUT_ACTIVE_WORKER")
    if queue["malformed_row_count"]:
        action_required.append("QUEUE_MALFORMED_ROWS_PRESENT")

    status = ACTION_REQUIRED if action_required else "NOTIFICATION_QUEUE_STATUS_DOCUMENTED"
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        target.isoformat(),
        worker["dead_zone_active"],
        worker["worker_status"],
        worker["lock_status"],
        worker["lock_pid_alive"],
        queue["queue_file_status"],
        queue["queue_status"],
        queue["pending_alert_count"],
        queue["terminal_marker_count"],
        queue["malformed_row_count"],
        sorted(action_required),
    )
    row_key = _stable_hash("notification_queue_dead_zone", source_dependency_signature)

    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-037",
        "target_date": target.isoformat(),
        "checked_at_utc": now.isoformat(),
        "notification_queue_status": status,
        "worker_status": worker["worker_status"],
        "queue_status": queue["queue_status"],
        "dead_zone_active": worker["dead_zone_active"],
        "expected_worker_policy": (
            "STOPPED_ALLOWED_DURING_DEAD_ZONE_CLEANUP"
            if worker["dead_zone_active"]
            else "RUNNING_REQUIRED_DURING_ACTIVE_WINDOW"
        ),
        "watchdog_local_time": worker["local_time"],
        "watchdog_local_day": worker["local_day"],
        "dead_zone_window_local": worker["dead_zone_window_local"],
        "queue_path": str(q_path),
        **queue,
        "lock_path": str(l_path),
        "lock_file_exists": worker["lock_file_exists"],
        "lock_status": worker["lock_status"],
        "lock_pid": worker["lock_pid"],
        "lock_pid_alive": worker["lock_pid_alive"],
        "action_required_codes": sorted(set(action_required)),
        "claim_boundary": (
            "This row classifies notification queue worker state against the "
            "watchdog dead-zone policy only. It does not deliver alerts, "
            "approve restarts, or validate trading behavior."
        ),
        "evidence_class": "CONTROL_ONLY",
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


def status_fields_for_contract() -> tuple[str, ...]:
    return (
        "notification_queue_status",
        "worker_status",
        "queue_status",
        "dead_zone_active",
        "expected_worker_policy",
        "queue_file_status",
        "pending_alert_count",
        "terminal_marker_count",
        "malformed_row_count",
        "lock_status",
        "lock_pid_alive",
        "action_required_codes",
    )
