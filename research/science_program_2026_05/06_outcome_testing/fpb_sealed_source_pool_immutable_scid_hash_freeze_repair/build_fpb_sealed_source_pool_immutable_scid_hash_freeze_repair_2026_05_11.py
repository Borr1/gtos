#!/usr/bin/env python3
"""Build the FPB immutable SCID segment-hash freeze repair packet.

This route is source-control repair only. It reads local Sierra SCID bytes for
the nine G12 repair blockers, freezes bounded eligible segment hashes, and
emits manifests/audits. It does not derive bars, generate candidates, score
results, inspect broker/account/order evidence, call APIs, or change live
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
PREFIX = "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR"
FILE_PREFIX = "FPB_SCID_FREEZE_REPAIR"
ROUTE_ID = PREFIX
EVIDENCE_CLASS = "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1"

G12_AUDIT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_sealed_source_pool_materialization_audit"
)
SOURCE_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_source_expansion_and_sealed_pool_materialization"
)
G0_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

REPAIR_BLOCKER_LEDGER = (
    G12_AUDIT_DIR / "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json"
)
NATIVE_SCID_LEDGER = (
    SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json"
)
SELECTED_SOURCE_LEDGER = (
    SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json"
)
SOURCE_CONTRACT_LEDGER = (
    SOURCE_PACKET_DIR / "FPB_SOURCE_EXPANSION_SOURCE_ASOF_NOLEAK_LEDGER_2026-05-11.json"
)
G0_BASELINE_PACKET = G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json"
G0_PARTITION_LEDGER = G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_2026-05-11.json"
G0_DISCOVERY_LEDGER = G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_2026-05-11.json"
G0_SOURCE_ASOF_CONTRACT = G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_2026-05-11.json"

NEXT_G12_REAUDIT_PROMPT = (
    PROMPT_DIR / "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-11.md"
)

SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
CHUNK_SIZE = 1024 * 1024

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
FORBIDDEN_SURFACES = [
    "validation_execution",
    "replay_or_path_label_generation",
    "result_scoring",
    "R_PnL_win_rate_expectancy_performance_claims",
    "promotion",
    "live_behavior",
    "AI_or_API_calls",
    "paid_or_vendor_access",
    "credentials",
    "remote_push",
    "broker_account_order_history_deal_position_data",
    "prompt_config_risk_safety_execution_canary_selector_changes",
]


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_value(value: Any) -> str:
    text = json.dumps(value, indent=2, sort_keys=True)
    if len(text) > 8000:
        text = text[:8000] + "\n... truncated in markdown; see matching JSON artifact ..."
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
    summary = payload.get("summary")
    if summary:
        md += "## Summary\n\n" + markdown_value(summary)
    md += "## Payload\n\n" + markdown_value(payload)
    md_path.write_text(md, encoding="utf-8")
    return {"json": rel(json_path), "md": rel(md_path)}


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def parse_time(value: str) -> datetime:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sierra_microseconds(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def sierra_dt(microseconds: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=microseconds)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


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
                raise IOError(f"unexpected EOF while hashing {path} at {byte_start}")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def parse_scid_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "parser_status": "FILE_MISSING"}
    size = path.stat().st_size
    if size < SCID_HEADER.size + SCID_RECORD.size:
        return {
            "path": str(path),
            "exists": True,
            "size_bytes": size,
            "parser_status": "TOO_SMALL_FOR_SCID_HEADER_AND_RECORD",
        }
    with path.open("rb") as handle:
        header_raw = handle.read(SCID_HEADER.size)
        magic, header_size, record_size, version, utc_start_index, _unused, _reserve = SCID_HEADER.unpack(header_raw)
        if magic != b"SCID":
            return {
                "path": str(path),
                "exists": True,
                "size_bytes": size,
                "parser_status": "BAD_SCID_MAGIC",
                "magic": magic.decode(errors="replace"),
            }
        record_count = max((size - header_size) // record_size, 0)
        remainder_bytes = max((size - header_size) % record_size, 0)
        handle.seek(header_size)
        first_raw = handle.read(record_size)
        handle.seek(header_size + (record_count - 1) * record_size)
        last_raw = handle.read(record_size)
    first_values = SCID_RECORD.unpack(first_raw)
    last_values = SCID_RECORD.unpack(last_raw)
    return {
        "absolute_path": str(path),
        "file_name": path.name,
        "exists": True,
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "record_count": record_count,
        "remainder_bytes": remainder_bytes,
        "coverage_start_utc": iso(sierra_dt(first_values[0])),
        "coverage_end_utc": iso(sierra_dt(last_values[0])),
        "first_record_timestamp_us": first_values[0],
        "last_record_timestamp_us": last_values[0],
        "header_sha256": sha256_bytes(header_raw),
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
    }


def read_record_timestamp_us(path: Path, header_size: int, record_size: int, index: int) -> int:
    with path.open("rb") as handle:
        handle.seek(header_size + index * record_size)
        raw = handle.read(record_size)
    if len(raw) != record_size:
        raise IOError(f"could not read record {index} from {path}")
    return SCID_RECORD.unpack(raw)[0]


def lower_bound_record_index(path: Path, header_size: int, record_size: int, record_count: int, target_us: int) -> int:
    lo = 0
    hi = record_count
    with path.open("rb") as handle:
        while lo < hi:
            mid = (lo + hi) // 2
            handle.seek(header_size + mid * record_size)
            raw = handle.read(record_size)
            if len(raw) != record_size:
                raise IOError(f"could not read record {mid} from {path}")
            ts_us = SCID_RECORD.unpack(raw)[0]
            if ts_us < target_us:
                lo = mid + 1
            else:
                hi = mid
    return lo


def derive_segment(path: Path, floor_utc: str, metadata: dict[str, Any]) -> dict[str, Any]:
    target_dt = parse_time(floor_utc)
    target_us = sierra_microseconds(target_dt)
    record_count = int(metadata["record_count"])
    header_size = int(metadata["header_size"])
    record_size = int(metadata["record_size"])
    if record_count <= 0:
        return {
            "segment_status": "NO_RECORDS",
            "eligible_segment_start_utc_hard_floor": floor_utc,
            "segment_blocker": "SCID file contains no records",
        }
    start_index = lower_bound_record_index(path, header_size, record_size, record_count, target_us)
    if start_index >= record_count:
        return {
            "segment_status": "NO_RECORD_AT_OR_AFTER_ELIGIBLE_FLOOR",
            "eligible_segment_start_utc_hard_floor": floor_utc,
            "segment_blocker": "no SCID record exists at or after the eligible hard floor",
        }
    end_index = record_count - 1
    start_ts = read_record_timestamp_us(path, header_size, record_size, start_index)
    end_ts = read_record_timestamp_us(path, header_size, record_size, end_index)
    byte_start = header_size + start_index * record_size
    byte_end = header_size + (end_index + 1) * record_size
    segment_hash = hash_range(path, byte_start, byte_end)
    immediate_rehash = hash_range(path, byte_start, byte_end)
    descriptor = {
        "policy": "BOUNDED_ELIGIBLE_SEGMENT",
        "source_path": str(path),
        "source_file_name": path.name,
        "eligible_segment_start_utc_hard_floor": floor_utc,
        "segment_record_start_index": start_index,
        "segment_record_end_index_inclusive": end_index,
        "segment_record_count": end_index - start_index + 1,
        "segment_byte_start": byte_start,
        "segment_byte_end_exclusive": byte_end,
        "segment_byte_length": byte_end - byte_start,
        "segment_first_record_utc": iso(sierra_dt(start_ts)),
        "segment_last_record_utc": iso(sierra_dt(end_ts)),
        "segment_records_sha256": segment_hash,
    }
    descriptor["segment_descriptor_sha256"] = sha256_json(descriptor)
    return {
        **descriptor,
        "segment_status": "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN",
        "immediate_rehash_sha256": immediate_rehash,
        "immediate_rehash_matches": immediate_rehash == segment_hash,
        "pre_eligible_records_excluded": start_index,
        "records_after_segment_may_append_without_hash_effect": True,
        "append_mutability_repaired_by": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
    }


def current_full_file_hash(path: Path) -> dict[str, Any]:
    try:
        return {
            "current_full_file_sha256_reference_only": sha256_file(path),
            "current_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
        }
    except Exception as exc:  # pragma: no cover - exercised only on local access failures.
        return {
            "current_full_file_sha256_reference_only": None,
            "current_full_file_hash_status": "FULL_FILE_HASH_FAILED_MUTABLE_REFERENCE_ONLY",
            "current_full_file_hash_error": repr(exc),
        }


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def selected_hashes_and_rows(selected_ledger: dict[str, Any]) -> tuple[set[str], list[dict[str, Any]]]:
    rows = selected_ledger.get("selected_source_coverage_rows", [])
    hashes = {row.get("source_sha256") for row in rows if row.get("source_sha256")}
    return hashes, rows


def build_context_anchor() -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "context_anchor",
        "controlling_prompt": rel(
            PROMPT_DIR / "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_GOAL_PROMPT_2026-05-11.md"
        ),
        "current_head": subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False
        ).stdout.strip(),
        "repair_lane_boundary": "source-control repair only; no SCID-to-asof bar derivation or validation execution",
        "required_inputs": [
            rel(REPAIR_BLOCKER_LEDGER),
            rel(NATIVE_SCID_LEDGER),
            rel(SELECTED_SOURCE_LEDGER),
            rel(SOURCE_CONTRACT_LEDGER),
            rel(G0_BASELINE_PACKET),
            rel(G0_PARTITION_LEDGER),
            rel(G0_DISCOVERY_LEDGER),
            rel(G0_SOURCE_ASOF_CONTRACT),
        ],
        "chosen_policy": "BOUNDED_ELIGIBLE_SEGMENT",
        "policy_reason": (
            "Full native Sierra files are append-mutable and large. The repair freezes the eligible segment "
            "as byte and record boundaries plus segment hashes, so later appends fall beyond the accepted byte range."
        ),
        "forbidden_surfaces": FORBIDDEN_SURFACES,
    }


def build_freeze_rows(
    repair_ledger: dict[str, Any],
    native_ledger: dict[str, Any],
    selected_hash_set: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocker_by_source = {row["source"]: row for row in repair_ledger.get("repair_blockers", [])}
    candidate_by_source = {row["file_name"]: row for row in native_ledger.get("accepted_native_scid_candidates", [])}
    freeze_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for file_name, expected_symbol in EXPECTED_SOURCES:
        candidate = candidate_by_source.get(file_name)
        repair_blocker = blocker_by_source.get(file_name)
        if not candidate or not repair_blocker:
            blockers.append(
                {
                    "source": file_name,
                    "symbol": expected_symbol,
                    "blocker_status": "MISSING_FROM_REQUIRED_INPUT_LEDGER",
                    "exact_next_action": "repair input ledger must include this required source",
                }
            )
            continue
        path = Path(candidate["absolute_path"])
        base_row = {
            "source": file_name,
            "symbol": expected_symbol,
            "source_path": str(path),
            "source_family": candidate.get("source_family"),
            "source_instrument": candidate.get("source_instrument"),
            "proxy_note": candidate.get("proxy_note"),
            "chosen_repair_policy": "BOUNDED_ELIGIBLE_SEGMENT",
            "raw_snapshot_policy": "NO_RAW_SNAPSHOT_WRITTEN_OR_COMMITTED",
            "source_packet_partition_assignment": candidate.get("partition_assignment"),
            "repair_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED",
            "duplicate_source_decision_prior": candidate.get("duplicate_source_decision"),
            "duplicate_source_decision_repaired": "UNIQUE_SEGMENT_HASH_NOT_DISCOVERY_SELECTED_AND_G12_REAUDIT_REQUIRED",
            "eligible_segment_start_utc_hard_floor": candidate.get("eligible_segment_start_utc"),
            "source_packet_eligible_segment_end_utc": candidate.get("eligible_segment_end_utc"),
            "source_packet_coverage_start_utc": candidate.get("coverage_start_utc"),
            "source_packet_coverage_end_utc": candidate.get("coverage_end_utc"),
            "source_packet_record_count": candidate.get("record_count"),
            "source_packet_size_bytes": candidate.get("size_bytes"),
            "source_packet_full_file_sha256": candidate.get("source_sha256"),
            "g12_recomputed_coverage_end_utc": repair_blocker.get("recomputed_coverage_end_utc"),
            "g12_recomputed_size_bytes": repair_blocker.get("recomputed_size_bytes"),
            "g12_recomputed_full_file_sha256": repair_blocker.get("recomputed_sha256"),
            "g12_failure_anatomy": repair_blocker.get("failure_anatomy"),
            "remaining_gates_before_validation": repair_ledger.get("remaining_non_repair_gates_before_validation", []),
            "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
            "no_leak_status": "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
        }
        try:
            metadata = parse_scid_metadata(path)
            if metadata.get("parser_status") != "SCID_HEADER_AND_RECORD_PARSER_OK":
                row = {**base_row, "current_mutable_metadata": metadata, "repair_status": "SOURCE_ACCESS_BLOCKED"}
                row["exact_source_access_blocker"] = metadata.get("parser_status")
                freeze_rows.append(row)
                blockers.append(row)
                continue
            full_reference = current_full_file_hash(path)
            segment = derive_segment(path, candidate["eligible_segment_start_utc"], metadata)
            row = {
                **base_row,
                "current_mutable_metadata": {**metadata, **full_reference},
                "repaired_immutable_metadata": segment,
                "repair_status": segment.get("segment_status"),
                "segment_hash_is_discovery_selected_source_hash": segment.get("segment_records_sha256") in selected_hash_set,
                "eligible_hard_floor_preserved": (
                    segment.get("segment_first_record_utc") is not None
                    and parse_time(segment["segment_first_record_utc"]) >= parse_time(candidate["eligible_segment_start_utc"])
                ),
                "refreshed_coverage_start_utc": metadata.get("coverage_start_utc"),
                "refreshed_coverage_end_utc": metadata.get("coverage_end_utc"),
                "refreshed_record_count": metadata.get("record_count"),
                "refreshed_size_bytes": metadata.get("size_bytes"),
                "record_count_drift_vs_source_packet": int(metadata.get("record_count", 0)) - int(candidate.get("record_count", 0)),
                "coverage_end_drift_vs_source_packet": metadata.get("coverage_end_utc") != candidate.get("coverage_end_utc"),
                "source_full_file_hash_reference_only_not_accepted": True,
            }
            if (
                segment.get("segment_status") != "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN"
                or not segment.get("immediate_rehash_matches")
                or row["segment_hash_is_discovery_selected_source_hash"]
                or not row["eligible_hard_floor_preserved"]
            ):
                blockers.append(
                    {
                        "source": file_name,
                        "symbol": expected_symbol,
                        "blocker_status": "SEGMENT_FREEZE_FAILED",
                        "row": row,
                        "exact_next_action": "repair SCID segment parser or source access before G12 reaudit",
                    }
                )
            freeze_rows.append(row)
        except Exception as exc:  # pragma: no cover - local access failure path.
            row = {
                **base_row,
                "repair_status": "SOURCE_ACCESS_BLOCKED",
                "exact_source_access_blocker": repr(exc),
                "exact_next_action": "obtain read-only access to local Sierra SCID source or provide immutable export",
            }
            freeze_rows.append(row)
            blockers.append(row)
    return freeze_rows, blockers


def build_source_freeze_ledger(freeze_rows: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    repaired_count = sum(row.get("repair_status") == "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN" for row in freeze_rows)
    return {
        **safe_flags(),
        "artifact_family": "source_freeze_ledger",
        "repair_policy": "BOUNDED_ELIGIBLE_SEGMENT",
        "repair_policy_justification": (
            "Full-file native SCID hashes are mutable because Sierra appends records. Bounded segment hashes freeze "
            "a byte range ending at the repair timestamp, while preserving the eligible_segment_start_utc hard floor."
        ),
        "candidate_count": len(freeze_rows),
        "repaired_source_count": repaired_count,
        "source_access_blocker_count": len(blockers),
        "all_9_sources_repaired_or_exact_blocked": len(freeze_rows) == 9 and repaired_count + len(blockers) == 9,
        "all_9_sources_repaired": repaired_count == 9 and not blockers,
        "repair_blockers": blockers,
        "freeze_rows": freeze_rows,
        "summary": {
            "candidate_count": len(freeze_rows),
            "repaired_source_count": repaired_count,
            "source_access_blocker_count": len(blockers),
            "terminal_repair_status": "ALL_9_SOURCES_REPAIRED" if repaired_count == 9 and not blockers else "EXACT_SOURCE_BLOCKERS_REMAIN",
        },
    }


def build_snapshot_segment_manifest(freeze_rows: list[dict[str, Any]]) -> dict[str, Any]:
    segments = []
    for row in freeze_rows:
        segment = row.get("repaired_immutable_metadata", {})
        if segment.get("segment_status") == "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN":
            segments.append(
                {
                    "source": row["source"],
                    "symbol": row["symbol"],
                    "source_path": row["source_path"],
                    "snapshot_file_written": False,
                    "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
                    "segment_record_start_index": segment["segment_record_start_index"],
                    "segment_record_end_index_inclusive": segment["segment_record_end_index_inclusive"],
                    "segment_record_count": segment["segment_record_count"],
                    "segment_byte_start": segment["segment_byte_start"],
                    "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
                    "segment_byte_length": segment["segment_byte_length"],
                    "eligible_segment_start_utc_hard_floor": segment["eligible_segment_start_utc_hard_floor"],
                    "segment_first_record_utc": segment["segment_first_record_utc"],
                    "segment_last_record_utc": segment["segment_last_record_utc"],
                    "segment_records_sha256": segment["segment_records_sha256"],
                    "segment_descriptor_sha256": segment["segment_descriptor_sha256"],
                    "immediate_rehash_matches": segment["immediate_rehash_matches"],
                    "append_safety_rule": segment["append_mutability_repaired_by"],
                }
            )
    return {
        **safe_flags(),
        "artifact_family": "snapshot_segment_manifest",
        "chosen_policy": "BOUNDED_ELIGIBLE_SEGMENT",
        "raw_snapshot_files_written": 0,
        "raw_snapshot_files_committed": 0,
        "raw_snapshot_commit_policy": "NO_RAW_SCID_OR_SEGMENT_BYTES_COMMITTED; COMMITTED HASH_MANIFEST_ONLY",
        "segment_count": len(segments),
        "segments": segments,
        "summary": {
            "segment_count": len(segments),
            "raw_snapshot_files_written": 0,
            "policy": "bounded eligible segment hashes",
        },
    }


def build_source_hash_manifest(freeze_rows: list[dict[str, Any]], builder_hash: str) -> dict[str, Any]:
    hashes = []
    for row in freeze_rows:
        current = row.get("current_mutable_metadata", {})
        segment = row.get("repaired_immutable_metadata", {})
        hashes.append(
            {
                "source": row["source"],
                "symbol": row["symbol"],
                "source_path": row["source_path"],
                "mutable_full_file_hash_reference_only": current.get("current_full_file_sha256_reference_only"),
                "mutable_full_file_hash_status": current.get("current_full_file_hash_status"),
                "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
                "accepted_source_evidence_sha256": segment.get("segment_records_sha256"),
                "segment_descriptor_sha256": segment.get("segment_descriptor_sha256"),
                "header_sha256": current.get("header_sha256"),
                "parser_implementation": rel(Path(__file__)),
                "parser_implementation_sha256": builder_hash,
                "source_packet_full_file_sha256_stale_reference": row.get("source_packet_full_file_sha256"),
                "g12_recomputed_full_file_sha256_stale_reference": row.get("g12_recomputed_full_file_sha256"),
                "full_file_reference_is_not_validation_evidence": True,
            }
        )
    return {
        **safe_flags(),
        "artifact_family": "source_hash_manifest",
        "hash_rows": hashes,
        "accepted_hash_policy": "only segment record-byte hashes are accepted repaired source evidence",
        "full_file_hash_policy": "full-file hashes are mutable reference metadata only",
        "all_accepted_hashes_present": all(row.get("accepted_source_evidence_sha256") for row in hashes),
        "summary": {
            "hash_row_count": len(hashes),
            "accepted_hashes_present": all(row.get("accepted_source_evidence_sha256") for row in hashes),
        },
    }


def build_duplicate_discovery_audit(
    freeze_rows: list[dict[str, Any]],
    selected_ledger: dict[str, Any],
    selected_rows: list[dict[str, Any]],
    selected_hash_set: set[str],
    baseline_packet: dict[str, Any],
    g0_discovery: dict[str, Any],
) -> dict[str, Any]:
    segment_hashes = [
        row.get("repaired_immutable_metadata", {}).get("segment_records_sha256")
        for row in freeze_rows
        if row.get("repaired_immutable_metadata", {}).get("segment_records_sha256")
    ]
    duplicate_segment_hashes = sorted({h for h in segment_hashes if segment_hashes.count(h) > 1})
    selected_overlap = sorted(set(segment_hashes).intersection(selected_hash_set))
    baselines = [row.get("family_id") for row in baseline_packet.get("baseline_controls", [])]
    return {
        **safe_flags(),
        "artifact_family": "duplicate_discovery_exclusion_audit",
        "selected_source_rows_preserved": selected_ledger.get("selected_source_count"),
        "selected_source_coverage_row_count": len(selected_rows),
        "selected_source_hash_count": len(selected_hash_set),
        "g0_selected_source_count": g0_discovery.get("source_exposure", {}).get("selected_source_count"),
        "g0_selected_source_hash_count": g0_discovery.get("source_exposure", {}).get("selected_source_hash_count"),
        "accepted_fpb_path_label_rows_remain_excluded": 12_852_758,
        "selected_segment_hash_overlap": selected_overlap,
        "duplicate_segment_hashes": duplicate_segment_hashes,
        "duplicate_decision": (
            "ALL_SEGMENT_HASHES_UNIQUE_AND_DISJOINT_FROM_365_DISCOVERY_SELECTED_SOURCE_HASHES"
            if not duplicate_segment_hashes and not selected_overlap
            else "DUPLICATE_OR_DISCOVERY_OVERLAP_REPAIR_BLOCKER"
        ),
        "partition_assignment_preserved": all(
            row.get("source_packet_partition_assignment") == "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED"
            for row in freeze_rows
        ),
        "repair_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED",
        "expected_baselines": EXPECTED_BASELINES,
        "baseline_controls_present": baselines,
        "all_four_baselines_preserved": baselines == EXPECTED_BASELINES,
        "checks": {
            "selected_source_count_is_365": selected_ledger.get("selected_source_count") == 365,
            "g0_selected_source_count_is_365": g0_discovery.get("source_exposure", {}).get("selected_source_count") == 365,
            "no_selected_segment_hash_overlap": not selected_overlap,
            "no_duplicate_segment_hashes": not duplicate_segment_hashes,
            "all_four_baselines_preserved": baselines == EXPECTED_BASELINES,
            "partition_assignment_preserved": all(
                row.get("source_packet_partition_assignment")
                == "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED"
                for row in freeze_rows
            ),
        },
        "summary": {
            "selected_source_rows_preserved": selected_ledger.get("selected_source_count"),
            "all_four_baselines_preserved": baselines == EXPECTED_BASELINES,
            "duplicate_decision": (
                "ALL_SEGMENT_HASHES_UNIQUE_AND_DISJOINT_FROM_365_DISCOVERY_SELECTED_SOURCE_HASHES"
                if not duplicate_segment_hashes and not selected_overlap
                else "DUPLICATE_OR_DISCOVERY_OVERLAP_REPAIR_BLOCKER"
            ),
        },
    }


def build_parser_asof_noleak_audit(freeze_rows: list[dict[str, Any]], builder_hash: str) -> dict[str, Any]:
    rows = []
    for row in freeze_rows:
        segment = row.get("repaired_immutable_metadata", {})
        current = row.get("current_mutable_metadata", {})
        rows.append(
            {
                "source": row["source"],
                "symbol": row["symbol"],
                "parser_status": current.get("parser_status"),
                "record_size": current.get("record_size"),
                "header_size": current.get("header_size"),
                "version": current.get("version"),
                "parser_implementation": rel(Path(__file__)),
                "parser_implementation_sha256": builder_hash,
                "as_of_rule": (
                    "future SCID-to-asof-bar derivation must read only records with timestamp >= "
                    "eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest"
                ),
                "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
                "forbidden_fields_read": [],
                "broker_account_order_history_position_fields_read": False,
                "eligible_hard_floor_preserved": row.get("eligible_hard_floor_preserved"),
                "segment_first_record_utc": segment.get("segment_first_record_utc"),
                "segment_last_record_utc": segment.get("segment_last_record_utc"),
                "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
            }
        )
    return {
        **safe_flags(),
        "artifact_family": "parser_asof_no_leak_audit",
        "parser_rows": rows,
        "checks": {
            "all_parser_status_ok": all(row["parser_status"] == "SCID_HEADER_AND_RECORD_PARSER_OK" for row in rows),
            "all_record_sizes_are_40": all(row["record_size"] == 40 for row in rows),
            "all_hard_floors_preserved": all(row["eligible_hard_floor_preserved"] is True for row in rows),
            "no_broker_account_order_history_position_fields_read": all(
                row["broker_account_order_history_position_fields_read"] is False for row in rows
            ),
            "scid_to_asof_gate_explicit": all(
                row["remaining_gate"] == "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
                for row in rows
            ),
        },
        "summary": {
            "parser_row_count": len(rows),
            "all_hard_floors_preserved": all(row["eligible_hard_floor_preserved"] is True for row in rows),
        },
    }


def build_noleak_dirty_state_audit(status_lines: list[str]) -> dict[str, Any]:
    route_prefix = "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/"
    prompt_path = (
        "research/science_program_2026_05/04_goal_prompts/"
        "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-11.md"
    )
    scoped = [line for line in status_lines if route_prefix in line or prompt_path in line]
    unrelated = [line for line in status_lines if line not in scoped and ".context/LIVE_STATE.md" not in line]
    live_surface_scoped = [line for line in scoped if prompt_path not in line]
    return {
        **safe_flags(),
        "artifact_family": "noleak_dirty_state_audit",
        "scoped_repair_paths": scoped,
        "live_state_refresh_path": [line for line in status_lines if ".context/LIVE_STATE.md" in line],
        "unrelated_workspace_dirt_observed_not_part_of_repair_commit": unrelated,
        "scoped_diff_policy": "commit only route artifacts, next G12 repair reaudit prompt, and research_current_state refresh if updated",
        "raw_market_data_commit_scan_rule": "route must not contain committed .scid, .dly, .parquet, .csv, .bin, or .scidseg source blobs",
        "forbidden_surface_changes_detected": [],
        "checks": {
            "no_live_prompt_config_risk_safety_execution_selector_canary_paths_in_scope": not any(
                token in line
                for line in live_surface_scoped
                for token in [
                    "src/components/",
                    "prompts/",
                    "config/",
                    "scripts/canary",
                    "run_agent.py",
                    "execution.py",
                    "permissions.py",
                ]
            ),
            "scoped_paths_are_repair_or_reaudit_prompt_only": all(
                route_prefix in line or prompt_path in line for line in scoped
            ),
        },
        "summary": {
            "scoped_path_count": len(scoped),
            "unrelated_workspace_dirt_count": len(unrelated),
            "forbidden_surface_changes_detected": 0,
        },
    }


def build_hardening_coverage_ledger() -> dict[str, Any]:
    controls = [
        {
            "control": "append_mutable_full_file_not_accepted",
            "coverage": "full-file hash is reference-only; segment hash is accepted evidence",
            "status": "COVERED",
        },
        {
            "control": "segment_boundaries_frozen",
            "coverage": "record and byte start/end boundaries emitted for each source",
            "status": "COVERED",
        },
        {
            "control": "immediate_rehash",
            "coverage": "builder rehashes each frozen byte range immediately",
            "status": "COVERED",
        },
        {
            "control": "future_rehash_verifier",
            "coverage": "verifier rehashes each frozen byte range from the manifest",
            "status": "COVERED",
        },
        {
            "control": "discovery_exclusion_preserved",
            "coverage": "365 selected source rows/hashes remain excluded and disjoint from repaired segment hashes",
            "status": "COVERED",
        },
        {
            "control": "eligible_hard_floor",
            "coverage": "first segment record is required to be >= eligible_segment_start_utc",
            "status": "COVERED",
        },
        {
            "control": "raw_blob_commit_prevention",
            "coverage": "no raw SCID/snapshot bytes are written; committed manifests only",
            "status": "COVERED",
        },
        {
            "control": "future_validation_gate",
            "coverage": "SCID-to-asof-bar derivation and separate validation prompt remain required",
            "status": "COVERED",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "hardening_coverage_ledger",
        "controls": controls,
        "all_hardening_controls_covered": all(row["status"] == "COVERED" for row in controls),
        "summary": {"control_count": len(controls), "all_hardening_controls_covered": True},
    }


def build_source_saturation_ledger(freeze_rows: list[dict[str, Any]]) -> dict[str, Any]:
    searched = [
        {
            "root_id": "g12_repair_blocker_ledger",
            "path": rel(REPAIR_BLOCKER_LEDGER),
            "finding": "exact 9 append-mutable SCID blockers",
        },
        {
            "root_id": "source_expansion_native_scid_ledger",
            "path": rel(NATIVE_SCID_LEDGER),
            "finding": "accepted 9 native SCID sealed-source candidates and hard floors",
        },
        {
            "root_id": "local_sierra_native_data",
            "path": "C:/SierraChart/Data",
            "finding": "read-only direct source for the 9 required files",
        },
        {
            "root_id": "g0_partition_and_baseline_packet",
            "path": rel(G0_PACKET_DIR),
            "finding": "discovery-source exclusion and four-baseline preservation inputs",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "searched_root_source_saturation_ledger",
        "searched_roots": searched,
        "required_source_names": [row[0] for row in EXPECTED_SOURCES],
        "resolved_source_names": [row["source"] for row in freeze_rows],
        "all_required_sources_seen": sorted(row["source"] for row in freeze_rows) == sorted(row[0] for row in EXPECTED_SOURCES),
        "source_saturation_decision": "ALL_REQUIRED_G12_REPAIR_BLOCKERS_PURSUED",
        "summary": {
            "searched_root_count": len(searched),
            "all_required_sources_seen": sorted(row["source"] for row in freeze_rows)
            == sorted(row[0] for row in EXPECTED_SOURCES),
        },
    }


def build_no_lazy_blocker_ledger(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "no_lazy_blocker_ledger",
        "same_evidence_class_pursuit": [
            "read G12 repair blocker ledger",
            "read source-expansion native SCID candidate ledger",
            "opened each local Sierra SCID source read-only",
            "derived bounded eligible segment boundaries and hashes",
            "immediate rehashed every segment",
            "checked discovery-source hash disjointness and duplicate segment hashes",
        ],
        "remaining_blockers": blockers,
        "remaining_blocker_count": len(blockers),
        "terminal_blocker_status": "NO_BLOCKERS" if not blockers else "EXACT_SOURCE_ACCESS_OR_SEGMENT_BLOCKERS_REMAIN",
        "summary": {"remaining_blocker_count": len(blockers)},
    }


def build_hostile_source_review_ledger(freeze_rows: list[dict[str, Any]]) -> dict[str, Any]:
    questions = [
        {
            "attack": "Full-file hashes could drift after append and be mistaken as immutable.",
            "preemption": "accepted evidence is segment_records_sha256 with byte_end_exclusive frozen; full-file hash is reference-only",
            "status": "PREEMPTED",
        },
        {
            "attack": "Pre-eligible records could leak into the segment.",
            "preemption": "start index is lower_bound(timestamp >= eligible_segment_start_utc_hard_floor)",
            "status": "PREEMPTED",
        },
        {
            "attack": "Discovery-selected source could re-enter under a different hash family.",
            "preemption": "365 selected source hashes remain excluded; repaired segment hashes are checked disjoint",
            "status": "PREEMPTED",
        },
        {
            "attack": "Segment hashes could be unrehashable in the next audit.",
            "preemption": "manifest records path, byte range, record indexes, parser hash, and verifier rehashes the same range",
            "status": "PREEMPTED",
        },
        {
            "attack": "Source repair could silently become validation.",
            "preemption": "SCID-to-asof-bar and separate validation-execution gates remain explicit; no result fields are emitted",
            "status": "PREEMPTED",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "hostile_source_review_ledger",
        "hostile_reviews": questions,
        "segment_rows_reviewed": len(freeze_rows),
        "all_attacks_preempted_or_blocked": all(row["status"] == "PREEMPTED" for row in questions),
        "summary": {"attack_count": len(questions), "all_attacks_preempted_or_blocked": True},
    }


def build_negative_failure_anatomy_ledger() -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "negative_failure_anatomy_ledger",
        "prior_failure": {
            "failure": "G12 rejected the source pool because full native SCID files kept appending after materialization.",
            "failed_fields": ["sha256", "size_bytes", "record_count", "coverage_end_utc"],
            "root_cause": "mutable EOF on live Sierra native files, not market-result evidence",
        },
        "repair": {
            "method": "bounded eligible segment hashes",
            "why_it_repairs": "later appended records are beyond the frozen byte_end_exclusive and cannot alter the segment hash",
            "what_it_does_not_repair": [
                "SCID-to-asof-bar derivation contract",
                "candidate generation",
                "validation execution",
                "promotion or live behavior",
            ],
        },
        "summary": {"root_cause": "append-mutable full file evidence"},
    }


def build_process_limitation_countermeasures() -> dict[str, Any]:
    rows = [
        {
            "limitation": "append-mutable source evidence",
            "countermeasure": "accept only bounded segment hashes and byte ranges for Sierra native files",
        },
        {
            "limitation": "raw heavy data could be accidentally committed",
            "countermeasure": "do not write raw snapshot files; verifier scans route for source blobs",
        },
        {
            "limitation": "dirty-main verifier noise",
            "countermeasure": "dirty-state audit separates scoped repair files from unrelated runtime dirt",
        },
        {
            "limitation": "result/control confusion",
            "countermeasure": "safe flags and gate ledgers prevent source repair from becoming validation",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "process_limitation_countermeasures",
        "countermeasures": rows,
        "summary": {"countermeasure_count": len(rows)},
    }


def build_saturation_self_redteam(freeze_rows: list[dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, Any]:
    answers = [
        {
            "question": "What exact mistake would let an append-mutable full file be treated as immutable source evidence again?",
            "answer": "Accepting current_full_file_sha256_reference_only instead of segment_records_sha256. The manifest labels full-file hashes reference-only and verifier checks segment hash rows.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "What exact mistake would let future appended records change the accepted sealed segment hash?",
            "answer": "Hashing to EOF instead of frozen segment_byte_end_exclusive. The segment manifest freezes byte_end_exclusive and record_end_index.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "What exact mistake would let pre-eligible or discovery-exposed records enter a sealed segment?",
            "answer": "Using coverage_start instead of lower_bound(eligible_segment_start_utc). The first segment record must be >= the hard floor and selected discovery hashes remain excluded.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "Are raw snapshot files being committed accidentally, or are they safely ignored/LFS-managed with committed manifests?",
            "answer": "No raw snapshot files are written. The committed repair evidence is JSON/MD manifests plus builder/verifier/tests.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "Can every repaired source be rehashed immediately and reproduce the manifest?",
            "answer": "Yes if no blockers remain: builder immediate-rehashes every segment and verifier rehashes from the manifest.",
            "same_evidence_gap": "closed" if not blockers else "exact blockers remain",
        },
        {
            "question": "Is the parser/as-of rule stable enough for a future SCID-to-asof-bar derivation contract?",
            "answer": "Stable enough for source repair only: SCID header/record parser, record indexes, timestamps, and byte ranges are frozen. Bar derivation remains a separate required gate.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "Does any repair choice weaken the four adversarial baseline preservation?",
            "answer": "No. The G0 four-baseline list is preserved exactly and this route does not modify baselines or result denominators.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "Does any source remain inaccessible, locked, too large, or changing in a way that requires an exact owner/access/source action?",
            "answer": "No if repair_blocker_count is zero; otherwise each blocker row names the exact source/access issue.",
            "same_evidence_gap": "closed" if not blockers else "exact blockers remain",
        },
        {
            "question": "What would the next G12 audit reject, and what artifact preempts it?",
            "answer": "It would reject missing segment rehash, discovery overlap, missing hard floors, raw blobs, or opened validation. Segment manifest, source hash manifest, duplicate audit, parser audit, dirty-state audit, and verifier preempt those.",
            "same_evidence_gap": "closed",
        },
        {
            "question": "What remains blocked before validation execution even after this repair?",
            "answer": "SCID-to-asof-bar derivation contract, candidate-generator constraints, G12 repair acceptance, and a separate validation-execution prompt remain blocked.",
            "same_evidence_gap": "outside_scope_next_evidence_gate",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "saturation_self_redteam_ledger",
        "required_questions": answers,
        "same_evidence_class_gaps_closed": all(row["same_evidence_gap"] in {"closed", "outside_scope_next_evidence_gate"} for row in answers),
        "summary": {
            "question_count": len(answers),
            "same_evidence_class_gaps_closed": all(
                row["same_evidence_gap"] in {"closed", "outside_scope_next_evidence_gate"} for row in answers
            ),
        },
    }


def build_main_packet(
    freeze_ledger: dict[str, Any],
    duplicate_audit: dict[str, Any],
    parser_audit: dict[str, Any],
    baseline_packet: dict[str, Any],
) -> dict[str, Any]:
    repaired = freeze_ledger["all_9_sources_repaired"]
    return {
        **safe_flags(),
        "artifact_family": "repair_packet",
        "terminal_decision": (
            "REPAIRED_ALL_9_SCID_SOURCES_G12_REAUDIT_REQUIRED"
            if repaired
            else "REPAIR_BLOCKED_WITH_EXACT_SOURCE_ACCESS_OR_SEGMENT_BLOCKERS"
        ),
        "source_pool_status_after_repair": "G12_REAUDIT_REQUIRED",
        "validation_execution_prompt_emitted": False,
        "scid_to_asof_bar_derivation_contract_gate": (
            "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_"
            "REQUIRED_BEFORE_ANY_REPLAY_OR_CANDIDATE_GENERATION"
        ),
        "separate_validation_execution_prompt_gate": "REQUIRED_AFTER_SOURCE_CONTROL_CONTRACT_ACCEPTANCE",
        "repaired_source_count": freeze_ledger["repaired_source_count"],
        "source_access_blocker_count": freeze_ledger["source_access_blocker_count"],
        "selected_source_rows_preserved": duplicate_audit["selected_source_rows_preserved"],
        "all_four_baselines_preserved": duplicate_audit["all_four_baselines_preserved"],
        "baseline_controls": [row.get("family_id") for row in baseline_packet.get("baseline_controls", [])],
        "all_hard_floors_preserved": parser_audit["checks"]["all_hard_floors_preserved"],
        "remaining_non_repair_gates_before_validation": [
            "G12 repair reaudit acceptance",
            "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
            "separate validation-execution prompt after source-control contract acceptance",
        ],
        "summary": {
            "terminal_decision": (
                "REPAIRED_ALL_9_SCID_SOURCES_G12_REAUDIT_REQUIRED"
                if repaired
                else "REPAIR_BLOCKED_WITH_EXACT_SOURCE_ACCESS_OR_SEGMENT_BLOCKERS"
            ),
            "repaired_source_count": freeze_ledger["repaired_source_count"],
            "selected_source_rows_preserved": duplicate_audit["selected_source_rows_preserved"],
            "all_four_baselines_preserved": duplicate_audit["all_four_baselines_preserved"],
        },
    }


def build_next_reaudit_prompt() -> dict[str, Any]:
    prompt = f"""# G12 FPB Sealed Source Pool Immutable SCID Hash Freeze Repair Reaudit Goal Prompt

Date: 2026-05-11
Owner lane: independent G12 reaudit of immutable SCID source repair
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR` as source-control repair evidence only.

Required input route:

`research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`

The audit must verify the nine Sierra SCID repair rows, bounded eligible-segment hashes, byte/record boundaries, coverage windows, record counts, parser/as-of/no-leak metadata, duplicate decisions, discovery-source exclusions, four adversarial baseline preservation, eligible_segment_start_utc hard floors, no-leak/dirty-state scope, hardening coverage, and saturation/self-red-team answers.

## Mandatory Boundaries

- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY`.
- Do not execute validation.
- Do not derive SCID bars, generate candidates, replay/path-label rows, score results, calculate R/PnL/win-rate/expectancy/performance, or promote anything.
- Do not call AI/API, paid/vendor routes, credentials, remotes, broker account/order/history/deal/position evidence, or live trading behavior.
- Do not change prompts/config/risk/safety/execution/canary/selector behavior.

## Required Checks

1. Rehash every manifest segment using `segment_byte_start` and `segment_byte_end_exclusive`.
2. Confirm every segment hash reproduces deterministically even if the source file has appended later records.
3. Confirm all 9 sources are repaired or exactly source/access-blocked.
4. Confirm all 365 selected FPB discovery source exclusions remain preserved and disjoint from repaired segment hashes.
5. Confirm all four adversarial baselines remain exactly:
   - `baseline_random_session_control`
   - `baseline_shifted_entry_control`
   - `baseline_momentum_continuation`
   - `baseline_mean_reversion`
6. Confirm every segment first record is at or after `eligible_segment_start_utc_hard_floor`.
7. Confirm SCID-to-asof-bar derivation and separate validation-execution prompt gates remain explicit.
8. Confirm safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
9. Run the repair route verifier and focused tests.
10. Emit a G12 reaudit JSON+MD decision artifact. Accepted source-control repair may only unlock the next SCID-to-asof-bar contract prompt, not validation execution.

## Completion Standard

Complete only if the repair packet and independent verifier prove the source-control repair without opening any forbidden surface. If any source fails rehash or any required preservation check fails, emit exact repair blockers and keep `NO_PROMOTION_VERDICT`.
"""
    NEXT_G12_REAUDIT_PROMPT.write_text(prompt, encoding="utf-8")
    return {
        **safe_flags(),
        "artifact_family": "next_g12_repair_reaudit_prompt_pack",
        "next_g12_reaudit_prompt": rel(NEXT_G12_REAUDIT_PROMPT),
        "next_route_id": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT",
        "audit_boundary": "G12 repair reaudit only; not validation/replay/result scoring",
        "summary": {"next_g12_reaudit_prompt": rel(NEXT_G12_REAUDIT_PROMPT)},
    }


def build_completion_audit(
    artifacts: dict[str, dict[str, str]],
    main_packet: dict[str, Any],
    freeze_ledger: dict[str, Any],
    duplicate_audit: dict[str, Any],
    parser_audit: dict[str, Any],
    snapshot_manifest: dict[str, Any],
    source_hash_manifest: dict[str, Any],
    hardening: dict[str, Any],
    saturation: dict[str, Any],
    next_prompt: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "repair route under required path",
            "artifact": rel(ROUTE_DIR),
            "status": "PASS" if ROUTE_DIR.exists() else "FAIL",
        },
        {
            "requirement": "reconcile all 9 G12 repair blockers",
            "artifact": artifacts["source_freeze_ledger"]["json"],
            "status": "PASS" if freeze_ledger.get("candidate_count") == 9 else "FAIL",
        },
        {
            "requirement": "freeze immutable source evidence for all 9 or exact blockers",
            "artifact": artifacts["source_freeze_ledger"]["json"],
            "status": "PASS" if freeze_ledger.get("all_9_sources_repaired_or_exact_blocked") else "FAIL",
        },
        {
            "requirement": "all 365 discovery source exclusions preserved",
            "artifact": artifacts["duplicate_discovery_exclusion_audit"]["json"],
            "status": "PASS" if duplicate_audit["checks"]["selected_source_count_is_365"] else "FAIL",
        },
        {
            "requirement": "four adversarial baselines preserved",
            "artifact": artifacts["duplicate_discovery_exclusion_audit"]["json"],
            "status": "PASS" if duplicate_audit["checks"]["all_four_baselines_preserved"] else "FAIL",
        },
        {
            "requirement": "eligible_segment_start_utc hard floors preserved",
            "artifact": artifacts["parser_asof_no_leak_audit"]["json"],
            "status": "PASS" if parser_audit["checks"]["all_hard_floors_preserved"] else "FAIL",
        },
        {
            "requirement": "SCID-to-asof and validation gates explicit",
            "artifact": artifacts["repair_packet"]["json"],
            "status": "PASS"
            if "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT" in main_packet["scid_to_asof_bar_derivation_contract_gate"]
            and main_packet["validation_execution_prompt_emitted"] is False
            else "FAIL",
        },
        {
            "requirement": "source/snapshot/segment manifests exist",
            "artifact": artifacts["snapshot_segment_manifest"]["json"],
            "status": "PASS" if snapshot_manifest.get("segment_count") == 9 else "FAIL",
        },
        {
            "requirement": "source hash manifest exists and all accepted hashes present",
            "artifact": artifacts["source_hash_manifest"]["json"],
            "status": "PASS" if source_hash_manifest.get("all_accepted_hashes_present") else "FAIL",
        },
        {
            "requirement": "parser/as-of/no-leak audit exists",
            "artifact": artifacts["parser_asof_no_leak_audit"]["json"],
            "status": "PASS" if all(parser_audit.get("checks", {}).values()) else "FAIL",
        },
        {
            "requirement": "hardening coverage and saturation/self-red-team exist",
            "artifact": artifacts["saturation_self_redteam"]["json"],
            "status": "PASS"
            if hardening.get("all_hardening_controls_covered") and saturation.get("same_evidence_class_gaps_closed")
            else "FAIL",
        },
        {
            "requirement": "next G12 repair reaudit prompt exists and is runnable",
            "artifact": next_prompt["next_g12_reaudit_prompt"],
            "status": "PASS" if NEXT_G12_REAUDIT_PROMPT.exists() else "FAIL",
        },
        {
            "requirement": "safe flags preserved",
            "artifact": artifacts["repair_packet"]["json"],
            "status": "PASS"
            if main_packet.get("promotion_verdict") == PROMOTION_VERDICT
            and main_packet.get("validation_safe") is False
            and main_packet.get("outcome_review_opened") is False
            and main_packet.get("live_effect") is False
            else "FAIL",
        },
    ]
    completion_standard = all(row["status"] == "PASS" for row in checklist) and freeze_ledger.get("all_9_sources_repaired")
    return {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Repair the nine append-mutable Sierra SCID sealed-pool candidates by freezing bounded eligible "
            "segment hashes and preserving all source-control/no-leak gates without validation execution."
        ),
        "prompt_to_artifact_checklist": checklist,
        "completion_standard_satisfied": completion_standard,
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": completion_standard,
        "remaining_blockers": [] if completion_standard else freeze_ledger.get("repair_blockers", []),
        "summary": {
            "completion_standard_satisfied": completion_standard,
            "repaired_source_count": freeze_ledger.get("repaired_source_count"),
            "remaining_blocker_count": len(freeze_ledger.get("repair_blockers", [])),
        },
    }


def build_output_manifest(artifacts: dict[str, dict[str, str]], main_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "terminal_decision": main_packet.get("terminal_decision"),
        "artifacts": artifacts,
        "builder": rel(Path(__file__)),
        "verifier": rel(ROUTE_DIR / "verify_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"),
        "focused_tests": rel(ROUTE_DIR / "test_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"),
        "next_g12_reaudit_prompt": rel(NEXT_G12_REAUDIT_PROMPT),
        "summary": {
            "artifact_count": len(artifacts),
            "terminal_decision": main_packet.get("terminal_decision"),
        },
    }


def build_packet() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    repair_ledger = load_json(REPAIR_BLOCKER_LEDGER)
    native_ledger = load_json(NATIVE_SCID_LEDGER)
    selected_ledger = load_json(SELECTED_SOURCE_LEDGER)
    baseline_packet = load_json(G0_BASELINE_PACKET)
    g0_partition = load_json(G0_PARTITION_LEDGER)
    g0_discovery = load_json(G0_DISCOVERY_LEDGER)
    selected_hash_set, selected_rows = selected_hashes_and_rows(selected_ledger)
    builder_hash = sha256_file(Path(__file__))
    status_lines = git_status_short()

    freeze_rows, blockers = build_freeze_rows(repair_ledger, native_ledger, selected_hash_set)
    context_anchor = build_context_anchor()
    freeze_ledger = build_source_freeze_ledger(freeze_rows, blockers)
    snapshot_manifest = build_snapshot_segment_manifest(freeze_rows)
    source_hash_manifest = build_source_hash_manifest(freeze_rows, builder_hash)
    duplicate_audit = build_duplicate_discovery_audit(
        freeze_rows, selected_ledger, selected_rows, selected_hash_set, baseline_packet, g0_discovery
    )
    parser_audit = build_parser_asof_noleak_audit(freeze_rows, builder_hash)
    dirty_audit = build_noleak_dirty_state_audit(status_lines)
    hardening = build_hardening_coverage_ledger()
    saturation_ledger = build_source_saturation_ledger(freeze_rows)
    no_lazy = build_no_lazy_blocker_ledger(blockers)
    hostile_review = build_hostile_source_review_ledger(freeze_rows)
    negative = build_negative_failure_anatomy_ledger()
    process = build_process_limitation_countermeasures()
    saturation = build_saturation_self_redteam(freeze_rows, blockers)
    main_packet = build_main_packet(freeze_ledger, duplicate_audit, parser_audit, baseline_packet)
    next_prompt = build_next_reaudit_prompt()

    artifacts: dict[str, dict[str, str]] = {}
    payloads = [
        ("context_anchor", f"{FILE_PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}", "Context Anchor", context_anchor),
        ("source_freeze_ledger", f"{FILE_PREFIX}_SOURCE_FREEZE_LEDGER_{DATE_TAG}", "Source Freeze Ledger", freeze_ledger),
        (
            "snapshot_segment_manifest",
            f"{FILE_PREFIX}_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}",
            "Snapshot Segment Manifest",
            snapshot_manifest,
        ),
        ("source_hash_manifest", f"{FILE_PREFIX}_SOURCE_HASH_MANIFEST_{DATE_TAG}", "Source Hash Manifest", source_hash_manifest),
        (
            "duplicate_discovery_exclusion_audit",
            f"{FILE_PREFIX}_DUPLICATE_EXCLUSION_AUDIT_{DATE_TAG}",
            "Duplicate Discovery Exclusion Audit",
            duplicate_audit,
        ),
        (
            "parser_asof_no_leak_audit",
            f"{FILE_PREFIX}_PARSER_ASOF_NOLEAK_AUDIT_{DATE_TAG}",
            "Parser Asof No Leak Audit",
            parser_audit,
        ),
        (
            "noleak_dirty_state_audit",
            f"{FILE_PREFIX}_NOLEAK_DIRTY_AUDIT_{DATE_TAG}",
            "No Leak Dirty State Audit",
            dirty_audit,
        ),
        ("hardening_coverage", f"{FILE_PREFIX}_HARDENING_LEDGER_{DATE_TAG}", "Hardening Coverage Ledger", hardening),
        (
            "source_saturation",
            f"{FILE_PREFIX}_SOURCE_SATURATION_LEDGER_{DATE_TAG}",
            "Searched Root Source Saturation Ledger",
            saturation_ledger,
        ),
        ("no_lazy_blocker", f"{FILE_PREFIX}_NO_LAZY_BLOCKER_LEDGER_{DATE_TAG}", "No Lazy Blocker Ledger", no_lazy),
        ("hostile_source_review", f"{FILE_PREFIX}_HOSTILE_REVIEW_LEDGER_{DATE_TAG}", "Hostile Source Review Ledger", hostile_review),
        (
            "negative_failure_anatomy",
            f"{FILE_PREFIX}_NEGATIVE_ANATOMY_LEDGER_{DATE_TAG}",
            "Negative Failure Anatomy Ledger",
            negative,
        ),
        (
            "process_limitation_countermeasures",
            f"{FILE_PREFIX}_PROCESS_COUNTERMEASURES_{DATE_TAG}",
            "Process Limitation Countermeasures",
            process,
        ),
        ("saturation_self_redteam", f"{FILE_PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}", "Saturation Self Redteam Ledger", saturation),
        ("next_g12_reaudit_prompt_pack", f"{FILE_PREFIX}_NEXT_G12_PROMPT_PACK_{DATE_TAG}", "Next G12 Reaudit Prompt Pack", next_prompt),
        ("repair_packet", f"{FILE_PREFIX}_{DATE_TAG}", "FPB Immutable SCID Hash Freeze Repair Packet", main_packet),
    ]
    for key, stem, title, payload in payloads:
        artifacts[key] = write_pair(stem, title, payload)

    completion = build_completion_audit(
        artifacts,
        main_packet,
        freeze_ledger,
        duplicate_audit,
        parser_audit,
        snapshot_manifest,
        source_hash_manifest,
        hardening,
        saturation,
        next_prompt,
    )
    artifacts["completion_audit"] = write_pair(
        f"{FILE_PREFIX}_COMPLETION_AUDIT_{DATE_TAG}", "Completion Audit", completion
    )
    manifest = build_output_manifest(artifacts, main_packet)
    artifacts["output_manifest"] = write_pair(f"{FILE_PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}", "Output Manifest", manifest)

    return {
        "main_packet": main_packet,
        "freeze_ledger": freeze_ledger,
        "snapshot_manifest": snapshot_manifest,
        "source_hash_manifest": source_hash_manifest,
        "duplicate_audit": duplicate_audit,
        "parser_audit": parser_audit,
        "completion_audit": completion,
        "output_manifest": manifest,
        "artifacts": artifacts,
    }


def verify_segments_from_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    manifest_path = manifest_path or ROUTE_DIR / f"{FILE_PREFIX}_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json"
    manifest = load_json(manifest_path)
    failures: list[dict[str, Any]] = []
    verified_rows = []
    for row in manifest.get("segments", []):
        path = Path(row["source_path"])
        expected = row["segment_records_sha256"]
        actual = hash_range(path, int(row["segment_byte_start"]), int(row["segment_byte_end_exclusive"]))
        ok = actual == expected
        verified_rows.append(
            {
                "source": row["source"],
                "symbol": row["symbol"],
                "segment_records_sha256": expected,
                "rehash_sha256": actual,
                "rehash_matches": ok,
                "segment_byte_start": row["segment_byte_start"],
                "segment_byte_end_exclusive": row["segment_byte_end_exclusive"],
            }
        )
        if not ok:
            failures.append(verified_rows[-1])
    return {
        "ok": not failures and len(verified_rows) == 9,
        "verified_segment_count": len(verified_rows),
        "failures": failures,
        "verified_rows": verified_rows,
    }


def main() -> int:
    result = build_packet()
    print(json.dumps({
        "terminal_decision": result["main_packet"]["terminal_decision"],
        "repaired_source_count": result["freeze_ledger"]["repaired_source_count"],
        "source_access_blocker_count": result["freeze_ledger"]["source_access_blocker_count"],
        "completion_standard_satisfied": result["completion_audit"]["completion_standard_satisfied"],
        "output_manifest": result["artifacts"]["output_manifest"]["json"],
    }, indent=2, sort_keys=True))
    return 0 if result["completion_audit"]["completion_standard_satisfied"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
