#!/usr/bin/env python3
"""Split imbalanced Sierra ladder rows after fallback and neighbor proof."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

IMBALANCED_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_ROW_INSPECTION_LEDGER_{STAMP}.jsonl"
IMBALANCED_NEIGHBOR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_NEIGHBOR_CONTEXT_LEDGER_{STAMP}.jsonl"
IMBALANCED_BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_BUCKET_LEDGER_{STAMP}.jsonl"
ROUTE_C_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
FALLBACK_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_TARGET_LEDGER_{STAMP}.jsonl"
REQUIREMENT_AFTER_FALLBACK_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_RESULT_{STAMP}.json"
ROW_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_ROW_LEDGER_{STAMP}.jsonl"
NEIGHBOR_CONTEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_NEIGHBOR_LEDGER_{STAMP}.jsonl"
FALLBACK_CONTEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_FALLBACK_CONTEXT_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth imbalanced ladder descriptor split after record-level no-event "
    "fallback and same-source neighbor controls; no strategy validation, trade "
    "outcome, R/PnL, expectancy, live-readiness, or promotion"
)


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


def safe_counter(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return safe_counter([row.get(key) for row in rows])


def bool_count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return safe_counter([row.get(key) for row in rows])


def share(num: int, denom: int) -> float | None:
    if denom <= 0:
        return None
    return num / denom


def source_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("source_symbol")), str(row.get("source_date"))


def classify_neighbor_context(neighbor_rows: list[dict[str, Any]]) -> str:
    if not neighbor_rows:
        return "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_CONTEXT"
    pair_count = len(neighbor_rows)
    known_route = [row for row in neighbor_rows if row.get("same_route_alignment_bool") is not None]
    aligned = sum(1 for row in known_route if row.get("same_route_alignment_bool") is True)
    same_ladder = sum(1 for row in neighbor_rows if row.get("same_ladder_bucket") is True)
    no_event_pairs = sum(1 for row in neighbor_rows if "NO_EVENT" in str(row.get("ladder_bucket_pair")))
    if pair_count < 20:
        if no_event_pairs:
            return "IMBALANCED_UNDERPOWERED_NEIGHBOR_WITH_NO_EVENT_CONTEXT"
        return "IMBALANCED_UNDERPOWERED_NEIGHBOR_CONTEXT"
    if known_route and share(aligned, len(known_route)) is not None:
        aligned_share = share(aligned, len(known_route)) or 0.0
        if aligned_share >= 0.60 and same_ladder == 0:
            return "IMBALANCED_NEIGHBOR_ROUTE_ALIGNMENT_SUPPORTS_BUT_LADDER_NOT_REPEATED"
        if aligned_share <= 0.40:
            return "IMBALANCED_NEIGHBOR_ROUTE_ALIGNMENT_WEAKENS_DESCRIPTOR"
    if same_ladder > 0:
        return "IMBALANCED_NEIGHBOR_SAME_LADDER_REPEATS_SPARSELY"
    return "IMBALANCED_NEIGHBOR_MIXED_DESCRIPTIVE_CONTEXT"


def classify_fallback_context(fallback_rows: list[dict[str, Any]]) -> str:
    if not fallback_rows:
        return "NO_SAME_SOURCE_NO_EVENT_FALLBACK_TARGETS"
    control_counts = Counter(str(row.get("target_neighbor_control_bucket")) for row in fallback_rows)
    proxy_counts = Counter(str(row.get("event15_proxy_bucket")) for row in fallback_rows)
    if control_counts.get("SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT"):
        return "SAME_SOURCE_FALLBACK_WEAKENING_CONTEXT_PRESENT"
    if control_counts.get("TARGET_EVENT15_PROXY_SOURCE_GAP_REMAINS") and not (
        control_counts.get("UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20")
        or control_counts.get("SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT")
    ):
        return "SAME_SOURCE_FALLBACK_SOURCE_GAP_ONLY"
    if control_counts.get("UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20") == len(fallback_rows):
        if proxy_counts.get("FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_IMBALANCED_PROXY"):
            return "SAME_SOURCE_FALLBACK_UNDERPOWERED_WITH_IMBALANCED_PROXY"
        return "SAME_SOURCE_FALLBACK_UNDERPOWERED_BALANCED_PROXY_ONLY"
    return "SAME_SOURCE_FALLBACK_MIXED_CONTEXT"


def classify_requirement_context(requirement_rows: list[dict[str, Any]]) -> str:
    if not requirement_rows:
        return "NO_SAME_SOURCE_REQUIREMENT_CONTEXT"
    statuses = Counter(str(row.get("post_fallback_requirement_status")) for row in requirement_rows)
    if statuses.get("LOCAL_FILE_PRESENT_BUT_PRIOR_BOOK_STATE_INSUFFICIENT") == len(requirement_rows):
        return "SAME_SOURCE_REQUIREMENTS_ONLY_EARLIER_BOOK_HISTORY"
    if statuses.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_NEIGHBOR_WEAKENED"):
        return "SAME_SOURCE_REQUIREMENTS_INCLUDE_NO_EVENT_WEAKENING_CONTEXT"
    if statuses.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_UNDERPOWERED_NEIGHBOR"):
        return "SAME_SOURCE_REQUIREMENTS_INCLUDE_NO_EVENT_UNDERPOWERED_CONTEXT"
    if statuses.get("BOUNDARY60_TRUE_EMPTY_AND_EVENT15_EMPTY_SOURCE_GAP_REMAINS"):
        return "SAME_SOURCE_REQUIREMENTS_INCLUDE_NO_EVENT_SOURCE_GAP"
    return "SAME_SOURCE_REQUIREMENTS_MIXED_CONTEXT"


def classify_combined(row: dict[str, Any], neighbor_bucket: str, fallback_bucket: str, requirement_bucket: str) -> str:
    relation = str(row.get("command_ladder_sign_relation"))
    alignment = str(row.get("route_alignment_descriptor"))
    route_aligned = row.get("route_c_delta_aligned_with_future")
    if relation == "COMMAND_AND_LADDER_SIGN_DIVERGE":
        return "DIVERGENT_COMMAND_LADDER_SPLIT_REQUIRED"
    if "WEAKENING" in alignment or route_aligned is False:
        return "AGREEING_COMMAND_LADDER_BUT_ROUTE_OR_CONTROL_WEAKENED"
    if neighbor_bucket == "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_CONTEXT":
        return "AGREEING_IMBALANCE_WITH_NO_NEIGHBOR_SUPPORT"
    if "UNDERPOWERED" in neighbor_bucket or "UNDERPOWERED" in fallback_bucket or "UNDERPOWERED" in requirement_bucket:
        return "AGREEING_IMBALANCE_WITH_UNDERPOWERED_CONTEXT"
    if "WEAKEN" in fallback_bucket or "WEAKEN" in requirement_bucket:
        return "AGREEING_IMBALANCE_WITH_SAME_SOURCE_WEAKENING_CONTEXT"
    if route_aligned is True and "SUPPORTS" in neighbor_bucket:
        return "AGREEING_ROUTE_ALIGNED_IMBALANCE_WITH_NEIGHBOR_SUPPORT"
    if route_aligned is None:
        return "AGREEING_IMBALANCE_ROUTE_ALIGNMENT_UNKNOWN"
    return "AGREEING_IMBALANCE_MIXED_DESCRIPTOR_CONTEXT"


def build_rows(
    imbalanced_rows: list[dict[str, Any]],
    neighbor_by_anchor: dict[str, list[dict[str, Any]]],
    fallback_by_source: dict[tuple[str, str], list[dict[str, Any]]],
    requirement_by_source: dict[tuple[str, str], list[dict[str, Any]]],
    route_c_by_request: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    row_outputs: list[dict[str, Any]] = []
    neighbor_outputs: list[dict[str, Any]] = []
    fallback_outputs: list[dict[str, Any]] = []

    for idx, row in enumerate(sorted(imbalanced_rows, key=lambda item: str(item.get("request_id"))), start=1):
        request_id = str(row.get("request_id"))
        key = source_key(row)
        neighbors = neighbor_by_anchor.get(request_id, [])
        fallback_rows = fallback_by_source.get(key, [])
        requirement_rows = requirement_by_source.get(key, [])
        route_c = route_c_by_request.get(request_id, {})

        known_route_neighbors = [item for item in neighbors if item.get("same_route_alignment_bool") is not None]
        same_route_alignment_true = sum(1 for item in known_route_neighbors if item.get("same_route_alignment_bool") is True)
        same_command_true = sum(1 for item in neighbors if item.get("same_command_bucket") is True)
        same_ladder_true = sum(1 for item in neighbors if item.get("same_ladder_bucket") is True)
        no_event_neighbor_pairs = sum(1 for item in neighbors if "NO_EVENT" in str(item.get("ladder_bucket_pair")))

        neighbor_bucket = classify_neighbor_context(neighbors)
        fallback_bucket = classify_fallback_context(fallback_rows)
        requirement_bucket = classify_requirement_context(requirement_rows)
        combined_bucket = classify_combined(row, neighbor_bucket, fallback_bucket, requirement_bucket)

        out = {
            "split_row_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-{idx:05d}",
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "request_id": request_id,
            "imbalanced_inspection_id": row.get("imbalanced_inspection_id"),
            "source_symbol": row.get("source_symbol"),
            "source_date": row.get("source_date"),
            "depth_path": row.get("depth_path"),
            "bar_start_utc": row.get("bar_start_utc"),
            "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
            "horizon_id": row.get("horizon_id"),
            "route_c_queue_id": row.get("route_c_queue_id"),
            "route_c_symbol": row.get("route_c_symbol"),
            "route_c_primitive_flag": row.get("route_c_primitive_flag"),
            "route_c_mechanism_family": row.get("route_c_mechanism_family"),
            "route_c_full_control_bucket": row.get("route_c_full_control_bucket"),
            "route_c_residual_transfer_class": row.get("route_c_residual_transfer_class"),
            "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
            "route_c_future_abs_change": row.get("route_c_future_abs_change"),
            "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
            "route_c_join_status": route_c.get("ladder_join_status"),
            "route_c_join_snapshot_bucket": route_c.get("ladder_snapshot_bucket"),
            "command_feature_bucket": row.get("command_feature_bucket"),
            "command_event15_imbalance_sign": row.get("command_event15_imbalance_sign"),
            "command_event15_bid_quantity_share": row.get("command_event15_bid_quantity_share"),
            "command_event15_bid_minus_ask_quantity_sum": row.get("command_event15_bid_minus_ask_quantity_sum"),
            "command_ladder_sign_relation": row.get("command_ladder_sign_relation"),
            "ladder_event_boundary60_imbalance_sign": row.get("ladder_event_boundary60_imbalance_sign"),
            "ladder_event_boundary60_median_depth10_imbalance": row.get("ladder_event_boundary60_median_depth10_imbalance"),
            "ladder_event_boundary60_median_depth20_imbalance": row.get("ladder_event_boundary60_median_depth20_imbalance"),
            "ladder_event_boundary60_median_total_depth10": row.get("ladder_event_boundary60_median_total_depth10"),
            "ladder_event_boundary60_median_wall_concentration10": row.get("ladder_event_boundary60_median_wall_concentration10"),
            "ladder_event_boundary60_mid_change_ticks": row.get("ladder_event_boundary60_mid_change_ticks"),
            "ladder_event_boundary60_sample_count": row.get("ladder_event_boundary60_sample_count"),
            "route_alignment_descriptor": row.get("route_alignment_descriptor"),
            "neighbor_context_bucket_original": row.get("neighbor_context_bucket"),
            "neighbor_pair_rows": len(neighbors),
            "neighbor_known_route_alignment_rows": len(known_route_neighbors),
            "neighbor_same_route_alignment_true": same_route_alignment_true,
            "neighbor_same_route_alignment_share": share(same_route_alignment_true, len(known_route_neighbors)),
            "neighbor_same_command_bucket_true": same_command_true,
            "neighbor_same_command_bucket_share": share(same_command_true, len(neighbors)),
            "neighbor_same_ladder_bucket_true": same_ladder_true,
            "neighbor_same_ladder_bucket_share": share(same_ladder_true, len(neighbors)),
            "neighbor_no_event_pair_rows": no_event_neighbor_pairs,
            "neighbor_ladder_bucket_pair_counts": count_by(neighbors, "ladder_bucket_pair"),
            "neighbor_split_bucket": neighbor_bucket,
            "same_source_fallback_target_rows": len(fallback_rows),
            "same_source_fallback_control_bucket_counts": count_by(fallback_rows, "target_neighbor_control_bucket"),
            "same_source_fallback_event15_proxy_bucket_counts": count_by(fallback_rows, "event15_proxy_bucket"),
            "fallback_context_bucket": fallback_bucket,
            "same_source_requirement_rows": len(requirement_rows),
            "same_source_requirement_status_counts": count_by(requirement_rows, "post_fallback_requirement_status"),
            "same_source_requirement_type_counts": count_by(requirement_rows, "requirement_type"),
            "requirement_context_bucket": requirement_bucket,
            "combined_split_bucket": combined_bucket,
            "next_same_resource_action": next_action(combined_bucket, neighbor_bucket, fallback_bucket, requirement_bucket),
        }
        row_outputs.append(out)

        for n_idx, neighbor in enumerate(neighbors, start=1):
            neighbor_outputs.append(
                {
                    "split_neighbor_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-NEIGHBOR-{len(neighbor_outputs) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "anchor_request_id": request_id,
                    "anchor_split_row_id": out["split_row_id"],
                    "anchor_combined_split_bucket": combined_bucket,
                    "anchor_neighbor_split_bucket": neighbor_bucket,
                    "neighbor_ordinal_for_anchor": n_idx,
                    **neighbor,
                }
            )

        for f_idx, fallback in enumerate(fallback_rows, start=1):
            fallback_outputs.append(
                {
                    "split_fallback_context_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-FALLBACK-{len(fallback_outputs) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "anchor_request_id": request_id,
                    "anchor_split_row_id": out["split_row_id"],
                    "anchor_combined_split_bucket": combined_bucket,
                    "anchor_fallback_context_bucket": fallback_bucket,
                    "fallback_ordinal_for_anchor": f_idx,
                    **fallback,
                }
            )

    return row_outputs, neighbor_outputs, fallback_outputs


def next_action(combined_bucket: str, neighbor_bucket: str, fallback_bucket: str, requirement_bucket: str) -> str:
    if combined_bucket == "DIVERGENT_COMMAND_LADDER_SPLIT_REQUIRED":
        return "split as potential divergence/avoid descriptor; do not merge with agreeing imbalanced rows"
    if combined_bucket == "AGREEING_COMMAND_LADDER_BUT_ROUTE_OR_CONTROL_WEAKENED":
        return "carry as weakening descriptor and compare only inside same route/control bucket"
    if combined_bucket == "AGREEING_IMBALANCE_WITH_NO_NEIGHBOR_SUPPORT":
        return "search same-source expansion or additional source dates before interpretation"
    if "UNDERPOWERED" in combined_bucket or "UNDERPOWERED" in neighbor_bucket or "UNDERPOWERED" in fallback_bucket:
        return "preserve descriptor but require additional same-source neighbor/context rows before stronger interpretation"
    if "WEAKEN" in combined_bucket or "WEAKEN" in fallback_bucket or "WEAKEN" in requirement_bucket:
        return "treat same-source fallback/requirement context as weakening evidence and split before mutation"
    if combined_bucket == "AGREEING_ROUTE_ALIGNED_IMBALANCE_WITH_NEIGHBOR_SUPPORT":
        return "preserve as descriptor-only candidate for source-date deconcentration and exact source expansion"
    if combined_bucket == "AGREEING_IMBALANCE_ROUTE_ALIGNMENT_UNKNOWN":
        return "repair missing route-alignment relation if current ledgers allow; otherwise keep as unknown split"
    return "retain in imbalanced descriptor ledger and route to source-date deconcentration"


def group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("command_ladder_sign_relation", ["command_ladder_sign_relation"]),
        ("route_alignment_descriptor", ["route_alignment_descriptor"]),
        ("source_symbol_date", ["source_symbol", "source_date"]),
        ("route_queue_primitive_horizon", ["route_c_queue_id", "route_c_primitive_flag", "horizon_id"]),
        ("neighbor_split_bucket", ["neighbor_split_bucket"]),
        ("fallback_context_bucket", ["fallback_context_bucket"]),
        ("requirement_context_bucket", ["requirement_context_bucket"]),
        ("combined_split_bucket", ["combined_split_bucket"]),
        (
            "combined_by_command_route_neighbor_fallback",
            [
                "command_ladder_sign_relation",
                "route_alignment_descriptor",
                "neighbor_split_bucket",
                "fallback_context_bucket",
            ],
        ),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "group_family": family,
                    "group_keys": keys,
                    "group_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "request_ids": sorted(str(row.get("request_id")) for row in group),
                    "source_symbol_counts": count_by(group, "source_symbol"),
                    "source_date_counts": count_by(group, "source_date"),
                    "route_c_queue_counts": count_by(group, "route_c_queue_id"),
                    "route_c_primitive_counts": count_by(group, "route_c_primitive_flag"),
                    "route_alignment_descriptor_counts": count_by(group, "route_alignment_descriptor"),
                    "combined_split_bucket_counts": count_by(group, "combined_split_bucket"),
                    "neighbor_pair_rows_sum": sum(int(row.get("neighbor_pair_rows") or 0) for row in group),
                    "fallback_target_rows_sum": sum(int(row.get("same_source_fallback_target_rows") or 0) for row in group),
                    "same_source_requirement_rows_sum": sum(int(row.get("same_source_requirement_rows") or 0) for row in group),
                    "next_same_resource_action": group_next_action(family, group),
                }
            )
    return outputs


def group_next_action(family: str, group: list[dict[str, Any]]) -> str:
    buckets = Counter(str(row.get("combined_split_bucket")) for row in group)
    if family == "combined_split_bucket":
        bucket = next(iter(buckets))
        if bucket == "DIVERGENT_COMMAND_LADDER_SPLIT_REQUIRED":
            return "preserve as a separate divergence/avoid-filter candidate family"
        if bucket == "AGREEING_ROUTE_ALIGNED_IMBALANCE_WITH_NEIGHBOR_SUPPORT":
            return "deconcentrate by source-date and compare against exact missing-source expansion"
    if any("UNDERPOWERED" in bucket for bucket in buckets):
        return "seek additional same-source neighbor rows or mark underpowered before stronger interpretation"
    if any("WEAKEN" in bucket for bucket in buckets):
        return "carry as weakening split into future mutation ledger"
    return "preserve full bucket and use as descriptor/control context only"


def build_question_rows(rows: list[dict[str, Any]], bucket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for bucket, count in sorted(Counter(str(row.get("combined_split_bucket")) for row in rows).items()):
        bucket_subset = [row for row in rows if row.get("combined_split_bucket") == bucket]
        questions.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-Q-{len(questions) + 1:03d}",
                "question_family": "combined_split_bucket_followup",
                "bucket": bucket,
                "row_count": count,
                "request_ids": sorted(str(row.get("request_id")) for row in bucket_subset),
                "question": f"What source-safe interpretation or mutation follows for all {count} imbalanced rows in {bucket}?",
                "next_same_resource_action": group_next_action("combined_split_bucket", bucket_subset),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for row in rows:
        if row.get("neighbor_split_bucket") == "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_CONTEXT":
            questions.append(
                {
                    "question_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-Q-{len(questions) + 1:03d}",
                    "question_family": "row_level_neighbor_gap",
                    "bucket": "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_CONTEXT",
                    "row_count": 1,
                    "request_ids": [row.get("request_id")],
                    "question": "Can this imbalanced row get any same-source neighbor support from owned/current/free sources, or must it stay isolated?",
                    "next_same_resource_action": "search same-source expansion or keep as isolated/underpowered descriptor",
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    if any(row.get("same_source_fallback_target_rows") for row in rows):
        questions.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-IMBALANCED-AFTER-FALLBACK-Q-{len(questions) + 1:03d}",
                "question_family": "fallback_relation_to_imbalanced_descriptors",
                "bucket": "SAME_SOURCE_FALLBACK_CONTEXT_EXISTS",
                "row_count": sum(1 for row in rows if row.get("same_source_fallback_target_rows")),
                "request_ids": sorted(str(row.get("request_id")) for row in rows if row.get("same_source_fallback_target_rows")),
                "question": "Do same-source no-event fallback contexts weaken, support, or merely bound the imbalanced ladder descriptors?",
                "next_same_resource_action": "carry fallback-context buckets into mutation rows and exact source-date acquisition",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    if not bucket_rows:
        raise RuntimeError("bucket_rows unexpectedly empty")
    return questions


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_imbalanced_after_fallback_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_imbalanced_after_fallback_result", "created"),
        (ROW_LEDGER, "sierra_depth_ladder_imbalanced_after_fallback_row_ledger", "created"),
        (NEIGHBOR_CONTEXT_LEDGER, "sierra_depth_ladder_imbalanced_after_fallback_neighbor_ledger", "created"),
        (FALLBACK_CONTEXT_LEDGER, "sierra_depth_ladder_imbalanced_after_fallback_fallback_context_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_imbalanced_after_fallback_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_imbalanced_after_fallback_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_imbalanced_after_fallback_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], split_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_imbalanced_after_fallback_split",
        "status": "done",
        "route": "sierra_depth_ladder_imbalanced_after_fallback_split",
        "details": "Split all imbalanced ladder descriptor rows by command-ladder relation, Route C alignment, same-source neighbor context, no-event fallback relation, and requirement context.",
        "counts": counts,
        "combined_split_bucket_counts": split_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROW_LEDGER),
            relative(NEIGHBOR_CONTEXT_LEDGER),
            relative(FALLBACK_CONTEXT_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], split_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Imbalanced Split After Fallback",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: imbalanced ladder descriptor/control split only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Combined Split Buckets", ""])
    for key, value in sorted(split_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- All `9` imbalanced ladder rows are preserved in the row ledger.",
            "- All `103` existing imbalanced neighbor-context rows are preserved in the neighbor ledger.",
            "- Same-source no-event fallback context is joined only as descriptor/control context; it does not replace exact boundary60 ladder truth.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Search/acquire exact missing `.depth` source-date files where owned/current/free routes exist.",
            "- Repair or proxy earlier-book-history rows where same-source depth history can be recovered.",
            "- Feed split buckets into mutation rows without promoting any branch.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    imbalanced_rows = read_jsonl(IMBALANCED_LEDGER)
    imbalanced_neighbor_rows = read_jsonl(IMBALANCED_NEIGHBOR_LEDGER)
    original_bucket_rows = read_jsonl(IMBALANCED_BUCKET_LEDGER)
    route_c_rows = read_jsonl(ROUTE_C_JOIN_LEDGER)
    fallback_targets = read_jsonl(FALLBACK_TARGET_LEDGER)
    requirements = read_jsonl(REQUIREMENT_AFTER_FALLBACK_LEDGER)

    neighbor_by_anchor: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in imbalanced_neighbor_rows:
        neighbor_by_anchor[str(row.get("anchor_request_id"))].append(row)
    fallback_by_source: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in fallback_targets:
        fallback_by_source[source_key(row)].append(row)
    requirement_by_source: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in requirements:
        requirement_by_source[source_key(row)].append(row)
    route_c_by_request = {str(row.get("request_id")): row for row in route_c_rows}

    row_outputs, neighbor_outputs, fallback_outputs = build_rows(
        imbalanced_rows,
        neighbor_by_anchor,
        fallback_by_source,
        requirement_by_source,
        route_c_by_request,
    )
    bucket_outputs = group_rows(row_outputs)
    question_outputs = build_question_rows(row_outputs, bucket_outputs)
    split_counts = count_by(row_outputs, "combined_split_bucket")
    counts = {
        "input_imbalanced_rows": len(imbalanced_rows),
        "split_row_rows": len(row_outputs),
        "input_imbalanced_neighbor_context_rows": len(imbalanced_neighbor_rows),
        "split_neighbor_rows": len(neighbor_outputs),
        "input_imbalanced_bucket_rows": len(original_bucket_rows),
        "route_c_join_input_rows": len(route_c_rows),
        "fallback_target_input_rows": len(fallback_targets),
        "fallback_context_rows": len(fallback_outputs),
        "requirement_after_fallback_input_rows": len(requirements),
        "bucket_rows": len(bucket_outputs),
        "question_rows": len(question_outputs),
        "rows_with_same_source_fallback_targets": sum(1 for row in row_outputs if row.get("same_source_fallback_target_rows")),
        "rows_without_same_source_neighbor_context": sum(
            1 for row in row_outputs if row.get("neighbor_split_bucket") == "IMBALANCED_NO_SAME_SOURCE_NEIGHBOR_CONTEXT"
        ),
        "rows_with_command_ladder_divergence": sum(
            1 for row in row_outputs if row.get("command_ladder_sign_relation") == "COMMAND_AND_LADDER_SIGN_DIVERGE"
        ),
        "rows_with_route_alignment_unknown": sum(1 for row in row_outputs if row.get("route_c_delta_aligned_with_future") is None),
    }

    write_jsonl(ROW_LEDGER, row_outputs)
    write_jsonl(NEIGHBOR_CONTEXT_LEDGER, neighbor_outputs)
    write_jsonl(FALLBACK_CONTEXT_LEDGER, fallback_outputs)
    write_jsonl(BUCKET_LEDGER, bucket_outputs)
    write_jsonl(QUESTION_LEDGER, question_outputs)
    result = {
        "schema": "sierra_depth_ladder_imbalanced_after_fallback_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_IMBALANCED_DESCRIPTOR_SPLIT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "combined_split_bucket_counts": split_counts,
        "neighbor_split_bucket_counts": count_by(row_outputs, "neighbor_split_bucket"),
        "fallback_context_bucket_counts": count_by(row_outputs, "fallback_context_bucket"),
        "requirement_context_bucket_counts": count_by(row_outputs, "requirement_context_bucket"),
        "next_same_resource_work": [
            "search/acquire exact missing .depth source-date files where owned/current/free routes exist",
            "repair/proxy earlier-book-history rows where current source history allows",
            "carry imbalanced split buckets into mutation rows as descriptor-only control evidence",
        ],
        "not_completion": "This split answers one imbalanced-descriptor follow-up and does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, split_counts)
    write_summary(generated_utc, counts, split_counts)
    print(json.dumps({"ok": True, "counts": counts, "split_counts": split_counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
