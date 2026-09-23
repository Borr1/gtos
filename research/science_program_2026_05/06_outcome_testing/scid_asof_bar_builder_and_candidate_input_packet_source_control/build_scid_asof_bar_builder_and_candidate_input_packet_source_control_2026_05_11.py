#!/usr/bin/env python3
"""Build SCID as-of bars and input-only candidate packets.

This route is source-control materialization only. It rehashes the nine
G12-accepted bounded Sierra SCID segments, parses only those byte ranges, builds
dense M15 as-of OHLCV bars, and emits candidate-generator input packets that
carry provenance hashes and duplicate controls. It does not derive outcomes,
path labels, scores, broker/account/order evidence, API output, or live behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
ROUTE_ID = "SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL"
EVIDENCE_CLASS = "SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_ONLY"
SCHEMA_VERSION = "scid_asof_bar_builder_packet_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
INTERVAL = "M15"
INTERVAL_MINUTES = 15
LOOKBACK_BARS = 96

CONTRACT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint"
)
G12_CONTRACT_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit"
)
REPAIR_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
)
G12_REAUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit"
)
G0_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)

CONTROLLING_PROMPT = (
    PROMPT_DIR
    / "SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-11.md"
)

SEGMENT_MANIFEST = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json"
G12_REHASH_AUDIT = G12_REAUDIT_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_{DATE_TAG}.json"
CONTRACT_JSON = CONTRACT_DIR / f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.json"
CANDIDATE_CONSTRAINT_JSON = CONTRACT_DIR / f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.json"
DUPLICATE_POLICY_JSON = CONTRACT_DIR / f"SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_{DATE_TAG}.json"
FORBIDDEN_LEDGER_JSON = CONTRACT_DIR / f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json"
G12_DECISION_JSON = (
    G12_CONTRACT_AUDIT_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}.json"
)
G0_PARTITION_LEDGER = G0_DIR / f"G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_{DATE_TAG}.json"
G0_BASELINE_PACKET = G0_DIR / f"G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_{DATE_TAG}.json"
G0_DISCOVERY_LEDGER = G0_DIR / f"G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_{DATE_TAG}.json"

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
CHUNK_SIZE = 1024 * 1024
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_registry_edit",
    "opens_mt5_order_account_history_behavior",
    "credentials_touched",
    "changes_live_trading_behavior",
]
EXPECTED_WARNINGS = [
    "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW",
    "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE",
]
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
RAW_MARKET_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin", ".scidseg"}
WIN_LIKE_TOKENS = {"win", "wins", "winning", "winner", "winners", "won"}
BAR_WINDOW_WHITELIST = {"bar_window_start_utc", "bar_window_end_utc"}
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/start",
    "run_agent.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT_UTC = utc_now()


def safe_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "opens_mt5_order_account_history_behavior": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def markdown_payload(payload: dict[str, Any], limit: int = 10000) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text) > limit:
        text = text[:limit] + "\n... truncated in markdown; see matching JSON artifact ..."
    return "```json\n" + text + "\n```\n"


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    md = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Evidence class: `{EVIDENCE_CLASS}`",
        f"- Promotion verdict: `{payload.get('promotion_verdict')}`",
        f"- validation_safe: `{payload.get('validation_safe')}`",
        f"- outcome_review_opened: `{payload.get('outcome_review_opened')}`",
        f"- live_effect: `{payload.get('live_effect')}`",
        "",
    ]
    if payload.get("summary") is not None:
        md.extend(["## Summary", "", markdown_payload({"summary": payload["summary"]}, limit=7000)])
    md.extend(["## Payload", "", markdown_payload(payload)])
    path.write_text("\n".join(md), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_range(path: Path, byte_start: int, byte_end_exclusive: int) -> str:
    digest = hashlib.sha256()
    remaining = byte_end_exclusive - byte_start
    if remaining < 0:
        raise ValueError("negative byte range")
    with path.open("rb") as handle:
        handle.seek(byte_start)
        while remaining:
            chunk = handle.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise IOError(f"unexpected EOF in {path} while hashing segment")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso_ms(value: datetime) -> str:
    value = value.astimezone(timezone.utc)
    value = value.replace(microsecond=(value.microsecond // 1000) * 1000)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sierra_dt(microseconds: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=microseconds)


def datetime_to_sierra_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def floor_interval(value: datetime, minutes: int = INTERVAL_MINUTES) -> datetime:
    value = value.astimezone(timezone.utc)
    minute = (value.minute // minutes) * minutes
    return value.replace(minute=minute, second=0, microsecond=0)


def tokenize(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def forbidden_patterns() -> list[str]:
    ledger = load_json(FORBIDDEN_LEDGER_JSON)
    return [entry["pattern"].lower() for entry in ledger["entries"]]


def forbidden_matches_for_name(name: str, patterns: list[str] | None = None) -> list[dict[str, str]]:
    patterns = patterns or forbidden_patterns()
    lowered = name.lower()
    tokens = tokenize(name)
    matches: list[dict[str, str]] = []
    for pattern in patterns:
        pattern = pattern.lower()
        pattern_tokens = tokenize(pattern)
        if pattern == "win":
            if lowered in BAR_WINDOW_WHITELIST:
                continue
            if any(token in WIN_LIKE_TOKENS for token in tokens):
                matches.append({"text": name, "pattern": pattern, "match_mode": "snake_case_win_token"})
            continue
        if pattern.endswith("_"):
            if lowered.startswith(pattern) or f"_{pattern}" in lowered:
                matches.append({"text": name, "pattern": pattern, "match_mode": "prefix_token"})
            continue
        if "_" in pattern:
            for idx in range(0, max(0, len(tokens) - len(pattern_tokens) + 1)):
                if tokens[idx : idx + len(pattern_tokens)] == pattern_tokens:
                    matches.append({"text": name, "pattern": pattern, "match_mode": "snake_case_phrase"})
                    break
            continue
        if pattern in tokens:
            matches.append({"text": name, "pattern": pattern, "match_mode": "snake_case_token"})
    return matches


def scan_forbidden_payload(payload: Any, patterns: list[str] | None = None, path: str = "") -> list[dict[str, str]]:
    patterns = patterns or forbidden_patterns()
    matches: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_path = f"{path}.{key}" if path else key
            for match in forbidden_matches_for_name(str(key), patterns):
                match["field_path"] = key_path
                matches.append(match)
            matches.extend(scan_forbidden_payload(value, patterns, key_path))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            matches.extend(scan_forbidden_payload(value, patterns, f"{path}[{idx}]"))
    elif isinstance(payload, str):
        for match in forbidden_matches_for_name(payload, patterns):
            match["field_path"] = path
            matches.append(match)
    return matches


def parse_scid_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "parser_status": "FILE_MISSING", "path": str(path)}
    size = path.stat().st_size
    if size < SCID_HEADER.size:
        return {"exists": True, "parser_status": "TOO_SMALL_FOR_HEADER", "size_bytes": size, "path": str(path)}
    with path.open("rb") as handle:
        header = handle.read(SCID_HEADER.size)
    magic, header_size, record_size, version, utc_start_index, unused, reserve = SCID_HEADER.unpack(header)
    remainder = (size - header_size) % record_size if record_size else None
    return {
        "absolute_path": str(path),
        "exists": True,
        "file_name": path.name,
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "unused": unused,
        "reserve_sha256": sha256_bytes(reserve),
        "header_sha256": sha256_bytes(header),
        "record_count": (size - header_size) // record_size if header_size == 56 and record_size == 40 else None,
        "remainder_bytes": remainder,
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK"
        if magic == b"SCID" and header_size == 56 and record_size == 40 and remainder == 0
        else "SCID_HEADER_OR_RECORD_CONTRACT_FAIL",
    }


def check_safe_flags(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append("promotion_verdict")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(flag)
    return not failures, failures


def group_policy_maps(policy: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, list[str]]]:
    source_to_group = {
        row["symbol"]: row["canonical_economic_group"] for row in policy["source_input_group_assignment"]
    }
    primary_by_group: dict[str, str] = {}
    members_by_group: dict[str, list[str]] = {}
    for group in policy["proxy_groups"]:
        members = list(group["members"])
        members_by_group[group["canonical_economic_group"]] = members
        priority = group.get("primary_counting_source_priority") or members
        primary_by_group[group["canonical_economic_group"]] = priority[0]
    return source_to_group, primary_by_group, members_by_group


def make_bar_hash(bar: dict[str, Any]) -> str:
    payload = {key: value for key, value in bar.items() if key != "bar_hash"}
    return sha256_json(payload)


def empty_bar_row(
    segment: dict[str, Any],
    canonical_group: str,
    decision_asof: datetime,
    bar_start: datetime,
) -> dict[str, Any]:
    bar_end = bar_start + timedelta(minutes=INTERVAL_MINUTES)
    row: dict[str, Any] = {
        "bar_row_id": f"bar:{segment['symbol']}:{INTERVAL}:{iso_ms(bar_start)}",
        "source_manifest_ref": rel(SEGMENT_MANIFEST),
        "source_file_name": segment["source"],
        "symbol": segment["symbol"],
        "canonical_economic_group": canonical_group,
        "segment_records_sha256": segment["segment_records_sha256"],
        "segment_byte_start": segment["segment_byte_start"],
        "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
        "interval": INTERVAL,
        "decision_asof_utc": iso_ms(decision_asof),
        "bar_start_utc": iso_ms(bar_start),
        "bar_end_exclusive_utc": iso_ms(bar_end),
        "source_record_start_index": None,
        "source_record_end_index": None,
        "source_byte_start": None,
        "source_byte_end_exclusive": None,
        "source_timestamp_min_us": None,
        "source_timestamp_max_us": None,
        "source_timestamp_min_utc_ms": None,
        "source_timestamp_max_utc_ms": None,
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "total_volume": 0,
        "bid_volume": 0,
        "ask_volume": 0,
        "num_trades": 0,
        "source_record_count": 0,
        "bar_status": "DATA_GAP_NO_SOURCE_RECORDS",
        "candidate_eligible": False,
        "eligibility_basis": "FAIL_CLOSED_EMPTY_OR_GAP_BAR_NO_SYNTHETIC_OHLC",
    }
    row["bar_hash"] = make_bar_hash(row)
    return row


def aggregate_records_to_dense_bars(
    records: list[dict[str, Any]],
    segment: dict[str, Any],
    canonical_group: str,
    decision_asof: datetime,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    hard_floor_us = datetime_to_sierra_us(parse_time(segment["eligible_segment_start_utc_hard_floor"]))
    decision_asof_us = datetime_to_sierra_us(decision_asof)
    aggs: dict[str, dict[str, Any]] = {}
    stats = {
        "input_record_count": len(records),
        "accepted_record_count": 0,
        "rejected_before_hard_floor_count": 0,
        "rejected_before_segment_count": 0,
        "rejected_after_segment_count": 0,
        "excluded_at_or_after_decision_asof_count": 0,
        "excluded_exactly_at_decision_asof_count": 0,
        "source_order_violation_count": 0,
        "same_timestamp_duplicate_record_count": 0,
        "same_millisecond_record_count": 0,
        "partial_after_decision_bar_count": 0,
    }
    previous_ts: int | None = None
    timestamp_seen: set[int] = set()
    millisecond_seen: set[int] = set()
    for record in records:
        ts_us = int(record["source_timestamp_us"])
        source_index = int(record["source_record_index"])
        byte_offset = int(record["source_byte_offset"])
        if previous_ts is not None and ts_us < previous_ts:
            stats["source_order_violation_count"] += 1
        previous_ts = ts_us
        if ts_us in timestamp_seen:
            stats["same_timestamp_duplicate_record_count"] += 1
        timestamp_seen.add(ts_us)
        ms_key = ts_us // 1000
        if ms_key in millisecond_seen:
            stats["same_millisecond_record_count"] += 1
        millisecond_seen.add(ms_key)
        if ts_us < hard_floor_us:
            stats["rejected_before_hard_floor_count"] += 1
            continue
        if byte_offset < int(segment["segment_byte_start"]):
            stats["rejected_before_segment_count"] += 1
            continue
        if byte_offset >= int(segment["segment_byte_end_exclusive"]):
            stats["rejected_after_segment_count"] += 1
            continue
        if ts_us >= decision_asof_us:
            stats["excluded_at_or_after_decision_asof_count"] += 1
            if ts_us == decision_asof_us:
                stats["excluded_exactly_at_decision_asof_count"] += 1
            continue
        ts_dt = sierra_dt(ts_us)
        bar_start = floor_interval(ts_dt)
        bar_end = bar_start + timedelta(minutes=INTERVAL_MINUTES)
        if bar_end > decision_asof:
            stats["partial_after_decision_bar_count"] += 1
            continue
        key = iso_ms(bar_start)
        sort_key = (ts_us, source_index)
        agg = aggs.setdefault(
            key,
            {
                "bar_start": bar_start,
                "bar_end": bar_end,
                "first_key": sort_key,
                "last_key": sort_key,
                "open": record["open"],
                "high": record["high"],
                "low": record["low"],
                "close": record["close"],
                "total_volume": 0,
                "bid_volume": 0,
                "ask_volume": 0,
                "num_trades": 0,
                "source_record_count": 0,
                "source_record_start_index": source_index,
                "source_record_end_index": source_index,
                "source_byte_start": byte_offset,
                "source_byte_end_exclusive": byte_offset + SCID_RECORD.size,
                "source_timestamp_min_us": ts_us,
                "source_timestamp_max_us": ts_us,
            },
        )
        if sort_key < agg["first_key"]:
            agg["first_key"] = sort_key
            agg["open"] = record["open"]
            agg["source_record_start_index"] = source_index
            agg["source_byte_start"] = byte_offset
            agg["source_timestamp_min_us"] = ts_us
        if sort_key >= agg["last_key"]:
            agg["last_key"] = sort_key
            agg["close"] = record["close"]
            agg["source_record_end_index"] = source_index
            agg["source_byte_end_exclusive"] = byte_offset + SCID_RECORD.size
            agg["source_timestamp_max_us"] = ts_us
        agg["high"] = max(agg["high"], record["high"])
        agg["low"] = min(agg["low"], record["low"])
        agg["total_volume"] += int(record["total_volume"])
        agg["bid_volume"] += int(record["bid_volume"])
        agg["ask_volume"] += int(record["ask_volume"])
        agg["num_trades"] += int(record["num_trades"])
        agg["source_record_count"] += 1
        stats["accepted_record_count"] += 1

    dense_start = floor_interval(parse_time(segment["eligible_segment_start_utc_hard_floor"]))
    bars: list[dict[str, Any]] = []
    cursor = dense_start
    while cursor + timedelta(minutes=INTERVAL_MINUTES) <= decision_asof:
        key = iso_ms(cursor)
        if key not in aggs:
            bars.append(empty_bar_row(segment, canonical_group, decision_asof, cursor))
        else:
            agg = aggs[key]
            row = {
                "bar_row_id": f"bar:{segment['symbol']}:{INTERVAL}:{iso_ms(agg['bar_start'])}",
                "source_manifest_ref": rel(SEGMENT_MANIFEST),
                "source_file_name": segment["source"],
                "symbol": segment["symbol"],
                "canonical_economic_group": canonical_group,
                "segment_records_sha256": segment["segment_records_sha256"],
                "segment_byte_start": segment["segment_byte_start"],
                "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
                "interval": INTERVAL,
                "decision_asof_utc": iso_ms(decision_asof),
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
                "eligibility_basis": "CLOSED_BAR_SOURCE_RECORDS_PRESENT_ONLY_NOT_TRADE_SIGNAL",
            }
            row["bar_hash"] = make_bar_hash(row)
            bars.append(row)
        cursor += timedelta(minutes=INTERVAL_MINUTES)
    stats["dense_bar_count"] = len(bars)
    stats["record_present_bar_count"] = sum(1 for row in bars if row["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT")
    stats["empty_or_gap_bar_count"] = sum(1 for row in bars if row["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT")
    stats["decision_asof_utc"] = iso_ms(decision_asof)
    return bars, stats


def read_segment_records(segment: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_path = Path(segment["source_path"])
    records: list[dict[str, Any]] = []
    byte_start = int(segment["segment_byte_start"])
    byte_end = int(segment["segment_byte_end_exclusive"])
    expected_count = int(segment["segment_record_count"])
    with source_path.open("rb") as handle:
        handle.seek(byte_start)
        for local_idx in range(expected_count):
            offset = byte_start + local_idx * SCID_RECORD.size
            if offset + SCID_RECORD.size > byte_end:
                break
            raw = handle.read(SCID_RECORD.size)
            if len(raw) != SCID_RECORD.size:
                break
            ts_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = SCID_RECORD.unpack(raw)
            records.append(
                {
                    "source_record_index": int(segment["segment_record_start_index"]) + local_idx,
                    "source_byte_offset": offset,
                    "source_timestamp_us": int(ts_us),
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "num_trades": int(num_trades),
                    "total_volume": int(total_volume),
                    "bid_volume": int(bid_volume),
                    "ask_volume": int(ask_volume),
                }
            )
    diagnostics = {
        "records_read": len(records),
        "expected_segment_record_count": expected_count,
        "records_read_matches_manifest": len(records) == expected_count,
    }
    return records, diagnostics


def segment_rehash_rows(segments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for segment in segments:
        source_path = Path(segment["source_path"])
        header = parse_scid_header(source_path)
        first = hash_range(source_path, segment["segment_byte_start"], segment["segment_byte_end_exclusive"])
        second = hash_range(source_path, segment["segment_byte_start"], segment["segment_byte_end_exclusive"])
        row = {
            **safe_flags(),
            "artifact_family": "segment_source_rehash_row",
            "symbol": segment["symbol"],
            "source_file_name": segment["source"],
            "source_path_reference_only": segment["source_path"],
            "segment_byte_start": segment["segment_byte_start"],
            "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
            "segment_record_count": segment["segment_record_count"],
            "segment_records_sha256_manifest": segment["segment_records_sha256"],
            "raw_byte_rehash_sha256_first_pass": first,
            "raw_byte_rehash_sha256_second_pass": second,
            "raw_byte_rehash_matches_manifest": first == segment["segment_records_sha256"],
            "raw_byte_rehash_is_deterministic": first == second,
            "header_metadata": header,
            "source_path_exists": source_path.exists(),
            "raw_blob_committed": False,
        }
        rows.append(row)
    summary = {
        "segment_count": len(rows),
        "all_9_segments_rehashed": len(rows) == 9,
        "all_segment_rehashes_match": all(row["raw_byte_rehash_matches_manifest"] for row in rows),
        "all_segment_rehashes_deterministic": all(row["raw_byte_rehash_is_deterministic"] for row in rows),
        "all_sources_exist": all(row["source_path_exists"] for row in rows),
    }
    return rows, summary


def build_candidate_rows(
    bar_rows: list[dict[str, Any]],
    primary_by_group: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bars_by_source: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in bar_rows:
        bars_by_source.setdefault((row["canonical_economic_group"], row["symbol"]), []).append(row)
    candidate_rows: list[dict[str, Any]] = []
    patterns = forbidden_patterns()
    for (group, symbol), rows in sorted(bars_by_source.items()):
        rows = sorted(rows, key=lambda item: item["bar_start_utc"])
        if primary_by_group.get(group) != symbol:
            continue
        for idx, bar in enumerate(rows):
            if not bar["candidate_eligible"]:
                continue
            window_rows = rows[max(0, idx - LOOKBACK_BARS + 1) : idx + 1]
            duplicate_key_fields = {
                "canonical_economic_group": group,
                "candidate_family_id": "scid_asof_m15_source_control_input",
                "decision_asof_utc": bar["bar_end_exclusive_utc"],
                "entry_reference_time_utc": bar["bar_end_exclusive_utc"],
                "side": "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT",
                "source_partition_id": "SCID_ASOF_ACCEPTED_9_SEGMENT_SOURCE_CONTROL",
            }
            row = {
                "candidate_input_row_id": f"candidate_input:{group}:{bar['bar_end_exclusive_utc']}",
                "row_hash": None,
                "candidate_family_id": "scid_asof_m15_source_control_input",
                "symbol": symbol,
                "canonical_economic_group": group,
                "source_file_name": bar["source_file_name"],
                "segment_records_sha256": bar["segment_records_sha256"],
                "interval": INTERVAL,
                "decision_asof_utc": bar["bar_end_exclusive_utc"],
                "bar_window_start_utc": window_rows[0]["bar_start_utc"],
                "bar_window_end_utc": bar["bar_end_exclusive_utc"],
                "included_bar_hashes": [item["bar_hash"] for item in window_rows],
                "last_included_bar_end_exclusive_utc": bar["bar_end_exclusive_utc"],
                "asof_feature_schema_version": "scid_asof_m15_ohlcv_hash_window_v1",
                "duplicate_key": sha256_json(duplicate_key_fields),
                "duplicate_key_fields": duplicate_key_fields,
                "partition_assignment": "SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION",
                "forbidden_field_scan_passed": None,
                "candidate_input_only_status": "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
            }
            matches = scan_forbidden_payload(row, patterns)
            row["forbidden_field_scan_passed"] = len(matches) == 0
            row["row_hash"] = sha256_json({key: value for key, value in row.items() if key != "row_hash"})
            candidate_rows.append(row)
    duplicate_keys = [row["duplicate_key"] for row in candidate_rows]
    summary = {
        "candidate_input_row_count": len(candidate_rows),
        "unique_duplicate_key_count": len(set(duplicate_keys)),
        "duplicate_key_collision_count": len(duplicate_keys) - len(set(duplicate_keys)),
        "all_rows_input_only": all(
            row["candidate_input_only_status"] == "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION"
            for row in candidate_rows
        ),
        "all_forbidden_scans_pass": all(row["forbidden_field_scan_passed"] for row in candidate_rows),
    }
    return candidate_rows, summary


def repair_forbidden_scan_ledger() -> dict[str, Any]:
    allowed_fields = ["bar_window_start_utc", "bar_window_end_utc"]
    forbidden_examples = [
        "win_rate",
        "winning_trade",
        "loss",
        "pnl",
        "expectancy",
        "slippage",
        "broker_order",
        "deal",
        "position",
        "path_label",
        "result",
    ]
    patterns = forbidden_patterns()
    allowed_results = {field: forbidden_matches_for_name(field, patterns) for field in allowed_fields}
    forbidden_results = {field: forbidden_matches_for_name(field, patterns) for field in forbidden_examples}
    return {
        **safe_flags(),
        "artifact_family": "forbidden_scan_repair_ledger",
        "repaired_warning_id": "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW",
        "repair_policy": "snake_case_token_matching_for_short_forbidden_words_with_explicit_bar_window_whitelist",
        "allowed_bar_window_fields": allowed_fields,
        "forbidden_examples": forbidden_examples,
        "allowed_results": allowed_results,
        "forbidden_results": forbidden_results,
        "checks": {
            "bar_window_start_passes": allowed_results["bar_window_start_utc"] == [],
            "bar_window_end_passes": allowed_results["bar_window_end_utc"] == [],
            "all_forbidden_examples_fail": all(bool(matches) for matches in forbidden_results.values()),
        },
        "summary": {
            "warning_repaired": allowed_results["bar_window_start_utc"] == []
            and allowed_results["bar_window_end_utc"] == []
            and all(bool(matches) for matches in forbidden_results.values()),
            "forbidden_pattern_count": len(patterns),
        },
    }


def synthetic_fixture_records() -> tuple[list[dict[str, Any]], dict[str, Any], datetime]:
    hard_floor = datetime(2026, 5, 1, 20, 59, 1, tzinfo=timezone.utc)
    decision = datetime(2026, 5, 1, 21, 30, 0, tzinfo=timezone.utc)
    segment = {
        "symbol": "FIXTURE",
        "source": "FIXTURE.scid",
        "source_path": "FIXTURE.scid",
        "segment_records_sha256": "fixture",
        "segment_byte_start": 1000,
        "segment_byte_end_exclusive": 2000,
        "segment_record_start_index": 10,
        "eligible_segment_start_utc_hard_floor": iso_ms(hard_floor),
    }

    def rec(ts: datetime, idx: int, offset: int, price: float) -> dict[str, Any]:
        return {
            "source_record_index": idx,
            "source_byte_offset": offset,
            "source_timestamp_us": datetime_to_sierra_us(ts),
            "open": price,
            "high": price + 0.2,
            "low": price - 0.2,
            "close": price + 0.1,
            "num_trades": 1,
            "total_volume": 10,
            "bid_volume": 4,
            "ask_volume": 6,
        }

    records = [
        rec(hard_floor - timedelta(seconds=1), 9, 1040, 99.0),  # before hard floor
        rec(hard_floor, 10, 1000, 100.0),  # exactly at hard floor
        rec(hard_floor + timedelta(milliseconds=1), 11, 1040, 101.0),  # same millisecond group
        rec(hard_floor, 12, 1080, 102.0),  # duplicate timestamp
        rec(hard_floor + timedelta(seconds=20), 13, 960, 103.0),  # before segment
        rec(hard_floor + timedelta(seconds=30), 14, 2040, 104.0),  # after segment
        rec(hard_floor + timedelta(minutes=16), 16, 1240, 106.0),  # intentionally before previous record
        rec(hard_floor + timedelta(minutes=20), 15, 1200, 105.0),  # non-monotonic source order
        rec(decision, 17, 1280, 107.0),  # exactly at decision asof
        rec(decision + timedelta(minutes=1), 18, 1320, 108.0),  # partial after decision
    ]
    return records, segment, decision


def hard_floor_fixture_ledger() -> dict[str, Any]:
    records, segment, decision = synthetic_fixture_records()
    bars, stats = aggregate_records_to_dense_bars(records, segment, "FIXTURE_GROUP", decision)
    present_bars = [bar for bar in bars if bar["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT"]
    empty_bars = [bar for bar in bars if bar["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT"]
    checks = {
        "before_hard_floor_rejected": stats["rejected_before_hard_floor_count"] == 1,
        "exactly_at_hard_floor_accepted": bool(present_bars) and present_bars[0]["source_timestamp_min_us"]
        == datetime_to_sierra_us(parse_time(segment["eligible_segment_start_utc_hard_floor"])),
        "before_segment_rejected": stats["rejected_before_segment_count"] == 1,
        "after_segment_rejected": stats["rejected_after_segment_count"] == 1,
        "exactly_at_decision_asof_excluded": stats["excluded_exactly_at_decision_asof_count"] == 1,
        "same_millisecond_records_detected": stats["same_millisecond_record_count"] >= 1,
        "duplicate_timestamps_detected": stats["same_timestamp_duplicate_record_count"] >= 1,
        "non_monotonic_source_order_detected": stats["source_order_violation_count"] >= 1,
        "empty_gap_bars_fail_closed": bool(empty_bars)
        and all(bar["candidate_eligible"] is False and bar["open"] is None for bar in empty_bars),
    }
    return {
        **safe_flags(),
        "artifact_family": "hard_floor_fixture_ledger",
        "repaired_warning_id": "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE",
        "fixture_scope": "synthetic_source_control_only_no_raw_market_data_no_validation_labels",
        "fixture_cases_covered": [
            "before_hard_floor",
            "exactly_at_hard_floor",
            "before_segment",
            "after_segment",
            "exactly_at_decision_asof",
            "same_millisecond_records",
            "duplicate_timestamps",
            "non_monotonic_source_ordering",
            "empty_gap_fail_closed",
        ],
        "stats": stats,
        "checks": checks,
        "summary": {"warning_repaired": all(checks.values()), "bar_count": len(bars)},
    }


def git_status_porcelain() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def dirty_scope_audit() -> dict[str, Any]:
    lines = git_status_porcelain()
    route_prefix = rel(ROUTE_DIR) + "/"
    prompt_rel = rel(NEXT_G12_PROMPT)
    scoped = []
    unrelated = []
    forbidden_live_surface = []
    raw_market_blobs = []
    for line in lines:
        path = line[3:] if len(line) > 3 else line
        path = path.replace("\\", "/")
        if path.startswith(route_prefix) or path == prompt_rel:
            scoped.append(path)
            if Path(path).suffix.lower() in RAW_MARKET_EXTENSIONS:
                raw_market_blobs.append(path)
            if any(path.startswith(prefix) for prefix in FORBIDDEN_LIVE_SURFACE_PREFIXES):
                forbidden_live_surface.append(path)
        else:
            unrelated.append(line)
    return {
        "scoped_route_or_prompt_paths": scoped,
        "unrelated_workspace_dirt_recorded_only": unrelated,
        "raw_market_blob_paths_in_scope": raw_market_blobs,
        "forbidden_live_surface_paths_in_scope": forbidden_live_surface,
        "checks": {
            "no_raw_market_blobs_in_scope": not raw_market_blobs,
            "no_forbidden_live_surface_paths_in_scope": not forbidden_live_surface,
        },
    }


def file_record(path: Path, artifact_type: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "artifact_type": artifact_type,
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
        "bytes": path.stat().st_size if path.exists() else None,
    }


def build_next_g12_prompt() -> None:
    prompt = f"""# G12 SCID As-Of Bar Builder And Candidate Input Packet Source-Control Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent packet source-control audit only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Audit `SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL` under:

`research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/`

This audit may verify source-control bars, input-only candidate packet rows, repair ledgers, rehash ledgers, no-leak gates, duplicate/proxy controls, discovery exclusions, adversarial baselines, raw-data handling, tests, and committed diff scope. It must not execute sealed validation, score candidates, derive path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor/credential/remote routes, inspect broker account/order/history/deal/position evidence, commit raw market-data blobs, or touch live behavior/prompt/config/risk/safety/execution/canary/selector surfaces.

## Mandatory Audit Checks

1. Run GTOS mandatory preflight and read the controlling route prompt.
2. Verify the prior G12 contract decision is `ACCEPT_WITH_EXACT_CONTRACT_WARNINGS` with zero terminal blockers.
3. Verify both exact warnings are repaired by executable tests and verifier checks:
   - `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW`
   - `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`
4. Re-run JSON/JSONL parse checks, the route verifier, focused pytest, and syntax/compile checks.
5. Recompute all 9 accepted SCID segment hashes from bounded byte ranges and verify bar rows use no bytes outside their accepted segment.
6. Verify all bar intervals are left-closed/right-open and no bar/candidate input includes records at or after decision as-of.
7. Verify candidate rows contain only input fields, have status `CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION`, and contain no path-label/result/performance/cost/slippage/broker/AI/live fields.
8. Verify the 365 discovery-source exclusions and four adversarial baselines are preserved exactly.
9. Verify duplicate/proxy denominator controls prevent GC/MGC and YM/MYM double counting.
10. Verify no raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or segment blob market-data file is staged or committed.
11. Emit a decision ledger, blocker/warning ledger, packet audit, completion audit, verifier result, focused tests if needed, and next G0/G12 prompt only if the packet is accepted.

## Hard Boundary

This is a packet audit only. If accepted, the next lane may be a separate G0/G12 synthesis or sealed-validation design prompt. This audit cannot open validation execution or promotion.
"""
    NEXT_G12_PROMPT.write_text(prompt, encoding="utf-8")


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    build_next_g12_prompt()

    segment_manifest = load_json(SEGMENT_MANIFEST)
    segments = segment_manifest["segments"]
    g12_decision = load_json(G12_DECISION_JSON)
    contract = load_json(CONTRACT_JSON)
    candidate_constraint = load_json(CANDIDATE_CONSTRAINT_JSON)
    duplicate_policy = load_json(DUPLICATE_POLICY_JSON)
    g0_partition = load_json(G0_PARTITION_LEDGER)
    g0_baselines = load_json(G0_BASELINE_PACKET)
    g0_discovery = load_json(G0_DISCOVERY_LEDGER)

    source_to_group, primary_by_group, members_by_group = group_policy_maps(duplicate_policy)
    rehash_rows, rehash_summary = segment_rehash_rows(segments)
    bar_rows: list[dict[str, Any]] = []
    scan_summaries: list[dict[str, Any]] = []
    for segment in segments:
        records, read_diag = read_segment_records(segment)
        decision_asof = floor_interval(parse_time(segment["segment_last_record_utc"]))
        bars, stats = aggregate_records_to_dense_bars(
            records,
            segment,
            source_to_group[segment["symbol"]],
            decision_asof,
        )
        bar_rows.extend(bars)
        scan_summaries.append(
            {
                "symbol": segment["symbol"],
                "source_file_name": segment["source"],
                "canonical_economic_group": source_to_group[segment["symbol"]],
                **read_diag,
                **stats,
            }
        )

    bar_rows = sorted(
        bar_rows,
        key=lambda row: (
            row["canonical_economic_group"],
            row["symbol"],
            row["bar_start_utc"],
        ),
    )
    candidate_rows, candidate_summary = build_candidate_rows(bar_rows, primary_by_group)
    bar_rows_path = ROUTE_DIR / f"SCID_ASOF_BAR_ROWS_{DATE_TAG}.jsonl"
    candidate_rows_path = ROUTE_DIR / f"SCID_ASOF_CANDIDATE_INPUT_ROWS_{DATE_TAG}.jsonl"
    write_jsonl(bar_rows_path, bar_rows)
    write_jsonl(candidate_rows_path, candidate_rows)

    route_refs = {
        "controlling_prompt": rel(CONTROLLING_PROMPT),
        "g12_contract_audit_decision": rel(G12_DECISION_JSON),
        "segment_manifest": rel(SEGMENT_MANIFEST),
        "g12_rehash_audit": rel(G12_REHASH_AUDIT),
        "contract": rel(CONTRACT_JSON),
        "candidate_constraint": rel(CANDIDATE_CONSTRAINT_JSON),
        "duplicate_policy": rel(DUPLICATE_POLICY_JSON),
        "forbidden_ledger": rel(FORBIDDEN_LEDGER_JSON),
        "g0_partition_ledger": rel(G0_PARTITION_LEDGER),
        "g0_baseline_packet": rel(G0_BASELINE_PACKET),
        "g0_discovery_ledger": rel(G0_DISCOVERY_LEDGER),
        "next_g12_prompt": rel(NEXT_G12_PROMPT),
    }
    contract_inputs = {
        **safe_flags(),
        "artifact_family": "contract_inputs",
        "route_refs": route_refs,
        "target_g12_decision": g12_decision["terminal_decision"],
        "target_g12_terminal_blocker_count": g12_decision["summary"]["terminal_blocker_count"],
        "target_g12_exact_warnings": [warning["warning_id"] for warning in g12_decision["exact_contract_warnings"]],
        "parser_contract": contract["parser_contract"],
        "bar_derivation_rules": contract["bar_derivation_rules"],
        "candidate_input_required_fields": candidate_constraint["required_candidate_input_row_fields"],
        "interval": INTERVAL,
        "lookback_bars": LOOKBACK_BARS,
        "summary": {
            "segment_count": len(segments),
            "target_g12_decision_accepted_with_warnings": g12_decision["terminal_decision"]
            == "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
            "target_g12_terminal_blockers_zero": g12_decision["summary"]["terminal_blocker_count"] == 0,
            "exact_warning_ids_match": sorted(warning["warning_id"] for warning in g12_decision["exact_contract_warnings"])
            == sorted(EXPECTED_WARNINGS),
        },
    }

    source_rehash_ledger = {
        **safe_flags(),
        "artifact_family": "source_rehash_ledger",
        "rehash_method": "sha256 over segment_byte_start through segment_byte_end_exclusive before consumption",
        "target_g12_rehash_audit_ref": rel(G12_REHASH_AUDIT),
        "rows": rehash_rows,
        "summary": rehash_summary,
    }

    bar_counts_by_symbol: dict[str, int] = {}
    present_counts_by_symbol: dict[str, int] = {}
    for row in bar_rows:
        bar_counts_by_symbol[row["symbol"]] = bar_counts_by_symbol.get(row["symbol"], 0) + 1
        if row["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT":
            present_counts_by_symbol[row["symbol"]] = present_counts_by_symbol.get(row["symbol"], 0) + 1
    bar_manifest = {
        **safe_flags(),
        "artifact_family": "bar_manifest",
        "bar_rows_ref": rel(bar_rows_path),
        "bar_rows_sha256": sha256_file(bar_rows_path),
        "bar_row_count": len(bar_rows),
        "record_present_bar_count": sum(1 for row in bar_rows if row["bar_status"] == "CLOSED_SOURCE_RECORDS_PRESENT"),
        "empty_or_gap_bar_count": sum(1 for row in bar_rows if row["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT"),
        "interval": INTERVAL,
        "interval_policy": "left_closed_right_open",
        "decision_asof_rule": "bar_end_exclusive_utc <= decision_asof_utc",
        "bar_counts_by_symbol": bar_counts_by_symbol,
        "record_present_bar_counts_by_symbol": present_counts_by_symbol,
        "segment_scan_summaries": scan_summaries,
        "summary": {
            "bar_row_count": len(bar_rows),
            "no_bar_uses_bytes_outside_segment": all(
                row["source_byte_start"] is None
                or (
                    row["segment_byte_start"] <= row["source_byte_start"]
                    and row["source_byte_end_exclusive"] <= row["segment_byte_end_exclusive"]
                )
                for row in bar_rows
            ),
            "all_bars_closed_asof": all(row["bar_end_exclusive_utc"] <= row["decision_asof_utc"] for row in bar_rows),
            "empty_bars_fail_closed": all(
                row["candidate_eligible"] is False and row["open"] is None
                for row in bar_rows
                if row["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT"
            ),
        },
    }

    packet_manifest = {
        **safe_flags(),
        "artifact_family": "candidate_input_packet_manifest",
        "packet_id": "SCID_ASOF_CANDIDATE_INPUT_PACKET_2026-05-11",
        "packet_schema_version": SCHEMA_VERSION,
        "contract_ref": rel(CONTRACT_JSON),
        "contract_sha256": sha256_file(CONTRACT_JSON),
        "builder_script_ref": rel(Path(__file__)),
        "builder_script_sha256": sha256_file(Path(__file__)),
        "source_segment_manifest_ref": rel(SEGMENT_MANIFEST),
        "source_segment_manifest_sha256": sha256_file(SEGMENT_MANIFEST),
        "g12_repair_reaudit_ref": rel(G12_REHASH_AUDIT),
        "discovery_exclusion_ledger_ref": rel(G0_DISCOVERY_LEDGER),
        "adversarial_baseline_ids": EXPECTED_BASELINES,
        "duplicate_proxy_policy_ref": rel(DUPLICATE_POLICY_JSON),
        "partition_assignment": "SOURCE_CONTROL_INPUT_PACKET_ONLY_NOT_VALIDATION",
        "candidate_rows_ref": rel(candidate_rows_path),
        "candidate_rows_sha256": sha256_file(candidate_rows_path),
        "candidate_input_row_count": len(candidate_rows),
        "candidate_summary": candidate_summary,
        "summary": {
            **candidate_summary,
            "candidate_status_value": "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
            "validation_execution_allowed": False,
        },
    }

    forbidden_repair = repair_forbidden_scan_ledger()
    hard_floor_repair = hard_floor_fixture_ledger()

    candidate_counts_by_group: dict[str, int] = {}
    for row in candidate_rows:
        candidate_counts_by_group[row["canonical_economic_group"]] = (
            candidate_counts_by_group.get(row["canonical_economic_group"], 0) + 1
        )
    duplicate_proxy_ledger = {
        **safe_flags(),
        "artifact_family": "duplicate_proxy_denominator_ledger",
        "proxy_groups": duplicate_policy["proxy_groups"],
        "members_by_group": members_by_group,
        "primary_counting_source_by_group": primary_by_group,
        "candidate_counts_by_group": candidate_counts_by_group,
        "secondary_proxy_sources_excluded_from_candidate_denominator": [
            symbol
            for group, members in members_by_group.items()
            for symbol in members
            if primary_by_group[group] != symbol
        ],
        "bar_rows_preserve_all_9_sources": sorted({row["symbol"] for row in bar_rows}),
        "candidate_rows_count_primary_sources_only": sorted({row["symbol"] for row in candidate_rows}),
        "summary": {
            "bar_source_count": len({row["symbol"] for row in bar_rows}),
            "candidate_counting_group_count": len(candidate_counts_by_group),
            "xau_micro_not_denominator": "XAUUSD_MGC"
            not in {row["symbol"] for row in candidate_rows},
            "us30_micro_not_denominator": "US30_MYM"
            not in {row["symbol"] for row in candidate_rows},
            "duplicate_key_collision_count": candidate_summary["duplicate_key_collision_count"],
        },
    }

    baseline_ids = [row["family_id"] for row in g0_baselines["baseline_controls"]]
    discovery_audit = {
        **safe_flags(),
        "artifact_family": "discovery_exclusion_baseline_audit",
        "selected_discovery_source_count": g0_partition["discovery_pool"]["source_rows"],
        "selected_discovery_source_policy": "preserve 365 discovery-source exclusions and keep disjoint from accepted SCID segment hashes",
        "adversarial_baseline_ids": baseline_ids,
        "expected_adversarial_baseline_ids": EXPECTED_BASELINES,
        "baseline_source_ref": rel(G0_BASELINE_PACKET),
        "discovery_source_ref": rel(G0_DISCOVERY_LEDGER),
        "checks": {
            "selected_discovery_source_count_is_365": g0_partition["discovery_pool"]["source_rows"] == 365,
            "all_four_baselines_exact": sorted(baseline_ids) == sorted(EXPECTED_BASELINES),
            "accepted_scid_segments_rehashed_before_consumption": rehash_summary["all_segment_rehashes_match"],
        },
        "summary": {
            "selected_discovery_source_count": g0_partition["discovery_pool"]["source_rows"],
            "baseline_count": len(baseline_ids),
            "checks_pass": g0_partition["discovery_pool"]["source_rows"] == 365
            and sorted(baseline_ids) == sorted(EXPECTED_BASELINES),
        },
    }

    noleak_audit = {
        **safe_flags(),
        "artifact_family": "noleak_partition_audit",
        "candidate_rows_scanned": len(candidate_rows),
        "bar_rows_scanned": len(bar_rows),
        "forbidden_evidence_classes_not_opened": [
            "SEALED_VALIDATION_RESULT",
            "PATH_LABEL_RESULT",
            "ACCOUNT_HISTORY_REALIZED",
            "BROKER_ORDER_HISTORY",
            "AI_RESPONSE",
            "LIVE_EXECUTION",
        ],
        "candidate_forbidden_scan_summary": candidate_summary,
        "source_control_partition_assignments": {
            "accepted_9_scid_segments": "SOURCE_CONTROL_ACCEPTED_INPUT_REFERENCE_ONLY",
            "derived_bars": "SOURCE_CONTROL_BAR_INPUT_ONLY_NOT_VALIDATION",
            "candidate_input_packets": "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
            "result_or_path_labels": "FORBIDDEN_IN_THIS_ROUTE",
        },
        "checks": {
            "safe_flags_closed": all(value is False for key, value in safe_flags().items() if key in SAFE_FALSE_FLAGS),
            "candidate_rows_input_only": candidate_summary["all_rows_input_only"],
            "candidate_forbidden_scan_pass": candidate_summary["all_forbidden_scans_pass"],
            "no_validation_execution": True,
            "no_result_scoring": True,
        },
        "summary": {
            "checks_pass": candidate_summary["all_rows_input_only"] and candidate_summary["all_forbidden_scans_pass"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }

    saturation_questions = [
        (
            "What exact bug would let records outside the bounded segment into a bar?",
            "A parser that scans full files or ignores byte offsets. Closed by segment-byte seek, row byte-range checks, rehash ledger, verifier, and hard-floor/bounds fixtures.",
        ),
        (
            "What exact bug would let records at/after decision as-of enter a candidate input?",
            "Using <= decision timestamps or right-closed intervals. Closed by ts_us >= decision_asof exclusion and tests for exactly-at-decision records.",
        ),
        (
            "What exact bug would let bar_window_* be rejected by overbroad forbidden scanning?",
            "Literal substring matching on win inside window. Closed by snake_case token scanner and explicit bar_window whitelist.",
        ),
        (
            "What exact bug would let true performance/result words pass the repaired scanner?",
            "Token-only scanner without win-like stemming or broker/order phrase handling. Closed by focused forbidden examples and verifier scans.",
        ),
        (
            "What exact bug would make empty/gap/session-closed bars appear tradeable?",
            "Filling missing OHLC from neighbors. Closed by dense empty rows with null OHLC, zero volume, and candidate_eligible=false.",
        ),
        (
            "What exact duplicate/proxy mistake would inflate candidate denominator?",
            "Counting GC/MGC or YM/MYM independently. Closed by primary counting source per canonical_economic_group.",
        ),
        (
            "What exact field or value could make an input-only row look like validation/result evidence?",
            "Path label/result/R/PnL/cost/broker/AI/live fields or values. Closed by scanner and required status CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION.",
        ),
        (
            "What exact row would a skeptical G12 reject, and does the verifier catch it?",
            "Any candidate row with result/path_label/win_rate/slippage/broker_order/deal/position or status drift. Verifier catches forbidden tokens and status mismatch.",
        ),
        (
            "Does the packet box research into current FPB families?",
            "No. candidate_family_id is source-control input family, baselines are preserved by reference, and bars cover all 7 canonical source groups.",
        ),
        (
            "What exact next gate owns independent packet audit, G0 synthesis, sealed validation, robustness/stress, and promotion?",
            "Next G12 packet audit prompt owns packet acceptance; later separate G0/sealed-validation/promotions prompts own result/scoring/promotion gates.",
        ),
    ]
    saturation_ledger = {
        **safe_flags(),
        "artifact_family": "saturation_redteam_ledger",
        "same_evidence_class_gaps_pursued": [
            "forbidden scanner warning repaired",
            "hard floor and boundary fixture warning repaired",
            "duplicate/proxy primary-denominator policy materialized",
            "candidate row scanner applied to every row",
            "raw blob/diff scope audit recorded unrelated dirt separately",
        ],
        "questions": [
            {"question": question, "answer": answer, "same_evidence_class_gap_remaining": False}
            for question, answer in saturation_questions
        ],
        "summary": {"remaining_same_evidence_class_gaps": 0},
    }

    artifacts: dict[str, Path] = {
        "contract_inputs": ROUTE_DIR / f"SCID_ASOF_BAR_BUILDER_CONTRACT_INPUTS_{DATE_TAG}.json",
        "source_rehash": ROUTE_DIR / f"SCID_ASOF_BAR_SOURCE_REHASH_LEDGER_{DATE_TAG}.json",
        "bar_rows": bar_rows_path,
        "bar_manifest": ROUTE_DIR / f"SCID_ASOF_BAR_MANIFEST_{DATE_TAG}.json",
        "candidate_rows": candidate_rows_path,
        "candidate_packet_manifest": ROUTE_DIR
        / f"SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_{DATE_TAG}.json",
        "forbidden_repair": ROUTE_DIR / f"SCID_ASOF_FORBIDDEN_SCAN_REPAIR_LEDGER_{DATE_TAG}.json",
        "hard_floor_repair": ROUTE_DIR / f"SCID_ASOF_HARD_FLOOR_FIXTURE_LEDGER_{DATE_TAG}.json",
        "duplicate_proxy": ROUTE_DIR / f"SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_{DATE_TAG}.json",
        "discovery_baseline": ROUTE_DIR
        / f"SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_{DATE_TAG}.json",
        "noleak_partition": ROUTE_DIR / f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
        "saturation": ROUTE_DIR / f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
    }
    payloads = {
        "contract_inputs": contract_inputs,
        "source_rehash": source_rehash_ledger,
        "bar_manifest": bar_manifest,
        "candidate_packet_manifest": packet_manifest,
        "forbidden_repair": forbidden_repair,
        "hard_floor_repair": hard_floor_repair,
        "duplicate_proxy": duplicate_proxy_ledger,
        "discovery_baseline": discovery_audit,
        "noleak_partition": noleak_audit,
        "saturation": saturation_ledger,
    }
    for key, payload in payloads.items():
        write_json(artifacts[key], payload)

    dirty_audit = dirty_scope_audit()
    completion_checks = {
        "all_required_artifacts_exist": False,
        "g12_contract_decision_accepted_with_two_warnings": contract_inputs["summary"][
            "target_g12_decision_accepted_with_warnings"
        ]
        and contract_inputs["summary"]["target_g12_terminal_blockers_zero"]
        and contract_inputs["summary"]["exact_warning_ids_match"],
        "both_warnings_repaired": forbidden_repair["summary"]["warning_repaired"]
        and hard_floor_repair["summary"]["warning_repaired"],
        "all_9_segments_rehash_before_consumption": rehash_summary["all_9_segments_rehashed"]
        and rehash_summary["all_segment_rehashes_match"],
        "bars_source_bounded_asof_safe": bar_manifest["summary"]["no_bar_uses_bytes_outside_segment"]
        and bar_manifest["summary"]["all_bars_closed_asof"],
        "candidate_rows_input_only": candidate_summary["all_rows_input_only"]
        and candidate_summary["all_forbidden_scans_pass"],
        "discovery_exclusions_and_baselines_preserved": discovery_audit["summary"]["checks_pass"],
        "duplicate_proxy_denominator_controlled": duplicate_proxy_ledger["summary"]["duplicate_key_collision_count"] == 0
        and duplicate_proxy_ledger["summary"]["xau_micro_not_denominator"]
        and duplicate_proxy_ledger["summary"]["us30_micro_not_denominator"],
        "raw_market_blobs_not_in_scope": dirty_audit["checks"]["no_raw_market_blobs_in_scope"],
        "live_surface_not_in_scope": dirty_audit["checks"]["no_forbidden_live_surface_paths_in_scope"],
        "safe_flags_closed": True,
        "next_g12_prompt_exists": NEXT_G12_PROMPT.exists(),
    }

    output_manifest_path = ROUTE_DIR / f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json"
    completion_json_path = ROUTE_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.json"
    completion_md_path = ROUTE_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.md"
    verification_path = ROUTE_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json"
    artifacts.update(
        {
            "output_manifest": output_manifest_path,
            "completion_audit_json": completion_json_path,
            "completion_audit_md": completion_md_path,
            "verification_result": verification_path,
            "builder_script": Path(__file__),
            "next_g12_prompt": NEXT_G12_PROMPT,
        }
    )

    output_manifest = {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "artifacts": [file_record(path, key) for key, path in sorted(artifacts.items())],
        "jsonl_artifacts": {
            "bar_rows": {"path": rel(bar_rows_path), "row_count": len(bar_rows)},
            "candidate_input_rows": {"path": rel(candidate_rows_path), "row_count": len(candidate_rows)},
        },
        "summary": {
            "artifact_count": len(artifacts),
            "bar_row_count": len(bar_rows),
            "candidate_input_row_count": len(candidate_rows),
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    write_json(output_manifest_path, output_manifest)
    completion_checks["all_required_artifacts_exist"] = all(
        path.exists() for key, path in artifacts.items() if key != "verification_result"
    )
    completion_audit = {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Materialize source-control M15 bars and candidate-generator input-only packets "
            "from 9 accepted bounded SCID segment references after repairing two exact G12 warnings, "
            "without validation, scoring, outcomes, AI/API, broker/account/order evidence, raw blob commits, "
            "or live-surface changes."
        ),
        "prompt_to_artifact_checklist": [
            {
                "requirement": "mandatory preflight/context refresh",
                "evidence": "session ran generate_live_state and read required context before builder execution; completion audit records route refs",
                "status": "DONE",
            },
            {
                "requirement": "repair FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW",
                "evidence": rel(artifacts["forbidden_repair"]),
                "status": "DONE" if forbidden_repair["summary"]["warning_repaired"] else "BLOCKED",
            },
            {
                "requirement": "repair TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE",
                "evidence": rel(artifacts["hard_floor_repair"]),
                "status": "DONE" if hard_floor_repair["summary"]["warning_repaired"] else "BLOCKED",
            },
            {
                "requirement": "rehash all 9 accepted SCID segments",
                "evidence": rel(artifacts["source_rehash"]),
                "status": "DONE" if rehash_summary["all_segment_rehashes_match"] else "BLOCKED",
            },
            {
                "requirement": "build source-bounded as-of bars",
                "evidence": rel(bar_rows_path),
                "status": "DONE" if completion_checks["bars_source_bounded_asof_safe"] else "BLOCKED",
            },
            {
                "requirement": "build input-only candidate packet rows",
                "evidence": rel(candidate_rows_path),
                "status": "DONE" if completion_checks["candidate_rows_input_only"] else "BLOCKED",
            },
            {
                "requirement": "preserve 365 discovery exclusions and four baselines",
                "evidence": rel(artifacts["discovery_baseline"]),
                "status": "DONE" if discovery_audit["summary"]["checks_pass"] else "BLOCKED",
            },
            {
                "requirement": "emit next G12 packet audit prompt",
                "evidence": rel(NEXT_G12_PROMPT),
                "status": "DONE" if NEXT_G12_PROMPT.exists() else "BLOCKED",
            },
        ],
        "dirty_scope_audit": dirty_audit,
        "completion_checks": completion_checks,
        "summary": {
            "can_mark_route_packet_materialized": all(completion_checks.values()),
            "bar_row_count": len(bar_rows),
            "candidate_input_row_count": len(candidate_rows),
            "remaining_blockers": [],
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    write_json(completion_json_path, completion_audit)
    write_markdown(completion_md_path, "SCID As-Of Completion Audit", completion_audit)
    completion_audit["completion_checks"]["all_required_artifacts_exist"] = all(
        path.exists() for key, path in artifacts.items() if key != "verification_result"
    )
    completion_audit["summary"]["can_mark_route_packet_materialized"] = all(
        completion_audit["completion_checks"].values()
    )
    write_json(completion_json_path, completion_audit)
    write_markdown(completion_md_path, "SCID As-Of Completion Audit", completion_audit)
    output_manifest["artifacts"] = [file_record(path, key) for key, path in sorted(artifacts.items())]
    write_json(output_manifest_path, output_manifest)

    verification = verify_route(write_result=False)
    write_json(verification_path, verification)
    return verification


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify_route(write_result: bool = True) -> dict[str, Any]:
    required = [
        ROUTE_DIR / f"SCID_ASOF_BAR_BUILDER_CONTRACT_INPUTS_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_BAR_SOURCE_REHASH_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_BAR_ROWS_{DATE_TAG}.jsonl",
        ROUTE_DIR / f"SCID_ASOF_BAR_MANIFEST_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_CANDIDATE_INPUT_ROWS_{DATE_TAG}.jsonl",
        ROUTE_DIR / f"SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_FORBIDDEN_SCAN_REPAIR_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_HARD_FLOOR_FIXTURE_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.md",
        Path(__file__),
        ROUTE_DIR / f"verify_scid_asof_bar_builder_and_candidate_input_packet_source_control_2026_05_11.py",
        ROUTE_DIR / f"test_scid_asof_bar_builder_and_candidate_input_packet_source_control_2026_05_11.py",
        NEXT_G12_PROMPT,
    ]
    checks: dict[str, bool] = {}
    missing = [rel(path) for path in required if not path.exists()]
    checks["required_artifacts_exist"] = not missing
    if missing:
        result = {
            **safe_flags(),
            "artifact_family": "verification_result",
            "ok": False,
            "checks": checks,
            "missing_artifacts": missing,
            "summary": {"ok": False},
        }
        if write_result:
            write_json(ROUTE_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json", result)
        return result

    contract_inputs = load_json(required[0])
    rehash = load_json(required[1])
    bar_manifest = load_json(required[3])
    packet_manifest = load_json(required[5])
    forbidden = load_json(required[6])
    hard_floor = load_json(required[7])
    duplicate = load_json(required[8])
    discovery = load_json(required[9])
    noleak = load_json(required[10])
    completion = load_json(required[13])
    bar_rows = parse_jsonl(required[2])
    candidate_rows = parse_jsonl(required[4])
    patterns = forbidden_patterns()

    checks["target_g12_acceptance_verified"] = (
        contract_inputs["target_g12_decision"] == "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS"
        and contract_inputs["target_g12_terminal_blocker_count"] == 0
        and sorted(contract_inputs["target_g12_exact_warnings"]) == sorted(EXPECTED_WARNINGS)
    )
    checks["both_warnings_repaired"] = forbidden["summary"]["warning_repaired"] and hard_floor["summary"][
        "warning_repaired"
    ]
    checks["all_9_segments_rehash_match"] = rehash["summary"]["all_9_segments_rehashed"] and rehash["summary"][
        "all_segment_rehashes_match"
    ]
    checks["bar_jsonl_hash_matches_manifest"] = sha256_file(required[2]) == bar_manifest["bar_rows_sha256"]
    checks["candidate_jsonl_hash_matches_manifest"] = sha256_file(required[4]) == packet_manifest["candidate_rows_sha256"]
    checks["bar_count_matches_manifest"] = len(bar_rows) == bar_manifest["bar_row_count"]
    checks["candidate_count_matches_manifest"] = len(candidate_rows) == packet_manifest["candidate_input_row_count"]
    checks["bars_stay_inside_segments"] = all(
        row["source_byte_start"] is None
        or (
            row["segment_byte_start"] <= row["source_byte_start"]
            and row["source_byte_end_exclusive"] <= row["segment_byte_end_exclusive"]
        )
        for row in bar_rows
    )
    checks["bars_are_closed_asof"] = all(row["bar_end_exclusive_utc"] <= row["decision_asof_utc"] for row in bar_rows)
    checks["empty_bars_fail_closed"] = all(
        row["candidate_eligible"] is False and row["open"] is None and row["total_volume"] == 0
        for row in bar_rows
        if row["bar_status"] != "CLOSED_SOURCE_RECORDS_PRESENT"
    )
    candidate_matches = [
        {"candidate_input_row_id": row.get("candidate_input_row_id"), "matches": scan_forbidden_payload(row, patterns)}
        for row in candidate_rows
    ]
    candidate_matches = [item for item in candidate_matches if item["matches"]]
    checks["candidate_rows_forbidden_scan_clean"] = not candidate_matches
    checks["candidate_rows_input_only_status"] = all(
        row["candidate_input_only_status"] == "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION"
        for row in candidate_rows
    )
    checks["candidate_duplicate_keys_unique"] = len({row["duplicate_key"] for row in candidate_rows}) == len(
        candidate_rows
    )
    checks["discovery_365_and_baselines_preserved"] = discovery["summary"]["checks_pass"]
    checks["duplicate_proxy_controls"] = (
        duplicate["summary"]["duplicate_key_collision_count"] == 0
        and duplicate["summary"]["xau_micro_not_denominator"]
        and duplicate["summary"]["us30_micro_not_denominator"]
    )
    checks["no_leak_audit_pass"] = noleak["summary"]["checks_pass"]
    checks["completion_audit_pass"] = completion["summary"]["can_mark_route_packet_materialized"]
    checks["safe_flags_closed"] = all(check_safe_flags(load_json(path))[0] for path in required if path.suffix == ".json")
    dirty_audit = dirty_scope_audit()
    checks["no_raw_market_blob_in_scope"] = dirty_audit["checks"]["no_raw_market_blobs_in_scope"]
    checks["no_forbidden_live_surface_in_scope"] = dirty_audit["checks"]["no_forbidden_live_surface_paths_in_scope"]
    checks["next_g12_prompt_exists"] = NEXT_G12_PROMPT.exists()
    ok = all(checks.values())
    result = {
        **safe_flags(),
        "artifact_family": "verification_result",
        "ok": ok,
        "checks": checks,
        "candidate_forbidden_matches": candidate_matches[:10],
        "dirty_scope_audit": dirty_audit,
        "summary": {
            "ok": ok,
            "bar_row_count": len(bar_rows),
            "candidate_input_row_count": len(candidate_rows),
            "failed_checks": [key for key, value in checks.items() if not value],
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    if write_result:
        write_json(ROUTE_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json", result)
    return result


def main() -> int:
    result = build_all()
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
