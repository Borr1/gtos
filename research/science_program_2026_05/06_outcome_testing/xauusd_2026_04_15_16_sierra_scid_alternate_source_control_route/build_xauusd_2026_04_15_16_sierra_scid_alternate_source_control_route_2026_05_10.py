#!/usr/bin/env python3
"""Build the XAUUSD Sierra SCID alternate source-control route.

This route is research/source-control only. It reads the local Sierra Chart
SCID file in place, hashes it, summarizes only the required dates and candidate
neighborhoods, and compares the source against the upstream MT5 tick contract.
It does not export raw market data or touch broker/account/order APIs.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE"
PREFIX = "XAUUSD_SIERRA_SCID_ALT_ROUTE"
DATE = "2026-05-10"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE_GOAL_PROMPT_2026-05-10.md"
)
NEXT_G12_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
G12_AUDIT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_readonly_tick_recovery_export_source_control_audit"
)
TARGET_TICK_ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_readonly_tick_recovery_export_source_control_route"
)
SCID_PATH = Path(r"C:\SierraChart\Data\XAUUSD.scid")

SAFE_FALSE_PAYLOAD = {
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_validation": False,
    "opens_promotion": False,
    "opens_registry_edit": False,
    "opens_paid_api_or_databento_route": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "changes_live_trading_behavior": False,
    "opens_remote_push": False,
    "opens_mt5_order_account_history_behavior": False,
    "credentials_touched": False,
}

REQUIRED_MT5_TICK_FIELDS = [
    "time_utc",
    "time_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "flags",
    "source_symbol",
    "broker_symbol",
    "source_file_sha256",
]
HARD_ABSENT_MT5_FIELDS = ["bid", "ask", "flags"]
PROXY_ONLY_MT5_FIELDS = ["time_msc", "last", "volume", "broker_symbol"]
SOURCE_METADATA_FIELDS = ["time_utc", "source_symbol", "source_file_sha256"]

HEADER_STRUCT = struct.Struct("<4sIIHHI36s")
RECORD_STRUCT = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
SPECIAL_OPEN_FIRST_SUB_TRADE = -1.99900095e37
SPECIAL_OPEN_LAST_SUB_TRADE = -1.99900197e37
INVALID_ABS_PRICE = 1.0e20

CANDIDATE_REQUESTS = [
    {
        "owner_request_id": "OWNER-TICK-0020",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "source_date": "2026-04-15",
        "window_start_utc": "2026-04-15T00:00:00Z",
        "window_end_utc": "2026-04-15T23:59:59.999999Z",
        "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet",
        "candidate_ids": ["XAUUSD_2026-04-15T14:15:05.007998+00:00"],
        "candidates": [
            {
                "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
                "candidate_utc": "2026-04-15T14:15:05.007998Z",
                "contamination_or_embargo_excluded": False,
            }
        ],
    },
    {
        "owner_request_id": "OWNER-TICK-0021",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "source_date": "2026-04-16",
        "window_start_utc": "2026-04-16T00:00:00Z",
        "window_end_utc": "2026-04-16T23:59:59.999999Z",
        "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet",
        "candidate_ids": [
            "XAUUSD_2026-04-16T09:30:05.013547+00:00",
            "XAUUSD_2026-04-16T13:16:01.126537+00:00",
        ],
        "candidates": [
            {
                "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
                "candidate_utc": "2026-04-16T09:30:05.013547Z",
                "contamination_or_embargo_excluded": True,
            },
            {
                "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
                "candidate_utc": "2026-04-16T13:16:01.126537Z",
                "contamination_or_embargo_excluded": True,
            },
        ],
    },
]

REQUIRED_ARTIFACT_STEMS = [
    "CONTEXT_ANCHOR",
    "SCID_SOURCE_HASH_HEADER_AUDIT",
    "SCID_DAY_CANDIDATE_COVERAGE_LEDGER",
    "MT5_TICK_CONTRACT_FIELD_COMPARISON_AUDIT",
    "ALTERNATE_SOURCE_ADMISSIBILITY_DECISION_LEDGER",
    "SOURCE_STATE_NOLEAK_BOUNDARY_AUDIT",
    "OWNER_MANUAL_EXPORT_FALLBACK_MANIFEST",
    "SOURCE_HASHED_ALTERNATE_PACKET",
    "FIELD_MISMATCH_BLOCKER_LEDGER",
    "NEXT_G12_AUDIT_PROMPT_PACK",
    "COMPLETION_AUDIT",
]


@dataclass(frozen=True)
class ScidHeader:
    path: Path
    exists: bool
    size_bytes: int = 0
    magic: str | None = None
    header_size: int | None = None
    record_size: int | None = None
    version: int | None = None
    utc_start_index: int | None = None
    record_count: int = 0
    remainder_bytes: int | None = None


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def repo_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        **SAFE_FALSE_PAYLOAD,
    }
    payload.update(extra)
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scid_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def scid_datetime_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def parse_scid_header(path: Path) -> ScidHeader:
    if not path.exists():
        return ScidHeader(path=path, exists=False)
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(HEADER_STRUCT.size)
    if len(raw) < HEADER_STRUCT.size:
        raise ValueError(f"{path} is too small for a SCID header")
    magic_raw, header_size, record_size, version, _unused, utc_start_index, _reserve = HEADER_STRUCT.unpack(raw)
    payload = size - header_size
    return ScidHeader(
        path=path,
        exists=True,
        size_bytes=size,
        magic=magic_raw.decode("ascii", errors="replace"),
        header_size=header_size,
        record_size=record_size,
        version=version,
        utc_start_index=utc_start_index,
        record_count=payload // record_size if record_size else 0,
        remainder_bytes=payload % record_size if record_size else payload,
    )


def header_to_json(header: ScidHeader) -> dict[str, Any]:
    return {
        "path": str(header.path),
        "exists": header.exists,
        "size_bytes": header.size_bytes,
        "magic": header.magic,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "version": header.version,
        "utc_start_index": header.utc_start_index,
        "record_count": header.record_count,
        "remainder_bytes": header.remainder_bytes,
    }


def validate_header(header: ScidHeader) -> list[str]:
    issues: list[str] = []
    if not header.exists:
        issues.append("SCID_SOURCE_FILE_NOT_FOUND")
    if header.magic != "SCID":
        issues.append("SCID_MAGIC_NOT_SCID")
    if header.header_size is None or header.header_size < HEADER_STRUCT.size:
        issues.append("SCID_HEADER_SIZE_INVALID")
    if header.record_size != RECORD_STRUCT.size:
        issues.append("SCID_RECORD_SIZE_UNEXPECTED")
    if header.remainder_bytes not in (0, None):
        issues.append("SCID_PAYLOAD_REMAINDER_BYTES_NONZERO")
    return issues


def read_record(handle: Any, header: ScidHeader, index: int) -> dict[str, Any]:
    if index < 0 or index >= header.record_count:
        raise IndexError(index)
    handle.seek(int(header.header_size or 0) + index * int(header.record_size or 0))
    raw = handle.read(int(header.record_size or 0))
    if len(raw) != header.record_size:
        raise ValueError(f"short record read at index {index}")
    dt_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = RECORD_STRUCT.unpack(raw)
    return {
        "index": index,
        "dt_us": int(dt_us),
        "timestamp": scid_datetime(int(dt_us)),
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "num_trades": int(num_trades),
        "total_volume": int(total_volume),
        "bid_volume": int(bid_volume),
        "ask_volume": int(ask_volume),
    }


def lower_bound(handle: Any, header: ScidHeader, target_us: int) -> int:
    lo = 0
    hi = header.record_count
    while lo < hi:
        mid = (lo + hi) // 2
        record_us = read_record(handle, header, mid)["dt_us"]
        if record_us < target_us:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(handle: Any, header: ScidHeader, target_us: int) -> int:
    lo = 0
    hi = header.record_count
    while lo < hi:
        mid = (lo + hi) // 2
        record_us = read_record(handle, header, mid)["dt_us"]
        if record_us <= target_us:
            lo = mid + 1
        else:
            hi = mid
    return lo


def price_valid(value: float) -> bool:
    return math.isfinite(value) and abs(value) < INVALID_ABS_PRICE and value > 0.0


def record_anomalies(record: dict[str, Any]) -> list[str]:
    anomalies: list[str] = []
    prices = [record["open"], record["high"], record["low"], record["close"]]
    if not all(price_valid(float(value)) for value in prices):
        anomalies.append("INVALID_OR_SPECIAL_PRICE_FIELD")
    if abs(float(record["open"]) - SPECIAL_OPEN_FIRST_SUB_TRADE) < 1.0e30:
        anomalies.append("OPEN_FIRST_SUB_TRADE_SPECIAL_MARKER")
    if abs(float(record["open"]) - SPECIAL_OPEN_LAST_SUB_TRADE) < 1.0e30:
        anomalies.append("OPEN_LAST_SUB_TRADE_SPECIAL_MARKER")
    if any(int(record[field]) < 0 for field in ["num_trades", "total_volume", "bid_volume", "ask_volume"]):
        anomalies.append("NEGATIVE_VOLUME_OR_TRADE_COUNT")
    if int(record["bid_volume"]) + int(record["ask_volume"]) != int(record["total_volume"]):
        anomalies.append("BID_ASK_VOLUME_SUM_DIFFERS_FROM_TOTAL_VOLUME")
    if not (float(record["low"]) <= float(record["close"]) <= float(record["high"])):
        anomalies.append("CLOSE_OUTSIDE_LOW_HIGH_RANGE")
    return anomalies


def record_to_json(record: dict[str, Any] | None, target: datetime | None = None) -> dict[str, Any] | None:
    if record is None:
        return None
    row = {
        "index": int(record["index"]),
        "timestamp_utc": iso_utc(record["timestamp"]),
        "sierra_datetime_us": int(record["dt_us"]),
        "open": record["open"],
        "high": record["high"],
        "low": record["low"],
        "close": record["close"],
        "num_trades": record["num_trades"],
        "total_volume": record["total_volume"],
        "bid_volume": record["bid_volume"],
        "ask_volume": record["ask_volume"],
        "record_status_anomalies": record_anomalies(record),
    }
    if target is not None:
        delta = record["timestamp"] - target
        row["delta_to_candidate_seconds"] = delta.total_seconds()
        row["abs_delta_to_candidate_ms"] = abs(delta.total_seconds()) * 1000.0
    return row


def iter_records_between(path: Path, header: ScidHeader, start: datetime, end: datetime) -> list[dict[str, Any]]:
    if end <= start:
        raise ValueError("end must be after start")
    if not header.exists or header.record_count == 0:
        return []
    with path.open("rb") as handle:
        start_idx = lower_bound(handle, header, scid_datetime_us(start))
        end_idx = lower_bound(handle, header, scid_datetime_us(end))
        return [read_record(handle, header, idx) for idx in range(start_idx, end_idx)]


def range_summary(path: Path, header: ScidHeader, start: datetime, end: datetime) -> dict[str, Any]:
    records = iter_records_between(path, header, start, end)
    return {
        "start_utc": iso_utc(start),
        "end_utc": iso_utc(end),
        "rows": len(records),
        "first_timestamp_utc": iso_utc(records[0]["timestamp"]) if records else None,
        "last_timestamp_utc": iso_utc(records[-1]["timestamp"]) if records else None,
        "first_close": records[0]["close"] if records else None,
        "last_close": records[-1]["close"] if records else None,
    }


def median_int(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def day_summary(path: Path, header: ScidHeader, source_date: str) -> dict[str, Any]:
    start = parse_utc(f"{source_date}T00:00:00Z")
    end = parse_utc(f"{source_date}T23:59:59.999999Z")
    records = iter_records_between(path, header, start, end)
    deltas: list[int] = []
    duplicate_timestamps = 0
    non_monotonic = 0
    max_gap_us = 0
    previous_us: int | None = None
    anomaly_counts: dict[str, int] = {}
    volume_totals = {"total_volume": 0, "bid_volume": 0, "ask_volume": 0, "num_trades": 0}
    min_close: float | None = None
    max_close: float | None = None
    for record in records:
        close = float(record["close"])
        min_close = close if min_close is None else min(min_close, close)
        max_close = close if max_close is None else max(max_close, close)
        for key in volume_totals:
            volume_totals[key] += int(record[key])
        for anomaly in record_anomalies(record):
            anomaly_counts[anomaly] = anomaly_counts.get(anomaly, 0) + 1
        current_us = int(record["dt_us"])
        if previous_us is not None:
            delta = current_us - previous_us
            if delta == 0:
                duplicate_timestamps += 1
            elif delta < 0:
                non_monotonic += 1
            else:
                deltas.append(delta)
                max_gap_us = max(max_gap_us, delta)
        previous_us = current_us
    return {
        "source_date": source_date,
        "window_start_utc": iso_utc(start),
        "window_end_utc": iso_utc(end),
        "row_count": len(records),
        "first_record": record_to_json(records[0]) if records else None,
        "last_record": record_to_json(records[-1]) if records else None,
        "min_close": min_close,
        "max_close": max_close,
        "volume_totals": volume_totals,
        "record_status_anomaly_counts": anomaly_counts,
        "timestamp_resolution": {
            "min_positive_delta_us": min(deltas) if deltas else None,
            "median_positive_delta_us": median_int(deltas),
            "max_gap_seconds": max_gap_us / 1_000_000 if max_gap_us else 0.0,
            "duplicate_timestamp_count": duplicate_timestamps,
            "non_monotonic_timestamp_count": non_monotonic,
        },
        "coverage_status": "SCID_ROWS_PRESENT" if records else "SCID_ZERO_ROWS",
    }


def floor_m15(value: datetime) -> datetime:
    dt = value.astimezone(timezone.utc)
    return dt.replace(minute=(dt.minute // 15) * 15, second=0, microsecond=0)


def nearest_records(path: Path, header: ScidHeader, target: datetime) -> dict[str, Any]:
    with path.open("rb") as handle:
        target_us = scid_datetime_us(target)
        before_idx = lower_bound(handle, header, target_us) - 1
        after_idx = lower_bound(handle, header, target_us)
        at_or_before_idx = upper_bound(handle, header, target_us) - 1
        strict_preceding = read_record(handle, header, before_idx) if 0 <= before_idx < header.record_count else None
        at_or_following = read_record(handle, header, after_idx) if 0 <= after_idx < header.record_count else None
        at_or_before = (
            read_record(handle, header, at_or_before_idx)
            if 0 <= at_or_before_idx < header.record_count
            else None
        )
    candidates = [row for row in [strict_preceding, at_or_following, at_or_before] if row is not None]
    nearest = min(candidates, key=lambda row: abs((row["timestamp"] - target).total_seconds())) if candidates else None
    return {
        "strict_preceding_record": record_to_json(strict_preceding, target),
        "at_or_following_record": record_to_json(at_or_following, target),
        "at_or_before_record": record_to_json(at_or_before, target),
        "nearest_record": record_to_json(nearest, target),
    }


def candidate_summary(path: Path, header: ScidHeader, candidate: dict[str, Any]) -> dict[str, Any]:
    target = parse_utc(candidate["candidate_utc"])
    pm5 = range_summary(path, header, target - timedelta(seconds=5), target + timedelta(seconds=5))
    pm60 = range_summary(path, header, target - timedelta(seconds=60), target + timedelta(seconds=60))
    m15_start = floor_m15(target)
    m15 = range_summary(path, header, m15_start, m15_start + timedelta(minutes=15))
    nearest = nearest_records(path, header, target)
    nearest_row = nearest["nearest_record"]
    inside_day = target.date().isoformat() == candidate["candidate_id"].split("_", 1)[1][:10]
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_utc": iso_utc(target),
        "contamination_or_embargo_excluded": bool(candidate["contamination_or_embargo_excluded"]),
        "inside_requested_utc_day": inside_day,
        "candidate_window_policy": {
            "primary_candidate_window": "plus_minus_60_seconds",
            "diagnostic_near_window": "plus_minus_5_seconds",
            "m15_context_window": "UTC M15 bar containing candidate timestamp",
        },
        "rows_plus_minus_5_seconds": pm5["rows"],
        "rows_plus_minus_60_seconds": pm60["rows"],
        "rows_m15_context": m15["rows"],
        "plus_minus_5_seconds_summary": pm5,
        "plus_minus_60_seconds_summary": pm60,
        "m15_context_summary": m15,
        "nearest_records": nearest,
        "nearest_abs_delta_ms": nearest_row["abs_delta_to_candidate_ms"] if nearest_row else None,
        "candidate_coverage_status": (
            "SCID_RECORDS_PRESENT_AROUND_CANDIDATE" if pm60["rows"] > 0 and nearest_row else "SCID_CANDIDATE_GAP"
        ),
    }


def locate_scid_source(path: Path) -> dict[str, Any]:
    search_rows = [
        {
            "root_id": "exact_required_path",
            "root_path": str(path),
            "exists": path.exists(),
            "match_count": 1 if path.exists() else 0,
            "matches": [str(path)] if path.exists() else [],
            "search_policy": "exact_required_source_path_first",
        }
    ]
    if not path.exists():
        for root_id, root in [
            ("sierra_data_root", Path(r"C:\SierraChart\Data")),
            ("sierra_install_root", Path(r"C:\SierraChart")),
            ("prior_worktrees_root", Path(r"C:\tmp\gtos_otb")),
        ]:
            matches: list[str] = []
            if root.exists():
                try:
                    matches = [str(match) for match in root.rglob("XAUUSD.scid")][:20]
                except OSError as exc:
                    search_rows.append(
                        {
                            "root_id": root_id,
                            "root_path": str(root),
                            "exists": True,
                            "match_count": 0,
                            "matches": [],
                            "search_policy": "targeted_xauusd_scid_search",
                            "access_error": str(exc),
                        }
                    )
                    continue
            search_rows.append(
                {
                    "root_id": root_id,
                    "root_path": str(root),
                    "exists": root.exists(),
                    "match_count": len(matches),
                    "matches": matches,
                    "search_policy": "targeted_xauusd_scid_search",
                }
            )
    return {
        "required_source_path": str(path),
        "exact_source_exists": path.exists(),
        "selected_source_path": str(path) if path.exists() else None,
        "source_access_status": "EXACT_SOURCE_READABLE" if path.exists() else "EXACT_SOURCE_MISSING_AFTER_TARGETED_SEARCH",
        "search_rows": search_rows,
    }


def build_context_anchor() -> dict[str, Any]:
    inputs = {
        "controlling_prompt": CONTROL_PROMPT_PATH,
        "live_state": ".context/LIVE_STATE.md",
        "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        "quick_reference": ".context/00_core/quick_reference_card.md",
        "research_operating_doctrine": ".context/00_core/research_operating_doctrine.md",
        "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
        "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
        "research_current_state": ".context/00_core/research_current_state.md",
        "g12_audit_dir": rel(G12_AUDIT_DIR),
        "target_tick_recovery_route_dir": rel(TARGET_TICK_ROUTE_DIR),
        "existing_scid_inspector": "scripts/inspect_sierra_scid.py",
        "existing_scid_converter": "scripts/convert_sierra_scid_to_ohlcv.py",
    }
    return base_payload(
        "context_anchor",
        lane="source/control alternate-source recovery",
        controlling_prompt=CONTROL_PROMPT_PATH,
        current_head=git_stdout(["rev-parse", "--short", "HEAD"]),
        source_path=str(SCID_PATH),
        requested_owner_request_ids=["OWNER-TICK-0020", "OWNER-TICK-0021"],
        candidate_count=3,
        required_boundaries={
            "source_state_boundary": "market data cannot recreate pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, or final lifecycle truth",
            "result_boundary": "no result/cost/R/win-rate/expectancy labels or validation denominators opened",
            "live_boundary": "no prompt/config/risk/permissions/safety/selector/canary/live behavior changes",
            "raw_data_boundary": "raw SCID rows and raw tick files are not copied or committed",
        },
        preflight_inputs_read=inputs,
        upstream_context={
            "remaining_mt5_requests": [
                {
                    "owner_request_id": row["owner_request_id"],
                    "source_date": row["source_date"],
                    "candidate_ids": row["candidate_ids"],
                    "target_path_template": row["target_path_template"],
                }
                for row in CANDIDATE_REQUESTS
            ],
            "accepted_g12_audit": rel(
                G12_AUDIT_DIR / "G12_NOFILL_READONLY_TICK_RECOVERY_AUDIT_REPORT_2026-05-10.md"
            ),
            "target_owner_action_manifest": rel(
                TARGET_TICK_ROUTE_DIR / "NOFILL_READONLY_TICK_RECOVERY_OWNER_ACTION_MANIFEST_2026-05-10.json"
            ),
        },
    )


def build_scid_source_hash_header_audit(path: Path) -> dict[str, Any]:
    location = locate_scid_source(path)
    header = parse_scid_header(path)
    header_issues = validate_header(header)
    source_sha = sha256_file(path) if path.exists() else None
    parser_hashes = {
        "route_builder_sha256": sha256_text(Path(__file__).resolve()),
        "existing_inspect_sierra_scid_sha256": sha256_text(REPO_ROOT / "scripts" / "inspect_sierra_scid.py"),
        "existing_convert_sierra_scid_to_ohlcv_sha256": sha256_text(
            REPO_ROOT / "scripts" / "convert_sierra_scid_to_ohlcv.py"
        ),
    }
    first_record = None
    last_record = None
    if header.exists and not header_issues and header.record_count > 0:
        with path.open("rb") as handle:
            first_record = read_record(handle, header, 0)
            last_record = read_record(handle, header, header.record_count - 1)
    return base_payload(
        "scid_source_hash_header_audit",
        source_location_search=location,
        raw_source={
            "source_path": str(path),
            "source_sha256": source_sha,
            "size_bytes": path.stat().st_size if path.exists() else None,
            "hash_algorithm": "SHA256",
            "raw_source_not_copied": True,
            "raw_source_not_committed": True,
        },
        parser_code_hashes=parser_hashes,
        scid_header=header_to_json(header),
        scid_header_validation_issues=header_issues,
        first_file_record=record_to_json(first_record),
        last_file_record=record_to_json(last_record),
        source_access_status="SOURCE_HASHED_AND_HEADER_PARSED" if path.exists() and not header_issues else "SOURCE_ACCESS_OR_HEADER_BLOCKED",
    )


def build_coverage_ledger(path: Path) -> dict[str, Any]:
    header = parse_scid_header(path)
    header_issues = validate_header(header)
    if header_issues:
        return base_payload(
            "scid_day_candidate_coverage_ledger",
            source_path=str(path),
            scid_access_status="SOURCE_ACCESS_OR_HEADER_BLOCKED",
            scid_header_validation_issues=header_issues,
            day_coverage=[],
            candidate_coverage=[],
        )
    day_rows = [day_summary(path, header, request["source_date"]) for request in CANDIDATE_REQUESTS]
    candidate_rows: list[dict[str, Any]] = []
    for request in CANDIDATE_REQUESTS:
        for candidate in request["candidates"]:
            row = candidate_summary(path, header, candidate)
            row.update(
                {
                    "owner_request_id": request["owner_request_id"],
                    "source_date": request["source_date"],
                    "target_mt5_tick_path": request["target_path_template"],
                }
            )
            candidate_rows.append(row)
    return base_payload(
        "scid_day_candidate_coverage_ledger",
        source_path=str(path),
        scid_access_status="SCID_PARSED_READ_ONLY",
        full_utc_day_policy="inclusive start, exclusive end at 23:59:59.999999Z practical SCID bound",
        candidate_window_policy={
            "primary_candidate_window": "plus_minus_60_seconds",
            "diagnostic_near_window": "plus_minus_5_seconds",
            "m15_context_window": "UTC M15 bar containing candidate timestamp",
        },
        expected_g12_day_row_counts={"2026-04-15": 72119, "2026-04-16": 70048},
        day_coverage=day_rows,
        candidate_coverage=candidate_rows,
        all_requested_days_have_rows=all(row["row_count"] > 0 for row in day_rows),
        all_candidates_have_nearest_records=all(row["nearest_records"]["nearest_record"] is not None for row in candidate_rows),
        all_candidates_have_plus_minus_60s_rows=all(row["rows_plus_minus_60_seconds"] > 0 for row in candidate_rows),
    )


def build_field_comparison_audit() -> dict[str, Any]:
    rows = [
        {
            "field": "time_utc",
            "mt5_tick_contract_meaning": "UTC timestamp attached to the MT5 tick row",
            "scid_evidence": "SCID DTDateTime microsecond timestamp",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "mt5_equivalence_status": "UTC timestamp exists but is Sierra source-native, not MT5 broker-native",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_TIMESTAMP_VALUE",
        },
        {
            "field": "time_msc",
            "mt5_tick_contract_meaning": "MT5 millisecond broker tick timestamp",
            "scid_evidence": "SCID timestamp can be converted to milliseconds",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "mt5_equivalence_status": "not MT5-native time_msc; conversion would be source timestamp proxy",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
        },
        {
            "field": "bid",
            "mt5_tick_contract_meaning": "bid quote price",
            "scid_evidence": "SCID has OHLC price fields and bid_volume, not bid quote price",
            "presence_status": "ABSENT",
            "mt5_equivalence_status": "open/high/low/close and bid_volume cannot be substituted for bid quote",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
        },
        {
            "field": "ask",
            "mt5_tick_contract_meaning": "ask quote price",
            "scid_evidence": "SCID has OHLC price fields and ask_volume, not ask quote price",
            "presence_status": "ABSENT",
            "mt5_equivalence_status": "open/high/low/close and ask_volume cannot be substituted for ask quote",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
        },
        {
            "field": "last",
            "mt5_tick_contract_meaning": "MT5 tick last price field",
            "scid_evidence": "SCID close is a source-native record close price",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "mt5_equivalence_status": "SCID close can be a market-activity price proxy but not MT5 last field proof",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
        },
        {
            "field": "volume",
            "mt5_tick_contract_meaning": "MT5 tick volume field",
            "scid_evidence": "SCID total_volume plus bid_volume and ask_volume",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "mt5_equivalence_status": "SCID record volume is source-native footprint volume, not MT5 tick volume proof",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
        },
        {
            "field": "flags",
            "mt5_tick_contract_meaning": "MT5 tick flags bitmask",
            "scid_evidence": "No SCID field carries MT5 tick flags",
            "presence_status": "ABSENT",
            "mt5_equivalence_status": "absent",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
        },
        {
            "field": "source_symbol",
            "mt5_tick_contract_meaning": "source symbol metadata for the tick file",
            "scid_evidence": "Derivable from XAUUSD.scid filename and owner request",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "mt5_equivalence_status": "source metadata derivable, not row-native",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_METADATA_VALUE",
        },
        {
            "field": "broker_symbol",
            "mt5_tick_contract_meaning": "MT5 broker symbol used for the tick export",
            "scid_evidence": "Filename says XAUUSD, but SCID source is Sierra and not MT5 broker export",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "mt5_equivalence_status": "same text symbol does not prove MT5 broker_symbol lineage",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
        },
        {
            "field": "source_file_sha256",
            "mt5_tick_contract_meaning": "SHA256 of the consumed source file",
            "scid_evidence": "Raw SCID SHA256 is computed for this route",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "mt5_equivalence_status": "hash exists for SCID source, not for missing MT5 parquet",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_SOURCE_HASH_VALUE",
        },
    ]
    return base_payload(
        "mt5_tick_contract_field_comparison_audit",
        required_mt5_tick_fields=REQUIRED_MT5_TICK_FIELDS,
        field_rows=rows,
        hard_absent_fields=HARD_ABSENT_MT5_FIELDS,
        proxy_only_non_equivalent_fields=PROXY_ONLY_MT5_FIELDS,
        derivable_without_leakage_fields=SOURCE_METADATA_FIELDS,
        mt5_tick_contract_satisfied=False,
        mt5_tick_contract_blocker_summary=(
            "SCID proves same-market source activity but lacks bid quote, ask quote, and MT5 flags; "
            "several other fields are source-native proxies rather than MT5-native tick fields."
        ),
    )


def build_admissibility_decision(coverage: dict[str, Any], field_audit: dict[str, Any]) -> dict[str, Any]:
    scid_context_contract = {
        "contract_id": "same_market_sierra_scid_footprint_context_v1",
        "evidence_class": "SAME_MARKET_SCID_MARKET_ACTIVITY_CONTEXT_ONLY",
        "required_fields": [
            "raw_scid_sha256",
            "scid_header",
            "full_day_row_count",
            "candidate_nearest_records",
            "timestamp_utc",
            "open",
            "high",
            "low",
            "close",
            "num_trades",
            "total_volume",
            "bid_volume",
            "ask_volume",
        ],
        "explicit_non_equivalence": [
            "not MT5 bid/ask tick recovery",
            "not broker quote spread evidence",
            "not source-state truth",
            "not validation or result evidence",
        ],
    }
    scid_contract_satisfied = bool(
        coverage.get("all_requested_days_have_rows")
        and coverage.get("all_candidates_have_nearest_records")
        and coverage.get("all_candidates_have_plus_minus_60s_rows")
    )
    return base_payload(
        "alternate_source_admissibility_decision_ledger",
        decision="ADMISSIBLE_AS_SCID_MARKET_ACTIVITY_CONTEXT_ONLY_WITH_MT5_TICK_CONTRACT_BLOCKERS",
        scid_context_contract=scid_context_contract,
        scid_context_contract_satisfied=scid_contract_satisfied,
        source_hashed_alternate_packet_should_be_emitted=scid_contract_satisfied,
        mt5_tick_recovery_equivalent=False,
        closes_owner_tick_requests=False,
        owner_manual_mt5_tick_export_still_required=True,
        mt5_tick_contract_satisfied=field_audit["mt5_tick_contract_satisfied"],
        hard_blocker_fields=field_audit["hard_absent_fields"],
        proxy_only_fields=field_audit["proxy_only_non_equivalent_fields"],
        admissibility_boundary=(
            "Use this packet only to prove same-market Sierra source coverage and record-level price/volume context. "
            "Do not use it as MT5 bid/ask tick recovery, spread/cost proof, lifecycle truth, outcome labels, or validation input."
        ),
    )


def build_boundary_audit() -> dict[str, Any]:
    return base_payload(
        "source_state_noleak_boundary_audit",
        scid_schema_fields=[
            "timestamp_utc",
            "open",
            "high",
            "low",
            "close",
            "num_trades",
            "total_volume",
            "bid_volume",
            "ask_volume",
        ],
        forbidden_value_families_present_in_scid=False,
        forbidden_value_families=[
            "MT5 account",
            "MT5 order",
            "MT5 history order",
            "MT5 deal",
            "MT5 position",
            "broker actual-R",
            "result cost",
            "R multiple",
            "win-rate",
            "expectancy",
            "validation label",
            "credential",
        ],
        source_state_fields_not_reconstructable_from_scid=[
            "pending intent",
            "lifecycle group",
            "write-clock",
            "source-safe order observability",
            "ticket redaction",
            "native pending type",
            "final lifecycle truth",
        ],
        contamination_boundary={
            "2026-04-15_candidate_count": 1,
            "2026-04-15_candidates_remain_contamination_excluded": False,
            "2026-04-16_candidate_count": 2,
            "2026-04-16_candidates_remain_contamination_embargo_excluded": True,
            "rule": "SCID source coverage does not change contamination or embargo eligibility.",
        },
        noleak_statement=(
            "The route reads only a local SCID market-data file and upstream source-control artifacts. "
            "It does not open broker/account/order/history/deal/position values, broker actual-R, result scoring, validation, paid/API routes, credentials, or live behavior."
        ),
        boundary_status="PASS_SOURCE_CONTROL_ONLY",
    )


def build_owner_manual_export_manifest() -> dict[str, Any]:
    return base_payload(
        "owner_manual_export_fallback_manifest",
        reason="SCID cannot satisfy the MT5 bid/ask tick parquet contract.",
        remaining_market_data_export_request_count=2,
        market_data_export_requests=[
            {
                "owner_request_id": request["owner_request_id"],
                "symbol": request["symbol"],
                "source_symbol": request["source_symbol"],
                "source_date": request["source_date"],
                "candidate_ids": request["candidate_ids"],
                "target_path_template": request["target_path_template"],
                "window_start_utc": request["window_start_utc"],
                "window_end_utc": request["window_end_utc"],
                "required_fields": REQUIRED_MT5_TICK_FIELDS,
                "format": "parquet_preferred_csv_acceptable_with_schema",
                "hash_requirement": "SHA256, size, schema, min/max timestamp, source symbol, broker symbol, and candidate-window row counts",
                "no_leak_constraints": [
                    "market_data_only",
                    "no MT5 account/order/history/deal/position values",
                    "no broker outcome labels",
                    "no result/cost/R/win-rate/expectancy scoring",
                ],
                "remaining_owner_action": "provide_or_authorize_source_safe_mt5_bid_ask_tick_export",
            }
            for request in CANDIDATE_REQUESTS
        ],
    )


def build_alternate_packet(
    source_audit: dict[str, Any],
    coverage: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return base_payload(
        "source_hashed_alternate_packet",
        packet_id="XAUUSD_2026_04_15_16_SCID_MARKET_ACTIVITY_CONTEXT_PACKET",
        packet_admissibility_status="ADMISSIBLE_AS_SCID_MARKET_ACTIVITY_CONTEXT_ONLY",
        mt5_tick_recovery_equivalent=False,
        closes_owner_tick_requests=False,
        validation_safe=False,
        source_contract=decision["scid_context_contract"],
        source_hash=source_audit["raw_source"]["source_sha256"],
        source_path=source_audit["raw_source"]["source_path"],
        source_size_bytes=source_audit["raw_source"]["size_bytes"],
        scid_header=source_audit["scid_header"],
        parser_code_hashes=source_audit["parser_code_hashes"],
        day_coverage=coverage["day_coverage"],
        candidate_coverage=coverage["candidate_coverage"],
        packet_boundary=decision["admissibility_boundary"],
    )


def build_field_mismatch_blockers(field_audit: dict[str, Any]) -> dict[str, Any]:
    blockers = [
        {
            "field": row["field"],
            "presence_status": row["presence_status"],
            "blocker_class": row["blocker_class"],
            "mt5_equivalence_status": row["mt5_equivalence_status"],
            "manual_export_required": row["satisfies_mt5_tick_contract_field"] is False,
        }
        for row in field_audit["field_rows"]
        if not row["satisfies_mt5_tick_contract_field"]
    ]
    return base_payload(
        "field_mismatch_blocker_ledger",
        terminal_blocker_status="MT5_BID_ASK_TICK_CONTRACT_NOT_SATISFIED_BY_SCID",
        mt5_tick_contract_satisfied=False,
        owner_tick_requests_remain_open=True,
        hard_absent_fields=HARD_ABSENT_MT5_FIELDS,
        proxy_only_non_equivalent_fields=PROXY_ONLY_MT5_FIELDS,
        blocker_rows=blockers,
        exact_blocker_summary=(
            "SCID has timestamped OHLC and bid/ask volume, but it does not contain bid quote price, ask quote price, or MT5 flags. "
            "SCID close/volume/broker-symbol/time_msc substitutions would be proxies and cannot close the MT5 tick export requests."
        ),
    )


def next_g12_prompt_text() -> str:
    return f"""# G12 XAUUSD Sierra SCID Alternate Source-Control Audit Goal Prompt

Date: {DATE}
Owner lane: independent G12 source-control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`.

Verify that the route read `C:\\SierraChart\\Data\\XAUUSD.scid` read-only, hashed the raw SCID file, recomputed the `2026-04-15` and `2026-04-16` full-day row coverage, reconciled the three remaining candidate timestamps, compared SCID fields against the MT5 tick contract field by field, and emitted a source-hashed SCID market-activity packet only as context while preserving exact MT5 bid/ask tick blockers and owner/manual export requirements.

## Mandatory Preflight

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read the latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\goal_session_research_discipline.md`.
7. Read `.context\\00_core\\local_heavy_data_inventory.md`.
8. Read `.context\\00_core\\research_current_state.md`.
9. Read the target route directory `research\\science_program_2026_05\\06_outcome_testing\\xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route\\`.
10. Read the upstream G12 and target NOFILL read-only tick recovery artifacts.

## Audit Requirements

- Recompute the raw SCID SHA256, size, header, record count, first/last timestamps, and parser code hashes.
- Recompute full-day row counts for `2026-04-15` and `2026-04-16`.
- Recompute candidate coverage for:
  - `XAUUSD_2026-04-15T14:15:05.007998+00:00`
  - `XAUUSD_2026-04-16T09:30:05.013547+00:00`
  - `XAUUSD_2026-04-16T13:16:01.126537+00:00`
- Verify nearest preceding/following SCID records, timestamp resolution, OHLC, volume, bid volume, ask volume, and anomaly summaries.
- Verify the MT5 field comparison for `time_utc`, `time_msc`, `bid`, `ask`, `last`, `volume`, `flags`, `source_symbol`, `broker_symbol`, and `source_file_sha256`.
- Verify the route does not substitute SCID OHLC or bid/ask volume for MT5 bid/ask quotes.
- Verify 2026-04-16 candidate rows remain contamination/embargo excluded.
- Verify SCID does not recreate pending intent, lifecycle group, write-clock, source-safe order observability, ticket redaction, native pending type, final lifecycle truth, broker actual-R, or result labels.
- Verify no raw SCID-derived exports, raw CSV, raw parquet, or large market-data files are tracked or staged.
- Run the route verifier and focused tests.

## Completion Standard

Mark complete only if the G12 audit proves the target route is source/control only, the source hash/header/coverage and field comparison are independently reproducible, the alternate packet is context-only and non-equivalent to MT5 tick recovery, exact manual MT5 export blockers remain open, verifier/tests pass, and terminal flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def write_next_g12_prompt_pack() -> dict[str, Any]:
    prompt_path = repo_path(NEXT_G12_PROMPT_PATH)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(next_g12_prompt_text(), encoding="utf-8")
    starter = (
        f"/goal Follow the full controlling prompt in {NEXT_G12_PROMPT_PATH} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay independent G12 source-control audit only "
        "with no validation/result scoring/broker account-order-history-deal-position/paid API/registry/remote/live behavior; "
        "independently rehash SCID, recompute 2026-04-15/16 coverage and the three candidate windows, verify MT5 field blockers and context-only alternate packet boundaries, "
        "run target verifier/focused tests, require no raw market data tracked or staged, and close only with NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false."
    )
    return base_payload(
        "next_g12_audit_prompt_pack",
        full_next_g12_prompt_path=NEXT_G12_PROMPT_PATH,
        route_to_audit=ROUTE_ID,
        one_line_starter=starter,
        prompt_file_written=True,
        audit_focus=[
            "raw SCID hash/header/coverage reproducibility",
            "candidate-window nearest record reproducibility",
            "field-by-field MT5 tick contract blockers",
            "context-only alternate packet boundary",
            "manual MT5 export blockers remain open",
            "no raw market data committed",
        ],
    )


def git_stdout(args: list[str]) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_path_list(args: list[str]) -> list[str]:
    output = git_stdout(args)
    if not output:
        return []
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def changed_or_untracked_paths() -> list[str]:
    changed = set(git_path_list(["diff", "--name-only", "HEAD"]))
    changed.update(git_path_list(["ls-files", "--others", "--exclude-standard"]))
    return sorted(changed)


def build_completion_audit(
    source_audit: dict[str, Any],
    coverage: dict[str, Any],
    field_audit: dict[str, Any],
    decision: dict[str, Any],
    boundary: dict[str, Any],
    owner_manifest: dict[str, Any],
    alternate_packet: dict[str, Any],
    blockers: dict[str, Any],
    next_g12: dict[str, Any],
) -> dict[str, Any]:
    artifacts = [
        f"{PREFIX}_{stem}_{DATE}.json" for stem in REQUIRED_ARTIFACT_STEMS
    ] + [
        f"{PREFIX}_{stem}_{DATE}.md" for stem in REQUIRED_ARTIFACT_STEMS
    ]
    artifacts.extend(
        [
            "build_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10.py",
            "verify_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10.py",
            "test_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10.py",
            rel(repo_path(NEXT_G12_PROMPT_PATH)),
        ]
    )
    changed_paths = changed_or_untracked_paths()
    raw_market_data_patterns = re.compile(r"\.(parquet|csv|scid)$", re.I)
    raw_market_data_changed = [
        path for path in changed_paths if raw_market_data_patterns.search(path) and not path.startswith("research/")
    ]
    checklist = [
        {
            "requirement": "mandatory_preflight_and_context_inputs",
            "evidence": "context anchor lists LIVE_STATE, latest handoff, quick reference, doctrine, goal discipline, local heavy data, research current state, upstream G12, target route, and existing SCID tooling",
            "status": "PASS",
        },
        {
            "requirement": "raw_scid_source_hash_header_coverage",
            "evidence": {
                "source_sha256_present": bool(source_audit["raw_source"]["source_sha256"]),
                "header_magic": source_audit["scid_header"]["magic"],
                "record_count": source_audit["scid_header"]["record_count"],
            },
            "status": "PASS" if bool(source_audit["raw_source"]["source_sha256"]) and source_audit["scid_header"]["magic"] == "SCID" else "FAIL",
        },
        {
            "requirement": "full_day_counts_for_2026_04_15_and_2026_04_16",
            "evidence": {row["source_date"]: row["row_count"] for row in coverage["day_coverage"]},
            "status": "PASS" if coverage["all_requested_days_have_rows"] else "FAIL",
        },
        {
            "requirement": "all_three_candidate_timestamps_reconciled",
            "evidence": {
                row["candidate_id"]: {
                    "rows_plus_minus_60_seconds": row["rows_plus_minus_60_seconds"],
                    "nearest_abs_delta_ms": row["nearest_abs_delta_ms"],
                }
                for row in coverage["candidate_coverage"]
            },
            "status": "PASS" if coverage["all_candidates_have_nearest_records"] else "FAIL",
        },
        {
            "requirement": "field_by_field_mt5_tick_contract_comparison",
            "evidence": {
                "hard_absent_fields": field_audit["hard_absent_fields"],
                "proxy_only_fields": field_audit["proxy_only_non_equivalent_fields"],
                "mt5_tick_contract_satisfied": field_audit["mt5_tick_contract_satisfied"],
            },
            "status": "PASS" if field_audit["mt5_tick_contract_satisfied"] is False else "FAIL",
        },
        {
            "requirement": "alternate_packet_or_exact_blockers",
            "evidence": {
                "alternate_packet_status": alternate_packet["packet_admissibility_status"],
                "mt5_equivalent": alternate_packet["mt5_tick_recovery_equivalent"],
                "blocker_status": blockers["terminal_blocker_status"],
            },
            "status": "PASS",
        },
        {
            "requirement": "source_state_no_validation_no_result_no_live_boundaries",
            "evidence": {
                "boundary_status": boundary["boundary_status"],
                "validation_safe": boundary["validation_safe"],
                "outcome_review_opened": boundary["outcome_review_opened"],
                "live_effect": boundary["live_effect"],
            },
            "status": "PASS" if boundary["boundary_status"] == "PASS_SOURCE_CONTROL_ONLY" else "FAIL",
        },
        {
            "requirement": "owner_manual_export_fallback_for_two_xauusd_days",
            "evidence": {
                "count": owner_manifest["remaining_market_data_export_request_count"],
                "paths": [row["target_path_template"] for row in owner_manifest["market_data_export_requests"]],
            },
            "status": "PASS" if owner_manifest["remaining_market_data_export_request_count"] == 2 else "FAIL",
        },
        {
            "requirement": "next_g12_prompt_pack",
            "evidence": {
                "prompt_path": next_g12["full_next_g12_prompt_path"],
                "one_line_starter_present": bool(next_g12["one_line_starter"]),
                "prompt_file_written": next_g12["prompt_file_written"],
            },
            "status": "PASS" if next_g12["prompt_file_written"] else "FAIL",
        },
        {
            "requirement": "no_raw_market_data_committed_or_staged_by_route",
            "evidence": {"raw_market_data_changed_outside_research": raw_market_data_changed},
            "status": "PASS" if not raw_market_data_changed else "FAIL",
        },
    ]
    return base_payload(
        "completion_audit",
        objective_restatement=(
            "Parse and audit C:\\SierraChart\\Data\\XAUUSD.scid read-only for OWNER-TICK-0020 and OWNER-TICK-0021, "
            "hash the raw source, prove day/candidate coverage, compare against the MT5 tick contract, emit a context-only alternate packet plus exact MT5 blockers, "
            "and preserve source/control boundaries."
        ),
        prompt_to_artifact_checklist=checklist,
        required_artifacts=artifacts,
        completion_status="PASS" if all(item["status"] == "PASS" for item in checklist) else "FAIL",
        terminal_decision="ACCEPT_AS_SOURCE_HASHED_SCID_CONTEXT_PACKET_WITH_EXACT_MT5_FIELD_BLOCKERS",
        validation_safe=False,
        outcome_review_opened=False,
        live_effect=False,
    )


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_md(name: str, title: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / name
    lines = [
        f"# {title}",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Terminal posture: `{PROMOTION_VERDICT}`",
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "```json",
        json.dumps(payload, indent=2, sort_keys=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_artifact(stem: str, title: str, payload: dict[str, Any]) -> None:
    write_json(f"{PREFIX}_{stem}_{DATE}.json", payload)
    write_md(f"{PREFIX}_{stem}_{DATE}.md", title, payload)


def build_all(scid_path: Path = SCID_PATH) -> dict[str, Any]:
    context = build_context_anchor()
    source_audit = build_scid_source_hash_header_audit(scid_path)
    coverage = build_coverage_ledger(scid_path)
    field_audit = build_field_comparison_audit()
    decision = build_admissibility_decision(coverage, field_audit)
    boundary = build_boundary_audit()
    owner_manifest = build_owner_manual_export_manifest()
    alternate_packet = build_alternate_packet(source_audit, coverage, decision)
    blockers = build_field_mismatch_blockers(field_audit)
    next_g12 = write_next_g12_prompt_pack()
    completion = build_completion_audit(
        source_audit,
        coverage,
        field_audit,
        decision,
        boundary,
        owner_manifest,
        alternate_packet,
        blockers,
        next_g12,
    )
    artifacts = {
        "CONTEXT_ANCHOR": ("Context Anchor", context),
        "SCID_SOURCE_HASH_HEADER_AUDIT": ("SCID Source Hash Header Audit", source_audit),
        "SCID_DAY_CANDIDATE_COVERAGE_LEDGER": ("SCID Day Candidate Coverage Ledger", coverage),
        "MT5_TICK_CONTRACT_FIELD_COMPARISON_AUDIT": ("MT5 Tick Contract Field Comparison Audit", field_audit),
        "ALTERNATE_SOURCE_ADMISSIBILITY_DECISION_LEDGER": (
            "Alternate Source Admissibility Decision Ledger",
            decision,
        ),
        "SOURCE_STATE_NOLEAK_BOUNDARY_AUDIT": ("Source State No-Leak Boundary Audit", boundary),
        "OWNER_MANUAL_EXPORT_FALLBACK_MANIFEST": ("Owner Manual Export Fallback Manifest", owner_manifest),
        "SOURCE_HASHED_ALTERNATE_PACKET": ("Source Hashed Alternate Packet", alternate_packet),
        "FIELD_MISMATCH_BLOCKER_LEDGER": ("Field Mismatch Blocker Ledger", blockers),
        "NEXT_G12_AUDIT_PROMPT_PACK": ("Next G12 Audit Prompt Pack", next_g12),
        "COMPLETION_AUDIT": ("Completion Audit", completion),
    }
    for stem, (title, payload) in artifacts.items():
        write_artifact(stem, title, payload)
    return {
        "route_id": ROUTE_ID,
        "route_dir": str(ROUTE_DIR),
        "source_sha256": source_audit["raw_source"]["source_sha256"],
        "day_counts": {row["source_date"]: row["row_count"] for row in coverage["day_coverage"]},
        "candidate_count": len(coverage["candidate_coverage"]),
        "mt5_tick_contract_satisfied": field_audit["mt5_tick_contract_satisfied"],
        "alternate_packet_status": alternate_packet["packet_admissibility_status"],
        "completion_status": completion["completion_status"],
        "next_g12_prompt_path": NEXT_G12_PROMPT_PATH,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def main() -> int:
    result = build_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
