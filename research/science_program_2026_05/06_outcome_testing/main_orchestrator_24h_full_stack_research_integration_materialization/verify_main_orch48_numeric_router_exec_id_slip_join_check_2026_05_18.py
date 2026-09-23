from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_VERIFY_RESULT_{DATE}.json"

EXPECTED_CONTRACT_ROWS = 1119
EXPECTED_SLIPPAGE_ROWS = 7
EXPECTED_EVENT_ROWS = EXPECTED_CONTRACT_ROWS * EXPECTED_SLIPPAGE_ROWS
EXPECTED_EVENT_STATUS_COUNTS = {
    "EXECUTION_IDENTITY_CAPTURE_EVENT_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT": 77,
    "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISSING": 7756,
}
EXPECTED_EVENT_STATUS_UNIQUE_CONTRACT_COUNTS = {
    "EXECUTION_IDENTITY_CAPTURE_EVENT_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT": 11,
    "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISSING": 1108,
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

    if len(rows) != EXPECTED_EVENT_ROWS:
        issues.append(f"event_row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if summary.get("unique_contract_rows_checked") != EXPECTED_CONTRACT_ROWS:
        issues.append(f"unique_contract_rows_checked_unexpected:{summary.get('unique_contract_rows_checked')}")
    if summary.get("unique_slippage_rows_checked") != EXPECTED_SLIPPAGE_ROWS:
        issues.append(f"unique_slippage_rows_checked_unexpected:{summary.get('unique_slippage_rows_checked')}")
    if summary.get("execution_identity_capture_event_status_counts") != EXPECTED_EVENT_STATUS_COUNTS:
        issues.append(
            "event_status_counts_unexpected:"
            f"{summary.get('execution_identity_capture_event_status_counts')}"
        )
    if (
        summary.get("execution_identity_capture_event_status_unique_contract_counts")
        != EXPECTED_EVENT_STATUS_UNIQUE_CONTRACT_COUNTS
    ):
        issues.append(
            "event_status_unique_contract_counts_unexpected:"
            f"{summary.get('execution_identity_capture_event_status_unique_contract_counts')}"
        )
    if summary.get("missing_source_repair_identity_event_rows") != 7756:
        issues.append(
            "missing_source_repair_identity_event_rows_unexpected:"
            f"{summary.get('missing_source_repair_identity_event_rows')}"
        )
    if summary.get("packet_context_execution_identity_absent_event_rows") != 77:
        issues.append(
            "packet_context_execution_identity_absent_event_rows_unexpected:"
            f"{summary.get('packet_context_execution_identity_absent_event_rows')}"
        )

    for key in (
        "slippage_row_bound_to_contract_rows",
        "slippage_join_repaired_by_this_event_rows",
        "exact_r_repaired_by_this_event_rows",
        "order_identity_missing_event_rows",
        "geometry_incomplete_event_rows",
        "contract_complete_event_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    for row in rows[:50]:
        if row.get("slippage_row_bound_to_contract"):
            issues.append(f"unexpected_bound_row:{row.get('execution_identity_capture_event_row_id')}")
            break
        if row.get("runtime_candidate_use_permitted"):
            issues.append(f"runtime_candidate_use_permitted:{row.get('execution_identity_capture_event_row_id')}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_current_slippage_join_check_available") is not True:
        issues.append("default_off_current_slippage_join_check_effect_missing")
    if effect.get("existing_slippage_rows_bound_to_contract") != 0:
        issues.append(f"existing_slippage_rows_bound_to_contract_nonzero:{effect.get('existing_slippage_rows_bound_to_contract')}")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_IDENTITY_CURRENT_SLIPPAGE_JOIN_CHECK",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "event_rows": len(rows),
        "unique_contract_rows_checked": summary.get("unique_contract_rows_checked"),
        "unique_slippage_rows_checked": summary.get("unique_slippage_rows_checked"),
        "execution_identity_capture_event_status_counts": summary.get(
            "execution_identity_capture_event_status_counts"
        ),
        "slippage_row_bound_to_contract_rows": summary.get("slippage_row_bound_to_contract_rows"),
        "exact_r_repaired_by_this_event_rows": summary.get("exact_r_repaired_by_this_event_rows"),
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
