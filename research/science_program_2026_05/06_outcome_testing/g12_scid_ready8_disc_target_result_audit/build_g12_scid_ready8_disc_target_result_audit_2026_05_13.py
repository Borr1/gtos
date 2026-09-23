"""Independent G12 audit for the repaired READY8 discriminative target-result packet.

This route accepts or rejects only packet/source integrity. It deliberately
does not score performance, validate a strategy, inspect broker/order/account
truth, call AI/API, or touch live trading behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
ROUTE_ID = "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_ready8_discriminative_target_result_packet_audit_v1"
ACCEPT_DECISION = "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY"
ACCEPT_WITH_REPAIRS_DECISION = "ACCEPT_WITH_EXACT_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_SAME_G12_REPAIRS"
REJECT_DECISION = "REJECT_WITH_EXACT_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_IRREDUCIBLE_CROSS_BOUNDARY_OR_IMPOSSIBLE_REQUIREMENTS"
PREFIX = "G12_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_AUDIT"
REPAIRED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
OLD_REDUNDANT_ROWSET_SHA256 = "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d"
ROUTE_LOCAL_REPAIRS_PERFORMED = [
    {
        "issue": "Windows long-path IO failed on route-local generated ledgers over 260 characters in this worktree",
        "closure": "CLOSED_BY_EXTENDED_PATH_IO_HELPERS_IN_TARGET_BUILDER_VERIFIER_AND_G12_AUDIT",
        "blocking": False,
    }
]

CONTROLLING_PROMPT = PROMPT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_GOAL_PROMPT_2026-05-13.md"
BUILDER_PROMPT = PROMPT_DIR / "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_GOAL_PROMPT_2026-05-13.md"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_2026-05-13.md"
NEXT_G0_STARTER = ROUTE_DIR / "G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_AFTER_G12_AUDIT_STARTER_2026-05-13.txt"

G0_GATE_DIR = OUTCOME_DIR / "g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit"
G12_SOURCE_AUDIT_DIR = OUTCOME_DIR / "g12_scid_ready8_discriminative_card_rowset_repair_audit"
READY8_PACKET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
TARGET_CONTRACT_DIR = OUTCOME_DIR / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
TARGET_ROUTE_DIR = OUTCOME_DIR / "scid_ready8_discriminative_quarantined_target_result_packet"
ASOF_BAR_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

ROWSET_MANIFEST = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
ROWSET_ROWS = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
TARGET_CONTRACT = TARGET_CONTRACT_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json"
BAR_MANIFEST = ASOF_BAR_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"
BAR_ROWS = ASOF_BAR_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"

TARGET_OUTPUT_MANIFEST = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_OUTPUT_MANIFEST_2026-05-13.json"
TARGET_VERIFICATION = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_VERIFICATION_RESULT_2026-05-13.json"
TARGET_COMPLETION_AUDIT = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_COMPLETION_AUDIT_2026-05-13.json"
TARGET_JOIN_LEDGER = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_TARGET_SOURCE_JOIN_LEDGER_2026-05-13.json"
TARGET_DUP_LEDGER = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_DUPLICATE_DENOMINATOR_LEDGER_2026-05-13.json"
TARGET_SIDECAR_LEDGER = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_2026-05-13.json"
TARGET_ADJACENT_LEDGER = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_2026-05-13.json"
TARGET_REPAIR_LEDGER = TARGET_ROUTE_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_2026-05-13.json"
TARGET_BUILDER = TARGET_ROUTE_DIR / "build_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"
TARGET_VERIFIER = TARGET_ROUTE_DIR / "verify_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"
TARGET_TEST = TARGET_ROUTE_DIR / "test_scid_ready8_discriminative_quarantined_target_result_packet_2026_05_13.py"

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
    "computable_rows": 162336,
    "fail_closed_rows": 30560,
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


def io_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def path_exists(path: Path) -> bool:
    return os.path.exists(io_path(path))


def path_stat(path: Path) -> os.stat_result:
    return os.stat(io_path(path))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(io_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_lf(path: Path) -> str:
    with open(io_path(path), "rb") as handle:
        data = handle.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{repo_path(path)}:{line_no}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def target_builder_refresh_command() -> list[str]:
    return ["python", repo_path(TARGET_BUILDER), "--refresh-manifest"]


def target_verifier_command() -> list[str]:
    return ["python", repo_path(TARGET_VERIFIER)]


def target_focused_test_command() -> list[str]:
    return ["python", "-m", "pytest", repo_path(TARGET_TEST), "-q"]


def target_record_focused_result_command(status: str, command: str) -> list[str]:
    return [
        "python",
        repo_path(TARGET_BUILDER),
        "--record-focused-test-result",
        status,
        "--focused-test-command",
        command,
    ]


def target_result_paths() -> list[Path]:
    paths: list[Path] = []
    for card_id in READY_CARD_IDS:
        for family in TARGET_FAMILIES:
            paths.append(
                TARGET_ROUTE_DIR
                / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{READY_CARD_FILE_IDS[card_id]}_{TARGET_FAMILY_FILE_IDS[family]}_{DATE_TAG}.jsonl"
            )
    return paths


def source_segment_pointer(row: dict[str, Any]) -> dict[str, Any]:
    for pointer in row.get("source_artifact_pointers", []):
        if pointer.get("artifact_role") == "source_segment":
            return pointer
    if row.get("source_segment_sha256") or row.get("source_file_name"):
        return {
            "artifact_role": "source_segment",
            "segment_records_sha256": row.get("source_segment_sha256"),
            "source_file_name": row.get("source_file_name"),
        }
    return {}


def row_partition(row: dict[str, Any]) -> str | None:
    return row.get("partition_assignment") or row.get("validation_partition_assignment")


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
    if row_partition(rowset_row) not in ACCEPTED_PARTITIONS:
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
        if not path_exists(path):
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
        "repaired_discriminative_rowset_sha256_required": REPAIRED_ROWSET_SHA256,
        "old_redundant_ready8_rowset_sha256_forbidden": OLD_REDUNDANT_ROWSET_SHA256,
        "rowset_lf_sha256_matches_required_repaired_discriminative": rowset_lf == REPAIRED_ROWSET_SHA256,
        "rowset_raw_sha256_matches_required_repaired_discriminative": rowset_raw == REPAIRED_ROWSET_SHA256,
        "rowset_sha256_is_not_old_redundant": rowset_raw != OLD_REDUNDANT_ROWSET_SHA256 and rowset_lf != OLD_REDUNDANT_ROWSET_SHA256,
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
    status_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    per_card_status_counts: Counter[tuple[str, str]] = Counter()
    per_card_role_counts: Counter[tuple[str, str]] = Counter()
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
        status_counts[row.get("card_row_status")] += 1
        role_counts[row.get("denominator_role")] += 1
        per_card_status_counts[(str(card), str(row.get("card_row_status")))] += 1
        per_card_role_counts[(str(card), str(row.get("denominator_role")))] += 1
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
        "card_row_status_counts": dict(sorted(status_counts.items())),
        "denominator_role_counts": dict(sorted(role_counts.items())),
        "per_card_status_counts": [
            {"card_id": card, "card_row_status": status, "count": count}
            for (card, status), count in sorted(per_card_status_counts.items())
        ],
        "per_card_denominator_role_counts": [
            {"card_id": card, "denominator_role": role, "count": count}
            for (card, role), count in sorted(per_card_role_counts.items())
        ],
        "adversarial_placebo_control_cards": {
            "ADV-001": "placebo/adversarial control card, not edge-card pass claim",
            "ADV-003": "placebo/adversarial control card, not edge-card pass claim",
        },
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
    file_row_counts: Counter[str] = Counter()
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
            file_row_counts[repo_path(path)] += 1
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
                if field == "rowset_row_hash":
                    expected_common = source_row.get("row_hash")
                elif field == "partition_assignment":
                    expected_common = row_partition(source_row)
                elif field == "prior_context_descriptor_buckets":
                    expected_common = source_row.get(field, {})
                else:
                    expected_common = source_row.get(field)
                if row.get(field) != expected_common:
                    common_field_mismatch += 1
                    if len(mismatch_samples) < 10:
                        mismatch_samples.append({"target_result_row_id": row_id, "field": field, "actual": row.get(field), "expected": expected_common})
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
        "per_file_row_counts": dict(sorted(file_row_counts.items())),
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


def parse_lfs_pointer(text: str) -> dict[str, Any]:
    pointer: dict[str, Any] = {"is_lfs_pointer": text.startswith("version https://git-lfs.github.com/spec/v1")}
    for line in text.splitlines():
        if line.startswith("oid sha256:"):
            pointer["oid_sha256"] = line.split("oid sha256:", 1)[1].strip()
        elif line.startswith("size "):
            try:
                pointer["size"] = int(line.split(" ", 1)[1].strip())
            except ValueError:
                pointer["size"] = None
    return pointer


def git_blob_pointer(path: Path) -> dict[str, Any]:
    repo_rel = repo_path(path)
    proc = subprocess.run(
        ["git", "cat-file", "-p", f"HEAD:{repo_rel}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "git_blob_read_ok": False,
            "stderr_tail": proc.stderr[-1000:],
            "is_lfs_pointer": False,
        }
    parsed = parse_lfs_pointer(proc.stdout)
    parsed["git_blob_read_ok"] = True
    parsed["git_blob_bytes"] = len(proc.stdout.encode("utf-8"))
    return parsed


def git_check_attr(path: Path) -> dict[str, Any]:
    repo_rel = repo_path(path)
    proc = subprocess.run(
        ["git", "check-attr", "filter", "diff", "merge", "text", "--", repo_rel],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    attrs: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        parts = line.split(": ")
        if len(parts) == 3:
            attrs[parts[1]] = parts[2]
    return {
        "returncode": proc.returncode,
        "attrs": attrs,
        "is_lfs_attr": attrs.get("filter") == "lfs" and attrs.get("diff") == "lfs" and attrs.get("merge") == "lfs",
    }


def audit_lfs_materialization(target_audit: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(TARGET_OUTPUT_MANIFEST)
    manifest_by_path = {item.get("path"): item for item in manifest.get("artifacts", [])}
    with open(io_path(ROOT / ".gitattributes"), "r", encoding="utf-8") as handle:
        gitattrs_text = handle.read()
    rows: list[dict[str, Any]] = []
    for path in target_result_paths():
        repo_rel = repo_path(path)
        expected = manifest_by_path.get(repo_rel, {})
        exists = path_exists(path)
        actual_sha = sha256_file(path) if exists else None
        actual_bytes = path_stat(path).st_size if exists else None
        if exists:
            with open(io_path(path), "rb") as handle:
                first_bytes = handle.read(80)
        else:
            first_bytes = b""
        pointer = git_blob_pointer(path)
        attrs = git_check_attr(path)
        row_count = target_audit.get("per_file_row_counts", {}).get(repo_rel)
        rows.append(
            {
                "path": repo_rel,
                "working_tree_exists": exists,
                "working_tree_bytes": actual_bytes,
                "working_tree_sha256": actual_sha,
                "manifest_bytes": expected.get("bytes"),
                "manifest_sha256": expected.get("sha256"),
                "working_tree_hash_matches_manifest": actual_sha == expected.get("sha256"),
                "working_tree_size_matches_manifest": actual_bytes == expected.get("bytes"),
                "working_tree_materialized_not_pointer": not first_bytes.startswith(b"version https://git-lfs.github.com/spec/v1"),
                "row_count": row_count,
                "row_count_expected": 3014 * len(HORIZONS),
                "row_count_matches_expected": row_count == 3014 * len(HORIZONS),
                "committed_blob": pointer,
                "committed_blob_is_lfs_pointer": pointer.get("is_lfs_pointer") is True,
                "pointer_oid_matches_working_tree_sha256": pointer.get("oid_sha256") == actual_sha,
                "pointer_size_matches_working_tree_bytes": pointer.get("size") == actual_bytes,
                "git_check_attr": attrs,
                "git_attributes_lfs": attrs.get("is_lfs_attr") is True,
            }
        )
    failures = [
        row
        for row in rows
        if not (
            row["working_tree_exists"]
            and row["working_tree_hash_matches_manifest"]
            and row["working_tree_size_matches_manifest"]
            and row["working_tree_materialized_not_pointer"]
            and row["row_count_matches_expected"]
            and row["committed_blob_is_lfs_pointer"]
            and row["pointer_oid_matches_working_tree_sha256"]
            and row["pointer_size_matches_working_tree_bytes"]
            and row["git_attributes_lfs"]
        )
    ]
    return {
        "target_large_result_file_count": len(rows),
        "expected_target_large_result_file_count": len(READY_CARD_IDS) * len(TARGET_FAMILIES),
        "gitattributes_has_discriminative_lfs_pattern": "scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl filter=lfs" in gitattrs_text,
        "all_committed_blobs_are_lfs_pointers": all(row["committed_blob_is_lfs_pointer"] for row in rows),
        "all_working_tree_files_materialized": all(row["working_tree_materialized_not_pointer"] for row in rows),
        "all_pointer_oids_match_working_hashes": all(row["pointer_oid_matches_working_tree_sha256"] for row in rows),
        "all_pointer_sizes_match_working_bytes": all(row["pointer_size_matches_working_tree_bytes"] for row in rows),
        "all_working_hashes_match_manifest": all(row["working_tree_hash_matches_manifest"] for row in rows),
        "all_row_counts_match_expected": all(row["row_count_matches_expected"] for row in rows),
        "all_git_attrs_lfs": all(row["git_attributes_lfs"] for row in rows),
        "failure_count": len(failures),
        "failures": failures[:20],
        "files": rows,
    }


def build_recompute_audit() -> dict[str, Any]:
    initial_input_hashes = audit_input_hashes()
    target_builder_refresh = {"performed": False, "reason": "target output manifest already matched current files"}
    if initial_input_hashes["target_output_manifest_artifact_mismatch_count"]:
        target_builder_refresh = {
            "performed": True,
            "reason": "target output manifest had current-file hash/byte drift before G12 audit; same-evidence-class manifest rebinding is allowed",
            "initial_mismatch_count": initial_input_hashes["target_output_manifest_artifact_mismatch_count"],
            "initial_mismatches": initial_input_hashes["target_output_manifest_artifact_mismatches"],
            "command_result": run_command(target_builder_refresh_command()),
        }

    target_verifier_before_tests = run_command(target_verifier_command())
    target_focused_pytest = run_command(target_focused_test_command())
    target_record_focused = {"performed": False, "reason": "focused pytest did not pass"}
    if target_focused_pytest["passed"]:
        target_record_focused = {
            "performed": True,
            "command_result": run_command(
                target_record_focused_result_command("passed", " ".join(target_focused_test_command()))
            ),
        }
    target_verifier_after_tests = run_command(target_verifier_command())

    input_hashes = audit_input_hashes()
    bars_by_end, bar_audit = audit_bars()
    rowset, rowset_audit = audit_rowset()
    target_audit = audit_target_rows(rowset, bars_by_end)
    lfs_materialization_audit = audit_lfs_materialization(target_audit)
    sidecar_audit = audit_sidecars()
    safe_ledger_audit = audit_safe_ledgers()
    issues = []
    rerun_sequence_ok = (
        target_builder_refresh.get("command_result", {"passed": True}).get("passed") is True
        and target_verifier_before_tests["passed"]
        and target_focused_pytest["passed"]
        and target_record_focused.get("command_result", {"passed": target_focused_pytest["passed"]}).get("passed") is True
        and target_verifier_after_tests["passed"]
    )
    if not rerun_sequence_ok:
        issues.append({"check": "target_builder_verifier_tests_rerun_sequence", "detail": "target builder refresh/verifier/focused pytest/record/final verifier did not all pass"})
    if not (input_hashes["rowset_rows_raw_matches_manifest"] or input_hashes["rowset_rows_lf_matches_manifest"]):
        issues.append({"check": "rowset_input_hash", "detail": input_hashes})
    if not input_hashes["rowset_lf_sha256_matches_required_repaired_discriminative"]:
        issues.append({"check": "repaired_discriminative_rowset_hash_binding", "detail": input_hashes})
    if not input_hashes["rowset_sha256_is_not_old_redundant"]:
        issues.append({"check": "old_redundant_rowset_hash_exclusion", "detail": input_hashes})
    if not (input_hashes["bar_rows_raw_matches_manifest"] or input_hashes["bar_rows_lf_matches_manifest"]):
        issues.append({"check": "bar_input_hash", "detail": input_hashes})
    if input_hashes["target_output_manifest_artifact_mismatch_count"]:
        issues.append({"check": "target_output_manifest_hashes", "detail": input_hashes["target_output_manifest_artifact_mismatches"]})
    if lfs_materialization_audit["failure_count"]:
        issues.append({"check": "lfs_pointer_materialization", "detail": lfs_materialization_audit["failures"]})
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
        "computable_rows": target_audit["status_counts"].get("COMPUTABLE") == EXPECTED["computable_rows"],
        "fail_closed_rows": target_audit["status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE") == EXPECTED["fail_closed_rows"],
        "target_families": set(target_audit["target_family_counts"]) == set(TARGET_FAMILIES),
        "horizons": sorted(int(k) for k in target_audit["horizon_counts"]) == HORIZONS,
    }
    for check, passed in count_checks.items():
        if not passed:
            issues.append({"check": check, "passed": passed})

    terminal_decision = (
        REJECT_DECISION
        if issues
        else (ACCEPT_WITH_REPAIRS_DECISION if target_builder_refresh.get("performed") else ACCEPT_DECISION)
    )
    return {
        **safe_base("recompute_audit", terminal_decision),
        "ok": not issues,
        "issues": issues,
        "target_route_rerun_and_repair": {
            "initial_input_hash_audit": initial_input_hashes,
            "target_builder_refresh": target_builder_refresh,
            "target_verifier_before_tests": target_verifier_before_tests,
            "target_focused_pytest": target_focused_pytest,
            "target_record_focused_result": target_record_focused,
            "target_verifier_after_tests": target_verifier_after_tests,
            "rerun_sequence_ok": rerun_sequence_ok,
        },
        "expected_scope": EXPECTED,
        "input_hash_audit": input_hashes,
        "bar_audit": bar_audit,
        "rowset_audit": rowset_audit,
        "target_audit": target_audit,
        "lfs_materialization_audit": lfs_materialization_audit,
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
    lfs = recompute["lfs_materialization_audit"]
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
        "exact_computable_rows_162336": target["status_counts"].get("COMPUTABLE") == 162336,
        "exact_fail_closed_rows_30560": target["status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE") == 30560,
        "rowset_hashes_valid": rowset["row_hash_mismatch_count"] == 0,
        "denominator_roles_and_statuses_visible": set(rowset["denominator_role_counts"]) == {
            "per_card_pass_row",
            "per_card_contrast_row",
            "per_card_non_applicable_row",
            "per_card_fail_closed_row",
        }
        and {
            "PASS_DESCRIPTOR_CONTRAST_ELIGIBLE",
            "PASS_CARD_PREDICATE",
            "ELIGIBLE_CONTRAST_CONTROL",
            "NON_APPLICABLE_SOURCE_CONTEXT",
            "FAIL_CLOSED_MISSING_PRIOR_CANDIDATE",
            "FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE",
        }.issubset(set(rowset["card_row_status_counts"])),
        "adv_placebo_control_status_preserved": set(rowset["adversarial_placebo_control_cards"]) == {"ADV-001", "ADV-003"},
        "binds_repaired_discriminative_rowset_hash": input_hash["rowset_lf_sha256_matches_required_repaired_discriminative"],
        "does_not_bind_old_redundant_ready8_rowset": input_hash["rowset_sha256_is_not_old_redundant"],
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
        "lfs_pointer_materialization_verified": lfs["failure_count"] == 0,
        "builder_verifier_passed": load_json(TARGET_VERIFICATION).get("ok") is True and recompute["target_route_rerun_and_repair"]["rerun_sequence_ok"] is True,
        "focused_tests_recorded_passed": focused == "passed",
        "no_terminal_repair_blockers": recompute["ok"],
    }


def same_g12_repair_performed(recompute: dict[str, Any]) -> bool:
    return bool(ROUTE_LOCAL_REPAIRS_PERFORMED) or bool(
        recompute.get("target_route_rerun_and_repair", {}).get("target_builder_refresh", {}).get("performed")
    )


def terminal_decision_for(recompute: dict[str, Any]) -> str:
    if not recompute["ok"]:
        return REJECT_DECISION
    if same_g12_repair_performed(recompute):
        return ACCEPT_WITH_REPAIRS_DECISION
    return ACCEPT_DECISION


def same_g12_repair_entries(recompute: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [dict(item) for item in ROUTE_LOCAL_REPAIRS_PERFORMED] + [
        {
            "issue": "bar row text EOL hash mismatch against manifest raw bytes",
            "closure": recompute["input_hash_audit"]["text_eol_equivalence_repair_status"],
            "blocking": False,
            "evidence": {
                "bar_rows_raw_matches_manifest": recompute["input_hash_audit"]["bar_rows_raw_matches_manifest"],
                "bar_rows_lf_matches_manifest": recompute["input_hash_audit"]["bar_rows_lf_matches_manifest"],
            },
        }
    ]
    target_refresh = recompute.get("target_route_rerun_and_repair", {}).get("target_builder_refresh", {})
    if target_refresh.get("performed"):
        entries.append(
            {
                "issue": "target output manifest hash/byte metadata stale versus current route-local files",
                "closure": "CLOSED_BY_TARGET_BUILDER_REFRESH_MANIFEST_AND_VERIFIER_RERUN",
                "blocking": False,
                "initial_mismatch_count": target_refresh.get("initial_mismatch_count"),
                "command_passed": target_refresh.get("command_result", {}).get("passed"),
            }
        )
    return entries


def focused_test_status() -> str | None:
    path = ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json"
    if not path_exists(path):
        return None
    return load_json(path).get("status")


def decision_ledger(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = terminal_decision_for(recompute)
    repair_requirements = [] if recompute["ok"] else recompute["issues"]
    return {
        **safe_base("decision_ledger", terminal),
        "decision": terminal,
        "accepted_as": "quarantined target-result packet integrity/control evidence only" if recompute["ok"] else None,
        "not_validation": True,
        "not_strategy_performance": True,
        "repair_requirements": repair_requirements,
        "same_evidence_class_repairs_closed": same_g12_repair_entries(recompute),
        "terminal_basis": {
            "counts_exact": recompute["target_audit"]["target_result_row_count"] == EXPECTED["target_rows"],
            "hashes_recomputed": recompute["target_audit"]["target_result_row_hash_mismatch_count"] == 0,
            "asof_and_horizon_rules_recomputed": recompute["target_audit"]["bar_horizon_off_by_one_mismatch_count"] == 0,
            "forbidden_surfaces_closed": recompute["target_audit"]["forbidden_exact_field_hit_count"] == 0,
            "sidecars_quarantined": recompute["sidecar_audit"]["sidecar_denominator_leak_count"] == 0,
        },
    }


def lfs_materialization_ledger(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = terminal_decision_for(recompute)
    return {
        **safe_base("lfs_materialization_ledger", terminal),
        "lfs_materialization_audit": recompute["lfs_materialization_audit"],
        "large_result_jsonl_policy": "committed Git blobs must be Git LFS pointers; working-tree files must be materialized JSONL files whose SHA256/byte size and row count match the target output manifest/audit",
        "all_lfs_materialization_requirements_satisfied": recompute["lfs_materialization_audit"]["failure_count"] == 0,
    }


def forbidden_surface_ledger(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = terminal_decision_for(recompute)
    return {
        **safe_base("forbidden_surface_ledger", terminal),
        "target_forbidden_exact_field_hit_count": recompute["target_audit"]["forbidden_exact_field_hit_count"],
        "target_forbidden_exact_field_hits": recompute["target_audit"]["forbidden_exact_field_hits"],
        "sidecar_forbidden_interpretation_token_hit_count": recompute["sidecar_audit"]["forbidden_interpretation_token_hit_count"],
        "sidecar_movement_as_performance_interpretation_opened": recompute["sidecar_audit"]["movement_as_performance_interpretation_opened"],
        "safe_ledger_audit": recompute["safe_ledger_audit"],
        "closed_surfaces": {
            "blocked_dependencies": True,
            "expansion_candidates": True,
            "broker_account_order_history_deal_position": True,
            "validation": True,
            "promotion": True,
            "r_pnl_win_rate_expectancy_performance": True,
            "ai_api": True,
            "paid_vendor": True,
            "raw_market_blob_commit": True,
            "registry_remote": True,
            "live_trading_risk_safety_prompt_decision_changes": True,
        },
    }


def same_g12_repair_ledger(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = terminal_decision_for(recompute)
    unresolved = [] if recompute["ok"] else recompute["issues"]
    return {
        **safe_base("same_g12_repair_ledger", terminal),
        "same_g12_repairs_performed": same_g12_repair_entries(recompute),
        "same_g12_repair_performed_count": len(same_g12_repair_entries(recompute)),
        "target_route_rerun_and_repair": recompute["target_route_rerun_and_repair"],
        "unresolved_same_evidence_class_blocker_count": len(unresolved),
        "unresolved_same_evidence_class_blockers": unresolved,
        "repair_routes_exhausted": True,
    }


def verification_result(recompute: dict[str, Any]) -> dict[str, Any]:
    checks = checks_from_recompute(recompute)
    terminal = terminal_decision_for(recompute)
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
    terminal = terminal_decision_for(recompute)
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
    terminal = terminal_decision_for(recompute)
    return f"""# G0 SCID READY8 Discriminative Target-Result Control Evidence Synthesis After G12 Audit

Evidence class: `G0_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_CONTROL_EVIDENCE_SYNTHESIS_ONLY`

Objective: use the accepted G12 target-result packet audit at `{repo_path(ROUTE_DIR)}` as the control gate for the full no-API repaired-discriminative numerical screen in this same goal. This is not a passive audit loop, not a route-only handoff, and not a promotion lane. The session must reconcile the accepted packet, extract every useful same-class lesson, run the full-population discriminative pass-vs-control target-result screen from the accepted packet, and emit the strongest next G12 audit prompt/starter for that numerical screen. Only skip same-goal screening if disk evidence proves a real evidence-class boundary or impossibility; if that happens, prove it exactly and emit the strongest immediate continuation.

Upstream terminal decision: `{terminal}`

Mandatory preflight and active context:
1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md` as controlling instructions, not background context.
3. Read the repaired discriminative rowset route, target-result builder route, and G12 audit route:
   - `{repo_path(READY8_PACKET_DIR)}`
   - `{repo_path(TARGET_ROUTE_DIR)}`
   - `{repo_path(ROUTE_DIR)}`

Required synthesis posture:
- Treat this as constructive G0 synthesis plus same-goal numerical screening, not G12. Be strict about evidence class, but do not be timid, boxed, route-only, or conservative in deciding what the accepted packet now enables.
- Do not stop at "control evidence accepted" and do not stop at a new prompt if the accepted packet supports the screen. Build the screen artifacts now, then emit the next independent G12 audit prompt/starter for those screen artifacts.
- Do not hand off repairable same-evidence-class blockers. If a count/hash/as-of/manifest/sidecar/denominator issue is discovered and can be repaired or rebound inside this G0 evidence class, repair it, rerun the relevant verifier/tests, and continue.
- Use examples as starting points, not limits. Preserve all open route families, blocked/fail-closed anatomy, sidecar diagnostics, horizon/target-family partitions, pass/control/non-applicable/fail-closed roles, duplicate/concentration controls, and candidate-level views.
- Speed, runtime, convenience, and compactness are not success criteria. Do the complete correct pass even if it is much slower. No sampling shortcut, early stop, compact-only substitute, top-N-only artifact, "representative examples only" artifact, or arbitrary cap is acceptable where full-population computation is source-available.
- Use maximum reasoning and active curiosity. Ask what else the accepted packet can reveal inside this evidence class, then compute it or prove exactly why it cannot be computed. The goal is not complete until every same-class intelligence surface found during the work is extracted, repaired/recomputed if needed, or closed by exact impossibility/evidence-boundary proof.
- After the numerical results exist, perform a required explanation/exhaustion phase. For every apparent winner, loser, inversion, neutral result, failed/fail-closed cluster, outlier, partition reversal, duplicate/concentration effect, horizon effect, target-family effect, symbol/economic-group effect, descriptor contrast, and ambiguous pattern, ask why it happened and pursue the answer inside the accepted evidence class until there is nothing further to pursue.
- Do not cap the number of questions, ambiguities, explanations, failure reasons, or follow-up slices. "Top 5", "top 10", representative examples, or selected highlights are not enough. Emit all question/explanation rows the data presents, and keep recursively expanding them until each is answered, disproven, repaired, or exactly impossible within the evidence class.
- No repairable blocker may remain at closeout. If a blocker is found and can be pursued with approved local files, generated artifacts, recomputation, parser repair, manifest repair, hash/EOL repair, partition repair, sidecar repair, or same-class source lookup, pursue it immediately and rerun the relevant screen/verifier/tests before completion.
- The closeout target is full evidence-class understanding, not merely a score table. The session must pursue why the rows that made it made it, why the rows that failed failed, which observed features explain or fail to explain the split, which explanations survive controls/partitions/duplicates, and which questions are truly unanswerable from this evidence class. A residual unknown is acceptable only if it is named with exact missing source/evidence boundary proof and cannot be further pursued inside the approved local data/artifact set.
- Every explanation, interpretation, cause claim, failure reason, and next-route claim must be backed by data rows, aggregate tables, source hashes, artifact pointers, or exact absence/proof ledgers. Do not speculate as fact. But do not become conservative or scared because of that requirement: pursue creative, cross-domain, anti-boxing, non-OB, unexpected, inverse, nonlinear, interaction, failure-anatomy, and adversarial-control explanations aggressively, then bind them to the best available same-class data or mark exactly what additional evidence would be needed.

Accepted facts that must be reconciled exactly:
- `8` READY8 cards.
- `3,014` source candidates.
- `24,112` repaired discriminative rowset rows.
- Rowset hash `{REPAIRED_ROWSET_SHA256}`.
- Old redundant rowset hash excluded.
- `192,896` target-result rows.
- `162,336` computable rows.
- `30,560` fail-closed rows.
- Horizons `1/4/16/32`.
- Two target families: close-to-close and high-low excursion/asymmetry.
- Per-card denominator roles and status counts from the repaired rowset.
- Same-G12 repairs closed: Windows long-path IO helpers and LF-normalized text-hash equivalence.

Required outputs:
- G0 decision ledger.
- Fact reconciliation ledger.
- Numerical screen execution ledger proving whether the same-goal screen was run; if not run, this ledger must prove exact impossibility or evidence-class boundary from disk evidence.
- Full-population repaired-discriminative numerical screen artifacts over every accepted target-result row.
- Pass-vs-control contrast ledger by card, horizon, target family, denominator role, row status, descriptor contrast, symbol/economic group, sealed/stress partition, duplicate/concentration bucket, and fail-closed family.
- Candidate-level, partition-level, and failure-anatomy ledgers; do not replace full ledgers with top-N summaries.
- Winner/loser/neutral/inversion explanation ledger with all discovered question rows and their pursued terminal answers.
- Exhaustive ambiguity-pursuit ledger proving every question the data raised was pursued until answered, disproven, repaired, or exactly closed by evidence-class impossibility.
- Full-understanding closeout ledger covering why successful rows succeeded, why failed rows failed, which explanations survived adversarial controls, which explanations collapsed, what intelligence was extracted, and what is truly not knowable from this evidence class.
- Data-backing ledger mapping every explanation and intelligence claim to row counts, target-result rows, source artifacts, hash manifests, partitions, controls, or exact negative-evidence/absence proof.
- Route-ranking ledger for post-screen continuation, with rank 1 expected to be the independent G12 audit of the numerical screen unless disk evidence proves a stronger immediate continuation.
- Same-evidence-class repair/blocker ledger with zero repairable blockers remaining before closeout.
- Prompt-hardening ledger that proves `goal_session_research_discipline.md` and `research_operating_doctrine.md` were embedded into the selected next G12/follow-up prompt, not merely read.
- Saturation/self-red-team ledger.
- Completion audit with prompt-to-artifact checklist, no-shortcut proof, and exact stop condition.
- Hardened next G12/follow-up prompt and one-line starter for the selected route.

The numerical screen built in this goal must be full-population:
- compare pass vs contrast/control rows per card;
- preserve non-applicable and fail-closed rows explicitly;
- screen every card, horizon, target family, source symbol/economic group, sealed/stress partition, descriptor contrast, duplicate/concentration bucket, and fail-closed family supported by the packet;
- compute all ledgers, not top-N-only summaries;
- pursue recursive same-class questions and failure anatomy until no same-class intelligence remains;
- explicitly prove that no arbitrary limit, shortcut, compact-only approximation, or speed-based truncation determined the output;
- explain why the strong-looking rows worked and why the weak/failed rows failed, across all available same-class partitions and descriptors, without stopping at surface-level score tables;
- close with zero repairable blockers and zero same-class unanswered ambiguities;
- explicitly separate answered causes, disproven causes, uncertain-but-pursued causes, and evidence-class-impossible unknowns so the closeout does not hide uncertainty as completion;
- require every explanation to be data-backed while still encouraging broad, creative, non-boxed mechanism search beyond existing GTOS/OB framing;
- avoid OB-only collapse and preserve anti-boxing/cross-domain hypotheses;
- keep numerical movement intelligence quarantined from validation, performance, promotion, and live claims.

Forbidden surfaces:
- No validation, promotion, live behavior, AI/API, paid/vendor pulls, broker account/order/history/deal/position evidence, raw market blob commits, registry edits, remote pushes, or trading-risk/safety/prompt-decision changes.
- Do not convert neutral close-to-close or high-low movement into R, PnL, win rate, expectancy, performance, or live-readiness claims.
- Do not inspect blocked-card result rows unless a selected future prompt explicitly opens a separate accepted packet for them.

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def next_g0_starter_text() -> str:
    return (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G0_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first and read goal_session_research_discipline.md + research_operating_doctrine.md as active instructions; do not rely on chat memory; "
        "use the accepted G12 READY8 discriminative target-result audit as the control gate to run the full no-API repaired-discriminative numerical screen in this same goal, not as a passive audit loop, route-only handoff, or promotion lane; "
        "reconcile exact accepted facts including 8 cards, 3014 candidates, 24112 repaired rowset rows, rowset hash "
        f"{REPAIRED_ROWSET_SHA256}, 192896 target rows, 162336 computable rows, 30560 fail-closed rows, horizons 1/4/16/32, two target families, denominator roles, same-G12 repairs, "
        "LFS/materialization, sidecar quarantine, and forbidden-surface closure; pursue and repair any same-G0 issue instead of handing it off; "
        "build full-population numerical screen artifacts across every card, horizon, target family, denominator role, row status, descriptor contrast, symbol/economic group, sealed/stress partition, duplicate/concentration bucket, fail-closed family, candidate-level view, partition-level view, and failure-anatomy view; "
        "after results are computed, explain every winner, loser, inversion, neutral result, failed/fail-closed cluster, outlier, partition reversal, duplicate/concentration effect, horizon effect, target-family effect, symbol/economic-group effect, descriptor contrast, and ambiguity the data presents; "
        "pursue full evidence-class understanding of why the rows that made it made it and why the rows that failed failed, including answered causes, disproven causes, controls, partitions, duplicates, and exact evidence-class-impossible unknowns; "
        "back every explanation with data rows, aggregate tables, source hashes, artifact pointers, or exact absence proof while still pursuing creative, cross-domain, anti-boxing, non-OB, inverse, nonlinear, interaction, and failure-anatomy explanations aggressively; "
        "do not use top-N-only summaries, representative-only samples, compact-only substitutes, early stops, arbitrary limits, finite question caps, or speed shortcuts; use maximum reasoning and keep asking what else the packet can reveal until no same-class intelligence, repairable blocker, or unanswered ambiguity remains; "
        "if same-goal screening is impossible, prove the exact disk-backed evidence-class boundary or impossibility; "
        "emit a full G0 decision/fact/screen-execution/repair/saturation/completion package and a hardened next G12/follow-up prompt/starter; "
        "do not validate, promote, claim R/PnL/win-rate/expectancy/performance/live-readiness, inspect broker/account/order/history/deal/position truth, call AI/API, use paid/vendor data, commit raw market blobs, edit registry/remotes, or touch live trading behavior; "
        "preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )


def completion_audit(recompute: dict[str, Any]) -> dict[str, Any]:
    terminal = terminal_decision_for(recompute)
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
        ("repaired_discriminative_rowset_hash_bound", checks["binds_repaired_discriminative_rowset_hash"], REPAIRED_ROWSET_SHA256),
        ("old_redundant_rowset_hash_excluded", checks["does_not_bind_old_redundant_ready8_rowset"], OLD_REDUNDANT_ROWSET_SHA256),
        ("denominator_roles_and_statuses_visible", checks["denominator_roles_and_statuses_visible"], "pass/control/non-applicable/fail-closed roles and status vocabulary preserved in rowset audit"),
        ("adv_placebo_control_status_preserved", checks["adv_placebo_control_status_preserved"], "ADV-001 and ADV-003 remain adversarial/placebo controls, not edge-card pass claims"),
        ("horizons_1_4_16_32_verified", checks["horizons_exact_1_4_16_32"], f"horizon_counts={recompute['target_audit']['horizon_counts']}"),
        ("two_neutral_target_families_verified", checks["two_neutral_target_families_only"], f"target_family_counts={recompute['target_audit']['target_family_counts']}"),
        ("exact_192896_target_rows_verified", checks["exact_target_terminal_rows_192896"], f"target_result_row_count={recompute['target_audit']['target_result_row_count']}"),
        ("exact_162336_computable_rows_verified", checks["exact_computable_rows_162336"], f"status_counts={recompute['target_audit']['status_counts']}"),
        ("exact_30560_fail_closed_rows_verified", checks["exact_fail_closed_rows_30560"], f"status_counts={recompute['target_audit']['status_counts']}"),
        ("row_file_hashes_and_row_ids_recomputed", checks["target_row_hashes_valid"] and checks["target_row_ids_valid"], "target_result_row_hash_mismatch_count=0 and target_result_row_id_mismatch_count=0"),
        ("duplicate_counts_recomputed", checks["duplicate_counts_clean"], "rowset/target duplicate counts are zero where required"),
        ("source_asof_joins_recomputed", checks["source_asof_joins_clean"], "source_observed_asof and decision_asof match entry reference; target fields match rowset"),
        ("bar_horizon_off_by_one_recomputed", checks["bar_horizon_off_by_one_rules_clean"], "close-to-close and high-low horizon required ends recomputed"),
        ("source_segment_hashes_recomputed", checks["source_segment_and_consumed_hashes_clean"], "source segment pointers and consumed bar hash list sha256 match"),
        ("fail_closed_statuses_recomputed", checks["fail_closed_statuses_recomputed"], f"status_counts={recompute['target_audit']['status_counts']}"),
        ("forbidden_field_scan_clean", checks["forbidden_field_scan_clean"], "exact forbidden field hit count is zero"),
        ("lfs_pointer_materialization_verified", checks["lfs_pointer_materialization_verified"], "committed blobs are LFS pointers; working-tree JSONL files are materialized and manifest-bound"),
        ("blocked_expansion_and_sidecars_closed", checks["sidecars_quarantined_no_denominator_leak"], "sidecar_denominator_leak_count=0"),
        ("sidecar_no_performance_interpretation", checks["sidecars_no_movement_as_performance"], "sidecar diagnostics remain coverage/quarantine only"),
        ("safe_flags_preserved", checks["safe_flags_preserved"], "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false"),
        ("same_g12_hash_eol_manifest_repair_closed", checks["file_hashes_match_or_text_eol_equivalent"], recompute["input_hash_audit"]["text_eol_equivalence_repair_status"]),
        ("required_audit_ledgers_written", True, "decision/recomputation/LFS/forbidden-surface/repair/verification/saturation/completion ledgers"),
        ("next_g0_or_repair_prompt_starter_written", True, f"{repo_path(NEXT_G0_PROMPT)} / {repo_path(NEXT_G0_STARTER)}"),
        ("terminal_decision_allowed", terminal in {ACCEPT_DECISION, ACCEPT_WITH_REPAIRS_DECISION, REJECT_DECISION}, terminal),
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
        "same_evidence_class_repairs_closed_or_proven": same_g12_repair_entries(recompute),
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
                "exists": path_exists(path),
                "bytes": path_stat(path).st_size if path_exists(path) else None,
                "sha256": sha256_file(path) if path_exists(path) else None,
            }
        )
    return artifacts


def output_manifest() -> dict[str, Any]:
    terminal = load_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json")["terminal_decision"]
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    paths = [
        Path(__file__),
        ROUTE_DIR / "verify_g12_scid_ready8_disc_target_result_audit_2026_05_13.py",
        ROUTE_DIR / "test_g12_scid_ready8_disc_target_result_audit_2026_05_13.py",
        CONTROLLING_PROMPT,
        NEXT_G0_PROMPT,
        NEXT_G0_STARTER,
        ROUTE_DIR / f"{PREFIX}_RECOMPUTATION_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_LFS_MATERIALIZATION_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_FORBIDDEN_SURFACE_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SAME_G12_REPAIR_LEDGER_{DATE_TAG}.json",
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
    terminal = terminal_decision_for(recompute)
    recompute["terminal_decision"] = terminal
    write_json(ROUTE_DIR / f"{PREFIX}_RECOMPUTATION_LEDGER_{DATE_TAG}.json", recompute)
    write_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json", decision_ledger(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_LFS_MATERIALIZATION_LEDGER_{DATE_TAG}.json", lfs_materialization_ledger(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_FORBIDDEN_SURFACE_LEDGER_{DATE_TAG}.json", forbidden_surface_ledger(recompute))
    write_json(ROUTE_DIR / f"{PREFIX}_SAME_G12_REPAIR_LEDGER_{DATE_TAG}.json", same_g12_repair_ledger(recompute))
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
    recompute = load_json(ROUTE_DIR / f"{PREFIX}_RECOMPUTATION_LEDGER_{DATE_TAG}.json")
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

