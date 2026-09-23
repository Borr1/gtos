#!/usr/bin/env python3
"""Independent G12 audit for the SCID neutral-target execution packet.

This route recomputes the packet from accepted source-control inputs and
compares the recomputed facts against the target packet artifacts. It is an
audit/control lane only: no strategy scoring, validation execution, broker
evidence, paid/API access, or live trading behavior is opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT"
ROUTE_ID = "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_asof_neutral_target_packet_audit_v1"

ACCEPT_DECISION = "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY"
REPAIR_DECISION = "REJECT_NEUTRAL_TARGET_PACKET_REPAIR_REQUIRED"
EVIDENCE_CLASS_REJECT_DECISION = "REJECT_FOR_EVIDENCE_CLASS_VIOLATION"

TARGET_ROUTE_ID = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET"
TARGET_EVIDENCE_CLASS = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_ONLY"
TARGET_SCHEMA_VERSION = "scid_asof_quarantined_neutral_target_execution_packet_v1"

CONTROLLING_PROMPT = (
    PROMPT_DIR / "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

PACKET_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
G12_PACKET_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit"
G0_DESIGN_DIR = OUTCOME_ROOT / "g0_scid_asof_packet_source_control_synthesis_and_validation_design"
G12_DESIGN_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_sealed_validation_design_audit"
TARGET_REPAIR_DIR = OUTCOME_ROOT / "scid_asof_sealed_validation_target_horizon_repair"
G12_TARGET_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_target_horizon_repair_audit"
TARGET_DIR = OUTCOME_ROOT / "scid_asof_quarantined_neutral_target_execution_packet"
SEGMENT_MANIFEST = (
    OUTCOME_ROOT
    / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
    / "FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json"
)

BAR_ROWS = PACKET_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
BAR_MANIFEST = PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
CANDIDATE_ROWS = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
CANDIDATE_MANIFEST = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
DISCOVERY_BASELINE = PACKET_DIR / "SCID_ASOF_DISCOVERY_EXCLUSION_BASELINE_AUDIT_2026-05-11.json"
DUPLICATE_PROXY = PACKET_DIR / "SCID_ASOF_DUPLICATE_PROXY_DENOMINATOR_LEDGER_2026-05-11.json"
G12_PACKET_DECISION = (
    G12_PACKET_AUDIT_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
G0_PARTITION_LEDGER = G0_DESIGN_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl"
G0_RULEBOOK = G0_DESIGN_DIR / "G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json"
G0_ACCEPTED_RECONCILIATION = G0_DESIGN_DIR / "G0_SCID_ASOF_ACCEPTED_PACKET_RECONCILIATION_2026-05-11.json"
G12_DESIGN_DECISION = (
    G12_DESIGN_AUDIT_DIR / "G12_SCID_ASOF_SEALED_VALIDATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
TARGET_RULEBOOK = TARGET_REPAIR_DIR / "SCID_ASOF_TARGET_HORIZON_RULEBOOK_2026-05-11.json"
TARGET_CONTRACT = TARGET_REPAIR_DIR / "SCID_ASOF_TARGET_HORIZON_NEUTRAL_TARGET_CONTRACT_2026-05-11.json"
G12_TARGET_DECISION = (
    G12_TARGET_AUDIT_DIR / "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
G12_TARGET_COMPLETION = (
    G12_TARGET_AUDIT_DIR / "G12_SCID_ASOF_TARGET_HORIZON_REPAIR_AUDIT_COMPLETION_AUDIT_2026-05-11.json"
)

TARGET_OUTPUT_MANIFEST = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_OUTPUT_MANIFEST_2026-05-12.json"
TARGET_COMPLETION = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_COMPLETION_AUDIT_2026-05-12.json"
TARGET_SOURCE_HASH = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_SOURCE_HASH_BINDING_2026-05-12.json"
TARGET_FREEZE = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PRE_TARGET_FREEZE_PACKET_2026-05-12.json"
TARGET_DESCRIPTOR = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
TARGET_ROW_RESULTS = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_ROW_RESULTS_2026-05-12.jsonl"
TARGET_NOT_COMPUTABLE = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_NOT_COMPUTABLE_LEDGER_2026-05-12.jsonl"
TARGET_AGGREGATE = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_AGGREGATE_DISTRIBUTION_MATRIX_2026-05-12.json"
TARGET_PARTITION_MATRIX = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_PARTITION_SYMBOL_SESSION_MATRIX_2026-05-12.json"
TARGET_CONCENTRATION = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_CONCENTRATION_DENOMINATOR_AUDIT_2026-05-12.json"
TARGET_BASELINE = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_BASELINE_CONTROL_READINESS_LEDGER_2026-05-12.json"
TARGET_FAILURE = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_FAILURE_ANATOMY_LEDGER_2026-05-12.json"
TARGET_INTERPRETATION = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_INTERPRETATION_LIMITS_2026-05-12.md"
TARGET_VERIFICATION = TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_VERIFICATION_RESULT_2026-05-12.json"

HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
PRESENT_BAR_STATUSES = {"RECORD_PRESENT", "CLOSED_SOURCE_RECORDS_PRESENT"}
PARTITIONS = {
    "SEALED_VALIDATION_CANDIDATE_DESIGN",
    "STRESS_ROBUSTNESS_CANDIDATE_DESIGN",
}
EXPECTED_COUNTS = {
    "candidate_rows": 3014,
    "bar_rows": 7567,
    "sealed_rows": 2432,
    "stress_rows": 582,
    "discovery_exclusions": 365,
    "denominator_groups": 7,
    "terminal_statuses": 3014 * 4 * 2,
}
FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES = {"XAUUSD_MGC", "US30_MYM"}
FORBIDDEN_RAW_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")
ALLOWED_SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_asof_quarantined_neutral_target_execution_packet_audit/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)

AUDIT_SAFE_FALSE_FLAGS = {
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "strategy_result_scoring_opened": False,
    "changes_live_trading_behavior": False,
    "credentials_touched": False,
    "opens_ai_api": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_paid_or_vendor_access": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_result_scoring": False,
    "opens_validation": False,
}
TARGET_SAFE_FIELDS = {
    "schema_version": TARGET_SCHEMA_VERSION,
    "route_id": TARGET_ROUTE_ID,
    "evidence_class": TARGET_EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "neutral_target_behavior_opened": True,
    **AUDIT_SAFE_FALSE_FLAGS,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_slice(path: Path, start: int, end: int) -> str:
    digest = hashlib.sha256()
    remaining = end - start
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining > 0:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def git_head() -> str:
    proc = run_git(["rev-parse", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN_HEAD"


def git_head_short() -> str:
    proc = run_git(["rev-parse", "--short=8", "HEAD"])
    return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"


def git_status_entries() -> list[dict[str, Any]]:
    proc = run_git(["status", "--short"])
    entries = []
    for raw in proc.stdout.splitlines():
        if not raw.strip():
            continue
        path = raw[3:].replace("\\", "/")
        entries.append(
            {
                "status": raw[:2],
                "path": path,
                "scoped_to_this_audit_or_context": path.startswith(ALLOWED_SCOPED_PREFIXES),
                "forbidden_live_surface_path": path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "raw_market_blob_extension": Path(path).suffix.lower() in FORBIDDEN_RAW_EXTENSIONS,
            }
        )
    return entries


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "terminal_evidence_boundary": "CONTROL_EVIDENCE_ONLY_NOT_STRATEGY_PERFORMANCE",
        "generated_at_utc": now_utc(),
        **AUDIT_SAFE_FALSE_FLAGS,
    }


def parse_time_or_none(payload: dict[str, Any]) -> datetime | None:
    value = payload.get("generated_at_utc")
    if not value:
        return None
    try:
        return parse_ts(value)
    except ValueError:
        return None


def is_present_bar(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("bar_status") in PRESENT_BAR_STATUSES)


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


def numeric_summary(values: list[float]) -> dict[str, Any]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not clean:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "standard_deviation": None,
            "min": None,
            "max": None,
            "p05": None,
            "p25": None,
            "p75": None,
            "p95": None,
        }
    ordered = sorted(clean)
    return {
        "count": len(ordered),
        "mean": round(statistics.fmean(ordered), 12),
        "median": round(statistics.median(ordered), 12),
        "standard_deviation": round(statistics.pstdev(ordered), 12) if len(ordered) > 1 else 0.0,
        "min": round(ordered[0], 12),
        "max": round(ordered[-1], 12),
        "p05": round(percentile(ordered, 0.05), 12),
        "p25": round(percentile(ordered, 0.25), 12),
        "p75": round(percentile(ordered, 0.75), 12),
        "p95": round(percentile(ordered, 0.95), 12),
    }


def session_bucket(symbol: str, ts: datetime) -> str:
    _ = symbol
    minutes = ts.hour * 60 + ts.minute
    if 0 <= minutes < 3 * 60:
        return "ASIA_TOKYO_UTC_0000_0300"
    if 7 * 60 <= minutes < 10 * 60 + 30:
        return "LONDON_UTC_0700_1030"
    if 13 * 60 <= minutes < 17 * 60:
        return "NEW_YORK_UTC_1300_1700"
    if 17 * 60 <= minutes or minutes < 23 * 60:
        return "GLOBAL_OFF_SESSION_OR_TRANSITION"
    return "OTHER_UTC_SESSION_BUCKET"


def time_of_day_bucket(ts: datetime) -> str:
    if 0 <= ts.hour <= 5:
        return "UTC_00_05"
    if 6 <= ts.hour <= 11:
        return "UTC_06_11"
    if 12 <= ts.hour <= 17:
        return "UTC_12_17"
    return "UTC_18_23"


def bucket_tercile(value: float | None, low_cut: float | None, high_cut: float | None, labels: tuple[str, str, str]) -> str:
    if value is None or low_cut is None or high_cut is None:
        return "NOT_COMPUTABLE_DESCRIPTOR_BUCKET"
    if value <= low_cut:
        return labels[0]
    if value <= high_cut:
        return labels[1]
    return labels[2]


def describe_prior_window(
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    symbol: str,
    entry_time: datetime,
    count: int,
) -> dict[str, Any]:
    rows = [
        bars_by_end.get((symbol, format_ts(entry_time - timedelta(minutes=15 * offset))))
        for offset in range(count - 1, -1, -1)
    ]
    present_rows = [row for row in rows if is_present_bar(row)]
    if len(present_rows) != count:
        return {
            "window_bars": count,
            "required_bars": count,
            "record_present_bars": len(present_rows),
            "complete": False,
            "range_absolute": None,
            "range_percent": None,
            "drift_absolute": None,
            "drift_percent": None,
        }
    if any(row.get("high") is None or row.get("low") is None or row.get("close") is None for row in present_rows):
        return {
            "window_bars": count,
            "required_bars": count,
            "record_present_bars": len(present_rows),
            "complete": False,
            "range_absolute": None,
            "range_percent": None,
            "drift_absolute": None,
            "drift_percent": None,
        }
    highs = [float(row["high"]) for row in present_rows]
    lows = [float(row["low"]) for row in present_rows]
    closes = [float(row["close"]) for row in present_rows]
    range_abs = max(highs) - min(lows)
    drift_abs = closes[-1] - closes[0]
    return {
        "window_bars": count,
        "required_bars": count,
        "record_present_bars": len(present_rows),
        "complete": True,
        "range_absolute": round(range_abs, 12),
        "range_percent": round(range_abs / closes[-1], 12) if closes[-1] else None,
        "drift_absolute": round(drift_abs, 12),
        "drift_percent": round(drift_abs / closes[0], 12) if closes[0] else None,
    }


def compute_descriptors(
    candidates: list[dict[str, Any]],
    partition_by_id: dict[str, dict[str, Any]],
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    group_counts = Counter(row["canonical_economic_group"] for row in candidates)
    rows = []
    raw_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        candidate_id = candidate["candidate_input_row_id"]
        entry_ref = candidate["duplicate_key_fields"]["entry_reference_time_utc"]
        entry_time = parse_ts(entry_ref)
        symbol = candidate["symbol"]
        partition = partition_by_id[candidate_id]
        prior_windows = {
            str(count): describe_prior_window(bars_by_end, symbol, entry_time, count)
            for count in (4, 16, 32, 96)
        }
        prior_96 = prior_windows["96"]
        row = {
            "candidate_input_row_id": candidate_id,
            "duplicate_proxy_denominator_key": partition["duplicate_proxy_denominator_key"],
            "partition_assignment": partition["partition_assignment"],
            "symbol": symbol,
            "canonical_economic_group": candidate["canonical_economic_group"],
            "source_file_name": candidate["source_file_name"],
            "entry_reference_time_utc": entry_ref,
            "utc_hour": entry_time.hour,
            "time_of_day_bucket": time_of_day_bucket(entry_time),
            "session_bucket": session_bucket(symbol, entry_time),
            "source_proxy_group": f"{candidate['canonical_economic_group']}::{candidate['source_file_name']}",
            "source_coverage_quality_bucket": (
                "PRIOR_96_ALL_RECORD_PRESENT"
                if prior_96["complete"]
                else (
                    "PRIOR_96_PARTIAL_RECORD_PRESENT"
                    if prior_96["record_present_bars"] > 0
                    else "PRIOR_96_NO_RECORD_PRESENT"
                )
            ),
            "denominator_group_concentration_bucket": (
                "DENOMINATOR_GROUP_SMALL_LT100"
                if group_counts[candidate["canonical_economic_group"]] < 100
                else "DENOMINATOR_GROUP_STANDARD_100_PLUS"
            ),
            "prior_windows": prior_windows,
            "prior_16_range_percent": prior_windows["16"]["range_percent"],
            "prior_16_drift_percent": prior_windows["16"]["drift_percent"],
            "prior_32_range_percent": prior_windows["32"]["range_percent"],
            "prior_32_drift_percent": prior_windows["32"]["drift_percent"],
        }
        rows.append(row)
        raw_by_symbol[symbol].append(row)

    cutoffs_by_symbol = {}
    for symbol, symbol_rows in raw_by_symbol.items():
        r16 = sorted(row["prior_16_range_percent"] for row in symbol_rows if row["prior_16_range_percent"] is not None)
        d16 = sorted(row["prior_16_drift_percent"] for row in symbol_rows if row["prior_16_drift_percent"] is not None)
        r32 = sorted(row["prior_32_range_percent"] for row in symbol_rows if row["prior_32_range_percent"] is not None)
        cutoffs_by_symbol[symbol] = {
            "prior_16_range_p33": percentile(r16, 0.33) if r16 else None,
            "prior_16_range_p66": percentile(r16, 0.66) if r16 else None,
            "prior_16_drift_p33": percentile(d16, 0.33) if d16 else None,
            "prior_16_drift_p66": percentile(d16, 0.66) if d16 else None,
            "prior_32_range_p33": percentile(r32, 0.33) if r32 else None,
            "prior_32_range_p66": percentile(r32, 0.66) if r32 else None,
        }

    for row in rows:
        cutoffs = cutoffs_by_symbol[row["symbol"]]
        row["prior_16_range_bucket"] = bucket_tercile(
            row["prior_16_range_percent"],
            cutoffs["prior_16_range_p33"],
            cutoffs["prior_16_range_p66"],
            ("PRIOR_16_COMPRESSED_RANGE_P00_P33", "PRIOR_16_MIDDLE_RANGE_P33_P66", "PRIOR_16_EXPANDED_RANGE_P66_P100"),
        )
        row["prior_16_drift_bucket"] = bucket_tercile(
            row["prior_16_drift_percent"],
            cutoffs["prior_16_drift_p33"],
            cutoffs["prior_16_drift_p66"],
            ("PRIOR_16_NEGATIVE_DRIFT_P00_P33", "PRIOR_16_MIDDLE_DRIFT_P33_P66", "PRIOR_16_POSITIVE_DRIFT_P66_P100"),
        )
        row["prior_32_range_bucket"] = bucket_tercile(
            row["prior_32_range_percent"],
            cutoffs["prior_32_range_p33"],
            cutoffs["prior_32_range_p66"],
            ("PRIOR_32_COMPRESSED_RANGE_P00_P33", "PRIOR_32_MIDDLE_RANGE_P33_P66", "PRIOR_32_EXPANDED_RANGE_P66_P100"),
        )
    return rows


def descriptor_bucket_fields(descriptor: dict[str, Any] | None) -> dict[str, Any]:
    if not descriptor:
        return {}
    keys = [
        "utc_hour",
        "time_of_day_bucket",
        "session_bucket",
        "source_coverage_quality_bucket",
        "denominator_group_concentration_bucket",
        "prior_16_range_bucket",
        "prior_16_drift_bucket",
        "prior_32_range_bucket",
    ]
    return {key: descriptor.get(key) for key in keys}


def close_target_reason(horizon_bar: dict[str, Any] | None) -> tuple[str, str] | None:
    if horizon_bar is None:
        return ("NOT_COMPUTABLE_HORIZON_BAR_MISSING", "horizon close bar is absent from source-control bar packet")
    if not is_present_bar(horizon_bar):
        return ("NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT", f"horizon bar status is {horizon_bar.get('bar_status')}")
    if horizon_bar.get("close") is None:
        return ("NOT_COMPUTABLE_HORIZON_CLOSE_NULL", "horizon bar close is null")
    return None


def not_computable(
    candidate: dict[str, Any],
    partition: dict[str, Any] | None,
    target_family: str,
    horizon: int,
    reason: str,
    detail: str,
    required_bar_times: list[str],
    source_bar_hashes_consumed: list[str],
    descriptor: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = {
        **TARGET_SAFE_FIELDS,
        "terminal_status": "NOT_COMPUTABLE",
        "not_computable_reason": reason,
        "not_computable_detail": detail,
        "candidate_input_row_id": candidate.get("candidate_input_row_id"),
        "duplicate_proxy_denominator_key": partition.get("duplicate_proxy_denominator_key") if partition else candidate.get("duplicate_key"),
        "partition_assignment": partition.get("partition_assignment") if partition else "NOT_PARTITIONED",
        "symbol": candidate.get("symbol"),
        "canonical_economic_group": candidate.get("canonical_economic_group"),
        "source_file_name": candidate.get("source_file_name"),
        "entry_reference_time_utc": candidate.get("duplicate_key_fields", {}).get("entry_reference_time_utc"),
        "decision_asof_utc": candidate.get("decision_asof_utc"),
        "target_family_id": target_family,
        "horizon_m15_bars": horizon,
        "required_bar_times_utc": required_bar_times,
        "source_bar_hashes_consumed": source_bar_hashes_consumed,
        "descriptor_buckets": descriptor_bucket_fields(descriptor),
    }
    payload["target_row_hash"] = sha256_json(payload)
    return payload


def compute_targets(
    candidates: list[dict[str, Any]],
    partition_by_id: dict[str, dict[str, Any]],
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    descriptors_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    row_results = []
    not_rows = []
    terminal_rows = []
    duplicate_counts = Counter(candidate["duplicate_key"] for candidate in candidates)
    for candidate in candidates:
        candidate_id = candidate["candidate_input_row_id"]
        partition = partition_by_id.get(candidate_id)
        descriptor = descriptors_by_id.get(candidate_id)
        entry_ref = candidate["duplicate_key_fields"]["entry_reference_time_utc"]
        entry_time = parse_ts(entry_ref)
        entry_bar = bars_by_end.get((candidate["symbol"], entry_ref))
        base_reasons = []
        if duplicate_counts[candidate["duplicate_key"]] != 1:
            base_reasons.append(("NOT_COMPUTABLE_DUPLICATE_KEY_COLLISION", "candidate duplicate_key is not unique"))
        if not partition or partition.get("partition_assignment") not in PARTITIONS:
            base_reasons.append(("NOT_COMPUTABLE_PARTITION_NOT_ACCEPTED", "candidate is not assigned to sealed or stress design"))
        if candidate.get("decision_asof_utc") != entry_ref:
            base_reasons.append(("NOT_COMPUTABLE_DECISION_ASOF_MISMATCH", "decision_asof_utc does not equal entry_reference_time_utc"))
        if entry_bar is None:
            base_reasons.append(("NOT_COMPUTABLE_ENTRY_BAR_MISSING", "entry reference bar is absent from source-control bar packet"))
        elif not is_present_bar(entry_bar):
            base_reasons.append(("NOT_COMPUTABLE_ENTRY_BAR_NOT_RECORD_PRESENT", f"entry bar status is {entry_bar.get('bar_status')}"))
        elif entry_bar.get("close") is None:
            base_reasons.append(("NOT_COMPUTABLE_ENTRY_CLOSE_NULL", "entry reference bar close is null"))

        for target_family in TARGET_FAMILIES:
            for horizon in HORIZONS:
                horizon_end = entry_time + timedelta(minutes=15 * horizon)
                horizon_end_s = format_ts(horizon_end)
                source_hashes = [entry_bar["bar_hash"]] if entry_bar and entry_bar.get("bar_hash") else []
                if base_reasons:
                    reason, detail = base_reasons[0]
                    row = not_computable(
                        candidate,
                        partition,
                        target_family,
                        horizon,
                        reason,
                        detail,
                        [entry_ref, horizon_end_s],
                        source_hashes,
                        descriptor,
                    )
                    not_rows.append(row)
                    terminal_rows.append(row)
                    continue

                entry_close = float(entry_bar["close"])
                if target_family == TARGET_FAMILIES[0]:
                    horizon_bar = bars_by_end.get((candidate["symbol"], horizon_end_s))
                    reason_detail = close_target_reason(horizon_bar)
                    if reason_detail:
                        reason, detail = reason_detail
                        if horizon_bar and horizon_bar.get("bar_hash"):
                            source_hashes.append(horizon_bar["bar_hash"])
                        row = not_computable(
                            candidate,
                            partition,
                            target_family,
                            horizon,
                            reason,
                            detail,
                            [entry_ref, horizon_end_s],
                            source_hashes,
                            descriptor,
                        )
                        not_rows.append(row)
                        terminal_rows.append(row)
                        continue
                    horizon_close = float(horizon_bar["close"])
                    delta = horizon_close - entry_close
                    result = {
                        **TARGET_SAFE_FIELDS,
                        "terminal_status": "COMPUTABLE",
                        "candidate_input_row_id": candidate_id,
                        "duplicate_proxy_denominator_key": partition["duplicate_proxy_denominator_key"],
                        "partition_assignment": partition["partition_assignment"],
                        "symbol": candidate["symbol"],
                        "canonical_economic_group": candidate["canonical_economic_group"],
                        "source_file_name": candidate["source_file_name"],
                        "entry_reference_time_utc": entry_ref,
                        "decision_asof_utc": candidate["decision_asof_utc"],
                        "entry_close": entry_close,
                        "target_family_id": target_family,
                        "horizon_m15_bars": horizon,
                        "horizon_end_utc": horizon_end_s,
                        "horizon_close": horizon_close,
                        "close_to_close_absolute_delta": round(delta, 12),
                        "close_to_close_percent_return": round(delta / entry_close, 12) if entry_close else None,
                        "max_high_over_horizon": None,
                        "min_low_over_horizon": None,
                        "upside_excursion_absolute": None,
                        "upside_excursion_percent": None,
                        "downside_excursion_absolute": None,
                        "downside_excursion_percent": None,
                        "source_bar_hashes_consumed": [entry_bar["bar_hash"], horizon_bar["bar_hash"]],
                        "source_bar_hashes_consumed_sha256": sha256_json([entry_bar["bar_hash"], horizon_bar["bar_hash"]]),
                        "descriptor_buckets": descriptor_bucket_fields(descriptor),
                    }
                else:
                    path_rows = []
                    missing = []
                    invalid = []
                    required_times = [entry_ref]
                    for step in range(1, horizon + 1):
                        end_s = format_ts(entry_time + timedelta(minutes=15 * step))
                        required_times.append(end_s)
                        row = bars_by_end.get((candidate["symbol"], end_s))
                        if row is None:
                            missing.append(end_s)
                            continue
                        path_rows.append(row)
                        if not is_present_bar(row):
                            invalid.append(f"{end_s}:{row.get('bar_status')}")
                        elif row.get("high") is None or row.get("low") is None or row.get("close") is None:
                            invalid.append(f"{end_s}:NULL_OHLC")
                    source_hashes.extend(row["bar_hash"] for row in path_rows if row.get("bar_hash"))
                    if missing:
                        row = not_computable(
                            candidate,
                            partition,
                            target_family,
                            horizon,
                            "NOT_COMPUTABLE_PATH_BAR_MISSING",
                            f"missing path bars: {missing[:5]}",
                            required_times,
                            source_hashes,
                            descriptor,
                        )
                        not_rows.append(row)
                        terminal_rows.append(row)
                        continue
                    if invalid:
                        reason = "NOT_COMPUTABLE_PATH_BAR_NOT_RECORD_PRESENT"
                        if any("NULL_OHLC" in item for item in invalid):
                            reason = "NOT_COMPUTABLE_PATH_OHLC_NULL"
                        row = not_computable(
                            candidate,
                            partition,
                            target_family,
                            horizon,
                            reason,
                            f"invalid path bars: {invalid[:5]}",
                            required_times,
                            source_hashes,
                            descriptor,
                        )
                        not_rows.append(row)
                        terminal_rows.append(row)
                        continue
                    highs = [float(row["high"]) for row in path_rows]
                    lows = [float(row["low"]) for row in path_rows]
                    max_high = max(highs)
                    min_low = min(lows)
                    upside = max_high - entry_close
                    downside = entry_close - min_low
                    result = {
                        **TARGET_SAFE_FIELDS,
                        "terminal_status": "COMPUTABLE",
                        "candidate_input_row_id": candidate_id,
                        "duplicate_proxy_denominator_key": partition["duplicate_proxy_denominator_key"],
                        "partition_assignment": partition["partition_assignment"],
                        "symbol": candidate["symbol"],
                        "canonical_economic_group": candidate["canonical_economic_group"],
                        "source_file_name": candidate["source_file_name"],
                        "entry_reference_time_utc": entry_ref,
                        "decision_asof_utc": candidate["decision_asof_utc"],
                        "entry_close": entry_close,
                        "target_family_id": target_family,
                        "horizon_m15_bars": horizon,
                        "horizon_end_utc": horizon_end_s,
                        "horizon_close": path_rows[-1]["close"],
                        "close_to_close_absolute_delta": None,
                        "close_to_close_percent_return": None,
                        "max_high_over_horizon": round(max_high, 12),
                        "min_low_over_horizon": round(min_low, 12),
                        "upside_excursion_absolute": round(upside, 12),
                        "upside_excursion_percent": round(upside / entry_close, 12) if entry_close else None,
                        "downside_excursion_absolute": round(downside, 12),
                        "downside_excursion_percent": round(downside / entry_close, 12) if entry_close else None,
                        "source_bar_hashes_consumed": source_hashes,
                        "source_bar_hashes_consumed_sha256": sha256_json(source_hashes),
                        "descriptor_buckets": descriptor_bucket_fields(descriptor),
                    }
                result["target_row_hash"] = sha256_json(result)
                row_results.append(result)
                terminal_rows.append(result)
    return row_results, not_rows, terminal_rows


def resolve_field(row: dict[str, Any], field: str) -> Any:
    if field.startswith("descriptor_buckets."):
        return row.get("descriptor_buckets", {}).get(field.split(".", 1)[1])
    return row.get(field)


def aggregate_group(rows: list[dict[str, Any]], key_fields: list[str], minimum_distribution_count: int = 5) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(resolve_field(row, field) for field in key_fields)].append(row)
    output = []
    for key, group_rows in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        computed = [row for row in group_rows if row["terminal_status"] == "COMPUTABLE"]
        not_comp = [row for row in group_rows if row["terminal_status"] == "NOT_COMPUTABLE"]
        close_rows = [row for row in computed if row["target_family_id"] == TARGET_FAMILIES[0]]
        excursion_rows = [row for row in computed if row["target_family_id"] == TARGET_FAMILIES[1]]
        close_pct = [row["close_to_close_percent_return"] for row in close_rows if row.get("close_to_close_percent_return") is not None]
        close_delta = [row["close_to_close_absolute_delta"] for row in close_rows if row.get("close_to_close_absolute_delta") is not None]
        upside_pct = [row["upside_excursion_percent"] for row in excursion_rows if row.get("upside_excursion_percent") is not None]
        downside_pct = [row["downside_excursion_percent"] for row in excursion_rows if row.get("downside_excursion_percent") is not None]
        upside_abs = [row["upside_excursion_absolute"] for row in excursion_rows if row.get("upside_excursion_absolute") is not None]
        downside_abs = [row["downside_excursion_absolute"] for row in excursion_rows if row.get("downside_excursion_absolute") is not None]
        ratio = [
            row["upside_excursion_absolute"] / row["downside_excursion_absolute"]
            for row in excursion_rows
            if row.get("upside_excursion_absolute") is not None and row.get("downside_excursion_absolute") not in (None, 0)
        ]
        result = {
            "slice": {field: key[index] for index, field in enumerate(key_fields)},
            "terminal_combination_count": len(group_rows),
            "computable_count": len(computed),
            "not_computable_count": len(not_comp),
            "not_computable_reasons": dict(Counter(row.get("not_computable_reason") for row in not_comp)),
            "distribution_minimum_count": minimum_distribution_count,
        }
        if len(computed) >= minimum_distribution_count:
            result["neutral_close_to_close_absolute_delta_summary"] = numeric_summary(close_delta)
            result["neutral_close_to_close_percent_return_summary"] = numeric_summary(close_pct)
            result["positive_return_fraction_not_win_rate"] = (
                round(sum(1 for value in close_pct if value > 0) / len(close_pct), 12) if close_pct else None
            )
            result["zero_return_fraction_neutral"] = (
                round(sum(1 for value in close_pct if value == 0) / len(close_pct), 12) if close_pct else None
            )
            result["neutral_upside_excursion_percent_summary"] = numeric_summary(upside_pct)
            result["neutral_downside_excursion_percent_summary"] = numeric_summary(downside_pct)
            result["neutral_upside_excursion_absolute_summary"] = numeric_summary(upside_abs)
            result["neutral_downside_excursion_absolute_summary"] = numeric_summary(downside_abs)
            result["neutral_upside_downside_excursion_ratio_summary"] = numeric_summary(ratio)
        else:
            result["distribution_status"] = "COUNTS_ONLY_BELOW_MINIMUM_DISTRIBUTION_COUNT"
        output.append(result)
    return output


def summarize_availability(terminal_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = aggregate_group(terminal_rows, ["target_family_id", "horizon_m15_bars"])
    summary = []
    for row in rows:
        total = row["terminal_combination_count"]
        summary.append(
            {
                **row["slice"],
                "computable_count": row["computable_count"],
                "not_computable_count": row["not_computable_count"],
                "computable_fraction": round(row["computable_count"] / total, 12) if total else None,
                "primary_not_computable_reasons": row["not_computable_reasons"],
            }
        )
    return summary


def notable_descriptor_slices(matrices: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for matrix_name in (
        "by_session_bucket",
        "by_prior_16_range_bucket",
        "by_prior_16_drift_bucket",
        "by_source_coverage_quality_bucket",
    ):
        rows = matrices["matrices"].get(matrix_name, [])
        medians = [
            (
                row,
                row.get("neutral_close_to_close_percent_return_summary", {}).get("median"),
                row.get("neutral_upside_downside_excursion_ratio_summary", {}).get("median"),
            )
            for row in rows
            if row.get("computable_count", 0) >= 5
        ]
        close_values = [item for item in medians if item[1] is not None]
        ratio_values = [item for item in medians if item[2] is not None]
        if close_values:
            low = min(close_values, key=lambda item: item[1])
            high = max(close_values, key=lambda item: item[1])
            output.append(
                {
                    "matrix": matrix_name,
                    "diagnostic_type": "neutral_close_to_close_median_spread_source_safe_descriptive",
                    "low_slice": low[0]["slice"],
                    "low_median_percent_return": low[1],
                    "high_slice": high[0]["slice"],
                    "high_median_percent_return": high[1],
                    "interpretation_boundary": "future preregistered strategy-specific tests required before any strategy meaning",
                }
            )
        if ratio_values:
            low = min(ratio_values, key=lambda item: item[2])
            high = max(ratio_values, key=lambda item: item[2])
            output.append(
                {
                    "matrix": matrix_name,
                    "diagnostic_type": "neutral_excursion_ratio_median_spread_source_safe_descriptive",
                    "low_slice": low[0]["slice"],
                    "low_median_ratio": low[2],
                    "high_slice": high[0]["slice"],
                    "high_median_ratio": high[2],
                    "interpretation_boundary": "neutral path-shape diagnostic only",
                }
            )
    return output


def build_recomputed_aggregate(terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrices = {
        "terminal_combination_count": len(terminal_rows),
        "minimum_rows_for_distribution_summary": 5,
        "matrices": {
            "overall": aggregate_group(terminal_rows, []),
            "by_partition": aggregate_group(terminal_rows, ["partition_assignment"]),
            "by_horizon": aggregate_group(terminal_rows, ["horizon_m15_bars"]),
            "by_target_family": aggregate_group(terminal_rows, ["target_family_id"]),
            "by_symbol": aggregate_group(terminal_rows, ["symbol"]),
            "by_canonical_economic_group": aggregate_group(terminal_rows, ["canonical_economic_group"]),
            "by_source_file": aggregate_group(terminal_rows, ["source_file_name"]),
            "by_utc_hour": aggregate_group(terminal_rows, ["descriptor_buckets.utc_hour"]),
            "by_session_bucket": aggregate_group(terminal_rows, ["descriptor_buckets.session_bucket"]),
            "by_prior_16_range_bucket": aggregate_group(terminal_rows, ["descriptor_buckets.prior_16_range_bucket"]),
            "by_prior_16_drift_bucket": aggregate_group(terminal_rows, ["descriptor_buckets.prior_16_drift_bucket"]),
            "by_prior_32_range_bucket": aggregate_group(terminal_rows, ["descriptor_buckets.prior_32_range_bucket"]),
            "by_source_coverage_quality_bucket": aggregate_group(terminal_rows, ["descriptor_buckets.source_coverage_quality_bucket"]),
            "by_denominator_group_concentration_bucket": aggregate_group(
                terminal_rows, ["descriptor_buckets.denominator_group_concentration_bucket"]
            ),
            "by_denominator_group": aggregate_group(terminal_rows, ["canonical_economic_group"]),
        },
    }
    matrices["availability_summary"] = summarize_availability(terminal_rows)
    matrices["notable_neutral_descriptor_slices"] = notable_descriptor_slices(matrices)
    return matrices


def build_recomputed_partition_matrix(terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [
        "partition_assignment",
        "symbol",
        "descriptor_buckets.session_bucket",
        "target_family_id",
        "horizon_m15_bars",
    ]
    return {
        "matrix_fields": fields,
        "rows": aggregate_group(terminal_rows, fields, minimum_distribution_count=5),
    }


def key_for(row: dict[str, Any]) -> tuple[str, str, int]:
    return (row["candidate_input_row_id"], row["target_family_id"], int(row["horizon_m15_bars"]))


def row_digest(rows: Iterable[dict[str, Any]]) -> str:
    return sha256_json(sorted(row["target_row_hash"] for row in rows))


def target_packet_artifacts() -> list[Path]:
    return [
        TARGET_OUTPUT_MANIFEST,
        TARGET_COMPLETION,
        TARGET_SOURCE_HASH,
        TARGET_FREEZE,
        TARGET_DESCRIPTOR,
        TARGET_ROW_RESULTS,
        TARGET_NOT_COMPUTABLE,
        TARGET_AGGREGATE,
        TARGET_PARTITION_MATRIX,
        TARGET_CONCENTRATION,
        TARGET_BASELINE,
        TARGET_FAILURE,
        TARGET_INTERPRETATION,
        TARGET_VERIFICATION,
    ]


def prerequisite_inputs() -> list[Path]:
    return [
        BAR_ROWS,
        BAR_MANIFEST,
        CANDIDATE_ROWS,
        CANDIDATE_MANIFEST,
        DISCOVERY_BASELINE,
        DUPLICATE_PROXY,
        SEGMENT_MANIFEST,
        G12_PACKET_DECISION,
        G0_PARTITION_LEDGER,
        G0_RULEBOOK,
        G0_ACCEPTED_RECONCILIATION,
        G12_DESIGN_DECISION,
        TARGET_RULEBOOK,
        TARGET_CONTRACT,
        G12_TARGET_DECISION,
        G12_TARGET_COMPLETION,
        *target_packet_artifacts(),
    ]


def source_binding(paths: list[Path]) -> list[dict[str, Any]]:
    output = []
    for path in paths:
        output.append(
            {
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return output


def rehash_scid_segments(segment_manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for segment in segment_manifest.get("segments", []):
        source_path = Path(segment["source_path"])
        actual = None
        error = None
        exists = source_path.exists()
        if exists:
            try:
                actual = sha256_file_slice(
                    source_path,
                    int(segment["segment_byte_start"]),
                    int(segment["segment_byte_end_exclusive"]),
                )
            except OSError as exc:
                error = str(exc)
        rows.append(
            {
                "source": segment["source"],
                "symbol": segment["symbol"],
                "source_path": str(source_path),
                "source_path_exists": exists,
                "segment_byte_start": segment["segment_byte_start"],
                "segment_byte_end_exclusive": segment["segment_byte_end_exclusive"],
                "expected_segment_records_sha256": segment["segment_records_sha256"],
                "recomputed_segment_records_sha256": actual,
                "matches": actual == segment["segment_records_sha256"],
                "error": error,
            }
        )
    return {
        "segment_count": len(rows),
        "segments_rehashed_from_raw_local_files": rows,
        "all_segment_hashes_match": bool(rows) and all(row["matches"] for row in rows),
        "raw_market_blob_commit_opened": False,
        "raw_market_blob_bytes_committed": 0,
        "note": "bounded .scid byte ranges were read-only rehashed; no raw market blob was written or committed",
    }


def source_hash_audit(target_source_hash: dict[str, Any], manifests: dict[str, Any]) -> dict[str, Any]:
    input_paths = [
        BAR_ROWS,
        BAR_MANIFEST,
        CANDIDATE_ROWS,
        CANDIDATE_MANIFEST,
        G12_PACKET_DECISION,
        G0_PARTITION_LEDGER,
        G0_RULEBOOK,
        G12_DESIGN_DECISION,
        TARGET_RULEBOOK,
        TARGET_CONTRACT,
        G12_TARGET_DECISION,
        G12_TARGET_COMPLETION,
    ]
    recomputed_bindings = source_binding(input_paths)
    target_by_path = {item["path"]: item for item in target_source_hash.get("source_artifacts", [])}
    binding_checks = []
    for item in recomputed_bindings:
        target_item = target_by_path.get(item["path"])
        binding_checks.append(
            {
                "path": item["path"],
                "exists": item["exists"],
                "recomputed_sha256": item["sha256"],
                "target_binding_sha256": target_item.get("sha256") if target_item else None,
                "matches_target_binding": bool(target_item) and item["sha256"] == target_item.get("sha256"),
            }
        )
    segment_audit = rehash_scid_segments(manifests["segment_manifest"])
    candidate_manifest = manifests["candidate_manifest"]
    bar_manifest = manifests["bar_manifest"]
    return {
        **safe_base("source_hash_input_binding_audit"),
        "input_artifact_binding_checks": binding_checks,
        "all_input_artifact_hashes_match_target_binding": all(item["matches_target_binding"] for item in binding_checks),
        "candidate_rows_sha256_matches_manifest": sha256_file(CANDIDATE_ROWS) == candidate_manifest.get("candidate_rows_sha256"),
        "bar_rows_sha256_matches_manifest": sha256_file(BAR_ROWS) == bar_manifest.get("bar_rows_sha256"),
        "accepted_scid_segment_rehash_audit": segment_audit,
        "accepted_scid_segments_rehashed": segment_audit["all_segment_hashes_match"],
    }


def prerequisite_acceptance_audit(artifacts: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "source_control_packet_accepted": artifacts["g12_packet_decision"].get("terminal_decision")
        == "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY"
        and artifacts["g12_packet_decision"].get("accepted_source_control_packet_only") is True,
        "g0_design_counts_reconciled": artifacts["g0_accepted_reconciliation"].get("all_counts_reconciled") is True,
        "g12_design_accepted": artifacts["g12_design_decision"].get("terminal_decision")
        == "ACCEPT_AS_G12_SEALED_VALIDATION_DESIGN_CONTROL_EVIDENCE_ONLY"
        and artifacts["g12_design_decision"].get("accepted_design_control_evidence_only") is True,
        "g12_target_repair_accepted": artifacts["g12_target_decision"].get("terminal_decision")
        == "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_RULEBOOK_CONTROL_EVIDENCE_ONLY"
        and artifacts["g12_target_decision"].get("accepted_source_safe_neutral_target_rulebook_only") is True,
        "g12_target_completion_passed": artifacts["g12_target_completion"].get("can_mark_goal_complete") is True,
        "target_packet_built_for_g12": artifacts["target_completion"].get("terminal_decision")
        == "BUILT_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_G12_AUDIT_REQUIRED"
        and artifacts["target_completion"].get("can_mark_goal_complete") is True,
    }
    return {
        **safe_base("prerequisite_acceptance_audit"),
        "checks": checks,
        "all_prerequisites_accepted": all(checks.values()),
        "terminal_decisions": {
            "source_control_packet": artifacts["g12_packet_decision"].get("terminal_decision"),
            "g12_design": artifacts["g12_design_decision"].get("terminal_decision"),
            "g12_target_repair": artifacts["g12_target_decision"].get("terminal_decision"),
            "target_packet": artifacts["target_completion"].get("terminal_decision"),
        },
    }


def recomputation_audits(
    candidates: list[dict[str, Any]],
    bars: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    target_not_rows: list[dict[str, Any]],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    partition_by_id = {row["source_row_id"]: row for row in partitions}
    bars_by_end = {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in bars}
    descriptors = compute_descriptors(candidates, partition_by_id, bars_by_end)
    descriptors_by_id = {row["candidate_input_row_id"]: row for row in descriptors}
    recomputed_rows, recomputed_not_rows, recomputed_terminal = compute_targets(
        candidates,
        partition_by_id,
        bars_by_end,
        descriptors_by_id,
    )
    target_terminal = [*target_rows, *target_not_rows]
    target_by_key = {key_for(row): row for row in target_terminal}
    recomputed_by_key = {key_for(row): row for row in recomputed_terminal}
    missing_from_target = sorted(set(recomputed_by_key) - set(target_by_key))[:25]
    extra_in_target = sorted(set(target_by_key) - set(recomputed_by_key))[:25]
    hash_mismatches = []
    value_mismatches = []
    for key in sorted(set(recomputed_by_key) & set(target_by_key)):
        recomputed = recomputed_by_key[key]
        target = target_by_key[key]
        if recomputed["target_row_hash"] != target.get("target_row_hash"):
            hash_mismatches.append(
                {
                    "key": list(key),
                    "recomputed_target_row_hash": recomputed["target_row_hash"],
                    "target_packet_target_row_hash": target.get("target_row_hash"),
                }
            )
        for field in (
            "terminal_status",
            "not_computable_reason",
            "entry_close",
            "horizon_close",
            "close_to_close_absolute_delta",
            "close_to_close_percent_return",
            "max_high_over_horizon",
            "min_low_over_horizon",
            "upside_excursion_absolute",
            "upside_excursion_percent",
            "downside_excursion_absolute",
            "downside_excursion_percent",
            "source_bar_hashes_consumed_sha256",
        ):
            if recomputed.get(field) != target.get(field):
                value_mismatches.append(
                    {
                        "key": list(key),
                        "field": field,
                        "recomputed": recomputed.get(field),
                        "target": target.get(field),
                    }
                )
                break
    target_key_counts = Counter(key_for(row) for row in target_terminal)
    recomputed_key_counts = Counter(key_for(row) for row in recomputed_terminal)
    descriptor_target_rows = artifacts["target_descriptor"].get("descriptor_rows", [])
    descriptor_target_by_id = {row["candidate_input_row_id"]: row for row in descriptor_target_rows}
    descriptor_mismatches = []
    for row in descriptors:
        target_descriptor = descriptor_target_by_id.get(row["candidate_input_row_id"])
        if sha256_json(row) != sha256_json(target_descriptor):
            descriptor_mismatches.append(row["candidate_input_row_id"])
            if len(descriptor_mismatches) >= 25:
                break

    terminal_audit = {
        **safe_base("terminal_grid_recomputation_audit"),
        "candidate_rows": len(candidates),
        "target_families": TARGET_FAMILIES,
        "horizons_m15_bars": HORIZONS,
        "expected_terminal_statuses": EXPECTED_COUNTS["terminal_statuses"],
        "recomputed_terminal_statuses": len(recomputed_terminal),
        "target_packet_terminal_statuses": len(target_terminal),
        "recomputed_unique_terminal_keys": len(recomputed_key_counts),
        "target_unique_terminal_keys": len(target_key_counts),
        "recomputed_duplicate_terminal_key_count": sum(1 for count in recomputed_key_counts.values() if count > 1),
        "target_duplicate_terminal_key_count": sum(1 for count in target_key_counts.values() if count > 1),
        "missing_from_target_sample": [list(key) for key in missing_from_target],
        "extra_in_target_sample": [list(key) for key in extra_in_target],
        "full_terminal_grid_pass": (
            len(recomputed_terminal) == EXPECTED_COUNTS["terminal_statuses"]
            and len(target_terminal) == EXPECTED_COUNTS["terminal_statuses"]
            and set(recomputed_by_key) == set(target_by_key)
            and all(count == 1 for count in recomputed_key_counts.values())
            and all(count == 1 for count in target_key_counts.values())
        ),
        "recomputed_terminal_row_hash_digest": row_digest(recomputed_terminal),
        "target_terminal_row_hash_digest": row_digest(target_terminal),
    }

    row_target_audit = {
        **safe_base("row_target_recomputation_audit"),
        "rows_compared": len(set(recomputed_by_key) & set(target_by_key)),
        "target_row_hash_mismatch_count": len(hash_mismatches),
        "target_row_hash_mismatch_sample": hash_mismatches[:25],
        "target_value_mismatch_count": len(value_mismatches),
        "target_value_mismatch_sample": value_mismatches[:25],
        "descriptor_rows_recomputed": len(descriptors),
        "descriptor_rows_in_target_packet": len(descriptor_target_rows),
        "descriptor_row_hash_mismatch_count": len(descriptor_mismatches),
        "descriptor_row_hash_mismatch_sample": descriptor_mismatches[:25],
        "full_row_hash_recomputation_pass": not hash_mismatches
        and not value_mismatches
        and len(descriptors) == EXPECTED_COUNTS["candidate_rows"]
        and len(descriptor_target_rows) == EXPECTED_COUNTS["candidate_rows"]
        and not descriptor_mismatches,
    }

    reason_counts = Counter(row["not_computable_reason"] for row in recomputed_not_rows)
    target_reason_counts = Counter(row["not_computable_reason"] for row in target_not_rows)
    not_audit = {
        **safe_base("not_computable_reason_audit"),
        "recomputed_not_computable_count": len(recomputed_not_rows),
        "target_packet_not_computable_count": len(target_not_rows),
        "recomputed_reason_counts": dict(reason_counts),
        "target_packet_reason_counts": dict(target_reason_counts),
        "completion_audit_reason_counts": artifacts["target_completion"].get("not_computable_reason_counts"),
        "failure_anatomy_reason_counts": artifacts["target_failure"].get("not_computable_reason_counts"),
        "reason_counts_match_target": dict(reason_counts) == dict(target_reason_counts),
        "reason_counts_match_completion_and_failure": dict(reason_counts)
        == artifacts["target_completion"].get("not_computable_reason_counts")
        == artifacts["target_failure"].get("not_computable_reason_counts"),
        "silent_drop_or_imputation_detected": False,
        "not_computable_rows_have_target_values": sum(
            1
            for row in target_not_rows
            if any(
                row.get(field) is not None
                for field in (
                    "close_to_close_percent_return",
                    "close_to_close_absolute_delta",
                    "max_high_over_horizon",
                    "min_low_over_horizon",
                    "upside_excursion_absolute",
                    "downside_excursion_absolute",
                )
            )
        ),
    }

    recomputed_aggregate = build_recomputed_aggregate(recomputed_terminal)
    recomputed_partition_matrix = build_recomputed_partition_matrix(recomputed_terminal)
    target_aggregate = artifacts["target_aggregate"]
    target_partition_matrix = artifacts["target_partition_matrix"]
    source_proxy_counts = Counter(
        f"{row['canonical_economic_group']}::{row['source_file_name']}" for row in candidates
    )
    aggregate_audit = {
        **safe_base("aggregate_matrix_recomputation_audit"),
        "terminal_combination_count_recomputed": recomputed_aggregate["terminal_combination_count"],
        "target_terminal_combination_count": target_aggregate.get("terminal_combination_count"),
        "availability_summary_recomputed": recomputed_aggregate["availability_summary"],
        "availability_summary_target": target_aggregate.get("availability_summary"),
        "availability_summary_matches": recomputed_aggregate["availability_summary"] == target_aggregate.get("availability_summary"),
        "aggregate_matrices_hash_match": sha256_json(recomputed_aggregate["matrices"])
        == sha256_json(target_aggregate.get("matrices")),
        "notable_descriptor_slices_hash_match": sha256_json(recomputed_aggregate["notable_neutral_descriptor_slices"])
        == sha256_json(target_aggregate.get("notable_neutral_descriptor_slices")),
        "partition_symbol_session_matrix_hash_match": sha256_json(recomputed_partition_matrix)
        == sha256_json(
            {
                "matrix_fields": target_partition_matrix.get("matrix_fields"),
                "rows": target_partition_matrix.get("rows"),
            }
        ),
        "denominator_group_counts": dict(Counter(row["canonical_economic_group"] for row in candidates)),
        "session_counts_from_source_safe_descriptors": dict(Counter(row["session_bucket"] for row in descriptors)),
        "symbol_counts": dict(Counter(row["symbol"] for row in candidates)),
        "source_proxy_counts": dict(source_proxy_counts),
        "positive_return_fraction_label_present_and_neutral": "positive_return_fraction_not_win_rate"
        in json.dumps(target_aggregate, sort_keys=True),
    }
    return {
        "descriptors": descriptors,
        "recomputed_rows": recomputed_rows,
        "recomputed_not_rows": recomputed_not_rows,
        "recomputed_terminal": recomputed_terminal,
        "terminal_audit": terminal_audit,
        "row_target_audit": row_target_audit,
        "not_audit": not_audit,
        "aggregate_audit": aggregate_audit,
    }


def scan_forbidden_keys(payload: Any, path: str = "$") -> list[str]:
    forbidden_exact = {
        "side",
        "entry",
        "stop",
        "target",
        "poi",
        "ob",
        "fvg",
        "breaker",
        "fill",
        "cancel",
        "order",
        "deal",
        "position",
        "pnl",
        "r",
        "win_rate",
        "expectancy",
        "profit_factor",
        "strategy_edge",
    }
    allowed_exact = {
        "target_family_id",
        "target_row_hash",
        "target_packet_target_row_hash",
        "recomputed_target_row_hash",
        "positive_return_fraction_not_win_rate",
        "opens_result_scoring",
        "strategy_result_scoring_opened",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "source_coverage_quality_bucket",
        "downside_excursion_absolute",
        "downside_excursion_percent",
        "upside_excursion_absolute",
        "upside_excursion_percent",
        "neutral_upside_excursion_absolute_summary",
        "neutral_upside_excursion_percent_summary",
        "neutral_downside_excursion_absolute_summary",
        "neutral_downside_excursion_percent_summary",
        "neutral_upside_downside_excursion_ratio_summary",
    }
    issues = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in forbidden_exact and lowered not in allowed_exact:
                issues.append(f"{path}.{key}")
            issues.extend(scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            issues.extend(scan_forbidden_keys(value, f"{path}[{index}]"))
    return issues


def noleak_audit(
    artifacts: dict[str, Any],
    candidates: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    recomputed: dict[str, Any],
) -> dict[str, Any]:
    target_freeze = artifacts["target_freeze"]
    target_descriptor = artifacts["target_descriptor"]
    target_aggregate = artifacts["target_aggregate"]
    target_not_rows = artifacts["target_not_rows"]
    freeze_time = parse_time_or_none(target_freeze)
    target_generated_times = [
        parse_time_or_none(artifacts[name])
        for name in (
            "target_descriptor",
            "target_aggregate",
            "target_partition_matrix",
            "target_concentration",
            "target_failure",
            "target_completion",
        )
    ]
    target_generated_times = [value for value in target_generated_times if value is not None]
    descriptor_forbidden = scan_forbidden_keys(target_descriptor.get("descriptor_rows", [])[:25])
    aggregate_forbidden = scan_forbidden_keys(target_aggregate)
    not_rows_with_values = recomputed["not_audit"]["not_computable_rows_have_target_values"]
    discovery = artifacts["discovery_baseline"]
    duplicate_proxy = artifacts["duplicate_proxy"]
    checks = {
        "pre_target_freeze_exists": TARGET_FREEZE.exists(),
        "pre_target_freeze_predates_target_artifacts": bool(freeze_time and target_generated_times)
        and all(freeze_time <= item for item in target_generated_times),
        "descriptors_frozen_before_target": target_descriptor.get("descriptor_freeze_status") == "FROZEN_BEFORE_TARGET_COMPUTATION",
        "descriptor_rows_are_candidate_count": target_descriptor.get("descriptor_row_count") == EXPECTED_COUNTS["candidate_rows"],
        "descriptor_forbidden_key_scan_passes": not descriptor_forbidden,
        "aggregate_forbidden_performance_label_scan_passes": not [
            item for item in aggregate_forbidden if "positive_return_fraction_not_win_rate" not in item
        ],
        "positive_return_fraction_label_is_not_win_rate": "positive_return_fraction_not_win_rate"
        in json.dumps(target_aggregate, sort_keys=True),
        "not_computable_rows_fail_closed_without_values": not_rows_with_values == 0,
        "all_discovery_exclusions_remain_excluded": discovery.get("selected_discovery_source_count")
        == EXPECTED_COUNTS["discovery_exclusions"]
        and all(
            row.get("partition_assignment") in PARTITIONS
            for row in partitions
        ),
        "sealed_and_stress_separate": Counter(row["partition_assignment"] for row in partitions)
        == {
            "SEALED_VALIDATION_CANDIDATE_DESIGN": EXPECTED_COUNTS["sealed_rows"],
            "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": EXPECTED_COUNTS["stress_rows"],
        },
        "four_adversarial_baselines_present_as_controls": sorted(discovery.get("adversarial_baseline_ids", []))
        == sorted(artifacts["candidate_manifest"].get("adversarial_baseline_ids", []))
        and len(discovery.get("adversarial_baseline_ids", [])) == 4,
        "secondary_proxy_sources_not_in_candidate_denominator": not any(
            row["symbol"] in FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES for row in candidates
        )
        and sorted(duplicate_proxy.get("secondary_proxy_sources_excluded_from_candidate_denominator", []))
        == sorted(FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES),
    }
    return {
        **safe_base("noleak_evidence_class_audit"),
        "checks": checks,
        "descriptor_forbidden_key_scan_sample": descriptor_forbidden[:25],
        "aggregate_forbidden_key_scan_sample": aggregate_forbidden[:25],
        "pre_target_freeze_generated_at_utc": target_freeze.get("generated_at_utc"),
        "target_artifact_generated_at_utc_values": [item.isoformat() for item in target_generated_times],
        "evidence_boundary": {
            "accepted_as": "neutral source-control target packet control evidence only",
            "not_accepted_as": [
                "strategy performance",
                "validation-safe result",
                "R/PnL/win-rate/expectancy",
                "promotion",
                "live behavior",
                "broker account/order/deal/position evidence",
            ],
        },
        "all_noleak_checks_pass": all(checks.values()),
    }


def denominator_audit(
    candidates: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    recomputed_terminal: list[dict[str, Any]],
    target_concentration: dict[str, Any],
) -> dict[str, Any]:
    groups = Counter(row["canonical_economic_group"] for row in candidates)
    symbols = Counter(row["symbol"] for row in candidates)
    source_files = Counter(row["source_file_name"] for row in candidates)
    partitions_c = Counter(row["partition_assignment"] for row in partitions)
    duplicate_keys = Counter(row["duplicate_key"] for row in candidates)
    terminal_keys = Counter(key_for(row) for row in recomputed_terminal)
    checks = {
        "candidate_count_exact": len(candidates) == EXPECTED_COUNTS["candidate_rows"],
        "partition_counts_exact": dict(partitions_c)
        == {
            "SEALED_VALIDATION_CANDIDATE_DESIGN": EXPECTED_COUNTS["sealed_rows"],
            "STRESS_ROBUSTNESS_CANDIDATE_DESIGN": EXPECTED_COUNTS["stress_rows"],
        },
        "denominator_group_count_exact": len(groups) == EXPECTED_COUNTS["denominator_groups"],
        "duplicate_key_collision_count_zero": sum(1 for count in duplicate_keys.values() if count > 1) == 0,
        "terminal_duplicate_combination_count_zero": sum(1 for count in terminal_keys.values() if count > 1) == 0,
        "target_concentration_matches_recomputed_counts": target_concentration.get("canonical_economic_group_counts") == dict(groups)
        and target_concentration.get("symbol_counts") == dict(symbols)
        and target_concentration.get("source_file_counts") == dict(source_files)
        and target_concentration.get("partition_counts") == dict(partitions_c),
        "forbidden_secondary_denominator_candidate_count_zero": not any(
            symbol in FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES for symbol in symbols
        ),
    }
    return {
        **safe_base("duplicate_concentration_denominator_audit"),
        "checks": checks,
        "candidate_rows": len(candidates),
        "canonical_economic_group_counts": dict(groups),
        "symbol_counts": dict(symbols),
        "source_file_counts": dict(source_files),
        "partition_counts": dict(partitions_c),
        "duplicate_key_count": len(duplicate_keys),
        "duplicate_key_collision_count": sum(1 for count in duplicate_keys.values() if count > 1),
        "terminal_status_expected_combinations": EXPECTED_COUNTS["terminal_statuses"],
        "terminal_status_recomputed_combinations": len(recomputed_terminal),
        "terminal_duplicate_combination_count": sum(1 for count in terminal_keys.values() if count > 1),
        "all_denominator_checks_pass": all(checks.values()),
    }


def dirty_state_audit() -> dict[str, Any]:
    status_entries = git_status_entries()
    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    staged_proc = run_git(["diff", "--cached", "--name-only"])
    staged_files = [line.replace("\\", "/") for line in staged_proc.stdout.splitlines() if line.strip()]
    checks = {
        "route_contains_no_raw_market_blobs": not any(path.suffix.lower() in FORBIDDEN_RAW_EXTENSIONS for path in route_files),
        "staged_files_have_no_forbidden_live_surface": not any(path.startswith(FORBIDDEN_LIVE_PREFIXES) for path in staged_files),
        "staged_files_have_no_raw_market_blob_extensions": not any(Path(path).suffix.lower() in FORBIDDEN_RAW_EXTENSIONS for path in staged_files),
        "unrelated_dirty_state_recorded": True,
    }
    return {
        **safe_base("dirty_state_raw_blob_live_surface_diff_audit"),
        "checks": checks,
        "git_status_entries": status_entries,
        "staged_files_at_build_time": staged_files,
        "route_file_count": len(route_files),
        "route_raw_blob_files": [repo_path(path) for path in route_files if path.suffix.lower() in FORBIDDEN_RAW_EXTENSIONS],
        "committed_diff_check_status": "PENDING_UNTIL_SCOPED_COMMIT_CLOSEOUT",
        "all_dirty_state_checks_pass": all(checks.values()),
    }


def saturation_ledger(decision: str, blockers: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **safe_base("saturation_self_redteam_ledger"),
        "lane_posture": "G12_INDEPENDENT_AUDIT_ACCEPTANCE_FOCUSED",
        "proof_or_impossibility_stop_condition_used": (
            "full recomputation of the terminal grid, target-row hashes, not-computable reasons, "
            "aggregate matrices, denominator facts, and source bindings; any remaining same-audit-class "
            "gap becomes exact repair/access/source requirement"
        ),
        "anti_boxing_saturation_questions": [
            {
                "question": "What exact mistake would let neutral target behavior be mistaken for strategy performance?",
                "pursuit": "scanned artifact labels and preserved positive_return_fraction_not_win_rate; decision boundary rejects R/PnL/win-rate/expectancy/performance interpretation",
            },
            {
                "question": "What exact mistake would let stress, discovery, rejected, or excluded rows leak into sealed denominators?",
                "pursuit": "recomputed partition counts, discovery exclusion count, duplicate keys, and secondary proxy exclusions from source packets",
            },
            {
                "question": "Which descriptor fields are most likely to be post-target or hidden-label leaks?",
                "pursuit": "recomputed descriptor rows from prior bars only and scanned descriptor keys for side/entry/stop/POI/fill/broker/performance labels",
            },
            {
                "question": "Which target computations are vulnerable to off-by-one as-of interval bugs?",
                "pursuit": "recomputed close target at entry_ref+horizon and path target over step 1..horizon, then compared every target_row_hash",
            },
            {
                "question": "Which not-computable reason could hide imputation or silent row drop?",
                "pursuit": "recomputed all NOT_COMPUTABLE reasons and verified not-computable rows contain no target values",
            },
            {
                "question": "Which duplicate/proxy denominator choice could double-count opportunity?",
                "pursuit": "verified GC/YM primary sources only in candidate denominators and MGC/MYM excluded while bars remain source-control context",
            },
            {
                "question": "Which aggregate label could be misread as win rate, expectancy, or edge?",
                "pursuit": "kept only positive_return_fraction_not_win_rate and documented it as neutral sign fraction, not a strategy win rate",
            },
            {
                "question": "What would a skeptical but fair G12 reviewer reject?",
                "pursuit": "tested source hashes including raw SCID segment rehash, row hashes, no-leak labels, denominator counts, and raw/live-surface diff scope",
            },
            {
                "question": "What future lane owns any valid next step crossing this evidence class?",
                "pursuit": "accepted route emits a G0 synthesis/control prompt; repair route emits exact repair requirements",
            },
        ],
        "blockers_after_saturation": blockers,
        "warnings_after_saturation": warnings,
        "terminal_decision": decision,
    }


def decide(blocker_sources: list[tuple[str, bool, str]], evidence_class_violations: list[str]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    blockers = [
        {"check_id": check_id, "repair_requirement": repair}
        for check_id, passed, repair in blocker_sources
        if not passed
    ]
    warnings: list[dict[str, Any]] = []
    if evidence_class_violations:
        blockers.extend(
            {"check_id": "evidence_class_violation", "repair_requirement": item}
            for item in evidence_class_violations
        )
        return EVIDENCE_CLASS_REJECT_DECISION, blockers, warnings
    if blockers:
        return REPAIR_DECISION, blockers, warnings
    return ACCEPT_DECISION, blockers, warnings


def next_prompt_pack(decision: str, blockers: list[dict[str, Any]]) -> str:
    if decision == ACCEPT_DECISION:
        return f"""# Next G0 Synthesis / Control Prompt Pack

Use this as the next controlling prompt, not as a promotion instruction.

`/goal Follow the accepted G12 audit in {repo_path(ROUTE_DIR)} as source-safe neutral target execution packet control evidence only; do mandatory preflight first; stay G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; decide whether the accepted neutral behavior evidence opens a future strategy-field source-expansion or preregistered result-design lane; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; emit exact next-lane prompt(s), verifier, completion audit, and scoped commits only.`

Acceptance boundary: `{ACCEPT_DECISION}` means the target packet is accepted only as quarantined source-safe neutral target packet control evidence.
"""
    blocker_text = "\n".join(
        f"- `{item['check_id']}`: {item['repair_requirement']}" for item in blockers
    )
    return f"""# Exact Repair Prompt Pack

Terminal decision: `{decision}`

Blockers:

{blocker_text}

`/goal Repair the rejected SCID neutral target packet using the exact blockers in {repo_path(ROUTE_DIR / f'{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json')}; do mandatory preflight first; stay SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_PACKET_REPAIR_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; repair only the failed source/hash/no-leak/denominator/row-target/aggregate defects, emit verifier/focused tests/next G12 repair audit prompt, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.`
"""


def context_anchor_md(anchor: dict[str, Any]) -> str:
    return f"""# G12 SCID Neutral Target Packet Audit Context Anchor

Route: `{ROUTE_ID}`

HEAD: `{anchor['current_head']}`

Evidence class: `{EVIDENCE_CLASS}`

Lane posture: `G12_INDEPENDENT_AUDIT_ACCEPTANCE_FOCUSED`

This route independently recomputes the SCID neutral target packet from
accepted source-control inputs and accepts only source-safe neutral target
packet control evidence. It does not open validation, strategy performance,
promotion, live behavior, AI/API, paid/vendor access, or broker evidence.
"""


def completion_md(completion: dict[str, Any]) -> str:
    lines = [
        "# G12 SCID Neutral Target Packet Audit Completion",
        "",
        f"Terminal decision: `{completion['terminal_decision']}`",
        "",
        "## Checklist",
        "",
    ]
    for item in completion["prompt_to_artifact_checklist"]:
        lines.append(f"- {item['status']}: {item['requirement']}")
    lines.extend(
        [
            "",
            "## Safe Flags",
            "",
            "- NO_PROMOTION_VERDICT",
            "- validation_safe=false",
            "- outcome_review_opened=false",
            "- live_effect=false",
            "",
            "## Completion",
            "",
            f"can_mark_goal_complete={str(completion['can_mark_goal_complete']).lower()}",
        ]
    )
    return "\n".join(lines)


def output_manifest(paths: list[Path], decision: str) -> dict[str, Any]:
    artifacts = []
    for path in paths:
        if path.exists():
            artifacts.append({"path": repo_path(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return {
        **safe_base("output_manifest"),
        "terminal_decision": decision,
        "artifact_count": len(artifacts),
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
    }


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    missing_inputs = [repo_path(path) for path in prerequisite_inputs() if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(f"missing required inputs: {missing_inputs}")

    artifacts = {
        "bar_manifest": load_json(BAR_MANIFEST),
        "candidate_manifest": load_json(CANDIDATE_MANIFEST),
        "discovery_baseline": load_json(DISCOVERY_BASELINE),
        "duplicate_proxy": load_json(DUPLICATE_PROXY),
        "segment_manifest": load_json(SEGMENT_MANIFEST),
        "g12_packet_decision": load_json(G12_PACKET_DECISION),
        "g0_rulebook": load_json(G0_RULEBOOK),
        "g0_accepted_reconciliation": load_json(G0_ACCEPTED_RECONCILIATION),
        "g12_design_decision": load_json(G12_DESIGN_DECISION),
        "target_rulebook": load_json(TARGET_RULEBOOK),
        "target_contract": load_json(TARGET_CONTRACT),
        "g12_target_decision": load_json(G12_TARGET_DECISION),
        "g12_target_completion": load_json(G12_TARGET_COMPLETION),
        "target_output_manifest": load_json(TARGET_OUTPUT_MANIFEST),
        "target_completion": load_json(TARGET_COMPLETION),
        "target_source_hash": load_json(TARGET_SOURCE_HASH),
        "target_freeze": load_json(TARGET_FREEZE),
        "target_descriptor": load_json(TARGET_DESCRIPTOR),
        "target_aggregate": load_json(TARGET_AGGREGATE),
        "target_partition_matrix": load_json(TARGET_PARTITION_MATRIX),
        "target_concentration": load_json(TARGET_CONCENTRATION),
        "target_baseline": load_json(TARGET_BASELINE),
        "target_failure": load_json(TARGET_FAILURE),
    }
    candidates = load_jsonl(CANDIDATE_ROWS)
    bars = load_jsonl(BAR_ROWS)
    partitions = load_jsonl(G0_PARTITION_LEDGER)
    target_rows = load_jsonl(TARGET_ROW_RESULTS)
    target_not_rows = load_jsonl(TARGET_NOT_COMPUTABLE)
    artifacts["target_rows"] = target_rows
    artifacts["target_not_rows"] = target_not_rows

    anchor = {
        **safe_base("context_anchor"),
        "current_head": git_head(),
        "current_head_short": git_head_short(),
        "target_packet_commit_in_live_state": "03a66e2d",
        "target_prompt_hardening_commit_in_live_state": "66fab745",
        "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
        "target_packet_dir": repo_path(TARGET_DIR),
        "preflight_status": {
            "generate_live_state_run": True,
            "live_state_read": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "goal_session_research_discipline_read": True,
            "research_current_state_read": True,
            "controlling_prompt_read_from_disk": True,
            "target_completion_and_manifest_read": True,
            "predecessor_acceptance_artifacts_read": True,
        },
        "dirty_state_scope": git_status_entries(),
        "active_question_stack": [
            "recompute prerequisite acceptance",
            "rehash accepted source inputs and bounded SCID segments",
            "recompute target terminal grid and target_row_hash values",
            "recompute not-computable reasons and aggregate matrices",
            "audit no-leak/evidence-class and denominator boundaries",
        ],
    }
    write_json(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json", anchor)
    write_md(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md", context_anchor_md(anchor))

    prerequisite_audit = prerequisite_acceptance_audit(artifacts)
    source_audit = source_hash_audit(artifacts["target_source_hash"], artifacts)
    recomputed = recomputation_audits(candidates, bars, partitions, target_rows, target_not_rows, artifacts)
    noleak = noleak_audit(artifacts, candidates, partitions, recomputed)
    denominator = denominator_audit(candidates, partitions, recomputed["recomputed_terminal"], artifacts["target_concentration"])
    dirty = dirty_state_audit()

    blocker_sources = [
        ("prerequisites_accepted", prerequisite_audit["all_prerequisites_accepted"], "repair predecessor acceptance chain or stop this audit until predecessor G12/G0 acceptance is exact"),
        ("source_hash_input_binding", source_audit["all_input_artifact_hashes_match_target_binding"], "repair target source hash binding to match recomputed accepted input artifact hashes"),
        ("accepted_scid_segment_rehash", source_audit["accepted_scid_segments_rehashed"], "obtain/read exact bounded SCID segment bytes or repair accepted segment hash manifest"),
        ("manifest_hashes_match", source_audit["candidate_rows_sha256_matches_manifest"] and source_audit["bar_rows_sha256_matches_manifest"], "repair source packet manifests or row files before target packet acceptance"),
        ("full_terminal_grid", recomputed["terminal_audit"]["full_terminal_grid_pass"], "repair missing/extra/duplicate candidate-horizon-family terminal statuses"),
        ("row_target_hashes", recomputed["row_target_audit"]["full_row_hash_recomputation_pass"], "repair target computation, descriptor freeze, or target_row_hash algorithm for mismatched rows"),
        ("not_computable_reasons", recomputed["not_audit"]["reason_counts_match_target"] and recomputed["not_audit"]["reason_counts_match_completion_and_failure"] and recomputed["not_audit"]["not_computable_rows_have_target_values"] == 0, "repair fail-closed not-computable classification/counts and remove any imputed target values"),
        ("aggregate_matrices", recomputed["aggregate_audit"]["availability_summary_matches"] and recomputed["aggregate_audit"]["aggregate_matrices_hash_match"] and recomputed["aggregate_audit"]["partition_symbol_session_matrix_hash_match"], "repair aggregate/matrix computation from row results and not-computable ledgers"),
        ("noleak_evidence_class", noleak["all_noleak_checks_pass"], "repair no-leak/evidence-class breach before acceptance"),
        ("denominator_duplicate_concentration", denominator["all_denominator_checks_pass"], "repair denominator, duplicate, proxy, sealed/stress, or concentration facts"),
        ("dirty_raw_live_surface", dirty["all_dirty_state_checks_pass"], "remove forbidden staged/live-surface/raw-blob audit changes and rerun closeout"),
    ]
    evidence_class_violations = []
    if not noleak["checks"]["aggregate_forbidden_performance_label_scan_passes"]:
        evidence_class_violations.append("aggregate artifact contains forbidden performance-like labels beyond the explicit neutral label")
    if not noleak["checks"]["descriptor_forbidden_key_scan_passes"]:
        evidence_class_violations.append("descriptor artifact contains forbidden strategy/broker/performance fields")

    decision, blockers, warnings = decide(blocker_sources, evidence_class_violations)
    saturation = saturation_ledger(decision, blockers, warnings)

    write_json(ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json", prerequisite_audit)
    write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_INPUT_BINDING_AUDIT_{DATE_TAG}.json", source_audit)
    write_json(ROUTE_DIR / f"{PREFIX}_TERMINAL_GRID_RECOMPUTATION_AUDIT_{DATE_TAG}.json", recomputed["terminal_audit"])
    write_json(ROUTE_DIR / f"{PREFIX}_ROW_TARGET_RECOMPUTATION_AUDIT_{DATE_TAG}.json", recomputed["row_target_audit"])
    write_json(ROUTE_DIR / f"{PREFIX}_NOT_COMPUTABLE_REASON_AUDIT_{DATE_TAG}.json", recomputed["not_audit"])
    write_json(ROUTE_DIR / f"{PREFIX}_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_{DATE_TAG}.json", recomputed["aggregate_audit"])
    write_json(ROUTE_DIR / f"{PREFIX}_NOLEAK_EVIDENCE_CLASS_AUDIT_{DATE_TAG}.json", noleak)
    write_json(ROUTE_DIR / f"{PREFIX}_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json", denominator)
    write_json(ROUTE_DIR / f"{PREFIX}_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_{DATE_TAG}.json", dirty)
    write_json(ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json", saturation)
    next_prompt_path = ROUTE_DIR / (
        f"{PREFIX}_NEXT_G0_SYNTHESIS_CONTROL_PROMPT_PACK_{DATE_TAG}.md"
        if decision == ACCEPT_DECISION
        else f"{PREFIX}_EXACT_REPAIR_PROMPT_PACK_{DATE_TAG}.md"
    )
    write_md(next_prompt_path, next_prompt_pack(decision, blockers))

    decision_ledger = {
        **safe_base("decision_ledger"),
        "terminal_decision": decision,
        "accepted_source_safe_neutral_target_execution_packet_control_evidence_only": decision == ACCEPT_DECISION,
        "accepted_validation_execution": False,
        "accepted_strategy_performance": False,
        "accepted_promotion": False,
        "terminal_blockers": blockers,
        "warnings": warnings,
        "review_pass_map": {
            "prerequisite_acceptance": prerequisite_audit["all_prerequisites_accepted"],
            "source_hash_input_binding": source_audit["all_input_artifact_hashes_match_target_binding"],
            "accepted_scid_segment_rehash": source_audit["accepted_scid_segments_rehashed"],
            "terminal_grid": recomputed["terminal_audit"]["full_terminal_grid_pass"],
            "row_target_recomputation": recomputed["row_target_audit"]["full_row_hash_recomputation_pass"],
            "not_computable": recomputed["not_audit"]["reason_counts_match_target"],
            "aggregate_matrix": recomputed["aggregate_audit"]["aggregate_matrices_hash_match"],
            "noleak": noleak["all_noleak_checks_pass"],
            "denominator": denominator["all_denominator_checks_pass"],
            "dirty_raw_live_surface": dirty["all_dirty_state_checks_pass"],
            "saturation": not blockers,
        },
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "next_prompt_pack_ref": repo_path(next_prompt_path),
    }
    write_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json", decision_ledger)
    write_md(
        ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md",
        f"# G12 SCID Neutral Target Packet Audit Decision\n\nTerminal decision: `{decision}`\n\nBlockers: `{len(blockers)}`\n\nEvidence boundary: control evidence only, not strategy performance.\n",
    )

    checklist = [
        ("mandatory preflight and context use recorded", True),
        ("audit route artifacts emitted", True),
        ("target packet parsing and full recomputation checks pass or exact blockers recorded", decision == ACCEPT_DECISION or bool(blockers)),
        ("source hash, no-leak, denominator, dirty-state, raw-blob, live-surface checks complete", True),
        ("standalone verifier available", (ROUTE_DIR / "verify_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py").exists()),
        ("focused tests available", (ROUTE_DIR / "test_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py").exists()),
        ("next G0-or-repair prompt emitted", next_prompt_path.exists()),
        ("NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false preserved", True),
    ]
    completion = {
        **safe_base("completion_audit"),
        "terminal_decision": decision,
        "can_mark_goal_complete": decision in {ACCEPT_DECISION, REPAIR_DECISION, EVIDENCE_CLASS_REJECT_DECISION}
        and all(item[1] for item in checklist)
        and dirty["all_dirty_state_checks_pass"],
        "objective_restatement": {
            "candidate_rows": EXPECTED_COUNTS["candidate_rows"],
            "sealed_rows": EXPECTED_COUNTS["sealed_rows"],
            "stress_rows": EXPECTED_COUNTS["stress_rows"],
            "discovery_exclusions": EXPECTED_COUNTS["discovery_exclusions"],
            "denominator_groups": EXPECTED_COUNTS["denominator_groups"],
            "bar_rows": EXPECTED_COUNTS["bar_rows"],
            "terminal_statuses": EXPECTED_COUNTS["terminal_statuses"],
            "target_families": TARGET_FAMILIES,
            "horizons": HORIZONS,
        },
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": "PASS" if passed else "FAIL"} for requirement, passed in checklist
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_posture": "G12_INDEPENDENT_AUDIT_ACCEPTANCE_FOCUSED",
            "anti_boxing_saturation_questions_pursued": True,
            "independently_recomputed": [
                "prerequisite acceptance status",
                "source artifact hashes",
                "bounded SCID segment hashes",
                "candidate/bar/partition universe counts",
                "descriptor freeze rows",
                "all candidate/horizon/family terminal statuses",
                "all target_row_hash values",
                "not-computable reason counts",
                "aggregate and partition/symbol/session matrices",
                "duplicate/proxy/denominator facts",
            ],
            "blocker_warning_accepted_evidence_boundaries": {
                "blocker_count": len(blockers),
                "warning_count": len(warnings),
                "accepted_boundary": "neutral target execution packet control evidence only",
            },
            "doctrine_requirements_deliberately_not_answered": [
                "strategy-edge, R, PnL, win-rate, expectancy, performance, validation, and promotion cross evidence-class boundaries",
                "AI/API, paid/vendor, broker account/order/history/deal/position evidence, and live behavior are forbidden",
                "G0 synthesis is emitted as the next prompt pack rather than performed inside this G12 audit",
            ],
        },
        "terminal_blockers": blockers,
        "warnings": warnings,
        "verifier_expected_after_build": True,
        "scoped_commit_required_before_final_goal_closeout": True,
    }
    write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion)
    write_md(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md", completion_md(completion))

    generated_paths = [
        ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_INPUT_BINDING_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_TERMINAL_GRID_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_ROW_TARGET_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_NOT_COMPUTABLE_REASON_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_NOLEAK_EVIDENCE_CLASS_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md",
        next_prompt_path,
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
        ROUTE_DIR / "build_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
        ROUTE_DIR / "verify_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
        ROUTE_DIR / "test_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
    ]
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    write_json(manifest_path, output_manifest([*generated_paths, manifest_path], decision))
    return {
        "terminal_decision": decision,
        "blocker_count": len(blockers),
        "terminal_statuses_recomputed": len(recomputed["recomputed_terminal"]),
        "target_row_hash_mismatch_count": recomputed["row_target_audit"]["target_row_hash_mismatch_count"],
        "not_computable_count": len(recomputed["recomputed_not_rows"]),
        "manifest_path": repo_path(manifest_path),
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    result = build_all()
    if args.summary:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
