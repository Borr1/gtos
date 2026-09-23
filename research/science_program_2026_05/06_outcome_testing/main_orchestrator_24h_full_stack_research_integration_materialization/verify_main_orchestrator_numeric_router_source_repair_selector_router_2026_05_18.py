from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
EVENT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_EVENT_LEDGER_{DATE}.jsonl"
ROUTER_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 1119
EXPECTED_INPUT_ACTION_ROWS = 17753
EXPECTED_EVENT_COUNTS = {
    "SOURCE_REPAIR_SELECTOR_EVENT_PACKET_CONTEXT_READY_FOR_PROSPECTIVE_CAPTURE_ROUTER": 11,
    "SOURCE_REPAIR_SELECTOR_EVENT_READY_FOR_DEFAULT_OFF_ROUTER": 1108,
}
EXPECTED_ROUTE_COUNTS = {
    "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE": 1108,
    "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE": 11,
}
EXPECTED_ROUTE_ACTION_COUNTS = {
    "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE": 10708,
    "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE": 7045,
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


def resolve_display_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO / path


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (EVENT_LEDGER, ROUTER_LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    event_rows = read_jsonl(EVENT_LEDGER) if EVENT_LEDGER.exists() else []
    router_rows = read_jsonl(ROUTER_LEDGER) if ROUTER_LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(event_rows) != EXPECTED_ROWS:
        issues.append(f"event_row_count_unexpected:{len(event_rows)}")
    if len(router_rows) != EXPECTED_ROWS:
        issues.append(f"router_row_count_unexpected:{len(router_rows)}")
    if summary.get("selector_event_rows") != len(event_rows):
        issues.append("summary_event_rows_mismatch")
    if summary.get("selector_route_rows") != len(router_rows):
        issues.append("summary_router_rows_mismatch")
    if summary.get("input_action_rows") != EXPECTED_INPUT_ACTION_ROWS:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")
    if summary.get("source_repair_selector_event_status_counts") != EXPECTED_EVENT_COUNTS:
        issues.append(
            "event_status_counts_unexpected:"
            f"{summary.get('source_repair_selector_event_status_counts')}"
        )
    if summary.get("source_repair_selector_route_status_counts") != EXPECTED_ROUTE_COUNTS:
        issues.append(
            "route_status_counts_unexpected:"
            f"{summary.get('source_repair_selector_route_status_counts')}"
        )
    if summary.get("source_repair_selector_route_status_input_action_counts") != EXPECTED_ROUTE_ACTION_COUNTS:
        issues.append(
            "route_status_action_counts_unexpected:"
            f"{summary.get('source_repair_selector_route_status_input_action_counts')}"
        )

    for key in (
        "catalog_entry_found_rows",
        "catalog_entry_id_match_rows",
        "catalog_family_spec_id_match_rows",
        "event_routable_rows",
        "router_path_ready_default_off_rows",
        "catalog_matched_rows",
        "source_repair_queue_matched_rows",
        "expected_catalog_entry_matched_rows",
    ):
        if summary.get(key) != EXPECTED_ROWS:
            issues.append(f"{key}_unexpected:{summary.get(key)}")
            break

    expected_identity = EXPECTED_ROUTE_COUNTS["ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"]
    expected_packet = EXPECTED_ROUTE_COUNTS[
        "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
    ]
    if summary.get("trade_params_source_repair_identity_patch_rows") != expected_identity:
        issues.append(
            "trade_params_patch_rows_unexpected:"
            f"{summary.get('trade_params_source_repair_identity_patch_rows')}"
        )
    if summary.get("trade_params_source_repair_identity_patch_input_action_rows") != 10708:
        issues.append(
            "trade_params_patch_input_action_rows_unexpected:"
            f"{summary.get('trade_params_source_repair_identity_patch_input_action_rows')}"
        )
    if summary.get("source_packet_context_payload_rows") != expected_packet:
        issues.append(f"packet_context_rows_unexpected:{summary.get('source_packet_context_payload_rows')}")
    if summary.get("source_packet_context_payload_input_action_rows") != 7045:
        issues.append(
            "packet_context_input_action_rows_unexpected:"
            f"{summary.get('source_packet_context_payload_input_action_rows')}"
        )
    if summary.get("requires_prospective_execution_identity_capture_rows") != expected_packet:
        issues.append(
            "requires_prospective_execution_identity_capture_rows_unexpected:"
            f"{summary.get('requires_prospective_execution_identity_capture_rows')}"
        )

    for key in (
        "exact_r_repaired_by_this_event_rows",
        "slippage_join_repaired_by_this_event_rows",
        "exact_r_repaired_by_this_route_rows",
        "slippage_join_repaired_by_this_route_rows",
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
        for row in router_rows
        if row.get("source_repair_selector_route_status")
        == "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"
    ]
    packet_rows = [
        row
        for row in router_rows
        if row.get("source_repair_selector_route_status")
        == "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
    ]
    for row in identity_rows[:25]:
        if not row.get("trade_params_source_repair_identity_patch"):
            issues.append(f"identity_route_missing_patch:{row.get('source_repair_selector_route_row_id')}")
            break
        if row.get("source_packet_context_payload") is not None:
            issues.append(f"identity_route_has_packet_context:{row.get('source_repair_selector_route_row_id')}")
            break
        if row.get("expected_catalog_entry_match_count") != 1:
            issues.append(f"identity_route_expected_match_not_one:{row.get('source_repair_selector_route_row_id')}")
            break
    for row in packet_rows:
        if not isinstance(row.get("source_packet_context_payload"), dict):
            issues.append(f"packet_route_missing_payload:{row.get('source_repair_selector_route_row_id')}")
            break
        if row.get("trade_params_source_repair_identity_patch") is not None:
            issues.append(f"packet_route_has_trade_params_patch:{row.get('source_repair_selector_route_row_id')}")
            break
        if row.get("requires_prospective_execution_identity_capture") is not True:
            issues.append(f"packet_route_capture_flag_missing:{row.get('source_repair_selector_route_row_id')}")
            break
        if row.get("expected_catalog_entry_match_count") != 1:
            issues.append(f"packet_route_expected_match_not_one:{row.get('source_repair_selector_route_row_id')}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_selector_event_router_available") is not True:
        issues.append("selector_event_router_effect_missing")
    if effect.get("catalog_evaluation_include_source_repair_required") is not True:
        issues.append("include_source_repair_requirement_missing")
    if effect.get("runtime_trading_or_live_broker_effect") is not False:
        issues.append("runtime_trading_or_live_broker_effect_claimed")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (EVENT_LEDGER, ROUTER_LEDGER, SUMMARY):
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_ROUTER",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "selector_event_rows": len(event_rows),
        "selector_route_rows": len(router_rows),
        "input_action_rows": summary.get("input_action_rows"),
        "source_repair_selector_route_status_counts": summary.get(
            "source_repair_selector_route_status_counts"
        ),
        "router_path_ready_default_off_rows": summary.get("router_path_ready_default_off_rows"),
        "trade_params_source_repair_identity_patch_rows": summary.get(
            "trade_params_source_repair_identity_patch_rows"
        ),
        "source_packet_context_payload_rows": summary.get("source_packet_context_payload_rows"),
        "exact_r_repaired_by_this_route_rows": summary.get("exact_r_repaired_by_this_route_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
