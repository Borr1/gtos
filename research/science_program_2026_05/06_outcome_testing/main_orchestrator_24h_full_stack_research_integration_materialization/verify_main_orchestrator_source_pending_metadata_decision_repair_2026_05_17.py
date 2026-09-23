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
SUMMARY_SAFE_FLAGS = SAFE_FLAGS

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_SUMMARY_{DATE}.json"
PENDING_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_SUMMARY_2026-05-16.json"
SOURCE_M15_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_2026-05-16.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_VERIFICATION_RESULT_{DATE}.json"


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
    return dict(Counter(str(row.get(field) or "") for row in rows))


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
    values = [
        value
        for row in rows
        if (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def action_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_source_pending_metadata_decision_repair_2026_05_17.py"
    verify_script = Path(__file__).resolve()
    required_paths = [
        build_script,
        verify_script,
        INPUT_LEDGER,
        INPUT_SUMMARY,
        PENDING_SUMMARY,
        SOURCE_M15_SUMMARY,
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
    pending_summary = read_json(PENDING_SUMMARY)
    source_m15_summary = read_json(SOURCE_M15_SUMMARY)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    source_rows = [row for row in output_rows if row.get("source_plate") == "source_m15_ordering_repair"]
    pending_rows = [
        row for row in output_rows if row.get("source_plate") == "pending_lifecycle_source_derivation_recompute"
    ]
    source_pending_rows = source_rows + pending_rows

    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    expected_action_delta = {
        "DOWNGRADE_OR_REPAIR": -47,
        "IMPLEMENT_DEFAULT_OFF": 33,
        "KEEP": 39,
        "KEEP_REPAIR_OR_AVOID": -27,
        "KEEP_WITH_SOURCE_DERIVATION": -39,
        "KILL": 47,
        "PRESERVE_REQUIREMENT": 3,
        "UPGRADE_CHALLENGER_REVIEW": -9,
    }
    expected_source_actions = {
        "IMPLEMENT_DEFAULT_OFF": 33,
        "KEEP": 39,
        "KILL": 50,
        "PRESERVE_REQUIREMENT": 16,
    }

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("summary_manifest_safe_flags_closed", summary.get("safe_flags") == SUMMARY_SAFE_FLAGS and manifest.get("safe_flags") == SUMMARY_SAFE_FLAGS))
    checks.append(check("row_count_preserved", len(input_rows) == len(output_rows) == summary.get("rows") == 3426))
    checks.append(check("input_summary_matches_previous_plate", input_summary.get("rows") == len(input_rows)))
    checks.append(check("source_pending_target_counts", len(source_rows) == 138 and len(pending_rows) == 274 and len(source_pending_rows) == 412))
    checks.append(check("source_m15_summary_counts_match", source_m15_summary.get("rows") == 138 and source_m15_summary.get("m15_ordering_repaired_rows") == 30))
    checks.append(check("pending_summary_counts_match", pending_summary.get("rows") == 274 and pending_summary.get("internal_pending_lifecycle_rows") == 39))
    checks.append(check("target_metadata_gaps_closed", sum(1 for row in source_pending_rows if has_metadata_gap(row)) == 0))
    checks.append(check("target_current_actions_concrete", all(str(row.get("current_action")) not in {"None", "False", ""} and str(row.get("next_action")) not in {"None", "False", ""} for row in source_pending_rows)))
    checks.append(check("action_class_counts_match_rows", summary.get("action_class_counts_after") == after_actions))
    checks.append(check("action_delta_expected", summary.get("action_class_delta_vs_previous") == expected_action_delta == action_delta(before_actions, after_actions), summary.get("action_class_delta_vs_previous")))
    checks.append(check("source_action_classes_expected", counter(source_rows, "action_class") == expected_source_actions))
    checks.append(check("pending_action_classes_all_keep", counter(pending_rows, "action_class") == {"KEEP": 274}))
    checks.append(check("nonterminal_action_classes_removed", all(after_actions.get(key, 0) == 0 for key in ("DOWNGRADE_OR_REPAIR", "KEEP_REPAIR_OR_AVOID", "KEEP_WITH_SOURCE_DERIVATION", "UPGRADE_CHALLENGER_REVIEW"))))
    checks.append(check("exact_r_rows_zero", summary.get("exact_r_rows") == 0 and all(row.get("exact_r") is None for row in output_rows)))
    checks.append(check("numeric_proxy_rows_unchanged", before_proxy["numeric_proxy_rows"] == after_proxy["numeric_proxy_rows"] == summary.get("numeric_proxy_rows_after") == summary.get("numeric_proxy_rows_before")))
    checks.append(check("proxy_r_sum_unchanged", before_proxy["proxy_r_sum"] == after_proxy["proxy_r_sum"] == summary.get("proxy_r_sum_before") == summary.get("proxy_r_sum_after") and summary.get("proxy_r_sum_delta") == 0.0))
    checks.append(check("source_m15_proxy_sum_preserved", summary.get("source_m15_proxy_midpoint_sum") == source_m15_summary.get("ordering_proxy_midpoint_sum") == 3.302239))
    checks.append(check("pending_derived_cells_preserved", summary.get("pending_lifecycle_after_derived_source_field_cells") == pending_summary.get("after_derived_source_field_cells") == 323))
    checks.append(check("pending_missing_cells_preserved", summary.get("pending_lifecycle_after_missing_source_field_cells") == pending_summary.get("after_missing_source_field_cells") == 184))

    row_errors: list[dict[str, Any]] = []
    input_by_row_id = {row.get("row_id"): row for row in input_rows}
    for row in output_rows:
        row_id = row.get("row_id")
        before = input_by_row_id.get(row_id)
        if before is None:
            row_errors.append({"line": row["_line_no"], "error": "row_id_not_in_input", "row_id": row_id})
            continue
        if row.get("safe_flags") != before.get("safe_flags") or row.get("no_live_behavior") is not True or row.get("no_promotion") is not True:
            row_errors.append({"line": row["_line_no"], "error": "safe_flag_or_no_effect_mismatch", "row_id": row_id})
        if row.get("candidate_id") != before.get("candidate_id") or row.get("source_plate") != before.get("source_plate"):
            row_errors.append({"line": row["_line_no"], "error": "source_identity_changed", "row_id": row_id})
        before_value = safe_float(before.get("after_proxy_r"))
        after_value = safe_float(row.get("after_proxy_r"))
        if before_value != after_value:
            row_errors.append({"line": row["_line_no"], "error": "proxy_changed", "row_id": row_id})
        if row.get("exact_r") is not None:
            row_errors.append({"line": row["_line_no"], "error": "exact_r_opened", "row_id": row_id})
    checks.append(check("rows_preserve_identity_safety_and_r", not row_errors, row_errors[:20]))

    manifest_input_errors = []
    for path in [INPUT_LEDGER, INPUT_SUMMARY, PENDING_SUMMARY, SOURCE_M15_SUMMARY]:
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
            "source_m15_rows": len(source_rows),
            "pending_lifecycle_source_derivation_rows": len(pending_rows),
            "action_class_counts_after": after_actions,
            "action_class_delta_vs_previous": summary.get("action_class_delta_vs_previous"),
            "source_m15_action_class_counts_after": counter(source_rows, "action_class"),
            "pending_lifecycle_action_class_counts_after": counter(pending_rows, "action_class"),
            "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
            "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        },
        "plate_decision": "SOURCE_PENDING_METADATA_DECISION_REPAIR_ACCEPTED_NO_PROMOTION",
        "can_mark_source_pending_metadata_decision_repair_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SUMMARY_SAFE_FLAGS,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(VERIFY_RESULT)}, sort_keys=True))


if __name__ == "__main__":
    main()
