from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 1119
EXPECTED_INPUT_ACTION_ROWS = 17753
EXPECTED_STATUS_COUNTS = {
    "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY": 1108,
    "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT": 11,
}
EXPECTED_STATUS_INPUT_ACTION_COUNTS = {
    "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY": 10708,
    "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT": 7045,
}
EXPECTED_ROUTE_COUNTS = {
    "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE": 1108,
    "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE": 11,
}
EXPECTED_GEOMETRY_FIELD_COUNT = 12
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
        issues.append(f"ledger_row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("input_action_rows") != EXPECTED_INPUT_ACTION_ROWS:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")
    if summary.get("execution_identity_capture_contract_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(
            "contract_status_counts_unexpected:"
            f"{summary.get('execution_identity_capture_contract_status_counts')}"
        )
    if (
        summary.get("execution_identity_capture_contract_status_input_action_counts")
        != EXPECTED_STATUS_INPUT_ACTION_COUNTS
    ):
        issues.append(
            "contract_status_action_counts_unexpected:"
            f"{summary.get('execution_identity_capture_contract_status_input_action_counts')}"
        )
    if summary.get("source_repair_selector_route_status_counts") != EXPECTED_ROUTE_COUNTS:
        issues.append(
            "route_status_counts_unexpected:"
            f"{summary.get('source_repair_selector_route_status_counts')}"
        )

    for key in (
        "source_repair_queue_route_bound_rows",
        "row_identity_bound_to_numeric_router_source_repair_queue_rows",
        "capture_patch_fields_bound_to_route_rows",
        "requires_execution_capture_row_for_exact_r_rows",
    ):
        if summary.get(key) != EXPECTED_ROWS:
            issues.append(f"{key}_unexpected:{summary.get(key)}")
            break

    if summary.get("trade_params_source_repair_identity_patch_rows") != 1108:
        issues.append(
            "trade_params_patch_rows_unexpected:"
            f"{summary.get('trade_params_source_repair_identity_patch_rows')}"
        )
    if summary.get("trade_params_source_repair_identity_patch_input_action_rows") != 10708:
        issues.append(
            "trade_params_patch_input_action_rows_unexpected:"
            f"{summary.get('trade_params_source_repair_identity_patch_input_action_rows')}"
        )
    if summary.get("source_repair_identity_key_rows") != 1108:
        issues.append(f"source_repair_identity_key_rows_unexpected:{summary.get('source_repair_identity_key_rows')}")
    if summary.get("source_packet_context_payload_rows") != 11:
        issues.append(f"source_packet_context_payload_rows_unexpected:{summary.get('source_packet_context_payload_rows')}")
    if summary.get("source_packet_context_payload_input_action_rows") != 7045:
        issues.append(
            "source_packet_context_payload_input_action_rows_unexpected:"
            f"{summary.get('source_packet_context_payload_input_action_rows')}"
        )
    if summary.get("source_packet_route_requires_prospective_execution_identity_capture_rows") != 11:
        issues.append(
            "source_packet_route_requires_prospective_execution_identity_capture_rows_unexpected:"
            f"{summary.get('source_packet_route_requires_prospective_execution_identity_capture_rows')}"
        )
    if summary.get("required_execution_geometry_field_count_min") != EXPECTED_GEOMETRY_FIELD_COUNT:
        issues.append(
            "required_execution_geometry_field_count_min_unexpected:"
            f"{summary.get('required_execution_geometry_field_count_min')}"
        )
    if summary.get("required_execution_geometry_field_count_max") != EXPECTED_GEOMETRY_FIELD_COUNT:
        issues.append(
            "required_execution_geometry_field_count_max_unexpected:"
            f"{summary.get('required_execution_geometry_field_count_max')}"
        )
    if summary.get("missing_capture_schema_field_rows") != 0:
        issues.append(f"missing_capture_schema_field_rows_nonzero:{summary.get('missing_capture_schema_field_rows')}")

    for key in (
        "current_historical_slippage_rows_bound_to_contract",
        "exact_r_repaired_by_this_contract_rows",
        "slippage_join_repaired_by_this_contract_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    identity_rows = [
        row
        for row in rows
        if row.get("execution_identity_capture_contract_status")
        == "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
    ]
    packet_rows = [
        row
        for row in rows
        if row.get("execution_identity_capture_contract_status")
        == "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    ]
    for row in identity_rows[:25]:
        if not row.get("source_repair_identity_key"):
            issues.append(f"identity_contract_missing_identity_key:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if not row.get("trade_params_source_repair_identity_patch"):
            issues.append(f"identity_contract_missing_trade_params_patch:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if row.get("source_packet_context_payload") is not None:
            issues.append(f"identity_contract_has_packet_payload:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if row.get("capture_patch_field_count") != EXPECTED_GEOMETRY_FIELD_COUNT:
            issues.append(f"identity_contract_capture_field_count_unexpected:{row.get('execution_identity_capture_contract_row_id')}")
            break
    for row in packet_rows:
        if row.get("source_repair_identity_key"):
            issues.append(f"packet_contract_has_identity_key:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if row.get("trade_params_source_repair_identity_patch") is not None:
            issues.append(f"packet_contract_has_trade_params_patch:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if not isinstance(row.get("source_packet_context_payload"), dict):
            issues.append(f"packet_contract_missing_payload:{row.get('execution_identity_capture_contract_row_id')}")
            break
        if row.get("source_packet_route_requires_prospective_execution_identity_capture") is not True:
            issues.append(f"packet_contract_missing_capture_flag:{row.get('execution_identity_capture_contract_row_id')}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_execution_identity_capture_contract_available") is not True:
        issues.append("default_off_capture_contract_effect_missing")
    if effect.get("selector_route_rows_bound_to_slippage_capture_schema") != EXPECTED_ROWS:
        issues.append(
            "selector_route_rows_bound_to_slippage_capture_schema_unexpected:"
            f"{effect.get('selector_route_rows_bound_to_slippage_capture_schema')}"
        )
    if effect.get("runtime_trading_or_live_broker_effect") is not False:
        issues.append("runtime_trading_or_live_broker_effect_claimed")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_IDENTITY_CAPTURE_CONTRACT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "contract_rows": len(rows),
        "input_action_rows": summary.get("input_action_rows"),
        "execution_identity_capture_contract_status_counts": summary.get(
            "execution_identity_capture_contract_status_counts"
        ),
        "row_identity_bound_to_numeric_router_source_repair_queue_rows": summary.get(
            "row_identity_bound_to_numeric_router_source_repair_queue_rows"
        ),
        "trade_params_source_repair_identity_patch_rows": summary.get(
            "trade_params_source_repair_identity_patch_rows"
        ),
        "source_packet_context_payload_rows": summary.get("source_packet_context_payload_rows"),
        "requires_execution_capture_row_for_exact_r_rows": summary.get(
            "requires_execution_capture_row_for_exact_r_rows"
        ),
        "exact_r_repaired_by_this_contract_rows": summary.get("exact_r_repaired_by_this_contract_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    if result["manifest_output_count"] != EXPECTED_MANIFEST_OUTPUT_COUNT:
        result["issues"].append(f"manifest_output_count_unexpected:{result['manifest_output_count']}")
        result["ok"] = False
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
