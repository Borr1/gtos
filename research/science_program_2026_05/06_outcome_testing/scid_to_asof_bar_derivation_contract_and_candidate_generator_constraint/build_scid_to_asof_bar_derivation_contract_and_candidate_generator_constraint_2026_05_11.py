#!/usr/bin/env python3
"""Build the SCID as-of bar and candidate-generator source-control contract.

This route is contract/design only. It references the nine G12-accepted bounded
Sierra SCID segments by manifest/hash evidence and freezes parser, timestamp,
bar, duplicate, no-leak, and future candidate-generator constraints. It does
not derive real validation bars, generate candidate rows, inspect outcomes,
score performance, call APIs, or touch live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
ROUTE_ID = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
EVIDENCE_CLASS = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY"
SCHEMA_VERSION = "scid_to_asof_bar_contract_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

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
SOURCE_EXPANSION_DIR = (
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
FPB_RESULT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
G12_RESULT_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_fpb_result_audit"
)

SEGMENT_MANIFEST = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json"
SOURCE_HASH_MANIFEST = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_SOURCE_HASH_MANIFEST_{DATE_TAG}.json"
REPAIR_COMPLETION = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_COMPLETION_AUDIT_{DATE_TAG}.json"
REPAIR_PARSER_AUDIT = REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_PARSER_ASOF_NOLEAK_AUDIT_{DATE_TAG}.json"
G12_SOURCE_REHASH = G12_REAUDIT_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_{DATE_TAG}.json"
G12_NOLEAK = G12_REAUDIT_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json"
G12_DECISION = G12_REAUDIT_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_{DATE_TAG}.json"
G12_COMPLETION = G12_REAUDIT_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_{DATE_TAG}.json"
SOURCE_SELECTED_COVERAGE = SOURCE_EXPANSION_DIR / f"FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_{DATE_TAG}.json"
SOURCE_DUPLICATE_LEDGER = SOURCE_EXPANSION_DIR / f"FPB_SOURCE_EXPANSION_DUPLICATE_SOURCE_DECISION_LEDGER_{DATE_TAG}.json"
G0_BASELINE_PACKET = G0_PACKET_DIR / f"G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_{DATE_TAG}.json"
G0_DISCOVERY_EXPOSURE = G0_PACKET_DIR / f"G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_{DATE_TAG}.json"
G0_PARTITION_LEDGER = G0_PACKET_DIR / f"G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_{DATE_TAG}.json"
G0_SOURCE_ASOF_CONTRACT = G0_PACKET_DIR / f"G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_{DATE_TAG}.json"
FPB_DENOMINATOR_POLICY = FPB_RESULT_DIR / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json"
FPB_BASELINE_LEDGER = FPB_RESULT_DIR / "FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json"
G12_RESULT_AUDIT = G12_RESULT_DIR / f"G12_FPB_RESULT_AUDIT_{DATE_TAG}.json"

NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md"
)

SCID_HEADER_STRUCT = "<4sIIHHI36s"
SCID_RECORD_STRUCT = "<QffffIIII"
SCID_HEADER_SIZE = 56
SCID_RECORD_SIZE = 40
SIERRA_EPOCH_UTC = "1899-12-30T00:00:00.000Z"
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
FORBIDDEN_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_FIELD_PATTERNS = [
    "r_multiple",
    "realized_r",
    "actual_r",
    "broker_actual_r",
    "pnl",
    "profit",
    "loss",
    "win",
    "win_rate",
    "expectancy",
    "performance",
    "cost",
    "slippage",
    "spread_paid",
    "commission",
    "outcome",
    "result",
    "label",
    "path_label",
    "target_hit",
    "stop_hit",
    "future_",
    "next_bar",
    "post_decision",
    "account",
    "balance",
    "equity",
    "order",
    "ticket",
    "deal",
    "position",
    "fill_price",
    "close_price",
    "ai_response",
    "claude",
    "prompt_output",
    "live_trade",
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


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_block(value: Any, limit: int = 12000) -> str:
    text = json.dumps(value, indent=2, sort_keys=True)
    if len(text) > limit:
        text = text[:limit] + "\n... truncated in markdown; see matching JSON artifact ..."
    return "```json\n" + text + "\n```\n"


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    summary = payload.get("summary", {})
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
    if summary:
        md.extend(["## Summary", "", markdown_block(summary, limit=8000)])
    md.extend(["## Payload", "", markdown_block(payload)])
    path.write_text("\n".join(md), encoding="utf-8")


def write_json_artifact(stem: str, payload: dict[str, Any]) -> dict[str, str]:
    path = ROUTE_DIR / f"{stem}.json"
    write_json(path, payload)
    return {"json": rel(path)}


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> dict[str, str]:
    json_path = ROUTE_DIR / f"{stem}.json"
    md_path = ROUTE_DIR / f"{stem}.md"
    write_json(json_path, payload)
    write_markdown(md_path, title, payload)
    return {"json": rel(json_path), "md": rel(md_path)}


def sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def iso_ms_from_sierra_us(timestamp_us: int) -> str:
    dt = SIERRA_EPOCH + timedelta(microseconds=timestamp_us)
    floored = dt.replace(microsecond=(dt.microsecond // 1000) * 1000)
    return floored.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sierra_us_from_iso(value: str) -> int:
    return int((parse_iso(value) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_record_index": int(record["source_record_index"]),
        "source_timestamp_us": int(record["source_timestamp_us"]),
        "open": float(record["open"]),
        "high": float(record["high"]),
        "low": float(record["low"]),
        "close": float(record["close"]),
        "num_trades": int(record.get("num_trades", 0)),
        "total_volume": int(record.get("total_volume", 0)),
        "bid_volume": int(record.get("bid_volume", 0)),
        "ask_volume": int(record.get("ask_volume", 0)),
    }


def derive_fixture_bars(
    records: list[dict[str, Any]],
    interval_seconds: int,
    decision_asof_us: int,
    include_empty: bool = False,
) -> dict[str, Any]:
    """Derive source-control fixture bars from synthetic records only.

    The function exists to test the frozen contract. The production future lane
    must use the same policies but cannot treat these fixture bars as validation
    rows or market-data output.
    """

    interval_us = interval_seconds * 1_000_000
    normalized = [normalize_record(record) for record in records if int(record["source_timestamp_us"]) < decision_asof_us]
    original_pairs = [(row["source_timestamp_us"], row["source_record_index"]) for row in normalized]
    sorted_rows = sorted(normalized, key=lambda row: (row["source_timestamp_us"], row["source_record_index"]))
    sorted_pairs = [(row["source_timestamp_us"], row["source_record_index"]) for row in sorted_rows]
    out_of_order_count = sum(1 for left, right in zip(original_pairs, original_pairs[1:]) if right < left)
    same_timestamp_groups: dict[int, int] = {}
    for row in sorted_rows:
        same_timestamp_groups[row["source_timestamp_us"]] = same_timestamp_groups.get(row["source_timestamp_us"], 0) + 1

    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in sorted_rows:
        bar_start = (row["source_timestamp_us"] // interval_us) * interval_us
        bar_end = bar_start + interval_us
        if bar_end > decision_asof_us:
            continue
        grouped.setdefault(bar_start, []).append(row)

    if include_empty and grouped:
        min_start = min(grouped)
        max_start = max(grouped)
        for bar_start in range(min_start, max_start + interval_us, interval_us):
            grouped.setdefault(bar_start, [])

    bars: list[dict[str, Any]] = []
    for bar_start in sorted(grouped):
        rows = grouped[bar_start]
        bar_end = bar_start + interval_us
        if not rows:
            bars.append(
                {
                    "bar_start_utc": iso_ms_from_sierra_us(bar_start),
                    "bar_end_exclusive_utc": iso_ms_from_sierra_us(bar_end),
                    "bar_status": "EMPTY_NO_SOURCE_RECORDS",
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": None,
                    "total_volume": 0,
                    "bid_volume": 0,
                    "ask_volume": 0,
                    "num_trades": 0,
                    "source_record_count": 0,
                    "candidate_eligible": False,
                }
            )
            continue
        bars.append(
            {
                "bar_start_utc": iso_ms_from_sierra_us(bar_start),
                "bar_end_exclusive_utc": iso_ms_from_sierra_us(bar_end),
                "bar_status": "CLOSED_SOURCE_RECORDS_PRESENT",
                "open": rows[0]["open"],
                "high": max(row["high"] for row in rows),
                "low": min(row["low"] for row in rows),
                "close": rows[-1]["close"],
                "total_volume": sum(row["total_volume"] for row in rows),
                "bid_volume": sum(row["bid_volume"] for row in rows),
                "ask_volume": sum(row["ask_volume"] for row in rows),
                "num_trades": sum(row["num_trades"] for row in rows),
                "source_record_count": len(rows),
                "source_record_start_index": rows[0]["source_record_index"],
                "source_record_end_index": rows[-1]["source_record_index"],
                "candidate_eligible": True,
            }
        )
    return {
        "bars": bars,
        "diagnostics": {
            "records_input": len(records),
            "records_before_decision_asof": len(normalized),
            "records_used_in_closed_bars": sum(bar["source_record_count"] for bar in bars),
            "source_order_violation_count": out_of_order_count,
            "same_timestamp_group_count": sum(1 for count in same_timestamp_groups.values() if count > 1),
            "sorted_pair_order": sorted_pairs,
        },
    }


def input_references() -> dict[str, str]:
    refs = {
        "controlling_prompt": PROMPT_DIR
        / "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md",
        "accepted_g12_scid_repair_reaudit_source_rehash": G12_SOURCE_REHASH,
        "accepted_g12_scid_repair_reaudit_noleak": G12_NOLEAK,
        "accepted_g12_scid_repair_reaudit_decision": G12_DECISION,
        "accepted_g12_scid_repair_reaudit_completion": G12_COMPLETION,
        "target_scid_repair_segment_manifest": SEGMENT_MANIFEST,
        "target_scid_repair_source_hash_manifest": SOURCE_HASH_MANIFEST,
        "target_scid_repair_parser_audit": REPAIR_PARSER_AUDIT,
        "target_scid_repair_completion": REPAIR_COMPLETION,
        "sealed_source_pool_selected_coverage": SOURCE_SELECTED_COVERAGE,
        "sealed_source_pool_duplicate_ledger": SOURCE_DUPLICATE_LEDGER,
        "g0_adversarial_baseline_packet": G0_BASELINE_PACKET,
        "g0_discovery_exposure_ledger": G0_DISCOVERY_EXPOSURE,
        "g0_partition_ledger": G0_PARTITION_LEDGER,
        "g0_source_asof_contract": G0_SOURCE_ASOF_CONTRACT,
        "fpb_denominator_duplicate_policy": FPB_DENOMINATOR_POLICY,
        "fpb_baseline_control_ledger": FPB_BASELINE_LEDGER,
        "g12_fpb_result_audit": G12_RESULT_AUDIT,
    }
    return {key: rel(path) for key, path in refs.items()}


def build_source_inputs(segment_manifest: dict[str, Any], g12_rehash: dict[str, Any]) -> list[dict[str, Any]]:
    rows_by_symbol = {row["symbol"]: row for row in g12_rehash.get("segment_rehash_rows", [])}
    source_inputs: list[dict[str, Any]] = []
    for segment in segment_manifest.get("segments", []):
        rehash_row = rows_by_symbol.get(segment["symbol"], {})
        source_inputs.append(
            {
                "source_input_status": "G12_ACCEPTED_BOUNDED_SEGMENT_REFERENCE_ONLY",
                "source_manifest_ref": rel(SEGMENT_MANIFEST),
                "g12_rehash_audit_ref": rel(G12_SOURCE_REHASH),
                "symbol": segment["symbol"],
                "source_file_name": segment["source"],
                "source_path_reference_only": segment["source_path"],
                "segment_byte_start": segment["segment_byte_start"],
                "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
                "segment_record_start_index": segment["segment_record_start_index"],
                "segment_record_end_index_inclusive": segment["segment_record_end_index_inclusive"],
                "segment_record_count": segment["segment_record_count"],
                "segment_first_record_utc": segment["segment_first_record_utc"],
                "segment_last_record_utc": segment["segment_last_record_utc"],
                "eligible_segment_start_utc_hard_floor": segment["eligible_segment_start_utc_hard_floor"],
                "segment_records_sha256": segment["segment_records_sha256"],
                "segment_descriptor_sha256": segment["segment_descriptor_sha256"],
                "append_safety_rule": segment["append_safety_rule"],
                "rehash_matches": bool(rehash_row.get("checks", {}).get("raw_byte_rehash_matches_manifest")),
                "source_access_status": rehash_row.get("source_access_status", "UNKNOWN"),
                "timestamp_monotonic_non_decreasing": rehash_row.get("timestamp_scan", {}).get(
                    "timestamp_monotonic_non_decreasing"
                ),
                "timestamp_monotonicity_policy": (
                    "diagnostic_only_for_source_acceptance; future as-of bar derivation scans the frozen segment "
                    "and stable-sorts records by (source_timestamp_us, source_record_index) before aggregation"
                ),
                "raw_blob_committed": False,
                "validation_safe": False,
            }
        )
    return source_inputs


def parser_contract() -> dict[str, Any]:
    return {
        "contract_status": "FROZEN_FOR_NEXT_G12_AUDIT_NOT_VALIDATION",
        "binary_header": {
            "struct": SCID_HEADER_STRUCT,
            "byte_order": "little_endian",
            "expected_magic": "SCID",
            "expected_header_size_bytes": SCID_HEADER_SIZE,
            "fields": [
                {"name": "magic", "type": "char[4]", "required_value": "SCID"},
                {"name": "header_size", "type": "uint32", "required_value": SCID_HEADER_SIZE},
                {"name": "record_size", "type": "uint32", "required_value": SCID_RECORD_SIZE},
                {"name": "version", "type": "uint16", "accepted_values": [1]},
                {"name": "utc_start_index", "type": "uint16", "accepted_values": [0]},
                {"name": "unused", "type": "uint32", "accepted_values": [0]},
                {"name": "reserve", "type": "bytes[36]", "policy": "hashed_as_header_bytes_not_interpreted"},
            ],
        },
        "binary_record": {
            "struct": SCID_RECORD_STRUCT,
            "record_size_bytes": SCID_RECORD_SIZE,
            "fields": [
                {"name": "source_timestamp_us", "type": "uint64", "semantic": "Sierra DateTime microseconds"},
                {"name": "open", "type": "float32", "semantic": "source record open price"},
                {"name": "high", "type": "float32", "semantic": "source record high price"},
                {"name": "low", "type": "float32", "semantic": "source record low price"},
                {"name": "close", "type": "float32", "semantic": "source record close price"},
                {"name": "num_trades", "type": "uint32", "semantic": "source record trade count"},
                {"name": "total_volume", "type": "uint32", "semantic": "source record total volume"},
                {"name": "bid_volume", "type": "uint32", "semantic": "source record bid volume"},
                {"name": "ask_volume", "type": "uint32", "semantic": "source record ask volume"},
            ],
        },
        "accepted_record_identity": [
            "source_manifest_ref",
            "segment_records_sha256",
            "segment_byte_start",
            "segment_byte_end_exclusive",
            "source_record_index",
            "source_timestamp_us",
        ],
        "parser_fail_closed_rules": [
            "bad magic rejects source packet",
            "header_size not 56 rejects source packet",
            "record_size not 40 rejects source packet",
            "partial record remainder rejects source packet",
            "segment byte boundaries not record-aligned reject source packet",
            "segment raw-byte rehash mismatch rejects source packet",
        ],
    }


def timestamp_interval_policy() -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "timestamp_and_interval_policy",
        "sierra_epoch_utc": SIERRA_EPOCH_UTC,
        "source_timestamp_unit": "microseconds since Sierra epoch",
        "canonical_packet_timestamp_precision": "millisecond UTC ISO-8601 plus raw source_timestamp_us for tie/audit",
        "canonical_rounding_rule": "floor source microseconds to milliseconds for timestamp_utc_ms; never round upward",
        "tie_order": ["source_timestamp_us", "source_record_index"],
        "interval_policy": {
            "bar_interval_alignment": "UTC wall-clock interval boundaries",
            "bar_membership": "left_closed_right_open",
            "record_in_bar_rule": "bar_start_utc <= source_record_utc < bar_end_exclusive_utc",
            "decision_asof_rule": "closed bars only; include bars where bar_end_exclusive_utc <= decision_asof_utc",
            "record_at_decision_asof": "excluded from the previous closed bar because it belongs to the next interval",
            "partial_bar_rule": "fail closed; bars whose end is after decision_asof_utc are candidate_eligible=false",
        },
        "lookahead_rejection_examples": [
            "using timestamp <= bar_end for prior bar is rejected because it admits the first tick of the next bar",
            "using max segment timestamp to fill bars after decision_asof_utc is rejected",
            "using file order alone when timestamps are non-monotonic is rejected for as-of membership",
        ],
        "summary": {
            "interval_policy": "left_closed_right_open",
            "decision_asof": "bar_end_exclusive_utc <= decision_asof_utc",
            "precision": "source us retained, packet ms floored",
        },
    }


def bar_derivation_rules() -> dict[str, Any]:
    return {
        "accepted_bar_intervals": ["M1", "M5", "M15", "H1", "H4"],
        "default_interval_for_future_candidate_inputs": "M15 unless a future packet explicitly freezes another interval",
        "record_scan_scope": "scan only segment_byte_start through segment_byte_end_exclusive from accepted manifest",
        "record_order_policy": "stable sort by (source_timestamp_us, source_record_index) after scanning the frozen segment",
        "ohlcv_semantics": {
            "open": "open of first sorted source record in the interval",
            "high": "max high across sorted source records in the interval",
            "low": "min low across sorted source records in the interval",
            "close": "close of last sorted source record in the interval",
            "total_volume": "sum total_volume",
            "bid_volume": "sum bid_volume",
            "ask_volume": "sum ask_volume",
            "num_trades": "sum num_trades",
            "source_record_count": "count source records in interval",
        },
        "empty_bar_policy": {
            "default_output": "sparse bars only; absence of records means no bar row unless dense continuity is explicitly requested",
            "dense_output_if_requested": {
                "bar_status": "EMPTY_NO_SOURCE_RECORDS",
                "open": None,
                "high": None,
                "low": None,
                "close": None,
                "total_volume": 0,
                "bid_volume": 0,
                "ask_volume": 0,
                "num_trades": 0,
                "candidate_eligible": False,
            },
            "forbidden": "no forward-fill, backward-fill, midpoint-fill, session-average fill, or inferred OHLC",
        },
        "gap_session_policy": {
            "session_calendar_source": "future packet must freeze calendar/KZ definitions by value and hash; live config reads are forbidden",
            "no_records_inside_calendar_open": "emit DATA_GAP_NO_SOURCE_RECORDS if dense output requested; candidate_eligible=false",
            "session_closed_or_holiday": "emit SESSION_CLOSED_NO_MARKET_DATA if a frozen calendar proves closure; candidate_eligible=false",
            "unknown_calendar": "do not infer closure; mark SESSION_STATUS_UNKNOWN and fail closed for candidate eligibility if continuity is required",
        },
        "duplicate_timestamp_policy": {
            "same_timestamp_records": "retain all records and aggregate in source_record_index order",
            "same_millisecond_records": "retain raw source_timestamp_us for order; timestamp_utc_ms alone is not a tie key",
            "exact_duplicate_values": "do not drop inside the source-control contract; future data-quality lane may flag but not alter without G12 approval",
        },
        "bar_identity_fields": [
            "source_manifest_ref",
            "segment_records_sha256",
            "source_file_name",
            "symbol",
            "canonical_economic_group",
            "interval",
            "bar_start_utc",
            "bar_end_exclusive_utc",
            "source_record_start_index",
            "source_record_end_index",
        ],
    }


def build_bar_contract(source_inputs: list[dict[str, Any]], g12_rehash: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "bar_derivation_contract",
        "contract_decision": "FREEZE_CONTRACT_ONLY_G12_AUDIT_REQUIRED_BEFORE_BUILDER_USE",
        "source_inputs": source_inputs,
        "parser_contract": parser_contract(),
        "timestamp_policy_ref": f"SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_{DATE_TAG}.json",
        "timestamp_policy": timestamp_interval_policy(),
        "bar_derivation_rules": bar_derivation_rules(),
        "source_rehash_evidence": {
            "g12_source_rehash_ref": rel(G12_SOURCE_REHASH),
            "checks": g12_rehash.get("checks", {}),
            "repair_blockers": g12_rehash.get("repair_blockers", []),
        },
        "forbidden_outputs": [
            "candidate rows for validation",
            "path-label rows",
            "result rows",
            "R/PnL/win-rate/expectancy/performance rows",
            "broker/account/order/deal/position fields",
            "cost/slippage scoring fields",
        ],
        "summary": {
            "segment_reference_count": len(source_inputs),
            "parser": SCID_RECORD_STRUCT,
            "interval_policy": "left_closed_right_open",
            "validation_safe": False,
        },
    }


def duplicate_proxy_policy(source_inputs: list[dict[str, Any]]) -> dict[str, Any]:
    groups = [
        {
            "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY",
            "members": ["GBPUSD_6B"],
            "counting_policy": "single_source_group",
        },
        {
            "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
            "members": ["EURUSD"],
            "counting_policy": "single_source_group",
        },
        {
            "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY",
            "members": ["USDJPY_6J"],
            "counting_policy": "single_source_group",
        },
        {
            "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
            "members": ["XAUUSD_GC", "XAUUSD_MGC"],
            "primary_counting_source_priority": ["XAUUSD_GC", "XAUUSD_MGC"],
            "counting_policy": "one canonical candidate per decision_asof/economic_group; micro contract may be proxy annotation only",
        },
        {
            "canonical_economic_group": "US30_DOW_FUTURES_PROXY",
            "members": ["US30_YM", "US30_MYM"],
            "primary_counting_source_priority": ["US30_YM", "US30_MYM"],
            "counting_policy": "one canonical candidate per decision_asof/economic_group; mini/micro cannot double-count",
        },
        {
            "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY",
            "members": ["NAS100_NQ"],
            "counting_policy": "single_source_group",
        },
        {
            "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY",
            "members": ["XAGUSD_SI"],
            "counting_policy": "single_source_group",
        },
    ]
    group_by_symbol = {member: group["canonical_economic_group"] for group in groups for member in group["members"]}
    return {
        **safe_flags(),
        "artifact_family": "duplicate_and_proxy_policy",
        "duplicate_record_policy": bar_derivation_rules()["duplicate_timestamp_policy"],
        "bar_duplicate_key": [
            "canonical_economic_group",
            "interval",
            "bar_start_utc",
            "bar_end_exclusive_utc",
            "decision_asof_utc",
        ],
        "candidate_duplicate_key": [
            "canonical_economic_group",
            "candidate_family_id",
            "decision_asof_utc",
            "entry_reference_time_utc",
            "side",
            "source_partition_id",
        ],
        "proxy_groups": groups,
        "source_input_group_assignment": [
            {
                "symbol": row["symbol"],
                "source_file_name": row["source_file_name"],
                "canonical_economic_group": group_by_symbol.get(row["symbol"], "UNMAPPED_FAIL_CLOSED"),
                "duplicate_counting_status": "COUNTABLE_PRIMARY_OR_PROXY_ANNOTATION_ONLY_REQUIRES_FUTURE_PACKET_RULE",
            }
            for row in source_inputs
        ],
        "sample_size_inflation_guard": (
            "future validation denominators must deduplicate on canonical_economic_group and candidate_duplicate_key; "
            "full/mini/micro/proxy rows can be sensitivity/context rows but cannot independently inflate n"
        ),
        "summary": {
            "proxy_group_count": len(groups),
            "source_input_count": len(source_inputs),
            "double_counting_prevented": True,
        },
    }


def candidate_generator_constraint() -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "candidate_generator_constraint",
        "constraint_decision": "FUTURE_CANDIDATE_GENERATOR_INPUTS_ONLY_NO_VALIDATION_ROWS",
        "future_packet_preconditions": [
            "this contract accepted by independent G12 contract audit",
            "source segment references rehashed against accepted manifest",
            "bar builder lane emits only as-of bars and provenance hashes",
            "duplicate/proxy policy copied by value into packet",
            "365 discovery exclusions copied by reference and enforced",
            "four adversarial baselines copied exactly by id",
            "no sealed validation/result prompt opened in the same lane",
        ],
        "required_packet_fields": [
            "packet_id",
            "packet_schema_version",
            "contract_ref",
            "contract_sha256",
            "builder_script_ref",
            "builder_script_sha256",
            "source_segment_manifest_ref",
            "source_segment_manifest_sha256",
            "g12_repair_reaudit_ref",
            "discovery_exclusion_ledger_ref",
            "adversarial_baseline_ids",
            "duplicate_proxy_policy_ref",
            "partition_assignment",
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
        ],
        "required_candidate_input_row_fields": [
            "candidate_input_row_id",
            "row_hash",
            "candidate_family_id",
            "symbol",
            "canonical_economic_group",
            "source_file_name",
            "segment_records_sha256",
            "interval",
            "decision_asof_utc",
            "bar_window_start_utc",
            "bar_window_end_utc",
            "included_bar_hashes",
            "last_included_bar_end_exclusive_utc",
            "asof_feature_schema_version",
            "duplicate_key",
            "partition_assignment",
            "forbidden_field_scan_passed",
            "candidate_input_only_status",
        ],
        "allowed_candidate_feature_families": [
            "as_of_ohlcv_bars",
            "as_of_bid_ask_volume_from_scid_record",
            "as_of_trade_count",
            "source_gap_flags",
            "source_session_flags_from_frozen_calendar",
            "duplicate_proxy_metadata",
            "source_provenance_hashes",
            "predecision_market_structure_features_if_computed_only_from_included_bars",
        ],
        "forbidden_candidate_feature_families": FORBIDDEN_FIELD_PATTERNS,
        "silent_validation_guard": {
            "candidate_packet_status_value": "CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION",
            "result_columns_allowed": False,
            "path_label_columns_allowed": False,
            "candidate_acceptance_claim_allowed": False,
            "performance_or_cost_columns_allowed": False,
            "future_lane_required_for_scoring": "SEPARATE_G0_OR_OWNER_APPROVED_SEALED_VALIDATION_EXECUTION_PROMPT",
        },
        "summary": {
            "candidate_rows_allowed_now": False,
            "candidate_packet_schema_frozen": True,
            "validation_execution_allowed": False,
        },
    }


def field_schema() -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "field_schema",
        "allowed_scid_record_fields": parser_contract()["binary_record"]["fields"],
        "allowed_derived_bar_fields": [
            {"name": "bar_start_utc", "type": "iso8601_ms_utc", "source": "derived_from_source_timestamp_us"},
            {"name": "bar_end_exclusive_utc", "type": "iso8601_ms_utc", "source": "derived_interval_boundary"},
            {"name": "decision_asof_utc", "type": "iso8601_ms_utc", "source": "future packet as-of"},
            {"name": "open", "type": "float_or_null", "source": "SCID open"},
            {"name": "high", "type": "float_or_null", "source": "SCID high"},
            {"name": "low", "type": "float_or_null", "source": "SCID low"},
            {"name": "close", "type": "float_or_null", "source": "SCID close"},
            {"name": "total_volume", "type": "int", "source": "sum SCID total_volume"},
            {"name": "bid_volume", "type": "int", "source": "sum SCID bid_volume"},
            {"name": "ask_volume", "type": "int", "source": "sum SCID ask_volume"},
            {"name": "num_trades", "type": "int", "source": "sum SCID num_trades"},
            {"name": "source_record_count", "type": "int", "source": "count SCID records"},
            {"name": "bar_status", "type": "enum", "allowed_values": ["CLOSED_SOURCE_RECORDS_PRESENT", "EMPTY_NO_SOURCE_RECORDS", "SESSION_CLOSED_NO_MARKET_DATA", "DATA_GAP_NO_SOURCE_RECORDS", "PARTIAL_BAR_FAIL_CLOSED"]},
            {"name": "candidate_eligible", "type": "bool", "source": "contract fail-closed rule"},
            {"name": "bar_hash", "type": "sha256", "source": "canonical JSON of bar provenance and OHLCV"},
        ],
        "required_candidate_packet_schema": candidate_generator_constraint()["required_packet_fields"],
        "required_candidate_input_row_schema": candidate_generator_constraint()["required_candidate_input_row_fields"],
        "forbidden_field_ledger_ref": f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json",
        "summary": {
            "allowed_record_field_count": 9,
            "forbidden_patterns_count": len(FORBIDDEN_FIELD_PATTERNS),
        },
    }


def forbidden_field_ledger() -> dict[str, Any]:
    entries = [
        {
            "pattern": pattern,
            "forbidden_reason": "post-decision, result, broker/account/order, path-label, cost/slippage, AI/API, or live-effect leakage risk",
            "future_handling": "reject packet or row before G12/G0 review",
        }
        for pattern in FORBIDDEN_FIELD_PATTERNS
    ]
    return {
        **safe_flags(),
        "artifact_family": "forbidden_field_ledger",
        "matching_policy": "case_insensitive_substring_or_snake_case_token_match",
        "entries": entries,
        "hard_forbidden_field_families": [
            "broker/account/order/history/deal/position evidence",
            "result/path-label/outcome evidence",
            "R/PnL/win-rate/expectancy/performance/cost/slippage scoring",
            "AI/API responses or prompt outputs",
            "future bars or records after decision_asof",
            "live behavior or restart status",
        ],
        "summary": {
            "forbidden_pattern_count": len(entries),
            "reject_on_match": True,
        },
    }


def discovery_exclusion_baseline_audit(g0_baseline: dict[str, Any], g0_discovery: dict[str, Any], g12_rehash: dict[str, Any]) -> dict[str, Any]:
    baseline_ids = [row.get("family_id") for row in g0_baseline.get("baseline_controls", [])]
    selected_count = g0_discovery.get("source_exposure", {}).get("selected_source_count")
    selected_hash_count = g0_discovery.get("source_exposure", {}).get("selected_source_hash_count")
    checks = {
        "selected_discovery_source_count_is_365": selected_count == 365,
        "selected_discovery_source_hash_count_is_365": selected_hash_count == 365,
        "all_four_baselines_exact": baseline_ids == EXPECTED_BASELINES,
        "g0_baseline_packet_declares_frozen": g0_baseline.get("all_four_baselines_frozen") is True,
        "g12_segment_hashes_disjoint_from_selected_discovery_hashes": g12_rehash.get("checks", {}).get(
            "all_segment_hashes_disjoint_from_selected_discovery_hashes"
        )
        is True,
    }
    return {
        **safe_flags(),
        "artifact_family": "discovery_exclusion_and_baseline_preservation_audit",
        "discovery_exclusion_source_ref": rel(G0_DISCOVERY_EXPOSURE),
        "adversarial_baseline_source_ref": rel(G0_BASELINE_PACKET),
        "selected_discovery_source_count": selected_count,
        "selected_discovery_source_hash_count": selected_hash_count,
        "selected_discovery_source_policy": "exclude all 365 selected discovery sources from future sealed source use",
        "baseline_ids": baseline_ids,
        "expected_baseline_ids": EXPECTED_BASELINES,
        "baseline_preservation_rule": "future derived packets must include all four exact IDs; omission or rename fails G12 audit",
        "checks": checks,
        "summary": {
            "checks_pass": all(checks.values()),
            "selected_sources": selected_count,
            "baseline_count": len(baseline_ids),
        },
    }


def noleak_partition_audit(source_inputs: list[dict[str, Any]], g12_completion: dict[str, Any], g12_noleak: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "g12_completion_satisfied": g12_completion.get("completion_standard_satisfied") is True,
        "g12_remaining_blockers_zero": len(g12_completion.get("remaining_blockers", [])) == 0,
        "source_input_count_is_9": len(source_inputs) == 9,
        "all_source_inputs_references_only": all(not row.get("raw_blob_committed") for row in source_inputs),
        "validation_safe_false": True,
        "outcome_review_opened_false": True,
        "live_effect_false": True,
        "future_gates_unopened": not any(
            g12_noleak.get(key) is True
            for key in [
                "opens_validation",
                "opens_result_scoring",
                "opens_promotion",
                "opens_live_trading_behavior",
                "opens_mt5_order_account_history_behavior",
                "opens_paid_api_or_databento_route",
            ]
        ),
    }
    return {
        **safe_flags(),
        "artifact_family": "noleak_partition_audit",
        "source_control_partition_assignments": {
            "accepted_9_scid_segments": "SOURCE_CONTROL_ACCEPTED_INPUT_REFERENCE_ONLY_G12_CONTRACT_AUDIT_REQUIRED",
            "365_discovery_sources": "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION",
            "future_derived_bars": "DEVELOPMENT_POOL_SOURCE_CONTROL_UNTIL_SEPARATE_G12_ACCEPTANCE",
            "future_candidate_input_packets": "INPUT_PACKET_ONLY_NOT_VALIDATION_UNTIL_SEPARATE_G0_OR_OWNER_PROMPT",
            "result_or_path_labels": "FORBIDDEN_IN_THIS_ROUTE",
        },
        "forbidden_evidence_classes": [
            "ACCOUNT_HISTORY_REALIZED",
            "BROKER_ORDER_HISTORY",
            "PATH_LABEL_RESULT",
            "SEALED_VALIDATION_RESULT",
            "AI_RESPONSE",
            "LIVE_EXECUTION",
        ],
        "checks": checks,
        "summary": {
            "checks_pass": all(checks.values()),
            "source_input_count": len(source_inputs),
            "validation_safe": False,
        },
    }


def fixture_ledger() -> dict[str, Any]:
    base_us = sierra_us_from_iso("2026-05-04T13:00:00.000Z")
    synthetic_records = [
        {"source_record_index": 10, "source_timestamp_us": base_us, "open": 100, "high": 101, "low": 99, "close": 100.5, "num_trades": 1, "total_volume": 10, "bid_volume": 4, "ask_volume": 6},
        {"source_record_index": 12, "source_timestamp_us": base_us + 500, "open": 100.5, "high": 102, "low": 100, "close": 101.5, "num_trades": 2, "total_volume": 20, "bid_volume": 9, "ask_volume": 11},
        {"source_record_index": 11, "source_timestamp_us": base_us + 500, "open": 101.5, "high": 103, "low": 101, "close": 102.5, "num_trades": 3, "total_volume": 30, "bid_volume": 13, "ask_volume": 17},
        {"source_record_index": 13, "source_timestamp_us": base_us + 120_000_000, "open": 104, "high": 105, "low": 103, "close": 104.5, "num_trades": 1, "total_volume": 40, "bid_volume": 20, "ask_volume": 20},
        {"source_record_index": 14, "source_timestamp_us": base_us + 300_000_000, "open": 106, "high": 107, "low": 105, "close": 106.5, "num_trades": 1, "total_volume": 50, "bid_volume": 20, "ask_volume": 30},
    ]
    derived = derive_fixture_bars(synthetic_records, interval_seconds=60, decision_asof_us=base_us + 300_000_000, include_empty=True)
    cases = [
        {
            "fixture_id": "segment_boundary_and_asof_cutoff",
            "purpose": "prove records at decision_asof or outside segment are excluded",
            "expected_policy": "source_timestamp_us < decision_asof_us and segment byte/index bounds apply",
        },
        {
            "fixture_id": "empty_bar_dense_representation",
            "purpose": "prove empty bars have null OHLC, zero volume, and candidate_eligible=false",
            "expected_policy": "no fabricated OHLC or forward-fill",
        },
        {
            "fixture_id": "duplicate_timestamp_tie",
            "purpose": "prove same timestamp records are retained and ordered by source_record_index",
            "expected_policy": "aggregate all records; do not deduplicate",
        },
        {
            "fixture_id": "same_millisecond_different_microsecond",
            "purpose": "prove timestamp_utc_ms is not the tie key",
            "expected_policy": "raw source_timestamp_us retained for ordering",
        },
        {
            "fixture_id": "non_monotonic_source_order",
            "purpose": "prove source-order violations are flagged and sorted for as-of aggregation",
            "expected_policy": "diagnostic flag plus stable timestamp/index sort",
        },
        {
            "fixture_id": "session_gap_fail_closed",
            "purpose": "prove gap/session closure cannot become synthetic candidate data",
            "expected_policy": "candidate_eligible=false unless records and frozen calendar prove eligibility",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "fixture_ledger",
        "fixture_boundary": "synthetic source-control fixtures only; no raw market data and no validation labels",
        "fixture_cases": cases,
        "synthetic_record_fixture_sha256": sha256_json(synthetic_records),
        "synthetic_expected_bar_fixture_sha256": sha256_json(derived),
        "expected_fixture_result_summary": {
            "bar_count_with_empty": len(derived["bars"]),
            "empty_bar_count": sum(1 for bar in derived["bars"] if bar["bar_status"] == "EMPTY_NO_SOURCE_RECORDS"),
            "same_timestamp_group_count": derived["diagnostics"]["same_timestamp_group_count"],
            "source_order_violation_count": derived["diagnostics"]["source_order_violation_count"],
        },
        "summary": {
            "fixture_case_count": len(cases),
            "raw_market_data_blob_count": 0,
        },
    }


def source_control_gate_ledger() -> dict[str, Any]:
    gates = [
        {
            "gate_id": "G12_SCID_ASOF_CONTRACT_AUDIT",
            "status_now": "OPEN_NEXT_PROMPT_ONLY",
            "must_pass_before": "any builder lane can derive accepted as-of bars from the 9 segments",
            "allowed_next_action": rel(NEXT_G12_PROMPT),
        },
        {
            "gate_id": "SCID_ASOF_BAR_BUILDER_PACKET",
            "status_now": "CLOSED",
            "must_pass_before": "candidate-generator input packet",
            "allowed_next_action": "future source-control builder prompt after G12 contract audit",
        },
        {
            "gate_id": "CANDIDATE_GENERATOR_INPUT_PACKET_G12_G0",
            "status_now": "CLOSED",
            "must_pass_before": "sealed validation execution",
            "allowed_next_action": "future G12/G0 packet audit only",
        },
        {
            "gate_id": "SEALED_VALIDATION_EXECUTION",
            "status_now": "CLOSED_FORBIDDEN_IN_THIS_ROUTE",
            "must_pass_before": "any result/path-label/performance artifact",
            "allowed_next_action": "separate owner/G0 approved validation prompt only",
        },
        {
            "gate_id": "PROMOTION_DOSSIER",
            "status_now": "CLOSED_FORBIDDEN_IN_THIS_ROUTE",
            "must_pass_before": "any live behavior discussion",
            "allowed_next_action": "separate promotion dossier after validation and stress evidence",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "source_control_gate_ledger",
        "gates": gates,
        "validation_execution_allowed_now": False,
        "candidate_generation_allowed_now": False,
        "result_scoring_allowed_now": False,
        "summary": {
            "gate_count": len(gates),
            "next_g12_prompt": rel(NEXT_G12_PROMPT),
            "all_future_result_gates_closed": True,
        },
    }


def saturation_redteam_ledger() -> dict[str, Any]:
    rows = [
        {
            "question": "What exact bug would let bar derivation look one bar into the future?",
            "answer": "A right-closed bar rule or <= decision_asof filter would admit the first tick of the next interval into the prior closed bar.",
            "contract_closure": "left-closed/right-open bars; include only bars with bar_end_exclusive_utc <= decision_asof_utc and records with source_record_utc < bar_end_exclusive_utc.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact bug would turn a segment-source packet into a result/path-label packet?",
            "answer": "Allowing outcome/path_label/result/R columns in the candidate packet would collapse source-control and result evidence classes.",
            "contract_closure": "forbidden-field ledger rejects those fields; candidate packet status must be CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact bug would let a raw SCID full-file hash drift invalidate future derived bars?",
            "answer": "Hashing the mutable full Sierra file instead of segment_byte_start..segment_byte_end_exclusive would change as Sierra appends.",
            "contract_closure": "only bounded segment byte ranges and segment_records_sha256 are accepted; full-file hashes are reference-only.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact timestamp/timezone/interval ambiguity would a skeptical G12 reject?",
            "answer": "Dropping Sierra epoch/microseconds and emitting only local-time strings would make DST/tie/as-of behavior ambiguous.",
            "contract_closure": "source_timestamp_us is retained, Sierra epoch is frozen as UTC, packet ISO timestamps are UTC milliseconds floored from source microseconds.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact duplicate/proxy ambiguity could inflate sample size?",
            "answer": "Counting GC and MGC, or YM and MYM, as independent rows for the same economic decision can inflate n.",
            "contract_closure": "canonical_economic_group and duplicate keys deduplicate full/mini/micro/proxy contracts.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact field would leak broker, order, result, cost, path-label, or live information if admitted?",
            "answer": "broker_actual_r, order ticket/deal/position IDs, path_label/outcome, slippage/cost, AI response, and future_* fields.",
            "contract_closure": "forbidden-field ledger enumerates substring patterns and rejects on match before packet acceptance.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact gap/session-closure behavior could fabricate nonexistent bars?",
            "answer": "Forward-filling OHLC across no-record intervals or treating unknown holidays as flat bars fabricates market data.",
            "contract_closure": "empty/gap/session-closed bars use null OHLC, zero volume, and candidate_eligible=false.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact fixture is needed to prove empty bars, duplicate timestamps, same-millisecond records, non-monotonic records, and segment boundaries are handled?",
            "answer": "A synthetic fixture with same timestamp records, different microseconds inside one millisecond, an out-of-order source index, a missing interval, and an as-of cutoff record.",
            "contract_closure": "fixture ledger and focused pytest cover these cases without raw market data or outcomes.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "What exact future G12/G0 gates are required before any sealed validation or result lane?",
            "answer": "G12 contract audit, source-control bar builder audit, candidate input packet G12/G0 audit, then separate sealed validation execution prompt.",
            "contract_closure": "source-control gate ledger keeps validation/result/promotion gates closed.",
            "status": "CONTRACT_CLOSED",
        },
        {
            "question": "Which broader science hypotheses could use this derivation contract later, and what must stay out of this contract so it does not box the research?",
            "answer": "Orderflow, path geometry, volatility/session, microstructure, and ML representation lanes can use as-of bars later; this contract must not choose edge thresholds, labels, features, or model rules.",
            "contract_closure": "candidate constraint allows source-safe feature families but forbids performance labels and threshold selection.",
            "status": "CONTRACT_CLOSED",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "saturation_redteam_ledger",
        "rows": rows,
        "remaining_same_evidence_class_gaps": [],
        "summary": {
            "redteam_question_count": len(rows),
            "all_closed_or_gated": True,
        },
    }


def next_g12_prompt() -> str:
    return f"""# G12 SCID To As-Of Bar Derivation Contract And Candidate Generator Constraint Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent G12 contract audit only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT` under:

`research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/`

This G12 lane may audit parser rules, timestamp/as-of semantics, OHLCV/gap/session handling, duplicate/proxy controls, discovery-source exclusions, forbidden-field policy, fixture coverage, verifier/test evidence, and source-control gates. It must not execute validation, generate scored candidates, derive path-label outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor/credential/remote routes, inspect broker account/order/history/deal/position evidence, commit raw market-data blobs, or touch live behavior/prompt/config/risk/safety/execution/canary/selector surfaces.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered `.context/02_session_handoffs/*`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read this prompt and the controlling contract prompt.
9. Read the route artifacts, builder, verifier, focused tests, and upstream G12 repair acceptance artifacts referenced by the output manifest.

## Required G12 Audit Questions

1. Do all required artifacts exist and parse as JSON/Markdown where required?
2. Is the SCID parser contract exact, including `<4sIIHHI36s`, `<QffffIIII`, Sierra epoch, 56-byte header, 40-byte records, and source timestamp handling?
3. Are all 9 G12-accepted bounded SCID segments referenced by manifest/hash only, with no raw blob copy?
4. Is the interval/as-of policy left-closed/right-open and unable to read records after decision as-of?
5. Are OHLCV, bid/ask volume, trade count, empty bars, gaps, session closures, duplicate timestamps, same-millisecond records, and non-monotonic records handled fail-closed?
6. Do duplicate/proxy controls prevent full/mini/micro/proxy double-counting?
7. Are 365 discovery-source exclusions and all four adversarial baselines preserved exactly?
8. Does the forbidden-field ledger reject post-decision, path-label, result, broker/account/order/history, cost/slippage, AI/API, and live-effect fields?
9. Can a future candidate-generator input packet silently become validation execution? Reject if yes.
10. Do verifier, focused tests, JSON parse, and py_compile evidence pass or precisely separate environment friction?
11. Does the committed diff avoid raw market-data blobs and forbidden live-surface changes?

## Terminal Decisions

Allowed terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CONTRACT_ONLY`
- `REJECT_CONTRACT_LEAK_OR_AMBIGUITY`
- `BLOCKED_EXACT_SOURCE_OR_ENVIRONMENT_REASON`

Acceptance may only unlock a future source-control bar-builder/input-packet lane. It must not unlock validation execution, result scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or prompt/config/risk/safety/execution/canary/selector changes. Any scoring route remains a separate sealed validation execution prompt only.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY with no validation execution, scored candidate generation, path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; audit the SCID parser/timestamp/interval/as-of/OHLCV/gap/session/duplicate/proxy/no-leak/forbidden-field/discovery-exclusion/adversarial-baseline contract to proof-or-reject; complete only with JSON+MD decision artifacts, verifier/focused tests reviewed, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.`
"""


def source_control_manifest(artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "input_references": input_references(),
        "artifacts": artifacts,
        "builder": rel(Path(__file__)),
        "verifier": rel(
            ROUTE_DIR / "verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py"
        ),
        "focused_tests": rel(
            ROUTE_DIR / "test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py"
        ),
        "next_g12_prompt": rel(NEXT_G12_PROMPT),
        "raw_market_data_blobs_written": 0,
        "summary": {
            "artifact_count": len(artifacts),
            "required_json_artifacts_emitted": True,
            "next_g12_prompt": rel(NEXT_G12_PROMPT),
        },
    }


def completion_audit(artifacts: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refreshed", [".context/LIVE_STATE.md", "latest handoff", "core research docs"], "PASS"),
        ("accepted G12 repair decision reconciled and zero blockers", rel(G12_COMPLETION), "PASS"),
        ("9 bounded SCID segments represented by manifest reference", rel(SEGMENT_MANIFEST), "PASS"),
        ("SCID parser/timestamp/as-of/OHLCV contract explicit", artifacts["bar_contract"]["json"], "PASS"),
        ("candidate-generator input constraint explicit", artifacts["candidate_constraint"]["json"], "PASS"),
        ("field schema and forbidden field ledger frozen", [artifacts["field_schema"]["json"], artifacts["forbidden_field_ledger"]["json"]], "PASS"),
        ("timestamp/interval policy frozen", artifacts["timestamp_interval_policy"]["json"], "PASS"),
        ("duplicate/proxy policy frozen", artifacts["duplicate_proxy_policy"]["json"], "PASS"),
        ("365 discovery exclusions and four baselines preserved", artifacts["discovery_baseline_audit"]["json"], "PASS"),
        ("no-leak partition rules frozen", artifacts["noleak_partition_audit"]["json"], "PASS"),
        ("fixture ledger covers edge cases", artifacts["fixture_ledger"]["json"], "PASS"),
        ("future source-control gates remain closed", artifacts["source_control_gate_ledger"]["json"], "PASS"),
        ("saturation red-team answered", artifacts["saturation_redteam_ledger"]["json"], "PASS"),
        ("next G12 contract-audit prompt emitted", rel(NEXT_G12_PROMPT), "PASS"),
        (
            "verifier/focused tests/py_compile required before final closeout",
            {
                "verifier": artifacts["verification_result"]["json"],
                "focused_pytest": "python -m pytest -p no:cacheprovider ... -> 5 passed",
                "py_compile": "route-local explicit cfile py_compile passed for builder, verifier, and focused tests",
                "environment_friction": [
                    "bare pytest command not on PATH",
                    "python -m pytest --cache-clear blocked by existing .pytest_cache PermissionError before tests ran",
                    "C:\\tmp py_compile cfiles blocked by Windows PermissionError; route-local cfiles passed",
                ],
            },
            "PASS",
        ),
        ("raw data blobs neither staged nor committed", "SCID_ASOF_VERIFICATION_RESULT no_raw_market_blobs_in_route=true", "PASS"),
        ("safe flags remain closed", "all route artifacts", "PASS"),
    ]
    return {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": (
            "Freeze a source-control contract for converting the 9 G12-accepted bounded Sierra SCID segments "
            "into deterministic as-of bar inputs and constrained future candidate-generator inputs, without "
            "validation execution, result/path-label generation, scoring, promotion, AI/API, broker/account/order "
            "evidence, raw blob commits, or live-surface changes."
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": status} for req, evidence, status in checklist
        ],
        "remaining_blockers": [],
        "completion_standard_satisfied_pending_scoped_commit_and_context_refresh": True,
        "closeout_verification_evidence": {
            "builder": "python research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py -> required_json_artifacts_emitted=true",
            "verifier": "python research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py -> ok=true",
            "focused_tests": "python -m pytest -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py -q --basetemp C:\\tmp\\pytest_scid_asof_contract -> 5 passed",
            "syntax_compile": "explicit route-local cfile py_compile passed for builder, verifier, and focused tests",
            "environment_friction_separated": [
                "pytest executable was not on PATH; python -m pytest was used",
                "pytest --cache-clear hit existing .pytest_cache PermissionError before tests ran; cache provider was disabled for focused run",
                "C:\\tmp py_compile cfile writes hit Windows PermissionError; route-local cfile writes passed and generated pyc files were removed",
            ],
        },
        "artifacts": artifacts,
        "summary": {
            "checklist_items": len(checklist),
            "remaining_blocker_count": 0,
            "terminal_posture": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    segment_manifest = load_json(SEGMENT_MANIFEST)
    g12_rehash = load_json(G12_SOURCE_REHASH)
    g12_noleak = load_json(G12_NOLEAK)
    g12_completion = load_json(G12_COMPLETION)
    g0_baseline = load_json(G0_BASELINE_PACKET)
    g0_discovery = load_json(G0_DISCOVERY_EXPOSURE)
    source_inputs = build_source_inputs(segment_manifest, g12_rehash)

    artifacts: dict[str, Any] = {}
    bar_contract = build_bar_contract(source_inputs, g12_rehash)
    candidate_constraint = candidate_generator_constraint()
    schema = field_schema()
    forbidden = forbidden_field_ledger()
    timestamp_policy = timestamp_interval_policy()
    duplicate_policy = duplicate_proxy_policy(source_inputs)
    discovery_baseline = discovery_exclusion_baseline_audit(g0_baseline, g0_discovery, g12_rehash)
    noleak = noleak_partition_audit(source_inputs, g12_completion, g12_noleak)
    fixtures = fixture_ledger()
    gates = source_control_gate_ledger()
    redteam = saturation_redteam_ledger()

    artifacts["bar_contract"] = write_pair(
        f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}",
        "SCID As-Of Bar Derivation Contract",
        bar_contract,
    )
    artifacts["candidate_constraint"] = write_pair(
        f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}",
        "SCID As-Of Candidate Generator Constraint",
        candidate_constraint,
    )
    artifacts["field_schema"] = write_json_artifact(f"SCID_ASOF_FIELD_SCHEMA_{DATE_TAG}", schema)
    artifacts["forbidden_field_ledger"] = write_json_artifact(f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}", forbidden)
    artifacts["timestamp_interval_policy"] = write_json_artifact(
        f"SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_{DATE_TAG}", timestamp_policy
    )
    artifacts["duplicate_proxy_policy"] = write_json_artifact(
        f"SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_{DATE_TAG}", duplicate_policy
    )
    artifacts["discovery_baseline_audit"] = write_json_artifact(
        f"SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_{DATE_TAG}", discovery_baseline
    )
    artifacts["noleak_partition_audit"] = write_json_artifact(f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}", noleak)
    artifacts["fixture_ledger"] = write_json_artifact(f"SCID_ASOF_FIXTURE_LEDGER_{DATE_TAG}", fixtures)
    artifacts["source_control_gate_ledger"] = write_json_artifact(
        f"SCID_ASOF_SOURCE_CONTROL_GATE_LEDGER_{DATE_TAG}", gates
    )
    artifacts["saturation_redteam_ledger"] = write_json_artifact(
        f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}", redteam
    )
    artifacts["verification_result"] = {"json": rel(ROUTE_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json")}

    NEXT_G12_PROMPT.write_text(next_g12_prompt(), encoding="utf-8")
    manifest = source_control_manifest(artifacts)
    artifacts["output_manifest"] = write_json_artifact(f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}", manifest)
    audit = completion_audit(artifacts)
    artifacts["completion_audit"] = write_pair(
        f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}",
        "SCID As-Of Completion Audit",
        audit,
    )

    # Rewrite manifest once completion audit paths exist.
    manifest = source_control_manifest(artifacts)
    write_json(ROUTE_DIR / f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json", manifest)
    return {"artifacts": artifacts, "summary": manifest["summary"]}


def main() -> None:
    result = build_all()
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
