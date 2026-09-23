from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 1119
EXPECTED_READY_ROWS = 1108
EXPECTED_PACKET_ABSENT_ROWS = 11
EXPECTED_STATUS_COUNTS = {
    "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT": EXPECTED_PACKET_ABSENT_ROWS,
    "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE": EXPECTED_READY_ROWS,
}
EXPECTED_STATUS_INPUT_ACTION_COUNTS = {
    "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT": 7045,
    "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE": 10708,
}
EXPECTED_CONTRACT_STATUS_COUNTS = {
    "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY": EXPECTED_READY_ROWS,
    "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT": EXPECTED_PACKET_ABSENT_ROWS,
}
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
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("future_slippage_lifecycle_emitter_status_counts") != EXPECTED_STATUS_COUNTS:
        issues.append(
            "emitter_status_counts_unexpected:"
            f"{summary.get('future_slippage_lifecycle_emitter_status_counts')}"
        )
    if summary.get("future_slippage_lifecycle_emitter_status_input_action_counts") != EXPECTED_STATUS_INPUT_ACTION_COUNTS:
        issues.append(
            "emitter_status_input_action_counts_unexpected:"
            f"{summary.get('future_slippage_lifecycle_emitter_status_input_action_counts')}"
        )
    if summary.get("execution_identity_capture_contract_status_counts") != EXPECTED_CONTRACT_STATUS_COUNTS:
        issues.append(
            "contract_status_counts_unexpected:"
            f"{summary.get('execution_identity_capture_contract_status_counts')}"
        )
    if summary.get("future_contract_complete_if_emitted_rows") != EXPECTED_READY_ROWS:
        issues.append(
            "future_contract_complete_if_emitted_rows_unexpected:"
            f"{summary.get('future_contract_complete_if_emitted_rows')}"
        )
    if summary.get("source_repair_identity_written_to_future_entry_payload_rows") != EXPECTED_READY_ROWS:
        issues.append(
            "source_repair_identity_written_to_future_entry_payload_rows_unexpected:"
            f"{summary.get('source_repair_identity_written_to_future_entry_payload_rows')}"
        )
    if summary.get("future_close_payload_joinable_by_order_ticket_rows") != EXPECTED_READY_ROWS:
        issues.append(
            "future_close_payload_joinable_by_order_ticket_rows_unexpected:"
            f"{summary.get('future_close_payload_joinable_by_order_ticket_rows')}"
        )
    if summary.get("packet_context_execution_identity_absent_rows") != EXPECTED_PACKET_ABSENT_ROWS:
        issues.append(
            "packet_context_execution_identity_absent_rows_unexpected:"
            f"{summary.get('packet_context_execution_identity_absent_rows')}"
        )

    for key in (
        "execution_geometry_incomplete_rows",
        "order_identity_missing_rows",
        "source_repair_identity_incomplete_rows",
        "slippage_join_repaired_by_this_emitter_rows",
        "exact_r_repaired_by_this_emitter_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    for row in rows:
        status = row.get("future_slippage_lifecycle_emitter_status")
        row_id = row.get("future_slippage_lifecycle_emitter_event_row_id")
        if row.get("runtime_candidate_use_permitted"):
            issues.append(f"runtime_candidate_use_permitted:{row_id}")
            break
        if row.get("slippage_join_repaired_by_this_emitter"):
            issues.append(f"historical_slippage_repair_claimed:{row_id}")
            break
        if status == "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE":
            entry_payload = row.get("future_entry_slippage_row_payload") or {}
            close_payload = row.get("future_close_slippage_row_payload") or {}
            merged_payload = row.get("future_merged_lifecycle_execution_identity_payload") or {}
            if not entry_payload.get("source_repair_identity_key"):
                issues.append(f"entry_identity_missing:{row_id}")
                break
            if entry_payload.get("source_repair_identity_key") != row.get("source_repair_identity_key"):
                issues.append(f"entry_identity_mismatch:{row_id}")
                break
            if close_payload.get("order_ticket") != entry_payload.get("order_ticket"):
                issues.append(f"entry_close_order_ticket_mismatch:{row_id}")
                break
            if merged_payload.get("executed_exit_price") is None:
                issues.append(f"merged_exit_price_missing:{row_id}")
                break
        elif row.get("future_entry_slippage_row_payload") is not None:
            issues.append(f"non_ready_entry_payload_present:{row_id}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_future_lifecycle_emitter_contract_available") is not True:
        issues.append("default_off_future_lifecycle_emitter_effect_missing")
    if effect.get("future_contract_complete_if_emitted_rows") != EXPECTED_READY_ROWS:
        issues.append(
            "effect_future_contract_complete_if_emitted_rows_unexpected:"
            f"{effect.get('future_contract_complete_if_emitted_rows')}"
        )
    if effect.get("historical_slippage_rows_repaired") != 0:
        issues.append(f"historical_slippage_rows_repaired_nonzero:{effect.get('historical_slippage_rows_repaired')}")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "emitter_rows": len(rows),
        "future_slippage_lifecycle_emitter_status_counts": summary.get(
            "future_slippage_lifecycle_emitter_status_counts"
        ),
        "future_contract_complete_if_emitted_rows": summary.get("future_contract_complete_if_emitted_rows"),
        "source_repair_identity_written_to_future_entry_payload_rows": summary.get(
            "source_repair_identity_written_to_future_entry_payload_rows"
        ),
        "future_close_payload_joinable_by_order_ticket_rows": summary.get(
            "future_close_payload_joinable_by_order_ticket_rows"
        ),
        "slippage_join_repaired_by_this_emitter_rows": summary.get(
            "slippage_join_repaired_by_this_emitter_rows"
        ),
        "exact_r_repaired_by_this_emitter_rows": summary.get("exact_r_repaired_by_this_emitter_rows"),
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
