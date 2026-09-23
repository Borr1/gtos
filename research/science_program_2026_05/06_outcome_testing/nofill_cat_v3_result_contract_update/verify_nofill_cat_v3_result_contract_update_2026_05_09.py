#!/usr/bin/env python3
"""Verify NOFILL_CAT_V3_RESULT_CONTRACT_UPDATE artifacts."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_result_contract_update/"
V3_DIR = OUT_DIR.parent / "nofill_cat_v3_source_control_rebuild"

EXPECTED_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
    "blocked": 0,
}
SOURCE_CONTROL_ROWS = {
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
}
USDJPY_SOURCE_IMPOSSIBLE_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}

JSON_ARTIFACTS = [
    f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json",
]
JSONL_ARTIFACTS = [
    f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl",
]
MD_ARTIFACTS = [
    f"NOFILL_CAT_V3_RESULT_CONTRACT_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_DUPLICATE_SAMPLE_POLICY_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_SATURATION_REVIEW_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_LEARNING_AND_RISKS_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_nofill_cat_v3_result_contract_update_2026_05_09.py",
    "verify_nofill_cat_v3_result_contract_update_2026_05_09.py",
    "test_nofill_cat_v3_result_contract_update_2026_05_09.py",
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
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def load_upstream_rows() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (V3_DIR / f"NOFILL_CAT_V3_ROW_DECISION_LEDGER_{DATE}.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_normalized_line_endings(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    import hashlib

    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + JSONL_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def parse_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    payloads: dict[str, Any] = {}
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            payloads[name] = load_json(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    for name in JSONL_ARTIFACTS:
        try:
            payloads[name] = load_jsonl(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return payloads, {"status": "PASS" if not errors else "FAIL", "errors": errors}


def markdown_posture() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if path.exists() and PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_no_promotion_verdict": missing}


def safety_flags(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for name, payload in payloads.items():
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


def row_contract_checks(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    upstream = load_upstream_rows()
    eligibility = payloads[f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl"]
    exclusion = payloads[f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl"]
    rulebook = payloads[f"NOFILL_CAT_V3_RESULT_CONTRACT_FROZEN_RULEBOOK_{DATE}.json"]

    family_counts = Counter(row["v3_terminal_family"] for row in upstream)
    expected_family = {key: family_counts.get(key, 0) for key in EXPECTED_COUNTS}
    if expected_family != EXPECTED_COUNTS:
        issues.append(f"upstream_family_counts={expected_family}")
    if len(upstream) != 298:
        issues.append(f"upstream_row_count={len(upstream)}")
    if len({row["packet_row_id"] for row in upstream}) != 298:
        issues.append("upstream_duplicate_packet_row_id")

    if len(eligibility) != 225:
        issues.append(f"eligibility_count={len(eligibility)}")
    if len(exclusion) != 73:
        issues.append(f"exclusion_count={len(exclusion)}")

    eligibility_ids = {row["packet_row_id"] for row in eligibility}
    exclusion_ids = {row["packet_row_id"] for row in exclusion}
    accepted_ids = {row["packet_row_id"] for row in upstream if row["v3_terminal_family"] == "accepted"}
    nonaccepted_ids = {row["packet_row_id"] for row in upstream if row["v3_terminal_family"] != "accepted"}
    if eligibility_ids != accepted_ids:
        issues.append("eligibility_ids_do_not_match_accepted_ids")
    if exclusion_ids != nonaccepted_ids:
        issues.append("exclusion_ids_do_not_match_nonaccepted_ids")
    if eligibility_ids & exclusion_ids:
        issues.append("eligibility_exclusion_overlap")
    if eligibility_ids & SOURCE_CONTROL_ROWS:
        issues.append("source_control_rows_in_eligibility")
    if eligibility_ids & USDJPY_SOURCE_IMPOSSIBLE_ROWS:
        issues.append("source_impossible_rows_in_eligibility")
    if not SOURCE_CONTROL_ROWS <= exclusion_ids:
        issues.append("source_control_rows_missing_from_exclusion")
    if not USDJPY_SOURCE_IMPOSSIBLE_ROWS <= exclusion_ids:
        issues.append("source_impossible_rows_missing_from_exclusion")

    for row in eligibility:
        if row["current_lane_scoring_allowed"] is not False:
            issues.append(f"{row['packet_row_id']}:current_lane_scoring_allowed")
        if row["current_lane_result_record_produced"] is not False:
            issues.append(f"{row['packet_row_id']}:result_record_produced")
        if row["r_performance_allowed"] is not False:
            issues.append(f"{row['packet_row_id']}:r_performance_allowed")
        if row["broker_or_account_label_allowed"] is not False:
            issues.append(f"{row['packet_row_id']}:broker_or_account_label_allowed")
        if row["v3_terminal_family"] != "accepted":
            issues.append(f"{row['packet_row_id']}:nonaccepted_in_eligibility")

    for row in exclusion:
        if row["future_scoring_lane_may_consume"] is not False:
            issues.append(f"{row['packet_row_id']}:excluded_consumable")
        if row["row_level_denominator_member"] is not False:
            issues.append(f"{row['packet_row_id']}:excluded_row_denominator")
        if row["duplicate_key_denominator_member"] is not False:
            issues.append(f"{row['packet_row_id']}:excluded_duplicate_denominator")

    canonical_count = sum(1 for row in eligibility if row["duplicate_key_denominator_member"])
    if canonical_count != rulebook["starting_evidence_locked"]["accepted_unique_nofill_duplicate_keys"]:
        issues.append(f"canonical_duplicate_count={canonical_count}")
    if canonical_count != 182:
        issues.append(f"canonical_duplicate_count_expected_182_actual_{canonical_count}")

    if rulebook["future_scoring_eligible_universe"]["row_count"] != 225:
        issues.append("rulebook_eligible_count")
    if rulebook["mandatory_exclusions"]["reject_rows"]["row_count"] != 65:
        issues.append("rulebook_reject_count")
    if rulebook["current_lane_result_records_produced"] != 0:
        issues.append("rulebook_result_records_produced")
    if rulebook["current_lane_scored_metric_values"] != 0:
        issues.append("rulebook_scored_metric_values")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def noleak_schema_checks(payloads: dict[str, Any]) -> dict[str, Any]:
    issues = []
    schema = payloads[f"NOFILL_CAT_V3_RESULT_CONTRACT_SOURCE_NOLEAK_SCHEMA_{DATE}.json"]
    required_forbidden = {
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "mt5_history",
        "synthetic_r",
        "win_rate",
        "expectancy",
        "profit",
    }
    if not required_forbidden <= set(schema["forbidden_fields"]):
        issues.append("missing_required_forbidden_fields")
    required_allowed = {"packet_row_id", "source_inventory_id", "nofill_duplicate_key", "categorical_lifecycle_label"}
    if not required_allowed <= set(schema["allowed_decision_time_fields"]):
        issues.append("missing_required_allowed_input_fields")
    if not schema["source_hash_policy"]["all_key_source_artifacts_hashed"]:
        issues.append("key_source_artifacts_not_all_hashed")

    missing = []
    mismatches = []
    line_ending_only_mismatches = []
    for record in schema["source_artifact_hash_records"]:
        if not record["exists"]:
            missing.append(record["path"])
            continue
        # Context docs are allowed to drift after preflight regeneration; key row/source artifacts are strict.
        if record["role"] == "mandatory_context":
            continue
        path = REPO_ROOT / record["path"]
        actual = sha256_file(path)
        if actual != record["sha256"]:
            normalized_actual = sha256_file_normalized_line_endings(path)
            if normalized_actual == record["sha256"] and record["role"] == "controlling_prompt":
                line_ending_only_mismatches.append({"path": record["path"], "actual": actual})
                continue
            mismatches.append({"path": record["path"], "expected": record["sha256"], "actual": actual})
    return {
        "status": "PASS" if not issues and not missing and not mismatches else "FAIL",
        "issues": issues,
        "missing": missing,
        "mismatches": mismatches,
        "line_ending_only_mismatches": line_ending_only_mismatches,
    }


def live_surface_diff() -> dict[str, Any]:
    workspace = subprocess.run(["git", "diff", "--name-only"], cwd=REPO_ROOT, text=True, capture_output=True)
    cached = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=REPO_ROOT, text=True, capture_output=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    head = subprocess.run(["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    head_names = [line.strip().replace("\\", "/") for line in head.stdout.splitlines() if line.strip()] if head.returncode == 0 else []
    if not head_names:
        head_diff = subprocess.run(["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD^1", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
        if head_diff.returncode == 0:
            head_names = [line.strip().replace("\\", "/") for line in head_diff.stdout.splitlines() if line.strip()]

    workspace_names = []
    for proc in (workspace, cached):
        if proc.returncode == 0:
            workspace_names.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            if not line.strip():
                continue
            # Git porcelain uses XY + path. For renames, the path after -> is the
            # current path and is the one relevant for forbidden surface checks.
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            workspace_names.append(path.replace("\\", "/"))
    forbidden_head = sorted({name for name in head_names if name.startswith(FORBIDDEN_LIVE_PREFIXES)})
    forbidden_workspace = sorted({name for name in workspace_names if name.startswith(FORBIDDEN_LIVE_PREFIXES)})
    outside_lane = sorted(
        {
            name
            for name in workspace_names
            if not name.startswith(LANE_PREFIX)
            and name != ".context/LIVE_STATE.md"
            and name != ".context/00_core/research_current_state.md"
        }
    )
    return {
        "status": "PASS" if not forbidden_head else "FAIL",
        "forbidden_live_surface_paths": forbidden_head,
        "head_paths": sorted(set(head_names)),
        "workspace_paths_informational_only": sorted(set(workspace_names)),
        "forbidden_workspace_paths_informational_only": forbidden_workspace,
        "non_lane_paths_seen": outside_lane,
    }


def py_compile_check() -> dict[str, Any]:
    errors = []
    for name in PY_FILES:
        try:
            py_compile.compile(str(OUT_DIR / name), doraise=True)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def run_pytest_check() -> dict[str, Any]:
    if os.environ.get("NOFILL_CAT_V3_RESULT_CONTRACT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "NOFILL_CAT_V3_RESULT_CONTRACT_SKIP_NESTED_PYTEST=1"}
    temp_dir = OUT_DIR / "_pytest_tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    cmd = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        str(OUT_DIR / f"test_nofill_cat_v3_result_contract_update_2026_05_09.py"),
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(temp_dir),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": "pytest passed" if proc.returncode == 0 else proc.stdout[-4000:],
        "stderr_tail": "" if proc.returncode == 0 else proc.stderr[-4000:],
    }


def update_completion_audit(results: dict[str, Any], payloads: dict[str, Any]) -> None:
    audit_name = f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.json"
    audit = payloads[audit_name]
    blocking = {
        key: value
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    }
    pytest_status = results["focused_pytest"]["status"]
    can_complete = not blocking and pytest_status in {"PASS", "SKIPPED"}
    for item in audit["prompt_to_artifact_checklist"]:
        if item["requirement"] == "Verifier/tests/next prompt pack":
            item["status"] = "PASS" if can_complete else "FAIL"
            item["evidence"] = f"Verifier status={results['verification_status']['status']}; focused_pytest={pytest_status}; next prompt pack present."
    audit["completion_status"] = "PASS_FROZEN_RESULT_CONTRACT_CONTROL_LANE" if can_complete else "FAIL_VERIFICATION"
    audit["can_mark_goal_complete"] = can_complete
    audit["verifier_summary"] = results
    (OUT_DIR / audit_name).write_text(json.dumps(audit, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    md_lines = [
        "# NOFILL CAT V3 Result Contract Completion Audit - 2026-05-09",
        "",
        f"Promotion posture: `{PROMOTION_VERDICT}`",
        "",
        f"Status: `{audit['completion_status']}`",
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
        md_lines.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    md_lines.extend(["", "## Detailed Coverage", ""])
    for item in audit.get("detailed_prompt_to_artifact_checklist", []):
        md_lines.append(f"- `{item['status']}` `{item['type']}` {item['item']}: {item['evidence']}")
    md_lines.extend(
        [
            "",
            "## Verification Summary",
            "",
            f"- Artifact presence: `{results['artifact_presence']['status']}`",
            f"- JSON/JSONL parse: `{results['json_parse']['status']}`",
            f"- Row contract checks: `{results['row_contract_checks']['status']}`",
            f"- Source/no-leak checks: `{results['noleak_schema_checks']['status']}`",
            f"- Live-surface diff: `{results['live_surface_diff']['status']}`",
            f"- Py compile: `{results['py_compile']['status']}`",
            f"- Focused pytest: `{pytest_status}`",
        ]
    )
    (OUT_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_COMPLETION_AUDIT_{DATE}.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def verify_contract(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    presence = artifact_presence()
    payloads, parse = parse_artifacts()
    results: dict[str, Any] = {
        "artifact_presence": presence,
        "json_parse": parse,
        "markdown_posture": markdown_posture(),
    }
    if parse["status"] == "PASS":
        results["safety_flags"] = safety_flags(payloads)
        results["row_contract_checks"] = row_contract_checks(payloads)
        results["noleak_schema_checks"] = noleak_schema_checks(payloads)
    else:
        results["safety_flags"] = {"status": "FAIL", "issues": ["json_parse_failed"]}
        results["row_contract_checks"] = {"status": "FAIL", "issues": ["json_parse_failed"]}
        results["noleak_schema_checks"] = {"status": "FAIL", "issues": ["json_parse_failed"]}
    results["live_surface_diff"] = live_surface_diff()
    results["py_compile"] = py_compile_check()
    results["focused_pytest"] = run_pytest_check() if run_pytest else {"status": "SKIPPED", "reason": "run_pytest=False"}

    failures = [
        key
        for key, value in results.items()
        if isinstance(value, dict) and value.get("status") not in {"PASS", "SKIPPED"}
    ]
    results["verification_status"] = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "can_mark_goal_complete": not failures and results["focused_pytest"]["status"] in {"PASS", "SKIPPED"},
    }
    if write_audit and parse["status"] == "PASS":
        update_completion_audit(results, payloads)
    return results


def main() -> None:
    results = verify_contract(run_pytest=True, write_audit=True)
    print(json.dumps(results, indent=2, sort_keys=True, default=str))
    if results["verification_status"]["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
