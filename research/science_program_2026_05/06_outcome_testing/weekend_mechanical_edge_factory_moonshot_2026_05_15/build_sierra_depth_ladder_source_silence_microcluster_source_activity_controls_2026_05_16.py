#!/usr/bin/env python3
"""Broaden source-activity controls for source-silence microcluster specs."""

from __future__ import annotations

import json
import math
import re
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
EVENT15_EMPTY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EVENT15_EMPTY_STATE_LEDGER_{STAMP}.jsonl"
CHALLENGER_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_SPEC_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_CONTROL_RESULT_{STAMP}.json"
EVENT15_ACTIVITY_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EVENT15_ACTIVITY_CONTROL_LEDGER_{STAMP}.jsonl"
DEDUP_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_DEDUP_SPEC_LEDGER_{STAMP}.jsonl"
BROADER_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_BROADER_CONTROL_LEDGER_{STAMP}.jsonl"
CONCENTRATION_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_CONCENTRATION_STRESS_LEDGER_{STAMP}.jsonl"
SURVIVOR_QUEUE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_SURVIVOR_QUEUE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local source-activity and concentration controls only; source-control/design "
    "evidence with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

CONTROL_SCOPES: list[tuple[str, tuple[str, ...]]] = [
    ("all_exact_features", ()),
    ("same_command_bucket", ("command_feature_bucket",)),
    ("same_route_queue", ("route_c_queue_id",)),
    ("same_source_symbol", ("source_symbol",)),
    ("same_source_date", ("source_date",)),
    ("same_horizon", ("horizon_id",)),
    ("same_source_proxy_family", ("source_proxy_family",)),
    ("same_queue_command", ("route_c_queue_id", "command_feature_bucket")),
    ("same_symbol_date", ("source_symbol", "source_date")),
    ("same_date_queue", ("source_date", "route_c_queue_id")),
    ("same_symbol_command", ("source_symbol", "command_feature_bucket")),
]

STRESS_AXES = [
    "request_id",
    "source_date",
    "source_symbol",
    "route_c_queue_id",
    "command_feature_bucket",
    "horizon_id",
    "source_proxy_family",
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
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
    }


def axis_values(rows: list[dict[str, Any]], axis: str) -> set[Any]:
    return {row.get(axis) for row in rows if row.get(axis) is not None}


def control_rows_for_scope(
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


def control_verdict(target_stats: dict[str, Any], control_stats: dict[str, Any], action: str) -> str:
    target_n = int(target_stats.get("n") or 0)
    control_n = int(control_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    control_align = control_stats.get("route_alignment_share")
    if target_n < 5:
        return f"{action.upper()}_TARGET_UNDERPOWERED_N_LT_5"
    if target_n < 20:
        sample_prefix = f"{action.upper()}_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = f"{action.upper()}_TARGET_N_OK"
    if control_n < 5:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_5"
    if control_n < 20:
        return f"{sample_prefix}_CONTROL_UNDERPOWERED_N_LT_20"
    if target_align is None or control_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < control_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_CONTROL"
    if target_align > control_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_CONTROL"
    return f"{sample_prefix}_NEAR_CONTROL"


def parse_predicate(predicate: str) -> list[tuple[str, str, Any]]:
    conditions: list[tuple[str, str, Any]] = []
    for raw_part in predicate.split(" AND "):
        part = raw_part.strip()
        in_match = re.fullmatch(r"([A-Za-z0-9_]+)\s+in\s+\{(.+)\}", part)
        if in_match:
            field = in_match.group(1)
            values = []
            for raw_value in in_match.group(2).split(","):
                values.append(raw_value.strip().strip("'").strip('"'))
            conditions.append((field, "in", set(values)))
            continue
        eq_match = re.fullmatch(r"([A-Za-z0-9_]+)\s*==\s*(.+)", part)
        if eq_match:
            field = eq_match.group(1)
            raw_value = eq_match.group(2).strip()
            try:
                value = json.loads(raw_value)
            except json.JSONDecodeError:
                value = raw_value.strip("'").strip('"')
            conditions.append((field, "eq", value))
            continue
        raise ValueError(f"Unsupported predicate component: {part}")
    return conditions


def row_matches(row: dict[str, Any], conditions: list[tuple[str, str, Any]]) -> bool:
    for field, operator, value in conditions:
        row_value = row.get(field)
        if operator == "eq" and row_value != value:
            return False
        if operator == "in" and row_value not in value:
            return False
    return True


def target_rows_for_spec(spec: dict[str, Any], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conditions = parse_predicate(str(spec["branch_local_predicate"]))
    return [row for row in targets if row_matches(row, conditions)]


def build_event15_activity_controls(
    event15_rows: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    target_rows = [
        targets_by_request[str(row["request_id"])]
        for row in event15_rows
        if str(row.get("request_id")) in targets_by_request
    ]
    rows: list[dict[str, Any]] = []
    target_stats = row_stats(target_rows)
    for scope_name, axes in CONTROL_SCOPES:
        controls = control_rows_for_scope(exact_rows, target_rows, axes)
        control_stats = row_stats(controls)
        rows.append(
            {
                "event15_activity_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EVENT15-ACTIVITY-CONTROL-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_quality_state": "EVENT15_EMPTY_SOURCE_ACTIVITY_PROXY_STATE",
                "target_request_ids": sorted(str(row.get("request_id")) for row in target_rows),
                "control_scope": scope_name,
                "control_axes": list(axes),
                "target_rows": target_stats,
                "control_rows": control_stats,
                "route_alignment_delta_vs_control": numeric_delta(
                    target_stats.get("route_alignment_share"),
                    control_stats.get("route_alignment_share"),
                ),
                "mean_future_change_delta_vs_control": numeric_delta(
                    target_stats.get("mean_route_c_future_change_per_current_range"),
                    control_stats.get("mean_route_c_future_change_per_current_range"),
                ),
                "control_verdict": control_verdict(target_stats, control_stats, "event15_empty"),
                "next_same_resource_action": "preserve as source-activity state; broaden controls and capture schema without waiting",
            }
        )
    return rows


def build_dedup_specs(
    specs: list[dict[str, Any]],
    targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for spec in specs:
        target_rows = target_rows_for_spec(spec, targets)
        request_ids = tuple(sorted(str(row.get("request_id")) for row in target_rows if row.get("request_id")))
        key = (str(spec.get("branch_local_action")), request_ids)
        if key not in by_key:
            by_key[key] = {
                "dedup_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-DEDUP-SPEC-{len(by_key) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "branch_local_action": spec.get("branch_local_action"),
                "dedup_request_ids": list(request_ids),
                "source_spec_ids": [],
                "source_predicates": [],
                "source_requirement_ids": [],
                "source_subgroups": [],
                "target_rows": row_stats(target_rows),
            }
        row = by_key[key]
        row["source_spec_ids"].append(spec.get("challenger_spec_id"))
        row["source_predicates"].append(spec.get("branch_local_predicate"))
        row["source_requirement_ids"].append(spec.get("requirement_id"))
        row["source_subgroups"].append(spec.get("subgroup"))
    rows = list(by_key.values())
    for row in rows:
        row["duplicate_spec_count"] = len(row["source_spec_ids"])
        row["dedup_status"] = (
            "DEDUP_SPEC_NO_TARGET_ROWS"
            if not row["dedup_request_ids"]
            else "DEDUP_SPEC_MERGED_DUPLICATE_SOURCE_SPECS"
            if row["duplicate_spec_count"] > 1
            else "DEDUP_SPEC_UNIQUE"
        )
    return rows


def rows_from_request_ids(rows_by_request: dict[str, dict[str, Any]], request_ids: list[str]) -> list[dict[str, Any]]:
    return [rows_by_request[request_id] for request_id in request_ids if request_id in rows_by_request]


def build_broader_controls(
    dedup_specs: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in dedup_specs:
        target_rows = rows_from_request_ids(targets_by_request, spec["dedup_request_ids"])
        target_stats = row_stats(target_rows)
        for scope_name, axes in CONTROL_SCOPES:
            controls = control_rows_for_scope(exact_rows, target_rows, axes)
            control_stats = row_stats(controls)
            rows.append(
                {
                    "broader_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-BROADER-CONTROL-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "dedup_spec_id": spec["dedup_spec_id"],
                    "branch_local_action": spec["branch_local_action"],
                    "control_scope": scope_name,
                    "control_axes": list(axes),
                    "target_rows": target_stats,
                    "control_rows": control_stats,
                    "route_alignment_delta_vs_control": numeric_delta(
                        target_stats.get("route_alignment_share"),
                        control_stats.get("route_alignment_share"),
                    ),
                    "mean_future_change_delta_vs_control": numeric_delta(
                        target_stats.get("mean_route_c_future_change_per_current_range"),
                        control_stats.get("mean_route_c_future_change_per_current_range"),
                    ),
                    "control_verdict": control_verdict(target_stats, control_stats, str(spec["branch_local_action"])),
                }
            )
    return rows


def max_axis_share(target_rows: list[dict[str, Any]], axis: str) -> float | None:
    if not target_rows:
        return None
    counts = Counter(row.get(axis) for row in target_rows)
    return max(counts.values()) / len(target_rows) if counts else None


def build_concentration_stress(
    dedup_specs: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_control_stats = row_stats(exact_rows)
    control_align = all_control_stats.get("route_alignment_share")
    rows: list[dict[str, Any]] = []
    for spec in dedup_specs:
        if spec.get("branch_local_action") != "source_quality_avoid_challenger_candidate":
            continue
        target_rows = rows_from_request_ids(targets_by_request, spec["dedup_request_ids"])
        original_stats = row_stats(target_rows)
        original_align = original_stats.get("route_alignment_share")
        for axis in STRESS_AXES:
            for value, count in sorted(Counter(row.get(axis) for row in target_rows).items(), key=lambda item: str(item[0])):
                remaining = [row for row in target_rows if row.get(axis) != value]
                remaining_stats = row_stats(remaining)
                remaining_align = remaining_stats.get("route_alignment_share")
                if remaining_stats["n"] < 5:
                    stress_status = "CONCENTRATION_STRESS_UNDERPOWERED_AFTER_REMOVAL"
                elif control_align is None or remaining_align is None or original_align is None:
                    stress_status = "CONCENTRATION_STRESS_DESCRIPTIVE_NO_ALIGNMENT"
                elif original_align < control_align and remaining_align < control_align:
                    stress_status = "CONCENTRATION_STRESS_AVOID_DIRECTION_STABLE"
                elif original_align < control_align <= remaining_align:
                    stress_status = "CONCENTRATION_STRESS_AVOID_DIRECTION_BREAKS"
                else:
                    stress_status = "CONCENTRATION_STRESS_NOT_AVOID_DIRECTION"
                rows.append(
                    {
                        "concentration_stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-CONCENTRATION-STRESS-{len(rows) + 1:05d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "dedup_spec_id": spec["dedup_spec_id"],
                        "axis": axis,
                        "axis_value": value,
                        "removed_rows": count,
                        "removed_share": count / len(target_rows) if target_rows else None,
                        "original_rows": original_stats,
                        "remaining_rows": remaining_stats,
                        "all_exact_control_rows": all_control_stats,
                        "route_alignment_delta_after_removal_vs_all_exact": numeric_delta(
                            remaining_align,
                            control_align,
                        ),
                        "stress_status": stress_status,
                    }
                )
    return rows


def build_survivor_queue(
    dedup_specs: list[dict[str, Any]],
    broader_controls: list[dict[str, Any]],
    concentration_rows: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    controls_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in broader_controls:
        controls_by_spec[str(row["dedup_spec_id"])].append(row)
    stress_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in concentration_rows:
        stress_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in dedup_specs:
        target_rows = rows_from_request_ids(targets_by_request, spec["dedup_request_ids"])
        if not target_rows:
            queue_status = "NO_TARGET_ROWS_DROP_TO_SOURCE_AUDIT"
        elif spec["branch_local_action"] == "source_quality_event15_empty_proxy_state":
            queue_status = "EVENT15_EMPTY_SOURCE_STATE_CONTROL_QUEUE"
        else:
            controls = controls_by_spec.get(str(spec["dedup_spec_id"]), [])
            avoid_controls = [
                row for row in controls
                if str(row.get("control_verdict", "")).endswith("_AVOID_DIRECTION_VS_CONTROL")
            ]
            break_count = sum(
                1 for row in stress_by_spec.get(str(spec["dedup_spec_id"]), [])
                if row.get("stress_status") == "CONCENTRATION_STRESS_AVOID_DIRECTION_BREAKS"
            )
            stable_count = sum(
                1 for row in stress_by_spec.get(str(spec["dedup_spec_id"]), [])
                if row.get("stress_status") == "CONCENTRATION_STRESS_AVOID_DIRECTION_STABLE"
            )
            max_date = max_axis_share(target_rows, "source_date")
            max_symbol = max_axis_share(target_rows, "source_symbol")
            if not avoid_controls:
                queue_status = "AVOID_SPEC_NO_BROADER_CONTROL_SUPPORT"
            elif break_count:
                queue_status = "AVOID_SPEC_CONCENTRATION_BREAKS_DIRECTION"
            elif len(target_rows) < 20:
                queue_status = "AVOID_SPEC_UNDERPOWERED_PROXY_VALIDATION_QUEUE"
            elif (max_date or 0.0) > 0.75 or (max_symbol or 0.0) > 0.75:
                queue_status = "AVOID_SPEC_CONCENTRATED_PROXY_VALIDATION_QUEUE"
            elif stable_count:
                queue_status = "AVOID_SPEC_STABLE_PROXY_VALIDATION_QUEUE"
            else:
                queue_status = "AVOID_SPEC_DESCRIPTIVE_QUEUE"
        rows.append(
            {
                "survivor_queue_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-SURVIVOR-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec["dedup_spec_id"],
                "branch_local_action": spec["branch_local_action"],
                "source_spec_ids": spec["source_spec_ids"],
                "dedup_request_ids": spec["dedup_request_ids"],
                "target_rows": row_stats(target_rows),
                "broader_control_verdict_counts": counter_dict(
                    row.get("control_verdict") for row in controls_by_spec.get(str(spec["dedup_spec_id"]), [])
                ),
                "concentration_stress_counts": counter_dict(
                    row.get("stress_status") for row in stress_by_spec.get(str(spec["dedup_spec_id"]), [])
                ),
                "max_source_date_share": max_axis_share(target_rows, "source_date"),
                "max_source_symbol_share": max_axis_share(target_rows, "source_symbol"),
                "queue_status": queue_status,
                "next_same_resource_action": next_action_for_queue_status(queue_status),
            }
        )
    return rows


def next_action_for_queue_status(status: str) -> str:
    if status == "EVENT15_EMPTY_SOURCE_STATE_CONTROL_QUEUE":
        return "build broader source-activity/capture schema and compare across all current exact-feature rows"
    if status.endswith("PROXY_VALIDATION_QUEUE"):
        return "build sealed/proxy validation packet with dedup identity and concentration guard"
    if status == "AVOID_SPEC_CONCENTRATION_BREAKS_DIRECTION":
        return "split by breaking concentration axis before any stronger challenger interpretation"
    if status == "AVOID_SPEC_NO_BROADER_CONTROL_SUPPORT":
        return "preserve as failure intelligence and source-control context"
    return "preserve row and route to next same-resource control"


def build_bucket_rows(
    event15_controls: list[dict[str, Any]],
    dedup_specs: list[dict[str, Any]],
    broader_controls: list[dict[str, Any]],
    concentration_rows: list[dict[str, Any]],
    survivor_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets = [
        ("event15_control_verdict", counter_dict(row.get("control_verdict") for row in event15_controls)),
        ("dedup_status", counter_dict(row.get("dedup_status") for row in dedup_specs)),
        ("broader_control_verdict", counter_dict(row.get("control_verdict") for row in broader_controls)),
        ("concentration_stress_status", counter_dict(row.get("stress_status") for row in concentration_rows)),
        ("survivor_queue_status", counter_dict(row.get("queue_status") for row in survivor_rows)),
        ("dedup_action", counter_dict(row.get("branch_local_action") for row in dedup_specs)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                }
            )
    return rows


def build_questions(
    survivor_rows: list[dict[str, Any]],
    broader_controls: list[dict[str, Any]],
    concentration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for survivor in survivor_rows:
        status = str(survivor.get("queue_status"))
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "question_family": "survivor_next_action",
                "dedup_spec_id": survivor.get("dedup_spec_id"),
                "question": f"What exact same-resource packet resolves queue status {status} for this source-activity spec?",
                "next_action": survivor.get("next_same_resource_action"),
                "evidence_boundary": EVIDENCE_BOUNDARY,
            }
        )
    for row in broader_controls:
        if "UNDERPOWERED" in str(row.get("control_verdict")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "question_family": "underpowered_control",
                    "dedup_spec_id": row.get("dedup_spec_id"),
                    "control_scope": row.get("control_scope"),
                    "question": "Which broader source/date/symbol/queue proxy can increase this control denominator now without waiting?",
                    "next_action": "broaden source activity controls across exact-feature rows and current local source roots",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                }
            )
    for row in concentration_rows:
        if row.get("stress_status") == "CONCENTRATION_STRESS_AVOID_DIRECTION_BREAKS":
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-ACTIVITY-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "question_family": "concentration_break",
                    "dedup_spec_id": row.get("dedup_spec_id"),
                    "axis": row.get("axis"),
                    "axis_value": row.get("axis_value"),
                    "question": "Does the breaking concentration axis explain the apparent avoid candidate?",
                    "next_action": "split the challenger by this axis and retest controls before any survivor queue",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_source_activity_controls_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_source_activity_control_result", "created"),
        (EVENT15_ACTIVITY_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_microcluster_event15_activity_control_ledger", "created"),
        (DEDUP_SPEC_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_dedup_spec_ledger", "created"),
        (BROADER_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_broader_control_ledger", "created"),
        (CONCENTRATION_STRESS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_concentration_stress_ledger", "created"),
        (SURVIVOR_QUEUE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_survivor_queue_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_activity_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_source_activity_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], queue_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_source_activity_controls",
        "status": "done",
        "route": "source_silence_microcluster_broader_source_activity_controls",
        "details": "Tested event15-empty source states and avoid challenger specs across broader source-activity controls, dedup identity, and concentration stress.",
        "counts": counts,
        "survivor_queue_status_counts": queue_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(EVENT15_ACTIVITY_CONTROL_LEDGER),
            relative(DEDUP_SPEC_LEDGER),
            relative(BROADER_CONTROL_LEDGER),
            relative(CONCENTRATION_STRESS_LEDGER),
            relative(SURVIVOR_QUEUE_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], queue_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Source-Activity Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local source-activity controls only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Survivor Queue Status", ""])
    for key, value in sorted(queue_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Build sealed/proxy packets only for deduplicated avoid specs that survive concentration stress.",
            "- Split every concentration-breaking spec by the breaking axis before any stronger interpretation.",
            "- Treat event15-empty as source-activity state until broader controls or source acquisition explain it.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets = read_jsonl(PROXY_TARGET_LEDGER)
    event15_rows = read_jsonl(EVENT15_EMPTY_LEDGER)
    specs = read_jsonl(CHALLENGER_SPEC_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in targets}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    event15_controls = build_event15_activity_controls(event15_rows, targets_by_request, exact_rows)
    dedup_specs = build_dedup_specs(specs, targets)
    broader_controls = build_broader_controls(dedup_specs, targets_by_request, exact_rows)
    concentration_rows = build_concentration_stress(dedup_specs, targets_by_request, exact_rows)
    survivor_rows = build_survivor_queue(dedup_specs, broader_controls, concentration_rows, targets_by_request)
    bucket_rows = build_bucket_rows(event15_controls, dedup_specs, broader_controls, concentration_rows, survivor_rows)
    question_rows = build_questions(survivor_rows, broader_controls, concentration_rows)
    queue_counts = counter_dict(row.get("queue_status") for row in survivor_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "proxy_target_input_rows": len(targets),
        "event15_empty_input_rows": len(event15_rows),
        "challenger_spec_input_rows": len(specs),
        "event15_activity_control_rows": len(event15_controls),
        "dedup_spec_rows": len(dedup_specs),
        "broader_control_rows": len(broader_controls),
        "concentration_stress_rows": len(concentration_rows),
        "survivor_queue_rows": len(survivor_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_source_activity_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_SOURCE_ACTIVITY_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "dedup_status_counts": counter_dict(row.get("dedup_status") for row in dedup_specs),
        "event15_control_verdict_counts": counter_dict(row.get("control_verdict") for row in event15_controls),
        "broader_control_verdict_counts": counter_dict(row.get("control_verdict") for row in broader_controls),
        "concentration_stress_status_counts": counter_dict(row.get("stress_status") for row in concentration_rows),
        "survivor_queue_status_counts": queue_counts,
        "not_completion": "This source-activity control packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "build sealed/proxy packets for deduplicated avoid specs that survive concentration stress",
            "split concentration-breaking specs by breaking source/date/symbol/queue/command axes",
            "broaden event15-empty state controls through exact source activity and capture-schema proxies",
        ],
    }
    write_jsonl(EVENT15_ACTIVITY_CONTROL_LEDGER, event15_controls)
    write_jsonl(DEDUP_SPEC_LEDGER, dedup_specs)
    write_jsonl(BROADER_CONTROL_LEDGER, broader_controls)
    write_jsonl(CONCENTRATION_STRESS_LEDGER, concentration_rows)
    write_jsonl(SURVIVOR_QUEUE_LEDGER, survivor_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, queue_counts)
    write_summary(generated_utc, counts, queue_counts)
    print(json.dumps({"ok": True, "counts": counts, "survivor_queue_status_counts": queue_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
