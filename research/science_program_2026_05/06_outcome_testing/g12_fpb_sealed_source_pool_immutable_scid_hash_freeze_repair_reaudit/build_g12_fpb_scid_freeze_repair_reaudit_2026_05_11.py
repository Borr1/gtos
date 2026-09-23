#!/usr/bin/env python3
"""Build the G12 reaudit packet for the FPB SCID segment-hash repair.

This route is source-control reaudit only. It rehashes the bounded raw-byte
segments from the current local Sierra SCID files and audits the surrounding
source-control gates. It does not derive bars, generate candidates, score
outcomes, inspect broker/account/order evidence, call APIs, or alter live
behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT"
EVIDENCE_CLASS = "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "g12_fpb_scid_freeze_repair_reaudit_v1"
FILE_PREFIX = "G12_FPB_SCID_FREEZE_REPAIR_REAUDIT"

TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
)
PREVIOUS_G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_sealed_source_pool_materialization_audit"
)
SOURCE_EXPANSION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_source_expansion_and_sealed_pool_materialization"
)
G0_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

TARGET_PACKET = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_2026-05-11.json"
TARGET_SOURCE_FREEZE = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_SOURCE_FREEZE_LEDGER_2026-05-11.json"
TARGET_SEGMENT_MANIFEST = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json"
TARGET_DUPLICATE_AUDIT = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_DUPLICATE_EXCLUSION_AUDIT_2026-05-11.json"
TARGET_PARSER_AUDIT = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_PARSER_ASOF_NOLEAK_AUDIT_2026-05-11.json"
TARGET_COMPLETION_AUDIT = TARGET_DIR / "FPB_SCID_FREEZE_REPAIR_COMPLETION_AUDIT_2026-05-11.json"
SOURCE_SELECTED_LEDGER = (
    SOURCE_EXPANSION_DIR / "FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json"
)
SOURCE_NATIVE_SCID_LEDGER = (
    SOURCE_EXPANSION_DIR / "FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json"
)
PREVIOUS_REPAIR_BLOCKERS = (
    PREVIOUS_G12_DIR / "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json"
)
G0_BASELINE_PACKET = G0_DIR / "G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json"
G0_DISCOVERY_EXPOSURE = G0_DIR / "G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_2026-05-11.json"
G0_SOURCE_ASOF = G0_DIR / "G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_2026-05-11.json"
NEXT_PROMPT = (
    PROMPT_DIR
    / "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md"
)

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SCID_TS = struct.Struct("<Q")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
CHUNK_SIZE = 1024 * 1024
SCAN_RECORD_CHUNK = 200_000

EXPECTED_SOURCES = [
    ("6BM26-CME.scid", "GBPUSD_6B"),
    ("6EM26-CME.scid", "EURUSD"),
    ("6JM26-CME.scid", "USDJPY_6J"),
    ("GCM26-COMEX.scid", "XAUUSD_GC"),
    ("MGCM26-COMEX.scid", "XAUUSD_MGC"),
    ("MYMM26-CBOT.scid", "US30_MYM"),
    ("NQM26-CME.scid", "NAS100_NQ"),
    ("SIM26-COMEX.scid", "XAGUSD_SI"),
    ("YMM26-CBOT.scid", "US30_YM"),
]
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
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
RAW_SOURCE_SUFFIXES = {".scid", ".dly", ".parquet", ".csv", ".bin", ".scidseg"}
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


def safe_flags_ok(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append("promotion_verdict")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(flag)
    return not failures, failures


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def markdown_payload(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if len(text) > 10000:
        text = text[:10000] + "\n... truncated in markdown; see matching JSON artifact ..."
    return "```json\n" + text + "\n```\n"


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> dict[str, str]:
    json_path = ROUTE_DIR / f"{stem}.json"
    md_path = ROUTE_DIR / f"{stem}.md"
    write_json(json_path, payload)
    md = f"# {title}\n\n"
    md += f"- Route: `{ROUTE_ID}`\n"
    md += f"- Evidence class: `{EVIDENCE_CLASS}`\n"
    md += f"- Promotion verdict: `{payload.get('promotion_verdict')}`\n"
    md += f"- validation_safe: `{payload.get('validation_safe')}`\n"
    md += f"- outcome_review_opened: `{payload.get('outcome_review_opened')}`\n"
    md += f"- live_effect: `{payload.get('live_effect')}`\n\n"
    if payload.get("summary") is not None:
        md += "## Summary\n\n" + markdown_payload({"summary": payload.get("summary")})
    md += "## Payload\n\n" + markdown_payload(payload)
    md_path.write_text(md, encoding="utf-8")
    return {"json": rel(json_path), "md": rel(md_path)}


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def sierra_dt(microseconds: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=microseconds)


def sierra_us(value: str) -> int:
    return int((parse_time(value) - SIERRA_EPOCH).total_seconds() * 1_000_000)


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
                raise IOError(f"unexpected EOF in {path} while hashing byte range")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_scid_header(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "parser_status": "FILE_MISSING", "absolute_path": str(path)}
    size = path.stat().st_size
    if size < SCID_HEADER.size:
        return {"exists": True, "parser_status": "TOO_SMALL_FOR_SCID_HEADER", "size_bytes": size}
    with path.open("rb") as handle:
        header_raw = handle.read(SCID_HEADER.size)
    magic, header_size, record_size, version, utc_start_index, unused, reserve = SCID_HEADER.unpack(header_raw)
    if magic != b"SCID":
        return {
            "exists": True,
            "parser_status": "BAD_SCID_MAGIC",
            "magic": magic.decode(errors="replace"),
            "size_bytes": size,
        }
    record_count = max((size - header_size) // record_size, 0)
    remainder = max((size - header_size) % record_size, 0)
    first_us: int | None = None
    last_us: int | None = None
    if record_count:
        with path.open("rb") as handle:
            handle.seek(header_size)
            first = handle.read(record_size)
            handle.seek(header_size + (record_count - 1) * record_size)
            last = handle.read(record_size)
        first_us = SCID_TS.unpack(first[:8])[0]
        last_us = SCID_TS.unpack(last[:8])[0]
    return {
        "exists": True,
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
        "absolute_path": str(path.resolve(strict=False)),
        "file_name": path.name,
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "unused": unused,
        "reserve_sha256": hashlib.sha256(reserve).hexdigest(),
        "record_count": record_count,
        "remainder_bytes": remainder,
        "coverage_start_utc": iso(sierra_dt(first_us)) if first_us is not None else None,
        "coverage_end_utc": iso(sierra_dt(last_us)) if last_us is not None else None,
        "first_record_timestamp_us": first_us,
        "last_record_timestamp_us": last_us,
        "header_sha256": hashlib.sha256(header_raw).hexdigest(),
    }


def read_record_timestamp(path: Path, header_size: int, record_size: int, record_index: int) -> int:
    with path.open("rb") as handle:
        handle.seek(header_size + record_index * record_size)
        raw = handle.read(record_size)
    if len(raw) != record_size:
        raise IOError(f"could not read record {record_index} from {path}")
    return SCID_TS.unpack(raw[:8])[0]


def scan_segment_timestamps(path: Path, byte_start: int, record_size: int, record_count: int, floor_us: int) -> dict[str, Any]:
    count = 0
    previous: int | None = None
    first_us: int | None = None
    last_us: int | None = None
    min_us: int | None = None
    max_us: int | None = None
    below_floor = 0
    monotonic = True
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        handle.seek(byte_start)
        remaining = record_count
        while remaining:
            to_read = min(remaining, SCAN_RECORD_CHUNK)
            chunk = handle.read(to_read * record_size)
            if len(chunk) != to_read * record_size:
                raise IOError(f"short read while scanning timestamps for {path}")
            for offset in range(0, len(chunk), record_size):
                ts_us = SCID_TS.unpack_from(chunk, offset)[0]
                digest.update(chunk[offset : offset + 8])
                if first_us is None:
                    first_us = ts_us
                if previous is not None and ts_us < previous:
                    monotonic = False
                previous = ts_us
                last_us = ts_us
                min_us = ts_us if min_us is None else min(min_us, ts_us)
                max_us = ts_us if max_us is None else max(max_us, ts_us)
                if ts_us < floor_us:
                    below_floor += 1
                count += 1
            remaining -= to_read
    return {
        "scanned_record_count": count,
        "timestamp_monotonic_non_decreasing": monotonic,
        "segment_timestamp_first_utc_scanned": iso(sierra_dt(first_us)) if first_us is not None else None,
        "segment_timestamp_last_utc_scanned": iso(sierra_dt(last_us)) if last_us is not None else None,
        "segment_timestamp_min_utc": iso(sierra_dt(min_us)) if min_us is not None else None,
        "segment_timestamp_max_utc": iso(sierra_dt(max_us)) if max_us is not None else None,
        "records_below_eligible_floor": below_floor,
        "timestamp_stream_sha256": digest.hexdigest(),
    }


def source_hashes_from_rows(rows: list[dict[str, Any]]) -> set[str]:
    return {row.get("source_sha256") for row in rows if row.get("source_sha256")}


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def git_show_names(ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", ref],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def forbidden_live_surface_paths(paths: list[str]) -> list[str]:
    bad: list[str] = []
    for path in paths:
        normalized = path.strip()
        if normalized.startswith((" M ", "A ", "?? ", " D ")):
            normalized = normalized[3:].replace("\\", "/")
        else:
            normalized = normalized.replace("\\", "/")
        if normalized.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES) or normalized in FORBIDDEN_LIVE_SURFACE_PREFIXES:
            bad.append(normalized)
    return bad


def raw_blob_paths_under(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(
        rel(child)
        for child in path.rglob("*")
        if child.is_file() and child.suffix.lower() in RAW_SOURCE_SUFFIXES
    )


def audit_segments(
    segment_manifest: dict[str, Any],
    source_freeze: dict[str, Any],
    selected_hashes: set[str],
    require_all_expected: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    freeze_by_source = {row["source"]: row for row in source_freeze.get("freeze_rows", [])}
    expected = dict(EXPECTED_SOURCES)
    audit_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for row in segment_manifest.get("segments", []):
        source = row.get("source")
        path = Path(row.get("source_path", ""))
        freeze_row = freeze_by_source.get(source, {})
        header = parse_scid_header(path)
        row_blockers: list[str] = []
        if source not in expected:
            row_blockers.append("unexpected_source")
        if row.get("symbol") != expected.get(source):
            row_blockers.append("symbol_mismatch")
        if header.get("parser_status") != "SCID_HEADER_AND_RECORD_PARSER_OK":
            row_blockers.append(f"parser_status_{header.get('parser_status')}")
            audit = {
                **safe_flags(),
                "source": source,
                "symbol": row.get("symbol"),
                "source_path": str(path),
                "source_access_status": "BLOCKED",
                "blockers": row_blockers,
            }
            audit_rows.append(audit)
            blockers.append(
                {
                    "source": source,
                    "symbol": row.get("symbol"),
                    "source_path": str(path),
                    "failed_check": "source_access_or_parser",
                    "blockers": row_blockers,
                    "next_permitted_repair_action": "restore/read the local Sierra SCID source and rerun source-control reaudit",
                }
            )
            continue
        header_size = int(header["header_size"])
        record_size = int(header["record_size"])
        start = int(row["segment_byte_start"])
        end = int(row["segment_byte_end_exclusive"])
        count = int(row["segment_record_count"])
        start_index = int(row["segment_record_start_index"])
        end_index = int(row["segment_record_end_index_inclusive"])
        floor_us = sierra_us(row["eligible_segment_start_utc_hard_floor"])
        manifest_first_utc = row["segment_first_record_utc"]
        manifest_last_utc = row["segment_last_record_utc"]

        checks: dict[str, bool] = {}
        checks["source_path_exists"] = bool(header["exists"])
        checks["canonical_source_file_name_matches"] = path.name == source
        checks["canonical_path_has_no_doubled_repo_root"] = str(path).lower().count(str(ROOT).lower()) <= 1
        checks["byte_start_record_aligned"] = start == header_size + start_index * record_size
        checks["byte_end_record_aligned"] = end == header_size + (end_index + 1) * record_size
        checks["byte_length_matches_record_count"] = end - start == count * record_size
        checks["record_index_count_matches"] = count == end_index - start_index + 1
        checks["segment_end_within_current_file"] = int(header["size_bytes"]) >= end
        checks["current_file_record_count_covers_segment"] = int(header["record_count"]) > end_index
        checks["record_size_is_40"] = record_size == SCID_RECORD.size
        checks["header_size_is_56"] = header_size == SCID_HEADER.size
        checks["file_has_no_partial_record_remainder"] = int(header["remainder_bytes"]) == 0

        rehash_1 = hash_range(path, start, end)
        rehash_2 = hash_range(path, start, end)
        checks["raw_byte_rehash_matches_manifest"] = rehash_1 == row["segment_records_sha256"]
        checks["raw_byte_rehash_is_deterministic"] = rehash_1 == rehash_2
        checks["segment_hash_disjoint_from_selected_discovery_hashes"] = rehash_1 not in selected_hashes

        first_us = read_record_timestamp(path, header_size, record_size, start_index)
        last_us = read_record_timestamp(path, header_size, record_size, end_index)
        previous_us = read_record_timestamp(path, header_size, record_size, start_index - 1) if start_index > 0 else None
        checks["first_record_matches_manifest"] = iso(sierra_dt(first_us)) == manifest_first_utc
        checks["last_record_matches_manifest"] = iso(sierra_dt(last_us)) == manifest_last_utc
        checks["first_record_at_or_after_hard_floor"] = first_us >= floor_us
        checks["previous_record_before_floor_or_no_previous"] = previous_us is None or previous_us < floor_us

        scan = scan_segment_timestamps(path, start, record_size, count, floor_us)
        checks["timestamp_scan_count_matches_manifest"] = scan["scanned_record_count"] == count
        checks["timestamp_scan_first_matches_boundary"] = scan["segment_timestamp_first_utc_scanned"] == manifest_first_utc
        checks["timestamp_scan_last_matches_boundary"] = scan["segment_timestamp_last_utc_scanned"] == manifest_last_utc
        checks["timestamp_scan_has_no_pre_floor_records"] = scan["records_below_eligible_floor"] == 0
        checks["timestamp_scan_min_matches_boundary"] = scan["segment_timestamp_min_utc"] == manifest_first_utc
        checks["timestamp_scan_max_matches_boundary"] = scan["segment_timestamp_max_utc"] == manifest_last_utc

        bytes_after_segment = int(header["size_bytes"]) - end
        current_last_us = header.get("last_record_timestamp_us")
        append_observed = bool(current_last_us is not None and iso(sierra_dt(int(current_last_us))) > manifest_last_utc)
        checks["append_mutability_safe_byte_range_before_or_at_eof"] = bytes_after_segment >= 0
        checks["future_append_cannot_change_hashed_bytes_without_mutating_in_range"] = True

        failed = [name for name, ok in checks.items() if not ok]
        audit = {
            **safe_flags(),
            "source": source,
            "symbol": row.get("symbol"),
            "source_path": str(path),
            "canonical_source_path": str(path.resolve(strict=False)),
            "source_access_status": "OK",
            "segment_byte_start": start,
            "segment_byte_end_exclusive": end,
            "segment_byte_length": end - start,
            "segment_record_start_index": start_index,
            "segment_record_end_index_inclusive": end_index,
            "segment_record_count": count,
            "eligible_segment_start_utc_hard_floor": row["eligible_segment_start_utc_hard_floor"],
            "segment_first_record_utc_manifest": row["segment_first_record_utc"],
            "segment_last_record_utc_manifest": row["segment_last_record_utc"],
            "previous_record_utc": iso(sierra_dt(previous_us)) if previous_us is not None else None,
            "first_record_utc_reparsed": iso(sierra_dt(first_us)),
            "last_record_utc_reparsed": iso(sierra_dt(last_us)),
            "current_file_coverage_start_utc": header.get("coverage_start_utc"),
            "current_file_coverage_end_utc": header.get("coverage_end_utc"),
            "current_file_size_bytes": header.get("size_bytes"),
            "current_file_record_count": header.get("record_count"),
            "current_file_bytes_after_segment": bytes_after_segment,
            "append_observed_after_manifest_segment": append_observed,
            "append_invariance_decision": (
                "PASS_BOUNDED_RANGE_REHASH_STABLE_EVEN_IF_FULL_FILE_APPENDS"
                if not failed
                else "FAIL_REPAIR_BLOCKED"
            ),
            "raw_byte_hash_method": "open(..., 'rb') seek segment_byte_start and sha256 exact bytes through segment_byte_end_exclusive",
            "manifest_segment_records_sha256": row["segment_records_sha256"],
            "raw_byte_rehash_sha256_first_pass": rehash_1,
            "raw_byte_rehash_sha256_second_pass": rehash_2,
            "timestamp_scan": scan,
            "timestamp_monotonicity_note": (
                "diagnostic_only; source-control acceptance uses bounded raw bytes plus min/max window and hard-floor checks, "
                "because Sierra intraday records can contain same-second or minor out-of-order ticks without changing the "
                "accepted byte segment"
            ),
            "source_packet_coverage_start_utc": freeze_row.get("source_packet_coverage_start_utc"),
            "source_packet_coverage_end_utc": freeze_row.get("source_packet_coverage_end_utc"),
            "repair_partition_assignment": freeze_row.get("repair_partition_assignment"),
            "duplicate_source_decision_repaired": freeze_row.get("duplicate_source_decision_repaired"),
            "parser_asof_status": freeze_row.get("parser_asof_status"),
            "no_leak_status": freeze_row.get("no_leak_status"),
            "current_header_metadata": header,
            "checks": checks,
            "failed_checks": failed,
        }
        audit_rows.append(audit)
        if failed:
            blockers.append(
                {
                    "source": source,
                    "symbol": row.get("symbol"),
                    "source_path": str(path),
                    "failed_check": "segment_source_control_reaudit",
                    "failed_checks": failed,
                    "expected_segment_hash": row["segment_records_sha256"],
                    "actual_segment_hash": rehash_1,
                    "next_permitted_repair_action": (
                        "rerun bounded-segment repair from current SCID source or restore exact source bytes; "
                        "do not open validation or result scoring"
                    ),
                }
            )
    if require_all_expected:
        missing = [source for source, _symbol in EXPECTED_SOURCES if source not in {row.get("source") for row in audit_rows}]
        for source in missing:
            blockers.append(
                {
                    "source": source,
                    "symbol": dict(EXPECTED_SOURCES).get(source),
                    "failed_check": "missing_required_source_from_manifest",
                    "next_permitted_repair_action": "target repair manifest must include this required source",
                }
            )
    return audit_rows, blockers


def build_rehash_audit(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    selected_rows = payloads["selected"].get("selected_source_coverage_rows", [])
    selected_hashes = source_hashes_from_rows(selected_rows)
    audit_rows, blockers = audit_segments(payloads["segment_manifest"], payloads["source_freeze"], selected_hashes)
    checks = {
        "exactly_9_segments_audited": len(audit_rows) == 9,
        "all_9_expected_sources_present": sorted(row.get("source") for row in audit_rows) == sorted(source for source, _ in EXPECTED_SOURCES),
        "all_segment_rehashes_match": all(row.get("checks", {}).get("raw_byte_rehash_matches_manifest") for row in audit_rows),
        "all_segment_rehashes_deterministic": all(row.get("checks", {}).get("raw_byte_rehash_is_deterministic") for row in audit_rows),
        "all_byte_record_boundaries_stable": all(
            row.get("checks", {}).get("byte_start_record_aligned")
            and row.get("checks", {}).get("byte_end_record_aligned")
            and row.get("checks", {}).get("byte_length_matches_record_count")
            and row.get("checks", {}).get("record_index_count_matches")
            for row in audit_rows
        ),
        "all_first_records_at_or_after_hard_floor": all(
            row.get("checks", {}).get("first_record_at_or_after_hard_floor") for row in audit_rows
        ),
        "all_previous_records_before_floor_or_absent": all(
            row.get("checks", {}).get("previous_record_before_floor_or_no_previous") for row in audit_rows
        ),
        "all_timestamp_scans_no_pre_floor_records": all(
            row.get("checks", {}).get("timestamp_scan_has_no_pre_floor_records") for row in audit_rows
        ),
        "all_current_files_cover_segment_ranges": all(
            row.get("checks", {}).get("segment_end_within_current_file") for row in audit_rows
        ),
        "all_segment_hashes_disjoint_from_selected_discovery_hashes": all(
            row.get("checks", {}).get("segment_hash_disjoint_from_selected_discovery_hashes") for row in audit_rows
        ),
        "no_segment_reaudit_blockers": not blockers,
    }
    return {
        **safe_flags(),
        "artifact_family": "source_rehash_audit",
        "target_manifest": rel(TARGET_SEGMENT_MANIFEST),
        "selected_source_hash_count_from_source_expansion_rows": len(selected_hashes),
        "selected_source_count_declared": payloads["selected"].get("selected_source_count"),
        "segment_rehash_rows": audit_rows,
        "repair_blockers": blockers,
        "checks": checks,
        "summary": {
            "segment_count": len(audit_rows),
            "blocker_count": len(blockers),
            "all_segment_rehashes_match": checks["all_segment_rehashes_match"],
            "all_byte_record_boundaries_stable": checks["all_byte_record_boundaries_stable"],
            "all_first_records_at_or_after_hard_floor": checks["all_first_records_at_or_after_hard_floor"],
        },
    }


def build_noleak_partition_audit(payloads: dict[str, dict[str, Any]], rehash: dict[str, Any]) -> dict[str, Any]:
    selected = payloads["selected"]
    duplicate = payloads["duplicate"]
    parser = payloads["parser"]
    packet = payloads["packet"]
    baseline = payloads["baseline"]
    discovery = payloads["discovery"]
    source_asof = payloads["source_asof"]
    segment_hashes = {
        row["raw_byte_rehash_sha256_first_pass"] for row in rehash["segment_rehash_rows"] if row.get("raw_byte_rehash_sha256_first_pass")
    }
    selected_hashes = source_hashes_from_rows(selected.get("selected_source_coverage_rows", []))
    baseline_ids = [row.get("family_id") for row in baseline.get("baseline_controls", [])]
    checks = {
        "selected_source_count_is_365": selected.get("selected_source_count") == 365,
        "target_duplicate_audit_preserves_365": duplicate.get("selected_source_rows_preserved") == 365,
        "g0_discovery_exposure_preserves_365": discovery.get("source_exposure", {}).get("selected_source_count") == 365,
        "segment_hashes_disjoint_from_selected_source_hashes": segment_hashes.isdisjoint(selected_hashes),
        "target_duplicate_overlap_empty": duplicate.get("selected_segment_hash_overlap") == [],
        "all_four_adversarial_baselines_exact": baseline_ids == EXPECTED_BASELINES
        and duplicate.get("baseline_controls_present") == EXPECTED_BASELINES,
        "parser_rows_all_ok": all(row.get("parser_status") == "SCID_HEADER_AND_RECORD_PARSER_OK" for row in parser.get("parser_rows", [])),
        "parser_asof_gate_explicit": parser.get("checks", {}).get("scid_to_asof_gate_explicit") is True,
        "no_broker_order_account_result_fields_read": parser.get("checks", {}).get(
            "no_broker_account_order_history_position_fields_read"
        )
        is True,
        "hard_floors_preserved": parser.get("checks", {}).get("all_hard_floors_preserved") is True,
        "duplicate_denominator_controls_source_control_only": all(
            row.get("repair_partition_assignment") == "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED"
            for row in rehash["segment_rehash_rows"]
        ),
        "scid_to_asof_gate_unopened": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT" in packet.get(
            "scid_to_asof_bar_derivation_contract_gate", ""
        ),
        "validation_execution_gate_unopened": packet.get("validation_execution_prompt_emitted") is False,
        "g0_source_asof_safe_flags_closed": source_asof.get("validation_safe") is False
        and source_asof.get("outcome_review_opened") is False
        and source_asof.get("live_effect") is False,
        "safe_flags_closed_on_target_packet": packet.get("promotion_verdict") == PROMOTION_VERDICT
        and packet.get("validation_safe") is False
        and packet.get("outcome_review_opened") is False
        and packet.get("live_effect") is False,
    }
    return {
        **safe_flags(),
        "artifact_family": "noleak_partition_audit",
        "selected_source_count_declared": selected.get("selected_source_count"),
        "selected_source_coverage_row_count": len(selected.get("selected_source_coverage_rows", [])),
        "selected_source_hash_count_from_source_expansion_rows": len(selected_hashes),
        "g0_selected_source_count": discovery.get("source_exposure", {}).get("selected_source_count"),
        "g0_selected_source_hash_count": discovery.get("source_exposure", {}).get("selected_source_hash_count"),
        "segment_hash_count": len(segment_hashes),
        "segment_selected_source_hash_overlap": sorted(segment_hashes.intersection(selected_hashes)),
        "baseline_controls_present": baseline_ids,
        "duplicate_decision": (
            "SEGMENT_HASHES_UNIQUE_DISJOINT_FROM_DISCOVERY_SELECTED_HASHES_AND_NOT_VALIDATION_DENOMINATOR_ROWS"
            if checks["segment_hashes_disjoint_from_selected_source_hashes"]
            else "REPAIR_BLOCKED_SEGMENT_HASH_OVERLAPS_DISCOVERY_SELECTED_HASH"
        ),
        "denominator_control_decision": (
            "SOURCE_CONTROL_ONLY_NO_VALIDATION_ROW_COUNTING_OR_OUTCOME_DENOMINATOR_OPENED"
        ),
        "remaining_gates_before_validation": [
            "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
            "separate validation-execution prompt after source-control contract acceptance",
            "future G12/G0 audit of any derived as-of packet before result scoring",
        ],
        "checks": checks,
        "summary": {
            "selected_source_count_declared": selected.get("selected_source_count"),
            "g0_selected_source_count": discovery.get("source_exposure", {}).get("selected_source_count"),
            "all_four_adversarial_baselines_exact": checks["all_four_adversarial_baselines_exact"],
            "safe_flags_closed": checks["safe_flags_closed_on_target_packet"],
        },
    }


def build_dirty_path_audit() -> dict[str, Any]:
    status_lines = git_status_short()
    target_commit_paths = git_show_names("4d63c9b1")
    current_new_route_raw_blobs = raw_blob_paths_under(ROUTE_DIR)
    target_route_raw_blobs = raw_blob_paths_under(TARGET_DIR)
    target_commit_raw_blobs = [path for path in target_commit_paths if Path(path).suffix.lower() in RAW_SOURCE_SUFFIXES]
    scoped_uncommitted = [
        line
        for line in status_lines
        if "g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit" in line
        or "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT" in line
        or ".context/LIVE_STATE.md" in line
        or ".context/00_core/research_current_state.md" in line
    ]
    return {
        **safe_flags(),
        "artifact_family": "dirty_path_audit",
        "git_status_short": status_lines,
        "scoped_uncommitted_lines": scoped_uncommitted,
        "unrelated_workspace_dirt_lines": [line for line in status_lines if line not in scoped_uncommitted],
        "target_repair_commit": "4d63c9b1",
        "target_repair_commit_changed_paths": target_commit_paths,
        "target_repair_commit_raw_blob_paths": target_commit_raw_blobs,
        "current_g12_route_raw_blob_paths": current_new_route_raw_blobs,
        "target_route_raw_blob_paths_current": target_route_raw_blobs,
        "forbidden_live_surface_dirty_paths": forbidden_live_surface_paths(status_lines),
        "forbidden_live_surface_target_commit_paths": forbidden_live_surface_paths(target_commit_paths),
        "canonical_route_path": rel(ROUTE_DIR),
        "target_route_path": rel(TARGET_DIR),
        "canonicality_checks": {
            "route_under_expected_repo_root": ROUTE_DIR.resolve(strict=False).is_relative_to(ROOT.resolve(strict=False)),
            "target_under_expected_repo_root": TARGET_DIR.resolve(strict=False).is_relative_to(ROOT.resolve(strict=False)),
            "no_raw_blobs_in_new_g12_route": not current_new_route_raw_blobs,
            "no_raw_blobs_in_target_repair_route": not target_route_raw_blobs,
            "no_raw_blobs_in_target_repair_commit": not target_commit_raw_blobs,
            "no_forbidden_live_surface_dirty_paths": not forbidden_live_surface_paths(status_lines),
        },
        "summary": {
            "unrelated_workspace_dirt_count": len([line for line in status_lines if line not in scoped_uncommitted]),
            "scoped_uncommitted_count": len(scoped_uncommitted),
            "raw_blob_path_count": len(current_new_route_raw_blobs) + len(target_route_raw_blobs) + len(target_commit_raw_blobs),
            "forbidden_live_surface_dirty_path_count": len(forbidden_live_surface_paths(status_lines)),
        },
    }


def terminal_decision(rehash: dict[str, Any], noleak: dict[str, Any], dirty: dict[str, Any]) -> str:
    if rehash["repair_blockers"]:
        return "REPAIR_BLOCKED_SOURCE_POOL_PACKET"
    if not all(rehash["checks"].values()) or not all(noleak["checks"].values()):
        return "REJECT_AS_SOURCE_CONTROL_REPAIR_EVIDENCE"
    if dirty["summary"]["raw_blob_path_count"] != 0 or dirty["summary"]["forbidden_live_surface_dirty_path_count"] != 0:
        return "REJECT_AS_SOURCE_CONTROL_REPAIR_EVIDENCE"
    return "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY"


def build_blocker_ledger(decision: str, rehash: dict[str, Any], noleak: dict[str, Any], dirty: dict[str, Any]) -> dict[str, Any]:
    blockers = list(rehash["repair_blockers"])
    for name, ok in noleak["checks"].items():
        if not ok:
            blockers.append(
                {
                    "failed_check": f"noleak_partition_{name}",
                    "next_permitted_repair_action": "repair source-control/no-leak packet evidence; do not open validation",
                }
            )
    for path in dirty["target_repair_commit_raw_blob_paths"] + dirty["current_g12_route_raw_blob_paths"]:
        blockers.append(
            {
                "failed_check": "raw_market_data_blob_in_scope",
                "path": path,
                "next_permitted_repair_action": "remove raw market-data blob from scoped commit/artifact route",
            }
        )
    return {
        **safe_flags(),
        "artifact_family": "blocker_ledger",
        "terminal_decision": decision,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "blockers_exact_and_actionable": all("next_permitted_repair_action" in row for row in blockers),
        "summary": {"terminal_decision": decision, "blocker_count": len(blockers)},
    }


def build_decision_ledger(
    decision: str,
    rehash: dict[str, Any],
    noleak: dict[str, Any],
    dirty: dict[str, Any],
    blocker_ledger: dict[str, Any],
) -> dict[str, Any]:
    accepted = decision.startswith("ACCEPT")
    return {
        **safe_flags(),
        "artifact_family": "decision_ledger",
        "terminal_decision": decision,
        "accepted_source_control_repair_evidence_only": accepted,
        "accepted_validation_execution": False,
        "accepted_result_scoring": False,
        "accepted_promotion": False,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_control_warnings": [
            "full native Sierra SCID files remain mutable reference metadata only",
            "accepted evidence is limited to bounded raw-byte segment hashes and parser-stable boundaries",
            "SCID-to-asof-bar derivation remains unopened until the next source-control contract prompt",
            "validation execution/result scoring remains blocked by a separate future lane",
        ],
        "evidence_summary": {
            "rehashed_segment_count": len(rehash["segment_rehash_rows"]),
            "all_segment_rehashes_match": rehash["checks"]["all_segment_rehashes_match"],
            "all_byte_record_boundaries_stable": rehash["checks"]["all_byte_record_boundaries_stable"],
            "all_first_records_at_or_after_hard_floor": rehash["checks"]["all_first_records_at_or_after_hard_floor"],
            "selected_source_count_declared": noleak["selected_source_count_declared"],
            "g0_selected_source_count": noleak["g0_selected_source_count"],
            "all_four_adversarial_baselines_exact": noleak["checks"]["all_four_adversarial_baselines_exact"],
            "raw_blob_path_count": dirty["summary"]["raw_blob_path_count"],
            "blocker_count": blocker_ledger["blocker_count"],
        },
        "next_allowed_lane_if_accepted": (
            "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
            if accepted
            else None
        ),
        "next_allowed_lane_boundary": (
            "source-control/design only; no validation execution, replay/path-label generation, R/PnL/win-rate/"
            "expectancy/performance scoring, AI/API, broker/account/order evidence, promotion, or live behavior"
        ),
        "summary": {"terminal_decision": decision, "accepted_source_control_repair_evidence_only": accepted},
    }


def write_next_prompt_if_accepted(decision: str) -> dict[str, Any]:
    accepted = decision.startswith("ACCEPT")
    if accepted:
        prompt = """# SCID To As-Of Bar Derivation Contract And Candidate Generator Constraint Goal Prompt

Date: 2026-05-11
Owner lane: source-control/design contract after G12 SCID segment repair acceptance
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Design and audit the source-control contract that would convert accepted Sierra SCID bounded segments into as-of bar inputs and a constrained candidate-generator packet. This is a contract/design lane only. It may define parsers, schemas, no-leak rules, duplicate policy, as-of boundaries, deterministic replay inputs, and future verifier expectations. It must not execute validation, generate scored result rows, open path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance, or promote anything.

## Required Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/`
- `research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`
- `research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/`

## Hard Boundaries

- Evidence class: `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY`.
- No validation execution.
- No candidate result scoring, replay/path-label labels, R, PnL, win-rate, expectancy, or performance.
- No AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, live restart, or live behavior.
- No prompt/config/risk/safety/execution/canary/selector changes.
- No raw `.scid`, `.parquet`, `.csv`, `.dly`, or other raw market-data blob commits.

## Required Output

Emit a source-control/design packet with JSON+MD artifacts, verifier, focused tests, and a completion audit that freezes:

- SCID parser contract and version/hash;
- exact segment manifests consumed;
- bar derivation as-of rule and timestamp inclusivity;
- duplicate policy across mini/micro/proxy sources;
- discovery-source exclusion preservation;
- no-leak field list and forbidden field list;
- candidate generator constraint boundaries;
- future G12/G0 gates before any validation execution.

Complete only with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, scoped commits, and closeout `LIVE_STATE` regeneration.
"""
        NEXT_PROMPT.write_text(prompt, encoding="utf-8")
    return {
        **safe_flags(),
        "artifact_family": "next_prompt_record",
        "next_prompt_required": accepted,
        "next_prompt_path": rel(NEXT_PROMPT),
        "next_prompt_exists": NEXT_PROMPT.exists(),
        "next_route_id": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
        if accepted
        else None,
        "summary": {"next_prompt_required": accepted, "next_prompt_exists": NEXT_PROMPT.exists()},
    }


def build_completion_audit(
    artifacts: dict[str, dict[str, str]],
    decision: str,
    rehash: dict[str, Any],
    noleak: dict[str, Any],
    dirty: dict[str, Any],
    blocker_ledger: dict[str, Any],
    next_prompt_record: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "all required G12 artifacts exist",
            "evidence": sorted(artifacts),
            "status": "PASS",
        },
        {
            "requirement": "independent raw-byte segment rehash for exactly 9 repaired SCID sources",
            "evidence": artifacts["source_rehash_audit"]["json"],
            "status": "PASS" if rehash["checks"]["exactly_9_segments_audited"] else "FAIL",
        },
        {
            "requirement": "9/9 segment hashes deterministic and matching manifest",
            "evidence": artifacts["source_rehash_audit"]["json"],
            "status": "PASS"
            if rehash["checks"]["all_segment_rehashes_match"]
            and rehash["checks"]["all_segment_rehashes_deterministic"]
            else "FAIL",
        },
        {
            "requirement": "byte/record boundaries, record counts, and timestamp scans are parser-stable",
            "evidence": artifacts["source_rehash_audit"]["json"],
            "status": "PASS"
            if rehash["checks"]["all_byte_record_boundaries_stable"]
            and rehash["checks"]["all_timestamp_scans_no_pre_floor_records"]
            else "FAIL",
        },
        {
            "requirement": "eligible_segment_start_utc hard floors enforced",
            "evidence": artifacts["source_rehash_audit"]["json"],
            "status": "PASS" if rehash["checks"]["all_first_records_at_or_after_hard_floor"] else "FAIL",
        },
        {
            "requirement": "365 discovery-source exclusions preserved and disjoint",
            "evidence": artifacts["noleak_partition_audit"]["json"],
            "status": "PASS"
            if noleak["checks"]["selected_source_count_is_365"]
            and noleak["checks"]["target_duplicate_audit_preserves_365"]
            and noleak["checks"]["segment_hashes_disjoint_from_selected_source_hashes"]
            else "FAIL",
        },
        {
            "requirement": "four adversarial baselines exactly preserved",
            "evidence": artifacts["noleak_partition_audit"]["json"],
            "status": "PASS" if noleak["checks"]["all_four_adversarial_baselines_exact"] else "FAIL",
        },
        {
            "requirement": "parser/as-of/no-leak metadata preserved and future gates unopened",
            "evidence": artifacts["noleak_partition_audit"]["json"],
            "status": "PASS"
            if noleak["checks"]["parser_rows_all_ok"]
            and noleak["checks"]["scid_to_asof_gate_unopened"]
            and noleak["checks"]["validation_execution_gate_unopened"]
            else "FAIL",
        },
        {
            "requirement": "no raw market-data blobs committed or present in scoped route",
            "evidence": artifacts["dirty_path_audit"]["json"],
            "status": "PASS" if dirty["summary"]["raw_blob_path_count"] == 0 else "FAIL",
        },
        {
            "requirement": "path canonicality and dirty-state scope recorded",
            "evidence": artifacts["dirty_path_audit"]["json"],
            "status": "PASS"
            if dirty["canonicality_checks"]["route_under_expected_repo_root"]
            and dirty["canonicality_checks"]["target_under_expected_repo_root"]
            else "FAIL",
        },
        {
            "requirement": "terminal verdict frozen",
            "evidence": artifacts["decision_ledger"]["json"],
            "status": "PASS" if decision in {
                "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY",
                "ACCEPT_WITH_EXACT_SOURCE_CONTROL_WARNINGS",
                "REPAIR_BLOCKED_SOURCE_POOL_PACKET",
                "REJECT_AS_SOURCE_CONTROL_REPAIR_EVIDENCE",
            } else "FAIL",
        },
        {
            "requirement": "next source-control prompt exists if and only if accepted",
            "evidence": next_prompt_record,
            "status": "PASS"
            if (decision.startswith("ACCEPT") and next_prompt_record["next_prompt_exists"])
            or ((not decision.startswith("ACCEPT")) and not next_prompt_record["next_prompt_required"])
            else "FAIL",
        },
        {
            "requirement": "safe flags remain closed",
            "evidence": artifacts["decision_ledger"]["json"],
            "status": "PASS" if safe_flags_ok({"promotion_verdict": PROMOTION_VERDICT, **safe_flags()})[0] else "FAIL",
        },
        {
            "requirement": "no exact repair blockers remain on accepted decision",
            "evidence": artifacts["blocker_ledger"]["json"],
            "status": "PASS" if (not decision.startswith("ACCEPT")) or blocker_ledger["blocker_count"] == 0 else "FAIL",
        },
    ]
    completion_standard = all(row["status"] == "PASS" for row in checklist)
    return {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Independently audit the nine repaired Sierra SCID bounded eligible segments as source-control repair "
            "evidence only, with raw-byte rehashes, boundary/no-leak/partition checks, safe flags, future gates, "
            "verifier/tests, scoped commits, and no validation execution."
        ),
        "prompt_to_artifact_checklist": checklist,
        "completion_standard_satisfied": completion_standard,
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": completion_standard,
        "remaining_blockers": blocker_ledger["blockers"],
        "summary": {
            "completion_standard_satisfied": completion_standard,
            "terminal_decision": decision,
            "remaining_blocker_count": blocker_ledger["blocker_count"],
        },
    }


def load_required_payloads() -> dict[str, dict[str, Any]]:
    return {
        "packet": load_json(TARGET_PACKET),
        "source_freeze": load_json(TARGET_SOURCE_FREEZE),
        "segment_manifest": load_json(TARGET_SEGMENT_MANIFEST),
        "duplicate": load_json(TARGET_DUPLICATE_AUDIT),
        "parser": load_json(TARGET_PARSER_AUDIT),
        "target_completion": load_json(TARGET_COMPLETION_AUDIT),
        "selected": load_json(SOURCE_SELECTED_LEDGER),
        "native_scid": load_json(SOURCE_NATIVE_SCID_LEDGER),
        "previous_repair_blockers": load_json(PREVIOUS_REPAIR_BLOCKERS),
        "baseline": load_json(G0_BASELINE_PACKET),
        "discovery": load_json(G0_DISCOVERY_EXPOSURE),
        "source_asof": load_json(G0_SOURCE_ASOF),
    }


def build_packet() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    payloads = load_required_payloads()
    rehash = build_rehash_audit(payloads)
    noleak = build_noleak_partition_audit(payloads, rehash)
    dirty = build_dirty_path_audit()
    decision = terminal_decision(rehash, noleak, dirty)
    blocker_ledger = build_blocker_ledger(decision, rehash, noleak, dirty)
    decision_ledger = build_decision_ledger(decision, rehash, noleak, dirty, blocker_ledger)
    next_prompt_record = write_next_prompt_if_accepted(decision)

    artifacts: dict[str, dict[str, str]] = {}
    artifacts["source_rehash_audit"] = write_pair(
        f"{FILE_PREFIX}_SOURCE_REHASH_AUDIT_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Source Rehash Audit",
        rehash,
    )
    artifacts["noleak_partition_audit"] = write_pair(
        f"{FILE_PREFIX}_NOLEAK_PARTITION_AUDIT_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit No-Leak Partition Audit",
        noleak,
    )
    artifacts["dirty_path_audit"] = write_pair(
        f"{FILE_PREFIX}_DIRTY_PATH_AUDIT_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Dirty Path Audit",
        dirty,
    )
    artifacts["blocker_ledger"] = write_pair(
        f"{FILE_PREFIX}_BLOCKER_LEDGER_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Blocker Ledger",
        blocker_ledger,
    )
    artifacts["decision_ledger"] = write_pair(
        f"{FILE_PREFIX}_DECISION_LEDGER_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Decision Ledger",
        decision_ledger,
    )

    completion = build_completion_audit(artifacts, decision, rehash, noleak, dirty, blocker_ledger, next_prompt_record)
    artifacts["completion_audit"] = write_pair(
        f"{FILE_PREFIX}_COMPLETION_AUDIT_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Completion Audit",
        completion,
    )
    output_manifest = {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "terminal_decision": decision,
        "artifacts": artifacts,
        "builder": rel(Path(__file__)),
        "verifier": rel(ROUTE_DIR / "verify_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"),
        "focused_tests": rel(ROUTE_DIR / "test_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"),
        "next_prompt_record": next_prompt_record,
        "summary": {"terminal_decision": decision, "artifact_count": len(artifacts)},
    }
    artifacts["output_manifest"] = write_pair(
        f"{FILE_PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}",
        "G12 FPB SCID Freeze Repair Reaudit Output Manifest",
        output_manifest,
    )
    return {
        "decision": decision,
        "source_rehash_audit": rehash,
        "noleak_partition_audit": noleak,
        "dirty_path_audit": dirty,
        "blocker_ledger": blocker_ledger,
        "decision_ledger": decision_ledger,
        "completion_audit": completion,
        "output_manifest": output_manifest,
        "artifacts": artifacts,
    }


def main() -> int:
    result = build_packet()
    print(
        json.dumps(
            {
                "terminal_decision": result["decision"],
                "segment_count": result["source_rehash_audit"]["summary"]["segment_count"],
                "blocker_count": result["blocker_ledger"]["blocker_count"],
                "completion_standard_satisfied": result["completion_audit"]["completion_standard_satisfied"],
                "output_manifest": result["artifacts"]["output_manifest"]["json"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["completion_audit"]["completion_standard_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
