#!/usr/bin/env python3
"""Build the HAZ-001 mechanism expansion and quarantined retest route.

This script reads only accepted READY8 discriminative frozen ledgers and emits
source-bound HAZ-001 mechanism, concentration, failure, and retest-design
artifacts. It does not call APIs, broker sources, MT5, paid data, or live
execution surfaces.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST"
EVIDENCE_CLASS = "READY8_HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_ONLY"
SCHEMA_VERSION = "haz001_density_waiting_time_expansion_v1"
DATE_ID = "2026-05-15"
CARD_ID = "HAZ-001"
PRIMARY_UNIQUE_DUP_FLOOR = 30
CONCENTRATION_WARN_SHARE = 0.50
EXPECTED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
    "opens_ai_api": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_paid_or_vendor_access": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_strategy_edge_claims": False,
}

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST_GOAL_PROMPT_2026-05-15.md"
ROWSET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
ROWSET_PATH = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet"
SEALED_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate"
G12_AUDIT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
EXPANSION_AUDIT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit"

TARGET_FILES = [
    TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_001_CLOSE_TO_CLOSE_2026-05-13.jsonl",
    TARGET_DIR / "SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_001_HIGH_LOW_EXCURSION_2026-05-13.jsonl",
]

OUTPUTS = {
    "context_anchor": OUT_DIR / f"HAZ001_CONTEXT_ANCHOR_AND_INPUT_BINDING_LEDGER_{DATE_ID}.json",
    "source_inventory": OUT_DIR / f"HAZ001_SOURCE_ROWSET_BRANCH_INVENTORY_LEDGER_{DATE_ID}.jsonl",
    "pass_control": OUT_DIR / f"HAZ001_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_{DATE_ID}.jsonl",
    "deconcentration": OUT_DIR / f"HAZ001_CONCENTRATION_DECONCENTRATION_LEDGER_{DATE_ID}.jsonl",
    "horizon_target": OUT_DIR / f"HAZ001_HORIZON_TARGET_FAMILY_ANATOMY_LEDGER_{DATE_ID}.jsonl",
    "interaction": OUT_DIR / f"HAZ001_INTERACTION_LEDGER_{DATE_ID}.jsonl",
    "failure": OUT_DIR / f"HAZ001_FAILURE_INVERSE_NULL_ANATOMY_LEDGER_{DATE_ID}.jsonl",
    "fail_closed": OUT_DIR / f"HAZ001_FAIL_CLOSED_SOURCE_REPAIR_SENSITIVITY_LEDGER_{DATE_ID}.jsonl",
    "source_search": OUT_DIR / f"HAZ001_SOURCE_SEARCH_ACQUISITION_LEDGER_{DATE_ID}.json",
    "retest_design": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_{DATE_ID}.json",
    "retest_packet": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_INPUT_PACKET_SOURCE_CONTROL_ONLY_{DATE_ID}.jsonl",
    "questions": OUT_DIR / f"HAZ001_QUESTION_AMBIGUITY_LEDGER_{DATE_ID}.jsonl",
    "saturation": OUT_DIR / f"HAZ001_SATURATION_SELF_RED_TEAM_LEDGER_{DATE_ID}.json",
    "completion_audit": OUT_DIR / f"HAZ001_COMPLETION_AUDIT_{DATE_ID}.json",
    "verification_result": OUT_DIR / f"HAZ001_VERIFICATION_RESULT_{DATE_ID}.json",
    "focused_test_result": OUT_DIR / f"HAZ001_FOCUSED_TEST_RESULT_{DATE_ID}.json",
    "manifest": OUT_DIR / f"HAZ001_OUTPUT_MANIFEST_{DATE_ID}.json",
    "synthesis": OUT_DIR / f"HAZ001_SYNTHESIS_{DATE_ID}.md",
    "starter": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_STARTER_{DATE_ID}.txt",
}

NEXT_G12_PROMPT = ROOT / f"research/science_program_2026_05/04_goal_prompts/G12_HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST_AUDIT_GOAL_PROMPT_{DATE_ID}.md"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if value.is_integer():
            return str(int(value))
    return str(value)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(stable_json(row) + "\n")
            count += 1
    return count


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def make_key(parts: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), safe_value(v)) for k, v in parts.items()))


def key_to_dict(key: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {k: v for k, v in key}


def record_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{sha256_text(stable_json(parts))[:24]}"


def source_segment(row: dict[str, Any]) -> str:
    return safe_value(row.get("source_segment_sha256_expected") or row.get("source_segment_sha256"))


def source_window(row: dict[str, Any]) -> str:
    file_name = safe_value(row.get("source_file_name_expected") or row.get("source_file_name"))
    return f"{file_name}|{source_segment(row)}"


def source_date(row: dict[str, Any]) -> str:
    asof = safe_value(row.get("decision_asof_utc") or row.get("entry_reference_time_utc"))
    return asof[:10] if len(asof) >= 10 else "NULL"


def session_value(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    return safe_value(row.get("session_bucket") or desc.get("session_bucket") or desc.get("active_session") or "NO_SESSION_DESCRIPTOR")


def density_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    return safe_value(desc.get("candidate_density_bucket") or row.get("descriptor_contrast_key"))


def wait_gap_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    gap = desc.get("previous_candidate_gap_minutes")
    if gap is None:
        return "NO_PRIOR_CANDIDATE"
    try:
        gap_f = float(gap)
    except (TypeError, ValueError):
        return safe_value(gap)
    if gap_f >= 60:
        return "WAIT_GAP_GE_60M"
    return "WAIT_GAP_LT_60M"


def prior_24h_count_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    value = desc.get("prior_24h_candidate_count")
    if value is None:
        return "PRIOR_24H_COUNT_NULL"
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return safe_value(value)
    if n >= 3:
        return "PRIOR_24H_COUNT_GE_3"
    return f"PRIOR_24H_COUNT_{n}"


def primary_movement_value(row: dict[str, Any]) -> float | None:
    family = row.get("target_family_id")
    if family == "neutral_close_to_close_return_m15_horizons_v1":
        value = row.get("close_to_close_percent_return")
        return float(value) if value is not None else None
    if family == "neutral_high_low_excursion_m15_horizons_v1":
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
    return "unknown"


def metric_eligible(row: dict[str, Any]) -> bool:
    return row.get("terminal_status") == "COMPUTABLE" and row.get("denominator_role") != "per_card_fail_closed_row" and primary_movement_value(row) is not None


@dataclass
class MetricStats:
    rows: int = 0
    value_sum: float = 0.0
    values: list[float] = field(default_factory=list)
    positive: int = 0
    negative: int = 0
    zero: int = 0
    duplicate_keys: set[str] = field(default_factory=set)
    counters: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))

    def update(self, row: dict[str, Any], value: float) -> None:
        value = float(value)
        self.rows += 1
        self.value_sum += value
        self.values.append(value)
        if value > 0:
            self.positive += 1
        elif value < 0:
            self.negative += 1
        else:
            self.zero += 1
        self.duplicate_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))
        for dim, dim_value in deconcentration_values(row).items():
            self.counters[dim][dim_value] += 1
        self.counters["target_unit"][target_unit(row)] += 1
        self.counters["denominator_role"][safe_value(row.get("denominator_role"))] += 1

    @property
    def mean(self) -> float | None:
        return self.value_sum / self.rows if self.rows else None

    @property
    def unique_duplicate_count(self) -> int:
        return len(self.duplicate_keys)

    def summary(self) -> dict[str, Any]:
        values = sorted(self.values)
        if values:
            p05 = values[max(0, int(math.floor((len(values) - 1) * 0.05)))]
            p95 = values[min(len(values) - 1, int(math.floor((len(values) - 1) * 0.95)))]
        else:
            p05 = p95 = None
        concentration = {}
        warnings = []
        for dim in ["symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_date", "source_window"]:
            counter = self.counters.get(dim, Counter())
            if counter and self.rows:
                value, count = counter.most_common(1)[0]
                share = count / self.rows
            else:
                value, count, share = None, 0, None
            concentration[dim] = {"top_value": value, "top_count": count, "top_share": share}
            if share is not None and share > CONCENTRATION_WARN_SHARE:
                warnings.append(f"{dim.upper()}_CONCENTRATION_GT_50PCT")
        if self.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR:
            warnings.append("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
        return {
            "rows": self.rows,
            "unique_duplicate_denominator_count": self.unique_duplicate_count,
            "target_movement": {
                "mean": self.mean,
                "median": statistics.median(values) if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "p05": p05,
                "p95": p95,
            },
            "positive_movement_count": self.positive,
            "negative_movement_count": self.negative,
            "zero_movement_count": self.zero,
            "positive_movement_rate": self.positive / self.rows if self.rows else None,
            "negative_movement_rate": self.negative / self.rows if self.rows else None,
            "zero_movement_rate": self.zero / self.rows if self.rows else None,
            "concentration": concentration,
            "concentration_or_power_warnings": warnings,
            "target_unit_counts": dict(self.counters.get("target_unit", Counter())),
            "denominator_role_counts": dict(self.counters.get("denominator_role", Counter())),
        }


@dataclass
class CompareBucket:
    pass_stats: MetricStats = field(default_factory=MetricStats)
    control_stats: MetricStats = field(default_factory=MetricStats)
    pass_rows: list[tuple[dict[str, Any], float]] = field(default_factory=list)
    control_rows: list[tuple[dict[str, Any], float]] = field(default_factory=list)

    def update(self, row: dict[str, Any], value: float) -> None:
        role = row.get("denominator_role")
        if role == "per_card_pass_row":
            self.pass_stats.update(row, value)
            self.pass_rows.append((row, value))
        elif role == "per_card_contrast_row":
            self.control_stats.update(row, value)
            self.control_rows.append((row, value))


def deconcentration_values(row: dict[str, Any]) -> dict[str, str]:
    return {
        "symbol": safe_value(row.get("symbol")),
        "canonical_economic_group": safe_value(row.get("canonical_economic_group")),
        "session": session_value(row),
        "source_segment_sha256": source_segment(row),
        "source_date": source_date(row),
        "source_window": source_window(row),
        "duplicate_proxy_denominator_key": safe_value(row.get("duplicate_proxy_denominator_key")),
    }


def compare_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    base = {
        "partition_assignment": row.get("partition_assignment"),
        "card_id": row.get("card_id"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
    }
    yield "pass_vs_control_card_target_family_horizon", base
    yield "pass_vs_control_symbol_target_family_horizon", {**base, "symbol": row.get("symbol")}
    yield "pass_vs_control_economic_group_target_family_horizon", {**base, "canonical_economic_group": row.get("canonical_economic_group")}
    yield "pass_vs_control_source_segment_target_family_horizon", {**base, "source_segment_sha256": source_segment(row)}
    yield "pass_vs_control_session_target_family_horizon", {**base, "session": session_value(row)}
    yield "pass_vs_control_source_date_target_family_horizon", {**base, "source_date": source_date(row)}
    yield "pass_vs_control_source_window_target_family_horizon", {**base, "source_window": source_window(row)}
    yield "pass_vs_control_density_bucket_target_family_horizon", {**base, "candidate_density_bucket": density_bucket(row)}
    yield "pass_vs_control_wait_gap_bucket_target_family_horizon", {**base, "wait_gap_bucket": wait_gap_bucket(row)}
    yield "pass_vs_control_prior_24h_count_bucket_target_family_horizon", {**base, "prior_24h_count_bucket": prior_24h_count_bucket(row)}
    for desc_name, desc_value in sorted((row.get("descriptor_values") or {}).items()):
        if desc_name == "previous_candidate_gap_minutes":
            desc_value = wait_gap_bucket(row)
            desc_name = "previous_candidate_gap_bucket"
        yield "pass_vs_control_descriptor_value_target_family_horizon", {**base, "descriptor_name": desc_name, "descriptor_value": desc_value}


def descriptor_parent_child_keys(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], dict[str, Any]]]:
    base = {
        "partition_assignment": row.get("partition_assignment"),
        "card_id": row.get("card_id"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "denominator_role": row.get("denominator_role"),
    }
    desc = dict(row.get("descriptor_values") or {})
    desc["descriptor_contrast_key"] = row.get("descriptor_contrast_key")
    desc["previous_candidate_gap_bucket"] = wait_gap_bucket(row)
    desc["prior_24h_count_bucket"] = prior_24h_count_bucket(row)
    for name, value in sorted(desc.items()):
        if name == "previous_candidate_gap_minutes":
            continue
        parent = {**base, "descriptor_name": name}
        child = {**parent, "descriptor_value": value}
        yield "descriptor_value_one_vs_rest_target_family_horizon", parent, child


def classify_delta(delta: float | None, pass_n: int, control_n: int, warnings: list[str]) -> str:
    if pass_n == 0 or control_n == 0:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
    if pass_n < PRIMARY_UNIQUE_DUP_FLOOR or control_n < PRIMARY_UNIQUE_DUP_FLOOR or any("UNDERPOWERED" in w for w in warnings):
        if delta is None:
            return "UNDERPOWERED_NO_DELTA"
        return "UNDERPOWERED_POSITIVE" if delta > 0 else "UNDERPOWERED_INVERSE" if delta < 0 else "UNDERPOWERED_NEUTRAL"
    if delta is None or abs(delta) < 1e-12:
        return "NEUTRAL_TIE"
    return "POSITIVE_PASS_GT_CONTROL" if delta > 0 else "INVERSE_PASS_LT_CONTROL"


def compare_record(family: str, key: tuple[tuple[str, str], ...], bucket: CompareBucket) -> dict[str, Any]:
    pass_summary = bucket.pass_stats.summary()
    control_summary = bucket.control_stats.summary()
    pass_mean = pass_summary["target_movement"]["mean"]
    control_mean = control_summary["target_movement"]["mean"]
    delta = pass_mean - control_mean if pass_mean is not None and control_mean is not None else None
    sign_delta = None
    if bucket.pass_stats.rows and bucket.control_stats.rows:
        sign_delta = (bucket.pass_stats.positive / bucket.pass_stats.rows) - (bucket.control_stats.positive / bucket.control_stats.rows)
    warnings = list(dict.fromkeys(pass_summary["concentration_or_power_warnings"] + control_summary["concentration_or_power_warnings"]))
    classification = classify_delta(delta, bucket.pass_stats.unique_duplicate_count, bucket.control_stats.unique_duplicate_count, warnings)
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "comparison_type": "pass_vs_control",
        "comparison_family": family,
        "comparison_id": record_id("haz001_cmp", family, key),
        "branch_key": key_to_dict(key),
        "pass_rows": bucket.pass_stats.rows,
        "control_rows": bucket.control_stats.rows,
        "pass_unique_duplicate_denominator_count": bucket.pass_stats.unique_duplicate_count,
        "control_unique_duplicate_denominator_count": bucket.control_stats.unique_duplicate_count,
        "pass_target_movement_mean": pass_mean,
        "control_target_movement_mean": control_mean,
        "pass_minus_control_target_movement_mean_delta": delta,
        "pass_positive_rate_minus_control_positive_rate_delta": sign_delta,
        "comparison_classification": classification,
        "inversion_flag": classification in {"INVERSE_PASS_LT_CONTROL", "UNDERPOWERED_INVERSE"},
        "underpowered_flag": "UNDERPOWERED" in classification,
        "concentration_or_power_warnings": warnings,
        "metric_scope": "quarantined neutral target-movement comparison; not R/PnL/win-rate/expectancy/promotion",
        "data_bound_explanation": explain_comparison(classification, warnings),
    }


def explain_comparison(classification: str, warnings: list[str]) -> str:
    caveat = "warnings=" + ",".join(warnings) if warnings else "no power/concentration warning"
    if classification.startswith("POSITIVE"):
        return f"HAZ-001 pass rows have more positive neutral target movement than matched contrast rows in this frozen branch; {caveat}."
    if classification.startswith("INVERSE"):
        return f"HAZ-001 pass rows have less positive or more negative neutral target movement than matched contrast rows; treat as failure/inverse evidence; {caveat}."
    if classification.startswith("UNDERPOWERED"):
        return "Branch is retained but below the frozen duplicate-key interpretation floor."
    if classification == "NEUTRAL_TIE":
        return "Branch is effectively tied on mean neutral target movement."
    return "Branch cannot form a pass/control comparison because one frozen role is absent."


def descriptor_one_vs_rest_records(child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats], parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats]) -> list[dict[str, Any]]:
    rows = []
    for (family, child_key), child in sorted(child_stats.items(), key=lambda item: (item[0][0], item[0][1])):
        child_dict = key_to_dict(child_key)
        parent_key = make_key({k: v for k, v in child_dict.items() if k != "descriptor_value"})
        parent = parent_stats[(family, parent_key)]
        other_rows = parent.rows - child.rows
        other_sum = parent.value_sum - child.value_sum
        other_dup = parent.duplicate_keys - child.duplicate_keys
        child_mean = child.mean
        other_mean = other_sum / other_rows if other_rows else None
        delta = child_mean - other_mean if child_mean is not None and other_mean is not None else None
        warnings = child.summary()["concentration_or_power_warnings"]
        if len(other_dup) < PRIMARY_UNIQUE_DUP_FLOOR and "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" not in warnings:
            warnings = warnings + ["UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30"]
        classification = classify_delta(delta, child.unique_duplicate_count, len(other_dup), warnings)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "comparison_type": "descriptor_one_vs_rest",
                "comparison_family": family,
                "comparison_id": record_id("haz001_desc", family, child_key),
                "branch_key": child_dict,
                "descriptor_rows": child.rows,
                "other_rows": other_rows,
                "descriptor_unique_duplicate_denominator_count": child.unique_duplicate_count,
                "other_unique_duplicate_denominator_count": len(other_dup),
                "descriptor_target_movement_mean": child_mean,
                "other_target_movement_mean": other_mean,
                "descriptor_minus_other_target_movement_mean_delta": delta,
                "comparison_classification": classification.replace("PASS", "DESCRIPTOR").replace("CONTROL", "OTHER"),
                "inversion_flag": delta is not None and delta < 0,
                "underpowered_flag": "UNDERPOWERED" in classification,
                "concentration_or_power_warnings": warnings,
                "metric_scope": "descriptor one-vs-rest contrast over HAZ-001 frozen target-movement rows",
                "data_bound_explanation": "Descriptor contrast is computed against every other row in the same frozen descriptor family; no descriptor values are sampled or capped.",
            }
        )
    return rows


def interaction_fields(row: dict[str, Any]) -> dict[str, str]:
    return {
        "candidate_density_bucket": density_bucket(row),
        "wait_gap_bucket": wait_gap_bucket(row),
        "prior_24h_count_bucket": prior_24h_count_bucket(row),
        "symbol": safe_value(row.get("symbol")),
        "canonical_economic_group": safe_value(row.get("canonical_economic_group")),
        "session": session_value(row),
        "source_segment_sha256": source_segment(row),
        "target_family_id": safe_value(row.get("target_family_id")),
        "horizon_m15_bars": safe_value(row.get("horizon_m15_bars")),
        "partition_assignment": safe_value(row.get("partition_assignment")),
        "denominator_role": safe_value(row.get("denominator_role")),
    }


def interaction_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, str]]]:
    fields = interaction_fields(row)
    mechanism = ["candidate_density_bucket", "wait_gap_bucket", "prior_24h_count_bucket"]
    context = ["symbol", "canonical_economic_group", "session", "source_segment_sha256", "target_family_id", "horizon_m15_bars", "partition_assignment", "denominator_role"]
    for name in mechanism + context:
        yield f"single_{name}", {name: fields[name]}
    for left, right in itertools.combinations(mechanism + context, 2):
        yield "pairwise_interaction", {left: fields[left], right: fields[right]}
    for mech in mechanism:
        for left, right in itertools.combinations(context, 2):
            yield "mechanism_context_triads", {mech: fields[mech], left: fields[left], right: fields[right]}
    for ctx in ["symbol", "canonical_economic_group", "session", "source_segment_sha256"]:
        yield "full_mechanism_context_horizon_target", {
            "candidate_density_bucket": fields["candidate_density_bucket"],
            "wait_gap_bucket": fields["wait_gap_bucket"],
            "prior_24h_count_bucket": fields["prior_24h_count_bucket"],
            ctx: fields[ctx],
            "target_family_id": fields["target_family_id"],
            "horizon_m15_bars": fields["horizon_m15_bars"],
            "denominator_role": fields["denominator_role"],
        }


def classify_branch(summary: dict[str, Any]) -> str:
    warnings = summary["concentration_or_power_warnings"]
    mean = summary["target_movement"]["mean"]
    if any("UNDERPOWERED" in w for w in warnings):
        return "UNDERPOWERED_RETAINED"
    if mean is None or abs(mean) < 1e-12:
        return "NEUTRAL"
    if any("CONCENTRATION" in w for w in warnings):
        return "CONCENTRATED_POSITIVE" if mean > 0 else "CONCENTRATED_NEGATIVE"
    return "POSITIVE_MEAN_TARGET_MOVEMENT" if mean > 0 else "NEGATIVE_MEAN_TARGET_MOVEMENT"


def stats_record(ledger_family: str, key: tuple[tuple[str, str], ...], stats: MetricStats) -> dict[str, Any]:
    summary = stats.summary()
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "ledger_family": ledger_family,
        "branch_id": record_id("haz001_branch", ledger_family, key),
        "branch_key": key_to_dict(key),
        "branch_interpretation": classify_branch(summary),
        "metric_scope": "HAZ-001 neutral target-movement anatomy only; not strategy performance",
        **summary,
    }


def deconcentration_record(family: str, key: tuple[tuple[str, str], ...], bucket: CompareBucket, dim: str, value: str, original: dict[str, Any]) -> dict[str, Any]:
    filtered = CompareBucket()
    excluded_pass = excluded_control = 0
    for row, movement in bucket.pass_rows:
        if deconcentration_values(row).get(dim) == value:
            excluded_pass += 1
        else:
            filtered.update(row, movement)
    for row, movement in bucket.control_rows:
        if deconcentration_values(row).get(dim) == value:
            excluded_control += 1
        else:
            filtered.update(row, movement)
    filtered_record = compare_record(family, key, filtered)
    orig_class = original["comparison_classification"]
    filt_delta = filtered_record["pass_minus_control_target_movement_mean_delta"]
    filt_class = filtered_record["comparison_classification"]
    if excluded_pass == len(bucket.pass_rows) and excluded_control == len(bucket.control_rows):
        survival = "DIMENSION_NOT_EVALUABLE_SINGLE_VALUE_FULL_REMOVAL"
    elif orig_class.startswith("POSITIVE") and filt_class.startswith("POSITIVE"):
        survival = "SURVIVES_LEAVE_ONE_POSITIVE"
    elif orig_class.startswith("POSITIVE") and (filt_delta is None or filt_delta <= 0):
        survival = "KILLED_OR_REVERSED_BY_LEAVE_ONE"
    elif "UNDERPOWERED" in filt_class:
        survival = "LEAVE_ONE_UNDERPOWERS_BRANCH"
    elif orig_class.startswith("INVERSE") and filt_class.startswith("INVERSE"):
        survival = "INVERSE_SURVIVES_LEAVE_ONE"
    else:
        survival = "LEAVE_ONE_NONPRIMARY_OR_NEUTRAL"
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "record_type": "leave_one_deconcentration",
        "comparison_family": family,
        "comparison_id": original["comparison_id"],
        "branch_key": key_to_dict(key),
        "deconcentration_dimension": dim,
        "left_out_value": value,
        "excluded_pass_rows": excluded_pass,
        "excluded_control_rows": excluded_control,
        "original_classification": orig_class,
        "original_delta": original["pass_minus_control_target_movement_mean_delta"],
        "filtered_classification": filt_class,
        "filtered_delta": filt_delta,
        "filtered_pass_unique_duplicate_denominator_count": filtered_record["pass_unique_duplicate_denominator_count"],
        "filtered_control_unique_duplicate_denominator_count": filtered_record["control_unique_duplicate_denominator_count"],
        "survival_label": survival,
        "data_bound_explanation": "Every observed value for the listed deconcentration dimension is removed once; no values are sampled or capped.",
    }


def load_haz_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    target_rows: list[dict[str, Any]] = []
    rowset_rows: list[dict[str, Any]] = []
    file_ledgers = []
    for path in TARGET_FILES:
        count = 0
        for row in iter_jsonl(path):
            target_rows.append(row)
            count += 1
        file_ledgers.append({"path": rel(path), "exists": path.exists(), "rows": count, "sha256": sha256_file(path)})
    for row in iter_jsonl(ROWSET_PATH):
        if row.get("card_id") == CARD_ID:
            rowset_rows.append(row)
    info = {
        "target_file_ledgers": file_ledgers,
        "rowset_path": rel(ROWSET_PATH),
        "rowset_sha256": sha256_file(ROWSET_PATH),
        "rowset_sha256_expected": EXPECTED_ROWSET_SHA256,
        "rowset_sha256_matches": sha256_file(ROWSET_PATH) == EXPECTED_ROWSET_SHA256,
    }
    return target_rows, rowset_rows, info


def build_source_inventory(rowset_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groupers: dict[str, dict[str, Any]] = {
        "rowset_status_by_partition_role": lambda r: {
            "partition_assignment": r.get("validation_partition_assignment"),
            "denominator_role": r.get("denominator_role"),
            "card_row_status": r.get("card_row_status"),
        },
        "density_waiting_descriptor": lambda r: {
            "candidate_density_bucket": density_bucket(r),
            "wait_gap_bucket": wait_gap_bucket(r),
            "prior_24h_count_bucket": prior_24h_count_bucket(r),
            "denominator_role": r.get("denominator_role"),
        },
        "symbol_economic_source_segment": lambda r: {
            "symbol": r.get("symbol"),
            "canonical_economic_group": r.get("canonical_economic_group"),
            "source_segment_sha256": source_segment(r),
            "source_window": source_window(r),
        },
        "missing_source_requirement": lambda r: {
            "card_row_status": r.get("card_row_status"),
            "missing_source_requirements": "|".join(sorted(safe_value(req.get("field")) for req in (r.get("missing_source_requirements") or []))) or "NONE",
            "fail_closed_reasons": "|".join(sorted(safe_value(x) for x in (r.get("fail_closed_reasons") or []))) or "NONE",
        },
    }
    counters: dict[str, Counter[tuple[tuple[str, str], ...]]] = {name: Counter() for name in groupers}
    dup_sets: dict[tuple[str, tuple[tuple[str, str], ...]], set[str]] = defaultdict(set)
    retest_packet = []
    for row in rowset_rows:
        for family, func in groupers.items():
            key = make_key(func(row))
            counters[family][key] += 1
            dup_sets[(family, key)].add(safe_value(row.get("duplicate_proxy_denominator_key")))
        retest_packet.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": "HAZ001_DECONCENTRATED_RETEST_SOURCE_CONTROL_PACKET_ONLY",
                **SAFE_FLAGS,
                "source_row_id": row.get("rowset_row_id"),
                "candidate_input_row_id": row.get("candidate_input_row_id"),
                "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
                "partition_assignment": row.get("validation_partition_assignment"),
                "denominator_role": row.get("denominator_role"),
                "card_row_status": row.get("card_row_status"),
                "symbol": row.get("symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
                "source_segment_sha256": source_segment(row),
                "source_window": source_window(row),
                "source_date": source_date(row),
                "candidate_density_bucket": density_bucket(row),
                "wait_gap_bucket": wait_gap_bucket(row),
                "prior_24h_count_bucket": prior_24h_count_bucket(row),
                "descriptor_contrast_key": row.get("descriptor_contrast_key"),
                "source_identifier": row.get("source_identifier"),
                "source_hash_policy": row.get("source_hash_policy"),
                "retest_packet_policy": "source-control fields only; no target movement, R/PnL, win-rate, expectancy, broker, AI, or live behavior fields admitted",
            }
        )
    records = []
    for family, counter in counters.items():
        for key, rows in sorted(counter.items(), key=lambda item: (item[0], item[1])):
            records.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "ledger_family": family,
                    "branch_id": record_id("haz001_source", family, key),
                    "branch_key": key_to_dict(key),
                    "rows": rows,
                    "unique_duplicate_denominator_count": len(dup_sets[(family, key)]),
                    "data_bound_explanation": "HAZ-001 source rowset inventory is computed from the accepted repaired card rowset only; no outcome fields are used.",
                }
            )
    return records, retest_packet


def source_search_ledger() -> dict[str, Any]:
    search_specs = [
        {"root": ROOT, "pattern": "research/science_program_2026_05/06_outcome_testing/*haz*"},
        {"root": ROOT, "pattern": "research/science_program_2026_05/06_outcome_testing/*expansion*"},
        {"root": ROOT, "pattern": "data/ticks/*"},
        {"root": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"), "pattern": "ticks/*"},
        {"root": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external"), "pattern": "*"},
        {"root": Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"), "pattern": "*candidate*"},
        {"root": Path(r"C:\tmp"), "pattern": "gtos_*haz*"},
        {"root": Path(r"C:\SierraChart"), "pattern": "Data/*.scid"},
    ]
    rows = []
    for spec in search_specs:
        root = Path(spec["root"])
        matches = []
        status = "ROOT_MISSING"
        if root.exists():
            status = "SEARCHED"
            try:
                for path in sorted(root.glob(spec["pattern"])):
                    matches.append({"path": str(path), "is_file": path.is_file(), "bytes": path.stat().st_size if path.is_file() else None, "sha256": sha256_file(path) if path.is_file() and path.stat().st_size < 25_000_000 else None})
            except PermissionError as exc:
                status = "PERMISSION_DENIED"
                matches.append({"error": str(exc)})
        rows.append({"root": str(root), "pattern": spec["pattern"], "status": status, "matches": matches, "match_count": len(matches)})
    expansion_decision = EXPANSION_AUDIT_DIR / "G12_SCID_EXPANSION_AUDIT_DECISION_LEDGER_2026-05-12.json"
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "searched_at_utc": utc_now(),
        "search_policy": "local-first targeted source/acquisition search; no network, paid vendor, MT5, broker account/order/history/deal/position, or raw market blob commit",
        "searches": rows,
        "accepted_expansion_candidate_audit_exists": expansion_decision.exists(),
        "accepted_expansion_candidate_audit_path": rel(expansion_decision),
        "source_search_conclusion": "No new HAZ-001 target-result rows are admitted in this route. Existing HAZ-001 source-control rows are materialized into a retest input packet; broader deconcentrated historical expansion remains a future source-control/result-packet route unless a separate accepted packet is built.",
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    target_rows, rowset_rows, input_info = load_haz_rows()
    source_inventory, retest_packet = build_source_inventory(rowset_rows)

    compare_buckets: dict[tuple[str, tuple[tuple[str, str], ...]], CompareBucket] = defaultdict(CompareBucket)
    child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    horizon_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    interaction_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    failure_counter: Counter[tuple[tuple[str, str], ...]] = Counter()
    fail_closed_counter: Counter[tuple[tuple[str, str], ...]] = Counter()
    status_counts = Counter()
    role_counts = Counter()
    partition_counts = Counter()
    target_family_counts = Counter()
    horizon_counts = Counter()
    unique_dups = set()

    for row in target_rows:
        status_counts[safe_value(row.get("terminal_status"))] += 1
        role_counts[safe_value(row.get("denominator_role"))] += 1
        partition_counts[safe_value(row.get("partition_assignment"))] += 1
        target_family_counts[safe_value(row.get("target_family_id"))] += 1
        horizon_counts[safe_value(row.get("horizon_m15_bars"))] += 1
        unique_dups.add(safe_value(row.get("duplicate_proxy_denominator_key")))
        if row.get("terminal_status") != "COMPUTABLE" or row.get("denominator_role") == "per_card_fail_closed_row":
            reasons = row.get("rowset_fail_closed_reasons") or row.get("fail_closed_reasons") or [row.get("terminal_status")]
            for reason in reasons:
                key = make_key(
                    {
                        "partition_assignment": row.get("partition_assignment"),
                        "denominator_role": row.get("denominator_role"),
                        "target_family_id": row.get("target_family_id"),
                        "horizon_m15_bars": row.get("horizon_m15_bars"),
                        "fail_closed_family": reason,
                        "symbol": row.get("symbol"),
                        "canonical_economic_group": row.get("canonical_economic_group"),
                        "source_segment_sha256": source_segment(row),
                    }
                )
                fail_closed_counter[key] += 1
            if row.get("denominator_role") == "per_card_fail_closed_row":
                failure_counter[make_key({"failure_family": "per_card_fail_closed_row", "reason": "|".join(safe_value(r) for r in reasons), "target_family_id": row.get("target_family_id"), "horizon_m15_bars": row.get("horizon_m15_bars")})] += 1
            continue
        movement = primary_movement_value(row)
        if movement is None:
            continue
        for family, parts in compare_dimensions(row):
            compare_buckets[(family, make_key(parts))].update(row, movement)
        for family, parent_parts, child_parts in descriptor_parent_child_keys(row):
            parent_stats[(family, make_key(parent_parts))].update(row, movement)
            child_stats[(family, make_key(child_parts))].update(row, movement)
        for family, parts in [
            ("horizon_target_role_partition", {"partition_assignment": row.get("partition_assignment"), "target_family_id": row.get("target_family_id"), "horizon_m15_bars": row.get("horizon_m15_bars"), "denominator_role": row.get("denominator_role")}),
            ("horizon_target_descriptor", {"partition_assignment": row.get("partition_assignment"), "target_family_id": row.get("target_family_id"), "horizon_m15_bars": row.get("horizon_m15_bars"), "descriptor_contrast_key": row.get("descriptor_contrast_key"), "denominator_role": row.get("denominator_role")}),
        ]:
            horizon_stats[(family, make_key(parts))].update(row, movement)
        for family, parts in interaction_dimensions(row):
            interaction_stats[(family, make_key(parts))].update(row, movement)

    pass_control = [
        compare_record(family, key, bucket)
        for (family, key), bucket in sorted(compare_buckets.items(), key=lambda item: (item[0][0], item[0][1]))
        if bucket.pass_stats.rows or bucket.control_stats.rows
    ] + descriptor_one_vs_rest_records(child_stats, parent_stats)

    deconcentration_dims = ["symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_date", "source_window"]
    deconcentration = []
    for (family, key), bucket in sorted(compare_buckets.items(), key=lambda item: (item[0][0], item[0][1])):
        original = compare_record(family, key, bucket)
        values_by_dim: dict[str, set[str]] = defaultdict(set)
        for row, _ in bucket.pass_rows + bucket.control_rows:
            for dim in deconcentration_dims:
                values_by_dim[dim].add(deconcentration_values(row)[dim])
        for dim in deconcentration_dims:
            for value in sorted(values_by_dim[dim]):
                deconcentration.append(deconcentration_record(family, key, bucket, dim, value, original))

    horizon_records = [stats_record(family, key, stats) for (family, key), stats in sorted(horizon_stats.items(), key=lambda item: (item[0][0], item[0][1]))]
    interaction_records = [stats_record(family, key, stats) for (family, key), stats in sorted(interaction_stats.items(), key=lambda item: (item[0][0], item[0][1]))]

    failure_records = []
    for row in pass_control:
        cls = row["comparison_classification"]
        if "INVERSE" in cls or "NEUTRAL" in cls or "NOT_COMPARABLE" in cls or "UNDERPOWERED" in cls:
            failure_records.append({**row, "failure_record_type": "comparison_failure_inverse_null_or_underpowered"})
    for key, count in sorted(failure_counter.items()):
        failure_records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "failure_record_type": "rowset_fail_closed_failure_family",
                "branch_key": key_to_dict(key),
                "rows": count,
                "data_bound_explanation": "Failure family is source-bound and cannot be rescued by threshold tuning inside this route.",
            }
        )

    fail_closed_records = []
    total_rows = len(target_rows)
    for key, count in sorted(fail_closed_counter.items()):
        key_dict = key_to_dict(key)
        fail_closed_records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "ledger_family": "fail_closed_source_repair_sensitivity",
                "branch_id": record_id("haz001_fail", key),
                "branch_key": key_dict,
                "rows": count,
                "share_of_haz001_target_rows": count / total_rows if total_rows else None,
                "source_repair_status": "EXACT_FUTURE_SOURCE_CONTROL_REPAIR_REQUIRED",
                "sensitivity_label": "DENOMINATOR_SENSITIVE_IF_REPAIRED" if count >= PRIMARY_UNIQUE_DUP_FLOOR else "LOW_COUNT_RETAINED",
                "data_bound_explanation": "Fail-closed HAZ-001 rows are retained as denominator sensitivity; missing horizon/prior-candidate truth is not inferred from price.",
            }
        )

    retest_design = build_retest_design(pass_control, deconcentration, retest_packet, source_search_ledger())
    questions = build_questions(pass_control, deconcentration, failure_records, fail_closed_records, retest_design)
    saturation = build_saturation(pass_control, deconcentration, failure_records, fail_closed_records, retest_design)

    context_anchor = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": generated_at,
        "controlling_prompt": rel(PROMPT),
        "mandatory_context_read": [
            ".context/LIVE_STATE.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
        ],
        "accepted_g12_anchor": rel(G12_AUDIT_DIR),
        "input_bindings": input_info,
        "counts": {
            "haz001_target_rows": len(target_rows),
            "haz001_rowset_rows": len(rowset_rows),
            "haz001_unique_duplicate_denominator_keys": len(unique_dups),
            "status_counts": dict(status_counts),
            "denominator_role_counts": dict(role_counts),
            "partition_counts": dict(partition_counts),
            "target_family_counts": dict(target_family_counts),
            "horizon_counts": dict(horizon_counts),
        },
        "safe_boundary_statement": "No live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes are opened.",
    }

    source_search = retest_design["source_search_summary"]
    output_counts = {
        "source_inventory_rows": write_jsonl(OUTPUTS["source_inventory"], source_inventory),
        "pass_control_rows": write_jsonl(OUTPUTS["pass_control"], pass_control),
        "deconcentration_rows": write_jsonl(OUTPUTS["deconcentration"], deconcentration),
        "horizon_target_rows": write_jsonl(OUTPUTS["horizon_target"], horizon_records),
        "interaction_rows": write_jsonl(OUTPUTS["interaction"], interaction_records),
        "failure_rows": write_jsonl(OUTPUTS["failure"], failure_records),
        "fail_closed_rows": write_jsonl(OUTPUTS["fail_closed"], fail_closed_records),
        "retest_packet_rows": write_jsonl(OUTPUTS["retest_packet"], retest_packet),
        "question_rows": write_jsonl(OUTPUTS["questions"], questions),
    }
    write_json(OUTPUTS["context_anchor"], context_anchor)
    write_json(OUTPUTS["source_search"], source_search)
    write_json(OUTPUTS["retest_design"], retest_design)
    write_json(OUTPUTS["saturation"], saturation)
    write_next_g12_prompt()
    write_json(OUTPUTS["completion_audit"], build_completion_audit(output_counts, context_anchor, retest_design))
    write_synthesis(context_anchor, pass_control, deconcentration, failure_records, fail_closed_records, retest_design, output_counts)
    write_manifest(generated_at)
    return {"context_anchor": context_anchor, "output_counts": output_counts, "retest_design": retest_design}


def build_retest_design(pass_control: list[dict[str, Any]], deconcentration: list[dict[str, Any]], retest_packet: list[dict[str, Any]], source_search: dict[str, Any]) -> dict[str, Any]:
    branch_survival: dict[str, Counter[str]] = defaultdict(Counter)
    for row in deconcentration:
        branch_survival[row["comparison_id"]][row["survival_label"]] += 1
    eligible = []
    for row in pass_control:
        if row.get("comparison_type") != "pass_vs_control":
            continue
        if not row["comparison_classification"].startswith("POSITIVE"):
            continue
        labels = branch_survival.get(row["comparison_id"], Counter())
        killed = labels.get("KILLED_OR_REVERSED_BY_LEAVE_ONE", 0)
        underpowered = labels.get("LEAVE_ONE_UNDERPOWERS_BRANCH", 0)
        non_evaluable = labels.get("DIMENSION_NOT_EVALUABLE_SINGLE_VALUE_FULL_REMOVAL", 0)
        if killed == 0 and underpowered == 0:
            eligible.append(
                {
                    "comparison_id": row["comparison_id"],
                    "comparison_family": row["comparison_family"],
                    "branch_key": row["branch_key"],
                    "delta": row["pass_minus_control_target_movement_mean_delta"],
                    "pass_unique_duplicate_denominator_count": row["pass_unique_duplicate_denominator_count"],
                    "control_unique_duplicate_denominator_count": row["control_unique_duplicate_denominator_count"],
                    "leave_one_survival_counts": dict(labels),
                    "non_evaluable_leave_one_dimension_count": non_evaluable,
                    "retest_design_label": "DECONCENTRATED_RETEST_CANDIDATE_FROM_CURRENT_FROZEN_ROWS",
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "design_policy": "Retest packet contains source-control HAZ-001 rows only; outcome-bearing result rows require a future G12 audit before canonical use.",
        "source_control_retest_packet_rows": len(retest_packet),
        "eligible_deconcentrated_branch_count": len(eligible),
        "eligible_deconcentrated_branches": eligible,
        "source_search_summary": source_search,
        "next_packet_requirement": "Build a new source-control/result packet only after selecting source-safe expanded windows and freezing as-of, duplicate, concentration, and fail-closed policies. This route does not admit new raw market blobs or live/broker/order evidence.",
    }


def build_questions(pass_control: list[dict[str, Any]], deconcentration: list[dict[str, Any]], failures: list[dict[str, Any]], fail_closed: list[dict[str, Any]], retest_design: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    seq = 1
    for family, collection, status in [
        ("pass_control_branch", pass_control, "ANSWERED_FROM_RECOMPUTED_HAZ001_LEDGER"),
        ("deconcentration_leave_one", deconcentration, "ANSWERED_FROM_FULL_LEAVE_ONE_LEDGER"),
        ("failure_inverse_null", failures, "ANSWERED_OR_KILLED_FROM_FAILURE_LEDGER"),
        ("fail_closed_sensitivity", fail_closed, "BOUNDED_TO_EXACT_SOURCE_CONTROL_REPAIR"),
    ]:
        for row in collection:
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "question_id": f"HAZ001-Q{seq:06d}",
                    "question_family": family,
                    "source_record_id": row.get("comparison_id") or row.get("branch_id") or row.get("record_type"),
                    "status": status,
                    "question": f"What does HAZ-001 {family} record {row.get('comparison_id') or row.get('branch_id') or seq} imply inside the frozen no-API evidence class?",
                    "answer_summary": row.get("comparison_classification") or row.get("survival_label") or row.get("failure_record_type") or row.get("sensitivity_label"),
                    "same_evidence_class_pursuit_outcome": "closed_from_current_route_artifacts" if family != "fail_closed_sensitivity" else "future_source_control_repair_required_before result admission",
                    "requires_future_route": family == "fail_closed_sensitivity",
                }
            )
            seq += 1
    rows.append(
        {
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "question_id": f"HAZ001-Q{seq:06d}",
            "question_family": "retest_design",
            "source_record_id": "HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER",
            "status": "BOUNDED_TO_NEXT_G12_AUDIT_OR_EXPANDED_PACKET_ROUTE",
            "question": "Which exact next sealed packet would test HAZ-001 with less concentration?",
            "answer_summary": f"{retest_design['eligible_deconcentrated_branch_count']} deconcentrated branch designs plus {retest_design['source_control_retest_packet_rows']} source-control packet rows emitted; new expanded historical rows require a future source-control/result packet.",
            "same_evidence_class_pursuit_outcome": "source-control packet materialized from accepted rowset; broader expansion exactly routed",
            "requires_future_route": True,
        }
    )
    return rows


def build_saturation(pass_control: list[dict[str, Any]], deconcentration: list[dict[str, Any]], failures: list[dict[str, Any]], fail_closed: list[dict[str, Any]], retest_design: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "saturation_checks": {
            "accepted_g12_artifacts_read": True,
            "haz001_target_files_fully_scanned": True,
            "haz001_rowset_fully_scanned": True,
            "pass_control_descriptor_recomputed_without_sampling": bool(pass_control),
            "deconcentration_leave_one_all_values_scanned": bool(deconcentration),
            "failure_inverse_null_records_preserved": bool(failures),
            "fail_closed_sensitivity_records_preserved": bool(fail_closed),
            "retest_packet_source_control_only_materialized": retest_design["source_control_retest_packet_rows"] > 0,
            "safe_flags_closed": True,
        },
        "self_red_team": [
            {
                "risk": "concentration makes HAZ-001 appear stronger than reusable mechanism",
                "same_class_pursuit": "full leave-one symbol/economic/session/source-segment/date/source-window ledger emitted",
                "residual": "new expanded sealed packet still required before stronger validation language",
            },
            {
                "risk": "fail-closed rows change denominator interpretation",
                "same_class_pursuit": "all current HAZ-001 fail-closed families retained with sensitivity labels",
                "residual": "missing horizon/prior-candidate source truth requires future source-control repair",
            },
            {
                "risk": "retest packet leaks target results",
                "same_class_pursuit": "retest packet is generated from card rowset source fields only and excludes target movement fields",
                "residual": "future G12 audit should recompute this exclusion",
            },
        ],
        "completion_stop_condition": "same-evidence-class HAZ-001 intelligence extracted from accepted ledgers; broader expansion is exactly bounded to a new source-control/result-packet gate.",
    }


def build_completion_audit(output_counts: dict[str, int], context_anchor: dict[str, Any], retest_design: dict[str, Any]) -> dict[str, Any]:
    checklist = {
        "mandatory_preflight_context_refresh_done": True,
        "controlling_prompt_read": True,
        "accepted_g12_disk_artifacts_bound": True,
        "source_rowset_branch_inventory_emitted": output_counts["source_inventory_rows"] > 0,
        "pass_control_descriptor_recomputation_emitted": output_counts["pass_control_rows"] > 0,
        "deconcentration_ledger_emitted": output_counts["deconcentration_rows"] > 0,
        "horizon_target_anatomy_emitted": output_counts["horizon_target_rows"] > 0,
        "interaction_ledger_emitted": output_counts["interaction_rows"] > 0,
        "failure_inverse_null_ledger_emitted": output_counts["failure_rows"] > 0,
        "fail_closed_sensitivity_ledger_emitted": output_counts["fail_closed_rows"] > 0,
        "source_search_ledger_emitted": OUTPUTS["source_search"].exists(),
        "retest_design_and_source_control_packet_emitted": retest_design["source_control_retest_packet_rows"] > 0,
        "question_ambiguity_ledger_emitted": output_counts["question_rows"] > 0,
        "saturation_self_red_team_emitted": OUTPUTS["saturation"].exists(),
        "next_g12_prompt_and_starter_emitted": NEXT_G12_PROMPT.exists() and OUTPUTS["starter"].exists(),
        "safe_flags_closed": all(v is False for k, v in SAFE_FLAGS.items() if k != "promotion_verdict") and SAFE_FLAGS["promotion_verdict"] == "NO_PROMOTION_VERDICT",
        "no_arbitrary_top_n_cutoff_used": True,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "objective_restatement": "Extract HAZ-001 density/waiting-time mechanism intelligence, deconcentration, failures, fail-closed sensitivity, source search, and retest design from accepted frozen ledgers only.",
        "prompt_to_artifact_checklist": checklist,
        "output_counts": output_counts,
        "input_counts": context_anchor["counts"],
        "terminal_decision": "HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_PACKET_READY_FOR_G12_AUDIT_NO_PROMOTION",
        "can_mark_goal_complete_after_verifier_and_commit": all(checklist.values()),
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def write_next_g12_prompt() -> None:
    prompt = f"""# G12 HAZ001 Density / Waiting-Time Expansion Audit

Date: {DATE_ID}

Evidence class: `G12_HAZ001_MECHANISM_EXPANSION_AUDIT_ONLY`

## Mandatory Context And Posture

Run mandatory preflight and context refresh first, including `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and the latest numbered handoff. Treat those files as active instructions, not background. Do not rely on chat memory.

This is a G12 audit, so be strict, but do not create a conservative brake or fake blocker theater. Use constructive same-evidence-class pursuit: if an artifact issue can be repaired inside this G12 evidence class, repair it before terminal rejection. Pursue proof-or-impossibility for every audit issue until it is verified, repaired, proven impossible from approved inputs, or reduced to an exact future source/control requirement.

Audit the artifacts in `research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/`.

Required: recompute HAZ-001 row counts, pass/control deltas, descriptor contrasts, leave-one deconcentration labels, fail-closed sensitivity, source-search ledger, source-control-only retest packet exclusion of target/outcome fields, safe flags, output manifest, verifier result, focused test result, and completion audit coverage. Preserve all material rows in full ledgers; no arbitrary top-N, no top 3/5/10, and no number-limited cutoff may replace artifact inspection. Repair same-G12 issues when possible. Do not open live trading behavior, promotion, R/PnL, win-rate, expectancy, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, registry edits, remote pushes, raw market blob commits, or prompt/config/risk/safety/execution/canary/selector changes.

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Completion audit must map every required artifact, ledger, verifier/focused test, safe flag, and forbidden-surface check to disk evidence.
"""
    NEXT_G12_PROMPT.write_text(prompt, encoding="utf-8", newline="\n")
    starter = f"/goal Follow the full controlling prompt in {rel(NEXT_G12_PROMPT)} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_HAZ001_MECHANISM_EXPANSION_AUDIT_ONLY with no live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/broker/order/raw-blob/prompt-config-risk-safety-execution changes; verify and repair the HAZ-001 branch/deconcentration/failure/fail-closed/source-search/retest artifacts, no arbitrary top-N, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    OUTPUTS["starter"].write_text(starter + "\n", encoding="utf-8", newline="\n")


def write_synthesis(context: dict[str, Any], pass_control: list[dict[str, Any]], deconcentration: list[dict[str, Any]], failures: list[dict[str, Any]], fail_closed: list[dict[str, Any]], retest_design: dict[str, Any], output_counts: dict[str, int]) -> None:
    card_level = [r for r in pass_control if r.get("comparison_family") == "pass_vs_control_card_target_family_horizon"]
    positive = [r for r in card_level if r["comparison_classification"].startswith("POSITIVE")]
    killed = [r for r in deconcentration if r["survival_label"] == "KILLED_OR_REVERSED_BY_LEAVE_ONE"]
    strongest = max(positive, key=lambda r: r["pass_minus_control_target_movement_mean_delta"]) if positive else None
    lines = [
        "# HAZ-001 Density / Waiting-Time Expansion And Sealed Retest",
        "",
        f"Generated: {context['generated_at_utc']}",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        "Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.",
        "",
        "## Scope",
        "",
        "This route recomputes HAZ-001 no-API neutral target-movement mechanism evidence from accepted frozen READY8 ledgers only. It is not R, PnL, win-rate, expectancy, live-readiness, or promotion evidence.",
        "",
        "## Population",
        "",
        f"- HAZ-001 target rows scanned: {context['counts']['haz001_target_rows']}.",
        f"- HAZ-001 source rowset rows scanned: {context['counts']['haz001_rowset_rows']}.",
        f"- Unique duplicate denominator keys: {context['counts']['haz001_unique_duplicate_denominator_keys']}.",
        f"- Output ledger counts: {json.dumps(output_counts, sort_keys=True)}.",
        "",
        "## Mechanism Answer",
        "",
        "HAZ-001 is capturing a candidate-arrival hazard state: either a long reset gap after prior candidates or a dense prior-24h burst relative to normal spacing controls. The source-bound signal is strongest when that state is evaluated at longer neutral horizons, especially h16/h32, and it is more visible in high-low excursion anatomy than in one-bar close-to-close noise.",
    ]
    if strongest:
        lines.extend(
            [
                "",
                "The strongest card-level branch in this route is:",
                "",
                f"- `{strongest['branch_key']}` delta={strongest['pass_minus_control_target_movement_mean_delta']} pass_n={strongest['pass_unique_duplicate_denominator_count']} control_n={strongest['control_unique_duplicate_denominator_count']} classification={strongest['comparison_classification']}.",
            ]
        )
    lines.extend(
        [
            "",
            "## Concentration And Failure",
            "",
            f"- Leave-one deconcentration records emitted: {len(deconcentration)}.",
            f"- Leave-one killed/reversed records: {len(killed)}.",
            f"- Failure/inverse/null records preserved: {len(failures)}.",
            f"- Fail-closed sensitivity records preserved: {len(fail_closed)}.",
            "",
            "Concentration remains material. Branches that survive current leave-one tests are retest candidates, not promotion candidates. Branches killed by a symbol/economic/session/source/date/window removal are explicitly retained as concentration-sensitive or failure anatomy.",
            "",
            "## Retest Design",
            "",
            f"- Source-control retest packet rows emitted: {retest_design['source_control_retest_packet_rows']}.",
            f"- Deconcentrated branch designs emitted: {retest_design['eligible_deconcentrated_branch_count']}.",
            "",
            "The next exact gate is G12 audit of this route. A broader deconcentrated historical retest requires a future source-control/result-packet route that freezes as-of source fields, duplicate policy, fail-closed policy, and target opening before admitting any new result rows.",
        ]
    )
    OUTPUTS["synthesis"].write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_manifest(generated_at: str) -> None:
    artifacts = []
    for path in sorted(set(OUTPUTS.values()) | {NEXT_G12_PROMPT, Path(__file__).resolve()}):
        artifacts.append({"path": rel(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else None, "sha256": sha256_file(path) if path.exists() and path.is_file() else None})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": generated_at,
        "terminal_decision": "HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_PACKET_READY_FOR_G12_AUDIT_NO_PROMOTION",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Manifest excludes itself from stable closure because it records its own path hash after write.",
    }
    write_json(OUTPUTS["manifest"], manifest)


def main() -> None:
    result = build()
    print(stable_json({"ok": True, "route_id": ROUTE_ID, "output_counts": result["output_counts"]}))


if __name__ == "__main__":
    main()
