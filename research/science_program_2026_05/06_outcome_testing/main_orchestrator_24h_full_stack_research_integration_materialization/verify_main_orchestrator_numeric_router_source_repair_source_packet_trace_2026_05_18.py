from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_LEDGER_{DATE}.jsonl"
PLAN_SUMMARY_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_PLAN_SUMMARY_LEDGER_{DATE}.jsonl"
)
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE_VERIFY_RESULT_{DATE}.json"

EXPECTED_TRACE_ROWS = 7045
EXPECTED_PLAN_ROWS = 11
EXPECTED_TRACE_STATUS_COUNTS = {
    "SOURCE_PACKET_TRACE_COMPLETE_PACKET_FOUND_EXECUTION_IDENTITY_ABSENT": 7045,
}
EXPECTED_SOURCE_COMPONENT_COUNTS = {
    "nofill_far_miss_avoid": 875,
    "nofill_far_miss_retest": 2555,
    "nofill_far_miss_source_confidence": 2555,
    "nofill_near_miss_market_entry": 848,
    "nofill_near_miss_offset": 212,
}
EXPECTED_SYMBOL_COUNTS = {"GBPJPY": 6868, "XAUUSD": 177}


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
    for path in (LEDGER, PLAN_SUMMARY_LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    plan_rows = read_jsonl(PLAN_SUMMARY_LEDGER) if PLAN_SUMMARY_LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_TRACE_ROWS:
        issues.append(f"trace_row_count_unexpected:{len(rows)}")
    if len(plan_rows) != EXPECTED_PLAN_ROWS:
        issues.append(f"plan_row_count_unexpected:{len(plan_rows)}")
    if summary.get("trace_rows") != len(rows):
        issues.append("summary_trace_rows_mismatch")
    if summary.get("plan_summary_rows") != len(plan_rows):
        issues.append("summary_plan_rows_mismatch")
    if summary.get("input_action_rows") != EXPECTED_TRACE_ROWS:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")
    if summary.get("source_packet_trace_status_counts") != EXPECTED_TRACE_STATUS_COUNTS:
        issues.append(f"trace_status_counts_unexpected:{summary.get('source_packet_trace_status_counts')}")
    if summary.get("source_component_counts") != EXPECTED_SOURCE_COMPONENT_COUNTS:
        issues.append(f"source_component_counts_unexpected:{summary.get('source_component_counts')}")
    if summary.get("symbol_counts") != EXPECTED_SYMBOL_COUNTS:
        issues.append(f"symbol_counts_unexpected:{summary.get('symbol_counts')}")

    for key in (
        "original_source_packet_found_rows",
        "source_join_packet_found_rows",
        "source_absence_proof_repaired_rows",
        "requires_prospective_execution_identity_capture_rows",
    ):
        if summary.get(key) != EXPECTED_TRACE_ROWS:
            issues.append(f"{key}_unexpected:{summary.get(key)}")
            break

    for key in (
        "direct_execution_identity_found_rows",
        "exact_r_repaired_by_this_trace_rows",
        "slippage_join_repaired_by_this_trace_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("source_packet_absence_proof_repaired_from_original_packets") is not True:
        issues.append("source_packet_absence_repair_effect_missing")
    if effect.get("exact_r_or_slippage_join_repaired") is not False:
        issues.append("exact_or_slippage_repair_claimed")
    if effect.get("runtime_trading_or_live_broker_effect") is not False:
        issues.append("runtime_trading_or_live_broker_effect_claimed")

    for row in plan_rows:
        row_id = row.get("source_packet_trace_plan_summary_row_id")
        if row.get("trace_rows") != row.get("input_action_rows"):
            issues.append(f"plan_trace_rows_mismatch:{row_id}")
            break
        if row.get("source_packet_trace_plan_status") != "SOURCE_PACKET_TRACE_PLAN_COMPLETE_EXECUTION_IDENTITY_ABSENT":
            issues.append(f"plan_status_unexpected:{row_id}:{row.get('source_packet_trace_plan_status')}")
            break
        if row.get("original_source_packet_found_rows") != row.get("input_action_rows"):
            issues.append(f"plan_original_packet_count_mismatch:{row_id}")
            break
        if row.get("source_join_packet_found_rows") != row.get("input_action_rows"):
            issues.append(f"plan_source_join_count_mismatch:{row_id}")
            break
        if row.get("direct_execution_identity_found_rows") != 0:
            issues.append(f"plan_direct_identity_nonzero:{row_id}")
            break

    for row in rows[:50] + rows[-50:]:
        row_id = row.get("source_packet_trace_row_id")
        if row.get("source_row_id") != row.get("original_source_packet_row_id"):
            issues.append(f"original_row_id_mismatch:{row_id}")
            break
        if row.get("source_row_id") != row.get("source_join_packet_row_id"):
            issues.append(f"source_join_row_id_mismatch:{row_id}")
            break
        if row.get("direct_execution_identity_fields_present"):
            issues.append(f"direct_execution_identity_present:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"runtime_candidate_enabled:{row_id}")
            break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, PLAN_SUMMARY_LEDGER, SUMMARY):
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

    for source in summary.get("source_packet_inputs") or []:
        for key, sha_key in (
            ("original_source_packet_artifact", "original_source_packet_sha256"),
            ("source_join_packet_artifact", "source_join_packet_sha256"),
        ):
            path = resolve_display_path(source.get(key, ""))
            if not path.exists():
                issues.append(f"source_packet_input_missing:{source.get(key)}")
                continue
            if source.get(sha_key) != sha256_path(path):
                issues.append(f"source_packet_input_hash_mismatch:{source.get(key)}")
                break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_TRACE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "trace_rows": len(rows),
        "plan_summary_rows": len(plan_rows),
        "source_packet_trace_status_counts": summary.get("source_packet_trace_status_counts"),
        "source_component_counts": summary.get("source_component_counts"),
        "direct_execution_identity_found_rows": summary.get("direct_execution_identity_found_rows"),
        "exact_r_repaired_by_this_trace_rows": summary.get("exact_r_repaired_by_this_trace_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
