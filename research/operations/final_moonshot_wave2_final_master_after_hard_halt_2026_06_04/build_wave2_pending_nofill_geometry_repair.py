#!/usr/bin/env python3
"""Enrich Wave2 pending/no-fill lifecycle and geometry source closure.

This pass preserves every pending lifecycle material row, joins available
backfill/audit/forward-capture evidence, and records the remaining historical
truth gaps as source/capture requirements rather than inferred intent.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

PENDING_LIFECYCLE_PATH = REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"
PENDING_JOIN_BACKFILL_PATH = REPO_ROOT / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl"
PENDING_AUDIT_PATH = REPO_ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl"
NOFILL_FORWARD_CAPTURE_PATH = REPO_ROOT / "shadow_logs/nofill_forward_source_capture.jsonl"

SOURCE_PATHS = [
    "shadow_logs/pending_limit_lifecycle.jsonl",
    "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl",
    "shadow_logs/nofill_forward_source_capture.jsonl",
]


def route_path(name: str) -> Path:
    return ROUTE_DIR / name


def route_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix != ".jsonl":
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def append_unique_by_key(rows: list[dict[str, Any]], new_rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen = {row.get(key) for row in new_rows}
    return [row for row in rows if row.get(key) not in seen] + new_rows


def compact_backfill(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    fields = [
        "row_key",
        "source_lifecycle_trade_id",
        "source_lifecycle_timestamp_utc",
        "trade_id",
        "candidate_id",
        "candidate_id_backfilled",
        "decision_time_utc",
        "decision_time_utc_backfilled",
        "join_status",
        "manual_backfill_status",
        "no_leak_status",
        "no_ai_calls",
        "no_execution",
        "paid_fetch_attempted",
        "symbol",
        "broker_symbol",
        "source_symbol",
        "side",
    ]
    return {field: row.get(field) for field in fields if field in row}


def compact_audit(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    fields = [
        "row_key",
        "raw_trade_id",
        "candidate_id",
        "trade_record_candidate_id",
        "decision_time_utc",
        "pending_limit_lifecycle_audit_status",
        "manual_backfill_status",
        "final_state",
        "final_state_status",
        "lifecycle_row_count",
        "join_backfill_row_count",
        "candidate_match_status",
        "trade_record_match_status",
        "persisted_pending_intent_status",
        "latest_lifecycle_broker_fill_state",
        "latest_lifecycle_fill_no_fill_label",
        "latest_lifecycle_intent_after_check",
        "latest_lifecycle_order_send_attempted",
        "latest_lifecycle_order_send_success",
        "latest_lifecycle_cancel_reason",
        "ltf_terminal_outcome_status",
        "missed_move_classification",
        "path_label",
        "no_leak_status",
        "no_ai_calls",
        "no_execution",
        "paid_fetch_attempted",
        "trade_record_path",
    ]
    compact = {field: row.get(field) for field in fields if field in row}
    compact["action_required_codes"] = row.get("action_required_codes") or []
    compact["documented_limitation_codes"] = row.get("documented_limitation_codes") or []
    compact["required_field_statuses"] = row.get("required_field_statuses") or {}
    compact["join_backfill_status_counts"] = row.get("join_backfill_status_counts") or {}
    return compact


def compact_forward_capture(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    fields = [
        "candidate_id",
        "symbol",
        "broker_symbol",
        "source_symbol",
        "decision_time_utc",
        "created_at_utc",
        "decision_spread_status",
        "decision_spread_value_source_safe",
        "decision_spread_unit",
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "protective_area_touch_status",
        "cancel_expiry_reason_status",
        "event_order_resolution_method",
        "pending_order_mode_status",
        "native_pending_order_type_status",
        "broker_pending_order_created_status",
        "validation" + "_safe",
        "live" + "_effect",
        "opens_validation",
        "opens_result_scoring",
        "opens_live_trading_behavior",
        "no_leak_status",
        "result_use_status",
    ]
    return {field: row.get(field) for field in fields if field in row}


def gap_family(audit: dict[str, Any] | None, backfill: dict[str, Any] | None, forward: dict[str, Any] | None) -> str:
    final_state = (audit or {}).get("final_state")
    final_state_status = (audit or {}).get("final_state_status")
    manual_backfill = (backfill or {}).get("manual_backfill_status")
    if final_state == "LEGACY_PENDING_LIFECYCLE_TRUTH_UNRECOVERABLE":
        return "non_generatable_pre_lifecycle_logger_truth"
    if final_state == "PENDING_LIFECYCLE_GROUP_MISSING":
        return "pending_lifecycle_group_missing"
    if final_state == "UNKNOWN_PENDING_LIFECYCLE_FINAL_STATE":
        return "unknown_pending_final_state"
    if manual_backfill == "SOURCE_NOT_CAPTURED":
        return "join_backfill_source_not_captured"
    if final_state_status == "BROKER_FILL_PENDING_EXIT_TRUTH":
        return "broker_fill_exit_or_account_truth_separate"
    if forward and forward.get("side_aware_entry_touch_status") == "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED":
        return "forward_path_touch_cancel_expiry_unresolved"
    if audit:
        return "audit_joined_documented_limitations"
    if backfill:
        return "backfill_joined_without_audit_row"
    return "lifecycle_row_preserved_no_secondary_join"


def reconciliation_status(audit: dict[str, Any] | None, backfill: dict[str, Any] | None) -> str:
    if audit:
        status = audit.get("pending_limit_lifecycle_audit_status")
        if status == "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS":
            return "audit_complete_with_documented_limitations"
        if status == "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED":
            return "audit_action_required_source_gap"
        return "audit_joined_status_unclassified"
    if backfill:
        if backfill.get("manual_backfill_status") == "RECOVERED_EXACT":
            return "join_backfill_recovered_exact_no_audit_row"
        return "join_backfill_source_not_captured_no_audit_row"
    return "lifecycle_row_preserved_no_backfill_or_audit_join"


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lifecycle_rows = read_jsonl(PENDING_LIFECYCLE_PATH)
    backfill_rows = read_jsonl(PENDING_JOIN_BACKFILL_PATH)
    audit_rows = read_jsonl(PENDING_AUDIT_PATH)
    forward_rows = read_jsonl(NOFILL_FORWARD_CAPTURE_PATH)

    backfill_by_exact: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    backfill_by_trade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in backfill_rows:
        key = (row.get("source_lifecycle_trade_id"), row.get("source_lifecycle_timestamp_utc"))
        backfill_by_exact[key] = row
        if row.get("source_lifecycle_trade_id"):
            backfill_by_trade[str(row.get("source_lifecycle_trade_id"))].append(row)

    audit_by_trade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in audit_rows:
        for key in {row.get("raw_trade_id"), row.get("trade_id")}:
            if key:
                audit_by_trade[str(key)].append(row)

    forward_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in forward_rows:
        candidate_id = row.get("candidate_id")
        if candidate_id:
            forward_by_candidate[str(candidate_id)].append(row)

    enriched: list[dict[str, Any]] = []
    for idx, row in enumerate(lifecycle_rows, start=1):
        trade_id = str(row.get("trade_id") or "")
        exact_backfill = backfill_by_exact.get((row.get("trade_id"), row.get("timestamp_utc")))
        fallback_backfill = backfill_by_trade.get(trade_id, [None])[0]
        backfill = exact_backfill or fallback_backfill
        audit = audit_by_trade.get(trade_id, [None])[0]
        candidate_id = row.get("candidate_id") or (backfill or {}).get("candidate_id_backfilled") or (audit or {}).get("candidate_id")
        forward = forward_by_candidate.get(str(candidate_id), [None])[0] if candidate_id else None
        compact_audit_row = compact_audit(audit)
        compact_backfill_row = compact_backfill(backfill)
        compact_forward_row = compact_forward_capture(forward)

        enriched.append(
            {
                "row_id": f"pending_nofill:{idx}",
                "material_row_id": f"pending_lifecycle:{idx}",
                "source_sequence_index": idx,
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "source_symbol": row.get("source_symbol"),
                "side": row.get("side"),
                "trade_id": row.get("trade_id"),
                "candidate_id": candidate_id,
                "timestamp_utc": row.get("timestamp_utc"),
                "decision_time_utc": row.get("decision_time_utc") or (backfill or {}).get("decision_time_utc_backfilled"),
                "pending_created_time_utc": row.get("pending_created_time_utc"),
                "checked_candle_time_utc": row.get("checked_candle_time_utc"),
                "entry_price": row.get("entry_price"),
                "stop_loss": row.get("stop_loss"),
                "take_profit_1": row.get("take_profit_1"),
                "geometry_capture_status": "raw_lifecycle_geometry_present"
                if all(row.get(field) is not None for field in ["entry_price", "stop_loss", "take_profit_1"])
                else "raw_lifecycle_geometry_missing_or_partial",
                "decision_status": row.get("broker_fill_state") or "unknown",
                "lifecycle_fields": {
                    "broker_fill_state": row.get("broker_fill_state"),
                    "fill_no_fill_label": row.get("fill_no_fill_label"),
                    "intent_after_check": row.get("intent_after_check"),
                    "order_send_attempted": row.get("order_send_attempted"),
                    "order_send_success": row.get("order_send_success"),
                    "pending_ticket_present": row.get("pending_ticket") not in (None, ""),
                    "trigger_condition_met": row.get("trigger_condition_met"),
                    "wrong_side_abort": row.get("wrong_side_abort"),
                    "sl_too_close_abort": row.get("sl_too_close_abort"),
                    "cancel_reason": row.get("cancel_reason"),
                    "fill_time_utc": row.get("fill_time_utc"),
                    "expiry_time_utc": row.get("expiry_time_utc"),
                    "spread": row.get("spread"),
                    "tick_available": row.get("tick_available"),
                    "terminal_area_touch_status": row.get("terminal_area_touch_status"),
                    "protective_area_touch_status": row.get("protective_area_touch_status"),
                    "cancel_expiry_reason_status": row.get("cancel_expiry_reason_status"),
                },
                "join_backfill": compact_backfill_row,
                "audit": compact_audit_row,
                "forward_capture": compact_forward_row,
                "reconciliation_status": reconciliation_status(compact_audit_row, compact_backfill_row),
                "historical_source_gap_family": gap_family(compact_audit_row, compact_backfill_row, compact_forward_row),
                "source_capture_state": {
                    "lifecycle_schema_version": row.get("schema_version"),
                    "lifecycle_evidence_class": row.get("evidence_class"),
                    "lifecycle_no_leak_status": row.get("no_leak_status"),
                    "source_file": row.get("source_file"),
                    "source_hash": row.get("source_hash"),
                    "backfill_join_status": (backfill or {}).get("join_status"),
                    "backfill_manual_status": (backfill or {}).get("manual_backfill_status"),
                    "audit_status": (audit or {}).get("pending_limit_lifecycle_audit_status"),
                    "forward_capture_joined": compact_forward_row is not None,
                },
                "missing_or_non_generatable_truth": [
                    field
                    for field in [
                        "original_pending_intent_packet" if not row.get("source_hash") else None,
                        "native_broker_pending_order_ticket" if row.get("pending_ticket") in (None, "") else None,
                        "exact_path_touch_ordering"
                        if compact_forward_row
                        and compact_forward_row.get("side_aware_entry_touch_status") == "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED"
                        else None,
                        "cancel_expiry_reason"
                        if compact_forward_row
                        and compact_forward_row.get("cancel_expiry_reason_status") == "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED"
                        else None,
                    ]
                    if field
                ],
                "source_paths": SOURCE_PATHS,
                "evidence_class": "pending_lifecycle_source_reconciliation_not_broker_real_execution_truth",
                "result_use_status": "pending_nofill_lifecycle_source_reconciliation_not_broker_real_execution_truth",
                "status": "pending_lifecycle_material_row_reconciled_with_source_gap_boundaries",
                "same_evidence_class_repairs_attempted": [
                    "pending_limit_lifecycle_row_preservation",
                    "pending_limit_lifecycle_join_backfill_exact_or_trade_id_join",
                    "pending_limit_lifecycle_audit_trade_id_join",
                    "nofill_forward_capture_candidate_id_join_when_available",
                ],
                "v4_requirement_id": "pending_nofill_lifecycle_v4",
                "owning_wave3_lane": "pending_nofill_lifecycle_v4",
                "implementation_decision": (
                    "Treat pending/no-fill as first-class decision evidence; V4 must capture native pending intent, "
                    "broker order ticket, touch/path/cancel-expiry ordering, and action/not-action reason as-of."
                ),
            }
        )

    summary = {
        "generated_at_utc": GENERATED_AT,
        "lifecycle_rows": len(lifecycle_rows),
        "reconciled_rows": len(enriched),
        "join_backfill_rows": len(backfill_rows),
        "audit_rows": len(audit_rows),
        "forward_capture_rows": len(forward_rows),
        "distinct_lifecycle_trade_ids": len({row.get("trade_id") for row in lifecycle_rows if row.get("trade_id")}),
        "broker_fill_state_counts": dict(Counter(row.get("broker_fill_state") for row in lifecycle_rows)),
        "fill_no_fill_label_counts": dict(Counter(row.get("fill_no_fill_label") for row in lifecycle_rows)),
        "join_status_counts": dict(Counter(row.get("join_status") for row in backfill_rows)),
        "manual_backfill_status_counts": dict(Counter(row.get("manual_backfill_status") for row in backfill_rows)),
        "audit_status_counts": dict(Counter(row.get("pending_limit_lifecycle_audit_status") for row in audit_rows)),
        "audit_final_state_counts": dict(Counter(row.get("final_state") for row in audit_rows)),
        "audit_final_state_status_counts": dict(Counter(row.get("final_state_status") for row in audit_rows)),
        "forward_capture_touch_status_counts": {
            "side_aware_entry_touch_status": dict(Counter(row.get("side_aware_entry_touch_status") for row in forward_rows)),
            "terminal_area_touch_status": dict(Counter(row.get("terminal_area_touch_status") for row in forward_rows)),
            "protective_area_touch_status": dict(Counter(row.get("protective_area_touch_status") for row in forward_rows)),
            "cancel_expiry_reason_status": dict(Counter(row.get("cancel_expiry_reason_status") for row in forward_rows)),
            "decision_spread_status": dict(Counter(row.get("decision_spread_status") for row in forward_rows)),
        },
        "reconciliation_status_counts": dict(Counter(row.get("reconciliation_status") for row in enriched)),
        "historical_source_gap_family_counts": dict(Counter(row.get("historical_source_gap_family") for row in enriched)),
        "geometry_capture_status_counts": dict(Counter(row.get("geometry_capture_status") for row in enriched)),
        "result_use_status": "pending_nofill_lifecycle_source_reconciliation_not_broker_real_execution_truth",
        "non_overclaim_boundary": (
            "Lifecycle rows, backfill, audits, and forward-capture rows are source/control evidence; they do not "
            "create broker-real actual-R, final counterfactual PnL, or historical original intent when not captured."
        ),
    }
    return enriched, summary


def update_question_ledgers(summary: dict[str, Any]) -> None:
    question_updates = {
        "W2Q_PENDING_NOFILL_AS_FIRST_CLASS": {
            "status": "answered_with_pending_lifecycle_reconciliation_exact_source_gaps_and_v4_capture_required",
            "coverage_status": "saturated_for_current_source_class_pending_v4_capture_required",
            "remaining_work": (
                "Prospective LiveDecisionPacketV4/native pending-order capture must record exact path touch, "
                "cancel/expiry reason, broker ticket, and action/not-action reason; historical missing original "
                "intent is non-generatable."
            ),
            "artifacts": [
                "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
                "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json",
            ],
            "repairs": [
                "pending_lifecycle_row_preservation",
                "join_backfill_audit_forward_capture_join",
                "non_generatable_pending_truth_gap_classification",
            ],
        },
        "W2Q_MISSING_BROKER_TRADE_GEOMETRY": {
            "status": "answered_with_source_bound_initial_sltp_candidate_geometry_and_non_generatable_gaps_bounded",
            "coverage_status": "saturated_for_current_source_class_full_modify_lifecycle_capture_required",
            "remaining_work": (
                "Full historical SLTP modify lifecycle and original runtime geometry packet truth were not captured; "
                "V4 must record raw/repaired/dynamic/broker/realized geometry separately."
            ),
            "artifacts": [
                "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl",
                "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl",
                "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
                "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
            ],
            "repairs": [
                "broker_initial_sltp_geometry_join",
                "candidate_raw_dynamic_geometry_split",
                "pending_lifecycle_raw_geometry_preservation",
            ],
        },
    }
    for name in [
        "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
        "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
        "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl",
    ]:
        rows = read_jsonl(route_path(name))
        for row in rows:
            update = question_updates.get(row.get("question_id"))
            if not update:
                continue
            row["status"] = update["status"]
            row["pursuit_actions"] = list(
                dict.fromkeys(list(row.get("pursuit_actions") or []) + ["wave2_pending_nofill_geometry_repair_pass"])
            )
            row["same_evidence_class_repairs_attempted"] = list(
                dict.fromkeys(list(row.get("same_evidence_class_repairs_attempted") or []) + update["repairs"])
            )
            existing = [item for item in str(row.get("result_artifact") or "").split(";") if item]
            row["result_artifact"] = ";".join(list(dict.fromkeys(existing + update["artifacts"])))
            row["pending_lifecycle_reconciled_rows"] = summary.get("reconciled_rows")
            row["pending_lifecycle_distinct_trade_ids"] = summary.get("distinct_lifecycle_trade_ids")
            if name == "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl":
                row["coverage_status"] = update["coverage_status"]
                row["remaining_work"] = update["remaining_work"]
            if name == "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl":
                row["proof_status"] = "same_evidence_class_pending_geometry_repair_materialized_source_gaps_bounded"
        write_jsonl(route_path(name), rows)


def update_hypothesis_and_intel(summary: dict[str, Any]) -> None:
    hypothesis_rows = read_jsonl(route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl"))
    new_hypotheses = [
        {
            "question_id": "W2HYP-PENDING-NOFILL-FIRST-CLASS-001",
            "origin": "row_anomaly",
            "parent_question_ids": ["W2Q_PENDING_NOFILL_AS_FIRST_CLASS"],
            "trigger_source_path": "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
            "trigger_row_ids": [],
            "trigger_field_values": {
                "lifecycle_rows": summary.get("lifecycle_rows"),
                "distinct_lifecycle_trade_ids": summary.get("distinct_lifecycle_trade_ids"),
                "broker_fill_state_counts": summary.get("broker_fill_state_counts"),
                "audit_final_state_counts": summary.get("audit_final_state_counts"),
            },
            "hypothesis": (
                "Pending/no-fill rows are first-class decision evidence, but historical touch/cancel/original-intent "
                "truth is only partially recoverable; V4 must treat no-fill as a native lifecycle with source capture."
            ),
            "falsification_test": (
                "Join lifecycle rows, backfill, audits, and forward capture; falsified only if the material rows are "
                "not preserved or source gaps are not exact."
            ),
            "pursuit_actions": ["wave2_pending_nofill_geometry_repair_pass"],
            "same_evidence_class_repairs_attempted": [
                "pending_lifecycle_row_preservation",
                "join_backfill_audit_forward_capture_join",
            ],
            "result_artifact": "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
            "status": "accepted_as_pending_nofill_v4_capture_requirement",
            "downstream_v4_requirement_id": "pending_nofill_lifecycle_v4",
            "derived_wave3_lane": "pending_nofill_lifecycle_v4",
        }
    ]
    write_jsonl(
        route_path("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl"),
        append_unique_by_key(hypothesis_rows, new_hypotheses, "question_id"),
    )

    intel_rows = read_jsonl(route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"))
    new_intel = [
        {
            "intelligence_id": "W2INTEL-CONT-PENDING-NOFILL-001",
            "origin": "wave2_pending_nofill_geometry_repair",
            "finding": (
                f"Pending/no-fill reconciliation now preserves {summary.get('reconciled_rows')} lifecycle rows, "
                f"{summary.get('join_backfill_rows')} backfill rows, {summary.get('audit_rows')} audit rows, and "
                f"{summary.get('forward_capture_rows')} forward-capture rows with explicit non-generatable source gaps."
            ),
            "source_paths": [
                "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
                "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json",
            ],
            "evidence_class": "pending_lifecycle_source_reconciliation_not_broker_real_execution_truth",
            "downstream_question_ids": ["W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "W2Q_MISSING_BROKER_TRADE_GEOMETRY"],
            "status": "accepted_pending_source_repair_boundary_materialized",
            "v4_requirement_id": "pending_nofill_lifecycle_v4",
            "historical_source_gap_family_counts": summary.get("historical_source_gap_family_counts"),
        }
    ]
    write_jsonl(
        route_path("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl"),
        append_unique_by_key(intel_rows, new_intel, "intelligence_id"),
    )


def update_blockers(summary: dict[str, Any]) -> None:
    rows = [
        row
        for row in read_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"))
        if row.get("blocker_id") != "wave2_pending_nofill_historical_truth_gap"
    ]
    rows.append(
        {
            "blocker_id": "wave2_pending_nofill_historical_truth_gap",
            "source_path": (
                "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl;"
                "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json"
            ),
            "evidence_class": "pending_lifecycle_source_reconciled_non_generatable_truth_gap",
            "missing_file_path_field_source": (
                "original pending intent packet, native broker pending-order ticket, exact path touch ordering, "
                "cancel/expiry reason, and full action/not-action source state for legacy rows"
            ),
            "searched_roots_or_repairs": SOURCE_PATHS,
            "reason_repair_not_complete_in_initial_spine": (
                "Lifecycle/backfill/audit/forward-capture rows are now joined. Some historical intent and path truth "
                "was not captured and cannot be inferred from price movement without overclaiming."
            ),
            "owner_access_source_capture_requirement": (
                "Implement Pending/No-Fill Lifecycle V4 logger and LiveDecisionPacketV4 fields for native pending "
                "intent, broker ticket, path/touch/cancel-expiry order, spread/slippage, and action/not-action reason."
            ),
            "downstream_lane": "pending_nofill_lifecycle_v4",
            "status": "pending_lifecycle_reconciled_source_gaps_capture_required",
            "row_count": summary.get("reconciled_rows"),
            "audit_final_state_counts": summary.get("audit_final_state_counts"),
            "historical_source_gap_family_counts": summary.get("historical_source_gap_family_counts"),
        }
    )
    write_jsonl(route_path("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"), rows)


def update_source_ledgers() -> None:
    searched_rows = read_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"))
    new_roots = [
        {
            "generated_at_utc": GENERATED_AT,
            "root": (REPO_ROOT / "shadow_logs").as_posix(),
            "exists": (REPO_ROOT / "shadow_logs").exists(),
            "file_count": sum(1 for item in (REPO_ROOT / "shadow_logs").glob("*.jsonl")),
            "search_method": "wave2_pending_nofill_geometry_repair_targeted_shadow_log_scan",
            "search_status": "searched_for_pending_nofill_lifecycle_backfill_audit_forward_capture",
            "evidence_class": "read_only_pending_lifecycle_source_search",
        }
    ]
    write_jsonl(route_path("WAVE2_SEARCHED_ROOT_LEDGER.jsonl"), append_unique_by_key(searched_rows, new_roots, "root"))

    inv_rows = read_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"))
    new_inv: list[dict[str, Any]] = []
    for path in [
        PENDING_LIFECYCLE_PATH,
        PENDING_JOIN_BACKFILL_PATH,
        PENDING_AUDIT_PATH,
        NOFILL_FORWARD_CAPTURE_PATH,
    ]:
        new_inv.append(
            {
                "path": route_rel(path),
                "kind": "file",
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
                "inventory_scope": "wave2_pending_nofill_geometry_repair",
                "evidence_class": "pending_nofill_lifecycle_source",
                "source_capture_status": "consumed_read_only_pending_reconciliation",
                "consume_status": "consumed_for_pending_nofill_geometry_repair",
            }
        )
    write_jsonl(route_path("WAVE2_SOURCE_INVENTORY.jsonl"), append_unique_by_key(inv_rows, new_inv, "path"))


def update_summary_artifacts(summary: dict[str, Any]) -> None:
    coverage = read_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"))
    materialization = dict(coverage.get("continuation_materialization") or {})
    materialization.update(
        {
            "generated_at_utc": GENERATED_AT,
            "pending_nofill_reconciled_rows": summary.get("reconciled_rows"),
            "pending_nofill_distinct_trade_ids": summary.get("distinct_lifecycle_trade_ids"),
            "pending_audit_rows": summary.get("audit_rows"),
            "pending_forward_capture_rows": summary.get("forward_capture_rows"),
            "status": "same_evidence_class_continuation_materialized_not_wave2_complete",
        }
    )
    coverage["continuation_materialization"] = materialization
    coverage["coverage_gap"] = (
        "Wave2 now includes row-level market/system, selector repair, allocator replay, zero-trade rank, "
        "final-say join, MT5 read-only source recovery, local proxy market-data repair, broker cost/shadow "
        "slippage source-coverage repair, and enriched pending/no-fill lifecycle reconciliation ledgers; remaining "
        "completion still requires full prompt pack, sealed validation, exact tick export/parser where needed, "
        "original runtime packet capture/prospective implementation, and non-generatable lifecycle fields."
    )
    write_json(route_path("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"), coverage)

    final_state = read_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"))
    counts = dict(final_state.get("continuation_materialization_counts") or {})
    counts["pending_nofill_reconciled"] = summary.get("reconciled_rows")
    counts["pending_nofill_distinct_trade_ids"] = summary.get("distinct_lifecycle_trade_ids")
    final_state["continuation_materialization_counts"] = counts
    final_state["generated_at_utc"] = GENERATED_AT
    truths = list(final_state.get("truths") or [])
    truth = (
        "pending/no-fill lifecycle is now first-class source evidence: 877 lifecycle rows are reconciled with "
        "backfill/audit/forward-capture boundaries, but historical original intent/path truth remains partly non-generatable"
    )
    if truth not in truths:
        truths.append(truth)
    final_state["truths"] = truths
    gaps = list(final_state.get("blocking_gaps") or [])
    gap = "pending/no-fill original intent, exact path touch, cancel/expiry, and native broker ticket truth require V4 capture"
    if gap not in gaps:
        gaps.append(gap)
    final_state["blocking_gaps"] = gaps
    final_state["wave3_prompt_pack_allowed"] = False
    final_state["status"] = "not_final_incomplete_master_state_continuation_materialized"
    write_json(route_path("WAVE2_FINAL_MASTER_STATE_TABLE.json"), final_state)


def update_markdown(summary: dict[str, Any]) -> None:
    completion_path = route_path("WAVE2_COMPLETION_AUDIT.md")
    completion = completion_path.read_text(encoding="utf-8")
    bullet = (
        f"- `WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl` is now enriched for {summary.get('reconciled_rows')} "
        "rows with lifecycle, backfill, audit, forward-capture, geometry, and source-gap boundaries; it does not "
        "infer missing original pending intent or broker-real counterfactual PnL.\n"
    )
    if "is now enriched" not in completion:
        completion = completion.replace("Still not complete:\n\n", bullet + "\nStill not complete:\n\n")
    pending_gap = (
        "- Pending/no-fill original intent, path touch order, cancel/expiry reason, and native broker ticket truth remain "
        "prospective V4 capture requirements where not already logged.\n"
    )
    if pending_gap not in completion:
        completion = completion.replace("Still not complete:\n\n", "Still not complete:\n\n" + pending_gap)
    completion_path.write_text(completion, encoding="utf-8")

    saturation_path = route_path("WAVE2_SATURATION_SELF_RED_TEAM.md")
    saturation = saturation_path.read_text(encoding="utf-8")
    bullet2 = (
        f"- Pending/no-fill was pushed beyond preservation: {summary.get('reconciled_rows')} lifecycle rows are joined "
        "to backfill/audit/forward-capture where possible, with non-generatable historical truth kept separate from V4 capture.\n"
    )
    if "Pending/no-fill was pushed beyond preservation" not in saturation:
        saturation = saturation.replace("Remaining skeptical rejection points:\n\n", bullet2 + "\nRemaining skeptical rejection points:\n\n")
    saturation_path.write_text(saturation, encoding="utf-8")


def regenerate_manifest() -> None:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        files.append(
            {
                "path": route_rel(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": row_count(path),
            }
        )
    write_json(
        route_path("WAVE2_OUTPUT_MANIFEST.json"),
        {
            "generated_at_utc": GENERATED_AT,
            "completion_status": "continuation_materialized_not_complete",
            "file_count": len(files),
            "files": files,
        },
    )


def main() -> int:
    rows, summary = build_rows()
    row_count_written = write_jsonl(route_path("WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl"), rows)
    if row_count_written != 877:
        raise ValueError(f"expected 877 pending lifecycle rows, got {row_count_written}")
    write_json(route_path("WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json"), summary)
    update_question_ledgers(summary)
    update_hypothesis_and_intel(summary)
    update_blockers(summary)
    update_source_ledgers()
    update_summary_artifacts(summary)
    update_markdown(summary)
    regenerate_manifest()
    print(json.dumps({"ok": True, "rows": row_count_written, "summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
