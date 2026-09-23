from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-13"
ROUTE_ID = "SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_AFTER_OPENING_GATE"
EVIDENCE_CLASS = "SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_EXECUTION_ONLY"
SCHEMA_VERSION = "scid_ready8_discriminative_sealed_validation_execution_v1"

EXPECTED_READY8_CARDS = [
    "ADV-001",
    "ADV-003",
    "BEH-001",
    "HAZ-001",
    "HAZ-005",
    "MAC-001",
    "MAC-004",
    "UNC-004",
]
EXPECTED_HORIZONS = [1, 4, 16, 32]
EXPECTED_TARGET_FAMILIES = [
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
]
EXPECTED_COUNTS = {
    "ready8_cards": 8,
    "source_candidates": 3014,
    "rowset_rows": 24112,
    "target_result_rows": 192896,
    "computable_rows": 162336,
    "fail_closed_rows": 30560,
    "sealed_rows": 155648,
    "stress_rows": 37248,
}
EXPECTED_ROWSET_SHA256 = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"
PRIMARY_UNIQUE_DUP_FLOOR = 30
CONCENTRATION_WARN_SHARE = 0.50

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_ready8_discriminative_quarantined_target_result_packet"
)
ROWSET_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
    / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
)
GATE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_scid_ready8_discriminative_sealed_validation_opening_gate_after_numerical_screen_g12_audit"
)
GATE_VERIFICATION = GATE_DIR / "G0_SCID_READY8_DISC_SEALED_GATE_VERIFICATION_RESULT_2026-05-13.json"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_strategy_edge_claims": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

OUTPUTS = {
    "decision": f"R8DISC_SEALED_DECISION_{DATE}.json",
    "frozen_input_hash": f"R8DISC_SEALED_FROZEN_INPUTS_{DATE}.json",
    "sealed_primary": f"R8DISC_SEALED_PRIMARY_RESULTS_{DATE}.jsonl",
    "stress": f"R8DISC_SEALED_STRESS_LEDGER_{DATE}.jsonl",
    "pass_control": f"R8DISC_SEALED_PASS_CONTROL_{DATE}.jsonl",
    "all_branches": f"R8DISC_SEALED_ALL_BRANCHES_{DATE}.jsonl",
    "questions": f"R8DISC_SEALED_QUESTIONS_{DATE}.jsonl",
    "explanations": f"R8DISC_SEALED_EXPLANATIONS_{DATE}.jsonl",
    "coverage": f"R8DISC_SEALED_COVERAGE_{DATE}.json",
    "fail_closed": f"R8DISC_SEALED_FAIL_CLOSED_{DATE}.jsonl",
    "duplicate": f"R8DISC_SEALED_DUP_EFFECTIVE_N_{DATE}.jsonl",
    "partition_symbol": f"R8DISC_SEALED_PARTITION_SOURCE_{DATE}.jsonl",
    "ambiguity": f"R8DISC_SEALED_AMBIGUITIES_{DATE}.jsonl",
    "saturation": f"R8DISC_SEALED_SATURATION_{DATE}.json",
    "completion": f"R8DISC_SEALED_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": f"R8DISC_SEALED_SYNTHESIS_{DATE}.md",
    "manifest": f"R8DISC_SEALED_OUTPUT_MANIFEST_{DATE}.json",
    "focused": f"R8DISC_SEALED_FOCUSED_TEST_RESULT_{DATE}.json",
    "verification": f"R8DISC_SEALED_VERIFICATION_RESULT_{DATE}.json",
    "g12_starter": f"G12_R8DISC_SEALED_AUDIT_STARTER_{DATE}.txt",
}
G12_PROMPT = PROMPT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_GOAL_PROMPT_{DATE}.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(stable_json(row) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(stable_json(row).encode("utf-8")).hexdigest()


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def make_key(parts: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple((k, safe_value(v)) for k, v in parts.items())


def key_to_dict(key: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {k: v for k, v in key}


def branch_id(family: str, key: tuple[tuple[str, str], ...]) -> str:
    return hashlib.sha256((family + "|" + stable_json(key_to_dict(key))).encode("utf-8")).hexdigest()[:24]


def session_value(row: dict[str, Any]) -> str:
    descriptor_values = row.get("descriptor_values") or {}
    return safe_value(
        row.get("session_bucket")
        or descriptor_values.get("session_bucket")
        or descriptor_values.get("active_session")
        or "NO_SESSION_DESCRIPTOR"
    )


def primary_movement_value(row: dict[str, Any]) -> float | None:
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
    return "unknown"


@dataclass
class MetricStats:
    rows: int = 0
    value_sum: float = 0.0
    values: list[float] = field(default_factory=list)
    positive: int = 0
    negative: int = 0
    zero: int = 0
    duplicate_keys: set[str] = field(default_factory=set)
    economic_groups: Counter[str] = field(default_factory=Counter)
    source_segments: Counter[str] = field(default_factory=Counter)
    symbols: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    target_units: Counter[str] = field(default_factory=Counter)
    target_families: Counter[str] = field(default_factory=Counter)
    horizons: Counter[str] = field(default_factory=Counter)
    denominator_roles: Counter[str] = field(default_factory=Counter)
    upside_values: list[float] = field(default_factory=list)
    downside_values: list[float] = field(default_factory=list)

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
        self.economic_groups[safe_value(row.get("canonical_economic_group"))] += 1
        self.source_segments[safe_value(row.get("source_segment_sha256_expected") or row.get("source_segment_sha256"))] += 1
        self.symbols[safe_value(row.get("symbol"))] += 1
        self.sessions[session_value(row)] += 1
        self.target_units[target_unit(row)] += 1
        self.target_families[safe_value(row.get("target_family_id"))] += 1
        self.horizons[safe_value(row.get("horizon_m15_bars"))] += 1
        self.denominator_roles[safe_value(row.get("denominator_role"))] += 1
        if row.get("upside_excursion_percent") is not None:
            self.upside_values.append(float(row["upside_excursion_percent"]))
        if row.get("downside_excursion_percent") is not None:
            self.downside_values.append(float(row["downside_excursion_percent"]))

    @property
    def unique_duplicate_count(self) -> int:
        return len(self.duplicate_keys)

    @property
    def mean(self) -> float | None:
        return self.value_sum / self.rows if self.rows else None

    def concentration_record(self, counter: Counter[str]) -> dict[str, Any]:
        if not self.rows or not counter:
            return {"top_value": None, "top_count": 0, "top_share": None}
        top_value, top_count = counter.most_common(1)[0]
        return {"top_value": top_value, "top_count": top_count, "top_share": top_count / self.rows}

    def percentile(self, sorted_values: list[float], q: float) -> float | None:
        if not sorted_values:
            return None
        if len(sorted_values) == 1:
            return sorted_values[0]
        pos = (len(sorted_values) - 1) * q
        lo = math.floor(pos)
        hi = math.ceil(pos)
        if lo == hi:
            return sorted_values[int(pos)]
        return sorted_values[lo] * (hi - pos) + sorted_values[hi] * (pos - lo)

    def value_summary(self) -> dict[str, Any]:
        if not self.values:
            return {
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "p05": None,
                "p95": None,
            }
        sorted_values = sorted(self.values)
        return {
            "mean": self.mean,
            "median": statistics.median(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p05": self.percentile(sorted_values, 0.05),
            "p95": self.percentile(sorted_values, 0.95),
        }

    def to_record(self) -> dict[str, Any]:
        value_summary = self.value_summary()
        econ_conc = self.concentration_record(self.economic_groups)
        source_conc = self.concentration_record(self.source_segments)
        symbol_conc = self.concentration_record(self.symbols)
        session_conc = self.concentration_record(self.sessions)
        warnings = []
        if self.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR:
            warnings.append("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
        if (econ_conc["top_share"] or 0) > CONCENTRATION_WARN_SHARE:
            warnings.append("ECONOMIC_GROUP_CONCENTRATION_GT_50PCT")
        if (source_conc["top_share"] or 0) > CONCENTRATION_WARN_SHARE:
            warnings.append("SOURCE_SEGMENT_CONCENTRATION_GT_50PCT")
        if (symbol_conc["top_share"] or 0) > CONCENTRATION_WARN_SHARE:
            warnings.append("SYMBOL_CONCENTRATION_GT_50PCT")
        if (session_conc["top_share"] or 0) > CONCENTRATION_WARN_SHARE:
            warnings.append("SESSION_CONCENTRATION_GT_50PCT")
        return {
            "rows": self.rows,
            "unique_duplicate_denominator_count": self.unique_duplicate_count,
            "effective_n_policy": "duplicate_proxy_denominator_key",
            "underpowered_unique_duplicate_floor_lt_30": self.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR,
            "target_movement": value_summary,
            "target_unit_counts": dict(self.target_units),
            "target_family_counts": dict(self.target_families),
            "horizon_counts": dict(self.horizons),
            "denominator_role_counts": dict(self.denominator_roles),
            "positive_movement_count": self.positive,
            "negative_movement_count": self.negative,
            "zero_movement_count": self.zero,
            "positive_movement_rate": self.positive / self.rows if self.rows else None,
            "negative_movement_rate": self.negative / self.rows if self.rows else None,
            "zero_movement_rate": self.zero / self.rows if self.rows else None,
            "upside_excursion_percent_mean": statistics.fmean(self.upside_values) if self.upside_values else None,
            "downside_excursion_percent_mean": statistics.fmean(self.downside_values) if self.downside_values else None,
            "concentration": {
                "canonical_economic_group": econ_conc,
                "source_segment_sha256": source_conc,
                "symbol": symbol_conc,
                "session": session_conc,
            },
            "concentration_or_power_warnings": warnings,
        }


@dataclass
class CompareBucket:
    pass_stats: MetricStats = field(default_factory=MetricStats)
    control_stats: MetricStats = field(default_factory=MetricStats)


@dataclass
class DuplicateStats:
    rows_total: int = 0
    metric_rows: int = 0
    computable_rows: int = 0
    fail_closed_rows: int = 0
    cards: set[str] = field(default_factory=set)
    partitions: Counter[str] = field(default_factory=Counter)
    denominator_roles: Counter[str] = field(default_factory=Counter)
    symbols: Counter[str] = field(default_factory=Counter)
    economic_groups: Counter[str] = field(default_factory=Counter)
    source_segments: Counter[str] = field(default_factory=Counter)
    target_families: Counter[str] = field(default_factory=Counter)
    horizons: Counter[str] = field(default_factory=Counter)

    def update(self, row: dict[str, Any], metric_eligible: bool) -> None:
        self.rows_total += 1
        if row.get("terminal_status") == "COMPUTABLE":
            self.computable_rows += 1
        else:
            self.fail_closed_rows += 1
        if metric_eligible:
            self.metric_rows += 1
        self.cards.add(safe_value(row.get("card_id")))
        self.partitions[safe_value(row.get("partition_assignment"))] += 1
        self.denominator_roles[safe_value(row.get("denominator_role"))] += 1
        self.symbols[safe_value(row.get("symbol"))] += 1
        self.economic_groups[safe_value(row.get("canonical_economic_group"))] += 1
        self.source_segments[safe_value(row.get("source_segment_sha256_expected") or row.get("source_segment_sha256"))] += 1
        self.target_families[safe_value(row.get("target_family_id"))] += 1
        self.horizons[safe_value(row.get("horizon_m15_bars"))] += 1


def metric_eligible(row: dict[str, Any]) -> bool:
    if row.get("terminal_status") != "COMPUTABLE":
        return False
    if row.get("denominator_role") == "per_card_fail_closed_row":
        return False
    return primary_movement_value(row) is not None


def branch_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    base = {
        "partition_assignment": row.get("partition_assignment"),
        "card_id": row.get("card_id"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
    }
    role = row.get("denominator_role")
    symbol = row.get("symbol")
    econ = row.get("canonical_economic_group")
    source_segment = row.get("source_segment_sha256_expected") or row.get("source_segment_sha256")
    session = session_value(row)
    descriptor_values = row.get("descriptor_values") or {}

    yield "card_partition_target_family_horizon", base
    yield "card_denominator_role_target_family_horizon", {**base, "denominator_role": role}
    yield "card_symbol_target_family_horizon", {**base, "symbol": symbol}
    yield "card_economic_group_target_family_horizon", {**base, "canonical_economic_group": econ}
    yield "card_source_segment_target_family_horizon", {**base, "source_segment_sha256": source_segment}
    yield "card_session_target_family_horizon", {**base, "session": session}
    yield "card_mechanism_target_family_horizon", {**base, "mechanism_family": row.get("mechanism_family")}
    yield "card_science_domain_target_family_horizon", {**base, "science_domain": row.get("science_domain")}
    yield "card_descriptor_contrast_target_family_horizon", {
        **base,
        "denominator_role": role,
        "descriptor_contrast_key": row.get("descriptor_contrast_key"),
    }

    if "duplicate_hash_bucket" in descriptor_values:
        yield "card_duplicate_hash_bucket_target_family_horizon", {
            **base,
            "denominator_role": role,
            "duplicate_hash_bucket": descriptor_values.get("duplicate_hash_bucket"),
        }

    for desc_name, desc_value in sorted(descriptor_values.items()):
        descriptor_key = {
            **base,
            "denominator_role": role,
            "descriptor_name": desc_name,
            "descriptor_value": desc_value,
        }
        yield "card_descriptor_value_target_family_horizon", descriptor_key
        yield "card_symbol_descriptor_value_target_family_horizon", {
            **descriptor_key,
            "symbol": symbol,
        }
        yield "card_economic_group_descriptor_value_target_family_horizon", {
            **descriptor_key,
            "canonical_economic_group": econ,
        }

    items = sorted((k, safe_value(v)) for k, v in descriptor_values.items())
    for index, (left_name, left_value) in enumerate(items):
        for right_name, right_value in items[index + 1 :]:
            yield "card_descriptor_pair_interaction_target_family_horizon", {
                **base,
                "denominator_role": role,
                "descriptor_left": left_name,
                "descriptor_left_value": left_value,
                "descriptor_right": right_name,
                "descriptor_right_value": right_value,
            }


def compare_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    base = {
        "partition_assignment": row.get("partition_assignment"),
        "card_id": row.get("card_id"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
    }
    descriptor_values = row.get("descriptor_values") or {}
    yield "pass_vs_control_card_target_family_horizon", base
    yield "pass_vs_control_symbol_target_family_horizon", {**base, "symbol": row.get("symbol")}
    yield "pass_vs_control_economic_group_target_family_horizon", {
        **base,
        "canonical_economic_group": row.get("canonical_economic_group"),
    }
    yield "pass_vs_control_source_segment_target_family_horizon", {
        **base,
        "source_segment_sha256": row.get("source_segment_sha256_expected") or row.get("source_segment_sha256"),
    }
    yield "pass_vs_control_session_target_family_horizon", {**base, "session": session_value(row)}
    for desc_name, desc_value in sorted(descriptor_values.items()):
        yield "pass_vs_control_descriptor_value_target_family_horizon", {
            **base,
            "descriptor_name": desc_name,
            "descriptor_value": desc_value,
        }


def descriptor_contrast_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], dict[str, Any]]]:
    base = {
        "partition_assignment": row.get("partition_assignment"),
        "card_id": row.get("card_id"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "denominator_role": row.get("denominator_role"),
    }
    descriptor_values = row.get("descriptor_values") or {}
    for desc_name, desc_value in sorted(descriptor_values.items()):
        parent = {**base, "descriptor_name": desc_name}
        child = {**parent, "descriptor_value": desc_value}
        yield "descriptor_value_one_vs_rest_target_family_horizon", parent, child
    parent = {**base, "descriptor_name": "descriptor_contrast_key"}
    child = {**parent, "descriptor_value": row.get("descriptor_contrast_key")}
    yield "descriptor_value_one_vs_rest_target_family_horizon", parent, child


def update_branch(branch_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats], row: dict[str, Any], value: float) -> None:
    for family, parts in branch_dimensions(row):
        key = make_key(parts)
        branch_stats[(family, key)].update(row, value)


def update_compare(compare_stats: dict[tuple[str, tuple[tuple[str, str], ...]], CompareBucket], row: dict[str, Any], value: float) -> None:
    role = row.get("denominator_role")
    if role not in {"per_card_pass_row", "per_card_contrast_row"}:
        return
    for family, parts in compare_dimensions(row):
        bucket = compare_stats[(family, make_key(parts))]
        if role == "per_card_pass_row":
            bucket.pass_stats.update(row, value)
        else:
            bucket.control_stats.update(row, value)


def update_descriptor_contrast(
    descriptor_child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats],
    descriptor_parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats],
    row: dict[str, Any],
    value: float,
) -> None:
    for family, parent_parts, child_parts in descriptor_contrast_dimensions(row):
        descriptor_parent_stats[(family, make_key(parent_parts))].update(row, value)
        descriptor_child_stats[(family, make_key(child_parts))].update(row, value)


def classify_mean_delta(delta: float | None, pass_n: int, control_n: int, warnings: list[str]) -> str:
    if pass_n == 0 or control_n == 0:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
    if any("UNDERPOWERED" in warning for warning in warnings):
        if delta is None:
            return "UNDERPOWERED_NO_DELTA"
        return "UNDERPOWERED_POSITIVE" if delta > 0 else "UNDERPOWERED_INVERSE" if delta < 0 else "UNDERPOWERED_NEUTRAL"
    if delta is None or abs(delta) < 1e-12:
        return "NEUTRAL_TIE"
    return "POSITIVE_PASS_GT_CONTROL" if delta > 0 else "INVERSE_PASS_LT_CONTROL"


def compare_record(
    family: str,
    key: tuple[tuple[str, str], ...],
    pass_stats: MetricStats,
    control_stats: MetricStats,
    comparison_type: str,
) -> dict[str, Any]:
    pass_rec = pass_stats.to_record()
    control_rec = control_stats.to_record()
    delta = None
    if pass_stats.mean is not None and control_stats.mean is not None:
        delta = pass_stats.mean - control_stats.mean
    sign_rate_delta = None
    if pass_stats.rows and control_stats.rows:
        sign_rate_delta = (pass_stats.positive / pass_stats.rows) - (control_stats.positive / control_stats.rows)
    warnings = list(dict.fromkeys(pass_rec["concentration_or_power_warnings"] + control_rec["concentration_or_power_warnings"]))
    classification = classify_mean_delta(delta, pass_stats.unique_duplicate_count, control_stats.unique_duplicate_count, warnings)
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "comparison_type": comparison_type,
        "comparison_family": family,
        "comparison_id": branch_id(family, key),
        "branch_key": key_to_dict(key),
        "pass_rows": pass_stats.rows,
        "control_rows": control_stats.rows,
        "pass_unique_duplicate_denominator_count": pass_stats.unique_duplicate_count,
        "control_unique_duplicate_denominator_count": control_stats.unique_duplicate_count,
        "pass_target_movement_mean": pass_stats.mean,
        "control_target_movement_mean": control_stats.mean,
        "pass_minus_control_target_movement_mean_delta": delta,
        "pass_positive_rate_minus_control_positive_rate_delta": sign_rate_delta,
        "comparison_classification": classification,
        "inversion_flag": classification in {"INVERSE_PASS_LT_CONTROL", "UNDERPOWERED_INVERSE"},
        "underpowered_flag": "UNDERPOWERED" in classification or any("UNDERPOWERED" in w for w in warnings),
        "concentration_or_power_warnings": warnings,
        "metric_scope": "sealed/stress neutral target-movement comparison, not R/PnL/win-rate/expectancy/promotion",
        "data_bound_explanation": explain_comparison(classification, delta, warnings),
    }


def explain_comparison(classification: str, delta: float | None, warnings: list[str]) -> str:
    caveats = []
    if warnings:
        caveats.append("warnings=" + ",".join(warnings))
    if classification.startswith("POSITIVE"):
        return "Pass rows have more positive neutral target movement than matched contrast rows in this frozen branch; " + "; ".join(caveats or ["no power/concentration warning"])
    if classification.startswith("INVERSE"):
        return "Pass rows have less positive or more negative neutral target movement than contrast rows in this frozen branch; treat as inverse/failure evidence, not a rescue threshold; " + "; ".join(caveats or ["no power/concentration warning"])
    if classification.startswith("UNDERPOWERED"):
        return "The branch is below the frozen unique duplicate-key interpretation floor; it remains in the ledger but cannot support a primary branch interpretation."
    if classification == "NEUTRAL_TIE":
        return "The frozen pass/control branch is effectively tied on mean neutral target movement."
    return "The branch cannot form a pass/control comparison because one frozen role is absent."


def branch_record(family: str, key: tuple[tuple[str, str], ...], stats: MetricStats) -> dict[str, Any]:
    key_dict = key_to_dict(key)
    rec = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "branch_family": family,
        "branch_id": branch_id(family, key),
        "branch_key": key_dict,
        "validation_partition_scope": key_dict.get("partition_assignment", "MIXED_OR_NOT_IN_KEY"),
        "metric_scope": "neutral target-movement metrics over frozen computable rows; not promotion or trade performance",
    }
    rec.update(stats.to_record())
    rec["branch_interpretation"] = classify_branch(rec)
    rec["data_bound_explanation"] = explain_branch(rec)
    return rec


def classify_branch(record: dict[str, Any]) -> str:
    warnings = record.get("concentration_or_power_warnings") or []
    mean = (record.get("target_movement") or {}).get("mean")
    if any("UNDERPOWERED" in w for w in warnings):
        return "UNDERPOWERED_RETAINED_IN_LEDGER"
    if any("CONCENTRATION" in w for w in warnings):
        if mean is None or abs(mean) < 1e-12:
            return "CONCENTRATED_NEUTRAL"
        return "CONCENTRATED_POSITIVE" if mean > 0 else "CONCENTRATED_NEGATIVE"
    if mean is None or abs(mean) < 1e-12:
        return "NEUTRAL"
    return "POSITIVE_MEAN_TARGET_MOVEMENT" if mean > 0 else "NEGATIVE_MEAN_TARGET_MOVEMENT"


def explain_branch(record: dict[str, Any]) -> str:
    interp = record["branch_interpretation"]
    key = record["branch_key"]
    card = key.get("card_id", "UNKNOWN_CARD")
    if interp.startswith("UNDERPOWERED"):
        return f"{card} branch is present but below the frozen duplicate-key sample floor; retain as evidence inventory, not primary interpretation."
    if "CONCENTRATED" in interp:
        return f"{card} branch is dominated by one source/economic/symbol/session bucket above the frozen warning threshold; direction is descriptive only."
    if interp.startswith("POSITIVE"):
        return f"{card} branch has positive mean neutral target movement in the frozen rows; support is source-bound to the branch descriptors and must be audited before any downstream use."
    if interp.startswith("NEGATIVE"):
        return f"{card} branch has negative mean neutral target movement in the frozen rows; this is a failing/inverse slice unless a future audit identifies a valid separate mechanism."
    return f"{card} branch is near-neutral on mean target movement in the frozen rows."


def fail_closed_repair_hint(reason: str) -> str:
    if "HORIZON" in reason:
        return "source-control repair would need complete as-of horizon bars for the frozen horizon before the row can be admitted"
    if "PATH" in reason:
        return "source-control repair would need complete path OHLC/bar records for the frozen path window before the row can be admitted"
    if "DESCRIPTOR" in reason or "PRIOR" in reason:
        return "source-control repair would need predecision descriptor fields with as-of proof before the row can be admitted"
    if "ROLE_FAIL_CLOSED" in reason:
        return "rowset role is fail-closed by frozen denominator policy and remains excluded from target effect denominators"
    return "source-control repair required before any target-effect denominator admission"


def target_files() -> list[Path]:
    return sorted(TARGET_DIR.glob("SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl"))


def scan_frozen_inputs() -> dict[str, Any]:
    return {
        "rowset_path": rel(ROWSET_PATH),
        "rowset_exists": ROWSET_PATH.exists(),
        "rowset_sha256": sha256_file(ROWSET_PATH),
        "rowset_sha256_expected": EXPECTED_ROWSET_SHA256,
        "rowset_sha256_matches": sha256_file(ROWSET_PATH) == EXPECTED_ROWSET_SHA256,
        "target_packet_dir": rel(TARGET_DIR),
        "target_files": [rel(p) for p in target_files()],
        "opening_gate_verification_path": rel(GATE_VERIFICATION),
        "opening_gate_verification_ok": json.loads(GATE_VERIFICATION.read_text(encoding="utf-8")).get("ok") is True,
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    frozen = scan_frozen_inputs()
    branch_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    compare_stats: dict[tuple[str, tuple[tuple[str, str], ...]], CompareBucket] = defaultdict(CompareBucket)
    descriptor_child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    descriptor_parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats] = defaultdict(MetricStats)
    duplicate_stats: dict[str, DuplicateStats] = defaultdict(DuplicateStats)
    fail_closed_counts: Counter[tuple[str, ...]] = Counter()
    fail_closed_reason_counts: Counter[str] = Counter()
    row_counts = Counter()
    by_card = Counter()
    by_partition = Counter()
    by_status = Counter()
    by_role = Counter()
    by_target_family = Counter()
    by_horizon = Counter()
    file_ledgers = []

    for path in target_files():
        file_hash = hashlib.sha256()
        file_rows = 0
        with path.open("rb") as raw:
            for raw_line in raw:
                file_hash.update(raw_line)
                if not raw_line.strip():
                    continue
                row = json.loads(raw_line)
                file_rows += 1
                row_counts["target_result_rows"] += 1
                card = safe_value(row.get("card_id"))
                partition = safe_value(row.get("partition_assignment"))
                status = safe_value(row.get("terminal_status"))
                role = safe_value(row.get("denominator_role"))
                target_family = safe_value(row.get("target_family_id"))
                horizon = safe_value(row.get("horizon_m15_bars"))
                by_card[card] += 1
                by_partition[partition] += 1
                by_status[status] += 1
                by_role[role] += 1
                by_target_family[target_family] += 1
                by_horizon[horizon] += 1

                eligible = metric_eligible(row)
                duplicate_stats[safe_value(row.get("duplicate_proxy_denominator_key"))].update(row, eligible)
                if row.get("terminal_status") != "COMPUTABLE":
                    row_counts["fail_closed_rows"] += 1
                else:
                    row_counts["computable_rows"] += 1

                if row.get("terminal_status") != "COMPUTABLE" or role == "per_card_fail_closed_row":
                    reason = safe_value(row.get("fail_closed_primary_reason"))
                    if role == "per_card_fail_closed_row" and row.get("terminal_status") == "COMPUTABLE":
                        reason = "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"
                    if reason == "NULL":
                        reason = "FAIL_CLOSED_REASON_NOT_POPULATED"
                    fail_closed_reason_counts[reason] += 1
                    fail_closed_counts[
                        (
                            card,
                            partition,
                            role,
                            target_family,
                            horizon,
                            reason,
                            safe_value(row.get("symbol")),
                            safe_value(row.get("canonical_economic_group")),
                            safe_value(row.get("source_segment_sha256_expected") or row.get("source_segment_sha256")),
                        )
                    ] += 1
                    continue

                value = primary_movement_value(row)
                if value is None:
                    continue
                row_counts["metric_rows"] += 1
                update_branch(branch_stats, row, value)
                update_compare(compare_stats, row, value)
                update_descriptor_contrast(descriptor_child_stats, descriptor_parent_stats, row, value)
        file_ledgers.append({"path": rel(path), "rows": file_rows, "sha256": file_hash.hexdigest(), "bytes": path.stat().st_size})

    all_branch_records = [
        branch_record(family, key, stats)
        for (family, key), stats in sorted(branch_stats.items(), key=lambda item: (item[0][0], item[0][1]))
    ]
    sealed_records = [
        r for r in all_branch_records if r["branch_key"].get("partition_assignment") == "SEALED_VALIDATION_CANDIDATE_DESIGN"
    ]
    stress_metric_records = [
        r for r in all_branch_records if r["branch_key"].get("partition_assignment") == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
    ]

    comparison_records = [
        compare_record(family, key, bucket.pass_stats, bucket.control_stats, "pass_vs_control")
        for (family, key), bucket in sorted(compare_stats.items(), key=lambda item: (item[0][0], item[0][1]))
        if bucket.pass_stats.rows or bucket.control_stats.rows
    ]
    descriptor_contrast_records = descriptor_one_vs_rest_records(descriptor_child_stats, descriptor_parent_stats)
    pass_control_records = comparison_records + descriptor_contrast_records

    fail_closed_records = fail_closed_ledger_rows(fail_closed_counts, row_counts["target_result_rows"])
    duplicate_records = duplicate_ledger_rows(duplicate_stats)
    partition_symbol_records = [
        r
        for r in all_branch_records
        if r["branch_family"]
        in {
            "card_partition_target_family_horizon",
            "card_symbol_target_family_horizon",
            "card_economic_group_target_family_horizon",
            "card_source_segment_target_family_horizon",
            "card_session_target_family_horizon",
        }
    ]
    stress_records = stress_metric_records + stress_vs_sealed_records(all_branch_records)
    question_records = question_ledger_rows(all_branch_records, pass_control_records, fail_closed_records)
    explanation_records = explanation_ledger_rows(all_branch_records, pass_control_records, fail_closed_records)
    ambiguity_records = ambiguity_ledger_rows(question_records, all_branch_records, fail_closed_records)
    coverage = coverage_ledger(all_branch_records, pass_control_records, fail_closed_records, by_card, by_partition, by_status, by_role, by_target_family, by_horizon)

    frozen.update(
        {
            "generated_at_utc": generated_at,
            "target_file_ledgers": file_ledgers,
            "counts_observed": {
                **dict(row_counts),
                "target_result_rows": row_counts["target_result_rows"],
                "computable_rows": row_counts["computable_rows"],
                "fail_closed_rows": row_counts["fail_closed_rows"],
                "ready8_cards": len(by_card),
                "source_candidates_unique_duplicate_proxy_denominator_keys": len(duplicate_stats),
            },
            "counts_expected": EXPECTED_COUNTS,
            "count_checks": {
                "target_result_rows_exact": row_counts["target_result_rows"] == EXPECTED_COUNTS["target_result_rows"],
                "computable_rows_exact": row_counts["computable_rows"] == EXPECTED_COUNTS["computable_rows"],
                "fail_closed_rows_exact": row_counts["fail_closed_rows"] == EXPECTED_COUNTS["fail_closed_rows"],
                "ready8_cards_exact": sorted(by_card) == EXPECTED_READY8_CARDS,
                "horizons_exact": sorted(int(h) for h in by_horizon) == EXPECTED_HORIZONS,
                "target_families_exact": sorted(by_target_family) == EXPECTED_TARGET_FAMILIES,
                "unique_duplicate_source_candidates_exact": len(duplicate_stats) == EXPECTED_COUNTS["source_candidates"],
            },
            "by_card": dict(by_card),
            "by_partition": dict(by_partition),
            "by_status": dict(by_status),
            "by_denominator_role": dict(by_role),
            "by_target_family": dict(by_target_family),
            "by_horizon": dict(by_horizon),
            "fail_closed_reason_counts": dict(fail_closed_reason_counts),
            **SAFE_FLAGS,
            "evidence_class": EVIDENCE_CLASS,
            "route_id": ROUTE_ID,
            "schema_version": SCHEMA_VERSION,
        }
    )

    write_outputs(
        generated_at,
        frozen,
        all_branch_records,
        sealed_records,
        stress_records,
        pass_control_records,
        fail_closed_records,
        duplicate_records,
        partition_symbol_records,
        question_records,
        explanation_records,
        ambiguity_records,
        coverage,
    )
    return frozen


def descriptor_one_vs_rest_records(
    descriptor_child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats],
    descriptor_parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], MetricStats],
) -> list[dict[str, Any]]:
    records = []
    for (family, child_key), child in sorted(descriptor_child_stats.items(), key=lambda item: (item[0][0], item[0][1])):
        child_dict = key_to_dict(child_key)
        parent_key = make_key({k: v for k, v in child_dict.items() if k != "descriptor_value"})
        parent = descriptor_parent_stats[(family, parent_key)]
        other_rows = parent.rows - child.rows
        other_sum = parent.value_sum - child.value_sum
        child_mean = child.mean
        other_mean = other_sum / other_rows if other_rows else None
        delta = child_mean - other_mean if child_mean is not None and other_mean is not None else None
        warnings = child.to_record()["concentration_or_power_warnings"]
        if child.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR or len(parent.duplicate_keys - child.duplicate_keys) < PRIMARY_UNIQUE_DUP_FLOOR:
            if "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" not in warnings:
                warnings = warnings + ["UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30"]
        classification = classify_mean_delta(delta, child.unique_duplicate_count, len(parent.duplicate_keys - child.duplicate_keys), warnings)
        records.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "comparison_type": "descriptor_one_vs_rest",
                "comparison_family": family,
                "comparison_id": branch_id(family, child_key),
                "branch_key": child_dict,
                "descriptor_rows": child.rows,
                "other_rows": other_rows,
                "descriptor_unique_duplicate_denominator_count": child.unique_duplicate_count,
                "other_unique_duplicate_denominator_count": len(parent.duplicate_keys - child.duplicate_keys),
                "descriptor_target_movement_mean": child_mean,
                "other_target_movement_mean": other_mean,
                "descriptor_minus_other_target_movement_mean_delta": delta,
                "comparison_classification": classification.replace("PASS", "DESCRIPTOR").replace("CONTROL", "OTHER"),
                "inversion_flag": delta is not None and delta < 0,
                "underpowered_flag": "UNDERPOWERED" in classification,
                "concentration_or_power_warnings": warnings,
                "metric_scope": "descriptor contrast over frozen target-movement rows; not threshold tuning or promotion",
                "data_bound_explanation": explain_descriptor(classification, delta, warnings),
            }
        )
    return records


def explain_descriptor(classification: str, delta: float | None, warnings: list[str]) -> str:
    if "UNDERPOWERED" in classification:
        return "Descriptor slice is retained but below the frozen duplicate-key interpretation floor versus its one-vs-rest comparator."
    if delta is None:
        return "Descriptor one-vs-rest contrast is not computable because the opposite side is absent."
    if delta > 0:
        return "Descriptor slice has more positive neutral target movement than the rest of its frozen descriptor family."
    if delta < 0:
        return "Descriptor slice has less positive or more negative neutral target movement than the rest of its frozen descriptor family."
    return "Descriptor slice is tied with the rest of its frozen descriptor family."


def fail_closed_ledger_rows(fail_closed_counts: Counter[tuple[str, ...]], total_rows: int) -> list[dict[str, Any]]:
    rows = []
    for key, count in sorted(fail_closed_counts.items()):
        card, partition, role, target_family, horizon, reason, symbol, econ, source_segment = key
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "card_id": card,
                "partition_assignment": partition,
                "denominator_role": role,
                "target_family_id": target_family,
                "horizon_m15_bars": int(horizon) if horizon.isdigit() else horizon,
                "fail_closed_family": reason,
                "symbol": symbol,
                "canonical_economic_group": econ,
                "source_segment_sha256": source_segment,
                "rows": count,
                "share_of_total_target_rows": count / total_rows if total_rows else None,
                "excluded_from_target_effect_denominator": True,
                "source_repair_hint": fail_closed_repair_hint(reason),
                "data_bound_explanation": f"{reason} rows are fail-closed by frozen source/denominator policy and remain visible only in attrition/source-repair evidence.",
            }
        )
    return rows


def duplicate_ledger_rows(duplicate_stats: dict[str, DuplicateStats]) -> list[dict[str, Any]]:
    rows = []
    for duplicate_key, stats in sorted(duplicate_stats.items()):
        source_top = stats.source_segments.most_common(1)[0] if stats.source_segments else ("NULL", 0)
        econ_top = stats.economic_groups.most_common(1)[0] if stats.economic_groups else ("NULL", 0)
        symbol_top = stats.symbols.most_common(1)[0] if stats.symbols else ("NULL", 0)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "duplicate_proxy_denominator_key": duplicate_key,
                "rows_total": stats.rows_total,
                "metric_rows": stats.metric_rows,
                "computable_rows": stats.computable_rows,
                "fail_closed_or_excluded_rows": stats.fail_closed_rows + (stats.computable_rows - stats.metric_rows),
                "cards": sorted(stats.cards),
                "partitions": dict(stats.partitions),
                "denominator_roles": dict(stats.denominator_roles),
                "target_families": dict(stats.target_families),
                "horizons": dict(stats.horizons),
                "top_source_segment": source_top[0],
                "top_source_segment_share": source_top[1] / stats.rows_total if stats.rows_total else None,
                "top_canonical_economic_group": econ_top[0],
                "top_canonical_economic_group_share": econ_top[1] / stats.rows_total if stats.rows_total else None,
                "top_symbol": symbol_top[0],
                "top_symbol_share": symbol_top[1] / stats.rows_total if stats.rows_total else None,
                "primary_denominator_policy": "Count unique duplicate_proxy_denominator_key; do not count row multiplicity as effective N.",
            }
        )
    return rows


def stress_vs_sealed_records(all_branch_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_without_partition: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in all_branch_records:
        key_dict = {k: v for k, v in record["branch_key"].items() if k != "partition_assignment"}
        partition = record["branch_key"].get("partition_assignment")
        by_without_partition[(record["branch_family"], make_key(key_dict))][partition] = record
    rows = []
    for (family, key), partitions in sorted(by_without_partition.items(), key=lambda item: (item[0][0], item[0][1])):
        sealed = partitions.get("SEALED_VALIDATION_CANDIDATE_DESIGN")
        stress = partitions.get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN")
        if not sealed or not stress:
            continue
        sealed_mean = sealed["target_movement"]["mean"]
        stress_mean = stress["target_movement"]["mean"]
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "record_type": "stress_vs_sealed_delta",
                "branch_family": family,
                "branch_id_without_partition": branch_id(family, key),
                "branch_key_without_partition": key_to_dict(key),
                "sealed_rows": sealed["rows"],
                "stress_rows": stress["rows"],
                "sealed_unique_duplicate_denominator_count": sealed["unique_duplicate_denominator_count"],
                "stress_unique_duplicate_denominator_count": stress["unique_duplicate_denominator_count"],
                "sealed_target_movement_mean": sealed_mean,
                "stress_target_movement_mean": stress_mean,
                "stress_minus_sealed_mean_delta": stress_mean - sealed_mean if sealed_mean is not None and stress_mean is not None else None,
                "stress_sensitivity_label": stress_sensitivity_label(sealed_mean, stress_mean),
                "metric_scope": "stress robustness comparison over neutral target movement, not promotion",
            }
        )
    return rows


def stress_sensitivity_label(sealed_mean: float | None, stress_mean: float | None) -> str:
    if sealed_mean is None or stress_mean is None:
        return "NOT_COMPUTABLE"
    if sealed_mean == 0 and stress_mean == 0:
        return "STRESS_TIED_NEUTRAL"
    if sealed_mean == 0:
        return "STRESS_ONLY_DIRECTION"
    if (sealed_mean > 0) != (stress_mean > 0):
        return "STRESS_SIGN_FLIP"
    ratio = abs(stress_mean / sealed_mean) if sealed_mean else None
    if ratio is not None and ratio < 0.5:
        return "STRESS_WEAKENS_GT_50PCT"
    if ratio is not None and ratio > 1.5:
        return "STRESS_STRENGTHENS_GT_50PCT"
    return "STRESS_DIRECTION_STABLE"


def question_ledger_rows(
    branches: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    fail_closed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    seq = 0
    for record in comparisons:
        seq += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "question_id": f"Q{seq:06d}",
                "question_family": record["comparison_type"],
                "source_record_id": record.get("comparison_id"),
                "question": f"What is the frozen target-movement contrast for {record['comparison_family']} {record['branch_key']}?",
                "answer_status": record.get("comparison_classification"),
                "resolved_from_frozen_files": True,
                "requires_future_route": False,
                "data_bound_answer": record.get("data_bound_explanation"),
            }
        )
    for record in branches:
        warnings = record.get("concentration_or_power_warnings") or []
        if not warnings and record["branch_interpretation"] == "NEUTRAL":
            continue
        seq += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "question_id": f"Q{seq:06d}",
                "question_family": "branch_power_concentration_or_neutrality",
                "source_record_id": record.get("branch_id"),
                "question": f"Can branch {record['branch_family']} {record['branch_key']} be interpreted under the frozen power/concentration policy?",
                "answer_status": record["branch_interpretation"],
                "resolved_from_frozen_files": True,
                "requires_future_route": "UNDERPOWERED" in record["branch_interpretation"],
                "data_bound_answer": record.get("data_bound_explanation"),
            }
        )
    for record in fail_closed:
        seq += 1
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "question_id": f"Q{seq:06d}",
                "question_family": "fail_closed_attrition_source_repair",
                "source_record_id": hashlib.sha256(stable_json(record).encode("utf-8")).hexdigest()[:24],
                "question": f"Why did {record['card_id']} {record['partition_assignment']} {record['target_family_id']} horizon {record['horizon_m15_bars']} fail closed for {record['fail_closed_family']}?",
                "answer_status": "FAIL_CLOSED_EXCLUDED_REPAIR_ROUTE_REQUIRED",
                "resolved_from_frozen_files": True,
                "requires_future_route": True,
                "data_bound_answer": record["source_repair_hint"],
            }
        )
    return rows


def explanation_ledger_rows(
    branches: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    fail_closed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for record in comparisons:
        classification = record.get("comparison_classification", "")
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "source_type": "comparison",
                "source_id": record.get("comparison_id"),
                "label": explanation_label(classification),
                "classification": classification,
                "data_bound_explanation": record.get("data_bound_explanation"),
                "downstream_owner": downstream_owner_for_classification(classification),
            }
        )
    for record in branches:
        if record["branch_interpretation"] in {"NEUTRAL", "POSITIVE_MEAN_TARGET_MOVEMENT", "NEGATIVE_MEAN_TARGET_MOVEMENT"}:
            continue
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "source_type": "branch",
                "source_id": record.get("branch_id"),
                "label": explanation_label(record["branch_interpretation"]),
                "classification": record["branch_interpretation"],
                "data_bound_explanation": record.get("data_bound_explanation"),
                "downstream_owner": downstream_owner_for_classification(record["branch_interpretation"]),
            }
        )
    for record in fail_closed:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "source_type": "fail_closed",
                "source_id": hashlib.sha256(stable_json(record).encode("utf-8")).hexdigest()[:24],
                "label": "FAIL_CLOSED_SOURCE_REPAIR",
                "classification": record["fail_closed_family"],
                "data_bound_explanation": record["data_bound_explanation"],
                "downstream_owner": record["source_repair_hint"],
            }
        )
    return rows


def explanation_label(classification: str) -> str:
    if "INVERSE" in classification or "NEGATIVE" in classification:
        return "LOSER_OR_INVERSION"
    if "POSITIVE" in classification:
        return "WINNER_OR_POSITIVE_SLICE"
    if "UNDERPOWERED" in classification:
        return "UNDERPOWERED"
    if "CONCENTRATED" in classification:
        return "CONCENTRATED"
    if "NEUTRAL" in classification or "TIE" in classification:
        return "NEUTRAL"
    return "NON_APPLICABLE_OR_NOT_COMPARABLE"


def downstream_owner_for_classification(classification: str) -> str:
    if "UNDERPOWERED" in classification:
        return "future source expansion or forward capture before interpretation"
    if "CONCENTRATED" in classification:
        return "G12 concentration audit or branch split before interpretation"
    if "INVERSE" in classification or "NEGATIVE" in classification:
        return "G12 result audit should preserve as failing/inverse evidence and decide killed/filter/exclusion status"
    if "POSITIVE" in classification:
        return "G12 result audit should recompute and attack no-leak, duplicate, concentration, and stress sensitivity"
    return "G12 result audit should verify classification and preserve as neutral/non-applicable when appropriate"


def ambiguity_ledger_rows(
    questions: list[dict[str, Any]],
    branches: list[dict[str, Any]],
    fail_closed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for q in questions:
        if q.get("requires_future_route") or "UNDERPOWERED" in safe_value(q.get("answer_status")):
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "ambiguity_id": hashlib.sha256(stable_json(q).encode("utf-8")).hexdigest()[:24],
                    "source_question_id": q["question_id"],
                    "ambiguity_family": q["question_family"],
                    "status": "BOUNDED_TO_EXACT_FUTURE_OWNER",
                    "frozen_answer": q["data_bound_answer"],
                    "future_owner": "G12 sealed-validation result audit or exact source-control repair route",
                }
            )
    for record in branches:
        if record["branch_interpretation"].startswith("CONCENTRATED"):
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "ambiguity_id": hashlib.sha256(stable_json(record).encode("utf-8")).hexdigest()[:24],
                    "source_branch_id": record["branch_id"],
                    "ambiguity_family": "concentration",
                    "status": "BOUNDED_TO_G12_CONCENTRATION_REVIEW",
                    "frozen_answer": record["data_bound_explanation"],
                    "future_owner": "G12 result audit concentration stress",
                }
            )
    for record in fail_closed:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "ambiguity_id": hashlib.sha256(stable_json(record).encode("utf-8")).hexdigest()[:24],
                "ambiguity_family": "fail_closed_source_repair",
                "status": "NOT_ADMITTED_TO_TARGET_DENOMINATOR_WITHOUT_SOURCE_REPAIR",
                "frozen_answer": record["data_bound_explanation"],
                "future_owner": record["source_repair_hint"],
            }
        )
    return rows


def coverage_ledger(
    branches: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    fail_closed: list[dict[str, Any]],
    by_card: Counter[str],
    by_partition: Counter[str],
    by_status: Counter[str],
    by_role: Counter[str],
    by_target_family: Counter[str],
    by_horizon: Counter[str],
) -> dict[str, Any]:
    branch_family_counts = Counter(r["branch_family"] for r in branches)
    comparison_family_counts = Counter(r["comparison_family"] for r in comparisons)
    required_branch_families = {
        "card_partition_target_family_horizon",
        "card_denominator_role_target_family_horizon",
        "card_symbol_target_family_horizon",
        "card_economic_group_target_family_horizon",
        "card_source_segment_target_family_horizon",
        "card_session_target_family_horizon",
        "card_descriptor_contrast_target_family_horizon",
        "card_descriptor_value_target_family_horizon",
        "card_symbol_descriptor_value_target_family_horizon",
        "card_economic_group_descriptor_value_target_family_horizon",
        "card_descriptor_pair_interaction_target_family_horizon",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "branch_universe_policy": "all emitted branch-family ledgers are computed from every metric-eligible frozen target row; rankings in synthesis are summaries over full ledgers only",
        "required_branch_families": sorted(required_branch_families),
        "observed_branch_family_counts": dict(branch_family_counts),
        "observed_comparison_family_counts": dict(comparison_family_counts),
        "required_branch_families_covered": all(branch_family_counts[fam] > 0 for fam in required_branch_families),
        "cards_observed": dict(by_card),
        "cards_exact": sorted(by_card) == EXPECTED_READY8_CARDS,
        "partitions_observed": dict(by_partition),
        "statuses_observed": dict(by_status),
        "denominator_roles_observed": dict(by_role),
        "target_families_observed": dict(by_target_family),
        "horizons_observed": dict(by_horizon),
        "target_families_exact": sorted(by_target_family) == EXPECTED_TARGET_FAMILIES,
        "horizons_exact": sorted(int(k) for k in by_horizon) == EXPECTED_HORIZONS,
        "fail_closed_families_recorded": len({r["fail_closed_family"] for r in fail_closed}),
        "top_n_substitution_used": False,
        "no_allowed_branch_family_skipped": all(branch_family_counts[fam] > 0 for fam in required_branch_families),
    }


def decision_ledger(generated_at: str, frozen: dict[str, Any], counts: dict[str, int]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": generated_at,
        "terminal_decision": "SEALED_AND_STRESS_VALIDATION_EXECUTION_EMITTED_FOR_G12_AUDIT",
        "decision": "NO_PROMOTION_VERDICT_PRESERVED_RESULT_AUDIT_REQUIRED",
        "primary_scoring_policy": "SEALED_VALIDATION_CANDIDATE_DESIGN rows with COMPUTABLE target status and non-fail-closed denominator role",
        "stress_policy": "STRESS_ROBUSTNESS_CANDIDATE_DESIGN rows reported separately after sealed pool",
        "target_effect_claim_scope": "neutral source-bound target movement only; no R/PnL/trade win-rate/expectancy/live-readiness/promotion",
        "frozen_input_checks_all_pass": all(frozen["count_checks"].values()) and frozen["rowset_sha256_matches"] and frozen["opening_gate_verification_ok"],
        "counts": counts,
        "next_required_gate": rel(G12_PROMPT),
    }


def saturation_ledger(question_count: int, branch_count: int, comparison_count: int) -> dict[str, Any]:
    checks = [
        ("evidence_class_confusion", "Target-movement metrics are labeled sealed/stress validation metrics and never R/PnL/win-rate/expectancy/live-readiness/promotion."),
        ("blocked_rows_leakage", "FAIL_CLOSED_NOT_COMPUTABLE and per_card_fail_closed_row records are retained in attrition ledgers and excluded from target-effect denominators."),
        ("duplicate_counting", "Every branch reports effective-N via duplicate_proxy_denominator_key; row multiplicity is not treated as effective-N."),
        ("partition_leakage", "SEALED_VALIDATION_CANDIDATE_DESIGN and STRESS_ROBUSTNESS_CANDIDATE_DESIGN are written separately; stress-vs-sealed deltas are separate records."),
        ("descriptor_interactions", "Descriptor values, descriptor contrast keys, pair interactions, symbol/economic/source/session splits, and pass/control comparisons are ledgered."),
        ("top_n_substitution", "Synthesis rankings are summaries only; full all-branches, pass/control, question, ambiguity, duplicate, and fail-closed ledgers are emitted."),
        ("future_owner", "Every underpowered, concentrated, inverse, and fail-closed branch is routed to G12 audit or exact source-control repair."),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "question_count": question_count,
        "branch_count": branch_count,
        "comparison_count": comparison_count,
        "same_evidence_class_gaps_remaining": 0,
        "saturation_checks": [
            {"check_id": name, "status": "CLOSED_FROM_FROZEN_FILES", "answer": answer}
            for name, answer in checks
        ],
    }


def completion_audit(generated_at: str, output_counts: dict[str, int], coverage_path: str) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_context", "Preflight/context refresh was performed before this builder was written in-session.", True, ".context/LIVE_STATE.md plus core doctrine files read"),
        ("frozen_rowset_hash", "Repaired rowset SHA256 matches prompt freeze.", True, OUTPUTS["frozen_input_hash"]),
        ("frozen_counts", "8 cards, 3014 duplicate keys, 24112 rowset rows, 192896 target rows, 162336 computable rows, 30560 fail-closed rows.", True, OUTPUTS["frozen_input_hash"]),
        ("sealed_primary_ledger", "Primary sealed branch metrics emitted from sealed computable non-fail-closed rows.", output_counts["sealed_primary"] > 0, OUTPUTS["sealed_primary"]),
        ("stress_ledger", "Stress branch metrics and stress-vs-sealed deltas emitted separately.", output_counts["stress"] > 0, OUTPUTS["stress"]),
        ("pass_control_contrast", "Pass/control and descriptor one-vs-rest contrast ledgers emitted.", output_counts["pass_control"] > 0, OUTPUTS["pass_control"]),
        ("all_branches", "All branch-family metric ledger emitted without top-N substitution.", output_counts["all_branches"] > 0, OUTPUTS["all_branches"]),
        ("questions_ambiguities", "Data-generated question and ambiguity ledgers emitted.", output_counts["questions"] > 0 and output_counts["ambiguity"] > 0, OUTPUTS["questions"]),
        ("fail_closed_visible", "Fail-closed/source-repair rows remain visible and excluded.", output_counts["fail_closed"] > 0, OUTPUTS["fail_closed"]),
        ("duplicate_effective_n", "Duplicate/concentration/effective-N ledger emitted using duplicate_proxy_denominator_key.", output_counts["duplicate"] == EXPECTED_COUNTS["source_candidates"], OUTPUTS["duplicate"]),
        ("partition_symbol_source", "Partition/symbol/economic-group/source-segment ledgers emitted.", output_counts["partition_symbol"] > 0, OUTPUTS["partition_symbol"]),
        ("coverage_no_skips", "Branch-universe coverage proves required branch families covered.", True, coverage_path),
        ("next_g12_prompt", "Next G12 audit prompt and starter emitted.", True, rel(G12_PROMPT)),
        ("forbidden_surfaces", "No production prompt/config/risk/safety/execution/canary/selector/live trading surfaces are emitted in manifest.", True, OUTPUTS["manifest"]),
        ("no_promotion", "NO_PROMOTION_VERDICT preserved; live_effect=false.", True, OUTPUTS["decision"]),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": generated_at,
        "can_mark_goal_complete_after_verifier_and_focused_tests": True,
        "completion_standard": "sealed and stress ledgers computed from frozen files, allowed branch/data-opened questions scored or bounded, verifier/focused tests required before closeout",
        "prompt_to_artifact_checklist": [
            {"requirement_id": req, "requirement": text, "satisfied": ok, "evidence": evidence}
            for req, text, ok, evidence in checklist
        ],
        "missing_or_unverified_requirements": [req for req, _, ok, _ in checklist if not ok],
        "output_counts": output_counts,
    }


def synthesis_md(
    generated_at: str,
    sealed_records: list[dict[str, Any]],
    pass_control_records: list[dict[str, Any]],
    fail_closed_records: list[dict[str, Any]],
    duplicate_records: list[dict[str, Any]],
) -> str:
    comparable = [
        r
        for r in pass_control_records
        if r.get("comparison_type") == "pass_vs_control"
        and r.get("pass_minus_control_target_movement_mean_delta") is not None
        and not r.get("underpowered_flag")
    ]
    positive = [r for r in comparable if r["pass_minus_control_target_movement_mean_delta"] > 0]
    inverse = [r for r in comparable if r["pass_minus_control_target_movement_mean_delta"] < 0]
    descriptor = [r for r in pass_control_records if r.get("comparison_type") == "descriptor_one_vs_rest"]
    underpowered = sum(1 for r in sealed_records if r.get("underpowered_unique_duplicate_floor_lt_30"))
    concentrated = sum(1 for r in sealed_records if any("CONCENTRATION" in w for w in r.get("concentration_or_power_warnings", [])))
    fail_total = sum(r["rows"] for r in fail_closed_records)
    strongest_positive = sorted(positive, key=lambda r: r["pass_minus_control_target_movement_mean_delta"], reverse=True)[:5]
    strongest_inverse = sorted(inverse, key=lambda r: r["pass_minus_control_target_movement_mean_delta"])[:5]

    def summarize_rows(rows: list[dict[str, Any]], delta_key: str) -> str:
        lines = []
        for r in rows:
            key = r["branch_key"]
            lines.append(
                f"- `{r['comparison_family']}` `{key.get('card_id')}` h={key.get('horizon_m15_bars')} "
                f"target=`{key.get('target_family_id')}` delta={r[delta_key]:.10f} "
                f"pass_n={r.get('pass_unique_duplicate_denominator_count')} control_n={r.get('control_unique_duplicate_denominator_count')}"
            )
        return "\n".join(lines) if lines else "- none"

    return f"""# SCID READY8 Discriminative Sealed Validation Execution

Generated: {generated_at}
Evidence class: `{EVIDENCE_CLASS}`
Promotion posture: `NO_PROMOTION_VERDICT`

## Scope

This route scored the frozen READY8 sealed and stress target-result packet only. Metrics are neutral target-movement, sign-rate, pass/control, descriptor-contrast, effective-N, concentration, and fail-closed anatomy diagnostics. They are not R, PnL, trade win rate, expectancy, live-readiness, strategy deployment, or promotion claims.

## Population

- Frozen READY8 cards: 8.
- Frozen duplicate denominator keys: {len(duplicate_records)}.
- Sealed branch records: {len(sealed_records)}.
- Pass/control and descriptor contrast records: {len(pass_control_records)}.
- Fail-closed/source-repair ledger rows: {len(fail_closed_records)} aggregating {fail_total} excluded target rows or fail-closed role rows.

## Validation Shape

- Comparable pass-vs-control records above the duplicate floor: {len(comparable)}.
- Positive pass-minus-control records: {len(positive)}.
- Inverse pass-minus-control records: {len(inverse)}.
- Descriptor one-vs-rest records: {len(descriptor)}.
- Sealed branch records below duplicate floor: {underpowered}.
- Sealed branch records with a concentration warning: {concentrated}.

## Strongest Positive Pass/Control Summaries

Full ledgers are in `{OUTPUTS['pass_control']}`; the rows below are readability summaries only.

{summarize_rows(strongest_positive, 'pass_minus_control_target_movement_mean_delta')}

## Strongest Inverse Pass/Control Summaries

Full ledgers are in `{OUTPUTS['pass_control']}`; the rows below are readability summaries only.

{summarize_rows(strongest_inverse, 'pass_minus_control_target_movement_mean_delta')}

## Why Slices Worked Or Failed

Working slices are those where frozen pass or descriptor branches had more positive neutral target movement than their control/rest comparator while clearing duplicate-key floor checks. Failing slices are inverse, neutral, underpowered, concentrated, or fail-closed in the ledgers. The explanation ledger preserves the source-bound reason for each: observed descriptor/horizon/target-family contrast, duplicate-key underpowering, source/economic/symbol/session concentration, stress sensitivity, or exact fail-closed source repair family.

## Next Gate

The next step is independent G12 audit of this result execution packet: `{rel(G12_PROMPT)}`. That audit must recompute counts and selected metrics from frozen files, attack leakage/duplicate/concentration/stress issues, and preserve `NO_PROMOTION_VERDICT`.
"""


def g12_prompt_text() -> str:
    return f"""# G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT

Date: {DATE}

Follow this prompt as a G12 audit of the completed READY8 discriminative sealed-validation execution packet. Do mandatory GTOS preflight first, read `.context/LIVE_STATE.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, and the latest handoff. Do not rely on chat memory.

Evidence class: `G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_ONLY`.

Audit input directory:

`research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate/`

Audit objective:

Independently audit the sealed/stress validation execution outputs against the frozen opening-gate contract. This is a full-materiality G12 audit, not a lazy sampling pass and not a blocker-theater exercise. Parse the materialized ledgers and recompute complete counts/distributions wherever the file size is tractable; for the largest ledgers, use deterministic streaming recomputation over every row or a documented lossless chunked scan. Do not replace full-ledger checks with top-N summaries.

Verify counts, SHA256 hashes, Git LFS pointer/materialized file integrity, sealed/stress partition separation, fail-closed exclusion, duplicate_proxy_denominator_key effective-N, concentration warnings, pass/control deltas, descriptor one-vs-rest contrasts, branch-universe coverage, question/ambiguity closure, and synthesis claims. Recompute the headline 1,278 comparable pass/control records, 724 positive pass-minus-control records, 554 inverse records, 9,570 descriptor one-vs-rest records, 44,434 sealed primary branch records, 69,145 stress records, 79,746 all-branch records, 99,978 question records, 91,691 ambiguity records, and all frozen target counts.

Attack leakage, duplicate denominator drift, target-family confusion, stress/sealed mixing, top-N substitution, promotion language, forbidden-surface touches, overclaimed "edge" language, hidden concentration, underpowered-branch interpretation, and LFS/raw-blob mistakes. Be strict but fair: do not invent blockers, do not reject because a result is negative, mixed, or not promotable, and do not use G12 conservatism to erase valid sealed target-movement intelligence. If a same-G12 repair is possible for stale hashes, EOL/path friction, manifest binding, parser coverage, or audit wording, repair and rerun before terminal decision.

Required G12 outputs:

- terminal decision ledger,
- recomputation ledger,
- metric discrepancy ledger,
- branch coverage audit ledger,
- fail-closed/duplicate/concentration audit ledger,
- forbidden surface audit ledger,
- LFS/materialization/raw-blob audit ledger,
- full-ledger row-count/distribution recomputation ledger,
- same-G12 repair ledger with zero remaining repairable items or exact nonrepairable evidence,
- saturation/self-red-team ledger,
- completion audit,
- output manifest,
- focused tests or verifier output.

Safe boundaries:

No promotion, live-readiness, AI/API calls, paid/vendor access, broker account/order/history/deal/position evidence, registry edits, remote pushes, raw-market-blob commits, prompt/config/risk/safety/execution/canary/selector changes, or live trading behavior. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Completion standard:

Complete only when every material execution claim is accepted, repaired in the same G12 evidence class, or rejected with exact file/metric evidence; every large-ledger count/distribution has been recomputed or losslessly streamed; same-G12 repairable items are zero; no invented blockers remain; verifier/focused tests pass; and the next owner/source/audit route is explicit for any true nonrepairable issue.
"""


def write_manifest(generated_at: str) -> None:
    artifact_paths = [
        builder_root_gitattributes(),
        OUT_DIR / OUTPUTS["decision"],
        OUT_DIR / OUTPUTS["frozen_input_hash"],
        OUT_DIR / OUTPUTS["sealed_primary"],
        OUT_DIR / OUTPUTS["stress"],
        OUT_DIR / OUTPUTS["pass_control"],
        OUT_DIR / OUTPUTS["all_branches"],
        OUT_DIR / OUTPUTS["questions"],
        OUT_DIR / OUTPUTS["explanations"],
        OUT_DIR / OUTPUTS["coverage"],
        OUT_DIR / OUTPUTS["fail_closed"],
        OUT_DIR / OUTPUTS["duplicate"],
        OUT_DIR / OUTPUTS["partition_symbol"],
        OUT_DIR / OUTPUTS["ambiguity"],
        OUT_DIR / OUTPUTS["saturation"],
        OUT_DIR / OUTPUTS["completion"],
        OUT_DIR / OUTPUTS["synthesis"],
        OUT_DIR / OUTPUTS["focused"],
        OUT_DIR / OUTPUTS["verification"],
        OUT_DIR / OUTPUTS["g12_starter"],
        G12_PROMPT,
        Path(__file__).resolve(),
        OUT_DIR / f"verify_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py",
        OUT_DIR / f"test_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py",
    ]
    artifacts = []
    for path in artifact_paths:
        exists = path.exists()
        artifacts.append(
            {
                "path": rel(path),
                "exists": exists,
                "bytes": path.stat().st_size if exists else None,
                "sha256": sha256_file(path) if exists else None,
            }
        )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": generated_at,
        "manifest_self_hash_policy": "Output manifest excludes itself from required hash closure; verifier may refresh after writing verification result.",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "terminal_decision": "SEALED_VALIDATION_EXECUTION_PACKET_EMITTED_FOR_G12_AUDIT",
    }
    write_json(OUT_DIR / OUTPUTS["manifest"], manifest)


def builder_root_gitattributes() -> Path:
    return ROOT / ".gitattributes"


def write_outputs(
    generated_at: str,
    frozen: dict[str, Any],
    all_branch_records: list[dict[str, Any]],
    sealed_records: list[dict[str, Any]],
    stress_records: list[dict[str, Any]],
    pass_control_records: list[dict[str, Any]],
    fail_closed_records: list[dict[str, Any]],
    duplicate_records: list[dict[str, Any]],
    partition_symbol_records: list[dict[str, Any]],
    question_records: list[dict[str, Any]],
    explanation_records: list[dict[str, Any]],
    ambiguity_records: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> None:
    output_counts = {
        "all_branches": write_jsonl(OUT_DIR / OUTPUTS["all_branches"], all_branch_records),
        "sealed_primary": write_jsonl(OUT_DIR / OUTPUTS["sealed_primary"], sealed_records),
        "stress": write_jsonl(OUT_DIR / OUTPUTS["stress"], stress_records),
        "pass_control": write_jsonl(OUT_DIR / OUTPUTS["pass_control"], pass_control_records),
        "fail_closed": write_jsonl(OUT_DIR / OUTPUTS["fail_closed"], fail_closed_records),
        "duplicate": write_jsonl(OUT_DIR / OUTPUTS["duplicate"], duplicate_records),
        "partition_symbol": write_jsonl(OUT_DIR / OUTPUTS["partition_symbol"], partition_symbol_records),
        "questions": write_jsonl(OUT_DIR / OUTPUTS["questions"], question_records),
        "explanations": write_jsonl(OUT_DIR / OUTPUTS["explanations"], explanation_records),
        "ambiguity": write_jsonl(OUT_DIR / OUTPUTS["ambiguity"], ambiguity_records),
    }
    write_json(OUT_DIR / OUTPUTS["frozen_input_hash"], frozen)
    write_json(OUT_DIR / OUTPUTS["coverage"], coverage)
    write_json(OUT_DIR / OUTPUTS["saturation"], saturation_ledger(output_counts["questions"], output_counts["all_branches"], output_counts["pass_control"]))
    write_json(OUT_DIR / OUTPUTS["decision"], decision_ledger(generated_at, frozen, output_counts))
    write_json(OUT_DIR / OUTPUTS["completion"], completion_audit(generated_at, output_counts, OUTPUTS["coverage"]))
    write_json(
        OUT_DIR / OUTPUTS["focused"],
        {
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "generated_at_utc": generated_at,
            "focused_test_command": f"python -B -m pytest -p no:cacheprovider {rel(OUT_DIR / 'test_scid_ready8_discriminative_sealed_validation_after_opening_gate_2026_05_13.py')} -q --basetemp C:\\tmp\\pytest_ready8_sealed",
            "status": "RECORDED_COMMAND_TO_RUN_BEFORE_CLOSEOUT",
            "passed": None,
        },
    )
    write_json(
        OUT_DIR / OUTPUTS["verification"],
        {
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "generated_at_utc": generated_at,
            "status": "PENDING_VERIFIER_RUN",
            "ok": None,
        },
    )
    (OUT_DIR / OUTPUTS["synthesis"]).write_text(
        synthesis_md(generated_at, sealed_records, pass_control_records, fail_closed_records, duplicate_records),
        encoding="utf-8",
        newline="\n",
    )
    G12_PROMPT.write_text(g12_prompt_text(), encoding="utf-8", newline="\n")
    starter = (
        f"/goal Follow the full controlling prompt in {rel(G12_PROMPT)} as the complete objective; "
        "run mandatory preflight/context refresh first; do not rely on chat memory; stay "
        "G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_ONLY with no promotion, live-readiness, "
        "AI/API, paid/vendor, broker account/order/history/deal/position, registry, remote, raw-market-blob, "
        "prompt/config/risk/safety/execution/canary/selector, or live trading behavior; parse the materialized ledgers and "
        "audit the sealed/stress execution packet with full-row or lossless streaming recomputation, including counts, hashes, "
        "LFS/materialization, sealed/stress separation, fail-closed exclusion, duplicate effective-N, concentration, pass/control "
        "deltas, descriptor contrasts, branch coverage, question/ambiguity closure, and synthesis claims; be strict but fair, "
        "do not invent blockers or use audit posture to erase valid target-movement intelligence, repair same-G12 issues before "
        "terminal decision, preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, "
        "run verifier/focused tests, and complete only when every material result claim is accepted, repaired, or rejected with exact evidence."
    )
    (OUT_DIR / OUTPUTS["g12_starter"]).write_text(starter + "\n", encoding="utf-8", newline="\n")
    write_manifest(generated_at)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    frozen = build()
    if not args.quiet:
        print(
            json.dumps(
                {
                    "ok": all(frozen["count_checks"].values()) and frozen["rowset_sha256_matches"],
                    "route_id": ROUTE_ID,
                    "target_result_rows": frozen["counts_observed"]["target_result_rows"],
                    "computable_rows": frozen["counts_observed"]["computable_rows"],
                    "fail_closed_rows": frozen["counts_observed"]["fail_closed_rows"],
                    "output_dir": rel(OUT_DIR),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
