"""Regime/decay outcome join helpers for LTO-018.

This module joins decision-time regime rows and OB-continuation decay rows to
candidate and filled-trade outcome context. It is research/tooling only: no
orders, no AI calls, no canaries, no paid data calls, and no live decision
impact.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "regime_decay_outcome_join_v1"
CLASSIFIER_VERSION = "regime_decay_outcome_join_classifier_v1"

COMPLETE = "REGIME_DECAY_CONTEXT_JOINED"
REGIME_MISSING = "REGIME_JOIN_MISSING_DECAY_CONTEXT_DOCUMENTED"
DECAY_MISSING = "DECAY_JOIN_MISSING_REGIME_CONTEXT_DOCUMENTED"
ACTION_REQUIRED = "REGIME_DECAY_CONTEXT_ACTION_REQUIRED"

SAME_CLOSE_GRACE_SECONDS = 90
MAX_REGIME_AGE_SECONDS = 6 * 60 * 60

SYMBOL_TO_OB_SCOPE = {
    "US30": "US30_cash",
    "US30_cash": "US30_cash",
}


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
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("timestamp_logged"))
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
        previous_key = (_clock(previous or {}), int((previous or {}).get("_line_no") or 0))
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
        priority = 1 if _broker_actual_allowed(item) else 0
        item_key = (priority, _clock(item), line_no)
        previous = latest.get(fill_id)
        previous_priority = 1 if _broker_actual_allowed(previous) else 0
        previous_key = (previous_priority, _clock(previous or {}), int((previous or {}).get("_line_no") or 0))
        if item_key >= previous_key:
            latest[fill_id] = item
    return latest


def _canonical_symbol(raw: Any) -> str:
    return str(raw or "").strip()


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_from_csv(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def _candidate_observable_until(row: dict[str, Any], decision_dt: datetime) -> datetime:
    created_dt = parse_utc(row.get("created_at_utc"))
    same_close_limit = decision_dt + timedelta(seconds=SAME_CLOSE_GRACE_SECONDS)
    if created_dt is None:
        return same_close_limit
    return min(created_dt, same_close_limit)


def select_asof_regime(
    *,
    symbol: str,
    decision_time_utc: Any,
    source_row: dict[str, Any],
    regime_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(decision_time_utc)
    if decision_dt is None:
        return {
            "join_status": "REGIME_JOIN_MISSING_DECISION_TIME_UNPARSEABLE",
            "row": None,
            "offset_seconds": None,
            "age_seconds": None,
        }
    observable_until = _candidate_observable_until(source_row, decision_dt)
    best: tuple[float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(regime_rows):
        if _canonical_symbol(row.get("symbol")) != symbol:
            continue
        ts = parse_utc(row.get("ts"))
        if ts is None:
            continue
        if ts > observable_until:
            continue
        if ts > decision_dt + timedelta(seconds=SAME_CLOSE_GRACE_SECONDS):
            continue
        if decision_dt - ts > timedelta(seconds=MAX_REGIME_AGE_SECONDS):
            continue
        distance = abs((ts - decision_dt).total_seconds())
        item = (distance, line_no, row, ts)
        if best is None or item[0] < best[0] or (item[0] == best[0] and item[1] > best[1]):
            best = item
    if best is None:
        return {
            "join_status": "REGIME_JOIN_MISSING_WITHIN_ASOF_WINDOW",
            "row": None,
            "offset_seconds": None,
            "age_seconds": None,
        }
    _, _, row, ts = best
    offset = int((ts - decision_dt).total_seconds())
    return {
        "join_status": "REGIME_ASOF_OR_SAME_CLOSE_JOINED",
        "row": row,
        "offset_seconds": offset,
        "age_seconds": max(0, -offset),
    }


def _ob_scope_for_symbol(symbol: str) -> str:
    return SYMBOL_TO_OB_SCOPE.get(symbol, symbol)


def _ob_snapshot(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "date_utc": row.get("date_utc"),
        "scope": row.get("scope"),
        "window_size": _int_or_none(row.get("window_size")),
        "window_start_date": row.get("window_start_date"),
        "window_end_date": row.get("window_end_date"),
        "continuation_count": _int_or_none(row.get("continuation_count")),
        "total_count": _int_or_none(row.get("total_count")),
        "rate_pct": _float_or_none(row.get("rate_pct")),
        "alarm_fired": _bool_from_csv(row.get("alarm_fired")),
        "insufficient_sample": _bool_from_csv(row.get("insufficient_sample")),
    }


def _latest_ob_row(
    ob_rows: list[dict[str, Any]] | list[tuple[int, dict[str, Any]]] | None,
    *,
    scope: str,
    decision_date: date,
) -> dict[str, Any] | None:
    best: tuple[date, int, dict[str, Any]] | None = None
    for line_no, row in _rows_with_lines(ob_rows):
        if str(row.get("scope") or "") != scope:
            continue
        row_date = _parse_date(row.get("date_utc"))
        if row_date is None or row_date > decision_date:
            continue
        item = (row_date, line_no, row)
        if best is None or item[:2] >= best[:2]:
            best = item
    return best[2] if best else None


def select_decay_context(
    *,
    symbol: str,
    decision_time_utc: Any,
    ob_rows: list[dict[str, Any]] | list[tuple[int, dict[str, Any]]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(decision_time_utc)
    if decision_dt is None:
        return {
            "join_status": "OB_CONTINUATION_JOIN_MISSING_DECISION_TIME_UNPARSEABLE",
            "symbol_scope_status": "OB_CONTINUATION_SYMBOL_SCOPE_MISSING",
            "symbol_scope": _ob_scope_for_symbol(symbol),
            "symbol_scope_snapshot": None,
            "portfolio_scope_status": "OB_CONTINUATION_PORTFOLIO_SCOPE_MISSING",
            "portfolio_scope_snapshot": None,
        }
    decision_date = decision_dt.date()
    symbol_scope = _ob_scope_for_symbol(symbol)
    symbol_snapshot = _ob_snapshot(_latest_ob_row(ob_rows, scope=symbol_scope, decision_date=decision_date))
    portfolio_snapshot = _ob_snapshot(_latest_ob_row(ob_rows, scope="PORTFOLIO", decision_date=decision_date))
    symbol_status = "OB_CONTINUATION_SYMBOL_SCOPE_JOINED" if symbol_snapshot else "OB_CONTINUATION_SYMBOL_SCOPE_MISSING"
    portfolio_status = "OB_CONTINUATION_PORTFOLIO_SCOPE_JOINED" if portfolio_snapshot else "OB_CONTINUATION_PORTFOLIO_SCOPE_MISSING"
    if symbol_scope not in {"XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"}:
        symbol_status = "OB_CONTINUATION_SYMBOL_SCOPE_UNAVAILABLE_PORTFOLIO_ONLY"
    joined = bool(symbol_snapshot or portfolio_snapshot)
    return {
        "join_status": "OB_CONTINUATION_JOINED" if joined else "OB_CONTINUATION_JOIN_MISSING",
        "symbol_scope_status": symbol_status,
        "symbol_scope": symbol_scope,
        "symbol_scope_snapshot": symbol_snapshot,
        "portfolio_scope_status": portfolio_status,
        "portfolio_scope_snapshot": portfolio_snapshot,
    }


def _broker_actual_allowed(row: dict[str, Any] | None) -> bool:
    return bool(
        row
        and row.get("actual_r_claim_allowed") is True
        and row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    )


def _monthly_status(monthly_decay_report: dict[str, Any] | None) -> dict[str, Any]:
    report = monthly_decay_report if isinstance(monthly_decay_report, dict) else {}
    if not report:
        return {
            "status": "MONTHLY_DECAY_REPORT_NOT_FOUND",
            "path": None,
            "mtime_utc": None,
        }
    return {
        "status": report.get("status") or "MONTHLY_DECAY_REPORT_PRESENT",
        "path": report.get("path"),
        "mtime_utc": report.get("mtime_utc"),
    }


def _regime_snapshot(regime_join: dict[str, Any]) -> dict[str, Any]:
    row = regime_join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": regime_join.get("join_status"),
            "regime": None,
            "classifier_version": None,
            "regime_ts_utc": None,
            "regime_offset_seconds": None,
            "regime_age_seconds": None,
            "reason": None,
            "raw_features": None,
        }
    return {
        "join_status": regime_join.get("join_status"),
        "regime": row.get("regime"),
        "classifier_version": row.get("classifier_version"),
        "lookback": row.get("lookback"),
        "regime_ts_utc": row.get("ts"),
        "regime_logged_at_utc": row.get("logged_at"),
        "regime_offset_seconds": regime_join.get("offset_seconds"),
        "regime_age_seconds": regime_join.get("age_seconds"),
        "reason": row.get("reason"),
        "raw_features": row.get("raw_features") if isinstance(row.get("raw_features"), dict) else None,
    }


def _status_for(
    *,
    regime_snapshot: dict[str, Any],
    decay_context: dict[str, Any],
    action_required: list[str],
) -> str:
    if action_required:
        return ACTION_REQUIRED
    regime_joined = regime_snapshot.get("regime") is not None
    decay_joined = decay_context.get("join_status") == "OB_CONTINUATION_JOINED"
    if regime_joined and decay_joined:
        return COMPLETE
    if not regime_joined:
        return REGIME_MISSING
    return DECAY_MISSING


def _ml_label_eligibility(*, actual_allowed: bool, path_row: dict[str, Any] | None) -> str:
    if actual_allowed:
        return "ACCOUNT_HISTORY_LABEL_WITH_REGIME_DECAY_CONTEXT"
    if path_row and path_row.get("touched_entry") is True:
        return "SYNTHETIC_PATH_LABEL_WITH_REGIME_DECAY_CONTEXT_NOT_ACCOUNT_HISTORY"
    if path_row:
        return "NO_ACTUAL_R_LABEL_PATH_CONTEXT_WITH_REGIME_DECAY"
    return "FEATURE_CONTEXT_ONLY_LABEL_NOT_AVAILABLE"


def build_context_row(
    *,
    row_type: str,
    source_row: dict[str, Any],
    regime_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    ob_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    path_row: dict[str, Any] | None = None,
    broker_row: dict[str, Any] | None = None,
    monthly_decay_report: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    symbol = _canonical_symbol(source_row.get("symbol") or source_row.get("instrument") or (broker_row or {}).get("symbol"))
    decision_time = source_row.get("decision_time_utc") or (broker_row or {}).get("decision_time_utc")
    candidate_id = source_row.get("candidate_id") or (broker_row or {}).get("candidate_id")
    fill_id = source_row.get("fill_id") or (broker_row or {}).get("fill_id")
    actual_allowed = _broker_actual_allowed(broker_row)
    regime_join = select_asof_regime(
        symbol=symbol,
        decision_time_utc=decision_time,
        source_row=source_row,
        regime_rows=regime_rows,
    )
    regime_snapshot = _regime_snapshot(regime_join)
    decay_context = select_decay_context(symbol=symbol, decision_time_utc=decision_time, ob_rows=ob_rows)
    monthly_status = _monthly_status(monthly_decay_report)
    action_required: list[str] = []
    documented_limitations: list[str] = []
    if regime_snapshot.get("regime") is None:
        documented_limitations.append(str(regime_snapshot.get("join_status") or "REGIME_JOIN_MISSING"))
    if decay_context.get("join_status") != "OB_CONTINUATION_JOINED":
        documented_limitations.append(str(decay_context.get("join_status") or "OB_CONTINUATION_JOIN_MISSING"))
    if decay_context.get("symbol_scope_status") == "OB_CONTINUATION_SYMBOL_SCOPE_UNAVAILABLE_PORTFOLIO_ONLY":
        documented_limitations.append("SYMBOL_OB_CONTINUATION_SCOPE_UNAVAILABLE_PORTFOLIO_ONLY")
    if monthly_status["status"] != "MONTHLY_DECAY_REPORT_PRESENT":
        documented_limitations.append(str(monthly_status["status"]))
    if actual_allowed and (broker_row or {}).get("accounting_evidence_class") != "ACCOUNT_HISTORY_REALIZED":
        action_required.append("ACTUAL_R_ALLOWED_WITHOUT_ACCOUNT_HISTORY_REALIZED")
    status = _status_for(
        regime_snapshot=regime_snapshot,
        decay_context=decay_context,
        action_required=action_required,
    )
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        row_type,
        candidate_id,
        fill_id,
        symbol,
        decision_time,
        source_row.get("created_at_utc"),
        source_row.get("final_outcome_at_log"),
        path_row.get("created_at_utc") if path_row else "",
        path_row.get("asof_latest_candle_utc") if path_row else "",
        path_row.get("path_label") if path_row else "",
        (broker_row or {}).get("row_key"),
        regime_snapshot.get("regime_ts_utc"),
        regime_snapshot.get("regime"),
        regime_snapshot.get("classifier_version"),
        decay_context.get("symbol_scope_snapshot"),
        decay_context.get("portfolio_scope_snapshot"),
        monthly_status,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("regime_decay_outcome_join", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-018",
        "follow_id": "LIVE-FOLLOW-015",
        "row_type": row_type,
        "regime_decay_context_status": status,
        "candidate_id": candidate_id,
        "fill_id": fill_id,
        "trade_id": source_row.get("trade_id") or (broker_row or {}).get("trade_id") or fill_id,
        "symbol": symbol,
        "broker_symbol": source_row.get("broker_symbol") or (broker_row or {}).get("broker_symbol") or symbol,
        "side": source_row.get("side"),
        "framework": source_row.get("framework"),
        "session": source_row.get("session") or source_row.get("kill_zone"),
        "decision_time_utc": decision_time,
        "candidate_final_outcome_at_log": source_row.get("final_outcome_at_log") or (path_row or {}).get("final_outcome_at_candidate_log"),
        "path_label": (path_row or {}).get("path_label"),
        "touched_entry": (path_row or {}).get("touched_entry"),
        "hit_tp1": (path_row or {}).get("hit_tp1"),
        "hit_sl": (path_row or {}).get("hit_sl"),
        "path_ambiguity_status": (path_row or {}).get("path_ambiguity_status"),
        "path_context_status": "PATH_JOINED" if path_row else "NO_CANDIDATE_PATH_ROW",
        "account_history_join_status": "ACCOUNT_HISTORY_REALIZED" if actual_allowed else "NO_ACCOUNT_HISTORY_REALIZED_FOR_ROW",
        "actual_r_claim_allowed": actual_allowed,
        "broker_actual_r": (broker_row or {}).get("broker_actual_r") if actual_allowed else None,
        "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        "broker_actual_r_evidence_class": (broker_row or {}).get("accounting_evidence_class"),
        "broker_actual_r_truth_lane": (broker_row or {}).get("truth_lane"),
        "regime_context": regime_snapshot,
        "ob_continuation_context": decay_context,
        "monthly_decay_report_context": monthly_status,
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "claim_boundary": (
            "Regime and decay fields are decision-time/as-of context for analysis and ML feature stratification. "
            "Actual-R claims are allowed only when joined to ACCOUNT_HISTORY_REALIZED broker evidence."
        ),
        "ml_feature_role": "ML_REGIME_DECAY_FEATURE_AND_STRATIFICATION_CONTEXT",
        "ml_label_eligibility": _ml_label_eligibility(actual_allowed=actual_allowed, path_row=path_row),
        "ml_no_leak_boundary": "REGIME_ASOF_SAME_CLOSE_GRACE_AND_DECAY_SNAPSHOT_ONLY_NO_POST_OUTCOME_FEATURES",
        "evidence_class": "DECISION_TIME_REGIME_DECAY_CONTEXT",
        "no_leak_status": "REGIME_DECAY_CONTEXT_AUDIT_NOT_DECISION_CHANGE",
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


def build_regime_decay_outcome_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    regime_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    ob_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    monthly_decay_report: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _latest_by_key(_rows_with_lines(candidate_rows), "candidate_id")
    broker_by_candidate = _latest_by_key(_rows_with_lines(broker_rows), "candidate_id")
    broker_by_fill = _latest_broker_by_fill_id(_rows_with_lines(broker_rows))
    path_by_candidate = _latest_by_key(_rows_with_lines(path_rows), "candidate_id")
    rows: list[dict[str, Any]] = []
    for candidate_id, candidate in sorted(candidates.items()):
        rows.append(
            build_context_row(
                row_type="candidate_regime_decay_context",
                source_row=candidate,
                broker_row=broker_by_candidate.get(candidate_id),
                path_row=path_by_candidate.get(candidate_id),
                regime_rows=regime_rows,
                ob_rows=ob_rows,
                monthly_decay_report=monthly_decay_report,
                generated_at_utc=generated_at_utc,
            )
        )
    for fill_id, broker_row in sorted(broker_by_fill.items()):
        if broker_row.get("audit_scope") != "filled_trade_reconciliation":
            continue
        source = {
            "fill_id": fill_id,
            "trade_id": broker_row.get("trade_id"),
            "candidate_id": broker_row.get("candidate_id"),
            "symbol": broker_row.get("symbol"),
            "broker_symbol": broker_row.get("broker_symbol"),
            "decision_time_utc": broker_row.get("decision_time_utc"),
            "created_at_utc": broker_row.get("created_at_utc"),
        }
        candidate_id = str(broker_row.get("candidate_id") or "")
        rows.append(
            build_context_row(
                row_type="filled_regime_decay_context",
                source_row=source,
                broker_row=broker_row,
                path_row=path_by_candidate.get(candidate_id) if candidate_id else None,
                regime_rows=regime_rows,
                ob_rows=ob_rows,
                monthly_decay_report=monthly_decay_report,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("regime_decay_context_status") or "UNKNOWN") for row in rows)
    row_type_counts = Counter(str(row.get("row_type") or "UNKNOWN") for row in rows)
    regime_counts = Counter()
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    label_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in rows)
    action_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    daily_mix: dict[str, Counter[str]] = defaultdict(Counter)
    weekly_mix: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        regime_context = row.get("regime_context") if isinstance(row.get("regime_context"), dict) else {}
        regime = str(regime_context.get("regime") or "REGIME_MISSING")
        regime_counts[regime] += 1
        action_counts.update(row.get("action_required_codes") or [])
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        decision_dt = parse_utc(row.get("decision_time_utc"))
        if decision_dt is not None:
            daily_mix[decision_dt.date().isoformat()][regime] += 1
            iso_year, iso_week, _ = decision_dt.isocalendar()
            weekly_mix[f"{iso_year:04d}-W{iso_week:02d}"][regime] += 1
    return {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "row_type_counts": dict(row_type_counts),
        "symbol_counts": dict(symbol_counts),
        "regime_counts": dict(regime_counts),
        "ml_label_eligibility_counts": dict(label_counts),
        "actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "regime_joined_rows": sum(1 for row in rows if isinstance(row.get("regime_context"), dict) and row["regime_context"].get("regime")),
        "ob_continuation_joined_rows": sum(1 for row in rows if isinstance(row.get("ob_continuation_context"), dict) and row["ob_continuation_context"].get("join_status") == "OB_CONTINUATION_JOINED"),
        "action_required_code_counts": dict(action_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
        "daily_regime_mix": {key: dict(value) for key, value in sorted(daily_mix.items())},
        "weekly_regime_mix": {key: dict(value) for key, value in sorted(weekly_mix.items())},
    }
