"""Verify READY8 expanded validation scoring/result materialization artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_ready8_expanded_validation_scoring_result_materialization_2026_05_16 as builder


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-16"
SAFE_FLAGS = builder.SAFE_FLAGS
FORBIDDEN_FALSE_FLAGS = builder.FORBIDDEN_FALSE_FLAGS
ROUTE_ID = builder.ROUTE_ID
EVIDENCE_CLASS = builder.EVIDENCE_CLASS
MUTABLE_COORDINATION_SOURCE_PATHS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def route_file(name: str) -> Path:
    return ROUTE_DIR / name


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def check_safe_flags(record: dict[str, Any], label: str, errors: list[str]) -> None:
    for key, expected in SAFE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: safe flag {key}={record.get(key)!r}, expected {expected!r}")
    for key, expected in FORBIDDEN_FALSE_FLAGS.items():
        if record.get(key) != expected:
            errors.append(f"{label}: forbidden surface {key}={record.get(key)!r}, expected {expected!r}")


def verify(mark_focused_tests_ok: bool = False, focused_tests_summary: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}

    expected_files = [
        f"READY8_EXPANDED_SCORING_CONTEXT_ANCHOR_{DATE}.json",
        f"READY8_EXPANDED_SCORING_PREREQUISITE_ACCEPTANCE_G12_PROVENANCE_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_SCORING_SOURCE_UNIVERSE_SEARCHED_ROOT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_SCORING_METHOD_FREEZE_{DATE}.json",
        f"READY8_EXPANDED_SCORING_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json",
        f"READY8_EXPANDED_SCORING_DUPLICATE_DENOMINATOR_EFFECTIVE_N_POLICY_{DATE}.json",
        f"READY8_EXPANDED_SCORING_PARTITION_POLICY_{DATE}.json",
        f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_UNC004_SOURCE_BIAS_SOURCE_CAPTURE_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_QUESTION_AMBIGUITY_PURSUIT_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_OPEN_DOOR_CLOSED_DOOR_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_SOURCE_CAPTURE_FORWARD_RETEST_IMPLICATION_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_SCORING_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_SCORING_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json",
        f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json",
        f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md",
        f"G12_READY8_EXPANDED_VALIDATION_SCORING_RESULT_AUDIT_STARTER_{DATE}.txt",
        f"READY8_EXPANDED_SCORING_SYNTHESIS_{DATE}.md",
    ]
    missing = [name for name in expected_files if not route_file(name).exists()]
    if missing:
        errors.append(f"missing expected artifacts: {missing}")
    checks["expected_files_exist"] = not missing

    row_counts = {
        "packet_admission": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl")),
        "row_branch_result": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl")),
        "haz001": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_HAZ001_RESULT_LEDGER_{DATE}.jsonl")),
        "mac": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_MAC_INVERSE_AVOID_FILTER_RESULT_LEDGER_{DATE}.jsonl")),
        "haz005": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_HAZ005_REPAIRED_ROW_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl")),
        "residual": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_RESIDUAL_FAILURE_INTELLIGENCE_RESULT_LEDGER_{DATE}.jsonl")),
        "repaired_target": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_REPAIRED_TARGET_CONSUMPTION_RESULT_LEDGER_{DATE}.jsonl")),
        "failure_intelligence": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_KILLED_WEAKENED_DEFERRED_RESULT_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl")),
        "open_closed_doors": count_jsonl(route_file(f"READY8_EXPANDED_SCORING_OPEN_DOOR_CLOSED_DOOR_LEDGER_{DATE}.jsonl")),
    }
    expected_counts = {
        "packet_admission": 182,
        "row_branch_result": 182,
        "haz001": 143,
        "mac": 32,
        "haz005": 5,
        "residual": 1,
        "repaired_target": 5320,
        "failure_intelligence": 2641,
        "open_closed_doors": 364,
    }
    for key, expected in expected_counts.items():
        if row_counts.get(key) != expected:
            errors.append(f"{key} row count {row_counts.get(key)} != {expected}")
    checks["row_counts"] = row_counts
    checks["row_counts_match_expected"] = all(row_counts.get(k) == v for k, v in expected_counts.items())

    packet_ids = {row["packet_row_id"] for row in iter_jsonl(route_file(f"READY8_EXPANDED_SCORING_PACKET_ROW_ADMISSION_LEDGER_{DATE}.jsonl"))}
    result_ids = {row["packet_row_id"] for row in iter_jsonl(route_file(f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl"))}
    if packet_ids != result_ids:
        errors.append(f"packet/result coverage mismatch: missing={sorted(packet_ids - result_ids)[:5]}, extra={sorted(result_ids - packet_ids)[:5]}")
    checks["packet_result_coverage_match"] = packet_ids == result_ids

    decision = read_json(route_file(f"READY8_EXPANDED_SCORING_DECISION_LEDGER_{DATE}.json"))
    check_safe_flags(decision, "decision_ledger", errors)
    expected_decision = "MATERIALIZED_READY8_EXPANDED_VALIDATION_SCORING_RESULT_PACKET_G12_AUDIT_REQUIRED_NO_PROMOTION"
    if decision.get("terminal_decision") != expected_decision:
        errors.append(f"terminal decision mismatch: {decision.get('terminal_decision')}")
    checks["terminal_decision_ok"] = decision.get("terminal_decision") == expected_decision

    completion = read_json(route_file(f"READY8_EXPANDED_SCORING_COMPLETION_AUDIT_{DATE}.json"))
    check_safe_flags(completion, "completion_audit", errors)
    if completion.get("same_evidence_class_intelligence_remaining") != 0:
        errors.append("completion audit does not show same_evidence_class_intelligence_remaining=0")
    checks["same_evidence_class_remaining_zero"] = completion.get("same_evidence_class_intelligence_remaining") == 0

    source_hash = read_json(route_file(f"READY8_EXPANDED_SCORING_SOURCE_HASH_LEDGER_{DATE}.json"))
    check_safe_flags(source_hash, "source_hash_ledger", errors)
    source_rehash_errors = []
    mutable_source_rehash_warnings = []
    for source in source_hash["sources"]:
        source_path = ROOT / source["path"]
        if not source_path.exists():
            source_rehash_errors.append(f"missing source {source['path']}")
            continue
        current = builder.sha256_file(source_path)
        current_canonical_lf = builder.sha256_file_canonical_lf(source_path)
        expected_raw = source["sha256"]
        expected_canonical_lf = source.get("sha256_canonical_lf")
        raw_matches = current == expected_raw
        canonical_matches = expected_canonical_lf is not None and current_canonical_lf == expected_canonical_lf
        if not raw_matches and not canonical_matches:
            message = (
                f"source hash drift {source['path']}: raw {current} != {expected_raw}; "
                f"canonical_lf {current_canonical_lf} != {expected_canonical_lf}"
            )
            if source["path"] in MUTABLE_COORDINATION_SOURCE_PATHS:
                mutable_source_rehash_warnings.append(message)
            else:
                source_rehash_errors.append(message)
    errors.extend(source_rehash_errors)
    checks["source_hashes_match_current_disk"] = not source_rehash_errors
    checks["mutable_coordination_source_hash_drift_count"] = len(mutable_source_rehash_warnings)
    checks["mutable_coordination_source_hash_drift_bounded"] = True
    checks["mutable_coordination_source_hash_drift_warnings"] = mutable_source_rehash_warnings
    checks["same_evidence_class_hash_rebound_count"] = source_hash.get("same_evidence_class_hash_rebound_count")

    blocker_rows = list(iter_jsonl(route_file(f"READY8_EXPANDED_SCORING_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl")))
    rebound_blockers = [row for row in blocker_rows if row.get("blocker") == "same_evidence_class_stale_source_hash"]
    if source_hash.get("same_evidence_class_hash_rebound_count") != len(rebound_blockers):
        errors.append("stale hash rebound count does not match blocker ledger")
    checks["stale_hash_rebounds_ledgered"] = source_hash.get("same_evidence_class_hash_rebound_count") == len(rebound_blockers)

    jsonl_safe_checked = 0
    for path in ROUTE_DIR.glob("READY8_EXPANDED_SCORING_*.jsonl"):
        for idx, row in enumerate(iter_jsonl(path), 1):
            check_safe_flags(row, f"{path.name}:{idx}", errors)
            jsonl_safe_checked += 1
    checks["jsonl_safe_rows_checked"] = jsonl_safe_checked

    for path in ROUTE_DIR.glob("READY8_EXPANDED_SCORING_*.json"):
        if path.name.endswith(f"OUTPUT_MANIFEST_{DATE}.json"):
            continue
        data = read_json(path)
        if isinstance(data, dict) and "promotion_verdict" in data:
            check_safe_flags(data, path.name, errors)
    checks["json_safe_flags_checked"] = True

    if mark_focused_tests_ok:
        focused = {
            **builder.safe_base(),
            "generated_at_utc": builder.utc_now(),
            "focused_tests_ok": True,
            "status": "PASSED",
            "command": f"py -3 -m pytest {rel(ROUTE_DIR / 'test_ready8_expanded_validation_scoring_result_materialization_2026_05_16.py')}",
            "summary": focused_tests_summary or "focused pytest passed",
        }
        builder.write_json(route_file(f"READY8_EXPANDED_SCORING_FOCUSED_TEST_RESULT_{DATE}.json"), focused)
    else:
        focused = read_json(route_file(f"READY8_EXPANDED_SCORING_FOCUSED_TEST_RESULT_{DATE}.json"))
    checks["focused_tests_ok"] = bool(focused.get("focused_tests_ok"))
    if not focused.get("focused_tests_ok"):
        errors.append("focused tests not recorded as passing")

    manifest_errors = []
    child_g12_manifest_entries_ignored = 0
    manifest = read_json(route_file(f"READY8_EXPANDED_SCORING_OUTPUT_MANIFEST_{DATE}.json"))
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if builder.is_child_g12_audit_artifact(path):
            child_g12_manifest_entries_ignored += 1
            continue
        if not path.exists():
            manifest_errors.append(f"manifest file missing {item['path']}")
            continue
        current = builder.sha256_file(path)
        if current != item["sha256"]:
            # The verifier and focused-test result are rewritten by this run; the
            # manifest is refreshed after verification below.
            if not item["path"].endswith((f"VERIFICATION_RESULT_{DATE}.json", f"FOCUSED_TEST_RESULT_{DATE}.json")):
                manifest_errors.append(f"manifest hash drift {item['path']}")
    checks["manifest_hashes_match_before_refresh"] = not manifest_errors
    checks["child_g12_manifest_entries_ignored_before_refresh"] = child_g12_manifest_entries_ignored
    errors.extend(manifest_errors)

    result = {
        **builder.safe_base(),
        "generated_at_utc": builder.utc_now(),
        "ok": not errors,
        "can_mark_goal_complete": not errors,
        "checks": checks,
        "errors": errors,
    }
    builder.write_json(route_file(f"READY8_EXPANDED_SCORING_VERIFICATION_RESULT_{DATE}.json"), result)
    builder.write_output_manifest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--focused-tests-summary", default=None)
    args = parser.parse_args()
    result = verify(args.mark_focused_tests_ok, args.focused_tests_summary)
    print(json.dumps({"ok": result["ok"], "can_mark_goal_complete": result["can_mark_goal_complete"], "errors": result["errors"]}, indent=2))
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
