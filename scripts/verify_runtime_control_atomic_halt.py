#!/usr/bin/env python3
"""Verify the runtime-control atomic halt wiring.

This verifier is read-only. It checks config/source contracts and emits JSON
evidence for the Wave3 runtime-control route.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FLAGS = {
    "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag",
    "pipeline_state/RESEARCH_RUNTIME_HALT.flag",
    "knowledge_base/meta/AUTOSTART_DISABLED.flag",
}


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def _contains_all(rel_path: str, required: list[str]) -> dict[str, Any]:
    text = _read(rel_path)
    missing = [token for token in required if token not in text]
    return {
        "path": rel_path,
        "status": "pass" if not missing else "fail",
        "missing_tokens": missing,
        "required_tokens": required,
    }


def _config_check() -> dict[str, Any]:
    config = yaml.safe_load(_read("config/agent_config.yaml")) or {}
    block = config.get("runtime_control") or {}
    flags = set(block.get("halt_flag_paths") or [])
    failures: list[str] = []
    if block.get("enabled") is not True:
        failures.append("runtime_control.enabled is not true")
    if block.get("halt_guard_version") != "runtime_control_atomic_halt_v1":
        failures.append("halt_guard_version mismatch")
    if flags != REQUIRED_FLAGS:
        failures.append(f"halt_flag_paths mismatch: {sorted(flags)}")
    if block.get("broker_runtime_change_status") is not False:
        failures.append("broker_runtime_change_status is not false")
    if not block.get("audit_log_path"):
        failures.append("audit_log_path missing")
    return {
        "path": "config/agent_config.yaml",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "runtime_control": block,
    }


def build_report() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(_config_check())
    checks.extend([
        _contains_all(
            "src/safety/runtime_halt.py",
            [
                "CONTROL_VERSION = \"runtime_control_atomic_halt_v1\"",
                "GTOS_HARD_PRODUCTION_HALT.flag",
                "RESEARCH_RUNTIME_HALT.flag",
                "AUTOSTART_DISABLED.flag",
                "no_broker_account_order_deal_position_mutation_performed",
            ],
        ),
        _contains_all(
            "run_agent.py",
            [
                "read_runtime_halt_state",
                "append_runtime_halt_audit",
                "run_agent_start",
                "refusing to start",
            ],
        ),
        _contains_all(
            "src/components/orchestrator.py",
            [
                "RuntimeHaltError",
                "orchestrator_bootstrap",
                "self.mode in {\"demo\", \"live\"}",
            ],
        ),
        _contains_all(
            "src/components/permissions.py",
            [
                "_reject_if_runtime_halted",
                "gate0_runtime_halt",
                "check_permissions",
                "runtime_halt_active",
            ],
        ),
        _contains_all(
            "src/components/execution.py",
            [
                "_enforce_runtime_halt_clear",
                "\"open_trade\"",
                "\"set_limit_intent\"",
                "\"check_limit_fill\"",
                "\"safe_place_order\"",
                "\"close_position\"",
                "\"modify_sl\"",
                "\"modify_tp\"",
                "runtime_halt_blocked_no_order_send",
                "runtime_halt_cancelled_no_order_send",
                "runtime_halt_active_no_sltp_modify",
            ],
        ),
        _contains_all(
            "src/components/pending_limit_lifecycle_logger.py",
            [
                "runtime_halt_cancelled_no_order_send",
                "no_fill_runtime_halt_cancelled",
            ],
        ),
        _contains_all(
            "scripts/watchdog.ps1",
            [
                "$HardProductionHaltFlag",
                "$ResearchHaltFlag",
                "$AutostartDisabledFlag",
                "$ActiveRuntimeHaltFlags",
                "watchdog exiting without launches",
            ],
        ),
        _contains_all(
            "start_all.bat",
            [
                "GTOS_HARD_PRODUCTION_HALT.flag",
                "RESEARCH_RUNTIME_HALT.flag",
                "AUTOSTART_DISABLED.flag",
            ],
        ),
        _contains_all(
            "scripts/watchdog.bat",
            [
                "GTOS_HARD_PRODUCTION_HALT.flag",
                "RESEARCH_RUNTIME_HALT.flag",
                "AUTOSTART_DISABLED.flag",
            ],
        ),
        _contains_all(
            "src/safety/heartbeat_monitor.py",
            [
                "read_runtime_halt_state",
                "heartbeat_monitor_start",
                "heartbeat_flatten_order_send",
                "runtime_halt_active_no_order_send",
                "before lock/MT5 interaction",
            ],
        ),
        _contains_all(
            "src/components/tick_capture.py",
            [
                "read_runtime_halt_state",
                "tick_capture_start",
                "before lock/MT5 interaction",
            ],
        ),
        _contains_all(
            "scripts/displacement_logger.py",
            [
                "read_runtime_halt_state",
                "displacement_logger_start",
                "before MT5 interaction",
            ],
        ),
        _contains_all(
            "scripts/run_shadow_observer.py",
            [
                "read_runtime_halt_state",
                "shadow observer disabled while runtime halt is active",
            ],
        ),
        _contains_all(
            "scripts/run_live_monitoring_maintenance.py",
            [
                "read_runtime_halt_state",
                "live monitoring maintenance disabled while runtime halt is active",
            ],
        ),
        _contains_all(
            "scripts/divergence_weekly_sample.py",
            [
                "read_runtime_halt_state",
                "divergence weekly sampler exiting",
            ],
        ),
        _contains_all(
            "scripts/emergency_close_and_stop_redacted_account.py",
            [
                "GTOS_HARD_PRODUCTION_HALT_FLAG",
                "GTOS_HARD_PRODUCTION_HALT.flag",
            ],
        ),
    ])

    runtime_halt_text = _read("src/safety/runtime_halt.py")
    forbidden_guard_check = {
        "path": "src/safety/runtime_halt.py",
        "status": "pass"
        if all(
            token not in runtime_halt_text
            for token in ("order_send(", "get_positions(", "get_account_balance(")
        )
        else "fail",
        "forbidden_tokens_absent": [
            "order_send(",
            "get_positions(",
            "get_account_balance(",
        ],
    }
    checks.append(forbidden_guard_check)

    failures = [check for check in checks if check.get("status") != "pass"]
    return {
        "schema_version": "runtime_control_atomic_halt_verification_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failures else "fail",
        "source_boundary": "static_source_and_config_parse_no_broker_runtime_access",
        "broker_runtime_change_status": False,
        "required_flags": sorted(REQUIRED_FLAGS),
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", help="Optional path to write the report JSON.")
    args = parser.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
