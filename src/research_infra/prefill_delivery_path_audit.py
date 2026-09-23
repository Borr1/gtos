"""Pre-fill delivery path audit helpers.

This module is research/tooling only. It reads append-only pre-fill delivery
path rows plus post-decision path/resolution rows to separate exact
decision-time captures, as-of derived path fields, and structural V3 fields
that remain explicitly source-not-captured.

It does not call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "prefill_delivery_path_audit_v1"
COMPLETE = "PREFILL_DELIVERY_PATH_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "PREFILL_DELIVERY_PATH_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
WAITING = "PREFILL_DELIVERY_PATH_WAITING_FOR_PATH"
ACTION_REQUIRED = "PREFILL_DELIVERY_PATH_ACTION_REQUIRED"

PREFILL_STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
PENDING_LIMIT_STRATEGY_ID = "PENDING_LIMIT_LIFECYCLE"
PLACEHOLDER_DELIVERY_VALUES = {"", "unresolved", "unresolved_live_forward", "none"}
PLACEHOLDER_ORDERING_VALUES = {"", "unresolved", "none"}


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


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line), row) for line, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _latest_clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("asof_latest_candle_utc"))
        or parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(
    rows: list[tuple[int, dict[str, Any]]],
    *,
    date_prefix: str | None = None,
) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows, date_prefix=date_prefix)


def _latest_mechanical_by_key(rows: list[tuple[int, dict[str, Any]]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if not candidate_id or not strategy_id or not asof:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        key = (candidate_id, strategy_id, asof)
        current_key = (
            parse_utc(item.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            line_no,
        )
        previous = latest.get(key)
        previous_key = (
            parse_utc((previous or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int((previous or {}).get("_line_no") or 0),
        )
        if current_key >= previous_key:
            latest[key] = item
    return latest


def _mechanical_for(
    mechanical_by_key: dict[tuple[str, str, str], dict[str, Any]],
    candidate_id: str,
    strategy_id: str,
    asof: str,
) -> dict[str, Any] | None:
    if asof:
        row = mechanical_by_key.get((candidate_id, strategy_id, asof))
        if row:
            return row
    candidates = [
        row
        for (cid, sid, _row_asof), row in mechanical_by_key.items()
        if cid == candidate_id and sid == strategy_id
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int(row.get("_line_no") or 0),
        ),
    )


def _seconds_between(start: Any, end: Any) -> int | None:
    start_dt = parse_utc(start)
    end_dt = parse_utc(end)
    if not start_dt or not end_dt:
        return None
    return int((end_dt - start_dt).total_seconds())


def _status_for_present(value: Any) -> str:
    if value is None or value == "" or value == []:
        return "SOURCE_NOT_CAPTURED_LEGACY_ROW"
    if isinstance(value, dict) and not any(item is not None and item != "" for item in value.values()):
        return "SOURCE_NOT_CAPTURED_LEGACY_ROW"
    return "PREFILL_SOURCE_CAPTURED"


def _source_capture_statuses(prefill: dict[str, Any]) -> dict[str, str]:
    return {
        "entry_arming_time_utc": _status_for_present(prefill.get("entry_arming_time_utc")),
        "original_poi_bounds": _status_for_present(prefill.get("original_poi_bounds")),
        "fvg_ob_swing_state_at_arm": _status_for_present(prefill.get("fvg_ob_swing_state_at_arm")),
        "pre_fill_candles": _status_for_present(prefill.get("pre_fill_candles")),
        "pre_fill_ticks_summary": _status_for_present(prefill.get("pre_fill_ticks_summary")),
    }


def _overall_source_capture_status(statuses: dict[str, str]) -> str:
    required = {
        "entry_arming_time_utc",
        "original_poi_bounds",
        "fvg_ob_swing_state_at_arm",
    }
    if all(statuses.get(field) == "PREFILL_SOURCE_CAPTURED" for field in required):
        return "PREFILL_DECISION_CORE_SOURCE_CAPTURED"
    if any(statuses.get(field) == "PREFILL_SOURCE_CAPTURED" for field in required):
        return "PREFILL_DECISION_CORE_PARTIAL_SOURCE_CAPTURED"
    return "PREFILL_DECISION_CORE_SOURCE_NOT_CAPTURED"


def _decision_no_leak_status(prefill: dict[str, Any]) -> str:
    problems: list[str] = []
    delivery = str(prefill.get("delivery_leg_direction") or "").lower()
    ordering = str(prefill.get("lower_timeframe_path_ordering") or "").lower()
    if delivery not in PLACEHOLDER_DELIVERY_VALUES:
        problems.append("DELIVERY_LEG_DIRECTION_NOT_PLACEHOLDER")
    if ordering not in PLACEHOLDER_ORDERING_VALUES:
        problems.append("LOWER_TIMEFRAME_ORDERING_NOT_PLACEHOLDER")
    if prefill.get("fill_happened") is not None:
        problems.append("FILL_HAPPENED_PRESENT_IN_DECISION_ROW")
    if prefill.get("fill_delay_seconds") is not None:
        problems.append("FILL_DELAY_PRESENT_IN_DECISION_ROW")
    if prefill.get("reversal_leg_timing") is not None:
        problems.append("REVERSAL_LEG_TIMING_PRESENT_IN_DECISION_ROW")
    return "NO_POST_OUTCOME_STATE_IN_PREFILL_DECISION_ROW" if not problems else "PREFILL_DECISION_ROW_POST_OUTCOME_STATE:" + ",".join(problems)


def _path_outcome_status(path: dict[str, Any] | None, resolution: dict[str, Any] | None) -> str | None:
    status = (resolution or {}).get("path_outcome_status") or (path or {}).get("path_outcome_status")
    if status:
        return str(status)
    label = str((resolution or path or {}).get("path_label") or "")
    label_map = {
        "entry_touched_then_reached_tp1": "ENTRY_TOUCHED_THEN_TP1",
        "went_through_entry_and_continued_to_sl": "ENTRY_TOUCHED_THEN_SL",
        "continued_without_entry_touch_to_tp_area": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
    }
    return label_map.get(label)


def _derive_fill_state(
    prefill: dict[str, Any],
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    ltf = ltf or {}
    path = path or {}
    resolution = resolution or {}
    entry_touch_utc = ltf.get("entry_first_touch_utc")
    path_touched = resolution.get("touched_entry")
    if path_touched is None:
        path_touched = path.get("touched_entry")
    if ltf and ltf.get("ltf_status") == "M1_PATH_RECOVERED":
        source_status = "DERIVED_FROM_LTF_PATH_ORDER_ASOF"
        fill_happened = bool(entry_touch_utc)
    elif path or resolution:
        source_status = "DERIVED_FROM_CANDIDATE_PATH_ASOF"
        fill_happened = bool(path_touched) if path_touched is not None else None
    else:
        source_status = "UNRESOLVED_PATH"
        fill_happened = None
    return {
        "source_status": source_status,
        "fill_happened_derived": fill_happened,
        "fill_delay_seconds_derived": _seconds_between(prefill.get("entry_arming_time_utc"), entry_touch_utc)
        if entry_touch_utc
        else None,
        "entry_first_touch_utc": entry_touch_utc,
        "path_touched_entry": path_touched,
        "ltf_status": ltf.get("ltf_status"),
        "terminal_outcome_status": ltf.get("terminal_outcome_status"),
        "terminal_order_ambiguity": ltf.get("terminal_order_ambiguity"),
    }


def _derive_delivery_leg_state(
    prefill: dict[str, Any],
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    outcome = str((ltf or {}).get("terminal_outcome_status") or _path_outcome_status(path, resolution) or "")
    path_label = (resolution or path or {}).get("path_label")
    touched_entry = (resolution or path or {}).get("touched_entry")
    if not path and not resolution and not ltf:
        derived = "UNRESOLVED_PATH"
        source_status = "UNRESOLVED_PATH"
    elif "SAME_M1_AMBIGUOUS" in outcome or (ltf or {}).get("terminal_order_ambiguity") is True:
        derived = "AMBIGUOUS_PATH_ORDER_REQUIRES_TICKS"
        source_status = "DERIVED_FROM_LTF_PATH_ORDER_ASOF"
    elif outcome in {
        "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
        "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
    }:
        derived = "MOVED_AWAY_FROM_ENTRY_TOWARD_TP_AREA_WITHOUT_FILL"
        source_status = "DERIVED_FROM_ASOF_PATH"
    elif outcome == "NO_ENTRY_SL_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        derived = "MOVED_AWAY_FROM_ENTRY_TOWARD_SL_AREA_WITHOUT_FILL"
        source_status = "DERIVED_FROM_LTF_PATH_ORDER_ASOF"
    elif outcome.startswith("ENTRY_") or touched_entry is True:
        derived = "REACHED_ENTRY_AFTER_ARM"
        source_status = "DERIVED_FROM_ASOF_PATH"
    elif outcome == "NO_ENTRY_TOUCH_BY_LTF_ASOF" or touched_entry is False:
        derived = "NOT_REACHED_ENTRY_BY_ASOF"
        source_status = "DERIVED_FROM_ASOF_PATH"
    else:
        derived = "PATH_OBSERVED_UNCLASSIFIED"
        source_status = "DERIVED_FROM_ASOF_PATH"
    return {
        "source_status": source_status,
        "delivery_leg_direction_derived": derived,
        "path_outcome_status": outcome or None,
        "path_label": path_label,
        "original_decision_placeholder": prefill.get("delivery_leg_direction"),
    }


def _derive_reversal_leg_state(
    fill_state: dict[str, Any],
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    outcome = str((ltf or {}).get("terminal_outcome_status") or _path_outcome_status(path, resolution) or "")
    terminal_event_utc = (ltf or {}).get("terminal_event_utc")
    terminal_event_r = (ltf or {}).get("terminal_event_r")
    if fill_state.get("source_status") == "UNRESOLVED_PATH":
        state = "UNRESOLVED_PATH"
        source_status = "UNRESOLVED_PATH"
    elif "SAME_M1_AMBIGUOUS" in outcome or (ltf or {}).get("terminal_order_ambiguity") is True:
        state = "AMBIGUOUS_LTF_ORDER_REQUIRES_TICKS"
        source_status = "DERIVED_FROM_LTF_PATH_ORDER_ASOF"
    elif fill_state.get("fill_happened_derived") is False:
        state = "NO_REVERSAL_LEG_NO_FILL"
        source_status = fill_state.get("source_status")
    elif outcome in {"ENTRY_THEN_TP1", "ENTRY_TOUCHED_THEN_TP1"}:
        state = "FILLED_THEN_TP1"
        source_status = "DERIVED_FROM_ASOF_PATH"
    elif outcome in {"ENTRY_THEN_SL", "ENTRY_TOUCHED_THEN_SL"}:
        state = "FILLED_THEN_SL"
        source_status = "DERIVED_FROM_ASOF_PATH"
    elif outcome == "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF" or fill_state.get("fill_happened_derived") is True:
        state = "ENTRY_TOUCHED_REVERSAL_UNRESOLVED_BY_ASOF"
        source_status = fill_state.get("source_status")
    else:
        state = "REVERSAL_LEG_UNCLASSIFIED"
        source_status = fill_state.get("source_status")
    return {
        "source_status": source_status,
        "reversal_leg_state_derived": state,
        "terminal_event_utc": terminal_event_utc,
        "terminal_event_r": terminal_event_r,
        "terminal_outcome_status": outcome or None,
    }


def _cancel_expiry_state(prefill: dict[str, Any], pending_audit: dict[str, Any] | None) -> dict[str, Any]:
    if pending_audit:
        return {
            "source_status": "DERIVED_FROM_PENDING_LIMIT_LIFECYCLE_AUDIT",
            "final_state": pending_audit.get("final_state"),
            "final_state_status": pending_audit.get("final_state_status"),
            "latest_lifecycle_intent_after_check": pending_audit.get("latest_lifecycle_intent_after_check"),
            "latest_lifecycle_fill_no_fill_label": pending_audit.get("latest_lifecycle_fill_no_fill_label"),
            "prefill_abort_reason_at_log": prefill.get("cancel_expiry_abort_reason"),
        }
    return {
        "source_status": "PREFILL_DECISION_OUTCOME_CAPTURED",
        "final_state": prefill.get("cancel_expiry_abort_reason"),
        "final_state_status": "FINAL_OUTCOME_AT_PREFILL_LOG_ONLY",
        "latest_lifecycle_intent_after_check": None,
        "latest_lifecycle_fill_no_fill_label": None,
        "prefill_abort_reason_at_log": prefill.get("cancel_expiry_abort_reason"),
    }


def _structural_source_state(structural: dict[str, Any] | None, field: str) -> dict[str, Any]:
    structural = structural or {}
    missing = structural.get("missing_exact_required_fields") or {}
    raw_status = missing.get(field)
    if raw_status == "SOURCE_NOT_CAPTURED" or not structural:
        status = "SOURCE_NOT_CAPTURED"
    else:
        status = "CAPTURED_OR_RECOVERED_EXACT"
    return {
        "source_status": status,
        "source_field_status": raw_status or "STRUCTURAL_METADATA_ROW_NOT_AVAILABLE",
        "source_row_key": structural.get("row_key"),
        "scoreability_effect": "V3_NOT_LIVE_SCORABLE_WHILE_SOURCE_NOT_CAPTURED"
        if status == "SOURCE_NOT_CAPTURED"
        else "V3_FIELD_AVAILABLE_FOR_FUTURE_SCORER",
    }


def _strategy_state(strategy_id: str, resolution: dict[str, Any] | None, mechanical: dict[str, Any] | None) -> dict[str, Any]:
    outcomes = ((resolution or {}).get("strategy_outcomes") or {})
    resolution_state = outcomes.get(strategy_id) if isinstance(outcomes, dict) else {}
    resolution_state = resolution_state if isinstance(resolution_state, dict) else {}
    mechanical = mechanical or {}
    return {
        "strategy_id": strategy_id,
        "strategy_status": mechanical.get("strategy_status") or resolution_state.get("strategy_status"),
        "score_status": mechanical.get("score_status") or resolution_state.get("score_status"),
        "outcome_status": mechanical.get("outcome_status") or resolution_state.get("outcome_status"),
        "status_reason": mechanical.get("status_reason") or resolution_state.get("status_reason"),
        "outcome_source": mechanical.get("outcome_source"),
        "strategy_proxy_r": mechanical.get("strategy_proxy_r"),
    }


def _latest_asof(resolution: dict[str, Any] | None, path: dict[str, Any] | None) -> str | None:
    return (resolution or {}).get("asof_latest_candle_utc") or (path or {}).get("asof_latest_candle_utc")


def _dependency_signature(
    *,
    prefill: dict[str, Any],
    resolution: dict[str, Any] | None,
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    pending_audit: dict[str, Any] | None,
    opportunity: dict[str, Any] | None,
    structural: dict[str, Any] | None,
    mechanical_rows: list[dict[str, Any] | None],
) -> str:
    parts = [
        prefill.get("created_at_utc"),
        prefill.get("_line_no"),
        (resolution or {}).get("row_key"),
        (resolution or {}).get("created_at_utc"),
        (path or {}).get("created_at_utc"),
        (ltf or {}).get("row_key"),
        (ltf or {}).get("created_at_utc"),
        (pending_audit or {}).get("row_key"),
        (pending_audit or {}).get("created_at_utc"),
        (opportunity or {}).get("row_key"),
        (opportunity or {}).get("created_at_utc"),
        (structural or {}).get("row_key"),
        (structural or {}).get("created_at_utc"),
    ]
    parts.extend((row or {}).get("created_at_utc") for row in mechanical_rows)
    return _stable_hash(*parts)


def build_prefill_delivery_path_audit_rows(
    prefill_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    resolution_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    *,
    mechanical_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    ltf_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    pending_lifecycle_audit_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    structural_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    prefill_by_candidate = _latest_by_candidate(_rows_with_lines(prefill_rows), date_prefix=decision_date_prefix)
    resolutions_by_candidate = _latest_by_candidate(_rows_with_lines(resolution_rows))
    paths_by_candidate = _latest_by_candidate(_rows_with_lines(path_rows))
    ltf_by_candidate = _latest_by_candidate(_rows_with_lines(ltf_rows))
    pending_audit_by_candidate = _latest_by_candidate(_rows_with_lines(pending_lifecycle_audit_rows))
    opportunities_by_candidate = _latest_by_candidate(_rows_with_lines(opportunity_rows))
    structural_by_candidate = _latest_by_candidate(_rows_with_lines(structural_rows))
    mechanical_by_key = _latest_mechanical_by_key(_rows_with_lines(mechanical_rows))

    rows: list[dict[str, Any]] = []
    for candidate_id, prefill in sorted(prefill_by_candidate.items(), key=lambda item: (str(item[1].get("decision_time_utc") or ""), item[0])):
        resolution = resolutions_by_candidate.get(candidate_id)
        path = paths_by_candidate.get(candidate_id)
        ltf = ltf_by_candidate.get(candidate_id)
        pending_audit = pending_audit_by_candidate.get(candidate_id)
        opportunity = opportunities_by_candidate.get(candidate_id)
        structural = structural_by_candidate.get(candidate_id)
        asof = str(_latest_asof(resolution, path) or "")
        prefill_mech = _mechanical_for(mechanical_by_key, candidate_id, PREFILL_STRATEGY_ID, asof)
        pending_mech = _mechanical_for(mechanical_by_key, candidate_id, PENDING_LIMIT_STRATEGY_ID, asof)

        source_statuses = _source_capture_statuses(prefill)
        source_capture_status = _overall_source_capture_status(source_statuses)
        decision_no_leak = _decision_no_leak_status(prefill)
        fill_state = _derive_fill_state(prefill, path, ltf, resolution)
        delivery_leg_state = _derive_delivery_leg_state(prefill, path, ltf, resolution)
        reversal_leg_state = _derive_reversal_leg_state(fill_state, path, ltf, resolution)
        cancel_state = _cancel_expiry_state(prefill, pending_audit)
        reentry_state = _structural_source_state(structural, "post_lock_reentry_state")
        cost_state = _structural_source_state(structural, "cost_aware_min_r_fields")
        prefill_strategy = _strategy_state(PREFILL_STRATEGY_ID, resolution, prefill_mech)
        pending_strategy = _strategy_state(PENDING_LIMIT_STRATEGY_ID, resolution, pending_mech)

        actions: list[str] = []
        limitations: list[str] = []
        if not candidate_id:
            actions.append("PREFILL_CANDIDATE_ID_MISSING")
        if decision_no_leak != "NO_POST_OUTCOME_STATE_IN_PREFILL_DECISION_ROW":
            actions.append(decision_no_leak)
        if source_capture_status != "PREFILL_DECISION_CORE_SOURCE_CAPTURED":
            limitations.append(source_capture_status)
        if source_statuses.get("pre_fill_candles") != "PREFILL_SOURCE_CAPTURED":
            limitations.append("EXACT_PREFILL_CANDLE_SEQUENCE_SOURCE_NOT_CAPTURED")
        if source_statuses.get("pre_fill_ticks_summary") != "PREFILL_SOURCE_CAPTURED":
            limitations.append("EXACT_PREFILL_TICK_SUMMARY_SOURCE_NOT_CAPTURED")
        if not prefill.get("source_hash"):
            limitations.append("PREFILL_SOURCE_HASH_NOT_CAPTURED")
        if not prefill.get("source_symbol"):
            limitations.append("PREFILL_SOURCE_SYMBOL_NOT_CAPTURED")
        if not prefill.get("trade_id"):
            limitations.append("PREFILL_TRADE_ID_NOT_CAPTURED")
        if not resolution:
            limitations.append("PREFILL_RESOLUTION_ROW_NOT_AVAILABLE_YET")
        if not path:
            limitations.append("CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_PREFILL")
        if not opportunity:
            limitations.append("OPPORTUNITY_CLUSTER_ROW_NOT_AVAILABLE_FOR_DUPLICATE_AWARE_COUNTING")
        if reentry_state["source_status"] == "SOURCE_NOT_CAPTURED":
            limitations.append("POST_LOCK_REENTRY_ELIGIBILITY_SOURCE_NOT_CAPTURED")
        if cost_state["source_status"] == "SOURCE_NOT_CAPTURED":
            limitations.append("COST_AWARE_MIN_R_SOURCE_NOT_CAPTURED")
        if prefill_strategy.get("score_status") in {None, "", "NOT_COMPUTABLE"}:
            limitations.append("PREFILL_DELIVERY_REVERSAL_SCORER_NOT_IMPLEMENTED")
        if delivery_leg_state["delivery_leg_direction_derived"] == "AMBIGUOUS_PATH_ORDER_REQUIRES_TICKS":
            limitations.append("AMBIGUOUS_PATH_ORDER_EXCLUDED_FROM_V3_SCORING")

        resolved_path = bool((resolution or {}).get("resolution_status") == "RESOLVED_FROM_LIVE_PATH_ROW" or path)
        audit_status = ACTION_REQUIRED if actions else WAITING if not resolved_path else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
        dependency_signature = _dependency_signature(
            prefill=prefill,
            resolution=resolution,
            path=path,
            ltf=ltf,
            pending_audit=pending_audit,
            opportunity=opportunity,
            structural=structural,
            mechanical_rows=[prefill_mech, pending_mech],
        )
        row_key = _stable_hash(SCHEMA_VERSION, candidate_id, asof, dependency_signature)
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_key": row_key,
            "source_dependency_signature": dependency_signature,
            "created_at_utc": generated_at_utc,
            "backfilled_at_utc": generated_at_utc,
            "candidate_id": candidate_id,
            "symbol": prefill.get("symbol"),
            "broker_symbol": prefill.get("broker_symbol"),
            "source_symbol": prefill.get("source_symbol"),
            "session": prefill.get("session") or prefill.get("kill_zone"),
            "kill_zone": prefill.get("kill_zone"),
            "side": prefill.get("side"),
            "framework": (prefill.get("fvg_ob_swing_state_at_arm") or {}).get("framework"),
            "decision_time_utc": prefill.get("decision_time_utc"),
            "trade_id": prefill.get("trade_id"),
            "source_prefill_line_no": prefill.get("_line_no"),
            "source_prefill_created_at_utc": prefill.get("created_at_utc"),
            "structural_setup_id": prefill.get("structural_setup_id"),
            "entry_arming_time_utc": prefill.get("entry_arming_time_utc"),
            "original_poi_bounds": prefill.get("original_poi_bounds"),
            "fvg_ob_swing_state_at_arm": prefill.get("fvg_ob_swing_state_at_arm"),
            "source_capture_statuses": source_statuses,
            "prefill_source_capture_status": source_capture_status,
            "decision_prefill_no_leak_status": decision_no_leak,
            "latest_resolution_row_key": (resolution or {}).get("row_key"),
            "latest_resolution_status": (resolution or {}).get("resolution_status"),
            "latest_resolution_asof_utc": (resolution or {}).get("asof_latest_candle_utc"),
            "latest_path_asof_utc": (path or {}).get("asof_latest_candle_utc"),
            "path_label": (resolution or path or {}).get("path_label"),
            "path_outcome_status": _path_outcome_status(path, resolution),
            "fill_state": fill_state,
            "delivery_leg_state": delivery_leg_state,
            "reversal_leg_state": reversal_leg_state,
            "cancel_expiry_state": cancel_state,
            "post_lock_reentry_eligibility": reentry_state,
            "cost_aware_min_r": cost_state,
            "prefill_delivery_reversal_outcome": prefill_strategy,
            "pending_limit_lifecycle_outcome": pending_strategy,
            "pending_limit_lifecycle_audit_status": (pending_audit or {}).get("pending_limit_lifecycle_audit_status"),
            "pending_limit_final_state": (pending_audit or {}).get("final_state"),
            "opportunity_id": (opportunity or {}).get("opportunity_id"),
            "opportunity_counting_status": (opportunity or {}).get("opportunity_counting_status"),
            "opportunity_duplicate_status": (opportunity or {}).get("opportunity_duplicate_status"),
            "duplicate_aware_counting_status": (
                "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                if (opportunity or {}).get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                else (opportunity or {}).get("opportunity_counting_status") or "NO_OPPORTUNITY_CLUSTER_ROW"
            ),
            "derived_prefill_path_status": fill_state["source_status"],
            "prefill_delivery_path_audit_status": audit_status,
            "documented_limitation_codes": sorted(set(limitations)),
            "action_required_codes": sorted(set(actions)),
            "manual_backfill_status": "BACKFILLED_FROM_PREFILL_RESOLUTION_PATH_LTF_PENDING_STRUCTURAL_AND_OPPORTUNITY_ROWS",
            "no_leak_status": "POST_DECISION_PREFILL_AUDIT_NO_DECISION_FEATURE",
            "promotion_verdict": PROMOTION_VERDICT,
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
            "paid_fetch_attempted": False,
            "scoreability_rule": (
                "V3/pre-fill rows remain exploratory. Exact arming time, original POI, "
                "and at-arm structure can be source-captured at decision time; delivery, "
                "fill, cancel, and reversal state are derived only from as-of post-decision "
                "path rows. Post-lock reentry eligibility and cost-aware min-R remain "
                "not scoreable until exact selector fields are captured."
            ),
        }
        rows.append(row)
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("prefill_delivery_path_audit_status") or "UNKNOWN") for row in rows)
    source_counts = Counter(str(row.get("prefill_source_capture_status") or "UNKNOWN") for row in rows)
    path_status_counts = Counter(str(row.get("derived_prefill_path_status") or "UNKNOWN") for row in rows)
    delivery_counts = Counter(str((row.get("delivery_leg_state") or {}).get("delivery_leg_direction_derived") or "UNKNOWN") for row in rows)
    reversal_counts = Counter(str((row.get("reversal_leg_state") or {}).get("reversal_leg_state_derived") or "UNKNOWN") for row in rows)
    reentry_counts = Counter(str((row.get("post_lock_reentry_eligibility") or {}).get("source_status") or "UNKNOWN") for row in rows)
    cost_counts = Counter(str((row.get("cost_aware_min_r") or {}).get("source_status") or "UNKNOWN") for row in rows)
    fill_counts = Counter(str((row.get("fill_state") or {}).get("fill_happened_derived")) for row in rows)
    limitation_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    for row in rows:
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])

    total = len(rows)
    duplicate_countable = sum(
        1
        for row in rows
        if row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    )
    return {
        "schema_version": "prefill_delivery_path_rolling_status_v1",
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_counts else "OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS",
        "prefill_rows": total,
        "resolved_path_rows": sum(1 for row in rows if row.get("latest_resolution_status") == "RESOLVED_FROM_LIVE_PATH_ROW"),
        "core_source_captured_rows": sum(1 for row in rows if row.get("prefill_source_capture_status") == "PREFILL_DECISION_CORE_SOURCE_CAPTURED"),
        "derived_path_rows": sum(1 for row in rows if str(row.get("derived_prefill_path_status") or "").startswith("DERIVED_FROM")),
        "duplicate_aware_countable_path_rows": duplicate_countable,
        "status_counts": dict(status_counts),
        "source_capture_status_counts": dict(source_counts),
        "derived_prefill_path_status_counts": dict(path_status_counts),
        "fill_happened_derived_counts": dict(fill_counts),
        "delivery_leg_direction_counts": dict(delivery_counts),
        "reversal_leg_state_counts": dict(reversal_counts),
        "post_lock_reentry_eligibility_status_counts": dict(reentry_counts),
        "cost_aware_min_r_status_counts": dict(cost_counts),
        "documented_limitation_counts": dict(limitation_counts),
        "action_required_counts": dict(action_counts),
        "no_leak_status": (
            "NO_DECISION_PREFILL_LEAKS_DETECTED"
            if not any(row.get("decision_prefill_no_leak_status") != "NO_POST_OUTCOME_STATE_IN_PREFILL_DECISION_ROW" for row in rows)
            else "ACTION_REQUIRED_DECISION_PREFILL_LEAK_STATUS_PRESENT"
        ),
    }
