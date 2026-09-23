"""XAGUSD late-NY fresh-OB lane tracking.

This is research-only bookkeeping. It labels XAGUSD late-NY OB signatures so
fresh structural resets are not merged with older duplicate OB clusters.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, time, timezone
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate
from src.research_infra.m15_choch_diagnostics import path_outcome_status


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "xagusd_fresh_ob_late_ny_v1"
REPORT_SCHEMA_VERSION = "xagusd_fresh_ob_late_ny_report_v1"


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


def _check_detail(candidate: dict[str, Any], check_name: str) -> str | None:
    for check in (candidate.get("verification") or {}).get("checks") or []:
        if isinstance(check, dict) and check.get("name") == check_name:
            return check.get("detail")
    return None


def extract_h1_ob_zone(candidate: dict[str, Any]) -> dict[str, Any]:
    detail = _check_detail(candidate, "h1_poi_exists") or ""
    match = re.search(r"H1 OB found at\s+([\d.]+)-([\d.]+)", detail)
    if not match:
        return {
            "zone_source_status": "H1_OB_ZONE_NOT_PARSED",
            "zone_low": None,
            "zone_high": None,
            "raw_detail": detail or None,
        }
    left = _safe_float(match.group(1))
    right = _safe_float(match.group(2))
    values = [value for value in (left, right) if value is not None]
    if len(values) != 2:
        return {
            "zone_source_status": "H1_OB_ZONE_PARSE_FAILED",
            "zone_low": None,
            "zone_high": None,
            "raw_detail": detail,
        }
    return {
        "zone_source_status": "PARSED_FROM_H1_POI_CHECK",
        "zone_low": min(values),
        "zone_high": max(values),
        "raw_detail": detail,
    }


def fresh_ob_signature(candidate: dict[str, Any]) -> str:
    params = candidate.get("trade_parameters") or {}
    zone = extract_h1_ob_zone(candidate)
    symbol = str(candidate.get("symbol") or "").upper()
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    framework = str(candidate.get("framework") or "").lower()
    entry = _safe_float(params.get("entry_price"))
    zone_low = zone.get("zone_low")
    zone_high = zone.get("zone_high")
    return (
        f"{symbol}|{side}|{framework}|entry={entry}|"
        f"zone={zone_low}-{zone_high}"
    )


def _in_late_ny(candidate: dict[str, Any], *, start: time = time(16, 0), end: time = time(17, 0)) -> bool:
    ts = parse_utc(candidate.get("decision_time_utc"))
    if ts is None:
        return False
    session = str(candidate.get("session") or candidate.get("kill_zone") or "").lower()
    if session != "ny":
        return False
    current = ts.time().replace(tzinfo=None)
    return start <= current <= end


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def first_seen_by_signature(candidate_rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    first: dict[str, dict[str, Any]] = {}
    for line_no, row in candidate_rows:
        if str(row.get("symbol") or "").upper() != "XAGUSD":
            continue
        if str(row.get("framework") or "").lower() != "ob_retest":
            continue
        sig = fresh_ob_signature(row)
        ts = parse_utc(row.get("decision_time_utc")) or datetime.max.replace(tzinfo=timezone.utc)
        prior_ts = parse_utc((first.get(sig) or {}).get("decision_time_utc")) or datetime.max.replace(tzinfo=timezone.utc)
        if ts < prior_ts:
            first[sig] = {
                "candidate_id": row.get("candidate_id"),
                "decision_time_utc": row.get("decision_time_utc"),
                "line_no": line_no,
            }
    return first


def _fresh_status(candidate: dict[str, Any], first_seen: dict[str, Any]) -> str:
    cid = str(candidate.get("candidate_id") or "")
    if not first_seen:
        return "FRESH_OB_SIGNATURE_SOURCE_MISSING"
    if first_seen.get("candidate_id") == cid:
        return "FRESH_OB_LATE_NY_NEW_SIGNATURE"
    first_ts = parse_utc(first_seen.get("decision_time_utc"))
    decision_ts = parse_utc(candidate.get("decision_time_utc"))
    if first_ts and decision_ts and first_ts.date() == decision_ts.date() and first_ts.hour >= 16:
        return "FRESH_OB_LATE_NY_DUPLICATE_SIGNATURE"
    return "OLD_OB_DUPLICATE_CARRYOVER"


def _near_close_status(path_row: dict[str, Any]) -> str:
    path_status = path_outcome_status(path_row)
    if path_status == "ENTRY_TOUCHED_UNRESOLVED":
        return "NEAR_CLOSE_ENTRY_TOUCHED_UNRESOLVED_DO_NOT_SCORE"
    if path_status == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
        return "NO_RETRACE_CONTINUATION_CONTEXT_NOT_FRESH_OB_SCORE"
    return "PATH_STATUS_NOT_LATE_CLOSE_UNRESOLVED"


def build_fresh_ob_row(
    line_no: int,
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
    first_seen: dict[str, Any],
    path_row: dict[str, Any] | None = None,
    opportunity_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path_row = path_row or {}
    opportunity_row = opportunity_row or {}
    zone = extract_h1_ob_zone(candidate)
    signature = fresh_ob_signature(candidate)
    first = first_seen.get(signature) or {}
    path_status = path_outcome_status(path_row)
    row_key = _stable_hash(
        SCHEMA_VERSION,
        candidate.get("candidate_id"),
        signature,
        path_row.get("asof_latest_candle_utc"),
        opportunity_row.get("opportunity_id"),
        opportunity_row.get("opportunity_counting_status"),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_line_no": line_no,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "side": candidate.get("side") or (candidate.get("trade_parameters") or {}).get("direction"),
        "framework": candidate.get("framework"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "fresh_ob_signature": signature,
        "h1_ob_zone": zone,
        "signature_first_seen_candidate_id": first.get("candidate_id"),
        "signature_first_seen_utc": first.get("decision_time_utc"),
        "fresh_ob_late_ny_status": _fresh_status(candidate, first),
        "trade_parameters": candidate.get("trade_parameters") or {},
        "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
        "path_label": path_row.get("path_label"),
        "path_outcome_status": path_status,
        "touched_entry": path_row.get("touched_entry"),
        "hit_tp1": path_row.get("hit_tp1"),
        "hit_sl": path_row.get("hit_sl"),
        "near_close_resolution_status": _near_close_status(path_row),
        "opportunity_id": opportunity_row.get("opportunity_id"),
        "opportunity_first_candidate_id": opportunity_row.get("opportunity_first_candidate_id"),
        "opportunity_lifecycle_state": opportunity_row.get("opportunity_lifecycle_state"),
        "opportunity_counting_status": opportunity_row.get("opportunity_counting_status"),
        "opportunity_duplicate_status": opportunity_row.get("opportunity_duplicate_status"),
        "same_symbol_overlap_status": opportunity_row.get("same_symbol_overlap_status"),
        "tracking_status": "TRACK_FRESH_OB_LATE_NY_NO_OUTCOME_CLAIM",
        "manual_backfill_status": "BACKFILLED_FROM_CANDIDATE_PATH_AND_OPPORTUNITY_ROWS",
        "no_leak_status": "POST_DECISION_XAGUSD_FRESH_OB_LATE_NY_AUDIT_NO_DECISION_FEATURE",
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


def build_fresh_ob_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    path_rows: list[tuple[int, dict[str, Any]]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    first_seen = first_seen_by_signature(candidate_rows)
    latest_paths = _latest_by_candidate(path_rows or [])
    latest_opportunities = _latest_by_candidate(opportunity_rows or [])
    out: list[dict[str, Any]] = []
    for line_no, candidate in candidate_rows:
        if decision_date_prefix and not str(candidate.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        if str(candidate.get("symbol") or "").upper() != "XAGUSD":
            continue
        if str(candidate.get("framework") or "").lower() != "ob_retest":
            continue
        if not _in_late_ny(candidate):
            continue
        cid = str(candidate.get("candidate_id") or "")
        out.append(
            build_fresh_ob_row(
                line_no,
                candidate,
                generated_at_utc=generated_at_utc,
                first_seen=first_seen,
                path_row=latest_paths.get(cid),
                opportunity_row=latest_opportunities.get(cid),
            )
        )
    return out


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: str) -> dict[str, Any]:
    status_counts = Counter(str(row.get("fresh_ob_late_ny_status") or "UNKNOWN") for row in rows)
    path_counts = Counter(str(row.get("path_outcome_status") or "UNKNOWN") for row in rows)
    near_close_counts = Counter(str(row.get("near_close_resolution_status") or "UNKNOWN") for row in rows)
    opportunity_counts = Counter(str(row.get("opportunity_counting_status") or "UNKNOWN") for row in rows)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": utc_now_iso(),
        "status": "OK_FRESH_OB_LATE_NY_TRACKED_NO_OUTCOME_CLAIM",
        "promotion_verdict": PROMOTION_VERDICT,
        "output_path": output_path,
        "counts": {
            "rows_built": len(rows),
            "rows_appended": len(appended_rows),
        },
        "fresh_ob_late_ny_status_counts": dict(status_counts),
        "path_outcome_status_counts": dict(path_counts),
        "near_close_resolution_status_counts": dict(near_close_counts),
        "opportunity_counting_status_counts": dict(opportunity_counts),
        "ambiguity_status": (
            "TRACKED_ONLY. The 16:30 XAGUSD newer-OB signature is separated "
            "from the older 75.471 duplicate cluster, but entry-touched "
            "near-close rows remain unresolved and unscored."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
