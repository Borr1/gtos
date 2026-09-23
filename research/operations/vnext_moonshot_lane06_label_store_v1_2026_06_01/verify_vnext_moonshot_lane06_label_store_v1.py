#!/usr/bin/env python3
"""Verify Lane06 label store artifacts."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any, Iterator

from build_vnext_moonshot_lane06_label_store_v1 import (
    ALL_LABEL_FAMILIES,
    COMPLETION_AUDIT,
    DEPENDENCY_STATE_LEDGER,
    DOWNSTREAM_CONTRACT,
    FOCUSED_TEST_RESULT,
    LANE05_DIR,
    LANE07_DIR,
    LABEL_FAMILY_COVERAGE_LEDGER,
    LABEL_SCHEMA,
    LABEL_VECTOR_LEDGER,
    MISSING_LABEL_GAP_LEDGER,
    NO_LEAK_LEDGER,
    OUTPUT_MANIFEST,
    RESULT_USE_STATUS,
    RESULT_USE_STATUS_PATH,
    ROUTE_DIR,
    ROUTE_ID,
    RUNTIME_EFFECT_BOUNDARY,
    RUNTIME_EFFECT_BOUNDARY_PATH,
    SOURCE_COMPLETENESS_LEDGER,
    SOURCE_COVERAGE_LEDGER,
    TEST_FILE,
    VERIFICATION_RESULT,
    VERIFIER,
    build_route,
    manifest_payload,
    rel,
    utc_now,
    write_json,
)


EXPECTED_MIN_LABEL_VECTOR_ROWS = 289_928
EXPECTED_MIN_MISSING_GAP_ROWS = 1
REQUIRED_CORE_FAMILIES = {
    "sl_before_1r",
    "one_r_reached",
    "partial_then_be",
    "partial_then_final",
    "final_target_reached",
    "no_entry_touch",
    "stuck_no_resolution",
    "mfe_r",
    "mae_r",
    "time_to_1r_seconds",
    "time_to_sl_seconds",
    "time_to_final_seconds",
    "execution_policy_result",
    "stale_blocker",
    "correct_rejection",
    "missed_opportunity",
    "source_gap_present",
    "source_bound_proxy_r",
    "cost_adjusted_r",
    "broker_real_net_r",
    "manual_intervention",
    "broker_modify_failure",
    "false_close",
    "ambiguity_state",
    "no_trade_baseline_outcome",
}


def iter_jsonl(path: Path, limit: int | None = None) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)
            count += 1
            if limit is not None and count >= limit:
                return


def count_jsonl(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"{rel(path)} is not a JSON object")
    return data


def sample_gzip_rows(path: Path, sample_count: int = 25) -> list[dict[str, Any]]:
    return list(iter_jsonl(path, limit=sample_count))


def verify_route() -> dict[str, Any]:
    issues: list[str] = []
    required = [
        LABEL_SCHEMA,
        LABEL_VECTOR_LEDGER,
        MISSING_LABEL_GAP_LEDGER,
        LABEL_FAMILY_COVERAGE_LEDGER,
        SOURCE_COVERAGE_LEDGER,
        NO_LEAK_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        DOWNSTREAM_CONTRACT,
        RUNTIME_EFFECT_BOUNDARY_PATH,
        RESULT_USE_STATUS_PATH,
        COMPLETION_AUDIT,
        OUTPUT_MANIFEST,
        Path(__file__).resolve().parent / "build_vnext_moonshot_lane06_label_store_v1.py",
        VERIFIER,
        TEST_FILE,
    ]
    for path in required:
        if not path.exists():
            issues.append(f"missing_required_output:{rel(path)}")
        elif path.stat().st_size == 0:
            issues.append(f"empty_required_output:{rel(path)}")
    if issues:
        return write_result(False, issues, {})

    schema = read_json(LABEL_SCHEMA)
    audit = read_json(COMPLETION_AUDIT)
    downstream = read_json(DOWNSTREAM_CONTRACT)
    result_use = read_json(RESULT_USE_STATUS_PATH)
    runtime_boundary = read_json(RUNTIME_EFFECT_BOUNDARY_PATH)

    schema_families = set((schema.get("label_families") or {}).keys())
    missing_schema_families = sorted(REQUIRED_CORE_FAMILIES - schema_families)
    if missing_schema_families:
        issues.append(f"schema_missing_label_families:{missing_schema_families}")
    if set(ALL_LABEL_FAMILIES) - schema_families:
        issues.append("schema_missing_builder_family_set")
    if schema.get("runtime_effect_boundary") != RUNTIME_EFFECT_BOUNDARY:
        issues.append("schema_runtime_effect_boundary_mismatch")

    label_rows = count_jsonl(LABEL_VECTOR_LEDGER)
    if label_rows < EXPECTED_MIN_LABEL_VECTOR_ROWS:
        issues.append(f"label_vector_rows_too_low:{label_rows}")
    missing_gap_rows = count_jsonl(MISSING_LABEL_GAP_LEDGER)
    if missing_gap_rows < EXPECTED_MIN_MISSING_GAP_ROWS:
        issues.append("missing_label_gap_rows_absent")

    coverage_rows = list(iter_jsonl(LABEL_FAMILY_COVERAGE_LEDGER))
    coverage_by_family = {row.get("label_family"): row for row in coverage_rows}
    for family in REQUIRED_CORE_FAMILIES:
        row = coverage_by_family.get(family)
        if not row:
            issues.append(f"coverage_missing_family:{family}")
        elif int(row.get("total_label_vector_rows") or 0) != label_rows:
            issues.append(f"coverage_total_mismatch:{family}")

    for family in ("sl_before_1r", "one_r_reached", "source_bound_proxy_r", "execution_policy_result"):
        row = coverage_by_family.get(family) or {}
        if int(row.get("available_rows") or 0) <= 0:
            issues.append(f"label_family_no_available_rows:{family}")
    broker_row = coverage_by_family.get("broker_real_net_r") or {}
    if int(broker_row.get("available_rows") or 0) <= 0:
        issues.append("broker_real_net_r_not_materialized")

    no_leak_rows = list(iter_jsonl(NO_LEAK_LEDGER))
    failing_checks = [row.get("check_id") for row in no_leak_rows if row.get("status") != "pass"]
    if failing_checks:
        issues.append(f"no_leak_checks_failed:{failing_checks}")

    deps = list(iter_jsonl(DEPENDENCY_STATE_LEDGER))
    dep_by_name = {row.get("dependency_name"): row for row in deps}
    for name in ("lane01_source_authority", "lane02_asof_contract", "lane03_canonical_reconstruction", "lane04_microscope_timelines"):
        if not dep_by_name.get(name, {}).get("exists"):
            issues.append(f"dependency_not_present:{name}")
    lane05 = dep_by_name.get("lane05_feature_store_contract")
    if LANE05_DIR.exists():
        if not lane05 or lane05.get("dependency_state") != "present_consumed_for_label_join_no_leak_contract":
            issues.append("lane05_present_dependency_state_missing")
    elif not lane05 or lane05.get("dependency_state") != "absent_dependency_state_recorded_not_blocking_label_builder":
        issues.append("lane05_absent_dependency_state_missing")
    lane07 = dep_by_name.get("lane07_broker_truth_cost_calibration")
    if LANE07_DIR.exists():
        if not lane07 or lane07.get("dependency_state") != "present_consumed_for_broker_truth_cost_labels_where_joinable":
            issues.append("lane07_present_dependency_state_missing")

    label_samples = sample_gzip_rows(LABEL_VECTOR_LEDGER, 40)
    if not label_samples:
        issues.append("label_vector_sample_empty")
    for row in label_samples:
        values = row.get("label_values") or {}
        if row.get("no_leak_status") != "label_only_excluded_from_feature_rows":
            issues.append("label_vector_no_leak_status_missing")
            break
        if "feature_name" in row or "feature_value" in row:
            issues.append("feature_fields_leaked_into_label_vector")
            break
        if not REQUIRED_CORE_FAMILIES.issubset(set(values.keys())):
            issues.append("label_vector_missing_core_label_values")
            break
        if row.get("runtime_effect_boundary") != RUNTIME_EFFECT_BOUNDARY:
            issues.append("label_vector_runtime_boundary_mismatch")
            break

    gap_samples = sample_gzip_rows(MISSING_LABEL_GAP_LEDGER, 20)
    if not gap_samples:
        issues.append("missing_gap_sample_empty")
    for row in gap_samples:
        if not row.get("canonical_candidate_id"):
            issues.append("missing_gap_without_canonical_candidate_id")
            break
        if not (row.get("repair_requirement") or row.get("repair_requirement_code")):
            issues.append("missing_gap_without_repair_requirement")
            break

    contract_sections = {"feature_store", "digital_twin", "ml", "selector", "scheduler", "execution_policy"}
    if not contract_sections.issubset(set(downstream.keys())):
        issues.append("downstream_contract_missing_sections")
    if "forbidden_as_feature_column" not in json.dumps(downstream.get("feature_store", {})):
        issues.append("feature_store_forbidden_label_contract_missing")
    if LANE05_DIR.exists() and downstream.get("feature_store", {}).get("lane05_state") != "present_consumed_for_label_join_no_leak_contract":
        issues.append("downstream_contract_lane05_present_state_missing")
    if LANE07_DIR.exists() and "broker_truth_cost_contract" not in json.dumps(downstream):
        issues.append("downstream_contract_lane07_cost_contract_missing")
    if result_use.get("result_use_status") != RESULT_USE_STATUS:
        issues.append("result_use_status_mismatch")
    if runtime_boundary.get("runtime_effect_boundary") != RUNTIME_EFFECT_BOUNDARY:
        issues.append("runtime_effect_boundary_mismatch")

    counts = audit.get("counts") or {}
    if counts.get("label_vector_rows") != label_rows:
        issues.append("audit_label_vector_count_mismatch")
    if counts.get("missing_label_gap_rows") != missing_gap_rows:
        issues.append("audit_missing_gap_count_mismatch")
    if not audit.get("instruction_coverage", {}).get("broker_real_proxy_replay_separated"):
        issues.append("audit_broker_proxy_separation_missing")
    if LANE05_DIR.exists() and not audit.get("instruction_coverage", {}).get("lane05_feature_store_present_consumed"):
        issues.append("audit_lane05_present_consumption_missing")
    if LANE07_DIR.exists() and not audit.get("instruction_coverage", {}).get("lane07_broker_truth_cost_present_consumed"):
        issues.append("audit_lane07_present_consumption_missing")

    metrics = {
        "label_vector_rows": label_rows,
        "missing_label_gap_rows": missing_gap_rows,
        "coverage_family_rows": len(coverage_rows),
        "no_leak_checks": len(no_leak_rows),
        "dependency_rows": len(deps),
    }
    return write_result(not issues, issues, metrics)


def write_result(ok: bool, issues: list[str], metrics: dict[str, Any]) -> dict[str, Any]:
    result = {
        "schema_version": "lane06_verification_result_v1",
        "route_id": ROUTE_ID,
        "verified_at_utc": utc_now(),
        "ok": ok,
        "issue_count": len(issues),
        "issues": issues,
        "metrics": metrics,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
    }
    write_json(VERIFICATION_RESULT, result)
    audit = read_json(COMPLETION_AUDIT) if COMPLETION_AUDIT.exists() else {}
    if audit:
        audit["last_verification_refresh_at_utc"] = result["verified_at_utc"]
        audit["verifier_ok"] = ok
        audit["verification_result"] = {"path": rel(VERIFICATION_RESULT), "ok": ok, "issues": issues}
        if ok:
            audit["status"] = "complete_verified" if FOCUSED_TEST_RESULT.exists() else "complete_verified_pending_focused_test_artifact"
            for req in audit.get("requirements", []):
                if req.get("requirement") == "manifest_verifier_focused_tests":
                    req["status"] = "complete" if FOCUSED_TEST_RESULT.exists() else "verifier_complete_focused_test_artifact_pending"
                    req["verifier_ok"] = True
                    req["focused_test_result_present"] = FOCUSED_TEST_RESULT.exists()
        write_json(COMPLETION_AUDIT, audit)
    write_json(OUTPUT_MANIFEST, manifest_payload(result["verified_at_utc"]))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--rebuild-first", action="store_true")
    args = parser.parse_args(argv)
    if args.rebuild_first:
        build_route()
    result = verify_route()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
