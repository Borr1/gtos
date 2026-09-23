#!/usr/bin/env python3
"""Build sealed/proxy packets for source-silence microcluster survivors."""

from __future__ import annotations

import itertools
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
DEDUP_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_DEDUP_SPEC_LEDGER_{STAMP}.jsonl"
BROADER_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_BROADER_CONTROL_LEDGER_{STAMP}.jsonl"
CONCENTRATION_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_CONCENTRATION_STRESS_LEDGER_{STAMP}.jsonl"
SURVIVOR_QUEUE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_SURVIVOR_QUEUE_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_PACKET_RESULT_{STAMP}.json"
SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_SPEC_LEDGER_{STAMP}.jsonl"
SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_SCOPE_LEDGER_{STAMP}.jsonl"
AXIS_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_AXIS_SPLIT_LEDGER_{STAMP}.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_MEMBER_LEDGER_{STAMP}.jsonl"
CAPTURE_SCHEMA_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_CAPTURE_SCHEMA_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_PACKET_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local sealed/proxy source-activity packet only; source-control/design "
    "evidence with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

CONTROL_AXES = [
    "route_c_queue_id",
    "command_feature_bucket",
    "source_symbol",
    "source_date",
    "horizon_id",
    "source_proxy_family",
]

STATE_SPLIT_AXES = [
    "candidate_replay_bucket",
    "proxy_target_status",
    "source_silence_status",
]

CAPTURE_FIELDS = [
    ("request_id", "stable event-window identity"),
    ("depth_path", "source file path under current local Sierra root"),
    ("source_symbol", "futures/proxy source symbol"),
    ("source_date", "source file/session date"),
    ("file_first_record_utc", "source file lower timestamp bound"),
    ("file_last_record_utc", "source file upper timestamp bound"),
    ("event15_record_count", "records inside full M15 event window"),
    ("event_boundary_record_count", "records inside final event-boundary slice"),
    ("source_silence_status", "exact source-silence/no-clear/no-record state"),
    ("candidate_replay_bucket", "target source-activity bucket"),
    ("command_feature_bucket", "command-flow proxy bucket"),
    ("route_c_queue_id", "Route C residual queue identity"),
    ("horizon_id", "Route C target horizon"),
    ("route_c_future_change_per_current_range", "research label magnitude, never a decision-time feature"),
    ("route_c_delta_aligned_with_future", "research label direction, never a decision-time feature"),
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
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "candidate_replay_bucket_counts": counter_dict(row.get("candidate_replay_bucket") for row in rows),
        "proxy_target_status_counts": counter_dict(row.get("proxy_target_status") for row in rows),
        "source_silence_status_counts": counter_dict(row.get("source_silence_status") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
    }


def axis_values(rows: list[dict[str, Any]], axis: str) -> set[Any]:
    return {row.get(axis) for row in rows if row.get(axis) is not None}


def all_axis_combinations() -> list[tuple[str, ...]]:
    combos: list[tuple[str, ...]] = [()]
    for size in range(1, len(CONTROL_AXES) + 1):
        combos.extend(itertools.combinations(CONTROL_AXES, size))
    return combos


def scope_name(axes: tuple[str, ...]) -> str:
    return "all_exact_features" if not axes else "same_" + "_".join(axes)


def control_rows_for_axes(
    exact_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    axes: tuple[str, ...],
) -> list[dict[str, Any]]:
    target_ids = {str(row.get("request_id")) for row in target_rows if row.get("request_id")}
    if not axes:
        return [row for row in exact_rows if str(row.get("request_id")) not in target_ids]
    values_by_axis = {axis: axis_values(target_rows, axis) for axis in axes}
    rows: list[dict[str, Any]] = []
    for row in exact_rows:
        if str(row.get("request_id")) in target_ids:
            continue
        if all(row.get(axis) in values_by_axis[axis] for axis in axes):
            rows.append(row)
    return rows


def verdict_vs_control(target_stats: dict[str, Any], control_stats: dict[str, Any]) -> str:
    target_n = int(target_stats.get("n") or 0)
    control_n = int(control_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    control_align = control_stats.get("route_alignment_share")
    if target_n < 5:
        return "SEALED_PROXY_TARGET_UNDERPOWERED_N_LT_5"
    if target_n < 20:
        sample_prefix = "SEALED_PROXY_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = "SEALED_PROXY_TARGET_N_OK"
    if control_n < 5:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_5"
    if control_n < 20:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_20"
    if target_align is None or control_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < control_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_PROXY_CONTROL"
    if target_align > control_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_PROXY_CONTROL"
    return f"{sample_prefix}_NEAR_PROXY_CONTROL"


def context_verdict(control_stats: dict[str, Any], baseline_stats: dict[str, Any]) -> str:
    control_n = int(control_stats.get("n") or 0)
    control_align = control_stats.get("route_alignment_share")
    baseline_align = baseline_stats.get("route_alignment_share")
    if control_n < 5:
        return "PROXY_CONTEXT_CONTROL_UNDERPOWERED_N_LT_5"
    if control_n < 20:
        return "PROXY_CONTEXT_CONTROL_UNDERPOWERED_N_LT_20"
    if control_align is None or baseline_align is None:
        return "PROXY_CONTEXT_DESCRIPTIVE_NO_ALIGNMENT"
    if control_align < baseline_align - 0.15:
        return "PROXY_CONTEXT_AVOID_DIRECTION_VS_ALL_EXACT"
    if control_align > baseline_align + 0.15:
        return "PROXY_CONTEXT_ALIGNED_VS_ALL_EXACT"
    return "PROXY_CONTEXT_NEAR_ALL_EXACT"


def rows_from_request_ids(rows_by_request: dict[str, dict[str, Any]], request_ids: list[str]) -> list[dict[str, Any]]:
    return [rows_by_request[request_id] for request_id in request_ids if request_id in rows_by_request]


def max_axis_share(target_rows: list[dict[str, Any]], axis: str) -> float | None:
    if not target_rows:
        return None
    counts = Counter(row.get(axis) for row in target_rows)
    return max(counts.values()) / len(target_rows) if counts else None


def concentration_axes(target_rows: list[dict[str, Any]]) -> list[str]:
    axes: list[str] = []
    for axis in [*CONTROL_AXES, *STATE_SPLIT_AXES]:
        share_value = max_axis_share(target_rows, axis)
        if share_value is not None and share_value > 0.75:
            axes.append(axis)
    return axes


def build_member_rows(
    survivors: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for survivor in survivors:
        for request_id in survivor.get("dedup_request_ids", []):
            target = targets_by_request.get(str(request_id))
            if not target:
                rows.append(
                    {
                        "member_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-MEMBER-{len(rows) + 1:05d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "survivor_queue_id": survivor.get("survivor_queue_id"),
                        "dedup_spec_id": survivor.get("dedup_spec_id"),
                        "request_id": request_id,
                        "member_status": "TARGET_REQUEST_ID_MISSING_FROM_PROXY_TARGET_LEDGER",
                    }
                )
                continue
            rows.append(
                {
                    "member_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-MEMBER-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "survivor_queue_id": survivor.get("survivor_queue_id"),
                    "dedup_spec_id": survivor.get("dedup_spec_id"),
                    "queue_status": survivor.get("queue_status"),
                    "branch_local_action": survivor.get("branch_local_action"),
                    "request_id": request_id,
                    "member_status": "TARGET_REQUEST_ID_JOINED",
                    "target_context": {
                        key: target.get(key)
                        for key in [
                            "route_c_symbol",
                            "route_c_queue_id",
                            "route_c_primitive_flag",
                            "route_c_mechanism_family",
                            "source_symbol",
                            "source_date",
                            "source_proxy_family",
                            "source_silence_status",
                            "candidate_replay_bucket",
                            "command_feature_bucket",
                            "proxy_target_status",
                            "horizon_id",
                            "event15_record_count",
                            "event_boundary_record_count",
                            "route_c_future_change_per_current_range",
                            "route_c_delta_aligned_with_future",
                        ]
                    },
                }
            )
    return rows


def build_scope_rows(
    survivors: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline_stats = row_stats(exact_rows)
    rows: list[dict[str, Any]] = []
    for survivor in survivors:
        target_rows = rows_from_request_ids(targets_by_request, survivor.get("dedup_request_ids", []))
        target_stats = row_stats(target_rows)
        for axes in all_axis_combinations():
            controls = control_rows_for_axes(exact_rows, target_rows, axes)
            control_stats = row_stats(controls)
            rows.append(
                {
                    "scope_row_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-SCOPE-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "survivor_queue_id": survivor.get("survivor_queue_id"),
                    "dedup_spec_id": survivor.get("dedup_spec_id"),
                    "branch_local_action": survivor.get("branch_local_action"),
                    "queue_status": survivor.get("queue_status"),
                    "control_scope": scope_name(axes),
                    "control_axes": list(axes),
                    "target_rows": target_stats,
                    "proxy_control_rows": control_stats,
                    "all_exact_baseline_rows": baseline_stats,
                    "target_alignment_delta_vs_proxy_control": numeric_delta(
                        target_stats.get("route_alignment_share"),
                        control_stats.get("route_alignment_share"),
                    ),
                    "proxy_context_alignment_delta_vs_all_exact": numeric_delta(
                        control_stats.get("route_alignment_share"),
                        baseline_stats.get("route_alignment_share"),
                    ),
                    "mean_future_change_delta_vs_proxy_control": numeric_delta(
                        target_stats.get("mean_route_c_future_change_per_current_range"),
                        control_stats.get("mean_route_c_future_change_per_current_range"),
                    ),
                    "scope_status": verdict_vs_control(target_stats, control_stats),
                    "proxy_context_status": context_verdict(control_stats, baseline_stats),
                }
            )
    return rows


def build_axis_split_rows(
    survivors: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    baseline_stats = row_stats(exact_rows)
    for survivor in survivors:
        target_rows = rows_from_request_ids(targets_by_request, survivor.get("dedup_request_ids", []))
        for axis in [*CONTROL_AXES, *STATE_SPLIT_AXES]:
            for value, count in sorted(Counter(row.get(axis) for row in target_rows).items(), key=lambda item: str(item[0])):
                subset = [row for row in target_rows if row.get(axis) == value]
                leaveout = [row for row in target_rows if row.get(axis) != value]
                subset_stats = row_stats(subset)
                leaveout_stats = row_stats(leaveout)
                if axis in CONTROL_AXES:
                    controls = [
                        row for row in exact_rows
                        if row.get(axis) == value and str(row.get("request_id")) not in survivor.get("dedup_request_ids", [])
                    ]
                    control_stats = row_stats(controls)
                    split_status = verdict_vs_control(subset_stats, control_stats).replace("SEALED_PROXY_", "AXIS_SPLIT_")
                else:
                    control_stats = row_stats([])
                    split_status = "AXIS_SPLIT_STATE_AXIS_NO_EXACT_FEATURE_CONTROL"
                rows.append(
                    {
                        "axis_split_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-AXIS-SPLIT-{len(rows) + 1:05d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "survivor_queue_id": survivor.get("survivor_queue_id"),
                        "dedup_spec_id": survivor.get("dedup_spec_id"),
                        "branch_local_action": survivor.get("branch_local_action"),
                        "queue_status": survivor.get("queue_status"),
                        "axis": axis,
                        "axis_value": value,
                        "axis_value_rows": count,
                        "axis_value_share": count / len(target_rows) if target_rows else None,
                        "subset_rows": subset_stats,
                        "leaveout_rows": leaveout_stats,
                        "axis_proxy_control_rows": control_stats,
                        "all_exact_baseline_rows": baseline_stats,
                        "subset_alignment_delta_vs_axis_control": numeric_delta(
                            subset_stats.get("route_alignment_share"),
                            control_stats.get("route_alignment_share"),
                        ),
                        "split_status": split_status,
                        "next_same_resource_action": (
                            "split/challenge this axis before stronger interpretation"
                            if count and len(target_rows) and count / len(target_rows) > 0.75
                            else "preserve split row for proxy packet and question ledger"
                        ),
                    }
                )
    return rows


def build_capture_schema_rows(survivors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for survivor in survivors:
        for field, purpose in CAPTURE_FIELDS:
            field_role = (
                "research_label_only_not_decision_feature"
                if field in {"route_c_future_change_per_current_range", "route_c_delta_aligned_with_future"}
                else "source_activity_feature_or_provenance"
            )
            rows.append(
                {
                    "capture_schema_row_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-CAPTURE-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "survivor_queue_id": survivor.get("survivor_queue_id"),
                    "dedup_spec_id": survivor.get("dedup_spec_id"),
                    "queue_status": survivor.get("queue_status"),
                    "field_name": field,
                    "field_role": field_role,
                    "field_purpose": purpose,
                    "required_for_next_packet": True,
                    "next_same_resource_action": (
                        "use current proxy-target and source-join ledgers now; add to future capture schema without stopping"
                    ),
                }
            )
    return rows


def packet_status_for_spec(
    survivor: dict[str, Any],
    target_rows: list[dict[str, Any]],
    spec_scope_rows: list[dict[str, Any]],
    spec_axis_rows: list[dict[str, Any]],
) -> str:
    target_n = len(target_rows)
    concentrated = concentration_axes(target_rows)
    viable_scopes = [
        row for row in spec_scope_rows
        if int(row.get("proxy_control_rows", {}).get("n") or 0) >= 20 and target_n >= 5
    ]
    avoid_scopes = [
        row for row in viable_scopes
        if str(row.get("scope_status", "")).endswith("AVOID_DIRECTION_VS_PROXY_CONTROL")
    ]
    context_avoid_scopes = [
        row for row in viable_scopes
        if row.get("proxy_context_status") == "PROXY_CONTEXT_AVOID_DIRECTION_VS_ALL_EXACT"
    ]
    concentrated_splits = [row for row in spec_axis_rows if (row.get("axis_value_share") or 0.0) > 0.75]
    if survivor.get("branch_local_action") == "source_quality_event15_empty_proxy_state":
        if concentrated_splits:
            return "EVENT15_SOURCE_STATE_CONCENTRATED_AXIS_CAPTURE_PRIORITY"
        return "EVENT15_SOURCE_STATE_PROXY_CONTROL_PACKET_OPEN"
    if target_n < 5:
        return "AVOID_PROXY_TARGET_TOO_SMALL_CAPTURE_FIRST"
    if concentrated:
        return "AVOID_PROXY_CONCENTRATED_AXIS_SPLIT_REQUIRED"
    if not viable_scopes:
        return "AVOID_PROXY_NO_VIABLE_CURRENT_CONTROL_SCOPE"
    avoid_share = len(avoid_scopes) / len(viable_scopes)
    context_share = len(context_avoid_scopes) / len(viable_scopes)
    if avoid_share >= 0.75 and context_share >= 0.25:
        return "AVOID_PROXY_BROAD_CURRENT_DATA_CHALLENGER_QUEUE"
    if avoid_share >= 0.50:
        return "AVOID_PROXY_PARTIAL_CURRENT_DATA_CHALLENGER_QUEUE"
    if avoid_scopes:
        return "AVOID_PROXY_WEAK_CURRENT_DATA_CHALLENGER_QUEUE"
    return "AVOID_PROXY_NOT_REPEATED_BY_COMBINATORIAL_CONTEXT"


def build_spec_rows(
    survivors: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    broader_rows: list[dict[str, Any]],
    concentration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scopes_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scope_rows:
        scopes_by_spec[str(row["dedup_spec_id"])].append(row)
    axes_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in axis_rows:
        axes_by_spec[str(row["dedup_spec_id"])].append(row)
    broader_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in broader_rows:
        broader_by_spec[str(row["dedup_spec_id"])].append(row)
    stress_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in concentration_rows:
        stress_by_spec[str(row["dedup_spec_id"])].append(row)

    rows: list[dict[str, Any]] = []
    for survivor in survivors:
        spec_id = str(survivor["dedup_spec_id"])
        target_rows = rows_from_request_ids(targets_by_request, survivor.get("dedup_request_ids", []))
        spec_scopes = scopes_by_spec[spec_id]
        spec_axes = axes_by_spec[spec_id]
        viable_scopes = [
            row for row in spec_scopes
            if int(row.get("proxy_control_rows", {}).get("n") or 0) >= 20 and len(target_rows) >= 5
        ]
        avoid_scopes = [
            row for row in viable_scopes
            if str(row.get("scope_status", "")).endswith("AVOID_DIRECTION_VS_PROXY_CONTROL")
        ]
        context_avoid_scopes = [
            row for row in viable_scopes
            if row.get("proxy_context_status") == "PROXY_CONTEXT_AVOID_DIRECTION_VS_ALL_EXACT"
        ]
        concentrated = concentration_axes(target_rows)
        packet_status = packet_status_for_spec(survivor, target_rows, spec_scopes, spec_axes)
        rows.append(
            {
                "sealed_proxy_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "survivor_queue_id": survivor.get("survivor_queue_id"),
                "dedup_spec_id": spec_id,
                "branch_local_action": survivor.get("branch_local_action"),
                "queue_status": survivor.get("queue_status"),
                "dedup_request_ids": survivor.get("dedup_request_ids", []),
                "source_spec_ids": survivor.get("source_spec_ids", []),
                "target_rows": row_stats(target_rows),
                "concentrated_axes_gt_75pct": concentrated,
                "full_combinatorial_scope_count": len(spec_scopes),
                "viable_scope_count": len(viable_scopes),
                "target_avoid_scope_count": len(avoid_scopes),
                "target_avoid_scope_share": len(avoid_scopes) / len(viable_scopes) if viable_scopes else None,
                "proxy_context_avoid_scope_count": len(context_avoid_scopes),
                "proxy_context_avoid_scope_share": len(context_avoid_scopes) / len(viable_scopes) if viable_scopes else None,
                "axis_split_rows": len(spec_axes),
                "concentrated_axis_split_rows": sum(1 for row in spec_axes if (row.get("axis_value_share") or 0.0) > 0.75),
                "prior_broader_control_verdict_counts": counter_dict(row.get("control_verdict") for row in broader_by_spec[spec_id]),
                "prior_concentration_stress_counts": counter_dict(row.get("stress_status") for row in stress_by_spec[spec_id]),
                "packet_status": packet_status,
                "next_same_resource_action": next_action_for_packet_status(packet_status),
            }
        )
    return rows


def next_action_for_packet_status(status: str) -> str:
    if "CONCENTRATED_AXIS" in status:
        return "split by concentrated axis and rerun same proxy packet before stronger interpretation"
    if status == "AVOID_PROXY_BROAD_CURRENT_DATA_CHALLENGER_QUEUE":
        return "materialize branch-local no-API challenger design and sealed historical/proxy test inputs"
    if status.startswith("AVOID_PROXY_PARTIAL") or status.startswith("AVOID_PROXY_WEAK"):
        return "deepen proxy controls by axis, source-date, and symbol before challenger design"
    if status.startswith("EVENT15_SOURCE_STATE"):
        return "broaden source-state controls and capture schema from current exact rows"
    return "preserve failure intelligence and route to broader data/source proxy search"


def build_bucket_rows(
    spec_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    axis_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets = [
        ("packet_status", counter_dict(row.get("packet_status") for row in spec_rows)),
        ("queue_status", counter_dict(row.get("queue_status") for row in spec_rows)),
        ("branch_local_action", counter_dict(row.get("branch_local_action") for row in spec_rows)),
        ("scope_status", counter_dict(row.get("scope_status") for row in scope_rows)),
        ("proxy_context_status", counter_dict(row.get("proxy_context_status") for row in scope_rows)),
        ("axis_split_status", counter_dict(row.get("split_status") for row in axis_rows)),
        ("capture_field_role", counter_dict(row.get("field_role") for row in capture_rows)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(spec_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]], axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "packet_status_next_action",
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "packet_status": spec.get("packet_status"),
                "question": "What immediate same-resource computation resolves this sealed/proxy packet status?",
                "next_action": spec.get("next_same_resource_action"),
            }
        )
    for scope in scope_rows:
        if "UNDERPOWERED" in str(scope.get("scope_status")) or "UNDERPOWERED" in str(scope.get("proxy_context_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "underpowered_proxy_scope",
                    "dedup_spec_id": scope.get("dedup_spec_id"),
                    "control_scope": scope.get("control_scope"),
                    "question": "Can this underpowered scope be repaired through current exact rows, broader axes, or source acquisition rather than waiting?",
                    "next_action": "use broader axis combinations, source-date/symbol splits, exact source search, or capture-schema proxy rows now",
                }
            )
    for axis in axis_rows:
        if (axis.get("axis_value_share") or 0.0) > 0.75 or "STATE_AXIS" in str(axis.get("split_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SEALED-PROXY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "axis_split_or_state_capture",
                    "dedup_spec_id": axis.get("dedup_spec_id"),
                    "axis": axis.get("axis"),
                    "axis_value": axis.get("axis_value"),
                    "question": "Does this axis explain the apparent source-quality signal or require capture-schema repair?",
                    "next_action": axis.get("next_same_resource_action"),
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_packet_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_packet_result", "created"),
        (SPEC_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_spec_ledger", "created"),
        (SCOPE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_scope_ledger", "created"),
        (AXIS_SPLIT_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_axis_split_ledger", "created"),
        (MEMBER_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_member_ledger", "created"),
        (CAPTURE_SCHEMA_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_capture_schema_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_packet_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], packet_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_packet",
        "status": "done",
        "route": "source_silence_microcluster_survivor_sealed_proxy_packet",
        "details": "Built full combinatorial proxy scope, axis split, member, and capture-schema packet for every source-activity survivor.",
        "counts": counts,
        "packet_status_counts": packet_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SPEC_LEDGER),
            relative(SCOPE_LEDGER),
            relative(AXIS_SPLIT_LEDGER),
            relative(MEMBER_LEDGER),
            relative(CAPTURE_SCHEMA_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], packet_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Sealed/Proxy Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local source-control/proxy packet only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Packet Status", ""])
    for key, value in sorted(packet_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Split concentrated event15/source states by the explicit axis-split ledger.",
            "- Convert broad or partial avoid proxy statuses into branch-local no-API challenger designs only after exact axis splits.",
            "- Use capture-schema rows as immediate source/proxy acquisition requirements, not as a waiting condition.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets = read_jsonl(PROXY_TARGET_LEDGER)
    dedup_specs = read_jsonl(DEDUP_SPEC_LEDGER)
    broader_controls = read_jsonl(BROADER_CONTROL_LEDGER)
    concentration_rows = read_jsonl(CONCENTRATION_STRESS_LEDGER)
    survivors = read_jsonl(SURVIVOR_QUEUE_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in targets}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]

    member_rows = build_member_rows(survivors, targets_by_request)
    scope_rows = build_scope_rows(survivors, targets_by_request, exact_rows)
    axis_rows = build_axis_split_rows(survivors, targets_by_request, exact_rows)
    capture_rows = build_capture_schema_rows(survivors)
    spec_rows = build_spec_rows(
        survivors,
        targets_by_request,
        scope_rows,
        axis_rows,
        broader_controls,
        concentration_rows,
    )
    bucket_rows = build_bucket_rows(spec_rows, scope_rows, axis_rows, capture_rows)
    question_rows = build_question_rows(spec_rows, scope_rows, axis_rows)
    packet_counts = counter_dict(row.get("packet_status") for row in spec_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "proxy_target_input_rows": len(targets),
        "dedup_spec_input_rows": len(dedup_specs),
        "broader_control_input_rows": len(broader_controls),
        "concentration_stress_input_rows": len(concentration_rows),
        "survivor_queue_input_rows": len(survivors),
        "avoid_survivor_input_rows": sum(1 for row in survivors if row.get("branch_local_action") == "source_quality_avoid_challenger_candidate"),
        "event15_survivor_input_rows": sum(1 for row in survivors if row.get("branch_local_action") == "source_quality_event15_empty_proxy_state"),
        "sealed_proxy_spec_rows": len(spec_rows),
        "sealed_proxy_scope_rows": len(scope_rows),
        "sealed_proxy_axis_split_rows": len(axis_rows),
        "sealed_proxy_member_rows": len(member_rows),
        "sealed_proxy_capture_schema_rows": len(capture_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "control_axis_count": len(CONTROL_AXES),
        "control_axis_combination_count": len(all_axis_combinations()),
        "capture_field_count": len(CAPTURE_FIELDS),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_sealed_proxy_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_PACKET_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "packet_status_counts": packet_counts,
        "queue_status_counts": counter_dict(row.get("queue_status") for row in spec_rows),
        "scope_status_counts": counter_dict(row.get("scope_status") for row in scope_rows),
        "proxy_context_status_counts": counter_dict(row.get("proxy_context_status") for row in scope_rows),
        "axis_split_status_counts": counter_dict(row.get("split_status") for row in axis_rows),
        "capture_field_role_counts": counter_dict(row.get("field_role") for row in capture_rows),
        "not_completion": "This sealed/proxy source-activity packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "split concentrated event15/source states by explicit axis split rows",
            "convert broad/partial avoid proxy statuses into no-API challenger designs only after axis repair",
            "use capture-schema rows for immediate source/proxy acquisition and recomputation",
        ],
    }
    write_jsonl(SPEC_LEDGER, spec_rows)
    write_jsonl(SCOPE_LEDGER, scope_rows)
    write_jsonl(AXIS_SPLIT_LEDGER, axis_rows)
    write_jsonl(MEMBER_LEDGER, member_rows)
    write_jsonl(CAPTURE_SCHEMA_LEDGER, capture_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, packet_counts)
    write_summary(generated_utc, counts, packet_counts)
    print(json.dumps({"ok": True, "counts": counts, "packet_status_counts": packet_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
