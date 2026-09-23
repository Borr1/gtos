from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CONFIDENCE_FILTER_QUARANTINE"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 2
EXPECTED_MANIFEST_OUTPUT_COUNT = 2
EXPECTED_B12_TRADES_EVALUATED = 312
EXPECTED_B12_FAMILY_SIZE = 8


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


def resolve_display_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO / path


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
    if summary.get("confidence_filter_mode") != "shadow":
        issues.append(f"confidence_filter_mode_unexpected:{summary.get('confidence_filter_mode')}")
    if summary.get("b12_confidence_trades_evaluated") != EXPECTED_B12_TRADES_EVALUATED:
        issues.append(f"b12_confidence_trades_evaluated_unexpected:{summary.get('b12_confidence_trades_evaluated')}")
    if summary.get("b12_confidence_family_size") != EXPECTED_B12_FAMILY_SIZE:
        issues.append(f"b12_confidence_family_size_unexpected:{summary.get('b12_confidence_family_size')}")
    if summary.get("b12_confidence_predictive_strata") != 0:
        issues.append(f"b12_confidence_predictive_strata_nonzero:{summary.get('b12_confidence_predictive_strata')}")
    if summary.get("confidence_filter_active_branch_present") is not True:
        issues.append("confidence_filter_active_branch_not_present")
    if summary.get("confidence_scorer_gold_price_config_present") is not True:
        issues.append("confidence_scorer_gold_price_config_not_present")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_not_active:{summary.get('runtime_halt_active')}")
    if summary.get("confidence_filter_quarantine_rows") != 1:
        issues.append(f"confidence_filter_quarantine_rows_unexpected:{summary.get('confidence_filter_quarantine_rows')}")

    for key in (
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "production_change_opened_now_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    actions = summary.get("ai_architecture_action_counts") or {}
    expected_action = "KEEP_CONFIDENCE_FILTER_SHADOW_AND_BLOCK_ACTIVE_PROMOTION_WITHOUT_FRESH_VALIDATION"
    if actions.get(expected_action) != 1:
        issues.append(f"expected_confidence_action_missing:{actions}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("confidence_filter_quarantine_materialized") is not True:
        issues.append("effect_confidence_quarantine_not_materialized")
    for key in (
        "confidence_filter_mode_changed",
        "live_ai_runtime_change_now",
        "runtime_decision_effect",
        "runtime_candidate_use_permitted",
        "candidate_use_allowed_now",
        "production_change_opened_now",
        "broker_operation",
        "paid_api_or_vendor_call",
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

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    for row in rows:
        row_id = row.get("ai_architecture_audit_row_id")
        for key in (
            "paid_api_or_vendor_call",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
            "production_change_opened_now",
            "broker_operation",
        ):
            if row.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "confidence_filter_mode": summary.get("confidence_filter_mode"),
        "b12_confidence_trades_evaluated": summary.get("b12_confidence_trades_evaluated"),
        "b12_confidence_predictive_strata": summary.get("b12_confidence_predictive_strata"),
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
