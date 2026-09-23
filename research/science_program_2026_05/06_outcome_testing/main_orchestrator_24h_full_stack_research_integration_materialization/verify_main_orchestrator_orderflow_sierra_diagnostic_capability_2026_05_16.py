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


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def nested_get(row: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = row
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_orderflow_sierra_diagnostic_capability_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY_VERIFICATION_RESULT_{DATE}.json"

    lto011_path = REPO_ROOT / "research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json"
    lto012_path = REPO_ROOT / "research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json"
    lto014_path = REPO_ROOT / "research/program_control/LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.json"
    lto033_path = REPO_ROOT / "research/program_control/LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    lto011 = read_json(lto011_path)
    lto012 = read_json(lto012_path)
    lto014 = read_json(lto014_path)
    lto033 = read_json(lto033_path)

    row_type_counts = Counter(row.get("row_type") for row in ledger)
    expected_counts = {
        "PLATE_DECISION_ROW": 5,
        "NAS100_FEATURE_FAMILY_PLAN_ROW": len(lto011.get("status_row", {}).get("feature_family_forward_plan", [])),
        "SIERRA_FEATURE_STATUS_ROW": len(lto012.get("status_row", {}).get("feature_status_counts", {})),
        "SIERRA_INTERPRETATION_STATUS_ROW": len(lto012.get("status_row", {}).get("interpretation_status_counts", {})),
        "SIERRA_SYMBOL_FEATURE_STATUS_ROW": len(lto012.get("status_row", {}).get("symbol_feature_status_counts", {})),
        "GBPJPY_PROXY_CANDIDATE_ROW": len(lto014.get("candidate_status_rows", [])),
        "GBPJPY_PROXY_TEST_ROW": len(lto014.get("pre_registered_tests", [])),
        "ORDERFLOW_PRIMITIVE_ROW": len(lto033.get("primitive_registry", [])),
        "ORDERFLOW_SOURCE_BLOCKER_ROW": len(lto033.get("status_row", {}).get("blocker_codes", [])),
        "SOURCE_LOG_SNAPSHOT_ROW": 7,
    }

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_summary_manifest_preserved", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("all_ledger_rows_have_safe_flags", all(row.get("safe_flags") == SAFE_FLAGS for row in ledger)))
    checks.append(check("row_type_counts_match_expected", dict(row_type_counts) == expected_counts, {"actual": dict(row_type_counts), "expected": expected_counts}))
    checks.append(check("output_row_count_matches_summary", summary.get("output_ledger_rows") == len(ledger) == sum(expected_counts.values())))

    checks.append(check("nas100_status_matches_source", summary.get("nas100_databento_status") == lto011.get("status") == "WAITING_FOR_DATABENTO_LIVE_LICENSE"))
    checks.append(check("nas100_license_blocker_preserved", summary.get("nas100_license_blocker") is True))
    checks.append(check("nas100_sample_floors_not_met", nested_get(lto011, ["status_row", "readiness_gates", "broker_actual_r_floor_met"]) is False and nested_get(lto011, ["status_row", "readiness_gates", "mbp10_candidate_floor_met"]) is False))
    checks.append(check("nas100_live_record_rows_zero", summary.get("nas100_live_record_rows") == 0))

    checks.append(check("sierra_candidate_count_current", summary.get("sierra_latest_candidate_rows") == nested_get(lto012, ["status_row", "current_counts", "latest_candidate_rows"]) == 274))
    checks.append(check("sierra_feature_rows_current", summary.get("sierra_features_extracted") == nested_get(lto012, ["status_row", "current_counts", "features_extracted"]) == 52))
    checks.append(check("sierra_missing_feature_rows_zero", summary.get("sierra_missing_feature_rows") == 0))
    checks.append(check("sierra_background_queue_preserved", summary.get("sierra_background_queue_candidates") == 195))
    checks.append(check("sierra_file_size_guard_preserved", summary.get("sierra_file_size_guard_candidates") == 11))
    checks.append(check("sierra_no_proxy_candidates_preserved", summary.get("sierra_no_registered_proxy_candidates") == 24))

    checks.append(check("gbpjpy_candidate_rows_preserved", summary.get("gbpjpy_candidate_status_rows") == len(lto014.get("candidate_status_rows", [])) == 24))
    checks.append(check("gbpjpy_no_proxy_preserved", summary.get("gbpjpy_direct_proxy_registered") is False and summary.get("gbpjpy_existing_confluence_inferred") is False))
    checks.append(check("gbpjpy_price_transfer_gate_not_met", summary.get("gbpjpy_zero_lag_corr") == nested_get(lto014, ["price_transfer_validation", "current_gate_readout", "zero_lag_corr"]) and nested_get(lto014, ["price_transfer_validation", "current_gate_readout", "zero_lag_corr_gate_met"]) is False))
    checks.append(check("gbpjpy_no_outcomes_opened_preserved", summary.get("gbpjpy_outcomes_opened") is False))

    checks.append(check("primitive_count_preserved", summary.get("orderflow_primitive_count") == len(lto033.get("primitive_registry", [])) == 6))
    checks.append(check("primitive_blocker_count_preserved", summary.get("orderflow_blocker_count") == len(lto033.get("status_row", {}).get("blocker_codes", [])) == 8))
    checks.append(check("primitive_no_lookahead_pass", summary.get("orderflow_no_lookahead_status") == "PASS"))
    checks.append(check("stacked_imbalance_coverage_zero_preserved", summary.get("orderflow_field_coverage", {}).get("X1_STACKED_IMBALANCE_FOOTPRINT_V1") == 0.0))
    checks.append(check("volume_profile_partial_coverage_preserved", summary.get("orderflow_field_coverage", {}).get("VP_VOLUME_PROFILE_CONTEXT_V1") == 0.714286))

    decision_families = {row.get("family"): row.get("materialized_decision") for row in ledger if row.get("row_type") == "PLATE_DECISION_ROW"}
    checks.append(
        check(
            "materialized_decisions_match_summary",
            decision_families == summary.get("materialized_decisions"),
            {"ledger": decision_families, "summary": summary.get("materialized_decisions")},
        )
    )

    manifest_errors: list[dict[str, Any]] = []
    for section in ("artifacts", "input_artifacts"):
        for artifact in manifest.get(section, []):
            path = REPO_ROOT / artifact["path"]
            if not artifact.get("exists"):
                if artifact.get("sha256") is not None:
                    manifest_errors.append({"path": artifact["path"], "error": "missing_with_hash"})
                continue
            if not path.exists():
                manifest_errors.append({"path": artifact["path"], "error": "missing"})
                continue
            if path.stat().st_size != artifact.get("size_bytes"):
                manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
            actual_hash = sha256(path)
            if actual_hash != artifact.get("sha256"):
                manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual_hash})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "output_ledger_rows": len(ledger),
            "row_type_counts": dict(row_type_counts),
            "nas100_cached_mbp10_candidate_rows": summary.get("nas100_cached_mbp10_candidate_rows"),
            "sierra_latest_candidate_rows": summary.get("sierra_latest_candidate_rows"),
            "sierra_features_extracted": summary.get("sierra_features_extracted"),
            "gbpjpy_candidate_status_rows": summary.get("gbpjpy_candidate_status_rows"),
            "orderflow_primitive_count": summary.get("orderflow_primitive_count"),
            "source_log_line_counts": summary.get("source_log_line_counts"),
        },
        "can_mark_orderflow_sierra_diagnostic_capability_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
