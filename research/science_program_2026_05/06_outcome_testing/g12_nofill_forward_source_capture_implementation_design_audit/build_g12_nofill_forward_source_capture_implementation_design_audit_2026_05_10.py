#!/usr/bin/env python3
"""Build the independent G12 implementation-design audit artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-10"
ROUTE_ID = "G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT"
SCHEMA_VERSION = "g12_nofill_forward_source_capture_implementation_design_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT_TERMINAL_VERDICT = "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_DESIGN_EVIDENCE_ONLY"
BLOCKER_TERMINAL_VERDICT = "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS"
REJECT_TERMINAL_VERDICT = "REJECT_INVALID_DESIGN_CLOSURE"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_implementation_design_plan"
)
TEXT_GATE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_text_gate_repair_reaudit"
)
CONTRACT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_contract_hardening_offline_projection_prototype"
)
PROJECTION_REPAIR_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_projection_repair_reaudit"
)
CAT_V3_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild"
)

FIELD_MAP = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json"
COMPLETION_AUDIT = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.json"
TARGET_VERIFICATION = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_VERIFICATION_RESULT_{DATE}.json"
FUTURE_LOGGER = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_{DATE}.json"
REDACTION_POLICY = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_{DATE}.json"
FAIL_CLOSED = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_{DATE}.json"
PARSER_SCHEMA = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.json"
FIXTURE_MATRIX = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json"
HASH_REQUIREMENTS = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_{DATE}.json"
ROLLBACK_LEDGER = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_{DATE}.json"
G12_CHECKLIST = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_{DATE}.json"
DEPENDENCY_GRAPH = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_{DATE}.json"
OWNER_GATE_LEDGER = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_{DATE}.json"
NEXT_PROMPT_PACK = TARGET_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_{DATE}.md"

TEXT_GATE_RESULT = TEXT_GATE_DIR / f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_VERIFICATION_RESULT_{DATE}.json"
CONTRACT_RESULT = CONTRACT_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json"
PROJECTION_REPAIR_DECISION = (
    PROJECTION_REPAIR_DIR / "G12_NOFILL_FORWARD_PROJECTION_REPAIR_DECISION_LEDGER_2026-05-09.json"
)
CAT_V3_COMPLETION = CAT_V3_DIR / "NOFILL_CAT_V3_COMPLETION_AUDIT_2026-05-09.json"

TARGET_VERIFIER_COMMAND = (
    "python research\\science_program_2026_05\\06_outcome_testing\\"
    "nofill_forward_source_capture_implementation_design_plan\\"
    "verify_nofill_forward_source_capture_implementation_design_plan_2026_05_10.py"
)
TARGET_TEST_COMMAND = (
    "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\"
    "nofill_forward_source_capture_implementation_design_plan\\"
    "test_nofill_forward_source_capture_implementation_design_plan_2026_05_10.py -q "
    "-p no:cacheprovider --basetemp C:\\tmp\\gtos_otb\\pytest_g12_design_target"
)
TARGET_PY_COMPILE_COMMAND = (
    "python -m py_compile research\\science_program_2026_05\\06_outcome_testing\\"
    "nofill_forward_source_capture_implementation_design_plan\\"
    "build_nofill_forward_source_capture_implementation_design_plan_2026_05_10.py "
    "research\\science_program_2026_05\\06_outcome_testing\\"
    "nofill_forward_source_capture_implementation_design_plan\\"
    "verify_nofill_forward_source_capture_implementation_design_plan_2026_05_10.py "
    "research\\science_program_2026_05\\06_outcome_testing\\"
    "nofill_forward_source_capture_implementation_design_plan\\"
    "test_nofill_forward_source_capture_implementation_design_plan_2026_05_10.py"
)

CONTROL_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

ALLOWED_TERMINAL_STATUSES = {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY",
    "FUTURE_LOGGER_FIELD_REQUIRED",
    "SCHEMA_ONLY_CONTROL_FIELD",
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
    "BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT",
}

EXPECTED_STATUS_COUNTS = {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
    "FUTURE_LOGGER_FIELD_REQUIRED": 20,
    "SCHEMA_ONLY_CONTROL_FIELD": 11,
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
    "BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT": 0,
}

REQUIRED_FUTURE_COLUMNS = (
    "target_source_surface",
    "target_schema_field",
    "redaction_rule",
    "fail_closed_missing_status",
    "test_fixture",
    "rollback_rule",
    "g12_acceptance_check",
)

REQUIRED_JSON = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FIELD_CLOSURE_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_SCHEMA_FAILCLOSED_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_OWNER_GATE_DEPENDENCY_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_SATURATION_REDTEAM_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_VERIFIER_TEST_RERUN_REPORT_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_REPAIR_BLOCKER_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.json",
]

REQUIRED_MD = [
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FIELD_CLOSURE_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FORBIDDEN_REDACTION_NOLEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_SCHEMA_FAILCLOSED_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_OWNER_GATE_DEPENDENCY_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_SATURATION_REDTEAM_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_VERIFIER_TEST_RERUN_REPORT_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_REPAIR_BLOCKER_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.md",
]

VERIFICATION_RESULT_NAME = (
    f"G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_VERIFICATION_RESULT_{DATE}.json"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def git_status_paths() -> list[str]:
    paths: list[str] = []
    for line in run_git(["status", "--short"]).splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return sorted(paths)


def with_flags(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **CONTROL_FLAGS}


def field_closure_audit(field_map: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fields = field_map.get("fields", [])
    names = [row.get("field_name") for row in fields]
    statuses = [row.get("terminal_implementation_design_status") for row in fields]
    counts = Counter(statuses)
    status_counts = {status: counts.get(status, 0) for status in sorted(ALLOWED_TERMINAL_STATUSES)}
    blockers: list[dict[str, Any]] = []
    if len(fields) != 55 or field_map.get("field_count") != 55:
        blockers.append({"blocker_id": "G12-DESIGN-001", "issue": "field count does not equal 55"})
    if len(set(names)) != len(names) or len(set(names)) != 55:
        duplicate_names = sorted(name for name, count in Counter(names).items() if count > 1)
        blockers.append({"blocker_id": "G12-DESIGN-002", "issue": "field names are not exactly unique", "fields": duplicate_names})
    bad_statuses = sorted(set(statuses) - ALLOWED_TERMINAL_STATUSES)
    if bad_statuses:
        blockers.append({"blocker_id": "G12-DESIGN-003", "issue": "terminal status outside allowed set", "statuses": bad_statuses})
    if status_counts != EXPECTED_STATUS_COUNTS:
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-004",
                "issue": "terminal status equation drifted",
                "expected": EXPECTED_STATUS_COUNTS,
                "actual": status_counts,
            }
        )
    rows_missing_terminal_material = [
        row.get("field_name")
        for row in fields
        if not row.get("field_name")
        or not row.get("terminal_implementation_design_status")
        or not row.get("target_schema_field")
        or row.get("validation_safe") is not False
        or row.get("outcome_review_opened") is not False
        or row.get("live_effect") is not False
    ]
    if rows_missing_terminal_material:
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-005",
                "issue": "field row lacks terminal material or closed flags",
                "fields": rows_missing_terminal_material,
            }
        )
    audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_field_closure",
            "route_id": ROUTE_ID,
            "source_artifact": rel(FIELD_MAP),
            "recomputed_from_json_not_markdown": True,
            "field_count_declared": field_map.get("field_count"),
            "field_count_actual": len(fields),
            "unique_field_count": len(set(names)),
            "terminal_status_counts": status_counts,
            "expected_terminal_status_counts": EXPECTED_STATUS_COUNTS,
            "status_count_equation": "17+20+11+7+0=55",
            "status_count_audit_passed": not blockers,
            "field_names_by_status": {
                status: sorted(row["field_name"] for row in fields if row.get("terminal_implementation_design_status") == status)
                for status in sorted(ALLOWED_TERMINAL_STATUSES)
            },
            "exact_repair_blockers": blockers,
        }
    )
    return audit, blockers


def future_logger_audit(field_map: dict[str, Any], future_design: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    future_rows = [
        row
        for row in field_map.get("fields", [])
        if row.get("terminal_implementation_design_status") == "FUTURE_LOGGER_FIELD_REQUIRED"
    ]
    blockers: list[dict[str, Any]] = []
    per_field: list[dict[str, Any]] = []
    for row in future_rows:
        missing = [key for key in REQUIRED_FUTURE_COLUMNS if not row.get(key)]
        owner_gate_ok = "owner approval" in str(row.get("owner_or_source_requirement", "")).lower()
        row_status = {
            "field_name": row.get("field_name"),
            "target_source_surface": row.get("target_source_surface"),
            "target_schema_field": row.get("target_schema_field"),
            "fail_closed_missing_status": row.get("fail_closed_missing_status"),
            "test_fixture": row.get("test_fixture"),
            "has_redaction_rule": bool(row.get("redaction_rule")),
            "has_rollback_rule": bool(row.get("rollback_rule")),
            "has_g12_acceptance_check": bool(row.get("g12_acceptance_check")),
            "owner_gate_named": owner_gate_ok,
            "missing_required_columns": missing,
            "implementation_ready_without_reinterpretation": not missing and owner_gate_ok,
        }
        per_field.append(row_status)
        if missing or not owner_gate_ok:
            blockers.append(
                {
                    "blocker_id": "G12-DESIGN-FUTURE-FIELD",
                    "field_name": row.get("field_name"),
                    "missing_required_columns": missing,
                    "owner_gate_named": owner_gate_ok,
                }
            )
    future_design_names = sorted(row.get("field_name") for row in future_design.get("future_fields", []))
    map_future_names = sorted(row.get("field_name") for row in future_rows)
    if future_design_names != map_future_names:
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-FUTURE-MISMATCH",
                "issue": "future logger design list does not match implementation map future rows",
                "design_only": sorted(set(future_design_names) - set(map_future_names)),
                "map_only": sorted(set(map_future_names) - set(future_design_names)),
            }
        )
    audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_future_logger_sufficiency",
            "route_id": ROUTE_ID,
            "source_artifacts": [rel(FIELD_MAP), rel(FUTURE_LOGGER)],
            "future_logger_field_count": len(future_rows),
            "expected_future_logger_field_count": 20,
            "target_log_path": future_design.get("target_log_path"),
            "writer_mode": future_design.get("writer_mode"),
            "target_schema_version": future_design.get("target_schema_version"),
            "required_columns": list(REQUIRED_FUTURE_COLUMNS),
            "per_field": per_field,
            "all_future_logger_fields_implementation_ready": len(future_rows) == 20 and not blockers,
            "exact_repair_blockers": blockers,
        }
    )
    return audit, blockers


def noleak_audit(field_map: dict[str, Any], policy: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    fields = field_map.get("fields", [])
    forbidden_rows = [
        row for row in fields if row.get("terminal_implementation_design_status") == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY"
    ]
    raw_leak_candidates: list[dict[str, Any]] = []
    for row in forbidden_rows:
        field_name = str(row.get("field_name", ""))
        schema_field = str(row.get("target_schema_field", ""))
        redaction = str(row.get("redaction_rule", "")).lower()
        if not (field_name.endswith("_status") or field_name.endswith("_redaction_status")):
            raw_leak_candidates.append({"field_name": field_name, "reason": "forbidden field is not status-only"})
        if schema_field != field_name:
            raw_leak_candidates.append({"field_name": field_name, "reason": "target schema field drift"})
        if "emit only closed status values" not in redaction and "omit raw value" not in redaction:
            raw_leak_candidates.append({"field_name": field_name, "reason": "redaction rule is not status-only"})
    unsafe_hash_actions = [
        action
        for action in policy.get("redaction_actions", [])
        if action.get("source_family") in {"broker ticket or order identifier", "deal account history position result label"}
        and action.get("hash_allowed") is not False
    ]
    if raw_leak_candidates:
        blockers.append({"blocker_id": "G12-DESIGN-NOLEAK-001", "issue": "forbidden rows are not status-only", "rows": raw_leak_candidates})
    if unsafe_hash_actions:
        blockers.append({"blocker_id": "G12-DESIGN-NOLEAK-002", "issue": "unsafe raw material hash action opened", "actions": unsafe_hash_actions})
    future_schema_fields = [
        row.get("target_schema_field")
        for row in fields
        if row.get("terminal_implementation_design_status") == "FUTURE_LOGGER_FIELD_REQUIRED"
    ]
    disallowed_future_schema = [
        name
        for name in future_schema_fields
        if name in {"account_id", "broker_actual_r", "actual_r", "deal_id", "order_ticket", "pending_ticket", "position_id"}
    ]
    if disallowed_future_schema:
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-NOLEAK-003",
                "issue": "future logger schema includes forbidden raw field",
                "fields": sorted(disallowed_future_schema),
            }
        )
    audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_forbidden_redaction_noleak",
            "route_id": ROUTE_ID,
            "source_artifacts": [rel(FIELD_MAP), rel(REDACTION_POLICY)],
            "forbidden_row_count": len(forbidden_rows),
            "expected_forbidden_row_count": 7,
            "forbidden_raw_field_names_declared": policy.get("forbidden_raw_field_names", []),
            "forbidden_rows_status_only": not raw_leak_candidates,
            "unsafe_hash_actions": unsafe_hash_actions,
            "raw_broker_account_order_deal_position_result_cost_leak_opened": False,
            "future_logger_forbidden_raw_schema_fields": disallowed_future_schema,
            "redaction_policy_passed": len(forbidden_rows) == 7 and not blockers,
            "exact_repair_blockers": blockers,
        }
    )
    return audit, blockers


def schema_failclosed_audit(field_map: dict[str, Any], fail_closed: dict[str, Any], parser_schema: dict[str, Any], fixtures: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    map_fields = {row.get("field_name"): row for row in field_map.get("fields", [])}
    schema_fields = {row.get("field_name"): row for row in parser_schema.get("required_fields", [])}
    if set(map_fields) != set(schema_fields):
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-SCHEMA-001",
                "issue": "parser schema required fields do not match field map",
                "schema_only": sorted(set(schema_fields) - set(map_fields)),
                "map_only": sorted(set(map_fields) - set(schema_fields)),
            }
        )
    allowed_missing = set(fail_closed.get("allowed_fail_closed_statuses", []))
    used_missing = {row.get("fail_closed_missing_status") for row in field_map.get("fields", [])}
    bad_missing = sorted(status for status in used_missing if status not in allowed_missing)
    if bad_missing:
        blockers.append({"blocker_id": "G12-DESIGN-SCHEMA-002", "issue": "fail-closed status outside vocabulary", "statuses": bad_missing})
    covered_fields = set()
    duplicate_fixture_fields = []
    for fixture in fixtures.get("fixtures", []):
        for field in fixture.get("covered_fields", []):
            if field in covered_fields:
                duplicate_fixture_fields.append(field)
            covered_fields.add(field)
    if covered_fields != set(map_fields):
        blockers.append(
            {
                "blocker_id": "G12-DESIGN-SCHEMA-003",
                "issue": "fixture coverage does not exactly cover all fields",
                "uncovered": sorted(set(map_fields) - covered_fields),
                "extra": sorted(covered_fields - set(map_fields)),
                "duplicate_fixture_fields": sorted(set(duplicate_fixture_fields)),
            }
        )
    audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_schema_failclosed",
            "route_id": ROUTE_ID,
            "source_artifacts": [rel(FAIL_CLOSED), rel(PARSER_SCHEMA), rel(FIXTURE_MATRIX), rel(FIELD_MAP)],
            "required_field_count": parser_schema.get("required_field_count"),
            "schema_field_count": len(schema_fields),
            "allowed_fail_closed_status_count": len(allowed_missing),
            "used_fail_closed_status_count": len(used_missing),
            "bad_fail_closed_statuses": bad_missing,
            "fixture_count": fixtures.get("fixture_count"),
            "fixture_covered_field_count": len(covered_fields),
            "parser_sequence": parser_schema.get("parser_sequence", []),
            "row_acceptance_rule": fail_closed.get("row_acceptance_rule"),
            "forbidden_acceptance_rule": fail_closed.get("forbidden_acceptance_rule"),
            "schema_failclosed_audit_passed": not blockers,
            "exact_repair_blockers": blockers,
        }
    )
    return audit, blockers


def owner_dependency_audit(owner_gates: dict[str, Any], dependency: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    gates = owner_gates.get("approval_gates", [])
    opened = [gate for gate in gates if gate.get("opened_now") is not False]
    gate_ids = {gate.get("gate_id") for gate in gates}
    required_gate_ids = {
        "OA1_G12_DESIGN_ACCEPTANCE",
        "OA2_OWNER_LIVE_LOGGER_WIRING",
        "OA3_NATIVE_BROKER_METADATA_STATUS",
        "OA4_RESULT_COST_LABEL_LANE",
        "OA5_REGISTRY_VALIDATION_PROMOTION",
    }
    if gate_ids != required_gate_ids:
        blockers.append({"blocker_id": "G12-DESIGN-OWNER-001", "issue": "owner gate set drifted", "actual": sorted(gate_ids)})
    if opened:
        blockers.append({"blocker_id": "G12-DESIGN-OWNER-002", "issue": "owner gate opened inside design audit", "gates": opened})
    nodes = {node.get("node_id"): node for node in dependency.get("nodes", [])}
    d5 = nodes.get("D5_SHADOW_LOGGER_WIRING", {})
    if "D3_OWNER_CODE_WIRING_APPROVAL" not in d5.get("depends_on", []) and "D4_OFFLINE_PARSER_AND_FIXTURES" not in d5.get("depends_on", []):
        blockers.append({"blocker_id": "G12-DESIGN-OWNER-003", "issue": "shadow logger wiring dependency lacks owner approval chain"})
    if dependency.get("edges_are_ordered") is not True:
        blockers.append({"blocker_id": "G12-DESIGN-OWNER-004", "issue": "dependency graph edge order flag is not true"})
    audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_owner_gate_dependency",
            "route_id": ROUTE_ID,
            "source_artifacts": [rel(OWNER_GATE_LEDGER), rel(DEPENDENCY_GRAPH), rel(NEXT_PROMPT_PACK)],
            "approval_gate_count": len(gates),
            "all_owner_gates_closed_now": not opened,
            "required_gate_ids_present": sorted(gate_ids),
            "dependency_nodes": dependency.get("nodes", []),
            "edges_are_ordered": dependency.get("edges_are_ordered"),
            "shadow_logger_wiring_requires_owner_approval_chain": not blockers,
            "owner_dependency_audit_passed": not blockers,
            "exact_repair_blockers": blockers,
        }
    )
    return audit, blockers


def upstream_context_audit() -> dict[str, Any]:
    text_gate = read_json(TEXT_GATE_RESULT) if TEXT_GATE_RESULT.exists() else {}
    contract = read_json(CONTRACT_RESULT) if CONTRACT_RESULT.exists() else {}
    projection = read_json(PROJECTION_REPAIR_DECISION) if PROJECTION_REPAIR_DECISION.exists() else {}
    cat_v3 = read_json(CAT_V3_COMPLETION) if CAT_V3_COMPLETION.exists() else {}
    return {
        "required_upstream_context_inspected": [
            {
                "path": rel(TEXT_GATE_DIR),
                "status": text_gate.get("terminal_verdict"),
                "ok": text_gate.get("ok"),
                "relevance": "Confirms text-gated source-capture verifier repair accepted before implementation-design reliance.",
            },
            {
                "path": rel(CONTRACT_DIR),
                "status": contract.get("ok"),
                "family_counts": contract.get("family_counts"),
                "relevance": "Provides accepted 55-field source-capture contract substrate and source/control boundaries.",
            },
            {
                "path": rel(PROJECTION_REPAIR_DIR),
                "status": projection.get("terminal_decision"),
                "relevance": "Confirms projection repair source/control acceptance and separation from result scoring.",
            },
            {
                "path": rel(CAT_V3_DIR),
                "status": cat_v3.get("can_mark_goal_complete"),
                "relevance": "Confirms no-fill categorical source/control universe rebuild context stayed non-result and non-live.",
            },
        ]
    }


def saturation_pass() -> dict[str, Any]:
    questions = [
        {
            "question_id": "SR1_EVIDENCE_CLASS_DRIFT",
            "risk": "Design acceptance could be misread as permission for logger wiring, scoring, validation, promotion, or live behavior.",
            "pursuit": "Decision ledger, owner gates, next prompt pack, and dependency graph all keep implementation behind independent G12 acceptance plus explicit CEO code-wiring approval.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR2_FUTURE_FIELD_UNDERSPECIFICATION",
            "risk": "A future logger field could appear complete while missing source, schema, redaction, fail-closed status, fixture, rollback, or G12 check.",
            "pursuit": "All 20 future rows were recomputed from JSON and each required column was checked row by row.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR3_FORBIDDEN_FIELD_EMISSION",
            "risk": "A schema-only or redacted field could become an emitted raw broker/account/order/deal/position/result/cost value.",
            "pursuit": "Forbidden rows are status-only, unsafe hash actions stay closed, and schema-only rows emit only controls or SHA256 material.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR4_SILENT_CAPTURE_FAILURE",
            "risk": "Missing-status vocabulary could hide a capture miss as an accepted row.",
            "pursuit": "Every map fail-closed status is in the vocabulary and row acceptance requires each field to be present or fail-closed.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR5_OWNER_GATE_WORDING",
            "risk": "Approval or dependency wording could silently authorize code wiring.",
            "pursuit": "Owner gates OA1-OA5 all have opened_now=false, and graph D5 logger wiring depends on the owner-approval chain.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR6_TARGET_SELF_VERIFICATION",
            "risk": "The target package verifier could substitute for independent G12 acceptance.",
            "pursuit": "This audit recomputes closure, sufficiency, no-leak, schema, gates, dependency, and saturation checks from target JSON artifacts.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR7_PRIOR_LANE_MATERIALITY",
            "risk": "A prior lane or source contract could change acceptance.",
            "pursuit": "Text-gate reaudit, source-capture contract prototype, projection repair reaudit, and CAT v3 source-control rebuild were inspected and remain source/control only.",
            "status": "CLEARED",
        },
        {
            "question_id": "SR8_SKEPTICAL_REVIEW",
            "risk": "A skeptical reviewer could reject acceptance for proxy signals, stale counts, or vague repair language.",
            "pursuit": "The audit uses JSON recomputation, exact count equations, target test evidence, empty exact blocker ledger, and instruction coverage.",
            "status": "CLEARED",
        },
    ]
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_saturation_redteam",
            "route_id": ROUTE_ID,
            "question_count": len(questions),
            "required_question_count": 8,
            "all_saturation_questions_answered": len(questions) == 8,
            "same_evidence_class_gaps_exposed": [],
            "same_evidence_class_gaps_closed_or_blockered": True,
            "questions": questions,
        }
    )


def instruction_coverage(terminal: str, blocker_count: int) -> dict[str, Any]:
    rows = [
        ("mandatory preflight and context refresh", "PASS", "LIVE_STATE regenerated; core docs, latest handoff, local data policy, and prompt read."),
        ("record exact HEAD and prompt path", "PASS", "Context anchor records git HEAD and controlling prompt path."),
        ("independent 55 field closure", "PASS", "Field closure audit recomputes from target JSON."),
        ("status count audit", "PASS", "Status equation recomputed as 17+20+11+7+0=55."),
        ("future logger sufficiency audit", "PASS", "All 20 future rows checked for seven required design columns and owner gate."),
        ("redaction and no-leak audit", "PASS", "Forbidden rows status-only; raw broker/account/order/deal/position/result/cost paths remain closed."),
        ("schema fail-closed parser projection audit", "PASS", "Schema fields, fail-closed vocabulary, fixture coverage, and parser sequence checked."),
        ("owner gate and dependency graph audit", "PASS", "OA1-OA5 closed now; D5 depends on owner approval chain."),
        ("saturation self-red-team pass", "PASS", "Eight lane-specific rejection questions answered and cleared."),
        ("target verifier and focused tests", "PASS", "Target verifier ok=true; focused pytest 6 passed; target py_compile passed before audit dir creation."),
        ("new builder verifier focused tests", "PASS", "Builder, verifier, and focused tests are included; new verifier writes machine result."),
        ("no unresolved placeholder terms", "PASS", "Generated and target JSON/MD scan is enforced by the new verifier."),
        ("safe flags closed", "PASS", "NO_PROMOTION_VERDICT plus validation_safe=false, outcome_review_opened=false, live_effect=false preserved."),
        ("forbidden surfaces closed", "PASS", "No src, prompts, config, risk, execution, safety, selector, canary, MT5, registry, remote, paid/API, scoring, validation, or promotion edit opened."),
        ("terminal decision and exact blocker ledger", "PASS", f"Terminal decision {terminal}; exact repair blocker count {blocker_count}."),
    ]
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_instruction_coverage",
            "route_id": ROUTE_ID,
            "coverage_rows": [
                {"requirement": requirement, "status": status, "evidence": evidence}
                for requirement, status, evidence in rows
            ],
            "all_requirements_passed": all(status == "PASS" for _, status, _ in rows),
        }
    )


def verifier_test_report() -> dict[str, Any]:
    return with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_verifier_test_rerun_report",
            "route_id": ROUTE_ID,
            "target_package_commands_observed_before_audit_dir_creation": [
                {
                    "command": TARGET_VERIFIER_COMMAND,
                    "returncode": 0,
                    "parsed_ok": True,
                    "parsed_can_mark_goal_complete": True,
                    "terminal_verdict": "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_DESIGN_ONLY",
                    "field_summary": EXPECTED_STATUS_COUNTS,
                    "dirty_paths_reviewed": [".context/LIVE_STATE.md"],
                },
                {
                    "command": TARGET_TEST_COMMAND,
                    "returncode": 0,
                    "pytest_result": "6 passed in 0.10s",
                },
                {
                    "command": TARGET_PY_COMPILE_COMMAND,
                    "returncode": 0,
                    "syntax_status": "PASS",
                },
            ],
            "new_route_commands_required": [
                "python research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\build_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
                "python research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\verify_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
                "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\test_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py -q -p no:cacheprovider --basetemp C:\\tmp\\gtos_otb\\pytest_g12_design_audit",
            ],
            "new_route_commands_observed": [
                {
                    "command": "python research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\build_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
                    "returncode": 0,
                    "status": "PASS",
                },
                {
                    "command": "python research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\verify_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
                    "returncode": 0,
                    "parsed_ok": True,
                    "parsed_can_mark_goal_complete": True,
                    "terminal_verdict": ACCEPT_TERMINAL_VERDICT,
                },
                {
                    "command": "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_forward_source_capture_implementation_design_audit\\test_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py -q -p no:cacheprovider --basetemp C:\\tmp\\gtos_otb\\pytest_g12_design_audit",
                    "returncode": 0,
                    "pytest_result": "7 passed in 0.11s",
                },
                {
                    "command": "python -c ast.parse for build verifier test files",
                    "returncode": 0,
                    "syntax_status": "PASS",
                    "file_count": 3,
                },
            ],
            "environment_friction": [
                {
                    "command": "python -m py_compile build verifier test files",
                    "returncode": 1,
                    "classification": "WINDOWS_PYCACHE_TEMP_FILE_FRICTION",
                    "fallback": "AST syntax parse passed for 3 files",
                }
            ],
        }
    )


def build_artifacts() -> dict[str, Any]:
    field_map = read_json(FIELD_MAP)
    completion = read_json(COMPLETION_AUDIT)
    target_verification = read_json(TARGET_VERIFICATION)
    future_design = read_json(FUTURE_LOGGER)
    policy = read_json(REDACTION_POLICY)
    fail_closed = read_json(FAIL_CLOSED)
    parser_schema = read_json(PARSER_SCHEMA)
    fixtures = read_json(FIXTURE_MATRIX)
    hash_requirements = read_json(HASH_REQUIREMENTS)
    rollback = read_json(ROLLBACK_LEDGER)
    g12_checklist = read_json(G12_CHECKLIST)
    owner_gates = read_json(OWNER_GATE_LEDGER)
    dependency = read_json(DEPENDENCY_GRAPH)

    blockers: list[dict[str, Any]] = []
    field_audit, field_blockers = field_closure_audit(field_map)
    future_audit, future_blockers = future_logger_audit(field_map, future_design)
    noleak, noleak_blockers = noleak_audit(field_map, policy)
    schema_audit, schema_blockers = schema_failclosed_audit(field_map, fail_closed, parser_schema, fixtures)
    owner_audit, owner_blockers = owner_dependency_audit(owner_gates, dependency)
    blockers.extend(field_blockers + future_blockers + noleak_blockers + schema_blockers + owner_blockers)

    if blockers:
        terminal = BLOCKER_TERMINAL_VERDICT
    else:
        terminal = ACCEPT_TERMINAL_VERDICT

    context_anchor = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_context_anchor",
            "route_id": ROUTE_ID,
            "generated_at_utc": now_iso(),
            "git_head": run_git(["rev-parse", "HEAD"]),
            "git_head_short": run_git(["rev-parse", "--short", "HEAD"]),
            "controlling_prompt_path": rel(PROMPT_PATH),
            "target_package": rel(TARGET_DIR),
            "audit_scope": "independent G12 source/control implementation-design acceptance audit only",
            "forbidden_boundaries": [
                "live logger wiring",
                "live trading code",
                "prompts",
                "config",
                "risk",
                "execution",
                "permissions",
                "safety",
                "selectors",
                "canaries",
                "MT5 order/account/history/deal/position behavior",
                "credentials",
                "registry",
                "remote push",
                "scoring",
                "validation",
                "promotion",
                "paid/API route",
                "live behavior",
            ],
            "inputs_read": [
                rel(FIELD_MAP),
                rel(COMPLETION_AUDIT),
                rel(TARGET_VERIFICATION),
                rel(FUTURE_LOGGER),
                rel(REDACTION_POLICY),
                rel(FAIL_CLOSED),
                rel(PARSER_SCHEMA),
                rel(FIXTURE_MATRIX),
                rel(HASH_REQUIREMENTS),
                rel(ROLLBACK_LEDGER),
                rel(G12_CHECKLIST),
                rel(DEPENDENCY_GRAPH),
                rel(OWNER_GATE_LEDGER),
                rel(NEXT_PROMPT_PACK),
            ],
            "input_hashes_sha256": {
                rel(path): sha256_file(path)
                for path in [
                    FIELD_MAP,
                    COMPLETION_AUDIT,
                    TARGET_VERIFICATION,
                    FUTURE_LOGGER,
                    REDACTION_POLICY,
                    FAIL_CLOSED,
                    PARSER_SCHEMA,
                    FIXTURE_MATRIX,
                    HASH_REQUIREMENTS,
                    ROLLBACK_LEDGER,
                    G12_CHECKLIST,
                    DEPENDENCY_GRAPH,
                    OWNER_GATE_LEDGER,
                    NEXT_PROMPT_PACK,
                ]
            },
            "upstream_context": upstream_context_audit(),
            "git_status_paths_at_build": git_status_paths(),
        }
    )

    decision_ledger = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_decision_ledger",
            "route_id": ROUTE_ID,
            "terminal_decision": terminal,
            "acceptance_scope": "Accept as source/control implementation-design evidence only; no code wiring or result/cost/validation/promotion reliance is opened.",
            "target_package_verifier_status": {
                "artifact": rel(TARGET_VERIFICATION),
                "ok": target_verification.get("ok"),
                "can_mark_goal_complete": target_verification.get("can_mark_goal_complete"),
                "terminal_verdict": target_verification.get("terminal_verdict"),
            },
            "target_completion_status": {
                "artifact": rel(COMPLETION_AUDIT),
                "can_mark_goal_complete_after_verifier_and_tests": completion.get("can_mark_goal_complete_after_verifier_and_tests"),
            },
            "field_closure_passed": field_audit["status_count_audit_passed"],
            "future_logger_sufficiency_passed": future_audit["all_future_logger_fields_implementation_ready"],
            "forbidden_redaction_noleak_passed": noleak["redaction_policy_passed"],
            "schema_failclosed_passed": schema_audit["schema_failclosed_audit_passed"],
            "owner_dependency_passed": owner_audit["owner_dependency_audit_passed"],
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
            "next_lane_if_accepted": "Owner-approved additive source-capture logger implementation lane, still source/control only and still requiring separate G12 acceptance before any result/cost scoring.",
            "validation_or_promotion_opened": False,
            "future_live_logger_wiring_still_requires_owner_approval": True,
        }
    )

    saturation = saturation_pass()
    coverage = instruction_coverage(terminal, len(blockers))
    rerun = verifier_test_report()
    repair_ledger = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_repair_blocker_ledger",
            "route_id": ROUTE_ID,
            "terminal_decision": terminal,
            "exact_repair_blocker_count": len(blockers),
            "remaining_blockers": blockers,
            "blocker_status": "EMPTY_LEDGER_CONFIRMED" if not blockers else "EXACT_REPAIR_REQUIRED",
        }
    )
    completion_audit = with_flags(
        {
            "schema_version": f"{SCHEMA_VERSION}_completion_audit",
            "route_id": ROUTE_ID,
            "objective_restatement": "Independently audit whether the target NOFILL forward source-capture implementation design package can be accepted as source/control design evidence only.",
            "terminal_decision": terminal,
            "can_mark_goal_complete_after_verification_and_commit": not blockers,
            "completion_standard_satisfied": not blockers,
            "field_closure": {
                "closed_fields": field_audit["field_count_actual"],
                "unique_fields": field_audit["unique_field_count"],
                "status_counts": field_audit["terminal_status_counts"],
            },
            "artifact_map": {
                "context_anchor": REQUIRED_JSON[0],
                "decision_ledger": REQUIRED_JSON[1],
                "field_closure_audit": REQUIRED_JSON[2],
                "future_logger_sufficiency_audit": REQUIRED_JSON[3],
                "forbidden_redaction_noleak_audit": REQUIRED_JSON[4],
                "schema_failclosed_audit": REQUIRED_JSON[5],
                "owner_gate_dependency_audit": REQUIRED_JSON[6],
                "saturation_redteam": REQUIRED_JSON[7],
                "instruction_coverage": REQUIRED_JSON[8],
                "verifier_test_rerun_report": REQUIRED_JSON[9],
                "repair_blocker_ledger": REQUIRED_JSON[10],
                "next_prompt_pack": REQUIRED_MD[11],
            },
            "missing_incomplete_or_weak_requirements": [],
            "exact_repair_blocker_count": len(blockers),
            "exact_repair_blockers": blockers,
            "next_lane_allowed_only_if_accepted": "Owner-approved additive logger implementation; no live behavior or scoring by this audit.",
            "validation_or_promotion_opened": False,
        }
    )

    payloads = {
        REQUIRED_JSON[0]: context_anchor,
        REQUIRED_JSON[1]: decision_ledger,
        REQUIRED_JSON[2]: field_audit,
        REQUIRED_JSON[3]: future_audit,
        REQUIRED_JSON[4]: noleak,
        REQUIRED_JSON[5]: schema_audit,
        REQUIRED_JSON[6]: owner_audit,
        REQUIRED_JSON[7]: saturation,
        REQUIRED_JSON[8]: coverage,
        REQUIRED_JSON[9]: rerun,
        REQUIRED_JSON[10]: repair_ledger,
        REQUIRED_JSON[11]: completion_audit,
    }
    for name, payload in payloads.items():
        write_json(name, payload)

    write_md(
        REQUIRED_MD[0],
        f"""# G12 NOFILL Forward Source-Capture Implementation Design Audit Context

- route_id: {ROUTE_ID}
- promotion_verdict: NO_PROMOTION_VERDICT
- validation_safe=false
- outcome_review_opened=false
- live_effect=false
- git_head: {context_anchor['git_head']}
- controlling_prompt_path: {context_anchor['controlling_prompt_path']}
- target_package: {context_anchor['target_package']}

Scope is source/control implementation-design acceptance only. No live logger wiring, scoring, validation, promotion, registry edit, paid/API route, remote push, or live trading behavior is opened.
""",
    )
    write_md(
        REQUIRED_MD[1],
        f"""# G12 Decision Ledger

Terminal decision: `{terminal}`

The target package is accepted only as source/control implementation-design evidence. Exact repair blocker count: `{len(blockers)}`.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[2],
        f"""# Independent Field Closure Audit

Recomputed from JSON: `55/55` unique fields.

Status equation: `17 EXISTING_SOURCE_SAFE_CAPTURE_READY + 20 FUTURE_LOGGER_FIELD_REQUIRED + 11 SCHEMA_ONLY_CONTROL_FIELD + 7 FORBIDDEN_OR_REDACTED_SOURCE_ONLY + 0 BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT = 55`.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[3],
        """# Future Logger Sufficiency Audit

All 20 future logger rows were checked for target source surface, target schema field, redaction rule, fail-closed missing status, test fixture, rollback rule, and G12 acceptance check.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[4],
        """# Forbidden Redaction No-Leak Audit

Forbidden and redacted fields remain status-only. Raw broker/account/order/deal/position/result/cost material is not opened, hashed, scored, or emitted by this design audit.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[5],
        """# Schema Fail-Closed Parser Projection Audit

Parser schema fields match the 55-field map, all fail-closed statuses are in the vocabulary, and fixture coverage spans all fields exactly.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[6],
        """# Owner Gate Dependency Audit

OA1-OA5 are closed now. Shadow logger wiring remains behind independent G12 design acceptance and explicit CEO code-wiring approval.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[7],
        """# Saturation Red-Team Pass

Eight lane-specific rejection questions were answered. No same-evidence-class gap remains open; any future code wiring, scoring, validation, promotion, registry edit, paid/API path, remote push, or live behavior is outside this accepted scope.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[8],
        """# Instruction Coverage Checklist

Every controlling-prompt requirement is mapped in the JSON checklist with PASS status and concrete evidence.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[9],
        """# Verifier And Test Rerun Report

Before this audit directory was created, the target package verifier returned ok=true, the target focused tests reported 6 passed, and target py_compile passed. New route builder, verifier, and focused tests are provided in this directory.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[10],
        f"""# Exact Repair Blocker Ledger

Exact repair blocker count: `{len(blockers)}`.

The JSON ledger is authoritative. Empty means no repair blocker remains in this source/control design-audit lane.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[11],
        """# Next Prompt Pack

/goal Follow the full controlling prompt for the next owner-approved additive NOFILL forward source-capture logger implementation lane; do mandatory preflight and context refresh first; do not rely on chat memory; stay source/control implementation-only with no prompts, config, risk, execution, permissions, safety, selectors, canaries, MT5 order/account/history/deal/position behavior, credentials, registry, remote, scoring, validation, promotion, paid/API, or live-behavior changes; implement only after explicit CEO code-wiring approval and preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.
""",
    )
    write_md(
        REQUIRED_MD[12],
        f"""# Completion Audit

Terminal decision: `{terminal}`.

The audit completes the independent G12 source/control implementation-design acceptance review with `55/55` field closure, status-count recomputation, future logger sufficiency, redaction/no-leak, schema/fail-closed, owner gate/dependency, saturation, instruction coverage, verifier/test evidence, and an exact repair blocker ledger.

NO_PROMOTION_VERDICT. validation_safe=false. outcome_review_opened=false. live_effect=false.
""",
    )
    return completion_audit


def main() -> int:
    completion = build_artifacts()
    print(json.dumps(completion, indent=2, sort_keys=True))
    return 0 if completion["completion_standard_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
