from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION"
SCHEMA_VERSION = "main_orch48_sl_beyond_ob_logger_activation_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO / "config/agent_config.yaml"
LOGGER_SOURCE = REPO / "src/components/sl_beyond_ob_shadow_logger.py"
VERIFICATION_SOURCE = REPO / "src/components/verification.py"
TEST_SOURCE = REPO / "tests/test_sl_beyond_ob_shadow_logger.py"
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


def config_enabled() -> bool:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    logger_cfg = ((config.get("shadow_loggers") or {}).get("sl_beyond_ob_decisions_logger") or {})
    return bool(logger_cfg.get("enabled"))


def source_contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8", errors="replace")


def build() -> dict[str, Any]:
    enabled = config_enabled()
    logger_has_config_gate = source_contains(LOGGER_SOURCE, "sl_beyond_ob_decisions_logger")
    logger_failure_isolated = source_contains(LOGGER_SOURCE, "except Exception as exc")
    logger_skips_skip_rows = source_contains(LOGGER_SOURCE, 'if status == "SKIP"')
    verification_calls_logger = source_contains(VERIFICATION_SOURCE, "log_sl_beyond_ob_decision(")
    runtime_halt_active = RUNTIME_HALT_FLAG.exists()

    rows = [
        {
            "activation_row_id": "MAIN-ORCH48-SL-BEYOND-OB-ACTIVATION-0001",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "CONFIG_SHADOW_LOGGER_ENABLED",
            "source_path": display_path(CONFIG_PATH),
            "source_sha256": sha256_path(CONFIG_PATH),
            "config_enabled": enabled,
            "action": "ENABLE_OBSERVATION_ONLY_SL_BEYOND_OB_DECISION_CAPTURE",
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-SL-BEYOND-OB-ACTIVATION-0002",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "LOGGER_WIRING_PRESENT",
            "source_path": display_path(VERIFICATION_SOURCE),
            "source_sha256": sha256_path(VERIFICATION_SOURCE),
            "verification_calls_logger": verification_calls_logger,
            "logger_source_path": display_path(LOGGER_SOURCE),
            "logger_source_sha256": sha256_path(LOGGER_SOURCE),
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-SL-BEYOND-OB-ACTIVATION-0003",
            "schema_version": SCHEMA_VERSION,
            "activation_check": "LOGGER_FAILURE_ISOLATION_AND_SCOPE",
            "source_path": display_path(LOGGER_SOURCE),
            "source_sha256": sha256_path(LOGGER_SOURCE),
            "logger_has_config_gate": logger_has_config_gate,
            "logger_failure_isolated": logger_failure_isolated,
            "logger_skips_skip_rows": logger_skips_skip_rows,
            "test_source_path": display_path(TEST_SOURCE),
            "test_source_sha256": sha256_path(TEST_SOURCE),
            "runtime_decision_effect": False,
            "prompt_risk_execution_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        {
            "activation_row_id": "MAIN-ORCH48-SL-BEYOND-OB-ACTIVATION-0004",
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
        "config_path": display_path(CONFIG_PATH),
        "config_sha256": sha256_path(CONFIG_PATH),
        "config_sl_beyond_ob_decisions_logger_enabled": enabled,
        "logger_wiring_present": verification_calls_logger,
        "logger_has_config_gate": logger_has_config_gate,
        "logger_failure_isolated": logger_failure_isolated,
        "logger_skips_skip_rows": logger_skips_skip_rows,
        "runtime_halt_active": runtime_halt_active,
        "activation_rows": len(rows),
        "implementation_effect": {
            "config_shadow_logger_enabled": enabled,
            "future_observation_only_capture_when_runtime_reenabled": enabled,
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
        "config_enabled": enabled,
        "runtime_halt_active": runtime_halt_active,
        "activation_rows": len(rows),
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
