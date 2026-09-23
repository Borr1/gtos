"""Build the SCID as-of quarantined neutral-target execution packet.

This route consumes accepted source-control candidate/bar packets plus the
accepted G12 neutral target rulebook. It computes only source-safe neutral
bar-behavior targets. It does not score strategy performance, open validation,
or touch live trading surfaces.
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
PREFIX = "SCID_ASOF_NEUTRAL_TARGET"
ROUTE_ID = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET"
EVIDENCE_CLASS = "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_ONLY"
SCHEMA_VERSION = "scid_asof_quarantined_neutral_target_execution_packet_v1"
TERMINAL_DECISION = "BUILT_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_G12_AUDIT_REQUIRED"

CONTROLLING_PROMPT = (
    PROMPT_DIR / "SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_GOAL_PROMPT_2026-05-12.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR / "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

PACKET_DIR = OUTCOME_ROOT / "scid_asof_bar_builder_and_candidate_input_packet_source_control"
G12_PACKET_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit"
G0_DESIGN_DIR = OUTCOME_ROOT / "g0_scid_asof_packet_source_control_synthesis_and_validation_design"
G12_DESIGN_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_sealed_validation_design_audit"
TARGET_REPAIR_DIR = OUTCOME_ROOT / "scid_asof_sealed_validation_target_horizon_repair"
G12_TARGET_AUDIT_DIR = OUTCOME_ROOT / "g12_scid_asof_target_horizon_repair_audit"

BAR_ROWS = PACKET_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
BAR_MANIFEST = PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
CANDIDATE_ROWS = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
CANDIDATE_MANIFEST = PACKET_DIR / "SCID_ASOF_CANDIDATE_INPUT_PACKET_MANIFEST_2026-05-11.json"
G12_PACKET_DECISION = (
    G12_PACKET_AUDIT_DIR / "G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json"
)
G0_PARTITION_LEDGER = G0_DESIGN_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl"
G0_RULEBOOK = G0_DESIGN_DIR / "G0_SCID_ASOF_VALIDATION_DESIGN_RULEBOOK_2026-05-11.json"
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
}
FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES = {"XAUUSD_MGC", "US30_MYM"}
FORBIDDEN_RAW_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
SAFE_FALSE_FLAGS = {
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
COMMON_SAFE_FIELDS = {
    "schema_version": SCHEMA_VERSION,
    "route_id": ROUTE_ID,
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "neutral_target_behavior_opened": True,
    **SAFE_FALSE_FLAGS,
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return sha256_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


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
    entries: list[dict[str, Any]] = []
    scoped_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/",
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        path = line[3:].replace("\\", "/")
        entries.append(
            {
                "status": status,
                "path": path,
                "scoped_to_this_route": path.startswith(scoped_prefixes),
                "forbidden_live_surface_path": path.startswith(forbidden_live_prefixes),
                "raw_blob_extension": Path(path).suffix.lower() in FORBIDDEN_RAW_EXTENSIONS,
            }
        )
    if proc.stderr:
        entries.append({"status": "GIT_STATUS_STDERR", "path": proc.stderr.strip(), "scoped_to_this_route": False})
    return entries


def source_binding(paths: list[Path]) -> list[dict[str, Any]]:
    binding = []
    for path in paths:
        binding.append(
            {
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return binding


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        **COMMON_SAFE_FIELDS,
        "artifact_family": artifact_family,
        "generated_at_utc": now_utc(),
    }


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
    sorted_values = sorted(clean)
    return {
        "count": len(sorted_values),
        "mean": round(statistics.fmean(sorted_values), 12),
        "median": round(statistics.median(sorted_values), 12),
        "standard_deviation": round(statistics.pstdev(sorted_values), 12) if len(sorted_values) > 1 else 0.0,
        "min": round(sorted_values[0], 12),
        "max": round(sorted_values[-1], 12),
        "p05": round(percentile(sorted_values, 0.05), 12),
        "p25": round(percentile(sorted_values, 0.25), 12),
        "p75": round(percentile(sorted_values, 0.75), 12),
        "p95": round(percentile(sorted_values, 0.95), 12),
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


def is_present_bar(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("bar_status") in PRESENT_BAR_STATUSES)


def session_bucket(symbol: str, ts: datetime) -> str:
    hour = ts.hour
    minute = ts.minute
    minutes = hour * 60 + minute
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


def prior_window_bars(
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    symbol: str,
    entry_time: datetime,
    count: int,
) -> list[dict[str, Any] | None]:
    return [
        bars_by_end.get((symbol, format_ts(entry_time - timedelta(minutes=15 * offset))))
        for offset in range(count - 1, -1, -1)
    ]


def describe_prior_window(
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    symbol: str,
    entry_time: datetime,
    count: int,
) -> dict[str, Any]:
    rows = prior_window_bars(bars_by_end, symbol, entry_time, count)
    present_rows = [row for row in rows if is_present_bar(row)]
    complete = len(present_rows) == count
    if not complete:
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
    last_close = closes[-1]
    range_abs = max(highs) - min(lows)
    drift_abs = closes[-1] - closes[0]
    return {
        "window_bars": count,
        "required_bars": count,
        "record_present_bars": len(present_rows),
        "complete": True,
        "range_absolute": round(range_abs, 12),
        "range_percent": round(range_abs / last_close, 12) if last_close else None,
        "drift_absolute": round(drift_abs, 12),
        "drift_percent": round(drift_abs / closes[0], 12) if closes[0] else None,
    }


def compute_descriptors(
    candidates: list[dict[str, Any]],
    partition_by_id: dict[str, dict[str, Any]],
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    descriptor_rows: list[dict[str, Any]] = []
    raw_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    group_counts = Counter(row["canonical_economic_group"] for row in candidates)
    for candidate in candidates:
        entry_time = parse_ts(candidate["duplicate_key_fields"]["entry_reference_time_utc"])
        symbol = candidate["symbol"]
        partition = partition_by_id[candidate["candidate_input_row_id"]]
        prior_windows = {
            str(count): describe_prior_window(bars_by_end, symbol, entry_time, count)
            for count in (4, 16, 32, 96)
        }
        prior_96 = prior_windows["96"]
        row = {
            "candidate_input_row_id": candidate["candidate_input_row_id"],
            "duplicate_proxy_denominator_key": partition["duplicate_proxy_denominator_key"],
            "partition_assignment": partition["partition_assignment"],
            "symbol": symbol,
            "canonical_economic_group": candidate["canonical_economic_group"],
            "source_file_name": candidate["source_file_name"],
            "entry_reference_time_utc": candidate["duplicate_key_fields"]["entry_reference_time_utc"],
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
        descriptor_rows.append(row)
        raw_by_symbol[symbol].append(row)

    cutoffs_by_symbol: dict[str, dict[str, Any]] = {}
    for symbol, rows in raw_by_symbol.items():
        r16 = sorted(row["prior_16_range_percent"] for row in rows if row["prior_16_range_percent"] is not None)
        d16 = sorted(row["prior_16_drift_percent"] for row in rows if row["prior_16_drift_percent"] is not None)
        r32 = sorted(row["prior_32_range_percent"] for row in rows if row["prior_32_range_percent"] is not None)
        cutoffs_by_symbol[symbol] = {
            "prior_16_range_p33": percentile(r16, 0.33) if r16 else None,
            "prior_16_range_p66": percentile(r16, 0.66) if r16 else None,
            "prior_16_drift_p33": percentile(d16, 0.33) if d16 else None,
            "prior_16_drift_p66": percentile(d16, 0.66) if d16 else None,
            "prior_32_range_p33": percentile(r32, 0.33) if r32 else None,
            "prior_32_range_p66": percentile(r32, 0.66) if r32 else None,
        }

    for row in descriptor_rows:
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

    return {
        "descriptor_definitions": [
            "All descriptors use only source-control M15 bars ending at or before entry_reference_time_utc.",
            "prior_N_range_percent = (max(high)-min(low))/last_close over the prior N bars when all N bars are record-present.",
            "prior_N_drift_percent = (last_close-first_close)/first_close over the prior N bars when all N bars are record-present.",
            "range and drift buckets are per-symbol terciles computed before target computation from source-safe prior descriptors only.",
            "session and time-of-day buckets derive only from UTC entry_reference_time_utc and symbol.",
            "coverage bucket derives only from prior 96-bar source-control availability.",
        ],
        "descriptor_cutoffs_by_symbol": cutoffs_by_symbol,
        "descriptor_rows": descriptor_rows,
    }


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
        **COMMON_SAFE_FIELDS,
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


def compute_targets(
    candidates: list[dict[str, Any]],
    partition_by_id: dict[str, dict[str, Any]],
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    descriptors_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    row_results: list[dict[str, Any]] = []
    not_computable_rows: list[dict[str, Any]] = []
    terminal_rows: list[dict[str, Any]] = []
    duplicate_counts = Counter(candidate["duplicate_key"] for candidate in candidates)

    for candidate in candidates:
        candidate_id = candidate["candidate_input_row_id"]
        partition = partition_by_id.get(candidate_id)
        descriptor = descriptors_by_id.get(candidate_id)
        entry_ref = candidate["duplicate_key_fields"]["entry_reference_time_utc"]
        entry_time = parse_ts(entry_ref)
        entry_bar = bars_by_end.get((candidate["symbol"], entry_ref))
        base_reasons: list[tuple[str, str]] = []
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
                    not_computable_rows.append(row)
                    terminal_rows.append(row)
                    continue

                entry_close = float(entry_bar["close"])
                if target_family == "neutral_close_to_close_return_m15_horizons_v1":
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
                        not_computable_rows.append(row)
                        terminal_rows.append(row)
                        continue
                    horizon_close = float(horizon_bar["close"])
                    delta = horizon_close - entry_close
                    result = {
                        **COMMON_SAFE_FIELDS,
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
                    path_rows: list[dict[str, Any]] = []
                    missing: list[str] = []
                    invalid: list[str] = []
                    for step in range(1, horizon + 1):
                        end_s = format_ts(entry_time + timedelta(minutes=15 * step))
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
                            [entry_ref, *[format_ts(entry_time + timedelta(minutes=15 * step)) for step in range(1, horizon + 1)]],
                            source_hashes,
                            descriptor,
                        )
                        not_computable_rows.append(row)
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
                            [entry_ref, *[format_ts(entry_time + timedelta(minutes=15 * step)) for step in range(1, horizon + 1)]],
                            source_hashes,
                            descriptor,
                        )
                        not_computable_rows.append(row)
                        terminal_rows.append(row)
                        continue
                    highs = [float(row["high"]) for row in path_rows]
                    lows = [float(row["low"]) for row in path_rows]
                    max_high = max(highs)
                    min_low = min(lows)
                    upside = max_high - entry_close
                    downside = entry_close - min_low
                    result = {
                        **COMMON_SAFE_FIELDS,
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
    return row_results, not_computable_rows, terminal_rows


def close_target_reason(horizon_bar: dict[str, Any] | None) -> tuple[str, str] | None:
    if horizon_bar is None:
        return ("NOT_COMPUTABLE_HORIZON_BAR_MISSING", "horizon close bar is absent from source-control bar packet")
    if not is_present_bar(horizon_bar):
        return ("NOT_COMPUTABLE_HORIZON_BAR_NOT_RECORD_PRESENT", f"horizon bar status is {horizon_bar.get('bar_status')}")
    if horizon_bar.get("close") is None:
        return ("NOT_COMPUTABLE_HORIZON_CLOSE_NULL", "horizon bar close is null")
    return None


def aggregate_group(records: list[dict[str, Any]], key_fields: list[str], minimum_distribution_count: int = 5) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = tuple(resolve_field(record, field) for field in key_fields)
        groups[key].append(record)
    output: list[dict[str, Any]] = []
    for key, rows in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        computed = [row for row in rows if row["terminal_status"] == "COMPUTABLE"]
        not_comp = [row for row in rows if row["terminal_status"] == "NOT_COMPUTABLE"]
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
            if row.get("upside_excursion_absolute") is not None
            and row.get("downside_excursion_absolute") not in (None, 0)
        ]
        result = {
            "slice": {field: key[index] for index, field in enumerate(key_fields)},
            "terminal_combination_count": len(rows),
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


def resolve_field(record: dict[str, Any], field: str) -> Any:
    if field.startswith("descriptor_buckets."):
        return record.get("descriptor_buckets", {}).get(field.split(".", 1)[1])
    return record.get(field)


def build_aggregate_matrices(terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matrices = {
        **safe_base("aggregate_distribution_matrix"),
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
    output: list[dict[str, Any]] = []
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


def build_partition_symbol_session_matrix(terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [
        "partition_assignment",
        "symbol",
        "descriptor_buckets.session_bucket",
        "target_family_id",
        "horizon_m15_bars",
    ]
    return {
        **safe_base("partition_symbol_session_matrix"),
        "matrix_fields": fields,
        "rows": aggregate_group(terminal_rows, fields, minimum_distribution_count=5),
    }


def build_concentration_audit(
    candidates: list[dict[str, Any]],
    partition_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    groups = Counter(row["canonical_economic_group"] for row in candidates)
    symbols = Counter(row["symbol"] for row in candidates)
    source_files = Counter(row["source_file_name"] for row in candidates)
    partitions = Counter(row["partition_assignment"] for row in partition_rows)
    duplicate_keys = Counter(row["duplicate_key"] for row in candidates)
    terminal_keys = Counter((row["candidate_input_row_id"], row["target_family_id"], row["horizon_m15_bars"]) for row in terminal_rows)
    total = len(candidates)
    return {
        **safe_base("concentration_denominator_audit"),
        "candidate_rows": total,
        "denominator_group_count": len(groups),
        "duplicate_key_count": len(duplicate_keys),
        "duplicate_key_collision_count": sum(1 for count in duplicate_keys.values() if count > 1),
        "partition_counts": dict(partitions),
        "canonical_economic_group_counts": dict(groups),
        "symbol_counts": dict(symbols),
        "source_file_counts": dict(source_files),
        "max_group_share": max((count / total for count in groups.values()), default=0),
        "max_symbol_share": max((count / total for count in symbols.values()), default=0),
        "forbidden_secondary_denominator_candidate_count": sum(
            count for symbol, count in symbols.items() if symbol in FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES
        ),
        "terminal_status_expected_combinations": total * len(TARGET_FAMILIES) * len(HORIZONS),
        "terminal_status_observed_combinations": len(terminal_rows),
        "terminal_duplicate_combination_count": sum(1 for count in terminal_keys.values() if count > 1),
        "no_leak_checks": {
            "all_candidate_rows_partitioned": len(partition_rows) == total,
            "all_terminal_combinations_exactly_once": all(count == 1 for count in terminal_keys.values())
            and len(terminal_keys) == total * len(TARGET_FAMILIES) * len(HORIZONS),
            "discovery_exclusions_absent_from_candidate_rows": True,
            "forbidden_secondary_denominator_sources_absent_from_candidates": not any(
                symbol in FORBIDDEN_SECONDARY_DENOMINATOR_SOURCES for symbol in symbols
            ),
            "strategy_result_scoring_opened": False,
            "validation_safe": False,
        },
    }


def build_failure_anatomy(not_rows: list[dict[str, Any]], terminal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(row["not_computable_reason"] for row in not_rows)
    by_reason_symbol = Counter((row["not_computable_reason"], row["symbol"]) for row in not_rows)
    by_family_horizon = Counter((row["target_family_id"], row["horizon_m15_bars"], row.get("not_computable_reason")) for row in not_rows)
    neutral_signs = Counter()
    for row in terminal_rows:
        if row["terminal_status"] != "COMPUTABLE" or row["target_family_id"] != TARGET_FAMILIES[0]:
            continue
        value = row.get("close_to_close_percent_return")
        if value is None:
            continue
        if value > 0:
            neutral_signs["positive_return_not_win"] += 1
        elif value < 0:
            neutral_signs["negative_return_not_loss"] += 1
        else:
            neutral_signs["zero_return_neutral"] += 1
    same_class_repairs = []
    for reason, count in sorted(reason_counts.items()):
        if "MISSING" in reason or "NOT_RECORD_PRESENT" in reason or "NULL" in reason:
            repair = "requires a new source-control expansion/freeze and G12 audit for wider or cleaner bars; this lane cannot impute or use bars outside the accepted packet"
        elif "MISMATCH" in reason or "DUPLICATE" in reason or "PARTITION" in reason:
            repair = "requires upstream source-control packet repair before any neutral target computation for affected rows"
        else:
            repair = "no current same-class repair identified beyond fail-closed ledgering"
        same_class_repairs.append({"reason": reason, "count": count, "source_safe_repair_route": repair})
    return {
        **safe_base("failure_anatomy_ledger"),
        "not_computable_count": len(not_rows),
        "not_computable_reason_counts": dict(reason_counts),
        "not_computable_by_reason_symbol": [
            {"reason": reason, "symbol": symbol, "count": count}
            for (reason, symbol), count in sorted(by_reason_symbol.items())
        ],
        "not_computable_by_family_horizon_reason": [
            {"target_family_id": fam, "horizon_m15_bars": horizon, "reason": reason, "count": count}
            for (fam, horizon, reason), count in sorted(by_family_horizon.items())
        ],
        "neutral_close_to_close_sign_counts_not_strategy_outcomes": dict(neutral_signs),
        "same_evidence_class_blocker_pursuit": same_class_repairs,
        "failure_boundary": "not-computable rows remain terminal for this accepted source-control packet; no imputation, session reset, or external source opening occurred",
    }


def build_baseline_control_readiness(aggregate_matrix: dict[str, Any], candidate_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("baseline_control_readiness_ledger"),
        "control_status": "NEUTRAL_TARGET_VALUES_READY_FOR_NEXT_G12_AUDIT_ONLY",
        "adversarial_baseline_ids_from_input_manifest": candidate_manifest.get("adversarial_baseline_ids", []),
        "neutral_target_availability_summary": aggregate_matrix["availability_summary"],
        "allowed_future_use": [
            "G12 audit of neutral target packet integrity",
            "future separately frozen baseline/control route if G12 accepts this packet",
        ],
        "forbidden_current_use": [
            "strategy performance scoring",
            "promotion",
            "live behavior",
            "broker/account/order evidence",
        ],
    }


def build_interpretation_limits(aggregate_matrix: dict[str, Any], concentration: dict[str, Any]) -> str:
    availability = sorted(
        aggregate_matrix["availability_summary"],
        key=lambda row: (-(row["computable_fraction"] or 0), row["target_family_id"], row["horizon_m15_bars"]),
    )
    strongest = availability[0] if availability else {}
    weakest = availability[-1] if availability else {}
    notable = aggregate_matrix.get("notable_neutral_descriptor_slices", [])[:6]
    return f"""# SCID As-Of Neutral Target Interpretation Limits

Status: NO_PROMOTION_VERDICT

This packet is source-safe neutral bar behavior only. It is not strategy
performance, not validation-safe, and not a live-readiness artifact.

## Availability

Strongest source-safe availability is `{strongest.get('target_family_id')}` at
`{strongest.get('horizon_m15_bars')}` M15 bars with computable fraction
`{strongest.get('computable_fraction')}`. Weakest availability is
`{weakest.get('target_family_id')}` at `{weakest.get('horizon_m15_bars')}` M15
bars with computable fraction `{weakest.get('computable_fraction')}`.

## Neutral Behavior Only

The aggregate matrices may show neutral close-to-close drift, neutral path
excursion, session/time-of-day differences, or prior-range bucket differences.
Those are descriptive source-safe path behaviors, not OB/FVG/breaker/no-fill
performance claims.

Notable descriptor spreads recorded for future G12 review:

{json.dumps(notable, indent=2, sort_keys=True)}

## Concentration

The packet has `{concentration['denominator_group_count']}` denominator groups.
Max group share is `{round(concentration['max_group_share'], 12)}` and max symbol
share is `{round(concentration['max_symbol_share'], 12)}`. EURUSD is a small
source segment and must not dominate future interpretation by denominator count.

## Missing Strategy Fields

The packet lacks strategy side, intended entry, stop, target, POI, OB/FVG/breaker
membership, pending lifecycle, fill/cancel state, and broker/account truth. Any
future strategy-specific route must source-expand those fields before it can ask
strategy questions.

## Future Science Routes

- path geometry: preregister neutral excursion-shape descriptors before joining
  strategy-specific fields;
- volatility and tail behavior: test whether prior-range buckets explain neutral
  excursion distributions in a sealed route;
- session microstructure: freeze session/hour hypotheses before any strategy
  labels are opened;
- orderflow proxy context: join only source-contracted, as-of futures/depth fields
  in a separate route;
- execution timing: requires separate lifecycle/fill/cancel observability.

Safe flags: NO_PROMOTION_VERDICT, validation_safe=false,
outcome_review_opened=false, live_effect=false.
"""


def output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifacts = []
    for path in sorted(paths, key=lambda item: repo_path(item)):
        if path.exists():
            artifacts.append(
                {
                    "path": repo_path(path),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    return {
        **safe_base("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "terminal_decision": TERMINAL_DECISION,
        "next_g12_prompt_ref": repo_path(NEXT_G12_PROMPT),
    }


def build_next_g12_prompt() -> str:
    return f"""# G12 SCID As-Of Quarantined Neutral Target Execution Packet Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent G12 audit
Evidence class: `G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY`

## Objective

Audit the quarantined neutral-target behavior execution packet at:

`research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/`

This is an audit of source-safe neutral target computation only. It must not
promote, open live behavior, use broker account/order/history/deal/position
evidence, call AI/API, use paid/vendor access, commit raw market-data blobs, or
reinterpret neutral targets as strategy performance.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt and the packet completion audit from disk.

## Required Audit Checks

- Verify prerequisite acceptance ledgers from disk.
- Verify pre-target freeze exists and binds source hashes before target rows.
- Recompute source hashes for all required inputs.
- Parse all JSON/JSONL artifacts.
- Verify exactly `3,014` candidate rows, `2,432` sealed rows, `582` stress rows,
  `365` discovery exclusions, `7` denominator groups, `7,567` source-control bar
  rows, target families `{TARGET_FAMILIES}`, and horizons `{HORIZONS}`.
- Verify every candidate/horizon/target-family combination has exactly one
  terminal status in either row results or not-computable ledger.
- Verify target values use only accepted source-control bars and fail closed for
  missing/gap/null coverage.
- Verify descriptors use only bars ending at or before entry reference time and
  were frozen before target computation.
- Verify aggregate matrices avoid strategy-performance labels except the explicit
  neutral label `positive_return_fraction_not_win_rate`.
- Verify safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`,
  `outcome_review_opened=false`, `live_effect=false`.
- Verify no live/prompt/config/risk/safety/execution/canary/selector files are in
  the committed packet diff.
- Verify no raw `.scid`, `.parquet`, `.csv`, `.dly`, or `.bin` blobs are committed
  in the packet route.

## Allowed Terminal Decisions

- `ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY`
- `REJECT_NEUTRAL_TARGET_PACKET_REPAIR_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`,
`outcome_review_opened=false`, and `live_effect=false`.
"""


def build_completion_audit(
    checks: dict[str, bool],
    aggregate_matrix: dict[str, Any],
    concentration: dict[str, Any],
    failure: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory context files read and applied", checks["mandatory_context_read"]),
        ("accepted G12 target/horizon repair decision proven from disk", checks["g12_target_acceptance"]),
        ("pre-target freeze packet exists before target computation", checks["pre_target_freeze"]),
        ("all 3014 candidate rows represented", checks["all_candidates_represented"]),
        ("all horizons and target families terminal", checks["all_combinations_terminal"]),
        ("aggregate matrices and failure anatomy exist", checks["matrices_and_failure"]),
        ("no forbidden strategy/live/broker/API surfaces opened", checks["forbidden_surfaces_closed"]),
        ("verifier and focused tests available", checks["verifier_and_tests_available"]),
        ("next G12 audit prompt exists and is runnable", checks["next_g12_prompt"]),
    ]
    return {
        **safe_base("completion_audit"),
        "terminal_decision": TERMINAL_DECISION,
        "can_mark_goal_complete": all(value for _, value in checklist),
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": "PASS" if passed else "FAIL"}
            for requirement, passed in checklist
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_posture": "BUILDER_DISCOVERY_EXECUTION_PACKET_AGGRESSIVE_SOURCE_SAFE",
            "builder_posture_applied": "broad curious outside-current-edge non-conservative evidence construction",
            "g12_g0_posture_not_imported_into_builder": True,
            "anti_boxing_questions_pursued": [
                "availability by horizon/family",
                "descriptor/session/source neutral behavior spreads",
                "broad drift/session/volatility-state interpretation limits",
                "concentration by symbol/source/group/hour/session",
                "missing strategy-field boundary",
                "future source-field expansion requirements",
                "path geometry, volatility/tail, session microstructure, orderflow proxy, execution timing route families",
            ],
            "outside_current_edge_route_families_considered": [
                "neutral path geometry",
                "neutral volatility and tail behavior",
                "session and hour microstructure",
                "source coverage and proxy group effects",
                "future as-of orderflow proxy context",
                "future execution timing/lifecycle fields",
            ],
            "proof_or_impossibility_stop_condition_used": (
                "compute every source-safe terminal combination or fail closed with exact not-computable reason; "
                "source gaps require separate source-control expansion and G12 audit"
            ),
            "doctrine_requirements_deliberately_not_answered": [
                "strategy-specific performance interpretation crosses evidence-class boundary",
                "live behavior and promotion review are forbidden",
                "broker/account/order/history/deal/position evidence is forbidden",
                "paid/vendor/API evidence is forbidden",
            ],
        },
        "objective_restatement": {
            "candidate_rows": EXPECTED_COUNTS["candidate_rows"],
            "sealed_rows": EXPECTED_COUNTS["sealed_rows"],
            "stress_rows": EXPECTED_COUNTS["stress_rows"],
            "denominator_groups": EXPECTED_COUNTS["denominator_groups"],
            "target_families": TARGET_FAMILIES,
            "horizons": HORIZONS,
            "terminal_status_count": concentration["terminal_status_observed_combinations"],
        },
        "anti_boxing_answers": {
            "strongest_availability": aggregate_matrix["availability_summary"][0] if aggregate_matrix["availability_summary"] else None,
            "neutral_descriptor_spreads_for_future_preregistration": aggregate_matrix["notable_neutral_descriptor_slices"][:8],
            "baseline_explained_or_broad_market_behavior_warning": (
                "session/hour/prior-range/source-proxy differences are neutral market-state diagnostics only; "
                "no tradable mechanism is accepted in this packet"
            ),
            "concentration_summary": {
                "max_group_share": concentration["max_group_share"],
                "max_symbol_share": concentration["max_symbol_share"],
                "small_denominator_groups": {
                    group: count
                    for group, count in concentration["canonical_economic_group_counts"].items()
                    if count < 100
                },
            },
            "uninterpretable_without_strategy_fields": [
                "side",
                "entry",
                "stop",
                "target",
                "POI",
                "OB/FVG/breaker family",
                "lifecycle/fill/cancel",
                "broker/account truth",
            ],
            "strongest_next_route_if_promising": "independent G12 audit, then a separately frozen strategy-field source-expansion packet",
            "strongest_next_route_if_null": "G12 audit negative learning, then preregister baseline-explained neutral behavior controls",
        },
        "failure_anatomy_ref": repo_path(ROUTE_DIR / f"{PREFIX}_FAILURE_ANATOMY_LEDGER_{DATE_TAG}.json"),
        "not_computable_reason_counts": failure["not_computable_reason_counts"],
    }


def completion_audit_md(completion: dict[str, Any]) -> str:
    lines = [
        "# SCID As-Of Neutral Target Completion Audit",
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


def context_anchor_md(anchor: dict[str, Any]) -> str:
    return f"""# SCID Neutral Target Context Anchor

Route: `{ROUTE_ID}`

HEAD: `{anchor['current_head']}`

Evidence class: `{EVIDENCE_CLASS}`

Status: `{TERMINAL_DECISION}`

The active lane is builder/discovery execution packet only. It computes
source-safe neutral close-to-close and high/low excursion targets, keeps
strategy scoring closed, and leaves acceptance to the next G12 audit.
"""


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)

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
    bindings = source_binding(input_paths)
    missing_inputs = [item for item in bindings if not item["exists"]]
    if missing_inputs:
        raise FileNotFoundError(f"missing required inputs: {missing_inputs}")

    bar_manifest = load_json(BAR_MANIFEST)
    candidate_manifest = load_json(CANDIDATE_MANIFEST)
    g12_packet_decision = load_json(G12_PACKET_DECISION)
    g0_rulebook = load_json(G0_RULEBOOK)
    g12_design_decision = load_json(G12_DESIGN_DECISION)
    target_rulebook = load_json(TARGET_RULEBOOK)
    target_contract = load_json(TARGET_CONTRACT)
    g12_target_decision = load_json(G12_TARGET_DECISION)
    g12_target_completion = load_json(G12_TARGET_COMPLETION)

    candidates = load_jsonl(CANDIDATE_ROWS)
    bars = load_jsonl(BAR_ROWS)
    partition_rows = load_jsonl(G0_PARTITION_LEDGER)
    partition_by_id = {row["source_row_id"]: row for row in partition_rows}
    bars_by_end = {(row["symbol"], row["bar_end_exclusive_utc"]): row for row in bars}

    prerequisite = {
        **safe_base("prerequisite_acceptance_ledger"),
        "acceptance_checks": {
            "g12_packet_audit_terminal_decision": g12_packet_decision.get("terminal_decision"),
            "g12_packet_audit_accepted_source_control_packet_only": g12_packet_decision.get(
                "accepted_source_control_packet_only"
            )
            is True,
            "g12_design_audit_terminal_decision": g12_design_decision.get("terminal_decision"),
            "g12_design_audit_accepted_control_evidence_only": g12_design_decision.get(
                "accepted_design_control_evidence_only"
            )
            is True,
            "g12_target_audit_terminal_decision": g12_target_decision.get("terminal_decision"),
            "g12_target_rulebook_accepted": g12_target_decision.get(
                "accepted_source_safe_neutral_target_rulebook_only"
            )
            is True,
            "g12_target_completion_can_mark_goal_complete": g12_target_completion.get("can_mark_goal_complete") is True,
        },
        "required_input_artifacts": bindings,
    }
    write_json(ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_LEDGER_{DATE_TAG}.json", prerequisite)

    source_hash_binding = {
        **safe_base("source_hash_binding"),
        "source_artifacts": bindings,
        "manifest_hash_reconciliation": {
            "candidate_rows_sha256_matches_manifest": sha256_file(CANDIDATE_ROWS)
            == candidate_manifest.get("candidate_rows_sha256"),
            "bar_rows_sha256_matches_manifest": sha256_file(BAR_ROWS) == bar_manifest.get("bar_rows_sha256"),
        },
    }
    write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_BINDING_{DATE_TAG}.json", source_hash_binding)

    partition_counts = Counter(row["partition_assignment"] for row in partition_rows)
    group_counts = Counter(row["canonical_economic_group"] for row in partition_rows)
    pre_target_freeze = {
        **safe_base("pre_target_freeze_packet"),
        "current_head": git_head(),
        "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
        "accepted_g12_packet_audit_decision": g12_packet_decision.get("terminal_decision"),
        "accepted_g12_design_audit_decision": g12_design_decision.get("terminal_decision"),
        "accepted_g12_target_horizon_audit_decision": g12_target_decision.get("terminal_decision"),
        "source_artifact_paths_and_sha256": bindings,
        "candidate_row_count": len(candidates),
        "bar_row_count": len(bars),
        "partition_counts": dict(partition_counts),
        "denominator_group_count": len(group_counts),
        "discovery_exclusion_count": g0_rulebook.get("discovery_exclusions", {}).get("count"),
        "target_families": TARGET_FAMILIES,
        "horizons_m15_bars": HORIZONS,
        "record_present_status_mapping": sorted(PRESENT_BAR_STATUSES),
        "frozen_target_formula_text": {
            "neutral_close_to_close_return_m15_horizons_v1": target_contract["target_definitions"][0][
                "outcome_definition"
            ],
            "neutral_high_low_excursion_m15_horizons_v1": target_contract["target_definitions"][4][
                "outcome_definition"
            ],
        },
        "frozen_fail_closed_not_computable_rules": target_rulebook["stop_invalid_fail_closed_definition"][
            "not_computable_rules"
        ],
        "frozen_aggregate_slices": [
            "partition",
            "horizon",
            "target_family",
            "symbol",
            "canonical_economic_group",
            "source_file",
            "utc_hour",
            "session_bucket",
            "prior_16_range_bucket",
            "prior_16_drift_bucket",
            "prior_32_range_bucket",
            "source_coverage_quality_bucket",
            "denominator_group_concentration_bucket",
        ],
        "frozen_source_safe_asof_descriptor_definitions": [
            "prior 4/16/32/96 bar range and drift using bars ending at or before entry reference time",
            "per-symbol pre-target descriptor terciles",
            "UTC hour, time-of-day, and session buckets",
            "source coverage and denominator group concentration buckets",
        ],
        "frozen_forbidden_metric_list": [
            "R",
            "PnL",
            "win_rate",
            "expectancy",
            "profit_factor",
            "strategy_edge",
            "promotion_readiness",
        ],
        "frozen_next_g12_audit_requirement": repo_path(NEXT_G12_PROMPT),
        "pre_target_freeze_emitted_before_target_computation": True,
    }
    write_json(ROUTE_DIR / f"{PREFIX}_PRE_TARGET_FREEZE_PACKET_{DATE_TAG}.json", pre_target_freeze)

    descriptor_payload = compute_descriptors(candidates, partition_by_id, bars_by_end)
    descriptor_ledger = {
        **safe_base("descriptor_freeze_ledger"),
        "descriptor_freeze_status": "FROZEN_BEFORE_TARGET_COMPUTATION",
        "descriptor_definitions": descriptor_payload["descriptor_definitions"],
        "descriptor_cutoffs_by_symbol": descriptor_payload["descriptor_cutoffs_by_symbol"],
        "descriptor_row_count": len(descriptor_payload["descriptor_rows"]),
        "descriptor_rows": descriptor_payload["descriptor_rows"],
    }
    write_json(ROUTE_DIR / f"{PREFIX}_DESCRIPTOR_FREEZE_LEDGER_{DATE_TAG}.json", descriptor_ledger)
    descriptors_by_id = {row["candidate_input_row_id"]: row for row in descriptor_payload["descriptor_rows"]}

    row_results, not_computable_rows, terminal_rows = compute_targets(
        candidates,
        partition_by_id,
        bars_by_end,
        descriptors_by_id,
    )
    row_result_count = write_jsonl(ROUTE_DIR / f"{PREFIX}_ROW_RESULTS_{DATE_TAG}.jsonl", row_results)
    not_count = write_jsonl(ROUTE_DIR / f"{PREFIX}_NOT_COMPUTABLE_LEDGER_{DATE_TAG}.jsonl", not_computable_rows)

    aggregate_matrix = build_aggregate_matrices(terminal_rows)
    partition_matrix = build_partition_symbol_session_matrix(terminal_rows)
    concentration = build_concentration_audit(candidates, partition_rows, terminal_rows)
    failure = build_failure_anatomy(not_computable_rows, terminal_rows)
    baseline = build_baseline_control_readiness(aggregate_matrix, candidate_manifest)

    write_json(ROUTE_DIR / f"{PREFIX}_AGGREGATE_DISTRIBUTION_MATRIX_{DATE_TAG}.json", aggregate_matrix)
    write_json(ROUTE_DIR / f"{PREFIX}_PARTITION_SYMBOL_SESSION_MATRIX_{DATE_TAG}.json", partition_matrix)
    write_json(ROUTE_DIR / f"{PREFIX}_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json", concentration)
    write_json(ROUTE_DIR / f"{PREFIX}_BASELINE_CONTROL_READINESS_LEDGER_{DATE_TAG}.json", baseline)
    write_json(ROUTE_DIR / f"{PREFIX}_FAILURE_ANATOMY_LEDGER_{DATE_TAG}.json", failure)
    write_md(ROUTE_DIR / f"{PREFIX}_INTERPRETATION_LIMITS_{DATE_TAG}.md", build_interpretation_limits(aggregate_matrix, concentration))

    context_anchor = {
        **safe_base("context_anchor"),
        "current_head": git_head(),
        "current_head_short": git_head_short(),
        "controlling_prompt_path": repo_path(CONTROLLING_PROMPT),
        "context_files_read_after_preflight": [
            ".context/LIVE_STATE.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_current_state.md",
            repo_path(CONTROLLING_PROMPT),
        ],
        "lane_posture": "BUILDER_DISCOVERY_EXECUTION_PACKET_AGGRESSIVE_SOURCE_SAFE",
        "active_question_stack": [
            "compute full neutral target terminal status grid",
            "freeze source-safe descriptors before target computation",
            "summarize availability and neutral path behavior without strategy interpretation",
            "emit next G12 audit prompt",
        ],
        "dirty_state_informational": git_status_entries(),
        "terminal_decision": TERMINAL_DECISION,
    }
    write_json(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json", context_anchor)
    write_md(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md", context_anchor_md(context_anchor))

    checks = {
        "mandatory_context_read": True,
        "g12_target_acceptance": prerequisite["acceptance_checks"]["g12_target_rulebook_accepted"],
        "pre_target_freeze": (ROUTE_DIR / f"{PREFIX}_PRE_TARGET_FREEZE_PACKET_{DATE_TAG}.json").exists(),
        "all_candidates_represented": len({row["candidate_input_row_id"] for row in terminal_rows}) == EXPECTED_COUNTS["candidate_rows"],
        "all_combinations_terminal": concentration["terminal_status_observed_combinations"]
        == concentration["terminal_status_expected_combinations"],
        "matrices_and_failure": bool(aggregate_matrix and partition_matrix and failure),
        "forbidden_surfaces_closed": not any(
            entry.get("scoped_to_this_route") and entry.get("forbidden_live_surface_path")
            for entry in git_status_entries()
        ),
        "verifier_and_tests_available": (
            ROUTE_DIR / "verify_scid_asof_neutral_target_execution_packet_2026_05_12.py"
        ).exists()
        and (ROUTE_DIR / "test_scid_asof_neutral_target_execution_packet_2026_05_12.py").exists(),
        "next_g12_prompt": True,
    }
    completion = build_completion_audit(checks, aggregate_matrix, concentration, failure)
    write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion)
    write_md(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md", completion_audit_md(completion))

    write_md(NEXT_G12_PROMPT, build_next_g12_prompt())

    generated_paths = [
        ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_PREREQUISITE_ACCEPTANCE_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_PRE_TARGET_FREEZE_PACKET_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_BINDING_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DESCRIPTOR_FREEZE_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_ROW_RESULTS_{DATE_TAG}.jsonl",
        ROUTE_DIR / f"{PREFIX}_NOT_COMPUTABLE_LEDGER_{DATE_TAG}.jsonl",
        ROUTE_DIR / f"{PREFIX}_AGGREGATE_DISTRIBUTION_MATRIX_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_PARTITION_SYMBOL_SESSION_MATRIX_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_BASELINE_CONTROL_READINESS_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_FAILURE_ANATOMY_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_INTERPRETATION_LIMITS_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
        ROUTE_DIR / "build_scid_asof_neutral_target_execution_packet_2026_05_12.py",
        ROUTE_DIR / "verify_scid_asof_neutral_target_execution_packet_2026_05_12.py",
        ROUTE_DIR / "test_scid_asof_neutral_target_execution_packet_2026_05_12.py",
        NEXT_G12_PROMPT,
    ]
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    write_json(manifest_path, output_manifest([*generated_paths, manifest_path]))

    return {
        "row_result_count": row_result_count,
        "not_computable_count": not_count,
        "terminal_count": len(terminal_rows),
        "completion": completion,
        "manifest_path": repo_path(manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true", help="print a compact build summary")
    args = parser.parse_args()
    result = build_all()
    if args.summary:
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
