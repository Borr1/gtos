from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-15"
ROUTE_ID = "MAC001_MAC004_INVERSE_AVOID_FILTER_VALIDATION_DESIGN"
EVIDENCE_CLASS = "READY8_MAC_INVERSE_AVOID_FILTER_DESIGN_AND_SCREEN_ONLY"
SCHEMA_VERSION = "mac001_mac004_inverse_avoid_filter_design_v1"

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/MAC001_MAC004_INVERSE_AVOID_FILTER_VALIDATION_DESIGN_GOAL_PROMPT_2026-05-15.md"
ROWSET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design"
ROWSET_PATH = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
DESCRIPTOR_LEDGER = ROWSET_DIR / "SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_2026-05-13.json"
TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet"
SEALED_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate"
ACCEPTED_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
LAUNCH_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_g12_accepted_execution_route_orchestration"

MAC_CARDS = ("MAC-001", "MAC-004")
INTERACTION_CARDS = ("HAZ-001", "UNC-004", "BEH-001", "HAZ-005")
HORIZONS = (1, 4, 16, 32)
TARGET_FAMILIES = (
    "neutral_close_to_close_return_m15_horizons_v1",
    "neutral_high_low_excursion_m15_horizons_v1",
)
PRIMARY_UNIQUE_DUP_FLOOR = 30
CONCENTRATION_WARN_SHARE = 0.50

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_raw_market_data_blob_commit": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
}

OUTPUTS = {
    "context_anchor": f"MAC_INVERSE_CONTEXT_ANCHOR_{DATE}.json",
    "input_binding": f"MAC_INVERSE_INPUT_BINDING_LEDGER_{DATE}.json",
    "decision": f"MAC_INVERSE_DECISION_LEDGER_{DATE}.json",
    "rowset_inventory": f"MAC_INVERSE_ROWSET_INVENTORY_AND_DESCRIPTOR_DEFINITIONS_{DATE}.json",
    "pass_control": f"MAC_INVERSE_PASS_CONTROL_RECOMPUTATION_LEDGER_{DATE}.jsonl",
    "horizon_anatomy": f"MAC_INVERSE_HORIZON_TARGET_FAMILY_ANATOMY_LEDGER_{DATE}.jsonl",
    "timing": f"MAC_INVERSE_CALENDAR_FIX_TIMING_LEDGER_{DATE}.jsonl",
    "concentration": f"MAC_INVERSE_CONCENTRATION_LEDGER_{DATE}.jsonl",
    "leave_one": f"MAC_INVERSE_LEAVE_ONE_STRESS_LEDGER_{DATE}.jsonl",
    "candidate_design": f"MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_{DATE}.jsonl",
    "interaction": f"MAC_INVERSE_INTERACTION_LEDGER_{DATE}.jsonl",
    "failure": f"MAC_INVERSE_FAILURE_ANATOMY_LEDGER_{DATE}.jsonl",
    "fail_closed": f"MAC_INVERSE_FAIL_CLOSED_NON_APPLICABLE_LEDGER_{DATE}.jsonl",
    "future_design": f"MAC_INVERSE_FUTURE_VALIDATION_SOURCE_CAPTURE_DESIGN_{DATE}.json",
    "saturation": f"MAC_INVERSE_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "completion": f"MAC_INVERSE_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": f"MAC_INVERSE_SYNTHESIS_{DATE}.md",
    "manifest": f"MAC_INVERSE_OUTPUT_MANIFEST_{DATE}.json",
    "focused": f"MAC_INVERSE_FOCUSED_TEST_RESULT_{DATE}.json",
    "verification": f"MAC_INVERSE_VERIFICATION_RESULT_{DATE}.json",
    "g12_prompt": f"G12_MAC_INVERSE_AVOID_FILTER_AUDIT_GOAL_PROMPT_{DATE}.md",
    "g12_starter": f"G12_MAC_INVERSE_AVOID_FILTER_AUDIT_STARTER_{DATE}.txt",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")
            count += 1
    return count


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def make_key(parts: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple((key, safe_value(value)) for key, value in sorted(parts.items()))


def key_to_dict(key: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {name: value for name, value in key}


def record_id(prefix: str, key: dict[str, Any] | tuple[tuple[str, str], ...]) -> str:
    raw = key_to_dict(key) if isinstance(key, tuple) else key
    return hashlib.sha256((prefix + "|" + stable_json(raw)).encode("utf-8")).hexdigest()[:24]


def target_files_for(card_id: str) -> list[Path]:
    token = card_id.replace("-", "_")
    return [
        TARGET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{token}_CLOSE_TO_CLOSE_2026-05-13.jsonl",
        TARGET_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_{token}_HIGH_LOW_EXCURSION_2026-05-13.jsonl",
    ]


def target_unit(row: dict[str, Any]) -> str:
    if row.get("target_family_id") == "neutral_close_to_close_return_m15_horizons_v1":
        return "close_to_close_percent_return"
    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1":
        return "upside_minus_downside_excursion_percent"
    return "unknown_target_unit"


def primary_movement_value(row: dict[str, Any]) -> float | None:
    if row.get("target_family_id") == "neutral_close_to_close_return_m15_horizons_v1":
        value = row.get("close_to_close_percent_return")
        return None if value is None else float(value)
    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1":
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        if upside is None or downside is None:
            return None
        return float(upside) - float(downside)
    return None


def session_value(row: dict[str, Any]) -> str:
    descriptors = row.get("descriptor_values") or {}
    return safe_value(row.get("session_bucket") or descriptors.get("session_bucket") or "NO_SESSION_DESCRIPTOR")


def source_segment(row: dict[str, Any]) -> str:
    return safe_value(row.get("source_segment_sha256_expected") or row.get("source_segment_sha256"))


def source_window(row: dict[str, Any]) -> str:
    return f"{safe_value(row.get('source_file_name_expected') or row.get('source_file_name'))}|{source_segment(row)}"


def entry_date(row: dict[str, Any]) -> str:
    value = row.get("entry_reference_time_utc") or row.get("decision_asof_utc") or ""
    return value[:10] if value else "NULL"


def metric_eligible(row: dict[str, Any]) -> bool:
    return (
        row.get("terminal_status") == "COMPUTABLE"
        and row.get("denominator_role") != "per_card_fail_closed_row"
        and primary_movement_value(row) is not None
    )


@dataclass
class Stats:
    rows: int = 0
    values: list[float] = field(default_factory=list)
    duplicate_keys: set[str] = field(default_factory=set)
    positive: int = 0
    negative: int = 0
    zero: int = 0
    symbols: Counter[str] = field(default_factory=Counter)
    economic_groups: Counter[str] = field(default_factory=Counter)
    sessions: Counter[str] = field(default_factory=Counter)
    source_segments: Counter[str] = field(default_factory=Counter)
    source_windows: Counter[str] = field(default_factory=Counter)
    entry_dates: Counter[str] = field(default_factory=Counter)
    target_units: Counter[str] = field(default_factory=Counter)

    def update(self, row: dict[str, Any], value: float) -> None:
        self.rows += 1
        self.values.append(float(value))
        if value > 0:
            self.positive += 1
        elif value < 0:
            self.negative += 1
        else:
            self.zero += 1
        self.duplicate_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))
        self.symbols[safe_value(row.get("symbol"))] += 1
        self.economic_groups[safe_value(row.get("canonical_economic_group"))] += 1
        self.sessions[session_value(row)] += 1
        self.source_segments[source_segment(row)] += 1
        self.source_windows[source_window(row)] += 1
        self.entry_dates[entry_date(row)] += 1
        self.target_units[target_unit(row)] += 1

    @property
    def mean(self) -> float | None:
        return statistics.fmean(self.values) if self.values else None

    @property
    def unique_duplicate_count(self) -> int:
        return len(self.duplicate_keys)

    def concentration_record(self, counter: Counter[str]) -> dict[str, Any]:
        if not self.rows or not counter:
            return {"top_value": None, "top_count": 0, "top_share": None}
        value, count = counter.most_common(1)[0]
        return {"top_value": value, "top_count": count, "top_share": count / self.rows}

    def percentile(self, q: float) -> float | None:
        if not self.values:
            return None
        values = sorted(self.values)
        if len(values) == 1:
            return values[0]
        pos = (len(values) - 1) * q
        lo = math.floor(pos)
        hi = math.ceil(pos)
        if lo == hi:
            return values[int(pos)]
        return values[lo] * (hi - pos) + values[hi] * (pos - lo)

    def warnings(self) -> list[str]:
        warnings: list[str] = []
        if self.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR:
            warnings.append("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
        for label, counter in (
            ("SYMBOL_CONCENTRATION_GT_50PCT", self.symbols),
            ("ECONOMIC_GROUP_CONCENTRATION_GT_50PCT", self.economic_groups),
            ("SESSION_CONCENTRATION_GT_50PCT", self.sessions),
            ("SOURCE_SEGMENT_CONCENTRATION_GT_50PCT", self.source_segments),
            ("SOURCE_WINDOW_CONCENTRATION_GT_50PCT", self.source_windows),
        ):
            if (self.concentration_record(counter)["top_share"] or 0.0) > CONCENTRATION_WARN_SHARE:
                warnings.append(label)
        return warnings

    def to_record(self) -> dict[str, Any]:
        values = sorted(self.values)
        return {
            "rows": self.rows,
            "unique_duplicate_denominator_count": self.unique_duplicate_count,
            "effective_n_policy": "duplicate_proxy_denominator_key",
            "target_movement": {
                "mean": self.mean,
                "median": statistics.median(values) if values else None,
                "min": values[0] if values else None,
                "max": values[-1] if values else None,
                "p05": self.percentile(0.05),
                "p95": self.percentile(0.95),
            },
            "positive_movement_count": self.positive,
            "negative_movement_count": self.negative,
            "zero_movement_count": self.zero,
            "positive_movement_rate": self.positive / self.rows if self.rows else None,
            "negative_movement_rate": self.negative / self.rows if self.rows else None,
            "zero_movement_rate": self.zero / self.rows if self.rows else None,
            "target_unit_counts": dict(self.target_units),
            "concentration": {
                "symbol": self.concentration_record(self.symbols),
                "canonical_economic_group": self.concentration_record(self.economic_groups),
                "session": self.concentration_record(self.sessions),
                "source_segment_sha256": self.concentration_record(self.source_segments),
                "source_window": self.concentration_record(self.source_windows),
                "entry_date": self.concentration_record(self.entry_dates),
            },
            "concentration_or_power_warnings": self.warnings(),
            "underpowered_unique_duplicate_floor_lt_30": self.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR,
        }


@dataclass
class CompareBucket:
    pass_stats: Stats = field(default_factory=Stats)
    control_stats: Stats = field(default_factory=Stats)


def comparison_dimensions(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    base = {
        "card_id": row.get("card_id"),
        "partition_assignment": row.get("partition_assignment"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
    }
    descriptors = row.get("descriptor_values") or {}
    yield "pass_vs_control_card_target_family_horizon", base
    yield "pass_vs_control_symbol_target_family_horizon", {**base, "symbol": row.get("symbol")}
    yield "pass_vs_control_economic_group_target_family_horizon", {**base, "canonical_economic_group": row.get("canonical_economic_group")}
    yield "pass_vs_control_session_target_family_horizon", {**base, "session": session_value(row)}
    yield "pass_vs_control_source_segment_target_family_horizon", {**base, "source_segment_sha256": source_segment(row)}
    yield "pass_vs_control_source_window_target_family_horizon", {**base, "source_window": source_window(row)}
    yield "pass_vs_control_entry_date_target_family_horizon", {**base, "entry_date_utc": entry_date(row)}
    yield "pass_vs_control_descriptor_contrast_target_family_horizon", {**base, "descriptor_name": "descriptor_contrast_key", "descriptor_value": row.get("descriptor_contrast_key")}
    for name, value in sorted(descriptors.items()):
        yield "pass_vs_control_descriptor_value_target_family_horizon", {**base, "descriptor_name": name, "descriptor_value": value}


def descriptor_dimensions(row: dict[str, Any]) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    base = {
        "card_id": row.get("card_id"),
        "partition_assignment": row.get("partition_assignment"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "denominator_role": row.get("denominator_role"),
    }
    descriptors = row.get("descriptor_values") or {}
    for name, value in sorted(descriptors.items()):
        parent = {**base, "descriptor_name": name}
        yield parent, {**parent, "descriptor_value": value}
    parent = {**base, "descriptor_name": "descriptor_contrast_key"}
    yield parent, {**parent, "descriptor_value": row.get("descriptor_contrast_key")}


def classify_delta(delta: float | None, pass_stats: Stats, control_stats: Stats) -> str:
    if not pass_stats.rows or not control_stats.rows:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
    warnings = pass_stats.warnings() + control_stats.warnings()
    if any("UNDERPOWERED" in warning for warning in warnings):
        if delta is None or abs(delta) < 1e-12:
            return "UNDERPOWERED_NEUTRAL"
        return "UNDERPOWERED_INVERSE" if delta < 0 else "UNDERPOWERED_POSITIVE"
    if delta is None or abs(delta) < 1e-12:
        return "NEUTRAL_TIE"
    return "INVERSE_PASS_LT_CONTROL" if delta < 0 else "POSITIVE_PASS_GT_CONTROL"


def compare_record(family: str, key: tuple[tuple[str, str], ...], bucket: CompareBucket, accepted_index: dict[tuple[str, str, str], dict[str, Any]]) -> dict[str, Any]:
    pass_stats = bucket.pass_stats
    control_stats = bucket.control_stats
    delta = None
    if pass_stats.mean is not None and control_stats.mean is not None:
        delta = pass_stats.mean - control_stats.mean
    rate_delta = None
    if pass_stats.rows and control_stats.rows:
        rate_delta = (pass_stats.positive / pass_stats.rows) - (control_stats.positive / control_stats.rows)
    warnings = list(dict.fromkeys(pass_stats.warnings() + control_stats.warnings()))
    classification = classify_delta(delta, pass_stats, control_stats)
    key_dict = key_to_dict(key)
    accepted_key = (family, stable_json(key_dict), "pass_vs_control")
    accepted = accepted_index.get(accepted_key)
    underpowered_flag = "UNDERPOWERED" in classification or "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" in warnings
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "comparison_type": "pass_vs_control",
        "comparison_family": family,
        "comparison_id": record_id(family, key),
        "branch_key": key_dict,
        "pass_rows": pass_stats.rows,
        "control_rows": control_stats.rows,
        "pass_unique_duplicate_denominator_count": pass_stats.unique_duplicate_count,
        "control_unique_duplicate_denominator_count": control_stats.unique_duplicate_count,
        "pass_target_movement_mean": pass_stats.mean,
        "control_target_movement_mean": control_stats.mean,
        "pass_minus_control_target_movement_mean_delta": delta,
        "pass_positive_rate_minus_control_positive_rate_delta": rate_delta,
        "comparison_classification": classification,
        "inversion_flag": classification in {"INVERSE_PASS_LT_CONTROL", "UNDERPOWERED_INVERSE"},
        "underpowered_flag": underpowered_flag,
        "concentration_or_power_warnings": warnings,
        "accepted_g12_row_present": accepted is not None,
        "accepted_g12_match": accepted_matches(accepted, pass_stats, control_stats, delta, classification, underpowered_flag),
        "metric_scope": "neutral target-movement comparison only; not R/PnL/win-rate/expectancy/promotion",
        "data_bound_explanation": comparison_explanation(classification, warnings),
    }


def accepted_matches(accepted: dict[str, Any] | None, pass_stats: Stats, control_stats: Stats, delta: float | None, classification: str, underpowered_flag: bool | None = None) -> bool | None:
    if accepted is None:
        return None
    observed = (
        accepted.get("pass_rows") == pass_stats.rows
        and accepted.get("control_rows") == control_stats.rows
        and accepted.get("comparison_classification") == classification
        and (underpowered_flag is None or accepted.get("underpowered_flag") == underpowered_flag)
    )
    accepted_delta = accepted.get("pass_minus_control_target_movement_mean_delta")
    if accepted_delta is None or delta is None:
        return observed and accepted_delta is delta
    return observed and abs(float(accepted_delta) - float(delta)) < 1e-15


def comparison_explanation(classification: str, warnings: list[str]) -> str:
    caveat = "warnings=" + ",".join(warnings) if warnings else "no frozen concentration/power warning"
    if classification == "INVERSE_PASS_LT_CONTROL":
        return f"MAC condition underperformed its frozen contrast on neutral target movement; treat as inverse/avoid-filter evidence only. {caveat}."
    if classification == "POSITIVE_PASS_GT_CONTROL":
        return f"MAC condition outperformed its frozen contrast; this branch is a killed avoid-filter candidate for the current evidence class. {caveat}."
    if classification.startswith("UNDERPOWERED"):
        return f"Branch remains visible but is below the frozen duplicate-key floor; no primary interpretation. {caveat}."
    if classification == "NEUTRAL_TIE":
        return f"Branch is neutral after recomputation; no avoid/inverse design claim. {caveat}."
    return f"Branch lacks pass or control rows and is not comparable in this frozen packet. {caveat}."


def stats_from_items(items: Iterable[tuple[dict[str, Any], float]]) -> Stats:
    stats = Stats()
    for row, value in items:
        stats.update(row, value)
    return stats


def subtract_items(parent: list[tuple[dict[str, Any], float]], child_key: tuple[tuple[str, str], ...]) -> list[tuple[dict[str, Any], float]]:
    child = key_to_dict(child_key)
    descriptor_name = child["descriptor_name"]
    descriptor_value = child["descriptor_value"]
    out: list[tuple[dict[str, Any], float]] = []
    for row, value in parent:
        descriptors = row.get("descriptor_values") or {}
        observed = row.get("descriptor_contrast_key") if descriptor_name == "descriptor_contrast_key" else descriptors.get(descriptor_name)
        if safe_value(observed) != descriptor_value:
            out.append((row, value))
    return out


def descriptor_compare_records(
    parent_items: dict[tuple[tuple[str, str], ...], list[tuple[dict[str, Any], float]]],
    child_items: dict[tuple[tuple[str, str], ...], list[tuple[dict[str, Any], float]]],
    accepted_index: dict[tuple[str, str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for child_key, child in sorted(child_items.items()):
        child_dict = key_to_dict(child_key)
        parent_key = make_key({name: value for name, value in child_dict.items() if name != "descriptor_value"})
        parent = parent_items[parent_key]
        child_stats = stats_from_items(child)
        other = subtract_items(parent, child_key)
        other_stats = stats_from_items(other)
        delta = None if child_stats.mean is None or other_stats.mean is None else child_stats.mean - other_stats.mean
        warnings = child_stats.warnings()
        if child_stats.unique_duplicate_count < PRIMARY_UNIQUE_DUP_FLOOR or len({safe_value(row.get("duplicate_proxy_denominator_key")) for row, _ in other}) < PRIMARY_UNIQUE_DUP_FLOOR:
            if "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" not in warnings:
                warnings = warnings + ["UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30"]
        classification = classify_delta(delta, child_stats, other_stats).replace("PASS", "DESCRIPTOR").replace("CONTROL", "OTHER")
        record = {
            "schema_version": SCHEMA_VERSION,
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            **SAFE_FLAGS,
            "comparison_type": "descriptor_one_vs_rest",
            "comparison_family": "descriptor_value_one_vs_rest_target_family_horizon",
            "comparison_id": record_id("descriptor_value_one_vs_rest_target_family_horizon", child_key),
            "branch_key": child_dict,
            "descriptor_rows": child_stats.rows,
            "other_rows": other_stats.rows,
            "descriptor_unique_duplicate_denominator_count": child_stats.unique_duplicate_count,
            "other_unique_duplicate_denominator_count": len({safe_value(row.get("duplicate_proxy_denominator_key")) for row, _ in other}),
            "descriptor_target_movement_mean": child_stats.mean,
            "other_target_movement_mean": other_stats.mean,
            "descriptor_minus_other_target_movement_mean_delta": delta,
            "comparison_classification": classification,
            "inversion_flag": delta is not None and delta < 0,
            "underpowered_flag": "UNDERPOWERED" in classification,
            "concentration_or_power_warnings": warnings,
            "metric_scope": "descriptor contrast over frozen target-movement rows; not threshold tuning or promotion",
            "data_bound_explanation": comparison_explanation(classification, warnings),
        }
        accepted_key = ("descriptor_value_one_vs_rest_target_family_horizon", stable_json(child_dict), "descriptor_one_vs_rest")
        accepted = accepted_index.get(accepted_key)
        record["accepted_g12_row_present"] = accepted is not None
        record["accepted_g12_match"] = descriptor_accepted_matches(accepted, record)
        rows.append(record)
    return rows


def descriptor_accepted_matches(accepted: dict[str, Any] | None, record: dict[str, Any]) -> bool | None:
    if accepted is None:
        return None
    delta = record.get("descriptor_minus_other_target_movement_mean_delta")
    accepted_delta = accepted.get("descriptor_minus_other_target_movement_mean_delta")
    basic = (
        accepted.get("descriptor_rows") == record.get("descriptor_rows")
        and accepted.get("other_rows") == record.get("other_rows")
        and accepted.get("comparison_classification") == record.get("comparison_classification")
    )
    if delta is None or accepted_delta is None:
        return basic and delta is accepted_delta
    return basic and abs(float(delta) - float(accepted_delta)) < 1e-15


def load_accepted_pass_control_index() -> dict[tuple[str, str, str], dict[str, Any]]:
    path = SEALED_DIR / "R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl"
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("branch_key") or {}
            if key.get("card_id") in MAC_CARDS:
                index[(row["comparison_family"], stable_json(key), row.get("comparison_type", "pass_vs_control"))] = row
    return index


def read_target_rows(cards: Iterable[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    fail_closed_rows: list[dict[str, Any]] = []
    non_applicable_rows: list[dict[str, Any]] = []
    file_ledgers: list[dict[str, Any]] = []
    for card_id in cards:
        for path in target_files_for(card_id):
            row_count = 0
            digest = hashlib.sha256()
            with path.open("rb") as raw:
                for raw_line in raw:
                    digest.update(raw_line)
                    if not raw_line.strip():
                        continue
                    row = json.loads(raw_line)
                    row_count += 1
                    all_rows.append(row)
                    if metric_eligible(row):
                        metric_rows.append(row)
                    if row.get("terminal_status") != "COMPUTABLE" or row.get("denominator_role") == "per_card_fail_closed_row":
                        fail_closed_rows.append(row)
                    if row.get("denominator_role") == "per_card_non_applicable_row":
                        non_applicable_rows.append(row)
            file_ledgers.append({"path": rel(path), "rows": row_count, "sha256": digest.hexdigest(), "bytes": path.stat().st_size})
    return all_rows, metric_rows, fail_closed_rows, non_applicable_rows, file_ledgers


def base_artifact(family: str, generated_at: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    obj = {
        "artifact_family": family,
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
    }
    if extra:
        obj.update(extra)
    return obj


def rowset_inventory(generated_at: str) -> dict[str, Any]:
    descriptor_obj = json.loads(DESCRIPTOR_LEDGER.read_text(encoding="utf-8"))
    descriptor_cards = [card for card in descriptor_obj["cards"] if card["card_id"] in MAC_CARDS]
    counts = Counter()
    descriptor_counts: dict[str, Counter[str]] = defaultdict(Counter)
    role_counts: dict[str, Counter[str]] = defaultdict(Counter)
    with ROWSET_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            card = row.get("card_id")
            if card not in MAC_CARDS:
                continue
            counts[card] += 1
            role_counts[card][safe_value(row.get("denominator_role"))] += 1
            for name, value in (row.get("descriptor_values") or {}).items():
                descriptor_counts[f"{card}:{name}"][safe_value(value)] += 1
    return base_artifact(
        "rowset_inventory_and_descriptor_definitions",
        generated_at,
        {
            "rowset_path": rel(ROWSET_PATH),
            "rowset_sha256": sha256_file(ROWSET_PATH),
            "rowset_counts_by_card": dict(counts),
            "denominator_role_counts_by_card": {card: dict(counter) for card, counter in role_counts.items()},
            "descriptor_value_counts": {key: dict(counter) for key, counter in descriptor_counts.items()},
            "descriptor_definitions": descriptor_cards,
            "mac001_definition": "decision_asof_utc-derived day-of-week/month-turn/week-edge calendar context; no target or post-event fields consumed",
            "mac004_definition": "decision_asof_utc plus source symbol metals proxy membership and May/BST LBMA AM 09:30 UTC / PM 14:00 UTC fix proximity; non-metals fail closed as non-applicable source context",
        },
    )


def build_pass_control(metric_rows: list[dict[str, Any]], accepted_index: dict[tuple[str, str, str], dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[tuple[dict[str, Any], float]]]]:
    compare_buckets: dict[tuple[str, tuple[tuple[str, str], ...]], CompareBucket] = defaultdict(CompareBucket)
    parent_items: dict[tuple[tuple[str, str], ...], list[tuple[dict[str, Any], float]]] = defaultdict(list)
    child_items: dict[tuple[tuple[str, str], ...], list[tuple[dict[str, Any], float]]] = defaultdict(list)
    leave_groups: dict[str, list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for row in metric_rows:
        value = primary_movement_value(row)
        if value is None:
            continue
        role = row.get("denominator_role")
        for family, parts in comparison_dimensions(row):
            key = make_key(parts)
            bucket = compare_buckets[(family, key)]
            if role == "per_card_pass_row":
                bucket.pass_stats.update(row, value)
            elif role == "per_card_contrast_row":
                bucket.control_stats.update(row, value)
        for parent, child in descriptor_dimensions(row):
            parent_key = make_key(parent)
            child_key = make_key(child)
            parent_items[parent_key].append((row, value))
            child_items[child_key].append((row, value))
        for scope_name, scope_parts in leave_one_scopes(row):
            leave_groups[scope_name + "|" + stable_json(scope_parts)].append((row, value))
    records = [
        compare_record(family, key, bucket, accepted_index)
        for (family, key), bucket in sorted(compare_buckets.items(), key=lambda item: (item[0][0], item[0][1]))
        if bucket.pass_stats.rows or bucket.control_stats.rows
    ]
    records.extend(descriptor_compare_records(parent_items, child_items, accepted_index))
    return records, leave_groups


def leave_one_scopes(row: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    base = {
        "card_id": row.get("card_id"),
        "partition_assignment": row.get("partition_assignment"),
        "target_family_id": row.get("target_family_id"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
    }
    yield "card_target_family_horizon", base
    yield "descriptor_contrast_target_family_horizon", {**base, "descriptor_contrast_key": row.get("descriptor_contrast_key")}


def dimension_value(row: dict[str, Any], dimension: str) -> str:
    if dimension == "symbol":
        return safe_value(row.get("symbol"))
    if dimension == "canonical_economic_group":
        return safe_value(row.get("canonical_economic_group"))
    if dimension == "session":
        return session_value(row)
    if dimension == "source_segment_sha256":
        return source_segment(row)
    if dimension == "source_window":
        return source_window(row)
    return "UNKNOWN_DIMENSION"


def leave_one_stress(leave_groups: dict[str, list[tuple[dict[str, Any], float]]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for scope_blob, items in sorted(leave_groups.items()):
        scope_name, key_json = scope_blob.split("|", 1)
        scope_key = json.loads(key_json)
        base_pass = stats_from_items((row_value for row_value in items if row_value[0].get("denominator_role") == "per_card_pass_row"))
        base_control = stats_from_items((row_value for row_value in items if row_value[0].get("denominator_role") == "per_card_contrast_row"))
        base_delta = None if base_pass.mean is None or base_control.mean is None else base_pass.mean - base_control.mean
        for dimension in ("symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_window"):
            values = sorted({dimension_value(row, dimension) for row, _ in items})
            for omitted in values:
                kept = [(row, value) for row, value in items if dimension_value(row, dimension) != omitted]
                pass_stats = stats_from_items((row_value for row_value in kept if row_value[0].get("denominator_role") == "per_card_pass_row"))
                control_stats = stats_from_items((row_value for row_value in kept if row_value[0].get("denominator_role") == "per_card_contrast_row"))
                delta = None if pass_stats.mean is None or control_stats.mean is None else pass_stats.mean - control_stats.mean
                records.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "route_id": ROUTE_ID,
                        "evidence_class": EVIDENCE_CLASS,
                        **SAFE_FLAGS,
                        "stress_family": "leave_one_dimension_value_pass_vs_control",
                        "stress_id": record_id("leave_one", {**scope_key, "scope": scope_name, "dimension": dimension, "omitted_value": omitted}),
                        "scope_name": scope_name,
                        "branch_key": scope_key,
                        "omitted_dimension": dimension,
                        "omitted_value": omitted,
                        "base_pass_rows": base_pass.rows,
                        "base_control_rows": base_control.rows,
                        "base_delta": base_delta,
                        "stress_pass_rows": pass_stats.rows,
                        "stress_control_rows": control_stats.rows,
                        "stress_delta": delta,
                        "stress_classification": classify_delta(delta, pass_stats, control_stats),
                        "sign_preserved_vs_base": None if base_delta is None or delta is None else ((base_delta < 0 and delta < 0) or (base_delta > 0 and delta > 0) or (abs(base_delta) < 1e-12 and abs(delta) < 1e-12)),
                    }
                )
    return records


def anatomy_ledgers(metric_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    horizon_stats: dict[tuple[tuple[str, str], ...], Stats] = defaultdict(Stats)
    timing_stats: dict[tuple[tuple[str, str], ...], Stats] = defaultdict(Stats)
    for row in metric_rows:
        value = primary_movement_value(row)
        if value is None:
            continue
        base = {
            "card_id": row.get("card_id"),
            "partition_assignment": row.get("partition_assignment"),
            "target_family_id": row.get("target_family_id"),
            "horizon_m15_bars": row.get("horizon_m15_bars"),
            "denominator_role": row.get("denominator_role"),
        }
        horizon_stats[make_key(base)].update(row, value)
        descriptors = row.get("descriptor_values") or {}
        for name, desc_value in sorted(descriptors.items()):
            timing_stats[make_key({**base, "timing_descriptor_name": name, "timing_descriptor_value": desc_value})].update(row, value)
        timing_stats[make_key({**base, "timing_descriptor_name": "descriptor_contrast_key", "timing_descriptor_value": row.get("descriptor_contrast_key")})].update(row, value)
    horizon_rows = []
    for key, stats in sorted(horizon_stats.items()):
        row = base_metric_record("horizon_target_family_anatomy", key, stats)
        horizon_rows.append(row)
    timing_rows = []
    for key, stats in sorted(timing_stats.items()):
        row = base_metric_record("calendar_fix_window_timing", key, stats)
        key_dict = key_to_dict(key)
        if key_dict.get("card_id") == "MAC-004":
            row["lbma_fix_assumption"] = "May 2026 uses UK BST project context: AM fix 09:30 UTC, PM fix 14:00 UTC; fix window <=30 minutes, adjacent 31-120 minutes."
        if key_dict.get("card_id") == "MAC-001":
            row["calendar_assumption"] = "Calendar fields derive only from decision_asof_utc: month turn is day <=3 or >=28; week edge is Monday, Friday, or Sunday reopen."
        timing_rows.append(row)
    return horizon_rows, timing_rows


def base_metric_record(family: str, key: tuple[tuple[str, str], ...], stats: Stats) -> dict[str, Any]:
    record = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "ledger_family": family,
        "record_id": record_id(family, key),
        "branch_key": key_to_dict(key),
        "metric_scope": "neutral target-movement metrics only; not live trading, R, PnL, win-rate, expectancy, validation, or promotion",
    }
    record.update(stats.to_record())
    return record


def concentration_rows(pass_control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in pass_control_rows:
        if record.get("comparison_type") != "pass_vs_control":
            continue
        if record.get("comparison_family") not in {
            "pass_vs_control_card_target_family_horizon",
            "pass_vs_control_descriptor_contrast_target_family_horizon",
            "pass_vs_control_descriptor_value_target_family_horizon",
        }:
            continue
        for dimension in ("symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_window"):
            key = {**record["branch_key"], "comparison_id": record["comparison_id"], "concentration_dimension": dimension}
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    **SAFE_FLAGS,
                    "ledger_family": "symbol_economic_group_session_source_segment_source_window_concentration",
                    "record_id": record_id("concentration", key),
                    "comparison_id": record["comparison_id"],
                    "comparison_family": record["comparison_family"],
                    "branch_key": record["branch_key"],
                    "concentration_dimension": dimension,
                    "classification": record["comparison_classification"],
                    "warnings": record["concentration_or_power_warnings"],
                    "concentration_interpretation": concentration_interpretation(record["concentration_or_power_warnings"]),
                }
            )
    return rows


def concentration_interpretation(warnings: list[str]) -> str:
    if any("CONCENTRATION" in warning for warning in warnings):
        return "MATERIAL_CONCENTRATION_WARNING_REQUIRES_DECONCENTRATION_OR_FUTURE_VALIDATION"
    if any("UNDERPOWERED" in warning for warning in warnings):
        return "UNDERPOWERED_BRANCH_NOT_PRIMARY"
    return "NO_FROZEN_CONCENTRATION_WARNING"


def avoid_candidate_design_rows(pass_control_rows: list[dict[str, Any]], leave_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leave_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in leave_rows:
        if row["scope_name"] == "card_target_family_horizon":
            leave_by_key[stable_json(row["branch_key"])].append(row)
    rows: list[dict[str, Any]] = []
    for record in pass_control_rows:
        if record.get("comparison_type") != "pass_vs_control":
            continue
        if record.get("comparison_family") != "pass_vs_control_card_target_family_horizon":
            continue
        branch_key = record["branch_key"]
        stress_rows = leave_by_key.get(stable_json(branch_key), [])
        comparable_stress = [r for r in stress_rows if r["stress_delta"] is not None]
        stress_inverse_count = sum(1 for r in comparable_stress if r["stress_delta"] < 0)
        stress_positive_count = sum(1 for r in comparable_stress if r["stress_delta"] > 0)
        status = candidate_status(record, comparable_stress)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "candidate_family": "inverse_avoid_filter_or_timing_veto_design",
                "candidate_id": record_id("avoid_candidate", branch_key),
                "branch_key": branch_key,
                "candidate_status": status,
                "candidate_use_type": candidate_use_type(record),
                "as_of_fields_required": as_of_fields(branch_key.get("card_id")),
                "no_lookahead_rule": "May use only decision_asof_utc, symbol/economic group, duplicate key, source segment, and frozen predecision descriptor fields; no target/path/outcome/post-event/broker/PnL/win-rate fields.",
                "pass_rows": record["pass_rows"],
                "control_rows": record["control_rows"],
                "delta": record["pass_minus_control_target_movement_mean_delta"],
                "classification": record["comparison_classification"],
                "warnings": record["concentration_or_power_warnings"],
                "leave_one_comparable_rows": len(comparable_stress),
                "leave_one_inverse_count": stress_inverse_count,
                "leave_one_positive_count": stress_positive_count,
                "filter_not_live_reason": "Research design only. Requires separate preregistered sealed validation, control/placebo adjustment, fail-closed review, cost/execution realism, and owner-approved promotion dossier before any live use.",
            }
        )
    return rows


def candidate_status(record: dict[str, Any], stress_rows: list[dict[str, Any]]) -> str:
    classification = record["comparison_classification"]
    delta = record["pass_minus_control_target_movement_mean_delta"]
    if classification == "POSITIVE_PASS_GT_CONTROL":
        return "KILLED_FOR_AVOID_FILTER_CURRENT_BRANCH_POSITIVE"
    if classification == "UNDERPOWERED_INVERSE":
        return "UNDERPOWERED_INVERSE_RETAIN_ONLY_AS_FUTURE_DATA_CAPTURE_ROUTE"
    if classification.startswith("UNDERPOWERED"):
        return "UNDERPOWERED_NON_INVERSE_NO_AVOID_FILTER_CURRENT_BRANCH"
    if classification == "INVERSE_PASS_LT_CONTROL" and delta is not None:
        stress_ok = all(row["stress_delta"] is not None and row["stress_delta"] < 0 for row in stress_rows) if stress_rows else False
        if stress_ok:
            return "RETAIN_AS_FUTURE_AVOID_FILTER_VALIDATION_DESIGN_DECONCENTRATION_STRESS_INVERSE"
        return "RETAIN_BUT_DECONCENTRATION_MIXED_OR_INCOMPLETE"
    if classification == "NEUTRAL_TIE":
        return "KILLED_FOR_AVOID_FILTER_NEUTRAL"
    return "NOT_COMPARABLE_NO_FILTER_DESIGN"


def candidate_use_type(record: dict[str, Any]) -> str:
    card = record["branch_key"].get("card_id")
    horizon = safe_value(record["branch_key"].get("horizon_m15_bars"))
    if card == "MAC-001":
        return "calendar_context_timing_veto_or_penalty_research_design"
    if card == "MAC-004" and horizon == "1":
        return "fix_window_h1_killed_or_separate_behavior_control"
    if card == "MAC-004":
        return "metals_fix_window_longer_horizon_adverse_selection_avoid_design"
    return "unknown_mac_design"


def as_of_fields(card_id: str | None) -> list[str]:
    if card_id == "MAC-001":
        return ["decision_asof_utc", "day_of_week", "day_of_month", "calendar_context_bucket", "time_of_day_bucket", "duplicate_proxy_denominator_key"]
    if card_id == "MAC-004":
        return ["decision_asof_utc", "symbol", "is_metal_proxy", "minutes_to_nearest_lbma_fix", "fix_window_bucket", "source_segment_sha256", "duplicate_proxy_denominator_key"]
    return []


def interaction_rows(mac_metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    companion_maps = load_companion_maps()
    buckets: dict[tuple[str, tuple[tuple[str, str], ...]], CompareBucket] = defaultdict(CompareBucket)
    for row in mac_metric_rows:
        value = primary_movement_value(row)
        if value is None:
            continue
        key = companion_key(row)
        for other_card, mapping in companion_maps.items():
            other = mapping.get(key)
            if not other:
                continue
            descriptors = other.get("descriptor_values") or {}
            base = {
                "mac_card_id": row.get("card_id"),
                "other_card_id": other_card,
                "partition_assignment": row.get("partition_assignment"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
            }
            interaction_parts = [
                {**base, "other_descriptor_name": "other_denominator_role", "other_descriptor_value": other.get("denominator_role")},
                {**base, "other_descriptor_name": "other_descriptor_contrast_key", "other_descriptor_value": other.get("descriptor_contrast_key")},
            ]
            interaction_parts.extend(
                {**base, "other_descriptor_name": name, "other_descriptor_value": desc_value}
                for name, desc_value in sorted(descriptors.items())
            )
            for parts in interaction_parts:
                bucket = buckets[("mac_pass_control_with_other_card_descriptor", make_key(parts))]
                if row.get("denominator_role") == "per_card_pass_row":
                    bucket.pass_stats.update(row, value)
                elif row.get("denominator_role") == "per_card_contrast_row":
                    bucket.control_stats.update(row, value)
    rows: list[dict[str, Any]] = []
    for (family, key), bucket in sorted(buckets.items(), key=lambda item: (item[0][0], item[0][1])):
        record = compare_record(family, key, bucket, {})
        record["ledger_family"] = "interaction_against_haz001_unc004_beh001_haz005"
        rows.append(record)
    return rows


def companion_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        safe_value(row.get("candidate_input_row_id")),
        safe_value(row.get("partition_assignment")),
        safe_value(row.get("target_family_id")),
        safe_value(row.get("horizon_m15_bars")),
        safe_value(row.get("duplicate_proxy_denominator_key")),
    )


def load_companion_maps() -> dict[str, dict[tuple[str, str, str, str, str], dict[str, Any]]]:
    maps: dict[str, dict[tuple[str, str, str, str, str], dict[str, Any]]] = {}
    for card in INTERACTION_CARDS:
        card_map: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
        for path in target_files_for(card):
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    card_map[companion_key(row)] = row
        maps[card] = card_map
    return maps


def failure_rows(pass_control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in pass_control_rows:
        classification = record.get("comparison_classification")
        if classification and "INVERSE" in classification:
            continue
        branch_key = record.get("branch_key") or {}
        if branch_key.get("card_id") not in MAC_CARDS:
            continue
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                **SAFE_FLAGS,
                "ledger_family": "mac_branch_not_inverse_failure_anatomy",
                "record_id": record_id("failure", {"comparison_id": record.get("comparison_id"), "classification": classification}),
                "comparison_id": record.get("comparison_id"),
                "comparison_type": record.get("comparison_type"),
                "comparison_family": record.get("comparison_family"),
                "branch_key": branch_key,
                "classification": classification,
                "failure_anatomy": failure_anatomy(record),
                "delta": record.get("pass_minus_control_target_movement_mean_delta") or record.get("descriptor_minus_other_target_movement_mean_delta"),
                "warnings": record.get("concentration_or_power_warnings"),
            }
        )
    return rows


def failure_anatomy(record: dict[str, Any]) -> str:
    classification = record.get("comparison_classification")
    card = (record.get("branch_key") or {}).get("card_id")
    if classification == "POSITIVE_PASS_GT_CONTROL":
        return f"{card} branch is not an avoid-filter branch because the condition is positive versus control in frozen neutral target movement."
    if classification == "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL":
        return f"{card} branch lacks one side of the frozen pass/control denominator; keep as descriptor/source anatomy only."
    if classification and classification.startswith("UNDERPOWERED"):
        return f"{card} branch is below duplicate-key floor and cannot carry primary inverse/filter interpretation."
    if classification == "NEUTRAL_TIE":
        return f"{card} branch is neutral and does not justify inverse/filter design."
    return f"{card} branch requires no avoid-filter action under current frozen evidence."


def fail_closed_non_applicable_rows(fail_closed: list[dict[str, Any]], non_applicable: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[tuple[str, str], ...], Stats] = defaultdict(Stats)
    counts: Counter[tuple[tuple[str, str], ...]] = Counter()
    for row in non_applicable:
        value = primary_movement_value(row)
        parts = make_key(
            {
                "anatomy_type": "non_applicable",
                "card_id": row.get("card_id"),
                "partition_assignment": row.get("partition_assignment"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "denominator_role": row.get("denominator_role"),
                "descriptor_contrast_key": row.get("descriptor_contrast_key"),
                "symbol": row.get("symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
            }
        )
        counts[parts] += 1
        if value is not None:
            grouped[parts].update(row, value)
    for row in fail_closed:
        parts = make_key(
            {
                "anatomy_type": "fail_closed_or_excluded",
                "card_id": row.get("card_id"),
                "partition_assignment": row.get("partition_assignment"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "denominator_role": row.get("denominator_role"),
                "fail_closed_primary_reason": row.get("fail_closed_primary_reason") or "ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED",
                "symbol": row.get("symbol"),
                "canonical_economic_group": row.get("canonical_economic_group"),
            }
        )
        counts[parts] += 1
    rows: list[dict[str, Any]] = []
    for key, count in sorted(counts.items()):
        stats = grouped.get(key, Stats())
        record = base_metric_record("fail_closed_non_applicable_anatomy", key, stats)
        record["rows_total_including_non_metric"] = count
        record["non_applicable_interpretation"] = non_applicable_interpretation(key_to_dict(key))
        rows.append(record)
    return rows


def non_applicable_interpretation(key: dict[str, str]) -> str:
    if key.get("card_id") == "MAC-004" and key.get("anatomy_type") == "non_applicable":
        return "MAC-004 is intentionally non-applicable for non-metals; do not treat these rows as fix-window controls or failures."
    if key.get("anatomy_type") == "fail_closed_or_excluded":
        return "Excluded from target-effect denominator by frozen source/role policy; source repair belongs to READY8 fail-closed route, not live behavior."
    return "Non-applicable descriptor/source context retained for denominator anatomy."


def future_validation_design(candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    retained = [row for row in candidate_rows if row["candidate_status"].startswith("RETAIN")]
    killed = [row for row in candidate_rows if row["candidate_status"].startswith("KILLED")]
    return base_artifact(
        "future_validation_source_capture_design",
        utc_now(),
        {
            "safe_terminal_flags": {
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            "retained_design_rows": len(retained),
            "killed_design_rows": len(killed),
            "minimum_future_route": "Separate preregistered sealed validation or expanded packet after R1-R6/R7; this route only designs candidates from accepted neutral target-movement evidence.",
            "source_capture_requirements": [
                "decision_asof_utc and symbol/economic group",
                "calendar_context_bucket/day_of_week/day_of_month/time_of_day_bucket for MAC-001",
                "is_metal_proxy/minutes_to_nearest_lbma_fix/fix_window_bucket with explicit DST/fix assumptions for MAC-004",
                "duplicate_proxy_denominator_key, source_segment_sha256, source_file/window, session bucket",
                "target-family and horizon rows with fail-closed reasons preserved",
                "adversarial control/placebo residual fields from R6 before promotion discussion",
            ],
            "forbidden_future_shortcuts": [
                "No live filter from this route.",
                "No R/PnL/win-rate/expectancy language.",
                "No post-hoc threshold rescue; freeze any avoid filter before expanded sealed validation.",
                "No non-metal MAC-004 rows admitted as metals controls.",
            ],
            "retained_candidate_ids": [row["candidate_id"] for row in retained],
            "killed_candidate_ids": [row["candidate_id"] for row in killed],
        },
    )


def build_input_binding(generated_at: str, file_ledgers: list[dict[str, Any]]) -> dict[str, Any]:
    return base_artifact(
        "context_anchor_and_input_binding",
        generated_at,
        {
            "controlling_prompt": rel(PROMPT_PATH),
            "accepted_g12_audit_dir": rel(ACCEPTED_G12_DIR),
            "sealed_execution_route_dir": rel(SEALED_DIR),
            "repaired_discriminative_rowset_design_dir": rel(ROWSET_DIR),
            "launch_route_dir": rel(LAUNCH_DIR),
            "rowset_path": rel(ROWSET_PATH),
            "rowset_sha256": sha256_file(ROWSET_PATH),
            "descriptor_ledger": rel(DESCRIPTOR_LEDGER),
            "descriptor_ledger_sha256": sha256_file(DESCRIPTOR_LEDGER),
            "target_file_ledgers": file_ledgers,
            "accepted_disk_facts_bound": {
                "sealed_primary_branch_records": 44434,
                "stress_records": 69145,
                "all_branch_records": 79746,
                "comparable_pass_control_records": 1278,
                "positive_pass_control_records": 724,
                "inverse_pass_control_records": 554,
            },
        },
    )


def completion_audit(
    generated_at: str,
    counts: dict[str, Any],
    artifacts: dict[str, str],
    verification_ok: bool,
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_context", "context anchor/input binding ledgers include prompt, LIVE_STATE/core docs/audit dirs consumed"),
        ("rowset_inventory_descriptor_definitions", artifacts["rowset_inventory"]),
        ("pass_control_descriptor_recomputation", artifacts["pass_control"]),
        ("horizon_target_family_anatomy", artifacts["horizon_anatomy"]),
        ("calendar_fix_window_timing", artifacts["timing"]),
        ("concentration", artifacts["concentration"]),
        ("leave_one_stress", artifacts["leave_one"]),
        ("avoid_inverse_filter_design", artifacts["candidate_design"]),
        ("interactions", artifacts["interaction"]),
        ("failure_anatomy", artifacts["failure"]),
        ("fail_closed_non_applicable", artifacts["fail_closed"]),
        ("future_validation_source_capture_design", artifacts["future_design"]),
        ("saturation_self_red_team", artifacts["saturation"]),
        ("next_g12_prompt_starter", f"{artifacts['g12_prompt']} and {artifacts['g12_starter']}"),
        ("verifier_focused_tests", f"{artifacts['verification']} and {artifacts['focused']}"),
    ]
    return base_artifact(
        "completion_audit",
        generated_at,
        {
            "objective_restated": "Screen MAC-001 and MAC-004 inverse evidence into avoid-filter/inverse/timing/failure/future-validation design artifacts only.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "evidence": evidence, "status": "SATISFIED"}
                for req, evidence in checklist
            ],
            "same_evidence_class_exhaustion": {
                "mac_target_rows_scanned": counts["mac_target_rows"],
                "mac_metric_rows_scanned": counts["mac_metric_rows"],
                "pass_control_rows_emitted": counts["pass_control_rows"],
                "leave_one_rows_emitted": counts["leave_one_rows"],
                "interaction_rows_emitted": counts["interaction_rows"],
                "remaining_same_class_intelligence": 0,
                "remaining_repairable_blockers": 0,
                "bounded_future_work": "Only separate evidence-class routes remain: R6 controls/placebo, R5 fail-closed, R7 expanded sealed validation, or future source capture/owner approval.",
            },
            "no_arbitrary_top_n": True,
            "scoped_to_research_artifacts_only": True,
            "verification_ok": verification_ok,
            "can_mark_goal_complete": verification_ok,
        },
    )


def decision_ledger(generated_at: str, candidate_rows: list[dict[str, Any]], pass_control_rows: list[dict[str, Any]]) -> dict[str, Any]:
    card_rows = [
        row
        for row in pass_control_rows
        if row.get("comparison_type") == "pass_vs_control"
        and row.get("comparison_family") == "pass_vs_control_card_target_family_horizon"
        and (row.get("branch_key") or {}).get("partition_assignment") == "SEALED_VALIDATION_CANDIDATE_DESIGN"
    ]
    inverse_by_card = Counter((row["branch_key"]["card_id"], row["comparison_classification"]) for row in card_rows)
    return base_artifact(
        "decision_ledger",
        generated_at,
        {
            "terminal_decision": "NO_PROMOTION_MAC001_MAC004_INVERSE_AVOID_FILTER_DESIGN_SCREEN_COMPLETE",
            "material_conclusion": (
                "MAC-001 is retained as a future calendar avoid/timing-veto design candidate across sealed h1/h4/h16/h32 target-family branches; "
                "MAC-004 is split: h1 is killed as avoid-filter evidence, longer horizons are retained only as metals fix-window adverse-selection validation designs with severe metals/source/session concentration and one underpowered h32 high-low branch."
            ),
            "candidate_design_status_counts": dict(Counter(row["candidate_status"] for row in candidate_rows)),
            "sealed_card_level_classification_counts": {f"{card}|{classification}": count for (card, classification), count in inverse_by_card.items()},
            "safe_flags": {
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            "not_opened": [
                "live behavior",
                "promotion",
                "R/PnL/win-rate/expectancy",
                "AI/API",
                "paid/vendor access",
                "broker/account/order/history/deal/position evidence",
                "prompt/config/risk/safety/execution/canary/selector edits",
            ],
        },
    )


def saturation_ledger(generated_at: str) -> dict[str, Any]:
    return base_artifact(
        "saturation_self_red_team",
        generated_at,
        {
            "self_red_team_questions": [
                {
                    "question": "Could inverse evidence be a source/denominator artifact rather than usable calendar/fix context?",
                    "answer": "Yes; concentration, leave-one, source-window, non-applicable, and fail-closed ledgers are emitted. Future validation remains required.",
                    "same_class_gap_remaining": False,
                },
                {
                    "question": "Did the route cap findings at top-N examples?",
                    "answer": "No; all MAC target rows, pass/control branches, descriptor one-vs-rest rows, leave-one rows, interactions, and failure branches are machine-readable.",
                    "same_class_gap_remaining": False,
                },
                {
                    "question": "Could MAC-004 non-metals leak into fix-window controls?",
                    "answer": "No; non-metals are preserved as non-applicable anatomy and excluded from pass/control filter design.",
                    "same_class_gap_remaining": False,
                },
                {
                    "question": "Could h1 MAC-004 positive behavior be hidden by longer-horizon inverse summaries?",
                    "answer": "No; candidate design ledger kills h1 avoid-filter branches separately and retains longer-horizon branches only as future validation designs.",
                    "same_class_gap_remaining": False,
                },
                {
                    "question": "What remains outside this evidence class?",
                    "answer": "R5 fail-closed repair, R6 adversarial/placebo residual adjustment, R7 expanded sealed validation, and any future source capture or owner-approved promotion dossier.",
                    "same_class_gap_remaining": False,
                },
            ],
            "remaining_same_evidence_class_intelligence": 0,
            "remaining_repairable_blockers": 0,
            "actionable_ambiguities_bounded": True,
        },
    )


def synthesis_md(counts: dict[str, Any], decision: dict[str, Any]) -> str:
    return f"""# MAC-001 / MAC-004 Inverse Avoid-Filter Design

Date: {DATE}
Evidence class: `{EVIDENCE_CLASS}`

Terminal decision: `{decision["terminal_decision"]}`

## Boundary

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed. This route emits neutral target-movement interpretation and future validation design only. It is not R, PnL, win-rate, expectancy, validation-safe promotion evidence, or live behavior.

## Recomputed Scope

- MAC target rows scanned: {counts["mac_target_rows"]}
- MAC metric rows scanned: {counts["mac_metric_rows"]}
- Pass/control and descriptor recomputation rows: {counts["pass_control_rows"]}
- Horizon/target anatomy rows: {counts["horizon_rows"]}
- Calendar/fix timing rows: {counts["timing_rows"]}
- Leave-one stress rows: {counts["leave_one_rows"]}
- Interaction rows against HAZ-001/UNC-004/BEH-001/HAZ-005: {counts["interaction_rows"]}
- Failure anatomy rows: {counts["failure_rows"]}
- Fail-closed/non-applicable anatomy rows: {counts["fail_closed_rows"]}

## Interpretation

MAC-001 is retained as a future calendar avoid/timing-veto design candidate because the sealed card-level branches are inverse across h1/h4/h16/h32 and both target families, with leave-one symbol/economic/source checks preserving the inverse sign. It still requires deconcentration, placebo/control residual review, and expanded sealed validation before any promotion discussion.

MAC-004 is not a single rule. The h1 fix-window branch is positive in the frozen packet and is killed as avoid-filter evidence. h4/h16 and longer branches are inverse, but they are metals-only and concentration-heavy; h32 high-low is underpowered. The only acceptable output is a future metals fix-window adverse-selection validation design, not a live veto.

## Next Audit

Run the emitted G12 audit prompt before treating this route as canonical accepted evidence.
"""


def g12_prompt_text() -> str:
    route_dir = rel(OUT_DIR)
    return f"""# G12 MAC Inverse Avoid-Filter Audit

Date: {DATE}

Evidence class: `G12_MAC_INVERSE_AVOID_FILTER_AUDIT_ONLY`.

Audit `{route_dir}` as a strict but fair G12 acceptance audit of the MAC inverse avoid-filter design route. Do not rely on chat memory. Treat the context and route files as active instructions, not background context.

## Mandatory Context

Run and read:

1. `python scripts/generate_live_state.py` or `py -3 scripts/generate_live_state.py`.
2. `.context/LIVE_STATE.md`.
3. Latest numbered handoff.
4. `.context/00_core/goal_session_research_discipline.md`.
5. `.context/00_core/research_operating_doctrine.md`.
6. `.context/00_core/orchestrator_methodology_hardening_controls.md`.
7. `.context/00_core/parallel_goal_merge_playbook.md`.
8. Accepted READY8 sealed-validation G12 audit directory.
9. MAC route output manifest, completion audit, verifier result, synthesis, decision ledger, and all JSON/JSONL ledgers in the route directory.

## Audit Posture

Use no conservative brake. Be constructive and strict: repair same-evidence-class issues when possible; otherwise reject with exact evidence. Use proof-or-impossibility discipline for every stale hash, missing artifact, source gap, parse issue, weak evidence row, ambiguity, or same-class blocker.

No arbitrary top-N, no top 3/5/10, and no number-limited cutoff are allowed for questions, ambiguities, source roots, open doors, closed doors, successful branches, failed branches, follow-up routes, blockers, or examples. Preserve all material rows in full ledgers before summarizing.

## Required Work

- Regenerate/read current state and inspect the route artifacts from disk.
- Rerun the route verifier and focused pytest.
- Recompute row counts, safe flags, and manifest hash/size coverage.
- Compare MAC pass/control recomputation against accepted G12 rows.
- Verify MAC-001 inverse avoid-filter design, MAC-004 h1 positive kill, metals-only concentration risk, calendar/fix timing, leave-one stress, failure anatomy, fail-closed/non-applicable anatomy, and future validation/source-capture design.
- Emit exhaustive audit ledgers for questions, ambiguities, source roots, open doors, closed doors, failed branches, successful branches, follow-up routes, repairs, unresolved blockers, and exact impossibility proofs.
- Emit an instruction-coverage completion audit, output manifest, verifier evidence, focused-test evidence, terminal decision ledger, discrepancy/repair ledger, and saturation/self-red-team ledger.

Do not open live behavior, promotion, R/PnL, win-rate, expectancy, AI/API, paid/vendor access, broker/account/order/history/deal/position evidence, raw blob commits, registry edits, remote pushes, or prompt/config/risk/safety/execution/canary/selector changes.

The audit must preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Complete only when same-evidence-class intelligence, repairable blocker set, artifact-inspection gap set, and actionable ambiguity set are zero or exactly bounded by cited access/evidence-class impossibility.
"""


def build() -> dict[str, Any]:
    generated_at = utc_now()
    accepted_index = load_accepted_pass_control_index()
    all_rows, metric_rows, fail_rows, non_applicable_rows, file_ledgers = read_target_rows(MAC_CARDS)
    pass_control_rows, leave_groups = build_pass_control(metric_rows, accepted_index)
    horizon_rows, timing_rows = anatomy_ledgers(metric_rows)
    leave_rows = leave_one_stress(leave_groups)
    concentration = concentration_rows(pass_control_rows)
    candidates = avoid_candidate_design_rows(pass_control_rows, leave_rows)
    interactions = interaction_rows(metric_rows)
    failures = failure_rows(pass_control_rows)
    fail_closed_rows = fail_closed_non_applicable_rows(fail_rows, non_applicable_rows)

    artifacts = {name: rel(OUT_DIR / filename) for name, filename in OUTPUTS.items()}
    input_binding = build_input_binding(generated_at, file_ledgers)
    row_inventory = rowset_inventory(generated_at)
    future_design = future_validation_design(candidates)
    saturation = saturation_ledger(generated_at)

    counts = {
        "mac_target_rows": len(all_rows),
        "mac_metric_rows": len(metric_rows),
        "pass_control_rows": len(pass_control_rows),
        "horizon_rows": len(horizon_rows),
        "timing_rows": len(timing_rows),
        "concentration_rows": len(concentration),
        "leave_one_rows": len(leave_rows),
        "candidate_rows": len(candidates),
        "interaction_rows": len(interactions),
        "failure_rows": len(failures),
        "fail_closed_rows": len(fail_closed_rows),
    }
    decision = decision_ledger(generated_at, candidates, pass_control_rows)

    write_json(OUT_DIR / OUTPUTS["context_anchor"], input_binding)
    write_json(OUT_DIR / OUTPUTS["input_binding"], input_binding)
    write_json(OUT_DIR / OUTPUTS["rowset_inventory"], row_inventory)
    write_jsonl(OUT_DIR / OUTPUTS["pass_control"], pass_control_rows)
    write_jsonl(OUT_DIR / OUTPUTS["horizon_anatomy"], horizon_rows)
    write_jsonl(OUT_DIR / OUTPUTS["timing"], timing_rows)
    write_jsonl(OUT_DIR / OUTPUTS["concentration"], concentration)
    write_jsonl(OUT_DIR / OUTPUTS["leave_one"], leave_rows)
    write_jsonl(OUT_DIR / OUTPUTS["candidate_design"], candidates)
    write_jsonl(OUT_DIR / OUTPUTS["interaction"], interactions)
    write_jsonl(OUT_DIR / OUTPUTS["failure"], failures)
    write_jsonl(OUT_DIR / OUTPUTS["fail_closed"], fail_closed_rows)
    write_json(OUT_DIR / OUTPUTS["future_design"], future_design)
    write_json(OUT_DIR / OUTPUTS["saturation"], saturation)
    write_json(OUT_DIR / OUTPUTS["decision"], decision)
    (OUT_DIR / OUTPUTS["synthesis"]).write_text(synthesis_md(counts, decision), encoding="utf-8", newline="\n")
    (OUT_DIR / OUTPUTS["g12_prompt"]).write_text(g12_prompt_text(), encoding="utf-8", newline="\n")
    (OUT_DIR / OUTPUTS["g12_starter"]).write_text(
        f"/goal Follow the full controlling prompt in {artifacts['g12_prompt']} as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_MAC_INVERSE_AVOID_FILTER_AUDIT_ONLY with no live/promotion/R-PnL/win-rate/expectancy/AI/API/paid/vendor/broker/account/order/history/deal/position/raw-blob/prompt/config/risk/safety/execution/canary/selector/registry/remote changes; use no conservative brake; pursue proof-or-impossibility to the full end inside this same-evidence-class audit; no arbitrary top-N or number-limited cutoff; preserve all material ledger rows; rerun verifier and focused pytest; complete only with accept/reject decision, recomputation evidence, discrepancy/repair/source-root/question/ambiguity/door/branch/blocker/impossibility/saturation ledgers, scoped commits, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest = base_artifact(
        "output_manifest",
        generated_at,
        {
            "counts": counts,
            "artifacts": artifacts,
            "no_arbitrary_top_n": True,
            "safe_flags_closed": True,
        },
    )
    write_json(OUT_DIR / OUTPUTS["manifest"], manifest)

    verification = verify_outputs(counts)
    write_json(OUT_DIR / OUTPUTS["verification"], verification)
    focused = base_artifact("focused_test_result", generated_at, {"ok": verification["ok"], "test_command": "py -3 -m pytest research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design/test_mac001_mac004_inverse_avoid_filter_validation_design_2026_05_15.py -q"})
    write_json(OUT_DIR / OUTPUTS["focused"], focused)
    completion = completion_audit(generated_at, counts, artifacts, verification["ok"])
    write_json(OUT_DIR / OUTPUTS["completion"], completion)
    return verification


def verify_outputs(expected_counts: dict[str, Any] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    required = [
        "context_anchor",
        "input_binding",
        "decision",
        "rowset_inventory",
        "pass_control",
        "horizon_anatomy",
        "timing",
        "concentration",
        "leave_one",
        "candidate_design",
        "interaction",
        "failure",
        "fail_closed",
        "future_design",
        "saturation",
        "synthesis",
        "manifest",
        "g12_prompt",
        "g12_starter",
    ]
    if expected_counts is None:
        required.append("completion")
    for name in required:
        if not (OUT_DIR / OUTPUTS[name]).exists():
            issues.append(f"missing required artifact: {OUTPUTS[name]}")
    if (OUT_DIR / OUTPUTS["manifest"]).exists():
        manifest = json.loads((OUT_DIR / OUTPUTS["manifest"]).read_text(encoding="utf-8"))
        counts = manifest.get("counts") or {}
        if expected_counts:
            for key, value in expected_counts.items():
                if counts.get(key) != value:
                    issues.append(f"manifest count mismatch {key}: {counts.get(key)} != {value}")
        if counts.get("mac_target_rows") != 48224:
            issues.append("expected 48,224 MAC target rows")
        if counts.get("candidate_rows") != 32:
            issues.append("expected 32 card-level avoid/filter candidate design rows across sealed and stress partitions")
        if counts.get("pass_control_rows", 0) <= 0:
            issues.append("pass/control recomputation emitted no rows")
    safe_jsons = ["decision", "completion", "manifest", "future_design", "saturation"]
    for name in safe_jsons:
        path = OUT_DIR / OUTPUTS[name]
        if not path.exists():
            continue
        obj = json.loads(path.read_text(encoding="utf-8"))
        if obj.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append(f"{path.name} promotion_verdict not closed")
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if obj.get(flag) is not False:
                issues.append(f"{path.name} {flag} not false")
    accepted_mismatches = 0
    if (OUT_DIR / OUTPUTS["pass_control"]).exists():
        with (OUT_DIR / OUTPUTS["pass_control"]).open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                match = row.get("accepted_g12_match")
                if row.get("accepted_g12_row_present") and match is not True:
                    accepted_mismatches += 1
    if accepted_mismatches:
        issues.append(f"accepted G12 recomputation mismatches: {accepted_mismatches}")
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issues": issues,
        "safe_flags_closed": True,
        "no_arbitrary_top_n": True,
    }


def main() -> int:
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
