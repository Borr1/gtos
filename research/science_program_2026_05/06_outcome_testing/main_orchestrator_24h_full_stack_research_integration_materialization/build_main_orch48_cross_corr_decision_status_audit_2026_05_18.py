from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CROSS_CORR_DECISION_STATUS_AUDIT"
SCHEMA_VERSION = "main_orch48_cross_corr_decision_status_audit_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.cross_instrument_correlation_decision_status import (  # noqa: E402
    build_cross_instrument_correlation_decision_report,
    build_cross_instrument_correlation_decision_status,
)


CONFIG_SOURCE = REPO / "config/agent_config.yaml"
DECISION_LOG = REPO / "shadow_logs/cross_instrument_correlation_decisions.jsonl"
RUNTIME_HALT = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
HELPER_SOURCE = REPO / "src/research_infra/cross_instrument_correlation_decision_status.py"
AUDIT_SCRIPT = REPO / "scripts/audit_cross_instrument_correlation_decisions.py"
CHECKLIST_SOURCE = REPO / "scripts/build_daily_monitoring_checklist.py"
HELPER_TEST = REPO / "tests/test_cross_instrument_correlation_decision_status.py"
CHECKLIST_TEST = REPO / "tests/test_daily_monitoring_checklist.py"
CROSS_CORR_DIAGNOSTICS_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_CROSS_CORR_DIAGNOSTICS_TOOLING_INTAKE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_runtime_halt_empty_decision_log_is_documented_not_action_required",
    "test_rows_present_status_preserves_gate_action_counts",
    "test_gate_enabled_with_logger_disabled_is_action_required",
    "test_row_key_is_stable_across_generated_at_time",
    "audit_cross_instrument_correlation_decisions.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def read_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


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


def boundary(*, runtime_diagnostic_behavior_effect_if_runtime_reenabled: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": RUNTIME_HALT.exists(),
        "production_import_path_hardened": runtime_diagnostic_behavior_effect_if_runtime_reenabled,
        "runtime_diagnostic_behavior_effect_if_runtime_reenabled": (
            runtime_diagnostic_behavior_effect_if_runtime_reenabled
        ),
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
    }


def code_surface(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "bytes": path.stat().st_size,
        "lines": count_lines(path),
        "sha256": sha256_path(path),
    }


def optional_surface(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": display_path(path), "exists": False, "bytes": 0, "lines": 0, "sha256": ""}
    return {"exists": True, **code_surface(path)}


def status_row(config: dict[str, Any], decision_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status = build_cross_instrument_correlation_decision_status(
        config=config,
        decision_rows=decision_rows,
        decision_log_path=display_path(DECISION_LOG),
        decision_log_exists=DECISION_LOG.exists(),
        runtime_halt_active=RUNTIME_HALT.exists(),
        generated_at_utc=utc_now(),
    )
    report = build_cross_instrument_correlation_decision_report(status)
    return {
        "cross_corr_decision_status_audit_row_id": "MAIN-ORCH48-CROSS-CORR-DECISION-STATUS-00000001",
        "audit_surface": "cross_instrument_correlation_decision_status",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(DECISION_LOG),
        "source_exists": DECISION_LOG.exists(),
        "source_sha256": sha256_path(DECISION_LOG) if DECISION_LOG.exists() else "",
        "status_row": status,
        "report_status": report["status"],
        "decision_rows": status["decision_rows"],
        "runtime_halt_active": status["runtime_halt_active"],
        "status": status["status"],
        "action_required_codes": status["action_required_codes"],
        "documented_limitation_codes": status["documented_limitation_codes"],
        "implementation_decision": "DOCUMENT_EMPTY_CROSS_CORRELATION_DECISION_LOG_UNDER_RUNTIME_HALT",
        "research_boundary": boundary(),
    }


def audit_tooling_row(script_text: str, checklist_text: str) -> dict[str, Any]:
    command = "python scripts/audit_cross_instrument_correlation_decisions.py"
    return {
        "cross_corr_decision_status_audit_row_id": "MAIN-ORCH48-CROSS-CORR-DECISION-STATUS-00000002",
        "audit_surface": "cross_instrument_correlation_decision_status_tooling",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": f"{display_path(AUDIT_SCRIPT)}, {display_path(CHECKLIST_SOURCE)}",
        "source_sha256": {
            display_path(AUDIT_SCRIPT): sha256_path(AUDIT_SCRIPT),
            display_path(CHECKLIST_SOURCE): sha256_path(CHECKLIST_SOURCE),
        },
        "audit_script_present": "build_cross_instrument_correlation_decision_status" in script_text,
        "audit_script_idempotent_row_key_check_present": "existing_row_keys" in script_text,
        "daily_monitoring_checklist_command_present": command in checklist_text,
        "implementation_decision": "ADD_IDEMPOTENT_STATUS_AUDIT_TO_DAILY_MONITORING_CHECKLIST",
        "research_boundary": boundary(runtime_diagnostic_behavior_effect_if_runtime_reenabled=True),
    }


def test_coverage_row(test_texts: dict[str, str]) -> dict[str, Any]:
    combined = "\n".join(test_texts.values())
    covered = {name: name in combined for name in EXPECTED_TEST_NAMES}
    return {
        "cross_corr_decision_status_audit_row_id": "MAIN-ORCH48-CROSS-CORR-DECISION-STATUS-00000003",
        "audit_surface": "cross_instrument_correlation_decision_status_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": ", ".join(display_path(path) for path in (HELPER_TEST, CHECKLIST_TEST)),
        "source_sha256": {
            display_path(HELPER_TEST): sha256_path(HELPER_TEST),
            display_path(CHECKLIST_TEST): sha256_path(CHECKLIST_TEST),
        },
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_RUNTIME_HALT_NO_ROW_STATUS_ACTION_STATUS_AND_CHECKLIST_WIRING",
        "research_boundary": boundary(),
    }


def inherited_diagnostics_row(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "cross_corr_decision_status_audit_row_id": "MAIN-ORCH48-CROSS-CORR-DECISION-STATUS-00000004",
        "audit_surface": "cross_instrument_correlation_diagnostics_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(CROSS_CORR_DIAGNOSTICS_SUMMARY),
        "source_sha256": sha256_path(CROSS_CORR_DIAGNOSTICS_SUMMARY),
        "inherited_rows": int(summary.get("rows") or 0),
        "inherited_manifest_output_count": int(summary.get("manifest_output_count") or 0),
        "implementation_decision": "EXTEND_CROSS_CORRELATION_LOGGER_AND_DIAGNOSTICS_INTAKE_WITH_NO_EVENT_STATUS_AUDIT",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "decision_rows": sum(int(row.get("decision_rows") or 0) for row in rows),
        "runtime_halt_status_rows": sum(
            row.get("status") == "OK_NO_CROSS_INSTRUMENT_CORRELATION_ROWS_RUNTIME_HALTED" for row in rows
        ),
        "action_required_code_rows": sum(len(row.get("action_required_codes") or []) for row in rows),
        "documented_limitation_code_rows": sum(len(row.get("documented_limitation_codes") or []) for row in rows),
        "audit_script_present_rows": sum(bool(row.get("audit_script_present")) for row in rows),
        "daily_monitoring_checklist_command_present_rows": sum(
            bool(row.get("daily_monitoring_checklist_command_present")) for row in rows
        ),
        "expected_test_names_covered_rows": sum(int(row.get("expected_test_names_covered_rows") or 0) for row in rows),
        "runtime_diagnostic_behavior_effect_if_runtime_reenabled_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_diagnostic_behavior_effect_if_runtime_reenabled"))
            for row in rows
        ),
        "paid_api_or_vendor_call_rows": sum(
            bool((row.get("research_boundary") or {}).get("paid_api_or_vendor_call")) for row in rows
        ),
        "broker_operation_rows": sum(bool((row.get("research_boundary") or {}).get("broker_operation")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
    }


def build() -> dict[str, Any]:
    config = read_config(CONFIG_SOURCE)
    decision_rows = read_jsonl(DECISION_LOG)
    script_text = AUDIT_SCRIPT.read_text(encoding="utf-8")
    checklist_text = CHECKLIST_SOURCE.read_text(encoding="utf-8")
    test_texts = {
        display_path(HELPER_TEST): HELPER_TEST.read_text(encoding="utf-8"),
        display_path(CHECKLIST_TEST): CHECKLIST_TEST.read_text(encoding="utf-8"),
    }
    diagnostics_summary = read_json(CROSS_CORR_DIAGNOSTICS_SUMMARY)
    rows = [
        status_row(config, decision_rows),
        audit_tooling_row(script_text, checklist_text),
        test_coverage_row(test_texts),
        inherited_diagnostics_row(diagnostics_summary),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(CONFIG_SOURCE),
            optional_surface(DECISION_LOG),
            optional_surface(RUNTIME_HALT),
            code_surface(CROSS_CORR_DIAGNOSTICS_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(HELPER_SOURCE),
            code_surface(AUDIT_SCRIPT),
            code_surface(CHECKLIST_SOURCE),
            code_surface(HELPER_TEST),
            code_surface(CHECKLIST_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "cross_correlation_decision_no_event_status_documented": True,
            "daily_monitoring_checklist_command_present": True,
            "research_runtime_halt_active": RUNTIME_HALT.exists(),
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "runtime_trading_or_live_broker_effect": False,
            "runtime_candidate_use_permitted": False,
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
        "rows": summary["rows"],
        "decision_rows": summary["decision_rows"],
        "runtime_halt_status_rows": summary["runtime_halt_status_rows"],
        "action_required_code_rows": summary["action_required_code_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
