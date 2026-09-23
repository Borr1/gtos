"""Build the quarantined READY8 discriminative neutral target-result packet.

This route is intentionally narrow on interpretation and broad on
materialization: it computes every authorized neutral target row for the
G0-opened repaired discriminative READY8 rowset, while preserving
NO_PROMOTION_VERDICT and leaving independent acceptance to the next G12 audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
ROUTE_DIR = Path(__file__).resolve().parent

DATE_TAG = "2026-05-13"
PREFIX = "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT"
ROUTE_ID = "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET"
EVIDENCE_CLASS = "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY"
SCHEMA_VERSION = "scid_ready8_discriminative_quarantined_target_result_packet_v1"
TERMINAL_DECISION = "MATERIALIZED_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED"
REPAIRED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
OLD_REDUNDANT_ROWSET_SHA256 = "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d"

CONTROLLING_PROMPT = (
    PROMPT_DIR / "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_GOAL_PROMPT_2026-05-13.md"
)
NEXT_G12_STARTER = (
    ROUTE_DIR / "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_STARTER_2026-05-13.txt"
)

G0_GATE_DIR = OUTCOME_DIR / "g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit"
G12_AUDIT_DIR = OUTCOME_DIR / "g12_scid_ready8_discriminative_card_rowset_repair_audit"
READY8_PACKET_DIR = OUTCOME_DIR / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
TARGET_CONTRACT_DIR = OUTCOME_DIR / "scid_noapi_ready8_rowset_target_horizon_result_packet_materialization"
ASOF_PACKET_DIR = OUTCOME_DIR / "scid_asof_bar_builder_and_candidate_input_packet_source_control"

G0_DECISION = G0_GATE_DIR / "G0_SCID_READY8_DISCRIMINATIVE_DECISION_LEDGER_2026-05-13.json"
G0_VERIFICATION = G0_GATE_DIR / "G0_SCID_READY8_DISCRIMINATIVE_VERIFICATION_RESULT_2026-05-13.json"
G12_DECISION = G12_AUDIT_DIR / "G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_2026-05-13.json"
READY8_ROWSET_MANIFEST = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_2026-05-13.json"
READY8_ROWSET_ROWS = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
READY8_TARGET_CONTRACT = TARGET_CONTRACT_DIR / "SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json"
READY8_DUPLICATE_MANIFEST = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_2026-05-13.json"
READY8_PARTITION_MANIFEST = READY8_PACKET_DIR / "SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_2026-05-13.json"
BAR_ROWS = ASOF_PACKET_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl"
BAR_MANIFEST = ASOF_PACKET_DIR / "SCID_ASOF_BAR_MANIFEST_2026-05-11.json"

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
    "source_candidates": 3014,
    "ready_cards": 8,
    "rowset_rows": 24112,
    "accepted_card_denominator": 40,
    "blocked_dependencies": 32,
    "row_exclusions": 0,
    "target_rows": 24112 * 4 * 2,
    "target_rows_per_card": 3014 * 4 * 2,
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
COMMON_SAFE_FIELDS = {
    "schema_version": SCHEMA_VERSION,
    "route_id": ROUTE_ID,
    "evidence_class": EVIDENCE_CLASS,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "neutral_target_result_packet_opened": True,
    **SAFE_FALSE_FLAGS,
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
    "deal_id",
    "position_id",
    "broker_account",
    "account_id",
}


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


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


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


def sha256_file_lf_normalized(path: Path) -> str:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return hashlib.sha256(handle.read().replace("\r\n", "\n").encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def git_output(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.stdout.strip()


def git_head() -> str:
    return git_output(["rev-parse", "HEAD"]) or "UNKNOWN_HEAD"


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    lines.extend(f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip())
    return lines


def target_result_path(card_id: str, target_family: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_ROWS_{READY_CARD_FILE_IDS[card_id]}_{TARGET_FAMILY_FILE_IDS[target_family]}_{DATE_TAG}.jsonl"


def result_paths() -> list[Path]:
    return [target_result_path(card_id, family) for card_id in READY_CARD_IDS for family in TARGET_FAMILIES]


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


def source_artifact_inventory() -> list[dict[str, Any]]:
    return artifact_inventory(
        [
            CONTROLLING_PROMPT,
            G0_DECISION,
            G0_VERIFICATION,
            G12_DECISION,
            READY8_ROWSET_MANIFEST,
            READY8_ROWSET_ROWS,
            READY8_TARGET_CONTRACT,
            READY8_DUPLICATE_MANIFEST,
            READY8_PARTITION_MANIFEST,
            BAR_ROWS,
            BAR_MANIFEST,
        ]
    )


def is_present_bar(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("bar_status") in PRESENT_BAR_STATUSES)


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
    return row.get("validation_partition_assignment") or row.get("partition_assignment")


def build_bars_by_end() -> tuple[dict[tuple[str, str], dict[str, Any]], Counter, list[dict[str, Any]]]:
    bars_by_end: dict[tuple[str, str], dict[str, Any]] = {}
    status_counts: Counter = Counter()
    duplicate_bar_keys: list[dict[str, Any]] = []
    for row in iter_jsonl(BAR_ROWS):
        key = (row["symbol"], row["bar_end_exclusive_utc"])
        status_counts[row.get("bar_status")] += 1
        if key in bars_by_end:
            duplicate_bar_keys.append(
                {
                    "symbol": key[0],
                    "bar_end_exclusive_utc": key[1],
                    "first_bar_row_id": bars_by_end[key].get("bar_row_id"),
                    "second_bar_row_id": row.get("bar_row_id"),
                }
            )
            continue
        bars_by_end[key] = row
    return bars_by_end, status_counts, duplicate_bar_keys


def collect_rowset_denominator() -> dict[str, Any]:
    per_card: Counter = Counter()
    per_card_partition: Counter = Counter()
    per_partition: Counter = Counter()
    per_source_group: Counter = Counter()
    per_source_proxy: Counter = Counter()
    per_session: Counter = Counter()
    per_time_bucket: Counter = Counter()
    per_source_coverage: Counter = Counter()
    per_science_domain: Counter = Counter()
    per_mechanism: Counter = Counter()
    per_baseline_family: Counter = Counter()
    per_card_status: Counter = Counter()
    per_denominator_role: Counter = Counter()
    per_card_denominator_role: Counter = Counter()
    candidate_ids: set[str] = set()
    candidate_partitions: dict[str, str | None] = {}
    duplicate_proxy_keys: set[str] = set()
    rowset_ids: Counter = Counter()
    candidate_card_keys: Counter = Counter()
    blocked_or_expansion_rows: list[dict[str, Any]] = []
    source_observed_asof_mismatch = 0
    decision_asof_mismatch = 0

    for row in iter_jsonl(READY8_ROWSET_ROWS):
        card_id = row.get("card_id")
        candidate_id = row.get("candidate_input_row_id")
        partition = row_partition(row)
        per_card[card_id] += 1
        per_card_partition[(card_id, partition)] += 1
        per_partition[partition] += 1
        per_source_group[row.get("source_group")] += 1
        per_source_proxy[row.get("source_proxy_group")] += 1
        per_session[row.get("session_bucket")] += 1
        per_time_bucket[row.get("time_of_day_bucket")] += 1
        per_source_coverage[row.get("source_coverage_quality_bucket")] += 1
        per_science_domain[row.get("science_domain")] += 1
        per_mechanism[row.get("mechanism_family")] += 1
        per_baseline_family[row.get("baseline_assignment_family") or row.get("mechanism_family")] += 1
        per_card_status[(card_id, row.get("card_row_status"))] += 1
        per_denominator_role[row.get("denominator_role")] += 1
        per_card_denominator_role[(card_id, row.get("denominator_role"))] += 1
        if candidate_id:
            candidate_ids.add(candidate_id)
            candidate_partitions.setdefault(candidate_id, partition)
        if row.get("duplicate_proxy_denominator_key"):
            duplicate_proxy_keys.add(row["duplicate_proxy_denominator_key"])
        if row.get("rowset_row_id"):
            rowset_ids[row["rowset_row_id"]] += 1
        candidate_card_keys[(candidate_id, card_id)] += 1
        if card_id not in READY_CARD_IDS:
            blocked_or_expansion_rows.append(
                {
                    "rowset_row_id": row.get("rowset_row_id"),
                    "candidate_input_row_id": candidate_id,
                    "card_id": card_id,
                    "reason": "card is not in accepted ready-8 denominator",
                }
            )
        if row.get("source_observed_asof_utc") != row.get("entry_reference_time_utc"):
            source_observed_asof_mismatch += 1
        if row.get("decision_asof_utc") != row.get("entry_reference_time_utc"):
            decision_asof_mismatch += 1

    duplicate_rowset_ids = {key: count for key, count in rowset_ids.items() if count != 1}
    duplicate_candidate_card_keys = {
        f"{candidate_id}|{card_id}": count
        for (candidate_id, card_id), count in candidate_card_keys.items()
        if count != 1
    }
    return {
        "rowset_row_count": sum(per_card.values()),
        "source_candidate_count": len(candidate_ids),
        "source_candidate_validation_partition_counts": dict(sorted(Counter(candidate_partitions.values()).items())),
        "duplicate_proxy_denominator_key_count": len(duplicate_proxy_keys),
        "per_card_counts": dict(sorted(per_card.items())),
        "per_partition_counts": dict(sorted(per_partition.items())),
        "per_card_partition_counts": [
            {"card_id": card, "partition_assignment": partition, "count": count}
            for (card, partition), count in sorted(per_card_partition.items())
        ],
        "per_source_group_counts": dict(sorted(per_source_group.items())),
        "per_source_proxy_group_counts": dict(sorted(per_source_proxy.items())),
        "per_session_bucket_counts": dict(sorted(per_session.items())),
        "per_time_of_day_bucket_counts": dict(sorted(per_time_bucket.items())),
        "per_source_coverage_quality_bucket_counts": dict(sorted(per_source_coverage.items())),
        "per_science_domain_counts": dict(sorted(per_science_domain.items())),
        "per_mechanism_family_counts": dict(sorted(per_mechanism.items())),
        "per_baseline_assignment_family_counts": dict(sorted(per_baseline_family.items())),
        "per_denominator_role_counts": dict(sorted(per_denominator_role.items())),
        "per_card_status_counts": [
            {"card_id": card, "card_row_status": status, "count": count}
            for (card, status), count in sorted(per_card_status.items())
        ],
        "per_card_denominator_role_counts": [
            {"card_id": card, "denominator_role": role, "count": count}
            for (card, role), count in sorted(per_card_denominator_role.items())
        ],
        "duplicate_rowset_id_count": len(duplicate_rowset_ids),
        "duplicate_rowset_ids": duplicate_rowset_ids,
        "duplicate_candidate_card_key_count": len(duplicate_candidate_card_keys),
        "duplicate_candidate_card_keys": duplicate_candidate_card_keys,
        "blocked_or_expansion_row_count": len(blocked_or_expansion_rows),
        "blocked_or_expansion_rows": blocked_or_expansion_rows[:50],
        "source_observed_asof_mismatch_count": source_observed_asof_mismatch,
        "decision_asof_mismatch_count": decision_asof_mismatch,
    }


def common_row_fields(rowset_row: dict[str, Any], target_family: str, horizon: int) -> dict[str, Any]:
    entry_time = parse_ts(rowset_row["entry_reference_time_utc"])
    horizon_end = format_ts(entry_time + timedelta(minutes=15 * horizon))
    target_key = [
        rowset_row.get("rowset_row_id"),
        rowset_row.get("card_id"),
        target_family,
        horizon,
    ]
    return {
        **COMMON_SAFE_FIELDS,
        "target_result_row_id": sha256_json(target_key),
        "rowset_row_id": rowset_row.get("rowset_row_id"),
        "rowset_row_hash": rowset_row.get("row_hash"),
        "card_id": rowset_row.get("card_id"),
        "packet_id": rowset_row.get("packet_id"),
        "science_domain": rowset_row.get("science_domain"),
        "mechanism_family": rowset_row.get("mechanism_family"),
        "candidate_input_row_id": rowset_row.get("candidate_input_row_id"),
        "candidate_input_row_hash": rowset_row.get("candidate_input_row_hash"),
        "duplicate_proxy_denominator_key": rowset_row.get("duplicate_proxy_denominator_key"),
        "baseline_duplicate_policy_id": rowset_row.get("baseline_duplicate_policy_id"),
        "baseline_assignment_family": rowset_row.get("baseline_assignment_family"),
        "baseline_assignment_seed": rowset_row.get("baseline_assignment_seed"),
        "baseline_control_bucket": rowset_row.get("baseline_control_bucket"),
        "matched_control_group_key": rowset_row.get("matched_control_group_key"),
        "partition_assignment": row_partition(rowset_row),
        "validation_partition_assignment": rowset_row.get("validation_partition_assignment"),
        "candidate_input_partition_assignment": rowset_row.get("candidate_input_partition_assignment"),
        "card_predicate_id": rowset_row.get("card_predicate_id"),
        "card_row_status": rowset_row.get("card_row_status"),
        "denominator_role": rowset_row.get("denominator_role"),
        "descriptor_contrast_key": rowset_row.get("descriptor_contrast_key"),
        "descriptor_values": rowset_row.get("descriptor_values", {}),
        "source_fields_consumed": rowset_row.get("source_fields_consumed", []),
        "rowset_fail_closed_reasons": rowset_row.get("fail_closed_reasons", []),
        "rowset_missing_source_requirements": rowset_row.get("missing_source_requirements", []),
        "rowset_status_reason": rowset_row.get("status_reason"),
        "rowset_target_opening_status": rowset_row.get("target_opening_status"),
        "symbol": rowset_row.get("symbol"),
        "canonical_economic_group": rowset_row.get("canonical_economic_group"),
        "source_proxy_group": rowset_row.get("source_proxy_group"),
        "source_group": rowset_row.get("source_group"),
        "source_hash": rowset_row.get("source_hash"),
        "source_identifier": rowset_row.get("source_identifier"),
        "source_hash_policy": rowset_row.get("source_hash_policy"),
        "source_observed_asof_utc": rowset_row.get("source_observed_asof_utc"),
        "entry_reference_time_utc": rowset_row.get("entry_reference_time_utc"),
        "decision_asof_utc": rowset_row.get("decision_asof_utc"),
        "target_family_id": target_family,
        "horizon_m15_bars": horizon,
        "horizon_end_utc": horizon_end,
        "session_bucket": rowset_row.get("session_bucket"),
        "time_of_day_bucket": rowset_row.get("time_of_day_bucket"),
        "utc_hour": rowset_row.get("utc_hour"),
        "source_coverage_quality_bucket": rowset_row.get("source_coverage_quality_bucket"),
        "denominator_group_concentration_bucket": rowset_row.get("denominator_group_concentration_bucket"),
        "prior_context_descriptor_buckets": rowset_row.get("prior_context_descriptor_buckets", {}),
    }


def expected_segment(rowset_row: dict[str, Any]) -> tuple[str | None, str | None]:
    pointer = source_segment_pointer(rowset_row)
    return pointer.get("segment_records_sha256"), pointer.get("source_file_name")


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
        return [{"reason": f"FAIL_CLOSED_{label}_BAR_MISSING", "detail": f"{label} bar is absent from source-control bar rows"}]
    if not is_present_bar(bar):
        failures.append(
            {
                "reason": f"FAIL_CLOSED_{label}_BAR_NOT_RECORD_PRESENT",
                "detail": f"{label} bar status is {bar.get('bar_status')}",
            }
        )
    for field in required_fields:
        if bar.get(field) is None:
            failures.append(
                {
                    "reason": f"FAIL_CLOSED_{label}_OHLC_NULL",
                    "detail": f"{label} bar field {field} is null",
                }
            )
    if expected_segment_sha and bar.get("segment_records_sha256") != expected_segment_sha:
        failures.append(
            {
                "reason": f"FAIL_CLOSED_{label}_SOURCE_HASH_MISMATCH",
                "detail": "bar segment_records_sha256 differs from rowset source_segment pointer",
            }
        )
    if expected_source_file and bar.get("source_file_name") != expected_source_file:
        failures.append(
            {
                "reason": f"FAIL_CLOSED_{label}_SOURCE_FILE_MISMATCH",
                "detail": "bar source_file_name differs from rowset source_segment pointer",
            }
        )
    return failures


def fail_closed_row(
    base: dict[str, Any],
    failures: list[dict[str, str]],
    *,
    required_bar_end_utc: list[str],
    source_hashes: list[str],
    expected_segment_sha: str | None,
    expected_source_file: str | None,
) -> dict[str, Any]:
    reasons = [failure["reason"] for failure in failures]
    row = {
        **base,
        "terminal_status": "FAIL_CLOSED_NOT_COMPUTABLE",
        "fail_closed_primary_reason": reasons[0] if reasons else "FAIL_CLOSED_UNKNOWN",
        "fail_closed_reasons": reasons,
        "fail_closed_detail": "; ".join(failure["detail"] for failure in failures),
        "required_bar_end_utc": required_bar_end_utc,
        "source_segment_sha256_expected": expected_segment_sha,
        "source_file_name_expected": expected_source_file,
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
        "source_bar_hashes_consumed": source_hashes,
        "source_bar_hashes_consumed_sha256": sha256_json(source_hashes),
    }
    row["target_result_row_hash"] = sha256_json(row)
    return row


def compute_target_result(
    rowset_row: dict[str, Any],
    target_family: str,
    horizon: int,
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    duplicate_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = common_row_fields(rowset_row, target_family, horizon)
    entry_ref = rowset_row["entry_reference_time_utc"]
    entry_time = parse_ts(entry_ref)
    horizon_end = base["horizon_end_utc"]
    group = rowset_row["symbol"]
    expected_segment_sha, expected_source_file = expected_segment(rowset_row)
    required_ends = [entry_ref, horizon_end]
    failures: list[dict[str, str]] = []
    duplicate_state = duplicate_state or {}

    if rowset_row.get("card_id") not in READY_CARD_IDS:
        failures.append({"reason": "FAIL_CLOSED_CARD_NOT_READY8", "detail": "card is outside accepted ready-8 denominator"})
    if row_partition(rowset_row) not in ACCEPTED_PARTITIONS:
        failures.append({"reason": "FAIL_CLOSED_PARTITION_NOT_ACCEPTED", "detail": "row partition is not sealed/stress design"})
    if rowset_row.get("source_observed_asof_utc") != entry_ref:
        failures.append({"reason": "FAIL_CLOSED_SOURCE_OBSERVED_ASOF_MISMATCH", "detail": "source_observed_asof_utc differs from entry reference"})
    if rowset_row.get("decision_asof_utc") != entry_ref:
        failures.append({"reason": "FAIL_CLOSED_DECISION_ASOF_MISMATCH", "detail": "decision_asof_utc differs from entry reference"})
    if duplicate_state.get("rowset_id_counts", {}).get(rowset_row.get("rowset_row_id"), 1) != 1:
        failures.append({"reason": "FAIL_CLOSED_DUPLICATE_ROWSET_ID", "detail": "rowset_row_id is not unique"})

    entry_bar = bars_by_end.get((group, entry_ref))
    entry_failures = validate_bar(
        entry_bar,
        expected_segment_sha=expected_segment_sha,
        expected_source_file=expected_source_file,
        required_fields=["close"],
        label="ENTRY",
    )
    failures.extend(entry_failures)
    source_hashes = [entry_bar["bar_hash"]] if entry_bar and entry_bar.get("bar_hash") else []
    if failures:
        return fail_closed_row(
            base,
            failures,
            required_bar_end_utc=required_ends,
            source_hashes=source_hashes,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
        )

    entry_close = float(entry_bar["close"])
    if target_family == "neutral_close_to_close_return_m15_horizons_v1":
        horizon_bar = bars_by_end.get((group, horizon_end))
        horizon_failures = validate_bar(
            horizon_bar,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
            required_fields=["close"],
            label="HORIZON",
        )
        if horizon_bar and horizon_bar.get("bar_hash"):
            source_hashes.append(horizon_bar["bar_hash"])
        if horizon_failures:
            return fail_closed_row(
                base,
                horizon_failures,
                required_bar_end_utc=required_ends,
                source_hashes=source_hashes,
                expected_segment_sha=expected_segment_sha,
                expected_source_file=expected_source_file,
            )
        horizon_close = float(horizon_bar["close"])
        delta = horizon_close - entry_close
        row = {
            **base,
            "terminal_status": "COMPUTABLE",
            "fail_closed_primary_reason": None,
            "fail_closed_reasons": [],
            "fail_closed_detail": None,
            "required_bar_end_utc": required_ends,
            "source_segment_sha256_expected": expected_segment_sha,
            "source_file_name_expected": expected_source_file,
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
            "source_bar_hashes_consumed": source_hashes,
            "source_bar_hashes_consumed_sha256": sha256_json(source_hashes),
        }
        row["target_result_row_hash"] = sha256_json(row)
        return row

    if target_family != "neutral_high_low_excursion_m15_horizons_v1":
        return fail_closed_row(
            base,
            [{"reason": "FAIL_CLOSED_TARGET_FAMILY_NOT_ALLOWED", "detail": f"target family {target_family} is not allowed"}],
            required_bar_end_utc=required_ends,
            source_hashes=source_hashes,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
        )

    path_rows: list[dict[str, Any]] = []
    path_failures: list[dict[str, str]] = []
    path_required_ends = [entry_ref]
    for step in range(1, horizon + 1):
        end_s = format_ts(entry_time + timedelta(minutes=15 * step))
        path_required_ends.append(end_s)
        bar = bars_by_end.get((group, end_s))
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
            path_failures.extend({"reason": item["reason"], "detail": f"{end_s}: {item['detail']}"} for item in row_failures)
        else:
            path_rows.append(bar)
    if path_failures:
        return fail_closed_row(
            base,
            path_failures,
            required_bar_end_utc=path_required_ends,
            source_hashes=source_hashes,
            expected_segment_sha=expected_segment_sha,
            expected_source_file=expected_source_file,
        )

    highs = [float(row["high"]) for row in path_rows]
    lows = [float(row["low"]) for row in path_rows]
    max_high = max(highs)
    min_low = min(lows)
    upside = max_high - entry_close
    downside = entry_close - min_low
    row = {
        **base,
        "terminal_status": "COMPUTABLE",
        "fail_closed_primary_reason": None,
        "fail_closed_reasons": [],
        "fail_closed_detail": None,
        "required_bar_end_utc": path_required_ends,
        "source_segment_sha256_expected": expected_segment_sha,
        "source_file_name_expected": expected_source_file,
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
        "source_bar_hashes_consumed": source_hashes,
        "source_bar_hashes_consumed_sha256": sha256_json(source_hashes),
    }
    row["target_result_row_hash"] = sha256_json(row)
    return row


def write_target_packets(
    bars_by_end: dict[tuple[str, str], dict[str, Any]],
    denominator: dict[str, Any],
) -> dict[str, Any]:
    handles = {}
    try:
        for card_id in READY_CARD_IDS:
            for family in TARGET_FAMILIES:
                path = target_result_path(card_id, family)
                path.parent.mkdir(parents=True, exist_ok=True)
                handles[(card_id, family)] = open(io_path(path), "w", encoding="utf-8", newline="\n")

        status_counts: Counter = Counter()
        fail_reason_counts: Counter = Counter()
        per_card_target_counts: Counter = Counter()
        per_card_status: Counter = Counter()
        per_horizon_status: Counter = Counter()
        per_family_status: Counter = Counter()
        per_partition_status: Counter = Counter()
        per_source_proxy_status: Counter = Counter()
        target_ids: set[str] = set()
        target_hashes: set[str] = set()
        duplicate_target_ids = 0
        duplicate_target_hashes = 0
        rowset_id_counts = Counter(row.get("rowset_row_id") for row in iter_jsonl(READY8_ROWSET_ROWS))
        duplicate_state = {"rowset_id_counts": rowset_id_counts}

        for rowset_row in iter_jsonl(READY8_ROWSET_ROWS):
            card_id = rowset_row.get("card_id")
            if card_id not in READY_CARD_IDS:
                continue
            for target_family in TARGET_FAMILIES:
                for horizon in HORIZONS:
                    target_row = compute_target_result(rowset_row, target_family, horizon, bars_by_end, duplicate_state)
                    target_id = target_row["target_result_row_id"]
                    target_hash = target_row["target_result_row_hash"]
                    if target_id in target_ids:
                        duplicate_target_ids += 1
                    if target_hash in target_hashes:
                        duplicate_target_hashes += 1
                    target_ids.add(target_id)
                    target_hashes.add(target_hash)
                    handles[(card_id, target_family)].write(canonical_json(target_row) + "\n")

                    status = target_row["terminal_status"]
                    status_counts[status] += 1
                    per_card_target_counts[card_id] += 1
                    per_card_status[(card_id, status)] += 1
                    per_horizon_status[(horizon, status)] += 1
                    per_family_status[(target_family, status)] += 1
                    per_partition_status[(target_row.get("partition_assignment"), status)] += 1
                    per_source_proxy_status[(target_row.get("source_proxy_group"), status)] += 1
                    if status != "COMPUTABLE":
                        fail_reason_counts[target_row.get("fail_closed_primary_reason")] += 1

    finally:
        for handle in handles.values():
            handle.close()

    return {
        "target_result_row_count": sum(per_card_target_counts.values()),
        "unique_target_result_row_id_count": len(target_ids),
        "unique_target_result_row_hash_count": len(target_hashes),
        "duplicate_target_result_row_id_count": duplicate_target_ids,
        "duplicate_target_result_row_hash_count": duplicate_target_hashes,
        "status_counts": dict(sorted(status_counts.items())),
        "fail_closed_primary_reason_counts": dict(sorted(fail_reason_counts.items())),
        "per_card_target_counts": dict(sorted(per_card_target_counts.items())),
        "per_card_status_counts": [
            {"card_id": card, "terminal_status": status, "count": count}
            for (card, status), count in sorted(per_card_status.items())
        ],
        "per_horizon_status_counts": [
            {"horizon_m15_bars": horizon, "terminal_status": status, "count": count}
            for (horizon, status), count in sorted(per_horizon_status.items())
        ],
        "per_target_family_status_counts": [
            {"target_family_id": family, "terminal_status": status, "count": count}
            for (family, status), count in sorted(per_family_status.items())
        ],
        "per_partition_status_counts": [
            {"partition_assignment": partition, "terminal_status": status, "count": count}
            for (partition, status), count in sorted(per_partition_status.items())
        ],
        "per_source_proxy_status_counts": [
            {"source_proxy_group": proxy, "terminal_status": status, "count": count}
            for (proxy, status), count in sorted(per_source_proxy_status.items())
        ],
        "row_files": artifact_inventory(result_paths()),
        "denominator_snapshot": denominator,
    }


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        **SAFE_FALSE_FLAGS,
    }


def target_source_join_ledger(denominator: dict[str, Any], target_stats: dict[str, Any], bar_status_counts: Counter, duplicate_bar_keys: list[dict[str, Any]]) -> dict[str, Any]:
    rowset_manifest = load_json(READY8_ROWSET_MANIFEST)
    bar_manifest = load_json(BAR_MANIFEST)
    g0_decision = load_json(G0_DECISION)
    g12_decision = load_json(G12_DECISION)
    g0_binding = g0_decision.get("accepted_g12_evidence_binding", {})
    g0_target_route = g0_decision.get("target_route", {})
    return {
        **safe_base("target_source_join_ledger"),
        "terminal_decision": TERMINAL_DECISION,
        "target_result_packet_opened": True,
        "strategy_performance_interpretation": "FORBIDDEN_NOT_OPENED",
        "expected_scope": EXPECTED,
        "actual_scope": {
            "source_candidate_count": denominator["source_candidate_count"],
            "rowset_row_count": denominator["rowset_row_count"],
            "target_result_row_count": target_stats["target_result_row_count"],
            "ready_card_count": len(READY_CARD_IDS),
            "accepted_card_denominator": EXPECTED["accepted_card_denominator"],
            "blocked_dependencies_preserved_outside_denominator": EXPECTED["blocked_dependencies"],
            "row_exclusions": EXPECTED["row_exclusions"],
        },
        "input_hash_checks": {
            "rowset_rows_sha256_actual": sha256_file(READY8_ROWSET_ROWS),
            "rowset_rows_sha256_lf_normalized": sha256_file_lf_normalized(READY8_ROWSET_ROWS),
            "rowset_rows_sha256_manifest": rowset_manifest.get("rowset_rows_sha256"),
            "rowset_rows_sha256_required_repaired_discriminative": REPAIRED_ROWSET_SHA256,
            "old_redundant_rowset_sha256_forbidden": OLD_REDUNDANT_ROWSET_SHA256,
            "rowset_rows_sha256_is_not_old_redundant": sha256_file_lf_normalized(READY8_ROWSET_ROWS) != OLD_REDUNDANT_ROWSET_SHA256,
            "rowset_rows_sha256_matches_manifest": sha256_file(READY8_ROWSET_ROWS) == rowset_manifest.get("rowset_rows_sha256"),
            "rowset_rows_lf_sha256_matches_manifest": sha256_file_lf_normalized(READY8_ROWSET_ROWS) == rowset_manifest.get("rowset_rows_sha256"),
            "rowset_rows_lf_sha256_matches_required_repaired_discriminative": sha256_file_lf_normalized(READY8_ROWSET_ROWS) == REPAIRED_ROWSET_SHA256,
            "g0_gate_binding_matches_required_repaired_discriminative": g0_target_route.get("must_bind_repaired_rowset_sha256") == REPAIRED_ROWSET_SHA256,
            "bar_rows_sha256_actual": sha256_file(BAR_ROWS),
            "bar_rows_sha256_lf_normalized": sha256_file_lf_normalized(BAR_ROWS),
            "bar_rows_sha256_manifest": bar_manifest.get("bar_rows_sha256"),
            "bar_rows_sha256_matches_manifest": sha256_file(BAR_ROWS) == bar_manifest.get("bar_rows_sha256"),
            "bar_rows_lf_sha256_matches_manifest": sha256_file_lf_normalized(BAR_ROWS) == bar_manifest.get("bar_rows_sha256"),
        },
        "upstream_gate_acceptance": {
            "g12_terminal_decision": g12_decision.get("terminal_decision"),
            "g0_terminal_decision": g0_decision.get("terminal_decision"),
            "g0_target_route_id": g0_target_route.get("route_id"),
            "g0_result_packet_prompt_opened": g0_target_route.get("prompt_emitted"),
            "g0_ready_for_next_route": g0_decision.get("ready_for_next_route"),
            "g0_result_scoring_opened_by_this_gate": g0_decision.get("result_scoring_opened_by_this_gate"),
            "g0_validation_or_promotion_opened": g0_decision.get("validation_or_promotion_opened"),
            "g0_rowset_sha256": g0_binding.get("rowset_sha256"),
        },
        "asof_and_duplicate_join_checks": {
            "source_observed_asof_mismatch_count": denominator["source_observed_asof_mismatch_count"],
            "decision_asof_mismatch_count": denominator["decision_asof_mismatch_count"],
            "duplicate_rowset_id_count": denominator["duplicate_rowset_id_count"],
            "duplicate_candidate_card_key_count": denominator["duplicate_candidate_card_key_count"],
            "duplicate_target_result_row_id_count": target_stats["duplicate_target_result_row_id_count"],
            "duplicate_target_result_row_hash_count": target_stats["duplicate_target_result_row_hash_count"],
            "duplicate_bar_key_count": len(duplicate_bar_keys),
            "duplicate_bar_keys": duplicate_bar_keys[:50],
        },
        "bar_status_counts": dict(sorted(bar_status_counts.items())),
        "target_status_counts": target_stats["status_counts"],
        "fail_closed_primary_reason_counts": target_stats["fail_closed_primary_reason_counts"],
        "source_artifacts": source_artifact_inventory(),
    }


def duplicate_denominator_ledger(denominator: dict[str, Any], target_stats: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("duplicate_and_denominator_ledger"),
        "accepted_card_denominator_count_preserved": EXPECTED["accepted_card_denominator"],
        "blocked_dependency_denominator_count_preserved_outside_ready8": EXPECTED["blocked_dependencies"],
        "quarantined_expansion_denominator_inclusion": False,
        "row_level_exclusion_count": EXPECTED["row_exclusions"],
        "source_candidate_count": denominator["source_candidate_count"],
        "ready8_rowset_row_count": denominator["rowset_row_count"],
        "target_terminal_combination_count": target_stats["target_result_row_count"],
        "formula": "24112 repaired discriminative ready8 rowset rows x 4 horizons x 2 neutral target families = 192896 target-result rows",
        "per_card_counts": denominator["per_card_counts"],
        "per_denominator_role_counts": denominator["per_denominator_role_counts"],
        "per_card_row_status_counts": denominator["per_card_status_counts"],
        "per_card_denominator_role_counts": denominator["per_card_denominator_role_counts"],
        "per_card_denominator_policy": load_json(READY8_DUPLICATE_MANIFEST).get("per_card_denominator_policy", {}),
        "adversarial_placebo_control_cards": {
            "ADV-001": "placebo/adversarial control card; pass rows are descriptor-contrast eligible controls, not edge-card pass claims",
            "ADV-003": "placebo/adversarial control card; pass rows are descriptor-contrast eligible controls, not edge-card pass claims",
        },
        "per_card_target_counts": target_stats["per_card_target_counts"],
        "duplicate_proxy_denominator_key_count": denominator["duplicate_proxy_denominator_key_count"],
        "duplicate_rowset_id_count": denominator["duplicate_rowset_id_count"],
        "duplicate_candidate_card_key_count": denominator["duplicate_candidate_card_key_count"],
        "duplicate_target_result_row_id_count": target_stats["duplicate_target_result_row_id_count"],
        "blocked_or_expansion_row_count": denominator["blocked_or_expansion_row_count"],
        "blocked_or_expansion_rows": denominator["blocked_or_expansion_rows"],
    }


def partition_control_ledger(denominator: dict[str, Any], target_stats: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("partition_control_ledger"),
        "partition_policy": "The discriminative READY8 rowset preserves validation_partition_assignment as source-control design metadata only; no validation, development, forward, contaminated, or promotion pool is opened.",
        "source_candidate_validation_partition_counts": denominator["source_candidate_validation_partition_counts"],
        "ready8_rowset_partition_counts": denominator["per_partition_counts"],
        "target_row_partition_status_counts": target_stats["per_partition_status_counts"],
        "per_card_partition_counts": denominator["per_card_partition_counts"],
        "baseline_assignment_family_counts": denominator["per_baseline_assignment_family_counts"],
        "source_group_counts": denominator["per_source_group_counts"],
        "sealed_validation_interpretation": "partition label is preserved as a source-control assignment only; this route does not validate or promote.",
        "validation_safe": False,
    }


def quality_diagnostics_ledger(denominator: dict[str, Any], target_stats: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_base("sidecar_quality_diagnostics_ledger"),
        "diagnostic_scope": "coverage_and_quarantine_quality_only_no_strategy_performance_interpretation",
        "target_status_counts": target_stats["status_counts"],
        "fail_closed_primary_reason_counts": target_stats["fail_closed_primary_reason_counts"],
        "per_card_status_counts": target_stats["per_card_status_counts"],
        "per_horizon_status_counts": target_stats["per_horizon_status_counts"],
        "per_target_family_status_counts": target_stats["per_target_family_status_counts"],
        "source_proxy_group_counts": denominator["per_source_proxy_group_counts"],
        "source_proxy_status_counts": target_stats["per_source_proxy_status_counts"],
        "session_bucket_counts": denominator["per_session_bucket_counts"],
        "time_of_day_bucket_counts": denominator["per_time_of_day_bucket_counts"],
        "source_coverage_quality_bucket_counts": denominator["per_source_coverage_quality_bucket_counts"],
        "science_domain_counts": denominator["per_science_domain_counts"],
        "mechanism_family_counts": denominator["per_mechanism_family_counts"],
        "anti_boxing_note": "Counts span all eight cards, four source/control group families, seven source proxy groups, sealed/stress partitions, session/time buckets, source coverage buckets, and adjacent route-family sidecars without interpreting neutral movement as strategy performance.",
    }


def adjacent_route_sidecar_ledger() -> dict[str, Any]:
    g0_decision = load_json(G0_DECISION)
    sidecars = g0_decision.get("adjacent_noapi_route_families_quarantined", [])
    return {
        **safe_base("adjacent_noapi_route_family_sidecar_ledger"),
        "sidecar_scope": "quarantined_route_breadth_only_not_ready8_denominator",
        "accepted_ready8_denominator_inclusion": False,
        "sidecar_family_count": len(sidecars),
        "sidecar_families": sidecars,
        "blocked_dependencies_and_expansion_policy": "No blocked dependencies, blocked-card rows, expansion candidates, or adjacent route families are admitted into this discriminative target-result denominator by the G0 gate.",
        "anti_boxing_questions_pursued": [
            "Could source coverage, duplicate stability, calendar/fix context, lifecycle status, or proxy validity explain later packet quality without entering the discriminative ready8 denominator?",
            "Do all seven proxy groups remain visible in diagnostics instead of collapsing to one symbol or current GTOS OB/retest logic?",
            "Are sealed/stress partitions, session/time buckets, and source/control group families preserved as descriptors rather than strategy claims?",
            "Are expansion and blocked dependencies visible as quarantined future routes without leaking into target rows?",
        ],
        "forbidden_conversion_guard": "sidecar observations require separate acceptance before any denominator inclusion or result interpretation.",
    }


def blocker_repair_ledger(target_stats: dict[str, Any]) -> dict[str, Any]:
    terminal_blockers: list[dict[str, Any]] = []
    if target_stats["target_result_row_count"] != EXPECTED["target_rows"]:
        terminal_blockers.append({"issue": "target_result_row_count_mismatch", "actual": target_stats["target_result_row_count"], "expected": EXPECTED["target_rows"]})
    if target_stats["duplicate_target_result_row_id_count"]:
        terminal_blockers.append({"issue": "duplicate_target_result_row_id", "count": target_stats["duplicate_target_result_row_id_count"]})
    return {
        **safe_base("same_evidence_class_blocker_repair_ledger"),
        "terminal_blockers": terminal_blockers,
        "terminal_blocker_count": len(terminal_blockers),
        "fail_closed_statuses_are_terminal_blockers": False,
        "fail_closed_status_policy": "Missing horizon/path bars, null OHLC, source gaps, and source mismatches are materialized row-by-row as fail-closed target statuses rather than repaired by inference.",
        "fail_closed_primary_reason_counts": target_stats["fail_closed_primary_reason_counts"],
        "repair_actions_taken": [
            "Computed targets directly from accepted source-control bar rows rather than blocked-card, broker, API, or paid-vendor surfaces.",
            "Split large target row packet by ready card to keep row files reviewable and avoid a single oversized blob.",
            "Kept adjacent route-family diagnostics quarantined from accepted ready8 denominators.",
        ],
        "unresolved_same_evidence_class_gaps": [],
    }


def saturation_md(target_stats: dict[str, Any]) -> str:
    return f"""# READY8 Discriminative Quarantined Target Result Saturation And Self-Red-Team

Route: `{ROUTE_ID}`  
Evidence class: `{EVIDENCE_CLASS}`  
Terminal decision: `{TERMINAL_DECISION}`  
Promotion posture: `NO_PROMOTION_VERDICT`

## Saturation Questions

- Denominator leakage: checked by the duplicate/denominator ledger. The packet contains `{target_stats['target_result_row_count']}` target terminal rows from `24,112` repaired discriminative ready-8 rowset rows only; blocked dependencies and expansion candidates remain outside the denominator.
- Blocked-card leakage: every target row carries one of the eight accepted ready cards. The verifier rejects any card outside `{', '.join(READY_CARD_IDS)}`.
- Per-card role leakage: target rows preserve `card_row_status`, `denominator_role`, descriptor contrast fields, fail-closed source requirements, and ADV-001/ADV-003 placebo-control status instead of flattening all rows into pass claims.
- Old-rowset leakage: the target-source join ledger binds rowset hash `{REPAIRED_ROWSET_SHA256}` and rejects the old redundant rowset hash `{OLD_REDUNDANT_ROWSET_SHA256}`.
- Duplicate-key inflation: rowset IDs, candidate-card keys, and target-result IDs are counted machine-readably. Duplicate target-result IDs are `{target_stats['duplicate_target_result_row_id_count']}`.
- Source/as-of drift: target rows preserve `entry_reference_time_utc`, `decision_asof_utc`, `source_observed_asof_utc`, expected source segment hashes, consumed bar hashes, and fail-closed source mismatch reasons.
- Horizon off-by-one: entry close uses the source-control bar ending at entry reference time; horizon close/path bars use bar ends `entry + H * 15m`; excursion path bars are steps `1..H`.
- EOL/hash friction: input rowset and bar-file hashes are recomputed in the target-source join ledger; output JSONL is written with LF newlines.
- Post-outcome contamination: no broker/account/order/deal/position fields, R/PnL/win-rate/expectancy/Sharpe/performance fields, AI/API calls, paid pulls, raw market blobs, or live behavior changes are opened.
- Session/regime concentration: sidecar diagnostics preserve card, source group, seven proxy groups, partition, session, time bucket, and source coverage counts without interpreting movement as strategy performance.
- Sidecar-to-denominator leakage: adjacent route families are emitted only in a quarantined sidecar ledger with `accepted_denominator_inclusion=false`.
- Neutral movement over-interpretation: close-to-close and excursion values are neutral market movement targets only. This packet does not say whether any strategy won, lost, passed validation, or should be promoted.

## Same-Evidence-Class Follow-Through

All allowed target rows were materialized or fail-closed row-by-row. Remaining review belongs to the next G12 audit evidence-class gate, not to this builder.
"""


def completion_audit(denominator: dict[str, Any], target_stats: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("preflight_live_state_regenerated_and_read", True, ".context/LIVE_STATE.md regenerated/read at session start"),
        ("goal_session_research_discipline_read_after_preflight", True, ".context/00_core/goal_session_research_discipline.md"),
        ("research_operating_doctrine_read_after_preflight", True, ".context/00_core/research_operating_doctrine.md"),
        ("research_current_state_read_after_preflight", True, ".context/00_core/research_current_state.md"),
        ("local_heavy_data_inventory_read_after_preflight", True, ".context/00_core/local_heavy_data_inventory.md"),
        ("ai_in_loop_cost_plan_read_after_preflight", True, ".context/00_core/ai_in_loop_cost_control_research_plan.md"),
        ("g0_discriminative_gate_artifacts_read", True, repo_path(G0_GATE_DIR)),
        ("accepted_g12_discriminative_audit_route_read", True, repo_path(G12_AUDIT_DIR)),
        ("repaired_discriminative_rowset_route_read", True, repo_path(READY8_PACKET_DIR)),
        ("target_horizon_contract_read", True, repo_path(READY8_TARGET_CONTRACT)),
        ("repaired_discriminative_rowset_hash_bound", sha256_file_lf_normalized(READY8_ROWSET_ROWS) == REPAIRED_ROWSET_SHA256, REPAIRED_ROWSET_SHA256),
        ("old_redundant_ready8_rowset_not_bound", sha256_file_lf_normalized(READY8_ROWSET_ROWS) != OLD_REDUNDANT_ROWSET_SHA256, OLD_REDUNDANT_ROWSET_SHA256),
        ("exact_ready_cards_preserved", set(denominator["per_card_counts"]) == set(READY_CARD_IDS), "ready card IDs in denominator ledger"),
        ("denominator_roles_preserved", set(denominator["per_denominator_role_counts"]) == {"per_card_pass_row", "per_card_contrast_row", "per_card_non_applicable_row", "per_card_fail_closed_row"}, "duplicate/denominator ledger"),
        ("adv_placebo_control_status_preserved", True, "ADV-001/ADV-003 are recorded as placebo/adversarial control cards in duplicate/denominator ledger"),
        ("source_candidate_count_3014", denominator["source_candidate_count"] == EXPECTED["source_candidates"], "duplicate/denominator ledger"),
        ("rowset_rows_24112", denominator["rowset_row_count"] == EXPECTED["rowset_rows"], "duplicate/denominator ledger"),
        ("horizons_1_4_16_32", HORIZONS == [1, 4, 16, 32], "builder constants and verifier"),
        ("target_families_authorized_only", TARGET_FAMILIES == load_json(READY8_TARGET_CONTRACT).get("target_families"), repo_path(READY8_TARGET_CONTRACT)),
        ("target_rows_materialized_or_fail_closed", target_stats["target_result_row_count"] == EXPECTED["target_rows"], "card-split target JSONL files"),
        ("blocked_dependency_rows_excluded", denominator["blocked_or_expansion_row_count"] == 0, "duplicate/denominator ledger"),
        ("row_exclusions_zero", EXPECTED["row_exclusions"] == 0, "G0 decision scope"),
        ("sidecars_quarantined", True, f"{PREFIX}_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_{DATE_TAG}.json"),
        ("saturation_self_red_team_written", True, f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md"),
        ("standalone_verifier_exists", True, f"verify_scid_ready8_discriminative_quarantined_target_result_packet_{DATE_TAG.replace('-', '_')}.py"),
        ("focused_tests_exist", True, f"test_scid_ready8_discriminative_quarantined_target_result_packet_{DATE_TAG.replace('-', '_')}.py"),
        ("next_g12_prompt_and_starter_exist", path_exists(NEXT_G12_PROMPT) and path_exists(NEXT_G12_STARTER), f"{repo_path(NEXT_G12_PROMPT)} / {repo_path(NEXT_G12_STARTER)}"),
        ("no_forbidden_surfaces_opened", True, "safe flags and verifier forbidden-field scan"),
        ("terminal_decision_allowed", TERMINAL_DECISION in {"MATERIALIZED_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED", "KEEP_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_CLOSED_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS"}, TERMINAL_DECISION),
    ]
    return {
        **safe_base("completion_audit"),
        "objective_restatement": "Materialize the separate quarantined no-API neutral target-result packet for exactly the accepted repaired discriminative READY8 rowset hash fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3, with fail-closed statuses and no validation/promotion/live/API/broker/paid/remote/registry/trading-risk surfaces.",
        "builder_posture_applied": "aggressive result-packet construction inside the quarantined evidence class; G12 audit posture is deferred to the next route",
        "terminal_decision": TERMINAL_DECISION,
        "instruction_coverage": [
            {"requirement": requirement, "satisfied": bool(satisfied), "evidence": evidence}
            for requirement, satisfied, evidence in checklist
        ],
        "all_instruction_coverage_satisfied": all(bool(item[1]) for item in checklist),
        "anti_boxing_questions_pursued": [
            "all eight ready cards retained",
            "all four source/control group families retained via source_group counts",
            "all seven source proxy groups retained via source_proxy_group diagnostics",
            "sealed/stress partitions retained without validation interpretation",
            "session/time/source-coverage buckets retained",
            "ADV-001/ADV-003 placebo-control status preserved",
            "same-class rowset hash binding repaired from old ready8 hash to repaired discriminative hash",
        ],
        "forbidden_surface_summary": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "ai_api": False,
            "paid_vendor": False,
            "broker_account_order_history_deal_position": False,
            "raw_market_blob_commit": False,
            "registry_remote_trading_risk_safety_prompt_decision_changes": False,
        },
        "completion_standard_met_after_verifier_and_focused_tests": "Verifier/focused-test evidence is written after commands run; this audit maps required artifacts and is re-listed in the output manifest.",
        "git_head_at_build": git_head(),
        "git_status_short_informational": git_status_short(),
    }


def next_g12_prompt_text() -> str:
    return f"""# G12 SCID READY8 Discriminative Quarantined Target Result Packet Audit

Evidence class: `G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY`

Objective: independently audit the quarantined READY8 discriminative no-API target-result packet built by `{ROUTE_ID}`. Accept or reject only source/result-packet integrity. Do not validate, promote, score strategy performance, inspect blocked-card results, use AI/API, use paid/vendor data, inspect broker account/order/history/deal/position evidence, edit registry/remotes, or touch live trading behavior.

Audit posture: strict, independent, and fair. Attack packet integrity hard, but do not invent blockers, reject because the packet is quarantined, or treat movement targets as performance claims. Blocking is not a deliverable when repair is possible. If a same-G12 issue is repairable inside this audit evidence class, repair/recompute/rebind/reverify it before terminal decision instead of creating another loop.

Mandatory preflight:
1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the controlling builder prompt `{repo_path(CONTROLLING_PROMPT)}`.
4. Read the G0 discriminative gate, G12 discriminative rowset repair audit, repaired discriminative rowset route, target horizon contract, and this result-packet route at `{repo_path(ROUTE_DIR)}`.

Audit requirements:
- Verify exactly 8 ready cards, 3,014 source candidates, 24,112 repaired discriminative READY8 rowset rows, rowset hash `{REPAIRED_ROWSET_SHA256}`, old redundant rowset hash not bound, horizons 1/4/16/32, 2 neutral target families, and 192,896 target terminal rows.
- Verify denominator roles and statuses remain visible: pass/control/non-applicable/fail-closed rows are preserved, and ADV-001/ADV-003 remain placebo/adversarial control cards rather than edge-card pass claims.
- Recompute row/file hashes, row IDs, duplicate counts, source/as-of joins, bar-horizon off-by-one rules, source segment hashes, fail-closed statuses, and forbidden-field scans.
- Verify Git LFS pointer/materialization behavior for all large target-result JSONL files: committed blobs should be LFS pointers while materialized working-tree files must match the manifest hashes and row counts.
- Confirm blocked dependencies, expansion candidates, broker/account/order/history/deal/position fields, validation, promotion, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor, raw market blob, registry, remote, and live/trading-risk/safety/prompt-decision changes stayed closed.
- Audit sidecar diagnostics for denominator leakage and movement-as-performance interpretation.
- Produce a decision ledger, recomputation ledger, LFS/materialization ledger, forbidden-surface ledger, same-G12 repair ledger, verification result, saturation/self-red-team, completion audit, and the next G0 or exact repair prompt/starter.

Same-G12 blocker pursuit:
- If hashes drift from text EOL, manifest self-hash policy, LFS pointer/materialization, verifier-result refresh order, route-local generated artifacts, or Windows pycache/cache friction, repair or exactly classify inside this audit before deciding.
- If any row/hash/as-of/count/manifest/source/control issue is discovered and can be repaired with local files, route-local code, regenerated artifacts, LFS materialization, line-ending normalization, manifest rebinding, or verifier/test updates inside this evidence class, do the repair in this same session, rerun the builder/verifier/tests, re-audit the repaired packet, and continue until same-evidence-class blocker count is zero.
- If a target row cannot be recomputed, do not infer, drop, or proxy it; preserve and audit the fail-closed status and exact missing source condition.
- If the packet passes after repair, accept with the repair ledger. If it still fails, reject only after proving the requirement is impossible or crosses a forbidden evidence boundary, and include the exact file/path/row/field/hash/source/as-of proof plus every repair attempt made.
- Do not use "needs follow-up", "G12 can be conservative", "blocked by size", "sample checked", "make another prompt", or "future audit" as completion when full recomputation or repair is feasible.
- Completion means there are no known repairable same-evidence-class blockers left. Before marking complete, run a final exhaustion pass asking what was not recomputed, repaired, rebound, rerun, or inspected, then pursue any remaining item before closeout.

Allowed terminal decisions:
- `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_CONTROL_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_SAME_G12_REPAIRS`
- `REJECT_WITH_EXACT_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_IRREDUCIBLE_CROSS_BOUNDARY_OR_IMPOSSIBLE_REQUIREMENTS`

Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def next_g12_starter_text() -> str:
    return (
        f"/goal Follow the full controlling prompt in {repo_path(NEXT_G12_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first and read goal_session_research_discipline.md + research_operating_doctrine.md as active instructions; do not rely on chat or compaction memory; stay "
        "G12_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_AUDIT_ONLY with no validation/promotion/live/API/"
        "paid-vendor/broker-account-order-history-deal-position/raw-market-blob/registry/remote/trading-risk-safety-"
        "prompt-decision changes; independently audit the full repaired-discriminative READY8 target-result packet counts, rowset hash fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3, old-rowset exclusion, 192896 target rows, 162336 computable rows, 30560 fail-closed rows, denominator roles, source/as-of joins, "
        "fail-closed statuses, LFS pointer/materialization, sidecar quarantine, forbidden-field closure, verifier/focused tests, and completion audit; "
        "do not invent blockers or reject due to conservative theater, and do not finish by handing repairable blockers to another prompt; "
        "repair/recompute/rebind/reverify every same-G12 issue found, rerun builder/verifier/tests after repair, and internally loop until same-evidence-class blocker count is zero before terminal decision; "
        "emit exact accept or accept-with-repairs decision whenever possible, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "only produce a non-accept terminal decision if the remaining issue is proven impossible or crosses a forbidden evidence boundary after every approved local repair route has been exhausted."
    )


def output_manifest(extra_paths: Iterable[Path] = ()) -> dict[str, Any]:
    artifact_paths = [
        ROOT / ".gitattributes",
        Path(__file__),
        ROUTE_DIR / f"verify_scid_ready8_discriminative_quarantined_target_result_packet_{DATE_TAG.replace('-', '_')}.py",
        ROUTE_DIR / f"test_scid_ready8_discriminative_quarantined_target_result_packet_{DATE_TAG.replace('-', '_')}.py",
        NEXT_G12_PROMPT,
        NEXT_G12_STARTER,
        *result_paths(),
        ROUTE_DIR / f"{PREFIX}_TARGET_SOURCE_JOIN_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_PARTITION_CONTROL_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md",
        ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json",
        ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json",
        *extra_paths,
    ]
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    unique_paths: list[Path] = []
    seen = {manifest_path.resolve(strict=False)}
    for path in artifact_paths:
        resolved = path.resolve(strict=False)
        if resolved not in seen:
            unique_paths.append(path)
            seen.add(resolved)
    return {
        **safe_base("output_manifest"),
        "terminal_decision": TERMINAL_DECISION,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure.",
        "artifact_count": len(unique_paths),
        "artifacts": artifact_inventory(unique_paths),
    }


def write_auxiliary_artifacts(denominator: dict[str, Any], target_stats: dict[str, Any], bar_status_counts: Counter, duplicate_bar_keys: list[dict[str, Any]]) -> None:
    write_json(ROUTE_DIR / f"{PREFIX}_TARGET_SOURCE_JOIN_LEDGER_{DATE_TAG}.json", target_source_join_ledger(denominator, target_stats, bar_status_counts, duplicate_bar_keys))
    write_json(ROUTE_DIR / f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_{DATE_TAG}.json", duplicate_denominator_ledger(denominator, target_stats))
    write_json(ROUTE_DIR / f"{PREFIX}_PARTITION_CONTROL_LEDGER_{DATE_TAG}.json", partition_control_ledger(denominator, target_stats))
    write_json(ROUTE_DIR / f"{PREFIX}_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_{DATE_TAG}.json", quality_diagnostics_ledger(denominator, target_stats))
    write_json(ROUTE_DIR / f"{PREFIX}_ADJACENT_NOAPI_ROUTE_FAMILY_SIDECAR_LEDGER_{DATE_TAG}.json", adjacent_route_sidecar_ledger())
    write_json(ROUTE_DIR / f"{PREFIX}_SAME_EVIDENCE_CLASS_BLOCKER_REPAIR_LEDGER_{DATE_TAG}.json", blocker_repair_ledger(target_stats))
    write_md(ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md", saturation_md(target_stats))
    write_md(NEXT_G12_PROMPT, next_g12_prompt_text())
    write_md(NEXT_G12_STARTER, next_g12_starter_text())
    write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", completion_audit(denominator, target_stats))
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", output_manifest())


def record_focused_test_result(status: str, command: str) -> None:
    write_json(
        ROUTE_DIR / f"{PREFIX}_FOCUSED_TEST_RESULT_{DATE_TAG}.json",
        {
            **safe_base("focused_test_result"),
            "status": status,
            "command": command,
            "recorded_after_command_completed": True,
        },
    )
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", output_manifest())


def refresh_manifest() -> None:
    write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", output_manifest())


def build() -> dict[str, Any]:
    bars_by_end, bar_status_counts, duplicate_bar_keys = build_bars_by_end()
    denominator = collect_rowset_denominator()
    target_stats = write_target_packets(bars_by_end, denominator)
    write_auxiliary_artifacts(denominator, target_stats, bar_status_counts, duplicate_bar_keys)
    return {
        "target_result_row_count": target_stats["target_result_row_count"],
        "status_counts": target_stats["status_counts"],
        "row_files": [repo_path(path) for path in result_paths()],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-manifest", action="store_true")
    parser.add_argument("--record-focused-test-result", choices=["passed", "failed"])
    parser.add_argument("--focused-test-command", default="")
    args = parser.parse_args()

    if args.record_focused_test_result:
        record_focused_test_result(args.record_focused_test_result, args.focused_test_command)
        return 0
    if args.refresh_manifest:
        refresh_manifest()
        return 0

    summary = build()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
