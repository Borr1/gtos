"""J46-J49 exit-comparator audit helpers for LTO-016.

This module is research/tooling only. It joins existing J46/J49 filled-trade
shadow outcomes to broker account-history truth, and separately documents
candidate/path rows that are no-fill or synthetic-path context. It does not
call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "j46_j49_exit_comparator_audit_v1"
CLASSIFIER_VERSION = "j46_j49_exit_comparator_audit_classifier_v1"
FILLED_JOINED = "J46_J49_FILLED_ACCOUNT_HISTORY_JOINED"
FILLED_MISSING = "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING"
CANDIDATE_NO_FILL_CONTEXT = "J46_J49_CANDIDATE_NO_FILL_CONTEXT"
CANDIDATE_PATH_SYNTHETIC_ONLY = "J46_J49_CANDIDATE_PATH_SYNTHETIC_ONLY"
ACTION_REQUIRED = "J46_J49_EXIT_COMPARATOR_ACTION_REQUIRED"

ACTUAL_R_TOLERANCE = 0.0002


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line_no), row) for line_no, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("timestamp_logged"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("asof_latest_candle_utc"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_key(rows: list[tuple[int, dict[str, Any]]], key: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        value = str(row.get(key) or "").strip()
        if not value:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        item_key = (_clock(item), line_no)
        previous = latest.get(value)
        previous_key = (
            _clock(previous or {}),
            int((previous or {}).get("_line_no") or 0),
        )
        if item_key >= previous_key:
            latest[value] = item
    return latest


def _latest_broker_by_fill_id(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        fill_id = str(row.get("fill_id") or row.get("trade_id") or "").strip()
        if not fill_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        priority = 1 if item.get("actual_r_claim_allowed") is True and item.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED" else 0
        item_key = (priority, _clock(item), line_no)
        previous = latest.get(fill_id)
        previous_priority = (
            1
            if previous
            and previous.get("actual_r_claim_allowed") is True
            and previous.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
            else 0
        )
        previous_key = (
            previous_priority,
            _clock(previous or {}),
            int((previous or {}).get("_line_no") or 0),
        )
        if item_key >= previous_key:
            latest[fill_id] = item
    return latest


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _nested_actual_r(row: dict[str, Any]) -> float | None:
    actual_close = row.get("actual_close")
    if isinstance(actual_close, dict):
        return _float_or_none(actual_close.get("realized_R"))
    return None


def _hypothetical_old_r(row: dict[str, Any]) -> float | None:
    hypothetical = row.get("hypothetical_old")
    if isinstance(hypothetical, dict):
        return _float_or_none(hypothetical.get("hypothetical_R"))
    return None


def _hypothetical_exit_reason(row: dict[str, Any]) -> str | None:
    hypothetical = row.get("hypothetical_old")
    if isinstance(hypothetical, dict):
        return hypothetical.get("exit_reason")
    return None


def _actual_exit_reason(row: dict[str, Any]) -> str | None:
    actual_close = row.get("actual_close")
    if isinstance(actual_close, dict):
        return actual_close.get("exit_reason")
    return None


def _source_links_for_broker(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    links = row.get("source_links")
    return links if isinstance(links, dict) else {}


def _candidate_path_status(path_row: dict[str, Any] | None) -> str:
    if not path_row:
        return "NO_CANDIDATE_PATH_ROW"
    if path_row.get("touched_entry") is True:
        return CANDIDATE_PATH_SYNTHETIC_ONLY
    return CANDIDATE_NO_FILL_CONTEXT


def _ml_feature_role(row_type: str) -> str:
    if row_type == "filled_exit_comparator":
        return "ML_TARGET_LABEL_QUALITY_INPUT_AFTER_TARGET_REFRESH"
    return "ML_SAMPLE_ELIGIBILITY_AND_NO_FILL_CONTEXT_INPUT"


def _ml_label_eligibility(status: str, actual_r_allowed: bool) -> str:
    if status == FILLED_JOINED and actual_r_allowed:
        return "ELIGIBLE_ACCOUNT_HISTORY_REALIZED_LABEL_AFTER_TARGET_REFRESH"
    if status == CANDIDATE_NO_FILL_CONTEXT:
        return "NO_ACTUAL_R_LABEL_NO_FILL_CONTEXT"
    if status == CANDIDATE_PATH_SYNTHETIC_ONLY:
        return "SYNTHETIC_PATH_LABEL_ONLY_NOT_ACCOUNT_HISTORY_ACTUAL_R"
    return "NOT_ELIGIBLE_ACTION_REQUIRED_OR_MISSING_ACCOUNT_HISTORY"


def build_filled_exit_comparator_row(
    outcome: dict[str, Any],
    *,
    broker_row: dict[str, Any] | None = None,
    path_row: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    fill_id = str(outcome.get("fill_id") or "")
    j46_realized_r = _nested_actual_r(outcome)
    broker_actual_r = _float_or_none((broker_row or {}).get("broker_actual_r"))
    broker_is_account_history = (
        broker_row is not None
        and broker_row.get("actual_r_claim_allowed") is True
        and broker_row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    )
    action_required: list[str] = []
    documented_limitations: list[str] = []
    if not broker_is_account_history:
        action_required.append("FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT")
    if broker_is_account_history and j46_realized_r is not None and broker_actual_r is not None:
        delta_vs_broker = round(float(j46_realized_r) - float(broker_actual_r), 6)
        if abs(delta_vs_broker) > ACTUAL_R_TOLERANCE:
            action_required.append("J46_REALIZED_R_MISMATCH_BROKER_HISTORY")
    else:
        delta_vs_broker = None
    if not path_row:
        documented_limitations.append("NO_CANDIDATE_PATH_JOIN_FOR_LEGACY_FILL")
    broker_links = _source_links_for_broker(broker_row)
    if "J46_REALIZED_R_MISMATCH_BROKER_HISTORY" in action_required:
        status = ACTION_REQUIRED
    elif broker_is_account_history:
        status = FILLED_JOINED
    else:
        status = FILLED_MISSING
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        "filled_exit_comparator",
        fill_id,
        outcome.get("timestamp_logged"),
        outcome.get("policy_version"),
        outcome.get("delta_r"),
        broker_row.get("row_key") if broker_row else "",
        broker_row.get("source_dependency_signature") if broker_row else "",
        path_row.get("created_at_utc") if path_row else "",
        path_row.get("asof_latest_candle_utc") if path_row else "",
        path_row.get("path_label") if path_row else "",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("j46_j49_exit_comparator_audit", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-016",
        "follow_id": "LIVE-FOLLOW-013",
        "row_type": "filled_exit_comparator",
        "j46_j49_exit_comparator_status": status,
        "fill_id": fill_id,
        "trade_id": outcome.get("fill_id"),
        "candidate_id": path_row.get("candidate_id") if path_row else broker_row.get("candidate_id") if broker_row else None,
        "symbol": outcome.get("instrument") or (broker_row or {}).get("symbol"),
        "broker_symbol": (broker_row or {}).get("broker_symbol") or outcome.get("instrument"),
        "side": outcome.get("direction") or (path_row or {}).get("side"),
        "framework": (path_row or {}).get("framework"),
        "decision_time_utc": (broker_row or {}).get("decision_time_utc") or outcome.get("entry_time"),
        "entry_time_utc": outcome.get("entry_time"),
        "exit_time_utc": (outcome.get("actual_close") or {}).get("exit_time") if isinstance(outcome.get("actual_close"), dict) else outcome.get("exit_time"),
        "policy_version": outcome.get("policy_version"),
        "actual_exit_reason": _actual_exit_reason(outcome),
        "hypothetical_old_exit_reason": _hypothetical_exit_reason(outcome),
        "j46_actual_close_realized_r": j46_realized_r,
        "hypothetical_old_r": _hypothetical_old_r(outcome),
        "delta_r": _float_or_none(outcome.get("delta_r")),
        "shadow_better": outcome.get("shadow_better"),
        "broker_actual_r": broker_actual_r if broker_is_account_history else None,
        "broker_actual_r_delta_vs_j46": delta_vs_broker,
        "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        "broker_actual_r_evidence_class": (broker_row or {}).get("accounting_evidence_class"),
        "broker_actual_r_truth_lane": (broker_row or {}).get("truth_lane"),
        "broker_actual_r_claim_allowed": bool(broker_is_account_history),
        "actual_r_claim_allowed": bool(broker_is_account_history),
        "path_label": (path_row or {}).get("path_label"),
        "touched_entry": (path_row or {}).get("touched_entry"),
        "hit_tp1": (path_row or {}).get("hit_tp1"),
        "hit_sl": (path_row or {}).get("hit_sl"),
        "path_ambiguity_status": (path_row or {}).get("path_ambiguity_status"),
        "path_context_status": "PATH_JOINED" if path_row else "NO_CANDIDATE_PATH_JOIN_FOR_LEGACY_FILL",
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "source_links": {
            "j46_shadow_outcome_fill_id": fill_id,
            "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
            "mt5_export_deal_id": broker_links.get("mt5_export_deal_id"),
            "mt5_export_order_id": broker_links.get("mt5_export_order_id"),
            "mt5_export_position_id": broker_links.get("mt5_export_position_id"),
        },
        "claim_boundary": (
            "Actual-R is allowed only when the filled J46/J49 comparator joins "
            "ACCOUNT_HISTORY_REALIZED broker audit evidence. Candidate/path-only rows stay synthetic or no-fill context."
        ),
        "ml_feature_role": _ml_feature_role("filled_exit_comparator"),
        "ml_label_eligibility": _ml_label_eligibility(status, broker_is_account_history),
        "ml_no_leak_boundary": "POST_DECISION_LABEL_QUALITY_AUDIT_NOT_DECISION_FEATURE",
        "evidence_class": "ACCOUNT_HISTORY_REALIZED" if broker_is_account_history else "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
        "no_leak_status": "POST_DECISION_EXIT_COMPARATOR_AUDIT_NOT_DECISION_FEATURE",
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


def build_candidate_context_row(
    candidate: dict[str, Any],
    *,
    path_row: dict[str, Any] | None = None,
    broker_row: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    candidate_id = str(candidate.get("candidate_id") or "")
    status = _candidate_path_status(path_row)
    action_required: list[str] = []
    documented_limitations: list[str] = []
    if not path_row:
        documented_limitations.append("NO_CANDIDATE_PATH_ROW_FOR_COMPARATOR_CONTEXT")
    if broker_row and broker_row.get("actual_r_claim_allowed") is True:
        action_required.append("CANDIDATE_CONTEXT_ROW_HAS_ACCOUNT_HISTORY_ACTUAL_R")
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        "candidate_context",
        candidate_id,
        candidate.get("created_at_utc"),
        candidate.get("final_outcome_at_log"),
        candidate.get("trade_id"),
        path_row.get("created_at_utc") if path_row else "",
        path_row.get("asof_latest_candle_utc") if path_row else "",
        path_row.get("path_label") if path_row else "",
        path_row.get("touched_entry") if path_row else "",
        broker_row.get("row_key") if broker_row else "",
    )
    final_status = ACTION_REQUIRED if action_required else status
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("j46_j49_exit_comparator_audit", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-016",
        "follow_id": "LIVE-FOLLOW-013",
        "row_type": "candidate_context",
        "j46_j49_exit_comparator_status": final_status,
        "candidate_id": candidate_id,
        "fill_id": None,
        "trade_id": candidate.get("trade_id") or (path_row or {}).get("trade_id"),
        "symbol": candidate.get("symbol") or (path_row or {}).get("symbol"),
        "broker_symbol": candidate.get("broker_symbol") or (path_row or {}).get("broker_symbol"),
        "side": candidate.get("side") or (path_row or {}).get("side"),
        "framework": candidate.get("framework") or (path_row or {}).get("framework"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "decision_time_utc": candidate.get("decision_time_utc") or (path_row or {}).get("decision_time_utc"),
        "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "path_label": (path_row or {}).get("path_label"),
        "touched_entry": (path_row or {}).get("touched_entry"),
        "hit_tp1": (path_row or {}).get("hit_tp1"),
        "hit_sl": (path_row or {}).get("hit_sl"),
        "path_ambiguity_status": (path_row or {}).get("path_ambiguity_status"),
        "path_context_status": "PATH_JOINED" if path_row else "NO_CANDIDATE_PATH_ROW",
        "j46_actual_close_realized_r": None,
        "hypothetical_old_r": None,
        "delta_r": None,
        "shadow_better": None,
        "broker_actual_r": None,
        "broker_actual_r_delta_vs_j46": None,
        "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        "broker_actual_r_evidence_class": (broker_row or {}).get("accounting_evidence_class"),
        "broker_actual_r_truth_lane": (broker_row or {}).get("truth_lane"),
        "broker_actual_r_claim_allowed": False,
        "actual_r_claim_allowed": False,
        "synthetic_path_available": bool(path_row),
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "source_links": {
            "candidate_created_at_utc": candidate.get("created_at_utc"),
            "path_created_at_utc": (path_row or {}).get("created_at_utc"),
            "path_asof_latest_candle_utc": (path_row or {}).get("asof_latest_candle_utc"),
            "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        },
        "claim_boundary": (
            "This candidate-context row prevents fill-only J46/J49 rows from being mistaken for the full candidate set. "
            "It carries no broker actual-R claim."
        ),
        "ml_feature_role": _ml_feature_role("candidate_context"),
        "ml_label_eligibility": _ml_label_eligibility(status, False),
        "ml_no_leak_boundary": "POST_DECISION_CONTEXT_AUDIT_NOT_DECISION_FEATURE",
        "evidence_class": "SYNTHETIC_PATH_R" if status == CANDIDATE_PATH_SYNTHETIC_ONLY else "FORWARD_SHADOW_PATH_CONTEXT",
        "no_leak_status": "POST_DECISION_EXIT_COMPARATOR_AUDIT_NOT_DECISION_FEATURE",
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


def build_j46_j49_exit_comparator_audit_rows(
    j46_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    broker_by_fill = _latest_broker_by_fill_id(_rows_with_lines(broker_rows))
    broker_by_candidate = _latest_by_key(_rows_with_lines(broker_rows), "candidate_id")
    candidate_by_id = _latest_by_key(_rows_with_lines(candidate_rows), "candidate_id")
    path_by_candidate = _latest_by_key(_rows_with_lines(path_rows), "candidate_id")

    rows: list[dict[str, Any]] = []
    for _, outcome in _rows_with_lines(j46_rows):
        fill_id = str(outcome.get("fill_id") or "")
        if not fill_id:
            continue
        broker_row = broker_by_fill.get(fill_id)
        candidate_id = str((broker_row or {}).get("candidate_id") or "")
        path_row = path_by_candidate.get(candidate_id) if candidate_id else None
        rows.append(
            build_filled_exit_comparator_row(
                outcome,
                broker_row=broker_row,
                path_row=path_row,
                generated_at_utc=generated_at_utc,
            )
        )

    represented_candidate_ids = {
        str(row.get("candidate_id") or "")
        for row in rows
        if row.get("candidate_id")
    }
    for candidate_id, candidate in sorted(candidate_by_id.items()):
        if not candidate_id or candidate_id in represented_candidate_ids:
            continue
        rows.append(
            build_candidate_context_row(
                candidate,
                path_row=path_by_candidate.get(candidate_id),
                broker_row=broker_by_candidate.get(candidate_id),
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("j46_j49_exit_comparator_status") or "UNKNOWN") for row in rows)
    row_type_counts = Counter(str(row.get("row_type") or "UNKNOWN") for row in rows)
    ml_label_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in rows)
    action_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    for row in rows:
        action_counts.update(row.get("action_required_codes") or [])
        limitation_counts.update(row.get("documented_limitation_codes") or [])
    return {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "row_type_counts": dict(row_type_counts),
        "ml_label_eligibility_counts": dict(ml_label_counts),
        "actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "candidate_context_rows": row_type_counts.get("candidate_context", 0),
        "filled_comparator_rows": row_type_counts.get("filled_exit_comparator", 0),
        "action_required_code_counts": dict(action_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
    }
