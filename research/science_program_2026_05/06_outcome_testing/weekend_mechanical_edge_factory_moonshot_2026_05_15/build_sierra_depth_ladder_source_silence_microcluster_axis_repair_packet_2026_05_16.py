#!/usr/bin/env python3
"""Repair concentrated axes from the source-silence sealed/proxy packet."""

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
SEALED_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_SPEC_LEDGER_{STAMP}.jsonl"
SEALED_SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_SCOPE_LEDGER_{STAMP}.jsonl"
SEALED_AXIS_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_AXIS_SPLIT_LEDGER_{STAMP}.jsonl"
SEALED_MEMBER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_MEMBER_LEDGER_{STAMP}.jsonl"
SEALED_CAPTURE_SCHEMA_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SEALED_PROXY_CAPTURE_SCHEMA_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_PACKET_RESULT_{STAMP}.json"
AXIS_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_TARGET_LEDGER_{STAMP}.jsonl"
PARENT_SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_PARENT_SCOPE_LEDGER_{STAMP}.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_DECISION_LEDGER_{STAMP}.jsonl"
SPEC_STATUS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_SPEC_STATUS_LEDGER_{STAMP}.jsonl"
CAPTURE_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_CAPTURE_REQUIREMENT_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_PACKET_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local concentrated-axis repair packet only; source-control/design "
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

STATE_AXES = [
    "candidate_replay_bucket",
    "proxy_target_status",
    "source_silence_status",
]

CAPTURE_PRIORITY_FIELDS = {
    "candidate_replay_bucket",
    "proxy_target_status",
    "source_silence_status",
    "event15_record_count",
    "event_boundary_record_count",
    "file_first_record_utc",
    "file_last_record_utc",
    "command_feature_bucket",
    "source_symbol",
    "source_date",
}


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


def all_combinations(axes: list[str]) -> list[tuple[str, ...]]:
    combos: list[tuple[str, ...]] = [()]
    for size in range(1, len(axes) + 1):
        combos.extend(itertools.combinations(axes, size))
    return combos


def axis_values(rows: list[dict[str, Any]], axis: str) -> set[Any]:
    return {row.get(axis) for row in rows if row.get(axis) is not None}


def control_rows_for_axes(exact_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], axes: tuple[str, ...]) -> list[dict[str, Any]]:
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


def verdict_vs_control(target_stats: dict[str, Any], control_stats: dict[str, Any], prefix: str) -> str:
    target_n = int(target_stats.get("n") or 0)
    control_n = int(control_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    control_align = control_stats.get("route_alignment_share")
    if target_n < 5:
        return f"{prefix}_TARGET_UNDERPOWERED_N_LT_5"
    if target_n < 20:
        sample_prefix = f"{prefix}_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = f"{prefix}_TARGET_N_OK"
    if control_n < 5:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_5"
    if control_n < 20:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_20"
    if target_align is None or control_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < control_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_PARENT_CONTROL"
    if target_align > control_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_PARENT_CONTROL"
    return f"{sample_prefix}_NEAR_PARENT_CONTROL"


def rows_from_request_ids(rows_by_request: dict[str, dict[str, Any]], request_ids: list[str]) -> list[dict[str, Any]]:
    return [rows_by_request[request_id] for request_id in request_ids if request_id in rows_by_request]


def target_axis_rows(axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in axis_rows:
        axis = str(row.get("axis"))
        share_value = safe_float(row.get("axis_value_share")) or 0.0
        if share_value > 0.75:
            rows.append(row)
        elif axis in STATE_AXES and row.get("split_status") == "AXIS_SPLIT_STATE_AXIS_NO_EXACT_FEATURE_CONTROL":
            rows.append(row)
    return rows


def build_axis_target_rows(axis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in target_axis_rows(axis_rows):
        axis = str(row.get("axis"))
        share_value = safe_float(row.get("axis_value_share")) or 0.0
        if axis in STATE_AXES:
            target_status = "STATE_AXIS_REQUIRES_CAPTURE_SCHEMA_OR_SOURCE_PROXY"
        elif share_value > 0.75:
            target_status = "CONTROL_AXIS_CONCENTRATED_VALUE_REQUIRES_PARENT_RETEST"
        else:
            target_status = "AXIS_ROW_RETAINED_FOR_REPAIR_CONTEXT"
        rows.append(
            {
                "axis_target_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-TARGET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_axis_split_id": row.get("axis_split_id"),
                "survivor_queue_id": row.get("survivor_queue_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "branch_local_action": row.get("branch_local_action"),
                "queue_status": row.get("queue_status"),
                "axis": axis,
                "axis_value": row.get("axis_value"),
                "axis_value_rows": row.get("axis_value_rows"),
                "axis_value_share": row.get("axis_value_share"),
                "source_split_status": row.get("split_status"),
                "axis_target_status": target_status,
                "next_same_resource_action": next_action_for_axis_target(target_status),
            }
        )
    return rows


def next_action_for_axis_target(status: str) -> str:
    if status == "STATE_AXIS_REQUIRES_CAPTURE_SCHEMA_OR_SOURCE_PROXY":
        return "materialize source-state capture/proxy requirements from existing ledgers and rerun source-state controls"
    if status == "CONTROL_AXIS_CONCENTRATED_VALUE_REQUIRES_PARENT_RETEST":
        return "retest every parent-axis control combination excluding this concentrated axis"
    return "preserve as repair context"


def scope_name(axes: tuple[str, ...]) -> str:
    return "all_exact_features" if not axes else "parent_same_" + "_".join(axes)


def build_parent_scope_rows(
    axis_targets: list[dict[str, Any]],
    spec_rows: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    spec_by_id = {str(row["dedup_spec_id"]): row for row in spec_rows}
    rows: list[dict[str, Any]] = []
    for axis_target in axis_targets:
        spec = spec_by_id[str(axis_target["dedup_spec_id"])]
        all_target_rows = rows_from_request_ids(targets_by_request, spec.get("dedup_request_ids", []))
        subset_target_rows = [
            row for row in all_target_rows
            if row.get(str(axis_target["axis"])) == axis_target.get("axis_value")
        ]
        if axis_target["axis"] in CONTROL_AXES:
            parent_axes = [axis for axis in CONTROL_AXES if axis != axis_target["axis"]]
        else:
            parent_axes = list(CONTROL_AXES)
        for axes in all_combinations(parent_axes):
            controls = control_rows_for_axes(exact_rows, subset_target_rows, axes)
            target_stats = row_stats(subset_target_rows)
            control_stats = row_stats(controls)
            status = (
                "PARENT_SCOPE_STATE_AXIS_NO_DIRECT_EXACT_CONTROL"
                if axis_target["axis"] in STATE_AXES
                else verdict_vs_control(target_stats, control_stats, "PARENT_SCOPE")
            )
            rows.append(
                {
                    "parent_scope_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-PARENT-SCOPE-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "axis_target_id": axis_target.get("axis_target_id"),
                    "dedup_spec_id": axis_target.get("dedup_spec_id"),
                    "axis": axis_target.get("axis"),
                    "axis_value": axis_target.get("axis_value"),
                    "parent_control_scope": scope_name(axes),
                    "parent_control_axes": list(axes),
                    "subset_target_rows": target_stats,
                    "parent_control_rows": control_stats,
                    "target_alignment_delta_vs_parent_control": numeric_delta(
                        target_stats.get("route_alignment_share"),
                        control_stats.get("route_alignment_share"),
                    ),
                    "parent_scope_status": status,
                }
            )
    return rows


def build_decision_rows(axis_targets: list[dict[str, Any]], parent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_by_axis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parent_rows:
        parent_by_axis[str(row["axis_target_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for target in axis_targets:
        parent = parent_by_axis[str(target["axis_target_id"])]
        status_counts = counter_dict(row.get("parent_scope_status") for row in parent)
        usable_parent = [
            row for row in parent
            if "UNDERPOWERED" not in str(row.get("parent_scope_status"))
            and "NO_DIRECT_EXACT_CONTROL" not in str(row.get("parent_scope_status"))
        ]
        avoid_parent = [
            row for row in usable_parent
            if str(row.get("parent_scope_status", "")).endswith("AVOID_DIRECTION_VS_PARENT_CONTROL")
        ]
        underpowered_avoid_parent = [
            row for row in parent
            if str(row.get("parent_scope_status", "")).endswith("AVOID_DIRECTION_VS_PARENT_CONTROL")
        ]
        if target.get("axis") in STATE_AXES:
            decision_status = "AXIS_REPAIR_STATE_CAPTURE_OR_SOURCE_PROXY_REQUIRED"
        elif avoid_parent:
            decision_status = "AXIS_REPAIR_AVOID_DIRECTION_SURVIVES_PARENT_SCOPES"
        elif underpowered_avoid_parent:
            decision_status = "AXIS_REPAIR_UNDERPOWERED_AVOID_PARENT_CONTEXT_REQUIRES_BROADER_SOURCE_OR_PROXY"
        elif not usable_parent:
            decision_status = "AXIS_REPAIR_NO_USABLE_PARENT_SCOPE_CURRENT_DATA"
        else:
            decision_status = "AXIS_REPAIR_AVOID_DIRECTION_DOES_NOT_SURVIVE_PARENT_SCOPES"
        rows.append(
            {
                "axis_repair_decision_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-DECISION-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "axis_target_id": target.get("axis_target_id"),
                "dedup_spec_id": target.get("dedup_spec_id"),
                "branch_local_action": target.get("branch_local_action"),
                "axis": target.get("axis"),
                "axis_value": target.get("axis_value"),
                "axis_value_share": target.get("axis_value_share"),
                "parent_scope_rows": len(parent),
                "usable_parent_scope_rows": len(usable_parent),
                "avoid_parent_scope_rows": len(avoid_parent),
                "underpowered_avoid_parent_scope_rows": len(underpowered_avoid_parent),
                "parent_scope_status_counts": status_counts,
                "decision_status": decision_status,
                "next_same_resource_action": next_action_for_decision(decision_status),
            }
        )
    return rows


def next_action_for_decision(status: str) -> str:
    if status == "AXIS_REPAIR_AVOID_DIRECTION_SURVIVES_PARENT_SCOPES":
        return "feed surviving parent-axis status into branch-local no-API challenger design with no promotion claim"
    if status == "AXIS_REPAIR_UNDERPOWERED_AVOID_PARENT_CONTEXT_REQUIRES_BROADER_SOURCE_OR_PROXY":
        return "broaden exact source/proxy denominators around this avoid-looking parent context now"
    if status == "AXIS_REPAIR_STATE_CAPTURE_OR_SOURCE_PROXY_REQUIRED":
        return "build source-state capture/proxy rows and rerun current source controls"
    if status == "AXIS_REPAIR_NO_USABLE_PARENT_SCOPE_CURRENT_DATA":
        return "broaden parent controls or exact source acquisition from current/free/local routes"
    return "preserve as killed/weak axis branch and test alternate axes"


def build_spec_status_rows(spec_rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        decisions_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        spec_decisions = decisions_by_spec[str(spec["dedup_spec_id"])]
        counts = counter_dict(row.get("decision_status") for row in spec_decisions)
        if counts.get("AXIS_REPAIR_AVOID_DIRECTION_SURVIVES_PARENT_SCOPES"):
            status = "SPEC_AXIS_REPAIR_HAS_SURVIVING_AVOID_PARENT_CONTEXT"
        elif counts.get("AXIS_REPAIR_UNDERPOWERED_AVOID_PARENT_CONTEXT_REQUIRES_BROADER_SOURCE_OR_PROXY"):
            status = "SPEC_AXIS_REPAIR_UNDERPOWERED_AVOID_CONTEXT_NEEDS_SOURCE_OR_PROXY"
        elif counts.get("AXIS_REPAIR_STATE_CAPTURE_OR_SOURCE_PROXY_REQUIRED") and len(counts) == 1:
            status = "SPEC_AXIS_REPAIR_STATE_CAPTURE_ONLY"
        elif counts.get("AXIS_REPAIR_NO_USABLE_PARENT_SCOPE_CURRENT_DATA"):
            status = "SPEC_AXIS_REPAIR_NEEDS_BROADER_SOURCE_OR_PROXY"
        else:
            status = "SPEC_AXIS_REPAIR_NO_SURVIVING_AVOID_PARENT_CONTEXT"
        rows.append(
            {
                "axis_repair_spec_status_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-SPEC-STATUS-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "sealed_proxy_spec_id": spec.get("sealed_proxy_spec_id"),
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "branch_local_action": spec.get("branch_local_action"),
                "prior_packet_status": spec.get("packet_status"),
                "axis_repair_decision_rows": len(spec_decisions),
                "axis_repair_decision_status_counts": counts,
                "spec_repair_status": status,
                "next_same_resource_action": next_action_for_spec_status(status),
            }
        )
    return rows


def next_action_for_spec_status(status: str) -> str:
    if status == "SPEC_AXIS_REPAIR_HAS_SURVIVING_AVOID_PARENT_CONTEXT":
        return "materialize branch-local no-API challenger design and exact source/proxy stress rows"
    if status == "SPEC_AXIS_REPAIR_UNDERPOWERED_AVOID_CONTEXT_NEEDS_SOURCE_OR_PROXY":
        return "broaden exact source/proxy denominators around underpowered avoid parent contexts now"
    if status == "SPEC_AXIS_REPAIR_STATE_CAPTURE_ONLY":
        return "build source-state capture/proxy control packet; do not wait for forward rows"
    if status == "SPEC_AXIS_REPAIR_NEEDS_BROADER_SOURCE_OR_PROXY":
        return "run broader source/proxy acquisition or parent-axis expansion now"
    return "preserve as failure intelligence and continue alternate route families"


def build_capture_requirement_rows(axis_targets: list[dict[str, Any]], capture_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    capture_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in capture_rows:
        capture_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for axis_target in axis_targets:
        for capture in capture_by_spec[str(axis_target["dedup_spec_id"])]:
            field = str(capture.get("field_name"))
            priority = (
                "AXIS_REPAIR_CAPTURE_PRIORITY"
                if axis_target.get("axis") in STATE_AXES or field in CAPTURE_PRIORITY_FIELDS
                else "AXIS_REPAIR_CAPTURE_CONTEXT"
            )
            rows.append(
                {
                    "capture_requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-CAPTURE-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "axis_target_id": axis_target.get("axis_target_id"),
                    "dedup_spec_id": axis_target.get("dedup_spec_id"),
                    "axis": axis_target.get("axis"),
                    "axis_value": axis_target.get("axis_value"),
                    "field_name": field,
                    "field_role": capture.get("field_role"),
                    "capture_priority": priority,
                    "source_capture_row": capture.get("capture_schema_row_id"),
                    "next_same_resource_action": "use existing source/proxy ledgers now and add the field to future capture without stopping",
                }
            )
    return rows


def build_bucket_rows(
    axis_targets: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    spec_status_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets = [
        ("axis_target_status", counter_dict(row.get("axis_target_status") for row in axis_targets)),
        ("axis_target_axis", counter_dict(row.get("axis") for row in axis_targets)),
        ("parent_scope_status", counter_dict(row.get("parent_scope_status") for row in parent_rows)),
        ("decision_status", counter_dict(row.get("decision_status") for row in decisions)),
        ("spec_repair_status", counter_dict(row.get("spec_repair_status") for row in spec_status_rows)),
        ("capture_priority", counter_dict(row.get("capture_priority") for row in capture_rows)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(decisions: list[dict[str, Any]], spec_status_rows: list[dict[str, Any]], parent_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "axis_decision_next_action",
                "dedup_spec_id": decision.get("dedup_spec_id"),
                "axis": decision.get("axis"),
                "axis_value": decision.get("axis_value"),
                "decision_status": decision.get("decision_status"),
                "question": "What immediate source/proxy/control computation resolves this concentrated axis?",
                "next_action": decision.get("next_same_resource_action"),
            }
        )
    for spec in spec_status_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "spec_repair_next_action",
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "spec_repair_status": spec.get("spec_repair_status"),
                "question": "Does the repaired spec become a branch-local challenger design, source-state capture task, or killed/weak branch?",
                "next_action": spec.get("next_same_resource_action"),
            }
        )
    for parent in parent_rows:
        if "UNDERPOWERED" in str(parent.get("parent_scope_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-AXIS-REPAIR-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "underpowered_parent_scope",
                    "dedup_spec_id": parent.get("dedup_spec_id"),
                    "axis": parent.get("axis"),
                    "parent_control_scope": parent.get("parent_control_scope"),
                    "question": "Can this parent scope be repaired by broader axes, exact source acquisition, or source-state proxy rows now?",
                    "next_action": "expand parent control axes, source roots, or capture-schema proxy rows; do not wait",
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_axis_repair_packet_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_axis_repair_packet_result", "created"),
        (AXIS_TARGET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_target_ledger", "created"),
        (PARENT_SCOPE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_parent_scope_ledger", "created"),
        (DECISION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_decision_ledger", "created"),
        (SPEC_STATUS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_spec_status_ledger", "created"),
        (CAPTURE_REQUIREMENT_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_capture_requirement_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_axis_repair_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_axis_repair_packet_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], spec_status_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_axis_repair_packet",
        "status": "done",
        "route": "source_silence_microcluster_concentrated_axis_repair",
        "details": "Retested every concentrated/source-state axis through parent-scope controls and capture requirements.",
        "counts": counts,
        "spec_repair_status_counts": spec_status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(AXIS_TARGET_LEDGER),
            relative(PARENT_SCOPE_LEDGER),
            relative(DECISION_LEDGER),
            relative(SPEC_STATUS_LEDGER),
            relative(CAPTURE_REQUIREMENT_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], spec_status_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Axis Repair Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local concentrated-axis repair only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Repair Status", ""])
    for key, value in sorted(spec_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Convert specs with surviving avoid parent context into branch-local no-API challenger designs and exact source/proxy stress rows.",
            "- Convert state-capture-only specs into source-state capture/proxy controls now; do not wait for forward rows.",
            "- Broaden underpowered parent scopes through current/free/local source routes or mark exact source requirements.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets = read_jsonl(PROXY_TARGET_LEDGER)
    spec_rows = read_jsonl(SEALED_SPEC_LEDGER)
    sealed_scope_rows = read_jsonl(SEALED_SCOPE_LEDGER)
    axis_split_rows = read_jsonl(SEALED_AXIS_SPLIT_LEDGER)
    member_rows = read_jsonl(SEALED_MEMBER_LEDGER)
    capture_schema_rows = read_jsonl(SEALED_CAPTURE_SCHEMA_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in targets}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    axis_targets = build_axis_target_rows(axis_split_rows)
    parent_scope_rows = build_parent_scope_rows(axis_targets, spec_rows, targets_by_request, exact_rows)
    decision_rows = build_decision_rows(axis_targets, parent_scope_rows)
    spec_status_rows = build_spec_status_rows(spec_rows, decision_rows)
    capture_requirement_rows = build_capture_requirement_rows(axis_targets, capture_schema_rows)
    bucket_rows = build_bucket_rows(axis_targets, parent_scope_rows, decision_rows, spec_status_rows, capture_requirement_rows)
    question_rows = build_question_rows(decision_rows, spec_status_rows, parent_scope_rows)
    spec_status_counts = counter_dict(row.get("spec_repair_status") for row in spec_status_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "proxy_target_input_rows": len(targets),
        "sealed_spec_input_rows": len(spec_rows),
        "sealed_scope_input_rows": len(sealed_scope_rows),
        "sealed_axis_split_input_rows": len(axis_split_rows),
        "sealed_member_input_rows": len(member_rows),
        "sealed_capture_schema_input_rows": len(capture_schema_rows),
        "axis_target_rows": len(axis_targets),
        "parent_scope_rows": len(parent_scope_rows),
        "axis_repair_decision_rows": len(decision_rows),
        "axis_repair_spec_status_rows": len(spec_status_rows),
        "capture_requirement_rows": len(capture_requirement_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_axis_repair_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_PACKET_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "axis_target_status_counts": counter_dict(row.get("axis_target_status") for row in axis_targets),
        "axis_target_axis_counts": counter_dict(row.get("axis") for row in axis_targets),
        "parent_scope_status_counts": counter_dict(row.get("parent_scope_status") for row in parent_scope_rows),
        "axis_repair_decision_status_counts": counter_dict(row.get("decision_status") for row in decision_rows),
        "spec_repair_status_counts": spec_status_counts,
        "capture_priority_counts": counter_dict(row.get("capture_priority") for row in capture_requirement_rows),
        "not_completion": "This concentrated-axis repair packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "materialize no-API challenger designs for specs with surviving avoid parent context",
            "build source-state capture/proxy controls for state-capture-only specs",
            "broaden underpowered parent scopes through exact source/proxy acquisition",
        ],
    }
    write_jsonl(AXIS_TARGET_LEDGER, axis_targets)
    write_jsonl(PARENT_SCOPE_LEDGER, parent_scope_rows)
    write_jsonl(DECISION_LEDGER, decision_rows)
    write_jsonl(SPEC_STATUS_LEDGER, spec_status_rows)
    write_jsonl(CAPTURE_REQUIREMENT_LEDGER, capture_requirement_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, spec_status_counts)
    write_summary(generated_utc, counts, spec_status_counts)
    print(json.dumps({"ok": True, "counts": counts, "spec_repair_status_counts": spec_status_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
