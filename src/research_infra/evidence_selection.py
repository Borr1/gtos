"""Append-only shadow evidence selection helpers.

Several shadow ledgers are append-only and can contain a later
``SOURCE_BLOCKED`` placeholder after an earlier MT5-recovered row. Latest-row
selection must prefer actual recovered evidence over placeholders, otherwise
downstream audits silently lose path/terminal truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


MIN_UTC = datetime.min.replace(tzinfo=timezone.utc)


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


def row_clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("asof_latest_candle_utc"))
        or parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or MIN_UTC
    )


def row_created_clock(row: dict[str, Any]) -> datetime:
    return parse_utc(row.get("created_at_utc")) or parse_utc(row.get("backfilled_at_utc")) or MIN_UTC


def evidence_quality(row: dict[str, Any]) -> int:
    """Rank evidence quality for append-only shadow rows.

    Quality is intentionally evaluated before recency. A later placeholder
    created after the M1 window falls outside the refresh horizon must not
    override an earlier recovered path/order row.
    """

    ltf_status = str(row.get("ltf_status") or "")
    manual_status = str(row.get("manual_backfill_status") or "")
    path_label = str(row.get("path_order_label") or "")
    ltf_label = str(row.get("ltf_path_order_label") or "")
    read_error = str(row.get("mt5_read_error") or "")
    terminal_status = str(row.get("terminal_outcome_status") or "")
    terminal_event = row.get("candidate_terminal_event") if isinstance(row.get("candidate_terminal_event"), dict) else {}
    terminal_event_status = str((terminal_event or {}).get("terminal_event_status") or "")

    blocked = (
        "SOURCE_BLOCKED" in ltf_status
        or "SOURCE_BLOCKED" in manual_status
        or path_label == "ltf_source_blocked"
        or ltf_label == "ltf_source_blocked"
        or read_error == "outside_max_hours"
    )
    recovered_ltf = ltf_status == "M1_PATH_RECOVERED"
    recovered_order_label = bool(path_label and path_label != "ltf_source_blocked")
    recovered_cluster_label = bool(ltf_label and ltf_label != "ltf_source_blocked")
    recovered_terminal = terminal_status in {
        "ENTRY_THEN_TP1",
        "ENTRY_THEN_SL",
        "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
        "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF",
        "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
        "NO_ENTRY_SL_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
    }
    recovered_cluster_terminal = terminal_event_status in {
        "ENTRY_THEN_TP1",
        "ENTRY_THEN_SL",
        "ENTRY_THEN_TP1_BEFORE_SL",
        "ENTRY_THEN_SL_BEFORE_TP1",
        "ENTRY_TOUCHED_NOT_TERMINAL",
        "NO_ENTRY_TP_AREA_REACHED_NO_TRADE_NO_RESET",
        "NO_ENTRY_SL_AREA_REACHED_NO_TRADE_NO_RESET",
    }

    if blocked:
        return 0
    if recovered_ltf or recovered_order_label or recovered_cluster_label or recovered_terminal or recovered_cluster_terminal:
        return 2
    return 1


def evidence_selection_key(row: dict[str, Any], line_no: int = 0) -> tuple[int, datetime, datetime, int]:
    return evidence_quality(row), row_clock(row), row_created_clock(row), line_no


def latest_by_candidate(
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    *,
    date_prefix: str | None = None,
    key_field: str = "candidate_id",
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(rows or [], start=1):
        if isinstance(item, tuple):
            line_no, row = item
        else:
            line_no, row = index, item
        cid = str(row.get(key_field) or "")
        if not cid:
            continue
        if date_prefix and not str(row.get("decision_time_utc") or "").startswith(date_prefix):
            continue
        candidate = dict(row)
        candidate["_line_no"] = line_no
        if cid not in latest or evidence_selection_key(candidate, line_no) >= evidence_selection_key(
            latest[cid],
            int((latest[cid]).get("_line_no") or 0),
        ):
            latest[cid] = candidate
    return latest
