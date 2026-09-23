"""Verify G12 R10 sealed historical validation result audit artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_g12_r10_sealed_historical_validation_result_audit_2026_05_16 as builder


DATE = builder.DATE
ROUTE_DIR = Path(__file__).resolve().parent


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_number"] = line_number
                yield row


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def check_safe(record: dict[str, Any], label: str, errors: list[str]) -> None:
    for key, expected in builder.SAFE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")
    for key, expected in builder.FORBIDDEN_FALSE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: {key}={record.get(key)!r}, expected {expected!r}")


def expected_files() -> list[str]:
    return [
        "build_g12_r10_sealed_historical_validation_result_audit_2026_05_16.py",
        "verify_g12_r10_sealed_historical_validation_result_audit_2026_05_16.py",
        "test_g12_r10_sealed_historical_validation_result_audit_2026_05_16.py",
        f"G12_R10_CONTEXT_ANCHOR_{DATE}.json",
        f"G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl",
        f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
        f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_SOURCE_HASH_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_SOURCE_DRIFT_REPAIR_LEDGER_{DATE}.jsonl",
        f"G12_R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"G12_R10_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"G12_R10_DECISION_LEDGER_{DATE}.json",
        f"G12_R10_COMPLETION_AUDIT_{DATE}.json",
        f"G12_R10_ARTIFACT_AUDIT_RESULT_{DATE}.json",
        f"G12_R10_FOCUSED_TEST_RESULT_{DATE}.json",
        f"G12_R10_VERIFICATION_RESULT_{DATE}.json",
        f"G12_R10_SYNTHESIS_{DATE}.md",
        f"G12_R10_OUTPUT_MANIFEST_{DATE}.json",
        f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md",
        f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_STARTER_{DATE}.txt",
    ]


def verify(
    *,
    update: bool = False,
    focused_tests_ok: bool = False,
    focused_tests_summary: str | None = None,
    artifact_audit_ok: bool | None = None,
    artifact_audit_summary: str | None = None,
    require_focused_tests: bool = True,
    require_artifact_audit: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    missing = [name for name in expected_files() if not route_file(name).exists()]
    checks["expected_files_exist"] = not missing
    if missing:
        errors.append(f"missing expected files: {missing}")

    repair_path = route_file(f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl")
    search_path = route_file(f"G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl")
    repair_rows = list(iter_jsonl(repair_path)) if repair_path.exists() else []
    search_rows = list(iter_jsonl(search_path)) if search_path.exists() else []
    repair_statuses = Counter(row.get("repair_status") for row in repair_rows)
    source_types = Counter(row.get("source_row_type") for row in repair_rows)
    checks["repair_row_count"] = len(repair_rows)
    checks["repair_status_counts"] = dict(repair_statuses)
    checks["repair_source_row_type_counts"] = dict(source_types)
    checks["search_root_count"] = len(search_rows)
    if len(repair_rows) != 5502:
        errors.append(f"repair attempt row count {len(repair_rows)} != 5502")
    if len(search_rows) != len(builder.SOURCE_ROOTS):
        errors.append(f"search root row count {len(search_rows)} != {len(builder.SOURCE_ROOTS)}")
    if repair_statuses != {"NO_REPAIR_EXACT_IMPOSSIBILITY_WITHIN_G12_EVIDENCE_CLASS": 5502}:
        errors.append(f"unexpected repair statuses: {dict(repair_statuses)}")
    if source_types.get("packet_row", 0) != 182:
        errors.append(f"packet repair rows {source_types.get('packet_row', 0)} != 182")
    repaired_target_count = source_types.get("repaired_target_row", 0) + source_types.get("accepted_r5_repaired_target_row", 0)
    if repaired_target_count != 5320:
        errors.append(f"repaired target repair rows {repaired_target_count} != 5320")

    missing_root_lists = 0
    missing_impossibility = 0
    exact_r_rows = 0
    neutral_side_rows = 0
    repaired_entry_horizon_rows = 0
    packet_entry_missing_rows = 0
    for row in repair_rows:
        check_safe(row, f"{repair_path.name}:{row['_source_line_number']}", errors)
        if len(row.get("accepted_local_source_roots_searched", [])) != len(builder.SOURCE_ROOTS):
            missing_root_lists += 1
        if not row.get("exact_owner_access_source_capture_evidence_class_impossibility"):
            missing_impossibility += 1
        if row.get("repair_status") != "NO_REPAIR_EXACT_IMPOSSIBILITY_WITHIN_G12_EVIDENCE_CLASS":
            exact_r_rows += 1
        if row.get("source_control_side_if_found") == "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT":
            neutral_side_rows += 1
        fields = row.get("field_repair_results", {})
        if fields.get("entry_reference") == "REPAIRED_SOURCE_BOUND_ENTRY_CLOSE_PRESENT" and fields.get("horizon") == "REPAIRED_SOURCE_BOUND_HORIZON_PRESENT":
            repaired_entry_horizon_rows += 1
        if row.get("source_row_type") == "packet_row" and "entry_reference" in row.get("missing_geometry_fields_after_audit", []):
            packet_entry_missing_rows += 1
    checks["rows_missing_full_root_list"] = missing_root_lists
    checks["rows_missing_exact_impossibility_text"] = missing_impossibility
    checks["exact_r_rows_computed"] = exact_r_rows
    checks["neutral_source_control_side_rows"] = neutral_side_rows
    checks["repaired_target_entry_horizon_repaired_rows"] = repaired_entry_horizon_rows
    checks["packet_rows_with_entry_missing"] = packet_entry_missing_rows
    if missing_root_lists:
        errors.append(f"repair rows missing full source root list: {missing_root_lists}")
    if missing_impossibility:
        errors.append(f"repair rows missing impossibility text: {missing_impossibility}")
    if exact_r_rows:
        errors.append(f"rows unexpectedly marked exact R repaired: {exact_r_rows}")
    if neutral_side_rows != 5320:
        errors.append(f"neutral source-control side rows {neutral_side_rows} != 5320")
    if repaired_entry_horizon_rows != 5320:
        errors.append(f"repaired target entry/horizon repaired rows {repaired_entry_horizon_rows} != 5320")
    if packet_entry_missing_rows != 182:
        errors.append(f"packet rows with entry missing {packet_entry_missing_rows} != 182")

    for path in ROUTE_DIR.glob("G12_R10_*.jsonl"):
        for row in iter_jsonl(path):
            check_safe(row, f"{path.name}:{row['_source_line_number']}", errors)

    json_files = [
        f"G12_R10_CONTEXT_ANCHOR_{DATE}.json",
        f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_SOURCE_HASH_RECOMPUTATION_LEDGER_{DATE}.json",
        f"G12_R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"G12_R10_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"G12_R10_DECISION_LEDGER_{DATE}.json",
        f"G12_R10_COMPLETION_AUDIT_{DATE}.json",
    ]
    for name in json_files:
        path = route_file(name)
        if path.exists():
            check_safe(read_json(path), name, errors)

    row_counts = read_json(route_file(f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json"))
    metrics = read_json(route_file(f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json"))
    target_stop = read_json(route_file(f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json"))
    decision = read_json(route_file(f"G12_R10_DECISION_LEDGER_{DATE}.json"))
    completion = read_json(route_file(f"G12_R10_COMPLETION_AUDIT_{DATE}.json"))
    instruction = read_json(route_file(f"G12_R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json"))
    source_hash = read_json(route_file(f"G12_R10_SOURCE_HASH_RECOMPUTATION_LEDGER_{DATE}.json"))

    checks["row_counts_match"] = row_counts.get("all_row_counts_match") is True
    checks["exact_r_expectancy_rows_computed"] = metrics.get("exact_r_expectancy_rows_computed_after_audit")
    checks["target_stop_hit_miss_rows_computed"] = metrics.get("target_stop_hit_miss_rows_computed_after_audit")
    checks["target_stop_ambiguous_rows"] = target_stop.get("ambiguous_rows")
    checks["terminal_decision_ok"] = decision.get("terminal_decision") == builder.TERMINAL_DECISION
    checks["completion_standard_met"] = completion.get("completion_standard_met") is True
    checks["same_evidence_class_remaining_zero"] = completion.get("same_evidence_class_intelligence_remaining") == 0
    checks["instruction_coverage_ok"] = instruction.get("all_requirements_satisfied") is True
    checks["real_immutable_source_drift_count"] = source_hash.get("real_immutable_source_drift_count")
    if not checks["row_counts_match"]:
        errors.append("G12 row-count recomputation has mismatches")
    if checks["exact_r_expectancy_rows_computed"] != 0:
        errors.append("exact R/expectancy rows computed is not zero")
    if checks["target_stop_hit_miss_rows_computed"] != 0:
        errors.append("target/stop hit/miss rows computed is not zero")
    if checks["target_stop_ambiguous_rows"] != 5502:
        errors.append(f"target-stop ambiguous rows {checks['target_stop_ambiguous_rows']} != 5502")
    if not checks["terminal_decision_ok"]:
        errors.append(f"terminal decision mismatch: {decision.get('terminal_decision')!r}")
    if not checks["completion_standard_met"]:
        errors.append("completion_standard_met is not true")
    if not checks["same_evidence_class_remaining_zero"]:
        errors.append("same evidence class remaining is not zero")
    if not checks["instruction_coverage_ok"]:
        errors.append("instruction coverage is not true")
    if checks["real_immutable_source_drift_count"] != 0:
        errors.append(f"real immutable source drift count {checks['real_immutable_source_drift_count']} != 0")

    if require_focused_tests and not focused_tests_ok:
        errors.append("focused tests not recorded as passed")
    if require_artifact_audit and artifact_audit_ok is not True:
        errors.append("artifact audit not recorded as passed")
    checks["focused_tests_ok"] = focused_tests_ok
    checks["focused_tests_summary"] = focused_tests_summary
    checks["artifact_audit_ok"] = artifact_audit_ok
    checks["artifact_audit_summary"] = artifact_audit_summary

    result = {
        **builder.safe_base(),
        "generated_at_utc": builder.utc_now(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    if update:
        if focused_tests_ok:
            builder.write_json(
                route_file(f"G12_R10_FOCUSED_TEST_RESULT_{DATE}.json"),
                {
                    **builder.safe_base(),
                    "generated_at_utc": builder.utc_now(),
                    "ok": True,
                    "summary": focused_tests_summary or "focused tests passed",
                },
            )
        if artifact_audit_ok is not None:
            builder.write_json(
                route_file(f"G12_R10_ARTIFACT_AUDIT_RESULT_{DATE}.json"),
                {
                    **builder.safe_base(),
                    "generated_at_utc": builder.utc_now(),
                    "ok": artifact_audit_ok,
                    "summary": artifact_audit_summary,
                    "command": f"py -3 scripts/audit_goal_route_artifacts.py {builder.rel(ROUTE_DIR)} --full-jsonl",
                },
            )
        builder.write_json(route_file(f"G12_R10_VERIFICATION_RESULT_{DATE}.json"), result)
        builder.write_json(route_file(f"G12_R10_OUTPUT_MANIFEST_{DATE}.json"), builder.output_manifest())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary")
    parser.add_argument("--artifact-audit-ok", action="store_true")
    parser.add_argument("--artifact-audit-summary")
    parser.add_argument("--no-require-focused-tests", action="store_true")
    parser.add_argument("--no-require-artifact-audit", action="store_true")
    args = parser.parse_args()
    result = verify(
        update=args.update,
        focused_tests_ok=args.focused_tests_ok,
        focused_tests_summary=args.focused_tests_summary,
        artifact_audit_ok=True if args.artifact_audit_ok else None,
        artifact_audit_summary=args.artifact_audit_summary,
        require_focused_tests=not args.no_require_focused_tests,
        require_artifact_audit=not args.no_require_artifact_audit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
