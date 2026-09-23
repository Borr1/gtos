#!/usr/bin/env python3
"""Broaden source/proxy denominators after microcluster axis repair."""

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
AXIS_REPAIR_DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_DECISION_LEDGER_{STAMP}.jsonl"
AXIS_REPAIR_SPEC_STATUS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_SPEC_STATUS_LEDGER_{STAMP}.jsonl"
AXIS_REPAIR_PARENT_SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_PARENT_SCOPE_LEDGER_{STAMP}.jsonl"
AXIS_REPAIR_CAPTURE_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_AXIS_REPAIR_CAPTURE_REQUIREMENT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_PACKET_RESULT_{STAMP}.json"
SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SPEC_LEDGER_{STAMP}.jsonl"
SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SCOPE_LEDGER_{STAMP}.jsonl"
STATE_PROXY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_STATE_PROXY_LEDGER_{STAMP}.jsonl"
CAPTURE_FIELD_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_CAPTURE_FIELD_LEDGER_{STAMP}.jsonl"
SPEC_DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SPEC_DECISION_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_PACKET_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local broader source/proxy denominator expansion only; source-control "
    "and design evidence with no strategy validation, trade outcome, R/PnL, "
    "expectancy, live-readiness, promotion, or live deployment"
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

STATE_AXES = {
    "candidate_replay_bucket",
    "proxy_target_status",
    "source_silence_status",
}

SPEC_REPAIR_STATUSES_REQUIRING_EXPANSION = {
    "SPEC_AXIS_REPAIR_UNDERPOWERED_AVOID_CONTEXT_NEEDS_SOURCE_OR_PROXY",
    "SPEC_AXIS_REPAIR_NEEDS_BROADER_SOURCE_OR_PROXY",
    "SPEC_AXIS_REPAIR_STATE_CAPTURE_ONLY",
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
        "updated_ladder_snapshot_bucket_counts": counter_dict(row.get("updated_ladder_snapshot_bucket") for row in rows),
        "depth_file_exists_counts": counter_dict(row.get("depth_file_exists") for row in rows),
    }


def all_combinations(axes: list[str]) -> list[tuple[str, ...]]:
    combos: list[tuple[str, ...]] = [()]
    for size in range(1, len(axes) + 1):
        combos.extend(itertools.combinations(axes, size))
    return combos


def axis_values(rows: list[dict[str, Any]], axis: str) -> set[Any]:
    return {row.get(axis) for row in rows if row.get(axis) is not None}


def rows_from_request_ids(rows_by_request: dict[str, dict[str, Any]], request_ids: list[str]) -> list[dict[str, Any]]:
    return [rows_by_request[request_id] for request_id in request_ids if request_id in rows_by_request]


def scope_name(axes: tuple[str, ...]) -> str:
    return "all_rows" if not axes else "same_" + "_".join(axes)


def matching_rows(
    denominator_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    axes: tuple[str, ...],
    exclude_request_ids: set[str],
) -> list[dict[str, Any]]:
    if not axes:
        return [row for row in denominator_rows if str(row.get("request_id")) not in exclude_request_ids]
    values_by_axis = {axis: axis_values(target_rows, axis) for axis in axes}
    rows: list[dict[str, Any]] = []
    for row in denominator_rows:
        if str(row.get("request_id")) in exclude_request_ids:
            continue
        if all(row.get(axis) in values_by_axis[axis] for axis in axes):
            rows.append(row)
    return rows


def denominator_families(source_join: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> list[tuple[str, str, list[dict[str, Any]]]]:
    local_depth_rows = [row for row in source_join if bool_value(row.get("depth_file_exists")) is True]
    source_silence_rows = [row for row in source_join if bool_value(row.get("source_silence_joined")) is True]
    missing_depth_rows = [row for row in source_join if bool_value(row.get("depth_file_exists")) is False]
    return [
        ("exact_feature_controls", "exact_ladder_feature_denominator", exact_rows),
        ("local_depth_available_source_proxy", "local_depth_source_proxy_denominator", local_depth_rows),
        ("source_silence_context_proxy", "source_silence_context_denominator", source_silence_rows),
        ("missing_depth_source_gap_route_proxy", "missing_source_date_route_proxy_denominator", missing_depth_rows),
        ("all_route_c_source_join_proxy", "all_route_c_source_join_denominator", source_join),
    ]


def verdict_vs_proxy(target_stats: dict[str, Any], proxy_stats: dict[str, Any], prefix: str) -> str:
    target_n = int(target_stats.get("n") or 0)
    proxy_n = int(proxy_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    proxy_align = proxy_stats.get("route_alignment_share")
    if target_n < 5:
        sample_prefix = f"{prefix}_TARGET_UNDERPOWERED_N_LT_5"
    elif target_n < 20:
        sample_prefix = f"{prefix}_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = f"{prefix}_TARGET_N_OK"
    if proxy_n < 5:
        return f"{sample_prefix}_PROXY_UNDERPOWERED_N_LT_5"
    if proxy_n < 20:
        return f"{sample_prefix}_PROXY_UNDERPOWERED_N_LT_20"
    if target_align is None or proxy_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < proxy_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_BROADER_PROXY"
    if target_align > proxy_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_BROADER_PROXY"
    return f"{sample_prefix}_NEAR_BROADER_PROXY"


def build_spec_rows(
    sealed_specs: list[dict[str, Any]],
    spec_status_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    status_by_spec = {str(row["dedup_spec_id"]): row for row in spec_status_rows}
    decision_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decision_rows:
        decision_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in sealed_specs:
        status = status_by_spec[str(spec["dedup_spec_id"])]
        decisions = decision_by_spec[str(spec["dedup_spec_id"])]
        state_decisions = [row for row in decisions if row.get("axis") in STATE_AXES]
        underpowered_avoid = [
            row for row in decisions
            if row.get("decision_status") == "AXIS_REPAIR_UNDERPOWERED_AVOID_PARENT_CONTEXT_REQUIRES_BROADER_SOURCE_OR_PROXY"
        ]
        rows.append(
            {
                "broader_source_proxy_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "sealed_proxy_spec_id": spec.get("sealed_proxy_spec_id"),
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "survivor_queue_id": spec.get("survivor_queue_id"),
                "branch_local_action": spec.get("branch_local_action"),
                "prior_packet_status": spec.get("packet_status"),
                "axis_repair_spec_status": status.get("spec_repair_status"),
                "expansion_required": status.get("spec_repair_status") in SPEC_REPAIR_STATUSES_REQUIRING_EXPANSION,
                "dedup_request_ids": spec.get("dedup_request_ids", []),
                "target_rows": spec.get("target_rows"),
                "state_axis_decision_count": len(state_decisions),
                "underpowered_avoid_axis_decision_count": len(underpowered_avoid),
                "axis_repair_decision_status_counts": counter_dict(row.get("decision_status") for row in decisions),
                "next_same_resource_action": "run all broader denominator families and state proxy controls now",
            }
        )
    return rows


def build_scope_rows(
    spec_rows: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    denom_families: list[tuple[str, str, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    combos = all_combinations(CONTROL_AXES)
    for spec in spec_rows:
        target_rows = rows_from_request_ids(targets_by_request, spec.get("dedup_request_ids", []))
        target_ids = {str(row.get("request_id")) for row in target_rows}
        target_stats = row_stats(target_rows)
        for family, role, denom_rows in denom_families:
            for axes in combos:
                proxy_rows = matching_rows(denom_rows, target_rows, axes, target_ids)
                proxy_stats = row_stats(proxy_rows)
                status = verdict_vs_proxy(target_stats, proxy_stats, "BROADER_SOURCE_PROXY_SCOPE")
                rows.append(
                    {
                        "broader_source_proxy_scope_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-SCOPE-{len(rows) + 1:05d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "broader_source_proxy_spec_id": spec.get("broader_source_proxy_spec_id"),
                        "dedup_spec_id": spec.get("dedup_spec_id"),
                        "branch_local_action": spec.get("branch_local_action"),
                        "axis_repair_spec_status": spec.get("axis_repair_spec_status"),
                        "denominator_family": family,
                        "denominator_role": role,
                        "denominator_rows": len(denom_rows),
                        "control_scope": scope_name(axes),
                        "control_axes": list(axes),
                        "target_rows": target_stats,
                        "broader_proxy_rows": proxy_stats,
                        "target_alignment_delta_vs_broader_proxy": numeric_delta(
                            target_stats.get("route_alignment_share"),
                            proxy_stats.get("route_alignment_share"),
                        ),
                        "mean_future_change_delta_vs_broader_proxy": numeric_delta(
                            target_stats.get("mean_route_c_future_change_per_current_range"),
                            proxy_stats.get("mean_route_c_future_change_per_current_range"),
                        ),
                        "broader_scope_status": status,
                    }
                )
    return rows


def build_state_proxy_rows(
    decision_rows: list[dict[str, Any]],
    sealed_spec_by_id: dict[str, dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    denom_families: list[tuple[str, str, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    combos = all_combinations(CONTROL_AXES)
    state_decisions = [row for row in decision_rows if row.get("axis") in STATE_AXES]
    for decision in state_decisions:
        spec = sealed_spec_by_id[str(decision["dedup_spec_id"])]
        all_targets = rows_from_request_ids(targets_by_request, spec.get("dedup_request_ids", []))
        axis = str(decision.get("axis"))
        state_targets = [row for row in all_targets if row.get(axis) == decision.get("axis_value")]
        target_ids = {str(row.get("request_id")) for row in state_targets}
        target_stats = row_stats(state_targets)
        for family, role, denom_rows in denom_families:
            for axes in combos:
                proxy_rows = matching_rows(denom_rows, state_targets, axes, target_ids)
                proxy_stats = row_stats(proxy_rows)
                status = verdict_vs_proxy(target_stats, proxy_stats, "SOURCE_STATE_PROXY")
                rows.append(
                    {
                        "state_proxy_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-STATE-{len(rows) + 1:05d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "axis_repair_decision_id": decision.get("axis_repair_decision_id"),
                        "axis_target_id": decision.get("axis_target_id"),
                        "dedup_spec_id": decision.get("dedup_spec_id"),
                        "branch_local_action": decision.get("branch_local_action"),
                        "state_axis": axis,
                        "state_axis_value": decision.get("axis_value"),
                        "denominator_family": family,
                        "denominator_role": role,
                        "denominator_rows": len(denom_rows),
                        "control_scope": scope_name(axes),
                        "control_axes": list(axes),
                        "target_rows": target_stats,
                        "state_proxy_rows": proxy_stats,
                        "target_alignment_delta_vs_state_proxy": numeric_delta(
                            target_stats.get("route_alignment_share"),
                            proxy_stats.get("route_alignment_share"),
                        ),
                        "state_proxy_status": status,
                        "next_same_resource_action": "use this broader state proxy context now; do not wait for forward rows",
                    }
                )
    return rows


def field_non_null_count(rows: list[dict[str, Any]], field: str) -> int:
    count = 0
    for row in rows:
        if field in row and row.get(field) not in (None, "", [], {}):
            count += 1
    return count


def build_capture_field_rows(
    capture_rows: list[dict[str, Any]],
    source_join: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
    exact_rows: list[dict[str, Any]],
    local_depth_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for capture in capture_rows:
        field = str(capture.get("field_name"))
        source_count = field_non_null_count(source_join, field)
        target_count = field_non_null_count(proxy_targets, field)
        exact_count = field_non_null_count(exact_rows, field)
        local_count = field_non_null_count(local_depth_rows, field)
        if target_count:
            status = "CAPTURE_FIELD_AVAILABLE_IN_TARGET_PROXY_ROWS"
        elif source_count:
            status = "CAPTURE_FIELD_AVAILABLE_IN_SOURCE_JOIN_ROWS"
        else:
            status = "CAPTURE_FIELD_NOT_IN_CURRENT_LEDGER_ROUTE_TO_EXTRACTION_SCHEMA"
        rows.append(
            {
                "capture_field_status_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-CAPTURE-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_capture_requirement_id": capture.get("capture_requirement_id"),
                "axis_target_id": capture.get("axis_target_id"),
                "dedup_spec_id": capture.get("dedup_spec_id"),
                "axis": capture.get("axis"),
                "axis_value": capture.get("axis_value"),
                "field_name": field,
                "field_role": capture.get("field_role"),
                "axis_repair_capture_priority": capture.get("capture_priority"),
                "source_join_non_null_count": source_count,
                "proxy_target_non_null_count": target_count,
                "exact_feature_non_null_count": exact_count,
                "local_depth_non_null_count": local_count,
                "capture_field_status": status,
                "next_same_resource_action": next_action_for_capture_field(status),
            }
        )
    return rows


def next_action_for_capture_field(status: str) -> str:
    if status == "CAPTURE_FIELD_AVAILABLE_IN_TARGET_PROXY_ROWS":
        return "use current proxy target rows immediately in state/source controls"
    if status == "CAPTURE_FIELD_AVAILABLE_IN_SOURCE_JOIN_ROWS":
        return "use source-join rows immediately and route sparse target coverage to proxy controls"
    return "materialize extraction/capture schema and use current proxies without stopping"


def best_status_priority(status: str) -> int:
    if "AVOID_DIRECTION_VS_BROADER_PROXY" in status:
        return 0
    if "TARGET_ALIGNED_VS_BROADER_PROXY" in status:
        return 1
    if "NEAR_BROADER_PROXY" in status:
        return 2
    if "PROXY_UNDERPOWERED" in status:
        return 3
    return 4


def build_spec_decision_rows(
    spec_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    state_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scope_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    state_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    capture_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scope_rows:
        scope_by_spec[str(row["dedup_spec_id"])].append(row)
    for row in state_rows:
        state_by_spec[str(row["dedup_spec_id"])].append(row)
    for row in capture_rows:
        capture_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        spec_scopes = scope_by_spec[str(spec["dedup_spec_id"])]
        spec_states = state_by_spec[str(spec["dedup_spec_id"])]
        spec_captures = capture_by_spec[str(spec["dedup_spec_id"])]
        avoid_scope_count = sum(1 for row in spec_scopes if "AVOID_DIRECTION_VS_BROADER_PROXY" in row["broader_scope_status"])
        avoid_state_count = sum(1 for row in spec_states if "AVOID_DIRECTION_VS_BROADER_PROXY" in row["state_proxy_status"])
        target_aligned_scope_count = sum(1 for row in spec_scopes if "TARGET_ALIGNED_VS_BROADER_PROXY" in row["broader_scope_status"])
        missing_capture_count = sum(1 for row in spec_captures if row["capture_field_status"] == "CAPTURE_FIELD_NOT_IN_CURRENT_LEDGER_ROUTE_TO_EXTRACTION_SCHEMA")
        best_scope = sorted(spec_scopes, key=lambda row: (best_status_priority(row["broader_scope_status"]), row["denominator_family"], row["control_scope"]))[0]
        if avoid_scope_count or avoid_state_count:
            status = "SPEC_BROADER_PROXY_AVOID_DIRECTION_REMAINS_DESCRIPTIVE_SOURCE_CONTROL"
        elif target_aligned_scope_count:
            status = "SPEC_BROADER_PROXY_TARGET_ALIGNED_OR_REVERSED_CONTEXT"
        elif missing_capture_count:
            status = "SPEC_BROADER_PROXY_NEEDS_EXTRACTION_SCHEMA_BUT_HAS_CURRENT_PROXY_CONTEXT"
        else:
            status = "SPEC_BROADER_PROXY_NEAR_OR_UNDERPOWERED_CONTEXT"
        rows.append(
            {
                "spec_decision_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-DECISION-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "broader_source_proxy_spec_id": spec.get("broader_source_proxy_spec_id"),
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "branch_local_action": spec.get("branch_local_action"),
                "axis_repair_spec_status": spec.get("axis_repair_spec_status"),
                "broader_scope_rows": len(spec_scopes),
                "state_proxy_rows": len(spec_states),
                "capture_field_rows": len(spec_captures),
                "broader_scope_status_counts": counter_dict(row.get("broader_scope_status") for row in spec_scopes),
                "state_proxy_status_counts": counter_dict(row.get("state_proxy_status") for row in spec_states),
                "capture_field_status_counts": counter_dict(row.get("capture_field_status") for row in spec_captures),
                "avoid_scope_count": avoid_scope_count,
                "avoid_state_proxy_count": avoid_state_count,
                "target_aligned_scope_count": target_aligned_scope_count,
                "missing_capture_field_count": missing_capture_count,
                "best_scope_status": best_scope.get("broader_scope_status"),
                "best_scope_denominator_family": best_scope.get("denominator_family"),
                "best_scope_control_scope": best_scope.get("control_scope"),
                "spec_broader_proxy_decision_status": status,
                "next_same_resource_action": next_action_for_spec_decision(status),
            }
        )
    return rows


def next_action_for_spec_decision(status: str) -> str:
    if status == "SPEC_BROADER_PROXY_AVOID_DIRECTION_REMAINS_DESCRIPTIVE_SOURCE_CONTROL":
        return "feed into branch-local no-API challenger design stress and source acquisition; no validation claim"
    if status == "SPEC_BROADER_PROXY_TARGET_ALIGNED_OR_REVERSED_CONTEXT":
        return "preserve as inverse/failure intelligence and test alternate axes/horizons"
    if status == "SPEC_BROADER_PROXY_NEEDS_EXTRACTION_SCHEMA_BUT_HAS_CURRENT_PROXY_CONTEXT":
        return "write extraction/capture requirements and continue current proxy computations"
    return "keep as weak/near-control source context and broaden other source roots"


def build_bucket_rows(
    spec_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    state_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
    spec_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets = [
        ("axis_repair_spec_status", counter_dict(row.get("axis_repair_spec_status") for row in spec_rows)),
        ("expansion_required", counter_dict(row.get("expansion_required") for row in spec_rows)),
        ("broader_denominator_family", counter_dict(row.get("denominator_family") for row in scope_rows)),
        ("broader_scope_status", counter_dict(row.get("broader_scope_status") for row in scope_rows)),
        ("state_axis", counter_dict(row.get("state_axis") for row in state_rows)),
        ("state_proxy_status", counter_dict(row.get("state_proxy_status") for row in state_rows)),
        ("capture_field_status", counter_dict(row.get("capture_field_status") for row in capture_rows)),
        ("spec_broader_proxy_decision_status", counter_dict(row.get("spec_broader_proxy_decision_status") for row in spec_decisions)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(spec_decisions: list[dict[str, Any]], state_rows: list[dict[str, Any]], capture_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for decision in spec_decisions:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "spec_broader_proxy_next_action",
                "dedup_spec_id": decision.get("dedup_spec_id"),
                "status": decision.get("spec_broader_proxy_decision_status"),
                "question": "Which immediate source/proxy/challenger computation follows from this broader denominator expansion?",
                "next_action": decision.get("next_same_resource_action"),
            }
        )
    for row in state_rows:
        if "PROXY_UNDERPOWERED" in row.get("state_proxy_status", ""):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "state_proxy_underpowered",
                    "dedup_spec_id": row.get("dedup_spec_id"),
                    "state_axis": row.get("state_axis"),
                    "denominator_family": row.get("denominator_family"),
                    "control_scope": row.get("control_scope"),
                    "question": "Can this source-state proxy be broadened through source roots, alternate axes, or exact capture fields now?",
                    "next_action": "broaden denominator family, exact source roots, or capture-schema proxy rows; do not wait",
                }
            )
    for row in capture_rows:
        if row.get("capture_field_status") == "CAPTURE_FIELD_NOT_IN_CURRENT_LEDGER_ROUTE_TO_EXTRACTION_SCHEMA":
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BROADER-SOURCE-PROXY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "capture_field_missing_current_ledger",
                    "dedup_spec_id": row.get("dedup_spec_id"),
                    "field_name": row.get("field_name"),
                    "question": "Which current/free/local extraction route can populate this field, and what proxy is usable immediately?",
                    "next_action": row.get("next_same_resource_action"),
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_packet_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_packet_result", "created"),
        (SPEC_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_spec_ledger", "created"),
        (SCOPE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_scope_ledger", "created"),
        (STATE_PROXY_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_state_proxy_ledger", "created"),
        (CAPTURE_FIELD_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_capture_field_ledger", "created"),
        (SPEC_DECISION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_spec_decision_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_packet_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], decision_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_packet",
        "status": "done",
        "route": "source_silence_microcluster_broader_source_proxy_denominator_expansion",
        "details": "Expanded every axis-repair spec and state-axis decision through broader same-resource source/proxy denominator families and capture-field availability.",
        "counts": counts,
        "spec_broader_proxy_decision_status_counts": decision_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SPEC_LEDGER),
            relative(SCOPE_LEDGER),
            relative(STATE_PROXY_LEDGER),
            relative(CAPTURE_FIELD_LEDGER),
            relative(SPEC_DECISION_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], decision_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Broader Source/Proxy Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local source/proxy denominator expansion only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Decisions", ""])
    for key, value in sorted(decision_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Convert descriptive avoid-direction specs into branch-local no-API challenger stress packets only after source/proxy denominator review.",
            "- Use source-state proxy rows and capture-field availability immediately; do not wait for future/live rows.",
            "- Convert missing capture fields into extraction schemas and strongest current proxy computations inside this goal.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    sealed_specs = read_jsonl(SEALED_SPEC_LEDGER)
    axis_repair_decisions = read_jsonl(AXIS_REPAIR_DECISION_LEDGER)
    axis_repair_spec_statuses = read_jsonl(AXIS_REPAIR_SPEC_STATUS_LEDGER)
    axis_repair_parent_scopes = read_jsonl(AXIS_REPAIR_PARENT_SCOPE_LEDGER)
    axis_repair_capture_requirements = read_jsonl(AXIS_REPAIR_CAPTURE_REQUIREMENT_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in proxy_targets}
    sealed_spec_by_id = {str(row["dedup_spec_id"]): row for row in sealed_specs}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    denom_families = denominator_families(source_join, exact_rows)
    local_depth_rows = [row for row in source_join if bool_value(row.get("depth_file_exists")) is True]

    spec_rows = build_spec_rows(sealed_specs, axis_repair_spec_statuses, axis_repair_decisions)
    scope_rows = build_scope_rows(spec_rows, targets_by_request, denom_families)
    state_proxy_rows = build_state_proxy_rows(axis_repair_decisions, sealed_spec_by_id, targets_by_request, denom_families)
    capture_field_rows = build_capture_field_rows(
        axis_repair_capture_requirements,
        source_join,
        proxy_targets,
        exact_rows,
        local_depth_rows,
    )
    spec_decision_rows = build_spec_decision_rows(spec_rows, scope_rows, state_proxy_rows, capture_field_rows)
    bucket_rows = build_bucket_rows(spec_rows, scope_rows, state_proxy_rows, capture_field_rows, spec_decision_rows)
    question_rows = build_question_rows(spec_decision_rows, state_proxy_rows, capture_field_rows)
    decision_counts = counter_dict(row.get("spec_broader_proxy_decision_status") for row in spec_decision_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "proxy_target_input_rows": len(proxy_targets),
        "sealed_spec_input_rows": len(sealed_specs),
        "axis_repair_decision_input_rows": len(axis_repair_decisions),
        "axis_repair_spec_status_input_rows": len(axis_repair_spec_statuses),
        "axis_repair_parent_scope_input_rows": len(axis_repair_parent_scopes),
        "axis_repair_capture_requirement_input_rows": len(axis_repair_capture_requirements),
        "denominator_family_count": len(denom_families),
        "control_axis_count": len(CONTROL_AXES),
        "control_axis_combination_count": len(all_combinations(CONTROL_AXES)),
        "broader_source_proxy_spec_rows": len(spec_rows),
        "broader_source_proxy_scope_rows": len(scope_rows),
        "state_proxy_rows": len(state_proxy_rows),
        "capture_field_rows": len(capture_field_rows),
        "spec_decision_rows": len(spec_decision_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_broader_source_proxy_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_PACKET_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "axis_repair_spec_status_counts": counter_dict(row.get("axis_repair_spec_status") for row in spec_rows),
        "broader_scope_status_counts": counter_dict(row.get("broader_scope_status") for row in scope_rows),
        "broader_denominator_family_counts": counter_dict(row.get("denominator_family") for row in scope_rows),
        "state_proxy_status_counts": counter_dict(row.get("state_proxy_status") for row in state_proxy_rows),
        "state_axis_counts": counter_dict(row.get("state_axis") for row in state_proxy_rows),
        "capture_field_status_counts": counter_dict(row.get("capture_field_status") for row in capture_field_rows),
        "spec_broader_proxy_decision_status_counts": decision_counts,
        "not_completion": "This broader source/proxy packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "build branch-local no-API challenger stress packets for descriptive avoid-direction specs",
            "materialize extraction scripts or source searches for capture fields missing from current ledgers",
            "continue exact .depth source-date acquisition and broader source roots without waiting for forward data",
        ],
    }
    write_jsonl(SPEC_LEDGER, spec_rows)
    write_jsonl(SCOPE_LEDGER, scope_rows)
    write_jsonl(STATE_PROXY_LEDGER, state_proxy_rows)
    write_jsonl(CAPTURE_FIELD_LEDGER, capture_field_rows)
    write_jsonl(SPEC_DECISION_LEDGER, spec_decision_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, decision_counts)
    write_summary(generated_utc, counts, decision_counts)
    print(json.dumps({"ok": True, "counts": counts, "spec_broader_proxy_decision_status_counts": decision_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
