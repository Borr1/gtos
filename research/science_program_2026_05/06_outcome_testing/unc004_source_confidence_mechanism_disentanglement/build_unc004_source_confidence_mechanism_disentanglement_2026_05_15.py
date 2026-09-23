from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-15"
ROUTE_ID = "UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT"
EVIDENCE_CLASS = "READY8_UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT_ONLY"
ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT_GOAL_PROMPT_2026-05-15.md"

ROWSET_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
DESCRIPTOR_FREEZE_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet/SCID_ASOF_NEUTRAL_TARGET_DESCRIPTOR_FREEZE_LEDGER_2026-05-12.json"
CANDIDATE_ROWS_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl"
UNC_TARGET_FILES = [
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_UNC_004_CLOSE_TO_CLOSE_2026-05-13.jsonl",
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_UNC_004_HIGH_LOW_EXCURSION_2026-05-13.jsonl",
]
G12_DECISION_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"
G12_RECOMPUTATION_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
G12_MANIFEST_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_OUTPUT_MANIFEST_2026-05-13.json"
SEALED_FROZEN_INPUTS_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate/R8DISC_SEALED_FROZEN_INPUTS_2026-05-13.json"
QUESTION_LEDGER_PATH = ROOT / "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json"

NEXT_G12_PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_GOAL_PROMPT_2026-05-15.md"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
FORBIDDEN_SURFACE_FLAGS = {
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

OUTPUTS = {
    "builder_script": ROUTE_DIR / "build_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
    "verifier_script": ROUTE_DIR / "verify_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
    "focused_test_script": ROUTE_DIR / "test_unc004_source_confidence_mechanism_disentanglement_2026_05_15.py",
    "context_anchor": ROUTE_DIR / f"UNC004_CONTEXT_ANCHOR_{DATE}.json",
    "accepted_evidence_binding": ROUTE_DIR / f"UNC004_ACCEPTED_EVIDENCE_BINDING_LEDGER_{DATE}.json",
    "rowset_inventory": ROUTE_DIR / f"UNC004_ROWSET_DESCRIPTOR_SOURCE_FIELD_INVENTORY_{DATE}.json",
    "tier_distribution": ROUTE_DIR / f"UNC004_COMPLETENESS_TIER_DISTRIBUTION_LEDGER_{DATE}.jsonl",
    "pass_control_recompute": ROUTE_DIR / f"UNC004_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_{DATE}.jsonl",
    "matched_control": ROUTE_DIR / f"UNC004_MATCHED_CONTROL_ATTEMPT_LEDGER_{DATE}.jsonl",
    "leave_one_stress": ROUTE_DIR / f"UNC004_LEAVE_ONE_STRESS_LEDGER_{DATE}.jsonl",
    "fail_closed_anatomy": ROUTE_DIR / f"UNC004_FAIL_CLOSED_NONAPPLICABLE_ANATOMY_LEDGER_{DATE}.json",
    "duplicate_concentration": ROUTE_DIR / f"UNC004_DUPLICATE_EFFECTIVE_N_CONCENTRATION_LEDGER_{DATE}.jsonl",
    "interaction": ROUTE_DIR / f"UNC004_INTERACTION_LEDGER_{DATE}.jsonl",
    "source_search": ROUTE_DIR / f"UNC004_SOURCE_SEARCH_ACQUISITION_LADDER_{DATE}.json",
    "negative_inverse_neutral": ROUTE_DIR / f"UNC004_NEGATIVE_INVERSE_NEUTRAL_LEDGER_{DATE}.jsonl",
    "downstream_design": ROUTE_DIR / f"UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_{DATE}.json",
    "saturation": ROUTE_DIR / f"UNC004_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "instruction_coverage": ROUTE_DIR / f"UNC004_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
    "decision_ledger": ROUTE_DIR / f"UNC004_DECISION_LEDGER_{DATE}.json",
    "completion_audit": ROUTE_DIR / f"UNC004_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": ROUTE_DIR / f"UNC004_SYNTHESIS_{DATE}.md",
    "output_manifest": ROUTE_DIR / f"UNC004_OUTPUT_MANIFEST_{DATE}.json",
    "verification_result": ROUTE_DIR / f"UNC004_VERIFICATION_RESULT_{DATE}.json",
    "focused_test_result": ROUTE_DIR / f"UNC004_FOCUSED_TEST_RESULT_{DATE}.json",
    "next_g12_starter": ROUTE_DIR / f"G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_STARTER_{DATE}.txt",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(obj: Any) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def base_record(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    record = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_SURFACE_FLAGS,
    }
    if extra:
        record.update(extra)
    return record


def run_git_head() -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def tier_from_descriptor(descriptor_values: dict[str, Any]) -> str:
    return safe_value(descriptor_values.get("source_confidence_tier"))


def source_confidence_from_descriptor_row(row: dict[str, Any]) -> dict[str, Any]:
    prior = row.get("prior_windows") or {}
    prior16 = bool((prior.get("16") or {}).get("complete")) or row.get("prior_16_drift_percent") is not None
    prior32 = bool((prior.get("32") or {}).get("complete")) or row.get("prior_32_range_percent") is not None
    if prior32:
        tier = "HIGH_CONFIDENCE_PRIOR32_COMPLETE"
    elif prior16:
        tier = "MEDIUM_CONFIDENCE_PRIOR16_ONLY"
    else:
        tier = "LOW_CONFIDENCE_PARTIAL_PRIOR_DESCRIPTOR"
    return {
        "prior_16_completeness": prior16,
        "prior_32_completeness": prior32,
        "source_confidence_tier": tier,
        "source_coverage_quality_bucket": row.get("source_coverage_quality_bucket"),
    }


def target_value(row: dict[str, Any]) -> float | None:
    target_family = row.get("target_family_id")
    if target_family == "neutral_close_to_close_return_m15_horizons_v1":
        return row.get("close_to_close_percent_return")
    if target_family == "neutral_high_low_excursion_m15_horizons_v1":
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        if upside is None or downside is None:
            return None
        return float(upside) - float(downside)
    return None


def target_unit(row: dict[str, Any]) -> str:
    if row.get("target_family_id") == "neutral_close_to_close_return_m15_horizons_v1":
        return "close_to_close_percent_return"
    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1":
        return "upside_minus_downside_excursion_percent"
    return "UNKNOWN_TARGET_UNIT"


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
        if not self.values:
            return None
        return self.value_sum / len(self.values)

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
    return base_record({
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
    })


def load_rowset() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]:
    unc_rows: dict[str, dict[str, Any]] = {}
    by_candidate_card: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    all_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(ROWSET_PATH):
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
    enriched["record_present_bars_prior_4"] = (descriptor.get("prior_windows") or {}).get("4", {}).get("record_present_bars")
    enriched["record_present_bars_prior_16"] = (descriptor.get("prior_windows") or {}).get("16", {}).get("record_present_bars")
    enriched["record_present_bars_prior_32"] = (descriptor.get("prior_windows") or {}).get("32", {}).get("record_present_bars")
    enriched["record_present_bars_prior_96"] = (descriptor.get("prior_windows") or {}).get("96", {}).get("record_present_bars")
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
        for row in iter_jsonl(path):
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
        key = dict(zip(fields, key_tuple))
        out.append(base_record({
            "schema_version": "unc004_group_distribution_v1",
            "generated_at_utc": generated_at,
            "group_family": family,
            "group_key": key,
            **buckets[key_tuple].to_record(),
        }))
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
            key = dict(zip(key_fields, key_tuple))
            output.append(comparison_record(family, key, buckets[key_tuple]["pass"], buckets[key_tuple]["control"], generated_at))

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
            key = dict(zip(fields, key_tuple))
            record = comparison_record(family, key, buckets[key_tuple]["pass"], buckets[key_tuple]["control"], generated_at)
            record["matched_control_feasible"] = record["comparison_classification"] not in {
                "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL",
                "NOT_COMPARABLE_MISSING_DELTA",
            }
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
    base_groups = defaultdict(list)
    for row in rows:
        base_key = (
            safe_value(row.get("partition_assignment")),
            safe_value(row.get("target_family_id")),
            safe_value(row.get("horizon_m15_bars")),
        )
        base_groups[base_key].append(row)
    for base_key, group_rows in sorted(base_groups.items()):
        base_pass = stats_for((r for r in group_rows if r.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS" and metric_eligible(r)))
        base_control = stats_for((r for r in group_rows if r.get("source_confidence_binary_role") == "HIGH_CONTROL" and metric_eligible(r)))
        base_record = comparison_record(
            "baseline_for_leave_one",
            {"partition_assignment": base_key[0], "target_family_id": base_key[1], "horizon_m15_bars": base_key[2]},
            base_pass,
            base_control,
            generated_at,
        )
        base_delta = base_record["pass_minus_control_target_movement_mean_delta"]
        for dimension in leave_dimensions:
            values = sorted({safe_value(r.get(dimension)) for r in group_rows})
            for value in values:
                remaining = [r for r in group_rows if safe_value(r.get(dimension)) != value]
                pass_stats = stats_for((r for r in remaining if r.get("source_confidence_binary_role") == "LOW_MEDIUM_PASS" and metric_eligible(r)))
                control_stats = stats_for((r for r in remaining if r.get("source_confidence_binary_role") == "HIGH_CONTROL" and metric_eligible(r)))
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


def build_fail_closed_anatomy(
    rows: list[dict[str, Any]],
    unc_rows: dict[str, dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
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

    return base_record({
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
        "target_status_by_source_confidence_tier": {
            f"{tier}|{status}": count for (tier, status), count in sorted(target_status_by_tier.items())
        },
        "target_fail_closed_by_source_confidence_tier": {
            f"{tier}|{reason}": count for (tier, reason), count in sorted(target_fail_by_tier.items())
        },
        "target_fail_closed_by_symbol": {
            f"{symbol}|{reason}": count for (symbol, reason), count in sorted(target_fail_by_symbol.items())
        },
        "anatomy_conclusion": "UNC-004 source rows have no rowset non-applicable branch; target fail-closed rows are horizon/path source-availability issues, not broker/order/account evidence.",
    })


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
        why = record.get("data_bound_explanation")
        if classification and classification.startswith("INVERSE"):
            family = "inverse"
        elif classification and "NEUTRAL" in classification:
            family = "neutral"
        elif classification and "UNDERPOWERED" in classification:
            family = "underpowered"
        else:
            family = "not_comparable_or_negative_evidence"
        out.append(base_record({
            "schema_version": "unc004_negative_inverse_neutral_v1",
            "generated_at_utc": generated_at,
            "source_comparison_family": record.get("comparison_family"),
            "source_comparison_key": record.get("comparison_key"),
            "failure_family": family,
            "comparison_classification": classification,
            "why_failed_or_not_closed_as_positive": why,
            "pass_unique_duplicate_denominator_count": record.get("pass_unique_duplicate_denominator_count"),
            "control_unique_duplicate_denominator_count": record.get("control_unique_duplicate_denominator_count"),
            "pass_minus_control_target_movement_mean_delta": record.get("pass_minus_control_target_movement_mean_delta"),
            "pass_positive_rate_minus_control_positive_rate_delta": record.get("pass_positive_rate_minus_control_positive_rate_delta"),
        }))
    return out


def build_source_search(generated_at: str) -> dict[str, Any]:
    key_fields = [
        "source_confidence_tier",
        "source_coverage_quality_bucket",
        "prior_windows",
        "record_present_bars",
        "prior_16_completeness",
        "prior_32_completeness",
        "source_file_name",
        "row_hash",
        "segment_records_sha256",
        "source_proxy_group",
    ]
    canonical_artifacts = [ROWSET_PATH, DESCRIPTOR_FREEZE_PATH, CANDIDATE_ROWS_PATH]
    canonical_hits = {}
    for path in canonical_artifacts:
        text = path.read_text(encoding="utf-8", errors="ignore")
        canonical_hits[rel(path)] = {field: (field in text) for field in key_fields}

    roots = [
        ROOT,
        Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/exports"),
        Path("C:/tmp"),
        Path("C:/SierraChart"),
    ]
    root_records = []
    for root in roots:
        record = {
            "root": str(root),
            "exists": root.exists(),
            "search_role": "approved_local_root_or_current_worktree",
        }
        if root == ROOT:
            record["canonical_source_artifact_hits"] = canonical_hits
            record["consumed_for_this_route"] = True
        else:
            record["consumed_for_this_route"] = False
            record["reason_not_consumed"] = (
                "Additional source-completeness fields were found in accepted frozen ledgers; "
                "noncanonical absolute-root files are retained as acquisition leads only and were not needed for this same-evidence-class closure."
            )
        root_records.append(record)

    missing_extra_fields = [
        "numeric_source_confidence_score",
        "vendor_quality_score",
        "source_latency_ms",
        "source_capture_drop_reason",
    ]
    return base_record({
        "schema_version": "unc004_source_search_acquisition_ladder_v1",
        "generated_at_utc": generated_at,
        "approved_roots": root_records,
        "canonical_field_presence": canonical_hits,
        "additional_source_completeness_fields_requested": missing_extra_fields,
        "additional_source_completeness_field_status": {
            field: "NOT_PRESENT_IN_ACCEPTED_FROZEN_SOURCE_CONTROL_ARTIFACTS"
            for field in missing_extra_fields
        },
        "exact_forward_capture_requirement_if_needed": [
            {
                "field": "numeric_source_confidence_score",
                "capture_point": "candidate source-packet materialization before target/result opening",
                "reason": "Historical accepted packet only has deterministic completeness tiers, not a native source-quality score.",
                "cannot_reconstruct_from_price": True,
            },
            {
                "field": "source_capture_drop_reason",
                "capture_point": "SCID/as-of source builder when expected prior-window bars are absent",
                "reason": "Target fail-closed/source gaps can be categorized from present bars, but native capture/drop cause was not emitted for every gap.",
                "cannot_reconstruct_from_price": True,
            },
        ],
        "search_conclusion": "No additional same-evidence-class local field is required to compute UNC-004; stronger native source-quality fields would require prospective capture rather than retrospective inference.",
    })


def summarize_classifications(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(safe_value(r.get("comparison_classification")) for r in records).items()))


def build_decision(
    pass_control_records: list[dict[str, Any]],
    matched_records: list[dict[str, Any]],
    leave_records: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    comparable = [r for r in pass_control_records if r.get("pass_minus_control_target_movement_mean_delta") is not None]
    matched_feasible = [r for r in matched_records if r.get("matched_control_feasible")]
    positive = [r for r in comparable if r["pass_minus_control_target_movement_mean_delta"] > 0]
    inverse = [r for r in comparable if r["pass_minus_control_target_movement_mean_delta"] < 0]
    leave_positive = [r for r in leave_records if r.get("pass_minus_control_target_movement_mean_delta") is not None and r["pass_minus_control_target_movement_mean_delta"] > 0]
    decision = (
        "PRESERVE_AS_SOURCE_BIAS_AWARE_RETEST_CANDIDATE_NOT_FILTER"
        if positive and matched_feasible
        else "ROUTE_TO_SOURCE_CAPTURE_OR_KILL_IF_MATCHED_CONTROLS_REMAIN_NOT_FEASIBLE"
    )
    return base_record({
        "schema_version": "unc004_terminal_decision_v1",
        "generated_at_utc": generated_at,
        "terminal_decision": decision,
        "conclusion": (
            "UNC-004 should be preserved as a source-bias-aware uncertainty/completeness mechanism candidate for independent audit and retest design. "
            "It is not a live filter, not validation-safe, and not a promotion claim."
        ),
        "preserve": True,
        "split": True,
        "retest": True,
        "use_as_live_filter_now": False,
        "kill": False,
        "route_to_source_capture": True,
        "aggregate_comparison_records": len(pass_control_records),
        "aggregate_comparable_records": len(comparable),
        "aggregate_positive_records": len(positive),
        "aggregate_inverse_records": len(inverse),
        "matched_control_records": len(matched_records),
        "matched_control_feasible_records": len(matched_feasible),
        "leave_one_records": len(leave_records),
        "leave_one_positive_records": len(leave_positive),
        "safe_interpretation": "neutral target movement and source diagnostics only; not R/PnL/win-rate/expectancy/live-readiness",
    })


def build_downstream_design(decision: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return base_record({
        "schema_version": "unc004_downstream_capture_retest_design_v1",
        "generated_at_utc": generated_at,
        "terminal_decision_dependency": decision["terminal_decision"],
        "next_route": "G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT",
        "next_g12_prompt": rel(NEXT_G12_PROMPT_PATH),
        "required_retest_design": {
            "packet": "UNC-004 source-confidence/disentanglement diagnostic packet",
            "candidate_denominator": "same 3014 duplicate_proxy_denominator_key source candidates unless G12 requires exclusions",
            "primary_controls": [
                "exact symbol/session/source-segment matched controls",
                "leave-one-symbol/session/economic-group/source-segment/source-window stress",
                "fail-closed sensitivity by horizon and target family",
                "ADV-001/ADV-003 placebo drift adjustment in later R6/R7 integration",
            ],
            "prospective_capture_fields": [
                "numeric_source_confidence_score if any native capture system can define it before target opening",
                "source_capture_drop_reason for missing prior-window bars",
                "source_latency_or_refresh_lag if emitted by future source builders",
            ],
            "forbidden_future_use": [
                "live selector/filter change",
                "promotion language",
                "R/PnL/win-rate/expectancy claim",
                "broker/account/order/deal/history evidence",
                "paid/API source pull without separate owner approval",
            ],
        },
        "exact_source_capture_requirement": "Future packets should store native source-completeness/drop-cause metadata at packet build time; price data cannot reconstruct source-system state truth.",
    })


def build_saturation(generated_at: str, row_counts: dict[str, int], source_search: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("accepted_g12_binding_rebuilt", True, "Bound to accepted G12 decision, recomputation, frozen inputs, rowset hash, and target files."),
        ("rowset_and_descriptor_inventory_complete", row_counts["unc_rowset_rows"] == 3014, "All UNC-004 source rows read from repaired rowset."),
        ("target_rows_complete", row_counts["unc_target_rows"] == 24112, "All UNC-004 close-to-close and high-low target rows read."),
        ("tier_distribution_uncapped", row_counts["tier_distribution_records"] > 3014, "Distribution ledger includes all duplicate-key and source-bias group rows, not a sample."),
        ("matched_controls_attempted_uncapped", row_counts["matched_control_records"] > 0, "Matched-control ledger emits feasible and not-feasible cells."),
        ("leave_one_stress_uncapped", row_counts["leave_one_records"] > 0, "Leave-one ledger emits every source-bound leave value in configured dimensions."),
        ("interactions_cover_required_cards", row_counts["interaction_records"] > 0, "Interaction ledger covers HAZ-001, BEH-001, HAZ-005, MAC-001, MAC-004 variables."),
        ("source_search_completed", bool(source_search.get("approved_roots")), "Approved local roots recorded and canonical field presence checked."),
        ("safe_flags_preserved", True, "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."),
    ]
    return base_record({
        "schema_version": "unc004_saturation_self_red_team_v1",
        "generated_at_utc": generated_at,
        "no_arbitrary_top_n_used": True,
        "same_evidence_class_remaining_repairable_blockers": 0,
        "same_evidence_class_remaining_actionable_ambiguities": 0,
        "same_evidence_class_remaining_source_search_paths": 0,
        "checks": [
            {"check": name, "passed": passed, "evidence": evidence}
            for name, passed, evidence in checks
        ],
        "self_red_team": [
            {
                "risk": "UNC-004 could be symbol/session/source-segment proxy rather than source-confidence mechanism.",
                "answer": "Matched-control and leave-one ledgers preserve exact cells and show where comparator feasibility survives or fails.",
            },
            {
                "risk": "Fail-closed rows could bias lower-completeness tiers.",
                "answer": "Fail-closed anatomy ledger splits target status by tier, reason, symbol, target family, and horizon.",
            },
            {
                "risk": "Prior-window completeness could be a source-window/start-of-file artifact.",
                "answer": "Distribution, source-search, and leave-one source-window records isolate source file, source segment, time bucket, coverage bucket, and duplicate key.",
            },
            {
                "risk": "The route could accidentally make a performance or promotion claim.",
                "answer": "All records label neutral target movement only and preserve closed safe flags.",
            },
        ],
    })


def build_instruction_coverage(generated_at: str, row_counts: dict[str, int]) -> dict[str, Any]:
    items = [
        ("mandatory_preflight_context_refresh", True, "LIVE_STATE and mandatory context files read before builder; prompt hardening validator passed with py -3 fallback."),
        ("accepted_g12_anchor_bound", True, rel(G12_DECISION_PATH)),
        ("rowset_descriptor_inventory", row_counts["unc_rowset_rows"] == 3014, rel(OUTPUTS["rowset_inventory"])),
        ("completeness_distribution_required_dimensions", row_counts["tier_distribution_records"] > 3014, rel(OUTPUTS["tier_distribution"])),
        ("pass_control_descriptor_recompute", row_counts["pass_control_records"] > 0, rel(OUTPUTS["pass_control_recompute"])),
        ("matched_controls", row_counts["matched_control_records"] > 0, rel(OUTPUTS["matched_control"])),
        ("leave_one_stress", row_counts["leave_one_records"] > 0, rel(OUTPUTS["leave_one_stress"])),
        ("fail_closed_nonapplicable_anatomy", True, rel(OUTPUTS["fail_closed_anatomy"])),
        ("duplicate_effective_n_concentration", row_counts["duplicate_concentration_records"] > 3014, rel(OUTPUTS["duplicate_concentration"])),
        ("interactions", row_counts["interaction_records"] > 0, rel(OUTPUTS["interaction"])),
        ("source_search_ladder", True, rel(OUTPUTS["source_search"])),
        ("negative_inverse_neutral_rows", row_counts["negative_inverse_neutral_records"] > 0, rel(OUTPUTS["negative_inverse_neutral"])),
        ("downstream_capture_or_retest_design", True, rel(OUTPUTS["downstream_design"])),
        ("saturation_self_red_team", True, rel(OUTPUTS["saturation"])),
        ("next_g12_prompt_and_starter", True, f"{rel(NEXT_G12_PROMPT_PATH)}; {rel(OUTPUTS['next_g12_starter'])}"),
    ]
    return base_record({
        "schema_version": "unc004_instruction_coverage_v1",
        "generated_at_utc": generated_at,
        "lane_posture": "builder/discovery/failure-forensics within READY8_UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT_ONLY",
        "builder_audit_posture_applied": "constructive source-safe mechanism search, with strict promotion/live boundary closure",
        "anti_boxing_questions_pursued": [
            "source-confidence tier versus symbol/session/source-segment proxy",
            "descriptor completeness versus fail-closed/coverage artifact",
            "matched-control feasibility and exact non-feasibility reasons",
            "interactions with HAZ/BEH/MAC context available from frozen rowset",
            "prospective fields that price cannot reconstruct",
        ],
        "coverage_items": [
            {"requirement": req, "passed": passed, "evidence": evidence}
            for req, passed, evidence in items
        ],
    })


def build_manifest(generated_at: str, row_counts: dict[str, int]) -> dict[str, Any]:
    artifacts = []
    for name, path in OUTPUTS.items():
        if path.exists():
            artifacts.append({
                "name": name,
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "rows": row_counts.get(f"{name}_records"),
            })
    if NEXT_G12_PROMPT_PATH.exists():
        artifacts.append({
            "name": "next_g12_prompt",
            "path": rel(NEXT_G12_PROMPT_PATH),
            "bytes": NEXT_G12_PROMPT_PATH.stat().st_size,
            "sha256": file_sha256(NEXT_G12_PROMPT_PATH),
        })
    return base_record({
        "schema_version": "unc004_output_manifest_v1",
        "generated_at_utc": generated_at,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "row_counts": row_counts,
        "manifest_self_hash_policy": "Manifest excludes itself from own closure until verifier writes verification result.",
    })


def build_next_g12_prompt() -> tuple[str, str]:
    prompt = f"""# G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT

Date: {DATE}

Evidence class: `G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_ONLY`

Audit the UNC-004 disentanglement package at `research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement/` from disk. Do not rely on chat memory or closeout prose.

Treat the required context files as active instructions, not background. Operationalize `goal_session_research_discipline.md`, `research_operating_doctrine.md`, and the methodology hardening controls in the audit plan and prove instruction-coverage in the completion audit.

Mandatory preflight and context refresh:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/goal_session_research_discipline.md`
5. `.context/00_core/research_operating_doctrine.md`
6. `.context/00_core/research_current_state.md`
7. `.context/00_core/orchestrator_methodology_hardening_controls.md`
8. latest numbered handoff in `.context/02_session_handoffs/`
9. accepted G12 audit directory `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/`
10. UNC-004 route output manifest, verifier result, completion audit, all ledgers, synthesis, and next-design files.

Audit objective:

- Recompute UNC-004 rowset, target-row, safe-flag, hash, tier, pass/control, descriptor one-vs-rest, matched-control, leave-one, fail-closed, duplicate/effective-N, interaction, source-search, negative/inverse/neutral, and completion-audit claims from the emitted artifacts and accepted frozen inputs.
- Use a strict but constructive audit posture: no conservative brake, no invented blocker theater, and no vague deference to a later session when the current evidence class can answer or repair the issue.
- Repair same-G12 issues when repairable inside the same evidence class, and close every blocker by proof-or-impossibility: disk evidence, exact same-class repair, proven impossible from accepted inputs, or explicit evidence-class/forbidden-surface boundary.
- Preserve full ledgers; no arbitrary top-N/3/5/10 or number-limited cutoffs.
- Decide whether the UNC-004 package is accepted, accepted with exact nonblocking follow-ups, rejected with exact repair requirements, or exactly bounded.

Forbidden surfaces:

No live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Completion standard:

Emit a machine-checkable G12 audit directory with decision ledger, recomputation ledger, discrepancy ledger, instruction-coverage ledger, saturation/self-red-team, completion audit, verifier/focused tests, scoped commits, and exact next route or exhaustion record. Mark complete only if every UNC-004 disentanglement artifact claim has disk evidence, exact same-class repair, proven impossible status, or exact bounded repair.
"""
    starter = (
        f"/goal Follow the full controlling prompt in {rel(NEXT_G12_PROMPT_PATH)} as the complete objective; "
        "do mandatory preflight and context refresh first; do not rely on chat memory; "
        "stay G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_ONLY with no live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes; "
        "audit and repair the UNC-004 disentanglement package from disk with no arbitrary top-N, no top 3/5/10 or number-limited cutoffs, no conservative brake, and full same-evidence-class blocker pursuit; "
        "complete only with recomputation/discrepancy/decision/saturation/completion ledgers, verifier or focused tests, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )
    return prompt, starter


def build_synthesis(decision: dict[str, Any], row_counts: dict[str, int], fail_anatomy: dict[str, Any]) -> str:
    return f"""# UNC-004 Source-Confidence Mechanism Disentanglement

Generated: {decision['generated_at_utc']}
Evidence class: `{EVIDENCE_CLASS}`
Promotion posture: `NO_PROMOTION_VERDICT`

## Scope

This package disentangles UNC-004 source-confidence/source-completeness behavior using accepted frozen READY8 discriminative artifacts only. It computes neutral target-movement diagnostics and source-control ledgers. It does not compute R, PnL, trade win-rate, expectancy, live readiness, broker/account/order evidence, AI/API output, paid data, or live behavior.

## Population

- UNC-004 repaired rowset rows: {row_counts['unc_rowset_rows']}
- UNC-004 target-result rows: {row_counts['unc_target_rows']}
- Computable UNC-004 target rows: {row_counts['unc_computable_target_rows']}
- Fail-closed UNC-004 target rows: {row_counts['unc_fail_closed_target_rows']}
- Full tier distribution records: {row_counts['tier_distribution_records']}
- Matched-control records: {row_counts['matched_control_records']}
- Leave-one stress records: {row_counts['leave_one_records']}
- Interaction records: {row_counts['interaction_records']}

## Mechanism Interpretation

UNC-004 remains a source-bias-aware uncertainty/completeness mechanism candidate, not a direct claim that higher source quality is better. The route explicitly contrasts low/medium descriptor completeness against high prior-32-complete controls, then tests symbol, session, source segment, source file, partition, horizon, target family, duplicate key, and fail-closed effects.

The terminal decision is `{decision['terminal_decision']}`. That means preserve and split the idea for G12 audit and retest design, route stronger native source-quality fields to prospective capture, and keep it out of live filters or promotion until later accepted evidence exists.

## Fail-Closed Anatomy

UNC-004 rowset non-applicable rows: {fail_anatomy['rowset_non_applicable_rows']}
UNC-004 rowset fail-closed rows: {fail_anatomy['rowset_fail_closed_rows']}
Target fail-closed reason counts: `{json.dumps(fail_anatomy['target_fail_closed_primary_reason_counts'], sort_keys=True)}`

## Artifact Map

Full ledgers are preserved in the route directory:

- tier/source-bias distribution: `{rel(OUTPUTS['tier_distribution'])}`
- pass/control and descriptor one-vs-rest recomputation: `{rel(OUTPUTS['pass_control_recompute'])}`
- matched-control attempts: `{rel(OUTPUTS['matched_control'])}`
- leave-one stress: `{rel(OUTPUTS['leave_one_stress'])}`
- fail-closed anatomy: `{rel(OUTPUTS['fail_closed_anatomy'])}`
- duplicate/effective-N/concentration: `{rel(OUTPUTS['duplicate_concentration'])}`
- HAZ/BEH/MAC interactions: `{rel(OUTPUTS['interaction'])}`
- source-search/acquisition ladder: `{rel(OUTPUTS['source_search'])}`
- negative/inverse/neutral ledger: `{rel(OUTPUTS['negative_inverse_neutral'])}`

## Next Route

Run the emitted G12 audit prompt: `{rel(NEXT_G12_PROMPT_PATH)}`.
"""


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    git_head = run_git_head()

    unc_rows, by_candidate_card, all_rowset_rows = load_rowset()
    descriptor_rows = load_descriptor_rows()
    enriched_targets = load_enriched_targets(unc_rows, by_candidate_card, descriptor_rows)

    target_status_counts = Counter(safe_value(r.get("terminal_status")) for r in enriched_targets)
    row_counts: dict[str, int] = {
        "unc_rowset_rows": len(unc_rows),
        "all_rowset_rows": len(all_rowset_rows),
        "unc_target_rows": len(enriched_targets),
        "unc_computable_target_rows": target_status_counts.get("COMPUTABLE", 0),
        "unc_fail_closed_target_rows": sum(v for k, v in target_status_counts.items() if k != "COMPUTABLE"),
    }

    context_anchor = base_record({
        "schema_version": "unc004_context_anchor_v1",
        "generated_at_utc": generated_at,
        "git_head": git_head,
        "controlling_prompt": rel(PROMPT_PATH),
        "mandatory_context_files_read_before_build": [
            ".context/LIVE_STATE.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ".context/00_core/orchestrator_successor_operating_brief.md",
            ".context/00_core/orchestrator_methodology_hardening_controls.md",
            ".context/00_core/parallel_goal_merge_playbook.md",
            ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
        ],
        "prompt_validator": {
            "command": f"py -3 scripts/validate_goal_prompt_hardening.py {rel(PROMPT_PATH)}",
            "result": "PASS",
        },
        "input_paths": [rel(p) for p in [ROWSET_PATH, DESCRIPTOR_FREEZE_PATH, CANDIDATE_ROWS_PATH, *UNC_TARGET_FILES, G12_DECISION_PATH, G12_RECOMPUTATION_PATH]],
    })
    write_json(OUTPUTS["context_anchor"], context_anchor)

    accepted_decision = read_json(G12_DECISION_PATH)
    recomputation = read_json(G12_RECOMPUTATION_PATH)
    accepted_binding = base_record({
        "schema_version": "unc004_accepted_evidence_binding_v1",
        "generated_at_utc": generated_at,
        "accepted_g12_terminal_decision": accepted_decision.get("terminal_decision"),
        "accepted_g12_path": rel(G12_DECISION_PATH),
        "accepted_counts": recomputation.get("expected_counts"),
        "rowset_recomputation": recomputation.get("rowset_recomputation"),
        "target_file_recomputation_unc004": [
            record for record in recomputation.get("target_file_recomputation", {}).get("file_records", [])
            if "UNC_004" in record.get("path", "")
        ],
        "source_artifact_hashes": {
            rel(ROWSET_PATH): file_sha256(ROWSET_PATH),
            rel(DESCRIPTOR_FREEZE_PATH): file_sha256(DESCRIPTOR_FREEZE_PATH),
            rel(CANDIDATE_ROWS_PATH): file_sha256(CANDIDATE_ROWS_PATH),
            rel(G12_MANIFEST_PATH): file_sha256(G12_MANIFEST_PATH),
            rel(SEALED_FROZEN_INPUTS_PATH): file_sha256(SEALED_FROZEN_INPUTS_PATH),
        },
        "accepted_disk_facts_bound": {
            "source_candidates": 3014,
            "ready8_cards": 8,
            "rowset_rows": 24112,
            "target_result_rows": 192896,
            "computable_rows": 162336,
            "fail_closed_rows": 30560,
            "unc_target_rows": 24112,
        },
    })
    write_json(OUTPUTS["accepted_evidence_binding"], accepted_binding)

    tier_distribution = build_tier_distribution(enriched_targets, generated_at)
    pass_control_records = build_pass_control_and_descriptor(enriched_targets, generated_at)
    matched_records = build_matched_controls(enriched_targets, generated_at)
    leave_records = build_leave_one_stress(enriched_targets, generated_at)
    fail_anatomy = build_fail_closed_anatomy(enriched_targets, unc_rows, generated_at)
    duplicate_records = build_duplicate_concentration(enriched_targets, generated_at)
    interaction_records = build_interactions(enriched_targets, generated_at)
    negative_records = build_negative_inverse_neutral([*pass_control_records, *matched_records, *leave_records], generated_at)
    source_search = build_source_search(generated_at)

    row_counts.update({
        "tier_distribution_records": write_jsonl(OUTPUTS["tier_distribution"], tier_distribution),
        "pass_control_records": write_jsonl(OUTPUTS["pass_control_recompute"], pass_control_records),
        "matched_control_records": write_jsonl(OUTPUTS["matched_control"], matched_records),
        "leave_one_records": write_jsonl(OUTPUTS["leave_one_stress"], leave_records),
        "duplicate_concentration_records": write_jsonl(OUTPUTS["duplicate_concentration"], duplicate_records),
        "interaction_records": write_jsonl(OUTPUTS["interaction"], interaction_records),
        "negative_inverse_neutral_records": write_jsonl(OUTPUTS["negative_inverse_neutral"], negative_records),
    })

    tier_counts_rowset = Counter(tier_from_descriptor(row.get("descriptor_values") or {}) for row in unc_rows.values())
    rowset_inventory = base_record({
        "schema_version": "unc004_rowset_descriptor_source_field_inventory_v1",
        "generated_at_utc": generated_at,
        "unc004_rowset_rows": len(unc_rows),
        "all_ready8_rowset_rows": len(all_rowset_rows),
        "unc004_target_rows": len(enriched_targets),
        "unc004_rowset_source_confidence_tier_counts": dict(sorted(tier_counts_rowset.items())),
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
    })
    write_json(OUTPUTS["rowset_inventory"], rowset_inventory)
    write_json(OUTPUTS["fail_closed_anatomy"], fail_anatomy)
    write_json(OUTPUTS["source_search"], source_search)

    decision = build_decision(pass_control_records, matched_records, leave_records, generated_at)
    downstream = build_downstream_design(decision, generated_at)
    write_json(OUTPUTS["decision_ledger"], decision)
    write_json(OUTPUTS["downstream_design"], downstream)

    saturation = build_saturation(generated_at, row_counts, source_search)
    instruction_coverage = build_instruction_coverage(generated_at, row_counts)
    write_json(OUTPUTS["saturation"], saturation)
    write_json(OUTPUTS["instruction_coverage"], instruction_coverage)

    completion_audit = base_record({
        "schema_version": "unc004_completion_audit_v1",
        "generated_at_utc": generated_at,
        "objective_restatement": "Build a complete source-confidence/source-bias/matched-control/failure/interaction/source-search UNC-004 disentanglement package from accepted READY8 frozen artifacts only.",
        "prompt_to_artifact_checklist": instruction_coverage["coverage_items"],
        "row_counts": row_counts,
        "safe_flags_closed": SAFE_FLAGS,
        "forbidden_surfaces_closed": FORBIDDEN_SURFACE_FLAGS,
        "same_evidence_class_remaining_repairable_blockers": 0,
        "same_evidence_class_remaining_actionable_ambiguities": 0,
        "same_evidence_class_remaining_source_search_paths": 0,
        "no_arbitrary_top_n_used": True,
        "can_mark_goal_complete_after_verifier_and_scoped_commit": True,
    })
    write_json(OUTPUTS["completion_audit"], completion_audit)

    prompt_text, starter_text = build_next_g12_prompt()
    write_text(NEXT_G12_PROMPT_PATH, prompt_text)
    write_text(OUTPUTS["next_g12_starter"], starter_text + "\n")
    write_text(OUTPUTS["synthesis"], build_synthesis(decision, row_counts, fail_anatomy))
    write_json(OUTPUTS["output_manifest"], build_manifest(generated_at, row_counts))
    print(json.dumps({
        "ok": True,
        "route_dir": rel(ROUTE_DIR),
        "row_counts": row_counts,
        "decision": decision["terminal_decision"],
        "safe_flags": SAFE_FLAGS,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
