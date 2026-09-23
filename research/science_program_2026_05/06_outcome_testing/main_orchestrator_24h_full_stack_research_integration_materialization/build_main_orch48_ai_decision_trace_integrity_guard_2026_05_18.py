from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD"
SCHEMA_VERSION = "main_orch48_ai_decision_trace_integrity_guard_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.verify_shadow_log_integrity import (  # noqa: E402
    AI_DECISION_TRACE_ALLOWED_STATUSES,
    AI_DECISION_TRACE_FORBIDDEN_TEXT_FIELDS,
    EXPECTED_WAITING_FILES,
    JSONL_SPECS,
)


VERIFY_SCRIPT = REPO / "scripts/verify_shadow_log_integrity.py"
VERIFY_TEST = REPO / "tests/test_verify_shadow_log_integrity.py"
TRACE_LOG = REPO / "shadow_logs/ai_decision_trace.jsonl"
TRACE_PROVENANCE_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"

EXPECTED_TEST_NAMES = [
    "test_ai_decision_trace_schema_registered",
    "test_ai_decision_trace_integrity_accepts_hash_only_rows",
    "test_ai_decision_trace_integrity_flags_full_text_or_runtime_flags",
    "test_ai_decision_trace_missing_file_is_documented_waiting_lane",
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


def boundary() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "research_runtime_halt_active": (REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag").exists(),
        "trading_decision_behavior_changed": False,
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


def schema_registration_row() -> dict[str, Any]:
    spec = JSONL_SPECS.get("ai_decision_trace.jsonl")
    required = tuple(spec.required_fields) if spec else ()
    return {
        "ai_decision_trace_integrity_guard_row_id": "MAIN-ORCH48-AI-TRACE-INTEGRITY-GUARD-00000001",
        "audit_surface": "ai_decision_trace_schema_registration",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(VERIFY_SCRIPT),
        "source_sha256": sha256_path(VERIFY_SCRIPT),
        "schema_registered": spec is not None,
        "expected_schema": getattr(spec, "expected_schema", None),
        "required_fields": required,
        "required_field_count": len(required),
        "unique_key": tuple(spec.unique_key) if spec else (),
        "implementation_decision": "REGISTER_AI_DECISION_TRACE_JSONL_WITH_SHADOW_INTEGRITY",
        "research_boundary": boundary(),
    }


def validation_guard_row(script_text: str) -> dict[str, Any]:
    forbidden_flags = [
        "runtime_trading_or_live_broker_effect",
        "broker_operation",
        "paid_api_or_vendor_call_added_by_logger",
        "runtime_candidate_use_permitted",
        "stores_full_prompt_or_response_text",
    ]
    return {
        "ai_decision_trace_integrity_guard_row_id": "MAIN-ORCH48-AI-TRACE-INTEGRITY-GUARD-00000002",
        "audit_surface": "ai_decision_trace_hash_only_validation_guard",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(VERIFY_SCRIPT),
        "source_sha256": sha256_path(VERIFY_SCRIPT),
        "allowed_response_status_count": len(AI_DECISION_TRACE_ALLOWED_STATUSES),
        "forbidden_text_field_count": len(AI_DECISION_TRACE_FORBIDDEN_TEXT_FIELDS),
        "prompt_hash_validation_present": "AI_DECISION_TRACE_PROMPT_HASH_INVALID" in script_text,
        "full_text_field_guard_present": "AI_DECISION_TRACE_FULL_TEXT_FIELD_PRESENT" in script_text,
        "boundary_flag_guard_present": "AI_DECISION_TRACE_FORBIDDEN_BOUNDARY_FLAG" in script_text,
        "forbidden_boundary_flags": forbidden_flags,
        "implementation_decision": "FAIL_SCHEMA_ROWS_THAT_STORE_FULL_TEXT_OR_RUNTIME_EFFECT_FLAGS",
        "research_boundary": boundary(),
    }


def waiting_lane_row() -> dict[str, Any]:
    trace_exists = TRACE_LOG.exists() and TRACE_LOG.stat().st_size > 0
    return {
        "ai_decision_trace_integrity_guard_row_id": "MAIN-ORCH48-AI-TRACE-INTEGRITY-GUARD-00000003",
        "audit_surface": "ai_decision_trace_runtime_halt_waiting_lane",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(VERIFY_SCRIPT),
        "source_sha256": sha256_path(VERIFY_SCRIPT),
        "trace_log_path": display_path(TRACE_LOG),
        "trace_log_exists_with_rows": trace_exists,
        "waiting_lane_registered": "ai_decision_trace.jsonl" in EXPECTED_WAITING_FILES,
        "waiting_lane_reason": EXPECTED_WAITING_FILES.get("ai_decision_trace.jsonl"),
        "runtime_halt_active": boundary()["research_runtime_halt_active"],
        "implementation_decision": "DOCUMENT_NO_TRACE_ROWS_WHILE_RUNTIME_HALTED_OR_BEFORE_FIRST_POST_PATCH_AI_CALL",
        "research_boundary": boundary(),
    }


def test_coverage_row(test_text: str) -> dict[str, Any]:
    covered = {name: name in test_text for name in EXPECTED_TEST_NAMES}
    return {
        "ai_decision_trace_integrity_guard_row_id": "MAIN-ORCH48-AI-TRACE-INTEGRITY-GUARD-00000004",
        "audit_surface": "ai_decision_trace_integrity_test_coverage",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(VERIFY_TEST),
        "source_sha256": sha256_path(VERIFY_TEST),
        "expected_test_names": EXPECTED_TEST_NAMES,
        "expected_test_name_coverage": covered,
        "expected_test_names_covered_rows": sum(covered.values()),
        "implementation_decision": "TEST_SCHEMA_REGISTRATION_HASH_ONLY_GUARDS_AND_WAITING_LANE",
        "research_boundary": boundary(),
    }


def inheritance_row(trace_summary: dict[str, Any]) -> dict[str, Any]:
    effect = trace_summary.get("implementation_effect") or {}
    return {
        "ai_decision_trace_integrity_guard_row_id": "MAIN-ORCH48-AI-TRACE-INTEGRITY-GUARD-00000005",
        "audit_surface": "ai_decision_trace_provenance_inheritance",
        "schema_version": SCHEMA_VERSION,
        "source_artifact": display_path(TRACE_PROVENANCE_SUMMARY),
        "source_sha256": sha256_path(TRACE_PROVENANCE_SUMMARY),
        "inherited_trace_logger_enabled": bool(effect.get("ai_decision_trace_logger_enabled")),
        "inherited_hash_only_prompt_response_provenance": bool(effect.get("hash_only_prompt_response_provenance")),
        "inherited_trading_decision_behavior_changed": bool(effect.get("trading_decision_behavior_changed")),
        "implementation_decision": "CONSUME_TRACE_PROVENANCE_PLATE_INTO_SHADOW_INTEGRITY_GUARD",
        "research_boundary": boundary(),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(row["audit_surface"] for row in rows).items())),
        "schema_registered_rows": sum(bool(row.get("schema_registered")) for row in rows),
        "required_field_count": sum(int(row.get("required_field_count") or 0) for row in rows),
        "prompt_hash_validation_present_rows": sum(bool(row.get("prompt_hash_validation_present")) for row in rows),
        "full_text_field_guard_present_rows": sum(bool(row.get("full_text_field_guard_present")) for row in rows),
        "boundary_flag_guard_present_rows": sum(bool(row.get("boundary_flag_guard_present")) for row in rows),
        "waiting_lane_registered_rows": sum(bool(row.get("waiting_lane_registered")) for row in rows),
        "trace_log_exists_with_rows": sum(bool(row.get("trace_log_exists_with_rows")) for row in rows),
        "runtime_halt_active_rows": sum(bool(row.get("runtime_halt_active")) for row in rows),
        "expected_test_names_covered_rows": sum(int(row.get("expected_test_names_covered_rows") or 0) for row in rows),
        "inherited_trace_logger_enabled_rows": sum(bool(row.get("inherited_trace_logger_enabled")) for row in rows),
        "inherited_hash_only_prompt_response_provenance_rows": sum(
            bool(row.get("inherited_hash_only_prompt_response_provenance")) for row in rows
        ),
        "trading_decision_behavior_changed_rows": sum(
            bool((row.get("research_boundary") or {}).get("trading_decision_behavior_changed")) for row in rows
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
    script_text = VERIFY_SCRIPT.read_text(encoding="utf-8")
    test_text = VERIFY_TEST.read_text(encoding="utf-8")
    rows = [
        schema_registration_row(),
        validation_guard_row(script_text),
        waiting_lane_row(),
        test_coverage_row(test_text),
        inheritance_row(read_json(TRACE_PROVENANCE_SUMMARY)),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "input_sources": [
            code_surface(TRACE_PROVENANCE_SUMMARY),
        ],
        "code_surfaces": [
            code_surface(VERIFY_SCRIPT),
            code_surface(VERIFY_TEST),
            code_surface(Path(__file__)),
        ],
        **summarize(rows),
        "implementation_effect": {
            "ai_decision_trace_integrity_guard_registered": True,
            "hash_only_text_storage_guard": True,
            "runtime_halt_waiting_lane_documented": True,
            "trading_decision_behavior_changed": False,
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
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
        "schema_registered_rows": summary["schema_registered_rows"],
        "waiting_lane_registered_rows": summary["waiting_lane_registered_rows"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
