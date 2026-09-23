from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 1119
EXPECTED_STATUS_COUNTS = {
    "NOT_SLIPPAGE_JOIN_APPLICABLE_SOURCE_PACKET_REQUIRED": 11,
    "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT": 1108,
}
EXPECTED_STATUS_INPUT_ACTION_COUNTS = {
    "NOT_SLIPPAGE_JOIN_APPLICABLE_SOURCE_PACKET_REQUIRED": 7045,
    "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT": 10708,
}


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

    if summary.get("contract_rows") != len(rows):
        issues.append("rows_mismatch")
    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("slippage_join_contract_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(f"status_counts_unexpected:{summary.get('slippage_join_contract_status_counts')}")
    if summary.get("slippage_join_contract_status_input_action_counts") != EXPECTED_STATUS_INPUT_ACTION_COUNTS:
        issues.append(
            "status_input_action_counts_unexpected:"
            f"{summary.get('slippage_join_contract_status_input_action_counts')}"
        )
    if summary.get("slippage_row_identity_binding_required_rows") != 1108:
        issues.append("identity_binding_required_count_unexpected")

    for key in (
        "current_historical_slippage_rows_bound_to_contract",
        "exact_r_repaired_by_this_contract_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("prospective_observability_schema_effect") is not True:
        issues.append("observability_schema_effect_missing")
    if effect.get("runtime_trading_or_live_broker_effect") is not False:
        issues.append("runtime_trading_or_live_broker_effect_claimed")

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

    ready_rows = [
        row
        for row in rows
        if row.get("slippage_join_contract_status") == "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT"
    ]
    if len(ready_rows) != 1108:
        issues.append(f"ready_rows_unexpected:{len(ready_rows)}")
    for row in ready_rows[:25]:
        row_id = row.get("slippage_join_contract_row_id")
        if not row.get("source_repair_identity_key"):
            issues.append(f"source_repair_identity_key_missing:{row_id}")
            break
        if row.get("required_source_repair_identity_fields") != [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ]:
            issues.append(f"identity_fields_unexpected:{row_id}")
            break
        if "order_ticket" not in row.get("required_order_identity_any_of", []):
            issues.append(f"order_identity_missing:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"runtime_candidate_enabled:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_JOIN_CONTRACT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "contract_rows": len(rows),
        "slippage_join_contract_status_counts": summary.get("slippage_join_contract_status_counts"),
        "slippage_row_identity_binding_required_rows": summary.get("slippage_row_identity_binding_required_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
