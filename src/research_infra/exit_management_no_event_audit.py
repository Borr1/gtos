"""Exit-management no-event status helpers for LTO-021.

This module is research/tooling only. It documents why BE, partial-close, and
time-in-trade shadow event logs may be empty without being broken. It does not
call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "exit_management_shadow_status_v1"
CLASSIFIER_VERSION = "exit_management_status_classifier_v4"
COMPLETE = "EXIT_MANAGEMENT_NO_EVENT_DOCUMENTED"
COMPLETE_WITH_EVENTS = "EXIT_MANAGEMENT_EVENT_ROWS_PRESENT"
ACTION_REQUIRED = "EXIT_MANAGEMENT_ACTION_REQUIRED"
NO_TRIGGER_R_FLOOR = 1.0

EVENT_LOG_NAMES = {
    "be": "be_shadow_log.jsonl",
    "partial_close": "partial_close_shadow_log.jsonl",
    "time_in_trade": "time_in_trade.jsonl",
}


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


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        current_key = (
            _latest_clock(item),
            parse_utc(item.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            line_no,
        )
        previous = latest.get(candidate_id)
        previous_key = (
            _latest_clock(previous or {}),
            parse_utc((previous or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int((previous or {}).get("_line_no") or 0),
        )
        if current_key >= previous_key:
            latest[candidate_id] = item
    return latest


def _event_rows_by_key(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for _, row in rows:
        for key in (row.get("candidate_id"), row.get("trade_id")):
            if key:
                by_key.setdefault(str(key), []).append(row)
    return by_key


def _event_count(event_rows_by_key: dict[str, list[dict[str, Any]]], candidate_id: str, trade_id: str) -> int:
    return _event_count_for_keys(event_rows_by_key, [candidate_id, trade_id])


def _event_rows_for_keys(event_rows_by_key: dict[str, list[dict[str, Any]]], keys: list[str]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    rows: list[dict[str, Any]] = []
    for key in keys:
        if not key:
            continue
        for row in event_rows_by_key.get(key, []):
            row_identity = id(row)
            if row_identity not in seen:
                seen.add(row_identity)
                rows.append(row)
    return rows


def _event_count_for_keys(event_rows_by_key: dict[str, list[dict[str, Any]]], keys: list[str]) -> int:
    return len(_event_rows_for_keys(event_rows_by_key, keys))


def _filled_trade_id(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and not text.startswith("lim_")


def _pending_fill_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_PENDING_LIFECYCLE_JOIN_ROW"
    source = _pending_source(row)
    label = str(source.get("fill_no_fill_label") or "").lower()
    intent = str(source.get("intent_after_check") or "").lower()
    if "filled" in label or "filled" in intent:
        return "FILLED_BY_PENDING_LIFECYCLE"
    if "no_fill" in label or "cancelled" in intent or "still_pending" in intent:
        return "NO_FILLED_TRADE_FROM_PENDING_LIFECYCLE"
    return "PENDING_LIFECYCLE_PRESENT_FILL_STATUS_UNCLEAR"


def _account_fill_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_ACCOUNT_TRUTH_ROW"
    status = str(row.get("account_truth_status") or "")
    if row.get("actual_r_claim_allowed") is True:
        return "ACCOUNT_HISTORY_REALIZED_FILL"
    if "NO_REALIZED_ACCOUNT_HISTORY" in status:
        return "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE"
    return status or "ACCOUNT_TRUTH_STATUS_UNCLEAR"


def _broker_fill_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_BROKER_AUDIT_ROW"
    if (
        row.get("fill_id")
        or row.get("ticket")
        or row.get("actual_r_claim_allowed") is True
        or row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    ):
        return "BROKER_AUDIT_FILLED_TRADE"
    if row.get("audit_scope") == "candidate_account_truth":
        return "BROKER_AUDIT_CANDIDATE_NO_FILL"
    return "BROKER_AUDIT_STATUS_UNCLEAR"


def _broker_is_realized_fill(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return (
        bool(row.get("fill_id") or row.get("ticket"))
        or row.get("actual_r_claim_allowed") is True
        or row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    )


def _pending_source(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    source = row.get("source_row")
    return source if isinstance(source, dict) else row


def _candidate_has_fill(
    candidate: dict[str, Any],
    pending: dict[str, Any] | None,
    account: dict[str, Any] | None,
    broker: dict[str, Any] | None,
) -> bool:
    if _filled_trade_id(candidate.get("trade_id")):
        return True
    if account and account.get("actual_r_claim_allowed") is True:
        return True
    if broker and (
        broker.get("fill_id")
        or broker.get("ticket")
        or broker.get("actual_r_claim_allowed") is True
        or broker.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    ):
        return True
    source = _pending_source(pending)
    text = f"{source.get('fill_no_fill_label', '')} {source.get('intent_after_check', '')}".lower()
    if "filled" in text:
        return True
    return False


def _ticket_keys(row: dict[str, Any] | None) -> list[str]:
    if not row:
        return []
    source = _pending_source(row)
    links = row.get("source_links")
    links = links if isinstance(links, dict) else {}
    keys: list[str] = []
    for payload in (row, source, links):
        for field in (
            "ticket",
            "trade_state_ticket",
            "pending_ticket",
            "mt5_order_ticket",
            "broker_order_ticket",
            "order_ticket",
            "slippage_ticket",
            "mt5_export_position_id",
            "mt5_export_order_id",
        ):
            value = payload.get(field)
            if value:
                keys.append(str(value))
    return keys


def _latest_broker_by_ticket(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    by_ticket: dict[str, dict[str, Any]] = {}
    for _, row in rows:
        for key in _ticket_keys(row):
            current = by_ticket.get(key)
            if not current or _latest_clock(row) >= _latest_clock(current):
                by_ticket[key] = row
    return by_ticket


def _event_lookup_keys(
    *,
    candidate_id: str,
    trade_id: str,
    candidate: dict[str, Any] | None = None,
    pending: dict[str, Any] | None,
    broker: dict[str, Any] | None,
) -> list[str]:
    keys = [candidate_id, trade_id]
    if candidate:
        symbol = str(candidate.get("symbol") or "").strip()
        session = str(candidate.get("session") or candidate.get("kill_zone") or "").strip().lower()
        decision_time = parse_utc(candidate.get("decision_time_utc") or candidate.get("asof_cutoff_utc"))
        if symbol and session and decision_time:
            keys.append(f"{symbol}_{decision_time:%Y-%m-%d}_{session}_{decision_time:%H%M}")
    for row in (pending, _pending_source(pending), broker):
        if not row:
            continue
        for field in ("candidate_id", "trade_id", "fill_id"):
            value = row.get(field)
            if value:
                keys.append(str(value))
    seen: set[str] = set()
    return [key for key in keys if key and not (key in seen or seen.add(key))]


def _actual_close_r_from_time_in_trade(rows: list[dict[str, Any]]) -> float | None:
    values: list[float] = []
    for row in rows:
        try:
            values.append(float(row.get("actual_close_r")))
        except (TypeError, ValueError):
            continue
    return max(values) if values else None


def build_exit_management_status_row(
    candidate: dict[str, Any],
    *,
    pending_row: dict[str, Any] | None = None,
    account_row: dict[str, Any] | None = None,
    broker_row: dict[str, Any] | None = None,
    be_event_count: int = 0,
    partial_event_count: int = 0,
    time_in_trade_event_count: int = 0,
    time_in_trade_actual_close_r: float | None = None,
    event_log_file_statuses: dict[str, str] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    candidate_id = str(candidate.get("candidate_id") or "")
    trade_id = str(candidate.get("trade_id") or "")
    has_fill = _candidate_has_fill(candidate, pending_row, account_row, broker_row)

    documented_no_events: list[str] = []
    action_required: list[str] = []
    if has_fill:
        fill_state = "FILLED_TRADE_OR_ACCOUNT_HISTORY_PRESENT"
    else:
        fill_state = "NO_FILLED_TRADE"
        documented_no_events.append("NO_FILLED_TRADE")

    if be_event_count:
        be_status = "EVENT_ROW_PRESENT"
    elif not has_fill:
        be_status = "NO_FILLED_TRADE"
        documented_no_events.append("NO_BE_TRIGGER")
    elif time_in_trade_actual_close_r is not None and time_in_trade_actual_close_r < NO_TRIGGER_R_FLOOR:
        be_status = "NO_BE_TRIGGER_BELOW_1R_TIME_IN_TRADE"
        documented_no_events.append("NO_BE_TRIGGER")
    else:
        be_status = "NO_BE_TRIGGER_OR_EVENT_ROW_NOT_CAPTURED"
        action_required.append("FILLED_TRADE_WITHOUT_BE_TRIGGER_STATUS_ROW")

    if partial_event_count:
        partial_status = "EVENT_ROW_PRESENT"
    elif not has_fill:
        partial_status = "NO_FILLED_TRADE"
        documented_no_events.append("NO_PARTIAL_TRIGGER")
    elif time_in_trade_actual_close_r is not None and time_in_trade_actual_close_r < NO_TRIGGER_R_FLOOR:
        partial_status = "NO_PARTIAL_TRIGGER_BELOW_1R_TIME_IN_TRADE"
        documented_no_events.append("NO_PARTIAL_TRIGGER")
    else:
        partial_status = "NO_PARTIAL_TRIGGER_OR_EVENT_ROW_NOT_CAPTURED"
        action_required.append("FILLED_TRADE_WITHOUT_PARTIAL_TRIGGER_STATUS_ROW")

    if time_in_trade_event_count:
        tit_status = "EVENT_ROW_PRESENT"
    elif not has_fill:
        tit_status = "NO_FILLED_TRADE"
        documented_no_events.append("NO_CLOSE_EVENT")
    else:
        tit_status = "NO_CLOSE_EVENT_OR_TIME_IN_TRADE_ROW_NOT_CAPTURED"
        action_required.append("FILLED_TRADE_WITHOUT_TIME_IN_TRADE_ROW")

    event_counts = {
        "be_shadow_log": be_event_count,
        "partial_close_shadow_log": partial_event_count,
        "time_in_trade": time_in_trade_event_count,
    }
    status = ACTION_REQUIRED if action_required else COMPLETE_WITH_EVENTS if any(event_counts.values()) else COMPLETE
    pending_status = _pending_fill_status(pending_row)
    account_status = _account_fill_status(account_row)
    broker_status = _broker_fill_status(broker_row)
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        candidate_id,
        candidate.get("created_at_utc"),
        pending_row.get("row_key") if pending_row else "",
        account_row.get("row_key") if account_row else "",
        broker_row.get("row_key") if broker_row else "",
        event_counts,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("exit_management_status", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-021",
        "follow_id": "LIVE-FOLLOW-018",
        "candidate_id": candidate_id,
        "trade_id": trade_id or None,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "exit_management_status": status,
        "fill_state": fill_state,
        "pending_lifecycle_fill_status": pending_status,
        "account_truth_fill_status": account_status,
        "broker_actual_r_fill_status": broker_status,
        "be_shadow_status": be_status,
        "partial_close_shadow_status": partial_status,
        "time_in_trade_shadow_status": tit_status,
        "documented_no_event_codes": sorted(set(documented_no_events)),
        "action_required_codes": sorted(set(action_required)),
        "actual_event_row_counts": event_counts,
        "time_in_trade_actual_close_r": time_in_trade_actual_close_r,
        "event_log_file_statuses": event_log_file_statuses or {},
        "event_rows_separate_from_status_rows": True,
        "claim_boundary": (
            "This row documents why exit-management shadow event logs are empty or populated. "
            "It is not a BE, partial-close, or time-in-trade outcome row."
        ),
        "evidence_class": "EXIT_MANAGEMENT_NO_EVENT_STATUS",
        "no_leak_status": "POST_DECISION_STATUS_ROW_NOT_DECISION_FEATURE",
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


def build_exit_management_status_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    pending_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    account_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    be_event_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    partial_event_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    time_in_trade_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    event_log_file_statuses: dict[str, str] | None = None,
    generated_at_utc: str | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _rows_with_lines(candidate_rows)
    if decision_date_prefix:
        candidates = [
            (line, row)
            for line, row in candidates
            if str(row.get("decision_time_utc") or "").startswith(decision_date_prefix)
        ]
    pending_by_candidate = _latest_by_candidate(_rows_with_lines(pending_rows))
    account_by_candidate = _latest_by_candidate(_rows_with_lines(account_rows))
    broker_rows_with_lines = _rows_with_lines(broker_rows)
    broker_by_candidate = _latest_by_candidate(broker_rows_with_lines)
    broker_by_ticket = _latest_broker_by_ticket(broker_rows_with_lines)
    be_by_key = _event_rows_by_key(_rows_with_lines(be_event_rows))
    partial_by_key = _event_rows_by_key(_rows_with_lines(partial_event_rows))
    tit_by_key = _event_rows_by_key(_rows_with_lines(time_in_trade_rows))

    rows: list[dict[str, Any]] = []
    for _, candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            continue
        trade_id = str(candidate.get("trade_id") or "")
        pending_row = pending_by_candidate.get(candidate_id)
        broker_row = broker_by_candidate.get(candidate_id)
        if pending_row:
            for ticket_key in _ticket_keys(pending_row):
                ticket_broker_row = broker_by_ticket.get(ticket_key)
                if ticket_broker_row and (
                    not broker_row or _broker_is_realized_fill(ticket_broker_row)
                ):
                    broker_row = ticket_broker_row
                if _broker_is_realized_fill(broker_row):
                    break
        lookup_keys = _event_lookup_keys(
            candidate_id=candidate_id,
            trade_id=trade_id,
            candidate=candidate,
            pending=pending_row,
            broker=broker_row,
        )
        tit_rows = _event_rows_for_keys(tit_by_key, lookup_keys)
        rows.append(
            build_exit_management_status_row(
                candidate,
                pending_row=pending_row,
                account_row=account_by_candidate.get(candidate_id),
                broker_row=broker_row,
                be_event_count=_event_count_for_keys(be_by_key, lookup_keys),
                partial_event_count=_event_count_for_keys(partial_by_key, lookup_keys),
                time_in_trade_event_count=len(tit_rows),
                time_in_trade_actual_close_r=_actual_close_r_from_time_in_trade(tit_rows),
                event_log_file_statuses=event_log_file_statuses,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("exit_management_status") or "UNKNOWN") for row in rows)
    fill_counts = Counter(str(row.get("fill_state") or "UNKNOWN") for row in rows)
    be_counts = Counter(str(row.get("be_shadow_status") or "UNKNOWN") for row in rows)
    partial_counts = Counter(str(row.get("partial_close_shadow_status") or "UNKNOWN") for row in rows)
    tit_counts = Counter(str(row.get("time_in_trade_shadow_status") or "UNKNOWN") for row in rows)
    no_event_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    for row in rows:
        no_event_counts.update(row.get("documented_no_event_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])
    return {
        "rows": len(rows),
        "exit_management_status_counts": dict(status_counts),
        "fill_state_counts": dict(fill_counts),
        "be_shadow_status_counts": dict(be_counts),
        "partial_close_shadow_status_counts": dict(partial_counts),
        "time_in_trade_shadow_status_counts": dict(tit_counts),
        "documented_no_event_code_counts": dict(no_event_counts),
        "action_required_code_counts": dict(action_counts),
        "actual_event_row_totals": {
            "be_shadow_log": sum(int((row.get("actual_event_row_counts") or {}).get("be_shadow_log") or 0) for row in rows),
            "partial_close_shadow_log": sum(int((row.get("actual_event_row_counts") or {}).get("partial_close_shadow_log") or 0) for row in rows),
            "time_in_trade": sum(int((row.get("actual_event_row_counts") or {}).get("time_in_trade") or 0) for row in rows),
        },
    }
