#!/usr/bin/env python3
"""Turn remaining Sierra ladder gaps into exact requirements.

This builder consumes the full Route C ladder join and does two same-resource
follow-ups:

1. Preserve every source-gap and ladder-blocker row as a concrete source or
   capture requirement.
2. Inspect every imbalanced ladder row against command-flow and same-source
   neighbor-pair controls.

The output remains descriptor/control/source-requirement evidence only.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
NEIGHBOR_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_NEIGHBOR_INTRADAY_PAIR_LEDGER_{STAMP}.jsonl"
ALT_GAP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_GAP_LEDGER_{STAMP}.jsonl"
ALT_CANDIDATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_SOURCE_GAP_ALT_ROOT_CANDIDATE_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_GAP_REQUIREMENT_RESULT_{STAMP}.json"
REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_LEDGER_{STAMP}.jsonl"
REQUIREMENT_GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_GROUP_LEDGER_{STAMP}.jsonl"
IMBALANCED_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_ROW_INSPECTION_LEDGER_{STAMP}.jsonl"
IMBALANCED_NEIGHBOR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_NEIGHBOR_CONTEXT_LEDGER_{STAMP}.jsonl"
IMBALANCED_BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_GAP_REQUIREMENT_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth ladder source/capture requirements and imbalanced-row inspection only; "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

GROUP_FAMILIES = [
    ("requirement_by_type_source_date", ("requirement_type", "source_symbol", "source_date")),
    ("requirement_by_type_recovery_bucket", ("requirement_type", "recovery_bucket")),
    ("requirement_by_type_route_symbol", ("requirement_type", "route_c_symbol")),
    ("requirement_by_type_queue", ("requirement_type", "route_c_queue_id")),
    ("requirement_by_type_mechanism", ("requirement_type", "route_c_mechanism_family")),
    ("requirement_by_type_command_bucket", ("requirement_type", "command_feature_bucket")),
    ("requirement_by_type_horizon", ("requirement_type", "horizon_id")),
]

IMBALANCED_GROUP_FAMILIES = [
    ("imbalanced_by_source_symbol_date", ("source_symbol", "source_date")),
    ("imbalanced_by_command_bucket", ("command_feature_bucket",)),
    ("imbalanced_by_route_symbol", ("route_c_symbol",)),
    ("imbalanced_by_route_queue", ("route_c_queue_id",)),
    ("imbalanced_by_mechanism", ("route_c_mechanism_family",)),
    ("imbalanced_by_command_ladder_sign_agreement", ("command_ladder_sign_relation",)),
    ("imbalanced_by_route_alignment_descriptor", ("route_alignment_descriptor",)),
    ("imbalanced_by_neighbor_context_bucket", ("neighbor_context_bucket",)),
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
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
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def hhi(values: list[str]) -> float | None:
    if not values:
        return None
    counts = Counter(values)
    total = len(values)
    return sum((count / total) ** 2 for count in counts.values())


def sign_relation(command_sign: Any, ladder_sign: Any) -> str:
    command = str(command_sign or "unknown")
    ladder = str(ladder_sign or "unknown")
    if command == "unknown" or ladder == "unknown":
        return "COMMAND_OR_LADDER_SIGN_UNKNOWN"
    if command == ladder:
        return "COMMAND_AND_LADDER_SIGN_AGREE"
    if command == "zero" or ladder == "zero":
        return "COMMAND_OR_LADDER_SIGN_ZERO_MIXED"
    return "COMMAND_AND_LADDER_SIGN_DIVERGE"


def route_alignment_descriptor(row: dict[str, Any], relation: str) -> str:
    aligned = bool_value(row.get("route_c_delta_aligned_with_future"))
    if relation == "COMMAND_AND_LADDER_SIGN_AGREE" and aligned is True:
        return "COMMAND_LADDER_AGREE_AND_ROUTE_ALIGNED_DESCRIPTOR"
    if relation == "COMMAND_AND_LADDER_SIGN_AGREE" and aligned is False:
        return "COMMAND_LADDER_AGREE_BUT_ROUTE_NOT_ALIGNED_WEAKENING_DESCRIPTOR"
    if relation == "COMMAND_AND_LADDER_SIGN_DIVERGE" and aligned is True:
        return "COMMAND_LADDER_DIVERGE_BUT_ROUTE_ALIGNED_SPLIT_REQUIRED"
    if relation == "COMMAND_AND_LADDER_SIGN_DIVERGE" and aligned is False:
        return "COMMAND_LADDER_DIVERGE_AND_ROUTE_NOT_ALIGNED_AVOID_CANDIDATE"
    return "IMBALANCED_ROW_ALIGNMENT_UNKNOWN_OR_MIXED"


def requirement_type(row: dict[str, Any]) -> str | None:
    if row.get("ladder_join_status") == "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE":
        return "MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT"
    blocker = row.get("ladder_blocker_type")
    if blocker == "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW":
        return "EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT"
    if blocker == "LADDER_BOUNDARY60_NO_EVENT_SAMPLES":
        return "EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT"
    return None


def requirement_action(req_type: str, recovery_bucket: str | None = None) -> str:
    if req_type == "MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT":
        if recovery_bucket == "NEAR_MATCH_SUFFIX_OR_DELAYED_FILE_ONLY":
            return "audit delayed/suffixed near-match source semantics; do not substitute until exact contract proves equivalence"
        return "obtain exact source-date Sierra .depth file or approved equivalent depth source with hash and as-of contract"
    if req_type == "EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT":
        return "recover earlier depth history or file-start book state; otherwise keep conservative no-ladder classification"
    if req_type == "EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT":
        return "audit event-window timestamp/session alignment; if true zero-sample, preserve fail-closed ladder descriptor"
    return "preserve requirement and route to source/capture ledger"


def requirement_status(req_type: str, recovery_bucket: str | None = None) -> str:
    if req_type == "MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT":
        if recovery_bucket == "NEAR_MATCH_SUFFIX_OR_DELAYED_FILE_ONLY":
            return "UNRESOLVED_NEAR_MATCH_NOT_SUBSTITUTABLE"
        return "UNRECOVERED_EXACT_DEPTH_FILE"
    if req_type == "EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT":
        return "LOCAL_FILE_PRESENT_BUT_PRIOR_BOOK_STATE_INSUFFICIENT"
    if req_type == "EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT":
        return "LOCAL_FILE_PRESENT_BUT_EVENT_WINDOW_EMPTY_OR_MISALIGNED"
    return "REQUIREMENT_RECORDED"


def alt_gap_maps(alt_gaps: list[dict[str, Any]]) -> tuple[dict[tuple[str, str, str], dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    exact: dict[tuple[str, str, str], dict[str, Any]] = {}
    loose: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in alt_gaps:
        key = (str(row.get("source_symbol")), str(row.get("source_date")), str(row.get("expected_depth_path")))
        exact[key] = row
        loose[(str(row.get("source_symbol")), str(row.get("source_date")))].append(row)
    return exact, loose


def find_alt_gap(row: dict[str, Any], exact: dict[tuple[str, str, str], dict[str, Any]], loose: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any] | None:
    key = (str(row.get("source_symbol")), str(row.get("source_date")), str(row.get("depth_path")))
    if key in exact:
        return exact[key]
    candidates = loose.get((str(row.get("source_symbol")), str(row.get("source_date"))), [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def build_requirement_rows(
    join_rows: list[dict[str, Any]],
    alt_gaps: list[dict[str, Any]],
    alt_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact, loose = alt_gap_maps(alt_gaps)
    candidates_by_gap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in alt_candidates:
        candidates_by_gap[str(row.get("gap_id"))].append(row)
    out: list[dict[str, Any]] = []
    for row in join_rows:
        req_type = requirement_type(row)
        if req_type is None:
            continue
        alt_gap = find_alt_gap(row, exact, loose) if req_type == "MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT" else None
        gap_id = None if alt_gap is None else alt_gap.get("gap_id")
        recovery_bucket = None if alt_gap is None else str(alt_gap.get("recovery_bucket"))
        near_candidates = candidates_by_gap.get(str(gap_id), []) if gap_id else []
        out.append(
            {
                "route_id": ROUTE_ID,
                "requirement_id": f"SIERRA-DEPTH-LADDER-REQ-{len(out) + 1:06d}",
                "request_id": row.get("request_id"),
                "replay_id": row.get("replay_id"),
                "requirement_type": req_type,
                "requirement_status": requirement_status(req_type, recovery_bucket),
                "next_same_resource_action": requirement_action(req_type, recovery_bucket),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "depth_path": row.get("depth_path"),
                "alt_gap_id": gap_id,
                "alt_recovery_bucket": recovery_bucket,
                "recovery_bucket": recovery_bucket or requirement_status(req_type, recovery_bucket),
                "near_candidate_count": len(near_candidates),
                "near_candidate_ids": [candidate.get("candidate_id") for candidate in near_candidates],
                "near_candidate_paths": [candidate.get("candidate_path") for candidate in near_candidates],
                "route_c_symbol": row.get("route_c_symbol"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                "route_c_mechanism_family": row.get("route_c_mechanism_family"),
                "route_c_residual_transfer_class": row.get("route_c_residual_transfer_class"),
                "route_c_full_control_bucket": row.get("route_c_full_control_bucket"),
                "request_family": row.get("request_family"),
                "horizon_id": row.get("horizon_id"),
                "bar_start_utc": row.get("bar_start_utc"),
                "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
                "window_start_utc": row.get("window_start_utc"),
                "event15_start_utc": row.get("event15_start_utc"),
                "command_feature_bucket": row.get("command_feature_bucket"),
                "command_event15_imbalance_sign": row.get("command_event15_imbalance_sign"),
                "ladder_join_status": row.get("ladder_join_status"),
                "ladder_blocker_type": row.get("ladder_blocker_type"),
                "ladder_snapshot_bucket": row.get("ladder_snapshot_bucket"),
                "ladder_pre_boundary60_sample_count": row.get("ladder_pre_boundary60_sample_count"),
                "ladder_event_boundary60_sample_count": row.get("ladder_event_boundary60_sample_count"),
                "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                "route_c_future_abs_change": row.get("route_c_future_abs_change"),
                "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                "requirement_boundary": (
                    "source/capture requirement only; do not backfill ladder state from price, "
                    "and do not interpret as validated edge"
                ),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def group_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_alignment = [
        value for row in rows
        if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None
    ]
    abs_future = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_abs_change"))) is not None
    ]
    per_range = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    event_times = [parse_dt(row.get("event15_start_utc") or row.get("bar_start_utc")) for row in rows]
    event_times = [value for value in event_times if value is not None]
    source_dates = [str(row.get("source_date")) for row in rows if row.get("source_date")]
    return {
        "n": len(rows),
        "request_family_counts": counter_dict([row.get("request_family") for row in rows]),
        "route_c_symbol_counts": counter_dict([row.get("route_c_symbol") for row in rows]),
        "route_c_queue_counts": counter_dict([row.get("route_c_queue_id") for row in rows]),
        "mechanism_family_counts": counter_dict([row.get("route_c_mechanism_family") for row in rows]),
        "command_bucket_counts": counter_dict([row.get("command_feature_bucket") for row in rows]),
        "horizon_counts": counter_dict([row.get("horizon_id") for row in rows]),
        "source_date_count": len(set(source_dates)),
        "source_date_hhi": hhi(source_dates),
        "near_candidate_rows": sum(1 for row in rows if int(row.get("near_candidate_count") or 0) > 0),
        "route_alignment_descriptor_share": share(route_alignment),
        "route_alignment_descriptor_n": len(route_alignment),
        "mean_route_c_abs_future_change_descriptor": mean(abs_future),
        "mean_route_c_future_change_per_current_range_descriptor": mean(per_range),
        "earliest_event_utc": min(event_times).isoformat().replace("+00:00", "Z") if event_times else None,
        "latest_event_utc": max(event_times).isoformat().replace("+00:00", "Z") if event_times else None,
    }


def build_requirement_groups(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for family, keys in GROUP_FAMILIES:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in requirements:
            groups[tuple(row.get(key) for key in keys)].append(row)
        for group_key, rows in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
            out.append(
                {
                    "route_id": ROUTE_ID,
                    "requirement_group_id": f"SIERRA-DEPTH-LADDER-REQ-GROUP-{len(out) + 1:05d}",
                    "group_family": family,
                    "group_keys": list(keys),
                    "group_values": {key: value for key, value in zip(keys, group_key, strict=True)},
                    "stats": group_stats(rows),
                    "next_same_resource_action": requirement_action(str(group_key[0])) if keys[0] == "requirement_type" else "preserve grouped requirement for source/capture planning",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return out


def build_neighbor_indexes(pairs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_request: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        by_request[str(row.get("left_request_id"))].append(row)
        by_request[str(row.get("right_request_id"))].append(row)
    return by_request


def neighbor_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    same_alignment = [
        value for row in rows
        if (value := bool_value(row.get("same_route_alignment_bool"))) is not None
    ]
    minutes = [
        value for row in rows
        if (value := safe_float(row.get("minutes_between_event15"))) is not None
    ]
    abs_delta = [
        value for row in rows
        if (value := safe_float(row.get("abs_route_c_future_change_delta"))) is not None
    ]
    same_ladder = [bool(row.get("same_ladder_bucket")) for row in rows]
    same_command = [bool(row.get("same_command_bucket")) for row in rows]
    return {
        "neighbor_pair_count": len(rows),
        "offset_bucket_counts": counter_dict([row.get("offset_bucket") for row in rows]),
        "ladder_bucket_pair_counts": counter_dict([row.get("ladder_bucket_pair") for row in rows]),
        "same_ladder_bucket_share": share(same_ladder),
        "same_command_bucket_share": share(same_command),
        "same_route_alignment_share": share(same_alignment),
        "same_route_alignment_n": len(same_alignment),
        "min_minutes_between_event15": min(minutes) if minutes else None,
        "mean_minutes_between_event15": mean(minutes),
        "mean_abs_route_c_future_change_delta": mean(abs_delta),
    }


def neighbor_bucket(context: dict[str, Any]) -> str:
    n = int(context.get("neighbor_pair_count") or 0)
    if n == 0:
        return "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_PAIRS"
    same_align = context.get("same_route_alignment_share")
    min_minutes = context.get("min_minutes_between_event15")
    if min_minutes is not None and min_minutes <= 60 and same_align is not None and same_align >= 0.65:
        return "IMBALANCED_NEARBY_NEIGHBORS_ROUTE_ALIGNMENT_CLUSTER"
    if same_align is not None and same_align <= 0.45:
        return "IMBALANCED_NEIGHBORS_ROUTE_ALIGNMENT_UNSTABLE"
    return "IMBALANCED_NEIGHBOR_CONTEXT_DESCRIPTIVE"


def build_imbalanced_rows(
    join_rows: list[dict[str, Any]],
    neighbor_by_request: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    neighbor_rows: list[dict[str, Any]] = []
    imbalanced = [
        row for row in join_rows
        if row.get("ladder_snapshot_bucket") == "LADDER_BOUNDARY60_EVENT_DEPTH10_IMBALANCED"
    ]
    for row in imbalanced:
        request_id = str(row.get("request_id"))
        neighbors = neighbor_by_request.get(request_id, [])
        context = neighbor_context(neighbors)
        relation = sign_relation(row.get("command_event15_imbalance_sign"), row.get("ladder_event_boundary60_imbalance_sign"))
        route_descriptor = route_alignment_descriptor(row, relation)
        bucket = neighbor_bucket(context)
        rows.append(
            {
                "route_id": ROUTE_ID,
                "imbalanced_inspection_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-{len(rows) + 1:05d}",
                "request_id": request_id,
                "replay_id": row.get("replay_id"),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "depth_path": row.get("depth_path"),
                "route_c_symbol": row.get("route_c_symbol"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                "route_c_mechanism_family": row.get("route_c_mechanism_family"),
                "route_c_residual_transfer_class": row.get("route_c_residual_transfer_class"),
                "route_c_full_control_bucket": row.get("route_c_full_control_bucket"),
                "horizon_id": row.get("horizon_id"),
                "bar_start_utc": row.get("bar_start_utc"),
                "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
                "event15_start_utc": row.get("event15_start_utc"),
                "command_feature_bucket": row.get("command_feature_bucket"),
                "command_event15_imbalance_sign": row.get("command_event15_imbalance_sign"),
                "command_event15_bid_quantity_share": row.get("event15_depth_bid_quantity_share"),
                "command_event15_bid_minus_ask_quantity_sum": row.get("event15_depth_bid_minus_ask_quantity_sum"),
                "ladder_event_boundary60_imbalance_sign": row.get("ladder_event_boundary60_imbalance_sign"),
                "ladder_event_boundary60_median_depth10_imbalance": row.get("ladder_event_boundary60_median_depth10_imbalance"),
                "ladder_event_boundary60_median_depth20_imbalance": row.get("ladder_event_boundary60_median_depth20_imbalance"),
                "ladder_event_boundary60_median_total_depth10": row.get("ladder_event_boundary60_median_total_depth10"),
                "ladder_event_boundary60_median_wall_concentration10": row.get("ladder_event_boundary60_median_wall_concentration10"),
                "ladder_event_boundary60_mid_change_ticks": row.get("ladder_event_boundary60_mid_change_ticks"),
                "ladder_event_boundary60_sample_count": row.get("ladder_event_boundary60_sample_count"),
                "pre60_depth_bid_quantity_share": row.get("pre60_depth_bid_quantity_share"),
                "pre60_depth_bid_minus_ask_quantity_sum": row.get("pre60_depth_bid_minus_ask_quantity_sum"),
                "command_ladder_sign_relation": relation,
                "route_alignment_descriptor": route_descriptor,
                "neighbor_context_bucket": bucket,
                "neighbor_context": context,
                "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                "route_c_future_abs_change": row.get("route_c_future_abs_change"),
                "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                "next_same_resource_action": "split imbalanced rows by command-ladder sign relation and same-source neighbor context before interpreting",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
        for neighbor in neighbors:
            neighbor_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "imbalanced_neighbor_context_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-NEIGHBOR-{len(neighbor_rows) + 1:06d}",
                    "anchor_request_id": request_id,
                    **neighbor,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows, neighbor_rows


def build_imbalanced_buckets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for family, keys in IMBALANCED_GROUP_FAMILIES:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row.get(key) for key in keys)].append(row)
        for group_key, group in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
            ladder_imbalance = [
                value for row in group
                if (value := safe_float(row.get("ladder_event_boundary60_median_depth10_imbalance"))) is not None
            ]
            command_bid_share = [
                value for row in group
                if (value := safe_float(row.get("command_event15_bid_quantity_share"))) is not None
            ]
            route_alignment = [
                value for row in group
                if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None
            ]
            out.append(
                {
                    "route_id": ROUTE_ID,
                    "imbalanced_bucket_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-BUCKET-{len(out) + 1:05d}",
                    "group_family": family,
                    "group_keys": list(keys),
                    "group_values": {key: value for key, value in zip(keys, group_key, strict=True)},
                    "n": len(group),
                    "source_symbol_counts": counter_dict([row.get("source_symbol") for row in group]),
                    "source_date_count": len({str(row.get("source_date")) for row in group if row.get("source_date")}),
                    "route_c_queue_counts": counter_dict([row.get("route_c_queue_id") for row in group]),
                    "command_bucket_counts": counter_dict([row.get("command_feature_bucket") for row in group]),
                    "route_alignment_descriptor_counts": counter_dict([row.get("route_alignment_descriptor") for row in group]),
                    "neighbor_context_bucket_counts": counter_dict([row.get("neighbor_context_bucket") for row in group]),
                    "mean_ladder_depth10_imbalance": mean(ladder_imbalance),
                    "mean_command_bid_quantity_share": mean(command_bid_share),
                    "route_alignment_descriptor_share": share(route_alignment),
                    "route_alignment_descriptor_n": len(route_alignment),
                    "next_same_resource_action": "preserve full imbalanced rowset and test broader aggregation or source expansion before interpretation",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return out


def build_questions(
    requirement_counts: Counter[str],
    requirement_status_counts: Counter[str],
    imbalanced_descriptor_counts: Counter[str],
    counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for req_type, count in sorted(requirement_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-REQ-Q-{len(rows) + 1:03d}",
                "question_family": "ladder_requirement_type",
                "bucket": req_type,
                "row_count": count,
                "question": f"What exact source/capture route closes all {count} rows in {req_type} without inventing ladder state?",
                "next_same_resource_action": requirement_action(req_type),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for status, count in sorted(requirement_status_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-REQ-Q-{len(rows) + 1:03d}",
                "question_family": "ladder_requirement_status",
                "bucket": status,
                "row_count": count,
                "question": f"Which current/free/owned source path can reduce {count} rows in status {status}?",
                "next_same_resource_action": "route status to exact source acquisition, parser audit, or conservative fail-closed requirement",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for descriptor, count in sorted(imbalanced_descriptor_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-REQ-Q-{len(rows) + 1:03d}",
                "question_family": "imbalanced_route_descriptor",
                "bucket": descriptor,
                "row_count": count,
                "question": f"What split or mutation follows from all {count} imbalanced rows in {descriptor}?",
                "next_same_resource_action": "inspect full imbalanced ledger with command-flow and neighbor context before any downstream hypothesis",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_gap_requirement_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_gap_requirement_result", "created"),
        (REQUIREMENT_LEDGER, "sierra_depth_ladder_requirement_ledger", "created"),
        (REQUIREMENT_GROUP_LEDGER, "sierra_depth_ladder_requirement_group_ledger", "created"),
        (IMBALANCED_LEDGER, "sierra_depth_ladder_imbalanced_row_inspection_ledger", "created"),
        (IMBALANCED_NEIGHBOR_LEDGER, "sierra_depth_ladder_imbalanced_neighbor_context_ledger", "created"),
        (IMBALANCED_BUCKET_LEDGER, "sierra_depth_ladder_imbalanced_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_requirement_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_gap_requirement_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], requirement_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_gap_requirements",
        "status": "done",
        "route": "sierra_depth_ladder_requirements_and_imbalanced_inspection",
        "details": "Converted ladder source gaps/blockers into exact source/capture requirements and inspected all imbalanced ladder rows against neighbor controls.",
        "counts": counts,
        "requirement_type_counts": dict(sorted(requirement_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(REQUIREMENT_LEDGER),
            relative(REQUIREMENT_GROUP_LEDGER),
            relative(IMBALANCED_LEDGER),
            relative(IMBALANCED_NEIGHBOR_LEDGER),
            relative(IMBALANCED_BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    requirement_counts: Counter[str],
    requirement_status_counts: Counter[str],
    imbalanced_descriptor_counts: Counter[str],
) -> None:
    lines = [
        "# Sierra Depth Ladder Gap Requirements And Imbalanced Inspection",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source/capture requirements plus imbalanced ladder row inspection only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Requirement Types", ""])
    for key, value in sorted(requirement_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Requirement Statuses", ""])
    for key, value in sorted(requirement_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Imbalanced Route Descriptors", ""])
    for key, value in sorted(imbalanced_descriptor_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- Search or request exact `.depth` source-date files for unrecovered missing-depth requirements.",
            "- Audit delayed/suffixed near-match NQ depth samples before any substitution.",
            "- Split the imbalanced rows by command-ladder sign relation and same-source neighbor context.",
            "- Continue mutation work from current depth/SCID/tick data; this packet is not completion.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    join_rows = read_jsonl(JOIN_LEDGER)
    neighbor_pairs = read_jsonl(NEIGHBOR_PAIR_LEDGER)
    alt_gaps = read_jsonl(ALT_GAP_LEDGER)
    alt_candidates = read_jsonl(ALT_CANDIDATE_LEDGER)
    requirements = build_requirement_rows(join_rows, alt_gaps, alt_candidates)
    requirement_groups = build_requirement_groups(requirements)
    neighbor_by_request = build_neighbor_indexes(neighbor_pairs)
    imbalanced_rows, imbalanced_neighbor_rows = build_imbalanced_rows(join_rows, neighbor_by_request)
    imbalanced_buckets = build_imbalanced_buckets(imbalanced_rows)
    requirement_type_counts = Counter(str(row["requirement_type"]) for row in requirements)
    requirement_status_counts = Counter(str(row["requirement_status"]) for row in requirements)
    imbalanced_descriptor_counts = Counter(str(row["route_alignment_descriptor"]) for row in imbalanced_rows)
    counts = {
        "join_input_rows": len(join_rows),
        "neighbor_pair_input_rows": len(neighbor_pairs),
        "alt_gap_input_rows": len(alt_gaps),
        "alt_candidate_input_rows": len(alt_candidates),
        "requirement_rows": len(requirements),
        "requirement_group_rows": len(requirement_groups),
        "missing_depth_file_requirement_rows": requirement_type_counts["MISSING_DEPTH_FILE_SOURCE_DATE_REQUIREMENT"],
        "earlier_book_history_requirement_rows": requirement_type_counts["EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT"],
        "event_window_alignment_requirement_rows": requirement_type_counts["EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT"],
        "near_match_requirement_rows": sum(1 for row in requirements if int(row.get("near_candidate_count") or 0) > 0),
        "imbalanced_ladder_rows": len(imbalanced_rows),
        "imbalanced_neighbor_context_rows": len(imbalanced_neighbor_rows),
        "imbalanced_bucket_rows": len(imbalanced_buckets),
        "question_rows": 0,
    }
    questions = build_questions(requirement_type_counts, requirement_status_counts, imbalanced_descriptor_counts, counts)
    counts["question_rows"] = len(questions)
    write_jsonl(REQUIREMENT_LEDGER, requirements)
    write_jsonl(REQUIREMENT_GROUP_LEDGER, requirement_groups)
    write_jsonl(IMBALANCED_LEDGER, imbalanced_rows)
    write_jsonl(IMBALANCED_NEIGHBOR_LEDGER, imbalanced_neighbor_rows)
    write_jsonl(IMBALANCED_BUCKET_LEDGER, imbalanced_buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_gap_requirement_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_REQUIREMENT_AND_IMBALANCED_INSPECTION_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "requirement_type_counts": dict(sorted(requirement_type_counts.items())),
        "requirement_status_counts": dict(sorted(requirement_status_counts.items())),
        "imbalanced_route_descriptor_counts": dict(sorted(imbalanced_descriptor_counts.items())),
        "not_completion": "This packet converts current ladder blockers into work requirements and inspections; it does not complete the 60-hour objective.",
        "next_same_resource_work": [
            "search or request exact missing .depth source-date files",
            "audit delayed/suffixed NQ near-match semantics before substitution",
            "split imbalanced rows by command-ladder sign relation and same-source neighbor context",
            "continue mutation rows answerable from current data",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, requirement_type_counts)
    write_summary(generated_utc, counts, requirement_type_counts, requirement_status_counts, imbalanced_descriptor_counts)
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
