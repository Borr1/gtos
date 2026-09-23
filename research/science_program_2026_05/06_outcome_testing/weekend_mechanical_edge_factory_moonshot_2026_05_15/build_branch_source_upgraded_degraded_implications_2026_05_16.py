#!/usr/bin/env python3
"""Build SOURCE upgraded/degraded implication rows from bar-spread recompute."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SOURCE_BAR_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_RESULT_2026-05-16.json"
SOURCE_BAR_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_BAR_WINDOW = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_WINDOW_LEDGER_2026-05-16.jsonl"
SOURCE_BAR_ACCEPTED = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_ACCEPTED_LEDGER_2026-05-16.jsonl"
SOURCE_BAR_REPAIR = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_REPAIR_LEDGER_2026-05-16.jsonl"
SOURCE_DETAIL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_BRANCH_LEDGER_2026-05-16.jsonl"
NEXT_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE_LEDGER_2026-05-16.jsonl"
ACCEPTED_BUILDER_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
SOURCE_WINDOW_MATERIALIZATION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION_RESULT_2026-05-16.json"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LEDGER_2026-05-16.jsonl"
ACCEPTED_CONFIRMED_LEDGER = ROUTE_DIR / f"{PREFIX}_ACCEPTED_CONFIRMED_LEDGER_2026-05-16.jsonl"
ACCEPTED_DEGRADED_LEDGER = ROUTE_DIR / f"{PREFIX}_ACCEPTED_DEGRADED_LEDGER_2026-05-16.jsonl"
AMBIGUITY_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_M15_AMBIGUITY_REVIEW_LEDGER_2026-05-16.jsonl"
REPAIR_CONFIRMED_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONFIRMED_LEDGER_2026-05-16.jsonl"
UPGRADED_CHALLENGER_LEDGER = ROUTE_DIR / f"{PREFIX}_UPGRADED_CHALLENGER_REVIEW_LEDGER_2026-05-16.jsonl"
NO_SCALAR_LEDGER = ROUTE_DIR / f"{PREFIX}_NO_SCALAR_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "SOURCE upgraded/degraded implication packet only. It consumes local bar-spread "
    "proxy recompute rows for the SOURCE family, computes branch-level confirmed, "
    "degraded, upgraded, ambiguity, and no-scalar implications, and preserves exact "
    "tick/source gaps. It does not change live behavior and does not claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SOURCE-IMPLICATION-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def avg(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def implication_for(decision: str) -> tuple[str, str, str, str]:
    if decision == "BAR_PROXY_ACCEPTED_CONFIRMED":
        return (
            "SOURCE_ACCEPTED_CONFIRMED_BY_BAR_SPREAD_PROXY",
            "PRESERVE_SOURCE_ACCEPTED_CHALLENGER_CANDIDATE",
            "SOURCE_SUCCESS_CONFIRMED_BY_MATERIALIZED_BAR_SPREAD_PROXY",
            "NO_SOURCE_FAILURE_AFTER_BAR_SPREAD_PROXY",
        )
    if decision == "BAR_PROXY_ACCEPTED_DEGRADED_TO_REPAIR":
        return (
            "SOURCE_ACCEPTED_DEGRADED_TO_REPAIR_OR_AVOID",
            "DOWNGRADE_ACCEPTED_SOURCE_UNTIL_EXACT_SOURCE_OR_ALTERNATIVE_SOURCE_REPAIR",
            "NO_SUCCESS_AFTER_BAR_SPREAD_PROXY",
            "ACCEPTED_LOW_HIGH_STRESS_CANDIDATE_REVERSED_UNDER_MATERIALIZED_BAR_SPREAD_PROXY",
        )
    if decision == "BAR_PROXY_PARTIAL_SCALAR_ACCEPTED_DEGRADED_REVIEW_WITH_M15_AMBIGUITY":
        return (
            "SOURCE_ACCEPTED_DEGRADED_WITH_M15_ORDERING_AMBIGUITY",
            "SPLIT_TO_M15_ORDERING_REPAIR_BEFORE_KEEPING_SOURCE_ACCEPTED",
            "PARTIAL_SOURCE_SIGNAL_SURVIVES_ONLY_WITH_ORDERING_AMBIGUITY_OPEN",
            "ACCEPTED_SOURCE_HAS_NEGATIVE_SCALAR_ROWS_AND_M15_ORDER_UNRESOLVED_ROWS",
        )
    if decision == "BAR_PROXY_REPAIR_CONFIRMED":
        return (
            "SOURCE_REPAIR_CONFIRMED_BY_BAR_SPREAD_PROXY",
            "KEEP_SOURCE_REPAIR_OR_AVOID_DECISION",
            "NO_SOURCE_SUCCESS_AFTER_BAR_SPREAD_PROXY",
            "REPAIR_BRANCH_REMAINS_NEGATIVE_UNDER_MATERIALIZED_BAR_SPREAD_PROXY",
        )
    if decision == "BAR_PROXY_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW":
        return (
            "SOURCE_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW",
            "OPEN_SOURCE_CHALLENGER_REVIEW_FROM_REPAIR_BRANCH",
            "REPAIR_ROW_TURNS_POSITIVE_UNDER_MATERIALIZED_BAR_SPREAD_PROXY",
            "ORIGINAL_SOURCE_REPAIR_LABEL_WAS_LOW_HIGH_STRESS_SOURCE_LIMITED",
        )
    if decision == "BAR_PROXY_PARTIAL_SCALAR_REPAIR_UPGRADED_REVIEW_WITH_M15_AMBIGUITY":
        return (
            "SOURCE_REPAIR_UPGRADED_WITH_M15_ORDERING_AMBIGUITY",
            "OPEN_CHALLENGER_REVIEW_AFTER_M15_ORDERING_REPAIR",
            "REPAIR_ROW_HAS_POSITIVE_SCALAR_ROWS_AFTER_BAR_SPREAD_PROXY",
            "M15_ORDER_UNRESOLVED_ROWS_PREVENT_FULL_SCALAR_COLLAPSE",
        )
    if decision == "BAR_PROXY_PARTIAL_SCALAR_REPAIR_SUPPORTS_WITH_M15_AMBIGUITY":
        return (
            "SOURCE_REPAIR_SUPPORTED_WITH_M15_ORDERING_AMBIGUITY",
            "KEEP_REPAIR_DECISION_AND_ROUTE_AMBIGUITY_TO_M15_ORDERING_REPAIR",
            "NO_FULL_SOURCE_UPGRADE_AFTER_BAR_SPREAD_PROXY",
            "REPAIR_ROW_HAS_MIXED_OR_UNRESOLVED_M15_ORDERING_CONTEXT",
        )
    return (
        "SOURCE_NO_SCALAR_PRESERVE_REQUIREMENT",
        "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR_DECISION",
        "NO_SCALAR_SUCCESS_CAUSE",
        "BAR_SPREAD_PROXY_HAS_NO_TARGET_STOP_SCALAR_ROWS",
    )


def main() -> int:
    generated_at = now_utc()
    source_bar_result = read_json(SOURCE_BAR_RESULT)
    materialization_result = read_json(SOURCE_WINDOW_MATERIALIZATION)
    branch_rows_input = read_jsonl(SOURCE_BAR_BRANCH)
    window_rows = read_jsonl(SOURCE_BAR_WINDOW)
    accepted_rows_input = read_jsonl(SOURCE_BAR_ACCEPTED)
    repair_rows_input = read_jsonl(SOURCE_BAR_REPAIR)
    source_detail_rows = read_jsonl(SOURCE_DETAIL_BRANCH)
    next_source_rows = read_jsonl(NEXT_SOURCE)
    accepted_builder_rows = read_jsonl(ACCEPTED_BUILDER_SOURCE)
    detail_by_branch = by_id(source_detail_rows)
    next_by_branch = by_id(next_source_rows)
    accepted_builder_by_branch = by_id(accepted_builder_rows)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            SOURCE_BAR_RESULT,
            SOURCE_BAR_BRANCH,
            SOURCE_BAR_WINDOW,
            SOURCE_BAR_ACCEPTED,
            SOURCE_BAR_REPAIR,
            SOURCE_DETAIL_BRANCH,
            NEXT_SOURCE,
            ACCEPTED_BUILDER_SOURCE,
            SOURCE_WINDOW_MATERIALIZATION,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    implementation_rows: list[dict[str, Any]] = []
    accepted_confirmed_rows: list[dict[str, Any]] = []
    accepted_degraded_rows: list[dict[str, Any]] = []
    ambiguity_review_rows: list[dict[str, Any]] = []
    repair_confirmed_rows: list[dict[str, Any]] = []
    upgraded_challenger_rows: list[dict[str, Any]] = []
    no_scalar_rows: list[dict[str, Any]] = []

    for row in branch_rows_input:
        branch_id = row.get("branch_queue_id")
        detail = detail_by_branch.get(branch_id, {})
        next_row = next_by_branch.get(branch_id, {})
        accepted_builder = accepted_builder_by_branch.get(branch_id, {})
        decision = row.get("bar_spread_recompute_decision")
        implication_class, next_action, success_cause, failure_cause = implication_for(str(decision))
        bar_mean = as_float(row.get("bar_spread_rstyle_mean"))
        source_mid = as_float(detail.get("rstyle_midpoint_mean"))
        source_lower = as_float(detail.get("rstyle_lower_mean"))
        source_upper = as_float(detail.get("rstyle_upper_mean"))
        score_delta_midpoint = (
            round(bar_mean - source_mid, 6)
            if bar_mean is not None and source_mid is not None
            else None
        )
        out = {
            "source_implication_branch_id": f"OHLC-GTOS-SOURCE-IMPLICATION-BRANCH-{len(branch_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "source_bar_spread_branch_recompute_id": row.get("source_bar_spread_branch_recompute_id"),
            "source_cost_cap_detail_branch_id": row.get("source_cost_cap_detail_branch_id"),
            "source_builder_result_id": accepted_builder.get("source_builder_result_id"),
            "source_evidence_detail_id": next_row.get("source_evidence_detail_id"),
            "matrix_branch_id": detail.get("matrix_branch_id"),
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "target_multiple": row.get("target_multiple"),
            "stop_multiple": row.get("stop_multiple"),
            "target_stop_result": detail.get("target_stop_result"),
            "primary_export_family": "SOURCE",
            "branch_result_binary_before_bar_proxy": row.get("branch_result_binary"),
            "source_builder_result_status": row.get("source_builder_result_status"),
            "source_cost_cap_detail_status": row.get("source_cost_cap_detail_status"),
            "source_cost_interval_sign_class": row.get("source_cost_interval_sign_class"),
            "source_detail_scope": row.get("source_detail_scope"),
            "source_scalar_permission_before_bar_proxy": row.get("source_scalar_permission"),
            "source_acquisition_state_before_bar_proxy": row.get("source_acquisition_state_before_bar_proxy"),
            "exact_tick_recompute_state": row.get("exact_tick_recompute_state"),
            "bar_spread_recompute_decision": decision,
            "source_implication_class": implication_class,
            "next_same_resource_action": next_action,
            "bar_spread_sign_class": row.get("bar_spread_sign_class"),
            "bar_spread_rstyle_min": row.get("bar_spread_rstyle_min"),
            "bar_spread_rstyle_mean": row.get("bar_spread_rstyle_mean"),
            "bar_spread_rstyle_max": row.get("bar_spread_rstyle_max"),
            "source_stress_lower_mean": source_lower,
            "source_stress_midpoint_mean": source_mid,
            "source_stress_upper_mean": source_upper,
            "bar_minus_source_midpoint": score_delta_midpoint,
            "bar_spread_scalar_rows": row.get("bar_spread_scalar_rows"),
            "bar_spread_unresolved_rows": row.get("bar_spread_unresolved_rows"),
            "bar_spread_materialized_window_rows": row.get("bar_spread_materialized_window_rows"),
            "bar_spread_descriptor_counts": row.get("bar_spread_descriptor_counts"),
            "bar_spread_position_counts": row.get("bar_spread_position_counts"),
            "bar_spread_scale_class_counts": row.get("bar_spread_scale_class_counts"),
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "exact_success_cause": success_cause,
            "exact_failure_cause": failure_cause,
            "exact_missing_geometry_or_source_reason": (
                "Exact SOURCE tick truth remains unavailable for these historical windows; "
                "the row uses materialized local bar-spread proxy descriptors and preserves "
                "M15 ordering ambiguity where same-M15 target/stop order is unresolved."
            ),
        }
        with_common(out, generated_at, manifest_hash)
        branch_rows.append(out)

        impl = {
            "source_implication_implementation_id": f"OHLC-GTOS-SOURCE-IMPLICATION-IMPL-{len(implementation_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "route_candidate_id": out["route_candidate_id"],
            "route_session": out["route_session"],
            "symbol": out["symbol"],
            "side": out["side"],
            "entry_variant": out["entry_variant"],
            "target_stop_contract_id": out["target_stop_contract_id"],
            "source_implication_class": implication_class,
            "bar_spread_recompute_decision": decision,
            "branch_local_module_surface": "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/build_branch_source_upgraded_degraded_implications_2026_05_16.py",
            "proposed_system_use": next_action,
            "data_requirement_state": row.get("exact_tick_recompute_state"),
            "m15_ordering_requirement": (
                "M15_ORDERING_REPAIR_REQUIRED"
                if "AMBIGUITY" in str(decision)
                else "M15_ORDERING_NOT_REQUIRED_FOR_THIS_SOURCE_IMPLICATION"
            ),
            "source_gap_handling": "EXACT_TICK_GAP_PRESERVED_BAR_SPREAD_PROXY_USED",
        }
        with_common(impl, generated_at, manifest_hash)
        implementation_rows.append(impl)

        if decision == "BAR_PROXY_ACCEPTED_CONFIRMED":
            accepted_confirmed_rows.append(out)
        elif decision == "BAR_PROXY_ACCEPTED_DEGRADED_TO_REPAIR":
            accepted_degraded_rows.append(out)
        elif decision == "BAR_PROXY_REPAIR_CONFIRMED":
            repair_confirmed_rows.append(out)
        elif decision == "BAR_PROXY_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW":
            upgraded_challenger_rows.append(out)
        elif decision == "BAR_PROXY_NO_SCALAR_DECISION":
            no_scalar_rows.append(out)
        elif "M15_AMBIGUITY" in str(decision):
            ambiguity_review_rows.append(out)
            if "REPAIR_UPGRADED" in str(decision):
                upgraded_challenger_rows.append(out)
            elif "ACCEPTED_DEGRADED" in str(decision):
                accepted_degraded_rows.append(out)
            elif "REPAIR_SUPPORTS" in str(decision):
                repair_confirmed_rows.append(out)
        else:
            no_scalar_rows.append(out)

    score_values = [as_float(row.get("bar_spread_rstyle_mean")) for row in branch_rows]
    score_values = [value for value in score_values if value is not None]
    delta_values = [as_float(row.get("bar_minus_source_midpoint")) for row in branch_rows]
    delta_values = [value for value in delta_values if value is not None]
    bucket_sources = {
        "source_implication_class": Counter(row.get("source_implication_class") for row in branch_rows),
        "bar_spread_recompute_decision": Counter(row.get("bar_spread_recompute_decision") for row in branch_rows),
        "branch_result_binary_before_bar_proxy": Counter(row.get("branch_result_binary_before_bar_proxy") for row in branch_rows),
        "source_cost_cap_detail_status": Counter(row.get("source_cost_cap_detail_status") for row in branch_rows),
        "source_cost_interval_sign_class": Counter(row.get("source_cost_interval_sign_class") for row in branch_rows),
        "bar_spread_sign_class": Counter(row.get("bar_spread_sign_class") for row in branch_rows),
        "route_session": Counter(row.get("route_session") for row in branch_rows),
        "symbol": Counter(row.get("symbol") for row in branch_rows),
        "entry_variant": Counter(row.get("entry_variant") for row in branch_rows),
        "target_stop_result": Counter(row.get("target_stop_result") for row in branch_rows),
        "next_same_resource_action": Counter(row.get("next_same_resource_action") for row in branch_rows),
        "m15_ordering_requirement": Counter(row.get("m15_ordering_requirement") for row in implementation_rows),
    }
    bucket_rows = []
    for category, counter in sorted(bucket_sources.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-SOURCE-IMPLICATION-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket": str(bucket),
                        "row_count": int(count),
                        "share": round(count / total, 9) if total else None,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    question_rows = [
        {
            "question_id": "OHLC-GTOS-SOURCE-IMPLICATION-QUESTION-001",
            "question": "Which previously accepted SOURCE rows degrade under materialized bar-spread proxy?",
            "answer_route": "Use accepted degraded ledger and source_implication_class.",
        },
        {
            "question_id": "OHLC-GTOS-SOURCE-IMPLICATION-QUESTION-002",
            "question": "Which previously repair SOURCE rows become challenger review candidates?",
            "answer_route": "Use upgraded challenger review ledger and M15 ambiguity split.",
        },
        {
            "question_id": "OHLC-GTOS-SOURCE-IMPLICATION-QUESTION-003",
            "question": "Which rows still cannot scalarize because M15 ordering or no-touch source ambiguity remains?",
            "answer_route": "Use ambiguity review and no-scalar ledgers.",
        },
        {
            "question_id": "OHLC-GTOS-SOURCE-IMPLICATION-QUESTION-004",
            "question": "What is the next executable queue after SOURCE implication split?",
            "answer_route": "Continue entry/adverse redesign detail integration and join SOURCE degraded/upgraded classes to branch recommendation synthesis.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_source_bar_branch_rows": len(branch_rows_input),
            "input_source_bar_window_rows": len(window_rows),
            "input_source_bar_accepted_rows": len(accepted_rows_input),
            "input_source_bar_repair_rows": len(repair_rows_input),
            "input_source_detail_branch_rows": len(source_detail_rows),
            "input_next_source_rows": len(next_source_rows),
            "input_accepted_builder_source_rows": len(accepted_builder_rows),
            "branch_implication_rows": len(branch_rows),
            "accepted_confirmed_rows": len(accepted_confirmed_rows),
            "accepted_degraded_rows": len(accepted_degraded_rows),
            "m15_ambiguity_review_rows": len(ambiguity_review_rows),
            "repair_confirmed_rows": len(repair_confirmed_rows),
            "upgraded_challenger_review_rows": len(upgraded_challenger_rows),
            "no_scalar_rows": len(no_scalar_rows),
            "implementation_rows": len(implementation_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_source_bar_counts": source_bar_result.get("counts", {}),
        "upstream_materialization_counts": materialization_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "score_stats": {
            "bar_spread_rstyle_mean_min": round(min(score_values), 6) if score_values else None,
            "bar_spread_rstyle_mean_max": round(max(score_values), 6) if score_values else None,
            "bar_spread_rstyle_mean_mean": avg(score_values),
            "bar_minus_source_midpoint_min": round(min(delta_values), 6) if delta_values else None,
            "bar_minus_source_midpoint_max": round(max(delta_values), 6) if delta_values else None,
            "bar_minus_source_midpoint_mean": avg(delta_values),
        },
        "system_decision": {
            "system_recommendation": (
                "SOURCE_UPGRADED_DEGRADED_IMPLICATION_RESULT: preserve accepted-confirmed SOURCE rows, "
                "downgrade accepted rows that reverse under materialized bar-spread proxy, open challenger "
                "review for repair rows that turn positive, keep M15 ambiguity separate, and continue "
                "entry/adverse redesign detail integration."
            ),
            "branch_rows": len(branch_rows),
            "accepted_confirmed_rows": len(accepted_confirmed_rows),
            "accepted_degraded_rows": len(accepted_degraded_rows),
            "m15_ambiguity_review_rows": len(ambiguity_review_rows),
            "repair_confirmed_rows": len(repair_confirmed_rows),
            "upgraded_challenger_review_rows": len(upgraded_challenger_rows),
            "no_scalar_rows": len(no_scalar_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_LEDGER, branch_rows),
        (ACCEPTED_CONFIRMED_LEDGER, accepted_confirmed_rows),
        (ACCEPTED_DEGRADED_LEDGER, accepted_degraded_rows),
        (AMBIGUITY_REVIEW_LEDGER, ambiguity_review_rows),
        (REPAIR_CONFIRMED_LEDGER, repair_confirmed_rows),
        (UPGRADED_CHALLENGER_LEDGER, upgraded_challenger_rows),
        (NO_SCALAR_LEDGER, no_scalar_rows),
        (IMPLEMENTATION_LEDGER, implementation_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch SOURCE Upgraded/Degraded Implication",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch implication rows: `{len(branch_rows)}`",
                f"- Accepted confirmed rows: `{len(accepted_confirmed_rows)}`",
                f"- Accepted degraded rows: `{len(accepted_degraded_rows)}`",
                f"- Upgraded challenger review rows: `{len(upgraded_challenger_rows)}`",
                f"- M15 ambiguity review rows: `{len(ambiguity_review_rows)}`",
            ]
        ),
        encoding="utf-8",
    )
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_source_upgraded_degraded_implication",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_source_upgraded_degraded_implication_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
