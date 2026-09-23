#!/usr/bin/env python3
"""Stress exact descriptive avoid branches for concentration and source splits."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
PROXY_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_LEDGER_{STAMP}.jsonl"
EXACT_RESTRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_RESTRESS_LEDGER_{STAMP}.jsonl"
EXACT_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_SPEC_PLAN_LEDGER_{STAMP}.jsonl"
NON_EXACT_INPUT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_NON_EXACT_ROUTE_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_CONCENTRATION_STRESS_RESULT_{STAMP}.json"
BRANCH_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_BRANCH_LEDGER_{STAMP}.jsonl"
GROUP_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_GROUP_STRESS_LEDGER_{STAMP}.jsonl"
NON_EXACT_NEXT_ROUTE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_NON_EXACT_NEXT_ROUTE_LEDGER_{STAMP}.jsonl"
SPEC_PLAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPEC_PLAN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_CONCENTRATION_STRESS_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local exact avoid concentration/source split stress only; "
    "source-control/repair evidence with no strategy validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

AVOID_FRAGMENT = "AVOID_DIRECTION_VS_EXACT"
TARGET_ALIGNED_FRAGMENT = "TARGET_ALIGNED_VS_EXACT"
NEAR_FRAGMENT = "NEAR_EXACT"

CONCENTRATION_AXES = [
    "source_date",
    "source_symbol",
    "source_proxy_family",
    "command_feature_bucket",
    "horizon_id",
    "route_c_queue_id",
    "request_id",
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(out) or math.isinf(out) else out


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignment_values = [
        value for row in rows
        if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None
    ]
    future_values = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "route_alignment_n": len(alignment_values),
        "route_alignment_share": share(alignment_values),
        "mean_route_c_future_change_per_current_range": mean(future_values),
        "source_date_counts": counter_dict(row.get("source_date") for row in rows),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") for row in rows),
    }


def rows_matching(rows: list[dict[str, Any]], axis: str, value: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get(axis)) == value]


def exact_feature_rows(source_join: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES
        and not row.get("source_silence_joined")
    ]


def verdict_vs_exact(target_stats: dict[str, Any], exact_stats: dict[str, Any]) -> str:
    target_n = int(target_stats.get("n") or 0)
    exact_n = int(exact_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    exact_align = exact_stats.get("route_alignment_share")
    if target_n < 5:
        sample_prefix = "EXACT_AVOID_STRESS_TARGET_UNDERPOWERED_N_LT_5"
    elif target_n < 20:
        sample_prefix = "EXACT_AVOID_STRESS_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = "EXACT_AVOID_STRESS_TARGET_N_OK"
    if exact_n < 5:
        return f"{sample_prefix}_EXACT_CONTROL_UNDERPOWERED_N_LT_5"
    if exact_n < 20:
        return f"{sample_prefix}_EXACT_CONTROL_UNDERPOWERED_N_LT_20"
    if target_align is None or exact_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < exact_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_EXACT"
    if target_align > exact_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_EXACT"
    return f"{sample_prefix}_NEAR_EXACT"


def group_values(target_rows: list[dict[str, Any]], exact_rows: list[dict[str, Any]], axis: str) -> list[str]:
    values = {
        str(row.get(axis))
        for row in [*target_rows, *exact_rows]
        if row.get(axis) is not None
    }
    return sorted(values)


def dominant_value(counts: dict[str, int]) -> tuple[str | None, int, float | None]:
    if not counts:
        return None, 0, None
    value, count = max(counts.items(), key=lambda item: (item[1], item[0]))
    total = sum(counts.values())
    return value, count, count / total if total else None


def classify_group_stress(after_status: str, target_without_n: int, target_share: float | None) -> str:
    if target_without_n < 5:
        return "EXACT_AVOID_GROUP_REMOVAL_TARGET_UNDERPOWERED_N_LT_5"
    if AVOID_FRAGMENT in after_status:
        return "EXACT_AVOID_PERSISTS_AFTER_LEAVE_GROUP"
    if TARGET_ALIGNED_FRAGMENT in after_status:
        return "EXACT_AVOID_REVERSES_TO_TARGET_ALIGNED_AFTER_LEAVE_GROUP"
    if NEAR_FRAGMENT in after_status:
        if target_share is not None and target_share >= 0.5:
            return "EXACT_AVOID_CONCENTRATION_WEAKENS_TO_NEAR_EXACT"
        return "EXACT_AVOID_WEAKENS_TO_NEAR_EXACT_AFTER_LEAVE_GROUP"
    if "CONTROL_UNDERPOWERED" in after_status:
        return "EXACT_AVOID_LEAVE_GROUP_CONTROL_UNDERPOWERED"
    return "EXACT_AVOID_LEAVE_GROUP_DESCRIPTIVE_NO_ALIGNMENT"


def classify_branch(group_rows: list[dict[str, Any]], target_n: int, original_status: str) -> str:
    if AVOID_FRAGMENT not in original_status:
        return "EXACT_RESTRESS_NON_AVOID_BRANCH_PRESERVED"
    if target_n < 5:
        return "EXACT_AVOID_BRANCH_TARGET_N_LT_5_SOURCE_EXPANSION_REQUIRED"
    feasible = [
        row for row in group_rows
        if row.get("target_without_group", {}).get("n", 0) >= 5
        and row.get("exact_without_group", {}).get("n", 0) >= 5
    ]
    if not feasible:
        return "EXACT_AVOID_BRANCH_NO_FEASIBLE_LEAVE_GROUP_STRESS"
    weak = [
        row for row in feasible
        if row.get("group_stress_status") in {
            "EXACT_AVOID_CONCENTRATION_WEAKENS_TO_NEAR_EXACT",
            "EXACT_AVOID_WEAKENS_TO_NEAR_EXACT_AFTER_LEAVE_GROUP",
            "EXACT_AVOID_REVERSES_TO_TARGET_ALIGNED_AFTER_LEAVE_GROUP",
        }
    ]
    persist = [row for row in feasible if row.get("group_stress_status") == "EXACT_AVOID_PERSISTS_AFTER_LEAVE_GROUP"]
    if weak and persist:
        return "EXACT_AVOID_BRANCH_MIXED_CONCENTRATION_SENSITIVE"
    if weak:
        return "EXACT_AVOID_BRANCH_CONCENTRATION_SENSITIVE"
    if len(persist) == len(feasible):
        return "EXACT_AVOID_BRANCH_PERSISTS_ALL_FEASIBLE_GROUP_STRESS"
    return "EXACT_AVOID_BRANCH_DESCRIPTIVE_REQUIRES_SOURCE_EXPANSION"


def next_route_for_non_exact(row: dict[str, Any]) -> str:
    status = str(row.get("acquisition_status"))
    if status == "LOCAL_DEPTH_ROWS_AVAILABLE_EXACT_FEATURE_UNDERPOWERED_REPLAY_OR_PROXY_NOW":
        return "NON_EXACT_LOCAL_DEPTH_REPLAY_OR_PROXY_NOW"
    if status == "ROUTE_C_SOURCE_JOIN_PROXY_AVAILABLE_EXACT_DEPTH_ACQUISITION_NEEDED":
        return "NON_EXACT_ROUTE_C_PROXY_EXACT_DEPTH_SOURCE_DATE_ACQUISITION"
    if status == "ONLY_TARGET_PROXY_ROWS_AVAILABLE_NEEDS_BROADER_SOURCE_ACQUISITION":
        return "NON_EXACT_TARGET_ONLY_BROADER_SOURCE_ACQUISITION"
    return "NON_EXACT_ROUTE_STATUS_REVIEW_REQUIRED"


def build_branch_and_group_rows(
    restress_rows: list[dict[str, Any]],
    source_join: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact_controls_all = exact_feature_rows(source_join)
    branch_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    groups_by_restress: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for restress in restress_rows:
        axis = str(restress.get("stress_axis"))
        value = str(restress.get("left_out_value"))
        target_rows = rows_matching(proxy_targets, axis, value)
        exact_controls = rows_matching(exact_controls_all, axis, value)
        original_status = str(restress.get("exact_split_restress_status"))
        if AVOID_FRAGMENT not in original_status:
            continue
        for stress_axis in CONCENTRATION_AXES:
            for group_value in group_values(target_rows, exact_controls, stress_axis):
                target_group = rows_matching(target_rows, stress_axis, group_value)
                exact_group = rows_matching(exact_controls, stress_axis, group_value)
                target_without = [row for row in target_rows if str(row.get(stress_axis)) != group_value]
                exact_without = [row for row in exact_controls if str(row.get(stress_axis)) != group_value]
                target_stats = row_stats(target_rows)
                exact_stats = row_stats(exact_controls)
                target_without_stats = row_stats(target_without)
                exact_without_stats = row_stats(exact_without)
                after_status = verdict_vs_exact(target_without_stats, exact_without_stats)
                target_share = len(target_group) / len(target_rows) if target_rows else None
                exact_share = len(exact_group) / len(exact_controls) if exact_controls else None
                group_status = classify_group_stress(after_status, int(target_without_stats["n"]), target_share)
                group_role = "target_and_exact"
                if target_group and not exact_group:
                    group_role = "target_only"
                elif exact_group and not target_group:
                    group_role = "exact_only"
                row = {
                    "group_stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-GROUP-STRESS-{len(group_rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "exact_split_restress_id": restress.get("exact_split_restress_id"),
                    "fragile_stress_split_id": restress.get("fragile_stress_split_id"),
                    "source_acquisition_requirement_id": restress.get("source_acquisition_requirement_id"),
                    "dedup_spec_id": restress.get("dedup_spec_id"),
                    "original_stress_axis": axis,
                    "original_left_out_value": value,
                    "original_exact_split_restress_status": original_status,
                    "concentration_axis": stress_axis,
                    "concentration_value": group_value,
                    "group_role": group_role,
                    "target_group_n": len(target_group),
                    "exact_group_n": len(exact_group),
                    "target_group_share": target_share,
                    "exact_group_share": exact_share,
                    "target_all": target_stats,
                    "exact_all": exact_stats,
                    "target_without_group": target_without_stats,
                    "exact_without_group": exact_without_stats,
                    "after_leave_group_status": after_status,
                    "group_stress_status": group_status,
                    "target_alignment_delta_without_group": numeric_delta(
                        target_without_stats.get("route_alignment_share"),
                        exact_without_stats.get("route_alignment_share"),
                    ),
                    "not_completion": "Concentration stress is source-control intelligence, not validation or completion.",
                }
                group_rows.append(row)
                groups_by_restress[str(restress.get("exact_split_restress_id"))].append(row)

    for restress in restress_rows:
        target_stats = restress.get("target_rows", {})
        exact_stats = restress.get("exact_feature_rows", {})
        source_date, source_date_count, source_date_share = dominant_value(target_stats.get("source_date_counts", {}))
        source_symbol, source_symbol_count, source_symbol_share = dominant_value(target_stats.get("source_symbol_counts", {}))
        command_bucket, command_bucket_count, command_bucket_share = dominant_value(
            target_stats.get("command_feature_bucket_counts", {})
        )
        restress_id = str(restress.get("exact_split_restress_id"))
        branch_group_rows = groups_by_restress.get(restress_id, [])
        branch_status = classify_branch(
            branch_group_rows,
            int(target_stats.get("n") or 0),
            str(restress.get("exact_split_restress_status")),
        )
        branch_rows.append(
            {
                "exact_avoid_branch_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-BRANCH-{len(branch_rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "exact_split_restress_id": restress.get("exact_split_restress_id"),
                "fragile_stress_split_id": restress.get("fragile_stress_split_id"),
                "source_acquisition_requirement_id": restress.get("source_acquisition_requirement_id"),
                "dedup_spec_id": restress.get("dedup_spec_id"),
                "stress_axis": restress.get("stress_axis"),
                "left_out_value": restress.get("left_out_value"),
                "exact_split_restress_status": restress.get("exact_split_restress_status"),
                "is_exact_descriptive_avoid_branch": AVOID_FRAGMENT in str(restress.get("exact_split_restress_status")),
                "branch_concentration_status": branch_status,
                "target_n": target_stats.get("n"),
                "exact_feature_n": exact_stats.get("n"),
                "target_alignment_delta_vs_exact": restress.get("target_alignment_delta_vs_exact"),
                "dominant_target_source_date": source_date,
                "dominant_target_source_date_n": source_date_count,
                "dominant_target_source_date_share": source_date_share,
                "dominant_target_source_symbol": source_symbol,
                "dominant_target_source_symbol_n": source_symbol_count,
                "dominant_target_source_symbol_share": source_symbol_share,
                "dominant_target_command_bucket": command_bucket,
                "dominant_target_command_bucket_n": command_bucket_count,
                "dominant_target_command_bucket_share": command_bucket_share,
                "group_stress_rows": len(branch_group_rows),
                "group_stress_status_counts": counter_dict(row.get("group_stress_status") for row in branch_group_rows),
                "concentration_axis_counts": counter_dict(row.get("concentration_axis") for row in branch_group_rows),
                "next_same_resource_action": next_action_for_branch(branch_status),
                "not_completion": "Exact avoid branch stress is descriptive source-control evidence only.",
            }
        )

    return branch_rows, group_rows


def next_action_for_branch(status: str) -> str:
    if status == "EXACT_RESTRESS_NON_AVOID_BRANCH_PRESERVED":
        return "preserve non-avoid exact split branch and prioritize avoid/non-exact routes"
    if "CONCENTRATION_SENSITIVE" in status:
        return "split by concentration axis and pursue source-date/source-symbol acquisition or broader proxy now"
    if "PERSISTS" in status:
        return "preserve descriptive avoid branch and seek broader exact source/proxy denominator now"
    if "NO_FEASIBLE" in status or "N_LT_5" in status:
        return "build local-depth/proxy expansion or exact source acquisition now"
    return "route to source expansion and unrelated challenger comparison"


def build_non_exact_next_routes(non_exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in non_exact_rows:
        route_status = next_route_for_non_exact(row)
        rows.append(
            {
                "non_exact_next_route_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-NON-EXACT-NEXT-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "non_exact_route_id": row.get("non_exact_route_id"),
                "source_acquisition_requirement_id": row.get("source_acquisition_requirement_id"),
                "fragile_stress_split_id": row.get("fragile_stress_split_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "stress_axis": row.get("stress_axis"),
                "left_out_value": row.get("left_out_value"),
                "acquisition_status": row.get("acquisition_status"),
                "current_exact_feature_rows": row.get("current_exact_feature_rows"),
                "current_local_depth_rows": row.get("current_local_depth_rows"),
                "current_source_join_rows": row.get("current_source_join_rows"),
                "current_target_proxy_rows": row.get("current_target_proxy_rows"),
                "non_exact_next_route_status": route_status,
                "next_same_resource_action": non_exact_action(route_status),
                "not_completion": "Non-exact route is carried forward for immediate replay/acquisition, not waiting.",
            }
        )
    return rows


def non_exact_action(status: str) -> str:
    if status == "NON_EXACT_LOCAL_DEPTH_REPLAY_OR_PROXY_NOW":
        return "build local-depth replay/proxy packet for this row family now"
    if status == "NON_EXACT_ROUTE_C_PROXY_EXACT_DEPTH_SOURCE_DATE_ACQUISITION":
        return "search owned/free/current exact .depth source-date roots and build acquisition manifest now"
    if status == "NON_EXACT_TARGET_ONLY_BROADER_SOURCE_ACQUISITION":
        return "broaden source/proxy denominator and search public/free/local source roots now"
    return "inspect row and assign exact acquisition/replay route"


def build_spec_plan_rows(
    exact_specs: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    non_exact_next_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    branches_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    non_exact_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rows:
        branches_by_spec[str(row.get("dedup_spec_id"))].append(row)
    for row in non_exact_next_rows:
        non_exact_by_spec[str(row.get("dedup_spec_id"))].append(row)

    rows: list[dict[str, Any]] = []
    for spec in exact_specs:
        spec_id = str(spec.get("dedup_spec_id"))
        spec_branches = branches_by_spec.get(spec_id, [])
        avoid_branches = [row for row in spec_branches if row.get("is_exact_descriptive_avoid_branch")]
        non_exact = non_exact_by_spec.get(spec_id, [])
        branch_counts = counter_dict(row.get("branch_concentration_status") for row in spec_branches)
        non_exact_counts = counter_dict(row.get("non_exact_next_route_status") for row in non_exact)
        spec_status = classify_spec_plan(avoid_branches, non_exact)
        rows.append(
            {
                "exact_avoid_spec_plan_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "prior_spec_exact_plan_id": spec.get("spec_exact_plan_id"),
                "prior_spec_exact_split_status": spec.get("spec_exact_split_status"),
                "exact_restress_rows": len(spec_branches),
                "exact_avoid_branch_rows": len(avoid_branches),
                "non_exact_next_route_rows": len(non_exact),
                "branch_concentration_status_counts": branch_counts,
                "non_exact_next_route_status_counts": non_exact_counts,
                "exact_avoid_spec_plan_status": spec_status,
                "next_same_resource_action": spec_action(spec_status),
                "not_completion": "Spec plan is source-control routing only, not validation or live readiness.",
            }
        )
    return rows


def classify_spec_plan(avoid_branches: list[dict[str, Any]], non_exact_rows: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("branch_concentration_status")) for row in avoid_branches}
    non_exact_statuses = {str(row.get("non_exact_next_route_status")) for row in non_exact_rows}
    if any("CONCENTRATION_SENSITIVE" in status for status in statuses):
        return "SPEC_EXACT_AVOID_CONCENTRATION_SENSITIVE_SPLIT_AND_ACQUIRE"
    if "EXACT_AVOID_BRANCH_PERSISTS_ALL_FEASIBLE_GROUP_STRESS" in statuses:
        return "SPEC_EXACT_AVOID_PERSISTS_BUT_REQUIRES_BROADER_DENOMINATOR"
    if non_exact_statuses:
        return "SPEC_EXACT_AVOID_REQUIRES_NON_EXACT_REPLAY_OR_SOURCE_ACQUISITION"
    return "SPEC_EXACT_AVOID_UNDERPOWERED_SOURCE_EXPANSION_QUEUE"


def spec_action(status: str) -> str:
    if status == "SPEC_EXACT_AVOID_CONCENTRATION_SENSITIVE_SPLIT_AND_ACQUIRE":
        return "split exact avoid rows by source concentration and acquire/proxy missing exact sources now"
    if status == "SPEC_EXACT_AVOID_PERSISTS_BUT_REQUIRES_BROADER_DENOMINATOR":
        return "broaden exact source/proxy denominator before implementation consideration"
    if status == "SPEC_EXACT_AVOID_REQUIRES_NON_EXACT_REPLAY_OR_SOURCE_ACQUISITION":
        return "execute local-depth replay/source acquisition routes from non-exact ledger now"
    return "expand source denominator and preserve failure intelligence"


def build_bucket_rows(
    branch_rows: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    non_exact_next_rows: list[dict[str, Any]],
    spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_sets = [
        ("branch_concentration_status", counter_dict(row.get("branch_concentration_status") for row in branch_rows)),
        ("group_stress_status", counter_dict(row.get("group_stress_status") for row in group_rows)),
        ("group_concentration_axis", counter_dict(row.get("concentration_axis") for row in group_rows)),
        ("source_date_group_status", counter_dict(row.get("group_stress_status") for row in group_rows if row.get("concentration_axis") == "source_date")),
        ("source_symbol_group_status", counter_dict(row.get("group_stress_status") for row in group_rows if row.get("concentration_axis") == "source_symbol")),
        ("non_exact_next_route_status", counter_dict(row.get("non_exact_next_route_status") for row in non_exact_next_rows)),
        ("exact_avoid_spec_plan_status", counter_dict(row.get("exact_avoid_spec_plan_status") for row in spec_rows)),
    ]
    for bucket_family, counts in bucket_sets:
        for value, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": bucket_family,
                    "bucket_value": value,
                    "row_count": count,
                    "not_completion": "Bucket rows summarize full ledgers without replacing them.",
                }
            )
    return rows


def build_question_rows(
    branch_rows: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    non_exact_next_rows: list[dict[str, Any]],
    spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for branch in branch_rows:
        if not branch.get("is_exact_descriptive_avoid_branch"):
            continue
        rows.append(
            question(
                len(rows) + 1,
                "exact_avoid_branch",
                branch.get("exact_split_restress_id"),
                branch.get("dedup_spec_id"),
                branch.get("branch_concentration_status"),
                branch.get("next_same_resource_action"),
            )
        )
    for group in group_rows:
        rows.append(
            question(
                len(rows) + 1,
                "exact_avoid_group_stress",
                group.get("group_stress_id"),
                group.get("dedup_spec_id"),
                group.get("group_stress_status"),
                "use this full leave-group row to split, acquire, proxy, or preserve the descriptive avoid branch",
            )
        )
    for route in non_exact_next_rows:
        rows.append(
            question(
                len(rows) + 1,
                "non_exact_next_route",
                route.get("non_exact_next_route_id"),
                route.get("dedup_spec_id"),
                route.get("non_exact_next_route_status"),
                route.get("next_same_resource_action"),
            )
        )
    for spec in spec_rows:
        rows.append(
            question(
                len(rows) + 1,
                "spec_plan",
                spec.get("exact_avoid_spec_plan_id"),
                spec.get("dedup_spec_id"),
                spec.get("exact_avoid_spec_plan_status"),
                spec.get("next_same_resource_action"),
            )
        )
    return rows


def question(
    index: int,
    scope: str,
    source_id: Any,
    spec_id: Any,
    status: Any,
    action: Any,
) -> dict[str, Any]:
    return {
        "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-Q-{index:05d}",
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "question_scope": scope,
        "source_row_id": source_id,
        "dedup_spec_id": spec_id,
        "status": status,
        "question": "What else can be extracted now from this source-control state without waiting?",
        "next_same_resource_action": action,
        "not_completion": "Question rows generate immediate work; they are not a parking lot.",
    }


def update_manifest(generated_utc: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", [])
    existing = {artifact.get("path") for artifact in artifacts if isinstance(artifact, dict)}
    for path, description in [
        (Path(__file__).resolve(), "Builder for exact avoid concentration/source-date/source-symbol stress."),
        (RESULT_PATH, "Exact avoid concentration stress result JSON."),
        (BRANCH_LEDGER, "All exact split branches with avoid/concentration status."),
        (GROUP_STRESS_LEDGER, "Full leave-group concentration stress ledger."),
        (NON_EXACT_NEXT_ROUTE_LEDGER, "All non-exact routes carried into immediate replay/acquisition."),
        (SPEC_PLAN_LEDGER, "Spec-level exact avoid source/acquisition plan."),
        (BUCKET_LEDGER, "Bucket counts for full exact avoid ledgers."),
        (QUESTION_LEDGER, "Question/action ledger for exact avoid concentration packet."),
        (SUMMARY_PATH, "Human summary for exact avoid concentration packet."),
    ]:
        rel = relative(path)
        if rel not in existing:
            artifacts.append({"path": rel, "description": description})
            existing.add(rel)
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], spec_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_exact_avoid_concentration_stress",
        "status": "done",
        "route": "source_silence_microcluster_exact_avoid_concentration_stress",
        "details": "Ran concentration/source-date/source-symbol leave-group stress on all exact descriptive avoid rows.",
        "counts": counts,
        "spec_status_counts": spec_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(BRANCH_LEDGER),
            relative(GROUP_STRESS_LEDGER),
            relative(NON_EXACT_NEXT_ROUTE_LEDGER),
            relative(SPEC_PLAN_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], spec_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Exact Avoid Concentration Stress",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local exact avoid concentration/source split stress only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Status", ""])
    for key, value in sorted(spec_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Split concentration-sensitive avoid branches by source date, source symbol, source proxy family, command bucket, horizon, queue, and request axis from the full group ledger.",
            "- Build local-depth replay/proxy packets for non-exact local-depth rows.",
            "- Search/acquire exact `.depth` source-date rows and broaden source/proxy denominators for target-only rows.",
            "- Keep unrelated challenger-family expansion active in parallel; this packet is not a completion checkpoint.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    restress_rows = read_jsonl(EXACT_RESTRESS_LEDGER)
    exact_specs = read_jsonl(EXACT_SPEC_LEDGER)
    non_exact_input_rows = read_jsonl(NON_EXACT_INPUT_LEDGER)
    branch_rows, group_rows = build_branch_and_group_rows(restress_rows, source_join, proxy_targets)
    non_exact_next_rows = build_non_exact_next_routes(non_exact_input_rows)
    spec_rows = build_spec_plan_rows(exact_specs, branch_rows, non_exact_next_rows)
    bucket_rows = build_bucket_rows(branch_rows, group_rows, non_exact_next_rows, spec_rows)
    question_rows = build_question_rows(branch_rows, group_rows, non_exact_next_rows, spec_rows)
    spec_counts = counter_dict(row.get("exact_avoid_spec_plan_status") for row in spec_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "exact_feature_control_rows": len(exact_feature_rows(source_join)),
        "exact_split_restress_input_rows": len(restress_rows),
        "exact_descriptive_avoid_input_rows": sum(1 for row in restress_rows if AVOID_FRAGMENT in str(row.get("exact_split_restress_status"))),
        "non_exact_route_input_rows": len(non_exact_input_rows),
        "exact_spec_input_rows": len(exact_specs),
        "branch_rows": len(branch_rows),
        "group_stress_rows": len(group_rows),
        "non_exact_next_route_rows": len(non_exact_next_rows),
        "spec_plan_rows": len(spec_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_exact_avoid_concentration_stress_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_CONCENTRATION_STRESS_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "branch_concentration_status_counts": counter_dict(row.get("branch_concentration_status") for row in branch_rows),
        "group_stress_status_counts": counter_dict(row.get("group_stress_status") for row in group_rows),
        "group_concentration_axis_counts": counter_dict(row.get("concentration_axis") for row in group_rows),
        "source_date_group_stress_status_counts": counter_dict(row.get("group_stress_status") for row in group_rows if row.get("concentration_axis") == "source_date"),
        "source_symbol_group_stress_status_counts": counter_dict(row.get("group_stress_status") for row in group_rows if row.get("concentration_axis") == "source_symbol"),
        "non_exact_next_route_status_counts": counter_dict(row.get("non_exact_next_route_status") for row in non_exact_next_rows),
        "spec_status_counts": spec_counts,
        "not_completion": "This concentration stress packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "split concentration-sensitive exact avoid branches by full group-stress ledger",
            "build local-depth replay/proxy packet for non-exact local-depth rows",
            "search/acquire exact .depth source-date files and broaden source/proxy denominators",
            "reopen unrelated challenger families from the frontier map in parallel",
        ],
    }
    write_jsonl(BRANCH_LEDGER, branch_rows)
    write_jsonl(GROUP_STRESS_LEDGER, group_rows)
    write_jsonl(NON_EXACT_NEXT_ROUTE_LEDGER, non_exact_next_rows)
    write_jsonl(SPEC_PLAN_LEDGER, spec_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, spec_counts)
    write_summary(generated_utc, counts, spec_counts)
    print(json.dumps({"ok": True, "counts": counts, "spec_counts": spec_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
