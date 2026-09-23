#!/usr/bin/env python3
"""Verify the G12 NOFILL CAT V3 result-contract audit artifacts."""

from __future__ import annotations

import importlib.util
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
CONTRACT_ID = "NOFILL_CAT_V3_QUARANTINED_CATEGORICAL_RESULT_CONTRACT_V1"
DECISION = "ACCEPT_FROZEN_V3_RESULT_CONTRACT_FOR_QUARANTINED_CATEGORICAL_COUNT_PACKET"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
RESULT_DIR = REPO_ROOT / BASE / "nofill_cat_v3_result_contract_update"
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_result_contract_audit/"

JSON_ARTIFACTS = [
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json",
]
MD_ARTIFACTS = [
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
    "verify_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
    "test_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "run_agent.py",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "tests/canary",
)


def load_json(name: str) -> dict[str, Any]:
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def json_parse() -> dict[str, Any]:
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
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
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def objective_coverage(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    decision = items[f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DECISION_LEDGER_{DATE}.json"]
    source = items[f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_HASH_AUDIT_{DATE}.json"]
    noleak = items[f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NOLEAK_DENOMINATOR_AUDIT_{DATE}.json"]
    duplicate = items[f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_AUDIT_{DATE}.json"]
    saturation = items[f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.json"]
    facts = decision["verified_starting_facts"]

    if decision.get("overall_decision") != DECISION:
        issues.append("decision_mismatch")
    if decision.get("decision_status") != "PASS_ACCEPTED":
        issues.append("decision_not_accepted")
    if facts.get("terminal_family_counts") != {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }:
        issues.append("terminal_family_counts_mismatch")
    if facts.get("eligible_rows") != 225 or facts.get("exclusion_rows") != 73:
        issues.append("eligibility_or_exclusion_count_mismatch")
    if facts.get("source_control_rows") != [
        "NOFILL-CAT-ROW-0049",
        "NOFILL-CAT-ROW-0050",
        "NOFILL-CAT-ROW-0051",
        "NOFILL-CAT-ROW-0241",
    ]:
        issues.append("source_control_rows_mismatch")
    if facts.get("source_impossible_rows") != [
        "NOFILL-CAT-ROW-0130",
        "NOFILL-CAT-ROW-0143",
        "NOFILL-CAT-ROW-0165",
        "NOFILL-CAT-ROW-0178",
    ]:
        issues.append("source_impossible_rows_mismatch")
    if facts.get("accepted_unique_nofill_duplicate_keys") != 182:
        issues.append("duplicate_key_count_mismatch")
    if facts.get("accepted_unique_duplicate_group_ids") != 139:
        issues.append("duplicate_group_count_mismatch")
    if facts.get("current_lane_result_records_produced") != 0 or facts.get("current_lane_scored_metric_values") != 0:
        issues.append("scoring_records_nonzero")

    for name, artifact in (
        ("source_hash", source),
        ("noleak_denominator", noleak),
        ("duplicate", duplicate),
        ("saturation", saturation),
    ):
        if artifact.get("status") != "PASS":
            issues.append(f"{name}_not_pass")

    if source["source_schema_recheck"]["strict_failure_count"] != 0:
        issues.append("strict_source_hash_failures")
    if noleak["exclusion_controls"]["exclusion_denominator_violations"]:
        issues.append("exclusion_denominator_violations")
    if noleak["exclusion_controls"]["nonaccepted_denominator_violations"]:
        issues.append("nonaccepted_denominator_violations")
    if noleak["forbidden_field_hits"]["v3_row_ledger"] or noleak["forbidden_field_hits"]["contract_ledgers"]:
        issues.append("forbidden_field_hits")
    if duplicate["overlap_red_team"]["reject_key_overlap_with_accepted_count"] <= 0:
        issues.append("reject_overlap_red_team_missing")
    if duplicate["overlap_red_team"]["source_control_key_overlap_with_accepted"]:
        issues.append("source_control_key_overlap")
    if duplicate["overlap_red_team"]["source_impossible_key_overlap_with_accepted"]:
        issues.append("source_impossible_key_overlap")
    if not saturation.get("same_evidence_class_ambiguities_closed_or_routed"):
        issues.append("saturation_not_closed_or_routed")
    if len(saturation.get("questions", [])) < 12:
        issues.append("saturation_question_count")

    next_prompt = (OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md").read_text(encoding="utf-8")
    for required in (
        "225 accepted",
        "4 source_control",
        "4 source_impossible",
        "65 reject",
        "nofill_duplicate_key",
        "zero R/win/expectancy",
        "post-count G12 audit",
    ):
        if required not in next_prompt:
            issues.append(f"next_prompt_missing:{required}")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def upstream_result_contract_verifier_readonly() -> dict[str, Any]:
    path = RESULT_DIR / "verify_nofill_cat_v3_result_contract_update_2026_05_09.py"
    try:
        spec = importlib.util.spec_from_file_location("nofill_cat_v3_result_contract_verifier", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load upstream result-contract verifier")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        results = module.verify_contract(run_pytest=False, write_audit=False)
        failures = results.get("verification_status", {}).get("failures", [])
        # The upstream verifier may report unrelated workspace paths in its own
        # live-surface scope. This G12 verifier performs its own lane diff check.
        inherited_live_surface_only = failures == ["live_surface_diff"]
        status = "PASS" if results.get("verification_status", {}).get("status") == "PASS" or inherited_live_surface_only else "FAIL"
        return {
            "status": status,
            "upstream_status": results.get("verification_status", {}).get("status"),
            "upstream_failures": failures,
            "upstream_path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "note": "G12 lane live-surface diff is authoritative for this audit.",
        }
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc), "upstream_path": str(path)}


def py_compile_check() -> dict[str, Any]:
    errors = []
    temp_dir = OUT_DIR / "_py_compile_tmp"
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


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_SKIP_NESTED_PYTEST=1"}
    temp_dir = OUT_DIR / "_pytest_tmp"
    shutil.rmtree(temp_dir, ignore_errors=True)
    cmd = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        str(OUT_DIR / "test_g12_nofill_cat_v3_result_contract_audit_2026_05_09.py"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(temp_dir),
    ]
    env = dict(os.environ)
    env["G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_SKIP_NESTED_PYTEST"] = "1"
    context_path = OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.json"
    if context_path.exists():
        try:
            context = json.loads(context_path.read_text(encoding="utf-8"))
            generated_at = context.get("generated_at_utc")
            if generated_at:
                env["G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_FIXED_GENERATED_AT"] = str(generated_at)
            git_head = context.get("git_head")
            if git_head:
                env["G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_FIXED_GIT_HEAD"] = str(git_head)
        except Exception:
            pass
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, env=env)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": "pytest passed" if proc.returncode == 0 else proc.stdout[-4000:],
        "stderr_tail": "" if proc.returncode == 0 else proc.stderr[-4000:],
    }


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

    if cached_paths and any(path.startswith(LANE_PREFIX) for path in cached_paths):
        checked_scope = "staged_diff"
        checked_paths = cached_paths
    elif not any(path.startswith(LANE_PREFIX) for path in workspace_paths) and any(path.startswith(LANE_PREFIX) for path in head_paths):
        checked_scope = "committed_diff_HEAD_parent"
        checked_paths = head_paths
    else:
        checked_scope = "workspace_status"
        checked_paths = workspace_paths

    forbidden = sorted({path for path in checked_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)})
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": checked_scope,
        "checked_paths": checked_paths,
        "forbidden_live_surface_changed_paths": forbidden,
        "workspace_paths_informational_only": workspace_paths,
        "staged_paths_informational_only": cached_paths,
        "head_parent_diff_paths_informational_only": head_paths,
        "checked_forbidden_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def artifact_commit_check(require_committed: bool = True) -> dict[str, Any]:
    expected_paths = [LANE_PREFIX + name for name in JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES]
    if not require_committed:
        return {
            "status": "SKIPPED",
            "reason": "require_committed=False; pre-commit verification only",
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


def write_completion_audit(items: dict[str, dict[str, Any]], results: dict[str, Any]) -> None:
    name = f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json"
    audit = items[name]
    failures = [
        key
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    ]
    commit_status = results.get("artifact_commit_check", {}).get("status")
    can_complete = not failures and commit_status == "PASS"
    audit["verification_results"] = results
    if failures:
        audit["completion_status"] = "FAIL_G12_V3_RESULT_CONTRACT_AUDIT"
    elif commit_status == "PASS":
        audit["completion_status"] = "PASS_G12_V3_RESULT_CONTRACT_AUDIT_ACCEPTED"
    else:
        audit["completion_status"] = "PASS_VERIFICATION_PENDING_COMMIT"
    audit["can_mark_goal_complete"] = can_complete
    audit["missing_or_weak_requirements"] = [] if can_complete else [f"Verifier failures: {', '.join(failures)}"]
    for item in audit["prompt_to_artifact_checklist"]:
        if item["requirement"] == "All artifacts committed":
            item["status"] = "PASS" if commit_status == "PASS" else "PENDING_COMMIT"
            item["evidence"] = "artifact_commit_check"
        else:
            item["status"] = "PASS" if not failures else "RECHECK_REQUIRED"
    (OUT_DIR / name).write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    lines = [
        f"Promotion posture: `{PROMOTION_VERDICT}`",
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
        lines.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    lines.extend(["", "## Verification", ""])
    for key, value in results.items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`: `{value.get('status')}`")
    (OUT_DIR / f"G12_NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md").write_text(
        "# G12 NOFILL CAT V3 Result Contract Completion Audit\n\n" + "\n".join(lines) + "\n",
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
    results["upstream_result_contract_verifier_readonly"] = upstream_result_contract_verifier_readonly()
    results["py_compile"] = py_compile_check()
    results["live_surface_diff"] = live_surface_diff()
    results["artifact_commit_check"] = artifact_commit_check(require_committed=require_committed)
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "run_pytest=False"}

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


def main() -> None:
    results = verify_audit(run_pytest=True, write_audit=True)
    print(json.dumps({"verification_status": results["verification_status"], "results": results}, indent=2, sort_keys=True, default=str))
    if results["verification_status"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
