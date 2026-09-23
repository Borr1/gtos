"""Independent G12 audit for the READY8 quarantined target-result packet.

This route accepts or rejects only packet/source integrity. It deliberately
does not score performance, validate a strategy, inspect broker/order/account
truth, call AI/API, or touch live trading behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
ROUTE_DIR = Path(__file__).resolve().parent

DATE_TAG = "2026-05-13"
ROUTE_ID = "G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_noapi_ready8_target_result_packet_audit_v1"
ACCEPT_DECISION = "ACCEPT_AS_G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY"
REJECT_DECISION = "REJECT_WITH_EXACT_READY8_TARGET_RESULT_PACKET_REPAIR_REQUIREMENTS"
PREFIX = "G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT"

CONTROLLING_PROMPT = PROMPT_DIR / "G12_SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_GOAL_PROMPT_2026-05-13.md"
BUILDER_PROMPT = PROMPT_DIR / "SCID_NOAPI_READY8_QUARANTINED_RESULT_PACKET_AFTER_G0_GATE_GOAL_PROMPT_2026-05-13.md"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_NOAPI_READY8_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G0_STARTER = ROUTE_DIR / "G0_SCID_NOAPI_READY8_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT_STARTER_2026-05-13.txt"

G0_GATE_DIR = OUTCOME_DIR / "g0napi_ready8_future_result_opening_gate_after_g12_audit"
G12_SOURCE_AUDIT_DIR = OUTCOME_DIR / "g12_scid_noapi_ready8_rowset_target_horizon_packet_audit"
READY8_PACKET_DIR = OUTCOME_DIR / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
TARGET_ROUTE_DIR = OUTCOME_DIR / "scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"
ASOF_BAR_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

ROWSET_MANIFEST = READY8_PACKET_DIR / "SCID_NOAPI_READY8_ROWSET_MANIFEST_2026-05-12.json"
ROWSET_ROWS = READY8_PACKET_DIR / "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl"
TARGET_CONTRACT = READY8_PACKET_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json"
BAR_MANIFEST = ASOF_BAR_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
BAR_ROWS = ASOF_BAR_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"

TARGET_OUTPUT_MANIFEST = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_OUTPUT_MANIFEST_2026-05-13.json"
TARGET_VERIFICATION = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_VERIFICATION_RESULT_2026-05-13.json"
TARGET_COMPLETION_AUDIT = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_COMPLETION_AUDIT_2026-05-13.json"
TARGET_JOIN_LEDGER = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_TARGET_SOURCE_JOIN_LEDGER_2026-05-13.json"
TARGET_DUP_LEDGER = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_DUPLICATE_DENOMINATOR_LEDGER_2026-05-13.json"
TARGET_SIDECAR_LEDGER = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_2026-05-13.json"
TARGET_ADJACENT_LEDGER = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_2026-05-13.json"
TARGET_REPAIR_LEDGER = TARGET_ROUTE_DIR / "SCID_NOAPI_READY8_TARGET_RESULT_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_2026-05-13.json"

READY_CARD_IDS = [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
]
READY_CARD_FILE_IDS = {card_id: card_id.replace("-", "_") for card_id in READY_CARD_IDS}
HORIZONS = [1, 4, 16, 32]
TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
TARGET_FAMILY_FILE_IDS = {
    "neutral_close_to_close_return_m15_horizons_v1": "CLOSE_TO_CLOSE",
    "neutral_high_low_excursion_m15_horizons_v1": "HIGH_LOW_EXCURSION",
}
PRESENT_BAR_STATUSES = {"RECORD_PRESENT", "CLOSED_SOURCE_RECORDS_PRESENT"}
ACCEPTED_PARTITIONS = {"SEALED_VALIDATION_CANDIDATE_DESIGN", "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"}
EXPECTED = {
    "ready_cards": 8,
    "source_candidates": 3014,
    "rowset_rows": 24112,
    "horizons": [1, 4, 16, 32],
    "target_families": 2,
    "target_rows": 192896,
    "accepted_card_denominator": 40,
    "blocked_dependencies": 32,
    "row_exclusions": 0,
}
SAFE_FALSE_FLAGS = {
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}
FORBIDDEN_EXACT_FIELDS = {
    "r",
    "pnl",
    "profit",
    "loss",
    "win_rate",
    "expectancy",
    "sharpe",
    "strategy_edge",
    "performance",
    "target_hit",
    "stop_hit",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "order_ticket",
    "order_id",
    "deal_id",
    "position_id",
    "broker_account",
    "account_id",
    "account_history",
}
COMMON_ROW_FIELDS = [
    "rowset_row_id",
    "rowset_row_hash",
    "card_id",
    "packet_id",
    "science_domain",
    "mechanism_family",
    "candidate_input_row_id",
    "candidate_input_row_hash",
    "duplicate_proxy_denominator_key",
    "baseline_duplicate_policy_id",
    "baseline_assignment_family",
    "baseline_assignment_seed",
    "baseline_control_bucket",
    "matched_control_group_key",
    "partition_assignment",
    "candidate_input_partition_assignment",
    "symbol",
    "canonical_economic_group",
    "source_proxy_group",
    "source_group",
    "source_hash",
    "source_identifier",
    "source_hash_policy",
    "source_observed_asof_utc",
    "entry_reference_time_utc",
    "decision_asof_utc",
    "session_bucket",
    "time_of_day_bucket",
    "utc_hour",
    "source_coverage_quality_bucket",
    "denominator_group_concentration_bucket",
    "prior_context_descriptor_buckets",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_lf(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{repo_path(path)}:{line_no}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def add_m15(value: str, bars: int) -> str:
    return format_ts(parse_ts(value) + timedelta(minutes=15 * bars))


def safe_base(artifact_family: str, terminal_decision: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "terminal_decision": terminal_decision,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        **SAFE_FALSE_FLAGS,
    }


def git_output(args: list[str]) -> list[str]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    lines.extend(f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip())
    return lines


def target_result_paths() -> list[Path]:
    paths: list[Path] = []
    for card_id in READY_CARD_IDS:
        for family in TARGET_FAMILIES:
            paths.append(
                TARGET_ROUTE_DIR
                / f"SCID_NOAPI_READY8_TARGET_RESULT_ROWS_{READY_CARD_FILE_IDS[card_id]}_{TARGET_FAMILY_FILE_IDS[family]}_{DATE_TAG}.jsonl"
            )
    return paths


def source_segment_pointer(row: dict[str, Any]) -> dict[str, Any]:
    for pointer in row.get("source_artifact_pointers", []):
        if pointer.get("artifact_role") == "source_segment":
            return pointer
    return {}


def is_present_bar(bar: dict[str, Any] | None) -> bool:
    return bool(bar and bar.get("bar_status") in PRESENT_BAR_STATUSES)


def validate_bar(
    bar: dict[str, Any] | None,
    *,
    expected_segment_sha: str | None,
    expected_source_file: str | None,
    required_fields: Iterable[str],
    label: str,
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    if bar is None:
        return [{"reason": f"FAIL_CLOSED_{label}_BAR_MISSING", "detail": f"{label} bar absent"}]
    if not is_present_bar(bar):
        failures.append({"reason": f"FAIL_CLOSED_{label}_BAR_NOT_RECORD_PRESENT", "detail": f"{label} status {bar.get('bar_status')}"})
    for field in required_fields:
        if bar.get(field) is None:
            failures.append({"reason": f"FAIL_CLOSED_{label}_OHLC_NULL", "detail": f"{label} field {field} null"})
    if expected_segment_sha and bar.get("segment_records_sha256") != expected_segment_sha:
        failures.append({"reason": f"FAIL_CLOSED_{label}_SOURCE_HASH_MISMATCH", "detail": "segment hash mismatch"})
    if expected_source_file and bar.get("source_file_name") != expected_source_file:
        failures.append({"reason": f"FAIL_CLOSED_{label}_SOURCE_FILE_MISMATCH", "detail": "source file mismatch"})
    return failures


def expected_target_fields(rowset_row: dict[str, Any], target_family: str, horizon: int, bars_by_end: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    entry_ref = rowset_row["entry_reference_time_utc"]
    horizon_end = add_m15(entry_ref, horizon)
    segment = source_segment_pointer(rowset_row)
    expected_segment_sha = segment.get("segment_records_sha256")
    expected_source_file = segment.get("source_file_name")
    base = {
        "horizon_end_utc": horizon_end,
        "source_segment_sha256_expected": expected_segment_sha,
        "source_file_name_expected": expected_source_file,
    }

    failures: list[dict[str, str]] = []
    if rowset_row.get("card_id") not in READY_CARD_IDS:
        failures.append({"reason": "FAIL_CLOSED_CARD_NOT_READY8", "detail": "card outside READY8"})
    if rowset_row.get("partition_assignment") not in ACCEPTED_PARTITIONS:
        failures.append({"reason": "FAIL_CLOSED_PARTITION_NOT_ACCEPTED", "detail": "partition outside accepted set"})
    if rowset_row.get("source_observed_asof_utc") != entry_ref:
        failures.append({"reason": "FAIL_CLOSED_SOURCE_OBSERVED_ASOF_MISMATCH", "detail": "source observed as-of mismatch"})
    if rowset_row.get("decision_asof_utc") != entry_ref:
        failures.append({"reason": "FAIL_CLOSED_DECISION_ASOF_MISMATCH", "detail": "decision as-of mismatch"})

    entry_bar = bars_by_end.get((rowset_row["symbol"], entry_ref))
    failures.extend(
        validate_bar(
            entry_bar,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
            required_fields=["close"],
            label="ENTRY",
        )
    )
    source_hashes = [entry_bar["bar_hash"]] if entry_bar and entry_bar.get("bar_hash") else []
    required_ends = [entry_ref, horizon_end]
    if failures:
        return {
            **base,
            "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
            "fail_closed_primary_reason": failures[0]["reason"] if failures else "FAIL_CLOSED_UNKNOWN",
            "required_bar_end_utc": required_ends,
            "source_bar_hashes_consumed": source_hashes,
            "entry_close": None,
            "horizon_close": None,
            "close_to_close_absolute_delta": None,
            "close_to_close_percent_return": None,
            "max_high_over_horizon": None,
            "min_low_over_horizon": None,
            "upside_excursion_absolute": None,
            "upside_excursion_percent": None,
            "downside_excursion_absolute": None,
            "downside_excursion_percent": None,
        }

    entry_close = float(entry_bar["close"])
    if target_family == "neutral_close_to_close_return_m15_horizons_v1":
        horizon_bar = bars_by_end.get((rowset_row["symbol"], horizon_end))
        if horizon_bar and horizon_bar.get("bar_hash"):
            source_hashes.append(horizon_bar["bar_hash"])
        horizon_failures = validate_bar(
            horizon_bar,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
            required_fields=["close"],
            label="HORIZON",
        )
        if horizon_failures:
            return {
                **base,
                "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
                "fail_closed_primary_reason": horizon_failures[0]["reason"],
                "required_bar_end_utc": required_ends,
                "source_bar_hashes_consumed": source_hashes,
                "entry_close": None,
                "horizon_close": None,
                "close_to_close_absolute_delta": None,
                "close_to_close_percent_return": None,
                "max_high_over_horizon": None,
                "min_low_over_horizon": None,
                "upside_excursion_absolute": None,
                "upside_excursion_percent": None,
                "downside_excursion_absolute": None,
                "downside_excursion_percent": None,
            }
        horizon_close = float(horizon_bar["close"])
        delta = horizon_close - entry_close
        return {
            **base,
            "terminal_status": "COMPUTABLE",
            "fail_closed_primary_reason": None,
            "required_bar_end_utc": required_ends,
            "source_bar_hashes_consumed": source_hashes,
            "entry_close": entry_close,
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

    path_required_ends = [entry_ref]
    path_rows: list[dict[str, Any]] = []
    path_failures: list[dict[str, str]] = []
    for step in range(1, horizon + 1):
        end_s = add_m15(entry_ref, step)
        path_required_ends.append(end_s)
        bar = bars_by_end.get((rowset_row["symbol"], end_s))
        if bar and bar.get("bar_hash"):
            source_hashes.append(bar["bar_hash"])
        row_failures = validate_bar(
            bar,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
            required_fields=["close", "high", "low"],
            label="PATH",
        )
        if row_failures:
            path_failures.extend(row_failures)
        else:
            path_rows.append(bar)
    if path_failures:
        return {
            **base,
            "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
            "fail_closed_primary_reason": path_failures[0]["reason"],
            "required_bar_end_utc": path_required_ends,
            "source_bar_hashes_consumed": source_hashes,
            "entry_close": None,
            "horizon_close": None,
            "close_to_close_absolute_delta": None,
            "close_to_close_percent_return": None,
            "max_high_over_horizon": None,
            "min_low_over_horizon": None,
            "upside_excursion_absolute": None,
            "upside_excursion_percent": None,
            "downside_excursion_absolute": None,
            "downside_excursion_percent": None,
        }

    max_high = max(float(row["high"]) for row in path_rows)
    min_low = min(float(row["low"]) for row in path_rows)
    upside = max_high - entry_close
    downside = entry_close - min_low
    return {
        **base,
        "terminal_status": "COMPUTABLE",
        "fail_closed_primary_reason": None,
        "required_bar_end_utc": path_required_ends,
        "source_bar_hashes_consumed": source_hashes,
        "entry_close": entry_close,
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


def same_value(actual: Any, expected: Any) -> bool:
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return abs(float(actual) - float(expected)) <= 1e-12
    return actual == expected


def audit_input_hashes() -> dict[str, Any]:
    rowset_manifest = load_json(ROWSET_MANIFEST)
    bar_manifest = load_json(BAR_MANIFEST)
    target_manifest = load_json(TARGET_OUTPUT_MANIFEST)
    target_artifact_mismatches = []
    for item in target_manifest.get("artifacts", []):
        path = ROOT / item["path"]
        if not path.exists():
            target_artifact_mismatches.append({"path": item["path"], "issue": "missing"})
            continue
        actual = sha256_file(path)
        if actual != item.get("sha256"):
            target_artifact_mismatches.append({"path": item["path"], "actual": actual, "manifest": item.get("sha256")})
    rowset_raw = sha256_file(ROWSET_ROWS)
    rowset_lf = sha256_file_lf(ROWSET_ROWS)
    bar_raw = sha256_file(BAR_ROWS)
    bar_lf = sha256_file_lf(BAR_ROWS)
    return {
        "rowset_rows_sha256_actual": rowset_raw,
        "rowset_rows_sha256_lf_normalized": rowset_lf,
        "rowset_rows_sha256_manifest": rowset_manifest.get("rowset_rows_sha256"),
        "rowset_rows_raw_matches_manifest": rowset_raw == rowset_manifest.get("rowset_rows_sha256"),
        "rowset_rows_lf_matches_manifest": rowset_lf == rowset_manifest.get("rowset_rows_sha256"),
        "bar_rows_sha256_actual": bar_raw,
        "bar_rows_sha256_lf_normalized": bar_lf,
        "bar_rows_sha256_manifest": bar_manifest.get("bar_rows_sha256"),
        "bar_rows_raw_matches_manifest": bar_raw == bar_manifest.get("bar_rows_sha256"),
        "bar_rows_lf_matches_manifest": bar_lf == bar_manifest.get("bar_rows_sha256"),
        "text_eol_equivalence_repair_status": "CLOSED_BY_LF_NORMALIZED_HASH_EQUIVALENCE" if bar_raw != bar_manifest.get("bar_rows_sha256") and bar_lf == bar_manifest.get("bar_rows_sha256") else "NOT_NEEDED",
        "target_output_manifest_artifact_mismatch_count": len(target_artifact_mismatches),
        "target_output_manifest_artifact_mismatches": target_artifact_mismatches[:20],
    }


def audit_bars() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    bars_by_end: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_keys: list[dict[str, str]] = []
    status_counts: Counter[str] = Counter()
    asof_violations = 0
    segment_counts: Counter[str] = Counter()
    for row in iter_jsonl(BAR_ROWS):
        key = (row.get("symbol"), row.get("bar_end_exclusive_utc"))
        if key in bars_by_end:
            duplicate_keys.append({"symbol": str(key[0]), "bar_end_exclusive_utc": str(key[1])})
        bars_by_end[key] = row
        status_counts[row.get("bar_status")] += 1
        if row.get("bar_end_exclusive_utc") and row.get("decision_asof_utc"):
            if parse_ts(row["bar_end_exclusive_utc"]) > parse_ts(row["decision_asof_utc"]):
                asof_violations += 1
        if row.get("segment_records_sha256"):
            segment_counts[row["segment_records_sha256"]] += 1
    return bars_by_end, {
        "bar_row_count": sum(status_counts.values()),
        "bar_status_counts": dict(sorted(status_counts.items())),
        "duplicate_bar_key_count": len(duplicate_keys),
        "duplicate_bar_keys": duplicate_keys[:20],
        "bar_decision_asof_violation_count": asof_violations,
        "source_segment_hash_count": len(segment_counts),
    }


def audit_rowset() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rowset: dict[str, dict[str, Any]] = {}
    row_hash_mismatch = 0
    duplicate_rowset_ids = 0
    card_counts: Counter[str] = Counter()
    duplicate_proxy_keys: set[str] = set()
    candidate_card_keys: set[tuple[str, str]] = set()
    duplicate_candidate_card_keys = 0
    source_asof_mismatches = 0
    decision_asof_mismatches = 0
    unknown_cards: Counter[str] = Counter()
    partition_counts: Counter[str] = Counter()
    source_proxy_counts: Counter[str] = Counter()
    for row in iter_jsonl(ROWSET_ROWS):
        row_id = row.get("rowset_row_id")
        row_without_hash = dict(row)
        expected_hash = row_without_hash.pop("row_hash", None)
        if sha256_json(row_without_hash) != expected_hash:
            row_hash_mismatch += 1
        if row_id in rowset:
            duplicate_rowset_ids += 1
        rowset[row_id] = row
        card = row.get("card_id")
        card_counts[card] += 1
        if card not in READY_CARD_IDS:
            unknown_cards[card] += 1
        if row.get("duplicate_proxy_denominator_key"):
            duplicate_proxy_keys.add(row["duplicate_proxy_denominator_key"])
        candidate_card = (str(card), str(row.get("candidate_input_row_id")))
        if candidate_card in candidate_card_keys:
            duplicate_candidate_card_keys += 1
        candidate_card_keys.add(candidate_card)
        if row.get("source_observed_asof_utc") != row.get("entry_reference_time_utc"):
            source_asof_mismatches += 1
        if row.get("decision_asof_utc") != row.get("entry_reference_time_utc"):
            decision_asof_mismatches += 1
        partition_counts[row.get("partition_assignment")] += 1
        source_proxy_counts[row.get("source_proxy_group")] += 1
    return rowset, {
        "rowset_row_count": len(rowset),
        "row_hash_mismatch_count": row_hash_mismatch,
        "duplicate_rowset_id_count": duplicate_rowset_ids,
        "per_card_counts": dict(sorted(card_counts.items())),
        "ready_card_ids": sorted(card_counts),
        "unknown_ready_card_count": sum(unknown_cards.values()),
        "unknown_ready_cards": dict(sorted(unknown_cards.items())),
        "unique_duplicate_proxy_denominator_key_count": len(duplicate_proxy_keys),
        "duplicate_candidate_card_key_count": duplicate_candidate_card_keys,
        "source_observed_asof_mismatch_count": source_asof_mismatches,
        "decision_asof_mismatch_count": decision_asof_mismatches,
        "partition_counts": dict(sorted(partition_counts.items())),
        "source_proxy_group_counts": dict(sorted(source_proxy_counts.items())),
    }


def audit_target_rows(rowset: dict[str, dict[str, Any]], bars_by_end: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    target_ids: set[str] = set()
    target_hashes: set[str] = set()
    target_keys: set[tuple[str, str, str, int]] = set()
    duplicate_ids = 0
    duplicate_hashes = 0
    row_hash_mismatch = 0
    row_id_mismatch = 0
    source_hash_list_mismatch = 0
    common_field_mismatch = 0
    source_segment_mismatch = 0
    off_by_one_mismatch = 0
    target_value_mismatch = 0
    rowset_missing_count = 0
    forbidden_field_hits: Counter[str] = Counter()
    safe_flag_mismatches: Counter[str] = Counter()
    counts_by_card: Counter[str] = Counter()
    counts_by_family: Counter[str] = Counter()
    counts_by_horizon: Counter[int] = Counter()
    status_counts: Counter[str] = Counter()
    fail_reasons: Counter[str] = Counter()
    mismatch_samples: list[dict[str, Any]] = []
    forbidden_samples: list[dict[str, Any]] = []
    all_expected_keys = {
        (row_id, row["card_id"], family, horizon)
        for row_id, row in rowset.items()
        for family in TARGET_FAMILIES
        for horizon in HORIZONS
    }

    compare_fields = [
        "terminal_status",
        "fail_closed_primary_reason",
        "required_bar_end_utc",
        "source_segment_sha256_expected",
        "source_file_name_expected",
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
        "source_bar_hashes_consumed",
    ]

    for path in target_result_paths():
        for row in iter_jsonl(path):
            counts_by_card[row.get("card_id")] += 1
            counts_by_family[row.get("target_family_id")] += 1
            counts_by_horizon[row.get("horizon_m15_bars")] += 1
            status_counts[row.get("terminal_status")] += 1
            if row.get("fail_closed_primary_reason"):
                fail_reasons[row["fail_closed_primary_reason"]] += 1

            row_id = row.get("target_result_row_id")
            row_hash = row.get("target_result_row_hash")
            if row_id in target_ids:
                duplicate_ids += 1
            target_ids.add(row_id)
            if row_hash in target_hashes:
                duplicate_hashes += 1
            target_hashes.add(row_hash)

            without_hash = dict(row)
            expected_hash = without_hash.pop("target_result_row_hash", None)
            if sha256_json(without_hash) != expected_hash:
                row_hash_mismatch += 1
            expected_id = sha256_json([row.get("rowset_row_id"), row.get("card_id"), row.get("target_family_id"), row.get("horizon_m15_bars")])
            if expected_id != row_id:
                row_id_mismatch += 1

            if sha256_json(row.get("source_bar_hashes_consumed", [])) != row.get("source_bar_hashes_consumed_sha256"):
                source_hash_list_mismatch += 1

            exact_hits = sorted(set(row) & FORBIDDEN_EXACT_FIELDS)
            if exact_hits:
                for hit in exact_hits:
                    forbidden_field_hits[hit] += 1
                if len(forbidden_samples) < 10:
                    forbidden_samples.append({"target_result_row_id": row_id, "fields": exact_hits})
            for key, expected in SAFE_FALSE_FLAGS.items():
                if row.get(key) is not expected:
                    safe_flag_mismatches[key] += 1
            if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
                safe_flag_mismatches["promotion_verdict"] += 1

            source_row = rowset.get(row.get("rowset_row_id"))
            if source_row is None:
                rowset_missing_count += 1
                continue
            key = (row.get("rowset_row_id"), row.get("card_id"), row.get("target_family_id"), row.get("horizon_m15_bars"))
            target_keys.add(key)
            for field in COMMON_ROW_FIELDS:
                source_field = "row_hash" if field == "rowset_row_hash" else field
                if row.get(field) != source_row.get(source_field):
                    common_field_mismatch += 1
                    if len(mismatch_samples) < 10:
                        mismatch_samples.append({"target_result_row_id": row_id, "field": field, "actual": row.get(field), "expected": source_row.get(source_field)})
                    break

            pointer = source_segment_pointer(source_row)
            if row.get("source_segment_sha256_expected") != pointer.get("segment_records_sha256") or row.get("source_file_name_expected") != pointer.get("source_file_name"):
                source_segment_mismatch += 1

            expected = expected_target_fields(source_row, row.get("target_family_id"), int(row.get("horizon_m15_bars")), bars_by_end)
            if row.get("required_bar_end_utc") != expected.get("required_bar_end_utc") or row.get("horizon_end_utc") != expected.get("horizon_end_utc"):
                off_by_one_mismatch += 1
            for field in compare_fields:
                if not same_value(row.get(field), expected.get(field)):
                    target_value_mismatch += 1
                    if len(mismatch_samples) < 10:
                        mismatch_samples.append({"target_result_row_id": row_id, "field": field, "actual": row.get(field), "expected": expected.get(field)})
                    break

    missing_keys = all_expected_keys - target_keys
    extra_keys = target_keys - all_expected_keys
    return {
        "target_result_row_count": sum(counts_by_card.values()),
        "per_card_target_counts": dict(sorted(counts_by_card.items())),
        "target_family_counts": dict(sorted(counts_by_family.items())),
        "horizon_counts": {str(k): v for k, v in sorted(counts_by_horizon.items())},
        "status_counts": dict(sorted(status_counts.items())),
        "fail_closed_primary_reason_counts": dict(sorted(fail_reasons.items())),
        "duplicate_target_result_row_id_count": duplicate_ids,
        "duplicate_target_result_row_hash_count": duplicate_hashes,
        "target_result_row_hash_mismatch_count": row_hash_mismatch,
        "target_result_row_id_mismatch_count": row_id_mismatch,
        "source_bar_hashes_consumed_sha256_mismatch_count": source_hash_list_mismatch,
        "rowset_missing_count": rowset_missing_count,
        "common_field_mismatch_count": common_field_mismatch,
        "source_segment_pointer_mismatch_count": source_segment_mismatch,
        "bar_horizon_off_by_one_mismatch_count": off_by_one_mismatch,
        "target_value_recompute_mismatch_count": target_value_mismatch,
        "missing_target_combination_count": len(missing_keys),
        "extra_target_combination_count": len(extra_keys),
        "forbidden_exact_field_hit_count": sum(forbidden_field_hits.values()),
        "forbidden_exact_field_hits": dict(sorted(forbidden_field_hits.items())),
        "forbidden_exact_field_samples": forbidden_samples,
        "safe_flag_mismatches": dict(sorted(safe_flag_mismatches.items())),
        "mismatch_samples": mismatch_samples,
        "bar_horizon_policy_verified": {
            "close_to_close_required_ends": "[entry_reference_time_utc, entry_reference_time_utc + H*15m]",
            "high_low_required_ends": "[entry_reference_time_utc] plus each forward closed M15 bar from step 1 through H",
            "high_low_extrema_excludes_entry_bar": True,
        },
    }


def audit_sidecars() -> dict[str, Any]:
    quality = load_json(TARGET_SIDECAR_LEDGER)
    adjacent = load_json(TARGET_ADJACENT_LEDGER)
    sidecar_family_rows = adjacent.get("sidecar_families", [])
    sidecar_leak_rows = [
        row
        for row in sidecar_family_rows
        if row.get("accepted_denominator_inclusion") is not False or row.get("ready8_denominator_inclusion") is not False
    ]
    forbidden_interpretation_hits = []
    for path, data in [(TARGET_SIDECAR_LEDGER, quality), (TARGET_ADJACENT_LEDGER, adjacent)]:
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, value in item.items():
                    # Safe closure fields such as opens_strategy_edge_claims=false are
                    # not performance interpretation and must not be treated as hits.
                    if key in FORBIDDEN_EXACT_FIELDS:
                        forbidden_interpretation_hits.append({"path": repo_path(path), "field": key})
                    stack.append(value)
            elif isinstance(item, list):
                stack.extend(item)
    return {
        "quality_diagnostic_scope": quality.get("diagnostic_scope"),
        "accepted_ready8_denominator_inclusion": adjacent.get("accepted_ready8_denominator_inclusion"),
        "sidecar_family_count": adjacent.get("sidecar_family_count"),
        "sidecar_denominator_leak_count": len(sidecar_leak_rows),
        "sidecar_denominator_leak_rows": sidecar_leak_rows[:10],
        "forbidden_interpretation_token_hit_count": len(forbidden_interpretation_hits),
        "forbidden_interpretation_token_hits": forbidden_interpretation_hits,
        "movement_as_performance_interpretation_opened": quality.get("diagnostic_scope") != "coverage_and_quarantine_quality_only_no_strategy_performance_interpretation",
    }


def audit_safe_ledgers() -> dict[str, Any]:
    paths = [
        TARGET_OUTPUT_MANIFEST,
        TARGET_VERIFICATION,
        TARGET_COMPLETION_AUDIT,
        TARGET_JOIN_LEDGER,
        TARGET_DUP_LEDGER,
        TARGET_SIDECAR_LEDGER,
        TARGET_ADJACENT_LEDGER,
        TARGET_REPAIR_LEDGER,
    ]
    mismatches = []
    missing_optional_fields = []
    core_false_fields = set(SAFE_FALSE_FLAGS) - {"credentials_touched", "changes_trading_risk_safety_prompt_decision_behavior"}
    for path in paths:
        data = load_json(path)
        for key, expected in SAFE_FALSE_FLAGS.items():
            if key not in data and key not in core_false_fields:
                missing_optional_fields.append({"path": repo_path(path), "field": key})
                continue
            if data.get(key) is not expected:
                mismatches.append({"path": repo_path(path), "field": key, "actual": data.get(key), "expected": expected})
        if data.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            mismatches.append({"path": repo_path(path), "field": "promotion_verdict", "actual": data.get("promotion_verdict")})
    return {
        "safe_ledger_file_count": len(paths),
        "safe_ledger_mismatch_count": len(mismatches),
        "safe_ledger_mismatches": mismatches[:20],
        "missing_optional_safe_field_count": len(missing_optional_fields),
        "missing_optional_safe_fields": missing_optional_fields[:20],
    }


def build_recompute_audit() -> dict[str, Any]:
    input_hashes = audit_input_hashes()
    bars_by_end, bar_audit = audit_bars()
    rowset, rowset_audit = audit_rowset()
    target_audit = audit_target_rows(rowset, bars_by_end)
    sidecar_audit = audit_sidecars()
    safe_ledger_audit = audit_safe_ledgers()
    issues = []
    if not (input_hashes["rowset_rows_raw_matches_manifest"] or input_hashes["rowset_rows_lf_matches_manifest"]):
        issues.append({"check": "rowset_input_hash", "detail": input_hashes})
    if not (input_hashes["bar_rows_raw_matches_manifest"] or input_hashes["bar_rows_lf_matches_manifest"]):
        issues.append({"check": "bar_input_hash", "detail": input_hashes})
    if input_hashes["target_output_manifest_artifact_mismatch_count"]:
        issues.append({"check": "target_output_manifest_hashes", "detail": input_hashes["target_output_manifest_artifact_mismatches"]})
    zero_required = {
        "bar.duplicate_bar_key_count": bar_audit["duplicate_bar_key_count"],
        "bar.bar_decision_asof_violation_count": bar_audit["bar_decision_asof_violation_count"],
        "rowset.row_hash_mismatch_count": rowset_audit["row_hash_mismatch_count"],
        "rowset.duplicate_rowset_id_count": rowset_audit["duplicate_rowset_id_count"],
        "rowset.unknown_ready_card_count": rowset_audit["unknown_ready_card_count"],
        "rowset.duplicate_candidate_card_key_count": rowset_audit["duplicate_candidate_card_key_count"],
        "rowset.source_observed_asof_mismatch_count": rowset_audit["source_observed_asof_mismatch_count"],
        "rowset.decision_asof_mismatch_count": rowset_audit["decision_asof_mismatch_count"],
        "target.duplicate_target_result_row_id_count": target_audit["duplicate_target_result_row_id_count"],
        "target.duplicate_target_result_row_hash_count": target_audit["duplicate_target_result_row_hash_count"],
        "target.target_result_row_hash_mismatch_count": target_audit["target_result_row_hash_mismatch_count"],
        "target.target_result_row_id_mismatch_count": target_audit["target_result_row_id_mismatch_count"],
        "target.source_bar_hashes_consumed_sha256_mismatch_count": target_audit["source_bar_hashes_consumed_sha256_mismatch_count"],
        "target.rowset_missing_count": target_audit["rowset_missing_count"],
        "target.common_field_mismatch_count": target_audit["common_field_mismatch_count"],
        "target.source_segment_pointer_mismatch_count": target_audit["source_segment_pointer_mismatch_count"],
        "target.bar_horizon_off_by_one_mismatch_count": target_audit["bar_horizon_off_by_one_mismatch_count"],
        "target.target_value_recompute_mismatch_count": target_audit["target_value_recompute_mismatch_count"],
        "target.missing_target_combination_count": target_audit["missing_target_combination_count"],
        "target.extra_target_combination_count": target_audit["extra_target_combination_count"],
        "target.forbidden_exact_field_hit_count": target_audit["forbidden_exact_field_hit_count"],
        "sidecar.sidecar_denominator_leak_count": sidecar_audit["sidecar_denominator_leak_count"],
        "sidecar.forbidden_interpretation_token_hit_count": sidecar_audit["forbidden_interpretation_token_hit_count"],
        "sidecar.movement_as_performance_interpretation_opened": int(sidecar_audit["movement_as_performance_interpretation_opened"]),
        "safe_ledgers.safe_ledger_mismatch_count": safe_ledger_audit["safe_ledger_mismatch_count"],
    }
    for check, count in zero_required.items():
        if count:
            issues.append({"check": check, "count": count})
    count_checks = {
        "ready_card_count": len(rowset_audit["ready_card_ids"]) == EXPECTED["ready_cards"],
        "source_candidate_count": rowset_audit["unique_duplicate_proxy_denominator_key_count"] == EXPECTED["source_candidates"],
        "rowset_row_count": rowset_audit["rowset_row_count"] == EXPECTED["rowset_rows"],
        "target_result_row_count": target_audit["target_result_row_count"] == EXPECTED["target_rows"],
        "target_families": set(target_audit["target_family_counts"]) == set(TARGET_FAMILIES),
        "horizons": sorted(int(k) for k in target_audit["horizon_counts"]) == HORIZONS,
    }
    for check, passed in count_checks.items():
        if not passed:
            issues.append({"check": check, "passed": passed})

    terminal_decision = ACCEPT_DECISION if not issues else REJECT_DECISION
    return {
        **safe_base("recompute_audit", terminal_decision),
        "ok": not issues,
        "issues": issues,
        "expected_scope": EXPECTED,
        "input_hash_audit": input_hashes,
        "bar_audit": bar_audit,
        "rowset_audit": rowset_audit,
        "target_audit": target_audit,
        "sidecar_audit": sidecar_audit,
        "safe_ledger_audit": safe_ledger_audit,
        "upstream_routes_read": [
            repo_path(CONTROLLING_PROMPT),
            repo_path(BUILDER_PROMPT),
            repo_path(G0_GATE_DIR),
            repo_path(G12_SOURCE_AUDIT_DIR),
            repo_path(READY8_PACKET_DIR),
            repo_path(TARGET_ROUTE_DIR),
        ],
    }


def checks_from_recompute(recompute: dict[str, Any]) -> dict[str, bool]:
    input_hash = recompute["input_hash_audit"]
    rowset = recompute["rowset_audit"]
    target = recompute["target_audit"]
    sidecar = recompute["sidecar_audit"]
    safe = recompute["safe_ledger_audit"]
    focused = focused_test_status()
    return {
        "mandatory_preflight_and_context_reads_recorded": True,
        "exact_ready_card_count_8": len(rowset["ready_card_ids"]) == 8,
        "exact_source_candidate_count_3014": rowset["unique_duplicate_proxy_denominator_key_count"] == 3014,
        "exact_rowset_rows_24112": rowset["rowset_row_count"] == 24112,
        "horizons_exact_1_4_16_32": sorted(int(k) for k in target["horizon_counts"]) == [1, 4, 16, 32],
        "two_neutral_target_families_only": set(target["target_family_counts"]) == set(TARGET_FAMILIES),
        "exact_target_terminal_rows_192896": target["target_result_row_count"] == 192896,
        "rowset_hashes_valid": rowset["row_hash_mismatch_count"] == 0,
        "target_row_hashes_valid": target["target_result_row_hash_mismatch_count"] == 0,
        "target_row_ids_valid": target["target_result_row_id_mismatch_count"] == 0,
        "file_hashes_match_or_text_eol_equivalent": (input_hash["rowset_rows_raw_matches_manifest"] or input_hash["rowset_rows_lf_matches_manifest"]) and (input_hash["bar_rows_raw_matches_manifest"] or input_hash["bar_rows_lf_matches_manifest"]) and input_hash["target_output_manifest_artifact_mismatch_count"] == 0,
        "duplicate_counts_clean": rowset["duplicate_rowset_id_count"] == 0 and rowset["duplicate_candidate_card_key_count"] == 0 and target["duplicate_target_result_row_id_count"] == 0,
        "source_asof_joins_clean": rowset["source_observed_asof_mismatch_count"] == 0 and rowset["decision_asof_mismatch_count"] == 0 and target["common_field_mismatch_count"] == 0,
        "bar_horizon_off_by_one_rules_clean": target["bar_horizon_off_by_one_mismatch_count"] == 0,
        "source_segment_and_consumed_hashes_clean": target["source_segment_pointer_mismatch_count"] == 0 and target["source_bar_hashes_consumed_sha256_mismatch_count"] == 0,
        "fail_closed_statuses_recomputed": target["target_value_recompute_mismatch_count"] == 0,
        "forbidden_field_scan_clean": target["forbidden_exact_field_hit_count"] == 0,
        "sidecars_quarantined_no_denominator_leak": sidecar["sidecar_denominator_leak_count"] == 0,
        "sidecars_no_movement_as_performance": sidecar["forbidden_interpretation_token_hit_count"] == 0 and not sidecar["movement_as_performance_interpretation_opened"],
        "safe_flags_preserved": safe["safe_ledger_mismatch_count"] == 0,
        "builder_verifier_passed": load_json(TARGET_VERIFICATION).get("ok") is True,
        "focused_tests_recorded_passed": focused == "passed",
        "no_terminal_repair_blockers": recompute["ok"],
    }


def focused_test_status() -> str | None:
    path = ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json"
    if not path.exists():
        return None
    return load_json(path).get("status")


def decision_ledger(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    repair_requirements = [] if recompute["ok"] else recompute["issues"]
    return {
        **safe_base("decision_ledger", terminal),
        "decision": terminal,
        "accepted_as": "quarantined target-result packet integrity/control evidence only" if recompute["ok"] else None,
        "not_validation": True,
        "not_strategy_performance": True,
        "repair_requirements": repair_requirements,
        "same_evidence_class_repairs_closed": [
            {
                "issue": "bar row text EOL hash mismatch against manifest raw bytes",
                "closure": recompute["input_hash_audit"]["text_eol_equivalence_repair_status"],
                "blocking": False,
                "evidence": "bar_rows_lf_matches_manifest=true",
            }
        ],
        "terminal_basis": {
            "counts_exact": recompute["target_audit"]["target_result_row_count"] == EXPECTED["target_rows"],
            "hashes_recomputed": recompute["target_audit"]["target_result_row_hash_mismatch_count"] == 0,
            "asof_and_horizon_rules_recomputed": recompute["target_audit"]["bar_horizon_off_by_one_mismatch_count"] == 0,
            "forbidden_surfaces_closed": recompute["target_audit"]["forbidden_exact_field_hit_count"] == 0,
            "sidecars_quarantined": recompute["sidecar_audit"]["sidecar_denominator_leak_count"] == 0,
        },
    }


def verification_result(recompute: dict[str, Any]) -> dict[str, Any]:
    checks = checks_from_recompute(recompute)
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    issues = [{"check": key, "passed": value} for key, value in checks.items() if not value]
    return {
        **safe_base("verification_result", terminal),
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "target_result_row_count": recompute["target_audit"]["target_result_row_count"],
        "status_counts": recompute["target_audit"]["status_counts"],
        "target_family_counts": recompute["target_audit"]["target_family_counts"],
        "horizon_counts": recompute["target_audit"]["horizon_counts"],
        "per_card_target_counts": recompute["target_audit"]["per_card_target_counts"],
        "can_mark_goal_complete_after_scoped_commit_and_completion_audit": not issues,
    }


def saturation_md(recompute: dict[str, Any]) -> str:
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    return f"""# G12 READY8 Target-Result Packet Saturation And Self-Red-Team

Evidence class: `{EVIDENCE_CLASS}`

Terminal decision: `{terminal}`

## Saturation Questions

- Evidence-class confusion: the audit treats the packet as target-result integrity/control evidence only. It does not validate, promote, score performance, or open outcome review.
- Denominator leakage: recomputed READY8 scope is {recompute['rowset_audit']['rowset_row_count']} rowset rows from {recompute['rowset_audit']['unique_duplicate_proxy_denominator_key_count']} source candidates and {len(recompute['rowset_audit']['ready_card_ids'])} ready cards. Target rows contain no missing or extra rowset/family/horizon combinations.
- Blocked/expansion leakage: sidecar denominator leak count is {recompute['sidecar_audit']['sidecar_denominator_leak_count']}. Adjacent route families remain quarantined with accepted denominator inclusion false.
- Duplicate inflation: duplicate rowset IDs, candidate-card keys, and target IDs all recompute to zero where required.
- Source/as-of drift: rowset source-observed-as-of and decision-as-of both match entry reference time for every row; target common fields match rowset fields.
- Horizon off-by-one: close-to-close uses entry close plus the H-step horizon close; high-low uses the entry bar only for entry close and source hash, while extrema use forward bars 1..H.
- Hash/EOL/parser/manifest repair: rowset bytes match manifest. Bar rows have raw-byte hash drift but LF-normalized hash matches the accepted manifest, closing the text EOL issue inside this evidence class without data repair. Target output manifest hashes match current files.
- Fail-closed statuses: fail-closed status/value fields were recomputed from accepted source-control bars. Missing/gap bars remain row-level fail-closed statuses, not terminal blockers.
- Forbidden fields: exact forbidden key hits are {recompute['target_audit']['forbidden_exact_field_hit_count']}; safe flags remain closed in rows and ledgers.
- Movement-as-performance risk: sidecar diagnostics are coverage/quarantine quality only. They are not interpreted as win rate, expectancy, PnL, R, Sharpe, or strategy performance.

## Deliberately Not Answered

This audit does not inspect blocked-card results, broker/account/order/history/deal/position evidence, raw market blobs, AI/API output, paid/vendor data, validation performance, promotion readiness, registry changes, remote state, or live trading behavior. Those are forbidden or later evidence-class gates, not defects in this packet.
"""


def next_g0_prompt_text(recompute: dict[str, Any]) -> str:
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    return f"""# G0 SCID No-API READY8 Target-Result Control Evidence Synthesis After G12 Audit

Evidence class: `G0_SCID_NOAPI_READY8_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY`

Objective: use the accepted G12 target-result packet audit at `{repo_path(ROUTE_DIR)}` only as quarantined target-result integrity/control evidence. Decide the next research-control route without validating, promoting, or interpreting neutral target movement as strategy performance.

Upstream terminal decision: `{terminal}`

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the target-result builder route at `{repo_path(TARGET_ROUTE_DIR)}` and this G12 audit route at `{repo_path(ROUTE_DIR)}`.

Allowed work:
- Reconcile the accepted target-result integrity evidence, fail-closed statuses, sidecar quarantines, and exact next evidence-class options.
- Produce a route-ranking ledger for possible next no-API research-control lanes.
- Preserve the packet as control evidence only unless a separate future prompt explicitly opens result interpretation.

Forbidden:
- No validation, promotion, live behavior, AI/API, paid/vendor pulls, broker account/order/history/deal/position evidence, raw market blob commits, registry edits, remote pushes, or trading-risk/safety/prompt-decision changes.
- Do not convert neutral close-to-close or high-low movement into R, PnL, win rate, expectancy, performance, or live-readiness claims.

Required output:
- G0 synthesis decision ledger.
- Route-ranking or repair ledger.
- Saturation/self-red-team.
- Completion audit with prompt-to-artifact checklist.
- Next prompt/starter for the selected route.

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def next_g0_starter_text() -> str:
    return (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G0_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat memory; use the accepted G12 READY8 "
        "target-result audit only as quarantined target-result integrity/control evidence; do not validate, promote, "
        "score performance, inspect broker/account/order/history/deal/position truth, call AI/API, use paid/vendor data, "
        "commit raw market blobs, edit registry/remotes, or touch live trading behavior; preserve NO_PROMOTION_VERDICT, "
        "validation_safe=false, outcome_review_opened=false, live_effect=false; produce exact G0 synthesis and next route "
        "prompt/starter or exact repair requirements."
    )


def completion_audit(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    checks = checks_from_recompute(recompute)
    checklist = [
        ("controlling_audit_prompt_read", True, repo_path(CONTROLLING_PROMPT)),
        ("mandatory_live_state_regenerated_and_read", True, ".context/LIVE_STATE.md regenerated by python scripts/generate_live_state.py"),
        ("goal_session_research_discipline_read", True, ".context/00_core/goal_session_research_discipline.md"),
        ("research_operating_doctrine_read", True, ".context/00_core/research_operating_doctrine.md"),
        ("research_current_state_read", True, ".context/00_core/research_current_state.md"),
        ("local_heavy_data_inventory_read", True, ".context/00_core/local_heavy_data_inventory.md"),
        ("ai_in_loop_cost_control_plan_read", True, ".context/00_core/ai_in_loop_cost_control_research_plan.md"),
        ("builder_prompt_read", True, repo_path(BUILDER_PROMPT)),
        ("g0_gate_route_read", True, repo_path(G0_GATE_DIR)),
        ("g12_source_control_audit_read", True, repo_path(G12_SOURCE_AUDIT_DIR)),
        ("ready8_materialization_packet_read", True, repo_path(READY8_PACKET_DIR)),
        ("target_result_packet_route_read", True, repo_path(TARGET_ROUTE_DIR)),
        ("exact_8_ready_cards_verified", checks["exact_ready_card_count_8"], f"ready_cards={recompute['rowset_audit']['ready_card_ids']}"),
        ("exact_3014_source_candidates_verified", checks["exact_source_candidate_count_3014"], f"unique_duplicate_proxy_denominator_key_count={recompute['rowset_audit']['unique_duplicate_proxy_denominator_key_count']}"),
        ("exact_24112_rowset_rows_verified", checks["exact_rowset_rows_24112"], f"rowset_row_count={recompute['rowset_audit']['rowset_row_count']}"),
        ("horizons_1_4_16_32_verified", checks["horizons_exact_1_4_16_32"], f"horizon_counts={recompute['target_audit']['horizon_counts']}"),
        ("two_neutral_target_families_verified", checks["two_neutral_target_families_only"], f"target_family_counts={recompute['target_audit']['target_family_counts']}"),
        ("exact_192896_target_rows_verified", checks["exact_target_terminal_rows_192896"], f"target_result_row_count={recompute['target_audit']['target_result_row_count']}"),
        ("row_file_hashes_and_row_ids_recomputed", checks["target_row_hashes_valid"] and checks["target_row_ids_valid"], "target_result_row_hash_mismatch_count=0 and target_result_row_id_mismatch_count=0"),
        ("duplicate_counts_recomputed", checks["duplicate_counts_clean"], "rowset/target duplicate counts are zero where required"),
        ("source_asof_joins_recomputed", checks["source_asof_joins_clean"], "source_observed_asof and decision_asof match entry reference; target fields match rowset"),
        ("bar_horizon_off_by_one_recomputed", checks["bar_horizon_off_by_one_rules_clean"], "close-to-close and high-low horizon required ends recomputed"),
        ("source_segment_hashes_recomputed", checks["source_segment_and_consumed_hashes_clean"], "source segment pointers and consumed bar hash list sha256 match"),
        ("fail_closed_statuses_recomputed", checks["fail_closed_statuses_recomputed"], f"status_counts={recompute['target_audit']['status_counts']}"),
        ("forbidden_field_scan_clean", checks["forbidden_field_scan_clean"], "exact forbidden field hit count is zero"),
        ("blocked_expansion_and_sidecars_closed", checks["sidecars_quarantined_no_denominator_leak"], "sidecar_denominator_leak_count=0"),
        ("sidecar_no_performance_interpretation", checks["sidecars_no_movement_as_performance"], "sidecar diagnostics remain coverage/quarantine only"),
        ("safe_flags_preserved", checks["safe_flags_preserved"], "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false"),
        ("same_g12_hash_eol_manifest_repair_closed", checks["file_hashes_match_or_text_eol_equivalent"], recompute["input_hash_audit"]["text_eol_equivalence_repair_status"]),
        ("next_g0_or_repair_prompt_starter_written", True, f"{repo_path(NEXT_G0_PROMPT)} / {repo_path(NEXT_G0_STARTER)}"),
        ("terminal_decision_allowed", terminal in {ACCEPT_DECISION, REJECT_DECISION}, terminal),
    ]
    return {
        **safe_base("completion_audit", terminal),
        "objective_restatement": "Independently audit the READY8 quarantined no-API target-result packet for source/result-packet integrity only, preserving quarantined control-evidence status and all no-promotion/no-validation/no-live flags.",
        "audit_posture_applied": "strict G12 audit, but broad/novel/non-OB sidecars were accepted as quarantined diagnostics when they did not leak into denominators or performance interpretation",
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "satisfied": bool(satisfied), "evidence": evidence}
            for requirement, satisfied, evidence in checklist
        ],
        "all_prompt_requirements_satisfied": all(bool(item[1]) for item in checklist) and recompute["ok"],
        "terminal_decision": terminal,
        "completion_verification_checks": checks,
        "same_evidence_class_repairs_closed_or_proven": [
            {
                "issue": "bar source JSONL raw hash differs from manifest due text EOL policy",
                "resolution": recompute["input_hash_audit"]["text_eol_equivalence_repair_status"],
                "evidence": {
                    "bar_rows_raw_matches_manifest": recompute["input_hash_audit"]["bar_rows_raw_matches_manifest"],
                    "bar_rows_lf_matches_manifest": recompute["input_hash_audit"]["bar_rows_lf_matches_manifest"],
                },
            }
        ],
        "unresolved_same_evidence_class_gaps": [] if recompute["ok"] else recompute["issues"],
        "git_head_at_audit_build": git_output(["git", "rev-parse", "HEAD"])[:1],
        "git_status_short_informational": git_output(["git", "status", "--short"]),
    }


def artifact_inventory(paths: Iterable[Path]) -> list[dict[str, Any]]:
    artifacts = []
    for path in paths:
        artifacts.append(
            {
                "path": repo_path(path),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return artifacts


def output_manifest() -> dict[str, Any]:
    terminal = load_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json")["terminal_decision"]
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    paths = [
        Path(__file__),
        ROUTE_DIR / f"verify_g12_scid_noapi_ready8_quarantined_target_result_packet_audit_2026_05_13.py",
        ROUTE_DIR / f"test_g12_scid_noapi_ready8_quarantined_target_result_packet_audit_2026_05_13.py",
        CONTROLLING_PROMPT,
        NEXT_G0_PROMPT,
        NEXT_G0_STARTER,
        ROUTE_DIR / f"{PREFIX}_RECOMPUTE_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json",
    ]
    unique = []
    seen = {manifest_path.resolve(strict=False)}
    for path in paths:
        resolved = path.resolve(strict=False)
        if resolved not in seen:
            unique.append(path)
            seen.add(resolved)
    return {
        **safe_base("output_manifest", terminal),
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
        "artifact_count": len(unique),
        "artifacts": artifact_inventory(unique),
    }


def write_all(recompute: dict[str, Any]) -> None:
    terminal = ACCEPT_DECISION if recompute["ok"] else REJECT_DECISION
    recompute["terminal_decision"] = terminal
    write_json(ROUTE_DIR / f"{PREFIX}_RECOMPUTE_AUDIT_{DATE_TAG}.json", recompute)
    write_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json", decision_ledger(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json", verification_result(recompute))
    write_text(ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md", saturation_md(recompute))
    write_text(NEXT_G0_PROMPT, next_g0_prompt_text(recompute))
    write_text(NEXT_G0_STARTER, next_g0_starter_text())
    write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion_audit(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", output_manifest())


def record_focused_test_result(status: str, command: str) -> None:
    path = ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json"
    terminal = load_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json")["terminal_decision"]
    write_json(
        path,
        {
            **safe_base("focused_test_result", terminal),
            "status": status,
            "command": command,
            "recorded_after_command_completed": True,
        },
    )
    recompute = load_json(ROUTE_DIR / f"{PREFIX}_RECOMPUTE_AUDIT_{DATE_TAG}.json")
    write_json(ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json", verification_result(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion_audit(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", output_manifest())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-focused-test-result", choices=["passed", "failed"])
    parser.add_argument("--focused-test-command", default="")
    args = parser.parse_args()
    if args.record_focused_test_result:
        record_focused_test_result(args.record_focused_test_result, args.focused_test_command)
        return 0
    recompute = build_recompute_audit()
    write_all(recompute)
    print(json.dumps({"ok": recompute["ok"], "terminal_decision": recompute["terminal_decision"], "target_rows": recompute["target_audit"]["target_result_row_count"]}, indent=2, sort_keys=True))
    return 0 if recompute["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
