"""Candidate path-follow contract audit helpers."""

from __future__ import annotations

from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "candidate_path_contract_audit_v1"
COMPLETE = "PATH_CONTRACT_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "PATH_CONTRACT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "PATH_CONTRACT_ACTION_REQUIRED"


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _derive_ambiguity(path_row: dict[str, Any], ltf_row: dict[str, Any] | None) -> str:
    if ltf_row and ltf_row.get("terminal_order_ambiguity") is True:
        return "LOWER_TF_TERMINAL_ORDER_AMBIGUOUS"
    if path_row.get("path_ambiguity_status"):
        return str(path_row["path_ambiguity_status"])
    label = str(path_row.get("path_label") or "")
    if label == "entry_touched_tp_and_sl_m15_ambiguous":
        return "M15_TP1_SL_ORDER_AMBIGUOUS_NO_TICK_ORDER_CLAIM"
    if label == "continued_without_entry_touch_to_tp_area":
        return "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL"
    return "M15_OHLC_PATH_LABEL_ONLY"


def _tick_order_claim(path_row: dict[str, Any], ltf_row: dict[str, Any] | None) -> str:
    if path_row.get("tick_order_claim_status"):
        return str(path_row["tick_order_claim_status"])
    if not ltf_row:
        return "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY"
    if ltf_row.get("terminal_order_ambiguity") is True:
        return "NO_TICK_ORDER_CLAIM_LOWER_TF_AMBIGUOUS"
    if ltf_row.get("ltf_status") == "M1_PATH_RECOVERED":
        return "LOWER_TF_M1_ORDER_OBSERVED"
    return "NO_TICK_ORDER_CLAIM_LOWER_TF_NOT_RECOVERED"


def _source_ohlc_range(path_row: dict[str, Any]) -> dict[str, Any]:
    existing = path_row.get("source_ohlc_range")
    if isinstance(existing, dict) and existing:
        return existing
    return {
        "source_timeframe": "M15",
        "bar_count": path_row.get("bars_elapsed"),
        "first_bar_utc": None,
        "last_bar_utc": path_row.get("asof_latest_candle_utc"),
        "min_low": path_row.get("min_low"),
        "max_high": path_row.get("max_high"),
    }


def build_candidate_path_contract_row(
    line_no: int,
    path_row: dict[str, Any],
    *,
    generated_at_utc: str,
    ltf_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actions: list[str] = []
    limitations: list[str] = []
    for field in (
        "candidate_id",
        "symbol",
        "broker_symbol",
        "decision_time_utc",
        "asof_latest_candle_utc",
        "path_label",
        "touched_entry",
        "hit_tp1",
        "hit_sl",
        "trade_parameters",
        "no_leak_status",
        "promotion_verdict",
    ):
        if _missing(path_row.get(field)):
            actions.append(f"MISSING_PATH_FIELD:{field}")

    first_touch = {
        "entry_first_touch_utc": path_row.get("entry_first_touch_utc")
        or (ltf_row or {}).get("entry_first_touch_utc"),
        "tp1_first_touch_utc": path_row.get("tp1_first_touch_utc")
        or (ltf_row or {}).get("tp1_first_touch_utc"),
        "sl_first_touch_utc": path_row.get("sl_first_touch_utc")
        or (ltf_row or {}).get("sl_first_touch_utc"),
    }
    if not any(first_touch.values()):
        limitations.append("FIRST_TOUCH_TIMES_SOURCE_NOT_CAPTURED_OR_NO_TOUCHES")
    elif not path_row.get("entry_first_touch_utc") and ltf_row:
        limitations.append("FIRST_TOUCH_TIMES_JOINED_FROM_LTF_PATH_ORDER")

    source_range = _source_ohlc_range(path_row)
    if not source_range.get("first_bar_utc"):
        limitations.append("SOURCE_OHLC_FIRST_BAR_NOT_CAPTURED_IN_LEGACY_PATH_ROW")

    ambiguity = _derive_ambiguity(path_row, ltf_row)
    tick_claim = _tick_order_claim(path_row, ltf_row)
    if "NO_TICK_ORDER_CLAIM" in tick_claim:
        limitations.append(tick_claim)

    label = str(path_row.get("path_label") or "")
    if "without_entry_touch" in label and path_row.get("touched_entry") is not False:
        actions.append("PATH_LABEL_TOUCH_CONFLICT")
    if "entry_touched" in label and path_row.get("touched_entry") is not True:
        actions.append("PATH_LABEL_TOUCH_CONFLICT")
    if label == "continued_without_entry_touch_to_tp_area" and path_row.get("hit_tp1") is not True:
        actions.append("NO_ENTRY_TP_AREA_WITHOUT_TP1_HIT")

    if actions:
        status = ACTION_REQUIRED
    elif limitations:
        status = COMPLETE_WITH_LIMITATIONS
    else:
        status = COMPLETE

    candidate_id = str(path_row.get("candidate_id") or "")
    asof = str(path_row.get("asof_latest_candle_utc") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": f"{candidate_id}|{asof}|{SCHEMA_VERSION}",
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "path_line_no": line_no,
        "symbol": path_row.get("symbol"),
        "broker_symbol": path_row.get("broker_symbol"),
        "decision_time_utc": path_row.get("decision_time_utc"),
        "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
        "path_label": path_row.get("path_label"),
        "touched_entry": path_row.get("touched_entry"),
        "hit_tp1": path_row.get("hit_tp1"),
        "hit_sl": path_row.get("hit_sl"),
        "first_touch_times": first_touch,
        "path_ambiguity_status": ambiguity,
        "tick_order_claim_status": tick_claim,
        "source_ohlc_range": source_range,
        "ltf_join_status": "JOINED_LTF_PATH_ORDER" if ltf_row else "LTF_PATH_ORDER_NOT_AVAILABLE",
        "path_contract_status": status,
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
        "manual_backfill_status": "BACKFILLED_FROM_CANDIDATE_PATH_AND_LTF_ROWS",
        "no_leak_status": "POST_DECISION_PATH_CONTRACT_AUDIT_NO_DECISION_FEATURE",
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


def build_candidate_path_contract_rows(
    path_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    ltf_rows_by_candidate: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    latest_by_candidate: dict[str, tuple[int, dict[str, Any]]] = {}
    for line_no, row in path_rows:
        cid = str(row.get("candidate_id") or "")
        if cid:
            latest_by_candidate[cid] = (line_no, row)
    out: list[dict[str, Any]] = []
    ltf_rows_by_candidate = ltf_rows_by_candidate or {}
    for cid, (line_no, row) in sorted(latest_by_candidate.items()):
        out.append(
            build_candidate_path_contract_row(
                line_no,
                row,
                generated_at_utc=generated_at_utc,
                ltf_row=ltf_rows_by_candidate.get(cid),
            )
        )
    return out
