#!/usr/bin/env python3
"""Verify the independent G12 implementation-design audit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
RESULT_JSON = OUT_DIR / builder.VERIFICATION_RESULT_NAME

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)

ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_implementation_design_audit/",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)

BAD_FRAGMENTS = tuple(
    item.lower()
    for item in (
        "tb" + "d",
        "to" + "do",
        "un" + "known",
        "may" + "be",
        "la" + "ter",
        "not" + " " + "yet" + " " + "decided",
    )
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return sorted(paths)


def verify_control_flags(name: str, payload: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": name, "value": payload.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(flag) is not False:
            failures.append({"check": "required_closed_flag", "file": name, "flag": flag, "value": payload.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_live_wiring",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_route_flag", "file": name, "flag": flag, "value": payload.get(flag)})


def scan_placeholders() -> list[dict[str, str]]:
    roots = [OUT_DIR, builder.TARGET_DIR]
    hits: list[dict[str, str]] = []
    for root in roots:
        for path in sorted(list(root.glob("*.json")) + list(root.glob("*.md"))):
            if path.name == builder.VERIFICATION_RESULT_NAME:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for fragment in BAD_FRAGMENTS:
                if fragment in text:
                    hits.append({"path": path.relative_to(REPO_ROOT).as_posix(), "fragment": fragment})
    return hits


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_files = (
        builder.REQUIRED_JSON
        + builder.REQUIRED_MD
        + [
            "build_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
            "verify_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
            "test_g12_nofill_forward_source_capture_implementation_design_audit_2026_05_10.py",
        ]
    )
    missing = [name for name in required_files if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_audit_artifacts", "missing": missing})

    parsed: dict[str, Any] = {}
    json_errors: list[dict[str, str]] = []
    for name in builder.REQUIRED_JSON:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(path)
        except json.JSONDecodeError as exc:
            json_errors.append({"file": name, "error": str(exc)})
    if json_errors:
        failures.append({"check": "json_parse", "errors": json_errors})

    for name in builder.REQUIRED_MD:
        path = OUT_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})
        for literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if literal in text:
                failures.append({"check": "forbidden_open_flag_literal", "file": name, "literal": literal})

    for name, payload in parsed.items():
        if isinstance(payload, dict):
            verify_control_flags(name, payload, failures)

    decision = parsed.get(builder.REQUIRED_JSON[1], {})
    terminal = decision.get("terminal_decision")
    if terminal != builder.ACCEPT_TERMINAL_VERDICT:
        failures.append({"check": "terminal_decision", "value": terminal})
    if decision.get("exact_repair_blocker_count") != 0 or decision.get("exact_repair_blockers") != []:
        failures.append({"check": "decision_repair_blockers", "value": decision.get("exact_repair_blockers")})
    if decision.get("future_live_logger_wiring_still_requires_owner_approval") is not True:
        failures.append({"check": "owner_wiring_gate_not_preserved"})
    if decision.get("validation_or_promotion_opened") is not False:
        failures.append({"check": "decision_validation_or_promotion_boundary"})

    field = parsed.get(builder.REQUIRED_JSON[2], {})
    if field.get("field_count_actual") != 55 or field.get("unique_field_count") != 55:
        failures.append({"check": "field_count", "field_audit": field})
    if field.get("terminal_status_counts") != builder.EXPECTED_STATUS_COUNTS:
        failures.append({"check": "terminal_status_counts", "value": field.get("terminal_status_counts")})
    if field.get("exact_repair_blockers") != [] or field.get("status_count_audit_passed") is not True:
        failures.append({"check": "field_closure_blockers", "value": field.get("exact_repair_blockers")})

    future = parsed.get(builder.REQUIRED_JSON[3], {})
    if future.get("future_logger_field_count") != 20 or future.get("all_future_logger_fields_implementation_ready") is not True:
        failures.append({"check": "future_logger_sufficiency", "value": future})
    for row in future.get("per_field", []):
        if row.get("missing_required_columns") or row.get("implementation_ready_without_reinterpretation") is not True:
            failures.append({"check": "future_logger_row", "row": row})

    noleak = parsed.get(builder.REQUIRED_JSON[4], {})
    if noleak.get("forbidden_row_count") != 7 or noleak.get("redaction_policy_passed") is not True:
        failures.append({"check": "noleak_status", "value": noleak})
    if noleak.get("raw_broker_account_order_deal_position_result_cost_leak_opened") is not False:
        failures.append({"check": "raw_leak_boundary_opened"})
    if noleak.get("future_logger_forbidden_raw_schema_fields"):
        failures.append({"check": "future_logger_forbidden_schema", "value": noleak.get("future_logger_forbidden_raw_schema_fields")})

    schema = parsed.get(builder.REQUIRED_JSON[5], {})
    if schema.get("schema_field_count") != 55 or schema.get("fixture_covered_field_count") != 55:
        failures.append({"check": "schema_fixture_field_count", "value": schema})
    if schema.get("bad_fail_closed_statuses") != [] or schema.get("schema_failclosed_audit_passed") is not True:
        failures.append({"check": "schema_failclosed", "value": schema})

    owner = parsed.get(builder.REQUIRED_JSON[6], {})
    if owner.get("approval_gate_count") != 5 or owner.get("all_owner_gates_closed_now") is not True:
        failures.append({"check": "owner_gate_count_or_open_state", "value": owner})
    if owner.get("shadow_logger_wiring_requires_owner_approval_chain") is not True:
        failures.append({"check": "owner_approval_chain"})

    saturation = parsed.get(builder.REQUIRED_JSON[7], {})
    if saturation.get("question_count") != 8 or saturation.get("all_saturation_questions_answered") is not True:
        failures.append({"check": "saturation_question_count", "value": saturation})
    for item in saturation.get("questions", []):
        if item.get("status") != "CLEARED":
            failures.append({"check": "saturation_item_not_cleared", "item": item})
    if saturation.get("same_evidence_class_gaps_exposed") != []:
        failures.append({"check": "saturation_open_gap", "value": saturation.get("same_evidence_class_gaps_exposed")})

    coverage = parsed.get(builder.REQUIRED_JSON[8], {})
    if coverage.get("all_requirements_passed") is not True:
        failures.append({"check": "instruction_coverage", "value": coverage})
    for row in coverage.get("coverage_rows", []):
        if row.get("status") != "PASS":
            failures.append({"check": "instruction_row", "row": row})

    rerun = parsed.get(builder.REQUIRED_JSON[9], {})
    observed = rerun.get("target_package_commands_observed_before_audit_dir_creation", [])
    if len(observed) != 3:
        failures.append({"check": "target_rerun_command_count", "value": observed})
    for item in observed:
        if item.get("returncode") != 0:
            failures.append({"check": "target_command_failed", "item": item})
    if observed and observed[0].get("parsed_ok") is not True:
        failures.append({"check": "target_verifier_not_ok", "item": observed[0]})

    repair = parsed.get(builder.REQUIRED_JSON[10], {})
    if repair.get("exact_repair_blocker_count") != 0 or repair.get("remaining_blockers") != []:
        failures.append({"check": "repair_blocker_ledger", "value": repair})

    completion = parsed.get(builder.REQUIRED_JSON[11], {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing_or_weak", "value": completion.get("missing_incomplete_or_weak_requirements")})
    if completion.get("exact_repair_blocker_count") != 0:
        failures.append({"check": "completion_blocker_count", "value": completion.get("exact_repair_blocker_count")})

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits})

    dirty_paths = git_status_paths()
    forbidden_live_dirty = [path for path in dirty_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_allowed_dirty = [
        path for path in dirty_paths if not any(path.startswith(prefix) or path == prefix for prefix in ALLOWED_DIRTY_PREFIXES)
    ]
    if forbidden_live_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_live_dirty})
    if outside_allowed_dirty:
        warnings.append({"check": "outside_allowed_dirty_informational", "paths": outside_allowed_dirty})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.CONTROL_FLAGS,
        "terminal_verdict": terminal,
        "exact_repair_blocker_count": repair.get("exact_repair_blocker_count"),
        "field_status_counts": field.get("terminal_status_counts"),
        "future_logger_field_count": future.get("future_logger_field_count"),
        "saturation_question_count": saturation.get("question_count"),
        "failures": failures,
        "warnings": warnings,
        "json_files_parsed": sorted(parsed),
        "placeholder_scan_passed": not placeholder_hits,
        "dirty_paths_reviewed": dirty_paths,
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "validation_or_promotion_opened": False,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
