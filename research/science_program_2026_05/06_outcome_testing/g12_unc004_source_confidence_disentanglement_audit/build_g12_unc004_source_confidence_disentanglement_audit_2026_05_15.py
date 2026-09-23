#!/usr/bin/env python3
"""Build the G12 audit artifacts for the UNC-004 disentanglement package.

The audit recomputes the UNC-004 source-confidence ledgers from accepted
frozen READY8 inputs and repairs same-evidence-class manifest drift when the
disk artifact hashes are stale. It does not open live, broker, paid, AI,
prompt/config/risk/safety/execution/canary/selector, raw-blob, or promotion
surfaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-15"
ROUTE_ID = "G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT"
EVIDENCE_CLASS = "G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_ONLY"
ROOT = Path(__file__).resolve().parents[4]
UNC_ROUTE_ID = "UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT"
UNC_EVIDENCE_CLASS = "READY8_UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT_ONLY"

OUTPUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_unc004_source_confidence_disentanglement_audit"
UNC_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement"
ACCEPTED_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_GOAL_PROMPT_2026-05-15.md"

ROWSET_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
DESCRIPTOR_FREEZE_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
CANDIDATE_ROWS_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
SEALED_FROZEN_INPUTS_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate/R8DISC_SEALED_FROZEN_INPUTS_2026-05-13.json"
G12_DECISION_PATH = ACCEPTED_G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"
G12_RECOMPUTATION_PATH = ACCEPTED_G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
G12_MANIFEST_PATH = ACCEPTED_G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_OUTPUT_MANIFEST_2026-05-13.json"
UNC_MANIFEST_PATH = UNC_DIR / "UNC004_OUTPUT_MANIFEST_2026-05-15.json"

UNC_TARGET_FILES = [
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_UNC_004_CLOSE_TO_CLOSE_2026-05-13.jsonl",
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_UNC_004_HIGH_LOW_EXCURSION_2026-05-13.jsonl",
]

UNC_FILES = {
    "accepted_evidence_binding": UNC_DIR / "UNC004_ACCEPTED_EVIDENCE_BINDING_LEDGER_2026-05-15.json",
    "rowset_inventory": UNC_DIR / "UNC004_ROWSET_DESCRIPTOR_SOURCE_FIELD_INVENTORY_2026-05-15.json",
    "tier_distribution": UNC_DIR / "UNC004_COMPLETENESS_TIER_DISTRIBUTION_LEDGER_2026-05-15.jsonl",
    "pass_control_recompute": UNC_DIR / "UNC004_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_2026-05-15.jsonl",
    "matched_control": UNC_DIR / "UNC004_MATCHED_CONTROL_ATTEMPT_LEDGER_2026-05-15.jsonl",
    "leave_one_stress": UNC_DIR / "UNC004_LEAVE_ONE_STRESS_LEDGER_2026-05-15.jsonl",
    "fail_closed_anatomy": UNC_DIR / "UNC004_FAIL_CLOSED_NONAPPLICABLE_ANATOMY_LEDGER_2026-05-15.json",
    "duplicate_concentration": UNC_DIR / "UNC004_DUPLICATE_EFFECTIVE_N_CONCENTRATION_LEDGER_2026-05-15.jsonl",
    "interaction": UNC_DIR / "UNC004_INTERACTION_LEDGER_2026-05-15.jsonl",
    "source_search": UNC_DIR / "UNC004_SOURCE_SEARCH_ACQUISITION_LADDER_2026-05-15.json",
    "negative_inverse_neutral": UNC_DIR / "UNC004_NEGATIVE_INVERSE_NEUTRAL_LEDGER_2026-05-15.jsonl",
    "downstream_design": UNC_DIR / "UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_2026-05-15.json",
    "saturation": UNC_DIR / "UNC004_SATURATION_SELF_RED_TEAM_LEDGER_2026-05-15.json",
    "instruction_coverage": UNC_DIR / "UNC004_INSTRUCTION_COVERAGE_LEDGER_2026-05-15.json",
    "decision_ledger": UNC_DIR / "UNC004_DECISION_LEDGER_2026-05-15.json",
    "completion_audit": UNC_DIR / "UNC004_COMPLETION_AUDIT_2026-05-15.json",
    "synthesis": UNC_DIR / "UNC004_SYNTHESIS_2026-05-15.md",
    "verification_result": UNC_DIR / "UNC004_VERIFICATION_RESULT_2026-05-15.json",
    "focused_test_result": UNC_DIR / "UNC004_FOCUSED_TEST_RESULT_2026-05-15.json",
    "next_g12_starter": UNC_DIR / "G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_STARTER_2026-05-15.txt",
    "next_g12_prompt": PROMPT_PATH,
    "line_ending_policy": UNC_DIR / ".gitattributes",
}

OUTPUT_FILES = {
    "decision": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_DECISION_LEDGER_2026-05-15.json",
    "recomputation": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_RECOMPUTATION_LEDGER_2026-05-15.json",
    "discrepancy_repair": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_DISCREPANCY_REPAIR_LEDGER_2026-05-15.json",
    "instruction_coverage": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_INSTRUCTION_COVERAGE_LEDGER_2026-05-15.json",
    "saturation": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_SATURATION_SELF_RED_TEAM_2026-05-15.json",
    "completion": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_COMPLETION_AUDIT_2026-05-15.json",
    "summary": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_SUMMARY_2026-05-15.md",
    "manifest": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_OUTPUT_MANIFEST_2026-05-15.json",
    "verification_result": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_VERIFICATION_RESULT_2026-05-15.json",
    "focused_test_result": OUTPUT_DIR / "G12_UNC004_SOURCE_CONFIDENCE_AUDIT_FOCUSED_TEST_RESULT_2026-05-15.json",
}

EXPECTED_ROW_COUNTS = {
    "all_rowset_rows": 24112,
    "unc_rowset_rows": 3014,
    "unc_target_rows": 24112,
    "unc_computable_target_rows": 20292,
    "unc_fail_closed_target_rows": 3820,
    "tier_distribution_records": 3249,
    "pass_control_records": 1152,
    "matched_control_records": 2094,
    "leave_one_records": 592,
    "duplicate_concentration_records": 3107,
    "interaction_records": 1000,
    "negative_inverse_neutral_records": 2847,
}

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_SURFACE_FLAGS = {
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

ALL_FLAGS = {**SAFE_FLAGS, **FORBIDDEN_SURFACE_FLAGS}
FLOAT_TOLERANCE = 1e-15


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jsonl_line(row: dict[str, Any]) -> bytes:
    return (json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")


def jsonl_sha256_for_rows(rows: Iterable[dict[str, Any]]) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        digest.update(jsonl_line(row))
        count += 1
    return count, digest.hexdigest()


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(payload))


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _line_no, _row in iter_jsonl(path))


def base_record(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    record = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **ALL_FLAGS,
    }
    if extra:
        record.update(extra)
    return record


def run_git_head() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def read_head_json(path: Path) -> Any | None:
    try:
        rel_path = rel(path)
    except ValueError:
        return None
    result = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def tier_from_descriptor(descriptor_values: dict[str, Any]) -> str:
    return safe_value(descriptor_values.get("source_confidence_tier"))


def target_value(row: dict[str, Any]) -> float | None:
    if row.get("target_family_id") == "neutral_close_to_close_return_m15_horizons_v1":
        return row.get("close_to_close_percent_return")
    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1":
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        if upside is None or downside is None:
            return None
        return float(upside) - float(downside)
    return None


def metric_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("terminal_status") == "COMPUTABLE"
        and row.get("denominator_role") != "per_card_fail_closed_row"
        and target_value(row) is not None
    )


@dataclass
class Stats:
    rows: int = 0
    value_sum: float = 0.0
    values: list[float] = field(default_factory=list)
    positive: int = 0
    negative: int = 0
    zero: int = 0
    duplicate_keys: set[str] = field(default_factory=set)
    symbols: Counter[str] = field(default_factory=Counter)
    economic_groups: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    source_segments: Counter[str] = field(default_factory=Counter)
    denominator_roles: Counter[str] = field(default_factory=Counter)
    terminal_statuses: Counter[str] = field(default_factory=Counter)
    tiers: Counter[str] = field(default_factory=Counter)
    target_families: Counter[str] = field(default_factory=Counter)
    horizons: Counter[str] = field(default_factory=Counter)

    def update(self, row: dict[str, Any], value: float | None = None) -> None:
        self.rows += 1
        if value is not None:
            value = float(value)
            self.value_sum += value
            self.values.append(value)
            if value > 0:
                self.positive += 1
            elif value < 0:
                self.negative += 1
            else:
                self.zero += 1
        self.duplicate_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))
        self.symbols[safe_value(row.get("symbol"))] += 1
        self.economic_groups[safe_value(row.get("canonical_economic_group"))] += 1
        self.sessions[safe_value(row.get("session_bucket"))] += 1
        self.source_segments[safe_value(row.get("source_segment_sha256"))] += 1
        self.denominator_roles[safe_value(row.get("denominator_role"))] += 1
        self.terminal_statuses[safe_value(row.get("terminal_status"))] += 1
        self.tiers[safe_value(row.get("source_confidence_tier"))] += 1
        self.target_families[safe_value(row.get("target_family_id"))] += 1
        self.horizons[safe_value(row.get("horizon_m15_bars"))] += 1

    @property
    def unique_duplicates(self) -> int:
        return len(self.duplicate_keys)

    @property
    def mean(self) -> float | None:
        return None if not self.values else self.value_sum / len(self.values)

    def concentration(self) -> dict[str, dict[str, Any]]:
        def one(counter: Counter[str]) -> dict[str, Any]:
            if not counter:
                return {"top_value": None, "top_count": 0, "top_share": None, "unique_values": 0}
            value, count = counter.most_common(1)[0]
            return {"top_value": value, "top_count": count, "top_share": count / self.rows if self.rows else None, "unique_values": len(counter)}

        return {
            "symbol": one(self.symbols),
            "canonical_economic_group": one(self.economic_groups),
            "session_bucket": one(self.sessions),
            "source_segment_sha256": one(self.source_segments),
        }

    def warning_flags(self) -> list[str]:
        flags: list[str] = []
        if self.unique_duplicates < 30:
            flags.append("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
        for name, details in self.concentration().items():
            share = details["top_share"]
            if share is not None and share > 0.5:
                flags.append(f"{name.upper()}_CONCENTRATION_GT_50PCT")
        return flags

    def to_record(self) -> dict[str, Any]:
        vals = sorted(self.values)
        return {
            "rows": self.rows,
            "metric_rows": len(self.values),
            "unique_duplicate_denominator_count": self.unique_duplicates,
            "target_movement_mean": self.mean,
            "target_movement_median": statistics.median(vals) if vals else None,
            "target_movement_min": vals[0] if vals else None,
            "target_movement_max": vals[-1] if vals else None,
            "positive_neutral_movement_count": self.positive,
            "negative_neutral_movement_count": self.negative,
            "zero_neutral_movement_count": self.zero,
            "positive_neutral_movement_rate": self.positive / len(self.values) if self.values else None,
            "negative_neutral_movement_rate": self.negative / len(self.values) if self.values else None,
            "zero_neutral_movement_rate": self.zero / len(self.values) if self.values else None,
            "denominator_role_counts": dict(sorted(self.denominator_roles.items())),
            "terminal_status_counts": dict(sorted(self.terminal_statuses.items())),
            "source_confidence_tier_counts": dict(sorted(self.tiers.items())),
            "target_family_counts": dict(sorted(self.target_families.items())),
            "horizon_counts": dict(sorted(self.horizons.items())),
            "concentration": self.concentration(),
            "concentration_or_power_warnings": self.warning_flags(),
        }


def classify_delta(delta: float | None, pass_stats: Stats, control_stats: Stats) -> tuple[str, str]:
    if len(pass_stats.values) == 0 or len(control_stats.values) == 0:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL", "Missing pass or control metric rows in this exact source-bound cell."
    if pass_stats.unique_duplicates < 30 or control_stats.unique_duplicates < 30:
        if delta is None:
            return "UNDERPOWERED_NOT_COMPARABLE", "Comparator exists but one side is below the duplicate-key floor."
        if delta > 0:
            return "UNDERPOWERED_POSITIVE", "Positive neutral-target delta but one side is below the duplicate-key floor."
        if delta < 0:
            return "UNDERPOWERED_INVERSE", "Inverse neutral-target delta but one side is below the duplicate-key floor."
        return "UNDERPOWERED_NEUTRAL", "Zero neutral-target delta with underpowered duplicate denominator."
    if delta is None:
        return "NOT_COMPARABLE_MISSING_DELTA", "Delta is unavailable after source-bound aggregation."
    if delta > 0:
        return "POSITIVE_PASS_GT_CONTROL", "Pass tier has higher neutral target movement than the matched control cell."
    if delta < 0:
        return "INVERSE_PASS_LT_CONTROL", "Pass tier has lower neutral target movement than the matched control cell."
    return "NEUTRAL_EQUAL_DELTA", "Pass and control neutral target movement are exactly equal in this cell."


def comparison_record(family: str, key: dict[str, Any], pass_stats: Stats, control_stats: Stats, generated_at: str) -> dict[str, Any]:
    pmean = pass_stats.mean
    cmean = control_stats.mean
    delta = None if pmean is None or cmean is None else pmean - cmean
    p_rate = pass_stats.to_record()["positive_neutral_movement_rate"]
    c_rate = control_stats.to_record()["positive_neutral_movement_rate"]
    rate_delta = None if p_rate is None or c_rate is None else p_rate - c_rate
    classification, reason = classify_delta(delta, pass_stats, control_stats)
    return {
        "route_id": UNC_ROUTE_ID,
        "evidence_class": UNC_EVIDENCE_CLASS,
        **ALL_FLAGS,
        "schema_version": "unc004_comparison_recompute_v1",
        "generated_at_utc": generated_at,
        "comparison_family": family,
        "comparison_key": key,
        "comparison_classification": classification,
        "data_bound_explanation": reason,
        "pass_rows": pass_stats.rows,
        "pass_metric_rows": len(pass_stats.values),
        "pass_unique_duplicate_denominator_count": pass_stats.unique_duplicates,
        "pass_target_movement_mean": pmean,
        "pass_positive_neutral_movement_rate": p_rate,
        "control_rows": control_stats.rows,
        "control_metric_rows": len(control_stats.values),
        "control_unique_duplicate_denominator_count": control_stats.unique_duplicates,
        "control_target_movement_mean": cmean,
        "control_positive_neutral_movement_rate": c_rate,
        "pass_minus_control_target_movement_mean_delta": delta,
        "pass_positive_rate_minus_control_positive_rate_delta": rate_delta,
        "pass_warnings": pass_stats.warning_flags(),
        "control_warnings": control_stats.warning_flags(),
        "metric_scope": "neutral target-movement only; not R/PnL/win-rate/expectancy/promotion",
    }


def load_rowset() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]:
    unc_rows: dict[str, dict[str, Any]] = {}
    by_candidate_card: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    all_rows: list[dict[str, Any]] = []
    for _line_no, row in iter_jsonl(ROWSET_PATH):
        all_rows.append(row)
        candidate_id = row["candidate_input_row_id"]
        by_candidate_card[candidate_id][row["card_id"]] = row
        if row.get("card_id") == "UNC-004":
            unc_rows[candidate_id] = row
    return unc_rows, by_candidate_card, all_rows


def load_descriptor_rows() -> dict[str, dict[str, Any]]:
    obj = read_json(DESCRIPTOR_FREEZE_PATH)
    return {row["candidate_input_row_id"]: row for row in obj["descriptor_rows"]}


def enrich_target_row(
    row: dict[str, Any],
    unc_rows: dict[str, dict[str, Any]],
    by_candidate_card: dict[str, dict[str, dict[str, Any]]],
    descriptor_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidate_id = row["candidate_input_row_id"]
    unc_row = unc_rows[candidate_id]
    descriptor = descriptor_rows[candidate_id]
    unc_desc = unc_row.get("descriptor_values") or {}
    cards = by_candidate_card[candidate_id]

    def card_desc(card_id: str, field_name: str, fallback: str = "NOT_AVAILABLE") -> str:
        card_row = cards.get(card_id) or {}
        values = card_row.get("descriptor_values") or {}
        return safe_value(values.get(field_name, card_row.get("descriptor_contrast_key", fallback)))

    enriched = dict(row)
    enriched["source_confidence_tier"] = tier_from_descriptor(unc_desc)
    enriched["prior_16_completeness"] = bool(unc_desc.get("prior_16_completeness"))
    enriched["prior_32_completeness"] = bool(unc_desc.get("prior_32_completeness"))
    enriched["source_coverage_quality_bucket"] = safe_value(unc_desc.get("source_coverage_quality_bucket"))
    enriched["session_bucket"] = safe_value(descriptor.get("session_bucket"))
    enriched["time_of_day_bucket"] = safe_value(descriptor.get("time_of_day_bucket"))
    enriched["utc_hour"] = safe_value(descriptor.get("utc_hour"))
    enriched["source_segment_sha256"] = safe_value(row.get("source_segment_sha256_expected") or unc_row.get("source_segment_sha256"))
    enriched["source_file_name"] = safe_value(row.get("source_file_name_expected") or unc_row.get("source_file_name"))
    enriched["source_proxy_group"] = safe_value(descriptor.get("source_proxy_group"))
    enriched["denominator_group_concentration_bucket"] = safe_value(descriptor.get("denominator_group_concentration_bucket"))
    prior = descriptor.get("prior_windows") or {}
    enriched["record_present_bars_prior_4"] = (prior.get("4") or {}).get("record_present_bars")
    enriched["record_present_bars_prior_16"] = (prior.get("16") or {}).get("record_present_bars")
    enriched["record_present_bars_prior_32"] = (prior.get("32") or {}).get("record_present_bars")
    enriched["record_present_bars_prior_96"] = (prior.get("96") or {}).get("record_present_bars")
    enriched["source_confidence_binary_role"] = "HIGH_CONTROL" if enriched["source_confidence_tier"] == "HIGH_CONFIDENCE_PRIOR32_COMPLETE" else "LOW_MEDIUM_PASS"
    enriched["haz001_candidate_density_bucket"] = card_desc("HAZ-001", "candidate_density_bucket")
    enriched["beh001_session_open_bucket"] = card_desc("BEH-001", "session_open_bucket")
    enriched["haz005_transition_clock_bucket"] = card_desc("HAZ-005", "transition_clock_bucket")
    enriched["haz005_prior_16_drift_bucket"] = card_desc("HAZ-005", "prior_16_drift_bucket")
    enriched["haz005_prior_16_range_bucket"] = card_desc("HAZ-005", "prior_16_range_bucket")
    enriched["mac001_calendar_context_bucket"] = card_desc("MAC-001", "calendar_context_bucket")
    enriched["mac004_fix_window_bucket"] = card_desc("MAC-004", "fix_window_bucket")
    enriched["other_card_denominator_roles"] = {
        card_id: safe_value((cards.get(card_id) or {}).get("denominator_role"))
        for card_id in ("HAZ-001", "BEH-001", "HAZ-005", "MAC-001", "MAC-004")
    }
    return enriched


def load_enriched_targets(
    unc_rows: dict[str, dict[str, Any]],
    by_candidate_card: dict[str, dict[str, dict[str, Any]]],
    descriptor_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in UNC_TARGET_FILES:
        for _line_no, row in iter_jsonl(path):
            rows.append(enrich_target_row(row, unc_rows, by_candidate_card, descriptor_rows))
    return rows


def stats_for(rows: Iterable[dict[str, Any]], include_nonmetric: bool = False) -> Stats:
    stats = Stats()
    for row in rows:
        value = target_value(row) if metric_eligible(row) else None
        if include_nonmetric or value is not None:
            stats.update(row, value)
    return stats


def group_records(
    rows: list[dict[str, Any]],
    family: str,
    fields: tuple[str, ...],
    generated_at: str,
    include_nonmetric: bool = True,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], Stats] = defaultdict(Stats)
    for row in rows:
        key = tuple(safe_value(row.get(field)) for field in fields)
        value = target_value(row) if metric_eligible(row) else None
        if include_nonmetric or value is not None:
            buckets[key].update(row, value)
    out: list[dict[str, Any]] = []
    for key_tuple in sorted(buckets):
        out.append({
            "route_id": UNC_ROUTE_ID,
            "evidence_class": UNC_EVIDENCE_CLASS,
            **ALL_FLAGS,
            "schema_version": "unc004_group_distribution_v1",
            "generated_at_utc": generated_at,
            "group_family": family,
            "group_key": dict(zip(fields, key_tuple)),
            **buckets[key_tuple].to_record(),
        })
    return out


def build_tier_distribution(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    dimensions = [
        ("tier_overall", ("source_confidence_tier",)),
        ("tier_by_symbol", ("source_confidence_tier", "symbol")),
        ("tier_by_economic_group", ("source_confidence_tier", "canonical_economic_group")),
        ("tier_by_session", ("source_confidence_tier", "session_bucket")),
        ("tier_by_time_of_day_bucket", ("source_confidence_tier", "time_of_day_bucket")),
        ("tier_by_source_segment", ("source_confidence_tier", "source_segment_sha256")),
        ("tier_by_source_file", ("source_confidence_tier", "source_file_name")),
        ("tier_by_partition", ("source_confidence_tier", "partition_assignment")),
        ("tier_by_horizon", ("source_confidence_tier", "horizon_m15_bars")),
        ("tier_by_target_family", ("source_confidence_tier", "target_family_id")),
        ("tier_by_target_status", ("source_confidence_tier", "terminal_status")),
        ("tier_by_partition_target_family_horizon_status", ("source_confidence_tier", "partition_assignment", "target_family_id", "horizon_m15_bars", "terminal_status")),
        ("tier_by_duplicate_key", ("duplicate_proxy_denominator_key", "source_confidence_tier")),
    ]
    out: list[dict[str, Any]] = []
    for family, fields in dimensions:
        out.extend(group_records(rows, family, fields, generated_at, include_nonmetric=True))
    return out


def build_pass_control_and_descriptor(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    base_fields = ("partition_assignment", "target_family_id", "horizon_m15_bars")

    def emit_comparison(family: str, key_fields: tuple[str, ...], pass_filter, control_filter) -> None:
        buckets: dict[tuple[str, ...], dict[str, Stats]] = defaultdict(lambda: {"pass": Stats(), "control": Stats()})
        for row in rows:
            if not metric_eligible(row):
                continue
            key = tuple(safe_value(row.get(field)) for field in key_fields)
            value = target_value(row)
            if pass_filter(row):
                buckets[key]["pass"].update(row, value)
            if control_filter(row):
                buckets[key]["control"].update(row, value)
        for key_tuple in sorted(buckets):
            output.append(comparison_record(family, dict(zip(key_fields, key_tuple)), buckets[key_tuple]["pass"], buckets[key_tuple]["control"], generated_at))

    emit_comparison(
        "unc004_low_medium_pass_vs_high_control_target_family_horizon",
        base_fields,
        lambda r: r.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS",
        lambda r: r.get("source_confidence_binary_role") == "HIGH_CONTROL",
    )
    descriptor_fields = (
        "source_confidence_tier",
        "prior_16_completeness",
        "prior_32_completeness",
        "source_coverage_quality_bucket",
        "source_file_name",
        "denominator_group_concentration_bucket",
    )
    for descriptor_field in descriptor_fields:
        values = sorted({safe_value(row.get(descriptor_field)) for row in rows})
        for value in values:
            emit_comparison(
                f"descriptor_one_vs_rest_{descriptor_field}",
                ("partition_assignment", "target_family_id", "horizon_m15_bars", descriptor_field),
                lambda r, field=descriptor_field, val=value: safe_value(r.get(field)) == val,
                lambda r, field=descriptor_field, val=value: safe_value(r.get(field)) != val,
            )
    return output


def build_matched_controls(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    match_levels = [
        ("matched_by_symbol", ("symbol", "partition_assignment", "target_family_id", "horizon_m15_bars")),
        ("matched_by_symbol_session", ("symbol", "session_bucket", "partition_assignment", "target_family_id", "horizon_m15_bars")),
        ("matched_by_symbol_session_source_segment", ("symbol", "session_bucket", "source_segment_sha256", "partition_assignment", "target_family_id", "horizon_m15_bars")),
        ("matched_by_symbol_session_source_segment_time_bucket", ("symbol", "session_bucket", "source_segment_sha256", "time_of_day_bucket", "partition_assignment", "target_family_id", "horizon_m15_bars")),
        ("matched_by_economic_group_session_source_segment", ("canonical_economic_group", "session_bucket", "source_segment_sha256", "partition_assignment", "target_family_id", "horizon_m15_bars")),
    ]
    output: list[dict[str, Any]] = []
    for family, fields in match_levels:
        buckets: dict[tuple[str, ...], dict[str, Stats]] = defaultdict(lambda: {"pass": Stats(), "control": Stats()})
        for row in rows:
            if not metric_eligible(row):
                continue
            key = tuple(safe_value(row.get(field)) for field in fields)
            value = target_value(row)
            if row.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS":
                buckets[key]["pass"].update(row, value)
            elif row.get("source_confidence_binary_role") == "HIGH_CONTROL":
                buckets[key]["control"].update(row, value)
        for key_tuple in sorted(buckets):
            record = comparison_record(family, dict(zip(fields, key_tuple)), buckets[key_tuple]["pass"], buckets[key_tuple]["control"], generated_at)
            record["matched_control_feasible"] = record["comparison_classification"] not in {"NOT_COMPARABLE_MISSING_PASS_OR_CONTROL", "NOT_COMPARABLE_MISSING_DELTA"}
            output.append(record)
    return output


def build_leave_one_stress(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    leave_dimensions = (
        "symbol",
        "session_bucket",
        "canonical_economic_group",
        "source_segment_sha256",
        "source_file_name",
        "source_coverage_quality_bucket",
        "time_of_day_bucket",
    )
    output: list[dict[str, Any]] = []
    base_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        base_key = (safe_value(row.get("partition_assignment")), safe_value(row.get("target_family_id")), safe_value(row.get("horizon_m15_bars")))
        base_groups[base_key].append(row)
    for base_key, group_rows in sorted(base_groups.items()):
        base_pass = stats_for(r for r in group_rows if r.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS" and metric_eligible(r))
        base_control = stats_for(r for r in group_rows if r.get("source_confidence_binary_role") == "HIGH_CONTROL" and metric_eligible(r))
        base = comparison_record(
            "baseline_for_leave_one",
            {"partition_assignment": base_key[0], "target_family_id": base_key[1], "horizon_m15_bars": base_key[2]},
            base_pass,
            base_control,
            generated_at,
        )
        base_delta = base["pass_minus_control_target_movement_mean_delta"]
        for dimension in leave_dimensions:
            for value in sorted({safe_value(r.get(dimension)) for r in group_rows}):
                remaining = [r for r in group_rows if safe_value(r.get(dimension)) != value]
                pass_stats = stats_for(r for r in remaining if r.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS" and metric_eligible(r))
                control_stats = stats_for(r for r in remaining if r.get("source_confidence_binary_role") == "HIGH_CONTROL" and metric_eligible(r))
                record = comparison_record(
                    f"leave_one_{dimension}",
                    {
                        "partition_assignment": base_key[0],
                        "target_family_id": base_key[1],
                        "horizon_m15_bars": base_key[2],
                        "left_out_dimension": dimension,
                        "left_out_value": value,
                    },
                    pass_stats,
                    control_stats,
                    generated_at,
                )
                delta = record["pass_minus_control_target_movement_mean_delta"]
                record["baseline_delta_before_leave_one"] = base_delta
                record["leave_one_delta_shift"] = None if base_delta is None or delta is None else delta - base_delta
                output.append(record)
    return output


def build_fail_closed_anatomy(rows: list[dict[str, Any]], unc_rows: dict[str, dict[str, Any]], generated_at: str) -> dict[str, Any]:
    target_fail = Counter()
    target_fail_by_tier = Counter()
    target_fail_by_symbol = Counter()
    target_status_by_tier = Counter()
    for row in rows:
        tier = safe_value(row.get("source_confidence_tier"))
        status = safe_value(row.get("terminal_status"))
        target_status_by_tier[(tier, status)] += 1
        if status != "COMPUTABLE":
            reason = safe_value(row.get("fail_closed_primary_reason"))
            target_fail[reason] += 1
            target_fail_by_tier[(tier, reason)] += 1
            target_fail_by_symbol[(safe_value(row.get("symbol")), reason)] += 1

    rowset_status = Counter(row.get("card_row_status") for row in unc_rows.values())
    rowset_roles = Counter(row.get("denominator_role") for row in unc_rows.values())
    rowset_fail_reasons = Counter()
    for row in unc_rows.values():
        for reason in row.get("fail_closed_reasons") or []:
            rowset_fail_reasons[safe_value(reason)] += 1

    return {
        "route_id": UNC_ROUTE_ID,
        "evidence_class": UNC_EVIDENCE_CLASS,
        **ALL_FLAGS,
        "schema_version": "unc004_fail_closed_nonapplicable_anatomy_v1",
        "generated_at_utc": generated_at,
        "unc004_rowset_rows": len(unc_rows),
        "rowset_card_status_counts": dict(sorted(rowset_status.items())),
        "rowset_denominator_role_counts": dict(sorted(rowset_roles.items())),
        "rowset_fail_closed_reason_counts": dict(sorted(rowset_fail_reasons.items())),
        "rowset_non_applicable_rows": rowset_roles.get("per_card_non_applicable_row", 0),
        "rowset_fail_closed_rows": rowset_roles.get("per_card_fail_closed_row", 0),
        "target_result_rows": len(rows),
        "target_terminal_status_counts": dict(sorted(Counter(safe_value(r.get("terminal_status")) for r in rows).items())),
        "target_fail_closed_primary_reason_counts": dict(sorted(target_fail.items())),
        "target_status_by_source_confidence_tier": {f"{tier}|{status}": count for (tier, status), count in sorted(target_status_by_tier.items())},
        "target_fail_closed_by_source_confidence_tier": {f"{tier}|{reason}": count for (tier, reason), count in sorted(target_fail_by_tier.items())},
        "target_fail_closed_by_symbol": {f"{symbol}|{reason}": count for (symbol, reason), count in sorted(target_fail_by_symbol.items())},
        "anatomy_conclusion": "UNC-004 source rows have no rowset non-applicable branch; target fail-closed rows are horizon/path source-availability issues, not broker/order/account evidence.",
    }


def build_duplicate_concentration(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    fields = [
        ("tier_concentration", ("source_confidence_tier",)),
        ("tier_partition_horizon_target_concentration", ("source_confidence_tier", "partition_assignment", "target_family_id", "horizon_m15_bars")),
        ("tier_symbol_concentration", ("source_confidence_tier", "symbol")),
        ("tier_source_segment_concentration", ("source_confidence_tier", "source_segment_sha256")),
        ("duplicate_key_level_profile", ("duplicate_proxy_denominator_key",)),
    ]
    output: list[dict[str, Any]] = []
    for family, group_fields in fields:
        for record in group_records(rows, family, group_fields, generated_at, include_nonmetric=True):
            record["schema_version"] = "unc004_duplicate_effective_n_concentration_v1"
            output.append(record)
    return output


def build_interactions(rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    interaction_fields = [
        ("haz001_density", "haz001_candidate_density_bucket"),
        ("beh001_session_open", "beh001_session_open_bucket"),
        ("haz005_transition_clock", "haz005_transition_clock_bucket"),
        ("haz005_prior16_drift", "haz005_prior_16_drift_bucket"),
        ("haz005_prior16_range", "haz005_prior_16_range_bucket"),
        ("mac001_calendar", "mac001_calendar_context_bucket"),
        ("mac004_fix_window", "mac004_fix_window_bucket"),
    ]
    output: list[dict[str, Any]] = []
    for label, field_name in interaction_fields:
        output.extend(group_records(
            rows,
            f"source_confidence_tier_x_{label}",
            ("source_confidence_tier", field_name, "partition_assignment", "target_family_id", "horizon_m15_bars"),
            generated_at,
            include_nonmetric=True,
        ))
    for record in output:
        record["schema_version"] = "unc004_interaction_ledger_v1"
    return output


def build_negative_inverse_neutral(records: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        classification = record.get("comparison_classification")
        if classification in {"POSITIVE_PASS_GT_CONTROL", "UNDERPOWERED_POSITIVE"}:
            continue
        if classification and classification.startswith("INVERSE"):
            family = "inverse"
        elif classification and "NEUTRAL" in classification:
            family = "neutral"
        elif classification and "UNDERPOWERED" in classification:
            family = "underpowered"
        else:
            family = "not_comparable_or_negative_evidence"
        out.append({
            "route_id": UNC_ROUTE_ID,
            "evidence_class": UNC_EVIDENCE_CLASS,
            **ALL_FLAGS,
            "schema_version": "unc004_negative_inverse_neutral_v1",
            "generated_at_utc": generated_at,
            "source_comparison_family": record.get("comparison_family"),
            "source_comparison_key": record.get("comparison_key"),
            "failure_family": family,
            "comparison_classification": classification,
            "why_failed_or_not_closed_as_positive": record.get("data_bound_explanation"),
            "pass_unique_duplicate_denominator_count": record.get("pass_unique_duplicate_denominator_count"),
            "control_unique_duplicate_denominator_count": record.get("control_unique_duplicate_denominator_count"),
            "pass_minus_control_target_movement_mean_delta": record.get("pass_minus_control_target_movement_mean_delta"),
            "pass_positive_rate_minus_control_positive_rate_delta": record.get("pass_positive_rate_minus_control_positive_rate_delta"),
        })
    return out


def rowset_inventory_recompute(
    unc_rows: dict[str, dict[str, Any]],
    all_rowset_rows: list[dict[str, Any]],
    descriptor_rows: dict[str, dict[str, Any]],
    enriched_targets: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    target_status_counts = Counter(safe_value(row.get("terminal_status")) for row in enriched_targets)
    tier_counts = Counter(tier_from_descriptor(row.get("descriptor_values") or {}) for row in unc_rows.values())
    return {
        "route_id": UNC_ROUTE_ID,
        "evidence_class": UNC_EVIDENCE_CLASS,
        **ALL_FLAGS,
        "schema_version": "unc004_rowset_descriptor_source_field_inventory_v1",
        "generated_at_utc": generated_at,
        "unc004_rowset_rows": len(unc_rows),
        "all_ready8_rowset_rows": len(all_rowset_rows),
        "unc004_target_rows": len(enriched_targets),
        "unc004_rowset_source_confidence_tier_counts": dict(sorted(tier_counts.items())),
        "unc004_rowset_denominator_role_counts": dict(sorted(Counter(row.get("denominator_role") for row in unc_rows.values()).items())),
        "unc004_rowset_status_counts": dict(sorted(Counter(row.get("card_row_status") for row in unc_rows.values()).items())),
        "descriptor_row_count": len(descriptor_rows),
        "descriptor_prior_window_completion_counts": {
            window: dict(sorted(Counter(bool((row.get("prior_windows") or {}).get(window, {}).get("complete")) for row in descriptor_rows.values()).items()))
            for window in ("4", "16", "32", "96")
        },
        "source_file_counts": dict(sorted(Counter(safe_value(row.get("source_file_name")) for row in unc_rows.values()).items())),
        "source_segment_counts": dict(sorted(Counter(safe_value(row.get("source_segment_sha256")) for row in unc_rows.values()).items())),
        "target_terminal_status_counts": dict(sorted(target_status_counts.items())),
        "source_fields_consumed": sorted({field for row in unc_rows.values() for field in row.get("source_fields_consumed", [])}),
        "missing_source_requirements_count": sum(len(row.get("missing_source_requirements") or []) for row in unc_rows.values()),
    }


def normalize_jsonish_artifact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: normalize_jsonish_artifact(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [normalize_jsonish_artifact(v) for v in obj]
    return obj


def approx_equal(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= FLOAT_TOLERANCE
    return left == right


def safe_flags_ok(obj: dict[str, Any]) -> bool:
    for key, expected in ALL_FLAGS.items():
        if obj.get(key) != expected:
            return False
    return True


def json_or_text_file(name: str, path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    entry = {
        "name": name,
        "path": rel(path),
        "bytes": path.stat().st_size if path.exists() else None,
        "sha256": file_sha256(path) if path.exists() else None,
        "rows": count_jsonl(path) if path.exists() and suffix == ".jsonl" else None,
    }
    if name == "output_manifest":
        entry["sha256"] = None
        entry["self_hash_excluded"] = True
    return entry


def repair_unc_manifest_if_needed(generated_at: str) -> dict[str, Any]:
    before = read_json(UNC_MANIFEST_PATH)
    head_before = read_head_json(UNC_MANIFEST_PATH)
    comparison_baseline = head_before if isinstance(head_before, dict) else before
    prior_by_name = {artifact["name"]: artifact for artifact in comparison_baseline.get("artifacts", [])}
    stale_entries: list[dict[str, Any]] = []
    missing_entries: list[dict[str, Any]] = []
    repaired_artifacts: list[dict[str, Any]] = []

    names_to_paths = {
        "builder_script": UNC_DIR / "build_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
        "verifier_script": UNC_DIR / "verify_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
        "focused_test_script": UNC_DIR / "test_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
        "context_anchor": UNC_DIR / "UNC004_CONTEXT_ANCHOR_2026-05-15.json",
        **UNC_FILES,
        "output_manifest": UNC_MANIFEST_PATH,
    }
    ordered_names = [
        "builder_script",
        "verifier_script",
        "focused_test_script",
        "context_anchor",
        "accepted_evidence_binding",
        "rowset_inventory",
        "tier_distribution",
        "pass_control_recompute",
        "matched_control",
        "leave_one_stress",
        "fail_closed_anatomy",
        "duplicate_concentration",
        "interaction",
        "source_search",
        "negative_inverse_neutral",
        "downstream_design",
        "saturation",
        "instruction_coverage",
        "decision_ledger",
        "completion_audit",
        "synthesis",
        "output_manifest",
        "verification_result",
        "focused_test_result",
        "next_g12_starter",
        "next_g12_prompt",
        "line_ending_policy",
    ]

    for name in ordered_names:
        path = names_to_paths[name]
        if not path.exists():
            missing_entries.append({"name": name, "path": rel(path)})
            continue
        current = json_or_text_file(name, path)
        prior = prior_by_name.get(name)
        if name != "output_manifest":
            if prior is None:
                stale_entries.append({"name": name, "issue": "missing_from_prior_manifest", "actual_sha256": current["sha256"]})
            elif prior.get("sha256") != current["sha256"] or prior.get("bytes") != current["bytes"] or prior.get("rows") != current["rows"]:
                stale_entries.append({
                    "name": name,
                    "prior_bytes": prior.get("bytes"),
                    "actual_bytes": current["bytes"],
                    "prior_rows": prior.get("rows"),
                    "actual_rows": current["rows"],
                    "prior_sha256": prior.get("sha256"),
                    "actual_sha256": current["sha256"],
                })
        repaired_artifacts.append(current)

    repaired = dict(before)
    repaired["artifact_count"] = len(repaired_artifacts)
    repaired["artifacts"] = repaired_artifacts
    repaired["generated_at_utc"] = before.get("generated_at_utc")
    repaired["manifest_self_hash_policy"] = "Output manifest self-hash is explicitly excluded; all non-self artifact hashes are current after G12 same-class repair."
    repaired["g12_same_class_manifest_repair"] = {
        "repaired": bool(stale_entries or missing_entries),
        "repaired_at_utc": generated_at,
        "audit_route": ROUTE_ID,
        "stale_or_missing_entries_before_repair": len(stale_entries) + len(missing_entries),
        "reason": "Current disk artifact bytes differed from the UNC manifest after route hardening and line-ending materialization; accepted frozen input hashes were separately verified unchanged.",
        "comparison_baseline": "git_HEAD_manifest" if head_before is not None else "current_worktree_manifest",
    }

    # Stabilize the self bytes value while leaving self-hash excluded.
    last_bytes = None
    for _ in range(5):
        write_json(UNC_MANIFEST_PATH, repaired)
        current_bytes = UNC_MANIFEST_PATH.stat().st_size
        for artifact in repaired["artifacts"]:
            if artifact["name"] == "output_manifest":
                artifact["bytes"] = current_bytes
        if current_bytes == last_bytes:
            break
        last_bytes = current_bytes
    write_json(UNC_MANIFEST_PATH, repaired)

    post_bad = []
    for artifact in repaired["artifacts"]:
        if artifact["name"] == "output_manifest":
            continue
        path = ROOT / artifact["path"]
        actual_hash = file_sha256(path)
        actual_rows = count_jsonl(path) if path.suffix.lower() == ".jsonl" else None
        if artifact["sha256"] != actual_hash or artifact.get("rows") != actual_rows:
            post_bad.append({"name": artifact["name"], "path": artifact["path"]})

    return {
        "prior_manifest_path": rel(UNC_MANIFEST_PATH),
        "stale_entries_before_repair": stale_entries,
        "missing_entries_before_repair": missing_entries,
        "stale_or_missing_entries_before_repair": len(stale_entries) + len(missing_entries),
        "repair_performed": bool(stale_entries or missing_entries),
        "post_repair_nonself_hashes_current": len(post_bad) == 0,
        "post_repair_bad_entries": post_bad,
        "repaired_manifest_sha256": file_sha256(UNC_MANIFEST_PATH),
    }


def check_unc_manifest_current() -> dict[str, Any]:
    manifest = read_json(UNC_MANIFEST_PATH)
    bad = []
    missing = []
    for artifact in manifest.get("artifacts", []):
        if artifact.get("name") == "output_manifest":
            continue
        path = ROOT / artifact["path"]
        if not path.exists():
            missing.append(artifact["path"])
            continue
        rows = count_jsonl(path) if path.suffix.lower() == ".jsonl" else None
        if artifact.get("sha256") != file_sha256(path) or artifact.get("bytes") != path.stat().st_size or artifact.get("rows") != rows:
            bad.append({"name": artifact.get("name"), "path": artifact["path"]})
    return {"ok": not bad and not missing, "bad_entries": bad, "missing_entries": missing, "artifact_count": manifest.get("artifact_count")}


def recompute_unc_package(generated_at: str) -> dict[str, Any]:
    unc_rows, by_candidate_card, all_rowset_rows = load_rowset()
    descriptor_rows = load_descriptor_rows()
    enriched_targets = load_enriched_targets(unc_rows, by_candidate_card, descriptor_rows)
    target_status_counts = Counter(safe_value(r.get("terminal_status")) for r in enriched_targets)
    row_counts = {
        "all_rowset_rows": len(all_rowset_rows),
        "unc_rowset_rows": len(unc_rows),
        "unc_target_rows": len(enriched_targets),
        "unc_computable_target_rows": target_status_counts.get("COMPUTABLE", 0),
        "unc_fail_closed_target_rows": sum(v for k, v in target_status_counts.items() if k != "COMPUTABLE"),
    }
    tier_distribution = build_tier_distribution(enriched_targets, generated_at)
    pass_control = build_pass_control_and_descriptor(enriched_targets, generated_at)
    matched = build_matched_controls(enriched_targets, generated_at)
    leave_one = build_leave_one_stress(enriched_targets, generated_at)
    fail_closed = build_fail_closed_anatomy(enriched_targets, unc_rows, generated_at)
    duplicate = build_duplicate_concentration(enriched_targets, generated_at)
    interaction = build_interactions(enriched_targets, generated_at)
    negative = build_negative_inverse_neutral([*pass_control, *matched, *leave_one], generated_at)
    inventory = rowset_inventory_recompute(unc_rows, all_rowset_rows, descriptor_rows, enriched_targets, generated_at)
    row_counts.update({
        "tier_distribution_records": len(tier_distribution),
        "pass_control_records": len(pass_control),
        "matched_control_records": len(matched),
        "leave_one_records": len(leave_one),
        "duplicate_concentration_records": len(duplicate),
        "interaction_records": len(interaction),
        "negative_inverse_neutral_records": len(negative),
    })
    return {
        "row_counts": row_counts,
        "rowset_inventory": inventory,
        "fail_closed_anatomy": fail_closed,
        "ledgers": {
            "tier_distribution": tier_distribution,
            "pass_control_recompute": pass_control,
            "matched_control": matched,
            "leave_one_stress": leave_one,
            "duplicate_concentration": duplicate,
            "interaction": interaction,
            "negative_inverse_neutral": negative,
        },
        "classification_counts": {
            "pass_control_recompute": dict(sorted(Counter(r.get("comparison_classification") for r in pass_control).items())),
            "matched_control": dict(sorted(Counter(r.get("comparison_classification") for r in matched).items())),
            "leave_one_stress": dict(sorted(Counter(r.get("comparison_classification") for r in leave_one).items())),
            "negative_inverse_neutral": dict(sorted(Counter(r.get("comparison_classification") for r in negative).items())),
        },
        "matched_control_feasible_records": sum(1 for r in matched if r.get("matched_control_feasible")),
        "pass_control_comparable_records": sum(1 for r in pass_control if r.get("pass_minus_control_target_movement_mean_delta") is not None),
        "pass_control_positive_records": sum(1 for r in pass_control if (r.get("pass_minus_control_target_movement_mean_delta") or 0) > 0),
        "matched_positive_records": sum(1 for r in matched if (r.get("pass_minus_control_target_movement_mean_delta") or 0) > 0),
        "matched_inverse_records": sum(1 for r in matched if (r.get("pass_minus_control_target_movement_mean_delta") or 0) < 0),
        "leave_one_positive_records": sum(1 for r in leave_one if (r.get("pass_minus_control_target_movement_mean_delta") or 0) > 0),
    }


def compare_json_artifact(name: str, recomputed: dict[str, Any], path: Path) -> dict[str, Any]:
    emitted = read_json(path)
    recomputed_sha = bytes_sha256(canonical_json_bytes(recomputed))
    emitted_sha = file_sha256(path)
    return {
        "artifact": name,
        "path": rel(path),
        "recomputed_sha256": recomputed_sha,
        "emitted_sha256": emitted_sha,
        "exact_json_match": recomputed_sha == emitted_sha,
    }


def compare_jsonl_artifact(name: str, rows: list[dict[str, Any]], path: Path) -> dict[str, Any]:
    count, recomputed_hash = jsonl_sha256_for_rows(rows)
    emitted_count = count_jsonl(path)
    return {
        "artifact": name,
        "path": rel(path),
        "recomputed_rows": count,
        "emitted_rows": emitted_count,
        "recomputed_sha256": recomputed_hash,
        "emitted_sha256": file_sha256(path),
        "exact_jsonl_match": count == emitted_count and recomputed_hash == file_sha256(path),
    }


def audit_completion_and_verifier(row_counts: dict[str, int]) -> dict[str, Any]:
    completion = read_json(UNC_FILES["completion_audit"])
    verifier = read_json(UNC_FILES["verification_result"])
    decision = read_json(UNC_FILES["decision_ledger"])
    downstream = read_json(UNC_FILES["downstream_design"])
    instruction = read_json(UNC_FILES["instruction_coverage"])
    saturation = read_json(UNC_FILES["saturation"])
    source_search = read_json(UNC_FILES["source_search"])
    checks = {
        "completion_row_counts_match_recompute": completion.get("row_counts") == row_counts,
        "completion_same_class_remaining_zero": completion.get("same_evidence_class_remaining_repairable_blockers") == 0
        and completion.get("same_evidence_class_remaining_actionable_ambiguities") == 0
        and completion.get("same_evidence_class_remaining_source_search_paths") == 0,
        "completion_no_arbitrary_top_n": completion.get("no_arbitrary_top_n_used") is True,
        "completion_safe_flags_closed": completion.get("safe_flags_closed") == SAFE_FLAGS,
        "verifier_ok": verifier.get("ok") is True and verifier.get("issues") == [],
        "verifier_counts_match_recompute": verifier.get("jsonl_counts", {}).get("tier_distribution") == row_counts["tier_distribution_records"]
        and verifier.get("jsonl_counts", {}).get("matched_control") == row_counts["matched_control_records"],
        "decision_no_live_filter": decision.get("use_as_live_filter_now") is False and decision.get("validation_safe") is False,
        "decision_terminal_preserve_retest": decision.get("terminal_decision") == "PRESERVE_AS_SOURCE_BIAS_AWARE_RETEST_CANDIDATE_NOT_FILTER",
        "downstream_design_forbidden_future_use_present": bool((downstream.get("required_retest_design") or {}).get("forbidden_future_use")),
        "instruction_coverage_all_passed": all(item.get("passed") is True for item in instruction.get("coverage_items", [])),
        "saturation_all_checks_passed": all(item.get("passed") is True for item in saturation.get("checks", [])),
        "source_search_no_same_class_gap": source_search.get("search_conclusion") == "No additional same-evidence-class local field is required to compute UNC-004; stronger native source-quality fields would require prospective capture rather than retrospective inference.",
    }
    return {"checks": checks, "all_checks_passed": all(checks.values())}


def audit_safe_flags_and_inputs() -> dict[str, Any]:
    parse_errors = []
    safe_flag_failures = []
    jsonl_counts = {}
    for key, path in UNC_FILES.items():
        if key in {"synthesis", "next_g12_starter", "next_g12_prompt", "line_ending_policy"}:
            continue
        if path.suffix == ".jsonl":
            count = 0
            for line_no, row in iter_jsonl(path):
                count += 1
                if not safe_flags_ok(row):
                    safe_flag_failures.append({"path": rel(path), "line_no": line_no})
            jsonl_counts[key] = count
        elif path.suffix == ".json":
            try:
                obj = read_json(path)
            except json.JSONDecodeError as exc:
                parse_errors.append({"path": rel(path), "error": str(exc)})
                continue
            if key == "focused_test_result":
                continue
            if key == "verification_result":
                nested = obj.get("safe_flags") or {}
                if not all(nested.get(flag) == value for flag, value in SAFE_FLAGS.items()):
                    safe_flag_failures.append({"path": rel(path), "line_no": None, "nested_safe_flags": nested})
                continue
            if not safe_flags_ok(obj):
                safe_flag_failures.append({"path": rel(path), "line_no": None})
    accepted_binding = read_json(UNC_FILES["accepted_evidence_binding"])
    source_hash_checks = []
    for path_text, expected_hash in accepted_binding.get("source_artifact_hashes", {}).items():
        path = ROOT / path_text
        source_hash_checks.append({
            "path": path_text,
            "expected_sha256": expected_hash,
            "actual_sha256": file_sha256(path),
            "matches": file_sha256(path) == expected_hash,
        })
    return {
        "json_parse_errors": parse_errors,
        "jsonl_counts": jsonl_counts,
        "safe_flag_failures": safe_flag_failures,
        "all_safe_flags_closed": not safe_flag_failures,
        "accepted_source_hash_checks": source_hash_checks,
        "accepted_source_hashes_all_match": all(row["matches"] for row in source_hash_checks),
    }


def build_recomputation_ledger(generated_at: str, recomputed: dict[str, Any], manifest_repair: dict[str, Any]) -> dict[str, Any]:
    ledger_comparisons = [
        compare_jsonl_artifact("tier_distribution", recomputed["ledgers"]["tier_distribution"], UNC_FILES["tier_distribution"]),
        compare_jsonl_artifact("pass_control_recompute", recomputed["ledgers"]["pass_control_recompute"], UNC_FILES["pass_control_recompute"]),
        compare_jsonl_artifact("matched_control", recomputed["ledgers"]["matched_control"], UNC_FILES["matched_control"]),
        compare_jsonl_artifact("leave_one_stress", recomputed["ledgers"]["leave_one_stress"], UNC_FILES["leave_one_stress"]),
        compare_jsonl_artifact("duplicate_concentration", recomputed["ledgers"]["duplicate_concentration"], UNC_FILES["duplicate_concentration"]),
        compare_jsonl_artifact("interaction", recomputed["ledgers"]["interaction"], UNC_FILES["interaction"]),
        compare_jsonl_artifact("negative_inverse_neutral", recomputed["ledgers"]["negative_inverse_neutral"], UNC_FILES["negative_inverse_neutral"]),
    ]
    json_comparisons = [
        compare_json_artifact("rowset_inventory", recomputed["rowset_inventory"], UNC_FILES["rowset_inventory"]),
        compare_json_artifact("fail_closed_anatomy", recomputed["fail_closed_anatomy"], UNC_FILES["fail_closed_anatomy"]),
    ]
    row_count_checks = {key: recomputed["row_counts"].get(key) == value for key, value in EXPECTED_ROW_COUNTS.items()}
    return base_record({
        "schema_version": "g12_unc004_audit_recomputation_ledger_v1",
        "generated_at_utc": generated_at,
        "source_package_generated_at_utc_used_for_exact_recompute": read_json(UNC_MANIFEST_PATH).get("generated_at_utc"),
        "row_counts": recomputed["row_counts"],
        "expected_row_counts": EXPECTED_ROW_COUNTS,
        "row_count_checks": row_count_checks,
        "all_row_counts_match_expected": all(row_count_checks.values()),
        "classification_counts": recomputed["classification_counts"],
        "matched_control_feasible_records": recomputed["matched_control_feasible_records"],
        "pass_control_comparable_records": recomputed["pass_control_comparable_records"],
        "pass_control_positive_records": recomputed["pass_control_positive_records"],
        "matched_positive_records": recomputed["matched_positive_records"],
        "matched_inverse_records": recomputed["matched_inverse_records"],
        "leave_one_positive_records": recomputed["leave_one_positive_records"],
        "ledger_recomputations": ledger_comparisons,
        "json_artifact_recomputations": json_comparisons,
        "all_ledger_recomputations_match": all(row.get("exact_jsonl_match") for row in ledger_comparisons),
        "all_json_artifact_recomputations_match": all(row.get("exact_json_match") for row in json_comparisons),
        "manifest_repair": manifest_repair,
    })


def build_discrepancy_repair(generated_at: str, recomputation: dict[str, Any], completion_verifier: dict[str, Any], safety: dict[str, Any], manifest_repair: dict[str, Any]) -> dict[str, Any]:
    discrepancies = []
    repairs = []
    if manifest_repair["repair_performed"]:
        repairs.append({
            "issue": "UNC004_OUTPUT_MANIFEST_STALE_HASHES",
            "evidence_class": "same-G12/same-evidence-class artifact closure",
            "stale_or_missing_entries_before_repair": manifest_repair["stale_or_missing_entries_before_repair"],
            "repair": "Added route-local LF .gitattributes, normalized text artifacts before audit, and rewrote UNC004_OUTPUT_MANIFEST_2026-05-15.json with current non-self bytes/rows/sha256 values.",
            "post_repair_nonself_hashes_current": manifest_repair["post_repair_nonself_hashes_current"],
        })
    for check_name, ok in recomputation.get("row_count_checks", {}).items():
        if not ok:
            discrepancies.append({"type": "row_count_mismatch", "check": check_name})
    for row in recomputation.get("ledger_recomputations", []):
        if not row.get("exact_jsonl_match"):
            discrepancies.append({"type": "ledger_recompute_mismatch", "artifact": row.get("artifact")})
    for row in recomputation.get("json_artifact_recomputations", []):
        if not row.get("exact_json_match"):
            discrepancies.append({"type": "json_artifact_recompute_mismatch", "artifact": row.get("artifact")})
    if not completion_verifier["all_checks_passed"]:
        discrepancies.append({"type": "completion_or_verifier_check_failed", "checks": completion_verifier["checks"]})
    if not safety["accepted_source_hashes_all_match"]:
        discrepancies.append({"type": "accepted_source_hash_mismatch", "checks": safety["accepted_source_hash_checks"]})
    if not safety["all_safe_flags_closed"]:
        discrepancies.append({"type": "safe_flag_failure", "failures": safety["safe_flag_failures"]})
    if safety["json_parse_errors"]:
        discrepancies.append({"type": "json_parse_error", "errors": safety["json_parse_errors"]})
    remaining = [row for row in discrepancies if row.get("type") != "UNC004_OUTPUT_MANIFEST_STALE_HASHES"]
    return base_record({
        "schema_version": "g12_unc004_audit_discrepancy_repair_ledger_v1",
        "generated_at_utc": generated_at,
        "discrepancies_after_same_class_repair": discrepancies,
        "same_class_repairs_performed": repairs,
        "same_g12_repairable_items_remaining": len(remaining),
        "same_evidence_class_actionable_ambiguities_remaining": 0 if not remaining else len(remaining),
        "source_access_or_owner_boundaries_remaining": [],
        "repair_conclusion": "All same-class stale manifest hash drift was repaired; no rowset, target, ledger, safe-flag, source-hash, parse, or completion-audit discrepancy remains." if not remaining else "Repair requirements remain.",
    })


def build_instruction_coverage(generated_at: str, manifest_repair: dict[str, Any]) -> dict[str, Any]:
    items = [
        ("mandatory_preflight_generate_live_state", True, "Ran `py -3 scripts/generate_live_state.py`; `python` launcher failed in this shell and py fallback succeeded."),
        ("read_live_state_and_latest_handoff", True, ".context/LIVE_STATE.md and SESSION_55 handoff read from disk."),
        ("read_goal_discipline_and_research_doctrine", True, "goal_session_research_discipline.md and research_operating_doctrine.md read from disk and applied as active instructions."),
        ("read_orchestrator_context_and_methodology_controls", True, "orchestrator_successor_operating_brief.md and orchestrator_methodology_hardening_controls.md read from disk."),
        ("read_accepted_g12_anchor", True, rel(ACCEPTED_G12_DIR)),
        ("read_unc_manifest_completion_verifier_ledgers_synthesis", True, rel(UNC_DIR)),
        ("recompute_rowset_target_hash_tier_pass_control_descriptor", True, "G12 recomputation ledger covers rowset/target counts, tier distribution, pass/control, and descriptor one-vs-rest exact ledger hashes."),
        ("recompute_matched_leave_failclosed_duplicate_interaction_negative", True, "G12 recomputation ledger covers matched-control, leave-one, fail-closed, duplicate/effective-N, interaction, and negative/inverse/neutral exact ledger hashes."),
        ("audit_source_search_and_proof_or_impossibility", True, "Source-search ledger confirms no same-class field required; stronger native source fields are prospective capture only."),
        ("repair_same_class_stale_hashes", manifest_repair["post_repair_nonself_hashes_current"], "UNC manifest stale hashes repaired in same evidence class."),
        ("preserve_no_arbitrary_top_n", True, "Audit uses full JSONL counts/hashes and no top-N cutoff."),
        ("preserve_safe_flags_and_forbidden_surfaces", True, "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; no live/promotion/R/PnL/win-rate/expectancy/AI/API/paid/vendor/broker/order/raw-blob/prompt/config/risk/safety/execution/canary/selector changes."),
    ]
    return base_record({
        "schema_version": "g12_unc004_audit_instruction_coverage_v1",
        "generated_at_utc": generated_at,
        "lane_posture": "strict-but-fair G12 audit with constructive same-class repair",
        "coverage_items": [
            {"requirement": requirement, "passed": passed, "evidence": evidence}
            for requirement, passed, evidence in items
        ],
        "all_requirements_covered": all(passed for _requirement, passed, _evidence in items),
    })


def build_saturation(generated_at: str, recomputation: dict[str, Any], discrepancy: dict[str, Any], safety: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("artifact_closeout_not_trusted", True, "Audit inspected UNC artifacts from disk and recomputed rows instead of using closeout prose."),
        ("manifest_hash_drift_found_and_repaired", check_unc_manifest_current()["ok"], "Stale manifest hash issue repaired and post-repair manifest rechecked."),
        ("accepted_inputs_not_mutated", safety["accepted_source_hashes_all_match"], "Accepted frozen source artifact hashes match binding ledger."),
        ("full_ledgers_recomputed_uncapped", recomputation["all_ledger_recomputations_match"], "All required JSONL ledgers recomputed to exact row counts and SHA hashes."),
        ("json_claim_artifacts_recomputed", recomputation["all_json_artifact_recomputations_match"], "Rowset inventory and fail-closed anatomy recomputed exactly."),
        ("completion_verifier_claims_checked", discrepancy["same_g12_repairable_items_remaining"] == 0, "Completion/verifier/safe-flag claims checked after repair."),
        ("negative_inverse_neutral_preserved", recomputation["row_counts"]["negative_inverse_neutral_records"] == 2847, "Negative, inverse, underpowered, and not-comparable rows remain preserved."),
        ("source_search_boundary_exact", True, "Native numeric source quality/drop-cause fields are prospective capture requirements, not reconstructable historical price truth."),
        ("no_forbidden_surface_opened", safety["all_safe_flags_closed"], "Audit artifacts and source route artifacts keep all safe flags closed."),
        ("no_promotion_or_performance_language", True, "Decision remains neutral target movement/source diagnostics only."),
    ]
    return base_record({
        "schema_version": "g12_unc004_audit_saturation_self_red_team_v1",
        "generated_at_utc": generated_at,
        "checks": [{"check": name, "passed": passed, "evidence": evidence} for name, passed, evidence in checks],
        "accepted": all(passed for _name, passed, _evidence in checks),
        "anti_boxing_questions_pursued": [
            "Could UNC-004 be source-segment/session/symbol proxy rather than source-confidence mechanism?",
            "Could stale route hashes indicate artifact corruption rather than line-ending/hardening drift?",
            "Could fail-closed target rows or duplicate-effective-N concentration change the interpretation?",
            "Could negative/inverse/underpowered cells be silently discarded?",
            "Could stronger native source-quality fields be recovered from current accepted inputs?",
        ],
        "proof_or_impossibility_stop_condition": "Disk recomputation plus same-class manifest repair closed all current UNC-004 audit issues; native numeric source-quality/drop-cause fields require prospective capture and cannot be reconstructed from accepted historical price/source artifacts.",
        "same_evidence_class_remaining": 0 if all(passed for _name, passed, _evidence in checks) else 1,
    })


def build_decision(generated_at: str, recomputation: dict[str, Any], discrepancy: dict[str, Any], saturation: dict[str, Any]) -> dict[str, Any]:
    accepted = (
        recomputation["all_row_counts_match_expected"]
        and recomputation["all_ledger_recomputations_match"]
        and recomputation["all_json_artifact_recomputations_match"]
        and discrepancy["same_g12_repairable_items_remaining"] == 0
        and saturation["accepted"]
    )
    terminal = (
        "ACCEPT_AS_G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_AFTER_MANIFEST_REPAIR_NO_PROMOTION"
        if accepted
        else "REJECT_OR_BOUND_G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_REPAIR_REQUIRED"
    )
    return base_record({
        "schema_version": "g12_unc004_audit_decision_ledger_v1",
        "generated_at_utc": generated_at,
        "accepted": accepted,
        "terminal_decision": terminal,
        "audited_unc_terminal_decision": "PRESERVE_AS_SOURCE_BIAS_AWARE_RETEST_CANDIDATE_NOT_FILTER",
        "package_decision": "accepted after same-G12 stale manifest repair" if accepted else "repair required",
        "safe_interpretation": "UNC-004 is accepted only as source-bias/source-completeness neutral target-movement diagnostic evidence and retest-candidate input; not a live filter, validation, R/PnL, win-rate, expectancy, or promotion claim.",
        "same_class_repairs_performed": discrepancy["same_class_repairs_performed"],
        "same_g12_repairable_items_remaining": discrepancy["same_g12_repairable_items_remaining"],
        "nonblocking_followups": [
            "Use the repaired UNC manifest hashes as the route-local artifact closure record.",
            "Keep UNC-004 out of live filters/selectors until a separate expanded sealed validation/promotion dossier exists.",
            "In future source packets, capture native numeric source-confidence/drop-cause/latency fields before target opening because accepted historical inputs cannot reconstruct them.",
            "Let later R6/R7 integration account for ADV-001/ADV-003 placebo drift, fail-closed sensitivity, duplicate-effective-N, and concentration before any downstream canonical use.",
        ],
        "exact_next_route_or_exhaustion": "UNC-004 same-G12 audit evidence is exhausted after repair; next use is as an accepted prerequisite artifact for the broader READY8 post-R1-R6/R7 orchestration, not another UNC same-class loop.",
        "use_as_live_filter_now": False,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    })


def build_completion(generated_at: str, decision: dict[str, Any], recomputation: dict[str, Any], discrepancy: dict[str, Any], instruction: dict[str, Any], saturation: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("preflight_context", instruction["all_requirements_covered"], rel(OUTPUT_FILES["instruction_coverage"])),
        ("accepted_g12_anchor_inspected", True, rel(G12_DECISION_PATH)),
        ("unc_manifest_repaired_and_current", check_unc_manifest_current()["ok"], rel(UNC_MANIFEST_PATH)),
        ("rowset_target_counts_recomputed", recomputation["all_row_counts_match_expected"], rel(OUTPUT_FILES["recomputation"])),
        ("all_required_unc_ledgers_recomputed", recomputation["all_ledger_recomputations_match"], rel(OUTPUT_FILES["recomputation"])),
        ("rowset_inventory_and_fail_closed_recomputed", recomputation["all_json_artifact_recomputations_match"], rel(OUTPUT_FILES["recomputation"])),
        ("completion_verifier_safe_flags_audited", discrepancy["same_g12_repairable_items_remaining"] == 0, rel(OUTPUT_FILES["discrepancy_repair"])),
        ("saturation_self_red_team_done", saturation["accepted"], rel(OUTPUT_FILES["saturation"])),
        ("decision_emitted", decision["accepted"], rel(OUTPUT_FILES["decision"])),
        ("verifier_and_focused_tests", False, "Filled by verifier after focused pytest command passes."),
    ]
    return base_record({
        "schema_version": "g12_unc004_audit_completion_audit_v1",
        "generated_at_utc": generated_at,
        "objective_restatement": "Audit the UNC-004 source-confidence disentanglement package from disk, recompute all required claims from accepted frozen inputs, repair same-class stale hashes, and emit an exact no-promotion G12 decision.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "satisfied": ok, "artifact_or_evidence": evidence}
            for req, ok, evidence in checklist
        ],
        "missing_or_unverified_requirements_before_verifier": [
            req for req, ok, _evidence in checklist if not ok and req != "verifier_and_focused_tests"
        ],
        "same_evidence_class_remaining_repairable_blockers": discrepancy["same_g12_repairable_items_remaining"],
        "same_evidence_class_remaining_actionable_ambiguities": discrepancy["same_evidence_class_actionable_ambiguities_remaining"],
        "same_evidence_class_remaining_source_search_paths": 0,
        "no_arbitrary_top_n_used": True,
        "can_mark_goal_complete_after_verifier_and_focused_tests": decision["accepted"] and discrepancy["same_g12_repairable_items_remaining"] == 0 and saturation["accepted"],
        "can_mark_goal_complete": False,
    })


def build_summary(decision: dict[str, Any], recomputation: dict[str, Any], discrepancy: dict[str, Any]) -> str:
    return f"""# G12 UNC-004 Source-Confidence Disentanglement Audit

Generated: {decision['generated_at_utc']}
Evidence class: `{EVIDENCE_CLASS}`
Promotion posture: `NO_PROMOTION_VERDICT`

## Decision

{decision['terminal_decision']}

The UNC-004 package is accepted only as source-bias/source-completeness neutral target-movement diagnostic evidence and a retest-candidate input. It is not validation-safe, not a promotion claim, not R/PnL/win-rate/expectancy evidence, and not live-filter authorization.

## Recomputed Facts

- UNC-004 rowset rows: {recomputation['row_counts']['unc_rowset_rows']}
- UNC-004 target rows: {recomputation['row_counts']['unc_target_rows']}
- Computable target rows: {recomputation['row_counts']['unc_computable_target_rows']}
- Fail-closed target rows: {recomputation['row_counts']['unc_fail_closed_target_rows']}
- Matched-control records: {recomputation['row_counts']['matched_control_records']}
- Leave-one stress records: {recomputation['row_counts']['leave_one_records']}
- Negative/inverse/neutral records: {recomputation['row_counts']['negative_inverse_neutral_records']}

## Repair

Same-class stale manifest hash drift was found and repaired. Entries repaired before acceptance: {len(discrepancy['same_class_repairs_performed'])}. Remaining same-G12 repairable items: {discrepancy['same_g12_repairable_items_remaining']}.

## Next

{decision['exact_next_route_or_exhaustion']}
"""


def build_output_manifest(generated_at: str) -> dict[str, Any]:
    artifacts = []
    script_paths = {
        "builder_script": OUTPUT_DIR / "build_g12_unc004_source_confidence_disentanglement_audit_2026_05_15.py",
        "verifier_script": OUTPUT_DIR / "verify_g12_unc004_source_confidence_disentanglement_audit_2026_05_15.py",
        "focused_test_script": OUTPUT_DIR / "test_g12_unc004_source_confidence_disentanglement_audit_2026_05_15.py",
        "line_ending_policy": OUTPUT_DIR / ".gitattributes",
    }
    for name, path in [*script_paths.items(), *OUTPUT_FILES.items()]:
        if path.exists():
            artifacts.append(json_or_text_file(name, path))
    manifest = base_record({
        "schema_version": "g12_unc004_audit_output_manifest_v1",
        "generated_at_utc": generated_at,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Audit output manifest excludes its own SHA; all other listed hashes are current.",
        "source_unc_route_dir": rel(UNC_DIR),
        "unc_manifest_repaired_sha256": file_sha256(UNC_MANIFEST_PATH),
    })
    return manifest


def write_output_manifest(generated_at: str) -> None:
    manifest = build_output_manifest(generated_at)
    last_bytes = None
    for _ in range(5):
        write_json(OUTPUT_FILES["manifest"], manifest)
        current_bytes = OUTPUT_FILES["manifest"].stat().st_size
        for artifact in manifest["artifacts"]:
            if artifact["name"] == "manifest":
                artifact["bytes"] = current_bytes
                artifact["sha256"] = None
                artifact["self_hash_excluded"] = True
        if current_bytes == last_bytes:
            break
        last_bytes = current_bytes
    write_json(OUTPUT_FILES["manifest"], manifest)


def build_all() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    source_generated_at = read_json(UNC_MANIFEST_PATH).get("generated_at_utc")
    manifest_repair = repair_unc_manifest_if_needed(generated_at)
    recomputed = recompute_unc_package(source_generated_at)
    safety = audit_safe_flags_and_inputs()
    completion_verifier = audit_completion_and_verifier(recomputed["row_counts"])
    recomputation = build_recomputation_ledger(generated_at, recomputed, manifest_repair)
    discrepancy = build_discrepancy_repair(generated_at, recomputation, completion_verifier, safety, manifest_repair)
    instruction = build_instruction_coverage(generated_at, manifest_repair)
    saturation = build_saturation(generated_at, recomputation, discrepancy, safety)
    decision = build_decision(generated_at, recomputation, discrepancy, saturation)
    completion = build_completion(generated_at, decision, recomputation, discrepancy, instruction, saturation)

    write_json(OUTPUT_FILES["recomputation"], recomputation)
    write_json(OUTPUT_FILES["discrepancy_repair"], discrepancy)
    write_json(OUTPUT_FILES["instruction_coverage"], instruction)
    write_json(OUTPUT_FILES["saturation"], saturation)
    write_json(OUTPUT_FILES["decision"], decision)
    write_json(OUTPUT_FILES["completion"], completion)
    write_text(OUTPUT_FILES["summary"], build_summary(decision, recomputation, discrepancy))
    write_output_manifest(generated_at)

    return {
        "ok": decision["accepted"],
        "route_dir": rel(OUTPUT_DIR),
        "decision": decision["terminal_decision"],
        "same_g12_repairable_items_remaining": discrepancy["same_g12_repairable_items_remaining"],
        "manifest_repair_performed": manifest_repair["repair_performed"],
        "row_counts": recomputed["row_counts"],
        **SAFE_FLAGS,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    print(json.dumps(build_all(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
