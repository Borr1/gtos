from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

ROUTE_DIR = Path(__file__).resolve().parent
INPUTS = {
    "fvg_structural_scorer_candidate_recompute": ROUTE_DIR / f"MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_LEDGER_{DATE}.jsonl",
    "entry_redesign_tick_offset_recompute": ROUTE_DIR / f"MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_{DATE}.jsonl",
    "pending_lifecycle_source_derivation_recompute": ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_LEDGER_{DATE}.jsonl",
    "source_m15_ordering_repair": ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_{DATE}.jsonl",
}
PREVIOUS_ACTION_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_SUMMARY_{DATE}.json"
SOURCE_M15_REPAIR_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_{DATE}.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def proxy_delta_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        value = safe_float(row.get("proxy_r_delta"))
        if value is None:
            continue
        grouped.setdefault(str(row.get("source_plate")), []).append(value)
    return {
        plate: {
            "numeric_proxy_delta_rows": len(values),
            "proxy_r_delta_sum": round(sum(values), 8),
            "proxy_r_delta_mean": round(sum(values) / len(values), 8) if values else None,
        }
        for plate, values in sorted(grouped.items())
    }


def action_count_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {key: int(after.get(key, 0)) - int(before.get(key, 0)) for key in keys if int(after.get(key, 0)) != int(before.get(key, 0))}


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_implementation_action_after_source_m15_repair_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    required_paths = [
        build_script,
        verify_script,
        ledger_path,
        summary_path,
        manifest_path,
        PREVIOUS_ACTION_SUMMARY,
        SOURCE_M15_REPAIR_SUMMARY,
        *INPUTS.values(),
    ]
    for path in required_paths:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    input_rows_by_plate = {plate: read_jsonl(path) for plate, path in INPUTS.items()}
    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    previous_summary = read_json(PREVIOUS_ACTION_SUMMARY)
    source_summary = read_json(SOURCE_M15_REPAIR_SUMMARY)

    expected_plate_counts = {plate: len(plate_rows) for plate, plate_rows in input_rows_by_plate.items()}
    expected_total = sum(expected_plate_counts.values())
    action_counts = counter(rows, "action_class")
    coverage_counts = counter(rows, "coverage_status")
    source_rows = [row for row in rows if row.get("source_plate") == "source_m15_ordering_repair"]
    affected_source_rows = [row for row in source_rows if row.get("m15_ordering_repair_status") == "REPAIRED_WITH_BOUNDED_ORDERING_PROXY"]
    source_proxy_rows = [row for row in source_rows if safe_float(row.get("ordering_proxy_midpoint_r")) is not None]

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("summary_manifest_safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("action_row_count_preserves_all_input_rows", len(rows) == expected_total == summary.get("action_rows"), {"rows": len(rows), "expected": expected_total}))
    checks.append(check("source_plate_counts_match_inputs", summary.get("source_plate_counts") == counter(rows, "source_plate") == expected_plate_counts))
    checks.append(check("action_class_counts_match_rows", summary.get("action_class_counts") == action_counts))
    checks.append(check("coverage_status_counts_match_rows", summary.get("coverage_status_counts") == coverage_counts))
    checks.append(check("primitive_family_counts_match_rows", summary.get("primitive_family_counts") == counter(rows, "primitive_family")))
    checks.append(check("branch_decision_counts_match_rows", summary.get("branch_decision_counts") == counter(rows, "branch_decision")))
    checks.append(check("implementation_decision_counts_match_rows", summary.get("implementation_decision_counts") == counter(rows, "implementation_decision")))
    checks.append(check("proxy_delta_summary_matches_rows", summary.get("proxy_delta_summary_by_plate") == proxy_delta_summary(rows), summary.get("proxy_delta_summary_by_plate")))
    checks.append(check("action_class_delta_matches_previous", summary.get("action_class_delta_vs_previous") == action_count_delta(previous_summary.get("action_class_counts", {}), action_counts)))
    checks.append(check("coverage_delta_matches_previous", summary.get("coverage_status_delta_vs_previous") == action_count_delta(previous_summary.get("coverage_status_counts", {}), coverage_counts)))

    checks.append(check("m15_ordering_repair_actions_closed", summary.get("m15_ordering_repair_actions_before") == 30 and summary.get("m15_ordering_repair_actions_after") == 0 and action_counts.get("M15_ORDERING_REPAIR", 0) == 0))
    checks.append(check("source_m15_rows_preserved", len(source_rows) == source_summary.get("rows") == 138))
    checks.append(check("source_m15_affected_rows_30", len(affected_source_rows) == source_summary.get("m15_ordering_repaired_rows") == 30))
    checks.append(check("source_m15_proxy_rows_30", len(source_proxy_rows) == source_summary.get("after_row_level_ordering_proxy_rows") == 30))
    checks.append(check("source_m15_exact_r_zero", all(row.get("exact_r") is None for row in source_rows) and source_summary.get("exact_r_rows") == 0))
    checks.append(check("source_m15_exact_chronology_zero", sum(1 for row in source_rows if row.get("exact_chronology_claim") is True) == 0 and source_summary.get("exact_chronology_true_rows") == 0))

    midpoint_sum = round(sum(safe_float(row.get("ordering_proxy_midpoint_r")) or 0.0 for row in source_proxy_rows), 6)
    lower_sum = round(sum(safe_float(row.get("ordering_proxy_lower_r")) or 0.0 for row in source_proxy_rows), 6)
    upper_sum = round(sum(safe_float(row.get("ordering_proxy_upper_r")) or 0.0 for row in source_proxy_rows), 6)
    checks.append(check("source_m15_midpoint_sum_matches", midpoint_sum == source_summary.get("ordering_proxy_midpoint_sum"), midpoint_sum))
    checks.append(check("source_m15_lower_sum_matches", lower_sum == source_summary.get("ordering_proxy_lower_sum"), lower_sum))
    checks.append(check("source_m15_upper_sum_matches", upper_sum == source_summary.get("ordering_proxy_upper_sum"), upper_sum))
    checks.append(check("source_m15_bounds_summary_matches", summary.get("source_m15_ordering_proxy_bounds") == {
        "rows": 30,
        "lower_sum": source_summary.get("ordering_proxy_lower_sum"),
        "midpoint_sum": source_summary.get("ordering_proxy_midpoint_sum"),
        "upper_sum": source_summary.get("ordering_proxy_upper_sum"),
        "exact_chronology_true_rows": 0,
    }))
    checks.append(check("source_m15_after_branch_counts_match", summary.get("source_m15_after_branch_decision_counts") == source_summary.get("after_branch_decision_counts")))
    checks.append(check("source_m15_evidence_counts_match", summary.get("source_m15_ordering_evidence_source_counts") == source_summary.get("ordering_evidence_source_counts")))

    expected_delta = {
        "KEEP": 20,
        "KEEP_REPAIR_OR_AVOID": 3,
        "KILL": 3,
        "M15_ORDERING_REPAIR": -30,
        "PRESERVE_REQUIREMENT": 4,
    }
    checks.append(check("action_delta_expected", summary.get("action_class_delta_vs_previous") == expected_delta, summary.get("action_class_delta_vs_previous")))

    row_errors = []
    source_seen: Counter[tuple[str, str]] = Counter()
    for row in rows:
        source_plate = str(row.get("source_plate") or "")
        source_key = (source_plate, str(row.get("source_row_id") or row.get("source_line_no")))
        source_seen[source_key] += 1
        if row.get("route_id") != ROUTE_ID:
            row_errors.append({"line": row["_line_no"], "error": "route_id_mismatch"})
        if row.get("safe_flags") != SAFE_FLAGS or row.get("no_live_behavior") is not True or row.get("no_shadow_log_append") is not True or row.get("no_promotion") is not True:
            row_errors.append({"line": row["_line_no"], "error": "safe_flag_or_no_effect_mismatch"})
        if row.get("exact_r") is not None:
            row_errors.append({"line": row["_line_no"], "error": "exact_r_claim_opened"})
        if row.get("action_class") == "REVIEW_REQUIRED" or row.get("coverage_status") == "REVIEW_REQUIRED":
            row_errors.append({"line": row["_line_no"], "error": "unclassified_review_required"})
        if not row.get("primitive_family") or not row.get("next_action"):
            row_errors.append({"line": row["_line_no"], "error": "missing_family_or_next_action"})
    duplicate_sources = [key for key, count in source_seen.items() if count != 1]
    checks.append(check("all_action_rows_safe_classified_and_source_bound", not row_errors, row_errors[:20]))
    checks.append(check("each_source_row_preserved_once", not duplicate_sources, duplicate_sources[:20]))

    manifest_input_errors = []
    for path in [*INPUTS.values(), PREVIOUS_ACTION_SUMMARY, SOURCE_M15_REPAIR_SUMMARY]:
        artifact = manifest.get("input_artifacts", {}).get(path.name)
        if not artifact:
            manifest_input_errors.append({"path": path.name, "error": "missing_manifest_input"})
            continue
        if artifact.get("sha256") != sha256(path):
            manifest_input_errors.append({"path": path.name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_input_errors.append({"path": path.name, "error": "size_mismatch"})
    checks.append(check("manifest_input_hashes_match", not manifest_input_errors, manifest_input_errors))

    manifest_output_errors = []
    for name, artifact in manifest.get("output_artifacts", {}).items():
        path = ROUTE_DIR / name
        if not path.exists():
            manifest_output_errors.append({"path": name, "error": "missing"})
            continue
        if artifact.get("sha256") != sha256(path):
            manifest_output_errors.append({"path": name, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            manifest_output_errors.append({"path": name, "error": "size_mismatch"})
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
            "action_rows": len(rows),
            "source_plate_counts": expected_plate_counts,
            "action_class_counts": action_counts,
            "coverage_status_counts": coverage_counts,
            "source_m15_rows": len(source_rows),
            "source_m15_affected_rows": len(affected_source_rows),
            "source_m15_proxy_rows": len(source_proxy_rows),
            "proxy_delta_summary_by_plate": summary.get("proxy_delta_summary_by_plate"),
            "action_class_delta_vs_previous": summary.get("action_class_delta_vs_previous"),
        },
        "plate_decision": "IMPLEMENTATION_ACTION_QUEUE_CONSUMES_SOURCE_M15_ORDERING_REPAIR",
        "can_mark_implementation_action_after_source_m15_repair_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
