"""Repair no-prior-clear Sierra ladder rows with in-window CLEAR_BOOK proof.

The prior ladder snapshot probe correctly refused to reconstruct a book from
an empty state when no CLEAR_BOOK existed before the feature window. Some of
those same rows contain a real CLEAR_BOOK inside the event window. This packet
uses only that source-safe subset: once an in-window CLEAR_BOOK is observed,
the book state is exact from that point forward. Boundary samples remain
blocked unless the clear occurs before the relevant boundary window starts.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from heapq import nlargest, nsmallest
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO))

from scripts import extract_sierra_depth_features as depth  # noqa: E402


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

COMMAND_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_FEATURE_LEDGER_{STAMP}.jsonl"
REQUIREMENT_AFTER_FALLBACK_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_RESULT_{STAMP}.json"
ROW_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_ROW_LEDGER_{STAMP}.jsonl"
FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_FEATURE_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_BLOCKER_LEDGER_{STAMP}.jsonl"
FILE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_FILE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth in-window CLEAR_BOOK repair for earlier-book-history rows; "
    "descriptor/source-control evidence only, with no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
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


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


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


def compact_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": row.get("request_id"),
        "request_family": row.get("request_family"),
        "replay_id": row.get("replay_id"),
        "route_c_queue_id": row.get("route_c_queue_id"),
        "route_c_symbol": row.get("route_c_symbol"),
        "route_c_primitive_flag": row.get("route_c_primitive_flag"),
        "sierra_primitive_flag": row.get("sierra_primitive_flag"),
        "horizon_id": row.get("horizon_id"),
        "source_symbol": row.get("source_symbol"),
        "source_proxy_family": row.get("source_proxy_family"),
        "proxy_relation": row.get("proxy_relation"),
        "source_date": row.get("source_date"),
        "bar_start_utc": row.get("bar_start_utc"),
        "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
        "window_start_utc": row.get("window_start_utc"),
        "event15_start_utc": row.get("event15_start_utc"),
        "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
        "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
        "route_c_future_abs_change": row.get("route_c_future_abs_change"),
        "sierra_future_follows_delta_sign": row.get("sierra_future_follows_delta_sign"),
        "sierra_future_follows_price_sign": row.get("sierra_future_follows_price_sign"),
        "sierra_future_change_per_current_range": row.get("sierra_future_change_per_current_range"),
        "sierra_abs_future_change": row.get("sierra_abs_future_change"),
        "command_feature_bucket": row.get("feature_bucket"),
        "command_event15_imbalance_sign": row.get("event15_imbalance_sign"),
        "command_event15_bid_quantity_share": row.get("event15_depth_bid_quantity_share"),
        "command_event15_bid_minus_ask_quantity_sum": row.get("event15_depth_bid_minus_ask_quantity_sum"),
    }


def requirement_context(row: dict[str, Any], requirements: dict[str, dict[str, Any]]) -> dict[str, Any]:
    requirement = requirements.get(str(row.get("request_id"))) or {}
    return {
        "requirement_id": requirement.get("requirement_id"),
        "requirement_type": requirement.get("requirement_type"),
        "requirement_status": requirement.get("requirement_status"),
        "post_fallback_requirement_status": requirement.get("post_fallback_requirement_status"),
        "post_fallback_update_scope": requirement.get("post_fallback_update_scope"),
        "requirement_recovery_bucket": requirement.get("recovery_bucket"),
        "requirement_post_fallback_action": requirement.get("post_fallback_next_same_resource_action"),
    }


def _top_qty(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(qty for _price, (qty, _orders) in levels[:n])


def _top_orders(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(orders for _price, (_qty, orders) in levels[:n])


def _max_wall(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return max((qty for _price, (qty, _orders) in levels[:n]), default=0)


def _imbalance(bid_qty: float, ask_qty: float) -> float | None:
    denom = bid_qty + ask_qty
    return None if denom <= 0 else (bid_qty - ask_qty) / denom


def fast_snapshot_features(
    bids: dict[float, tuple[int, int]],
    asks: dict[float, tuple[int, int]],
    *,
    timestamp_us: int,
    tick_size: float,
) -> dict[str, Any]:
    bid_levels = nlargest(20, bids.items(), key=lambda item: item[0])
    ask_levels = nsmallest(20, asks.items(), key=lambda item: item[0])
    best_bid = bid_levels[0][0] if bid_levels else None
    best_ask = ask_levels[0][0] if ask_levels else None
    out: dict[str, Any] = {
        "timestamp_utc": depth.iso_utc(depth.sierra_datetime(timestamp_us)),
        "timestamp_us": timestamp_us,
        "book_levels_bid": len(bids),
        "book_levels_ask": len(asks),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_px": None,
        "spread_ticks": None,
    }
    if best_bid is not None and best_ask is not None:
        out["mid_px"] = (best_bid + best_ask) / 2.0
        out["spread_ticks"] = (best_ask - best_bid) / tick_size
    for n in (1, 5, 10, 20):
        bid_qty = _top_qty(bid_levels, n)
        ask_qty = _top_qty(ask_levels, n)
        out[f"top_{n}_bid_qty"] = bid_qty
        out[f"top_{n}_ask_qty"] = ask_qty
        out[f"total_depth{n}"] = bid_qty + ask_qty
        out[f"depth{n}_imbalance"] = _imbalance(bid_qty, ask_qty)
    near10 = _top_qty(bid_levels, 3) + _top_qty(ask_levels, 3)
    far10 = out["total_depth10"] - near10
    out["near_far_ratio"] = None if far10 <= 0 else near10 / far10
    near20 = out["total_depth5"]
    far20 = out["total_depth20"] - out["total_depth5"]
    out["near_far_ratio20"] = None if far20 <= 0 else near20 / far20
    max_bid_wall10 = _max_wall(bid_levels, 10)
    max_ask_wall10 = _max_wall(ask_levels, 10)
    max_bid_wall20 = _max_wall(bid_levels, 20)
    max_ask_wall20 = _max_wall(ask_levels, 20)
    out["max_bid_wall10"] = max_bid_wall10
    out["max_ask_wall10"] = max_ask_wall10
    out["max_bid_wall20"] = max_bid_wall20
    out["max_ask_wall20"] = max_ask_wall20
    out["wall_concentration10"] = None if out["total_depth10"] <= 0 else max(max_bid_wall10, max_ask_wall10) / out["total_depth10"]
    out["wall_concentration20"] = None if out["total_depth20"] <= 0 else max(max_bid_wall20, max_ask_wall20) / out["total_depth20"]
    out["top_10_num_orders_bid"] = _top_orders(bid_levels, 10)
    out["top_10_num_orders_ask"] = _top_orders(ask_levels, 10)
    return out


def classify_exact_feature(feature: dict[str, Any]) -> str:
    if feature.get("event_boundary60_sample_count") == 0:
        return "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_NO_EVENT_SAMPLES"
    depth10 = safe_float(feature.get("event_boundary60_median_total_depth10"))
    imbalance = safe_float(feature.get("event_boundary60_median_depth10_imbalance"))
    if depth10 is None:
        return "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_MISSING"
    if imbalance is None:
        return "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_IMBALANCE_MISSING"
    if abs(imbalance) >= 0.20:
        return "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_IMBALANCED"
    return "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_BALANCED"


def build_event(row: dict[str, Any], requirements: dict[str, dict[str, Any]]) -> dict[str, Any]:
    pre_start = parse_dt(str(row["window_start_utc"]))
    event15_start = parse_dt(str(row["event15_start_utc"]))
    canonical = parse_dt(str(row["canonical_m15_close_utc"]))
    boundary_us = 60 * 1_000_000
    return {
        "row": row,
        "requirement": requirement_context(row, requirements),
        "pre_start_us": depth.sierra_us(pre_start),
        "event15_start_us": depth.sierra_us(event15_start),
        "canonical_us": depth.sierra_us(canonical),
        "pre_boundary_start_us": depth.sierra_us(event15_start) - boundary_us,
        "event_boundary_start_us": depth.sierra_us(canonical) - boundary_us,
        "replay_start_record_index": int(row.get("replay_start_record_index") or 0),
        "first_in_window_clear_us": None,
        "first_in_window_clear_record_index": None,
        "pre_boundary_exact_by_second": {},
        "event_boundary_exact_by_second": {},
        "pre_boundary_partial_by_second": {},
        "event_boundary_partial_by_second": {},
    }


def clear_timing_status(event: dict[str, Any]) -> str:
    first_clear_us = event.get("first_in_window_clear_us")
    if first_clear_us is None:
        return "NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
    if int(first_clear_us) <= event["pre_boundary_start_us"]:
        return "IN_WINDOW_CLEAR_BEFORE_PRE_BOUNDARY_START_FULL_PRE_AND_EVENT_EXACT"
    if int(first_clear_us) <= event["event_boundary_start_us"]:
        return "IN_WINDOW_CLEAR_BEFORE_EVENT_BOUNDARY_START_EVENT_ONLY_EXACT"
    if int(first_clear_us) < event["canonical_us"]:
        return "IN_WINDOW_CLEAR_AFTER_EVENT_BOUNDARY_START_PARTIAL_ONLY"
    return "NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"


def primary_status_for_event(event: dict[str, Any], feature_bucket: str | None) -> str:
    timing_status = clear_timing_status(event)
    if timing_status == "NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL":
        return "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
    if timing_status == "IN_WINDOW_CLEAR_AFTER_EVENT_BOUNDARY_START_PARTIAL_ONLY":
        return "BLOCKED_IN_WINDOW_CLEAR_TOO_LATE_FOR_EXACT_BOUNDARY60"
    if feature_bucket == "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_NO_EVENT_SAMPLES":
        return "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES"
    if feature_bucket in {
        "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_MISSING",
        "IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_IMBALANCE_MISSING",
    }:
        return "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_METRIC_MISSING"
    if timing_status == "IN_WINDOW_CLEAR_BEFORE_PRE_BOUNDARY_START_FULL_PRE_AND_EVENT_EXACT":
        return "REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60"
    return "REPAIRED_IN_WINDOW_CLEAR_EVENT_BOUNDARY60_ONLY_PRE_BOUNDARY_BLOCKED"


def build_feature(event: dict[str, Any], path: Path, *, feature_bucket: str | None = None) -> dict[str, Any]:
    row = event["row"]
    tick_size = float(row.get("tick_size") or 0.01)
    pre_exact = [
        event["pre_boundary_exact_by_second"][key]
        for key in sorted(event["pre_boundary_exact_by_second"])
    ]
    event_exact = [
        event["event_boundary_exact_by_second"][key]
        for key in sorted(event["event_boundary_exact_by_second"])
    ]
    pre_partial = [
        event["pre_boundary_partial_by_second"][key]
        for key in sorted(event["pre_boundary_partial_by_second"])
    ]
    event_partial = [
        event["event_boundary_partial_by_second"][key]
        for key in sorted(event["event_boundary_partial_by_second"])
    ]
    pre_threshold = depth.quantile([sample.get("total_depth10") for sample in pre_exact], 0.2)
    feature: dict[str, Any] = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        **compact_context(row),
        **event["requirement"],
        "depth_path": str(path),
        "tick_size": tick_size,
        "ladder_sample_method": "single_pass_end_of_batch_boundary60_in_window_clear_only",
        "ladder_replay_start_record_index": event["replay_start_record_index"],
        "first_in_window_clear_utc": depth.iso_utc(depth.sierra_datetime(event["first_in_window_clear_us"]))
        if event.get("first_in_window_clear_us") is not None
        else None,
        "first_in_window_clear_us": event.get("first_in_window_clear_us"),
        "first_in_window_clear_record_index": event.get("first_in_window_clear_record_index"),
        "clear_timing_status": clear_timing_status(event),
        "pre_boundary60_exact_clear_required_before_us": event["pre_boundary_start_us"],
        "event_boundary60_exact_clear_required_before_us": event["event_boundary_start_us"],
        "pre_boundary60_partial_post_clear_sample_count": len(pre_partial),
        "event_boundary60_partial_post_clear_sample_count": len(event_partial),
        "pre_boundary60_thin_depth10_threshold": pre_threshold,
        "full_per_second_median_attempt_status": "NOT_REUSED_IN_WINDOW_CLEAR_REPAIR_SINGLE_PASS_BOUNDARY_ONLY",
    }
    feature.update(depth.summarize_samples(pre_exact, "pre_boundary60", tick_size=tick_size))
    feature.update(
        depth.summarize_samples(
            event_exact,
            "event_boundary60",
            tick_size=tick_size,
            thin_threshold=pre_threshold,
        )
    )
    feature["in_window_clear_feature_bucket"] = feature_bucket or classify_exact_feature(feature)
    feature["primary_repair_status"] = primary_status_for_event(event, feature["in_window_clear_feature_bucket"])
    return feature


def blocker_from_feature(feature: dict[str, Any], next_action: str) -> dict[str, Any]:
    blocker = dict(feature)
    blocker.update(
        {
            "blocker_type": feature["primary_repair_status"],
            "next_same_resource_action": next_action,
        }
    )
    return blocker


def blocker_from_event(event: dict[str, Any], path: Path, blocker_type: str, next_action: str) -> dict[str, Any]:
    row = event["row"]
    return {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        **compact_context(row),
        **event["requirement"],
        "depth_path": str(path),
        "tick_size": float(row.get("tick_size") or 0.01),
        "ladder_sample_method": "single_pass_end_of_batch_boundary60_in_window_clear_only",
        "ladder_replay_start_record_index": event["replay_start_record_index"],
        "first_in_window_clear_utc": depth.iso_utc(depth.sierra_datetime(event["first_in_window_clear_us"]))
        if event.get("first_in_window_clear_us") is not None
        else None,
        "first_in_window_clear_us": event.get("first_in_window_clear_us"),
        "first_in_window_clear_record_index": event.get("first_in_window_clear_record_index"),
        "clear_timing_status": clear_timing_status(event),
        "pre_boundary60_partial_post_clear_sample_count": len(event["pre_boundary_partial_by_second"]),
        "event_boundary60_partial_post_clear_sample_count": len(event["event_boundary_partial_by_second"]),
        "primary_repair_status": blocker_type,
        "blocker_type": blocker_type,
        "next_same_resource_action": next_action,
    }


def process_file(
    path: Path,
    rows: list[dict[str, Any]],
    requirements: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    header = depth.read_header(path)
    events = [build_event(row, requirements) for row in rows]
    events.sort(key=lambda item: (item["pre_start_us"], item["canonical_us"], str(item["row"].get("request_id"))))
    start_record = min(event["replay_start_record_index"] for event in events)
    max_canonical = max(event["canonical_us"] for event in events)
    add_index = 0
    active: list[dict[str, Any]] = []
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    command_counts: Counter[str] = Counter()
    records_processed = 0
    batches_seen = 0
    exact_sampled_batches = 0
    partial_sampled_batches = 0
    clear_records_seen = 0
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    last_clear_us: int | None = None
    last_clear_record_index: int | None = None
    for record_index, record in enumerate(
        depth.iter_records(path, header, start_record=start_record),
        start=start_record,
    ):
        dt_us, command, flags, num_orders, price, quantity = record
        if dt_us >= max_canonical:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_counts[depth.COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in depth.COMMANDS:
            continue
        depth.apply_book_record(command, price, quantity, num_orders, bids, asks)
        if command == 1:
            last_clear_us = dt_us
            last_clear_record_index = record_index
            clear_records_seen += 1
        while add_index < len(events) and events[add_index]["pre_start_us"] <= dt_us:
            event = events[add_index]
            if last_clear_us is not None and last_clear_us >= event["pre_start_us"]:
                event["first_in_window_clear_us"] = last_clear_us
                event["first_in_window_clear_record_index"] = last_clear_record_index
            active.append(event)
            add_index += 1
        if command == 1:
            for event in active:
                if (
                    event["first_in_window_clear_us"] is None
                    and event["pre_start_us"] <= dt_us < event["canonical_us"]
                ):
                    event["first_in_window_clear_us"] = dt_us
                    event["first_in_window_clear_record_index"] = record_index
        if active:
            active = [event for event in active if dt_us < event["canonical_us"]]
        if not active or not (flags & depth.END_OF_BATCH):
            continue
        sample_targets = [
            event for event in active
            if (
                event["pre_boundary_start_us"] <= dt_us < event["event15_start_us"]
                or event["event_boundary_start_us"] <= dt_us < event["canonical_us"]
            )
        ]
        if not sample_targets:
            continue
        batches_seen += 1
        sample = fast_snapshot_features(
            bids,
            asks,
            timestamp_us=dt_us,
            tick_size=float(sample_targets[0]["row"].get("tick_size") or 0.01),
        )
        second = dt_us // 1_000_000
        batch_exact = False
        batch_partial = False
        for event in sample_targets:
            first_clear_us = event.get("first_in_window_clear_us")
            if first_clear_us is None:
                continue
            if event["pre_boundary_start_us"] <= dt_us < event["event15_start_us"]:
                if int(first_clear_us) <= event["pre_boundary_start_us"]:
                    event["pre_boundary_exact_by_second"][second] = sample
                    batch_exact = True
                else:
                    event["pre_boundary_partial_by_second"][second] = sample
                    batch_partial = True
            if event["event_boundary_start_us"] <= dt_us < event["canonical_us"]:
                if int(first_clear_us) <= event["event_boundary_start_us"]:
                    event["event_boundary_exact_by_second"][second] = sample
                    batch_exact = True
                else:
                    event["event_boundary_partial_by_second"][second] = sample
                    batch_partial = True
        if batch_exact:
            exact_sampled_batches += 1
        if batch_partial:
            partial_sampled_batches += 1

    row_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for event in events:
        timing_status = clear_timing_status(event)
        feature_bucket: str | None = None
        feature: dict[str, Any] | None = None
        if timing_status in {
            "IN_WINDOW_CLEAR_BEFORE_PRE_BOUNDARY_START_FULL_PRE_AND_EVENT_EXACT",
            "IN_WINDOW_CLEAR_BEFORE_EVENT_BOUNDARY_START_EVENT_ONLY_EXACT",
        }:
            feature = build_feature(event, path)
            feature_bucket = str(feature["in_window_clear_feature_bucket"])
            feature_rows.append(feature)
        primary_status = primary_status_for_event(event, feature_bucket)
        if feature is None:
            row = blocker_from_event(
                event,
                path,
                primary_status,
                next_action_for_status(primary_status),
            )
        else:
            row = dict(feature)
            row["next_same_resource_action"] = next_action_for_status(primary_status)
        row_rows.append(row)
        if primary_status.startswith("BLOCKED_"):
            if feature is None:
                blocker_rows.append(dict(row))
            else:
                blocker_rows.append(blocker_from_feature(feature, next_action_for_status(primary_status)))
    status_counts = Counter(str(row.get("primary_repair_status")) for row in row_rows)
    file_row = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "depth_path": str(path),
        "source_symbol": rows[0].get("source_symbol"),
        "source_date": rows[0].get("source_date"),
        "input_no_prior_clear_rows": len(rows),
        "row_rows": len(row_rows),
        "feature_rows": len(feature_rows),
        "blocker_rows": len(blocker_rows),
        "primary_status_counts": dict(sorted(status_counts.items())),
        "start_record": start_record,
        "records_processed_until_max_canonical": records_processed,
        "clear_records_seen_after_group_start": clear_records_seen,
        "batches_seen_with_boundary60_targets": batches_seen,
        "exact_sampled_batches_with_boundary60_targets": exact_sampled_batches,
        "partial_sampled_batches_with_boundary60_targets": partial_sampled_batches,
        "command_counts_processed": dict(sorted(command_counts.items())),
        "first_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
        "last_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
        "header_record_count": header.record_count,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "file_size_bytes": header.size_bytes,
    }
    return row_rows, feature_rows, blocker_rows, file_row


def next_action_for_status(status: str) -> str:
    if status == "REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60":
        return "join repaired full pre/event boundary ladder rows back to Route C controls and mutation rows"
    if status == "REPAIRED_IN_WINDOW_CLEAR_EVENT_BOUNDARY60_ONLY_PRE_BOUNDARY_BLOCKED":
        return "use event-boundary descriptor only and keep pre-boundary context blocked unless earlier source history is recovered"
    if status == "BLOCKED_IN_WINDOW_CLEAR_TOO_LATE_FOR_EXACT_BOUNDARY60":
        return "preserve partial post-clear sample counts only; do not interpret boundary60 ladder without earlier clear or earlier source history"
    if status == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL":
        return "recover earlier depth history or file-start book state; otherwise keep conservative no-ladder classification"
    if status == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES":
        return "inspect Sierra batch timestamps and event boundary alignment before using the descriptor"
    if status == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_METRIC_MISSING":
        return "inspect reconstructed top-of-book depth state and source recording quality before using the descriptor"
    return "manual in-window CLEAR_BOOK repair review required"


def build_bucket_rows(row_rows: list[dict[str, Any]], feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("primary_repair_status", ["primary_repair_status"]),
        ("clear_timing_status", ["clear_timing_status"]),
        ("feature_bucket", ["in_window_clear_feature_bucket"]),
        ("status_by_source_symbol", ["source_symbol", "primary_repair_status"]),
        ("status_by_route_queue", ["route_c_queue_id", "primary_repair_status"]),
        ("status_by_horizon", ["horizon_id", "primary_repair_status"]),
        ("feature_bucket_by_command_bucket", ["command_feature_bucket", "in_window_clear_feature_bucket"]),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys in families:
        source_rows = feature_rows if family.startswith("feature_bucket") else row_rows
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-DEPTH-LADDER-IN-WINDOW-CLEAR-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "group_family": family,
                    "group_keys": keys,
                    "group_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "request_ids": sorted(str(row.get("request_id")) for row in group),
                    "source_symbol_counts": dict(sorted(Counter(str(row.get("source_symbol")) for row in group).items())),
                    "route_queue_counts": dict(sorted(Counter(str(row.get("route_c_queue_id")) for row in group).items())),
                    "next_same_resource_action": next_action_for_group(group),
                }
            )
    return outputs


def next_action_for_group(group: list[dict[str, Any]]) -> str:
    statuses = Counter(str(row.get("primary_repair_status")) for row in group)
    if any(status.startswith("REPAIRED_") for status in statuses):
        return "consume repaired rows in the next source-control/mutation update while preserving no-promotion boundary"
    if "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL" in statuses:
        return "continue exact earlier depth source acquisition or keep source/capture requirement"
    if "BLOCKED_IN_WINDOW_CLEAR_TOO_LATE_FOR_EXACT_BOUNDARY60" in statuses:
        return "preserve partial samples as non-boundary evidence only and seek earlier clear/source history"
    return "inspect blocker family before any descriptor interpretation"


def build_question_rows(
    row_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for status, count in sorted(Counter(str(row.get("primary_repair_status")) for row in row_rows).items()):
        group = [row for row in row_rows if row.get("primary_repair_status") == status]
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-IN-WINDOW-CLEAR-Q-{len(rows) + 1:03d}",
                "question_family": "primary_repair_status",
                "bucket": status,
                "row_count": count,
                "request_ids": sorted(str(row.get("request_id")) for row in group),
                "question": f"What same-resource source-control or mutation action follows for all {count} rows in {status}?",
                "next_same_resource_action": next_action_for_status(status),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for feature_bucket, count in sorted(Counter(str(row.get("in_window_clear_feature_bucket")) for row in feature_rows).items()):
        group = [row for row in feature_rows if row.get("in_window_clear_feature_bucket") == feature_bucket]
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-IN-WINDOW-CLEAR-Q-{len(rows) + 1:03d}",
                "question_family": "repaired_feature_bucket",
                "bucket": feature_bucket,
                "row_count": count,
                "request_ids": sorted(str(row.get("request_id")) for row in group),
                "question": f"How do all {count} repaired in-window-clear feature rows in {feature_bucket} alter Route C control interpretation?",
                "next_same_resource_action": "join repaired feature buckets to Route C controls, neighbor rows, and mutation rows without promotion language",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    rows.append(
        {
            "question_id": f"SIERRA-DEPTH-LADDER-IN-WINDOW-CLEAR-Q-{len(rows) + 1:03d}",
            "question_family": "remaining_blockers",
            "bucket": "ALL_REMAINING_BLOCKERS",
            "row_count": len(blocker_rows),
            "question": "Which remaining earlier-book-history rows are exact source-acquisition gaps after in-window CLEAR_BOOK repair?",
            "next_same_resource_action": "split remaining blockers into no-clear, too-late-clear, no-sample, and metric-missing requirements",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_in_window_clear_repair_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_in_window_clear_repair_result", "created"),
        (ROW_LEDGER, "sierra_depth_ladder_in_window_clear_repair_row_ledger", "created"),
        (FEATURE_LEDGER, "sierra_depth_ladder_in_window_clear_repair_feature_ledger", "created"),
        (BLOCKER_LEDGER, "sierra_depth_ladder_in_window_clear_repair_blocker_ledger", "created"),
        (FILE_LEDGER, "sierra_depth_ladder_in_window_clear_repair_file_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_in_window_clear_repair_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_in_window_clear_repair_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_in_window_clear_repair_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_in_window_clear_repair",
        "status": "done",
        "route": "sierra_depth_ladder_in_window_clear_repair",
        "details": "Replayed all no-prior-clear local depth rows and computed exact boundary descriptors only after an in-window CLEAR_BOOK occurred before the relevant boundary window.",
        "counts": counts,
        "primary_repair_status_counts": status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROW_LEDGER),
            relative(FEATURE_LEDGER),
            relative(BLOCKER_LEDGER),
            relative(FILE_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int], feature_bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder In-Window CLEAR_BOOK Repair",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: same-source Sierra `.depth` source-control repair only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Primary Repair Status", ""])
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Feature Buckets", ""])
    for key, value in sorted(feature_bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The input denominator is every `393` no-prior-clear local Sierra depth row from the prior ladder probe.",
            "- A row is repaired only when a real in-window `CLEAR_BOOK` occurs before the event boundary window required for exact reconstruction.",
            "- Rows with late clears keep partial post-clear sample counts as source diagnostics only; they are not boundary60 ladder features.",
            "- Rows with no in-window clear remain exact earlier-source-history/file-start-state requirements.",
            "- This packet is descriptor/source-control intelligence only and does not alter live behavior.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Join repaired in-window-clear rows into the ladder Route C denominator and mutation-design ledgers.",
            "- Split remaining earlier-book blockers by no-clear, late-clear, no-sample, and metric-missing families.",
            "- Continue exact missing `.depth` source-date acquisition from owned/free/current roots.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    command_rows = read_jsonl(COMMAND_FEATURE_LEDGER)
    requirements = {
        str(row.get("request_id")): row
        for row in read_jsonl(REQUIREMENT_AFTER_FALLBACK_LEDGER)
        if row.get("requirement_type") == "EARLIER_BOOK_HISTORY_OR_INITIAL_STATE_REQUIREMENT"
    }
    no_prior_rows = [
        row for row in command_rows
        if row.get("clear_book_seen_at_or_before_window_start") is not True
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in no_prior_rows:
        grouped[str(row["depth_path"])].append(row)

    row_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    for path_str, group in sorted(grouped.items()):
        path = Path(path_str)
        try:
            rows, features, blockers, file_row = process_file(path, group, requirements)
        except Exception as exc:  # noqa: BLE001 - preserve exact local parser/replay failure.
            error_rows: list[dict[str, Any]] = []
            for row in group:
                event = build_event(row, requirements)
                blocker = blocker_from_event(
                    event,
                    path,
                    "BLOCKED_IN_WINDOW_CLEAR_REPLAY_ERROR",
                    "inspect parser/file window and rerun after fixing in-window clear replay error",
                )
                blocker["error"] = f"{type(exc).__name__}: {exc}"
                error_rows.append(blocker)
            row_rows.extend(error_rows)
            blocker_rows.extend(error_rows)
            file_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "depth_path": path_str,
                    "input_no_prior_clear_rows": len(group),
                    "row_rows": len(error_rows),
                    "feature_rows": 0,
                    "blocker_rows": len(error_rows),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        row_rows.extend(rows)
        feature_rows.extend(features)
        blocker_rows.extend(blockers)
        file_rows.append(file_row)

    status_counts = dict(sorted(Counter(str(row.get("primary_repair_status")) for row in row_rows).items()))
    timing_counts = dict(sorted(Counter(str(row.get("clear_timing_status")) for row in row_rows).items()))
    feature_bucket_counts = dict(sorted(Counter(str(row.get("in_window_clear_feature_bucket")) for row in feature_rows).items()))
    bucket_rows = build_bucket_rows(row_rows, feature_rows)
    question_rows = build_question_rows(row_rows, feature_rows, blocker_rows)
    counts = {
        "input_no_prior_clear_rows": len(no_prior_rows),
        "requirement_earlier_book_rows": len(requirements),
        "row_rows": len(row_rows),
        "feature_rows": len(feature_rows),
        "blocker_rows": len(blocker_rows),
        "file_rows": len(file_rows),
        "rows_with_in_window_clear_before_canonical": sum(
            1 for row in row_rows if row.get("clear_timing_status") != "NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL"
        ),
        "repaired_full_pre_and_event_rows": status_counts.get("REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60", 0),
        "repaired_event_only_rows": status_counts.get("REPAIRED_IN_WINDOW_CLEAR_EVENT_BOUNDARY60_ONLY_PRE_BOUNDARY_BLOCKED", 0),
        "remaining_blocker_primary_rows": sum(count for status, count in status_counts.items() if status.startswith("BLOCKED_")),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    write_jsonl(ROW_LEDGER, row_rows)
    write_jsonl(FEATURE_LEDGER, feature_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(FILE_LEDGER, file_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_in_window_clear_repair_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_IN_WINDOW_CLEAR_BOOK_REPAIR_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "primary_repair_status_counts": status_counts,
        "clear_timing_status_counts": timing_counts,
        "feature_bucket_counts": feature_bucket_counts,
        "next_same_resource_work": [
            "join repaired in-window-clear rows into ladder Route C and mutation design packets",
            "split remaining earlier-book blockers by no-clear, late-clear, no-sample, and metric-missing families",
            "continue exact missing .depth source-date acquisition from owned/free/current routes",
        ],
        "not_completion": "This repair packet clears a subset of earlier-book-history rows but does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts, feature_bucket_counts)
    print(
        json.dumps(
            {
                "ok": True,
                "counts": counts,
                "primary_repair_status_counts": status_counts,
                "result": str(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
