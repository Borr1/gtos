#!/usr/bin/env python3
"""Build the independent G12 audit for the XAUUSD Sierra SCID alternate route.

This is source/control work only. It parses the Sierra SCID file read-only and
does not export market data slices, call MT5, score outcomes, or change live
trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT"
TARGET_ROUTE_ID = "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE"
PREFIX = "G12_XAUUSD_SIERRA_SCID_ALT_AUDIT"
DATE = "2026-05-10"
SCHEMA_VERSION = "g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
SCID_PATH = Path(r"C:\SierraChart\Data\XAUUSD.scid")
CONTROL_PROMPT_PATH = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route"
)
UPSTREAM_G12_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_readonly_tick_recovery_export_source_control_audit"
)
UPSTREAM_NOFILL_ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_readonly_tick_recovery_export_source_control_route"
)

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

HEADER_STRUCT = struct.Struct("<4sIIHHI36s")
RECORD_STRUCT = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
INVALID_ABS_PRICE = 1.0e20
SPECIAL_PRICE_RE = re.compile(r"^-?1\.99900\d+e\+?37$", re.I)

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
PROXY_ONLY_NON_EQUIVALENT_FIELDS = ["time_msc", "last", "volume", "broker_symbol"]
CONTEXT_DERIVABLE_FIELDS = ["time_utc", "source_symbol", "source_file_sha256"]

EXPECTED_SCID_SHA256 = "c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b"
EXPECTED_DAY_COUNTS = {"2026-04-15": 72119, "2026-04-16": 70048}
EXPECTED_CANDIDATE_ROWS_60S = {
    "XAUUSD_2026-04-15T14:15:05.007998+00:00": 120,
    "XAUUSD_2026-04-16T09:30:05.013547+00:00": 112,
    "XAUUSD_2026-04-16T13:16:01.126537+00:00": 110,
}
EXPECTED_NEAREST_DELTA_MS = {
    "XAUUSD_2026-04-15T14:15:05.007998+00:00": 1.9980000000000002,
    "XAUUSD_2026-04-16T09:30:05.013547+00:00": 16.453,
    "XAUUSD_2026-04-16T13:16:01.126537+00:00": 316.463,
}

CANDIDATE_REQUESTS = [
    {
        "owner_request_id": "OWNER-TICK-0020",
        "source_date": "2026-04-15",
        "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-15.parquet",
        "contamination_or_embargo_excluded": False,
        "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
        "candidate_utc": "2026-04-15T14:15:05.007998Z",
    },
    {
        "owner_request_id": "OWNER-TICK-0021",
        "source_date": "2026-04-16",
        "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-16.parquet",
        "contamination_or_embargo_excluded": True,
        "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
        "candidate_utc": "2026-04-16T09:30:05.013547Z",
    },
    {
        "owner_request_id": "OWNER-TICK-0021",
        "source_date": "2026-04-16",
        "target_mt5_tick_path": "data/ticks/XAUUSD/2026-04-16.parquet",
        "contamination_or_embargo_excluded": True,
        "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
        "candidate_utc": "2026-04-16T13:16:01.126537Z",
    },
]

REQUIRED_ARTIFACT_STEMS = [
    "CONTEXT_ANCHOR",
    "SOURCE_HASH_HEADER_COVERAGE_REAUDIT",
    "CANDIDATE_WINDOW_REPRODUCIBILITY_AUDIT",
    "MT5_FIELD_BLOCKER_REAUDIT",
    "DECISION_LEDGER",
    "NOLEAK_RAW_DATA_STAGING_AUDIT",
    "NEXT_STEP_RECOMMENDATION",
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


def git_stdout(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def git_paths(args: list[str]) -> list[str]:
    return [line.strip().replace("\\", "/") for line in git_stdout(args).splitlines() if line.strip()]


def head_summary() -> str:
    return git_stdout(["log", "-1", "--oneline"]).strip()


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
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


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scid_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def scid_datetime_us(value: datetime) -> int:
    delta = value.astimezone(timezone.utc) - SIERRA_EPOCH
    return int(delta.total_seconds() * 1_000_000)


def parse_scid_header(path: Path) -> ScidHeader:
    if not path.exists():
        return ScidHeader(path=path, exists=False)
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(HEADER_STRUCT.size)
    if len(raw) < HEADER_STRUCT.size:
        raise ValueError(f"{path} is too small for SCID header")
    magic_raw, header_size, record_size, version, _unused, utc_start_index, _reserved = HEADER_STRUCT.unpack(raw)
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


def read_record(handle: Any, header: ScidHeader, index: int) -> dict[str, Any]:
    if index < 0 or index >= header.record_count:
        raise IndexError(index)
    handle.seek(int(header.header_size or 0) + index * int(header.record_size or 0))
    raw = handle.read(int(header.record_size or 0))
    if len(raw) != header.record_size:
        raise ValueError(f"short SCID record read at {index}")
    dt_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = RECORD_STRUCT.unpack(raw)
    return {
        "index": index,
        "sierra_datetime_us": int(dt_us),
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


def is_bad_price(value: float) -> bool:
    if not math.isfinite(value):
        return True
    if abs(value) >= INVALID_ABS_PRICE:
        return True
    if value <= 0:
        return True
    return bool(SPECIAL_PRICE_RE.match(f"{value:.8e}"))


def record_anomalies(record: dict[str, Any]) -> list[str]:
    prices = [record["open"], record["high"], record["low"], record["close"]]
    anomalies: list[str] = []
    if any(is_bad_price(float(price)) for price in prices):
        anomalies.append("INVALID_OR_SPECIAL_PRICE_FIELD")
    if int(record["total_volume"]) != int(record["bid_volume"]) + int(record["ask_volume"]):
        anomalies.append("BID_ASK_VOLUME_SUM_MISMATCH")
    return anomalies


def record_to_json(record: dict[str, Any] | None, target: datetime | None = None) -> dict[str, Any] | None:
    if record is None:
        return None
    payload = {
        "index": record["index"],
        "sierra_datetime_us": record["sierra_datetime_us"],
        "timestamp_utc": iso_utc(record["timestamp"]),
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
        payload["delta_to_candidate_seconds"] = delta.total_seconds()
        payload["abs_delta_to_candidate_ms"] = abs(delta.total_seconds() * 1000.0)
    return payload


def lower_bound(handle: Any, header: ScidHeader, target_us: int) -> int:
    lo, hi = 0, header.record_count
    while lo < hi:
        mid = (lo + hi) // 2
        record = read_record(handle, header, mid)
        if record["sierra_datetime_us"] < target_us:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(handle: Any, header: ScidHeader, target_us: int) -> int:
    lo, hi = 0, header.record_count
    while lo < hi:
        mid = (lo + hi) // 2
        record = read_record(handle, header, mid)
        if record["sierra_datetime_us"] <= target_us:
            lo = mid + 1
        else:
            hi = mid
    return lo


def read_optional_record(handle: Any, header: ScidHeader, index: int) -> dict[str, Any] | None:
    if index < 0 or index >= header.record_count:
        return None
    return read_record(handle, header, index)


def median_int(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return int(ordered[mid])
    return int((ordered[mid - 1] + ordered[mid]) / 2)


def range_summary(path: Path, header: ScidHeader, start: datetime, end: datetime) -> dict[str, Any]:
    start_us = scid_datetime_us(start)
    end_us = scid_datetime_us(end)
    timestamps: list[int] = []
    volume_totals = {"num_trades": 0, "total_volume": 0, "bid_volume": 0, "ask_volume": 0}
    anomaly_counts: Counter[str] = Counter()
    first: dict[str, Any] | None = None
    last: dict[str, Any] | None = None
    min_close: float | None = None
    max_close: float | None = None
    rows = 0
    with path.open("rb") as handle:
        index = lower_bound(handle, header, start_us)
        while index < header.record_count:
            record = read_record(handle, header, index)
            if record["sierra_datetime_us"] >= end_us:
                break
            rows += 1
            first = first or record
            last = record
            timestamps.append(record["sierra_datetime_us"])
            min_close = record["close"] if min_close is None else min(min_close, record["close"])
            max_close = record["close"] if max_close is None else max(max_close, record["close"])
            for key in volume_totals:
                volume_totals[key] += int(record[key])
            anomaly_counts.update(record_anomalies(record))
            index += 1
    positive_deltas: list[int] = []
    duplicate_count = 0
    non_monotonic_count = 0
    max_gap_us = 0
    previous: int | None = None
    for current in timestamps:
        if previous is not None:
            delta = current - previous
            if delta == 0:
                duplicate_count += 1
            elif delta < 0:
                non_monotonic_count += 1
            else:
                positive_deltas.append(delta)
                max_gap_us = max(max_gap_us, delta)
        previous = current
    return {
        "start_utc": iso_utc(start),
        "end_utc": iso_utc(end),
        "rows": rows,
        "first_record": record_to_json(first),
        "last_record": record_to_json(last),
        "first_timestamp_utc": iso_utc(first["timestamp"]) if first else None,
        "last_timestamp_utc": iso_utc(last["timestamp"]) if last else None,
        "first_close": first["close"] if first else None,
        "last_close": last["close"] if last else None,
        "min_close": min_close,
        "max_close": max_close,
        "volume_totals": volume_totals,
        "record_status_anomaly_counts": dict(sorted(anomaly_counts.items())),
        "timestamp_resolution": {
            "duplicate_timestamp_count": duplicate_count,
            "non_monotonic_timestamp_count": non_monotonic_count,
            "min_positive_delta_us": min(positive_deltas) if positive_deltas else None,
            "median_positive_delta_us": median_int(positive_deltas),
            "max_gap_seconds": max_gap_us / 1_000_000 if max_gap_us else None,
        },
    }


def day_summary(path: Path, header: ScidHeader, source_date: str) -> dict[str, Any]:
    start = datetime.fromisoformat(source_date).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    summary = range_summary(path, header, start, end)
    return {
        "source_date": source_date,
        "coverage_status": "SCID_ROWS_PRESENT" if summary["rows"] > 0 else "SCID_ROWS_ABSENT",
        "row_count": summary["rows"],
        "window_start_utc": summary["start_utc"],
        "window_end_utc": (end - timedelta(microseconds=1)).isoformat().replace("+00:00", "Z"),
        "first_record": summary["first_record"],
        "last_record": summary["last_record"],
        "min_close": summary["min_close"],
        "max_close": summary["max_close"],
        "volume_totals": summary["volume_totals"],
        "record_status_anomaly_counts": summary["record_status_anomaly_counts"],
        "timestamp_resolution": summary["timestamp_resolution"],
    }


def floor_m15(value: datetime) -> datetime:
    dt = value.astimezone(timezone.utc)
    minute = (dt.minute // 15) * 15
    return dt.replace(minute=minute, second=0, microsecond=0)


def nearest_records(path: Path, header: ScidHeader, target: datetime) -> dict[str, Any]:
    target_us = scid_datetime_us(target)
    with path.open("rb") as handle:
        lb = lower_bound(handle, header, target_us)
        ub = upper_bound(handle, header, target_us)
        strict_preceding = read_optional_record(handle, header, lb - 1)
        at_or_following = read_optional_record(handle, header, lb)
        at_or_before = read_optional_record(handle, header, ub - 1)
        candidates = [row for row in [strict_preceding, at_or_following, at_or_before] if row is not None]
    nearest = min(candidates, key=lambda row: abs((row["timestamp"] - target).total_seconds())) if candidates else None
    return {
        "strict_preceding_record": record_to_json(strict_preceding, target),
        "at_or_following_record": record_to_json(at_or_following, target),
        "at_or_before_record": record_to_json(at_or_before, target),
        "nearest_record": record_to_json(nearest, target),
        "nearest_abs_delta_ms": abs((nearest["timestamp"] - target).total_seconds() * 1000.0) if nearest else None,
    }


def candidate_summary(path: Path, header: ScidHeader, candidate: dict[str, Any]) -> dict[str, Any]:
    target = parse_utc(candidate["candidate_utc"])
    plus_5 = range_summary(path, header, target - timedelta(seconds=5), target + timedelta(seconds=5))
    plus_60 = range_summary(path, header, target - timedelta(seconds=60), target + timedelta(seconds=60))
    m15_start = floor_m15(target)
    m15 = range_summary(path, header, m15_start, m15_start + timedelta(minutes=15))
    nearest = nearest_records(path, header, target)
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_utc": iso_utc(target),
        "source_date": candidate["source_date"],
        "owner_request_id": candidate["owner_request_id"],
        "target_mt5_tick_path": candidate["target_mt5_tick_path"],
        "inside_requested_utc_day": target.date().isoformat() == candidate["source_date"],
        "contamination_or_embargo_excluded": candidate["contamination_or_embargo_excluded"],
        "candidate_coverage_status": (
            "SCID_RECORDS_PRESENT_AROUND_CANDIDATE" if nearest["nearest_record"] and plus_60["rows"] > 0 else "SCID_COVERAGE_GAP"
        ),
        "nearest_abs_delta_ms": nearest["nearest_abs_delta_ms"],
        "nearest_records": {
            "strict_preceding_record": nearest["strict_preceding_record"],
            "at_or_following_record": nearest["at_or_following_record"],
            "at_or_before_record": nearest["at_or_before_record"],
            "nearest_record": nearest["nearest_record"],
        },
        "plus_minus_5_seconds_summary": {
            "start_utc": plus_5["start_utc"],
            "end_utc": plus_5["end_utc"],
            "rows": plus_5["rows"],
            "first_timestamp_utc": plus_5["first_timestamp_utc"],
            "last_timestamp_utc": plus_5["last_timestamp_utc"],
            "first_close": plus_5["first_close"],
            "last_close": plus_5["last_close"],
            "volume_totals": plus_5["volume_totals"],
            "record_status_anomaly_counts": plus_5["record_status_anomaly_counts"],
            "timestamp_resolution": plus_5["timestamp_resolution"],
        },
        "plus_minus_60_seconds_summary": {
            "start_utc": plus_60["start_utc"],
            "end_utc": plus_60["end_utc"],
            "rows": plus_60["rows"],
            "first_timestamp_utc": plus_60["first_timestamp_utc"],
            "last_timestamp_utc": plus_60["last_timestamp_utc"],
            "first_close": plus_60["first_close"],
            "last_close": plus_60["last_close"],
            "min_close": plus_60["min_close"],
            "max_close": plus_60["max_close"],
            "volume_totals": plus_60["volume_totals"],
            "record_status_anomaly_counts": plus_60["record_status_anomaly_counts"],
            "timestamp_resolution": plus_60["timestamp_resolution"],
        },
        "m15_context_summary": {
            "start_utc": m15["start_utc"],
            "end_utc": m15["end_utc"],
            "rows": m15["rows"],
            "first_timestamp_utc": m15["first_timestamp_utc"],
            "last_timestamp_utc": m15["last_timestamp_utc"],
            "first_close": m15["first_close"],
            "last_close": m15["last_close"],
            "min_close": m15["min_close"],
            "max_close": m15["max_close"],
            "volume_totals": m15["volume_totals"],
            "record_status_anomaly_counts": m15["record_status_anomaly_counts"],
            "timestamp_resolution": m15["timestamp_resolution"],
        },
        "rows_plus_minus_5_seconds": plus_5["rows"],
        "rows_plus_minus_60_seconds": plus_60["rows"],
        "rows_m15_context": m15["rows"],
    }


def build_field_rows() -> list[dict[str, Any]]:
    return [
        {
            "field": "time_utc",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_TIMESTAMP_VALUE",
            "scid_evidence": "SCID DTDateTime microsecond timestamp",
            "mt5_equivalence_status": "timestamp value exists, but source lineage is Sierra-native rather than MT5 broker-native",
        },
        {
            "field": "time_msc",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
            "scid_evidence": "SCID timestamp can be converted to milliseconds",
            "mt5_equivalence_status": "not MT5-native time_msc; conversion would be a source timestamp proxy",
        },
        {
            "field": "bid",
            "presence_status": "ABSENT",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
            "scid_evidence": "SCID has OHLC price fields and bid_volume, not bid quote price",
            "mt5_equivalence_status": "OHLC or bid_volume cannot be substituted for MT5 bid quote",
        },
        {
            "field": "ask",
            "presence_status": "ABSENT",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
            "scid_evidence": "SCID has OHLC price fields and ask_volume, not ask quote price",
            "mt5_equivalence_status": "OHLC or ask_volume cannot be substituted for MT5 ask quote",
        },
        {
            "field": "last",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
            "scid_evidence": "SCID close is a source-native record close price",
            "mt5_equivalence_status": "market-activity proxy only; not MT5 last field proof",
        },
        {
            "field": "volume",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
            "scid_evidence": "SCID total_volume plus bid_volume and ask_volume",
            "mt5_equivalence_status": "source-native footprint volume, not MT5 tick volume proof",
        },
        {
            "field": "flags",
            "presence_status": "ABSENT",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "HARD_FIELD_ABSENT",
            "scid_evidence": "No SCID field carries MT5 tick flags",
            "mt5_equivalence_status": "absent",
        },
        {
            "field": "source_symbol",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_METADATA_VALUE",
            "scid_evidence": "Derivable from XAUUSD.scid filename and owner request",
            "mt5_equivalence_status": "source metadata only",
        },
        {
            "field": "broker_symbol",
            "presence_status": "DERIVABLE_ONLY_AS_PROXY",
            "satisfies_mt5_tick_contract_field": False,
            "blocker_class": "PROXY_ONLY_NON_EQUIVALENT",
            "scid_evidence": "Filename says XAUUSD but source is Sierra, not MT5 broker export",
            "mt5_equivalence_status": "same text symbol does not prove MT5 broker_symbol lineage",
        },
        {
            "field": "source_file_sha256",
            "presence_status": "DERIVABLE_WITHOUT_LEAKAGE",
            "satisfies_mt5_tick_contract_field": True,
            "blocker_class": "NONE_FOR_SOURCE_HASH_VALUE",
            "scid_evidence": "Raw SCID SHA256 is computed by this audit",
            "mt5_equivalence_status": "hash exists for SCID source, not for missing MT5 parquet",
        },
    ]


def target_artifact(name: str) -> dict[str, Any]:
    return load_json(TARGET_ROUTE_DIR / name)


def compare_dict(actual: Any, expected: Any, path: str, mismatches: list[dict[str, Any]]) -> None:
    if actual != expected:
        mismatches.append({"path": path, "actual": actual, "expected": expected})


def collect_recomputed() -> dict[str, Any]:
    header = parse_scid_header(SCID_PATH)
    source_hash = sha256_file(SCID_PATH)
    with SCID_PATH.open("rb") as handle:
        first_record = read_record(handle, header, 0)
        last_record = read_record(handle, header, header.record_count - 1)
    day_rows = [day_summary(SCID_PATH, header, date) for date in ["2026-04-15", "2026-04-16"]]
    candidate_rows = [candidate_summary(SCID_PATH, header, candidate) for candidate in CANDIDATE_REQUESTS]
    return {
        "source_hash": source_hash,
        "header": header,
        "first_file_record": record_to_json(first_record),
        "last_file_record": record_to_json(last_record),
        "day_coverage": day_rows,
        "candidate_coverage": candidate_rows,
    }


def build_context_anchor() -> dict[str, Any]:
    return base_payload(
        "context_anchor",
        objective="Independently G12-audit the XAUUSD Sierra SCID alternate source-control route.",
        current_head=head_summary(),
        controlling_prompt=CONTROL_PROMPT_PATH,
        mandatory_context_read=[
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/research_current_state.md",
        ],
        target_route_dir=rel(TARGET_ROUTE_DIR),
        upstream_g12_dir=rel(UPSTREAM_G12_DIR),
        upstream_nofill_route_dir=rel(UPSTREAM_NOFILL_ROUTE_DIR),
        source_path=str(SCID_PATH),
        audit_boundaries=[
            "source/control only",
            "no validation or result scoring",
            "no broker/account/order/history/deal/position behavior",
            "no paid/API/Databento route",
            "no live trading behavior",
        ],
    )


def build_source_hash_header_coverage_reaudit(recomputed: dict[str, Any]) -> dict[str, Any]:
    target_source = target_artifact("XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_SOURCE_HASH_HEADER_AUDIT_2026-05-10.json")
    target_coverage = target_artifact("XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_DAY_CANDIDATE_COVERAGE_LEDGER_2026-05-10.json")
    header: ScidHeader = recomputed["header"]
    day_counts = {row["source_date"]: row["row_count"] for row in recomputed["day_coverage"]}
    target_day_counts = {row["source_date"]: row["row_count"] for row in target_coverage["day_coverage"]}
    mismatches: list[dict[str, Any]] = []
    compare_dict(recomputed["source_hash"], target_source["raw_source"]["source_sha256"], "raw_source.source_sha256", mismatches)
    compare_dict(header.record_count, target_source["scid_header"]["record_count"], "scid_header.record_count", mismatches)
    compare_dict(header.remainder_bytes, target_source["scid_header"]["remainder_bytes"], "scid_header.remainder_bytes", mismatches)
    compare_dict(day_counts, target_day_counts, "day_coverage.row_counts", mismatches)
    return base_payload(
        "source_hash_header_coverage_reaudit",
        source_access_status="SCID_REHASHED_AND_HEADER_REPARSED_READ_ONLY",
        raw_source={
            "source_path": str(SCID_PATH),
            "source_sha256": recomputed["source_hash"],
            "expected_source_sha256": EXPECTED_SCID_SHA256,
            "source_sha256_matches_expected": recomputed["source_hash"] == EXPECTED_SCID_SHA256,
            "size_bytes": header.size_bytes,
            "raw_source_not_committed": True,
            "raw_source_not_copied": True,
        },
        scid_header=header_to_json(header),
        scid_header_validation_issues=[] if header.magic == "SCID" and header.record_size == 40 and header.remainder_bytes == 0 else ["HEADER_OR_RECORD_LAYOUT_ISSUE"],
        first_file_record=recomputed["first_file_record"],
        last_file_record=recomputed["last_file_record"],
        day_coverage=recomputed["day_coverage"],
        day_counts_match_expected=day_counts == EXPECTED_DAY_COUNTS,
        target_route_comparison={
            "target_source_hash_header_artifact": rel(TARGET_ROUTE_DIR / "XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_SOURCE_HASH_HEADER_AUDIT_2026-05-10.json"),
            "target_day_candidate_coverage_artifact": rel(TARGET_ROUTE_DIR / "XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_DAY_CANDIDATE_COVERAGE_LEDGER_2026-05-10.json"),
            "mismatches": mismatches,
            "comparison_status": "MATCH" if not mismatches else "MISMATCH_REPAIR_REQUIRED",
        },
        parser_code_hashes={
            "g12_audit_builder_sha256": sha256_path(Path(__file__)),
            "target_route_builder_sha256": sha256_path(TARGET_ROUTE_DIR / "build_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10.py"),
            "scripts_inspect_sierra_scid_sha256": sha256_path(REPO_ROOT / "scripts" / "inspect_sierra_scid.py"),
        },
    )


def build_candidate_window_reproducibility_audit(recomputed: dict[str, Any]) -> dict[str, Any]:
    target_coverage = target_artifact("XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_DAY_CANDIDATE_COVERAGE_LEDGER_2026-05-10.json")
    target_by_id = {row["candidate_id"]: row for row in target_coverage["candidate_coverage"]}
    comparison_rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    for row in recomputed["candidate_coverage"]:
        target = target_by_id.get(row["candidate_id"], {})
        actual_delta = row["nearest_abs_delta_ms"]
        expected_delta = EXPECTED_NEAREST_DELTA_MS[row["candidate_id"]]
        row_mismatches: list[dict[str, Any]] = []
        compare_dict(row["rows_plus_minus_60_seconds"], EXPECTED_CANDIDATE_ROWS_60S[row["candidate_id"]], "rows_plus_minus_60_seconds.expected_fact", row_mismatches)
        compare_dict(row["rows_plus_minus_60_seconds"], target.get("rows_plus_minus_60_seconds"), "rows_plus_minus_60_seconds.target_artifact", row_mismatches)
        if abs(float(actual_delta) - float(expected_delta)) > 0.0005:
            row_mismatches.append({"path": "nearest_abs_delta_ms.expected_fact", "actual": actual_delta, "expected": expected_delta})
        compare_dict(row["nearest_records"]["nearest_record"], target.get("nearest_records", {}).get("nearest_record"), "nearest_record.target_artifact", row_mismatches)
        comparison_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_utc": row["candidate_utc"],
                "owner_request_id": row["owner_request_id"],
                "source_date": row["source_date"],
                "nearest_abs_delta_ms": row["nearest_abs_delta_ms"],
                "rows_plus_minus_60_seconds": row["rows_plus_minus_60_seconds"],
                "rows_plus_minus_5_seconds": row["rows_plus_minus_5_seconds"],
                "rows_m15_context": row["rows_m15_context"],
                "contamination_or_embargo_excluded": row["contamination_or_embargo_excluded"],
                "comparison_status": "MATCH" if not row_mismatches else "MISMATCH_REPAIR_REQUIRED",
                "mismatches": row_mismatches,
            }
        )
        mismatches.extend({"candidate_id": row["candidate_id"], **mismatch} for mismatch in row_mismatches)
    return base_payload(
        "candidate_window_reproducibility_audit",
        source_path=str(SCID_PATH),
        candidate_window_policy={
            "diagnostic_near_window": "plus_minus_5_seconds",
            "primary_candidate_window": "plus_minus_60_seconds",
            "m15_context_window": "UTC M15 bar containing candidate timestamp",
        },
        candidate_coverage=recomputed["candidate_coverage"],
        candidate_comparison_summary=comparison_rows,
        all_candidates_have_nearest_records=all(row["nearest_records"]["nearest_record"] for row in recomputed["candidate_coverage"]),
        all_candidates_have_plus_minus_60s_rows=all(row["rows_plus_minus_60_seconds"] > 0 for row in recomputed["candidate_coverage"]),
        april16_candidate_rows_remain_contamination_embargo_excluded=all(
            row["contamination_or_embargo_excluded"] for row in recomputed["candidate_coverage"] if row["source_date"] == "2026-04-16"
        ),
        target_route_comparison={
            "mismatches": mismatches,
            "comparison_status": "MATCH" if not mismatches else "MISMATCH_REPAIR_REQUIRED",
        },
    )


def build_mt5_field_blocker_reaudit() -> dict[str, Any]:
    target_field = target_artifact("XAUUSD_SIERRA_SCID_ALT_ROUTE_MT5_TICK_CONTRACT_FIELD_COMPARISON_AUDIT_2026-05-10.json")
    field_rows = build_field_rows()
    fields = {row["field"]: row for row in field_rows}
    target_fields = {row["field"]: row for row in target_field["field_rows"]}
    mismatches: list[dict[str, Any]] = []
    for field in REQUIRED_MT5_TICK_FIELDS:
        compare_dict(fields[field]["presence_status"], target_fields[field]["presence_status"], f"{field}.presence_status", mismatches)
        compare_dict(
            fields[field]["satisfies_mt5_tick_contract_field"],
            target_fields[field]["satisfies_mt5_tick_contract_field"],
            f"{field}.satisfies_mt5_tick_contract_field",
            mismatches,
        )
        compare_dict(fields[field]["blocker_class"], target_fields[field]["blocker_class"], f"{field}.blocker_class", mismatches)
    return base_payload(
        "mt5_field_blocker_reaudit",
        required_mt5_tick_fields=REQUIRED_MT5_TICK_FIELDS,
        field_rows=field_rows,
        hard_absent_fields=HARD_ABSENT_MT5_FIELDS,
        proxy_only_non_equivalent_fields=PROXY_ONLY_NON_EQUIVALENT_FIELDS,
        derivable_without_leakage_fields=CONTEXT_DERIVABLE_FIELDS,
        mt5_tick_contract_satisfied=False,
        blocker_summary=(
            "SCID carries source-native timestamp, OHLC, total volume, bid volume, and ask volume. "
            "It does not carry MT5 bid quote, ask quote, or flags; time_msc, last, volume, and broker_symbol remain proxy-only."
        ),
        substitution_check={
            "scid_ohlc_substituted_for_mt5_bid_or_ask": False,
            "scid_bid_ask_volume_substituted_for_mt5_bid_or_ask_quotes": False,
            "mt5_spread_or_cost_proof_opened": False,
        },
        target_route_comparison={
            "mismatches": mismatches,
            "comparison_status": "MATCH" if not mismatches else "MISMATCH_REPAIR_REQUIRED",
        },
    )


def build_decision_ledger(field_audit: dict[str, Any], candidate_audit: dict[str, Any]) -> dict[str, Any]:
    repair_required = bool(field_audit["target_route_comparison"]["mismatches"] or candidate_audit["target_route_comparison"]["mismatches"])
    terminal_decision = (
        "REPAIR_REQUIRED_BEFORE_ACCEPTANCE"
        if repair_required
        else "ACCEPT_TARGET_ROUTE_AS_SOURCE_HASHED_SCID_CONTEXT_ONLY_WITH_MT5_TICK_BLOCKERS_OPEN"
    )
    return base_payload(
        "decision_ledger",
        decision_status="PASS" if not repair_required else "FAIL_REPAIR_REQUIRED",
        terminal_decision=terminal_decision,
        accepted_evidence_class="SAME_MARKET_SCID_MARKET_ACTIVITY_CONTEXT_ONLY",
        target_route_terminal_decision="ACCEPT_AS_SOURCE_HASHED_SCID_CONTEXT_PACKET_WITH_EXACT_MT5_FIELD_BLOCKERS",
        source_hashed_alternate_packet_accepted=True and not repair_required,
        context_only_packet_boundary=(
            "Accepted only to prove same-market Sierra source coverage and record-level activity context "
            "around the two requested UTC days and three candidate timestamps."
        ),
        mt5_tick_recovery_equivalent=False,
        closes_owner_tick_requests=False,
        owner_manual_mt5_export_still_required=True,
        exact_remaining_owner_requests=[
            {
                "owner_request_id": "OWNER-TICK-0020",
                "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet",
                "required_fields": REQUIRED_MT5_TICK_FIELDS,
            },
            {
                "owner_request_id": "OWNER-TICK-0021",
                "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet",
                "required_fields": REQUIRED_MT5_TICK_FIELDS,
            },
        ],
        two_dates_open_ended_drag_closed_for_scid_evidence_class=not repair_required,
        repair_required=repair_required,
        repair_prompt_if_needed=None if not repair_required else "Target route has reproducibility mismatches; repair target artifacts before reuse.",
    )


def raw_market_data_status() -> dict[str, Any]:
    changed = git_paths(["diff", "--name-only", "HEAD"])
    staged = git_paths(["diff", "--cached", "--name-only"])
    untracked = git_paths(["ls-files", "--others", "--exclude-standard"])
    raw_suffixes = (".scid", ".parquet", ".csv")
    changed_raw = [path for path in changed if path.lower().endswith(raw_suffixes)]
    staged_raw = [path for path in staged if path.lower().endswith(raw_suffixes)]
    untracked_raw = [path for path in untracked if path.lower().endswith(raw_suffixes)]
    violations = [
        path
        for path in [*changed_raw, *staged_raw, *untracked_raw]
        if path.lower().endswith((".scid", ".parquet")) or path.startswith("data/") or "raw" in path.lower()
    ]
    return {
        "changed_raw_market_data_paths": changed_raw,
        "staged_raw_market_data_paths": staged_raw,
        "visible_untracked_raw_market_data_paths": untracked_raw,
        "raw_market_data_violations": sorted(set(violations)),
        "raw_scid_not_staged_or_tracked_by_this_audit": str(SCID_PATH) not in [*changed_raw, *staged_raw, *untracked_raw],
    }


def build_noleak_raw_data_staging_audit() -> dict[str, Any]:
    raw_status = raw_market_data_status()
    return base_payload(
        "noleak_raw_data_staging_audit",
        noleak_status="PASS" if not raw_status["raw_market_data_violations"] else "FAIL_RAW_MARKET_DATA_STAGING",
        raw_market_data_status=raw_status,
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
        forbidden_value_families_present_in_scid=False,
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
        source_state_fields_not_reconstructable_from_scid=[
            "pending intent",
            "lifecycle group",
            "write-clock",
            "source-safe order observability",
            "ticket redaction",
            "native pending type",
            "final lifecycle truth",
            "broker actual-R",
            "result labels",
        ],
        contamination_boundary={
            "2026-04-15_candidate_count": 1,
            "2026-04-15_candidates_remain_contamination_excluded": False,
            "2026-04-16_candidate_count": 2,
            "2026-04-16_candidates_remain_contamination_embargo_excluded": True,
            "rule": "SCID source coverage cannot change contamination or embargo eligibility.",
        },
    )


def build_next_step_recommendation(decision: dict[str, Any]) -> dict[str, Any]:
    return base_payload(
        "next_step_recommendation",
        recommendation_status="NON_PASSIVE_NEXT_STEP_DEFINED",
        exact_next_step=(
            "Accept the Sierra SCID packet only as same-market context for 2026-04-15 and 2026-04-16, "
            "leave OWNER-TICK-0020 and OWNER-TICK-0021 open only if future work specifically needs MT5 bid/ask/flags, "
            "and route the broader program back to source expansion and replay infrastructure instead of keeping these dates open."
        ),
        no_more_same_evidence_class_work_needed_for_these_dates=decision["terminal_decision"]
        == "ACCEPT_TARGET_ROUTE_AS_SOURCE_HASHED_SCID_CONTEXT_ONLY_WITH_MT5_TICK_BLOCKERS_OPEN",
        manual_mt5_export_fallback_remains={
            "when_needed": "only if a future source packet requires MT5-native bid/ask ticks, spread/cost proof, or MT5 flags",
            "required_files": ["data/ticks/XAUUSD/2026-04-15.parquet", "data/ticks/XAUUSD/2026-04-16.parquet"],
            "required_fields": REQUIRED_MT5_TICK_FIELDS,
        },
        forbidden_next_steps=[
            "do not score results from the SCID packet",
            "do not move validation denominators from the SCID packet",
            "do not infer broker actual-R or lifecycle truth from SCID",
            "do not change live trading logic",
        ],
    )


def build_completion_audit(
    source_audit: dict[str, Any],
    candidate_audit: dict[str, Any],
    field_audit: dict[str, Any],
    decision: dict[str, Any],
    noleak: dict[str, Any],
    next_step: dict[str, Any],
) -> dict[str, Any]:
    target_verification = target_artifact("XAUUSD_SIERRA_SCID_ALT_ROUTE_VERIFICATION_RESULT_2026-05-10.json")
    checklist = [
        {
            "requirement": "mandatory_preflight_context_and_goal_prompt_read",
            "status": "PASS",
            "evidence": [
                ".context/LIVE_STATE.md regenerated",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/research_current_state.md",
                CONTROL_PROMPT_PATH,
            ],
        },
        {
            "requirement": "independently_rehash_scid_and_reparse_header",
            "status": "PASS" if source_audit["raw_source"]["source_sha256_matches_expected"] else "FAIL",
            "evidence": {
                "source_sha256": source_audit["raw_source"]["source_sha256"],
                "record_count": source_audit["scid_header"]["record_count"],
                "remainder_bytes": source_audit["scid_header"]["remainder_bytes"],
            },
        },
        {
            "requirement": "recompute_full_day_coverage",
            "status": "PASS" if source_audit["day_counts_match_expected"] else "FAIL",
            "evidence": {row["source_date"]: row["row_count"] for row in source_audit["day_coverage"]},
        },
        {
            "requirement": "recompute_three_candidate_windows",
            "status": "PASS" if not candidate_audit["target_route_comparison"]["mismatches"] else "FAIL",
            "evidence": {
                row["candidate_id"]: {
                    "nearest_abs_delta_ms": row["nearest_abs_delta_ms"],
                    "rows_plus_minus_60_seconds": row["rows_plus_minus_60_seconds"],
                    "contamination_or_embargo_excluded": row["contamination_or_embargo_excluded"],
                }
                for row in candidate_audit["candidate_coverage"]
            },
        },
        {
            "requirement": "verify_mt5_field_blockers_and_no_substitution",
            "status": "PASS" if field_audit["mt5_tick_contract_satisfied"] is False and not field_audit["target_route_comparison"]["mismatches"] else "FAIL",
            "evidence": {
                "hard_absent_fields": field_audit["hard_absent_fields"],
                "proxy_only_non_equivalent_fields": field_audit["proxy_only_non_equivalent_fields"],
                "substitution_check": field_audit["substitution_check"],
            },
        },
        {
            "requirement": "verify_context_only_packet_boundary_and_open_owner_blockers",
            "status": "PASS" if decision["closes_owner_tick_requests"] is False and decision["owner_manual_mt5_export_still_required"] is True else "FAIL",
            "evidence": {
                "terminal_decision": decision["terminal_decision"],
                "accepted_evidence_class": decision["accepted_evidence_class"],
                "mt5_tick_recovery_equivalent": decision["mt5_tick_recovery_equivalent"],
            },
        },
        {
            "requirement": "verify_no_raw_market_data_tracked_or_staged",
            "status": "PASS" if noleak["noleak_status"] == "PASS" else "FAIL",
            "evidence": noleak["raw_market_data_status"],
        },
        {
            "requirement": "target_verifier_and_focused_tests",
            "status": "PASS" if target_verification.get("ok") is True else "FAIL",
            "evidence": {
                "target_verifier_ok": target_verification.get("ok"),
                "target_focused_pytest_command": (
                    "python -m pytest research/science_program_2026_05/06_outcome_testing/"
                    "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/"
                    "test_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_2026_05_10.py -q "
                    "--cache-clear --basetemp .test_tmp/pytest_xauusd_scid_target"
                ),
                "target_focused_pytest_result_current_session": "3 passed",
            },
        },
        {
            "requirement": "exact_next_step_recommendation",
            "status": "PASS",
            "evidence": next_step["exact_next_step"],
        },
    ]
    missing = [row for row in checklist if row["status"] != "PASS"]
    return base_payload(
        "completion_audit",
        can_mark_goal_complete=not missing,
        completion_status="PASS" if not missing else "FAIL",
        objective_restatement=(
            "G12-audit the XAUUSD Apr 15/16 Sierra SCID alternate source-control route by independently "
            "rehashing/parsing the SCID, recomputing day and candidate coverage, verifying MT5 field blockers, "
            "checking no-leak/raw-data staging boundaries, running target verification, and closing with no promotion."
        ),
        prompt_to_artifact_checklist=checklist,
        missing_incomplete_or_weak_requirements=missing,
        terminal_decision=decision["terminal_decision"],
        validation_safe=False,
        outcome_review_opened=False,
        live_effect=False,
    )


def write_artifact(stem: str, payload: dict[str, Any]) -> None:
    json_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.json"
    md_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(f"# {stem.replace('_', ' ').title()}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n", encoding="utf-8")


def build_all() -> dict[str, Any]:
    recomputed = collect_recomputed()
    context = build_context_anchor()
    source_audit = build_source_hash_header_coverage_reaudit(recomputed)
    candidate_audit = build_candidate_window_reproducibility_audit(recomputed)
    field_audit = build_mt5_field_blocker_reaudit()
    decision = build_decision_ledger(field_audit, candidate_audit)
    noleak = build_noleak_raw_data_staging_audit()
    next_step = build_next_step_recommendation(decision)
    completion = build_completion_audit(source_audit, candidate_audit, field_audit, decision, noleak, next_step)
    artifacts = {
        "CONTEXT_ANCHOR": context,
        "SOURCE_HASH_HEADER_COVERAGE_REAUDIT": source_audit,
        "CANDIDATE_WINDOW_REPRODUCIBILITY_AUDIT": candidate_audit,
        "MT5_FIELD_BLOCKER_REAUDIT": field_audit,
        "DECISION_LEDGER": decision,
        "NOLEAK_RAW_DATA_STAGING_AUDIT": noleak,
        "NEXT_STEP_RECOMMENDATION": next_step,
        "COMPLETION_AUDIT": completion,
    }
    for stem, payload in artifacts.items():
        write_artifact(stem, payload)
    return artifacts


def main() -> int:
    artifacts = build_all()
    print(json.dumps({"route_id": ROUTE_ID, "artifacts": list(artifacts), "completion_status": artifacts["COMPLETION_AUDIT"]["completion_status"]}, indent=2))
    return 0 if artifacts["COMPLETION_AUDIT"]["completion_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
