#!/usr/bin/env python3
"""Record dual-supervisor process and memory evidence.

This script is read-only with respect to broker/runtime state. It captures the
current Windows process list, memory status, and MT5 terminal path existence,
then appends checkpoint rows to the route ledgers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
EVIDENCE_CLASS = "DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION"

PROCESS_QUERY = r"""
$names=@('python.exe','pythonw.exe','terminal64.exe','MetaEditor64.exe','powershell.exe','pwsh.exe','wscript.exe','cmd.exe')
Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -in $names -or
    $_.CommandLine -like '*ai-trading-agent*' -or
    $_.CommandLine -like '*watchdog.ps1*' -or
    $_.CommandLine -like '*watchdog.bat*' -or
    $_.CommandLine -like '*watchdog_launcher.vbs*' -or
    $_.CommandLine -like '*run_agent.py*' -or
    $_.CommandLine -like '*notification_queue*' -or
    $_.CommandLine -like '*m1_capture*' -or
    $_.CommandLine -like '*tick_capture*'
  } |
  Select-Object ProcessId,Name,ParentProcessId,ExecutablePath,CommandLine,CreationDate,WorkingSetSize,VirtualSize |
  Sort-Object Name,ProcessId |
  ConvertTo-Json -Depth 5
"""

MEMORY_QUERY = r"""
$os=Get-CimInstance Win32_OperatingSystem
$paths=@('C:\Program Files\MetaTrader 5\terminal64.exe','C:\MT5\FTMO\terminal64.exe')
[pscustomobject]@{
  checked_at_utc=(Get-Date).ToUniversalTime().ToString('o')
  total_visible_memory_kb=$os.TotalVisibleMemorySize
  free_physical_memory_kb=$os.FreePhysicalMemory
  total_virtual_memory_kb=$os.TotalVirtualMemorySize
  free_virtual_memory_kb=$os.FreeVirtualMemory
  terminal_paths=$paths | ForEach-Object {
    [pscustomobject]@{path=$_; exists=Test-Path -LiteralPath $_}
  }
} | ConvertTo-Json -Depth 5
"""

SCHEDULED_TASK_QUERY = r"""
$task = Get-ScheduledTask -TaskName GTOS_Watchdog -ErrorAction SilentlyContinue
if ($null -eq $task) {
  [pscustomobject]@{
    exists=$false
    task_name='GTOS_Watchdog'
    status='absent'
  } | ConvertTo-Json -Depth 5
} else {
  $info = Get-ScheduledTaskInfo -TaskName GTOS_Watchdog -ErrorAction SilentlyContinue
  [pscustomobject]@{
    exists=$true
    task_name=$task.TaskName
    task_path=$task.TaskPath
    state=[string]$task.State
    enabled=$task.Settings.Enabled
    action_execute=($task.Actions | Select-Object -First 1).Execute
    action_arguments=($task.Actions | Select-Object -First 1).Arguments
    last_run_time=if ($info) { $info.LastRunTime.ToUniversalTime().ToString('o') } else { $null }
    last_task_result=if ($info) { $info.LastTaskResult } else { $null }
    next_run_time=if ($info) { $info.NextRunTime.ToUniversalTime().ToString('o') } else { $null }
    number_of_missed_runs=if ($info) { $info.NumberOfMissedRuns } else { $null }
    supervision_model='scheduled_one_shot_hidden_launcher'
  } | ConvertTo-Json -Depth 5
}
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def powershell_json(script: str) -> Any:
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()
    if not output:
        return []
    return json.loads(output)


def as_list(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bridge_process_summary(checkpoint: dict[str, Any]) -> dict[str, Any]:
    followers = checkpoint.get("dual_broker_execution_followers") or []
    projectors = checkpoint.get("dual_broker_trade_record_projectors") or []
    follower = followers[0] if followers else {}
    projector = projectors[0] if projectors else {}
    return {
        "dual_broker_execution_follower_ftmo": {
            "pid": follower.get("pid"),
            "runtime_namespace": "operator_profile",
            "source_namespace": "redacted_account_live_bee34003",
            "profile": "operator_profile",
            "terminal_path": "C:\\MT5\\FTMO\\terminal64.exe",
            "order_enabled": "--order-enabled" in safe_cmd(follower),
            "notifications_enabled": "--enable-notifications" in safe_cmd(follower),
            "command_line": safe_cmd(follower),
        },
        "dual_broker_trade_record_projector": {
            "pid": projector.get("pid"),
            "source_profile": "redacted_account",
            "source_runtime_namespace": "redacted_account_live_bee34003",
            "source_root": "knowledge_base\\redacted_account_live_bee34003\\trade_records",
            "intent_log": "pipeline_state\\dual_broker\\canonical_trade_intents.jsonl",
            "command_line": safe_cmd(projector),
        },
    }


def mt5_probe_summary(probe: dict[str, Any]) -> dict[str, Any]:
    probes = probe.get("probes") if isinstance(probe.get("probes"), dict) else {}
    redacted_account = probes.get("redacted_account") if isinstance(probes.get("redacted_account"), dict) else {}
    ftmo = (
        probes.get("operator_profile")
        if isinstance(probes.get("operator_profile"), dict)
        else {}
    )
    redacted_account_symbols = (
        redacted_account.get("symbol_check_summary")
        if isinstance(redacted_account.get("symbol_check_summary"), dict)
        else {}
    )
    ftmo_symbols = (
        ftmo.get("symbol_check_summary")
        if isinstance(ftmo.get("symbol_check_summary"), dict)
        else {}
    )
    return {
        "artifact": "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json",
        "account_probe_status": probe.get("account_probe_status"),
        "status": probe.get("status"),
        "recorded_at_utc": probe.get("recorded_at_utc"),
        "broker_mutation_status": probe.get("broker_mutation_status", "none"),
        "runtime_effect_boundary": probe.get("runtime_effect_boundary"),
        "redacted_account": {
            "account_match_all": redacted_account.get("account_match_all"),
            "positions_total": redacted_account.get("positions_total"),
            "orders_total": redacted_account.get("orders_total"),
            "symbol_info_found": redacted_account_symbols.get("symbol_info_found"),
            "ticks_positive_without_mass_select": redacted_account_symbols.get(
                "positive_ticks_without_mass_select"
            ),
        },
        "ftmo": {
            "account_match_all": ftmo.get("account_match_all"),
            "positions_total": ftmo.get("positions_total"),
            "orders_total": ftmo.get("orders_total"),
            "symbol_info_found": ftmo_symbols.get("symbol_info_found"),
            "positive_ticks_without_mass_select": ftmo_symbols.get(
                "positive_ticks_without_mass_select"
            ),
            "absent_ticks_without_mass_select": ftmo_symbols.get(
                "absent_ticks_without_mass_select"
            ),
            "tick_policy": "unselected symbols intentionally not mass-selected; follower lazy-selects target symbol on real intent",
        },
    }


def safe_cmd(process: dict[str, Any]) -> str:
    return str(process.get("CommandLine") or process.get("command_line") or "")


def extract_arg(command_line: str, arg_name: str) -> str | None:
    pattern = rf"--{re.escape(arg_name)}(?:=|\s+)(\"[^\"]+\"|'[^']+'|\S+)"
    match = re.search(pattern, command_line)
    if not match:
        return None
    return match.group(1).strip("\"'")


def classify_run_agent(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for process in processes:
        if str(process.get("Name") or "").lower() not in {"python.exe", "pythonw.exe"}:
            continue
        command_line = safe_cmd(process)
        if "run_agent.py" not in command_line:
            continue
        row = {
            "pid": process.get("ProcessId"),
            "parent_pid": process.get("ParentProcessId"),
            "profile": extract_arg(command_line, "profile"),
            "runtime_namespace": extract_arg(command_line, "runtime-namespace"),
            "symbol": extract_arg(command_line, "symbol"),
            "terminal_path": extract_arg(command_line, "terminal-path"),
            "has_profile": "--profile" in command_line,
            "has_runtime_namespace": "--runtime-namespace" in command_line,
            "has_terminal_path": "--terminal-path" in command_line,
            "command_line": command_line,
        }
        row["account_classification"] = classify_account(row)
        rows.append(row)
    return rows


def classify_account(row: dict[str, Any]) -> str:
    profile = str(row.get("profile") or "").lower()
    namespace = str(row.get("runtime_namespace") or "").lower()
    terminal_path = str(row.get("terminal_path") or "").lower()
    if "ftmo" in profile or "ftmo" in namespace or "\\mt5\\ftmo\\" in terminal_path:
        return "ftmo"
    if "redacted_account" in profile or "redacted_account" in namespace or "program files\\metatrader 5" in terminal_path:
        return "redacted_account"
    return "unknown"


def duplicate_run_agents(run_agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str | None, str | None, str | None, str | None], list[int]] = {}
    for row in run_agents:
        key = (
            row.get("profile"),
            row.get("runtime_namespace"),
            row.get("symbol"),
            row.get("terminal_path"),
        )
        buckets.setdefault(key, []).append(int(row["pid"]))
    duplicates = []
    for key, pids in sorted(buckets.items(), key=lambda item: str(item[0])):
        if len(pids) > 1:
            duplicates.append(
                {
                    "profile": key[0],
                    "runtime_namespace": key[1],
                    "symbol": key[2],
                    "terminal_path": key[3],
                    "pids": pids,
                }
            )
    return duplicates


def count_matching(processes: list[dict[str, Any]], needle: str, python_only: bool = False) -> int:
    needle_lower = needle.lower()
    count = 0
    for process in processes:
        if python_only and str(process.get("Name") or "").lower() not in {"python.exe", "pythonw.exe"}:
            continue
        if needle_lower in safe_cmd(process).lower():
            count += 1
    return count


def command_has_script(process: dict[str, Any], script_name: str) -> bool:
    command_line = safe_cmd(process).replace("\\", "/").lower()
    return f"scripts/{script_name.lower()}" in command_line


def is_watchdog_process(process: dict[str, Any]) -> bool:
    name = str(process.get("Name") or "").lower()
    command_line = safe_cmd(process).replace("\\", "/").lower()
    if "get-ciminstance win32_process" in command_line:
        return False
    if name == "wscript.exe" and "scripts/watchdog_launcher.vbs" in command_line:
        return True
    if name == "cmd.exe" and "scripts/watchdog.bat" in command_line:
        return True
    if name in {"powershell.exe", "pwsh.exe"} and "-file" in command_line and "scripts/watchdog.ps1" in command_line:
        return True
    return False


def build_checkpoint(user_reported_reboot: bool) -> dict[str, Any]:
    now = utc_now()
    processes = as_list(powershell_json(PROCESS_QUERY))
    memory = powershell_json(MEMORY_QUERY)
    scheduled_watchdog = powershell_json(SCHEDULED_TASK_QUERY)
    run_agents = classify_run_agent(processes)
    terminals = [
        process
        for process in processes
        if str(process.get("Name") or "").lower() == "terminal64.exe"
    ]
    watchdog_processes = [process for process in processes if is_watchdog_process(process)]
    python_gtos_processes = [
        process
        for process in processes
        if str(process.get("Name") or "").lower() in {"python.exe", "pythonw.exe"}
        and "record_post_reboot_checkpoint.py" not in safe_cmd(process)
    ]
    unscoped_run_agents = [
        row
        for row in run_agents
        if not row["has_profile"] or not row["has_runtime_namespace"] or not row["has_terminal_path"]
    ]
    redacted_account_run_agents = [row for row in run_agents if row["account_classification"] == "redacted_account"]
    ftmo_run_agents = [row for row in run_agents if row["account_classification"] == "ftmo"]
    dual_broker_followers = [
        process
        for process in python_gtos_processes
        if command_has_script(process, "dual_broker_execution_follower.py")
    ]
    ftmo_dual_broker_followers = [
        process
        for process in dual_broker_followers
        if (
            "operator_profile" in safe_cmd(process).lower()
            or "\\mt5\\ftmo\\" in safe_cmd(process).lower()
        )
    ]
    dual_broker_projectors = [
        process
        for process in python_gtos_processes
        if command_has_script(process, "dual_broker_trade_record_projector.py")
    ]
    terminal_command_lines = [safe_cmd(process) for process in terminals]

    total_kb = int(memory.get("total_visible_memory_kb") or 0)
    free_kb = int(memory.get("free_physical_memory_kb") or 0)
    free_pct = round((free_kb / total_kb) * 100, 2) if total_kb else None
    if free_pct is not None and (free_kb < 800_000 or free_pct < 10.0):
        memory_status = "pressure"
    elif free_pct is not None and (free_kb < 1_500_000 or free_pct < 18.0):
        memory_status = "watch"
    else:
        memory_status = "healthy"

    duplicate_agents = duplicate_run_agents(run_agents)
    notification_worker_count = count_matching(processes, "src.utils.notification_queue", python_only=True)
    m1_capture_count = count_matching(processes, "src.components.m1_capture", python_only=True)
    tick_capture_count = count_matching(processes, "src.components.tick_capture", python_only=True)
    runtime_observed = bool(terminals or run_agents or dual_broker_followers or dual_broker_projectors or tick_capture_count or m1_capture_count)
    scheduled_watchdog_enabled = bool(scheduled_watchdog.get("exists") and scheduled_watchdog.get("enabled"))
    correct_dual_shape = bool(
        len(redacted_account_run_agents) == 24
        and len(ftmo_run_agents) == 0
        and len(ftmo_dual_broker_followers) == 1
        and len(dual_broker_projectors) == 1
        and not duplicate_agents
        and not unscoped_run_agents
    )
    if memory_status == "pressure":
        additional_launch_gate = "repair_process_footprint_before_continuing_memory_pressure_observed"
        next_action = "stop widening ledgers and repair live launch/process footprint before continuing"
    elif correct_dual_shape:
        additional_launch_gate = "continue_live_supervision_without_widening_footprint"
        next_action = "continue first post-activation intent, follower result, and lifecycle-copy supervision"
    else:
        additional_launch_gate = "repair_launch_process_footprint_before_continuing"
        next_action = "repair duplicate legacy unscoped or missing dual-bridge process footprint before launch"

    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "recorded_at_utc": now,
        "checkpoint_id": "dual_supervisor_process_memory_checkpoint",
        "user_reported_vps_reboot": user_reported_reboot,
        "runtime_effect_boundary": "read_only_os_process_memory_terminal_path_observation_no_broker_mutation",
        "memory": memory,
        "memory_status": memory_status,
        "memory_policy": "memory is a health checkpoint, not a reason to under-run the approved architecture; repair only sustained pressure or duplicate/stale process footprint",
        "free_physical_memory_pct": free_pct,
        "process_counts": {
            "total_relevant_processes": len(processes),
            "terminal64": len(terminals),
            "python_gtos_candidates": len(python_gtos_processes),
            "run_agent_total": len(run_agents),
            "run_agent_redacted_account": len(redacted_account_run_agents),
            "run_agent_ftmo": len(ftmo_run_agents),
            "dual_broker_execution_follower": len(dual_broker_followers),
            "dual_broker_execution_follower_ftmo": len(ftmo_dual_broker_followers),
            "dual_broker_trade_record_projector": len(dual_broker_projectors),
            "run_agent_unscoped_or_incomplete": len(unscoped_run_agents),
            "watchdog_related": len(watchdog_processes),
            "watchdog_live_processes": len(watchdog_processes),
            "notification_worker": notification_worker_count,
            "m1_capture": m1_capture_count,
            "tick_capture": tick_capture_count,
        },
        "watchdog_scheduler": scheduled_watchdog,
        "watchdog_supervision_model": (
            "scheduled_one_shot_configured_enabled"
            if scheduled_watchdog_enabled
            else "scheduled_watchdog_absent_or_disabled"
        ),
        "terminal_processes": [
            {
                "pid": process.get("ProcessId"),
                "parent_pid": process.get("ParentProcessId"),
                "executable_path": process.get("ExecutablePath"),
                "command_line": safe_cmd(process),
                "creation_date": process.get("CreationDate"),
                "working_set_size": process.get("WorkingSetSize"),
            }
            for process in terminals
        ],
        "terminal_command_lines": terminal_command_lines,
        "watchdog_processes": [
            {
                "pid": process.get("ProcessId"),
                "parent_pid": process.get("ParentProcessId"),
                "name": process.get("Name"),
                "command_line": safe_cmd(process),
                "creation_date": process.get("CreationDate"),
            }
            for process in watchdog_processes
        ],
        "run_agents": run_agents,
        "dual_broker_execution_followers": [
            {
                "pid": process.get("ProcessId"),
                "parent_pid": process.get("ParentProcessId"),
                "name": process.get("Name"),
                "command_line": safe_cmd(process),
                "creation_date": process.get("CreationDate"),
                "working_set_size": process.get("WorkingSetSize"),
            }
            for process in dual_broker_followers
        ],
        "dual_broker_trade_record_projectors": [
            {
                "pid": process.get("ProcessId"),
                "parent_pid": process.get("ParentProcessId"),
                "name": process.get("Name"),
                "command_line": safe_cmd(process),
                "creation_date": process.get("CreationDate"),
                "working_set_size": process.get("WorkingSetSize"),
            }
            for process in dual_broker_projectors
        ],
        "redacted_account_symbols": sorted({str(row.get("symbol")) for row in redacted_account_run_agents if row.get("symbol")}),
        "ftmo_symbols": sorted({str(row.get("symbol")) for row in ftmo_run_agents if row.get("symbol")}),
        "duplicate_run_agents": duplicate_agents,
        "unscoped_or_incomplete_run_agents": unscoped_run_agents,
        "correct_memory_conscious_dual_shape": correct_dual_shape,
        "auto_started_runtime_observed": runtime_observed,
        "redacted_account_runtime_status": "auto_started_present" if redacted_account_run_agents else "absent",
        "ftmo_runtime_status": (
            "secondary_execution_follower_present"
            if ftmo_dual_broker_followers
            else "present"
            if ftmo_run_agents
            else "absent"
        ),
        "additional_launch_gate": additional_launch_gate,
        "next_action": next_action,
    }


def write_route_evidence(checkpoint: dict[str, Any]) -> None:
    process_counts = checkpoint["process_counts"]
    environment_row = {
        **checkpoint,
        "artifact": "DUAL_ENVIRONMENT_LEDGER.jsonl",
        "status": "process_memory_environment_recorded",
    }
    process_row = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact": "DUAL_PROCESS_HEALTH_LEDGER.jsonl",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "status": "process_memory_snapshot_recorded",
        "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
        "process_counts": process_counts,
        "terminal_processes": checkpoint["terminal_processes"],
        "watchdog_processes": checkpoint["watchdog_processes"],
        "run_agents": checkpoint["run_agents"],
        "duplicate_run_agents": checkpoint["duplicate_run_agents"],
        "unscoped_or_incomplete_run_agents": checkpoint["unscoped_or_incomplete_run_agents"],
    }
    watchdog_row = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact": "DUAL_WATCHDOG_SCHEDULER_LEDGER.jsonl",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "status": "watchdog_autostart_observed" if checkpoint["auto_started_runtime_observed"] else "watchdog_absent",
        "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
        "watchdog_processes": checkpoint["watchdog_processes"],
        "watchdog_scheduler": checkpoint["watchdog_scheduler"],
        "watchdog_supervision_model": checkpoint["watchdog_supervision_model"],
        "auto_started_runtime_observed": checkpoint["auto_started_runtime_observed"],
    }
    restart_row = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact": "DUAL_RESTART_RELOAD_LEDGER.jsonl",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "status": "process_memory_checkpoint_no_process_launch",
        "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
        "user_reported_vps_reboot": checkpoint["user_reported_vps_reboot"],
        "assistant_launched_processes": False,
        "auto_started_runtime_observed": checkpoint["auto_started_runtime_observed"],
        "process_counts": process_counts,
    }
    checkpoint_row = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact": "DUAL_SUPERVISOR_CHECKPOINTS.jsonl",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "checkpoint_id": checkpoint["checkpoint_id"],
        "status": "process_memory_checkpoint_recorded",
        "memory_status": checkpoint["memory_status"],
        "memory_policy": checkpoint.get("memory_policy"),
        "free_physical_memory_pct": checkpoint["free_physical_memory_pct"],
        "redacted_account_runtime_status": checkpoint["redacted_account_runtime_status"],
        "ftmo_runtime_status": checkpoint["ftmo_runtime_status"],
        "next_action": checkpoint["next_action"],
        "additional_launch_gate": checkpoint["additional_launch_gate"],
        "correct_memory_conscious_dual_shape": checkpoint["correct_memory_conscious_dual_shape"],
        "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
    }
    action_row = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact": "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "action": "recorded_dual_supervisor_process_memory_checkpoint",
        "status": "completed",
        "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
    }

    append_jsonl(ROUTE_DIR / "DUAL_ENVIRONMENT_LEDGER.jsonl", environment_row)
    append_jsonl(ROUTE_DIR / "DUAL_PROCESS_HEALTH_LEDGER.jsonl", process_row)
    append_jsonl(ROUTE_DIR / "DUAL_WATCHDOG_SCHEDULER_LEDGER.jsonl", watchdog_row)
    append_jsonl(ROUTE_DIR / "DUAL_RESTART_RELOAD_LEDGER.jsonl", restart_row)
    append_jsonl(ROUTE_DIR / "DUAL_SUPERVISOR_CHECKPOINTS.jsonl", checkpoint_row)
    append_jsonl(ROUTE_DIR / "DUAL_SUPERVISOR_ACTION_LEDGER.jsonl", action_row)

    mt5_probe_path = ROUTE_DIR / "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json"
    mt5_probe = read_json(mt5_probe_path)
    state_path = ROUTE_DIR / "DUAL_SUPERVISOR_STATE.json"
    state = read_json(state_path)
    state.update(
        {
            "route_id": ROUTE_ID,
            "status": "active_supervision_checkpoint_repaired_bridge_live_continuation_required"
            if checkpoint["correct_memory_conscious_dual_shape"]
            else "active_supervision_process_footprint_repair_required",
            "latest_process_memory_checkpoint": checkpoint_row,
            "latest_read_only_process_observation": checkpoint,
            "post_reboot_checkpoint": checkpoint_row,
            "post_reboot_process_counts": process_counts,
            "post_reboot_memory_status": checkpoint["memory_status"],
            "post_reboot_free_physical_memory_pct": checkpoint["free_physical_memory_pct"],
            "watchdog_scheduler": checkpoint["watchdog_scheduler"],
            "watchdog_supervision_model": checkpoint["watchdog_supervision_model"],
            "redacted_account_runtime_status": checkpoint["redacted_account_runtime_status"],
            "ftmo_runtime_status": checkpoint["ftmo_runtime_status"],
            "live_bridge_processes": bridge_process_summary(checkpoint),
            "mt5_account_probe": mt5_probe_summary(mt5_probe),
            "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
            "additional_launch_gate": checkpoint["additional_launch_gate"],
            "next_required_action": checkpoint["next_action"],
            "goal_remains_active": True,
            "terminal_completion": False,
            "last_updated_utc": checkpoint["recorded_at_utc"],
        }
    )
    write_json(state_path, state)

    account_probe_status = mt5_probe.get("account_probe_status")
    if not account_probe_status:
        account_probe_status = "not_performed_by_process_memory_checkpoint"
    mt5_probe.update(
        {
            "route_id": ROUTE_ID,
            "post_reboot_updated_at_utc": checkpoint["recorded_at_utc"],
            "process_checkpoint_updated_at_utc": checkpoint["recorded_at_utc"],
            "terminal_path_existence": checkpoint["memory"].get("terminal_paths"),
            "terminal_processes": checkpoint["terminal_processes"],
            "account_probe_status": account_probe_status,
            "runtime_effect_boundary": checkpoint["runtime_effect_boundary"],
        }
    )
    write_json(mt5_probe_path, mt5_probe)

    manifest_path = ROUTE_DIR / "DUAL_OUTPUT_MANIFEST.json"
    manifest = read_json(manifest_path)
    manifest.update(
        {
            "route_id": ROUTE_ID,
            "post_reboot_evidence_updated_at_utc": checkpoint["recorded_at_utc"],
            "process_memory_checkpoint_updated_at_utc": checkpoint["recorded_at_utc"],
            "post_reboot_checkpoint_script": "record_post_reboot_checkpoint.py",
            "terminal_completion": False,
        }
    )
    write_json(manifest_path, manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-reported-reboot", action="store_true")
    args = parser.parse_args()
    checkpoint = build_checkpoint(user_reported_reboot=args.user_reported_reboot)
    write_route_evidence(checkpoint)
    print(json.dumps({
        "status": "RECORDED",
        "recorded_at_utc": checkpoint["recorded_at_utc"],
        "process_counts": checkpoint["process_counts"],
        "memory_status": checkpoint["memory_status"],
        "free_physical_memory_pct": checkpoint["free_physical_memory_pct"],
        "redacted_account_runtime_status": checkpoint["redacted_account_runtime_status"],
        "ftmo_runtime_status": checkpoint["ftmo_runtime_status"],
        "auto_started_runtime_observed": checkpoint["auto_started_runtime_observed"],
        "additional_launch_gate": checkpoint["additional_launch_gate"],
        "next_action": checkpoint["next_action"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
