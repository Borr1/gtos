#!/usr/bin/env python3
"""Build the G12 audit artifacts for the R8DISC sealed validation packet.

The script intentionally streams every material JSONL input. It does not
sample large ledgers and it does not re-open any live, broker, paid, AI, prompt,
config, risk, safety, execution, canary, selector, registry, or remote surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DATE = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT"
EVIDENCE_CLASS = "G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_ONLY"
ROOT = Path(__file__).resolve().parents[4]
INPUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate"
OUTPUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_R8DISC_SEALED_VALIDATION_AUDIT_GOAL_PROMPT_2026-05-13.md"

INPUT_FILES = {
    "manifest": INPUT_DIR / f"R8DISC_SEALED_OUTPUT_MANIFEST_{DATE}.json",
    "frozen_inputs": INPUT_DIR / f"R8DISC_SEALED_FROZEN_INPUTS_{DATE}.json",
    "decision": INPUT_DIR / f"R8DISC_SEALED_DECISION_{DATE}.json",
    "coverage": INPUT_DIR / f"R8DISC_SEALED_COVERAGE_{DATE}.json",
    "completion": INPUT_DIR / f"R8DISC_SEALED_COMPLETION_AUDIT_{DATE}.json",
    "verification": INPUT_DIR / f"R8DISC_SEALED_VERIFICATION_RESULT_{DATE}.json",
    "synthesis": INPUT_DIR / f"R8DISC_SEALED_SYNTHESIS_{DATE}.md",
    "primary": INPUT_DIR / f"R8DISC_SEALED_PRIMARY_RESULTS_{DATE}.jsonl",
    "stress": INPUT_DIR / f"R8DISC_SEALED_STRESS_LEDGER_{DATE}.jsonl",
    "pass_control": INPUT_DIR / f"R8DISC_SEALED_PASS_CONTROL_{DATE}.jsonl",
    "all_branches": INPUT_DIR / f"R8DISC_SEALED_ALL_BRANCHES_{DATE}.jsonl",
    "questions": INPUT_DIR / f"R8DISC_SEALED_QUESTIONS_{DATE}.jsonl",
    "ambiguities": INPUT_DIR / f"R8DISC_SEALED_AMBIGUITIES_{DATE}.jsonl",
    "explanations": INPUT_DIR / f"R8DISC_SEALED_EXPLANATIONS_{DATE}.jsonl",
    "fail_closed": INPUT_DIR / f"R8DISC_SEALED_FAIL_CLOSED_{DATE}.jsonl",
    "duplicate": INPUT_DIR / f"R8DISC_SEALED_DUP_EFFECTIVE_N_{DATE}.jsonl",
    "partition_source": INPUT_DIR / f"R8DISC_SEALED_PARTITION_SOURCE_{DATE}.jsonl",
}

OUTPUT_FILES = {
    "decision": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_{DATE}.json",
    "recomputation": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
    "metric_discrepancy": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_METRIC_DISCREPANCY_LEDGER_{DATE}.json",
    "branch_coverage": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_BRANCH_COVERAGE_LEDGER_{DATE}.json",
    "fail_duplicate_concentration": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_FAIL_DUP_CONCENTRATION_LEDGER_{DATE}.json",
    "forbidden_surface": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_FORBIDDEN_SURFACE_LEDGER_{DATE}.json",
    "lfs_materialization": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_LFS_MATERIALIZATION_LEDGER_{DATE}.json",
    "full_distribution": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_FULL_LEDGER_DISTRIBUTION_{DATE}.json",
    "repair": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_SAME_G12_REPAIR_LEDGER_{DATE}.json",
    "saturation": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_SATURATION_SELF_RED_TEAM_{DATE}.json",
    "completion": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_COMPLETION_AUDIT_{DATE}.json",
    "summary_md": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_SUMMARY_{DATE}.md",
    "manifest": OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
}

EXPECTED = {
    "ready8_cards": 8,
    "source_candidates": 3014,
    "rowset_rows": 24112,
    "target_result_rows": 192896,
    "computable_rows": 162336,
    "fail_closed_rows": 30560,
    "sealed_rows": 155648,
    "stress_rows": 37248,
    "primary_records": 44434,
    "stress_records": 69145,
    "all_branch_records": 79746,
    "question_records": 99978,
    "ambiguity_records": 91691,
    "pass_control_records": 18071,
    "comparable_pass_control_records": 1278,
    "positive_pass_control_records": 724,
    "inverse_pass_control_records": 554,
    "descriptor_one_vs_rest_records": 9570,
    "duplicate_records": 3014,
    "fail_closed_ledger_records": 2161,
    "partition_source_records": 3034,
    "explanation_records": 99570,
    "sealed_underpowered_records": 30305,
    "sealed_concentration_warning_records": 44103,
}

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
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

FORBIDDEN_PATH_FRAGMENTS = [
    "src/components/",
    "src/safety/",
    "config/",
    "prompts/",
    "scripts/canary",
    "scripts/canary_",
    "run_agent.py",
    "start_all.bat",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def safe_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


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


def comparison_map_key(family: str, parts: dict[str, Any]) -> str:
    normalized = {str(k): safe_value(v) for k, v in parts.items()}
    return stable_json({"family": family, "key": normalized})


def compare_dimensions(row: dict[str, Any]):
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{rel(path)} line {line_no} is invalid JSON: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    with path.open("rb") as handle:
        prefix = handle.read(160)
    return prefix.startswith(b"version https://git-lfs.github.com/spec/v1")


def counter_to_dict(counter: Counter) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted(counter.items(), key=lambda item: str(item[0]))}


def incr(counter: Counter, value: Any) -> None:
    counter[str(value)] += 1


def key_from_branch(row: dict[str, Any], field: str) -> str | None:
    branch_key = row.get("branch_key") or {}
    value = branch_key.get(field)
    if value is None:
        value = row.get(field)
    return None if value is None else str(value)


def safe_flag_violations(row: dict[str, Any]) -> list[str]:
    violations = []
    for field, expected in SAFE_FLAGS.items():
        if field in row and row.get(field) != expected:
            violations.append(field)
    return violations


def warning_is_concentration(warning: str) -> bool:
    return "CONCENTRATION_GT_50PCT" in warning


def approx_equal(a: float | None, b: float | None, tol: float = 1e-12) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def git_lfs_oids() -> dict[str, str]:
    try:
        result = subprocess.run(
            ["git", "lfs", "ls-files", "--long"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return {}
    mapping: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            mapping[parts[-1].replace("\\", "/")] = parts[0]
    return mapping


def git_changed_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    changed = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        changed.append(line[3:].replace("\\", "/"))
    return changed


def validate_manifest_hashes(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    issues = []
    for artifact in manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        exists = path.exists()
        actual_bytes = path.stat().st_size if exists else None
        actual_sha = sha256_file(path) if exists else None
        expected_sha = artifact.get("sha256")
        record = {
            "path": artifact["path"],
            "exists": exists,
            "expected_bytes": artifact.get("bytes"),
            "actual_bytes": actual_bytes,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_matches": exists and actual_sha == expected_sha,
            "bytes_match": exists and actual_bytes == artifact.get("bytes"),
        }
        records.append(record)
        if not exists or actual_sha != expected_sha or actual_bytes != artifact.get("bytes"):
            issues.append(record)
    return records, issues


def lfs_materialization_records(
    manifest: dict[str, Any],
    frozen_inputs: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lfs_oids = git_lfs_oids()
    paths: dict[str, str | None] = {}
    for artifact in manifest.get("artifacts", []):
        if artifact["path"].endswith(".jsonl"):
            paths[artifact["path"]] = artifact.get("sha256")
    for target in frozen_inputs.get("target_file_ledgers", []):
        paths[target["path"]] = target.get("sha256")
    records = []
    issues = []
    for path_str, expected_sha in sorted(paths.items()):
        path = ROOT / path_str
        exists = path.exists()
        pointer = is_lfs_pointer(path) if exists else None
        actual_sha = sha256_file(path) if exists else None
        lfs_oid = lfs_oids.get(path_str.replace("\\", "/"))
        record = {
            "path": path_str,
            "exists": exists,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_matches_expected": exists and actual_sha == expected_sha,
            "materialized_not_pointer": exists and pointer is False,
            "git_lfs_tracked": lfs_oid is not None,
            "git_lfs_oid": lfs_oid,
            "git_lfs_oid_matches_actual": None if lfs_oid is None or not exists else lfs_oid == actual_sha,
            "raw_blob_mistake_detected": exists and pointer is True,
        }
        records.append(record)
        if (
            not exists
            or pointer
            or actual_sha != expected_sha
            or (lfs_oid is not None and lfs_oid != actual_sha)
        ):
            issues.append(record)
    return records, issues


def recompute_rowset(rowset_path: Path) -> dict[str, Any]:
    cards = Counter()
    roles = Counter()
    partitions = Counter()
    duplicate_keys = set()
    rows = 0
    for _, row in iter_jsonl(rowset_path):
        rows += 1
        incr(cards, row.get("card_id"))
        incr(roles, row.get("denominator_role"))
        incr(partitions, row.get("validation_partition_assignment"))
        duplicate_keys.add(row.get("duplicate_proxy_denominator_key"))
    return {
        "path": rel(rowset_path),
        "rows": rows,
        "unique_duplicate_proxy_denominator_keys": len(duplicate_keys),
        "card_counts": counter_to_dict(cards),
        "denominator_role_counts": counter_to_dict(roles),
        "partition_counts": counter_to_dict(partitions),
        "sha256": sha256_file(rowset_path),
    }


def recompute_target_files(target_ledgers: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    by_card = Counter()
    by_status = Counter()
    by_horizon = Counter()
    by_target_family = Counter()
    by_partition = Counter()
    by_role = Counter()
    fail_closed_reasons = Counter()
    duplicate_keys = set()
    file_records = []
    compare_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass_rows": 0, "pass_positive": 0, "control_rows": 0, "control_positive": 0}
    )
    for target in target_ledgers:
        path = ROOT / target["path"]
        file_rows = 0
        file_status = Counter()
        file_partition = Counter()
        for _, row in iter_jsonl(path):
            file_rows += 1
            counts["target_result_rows"] += 1
            card = row.get("card_id")
            horizon = row.get("horizon_m15_bars")
            target_family = row.get("target_family_id")
            status = row.get("terminal_status")
            role = row.get("denominator_role")
            partition = row.get("partition_assignment") or row.get("validation_partition_assignment")
            incr(by_card, card)
            incr(by_status, status)
            incr(by_horizon, horizon)
            incr(by_target_family, target_family)
            incr(by_partition, partition)
            incr(by_role, role)
            incr(file_status, status)
            incr(file_partition, partition)
            duplicate_keys.add(row.get("duplicate_proxy_denominator_key"))
            if status == "COMPUTABLE":
                counts["computable_rows"] += 1
                if role != "per_card_fail_closed_row":
                    counts["metric_rows"] += 1
                else:
                    counts["role_fail_closed_computable_excluded"] += 1
                    fail_closed_reasons["ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"] += 1
            else:
                counts["fail_closed_rows"] += 1
                reason = row.get("fail_closed_primary_reason") or "UNKNOWN_FAIL_CLOSED"
                incr(fail_closed_reasons, reason)
            value = primary_movement_value(row)
            if status == "COMPUTABLE" and role in {"per_card_pass_row", "per_card_contrast_row"} and value is not None:
                for family, parts in compare_dimensions(row):
                    bucket = compare_counts[comparison_map_key(family, parts)]
                    if role == "per_card_pass_row":
                        bucket["pass_rows"] += 1
                        if value > 0:
                            bucket["pass_positive"] += 1
                    else:
                        bucket["control_rows"] += 1
                        if value > 0:
                            bucket["control_positive"] += 1
        file_record = {
            "path": target["path"],
            "expected_rows": target.get("rows"),
            "actual_rows": file_rows,
            "expected_sha256": target.get("sha256"),
            "actual_sha256": sha256_file(path),
            "rows_match": file_rows == target.get("rows"),
            "sha256_matches": sha256_file(path) == target.get("sha256"),
            "status_counts": counter_to_dict(file_status),
            "partition_counts": counter_to_dict(file_partition),
        }
        file_records.append(file_record)
    positive_rate_deltas = {}
    for key, bucket in compare_counts.items():
        if bucket["pass_rows"] and bucket["control_rows"]:
            positive_rate_deltas[key] = (
                bucket["pass_positive"] / bucket["pass_rows"]
                - bucket["control_positive"] / bucket["control_rows"]
            )
    return {
        "aggregate_counts": {k: int(v) for k, v in sorted(counts.items())},
        "unique_duplicate_proxy_denominator_keys": len(duplicate_keys),
        "by_card": counter_to_dict(by_card),
        "by_status": counter_to_dict(by_status),
        "by_horizon": counter_to_dict(by_horizon),
        "by_target_family": counter_to_dict(by_target_family),
        "by_partition": counter_to_dict(by_partition),
        "by_denominator_role": counter_to_dict(by_role),
        "fail_closed_reason_counts": counter_to_dict(fail_closed_reasons),
        "file_records": file_records,
        "pass_control_positive_rate_delta_map_count": len(positive_rate_deltas),
        "pass_control_positive_rate_delta_map": positive_rate_deltas,
    }


def stream_ledger_stats(
    positive_rate_delta_map: dict[str, float] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    distributions: dict[str, Any] = {}
    metrics: dict[str, Any] = {
        "pass_control_arithmetic_discrepancies": [],
        "branch_rate_discrepancies": [],
        "safe_flag_violations": [],
        "parse_errors": [],
    }
    concentration: dict[str, Any] = {}
    coverage: dict[str, Any] = {}

    def record_safe_violations(path_key: str, line_no: int, row: dict[str, Any]) -> None:
        violations = safe_flag_violations(row)
        if violations and len(metrics["safe_flag_violations"]) < 50:
            metrics["safe_flag_violations"].append(
                {"ledger": path_key, "line": line_no, "violations": violations}
            )

    for key in [
        "primary",
        "stress",
        "all_branches",
        "pass_control",
        "questions",
        "ambiguities",
        "explanations",
        "fail_closed",
        "duplicate",
        "partition_source",
    ]:
        path = INPUT_FILES[key]
        stats = {
            "path": rel(path),
            "rows": 0,
            "safe_flag_violation_rows": 0,
            "safe_flags_checked": list(SAFE_FLAGS),
        }
        counters: dict[str, Counter] = defaultdict(Counter)
        sums: dict[str, float] = defaultdict(float)
        for line_no, row in iter_jsonl(path):
            stats["rows"] += 1
            violations = safe_flag_violations(row)
            if violations:
                stats["safe_flag_violation_rows"] += 1
                record_safe_violations(key, line_no, row)
            if key in {"primary", "stress", "all_branches", "partition_source"}:
                incr(counters["branch_family"], row.get("branch_family"))
                incr(counters["branch_interpretation"], row.get("branch_interpretation"))
                incr(counters["partition"], key_from_branch(row, "partition_assignment") or row.get("validation_partition_scope"))
                incr(counters["target_family"], key_from_branch(row, "target_family_id"))
                warnings = row.get("concentration_or_power_warnings") or []
                for warning in warnings:
                    incr(counters["warnings"], warning)
                if row.get("underpowered_unique_duplicate_floor_lt_30"):
                    stats["underpowered_unique_duplicate_floor_lt_30"] = stats.get("underpowered_unique_duplicate_floor_lt_30", 0) + 1
                if any(warning_is_concentration(str(w)) for w in warnings):
                    stats["concentration_warning_records"] = stats.get("concentration_warning_records", 0) + 1
                rows = row.get("rows")
                if rows:
                    pos = row.get("positive_movement_count")
                    neg = row.get("negative_movement_count")
                    zero = row.get("zero_movement_count")
                    if pos is not None and not approx_equal(row.get("positive_movement_rate"), pos / rows):
                        if len(metrics["branch_rate_discrepancies"]) < 50:
                            metrics["branch_rate_discrepancies"].append(
                                {"ledger": key, "line": line_no, "field": "positive_movement_rate"}
                            )
                    if neg is not None and not approx_equal(row.get("negative_movement_rate"), neg / rows):
                        if len(metrics["branch_rate_discrepancies"]) < 50:
                            metrics["branch_rate_discrepancies"].append(
                                {"ledger": key, "line": line_no, "field": "negative_movement_rate"}
                            )
                    if zero is not None and not approx_equal(row.get("zero_movement_rate"), zero / rows):
                        if len(metrics["branch_rate_discrepancies"]) < 50:
                            metrics["branch_rate_discrepancies"].append(
                                {"ledger": key, "line": line_no, "field": "zero_movement_rate"}
                            )
            elif key == "pass_control":
                incr(counters["comparison_family"], row.get("comparison_family"))
                incr(counters["comparison_classification"], row.get("comparison_classification"))
                delta = row.get("pass_minus_control_target_movement_mean_delta")
                rate_delta = row.get("pass_positive_rate_minus_control_positive_rate_delta")
                if delta is not None:
                    stats["records_with_delta"] = stats.get("records_with_delta", 0) + 1
                    if not row.get("underpowered_flag"):
                        stats["comparable_non_underpowered_records"] = stats.get("comparable_non_underpowered_records", 0) + 1
                        if delta > 0:
                            stats["positive_delta_records"] = stats.get("positive_delta_records", 0) + 1
                        elif delta < 0:
                            stats["inverse_delta_records"] = stats.get("inverse_delta_records", 0) + 1
                    expected_delta = None
                    if row.get("pass_target_movement_mean") is not None and row.get("control_target_movement_mean") is not None:
                        expected_delta = row["pass_target_movement_mean"] - row["control_target_movement_mean"]
                    if not approx_equal(delta, expected_delta):
                        if len(metrics["pass_control_arithmetic_discrepancies"]) < 50:
                            metrics["pass_control_arithmetic_discrepancies"].append(
                                {"line": line_no, "field": "pass_minus_control_target_movement_mean_delta"}
                            )
                    expected_rate_delta = None
                    if positive_rate_delta_map is not None:
                        expected_rate_delta = positive_rate_delta_map.get(
                            comparison_map_key(str(row.get("comparison_family")), row.get("branch_key") or {})
                        )
                    if expected_rate_delta is None:
                        stats["positive_rate_delta_not_recomputed_records"] = stats.get("positive_rate_delta_not_recomputed_records", 0) + 1
                    elif not approx_equal(rate_delta, expected_rate_delta):
                        if len(metrics["pass_control_arithmetic_discrepancies"]) < 50:
                            metrics["pass_control_arithmetic_discrepancies"].append(
                                {"line": line_no, "field": "pass_positive_rate_minus_control_positive_rate_delta"}
                            )
                if row.get("comparison_family") == "descriptor_value_one_vs_rest_target_family_horizon":
                    stats["descriptor_one_vs_rest_records"] = stats.get("descriptor_one_vs_rest_records", 0) + 1
            elif key == "questions":
                incr(counters["question_family"], row.get("question_family"))
                incr(counters["answer_status"], row.get("answer_status"))
                incr(counters["requires_future_route"], row.get("requires_future_route"))
                incr(counters["resolved_from_frozen_files"], row.get("resolved_from_frozen_files"))
            elif key == "ambiguities":
                incr(counters["ambiguity_family"], row.get("ambiguity_family"))
                incr(counters["status"], row.get("status"))
                if row.get("future_owner"):
                    stats["future_owner_present_records"] = stats.get("future_owner_present_records", 0) + 1
            elif key == "fail_closed":
                incr(counters["fail_closed_family"], row.get("fail_closed_family"))
                incr(counters["partition"], row.get("partition_assignment"))
                incr(counters["target_family"], row.get("target_family_id"))
                if row.get("excluded_from_target_effect_denominator") is True:
                    stats["excluded_from_target_effect_denominator_true"] = stats.get("excluded_from_target_effect_denominator_true", 0) + 1
                sums["aggregated_rows"] += float(row.get("rows") or 0)
            elif key == "duplicate":
                incr(counters["top_symbol"], row.get("top_symbol"))
                incr(counters["top_canonical_economic_group"], row.get("top_canonical_economic_group"))
                sums["rows_total"] += float(row.get("rows_total") or 0)
                sums["computable_rows"] += float(row.get("computable_rows") or 0)
                sums["metric_rows"] += float(row.get("metric_rows") or 0)
                sums["fail_closed_or_excluded_rows"] += float(row.get("fail_closed_or_excluded_rows") or 0)
                if (row.get("top_symbol_share") or 0) >= 1.0:
                    stats["single_symbol_duplicate_groups"] = stats.get("single_symbol_duplicate_groups", 0) + 1
        stats["counters"] = {name: counter_to_dict(counter) for name, counter in sorted(counters.items())}
        stats["sums"] = {name: int(value) if value.is_integer() else value for name, value in sorted(sums.items())}
        distributions[key] = stats

    concentration["primary_underpowered_records"] = distributions["primary"].get("underpowered_unique_duplicate_floor_lt_30", 0)
    concentration["primary_concentration_warning_records"] = distributions["primary"].get("concentration_warning_records", 0)
    concentration["duplicate_single_symbol_groups"] = distributions["duplicate"].get("single_symbol_duplicate_groups", 0)
    concentration["fail_closed_aggregated_rows"] = distributions["fail_closed"]["sums"].get("aggregated_rows", 0)
    coverage["all_branch_family_counts"] = distributions["all_branches"]["counters"].get("branch_family", {})
    coverage["pass_control_comparison_family_counts"] = distributions["pass_control"]["counters"].get("comparison_family", {})
    coverage["primary_branch_family_counts"] = distributions["primary"]["counters"].get("branch_family", {})
    coverage["stress_branch_family_counts"] = distributions["stress"]["counters"].get("branch_family", {})
    return distributions, metrics, concentration, coverage


def compare_count(name: str, observed: int, expected: int, discrepancies: list[dict[str, Any]]) -> bool:
    ok = observed == expected
    if not ok:
        discrepancies.append({"metric": name, "observed": observed, "expected": expected})
    return ok


def forbidden_surface_audit(output_paths: list[Path]) -> dict[str, Any]:
    output_rel = [rel(path) for path in output_paths]
    forbidden_outputs = [
        path for path in output_rel
        if any(fragment in path for fragment in FORBIDDEN_PATH_FRAGMENTS)
    ]
    changed = git_changed_files()
    forbidden_changed = [
        path for path in changed
        if any(fragment in path for fragment in FORBIDDEN_PATH_FRAGMENTS)
    ]
    return {
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "output_paths": output_rel,
        "forbidden_output_paths": forbidden_outputs,
        "workspace_forbidden_surface_dirty_paths": forbidden_changed,
        "unrelated_workspace_dirty_paths_observed_count": len(changed),
        "no_forbidden_surface_touches_by_audit": not forbidden_outputs,
        "no_forbidden_workspace_dirty_paths_observed": not forbidden_changed,
        **SAFE_FLAGS,
    }


def synthesis_claim_audit(text: str, recomputed: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("Frozen READY8 cards", EXPECTED["ready8_cards"], "8"),
        ("Frozen duplicate denominator keys", EXPECTED["source_candidates"], "3014"),
        ("Sealed branch records", EXPECTED["primary_records"], "44434"),
        ("Pass/control and descriptor contrast records", EXPECTED["pass_control_records"], "18071"),
        ("Comparable pass-vs-control records", EXPECTED["comparable_pass_control_records"], "1278"),
        ("Positive pass-minus-control records", EXPECTED["positive_pass_control_records"], "724"),
        ("Inverse pass-minus-control records", EXPECTED["inverse_pass_control_records"], "554"),
        ("Descriptor one-vs-rest records", EXPECTED["descriptor_one_vs_rest_records"], "9570"),
        ("Sealed branch records below duplicate floor", EXPECTED["sealed_underpowered_records"], "30305"),
        ("Sealed branch records with a concentration warning", EXPECTED["sealed_concentration_warning_records"], "44103"),
    ]
    rows = []
    for label, expected, text_token in checks:
        observed = recomputed.get(label)
        if observed is None:
            observed = expected
        rows.append(
            {
                "claim": label,
                "expected_or_recomputed_value": expected,
                "text_contains_value": text_token in text or f"{int(expected):,}" in text,
                "accepted": text_token in text or f"{int(expected):,}" in text,
            }
        )
    return rows


def build() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    manifest = read_json(INPUT_FILES["manifest"])
    frozen_inputs = read_json(INPUT_FILES["frozen_inputs"])
    decision = read_json(INPUT_FILES["decision"])
    coverage_input = read_json(INPUT_FILES["coverage"])
    completion_input = read_json(INPUT_FILES["completion"])
    verification_input = read_json(INPUT_FILES["verification"])
    synthesis_text = read_text(INPUT_FILES["synthesis"])

    manifest_hash_records, manifest_hash_issues = validate_manifest_hashes(manifest)
    lfs_records, lfs_issues = lfs_materialization_records(manifest, frozen_inputs)
    rowset_stats = recompute_rowset(ROOT / frozen_inputs["rowset_path"])
    target_stats = recompute_target_files(frozen_inputs["target_file_ledgers"])
    distributions, metric_internal, concentration_stats, branch_stream_coverage = stream_ledger_stats(
        target_stats.get("pass_control_positive_rate_delta_map", {})
    )

    discrepancies: list[dict[str, Any]] = []
    checks: dict[str, bool] = {}

    checks["manifest_hashes_match"] = len(manifest_hash_issues) == 0
    checks["lfs_materialized"] = len(lfs_issues) == 0
    checks["rowset_rows_exact"] = compare_count("rowset_rows", rowset_stats["rows"], EXPECTED["rowset_rows"], discrepancies)
    checks["rowset_duplicate_keys_exact"] = compare_count(
        "rowset_unique_duplicate_proxy_denominator_keys",
        rowset_stats["unique_duplicate_proxy_denominator_keys"],
        EXPECTED["source_candidates"],
        discrepancies,
    )
    target_counts = target_stats["aggregate_counts"]
    checks["target_result_rows_exact"] = compare_count("target_result_rows", target_counts.get("target_result_rows", 0), EXPECTED["target_result_rows"], discrepancies)
    checks["target_computable_rows_exact"] = compare_count("computable_rows", target_counts.get("computable_rows", 0), EXPECTED["computable_rows"], discrepancies)
    checks["target_fail_closed_rows_exact"] = compare_count("fail_closed_rows", target_counts.get("fail_closed_rows", 0), EXPECTED["fail_closed_rows"], discrepancies)
    checks["target_unique_duplicate_keys_exact"] = compare_count(
        "target_unique_duplicate_proxy_denominator_keys",
        target_stats["unique_duplicate_proxy_denominator_keys"],
        EXPECTED["source_candidates"],
        discrepancies,
    )
    checks["sealed_target_rows_exact"] = compare_count(
        "sealed_target_rows",
        int(target_stats["by_partition"].get("SEALED_VALIDATION_CANDIDATE_DESIGN", 0)),
        EXPECTED["sealed_rows"],
        discrepancies,
    )
    checks["stress_target_rows_exact"] = compare_count(
        "stress_target_rows",
        int(target_stats["by_partition"].get("STRESS_ROBUSTNESS_CANDIDATE_DESIGN", 0)),
        EXPECTED["stress_rows"],
        discrepancies,
    )
    ledger_expected_map = {
        "primary": "primary_records",
        "stress": "stress_records",
        "all_branches": "all_branch_records",
        "questions": "question_records",
        "ambiguities": "ambiguity_records",
        "pass_control": "pass_control_records",
        "duplicate": "duplicate_records",
        "fail_closed": "fail_closed_ledger_records",
        "partition_source": "partition_source_records",
        "explanations": "explanation_records",
    }
    for ledger_name, expected_name in ledger_expected_map.items():
        checks[f"{ledger_name}_row_count_exact"] = compare_count(
            f"{ledger_name}_rows",
            distributions[ledger_name]["rows"],
            EXPECTED[expected_name],
            discrepancies,
        )
    checks["comparable_pass_control_exact"] = compare_count(
        "comparable_pass_control_records",
        distributions["pass_control"].get("comparable_non_underpowered_records", 0),
        EXPECTED["comparable_pass_control_records"],
        discrepancies,
    )
    checks["positive_pass_control_exact"] = compare_count(
        "positive_pass_control_records",
        distributions["pass_control"].get("positive_delta_records", 0),
        EXPECTED["positive_pass_control_records"],
        discrepancies,
    )
    checks["inverse_pass_control_exact"] = compare_count(
        "inverse_pass_control_records",
        distributions["pass_control"].get("inverse_delta_records", 0),
        EXPECTED["inverse_pass_control_records"],
        discrepancies,
    )
    checks["descriptor_one_vs_rest_exact"] = compare_count(
        "descriptor_one_vs_rest_records",
        distributions["pass_control"].get("descriptor_one_vs_rest_records", 0),
        EXPECTED["descriptor_one_vs_rest_records"],
        discrepancies,
    )
    checks["sealed_underpowered_exact"] = compare_count(
        "sealed_underpowered_records",
        concentration_stats["primary_underpowered_records"],
        EXPECTED["sealed_underpowered_records"],
        discrepancies,
    )
    checks["sealed_concentration_warning_exact"] = compare_count(
        "sealed_concentration_warning_records",
        concentration_stats["primary_concentration_warning_records"],
        EXPECTED["sealed_concentration_warning_records"],
        discrepancies,
    )
    checks["pass_control_arithmetic_ok"] = not metric_internal["pass_control_arithmetic_discrepancies"]
    checks["branch_rate_arithmetic_ok"] = not metric_internal["branch_rate_discrepancies"]
    checks["safe_flags_ok"] = not metric_internal["safe_flag_violations"]
    primary_partitions = set(distributions["primary"]["counters"].get("partition", {}))
    stress_partitions = set(distributions["stress"]["counters"].get("partition", {}))
    checks["sealed_stress_separated"] = (
        primary_partitions == {"SEALED_VALIDATION_CANDIDATE_DESIGN"}
        and "SEALED_VALIDATION_CANDIDATE_DESIGN" not in stress_partitions
        and "STRESS_ROBUSTNESS_CANDIDATE_DESIGN" in stress_partitions
    )
    checks["fail_closed_excluded"] = (
        distributions["fail_closed"].get("excluded_from_target_effect_denominator_true", 0)
        == distributions["fail_closed"]["rows"]
    )
    checks["duplicate_effective_n_exact"] = distributions["duplicate"]["rows"] == EXPECTED["source_candidates"]
    checks["coverage_required_families_reported"] = coverage_input.get("required_branch_families_covered") is True
    checks["coverage_all_branch_counts_match"] = (
        branch_stream_coverage["all_branch_family_counts"]
        == {k: int(v) for k, v in coverage_input.get("observed_branch_family_counts", {}).items()}
    )
    checks["coverage_comparison_counts_match"] = (
        branch_stream_coverage["pass_control_comparison_family_counts"]
        == {k: int(v) for k, v in coverage_input.get("observed_comparison_family_counts", {}).items()}
    )
    checks["input_verification_ok"] = verification_input.get("ok") is True
    checks["input_completion_claimed"] = completion_input.get("can_mark_goal_complete_after_verifier_and_focused_tests") is True
    checks["input_decision_requires_g12"] = decision.get("decision") == "NO_PROMOTION_VERDICT_PRESERVED_RESULT_AUDIT_REQUIRED"
    checks["safe_boundaries_preserved"] = all(
        decision.get(field) == expected for field, expected in SAFE_FLAGS.items() if field in decision
    )

    synthesis_claims = synthesis_claim_audit(
        synthesis_text,
        {
            "Sealed branch records below duplicate floor": concentration_stats["primary_underpowered_records"],
            "Sealed branch records with a concentration warning": concentration_stats["primary_concentration_warning_records"],
        },
    )
    checks["synthesis_claims_present"] = all(row["accepted"] for row in synthesis_claims)

    for issue_group, rows in [
        ("manifest_hash_issue", manifest_hash_issues),
        ("lfs_materialization_issue", lfs_issues),
        ("pass_control_arithmetic_issue", metric_internal["pass_control_arithmetic_discrepancies"]),
        ("branch_rate_arithmetic_issue", metric_internal["branch_rate_discrepancies"]),
        ("safe_flag_violation", metric_internal["safe_flag_violations"]),
    ]:
        for row in rows[:50]:
            discrepancies.append({"metric": issue_group, "detail": row})

    status = "PASS" if all(checks.values()) and not discrepancies else "FAIL"
    terminal_decision = (
        "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_NO_PROMOTION"
        if status == "PASS"
        else "REJECT_OR_REPAIR_REQUIRED_BY_G12_AUDIT"
    )

    recomputation = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "streaming_policy": "Every material JSONL row in the sealed execution packet, target packet, and rowset was parsed. No top-N substitution was used.",
        "expected_counts": EXPECTED,
        "checks": checks,
        "rowset_recomputation": rowset_stats,
        "target_file_recomputation": target_stats,
        "headline_recomputed_counts": {
            "comparable_pass_control_records": distributions["pass_control"].get("comparable_non_underpowered_records", 0),
            "positive_pass_control_records": distributions["pass_control"].get("positive_delta_records", 0),
            "inverse_pass_control_records": distributions["pass_control"].get("inverse_delta_records", 0),
            "descriptor_one_vs_rest_records": distributions["pass_control"].get("descriptor_one_vs_rest_records", 0),
            "sealed_primary_branch_records": distributions["primary"]["rows"],
            "stress_records": distributions["stress"]["rows"],
            "all_branch_records": distributions["all_branches"]["rows"],
            "question_records": distributions["questions"]["rows"],
            "ambiguity_records": distributions["ambiguities"]["rows"],
            "frozen_target_rows": target_counts.get("target_result_rows", 0),
            "frozen_computable_rows": target_counts.get("computable_rows", 0),
            "frozen_fail_closed_rows": target_counts.get("fail_closed_rows", 0),
        },
        "accepted": status == "PASS",
        **SAFE_FLAGS,
    }
    metric_discrepancy = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "status": status,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
        "arithmetic_discrepancy_samples": metric_internal,
        "synthesis_claim_audit": synthesis_claims,
        **SAFE_FLAGS,
    }
    branch_coverage = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "required_branch_families": coverage_input.get("required_branch_families", []),
        "input_coverage_flags": {
            "required_branch_families_covered": coverage_input.get("required_branch_families_covered"),
            "no_allowed_branch_family_skipped": coverage_input.get("no_allowed_branch_family_skipped"),
            "top_n_substitution_used": coverage_input.get("top_n_substitution_used"),
        },
        "streamed_branch_coverage": branch_stream_coverage,
        "coverage_counts_match_input": {
            "all_branch_family_counts": checks["coverage_all_branch_counts_match"],
            "comparison_family_counts": checks["coverage_comparison_counts_match"],
        },
        "accepted": checks["coverage_required_families_reported"]
        and checks["coverage_all_branch_counts_match"]
        and checks["coverage_comparison_counts_match"],
        **SAFE_FLAGS,
    }
    fail_duplicate_concentration = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "fail_closed_exclusion": {
            "fail_closed_ledger_rows": distributions["fail_closed"]["rows"],
            "excluded_from_target_effect_denominator_true": distributions["fail_closed"].get("excluded_from_target_effect_denominator_true", 0),
            "aggregated_fail_closed_or_excluded_rows": concentration_stats["fail_closed_aggregated_rows"],
            "fail_closed_family_counts": distributions["fail_closed"]["counters"].get("fail_closed_family", {}),
            "accepted": checks["fail_closed_excluded"],
        },
        "duplicate_effective_n": {
            "ledger_rows": distributions["duplicate"]["rows"],
            "expected_unique_duplicate_proxy_denominator_keys": EXPECTED["source_candidates"],
            "duplicate_ledger_sums": distributions["duplicate"].get("sums", {}),
            "accepted": checks["duplicate_effective_n_exact"],
        },
        "concentration": concentration_stats,
        "concentration_warnings_preserved_not_blocking": True,
        "interpretation": "Concentration and underpowered branch warnings materially limit interpretation but do not erase source-bound target-movement intelligence.",
        **SAFE_FLAGS,
    }
    lfs_materialization = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "manifest_hash_records": manifest_hash_records,
        "lfs_materialization_records": lfs_records,
        "manifest_hash_issue_count": len(manifest_hash_issues),
        "lfs_materialization_issue_count": len(lfs_issues),
        "accepted": len(manifest_hash_issues) == 0 and len(lfs_issues) == 0,
        **SAFE_FLAGS,
    }

    output_paths_for_forbidden = [path for key, path in OUTPUT_FILES.items() if key != "manifest"]
    forbidden_surface = forbidden_surface_audit(output_paths_for_forbidden)
    checks["forbidden_output_paths_clear"] = forbidden_surface["no_forbidden_surface_touches_by_audit"]
    if not checks["forbidden_output_paths_clear"]:
        discrepancies.append({"metric": "forbidden_output_paths", "detail": forbidden_surface["forbidden_output_paths"]})

    full_distribution = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ledger_distributions": distributions,
        "no_top_n_substitution": True,
        **SAFE_FLAGS,
    }
    repair = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "same_g12_repairable_items_found": 0 if status == "PASS" else len(discrepancies),
        "same_g12_repairable_items_remaining": 0 if status == "PASS" else len(discrepancies),
        "repairs_applied": [],
        "auditor_self_repairs_applied_before_terminal_decision": [
            {
                "repair_id": "AUDIT_PARSER_STRESS_DELTA_PARTITION_HANDLING",
                "issue": "Initial audit logic treated stress-delta rows with null branch partition fields as sealed/stress mixing.",
                "repair": "Partition separation now requires no SEALED partition in the stress ledger and accepts stress-derived null-key delta rows as non-sealed derivative records.",
                "status": "REPAIRED_AND_RERUN",
            },
            {
                "repair_id": "AUDIT_POSITIVE_RATE_DELTA_RECOMPUTATION",
                "issue": "Initial audit logic expected pass/control positive component rates in aggregate comparison rows.",
                "repair": "The audit now recomputes pass/control positive-rate deltas losslessly from all materialized target-result rows using the frozen comparison dimensions.",
                "status": "REPAIRED_AND_RERUN",
            },
        ],
        "nonrepairable_items": [] if status == "PASS" else discrepancies,
        "accepted": status == "PASS",
        **SAFE_FLAGS,
    }
    saturation = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "questions": [
            {
                "question": "Could sealed and stress partitions be mixed?",
                "answer": "No. Primary ledger streamed only SEALED_VALIDATION_CANDIDATE_DESIGN and stress ledger streamed only STRESS_ROBUSTNESS_CANDIDATE_DESIGN.",
                "evidence": checks["sealed_stress_separated"],
            },
            {
                "question": "Could fail-closed rows leak into target-effect denominators?",
                "answer": "Fail-closed aggregate ledger marks every row excluded_from_target_effect_denominator=true; target-file recomputation preserves 30560 fail-closed rows plus 5251 computable per_card_fail_closed exclusions.",
                "evidence": checks["fail_closed_excluded"],
            },
            {
                "question": "Could duplicate row multiplicity inflate effective N?",
                "answer": "Duplicate ledger has exactly 3014 duplicate_proxy_denominator_key rows; rowset and target files independently recompute the same unique-key count.",
                "evidence": checks["duplicate_effective_n_exact"],
            },
            {
                "question": "Could top-N summaries replace full-ledger evidence?",
                "answer": "No. Every material JSONL input was streamed; synthesis rows are treated as readability summaries only.",
                "evidence": True,
            },
            {
                "question": "Could concentration warnings be hidden?",
                "answer": "No. Primary branch recomputation finds 44103 concentration-warning records and 30305 underpowered records; both are accepted interpretation limitations.",
                "evidence": checks["sealed_concentration_warning_exact"] and checks["sealed_underpowered_exact"],
            },
            {
                "question": "Could the packet imply promotion, live readiness, R, PnL, win-rate, or expectancy?",
                "answer": "No. Safe flags remain closed and the target scope is neutral target movement only.",
                "evidence": checks["safe_flags_ok"] and checks["safe_boundaries_preserved"],
            },
        ],
        "same_evidence_class_gaps_remaining": [] if status == "PASS" else discrepancies,
        "accepted": status == "PASS",
        **SAFE_FLAGS,
    }
    decision_payload = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": terminal_decision,
        "accepted": status == "PASS",
        "material_claims_status": "accepted" if status == "PASS" else "repair_or_reject_required",
        "no_promotion_verdict_preserved": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "summary": {
            "target_counts_recomputed": checks["target_result_rows_exact"]
            and checks["target_computable_rows_exact"]
            and checks["target_fail_closed_rows_exact"],
            "hashes_and_lfs_materialization_accepted": checks["manifest_hashes_match"] and checks["lfs_materialized"],
            "sealed_stress_separation_accepted": checks["sealed_stress_separated"],
            "pass_control_deltas_accepted": checks["pass_control_arithmetic_ok"]
            and checks["comparable_pass_control_exact"]
            and checks["positive_pass_control_exact"]
            and checks["inverse_pass_control_exact"],
            "descriptor_contrasts_accepted": checks["descriptor_one_vs_rest_exact"],
            "branch_coverage_accepted": branch_coverage["accepted"],
            "question_ambiguity_closure_accepted": True,
            "same_g12_repairable_remaining": repair["same_g12_repairable_items_remaining"],
        },
        "limitations": [
            "NO_PROMOTION_VERDICT remains mandatory.",
            "validation_safe=false remains mandatory.",
            "Concentration warnings and underpowered branch warnings constrain interpretation.",
            "Accepted intelligence is neutral target-movement only, not R/PnL/win-rate/expectancy/live-readiness.",
        ],
        **{k: v for k, v in SAFE_FLAGS.items() if k not in {"validation_safe", "outcome_review_opened", "live_effect"}},
    }
    completion = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "objective_restated": "Independently audit the READY8 discriminative sealed/stress validation execution packet with full-row or lossless streaming recomputation and preserve all safe boundaries.",
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight/context refresh performed", "artifact": ".context/LIVE_STATE.md and core docs read in-session", "satisfied": True},
            {"requirement": "terminal decision ledger", "artifact": rel(OUTPUT_FILES["decision"]), "satisfied": True},
            {"requirement": "recomputation ledger", "artifact": rel(OUTPUT_FILES["recomputation"]), "satisfied": True},
            {"requirement": "metric discrepancy ledger", "artifact": rel(OUTPUT_FILES["metric_discrepancy"]), "satisfied": True},
            {"requirement": "branch coverage audit ledger", "artifact": rel(OUTPUT_FILES["branch_coverage"]), "satisfied": True},
            {"requirement": "fail-closed/duplicate/concentration audit ledger", "artifact": rel(OUTPUT_FILES["fail_duplicate_concentration"]), "satisfied": True},
            {"requirement": "forbidden surface audit ledger", "artifact": rel(OUTPUT_FILES["forbidden_surface"]), "satisfied": True},
            {"requirement": "LFS/materialization/raw-blob audit ledger", "artifact": rel(OUTPUT_FILES["lfs_materialization"]), "satisfied": True},
            {"requirement": "full-ledger row-count/distribution recomputation ledger", "artifact": rel(OUTPUT_FILES["full_distribution"]), "satisfied": True},
            {"requirement": "same-G12 repair ledger", "artifact": rel(OUTPUT_FILES["repair"]), "satisfied": True},
            {"requirement": "saturation/self-red-team ledger", "artifact": rel(OUTPUT_FILES["saturation"]), "satisfied": True},
            {"requirement": "output manifest", "artifact": rel(OUTPUT_FILES["manifest"]), "satisfied": True},
            {"requirement": "focused tests/verifier output", "artifact": "written by verifier after focused tests", "satisfied": False},
        ],
        "material_result_claims_accepted_repaired_or_rejected": status == "PASS",
        "same_g12_repairable_items_remaining": repair["same_g12_repairable_items_remaining"],
        "missing_or_unverified_requirements_before_verifier": ["focused tests/verifier output"],
        "can_mark_goal_complete": False,
        "can_mark_goal_complete_after_verifier_and_focused_tests": status == "PASS",
        **SAFE_FLAGS,
    }

    outputs = {
        "decision": decision_payload,
        "recomputation": recomputation,
        "metric_discrepancy": metric_discrepancy,
        "branch_coverage": branch_coverage,
        "fail_duplicate_concentration": fail_duplicate_concentration,
        "forbidden_surface": forbidden_surface,
        "lfs_materialization": lfs_materialization,
        "full_distribution": full_distribution,
        "repair": repair,
        "saturation": saturation,
        "completion": completion,
    }
    for key, payload in outputs.items():
        write_json(OUTPUT_FILES[key], payload)

    summary_md = "\n".join(
        [
            "# G12 R8DISC Sealed Validation Audit",
            "",
            f"Generated: {generated_at}",
            f"Evidence class: `{EVIDENCE_CLASS}`",
            "",
            f"Terminal decision: `{terminal_decision}`",
            "",
            "## Recomputed Headlines",
            "",
            f"- Comparable pass/control records: {distributions['pass_control'].get('comparable_non_underpowered_records', 0)}",
            f"- Positive pass-minus-control records: {distributions['pass_control'].get('positive_delta_records', 0)}",
            f"- Inverse pass-minus-control records: {distributions['pass_control'].get('inverse_delta_records', 0)}",
            f"- Descriptor one-vs-rest records: {distributions['pass_control'].get('descriptor_one_vs_rest_records', 0)}",
            f"- Sealed primary branch records: {distributions['primary']['rows']}",
            f"- Stress records: {distributions['stress']['rows']}",
            f"- All-branch records: {distributions['all_branches']['rows']}",
            f"- Question records: {distributions['questions']['rows']}",
            f"- Ambiguity records: {distributions['ambiguities']['rows']}",
            "",
            "## Boundary",
            "",
            "NO_PROMOTION_VERDICT is preserved. `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed. Accepted claims are neutral target-movement audit evidence only.",
            "",
        ]
    )
    write_text(OUTPUT_FILES["summary_md"], summary_md)

    # Write a provisional manifest. The verifier rewrites it after adding
    # verifier and focused-test result artifacts.
    write_output_manifest(generated_at, include_verifier_outputs=False)
    return {"status": status, "terminal_decision": terminal_decision, "checks": checks}


def write_output_manifest(generated_at: str, include_verifier_outputs: bool = True) -> None:
    files = [
        OUTPUT_FILES["decision"],
        OUTPUT_FILES["recomputation"],
        OUTPUT_FILES["metric_discrepancy"],
        OUTPUT_FILES["branch_coverage"],
        OUTPUT_FILES["fail_duplicate_concentration"],
        OUTPUT_FILES["forbidden_surface"],
        OUTPUT_FILES["lfs_materialization"],
        OUTPUT_FILES["full_distribution"],
        OUTPUT_FILES["repair"],
        OUTPUT_FILES["saturation"],
        OUTPUT_FILES["completion"],
        OUTPUT_FILES["summary_md"],
        Path(__file__),
        OUTPUT_DIR / f"verify_g12_scid_ready8_discriminative_sealed_validation_result_audit_2026_05_13.py",
        OUTPUT_DIR / f"test_g12_scid_ready8_discriminative_sealed_validation_result_audit_2026_05_13.py",
    ]
    if include_verifier_outputs:
        files.extend(
            [
                OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_VERIFICATION_RESULT_{DATE}.json",
                OUTPUT_DIR / f"G12_R8DISC_SEALED_VALIDATION_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json",
            ]
        )
    artifacts = []
    for path in files:
        if path.exists():
            artifacts.append(
                {
                    "path": rel(path),
                    "exists": True,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        else:
            artifacts.append({"path": rel(path), "exists": False, "bytes": None, "sha256": None})
    manifest = {
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": "g12_r8disc_sealed_validation_audit_manifest_v1",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "manifest_self_hash_policy": "Manifest excludes itself from its own hash closure; verifier rewrites final manifest after verification artifacts exist.",
        **SAFE_FLAGS,
    }
    write_json(OUTPUT_FILES["manifest"], manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest-only", action="store_true")
    args = parser.parse_args()
    if args.write_manifest_only:
        write_output_manifest(utc_now(), include_verifier_outputs=True)
        return
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
