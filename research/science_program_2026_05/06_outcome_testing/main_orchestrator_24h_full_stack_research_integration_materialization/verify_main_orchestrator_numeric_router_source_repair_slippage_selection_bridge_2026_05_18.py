from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_MANIFEST_{DATE}.json"
VERIFY_RESULT = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE_VERIFY_RESULT_{DATE}.json"
)

EXPECTED_ROWS = 1119
EXPECTED_STATUS_COUNTS = {
    "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH": 1108,
    "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED": 11,
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

    if summary.get("selection_event_rows") != len(rows):
        issues.append("rows_mismatch")
    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("slippage_selection_event_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(
            f"status_counts_unexpected:{summary.get('slippage_selection_event_status_counts')}"
        )
    if summary.get("trade_params_patch_rows") != 1108:
        issues.append(f"trade_params_patch_rows_unexpected:{summary.get('trade_params_patch_rows')}")
    if summary.get("requires_explicit_future_source_repair_row_selection_rows") != 1108:
        issues.append(
            "requires_explicit_future_source_repair_row_selection_rows_unexpected:"
            f"{summary.get('requires_explicit_future_source_repair_row_selection_rows')}"
        )

    for key in (
        "exact_r_repaired_by_this_selection_event_rows",
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
    if effect.get("default_off_selection_to_trade_params_identity_patch_self_check") is not True:
        issues.append("selection_self_check_effect_missing")
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
        if row.get("slippage_selection_event_status")
        == "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH"
    ]
    if len(ready_rows) != 1108:
        issues.append(f"ready_rows_unexpected:{len(ready_rows)}")
    for row in ready_rows[:25]:
        row_id = row.get("slippage_selection_event_row_id")
        if row.get("expected_source_repair_identity_key") != row.get("selected_source_repair_identity_key"):
            issues.append(f"identity_key_mismatch:{row_id}")
            break
        patch = row.get("trade_params_source_repair_identity_patch") or {}
        payload = patch.get("source_repair_identity") or {}
        if set(payload) != {
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        }:
            issues.append(f"payload_fields_unexpected:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"runtime_candidate_enabled:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_SELECTION_BRIDGE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "selection_event_rows": len(rows),
        "slippage_selection_event_status_counts": summary.get("slippage_selection_event_status_counts"),
        "trade_params_patch_rows": summary.get("trade_params_patch_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
