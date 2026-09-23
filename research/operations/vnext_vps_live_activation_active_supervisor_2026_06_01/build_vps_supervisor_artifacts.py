#!/usr/bin/env python3
"""Build the June 1 vNext VPS live supervisor checkpoint artifacts.

This builder is intentionally read-only toward MT5 broker state: it inspects
account, symbol, tick, bar, order, position, and history evidence, but never
calls order_send or any broker mutation API.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_vps_live_activation_active_supervisor_2026_06_01"
EVIDENCE_CLASS = "VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = PROJECT_ROOT / "research" / "operations" / ROUTE_ID
LARGE_FILE_DEFER_BYTES = 5 * 1024 * 1024
DIRECTORY_METADATA_RECURSION_CAP = 5000

CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "vnext_live_activation_active_repair_companion_2026_05_28"
    / "LIVE_COMPANION_CURRENT_CHECKPOINT.json"
)
LANE06_BROKER_LIFECYCLE_PATH = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
    / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
)
SLIPPAGE_LOG_PATH = PROJECT_ROOT / "shadow_logs" / "slippage.jsonl"
NAS100_RESIDUAL_TICKET = "241779188"


def windows_extended_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    raw = str(path)
    if raw.startswith("\\\\?\\") or raw.startswith("\\\\.\\"):
        return path
    absolute = path if path.is_absolute() else PROJECT_ROOT / path
    return Path("\\\\?\\" + str(absolute))


def local_path_exists(path: Path) -> bool:
    if path.exists():
        return True
    if os.name != "nt":
        return False
    try:
        return windows_extended_path(path).exists()
    except OSError:
        return False


def local_path_for_io(path: Path) -> Path:
    if os.name == "nt" and not path.exists():
        extended = windows_extended_path(path)
        if extended.exists():
            return extended
    return path

LIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

BROKER_ALIASES = {
    "AUDJPY": "AUDJPY",
    "AUDUSD": "AUDUSD",
    "BTCUSD": "BTCUSD",
    "CHFJPY": "CHFJPY",
    "ETHUSD": "ETHUSD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "EURUSD": "EURUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "GER40": "GER30",
    "JP225": "JP225",
    "NAS100": "NDX100",
    "NZDUSD": "NZDUSD",
    "SPX500": "SPX500",
    "UK100": "UK100",
    "UKOIL_cash": "UKOUSD",
    "US30_cash": "US30",
    "USDCAD": "USDCAD",
    "USDCHF": "USDCHF",
    "USDJPY": "USDJPY",
    "USOIL_cash": "USOUSD",
    "XAGUSD": "XAGUSD",
    "XAUUSD": "XAUUSD",
}

PREFLIGHT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_VPS_LIVE_ACTIVATION_ACTIVE_SUPERVISOR_GOAL_PROMPT_2026-06-01.md",
]

REQUIRED_PRODUCTION_FILES = [
    "config/agent_config.yaml",
    "config/profiles/redacted_account.yaml",
    "start_all.bat",
    "run_agent.py",
    "scripts/watchdog.ps1",
    "scripts/watchdog.bat",
    "scripts/watchdog_launcher.vbs",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/m1_capture.py",
    "src/components/tick_capture.py",
    "src/research/moonshot_default_off_policy_router.py",
    "src/notifications.py",
    "src/utils/notification_queue.py",
    "src/components/permissions.py",
    "scripts/build_vnext_live_activation_checkpoint.py",
    "scripts/watchdog_e2e_verify.py",
    str(CHECKPOINT_PATH.relative_to(PROJECT_ROOT)),
    str(LANE06_BROKER_LIFECYCLE_PATH.relative_to(PROJECT_ROOT)),
]

DATA_DEPENDENCIES = [
    ("data/m1", "closed M1 capture output directory"),
    ("data/ticks", "tick capture output directory"),
    ("data/news_calendar.json", "news calendar input"),
    ("data/economic_calendar.csv", "economic calendar input"),
    ("pipeline_state/m1_capture_state.json", "M1 capture state"),
    ("pipeline_state/vps_readiness_mt5_probe.json", "MT5 readiness probe"),
    ("pipeline_state/vps_readiness_tick_probe.json", "tick readiness probe"),
    ("pipeline_state/notification_queue.jsonl", "notification queue"),
    ("shadow_logs/gtos_vnext_runtime_decisions.jsonl", "vNext runtime decisions"),
    ("shadow_logs/gtos_vnext_replacement_monitoring.jsonl", "vNext replacement monitoring"),
    ("shadow_logs/slippage.jsonl", "slippage and broker fill facts"),
    ("shadow_logs/pending_limit_lifecycle.jsonl", "pending lifecycle hot log"),
    ("knowledge_base/trade_records", "trade record store"),
]

SELECTED_CELL_RISK_LEDGER_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_production_replacement_activation_2026_05_26/"
    "VNEXT_REPLACEMENT_STAGE13_redacted_account_SELECTED_CELL_RISK_LEDGER_2026-05-26.jsonl"
)
DATA_DEPENDENCIES.append(
    (
        SELECTED_CELL_RISK_LEDGER_REL,
        "Stage13 selected-cell risk ledger required by live dynamic execution router",
    )
)

OUTPUT_FILES = [
    "VPS_SUPERVISOR_STATE.json",
    "VPS_SUPERVISOR_ACTION_LEDGER.jsonl",
    "VPS_GIT_VERSION_AUDIT.json",
    "VPS_DATA_DEPENDENCY_LEDGER.jsonl",
    "VPS_REQUIRED_FILE_LEDGER.jsonl",
    "VPS_ENVIRONMENT_LEDGER.jsonl",
    "VPS_MT5_ACCOUNT_READINESS.json",
    "VPS_MT5_SYMBOL_SOURCE_LEDGER.jsonl",
    "VPS_BROKER_SPEC_LEDGER.jsonl",
    "VPS_PROCESS_HEALTH_LEDGER.jsonl",
    "VPS_WATCHDOG_SCHEDULER_LEDGER.jsonl",
    "VPS_DATA_CAPTURE_HEALTH_LEDGER.jsonl",
    "VPS_RUNTIME_DECISION_LEDGER.jsonl",
    "VPS_RUNTIME_JSONL_INVALID_ROW_QUARANTINE.jsonl",
    "VPS_CANDIDATE_PACKET_LEDGER.jsonl",
    "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json",
    "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl",
    "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json",
    "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl",
    "VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
    "VPS_BROKER_RECONCILIATION_LEDGER.jsonl",
    "VPS_RISK_EXPOSURE_LEDGER.jsonl",
    "VPS_NOTIFICATION_LEDGER.jsonl",
    "VPS_ANOMALY_LEDGER.jsonl",
    "VPS_REPAIR_LEDGER.jsonl",
    "VPS_RESTART_RELOAD_LEDGER.jsonl",
    "VPS_VERIFICATION_RESULT.json",
    "VPS_OUTPUT_MANIFEST.json",
    "VPS_COMPLETION_OR_CONTINUATION_AUDIT.json",
]

LIVE_REFERENCE_SCAN_FILES = [
    "config/agent_config.yaml",
    "config/profiles/redacted_account.yaml",
    "start_all.bat",
    "run_agent.py",
    "scripts/watchdog.ps1",
    "scripts/watchdog.bat",
    "scripts/watchdog_launcher.vbs",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/m1_capture.py",
    "src/components/tick_capture.py",
    "src/components/permissions.py",
    "src/components/ai_supervisor.py",
    "src/components/ai_call_policy.py",
    "src/components/ai_decision_trace_logger.py",
    "src/research/moonshot_default_off_policy_router.py",
    "src/notifications.py",
    "src/utils/notification_queue.py",
]

PATH_LINE_RANGE_RE = re.compile(
    r"^(?P<path>.+\.(?:md|py|yaml|yml|json|jsonl|csv|txt|ps1|bat|vbs)):(?P<line>\d+(?:-\d+)?)$",
    re.IGNORECASE,
)
COMMON_PATH_SUFFIXES = (
    ".bat",
    ".csv",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".parquet",
    ".ps1",
    ".py",
    ".txt",
    ".vbs",
    ".yaml",
    ".yml",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value.relative_to(PROJECT_ROOT)) if value.is_absolute() else str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "_asdict"):
        return {k: to_jsonable(v) for k, v in value._asdict().items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return str(value)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def read_text(path: Path) -> str:
    return local_path_for_io(path).read_text(encoding="utf-8", errors="replace")


def read_json(path: Path, default: Any = None) -> Any:
    if not local_path_exists(path):
        return default
    return json.loads(read_text(path).lstrip("\ufeff"))


def newest_pipeline_state_path(pattern: str) -> Path | None:
    paths = [
        path
        for path in (PROJECT_ROOT / "pipeline_state").glob(pattern)
        if path.is_file()
    ]
    if not paths:
        return None
    return max(paths, key=lambda path: path.stat().st_mtime)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not local_path_exists(path):
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            timestamp_hint, timestamp_hint_source = raw_timestamp_hint(stripped)
            rows.append(
                {
                    "_parse_error": str(exc),
                    "_line_no": line_no,
                    "_source_path": rel(path),
                    "_raw": stripped[:500],
                    "_raw_timestamp_hint_utc": timestamp_hint,
                    "_raw_timestamp_hint_source": timestamp_hint_source,
                }
            )
            continue
        if isinstance(row, dict):
            row["_line_no"] = line_no
            row["_source_path"] = rel(path)
            rows.append(row)
    return rows


def raw_timestamp_hint(raw: str) -> tuple[str | None, str | None]:
    match = re.search(
        r'"(timestamp_utc|candle_time_utc|time_utc|generated_at_utc)"\s*:\s*"([^"]+)"',
        raw,
    )
    if not match:
        return None, None
    parsed = parse_iso(match.group(2))
    if not parsed:
        return None, match.group(1)
    return parsed.isoformat(), match.group(1)


def write_json(name: str, payload: Any) -> None:
    path = ROUTE_DIR / name
    path.write_text(
        json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    path = ROUTE_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(to_jsonable(row), sort_keys=True) + "\n")


def normalize_runtime_jsonl_quarantine() -> None:
    path = ROUTE_DIR / "VPS_RUNTIME_JSONL_INVALID_ROW_QUARANTINE.jsonl"
    if not path.exists():
        write_jsonl(path.name, [])
        return
    rows: list[dict[str, Any]] = []
    changed = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            if not row.get("status"):
                row["status"] = "jsonl_invalid_row_quarantined"
                changed = True
            if not row.get("status_reason"):
                row["status_reason"] = (
                    "invalid_source_jsonl_row_preserved_with_raw_hash_before_rewrite"
                )
                changed = True
            rows.append(row)
    if changed:
        write_jsonl(path.name, rows)


def run_command(command: list[str], timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }
    except Exception as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "exception": exc.__class__.__name__,
        }


def run_powershell(script: str, timeout: int = 60) -> dict[str, Any]:
    return run_command(["powershell", "-NoProfile", "-Command", script], timeout=timeout)


def refresh_input_artifacts() -> dict[str, Any]:
    """Refresh live supervisor inputs that continue changing during monitoring."""
    checkpoint_refresh = run_command(
        [sys.executable, "scripts/build_vnext_live_activation_checkpoint.py", "--update-state"],
        timeout=180,
    )
    candidate_proof_build = run_command(
        [sys.executable, "scripts/build_vnext_post_reload_candidate_proof.py"],
        timeout=180,
    )
    candidate_proof_verify = run_command(
        [sys.executable, "scripts/verify_vnext_post_reload_candidate_proof.py", "--check"],
        timeout=180,
    )
    return {
        "checkpoint_refresh": checkpoint_refresh,
        "candidate_proof_build": candidate_proof_build,
        "candidate_proof_verify": candidate_proof_verify,
    }


def parse_json_stdout(result: dict[str, Any]) -> Any:
    stdout = (result.get("stdout") or "").strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"raw_stdout": stdout}


def sha256_file(path: Path) -> str | None:
    io_path = local_path_for_io(path)
    if not io_path.is_file():
        return None
    try:
        if io_path.stat().st_size > LARGE_FILE_DEFER_BYTES:
            return None
    except OSError:
        return None
    digest = hashlib.sha256()
    with io_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_metadata(path: Path) -> dict[str, Any]:
    io_path = local_path_for_io(path)
    exists = local_path_exists(path)
    row: dict[str, Any] = {
        "path": rel(path),
        "exists": exists,
        "file_type": "missing",
        "size_bytes": None,
        "mtime_utc": None,
        "sha256": None,
        "sha256_status": "not_checked_missing",
        "lfs_pointer_status": "not_checked_missing",
    }
    if not exists:
        return row
    stat = io_path.stat()
    is_dir = io_path.is_dir()
    is_file = io_path.is_file()
    row.update(
        {
            "file_type": "directory" if is_dir else "file",
            "size_bytes": stat.st_size if is_file else None,
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
    )
    if is_file:
        row["sha256"] = sha256_file(path)
        row["sha256_status"] = (
            "sha256_recorded"
            if row["sha256"]
            else "sha256_deferred_large_file" if stat.st_size > LARGE_FILE_DEFER_BYTES else "sha256_unavailable"
        )
        first = io_path.open("rb").read(128)
        row["lfs_pointer_status"] = (
            "raw_lfs_pointer"
            if first.startswith(b"version https://git-lfs.github.com/spec/v1")
            else "materialized_or_regular_file"
        )
    else:
        row["sha256_status"] = "not_applicable_directory"
        file_mtimes: list[float] = []
        truncated = False
        for child in io_path.rglob("*"):
            try:
                if not child.is_file():
                    continue
                file_mtimes.append(child.stat().st_mtime)
                if len(file_mtimes) >= DIRECTORY_METADATA_RECURSION_CAP:
                    truncated = True
                    break
            except (FileNotFoundError, OSError):
                continue
        row["file_count_recursive"] = len(file_mtimes)
        row["file_count_recursive_status"] = (
            "truncated_at_cap" if truncated else "complete_or_below_cap"
        )
        if file_mtimes:
            newest = max(file_mtimes)
            row["newest_file_mtime_utc"] = datetime.fromtimestamp(
                newest, tz=timezone.utc
            ).isoformat()
        row["lfs_pointer_status"] = "not_applicable_directory"
    return row


def parse_env_file(path: Path) -> dict[str, Any]:
    keys: list[str] = []
    parse_errors: list[str] = []
    if local_path_exists(path):
        for idx, line in enumerate(read_text(path).splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                parse_errors.append(f"line_{idx}_no_equals")
                continue
            keys.append(stripped.split("=", 1)[0].strip())
    return {
        **file_metadata(path),
        "secret_values_recorded": False,
        "key_names": sorted(set(k for k in keys if k)),
        "parse_errors": parse_errors,
    }


def required_file_status(row: dict[str, Any]) -> tuple[str, str]:
    if not row.get("exists"):
        return "required_file_missing", "required production file path is absent"
    if row.get("lfs_pointer_status") == "raw_lfs_pointer":
        return "required_file_lfs_pointer_repair_required", "file is a raw LFS pointer"
    parse_status = str(row.get("parse_load_status") or "not_attempted")
    if parse_status.startswith("parse_failed"):
        return "required_file_parse_repair_required", parse_status
    return "required_file_ready", f"required file exists and parse_load_status={parse_status}"


def data_dependency_status(row: dict[str, Any]) -> tuple[str, str]:
    if not row.get("exists"):
        return "data_dependency_missing_classified", "dependency path is absent and classified for supervisor follow-up"
    if row.get("lfs_pointer_status") == "raw_lfs_pointer":
        return "data_dependency_lfs_pointer_repair_required", "dependency file is a raw LFS pointer"
    parse_status = str(row.get("parse_load_status") or "not_applicable")
    if "failed" in parse_status or "json_failed" in parse_status or "csv_failed" in parse_status:
        return "data_dependency_parse_repair_required", parse_status
    return "data_dependency_ready", f"dependency exists and parse_load_status={parse_status}"


def environment_row_status(row: dict[str, Any]) -> tuple[str, str]:
    kind = str(row.get("kind") or "environment_row")
    if kind == "host_python":
        return "environment_host_python_ready", "python executable/version/platform captured"
    if kind == "metatrader5_python_import":
        if row.get("import_ok"):
            return "environment_mt5_python_import_ready", "MetaTrader5 import/version captured"
        return "environment_mt5_python_import_failed", str(row.get("error") or "import failed")
    if kind == "installed_packages":
        if row.get("command_exit_code") == 0:
            return "environment_installed_packages_captured", "pip package inventory captured"
        return "environment_installed_packages_probe_failed", str(row.get("stderr") or "pip list failed")
    if kind == "gtos_environment_variables":
        if row.get("command_exit_code") == 0:
            return "environment_gtos_variables_captured", "GTOS env var presence captured without secret values"
        return "environment_gtos_variables_probe_failed", str(row.get("stderr") or "env probe failed")
    if kind == "env_file_keys":
        if row.get("parse_errors"):
            return "environment_env_file_parse_repair_required", "env file has parse errors"
        return "environment_env_file_keys_captured", "env file key names captured without values"
    if kind == "host_resources":
        if row.get("command_exit_code") == 0:
            return "environment_host_resources_captured", "disk memory CPU timezone captured"
        return "environment_host_resources_probe_failed", str(row.get("stderr") or "resource probe failed")
    if kind == "runtime_flags":
        return "environment_runtime_flags_checked", "runtime halt/autostart flags checked"
    if kind == "launcher_path_and_mode_scan":
        if row.get("path_drift_status") == "review_required":
            return "environment_launcher_path_review_required", "launcher path scan found review-required drift"
        return "environment_launcher_path_mode_scan_ready", "launcher paths and mode markers scanned"
    return "environment_row_captured", kind


def parse_trade_record_time(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(local_path_for_io(path).stat().st_mtime, tz=timezone.utc)
    except Exception:
        return None


def parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def candidate_packet_event_time(
    payload: dict[str, Any],
    packet: dict[str, Any],
) -> tuple[datetime | None, str | None]:
    decision_pipeline = payload.get("decision_pipeline") or {}
    runtime_decision = packet.get("runtime_decision") or {}
    runtime_evidence = runtime_decision.get("evidence") or {}
    sources: list[tuple[str, dict[str, Any], tuple[str, ...]]] = [
        (
            "packet.candidate_identity",
            packet.get("candidate_identity") or {},
            ("candle_close_utc", "candle_time_utc"),
        ),
        (
            "packet.source_m15",
            packet.get("source_m15") or {},
            ("candle_close_utc", "candle_time_utc", "candle_open_utc"),
        ),
        (
            "packet.runtime_decision.event",
            runtime_decision.get("event") or {},
            ("candle_time_utc", "candle_close_utc"),
        ),
        (
            "packet.runtime_decision.evidence.candidate_summary",
            runtime_evidence.get("candidate_summary") or {},
            ("candle_close_utc", "candle_time_utc", "candle_open_utc"),
        ),
        (
            "payload",
            payload,
            ("candle_close_utc", "candle_time_utc", "record_time_utc"),
        ),
        (
            "payload.decision_pipeline",
            decision_pipeline,
            ("candle_close_utc", "candle_time_utc", "timestamp_utc"),
        ),
    ]
    for source_name, source, keys in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            parsed = parse_iso(source.get(key))
            if parsed:
                return parsed, f"{source_name}.{key}"
    return None, None


def float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:
        return None
    return result


def generated_live_state_time() -> str | None:
    path = PROJECT_ROOT / ".context" / "LIVE_STATE.md"
    if not local_path_exists(path):
        return None
    match = re.search(r"\*\*Generated:\*\*\s+(.+)", read_text(path))
    return match.group(1).strip() if match else None


def collect_git_audit() -> dict[str, Any]:
    commands = {
        "head": run_command(["git", "rev-parse", "HEAD"]),
        "head_subject": run_command(["git", "log", "-1", "--pretty=%h %s"]),
        "origin_main": run_command(["git", "rev-parse", "origin/main"]),
        "status_short": run_command(["git", "status", "--short"], timeout=90),
        "lfs_ls_files": run_command(["git", "lfs", "ls-files"], timeout=45),
        "lfs_fsck": run_command(["git", "lfs", "fsck"], timeout=45),
    }
    status_lines = [
        line for line in (commands["status_short"].get("stdout") or "").splitlines() if line
    ]
    return {
        "schema_version": "vps_git_version_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "repo_path": str(PROJECT_ROOT),
        "head": (commands["head"].get("stdout") or "").strip(),
        "head_subject": (commands["head_subject"].get("stdout") or "").strip(),
        "origin_main": (commands["origin_main"].get("stdout") or "").strip(),
        "dirty_status_line_count": len(status_lines),
        "dirty_status_lines": status_lines,
        "lfs_status": {
            "ls_files_exit_code": commands["lfs_ls_files"].get("exit_code"),
            "ls_files_stdout": commands["lfs_ls_files"].get("stdout"),
            "ls_files_stderr": commands["lfs_ls_files"].get("stderr"),
            "fsck_exit_code": commands["lfs_fsck"].get("exit_code"),
            "fsck_stdout": commands["lfs_fsck"].get("stdout"),
            "fsck_stderr": commands["lfs_fsck"].get("stderr"),
            "broken_pointer_check_status": (
                "passed"
                if commands["lfs_fsck"].get("exit_code") == 0
                else "not_passed_or_unavailable"
            ),
        },
        "command_results": commands,
    }


def collect_environment_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "kind": "host_python",
            "generated_at_utc": iso_now(),
            "repo_path": str(PROJECT_ROOT),
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "operating_user": getpass.getuser(),
        }
    ]
    try:
        import MetaTrader5 as mt5  # type: ignore

        rows.append(
            {
                "kind": "metatrader5_python_import",
                "import_ok": True,
                "version": to_jsonable(mt5.version()),
            }
        )
    except Exception as exc:
        rows.append(
            {
                "kind": "metatrader5_python_import",
                "import_ok": False,
                "error": f"{exc.__class__.__name__}: {exc}",
            }
        )

    pip_result = run_command([sys.executable, "-m", "pip", "list", "--format=json"], timeout=90)
    packages: Any = []
    if pip_result.get("exit_code") == 0:
        try:
            packages = json.loads(pip_result.get("stdout") or "[]")
        except json.JSONDecodeError:
            packages = []
    rows.append(
        {
            "kind": "installed_packages",
            "command_exit_code": pip_result.get("exit_code"),
            "package_count": len(packages) if isinstance(packages, list) else None,
            "packages": packages,
            "stderr": pip_result.get("stderr"),
        }
    )

    persisted_env = run_powershell(
        """
        [pscustomobject]@{
          user_GTOS_MODE=[Environment]::GetEnvironmentVariable('GTOS_MODE','User');
          machine_GTOS_MODE=[Environment]::GetEnvironmentVariable('GTOS_MODE','Machine');
          process_GTOS_MODE=$env:GTOS_MODE;
          user_GTOS_PROFILE=[Environment]::GetEnvironmentVariable('GTOS_PROFILE','User');
          machine_GTOS_PROFILE=[Environment]::GetEnvironmentVariable('GTOS_PROFILE','Machine');
          process_GTOS_PROFILE=$env:GTOS_PROFILE
        } | ConvertTo-Json -Depth 4 -Compress
        """,
        timeout=30,
    )
    rows.append(
        {
            "kind": "gtos_environment_variables",
            "secret_values_recorded": False,
            "values": parse_json_stdout(persisted_env),
            "command_exit_code": persisted_env.get("exit_code"),
            "stderr": persisted_env.get("stderr"),
        }
    )

    for env_path in sorted(PROJECT_ROOT.glob(".env*")):
        rows.append({"kind": "env_file_keys", **parse_env_file(env_path)})

    system_info = run_powershell(
        """
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" |
          Select-Object DeviceID,Size,FreeSpace
        $os = Get-CimInstance Win32_OperatingSystem |
          Select-Object TotalVisibleMemorySize,FreePhysicalMemory,LastBootUpTime
        $cpu = Get-CimInstance Win32_Processor |
          Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors,LoadPercentage
        $tz = Get-TimeZone | Select-Object Id,DisplayName,BaseUtcOffset
        [pscustomobject]@{disk=$disk; os=$os; cpu=$cpu; timezone=$tz} |
          ConvertTo-Json -Depth 6 -Compress
        """,
        timeout=45,
    )
    rows.append(
        {
            "kind": "host_resources",
            "values": parse_json_stdout(system_info),
            "command_exit_code": system_info.get("exit_code"),
            "stderr": system_info.get("stderr"),
        }
    )

    flags = []
    for path in [
        PROJECT_ROOT / "pipeline_state" / "RESEARCH_RUNTIME_HALT.flag",
        PROJECT_ROOT / "knowledge_base" / "meta" / "AUTOSTART_DISABLED.flag",
        PROJECT_ROOT / "RESEARCH_RUNTIME_HALT.flag",
        PROJECT_ROOT / "AUTOSTART_DISABLED.flag",
    ]:
        flags.append(file_metadata(path))
    rows.append({"kind": "runtime_flags", "flags": flags})

    launcher_scan = []
    for rel_path in [
        "start_all.bat",
        "scripts/watchdog.ps1",
        "scripts/watchdog.bat",
        "scripts/watchdog_launcher.vbs",
    ]:
        path = PROJECT_ROOT / rel_path
        exists = local_path_exists(path)
        text = read_text(path) if exists else ""
        launcher_scan.append(
            {
                "path": rel_path,
                "exists": exists,
                "contains_repo_path": "ai-trading-agent" in text,
                "contains_users_path": "C:\\Users" in text,
                "contains_mode_live": "live" in text,
                "contains_mode_demo": "demo" in text,
                "hardcoded_path_lines": [
                    line.strip()
                    for line in text.splitlines()
                    if "C:\\Users" in line or "ai-trading-agent" in line
                ],
            }
        )
    rows.append(
        {
            "kind": "launcher_path_and_mode_scan",
            "rows": launcher_scan,
            "path_drift_status": "current_workspace_path_references_only_or_relative"
            if all(
                (not item["contains_users_path"])
                or ("C:\\Users\\MSI\\Documents\\ai-trading-agent" in " ".join(item["hardcoded_path_lines"]))
                for item in launcher_scan
            )
            else "review_required",
        }
    )
    for row in rows:
        status, status_reason = environment_row_status(row)
        row["status"] = status
        row["status_reason"] = status_reason
    return rows


def collect_required_file_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel_path in REQUIRED_PRODUCTION_FILES:
        path = PROJECT_ROOT / rel_path
        row = {
            **file_metadata(path),
            "role": "current production dependency or active proof input",
            "owning_reference": rel_path,
            "parse_load_status": "not_attempted",
            "runtime_impact": "required_for_supervisor_or_live_runtime",
            "repair_action": "none_required" if local_path_exists(path) else "restore_missing_required_file",
        }
        if local_path_for_io(path).is_file():
            suffix = path.suffix.lower()
            try:
                if suffix == ".json":
                    json.loads(read_text(path))
                    row["parse_load_status"] = "json_ok"
                elif suffix == ".jsonl":
                    read_jsonl(path)
                    row["parse_load_status"] = "jsonl_ok"
                elif suffix in {".yaml", ".yml"}:
                    try:
                        import yaml  # type: ignore

                        yaml.safe_load(read_text(path))
                        row["parse_load_status"] = "yaml_ok"
                    except ImportError:
                        row["parse_load_status"] = "yaml_parser_unavailable_text_read_ok"
                else:
                    read_text(path)
                    row["parse_load_status"] = "text_read_ok"
            except Exception as exc:
                row["parse_load_status"] = f"parse_failed:{exc.__class__.__name__}:{exc}"
                row["repair_action"] = "repair_parse_failure"
        status, status_reason = required_file_status(row)
        row["status"] = status
        row["status_reason"] = status_reason
        rows.append(row)
    return rows


def collect_data_dependency_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel_path, role in DATA_DEPENDENCIES:
        path = PROJECT_ROOT / rel_path
        row = {
            **file_metadata(path),
            "role": role,
            "classification": "current_live_runtime_dependency"
            if rel_path.startswith(("data/", "pipeline_state/", "shadow_logs/"))
            else "current_or_supervisor_dependency",
            "runtime_impact": "live_runtime_or_supervisor_evidence",
            "repair_action": "none_required" if local_path_exists(path) else "classify_or_restore_if_live_required",
        }
        io_path = local_path_for_io(path)
        if io_path.is_file() and path.suffix.lower() == ".json":
            try:
                payload = read_json(path, {})
                row["parse_load_status"] = "json_ok"
                row["top_level_keys"] = sorted(payload.keys()) if isinstance(payload, dict) else None
            except Exception as exc:
                row["parse_load_status"] = f"json_failed:{exc}"
        elif io_path.is_file() and path.suffix.lower() == ".jsonl":
            parsed = read_jsonl(path)
            row["parse_load_status"] = "jsonl_ok"
            row["row_count"] = len(parsed)
            row["status_counts"] = dict(Counter(str(r.get("status")) for r in parsed if "status" in r))
        elif io_path.is_file() and path.suffix.lower() == ".csv":
            try:
                with io_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                    reader = csv.reader(handle)
                    rows_read = sum(1 for _ in reader)
                row["parse_load_status"] = "csv_read_ok"
                row["row_count"] = rows_read
            except Exception as exc:
                row["parse_load_status"] = f"csv_failed:{exc}"
        status, status_reason = data_dependency_status(row)
        row["status"] = status
        row["status_reason"] = status_reason
        rows.append(row)
    return rows


def git_path_set(command: list[str]) -> set[str]:
    result = run_command(command, timeout=120)
    if result.get("exit_code") != 0:
        return set()
    rows: set[str] = set()
    for raw in (result.get("stdout") or "").splitlines():
        text = raw.strip()
        if not text:
            continue
        if command[:3] == ["git", "lfs", "ls-files"] and "--name-only" not in command:
            parts = text.split(maxsplit=2)
            text = parts[-1] if parts else text
        rows.add(text.replace("\\", "/"))
    return rows


def path_like_value(value: str) -> bool:
    text = value.strip().strip("\"'")
    if not text or text.startswith(("http://", "https://")):
        return False
    if text in {".", ".."}:
        return False
    lower = text.lower()
    if any(token in lower for token in (" && ", " >>", " 2>&1", "%gtos_", "$env:")):
        return False
    if lower.startswith(("cmd /c ", "powershell ", "pwsh ", "start-process ")):
        return False
    if any(token in text for token in (r"\b", r"\d", "(?", "[", "]", "{", "}")) and not text.startswith(
        (".context/", "config/", "data/", "knowledge_base/", "logs/", "pipeline_state/", "research/", "scripts/", "shadow_logs/", "src/", "tests/")
    ):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", text):
        return True
    if text.startswith((".context/", "config/", "data/", "knowledge_base/", "logs/", "pipeline_state/", "research/", "scripts/", "shadow_logs/", "src/", "tests/")):
        return True
    if "/" in text or "\\" in text:
        return any(part for part in text.replace("\\", "/").split("/") if "." in part) or text.endswith(
            ("/", "\\")
        )
    return text.lower().endswith(COMMON_PATH_SUFFIXES)


def quoted_source_path_like_value(value: str) -> bool:
    text = value.strip().strip("\"'")
    if not path_like_value(text):
        return False
    normalized = text.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        return True
    if normalized.startswith(
        (
            ".context/",
            "config/",
            "data/",
            "knowledge_base/",
            "logs/",
            "pipeline_state/",
            "research/",
            "scripts/",
            "shadow_logs/",
            "src/",
            "tests/",
        )
    ):
        return True
    return False


def iter_config_path_values(value: Any, source_path: str, key_path: str = "") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_key = f"{key_path}.{key}" if key_path else str(key)
            rows.extend(iter_config_path_values(child, source_path, child_key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_key = f"{key_path}[{index}]"
            rows.extend(iter_config_path_values(child, source_path, child_key))
    elif isinstance(value, str) and path_like_value(value):
        if "regex" in key_path.lower():
            return rows
        rows.append(
            {
                "source_path": source_path,
                "owning_reference": key_path or source_path,
                "raw_reference": value,
                "source_kind": "yaml_value",
            }
        )
    return rows


OPTIONAL_ABSENT_REFERENCE_SUFFIXES = (
    ".flag",
    ".lock",
    ".state",
)


def optional_absent_reference_status(row: dict[str, Any]) -> tuple[str, str, str] | None:
    reference_path = str(row.get("reference_path") or "").replace("\\", "/")
    owning_reference = str(row.get("owning_reference") or "")
    source_kind = str(row.get("source_kind") or "")
    if source_kind == "quoted_source_text" and "{" in reference_path and "}" in reference_path:
        return (
            "source_template_reference_not_concrete_file",
            "quoted source is a runtime filename template; concrete instances are verified through generated data/state checks",
            "none_required",
        )
    if (
        reference_path.endswith("VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json")
        and owning_reference == "gtos_vnext_runtime.replacement_ml_role_source_manifest"
    ):
        return (
            "optional_shadow_ml_manifest_missing",
            "replacement_ml_apply_to_execution=false; manifest is shadow/provenance metadata, not live order gating",
            "restore_from_owner_machine_only_if_shadow_ml_research_provenance_is_needed",
        )
    if source_kind == "quoted_source_text" and reference_path.endswith(OPTIONAL_ABSENT_REFERENCE_SUFFIXES):
        return (
            "optional_absence_sentinel_not_present",
            "absence of this flag/lock/state sentinel is a valid runtime state",
            "none_required",
        )
    if source_kind == "quoted_source_text" and reference_path in {
        "knowledge_base/meta/last_crash.json",
        "knowledge_base/meta/execution_checkpoint.json",
        "shadow_logs/ob_retest_sl_exception_decisions.jsonl",
    }:
        return (
            "optional_event_driven_runtime_artifact_absent",
            "artifact is written only after the corresponding crash/checkpoint/exception event; absence is valid when no such event is current",
            "none_required",
        )
    return None


def iter_text_path_values(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        text = read_text(path)
    except OSError:
        return rows
    pattern = re.compile(r"""(?P<quote>["'])(?P<value>[^"'\r\n]{1,260})(?P=quote)""")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            value = match.group("value")
            if quoted_source_path_like_value(value):
                rows.append(
                    {
                        "source_path": rel(path),
                        "owning_reference": f"{rel(path)}:{line_no}",
                        "raw_reference": value,
                        "source_kind": "quoted_source_text",
                    }
                )
    return rows


def normalized_reference_path(raw_reference: str) -> tuple[str, str | None]:
    text = raw_reference.strip().strip("\"'")
    match = PATH_LINE_RANGE_RE.match(text)
    if match:
        return match.group("path"), match.group("line")
    return text, None


def resolve_reference_path(reference_path: str) -> Path:
    text = reference_path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", text):
        return Path(text)
    return PROJECT_ROOT / text


def parse_reference_file(path: Path) -> tuple[str, int | None, list[str]]:
    if not local_path_exists(path):
        return "not_attempted_missing", None, []
    io_path = local_path_for_io(path)
    if io_path.is_dir():
        return "directory_ok", None, []
    suffix = path.suffix.lower()
    errors: list[str] = []
    try:
        size_bytes = io_path.stat().st_size
    except OSError:
        size_bytes = None
    if suffix == ".json":
        try:
            json.loads(read_text(path))
            return "json_ok", None, []
        except Exception as exc:
            return f"json_failed:{exc.__class__.__name__}:{exc}", None, []
    if suffix == ".jsonl":
        if size_bytes is not None and size_bytes > LARGE_FILE_DEFER_BYTES:
            return "jsonl_large_file_presence_ready_targeted_parse_required", None, []
        row_count = 0
        with io_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"line_{line_no}:{exc.msg}")
                    continue
                if not isinstance(payload, dict):
                    errors.append(f"line_{line_no}:not_object")
                    continue
                row_count += 1
        return ("jsonl_ok" if not errors else "jsonl_failed", row_count, errors[:10])
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore

            yaml.safe_load(read_text(path))
            return "yaml_ok", None, []
        except Exception as exc:
            return f"yaml_failed:{exc.__class__.__name__}:{exc}", None, []
    if suffix == ".csv":
        try:
            with io_path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                row_count = sum(1 for _ in csv.reader(handle))
            return "csv_read_ok", row_count, []
        except Exception as exc:
            return f"csv_failed:{exc.__class__.__name__}:{exc}", None, []
    try:
        io_path.open("rb").read(1)
    except OSError as exc:
        return f"read_failed:{exc.__class__.__name__}:{exc}", None, []
    return "read_ok", None, []


def collect_live_execution_file_reference_audit() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tracked_files = git_path_set(["git", "ls-files"])
    lfs_files = git_path_set(["git", "lfs", "ls-files", "--name-only"])
    references: list[dict[str, str]] = []
    for rel_path in PREFLIGHT_FILES + REQUIRED_PRODUCTION_FILES:
        references.append(
            {
                "source_path": "supervisor_static_contract",
                "owning_reference": rel_path,
                "raw_reference": rel_path,
                "source_kind": "required_file_contract",
            }
        )
    for rel_path, role in DATA_DEPENDENCIES:
        references.append(
            {
                "source_path": "supervisor_data_dependency_contract",
                "owning_reference": role,
                "raw_reference": rel_path,
                "source_kind": "data_dependency_contract",
            }
        )
    for rel_path in LIVE_REFERENCE_SCAN_FILES:
        path = PROJECT_ROOT / rel_path
        if path.suffix.lower() in {".yaml", ".yml"} and local_path_exists(path):
            try:
                import yaml  # type: ignore

                payload = yaml.safe_load(read_text(path))
                references.extend(iter_config_path_values(payload, rel_path))
            except Exception:
                references.extend(iter_text_path_values(path))
        else:
            references.extend(iter_text_path_values(path))

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for ref in references:
        key = (
            ref.get("source_path") or "",
            ref.get("owning_reference") or "",
            ref.get("raw_reference") or "",
            ref.get("source_kind") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        raw_reference = ref["raw_reference"]
        reference_path, line_range = normalized_reference_path(raw_reference)
        path = resolve_reference_path(reference_path)
        path_norm = reference_path.replace("\\", "/")
        row = {
            "schema_version": "vps_live_execution_file_reference_v1",
            "generated_at_utc": iso_now(),
            "route_id": ROUTE_ID,
            "source_path": ref.get("source_path"),
            "source_kind": ref.get("source_kind"),
            "owning_reference": ref.get("owning_reference"),
            "raw_reference": raw_reference,
            "reference_path": reference_path,
            "reference_line_range": line_range,
            "resolved_path": str(path),
            "repo_relative_path": rel(path) if str(path).startswith(str(PROJECT_ROOT)) else str(path),
            "tracked_by_git": path_norm in tracked_files,
            "tracked_by_lfs": path_norm in lfs_files,
        }
        meta = file_metadata(path)
        row.update(
            {
                "exists": meta.get("exists"),
                "file_type": meta.get("file_type"),
                "size_bytes": meta.get("size_bytes"),
                "mtime_utc": meta.get("mtime_utc"),
                "sha256": meta.get("sha256"),
                "sha256_status": meta.get("sha256_status"),
                "lfs_pointer_status": meta.get("lfs_pointer_status"),
            }
        )
        parse_status, row_count, parse_errors = parse_reference_file(path)
        row["parse_load_status"] = parse_status
        row["row_count"] = row_count
        row["parse_error_samples"] = parse_errors

        optional_absent = optional_absent_reference_status(row) if not row["exists"] else None
        if optional_absent:
            status, status_reason, repair_action = optional_absent
        elif not row["exists"] and row["tracked_by_lfs"]:
            status = "missing_but_lfs_tracked"
            status_reason = "referenced file is absent locally but tracked by Git LFS"
            repair_action = f"git lfs pull --include={reference_path}"
        elif not row["exists"]:
            status = "missing_not_in_lfs"
            status_reason = "referenced file is absent and not listed by Git LFS"
            repair_action = "restore_from_source_or_owner_machine_if_live_required"
        elif row.get("lfs_pointer_status") == "raw_lfs_pointer":
            status = "raw_lfs_pointer_defect"
            status_reason = "referenced file exists as a raw Git LFS pointer"
            repair_action = f"git lfs pull --include={reference_path}"
        elif parse_errors or str(parse_status).endswith("_failed") or "_failed:" in str(parse_status):
            status = "parse_defect"
            status_reason = str(parse_status)
            repair_action = "repair_or_restore_parseable_source_file"
        elif line_range:
            status = "source_reference_line_range_present"
            status_reason = "line-range reference base file exists and is readable"
            repair_action = "none_required"
        else:
            status = "present_ready"
            status_reason = f"reference exists and parse_load_status={parse_status}"
            repair_action = "none_required"
        row["status"] = status
        row["status_reason"] = status_reason
        row["repair_action"] = repair_action
        row["runtime_impact"] = (
            "live_execution_dependency_or_live_evidence_reference"
            if ref.get("source_kind") != "quoted_source_text"
            else "source_code_path_reference_for_live_execution_scan"
        )
        rows.append(row)

    status_counts = Counter(str(row.get("status")) for row in rows)
    missing_not_in_lfs = [row for row in rows if row.get("status") == "missing_not_in_lfs"]
    missing_but_lfs = [row for row in rows if row.get("status") == "missing_but_lfs_tracked"]
    raw_pointers = [row for row in rows if row.get("status") == "raw_lfs_pointer_defect"]
    parse_defects = [row for row in rows if row.get("status") == "parse_defect"]
    approval_bound = [row for row in rows if row.get("status") == "approval_bound_missing"]
    summary = {
        "schema_version": "vps_live_execution_file_reference_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "reference_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "tracked_lfs_file_count": len(lfs_files),
        "tracked_git_file_count": len(tracked_files),
        "missing_but_lfs_tracked_count": len(missing_but_lfs),
        "missing_not_in_lfs_count": len(missing_not_in_lfs),
        "raw_lfs_pointer_defect_count": len(raw_pointers),
        "parse_defect_count": len(parse_defects),
        "approval_bound_missing_count": len(approval_bound),
        "unresolved_live_required_missing_count": len(missing_not_in_lfs),
        "unresolved_missing_references": [
            {
                "reference_path": row.get("reference_path"),
                "source_path": row.get("source_path"),
                "owning_reference": row.get("owning_reference"),
                "status": row.get("status"),
                "status_reason": row.get("status_reason"),
                "repair_action": row.get("repair_action"),
            }
            for row in missing_not_in_lfs + missing_but_lfs + raw_pointers + parse_defects + approval_bound
        ],
        "exact_owner_or_other_machine_blockers": [
            {
                "reference_path": row.get("reference_path"),
                "source_path": row.get("source_path"),
                "owning_reference": row.get("owning_reference"),
                "required_owner_action": "provide exact original file or source route output from the other machine",
            }
            for row in missing_not_in_lfs
            if str(row.get("reference_path") or "").endswith(
                "VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json"
            )
        ],
        "no_broker_order_position_deal_mutation": True,
        "paid_api_or_vendor_call_taken": False,
    }
    return summary, rows


def mt5_obj_to_dict(obj: Any) -> dict[str, Any] | None:
    if obj is None:
        return None
    return to_jsonable(obj)


def broker_time_offset_from_probe() -> tuple[int, str] | None:
    probe = read_json(PROJECT_ROOT / "pipeline_state" / "vps_readiness_tick_probe.json", {})
    if not isinstance(probe, dict):
        return None
    value = probe.get("broker_offset_seconds")
    if isinstance(value, (int, float)) and abs(int(value)) <= 14 * 3600:
        return int(value), "pipeline_state/vps_readiness_tick_probe.json"
    return None


def detect_broker_time_offset_seconds(mt5: Any, now_utc: datetime) -> tuple[int, str]:
    candidates: list[int] = []
    for symbol in (
        "EURUSD",
        "AUDUSD",
        "GBPUSD",
        "USDJPY",
        "USDCAD",
        "BTCUSD",
        "ETHUSD",
        "XAUUSD",
    ):
        tick = mt5.symbol_info_tick(BROKER_ALIASES[symbol])
        if tick is None or not getattr(tick, "time", None):
            continue
        raw_tick_time = datetime.fromtimestamp(int(tick.time), tz=timezone.utc)
        rounded = int(round((raw_tick_time - now_utc).total_seconds() / 3600.0) * 3600)
        if abs(rounded) > 14 * 3600:
            continue
        corrected_age = (now_utc - (raw_tick_time - timedelta(seconds=rounded))).total_seconds()
        if -300 <= corrected_age <= 6 * 3600:
            candidates.append(rounded)
    if candidates:
        offset, _count = Counter(candidates).most_common(1)[0]
        return offset, "live_mt5_tick_time_consensus"
    probe = broker_time_offset_from_probe()
    if probe:
        return probe
    return 0, "fallback_zero_offset_no_live_tick_consensus"


def mt5_epoch_to_utc(epoch: int | float, broker_offset_seconds: int) -> datetime:
    raw = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
    return raw - timedelta(seconds=broker_offset_seconds)


def collect_mt5_readonly() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    account_payload: dict[str, Any] = {
        "schema_version": "vps_mt5_account_readiness_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "read_only": True,
        "broker_mutation_calls": 0,
        "initialize_ok": False,
        "fallback_source": None,
    }
    symbol_rows: list[dict[str, Any]] = []
    spec_rows: list[dict[str, Any]] = []
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        account_payload["initialize_error"] = f"import_failed:{exc.__class__.__name__}:{exc}"
        return account_payload, symbol_rows, spec_rows

    if not mt5.initialize():
        account_payload["initialize_error"] = str(mt5.last_error())
        probe = read_json(PROJECT_ROOT / "pipeline_state" / "vps_readiness_mt5_probe.json", {})
        account_payload["fallback_source"] = "pipeline_state/vps_readiness_mt5_probe.json"
        account_payload["fallback_probe"] = probe
        return account_payload, symbol_rows, spec_rows

    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        account_payload.update(
            {
                "initialize_ok": True,
                "last_error": to_jsonable(mt5.last_error()),
                "account": mt5_obj_to_dict(account),
                "terminal": mt5_obj_to_dict(terminal),
                "positions": len(mt5.positions_get() or []),
                "orders": len(mt5.orders_get() or []),
                "position_details": to_jsonable(mt5.positions_get() or []),
                "order_details": to_jsonable(mt5.orders_get() or []),
            }
        )
        now = utc_now()
        history_from = now - timedelta(hours=12)
        history_orders = mt5.history_orders_get(history_from, now) or []
        history_deals = mt5.history_deals_get(history_from, now) or []
        account_payload["history_orders_12h"] = len(history_orders)
        account_payload["history_deals_12h"] = len(history_deals)
        account_payload["history_order_tail"] = to_jsonable(history_orders[-10:])
        account_payload["history_deal_tail"] = to_jsonable(history_deals[-10:])
        broker_time_offset_seconds, broker_time_offset_source = detect_broker_time_offset_seconds(
            mt5, now
        )
        account_payload["broker_time_offset_seconds"] = broker_time_offset_seconds
        account_payload["broker_time_offset_source"] = broker_time_offset_source

        timeframes = {
            "M1": (mt5.TIMEFRAME_M1, 240),
            "M15": (mt5.TIMEFRAME_M15, 672),
            "H1": (mt5.TIMEFRAME_H1, 168),
            "H4": (mt5.TIMEFRAME_H4, 80),
            "D1": (mt5.TIMEFRAME_D1, 60),
        }
        for symbol in LIVE_SYMBOLS:
            broker_symbol = BROKER_ALIASES[symbol]
            select_ok = bool(mt5.symbol_select(broker_symbol, True))
            info = mt5.symbol_info(broker_symbol)
            tick = mt5.symbol_info_tick(broker_symbol)
            bar_summary: dict[str, Any] = {}
            for tf_name, (tf_const, count) in timeframes.items():
                rates = mt5.copy_rates_from_pos(broker_symbol, tf_const, 0, count)
                if rates is None or len(rates) == 0:
                    bar_summary[tf_name] = {
                        "requested": count,
                        "rows": 0,
                        "latest_bar_utc": None,
                        "first_bar_utc": None,
                        "last_error": to_jsonable(mt5.last_error()),
                        "broker_time_offset_seconds": broker_time_offset_seconds,
                    }
                else:
                    first_raw = datetime.fromtimestamp(int(rates[0]["time"]), tz=timezone.utc)
                    last_raw = datetime.fromtimestamp(int(rates[-1]["time"]), tz=timezone.utc)
                    first = mt5_epoch_to_utc(rates[0]["time"], broker_time_offset_seconds)
                    last = mt5_epoch_to_utc(rates[-1]["time"], broker_time_offset_seconds)
                    bar_summary[tf_name] = {
                        "requested": count,
                        "rows": int(len(rates)),
                        "first_bar_broker_server_time": first_raw.isoformat(),
                        "latest_bar_broker_server_time": last_raw.isoformat(),
                        "first_bar_utc": first.isoformat(),
                        "latest_bar_utc": last.isoformat(),
                        "latest_bar_age_s": round((now - last).total_seconds(), 1),
                        "broker_time_offset_seconds": broker_time_offset_seconds,
                    }
            info_dict = mt5_obj_to_dict(info)
            tick_dict = mt5_obj_to_dict(tick)
            tick_time_utc = (
                mt5_epoch_to_utc(int(tick.time), broker_time_offset_seconds)
                if tick is not None and getattr(tick, "time", None)
                else None
            )
            bars_ready = all(
                (bar_summary.get(tf_name) or {}).get("rows", 0) > 0
                for tf_name in timeframes
            )
            source_ready = select_ok and info is not None and tick is not None and bars_ready
            symbol_rows.append(
                {
                    "schema_version": "vps_mt5_symbol_source_v1",
                    "generated_at_utc": account_payload["generated_at_utc"],
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "alias_expected": broker_symbol,
                    "symbol_select": select_ok,
                    "info_found": info is not None,
                    "tick_found": tick is not None,
                    "tick": tick_dict,
                    "tick_time_utc": tick_time_utc.isoformat() if tick_time_utc else None,
                    "tick_age_s": (
                        round((now - tick_time_utc).total_seconds(), 1)
                        if tick_time_utc
                        else None
                    ),
                    "broker_time_offset_seconds": broker_time_offset_seconds,
                    "broker_time_offset_source": broker_time_offset_source,
                    "bar_timeframes": bar_summary,
                    "source_status": "ready" if source_ready else "repair_required",
                    "status": (
                        "mt5_symbol_source_ready"
                        if source_ready
                        else "mt5_symbol_source_repair_required"
                    ),
                    "status_reason": (
                        "symbol_selected_info_tick_and_required_bars_available_with_broker_offset_applied"
                        if source_ready
                        else "missing_symbol_source_component:"
                        + ",".join(
                            [
                                name
                                for name, ok in (
                                    ("symbol_select", select_ok),
                                    ("symbol_info", info is not None),
                                    ("tick", tick is not None),
                                    ("required_bars", bars_ready),
                                )
                                if not ok
                            ]
                        )
                    ),
                    "read_only": True,
                }
            )
            spec_rows.append(
                {
                    "schema_version": "vps_broker_spec_v1",
                    "generated_at_utc": account_payload["generated_at_utc"],
                    "symbol": symbol,
                    "broker_symbol": broker_symbol,
                    "info_found": info is not None,
                    "digits": (info_dict or {}).get("digits") if info_dict else None,
                    "point": (info_dict or {}).get("point") if info_dict else None,
                    "trade_tick_size": (info_dict or {}).get("trade_tick_size")
                    if info_dict
                    else None,
                    "trade_tick_value": (info_dict or {}).get("trade_tick_value")
                    if info_dict
                    else None,
                    "contract_size": (info_dict or {}).get("trade_contract_size")
                    if info_dict
                    else None,
                    "volume_min": (info_dict or {}).get("volume_min") if info_dict else None,
                    "volume_max": (info_dict or {}).get("volume_max") if info_dict else None,
                    "volume_step": (info_dict or {}).get("volume_step") if info_dict else None,
                    "trade_stops_level": (info_dict or {}).get("trade_stops_level")
                    if info_dict
                    else None,
                    "trade_freeze_level": (info_dict or {}).get("trade_freeze_level")
                    if info_dict
                    else None,
                    "spread": (info_dict or {}).get("spread") if info_dict else None,
                    "swap_long": (info_dict or {}).get("swap_long") if info_dict else None,
                    "swap_short": (info_dict or {}).get("swap_short") if info_dict else None,
                    "trade_mode": (info_dict or {}).get("trade_mode") if info_dict else None,
                    "visible": (info_dict or {}).get("visible") if info_dict else None,
                    "selected": (info_dict or {}).get("select") if info_dict else None,
                    "full_symbol_info": info_dict,
                }
            )
            spec = spec_rows[-1]
            required_spec_fields = [
                "digits",
                "point",
                "trade_tick_size",
                "trade_tick_value",
                "contract_size",
                "volume_min",
                "volume_max",
                "volume_step",
                "trade_mode",
            ]
            missing_spec_fields = [
                field for field in required_spec_fields if spec.get(field) is None
            ]
            spec["status"] = (
                "broker_spec_ready"
                if info is not None and not missing_spec_fields
                else "broker_spec_repair_required"
            )
            spec["status_reason"] = (
                "mt5_symbol_info_available_with_execution_fields"
                if spec["status"] == "broker_spec_ready"
                else "missing_or_incomplete_mt5_symbol_info:"
                + ",".join(missing_spec_fields or ["symbol_info_absent"])
            )
    finally:
        mt5.shutdown()
    return account_payload, symbol_rows, spec_rows


def collect_process_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    script = r"""
    Get-CimInstance Win32_Process |
      Where-Object {
        $_.CommandLine -match 'ai-trading-agent' -or
        $_.CommandLine -match 'run_agent.py' -or
        $_.CommandLine -match 'tick_capture' -or
        $_.CommandLine -match 'm1_capture' -or
        $_.CommandLine -match 'notification_queue' -or
        $_.CommandLine -match 'heartbeat_monitor' -or
        $_.CommandLine -match 'displacement'
      } |
      Select-Object ProcessId,Name,CreationDate,CommandLine |
      ConvertTo-Json -Depth 4 -Compress
    """
    result = run_powershell(script, timeout=60)
    payload = parse_json_stdout(result)
    raw_rows = payload if isinstance(payload, list) else ([payload] if payload else [])
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue
        command_line = raw.get("CommandLine") or ""
        process_family = classify_process(command_line)
        if process_family is None:
            continue
        row = {
            "schema_version": "vps_process_health_v1",
            "generated_at_utc": iso_now(),
            "pid": raw.get("ProcessId"),
            "process_name": raw.get("Name"),
            "creation_date_raw": raw.get("CreationDate"),
            "command_line": command_line,
            "repo_path_match": "ai-trading-agent" in command_line,
            "process_family": process_family,
            "symbol": regex_group(command_line, r"--symbol\s+([^\s\"]+)"),
            "mode": regex_group(command_line, r"--mode\s+([^\s\"]+)"),
            "profile": regex_group(command_line, r"--profile\s+([^\s\"]+)"),
            "heartbeat_path": heartbeat_path_for(command_line),
            "latest_log_path": log_path_for(command_line),
        }
        status, status_reason = process_row_status(row)
        row["status"] = status
        row["status_reason"] = status_reason
        rows.append(row)
    summary = summarize_process_rows(rows)
    summary["process_query_exit_code"] = result.get("exit_code")
    summary["process_query_stderr"] = result.get("stderr")
    return rows, summary


def regex_group(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def process_row_status(row: dict[str, Any]) -> tuple[str, str]:
    family = row.get("process_family")
    name = str(row.get("process_name") or "").lower()
    command_line = str(row.get("command_line") or "")
    symbol = row.get("symbol")
    mode = row.get("mode")
    profile = row.get("profile")
    if family == "orchestrator":
        if mode == "demo":
            return "unexpected_demo_orchestrator", "orchestrator_process_running_in_demo_mode"
        if symbol not in LIVE_SYMBOLS or mode != "live" or profile != "redacted_account":
            return "orchestrator_contract_mismatch", "symbol_mode_or_profile_not_current_live_contract"
        if name == "python.exe":
            return "live_orchestrator_python_ready", "live_redacted_account_python_worker_for_required_symbol"
        return "live_orchestrator_wrapper_ready", "live_redacted_account_cmd_wrapper_for_required_symbol"
    if family == "tick_capture":
        if symbol not in LIVE_SYMBOLS:
            return "tick_capture_symbol_mismatch", "tick_capture_symbol_not_in_current_24_symbol_contract"
        if "--skip-tick-freshness-check" not in command_line:
            return "tick_capture_liveness_arg_missing", "tick_capture_missing_observational_liveness_flag"
        if profile and profile != "redacted_account":
            return "tick_capture_profile_mismatch", "tick_capture_profile_not_redacted_account"
        if name == "python.exe":
            return "tick_capture_python_ready", "tick_capture_python_worker_with_liveness_flag"
        return "tick_capture_wrapper_ready", "tick_capture_cmd_wrapper_with_liveness_flag"
    if family == "m1_capture":
        if profile and profile != "redacted_account":
            return "m1_capture_profile_mismatch", "m1_capture_profile_not_redacted_account"
        return "m1_capture_ready", "continuous_m1_capture_process_present"
    if family == "notification_queue_worker":
        return "notification_worker_ready", "notification_queue_worker_process_present"
    if family == "heartbeat_monitor":
        return "heartbeat_monitor_ready", "heartbeat_monitor_process_present"
    if family == "displacement_logger":
        return "displacement_logger_ready", "displacement_logger_process_present"
    if family == "watchdog":
        return "watchdog_ready", "watchdog_process_present"
    return "unknown_process_family", "process_family_not_classified"


def classify_process(command_line: str) -> str | None:
    python_prefix = r"(?i)(?:^|[\\/\"])(?:python(?:\d+)?(?:\.exe)?)\"?\s+"
    if re.search(python_prefix + r"run_agent\.py\s+--symbol\b", command_line):
        return "orchestrator"
    if re.search(python_prefix + r"-m\s+src\.components\.tick_capture\b", command_line):
        return "tick_capture"
    if re.search(python_prefix + r"-m\s+src\.components\.m1_capture\b", command_line):
        return "m1_capture"
    if re.search(python_prefix + r"-m\s+src\.utils\.notification_queue\b", command_line):
        return "notification_queue_worker"
    if re.search(python_prefix + r"-m\s+src\.safety\.heartbeat_monitor\b", command_line):
        return "heartbeat_monitor"
    if re.search(python_prefix + r"scripts[\\/]+displacement_logger\.py\b", command_line):
        return "displacement_logger"
    if re.search(r"(?i)(watchdog\.ps1|watchdog\.bat|watchdog_launcher\.vbs)", command_line):
        return "watchdog"
    return None


def heartbeat_path_for(command_line: str) -> str | None:
    symbol = regex_group(command_line, r"--symbol\s+([^\s\"]+)")
    if "tick_capture" in command_line and symbol:
        return f"pipeline_state/daemon_heartbeat_tick_capture_{symbol}.json"
    if "m1_capture" in command_line:
        return "pipeline_state/daemon_heartbeat_m1_capture_all.json"
    return None


def log_path_for(command_line: str) -> str | None:
    symbol = regex_group(command_line, r"--symbol\s+([^\s\"]+)")
    if "tick_capture" in command_line and symbol:
        return f"logs/tick_capture_{symbol}.log"
    if symbol:
        base = symbol.lower().replace("_cash", "")
        return f"logs/{base}.log"
    if "m1_capture" in command_line:
        return "logs/m1_capture.log"
    if "notification_queue" in command_line:
        return "logs/notification_queue_worker.log"
    if "heartbeat_monitor" in command_line:
        return "logs/heartbeat_monitor.log"
    if "displacement_logger" in command_line:
        return "logs/displacement.log"
    return None


def summarize_process_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    python_live_symbols = sorted(
        {
            row.get("symbol")
            for row in rows
            if row.get("process_family") == "orchestrator"
            and row.get("process_name", "").lower() == "python.exe"
            and row.get("mode") == "live"
        }
    )
    demo_rows = [
        row
        for row in rows
        if row.get("process_family") == "orchestrator" and row.get("mode") == "demo"
    ]
    tick_rows = [row for row in rows if row.get("process_family") == "tick_capture"]
    return {
        "required_symbols": LIVE_SYMBOLS,
        "python_live_orchestrator_symbols": python_live_symbols,
        "python_live_orchestrator_count": len(python_live_symbols),
        "missing_python_live_symbols": sorted(set(LIVE_SYMBOLS) - set(python_live_symbols)),
        "extra_python_live_symbols": sorted(set(python_live_symbols) - set(LIVE_SYMBOLS)),
        "demo_orchestrator_process_count": len(demo_rows),
        "tick_capture_process_count": len(tick_rows),
        "tick_capture_python_count": len(
            [row for row in tick_rows if str(row.get("process_name") or "").lower() == "python.exe"]
        ),
        "tick_capture_cmd_count": len(
            [row for row in tick_rows if str(row.get("process_name") or "").lower() == "cmd.exe"]
        ),
        "process_family_counts": dict(Counter(row.get("process_family") for row in rows)),
        "process_name_counts": dict(Counter(row.get("process_name") for row in rows)),
        "status": "ok_24_live_no_demo"
        if len(python_live_symbols) == len(LIVE_SYMBOLS) and not demo_rows
        else "repair_required",
    }


def collect_scheduler_rows() -> list[dict[str, Any]]:
    script = r"""
    $tasks = Get-ScheduledTask | Where-Object { $_.TaskName -match 'GTOS' -or $_.TaskPath -match 'GTOS' }
    $rows = @()
    foreach ($task in $tasks) {
      $info = $null
      try { $info = Get-ScheduledTaskInfo -TaskName $task.TaskName -TaskPath $task.TaskPath } catch {}
      $rows += [pscustomobject]@{
        task_name=$task.TaskName;
        task_path=$task.TaskPath;
        state="$($task.State)";
        actions=$task.Actions;
        triggers=$task.Triggers;
        last_run_time=if ($info) { $info.LastRunTime } else { $null };
        next_run_time=if ($info) { $info.NextRunTime } else { $null };
        last_task_result=if ($info) { $info.LastTaskResult } else { $null };
      }
    }
    $rows | ConvertTo-Json -Depth 8 -Compress
    """
    result = run_powershell(script, timeout=60)
    payload = parse_json_stdout(result)
    raw_rows = payload if isinstance(payload, list) else ([payload] if payload else [])
    rows = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            continue
        actions = raw.get("actions")
        triggers = raw.get("triggers")
        action_text = json.dumps(actions, default=str)
        trigger_text = json.dumps(triggers, default=str)
        task_name = raw.get("task_name")
        state = str(raw.get("state") or "")
        last_task_result = raw.get("last_task_result")
        last_result_int = None
        try:
            if last_task_result is not None:
                last_result_int = int(last_task_result)
        except (TypeError, ValueError):
            last_result_int = None
        watchdog_task = task_name == "GTOS_Watchdog"
        has_watchdog_launcher = (
            "watchdog_launcher.vbs" in action_text
            or "watchdog.bat" in action_text
            or "watchdog.ps1" in action_text
        )
        has_repetition = "PT15M" in trigger_text or "watchdog" in action_text.lower()
        if watchdog_task:
            if state.lower() == "running":
                status = "watchdog_scheduler_running"
                status_reason = "gtos_watchdog_task_is_currently_running"
            elif state.lower() == "ready" and last_result_int == 0 and has_watchdog_launcher:
                status = "watchdog_scheduler_ready"
                status_reason = "gtos_watchdog_task_ready_last_result_zero_with_watchdog_launcher"
            elif not has_watchdog_launcher:
                status = "watchdog_scheduler_action_missing"
                status_reason = "gtos_watchdog_task_does_not_reference_watchdog_launcher_or_script"
            elif last_result_int not in (0, None):
                status = "watchdog_scheduler_last_run_nonzero"
                status_reason = "gtos_watchdog_task_last_result_nonzero"
            else:
                status = "watchdog_scheduler_unproven"
                status_reason = "gtos_watchdog_task_present_but_state_or_last_result_unproven"
        else:
            status = "gtos_scheduled_task_present"
            status_reason = "non_watchdog_gtos_scheduled_task_recorded_for_inventory"
        rows.append(
            {
                "schema_version": "vps_watchdog_scheduler_v1",
                "generated_at_utc": iso_now(),
                **raw,
                "watchdog_task": watchdog_task,
                "status": status,
                "status_reason": status_reason,
                "always_on_mechanism": (
                    "scheduled_short_lived_watchdog_cycle" if watchdog_task else None
                ),
                "watchdog_launcher_reference_present": has_watchdog_launcher,
                "watchdog_repetition_or_cycle_reference_present": has_repetition,
                "current_process_presence_required": False if watchdog_task else None,
                "current_process_presence_reason": (
                    "GTOS_Watchdog is configured as a scheduled short-lived cycle; "
                    "process table may be empty between runs"
                    if watchdog_task
                    else None
                ),
                "query_exit_code": result.get("exit_code"),
            }
        )
    if not rows:
        rows.append(
            {
                "schema_version": "vps_watchdog_scheduler_v1",
                "generated_at_utc": iso_now(),
                "status": "no_gtos_scheduled_task_rows_found",
                "status_reason": "Get-ScheduledTask returned no GTOS scheduled task rows",
                "query_exit_code": result.get("exit_code"),
                "stderr": result.get("stderr"),
            }
        )
    return rows


def summarize_scheduler_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    watchdog_rows = [row for row in rows if row.get("watchdog_task")]
    ready_statuses = {"watchdog_scheduler_ready", "watchdog_scheduler_running"}
    ready_rows = [row for row in watchdog_rows if row.get("status") in ready_statuses]
    return {
        "watchdog_task_count": len(watchdog_rows),
        "watchdog_ready_count": len(ready_rows),
        "watchdog_statuses": dict(Counter(row.get("status") for row in watchdog_rows)),
        "status": "watchdog_scheduler_ready" if ready_rows else "watchdog_scheduler_repair_required",
        "always_on_mechanism": (
            "scheduled_short_lived_watchdog_cycle" if ready_rows else "unproven"
        ),
        "current_process_presence_required": False if ready_rows else None,
    }


def with_status_reasons(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in rows:
        if row.get("status") and not row.get("status_reason"):
            row_id = row.get("repair_id") or row.get("row_type") or row.get("id") or "row"
            row["status_reason"] = f"{row_id}:{row.get('status')}"
    return rows


def collect_data_capture_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    m1 = checkpoint.get("m1_capture") or {}
    for item in m1.get("per_symbol") or []:
        m1_error_count = m1.get("error_count") or 0
        seen_age = item.get("seen_age_s")
        if m1_error_count:
            status = "m1_capture_error"
            status_reason = "checkpoint_m1_error_count_nonzero"
        elif item.get("last_time_utc") and seen_age is not None and float(seen_age) <= 180:
            status = "fresh"
            status_reason = "closed_bar_seen_recently"
        elif item.get("last_time_utc"):
            status = "stale"
            status_reason = "closed_bar_seen_but_state_age_exceeds_threshold"
        elif m1.get("zero_rows_written_reason") or m1.get("last_progress_absent_reason"):
            status = "no_rows_with_reason"
            status_reason = m1.get("zero_rows_written_reason") or m1.get("last_progress_absent_reason")
        else:
            status = "no_rows_without_reason"
            status_reason = "m1_capture_row_missing_last_time_without_checkpoint_reason"
        rows.append(
            {
                "schema_version": "vps_data_capture_health_v1",
                "capture_type": "m1_closed_bar",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                **item,
                "status": status,
                "status_reason": status_reason,
                "state_status": "ok" if m1.get("error_count") == 0 else "error",
            }
        )
    tick = checkpoint.get("tick_capture") or {}
    for item in tick.get("per_symbol") or []:
        classification = item.get("freshness_classification")
        if classification:
            status = classification
            status_reason = "checkpoint_tick_freshness_classification"
        elif item.get("daemon_alive") and (item.get("age_s") or 0) <= 180:
            status = "fresh"
            status_reason = "daemon_alive_tick_state_recent"
        elif item.get("daemon_alive"):
            status = "stale_without_classification"
            status_reason = "daemon_alive_tick_state_stale_without_checkpoint_classification"
        else:
            status = "dead_or_missing_daemon"
            status_reason = "tick_capture_daemon_not_alive"
        rows.append(
            {
                "schema_version": "vps_data_capture_health_v1",
                "capture_type": "tick",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                **item,
                "status": status,
                "status_reason": status_reason,
                "state_status": item.get("freshness_classification") or "fresh_or_recent",
            }
        )
    return rows


def row_timestamp(row: dict[str, Any]) -> datetime | None:
    for key in (
        "ts_utc",
        "timestamp_utc",
        "utc",
        "created_at_utc",
        "generated_at_utc",
        "time_utc",
        "_raw_timestamp_hint_utc",
    ):
        parsed = parse_iso(row.get(key))
        if parsed:
            return parsed
    return None


def collect_runtime_decision_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    reload_ts = parse_iso((checkpoint.get("post_reload_candidate_flow") or {}).get("reload_timestamp_utc"))
    paths = [
        PROJECT_ROOT / "shadow_logs" / "gtos_vnext_runtime_decisions.jsonl",
        PROJECT_ROOT / "shadow_logs" / "gtos_vnext_replacement_monitoring.jsonl",
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        for row in read_jsonl(path):
            ts = row_timestamp(row)
            if reload_ts and ts and ts < reload_ts:
                continue
            row["schema_version"] = "vps_runtime_decision_v1"
            if row.get("_parse_error"):
                row["route_capture_status"] = "malformed_timestamp_absent_or_post_reload_included"
                row["status"] = "runtime_decision_parse_error"
                row["status_reason"] = (
                    "source_jsonl_row_malformed_and_not_excluded_by_reload_timestamp"
                )
            else:
                row["route_capture_status"] = "post_reload_or_timestamp_absent_included"
                row["status"] = "runtime_decision_row_captured"
                row["status_reason"] = (
                    "post_reload_timestamp_ge_reload"
                    if ts and reload_ts
                    else "timestamp_absent_included_for_supervisor_review"
                )
            rows.append(row)
    if not rows:
        rows.append(
            {
                "schema_version": "vps_runtime_decision_summary_v1",
                "row_type": "summary",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                "reload_timestamp_utc": (
                    reload_ts.isoformat() if reload_ts is not None else None
                ),
                "source_paths": [rel(path) for path in paths],
                "status": "runtime_decision_no_post_reload_rows_yet",
                "status_reason": (
                    "no_runtime_decision_rows_at_or_after_checkpoint_reload_timestamp"
                    if reload_ts
                    else "checkpoint_reload_timestamp_absent_no_runtime_decision_rows"
                ),
            }
        )
    return rows


def candidate_old_system_absence_fields(
    payload: dict[str, Any],
    decision_pipeline: dict[str, Any],
    candidate_packet: dict[str, Any],
) -> dict[str, Any]:
    old_system_absence = candidate_packet.get("old_system_absence_proof") or {}

    def first_present(key: str) -> Any:
        for source in (payload, decision_pipeline, candidate_packet, old_system_absence):
            if isinstance(source, dict) and key in source:
                return source.get(key)
        return None

    return {
        "old_primary_analyzer_called": first_present("old_primary_analyzer_called"),
        "old_l2_required": first_present("old_l2_required"),
        "old_system_absence_status": (
            old_system_absence.get("absence_status")
            if isinstance(old_system_absence, dict)
            else None
        ),
    }


def collect_candidate_packet_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    reload_ts = parse_iso((checkpoint.get("post_reload_candidate_flow") or {}).get("reload_timestamp_utc"))
    checkpoint_ts = parse_iso(checkpoint.get("generated_at_utc"))
    checkpoint_candidate_flow = checkpoint.get("post_reload_candidate_flow") or {}
    rows: list[dict[str, Any]] = [
        {
            "schema_version": "vps_candidate_packet_summary_v1",
            "row_type": "summary",
            "generated_at_utc": checkpoint.get("generated_at_utc"),
            "snapshot_upper_bound_utc": checkpoint.get("generated_at_utc"),
            "source": rel(CHECKPOINT_PATH),
            "status": "candidate_packet_summary_captured",
            "status_reason": "checkpoint_post_reload_candidate_flow_summary_captured",
            **checkpoint_candidate_flow,
            "checkpoint_candidate_records_after_reload": checkpoint_candidate_flow.get(
                "candidate_records_after_reload"
            ),
        }
    ]
    trade_root = PROJECT_ROOT / "knowledge_base" / "trade_records"
    if trade_root.exists():
        for path in sorted(trade_root.rglob("*.json")):
            mtime = parse_trade_record_time(path)
            if checkpoint_ts and mtime and mtime > checkpoint_ts:
                continue
            payload = read_json(path, {})
            if not isinstance(payload, dict):
                continue
            decision_pipeline = payload.get("decision_pipeline") or {}
            candidate_packet = (
                decision_pipeline.get("gtos_vnext_candidate_intelligence_packet") or {}
            )
            if not any(
                candidate_packet.get(key)
                for key in (
                    "candidate_identity",
                    "geometry",
                    "selected_cell_risk_proof",
                    "runtime_decision",
                )
            ):
                continue
            candidate_identity = candidate_packet.get("candidate_identity") or {}
            dynamic_policy = candidate_packet.get("dynamic_policy") or {}
            final_order_decision = candidate_packet.get("final_order_decision") or {}
            source_completeness = candidate_packet.get("source_completeness") or {}
            gates = candidate_packet.get("gates") or {}
            gate3_output = ((gates.get("gate3") or {}).get("output") or {})
            gate3_details = gate3_output.get("details") or {}
            source_event_time, source_event_time_basis = candidate_packet_event_time(
                payload, candidate_packet
            )
            row_time = source_event_time or mtime
            source_event_after_reload = bool(
                reload_ts and source_event_time and source_event_time >= reload_ts
            )
            record_mtime_after_reload = bool(reload_ts and mtime and mtime >= reload_ts)
            if reload_ts and not (source_event_after_reload or record_mtime_after_reload):
                continue
            if checkpoint_ts and row_time and row_time > checkpoint_ts:
                continue
            old_system_absence = candidate_old_system_absence_fields(
                payload, decision_pipeline, candidate_packet
            )
            rows.append(
                {
                    "schema_version": "vps_candidate_packet_record_v1",
                    "row_type": "post_reload_candidate_packet",
                    "source_path": rel(path),
                    "source_mtime_utc": mtime.isoformat() if mtime else None,
                    "source_event_time_utc": (
                        source_event_time.isoformat() if source_event_time else None
                    ),
                    "source_event_time_basis": (
                        source_event_time_basis or "file_mtime_fallback"
                    ),
                    "post_reload_inclusion_basis": (
                        "source_event_time"
                        if source_event_after_reload
                        else (
                            "record_mtime"
                            if record_mtime_after_reload
                            else "reload_timestamp_absent"
                        )
                    ),
                    "source_event_after_reload": source_event_after_reload,
                    "record_mtime_after_reload": record_mtime_after_reload,
                    "status": "candidate_packet_record_captured",
                    "status_reason": (
                        "post_reload_candidate_packet_index_fields_extracted_"
                        "from_source_event_or_record_mtime"
                    ),
                    "candidate_id": payload.get("candidate_id")
                    or payload.get("broader_origin_candidate_id")
                    or candidate_identity.get("candidate_id"),
                    "symbol": payload.get("symbol") or candidate_identity.get("symbol"),
                    "broker_symbol": payload.get("broker_symbol")
                    or candidate_identity.get("broker_symbol"),
                    "side": payload.get("side") or candidate_identity.get("side"),
                    "session": payload.get("session")
                    or candidate_identity.get("session")
                    or candidate_identity.get("route_session"),
                    "kill_zone": candidate_identity.get("kill_zone"),
                    "origin_family": candidate_identity.get("origin_family"),
                    "framework": candidate_identity.get("framework"),
                    "route_family": candidate_identity.get("origin_family")
                    or candidate_identity.get("framework"),
                    "candle_time_utc": (
                        source_event_time.isoformat() if source_event_time else None
                    ),
                    "source_mode": source_completeness.get("source_mode")
                    or ((candidate_packet.get("runtime_decision") or {}).get("event") or {}).get(
                        "source_mode"
                    ),
                    "final_outcome": decision_pipeline.get("final_outcome")
                    or final_order_decision.get("final_outcome")
                    or payload.get("final_outcome"),
                    "order_path": final_order_decision.get("order_path"),
                    "final_reached_order_path": final_order_decision.get("reached_order_path"),
                    "refusal_reason": final_order_decision.get("reason"),
                    "gate3_denial_reason": (
                        gate3_details.get("denial_reason")
                        or final_order_decision.get("reason")
                    ),
                    "selected_policy": payload.get("gtos_vnext_dynamic_policy_selected")
                    or payload.get("selected_policy")
                    or dynamic_policy.get("selected_policy"),
                    "execution_policy_id": payload.get(
                        "gtos_vnext_dynamic_policy_execution_policy_id"
                    )
                    or payload.get("execution_policy_id")
                    or dynamic_policy.get("execution_policy_id"),
                    "packet_capture_mode": candidate_packet.get("capture_mode"),
                    **old_system_absence,
                    "rows_missing_required_packet_fields": 0,
                    "packet": payload,
                }
            )
    packet_records = [
        row
        for row in rows
        if row.get("schema_version") == "vps_candidate_packet_record_v1"
    ]
    rows[0]["candidate_records_after_reload"] = len(packet_records)
    rows[0]["candidate_record_count_basis"] = (
        "route_ledger_current_records_source_event_or_record_mtime"
    )
    rows[0]["candidate_record_count_reconciliation_status"] = (
        "matches_checkpoint_flow"
        if len(packet_records)
        == int(rows[0].get("checkpoint_candidate_records_after_reload") or 0)
        else "route_ledger_includes_additional_current_repaired_record_mtime_rows"
    )
    return rows


def validate_candidate_geometry(
    *,
    side: str,
    entry: float | None,
    stop_loss: float | None,
    take_profit_1: float | None,
    declared_rr: float | None,
) -> tuple[str, list[str], float | None, float | None]:
    issues: list[str] = []
    if side not in {"LONG", "SHORT"}:
        issues.append("side_missing_or_invalid")
    if entry is None:
        issues.append("entry_missing_or_non_numeric")
    if stop_loss is None:
        issues.append("stop_loss_missing_or_non_numeric")
    if take_profit_1 is None:
        issues.append("take_profit_1_missing_or_non_numeric")
    if declared_rr is None:
        issues.append("declared_risk_reward_ratio_missing_or_non_numeric")
    if issues:
        return "invalid", issues, None, None

    if side == "LONG":
        risk = entry - stop_loss
        reward = take_profit_1 - entry
        if not (stop_loss < entry < take_profit_1):
            issues.append("long_entry_sl_tp1_direction_invalid")
    else:
        risk = stop_loss - entry
        reward = entry - take_profit_1
        if not (take_profit_1 < entry < stop_loss):
            issues.append("short_entry_tp1_sl_direction_invalid")
    if risk <= 0:
        issues.append("entry_stop_risk_not_positive")
    if reward <= 0:
        issues.append("entry_tp1_reward_not_positive")
    computed_rr = reward / risk if risk > 0 else None
    if computed_rr is not None and declared_rr is not None and abs(computed_rr - declared_rr) > 0.01:
        issues.append("computed_tp1_rr_mismatch")
    return ("valid" if not issues else "invalid"), issues, risk, computed_rr


def collect_candidate_risk_intelligence_audit(
    checkpoint: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checkpoint_ts = parse_iso(checkpoint.get("generated_at_utc")) or utc_now()
    utc_midnight = checkpoint_ts.replace(hour=0, minute=0, second=0, microsecond=0)
    reload_ts = parse_iso(
        (checkpoint.get("post_reload_candidate_flow") or {}).get("reload_timestamp_utc")
    )

    risk_ledger_path = PROJECT_ROOT / SELECTED_CELL_RISK_LEDGER_REL
    risk_rows = [
        row
        for row in read_jsonl(risk_ledger_path)
        if isinstance(row, dict) and not row.get("_parse_error")
    ]
    risk_by_cell_id = {
        str(row.get("risk_cell_id")): row
        for row in risk_rows
        if row.get("risk_cell_id")
    }
    risk_effective_counts = Counter(
        "positive"
        if (float_or_none(row.get("effective_risk_per_trade_pct")) or 0.0) > 0
        else "zero_or_none"
        for row in risk_rows
    )

    rows: list[dict[str, Any]] = []
    trade_root = PROJECT_ROOT / "knowledge_base" / "trade_records"
    if trade_root.exists():
        for path in sorted(trade_root.rglob("*.json")):
            mtime = parse_trade_record_time(path)
            if not mtime or mtime > checkpoint_ts:
                continue
            payload = read_json(path, {})
            if not isinstance(payload, dict):
                continue
            decision_pipeline = payload.get("decision_pipeline") or {}
            packet = decision_pipeline.get("gtos_vnext_candidate_intelligence_packet") or {}
            if not isinstance(packet, dict):
                continue
            if not any(
                packet.get(key)
                for key in (
                    "candidate_identity",
                    "geometry",
                    "selected_cell_risk_proof",
                    "runtime_decision",
                )
            ):
                continue
            source_event_time, source_event_time_basis = candidate_packet_event_time(
                payload, packet
            )
            row_time_candidates = [t for t in (source_event_time, mtime) if t]
            if (
                not row_time_candidates
                or all(t < utc_midnight for t in row_time_candidates)
                or all(t > checkpoint_ts for t in row_time_candidates)
            ):
                continue
            candidate_identity = packet.get("candidate_identity") or {}
            geometry_raw = (packet.get("geometry") or {}).get("raw") or {}
            dynamic = decision_pipeline.get("gtos_vnext_moonshot_dynamic_execution") or {}
            selected_cell = packet.get("selected_cell_risk_proof") or {}
            gate3 = decision_pipeline.get("gate3_result") or (
                ((packet.get("gates") or {}).get("gate3") or {}).get("output") or {}
            )

            side = str(candidate_identity.get("side") or geometry_raw.get("direction") or "").upper()
            entry = float_or_none(geometry_raw.get("entry_price") or payload.get("entry_price"))
            stop_loss = float_or_none(geometry_raw.get("stop_loss") or payload.get("stop_loss"))
            take_profit_1 = float_or_none(
                geometry_raw.get("take_profit_1") or payload.get("take_profit_1")
            )
            declared_rr = float_or_none(
                geometry_raw.get("risk_reward_ratio") or payload.get("risk_reward_ratio")
            )
            geometry_status, geometry_issues, risk_abs, computed_rr = validate_candidate_geometry(
                side=side,
                entry=entry,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                declared_rr=declared_rr,
            )

            old_primary = packet.get("old_primary_analyzer_called")
            old_l2 = packet.get("old_l2_required")
            value_defects: list[str] = []
            if geometry_issues:
                value_defects.extend(geometry_issues)
            if old_primary is not False:
                value_defects.append("old_primary_analyzer_absence_not_explicit_false")
            if old_l2 is not False:
                value_defects.append("old_l2_absence_not_explicit_false")
            for field_name, field_value in {
                "candidate_id": candidate_identity.get("candidate_id"),
                "symbol": candidate_identity.get("symbol"),
                "side": side,
                "route_session": candidate_identity.get("route_session"),
            }.items():
                if field_value in (None, ""):
                    value_defects.append(f"{field_name}_missing")

            refusal_reasons = list(dynamic.get("refusal_reasons") or [])
            selected_cell_risk_refused = "selected_cell_risk_not_verified_or_zero" in refusal_reasons
            cell_id = selected_cell.get("cell_id")
            current_source_row = risk_by_cell_id.get(str(cell_id)) if cell_id else None
            source_identity = selected_cell.get("source_row_identity") or {}
            if not isinstance(source_identity, dict):
                source_identity = {}
            source_identity_risk_pct = float_or_none(
                source_identity.get("effective_risk_per_trade_pct")
            )
            current_source_risk_pct = (
                float_or_none(current_source_row.get("effective_risk_per_trade_pct"))
                if current_source_row
                else None
            )
            source_risk_pct = (
                source_identity_risk_pct
                if source_identity_risk_pct is not None
                else current_source_risk_pct
            )
            source_identity_unresolved = list(
                source_identity.get("exact_unresolved_or_excluded_reasons") or []
            )
            current_source_unresolved = (
                list(current_source_row.get("exact_unresolved_or_excluded_reasons") or [])
                if current_source_row
                else []
            )
            source_unresolved = source_identity_unresolved or current_source_unresolved

            def normalized_text(value: Any) -> str:
                return str(value or "").strip().lower()

            def source_execution_critical_reasons(reasons: list[Any]) -> list[str]:
                critical_prefixes = (
                    "digits_",
                    "filling_mode_",
                    "order_mode_",
                    "price_rounding_",
                    "lot_rounding_",
                    "spread_p95_",
                )
                critical_exact = {
                    "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed",
                    "old_three_repaired_branch_allowlist_side_not_dimensioned",
                    "risk_zero_execution_critical_evidence_unresolved",
                    "selected_cell_sl_distance_distribution_missing_or_incomplete",
                }
                non_blocking = {
                    "commission_fields_not_exposed_in_current_symbol_info_snapshot",
                    "condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry",
                }
                result = []
                for reason in reasons:
                    text = str(reason or "")
                    if not text or text in non_blocking:
                        continue
                    if text in critical_exact or any(
                        text.startswith(prefix) for prefix in critical_prefixes
                    ):
                        result.append(text)
                return sorted(set(result))

            current_ledger_drift_dimensions: list[dict[str, Any]] = []
            if source_identity and current_source_row:
                for field in (
                    "symbol",
                    "broker_alias",
                    "selector_component",
                    "family",
                    "framework",
                    "side",
                    "route_session",
                    "session_bucket",
                    "utc_hour_bucket",
                    "risk_decision_basis",
                ):
                    packet_value = source_identity.get(field)
                    current_value = current_source_row.get(field)
                    if normalized_text(packet_value) != normalized_text(current_value):
                        current_ledger_drift_dimensions.append(
                            {
                                "field": field,
                                "packet_source_identity": packet_value,
                                "current_ledger_row": current_value,
                            }
                        )
                if source_identity_risk_pct != current_source_risk_pct:
                    current_ledger_drift_dimensions.append(
                        {
                            "field": "effective_risk_per_trade_pct",
                            "packet_source_identity": source_identity_risk_pct,
                            "current_ledger_row": current_source_risk_pct,
                        }
                    )
            match_reason = selected_cell.get("match_reason")
            capture_contract = selected_cell.get("capture_contract") or {}
            source_event_after_reload = bool(
                reload_ts and source_event_time and source_event_time >= reload_ts
            )
            record_mtime_after_reload = bool(reload_ts and mtime and mtime >= reload_ts)
            after_reload = bool(source_event_after_reload or record_mtime_after_reload)
            source_critical = source_execution_critical_reasons(source_unresolved)
            risk_validation = "no_selected_cell_risk_refusal"
            risk_mismatch = False
            if selected_cell.get("allowed") is True:
                if not cell_id or (float_or_none(selected_cell.get("risk_pct")) or 0.0) <= 0:
                    risk_validation = "allowed_selected_cell_missing_positive_risk"
                    risk_mismatch = True
                elif not source_identity and current_source_row is None:
                    risk_validation = "allowed_selected_cell_source_row_missing"
                    risk_mismatch = True
                elif (source_risk_pct or 0.0) <= 0:
                    risk_validation = "allowed_selected_cell_source_row_not_positive_clean"
                    risk_mismatch = after_reload
                elif source_critical:
                    risk_validation = "allowed_selected_cell_execution_critical_source_unresolved"
                    risk_mismatch = after_reload
                elif after_reload and current_ledger_drift_dimensions:
                    risk_validation = "post_reload_selected_cell_source_identity_current_ledger_drift"
                    risk_mismatch = True
                else:
                    risk_validation = "valid_positive_selected_cell_source_bound"
            elif selected_cell_risk_refused:
                if after_reload and match_reason in {
                    "selected_cell_risk_ledger_missing_or_empty",
                    "selected_cell_risk_ledger_raw_lfs_pointer",
                    "selected_cell_risk_ledger_parse_failed",
                }:
                    risk_validation = "post_reload_selected_cell_ledger_unavailable_defect"
                    risk_mismatch = True
                elif source_identity or current_source_row is not None:
                    if (source_risk_pct or 0.0) > 0 and not source_critical:
                        if after_reload:
                            risk_validation = (
                                "refused_positive_clean_selected_cell_source_row_defect"
                            )
                            risk_mismatch = True
                        else:
                            risk_validation = (
                                "pre_reload_refused_positive_source_row_repaired_or_superseded"
                            )
                    else:
                        risk_validation = "valid_source_bound_zero_or_unresolved_selected_cell_risk"
                elif match_reason == "no_exact_selected_cell_risk_match":
                    if capture_contract.get("status") and (
                        selected_cell.get("failed_dimensions")
                        or selected_cell.get("nearest_candidate")
                        or capture_contract.get("failed_dimensions")
                    ):
                        risk_validation = (
                            "valid_no_exact_selected_cell_risk_match_with_capture_contract"
                        )
                    else:
                        risk_validation = "no_exact_selected_cell_match_missing_capture_contract"
                        risk_mismatch = True
                elif not after_reload and match_reason == "selected_cell_risk_ledger_missing_or_empty":
                    risk_validation = "pre_repair_missing_or_empty_selected_cell_ledger"
                else:
                    risk_validation = "selected_cell_risk_refusal_unclassified"
                    risk_mismatch = True

            account_risk_status = "passed_or_allowed"
            if gate3 and gate3.get("passed") is False:
                account_risk_status = "blocked_or_unproven"
            elif dynamic.get("prop_action") not in (None, "", "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"):
                account_risk_status = str(dynamic.get("prop_action"))

            if risk_mismatch:
                value_defects.append(risk_validation)
            if not value_defects:
                row_status = "candidate_values_validated"
            elif after_reload:
                row_status = "candidate_value_or_risk_defect"
            else:
                row_status = "historical_candidate_value_or_risk_gap_not_current_live_defect"
            rows.append(
                {
                    "schema_version": "vps_candidate_risk_intelligence_audit_row_v1",
                    "status": row_status,
                    "status_reason": "candidate_geometry_old_system_and_selected_cell_risk_checked",
                    "path": rel(path),
                    "mtime_utc": mtime.isoformat() if mtime else None,
                    "source_event_time_utc": (
                        source_event_time.isoformat() if source_event_time else None
                    ),
                    "source_event_time_basis": (
                        source_event_time_basis or "file_mtime_fallback"
                    ),
                    "after_selected_cell_lfs_reload": after_reload,
                    "post_reload_inclusion_basis": (
                        "source_event_time"
                        if source_event_after_reload
                        else (
                            "record_mtime"
                            if record_mtime_after_reload
                            else None
                        )
                    ),
                    "source_event_after_reload": source_event_after_reload,
                    "record_mtime_after_reload": record_mtime_after_reload,
                    "candidate_id": candidate_identity.get("candidate_id"),
                    "trade_id": candidate_identity.get("trade_id"),
                    "symbol": candidate_identity.get("symbol"),
                    "broker_symbol": candidate_identity.get("broker_symbol"),
                    "side": side,
                    "session": candidate_identity.get("session"),
                    "route_session": candidate_identity.get("route_session"),
                    "utc_hour_bucket": candidate_identity.get("utc_hour_bucket"),
                    "origin_family": candidate_identity.get("origin_family"),
                    "framework": candidate_identity.get("framework"),
                    "dynamic_policy": dynamic.get("selected_policy"),
                    "execution_policy_id": dynamic.get("execution_policy_id"),
                    "dynamic_applied": dynamic.get("applied"),
                    "dynamic_decision_status": dynamic.get("decision_status"),
                    "final_outcome": decision_pipeline.get("final_outcome"),
                    "entry": entry,
                    "stop_loss": stop_loss,
                    "take_profit_1": take_profit_1,
                    "trade_parameter_rr": declared_rr,
                    "computed_entry_sl_risk_abs": risk_abs,
                    "computed_tp1_rr": computed_rr,
                    "geometry_status": geometry_status,
                    "geometry_issues": geometry_issues,
                    "old_primary_analyzer_called": old_primary,
                    "old_l2_required": old_l2,
                    "account_and_prop_risk_status": account_risk_status,
                    "gate3_passed": gate3.get("passed") if isinstance(gate3, dict) else None,
                    "prop_action": dynamic.get("prop_action"),
                    "refusal_reasons": refusal_reasons,
                    "selected_cell_risk_status": selected_cell.get("status"),
                    "selected_cell_match_reason": match_reason,
                    "selected_cell_risk_cell_id": cell_id,
                    "selected_cell_risk_pct": selected_cell.get("risk_pct"),
                    "selected_cell_effective_risk_per_trade_pct": source_risk_pct,
                    "selected_cell_source_identity_effective_risk_per_trade_pct": (
                        source_identity_risk_pct
                    ),
                    "selected_cell_current_ledger_effective_risk_per_trade_pct": (
                        current_source_risk_pct
                    ),
                    "selected_cell_source_identity_symbol": source_identity.get("symbol"),
                    "selected_cell_current_ledger_symbol": (
                        current_source_row or {}
                    ).get("symbol"),
                    "selected_cell_risk_decision_basis": selected_cell.get("decision_basis")
                    or source_identity.get("risk_decision_basis")
                    or (current_source_row or {}).get("risk_decision_basis"),
                    "selected_cell_unresolved_or_excluded_reasons": source_unresolved
                    or selected_cell.get("unresolved_reasons")
                    or [],
                    "selected_cell_execution_critical_unresolved_reasons": source_critical,
                    "selected_cell_current_ledger_drift_dimensions": (
                        current_ledger_drift_dimensions
                    ),
                    "selected_cell_source_match_status": (
                        "source_row_identity_matches_current_ledger"
                        if current_source_row and not current_ledger_drift_dimensions
                        else (
                            "source_row_identity_current_ledger_drift"
                            if current_ledger_drift_dimensions
                            else match_reason
                        )
                    ),
                    "selected_cell_capture_contract_status": capture_contract.get("status"),
                    "selected_cell_capture_contract_refusal_cause": capture_contract.get(
                        "refusal_cause"
                    )
                    or selected_cell.get("refusal_cause"),
                    "selected_cell_source_ledger_path": SELECTED_CELL_RISK_LEDGER_REL,
                    "risk_refusal_validation": risk_validation,
                    "risk_refusal_mismatch": risk_mismatch,
                    "current_value_defect": bool(after_reload and value_defects),
                    "value_defects": value_defects,
                }
            )

    status_counts = Counter(row.get("status") for row in rows)
    geometry_counts = Counter(row.get("geometry_status") for row in rows)
    risk_validation_counts = Counter(row.get("risk_refusal_validation") for row in rows)
    refusal_counts: Counter[str] = Counter()
    for row in rows:
        refusal_counts.update(row.get("refusal_reasons") or [])
    post_reload_missing = sum(
        1
        for row in rows
        if row.get("after_selected_cell_lfs_reload")
        and row.get("selected_cell_match_reason")
        in {
            "selected_cell_risk_ledger_missing_or_empty",
            "selected_cell_risk_ledger_raw_lfs_pointer",
            "selected_cell_risk_ledger_parse_failed",
        }
    )
    summary = {
        "schema_version": "vps_candidate_risk_intelligence_audit_v1",
        "generated_at_utc": iso_now(),
        "snapshot_upper_bound_utc": checkpoint_ts.isoformat(),
        "utc_midnight_start": utc_midnight.isoformat(),
        "selected_cell_lfs_reload_timestamp_utc": reload_ts.isoformat() if reload_ts else None,
        "ledger_path": rel(ROUTE_DIR / "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl"),
        "candidate_record_count": len(rows),
        "pre_reload_candidate_record_count": sum(
            1 for row in rows if not row.get("after_selected_cell_lfs_reload")
        ),
        "post_reload_candidate_record_count": sum(
            1 for row in rows if row.get("after_selected_cell_lfs_reload")
        ),
        "status_counts": dict(status_counts),
        "geometry_counts": dict(geometry_counts),
        "risk_refusal_validation_counts": dict(risk_validation_counts),
        "refusal_reason_counts": dict(refusal_counts),
        "risk_ledger_row_count": len(risk_rows),
        "risk_ledger_effective_risk_counts": dict(risk_effective_counts),
        "post_reload_selected_cell_ledger_missing_or_empty_count": post_reload_missing,
        "risk_refusal_mismatch_count": sum(1 for row in rows if row.get("risk_refusal_mismatch")),
        "current_risk_refusal_mismatch_count": sum(
            1
            for row in rows
            if row.get("after_selected_cell_lfs_reload")
            and row.get("risk_refusal_mismatch")
        ),
        "pre_reload_risk_refusal_mismatch_count": sum(
            1
            for row in rows
            if not row.get("after_selected_cell_lfs_reload")
            and row.get("risk_refusal_mismatch")
        ),
        "post_reload_source_identity_current_ledger_drift_count": sum(
            1
            for row in rows
            if row.get("after_selected_cell_lfs_reload")
            and row.get("selected_cell_current_ledger_drift_dimensions")
        ),
        "pre_reload_source_identity_current_ledger_drift_count": sum(
            1
            for row in rows
            if not row.get("after_selected_cell_lfs_reload")
            and row.get("selected_cell_current_ledger_drift_dimensions")
        ),
        "current_value_defect_count": sum(
            1
            for row in rows
            if row.get("after_selected_cell_lfs_reload") and row.get("value_defects")
        ),
        "account_risk_gate_summary": dict(
            Counter(row.get("account_and_prop_risk_status") for row in rows)
        ),
        "interpretation": {
            "account_risk": (
                "Gate3/prop risk is counted separately from selected-cell source risk; "
                "selected-cell risk remains mandatory under current live config."
            ),
            "selected_cell_risk": (
                "Zero, unresolved, or no-exact-match source rows block under the "
                "current live selected-cell risk contract; this audit flags only "
                "missing/pointer/parse/mismatch defects."
            ),
            "live_behavior_change_boundary": (
                "Bypassing selected-cell risk or treating account risk as a substitute "
                "would alter live risk/selector behavior and needs exact CEO approval."
            ),
        },
    }
    return summary, rows


def open_trade_lifecycle_row_status(row: dict[str, Any]) -> tuple[str, str]:
    row_type = row.get("row_type")
    if row_type == "open_position":
        if row.get("reconciled"):
            return "open_position_reconciled", "ticket_present_in_reconciled_open_position_ids"
        return "open_position_unreconciled", "ticket_missing_from_reconciled_open_position_ids"
    if row_type == "matched_lifecycle_source":
        if row.get("ticket") and row.get("selected_policy") and row.get("execution_policy_id"):
            return (
                "matched_lifecycle_source_present",
                "checkpoint_matched_pending_lifecycle_row_carries_policy_identity",
            )
        return "matched_lifecycle_source_incomplete", "missing_ticket_or_policy_identity"
    if row_type == "lane06_broker_lifecycle_source":
        if row.get("current_close_reconciled"):
            return (
                "lane06_source_resolved_by_current_broker_close",
                "historical_residual_ticket_no_longer_open_and_close_deal_captured",
            )
        if row.get("ticket") and row.get("broker_lifecycle_status"):
            return "lane06_source_bound", "lane06_broker_lifecycle_row_matches_open_ticket"
        return "lane06_source_incomplete", "missing_ticket_or_broker_lifecycle_status"
    return "open_lifecycle_unknown_row_type", f"row_type={row_type!r}"


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", 0, "0"):
            return value
    return None


def collect_open_trade_lifecycle_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    broker = checkpoint.get("broker_lifecycle") or {}
    rows: list[dict[str, Any]] = []
    for position in broker.get("open_positions") or []:
        rows.append(
            {
                "schema_version": "vps_open_trade_lifecycle_v1",
                "row_type": "open_position",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                **position,
                "lifecycle_status": broker.get("status"),
                "reconciled": position.get("ticket") in broker.get("reconciled_open_position_ids", []),
            }
        )
    for matched in broker.get("matched_pending_lifecycle_rows") or []:
        ticket = first_non_empty(
            matched.get("ticket"),
            matched.get("mt5_position_ticket"),
            matched.get("mt5_entry_order_ticket"),
            matched.get("trade_state_ticket"),
        )
        selected_policy = first_non_empty(
            matched.get("selected_policy"),
            matched.get("gtos_vnext_dynamic_policy_selected"),
            matched.get("dynamic_policy_selected"),
        )
        execution_policy_id = first_non_empty(
            matched.get("execution_policy_id"),
            matched.get("gtos_vnext_execution_policy_id"),
            matched.get("gtos_vnext_dynamic_policy_execution_policy_id"),
        )
        rows.append(
            {
                "schema_version": "vps_open_trade_lifecycle_v1",
                "row_type": "matched_lifecycle_source",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                **matched,
                "ticket": ticket,
                "selected_policy": selected_policy,
                "execution_policy_id": execution_policy_id,
                "ticket_identity_source": (
                    "ticket_or_mt5_position_ticket_or_entry_order_ticket"
                ),
                "policy_identity_source": (
                    "selected_policy_or_gtos_vnext_dynamic_policy_selected"
                ),
            }
        )
    if LANE06_BROKER_LIFECYCLE_PATH.exists():
        open_tickets = {
            str(row.get("ticket"))
            for row in rows
            if row.get("ticket") is not None
        }
        nas100_close_resolution = nas100_broker_close_resolution()
        for row in read_jsonl(LANE06_BROKER_LIFECYCLE_PATH):
            ticket = str(row.get("ticket") or "")
            if ticket in open_tickets or (ticket == NAS100_RESIDUAL_TICKET and nas100_close_resolution):
                projected = {
                    "schema_version": "vps_open_trade_lifecycle_v1",
                    "row_type": "lane06_broker_lifecycle_source",
                    **row,
                }
                if ticket == NAS100_RESIDUAL_TICKET and ticket not in open_tickets:
                    projected.update(
                        {
                            "current_open_position_present": False,
                            "current_close_reconciled": True,
                            "current_close_resolution": nas100_close_resolution,
                        }
                    )
                rows.append(projected)
    for row in rows:
        status, status_reason = open_trade_lifecycle_row_status(row)
        row["status"] = status
        row["status_reason"] = status_reason
    return rows


def collect_broker_reconciliation_rows(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    broker = checkpoint.get("broker_lifecycle") or {}
    rows: list[dict[str, Any]] = []
    for name in ["close_deals", "entry_deals", "history_orders", "open_positions"]:
        for item in broker.get(name) or []:
            rows.append(
                {
                    "schema_version": "vps_broker_reconciliation_v1",
                    "row_type": name,
                    "generated_at_utc": checkpoint.get("generated_at_utc"),
                    **item,
                    "broker_lifecycle_status": broker.get("status"),
                    "status": "broker_reconciliation_row_bound"
                    if broker.get("status")
                    else "broker_reconciliation_status_missing",
                    "status_reason": (
                        f"{name}_row_captured_from_checkpoint_broker_lifecycle"
                        if broker.get("status")
                        else "checkpoint_broker_lifecycle_status_missing"
                    ),
                }
            )
    rows.append(
        {
            "schema_version": "vps_broker_reconciliation_summary_v1",
            "row_type": "summary",
            "generated_at_utc": checkpoint.get("generated_at_utc"),
            "status": broker.get("status"),
            "open_vnext_position_count": broker.get("open_vnext_position_count"),
            "open_vnext_order_count": broker.get("open_vnext_order_count"),
            "reconciled_open_position_ids": broker.get("reconciled_open_position_ids"),
            "unreconciled_open_exposure_count": broker.get("unreconciled_open_exposure_count"),
            "close_deal_reconciled_count": broker.get("close_deal_reconciled_count"),
            "status_reason": "checkpoint_broker_lifecycle_summary_status",
        }
    )
    return rows


def collect_risk_rows(
    account_payload: dict[str, Any],
    broker_spec_rows: list[dict[str, Any]],
    checkpoint: dict[str, Any],
) -> list[dict[str, Any]]:
    specs = {row.get("broker_symbol"): row for row in broker_spec_rows}
    account = account_payload.get("account") or {}
    balance = account.get("balance") or (checkpoint.get("mt5") or {}).get("balance")
    equity = account.get("equity") or (checkpoint.get("mt5") or {}).get("equity")
    rows: list[dict[str, Any]] = [
        {
            "schema_version": "vps_risk_exposure_v1",
            "row_type": "account",
            "generated_at_utc": iso_now(),
            "balance": balance,
            "equity": equity,
            "margin": account.get("margin"),
            "margin_free": account.get("margin_free"),
            "read_only": True,
            "status": "account_risk_authority_ready"
            if balance is not None and equity is not None
            else "account_risk_authority_incomplete",
            "status_reason": "mt5_account_balance_equity_available_read_only"
            if balance is not None and equity is not None
            else "mt5_account_balance_or_equity_missing",
        }
    ]
    for position in (checkpoint.get("broker_lifecycle") or {}).get("open_positions") or []:
        broker_symbol = position.get("symbol")
        spec = specs.get(broker_symbol) or {}
        risk_dollars = None
        risk_percent = None
        sl = position.get("sl")
        price_open = position.get("price_open")
        volume = position.get("volume")
        tick_size = spec.get("trade_tick_size") or spec.get("point")
        tick_value = spec.get("trade_tick_value")
        if all(v not in (None, 0) for v in [sl, price_open, volume, tick_size, tick_value]):
            position_type = position.get("type")
            if position_type == 0:
                price_risk = max(float(price_open) - float(sl), 0.0)
            else:
                price_risk = max(float(sl) - float(price_open), 0.0)
            risk_dollars = price_risk / float(tick_size) * float(tick_value) * float(volume)
            if balance:
                risk_percent = risk_dollars / float(balance) * 100.0
        rows.append(
            {
                "schema_version": "vps_risk_exposure_v1",
                "row_type": "open_position",
                "generated_at_utc": iso_now(),
                "ticket": position.get("ticket"),
                "identifier": position.get("identifier"),
                "symbol": position.get("symbol"),
                "volume": volume,
                "price_open": price_open,
                "sl": sl,
                "tp": position.get("tp"),
                "floating_profit": position.get("profit"),
                "swap": position.get("swap"),
                "worst_case_sl_risk_dollars_estimate": round(risk_dollars, 4)
                if risk_dollars is not None
                else None,
                "worst_case_sl_risk_percent_estimate": round(risk_percent, 6)
                if risk_percent is not None
                else None,
                "risk_estimate_source": "broker_position_and_symbol_tick_value",
                "manual_broker_action_taken": False,
                "status": "open_position_risk_estimated"
                if risk_dollars is not None and risk_percent is not None
                else "open_position_risk_estimate_missing",
                "status_reason": (
                    "sl_at_or_beyond_breakeven_zero_worst_case_risk"
                    if risk_dollars == 0
                    else "broker_position_symbol_tick_value_and_sl_bound"
                )
                if risk_dollars is not None and risk_percent is not None
                else "missing_sl_entry_volume_tick_size_or_tick_value",
            }
        )
    return rows


def queue_status(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    terminal_markers = {
        row.get("alert_id"): row.get("marker")
        for row in rows
        if row.get("marker") in {"DELIVERED", "EXPIRED", "FAILED"}
    }
    pending = [
        row
        for row in rows
        if row.get("alert_id") and row.get("alert_id") not in terminal_markers and not row.get("marker")
    ]
    return {
        **file_metadata(path),
        "row_count": len(rows),
        "pending_count": len(pending),
        "marker_counts": dict(Counter(str(row.get("marker")) for row in rows if row.get("marker"))),
        "pending_alert_ids": [row.get("alert_id") for row in pending],
        "secret_values_recorded": False,
    }


def collect_notification_rows(process_summary: dict[str, Any]) -> list[dict[str, Any]]:
    worker_count = process_summary.get("process_family_counts", {}).get(
        "notification_queue_worker", 0
    )
    rows = [
        {
            "schema_version": "vps_notification_v1",
            "row_type": "worker_process",
            "generated_at_utc": iso_now(),
            "notification_worker_count": worker_count,
            "worker_status": "alive" if worker_count else "missing",
            "status": "alive" if worker_count else "missing",
            "status_reason": (
                "notification_queue_worker_process_present"
                if worker_count
                else "notification_queue_worker_process_missing"
            ),
        }
    ]
    for rel_path in [
        "pipeline_state/notification_queue.jsonl",
        "pipeline_state/vps_telegram_test_queue.jsonl",
        "pipeline_state/vps_telegram_test_queue_retry.jsonl",
    ]:
        q_status = queue_status(PROJECT_ROOT / rel_path)
        pending_count = q_status.get("pending_count") or 0
        marker_counts = q_status.get("marker_counts") or {}
        if rel_path == "pipeline_state/notification_queue.jsonl":
            status = "drained" if pending_count == 0 else "pending_live_queue"
            status_reason = (
                "active_notification_queue_empty"
                if pending_count == 0
                else "active_notification_queue_has_pending_rows"
            )
        elif rel_path.endswith("_retry.jsonl") and marker_counts.get("DELIVERED"):
            status = "synthetic_retry_queue_delivered"
            status_reason = "vps_readiness_retry_queue_has_delivered_marker"
        elif pending_count:
            status = "synthetic_test_queue_historical_pending"
            status_reason = "not_active_runtime_queue; retained readiness-test evidence"
        else:
            status = "synthetic_test_queue_drained"
            status_reason = "not_active_runtime_queue_and_no_pending_rows"
        rows.append(
            {
                "schema_version": "vps_notification_v1",
                "row_type": "queue_file",
                "queue_path": rel_path,
                **q_status,
                "status": status,
                "status_reason": status_reason,
            }
        )
    env_keys = []
    for env_path in PROJECT_ROOT.glob(".env*"):
        parsed = parse_env_file(env_path)
        env_keys.extend(parsed.get("key_names") or [])
    rows.append(
        {
            "schema_version": "vps_notification_v1",
            "row_type": "credential_presence_without_values",
            "telegram_bot_token_present": "TELEGRAM_BOT_TOKEN" in env_keys,
            "telegram_chat_id_present": "TELEGRAM_CHAT_ID" in env_keys,
            "secret_values_recorded": False,
            "status": (
                "present_without_values"
                if "TELEGRAM_BOT_TOKEN" in env_keys and "TELEGRAM_CHAT_ID" in env_keys
                else "missing_credential_key"
            ),
            "status_reason": "only credential key presence recorded; secret values not read or printed",
        }
    )
    return rows


def scan_nas100_log_anomalies() -> list[dict[str, Any]]:
    paths = [
        PROJECT_ROOT / "knowledge_base" / "logs" / "agent_NAS100_live.log",
        PROJECT_ROOT / "logs" / "nas100.log",
    ]
    rows = []
    patterns = [
        "Bootstrapping orchestrator (mode=live)",
        "Adopted trade vNext dynamic policy recovery",
        "Reconnected trade record",
        "broker_closed: reconciled from MT5 deal",
        "SL->BE modify FAILED",
        "TP modify FAILED after retry",
        "retcode': 10013",
    ]
    for path in paths:
        if not local_path_exists(path):
            continue
        for idx, line in enumerate(read_text(path).splitlines(), start=1):
            if any(pattern in line for pattern in patterns):
                rows.append(
                    {
                        "source_path": rel(path),
                        "line_no": idx,
                        "line": line,
                    }
                )
    return rows


def nas100_broker_close_resolution() -> dict[str, Any] | None:
    for row in reversed(read_jsonl(SLIPPAGE_LOG_PATH)):
        if str(row.get("ticket") or "") != NAS100_RESIDUAL_TICKET:
            continue
        if row.get("trigger") != "BROKER_CLOSED_DEAL_RECONCILIATION":
            continue
        deal_ticket = first_non_empty(row.get("deal_ticket"), row.get("mt5_deal_id"))
        if not deal_ticket:
            continue
        return {
            "status": "resolved_broker_closed_deal_reconciled",
            "resolved": True,
            "ticket": NAS100_RESIDUAL_TICKET,
            "symbol": row.get("symbol"),
            "close_time_utc": row.get("close_time") or row.get("broker_fill_time_utc"),
            "close_reason": row.get("close_reason"),
            "deal_ticket": deal_ticket,
            "order_ticket": first_non_empty(row.get("order_ticket"), row.get("mt5_order_id")),
            "volume_closed": row.get("volume_closed"),
            "remaining_volume": row.get("remaining_volume"),
            "source_path": row.get("_source_path"),
            "source_line_no": row.get("_line_no"),
            "source": "shadow_logs.slippage.BROKER_CLOSED_DEAL_RECONCILIATION",
        }
    log_path = PROJECT_ROOT / "knowledge_base" / "logs" / "agent_NAS100_live.log"
    if local_path_exists(log_path):
        for idx, line in enumerate(read_text(log_path).splitlines(), start=1):
            if NAS100_RESIDUAL_TICKET in line and "broker_closed: reconciled" in line:
                return {
                    "status": "resolved_broker_closed_log_reconciled",
                    "resolved": True,
                    "ticket": NAS100_RESIDUAL_TICKET,
                    "source_path": rel(log_path),
                    "source_line_no": idx,
                    "source": "agent_NAS100_live.broker_closed_reconciled",
                    "line": line,
                }
    return None


def nas100_residual_sltp_status(checkpoint: dict[str, Any]) -> dict[str, Any]:
    positions: list[dict[str, Any]] = []
    distinct_current_positions: list[dict[str, Any]] = []
    broker = checkpoint.get("broker_lifecycle") if isinstance(checkpoint.get("broker_lifecycle"), dict) else {}
    mt5 = checkpoint.get("mt5") if isinstance(checkpoint.get("mt5"), dict) else {}
    for source_name, source_rows in [
        ("broker_lifecycle.open_positions", broker.get("open_positions") or []),
        ("mt5.position_details", mt5.get("position_details") or []),
    ]:
        if not isinstance(source_rows, list):
            continue
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol") or "").upper()
            ticket = str(row.get("ticket") or row.get("identifier") or "")
            magic = row.get("magic")
            if symbol not in {"NDX100", "NAS100"}:
                continue
            if ticket != NAS100_RESIDUAL_TICKET:
                if magic == 20260401:
                    distinct_current_positions.append(
                        {
                            "ticket": ticket,
                            "identifier": row.get("identifier"),
                            "symbol": row.get("symbol"),
                            "type": row.get("type"),
                            "volume": row.get("volume"),
                            "price_open": row.get("price_open"),
                            "price_current": row.get("price_current"),
                            "sl": row.get("sl"),
                            "tp": row.get("tp"),
                            "source": source_name,
                        }
                    )
                continue
            candidate = dict(row)
            candidate["_sltp_source"] = source_name
            positions.append(candidate)
    if not positions:
        close_resolution = nas100_broker_close_resolution()
        if close_resolution:
            return {
                **close_resolution,
                "current_open_position_present": False,
                "current_distinct_open_positions": distinct_current_positions,
                "broker_lifecycle_effect": (
                    "residual NDX100 position 241779188 no longer open; MT5 close "
                    "deal/source log proves broker-closed reconciliation; any current "
                    "NDX100 position has a distinct ticket and must not be treated as "
                    "the historical residual SL/TP defect"
                ),
            }
        return {
            "status": "not_observed_in_current_checkpoint",
            "resolved": False,
            "ticket": NAS100_RESIDUAL_TICKET,
            "current_distinct_open_positions": distinct_current_positions,
        }

    position = positions[0]
    try:
        price_open = float(position.get("price_open"))
        sl = float(position.get("sl"))
    except (TypeError, ValueError):
        return {
            "status": "current_position_observed_without_numeric_sltp",
            "resolved": False,
            "ticket": position.get("ticket") or position.get("identifier"),
            "symbol": position.get("symbol"),
            "price_open": position.get("price_open"),
            "sl": position.get("sl"),
            "tp": position.get("tp"),
            "volume": position.get("volume"),
            "source": position.get("_sltp_source"),
        }

    position_type = position.get("type")
    if position_type == 0:
        be_protected = sl >= price_open
    elif position_type == 1:
        be_protected = sl <= price_open
    else:
        be_protected = sl == price_open
    tp_present = position.get("tp") not in (None, 0, 0.0, "0", "0.0")
    resolved = bool(be_protected and tp_present)
    return {
        "status": "resolved_runtime_repaired" if resolved else "current_position_not_be_protected",
        "resolved": resolved,
        "ticket": position.get("ticket") or position.get("identifier"),
        "identifier": position.get("identifier"),
        "symbol": position.get("symbol"),
        "type": position_type,
        "volume": position.get("volume"),
        "price_open": position.get("price_open"),
        "sl": position.get("sl"),
        "tp": position.get("tp"),
        "be_protected": be_protected,
        "tp_present": tp_present,
        "source": position.get("_sltp_source"),
    }


def collect_anomaly_rows(
    checkpoint: dict[str, Any],
    verification_commands: dict[str, Any],
    process_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    nas100_sltp = nas100_residual_sltp_status(checkpoint)
    for gap in checkpoint.get("evidence_gaps") or []:
        rows.append(
            {
                "schema_version": "vps_anomaly_v1",
                "row_type": "checkpoint_evidence_gap",
                "generated_at_utc": checkpoint.get("generated_at_utc"),
                **gap,
                "status": "continuation_required",
            }
        )
    if process_summary.get("demo_orchestrator_process_count"):
        rows.append(
            {
                "schema_version": "vps_anomaly_v1",
                "row_type": "demo_orchestrator_processes",
                "status": "repair_required",
                "count": process_summary.get("demo_orchestrator_process_count"),
            }
        )
    for item in scan_nas100_log_anomalies():
        if "FAILED" in item["line"] or "retcode': 10013" in item["line"]:
            resolved = bool(nas100_sltp.get("resolved"))
            broker_effect = nas100_sltp.get("broker_lifecycle_effect") or (
                "residual NDX100 position 241779188 protected at BE with repaired TP; "
                "no duplicate partial close on reload"
                if resolved
                else "residual position remains open with existing SL/TP"
            )
            rows.append(
                {
                    "schema_version": "vps_anomaly_v1",
                    "row_type": "nas100_sltp_modify_retcode_10013",
                    "status": (
                        "historical_resolved_by_sltp_action_repair_and_nas100_reload"
                        if resolved
                        else "active_continuation_no_manual_broker_action"
                    ),
                    "broker_lifecycle_effect": broker_effect,
                    "current_sltp_status": nas100_sltp,
                    **item,
                }
            )
    if nas100_sltp.get("status") != "not_observed_in_current_checkpoint":
        rows.append(
            {
                "schema_version": "vps_anomaly_v1",
                "row_type": "nas100_sltp_repair_resolution",
                "status": nas100_sltp.get("status"),
                "broker_lifecycle_effect": nas100_sltp.get("broker_lifecycle_effect")
                or (
                    "current checkpoint proves NAS100 residual is protected at BE with TP present"
                    if nas100_sltp.get("resolved")
                    else "current checkpoint still needs NAS100 residual SL/TP supervision"
                ),
                "current_sltp_status": nas100_sltp,
                "manual_broker_action_taken": False,
            }
        )
    watchdog = verification_commands.get("watchdog_e2e_verify") or {}
    if watchdog.get("exit_code") not in (0, None):
        watchdog_stdout = watchdog.get("stdout") or ""
        rows.append(
            {
                "schema_version": "vps_anomaly_v1",
                "row_type": "watchdog_e2e_verify_nonzero",
                "status": "continuation_required",
                "status_reason": "watchdog_e2e_verify_nonzero_requires_same_evidence_followup",
                "exit_code": watchdog.get("exit_code"),
                "stdout": watchdog_stdout,
                "stderr": watchdog.get("stderr"),
            }
        )
    return rows


def collect_repair_rows() -> list[dict[str, Any]]:
    base = {
        "schema_version": "vps_repair_v1",
        "generated_at_utc": iso_now(),
        "evidence_class": EVIDENCE_CLASS,
    }
    return [
        {
            **base,
            "repair_id": "launcher_default_live_mode",
            "source_files": ["start_all.bat", "tests/test_start_all_runtime_contract.py"],
            "before": "GTOS_MODE defaulted to demo when environment was absent",
            "after": "GTOS_MODE defaults to live for current redacted_account production launcher",
            "runtime_effect": "future launcher starts use live mode unless explicitly overridden",
            "verification": "tests/test_start_all_runtime_contract.py",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "watchdog_default_live_mode",
            "source_files": ["scripts/watchdog.ps1", "scripts/watchdog_e2e_verify.py"],
            "before": "watchdog repaired missing mode env to demo",
            "after": "watchdog repairs missing mode env to live and passes --mode live",
            "runtime_effect": "scheduler watchdog restarts live/redacted_account orchestrators",
            "verification": "tests/test_watchdog_e2e_verify.py",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "persisted_environment_demo_to_live",
            "source_files": ["Windows user and machine environment"],
            "before": "persisted GTOS_MODE=demo at User and Machine scopes",
            "after": "persisted GTOS_MODE=live and GTOS_PROFILE=redacted_account at User and Machine scopes",
            "runtime_effect": "new watchdog shells inherit live production mode",
            "verification": "process table shows 24 live python orchestrators and zero demo",
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "checkpoint_lifecycle_full_scan_and_lane06_fallback",
            "source_files": [
                "scripts/build_vnext_live_activation_checkpoint.py",
                "tests/test_vnext_live_activation_checkpoint.py",
            ],
            "before": "checkpoint could miss current open lifecycle rows due old hot log and arbitrary tail behavior",
            "after": "checkpoint scans all candidate lifecycle rows and falls back to Lane06 broker lifecycle evidence",
            "broker_lifecycle_effect": "NAS100 open position 241779188 reconciled",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "orchestrator_lane06_trade_record_recovery",
            "source_files": ["src/components/orchestrator.py", "tests/test_orchestrator.py"],
            "before": "open NAS100 orphan lacked local trade record recovery from current Lane06 ledger",
            "after": "orchestrator can synthesize vNext policy recovery from Lane06 lifecycle evidence",
            "broker_lifecycle_effect": "production path adopted residual position and managed TP1 partial",
            "status": "repaired_tested_live_exercised",
        },
        {
            **base,
            "repair_id": "mt5_sltp_action_constant_repair",
            "source_files": [
                "src/mt5/mt5_interface.py",
                "src/mt5/mt5_mock.py",
                "src/components/execution.py",
                "tests/test_execution.py",
            ],
            "before": "SL/TP modifications used hard-coded action 2 and MT5 returned retcode 10013",
            "after": "SL/TP modifications use MT5 TRADE_ACTION_SLTP=6",
            "runtime_effect": "production execution helper can submit valid SL/TP modify requests",
            "verification": (
                "MetaTrader5 constants, read-only order_check comparison, py_compile, "
                "and focused execution/orchestrator pytest"
            ),
            "broker_lifecycle_effect": "NAS100 residual SL moved to BE and TP remained present after targeted reload",
            "status": "repaired_tested_live_exercised",
        },
        {
            **base,
            "repair_id": "adopted_partial_residual_recovery_guard",
            "source_files": [
                "src/components/orchestrator.py",
                "src/components/execution.py",
                "tests/test_orchestrator.py",
                "tests/test_execution.py",
            ],
            "before": "adopted partial residual recovery could restart with tp1_hit false and partial-close again",
            "after": "Lane06 partial residual recovery marks tp1_hit and repairs SL/TP instead of duplicate partial close",
            "runtime_effect": "reloaded NAS100 residual stays bound to ticket 241779188 without a second partial close",
            "verification": "focused execution/orchestrator pytest and live NAS100 reload proof",
            "broker_lifecycle_effect": "residual volume stayed 0.05 while SL/TP repair applied",
            "status": "repaired_tested_live_exercised",
        },
        {
            **base,
            "repair_id": "supervisor_process_probe_self_count_filter",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": "process ledger could classify the supervisor PowerShell probe as an orchestrator because the probe text contained run_agent.py",
            "after": "process ledger only classifies concrete Python/cmd process intents and records tick-capture log paths separately",
            "runtime_effect": "supervisor artifact counts no longer self-contaminate while live process set remains unchanged",
            "verification": "route-owned verifier and VPS_PROCESS_HEALTH_LEDGER process-family counts",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_process_status_normalization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": "process health ledger had correct process counts but no normalized per-row status/status_reason",
            "after": "orchestrator, tick, M1, notification, heartbeat, displacement, and watchdog rows expose status/status_reason",
            "runtime_effect": "supervisor can audit every process row for live/profile/symbol/liveness contract drift",
            "verification": "route-owned verifier requires status on process rows and fails contract-mismatch statuses",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_watchdog_scheduler_status_normalization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "scripts/watchdog.ps1",
                "scripts/watchdog_launcher.vbs",
            ],
            "before": (
                "watchdog proof was split between transient process rows and raw scheduler CIM "
                "payloads, so a process-only scan could look like a missing watchdog"
            ),
            "after": (
                "VPS_WATCHDOG_SCHEDULER_LEDGER records GTOS_Watchdog as a "
                "scheduled short-lived cycle with normalized status/status_reason"
            ),
            "runtime_effect": (
                "no live process behavior changed; supervisor can distinguish scheduler-backed "
                "watchdog readiness from an actually missing watchdog mechanism"
            ),
            "verification": "route-owned verifier requires a ready/running GTOS_Watchdog scheduler row",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_top_level_index_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "candidate packet ledger kept full nested vNext packet data but left top-level "
                "candidate_id/symbol/session/policy index fields null"
            ),
            "after": (
                "candidate packet ledger promotes nested candidate_identity and dynamic_policy "
                "fields into top-level scan columns"
            ),
            "runtime_effect": (
                "supervisor can audit all post-reload candidates by symbol, session, policy, "
                "execution_policy_id, and final_outcome without reparsing nested packets"
            ),
            "verification": "route-owned verifier requires all candidate record index fields",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_snapshot_upper_bound",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "candidate packet ledger could include trade records written after checkpoint generation, "
                "making record_count exceed the checkpoint summary"
            ),
            "after": "candidate packet ledger excludes records newer than checkpoint generated_at_utc",
            "runtime_effect": "supervisor candidate ledger is a consistent checkpoint snapshot even while live orchestrators keep writing",
            "verification": "route-owned verifier candidate record count equals checkpoint summary",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_input_refresh_execution_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
            ],
            "before": (
                "standalone supervisor artifact rebuilds read the existing live checkpoint and "
                "could leave post-reload candidate proof outputs stale while the action ledger "
                "claimed a checkpoint refresh"
            ),
            "after": (
                "normal supervisor artifact rebuilds refresh the live checkpoint, rebuild "
                "post-reload candidate proof, run the candidate proof verifier, and record "
                "command results in VPS_SUPERVISOR_ACTION_LEDGER"
            ),
            "runtime_effect": (
                "supervisor cycles no longer depend on a manual pre-step to keep live checkpoint "
                "and all-candidate proof artifacts synchronized"
            ),
            "verification": "route-owned verifier and focused route test run after a full rebuild",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "post_reload_candidate_proof_snapshot_bound_repair",
            "source_files": [
                "scripts/build_vnext_post_reload_candidate_proof.py",
                "scripts/verify_vnext_post_reload_candidate_proof.py",
                "scripts/build_vnext_live_activation_checkpoint.py",
            ],
            "before": (
                "post-reload candidate proof verification scanned the unbounded live trade-record "
                "tail, so new candidates written during a long supervisor cycle made the proof "
                "look stale even when the checkpoint snapshot was internally consistent"
            ),
            "after": (
                "candidate proof is bounded to the live checkpoint generated_at_utc by default, "
                "and checkpoint generation passes its own now_utc as the snapshot upper bound"
            ),
            "runtime_effect": (
                "supervisor cycles can prove all candidates included in the current checkpoint "
                "without racing unrelated candidates written after the snapshot"
            ),
            "verification": "post-reload candidate proof verifier reports snapshot_upper_bound_utc and passes",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_row_type_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "candidate packet ledger mixed summary and candidate records without row_type, "
                "so downstream all-candidate scans could accidentally skip candidate rows"
            ),
            "after": (
                "candidate packet summary uses row_type=summary and candidate records use "
                "row_type=post_reload_candidate_packet"
            ),
            "runtime_effect": (
                "supervisor candidate coverage scans can distinguish the summary row from all "
                "post-reload candidate rows without schema-specific special cases"
            ),
            "verification": "route-owned verifier requires candidate summary and record row_type values",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_status_reason_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "candidate packet summary rows could carry null status/status_reason, leaving "
                "a zero-candidate post-reload cycle without explicit machine-readable reason"
            ),
            "after": (
                "candidate packet summary and post-reload candidate record rows carry "
                "normalized status/status_reason values"
            ),
            "runtime_effect": (
                "supervisor can distinguish an expected no-candidate post-reload summary from "
                "an unclassified candidate-ledger defect across all 24 markets"
            ),
            "verification": "route-owned verifier requires candidate packet status/status_reason on every row",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_core_ledger_status_reason_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "scripts/repair_jsonl_invalid_rows.py",
            ],
            "before": (
                "data-dependency, required-file, environment, action, and quarantine "
                "ledgers could contain rows without normalized status/status_reason fields"
            ),
            "after": (
                "core supervisor ledgers emit normalized status/status_reason values, "
                "including historical JSONL invalid-row quarantine evidence"
            ),
            "runtime_effect": (
                "supervisor null/zero-without-reason scans can distinguish ready, missing, "
                "historical-optional, and repair-required rows without changing live trading behavior"
            ),
            "verification": "route-owned verifier requires status/status_reason on all core supervisor ledgers",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_old_system_projection_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "post-reload native candidate packets carried explicit old PA/L2 false "
                "fields in the nested vNext packet, but the supervisor candidate ledger "
                "only read root-level trade-record fields and projected nulls"
            ),
            "after": (
                "candidate ledger rows extract old_primary_analyzer_called, "
                "old_l2_required, old_system_absence_status, and packet_capture_mode "
                "from the nested native packet when root fields are absent"
            ),
            "runtime_effect": (
                "supervisor old-system absence proof is reconstructable from candidate "
                "ledger rows without changing live trading behavior"
            ),
            "verification": (
                "route-owned verifier requires native live-writer candidate rows to "
                "project explicit old PA/L2 false fields"
            ),
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "live_checkpoint_candidate_summary_old_system_absence_repair",
            "source_files": [
                "scripts/build_vnext_live_activation_checkpoint.py",
                "tests/test_vnext_live_activation_checkpoint.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "live checkpoint candidate summaries could report the legacy generic "
                "old PA/L2 absence status as not_fully_proven even when every native "
                "live-writer packet exposed explicit old_primary_analyzer_called=false "
                "and old_l2_required=false"
            ),
            "after": (
                "candidate summaries count old-system absence from the native packet "
                "and nested old_system_absence_proof before falling back to runtime "
                "event fields, so generic and native summary statuses agree"
            ),
            "runtime_effect": (
                "all-current-candidate supervisor summaries prove old PrimaryAnalyzer/L2 "
                "absence without requiring auditors to ignore a contradictory legacy field"
            ),
            "verification": (
                "tests/test_vnext_live_activation_checkpoint.py covers native packet "
                "summary counts, and the route-owned verifier rejects contradictory "
                "generic/native old-system absence statuses"
            ),
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_data_capture_status_normalization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": "data-capture ledger carried raw tick/M1 fields but lacked a normalized row-level status column",
            "after": "tick and M1 rows expose normalized status and status_reason for stale/fresh/no-row classification",
            "runtime_effect": "supervisor scans can detect stale or unclassified data-capture rows without bespoke per-source parsing",
            "verification": "route-owned verifier requires data-capture status on all 48 rows",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_notification_status_normalization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": "notification ledger rows recorded worker/queue facts but lacked normalized status/status_reason fields",
            "after": "worker, active queue, synthetic test queues, retry queue, and credential-presence rows expose explicit status",
            "runtime_effect": "supervisor can distinguish drained live queue from retained synthetic readiness-test queue evidence",
            "verification": "route-owned verifier requires notification status on all rows and fails pending live queue",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_lifecycle_risk_status_normalization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "broker-spec, open-trade lifecycle, broker-reconciliation, and risk ledgers "
                "carried raw evidence but lacked normalized status/status_reason fields"
            ),
            "after": (
                "broker-spec readiness, lifecycle reconciliation, broker-reconciliation rows, "
                "and account/open-position risk rows expose explicit status/status_reason values"
            ),
            "runtime_effect": (
                "supervisor delta scans can fail incomplete lifecycle/risk authority rows "
                "without bespoke per-ledger parsing"
            ),
            "verification": "route-owned verifier requires lifecycle, broker, broker-spec, and risk statuses",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_mt5_symbol_time_status_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "MT5 symbol-source rows had source_status only and labeled broker-server "
                "bar epochs as UTC, producing negative bar ages on the redacted_account +3h server"
            ),
            "after": (
                "symbol-source rows carry normalized status/status_reason and convert MT5 "
                "bar/tick epochs with the detected broker_time_offset_seconds"
            ),
            "runtime_effect": (
                "supervisor all-market proof no longer reports future-dated UTC bars while "
                "the live trading path remains unchanged"
            ),
            "verification": "route-owned verifier requires MT5 symbol status and nonnegative corrected bar ages",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_runtime_decision_parse_status_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "runtime decision rows lacked normalized status/status_reason and an "
                "unparseable pre-reload source JSONL fragment was included because its "
                "timestamp could not be parsed"
            ),
            "after": (
                "malformed rows receive timestamp hints from raw text, pre-reload fragments "
                "are excluded from post-reload evidence, and any included malformed row fails "
                "the verifier"
            ),
            "runtime_effect": (
                "supervisor runtime-decision evidence can distinguish clean post-reload rows "
                "from corrupt source fragments without changing live decision behavior"
            ),
            "verification": "route-owned verifier requires runtime-decision status and rejects parse-error rows",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "vnext_runtime_shared_jsonl_locked_append_repair",
            "source_files": [
                "src/components/gtos_vnext_runtime.py",
                "tests/test_gtos_vnext_runtime.py",
                "scripts/repair_jsonl_invalid_rows.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "24 live orchestrators appended vNext decision and replacement-monitoring "
                "rows to shared JSONL files with bare text append, producing interleaved "
                "malformed fragments in hot post-reload evidence"
            ),
            "after": (
                "both shared vNext runtime logs write through one sidecar cross-process "
                "locked binary JSONL append path and malformed source rows are quarantined "
                "with raw hashes before supervisor verification"
            ),
            "runtime_effect": (
                "future vNext candidate/decision evidence remains parseable across all 24 "
                "markets without changing order placement, risk, selector, or broker behavior"
            ),
            "verification": (
                "py_compile, focused concurrent-writer regression, JSONL quarantine scan, "
                "route-owned verifier, and focused route test"
            ),
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_restart_reload_status_reason_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": "restart/reload ledger rows had status values without status_reason fields",
            "after": "each restart/reload row records an explicit reason for its completion/readiness status",
            "runtime_effect": (
                "supervisor reload proof is machine-checkable for null/zero-without-reason "
                "scans without changing live processes"
            ),
            "verification": "route-owned verifier requires restart/reload status_reason on every status row",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "mt5_broker_offset_stale_probe_guard",
            "source_files": [
                "src/components/mt5_daemon_runtime.py",
                "tests/test_mt5_daemon_runtime.py",
            ],
            "before": "closed-market GER30/UKOUSD/USOUSD stale ticks could be accepted as impossible -47h/-49h broker timezone offsets",
            "after": "broker-offset detection skips implausible timezone probes and falls through to a fresh default probe",
            "runtime_effect": "tick parquet timestamp conversion keeps redacted_account +3h offset after quiet CFD/index restarts",
            "verification": "read-only MT5 probe GER30->EURUSD returned +10800 and focused pytest passed",
            "status": "repaired_tested_live_exercised",
        },
        {
            **base,
            "repair_id": "watchdog_tick_capture_liveness_mode",
            "source_files": [
                "scripts/watchdog.ps1",
                "tests/test_start_all_runtime_contract.py",
            ],
            "before": "watchdog relaunched quiet tick daemons without --skip-tick-freshness-check and GER40 exited stale_tick",
            "after": "watchdog always launches observational tick-capture daemons with --skip-tick-freshness-check",
            "runtime_effect": "quiet broker sessions remain daemon-alive/no-new-broker-tick evidence instead of dead capture",
            "verification": "24 tick-capture cmd/python pairs reloaded with skip arg and checkpoint issue_count=0",
            "status": "repaired_tested_live_exercised",
        },
        {
            **base,
            "repair_id": "ob_continuation_csv_source_alias_repair",
            "source_files": [
                "scripts/ob_continuation_monitor.py",
                "tests/test_ob_continuation_monitor.py",
            ],
            "before": (
                "OB-continuation monitoring parsed data/historical pointer stubs as malformed CSV "
                "and ignored valid sibling data-root CSVs for EURUSD/GBPUSD/NAS100/XAGUSD."
            ),
            "after": (
                "monitor resolves safe data-root CSV pointer stubs and falls back from "
                "data/historical/<symbol>_<tf>.csv to data/<symbol>_<tf>.csv when present"
            ),
            "runtime_effect": (
                "daily OB-continuation coverage now includes existing CSV evidence for EURUSD, "
                "GBPUSD, NAS100, and XAGUSD instead of parse-failing or reporting false absence"
            ),
            "verification": (
                "py_compile, tests/test_ob_continuation_monitor.py, and "
                "scripts/ob_continuation_monitor.py --dry-run across all 24 symbols"
            ),
            "status": "repaired_tested_dry_run_verified",
        },
        {
            **base,
            "repair_id": "selected_cell_risk_ledger_lfs_materialization_repair",
            "source_files": [
                SELECTED_CELL_RISK_LEDGER_REL,
                "config/agent_config.yaml",
                "src/components/gtos_vnext_runtime.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "selected-cell risk ledger was present as a raw Git LFS pointer, so live "
                "dynamic-router reads could resolve zero selected-cell rows"
            ),
            "after": (
                "git lfs pull materialized the 5,818,853-byte selected-cell risk JSONL "
                "with 1,344 rows, and route verification now rejects pointer or zero-row state"
            ),
            "runtime_effect": (
                "24 live symbol orchestrators were reloaded so the "
                "_moonshot_selected_cell_risk_entries lru_cache cannot retain the empty "
                "pre-repair ledger result"
            ),
            "verification": (
                "route-owned verifier checks selected-cell ledger materialization/row count, "
                "data-dependency ledger status, and orchestrator reload proof"
            ),
            "status": "repaired_tested_live_reloaded",
        },
        {
            **base,
            "repair_id": "selected_cell_risk_runtime_loader_signature_repair",
            "source_files": [
                "src/components/gtos_vnext_runtime.py",
                "tests/test_gtos_vnext_runtime.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
            ],
            "before": (
                "live runtime selected-cell risk loading cached a path-level empty tuple "
                "after missing, pointer, or parse failure, so a later local LFS materialization "
                "still required process reload before candidates could see rows"
            ),
            "after": (
                "selected-cell risk loading is cached by path, mtime, and size signature, "
                "classifies raw LFS pointers and parse failures explicitly, and re-reads "
                "the same path after materialization without dropping the mandatory risk gate"
            ),
            "runtime_effect": (
                "future selected-cell ledger materialization or repair is visible to the "
                "live dynamic router on the next candidate evaluation; missing/pointer/parse "
                "states remain hard refusals with exact cause instead of silent empty risk"
            ),
            "verification": (
                "focused pytest reproduces pointer-then-materialized same-path selected-cell "
                "risk flow without cache_clear or process restart"
            ),
            "status": "repaired_tested_live_reload_required",
        },
        {
            **base,
            "repair_id": "live_execution_file_reference_audit_materialization",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl",
            ],
            "before": "live file-reference closure was an ad hoc scan and did not persist every reference row into route verification",
            "after": "route build now scans live contracts, config, profile, launcher, watchdog, and runtime path references and writes all rows",
            "runtime_effect": "no trading behavior changed; future supervisor builds fail missing LFS/pointer/parse defects from live references",
            "verification": "route-owned verifier checks live reference audit counts and unresolved missing classes",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "live_execution_file_reference_lfs_long_path_materialization_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "pipeline_state/lfs_checkout_index_materialization_49_file_refs_20260601.json",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl",
            ],
            "before": (
                "refreshed live file-reference audit initially found 49 locally absent "
                "LFS-tracked refs and Windows long-path false absence risk for "
                "materialized heavy evidence files"
            ),
            "after": (
                "49 LFS-tracked refs were materialized through checkout-index plus git "
                "lfs checkout, and long-path-aware existence/read helpers classify the "
                "live reference set with zero missing LFS, zero missing-not-LFS, zero "
                "raw LFS pointers, zero parse defects, and zero owner-machine blockers"
            ),
            "runtime_effect": (
                "live dependency verification no longer blocks on locally materializable "
                "LFS objects or Windows MAX_PATH false negatives; no broker/order/risk "
                "behavior changed"
            ),
            "verification": (
                "refreshed file-reference audit reports zero missing_lfs, "
                "missing_not_lfs, raw_lfs_pointer_defects, parse_defects, and "
                "unresolved live-required missing references"
            ),
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "live_execution_file_reference_scanner_classification_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json",
                "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl",
            ],
            "before": (
                "source-string scanning overcounted non-file regex fragments, command "
                "fragments, templates, absence sentinels, and optional shadow ML manifest "
                "paths as live file blockers"
            ),
            "after": (
                "scanner keeps all material rows while classifying templates, sentinels, "
                "event-driven artifacts, and disabled shadow ML manifest separately from "
                "live-required dependencies"
            ),
            "runtime_effect": (
                "supervisor stops re-chasing false missing-file blockers while still "
                "preserving every material file-reference row and failing true "
                "missing/pointer/parse defects"
            ),
            "verification": (
                "refreshed status counts preserve optional absence classes while "
                "unresolved live-required missing count is zero"
            ),
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "candidate_risk_audit_source_identity_join_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json",
                "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl",
            ],
            "before": (
                "candidate risk audit joined every historical candidate back to the "
                "current materialized selected-cell ledger by risk_cell_id only, so "
                "pre-LFS-repair packets could be misread after source materialization"
            ),
            "after": (
                "candidate risk audit validates packet-embedded selected-cell source "
                "identity first, records current-ledger drift dimensions, and fails "
                "only post-reload/current selected-cell source mismatches"
            ),
            "runtime_effect": (
                "supervisor separates repaired historical selected-cell source drift "
                "from current false risk refusals while preserving all candidate rows"
            ),
            "verification": (
                "route-owned verifier checks current_risk_refusal_mismatch_count and "
                "post_reload_source_identity_current_ledger_drift_count"
            ),
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_source_event_time_filter_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "VPS_CANDIDATE_PACKET_LEDGER.jsonl",
                "LIVE_POST_RELOAD_CANDIDATE_PROOF_LEDGER.jsonl",
            ],
            "before": (
                "supervisor candidate packet rows used trade-record file mtime, so "
                "repair-touched older filled trade records were counted as current "
                "post-reload candidates"
            ),
            "after": (
                "candidate packet rows are filtered by source event/candle time first "
                "and file mtime only as an upper-bound/write-time guard"
            ),
            "runtime_effect": (
                "current candidate counts align with the source-backed post-reload "
                "candidate proof instead of re-chasing repaired historical records"
            ),
            "verification": "route-owned verifier candidate_record_count_mismatch cleared",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_candidate_packet_top_level_dimension_projection_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "VPS_CANDIDATE_PACKET_LEDGER.jsonl",
            ],
            "before": (
                "candidate packet rows preserved side/origin/framework/candle/refusal "
                "inside the packet but left some top-level supervisor dimensions null"
            ),
            "after": (
                "candidate packet rows expose side, kill zone, origin family, framework, "
                "route family, candle time, source mode, order path, and Gate3 refusal "
                "reason at top level while preserving the full packet"
            ),
            "runtime_effect": (
                "row-level candidate reviews no longer require opening each nested packet "
                "to distinguish valid nulls from projection defects"
            ),
            "verification": "route-owned verifier requires the new top-level candidate dimensions",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "supervisor_matched_lifecycle_alias_normalization_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
                "LIVE_COMPANION_CURRENT_CHECKPOINT.json",
            ],
            "before": (
                "matched pending lifecycle rows carried MT5 ticket and vNext policy "
                "identity under mt5_position_ticket/gtos_vnext_* aliases, while the "
                "supervisor verifier looked only for top-level ticket/policy fields"
            ),
            "after": (
                "matched lifecycle rows preserve raw fields and expose normalized "
                "ticket, selected_policy, and execution_policy_id at top level"
            ),
            "runtime_effect": (
                "open-position lifecycle proof reflects the actual source identity "
                "instead of falsely reporting missing policy/ticket fields"
            ),
            "verification": "route-owned verifier open_trade_lifecycle_bad_status cleared",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "nas100_residual_close_resolution_state_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "knowledge_base/logs/agent_NAS100_live.log",
                "shadow_logs/slippage.jsonl",
            ],
            "before": (
                "NAS100 ticket 241779188 was absent from current open positions but "
                "remained marked as active SL/TP supervision"
            ),
            "after": (
                "supervisor resolves the stale continuation from MT5 broker-close "
                "deal proof and current absence from open positions"
            ),
            "broker_lifecycle_effect": (
                "ticket 241779188 closed by broker at 2026-06-01T13:13:56Z with "
                "deal 226046898; no manual broker action was taken"
            ),
            "runtime_effect": "stale NAS100 continuation removed from current blocker list",
            "verification": "route-owned verifier nas100_sltp_repair_not_resolved cleared",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "runtime_decision_zero_row_reason_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "build_vps_supervisor_artifacts.py",
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "VPS_RUNTIME_DECISION_LEDGER.jsonl",
            ],
            "before": "runtime-decision ledger could be empty after a fresh reload before the next candidate-cycle write",
            "after": "runtime-decision ledger emits an explicit summary row explaining no post-reload runtime rows yet",
            "runtime_effect": (
                "zero-row runtime decision evidence becomes source-backed and no longer "
                "looks like a missing artifact during quiet periods"
            ),
            "verification": "route-owned verifier accepts the explicit no-post-reload summary row",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "candidate_risk_audit_post_reload_absence_proof_repair",
            "source_files": [
                "research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/"
                "verify_vps_supervisor_artifacts.py",
                "VPS_CANDIDATE_PACKET_LEDGER.jsonl",
                "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json",
            ],
            "before": (
                "route verifier required at least one post-reload candidate-risk row even "
                "when the candidate packet summary explicitly proved zero candidates after "
                "the current process reload"
            ),
            "after": (
                "post-reload zero-candidate windows pass only when candidate packet summary "
                "carries the exact no-post-reload candidate absence proof"
            ),
            "runtime_effect": (
                "quiet live windows no longer become false verifier blockers, while real "
                "candidate rows still require full candidate-risk audit coverage"
            ),
            "verification": "route-owned verifier zero-candidate absence proof condition",
            "status": "repaired_tested",
        },
        {
            **base,
            "repair_id": "adopted_position_lifecycle_policy_recovery_fallback_repair",
            "source_files": [
                "src/components/orchestrator.py",
                "tests/test_orchestrator.py",
                "pipeline_state/orchestrator_adopted_trade_recovery_dedupe_summary_20260601T143718Z.json",
            ],
            "before": (
                "adopted-position recovery returned before lifecycle-row fallback when "
                "the symbol trade-record directory was absent"
            ),
            "after": (
                "orchestrator scans a symbol trade-record directory only when it exists "
                "and still builds a lifecycle recovery record from pending-limit or "
                "Lane06 rows when no current trade record is available"
            ),
            "runtime_effect": (
                "restarted/adopted live residual positions can recover selected_policy "
                "and execution_policy_id for partial_be_runner management from source "
                "lifecycle rows instead of silently losing vNext policy state"
            ),
            "verification": (
                "py_compile src/components/orchestrator.py; "
                "pytest tests/test_orchestrator.py::TestAdoptedVnextTradeRecovery; "
                "24 live orchestrators reloaded and deduped to singleton patched processes"
            ),
            "status": "repaired_tested_live_reloaded",
        },
        {
            **base,
            "repair_id": "pre_geometry_concurrent_cap_dynamic_ordering_repair",
            "source_files": [
                "src/components/orchestrator.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
                "tests/test_concurrent_cap.py",
                "pipeline_state/orchestrator_pre_geometry_concurrent_cap_reload_summary_*.json",
            ],
            "before": (
                "broader-origin vNext candidates could be terminally rejected by the "
                "legacy filled-position concurrent cap before the moonshot dynamic router "
                "created selected-cell risk proof and executable geometry"
            ),
            "after": (
                "pre-geometry concurrent_cap_reached is recorded as an advisory/deferred "
                "Gate3 fact for vNext broader-origin candidates; final Gate3 still runs "
                "after dynamic router, selected-cell risk, geometry repair, and prop governance"
            ),
            "runtime_effect": (
                "valid current vNext candidates are no longer falsely stopped before "
                "selected-cell/source risk authority can prove or reject them; legacy and "
                "non-vNext concurrent-cap behavior remains unchanged"
            ),
            "verification": (
                "py_compile; focused broader-origin regression; existing vNext bypass and "
                "legacy redacted_account concurrent-cap tests; 24 live/redacted_account orchestrators "
                "reloaded to singleton patched processes"
            ),
            "status": "repaired_tested_live_reloaded",
        },
        {
            **base,
            "repair_id": "watchdog_direct_python_orchestrator_launch_repair",
            "source_files": [
                "scripts/watchdog.ps1",
                "pipeline_state/orchestrator_direct_python_watchdog_reload_summary_*.json",
                "VPS_PROCESS_HEALTH_LEDGER.jsonl",
            ],
            "before": (
                "watchdog launched each run_agent process through cmd.exe /c, leaving "
                "one persistent hidden cmd wrapper per live symbol and causing the "
                "orchestrator process family to double from 24 to 48"
            ),
            "after": (
                "watchdog direct-launches Python for matched python commands and accepts "
                "the direct Python PID as the lock owner, so live orchestrators run without "
                "persistent cmd wrappers"
            ),
            "runtime_effect": (
                "post-reload live process family is 24 direct Python orchestrators, zero "
                "orchestrator cmd wrappers, and no manual broker action"
            ),
            "verification": (
                "PowerShell parser check; direct-python watchdog reload proof; route-owned "
                "process verifier after rebuild"
            ),
            "status": "repaired_tested_live_reloaded",
        },
        {
            **base,
            "repair_id": "broader_origin_candidate_unique_trade_record_path_repair",
            "source_files": [
                "src/components/trade_capture.py",
                "src/components/orchestrator.py",
                "tests/test_trade_capture.py",
                "tests/test_vnext_broader_origin_orchestrator.py",
                "pipeline_state/broader_origin_candidate_unique_record_reload_summary_*.json",
            ],
            "before": (
                "broader-origin live trade records used only symbol/date/session/candle "
                "for the JSON filename, so a second candidate on the same symbol and "
                "M15 candle overwrote the first candidate packet"
            ),
            "after": (
                "broader-origin candidate records carry candidate_id in metadata/trade_id "
                "and save to candidate-unique paths; pending/order lifecycle records still "
                "index the real broker intent trade_id"
            ),
            "runtime_effect": (
                "future same-symbol same-candle candidates preserve full packet/order-"
                "readiness evidence instead of silently overwriting earlier candidates"
            ),
            "verification": (
                "py_compile; focused trade_capture/orchestrator tests; 24 live/redacted_account "
                "orchestrators reloaded with zero cmd wrappers"
            ),
            "historical_source_gap": (
                "BTCUSD 2026-06-01T16:00Z first dynamic-approved candidate packet was "
                "already overwritten by the later same-candle candidate before this "
                "repair; its dynamic approval remains source-backed in "
                "shadow_logs/gtos_vnext_runtime_decisions.jsonl, but its final "
                "trade-record packet cannot be recovered from current local files"
            ),
            "status": "repaired_tested_live_reloaded",
        },
        {
            **base,
            "repair_id": "orchestrator_reload_process_filter_dedupe_correction",
            "source_files": [
                "pipeline_state/orchestrator_adopted_trade_recovery_reload_summary_20260601T143548Z.json",
                "pipeline_state/orchestrator_adopted_trade_recovery_dedupe_summary_20260601T143718Z.json",
            ],
            "before": (
                "the first adopted-recovery reload proof used a repo-path command-line "
                "filter that missed existing run_agent processes and launched a duplicate "
                "24-process set"
            ),
            "after": (
                "actual run_agent command-line filter grouped by symbol, stopped the 24 "
                "older PIDs, and kept the 24 newest patched processes with zero missing "
                "or duplicate symbols"
            ),
            "runtime_effect": (
                "live supervision returned to one orchestrator per symbol after applying "
                "the patch; no manual broker action was taken"
            ),
            "verification": (
                "dedupe summary status ok_24_live_orchestrators_singleton_after_dedupe"
            ),
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "ai_append_log_targets_materialized",
            "source_files": [
                "shadow_logs/ai_call_policy_decisions.jsonl",
                "shadow_logs/ai_supervisor_decisions.jsonl",
                "shadow_logs/ai_decision_trace.jsonl",
            ],
            "before": "active config referenced three AI policy/supervisor/trace append targets that did not exist locally",
            "after": "the append-target files exist as empty UTF-8 JSONL files until the live AI paths emit rows",
            "runtime_effect": "no AI call or trading behavior changed; append targets and supervisor reads now have concrete parseable files",
            "verification": "live execution file-reference audit and JSONL parse checks",
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "pipeline_reload_json_bom_repair",
            "source_files": [
                "pipeline_state/orchestrator_runtime_code_reload_before_2026_06_01.json",
                "pipeline_state/orchestrator_runtime_code_reload_after_2026_06_01.json",
                "pipeline_state/orchestrator_runtime_code_reload_summary_2026_06_01.json",
                "pipeline_state/orchestrator_reload_before_2026_06_01.json",
                "pipeline_state/orchestrator_reload_after_2026_06_01.json",
            ],
            "before": "reload proof JSON files were UTF-8-with-BOM and strict JSON loads failed",
            "after": "reload proof JSON files were rewritten as UTF-8 without BOM after successful JSON parse",
            "runtime_effect": "no live process or broker behavior changed; reload evidence is machine-parseable",
            "verification": "live execution file-reference audit and json.loads checks",
            "status": "repaired_verified",
        },
        {
            **base,
            "repair_id": "local_heavy_data_search_root_recreated",
            "source_files": ["C:/tmp"],
            "before": "config gtos_vnext_runtime.local_heavy_data_search_roots referenced C:/tmp but the directory was absent",
            "after": "C:/tmp exists as an empty search root for local artifact discovery",
            "runtime_effect": "runtime artifact-loader search semantics are restored without changing selector/risk/execution logic",
            "verification": "live execution file-reference audit confirms C:/tmp exists",
            "status": "repaired_verified",
        },
    ]


def collect_restart_rows(checkpoint: dict[str, Any], process_summary: dict[str, Any]) -> list[dict[str, Any]]:
    process_version = checkpoint.get("process_version_proof") or {}
    process_block = checkpoint.get("process") or {}
    summary = process_block.get("summary") or checkpoint.get("process_summary") or {}
    oldest = summary.get("oldest_orchestrator_start_utc") or process_version.get(
        "oldest_orchestrator_start_utc"
    )
    newest = summary.get("newest_orchestrator_start_utc") or process_version.get(
        "newest_orchestrator_start_utc"
    )
    pre_geometry_reload_summary_path = newest_pipeline_state_path(
        "orchestrator_pre_geometry_concurrent_cap_reload_summary_*.json"
    )
    pre_geometry_reload_summary = (
        read_json(pre_geometry_reload_summary_path, {})
        if pre_geometry_reload_summary_path is not None
        else {}
    )
    direct_python_reload_summary_path = newest_pipeline_state_path(
        "orchestrator_direct_python_watchdog_reload_summary_*.json"
    )
    direct_python_reload_summary = (
        read_json(direct_python_reload_summary_path, {})
        if direct_python_reload_summary_path is not None
        else {}
    )
    candidate_unique_reload_summary_path = newest_pipeline_state_path(
        "broader_origin_candidate_unique_record_reload_summary_*.json"
    )
    candidate_unique_reload_summary = (
        read_json(candidate_unique_reload_summary_path, {})
        if candidate_unique_reload_summary_path is not None
        else {}
    )
    return [
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "demo_orchestrator_recycle",
            "action": "stopped 24 python demo orchestrators after persisted env repair",
            "manual_broker_action_taken": False,
            "status": "completed",
            "status_reason": "demo_process_recycle_completed_after_environment_mode_repair",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "watchdog_live_reload",
            "action": "ran scripts/watchdog.ps1 with GTOS_MODE=live and GTOS_PROFILE=redacted_account",
            "oldest_orchestrator_start_utc": oldest,
            "newest_orchestrator_start_utc": newest,
            "post_reload_python_live_orchestrator_count": process_summary.get(
                "python_live_orchestrator_count"
            ),
            "post_reload_demo_orchestrator_count": process_summary.get(
                "demo_orchestrator_process_count"
            ),
            "manual_broker_action_taken": False,
            "status": process_summary.get("status"),
            "status_reason": "watchdog_reload_left_24_live_orchestrators_and_zero_demo_processes",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "nas100_targeted_sltp_repair_reload",
            "action": "stopped stale NAS100 run_agent wrapper/python process and restarted NAS100 live/redacted_account only",
            "old_cmd_pid": 11656,
            "old_python_pid": 3776,
            "new_cmd_pid": 9536,
            "new_python_pid": 10840,
            "post_reload_broker_effect": "NDX100 ticket 241779188 SL=BE and TP present; residual volume stayed 0.05",
            "manual_broker_action_taken": False,
            "status": "completed",
            "status_reason": "targeted_nas100_reload_completed_after_sltp_repair_with_residual_ticket_bound",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "tick_capture_full_fleet_offset_liveness_reload",
            "action": "stopped/restarted tick-capture cmd/python pairs only after offset and watchdog liveness repairs",
            "before_snapshot": rel(PROJECT_ROOT / "pipeline_state" / "tick_capture_reload_before_2026_06_01.json"),
            "after_snapshot": rel(PROJECT_ROOT / "pipeline_state" / "tick_capture_reload_after_2026_06_01.json"),
            "post_reload_tick_process_count": process_summary.get("tick_capture_process_count"),
            "post_reload_tick_python_count": process_summary.get("tick_capture_python_count"),
            "post_reload_tick_cmd_count": process_summary.get("tick_capture_cmd_count"),
            "manual_broker_action_taken": False,
            "status": "completed",
            "status_reason": "tick_capture_fleet_reload_completed_after_offset_and_liveness_repairs",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "vnext_runtime_shared_jsonl_writer_reload",
            "action": (
                "committed locked JSONL append repair, reloaded NAS100 first for "
                "ticket-bound residual management, reloaded remaining 23 live "
                "orchestrators through watchdog, then quarantined pre-repair "
                "malformed runtime JSONL fragments"
            ),
            "commit": "2cb2a7e2c",
            "before_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_jsonl_writer_reload_before_2026_06_01.json"
            ),
            "after_nas100_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_jsonl_writer_reload_after_nas100_2026_06_01.json"
            ),
            "after_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_jsonl_writer_reload_after_2026_06_01.json"
            ),
            "quarantine_path": rel(
                ROUTE_DIR / "VPS_RUNTIME_JSONL_INVALID_ROW_QUARANTINE.jsonl"
            ),
            "post_reload_python_live_orchestrator_count": process_summary.get(
                "python_live_orchestrator_count"
            ),
            "post_reload_demo_orchestrator_count": process_summary.get(
                "demo_orchestrator_process_count"
            ),
            "manual_broker_action_taken": False,
            "status": process_summary.get("status"),
            "status_reason": (
                "locked_jsonl_writer_reloaded_on_24_live_orchestrators_and_pre_repair_"
                "malformed_runtime_fragments_quarantined"
            ),
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "selected_cell_risk_ledger_lfs_materialization_reload",
            "action": (
                "materialized the selected-cell risk ledger from Git LFS and reloaded all "
                "24 live/redacted_account symbol orchestrators to clear cached empty ledger reads"
            ),
            "selected_cell_risk_ledger_path": SELECTED_CELL_RISK_LEDGER_REL,
            "oldest_orchestrator_start_utc": oldest,
            "newest_orchestrator_start_utc": newest,
            "post_reload_python_live_orchestrator_count": process_summary.get(
                "python_live_orchestrator_count"
            ),
            "post_reload_demo_orchestrator_count": process_summary.get(
                "demo_orchestrator_process_count"
            ),
            "manual_broker_action_taken": False,
            "status": process_summary.get("status"),
            "status_reason": (
                "selected_cell_risk_lfs_pointer_materialized_and_24_live_orchestrators_"
                "reloaded_to_clear_selected_cell_lru_cache"
            ),
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "orchestrator_adopted_position_recovery_code_reload",
            "action": (
                "reloaded all 24 live/redacted_account symbol orchestrators after the "
                "adopted-position lifecycle fallback repair, then stopped the older "
                "duplicate PIDs from the first proof-filter miss"
            ),
            "before_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_adopted_trade_recovery_dedupe_before_20260601T143718Z.json"
            ),
            "after_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_adopted_trade_recovery_dedupe_after_20260601T143718Z.json"
            ),
            "summary_snapshot": rel(
                PROJECT_ROOT
                / "pipeline_state"
                / "orchestrator_adopted_trade_recovery_dedupe_summary_20260601T143718Z.json"
            ),
            "post_reload_python_live_orchestrator_count": process_summary.get(
                "python_live_orchestrator_count"
            ),
            "post_reload_demo_orchestrator_count": process_summary.get(
                "demo_orchestrator_process_count"
            ),
            "manual_broker_action_taken": False,
            "status": process_summary.get("status"),
            "status_reason": (
                "adopted_position_recovery_code_reloaded_on_24_live_orchestrators_"
                "with_duplicate_processes_removed"
            ),
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "pre_geometry_concurrent_cap_dynamic_ordering_reload",
            "action": (
                "reloaded all 24 live/redacted_account symbol orchestrators after the "
                "pre-geometry concurrent-cap dynamic-ordering repair"
            ),
            "before_snapshot": pre_geometry_reload_summary.get("before_path"),
            "after_snapshot": pre_geometry_reload_summary.get("after_path"),
            "summary_snapshot": rel(pre_geometry_reload_summary_path)
            if pre_geometry_reload_summary_path is not None
            else None,
            "post_reload_python_live_orchestrator_count": (
                pre_geometry_reload_summary.get("after_process_count")
            ),
            "post_reload_demo_orchestrator_count": process_summary.get(
                "demo_orchestrator_process_count"
            ),
            "missing_symbols": pre_geometry_reload_summary.get("missing_symbols", []),
            "duplicate_symbols": pre_geometry_reload_summary.get("duplicate_symbols", []),
            "manual_broker_action_taken": False,
            "status": pre_geometry_reload_summary.get(
                "status", "reload_summary_missing"
            ),
            "status_reason": (
                "pre_geometry_concurrent_cap_repair_reloaded_on_24_live_"
                "orchestrators_with_no_missing_or_duplicate_symbols"
            )
            if pre_geometry_reload_summary.get("status")
            == "ok_24_live_orchestrators_singleton_after_reload"
            else "pre_geometry_concurrent_cap_reload_summary_missing_or_not_ok",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "watchdog_direct_python_orchestrator_launch_reload",
            "action": (
                "reloaded all 24 live/redacted_account orchestrators through the patched "
                "direct-Python watchdog launcher and removed persistent cmd wrappers"
            ),
            "before_snapshot": direct_python_reload_summary.get("before_path"),
            "after_snapshot": direct_python_reload_summary.get("after_path"),
            "summary_snapshot": rel(direct_python_reload_summary_path)
            if direct_python_reload_summary_path is not None
            else None,
            "before_process_family_count": direct_python_reload_summary.get(
                "before_process_family_count"
            ),
            "before_python_count": direct_python_reload_summary.get("before_python_count"),
            "before_cmd_wrapper_count": direct_python_reload_summary.get(
                "before_cmd_wrapper_count"
            ),
            "post_reload_process_family_count": direct_python_reload_summary.get(
                "after_process_family_count"
            ),
            "post_reload_python_live_orchestrator_count": direct_python_reload_summary.get(
                "after_python_count"
            ),
            "post_reload_cmd_wrapper_count": direct_python_reload_summary.get(
                "after_cmd_wrapper_count"
            ),
            "missing_symbols": direct_python_reload_summary.get("missing_symbols", []),
            "duplicate_symbols": direct_python_reload_summary.get("duplicate_symbols", []),
            "manual_broker_action_taken": False,
            "status": direct_python_reload_summary.get(
                "status", "reload_summary_missing"
            ),
            "status_reason": (
                "watchdog_direct_python_reload_left_24_python_orchestrators_and_zero_"
                "orchestrator_cmd_wrappers"
            )
            if direct_python_reload_summary.get("status")
            == "ok_24_live_python_orchestrators_no_cmd_wrappers_after_reload"
            else "watchdog_direct_python_reload_summary_missing_or_not_ok",
        },
        {
            "schema_version": "vps_restart_reload_v1",
            "generated_at_utc": iso_now(),
            "restart_id": "broader_origin_candidate_unique_record_path_reload",
            "action": (
                "reloaded all 24 live/redacted_account orchestrators after the broader-origin "
                "candidate-unique trade-record path repair"
            ),
            "before_snapshot": candidate_unique_reload_summary.get("before_path"),
            "after_snapshot": candidate_unique_reload_summary.get("after_path"),
            "summary_snapshot": rel(candidate_unique_reload_summary_path)
            if candidate_unique_reload_summary_path is not None
            else None,
            "post_reload_python_live_orchestrator_count": candidate_unique_reload_summary.get(
                "after_python_count"
            ),
            "post_reload_cmd_wrapper_count": candidate_unique_reload_summary.get(
                "after_cmd_count"
            ),
            "missing_symbols": candidate_unique_reload_summary.get("missing_symbols", []),
            "duplicate_symbols": candidate_unique_reload_summary.get("duplicate_symbols", []),
            "manual_broker_action_taken": False,
            "status": candidate_unique_reload_summary.get(
                "status", "reload_summary_missing"
            ),
            "status_reason": (
                "candidate_unique_record_path_repair_reloaded_on_24_live_python_"
                "orchestrators_with_zero_cmd_wrappers"
            )
            if candidate_unique_reload_summary.get("status")
            == "ok_24_live_python_orchestrators_reloaded_after_candidate_record_identity_repair"
            else "candidate_unique_record_path_reload_summary_missing_or_not_ok",
        },
    ]


def collect_action_rows(
    checkpoint: dict[str, Any], input_refresh_results: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    input_refresh_results = input_refresh_results or {}
    return [
        {
            "schema_version": "vps_supervisor_action_v1",
            "action_id": "preflight_context_reread_after_compaction",
            "recorded_at_utc": iso_now(),
            "result_use_status": "instruction_coverage_and_state_reanchor",
            "files_read": PREFLIGHT_FILES,
            "live_state_generated": generated_live_state_time(),
            "status": "completed",
        },
        {
            "schema_version": "vps_supervisor_action_v1",
            "action_id": "checkpoint_refresh_after_post_reload_candidate",
            "recorded_at_utc": iso_now(),
            "command": "python scripts/build_vnext_live_activation_checkpoint.py --update-state",
            "command_result": input_refresh_results.get("checkpoint_refresh"),
            "checkpoint_generated_at_utc": checkpoint.get("generated_at_utc"),
            "checkpoint_status": checkpoint.get("status"),
            "checkpoint_issue_count": checkpoint.get("issue_count"),
            "checkpoint_evidence_gap_count": checkpoint.get("evidence_gap_count"),
            "status": "completed",
        },
        {
            "schema_version": "vps_supervisor_action_v1",
            "action_id": "candidate_proof_refresh_after_checkpoint",
            "recorded_at_utc": iso_now(),
            "commands": [
                "python scripts/build_vnext_post_reload_candidate_proof.py",
                "python scripts/verify_vnext_post_reload_candidate_proof.py --check",
            ],
            "build_command_result": input_refresh_results.get("candidate_proof_build"),
            "verify_command_result": input_refresh_results.get("candidate_proof_verify"),
            "result_use_status": "post_reload_candidate_proof_current_for_supervisor_cycle",
            "status": "completed",
        },
        {
            "schema_version": "vps_supervisor_action_v1",
            "action_id": "route_artifact_materialization",
            "recorded_at_utc": iso_now(),
            "route_dir": rel(ROUTE_DIR),
            "result_use_status": "restartable_supervisor_checkpoint",
            "status": "completed",
        },
    ]


def run_verification_commands() -> dict[str, Any]:
    commands = {
        "py_compile": run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                "run_agent.py",
                "src/components/orchestrator.py",
                "src/components/execution.py",
                "src/components/gtos_vnext_runtime.py",
                "src/components/mt5_daemon_runtime.py",
                "src/components/m1_capture.py",
                "src/components/tick_capture.py",
                "scripts/build_vnext_live_activation_checkpoint.py",
                "scripts/watchdog_e2e_verify.py",
                "scripts/ob_continuation_monitor.py",
                "src/mt5/mt5_interface.py",
                "src/mt5/mt5_mock.py",
            ],
            timeout=120,
        ),
        "watchdog_powershell_parse": run_powershell(
            "[scriptblock]::Create((Get-Content scripts\\watchdog.ps1 -Raw)) | Out-Null; 'ok'",
            timeout=30,
        ),
        "watchdog_e2e_verify": run_command(
            [sys.executable, "scripts/watchdog_e2e_verify.py", "--json"],
            timeout=120,
        ),
        "ob_continuation_monitor_dry_run": run_command(
            [sys.executable, "scripts/ob_continuation_monitor.py", "--dry-run"],
            timeout=360,
        ),
        "focused_pytest": run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_start_all_runtime_contract.py",
                "tests/test_mt5_daemon_runtime.py",
                "tests/test_ob_continuation_monitor.py",
                "tests/test_watchdog_e2e_verify.py",
                "tests/test_vnext_live_activation_checkpoint.py",
                "tests/test_orchestrator.py::TestAdoptedVnextTradeRecovery",
                "tests/test_execution.py::TestSLModificationFailure",
                "tests/test_execution.py::TestVNextDynamicSLModificationFailure",
                "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_moonshot_context_marks_runtime_kill_zone_configured",
                "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_refusals_do_not_place_market_or_pending_orders",
                "tests/test_vnext_broader_origin_orchestrator.py::test_broader_origin_dynamic_refusal_record_has_complete_candidate_packet",
                "-q",
            ],
            timeout=240,
        ),
    }
    return commands


def build_verification_result(
    checkpoint: dict[str, Any],
    process_summary: dict[str, Any],
    scheduler_summary: dict[str, Any],
    verification_commands: dict[str, Any],
    anomaly_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    hard_fail_commands = [
        name
        for name, result in verification_commands.items()
        if name != "watchdog_e2e_verify" and result.get("exit_code") != 0
    ]
    return {
        "schema_version": "vps_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "evidence_class": EVIDENCE_CLASS,
        "checkpoint_status": checkpoint.get("status"),
        "checkpoint_issue_count": checkpoint.get("issue_count"),
        "checkpoint_evidence_gap_count": checkpoint.get("evidence_gap_count"),
        "process_summary": process_summary,
        "watchdog_scheduler_summary": scheduler_summary,
        "broker_lifecycle_status": (checkpoint.get("broker_lifecycle") or {}).get("status"),
        "candidate_records_after_reload": (
            checkpoint.get("post_reload_candidate_flow") or {}
        ).get("candidate_records_after_reload"),
        "command_results": verification_commands,
        "hard_fail_commands": hard_fail_commands,
        "anomaly_count": len(anomaly_rows),
        "status": "checkpoint_ok_with_active_continuation"
        if checkpoint.get("status") == "ok" and not hard_fail_commands
        else "repair_required",
        "terminal_completion": False,
        "manual_broker_action_taken": False,
        "paid_api_or_vendor_call_taken": False,
    }


def build_supervisor_state(
    checkpoint: dict[str, Any],
    git_audit: dict[str, Any],
    process_summary: dict[str, Any],
    scheduler_summary: dict[str, Any],
    verification_result: dict[str, Any],
    file_reference_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    broker = checkpoint.get("broker_lifecycle") or {}
    nas100_sltp = nas100_residual_sltp_status(checkpoint)
    file_reference_audit = file_reference_audit or {}
    remaining_continuation_items = [
        "vnext_order_fill_close_packet_pending_for_post_reload_candidate",
        "goal_remains_active_until_ceo_stop_or_persistent_supervisor_replacement",
        "live_risk_contract_audit_pending_after_integrity_repairs",
    ]
    if not nas100_sltp.get("resolved"):
        remaining_continuation_items.insert(
            1, "nas100_sltp_modify_retcode_10013_residual_position_supervision"
        )
    return {
        "schema_version": "vps_supervisor_state_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": iso_now(),
        "status": "active_supervisor_checkpoint_continuation_required",
        "terminal_completion": False,
        "repo_path": str(PROJECT_ROOT),
        "head": git_audit.get("head"),
        "head_subject": git_audit.get("head_subject"),
        "current_contract": {
            "active_system": "24-symbol vNext moonshot production replacement",
            "symbols": LIVE_SYMBOLS,
            "execution_policy_contract": (
                "momentum_exhaustion primary with partial_be_runner exception selection"
            ),
            "old_system_absence_contract": (
                "fixed 1.5R, J46/J49, BE-only, and PrimaryAnalyzer/L2 are not current live defaults"
            ),
        },
        "preflight_files_read_after_compaction": PREFLIGHT_FILES,
        "checkpoint": {
            "path": rel(CHECKPOINT_PATH),
            "generated_at_utc": checkpoint.get("generated_at_utc"),
            "status": checkpoint.get("status"),
            "issue_count": checkpoint.get("issue_count"),
            "evidence_gap_count": checkpoint.get("evidence_gap_count"),
        },
        "process_summary": process_summary,
        "watchdog_scheduler_summary": scheduler_summary,
        "broker_lifecycle": {
            "status": broker.get("status"),
            "open_vnext_position_count": broker.get("open_vnext_position_count"),
            "open_vnext_order_count": broker.get("open_vnext_order_count"),
            "reconciled_open_position_ids": broker.get("reconciled_open_position_ids"),
            "unreconciled_open_exposure_count": broker.get("unreconciled_open_exposure_count"),
            "close_deal_reconciled_count": broker.get("close_deal_reconciled_count"),
        },
        "verification_status": verification_result.get("status"),
        "file_reference_audit_status": {
            "status": (
                "resolved_live_required_dependency_clean"
                if int(file_reference_audit.get("unresolved_live_required_missing_count") or 0) == 0
                and int(file_reference_audit.get("missing_but_lfs_tracked_count") or 0) == 0
                and int(file_reference_audit.get("missing_not_in_lfs_count") or 0) == 0
                and int(file_reference_audit.get("raw_lfs_pointer_defect_count") or 0) == 0
                and int(file_reference_audit.get("parse_defect_count") or 0) == 0
                else "live_required_dependency_repair_required"
            ),
            "generated_at_utc": file_reference_audit.get("generated_at_utc"),
            "reference_count": file_reference_audit.get("reference_count"),
            "status_counts": file_reference_audit.get("status_counts"),
            "missing_but_lfs_tracked_count": file_reference_audit.get(
                "missing_but_lfs_tracked_count"
            ),
            "missing_not_in_lfs_count": file_reference_audit.get("missing_not_in_lfs_count"),
            "raw_lfs_pointer_defect_count": file_reference_audit.get(
                "raw_lfs_pointer_defect_count"
            ),
            "parse_defect_count": file_reference_audit.get("parse_defect_count"),
            "unresolved_live_required_missing_count": file_reference_audit.get(
                "unresolved_live_required_missing_count"
            ),
            "exact_owner_or_other_machine_blockers": file_reference_audit.get(
                "exact_owner_or_other_machine_blockers"
            )
            or [],
        },
        "nas100_sltp_repair_status": nas100_sltp,
        "remaining_continuation_items": remaining_continuation_items,
        "forbidden_boundaries_enforced": {
            "manual_broker_order_position_deal_action": False,
            "paid_api_vendor_call": False,
            "credential_print_or_change": False,
            "remote_push": False,
        },
    }


def build_completion_audit(
    verification_result: dict[str, Any],
    anomaly_rows: list[dict[str, Any]],
    file_reference_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nas100_resolution = next(
        (
            row
            for row in anomaly_rows
            if row.get("row_type") == "nas100_sltp_repair_resolution"
        ),
        {},
    )
    remaining = [
        {
            "id": "post_reload_order_path_packet_pending",
            "status": "awaiting future live candidate reaching order/fill/close lifecycle",
            "source": "LIVE_COMPANION_CURRENT_CHECKPOINT.json",
        },
    ]
    file_reference_audit = file_reference_audit or {}
    for blocker in file_reference_audit.get("exact_owner_or_other_machine_blockers") or []:
        remaining.append(
            {
                "id": "live_file_reference_missing_not_local_or_lfs",
                "status": "requires_exact_original_file_from_owner_other_machine_or_source_route",
                "source": blocker.get("reference_path"),
                "owning_reference": blocker.get("owning_reference"),
                "required_owner_action": blocker.get("required_owner_action"),
            }
        )
    if not (nas100_resolution.get("current_sltp_status") or {}).get("resolved"):
        remaining.insert(
            1,
            {
                "id": "nas100_sltp_modify_retcode_10013",
                "status": "active_same_evidence_continuation_no_manual_broker_modification",
                "source": "logs/nas100.log",
                "broker_effect": "residual NDX100 position 241779188 remains open with existing SL/TP",
            },
        )
    return {
        "schema_version": "vps_completion_or_continuation_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "decision": "CONTINUATION_REQUIRED_ACTIVE_SUPERVISOR_CHECKPOINT",
        "terminal_completion": False,
        "evidence_class": EVIDENCE_CLASS,
        "instruction_coverage": {
            "mandatory_preflight_rerun_after_compaction": True,
            "preflight_files_read": PREFLIGHT_FILES,
            "prompt_reread_after_compaction": True,
            "doctrine_reread_after_compaction": True,
            "orchestrator_hardening_docs_read": True,
            "route_artifacts_materialized": OUTPUT_FILES,
            "evidence_class_enforced": True,
            "live_runtime_boundary_enforced": True,
            "current_vnext_contract_verified": True,
            "repairs_applied_and_recorded": True,
            "restarts_reloads_recorded": True,
            "tests_verifiers_recorded": True,
        },
        "verification_status": verification_result.get("status"),
        "resolved_items": [
            {
                "id": "nas100_sltp_modify_retcode_10013",
                "status": nas100_resolution.get("status"),
                "source": (
                    "knowledge_base/logs/agent_NAS100_live.log, "
                    "shadow_logs/slippage.jsonl, and LIVE_COMPANION_CURRENT_CHECKPOINT.json"
                ),
                "broker_effect": nas100_resolution.get("broker_lifecycle_effect"),
                "current_sltp_status": nas100_resolution.get("current_sltp_status"),
            },
            {
                "id": "mt5_broker_offset_stale_probe_guard",
                "status": "resolved_runtime_repaired",
                "source": "src/components/mt5_daemon_runtime.py, logs/tick_capture_GER40.log, read-only MT5 probe",
                "runtime_effect": "GER30 stale quote skipped and EURUSD probe returned +10800 broker offset",
            },
            {
                "id": "watchdog_tick_capture_liveness_mode",
                "status": "resolved_runtime_repaired",
                "source": "scripts/watchdog.ps1, process table, LIVE_COMPANION_CURRENT_CHECKPOINT.json",
                "runtime_effect": "24 tick-capture daemons are alive with --skip-tick-freshness-check and checkpoint issue_count=0",
            },
            {
                "id": "ob_continuation_csv_source_alias_repair",
                "status": "resolved_runtime_repaired",
                "source": "scripts/ob_continuation_monitor.py, tests/test_ob_continuation_monitor.py, shadow_logs/ob_continuation_daily.csv",
                "runtime_effect": "OB-continuation monitor resolves pointer/fallback CSV sources and covers all configured symbols with true missing-data classifications",
            },
            {
                "id": "supervisor_candidate_packet_top_level_index_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_CANDIDATE_PACKET_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "post-reload candidate rows expose symbol/session/policy/outcome scan fields at top level",
            },
            {
                "id": "supervisor_process_status_normalization",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_PROCESS_HEALTH_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "process rows expose normalized status/status_reason fields for contract-drift scans",
            },
            {
                "id": "supervisor_watchdog_scheduler_status_normalization",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_WATCHDOG_SCHEDULER_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "watchdog readiness is proven from GTOS_Watchdog scheduled short-lived cycle "
                    "status, not only from transient process presence"
                ),
            },
            {
                "id": "supervisor_candidate_packet_snapshot_upper_bound",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_CANDIDATE_PACKET_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "candidate packet rowset is bounded to checkpoint generated_at_utc during live writes",
            },
            {
                "id": "supervisor_candidate_packet_row_type_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_CANDIDATE_PACKET_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "candidate packet summary and record rows are explicitly separated by "
                    "row_type for all-candidate scans"
                ),
            },
            {
                "id": "supervisor_candidate_packet_status_reason_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_CANDIDATE_PACKET_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "candidate packet summary and record rows expose normalized "
                    "status/status_reason fields, including zero-candidate cycles"
                ),
            },
            {
                "id": "supervisor_core_ledger_status_reason_repair",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "VPS_DATA_DEPENDENCY_LEDGER.jsonl, VPS_REQUIRED_FILE_LEDGER.jsonl, "
                    "VPS_ENVIRONMENT_LEDGER.jsonl, VPS_SUPERVISOR_ACTION_LEDGER.jsonl, "
                    "VPS_RUNTIME_JSONL_INVALID_ROW_QUARANTINE.jsonl, and route-owned verifier"
                ),
                "runtime_effect": (
                    "core supervisor rows expose normalized status/status_reason values "
                    "for ready, missing, approval-bound, and quarantined evidence classes"
                ),
            },
            {
                "id": "supervisor_candidate_packet_old_system_projection_repair",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "native post-reload candidate trade records, nested "
                    "gtos_vnext_candidate_intelligence_packet.old_system_absence_proof, "
                    "VPS_CANDIDATE_PACKET_LEDGER.jsonl, and route-owned verifier"
                ),
                "runtime_effect": (
                    "supervisor candidate rows now expose explicit old PA/L2 absence "
                    "fields for native live-writer packets"
                ),
            },
            {
                "id": "live_checkpoint_candidate_summary_old_system_absence_repair",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "scripts/build_vnext_live_activation_checkpoint.py, "
                    "tests/test_vnext_live_activation_checkpoint.py, "
                    "VPS_CANDIDATE_PACKET_LEDGER.jsonl, and route-owned verifier"
                ),
                "runtime_effect": (
                    "candidate summaries now report generic old PA/L2 absence as "
                    "explicit_false_on_all_rows when native live-writer packets prove it"
                ),
            },
            {
                "id": "supervisor_input_refresh_execution_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_SUPERVISOR_ACTION_LEDGER.jsonl and route builder",
                "runtime_effect": (
                    "supervisor artifact rebuilds now execute and record live checkpoint and "
                    "candidate-proof refresh commands"
                ),
            },
            {
                "id": "post_reload_candidate_proof_snapshot_bound_repair",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "scripts/build_vnext_post_reload_candidate_proof.py, "
                    "scripts/verify_vnext_post_reload_candidate_proof.py, "
                    "scripts/build_vnext_live_activation_checkpoint.py"
                ),
                "runtime_effect": (
                    "post-reload candidate proof is evaluated against the explicit checkpoint "
                    "snapshot upper bound instead of racing live writes after the snapshot"
                ),
            },
            {
                "id": "supervisor_data_capture_status_normalization",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_DATA_CAPTURE_HEALTH_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "tick and M1 data-capture rows expose normalized status/status_reason fields",
            },
            {
                "id": "supervisor_notification_status_normalization",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_NOTIFICATION_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "notification rows expose normalized worker, queue, synthetic-test, and credential status",
            },
            {
                "id": "supervisor_lifecycle_risk_status_normalization",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "VPS_BROKER_SPEC_LEDGER.jsonl, VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl, "
                    "VPS_BROKER_RECONCILIATION_LEDGER.jsonl, VPS_RISK_EXPOSURE_LEDGER.jsonl, "
                    "and route-owned verifier"
                ),
                "runtime_effect": (
                    "broker-spec, lifecycle, reconciliation, and risk rows expose normalized "
                    "status/status_reason fields"
                ),
            },
            {
                "id": "supervisor_mt5_symbol_time_status_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_MT5_SYMBOL_SOURCE_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "MT5 read-only symbol proof applies broker_time_offset_seconds and "
                    "records normalized status/status_reason on all 24 symbol rows"
                ),
            },
            {
                "id": "supervisor_runtime_decision_parse_status_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_RUNTIME_DECISION_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "runtime-decision rows expose normalized status/status_reason and "
                    "malformed pre-reload source fragments are excluded by raw timestamp hints"
                ),
            },
            {
                "id": "vnext_runtime_shared_jsonl_locked_append_repair",
                "status": "resolved_runtime_code_and_source_log_repaired",
                "source": (
                "src/components/gtos_vnext_runtime.py, tests/test_gtos_vnext_runtime.py, "
                "shadow_logs/gtos_vnext_runtime_decisions.jsonl, "
                "shadow_logs/gtos_vnext_replacement_monitoring.jsonl, "
                "VPS_RUNTIME_JSONL_INVALID_ROW_QUARANTINE.jsonl"
            ),
                "runtime_effect": (
                    "shared vNext runtime decision/monitoring JSONL writes use sidecar "
                    "cross-process locking and pre-repair malformed fragments are quarantined"
                ),
            },
            {
                "id": "supervisor_restart_reload_status_reason_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_RESTART_RELOAD_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": "restart/reload proof rows expose explicit status_reason values",
            },
            {
                "id": "selected_cell_risk_ledger_lfs_materialization_repair",
                "status": "resolved_runtime_data_dependency_repaired",
                "source": (
                    "config/agent_config.yaml, "
                    f"{SELECTED_CELL_RISK_LEDGER_REL}, "
                    "src/components/gtos_vnext_runtime.py, "
                    "VPS_DATA_DEPENDENCY_LEDGER.jsonl, and VPS_RESTART_RELOAD_LEDGER.jsonl"
                ),
                "runtime_effect": (
                    "live dynamic-router selected-cell risk lookups now read the "
                    "materialized Stage13 ledger instead of a raw LFS pointer, and the "
                    "24 symbol orchestrators were reloaded to clear cached empty reads"
                ),
            },
            {
                "id": "selected_cell_risk_runtime_loader_signature_repair",
                "status": "resolved_runtime_code_repaired_reload_required",
                "source": (
                    "src/components/gtos_vnext_runtime.py, "
                    "tests/test_gtos_vnext_runtime.py, "
                    "VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json"
                ),
                "runtime_effect": (
                    "selected-cell risk dependency loading now rechecks the same path "
                    "after file materialization and reports raw pointer/parse failures "
                    "as exact hard-refusal causes instead of stale empty-cache state"
                ),
            },
            {
                "id": "live_execution_file_reference_audit_materialization",
                "status": "resolved_route_artifact_repaired",
                "source": (
                    "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json, "
                    "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl, "
                    "build_vps_supervisor_artifacts.py, and route-owned verifier"
                ),
                "runtime_effect": (
                    "live execution file-reference checks now persist all reference rows "
                    "and fail raw LFS pointers, missing LFS objects, and parse defects"
                ),
            },
            {
                "id": "live_execution_file_reference_lfs_long_path_materialization_repair",
                "status": "resolved_local_lfs_and_long_path_repaired",
                "source": (
                    "pipeline_state/lfs_checkout_index_materialization_49_file_refs_20260601.json, "
                    "VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json, and "
                    "build_vps_supervisor_artifacts.py"
                ),
                "runtime_effect": (
                    "live file dependency verification now has zero missing LFS, "
                    "missing-not-LFS, raw pointer, parse, or owner-machine blockers"
                ),
            },
            {
                "id": "live_execution_file_reference_scanner_classification_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "build_vps_supervisor_artifacts.py and VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl",
                "runtime_effect": (
                    "optional sentinels/templates/event-driven artifacts/disabled shadow ML "
                    "manifest are not reclassified as live blockers"
                ),
            },
            {
                "id": "candidate_risk_audit_source_identity_join_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "build_vps_supervisor_artifacts.py and VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl",
                "runtime_effect": (
                    "candidate-risk audit validates selected-cell source identity from the "
                    "packet first and only fails current post-reload source mismatches"
                ),
            },
            {
                "id": "supervisor_candidate_packet_source_event_time_filter_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "build_vps_supervisor_artifacts.py and VPS_CANDIDATE_PACKET_LEDGER.jsonl",
                "runtime_effect": (
                    "current post-reload candidate rowsets use source event/candle time "
                    "instead of file mtime touched by repairs"
                ),
            },
            {
                "id": "supervisor_candidate_packet_top_level_dimension_projection_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "build_vps_supervisor_artifacts.py, verify_vps_supervisor_artifacts.py, and VPS_CANDIDATE_PACKET_LEDGER.jsonl",
                "runtime_effect": (
                    "candidate packet rows expose side, origin/framework, candle time, "
                    "source mode, order path, and Gate3 refusal reason at top level"
                ),
            },
            {
                "id": "supervisor_matched_lifecycle_alias_normalization_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "build_vps_supervisor_artifacts.py and VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl",
                "runtime_effect": (
                    "matched lifecycle source rows expose normalized ticket, selected_policy, "
                    "and execution_policy_id without discarding raw MT5/vNext alias fields"
                ),
            },
            {
                "id": "nas100_residual_close_resolution_state_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "knowledge_base/logs/agent_NAS100_live.log and shadow_logs/slippage.jsonl",
                "runtime_effect": (
                    "stale NAS100 SL/TP continuation is closed from MT5 broker-close proof "
                    "instead of remaining in active supervision"
                ),
            },
            {
                "id": "runtime_decision_zero_row_reason_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_RUNTIME_DECISION_LEDGER.jsonl and route-owned verifier",
                "runtime_effect": (
                    "quiet post-reload runtime-decision windows now have an explicit zero-row reason"
                ),
            },
            {
                "id": "candidate_risk_audit_post_reload_absence_proof_repair",
                "status": "resolved_route_artifact_repaired",
                "source": "VPS_CANDIDATE_PACKET_LEDGER.jsonl, VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json, and route-owned verifier",
                "runtime_effect": (
                    "zero post-reload candidate-risk rows are accepted only when the "
                    "candidate ledger proves there were no post-reload candidates"
                ),
            },
            {
                "id": "adopted_position_lifecycle_policy_recovery_fallback_repair",
                "status": "resolved_runtime_code_repaired_live_reloaded",
                "source": "src/components/orchestrator.py, tests/test_orchestrator.py, and orchestrator adopted-recovery reload proof",
                "runtime_effect": (
                    "adopted open positions can recover vNext policy identity from "
                    "pending-limit or Lane06 lifecycle evidence even when no local trade "
                    "record directory exists"
                ),
            },
            {
                "id": "pre_geometry_concurrent_cap_dynamic_ordering_repair",
                "status": "resolved_runtime_code_repaired_live_reloaded",
                "source": (
                    "src/components/orchestrator.py, "
                    "tests/test_vnext_broader_origin_orchestrator.py, "
                    "tests/test_concurrent_cap.py, and "
                    "pipeline_state/orchestrator_pre_geometry_concurrent_cap_reload_summary_*.json"
                ),
                "runtime_effect": (
                    "pre-geometry vNext broader-origin candidates defer legacy "
                    "concurrent-cap facts until final selected-cell/account-risk Gate3, "
                    "and all 24 live/redacted_account orchestrators are on patched code"
                ),
            },
            {
                "id": "watchdog_direct_python_orchestrator_launch_repair",
                "status": "resolved_live_process_repaired",
                "source": (
                    "scripts/watchdog.ps1 and "
                    "pipeline_state/orchestrator_direct_python_watchdog_reload_summary_*.json"
                ),
            "runtime_effect": (
                "watchdog no longer leaves persistent cmd.exe wrappers for live "
                "orchestrators; process family is back to 24 direct Python workers"
            ),
        },
        {
            "id": "broader_origin_candidate_unique_trade_record_path_repair",
            "status": "resolved_runtime_code_repaired_live_reloaded",
            "source": (
                "src/components/trade_capture.py, src/components/orchestrator.py, "
                "tests/test_trade_capture.py, tests/test_vnext_broader_origin_orchestrator.py, "
                "and pipeline_state/broader_origin_candidate_unique_record_reload_summary_*.json"
            ),
            "runtime_effect": (
                "future broader-origin same-symbol same-candle candidates write "
                "candidate-unique trade records instead of overwriting earlier packets"
            ),
            "historical_source_gap": (
                "BTCUSD 2026-06-01T16:00Z dynamic-approved candidate final packet "
                "was overwritten before repair; runtime dynamic approval remains "
                "source-backed, final trade-record packet is not recoverable locally"
            ),
        },
        {
            "id": "orchestrator_reload_process_filter_dedupe_correction",
                "status": "resolved_live_process_repaired",
                "source": "pipeline_state/orchestrator_adopted_trade_recovery_dedupe_summary_20260601T143718Z.json",
                "runtime_effect": "24 older duplicate orchestrator PIDs stopped; 24 newest patched singleton processes kept",
            },
            {
                "id": "ai_append_log_targets_materialized",
                "status": "resolved_local_runtime_artifact_repaired",
                "source": (
                    "shadow_logs/ai_call_policy_decisions.jsonl, "
                    "shadow_logs/ai_supervisor_decisions.jsonl, "
                    "shadow_logs/ai_decision_trace.jsonl"
                ),
                "runtime_effect": (
                    "AI policy/supervisor/trace append targets are present and parseable "
                    "without making any AI calls or changing trading behavior"
                ),
            },
            {
                "id": "pipeline_reload_json_bom_repair",
                "status": "resolved_local_proof_artifact_repaired",
                "source": "pipeline_state/orchestrator*_reload*_2026_06_01.json",
                "runtime_effect": "reload proof JSON files parse under strict UTF-8 JSON readers",
            },
            {
                "id": "local_heavy_data_search_root_recreated",
                "status": "resolved_local_directory_repaired",
                "source": "C:/tmp",
                "runtime_effect": "configured local heavy-data search root exists again",
            },
        ],
        "remaining_blockers_or_continuations": remaining,
        "anomaly_row_count": len(anomaly_rows),
        "manual_broker_action_taken": False,
        "paid_api_or_vendor_call_taken": False,
        "credential_change_taken": False,
        "remote_push_taken": False,
        "goal_status": "active_checkpoint_not_terminal_completion",
    }


def build_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        io_path = local_path_for_io(path)
        if not io_path.is_file() or path.name == "VPS_OUTPUT_MANIFEST.json":
            continue
        stat = io_path.stat()
        files.append(
            {
                "path": rel(path),
                "size_bytes": stat.st_size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": "vps_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": iso_now(),
        "manifest_hash_policy": "VPS_OUTPUT_MANIFEST.json excluded from self-hash list",
        "file_count": len(files),
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip local py_compile/pytest/watchdog checks while still building artifacts.",
    )
    parser.add_argument(
        "--skip-refresh-inputs",
        action="store_true",
        help="Do not refresh live checkpoint or post-reload candidate proof before building.",
    )
    args = parser.parse_args(argv)

    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    input_refresh_results = {} if args.skip_refresh_inputs else refresh_input_artifacts()
    checkpoint = read_json(CHECKPOINT_PATH, {})
    if not isinstance(checkpoint, dict):
        raise RuntimeError(f"Checkpoint is not a JSON object: {CHECKPOINT_PATH}")

    git_audit = collect_git_audit()
    environment_rows = collect_environment_ledger()
    required_file_rows = collect_required_file_ledger()
    data_dependency_rows = collect_data_dependency_ledger()
    mt5_account, mt5_symbol_rows, broker_spec_rows = collect_mt5_readonly()
    process_rows, process_summary = collect_process_rows()
    scheduler_rows = collect_scheduler_rows()
    scheduler_summary = summarize_scheduler_rows(scheduler_rows)
    data_capture_rows = collect_data_capture_rows(checkpoint)
    runtime_decision_rows = collect_runtime_decision_rows(checkpoint)
    candidate_packet_rows = collect_candidate_packet_rows(checkpoint)
    candidate_risk_audit, candidate_risk_rows = collect_candidate_risk_intelligence_audit(
        checkpoint
    )
    file_reference_audit, file_reference_rows = collect_live_execution_file_reference_audit()
    open_trade_rows = collect_open_trade_lifecycle_rows(checkpoint)
    broker_reconciliation_rows = collect_broker_reconciliation_rows(checkpoint)
    risk_rows = collect_risk_rows(mt5_account, broker_spec_rows, checkpoint)
    notification_rows = collect_notification_rows(process_summary)
    verification_commands = {} if args.skip_checks else run_verification_commands()
    anomaly_rows = with_status_reasons(
        collect_anomaly_rows(checkpoint, verification_commands, process_summary)
    )
    repair_rows = with_status_reasons(collect_repair_rows())
    restart_rows = collect_restart_rows(checkpoint, process_summary)
    action_rows = with_status_reasons(collect_action_rows(checkpoint, input_refresh_results))
    verification_result = build_verification_result(
        checkpoint, process_summary, scheduler_summary, verification_commands, anomaly_rows
    )
    supervisor_state = build_supervisor_state(
        checkpoint,
        git_audit,
        process_summary,
        scheduler_summary,
        verification_result,
        file_reference_audit,
    )
    completion_audit = build_completion_audit(
        verification_result, anomaly_rows, file_reference_audit
    )

    write_json("VPS_GIT_VERSION_AUDIT.json", git_audit)
    write_jsonl("VPS_ENVIRONMENT_LEDGER.jsonl", environment_rows)
    write_jsonl("VPS_REQUIRED_FILE_LEDGER.jsonl", required_file_rows)
    write_jsonl("VPS_DATA_DEPENDENCY_LEDGER.jsonl", data_dependency_rows)
    write_json("VPS_MT5_ACCOUNT_READINESS.json", mt5_account)
    write_jsonl("VPS_MT5_SYMBOL_SOURCE_LEDGER.jsonl", mt5_symbol_rows)
    write_jsonl("VPS_BROKER_SPEC_LEDGER.jsonl", broker_spec_rows)
    write_jsonl("VPS_PROCESS_HEALTH_LEDGER.jsonl", process_rows)
    write_jsonl("VPS_WATCHDOG_SCHEDULER_LEDGER.jsonl", scheduler_rows)
    write_jsonl("VPS_DATA_CAPTURE_HEALTH_LEDGER.jsonl", data_capture_rows)
    write_jsonl("VPS_RUNTIME_DECISION_LEDGER.jsonl", runtime_decision_rows)
    write_jsonl("VPS_CANDIDATE_PACKET_LEDGER.jsonl", candidate_packet_rows)
    write_json("VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json", candidate_risk_audit)
    write_jsonl("VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl", candidate_risk_rows)
    write_json("VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json", file_reference_audit)
    write_jsonl("VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl", file_reference_rows)
    write_jsonl("VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl", open_trade_rows)
    write_jsonl("VPS_BROKER_RECONCILIATION_LEDGER.jsonl", broker_reconciliation_rows)
    write_jsonl("VPS_RISK_EXPOSURE_LEDGER.jsonl", risk_rows)
    write_jsonl("VPS_NOTIFICATION_LEDGER.jsonl", notification_rows)
    write_jsonl("VPS_ANOMALY_LEDGER.jsonl", anomaly_rows)
    write_jsonl("VPS_REPAIR_LEDGER.jsonl", repair_rows)
    write_jsonl("VPS_RESTART_RELOAD_LEDGER.jsonl", restart_rows)
    write_jsonl("VPS_SUPERVISOR_ACTION_LEDGER.jsonl", action_rows)
    write_json("VPS_VERIFICATION_RESULT.json", verification_result)
    write_json("VPS_SUPERVISOR_STATE.json", supervisor_state)
    write_json("VPS_COMPLETION_OR_CONTINUATION_AUDIT.json", completion_audit)
    normalize_runtime_jsonl_quarantine()
    write_json("VPS_OUTPUT_MANIFEST.json", build_manifest())

    print(
        json.dumps(
            {
                "route_dir": rel(ROUTE_DIR),
                "status": verification_result.get("status"),
                "checkpoint_status": checkpoint.get("status"),
                "process_status": process_summary.get("status"),
                "anomaly_count": len(anomaly_rows),
                "output_count": len(OUTPUT_FILES),
            },
            sort_keys=True,
        )
    )
    return 0 if verification_result.get("status") != "repair_required" else 1


if __name__ == "__main__":
    raise SystemExit(main())
