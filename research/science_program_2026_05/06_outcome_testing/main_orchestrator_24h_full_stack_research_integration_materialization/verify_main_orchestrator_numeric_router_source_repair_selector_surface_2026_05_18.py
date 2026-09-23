from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 1119
EXPECTED_INPUT_ACTION_ROWS = 17753
EXPECTED_STATUS_COUNTS = {
    "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT": 11,
    "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR": 1108,
}
EXPECTED_STATUS_ACTION_COUNTS = {
    "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT": 7045,
    "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR": 10708,
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
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("selector_surface_rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("input_action_rows") != EXPECTED_INPUT_ACTION_ROWS:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")
    if summary.get("source_repair_selector_surface_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(
            f"status_counts_unexpected:{summary.get('source_repair_selector_surface_status_counts')}"
        )
    if summary.get("source_repair_selector_surface_status_input_action_counts") != EXPECTED_STATUS_ACTION_COUNTS:
        issues.append(
            "status_action_counts_unexpected:"
            f"{summary.get('source_repair_selector_surface_status_input_action_counts')}"
        )
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
    if summary.get("source_packet_context_payload_rows") != 11:
        issues.append(f"packet_context_rows_unexpected:{summary.get('source_packet_context_payload_rows')}")
    if summary.get("source_packet_context_payload_input_action_rows") != 7045:
        issues.append(
            "packet_context_input_action_rows_unexpected:"
            f"{summary.get('source_packet_context_payload_input_action_rows')}"
        )
    if summary.get("requires_prospective_execution_identity_capture_rows") != 11:
        issues.append(
            "requires_prospective_execution_identity_capture_rows_unexpected:"
            f"{summary.get('requires_prospective_execution_identity_capture_rows')}"
        )
    if summary.get("requires_prospective_execution_identity_capture_input_action_rows") != 7045:
        issues.append(
            "requires_prospective_execution_identity_capture_input_action_rows_unexpected:"
            f"{summary.get('requires_prospective_execution_identity_capture_input_action_rows')}"
        )

    for key in (
        "exact_r_repaired_by_this_selector_rows",
        "slippage_join_repaired_by_this_selector_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    ready_rows = [
        row
        for row in rows
        if row.get("source_repair_selector_surface_status")
        == "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
    ]
    packet_rows = [
        row
        for row in rows
        if row.get("source_repair_selector_surface_status")
        == "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT"
    ]
    for row in ready_rows[:25]:
        if not row.get("trade_params_source_repair_identity_patch"):
            issues.append(f"ready_row_missing_trade_params_patch:{row.get('source_repair_selector_surface_row_id')}")
            break
        if row.get("source_packet_context_payload") is not None:
            issues.append(f"ready_row_has_packet_context:{row.get('source_repair_selector_surface_row_id')}")
            break
    for row in packet_rows:
        row_id = row.get("source_repair_selector_surface_row_id")
        payload = row.get("source_packet_context_payload")
        if not isinstance(payload, dict):
            issues.append(f"packet_row_missing_payload:{row_id}")
            break
        if payload.get("direct_execution_identity_found_rows") != 0:
            issues.append(f"packet_row_direct_identity_nonzero:{row_id}")
            break
        if row.get("trade_params_source_repair_identity_patch") is not None:
            issues.append(f"packet_row_has_trade_params_patch:{row_id}")
            break
        if row.get("requires_prospective_execution_identity_capture") is not True:
            issues.append(f"packet_row_capture_flag_missing:{row_id}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_source_repair_selector_surface_available") is not True:
        issues.append("selector_surface_effect_missing")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SELECTOR_SURFACE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "selector_surface_rows": len(rows),
        "input_action_rows": summary.get("input_action_rows"),
        "source_repair_selector_surface_status_counts": summary.get(
            "source_repair_selector_surface_status_counts"
        ),
        "trade_params_source_repair_identity_patch_rows": summary.get(
            "trade_params_source_repair_identity_patch_rows"
        ),
        "source_packet_context_payload_rows": summary.get("source_packet_context_payload_rows"),
        "exact_r_repaired_by_this_selector_rows": summary.get("exact_r_repaired_by_this_selector_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
