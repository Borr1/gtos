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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_ACTION_BEFORE = {
    "IMPLEMENT_DEFAULT_OFF": 1370,
    "KEEP": 1026,
    "KILL": 1014,
    "PRESERVE_REQUIREMENT": 16,
}
EXPECTED_ACTION_AFTER = {
    "IMPLEMENT_DEFAULT_OFF": 518,
    "KEEP": 1026,
    "KILL": 1014,
    "PRESERVE_REQUIREMENT": 16,
    "REDESIGN": 852,
}
EXPECTED_ACTION_DELTA = {
    "IMPLEMENT_DEFAULT_OFF": -852,
    "REDESIGN": 852,
}
EXPECTED_TICK_STATUS_COUNTS = {
    "NOT_TARGET_ROW": 3230,
    "TICK_DERIVED_SOURCE_REPAIR_AMBIGUITY_EXCLUDED": 32,
    "TICK_DERIVED_SOURCE_REPAIR_COMPUTED_PROXY": 89,
    "TICK_DERIVED_SOURCE_REPAIR_KILLED": 75,
}


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
    build_script = ROUTE_DIR / "build_main_orchestrator_implementation_selection_2026_05_17.py"
    verify_script = Path(__file__).resolve()
    required_paths = [
        build_script,
        verify_script,
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

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("row_count_preserved", len(input_rows) == len(output_rows) == summary.get("rows") == 3426))
    checks.append(check("previous_summary_matches_input", input_summary.get("rows") == len(input_rows)))
    checks.append(check("no_metadata_gaps", summary.get("all_metadata_gaps_after") == 0 and sum(1 for row in output_rows if has_metadata_gap(row)) == 0))
    checks.append(check("action_counts_before_expected", summary.get("action_class_counts_before") == EXPECTED_ACTION_BEFORE and counter(input_rows, "action_class") == EXPECTED_ACTION_BEFORE))
    checks.append(check("action_counts_after_expected", summary.get("action_class_counts_after") == EXPECTED_ACTION_AFTER and counter(output_rows, "action_class") == EXPECTED_ACTION_AFTER))
    checks.append(check("action_delta_expected", summary.get("action_class_delta_vs_previous") == EXPECTED_ACTION_DELTA))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in output_rows)))
    checks.append(check("proxy_r_invariants_preserved", input_proxy == output_proxy == {"numeric_proxy_rows": 1475, "proxy_r_sum": 408.47201587}))

    selection = summary.get("selection_stats", {})
    checks.append(check("duplicate_structural_redesigned", selection.get("duplicate_structural_rows_redesigned") == 822))
    checks.append(check("standalone_fvg_redesigned", selection.get("standalone_fvg_default_off_rows_redesigned") == 30))
    checks.append(check("canonical_and_swing_kept", selection.get("canonical_structural_rows_kept") == 274 and selection.get("swing_protected_rows_kept") == 185))

    structural = summary.get("structural_selection_decisions", {})
    checks.append(check("structural_decision_numbers", structural.get("canonical_structural_shared_path_numeric_proxy_rows") == 188 and structural.get("canonical_structural_shared_path_proxy_r_sum") == 59.0 and structural.get("swing_protected_numeric_proxy_rows") == 136 and structural.get("swing_protected_proxy_r_sum") == 55.5))
    standalone = summary.get("standalone_fvg_selection_decisions", {})
    checks.append(check("standalone_fvg_negative_current_proxy", standalone.get("standalone_fvg_default_off_rows_redesigned") == 30 and standalone.get("standalone_fvg_default_off_numeric_proxy_rows_before") == 8 and standalone.get("standalone_fvg_default_off_proxy_r_sum_before") == -8.0))

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
        if row.get("implementation_selection_status") == "NOT_TARGET_ROW":
            for field in ("action_class", "branch_decision", "decision_evidence", "scoring_boundary", "implementation_candidate", "current_action", "next_action"):
                if row.get(field) != before.get(field):
                    row_errors.append({"line": row["_line_no"], "error": f"non_target_{field}_changed", "row_id": row.get("row_id")})
                    break
    checks.append(check("rows_preserve_identity_safety_r_and_non_targets", not row_errors, row_errors[:20]))

    manifest_input_errors = []
    for path in [INPUT_LEDGER, INPUT_SUMMARY]:
        artifact = manifest.get("input_artifacts", {}).get(path.name)
        if not artifact:
            manifest_input_errors.append({"path": path.name, "error": "missing_manifest_input"})
            continue
        if artifact.get("sha256") != sha256_file(path):
            manifest_input_errors.append({"path": path.name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_input_errors.append({"path": path.name, "error": "size_mismatch"})
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

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "rows": len(output_rows),
            "action_class_counts_after": counter(output_rows, "action_class"),
            "numeric_proxy_rows_after": output_proxy["numeric_proxy_rows"],
            "proxy_r_sum_after": output_proxy["proxy_r_sum"],
            "selection_stats": selection,
            "far_miss_retest_control_invariants": far,
            "tick_structural_source_repair_invariants": tick,
        },
        "plate_decision": "IMPLEMENTATION_SELECTION_ACCEPTED_NO_PROMOTION",
        "can_mark_implementation_selection_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(VERIFY_RESULT)}, sort_keys=True))


if __name__ == "__main__":
    main()
