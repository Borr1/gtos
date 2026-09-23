#!/usr/bin/env python3
"""Verify G12 no-fill CAT V2 forensics-audit artifacts."""

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
DECISION = "ACCEPT_FORENSICS_SYNTHESIS_AS_QUARANTINED_CATEGORICAL_SOURCE_CONTROL_LEARNING_OPEN_G0_CONTROL_SYNTHESIS"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_quarantined_categorical_synthesis_forensics_audit/"

EXPECTED_PARTITION = {"accepted": 225, "blocked": 8, "rejected": 65, "universe": 298}
EXPECTED_ACCEPTED_SPLIT = {"accepted_prior": 52, "accepted_source_corrected": 173}
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
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.json",
]
MD_ARTIFACTS = [
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
    "test_g12_nofill_cat_v2_forensics_audit_2026_05_09.py",
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
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


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
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_decision(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    decision = items[f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_DECISION_LEDGER_{DATE}.json"]
    checks = {
        "status": decision["status"] == "PASS",
        "decision": decision["decision"] == DECISION,
        "partition": decision["partition_counts"] == EXPECTED_PARTITION,
        "accepted_split": decision["accepted_split"] == EXPECTED_ACCEPTED_SPLIT,
        "accepted_labels": decision["accepted_label_counts"] == EXPECTED_ACCEPTED_LABELS,
        "accepted_source_lanes": decision["accepted_source_lane_counts"] == EXPECTED_ACCEPTED_SOURCE_LANES,
        "route": decision["route_decision"]["primary_next_route"] == "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE",
        "quant_boundary": decision["route_decision"]["quantitative_result_lane"].startswith("CLOSED_UNTIL_"),
    }
    failures = [key for key, ok in checks.items() if not ok]
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "checks": checks}


def check_slices(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    slices = items[f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SLICE_RECHECK_{DATE}.json"]
    failing = [key for key, value in slices["checks"].items() if value["status"] != "PASS"]
    duplicate = slices["duplicate_policy"]
    if duplicate["accepted_unique_nofill_duplicate_keys"] != 182:
        failing.append("accepted_unique_nofill_duplicate_keys")
    if duplicate["duplicate_key_collision_count"] != 5:
        failing.append("duplicate_key_collision_count")
    if duplicate["rows_in_duplicate_key_collisions"] != 48:
        failing.append("rows_in_duplicate_key_collisions")
    if duplicate["oti5_canonical_duplicate_rows_accepted"] != 3:
        failing.append("oti5_canonical_duplicate_rows_accepted")
    if duplicate["oti5_noncanonical_duplicate_rows_rejected"] != 39:
        failing.append("oti5_noncanonical_duplicate_rows_rejected")
    return {"status": "PASS" if not failing and slices["status"] == "PASS" else "FAIL", "failures": failing}


def check_label_learning(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    review = items[f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_LABEL_LEARNING_REVIEW_{DATE}.json"]
    failures = []
    if review["status"] != "PASS":
        failures.append("status")
    if sorted(review["label_reviews"]) != sorted(EXPECTED_ACCEPTED_LABELS):
        failures.append("label set")
    for label, expected_count in EXPECTED_ACCEPTED_LABELS.items():
        item = review["label_reviews"][label]
        if item["row_count_check"]["status"] != "PASS" or item["row_count_check"]["actual"] != expected_count:
            failures.append(label)
        if item["missing_required_fields"] or item["missing_required_nonclaims"]:
            failures.append(f"{label}: missing fields/nonclaims")
        if item["descriptive_only"] is not True or item["validation_safe_false"] is not True:
            failures.append(f"{label}: flags")
    if review["oti2_fill_path_rollup_check"]["actual"] != 29:
        failures.append("oti2 rollup")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def check_blockers(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    review = items[f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_BLOCKER_REJECT_REVIEW_{DATE}.json"]
    failures = []
    if review["status"] != "PASS":
        failures.append("status")
    for key, value in review["checks"].items():
        if value["status"] != "PASS":
            failures.append(key)
    expected_families = {
        "oti4_may3_source_gaps": 3,
        "oti3_same_tick_order_ambiguities": 4,
        "original_oti2_source_gap": 1,
    }
    for family, count in expected_families.items():
        item = review["blocker_family_checks"][family]
        if item["row_count"]["actual"] != count or not item["has_unblocker"]:
            failures.append(family)
    if review["source_access_requirement"]["oti4_may3_source_gaps"].find("2026-05-03 13:00-13:30 UTC") < 0:
        failures.append("oti4 exact range")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def check_noleak_future(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    review = items[f"G12_NOFILL_CAT_V2_FORENSICS_AUDIT_NO_LEAK_DUPLICATE_SOURCE_REVIEW_{DATE}.json"]
    failures = []
    if review["status"] != "PASS":
        failures.append("status")
    for key, value in review["checks"].items():
        if value["status"] != "PASS":
            failures.append(key)
    if review["forbidden_key_hits"]:
        failures.append("forbidden_key_hits")
    if review["source_hash_posture"]["g12_v2_source_status"] != "PASS":
        failures.append("source status")
    if review["future_route_boundary"]["accepted_next_route"] != "NOFILL_CAT_V2_G0_SYNTHESIS_CONTROL_ROUTE":
        failures.append("accepted next route")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def check_py_compile() -> dict[str, Any]:
    results = []
    cache_dir = OUT_DIR / "__pycache__"
    cache_dir.mkdir(exist_ok=True)
    for index, name in enumerate(PY_FILES):
        cfile = cache_dir / f"g12_forensics_audit_{index}.pyc"
        try:
            py_compile.compile(str(OUT_DIR / name), cfile=str(cfile), doraise=True)
            if cfile.exists():
                cfile.unlink()
            results.append({"path": name, "status": "PASS"})
        except Exception as exc:
            results.append({"path": name, "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["G12_NOFILL_CAT_V2_FORENSICS_AUDIT_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_g12_nofill_cat_v2_forensics_audit_2026_05_09.py"),
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


def recent_committed_lane_paths() -> tuple[list[str], list[str]]:
    proc = subprocess.run(["git", "log", "-n", "30", "--format=%H"], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [], []
    commits = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    lane_commits = []
    paths = set()
    for commit in commits:
        diff = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        if diff.returncode != 0:
            continue
        commit_paths = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
        if any(path.startswith(LANE_PREFIX) for path in commit_paths):
            lane_commits.append(commit[:8])
            paths.update(commit_paths)
    return sorted(paths), lane_commits


def check_live_surface_diff() -> dict[str, Any]:
    workspace_paths = changed_paths_from_status()
    committed_paths, committed_ok = changed_paths_from_head_diff()
    recent_lane_paths, recent_lane_commits = recent_committed_lane_paths()
    committed_scope_relevant = committed_ok and any(path.startswith(LANE_PREFIX) for path in committed_paths)
    if recent_lane_paths:
        checked_paths = recent_lane_paths
        checked_scope = "recent_committed_lane_diffs"
    elif committed_scope_relevant:
        checked_paths = committed_paths
        checked_scope = "committed_diff_HEAD_parent"
    else:
        checked_paths = workspace_paths
        checked_scope = "workspace_status"
    forbidden = [path for path in checked_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    workspace_forbidden = [path for path in workspace_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    status_ok = not forbidden and (recent_lane_paths or committed_scope_relevant or not workspace_forbidden)
    return {
        "status": "PASS" if status_ok else "FAIL",
        "checked_scope": checked_scope,
        "recent_lane_commits": recent_lane_commits,
        "changed_paths": checked_paths,
        "workspace_changed_paths_observed": workspace_paths,
        "forbidden_live_surface_changed_paths": forbidden,
        "workspace_forbidden_live_surface_changed_paths": workspace_forbidden,
        "workspace_forbidden_paths_informational_only": bool(recent_lane_paths or committed_scope_relevant),
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def write_completion(verification: dict[str, Any]) -> None:
    builder_path = OUT_DIR / "build_g12_nofill_cat_v2_forensics_audit_2026_05_09.py"
    spec = importlib.util.spec_from_file_location("g12_nofill_cat_v2_forensics_audit_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audit builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_completion_audit(status="VERIFIED_BY_G12_FORENSICS_AUDIT_VERIFIER", verification=verification)


def verify_audit(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    results: dict[str, Any] = {
        "artifact_presence": check_artifact_presence(),
        "json_parse": check_json_parse(),
        "markdown_promotion": check_markdown_promotion(),
    }
    items = payloads()
    if results["json_parse"]["status"] == "PASS":
        results.update(
            {
                "flags": check_flags(items),
                "decision": check_decision(items),
                "slices": check_slices(items),
                "label_learning": check_label_learning(items),
                "blocker_reject": check_blockers(items),
                "noleak_duplicate_source_future": check_noleak_future(items),
            }
        )
    results["py_compile"] = check_py_compile()
    results["live_surface_diff"] = check_live_surface_diff()
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "called with run_pytest=False"}
    status = "PASS" if all(item.get("status") in {"PASS", "SKIPPED"} for item in results.values() if isinstance(item, dict)) else "FAIL"
    verification = {
        "artifact_family": "G12_NOFILL_CAT_V2_FORENSICS_AUDIT_VERIFICATION",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "verification_status": {"status": status},
        "can_mark_goal_complete": status == "PASS",
        "results": results,
    }
    if write_audit:
        write_completion(verification)
    return verification


def main() -> int:
    report = verify_audit(run_pytest=True, write_audit=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
