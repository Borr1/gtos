#!/usr/bin/env python3
"""Verify the NOFILL CAT V3 quarantined categorical count packet."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
LANE_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET"
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_quarantined_categorical_count_packet/"

SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
EXPECTED_ROW_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_KEY_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_GROUP_LABEL_COUNTS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 7,
}

JSON_ARTIFACTS = [
    f"NOFILL_CAT_V3_COUNT_CONTEXT_ANCHOR_{DATE}.json",
    f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.json",
    f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.json",
    f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.json",
]
JSONL_ARTIFACTS = [
    f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl",
    f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl",
]
MD_ARTIFACTS = [
    f"NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_GOAL_PROMPT_{DATE}.md",
    f"NOFILL_CAT_V3_COUNT_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.md",
    f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V3_LABEL_FAMILY_INTERPRETATION_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.md",
    f"NOFILL_CAT_V3_COUNT_NEXT_G12_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09.py",
    "verify_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09.py",
    "test_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "tests/canary",
)
ALLOWED_CONTEXT_REFRESH = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}


def read_json(name: str) -> dict[str, Any]:
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(name: str) -> list[dict[str, Any]]:
    rows = []
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def payloads() -> dict[str, Any]:
    data: dict[str, Any] = {name: read_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}
    for name in JSONL_ARTIFACTS:
        if (OUT_DIR / name).exists():
            data[name] = read_jsonl(name)
    return data


def artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + JSONL_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def json_parse() -> dict[str, Any]:
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            read_json(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    for name in JSONL_ARTIFACTS:
        try:
            read_jsonl(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def markdown_posture() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if not path.exists() or PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_no_promotion_verdict": missing}


def flags(items: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for name, payload in items.items():
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            row_id = candidate.get("packet_row_id", "artifact")
            if candidate.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{name}:{row_id}:promotion_verdict")
            if candidate.get("validation_safe") is not False:
                issues.append(f"{name}:{row_id}:validation_safe")
            if candidate.get("outcome_review_opened") is not False:
                issues.append(f"{name}:{row_id}:outcome_review_opened")
            if candidate.get("live_effect") is not False:
                issues.append(f"{name}:{row_id}:live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def objective_coverage(items: dict[str, Any]) -> dict[str, Any]:
    issues = []
    accepted = items[f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl"]
    exclusions = items[f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl"]
    count = items[f"NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_{DATE}.json"]
    duplicate = items[f"NOFILL_CAT_V3_DUPLICATE_CONCENTRATION_DIAGNOSTICS_{DATE}.json"]
    overlap = items[f"NOFILL_CAT_V3_REJECT_OVERLAP_ANTI_LAUNDERING_AUDIT_{DATE}.json"]
    source = items[f"NOFILL_CAT_V3_COUNT_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"]
    saturation = items[f"NOFILL_CAT_V3_COUNT_SATURATION_REVIEW_{DATE}.json"]

    accepted_ids = {row["packet_row_id"] for row in accepted}
    exclusion_ids = {row["packet_row_id"] for row in exclusions}
    if len(accepted) != 225 or len(accepted_ids) != 225:
        issues.append(f"accepted_row_count={len(accepted)} unique={len(accepted_ids)}")
    if len(exclusions) != 73 or len(exclusion_ids) != 73:
        issues.append(f"exclusion_row_count={len(exclusions)} unique={len(exclusion_ids)}")
    if accepted_ids & exclusion_ids:
        issues.append("accepted_exclusion_id_overlap")
    if accepted_ids & SOURCE_CONTROL_ROWS:
        issues.append("source_control_rows_in_accepted")
    if accepted_ids & SOURCE_IMPOSSIBLE_ROWS:
        issues.append("source_impossible_rows_in_accepted")
    if not SOURCE_CONTROL_ROWS <= exclusion_ids:
        issues.append("source_control_rows_missing_from_exclusions")
    if not SOURCE_IMPOSSIBLE_ROWS <= exclusion_ids:
        issues.append("source_impossible_rows_missing_from_exclusions")

    for row in accepted:
        if row["v3_terminal_family"] != "accepted":
            issues.append(f"{row['packet_row_id']}:nonaccepted_in_accepted_rows")
        if row["source_safe_input_only"] is not True:
            issues.append(f"{row['packet_row_id']}:source_safe_input_only_not_true")
        if row["label_class"] != "input_only_categorical":
            issues.append(f"{row['packet_row_id']}:label_class_not_input_only")
        if row["row_level_count_member"] is not True:
            issues.append(f"{row['packet_row_id']}:row_level_member_not_true")
    for row in exclusions:
        if not row["excluded_before_any_count"]:
            issues.append(f"{row['packet_row_id']}:not_excluded_before_count")
        if row["row_level_count_member"] or row["nofill_duplicate_key_count_member"] or row["duplicate_group_id_count_member"]:
            issues.append(f"{row['packet_row_id']}:exclusion_denominator_member")

    if count["accepted_row_level_total"] != 225:
        issues.append("count_ledger_accepted_total")
    if count["primary_unique_nofill_duplicate_key_total"] != 182:
        issues.append("count_ledger_primary_duplicate_total")
    if count["secondary_unique_duplicate_group_id_total"] != 139:
        issues.append("count_ledger_secondary_group_total")
    if count["row_level_label_counts"] != EXPECTED_ROW_LABEL_COUNTS:
        issues.append("row_level_label_counts_mismatch")
    if count["primary_nofill_duplicate_key_label_counts"] != EXPECTED_KEY_LABEL_COUNTS:
        issues.append("primary_duplicate_key_label_counts_mismatch")
    if count["secondary_duplicate_group_id_label_counts"] != EXPECTED_GROUP_LABEL_COUNTS:
        issues.append("secondary_duplicate_group_label_counts_mismatch")
    if "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject" not in count["universe_equation_asserted_before_counts"]:
        issues.append("universe_equation_not_asserted")

    conflict = duplicate["conflict_audit"]
    for key in (
        "accepted_duplicate_key_label_conflict_count",
        "accepted_duplicate_key_source_geometry_conflict_count",
        "accepted_duplicate_key_source_ordering_blocker_count",
        "accepted_duplicate_key_denominator_conflict_count",
    ):
        if conflict[key] != 0:
            issues.append(f"blocking_conflict_nonzero:{key}")
    if duplicate["accepted_noncanonical_projection_count"] != 43:
        issues.append("accepted_noncanonical_projection_count")
    if duplicate["primary_unique_nofill_duplicate_key_total"] != 182:
        issues.append("duplicate_primary_total")
    if duplicate["secondary_unique_duplicate_group_id_total"] != 139:
        issues.append("duplicate_secondary_total")

    if overlap["reject_key_overlap_with_accepted_count"] != 47:
        issues.append("reject_key_overlap_count_not_47")
    if overlap["reject_group_overlap_with_accepted_count"] != 47:
        issues.append("reject_group_overlap_count_not_47")
    if overlap["source_control_key_overlap_with_accepted"]:
        issues.append("source_control_key_overlap")
    if overlap["source_impossible_key_overlap_with_accepted"]:
        issues.append("source_impossible_key_overlap")
    if any(value != 0 for key, value in overlap["denominator_effect"].items() if key.endswith("_delta_from_rejects")):
        issues.append("reject_denominator_delta_nonzero")

    if source["status"] != "PASS":
        issues.append("source_hash_noleak_status_not_pass")
    if source["source_schema_recheck"]["strict_failure_count"] != 0:
        issues.append("strict_source_hash_failures")
    if source["source_schema_recheck"]["missing_record_count"] != 0:
        issues.append("missing_source_hash_records")
    if source["forbidden_row_key_hit_count"] != 0 or source["forbidden_row_string_hit_count"] != 0:
        issues.append("forbidden_row_hits")
    if source["safe_flag_issue_packet_row_ids"]:
        issues.append("safe_flag_issues")

    if saturation["status"] != "PASS":
        issues.append("saturation_status_not_pass")
    if saturation["same_evidence_class_status"] != "SATURATED_FOR_COUNT_PACKET":
        issues.append("saturation_status_not_saturated")
    if len(saturation["questions"]) < 12:
        issues.append("saturation_question_count")

    next_prompt = (OUT_DIR / f"NOFILL_CAT_V3_COUNT_NEXT_G12_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")
    for required in (
        "G12_NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_COUNT_PACKET_AUDIT",
        "225 accepted",
        "182 nofill_duplicate_key",
        "139 duplicate_group_id",
        "47 reject-overlap",
        "NO_PROMOTION_VERDICT",
    ):
        if required not in next_prompt:
            issues.append(f"next_prompt_missing:{required}")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def py_compile_check() -> dict[str, Any]:
    errors = []
    temp_dir = OUT_DIR / "_py_compile_tmp"
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(exist_ok=True)
    try:
        for name in PY_FILES:
            try:
                py_compile.compile(str(OUT_DIR / name), cfile=str(temp_dir / f"{name}.pyc"), doraise=True)
            except Exception as exc:
                errors.append({"path": name, "error": str(exc)})
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _names_from_proc(args: list[str]) -> list[str]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def _porcelain_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    paths = []
    if proc.returncode != 0:
        return paths
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return paths


def live_surface_diff() -> dict[str, Any]:
    workspace_paths = sorted(set(_porcelain_paths()))
    cached_paths = sorted(set(_names_from_proc(["git", "diff", "--cached", "--name-only"])))
    head_paths = sorted(set(_names_from_proc(["git", "diff", "--name-only", "HEAD^1", "HEAD"])))

    if cached_paths and any(path.startswith(LANE_PREFIX) or path in ALLOWED_CONTEXT_REFRESH for path in cached_paths):
        checked_scope = "staged_diff"
        checked_paths = cached_paths
    elif not any(path.startswith(LANE_PREFIX) for path in workspace_paths) and any(path.startswith(LANE_PREFIX) for path in head_paths):
        checked_scope = "committed_diff_HEAD_parent"
        checked_paths = head_paths
    else:
        checked_scope = "workspace_status"
        checked_paths = workspace_paths

    forbidden = sorted({path for path in checked_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)})
    outside_allowed = sorted(
        {
            path
            for path in checked_paths
            if not path.startswith(LANE_PREFIX) and path not in ALLOWED_CONTEXT_REFRESH
        }
    )
    return {
        "status": "PASS" if not forbidden and not outside_allowed else "FAIL",
        "checked_scope": checked_scope,
        "checked_paths": checked_paths,
        "forbidden_live_surface_changed_paths": forbidden,
        "outside_allowed_scope_paths": outside_allowed,
        "workspace_paths_informational_only": workspace_paths,
        "staged_paths_informational_only": cached_paths,
        "head_parent_diff_paths_informational_only": head_paths,
        "checked_forbidden_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def artifact_commit_check(require_committed: bool = True) -> dict[str, Any]:
    expected_paths = [LANE_PREFIX + name for name in JSON_ARTIFACTS + JSONL_ARTIFACTS + MD_ARTIFACTS + PY_FILES]
    if not require_committed:
        return {
            "status": "SKIPPED",
            "reason": "require_committed=False; pre-commit verification",
            "expected_paths": expected_paths,
        }
    tracked = set(_names_from_proc(["git", "ls-files", "--", LANE_PREFIX]))
    missing_tracked = [path for path in expected_paths if path not in tracked]
    dirty_paths = set(_names_from_proc(["git", "diff", "--name-only", "--", LANE_PREFIX]))
    dirty_paths.update(_names_from_proc(["git", "diff", "--cached", "--name-only", "--", LANE_PREFIX]))
    dirty_expected = sorted(path for path in expected_paths if path in dirty_paths)
    return {
        "status": "PASS" if not missing_tracked and not dirty_expected else "FAIL",
        "expected_paths": expected_paths,
        "missing_tracked_paths": missing_tracked,
        "dirty_expected_paths": dirty_expected,
        "tracked_lane_path_count": len(tracked),
    }


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("NOFILL_CAT_V3_COUNT_PACKET_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "NOFILL_CAT_V3_COUNT_PACKET_SKIP_NESTED_PYTEST=1"}
    temp_dir = OUT_DIR / "_pytest_tmp"
    shutil.rmtree(temp_dir, ignore_errors=True)
    cmd = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        str(OUT_DIR / f"test_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09.py"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(temp_dir),
    ]
    env = dict(os.environ)
    env["NOFILL_CAT_V3_COUNT_PACKET_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, env=env)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": "pytest passed" if proc.returncode == 0 else proc.stdout[-4000:],
        "stderr_tail": "" if proc.returncode == 0 else proc.stderr[-4000:],
    }


def write_completion_audit(items: dict[str, Any], results: dict[str, Any]) -> None:
    name = f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.json"
    audit = items[name]
    failures = [
        key
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    ]
    commit_status = results.get("artifact_commit_check", {}).get("status")
    if failures:
        completion_status = "FAIL_COUNT_PACKET_VERIFICATION"
        can_complete = False
        missing = [f"Verifier failures: {', '.join(failures)}"]
    elif commit_status == "PASS":
        completion_status = "PASS_COUNT_PACKET_CONTROL_LANE"
        can_complete = True
        missing = []
    else:
        completion_status = "PASS_VERIFICATION_PENDING_COMMIT"
        can_complete = False
        missing = ["Scoped artifacts are not yet committed."]

    audit["verification_results"] = results
    audit["completion_status"] = completion_status
    audit["can_mark_goal_complete"] = can_complete
    audit["missing_incomplete_or_weak_requirements"] = missing
    for item in audit["prompt_to_artifact_checklist"]:
        if item["requirement"] == "Scoped commit completed":
            item["status"] = "PASS" if commit_status == "PASS" else "PENDING_COMMIT"
            item["evidence"] = "artifact_commit_check"
        else:
            item["status"] = "PASS" if not failures else "RECHECK_REQUIRED"
    (OUT_DIR / name).write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    lines = [
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        f"Completion status: `{completion_status}`",
        f"Can mark goal complete: `{str(can_complete).lower()}`",
        "",
        "## Objective Restatement",
        "",
        audit["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    lines.extend(["", "## Verification", ""])
    for key, value in results.items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`: `{value.get('status')}`")
    (OUT_DIR / f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.md").write_text(
        "# NOFILL CAT V3 Count Completion Audit\n\n" + "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def verify_packet(run_pytest: bool = True, write_audit: bool = True, require_committed: bool = True) -> dict[str, Any]:
    presence = artifact_presence()
    parse = json_parse()
    items = payloads() if parse["status"] == "PASS" else {}
    results: dict[str, Any] = {
        "artifact_presence": presence,
        "json_parse": parse,
        "markdown_posture": markdown_posture(),
    }
    if items:
        results["flags"] = flags(items)
        results["objective_coverage"] = objective_coverage(items)
    else:
        results["flags"] = {"status": "FAIL", "issues": ["json_parse_failed"]}
        results["objective_coverage"] = {"status": "FAIL", "issues": ["json_parse_failed"]}
    results["py_compile"] = py_compile_check()
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "run_pytest=False"}
    results["live_surface_diff"] = live_surface_diff()
    results["artifact_commit_check"] = artifact_commit_check(require_committed=require_committed)

    failures = [
        key
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    ]
    results["verification_status"] = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "can_mark_goal_complete": not failures and results["artifact_commit_check"]["status"] == "PASS",
    }
    if write_audit and items:
        write_completion_audit(items, results)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--no-require-committed", action="store_true")
    args = parser.parse_args()
    results = verify_packet(
        run_pytest=not args.skip_pytest,
        write_audit=not args.no_write,
        require_committed=not args.no_require_committed,
    )
    print(json.dumps({"verification_status": results["verification_status"], "results": results}, indent=2, sort_keys=True, default=str))
    return 0 if results["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
