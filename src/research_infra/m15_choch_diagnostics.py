"""Diagnostic helpers for m15_choch_exists L2 failures.

This module is research-only. It derives decision-time diagnostics from
already-recorded verification checks, then joins post-decision path and
opportunity evidence without changing any live gate.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "m15_choch_diagnostic_audit_v1"

PATH_LABEL_TO_OUTCOME = {
    "entry_touched_then_reached_tp1": "ENTRY_TOUCHED_THEN_TP1",
    "went_through_entry_and_continued_to_sl": "ENTRY_TOUCHED_THEN_SL",
    "continued_without_entry_touch_to_tp_area": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
    "entry_touched_tp_and_sl_m15_ambiguous": "ENTRY_TOUCHED_TP1_SL_M15_AMBIGUOUS",
    "entry_touched_unresolved": "ENTRY_TOUCHED_UNRESOLVED",
    "no_touch_stayed_above_entry": "NO_FILL_NO_TP1_REACHED_YET",
    "no_touch_stayed_below_entry": "NO_FILL_NO_TP1_REACHED_YET",
    "no_m15_bars_available": "PATH_SOURCE_INCOMPLETE",
    "missing_trade_parameters_or_prices": "PATH_SOURCE_INCOMPLETE",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _safe_get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _check_map(verification: Any) -> dict[str, dict[str, Any]]:
    checks = _safe_get(verification, "checks", []) or []
    out: dict[str, dict[str, Any]] = {}
    for check in checks:
        name = str(_safe_get(check, "name") or "")
        if name:
            out[name] = {
                "name": _safe_get(check, "name"),
                "status": _safe_get(check, "status"),
                "detail": _safe_get(check, "detail"),
                "mso_value": _safe_get(check, "mso_value"),
                "ai_value": _safe_get(check, "ai_value"),
            }
    return out


def m15_choch_decision_diagnostic(verification: Any) -> dict[str, Any]:
    """Return a decision-time explanation of the M15 CHoCH gate state.

    This is derived only from verification output already available at the
    decision timestamp. It intentionally excludes path/outcome fields.
    """

    checks = _check_map(verification)
    m15 = checks.get("m15_choch_exists") or {}
    displacement = checks.get("displacement_ratio") or {}
    blocked_by = _safe_get(verification, "blocked_by")
    m15_status = m15.get("status")

    if blocked_by == "m15_choch_exists" or m15_status == "FAIL":
        status = "M15_CHOCH_GATE_FAILED"
    elif m15_status == "PASS":
        status = "M15_CHOCH_GATE_PASSED"
    elif m15_status in {"SKIP", "WARN"}:
        status = f"M15_CHOCH_GATE_{m15_status}"
    elif m15:
        status = "M15_CHOCH_GATE_STATUS_CAPTURED"
    else:
        status = "M15_CHOCH_CHECK_NOT_CAPTURED"

    return {
        "diagnostic_status": status,
        "blocked_by": blocked_by,
        "m15_choch_check_status": m15_status,
        "m15_choch_check_detail": m15.get("detail"),
        "m15_choch_mso_value": m15.get("mso_value"),
        "m15_choch_ai_value": m15.get("ai_value"),
        "displacement_ratio_check_status": displacement.get("status"),
        "displacement_ratio_check_detail": displacement.get("detail"),
        "displacement_ratio_mso_value": displacement.get("mso_value"),
        "displacement_ratio_ai_value": displacement.get("ai_value"),
        "decision_time_only": True,
    }


def is_m15_choch_failure(candidate: dict[str, Any]) -> bool:
    diagnostic = m15_choch_decision_diagnostic(candidate.get("verification") or {})
    return diagnostic.get("diagnostic_status") == "M15_CHOCH_GATE_FAILED"


def path_outcome_status(path_row: dict[str, Any] | None) -> str:
    if not path_row:
        return "WAITING_FOR_PATH_ROW"
    label = str(path_row.get("path_label") or "")
    if label in PATH_LABEL_TO_OUTCOME:
        return PATH_LABEL_TO_OUTCOME[label]
    if not label:
        return "PATH_LABEL_NOT_CAPTURED"
    return "PATH_LABEL_OBSERVED_UNMAPPED"


def _gate_interpretation(path_status: str) -> str:
    if path_status == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
        return "FAST_CONTINUATION_RESEARCH_DOOR_NOT_GATE_CHANGE"
    if path_status == "ENTRY_TOUCHED_THEN_TP1":
        return "M15_GATE_FAILED_BUT_ORIGINAL_LIMIT_PATH_REACHED_TP1_REVIEW_ONLY"
    if path_status == "ENTRY_TOUCHED_THEN_SL":
        return "M15_GATE_FAILED_AND_ORIGINAL_LIMIT_PATH_LOST"
    if path_status == "ENTRY_TOUCHED_TP1_SL_M15_AMBIGUOUS":
        return "M15_GATE_FAILED_WITH_M15_PATH_ORDER_AMBIGUOUS"
    if path_status in {"WAITING_FOR_PATH_ROW", "PATH_SOURCE_INCOMPLETE"}:
        return "M15_GATE_FAILURE_AWAITS_PATH_EVIDENCE"
    return "M15_GATE_FAILURE_OBSERVATIONAL_ONLY"


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def build_m15_choch_diagnostic_row(
    line_no: int,
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    path_row: dict[str, Any] | None = None,
    opportunity_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    path_row = path_row or {}
    opportunity_row = opportunity_row or {}
    decision_diagnostic = m15_choch_decision_diagnostic(candidate.get("verification") or {})
    path_status = path_outcome_status(path_row)
    gate_interpretation = _gate_interpretation(path_status)
    asof = str(path_row.get("asof_latest_candle_utc") or "")
    row_key = _stable_hash(
        SCHEMA_VERSION,
        candidate_id,
        asof,
        decision_diagnostic,
        path_row.get("path_label"),
        opportunity_row.get("opportunity_id"),
        opportunity_row.get("opportunity_lifecycle_state"),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "candidate_line_no": line_no,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "kill_zone": candidate.get("kill_zone") or candidate.get("session"),
        "side": candidate.get("side") or (candidate.get("trade_parameters") or {}).get("direction"),
        "framework": candidate.get("framework"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "analysis_decision": candidate.get("analysis_decision"),
        "trade_parameters": candidate.get("trade_parameters") or {},
        "m15_choch_decision_diagnostic": decision_diagnostic,
        "post_decision_join_status": (
            "JOINED_LATEST_CANDIDATE_PATH" if path_row else "PATH_ROW_NOT_AVAILABLE"
        ),
        "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
        "later_path_label": path_row.get("path_label"),
        "later_path_outcome_status": path_status,
        "touched_entry": path_row.get("touched_entry"),
        "hit_tp1": path_row.get("hit_tp1"),
        "hit_sl": path_row.get("hit_sl"),
        "first_touch_times": {
            "entry_first_touch_utc": path_row.get("entry_first_touch_utc"),
            "tp1_first_touch_utc": path_row.get("tp1_first_touch_utc"),
            "sl_first_touch_utc": path_row.get("sl_first_touch_utc"),
        },
        "path_ambiguity_status": path_row.get("path_ambiguity_status"),
        "tick_order_claim_status": path_row.get("tick_order_claim_status"),
        "source_ohlc_range": path_row.get("source_ohlc_range"),
        "opportunity_join_status": (
            "JOINED_LIVE_OPPORTUNITY_CLUSTER" if opportunity_row else "OPPORTUNITY_CLUSTER_NOT_AVAILABLE"
        ),
        "opportunity_id": opportunity_row.get("opportunity_id"),
        "opportunity_lifecycle_state": opportunity_row.get("opportunity_lifecycle_state"),
        "opportunity_counting_status": opportunity_row.get("opportunity_counting_status"),
        "opportunity_duplicate_status": opportunity_row.get("opportunity_duplicate_status"),
        "opportunity_candidate_count": opportunity_row.get("opportunity_candidate_count"),
        "same_symbol_overlap_status": opportunity_row.get("same_symbol_overlap_status"),
        "gate_interpretation_status": gate_interpretation,
        "m15_choch_audit_status": (
            "M15_CHOCH_FAILURE_JOINED_TO_PATH"
            if path_row
            else "M15_CHOCH_FAILURE_WAITING_FOR_PATH"
        ),
        "manual_backfill_status": "BACKFILLED_FROM_CANDIDATE_PATH_AND_OPPORTUNITY_ROWS",
        "no_leak_status": "POST_DECISION_M15_CHOCH_DIAGNOSTIC_AUDIT_NO_DECISION_FEATURE",
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


def build_m15_choch_diagnostic_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    path_rows: list[tuple[int, dict[str, Any]]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    latest_paths = _latest_by_candidate(path_rows or [])
    latest_opportunities = _latest_by_candidate(opportunity_rows or [])
    out: list[dict[str, Any]] = []
    for line_no, candidate in candidate_rows:
        if decision_date_prefix and not str(candidate.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        if not is_m15_choch_failure(candidate):
            continue
        cid = str(candidate.get("candidate_id") or "")
        out.append(
            build_m15_choch_diagnostic_row(
                line_no,
                candidate,
                generated_at_utc=generated_at_utc,
                path_row=latest_paths.get(cid),
                opportunity_row=latest_opportunities.get(cid),
            )
        )
    return out


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: str) -> dict[str, Any]:
    path_counts = Counter(str(row.get("later_path_outcome_status") or "UNKNOWN") for row in rows)
    interpretation_counts = Counter(str(row.get("gate_interpretation_status") or "UNKNOWN") for row in rows)
    opportunity_counts = Counter(str(row.get("opportunity_counting_status") or "UNKNOWN") for row in rows)
    joined_count = sum(1 for row in rows if row.get("post_decision_join_status") == "JOINED_LATEST_CANDIDATE_PATH")
    continuation_examples = [
        {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "later_path_outcome_status": row.get("later_path_outcome_status"),
            "opportunity_counting_status": row.get("opportunity_counting_status"),
        }
        for row in rows
        if row.get("later_path_outcome_status") == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    ][:25]

    return {
        "schema_version": "m15_choch_diagnostic_audit_report_v1",
        "generated_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "OK_DIAGNOSTIC_ONLY_NO_GATE_CHANGE",
        "audit_log_path": output_path,
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "m15_choch_failures_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "joined_to_latest_path": joined_count,
            "waiting_for_path": len(rows) - joined_count,
        },
        "later_path_outcome_counts": dict(path_counts),
        "gate_interpretation_counts": dict(interpretation_counts),
        "opportunity_counting_status_counts": dict(opportunity_counts),
        "continuation_no_retrace_examples": continuation_examples,
        "ambiguity_status": (
            "DIAGNOSTICS_EXPANDED_ONLY. This audit can identify fast-continuation "
            "and original-limit path outcomes after an m15_choch_exists failure, "
            "but it does not answer promotion or gate-loosening questions."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
