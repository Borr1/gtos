from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
SCHEMA = "nofill_lifecycle_categorical_result_packet_v1"
PACKET_ID = "NOFILL_LIFECYCLE_CLOSURE_CATEGORICAL_RESULT_PACKET_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/"

JSON_ARTIFACTS = [
    f"NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.json",
    f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{DATE}.json",
    f"NOFILL_CAT_PACKET_MANIFEST_{DATE}.json",
    f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json",
    f"NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.json",
    f"NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json",
    f"NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_{DATE}.json",
    f"NOFILL_CAT_FAILURE_LEARNING_LEDGER_{DATE}.json",
    f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{DATE}.md",
    f"NOFILL_CAT_PACKET_MANIFEST_{DATE}.md",
    f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.md",
    f"NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.md",
    f"NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.md",
    f"NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_{DATE}.md",
    f"NOFILL_CAT_FAILURE_LEARNING_LEDGER_{DATE}.md",
    f"NOFILL_CAT_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.md",
]

PY_FILES = [
    "build_nofill_lifecycle_categorical_result_packet_2026_05_08.py",
    "verify_nofill_lifecycle_categorical_result_packet_2026_05_08.py",
    "test_nofill_lifecycle_categorical_result_packet_2026_05_08.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "tests/canary",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def check_artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES + [f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl"]
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
    try:
        rows = load_jsonl(f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl")
        parsed += len(rows)
    except Exception as exc:
        errors.append({"path": f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl", "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": parsed, "errors": errors}


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def check_flags(items: dict[str, dict[str, Any]], packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
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
    for row in packet_rows:
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{row.get('packet_row_id')}: promotion_verdict")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False:
            issues.append(f"{row.get('packet_row_id')}: false flag")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_objective_coverage(items: dict[str, dict[str, Any]], packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    manifest = items[f"NOFILL_CAT_PACKET_MANIFEST_{DATE}.json"]
    eligibility = items[f"NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_{DATE}.json"]
    source = items[f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json"]
    noleak = items[f"NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.json"]
    duplicate = items[f"NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"]
    counts = items[f"NOFILL_CAT_LIFECYCLE_CATEGORY_COUNTS_{DATE}.json"]
    failure = items[f"NOFILL_CAT_FAILURE_LEARNING_LEDGER_{DATE}.json"]

    if len(packet_rows) != 298:
        issues.append("packet rows != 298")
    if manifest["source_universe"]["source_closed_rows"] != 298:
        issues.append("source_closed rows != 298")
    if manifest["row_outcome"]["eligible_label_assigned_rows"] + manifest["row_outcome"]["blocked_before_label_rows"] != 298:
        issues.append("eligible+blocked != 298")
    if eligibility["eligibility_counts"].get("ELIGIBLE_LABEL_ASSIGNED") != manifest["row_outcome"]["eligible_label_assigned_rows"]:
        issues.append("eligibility count mismatch")
    if counts["row_level"]["total_rows"] != 298:
        issues.append("category counts total rows mismatch")
    if noleak["status"] != "PASS":
        issues.append("no-leak audit not PASS")
    if source["status"] != "PASS":
        issues.append("source/asof audit not PASS")
    if duplicate["status"] != "PASS":
        issues.append("duplicate audit not PASS")
    if failure["next_action"] != "G12 categorical packet audit if this verifier passes; blocked families should route to source-correction or contract-revision lanes before result labels.":
        issues.append("failure ledger next action missing")
    if source["row_0127_terminal_first_recompute"]["status"] != "PASS":
        issues.append("row 0127 recompute not PASS")
    if source["row_0127_terminal_first_recompute"]["first_event"]["first_touch_utc"] != "2026-05-06T07:15:00.634000Z":
        issues.append("row 0127 first touch mismatch")
    if duplicate["duplicate_conflict_group_count"] != 3:
        issues.append("expected 3 duplicate conflict groups")
    if not all(row["eligibility_checked_before_label"] is True for row in packet_rows):
        issues.append("eligibility before label flag missing")
    blocked_with_label = [row["packet_row_id"] for row in packet_rows if row["eligibility_decision"] != "ELIGIBLE_LABEL_ASSIGNED" and row["categorical_lifecycle_label"] is not None]
    if blocked_with_label:
        issues.append(f"blocked rows carry labels: {blocked_with_label[:5]}")
    eligible_without_label = [row["packet_row_id"] for row in packet_rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED" and not row["categorical_lifecycle_label"]]
    if eligible_without_label:
        issues.append(f"eligible rows missing labels: {eligible_without_label[:5]}")
    row0127 = [row for row in packet_rows if row["source_close_packet_row_id"] == "NOFILL-CLOSE-ROW-0127"]
    if not row0127 or row0127[0]["eligibility_decision"] != "BLOCKED_BEFORE_LABEL":
        issues.append("row 0127 not present or not blocked")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_field_order() -> dict[str, Any]:
    issues = []
    for idx, line in enumerate((OUT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl").read_text(encoding="utf-8").splitlines(), start=1):
        e = line.find('"eligibility_decision"')
        c = line.find('"categorical_lifecycle_label"')
        if e == -1 or c == -1 or e > c:
            issues.append({"line": idx, "issue": "eligibility_decision does not precede categorical_lifecycle_label"})
            break
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_exclusions_and_forbidden_fields(items: dict[str, dict[str, Any]], packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    excluded = {f"CNR-T3-CAND-{i:04d}" for i in range(1, 7)}
    t3_hits = [row["source_inventory_id"] for row in packet_rows if row["source_inventory_id"] in excluded]
    cnr_hits = [row["packet_row_id"] for row in packet_rows if row["source_lane"] == "OTI8_CNR061" or row["source_closure_label"] == "stop_after_original_horizon"]
    if t3_hits:
        issues.append(f"six T3 overlap: {t3_hits}")
    if cnr_hits:
        issues.append(f"blocked CNR061 overlap: {cnr_hits[:5]}")
    noleak = items[f"NOFILL_CAT_NOLEAK_LABEL_FAMILY_AUDIT_{DATE}.json"]
    if noleak["forbidden_packet_field_hits"]:
        issues.append("forbidden packet field hits")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hashes(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    audit = items[f"NOFILL_CAT_SOURCE_HASH_AND_ASOF_AUDIT_{DATE}.json"]
    issues = []
    if audit["hash_mismatches"]:
        issues.append("hash mismatches present")
    if audit["missing_source_files"]:
        issues.append("missing source files present")
    if audit["asof_issues"]:
        issues.append("asof issues present")
    if audit["row_0127_terminal_first_recompute"]["source_sha256"] != "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff":
        issues.append("row 0127 sha mismatch")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "hash_record_count": len(audit.get("hash_records", [])),
    }


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
    if os.environ.get("NOFILL_CAT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "NOFILL_CAT_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["NOFILL_CAT_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_nofill_lifecycle_categorical_result_packet_2026_05_08.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    return {
        "command": f"{sys.executable} -B -m pytest -p no:cacheprovider {OUT_DIR / 'test_nofill_lifecycle_categorical_result_packet_2026_05_08.py'} -q",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def check_live_surface_diff() -> dict[str, Any]:
    workspace_proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    workspace_changed = []
    for line in workspace_proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        workspace_changed.append(path)
    committed_proc = subprocess.run(["git", "diff", "--name-only", "HEAD^1", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    committed_changed = [line.strip().replace("\\", "/") for line in committed_proc.stdout.splitlines() if line.strip()]
    use_committed_scope = committed_proc.returncode == 0 and any(path.startswith(LANE_PREFIX) for path in committed_changed)
    checked_scope = "committed_diff_HEAD_parent" if use_committed_scope else "workspace_status"

    if not use_committed_scope:
        lane_commit_proc = subprocess.run(
            ["git", "log", "--format=%H", "-n", "1", "--", LANE_PREFIX],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        lane_commit = lane_commit_proc.stdout.strip().splitlines()[0] if lane_commit_proc.returncode == 0 and lane_commit_proc.stdout.strip() else ""
        if lane_commit:
            lane_diff_proc = subprocess.run(
                ["git", "diff", "--name-only", f"{lane_commit}^1", lane_commit],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            lane_changed = [line.strip().replace("\\", "/") for line in lane_diff_proc.stdout.splitlines() if line.strip()]
            if lane_diff_proc.returncode == 0 and any(path.startswith(LANE_PREFIX) for path in lane_changed):
                committed_changed = lane_changed
                use_committed_scope = True
                checked_scope = f"historical_committed_lane_diff_{lane_commit[:8]}"

    changed = committed_changed if use_committed_scope else workspace_changed
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": checked_scope,
        "changed_paths": changed,
        "workspace_changed_path_count_observed": len(workspace_changed),
        "workspace_changed_paths_observed_sample": workspace_changed[:60],
        "forbidden_live_surface_changed_paths": forbidden,
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def write_completion_audit(items: dict[str, dict[str, Any]], verification: dict[str, Any]) -> None:
    audit = items[f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json"]
    all_pass = all(value.get("status") in ("PASS", "SKIPPED") for value in verification.values() if isinstance(value, dict))
    audit["verification_results"] = verification
    audit["completion_status"] = "PASS_VERIFIED_CATEGORICAL_PACKET" if all_pass else "FAIL_CATEGORICAL_PACKET_VERIFICATION"
    audit["can_mark_goal_complete"] = bool(all_pass)
    audit["missing_or_weak_requirements"] = [] if all_pass else ["One or more verifier checks failed."]
    for item in audit["prompt_to_artifact_checklist"]:
        if item["status"] == "PENDING_VERIFIER":
            item["status"] = "PASS" if all_pass else "RECHECK_REQUIRED"
    (OUT_DIR / f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# NOFILL CAT Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{audit['completion_status']}`",
        f"Can mark goal complete: `{str(audit['can_mark_goal_complete']).lower()}`",
        f"Next action: `{audit['next_action']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"- `{item['status']}` {item['requirement']}: `{item['artifact']}`")
    lines += ["", "## Verification Results"]
    for key, value in verification.items():
        if isinstance(value, dict):
            lines.append(f"- `{key}`: `{value.get('status')}`")
    (OUT_DIR / f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify_packet(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    presence = check_artifact_presence()
    parse = check_json_parse()
    items = payloads()
    packet_rows = load_jsonl(f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl") if (OUT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl").exists() else []
    results = {
        "artifact_presence": presence,
        "json_parse": parse,
        "flags": check_flags(items, packet_rows),
        "objective_coverage": check_objective_coverage(items, packet_rows),
        "eligibility_before_labels": check_field_order(),
        "exclusions_and_forbidden_fields": check_exclusions_and_forbidden_fields(items, packet_rows),
        "source_hashes": check_source_hashes(items),
        "py_compile": check_py_compile(),
        "live_surface_diff": check_live_surface_diff(),
    }
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "called with run_pytest=False"}
    results["verification_status"] = {
        "status": "PASS" if all(value.get("status") in ("PASS", "SKIPPED") for value in results.values() if isinstance(value, dict)) else "FAIL"
    }
    if write_audit and f"NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json" in items:
        write_completion_audit(items, results)
    return results


def main() -> None:
    results = verify_packet(run_pytest=True, write_audit=True)
    status = results["verification_status"]["status"]
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

