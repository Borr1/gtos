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
    "source_upgraded_degraded_branch_decisions": ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_LEDGER_{DATE}.jsonl",
}


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


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_implementation_recompute_branch_action_ledger_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path, *INPUTS.values()]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    input_rows_by_plate = {plate: read_jsonl(path) for plate, path in INPUTS.items()}
    rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    expected_plate_counts = {plate: len(plate_rows) for plate, plate_rows in input_rows_by_plate.items()}
    expected_total = sum(expected_plate_counts.values())

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("summary_manifest_safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("action_row_count_preserves_all_input_rows", len(rows) == expected_total == summary.get("action_rows"), {"rows": len(rows), "expected": expected_total}))
    checks.append(check("source_plate_counts_match_inputs", summary.get("source_plate_counts") == counter(rows, "source_plate") == expected_plate_counts))
    checks.append(check("action_class_counts_match_rows", summary.get("action_class_counts") == counter(rows, "action_class")))
    checks.append(check("coverage_status_counts_match_rows", summary.get("coverage_status_counts") == counter(rows, "coverage_status")))
    checks.append(check("primitive_family_counts_match_rows", summary.get("primitive_family_counts") == counter(rows, "primitive_family")))
    checks.append(check("branch_decision_counts_match_rows", summary.get("branch_decision_counts") == counter(rows, "branch_decision")))
    checks.append(check("implementation_decision_counts_match_rows", summary.get("implementation_decision_counts") == counter(rows, "implementation_decision")))
    checks.append(check("proxy_delta_summary_matches_rows", summary.get("proxy_delta_summary_by_plate") == proxy_delta_summary(rows), summary.get("proxy_delta_summary_by_plate")))

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
        if not row.get("primitive_family"):
            row_errors.append({"line": row["_line_no"], "error": "missing_primitive_family"})
        if not row.get("next_action"):
            row_errors.append({"line": row["_line_no"], "error": "missing_next_action"})
    duplicate_sources = [key for key, count in source_seen.items() if count != 1]
    checks.append(check("all_action_rows_safe_classified_and_source_bound", not row_errors, row_errors[:20]))
    checks.append(check("each_source_row_preserved_once", not duplicate_sources, duplicate_sources[:20]))

    manifest_input_errors = []
    for plate, path in INPUTS.items():
        artifact = manifest.get("input_artifacts", {}).get(path.name)
        if not artifact:
            manifest_input_errors.append({"path": path.name, "error": "missing_manifest_input", "plate": plate})
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
            "action_class_counts": summary.get("action_class_counts"),
            "coverage_status_counts": summary.get("coverage_status_counts"),
            "primitive_family_counts": summary.get("primitive_family_counts"),
            "proxy_delta_summary_by_plate": summary.get("proxy_delta_summary_by_plate"),
        },
        "plate_decision": "IMPLEMENTATION_RECOMPUTE_BRANCH_ACTIONS_MATERIALIZED_FROM_LATEST_SCORER_TICK_SOURCE_PLATES",
        "can_mark_implementation_recompute_branch_action_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
