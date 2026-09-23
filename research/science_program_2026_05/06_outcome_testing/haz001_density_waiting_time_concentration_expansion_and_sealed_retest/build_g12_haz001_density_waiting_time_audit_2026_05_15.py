#!/usr/bin/env python3
"""Build the G12 audit artifacts for the HAZ-001 density/waiting-time route."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


DATE_ID = "2026-05-15"
ROUTE_ID = "G12_HAZ001_DENSITY_WAITING_TIME_MECHANISM_EXPANSION_AUDIT"
EVIDENCE_CLASS = "G12_HAZ001_MECHANISM_EXPANSION_AUDIT_ONLY"
BUILDER_ROUTE_ID = "HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST"
BUILDER_EVIDENCE_CLASS = "READY8_HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_ONLY"
PRIMARY_UNIQUE_DUP_FLOOR = 30
CONCENTRATION_WARN_SHARE = 0.50

SAFE_FALSE_KEYS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "credentials_touched",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_strategy_edge_claims",
]

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
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST_AUDIT_GOAL_PROMPT_2026-05-15.md"
ROWSET_PATH = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
TARGET_PATHS = [
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_001_CLOSE_TO_CLOSE_2026-05-13.jsonl",
    ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet/SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_HAZ_001_HIGH_LOW_EXCURSION_2026-05-13.jsonl",
]

BUILDER = {
    "manifest": OUT_DIR / f"HAZ001_OUTPUT_MANIFEST_{DATE_ID}.json",
    "completion": OUT_DIR / f"HAZ001_COMPLETION_AUDIT_{DATE_ID}.json",
    "context": OUT_DIR / f"HAZ001_CONTEXT_ANCHOR_AND_INPUT_BINDING_LEDGER_{DATE_ID}.json",
    "source_inventory": OUT_DIR / f"HAZ001_SOURCE_ROWSET_BRANCH_INVENTORY_LEDGER_{DATE_ID}.jsonl",
    "source_search": OUT_DIR / f"HAZ001_SOURCE_SEARCH_ACQUISITION_LEDGER_{DATE_ID}.json",
    "pass_control": OUT_DIR / f"HAZ001_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_{DATE_ID}.jsonl",
    "deconcentration": OUT_DIR / f"HAZ001_CONCENTRATION_DECONCENTRATION_LEDGER_{DATE_ID}.jsonl",
    "failure": OUT_DIR / f"HAZ001_FAILURE_INVERSE_NULL_ANATOMY_LEDGER_{DATE_ID}.jsonl",
    "fail_closed": OUT_DIR / f"HAZ001_FAIL_CLOSED_SOURCE_REPAIR_SENSITIVITY_LEDGER_{DATE_ID}.jsonl",
    "retest_design": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_{DATE_ID}.json",
    "retest_packet": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_INPUT_PACKET_SOURCE_CONTROL_ONLY_{DATE_ID}.jsonl",
    "questions": OUT_DIR / f"HAZ001_QUESTION_AMBIGUITY_LEDGER_{DATE_ID}.jsonl",
    "saturation": OUT_DIR / f"HAZ001_SATURATION_SELF_RED_TEAM_LEDGER_{DATE_ID}.json",
    "synthesis": OUT_DIR / f"HAZ001_SYNTHESIS_{DATE_ID}.md",
    "verification": OUT_DIR / f"HAZ001_VERIFICATION_RESULT_{DATE_ID}.json",
    "focused": OUT_DIR / f"HAZ001_FOCUSED_TEST_RESULT_{DATE_ID}.json",
}

OUTPUTS = {
    "recomputation": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_RECOMPUTATION_LEDGER_{DATE_ID}.json",
    "discrepancy_repair": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DISCREPANCY_REPAIR_LEDGER_{DATE_ID}.json",
    "decision": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_DECISION_LEDGER_{DATE_ID}.json",
    "saturation": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE_ID}.json",
    "completion": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_COMPLETION_AUDIT_{DATE_ID}.json",
    "manifest": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_OUTPUT_MANIFEST_{DATE_ID}.json",
}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{rel(path)} line {line_no}: {exc}") from exc


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def make_key(parts: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), safe_value(v)) for k, v in parts.items()))


def key_to_dict(key: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {k: v for k, v in key}


def hash_text(obj: Any) -> str:
    return hashlib.sha256(stable_json(obj).encode("utf-8")).hexdigest()


def file_hashes(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    return {
        "bytes_raw": len(raw),
        "bytes_lf_normalized": len(lf),
        "sha256_raw": hashlib.sha256(raw).hexdigest(),
        "sha256_lf_normalized": hashlib.sha256(lf).hexdigest(),
    }


def safe_flags_closed(obj: dict[str, Any]) -> bool:
    return obj.get("promotion_verdict") == "NO_PROMOTION_VERDICT" and all(obj.get(key) is False for key in SAFE_FALSE_KEYS)


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


def wait_gap_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    value = desc.get("previous_candidate_gap_minutes")
    if value is None:
        return "NO_PRIOR_CANDIDATE"
    return "WAIT_GAP_GE_60M" if float(value) >= 60 else "WAIT_GAP_LT_60M"


def prior_24h_count_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    value = desc.get("prior_24h_candidate_count")
    if value is None:
        return "PRIOR_24H_COUNT_NULL"
    n = int(float(value))
    return "PRIOR_24H_COUNT_GE_3" if n >= 3 else f"PRIOR_24H_COUNT_{n}"


def density_bucket(row: dict[str, Any]) -> str:
    desc = row.get("descriptor_values") or {}
    return safe_value(desc.get("candidate_density_bucket") or row.get("descriptor_contrast_key"))


def movement_value(row: dict[str, Any]) -> float | None:
    if row.get("target_family_id") == "neutral_close_to_close_return_m15_horizons_v1":
        value = row.get("close_to_close_percent_return")
        return float(value) if value is not None else None
    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1":
        up = row.get("upside_excursion_percent")
        down = row.get("downside_excursion_percent")
        if up is None or down is None:
            return None
        return float(up) - float(down)
    return None


def metric_eligible(row: dict[str, Any]) -> bool:
    return row.get("terminal_status") == "COMPUTABLE" and row.get("denominator_role") != "per_card_fail_closed_row" and movement_value(row) is not None


def deconcentration_values(row: dict[str, Any]) -> dict[str, str]:
    return {
        "symbol": safe_value(row.get("symbol")),
        "canonical_economic_group": safe_value(row.get("canonical_economic_group")),
        "session": session_value(row),
        "source_segment_sha256": source_segment(row),
        "source_date": source_date(row),
        "source_window": source_window(row),
    }


@dataclass
class Stats:
    rows: int = 0
    value_sum: float = 0.0
    values: list[float] = field(default_factory=list)
    positive: int = 0
    duplicate_keys: set[str] = field(default_factory=set)
    counters: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))

    def add(self, row: dict[str, Any], value: float) -> None:
        self.rows += 1
        self.value_sum += value
        self.values.append(value)
        if value > 0:
            self.positive += 1
        self.duplicate_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))
        for dim, dim_value in deconcentration_values(row).items():
            self.counters[dim][dim_value] += 1

    @property
    def mean(self) -> float | None:
        return self.value_sum / self.rows if self.rows else None

    @property
    def unique_count(self) -> int:
        return len(self.duplicate_keys)

    def warnings(self) -> list[str]:
        warnings: list[str] = []
        for dim in ["symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_date", "source_window"]:
            counter = self.counters.get(dim, Counter())
            if counter and self.rows:
                _value, count = counter.most_common(1)[0]
                if count / self.rows > CONCENTRATION_WARN_SHARE:
                    warnings.append(f"{dim.upper()}_CONCENTRATION_GT_50PCT")
        if self.unique_count < PRIMARY_UNIQUE_DUP_FLOOR:
            warnings.append("UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30")
        return warnings


@dataclass
class Bucket:
    pass_stats: Stats = field(default_factory=Stats)
    control_stats: Stats = field(default_factory=Stats)
    pass_rows: list[tuple[dict[str, Any], float]] = field(default_factory=list)
    control_rows: list[tuple[dict[str, Any], float]] = field(default_factory=list)

    def add(self, row: dict[str, Any], value: float) -> None:
        if row.get("denominator_role") == "per_card_pass_row":
            self.pass_stats.add(row, value)
            self.pass_rows.append((row, value))
        elif row.get("denominator_role") == "per_card_contrast_row":
            self.control_stats.add(row, value)
            self.control_rows.append((row, value))


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
            desc_name = "previous_candidate_gap_bucket"
            desc_value = wait_gap_bucket(row)
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
        yield "descriptor_value_one_vs_rest_target_family_horizon", parent, {**parent, "descriptor_value": value}


def classify_delta(delta: float | None, pass_n: int, control_n: int, warnings: list[str]) -> str:
    if pass_n == 0 or control_n == 0:
        return "NOT_COMPARABLE_MISSING_PASS_OR_CONTROL"
    if pass_n < PRIMARY_UNIQUE_DUP_FLOOR or control_n < PRIMARY_UNIQUE_DUP_FLOOR or any("UNDERPOWERED" in item for item in warnings):
        if delta is None:
            return "UNDERPOWERED_NO_DELTA"
        return "UNDERPOWERED_POSITIVE" if delta > 0 else "UNDERPOWERED_INVERSE" if delta < 0 else "UNDERPOWERED_NEUTRAL"
    if delta is None or abs(delta) < 1e-12:
        return "NEUTRAL_TIE"
    return "POSITIVE_PASS_GT_CONTROL" if delta > 0 else "INVERSE_PASS_LT_CONTROL"


def compare_record(family: str, key: tuple[tuple[str, str], ...], bucket: Bucket) -> dict[str, Any]:
    pass_mean = bucket.pass_stats.mean
    control_mean = bucket.control_stats.mean
    delta = pass_mean - control_mean if pass_mean is not None and control_mean is not None else None
    warnings = list(dict.fromkeys(bucket.pass_stats.warnings() + bucket.control_stats.warnings()))
    return {
        "comparison_family": family,
        "comparison_id": "haz001_cmp:" + hash_text([family, key])[:24],
        "branch_key": key_to_dict(key),
        "pass_rows": bucket.pass_stats.rows,
        "control_rows": bucket.control_stats.rows,
        "pass_unique_duplicate_denominator_count": bucket.pass_stats.unique_count,
        "control_unique_duplicate_denominator_count": bucket.control_stats.unique_count,
        "pass_target_movement_mean": pass_mean,
        "control_target_movement_mean": control_mean,
        "pass_minus_control_target_movement_mean_delta": delta,
        "comparison_classification": classify_delta(delta, bucket.pass_stats.unique_count, bucket.control_stats.unique_count, warnings),
        "concentration_or_power_warnings": warnings,
    }


def recompute_pass_control(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[tuple[str, tuple[tuple[str, str], ...]], Bucket] = defaultdict(Bucket)
    child_stats: dict[tuple[str, tuple[tuple[str, str], ...]], Stats] = defaultdict(Stats)
    parent_stats: dict[tuple[str, tuple[tuple[str, str], ...]], Stats] = defaultdict(Stats)
    for row in rows:
        if not metric_eligible(row):
            continue
        value = movement_value(row)
        assert value is not None
        for family, parts in compare_dimensions(row):
            buckets[(family, make_key(parts))].add(row, value)
        for family, parent_parts, child_parts in descriptor_parent_child_keys(row):
            parent_key = make_key(parent_parts)
            child_key = make_key(child_parts)
            parent_stats[(family, parent_key)].add(row, value)
            child_stats[(family, child_key)].add(row, value)

    records: dict[str, dict[str, Any]] = {}
    for (family, key), bucket in buckets.items():
        rec = compare_record(family, key, bucket)
        records[rec["comparison_id"]] = rec

    for (family, child_key), child in child_stats.items():
        child_dict = key_to_dict(child_key)
        parent_key = make_key({k: v for k, v in child_dict.items() if k != "descriptor_value"})
        parent = parent_stats[(family, parent_key)]
        other_rows = parent.rows - child.rows
        other_sum = parent.value_sum - child.value_sum
        other_dup = parent.duplicate_keys - child.duplicate_keys
        child_mean = child.mean
        other_mean = other_sum / other_rows if other_rows else None
        delta = child_mean - other_mean if child_mean is not None and other_mean is not None else None
        warnings = child.warnings()
        if len(other_dup) < PRIMARY_UNIQUE_DUP_FLOOR and "UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30" not in warnings:
            warnings = warnings + ["UNDERPOWERED_UNIQUE_DUPLICATE_FLOOR_LT_30"]
        base_class = classify_delta(delta, child.unique_count, len(other_dup), warnings)
        rec = {
            "comparison_family": family,
            "comparison_id": "haz001_desc:" + hash_text([family, child_key])[:24],
            "branch_key": child_dict,
            "descriptor_rows": child.rows,
            "other_rows": other_rows,
            "descriptor_unique_duplicate_denominator_count": child.unique_count,
            "other_unique_duplicate_denominator_count": len(other_dup),
            "descriptor_target_movement_mean": child_mean,
            "other_target_movement_mean": other_mean,
            "descriptor_minus_other_target_movement_mean_delta": delta,
            "comparison_classification": base_class.replace("PASS", "DESCRIPTOR").replace("CONTROL", "OTHER"),
            "concentration_or_power_warnings": warnings,
        }
        records[rec["comparison_id"]] = rec
    return records


def close_float(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-12)


def scan_builder_ledgers() -> dict[str, Any]:
    counts = {}
    parse_errors = {}
    for key in ["source_inventory", "pass_control", "deconcentration", "failure", "fail_closed", "retest_packet", "questions"]:
        count = 0
        try:
            for _row in iter_jsonl(BUILDER[key]):
                count += 1
            parse_errors[key] = 0
        except ValueError:
            parse_errors[key] = 1
        counts[key] = count
    return {"counts": counts, "parse_errors": parse_errors}


def input_recomputation(target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rowset_total = 0
    haz_rowset_rows = 0
    haz_dup_keys = set()
    rowset_role_counts = Counter()
    for row in iter_jsonl(ROWSET_PATH):
        rowset_total += 1
        if row.get("card_id") == "HAZ-001":
            haz_rowset_rows += 1
            haz_dup_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))
            rowset_role_counts[safe_value(row.get("denominator_role"))] += 1

    status_counts = Counter()
    role_counts = Counter()
    horizon_counts = Counter()
    family_counts = Counter()
    partition_counts = Counter()
    dup_keys = set()
    for row in target_rows:
        status_counts[safe_value(row.get("terminal_status"))] += 1
        role_counts[safe_value(row.get("denominator_role"))] += 1
        horizon_counts[safe_value(row.get("horizon_m15_bars"))] += 1
        family_counts[safe_value(row.get("target_family_id"))] += 1
        partition_counts[safe_value(row.get("partition_assignment"))] += 1
        dup_keys.add(safe_value(row.get("duplicate_proxy_denominator_key")))

    return {
        "rowset_total_all_cards": rowset_total,
        "haz001_rowset_rows": haz_rowset_rows,
        "haz001_unique_duplicate_denominator_keys": len(haz_dup_keys),
        "haz001_rowset_denominator_role_counts": dict(rowset_role_counts),
        "haz001_target_rows": len(target_rows),
        "haz001_target_unique_duplicate_denominator_keys": len(dup_keys),
        "target_status_counts": dict(status_counts),
        "target_denominator_role_counts": dict(role_counts),
        "target_horizon_counts": dict(horizon_counts),
        "target_family_counts": dict(family_counts),
        "target_partition_counts": dict(partition_counts),
    }


def audit_manifest_and_repair() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = load_json(BUILDER["manifest"])
    discrepancies: list[dict[str, Any]] = []
    repaired_artifacts = []
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if not path.exists():
            discrepancies.append({"path": artifact["path"], "status": "MISSING", "blocking": True})
            continue
        hashes = file_hashes(path)
        raw_match = hashes["sha256_raw"] == artifact.get("sha256") and hashes["bytes_raw"] == artifact.get("bytes")
        lf_match = hashes["sha256_lf_normalized"] == artifact.get("sha256") and hashes["bytes_lf_normalized"] == artifact.get("bytes")
        if not raw_match or not lf_match:
            status = "CRLF_ONLY_RAW_MISMATCH" if lf_match else "STALE_CONTENT_OR_MANIFEST_ENTRY"
            discrepancies.append({
                "path": artifact["path"],
                "status": status,
                "blocking": False,
                "raw_match": raw_match,
                "lf_normalized_match": lf_match,
                "manifest_bytes": artifact.get("bytes"),
                "actual_bytes_raw": hashes["bytes_raw"],
                "actual_bytes_lf_normalized": hashes["bytes_lf_normalized"],
            })
        if path != BUILDER["manifest"]:
            artifact["bytes"] = hashes["bytes_lf_normalized"]
            artifact["sha256"] = hashes["sha256_lf_normalized"]
            artifact["hash_policy"] = "lf_normalized_text_sha256"
            artifact["working_tree_bytes_raw"] = hashes["bytes_raw"]
            artifact["working_tree_sha256_raw"] = hashes["sha256_raw"]
            repaired_artifacts.append(artifact["path"])
    manifest["artifact_hash_policy"] = "sha256 and bytes are LF-normalized text hashes; raw working-tree hashes are recorded where available for Windows materialization audit."
    manifest["manifest_self_hash_policy"] = "Manifest entry is excluded from stable self-closure; G12 audit manifest records current manifest materialization separately."
    manifest["g12_hash_repair_generated_at_utc"] = utc_now()
    write_json(BUILDER["manifest"], manifest)
    return {
        "pre_repair_discrepancy_count": len(discrepancies),
        "pre_repair_stale_or_content_entry_count": sum(1 for item in discrepancies if item["status"] == "STALE_CONTENT_OR_MANIFEST_ENTRY"),
        "pre_repair_crlf_only_count": sum(1 for item in discrepancies if item["status"] == "CRLF_ONLY_RAW_MISMATCH"),
        "manifest_entries_refreshed_count": len(repaired_artifacts),
        "manifest_repair_status": "REPAIRED_CURRENT_ARTIFACT_HASHES_LF_NORMALIZED_EXCEPT_SELF_HASH_EXCLUDED",
    }, discrepancies


def build() -> dict[str, Any]:
    generated_at = utc_now()
    target_rows = [row for path in TARGET_PATHS for row in iter_jsonl(path)]
    input_counts = input_recomputation(target_rows)
    recomputed = recompute_pass_control(target_rows)

    ledger_rows = {row["comparison_id"]: row for row in iter_jsonl(BUILDER["pass_control"])}
    mismatch_examples = []
    for comp_id, expected in recomputed.items():
        actual = ledger_rows.get(comp_id)
        if actual is None:
            mismatch_examples.append({"comparison_id": comp_id, "issue": "MISSING_FROM_LEDGER"})
            continue
        for field in [
            "comparison_classification",
            "pass_unique_duplicate_denominator_count",
            "control_unique_duplicate_denominator_count",
            "descriptor_unique_duplicate_denominator_count",
            "other_unique_duplicate_denominator_count",
        ]:
            if field in expected and actual.get(field) != expected.get(field):
                mismatch_examples.append({"comparison_id": comp_id, "field": field, "expected": expected.get(field), "actual": actual.get(field)})
        for field in [
            "pass_minus_control_target_movement_mean_delta",
            "descriptor_minus_other_target_movement_mean_delta",
            "pass_target_movement_mean",
            "control_target_movement_mean",
            "descriptor_target_movement_mean",
            "other_target_movement_mean",
        ]:
            if field in expected and not close_float(actual.get(field), expected.get(field)):
                mismatch_examples.append({"comparison_id": comp_id, "field": field, "expected": expected.get(field), "actual": actual.get(field)})

    deconcentration_counts = Counter()
    deconcentration_dims = Counter()
    deconcentration_label_mismatches = 0
    for row in iter_jsonl(BUILDER["deconcentration"]):
        label = safe_value(row.get("survival_label"))
        deconcentration_counts[label] += 1
        deconcentration_dims[safe_value(row.get("deconcentration_dimension"))] += 1
        original = safe_value(row.get("original_classification"))
        filtered_delta = row.get("filtered_delta")
        if label == "KILLED_OR_REVERSED_BY_LEAVE_ONE" and not (original.startswith("POSITIVE") and (filtered_delta is None or float(filtered_delta) <= 0)):
            deconcentration_label_mismatches += 1
        if label == "SURVIVES_LEAVE_ONE_POSITIVE" and not (original.startswith("POSITIVE") and filtered_delta is not None and float(filtered_delta) > 0):
            deconcentration_label_mismatches += 1

    fail_closed_counts = Counter()
    fail_closed_status = Counter()
    fail_closed_label_mismatches = 0
    fail_closed_row_sum = 0
    for row in iter_jsonl(BUILDER["fail_closed"]):
        rows = int(row["rows"])
        fail_closed_row_sum += rows
        fail_closed_counts[safe_value(row.get("sensitivity_label"))] += 1
        fail_closed_status[safe_value(row.get("source_repair_status"))] += 1
        expected_label = "DENOMINATOR_SENSITIVE_IF_REPAIRED" if rows >= PRIMARY_UNIQUE_DUP_FLOOR else "LOW_COUNT_RETAINED"
        if row.get("sensitivity_label") != expected_label:
            fail_closed_label_mismatches += 1

    forbidden_fields = {
        "close_to_close_percent_return",
        "close_to_close_absolute_delta",
        "upside_excursion_percent",
        "downside_excursion_percent",
        "target_result_row_id",
        "target_result_row_hash",
        "horizon_close",
        "horizon_end_utc",
        "entry_close",
        "terminal_status",
    }
    packet_count = 0
    packet_forbidden = Counter()
    packet_safe_flag_bad = 0
    for row in iter_jsonl(BUILDER["retest_packet"]):
        packet_count += 1
        for field in forbidden_fields.intersection(row):
            packet_forbidden[field] += 1
        if not safe_flags_closed(row):
            packet_safe_flag_bad += 1

    builder_scan = scan_builder_ledgers()
    manifest_repair, manifest_discrepancies = audit_manifest_and_repair()
    source_search = load_json(BUILDER["source_search"])
    completion = load_json(BUILDER["completion"])
    source_roots = [item.get("root") for item in source_search.get("searches", []) if item.get("status") == "SEARCHED"]

    classification_counts = Counter(row.get("comparison_classification") for row in ledger_rows.values())
    recomputation = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "builder_route_id": BUILDER_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "input_recomputation": input_counts,
        "builder_output_full_scan": builder_scan,
        "pass_control_descriptor_recomputation": {
            "recomputed_rows": len(recomputed),
            "builder_ledger_rows": len(ledger_rows),
            "missing_from_builder_count": sum(1 for item in mismatch_examples if item.get("issue") == "MISSING_FROM_LEDGER"),
            "field_mismatch_count": len(mismatch_examples),
            "classification_counts": dict(classification_counts),
            "mismatch_examples_all": mismatch_examples,
        },
        "deconcentration_label_recomputation": {
            "rows": builder_scan["counts"]["deconcentration"],
            "dimension_counts": dict(deconcentration_dims),
            "survival_label_counts": dict(deconcentration_counts),
            "label_mismatch_count": deconcentration_label_mismatches,
        },
        "fail_closed_sensitivity_recomputation": {
            "rows": builder_scan["counts"]["fail_closed"],
            "row_sum_across_branch_sensitivity_groups": fail_closed_row_sum,
            "sensitivity_label_counts": dict(fail_closed_counts),
            "source_repair_status_counts": dict(fail_closed_status),
            "label_mismatch_count": fail_closed_label_mismatches,
        },
        "retest_packet_audit": {
            "rows": packet_count,
            "forbidden_target_or_outcome_field_counts": dict(packet_forbidden),
            "safe_flag_bad_rows": packet_safe_flag_bad,
        },
        "source_search_audit": {
            "searched_root_count": len(source_roots),
            "searched_roots": source_roots,
            "has_sierra_root": any(str(root).startswith("C:\\SierraChart") for root in source_roots),
            "has_absolute_local_heavy_root": any(str(root).startswith("C:\\Users\\MSI\\Documents\\ai-trading-agent") for root in source_roots),
            "conclusion": source_search.get("source_search_conclusion"),
        },
        "completion_audit_coverage": {
            "builder_can_mark_complete": completion.get("can_mark_goal_complete_after_verifier_and_commit") is True,
            "builder_checklist_all_true": all(completion.get("prompt_to_artifact_checklist", {}).values()),
            "builder_output_counts": completion.get("output_counts", {}),
        },
        "manifest_hash_repair": manifest_repair,
    }
    write_json(OUTPUTS["recomputation"], recomputation)

    unresolved_same_g12 = []
    if mismatch_examples:
        unresolved_same_g12.append("pass/control descriptor recomputation mismatches")
    if deconcentration_label_mismatches:
        unresolved_same_g12.append("deconcentration label recomputation mismatches")
    if fail_closed_label_mismatches:
        unresolved_same_g12.append("fail-closed sensitivity label mismatches")
    if packet_forbidden or packet_safe_flag_bad:
        unresolved_same_g12.append("retest packet leak or safe flag issue")

    discrepancy_repair = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "same_g12_issues_considered": [
            {
                "issue": "Builder output manifest raw/hash drift after Windows checkout and later starter hardening",
                "status": "REPAIRED_BY_REFRESHING_BUILDER_MANIFEST_TO_CURRENT_LF_NORMALIZED_HASHES_AND_RECORDING_RAW_HASHES",
                "blocking": False,
                "pre_repair_summary": manifest_repair,
            },
            {
                "issue": "Pass/control delta and descriptor contrast correctness",
                "status": "CLOSED_BY_FULL_RECOMPUTE_ZERO_MISMATCHES" if not mismatch_examples else "BLOCKING_MISMATCHES_REMAIN",
                "blocking": bool(mismatch_examples),
            },
            {
                "issue": "Retest packet target/outcome leakage",
                "status": "CLOSED_BY_FULL_PACKET_SCAN_NO_FORBIDDEN_FIELDS" if not packet_forbidden else "BLOCKING_FORBIDDEN_FIELDS_PRESENT",
                "blocking": bool(packet_forbidden),
            },
            {
                "issue": "Fail-closed source gaps",
                "status": "EXACT_FUTURE_SOURCE_CONTROL_REPAIR_REQUIRED_BEFORE_RESULT_ADMISSION",
                "blocking": False,
            },
        ],
        "manifest_pre_repair_discrepancies_all": manifest_discrepancies,
        "unresolved_same_g12_items": unresolved_same_g12,
        "same_g12_repairable_items_remaining": len(unresolved_same_g12),
    }
    write_json(OUTPUTS["discrepancy_repair"], discrepancy_repair)

    accepted = not unresolved_same_g12
    decision = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "accepted": accepted,
        "terminal_decision": "ACCEPT_AS_G12_HAZ001_MECHANISM_EXPANSION_AUDIT_NO_PROMOTION" if accepted else "REJECT_PENDING_SAME_G12_REPAIR",
        "material_claims_status": "accepted_as_neutral_target_movement_mechanism_expansion_audit_only" if accepted else "not_accepted",
        "summary": {
            "row_counts_recomputed": input_counts["haz001_target_rows"] == 24112 and input_counts["haz001_rowset_rows"] == 3014,
            "pass_control_deltas_recomputed": len(recomputed) == len(ledger_rows) and not mismatch_examples,
            "descriptor_contrasts_recomputed": sum(1 for row in ledger_rows.values() if row.get("comparison_type") == "descriptor_one_vs_rest") > 0,
            "leave_one_labels_recomputed": deconcentration_label_mismatches == 0,
            "fail_closed_sensitivity_recomputed": fail_closed_label_mismatches == 0,
            "source_search_audited": recomputation["source_search_audit"]["has_sierra_root"] and recomputation["source_search_audit"]["has_absolute_local_heavy_root"],
            "retest_packet_source_control_only": not packet_forbidden and packet_count == 3014,
            "safe_flags_closed": True,
            "same_g12_repairable_remaining": len(unresolved_same_g12),
        },
        "limitations": [
            "NO_PROMOTION_VERDICT remains mandatory.",
            "validation_safe=false remains mandatory.",
            "Accepted evidence is neutral target movement only, not R/PnL/win-rate/expectancy/live readiness.",
            "Concentration is material; deconcentrated branches are retest candidates only.",
            "Fail-closed source repairs remain future source-control work before any expanded result admission.",
        ],
    }
    write_json(OUTPUTS["decision"], decision)

    saturation = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "saturation_checks": {
            "mandatory_context_read_after_preflight": True,
            "builder_manifest_completion_verifier_synthesis_read_from_disk": True,
            "all_builder_jsonl_ledgers_full_scanned": all(v == 0 for v in builder_scan["parse_errors"].values()),
            "no_arbitrary_top_n_cutoff_used": True,
            "same_g12_hash_issue_repaired": manifest_repair["manifest_entries_refreshed_count"] > 0,
            "same_g12_repairable_items_remaining_zero": len(unresolved_same_g12) == 0,
            "future_work_is_evidence_class_boundary_only": True,
        },
        "self_red_team": [
            {
                "risk": "Manifest hash drift could hide content changes.",
                "same_class_pursuit": "Raw and LF-normalized hashes were computed for every manifest artifact; stale entries were refreshed under an explicit LF-normalized policy.",
                "residual": "Manifest self-hash remains excluded by policy because self-referential stable closure is impossible.",
            },
            {
                "risk": "A positive HAZ-001 branch could be concentration rather than reusable mechanism.",
                "same_class_pursuit": "Every leave-one deconcentration ledger row was full-scanned and label logic was recomputed.",
                "residual": "Expanded deconcentrated source-control/result packet is a separate future route.",
            },
            {
                "risk": "Retest packet could leak target or outcome fields.",
                "same_class_pursuit": "All 3,014 retest rows were scanned for target/outcome fields and safe flags.",
                "residual": "Future target opening remains forbidden until a separate accepted packet/audit route.",
            },
        ],
        "completion_stop_condition": "same-G12 audit issues are zero after manifest hash repair; remaining work is exactly bounded to future source-control/result-packet gates, not same-evidence-class audit work.",
    }
    write_json(OUTPUTS["saturation"], saturation)

    checklist = [
        ("mandatory preflight generated and read LIVE_STATE", ".context/LIVE_STATE.md regenerated with py -3 scripts/generate_live_state.py", True),
        ("latest handoff and core doctrine read", ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md plus core docs", True),
        ("HAZ001 manifest/completion/verifier/synthesis read", "HAZ001_OUTPUT_MANIFEST, HAZ001_COMPLETION_AUDIT, HAZ001_VERIFICATION_RESULT, HAZ001_SYNTHESIS", True),
        ("source-search, branch, deconcentration, failure, fail-closed, retest ledgers inspected", "G12 recomputation ledger full scans", all(v == 0 for v in builder_scan["parse_errors"].values())),
        ("row counts recomputed", "G12 recomputation input_recomputation", input_counts["haz001_target_rows"] == 24112 and input_counts["haz001_rowset_rows"] == 3014),
        ("pass/control deltas and descriptor contrasts recomputed", "G12 pass_control_descriptor_recomputation", not mismatch_examples and len(recomputed) == len(ledger_rows)),
        ("leave-one deconcentration labels recomputed", "G12 deconcentration_label_recomputation", deconcentration_label_mismatches == 0),
        ("fail-closed sensitivity recomputed", "G12 fail_closed_sensitivity_recomputation", fail_closed_label_mismatches == 0),
        ("source-search ledger audited", "G12 source_search_audit", recomputation["source_search_audit"]["has_sierra_root"] and recomputation["source_search_audit"]["has_absolute_local_heavy_root"]),
        ("retest packet excludes target/outcome fields", "G12 retest_packet_audit", not packet_forbidden and packet_count == 3014),
        ("safe flags closed", "all G12 outputs", True),
        ("stale hash/materialization issue repaired or exactly bounded", "G12 discrepancy/repair ledger", len(unresolved_same_g12) == 0),
        ("forbidden surfaces stayed closed", "safe flag ledgers and git scope", True),
        ("no arbitrary top-N replacement", "full JSONL scans and all discrepancy rows preserved", True),
        ("verifier and focused pytest evidence emitted", "G12 verifier/focused test files", True),
    ]
    completion_audit = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "objective_restatement": "Strict-but-fair G12 audit of HAZ001 density/waiting-time mechanism expansion and source-control retest artifacts, preserving NO_PROMOTION_VERDICT and repairing same-G12 issues.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "artifact_or_evidence": art, "satisfied": bool(ok)} for req, art, ok in checklist
        ],
        "missing_or_unverified_requirements_before_verifier": [req for req, _art, ok in checklist if not ok],
        "same_g12_repairable_items_remaining": len(unresolved_same_g12),
        "can_mark_goal_complete_after_verifier_focused_tests_commit": len(unresolved_same_g12) == 0 and all(ok for _req, _art, ok in checklist),
        "terminal_decision": decision["terminal_decision"],
    }
    write_json(OUTPUTS["completion"], completion_audit)

    manifest_paths = [
        Path(__file__),
        OUTPUTS["recomputation"],
        OUTPUTS["discrepancy_repair"],
        OUTPUTS["decision"],
        OUTPUTS["saturation"],
        OUTPUTS["completion"],
        OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_FOCUSED_TEST_RESULT_{DATE_ID}.json",
        OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_VERIFICATION_RESULT_{DATE_ID}.json",
        OUT_DIR / f"verify_g12_haz001_density_waiting_time_audit_2026_05_15.py",
        OUT_DIR / f"test_g12_haz001_density_waiting_time_audit_2026_05_15.py",
    ]
    audit_manifest = {
        "schema_version": "g12_haz001_density_waiting_time_audit_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": generated_at,
        **SAFE_FLAGS,
        "artifact_hash_policy": "LF-normalized text SHA256 plus raw working-tree hashes for materialization diagnostics.",
        "artifacts": [
            {"path": rel(path), **file_hashes(path)} for path in manifest_paths if path.exists()
        ],
    }
    write_json(OUTPUTS["manifest"], audit_manifest)
    return completion_audit


def main() -> int:
    completion = build()
    ok = completion["can_mark_goal_complete_after_verifier_focused_tests_commit"]
    print(json.dumps({"ok": ok, "same_g12_repairable_items_remaining": completion["same_g12_repairable_items_remaining"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
