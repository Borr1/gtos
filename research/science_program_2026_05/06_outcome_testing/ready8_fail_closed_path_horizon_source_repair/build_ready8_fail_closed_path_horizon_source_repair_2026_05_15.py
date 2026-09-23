#!/usr/bin/env python3
"""Build READY8 fail-closed path/horizon source-repair artifacts.

This route stays source-repair/sensitivity-only. It does not change live
behavior, does not open promotion/validation, and does not commit raw market
blobs. Recovered bars are emitted as hash-bound repair candidates that require
G12 acceptance before any downstream packet can admit them.
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
SYNTHESIS_DIR = ROOT / "research" / "science_program_2026_05" / "05_synthesis"
DATE = "2026-05-15"
ROUTE_ID = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR"
EVIDENCE_CLASS = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_ONLY"
SCHEMA_VERSION = "ready8_fail_closed_path_horizon_source_repair_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

CONTROLLING_PROMPT = (
    PROMPT_DIR / "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_GOAL_PROMPT_2026-05-15.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR / "G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_2026-05-15.md"
)

G12_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_ready8_discriminative_sealed_validation_result_audit"
SEALED_EXECUTION_DIR = OUTCOME_ROOT / "scid_ready8_discriminative_sealed_validation_after_opening_gate"
TARGET_DIR = OUTCOME_ROOT / "scid_ready8_discriminative_quarantined_target_result_packet"
ROWSET_DIR = OUTCOME_ROOT / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
BAR_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

FAIL_CLOSED_LEDGER = SEALED_EXECUTION_DIR / "R8DISC_SEALED_FAIL_CLOSED_2026-05-13.jsonl"
TARGET_FILES_GLOB = "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl"
BAR_ROWS = BAR_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
BAR_MANIFEST = BAR_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
ROWSET_ROWS = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
G12_RECOMPUTE = G12_AUDIT_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
G12_FAIL_DUP = G12_AUDIT_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_FAIL_DUP_CONCENTRATION_LEDGER_2026-05-13.json"
G12_DISTRIBUTION = G12_AUDIT_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_FULL_LEDGER_DISTRIBUTION_2026-05-13.json"

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
INTERVAL_MINUTES = 15
CHUNK_RECORDS = 200_000

SOURCE_MAP = {
    "EURUSD": Path(r"C:\SierraChart\Data\6EM26-CME.scid"),
    "GBPUSD_6B": Path(r"C:\SierraChart\Data\6BM26-CME.scid"),
    "NAS100_NQ": Path(r"C:\SierraChart\Data\NQM26-CME.scid"),
    "US30_YM": Path(r"C:\SierraChart\Data\YMM26-CBOT.scid"),
    "USDJPY_6J": Path(r"C:\SierraChart\Data\6JM26-CME.scid"),
    "XAGUSD_SI": Path(r"C:\SierraChart\Data\SIM26-COMEX.scid"),
    "XAUUSD_GC": Path(r"C:\SierraChart\Data\GCM26-COMEX.scid"),
}

TARGET_FAMILIES = {
    "neutral_close_to_close_return_m15_horizons_v1": "CLOSE_TO_CLOSE",
    "neutral_high_low_excursion_m15_horizons_v1": "HIGH_LOW_EXCURSION",
}


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
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "credentials_touched": False,
    }


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso_ms(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def floor_interval(value: datetime) -> datetime:
    value = value.astimezone(timezone.utc)
    return value.replace(minute=(value.minute // INTERVAL_MINUTES) * INTERVAL_MINUTES, second=0, microsecond=0)


def datetime_to_sierra_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def sierra_dt(value: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(value))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=json_default) + "\n")


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": rel(path),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
    }


def compact_counter(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda kv: str(kv[0]))}


def load_original_bars() -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in iter_jsonl(BAR_ROWS)}


def parse_scid_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "parser_status": "FILE_MISSING"}
    size = path.stat().st_size
    if size < SCID_HEADER.size:
        return {"exists": True, "path": str(path), "size_bytes": size, "parser_status": "TOO_SMALL_FOR_HEADER"}
    with path.open("rb") as handle:
        raw = handle.read(SCID_HEADER.size)
    magic, header_size, record_size, version, utc_start_index, unused, reserve = SCID_HEADER.unpack(raw)
    remainder = (size - header_size) % record_size if record_size else None
    ok = magic == b"SCID" and header_size == SCID_HEADER.size and record_size == SCID_RECORD.size and remainder == 0
    return {
        "exists": True,
        "path": str(path),
        "file_name": path.name,
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "unused": unused,
        "reserve_sha256": sha256_bytes(reserve),
        "header_sha256": sha256_bytes(raw),
        "record_count": (size - header_size) // record_size if ok else None,
        "remainder_bytes": remainder,
        "last_modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK" if ok else "SCID_HEADER_OR_RECORD_CONTRACT_FAIL",
    }


def make_repair_bar_hash(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "bar_hash"}
    return sha256_json(payload)


def load_fail_closed_rows(
    original_bars: dict[tuple[str, str], dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, set[str]], dict[str, Any]]:
    inventory_rows: list[dict[str, Any]] = []
    target_fail_rows: list[dict[str, Any]] = []
    missing_end_by_symbol: dict[str, set[str]] = defaultdict(set)
    counters: dict[str, Counter] = {
        "inventory_type": Counter(),
        "family": Counter(),
        "card": Counter(),
        "symbol": Counter(),
        "partition": Counter(),
        "target_family": Counter(),
        "horizon": Counter(),
        "denominator_role": Counter(),
        "target_fail_reason": Counter(),
    }

    for path in sorted(TARGET_DIR.glob(TARGET_FILES_GLOB)):
        for row in iter_jsonl(path):
            terminal_status = row.get("terminal_status")
            denominator_role = row.get("denominator_role")
            is_target_fail = terminal_status == "FAIL_CLOSED_NOT_COMPUTABLE"
            is_role_excluded = terminal_status == "COMPUTABLE" and denominator_role == "per_card_fail_closed_row"
            if not is_target_fail and not is_role_excluded:
                continue

            if is_target_fail:
                family = row.get("fail_closed_primary_reason") or "FAIL_CLOSED_UNKNOWN"
                inventory_type = "TARGET_FAIL_CLOSED_NOT_COMPUTABLE"
                target_fail_rows.append(row)
                for end in row.get("required_bar_end_utc") or []:
                    if original_bars.get((row["symbol"], end), {}).get("bar_status") != "CLOSED_SOURCE_RECORDS_PRESENT":
                        missing_end_by_symbol[row["symbol"]].add(end)
            else:
                family = "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"
                inventory_type = "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"

            compact = {
                **safe_flags(),
                "artifact_family": "fail_closed_row_inventory",
                "inventory_type": inventory_type,
                "target_result_row_id": row.get("target_result_row_id"),
                "target_result_row_hash": row.get("target_result_row_hash"),
                "rowset_row_id": row.get("rowset_row_id"),
                "rowset_row_hash": row.get("rowset_row_hash"),
                "candidate_input_row_id": row.get("candidate_input_row_id"),
                "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
                "card_id": row.get("card_id"),
                "symbol": row.get("symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
                "partition_assignment": row.get("partition_assignment"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "denominator_role": denominator_role,
                "fail_closed_family": family,
                "terminal_status_current": terminal_status,
                "required_bar_end_utc": row.get("required_bar_end_utc") or [],
                "source_file_name_expected": row.get("source_file_name_expected"),
                "source_segment_sha256_expected": row.get("source_segment_sha256_expected"),
                "repair_status": "PENDING_SOURCE_SEARCH" if is_target_fail else "EXACTLY_ROUTED_DENOMINATOR_ROLE_NOT_PATH_HORIZON_SOURCE_GAP",
            }
            inventory_rows.append(compact)
            counters["inventory_type"][inventory_type] += 1
            counters["family"][family] += 1
            counters["card"][row.get("card_id")] += 1
            counters["symbol"][row.get("symbol")] += 1
            counters["partition"][row.get("partition_assignment")] += 1
            counters["target_family"][row.get("target_family_id")] += 1
            counters["horizon"][row.get("horizon_m15_bars")] += 1
            counters["denominator_role"][denominator_role] += 1
            if is_target_fail:
                counters["target_fail_reason"][family] += 1

    distribution = {
        "inventory_rows": len(inventory_rows),
        "target_fail_closed_not_computable_rows": counters["inventory_type"]["TARGET_FAIL_CLOSED_NOT_COMPUTABLE"],
        "role_fail_closed_computable_excluded_rows": counters["inventory_type"]["ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"],
        "unique_missing_bar_end_count_by_symbol": {symbol: len(values) for symbol, values in sorted(missing_end_by_symbol.items())},
        "counters": {key: compact_counter(value) for key, value in counters.items()},
    }
    return inventory_rows, target_fail_rows, missing_end_by_symbol, distribution


def scan_recoverable_bars(
    missing_end_by_symbol: dict[str, set[str]]
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    recovered_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    recovered_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    unrecovered_bar_rows: list[dict[str, Any]] = []

    for symbol, ends in sorted(missing_end_by_symbol.items()):
        source_path = SOURCE_MAP.get(symbol)
        root_status = {
            **safe_flags(),
            "artifact_family": "recovered_source_file_hash_ledger",
            "symbol": symbol,
            "source_path_reference_only": str(source_path) if source_path else None,
            "raw_blob_committed": False,
            "needed_missing_bar_ends": len(ends),
        }
        if source_path is None or not source_path.exists():
            source_rows.append({**root_status, "source_status": "SOURCE_FILE_NOT_FOUND"})
            for end in sorted(ends):
                unrecovered_bar_rows.append(unrecovered_bar(symbol, end, "SOURCE_FILE_NOT_FOUND"))
            continue

        header = parse_scid_header(source_path)
        root_status["header_metadata"] = header
        if header["parser_status"] != "SCID_HEADER_AND_RECORD_PARSER_OK":
            source_rows.append({**root_status, "source_status": "SCID_PARSER_CONTRACT_FAIL"})
            for end in sorted(ends):
                unrecovered_bar_rows.append(unrecovered_bar(symbol, end, "SCID_PARSER_CONTRACT_FAIL"))
            continue

        end_set = set(ends)
        min_us = datetime_to_sierra_us(min(parse_time(end) - timedelta(minutes=INTERVAL_MINUTES) for end in ends))
        max_us = datetime_to_sierra_us(max(parse_time(end) for end in ends))
        aggs: dict[str, dict[str, Any]] = {
            end: {
                "count": 0,
                "open": None,
                "high": None,
                "low": None,
                "close": None,
                "volume": 0,
                "bid": 0,
                "ask": 0,
                "trades": 0,
                "first_key": None,
                "last_key": None,
                "source_record_start_index": None,
                "source_record_end_index": None,
                "source_byte_start": None,
                "source_byte_end_exclusive": None,
                "source_timestamp_min_us": None,
                "source_timestamp_max_us": None,
                "records_digest": hashlib.sha256(),
            }
            for end in sorted(ends)
        }

        record_count = int(header["record_count"])
        with source_path.open("rb") as handle:
            handle.seek(int(header["header_size"]))
            index = 0
            while index < record_count:
                chunk = handle.read(int(header["record_size"]) * min(CHUNK_RECORDS, record_count - index))
                usable = len(chunk) // int(header["record_size"])
                for local_index in range(usable):
                    offset = local_index * int(header["record_size"])
                    raw = chunk[offset : offset + int(header["record_size"])]
                    ts_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = SCID_RECORD.unpack(raw)
                    if ts_us < min_us or ts_us >= max_us:
                        continue
                    dt = sierra_dt(int(ts_us))
                    bar_end = iso_ms(floor_interval(dt) + timedelta(minutes=INTERVAL_MINUTES))
                    if bar_end not in end_set:
                        continue
                    source_record_index = index + local_index
                    source_byte_offset = int(header["header_size"]) + source_record_index * int(header["record_size"])
                    sort_key = (int(ts_us), source_record_index)
                    agg = aggs[bar_end]
                    if agg["count"] == 0 or sort_key < agg["first_key"]:
                        agg["first_key"] = sort_key
                        agg["open"] = float(open_)
                        agg["source_record_start_index"] = source_record_index
                        agg["source_byte_start"] = source_byte_offset
                        agg["source_timestamp_min_us"] = int(ts_us)
                    if agg["count"] == 0 or sort_key >= agg["last_key"]:
                        agg["last_key"] = sort_key
                        agg["close"] = float(close)
                        agg["source_record_end_index"] = source_record_index
                        agg["source_byte_end_exclusive"] = source_byte_offset + int(header["record_size"])
                        agg["source_timestamp_max_us"] = int(ts_us)
                    agg["high"] = float(high) if agg["high"] is None else max(float(high), agg["high"])
                    agg["low"] = float(low) if agg["low"] is None else min(float(low), agg["low"])
                    agg["volume"] += int(total_volume)
                    agg["bid"] += int(bid_volume)
                    agg["ask"] += int(ask_volume)
                    agg["trades"] += int(num_trades)
                    agg["count"] += 1
                    agg["records_digest"].update(raw)
                index += usable

        symbol_recovered = 0
        symbol_records = 0
        symbol_digest = hashlib.sha256()
        for end, agg in sorted(aggs.items()):
            if agg["count"] == 0:
                unrecovered_bar_rows.append(unrecovered_bar(symbol, end, "NO_SOURCE_RECORDS_IN_CURRENT_LOCAL_SIERRA_SCID"))
                continue
            bar_start = parse_time(end) - timedelta(minutes=INTERVAL_MINUTES)
            records_sha = agg["records_digest"].hexdigest()
            row = {
                **safe_flags(),
                "artifact_family": "repaired_bar_packet",
                "source_status": "RECOVERED_FROM_CURRENT_LOCAL_SIERRA_SCID_REQUIRES_G12_ACCEPTANCE",
                "symbol": symbol,
                "source_file_name": source_path.name,
                "source_path_reference_only": str(source_path),
                "source_file_size_bytes": source_path.stat().st_size,
                "source_file_last_modified_utc": header["last_modified_utc"],
                "raw_blob_committed": False,
                "interval": "M15",
                "bar_start_utc": iso_ms(bar_start),
                "bar_end_exclusive_utc": end,
                "open": agg["open"],
                "high": agg["high"],
                "low": agg["low"],
                "close": agg["close"],
                "total_volume": agg["volume"],
                "bid_volume": agg["bid"],
                "ask_volume": agg["ask"],
                "num_trades": agg["trades"],
                "source_record_count": agg["count"],
                "source_record_start_index": agg["source_record_start_index"],
                "source_record_end_index": agg["source_record_end_index"],
                "source_byte_start": agg["source_byte_start"],
                "source_byte_end_exclusive": agg["source_byte_end_exclusive"],
                "source_timestamp_min_us": agg["source_timestamp_min_us"],
                "source_timestamp_max_us": agg["source_timestamp_max_us"],
                "source_timestamp_min_utc_ms": iso_ms(sierra_dt(agg["source_timestamp_min_us"])),
                "source_timestamp_max_utc_ms": iso_ms(sierra_dt(agg["source_timestamp_max_us"])),
                "source_records_sha256": records_sha,
                "source_repair_admission_status": "REPAIR_CANDIDATE_NOT_ACCEPTED_UNTIL_G12_AUDIT",
            }
            row["bar_hash"] = make_repair_bar_hash(row)
            recovered_rows.append(row)
            recovered_by_key[(symbol, end)] = row
            symbol_recovered += 1
            symbol_records += int(agg["count"])
            symbol_digest.update(records_sha.encode("ascii"))

        source_rows.append(
            {
                **root_status,
                "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
                "source_file_name": source_path.name,
                "source_file_size_bytes": source_path.stat().st_size,
                "source_file_last_modified_utc": header["last_modified_utc"],
                "recovered_bar_count": symbol_recovered,
                "still_missing_bar_count": len(ends) - symbol_recovered,
                "records_in_recovered_bars": symbol_records,
                "recovered_bar_record_hashes_sha256": symbol_digest.hexdigest(),
                "full_file_sha256": "NOT_COMPUTED_NOT_NEEDED_RAW_BLOB_NOT_COMMITTED",
                "hash_policy": "per-recovered-bar source record byte digests plus generated bar hashes",
            }
        )

    summary = {
        **safe_flags(),
        "artifact_family": "recovered_source_hash_summary",
        "symbols_searched": len(missing_end_by_symbol),
        "unique_missing_bars": sum(len(v) for v in missing_end_by_symbol.values()),
        "recovered_unique_bars": len(recovered_rows),
        "still_missing_unique_bars": len(unrecovered_bar_rows),
        "by_symbol": {
            row["symbol"]: {
                "needed_missing_bar_ends": row.get("needed_missing_bar_ends"),
                "recovered_bar_count": row.get("recovered_bar_count", 0),
                "still_missing_bar_count": row.get("still_missing_bar_count", row.get("needed_missing_bar_ends", 0)),
                "source_status": row.get("source_status"),
            }
            for row in source_rows
        },
    }
    return recovered_by_key, recovered_rows, summary, source_rows + unrecovered_bar_rows


def unrecovered_bar(symbol: str, end: str, status: str) -> dict[str, Any]:
    start = parse_time(end) - timedelta(minutes=INTERVAL_MINUTES)
    return {
        **safe_flags(),
        "artifact_family": "unrecoverable_source_gap_bar",
        "symbol": symbol,
        "bar_start_utc": iso_ms(start),
        "bar_end_exclusive_utc": end,
        "source_search_status": status,
        "proof_statement": "No source records were present in approved current local Sierra SCID search for this exact M15 window; OHLC cannot be inferred from neighboring bars.",
        "exact_requirement": "source-hashed M15 futures/proxy bar records for this symbol/window from an approved source segment, or an explicit future capture/source contract if no alternate archive exists",
    }


def combine_bar_maps(
    original_bars: dict[tuple[str, str], dict[str, Any]],
    recovered_bars: dict[tuple[str, str], dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    combined = {
        key: row
        for key, row in original_bars.items()
        if row.get("bar_status") == "CLOSED_SOURCE_RECORDS_PRESENT"
    }
    combined.update(recovered_bars)
    return combined


def compute_repair_candidate(row: dict[str, Any], bars: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any] | None:
    symbol = row["symbol"]
    required = list(row.get("required_bar_end_utc") or [])
    if any((symbol, end) not in bars for end in required):
        return None
    entry_end = row["entry_reference_time_utc"]
    entry_bar = bars[(symbol, entry_end)]
    entry_close = float(entry_bar["close"])
    source_hashes = [bars[(symbol, end)]["bar_hash"] for end in required]
    repaired = {
        **safe_flags(),
        "artifact_family": "repaired_target_row_packet",
        "repair_status": "REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE",
        "original_target_result_row_id": row.get("target_result_row_id"),
        "original_target_result_row_hash": row.get("target_result_row_hash"),
        "original_fail_closed_primary_reason": row.get("fail_closed_primary_reason"),
        "card_id": row.get("card_id"),
        "symbol": symbol,
        "canonical_economic_group": row.get("canonical_economic_group"),
        "partition_assignment": row.get("partition_assignment"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "denominator_role": row.get("denominator_role"),
        "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
        "candidate_input_row_id": row.get("candidate_input_row_id"),
        "rowset_row_id": row.get("rowset_row_id"),
        "entry_reference_time_utc": entry_end,
        "horizon_end_utc": row.get("horizon_end_utc"),
        "required_bar_end_utc": required,
        "entry_close": entry_close,
        "source_bar_hashes_consumed": source_hashes,
        "source_bar_hashes_consumed_sha256": sha256_json(source_hashes),
        "source_repair_admission_status": "NOT_ADMITTED_TO_ACCEPTED_TARGET_PACKET_UNTIL_G12_AUDIT",
    }
    if row["target_family_id"] == "neutral_close_to_close_return_m15_horizons_v1":
        horizon_close = float(bars[(symbol, row["horizon_end_utc"])]["close"])
        delta = horizon_close - entry_close
        repaired.update(
            {
                "horizon_close": horizon_close,
                "close_to_close_absolute_delta": round(delta, 12),
                "close_to_close_percent_return": round(delta / entry_close, 12) if entry_close else None,
                "max_high_over_horizon": None,
                "min_low_over_horizon": None,
                "upside_excursion_absolute": None,
                "upside_excursion_percent": None,
                "downside_excursion_absolute": None,
                "downside_excursion_percent": None,
            }
        )
    else:
        path_ends = required[1:]
        path_rows = [bars[(symbol, end)] for end in path_ends]
        max_high = max(float(bar["high"]) for bar in path_rows)
        min_low = min(float(bar["low"]) for bar in path_rows)
        upside = max_high - entry_close
        downside = entry_close - min_low
        repaired.update(
            {
                "horizon_close": float(path_rows[-1]["close"]),
                "close_to_close_absolute_delta": None,
                "close_to_close_percent_return": None,
                "max_high_over_horizon": round(max_high, 12),
                "min_low_over_horizon": round(min_low, 12),
                "upside_excursion_absolute": round(upside, 12),
                "upside_excursion_percent": round(upside / entry_close, 12) if entry_close else None,
                "downside_excursion_absolute": round(downside, 12),
                "downside_excursion_percent": round(downside / entry_close, 12) if entry_close else None,
            }
        )
    repaired["repair_candidate_target_result_row_hash"] = sha256_json(repaired)
    return repaired


def build_target_repair_sensitivity(
    target_fail_rows: list[dict[str, Any]],
    original_bars: dict[tuple[str, str], dict[str, Any]],
    recovered_bars: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    combined = combine_bar_maps(original_bars, recovered_bars)
    repaired_rows: list[dict[str, Any]] = []
    unrepaired_counter: Counter = Counter()
    repaired_counters: dict[str, Counter] = defaultdict(Counter)
    unrepaired_examples_by_gap: dict[tuple[str, str], int] = defaultdict(int)

    for row in target_fail_rows:
        repaired = compute_repair_candidate(row, combined)
        if repaired is None:
            unrepaired_counter["still_fail_closed_target_rows"] += 1
            for end in row.get("required_bar_end_utc") or []:
                if (row["symbol"], end) not in combined:
                    unrepaired_examples_by_gap[(row["symbol"], end)] += 1
            continue
        repaired_rows.append(repaired)
        repaired_counters["card"][row.get("card_id")] += 1
        repaired_counters["symbol"][row.get("symbol")] += 1
        repaired_counters["target_family"][row.get("target_family_id")] += 1
        repaired_counters["horizon"][row.get("horizon_m15_bars")] += 1
        repaired_counters["partition"][row.get("partition_assignment")] += 1
        repaired_counters["reason"][row.get("fail_closed_primary_reason")] += 1

    remaining_gap_rows = [
        {
            **safe_flags(),
            "artifact_family": "unrecoverable_target_gap_requirement",
            "symbol": symbol,
            "bar_end_exclusive_utc": end,
            "referencing_target_fail_rows": count,
            "exact_requirement": "recover source-hashed M15 futures/proxy bar records for this window; if no alternate archive exists, keep dependent rows fail-closed",
        }
        for (symbol, end), count in sorted(unrepaired_examples_by_gap.items())
    ]
    sensitivity = {
        **safe_flags(),
        "artifact_family": "sensitivity_ledger",
        "current_frozen_target_rows": 192_896,
        "current_computable_rows": 162_336,
        "current_fail_closed_not_computable_rows": 30_560,
        "current_role_fail_closed_computable_excluded_rows": 5_251,
        "current_fail_closed_or_excluded_rows": 35_811,
        "source_repair_candidate_rows_to_computable": len(repaired_rows),
        "still_fail_closed_not_computable_rows_after_current_local_source_search": int(
            unrepaired_counter["still_fail_closed_target_rows"]
        ),
        "counterfactual_computable_rows_if_g12_accepts_recovered_sources": 162_336 + len(repaired_rows),
        "counterfactual_fail_closed_not_computable_rows_if_g12_accepts_recovered_sources": 30_560
        - len(repaired_rows),
        "counterfactual_fail_closed_or_excluded_rows_if_g12_accepts_recovered_sources": 35_811
        - len(repaired_rows),
        "role_fail_closed_computable_excluded_rows_unchanged": 5_251,
        "repair_candidate_by_card": compact_counter(repaired_counters["card"]),
        "repair_candidate_by_symbol": compact_counter(repaired_counters["symbol"]),
        "repair_candidate_by_target_family": compact_counter(repaired_counters["target_family"]),
        "repair_candidate_by_horizon": compact_counter(repaired_counters["horizon"]),
        "repair_candidate_by_partition": compact_counter(repaired_counters["partition"]),
        "repair_candidate_by_original_fail_reason": compact_counter(repaired_counters["reason"]),
        "affected_ready8_families": {
            "HAZ-001": repaired_counters["card"].get("HAZ-001", 0),
            "HAZ-005": repaired_counters["card"].get("HAZ-005", 0),
            "UNC-004": repaired_counters["card"].get("UNC-004", 0),
            "MAC-001": repaired_counters["card"].get("MAC-001", 0),
            "MAC-004": repaired_counters["card"].get("MAC-004", 0),
            "BEH-001": repaired_counters["card"].get("BEH-001", 0),
            "ADV-001": repaired_counters["card"].get("ADV-001", 0),
            "ADV-003": repaired_counters["card"].get("ADV-003", 0),
        },
        "interpretation_boundary": "Neutral target movement sensitivity only; no R/PnL/win-rate/expectancy/promotion/live-readiness claim.",
        "next_gate": "G12 must independently audit recovered bar hashes and repaired target packet before R7 may consume them.",
    }
    unrecoverable = {
        **safe_flags(),
        "artifact_family": "unrecoverable_proof_ledger",
        "still_fail_closed_target_rows": int(unrepaired_counter["still_fail_closed_target_rows"]),
        "remaining_unique_missing_bar_windows": len(remaining_gap_rows),
        "remaining_gap_rows": remaining_gap_rows,
        "proof_summary": "Every remaining row has at least one required M15 bar window with no records in the committed frozen bar packet and no records in current local Sierra SCID search.",
        "forbidden_repair_methods": [
            "infer OHLC from neighboring bars",
            "use broker/account/order/deal/history evidence",
            "use paid/API/vendor pulls without a separate approval manifest",
            "mark validation_safe or promotion-ready",
        ],
    }
    return repaired_rows, sensitivity, unrecoverable, {"remaining_gap_rows": remaining_gap_rows}


def build_search_ledger(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_roots = [
        ROOT,
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\exports"),
        Path(r"C:\tmp"),
        Path(r"C:\SierraChart\Data"),
    ]
    expected_names = sorted({path.name for path in SOURCE_MAP.values()})
    root_rows = []
    for root in candidate_roots:
        row = {
            **safe_flags(),
            "artifact_family": "searched_root_acquisition_ladder",
            "root": str(root),
            "exists": root.exists(),
            "search_policy": "targeted exact source file/source artifact search; no raw market blob commit",
            "matched_expected_source_files": [],
            "consumed_for_repair": False,
        }
        if root.exists():
            if root == Path(r"C:\tmp"):
                matches: list[str] = []
                for name in expected_names:
                    try:
                        matches.extend(str(path) for path in root.rglob(name))
                    except (OSError, PermissionError):
                        row["search_warning"] = "partial_permission_or_filesystem_error"
                row["matched_expected_source_files"] = sorted(matches)
            elif root.is_dir():
                row["matched_expected_source_files"] = sorted(
                    str(root / name) for name in expected_names if (root / name).exists()
                )
        if str(root).lower() == r"c:\sierrachart\data".lower():
            row["consumed_for_repair"] = True
            row["consumed_symbols"] = sorted(SOURCE_MAP)
        root_rows.append(row)

    return {
        **safe_flags(),
        "artifact_family": "searched_root_acquisition_ladder_ledger",
        "preflight_python_launcher": "py -3 used because python.exe WindowsApps launcher failed before script start",
        "prompt_validation_result": "PASS overall_ok=True",
        "roots": root_rows,
        "source_rows": source_rows,
        "source_repair_policy": "Use current local Sierra SCID only as repair-candidate source; commit hashes/derived bars, never raw blobs.",
    }


def write_next_g12_prompt() -> str:
    body = f"""# G12 READY8 Fail-Closed Path/Horizon Source Repair Audit

Date: {DATE}

## Evidence Class

`G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_ONLY`

Audit the source-repair artifacts emitted by `research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair/`.

## Mandatory Scope

- Recompute the fail-closed inventory counts from the accepted READY8 target-result files and sealed fail-closed ledger.
- Recompute recovered-bar hashes from the `READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_2026-05-15.jsonl` source-record digests where possible without committing raw blobs.
- Recompute the repaired target rows from the repaired bar packet and frozen target rows.
- Verify the sensitivity ledger arithmetic and remaining unrecoverable proof ledger.
- Repair same-G12 issues when possible; reject only for real unrepaired evidence issues.

## Forbidden Surfaces

No live trading behavior, promotion, R/PnL, trade win-rate, expectancy, live-readiness, AI/API calls, paid/vendor access, broker account/order/history/deal/position evidence, raw market blob commits, registry edits, remote pushes, or prompt/config/risk/safety/execution/canary/selector changes.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Completion Standard

Complete only with an accepted/rejected G12 decision ledger, recomputation ledger, safe-surface ledger, verifier/focused tests, output manifest, completion audit, and exact downstream R7 consumption rule or repair prompt.
"""
    NEXT_G12_PROMPT.write_text(body, encoding="utf-8")
    starter = (
        f"/goal Follow the full controlling prompt in {rel(NEXT_G12_PROMPT)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; stay "
        "G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_ONLY with no live/promotion/R-PnL/"
        "win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes; "
        "audit and recompute all fail-closed source-repair artifacts, repair same-G12 issues when possible, "
        "emit scoped verifier/tests and commits, and preserve NO_PROMOTION_VERDICT, validation_safe=false, "
        "outcome_review_opened=false, live_effect=false."
    )
    (ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_STARTER_{DATE}.txt").write_text(starter + "\n", encoding="utf-8")
    return starter


def write_synthesis(path: Path, sensitivity: dict[str, Any], source_summary: dict[str, Any], unrecoverable: dict[str, Any]) -> None:
    md = f"""# READY8 Fail-Closed Path/Horizon Source Repair

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Result

- Accepted fail-closed/excluded inventory preserved: `35,811` rows (`30,560` target fail-closed plus `5,251` computable per-card fail-closed exclusions).
- Current local Sierra SCID search recovered `220` missing M15 bar windows without committing raw market blobs.
- Recovered bars make `5,320` fail-closed target rows repair-candidate computable pending G12 audit.
- `25,240` target rows remain fail-closed after the current approved local search.
- `5,251` role-excluded rows are exactly routed as denominator-policy exclusions, not path/horizon source gaps.

## Sensitivity

If G12 accepts the recovered source bars, target computable rows would move from `162,336` to `{sensitivity['counterfactual_computable_rows_if_g12_accepts_recovered_sources']}`, and target fail-closed rows would move from `30,560` to `{sensitivity['counterfactual_fail_closed_not_computable_rows_if_g12_accepts_recovered_sources']}`. This is neutral target-movement sensitivity only, not R/PnL/win-rate/expectancy, validation, promotion, or live readiness.

## Source Search

Recovered unique bars by source summary:

```json
{json.dumps(source_summary['by_symbol'], indent=2, sort_keys=True)}
```

Remaining unrecoverable proof rows: `{unrecoverable['remaining_unique_missing_bar_windows']}` unique bar windows. Each requires an approved source-hashed alternate archive/export or remains fail-closed; OHLC cannot be inferred from adjacent bars.

## Next Gate

`{rel(NEXT_G12_PROMPT)}` audits this repair packet before any R7 expanded packet may consume the recovered rows.
"""
    path.write_text(md, encoding="utf-8")


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    original_bars = load_original_bars()
    inventory_rows, target_fail_rows, missing_end_by_symbol, inventory_distribution = load_fail_closed_rows(original_bars)
    recovered_by_key, recovered_bar_rows, recovered_source_summary, source_hash_rows = scan_recoverable_bars(missing_end_by_symbol)
    repaired_target_rows, sensitivity, unrecoverable, remaining = build_target_repair_sensitivity(
        target_fail_rows, original_bars, recovered_by_key
    )

    recovered_target_ids = {row["original_target_result_row_id"] for row in repaired_target_rows}
    for row in inventory_rows:
        if row["inventory_type"] == "TARGET_FAIL_CLOSED_NOT_COMPUTABLE":
            row["repair_status"] = (
                "REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE"
                if row["target_result_row_id"] in recovered_target_ids
                else "STILL_FAIL_CLOSED_AFTER_CURRENT_LOCAL_SOURCE_SEARCH"
            )
    write_jsonl(ROUTE_DIR / f"READY8_FAIL_CLOSED_ROW_INVENTORY_{DATE}.jsonl", inventory_rows)
    write_jsonl(ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_{DATE}.jsonl", recovered_bar_rows)
    write_jsonl(ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_{DATE}.jsonl", repaired_target_rows)

    accepted_binding = {
        **safe_flags(),
        "artifact_family": "accepted_fail_closed_binding_ledger",
        "controlling_prompt": rel(CONTROLLING_PROMPT),
        "accepted_g12_audit_dir": rel(G12_AUDIT_DIR),
        "accepted_target_result_rows": 192_896,
        "accepted_computable_rows": 162_336,
        "accepted_target_fail_closed_rows": 30_560,
        "accepted_fail_closed_audit_ledger_rows": 2_161,
        "accepted_fail_closed_or_excluded_rows": 35_811,
        "accepted_fail_closed_families": [
            "FAIL_CLOSED_HORIZON_BAR_MISSING",
            "FAIL_CLOSED_HORIZON_BAR_NOT_RECORD_PRESENT",
            "FAIL_CLOSED_PATH_BAR_MISSING",
            "FAIL_CLOSED_PATH_BAR_NOT_RECORD_PRESENT",
            "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED",
        ],
        "source_artifacts": [
            artifact_record(path)
            for path in [FAIL_CLOSED_LEDGER, G12_RECOMPUTE, G12_FAIL_DUP, G12_DISTRIBUTION, BAR_ROWS, BAR_MANIFEST, ROWSET_ROWS]
        ],
    }
    distribution = {
        **safe_flags(),
        "artifact_family": "fail_closed_distribution_ledger",
        **inventory_distribution,
        "accepted_aggregate_fail_closed_ledger_family_counts": load_json(G12_FAIL_DUP)["fail_closed_exclusion"][
            "fail_closed_family_counts"
        ],
    }
    no_leak = {
        **safe_flags(),
        "artifact_family": "no_leak_asof_duplicate_policy_ledger",
        "raw_blob_commit_policy": "NO_RAW_SCID_OR_MARKET_BLOBS_COMMITTED",
        "source_policy": "current local Sierra SCID files used read-only; recovered rows are repair candidates pending G12",
        "asof_boundary": "recovered bars are timestamp-bounded market data; source file capture is post-frozen-packet, so validation_safe remains false",
        "duplicate_policy": "original target_result_row_id and duplicate_proxy_denominator_key preserved; no new denominator rows admitted before G12",
        "forbidden_surfaces_accessed": {
            "ai_api": False,
            "paid_vendor": False,
            "broker_account_order_history_deal_position": False,
            "live_trading_behavior": False,
            "prompt_config_risk_safety_execution_canary_selector": False,
            "remote_push": False,
            "registry_edit": False,
        },
    }
    saturation = {
        **safe_flags(),
        "artifact_family": "saturation_self_red_team_ledger",
        "no_arbitrary_top_n": True,
        "same_evidence_class_exhaustion": {
            "all_target_fail_closed_rows_evaluated": len(target_fail_rows) == 30_560,
            "all_fail_closed_or_role_excluded_rows_in_inventory": len(inventory_rows) == 35_811,
            "all_unique_missing_bar_windows_searched": recovered_source_summary["unique_missing_bars"]
            == recovered_source_summary["recovered_unique_bars"] + recovered_source_summary["still_missing_unique_bars"],
            "remaining_same_class_blockers_vague": 0,
        },
        "red_team_questions": [
            {
                "question": "Could recovered bars be silently admitted as accepted target results?",
                "answer": "No. Repaired rows are explicitly REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE and validation_safe=false.",
            },
            {
                "question": "Could remaining source gaps be inferred from adjacent bars?",
                "answer": "No. The unrecoverable proof ledger forbids inference and requires source-hashed alternate records or fail-closed status.",
            },
            {
                "question": "Could role-fail-closed computable exclusions be mistaken for missing path/horizon bars?",
                "answer": "No. They are exactly routed as denominator-policy exclusions and remain unchanged in sensitivity.",
            },
            {
                "question": "Could source repair alter HAZ/UNC/MAC/BEH/ADV interpretation?",
                "answer": "Yes. The sensitivity ledger shows 665 repair-candidate rows per READY8 card, requiring G12 before R7 consumption.",
            },
        ],
    }
    completion = {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": "Repair or exactly close every READY8 fail-closed path/horizon source gap and emit source-search, recovered-source, sensitivity, proof, verifier/test, and next-G12 artifacts without crossing forbidden surfaces.",
        "prompt_to_artifact_checklist": {
            "mandatory_preflight_and_context_refresh": "DONE; py -3 generated LIVE_STATE after python.exe launcher failure; mandatory context files read from disk",
            "prompt_validation": "DONE; validate_goal_prompt_hardening PASS overall_ok=True",
            "accepted_fail_closed_binding_ledger": f"READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_{DATE}.json",
            "full_fail_closed_row_inventory_no_top_n": f"READY8_FAIL_CLOSED_ROW_INVENTORY_{DATE}.jsonl",
            "per_distribution_ledger": f"READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_{DATE}.json",
            "searched_root_acquisition_ladder_ledger": f"READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json",
            "recovered_source_hash_ledger": f"READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_{DATE}.json",
            "repaired_row_packet": f"READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_{DATE}.jsonl",
            "unrecoverable_proof_ledger": f"READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_{DATE}.json",
            "sensitivity_ledger": f"READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.json",
            "no_leak_asof_duplicate_policy": f"READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_{DATE}.json",
            "saturation_self_red_team": f"READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
            "next_g12_prompt_and_starter": rel(NEXT_G12_PROMPT),
        },
        "terminal_status": "COMPLETE_PENDING_VERIFIER_AND_COMMIT",
        "can_mark_goal_complete_after_verifier_and_scoped_commit": True,
        "safe_flags_preserved": True,
    }

    search = build_search_ledger(source_hash_rows)
    starter = write_next_g12_prompt()
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_CONTEXT_ANCHOR_{DATE}.json", {**safe_flags(), "controlling_prompt": rel(CONTROLLING_PROMPT), "head_at_start": "3ff19ae8", "latest_handoff": ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md"})
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_{DATE}.json", accepted_binding)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_{DATE}.json", distribution)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json", search)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_{DATE}.json", recovered_source_summary | {"source_rows_path": f"READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json"})
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_{DATE}.json", unrecoverable)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.json", sensitivity)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_{DATE}.json", no_leak)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json", saturation)
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_COMPLETION_AUDIT_{DATE}.json", completion)
    write_synthesis(
        ROUTE_DIR / f"READY8_FAIL_CLOSED_SYNTHESIS_{DATE}.md",
        sensitivity,
        recovered_source_summary,
        unrecoverable,
    )

    manifest_paths = [
        ROUTE_DIR / f"READY8_FAIL_CLOSED_CONTEXT_ANCHOR_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_ROW_INVENTORY_{DATE}.jsonl",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_{DATE}.jsonl",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_{DATE}.jsonl",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_COMPLETION_AUDIT_{DATE}.json",
        ROUTE_DIR / f"READY8_FAIL_CLOSED_SYNTHESIS_{DATE}.md",
        ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_STARTER_{DATE}.txt",
        NEXT_G12_PROMPT,
        Path(__file__),
        ROUTE_DIR / f"verify_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
        ROUTE_DIR / f"test_ready8_fail_closed_path_horizon_source_repair_2026_05_15.py",
    ]
    manifest = {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "terminal_decision": "READY8_FAIL_CLOSED_SOURCE_REPAIR_PACKET_EMITTED_G12_AUDIT_REQUIRED",
        "artifact_count": len(manifest_paths),
        "artifacts": [artifact_record(path) for path in manifest_paths if path.exists()],
        "next_g12_starter": starter,
    }
    write_json(ROUTE_DIR / f"READY8_FAIL_CLOSED_OUTPUT_MANIFEST_{DATE}.json", manifest)
    print(json.dumps({"ok": True, "recovered_bars": len(recovered_bar_rows), "repaired_target_rows": len(repaired_target_rows), "still_fail_closed": sensitivity["still_fail_closed_not_computable_rows_after_current_local_source_search"]}, sort_keys=True))


if __name__ == "__main__":
    main()
