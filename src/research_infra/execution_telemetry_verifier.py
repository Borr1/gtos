"""Research-only verifiers for execution telemetry completeness.

These helpers read GTOS knowledge-base artifacts and produce diagnostics. They
do not write runtime state and do not change live trading behavior.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) < 10:
        return None
    candidate = text[:10]
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return None
    return candidate


def days_between(later: str | None, earlier: str | None) -> int | None:
    if later is None or earlier is None:
        return None
    return (date.fromisoformat(later) - date.fromisoformat(earlier)).days


def nested_get(payload: dict[str, Any], dotted: str) -> Any:
    current: Any = payload
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def present(payload: dict[str, Any], dotted: str) -> bool:
    value = nested_get(payload, dotted)
    return value is not None and value != ""


def iter_trade_record_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    out = []
    for path in root.rglob("*.json"):
        if path.name.startswith("_"):
            continue
        out.append(path)
    return sorted(out)


def summarize_trade_index(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        return {
            "exists": False,
            "trade_count": 0,
            "latest_date": None,
            "source_counts": {},
            "status": "MISSING_INDEX",
        }
    payload = load_json(index_path)
    trades = payload.get("trades", [])
    dates = [parse_date(row.get("date")) for row in trades if isinstance(row, dict)]
    dates = [value for value in dates if value is not None]
    source_counts = Counter(
        str(row.get("source") or "unknown") for row in trades if isinstance(row, dict)
    )
    return {
        "exists": True,
        "version": payload.get("version"),
        "source": payload.get("source"),
        "trade_count": len(trades),
        "declared_trade_count": payload.get("trade_count"),
        "earliest_date": min(dates) if dates else None,
        "latest_date": max(dates) if dates else None,
        "source_counts": dict(sorted(source_counts.items())),
        "status": "INDEX_READ",
    }


def load_trade_record(path: Path, root: Path) -> dict[str, Any]:
    payload = load_json(path)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    pipeline = payload.get("decision_pipeline") if isinstance(payload.get("decision_pipeline"), dict) else {}
    record_date = (
        parse_date(metadata.get("date"))
        or parse_date(metadata.get("candle_close_utc"))
        or parse_date(metadata.get("candle_time"))
        or parse_date(metadata.get("wall_clock_timestamp_utc"))
    )
    return {
        "path": path.relative_to(root).as_posix(),
        "payload": payload,
        "date": record_date,
        "symbol": metadata.get("symbol"),
        "trade_id": metadata.get("trade_id"),
        "final_outcome": pipeline.get("final_outcome") or payload.get("final_outcome") or payload.get("status"),
        "ai_decision": pipeline.get("ai_decision"),
    }


def summarize_trade_records(root: Path) -> dict[str, Any]:
    records = [load_trade_record(path, root) for path in iter_trade_record_files(root)]
    dates = [row["date"] for row in records if row["date"] is not None]
    by_symbol = Counter(str(row["symbol"] or "unknown") for row in records)
    by_outcome = Counter(str(row["final_outcome"] or "UNKNOWN") for row in records)
    return {
        "record_count": len(records),
        "earliest_date": min(dates) if dates else None,
        "latest_date": max(dates) if dates else None,
        "by_symbol": dict(sorted(by_symbol.items())),
        "by_final_outcome": dict(sorted(by_outcome.items())),
        "records": records,
    }


def classify_lifecycle_state(record: dict[str, Any]) -> str:
    payload = record["payload"]
    pipeline = payload.get("decision_pipeline") if isinstance(payload.get("decision_pipeline"), dict) else {}
    l2 = pipeline.get("level2_verification") if isinstance(pipeline.get("level2_verification"), dict) else {}
    gate3 = pipeline.get("gate3_result") if isinstance(pipeline.get("gate3_result"), dict) else {}
    final = str(record.get("final_outcome") or "UNKNOWN")

    if final == "REJECTED_L2" or l2.get("passed") is False:
        return "REJECTED_L2"
    if final in {"LIMIT_PLACED", "ORDER_PLACED", "PENDING_LIMIT"}:
        return "LIMIT_PLACED"
    if final in {"FILLED", "POSITION_OPENED", "CLOSED", "CLOSED_TP", "CLOSED_SL", "TP", "SL", "BE_STOP"}:
        return "FILLED_OR_CLOSED"
    if final.startswith("REJECTED") or final in {"NO_TRADE", "SKIPPED", "DORMANT"}:
        return "NON_EXECUTED_REJECT"
    if record.get("ai_decision") == "CANDIDATE" and l2.get("passed") is True and gate3.get("passed") is True:
        return "LIMIT_PLACED_UNLABELED"
    return "UNKNOWN"


def required_fields_for_state(state: str) -> list[str]:
    common = [
        "metadata.trade_id",
        "metadata.symbol",
        "metadata.date",
        "decision_pipeline.ai_decision",
        "decision_pipeline.final_outcome",
    ]
    if state == "REJECTED_L2":
        return common + ["decision_pipeline.level2_verification"]
    if state in {"LIMIT_PLACED", "LIMIT_PLACED_UNLABELED"}:
        return common + ["execution", "pending_lifecycle"]
    if state == "FILLED_OR_CLOSED":
        return common + ["execution", "exit", "outcome"]
    if state == "NON_EXECUTED_REJECT":
        return common
    return common


def lifecycle_completeness(records: list[dict[str, Any]], *, sample_limit: int = 20) -> dict[str, Any]:
    state_counts: Counter[str] = Counter()
    complete_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    incomplete_samples = []

    for record in records:
        payload = record["payload"]
        state = classify_lifecycle_state(record)
        state_counts[state] += 1
        required = required_fields_for_state(state)
        missing = [field for field in required if not present(payload, field)]
        if missing:
            for field in missing:
                missing_field_counts[field] += 1
            if len(incomplete_samples) < sample_limit:
                incomplete_samples.append(
                    {
                        "path": record["path"],
                        "state": state,
                        "trade_id": record.get("trade_id"),
                        "symbol": record.get("symbol"),
                        "date": record.get("date"),
                        "missing_fields": missing,
                    }
                )
        else:
            complete_counts[state] += 1

    incomplete_count = sum(state_counts.values()) - sum(complete_counts.values())
    return {
        "state_counts": dict(sorted(state_counts.items())),
        "complete_counts": dict(sorted(complete_counts.items())),
        "incomplete_count": incomplete_count,
        "missing_field_counts": dict(sorted(missing_field_counts.items())),
        "incomplete_samples": incomplete_samples,
        "status": "COMPLETE" if incomplete_count == 0 else "INCOMPLETE_CURRENT_DATA",
    }


def summarize_live_evaluations(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {"file_count": 0, "row_count": 0, "latest_date": None, "decision_counts": {}, "by_symbol": {}}
    file_count = 0
    row_count = 0
    dates: list[str] = []
    decision_counts: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    for path in sorted(root.rglob("*.jsonl")):
        file_count += 1
        symbol = path.parent.name
        by_symbol[symbol] += 0
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    decision_counts["JSON_DECODE_ERROR"] += 1
                    continue
                row_count += 1
                by_symbol[symbol] += 1
                decision_counts[str(row.get("decision") or "UNKNOWN")] += 1
                parsed = parse_date(row.get("candle_time")) or parse_date(row.get("timestamp"))
                if parsed:
                    dates.append(parsed)
    return {
        "file_count": file_count,
        "row_count": row_count,
        "latest_date": max(dates) if dates else None,
        "decision_counts": dict(sorted(decision_counts.items())),
        "by_symbol": dict(sorted(by_symbol.items())),
    }


def build_verification(
    *,
    index_path: Path,
    trade_records_root: Path,
    live_evaluations_root: Path,
    max_allowed_index_lag_days: int = 1,
) -> dict[str, Any]:
    index = summarize_trade_index(index_path)
    trade_records = summarize_trade_records(trade_records_root)
    lifecycle = lifecycle_completeness(trade_records["records"])
    live_evaluations = summarize_live_evaluations(live_evaluations_root)

    stale_by_days = days_between(trade_records["latest_date"], index["latest_date"])
    index_is_stale = (
        not index["exists"]
        or (stale_by_days is not None and stale_by_days > max_allowed_index_lag_days)
        or trade_records["record_count"] > index["trade_count"]
    )
    o1_status = "STALE_REBUILD_OR_CONSUMER_MIGRATION_REQUIRED" if index_is_stale else "CURRENT_WITHIN_LAG"
    o8_status = lifecycle["status"]

    return {
        "index_summary": index,
        "trade_record_summary": {k: v for k, v in trade_records.items() if k != "records"},
        "live_evaluation_summary": live_evaluations,
        "o1_index_verifier": {
            "status": o1_status,
            "stale_by_days": stale_by_days,
            "max_allowed_index_lag_days": max_allowed_index_lag_days,
            "index_trade_count": index["trade_count"],
            "trade_record_count": trade_records["record_count"],
            "index_latest_date": index["latest_date"],
            "trade_record_latest_date": trade_records["latest_date"],
        },
        "o8_lifecycle_completeness_verifier": {
            "status": o8_status,
            **lifecycle,
        },
    }
