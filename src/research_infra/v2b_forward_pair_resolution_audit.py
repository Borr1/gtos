"""V2b forward-pair resolution audit helpers.

This module is research/tooling only. It reads append-only V2b decision-time
pair rows, post-decision path/resolution rows, mechanical strategy outcomes,
opportunity clusters, pending lifecycle audits, and account-truth blockers to
separate broker-actual R, synthetic path R, and unresolved path evidence.

It does not call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "v2b_forward_pair_resolution_audit_v1"
COMPLETE = "V2B_FORWARD_PAIR_RESOLUTION_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "V2B_FORWARD_PAIR_RESOLUTION_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
WAITING = "V2B_FORWARD_PAIR_RESOLUTION_WAITING_FOR_PATH"
ACTION_REQUIRED = "V2B_FORWARD_PAIR_RESOLUTION_ACTION_REQUIRED"

V2B_STRATEGY_ID = "V2B_OB_BOUNDARY_PROSPECTIVE"
BASELINE_STRATEGY_ID = "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
FIXED_R_COMPARATOR_ID = BASELINE_STRATEGY_ID
FVG_COMPARATOR_IDS = ("V2_STRUCT_FVG_MID_EDGE", "FVG_OB_CONFLUENCE_OB_AFTER_FVG")

COUNTABLE_SCORE_STATUSES = {
    "COMPUTED_FROM_CANDIDATE_PATH",
    "COMPUTED_FROM_PENDING_LIFECYCLE",
    "COMPUTED_FROM_LTF_PATH_ORDER",
}
AMBIGUOUS_SCORE_STATUSES = {
    "AMBIGUOUS_LTF_ORDER",
    "AMBIGUOUS_M15_ORDER_REQUIRES_LTF",
}
SOURCE_NOT_CAPTURED_SCORE_PREFIXES = (
    "MISSING_REQUIRED",
    "NOT_COMPUTABLE",
)


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


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _latest_mechanical_by_key(
    rows: list[tuple[int, dict[str, Any]]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
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


def _proxy_r_for_outcome(outcome_status: str) -> float | None:
    if outcome_status == "ENTRY_TOUCHED_THEN_TP1":
        return 1.5
    if outcome_status == "ENTRY_TOUCHED_THEN_SL":
        return -1.0
    if outcome_status.startswith("NO_FILL_") or outcome_status == "NO_ENTRY_TOUCH_BY_ASOF":
        return 0.0
    return None


def _actual_r_from_account(row: dict[str, Any] | None) -> float | None:
    row = row or {}
    for field in ("actual_r", "broker_actual_r", "account_actual_r", "realized_r", "net_r"):
        value = safe_float(row.get(field))
        if value is not None:
            return value
    return None


def _account_truth_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_ACCOUNT_TRUTH_ROW"
    if row.get("actual_r_claim_allowed") is False:
        return "ACCOUNT_TRUTH_SOURCE_BLOCKED_NO_BROKER_ACTUAL_R"
    if row.get("actual_r_claim_allowed") is True and _actual_r_from_account(row) is not None:
        return "BROKER_ACTUAL_R_AVAILABLE"
    if row.get("actual_r_claim_allowed") is True:
        return "BROKER_ACTUAL_R_ALLOWED_VALUE_MISSING"
    return str(row.get("account_truth_status") or "ACCOUNT_TRUTH_STATUS_UNKNOWN")


def _decision_pair_no_leak_status(pair: dict[str, Any]) -> str:
    lane = str(pair.get("actual_synthetic_label_lane") or "")
    if lane != "no_outcome_at_decision_time":
        return "DECISION_PAIR_POST_OUTCOME_LANE_NOT_PLACEHOLDER"
    for field in ("ob_boundary_outcome", "j46_baseline_outcome", "fixed_r_comparator", "fvg_comparator"):
        value = pair.get(field)
        if not isinstance(value, dict):
            return f"DECISION_PAIR_{field.upper()}_NOT_OBJECT"
        status = str(value.get("label_status") or "")
        if status not in {"unresolved_live_forward", "unresolved", ""}:
            return f"DECISION_PAIR_{field.upper()}_POST_OUTCOME_STATUS:{status}"
    return "NO_POST_OUTCOME_LABEL_IN_DECISION_PAIR"


def _state_from_strategy(
    *,
    strategy_id: str,
    role: str,
    resolution: dict[str, Any] | None,
    mechanical: dict[str, Any] | None,
    account_truth: dict[str, Any] | None,
) -> dict[str, Any]:
    resolution_outcomes = ((resolution or {}).get("strategy_outcomes") or {})
    resolution_state = resolution_outcomes.get(strategy_id) if isinstance(resolution_outcomes, dict) else None
    resolution_state = resolution_state if isinstance(resolution_state, dict) else {}
    mechanical = mechanical or {}
    score_status = str(mechanical.get("score_status") or resolution_state.get("score_status") or "")
    outcome_status = str(mechanical.get("outcome_status") or resolution_state.get("outcome_status") or "")
    strategy_status = str(mechanical.get("strategy_status") or resolution_state.get("strategy_status") or "")
    status_reason = mechanical.get("status_reason") or resolution_state.get("status_reason")
    outcome_source = mechanical.get("outcome_source")
    proxy_r = safe_float(mechanical.get("strategy_proxy_r"))
    if proxy_r is None and score_status in COUNTABLE_SCORE_STATUSES:
        proxy_r = _proxy_r_for_outcome(outcome_status)

    actual_truth_status = _account_truth_status(account_truth)
    broker_actual_r = _actual_r_from_account(account_truth)
    limitations: list[str] = []
    actions: list[str] = []

    if (account_truth or {}).get("account_truth_status") and "MISMATCH" in str((account_truth or {}).get("account_truth_status")):
        actions.append("BROKER_POSITION_MISMATCH_REPORTED_BY_ACCOUNT_TRUTH")

    if actual_truth_status == "BROKER_ACTUAL_R_AVAILABLE":
        lane = "BROKER_ACTUAL_R"
        r_value = broker_actual_r
        r_counted = broker_actual_r is not None
        r_counting_status = "BROKER_ACTUAL_R_COUNTED" if r_counted else "BROKER_ACTUAL_R_ALLOWED_VALUE_MISSING"
    elif score_status in COUNTABLE_SCORE_STATUSES and proxy_r is not None:
        lane = "SYNTHETIC_PATH_R"
        r_value = proxy_r
        r_counted = True
        r_counting_status = score_status
        limitations.append(actual_truth_status)
    elif score_status in AMBIGUOUS_SCORE_STATUSES or "AMBIGUOUS" in outcome_status:
        lane = "UNRESOLVED_PATH"
        r_value = None
        r_counted = False
        r_counting_status = "AMBIGUOUS_EXCLUDED_FROM_R"
        limitations.append("AMBIGUOUS_PATH_EXCLUDED_FROM_R")
    elif not resolution:
        lane = "UNRESOLVED_PATH"
        r_value = None
        r_counted = False
        r_counting_status = "WAITING_FOR_V2B_RESOLUTION_ROW"
        limitations.append("V2B_RESOLUTION_ROW_NOT_AVAILABLE_YET")
    elif score_status.startswith(SOURCE_NOT_CAPTURED_SCORE_PREFIXES) or not score_status:
        lane = "UNRESOLVED_PATH"
        r_value = None
        r_counted = False
        r_counting_status = "SOURCE_NOT_CAPTURED_OR_NOT_COMPUTABLE"
        limitations.append("STRATEGY_SPECIFIC_EXACT_FIELDS_SOURCE_NOT_CAPTURED")
    else:
        lane = "UNRESOLVED_PATH"
        r_value = None
        r_counted = False
        r_counting_status = score_status or "STRATEGY_OUTCOME_NOT_R_COUNTABLE"
        limitations.append("STRATEGY_OUTCOME_NOT_R_COUNTABLE")

    if strategy_status == "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH":
        limitations.append("OB_BOUNDARY_USES_SHARED_CANDIDATE_PATH_PROXY_NOT_EXACT_V2_LOCK_METADATA")
    if role == "fvg_comparator" and lane == "UNRESOLVED_PATH":
        limitations.append("FVG_COMPARATOR_EXACT_ENTRY_OR_LOCK_METADATA_SOURCE_NOT_CAPTURED")

    return {
        "role": role,
        "strategy_id": strategy_id,
        "label_lane": lane,
        "r_counted": r_counted,
        "r_value": r_value,
        "r_counting_status": r_counting_status,
        "broker_actual_r": broker_actual_r if lane == "BROKER_ACTUAL_R" else None,
        "synthetic_path_r": r_value if lane == "SYNTHETIC_PATH_R" else None,
        "actual_r_lane_status": actual_truth_status,
        "score_status": score_status or None,
        "outcome_status": outcome_status or None,
        "strategy_status": strategy_status or None,
        "status_reason": status_reason,
        "outcome_source": outcome_source,
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
    }


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
    # Fallback for waiting/no-resolution rows: use the latest strategy row.
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


def _choose_fvg_mechanical(
    mechanical_by_key: dict[tuple[str, str, str], dict[str, Any]],
    candidate_id: str,
    asof: str,
) -> tuple[str, dict[str, Any] | None]:
    for strategy_id in FVG_COMPARATOR_IDS:
        row = _mechanical_for(mechanical_by_key, candidate_id, strategy_id, asof)
        if row:
            return strategy_id, row
    return FVG_COMPARATOR_IDS[0], None


def _dependency_signature(
    *,
    pair: dict[str, Any],
    resolution: dict[str, Any] | None,
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    account_truth: dict[str, Any] | None,
    opportunity: dict[str, Any] | None,
    pending_audit: dict[str, Any] | None,
    mechanical_rows: list[dict[str, Any] | None],
) -> str:
    parts = [
        pair.get("created_at_utc"),
        pair.get("_line_no"),
        (resolution or {}).get("row_key"),
        (resolution or {}).get("created_at_utc"),
        (path or {}).get("created_at_utc"),
        (ltf or {}).get("row_key"),
        (ltf or {}).get("created_at_utc"),
        (account_truth or {}).get("row_key"),
        (account_truth or {}).get("created_at_utc"),
        (opportunity or {}).get("row_key"),
        (opportunity or {}).get("created_at_utc"),
        (pending_audit or {}).get("row_key"),
        (pending_audit or {}).get("created_at_utc"),
    ]
    parts.extend((row or {}).get("created_at_utc") for row in mechanical_rows)
    return _stable_hash(*parts)


def _pair_label_lane(*states: dict[str, Any]) -> str:
    lanes = {str(state.get("label_lane") or "") for state in states if state}
    if lanes == {"BROKER_ACTUAL_R"}:
        return "BROKER_ACTUAL_R"
    if lanes and lanes <= {"SYNTHETIC_PATH_R"}:
        return "SYNTHETIC_PATH_R"
    if "BROKER_ACTUAL_R" in lanes and "SYNTHETIC_PATH_R" in lanes:
        return "MIXED_BROKER_ACTUAL_AND_SYNTHETIC_PATH_R"
    return "UNRESOLVED_PATH"


def _latest_asof(resolution: dict[str, Any] | None, path: dict[str, Any] | None) -> str | None:
    return (resolution or {}).get("asof_latest_candle_utc") or (path or {}).get("asof_latest_candle_utc")


def build_v2b_forward_pair_audit_rows(
    pair_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    resolution_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    *,
    mechanical_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    ltf_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    account_truth_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    pending_lifecycle_audit_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    pairs_by_candidate = _latest_by_candidate(_rows_with_lines(pair_rows), date_prefix=decision_date_prefix)
    resolutions_by_candidate = _latest_by_candidate(_rows_with_lines(resolution_rows))
    paths_by_candidate = _latest_by_candidate(_rows_with_lines(path_rows))
    ltf_by_candidate = _latest_by_candidate(_rows_with_lines(ltf_rows))
    account_by_candidate = _latest_by_candidate(_rows_with_lines(account_truth_rows))
    opportunities_by_candidate = _latest_by_candidate(_rows_with_lines(opportunity_rows))
    pending_audit_by_candidate = _latest_by_candidate(_rows_with_lines(pending_lifecycle_audit_rows))
    mechanical_by_key = _latest_mechanical_by_key(_rows_with_lines(mechanical_rows))

    rows: list[dict[str, Any]] = []
    for candidate_id, pair in sorted(pairs_by_candidate.items(), key=lambda item: (str(item[1].get("decision_time_utc") or ""), item[0])):
        resolution = resolutions_by_candidate.get(candidate_id)
        path = paths_by_candidate.get(candidate_id)
        ltf = ltf_by_candidate.get(candidate_id)
        account_truth = account_by_candidate.get(candidate_id)
        opportunity = opportunities_by_candidate.get(candidate_id)
        pending_audit = pending_audit_by_candidate.get(candidate_id)
        asof = str(_latest_asof(resolution, path) or "")

        v2b_mech = _mechanical_for(mechanical_by_key, candidate_id, V2B_STRATEGY_ID, asof)
        baseline_mech = _mechanical_for(mechanical_by_key, candidate_id, BASELINE_STRATEGY_ID, asof)
        fixed_mech = _mechanical_for(mechanical_by_key, candidate_id, FIXED_R_COMPARATOR_ID, asof)
        fvg_strategy_id, fvg_mech = _choose_fvg_mechanical(mechanical_by_key, candidate_id, asof)

        ob_boundary_state = _state_from_strategy(
            strategy_id=V2B_STRATEGY_ID,
            role="ob_boundary_target",
            resolution=resolution,
            mechanical=v2b_mech,
            account_truth=account_truth,
        )
        baseline_state = _state_from_strategy(
            strategy_id=BASELINE_STRATEGY_ID,
            role="j46_baseline_comparator",
            resolution=resolution,
            mechanical=baseline_mech,
            account_truth=account_truth,
        )
        fixed_state = _state_from_strategy(
            strategy_id=FIXED_R_COMPARATOR_ID,
            role="fixed_r_comparator",
            resolution=resolution,
            mechanical=fixed_mech,
            account_truth=account_truth,
        )
        fvg_state = _state_from_strategy(
            strategy_id=fvg_strategy_id,
            role="fvg_comparator",
            resolution=resolution,
            mechanical=fvg_mech,
            account_truth=account_truth,
        )

        decision_no_leak = _decision_pair_no_leak_status(pair)
        actions: list[str] = []
        limitations: list[str] = []
        states = [ob_boundary_state, baseline_state, fixed_state, fvg_state]
        for state in states:
            limitations.extend(state.get("documented_limitation_codes") or [])
            actions.extend(state.get("action_required_codes") or [])

        if not candidate_id:
            actions.append("V2B_PAIR_CANDIDATE_ID_MISSING")
        if not pair.get("source_hash"):
            limitations.append("V2B_DECISION_PAIR_SOURCE_HASH_NOT_CAPTURED")
        if not pair.get("source_symbol"):
            limitations.append("V2B_DECISION_PAIR_SOURCE_SYMBOL_NOT_CAPTURED")
        if not pair.get("trade_id"):
            limitations.append("V2B_DECISION_PAIR_TRADE_ID_NOT_CAPTURED")
        if decision_no_leak != "NO_POST_OUTCOME_LABEL_IN_DECISION_PAIR":
            actions.append(decision_no_leak)
        if not resolution:
            limitations.append("V2B_FORWARD_PAIR_RESOLUTION_ROW_NOT_AVAILABLE_YET")
        if not path:
            limitations.append("CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_V2B_PAIR")
        if not opportunity:
            limitations.append("OPPORTUNITY_CLUSTER_ROW_NOT_AVAILABLE_FOR_DUPLICATE_AWARE_COUNTING")

        resolved_pair = bool((resolution or {}).get("resolution_status") == "RESOLVED_FROM_LIVE_PATH_ROW")
        r_counted_pair = bool(ob_boundary_state.get("r_counted") and baseline_state.get("r_counted"))
        pair_lane = _pair_label_lane(ob_boundary_state, baseline_state)
        if pair_lane == "SYNTHETIC_PATH_R":
            limitations.append("PAIR_R_IS_SYNTHETIC_PATH_R_NOT_BROKER_ACTUAL_R")
        if pair_lane == "UNRESOLVED_PATH":
            limitations.append("PAIR_R_NOT_COUNTED_UNRESOLVED_PATH_OR_SOURCE_BLOCKER")

        audit_status = ACTION_REQUIRED if actions else WAITING if not resolved_pair else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
        dependency_signature = _dependency_signature(
            pair=pair,
            resolution=resolution,
            path=path,
            ltf=ltf,
            account_truth=account_truth,
            opportunity=opportunity,
            pending_audit=pending_audit,
            mechanical_rows=[v2b_mech, baseline_mech, fixed_mech, fvg_mech],
        )
        row_key = _stable_hash(SCHEMA_VERSION, candidate_id, asof, dependency_signature)
        sample_floor = pair.get("sample_floor_target_resolved_pairs") or 30
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_key": row_key,
            "source_dependency_signature": dependency_signature,
            "created_at_utc": generated_at_utc,
            "backfilled_at_utc": generated_at_utc,
            "candidate_id": candidate_id,
            "symbol": pair.get("symbol"),
            "broker_symbol": pair.get("broker_symbol"),
            "source_symbol": pair.get("source_symbol"),
            "session": pair.get("session") or pair.get("kill_zone"),
            "kill_zone": pair.get("kill_zone"),
            "side": pair.get("side"),
            "framework": pair.get("framework"),
            "decision_time_utc": pair.get("decision_time_utc"),
            "trade_id": pair.get("trade_id"),
            "source_pair_line_no": pair.get("_line_no"),
            "source_pair_created_at_utc": pair.get("created_at_utc"),
            "source_pair_path_label_status": pair.get("path_label_status"),
            "source_pair_actual_synthetic_label_lane": pair.get("actual_synthetic_label_lane"),
            "source_pair_no_leak_status": pair.get("no_leak_status"),
            "decision_pair_no_leak_status": decision_no_leak,
            "latest_resolution_row_key": (resolution or {}).get("row_key"),
            "latest_resolution_status": (resolution or {}).get("resolution_status"),
            "latest_resolution_asof_utc": (resolution or {}).get("asof_latest_candle_utc"),
            "latest_path_asof_utc": (path or {}).get("asof_latest_candle_utc"),
            "path_label": (resolution or path or {}).get("path_label"),
            "path_outcome_status": (resolution or {}).get("path_outcome_status"),
            "touched_entry": (resolution or path or {}).get("touched_entry"),
            "hit_tp1": (resolution or path or {}).get("hit_tp1"),
            "hit_sl": (resolution or path or {}).get("hit_sl"),
            "bars_elapsed": (resolution or path or {}).get("bars_elapsed"),
            "ltf_path_order_label": (ltf or {}).get("path_order_label"),
            "ltf_terminal_outcome_status": (ltf or {}).get("terminal_outcome_status"),
            "ltf_terminal_order_ambiguity": (ltf or {}).get("terminal_order_ambiguity"),
            "account_truth_status": (account_truth or {}).get("account_truth_status"),
            "actual_r_claim_allowed": (account_truth or {}).get("actual_r_claim_allowed"),
            "pending_limit_lifecycle_audit_status": (pending_audit or {}).get("pending_limit_lifecycle_audit_status"),
            "pending_limit_final_state": (pending_audit or {}).get("final_state"),
            "opportunity_id": (opportunity or {}).get("opportunity_id"),
            "opportunity_counting_status": (opportunity or {}).get("opportunity_counting_status"),
            "opportunity_duplicate_status": (opportunity or {}).get("opportunity_duplicate_status"),
            "opportunity_assignment_algorithm_version": (opportunity or {}).get("opportunity_assignment_algorithm_version"),
            "duplicate_aware_counting_status": (
                "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                if (opportunity or {}).get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                else (opportunity or {}).get("opportunity_counting_status") or "NO_OPPORTUNITY_CLUSTER_ROW"
            ),
            "resolved_pair": resolved_pair,
            "r_counted_pair": r_counted_pair,
            "actual_synthetic_label_lane": pair_lane,
            "broker_actual_r_pair_counted": pair_lane == "BROKER_ACTUAL_R" and r_counted_pair,
            "synthetic_path_r_pair_counted": pair_lane == "SYNTHETIC_PATH_R" and r_counted_pair,
            "ob_boundary_outcome": ob_boundary_state,
            "j46_baseline_outcome": baseline_state,
            "fixed_r_comparator": fixed_state,
            "fvg_comparator": fvg_state,
            "sample_floor_target_resolved_pairs": sample_floor,
            "documented_limitation_codes": sorted(set(limitations)),
            "action_required_codes": sorted(set(actions)),
            "v2b_forward_pair_resolution_audit_status": audit_status,
            "manual_backfill_status": "BACKFILLED_FROM_V2B_RESOLUTION_PATH_MECHANICAL_OPPORTUNITY_AND_ACCOUNT_ROWS",
            "no_leak_status": "POST_DECISION_V2B_RESOLUTION_AUDIT_NO_DECISION_FEATURE",
            "promotion_verdict": PROMOTION_VERDICT,
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
            "paid_fetch_attempted": False,
            "r_counting_rule": (
                "Count a V2b pair only when both the V2b OB-boundary target and the "
                "live J46/J49 baseline comparator have broker actual R or explicit "
                "synthetic path R from candidate_path_follow, candidate_ltf_path_order, "
                "or pending lifecycle truth. Same-M1 ambiguity and source-not-captured "
                "comparators are retained but excluded from R."
            ),
        }
        rows.append(row)
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("v2b_forward_pair_resolution_audit_status") or "UNKNOWN") for row in rows)
    label_lane_counts = Counter(str(row.get("actual_synthetic_label_lane") or "UNKNOWN") for row in rows)
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    session_counts = Counter(str(row.get("session") or "UNKNOWN") for row in rows)
    symbol_session_counts = Counter(
        f"{row.get('symbol') or 'UNKNOWN'}|{row.get('session') or 'UNKNOWN'}" for row in rows
    )
    limitation_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    ambiguity_count = 0
    for row in rows:
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])
        states = [
            row.get("ob_boundary_outcome") or {},
            row.get("j46_baseline_outcome") or {},
            row.get("fixed_r_comparator") or {},
            row.get("fvg_comparator") or {},
        ]
        if any(state.get("r_counting_status") == "AMBIGUOUS_EXCLUDED_FROM_R" for state in states):
            ambiguity_count += 1

    total = len(rows)
    largest_symbol_count = max(symbol_counts.values(), default=0)
    countable_unique_r = sum(
        1
        for row in rows
        if row.get("r_counted_pair") and row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    )
    sample_floor_target = max((int(row.get("sample_floor_target_resolved_pairs") or 30) for row in rows), default=30)
    return {
        "schema_version": "v2b_forward_pair_resolution_rolling_status_v1",
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_counts else "OK_WITH_DOCUMENTED_V2B_LIMITATIONS",
        "raw_v2b_pair_rows": total,
        "resolved_pair_count": sum(1 for row in rows if row.get("resolved_pair")),
        "r_counted_pair_count": sum(1 for row in rows if row.get("r_counted_pair")),
        "broker_actual_r_counted_pair_count": sum(1 for row in rows if row.get("broker_actual_r_pair_counted")),
        "synthetic_path_r_counted_pair_count": sum(1 for row in rows if row.get("synthetic_path_r_pair_counted")),
        "unresolved_path_pair_count": sum(1 for row in rows if row.get("actual_synthetic_label_lane") == "UNRESOLVED_PATH"),
        "duplicate_aware_countable_r_pair_count": countable_unique_r,
        "sample_floor_target_resolved_pairs": sample_floor_target,
        "sample_floor_progress": {
            "raw_resolved_pairs": f"{sum(1 for row in rows if row.get('resolved_pair'))}/{sample_floor_target}",
            "raw_r_counted_pairs": f"{sum(1 for row in rows if row.get('r_counted_pair'))}/{sample_floor_target}",
            "duplicate_aware_countable_r_pairs": f"{countable_unique_r}/{sample_floor_target}",
        },
        "ambiguity_count": ambiguity_count,
        "ambiguity_rate": round(ambiguity_count / total, 6) if total else 0.0,
        "symbol_counts": dict(symbol_counts),
        "session_counts": dict(session_counts),
        "symbol_session_counts": dict(symbol_session_counts),
        "largest_symbol_share": round(largest_symbol_count / total, 6) if total else 0.0,
        "label_lane_counts": dict(label_lane_counts),
        "audit_status_counts": dict(status_counts),
        "documented_limitation_counts": dict(limitation_counts),
        "action_required_counts": dict(action_counts),
        "no_leak_status": (
            "NO_DECISION_PAIR_LEAKS_DETECTED"
            if not any(row.get("decision_pair_no_leak_status") != "NO_POST_OUTCOME_LABEL_IN_DECISION_PAIR" for row in rows)
            else "ACTION_REQUIRED_DECISION_PAIR_LEAK_STATUS_PRESENT"
        ),
    }
