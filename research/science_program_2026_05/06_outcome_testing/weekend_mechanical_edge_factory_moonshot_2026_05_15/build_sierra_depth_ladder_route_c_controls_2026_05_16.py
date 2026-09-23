#!/usr/bin/env python3
"""Join Sierra ladder snapshots back to the full Route C depth request set.

The ladder probe repaired the feasible prior-clear subset. This builder keeps
that subset inside the full depth request denominator, preserves every source
gap and no-prior-clear blocker, and builds same-source intraday pair controls
without truncating to representative examples.
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

COMMAND_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_ROUTE_C_COMMAND_FLOW_JOIN_LEDGER_{STAMP}.jsonl"
LADDER_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_FEATURE_LEDGER_{STAMP}.jsonl"
LADDER_BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SNAPSHOT_BLOCKER_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_RESULT_{STAMP}.json"
JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_BUCKET_CONTROL_LEDGER_{STAMP}.jsonl"
NEIGHBOR_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_NEIGHBOR_INTRADAY_PAIR_LEDGER_{STAMP}.jsonl"
NEIGHBOR_BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_NEIGHBOR_INTRADAY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth ladder boundary60 descriptors joined to Route C/Sierra controls; "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

CONTROL_FAMILIES = [
    ("ladder_bucket_all_requests", ("ladder_snapshot_bucket",), ()),
    ("ladder_bucket_by_command_bucket", ("ladder_snapshot_bucket", "command_feature_bucket"), ("command_feature_bucket",)),
    ("ladder_bucket_by_request_family", ("ladder_snapshot_bucket", "request_family"), ("request_family",)),
    ("ladder_bucket_by_source_symbol", ("ladder_snapshot_bucket", "source_symbol"), ("source_symbol",)),
    ("ladder_bucket_by_route_c_queue", ("ladder_snapshot_bucket", "route_c_queue_id"), ("route_c_queue_id",)),
    (
        "ladder_bucket_by_residual_family",
        ("ladder_snapshot_bucket", "route_c_mechanism_family"),
        ("route_c_mechanism_family",),
    ),
    (
        "ladder_imbalance_sign_by_command_imbalance_sign",
        ("ladder_event_boundary60_imbalance_sign", "command_event15_imbalance_sign"),
        ("command_event15_imbalance_sign",),
    ),
]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


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


def hhi(values: list[str]) -> float | None:
    if not values:
        return None
    counts = Counter(values)
    total = len(values)
    return sum((count / total) ** 2 for count in counts.values())


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def sign_bucket(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "unknown"
    if number > 0:
        return "positive"
    if number < 0:
        return "negative"
    return "zero"


def delta(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def residual_context(row: dict[str, Any]) -> dict[str, Any]:
    context = row.get("route_c_residual_context")
    return context if isinstance(context, dict) else {}


def ladder_join_status(row: dict[str, Any], feature: dict[str, Any] | None, blocker: dict[str, Any] | None) -> str:
    if feature and blocker:
        return "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED"
    if feature:
        return "LADDER_FEATURE_JOINED"
    if blocker:
        return "LADDER_BLOCKER_JOINED"
    if row.get("depth_file_exists") is False:
        return "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE"
    return "LADDER_NOT_COMPUTED_UNCLASSIFIED_LOCAL_ROW"


def build_join_rows(
    command_rows: list[dict[str, Any]],
    feature_by_request: dict[str, dict[str, Any]],
    blocker_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in command_rows:
        request_id = str(row["request_id"])
        feature = feature_by_request.get(request_id)
        blocker = blocker_by_request.get(request_id)
        residual = residual_context(row)
        bucket = "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE" if row.get("depth_file_exists") is False else "LADDER_NOT_COMPUTED_UNCLASSIFIED_LOCAL_ROW"
        if feature:
            bucket = str(feature.get("ladder_snapshot_bucket"))
        elif blocker:
            bucket = str(blocker.get("blocker_type"))
        joined = {
            **row,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
            "command_feature_bucket": row.get("command_feature_bucket", row.get("feature_bucket")),
            "command_event15_imbalance_sign": row.get(
                "command_event15_imbalance_sign",
                row.get("event15_imbalance_sign"),
            ),
            "ladder_join_status": ladder_join_status(row, feature, blocker),
            "ladder_snapshot_bucket": bucket,
            "ladder_replay_status": None,
            "ladder_blocker_type": None if blocker is None else blocker.get("blocker_type"),
            "ladder_event_boundary60_imbalance_sign": "unknown",
            "route_c_mechanism_family": residual.get("route_c_mechanism_family"),
            "route_c_residual_transfer_class": residual.get("residual_transfer_class"),
            "route_c_full_control_bucket": residual.get("full_control_bucket"),
        }
        if feature:
            joined.update(
                {
                    "ladder_replay_status": feature.get("ladder_replay_status"),
                    "ladder_sample_method": feature.get("ladder_sample_method"),
                    "ladder_event_boundary60_sample_count": feature.get("event_boundary60_sample_count"),
                    "ladder_event_boundary60_median_depth10_imbalance": feature.get("event_boundary60_median_depth10_imbalance"),
                    "ladder_event_boundary60_median_depth20_imbalance": feature.get("event_boundary60_median_depth20_imbalance"),
                    "ladder_event_boundary60_median_total_depth10": feature.get("event_boundary60_median_total_depth10"),
                    "ladder_event_boundary60_median_total_depth20": feature.get("event_boundary60_median_total_depth20"),
                    "ladder_event_boundary60_thin_depth10_rate": feature.get("event_boundary60_thin_depth10_rate"),
                    "ladder_event_boundary60_median_max_bid_wall": feature.get("event_boundary60_median_max_bid_wall"),
                    "ladder_event_boundary60_median_max_ask_wall": feature.get("event_boundary60_median_max_ask_wall"),
                    "ladder_event_boundary60_median_wall_concentration10": feature.get("event_boundary60_median_wall_concentration10"),
                    "ladder_event_boundary60_mid_change_ticks": feature.get("event_boundary60_mid_change_ticks"),
                    "ladder_pre_boundary60_sample_count": feature.get("pre_boundary60_sample_count"),
                    "ladder_pre_boundary60_median_depth10_imbalance": feature.get("pre_boundary60_median_depth10_imbalance"),
                    "ladder_pre_boundary60_median_total_depth10": feature.get("pre_boundary60_median_total_depth10"),
                    "ladder_pre_boundary60_mid_change_ticks": feature.get("pre_boundary60_mid_change_ticks"),
                    "ladder_replay_start_record_index": feature.get("ladder_replay_start_record_index"),
                    "ladder_event_boundary60_imbalance_sign": sign_bucket(feature.get("event_boundary60_median_depth10_imbalance")),
                }
            )
        if blocker and not feature:
            joined["ladder_replay_status"] = blocker.get("ladder_replay_status")
        rows.append(joined)
    return rows


def descriptor_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_alignment: list[bool] = []
    sierra_delta_alignment: list[bool] = []
    route_abs: list[float] = []
    route_per_range: list[float] = []
    ladder_imbalance: list[float] = []
    ladder_depth10: list[float] = []
    ladder_sample_count: list[float] = []
    command_bid_share: list[float] = []
    feature_rows = 0
    blocker_rows = 0
    source_gap_rows = 0
    no_prior_clear_rows = 0
    for row in rows:
        if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None:
            route_alignment.append(value)
        if (value := bool_value(row.get("sierra_future_follows_delta_sign"))) is not None:
            sierra_delta_alignment.append(value)
        for key, target in [
            ("route_c_future_abs_change", route_abs),
            ("route_c_future_change_per_current_range", route_per_range),
            ("ladder_event_boundary60_median_depth10_imbalance", ladder_imbalance),
            ("ladder_event_boundary60_median_total_depth10", ladder_depth10),
            ("ladder_event_boundary60_sample_count", ladder_sample_count),
            ("event15_depth_bid_quantity_share", command_bid_share),
        ]:
            number = safe_float(row.get(key))
            if number is not None:
                target.append(number)
        status = str(row.get("ladder_join_status"))
        if "FEATURE" in status:
            feature_rows += 1
        if "BLOCKER" in status:
            blocker_rows += 1
        if status == "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE":
            source_gap_rows += 1
        if row.get("ladder_snapshot_bucket") == "LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW":
            no_prior_clear_rows += 1
    row_count = len(rows)
    source_dates = [str(row.get("source_date")) for row in rows if row.get("source_date")]
    return {
        "n": row_count,
        "feature_rows": feature_rows,
        "blocker_rows": blocker_rows,
        "source_gap_rows": source_gap_rows,
        "no_prior_clear_rows": no_prior_clear_rows,
        "feature_share": feature_rows / row_count if row_count else None,
        "source_gap_share": source_gap_rows / row_count if row_count else None,
        "no_prior_clear_share": no_prior_clear_rows / row_count if row_count else None,
        "ladder_bucket_counts": counter_dict([row.get("ladder_snapshot_bucket") for row in rows]),
        "command_bucket_counts": counter_dict([row.get("command_feature_bucket") for row in rows]),
        "source_symbol_counts": counter_dict([row.get("source_symbol") for row in rows]),
        "source_date_count": len(set(source_dates)),
        "source_date_hhi": hhi(source_dates),
        "route_c_queue_count": len({str(row.get("route_c_queue_id")) for row in rows if row.get("route_c_queue_id")}),
        "route_c_delta_alignment_descriptor_share": share(route_alignment),
        "route_c_delta_alignment_descriptor_n": len(route_alignment),
        "sierra_delta_alignment_descriptor_share": share(sierra_delta_alignment),
        "sierra_delta_alignment_descriptor_n": len(sierra_delta_alignment),
        "mean_route_c_abs_future_change_descriptor": mean(route_abs),
        "mean_route_c_future_change_per_current_range_descriptor": mean(route_per_range),
        "mean_ladder_event_boundary60_depth10_imbalance": mean(ladder_imbalance),
        "mean_ladder_event_boundary60_total_depth10": mean(ladder_depth10),
        "mean_ladder_event_boundary60_sample_count": mean(ladder_sample_count),
        "mean_command_event15_bid_quantity_share": mean(command_bid_share),
    }


def control_basis(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    out: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[tuple(row.get(key) for key in keys)].append(row)
    return out


def classify_control(stats: dict[str, Any], denom: dict[str, Any]) -> str:
    if stats["n"] < 20:
        return "UNDERPOWERED_LADDER_GROUP_N_LT_20"
    if stats.get("source_gap_share") is not None and stats["source_gap_share"] >= 0.80:
        return "SOURCE_GAP_DOMINATES_LADDER_CONTEXT"
    if stats.get("no_prior_clear_share") is not None and stats["no_prior_clear_share"] >= 0.50:
        return "NO_PRIOR_CLEAR_DOMINATES_LADDER_CONTEXT"
    if stats.get("feature_share") == 0:
        return "NO_LADDER_FEATURE_ROWS_IN_GROUP"
    route_delta = delta(
        stats.get("route_c_delta_alignment_descriptor_share"),
        denom.get("route_c_delta_alignment_descriptor_share"),
    )
    if route_delta is None:
        return "NO_DIRECTIONAL_DESCRIPTOR_AVAILABLE"
    if route_delta >= 0.10:
        return "LADDER_BUCKET_ABOVE_DENOMINATOR_DESCRIPTIVE"
    if route_delta <= -0.10:
        return "LADDER_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR"
    if abs(route_delta) <= 0.05:
        return "LADDER_BUCKET_NEAR_DENOMINATOR_GENERIC_CONTEXT"
    return "LADDER_BUCKET_MIXED_SMALL_DESCRIPTOR_DIFFERENCE"


def build_bucket_controls(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    out: list[dict[str, Any]] = []
    buckets: Counter[str] = Counter()
    idx = 0
    for family, group_keys, denom_keys in CONTROL_FAMILIES:
        group_map = control_basis(rows, group_keys)
        denom_map = control_basis(rows, denom_keys)
        for group_key, group in sorted(group_map.items(), key=lambda item: tuple(str(x) for x in item[0])):
            idx += 1
            denom_key = tuple(group_key[group_keys.index(key)] for key in denom_keys)
            denom = denom_map.get(denom_key, rows)
            stats = descriptor_stats(group)
            denom_stats = descriptor_stats(denom)
            bucket = classify_control(stats, denom_stats)
            buckets[bucket] += 1
            out.append(
                {
                    "route_id": ROUTE_ID,
                    "ladder_control_id": f"SIERRA-DEPTH-LADDER-CONTROL-{idx:05d}",
                    "control_family": family,
                    "group_keys": list(group_keys),
                    "group_values": {key: value for key, value in zip(group_keys, group_key, strict=True)},
                    "denominator_keys": list(denom_keys),
                    "denominator_values": {key: value for key, value in zip(denom_keys, denom_key, strict=True)},
                    "stats": stats,
                    "denominator_stats": denom_stats,
                    "route_alignment_delta_vs_denominator": delta(
                        stats.get("route_c_delta_alignment_descriptor_share"),
                        denom_stats.get("route_c_delta_alignment_descriptor_share"),
                    ),
                    "mean_ladder_depth10_imbalance_delta_vs_denominator": delta(
                        stats.get("mean_ladder_event_boundary60_depth10_imbalance"),
                        denom_stats.get("mean_ladder_event_boundary60_depth10_imbalance"),
                    ),
                    "control_bucket": bucket,
                    "next_same_resource_action": next_action_for_control(bucket),
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return out, buckets


def offset_bucket(minutes: float | None) -> str:
    if minutes is None:
        return "OFFSET_UNKNOWN"
    if minutes == 0:
        return "OFFSET_SAME_MINUTE"
    if minutes <= 15:
        return "OFFSET_LE_15M"
    if minutes <= 60:
        return "OFFSET_LE_60M"
    if minutes <= 240:
        return "OFFSET_LE_4H"
    return "OFFSET_GT_4H"


def build_neighbor_pairs(feature_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in feature_rows:
        grouped[(str(row.get("source_symbol")), str(row.get("source_date")))].append(row)
    pairs: list[dict[str, Any]] = []
    for (source_symbol, source_date), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: (str(row.get("event15_start_utc")), str(row.get("request_id"))))
        for left_idx in range(len(ordered)):
            left = ordered[left_idx]
            left_dt = parse_dt(left.get("event15_start_utc"))
            for right in ordered[left_idx + 1 :]:
                right_dt = parse_dt(right.get("event15_start_utc"))
                minutes = None
                if left_dt is not None and right_dt is not None:
                    minutes = abs((right_dt - left_dt).total_seconds()) / 60.0
                left_align = bool_value(left.get("route_c_delta_aligned_with_future"))
                right_align = bool_value(right.get("route_c_delta_aligned_with_future"))
                pair_bucket = f"{left.get('ladder_snapshot_bucket')}|{right.get('ladder_snapshot_bucket')}"
                pairs.append(
                    {
                        "route_id": ROUTE_ID,
                        "pair_id": f"SIERRA-DEPTH-LADDER-PAIR-{len(pairs) + 1:06d}",
                        "source_symbol": source_symbol,
                        "source_date": source_date,
                        "left_request_id": left.get("request_id"),
                        "right_request_id": right.get("request_id"),
                        "left_ladder_bucket": left.get("ladder_snapshot_bucket"),
                        "right_ladder_bucket": right.get("ladder_snapshot_bucket"),
                        "ladder_bucket_pair": pair_bucket,
                        "same_ladder_bucket": left.get("ladder_snapshot_bucket") == right.get("ladder_snapshot_bucket"),
                        "left_command_bucket": left.get("command_feature_bucket"),
                        "right_command_bucket": right.get("command_feature_bucket"),
                        "same_command_bucket": left.get("command_feature_bucket") == right.get("command_feature_bucket"),
                        "minutes_between_event15": minutes,
                        "offset_bucket": offset_bucket(minutes),
                        "left_route_c_delta_aligned_with_future": left_align,
                        "right_route_c_delta_aligned_with_future": right_align,
                        "same_route_alignment_bool": None if left_align is None or right_align is None else left_align == right_align,
                        "abs_route_c_future_change_delta": None
                        if safe_float(left.get("route_c_future_abs_change")) is None
                        or safe_float(right.get("route_c_future_abs_change")) is None
                        else abs(float(left["route_c_future_abs_change"]) - float(right["route_c_future_abs_change"])),
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "safe_flags": SAFE_FLAGS,
                    }
                )
    bucket_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        bucket_map[(str(row.get("offset_bucket")), str(row.get("ladder_bucket_pair")))].append(row)
    bucket_rows: list[dict[str, Any]] = []
    for idx, ((off_bucket, ladder_pair), group) in enumerate(sorted(bucket_map.items()), 1):
        same_alignment = [
            value for row in group
            if (value := bool_value(row.get("same_route_alignment_bool"))) is not None
        ]
        abs_delta_values = [
            value for row in group
            if (value := safe_float(row.get("abs_route_c_future_change_delta"))) is not None
        ]
        bucket_rows.append(
            {
                "route_id": ROUTE_ID,
                "neighbor_bucket_id": f"SIERRA-DEPTH-LADDER-NEIGHBOR-BUCKET-{idx:05d}",
                "offset_bucket": off_bucket,
                "ladder_bucket_pair": ladder_pair,
                "pair_rows": len(group),
                "source_symbol_counts": counter_dict([row.get("source_symbol") for row in group]),
                "source_date_count": len({str(row.get("source_date")) for row in group}),
                "same_ladder_bucket_share": share([bool(row.get("same_ladder_bucket")) for row in group]),
                "same_command_bucket_share": share([bool(row.get("same_command_bucket")) for row in group]),
                "same_route_alignment_share": share(same_alignment),
                "mean_abs_route_c_future_change_delta": mean(abs_delta_values),
                "control_bucket": classify_neighbor_bucket(off_bucket, ladder_pair, len(group), share(same_alignment)),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return pairs, bucket_rows


def classify_neighbor_bucket(off_bucket: str, ladder_pair: str, n: int, same_alignment_share: float | None) -> str:
    if n < 20:
        return "UNDERPOWERED_NEIGHBOR_PAIR_BUCKET_N_LT_20"
    if "NO_EVENT_SAMPLES" in ladder_pair or "BLOCKED_NO_PRIOR_CLEAR" in ladder_pair:
        return "NEIGHBOR_BUCKET_CONTAINS_LADDER_BLOCKER"
    if off_bucket in {"OFFSET_LE_15M", "OFFSET_LE_60M"} and same_alignment_share is not None and same_alignment_share >= 0.65:
        return "SAME_SOURCE_NEARBY_ALIGNMENT_CLUSTERS"
    if same_alignment_share is not None and same_alignment_share <= 0.45:
        return "SAME_SOURCE_NEIGHBOR_ALIGNMENT_UNSTABLE"
    return "SAME_SOURCE_NEIGHBOR_GENERIC_CONTEXT"


def next_action_for_control(bucket: str) -> str:
    if bucket == "LADDER_BUCKET_ABOVE_DENOMINATOR_DESCRIPTIVE":
        return "deepen with full same-source neighbor pairs and route-specific forward-capture design"
    if bucket == "LADDER_BUCKET_BELOW_DENOMINATOR_AVOID_OR_WEAKENING_DESCRIPTOR":
        return "test as avoid/filter intelligence against same-source intraday controls"
    if bucket == "SOURCE_GAP_DOMINATES_LADDER_CONTEXT":
        return "repair exact missing depth source dates before interpreting this group"
    if bucket == "NO_PRIOR_CLEAR_DOMINATES_LADDER_CONTEXT":
        return "treat as earlier-book-history capture requirement before ladder interpretation"
    if bucket == "UNDERPOWERED_LADDER_GROUP_N_LT_20":
        return "aggregate to broader preserved families or acquire more same-source rows"
    return "preserve as descriptor/control context and continue same-resource mutation"


def build_questions(control_buckets: Counter[str], neighbor_buckets: Counter[str], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    idx = 0
    for bucket, count in sorted(control_buckets.items()):
        idx += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-ROUTEC-Q-{idx:03d}",
                "question_family": "ladder_route_c_control_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What same-resource repair, split, or mutation follows for all {count} ladder control rows in {bucket}?",
                "next_same_resource_action": next_action_for_control(bucket),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(neighbor_buckets.items()):
        idx += 1
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-ROUTEC-Q-{idx:03d}",
                "question_family": "same_source_neighbor_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What intraday-offset source-control implication follows for all {count} neighbor buckets in {bucket}?",
                "next_same_resource_action": "use full pair ledger to split clustered versus unstable same-source ladder contexts",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_route_c_control_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_route_c_control_result", "created"),
        (JOIN_LEDGER, "sierra_depth_ladder_route_c_join_ledger", "created"),
        (BUCKET_CONTROL_LEDGER, "sierra_depth_ladder_route_c_bucket_control_ledger", "created"),
        (NEIGHBOR_PAIR_LEDGER, "sierra_depth_ladder_route_c_neighbor_pair_ledger", "created"),
        (NEIGHBOR_BUCKET_LEDGER, "sierra_depth_ladder_route_c_neighbor_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_route_c_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_route_c_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], buckets: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_route_c_controls",
        "status": "done",
        "route": "sierra_depth_ladder_route_c_same_source_controls",
        "details": "Joined ladder boundary60 buckets to the full Route C depth request universe and emitted same-source intraday pair controls.",
        "counts": counts,
        "control_bucket_counts": dict(sorted(buckets.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(JOIN_LEDGER),
            relative(BUCKET_CONTROL_LEDGER),
            relative(NEIGHBOR_PAIR_LEDGER),
            relative(NEIGHBOR_BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], control_buckets: Counter[str], neighbor_buckets: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Ladder Route C Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: ladder boundary60 descriptors joined to Route C/Sierra depth controls only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Ladder Control Buckets", ""])
    for bucket, count in sorted(control_buckets.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(["", "## Neighbor Control Buckets", ""])
    for bucket, count in sorted(neighbor_buckets.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- Convert no-prior-clear rows into earlier-book-history capture requirements.",
            "- Inspect imbalanced ladder rows against command-flow and same-source pair ledgers.",
            "- Use underpowered and source-gap buckets as acquisition/aggregation requirements, not stopping labels.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    command_rows = read_jsonl(COMMAND_JOIN_LEDGER)
    ladder_features = read_jsonl(LADDER_FEATURE_LEDGER)
    ladder_blockers = read_jsonl(LADDER_BLOCKER_LEDGER)
    feature_by_request = {str(row["request_id"]): row for row in ladder_features}
    blocker_by_request = {str(row["request_id"]): row for row in ladder_blockers}
    join_rows = build_join_rows(command_rows, feature_by_request, blocker_by_request)
    bucket_controls, control_bucket_counts = build_bucket_controls(join_rows)
    feature_join_rows = [row for row in join_rows if "FEATURE" in str(row.get("ladder_join_status"))]
    neighbor_pairs, neighbor_buckets = build_neighbor_pairs(feature_join_rows)
    neighbor_bucket_counts = Counter(str(row["control_bucket"]) for row in neighbor_buckets)
    counts = {
        "command_join_input_rows": len(command_rows),
        "ladder_feature_input_rows": len(ladder_features),
        "ladder_blocker_input_rows": len(ladder_blockers),
        "joined_rows": len(join_rows),
        "ladder_feature_join_rows": len(feature_join_rows),
        "ladder_blocker_join_rows": sum(1 for row in join_rows if "BLOCKER" in str(row.get("ladder_join_status"))),
        "source_gap_ladder_rows": sum(1 for row in join_rows if row.get("ladder_join_status") == "LADDER_SOURCE_GAP_MISSING_DEPTH_FILE"),
        "bucket_control_rows": len(bucket_controls),
        "neighbor_pair_rows": len(neighbor_pairs),
        "neighbor_bucket_rows": len(neighbor_buckets),
        "question_rows": 0,
    }
    questions = build_questions(control_bucket_counts, neighbor_bucket_counts, counts)
    counts["question_rows"] = len(questions)
    write_jsonl(JOIN_LEDGER, join_rows)
    write_jsonl(BUCKET_CONTROL_LEDGER, bucket_controls)
    write_jsonl(NEIGHBOR_PAIR_LEDGER, neighbor_pairs)
    write_jsonl(NEIGHBOR_BUCKET_LEDGER, neighbor_buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_route_c_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "control_bucket_counts": dict(sorted(control_bucket_counts.items())),
        "neighbor_control_bucket_counts": dict(sorted(neighbor_bucket_counts.items())),
        "not_completion": "This control packet deepens the depth route but does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "convert no-prior-clear and source-gap rows into exact capture requirements",
            "inspect imbalanced ladder rows against command-flow and neighbor pair ledgers",
            "continue mutation rows answerable from current depth/SCID/tick data",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, control_bucket_counts)
    write_summary(generated_utc, counts, control_bucket_counts, neighbor_bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
