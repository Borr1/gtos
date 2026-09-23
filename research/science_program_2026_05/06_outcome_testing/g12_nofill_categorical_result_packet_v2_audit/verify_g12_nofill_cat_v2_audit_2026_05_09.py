#!/usr/bin/env python3
"""Verify G12 no-fill categorical V2 audit artifacts."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_INPUT_ONLY_CATEGORICAL_LIFECYCLE_EVIDENCE_WITH_BLOCKED_AND_REJECTED_FAMILIES_PRESERVED"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/"

EXPECTED_DECISIONS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ACCEPTED_SOURCE_LANES = {
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
    "prior_g12_categorical_packet_audit": 52,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}
EXPECTED_REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

JSON_ARTIFACTS = [
    f"G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"G12_NOFILL_CAT_V2_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_LEARNING_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V2_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V2_COMPLETION_AUDIT_{DATE}.md",
]

PY_FILES = [
    "build_g12_nofill_cat_v2_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v2_audit_2026_05_09.py",
    "test_g12_nofill_cat_v2_audit_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
    "tests/canary",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def check_artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def check_json_parse() -> dict[str, Any]:
    errors = []
    parsed = 0
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
            parsed += 1
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": parsed, "errors": errors}


def check_markdown_promotion() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if path.exists() and PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_promotion_verdict": missing}


def check_flags(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for name, payload in items.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{name}: promotion_verdict")
        if payload.get("validation_safe") is not False:
            issues.append(f"{name}: validation_safe")
        if payload.get("outcome_review_opened") is not False:
            issues.append(f"{name}: outcome_review_opened")
        if payload.get("live_effect") is not False:
            issues.append(f"{name}: live_effect")
        for row in payload.get("row_decisions", []):
            if row.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{name}:{row.get('packet_row_id')}: promotion_verdict")
            if row.get("validation_safe") is not False:
                issues.append(f"{name}:{row.get('packet_row_id')}: validation_safe")
            if row.get("outcome_review_opened") is not False:
                issues.append(f"{name}:{row.get('packet_row_id')}: outcome_review_opened")
            if row.get("live_effect") is not False:
                issues.append(f"{name}:{row.get('packet_row_id')}: live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_decision_counts(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    decision = items[f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"]
    if decision["decision"] != DECISION:
        issues.append("decision mismatch")
    if decision["status"] != "PASS":
        issues.append("decision status")
    if decision["row_count"] != 298:
        issues.append("row count")
    if decision["partition_counts"] != {
        "accepted": 225,
        "accepted_prior": 52,
        "accepted_source_corrected": 173,
        "blocked": 8,
        "rejected": 65,
    }:
        issues.append({"partition_counts": decision["partition_counts"]})
    if decision["decision_counts"] != EXPECTED_DECISIONS:
        issues.append({"decision_counts": decision["decision_counts"]})
    if decision["accepted_label_counts"] != EXPECTED_ACCEPTED_LABELS:
        issues.append({"accepted_label_counts": decision["accepted_label_counts"]})
    if decision["accepted_source_lane_counts"] != EXPECTED_ACCEPTED_SOURCE_LANES:
        issues.append({"accepted_source_lane_counts": decision["accepted_source_lane_counts"]})
    overlaps = decision["overlap_checks"]
    if overlaps["accepted_blocker_overlap"] or overlaps["accepted_reject_overlap"] or overlaps["blocker_reject_overlap"]:
        issues.append({"overlaps": overlaps})
    if overlaps["partition_unique_ids"] != 298 or overlaps["covers_298_rows"] is not True:
        issues.append("partition coverage")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_label_rules(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    decision = items[f"G12_NOFILL_CAT_V2_DECISION_LEDGER_{DATE}.json"]
    meanings = decision["label_meanings"]
    for label, count in EXPECTED_ACCEPTED_LABELS.items():
        if label not in meanings:
            issues.append(f"missing label meaning: {label}")
        elif meanings[label]["count"] != count:
            issues.append(f"label meaning count mismatch: {label}")
        elif not any("not R/performance" == item for item in meanings[label]["does_not_prove"]):
            issues.append(f"label non-claim missing: {label}")
    rows = decision["row_decisions"]
    accepted = [row for row in rows if row["g12_audit_decision"] == "ACCEPT_NARROW_INPUT_ONLY_ROW"]
    blocked_rejected = [row for row in rows if row["g12_audit_decision"] != "ACCEPT_NARROW_INPUT_ONLY_ROW"]
    if len(accepted) != 225 or len(blocked_rejected) != 73:
        issues.append("accepted/blocked/rejected decision row split")
    if any(row.get("categorical_input_label") is None for row in accepted):
        issues.append("accepted row missing label")
    if any(row.get("categorical_input_label") is not None for row in blocked_rejected):
        issues.append("blocked/rejected row has label")
    if any(row.get("in_accepted_packet_denominator") for row in blocked_rejected):
        issues.append("blocked/rejected row in denominator")
    if any(row.get("label_is_performance_outcome") is not False for row in rows):
        issues.append("performance label flag")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hash_and_blocker_proof(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    source = items[f"G12_NOFILL_CAT_V2_SOURCE_HASH_AUDIT_{DATE}.json"]
    if source["status"] != "PASS":
        issues.append("source hash status")
    if source["missing_control_inputs"]:
        issues.append("missing control inputs")
    if source["v2_control_input_rehash"]["status"] != "PASS":
        issues.append("v2 control input rehash status")
    if source["v2_control_input_rehash"]["mismatches"]:
        issues.append("source data/control mismatches")
    if source["source_hash_drift_classification"] not in {
        "NO_DRIFT",
        "NON_SOURCE_CONTROL_PROMPT_HASH_DRIFT_NO_DATA_INVALIDATION",
    }:
        issues.append("drift classification")
    if len(source["recomputed_oti3_same_tick_order_checks"]) != 4:
        issues.append("OTI3 check count")
    if any(item["status"] != "PASS" or item["matching_tick_record_count"] != 1 or len(item["simultaneous_events"]) < 2 for item in source["recomputed_oti3_same_tick_order_checks"]):
        issues.append("OTI3 blocker proof")
    if len(source["recomputed_oti4_may3_source_gap_checks"]) != 3:
        issues.append("OTI4 check count")
    if any(item["status"] != "PASS" or any(file_check["required_range_count"] != 0 for file_check in item["file_checks"]) for item in source["recomputed_oti4_may3_source_gap_checks"]):
        issues.append("OTI4 source gap proof")
    original = source["recomputed_original_oti2_source_gap_check"]
    if original["status"] != "PASS" or original["row_count"] != 1:
        issues.append("original OTI2 source gap proof")
    if source["inherited_g12_source_hash_mismatches"] or source["inherited_g12_missing_source_hash_records"]:
        issues.append("inherited G12 source hash issues")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_noleak_duplicate_rejects(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    noleak = items[f"G12_NOFILL_CAT_V2_NO_LEAK_LABEL_DUPLICATE_AUDIT_{DATE}.json"]
    review = items[f"G12_NOFILL_CAT_V2_BLOCKER_REJECT_REVIEW_{DATE}.json"]
    if noleak["status"] != "PASS":
        issues.append("noleak status")
    if noleak["forbidden_key_hits"] or noleak["flag_issues"] or noleak["label_issues"]:
        issues.append("noleak issues")
    if noleak["countable_scope"] != {
        "performance_outcome_rows": 0,
        "row_level_input_only_categorical_evidence": 225,
        "unique_duplicate_key_input_only_categorical_evidence": 182,
        "validation_or_promotion_rows": 0,
    }:
        issues.append({"countable_scope": noleak["countable_scope"]})
    if noleak["sample_floor_posture"]["validation_sample_floor_status"] != "NOT_A_VALIDATION_OR_PROMOTION_LANE_NO_SAMPLE_FLOOR_CLAIM":
        issues.append("sample floor status")
    if review["status"] != "PASS":
        issues.append("blocker/reject review status")
    if review["blocked_row_count"] != 8 or review["rejected_row_count"] != 65:
        issues.append("blocker/reject counts")
    if review["blocker_code_counts"] != EXPECTED_BLOCKER_CODES:
        issues.append({"blocker_code_counts": review["blocker_code_counts"]})
    if review["reject_decision_counts"] != EXPECTED_REJECT_DECISIONS:
        issues.append({"reject_decision_counts": review["reject_decision_counts"]})
    if review["blocked_or_rejected_rows_have_no_label"] is not True:
        issues.append("blocked/rejected labels")
    if review["blocked_or_rejected_rows_in_denominator"]:
        issues.append("blocked/rejected denominator")
    if review["hidden_performance_reason_detected"] is not False:
        issues.append("hidden performance reason")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_py_compile() -> dict[str, Any]:
    results = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
            results.append({"path": name, "status": "PASS"})
        except Exception as exc:
            results.append({"path": name, "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("G12_NOFILL_CAT_V2_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_NOFILL_CAT_V2_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["G12_NOFILL_CAT_V2_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_g12_nofill_cat_v2_audit_2026_05_09.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
        "command": f"{sys.executable} -B -m pytest -p no:cacheprovider {OUT_DIR / 'test_g12_nofill_cat_v2_audit_2026_05_09.py'} -q",
    }


def changed_paths_from_status() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    paths = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def changed_paths_from_head_diff() -> tuple[list[str], bool]:
    proc = subprocess.run(["git", "diff", "--name-only", "HEAD^", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [], False
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()], True


def check_live_surface_diff() -> dict[str, Any]:
    workspace_paths = changed_paths_from_status()
    committed_paths, committed_ok = changed_paths_from_head_diff()
    committed_scope_relevant = committed_ok and any(path.startswith(LANE_PREFIX) for path in committed_paths)
    checked_paths = committed_paths if committed_scope_relevant else workspace_paths
    forbidden = [path for path in checked_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    workspace_forbidden = [path for path in workspace_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    status_ok = not forbidden and (committed_scope_relevant or not workspace_forbidden)
    return {
        "status": "PASS" if status_ok else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if committed_scope_relevant else "workspace_status",
        "changed_paths": checked_paths,
        "workspace_changed_paths_observed": workspace_paths,
        "forbidden_live_surface_changed_paths": forbidden,
        "workspace_forbidden_live_surface_changed_paths": workspace_forbidden,
        "workspace_forbidden_paths_informational_only": committed_scope_relevant,
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def write_completion(verification: dict[str, Any]) -> None:
    builder_path = OUT_DIR / "build_g12_nofill_cat_v2_audit_2026_05_09.py"
    spec = importlib.util.spec_from_file_location("g12_cat_v2_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load G12 CAT V2 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_completion_audit(status="VERIFIED_BY_G12_CAT_V2_VERIFIER", verification=verification)


def verify_audit(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    items = payloads()
    results: dict[str, Any] = {
        "artifact_presence": check_artifact_presence(),
        "json_parse": check_json_parse(),
        "markdown_promotion": check_markdown_promotion(),
    }
    if results["json_parse"]["status"] == "PASS":
        items = payloads()
        results.update(
            {
                "flags": check_flags(items),
                "decision_counts": check_decision_counts(items),
                "label_rules": check_label_rules(items),
                "source_hash_and_blocker_proof": check_source_hash_and_blocker_proof(items),
                "noleak_duplicate_rejects": check_noleak_duplicate_rejects(items),
            }
        )
    results["py_compile"] = check_py_compile()
    results["live_surface_diff"] = check_live_surface_diff()
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "called with run_pytest=False"}
    results["verification_status"] = {
        "status": "PASS" if all(value.get("status") in ("PASS", "SKIPPED") for value in results.values() if isinstance(value, dict)) else "FAIL"
    }
    if write_audit:
        write_completion(results)
    return results


def main() -> int:
    results = verify_audit(run_pytest=True, write_audit=True)
    status = results["verification_status"]["status"]
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
