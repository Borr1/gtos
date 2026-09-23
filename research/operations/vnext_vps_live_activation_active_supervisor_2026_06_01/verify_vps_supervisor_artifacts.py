#!/usr/bin/env python3
"""Verify the June 1 VPS live supervisor route artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_vps_supervisor_artifacts import (  # noqa: E402
    BROKER_ALIASES,
    EVIDENCE_CLASS,
    LIVE_SYMBOLS,
    OUTPUT_FILES,
    PROJECT_ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    SELECTED_CELL_RISK_LEDGER_REL,
    rel,
)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_jsonl_file(path: Path, max_error_samples: int = 5) -> tuple[int, list[str]]:
    row_count = 0
    errors: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                if len(errors) < max_error_samples:
                    errors.append(f"line_{line_no}:{exc.msg}")
                continue
            if not isinstance(payload, dict):
                if len(errors) < max_error_samples:
                    errors.append(f"line_{line_no}:not_object")
                continue
            row_count += 1
    return row_count, errors


def normalized_rel_path(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def build_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file() or path.name == "VPS_OUTPUT_MANIFEST.json":
            continue
        files.append(
            {
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "mtime_utc": datetime.fromtimestamp(
                    path.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
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


def verify_route(write_result: bool = False) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    parsed: dict[str, Any] = {}

    for name in OUTPUT_FILES:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append({"code": "missing_required_output", "path": rel(path)})
            continue
        try:
            if name.endswith(".jsonl"):
                parsed[name] = read_jsonl(path)
            else:
                parsed[name] = read_json(path)
        except Exception as exc:
            issues.append(
                {
                    "code": "parse_failed",
                    "path": rel(path),
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )

    selected_cell_path = PROJECT_ROOT / SELECTED_CELL_RISK_LEDGER_REL
    if not selected_cell_path.is_file():
        issues.append(
            {
                "code": "selected_cell_risk_ledger_missing",
                "path": SELECTED_CELL_RISK_LEDGER_REL,
            }
        )
    else:
        first = selected_cell_path.open("rb").read(128)
        if first.startswith(b"version https://git-lfs.github.com/spec/v1"):
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_raw_lfs_pointer",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                    "size_bytes": selected_cell_path.stat().st_size,
                }
            )
        selected_cell_rows, selected_cell_parse_errors = validate_jsonl_file(
            selected_cell_path
        )
        if selected_cell_rows <= 0:
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_zero_rows",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                }
            )
        if selected_cell_parse_errors:
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_parse_errors",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                    "row_count": selected_cell_rows,
                    "sample": selected_cell_parse_errors,
                }
            )

    data_dependency_rows = parsed.get("VPS_DATA_DEPENDENCY_LEDGER.jsonl") or []
    selected_cell_dependency_rows = [
        row
        for row in data_dependency_rows
        if normalized_rel_path(row.get("path")) == SELECTED_CELL_RISK_LEDGER_REL
    ]
    if not selected_cell_dependency_rows:
        issues.append(
            {
                "code": "selected_cell_risk_ledger_dependency_row_missing",
                "path": SELECTED_CELL_RISK_LEDGER_REL,
            }
        )
    else:
        selected_cell_dependency = selected_cell_dependency_rows[-1]
        if selected_cell_dependency.get("lfs_pointer_status") == "raw_lfs_pointer":
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_dependency_raw_lfs_pointer",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                }
            )
        if selected_cell_dependency.get("status") != "data_dependency_ready":
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_dependency_not_ready",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                    "status": selected_cell_dependency.get("status"),
                    "status_reason": selected_cell_dependency.get("status_reason"),
                }
            )
        if int(selected_cell_dependency.get("row_count") or 0) <= 0:
            issues.append(
                {
                    "code": "selected_cell_risk_ledger_dependency_zero_rows",
                    "path": SELECTED_CELL_RISK_LEDGER_REL,
                    "row_count": selected_cell_dependency.get("row_count"),
                }
            )

    for name in [item for item in OUTPUT_FILES if item.endswith(".jsonl")]:
        rows = parsed.get(name) or []
        missing_status = [
            {
                "line_no": row.get("_line_no"),
                "status": row.get("status"),
                "status_reason": row.get("status_reason"),
                "row_type": row.get("row_type"),
                "kind": row.get("kind"),
                "path": row.get("path"),
                "symbol": row.get("symbol"),
                "repair_id": row.get("repair_id"),
                "action_id": row.get("action_id"),
            }
            for row in rows
            if not row.get("status") or not row.get("status_reason")
        ]
        if missing_status:
            issues.append(
                {
                    "code": "ledger_status_or_reason_missing",
                    "ledger": name,
                    "count": len(missing_status),
                    "sample": missing_status[:5],
                }
            )

    state = parsed.get("VPS_SUPERVISOR_STATE.json") or {}
    if state.get("route_id") != ROUTE_ID:
        issues.append({"code": "state_route_id_mismatch", "value": state.get("route_id")})
    if state.get("evidence_class") != EVIDENCE_CLASS:
        issues.append(
            {"code": "state_evidence_class_mismatch", "value": state.get("evidence_class")}
        )
    if state.get("terminal_completion") is not False:
        issues.append({"code": "state_terminal_completion_should_be_false"})
    symbols = ((state.get("current_contract") or {}).get("symbols")) or []
    if symbols != LIVE_SYMBOLS:
        issues.append({"code": "state_symbol_contract_mismatch", "count": len(symbols)})

    action_rows = parsed.get("VPS_SUPERVISOR_ACTION_LEDGER.jsonl") or []
    action_by_id = {row.get("action_id"): row for row in action_rows}
    checkpoint_action = action_by_id.get("checkpoint_refresh_after_post_reload_candidate")
    if not checkpoint_action:
        issues.append({"code": "checkpoint_refresh_action_missing"})
    else:
        checkpoint_result = checkpoint_action.get("command_result") or {}
        if checkpoint_result.get("exit_code") != 0:
            issues.append(
                {
                    "code": "checkpoint_refresh_action_failed_or_unrecorded",
                    "exit_code": checkpoint_result.get("exit_code"),
                    "timed_out": checkpoint_result.get("timed_out"),
                }
            )
    candidate_proof_action = action_by_id.get("candidate_proof_refresh_after_checkpoint")
    if not candidate_proof_action:
        issues.append({"code": "candidate_proof_refresh_action_missing"})
    else:
        build_result = candidate_proof_action.get("build_command_result") or {}
        verify_result = candidate_proof_action.get("verify_command_result") or {}
        if build_result.get("exit_code") != 0 or verify_result.get("exit_code") != 0:
            issues.append(
                {
                    "code": "candidate_proof_refresh_action_failed_or_unrecorded",
                    "build_exit_code": build_result.get("exit_code"),
                    "verify_exit_code": verify_result.get("exit_code"),
                    "build_timed_out": build_result.get("timed_out"),
                    "verify_timed_out": verify_result.get("timed_out"),
                }
            )

    verification = parsed.get("VPS_VERIFICATION_RESULT.json") or {}
    if verification.get("checkpoint_status") != "ok":
        issues.append(
            {"code": "checkpoint_not_ok", "value": verification.get("checkpoint_status")}
        )
    if verification.get("checkpoint_issue_count") != 0:
        issues.append(
            {
                "code": "checkpoint_issue_count_nonzero",
                "value": verification.get("checkpoint_issue_count"),
            }
        )
    process_summary = verification.get("process_summary") or {}
    if process_summary.get("python_live_orchestrator_count") != 24:
        issues.append(
            {
                "code": "python_live_orchestrator_count_not_24",
                "value": process_summary.get("python_live_orchestrator_count"),
            }
        )
    if process_summary.get("demo_orchestrator_process_count") != 0:
        issues.append(
            {
                "code": "demo_orchestrator_processes_present",
                "value": process_summary.get("demo_orchestrator_process_count"),
            }
        )
    family_counts = process_summary.get("process_family_counts") or {}
    if family_counts.get("orchestrator") != 24:
        issues.append(
            {
                "code": "orchestrator_process_family_count_not_24",
                "value": family_counts.get("orchestrator"),
            }
        )
    process_rows = parsed.get("VPS_PROCESS_HEALTH_LEDGER.jsonl") or []
    if any(
        row.get("process_family") == "orchestrator"
        and str(row.get("process_name") or "").lower() == "powershell.exe"
        for row in process_rows
    ):
        issues.append({"code": "powershell_self_probe_counted_as_orchestrator"})
    missing_process_status = [
        {
            "process_family": row.get("process_family"),
            "process_name": row.get("process_name"),
            "symbol": row.get("symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in process_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if missing_process_status:
        issues.append(
            {
                "code": "process_status_or_reason_missing",
                "count": len(missing_process_status),
                "sample": missing_process_status[:5],
            }
        )
    bad_process_statuses = {
        "m1_capture_profile_mismatch",
        "orchestrator_contract_mismatch",
        "tick_capture_liveness_arg_missing",
        "tick_capture_profile_mismatch",
        "tick_capture_symbol_mismatch",
        "unexpected_demo_orchestrator",
        "unknown_process_family",
    }
    bad_process_rows = [
        {
            "process_family": row.get("process_family"),
            "process_name": row.get("process_name"),
            "symbol": row.get("symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in process_rows
        if row.get("status") in bad_process_statuses
    ]
    if bad_process_rows:
        issues.append(
            {
                "code": "process_bad_status",
                "count": len(bad_process_rows),
                "sample": bad_process_rows[:5],
            }
        )
    scheduler_rows = parsed.get("VPS_WATCHDOG_SCHEDULER_LEDGER.jsonl") or []
    missing_scheduler_status = [
        {
            "task_name": row.get("task_name"),
            "watchdog_task": row.get("watchdog_task"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in scheduler_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if missing_scheduler_status:
        issues.append(
            {
                "code": "watchdog_scheduler_status_or_reason_missing",
                "count": len(missing_scheduler_status),
                "sample": missing_scheduler_status[:5],
            }
        )
    watchdog_scheduler_rows = [
        row for row in scheduler_rows if row.get("watchdog_task") is True
    ]
    ready_scheduler_rows = [
        row
        for row in watchdog_scheduler_rows
        if row.get("status") in {"watchdog_scheduler_ready", "watchdog_scheduler_running"}
    ]
    if not ready_scheduler_rows:
        issues.append(
            {
                "code": "watchdog_scheduler_not_ready",
                "watchdog_task_count": len(watchdog_scheduler_rows),
                "statuses": [row.get("status") for row in watchdog_scheduler_rows],
            }
        )
    bad_scheduler_rows = [
        {
            "task_name": row.get("task_name"),
            "state": row.get("state"),
            "last_task_result": row.get("last_task_result"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in watchdog_scheduler_rows
        if row.get("status")
        in {
            "watchdog_scheduler_action_missing",
            "watchdog_scheduler_last_run_nonzero",
            "watchdog_scheduler_repair_required",
            "watchdog_scheduler_unproven",
        }
    ]
    if bad_scheduler_rows:
        issues.append(
            {
                "code": "watchdog_scheduler_bad_status",
                "count": len(bad_scheduler_rows),
                "sample": bad_scheduler_rows[:5],
            }
        )
    bad_tick_log_paths = [
        row
        for row in process_rows
        if row.get("process_family") == "tick_capture"
        and row.get("symbol")
        and row.get("latest_log_path") != f"logs/tick_capture_{row.get('symbol')}.log"
    ]
    if bad_tick_log_paths:
        issues.append(
            {
                "code": "tick_capture_log_path_mismatch",
                "count": len(bad_tick_log_paths),
            }
        )
    tick_without_skip = [
        row
        for row in process_rows
        if row.get("process_family") == "tick_capture"
        and "--skip-tick-freshness-check" not in str(row.get("command_line") or "")
    ]
    if tick_without_skip:
        issues.append(
            {
                "code": "tick_capture_liveness_mode_arg_missing",
                "count": len(tick_without_skip),
            }
        )

    symbol_rows = parsed.get("VPS_MT5_SYMBOL_SOURCE_LEDGER.jsonl") or []
    symbol_map = {row.get("symbol"): row for row in symbol_rows}
    if sorted(symbol_map) != sorted(LIVE_SYMBOLS):
        issues.append(
            {
                "code": "mt5_symbol_source_count_or_symbols_mismatch",
                "symbols": sorted(symbol_map),
            }
        )
    for symbol, broker_symbol in BROKER_ALIASES.items():
        row = symbol_map.get(symbol) or {}
        if row.get("broker_symbol") != broker_symbol:
            issues.append(
                {
                    "code": "broker_alias_mismatch",
                    "symbol": symbol,
                    "expected": broker_symbol,
                    "actual": row.get("broker_symbol"),
                }
            )
        if row and row.get("source_status") != "ready":
            issues.append(
                {"code": "mt5_symbol_not_ready", "symbol": symbol, "row": row}
            )
        if row and (not row.get("status") or not row.get("status_reason")):
            issues.append(
                {
                    "code": "mt5_symbol_status_or_reason_missing",
                    "symbol": symbol,
                    "status": row.get("status"),
                    "status_reason": row.get("status_reason"),
                }
            )
        if row and row.get("status") == "mt5_symbol_source_repair_required":
            issues.append(
                {
                    "code": "mt5_symbol_source_bad_status",
                    "symbol": symbol,
                    "status_reason": row.get("status_reason"),
                }
            )
        if row and not isinstance(row.get("broker_time_offset_seconds"), int):
            issues.append(
                {
                    "code": "mt5_symbol_broker_time_offset_missing",
                    "symbol": symbol,
                    "value": row.get("broker_time_offset_seconds"),
                }
            )
        bars = row.get("bar_timeframes") or {}
        for timeframe in ["M1", "M15", "H1", "H4", "D1"]:
            if (bars.get(timeframe) or {}).get("rows", 0) <= 0:
                issues.append(
                    {
                        "code": "mt5_bar_rows_missing",
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )
            age = (bars.get(timeframe) or {}).get("latest_bar_age_s")
            if isinstance(age, (int, float)) and age < -60:
                issues.append(
                    {
                        "code": "mt5_bar_age_negative_after_broker_offset",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "latest_bar_age_s": age,
                    }
                )

    broker_spec_rows = parsed.get("VPS_BROKER_SPEC_LEDGER.jsonl") or []
    broker_spec_map = {row.get("symbol"): row for row in broker_spec_rows}
    if sorted(broker_spec_map) != sorted(LIVE_SYMBOLS):
        issues.append(
            {
                "code": "broker_spec_count_or_symbols_mismatch",
                "symbols": sorted(broker_spec_map),
            }
        )
    broker_spec_missing_status = [
        {
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in broker_spec_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if broker_spec_missing_status:
        issues.append(
            {
                "code": "broker_spec_status_or_reason_missing",
                "count": len(broker_spec_missing_status),
                "sample": broker_spec_missing_status[:5],
            }
        )
    bad_broker_spec_rows = [
        {
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in broker_spec_rows
        if row.get("status") == "broker_spec_repair_required"
    ]
    if bad_broker_spec_rows:
        issues.append(
            {
                "code": "broker_spec_bad_status",
                "count": len(bad_broker_spec_rows),
                "sample": bad_broker_spec_rows[:5],
            }
        )

    data_capture_rows = parsed.get("VPS_DATA_CAPTURE_HEALTH_LEDGER.jsonl") or []
    capture_counts = {}
    for row in data_capture_rows:
        capture_counts[row.get("capture_type")] = capture_counts.get(row.get("capture_type"), 0) + 1
    if capture_counts.get("m1_closed_bar") != 24:
        issues.append(
            {"code": "m1_capture_rows_not_24", "value": capture_counts.get("m1_closed_bar")}
        )
    if capture_counts.get("tick") != 24:
        issues.append({"code": "tick_capture_rows_not_24", "value": capture_counts.get("tick")})
    capture_missing_status = [
        {
            "capture_type": row.get("capture_type"),
            "symbol": row.get("symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in data_capture_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if capture_missing_status:
        issues.append(
            {
                "code": "data_capture_status_or_reason_missing",
                "count": len(capture_missing_status),
                "sample": capture_missing_status[:5],
            }
        )
    bad_capture_statuses = {
        "dead_or_missing_daemon",
        "m1_capture_error",
        "no_rows_without_reason",
        "stale",
        "stale_without_classification",
    }
    bad_capture_rows = [
        {
            "capture_type": row.get("capture_type"),
            "symbol": row.get("symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in data_capture_rows
        if row.get("status") in bad_capture_statuses
    ]
    if bad_capture_rows:
        issues.append(
            {
                "code": "data_capture_bad_status",
                "count": len(bad_capture_rows),
                "sample": bad_capture_rows[:5],
            }
        )

    runtime_rows = parsed.get("VPS_RUNTIME_DECISION_LEDGER.jsonl") or []
    if not runtime_rows:
        issues.append({"code": "runtime_decision_ledger_empty"})
    runtime_missing_status = [
        {
            "source_path": row.get("_source_path"),
            "line_no": row.get("_line_no"),
            "symbol": row.get("symbol"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in runtime_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if runtime_missing_status:
        issues.append(
            {
                "code": "runtime_decision_status_or_reason_missing",
                "count": len(runtime_missing_status),
                "sample": runtime_missing_status[:5],
            }
        )
    runtime_parse_errors = [
        {
            "source_path": row.get("_source_path"),
            "line_no": row.get("_line_no"),
            "parse_error": row.get("_parse_error"),
            "timestamp_hint": row.get("_raw_timestamp_hint_utc"),
        }
        for row in runtime_rows
        if row.get("_parse_error") or row.get("status") == "runtime_decision_parse_error"
    ]
    if runtime_parse_errors:
        issues.append(
            {
                "code": "runtime_decision_parse_error_row_in_post_reload_ledger",
                "count": len(runtime_parse_errors),
                "sample": runtime_parse_errors[:5],
            }
        )
    bad_runtime_statuses = [
        {
            "source_path": row.get("_source_path"),
            "line_no": row.get("_line_no"),
            "row_type": row.get("row_type"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in runtime_rows
        if row.get("status")
        not in {
            "runtime_decision_row_captured",
            "runtime_decision_no_post_reload_rows_yet",
        }
    ]
    if bad_runtime_statuses:
        issues.append(
            {
                "code": "runtime_decision_bad_status",
                "count": len(bad_runtime_statuses),
                "sample": bad_runtime_statuses[:5],
            }
        )

    candidate_rows = parsed.get("VPS_CANDIDATE_PACKET_LEDGER.jsonl") or []
    candidate_summary = next(
        (
            row
            for row in candidate_rows
            if row.get("schema_version") == "vps_candidate_packet_summary_v1"
        ),
        {},
    )
    candidate_records = [
        row
        for row in candidate_rows
        if row.get("schema_version") == "vps_candidate_packet_record_v1"
    ]
    if candidate_summary.get("row_type") != "summary":
        issues.append(
            {
                "code": "candidate_packet_summary_row_type_missing",
                "row_type": candidate_summary.get("row_type"),
            }
        )
    if (
        int(candidate_summary.get("native_live_writer_packet_rows") or 0) > 0
        and candidate_summary.get("native_old_primary_analyzer_l2_absence_proof_status")
        == "explicit_false_on_native_live_writer_rows"
        and candidate_summary.get("old_primary_analyzer_l2_absence_proof_status")
        != "explicit_false_on_all_rows"
    ):
        issues.append(
            {
                "code": "candidate_packet_summary_old_system_absence_contradiction",
                "old_status": candidate_summary.get(
                    "old_primary_analyzer_l2_absence_proof_status"
                ),
                "native_status": candidate_summary.get(
                    "native_old_primary_analyzer_l2_absence_proof_status"
                ),
                "old_primary_analyzer_field_missing_count": candidate_summary.get(
                    "old_primary_analyzer_field_missing_count"
                ),
                "old_l2_required_field_missing_count": candidate_summary.get(
                    "old_l2_required_field_missing_count"
                ),
            }
        )
    candidate_status_missing = [
        {
            "row_type": row.get("row_type"),
            "source_path": row.get("source_path") or row.get("source"),
            "candidate_id": row.get("candidate_id"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in candidate_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if candidate_status_missing:
        issues.append(
            {
                "code": "candidate_packet_status_or_reason_missing",
                "count": len(candidate_status_missing),
                "sample": candidate_status_missing[:5],
            }
        )
    bad_candidate_row_types = [
        {
            "source_path": row.get("source_path"),
            "row_type": row.get("row_type"),
            "candidate_id": row.get("candidate_id"),
        }
        for row in candidate_records
        if row.get("row_type") != "post_reload_candidate_packet"
    ]
    if bad_candidate_row_types:
        issues.append(
            {
                "code": "candidate_packet_record_row_type_missing",
                "count": len(bad_candidate_row_types),
                "sample": bad_candidate_row_types[:5],
            }
        )
    expected_candidate_count = candidate_summary.get("candidate_records_after_reload")
    if expected_candidate_count is not None and len(candidate_records) != expected_candidate_count:
        issues.append(
            {
                "code": "candidate_record_count_mismatch",
                "expected": expected_candidate_count,
                "actual": len(candidate_records),
            }
        )
    required_candidate_index_fields = [
        "candidate_id",
        "symbol",
        "broker_symbol",
        "side",
        "session",
        "origin_family",
        "framework",
        "source_event_time_utc",
        "final_outcome",
        "selected_policy",
        "execution_policy_id",
    ]
    missing_candidate_index_rows = [
        {
            "source_path": row.get("source_path"),
            "missing_fields": [
                field for field in required_candidate_index_fields if not row.get(field)
            ],
        }
        for row in candidate_records
        if any(not row.get(field) for field in required_candidate_index_fields)
    ]
    if missing_candidate_index_rows:
        issues.append(
            {
                "code": "candidate_packet_top_level_index_fields_missing",
                "count": len(missing_candidate_index_rows),
                "sample": missing_candidate_index_rows[:5],
            }
        )
    native_old_system_projection_missing = [
        {
            "source_path": row.get("source_path"),
            "candidate_id": row.get("candidate_id"),
            "packet_capture_mode": row.get("packet_capture_mode"),
            "old_primary_analyzer_called": row.get("old_primary_analyzer_called"),
            "old_l2_required": row.get("old_l2_required"),
            "old_system_absence_status": row.get("old_system_absence_status"),
        }
        for row in candidate_records
        if row.get("packet_capture_mode") == "native_live_writer"
        and (
            row.get("old_primary_analyzer_called") is not False
            or row.get("old_l2_required") is not False
            or row.get("old_system_absence_status") != "explicit_absent"
        )
    ]
    if native_old_system_projection_missing:
        issues.append(
            {
                "code": "candidate_packet_native_old_system_absence_projection_missing",
                "count": len(native_old_system_projection_missing),
                "sample": native_old_system_projection_missing[:5],
            }
        )

    candidate_risk_audit = parsed.get("VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT.json") or {}
    candidate_risk_rows = parsed.get("VPS_CANDIDATE_RISK_INTELLIGENCE_AUDIT_LEDGER.jsonl") or []
    if candidate_risk_audit.get("schema_version") != "vps_candidate_risk_intelligence_audit_v1":
        issues.append(
            {
                "code": "candidate_risk_audit_schema_mismatch",
                "value": candidate_risk_audit.get("schema_version"),
            }
        )
    if int(candidate_risk_audit.get("candidate_record_count") or 0) != len(
        candidate_risk_rows
    ):
        issues.append(
            {
                "code": "candidate_risk_audit_count_mismatch",
                "summary_count": candidate_risk_audit.get("candidate_record_count"),
                "ledger_count": len(candidate_risk_rows),
            }
        )
    post_reload_candidate_count = int(
        candidate_risk_audit.get("post_reload_candidate_record_count") or 0
    )
    post_reload_candidate_absence_ok = (
        post_reload_candidate_count == 0
        and int(candidate_summary.get("candidate_records_after_reload") or 0) == 0
        and candidate_summary.get("candidate_absence_proof_status")
        == "no_post_reload_vnext_candidate_records_since_current_process_reload"
    )
    if post_reload_candidate_count <= 0 and not post_reload_candidate_absence_ok:
        issues.append({"code": "candidate_risk_audit_post_reload_empty"})
    if int(candidate_risk_audit.get("risk_ledger_row_count") or 0) <= 0:
        issues.append({"code": "candidate_risk_audit_selected_cell_risk_rows_empty"})
    if int(candidate_risk_audit.get("post_reload_selected_cell_ledger_missing_or_empty_count") or 0) != 0:
        issues.append(
            {
                "code": "candidate_risk_audit_post_reload_selected_cell_dependency_unavailable",
                "value": candidate_risk_audit.get(
                    "post_reload_selected_cell_ledger_missing_or_empty_count"
                ),
            }
        )
    if int(candidate_risk_audit.get("current_risk_refusal_mismatch_count") or 0) != 0:
        issues.append(
            {
                "code": "candidate_risk_audit_current_risk_refusal_mismatch",
                "value": candidate_risk_audit.get("current_risk_refusal_mismatch_count"),
                "sample": [
                    {
                        "path": row.get("path"),
                        "candidate_id": row.get("candidate_id"),
                        "risk_refusal_validation": row.get("risk_refusal_validation"),
                        "value_defects": row.get("value_defects"),
                    }
                    for row in candidate_risk_rows
                    if row.get("after_selected_cell_lfs_reload")
                    and row.get("risk_refusal_mismatch")
                ][:5],
            }
        )
    if int(candidate_risk_audit.get("post_reload_source_identity_current_ledger_drift_count") or 0) != 0:
        issues.append(
            {
                "code": "candidate_risk_audit_post_reload_source_identity_current_ledger_drift",
                "value": candidate_risk_audit.get(
                    "post_reload_source_identity_current_ledger_drift_count"
                ),
                "sample": [
                    {
                        "path": row.get("path"),
                        "candidate_id": row.get("candidate_id"),
                        "selected_cell_risk_cell_id": row.get(
                            "selected_cell_risk_cell_id"
                        ),
                        "drift": row.get("selected_cell_current_ledger_drift_dimensions"),
                    }
                    for row in candidate_risk_rows
                    if row.get("after_selected_cell_lfs_reload")
                    and row.get("selected_cell_current_ledger_drift_dimensions")
                ][:5],
            }
        )
    if int(candidate_risk_audit.get("current_value_defect_count") or 0) != 0:
        issues.append(
            {
                "code": "candidate_risk_audit_current_value_defects",
                "value": candidate_risk_audit.get("current_value_defect_count"),
                "sample": [
                    {
                        "path": row.get("path"),
                        "candidate_id": row.get("candidate_id"),
                        "value_defects": row.get("value_defects"),
                    }
                    for row in candidate_risk_rows
                    if row.get("after_selected_cell_lfs_reload") and row.get("value_defects")
                ][:5],
            }
        )

    file_reference_audit = parsed.get("VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT.json") or {}
    file_reference_rows = parsed.get("VPS_LIVE_EXECUTION_FILE_REFERENCE_AUDIT_LEDGER.jsonl") or []
    if file_reference_audit.get("schema_version") != "vps_live_execution_file_reference_audit_v1":
        issues.append(
            {
                "code": "live_file_reference_audit_schema_mismatch",
                "value": file_reference_audit.get("schema_version"),
            }
        )
    if int(file_reference_audit.get("reference_count") or 0) != len(file_reference_rows):
        issues.append(
            {
                "code": "live_file_reference_audit_count_mismatch",
                "summary_count": file_reference_audit.get("reference_count"),
                "ledger_count": len(file_reference_rows),
            }
        )
    for field, code in [
        ("missing_but_lfs_tracked_count", "live_file_reference_missing_lfs_objects"),
        ("raw_lfs_pointer_defect_count", "live_file_reference_raw_lfs_pointers"),
        ("parse_defect_count", "live_file_reference_parse_defects"),
    ]:
        if int(file_reference_audit.get(field) or 0) != 0:
            issues.append({"code": code, "value": file_reference_audit.get(field)})
    unexpected_missing_not_lfs = [
        row
        for row in file_reference_rows
        if row.get("status") == "missing_not_in_lfs"
        and not str(row.get("reference_path") or "").endswith(
            "VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json"
        )
    ]
    if unexpected_missing_not_lfs:
        issues.append(
            {
                "code": "unexpected_live_file_reference_missing_not_lfs",
                "count": len(unexpected_missing_not_lfs),
                "sample": [
                    {
                        "reference_path": row.get("reference_path"),
                        "source_path": row.get("source_path"),
                        "owning_reference": row.get("owning_reference"),
                    }
                    for row in unexpected_missing_not_lfs[:5]
                ],
            }
        )
    if int(file_reference_audit.get("missing_not_in_lfs_count") or 0) > 0 and not (
        file_reference_audit.get("exact_owner_or_other_machine_blockers") or []
    ):
        issues.append({"code": "live_file_reference_missing_not_lfs_without_blocker"})
    if int(file_reference_audit.get("approval_bound_missing_count") or 0) > 1:
        issues.append(
            {
                "code": "live_file_reference_unexpected_approval_bound_missing_count",
                "value": file_reference_audit.get("approval_bound_missing_count"),
            }
        )
    missing_status_file_refs = [
        {
            "reference_path": row.get("reference_path"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in file_reference_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if missing_status_file_refs:
        issues.append(
            {
                "code": "live_file_reference_status_or_reason_missing",
                "count": len(missing_status_file_refs),
                "sample": missing_status_file_refs[:5],
            }
        )

    lifecycle_rows = parsed.get("VPS_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl") or []
    if not any(str(row.get("ticket")) == "241779188" for row in lifecycle_rows):
        issues.append({"code": "open_nas100_ticket_not_recorded"})
    if not any(
        row.get("selected_policy") == "partial_be_runner" for row in lifecycle_rows
    ):
        issues.append({"code": "partial_be_runner_lifecycle_policy_not_recorded"})
    lifecycle_missing_status = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in lifecycle_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if lifecycle_missing_status:
        issues.append(
            {
                "code": "open_trade_lifecycle_status_or_reason_missing",
                "count": len(lifecycle_missing_status),
                "sample": lifecycle_missing_status[:5],
            }
        )
    bad_lifecycle_statuses = {
        "open_position_unreconciled",
        "matched_lifecycle_source_incomplete",
        "lane06_source_incomplete",
        "open_lifecycle_unknown_row_type",
    }
    bad_lifecycle_rows = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in lifecycle_rows
        if row.get("status") in bad_lifecycle_statuses
    ]
    if bad_lifecycle_rows:
        issues.append(
            {
                "code": "open_trade_lifecycle_bad_status",
                "count": len(bad_lifecycle_rows),
                "sample": bad_lifecycle_rows[:5],
            }
        )

    broker_reconciliation_rows = parsed.get("VPS_BROKER_RECONCILIATION_LEDGER.jsonl") or []
    broker_reconciliation_missing_status = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in broker_reconciliation_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if broker_reconciliation_missing_status:
        issues.append(
            {
                "code": "broker_reconciliation_status_or_reason_missing",
                "count": len(broker_reconciliation_missing_status),
                "sample": broker_reconciliation_missing_status[:5],
            }
        )
    bad_broker_reconciliation_rows = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in broker_reconciliation_rows
        if row.get("status") == "broker_reconciliation_status_missing"
    ]
    if bad_broker_reconciliation_rows:
        issues.append(
            {
                "code": "broker_reconciliation_bad_status",
                "count": len(bad_broker_reconciliation_rows),
                "sample": bad_broker_reconciliation_rows[:5],
            }
        )

    risk_rows = parsed.get("VPS_RISK_EXPOSURE_LEDGER.jsonl") or []
    risk_missing_status = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in risk_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if risk_missing_status:
        issues.append(
            {
                "code": "risk_exposure_status_or_reason_missing",
                "count": len(risk_missing_status),
                "sample": risk_missing_status[:5],
            }
        )
    bad_risk_statuses = {
        "account_risk_authority_incomplete",
        "open_position_risk_estimate_missing",
    }
    bad_risk_rows = [
        {
            "row_type": row.get("row_type"),
            "ticket": row.get("ticket"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in risk_rows
        if row.get("status") in bad_risk_statuses
    ]
    if bad_risk_rows:
        issues.append(
            {
                "code": "risk_exposure_bad_status",
                "count": len(bad_risk_rows),
                "sample": bad_risk_rows[:5],
            }
        )

    notification_rows = parsed.get("VPS_NOTIFICATION_LEDGER.jsonl") or []
    missing_notification_status = [
        {
            "row_type": row.get("row_type"),
            "queue_path": row.get("queue_path"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in notification_rows
        if not row.get("status") or not row.get("status_reason")
    ]
    if missing_notification_status:
        issues.append(
            {
                "code": "notification_status_or_reason_missing",
                "count": len(missing_notification_status),
                "sample": missing_notification_status[:5],
            }
        )
    bad_notification_rows = [
        {
            "row_type": row.get("row_type"),
            "queue_path": row.get("queue_path"),
            "status": row.get("status"),
            "pending_count": row.get("pending_count"),
        }
        for row in notification_rows
        if row.get("status") in {"missing", "pending_live_queue", "missing_credential_key"}
    ]
    if bad_notification_rows:
        issues.append(
            {
                "code": "notification_bad_status",
                "count": len(bad_notification_rows),
                "sample": bad_notification_rows[:5],
            }
        )

    repair_rows = parsed.get("VPS_REPAIR_LEDGER.jsonl") or []
    missing_repair_status_reason = [
        {
            "repair_id": row.get("repair_id"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in repair_rows
        if row.get("status") and not row.get("status_reason")
    ]
    if missing_repair_status_reason:
        issues.append(
            {
                "code": "repair_status_reason_missing",
                "count": len(missing_repair_status_reason),
                "sample": missing_repair_status_reason[:5],
            }
        )
    required_repairs = {
        "launcher_default_live_mode",
        "watchdog_default_live_mode",
        "persisted_environment_demo_to_live",
        "checkpoint_lifecycle_full_scan_and_lane06_fallback",
        "orchestrator_lane06_trade_record_recovery",
        "mt5_sltp_action_constant_repair",
        "adopted_partial_residual_recovery_guard",
        "supervisor_process_probe_self_count_filter",
        "supervisor_process_status_normalization",
        "supervisor_candidate_packet_top_level_index_repair",
        "supervisor_candidate_packet_snapshot_upper_bound",
        "supervisor_candidate_packet_row_type_repair",
        "supervisor_candidate_packet_status_reason_repair",
        "supervisor_core_ledger_status_reason_repair",
        "supervisor_candidate_packet_old_system_projection_repair",
        "supervisor_input_refresh_execution_repair",
        "post_reload_candidate_proof_snapshot_bound_repair",
        "supervisor_data_capture_status_normalization",
        "supervisor_notification_status_normalization",
        "supervisor_lifecycle_risk_status_normalization",
        "supervisor_mt5_symbol_time_status_repair",
        "supervisor_runtime_decision_parse_status_repair",
        "vnext_runtime_shared_jsonl_locked_append_repair",
        "supervisor_restart_reload_status_reason_repair",
        "supervisor_watchdog_scheduler_status_normalization",
        "mt5_broker_offset_stale_probe_guard",
        "watchdog_tick_capture_liveness_mode",
        "ob_continuation_csv_source_alias_repair",
        "selected_cell_risk_ledger_lfs_materialization_repair",
        "selected_cell_risk_runtime_loader_signature_repair",
        "pre_geometry_concurrent_cap_dynamic_ordering_repair",
        "watchdog_direct_python_orchestrator_launch_repair",
        "broader_origin_candidate_unique_trade_record_path_repair",
        "candidate_risk_audit_post_reload_absence_proof_repair",
        "live_execution_file_reference_audit_materialization",
        "ai_append_log_targets_materialized",
        "pipeline_reload_json_bom_repair",
        "local_heavy_data_search_root_recreated",
    }
    repair_ids = {row.get("repair_id") for row in repair_rows}
    missing_repairs = sorted(required_repairs - repair_ids)
    if missing_repairs:
        issues.append({"code": "missing_repair_rows", "repair_ids": missing_repairs})

    anomaly_rows = parsed.get("VPS_ANOMALY_LEDGER.jsonl") or []
    missing_anomaly_status_reason = [
        {
            "row_type": row.get("row_type"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in anomaly_rows
        if row.get("status") and not row.get("status_reason")
    ]
    if missing_anomaly_status_reason:
        issues.append(
            {
                "code": "anomaly_status_reason_missing",
                "count": len(missing_anomaly_status_reason),
                "sample": missing_anomaly_status_reason[:5],
            }
        )

    restart_rows = parsed.get("VPS_RESTART_RELOAD_LEDGER.jsonl") or []
    missing_restart_status_reason = [
        {
            "restart_id": row.get("restart_id"),
            "status": row.get("status"),
            "status_reason": row.get("status_reason"),
        }
        for row in restart_rows
        if row.get("status") and not row.get("status_reason")
    ]
    if missing_restart_status_reason:
        issues.append(
            {
                "code": "restart_reload_status_reason_missing",
                "count": len(missing_restart_status_reason),
                "sample": missing_restart_status_reason[:5],
            }
        )
    restart_broker_mutations = [
        {"restart_id": row.get("restart_id"), "action": row.get("action")}
        for row in restart_rows
        if row.get("manual_broker_action_taken") is not False
    ]
    if restart_broker_mutations:
        issues.append(
            {
                "code": "restart_reload_manual_broker_action_not_false",
                "count": len(restart_broker_mutations),
                "sample": restart_broker_mutations[:5],
            }
        )
    restart_ids = {row.get("restart_id") for row in restart_rows}
    if "selected_cell_risk_ledger_lfs_materialization_reload" not in restart_ids:
        issues.append({"code": "selected_cell_risk_ledger_reload_not_recorded"})
    if "pre_geometry_concurrent_cap_dynamic_ordering_reload" not in restart_ids:
        issues.append({"code": "pre_geometry_concurrent_cap_reload_not_recorded"})
    if "watchdog_direct_python_orchestrator_launch_reload" not in restart_ids:
        issues.append({"code": "watchdog_direct_python_reload_not_recorded"})
    if "broader_origin_candidate_unique_record_path_reload" not in restart_ids:
        issues.append({"code": "broader_origin_candidate_unique_record_reload_not_recorded"})

    nas100_sltp = state.get("nas100_sltp_repair_status") or {}
    if nas100_sltp.get("resolved") is not True:
        issues.append({"code": "nas100_sltp_repair_not_resolved", "value": nas100_sltp})

    completion = parsed.get("VPS_COMPLETION_OR_CONTINUATION_AUDIT.json") or {}
    if completion.get("terminal_completion") is not False:
        issues.append({"code": "completion_audit_terminal_completion_should_be_false"})
    if completion.get("decision") != "CONTINUATION_REQUIRED_ACTIVE_SUPERVISOR_CHECKPOINT":
        issues.append({"code": "completion_decision_mismatch", "value": completion.get("decision")})
    remaining_ids = {
        row.get("id")
        for row in completion.get("remaining_blockers_or_continuations") or []
        if isinstance(row, dict)
    }
    if "nas100_sltp_modify_retcode_10013" in remaining_ids:
        issues.append({"code": "nas100_sltp_repair_still_marked_remaining"})
    resolved_ids = {
        row.get("id")
        for row in completion.get("resolved_items") or []
        if isinstance(row, dict)
    }
    if "nas100_sltp_modify_retcode_10013" not in resolved_ids:
        issues.append({"code": "nas100_sltp_repair_not_recorded_resolved"})
    if "ob_continuation_csv_source_alias_repair" not in resolved_ids:
        issues.append({"code": "ob_continuation_repair_not_recorded_resolved"})
    if "supervisor_process_status_normalization" not in resolved_ids:
        issues.append({"code": "process_status_repair_not_recorded_resolved"})
    if "supervisor_candidate_packet_top_level_index_repair" not in resolved_ids:
        issues.append({"code": "candidate_packet_index_repair_not_recorded_resolved"})
    if "supervisor_candidate_packet_snapshot_upper_bound" not in resolved_ids:
        issues.append({"code": "candidate_packet_snapshot_upper_bound_not_recorded_resolved"})
    if "supervisor_candidate_packet_row_type_repair" not in resolved_ids:
        issues.append({"code": "candidate_packet_row_type_repair_not_recorded_resolved"})
    if "supervisor_candidate_packet_status_reason_repair" not in resolved_ids:
        issues.append({"code": "candidate_packet_status_reason_repair_not_recorded_resolved"})
    if "supervisor_core_ledger_status_reason_repair" not in resolved_ids:
        issues.append({"code": "core_ledger_status_reason_repair_not_recorded_resolved"})
    if "supervisor_candidate_packet_old_system_projection_repair" not in resolved_ids:
        issues.append(
            {"code": "candidate_packet_old_system_projection_repair_not_recorded_resolved"}
        )
    if "supervisor_input_refresh_execution_repair" not in resolved_ids:
        issues.append({"code": "input_refresh_execution_repair_not_recorded_resolved"})
    if "post_reload_candidate_proof_snapshot_bound_repair" not in resolved_ids:
        issues.append({"code": "candidate_proof_snapshot_bound_repair_not_recorded_resolved"})
    if "supervisor_data_capture_status_normalization" not in resolved_ids:
        issues.append({"code": "data_capture_status_repair_not_recorded_resolved"})
    if "supervisor_notification_status_normalization" not in resolved_ids:
        issues.append({"code": "notification_status_repair_not_recorded_resolved"})
    if "supervisor_lifecycle_risk_status_normalization" not in resolved_ids:
        issues.append({"code": "lifecycle_risk_status_repair_not_recorded_resolved"})
    if "supervisor_mt5_symbol_time_status_repair" not in resolved_ids:
        issues.append({"code": "mt5_symbol_time_status_repair_not_recorded_resolved"})
    if "supervisor_runtime_decision_parse_status_repair" not in resolved_ids:
        issues.append({"code": "runtime_decision_parse_status_repair_not_recorded_resolved"})
    if "vnext_runtime_shared_jsonl_locked_append_repair" not in resolved_ids:
        issues.append({"code": "runtime_shared_jsonl_locked_append_repair_not_recorded_resolved"})
    if "supervisor_restart_reload_status_reason_repair" not in resolved_ids:
        issues.append({"code": "restart_reload_status_reason_repair_not_recorded_resolved"})
    if "selected_cell_risk_ledger_lfs_materialization_repair" not in resolved_ids:
        issues.append({"code": "selected_cell_risk_ledger_repair_not_recorded_resolved"})
    if "selected_cell_risk_runtime_loader_signature_repair" not in resolved_ids:
        issues.append({"code": "selected_cell_risk_runtime_loader_repair_not_recorded_resolved"})
    if "pre_geometry_concurrent_cap_dynamic_ordering_repair" not in resolved_ids:
        issues.append({"code": "pre_geometry_concurrent_cap_repair_not_recorded_resolved"})
    if "watchdog_direct_python_orchestrator_launch_repair" not in resolved_ids:
        issues.append({"code": "watchdog_direct_python_repair_not_recorded_resolved"})
    if "broader_origin_candidate_unique_trade_record_path_repair" not in resolved_ids:
        issues.append({"code": "broader_origin_candidate_unique_record_repair_not_recorded_resolved"})
    if "candidate_risk_audit_post_reload_absence_proof_repair" not in resolved_ids:
        issues.append({"code": "candidate_risk_absence_proof_repair_not_recorded_resolved"})
    if "live_execution_file_reference_audit_materialization" not in resolved_ids:
        issues.append({"code": "live_file_reference_audit_not_recorded_resolved"})
    if "ai_append_log_targets_materialized" not in resolved_ids:
        issues.append({"code": "ai_append_log_targets_not_recorded_resolved"})
    if "pipeline_reload_json_bom_repair" not in resolved_ids:
        issues.append({"code": "pipeline_reload_json_bom_repair_not_recorded_resolved"})
    if "local_heavy_data_search_root_recreated" not in resolved_ids:
        issues.append({"code": "local_heavy_data_search_root_repair_not_recorded_resolved"})
    if int(file_reference_audit.get("missing_not_in_lfs_count") or 0) > 0 and (
        "live_file_reference_missing_not_local_or_lfs" not in remaining_ids
    ):
        issues.append({"code": "live_missing_file_reference_blocker_not_recorded_remaining"})

    result = {
        "schema_version": "vps_route_owned_verifier_result_v1",
        "route_id": ROUTE_ID,
        "checked_at_utc": iso_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "checked_files": [name for name in OUTPUT_FILES if (ROUTE_DIR / name).exists()],
    }

    if write_result:
        verification_path = ROUTE_DIR / "VPS_VERIFICATION_RESULT.json"
        verification_payload = (
            read_json(verification_path) if verification_path.exists() else {}
        )
        verification_payload["route_owned_verifier"] = result
        verification_path.write_text(
            json.dumps(verification_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (ROUTE_DIR / "VPS_OUTPUT_MANIFEST.json").write_text(
            json.dumps(build_manifest(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route(write_result=args.write_result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
