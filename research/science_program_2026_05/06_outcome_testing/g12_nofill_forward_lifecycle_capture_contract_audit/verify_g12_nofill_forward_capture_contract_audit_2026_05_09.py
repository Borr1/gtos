#!/usr/bin/env python3
"""Verify the G12 NOFILL forward lifecycle capture contract audit artifacts."""

from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_VERDICT = "ACCEPT_WITH_EXACT_CONTRACT_BLOCKERS"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/"
ALLOWED_CONTEXT_PATHS = {
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
}
FORBIDDEN_LIVE_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "knowledge_base/",
    "pipeline_state/",
)

JSON_ARTIFACTS = [
    f"G12_NOFILL_FORWARD_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json",
]
MD_ARTIFACTS = [
    f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_FORWARD_BACKLOG_AND_IMPLEMENTATION_AUDIT_{DATE}.md",
    f"G12_NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_{DATE}.md",
    f"G12_NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_g12_nofill_forward_capture_contract_audit_2026_05_09.py",
    "verify_g12_nofill_forward_capture_contract_audit_2026_05_09.py",
    "test_g12_nofill_forward_capture_contract_audit_2026_05_09.py",
]


def load_json(name: str) -> dict[str, Any]:
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def names_from_proc(args: list[str]) -> list[str]:
    proc = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def porcelain_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    paths: list[str] = []
    if proc.returncode != 0:
        return paths
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/").rstrip("/"))
    return paths


def artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def json_parse() -> dict[str, Any]:
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
        except Exception as exc:  # noqa: BLE001
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def markdown_posture() -> dict[str, Any]:
    missing = []
    required_literals = [
        PROMOTION_VERDICT,
        "validation_safe: `false`",
        "outcome_review_opened: `false`",
        "live_effect: `false`",
        "opens_result_scoring: `false`",
        "changes_live_trading_behavior: `false`",
    ]
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        for literal in required_literals:
            if literal not in text:
                missing.append({"path": name, "missing": literal})
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def flags(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for name, payload in items.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{name}:promotion_verdict")
        if payload.get("validation_safe") is not False:
            issues.append(f"{name}:validation_safe")
        if payload.get("outcome_review_opened") is not False:
            issues.append(f"{name}:outcome_review_opened")
        if payload.get("live_effect") is not False:
            issues.append(f"{name}:live_effect")
        if payload.get("opens_result_scoring") is not False:
            issues.append(f"{name}:opens_result_scoring")
        if payload.get("changes_live_trading_behavior") is not False:
            issues.append(f"{name}:changes_live_trading_behavior")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def objective_coverage(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues: list[str] = []
    context = items[f"G12_NOFILL_FORWARD_CONTEXT_ANCHOR_{DATE}.json"]
    decision = items[f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json"]
    schema = items[f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json"]
    noleak = items[f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json"]
    duplicate = items[f"G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json"]

    if decision.get("terminal_g12_verdict") != TERMINAL_VERDICT:
        issues.append("terminal_verdict_not_accept_with_blockers")
    if decision.get("decision_status") != "PASS_ACCEPTED_WITH_BLOCKERS":
        issues.append("decision_status_not_pass")
    if len(decision.get("exact_contract_blockers", [])) != 3:
        issues.append("exact_contract_blockers_missing")
    if not context.get("input_files_read_or_inventoried"):
        issues.append("input_manifest_missing")
    if context.get("required_forward_inputs_missing"):
        issues.append("required_forward_inputs_missing")

    if schema.get("field_count") != 80:
        issues.append("schema_field_count_mismatch")
    if schema.get("family_count") != 12:
        issues.append("schema_family_count_mismatch")
    if schema.get("status") != "PASS_WITH_EXACT_CONTRACT_BLOCKERS":
        issues.append("schema_not_pass_with_blockers")
    coverage = schema.get("coverage_assessment", {})
    for key in (
        "source_asof_timestamp_fields",
        "no_leak_exclusions",
        "duplicate_denominator_controls",
        "source_provenance_hash_parser",
        "blocker_patterns",
    ):
        if coverage.get(key) != "PASS":
            issues.append(f"schema_coverage_{key}")
    if coverage.get("capture_latency") != "PARTIAL_WITH_BLOCKER":
        issues.append("capture_latency_blocker_not_detected")
    if coverage.get("cost_spread_slippage_execution_observability") != "PARTIAL_WITH_BLOCKER":
        issues.append("cost_execution_blocker_not_detected")

    if noleak.get("status") != "PASS_WITH_RAW_SOURCE_PROJECTION_REQUIRED":
        issues.append("noleak_not_pass")
    if noleak.get("artifact_flag_issues"):
        issues.append("forward_artifact_flag_issues")
    if not noleak.get("raw_log_hazards_requiring_allowlist_projection"):
        issues.append("raw_log_projection_hazards_not_detected")
    if not noleak.get("local_heavy_data_search", {}).get("searched_roots"):
        issues.append("local_heavy_data_not_searched")

    if duplicate.get("status") != "PASS":
        issues.append("duplicate_not_pass")
    if duplicate["universe_equation"]["total"] != 298:
        issues.append("universe_total_mismatch")
    if duplicate["universe_equation"]["terminal_counts"] != {
        "accepted": 225,
        "blocked": 0,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }:
        issues.append("terminal_counts_mismatch")
    if duplicate["denominators"]["row_level_accepted"] != 225:
        issues.append("row_level_accepted_mismatch")
    if duplicate["denominators"]["unique_nofill_duplicate_key"] != 182:
        issues.append("duplicate_key_mismatch")
    if duplicate["denominators"]["unique_duplicate_group_id"] != 139:
        issues.append("duplicate_group_mismatch")
    if duplicate["reject_overlap"]["reject_key_overlap_count"] != 47:
        issues.append("reject_overlap_key_mismatch")
    if duplicate["mandatory_exclusions"]["exclusion_denominator_violations"]:
        issues.append("exclusion_denominator_violation")
    if duplicate["accepted_flag_issues"]:
        issues.append("accepted_flag_issue")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def py_compile_check() -> dict[str, Any]:
    errors = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
        except Exception as exc:  # noqa: BLE001
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def run_focused_pytest() -> dict[str, Any]:
    tmp = OUT_DIR / "_pytest_tmp"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    cmd = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        str(OUT_DIR / f"test_g12_nofill_forward_capture_contract_audit_2026_05_09.py"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(tmp),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    shutil.rmtree(tmp, ignore_errors=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": "pytest passed" if proc.returncode == 0 else proc.stdout[-4000:],
        "stderr_tail": "" if proc.returncode == 0 else proc.stderr[-4000:],
    }


def live_surface_diff() -> dict[str, Any]:
    workspace_paths = sorted(set(porcelain_paths()))
    cached_paths = sorted(set(names_from_proc(["git", "diff", "--cached", "--name-only"])))
    head_paths = sorted(set(names_from_proc(["git", "diff", "--name-only", "HEAD^1", "HEAD"])))
    if cached_paths:
        checked_scope = "staged_diff"
        checked_paths = cached_paths
    elif any(path.startswith(LANE_PREFIX) for path in workspace_paths):
        checked_scope = "workspace_status"
        checked_paths = workspace_paths
    elif any(path.startswith(LANE_PREFIX) or path in ALLOWED_CONTEXT_PATHS for path in head_paths):
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
            if path
            and not path.startswith(LANE_PREFIX)
            and path not in ALLOWED_CONTEXT_PATHS
            and not path.startswith("?? ")
        }
    )
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": checked_scope,
        "checked_path_count": len(checked_paths),
        "outside_allowed_scope_in_checked_paths": outside_allowed,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def artifact_commit_check(require_committed: bool = True) -> dict[str, Any]:
    expected_paths = [LANE_PREFIX + name for name in JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES]
    if not require_committed:
        return {"status": "SKIPPED", "reason": "pre-commit verification", "expected_paths": expected_paths}
    tracked = set(names_from_proc(["git", "ls-files", "--", LANE_PREFIX]))
    missing_tracked = [path for path in expected_paths if path not in tracked]
    dirty_paths = set(names_from_proc(["git", "diff", "--name-only", "--", LANE_PREFIX]))
    dirty_paths.update(names_from_proc(["git", "diff", "--cached", "--name-only", "--", LANE_PREFIX]))
    dirty_expected = sorted(path for path in expected_paths if path in dirty_paths)
    return {
        "status": "PASS" if not missing_tracked and not dirty_expected else "FAIL",
        "expected_paths": expected_paths,
        "missing_tracked_paths": missing_tracked,
        "dirty_expected_paths": dirty_expected,
        "tracked_lane_path_count": len(tracked),
    }


def final_git_show_scope_check(require_committed: bool = True) -> dict[str, Any]:
    if not require_committed:
        return {"status": "SKIPPED", "reason": "pre-commit verification"}
    paths = names_from_proc(["git", "show", "--name-only", "--format=", "HEAD"])
    outside_allowed = [
        path
        for path in paths
        if path and not path.startswith(LANE_PREFIX) and path not in ALLOWED_CONTEXT_PATHS
    ]
    forbidden = sorted({path for path in paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)})
    return {
        "status": "PASS" if not outside_allowed and not forbidden else "FAIL",
        "outside_allowed_scope": outside_allowed,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def write_completion_audit(items: dict[str, dict[str, Any]], results: dict[str, Any]) -> None:
    audit_name = f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json"
    audit = items[audit_name]
    failures = [
        key
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    ]
    commit_status = results.get("artifact_commit_check", {}).get("status")
    can_complete = not failures and commit_status == "PASS"
    if failures:
        audit["completion_status"] = "FAIL_G12_NOFILL_FORWARD_AUDIT_VERIFICATION"
    elif commit_status == "PASS":
        audit["completion_status"] = "PASS_G12_NOFILL_FORWARD_AUDIT_ACCEPTED_WITH_BLOCKERS"
    else:
        audit["completion_status"] = "PASS_VERIFICATION_PENDING_COMMIT"
    audit["can_mark_goal_complete"] = can_complete
    audit["verification_results"] = results
    audit["missing_incomplete_or_weak_requirements"] = [] if can_complete else [f"Pending/failing verifier items: {', '.join(failures) or commit_status}"]
    for item in audit["prompt_to_artifact_checklist"]:
        if item["id"] == "context_refresh_commit":
            item["status"] = "PENDING_CONTEXT_COMMIT" if not can_complete else "PASS_OR_SEPARATE_DOC_COMMIT_REQUIRED"
            item["evidence"] = "checked after research-context refresh commit"
        else:
            item["status"] = "PASS" if not failures else "RECHECK_REQUIRED"
            item["evidence"] = "objective_coverage and verifier results"
    (OUT_DIR / audit_name).write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    lines = [
        f"- audit_lane_id: `G12_NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT`",
        f"- promotion_verdict: `{PROMOTION_VERDICT}`",
        "- validation_safe: `false`",
        "- outcome_review_opened: `false`",
        "- live_effect: `false`",
        "- opens_result_scoring: `false`",
        "- changes_live_trading_behavior: `false`",
        "",
        f"Completion status: `{audit['completion_status']}`",
        f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`",
        "",
        "## Objective Restatement",
        "",
        audit["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` `{item['id']}`: {item['requirement']} ({item['evidence']})")
    lines.extend(["", "## Verification", ""])
    for key, value in results.items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`: `{value.get('status')}`")
    (OUT_DIR / f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.md").write_text(
        "# G12 NOFILL Forward Completion Audit 2026-05-09\n\n" + "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def verify_audit(run_pytest: bool = True, write_audit: bool = True, require_committed: bool = True) -> dict[str, Any]:
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
    results["final_git_show_scope_check"] = final_git_show_scope_check(require_committed=require_committed)

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
    results = verify_audit(
        run_pytest=not args.skip_pytest,
        write_audit=not args.no_write,
        require_committed=not args.no_require_committed,
    )
    print(json.dumps({"verification_status": results["verification_status"], "results": results}, indent=2, sort_keys=True, default=str))
    return 0 if results["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
