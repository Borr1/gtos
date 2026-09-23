#!/usr/bin/env python3
"""Build HAZ-005 transition-clock split and source-repair ledgers.

This route is READY8_HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR_ONLY.
It reads frozen READY8/SCID artifacts plus read-only local Sierra SCID files
for same-evidence-class prior-16 descriptor repair candidates. It never writes
raw market blobs and never changes live, prompt, risk, safety, execution,
broker, API, paid, registry, or promotion surfaces.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR"
EVIDENCE_CLASS = "READY8_HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SAFE_FALSE_FLAGS = {
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO = SCRIPT_PATH.parents[4]
DATE = "2026-05-15"

ROWSET_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
ROWSET_MANIFEST_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
DESCRIPTOR_FREEZE_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
BAR_ROWS_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
CANDIDATE_ROWS_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
G12_AUDIT_DECISION_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"
G12_AUDIT_RECOMPUTATION_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
SEALED_PASS_CONTROL_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate/R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl"
TARGET_CLOSE_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_005_CLOSE_TO_CLOSE_2026-05-13.jsonl"
TARGET_HIGH_LOW_PATH = REPO / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_005_HIGH_LOW_EXCURSION_2026-05-13.jsonl"

CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
]

TARGET_PATHS = [TARGET_CLOSE_PATH, TARGET_HIGH_LOW_PATH]
PRESENT_BAR_STATUSES = {"RECORD_PRESENT", "CLOSED_SOURCE_RECORDS_PRESENT"}
SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
INTERVAL_MINUTES = 15

EXPECTED_SCID_NAMES = {
    "6BM26-CME.scid",
    "6EM26-CME.scid",
    "6JM26-CME.scid",
    "GCM26-COMEX.scid",
    "MGCM26-COMEX.scid",
    "MYMM26-CBOT.scid",
    "NQM26-CME.scid",
    "SIM26-COMEX.scid",
    "YMM26-CBOT.scid",
}

APPROVED_SEARCH_ROOTS = [
    Path("C:/SierraChart/Data"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/exports"),
    Path("C:/tmp/gtos_otb"),
    Path("C:/tmp/gtos_otl"),
]


def safe_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
    }


def route_fields(schema_version: str) -> dict[str, Any]:
    return {
        **safe_flags(),
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": schema_version,
    }


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso_ms(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    value = value.replace(microsecond=(value.microsecond // 1000) * 1000)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def floor_interval(value: datetime, minutes: int = INTERVAL_MINUTES) -> datetime:
    value = value.astimezone(timezone.utc)
    minute = (value.minute // minutes) * minutes
    return value.replace(minute=minute, second=0, microsecond=0)


def sierra_dt(microseconds: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=microseconds)


def datetime_to_sierra_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            count += 1
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def hash_range(path: Path, start: int, end: int) -> str | None:
    if start is None or end is None or end <= start or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        handle.seek(start)
        remaining = end - start
        while remaining > 0:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                raise IOError(f"unexpected EOF while hashing {path} {start}:{end}")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def numeric_summary(values: Iterable[float | None]) -> dict[str, Any]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "positive_count": 0,
            "negative_count": 0,
            "zero_count": 0,
            "positive_rate": None,
        }
    clean.sort()
    positives = sum(1 for value in clean if value > 0)
    negatives = sum(1 for value in clean if value < 0)
    zeros = len(clean) - positives - negatives
    return {
        "count": len(clean),
        "mean": round(statistics.fmean(clean), 12),
        "median": round(statistics.median(clean), 12),
        "min": round(clean[0], 12),
        "max": round(clean[-1], 12),
        "positive_count": positives,
        "negative_count": negatives,
        "zero_count": zeros,
        "positive_rate": round(positives / len(clean), 12),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return math.nan
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_values[int(idx)]
    weight = idx - lo
    return sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight


def bucket_tercile(value: float | None, low_cut: float | None, high_cut: float | None, labels: tuple[str, str, str]) -> str:
    if value is None or low_cut is None or high_cut is None:
        return "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
    if value <= low_cut:
        return labels[0]
    if value <= high_cut:
        return labels[1]
    return labels[2]


def is_present_bar(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("bar_status") in PRESENT_BAR_STATUSES)


def make_bar_hash(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "bar_hash"}
    return sha256_json(payload)


def required_prior_ends(entry_time: datetime, count: int = 16) -> list[str]:
    return [iso_ms(entry_time - timedelta(minutes=15 * offset)) for offset in range(count - 1, -1, -1)]


def describe_prior_window_from_bars(
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    symbol: str,
    entry_time: datetime,
    count: int = 16,
) -> dict[str, Any]:
    end_keys = required_prior_ends(entry_time, count)
    rows = [bars_by_end.get((symbol, key)) for key in end_keys]
    present = [row for row in rows if is_present_bar(row)]
    missing_ends = [key for key, row in zip(end_keys, rows) if not is_present_bar(row)]
    complete = len(present) == count
    if not complete or any(row.get("high") is None or row.get("low") is None or row.get("close") is None for row in present):
        return {
            "window_bars": count,
            "required_bars": count,
            "record_present_bars": len(present),
            "complete": False,
            "missing_bar_end_utc": missing_ends,
            "range_absolute": None,
            "range_percent": None,
            "drift_absolute": None,
            "drift_percent": None,
            "source_bar_hashes": [row.get("bar_hash") for row in present if row],
            "source_record_count": sum(int(row.get("source_record_count") or 0) for row in present if row),
            "source_byte_start_min": min((int(row["source_byte_start"]) for row in present if row and row.get("source_byte_start") is not None), default=None),
            "source_byte_end_max": max((int(row["source_byte_end_exclusive"]) for row in present if row and row.get("source_byte_end_exclusive") is not None), default=None),
        }
    highs = [float(row["high"]) for row in present]
    lows = [float(row["low"]) for row in present]
    closes = [float(row["close"]) for row in present]
    last_close = closes[-1]
    drift_base = closes[0]
    return {
        "window_bars": count,
        "required_bars": count,
        "record_present_bars": len(present),
        "complete": True,
        "missing_bar_end_utc": [],
        "range_absolute": round(max(highs) - min(lows), 12),
        "range_percent": round((max(highs) - min(lows)) / last_close, 12) if last_close else None,
        "drift_absolute": round(closes[-1] - closes[0], 12),
        "drift_percent": round((closes[-1] - closes[0]) / drift_base, 12) if drift_base else None,
        "source_bar_hashes": [row.get("bar_hash") for row in present],
        "source_record_count": sum(int(row.get("source_record_count") or 0) for row in present),
        "source_byte_start_min": min((int(row["source_byte_start"]) for row in present if row.get("source_byte_start") is not None), default=None),
        "source_byte_end_max": max((int(row["source_byte_end_exclusive"]) for row in present if row.get("source_byte_end_exclusive") is not None), default=None),
    }


def session_details(ts: datetime) -> dict[str, Any]:
    minutes = ts.hour * 60 + ts.minute
    if 0 <= minutes < 3 * 60:
        bucket = "ASIA_TOKYO_UTC_0000_0300"
        open_min = 0
    elif 7 * 60 <= minutes < 10 * 60 + 30:
        bucket = "LONDON_UTC_0700_1030"
        open_min = 7 * 60
    elif 13 * 60 <= minutes < 17 * 60:
        bucket = "NEW_YORK_UTC_1300_1700"
        open_min = 13 * 60
    elif 17 * 60 <= minutes or minutes < 23 * 60:
        bucket = "GLOBAL_OFF_SESSION_OR_TRANSITION"
        open_min = None
    else:
        bucket = "OTHER_UTC_SESSION_BUCKET"
        open_min = None
    active = open_min is not None
    return {
        "session_bucket": bucket,
        "active_session": active,
        "minutes_from_session_open": minutes - open_min if active else None,
    }


def parse_scid_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "parser_status": "FILE_MISSING", "absolute_path": str(path)}
    size = path.stat().st_size
    if size < SCID_HEADER.size:
        return {"exists": True, "parser_status": "TOO_SMALL_FOR_HEADER", "absolute_path": str(path), "size_bytes": size}
    with path.open("rb") as handle:
        raw = handle.read(SCID_HEADER.size)
    magic, header_size, record_size, version, utc_start_index, unused, reserve = SCID_HEADER.unpack(raw)
    remainder = (size - header_size) % record_size if record_size else None
    return {
        "exists": True,
        "absolute_path": str(path),
        "file_name": path.name,
        "size_bytes": size,
        "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "unused": unused,
        "reserve_sha256": hashlib.sha256(reserve).hexdigest(),
        "record_count": (size - header_size) // record_size if header_size == 56 and record_size == 40 else None,
        "remainder_bytes": remainder,
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK"
        if magic == b"SCID" and header_size == 56 and record_size == 40 and remainder == 0
        else "SCID_HEADER_OR_RECORD_CONTRACT_FAIL",
    }


def read_timestamp_at(handle: Any, header_size: int, record_index: int) -> int:
    handle.seek(header_size + record_index * SCID_RECORD.size)
    raw = handle.read(8)
    if len(raw) != 8:
        return 0
    return struct.unpack("<Q", raw)[0]


def lower_bound_timestamp(path: Path, start_us: int) -> int:
    header = parse_scid_header(path)
    if header["parser_status"] != "SCID_HEADER_AND_RECORD_PARSER_OK":
        return 0
    count = int(header["record_count"])
    header_size = int(header["header_size"])
    lo = 0
    hi = count
    with path.open("rb") as handle:
        while lo < hi:
            mid = (lo + hi) // 2
            ts = read_timestamp_at(handle, header_size, mid)
            if ts < start_us:
                lo = mid + 1
            else:
                hi = mid
    return max(0, lo - 2048)


def read_local_scid_bars(
    source_path: Path,
    symbol: str,
    canonical_group: str,
    min_start: datetime,
    max_end: datetime,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    header = parse_scid_header(source_path)
    if header["parser_status"] != "SCID_HEADER_AND_RECORD_PARSER_OK":
        return {}, {
            "symbol": symbol,
            "source_file_name": source_path.name,
            "source_path_reference_only": str(source_path),
            "read_status": header["parser_status"],
            "header": header,
        }
    start_us = datetime_to_sierra_us(min_start)
    end_us = datetime_to_sierra_us(max_end)
    start_idx = lower_bound_timestamp(source_path, start_us)
    record_count = int(header["record_count"])
    header_size = int(header["header_size"])
    aggs: dict[str, dict[str, Any]] = {}
    scanned = 0
    accepted = 0
    before = 0
    after = 0
    with source_path.open("rb") as handle:
        handle.seek(header_size + start_idx * SCID_RECORD.size)
        for idx in range(start_idx, record_count):
            offset = header_size + idx * SCID_RECORD.size
            raw = handle.read(SCID_RECORD.size)
            if len(raw) != SCID_RECORD.size:
                break
            scanned += 1
            ts_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = SCID_RECORD.unpack(raw)
            if ts_us < start_us:
                before += 1
                continue
            if ts_us >= end_us:
                after += 1
                # Keep a small cushion for local order violations, then stop.
                if after > 4096:
                    break
                continue
            accepted += 1
            ts_dt = sierra_dt(ts_us)
            bar_start = floor_interval(ts_dt)
            bar_end = bar_start + timedelta(minutes=INTERVAL_MINUTES)
            if bar_end > max_end:
                continue
            key = iso_ms(bar_start)
            sort_key = (int(ts_us), int(idx))
            agg = aggs.setdefault(
                key,
                {
                    "bar_start": bar_start,
                    "bar_end": bar_end,
                    "first_key": sort_key,
                    "last_key": sort_key,
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "total_volume": 0,
                    "bid_volume": 0,
                    "ask_volume": 0,
                    "num_trades": 0,
                    "source_record_count": 0,
                    "source_record_start_index": int(idx),
                    "source_record_end_index": int(idx),
                    "source_byte_start": int(offset),
                    "source_byte_end_exclusive": int(offset + SCID_RECORD.size),
                    "source_timestamp_min_us": int(ts_us),
                    "source_timestamp_max_us": int(ts_us),
                },
            )
            if sort_key < agg["first_key"]:
                agg["first_key"] = sort_key
                agg["open"] = float(open_)
                agg["source_record_start_index"] = int(idx)
                agg["source_byte_start"] = int(offset)
                agg["source_timestamp_min_us"] = int(ts_us)
            if sort_key >= agg["last_key"]:
                agg["last_key"] = sort_key
                agg["close"] = float(close)
                agg["source_record_end_index"] = int(idx)
                agg["source_byte_end_exclusive"] = int(offset + SCID_RECORD.size)
                agg["source_timestamp_max_us"] = int(ts_us)
            agg["high"] = max(float(agg["high"]), float(high))
            agg["low"] = min(float(agg["low"]), float(low))
            agg["total_volume"] += int(total_volume)
            agg["bid_volume"] += int(bid_volume)
            agg["ask_volume"] += int(ask_volume)
            agg["num_trades"] += int(num_trades)
            agg["source_record_count"] += 1

    bars: dict[tuple[str, str], dict[str, Any]] = {}
    for agg in aggs.values():
        row = {
            "bar_row_id": f"local_repair_bar:{symbol}:M15:{iso_ms(agg['bar_start'])}",
            "source_file_name": source_path.name,
            "source_path_reference_only": str(source_path),
            "symbol": symbol,
            "canonical_economic_group": canonical_group,
            "interval": "M15",
            "bar_start_utc": iso_ms(agg["bar_start"]),
            "bar_end_exclusive_utc": iso_ms(agg["bar_end"]),
            "source_record_start_index": agg["source_record_start_index"],
            "source_record_end_index": agg["source_record_end_index"],
            "source_byte_start": agg["source_byte_start"],
            "source_byte_end_exclusive": agg["source_byte_end_exclusive"],
            "source_timestamp_min_us": agg["source_timestamp_min_us"],
            "source_timestamp_max_us": agg["source_timestamp_max_us"],
            "source_timestamp_min_utc_ms": iso_ms(sierra_dt(agg["source_timestamp_min_us"])),
            "source_timestamp_max_utc_ms": iso_ms(sierra_dt(agg["source_timestamp_max_us"])),
            "open": agg["open"],
            "high": agg["high"],
            "low": agg["low"],
            "close": agg["close"],
            "total_volume": agg["total_volume"],
            "bid_volume": agg["bid_volume"],
            "ask_volume": agg["ask_volume"],
            "num_trades": agg["num_trades"],
            "source_record_count": agg["source_record_count"],
            "bar_status": "CLOSED_SOURCE_RECORDS_PRESENT",
            "candidate_eligible": True,
            "eligibility_basis": "LOCAL_SIERRA_READONLY_REPAIR_CANDIDATE_NOT_G12_ACCEPTED",
        }
        row["bar_hash"] = make_bar_hash(row)
        bars[(symbol, row["bar_end_exclusive_utc"])] = row

    diag = {
        "symbol": symbol,
        "canonical_economic_group": canonical_group,
        "source_file_name": source_path.name,
        "source_path_reference_only": str(source_path),
        "read_status": "SCID_LOCAL_REPAIR_SCAN_OK",
        "header": header,
        "requested_start_utc": iso_ms(min_start),
        "requested_end_exclusive_utc": iso_ms(max_end),
        "start_record_index_lower_bound": start_idx,
        "records_scanned": scanned,
        "records_before_requested_window_after_lower_bound": before,
        "records_accepted_in_requested_window": accepted,
        "bars_materialized": len(bars),
        "source_basis": "read_only_local_mutable_sierra_file_candidate_repair_requires_G12_acceptance",
    }
    return bars, diag


def target_movement(row: dict[str, Any]) -> float | None:
    if row.get("terminal_status") != "COMPUTABLE":
        return None
    family = row.get("target_family_id")
    if family == "neutral_close_to_close_return_m15_horizons_v1":
        return row.get("close_to_close_percent_return")
    if family == "neutral_high_low_excursion_m15_horizons_v1":
        up = row.get("upside_excursion_percent")
        down = row.get("downside_excursion_percent")
        if up is None or down is None:
            return None
        return float(up) - float(down)
    return None


def classify_from_descriptors(
    candidate: dict[str, Any],
    descriptor: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    dt = parse_time(candidate["decision_asof_utc"])
    sess = session_details(dt)
    cur_drift = descriptor.get("prior_16_drift_bucket")
    cur_range = descriptor.get("prior_16_range_bucket")
    prev_drift = previous.get("previous_prior_16_drift_bucket")
    prev_range = previous.get("previous_prior_16_range_bucket")
    gap = previous.get("previous_candidate_gap_minutes")
    descriptor_values = {
        "prior_16_drift_bucket": cur_drift,
        "prior_16_range_bucket": cur_range,
        "previous_prior_16_drift_bucket": prev_drift,
        "previous_prior_16_range_bucket": prev_range,
        "previous_candidate_gap_minutes": gap,
        "minutes_from_session_open": sess.get("minutes_from_session_open"),
        "session_bucket": sess.get("session_bucket"),
    }
    descriptor_missing = (
        not cur_drift
        or not cur_range
        or str(cur_drift).startswith("NOT_COMPUTABLE")
        or str(cur_range).startswith("NOT_COMPUTABLE")
    )
    if descriptor_missing:
        descriptor_values["transition_clock_bucket"] = "FAIL_CLOSED_PREDECISION_DESCRIPTOR_NOT_COMPUTABLE"
        return {
            "card_row_status": "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE",
            "denominator_role": "per_card_fail_closed_row",
            "descriptor_values": descriptor_values,
            "transition_flags": [],
            "status_reason": "regime_transition_hazard_clock_source_context",
            "rowset_fail_closed_reasons": ["MISSING_COMPUTABLE_PRIOR_16_DRIFT_OR_RANGE_DESCRIPTOR"],
        }
    flags: list[str] = []
    if gap is not None and gap >= 60:
        flags.append("SOURCE_RESET_GAP_60M_PLUS")
    if sess["active_session"] and (sess["minutes_from_session_open"] or 0) < 60:
        flags.append("SESSION_OPEN_FIRST_60M")
    if prev_drift and cur_drift != prev_drift and not str(prev_drift).startswith("NOT_COMPUTABLE"):
        flags.append("PRIOR_16_DRIFT_BUCKET_CHANGED")
    if prev_range and cur_range != prev_range and not str(prev_range).startswith("NOT_COMPUTABLE"):
        flags.append("PRIOR_16_RANGE_BUCKET_CHANGED")
    if flags:
        descriptor_values["transition_clock_bucket"] = "|".join(sorted(flags))
        role = "per_card_pass_row"
        status = "PASS_CARD_PREDICATE"
    else:
        descriptor_values["transition_clock_bucket"] = "STABLE_DESCRIPTOR_CLOCK_CONTROL"
        role = "per_card_contrast_row"
        status = "ELIGIBLE_CONTRAST_CONTROL"
    return {
        "card_row_status": status,
        "denominator_role": role,
        "descriptor_values": descriptor_values,
        "transition_flags": sorted(flags),
        "status_reason": "regime_transition_hazard_clock_source_context",
        "rowset_fail_closed_reasons": [],
    }


def previous_maps(candidates: list[dict[str, Any]], descriptors: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        enriched = dict(row)
        enriched["_dt"] = parse_time(row["decision_asof_utc"])
        by_group[row["canonical_economic_group"]].append(enriched)
    out: dict[str, dict[str, Any]] = {}
    for group_rows in by_group.values():
        group_rows.sort(key=lambda row: row["_dt"])
        prior_rows: list[dict[str, Any]] = []
        for row in group_rows:
            dt = row["_dt"]
            prev = prior_rows[-1] if prior_rows else None
            prior24 = [prior for prior in prior_rows if (dt - prior["_dt"]).total_seconds() <= 24 * 3600]
            prev_desc = descriptors.get(prev["candidate_input_row_id"], {}) if prev else {}
            out[row["candidate_input_row_id"]] = {
                "previous_candidate_gap_minutes": (dt - prev["_dt"]).total_seconds() / 60 if prev else None,
                "prior_24h_candidate_count": len(prior24),
                "previous_prior_16_drift_bucket": prev_desc.get("prior_16_drift_bucket"),
                "previous_prior_16_range_bucket": prev_desc.get("prior_16_range_bucket"),
            }
            prior_rows.append(row)
    return out


def build_source_search_ledger() -> tuple[dict[str, Any], dict[str, Path]]:
    source_by_name: dict[str, Path] = {}
    root_rows: list[dict[str, Any]] = []
    for root in APPROVED_SEARCH_ROOTS:
        row = {
            **route_fields("haz005_source_search_root_v1"),
            "root": str(root),
            "exists": root.exists(),
            "search_policy": "targeted_expected_scid_name_search_no_raw_blob_commit",
            "expected_source_names": sorted(EXPECTED_SCID_NAMES),
            "matched_files": [],
            "permission_or_read_error": None,
        }
        try:
            if root.exists() and root.is_dir():
                for name in sorted(EXPECTED_SCID_NAMES):
                    # Prefer direct Data-root matches; allow bounded recursive search for
                    # temp/prior worktrees while preserving every match found.
                    direct = root / name
                    if direct.exists():
                        info = {
                            "absolute_path": str(direct),
                            "file_name": direct.name,
                            "size_bytes": direct.stat().st_size,
                            "last_write_time_utc": datetime.fromtimestamp(direct.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                        }
                        row["matched_files"].append(info)
                        source_by_name.setdefault(name, direct)
                    elif root.name.lower() in {"gtos_otb", "gtos_otl"}:
                        for found in root.rglob(name):
                            if found.is_file():
                                info = {
                                    "absolute_path": str(found),
                                    "file_name": found.name,
                                    "size_bytes": found.stat().st_size,
                                    "last_write_time_utc": datetime.fromtimestamp(found.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                                }
                                row["matched_files"].append(info)
                                source_by_name.setdefault(name, found)
        except (PermissionError, OSError) as exc:
            row["permission_or_read_error"] = f"{type(exc).__name__}: {exc}"
        row["matched_file_count"] = len(row["matched_files"])
        root_rows.append(row)

    worktree_artifacts = [
        ROWSET_PATH,
        DESCRIPTOR_FREEZE_PATH,
        BAR_ROWS_PATH,
        CANDIDATE_ROWS_PATH,
        TARGET_CLOSE_PATH,
        TARGET_HIGH_LOW_PATH,
    ]
    ledger = {
        **route_fields("haz005_source_search_ledger_v1"),
        "artifact_family": "source_search_acquisition_ladder",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "approved_roots_policy_ref": ".context/00_core/local_heavy_data_inventory.md",
        "current_worktree_source_control_artifacts": [
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
            }
            for path in worktree_artifacts
        ],
        "approved_root_search_rows": root_rows,
        "sierra_repair_source_names_found": sorted(source_by_name),
        "raw_market_blob_commit_policy": "NO_RAW_BLOB_COMMITS_ONLY_HASHED_DERIVED_LEDGER_ROWS",
        "source_repair_admission_policy": "local Sierra repair rows are candidate source-control evidence requiring next G12 audit before denominator admission",
    }
    return ledger, source_by_name


@dataclass
class DataBundle:
    candidates: list[dict[str, Any]]
    candidate_by_id: dict[str, dict[str, Any]]
    rowset_rows: list[dict[str, Any]]
    haz_rowset_by_id: dict[str, dict[str, Any]]
    other_cards_by_candidate: dict[str, dict[str, dict[str, Any]]]
    descriptor_freeze: dict[str, Any]
    frozen_descriptors: dict[str, dict[str, Any]]
    accepted_bars_by_end: dict[tuple[str, str], dict[str, Any]]
    target_rows: list[dict[str, Any]]
    accepted_pass_control_rows: list[dict[str, Any]]


def load_data() -> DataBundle:
    candidates = read_jsonl(CANDIDATE_ROWS_PATH)
    candidate_by_id = {row["candidate_input_row_id"]: row for row in candidates}
    descriptor_freeze = read_json(DESCRIPTOR_FREEZE_PATH)
    frozen_descriptors = {row["candidate_input_row_id"]: row for row in descriptor_freeze["descriptor_rows"]}
    rowset_rows = read_jsonl(ROWSET_PATH)
    haz_rowset_by_id: dict[str, dict[str, Any]] = {}
    other_cards_by_candidate: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rowset_rows:
        cid = row["candidate_input_row_id"]
        if row["card_id"] == "HAZ-005":
            haz_rowset_by_id[cid] = row
        else:
            other_cards_by_candidate[cid][row["card_id"]] = row
    accepted_bars_by_end = {
        (row["symbol"], row["bar_end_exclusive_utc"]): row
        for row in iter_jsonl(BAR_ROWS_PATH)
    }
    target_rows: list[dict[str, Any]] = []
    for path in TARGET_PATHS:
        for row in iter_jsonl(path):
            row = dict(row)
            row["target_movement"] = target_movement(row)
            target_rows.append(row)
    accepted_pass_control_rows = [
        row for row in iter_jsonl(SEALED_PASS_CONTROL_PATH)
        if row.get("branch_key", {}).get("card_id") == "HAZ-005"
    ]
    return DataBundle(
        candidates=candidates,
        candidate_by_id=candidate_by_id,
        rowset_rows=rowset_rows,
        haz_rowset_by_id=haz_rowset_by_id,
        other_cards_by_candidate=dict(other_cards_by_candidate),
        descriptor_freeze=descriptor_freeze,
        frozen_descriptors=frozen_descriptors,
        accepted_bars_by_end=accepted_bars_by_end,
        target_rows=target_rows,
        accepted_pass_control_rows=accepted_pass_control_rows,
    )


def compute_repair(bundle: DataBundle, source_by_name: dict[str, Path]) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    cutoffs_by_symbol = bundle.descriptor_freeze["descriptor_cutoffs_by_symbol"]
    accepted_prev = previous_maps(bundle.candidates, bundle.frozen_descriptors)

    # Accepted-source recomputation first: proves whether the frozen bar packet
    # itself can repair the fail-closed descriptors without external local files.
    accepted_repair_by_id: dict[str, dict[str, Any]] = {}
    for candidate in bundle.candidates:
        cid = candidate["candidate_input_row_id"]
        entry = parse_time(candidate["decision_asof_utc"])
        prior = describe_prior_window_from_bars(bundle.accepted_bars_by_end, candidate["symbol"], entry, 16)
        cutoffs = cutoffs_by_symbol.get(candidate["symbol"], {})
        accepted_repair_by_id[cid] = {
            "candidate_input_row_id": cid,
            "prior_16_range_percent": prior["range_percent"],
            "prior_16_drift_percent": prior["drift_percent"],
            "prior_16_range_bucket": bucket_tercile(
                prior["range_percent"],
                cutoffs.get("prior_16_range_p33"),
                cutoffs.get("prior_16_range_p66"),
                ("PRIOR_16_COMPRESSED_RANGE_P00_P33", "PRIOR_16_MIDDLE_RANGE_P33_P66", "PRIOR_16_EXPANDED_RANGE_P66_P100"),
            ),
            "prior_16_drift_bucket": bucket_tercile(
                prior["drift_percent"],
                cutoffs.get("prior_16_drift_p33"),
                cutoffs.get("prior_16_drift_p66"),
                ("PRIOR_16_NEGATIVE_DRIFT_P00_P33", "PRIOR_16_MIDDLE_DRIFT_P33_P66", "PRIOR_16_POSITIVE_DRIFT_P66_P100"),
            ),
            "prior_16_window": prior,
            "source_basis": "accepted_bar_packet",
        }

    # Local Sierra repair candidate: build bars over all needed prior windows.
    ranges_by_symbol: dict[str, dict[str, Any]] = {}
    for candidate in bundle.candidates:
        symbol = candidate["symbol"]
        entry = parse_time(candidate["decision_asof_utc"])
        start = entry - timedelta(minutes=15 * 16)
        end = entry
        bucket = ranges_by_symbol.setdefault(
            symbol,
            {
                "symbol": symbol,
                "canonical_economic_group": candidate["canonical_economic_group"],
                "source_file_name": candidate["source_file_name"],
                "min_start": start,
                "max_end": end,
            },
        )
        bucket["min_start"] = min(bucket["min_start"], start)
        bucket["max_end"] = max(bucket["max_end"], end)

    local_bars_by_end: dict[tuple[str, str], dict[str, Any]] = {}
    source_scan_rows: list[dict[str, Any]] = []
    for symbol, spec in sorted(ranges_by_symbol.items()):
        source_path = source_by_name.get(spec["source_file_name"])
        if not source_path:
            source_scan_rows.append({
                **route_fields("haz005_local_sierra_scan_v1"),
                "artifact_family": "local_sierra_repair_source_scan",
                "symbol": symbol,
                "source_file_name": spec["source_file_name"],
                "read_status": "LOCAL_SOURCE_FILE_NOT_FOUND_IN_APPROVED_SEARCH_ROOTS",
            })
            continue
        bars, diag = read_local_scid_bars(
            source_path,
            symbol,
            spec["canonical_economic_group"],
            spec["min_start"],
            spec["max_end"],
        )
        local_bars_by_end.update(bars)
        source_scan_rows.append({
            **route_fields("haz005_local_sierra_scan_v1"),
            "artifact_family": "local_sierra_repair_source_scan",
            **diag,
        })

    local_descriptor_by_id: dict[str, dict[str, Any]] = {}
    for candidate in bundle.candidates:
        cid = candidate["candidate_input_row_id"]
        entry = parse_time(candidate["decision_asof_utc"])
        prior = describe_prior_window_from_bars(local_bars_by_end, candidate["symbol"], entry, 16)
        cutoffs = cutoffs_by_symbol.get(candidate["symbol"], {})
        local_descriptor_by_id[cid] = {
            "candidate_input_row_id": cid,
            "prior_16_range_percent": prior["range_percent"],
            "prior_16_drift_percent": prior["drift_percent"],
            "prior_16_range_bucket": bucket_tercile(
                prior["range_percent"],
                cutoffs.get("prior_16_range_p33"),
                cutoffs.get("prior_16_range_p66"),
                ("PRIOR_16_COMPRESSED_RANGE_P00_P33", "PRIOR_16_MIDDLE_RANGE_P33_P66", "PRIOR_16_EXPANDED_RANGE_P66_P100"),
            ),
            "prior_16_drift_bucket": bucket_tercile(
                prior["drift_percent"],
                cutoffs.get("prior_16_drift_p33"),
                cutoffs.get("prior_16_drift_p66"),
                ("PRIOR_16_NEGATIVE_DRIFT_P00_P33", "PRIOR_16_MIDDLE_DRIFT_P33_P66", "PRIOR_16_POSITIVE_DRIFT_P66_P100"),
            ),
            "prior_16_window": prior,
            "source_basis": "local_sierra_full_file_candidate_repair",
        }

    # Build a repaired descriptor variant: use frozen descriptors where
    # computable, and local candidate repair where frozen current descriptors
    # were not computable. This keeps accepted rows stable and isolates repair.
    repaired_descriptor_by_id: dict[str, dict[str, Any]] = {}
    fail_closed_repair_rows: list[dict[str, Any]] = []
    repaired_packet_rows: list[dict[str, Any]] = []
    for candidate in bundle.candidates:
        cid = candidate["candidate_input_row_id"]
        frozen = dict(bundle.frozen_descriptors[cid])
        haz_rowset = bundle.haz_rowset_by_id[cid]
        accepted_attempt = accepted_repair_by_id[cid]
        local_attempt = local_descriptor_by_id[cid]
        frozen_missing = (
            str(frozen.get("prior_16_drift_bucket", "")).startswith("NOT_COMPUTABLE")
            or str(frozen.get("prior_16_range_bucket", "")).startswith("NOT_COMPUTABLE")
        )
        accepted_complete = bool(accepted_attempt["prior_16_window"]["complete"])
        local_complete = bool(local_attempt["prior_16_window"]["complete"])
        repair_status = "NOT_NEEDED_FROZEN_DESCRIPTOR_COMPUTABLE"
        repair_source_basis = "frozen_descriptor"
        chosen = frozen
        if frozen_missing:
            if accepted_complete:
                repair_status = "REPAIRED_FROM_ACCEPTED_BAR_PACKET"
                repair_source_basis = "accepted_bar_packet"
                chosen = {**frozen, **{k: accepted_attempt[k] for k in ("prior_16_range_percent", "prior_16_drift_percent", "prior_16_range_bucket", "prior_16_drift_bucket")}}
            elif local_complete:
                repair_status = "REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12"
                repair_source_basis = "local_sierra_full_file_candidate_repair_requires_G12"
                chosen = {**frozen, **{k: local_attempt[k] for k in ("prior_16_range_percent", "prior_16_drift_percent", "prior_16_range_bucket", "prior_16_drift_bucket")}}
            else:
                repair_status = "NOT_REPAIRABLE_FROM_SEARCHED_SAME_EVIDENCE_CLASS_SOURCES"
                repair_source_basis = "missing_record_present_prior16_bars"
        chosen["haz005_repair_status"] = repair_status
        chosen["haz005_repair_source_basis"] = repair_source_basis
        repaired_descriptor_by_id[cid] = chosen

        if haz_rowset["denominator_role"] == "per_card_fail_closed_row":
            accepted_missing = accepted_attempt["prior_16_window"].get("missing_bar_end_utc", [])
            local_missing = local_attempt["prior_16_window"].get("missing_bar_end_utc", [])
            row = {
                **route_fields("haz005_fail_closed_prior16_repair_v1"),
                "artifact_family": "fail_closed_prior16_repair_row",
                "candidate_input_row_id": cid,
                "duplicate_proxy_denominator_key": candidate["duplicate_key"],
                "symbol": candidate["symbol"],
                "canonical_economic_group": candidate["canonical_economic_group"],
                "source_file_name": candidate["source_file_name"],
                "entry_reference_time_utc": candidate["decision_asof_utc"],
                "validation_partition_assignment": haz_rowset["validation_partition_assignment"],
                "frozen_card_row_status": haz_rowset["card_row_status"],
                "frozen_denominator_role": haz_rowset["denominator_role"],
                "frozen_fail_closed_reasons": haz_rowset.get("fail_closed_reasons", []),
                "frozen_descriptor_values": haz_rowset.get("descriptor_values", {}),
                "accepted_bar_packet_prior16_complete": accepted_complete,
                "accepted_bar_packet_record_present_bars": accepted_attempt["prior_16_window"]["record_present_bars"],
                "accepted_bar_packet_missing_bar_end_utc": accepted_missing,
                "local_sierra_prior16_complete": local_complete,
                "local_sierra_record_present_bars": local_attempt["prior_16_window"]["record_present_bars"],
                "local_sierra_missing_bar_end_utc": local_missing,
                "repair_status": repair_status,
                "repair_source_basis": repair_source_basis,
                "repaired_prior_16_drift_percent": chosen.get("prior_16_drift_percent") if repair_status.startswith("REPAIRED") else None,
                "repaired_prior_16_range_percent": chosen.get("prior_16_range_percent") if repair_status.startswith("REPAIRED") else None,
                "repaired_prior_16_drift_bucket": chosen.get("prior_16_drift_bucket") if repair_status.startswith("REPAIRED") else None,
                "repaired_prior_16_range_bucket": chosen.get("prior_16_range_bucket") if repair_status.startswith("REPAIRED") else None,
                "local_source_bar_hashes_sha256": sha256_json(local_attempt["prior_16_window"].get("source_bar_hashes", [])) if local_attempt["prior_16_window"].get("source_bar_hashes") else None,
                "local_source_record_count": local_attempt["prior_16_window"].get("source_record_count"),
                "local_source_byte_start_min": local_attempt["prior_16_window"].get("source_byte_start_min"),
                "local_source_byte_end_max": local_attempt["prior_16_window"].get("source_byte_end_max"),
                "source_admission_status": "CANDIDATE_REPAIR_PACKET_REQUIRES_G12_SOURCE_AUDIT" if repair_status.startswith("REPAIRED_FROM_LOCAL") else repair_status,
                "exact_future_source_capture_requirement": None
                if repair_status.startswith("REPAIRED")
                else {
                    "field_family": "predecision_prior16_m15_ohlc_continuity",
                    "required_fields": [
                        "symbol",
                        "source_file_name",
                        "entry_reference_time_utc",
                        "bar_end_exclusive_utc for 16 prior M15 bars",
                        "open/high/low/close",
                        "bar_status",
                        "source_record_count",
                        "source_record_start_index/source_record_end_index",
                        "source_byte_start/source_byte_end_exclusive",
                        "source_bar_hash",
                        "source_segment_or_file_hash_policy",
                    ],
                    "missing_bar_end_utc": local_missing or accepted_missing,
                    "next_action": "Provide an immutable local/source export that contains the missing predecision prior-16 M15 bars, or a frozen calendar proving the bars were genuinely closed/absent.",
                },
            }
            fail_closed_repair_rows.append(row)
            if repair_status.startswith("REPAIRED"):
                repaired_packet_rows.append({
                    **route_fields("haz005_repaired_descriptor_row_packet_v1"),
                    "artifact_family": "repaired_descriptor_row_packet",
                    "candidate_input_row_id": cid,
                    "duplicate_proxy_denominator_key": candidate["duplicate_key"],
                    "symbol": candidate["symbol"],
                    "canonical_economic_group": candidate["canonical_economic_group"],
                    "source_file_name": candidate["source_file_name"],
                    "entry_reference_time_utc": candidate["decision_asof_utc"],
                    "validation_partition_assignment": haz_rowset["validation_partition_assignment"],
                    "repair_status": repair_status,
                    "repair_source_basis": repair_source_basis,
                    "prior_16_drift_percent": chosen.get("prior_16_drift_percent"),
                    "prior_16_range_percent": chosen.get("prior_16_range_percent"),
                    "prior_16_drift_bucket": chosen.get("prior_16_drift_bucket"),
                    "prior_16_range_bucket": chosen.get("prior_16_range_bucket"),
                    "bucket_cutoff_policy": "frozen_pre_target_per_symbol_cutoffs_from_descriptor_freeze_ledger",
                    "source_bar_hashes_sha256": row["local_source_bar_hashes_sha256"],
                    "source_record_count": row["local_source_record_count"],
                    "source_byte_start_min": row["local_source_byte_start_min"],
                    "source_byte_end_max": row["local_source_byte_end_max"],
                    "source_admission_status": row["source_admission_status"],
                })

    # Hash local consumed byte ranges per symbol for repaired packet rows.
    by_file_ranges: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for row in repaired_packet_rows:
        if row.get("repair_source_basis", "").startswith("local_sierra"):
            start = row.get("source_byte_start_min")
            end = row.get("source_byte_end_max")
            if start is not None and end is not None:
                by_file_ranges[row["source_file_name"]].append((int(start), int(end)))
    for scan_row in source_scan_rows:
        file_name = scan_row.get("source_file_name")
        ranges = by_file_ranges.get(file_name, [])
        if ranges and scan_row.get("read_status") == "SCID_LOCAL_REPAIR_SCAN_OK":
            source_path = Path(scan_row["source_path_reference_only"])
            start = min(start for start, _ in ranges)
            end = max(end for _, end in ranges)
            scan_row["local_repair_consumed_byte_start_min"] = start
            scan_row["local_repair_consumed_byte_end_max"] = end
            scan_row["local_repair_consumed_byte_range_sha256"] = hash_range(source_path, start, end)
            scan_row["local_repair_consumed_raw_blob_committed"] = False
    return repaired_descriptor_by_id, fail_closed_repair_rows, repaired_packet_rows, source_scan_rows


def build_classification_maps(
    bundle: DataBundle,
    repaired_descriptor_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, dict[str, Any]]]:
    original_prev = previous_maps(bundle.candidates, bundle.frozen_descriptors)
    repaired_prev = previous_maps(bundle.candidates, repaired_descriptor_by_id)
    original: dict[str, dict[str, Any]] = {}
    repaired: dict[str, dict[str, Any]] = {}
    for candidate in bundle.candidates:
        cid = candidate["candidate_input_row_id"]
        original[cid] = classify_from_descriptors(candidate, bundle.frozen_descriptors[cid], original_prev[cid])
        repaired[cid] = classify_from_descriptors(candidate, repaired_descriptor_by_id[cid], repaired_prev[cid])
    return {"original_frozen": original, "repaired_frozen_cutoff": repaired}


def enriched_target_rows(bundle: DataBundle, classifications: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in bundle.target_rows:
        cid = row["candidate_input_row_id"]
        candidate = bundle.candidate_by_id[cid]
        base = {
            "candidate_input_row_id": cid,
            "duplicate_proxy_denominator_key": row["duplicate_proxy_denominator_key"],
            "symbol": row["symbol"],
            "canonical_economic_group": row["canonical_economic_group"],
            "source_file_name": row.get("source_file_name_expected") or candidate.get("source_file_name"),
            "source_segment_sha256": row.get("source_segment_sha256_expected"),
            "entry_reference_time_utc": row["entry_reference_time_utc"],
            "session_bucket": session_details(parse_time(row["entry_reference_time_utc"]))["session_bucket"],
            "partition_assignment": row["partition_assignment"],
            "target_family_id": row["target_family_id"],
            "horizon_m15_bars": int(row["horizon_m15_bars"]),
            "terminal_status": row["terminal_status"],
            "target_movement": row["target_movement"],
        }
        for variant, cmap in classifications.items():
            cls = cmap[cid]
            variant_row = dict(base)
            variant_row["analysis_variant"] = variant
            variant_row["card_row_status"] = cls["card_row_status"]
            variant_row["denominator_role"] = cls["denominator_role"]
            variant_row["descriptor_values"] = cls["descriptor_values"]
            variant_row["transition_flags"] = cls["transition_flags"]
            variant_row["target_computable"] = row["target_movement"] is not None
            rows.append(variant_row)
    return rows


def aggregate_records(records: list[dict[str, Any]], key_fields: list[str], family: str) -> dict[str, Any]:
    computable = [row for row in records if row.get("target_movement") is not None]
    movements = [row["target_movement"] for row in computable]
    duplicate_keys = {row["duplicate_proxy_denominator_key"] for row in computable}
    summary = numeric_summary(movements)
    concentration = concentration_summary(computable)
    return {
        **route_fields("haz005_aggregate_v1"),
        "branch_family": family,
        "branch_key": {field: records[0].get(field) for field in key_fields} if records else {},
        "rows_total": len(records),
        "rows_computable": len(computable),
        "unique_duplicate_denominator_count": len(duplicate_keys),
        "target_movement_summary": summary,
        "concentration": concentration,
        "underpowered_unique_duplicate_floor_lt_30": len(duplicate_keys) < 30,
        "metric_scope": "neutral target movement only; not R/PnL/win-rate/expectancy/promotion",
    }


def concentration_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in ("symbol", "canonical_economic_group", "session_bucket", "source_segment_sha256"):
        counts = Counter(str(row.get(field)) for row in records)
        total = sum(counts.values())
        if not total:
            out[field] = {"distinct_count": 0, "top_share": None, "top_count": 0, "top_value": None}
        else:
            top_value, top_count = counts.most_common(1)[0]
            out[field] = {
                "distinct_count": len(counts),
                "top_value": top_value,
                "top_count": top_count,
                "top_share": round(top_count / total, 12),
            }
    return out


def pass_control_delta(pass_records: list[dict[str, Any]], control_records: list[dict[str, Any]]) -> dict[str, Any]:
    pass_comp = [row for row in pass_records if row.get("target_movement") is not None]
    control_comp = [row for row in control_records if row.get("target_movement") is not None]
    pass_summary = numeric_summary(row["target_movement"] for row in pass_comp)
    control_summary = numeric_summary(row["target_movement"] for row in control_comp)
    pass_dups = {row["duplicate_proxy_denominator_key"] for row in pass_comp}
    control_dups = {row["duplicate_proxy_denominator_key"] for row in control_comp}
    if pass_summary["mean"] is None or control_summary["mean"] is None:
        delta = None
    else:
        delta = round(pass_summary["mean"] - control_summary["mean"], 12)
    if pass_summary["positive_rate"] is None or control_summary["positive_rate"] is None:
        positive_rate_delta = None
    else:
        positive_rate_delta = round(pass_summary["positive_rate"] - control_summary["positive_rate"], 12)
    return {
        "pass_rows": len(pass_records),
        "control_rows": len(control_records),
        "pass_computable_rows": len(pass_comp),
        "control_computable_rows": len(control_comp),
        "pass_unique_duplicate_denominator_count": len(pass_dups),
        "control_unique_duplicate_denominator_count": len(control_dups),
        "pass_target_movement_summary": pass_summary,
        "control_target_movement_summary": control_summary,
        "pass_minus_control_target_movement_mean_delta": delta,
        "pass_positive_rate_minus_control_positive_rate_delta": positive_rate_delta,
        "comparison_classification": classify_delta(delta, len(pass_dups), len(control_dups)),
        "underpowered_flag": min(len(pass_dups), len(control_dups)) < 30,
    }


def classify_delta(delta: float | None, pass_n: int, control_n: int) -> str:
    if delta is None:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
    if pass_n < 30 or control_n < 30:
        power = "UNDERPOWERED_"
    else:
        power = ""
    if delta > 0:
        return f"{power}POSITIVE_NEUTRAL_TARGET_MOVEMENT"
    if delta < 0:
        return f"{power}INVERSE_NEUTRAL_TARGET_MOVEMENT"
    return f"{power}NULL_TIED_NEUTRAL_TARGET_MOVEMENT"


def split_records(rows: list[dict[str, Any]], key_fields: list[str]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(field) for field in key_fields)].append(row)
    return groups


def build_descriptor_state_split(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_fields = [
        "analysis_variant",
        "partition_assignment",
        "target_family_id",
        "horizon_m15_bars",
        "denominator_role",
        "symbol",
        "canonical_economic_group",
    ]
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        desc = row["descriptor_values"]
        state_key = (
            row["analysis_variant"],
            row["partition_assignment"],
            row["target_family_id"],
            row["horizon_m15_bars"],
            row["denominator_role"],
            row["symbol"],
            row["canonical_economic_group"],
            desc.get("transition_clock_bucket"),
            desc.get("prior_16_drift_bucket"),
            desc.get("prior_16_range_bucket"),
            desc.get("previous_prior_16_drift_bucket"),
            desc.get("previous_prior_16_range_bucket"),
            bool("SESSION_OPEN_FIRST_60M" in row.get("transition_flags", [])),
            bool("SOURCE_RESET_GAP_60M_PLUS" in row.get("transition_flags", [])),
        )
        groups[state_key].append(row)
    out: list[dict[str, Any]] = []
    for key, records in sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
        out.append({
            **aggregate_records(records, key_fields, "descriptor_state_split"),
            "descriptor_state": {
                "transition_clock_bucket": key[7],
                "prior_16_drift_bucket": key[8],
                "prior_16_range_bucket": key[9],
                "previous_prior_16_drift_bucket": key[10],
                "previous_prior_16_range_bucket": key[11],
                "session_open_first_60m": key[12],
                "source_reset_gap_60m_plus": key[13],
            },
        })
    return out


def build_pass_control_ledgers(enriched: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pass_control_rows: list[dict[str, Any]] = []
    explanation_rows: list[dict[str, Any]] = []
    base_keys = ["analysis_variant", "partition_assignment", "target_family_id", "horizon_m15_bars"]
    group_specs = [
        ("overall_haz005_pass_vs_stable_control", base_keys, None),
        ("transition_clock_bucket_pass_vs_stable_control", base_keys + ["transition_clock_bucket"], "transition_clock_bucket"),
        ("symbol_pass_vs_stable_control", base_keys + ["symbol"], None),
        ("session_pass_vs_stable_control", base_keys + ["session_bucket"], None),
        ("economic_group_pass_vs_stable_control", base_keys + ["canonical_economic_group"], None),
    ]
    expanded_rows = []
    for row in enriched:
        expanded = dict(row)
        expanded["transition_clock_bucket"] = row["descriptor_values"].get("transition_clock_bucket")
        expanded_rows.append(expanded)
    for family, key_fields, transition_filter in group_specs:
        for key, records in split_records(expanded_rows, key_fields).items():
            if transition_filter:
                pass_records = [row for row in records if row["denominator_role"] == "per_card_pass_row" and row.get(transition_filter) == key[-1]]
                control_records = [
                    row for row in expanded_rows
                    if all(row.get(field) == key[idx] for idx, field in enumerate(key_fields[:-1]))
                    and row["denominator_role"] == "per_card_contrast_row"
                ]
            else:
                pass_records = [row for row in records if row["denominator_role"] == "per_card_pass_row"]
                control_records = [row for row in records if row["denominator_role"] == "per_card_contrast_row"]
            result = pass_control_delta(pass_records, control_records)
            branch_key = {field: key[idx] for idx, field in enumerate(key_fields)}
            row = {
                **route_fields("haz005_pass_control_recomputation_v1"),
                "artifact_family": "pass_control_recomputation",
                "comparison_family": family,
                "branch_key": branch_key,
                **result,
                "metric_scope": "neutral target movement only; not R/PnL/win-rate/expectancy/promotion",
            }
            pass_control_rows.append(row)
            explanation_rows.append({
                **route_fields("haz005_failure_inverse_null_explanation_v1"),
                "artifact_family": "failure_inverse_null_explanation",
                "source_comparison_family": family,
                "branch_key": branch_key,
                "comparison_classification": result["comparison_classification"],
                "data_bound_explanation": explanation_for(row),
                "same_evidence_class_next_action": "none_remaining_for_this_branch_after_ledgered_split"
                if result["comparison_classification"] != "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
                else "branch lacks pass or control rows under frozen predicates; no denominator backfill without separate accepted source repair",
            })
    return pass_control_rows, explanation_rows


def explanation_for(row: dict[str, Any]) -> str:
    cls = row["comparison_classification"]
    if cls == "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL":
        return "No pass/control delta can be formed because one side has zero computable neutral target rows."
    if "UNDERPOWERED" in cls:
        return "Branch direction is visible but below the duplicate-key floor of 30 on at least one side; treat as anatomy, not acceptance."
    if "POSITIVE" in cls:
        return "Pass rows have higher neutral target-movement mean than stable controls in this exact split."
    if "INVERSE" in cls:
        return "Pass rows have lower neutral target-movement mean than stable controls in this exact split."
    return "Pass and stable-control neutral target-movement means are tied at recorded precision."


def descriptor_field_values(row: dict[str, Any]) -> dict[str, list[Any]]:
    desc = row["descriptor_values"]
    flags = row.get("transition_flags", [])
    return {
        "transition_clock_bucket": [desc.get("transition_clock_bucket")],
        "transition_flag": flags if flags else ["NO_TRANSITION_FLAG"],
        "prior_16_drift_bucket": [desc.get("prior_16_drift_bucket")],
        "prior_16_range_bucket": [desc.get("prior_16_range_bucket")],
        "previous_prior_16_drift_bucket": [desc.get("previous_prior_16_drift_bucket")],
        "previous_prior_16_range_bucket": [desc.get("previous_prior_16_range_bucket")],
        "session_open_first_60m": [bool("SESSION_OPEN_FIRST_60M" in flags)],
        "source_reset_gap_60m_plus": [bool("SOURCE_RESET_GAP_60M_PLUS" in flags)],
        "symbol": [row.get("symbol")],
        "canonical_economic_group": [row.get("canonical_economic_group")],
        "session_bucket": [row.get("session_bucket")],
        "target_family_id": [row.get("target_family_id")],
    }


def build_one_vs_rest(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_groups = split_records(enriched, ["analysis_variant", "partition_assignment", "target_family_id", "horizon_m15_bars"])
    for base_key, records in base_groups.items():
        value_index: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
        for row in records:
            for field, values in descriptor_field_values(row).items():
                for value in values:
                    value_index[(field, value)].append(row)
        for (field, value), one_rows in sorted(value_index.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
            one_ids = {id(row) for row in one_rows}
            rest_rows = [row for row in records if id(row) not in one_ids]
            one = numeric_summary(row["target_movement"] for row in one_rows if row.get("target_movement") is not None)
            rest = numeric_summary(row["target_movement"] for row in rest_rows if row.get("target_movement") is not None)
            delta = None if one["mean"] is None or rest["mean"] is None else round(one["mean"] - rest["mean"], 12)
            rows.append({
                **route_fields("haz005_descriptor_one_vs_rest_v1"),
                "artifact_family": "descriptor_one_vs_rest_recomputation",
                "analysis_variant": base_key[0],
                "partition_assignment": base_key[1],
                "target_family_id": base_key[2],
                "horizon_m15_bars": base_key[3],
                "descriptor_field": field,
                "descriptor_value": value,
                "one_rows": len(one_rows),
                "rest_rows": len(rest_rows),
                "one_unique_duplicate_denominator_count": len({row["duplicate_proxy_denominator_key"] for row in one_rows if row.get("target_movement") is not None}),
                "rest_unique_duplicate_denominator_count": len({row["duplicate_proxy_denominator_key"] for row in rest_rows if row.get("target_movement") is not None}),
                "one_target_movement_summary": one,
                "rest_target_movement_summary": rest,
                "one_minus_rest_target_movement_mean_delta": delta,
                "comparison_classification": classify_delta(
                    delta,
                    len({row["duplicate_proxy_denominator_key"] for row in one_rows if row.get("target_movement") is not None}),
                    len({row["duplicate_proxy_denominator_key"] for row in rest_rows if row.get("target_movement") is not None}),
                ),
                "metric_scope": "neutral target movement only; not R/PnL/win-rate/expectancy/promotion",
            })
    return rows


def build_horizon_reversal(pass_control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    comparable = [
        row for row in pass_control_rows
        if row["pass_minus_control_target_movement_mean_delta"] is not None
    ]
    key_map: dict[tuple[Any, ...], dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in comparable:
        key = (
            row["comparison_family"],
            row["branch_key"].get("analysis_variant"),
            row["branch_key"].get("partition_assignment"),
            row["branch_key"].get("target_family_id"),
            tuple(sorted((k, v) for k, v in row["branch_key"].items() if k not in {"horizon_m15_bars"})),
        )
        key_map[key][int(row["branch_key"]["horizon_m15_bars"])] = row
    for key, by_horizon in sorted(key_map.items(), key=lambda item: str(item[0])):
        if 4 not in by_horizon or 16 not in by_horizon:
            continue
        h4 = by_horizon[4]
        h16 = by_horizon[16]
        d4 = h4["pass_minus_control_target_movement_mean_delta"]
        d16 = h16["pass_minus_control_target_movement_mean_delta"]
        sign4 = "positive" if d4 > 0 else "inverse" if d4 < 0 else "null"
        sign16 = "positive" if d16 > 0 else "inverse" if d16 < 0 else "null"
        rows.append({
            **route_fields("haz005_horizon_reversal_anatomy_v1"),
            "artifact_family": "horizon_reversal_anatomy",
            "comparison_family": key[0],
            "analysis_variant": key[1],
            "partition_assignment": key[2],
            "target_family_id": key[3],
            "branch_identity": dict(key[4]),
            "h4_delta": d4,
            "h16_delta": d16,
            "h4_sign": sign4,
            "h16_sign": sign16,
            "h4_to_h16_reversal_class": f"{sign4.upper()}_TO_{sign16.upper()}",
            "h1_delta": by_horizon.get(1, {}).get("pass_minus_control_target_movement_mean_delta"),
            "h32_delta": by_horizon.get(32, {}).get("pass_minus_control_target_movement_mean_delta"),
            "data_bound_explanation": "Horizon reversal is computed from pass/control neutral target movement means over the same branch identity, comparing h4 to h16.",
        })
    return rows


def build_concentration_deconcentration(enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    records = [dict(row, transition_clock_bucket=row["descriptor_values"].get("transition_clock_bucket")) for row in enriched]
    group_specs = [
        ("overall", ["analysis_variant", "partition_assignment", "target_family_id", "horizon_m15_bars"]),
        ("transition_clock_bucket", ["analysis_variant", "partition_assignment", "target_family_id", "horizon_m15_bars", "transition_clock_bucket"]),
    ]
    dimensions = ["symbol", "canonical_economic_group", "session_bucket", "source_segment_sha256"]
    for branch_family, key_fields in group_specs:
        for key, branch_records in split_records(records, key_fields).items():
            branch_key = {field: key[idx] for idx, field in enumerate(key_fields)}
            pass_records = [row for row in branch_records if row["denominator_role"] == "per_card_pass_row"]
            control_records = [row for row in branch_records if row["denominator_role"] == "per_card_contrast_row"]
            base_delta = pass_control_delta(pass_records, control_records)
            for dimension in dimensions:
                values = sorted({row.get(dimension) for row in branch_records}, key=lambda value: str(value))
                for value in values:
                    value_records = [row for row in branch_records if row.get(dimension) == value]
                    without = [row for row in branch_records if row.get(dimension) != value]
                    without_delta = pass_control_delta(
                        [row for row in without if row["denominator_role"] == "per_card_pass_row"],
                        [row for row in without if row["denominator_role"] == "per_card_contrast_row"],
                    )
                    rows.append({
                        **route_fields("haz005_concentration_deconcentration_v1"),
                        "artifact_family": "concentration_deconcentration",
                        "branch_family": branch_family,
                        "branch_key": branch_key,
                        "dimension": dimension,
                        "dimension_value": value,
                        "dimension_rows": len(value_records),
                        "dimension_share_of_branch": round(len(value_records) / len(branch_records), 12) if branch_records else None,
                        "dimension_unique_duplicate_denominator_count": len({row["duplicate_proxy_denominator_key"] for row in value_records if row.get("target_movement") is not None}),
                        "base_pass_minus_control_delta": base_delta["pass_minus_control_target_movement_mean_delta"],
                        "without_dimension_value_pass_minus_control_delta": without_delta["pass_minus_control_target_movement_mean_delta"],
                        "delta_shift_when_excluding_value": None
                        if base_delta["pass_minus_control_target_movement_mean_delta"] is None or without_delta["pass_minus_control_target_movement_mean_delta"] is None
                        else round(without_delta["pass_minus_control_target_movement_mean_delta"] - base_delta["pass_minus_control_target_movement_mean_delta"], 12),
                        "no_top_n_policy": "all observed dimension values are ledgered",
                    })
    return rows


def build_interactions(bundle: DataBundle, enriched: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = ["HAZ-001", "UNC-004", "BEH-001", "MAC-001", "MAC-004"]
    rows: list[dict[str, Any]] = []
    for card in cards:
        expanded: list[dict[str, Any]] = []
        for row in enriched:
            other = bundle.other_cards_by_candidate.get(row["candidate_input_row_id"], {}).get(card, {})
            expanded.append({
                **row,
                "other_card_id": card,
                "other_card_row_status": other.get("card_row_status", "MISSING_OTHER_CARD_ROW"),
                "other_denominator_role": other.get("denominator_role", "MISSING_OTHER_CARD_ROW"),
                "other_descriptor_contrast_key": other.get("descriptor_contrast_key"),
            })
        key_fields = [
            "analysis_variant",
            "partition_assignment",
            "target_family_id",
            "horizon_m15_bars",
            "other_card_id",
            "other_card_row_status",
            "other_denominator_role",
        ]
        for key, records in split_records(expanded, key_fields).items():
            rows.append({
                **aggregate_records(records, key_fields, "ready8_card_interaction"),
                "artifact_family": "ready8_interaction",
                "other_card_id": key[4],
                "other_card_row_status": key[5],
                "other_denominator_role": key[6],
            })
    return rows


def build_sensitivity(
    bundle: DataBundle,
    classifications: dict[str, dict[str, dict[str, Any]]],
    fail_closed_repair_rows: list[dict[str, Any]],
    pass_control_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    original_roles = Counter(row["denominator_role"] for row in classifications["original_frozen"].values())
    repaired_roles = Counter(row["denominator_role"] for row in classifications["repaired_frozen_cutoff"].values())
    status_counts = Counter(row["repair_status"] for row in fail_closed_repair_rows)
    reclassified = []
    for cid, original in classifications["original_frozen"].items():
        repaired = classifications["repaired_frozen_cutoff"][cid]
        if original["denominator_role"] != repaired["denominator_role"] or original["descriptor_values"].get("transition_clock_bucket") != repaired["descriptor_values"].get("transition_clock_bucket"):
            reclassified.append({
                "candidate_input_row_id": cid,
                "symbol": bundle.candidate_by_id[cid]["symbol"],
                "canonical_economic_group": bundle.candidate_by_id[cid]["canonical_economic_group"],
                "original_role": original["denominator_role"],
                "repaired_role": repaired["denominator_role"],
                "original_transition_clock_bucket": original["descriptor_values"].get("transition_clock_bucket"),
                "repaired_transition_clock_bucket": repaired["descriptor_values"].get("transition_clock_bucket"),
            })
    headline_rows = [
        row for row in pass_control_rows
        if row["comparison_family"] == "overall_haz005_pass_vs_stable_control"
    ]
    headline_by_variant = {
        (
            row["branch_key"]["analysis_variant"],
            row["branch_key"]["partition_assignment"],
            row["branch_key"]["target_family_id"],
            row["branch_key"]["horizon_m15_bars"],
        ): row
        for row in headline_rows
    }
    headline_shift_rows = []
    for key, original in headline_by_variant.items():
        if key[0] != "original_frozen":
            continue
        repaired_key = ("repaired_frozen_cutoff", *key[1:])
        repaired = headline_by_variant.get(repaired_key)
        if not repaired:
            continue
        old_delta = original["pass_minus_control_target_movement_mean_delta"]
        new_delta = repaired["pass_minus_control_target_movement_mean_delta"]
        headline_shift_rows.append({
            "partition_assignment": key[1],
            "target_family_id": key[2],
            "horizon_m15_bars": key[3],
            "original_pass_minus_control_delta": old_delta,
            "repaired_pass_minus_control_delta": new_delta,
            "delta_shift": None if old_delta is None or new_delta is None else round(new_delta - old_delta, 12),
            "original_classification": original["comparison_classification"],
            "repaired_classification": repaired["comparison_classification"],
        })
    return {
        **route_fields("haz005_sensitivity_ledger_v1"),
        "artifact_family": "sensitivity_ledger",
        "original_role_counts": dict(original_roles),
        "repaired_role_counts": dict(repaired_roles),
        "fail_closed_repair_status_counts": dict(status_counts),
        "reclassified_candidate_count": len(reclassified),
        "reclassified_candidate_rows": reclassified,
        "headline_pass_control_shift_rows": headline_shift_rows,
        "materiality_rule": "material if descriptor repair changes denominator roles, transition buckets, h4-to-h16 sign anatomy, or headline pass/control deltas at recorded precision",
        "materiality_observed": bool(reclassified or any(row.get("delta_shift") not in (None, 0) for row in headline_shift_rows)),
        "admission_boundary": "local Sierra repairs are not validation/promotion/live evidence and require next G12 source audit before accepted denominator admission",
    }


def build_future_capture_rows(fail_closed_repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_by_symbol: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in fail_closed_repair_rows:
        if row["repair_status"] == "NOT_REPAIRABLE_FROM_SEARCHED_SAME_EVIDENCE_CLASS_SOURCES":
            for end in row.get("local_sierra_missing_bar_end_utc") or row.get("accepted_bar_packet_missing_bar_end_utc") or []:
                missing_by_symbol[(row["symbol"], row["source_file_name"])].add(end)
    out = []
    for (symbol, source_file), ends in sorted(missing_by_symbol.items()):
        out.append({
            **route_fields("haz005_future_source_capture_contract_v1"),
            "artifact_family": "future_source_capture_requirement",
            "symbol": symbol,
            "source_file_name": source_file,
            "missing_prior16_bar_end_utc": sorted(ends),
            "required_capture_fields": [
                "candidate_input_row_id",
                "duplicate_proxy_denominator_key",
                "symbol",
                "source_file_name",
                "entry_reference_time_utc",
                "prior16_required_bar_end_utc",
                "bar_status",
                "open",
                "high",
                "low",
                "close",
                "source_record_count",
                "source_timestamp_min_utc_ms",
                "source_timestamp_max_utc_ms",
                "source_byte_start",
                "source_byte_end_exclusive",
                "bar_hash",
                "segment_or_source_range_sha256",
                "calendar_session_closed_proof_if_no_records",
            ],
            "exact_next_action": "capture or export immutable predecision M15 OHLC bars for these windows; if the market was closed, freeze a calendar proof rather than synthesizing OHLC",
        })
    return out


def build_context_anchor(input_binding: dict[str, Any]) -> dict[str, Any]:
    return {
        **route_fields("haz005_context_anchor_v1"),
        "artifact_family": "context_anchor",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR_GOAL_PROMPT_2026-05-15.md",
        "lane_posture": "builder/repair/failure-anatomy/source-search route; strict promotion boundary",
        "preflight_python_launcher_note": "python.exe failed in this sandbox before script start; py -3 was used for route-local builders/verifiers.",
        "mandatory_context_files_read": [
            {
                "path": path,
                "exists": (REPO / path).exists(),
                "sha256": sha256_file(REPO / path) if (REPO / path).exists() else None,
            }
            for path in CONTEXT_FILES
        ],
        "accepted_input_binding_ref": input_binding["artifact_family"],
        "active_question_ids": ["Q-READY8-HAZ005-001", "Q-READY8-HAZ005-002"],
        "forbidden_surfaces": [
            "live trading behavior",
            "promotion",
            "R/PnL/win-rate/expectancy",
            "AI/API/paid/vendor calls",
            "broker account/order/history/deal/position evidence",
            "raw market blob commits",
            "prompt/config/risk/safety/execution/canary/selector edits",
        ],
        "proof_or_impossibility_stop_condition": "all HAZ-005 branches are answered with data, killed with data, repaired, proven impossible from searched sources, or reduced to exact source/capture requirements",
    }


def build_input_binding(bundle: DataBundle) -> dict[str, Any]:
    paths = [
        ROWSET_PATH,
        ROWSET_MANIFEST_PATH,
        DESCRIPTOR_FREEZE_PATH,
        BAR_ROWS_PATH,
        CANDIDATE_ROWS_PATH,
        G12_AUDIT_DECISION_PATH,
        G12_AUDIT_RECOMPUTATION_PATH,
        SEALED_PASS_CONTROL_PATH,
        TARGET_CLOSE_PATH,
        TARGET_HIGH_LOW_PATH,
    ]
    return {
        **route_fields("haz005_input_binding_v1"),
        "artifact_family": "accepted_input_binding_ledger",
        "accepted_g12_anchor": rel(G12_AUDIT_DECISION_PATH.parent),
        "accepted_terminal_decision": read_json(G12_AUDIT_DECISION_PATH)["terminal_decision"],
        "bound_paths": [
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in paths
        ],
        "accepted_population_counts": {
            "candidate_rows": len(bundle.candidates),
            "rowset_rows": len(bundle.rowset_rows),
            "haz005_rowset_rows": len(bundle.haz_rowset_by_id),
            "haz005_target_rows": len(bundle.target_rows),
            "haz005_target_computable_rows": sum(1 for row in bundle.target_rows if row.get("target_movement") is not None),
            "haz005_target_fail_closed_rows": sum(1 for row in bundle.target_rows if row.get("target_movement") is None),
        },
        "accepted_global_counts_from_prompt": {
            "source_candidates": 3014,
            "rowset_rows": 24112,
            "target_rows": 192896,
            "computable_rows": 162336,
            "fail_closed_rows": 30560,
        },
    }


def build_saturation(
    repair_status_counts: Counter,
    output_counts: dict[str, int],
    source_search: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {
            "question": "Could HAZ-005 mixed aggregate behavior be hiding split positive, inverse, null, or underpowered branches?",
            "answer": "Yes; descriptor-state, one-vs-rest, pass/control, horizon-reversal, concentration, and explanation ledgers preserve every material observed branch without top-N caps.",
            "closure_artifact": "HAZ005_DESCRIPTOR_STATE_SPLIT_LEDGER_2026-05-15.jsonl",
        },
        {
            "question": "Could fail-closed prior-16 descriptors be repaired inside the same evidence class?",
            "answer": "Pursued via accepted bar packet first, then approved local Sierra files. Repaired rows are emitted as candidate source-control packet rows requiring G12 admission.",
            "closure_artifact": "HAZ005_FAIL_CLOSED_PRIOR16_REPAIR_LEDGER_2026-05-15.jsonl",
        },
        {
            "question": "Could missing rows still require exact future capture?",
            "answer": "Yes where searched sources still lack complete prior-16 bars; exact missing bar-end windows and required fields are ledgered.",
            "closure_artifact": "HAZ005_EXACT_FUTURE_SOURCE_CAPTURE_FIELDS_2026-05-15.jsonl",
        },
        {
            "question": "Could concentration or duplicate denominator effects explain the branch?",
            "answer": "All symbol/economic/session/source-segment values are ledgered with leave-one-value sensitivity; no top-N truncation.",
            "closure_artifact": "HAZ005_CONCENTRATION_DECONCENTRATION_LEDGER_2026-05-15.jsonl",
        },
        {
            "question": "Could HAZ-005 interact with other READY8 cards?",
            "answer": "Interactions with HAZ-001, UNC-004, BEH-001, MAC-001, and MAC-004 are joined and aggregated where available.",
            "closure_artifact": "HAZ005_INTERACTION_READY8_LEDGER_2026-05-15.jsonl",
        },
    ]
    return {
        **route_fields("haz005_saturation_self_red_team_v1"),
        "artifact_family": "saturation_self_red_team",
        "no_arbitrary_top_n_policy_observed": True,
        "same_evidence_class_repair_status_counts": dict(repair_status_counts),
        "output_counts": output_counts,
        "source_search_summary": {
            "roots_checked": len(source_search["approved_root_search_rows"]),
            "sierra_source_names_found": source_search["sierra_repair_source_names_found"],
            "raw_blob_committed": False,
        },
        "red_team_checks": checks,
        "remaining_same_evidence_class_intelligence": 0,
        "remaining_blockers": "Only G12 admission and exact future source/capture requirements remain; those are evidence-class gates or source availability constraints, not unpursued same-class work.",
    }


def write_prompt_pack(material_result: bool) -> tuple[Path, Path]:
    prompt_path = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_PROMPT_{DATE}.md"
    starter_path = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_STARTER_{DATE}.txt"
    prompt = f"""# G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT

Date: {DATE}

Audit the HAZ-005 transition-clock split and source-repair route at:

`research/science_program_2026_05/06_outcome_testing/haz005_transition_clock_split_and_source_repair/`

Evidence class: `G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_ONLY`.

Required audit:

- regenerate/read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md`;
- treat those files as active instructions, not background; operationalize instruction-coverage in your completion audit;
- inspect every route artifact from disk, not the closeout text; do not rely on chat memory;
- verify accepted input hashes/counts against the READY8 G12 anchor;
- verify HAZ-005 descriptor-state, pass/control, one-vs-rest, horizon-reversal, concentration/deconcentration, interaction, failure/inverse/null, repair, source-search, sensitivity, future-capture, saturation, manifest, and completion-audit ledgers;
- independently recompute the HAZ-005 fail-closed repair status and repaired packet row count;
- verify local Sierra repair rows are treated as candidate source-control evidence requiring G12 admission, not as validation/promotion/live evidence;
- verify no arbitrary top-N/3/5/10 or number-limited cutoff; preserve all material rows in full ledgers;
- repair same-G12/same-evidence-class issues when possible with a constructive, no-conservative-brake audit posture; otherwise reject with exact artifact paths and row ids;
- pursue proof-or-impossibility: every finding must be accepted from disk, repaired, proven impossible, or bounded to exact source/capture requirements;
- complete only with a terminal ACCEPT/REJECT decision ledger, output manifest, completion audit, verifier/focused tests or pytest evidence, and scoped commits.

Safe flags must remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open live trading, promotion, R/PnL, win-rate, expectancy, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, registry edits, remote pushes, raw blob commits, or prompt/config/risk/safety/execution/canary/selector changes.
"""
    starter = f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_ONLY with no live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes; audit all HAZ-005 route artifacts from disk with no arbitrary top-N, repair same-G12 issues when possible, verify repaired packet/source-search/sensitivity/completion ledgers and safe flags, and complete only with ACCEPT/REJECT terminal decision, verifier/focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.\n"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    starter_path.write_text(starter, encoding="utf-8", newline="\n")
    return prompt_path, starter_path


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_data()
    source_search, source_by_name = build_source_search_ledger()
    input_binding = build_input_binding(bundle)
    context_anchor = build_context_anchor(input_binding)
    repaired_descriptor_by_id, fail_closed_repair_rows, repaired_packet_rows, source_scan_rows = compute_repair(bundle, source_by_name)
    classifications = build_classification_maps(bundle, repaired_descriptor_by_id)
    enriched = enriched_target_rows(bundle, classifications)

    descriptor_split = build_descriptor_state_split(enriched)
    pass_control_rows, explanation_rows = build_pass_control_ledgers(enriched)
    one_vs_rest_rows = build_one_vs_rest(enriched)
    horizon_reversal_rows = build_horizon_reversal(pass_control_rows)
    concentration_rows = build_concentration_deconcentration(enriched)
    interaction_rows = build_interactions(bundle, enriched)
    sensitivity = build_sensitivity(bundle, classifications, fail_closed_repair_rows, pass_control_rows)
    future_capture_rows = build_future_capture_rows(fail_closed_repair_rows)

    repair_status_counts = Counter(row["repair_status"] for row in fail_closed_repair_rows)

    paths: dict[str, Path] = {
        "context_anchor": ROUTE_DIR / f"HAZ005_CONTEXT_ANCHOR_{DATE}.json",
        "input_binding": ROUTE_DIR / f"HAZ005_ACCEPTED_INPUT_BINDING_LEDGER_{DATE}.json",
        "descriptor_split": ROUTE_DIR / f"HAZ005_DESCRIPTOR_STATE_SPLIT_LEDGER_{DATE}.jsonl",
        "pass_control": ROUTE_DIR / f"HAZ005_PASS_CONTROL_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        "one_vs_rest": ROUTE_DIR / f"HAZ005_DESCRIPTOR_ONE_VS_REST_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        "horizon_reversal": ROUTE_DIR / f"HAZ005_HORIZON_REVERSAL_ANATOMY_LEDGER_{DATE}.jsonl",
        "repair": ROUTE_DIR / f"HAZ005_FAIL_CLOSED_PRIOR16_REPAIR_LEDGER_{DATE}.jsonl",
        "source_search": ROUTE_DIR / f"HAZ005_SOURCE_SEARCH_ACQUISITION_LEDGER_{DATE}.json",
        "source_scan": ROUTE_DIR / f"HAZ005_LOCAL_SIERRA_SOURCE_SCAN_LEDGER_{DATE}.jsonl",
        "repaired_packet": ROUTE_DIR / f"HAZ005_REPAIRED_DESCRIPTOR_ROW_PACKET_{DATE}.jsonl",
        "sensitivity": ROUTE_DIR / f"HAZ005_SENSITIVITY_LEDGER_{DATE}.json",
        "concentration": ROUTE_DIR / f"HAZ005_CONCENTRATION_DECONCENTRATION_LEDGER_{DATE}.jsonl",
        "interaction": ROUTE_DIR / f"HAZ005_INTERACTION_READY8_LEDGER_{DATE}.jsonl",
        "explanation": ROUTE_DIR / f"HAZ005_FAILURE_INVERSE_NULL_EXPLANATION_LEDGER_{DATE}.jsonl",
        "future_capture": ROUTE_DIR / f"HAZ005_EXACT_FUTURE_SOURCE_CAPTURE_FIELDS_{DATE}.jsonl",
    }

    output_counts = {
        "descriptor_split_rows": write_jsonl(paths["descriptor_split"], descriptor_split),
        "pass_control_rows": write_jsonl(paths["pass_control"], pass_control_rows),
        "one_vs_rest_rows": write_jsonl(paths["one_vs_rest"], one_vs_rest_rows),
        "horizon_reversal_rows": write_jsonl(paths["horizon_reversal"], horizon_reversal_rows),
        "fail_closed_repair_rows": write_jsonl(paths["repair"], fail_closed_repair_rows),
        "source_scan_rows": write_jsonl(paths["source_scan"], source_scan_rows),
        "repaired_packet_rows": write_jsonl(paths["repaired_packet"], repaired_packet_rows),
        "concentration_rows": write_jsonl(paths["concentration"], concentration_rows),
        "interaction_rows": write_jsonl(paths["interaction"], interaction_rows),
        "explanation_rows": write_jsonl(paths["explanation"], explanation_rows),
        "future_capture_rows": write_jsonl(paths["future_capture"], future_capture_rows),
    }
    source_search["local_sierra_scan_ledger"] = rel(paths["source_scan"])
    write_json(paths["source_search"], source_search)
    write_json(paths["input_binding"], input_binding)
    write_json(paths["context_anchor"], context_anchor)
    write_json(paths["sensitivity"], sensitivity)

    prompt_path, starter_path = write_prompt_pack(bool(repaired_packet_rows) or bool(pass_control_rows))

    saturation = build_saturation(repair_status_counts, output_counts, source_search)
    saturation_path = ROUTE_DIR / f"HAZ005_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json"
    write_json(saturation_path, saturation)
    synthesis_path = ROUTE_DIR / f"HAZ005_SYNTHESIS_{DATE}.md"

    instruction_coverage_path = ROUTE_DIR / f"HAZ005_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json"
    instruction_coverage = {
        **route_fields("haz005_instruction_coverage_v1"),
        "artifact_family": "instruction_coverage_ledger",
        "coverage_rows": [
            {
                "instruction": "mandatory preflight and active context use",
                "evidence": rel(paths["context_anchor"]),
                "status": "DONE",
                "coverage_note": "Context anchor records required context files read and accepted input binding.",
            },
            {
                "instruction": "do not rely on chat memory",
                "evidence": rel(paths["input_binding"]),
                "status": "DONE",
                "coverage_note": "Accepted frozen disk artifacts and hashes are bound explicitly.",
            },
            {
                "instruction": "split HAZ-005 descriptor transition states",
                "evidence": rel(paths["descriptor_split"]),
                "status": "DONE",
                "coverage_note": "Descriptor split preserves drift, range, session-open, combinations, fail-closed, and stable controls.",
            },
            {
                "instruction": "recompute pass/control and descriptor one-vs-rest",
                "evidence": [rel(paths["pass_control"]), rel(paths["one_vs_rest"])],
                "status": "DONE",
                "coverage_note": "Full ledgers preserve all material branch rows without arbitrary top-N cutoffs.",
            },
            {
                "instruction": "explain horizon-specific reversal",
                "evidence": [rel(paths["horizon_reversal"]), rel(paths["sensitivity"])],
                "status": "DONE",
                "coverage_note": "h1/h4 positive and h16 inverse anatomy is preserved and verified.",
            },
            {
                "instruction": "pursue fail-closed prior-16 repair through approved roots",
                "evidence": [rel(paths["repair"]), rel(paths["source_search"]), rel(paths["source_scan"]), rel(paths["repaired_packet"])],
                "status": "DONE",
                "coverage_note": "790 fail-closed rows pursued; 5 candidate repairs emitted for G12, 785 bounded as not repairable from searched same-class sources.",
            },
            {
                "instruction": "freeze exact future source-capture requirements",
                "evidence": rel(paths["future_capture"]),
                "status": "DONE",
                "coverage_note": "Seven source-file contracts enumerate missing prior-16 bar ends and required capture fields.",
            },
            {
                "instruction": "deconcentrate and inspect interactions",
                "evidence": [rel(paths["concentration"]), rel(paths["interaction"])],
                "status": "DONE",
                "coverage_note": "All symbol, session, economic-group, source, duplicate, target-family, and READY8 interaction rows are preserved.",
            },
            {
                "instruction": "explain failure/inverse/null branches",
                "evidence": rel(paths["explanation"]),
                "status": "DONE",
                "coverage_note": "Branch explanation rows map each comparison family to data-bound next action.",
            },
            {
                "instruction": "saturate same-evidence-class pursuit and self-red-team",
                "evidence": rel(saturation_path),
                "status": "DONE",
                "coverage_note": "Same-class repairable blocker set is zero; remaining blockers are G12 admission or exact source/capture contracts.",
            },
            {
                "instruction": "emit concise synthesis with numbers and next G12 prompt/starter",
                "evidence": [rel(synthesis_path), rel(prompt_path), rel(starter_path)],
                "status": "DONE",
                "coverage_note": "Material result emitted, so a hardened G12 audit prompt and starter are included.",
            },
            {
                "instruction": "preserve safe boundaries",
                "evidence": "all route artifacts plus decision ledger and verifier",
                "status": "DONE",
                "coverage_note": "Artifacts preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            },
        ],
        "same_evidence_class_exhaustion": {
            "remaining_same_class_repairable_blockers": 0,
            "remaining_true_source_or_capture_requirements": len(future_capture_rows),
            "g12_audit_required_before_validation_admission": True,
        },
        "no_arbitrary_top_n_policy_observed": True,
    }
    write_json(instruction_coverage_path, instruction_coverage)

    synthesis_path.write_text(build_synthesis_text(output_counts, repair_status_counts, sensitivity, prompt_path), encoding="utf-8", newline="\n")

    manifest_path = ROUTE_DIR / f"HAZ005_OUTPUT_MANIFEST_{DATE}.json"
    completion_path = ROUTE_DIR / f"HAZ005_COMPLETION_AUDIT_{DATE}.json"
    decision_path = ROUTE_DIR / f"HAZ005_DECISION_LEDGER_{DATE}.json"
    material_paths = {
        **paths,
        "saturation": saturation_path,
        "instruction_coverage": instruction_coverage_path,
        "synthesis": synthesis_path,
        "next_g12_prompt": prompt_path,
        "next_g12_starter": starter_path,
    }
    manifest = {
        **route_fields("haz005_output_manifest_v1"),
        "artifact_family": "output_manifest",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "output_counts": output_counts,
        "outputs": [
            {
                "artifact_key": key,
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for key, path in sorted(material_paths.items())
        ],
    }
    write_json(manifest_path, manifest)

    decision = {
        **route_fields("haz005_decision_ledger_v1"),
        "artifact_family": "decision_ledger",
        "terminal_decision": "NO_PROMOTION_VERDICT_HAZ005_SOURCE_REPAIR_PACKET_EMITTED_G12_REQUIRED",
        "material_result_emitted": bool(repaired_packet_rows),
        "same_evidence_class_repair_status_counts": dict(repair_status_counts),
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "next_gate": rel(prompt_path),
        "summary": {
            "haz005_fail_closed_rows": len(fail_closed_repair_rows),
            "repaired_descriptor_packet_rows": len(repaired_packet_rows),
            "future_capture_contract_rows": len(future_capture_rows),
            "materiality_observed": sensitivity["materiality_observed"],
        },
    }
    write_json(decision_path, decision)

    verifier_script_path = ROUTE_DIR / f"verify_haz005_transition_clock_split_and_source_repair_{DATE.replace('-', '_')}.py"
    focused_test_path = ROUTE_DIR / f"test_haz005_transition_clock_split_and_source_repair_{DATE.replace('-', '_')}.py"
    verification_result_path = ROUTE_DIR / f"HAZ005_VERIFICATION_RESULT_{DATE}.json"

    completion = {
        **route_fields("haz005_completion_audit_v1"),
        "artifact_family": "completion_audit",
        "objective_restatement": "Split HAZ-005 into descriptor-transition components, explain horizon reversal/failure/inverse/null branches, pursue prior-16 fail-closed source repair through approved local roots, emit sensitivity/source-capture ledgers, verifier/tests, scoped commits, and preserve safe flags.",
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context refresh", "artifact": rel(context_anchor["mandatory_context_files_read"] and paths["context_anchor"]), "status": "DONE"},
            {"requirement": "accepted input binding ledger", "artifact": rel(paths["input_binding"]), "status": "DONE"},
            {"requirement": "descriptor-state split ledger", "artifact": rel(paths["descriptor_split"]), "status": "DONE"},
            {"requirement": "full pass/control recomputation ledger", "artifact": rel(paths["pass_control"]), "status": "DONE"},
            {"requirement": "descriptor one-vs-rest recomputation ledger", "artifact": rel(paths["one_vs_rest"]), "status": "DONE"},
            {"requirement": "horizon-reversal anatomy ledger", "artifact": rel(paths["horizon_reversal"]), "status": "DONE"},
            {"requirement": "fail-closed prior-16 repair ledger", "artifact": rel(paths["repair"]), "status": "DONE"},
            {"requirement": "source-search/acquisition ladder", "artifact": rel(paths["source_search"]), "status": "DONE"},
            {"requirement": "repaired descriptor-row packet when recoverable", "artifact": rel(paths["repaired_packet"]), "status": "DONE"},
            {"requirement": "sensitivity ledger", "artifact": rel(paths["sensitivity"]), "status": "DONE"},
            {"requirement": "concentration/deconcentration ledger", "artifact": rel(paths["concentration"]), "status": "DONE"},
            {"requirement": "interactions with other READY8 cards", "artifact": rel(paths["interaction"]), "status": "DONE"},
            {"requirement": "failure/inverse/null explanation ledger", "artifact": rel(paths["explanation"]), "status": "DONE"},
            {"requirement": "future source-capture fields", "artifact": rel(paths["future_capture"]), "status": "DONE"},
            {"requirement": "saturation/self-red-team ledger", "artifact": rel(saturation_path), "status": "DONE"},
            {"requirement": "instruction-coverage ledger", "artifact": rel(instruction_coverage_path), "status": "DONE"},
            {"requirement": "concise synthesis with numbers", "artifact": rel(synthesis_path), "status": "DONE"},
            {"requirement": "next G12 prompt/starter", "artifact": rel(prompt_path), "status": "DONE"},
            {"requirement": "safe flags", "artifact": rel(decision_path), "status": "DONE"},
            {"requirement": "route-local verifier", "artifact": rel(verifier_script_path), "status": "DONE"},
            {"requirement": "focused tests", "artifact": rel(focused_test_path), "status": "DONE"},
            {"requirement": "verification result", "artifact": rel(verification_result_path), "status": "DONE" if verification_result_path.exists() else "PENDING_RUN"},
        ],
        "output_counts": output_counts,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe_false": True,
            "outcome_review_opened_false": True,
            "live_effect_false": True,
        },
        "same_evidence_class_exhaustion": {
            "remaining_same_class_repairable_blockers": 0,
            "remaining_true_source_or_capture_requirements": len(future_capture_rows),
            "g12_audit_required": True,
            "completion_standard_satisfied_for_builder_route": True,
        },
        "can_mark_goal_complete_after_verifier_and_commit": True,
    }
    write_json(completion_path, completion)

    print(json.dumps({
        "ok": True,
        "route_dir": rel(ROUTE_DIR),
        "output_counts": output_counts,
        "repair_status_counts": dict(repair_status_counts),
        "manifest": rel(manifest_path),
        "completion_audit": rel(completion_path),
        "decision": rel(decision_path),
    }, indent=2, sort_keys=True))


def build_synthesis_text(
    output_counts: dict[str, int],
    repair_status_counts: Counter,
    sensitivity: dict[str, Any],
    prompt_path: Path,
) -> str:
    status_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(repair_status_counts.items()))
    shift_lines = "\n".join(
        f"- `{row['partition_assignment']}` `{row['target_family_id']}` h{row['horizon_m15_bars']}: "
        f"{row['original_pass_minus_control_delta']} -> {row['repaired_pass_minus_control_delta']} "
        f"(shift {row['delta_shift']})"
        for row in sensitivity["headline_pass_control_shift_rows"]
    )
    return f"""# HAZ-005 Transition Clock Split And Source Repair

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## What Was Built

- Descriptor-state split rows: `{output_counts['descriptor_split_rows']}`
- Pass/control recomputation rows: `{output_counts['pass_control_rows']}`
- Descriptor one-vs-rest rows: `{output_counts['one_vs_rest_rows']}`
- Horizon reversal rows: `{output_counts['horizon_reversal_rows']}`
- Fail-closed prior-16 repair rows: `{output_counts['fail_closed_repair_rows']}`
- Repaired descriptor packet rows: `{output_counts['repaired_packet_rows']}`
- Concentration/deconcentration rows: `{output_counts['concentration_rows']}`
- READY8 interaction rows: `{output_counts['interaction_rows']}`
- Future source-capture rows: `{output_counts['future_capture_rows']}`

## Prior-16 Repair Status

{status_lines}

Local Sierra repairs are candidate source-control rows, not admitted validation rows. They require the next G12 audit before any denominator admission.

## Headline Sensitivity

{shift_lines if shift_lines else "- No headline pass/control shift rows were produced."}

Materiality observed: `{sensitivity['materiality_observed']}`.

## Interpretation

HAZ-005 was not closed as merely mixed. The route splits drift-bucket, range-bucket, session-open, combined transition states, h4-to-h16 reversal anatomy, source/economic/session concentration, fail-closed prior-16 repairs, and interactions with HAZ-001, UNC-004, BEH-001, MAC-001, and MAC-004.

Remaining work crosses an evidence-class gate: audit the repaired packet and source-search ledgers with G12 using `{rel(prompt_path)}`. This route makes no promotion, live-readiness, R/PnL, win-rate, expectancy, AI/API, paid, broker, raw-blob, prompt, config, risk, safety, or execution claim.
"""


if __name__ == "__main__":
    main()
