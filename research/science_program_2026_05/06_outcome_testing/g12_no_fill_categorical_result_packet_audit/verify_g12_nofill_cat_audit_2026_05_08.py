from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DECISION = "ACCEPT_AS_CATEGORICAL_LIFECYCLE_ONLY_EVIDENCE_WITH_BLOCKED_FAMILIES"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
CAT_DIR = OUT_DIR.parent / "no_fill_lifecycle_categorical_result_packet"
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/g12_no_fill_categorical_result_packet_audit/"

JSON_ARTIFACTS = [
    f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.json",
    f"G12_NOFILL_CAT_LEARNING_LEDGER_{DATE}.json",
    f"G12_NOFILL_CAT_COMPLETION_AUDIT_{DATE}.json",
]

MD_ARTIFACTS = [
    f"G12_NOFILL_CAT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.md",
    f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.md",
    f"G12_NOFILL_CAT_LEARNING_LEDGER_{DATE}.md",
    f"G12_NOFILL_CAT_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_CAT_COMPLETION_AUDIT_{DATE}.md",
]

PY_FILES = [
    "build_g12_nofill_cat_audit_2026_05_08.py",
    "verify_g12_nofill_cat_audit_2026_05_08.py",
    "test_g12_nofill_cat_audit_2026_05_08.py",
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


def load_upstream_rows() -> list[dict[str, Any]]:
    path = CAT_DIR / f"NOFILL_CAT_PACKET_ROWS_{DATE}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    try:
        rows = load_upstream_rows()
        parsed += len(rows)
    except Exception as exc:
        errors.append({"path": "upstream NOFILL_CAT_PACKET_ROWS jsonl", "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": parsed, "errors": errors}


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def check_flags(items: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
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
    for row in rows:
        if (row.get("promotion_verdict"), row.get("validation_safe"), row.get("outcome_review_opened"), row.get("live_effect")) != (PROMOTION_VERDICT, False, False, False):
            issues.append(f"{row.get('packet_row_id')}: flags")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_decision_and_counts(items: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    decision = items[f"G12_NOFILL_CAT_DECISION_LEDGER_{DATE}.json"]
    if decision.get("decision") != DECISION:
        issues.append("decision mismatch")
    if len(rows) != 298:
        issues.append("upstream row count != 298")
    eligible = [row for row in rows if row.get("eligibility_decision") == "ELIGIBLE_LABEL_ASSIGNED"]
    blocked = [row for row in rows if row.get("eligibility_decision") == "BLOCKED_BEFORE_LABEL"]
    if len(eligible) != 52 or len(blocked) != 246:
        issues.append("52/246 split mismatch")
    if any(row.get("categorical_lifecycle_label") != "nofill_terminal_before_entry" for row in eligible):
        issues.append("eligible label mismatch")
    if any(row.get("categorical_lifecycle_label") is not None for row in blocked):
        issues.append("blocked row has label")
    if any(row.get("eligibility_checked_before_label") is not True for row in rows):
        issues.append("eligibility flag not true for every row")
    source_universe = decision["source_universe"]
    if not source_universe["id_sets_equal"]:
        issues.append("source universe id sets differ")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_source_hash_and_row0127(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    audit = items[f"G12_NOFILL_CAT_SOURCE_HASH_AUDIT_{DATE}.json"]
    issues = []
    if audit["status"] != "PASS":
        issues.append("source hash artifact status")
    if audit["hash_record_count"] != 65:
        issues.append("expected 65 source hash records")
    if audit["missing_source_files"]:
        issues.append("missing source files")
    if audit["hash_mismatches"]:
        issues.append("hash mismatches")
    row0127 = audit["row_0127_terminal_first_recompute"]
    if row0127["status"] != "PASS":
        issues.append("row0127 recompute status")
    if row0127["first_event"]["first_touch_utc"] != "2026-05-06T07:15:00.634000Z":
        issues.append("row0127 first touch")
    if row0127["source_sha256"] != "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff":
        issues.append("row0127 sha")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_noleak_duplicate_blockers(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    noleak = items[f"G12_NOFILL_CAT_NOLEAK_LABEL_AUDIT_{DATE}.json"]
    duplicate = items[f"G12_NOFILL_CAT_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"]
    blocker = items[f"G12_NOFILL_CAT_BLOCKER_REVIEW_{DATE}.json"]
    if noleak["status"] != "PASS":
        issues.append("noleak status")
    if noleak["forbidden_packet_field_hits"] or noleak["six_t3_overlap"] or noleak["blocked_cnr061_overlap"]:
        issues.append("noleak overlap/forbidden hits")
    if noleak["price_compatible_m1_rows_with_labels"] or noleak["pending_lifecycle_rows_with_labels"]:
        issues.append("blocked source families received labels")
    if duplicate["status"] != "PASS" or duplicate["duplicate_conflict_blocked_rows"] != 42 or duplicate["duplicate_conflict_group_count"] != 3:
        issues.append("duplicate status/counts")
    if duplicate["sample_floor_status"] != "DISCOVERY_UNDER_SAMPLE_FLOOR_NO_VALIDATION_OR_PROMOTION":
        issues.append("sample floor status")
    if blocker["status"] != "PASS" or not blocker["no_blocked_row_relabelable_under_current_contract"]:
        issues.append("blocker review status")
    expected = {
        "BLOCK_RESULT_DUPLICATE_CONFLICT": 42,
        "BLOCK_RESULT_LTF_PRICE_ONLY": 69,
        "BLOCK_RESULT_MISSING_PENDING_INTENT_CLOSURE_FIELD": 54,
        "BLOCK_RESULT_MISSING_SOURCE": 80,
        "BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 1,
        "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 1,
    }
    if blocker["blocker_code_counts"] != expected:
        issues.append("blocker counts")
    if blocker["otx_ambiguity_resolution"]["status"] != "DOES_NOT_RESCUE_CURRENT_BLOCKED_ROWS":
        issues.append("otx ambiguity status")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_upstream_verifier_no_write() -> dict[str, Any]:
    verifier_path = CAT_DIR / "verify_nofill_lifecycle_categorical_result_packet_2026_05_08.py"
    spec = importlib.util.spec_from_file_location("upstream_nofill_cat_verifier", verifier_path)
    if spec is None or spec.loader is None:
        return {"status": "FAIL", "error": "cannot load upstream verifier"}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = module.verify_packet(run_pytest=False, write_audit=False)
    status = results.get("verification_status", {}).get("status")
    return {"status": "PASS" if status == "PASS" else "FAIL", "upstream_status": status}


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
    if os.environ.get("G12_NOFILL_CAT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_NOFILL_CAT_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["G12_NOFILL_CAT_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_g12_nofill_cat_audit_2026_05_08.py"),
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
        "command": f"{sys.executable} -B -m pytest -p no:cacheprovider {OUT_DIR / 'test_g12_nofill_cat_audit_2026_05_08.py'} -q",
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
    committed_proc = subprocess.run(["git", "diff", "--name-only", "HEAD^", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    committed_changed = [line.strip().replace("\\", "/") for line in committed_proc.stdout.splitlines() if line.strip()]
    use_committed_scope = committed_proc.returncode == 0 and any(path.startswith(LANE_PREFIX) for path in committed_changed)
    changed = committed_changed if use_committed_scope else workspace_changed
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if use_committed_scope else "workspace_status",
        "changed_paths": changed,
        "forbidden_live_surface_changed_paths": forbidden,
        "workspace_changed_path_count_observed": len(workspace_changed),
        "workspace_changed_paths_observed_sample": workspace_changed[:80],
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def write_completion(verification: dict[str, Any]) -> None:
    builder_path = OUT_DIR / "build_g12_nofill_cat_audit_2026_05_08.py"
    spec = importlib.util.spec_from_file_location("g12_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load G12 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_completion_audit(status="VERIFIED_BY_G12_VERIFIER", verification=verification)


def verify_audit(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    rows = load_upstream_rows()
    items = payloads()
    results: dict[str, Any] = {
        "artifact_presence": check_artifact_presence(),
        "json_parse": check_json_parse(),
        "flags": check_flags(items, rows),
        "decision_and_counts": check_decision_and_counts(items, rows),
        "source_hash_and_row0127": check_source_hash_and_row0127(items),
        "noleak_duplicate_blockers": check_noleak_duplicate_blockers(items),
        "upstream_packet_verifier_no_write": check_upstream_verifier_no_write(),
        "py_compile": check_py_compile(),
        "live_surface_diff": check_live_surface_diff(),
    }
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "called with run_pytest=False"}
    results["verification_status"] = {
        "status": "PASS" if all(value.get("status") in ("PASS", "SKIPPED") for value in results.values() if isinstance(value, dict)) else "FAIL"
    }
    if write_audit:
        write_completion(results)
    return results


def main() -> None:
    results = verify_audit(run_pytest=True, write_audit=True)
    status = results["verification_status"]["status"]
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
