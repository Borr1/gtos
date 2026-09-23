from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/"

EXPECTED_FINAL_DECISION_COUNTS = {
    "ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
    "ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 173,
    "BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 8,
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

JSON_ARTIFACTS = [
    f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_SOURCE_CORRECTION_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"G12_NOFILL_SOURCE_CORRECTION_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_LEARNING_LEDGER_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_SOURCE_CORRECTION_COMPLETION_AUDIT_{DATE}.md",
]

PY_FILES = [
    "build_g12_nofill_source_correction_consolidated_audit_2026_05_08.py",
    "verify_g12_nofill_source_correction_consolidated_audit_2026_05_08.py",
    "test_g12_nofill_source_correction_consolidated_audit_2026_05_08.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
)

ALLOWED_DIRTY_PREFIXES = (
    LANE_PREFIX,
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
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
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "parsed_count": len(JSON_ARTIFACTS) - len(errors)}


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
    for collection_name in [
        f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json",
        f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{DATE}.json",
        f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{DATE}.json",
    ]:
        for row in items[collection_name].get("row_decisions", []) + items[collection_name].get("rows", []):
            if row.get("promotion_verdict") != PROMOTION_VERDICT:
                issues.append(f"{collection_name}:{row.get('packet_row_id')}: promotion")
            if row.get("validation_safe") is not False:
                issues.append(f"{collection_name}:{row.get('packet_row_id')}: validation_safe")
            if row.get("outcome_review_opened") is not False:
                issues.append(f"{collection_name}:{row.get('packet_row_id')}: outcome_review_opened")
            if row.get("live_effect") is not False:
                issues.append(f"{collection_name}:{row.get('packet_row_id')}: live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_universe_and_counts(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    universe = items[f"G12_NOFILL_SOURCE_CORRECTION_UNIVERSE_RECONCILIATION_{DATE}.json"]
    decision = items[f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json"]
    accepted = items[f"G12_NOFILL_SOURCE_CORRECTION_ACCEPTED_ROW_SHORTLIST_{DATE}.json"]
    blockers = items[f"G12_NOFILL_SOURCE_CORRECTION_BLOCKER_LEDGER_{DATE}.json"]
    if universe["source_universe"]["row_count"] != 298:
        issues.append("universe row count")
    if universe["source_universe"]["prior_accepted_categorical_rows"] != 52:
        issues.append("prior accepted count")
    if universe["source_universe"]["prior_blocked_rows"] != 246:
        issues.append("prior blocked count")
    if not universe["router_reconciliation"]["router_matches_prior_blocked_packet_ids"]:
        issues.append("router does not match blocked rows")
    if universe["router_reconciliation"]["router_overlap_with_prior_accepted"]:
        issues.append("router overlaps prior accepted rows")
    if decision["row_count"] != 298:
        issues.append("decision row count")
    if decision["final_decision_counts"] != EXPECTED_FINAL_DECISION_COUNTS:
        issues.append(f"final decision counts {decision['final_decision_counts']}")
    if accepted["accepted_row_count"] != 225:
        issues.append("accepted shortlist count")
    if blockers["blocked_row_count"] != 8:
        issues.append("blocker ledger count")
    if universe["six_t3_overlap"] or universe["blocked_cnr061_overlap"]:
        issues.append("excluded T3/CNR061 overlap")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_lane_specifics(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    decision_rows = items[f"G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_{DATE}.json"]["row_decisions"]
    counts_by_lane_decision: dict[str, int] = {}
    for row in decision_rows:
        key = f"{row['accepted_source_lane']}|{row['consolidated_decision']}"
        counts_by_lane_decision[key] = counts_by_lane_decision.get(key, 0) + 1
    expected_pairs = {
        "prior_g12_categorical_packet_audit|ACCEPT_PRIOR_CATEGORICAL_LABEL": 52,
        "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 32,
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 29,
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2|BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 5,
        "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 58,
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 51,
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|BLOCK_EXACT_SOURCE_OR_ORDERING_GAP": 3,
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION|REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT|ACCEPT_SOURCE_CORRECTED_INPUT_FOR_REBUILD": 3,
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT|REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
    }
    if counts_by_lane_decision != expected_pairs:
        issues.append({"counts_by_lane_decision": counts_by_lane_decision})
    source_audit = items[f"G12_NOFILL_SOURCE_CORRECTION_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"]
    if source_audit["status"] != "PASS":
        issues.append("source/no-leak status")
    if source_audit["missing_source_hash_records"] or source_audit["source_hash_mismatches"] or source_audit["forbidden_output_key_hits"]:
        issues.append("source/no-leak missing/mismatch/forbidden")
    if len(source_audit["oti3_same_timestamp_red_team_checks"]) != 4:
        issues.append("OTI3 same-timestamp check count")
    if any(check["matching_tick_record_count"] != 1 for check in source_audit["oti3_same_timestamp_red_team_checks"]):
        issues.append("OTI3 same-timestamp did not resolve to exactly one source tick")
    if len(source_audit["oti4_may3_source_gap_red_team_checks"]) != 3:
        issues.append("OTI4 May3 check count")
    if any(check["local_tick_required_range_count"] != 0 for check in source_audit["oti4_may3_source_gap_red_team_checks"]):
        issues.append("OTI4 May3 range unexpectedly has ticks")
    duplicate = items[f"G12_NOFILL_SOURCE_CORRECTION_DUPLICATE_SAMPLE_FLOOR_AUDIT_{DATE}.json"]
    if duplicate["oti5_canonical_rows_accepted_for_rebuild"] != [
        "NOFILL-CAT-ROW-0001",
        "NOFILL-CAT-ROW-0016",
        "NOFILL-CAT-ROW-0017",
    ]:
        issues.append("OTI5 canonical packet ids")
    if duplicate["oti5_noncanonical_rows_rejected_from_denominator"] != 39:
        issues.append("OTI5 noncanonical count")
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
    if os.environ.get("G12_NOFILL_SOURCE_CORRECTION_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_NOFILL_SOURCE_CORRECTION_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["G12_NOFILL_SOURCE_CORRECTION_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / f"test_g12_nofill_source_correction_consolidated_audit_2026_05_08.py"),
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


def check_git_scope() -> dict[str, Any]:
    dirty_proc = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    dirty_paths = [line.strip().replace("\\", "/") for line in dirty_proc.stdout.splitlines() if line.strip()]
    commit_proc = subprocess.run(
        ["git", "log", "--format=%H", "-n", "1", "--", LANE_PREFIX],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    lane_commit = commit_proc.stdout.strip()
    if lane_commit:
        diff_proc = subprocess.run(
            ["git", "diff", "--name-only", f"{lane_commit}^1", lane_commit],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
    else:
        diff_proc = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="lane commit not found")
    committed_paths = [line.strip().replace("\\", "/") for line in diff_proc.stdout.splitlines() if line.strip()]
    forbidden = [path for path in committed_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    outside_allowed = [
        path
        for path in committed_paths
        if not any(path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES)
    ]
    return {
        "status": "PASS" if dirty_proc.returncode == 0 and diff_proc.returncode == 0 and not forbidden and not outside_allowed else "FAIL",
        "check_scope": "latest committed lane diff",
        "lane_commit": lane_commit,
        "dirty_paths": dirty_paths,
        "committed_paths": committed_paths,
        "forbidden_live_paths": forbidden,
        "outside_allowed_paths": outside_allowed,
    }


def verify(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    results: dict[str, Any] = {}
    results["artifact_presence"] = check_artifact_presence()
    results["json_parse"] = check_json_parse()
    items = payloads()
    results["markdown_promotion"] = check_markdown_promotion()
    if len(items) == len(JSON_ARTIFACTS):
        results["flags"] = check_flags(items)
        results["universe_and_counts"] = check_universe_and_counts(items)
        results["lane_specifics"] = check_lane_specifics(items)
    else:
        results["flags"] = {"status": "FAIL", "issues": ["not all payloads loaded"]}
        results["universe_and_counts"] = {"status": "FAIL", "issues": ["not all payloads loaded"]}
        results["lane_specifics"] = {"status": "FAIL", "issues": ["not all payloads loaded"]}
    results["py_compile"] = check_py_compile()
    results["git_scope"] = check_git_scope()
    if run_pytest:
        results["focused_pytest"] = run_focused_pytest()
    statuses = {
        name: value.get("status")
        for name, value in results.items()
        if isinstance(value, dict) and "status" in value
    }
    overall = "PASS" if all(status in {"PASS", "SKIPPED"} for status in statuses.values()) else "FAIL"
    payload = {
        "artifact_family": "G12_NOFILL_SOURCE_CORRECTION_VERIFICATION",
        "schema_version": "g12_nofill_source_correction_consolidated_audit_verifier_v1",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "verification_status": overall,
        "can_mark_goal_complete": overall == "PASS",
        "checks": results,
    }
    if write_audit:
        (OUT_DIR / f"G12_NOFILL_SOURCE_CORRECTION_VERIFICATION_{DATE}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
    return payload


def main() -> int:
    payload = verify(run_pytest=True, write_audit=True)
    print(json.dumps({"verification_status": payload["verification_status"], "can_mark_goal_complete": payload["can_mark_goal_complete"]}, indent=2))
    return 0 if payload["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
