"""Trade-record reconciliation for live candidate shadow capture.

The live orchestrator saves a trade record before it emits all research-only
forward-shadow rows. If the process is interrupted in that small window, the
trade record remains the original decision-time source of truth, but
``strategy_follow_candidates.jsonl`` can miss the candidate. This module closes
that append-only gap without calling AI, canary, orders, or paid data sources.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.research_infra.forward_capture import (
    STRATEGY_FOLLOW_PATH,
    record_live_candidate_forward_shadow,
)

DEFAULT_TRADE_RECORD_ROOT = Path("knowledge_base/trade_records")
BROKER_SYMBOL_BY_CANONICAL = {
    "NAS100": "NDX100",
    "US30_cash": "US30",
    "US30": "US30",
}


@dataclass(frozen=True)
class TradeRecordCandidate:
    path: Path
    record: dict[str, Any]
    candidate_id: str
    symbol: str
    broker_symbol: str
    decision_time_utc: str
    kill_zone: str | None
    side: str | None
    framework: str | None
    final_outcome: str | None
    trade_parameters: dict[str, Any]


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


def infer_project_root(candidates_path: str | Path) -> Path:
    path = Path(candidates_path)
    if path.name == Path(STRATEGY_FOLLOW_PATH).name and path.parent.name == "shadow_logs":
        return path.parent.parent if str(path.parent.parent) else Path(".")
    return Path(".")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def candidate_ids_from_jsonl(path: Path) -> set[str]:
    return {str(row.get("candidate_id")) for row in read_jsonl(path) if row.get("candidate_id")}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _date_from_trade_record_path(path: Path) -> date | None:
    try:
        return date.fromisoformat(path.name[:10])
    except ValueError:
        return None


def _candidate_id_from_trade_record_path(path: Path) -> str | None:
    """Derive the canonical M15 candidate id from the trade-record filename.

    Live trade records are named like ``2026-05-04_ny_1315.json`` under the
    canonical-symbol directory. This lets the reconciliation path skip full JSON
    reads for candidates already present in ``strategy_follow_candidates`` while
    still opening the original decision-time record for rows that are missing.
    """
    path_date = _date_from_trade_record_path(path)
    if path_date is None:
        return None
    stem_parts = path.stem.split("_")
    hhmm = stem_parts[-1] if stem_parts else ""
    if len(hhmm) != 4 or not hhmm.isdigit():
        return None
    hour = int(hhmm[:2])
    minute = int(hhmm[2:])
    if hour > 23 or minute > 59:
        return None
    return f"{path.parent.name}_{path_date.isoformat()}T{hour:02d}:{minute:02d}:00+00:00"


def _broker_symbol(record: dict[str, Any], symbol: str) -> str:
    metadata = _safe_dict(record.get("metadata"))
    market = _safe_dict(record.get("market"))
    configured = metadata.get("broker_symbol") or metadata.get("mt5_symbol") or market.get("mt5_symbol")
    return str(configured or BROKER_SYMBOL_BY_CANONICAL.get(symbol, symbol))


def trade_record_candidate_from_record(path: Path, record: dict[str, Any]) -> TradeRecordCandidate | None:
    metadata = _safe_dict(record.get("metadata"))
    decision_pipeline = _safe_dict(record.get("decision_pipeline"))
    ai_response = _safe_dict(record.get("ai_response"))
    ai_decision = decision_pipeline.get("ai_decision") or ai_response.get("decision")
    if str(ai_decision or "").upper() != "CANDIDATE":
        return None

    symbol = str(metadata.get("symbol") or record.get("symbol") or "")
    decision_time = str(metadata.get("candle_close_utc") or ai_response.get("timestamp_utc") or "")
    if not symbol or not decision_time:
        return None

    trade_parameters = _safe_dict(ai_response.get("trade_parameters")) or _safe_dict(record.get("trade_parameters"))
    side = trade_parameters.get("direction") or decision_pipeline.get("ai_direction")
    candidate_id = f"{symbol}_{decision_time}"
    return TradeRecordCandidate(
        path=path,
        record=record,
        candidate_id=candidate_id,
        symbol=symbol,
        broker_symbol=_broker_symbol(record, symbol),
        decision_time_utc=decision_time,
        kill_zone=metadata.get("kill_zone") or ai_response.get("kill_zone"),
        side=str(side) if side is not None else None,
        framework=str(decision_pipeline.get("ai_framework") or ai_response.get("framework") or ""),
        final_outcome=decision_pipeline.get("final_outcome"),
        trade_parameters=trade_parameters,
    )


def iter_trade_record_candidates(
    trade_records_root: Path,
    *,
    include_dates: Iterable[date] | None = None,
    since_utc: datetime | None = None,
) -> tuple[list[TradeRecordCandidate], dict[str, int]]:
    include_date_set = set(include_dates or [])
    rows: list[TradeRecordCandidate] = []
    skipped: dict[str, int] = {}
    if not trade_records_root.exists():
        skipped["trade_records_root_missing"] = 1
        return rows, skipped

    for path in sorted(trade_records_root.glob("*/*.json")):
        path_date = _date_from_trade_record_path(path)
        if include_date_set and path_date is not None and path_date not in include_date_set:
            skipped["outside_include_dates"] = skipped.get("outside_include_dates", 0) + 1
            continue
        if since_utc is not None and path_date is not None and path_date < since_utc.date():
            skipped["outside_since_window"] = skipped.get("outside_since_window", 0) + 1
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            skipped["unreadable_trade_record"] = skipped.get("unreadable_trade_record", 0) + 1
            continue
        if not isinstance(record, dict):
            skipped["non_object_trade_record"] = skipped.get("non_object_trade_record", 0) + 1
            continue
        candidate = trade_record_candidate_from_record(path, record)
        if candidate is None:
            skipped["not_ai_candidate_record"] = skipped.get("not_ai_candidate_record", 0) + 1
            continue
        decision_dt = parse_utc(candidate.decision_time_utc)
        if decision_dt is None:
            skipped["missing_parseable_decision_time"] = skipped.get("missing_parseable_decision_time", 0) + 1
            continue
        if include_date_set and decision_dt.date() not in include_date_set:
            skipped["outside_include_dates"] = skipped.get("outside_include_dates", 0) + 1
            continue
        if since_utc is not None and decision_dt < since_utc:
            skipped["outside_since_window"] = skipped.get("outside_since_window", 0) + 1
            continue
        rows.append(candidate)
    return rows, skipped


def sync_trade_record_candidates(
    *,
    candidates_path: str | Path = STRATEGY_FOLLOW_PATH,
    trade_records_root: str | Path | None = None,
    max_hours: float | None = 12.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append missing live candidate shadow rows from saved trade records."""
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    candidates = Path(candidates_path)
    project_root = infer_project_root(candidates)
    if not candidates.is_absolute():
        candidates = project_root / candidates
    root = Path(trade_records_root) if trade_records_root is not None else project_root / DEFAULT_TRADE_RECORD_ROOT
    since = now_utc - timedelta(hours=max_hours) if max_hours is not None else None

    existing_ids = candidate_ids_from_jsonl(candidates)
    trade_record_candidates: list[TradeRecordCandidate] = []
    skipped: dict[str, int] = {}
    if not root.exists():
        skipped["trade_records_root_missing"] = 1
    else:
        for path in sorted(root.glob("*/*.json")):
            path_date = _date_from_trade_record_path(path)
            if since is not None and path_date is not None and path_date < since.date():
                skipped["outside_since_window"] = skipped.get("outside_since_window", 0) + 1
                continue
            inferred_candidate_id = _candidate_id_from_trade_record_path(path)
            if inferred_candidate_id and inferred_candidate_id in existing_ids:
                skipped["candidate_already_shadowed_by_filename"] = (
                    skipped.get("candidate_already_shadowed_by_filename", 0) + 1
                )
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                skipped["unreadable_trade_record"] = skipped.get("unreadable_trade_record", 0) + 1
                continue
            if not isinstance(record, dict):
                skipped["non_object_trade_record"] = skipped.get("non_object_trade_record", 0) + 1
                continue
            candidate = trade_record_candidate_from_record(path, record)
            if candidate is None:
                skipped["not_ai_candidate_record"] = skipped.get("not_ai_candidate_record", 0) + 1
                continue
            decision_dt = parse_utc(candidate.decision_time_utc)
            if decision_dt is None:
                skipped["missing_parseable_decision_time"] = skipped.get("missing_parseable_decision_time", 0) + 1
                continue
            if since is not None and decision_dt < since:
                skipped["outside_since_window"] = skipped.get("outside_since_window", 0) + 1
                continue
            trade_record_candidates.append(candidate)
    records_by_candidate_id: dict[str, list[TradeRecordCandidate]] = defaultdict(list)
    for candidate in trade_record_candidates:
        records_by_candidate_id[candidate.candidate_id].append(candidate)
    ambiguous_candidate_ids = {
        candidate_id: rows
        for candidate_id, rows in records_by_candidate_id.items()
        if len(rows) > 1
    }
    if ambiguous_candidate_ids:
        skipped["ambiguous_candidate_id_collision"] = sum(
            len(rows) for rows in ambiguous_candidate_ids.values()
        )

    written: list[str] = []
    duplicate: list[str] = []
    ambiguous: list[dict[str, Any]] = []
    for candidate in trade_record_candidates:
        collision_rows = ambiguous_candidate_ids.get(candidate.candidate_id)
        if collision_rows:
            if not any(item["candidate_id"] == candidate.candidate_id for item in ambiguous):
                ambiguous.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "source_files": [str(row.path) for row in collision_rows],
                    }
                )
            continue
        if candidate.candidate_id in existing_ids:
            duplicate.append(candidate.candidate_id)
            continue
        decision_pipeline = _safe_dict(candidate.record.get("decision_pipeline"))
        record_with_source = {
            **candidate.record,
            "_source_file": str(candidate.path),
        }
        record_live_candidate_forward_shadow(
            symbol=candidate.symbol,
            broker_symbol=candidate.broker_symbol,
            source_symbol=None,
            kill_zone=candidate.kill_zone,
            analysis=_safe_dict(candidate.record.get("ai_response")),
            mso=_safe_dict(candidate.record.get("mso")),
            record=record_with_source,
            verification=_safe_dict(decision_pipeline.get("level2_verification")),
            final_outcome=candidate.final_outcome,
            trade_id=None,
            log_root=project_root,
        )
        existing_ids.add(candidate.candidate_id)
        written.append(candidate.candidate_id)

    return {
        "status": "OK",
        "candidates_path": str(candidates),
        "trade_records_root": str(root),
        "trade_records_seen": len(trade_record_candidates),
        "rows_written": len(written),
        "written_candidate_ids": written,
        "duplicate_existing_candidate_ids": duplicate,
        "ambiguous_candidate_id_collisions": ambiguous,
        "skipped": dict(sorted(skipped.items())),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
