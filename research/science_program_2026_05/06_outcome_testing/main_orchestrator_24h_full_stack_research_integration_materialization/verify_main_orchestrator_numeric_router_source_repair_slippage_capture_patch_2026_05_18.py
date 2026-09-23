from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH_VERIFY_RESULT_{DATE}.json"
EXPECTED_FIELD_COUNT = 12
EXPECTED_STATUS = "PROSPECTIVE_SLIPPAGE_CAPTURE_SCHEMA_PRESENT_WITH_STATUS_GUARDS"


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

    if summary.get("rows") != len(rows):
        issues.append("rows_mismatch")
    if len(rows) != EXPECTED_FIELD_COUNT:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("all_repair_fields_have_slippage_schema_rows") is not True:
        issues.append("not_all_repair_fields_have_slippage_schema_rows")
    if summary.get("prospective_capture_status_counts") != {EXPECTED_STATUS: EXPECTED_FIELD_COUNT}:
        issues.append(f"status_counts_unexpected:{summary.get('prospective_capture_status_counts')}")

    for key in (
        "row_identity_bound_to_numeric_router_source_repair_queue_rows",
        "exact_r_repaired_by_this_patch_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    for surface in summary.get("code_surfaces") or []:
        path = REPO / surface.get("path", "")
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    for row in rows:
        row_id = row.get("slippage_capture_patch_row_id")
        if row.get("prospective_capture_status") != EXPECTED_STATUS:
            issues.append(f"unexpected_capture_status:{row_id}")
            break
        if "src/components/slippage_shadow_logger.py" not in row.get("source_code_hits", []):
            issues.append(f"slippage_logger_source_hit_missing:{row_id}")
            break
        if row.get("row_identity_bound_to_numeric_router_source_repair_queue") is not False:
            issues.append(f"unexpected_row_identity_binding:{row_id}")
            break
        if row.get("exact_r_repaired_by_this_patch") is not False:
            issues.append(f"unexpected_exact_r_repair_claim:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_enabled:{row_id}")
            break
        effect = row.get("implementation_effect") or {}
        if effect.get("prospective_observability_schema_effect") is not True:
            issues.append(f"observability_schema_effect_missing:{row_id}")
            break
        if effect.get("runtime_trading_or_live_broker_effect") is not False:
            issues.append(f"trading_or_broker_effect_claimed:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_CAPTURE_PATCH",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "prospective_capture_status_counts": summary.get("prospective_capture_status_counts"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
