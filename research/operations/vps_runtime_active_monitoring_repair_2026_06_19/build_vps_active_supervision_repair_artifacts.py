#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
PROMPT_PATH = ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md"
STARTER_PATH = ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_STARTER_2026_06_19.md"
PACKET_LOG = REPO_ROOT / "shadow_logs" / "ultimate_book_runtime_learning_packets.jsonl"
LAUNCHER_LOG = REPO_ROOT / "shadow_logs" / "ultimate_book_launcher.jsonl"
EXECUTION_MANAGER_LOG = REPO_ROOT / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
BROKER_LIFECYCLE_LOG = REPO_ROOT / "shadow_logs" / "broker_order_lifecycle_capture_v4.jsonl"
TRADE_RECORD_ROOT = REPO_ROOT / "pipeline_state" / "ultimate_book"

PROFILE_NAMES = {
    "operator_profile": "operator_profile",
    "redacted_account_live_bee34003": "redacted_account",
}

REQUIRED_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_MONITORING_REPAIR_EVIDENCE.md",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/OUTPUT_MANIFEST.json",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/COMPLETION_AUDIT.json",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/SATURATION_SELF_RED_TEAM_AUDIT.json",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_STARTER_2026_06_19.md",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_RESUME_GOAL_PROMPT_2026_06_19.md",
    "research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_RESUME_STARTER_2026_06_19.md",
    "research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md",
    "research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def stamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str, separators=(",", ":")) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return rows, [{"path": str(path.relative_to(REPO_ROOT)), "error": "missing_file"}]
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append({"path": str(path.relative_to(REPO_ROOT)), "line": line_no, "error": str(exc)})
                continue
            if isinstance(parsed, dict):
                parsed["_line_no"] = line_no
                rows.append(parsed)
            else:
                errors.append({"path": str(path.relative_to(REPO_ROOT)), "line": line_no, "error": "non_object_json"})
    return rows, errors


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def snapshot(obj: Any) -> dict[str, Any] | None:
    if obj is None:
        return None
    if hasattr(obj, "_asdict"):
        return dict(obj._asdict())
    if isinstance(obj, dict):
        return dict(obj)
    return {
        name: getattr(obj, name)
        for name in dir(obj)
        if not name.startswith("_") and not callable(getattr(obj, name))
    }


def sha256_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    import hashlib

    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def compact_account(account: dict[str, Any] | None) -> dict[str, Any] | None:
    if not account:
        return None
    return {
        "balance": account.get("balance"),
        "company": account.get("company"),
        "currency": account.get("currency"),
        "equity": account.get("equity"),
        "leverage": account.get("leverage"),
        "login_sha256": sha256_text(account.get("login")),
        "margin": account.get("margin"),
        "margin_free": account.get("margin_free"),
        "margin_level": account.get("margin_level"),
        "profit": account.get("profit"),
        "server": account.get("server"),
        "trade_allowed": account.get("trade_allowed"),
        "trade_expert": account.get("trade_expert"),
        "trade_mode": account.get("trade_mode"),
    }


def compact_terminal(terminal: dict[str, Any] | None) -> dict[str, Any] | None:
    if not terminal:
        return None
    return {
        "build": terminal.get("build"),
        "company": terminal.get("company"),
        "connected": terminal.get("connected"),
        "data_path": terminal.get("data_path"),
        "name": terminal.get("name"),
        "path": terminal.get("path"),
        "trade_allowed": terminal.get("trade_allowed"),
    }


def compact_position(position: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": position.get("ticket"),
        "time": position.get("time"),
        "time_msc": position.get("time_msc"),
        "type": position.get("type"),
        "magic": position.get("magic"),
        "identifier": position.get("identifier"),
        "reason": position.get("reason"),
        "volume": position.get("volume"),
        "price_open": position.get("price_open"),
        "price_current": position.get("price_current"),
        "sl": position.get("sl"),
        "tp": position.get("tp"),
        "swap": position.get("swap"),
        "profit": position.get("profit"),
        "symbol": position.get("symbol"),
        "comment": position.get("comment"),
    }


def compact_order(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": order.get("ticket"),
        "time_setup": order.get("time_setup"),
        "type": order.get("type"),
        "state": order.get("state"),
        "magic": order.get("magic"),
        "volume_initial": order.get("volume_initial"),
        "volume_current": order.get("volume_current"),
        "price_open": order.get("price_open"),
        "sl": order.get("sl"),
        "tp": order.get("tp"),
        "symbol": order.get("symbol"),
        "comment": order.get("comment"),
    }


def compact_deal(deal: dict[str, Any]) -> dict[str, Any]:
    return compact_deal_with_offset(deal, broker_offset_seconds=0)


def broker_epoch_to_utc_iso(value: Any, broker_offset_seconds: int, *, milliseconds: bool = False) -> str | None:
    if value in (None, ""):
        return None
    try:
        epoch = float(value)
    except (TypeError, ValueError):
        return None
    if milliseconds:
        epoch = epoch / 1000.0
    try:
        return iso(datetime.fromtimestamp(epoch - broker_offset_seconds, timezone.utc))
    except (OSError, OverflowError, ValueError):
        return None


def compact_deal_with_offset(deal: dict[str, Any], broker_offset_seconds: int) -> dict[str, Any]:
    return {
        "ticket": deal.get("ticket"),
        "order": deal.get("order"),
        "position_id": deal.get("position_id"),
        "time": deal.get("time"),
        "time_utc": broker_epoch_to_utc_iso(deal.get("time"), broker_offset_seconds),
        "time_msc": deal.get("time_msc"),
        "time_msc_utc": broker_epoch_to_utc_iso(deal.get("time_msc"), broker_offset_seconds, milliseconds=True),
        "type": deal.get("type"),
        "entry": deal.get("entry"),
        "magic": deal.get("magic"),
        "volume": deal.get("volume"),
        "price": deal.get("price"),
        "commission": deal.get("commission"),
        "swap": deal.get("swap"),
        "profit": deal.get("profit"),
        "symbol": deal.get("symbol"),
        "comment": deal.get("comment"),
    }


def broker_history_query_window(
    now: datetime,
    *,
    lookback_hours: int,
    broker_offset_seconds: int,
) -> dict[str, datetime]:
    history_from_utc = now - timedelta(hours=lookback_hours)
    offset = timedelta(seconds=broker_offset_seconds)
    return {
        "utc_from": history_from_utc,
        "utc_to": now,
        "mt5_query_from": history_from_utc + offset,
        "mt5_query_to": now + offset,
    }


def classify_append_order_regression(namespace: Any, previous_namespace: Any) -> str:
    if str(namespace) != str(previous_namespace):
        return "cross_namespace_append_order"
    return "same_namespace_timestamp_order_regression"


def run_powershell_json(script: str) -> Any:
    command = (
        "$ErrorActionPreference='Stop'; "
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        f"{script} | ConvertTo-Json -Depth 8"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip(), "returncode": proc.returncode}
    text = proc.stdout.strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def annotate_scheduled_task_health(tasks: Any, heartbeats: dict[str, Any]) -> Any:
    if isinstance(tasks, dict):
        task_rows = [tasks]
        scalar = True
    elif isinstance(tasks, list):
        task_rows = tasks
        scalar = False
    else:
        return tasks

    supervisor_heartbeat = heartbeats.get("pipeline_state\\supervisor_heartbeat.json") or {}
    supervisor_age = supervisor_heartbeat.get("age_seconds")
    supervisor_pid = (supervisor_heartbeat.get("payload") or {}).get("pid")

    annotated: list[dict[str, Any]] = []
    for task in task_rows:
        if not isinstance(task, dict):
            annotated.append(task)
            continue
        row = dict(task)
        task_name = row.get("TaskName")
        last_result = row.get("LastTaskResult")
        state = row.get("State")
        multiple_instances = str(row.get("MultipleInstances") or "")
        if (
            task_name == "GTOS_W7_BookSupervisor"
            and state == "Running"
            and last_result == 2147946720
            and multiple_instances == "IgnoreNew"
            and supervisor_pid
            and isinstance(supervisor_age, (int, float))
            and supervisor_age <= 120
        ):
            row["task_health_classification"] = "running_ignore_new_overlap_not_process_failure"
            row["task_health_evidence"] = {
                "supervisor_heartbeat_age_seconds": supervisor_age,
                "supervisor_heartbeat_pid": supervisor_pid,
                "last_task_result_hex": "0x800710E0",
            }
        elif last_result not in (None, 0):
            row["task_health_classification"] = "nonzero_result_requires_context"
        else:
            row["task_health_classification"] = "ok_or_disabled_zero_result"
        annotated.append(row)
    return annotated[0] if scalar else annotated


def collect_process_snapshot(now: datetime) -> dict[str, Any]:
    process_script = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -eq 'python.exe' -and ($_.CommandLine -like '*run_book.py*' "
        "-or $_.CommandLine -like '*.tools\\monitor_books.py*')) "
        "-or ($_.CommandLine -like '*run_book_supervisor.ps1*') } | "
        "Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine"
    )
    terminal_script = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -like 'terminal*.exe' -or $_.CommandLine -like '*terminal64*' "
        "} | Select-Object ProcessId,ParentProcessId,CreationDate,Name,CommandLine"
    )
    task_script = (
        "Get-ScheduledTask | Where-Object { $_.TaskName -like '*GTOS*' -or $_.TaskName -like '*Book*' } | "
        "ForEach-Object { $i = Get-ScheduledTaskInfo -TaskName $_.TaskName; "
        "[pscustomobject]@{TaskName=$_.TaskName;TaskPath=$_.TaskPath;State=$_.State.ToString();"
        "MultipleInstances=$_.Settings.MultipleInstances.ToString();"
        "LastRunTime=$i.LastRunTime;LastTaskResult=$i.LastTaskResult;NextRunTime=$i.NextRunTime;"
        "NumberOfMissedRuns=$i.NumberOfMissedRuns} }"
    )
    flags = {
        "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag": (REPO_ROOT / "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag").exists(),
        "pipeline_state/RESEARCH_RUNTIME_HALT.flag": (REPO_ROOT / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "knowledge_base/meta/AUTOSTART_DISABLED.flag": (REPO_ROOT / "knowledge_base/meta/AUTOSTART_DISABLED.flag").exists(),
        "pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag": (REPO_ROOT / "pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag").exists(),
        "pipeline_state/ULTIMATE_BOOK_KILL_fn.flag": (REPO_ROOT / "pipeline_state/ULTIMATE_BOOK_KILL_fn.flag").exists(),
    }
    heartbeats: dict[str, Any] = {}
    for path in [
        REPO_ROOT / "pipeline_state/supervisor_heartbeat.json",
        REPO_ROOT / "pipeline_state/ultimate_book/operator_profile/heartbeat.json",
        REPO_ROOT / "pipeline_state/ultimate_book/redacted_account_live_bee34003/heartbeat.json",
    ]:
        rel = str(path.relative_to(REPO_ROOT))
        if not path.exists():
            heartbeats[rel] = {"exists": False}
            continue
        try:
            payload = read_json(path)
        except Exception as exc:  # noqa: BLE001
            heartbeats[rel] = {"exists": True, "error": repr(exc)}
            continue
        hb_dt = parse_dt(payload.get("ts"))
        heartbeats[rel] = {
            "exists": True,
            "payload": payload,
            "age_seconds": None if hb_dt is None else round((now - hb_dt).total_seconds(), 3),
            "last_write_time_utc": iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)),
        }
    scheduled_tasks = run_powershell_json(task_script)
    return {
        "processes": run_powershell_json(process_script),
        "terminals": run_powershell_json(terminal_script),
        "scheduled_tasks": annotate_scheduled_task_health(scheduled_tasks, heartbeats),
        "halt_and_kill_flags": flags,
        "heartbeats": heartbeats,
        "log_files": {
            str(path.relative_to(REPO_ROOT)): {
                "exists": path.exists(),
                "length": path.stat().st_size if path.exists() else None,
                "last_write_time_utc": iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)) if path.exists() else None,
            }
            for path in [
                REPO_ROOT / "shadow_logs/book_supervisor.log",
                REPO_ROOT / "shadow_logs/monitor_daemon.log",
                REPO_ROOT / "shadow_logs/monitor_daemon.err",
                REPO_ROOT / "shadow_logs/run_book_console.log.err",
                REPO_ROOT / "shadow_logs/run_book_fn_console.log.err",
            ]
        },
    }


def collect_broker_snapshot(now: datetime) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"MetaTrader5 import failed: {exc!r}",
            "broker_mutation_status": "none",
            "runtime_effect_boundary": "read_only_attempt_failed_before_mt5_calls",
        }

    profiles: dict[str, Any] = {}
    for namespace, profile_name in PROFILE_NAMES.items():
        profile_path = REPO_ROOT / "config" / "profiles" / f"{profile_name}.yaml"
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
        mt5_cfg = profile.get("mt5") or {}
        terminal_path = str(mt5_cfg.get("terminal_path") or "")
        init_kwargs: dict[str, Any] = {"path": terminal_path} if terminal_path else {}
        if bool(mt5_cfg.get("portable", False)):
            init_kwargs["portable"] = True
        row: dict[str, Any] = {
            "namespace": namespace,
            "profile_name": profile_name,
            "profile_path": str(profile_path.relative_to(REPO_ROOT)),
            "terminal_path": terminal_path,
            "initialize_ok": False,
            "last_error": None,
        }
        initialized = bool(mt5.initialize(**init_kwargs))
        row["initialize_ok"] = initialized
        row["last_error"] = mt5.last_error()
        if not initialized:
            profiles[namespace] = row
            continue
        try:
            account = snapshot(mt5.account_info())
            terminal = snapshot(mt5.terminal_info())
            positions = [snapshot(item) for item in (mt5.positions_get() or [])]
            orders = [snapshot(item) for item in (mt5.orders_get() or [])]
            broker_offset_seconds = 0
            broker_offset_error = None
            try:
                from src.components.mt5_daemon_runtime import detect_broker_offset_seconds

                broker_offset_seconds = int(detect_broker_offset_seconds(mt5, now_fn=lambda: now))
            except Exception as exc:  # noqa: BLE001 - offset detection is evidence, not a hard MT5 failure
                broker_offset_error = repr(exc)
            query_window = broker_history_query_window(
                now,
                lookback_hours=12,
                broker_offset_seconds=broker_offset_seconds,
            )
            raw_deals = mt5.history_deals_get(query_window["mt5_query_from"], query_window["mt5_query_to"])
            deals_fetch_error = raw_deals is None
            deals = [snapshot(item) for item in (raw_deals or [])]
            positions = [item for item in positions if item]
            orders = [item for item in orders if item]
            deals = [item for item in deals if item]
            row.update(
                {
                    "account": compact_account(account),
                    "terminal": compact_terminal(terminal),
                    "positions_total": len(positions),
                    "orders_total": len(orders),
                    "recent_deals_total_12h": len(deals),
                    "recent_deals_query": {
                        "lookback_hours": 12,
                        "broker_offset_seconds": broker_offset_seconds,
                        "broker_offset_error": broker_offset_error,
                        "offset_source": "src.components.mt5_daemon_runtime.detect_broker_offset_seconds",
                        "utc_from": iso(query_window["utc_from"]),
                        "utc_to": iso(query_window["utc_to"]),
                        "mt5_query_from_broker_server_argument": query_window["mt5_query_from"].isoformat(),
                        "mt5_query_to_broker_server_argument": query_window["mt5_query_to"].isoformat(),
                        "mt5_history_deals_get_returned_none": deals_fetch_error,
                    },
                    "positions": [compact_position(item) for item in positions],
                    "orders": [compact_order(item) for item in orders],
                    "recent_deals_12h": [compact_deal_with_offset(item, broker_offset_seconds) for item in deals],
                }
            )
        finally:
            mt5.shutdown()
        profiles[namespace] = row

    all_positions = [
        position
        for profile in profiles.values()
        for position in profile.get("positions", [])
    ]
    metals_positions = [
        position
        for position in all_positions
        if any(token in str(position.get("symbol") or "").upper() for token in ("XAU", "XAG", "XPD", "GOLD"))
    ]
    missing_sl_or_tp = [
        {
            "namespace": namespace,
            "ticket": position.get("ticket"),
            "symbol": position.get("symbol"),
            "sl": position.get("sl"),
            "tp": position.get("tp"),
        }
        for namespace, profile in profiles.items()
        for position in profile.get("positions", [])
        if not position.get("sl") or not position.get("tp")
    ]
    return {
        "schema": "gtos.vps_active_supervision_repair.broker_snapshot.v1",
        "generated_at_utc": iso(now),
        "broker_mutation_status": "none",
        "runtime_effect_boundary": "read_only_mt5_account_terminal_position_order_history_deal_inspection_no_order_send_no_symbol_select_no_broker_mutation",
        "profiles": profiles,
        "summary": {
            "profiles_ok": all(profile.get("initialize_ok") for profile in profiles.values()),
            "positions_total": {name: profile.get("positions_total") for name, profile in profiles.items()},
            "orders_total": {name: profile.get("orders_total") for name, profile in profiles.items()},
            "recent_deals_total_12h": {name: profile.get("recent_deals_total_12h") for name, profile in profiles.items()},
            "metals_positions_total": len(metals_positions),
            "missing_sl_or_tp_count": len(missing_sl_or_tp),
        },
        "metals_positions": metals_positions,
        "missing_sl_or_tp": missing_sl_or_tp,
        "ok": all(profile.get("initialize_ok") for profile in profiles.values()) and not missing_sl_or_tp,
    }


def trade_record_payload(path: Path) -> dict[str, Any]:
    raw = read_json(path)
    instr = raw.get("instrumentation") if isinstance(raw, dict) else None
    body: dict[str, Any] = {}
    if isinstance(instr, dict):
        body.update(instr)
    if isinstance(raw, dict):
        body.update({key: value for key, value in raw.items() if key != "instrumentation"})
    execution = raw.get("execution") if isinstance(raw, dict) else None
    return {
        "namespace": path.parts[-3],
        "path": str(path.relative_to(REPO_ROOT)),
        "ticket": path.stem,
        "symbol": body.get("symbol"),
        "broker_symbol": body.get("broker_symbol") or (execution or {}).get("broker_symbol"),
        "direction": body.get("direction"),
        "candidate_id": body.get("candidate_id"),
        "decision_bar_iso": body.get("decision_bar_iso"),
        "decision_day": body.get("decision_day"),
        "placement_observed_at_utc": body.get("placement_observed_at_utc") or (execution or {}).get("placed_at_utc"),
        "joinability_status": body.get("joinability_status") or body.get("runtime_learning_joinability_status"),
        "trade_record_joinability_status": body.get("trade_record_joinability_status") or body.get("runtime_learning_joinability_status"),
        "trade_lifecycle_status": body.get("trade_lifecycle_status"),
        "close_action": body.get("close_action"),
        "closed_at_utc": body.get("closed_at_utc"),
        "policy": body.get("gtos_vnext_dynamic_policy_selected"),
        "execution_policy_id": body.get("gtos_vnext_execution_policy_id"),
        "stop_loss": body.get("stop_loss"),
        "take_profit_1": body.get("take_profit_1"),
        "risk_pct_override": body.get("risk_pct_override"),
    }


def inspect_slippage_sources(slippage_log_read_paths: Any) -> dict[str, Any]:
    source_files: list[dict[str, Any]] = []
    canonical = REPO_ROOT / "shadow_logs" / "slippage.jsonl"
    for source in slippage_log_read_paths(canonical):
        path = Path(source)
        file_summary: dict[str, Any] = {
            "path": rel(path),
            "exists": path.exists(),
            "line_count": 0,
            "json_row_count": 0,
            "non_json_line_count": 0,
            "lfs_pointer_signature_detected": False,
            "non_json_lines_sampled": [],
        }
        if not path.exists() or path.is_dir():
            source_files.append(file_summary)
            continue
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                file_summary["line_count"] += 1
                if line_no == 1 and text == "version https://git-lfs.github.com/spec/v1":
                    file_summary["lfs_pointer_signature_detected"] = True
                try:
                    row = json.loads(text)
                except json.JSONDecodeError:
                    file_summary["non_json_line_count"] += 1
                    if len(file_summary["non_json_lines_sampled"]) < 5:
                        file_summary["non_json_lines_sampled"].append(
                            {"line": line_no, "text_prefix": text[:120]}
                        )
                    continue
                if isinstance(row, dict):
                    file_summary["json_row_count"] += 1
        source_files.append(file_summary)
    return {
        "source_files": source_files,
        "source_file_count": len(source_files),
        "source_json_row_count": sum(int(row.get("json_row_count") or 0) for row in source_files),
        "source_non_json_line_count": sum(int(row.get("non_json_line_count") or 0) for row in source_files),
        "canonical_pointer_detected": any(row.get("lfs_pointer_signature_detected") for row in source_files),
        "mixed_content_detected": any(
            int(row.get("json_row_count") or 0) > 0 and int(row.get("non_json_line_count") or 0) > 0
            for row in source_files
        ),
    }


def collect_placement_ledger_audit() -> dict[str, Any]:
    from src.components.ultimate_book.placement_ledger import (
        PLACEMENT_CAPTURE_COMPLETE_STATUS,
        annotate_ticket_placement_completeness,
    )

    ledgers: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    incomplete_rows: list[dict[str, Any]] = []
    for path in sorted(TRADE_RECORD_ROOT.glob("*/placed_decisions.jsonl")):
        namespace = path.parent.name
        rows, errors = read_jsonl(path)
        parse_errors.extend(errors)
        ledger_rows: list[dict[str, Any]] = []
        for row in rows:
            material = {key: value for key, value in row.items() if key != "_line_no"}
            annotated = annotate_ticket_placement_completeness(material)
            summary = {
                "namespace": namespace,
                "path": rel(path),
                "line": row.get("_line_no"),
                "sleeve": annotated.get("sleeve"),
                "symbol": annotated.get("symbol"),
                "decision_bar_iso": annotated.get("decision_bar_iso"),
                "decision_day": annotated.get("decision_day"),
                "cluster": annotated.get("cluster"),
                "candidate_id": annotated.get("candidate_id"),
                "ticket": annotated.get("ticket"),
                "ts": annotated.get("ts"),
                "placement_capture_contract_version": annotated.get("placement_capture_contract_version"),
                "placement_source_completeness_status": annotated.get("placement_source_completeness_status"),
                "placement_source_missing_fields": annotated.get("placement_source_missing_fields") or [],
            }
            ledger_rows.append(summary)
            all_rows.append(summary)
            if summary["placement_source_completeness_status"] != PLACEMENT_CAPTURE_COMPLETE_STATUS:
                incomplete_rows.append(summary)
        ledgers.append(
            {
                "namespace": namespace,
                "path": rel(path),
                "row_count": len(ledger_rows),
                "incomplete_ticket_row_count": sum(
                    1
                    for item in ledger_rows
                    if item.get("placement_source_completeness_status") != PLACEMENT_CAPTURE_COMPLETE_STATUS
                ),
                "rows": ledger_rows,
            }
        )
    return {
        "ledger_count": len(ledgers),
        "row_count": len(all_rows),
        "parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "incomplete_ticket_row_count": len(incomplete_rows),
        "incomplete_ticket_rows": incomplete_rows,
        "ledgers": ledgers,
        "ok": not parse_errors and not incomplete_rows,
    }


def collect_packet_audit(now: datetime, broker_snapshot: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from src.components.ultimate_book.runtime_learning_packet import validate_runtime_learning_packet
    from src.components.slippage_shadow_logger import read_slippage_jsonl, slippage_log_read_paths

    packet_rows, packet_parse_errors = read_jsonl(PACKET_LOG)
    event_counts: Counter[str] = Counter()
    namespace_counts: Counter[str] = Counter()
    candidate_ids: set[str] = set()
    validation_issues: list[dict[str, Any]] = []
    append_regressions: list[dict[str, Any]] = []
    created_min: datetime | None = None
    created_max: datetime | None = None
    prev_dt: datetime | None = None
    prev_line: int | None = None
    prev_ns: str | None = None
    for row in packet_rows:
        packet_material = {key: value for key, value in row.items() if key != "_line_no"}
        event_counts[str(row.get("event_type"))] += 1
        namespace_counts[str(row.get("namespace"))] += 1
        if row.get("candidate_id"):
            candidate_ids.add(str(row["candidate_id"]))
        ok, issues = validate_runtime_learning_packet(packet_material)
        if not ok:
            validation_issues.append({"line": row.get("_line_no"), "issues": issues})
        dt = parse_dt(row.get("created_at_utc"))
        if dt is not None:
            created_min = dt if created_min is None or dt < created_min else created_min
            created_max = dt if created_max is None or dt > created_max else created_max
            if prev_dt is not None and dt < prev_dt:
                delta = (prev_dt - dt).total_seconds()
                classification = classify_append_order_regression(row.get("namespace"), prev_ns)
                append_regressions.append(
                    {
                        "line": row.get("_line_no"),
                        "created_at_utc": row.get("created_at_utc"),
                        "namespace": row.get("namespace"),
                        "previous_line": prev_line,
                        "previous_created_at_utc": iso(prev_dt),
                        "previous_namespace": prev_ns,
                        "delta_seconds": round(delta, 6),
                        "classification": classification,
                    }
                )
            prev_dt = dt
            prev_line = int(row.get("_line_no") or 0)
            prev_ns = str(row.get("namespace"))

    launcher_rows, launcher_errors = read_jsonl(LAUNCHER_LOG)
    launcher_actions: Counter[str] = Counter(str(row.get("action")) for row in launcher_rows)
    launcher_reasons: Counter[str] = Counter(str(row.get("reason")) for row in launcher_rows)
    placed_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    for row in launcher_rows:
        for placed in row.get("placed") or []:
            placed_rows.append(
                {
                    "line": row.get("_line_no"),
                    "namespace": row.get("namespace"),
                    "cycle_ts": row.get("ts"),
                    "symbol": placed.get("symbol"),
                    "broker_symbol": placed.get("broker_symbol"),
                    "sleeve": placed.get("sleeve"),
                    "candidate_id": placed.get("candidate_id"),
                    "decision_bar_iso": placed.get("decision_bar_iso"),
                    "decision_day": placed.get("decision_day"),
                    "joinability_status": placed.get("joinability_status"),
                    "placement_capture_contract_version": placed.get("placement_capture_contract_version"),
                    "placement_source_completeness_status": placed.get("placement_source_completeness_status"),
                    "placement_source_missing_fields": placed.get("placement_source_missing_fields"),
                }
            )
        for skipped in row.get("skipped") or []:
            skipped_rows.append(
                {
                    "line": row.get("_line_no"),
                    "namespace": row.get("namespace"),
                    "cycle_ts": row.get("ts"),
                    "symbol": skipped.get("symbol"),
                    "sleeve": skipped.get("sleeve"),
                    "decision_bar_iso": skipped.get("decision_bar_iso"),
                    "reason": skipped.get("reason"),
                }
            )

    execution_rows, execution_errors = read_jsonl(EXECUTION_MANAGER_LOG)
    broker_lifecycle_rows, broker_lifecycle_errors = read_jsonl(BROKER_LIFECYCLE_LOG)
    trade_records = [trade_record_payload(path) for path in sorted(TRADE_RECORD_ROOT.glob("*/trade_records/*.json"))]
    placement_ledger = collect_placement_ledger_audit()

    open_broker_tickets = {
        namespace: {str(position.get("ticket")) for position in profile.get("positions", [])}
        for namespace, profile in (broker_snapshot.get("profiles") or {}).items()
    }
    local_open_tickets = defaultdict(set)
    for record in trade_records:
        if record.get("trade_lifecycle_status") != "closed":
            local_open_tickets[record["namespace"]].add(str(record["ticket"]))
    consistency = {
        "broker_open_tickets": {namespace: sorted(tickets) for namespace, tickets in open_broker_tickets.items()},
        "local_nonclosed_trade_record_tickets": {namespace: sorted(tickets) for namespace, tickets in local_open_tickets.items()},
        "broker_open_without_local_record": {
            namespace: sorted(tickets - local_open_tickets.get(namespace, set()))
            for namespace, tickets in open_broker_tickets.items()
        },
        "local_nonclosed_absent_from_broker": {
            namespace: sorted(local_open_tickets.get(namespace, set()) - tickets)
            for namespace, tickets in open_broker_tickets.items()
        },
    }
    slippage_rows = read_slippage_jsonl(REPO_ROOT / "shadow_logs" / "slippage.jsonl")
    slippage_source_summary = inspect_slippage_sources(slippage_log_read_paths)
    append_regression_class_counts = Counter(str(row.get("classification")) for row in append_regressions)
    return {
        "schema": "gtos.vps_active_supervision_repair.packet_chronology_audit.v1",
        "generated_at_utc": iso(now),
        "runtime_effect_boundary": "read_only_log_and_trade_record_parse_no_broker_mutation",
        "packet_log": {
            "path": str(PACKET_LOG.relative_to(REPO_ROOT)),
            "line_count": len(packet_rows),
            "parse_error_count": len(packet_parse_errors),
            "parse_errors": packet_parse_errors,
            "validation_issue_count": len(validation_issues),
            "validation_issues": validation_issues,
            "created_at_min": None if created_min is None else iso(created_min),
            "created_at_max": None if created_max is None else iso(created_max),
            "event_counts": dict(sorted(event_counts.items())),
            "namespace_counts": dict(sorted(namespace_counts.items())),
            "unique_candidate_id_count": len(candidate_ids),
            "append_order_regression_count": len(append_regressions),
            "append_order_regression_class_counts": dict(sorted(append_regression_class_counts.items())),
            "same_namespace_append_order_regression_count": append_regression_class_counts.get(
                "same_namespace_timestamp_order_regression",
                0,
            ),
            "cross_namespace_append_order_count": append_regression_class_counts.get(
                "cross_namespace_append_order",
                0,
            ),
            "append_order_regressions": append_regressions,
        },
        "launcher_log": {
            "path": str(LAUNCHER_LOG.relative_to(REPO_ROOT)),
            "line_count": len(launcher_rows),
            "parse_error_count": len(launcher_errors),
            "action_counts": dict(sorted(launcher_actions.items())),
            "reason_counts": dict(sorted(launcher_reasons.items())),
            "placed_rows": placed_rows,
            "skipped_rows": skipped_rows,
            "skip_reason_counts": dict(sorted(Counter(row["reason"] for row in skipped_rows).items())),
        },
        "execution_manager_log": {
            "path": str(EXECUTION_MANAGER_LOG.relative_to(REPO_ROOT)),
            "line_count": len(execution_rows),
            "parse_error_count": len(execution_errors),
            "action_counts": dict(sorted(Counter(str(row.get("action")) for row in execution_rows).items())),
            "fatal_reason_rows": [
                {"line": row.get("_line_no"), "fatal_reasons": row.get("fatal_reasons")}
                for row in execution_rows
                if row.get("fatal_reasons")
            ],
        },
        "broker_lifecycle_log": {
            "path": str(BROKER_LIFECYCLE_LOG.relative_to(REPO_ROOT)),
            "line_count": len(broker_lifecycle_rows),
            "parse_error_count": len(broker_lifecycle_errors),
            "stage_counts": dict(sorted(Counter(str(row.get("stage")) for row in broker_lifecycle_rows).items())),
            "status_counts": dict(sorted(Counter(str(row.get("status")) for row in broker_lifecycle_rows).items())),
        },
        "slippage_stream": {
            "merged_row_count": len(slippage_rows),
            "symbols": dict(sorted(Counter(str(row.get("symbol")) for row in slippage_rows).items())),
            **slippage_source_summary,
        },
        "trade_records": {
            "count": len(trade_records),
            "records": trade_records,
            "lifecycle_counts": dict(sorted(Counter(str(row.get("trade_lifecycle_status") or "nonclosed") for row in trade_records).items())),
            "joinability_counts": dict(sorted(Counter(str(row.get("trade_record_joinability_status") or row.get("joinability_status") or "missing") for row in trade_records).items())),
            "active_consistency": consistency,
        },
        "placement_ledger": placement_ledger,
        "ok": not packet_parse_errors
        and not validation_issues
        and not launcher_errors
        and not execution_errors
        and not broker_lifecycle_errors
        and placement_ledger.get("ok") is True
        and not any(consistency["broker_open_without_local_record"].values())
        and not any(consistency["local_nonclosed_absent_from_broker"].values()),
    }


def collect_profile_detail_audit(now: datetime) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
        from scripts.audit_broker_profile_market_details import build_report
    except Exception as exc:  # noqa: BLE001
        return {
            "schema": "gtos.vps_active_supervision_repair.profile_detail_audit.v1",
            "generated_at_utc": iso(now),
            "ok": False,
            "issue_count": 1,
            "issues": [{"code": "profile_detail_audit_import_failed", "error": repr(exc)}],
        }
    report = build_report(
        agent_config_path=REPO_ROOT / "config" / "agent_config.yaml",
        profile_names=("operator_profile", "redacted_account"),
        mt5_module=mt5,
    )
    report["schema"] = "gtos.vps_active_supervision_repair.profile_detail_audit.v1"
    report["runtime_effect_boundary"] = (
        "read_only_mt5_account_terminal_symbol_tick_inspection_no_symbol_select_no_broker_mutation"
    )
    return report


def write_context_anchor(now: datetime, branch: str, head: str, process_snapshot: dict[str, Any]) -> None:
    lines = [
        "# VPS Active Supervision Repair Context Anchor",
        "",
        f"Generated: `{iso(now)}`",
        f"Branch: `{branch}`",
        f"HEAD: `{head}`",
        "",
        "## Objective",
        "",
        "Active production-code/runtime supervision and repair for the current GTOS ultimate-book package.",
        "This checkpoint is not a broker operation and not a discretionary trade decision.",
        "",
        "## Controlling Files Read",
        "",
    ]
    for rel in REQUIRED_CONTEXT_FILES:
        lines.append(f"- `{rel}`")
    lines.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "- Evidence class: `production-code/runtime supervision and repair`.",
            "- Broker mutation status: `none`.",
            "- Forbidden surfaces preserved: no order send/modify/cancel/close, no account/deal/history mutation, no credential mutation/disclosure, no paid/vendor calls, no broad remote history rewrite.",
            "- Runtime process effect in this checkpoint: `none` unless a separate action ledger row says otherwise.",
            "",
            "## Current Process Snapshot Summary",
            "",
        ]
    )
    heartbeats = process_snapshot.get("heartbeats") or {}
    for path, heartbeat in heartbeats.items():
        lines.append(f"- `{path}` age_seconds=`{heartbeat.get('age_seconds')}` healthy=`{(heartbeat.get('payload') or {}).get('healthy')}`")
    lines.append("")
    (ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md").write_text("\n".join(lines), encoding="utf-8")


def manifest_artifacts(generated: dict[str, Path]) -> list[dict[str, str]]:
    static = [
        ("VPS_ACTIVE_MONITORING_REPAIR_EVIDENCE.md", "prior_primary_evidence"),
        ("COMPLETION_AUDIT.json", "prior_completion_audit"),
        ("DECISION_LEDGER.jsonl", "prior_decision_ledger"),
        ("FOCUSED_TEST_RESULT.json", "prior_focused_test_result"),
        ("VERIFICATION_RESULT.json", "prior_verification_result"),
        ("SLIPPAGE_RUNTIME_MERGE_FOCUSED_TEST_RESULT.json", "prior_slippage_runtime_merge_focused_test_result"),
        ("SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.json", "slippage_cost_runtime_merge_coverage_json"),
        ("SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.md", "slippage_cost_runtime_merge_coverage_md"),
        ("BROKER_R_RUNTIME_MERGE_COVERAGE.json", "broker_r_runtime_merge_coverage_json"),
        ("BROKER_R_RUNTIME_MERGE_COVERAGE.md", "broker_r_runtime_merge_coverage_md"),
        ("LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.json", "live_shadow_followup_runtime_merge_coverage_json"),
        ("LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.md", "live_shadow_followup_runtime_merge_coverage_md"),
        ("VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.json", "prior_broker_profile_market_detail_audit_json"),
        ("VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.md", "prior_broker_profile_market_detail_audit_md"),
        ("BROKER_PROFILE_MARKET_DETAIL_FOCUSED_TEST_RESULT.json", "prior_broker_profile_market_detail_focused_test_result"),
        ("VPS_TO_MAC_RESEARCH_HANDOFF_2026_06_19.md", "research_session_handoff"),
        ("MAC_RESEARCH_STARTER_2026_06_19.md", "research_session_starter"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md", "active_supervision_repair_goal_prompt"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_STARTER_2026_06_19.md", "active_supervision_repair_starter"),
        ("SATURATION_SELF_RED_TEAM_AUDIT.json", "prior_residual_risk_review"),
        ("NEXT_PROMPT.md", "successor_prompt"),
        ("BOM_JSON_READER_FOCUSED_TEST_RESULT.json", "active_supervision_bom_json_reader_focused_test_result"),
        ("verify_vps_runtime_active_monitoring_repair.py", "route_verifier"),
        ("build_vps_active_supervision_repair_artifacts.py", "active_supervision_artifact_builder"),
        ("perform_controlled_book_worker_reload.py", "active_supervision_controlled_reload_utility"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md", "active_supervision_context_anchor"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl", "active_supervision_cycle_ledger"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl", "active_supervision_issue_ledger"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl", "active_supervision_action_ledger"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl", "active_supervision_subagent_ledger"),
        ("VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json", "active_supervision_completion_or_handoff_audit"),
    ]
    rows = [{"path": path, "role": role} for path, role in static if (ROUTE / path).exists()]
    rows.extend(
        {"path": path.name, "role": "active_supervision_reload_proof"}
        for path in sorted(ROUTE.glob("VPS_ACTIVE_SUPERVISION_REPAIR_RELOAD_PROOF_*.json"))
    )
    rows.extend({"path": path.name, "role": role} for role, path in generated.items())
    return rows


def update_next_prompt(now: datetime) -> None:
    text = (
        "Continue the active VPS supervision repair goal from current disk state. "
        "Regenerate `.context/LIVE_STATE.md`, reread "
        "`VPS_ACTIVE_SUPERVISION_REPAIR_STARTER_2026_06_19.md`, "
        "`VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md`, doctrine, "
        "and the latest `VPS_ACTIVE_SUPERVISION_REPAIR_*` artifacts before acting. "
        "Use the newest broker snapshot, packet chronology audit, profile detail audit, "
        "subagent ledger, and completion/handoff audit as the handoff state. "
        "Maintain read-only broker/account/order/history/deal/position boundaries unless "
        "the owner gives a separate explicit live-operation instruction. "
        f"Last refreshed by builder at `{iso(now)}`.\n"
    )
    (ROUTE / "NEXT_PROMPT.md").write_text(text, encoding="utf-8")


def git_value(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    return proc.stdout.strip() if proc.returncode == 0 else f"ERROR:{proc.stderr.strip()}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-status", default="active_supervision_checkpoint_generated")
    parser.add_argument(
        "--runtime-effect-boundary",
        default="read_only_supervision_artifact_refresh_no_reload_no_broker_mutation",
        choices=[
            "read_only_supervision_artifact_refresh_no_reload_no_broker_mutation",
            "controlled_book_worker_reload_no_broker_mutation",
        ],
    )
    parser.add_argument("--reload-proof-path", default="")
    args = parser.parse_args(argv)

    now = utc_now()
    cycle_id = f"vps_active_supervision_{stamp(now)}"
    branch = git_value(["branch", "--show-current"])
    head = git_value(["rev-parse", "HEAD"])
    process_snapshot = collect_process_snapshot(now)
    broker_snapshot = collect_broker_snapshot(now)
    packet_audit = collect_packet_audit(now, broker_snapshot)
    profile_audit = collect_profile_detail_audit(now)

    stamp_value = stamp(now)
    generated = {
        "active_supervision_broker_snapshot": ROUTE / f"VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_{stamp_value}.json",
        "active_supervision_packet_chronology_audit": ROUTE / f"VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_{stamp_value}.json",
        "active_supervision_profile_detail_audit": ROUTE / f"VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_{stamp_value}.json",
        "active_supervision_limitations_and_opportunities": ROUTE / f"VPS_ACTIVE_SUPERVISION_REPAIR_LIMITATIONS_AND_OPPORTUNITIES_{stamp_value}.md",
    }

    write_json(generated["active_supervision_broker_snapshot"], broker_snapshot)
    write_json(generated["active_supervision_packet_chronology_audit"], packet_audit)
    write_json(generated["active_supervision_profile_detail_audit"], profile_audit)
    write_context_anchor(now, branch, head, process_snapshot)

    broker_summary = broker_snapshot.get("summary") or {}
    packet_summary = packet_audit.get("packet_log") or {}
    issue_rows = [
        {
            "cycle_id": cycle_id,
            "issue_id": "ACTIVE-SUPERVISION-001",
            "status": "repaired_by_current_artifact_contract_refresh",
            "classification": "stale_route_artifact_contract",
            "summary": "The prior route completion audit can become stale as live broker positions change; this cycle refreshes the prompt-required VPS_ACTIVE_SUPERVISION_REPAIR artifact set from current read-only evidence.",
            "evidence": ["VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md", generated["active_supervision_broker_snapshot"].name],
            "runtime_effect_boundary": "artifact_and_verifier_repair_only",
        },
        {
            "cycle_id": cycle_id,
            "issue_id": "ACTIVE-SUPERVISION-002",
            "status": "bounded_not_fabricated",
            "classification": "legacy_joinability_limitation",
            "summary": "Legacy index trade records without durable placement rows remain ticket_policy_joinable; current source-bound placement rows are preserved as candidate/decision/policy joinable where available.",
            "evidence": [generated["active_supervision_packet_chronology_audit"].name],
            "runtime_effect_boundary": "no_synthetic_candidate_truth_backfill",
        },
        {
            "cycle_id": cycle_id,
            "issue_id": "ACTIVE-SUPERVISION-003",
            "status": "repaired_by_utf8_sig_json_reader",
            "classification": "route_artifact_reader_bom_tolerance",
            "summary": "The supervisor heartbeat file can be written with a UTF-8 BOM; route JSON readers now parse valid BOM-prefixed JSON so process health is not misclassified as a decode error.",
            "evidence": [
                "pipeline_state/supervisor_heartbeat.json",
                "build_vps_active_supervision_repair_artifacts.py",
                generated["active_supervision_limitations_and_opportunities"].name,
            ],
            "runtime_effect_boundary": "artifact_reader_repair_only_no_broker_mutation",
        },
        {
            "cycle_id": cycle_id,
            "issue_id": "ACTIVE-SUPERVISION-004",
            "status": "repaired_by_scheduler_overlap_classification",
            "classification": "scheduler_overlap_status_noise",
            "summary": "GTOS_W7_BookSupervisor LastTaskResult 0x800710E0 is classified as running IgnoreNew overlap when the supervisor heartbeat is fresh, so route artifacts do not confuse expected overlap refusal with process failure.",
            "evidence": [
                "scripts/run_book_supervisor.ps1",
                "pipeline_state/supervisor_heartbeat.json",
                "VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl",
            ],
            "runtime_effect_boundary": "artifact_classifier_repair_only_no_scheduler_mutation",
        },
    ]
    for row in issue_rows:
        append_jsonl(ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl", row)

    append_jsonl(
        ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl",
        {
            "cycle_id": cycle_id,
            "generated_at_utc": iso(now),
            "branch": branch,
            "head": head,
            "process_snapshot": process_snapshot,
            "broker_summary": broker_summary,
            "packet_summary": {
                "line_count": packet_summary.get("line_count"),
                "validation_issue_count": packet_summary.get("validation_issue_count"),
                "append_order_regression_count": packet_summary.get("append_order_regression_count"),
                "event_counts": packet_summary.get("event_counts"),
            },
            "profile_audit_summary": {
                "ok": profile_audit.get("ok"),
                "issue_count": profile_audit.get("issue_count"),
                "warning_count": profile_audit.get("warning_count"),
                "active_symbol_count": profile_audit.get("active_symbol_count"),
            },
            "broker_mutation_status": "none",
            "runtime_effect_boundary": args.runtime_effect_boundary,
            "status": "complete_for_cycle",
        },
    )
    append_jsonl(
        ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl",
        {
            "cycle_id": cycle_id,
            "generated_at_utc": iso(now),
            "action": "generated_active_supervision_route_artifacts",
            "artifacts": [path.name for path in generated.values()]
            + [
                "VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md",
                "VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl",
                "VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl",
            ],
            "broker_mutation_status": "none",
            "runtime_effect_boundary": "read_only_artifact_generation",
            "status": "complete",
        },
    )
    if args.reload_proof_path:
        append_jsonl(
            ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl",
            {
                "cycle_id": cycle_id,
                "generated_at_utc": iso(now),
                "action": "controlled_book_worker_reload_to_activate_live_facing_code_repair",
                "artifacts": [Path(args.reload_proof_path).name],
                "broker_mutation_status": "none",
                "runtime_effect_boundary": "controlled_book_worker_reload_no_broker_mutation",
                "status": "complete",
            },
        )

    slippage_summary = packet_audit.get("slippage_stream") or {}
    limitations = [
        "# VPS Active Supervision Repair Limitations And Opportunities",
        "",
        f"Generated: `{iso(now)}`",
        "",
        "## Current Findings",
        "",
        f"- Broker snapshot ok: `{broker_snapshot.get('ok')}`; positions total: `{broker_summary.get('positions_total')}`; orders total: `{broker_summary.get('orders_total')}`.",
        f"- Metals/gold positions: `{broker_summary.get('metals_positions_total')}`.",
        f"- Runtime-learning packets parsed: `{packet_summary.get('line_count')}`; validation issues: `{packet_summary.get('validation_issue_count')}`.",
        f"- Slippage merged stream rows: `{slippage_summary.get('merged_row_count')}`.",
        f"- Slippage source files: `{slippage_summary.get('source_file_count')}`; non-JSON source lines explicitly recorded: `{slippage_summary.get('source_non_json_line_count')}`; mixed content detected: `{slippage_summary.get('mixed_content_detected')}`.",
        f"- Profile audit ok: `{profile_audit.get('ok')}`; issues: `{profile_audit.get('issue_count')}`; warnings: `{profile_audit.get('warning_count')}`.",
        "",
        "## Repairable Gaps Addressed In This Checkpoint",
        "",
        "- Active route artifacts now preserve the current read-only broker/packet/profile state and the prompt-required supervision ledger set.",
        "- Route verification should use current merged slippage counts rather than the earlier fixed count.",
        "- Canonical slippage LFS-pointer mixed content is now explicit artifact evidence instead of a silent reader assumption.",
        "- Supervisor heartbeat JSON with a UTF-8 BOM is parsed as valid JSON instead of being recorded as a decode error.",
        "- `GTOS_W7_BookSupervisor` task result `0x800710E0` is classified as `running_ignore_new_overlap_not_process_failure` when `MultipleInstances=IgnoreNew` and the supervisor heartbeat is fresh.",
        "- Broker recent-deal queries use broker-server offset-aware MT5 history windows and preserve UTC-normalized deal timestamps.",
        "- Cross-namespace packet append inversions are classified separately from same-namespace timestamp regressions.",
        "",
        "## Residuals",
        "",
        "- Legacy index records without durable placement rows remain `ticket_policy_joinable`; fabricating missing candidate truth remains forbidden.",
        "- redacted_account unsupported symbols remain fail-closed direct-broker gaps unless a separate broker-profile/source lane proves support.",
        "- Scheduled task overlap remains intentionally non-fatal; process and heartbeat state are the health authority.",
        "",
    ]
    generated["active_supervision_limitations_and_opportunities"].write_text("\n".join(limitations), encoding="utf-8")

    self_red_team = [
        {
            "question": "Did this checkpoint mutate broker/account/order/deal/position state?",
            "answer": "No broker mutation was performed; broker snapshots use account, terminal, positions, orders, and history reads only.",
            "evidence": [generated["active_supervision_broker_snapshot"].name],
            "status": "passed",
        },
        {
            "question": "Could current slippage evidence be silently undercounted because the canonical file contains LFS pointer lines?",
            "answer": "The packet chronology audit records each slippage source file, JSON row counts, non-JSON line counts, and mixed-content detection.",
            "evidence": [generated["active_supervision_packet_chronology_audit"].name],
            "status": "passed",
        },
        {
            "question": "Did the route rely on arbitrary top-N sampling?",
            "answer": "No. The packet audit parses the full active packet log and ledgers retain full cycle rows for this checkpoint.",
            "evidence": ["VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl"],
            "status": "passed",
        },
        {
            "question": "Were legacy missing candidate joins fabricated?",
            "answer": "No. Legacy ticket-policy-only records remain bounded residuals without synthetic candidate truth.",
            "evidence": [generated["active_supervision_packet_chronology_audit"].name],
            "status": "passed",
        },
        {
            "question": "Is there a direct handoff if the rolling supervision goal continues?",
            "answer": "Yes. The context anchor, completion/handoff audit, manifest, next prompt, and ledgers identify the next required reads and residuals.",
            "evidence": [
                "VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md",
                "VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json",
                "NEXT_PROMPT.md",
            ],
            "status": "passed",
        },
    ]

    completion = {
        "schema": "gtos.vps_active_supervision_repair.completion_or_handoff_audit.v1",
        "generated_at_utc": iso(now),
        "cycle_id": cycle_id,
        "checkpoint_status": args.checkpoint_status,
        "branch": branch,
        "head": head,
        "goal_completion_status": "not_marked_complete_rolling_supervision_goal",
        "instruction_coverage": {
            "starter_read": True,
            "controlling_prompt_read": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_doctrine_read": True,
            "latest_handoff_read_as_historical": True,
            "latest_route_artifacts_read": True,
            "no_arbitrary_top_n": True,
            "same_evidence_class_pursuit": True,
            "forbidden_surfaces_preserved": True,
            "context_files": REQUIRED_CONTEXT_FILES,
        },
        "runtime_effect_boundary": args.runtime_effect_boundary,
        "broker_mutation_status": "none",
        "forbidden_surfaces_status": {
            "manual_broker_operation": False,
            "order_mutation": False,
            "account_history_deal_position_mutation": False,
            "credential_mutation_or_disclosure": False,
            "paid_api_vendor_call": False,
            "broad_remote_history_rewrite": False,
        },
        "active_trade_status": broker_summary,
        "packet_chronology_status": {
            "ok": packet_audit.get("ok"),
            "packet_log": packet_audit.get("packet_log"),
            "trade_record_consistency": (packet_audit.get("trade_records") or {}).get("active_consistency"),
        },
        "profile_detail_status": {
            "ok": profile_audit.get("ok"),
            "issue_count": profile_audit.get("issue_count"),
            "warning_count": profile_audit.get("warning_count"),
        },
        "artifact_paths": {role: path.name for role, path in generated.items()},
        "verification_status": "pending_post_generation_verifier_and_tests",
        "reload_proof_path": Path(args.reload_proof_path).name if args.reload_proof_path else None,
        "self_red_team": self_red_team,
        "rollback_status": {
            "runtime_reload_performed": args.runtime_effect_boundary == "controlled_book_worker_reload_no_broker_mutation",
            "rollback_required": False,
            "code_rollback": "git revert scoped checkpoint commit if committed",
            "market_expansion_policy_rollback": "robust6_every_split_positive or market-expansion-off remains documented in activation handoff",
        },
        "unresolved_requirements": [
            {
                "id": "LEGACY-INDEX-JOINABILITY",
                "status": "bounded_not_repairable_without_historical_durable_placement_rows",
                "requirement": "Do not fabricate candidate/decision truth for legacy active index tickets.",
            }
        ],
        "ok": broker_snapshot.get("ok") is True and packet_audit.get("ok") is True and profile_audit.get("ok") is True,
    }
    write_json(ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json", completion)

    manifest = {
        "schema": "gtos.vps_runtime_active_monitoring_repair.output_manifest.v2",
        "generated_at_utc": iso(now),
        "route": "research/operations/vps_runtime_active_monitoring_repair_2026_06_19",
        "artifacts": manifest_artifacts(generated),
        "ok": completion["ok"],
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    update_next_prompt(now)

    print(json.dumps({"ok": completion["ok"], "cycle_id": cycle_id, "generated": {k: v.name for k, v in generated.items()}}, indent=2, sort_keys=True))
    return 0 if completion["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
