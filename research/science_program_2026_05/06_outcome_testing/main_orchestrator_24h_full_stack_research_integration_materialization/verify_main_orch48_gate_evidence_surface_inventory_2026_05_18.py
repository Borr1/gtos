from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_GATE_EVIDENCE_SURFACE_INVENTORY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 6
EXPECTED_MANIFEST_OUTPUT_COUNT = 2


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('rows')}:{len(rows)}")

    expected_surfaces = {
        "touch_count_gate",
        "sl_beyond_ob_l2",
        "pre_ai_h1_poi_availability",
        "confidence_filter",
        "cross_instrument_correlation_gate",
        "session_57_runtime_halt_boundary",
    }
    surfaces = {str(row.get("gate_surface") or "") for row in rows}
    if surfaces != expected_surfaces:
        issues.append(f"gate_surfaces_unexpected:{sorted(surfaces)}")

    by_surface = {str(row.get("gate_surface") or ""): row for row in rows}
    if int(by_surface.get("touch_count_gate", {}).get("decision_rows") or 0) <= 0:
        issues.append("touch_count_decision_rows_not_positive")
    if int(by_surface.get("sl_beyond_ob_l2", {}).get("decision_rows") or 0) <= 0:
        issues.append("sl_beyond_decision_rows_not_positive")
    if int(by_surface.get("pre_ai_h1_poi_availability", {}).get("pre_ai_gate_skipped_rows") or 0) <= 0:
        issues.append("pre_ai_skip_rows_not_positive")
    if by_surface.get("sl_beyond_ob_l2", {}).get("config_shadow_logger_enabled") is not True:
        issues.append("sl_beyond_config_not_enabled")
    if by_surface.get("confidence_filter", {}).get("confidence_filter_mode") != "shadow":
        issues.append("confidence_filter_not_shadow")
    if by_surface.get("confidence_filter", {}).get("b12_confidence_predictive_strata") != 0:
        issues.append("confidence_filter_predictive_strata_nonzero")
    if by_surface.get("cross_instrument_correlation_gate", {}).get("capture_status") != (
        "CAPTURE_GAP_DEDICATED_DECISION_LOG_MISSING"
    ):
        issues.append("cross_instrument_capture_gap_not_recorded")
    if by_surface.get("session_57_runtime_halt_boundary", {}).get("runtime_halt_active") is not True:
        issues.append("runtime_halt_not_active")

    if int(summary.get("capture_gap_rows") or 0) < 1:
        issues.append("capture_gap_rows_not_positive")
    if summary.get("runtime_halt_active") is not True:
        issues.append("summary_runtime_halt_not_active")

    effect = summary.get("implementation_effect") or {}
    if effect.get("gate_evidence_inventory_materialized") is not True:
        issues.append("effect_inventory_not_materialized")
    for key in (
        "runtime_decision_effect",
        "production_change_opened_now",
        "runtime_candidate_use_permitted",
        "broker_operation",
        "paid_api_or_vendor_call",
        "live_runtime_restart_now",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUT_COUNT:
        issues.append(f"manifest_output_count_unexpected:{len(output_by_name)}")

    for row in rows:
        row_id = row.get("gate_surface_row_id")
        for key in ("runtime_decision_effect", "production_change_opened_now", "broker_operation", "paid_api_or_vendor_call"):
            if row.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "gate_surfaces_with_decision_rows": summary.get("gate_surfaces_with_decision_rows"),
        "capture_gap_rows": summary.get("capture_gap_rows"),
        "runtime_halt_active": summary.get("runtime_halt_active"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
