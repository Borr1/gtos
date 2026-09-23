"""Continuation/no-retrace shadow lane helpers.

This module is research-only. It builds append-only candidate and resolution
rows for a preregistered continuation hypothesis without changing live trading
behavior or using later outcomes as decision features.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate
from src.research_infra.m15_choch_diagnostics import (
    m15_choch_decision_diagnostic,
    path_outcome_status,
)


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
STRATEGY_ID = "CONTINUATION_NO_RETRACE_M15_FAIL_V1"
PREREGISTRATION_VERSION = "continuation_no_retrace_prereg_v1"
CANDIDATE_SCHEMA_VERSION = "continuation_no_retrace_candidate_v1"
RESOLUTION_SCHEMA_VERSION = "continuation_no_retrace_resolution_v1"

COUNTABLE_STATUS = "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(_canonical_json(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 8)


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


def _trade_record_path(root: Path, candidate: dict[str, Any]) -> Path | None:
    symbol = str(candidate.get("symbol") or "")
    decision = parse_utc(candidate.get("decision_time_utc"))
    session = str(candidate.get("session") or candidate.get("kill_zone") or "")
    if not symbol or decision is None or not session:
        return None
    name = f"{decision.date().isoformat()}_{session}_{decision:%H%M}.json"
    return root / symbol / name


def load_trade_record_for_candidate(root: Path, candidate: dict[str, Any]) -> dict[str, Any] | None:
    path = _trade_record_path(root, candidate)
    if path is None or not path.exists():
        return None
    try:
        item = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(item, dict):
        item["_source_path"] = str(path)
        return item
    return None


def decision_price_proxy_from_trade_record(record: dict[str, Any] | None) -> dict[str, Any]:
    record = record or {}
    proxy = ((record.get("shadow") or {}).get("proximity") or {}).get("current_price")
    spread = (record.get("shadow_data") or {}).get("spread_at_entry")
    source_path = record.get("_source_path")
    if proxy is None:
        return {
            "price_source_status": "DECISION_PRICE_PROXY_NOT_CAPTURED",
            "price": None,
            "source": None,
            "source_path": source_path,
            "spread_at_entry": spread,
        }
    return {
        "price_source_status": "DECISION_PRICE_PROXY_AVAILABLE_NOT_EXECUTABLE_QUOTE",
        "price": proxy,
        "source": "trade_record.shadow.proximity.current_price",
        "source_path": source_path,
        "spread_at_entry": spread,
        "promotion_eligible_price_source": False,
    }


def _check_by_name(candidate: dict[str, Any], name: str) -> dict[str, Any]:
    verification = candidate.get("verification") or {}
    checks = verification.get("checks") or []
    for check in checks:
        if isinstance(check, dict) and check.get("name") == name:
            return check
    return {}


def _geometry(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters") or {}
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    tp1 = _safe_float(params.get("take_profit_1"))
    base_r = abs(entry - stop) if entry is not None and stop is not None else None
    if side == "LONG" and None not in (entry, stop, tp1):
        valid = bool(stop < entry < tp1)  # type: ignore[operator]
    elif side == "SHORT" and None not in (entry, stop, tp1):
        valid = bool(tp1 < entry < stop)  # type: ignore[operator]
    else:
        valid = False
    return {
        "side": side,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": tp1,
        "base_r_price": _round(base_r),
        "geometry_valid": valid,
    }


def _known_hard_failures(candidate: dict[str, Any]) -> list[str]:
    hard_failures: list[str] = []
    for check in (candidate.get("verification") or {}).get("checks") or []:
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or "")
        status = str(check.get("status") or "")
        if status == "FAIL" and name != "m15_choch_exists":
            hard_failures.append(name)
    return hard_failures


def eligibility(candidate: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    diagnostic = candidate.get("m15_choch_diagnostic") or m15_choch_decision_diagnostic(
        candidate.get("verification") or {}
    )
    geometry = _geometry(candidate)
    if candidate.get("analysis_decision") != "CANDIDATE":
        reasons.append("ANALYSIS_DECISION_NOT_CANDIDATE")
    if diagnostic.get("diagnostic_status") != "M15_CHOCH_GATE_FAILED":
        reasons.append("M15_CHOCH_GATE_DID_NOT_FAIL")
    if not geometry["geometry_valid"]:
        reasons.append("INVALID_OR_MISSING_ORIGINAL_TRADE_GEOMETRY")
    hard_failures = _known_hard_failures(candidate)
    if hard_failures:
        reasons.extend(f"NON_M15_L2_HARD_FAILURE:{name}" for name in hard_failures)
    if reasons:
        status = "NOT_ELIGIBLE"
    else:
        status = "ELIGIBLE_SHADOW_ONLY"
    return {
        "eligibility_status": status,
        "eligibility_reasons": reasons or ["PASSED_PREREGISTERED_FILTERS"],
        "m15_choch_diagnostic": diagnostic,
        "original_geometry": geometry,
    }


def _distance_from_original_limit(proxy_price: float | None, geometry: dict[str, Any]) -> dict[str, Any]:
    entry = geometry.get("entry_price")
    base_r = geometry.get("base_r_price")
    side = str(geometry.get("side") or "")
    if proxy_price is None or entry is None:
        return {"status": "DECISION_PRICE_PROXY_MISSING", "distance_price": None, "distance_r": None}
    if side == "LONG":
        distance = float(proxy_price) - float(entry)
    elif side == "SHORT":
        distance = float(entry) - float(proxy_price)
    else:
        distance = None
    return {
        "status": "COMPUTED_FROM_DECISION_PRICE_PROXY",
        "distance_price": _round(distance),
        "distance_r": _round(distance / base_r) if distance is not None and base_r else None,
    }


def _entry_models(price_proxy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
            "entry_source_status": "EXACT_DECISION_ENTRY_PRICE_REQUIRED",
            "entry_price": None,
            "promotion_eligible": False,
            "reason": "Exact executable decision-time price is not captured in current candidate rows.",
        },
        {
            "entry_model_id": "CNR_E1_DECISION_PRICE_PROXY",
            "entry_source_status": price_proxy.get("price_source_status"),
            "entry_price": price_proxy.get("price"),
            "promotion_eligible": False,
            "reason": "Proxy is diagnostic-only and cannot support promotion-grade R scoring.",
        },
    ]


def build_continuation_candidate_row(
    line_no: int,
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    trade_record: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    elig = eligibility(candidate)
    if elig["eligibility_status"] != "ELIGIBLE_SHADOW_ONLY":
        return None
    proxy = decision_price_proxy_from_trade_record(trade_record)
    geometry = elig["original_geometry"]
    distance = _distance_from_original_limit(_safe_float(proxy.get("price")), geometry)
    candidate_id = str(candidate.get("candidate_id") or "")
    row_key = _stable_hash(
        CANDIDATE_SCHEMA_VERSION,
        candidate_id,
        PREREGISTRATION_VERSION,
        geometry,
        proxy,
    )
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "strategy_id": STRATEGY_ID,
        "preregistration_version": PREREGISTRATION_VERSION,
        "candidate_id": candidate_id,
        "candidate_line_no": line_no,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "kill_zone": candidate.get("kill_zone") or candidate.get("session"),
        "side": geometry.get("side"),
        "framework": candidate.get("framework"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "eligibility_status": elig["eligibility_status"],
        "eligibility_reasons": elig["eligibility_reasons"],
        "original_trade_geometry": geometry,
        "decision_price_proxy": proxy,
        "distance_from_original_limit": distance,
        "entry_models": _entry_models(proxy),
        "stop_model": {
            "stop_model_id": "CNR_S0_ORIGINAL_STRUCTURAL_SL",
            "stop_loss": geometry.get("stop_loss"),
            "source": "original_gtos_trade_parameters.stop_loss",
        },
        "target_model": {
            "target_model_id": "CNR_T0_ORIGINAL_TP1",
            "take_profit_1": geometry.get("take_profit_1"),
            "source": "original_gtos_trade_parameters.take_profit_1",
        },
        "duplicate_counting_rule": "AGGREGATE_ONLY_COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
        "no_leak_status": "DECISION_TIME_CONTINUATION_NO_RETRACE_CANDIDATE_NO_OUTCOME_FIELDS",
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


def _aggregate_counting_status(opportunity_row: dict[str, Any] | None) -> str:
    status = str((opportunity_row or {}).get("opportunity_counting_status") or "")
    if status == COUNTABLE_STATUS:
        return "COUNTABLE_PRIMARY_ONLY"
    if status:
        return f"EXCLUDED_{status}"
    return "OPPORTUNITY_COUNTING_STATUS_NOT_JOINED"


def _resolution_status(path_status: str) -> str:
    if path_status == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
        return "FAST_CONTINUATION_PATH_CONTEXT"
    if path_status == "ENTRY_TOUCHED_UNRESOLVED":
        return "RETRACE_OCCURRED_UNRESOLVED"
    if path_status == "ENTRY_TOUCHED_THEN_TP1":
        return "RETRACE_OCCURRED_ORIGINAL_LIMIT_REACHED_TP1"
    if path_status == "ENTRY_TOUCHED_THEN_SL":
        return "RETRACE_OCCURRED_ORIGINAL_LIMIT_REACHED_SL"
    return "PATH_CONTEXT_UNRESOLVED_OR_UNMAPPED"


def build_continuation_resolution_row(
    candidate_row: dict[str, Any],
    *,
    generated_at_utc: str,
    path_row: dict[str, Any] | None = None,
    opportunity_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_row = path_row or {}
    opportunity_row = opportunity_row or {}
    path_status = path_outcome_status(path_row)
    aggregate_status = _aggregate_counting_status(opportunity_row)
    source_blockers = [
        "EXACT_DECISION_ENTRY_PRICE_NOT_CAPTURED",
        "ORDERED_POST_ENTRY_M1_OR_TICK_PATH_NOT_CAPTURED",
    ]
    candidate_id = str(candidate_row.get("candidate_id") or "")
    row_key = _stable_hash(
        RESOLUTION_SCHEMA_VERSION,
        candidate_id,
        path_row.get("asof_latest_candle_utc"),
        path_status,
        opportunity_row.get("opportunity_id"),
        aggregate_status,
    )
    return {
        "schema_version": RESOLUTION_SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "strategy_id": STRATEGY_ID,
        "preregistration_version": PREREGISTRATION_VERSION,
        "candidate_id": candidate_id,
        "symbol": candidate_row.get("symbol"),
        "broker_symbol": candidate_row.get("broker_symbol"),
        "session": candidate_row.get("session") or candidate_row.get("kill_zone"),
        "side": candidate_row.get("side"),
        "framework": candidate_row.get("framework"),
        "decision_time_utc": candidate_row.get("decision_time_utc"),
        "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
        "continuation_resolution_status": _resolution_status(path_status),
        "later_path_outcome_status": path_status,
        "later_path_label": path_row.get("path_label"),
        "touched_original_limit_entry": path_row.get("touched_entry"),
        "hit_original_tp1_area": path_row.get("hit_tp1"),
        "hit_original_sl_area": path_row.get("hit_sl"),
        "path_ambiguity_status": path_row.get("path_ambiguity_status"),
        "tick_order_claim_status": path_row.get("tick_order_claim_status"),
        "first_touch_times": {
            "entry_first_touch_utc": path_row.get("entry_first_touch_utc"),
            "tp1_first_touch_utc": path_row.get("tp1_first_touch_utc"),
            "sl_first_touch_utc": path_row.get("sl_first_touch_utc"),
        },
        "opportunity_id": opportunity_row.get("opportunity_id"),
        "opportunity_counting_status": opportunity_row.get("opportunity_counting_status"),
        "opportunity_duplicate_status": opportunity_row.get("opportunity_duplicate_status"),
        "opportunity_lifecycle_state": opportunity_row.get("opportunity_lifecycle_state"),
        "aggregate_counting_status": aggregate_status,
        "decision_price_proxy": candidate_row.get("decision_price_proxy"),
        "distance_from_original_limit": candidate_row.get("distance_from_original_limit"),
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "synthetic_r": None,
        "source_blockers": source_blockers,
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "manual_backfill_status": "BACKFILLED_FROM_PREREGISTERED_CANDIDATE_PATH_AND_OPPORTUNITY_ROWS",
        "no_leak_status": "POST_DECISION_CONTINUATION_NO_RETRACE_AUDIT_NO_DECISION_FEATURE",
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


def build_continuation_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    trade_records_root: Path = Path("knowledge_base/trade_records"),
    path_rows: list[tuple[int, dict[str, Any]]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | None = None,
    decision_date_prefix: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    latest_paths = _latest_by_candidate(path_rows or [])
    latest_opportunities = _latest_by_candidate(opportunity_rows or [])
    candidates_out: list[dict[str, Any]] = []
    resolutions_out: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for line_no, candidate in candidate_rows:
        if decision_date_prefix and not str(candidate.get("decision_time_utc") or "").startswith(decision_date_prefix):
            skipped["outside_decision_date_prefix"] += 1
            continue
        trade_record = load_trade_record_for_candidate(trade_records_root, candidate)
        row = build_continuation_candidate_row(
            line_no,
            candidate,
            generated_at_utc=generated_at_utc,
            trade_record=trade_record,
        )
        if row is None:
            skipped["not_eligible"] += 1
            continue
        cid = str(row.get("candidate_id") or "")
        candidates_out.append(row)
        resolutions_out.append(
            build_continuation_resolution_row(
                row,
                generated_at_utc=generated_at_utc,
                path_row=latest_paths.get(cid),
                opportunity_row=latest_opportunities.get(cid),
            )
        )
    return candidates_out, resolutions_out, dict(skipped)


def build_report(
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    *,
    appended_candidates: int,
    appended_resolutions: int,
    skipped: dict[str, int],
    candidate_output_path: str,
    resolution_output_path: str,
) -> dict[str, Any]:
    path_counts = Counter(str(row.get("later_path_outcome_status") or "UNKNOWN") for row in resolution_rows)
    aggregate_counts = Counter(str(row.get("aggregate_counting_status") or "UNKNOWN") for row in resolution_rows)
    source_blockers: Counter[str] = Counter()
    distance_available = 0
    for row in resolution_rows:
        source_blockers.update(row.get("source_blockers") or [])
        distance = (row.get("distance_from_original_limit") or {}).get("distance_r")
        if distance is not None:
            distance_available += 1

    return {
        "schema_version": "continuation_no_retrace_audit_report_v1",
        "generated_at_utc": utc_now_iso(),
        "status": "OK_SHADOW_ONLY_SOURCE_BLOCKED_FOR_R_SCORING",
        "promotion_verdict": PROMOTION_VERDICT,
        "strategy_id": STRATEGY_ID,
        "preregistration_version": PREREGISTRATION_VERSION,
        "candidate_output_path": candidate_output_path,
        "resolution_output_path": resolution_output_path,
        "counts": {
            "eligible_candidates": len(candidate_rows),
            "candidate_rows_appended": appended_candidates,
            "resolution_rows": len(resolution_rows),
            "resolution_rows_appended": appended_resolutions,
            "distance_proxy_available": distance_available,
        },
        "skipped": dict(sorted(skipped.items())),
        "later_path_outcome_counts": dict(path_counts),
        "aggregate_counting_status_counts": dict(aggregate_counts),
        "source_blocker_counts": dict(source_blockers),
        "ambiguity_status": (
            "SHADOW_LANE_BUILT. Current rows can diagnose fast-continuation "
            "path context and duplicate-aware countability, but exact synthetic "
            "R remains source-blocked until executable decision price and "
            "ordered post-entry path data are captured."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
