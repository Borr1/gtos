"""Trade-record inventory index and lifecycle completeness audit.

Research/tooling only. This module builds a current inventory from
``knowledge_base/trade_records`` without mutating the legacy
``knowledge_base/index/_trade_index.json`` research cohort.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "trade_index_lifecycle_audit_v1"
INDEX_SCHEMA_VERSION = "trade_record_inventory_index_v1"
REPORT_SCHEMA_VERSION = "lto026_trade_index_lifecycle_completeness_v1"

COMPLETE = "TRADE_INDEX_LIFECYCLE_COMPLETE"
COMPLETE_WITH_BLOCKERS = "TRADE_INDEX_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_BLOCKERS"
ACTION_REQUIRED = "TRADE_INDEX_LIFECYCLE_ACTION_REQUIRED"

LEGACY_INDEX_DEPRECATED_FOR_CURRENT_COUNTS = "LEGACY_TRADE_INDEX_DEPRECATED_FOR_CURRENT_COUNTS"
CURRENT_INVENTORY_INDEX = "CURRENT_TRADE_RECORD_INVENTORY_INDEX"


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()[:32]


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def iter_trade_record_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*/*.json") if not path.name.startswith("_"))


def read_trade_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in iter_trade_record_files(root):
        payload = read_json(path)
        if payload is not None:
            records.append((path, payload))
    return records


def _candidate_id(symbol: str | None, decision_time_utc: str | None) -> str | None:
    if not symbol or not decision_time_utc:
        return None
    return f"{symbol}_{decision_time_utc}"


def _decision_time(metadata: dict[str, Any], ai_response: dict[str, Any]) -> str | None:
    return (
        metadata.get("candle_close_utc")
        or metadata.get("candle_time")
        or metadata.get("wall_clock_timestamp_utc")
        or ai_response.get("timestamp_utc")
    )


def _metadata_date(metadata: dict[str, Any], decision_time_utc: str | None) -> str | None:
    date_value = metadata.get("date")
    if date_value:
        return str(date_value)[:10]
    parsed = _parse_dt(decision_time_utc)
    return parsed.date().isoformat() if parsed is not None else None


def _broker_symbol(metadata: dict[str, Any], market: dict[str, Any], symbol: str | None) -> str | None:
    return metadata.get("broker_symbol") or metadata.get("mt5_symbol") or market.get("mt5_symbol") or symbol


def _lifecycle_state(record: dict[str, Any], final_outcome: str | None) -> str:
    pipeline = _safe_dict(record.get("decision_pipeline"))
    l2 = _safe_dict(pipeline.get("level2_verification"))
    if final_outcome == "REJECTED_L2" or l2.get("passed") is False:
        return "REJECTED_L2"
    if final_outcome and str(final_outcome).startswith("REJECTED"):
        return "NON_EXECUTED_REJECT"
    if final_outcome in {"LIMIT_PLACED", "PENDING_LIMIT", "ORDER_PLACED"}:
        return "LIMIT_PLACED"
    if final_outcome in {"FILLED", "POSITION_OPENED", "CLOSED", "CLOSED_TP", "CLOSED_SL", "TP", "SL", "BE_STOP"}:
        return "FILLED_OR_CLOSED"
    return "UNKNOWN"


def _pending_audit_by_trade_record_path(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for _line, row in rows:
        if (
            row.get("pending_limit_lifecycle_audit_status") == "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED"
            and row.get("final_state") == "PENDING_LIFECYCLE_GROUP_MISSING"
            and row.get("manual_backfill_status") == "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
        ):
            continue
        raw_path = row.get("trade_record_path")
        if not raw_path:
            continue
        normalized = str(raw_path).replace("\\", "/")
        by_path[normalized] = row
    return by_path


def _raw_trade_id_collisions(
    records: list[tuple[Path, dict[str, Any]]],
    *,
    root: Path,
) -> dict[str, set[str]]:
    symbols_by_raw_id: dict[str, set[str]] = defaultdict(set)
    for path, record in records:
        metadata = _safe_dict(record.get("metadata"))
        symbol = str(metadata.get("symbol") or path.parent.name)
        limit_intent = _safe_dict(record.get("limit_intent"))
        raw_trade_id = str(limit_intent.get("trade_id") or metadata.get("trade_id") or "")
        if raw_trade_id:
            symbols_by_raw_id[raw_trade_id].add(symbol)
    return {trade_id: symbols for trade_id, symbols in symbols_by_raw_id.items() if len(symbols) > 1}


def _base_row(generated_at_utc: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "no_leak_status": "POST_DECISION_TRADE_RECORD_INVENTORY_AUDIT_NOT_DECISION_FEATURE",
    }


def build_trade_record_audit_row(
    path: Path,
    record: dict[str, Any],
    *,
    root: Path,
    pending_audit_row: dict[str, Any] | None,
    raw_trade_id_collision_symbols: list[str],
    generated_at_utc: str,
) -> dict[str, Any]:
    metadata = _safe_dict(record.get("metadata"))
    pipeline = _safe_dict(record.get("decision_pipeline"))
    ai_response = _safe_dict(record.get("ai_response"))
    market = _safe_dict(record.get("market"))
    trade_params = _safe_dict(record.get("trade_parameters")) or _safe_dict(ai_response.get("trade_parameters"))
    limit_intent = _safe_dict(record.get("limit_intent"))
    execution = record.get("execution")
    exit_payload = record.get("exit")
    embedded_pending = record.get("pending_lifecycle")

    rel_path = _rel(path, root)
    normalized_rel_path = rel_path.replace("\\", "/")
    record_hash = _record_hash(record)
    symbol = str(metadata.get("symbol") or path.parent.name)
    decision_time_utc = _decision_time(metadata, ai_response)
    candidate_id = _candidate_id(symbol, decision_time_utc)
    final_outcome = pipeline.get("final_outcome") or record.get("final_outcome") or record.get("status")
    state = _lifecycle_state(record, str(final_outcome) if final_outcome is not None else None)
    has_execution = isinstance(execution, dict) and bool(execution)
    has_exit = isinstance(exit_payload, dict) and bool(exit_payload)
    has_embedded_pending = isinstance(embedded_pending, dict) and bool(embedded_pending)
    has_pending_audit = pending_audit_row is not None

    limitations: list[str] = []
    actions: list[str] = []
    if state == "LIMIT_PLACED":
        if has_exit:
            completeness = "LIMIT_PLACED_COMPLETE_WITH_EXIT"
        elif has_execution:
            completeness = "LIMIT_PLACED_COMPLETE_WITH_EXECUTION"
        elif has_embedded_pending:
            completeness = "LIMIT_PLACED_COMPLETE_WITH_EMBEDDED_PENDING_LIFECYCLE"
        elif has_pending_audit:
            completeness = "LIMIT_PLACED_COMPLETE_WITH_PENDING_LIFECYCLE_AUDIT"
        else:
            completeness = "LIMIT_PLACED_DOCUMENTED_LEGACY_LIFECYCLE_GAP"
            limitations.append("LIMIT_PLACED_MISSING_EXECUTION_AND_PENDING_LIFECYCLE_STATE")
    elif state in {"REJECTED_L2", "NON_EXECUTED_REJECT"}:
        completeness = "NON_EXECUTED_DECISION_COMPLETE_NO_LIFECYCLE_REQUIRED"
    elif state == "FILLED_OR_CLOSED":
        completeness = "FILLED_OR_CLOSED_COMPLETE" if has_exit or has_execution else "FILLED_OR_CLOSED_MISSING_EXIT_OR_EXECUTION"
        if completeness.endswith("MISSING_EXIT_OR_EXECUTION"):
            actions.append("FILLED_OR_CLOSED_RECORD_LACKS_EXIT_OR_EXECUTION")
    else:
        completeness = "UNKNOWN_STATE_DOCUMENTED"
        limitations.append("TRADE_RECORD_STATE_UNKNOWN")

    if raw_trade_id_collision_symbols:
        limitations.append("LEGACY_RAW_TRADE_ID_NOT_GLOBALLY_UNIQUE")
    if has_exit and not has_execution:
        limitations.append("TRADE_RECORD_EXIT_PRESENT_BUT_EXECUTION_FIELD_NULL")
    if state == "LIMIT_PLACED" and has_pending_audit and not has_embedded_pending:
        limitations.append("PENDING_LIFECYCLE_PRESENT_IN_AUDIT_NOT_EMBEDDED_IN_TRADE_RECORD")

    if pending_audit_row and pending_audit_row.get("pending_limit_lifecycle_audit_status") == "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED":
        actions.append("MATCHED_PENDING_LIFECYCLE_AUDIT_ACTION_REQUIRED")

    status = ACTION_REQUIRED if actions else COMPLETE_WITH_BLOCKERS if limitations else COMPLETE
    source_sig = _stable_hash(
        SCHEMA_VERSION,
        normalized_rel_path,
        record_hash,
        (pending_audit_row or {}).get("row_key"),
        completeness,
        status,
    )
    row = _base_row(generated_at_utc)
    row.update(
        {
            "row_key": _stable_hash("trade_index_lifecycle", source_sig),
            "source_dependency_signature": source_sig,
            "source_log": "knowledge_base/trade_records",
            "source_path": normalized_rel_path,
            "record_hash": record_hash,
            "candidate_id": candidate_id,
            "trade_record_trade_id": metadata.get("trade_id"),
            "limit_intent_trade_id": limit_intent.get("trade_id"),
            "symbol": symbol,
            "broker_symbol": _broker_symbol(metadata, market, symbol),
            "record_date": _metadata_date(metadata, decision_time_utc),
            "decision_time_utc": decision_time_utc,
            "kill_zone": metadata.get("kill_zone") or ai_response.get("kill_zone"),
            "ai_decision": pipeline.get("ai_decision") or ai_response.get("decision"),
            "final_outcome": final_outcome,
            "lifecycle_state": state,
            "lifecycle_completeness": completeness,
            "has_execution": has_execution,
            "has_exit": has_exit,
            "has_embedded_pending_lifecycle": has_embedded_pending,
            "has_pending_lifecycle_audit": has_pending_audit,
            "pending_lifecycle_audit_row_key": (pending_audit_row or {}).get("row_key"),
            "pending_lifecycle_final_state": (pending_audit_row or {}).get("final_state"),
            "pending_lifecycle_final_state_status": (pending_audit_row or {}).get("final_state_status"),
            "pending_lifecycle_missed_move_classification": (pending_audit_row or {}).get("missed_move_classification"),
            "pending_lifecycle_trade_id_global_uniqueness_status": (pending_audit_row or {}).get("trade_id_global_uniqueness_status"),
            "raw_trade_id_collision_symbols": raw_trade_id_collision_symbols,
            "broker_position_mismatch_status": (
                "EXIT_PRESENT_EXECUTION_FIELD_NULL_ACCOUNT_HISTORY_REQUIRED" if has_exit and not has_execution else "NOT_DETECTED"
            ),
            "entry_price": _num(limit_intent.get("limit_price") or trade_params.get("entry_price")),
            "stop_loss": _num(limit_intent.get("stop_loss") or trade_params.get("stop_loss")),
            "take_profit_1": _num(limit_intent.get("take_profit_1") or trade_params.get("take_profit_1")),
            "actual_r": _num(_safe_dict(exit_payload).get("actual_r") or _safe_dict(exit_payload).get("realized_R")),
            "trade_index_lifecycle_status": status,
            "documented_limitation_codes": sorted(set(limitations)),
            "action_required_codes": sorted(set(actions)),
            "source_links": {
                "legacy_trade_index_path": "knowledge_base/index/_trade_index.json",
                "trade_record_path": normalized_rel_path,
                "pending_lifecycle_audit_row_key": (pending_audit_row or {}).get("row_key"),
            },
        }
    )
    return row


def build_trade_index_lifecycle_rows(
    *,
    trade_records: list[tuple[Path, dict[str, Any]]],
    trade_records_root: Path,
    pending_lifecycle_audit_rows: list[tuple[int, dict[str, Any]]] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    pending_by_path = _pending_audit_by_trade_record_path(pending_lifecycle_audit_rows or [])
    collisions = _raw_trade_id_collisions(trade_records, root=trade_records_root)
    rows: list[dict[str, Any]] = []
    for path, record in trade_records:
        rel_path = _rel(path, trade_records_root).replace("\\", "/")
        metadata = _safe_dict(record.get("metadata"))
        symbol = str(metadata.get("symbol") or path.parent.name)
        raw_trade_id = str(_safe_dict(record.get("limit_intent")).get("trade_id") or metadata.get("trade_id") or "")
        collision_symbols = sorted(sym for sym in collisions.get(raw_trade_id, set()) if sym != symbol)
        rows.append(
            build_trade_record_audit_row(
                path,
                record,
                root=trade_records_root,
                pending_audit_row=pending_by_path.get(rel_path) or pending_by_path.get(f"knowledge_base/trade_records/{rel_path}"),
                raw_trade_id_collision_symbols=collision_symbols,
                generated_at_utc=generated,
            )
        )
    return rows


def build_inventory_index(
    rows: list[dict[str, Any]],
    *,
    generated_at_utc: str | None = None,
    legacy_index_path: str = "knowledge_base/index/_trade_index.json",
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    dates = [row.get("record_date") for row in rows if row.get("record_date")]
    source_paths = sorted(str(row.get("source_path")) for row in rows)
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "created_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "index_role": CURRENT_INVENTORY_INDEX,
        "legacy_trade_index_status": LEGACY_INDEX_DEPRECATED_FOR_CURRENT_COUNTS,
        "legacy_trade_index_path": legacy_index_path,
        "source_trade_records_root": "knowledge_base/trade_records",
        "trade_record_count": len(rows),
        "index_count": len(rows),
        "index_count_equals_trade_record_count": True,
        "earliest_record_date": min(dates) if dates else None,
        "latest_record_date": max(dates) if dates else None,
        "by_symbol": dict(sorted(Counter(str(row.get("symbol") or "UNKNOWN") for row in rows).items())),
        "by_final_outcome": dict(sorted(Counter(str(row.get("final_outcome") or "UNKNOWN") for row in rows).items())),
        "by_lifecycle_completeness": dict(sorted(Counter(str(row.get("lifecycle_completeness") or "UNKNOWN") for row in rows).items())),
        "by_trade_index_lifecycle_status": dict(sorted(Counter(str(row.get("trade_index_lifecycle_status") or "UNKNOWN") for row in rows).items())),
        "entries": [
            {
                "source_path": row.get("source_path"),
                "record_hash": row.get("record_hash"),
                "candidate_id": row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "record_date": row.get("record_date"),
                "decision_time_utc": row.get("decision_time_utc"),
                "final_outcome": row.get("final_outcome"),
                "lifecycle_completeness": row.get("lifecycle_completeness"),
                "trade_index_lifecycle_status": row.get("trade_index_lifecycle_status"),
                "row_key": row.get("row_key"),
            }
            for row in rows
        ],
    }


def build_rolling_status(rows: list[dict[str, Any]], *, legacy_index: dict[str, Any] | None = None) -> dict[str, Any]:
    status_counts = Counter(str(row.get("trade_index_lifecycle_status") or "UNKNOWN") for row in rows)
    completeness_counts = Counter(str(row.get("lifecycle_completeness") or "UNKNOWN") for row in rows)
    legacy_count = len((legacy_index or {}).get("trades") or [])
    current_count = len(rows)
    blockers = [row for row in rows if row.get("documented_limitation_codes")]
    action_rows = [row for row in rows if row.get("trade_index_lifecycle_status") == ACTION_REQUIRED]
    return {
        "trade_record_count": current_count,
        "legacy_trade_index_count": legacy_count,
        "legacy_vs_current_count_delta": current_count - legacy_count,
        "index_count_equals_trade_record_count": True,
        "status_counts": dict(sorted(status_counts.items())),
        "lifecycle_completeness_counts": dict(sorted(completeness_counts.items())),
        "documented_blocker_rows": len(blockers),
        "action_required_rows": len(action_rows),
        "limit_placed_rows": sum(1 for row in rows if row.get("lifecycle_state") == "LIMIT_PLACED"),
        "limit_placed_without_lifecycle_truth_rows": sum(
            1 for row in rows if row.get("lifecycle_completeness") == "LIMIT_PLACED_DOCUMENTED_LEGACY_LIFECYCLE_GAP"
        ),
        "raw_trade_id_collision_rows": sum(1 for row in rows if row.get("raw_trade_id_collision_symbols")),
        "exit_present_execution_null_rows": sum(
            1 for row in rows if row.get("broker_position_mismatch_status") == "EXIT_PRESENT_EXECUTION_FIELD_NULL_ACCOUNT_HISTORY_REQUIRED"
        ),
    }
