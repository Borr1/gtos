"""Opportunity lifecycle contract audit helpers.

This module recomputes live candidate opportunity assignments from the
append-only candidate/path/LTF evidence, then compares the result with the
documented cluster rows. It is research/tooling only: no AI, canary, broker,
order, MT5, or paid-data calls.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate
from src.research_infra.live_opportunity_dedupe import (
    FORMAL_LIFECYCLE_STATES,
    OPPORTUNITY_ALGORITHM_VERSION,
    build_opportunity_index,
    candidate_lifecycle_signature,
    same_level_tolerance_band,
    terminal_event_summary,
)


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "opportunity_lifecycle_audit_v1"
COMPLETE = "OPPORTUNITY_LIFECYCLE_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "OPPORTUNITY_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "OPPORTUNITY_LIFECYCLE_ACTION_REQUIRED"

COMPARISON_FIELDS = (
    "opportunity_id",
    "opportunity_first_candidate_id",
    "opportunity_sequence_index",
    "opportunity_candidate_count",
    "opportunity_duplicate_status",
    "opportunity_reset_reason",
    "opportunity_counting_status",
    "same_symbol_overlap_status",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(_canonical_json(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def _reset_policy_status(terminal: dict[str, Any]) -> str:
    status = str(terminal.get("terminal_event_status") or "")
    if terminal.get("reset_eligible") is True:
        return "RESET_ALLOWED_ENTRY_THEN_TERMINAL_TP_OR_SL"
    if status in {
        "ENTRY_TP1_SL_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
    }:
        return "NO_RESET_TERMINAL_ORDER_AMBIGUOUS"
    if status in {
        "NO_ENTRY_TP_AREA_REACHED_NO_TRADE_NO_RESET",
        "NO_ENTRY_SL_AREA_REACHED_NO_TRADE_NO_RESET",
    }:
        return "NO_RESET_NO_ENTRY_TOUCH"
    if status == "ENTRY_TOUCHED_NOT_TERMINAL":
        return "NO_RESET_ENTRY_TOUCHED_NOT_TERMINAL"
    return "NO_RESET_NO_ELIGIBLE_TERMINAL_EVENT"


def _comparison_mismatches(
    computed: dict[str, Any] | None,
    documented: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if not computed or not documented:
        return {}
    mismatches: dict[str, dict[str, Any]] = {}
    for field in COMPARISON_FIELDS:
        if computed.get(field) != documented.get(field):
            mismatches[field] = {
                "computed": computed.get(field),
                "documented": documented.get(field),
            }
    return mismatches


def _comparison_projection(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    projected = {field: row.get(field) for field in COMPARISON_FIELDS}
    projected["opportunity_lifecycle_state"] = row.get("opportunity_lifecycle_state")
    projected["opportunity_lifecycle_signature"] = row.get("opportunity_lifecycle_signature")
    projected["same_level_tolerance_band"] = row.get("same_level_tolerance_band")
    return projected


def _count_mismatch_is_point_in_time_stale(mismatches: dict[str, dict[str, Any]]) -> bool:
    if set(mismatches) != {"opportunity_candidate_count"}:
        return False
    values = mismatches["opportunity_candidate_count"]
    try:
        computed = int(values.get("computed"))
        documented = int(values.get("documented"))
    except (TypeError, ValueError):
        return False
    return documented <= computed


def build_opportunity_lifecycle_audit_row(
    line_no: int,
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    computed_opportunity: dict[str, Any] | None,
    documented_cluster: dict[str, Any] | None,
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None,
) -> dict[str, Any]:
    actions: list[str] = []
    limitations: list[str] = []
    candidate_id = str(candidate.get("candidate_id") or "")
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    terminal = terminal_event_summary(path_row, ltf_row)
    lifecycle_state = str((computed_opportunity or {}).get("opportunity_lifecycle_state") or "UNKNOWN_LIFECYCLE_STATE")

    if not computed_opportunity:
        actions.append("OPPORTUNITY_INDEX_COMPUTATION_MISSING")
    if not documented_cluster:
        actions.append("LIVE_CLUSTER_ROW_MISSING")
    if lifecycle_state not in FORMAL_LIFECYCLE_STATES:
        actions.append(f"UNKNOWN_LIFECYCLE_STATE:{lifecycle_state}")

    mismatches = _comparison_mismatches(computed_opportunity, documented_cluster)
    count_stale_mismatch = bool(mismatches and _count_mismatch_is_point_in_time_stale(mismatches))
    if count_stale_mismatch:
        limitations.append("OPPORTUNITY_CANDIDATE_COUNT_POINT_IN_TIME_STALE")
    elif mismatches:
        actions.append("OPPORTUNITY_CLUSTER_MISMATCH")

    if documented_cluster and not documented_cluster.get("opportunity_lifecycle_state"):
        limitations.append("LEGACY_CLUSTER_ROW_LIFECYCLE_STATE_NOT_CAPTURED")
    if documented_cluster and not documented_cluster.get("opportunity_lifecycle_signature"):
        limitations.append("LEGACY_CLUSTER_ROW_LIFECYCLE_SIGNATURE_NOT_CAPTURED")
    if documented_cluster and not documented_cluster.get("same_level_tolerance_band"):
        limitations.append("LEGACY_CLUSTER_ROW_TOLERANCE_BAND_NOT_CAPTURED")
    if not path_row and not ltf_row:
        actions.append("LATEST_CANDIDATE_PATH_ROW_MISSING")
    elif not path_row and ltf_row:
        limitations.append("CANDIDATE_PATH_ROW_MISSING_BUT_LTF_ORDER_RECOVERED")
    if not ltf_row:
        limitations.append("LTF_PATH_ORDER_ROW_NOT_AVAILABLE")
    if path_row and not path_row.get("source_ohlc_range"):
        limitations.append("LEGACY_PATH_ROW_SOURCE_OHLC_RANGE_NOT_CAPTURED")

    # Current v1 evidence supports entry+TP/SL resets. Expiry/cancel/
    # invalidation resets require pending-lifecycle truth, handled in LTO-005.
    limitations.append("NO_EXPLICIT_EXPIRY_OR_INVALIDATION_RESET_SOURCE_IN_LIFECYCLE_V1")

    reset_policy_status = _reset_policy_status(terminal)
    if lifecycle_state == "REOPENED_AFTER_TERMINAL" and (computed_opportunity or {}).get("opportunity_reset_reason") != "PRIOR_SIMILAR_OPPORTUNITY_TERMINATED_BEFORE_THIS_DECISION":
        actions.append("REOPENED_STATE_WITHOUT_TERMINAL_RESET_REASON")
    if lifecycle_state == "NEW_AFTER_COOLDOWN":
        limitations.append("COOLDOWN_WINDOW_NOT_EXPLICIT_IN_ASSIGNMENT_V1")

    if actions:
        audit_status = ACTION_REQUIRED
    elif limitations:
        audit_status = COMPLETE_WITH_LIMITATIONS
    else:
        audit_status = COMPLETE

    asof = str(
        path_row.get("asof_latest_candle_utc")
        or ltf_row.get("asof_latest_candle_utc")
        or ltf_row.get("window_end_utc")
        or ltf_row.get("terminal_event_utc")
        or (documented_cluster or {}).get("asof_latest_candle_utc")
        or ""
    )
    counting_status = (computed_opportunity or {}).get("opportunity_counting_status")
    if counting_status == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY":
        counting_rule_status = "COUNTABLE_PRIMARY_ONLY"
    elif counting_status == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE":
        counting_rule_status = "NOT_COUNTABLE_DUPLICATE_ACTIVE_SETUP"
    elif counting_status == "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP":
        counting_rule_status = "NOT_COUNTABLE_ACTIVE_SAME_SYMBOL_OVERLAP"
    else:
        counting_rule_status = "UNKNOWN_COUNTING_RULE_STATUS"

    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        candidate_id,
        asof,
        _comparison_projection(computed_opportunity),
        _comparison_projection(documented_cluster),
        terminal,
        counting_rule_status,
        actions,
        limitations,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("opportunity_lifecycle_audit", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "candidate_line_no": line_no,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "asof_latest_candle_utc": asof,
        "opportunity_assignment_algorithm_version": (computed_opportunity or {}).get(
            "opportunity_assignment_algorithm_version"
        )
        or OPPORTUNITY_ALGORITHM_VERSION,
        "opportunity_lifecycle_state": lifecycle_state,
        "formal_lifecycle_states": sorted(FORMAL_LIFECYCLE_STATES),
        "opportunity_lifecycle_signature": (computed_opportunity or {}).get("opportunity_lifecycle_signature")
        or candidate_lifecycle_signature(candidate),
        "same_level_tolerance_band": (computed_opportunity or {}).get("same_level_tolerance_band")
        or same_level_tolerance_band(candidate),
        "computed_opportunity_id": (computed_opportunity or {}).get("opportunity_id"),
        "documented_opportunity_id": (documented_cluster or {}).get("opportunity_id"),
        "opportunity_first_candidate_id": (computed_opportunity or {}).get("opportunity_first_candidate_id"),
        "opportunity_sequence_index": (computed_opportunity or {}).get("opportunity_sequence_index"),
        "opportunity_candidate_count": (computed_opportunity or {}).get("opportunity_candidate_count"),
        "opportunity_counting_status": counting_status,
        "opportunity_duplicate_status": (computed_opportunity or {}).get("opportunity_duplicate_status"),
        "opportunity_reset_reason": (computed_opportunity or {}).get("opportunity_reset_reason"),
        "same_symbol_overlap_status": (computed_opportunity or {}).get("same_symbol_overlap_status"),
        "overlapping_active_symbol_opportunity_ids": (computed_opportunity or {}).get(
            "overlapping_active_symbol_opportunity_ids"
        ),
        "candidate_terminal_event": {key: value for key, value in terminal.items() if not key.startswith("_")},
        "reset_policy_status": reset_policy_status,
        "opportunity_counting_rule_status": counting_rule_status,
        "cluster_comparison_status": (
            "MATCHED_COMPUTED_OPPORTUNITY_INDEX"
            if not mismatches and documented_cluster
            else "MATCHED_EXCEPT_POINT_IN_TIME_CANDIDATE_COUNT"
            if count_stale_mismatch
            else "MISMATCH_OR_MISSING_CLUSTER"
        ),
        "cluster_comparison_mismatches": mismatches,
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
        "opportunity_lifecycle_audit_status": audit_status,
        "manual_backfill_status": "BACKFILLED_FROM_CANDIDATE_PATH_LTF_AND_CLUSTER_ROWS",
        "no_leak_status": "POST_DECISION_OPPORTUNITY_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_opportunity_lifecycle_audit_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    path_rows: list[tuple[int, dict[str, Any]]] | None = None,
    ltf_rows: list[tuple[int, dict[str, Any]]] | None = None,
    cluster_rows: list[tuple[int, dict[str, Any]]] | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    filtered_candidates = [
        (line_no, row)
        for line_no, row in candidate_rows
        if not decision_date_prefix or str(row.get("decision_time_utc") or "").startswith(decision_date_prefix)
    ]
    candidates = [row for _, row in filtered_candidates]
    latest_paths = _latest_by_candidate(path_rows or [])
    latest_ltf = _latest_by_candidate(ltf_rows or [])
    latest_clusters = _latest_by_candidate(cluster_rows or [])
    computed_index = build_opportunity_index(
        candidates,
        latest_paths=latest_paths,
        latest_ltf=latest_ltf,
    )
    rows: list[dict[str, Any]] = []
    for line_no, candidate in filtered_candidates:
        cid = str(candidate.get("candidate_id") or "")
        rows.append(
            build_opportunity_lifecycle_audit_row(
                line_no,
                candidate,
                generated_at_utc=generated_at_utc,
                computed_opportunity=computed_index.get(cid),
                documented_cluster=latest_clusters.get(cid),
                path_row=latest_paths.get(cid),
                ltf_row=latest_ltf.get(cid),
            )
        )
    return rows
