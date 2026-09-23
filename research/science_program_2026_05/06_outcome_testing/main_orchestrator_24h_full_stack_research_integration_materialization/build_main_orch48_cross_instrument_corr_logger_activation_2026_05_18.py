from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CROSS_INSTRUMENT_CORR_LOGGER_ACTIVATION"
SCHEMA_VERSION = "main_orch48_cross_instrument_corr_logger_activation_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO / "config/agent_config.yaml"
LOGGER_SOURCE = REPO / "src/components/cross_instrument_correlation_gate_logger.py"
GATE_SOURCE = REPO / "src/components/cross_instrument_correlation_gate.py"
PERMISSIONS_SOURCE = REPO / "src/components/permissions.py"
ORCHESTRATOR_SOURCE = REPO / "src/components/orchestrator.py"
TEST_SOURCE = REPO / "tests/test_cross_instrument_correlation_gate.py"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def source_contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8", errors="replace")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def config_logger_enabled() -> bool:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    logger_cfg = ((config.get("shadow_loggers") or {}).get("cross_instrument_correlation_decisions_logger") or {})
    return bool(logger_cfg.get("enabled"))


def build() -> dict[str, Any]:
    config_enabled = config_logger_enabled()
    gate_calls_logger = source_contains(GATE_SOURCE, "log_cross_instrument_correlation_decision(")
    logger_config_gated = source_contains(LOGGER_SOURCE, "cross_instrument_correlation_decisions_logger")
    logger_failure_isolated = source_contains(LOGGER_SOURCE, "except Exception as exc")
    permissions_context_present = source_contains(PERMISSIONS_SOURCE, "permissions_gate3_5_reject_check")
    orchestrator_context_present = source_contains(ORCHESTRATOR_SOURCE, "orchestrator_sizing_risk_adjustment")
    tests_cover_enabled_write = source_contains(TEST_SOURCE, "test_evaluate_logs_when_shadow_logger_enabled")
    tests_cover_disabled_no_write = source_contains(TEST_SOURCE, "test_evaluate_does_not_log_without_explicit_logger_enable")
    runtime_halt_active = RUNTIME_HALT_FLAG.exists()

    rows = [
        {
            "activation_row_id": "MAIN-ORCH48-CROSS-CORR-LOGGER-ACTIVATION-0001",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "CONFIG_SHADOW_LOGGER_ENABLED",
            "source_path": display_path(CONFIG_PATH),
            "source_sha256": sha256_path(CONFIG_PATH),
            "config_enabled": config_enabled,
            "action": "ENABLE_OBSERVATION_ONLY_CROSS_INSTRUMENT_CORRELATION_DECISION_CAPTURE",
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-CROSS-CORR-LOGGER-ACTIVATION-0002",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "LOGGER_SOURCE_AND_GATE_WIRING",
            "source_path": display_path(LOGGER_SOURCE),
            "source_sha256": sha256_path(LOGGER_SOURCE),
            "gate_source_path": display_path(GATE_SOURCE),
            "gate_source_sha256": sha256_path(GATE_SOURCE),
            "gate_calls_logger": gate_calls_logger,
            "logger_config_gated": logger_config_gated,
            "logger_failure_isolated": logger_failure_isolated,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-CROSS-CORR-LOGGER-ACTIVATION-0003",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "CALL_SITE_CONTEXT_AND_TEST_COVERAGE",
            "permissions_source_path": display_path(PERMISSIONS_SOURCE),
            "permissions_source_sha256": sha256_path(PERMISSIONS_SOURCE),
            "orchestrator_source_path": display_path(ORCHESTRATOR_SOURCE),
            "orchestrator_source_sha256": sha256_path(ORCHESTRATOR_SOURCE),
            "test_source_path": display_path(TEST_SOURCE),
            "test_source_sha256": sha256_path(TEST_SOURCE),
            "permissions_context_present": permissions_context_present,
            "orchestrator_context_present": orchestrator_context_present,
            "tests_cover_enabled_write": tests_cover_enabled_write,
            "tests_cover_disabled_no_write": tests_cover_disabled_no_write,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-CROSS-CORR-LOGGER-ACTIVATION-0004",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "SESSION_57_RUNTIME_HALT_BOUNDARY",
            "source_path": display_path(RUNTIME_HALT_FLAG),
            "runtime_halt_active": runtime_halt_active,
            "live_runtime_restart_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
        },
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "activation_rows": len(rows),
        "config_cross_instrument_correlation_decisions_logger_enabled": config_enabled,
        "gate_calls_logger": gate_calls_logger,
        "logger_config_gated": logger_config_gated,
        "logger_failure_isolated": logger_failure_isolated,
        "permissions_context_present": permissions_context_present,
        "orchestrator_context_present": orchestrator_context_present,
        "tests_cover_enabled_write": tests_cover_enabled_write,
        "tests_cover_disabled_no_write": tests_cover_disabled_no_write,
        "runtime_halt_active": runtime_halt_active,
        "implementation_effect": {
            "config_shadow_logger_enabled": config_enabled,
            "future_observation_only_capture_when_runtime_reenabled": config_enabled,
            "current_runtime_restart_now": False,
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "activation_rows": len(rows),
        "config_enabled": config_enabled,
        "runtime_halt_active": runtime_halt_active,
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
