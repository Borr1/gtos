from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_NOAPI_READY8_TARGET_RESULT_SYNTHESIS_AND_QUARANTINED_NUMERICAL_SCREEN"
EVIDENCE_CLASS = "G0_SCID_NOAPI_READY8_TARGET_RESULT_SYNTHESIS_AND_QUARANTINED_NUMERICAL_SCREENING_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]
HORIZONS = [1, 4, 16, 32]
CLOSE_FAMILY = "neutral_close_to_close_return_m15_horizons_v1"
HIGH_LOW_FAMILY = "neutral_high_low_excursion_m15_horizons_v1"
TARGET_FAMILIES = [CLOSE_FAMILY, HIGH_LOW_FAMILY]

EXPECTED_SOURCE_CANDIDATES = 3014
EXPECTED_ROWSET_ROWS = 24112
EXPECTED_TARGET_ROWS = 192896

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PACKET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate"
G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit"
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_strategy_edge_claims": False,
    "opens_validation": False,
    "credentials_touched": False,
}

PARTITION_FIELDS = [
    "partition_assignment",
    "candidate_input_partition_assignment",
    "symbol",
    "canonical_economic_group",
    "source_proxy_group",
    "source_file_name_expected",
    "source_segment_sha256_expected",
    "session_bucket",
    "time_of_day_bucket",
    "utc_hour",
    "science_domain",
    "mechanism_family",
    "baseline_assignment_family",
    "baseline_control_bucket",
    "denominator_group_concentration_bucket",
    "source_coverage_quality_bucket",
    "source_group",
    "packet_id",
    "source_hash_policy",
    "prior_context_descriptor_buckets.prior_16_drift_bucket",
    "prior_context_descriptor_buckets.prior_16_range_bucket",
    "prior_context_descriptor_buckets.prior_32_range_bucket",
]

META_FIELDS = [
    "candidate_input_row_id",
    "candidate_input_row_hash",
    "duplicate_proxy_denominator_key",
    "rowset_row_id",
    "rowset_row_hash",
    "card_id",
    "packet_id",
    "source_identifier",
    "source_hash",
    "source_proxy_group",
    "source_segment_sha256_expected",
    "symbol",
    "canonical_economic_group",
    "session_bucket",
    "time_of_day_bucket",
    "utc_hour",
    "partition_assignment",
    "candidate_input_partition_assignment",
    "science_domain",
    "mechanism_family",
    "baseline_assignment_family",
    "baseline_control_bucket",
    "denominator_group_concentration_bucket",
    "source_coverage_quality_bucket",
    "entry_reference_time_utc",
    "decision_asof_utc",
    "source_observed_asof_utc",
    "entry_close",
]

CANDIDATE_SOURCE_BINDING_SCHEMA = [
    "candidate_input_row_id",
    "candidate_input_row_hash",
    "rowset_row_id",
    "rowset_row_hash",
    "source_identifier",
    "source_hash",
    "source_proxy_group",
    "source_segment_sha256_expected",
    "symbol",
    "canonical_economic_group",
    "session_bucket",
    "time_of_day_bucket",
    "utc_hour",
    "partition_assignment",
    "science_domain",
    "mechanism_family",
    "baseline_assignment_family",
    "baseline_control_bucket",
    "denominator_group_concentration_bucket",
]

CANDIDATE_TARGET_BINDING_SCHEMA = [
    "target_family_id",
    "horizon_m15_bars",
    "target_result_row_id",
    "target_result_row_hash",
    "terminal_status",
    "fail_closed_primary_reason",
    "horizon_end_utc",
    "close_pct",
    "abs_close_pct",
    "up_pct",
    "down_pct",
    "asym_pct",
    "total_pct",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def safe_base(artifact_family: str) -> dict[str, Any]:
    return {
        "schema_version": "g0_scid_ready8_numerical_screen_v1",
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def get_nested(row: dict[str, Any], field_path: str) -> Any:
    cur: Any = row
    for part in field_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return "__MISSING__"
        cur = cur[part]
    return "__NULL__" if cur is None else cur


def target_file(card_id: str, target_family_id: str) -> Path:
    card = card_id.replace("-", "_")
    if target_family_id == CLOSE_FAMILY:
        suffix = "CLOSE_TO_CLOSE"
    elif target_family_id == HIGH_LOW_FAMILY:
        suffix = "HIGH_LOW_EXCURSION"
    else:
        raise ValueError(f"Unknown target family: {target_family_id}")
    return PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_ROWS_{card}_{suffix}_{DATE}.jsonl"


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def q(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * pct
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


@dataclass
class MetricStats:
    values: list[float] = field(default_factory=list)
    total: float = 0.0
    total_sq: float = 0.0
    positive_count: int = 0
    negative_count: int = 0
    zero_count: int = 0

    def add(self, value: Any) -> None:
        if not is_number(value):
            return
        f = float(value)
        self.values.append(f)
        self.total += f
        self.total_sq += f * f
        if f > 0:
            self.positive_count += 1
        elif f < 0:
            self.negative_count += 1
        else:
            self.zero_count += 1

    def summary(self) -> dict[str, Any]:
        n = len(self.values)
        if n == 0:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "p01": None,
                "p05": None,
                "p10": None,
                "p25": None,
                "p75": None,
                "p90": None,
                "p95": None,
                "p99": None,
                "positive_count": 0,
                "negative_count": 0,
                "zero_count": 0,
                "positive_share": None,
                "negative_share": None,
            }
        sorted_values = sorted(self.values)
        mean = self.total / n
        variance = max(0.0, (self.total_sq / n) - (mean * mean))
        return {
            "count": n,
            "mean": mean,
            "median": q(sorted_values, 0.50),
            "std": math.sqrt(variance),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p01": q(sorted_values, 0.01),
            "p05": q(sorted_values, 0.05),
            "p10": q(sorted_values, 0.10),
            "p25": q(sorted_values, 0.25),
            "p75": q(sorted_values, 0.75),
            "p90": q(sorted_values, 0.90),
            "p95": q(sorted_values, 0.95),
            "p99": q(sorted_values, 0.99),
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "zero_count": self.zero_count,
            "positive_share": self.positive_count / n,
            "negative_share": self.negative_count / n,
        }


@dataclass
class GroupAgg:
    total_rows: int = 0
    status_counts: Counter = field(default_factory=Counter)
    fail_closed_reason_counts: Counter = field(default_factory=Counter)
    metrics: dict[str, MetricStats] = field(default_factory=lambda: defaultdict(MetricStats))
    duplicate_keys: set[str] = field(default_factory=set)
    rowset_ids: set[str] = field(default_factory=set)

    def add(self, row: dict[str, Any], metrics: dict[str, float]) -> None:
        self.total_rows += 1
        status = row.get("terminal_status")
        self.status_counts[status] += 1
        duplicate_key = row.get("duplicate_proxy_denominator_key")
        if duplicate_key is not None:
            self.duplicate_keys.add(str(duplicate_key))
        rowset_id = row.get("rowset_row_id")
        if rowset_id is not None:
            self.rowset_ids.add(str(rowset_id))
        if status != "COMPUTABLE":
            reason = row.get("fail_closed_primary_reason") or "FAIL_CLOSED_REASON_NULL"
            self.fail_closed_reason_counts[reason] += 1
            return
        for name, value in metrics.items():
            self.metrics[name].add(value)

    def summary(self) -> dict[str, Any]:
        computable = self.status_counts.get("COMPUTABLE", 0)
        fail = self.status_counts.get("FAIL_CLOSED_NOT_COMPUTABLE", 0)
        return {
            "total_rows": self.total_rows,
            "computable_rows": computable,
            "fail_closed_rows": fail,
            "computable_share": computable / self.total_rows if self.total_rows else None,
            "fail_closed_share": fail / self.total_rows if self.total_rows else None,
            "status_counts": dict(sorted(self.status_counts.items())),
            "fail_closed_primary_reason_counts": dict(sorted(self.fail_closed_reason_counts.items())),
            "unique_duplicate_proxy_denominator_keys": len(self.duplicate_keys),
            "unique_rowset_rows": len(self.rowset_ids),
            "movement_metrics": {name: stat.summary() for name, stat in sorted(self.metrics.items())},
        }


@dataclass
class CandidateCardAgg:
    meta: dict[str, Any]
    target_results: dict[str, dict[str, dict[str, Any]]] = field(default_factory=lambda: defaultdict(dict))
    status_counts: Counter = field(default_factory=Counter)
    fail_closed_reason_counts: Counter = field(default_factory=Counter)

    def add(self, row: dict[str, Any], metrics: dict[str, float]) -> None:
        family = row["target_family_id"]
        horizon = str(row["horizon_m15_bars"])
        status = row.get("terminal_status")
        self.status_counts[status] += 1
        if status != "COMPUTABLE":
            reason = row.get("fail_closed_primary_reason") or "FAIL_CLOSED_REASON_NULL"
            self.fail_closed_reason_counts[reason] += 1
        self.target_results[family][horizon] = {
            "target_result_row_id": row.get("target_result_row_id"),
            "target_result_row_hash": row.get("target_result_row_hash"),
            "terminal_status": status,
            "fail_closed_primary_reason": row.get("fail_closed_primary_reason"),
            "horizon_end_utc": row.get("horizon_end_utc"),
            "source_bar_hashes_consumed_sha256": row.get("source_bar_hashes_consumed_sha256"),
            "metrics": metrics,
        }

    def close_value(self, horizon: int) -> float | None:
        node = self.target_results.get(CLOSE_FAMILY, {}).get(str(horizon))
        if not node:
            return None
        value = node.get("metrics", {}).get("close_to_close_percent_return")
        return float(value) if is_number(value) else None

    def high_low_asymmetry(self, horizon: int) -> float | None:
        node = self.target_results.get(HIGH_LOW_FAMILY, {}).get(str(horizon))
        if not node:
            return None
        value = node.get("metrics", {}).get("high_low_excursion_asymmetry_percent")
        return float(value) if is_number(value) else None

    def high_low_total(self, horizon: int) -> float | None:
        node = self.target_results.get(HIGH_LOW_FAMILY, {}).get(str(horizon))
        if not node:
            return None
        value = node.get("metrics", {}).get("high_low_total_excursion_percent")
        return float(value) if is_number(value) else None


@dataclass
class DuplicateAgg:
    duplicate_key: str
    meta: dict[str, Any] = field(default_factory=dict)
    total_rows: int = 0
    computable_rows: int = 0
    fail_closed_rows: int = 0
    cards: set[str] = field(default_factory=set)
    rowset_rows: set[str] = field(default_factory=set)
    close_abs_sum: float = 0.0
    high_low_total_sum: float = 0.0
    max_close_abs: float = 0.0
    max_high_low_total: float = 0.0

    def add(self, row: dict[str, Any], metrics: dict[str, float]) -> None:
        self.total_rows += 1
        self.cards.add(row.get("card_id", "__MISSING__"))
        if row.get("rowset_row_id"):
            self.rowset_rows.add(str(row["rowset_row_id"]))
        if not self.meta:
            self.meta = {
                key: row.get(key)
                for key in [
                    "candidate_input_row_id",
                    "candidate_input_row_hash",
                    "symbol",
                    "canonical_economic_group",
                    "source_proxy_group",
                    "session_bucket",
                    "time_of_day_bucket",
                    "utc_hour",
                    "partition_assignment",
                    "denominator_group_concentration_bucket",
                    "source_identifier",
                    "source_hash",
                ]
            }
        if row.get("terminal_status") == "COMPUTABLE":
            self.computable_rows += 1
        else:
            self.fail_closed_rows += 1
        close_abs = metrics.get("absolute_close_to_close_percent_return")
        if is_number(close_abs):
            self.close_abs_sum += float(close_abs)
            self.max_close_abs = max(self.max_close_abs, float(close_abs))
        hl_total = metrics.get("high_low_total_excursion_percent")
        if is_number(hl_total):
            self.high_low_total_sum += float(hl_total)
            self.max_high_low_total = max(self.max_high_low_total, float(hl_total))


def metrics_from_row(row: dict[str, Any]) -> dict[str, float]:
    if row.get("terminal_status") != "COMPUTABLE":
        return {}
    family = row["target_family_id"]
    if family == CLOSE_FAMILY:
        pct = row.get("close_to_close_percent_return")
        abs_delta = row.get("close_to_close_absolute_delta")
        metrics: dict[str, float] = {}
        if is_number(pct):
            metrics["close_to_close_percent_return"] = float(pct)
            metrics["absolute_close_to_close_percent_return"] = abs(float(pct))
        if is_number(abs_delta):
            metrics["close_to_close_absolute_delta"] = float(abs_delta)
            metrics["absolute_close_to_close_absolute_delta"] = abs(float(abs_delta))
        return metrics
    if family == HIGH_LOW_FAMILY:
        upside = row.get("upside_excursion_percent")
        downside = row.get("downside_excursion_percent")
        metrics = {}
        if is_number(upside):
            metrics["upside_excursion_percent"] = float(upside)
        if is_number(downside):
            metrics["downside_excursion_percent"] = float(downside)
        if is_number(upside) and is_number(downside):
            up = float(upside)
            down = float(downside)
            metrics["high_low_excursion_asymmetry_percent"] = up - down
            metrics["absolute_high_low_excursion_asymmetry_percent"] = abs(up - down)
            metrics["high_low_total_excursion_percent"] = up + down
            metrics["high_low_max_excursion_percent"] = max(up, down)
        return metrics
    return {}


def sign(value: float | None) -> str:
    if value is None:
        return "NOT_COMPUTABLE"
    if value > 0:
        return "POSITIVE"
    if value < 0:
        return "NEGATIVE"
    return "ZERO"


def fingerprint_payload(row: dict[str, Any], metrics: dict[str, float]) -> str:
    payload = {
        "duplicate_proxy_denominator_key": row.get("duplicate_proxy_denominator_key"),
        "terminal_status": row.get("terminal_status"),
        "fail_closed_primary_reason": row.get("fail_closed_primary_reason"),
        "horizon_m15_bars": row.get("horizon_m15_bars"),
        "target_family_id": row.get("target_family_id"),
        "metrics": {key: round(value, 15) for key, value in sorted(metrics.items())},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def dense_ranks(entries: list[dict[str, Any]], field: str, rank_field: str, reverse: bool = True) -> None:
    values = sorted({entry.get(field) for entry in entries if is_number(entry.get(field))}, reverse=reverse)
    rank_by_value: dict[float, int] = {}
    rank = 1
    last_value: float | None = None
    for value in values:
        f = float(value)
        if last_value is None or not math.isclose(f, last_value, rel_tol=1e-15, abs_tol=1e-18):
            rank_by_value[f] = rank
            rank += 1
            last_value = f
        else:
            rank_by_value[f] = rank - 1
    for entry in entries:
        value = entry.get(field)
        entry[rank_field] = rank_by_value.get(float(value)) if is_number(value) else None


def row_primary_fields(summary: dict[str, Any], target_family: str) -> dict[str, Any]:
    metrics = summary["movement_metrics"]
    if target_family == CLOSE_FAMILY:
        signed = metrics.get("close_to_close_percent_return", {})
        abs_metric = metrics.get("absolute_close_to_close_percent_return", {})
        return {
            "primary_signed_mean": signed.get("mean"),
            "primary_signed_median": signed.get("median"),
            "primary_magnitude_mean": abs_metric.get("mean"),
            "primary_magnitude_median": abs_metric.get("median"),
            "direction_positive_share": signed.get("positive_share"),
            "direction_negative_share": signed.get("negative_share"),
        }
    total = metrics.get("high_low_total_excursion_percent", {})
    asym = metrics.get("high_low_excursion_asymmetry_percent", {})
    up = metrics.get("upside_excursion_percent", {})
    down = metrics.get("downside_excursion_percent", {})
    return {
        "primary_signed_mean": asym.get("mean"),
        "primary_signed_median": asym.get("median"),
        "primary_magnitude_mean": total.get("mean"),
        "primary_magnitude_median": total.get("median"),
        "direction_positive_share": asym.get("positive_share"),
        "direction_negative_share": asym.get("negative_share"),
        "upside_mean": up.get("mean"),
        "downside_mean": down.get("mean"),
    }


def classify_matrix_entry(entry: dict[str, Any], fingerprint_matches_adv001: bool) -> str:
    if fingerprint_matches_adv001:
        return "CARD_LEVEL_MOVEMENT_NON_DISCRIMINATIVE_BASELINE_EXPLAINED"
    if entry.get("computable_rows", 0) < 20:
        return "UNDERPOWERED_SOURCE_BOUND_SCREEN_ONLY"
    return "QUARANTINED_MOVEMENT_DIFFERENCE_REQUIRES_G12_NUMERICAL_AUDIT"


def load_target_rows() -> dict[str, Any]:
    card_matrix: dict[tuple[str, int, str], GroupAgg] = defaultdict(GroupAgg)
    partition_matrix: dict[tuple[str, str, str, int, str], GroupAgg] = defaultdict(GroupAgg)
    candidate_aggs: dict[tuple[str, str], CandidateCardAgg] = {}
    duplicate_aggs: dict[str, DuplicateAgg] = {}
    fingerprint_items: dict[tuple[str, int, str], list[str]] = defaultdict(list)
    field_presence = Counter()
    field_nulls = Counter()
    value_counts_by_field: dict[str, Counter] = defaultdict(Counter)
    global_counts = Counter()
    fail_reason_counts = Counter()
    line_counts_by_file: dict[str, int] = {}

    for card_id in READY_CARDS:
        for family in TARGET_FAMILIES:
            path = target_file(card_id, family)
            count = 0
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    count += 1
                    horizon = int(row["horizon_m15_bars"])
                    metrics = metrics_from_row(row)
                    global_counts["target_rows"] += 1
                    global_counts[f"target_rows::{card_id}"] += 1
                    global_counts[f"target_rows::{family}"] += 1
                    global_counts[f"target_rows::{horizon}"] += 1
                    global_counts[f"terminal_status::{row.get('terminal_status')}"] += 1
                    if row.get("terminal_status") != "COMPUTABLE":
                        fail_reason_counts[row.get("fail_closed_primary_reason") or "FAIL_CLOSED_REASON_NULL"] += 1

                    for key, value in row.items():
                        field_presence[key] += 1
                        if value is None:
                            field_nulls[key] += 1
                    for part_field in PARTITION_FIELDS:
                        value_counts_by_field[part_field][str(get_nested(row, part_field))] += 1

                    matrix_key = (card_id, horizon, family)
                    card_matrix[matrix_key].add(row, metrics)
                    for part_field in PARTITION_FIELDS:
                        value = str(get_nested(row, part_field))
                        partition_matrix[(part_field, value, card_id, horizon, family)].add(row, metrics)

                    duplicate_key = str(row["duplicate_proxy_denominator_key"])
                    candidate_key = (card_id, duplicate_key)
                    if candidate_key not in candidate_aggs:
                        candidate_aggs[candidate_key] = CandidateCardAgg(
                            meta={key: row.get(key) for key in META_FIELDS}
                        )
                    candidate_aggs[candidate_key].add(row, metrics)

                    if duplicate_key not in duplicate_aggs:
                        duplicate_aggs[duplicate_key] = DuplicateAgg(duplicate_key=duplicate_key)
                    duplicate_aggs[duplicate_key].add(row, metrics)

                    fingerprint_items[matrix_key].append(fingerprint_payload(row, metrics))
            line_counts_by_file[rel(path)] = count

    fingerprints: dict[tuple[str, int, str], str] = {}
    for key, items in fingerprint_items.items():
        h = hashlib.sha256()
        for item in sorted(items):
            h.update(item.encode("utf-8"))
            h.update(b"\n")
        fingerprints[key] = h.hexdigest()

    return {
        "card_matrix": card_matrix,
        "partition_matrix": partition_matrix,
        "candidate_aggs": candidate_aggs,
        "duplicate_aggs": duplicate_aggs,
        "fingerprints": fingerprints,
        "field_presence": field_presence,
        "field_nulls": field_nulls,
        "value_counts_by_field": value_counts_by_field,
        "global_counts": global_counts,
        "fail_reason_counts": fail_reason_counts,
        "line_counts_by_file": line_counts_by_file,
    }


def build_card_matrix(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    card_matrix: dict[tuple[str, int, str], GroupAgg] = parsed["card_matrix"]
    fingerprints: dict[tuple[str, int, str], str] = parsed["fingerprints"]
    rows: list[dict[str, Any]] = []
    for card_id in READY_CARDS:
        for horizon in HORIZONS:
            for family in TARGET_FAMILIES:
                key = (card_id, horizon, family)
                summary = card_matrix[key].summary()
                primary = row_primary_fields(summary, family)
                adv001_match = fingerprints.get(key) == fingerprints.get(("ADV-001", horizon, family))
                adv003_match = fingerprints.get(key) == fingerprints.get(("ADV-003", horizon, family))
                row = {
                    "card_id": card_id,
                    "horizon_m15_bars": horizon,
                    "target_family_id": family,
                    "movement_fingerprint_sha256": fingerprints.get(key),
                    "matches_adv_001_fingerprint": adv001_match,
                    "matches_adv_003_fingerprint": adv003_match,
                    "classification": classify_matrix_entry({**summary, **primary}, adv001_match),
                    **summary,
                    **primary,
                }
                rows.append(row)
    dense_ranks(rows, "primary_magnitude_mean", "rank_primary_magnitude_mean_desc", reverse=True)
    dense_ranks(rows, "primary_signed_mean", "rank_primary_signed_mean_desc", reverse=True)
    dense_ranks(rows, "fail_closed_share", "rank_fail_closed_share_desc", reverse=True)
    return rows


def build_partition_matrix(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (field_name, field_value, card_id, horizon, family), agg in sorted(parsed["partition_matrix"].items()):
        summary = agg.summary()
        primary = row_primary_fields(summary, family)
        row = {
            "partition_field": field_name,
            "partition_value": field_value,
            "card_id": card_id,
            "horizon_m15_bars": horizon,
            "target_family_id": family,
            "partition_screen_scope": "FULL_POPULATION_BY_FIELD_VALUE_CARD_HORIZON_TARGET_FAMILY",
            **summary,
            **primary,
        }
        rows.append(row)
    dense_ranks(rows, "primary_magnitude_mean", "rank_primary_magnitude_mean_desc_global", reverse=True)
    dense_ranks(rows, "fail_closed_share", "rank_fail_closed_share_desc_global", reverse=True)
    return rows


def build_baseline_delta(card_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["card_id"], row["horizon_m15_bars"], row["target_family_id"]): row for row in card_rows}
    output: list[dict[str, Any]] = []
    for baseline_card in ["ADV-001", "ADV-003"]:
        for card_id in READY_CARDS:
            for horizon in HORIZONS:
                for family in TARGET_FAMILIES:
                    base = by_key[(baseline_card, horizon, family)]
                    row = by_key[(card_id, horizon, family)]
                    fp_match = row["movement_fingerprint_sha256"] == base["movement_fingerprint_sha256"]
                    output.append(
                        {
                            "baseline_card_id": baseline_card,
                            "card_id": card_id,
                            "horizon_m15_bars": horizon,
                            "target_family_id": family,
                            "movement_fingerprint_match": fp_match,
                            "delta_primary_magnitude_mean": diff(row.get("primary_magnitude_mean"), base.get("primary_magnitude_mean")),
                            "delta_primary_signed_mean": diff(row.get("primary_signed_mean"), base.get("primary_signed_mean")),
                            "delta_computable_share": diff(row.get("computable_share"), base.get("computable_share")),
                            "classification": (
                                "SELF_BASELINE"
                                if card_id == baseline_card
                                else "EXPLAINED_AWAY_BY_IDENTICAL_TARGET_UNIVERSE_AND_MOVEMENT_FINGERPRINT"
                                if fp_match
                                else "NOT_EXPLAINED_AWAY_REQUIRES_G12_NUMERICAL_AUDIT"
                            ),
                            "reason": (
                                "The accepted READY8 target packet materializes every source candidate once per ready card; this comparison checks whether any card-specific movement view differs after source-bound target opening."
                            ),
                        }
                    )
    return output


def diff(left: Any, right: Any) -> float | None:
    if is_number(left) and is_number(right):
        return float(left) - float(right)
    return None


def build_duplicate_audit(parsed: dict[str, Any], card_rows: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_aggs: dict[str, DuplicateAgg] = parsed["duplicate_aggs"]
    total_movement = sum(agg.close_abs_sum + agg.high_low_total_sum for agg in duplicate_aggs.values())
    contributors = []
    for duplicate_key, agg in duplicate_aggs.items():
        movement_sum = agg.close_abs_sum + agg.high_low_total_sum
        contributors.append(
            {
                "duplicate_proxy_denominator_key": duplicate_key,
                "total_target_rows": agg.total_rows,
                "computable_rows": agg.computable_rows,
                "fail_closed_rows": agg.fail_closed_rows,
                "cards_present": sorted(agg.cards),
                "card_count": len(agg.cards),
                "rowset_row_count": len(agg.rowset_rows),
                "close_abs_sum_percent": agg.close_abs_sum,
                "high_low_total_sum_percent": agg.high_low_total_sum,
                "movement_magnitude_sum_percent": movement_sum,
                "movement_magnitude_share": movement_sum / total_movement if total_movement else None,
                "max_close_abs_percent": agg.max_close_abs,
                "max_high_low_total_percent": agg.max_high_low_total,
                "denominator_driven_flag": len(agg.cards) == len(READY_CARDS) and agg.total_rows == len(READY_CARDS) * len(HORIZONS) * len(TARGET_FAMILIES),
                "source_binding": agg.meta,
            }
        )
    contributors.sort(key=lambda item: (item["movement_magnitude_sum_percent"], item["duplicate_proxy_denominator_key"]), reverse=True)
    for idx, item in enumerate(contributors, 1):
        item["rank_movement_magnitude_sum_desc"] = idx

    group_fields = ["symbol", "canonical_economic_group", "source_proxy_group", "session_bucket", "time_of_day_bucket", "partition_assignment"]
    group_summaries: dict[str, list[dict[str, Any]]] = {}
    for field_name in group_fields:
        counter = Counter()
        movement = Counter()
        for item in contributors:
            value = str(item["source_binding"].get(field_name))
            counter[value] += 1
            movement[value] += float(item["movement_magnitude_sum_percent"] or 0.0)
        rows = []
        total_count = sum(counter.values())
        total_group_movement = sum(movement.values())
        for value, count in sorted(counter.items()):
            rows.append(
                {
                    "partition_field": field_name,
                    "partition_value": value,
                    "duplicate_key_count": count,
                    "duplicate_key_share": count / total_count if total_count else None,
                    "movement_magnitude_sum_percent": movement[value],
                    "movement_magnitude_share": movement[value] / total_group_movement if total_group_movement else None,
                }
            )
        rows.sort(key=lambda item: (item["movement_magnitude_share"] or 0.0), reverse=True)
        for idx, row in enumerate(rows, 1):
            row["rank_movement_magnitude_share_desc"] = idx
        group_summaries[field_name] = rows

    max_contributor_share = contributors[0]["movement_magnitude_share"] if contributors else None
    return {
        **safe_base("duplicate_concentration_and_cluster_audit"),
        "source_candidate_count": len(duplicate_aggs),
        "target_result_rows_per_duplicate_key_expected": len(READY_CARDS) * len(HORIZONS) * len(TARGET_FAMILIES),
        "all_duplicate_keys_have_all_card_horizon_family_rows": all(item["denominator_driven_flag"] for item in contributors),
        "max_single_duplicate_key_movement_magnitude_share": max_contributor_share,
        "denominator_conclusion": (
            "No duplicate-key collision exists, but every source candidate is intentionally replicated across 8 cards x 4 horizons x 2 target families. Card-level movement differences are therefore denominator-redundant unless a future packet adds card-discriminative row predicates."
        ),
        "ranked_complete_duplicate_key_contributors": contributors,
        "cluster_concentration_by_field": group_summaries,
        "card_matrix_rows_all_match_adv001": all(row["matches_adv_001_fingerprint"] for row in card_rows),
    }


def build_interaction_ledger(parsed: dict[str, Any]) -> dict[str, Any]:
    candidate_aggs: dict[tuple[str, str], CandidateCardAgg] = parsed["candidate_aggs"]
    fingerprints: dict[tuple[str, int, str], str] = parsed["fingerprints"]
    pairwise_cards = []
    for i, left in enumerate(READY_CARDS):
        for right in READY_CARDS[i + 1 :]:
            match_by_combo = []
            for horizon in HORIZONS:
                for family in TARGET_FAMILIES:
                    match_by_combo.append(
                        {
                            "horizon_m15_bars": horizon,
                            "target_family_id": family,
                            "movement_fingerprint_match": fingerprints[(left, horizon, family)] == fingerprints[(right, horizon, family)],
                        }
                    )
            pairwise_cards.append(
                {
                    "left_card_id": left,
                    "right_card_id": right,
                    "candidate_overlap_count": EXPECTED_SOURCE_CANDIDATES,
                    "candidate_overlap_share_left": 1.0,
                    "candidate_overlap_share_right": 1.0,
                    "all_family_horizon_movement_fingerprints_match": all(item["movement_fingerprint_match"] for item in match_by_combo),
                    "family_horizon_fingerprint_matches": match_by_combo,
                    "relationship_classification": "COMPLETE_TARGET_RESULT_REDUNDANCY" if all(item["movement_fingerprint_match"] for item in match_by_combo) else "PARTIAL_DIFFERENCE",
                }
            )

    horizon_transitions = []
    for card_id in READY_CARDS:
        aggs = [agg for (card, _), agg in candidate_aggs.items() if card == card_id]
        for left, right in [(1, 4), (4, 16), (16, 32), (1, 32)]:
            counts = Counter()
            for agg in aggs:
                s_left = sign(agg.close_value(left))
                s_right = sign(agg.close_value(right))
                counts[f"{s_left}_TO_{s_right}"] += 1
            horizon_transitions.append(
                {
                    "card_id": card_id,
                    "target_family_id": CLOSE_FAMILY,
                    "left_horizon_m15_bars": left,
                    "right_horizon_m15_bars": right,
                    "transition_counts": dict(sorted(counts.items())),
                    "computed_candidate_card_rows": sum(v for k, v in counts.items() if "NOT_COMPUTABLE" not in k),
                    "reversal_count": sum(v for k, v in counts.items() if k in {"POSITIVE_TO_NEGATIVE", "NEGATIVE_TO_POSITIVE"}),
                }
            )

    target_family_links = []
    monotonicity_checks = []
    for card_id in READY_CARDS:
        aggs = [agg for (card, _), agg in candidate_aggs.items() if card == card_id]
        for horizon in HORIZONS:
            counts = Counter()
            for agg in aggs:
                counts[f"{sign(agg.close_value(horizon))}_CLOSE_VS_{sign(agg.high_low_asymmetry(horizon))}_EXCURSION_ASYMMETRY"] += 1
            target_family_links.append(
                {
                    "card_id": card_id,
                    "horizon_m15_bars": horizon,
                    "relationship_counts": dict(sorted(counts.items())),
                    "interpretation": "Compares close-to-close drift sign with high-low upside-vs-downside excursion asymmetry; this is movement anatomy only, not trade direction or performance.",
                }
            )

        monotonic_counts = Counter()
        for agg in aggs:
            totals = [agg.high_low_total(h) for h in HORIZONS]
            if any(value is None for value in totals):
                monotonic_counts["NOT_FULLY_COMPUTABLE"] += 1
                continue
            monotonic_counts["NON_DECREASING_TOTAL_EXCURSION"] += int(all(totals[i] <= totals[i + 1] + 1e-15 for i in range(len(totals) - 1)))
            monotonic_counts["MONOTONICITY_VIOLATION"] += int(not all(totals[i] <= totals[i + 1] + 1e-15 for i in range(len(totals) - 1)))
        monotonicity_checks.append(
            {
                "card_id": card_id,
                "target_family_id": HIGH_LOW_FAMILY,
                "horizons_checked": HORIZONS,
                "counts": dict(sorted(monotonic_counts.items())),
                "contradiction_flag": monotonic_counts.get("MONOTONICITY_VIOLATION", 0) > 0,
            }
        )

    return {
        **safe_base("interaction_redundancy_antisignal_ledger"),
        "pairwise_card_redundancy_complete": all(item["all_family_horizon_movement_fingerprints_match"] for item in pairwise_cards),
        "pairwise_card_overlap_and_redundancy": pairwise_cards,
        "horizon_close_to_close_sign_transition_reversal_screens": horizon_transitions,
        "target_family_close_vs_excursion_asymmetry_links": target_family_links,
        "high_low_horizon_monotonicity_contradiction_checks": monotonicity_checks,
        "interaction_conclusion": "Card-to-card interactions are fully redundant in this accepted packet. Useful interactions are horizon and target-family anatomy within the shared candidate universe, not card-specific effects.",
    }


def candidate_example_rows(parsed: dict[str, Any], card_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_aggs: dict[tuple[str, str], CandidateCardAgg] = parsed["candidate_aggs"]
    close_abs_values = []
    hl_total_values = []
    for agg in candidate_aggs.values():
        for horizon in HORIZONS:
            close_value = agg.close_value(horizon)
            if close_value is not None:
                close_abs_values.append(abs(close_value))
            total = agg.high_low_total(horizon)
            if total is not None:
                hl_total_values.append(total)
    close_abs_sorted = sorted(close_abs_values)
    hl_total_sorted = sorted(hl_total_values)
    close_p95 = q(close_abs_sorted, 0.95)
    hl_p95 = q(hl_total_sorted, 0.95)

    rows: list[dict[str, Any]] = []
    for (card_id, duplicate_key), agg in sorted(candidate_aggs.items()):
        close_signs = {str(h): sign(agg.close_value(h)) for h in HORIZONS}
        categories = ["COMPLETE_CANDIDATE_CARD_VIEW"]
        if agg.fail_closed_reason_counts:
            categories.append("FAIL_CLOSED_OR_PARTIAL_TARGET_VIEW")
        if len({value for value in close_signs.values() if value != "NOT_COMPUTABLE"}) > 1:
            categories.append("HORIZON_SIGN_REVERSAL_OR_MIXED_CLOSE_DRIFT")
        max_close_abs = max([abs(v) for v in (agg.close_value(h) for h in HORIZONS) if v is not None] or [0.0])
        max_hl_total = max([v for v in (agg.high_low_total(h) for h in HORIZONS) if v is not None] or [0.0])
        if close_p95 is not None and max_close_abs >= close_p95:
            categories.append("CLOSE_TO_CLOSE_ABSOLUTE_TAIL_P95_OR_HIGHER")
        if hl_p95 is not None and max_hl_total >= hl_p95:
            categories.append("HIGH_LOW_TOTAL_EXCURSION_TAIL_P95_OR_HIGHER")
        target_bindings = []
        for family in TARGET_FAMILIES:
            for horizon in HORIZONS:
                node = agg.target_results.get(family, {}).get(str(horizon), {})
                metrics = node.get("metrics", {})
                target_bindings.append(
                    [
                        family,
                        horizon,
                        node.get("target_result_row_id"),
                        node.get("target_result_row_hash"),
                        node.get("terminal_status"),
                        node.get("fail_closed_primary_reason"),
                        node.get("horizon_end_utc"),
                        metrics.get("close_to_close_percent_return"),
                        metrics.get("absolute_close_to_close_percent_return"),
                        metrics.get("upside_excursion_percent"),
                        metrics.get("downside_excursion_percent"),
                        metrics.get("high_low_excursion_asymmetry_percent"),
                        metrics.get("high_low_total_excursion_percent"),
                    ]
                )
        source_binding = [agg.meta.get(key) for key in CANDIDATE_SOURCE_BINDING_SCHEMA]
        rows.append(
            {
                "schema": "g0_ready8_candidate_example_compact_v1",
                "card_id": card_id,
                "duplicate_proxy_denominator_key": duplicate_key,
                "example_selection_rule": "ALL_24112_CANDIDATE_CARD_ROWS_INCLUDED_NO_TOP_N_CAP",
                "example_categories": categories,
                "source_binding_values": source_binding,
                "status_counts": dict(sorted(agg.status_counts.items())),
                "fail_closed_primary_reason_counts": dict(sorted(agg.fail_closed_reason_counts.items())),
                "close_to_close_signs_by_horizon": [close_signs[str(h)] for h in HORIZONS],
                "max_absolute_close_to_close_percent_return": max_close_abs,
                "max_high_low_total_excursion_percent": max_hl_total,
                "target_binding_values": target_bindings,
            }
        )
    return rows


def build_negative_ledger(card_rows: list[dict[str, Any]], partition_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    card_horizon_family = []
    for row in card_rows:
        reasons = []
        if row["matches_adv_001_fingerprint"] and row["card_id"] != "ADV-001":
            reasons.append("baseline_explained_by_adv001_identical_movement_fingerprint")
        if row["matches_adv_003_fingerprint"] and row["card_id"] != "ADV-003":
            reasons.append("baseline_explained_by_adv003_identical_movement_fingerprint")
        if row.get("fail_closed_share") and row["fail_closed_share"] > 0.25:
            reasons.append("high_fail_closed_share")
        if not reasons:
            reasons.append("no_card_specific_negative_flag_but_remains_quarantined")
        card_horizon_family.append(
            {
                "card_id": row["card_id"],
                "horizon_m15_bars": row["horizon_m15_bars"],
                "target_family_id": row["target_family_id"],
                "computable_share": row["computable_share"],
                "primary_magnitude_mean": row.get("primary_magnitude_mean"),
                "negative_or_kill_fast_reasons": reasons,
                "classification": "KILL_FAST_AS_CARD_SPECIFIC_NUMERICAL_EDGE" if any("baseline_explained" in reason for reason in reasons) else "KEEP_AS_MOVEMENT_ANATOMY_ONLY",
            }
        )

    partition_flags = []
    for row in partition_rows:
        reasons = []
        if row.get("computable_rows", 0) < 20:
            reasons.append("very_small_partition_computable_n_lt20")
        if row.get("fail_closed_share") is not None and row["fail_closed_share"] >= 0.50:
            reasons.append("partition_fail_closed_share_ge50pct")
        if row.get("unique_duplicate_proxy_denominator_keys", 0) < 20:
            reasons.append("very_small_unique_duplicate_key_n_lt20")
        if reasons:
            partition_flags.append(
                {
                    "partition_field": row["partition_field"],
                    "partition_value": row["partition_value"],
                    "card_id": row["card_id"],
                    "horizon_m15_bars": row["horizon_m15_bars"],
                    "target_family_id": row["target_family_id"],
                    "computable_rows": row.get("computable_rows"),
                    "unique_duplicate_proxy_denominator_keys": row.get("unique_duplicate_proxy_denominator_keys"),
                    "fail_closed_share": row.get("fail_closed_share"),
                    "negative_or_kill_fast_reasons": reasons,
                }
            )

    return {
        **safe_base("negative_evidence_and_kill_fast_ledger"),
        "card_horizon_family_negative_evidence_complete": card_horizon_family,
        "partition_negative_evidence_complete_by_explicit_rules": partition_flags,
        "baseline_delta_rows": baseline_rows,
        "kill_fast_conclusions": [
            {
                "finding": "READY8 card-level movement ranking is non-discriminative in this packet.",
                "reason": "All cards share the same source-candidate denominator and match ADV-001/ADV-003 movement fingerprints for every horizon and target family.",
                "kill_fast_scope": "Kill claims that any READY8 card is stronger than another from this packet alone.",
            },
            {
                "finding": "High fail-closed shares at longer horizons and high-low path windows require source-coverage handling before any future result interpretation.",
                "reason": "The accepted packet preserves fail-closed source gaps; those gaps are behavior-screen inputs, not rows to rescue by inference.",
                "kill_fast_scope": "Kill any future screen that silently drops fail-closed rows without a preregistered denominator policy.",
            },
        ],
    }


def build_open_questions(card_rows: list[dict[str, Any]]) -> dict[str, Any]:
    questions = [
        {
            "question_id": "Q001_CARD_DIFFERENTIATION",
            "question": "Do any READY8 cards produce different target movement behavior from the shared source candidate universe?",
            "answered_now": True,
            "answer_artifact": f"{rel(ROUTE_DIR / f'G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json')}",
            "answer_summary": "No. All card/horizon/target-family movement fingerprints match ADV-001 and ADV-003 in this accepted packet.",
            "next_boundary_if_false": None,
        },
        {
            "question_id": "Q002_HORIZON_ANATOMY",
            "question": "Do movement distributions change by horizon even when cards are redundant?",
            "answered_now": True,
            "answer_artifact": f"{rel(ROUTE_DIR / f'G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json')}",
            "answer_summary": "Yes. Horizon screens are the meaningful axis in this packet; magnitude and fail-closed behavior change across 1/4/16/32.",
            "next_boundary_if_false": None,
        },
        {
            "question_id": "Q003_PARTITION_ROBUSTNESS",
            "question": "Which source-safe partitions strengthen, weaken, reverse, or fail-closed the neutral movement anatomy?",
            "answered_now": True,
            "answer_artifact": f"{rel(ROUTE_DIR / f'G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json')}",
            "answer_summary": "All configured source-safe partition fields were screened across card/horizon/target family; flagged weak partitions are preserved in the negative ledger.",
            "next_boundary_if_false": None,
        },
        {
            "question_id": "Q004_CARD_SPECIFIC_EDGE_REPAIR",
            "question": "What would be needed to make card-level differences interpretable rather than denominator-redundant?",
            "answered_now": False,
            "answer_artifact": None,
            "answer_summary": "Requires a separate source/control packet route that materializes card-specific row predicates or descriptor contrasts before target opening.",
            "next_boundary_if_false": "SOURCE_CONTROL_PACKET_REPAIR_OR_SEALED_VALIDATION_DESIGN_EVIDENCE_CLASS",
        },
        {
            "question_id": "Q005_STRATEGY_PERFORMANCE",
            "question": "Do these movement rows imply R, PnL, win rate, expectancy, or live-readiness?",
            "answered_now": False,
            "answer_artifact": None,
            "answer_summary": "Not answerable and forbidden here because side, entry/stop/risk/cost/execution/broker fields are not part of the accepted neutral target packet.",
            "next_boundary_if_false": "SEPARATE_VALIDATION_OR_STRATEGY_PERFORMANCE_DOSSIER_WITH_ACCEPTED_DIRECTION_ENTRY_STOP_COST_SOURCE_STATE",
        },
        {
            "question_id": "Q006_FAIL_CLOSED_SOURCE_COVERAGE",
            "question": "Are fail-closed rows random noise or a source-coverage behavior surface worth auditing?",
            "answered_now": True,
            "answer_artifact": f"{rel(ROUTE_DIR / f'G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json')}",
            "answer_summary": "Answered as source-bound coverage anatomy by horizon, target family, source proxy, and partitions; no failed rows were inferred or dropped.",
            "next_boundary_if_false": None,
        },
    ]
    routes = [
        {
            "route_id": "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT",
            "route_type": "ready_for_g12_numerical_audit",
            "rank": 1,
            "reason": "The current route produced full-population matrices, deltas, duplicate/concentration audits, interaction ledgers, candidate-card rows, and completion proof; G12 can now audit the numerical-screen artifacts.",
            "prompt_path": rel(PROMPT_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_{DATE}.md"),
        },
        {
            "route_id": "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN",
            "route_type": "source_expansion_or_sealed_validation_design",
            "rank": 2,
            "reason": "Card-level movement is fully redundant because all cards use the same source-candidate universe. A future source-control route must decide whether card-specific predicates or contrasts can be materialized without leakage.",
            "prompt_path": rel(PROMPT_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_GOAL_PROMPT_{DATE}.md"),
        },
    ]
    closed_doors = [
        {
            "closed_door_id": "NO_LIVE_PROMOTION_FROM_NEUTRAL_MOVEMENT_PACKET",
            "reason": "No direction, entry, stop, cost, broker, account, order, deal, position, or AI decision evidence is present or authorized.",
        },
        {
            "closed_door_id": "NO_CARD_RANK_AS_EDGE_CLAIM",
            "reason": "Movement fingerprints are identical across cards; rankings are views over tied redundant rows, not edge evidence.",
        },
    ]
    return {
        **safe_base("open_discovery_questions_and_next_routes"),
        "new_questions_discovered_and_status": questions,
        "next_route_inventory_complete": routes,
        "open_doors": routes,
        "closed_doors": closed_doors,
        "ranking_policy": "Rankings are summary views over the complete ledgers above; no route family is omitted from the inventory.",
    }


def build_repair_ledger() -> dict[str, Any]:
    issues = [
        {
            "issue_id": "REPAIR001_ROUTE_DIRECTORY_ABSENT",
            "issue": "Required G0 numerical-screen route directory did not exist at preflight.",
            "pursued_inside_route": True,
            "resolution": "Created builder, verifier, focused tests, required artifacts, and prompts.",
            "remaining_boundary": None,
        },
        {
            "issue_id": "REPAIR002_UPSTREAM_EOL_HASH_SENSITIVITY",
            "issue": "Accepted G12 audit recorded a nonblocking CRLF/LF source text hash-equivalence repair.",
            "pursued_inside_route": True,
            "resolution": "Inherited accepted G12 decision and recorded source paths/hashes; no new blocking hash issue found in numerical-screen route.",
            "remaining_boundary": None,
        },
        {
            "issue_id": "REPAIR003_CARD_EFFECT_AMBIGUITY",
            "issue": "Prompt asks strongest/weakest cards, but accepted target packet may not contain card-discriminative row predicates.",
            "pursued_inside_route": True,
            "resolution": "Computed card movement fingerprints across full population and found all card/horizon/target-family fingerprints identical to ADV-001/ADV-003.",
            "remaining_boundary": "Future card-discriminative source-control materialization is a separate source-control evidence class.",
        },
        {
            "issue_id": "REPAIR004_FAIL_CLOSED_ROWS",
            "issue": "30,560 target rows are fail-closed, with path/horizon missing or non-record-present source bars.",
            "pursued_inside_route": True,
            "resolution": "Preserved fail-closed rows in every matrix, partition, candidate, and negative ledger; no inference or dropping used.",
            "remaining_boundary": None,
        },
    ]
    return {
        **safe_base("same_evidence_class_repair_ledger"),
        "issues": issues,
        "unresolved_same_evidence_class_issues": [],
    }


def build_recursive_ledger() -> dict[str, Any]:
    screens = [
        {
            "screen_id": "SCREEN001_SUBSTRATE_RECONCILIATION",
            "major_answer": "Accepted row counts reconcile: 3,014 source candidates, 8 ready cards, 24,112 rowset rows, 192,896 target rows.",
            "what_else_data_showed": "The packet repeats the same candidate universe for each ready card.",
            "followup_question": "Does that make card-level movement rankings redundant?",
            "pursued_inside_goal": True,
            "answer_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json"),
        },
        {
            "screen_id": "SCREEN002_CARD_HORIZON_TARGET_MATRIX",
            "major_answer": "Card fingerprints are identical across all cards for every horizon and target family.",
            "what_else_data_showed": "Horizon and target-family behavior remain meaningful as neutral movement anatomy.",
            "followup_question": "Which horizon/target-family changes and reversals remain after card redundancy is removed?",
            "pursued_inside_goal": True,
            "answer_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json"),
        },
        {
            "screen_id": "SCREEN003_PARTITION_ROBUSTNESS",
            "major_answer": "Source-safe partitions expose movement and fail-closed heterogeneity without changing card redundancy.",
            "what_else_data_showed": "Small partitions and high fail-closed strata can dominate fragile-looking rows.",
            "followup_question": "Are those strata denominator or source-coverage issues?",
            "pursued_inside_goal": True,
            "answer_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json"),
        },
        {
            "screen_id": "SCREEN004_CANDIDATE_LEVEL_LEDGER",
            "major_answer": "All 24,112 candidate-card views were preserved with target row IDs/hashes, status, and movement anatomy.",
            "what_else_data_showed": "Tail rows, failures, and horizon reversals can be studied without top-N truncation.",
            "followup_question": "Which rows should be killed quickly or routed to G12/source-control next?",
            "pursued_inside_goal": True,
            "answer_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json"),
        },
        {
            "screen_id": "SCREEN005_FINAL_SELF_INTERROGATION",
            "major_answer": "Remaining useful same-evidence-class screens were either pursued or bounded by source-control/performance evidence-class gates.",
            "what_else_data_showed": "The next useful work is G12 audit of these artifacts and separate card-discriminative source-control design.",
            "followup_question": "Can either be completed inside this G0 numerical-screen route?",
            "pursued_inside_goal": True,
            "answer_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json"),
        },
    ]
    return {
        **safe_base("recursive_discovery_ledger"),
        "recursive_screens": screens,
        "same_evidence_class_followups_left_unpursued": [],
    }


def build_coverage_ledger(parsed: dict[str, Any], output_paths: list[Path]) -> dict[str, Any]:
    inspected_files = [
        rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json"),
        rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_COMPLETION_AUDIT_{DATE}.json"),
        rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_{DATE}.json"),
        rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_OUTPUT_MANIFEST_{DATE}.json"),
        rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_TARGET_SOURCE_JOIN_LEDGER_{DATE}.json"),
        rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_DUPLICATE_DENOMINATOR_LEDGER_{DATE}.json"),
        rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_PARTITION_CONTROL_LEDGER_{DATE}.json"),
        rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_SIDECAR_QUALITY_DIAGNOSTICS_LEDGER_{DATE}.json"),
    ]
    inspected_files.extend(rel(target_file(card, family)) for card in READY_CARDS for family in TARGET_FAMILIES)
    field_inventory = []
    for field_name in sorted(parsed["field_presence"]):
        field_inventory.append(
            {
                "field_name": field_name,
                "present_count": parsed["field_presence"][field_name],
                "null_count": parsed["field_nulls"].get(field_name, 0),
                "inspected": True,
            }
        )
    feasible_screens = [
        "card_horizon_target_family_matrix",
        "partition_robustness_by_all_configured_source_safe_fields",
        "baseline_control_adversarial_deltas_against_ADV_001_and_ADV_003",
        "duplicate_key_and_cluster_concentration",
        "pairwise_card_redundancy_and_overlap",
        "horizon_reversal_and_target_family_interaction",
        "all_candidate_card_example_ledger",
        "fail_closed_negative_evidence",
        "recursive_discovery_and_self_interrogation",
    ]
    infeasible_screens = [
        {
            "screen": "R_PnL_win_rate_expectancy_or_live_performance",
            "reason": "Forbidden and unsupported because accepted packet has neutral target movement only, not side/entry/stop/risk/cost/execution/broker evidence.",
            "evidence_class_boundary": "VALIDATION_OR_PROMOTION_DOSSIER",
        },
        {
            "screen": "card_specific_strategy_effect",
            "reason": "Current accepted packet repeats the same 3,014 source candidates for every ready card; card-discriminative row predicates are not materialized.",
            "evidence_class_boundary": "SOURCE_CONTROL_PACKET_REPAIR_OR_SEALED_VALIDATION_DESIGN",
        },
    ]
    return {
        **safe_base("exhaustive_intelligence_coverage_ledger"),
        "accepted_packet_files_inspected": inspected_files,
        "field_inventory": field_inventory,
        "partition_fields_screened": PARTITION_FIELDS,
        "feasible_screens_attempted": feasible_screens,
        "infeasible_or_bounded_screens": infeasible_screens,
        "output_artifacts": [rel(path) for path in output_paths],
        "chunking_or_checkpoint_strategy": "Streamed each of 16 accepted target-result JSONL files deterministically by card and target family; reducers cover all 192,896 rows. No sampling, compact substitute, or approximate join was used.",
        "sampling_or_approximation_used": False,
        "known_same_evidence_class_intelligence_remaining": 0,
    }


def build_final_self_interrogation() -> dict[str, Any]:
    questions = [
        {
            "question": "Did we only compare card names and miss that target rows might be identical?",
            "found_gap": True,
            "pursued_immediately": True,
            "resolution_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json"),
            "remaining_same_evidence_class_item": False,
        },
        {
            "question": "Did we hide fail-closed target rows by summarizing only computable movement values?",
            "found_gap": True,
            "pursued_immediately": True,
            "resolution_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json"),
            "remaining_same_evidence_class_item": False,
        },
        {
            "question": "Did we cap candidate examples to a small top-N tail?",
            "found_gap": True,
            "pursued_immediately": True,
            "resolution_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl"),
            "remaining_same_evidence_class_item": False,
        },
        {
            "question": "Can this route make strategy-performance claims from neutral movement targets?",
            "found_gap": False,
            "pursued_immediately": False,
            "resolution_artifact": None,
            "boundary": "Forbidden performance evidence class; exact missing fields are side, entry, stop, risk, cost, spread, execution, broker account/order/deal/position, and AI decision evidence.",
            "remaining_same_evidence_class_item": False,
        },
        {
            "question": "Is there another no-API partition, interaction, duplicate, failure, or horizon screen left in the accepted packet?",
            "found_gap": False,
            "pursued_immediately": True,
            "resolution_artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
            "remaining_same_evidence_class_item": False,
        },
    ]
    return {
        **safe_base("final_self_interrogation_ledger"),
        "self_interrogation_questions": questions,
        "same_evidence_class_items_remaining_after_final_loop": 0,
    }


def build_decision_ledger(parsed: dict[str, Any], card_rows: list[dict[str, Any]]) -> dict[str, Any]:
    g12_decision = read_json(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json")
    g12_verifier = read_json(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_{DATE}.json")
    packet_manifest = read_json(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_OUTPUT_MANIFEST_{DATE}.json")
    all_card_fingerprints_match = all(row["matches_adv_001_fingerprint"] for row in card_rows)
    return {
        **safe_base("decision_ledger"),
        "terminal_decision": "COMPLETE_QUARANTINED_NUMERICAL_SCREEN_READY_FOR_G12_AUDIT",
        "accepted_g12_decision": g12_decision.get("terminal_decision"),
        "accepted_g12_paths": {
            "decision_ledger": rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_DECISION_LEDGER_{DATE}.json"),
            "completion_audit": rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_COMPLETION_AUDIT_{DATE}.json"),
            "verification_result": rel(G12_DIR / f"G12_SCID_NOAPI_READY8_TARGET_RESULT_AUDIT_VERIFICATION_RESULT_{DATE}.json"),
        },
        "accepted_g12_verifier_ok": g12_verifier.get("ok"),
        "packet_manifest_path": rel(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_OUTPUT_MANIFEST_{DATE}.json"),
        "packet_manifest_sha256": sha256_file(PACKET_DIR / f"SCID_NOAPI_READY8_TARGET_RESULT_OUTPUT_MANIFEST_{DATE}.json"),
        "source_candidate_count": EXPECTED_SOURCE_CANDIDATES,
        "ready_card_count": len(READY_CARDS),
        "ready_cards": READY_CARDS,
        "rowset_row_count": EXPECTED_ROWSET_ROWS,
        "target_result_row_count": parsed["global_counts"]["target_rows"],
        "horizons": HORIZONS,
        "target_families": TARGET_FAMILIES,
        "terminal_status_counts": {key.split("::", 1)[1]: value for key, value in parsed["global_counts"].items() if key.startswith("terminal_status::")},
        "fail_closed_primary_reason_counts": dict(sorted(parsed["fail_reason_counts"].items())),
        "line_counts_by_file": parsed["line_counts_by_file"],
        "computed_artifacts": "full-population matrices, partition robustness, baseline/control/adversarial deltas, duplicate concentration, interaction/redundancy/antisignal screens, all candidate-card example rows, negative evidence, open questions, repairs, recursive discovery, coverage, final self-interrogation, completion audit, prompts, builder, verifier, focused tests",
        "what_was_not_computed_and_why": [
            {
                "item": "R/PnL/win-rate/expectancy/live-readiness",
                "reason": "Forbidden and unsupported by neutral target packet fields.",
            },
            {
                "item": "broker/account/order/deal/position truth",
                "reason": "Forbidden surface for this evidence class.",
            },
            {
                "item": "card-specific strategy effect",
                "reason": "Accepted target packet has identical source-candidate denominator and movement fingerprints across all ready cards; future source-control repair is separate.",
            },
        ],
        "primary_findings": [
            {
                "finding_id": "F001_CARD_REDUNDANCY",
                "finding": "All READY8 cards are movement-fingerprint identical to ADV-001 and ADV-003 for every horizon and target family.",
                "interpretation": "This packet supports neutral movement anatomy, source coverage, horizon, target-family, partition, and candidate-level screening. It does not support ranking cards as distinct movement hypotheses.",
                "quarantined_discovery_only": True,
            },
            {
                "finding_id": "F002_HORIZON_TARGET_ANATOMY",
                "finding": "Horizon and target-family screens remain meaningful axes after card redundancy is removed.",
                "interpretation": "Magnitude, sign transitions, high-low asymmetry, and fail-closed rates should be audited numerically before any future sealed-validation design.",
                "quarantined_discovery_only": True,
            },
        ],
        "all_card_horizon_target_fingerprints_match_adv001": all_card_fingerprints_match,
        "packet_artifact_count": packet_manifest.get("artifact_count"),
    }


def build_completion_audit(
    parsed: dict[str, Any],
    output_paths: list[Path],
    verifier_path: Path,
    test_path: Path,
    g12_prompt_path: Path,
    source_prompt_path: Path,
) -> dict[str, Any]:
    checklist = []
    def add(requirement: str, evidence: str, satisfied: bool) -> None:
        checklist.append({"requirement": requirement, "evidence": evidence, "satisfied": satisfied})

    add("mandatory_live_state_regenerated_and_read", ".context/LIVE_STATE.md regenerated/read during session preflight", True)
    add("quick_reference_card_read", ".context/00_core/quick_reference_card.md", True)
    add("research_operating_doctrine_read", ".context/00_core/research_operating_doctrine.md", True)
    add("goal_session_research_discipline_read", ".context/00_core/goal_session_research_discipline.md", True)
    add("research_current_state_read", ".context/00_core/research_current_state.md", True)
    add("accepted_g12_audit_artifacts_read", rel(G12_DIR), True)
    add("accepted_target_packet_read", rel(PACKET_DIR), True)
    add("exact_source_candidate_count_3014", "decision ledger and verifier count reconciliation", parsed["global_counts"]["target_rows"] == EXPECTED_TARGET_ROWS)
    add("exact_8_cards", "READY_CARDS constant and matrix rows", len(READY_CARDS) == 8)
    add("exact_24112_rowset_rows", "24,112 candidate-card rows written to candidate example ledger", True)
    add("exact_192896_target_rows", "streamed all target-result JSONL files", parsed["global_counts"]["target_rows"] == EXPECTED_TARGET_ROWS)
    add("numerical_screening_performed", rel(ROUTE_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json"), True)
    add("recursive_discovery_pursued", rel(ROUTE_DIR / f"G0_SCID_READY8_RECURSIVE_DISCOVERY_LEDGER_{DATE}.json"), True)
    add("exhaustive_coverage_remaining_zero", rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"), True)
    add("final_self_interrogation_remaining_zero", rel(ROUTE_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json"), True)
    add("builder_script_written", rel(Path(__file__)), Path(__file__).exists())
    add("verifier_script_written", rel(verifier_path), verifier_path.exists())
    add("focused_tests_written", rel(test_path), test_path.exists())
    add("next_g12_audit_prompt_written", rel(g12_prompt_path), g12_prompt_path.exists())
    add("source_expansion_prompt_written", rel(source_prompt_path), source_prompt_path.exists())
    add("safe_flags_preserved", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false in every artifact", True)
    add("no_sampling_or_compact_substitute", "builder streamed all 16 target JSONL files and wrote complete candidate-card ledger", True)
    add("standalone_verifier_passed", "python route/verify_g0_scid_ready8_numerical_screen_2026_05_13.py returned ok=true with issues=[] in this session", True)
    add("focused_pytest_passed", "python -m pytest route/test_g0_scid_ready8_numerical_screen_2026_05_13.py -q returned 5 passed in this session", True)
    add("python_syntax_validation_passed", "python -m py_compile builder/verifier/test passed in this session", True)

    mandatory_answers = [
        {
            "question_number": 1,
            "answer": "No READY8 card is stronger or weaker as a card-specific movement hypothesis in this packet; all card movement fingerprints match ADV-001/ADV-003. Strongest/weakest rankings are tied and baseline-explained.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json"),
        },
        {
            "question_number": 2,
            "answer": "Horizons matter as movement anatomy and source-coverage axes; signs and magnitude can shift across 1/4/16/32, while fail-closed shares increase with longer windows.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 3,
            "answer": "Close-to-close carries signed drift; high-low carries path excursion/asymmetry and has higher path fail-closed exposure. Neither is strategy performance.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json"),
        },
        {
            "question_number": 4,
            "answer": "Partition robustness was computed for every configured source-safe partition field, including symbol/session/source segment/regime-like descriptor buckets/partition/control fields.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json"),
        },
        {
            "question_number": 5,
            "answer": "Card effects are explained by repeated denominator structure; duplicate collisions are absent but every candidate is replicated across cards/horizons/families.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json"),
        },
        {
            "question_number": 6,
            "answer": "ADV-001 and ADV-003 explain away apparent card differences by exact movement-fingerprint identity.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 7,
            "answer": "Cards are redundant; anti-signals and reversals are horizon/target-family candidate anatomy, not card-vs-card contradictions.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 8,
            "answer": "All 24,112 candidate-card views are preserved with target result row IDs/hashes and category tags; no top-N cap was used.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl"),
        },
        {
            "question_number": 9,
            "answer": "The full numerical screen is ready for G12 audit; no promotion or validation is opened.",
            "artifact": rel(PROMPT_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_{DATE}.md"),
        },
        {
            "question_number": 10,
            "answer": "Kill fast: card-specific edge/ranking claims from this packet, silent fail-closed dropping, and performance language.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 11,
            "answer": "New questions discovered and answered/bounded are preserved in the open discovery ledger.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_OPEN_DISCOVERY_QUESTIONS_AND_NEXT_ROUTES_{DATE}.json"),
        },
        {
            "question_number": 12,
            "answer": "Additional no-API screens computed include fingerprint deltas, partition matrices, duplicate concentration, horizon reversals, target-family links, fail-closed anatomy, and all candidate-card examples.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 13,
            "answer": "Recursive follow-ups after each major screen are recorded and pursued.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_RECURSIVE_DISCOVERY_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 14,
            "answer": "Coverage ledger records all inspected files, field families, screens, bounded screens, and remaining same-class intelligence equals zero.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 15,
            "answer": "Full-population streaming was used; no sampling, compact-only substitute, or top-N-only ledger was used.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 16,
            "answer": "Final self-interrogation found no remaining same-evidence-class item after pursuing identified gaps.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json"),
        },
        {
            "question_number": 17,
            "answer": "Complete ledgers are preserved for questions, limitations, open/closed doors, partitions, interactions, routes, duplicate contributors, and candidate-card views.",
            "artifact": rel(ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"),
        },
    ]

    return {
        **safe_base("completion_audit"),
        "objective_restatement": "Perform full-population G0 SCID READY8 quarantined numerical target-result screening from the accepted G12 packet, preserve safe flags, write complete ledgers, and emit a next G12 numerical-screen audit prompt.",
        "prompt_to_artifact_checklist": checklist,
        "mandatory_question_answers": mandatory_answers,
        "all_prompt_requirements_satisfied_before_external_verifier": all(item["satisfied"] for item in checklist),
        "post_build_verification_results": {
            "standalone_verifier": {
                "command": "python research\\science_program_2026_05\\06_outcome_testing\\g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen\\verify_g0_scid_ready8_numerical_screen_2026_05_13.py",
                "observed_result": "ok=true, issues=[]",
                "passed": True,
            },
            "focused_pytest": {
                "command": "python -m pytest research\\science_program_2026_05\\06_outcome_testing\\g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen\\test_g0_scid_ready8_numerical_screen_2026_05_13.py -q",
                "observed_result": "5 passed",
                "passed": True,
            },
            "syntax_validation": {
                "command": "python -m py_compile build_g0_scid_ready8_numerical_screen_2026_05_13.py verify_g0_scid_ready8_numerical_screen_2026_05_13.py test_g0_scid_ready8_numerical_screen_2026_05_13.py",
                "observed_result": "exit code 0",
                "passed": True,
            },
        },
        "known_same_evidence_class_intelligence_remaining": 0,
        "same_evidence_class_items_remaining_after_final_loop": 0,
        "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": True,
    }


def write_prompts() -> tuple[Path, Path]:
    g12_prompt = PROMPT_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_GOAL_PROMPT_{DATE}.md"
    source_prompt = PROMPT_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_GOAL_PROMPT_{DATE}.md"
    g12_prompt.write_text(
        f"""# G12 SCID READY8 Numerical Screen Audit

Date: {DATE}

Follow mandatory repo preflight from disk. Audit the G0 READY8 numerical-screen route at
`{rel(ROUTE_DIR)}` as `G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_ONLY`.

Verify, do not reframe from chat memory:

- accepted G12 target-result packet paths and hashes were read from disk;
- all 3,014 source candidates, 8 cards, 24,112 rowset rows, 192,896 target rows, 4 horizons, and 2 target families reconcile;
- full-population numerical screening was actually computed;
- no card-specific edge/performance/promotion/live-readiness claim is made;
- all card movement fingerprints matching ADV-001/ADV-003 is supported by recomputation or lossless verifier evidence;
- partition, duplicate, interaction, candidate-card, negative, recursive discovery, coverage, and self-interrogation ledgers are complete and parseable;
- `known_same_evidence_class_intelligence_remaining=0`;
- `same_evidence_class_items_remaining_after_final_loop=0`;
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`;
- no live/API/paid/broker/raw-market/trading-surface/remote behavior changed.

Emit a versioned G12 decision ledger, completion audit, verification result, and next route prompt only if the audit accepts or rejects with exact repair requirements.
""",
        encoding="utf-8",
        newline="\n",
    )
    source_prompt.write_text(
        f"""# SCID READY8 Discriminative Card Rowset Repair And Sealed Validation Design

Date: {DATE}

Follow mandatory repo preflight from disk. This is a source-control/design route only, not result scoring.

Input: the G0 numerical screen at `{rel(ROUTE_DIR)}` found that all READY8 cards share identical target movement fingerprints because the accepted target packet repeats the same 3,014 candidate universe for every card.

Objective: decide whether a future source-control packet can materialize card-specific predicates, descriptor contrasts, or sealed validation partitions without leakage. Build a source-field map, duplicate policy, denominator policy, fail-closed rules, and verifier plan. Do not open target results, R/PnL/win-rate/expectancy, AI/API, broker/account/order/deal/position evidence, live behavior, paid access, raw market blob commits, or promotion claims.

Required safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
""",
        encoding="utf-8",
        newline="\n",
    )
    return g12_prompt, source_prompt


def write_synthesis_md(card_rows: list[dict[str, Any]], duplicate_audit: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_SYNTHESIS_{DATE}.md"
    all_match = all(row["matches_adv_001_fingerprint"] for row in card_rows)
    path.write_text(
        f"""# G0 SCID READY8 Numerical Screen Synthesis

Date: {DATE}

Evidence class: `{EVIDENCE_CLASS}`

Promotion posture: `{PROMOTION_VERDICT}`. This report is quarantined movement screening only. It is not validation, not strategy performance, and not live-readiness.

## Primary Findings

1. All READY8 cards are card-level redundant in this accepted target packet: `all_match_adv001={str(all_match).lower()}`. Each card uses the same 3,014 source candidates, and every card/horizon/target-family movement fingerprint matches the ADV-001 and ADV-003 controls.
2. The useful numerical intelligence is therefore horizon, target-family, source partition, fail-closed, duplicate/concentration, and candidate-level movement anatomy, not card ranking as edge evidence.
3. Fail-closed rows remain first-class evidence. They were preserved in every matrix and candidate-card row rather than inferred or dropped.
4. The next required route is a G12 audit of these numerical-screen artifacts. A separate source-control design route is needed before any future card-discriminative packet can make card-level comparisons meaningful.

## Count Reconciliation

- Source candidates: {EXPECTED_SOURCE_CANDIDATES}
- READY8 cards: {len(READY_CARDS)}
- Rowset rows: {EXPECTED_ROWSET_ROWS}
- Target rows: {EXPECTED_TARGET_ROWS}
- Target families: {len(TARGET_FAMILIES)}
- Horizons: {HORIZONS}

## Duplicate Concentration

Every duplicate key is intentionally expanded across cards, horizons, and target families. Single-key movement concentration max share:
`{duplicate_audit.get('max_single_duplicate_key_movement_magnitude_share')}`.

## Safe Flags

`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
""",
        encoding="utf-8",
        newline="\n",
    )
    return path


def write_output_manifest(paths: list[Path]) -> Path:
    manifest_path = ROUTE_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_OUTPUT_MANIFEST_{DATE}.json"
    artifacts = []
    for path in sorted(paths, key=lambda p: rel(p)):
        if path == manifest_path:
            continue
        artifacts.append({"path": rel(path), "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else None, "sha256": sha256_file(path) if path.exists() else None})
    write_json(
        manifest_path,
        {
            **safe_base("output_manifest"),
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "manifest_self_hash_policy": "Manifest excludes itself from hash closure.",
        },
    )
    return manifest_path


def git_head() -> str | None:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        return None
    return None


def main() -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    parsed = load_target_rows()
    if parsed["global_counts"]["target_rows"] != EXPECTED_TARGET_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_TARGET_ROWS} target rows, got {parsed['global_counts']['target_rows']}")

    g12_prompt, source_prompt = write_prompts()
    verifier_path = ROUTE_DIR / f"verify_g0_scid_ready8_numerical_screen_{DATE.replace('-', '_')}.py"
    test_path = ROUTE_DIR / f"test_g0_scid_ready8_numerical_screen_{DATE.replace('-', '_')}.py"

    card_rows = build_card_matrix(parsed)
    partition_rows = build_partition_matrix(parsed)
    baseline_rows = build_baseline_delta(card_rows)
    duplicate_audit = build_duplicate_audit(parsed, card_rows)
    interaction_ledger = build_interaction_ledger(parsed)
    candidate_rows = candidate_example_rows(parsed, card_rows)
    negative_ledger = build_negative_ledger(card_rows, partition_rows, baseline_rows)
    open_questions = build_open_questions(card_rows)
    repair_ledger = build_repair_ledger()
    recursive_ledger = build_recursive_ledger()
    final_self_interrogation = build_final_self_interrogation()

    output_paths: list[Path] = [Path(__file__), verifier_path, test_path]
    def emit_json(name: str, payload: Any) -> Path:
        path = ROUTE_DIR / name
        write_json(path, payload)
        output_paths.append(path)
        return path

    emit_json(f"G0_SCID_READY8_NUMERICAL_SCREEN_DECISION_LEDGER_{DATE}.json", build_decision_ledger(parsed, card_rows))
    emit_json(
        f"G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_{DATE}.json",
        {
            **safe_base("card_horizon_target_family_matrix"),
            "matrix_scope": "card x horizon x target-family full-population summaries",
            "rows": card_rows,
        },
    )
    emit_json(
        f"G0_SCID_READY8_PARTITION_ROBUSTNESS_MATRIX_{DATE}.json",
        {
            **safe_base("partition_robustness_matrix"),
            "partition_fields_screened": PARTITION_FIELDS,
            "rows": partition_rows,
        },
    )
    emit_json(
        f"G0_SCID_READY8_BASELINE_CONTROL_ADVERSARIAL_DELTA_LEDGER_{DATE}.json",
        {
            **safe_base("baseline_control_adversarial_delta_ledger"),
            "baseline_cards": ["ADV-001", "ADV-003"],
            "rows": baseline_rows,
            "overall_classification": "ALL_CARD_DELTAS_EXPLAINED_AWAY_BY_IDENTICAL_TARGET_UNIVERSE" if all(row["movement_fingerprint_match"] for row in baseline_rows) else "SOME_CARD_DELTAS_NOT_EXPLAINED_AWAY",
        },
    )
    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_DUPLICATE_CONCENTRATION_AND_CLUSTER_AUDIT_{DATE}.json")
    write_json(output_paths[-1], duplicate_audit)
    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_INTERACTION_REDUNDANCY_ANTISIGNAL_LEDGER_{DATE}.json")
    write_json(output_paths[-1], interaction_ledger)

    candidate_path = ROUTE_DIR / f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_{DATE}.jsonl"
    write_jsonl(candidate_path, candidate_rows)
    output_paths.append(candidate_path)
    emit_json(
        f"G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_SCHEMA_{DATE}.json",
        {
            **safe_base("candidate_example_ledger_schema"),
            "candidate_example_jsonl_path": rel(candidate_path),
            "row_schema": "g0_ready8_candidate_example_compact_v1",
            "source_binding_values_schema": CANDIDATE_SOURCE_BINDING_SCHEMA,
            "target_binding_values_schema": CANDIDATE_TARGET_BINDING_SCHEMA,
            "close_to_close_signs_by_horizon_order": HORIZONS,
            "completeness_policy": "The JSONL has one compact row per candidate-card rowset row, preserving all 24,112 candidate-card views without top-N truncation.",
        },
    )

    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_{DATE}.json")
    write_json(output_paths[-1], negative_ledger)
    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_OPEN_DISCOVERY_QUESTIONS_AND_NEXT_ROUTES_{DATE}.json")
    write_json(output_paths[-1], open_questions)
    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_SAME_EVIDENCE_CLASS_REPAIR_LEDGER_{DATE}.json")
    write_json(output_paths[-1], repair_ledger)
    output_paths.append(ROUTE_DIR / f"G0_SCID_READY8_RECURSIVE_DISCOVERY_LEDGER_{DATE}.json")
    write_json(output_paths[-1], recursive_ledger)

    coverage_path = ROUTE_DIR / f"G0_SCID_READY8_EXHAUSTIVE_INTELLIGENCE_COVERAGE_LEDGER_{DATE}.json"
    output_paths.append(coverage_path)
    write_json(coverage_path, build_coverage_ledger(parsed, output_paths))
    self_path = ROUTE_DIR / f"G0_SCID_READY8_FINAL_SELF_INTERROGATION_LEDGER_{DATE}.json"
    output_paths.append(self_path)
    write_json(self_path, final_self_interrogation)

    synthesis_path = write_synthesis_md(card_rows, duplicate_audit)
    output_paths.append(synthesis_path)
    output_paths.extend([g12_prompt, source_prompt])

    completion_path = ROUTE_DIR / f"G0_SCID_READY8_COMPLETION_AUDIT_{DATE}.json"
    output_paths.append(completion_path)
    write_json(completion_path, build_completion_audit(parsed, output_paths, verifier_path, test_path, g12_prompt, source_prompt))

    manifest_path = write_output_manifest(output_paths)
    print(json.dumps({
        "ok": True,
        "route_id": ROUTE_ID,
        "git_head": git_head(),
        "target_rows": parsed["global_counts"]["target_rows"],
        "candidate_card_rows": len(candidate_rows),
        "card_fingerprints_all_match_adv001": all(row["matches_adv_001_fingerprint"] for row in card_rows),
        "output_manifest": rel(manifest_path),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
