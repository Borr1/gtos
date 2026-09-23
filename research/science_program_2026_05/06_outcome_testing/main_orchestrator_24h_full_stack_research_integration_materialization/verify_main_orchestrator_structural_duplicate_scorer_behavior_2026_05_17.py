from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 1026,
    "KILL": 1014,
    "PRESERVE_REQUIREMENT": 16,
    "REDESIGN": 852,
}
EXPECTED_TICK_STATUS_COUNTS = {
    "NOT_TARGET_ROW": 3230,
    "TICK_DERIVED_SOURCE_REPAIR_AMBIGUITY_EXCLUDED": 32,
    "TICK_DERIVED_SOURCE_REPAIR_COMPUTED_PROXY": 89,
    "TICK_DERIVED_SOURCE_REPAIR_KILLED": 75,
}
EXPECTED_DUPLICATE_BRANCH = "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION"
PREVIOUS_DUPLICATE_BRANCH = "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF"
TARGET_STATUS = "SOURCE_SCORER_NOW_EMITS_DUPLICATE_STRUCTURAL_REDESIGN"
SOURCE_REPAIR_DEPENDENT_STATUS = "RAW_SOURCE_SCORER_REQUIRES_STRUCTURAL_SOURCE_REPAIR_MATERIALIZATION"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {"numeric_proxy_rows": len(values), "proxy_r_sum": round(sum(values), 8)}


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    repo_root = find_repo_root(ROUTE_DIR)
    build_script = ROUTE_DIR / "build_main_orchestrator_structural_duplicate_scorer_behavior_2026_05_17.py"
    verify_script = Path(__file__).resolve()
    source_file = repo_root / "src/research_infra/live_mechanical_shadow.py"
    test_file = repo_root / "tests/test_live_mechanical_shadow.py"
    required_paths = [
        build_script,
        verify_script,
        source_file,
        test_file,
        INPUT_LEDGER,
        INPUT_SUMMARY,
        OUTPUT_LEDGER,
        OUTPUT_SUMMARY,
        OUTPUT_MANIFEST,
    ]
    checks: list[dict[str, Any]] = [
        check(f"{path.name}_exists", path.exists(), str(path)) for path in required_paths
    ]

    input_rows = read_jsonl(INPUT_LEDGER)
    output_rows = read_jsonl(OUTPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    input_proxy = proxy_summary(input_rows)
    output_proxy = proxy_summary(output_rows)
    target_rows = [
        row
        for row in output_rows
        if row.get("structural_duplicate_scorer_behavior_status")
        in {TARGET_STATUS, SOURCE_REPAIR_DEPENDENT_STATUS}
    ]

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_preserved", len(input_rows) == len(output_rows) == summary.get("rows") == 3426))
    checks.append(check("previous_summary_matches_input", input_summary.get("rows") == len(input_rows)))
    checks.append(check("target_rows_expected", len(target_rows) == summary.get("target_rows") == 822))
    checks.append(check("native_and_repair_dependent_split_expected", summary.get("native_source_scorer_redesign_rows") == 822 and summary.get("source_repair_dependent_rows") == 0))
    checks.append(check("target_numeric_proxy_preserved", summary.get("target_numeric_proxy_rows") == 564 and summary.get("target_proxy_r_sum") == 177.0))
    checks.append(check("target_previous_branch_expected", summary.get("before_source_scorer_patch_branch_counts") == {PREVIOUS_DUPLICATE_BRANCH: 822}))
    checks.append(check("target_after_branch_expected", summary.get("after_source_scorer_patch_branch_counts") == {EXPECTED_DUPLICATE_BRANCH: 822}))
    checks.append(check("target_matches_action_selection_where_native", summary.get("repair_stats", {}).get("target_rows_action_branch_matches_source_patch") == 822 and summary.get("repair_stats", {}).get("target_rows_action_candidate_matches_source_patch") == 822))
    checks.append(check("target_proxy_match_counts_expected", summary.get("target_proxy_match_counts") == {"True": 822}))
    checks.append(check("action_counts_preserved", summary.get("action_class_counts_after") == EXPECTED_ACTION_COUNTS and counter(output_rows, "action_class") == EXPECTED_ACTION_COUNTS))
    checks.append(check("no_metadata_gaps", summary.get("all_metadata_gaps_after") == 0 and sum(1 for row in output_rows if has_metadata_gap(row)) == 0))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in output_rows)))
    checks.append(check("proxy_r_invariants_preserved", input_proxy == output_proxy == {"numeric_proxy_rows": 1475, "proxy_r_sum": 408.47201587}))

    far = summary.get("far_miss_retest_control_invariants", {})
    checks.append(check("far_miss_default_off_invariant", far.get("entry_default_off_candidates") == 10 and far.get("entry_default_off_proxy_r_sum") == 6.67275084))
    checks.append(check("far_miss_kill_invariant", far.get("killed_far_miss_rows") == 84 and far.get("killed_far_miss_candidates") == 84))
    tick = summary.get("tick_structural_source_repair_invariants", {})
    checks.append(check("tick_structural_invariants", tick.get("tick_structural_converted_rows") == 196 and tick.get("tick_structural_status_counts") == EXPECTED_TICK_STATUS_COUNTS))

    row_errors: list[dict[str, Any]] = []
    input_by_row_id = {row.get("row_id"): row for row in input_rows}
    for row in output_rows:
        before = input_by_row_id.get(row.get("row_id"))
        if before is None:
            row_errors.append({"line": row["_line_no"], "error": "row_id_not_in_input", "row_id": row.get("row_id")})
            continue
        if row.get("candidate_id") != before.get("candidate_id") or row.get("source_plate") != before.get("source_plate"):
            row_errors.append({"line": row["_line_no"], "error": "source_identity_changed", "row_id": row.get("row_id")})
        if row.get("safe_flags") != before.get("safe_flags") or row.get("no_live_behavior") is not True or row.get("no_promotion") is not True:
            row_errors.append({"line": row["_line_no"], "error": "safe_flag_or_no_effect_mismatch", "row_id": row.get("row_id")})
        if safe_float(row.get("after_proxy_r")) != safe_float(before.get("after_proxy_r")):
            row_errors.append({"line": row["_line_no"], "error": "proxy_changed", "row_id": row.get("row_id")})
        if row.get("structural_duplicate_scorer_behavior_status") == "NOT_TARGET_ROW":
            for field in ("action_class", "branch_decision", "decision_evidence", "scoring_boundary", "implementation_candidate", "current_action", "next_action"):
                if row.get(field) != before.get(field):
                    row_errors.append({"line": row["_line_no"], "error": f"non_target_{field}_changed", "row_id": row.get("row_id")})
                    break
    checks.append(check("rows_preserve_identity_safety_r_and_non_targets", not row_errors, row_errors[:20]))

    manifest_input_errors = []
    for artifact_name, artifact in manifest.get("input_artifacts", {}).items():
        path = repo_root / artifact_name
        if not path.exists():
            manifest_input_errors.append({"path": artifact_name, "error": "path_missing"})
            continue
        if artifact.get("sha256") != sha256_file(path):
            manifest_input_errors.append({"path": artifact_name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_input_errors.append({"path": artifact_name, "error": "size_mismatch"})
    checks.append(check("manifest_input_hashes_match", not manifest_input_errors, manifest_input_errors))

    manifest_output_errors = []
    for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]:
        artifact = manifest.get("output_artifacts", {}).get(path.name)
        if not artifact:
            manifest_output_errors.append({"path": path.name, "error": "missing_manifest_output"})
            continue
        if artifact.get("sha256") != sha256_file(path):
            manifest_output_errors.append({"path": path.name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_output_errors.append({"path": path.name, "error": "size_mismatch"})
    checks.append(check("manifest_output_hashes_match", not manifest_output_errors, manifest_output_errors))

    for path in [source_file, test_file, build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "rows": len(output_rows),
            "target_rows": len(target_rows),
            "target_proxy_r_sum": summary.get("target_proxy_r_sum"),
            "action_class_counts_after": counter(output_rows, "action_class"),
            "numeric_proxy_rows_after": output_proxy["numeric_proxy_rows"],
            "proxy_r_sum_after": output_proxy["proxy_r_sum"],
            "far_miss_retest_control_invariants": far,
            "tick_structural_source_repair_invariants": tick,
        },
        "plate_decision": "STRUCTURAL_DUPLICATE_SCORER_BEHAVIOR_ACCEPTED_NO_PROMOTION",
        "can_mark_structural_duplicate_scorer_behavior_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(VERIFY_RESULT)}, sort_keys=True))


if __name__ == "__main__":
    main()
