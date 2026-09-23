#!/usr/bin/env python3
"""Repair Sierra ladder no-event-sample rows with record-level snapshots.

The boundary60 ladder probe sampled only END_OF_BATCH records. Some local
Sierra .depth windows have command-flow activity inside the M15 bar but no
END_OF_BATCH snapshot in the final minute before close, so the previous packet
correctly emitted ``LADDER_BOUNDARY60_NO_EVENT_SAMPLES``. This fallback replays
the same local files from the prior CLEAR_BOOK, samples every recognized command
record in the pre/event boundary windows, and also builds a full-M15 event-window
proxy when boundary60 is truly empty. It is descriptor/control evidence only.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
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

JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_RESULT_{STAMP}.json"
FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_FEATURE_LEDGER_{STAMP}.jsonl"
SAMPLE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_SAMPLE_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_BLOCKER_LEDGER_{STAMP}.jsonl"
FILE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_FILE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth record-level fallback for rows where END_OF_BATCH boundary60 "
    "sampling produced no event samples; no strategy validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, or promotion"
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


def sign_label(value: Any) -> str:
    clean = safe_float(value)
    if clean is None:
        return "unknown"
    if clean > 0:
        return "positive"
    if clean < 0:
        return "negative"
    return "zero"


def compact_context(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": row.get("request_id"),
        "request_family": row.get("request_family"),
        "replay_id": row.get("replay_id"),
        "route_c_queue_id": row.get("route_c_queue_id"),
        "route_c_symbol": row.get("route_c_symbol"),
        "route_c_primitive_flag": row.get("route_c_primitive_flag"),
        "route_c_mechanism_family": row.get("route_c_mechanism_family"),
        "route_c_full_control_bucket": row.get("route_c_full_control_bucket"),
        "route_c_residual_transfer_class": row.get("route_c_residual_transfer_class"),
        "sierra_primitive_flag": row.get("sierra_primitive_flag"),
        "horizon_id": row.get("horizon_id"),
        "source_symbol": row.get("source_symbol"),
        "source_proxy_family": row.get("source_proxy_family"),
        "proxy_relation": row.get("proxy_relation"),
        "source_date": row.get("source_date"),
        "bar_start_utc": row.get("bar_start_utc"),
        "canonical_m15_close_utc": row.get("canonical_m15_close_utc"),
        "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
        "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
        "route_c_future_abs_change": row.get("route_c_future_abs_change"),
        "sierra_future_follows_delta_sign": row.get("sierra_future_follows_delta_sign"),
        "sierra_future_follows_price_sign": row.get("sierra_future_follows_price_sign"),
        "sierra_future_change_per_current_range": row.get("sierra_future_change_per_current_range"),
        "sierra_abs_future_change": row.get("sierra_abs_future_change"),
        "command_feature_bucket": row.get("command_feature_bucket") or row.get("feature_bucket"),
        "command_event15_imbalance_sign": row.get("command_event15_imbalance_sign") or row.get("event15_imbalance_sign"),
        "command_event15_bid_quantity_share": row.get("event15_depth_bid_quantity_share"),
        "command_event15_bid_minus_ask_quantity_sum": row.get("event15_depth_bid_minus_ask_quantity_sum"),
        "command_event15_record_count": row.get("event15_depth_command_record_count"),
        "previous_ladder_snapshot_bucket": row.get("ladder_snapshot_bucket"),
        "previous_ladder_blocker_type": row.get("ladder_blocker_type"),
        "previous_ladder_sample_method": row.get("ladder_sample_method"),
        "previous_ladder_pre_boundary60_sample_count": row.get("ladder_pre_boundary60_sample_count"),
        "previous_ladder_pre_boundary60_median_total_depth10": row.get("ladder_pre_boundary60_median_total_depth10"),
        "previous_ladder_pre_boundary60_median_depth10_imbalance": row.get("ladder_pre_boundary60_median_depth10_imbalance"),
        "previous_ladder_event_boundary60_sample_count": row.get("ladder_event_boundary60_sample_count"),
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


def classify_fallback_feature(feature: dict[str, Any]) -> str:
    if feature.get("fallback_event_boundary60_record_sample_count") == 0:
        return "FALLBACK_RECORD_LEVEL_NO_EVENT_SAMPLES"
    depth10 = safe_float(feature.get("fallback_event_boundary60_record_median_total_depth10"))
    imbalance = safe_float(feature.get("fallback_event_boundary60_record_median_depth10_imbalance"))
    if depth10 is None:
        return "FALLBACK_RECORD_LEVEL_DEPTH10_MISSING"
    if imbalance is None:
        return "FALLBACK_RECORD_LEVEL_IMBALANCE_MISSING"
    if abs(imbalance) >= 0.20:
        return "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_IMBALANCED"
    return "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_BALANCED"


def classify_event15_proxy(feature: dict[str, Any]) -> str:
    if feature.get("fallback_event15_record_sample_count") == 0:
        return "FALLBACK_RECORD_LEVEL_EVENT15_NO_SAMPLES"
    depth10 = safe_float(feature.get("fallback_event15_record_median_total_depth10"))
    imbalance = safe_float(feature.get("fallback_event15_record_median_depth10_imbalance"))
    if depth10 is None:
        return "FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_MISSING"
    if imbalance is None:
        return "FALLBACK_RECORD_LEVEL_EVENT15_IMBALANCE_MISSING"
    if abs(imbalance) >= 0.20:
        return "FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_IMBALANCED_PROXY"
    return "FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_BALANCED_PROXY"


def route_relation(row: dict[str, Any], fallback_sign: str) -> str:
    command_sign = str(row.get("command_event15_imbalance_sign") or "unknown")
    aligned = row.get("route_c_delta_aligned_with_future")
    if fallback_sign == "unknown" or command_sign == "unknown":
        return "COMMAND_OR_FALLBACK_SIGN_UNKNOWN"
    if fallback_sign == command_sign and aligned is True:
        return "COMMAND_FALLBACK_AGREE_AND_ROUTE_ALIGNED_DESCRIPTOR"
    if fallback_sign == command_sign and aligned is False:
        return "COMMAND_FALLBACK_AGREE_BUT_ROUTE_NOT_ALIGNED_WEAKENING_DESCRIPTOR"
    if fallback_sign != command_sign and aligned is True:
        return "COMMAND_FALLBACK_DIVERGE_BUT_ROUTE_ALIGNED_SPLIT_REQUIRED"
    if fallback_sign != command_sign and aligned is False:
        return "COMMAND_FALLBACK_DIVERGE_AND_ROUTE_NOT_ALIGNED_WEAKENING_DESCRIPTOR"
    return "COMMAND_FALLBACK_ROUTE_ALIGNMENT_MIXED_OR_UNAVAILABLE"


def build_event(row: dict[str, Any]) -> dict[str, Any]:
    canonical = parse_dt(str(row["canonical_m15_close_utc"]))
    bar_start = parse_dt(str(row["bar_start_utc"]))
    boundary = timedelta(seconds=60)
    return {
        "row": row,
        "pre_boundary_start_us": depth.sierra_us(bar_start - boundary),
        "event15_start_us": depth.sierra_us(bar_start),
        "event_boundary_start_us": depth.sierra_us(canonical - boundary),
        "canonical_us": depth.sierra_us(canonical),
        "replay_start_record_index": int(row.get("ladder_replay_start_record_index") or 0),
        "pre_boundary_samples": [],
        "event_boundary_samples": [],
        "event15_samples": [],
        "pre_boundary_record_count": 0,
        "event_boundary_record_count": 0,
        "event15_record_count": 0,
    }


def sample_row(
    *,
    event: dict[str, Any],
    boundary_type: str,
    sample: dict[str, Any],
    command: int,
    flags: int,
    num_orders: int,
    price: float,
    quantity: int,
    ordinal: int,
) -> dict[str, Any]:
    row = event["row"]
    return {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "request_id": row.get("request_id"),
        "route_c_queue_id": row.get("route_c_queue_id"),
        "route_c_symbol": row.get("route_c_symbol"),
        "route_c_primitive_flag": row.get("route_c_primitive_flag"),
        "source_symbol": row.get("source_symbol"),
        "source_date": row.get("source_date"),
        "depth_path": row.get("depth_path"),
        "boundary_type": boundary_type,
        "sample_ordinal": ordinal,
        "timestamp_utc": sample.get("timestamp_utc"),
        "timestamp_us": sample.get("timestamp_us"),
        "command": depth.COMMANDS.get(command, f"UNKNOWN_{command}"),
        "flags": flags,
        "end_of_batch_flag": bool(flags & depth.END_OF_BATCH),
        "num_orders": num_orders,
        "record_price": price,
        "record_quantity": quantity,
        "book_levels_bid": sample.get("book_levels_bid"),
        "book_levels_ask": sample.get("book_levels_ask"),
        "best_bid": sample.get("best_bid"),
        "best_ask": sample.get("best_ask"),
        "spread_ticks": sample.get("spread_ticks"),
        "total_depth10": sample.get("total_depth10"),
        "total_depth20": sample.get("total_depth20"),
        "depth10_imbalance": sample.get("depth10_imbalance"),
        "depth20_imbalance": sample.get("depth20_imbalance"),
        "wall_concentration10": sample.get("wall_concentration10"),
        "max_bid_wall10": sample.get("max_bid_wall10"),
        "max_ask_wall10": sample.get("max_ask_wall10"),
    }


def process_file(path: Path, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    header = depth.read_header(path)
    events = [build_event(row) for row in rows]
    events.sort(key=lambda item: (item["pre_boundary_start_us"], item["canonical_us"], str(item["row"].get("request_id"))))
    start_record = min(event["replay_start_record_index"] for event in events)
    max_canonical = max(event["canonical_us"] for event in events)
    add_index = 0
    active: list[dict[str, Any]] = []
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    command_counts: Counter[str] = Counter()
    records_processed = 0
    unknown_commands: Counter[int] = Counter()
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    sample_rows: list[dict[str, Any]] = []
    for dt_us, command, flags, num_orders, price, quantity in depth.iter_records(path, header, start_record=start_record):
        if dt_us >= max_canonical:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_counts[depth.COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in depth.COMMANDS:
            unknown_commands[command] += 1
            continue
        depth.apply_book_record(command, price, quantity, num_orders, bids, asks)
        while add_index < len(events) and events[add_index]["pre_boundary_start_us"] <= dt_us:
            active.append(events[add_index])
            add_index += 1
        if active:
            active = [event for event in active if dt_us < event["canonical_us"]]
        if not active:
            continue
        for event in active:
            in_pre = event["pre_boundary_start_us"] <= dt_us < event["event15_start_us"]
            in_event15 = event["event15_start_us"] <= dt_us < event["canonical_us"]
            in_event = event["event_boundary_start_us"] <= dt_us < event["canonical_us"]
            if not in_pre and not in_event15:
                continue
            tick_size = float(event["row"].get("tick_size") or 0.01)
            sample = fast_snapshot_features(bids, asks, timestamp_us=dt_us, tick_size=tick_size)
            if in_pre:
                event["pre_boundary_record_count"] += 1
                event["pre_boundary_samples"].append(sample)
                sample_rows.append(
                    sample_row(
                        event=event,
                        boundary_type="pre_boundary60_record",
                        sample=sample,
                        command=command,
                        flags=flags,
                        num_orders=num_orders,
                        price=price,
                        quantity=quantity,
                        ordinal=event["pre_boundary_record_count"],
                    )
                )
            if in_event15:
                event["event15_record_count"] += 1
                event["event15_samples"].append(sample)
                sample_rows.append(
                    sample_row(
                        event=event,
                        boundary_type="event15_record",
                        sample=sample,
                        command=command,
                        flags=flags,
                        num_orders=num_orders,
                        price=price,
                        quantity=quantity,
                        ordinal=event["event15_record_count"],
                    )
                )
            if in_event:
                event["event_boundary_record_count"] += 1
                event["event_boundary_samples"].append(sample)
                sample_rows.append(
                    sample_row(
                        event=event,
                        boundary_type="event_boundary60_record",
                        sample=sample,
                        command=command,
                        flags=flags,
                        num_orders=num_orders,
                        price=price,
                        quantity=quantity,
                        ordinal=event["event_boundary_record_count"],
                    )
                )

    feature_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    for event in events:
        row = event["row"]
        tick_size = float(row.get("tick_size") or 0.01)
        pre_threshold = depth.quantile([sample.get("total_depth10") for sample in event["pre_boundary_samples"]], 0.2)
        feature: dict[str, Any] = {
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            **compact_context(row),
            "depth_path": str(path),
            "tick_size": tick_size,
            "fallback_sample_method": "record_level_snapshot_after_each_recognized_command_boundary60_prior_clear_only",
            "fallback_replay_start_record_index": event["replay_start_record_index"],
            "fallback_replay_status": "FALLBACK_RECORD_LEVEL_PRIOR_CLEAR_COMPUTED",
            "fallback_pre_boundary60_record_count": event["pre_boundary_record_count"],
            "fallback_event_boundary60_record_count": event["event_boundary_record_count"],
            "fallback_event15_record_count": event["event15_record_count"],
            "fallback_pre_boundary60_record_thin_depth10_threshold": pre_threshold,
            "prior_end_of_batch_event_sample_count": row.get("ladder_event_boundary60_sample_count"),
            "no_event_sample_repair_boundary": "boundary60 remains exact; full event15 record-level proxy is included only when final-minute depth is empty",
        }
        feature.update(
            depth.summarize_samples(
                event["pre_boundary_samples"],
                "fallback_pre_boundary60_record",
                tick_size=tick_size,
            )
        )
        feature.update(
            depth.summarize_samples(
                event["event_boundary_samples"],
                "fallback_event_boundary60_record",
                tick_size=tick_size,
                thin_threshold=pre_threshold,
            )
        )
        feature.update(
            depth.summarize_samples(
                event["event15_samples"],
                "fallback_event15_record",
                tick_size=tick_size,
                thin_threshold=pre_threshold,
            )
        )
        feature["fallback_ladder_snapshot_bucket"] = classify_fallback_feature(feature)
        feature["fallback_event15_proxy_bucket"] = classify_event15_proxy(feature)
        feature["fallback_event_boundary60_imbalance_sign"] = sign_label(
            feature.get("fallback_event_boundary60_record_median_depth10_imbalance")
        )
        feature["fallback_event15_imbalance_sign"] = sign_label(
            feature.get("fallback_event15_record_median_depth10_imbalance")
        )
        feature["command_fallback_route_relation_bucket"] = route_relation(
            feature,
            str(feature["fallback_event15_imbalance_sign"]),
        )
        feature_rows.append(feature)
        if feature["fallback_ladder_snapshot_bucket"] in {
            "FALLBACK_RECORD_LEVEL_NO_EVENT_SAMPLES",
            "FALLBACK_RECORD_LEVEL_DEPTH10_MISSING",
            "FALLBACK_RECORD_LEVEL_IMBALANCE_MISSING",
        }:
            blocker = dict(feature)
            blocker.update(
                {
                    "blocker_type": feature["fallback_ladder_snapshot_bucket"],
                    "next_same_resource_action": "use full-event15 proxy if available; otherwise inspect raw record timestamps and preserve fail-closed event-window ladder descriptor",
                }
            )
            blocker_rows.append(blocker)
    file_row = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "depth_path": str(path),
        "source_symbol": rows[0].get("source_symbol"),
        "source_date": rows[0].get("source_date"),
        "input_no_event_rows": len(rows),
        "feature_rows": len(feature_rows),
        "blocker_rows": len(blocker_rows),
        "sample_rows": len(sample_rows),
        "start_record": start_record,
        "records_processed_until_max_canonical": records_processed,
        "command_counts_processed": dict(sorted(command_counts.items())),
        "unknown_commands_processed": dict(sorted(unknown_commands.items())),
        "first_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
        "last_timestamp_utc_seen": depth.iso_utc(depth.sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
        "header_record_count": header.record_count,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "file_size_bytes": header.size_bytes,
    }
    return feature_rows, sample_rows, blocker_rows, file_row


def bucket_rows(feature_rows: list[dict[str, Any]], blocker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: Counter[tuple[str, str, str, str, str, str]] = Counter()
    for row in feature_rows:
        grouped[
            (
                str(row.get("fallback_ladder_snapshot_bucket")),
                str(row.get("fallback_event15_proxy_bucket")),
                str(row.get("command_fallback_route_relation_bucket")),
                str(row.get("command_feature_bucket")),
                str(row.get("fallback_event15_imbalance_sign")),
                str(row.get("route_c_full_control_bucket")),
            )
        ] += 1
    for row in blocker_rows:
        grouped[
            (
                str(row.get("blocker_type")),
                str(row.get("fallback_event15_proxy_bucket")),
                str(row.get("command_fallback_route_relation_bucket")),
                str(row.get("command_feature_bucket")),
                str(row.get("fallback_event15_imbalance_sign")),
                str(row.get("route_c_full_control_bucket")),
            )
        ] += 0
    out: list[dict[str, Any]] = []
    for ordinal, (key, count) in enumerate(sorted(grouped.items()), start=1):
        fallback_bucket, event15_proxy_bucket, relation_bucket, command_bucket, fallback_sign, route_bucket = key
        out.append(
            {
                "bucket_id": f"SIERRA-DEPTH-LADDER-FALLBACK-BUCKET-{ordinal:04d}",
                "fallback_ladder_snapshot_bucket": fallback_bucket,
                "fallback_event15_proxy_bucket": event15_proxy_bucket,
                "command_fallback_route_relation_bucket": relation_bucket,
                "command_feature_bucket": command_bucket,
                "fallback_event15_imbalance_sign": fallback_sign,
                "route_c_full_control_bucket": route_bucket,
                "row_count": count,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return out


def question_rows(
    bucket_counts: Counter[str],
    event15_proxy_bucket_counts: Counter[str],
    relation_counts: Counter[str],
    counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket, count in sorted(bucket_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-FALLBACK-Q-{len(rows) + 1:03d}",
                "question_family": "fallback_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"What command-flow, route-control, and same-source neighbor split follows for all {count} rows in {bucket}?",
                "next_same_resource_action": fallback_next_action(bucket),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(relation_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-FALLBACK-Q-{len(rows) + 1:03d}",
                "question_family": "command_fallback_relation",
                "bucket": bucket,
                "row_count": count,
                "question": f"Does the command-flow/fallback-ladder relation bucket {bucket} behave like generic context, weakening evidence, or a split descriptor across all {count} rows?",
                "next_same_resource_action": "join this relation bucket to same-source neighbor controls and Route C residual transfer classes",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for bucket, count in sorted(event15_proxy_bucket_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-FALLBACK-Q-{len(rows) + 1:03d}",
                "question_family": "event15_proxy_bucket",
                "bucket": bucket,
                "row_count": count,
                "question": f"Can the full-M15 record-level proxy bucket {bucket} explain, weaken, or split the final-minute no-sample blocker across all {count} rows?",
                "next_same_resource_action": "join event15 proxy buckets to command-flow controls, Route C residual transfer classes, and same-source neighbors",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def fallback_next_action(bucket: str) -> str:
    if bucket == "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_IMBALANCED":
        return "split by imbalance sign, command-flow sign, and same-source neighbor context"
    if bucket == "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_BALANCED":
        return "treat as generic denominator context unless route-control residual remains after neighbor split"
    if bucket == "FALLBACK_RECORD_LEVEL_NO_EVENT_SAMPLES":
        return "preserve true empty-event-window source/capture requirement after raw timestamp proof"
    if bucket.endswith("MISSING"):
        return "inspect book completeness and top-depth construction before interpretation"
    return "manual fallback bucket review required"


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_no_event_fallback_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_no_event_fallback_result", "created"),
        (FEATURE_LEDGER, "sierra_depth_ladder_no_event_fallback_feature_ledger", "created"),
        (SAMPLE_LEDGER, "sierra_depth_ladder_no_event_fallback_sample_ledger", "created"),
        (BLOCKER_LEDGER, "sierra_depth_ladder_no_event_fallback_blocker_ledger", "created"),
        (FILE_LEDGER, "sierra_depth_ladder_no_event_fallback_file_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_no_event_fallback_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_no_event_fallback_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_no_event_fallback_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(
    generated_utc: str,
    counts: dict[str, int],
    bucket_counts: Counter[str],
    event15_proxy_bucket_counts: Counter[str],
) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_no_event_fallback_probe",
        "status": "done",
        "route": "sierra_depth_ladder_reconstruction_repair",
        "details": "Replayed every Route C LADDER_BOUNDARY60_NO_EVENT_SAMPLES row at record level, proving final-minute boundary60 remained empty and adding full-M15 event-window proxy splits where available.",
        "counts": counts,
        "fallback_bucket_counts": dict(sorted(bucket_counts.items())),
        "event15_proxy_bucket_counts": dict(sorted(event15_proxy_bucket_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(FEATURE_LEDGER),
            relative(SAMPLE_LEDGER),
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


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    bucket_counts: Counter[str],
    event15_proxy_bucket_counts: Counter[str],
    relation_counts: Counter[str],
) -> None:
    lines = [
        "# Sierra Depth Ladder No-Event Fallback Probe",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: local Sierra `.depth` record-level fallback for Route C rows where END_OF_BATCH boundary60 sampling produced no event samples. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Fallback Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Event15 Proxy Buckets", ""])
    for key, value in sorted(event15_proxy_bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Command/Fallback Relation Buckets", ""])
    for key, value in sorted(relation_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- Boundary60 remains exact: the run proves whether final-minute command records exist after removing the END_OF_BATCH filter.",
            "- Full-M15 event-window record-level summaries are a proxy only when boundary60 is empty; they are not substituted as the exact final-minute descriptor.",
            "- It does not repair exact missing `.depth` files, earlier-book-history/no-prior-clear requirements, or any outcome/validation class.",
            "- Every sampled command record is preserved in the sample ledger; feature rows are per request and bucket rows are aggregate descriptors.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Join fallback relation and full-M15 event proxy buckets into same-source intraday neighbor controls.",
            "- Recompute source/capture requirements after preserving true boundary60-empty rows and adding full-event15 proxy splits.",
            "- Continue source search for exact missing `.depth` files and split imbalanced descriptors by command-ladder sign.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    join_rows = read_jsonl(JOIN_LEDGER)
    target_rows = [
        row for row in join_rows
        if row.get("ladder_blocker_type") == "LADDER_BOUNDARY60_NO_EVENT_SAMPLES"
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        grouped[str(row["depth_path"])].append(row)

    feature_rows: list[dict[str, Any]] = []
    sample_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    for path_str, group in sorted(grouped.items()):
        path = Path(path_str)
        try:
            features, samples, blockers, file_row = process_file(path, group)
        except Exception as exc:  # noqa: BLE001 - preserve exact parser/replay failure.
            file_row = {
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "depth_path": path_str,
                "input_no_event_rows": len(group),
                "feature_rows": 0,
                "sample_rows": 0,
                "blocker_rows": len(group),
                "error": f"{type(exc).__name__}: {exc}",
            }
            file_rows.append(file_row)
            for row in group:
                blocker = {
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    **compact_context(row),
                    "depth_path": path_str,
                    "blocker_type": "FALLBACK_RECORD_LEVEL_REPLAY_ERROR",
                    "fallback_replay_status": "LOCAL_DEPTH_RECORD_LEVEL_REPLAY_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "next_same_resource_action": "inspect parser/file window and rerun after fixing record-level fallback replay error",
                }
                blocker_rows.append(blocker)
            continue
        feature_rows.extend(features)
        sample_rows.extend(samples)
        blocker_rows.extend(blockers)
        file_rows.append(file_row)

    bucket_counts: Counter[str] = Counter(str(row.get("fallback_ladder_snapshot_bucket")) for row in feature_rows)
    event15_proxy_bucket_counts: Counter[str] = Counter(str(row.get("fallback_event15_proxy_bucket")) for row in feature_rows)
    relation_counts: Counter[str] = Counter(str(row.get("command_fallback_route_relation_bucket")) for row in feature_rows)
    counts = {
        "join_input_rows": len(join_rows),
        "target_no_event_rows": len(target_rows),
        "target_depth_files": len(grouped),
        "fallback_feature_rows": len(feature_rows),
        "fallback_sample_rows": len(sample_rows),
        "fallback_blocker_rows": len(blocker_rows),
        "fallback_file_rows": len(file_rows),
        "fallback_bucket_rows": 0,
        "question_rows": 0,
        "event15_proxy_rows": sum(
            1 for row in feature_rows
            if row.get("fallback_event15_proxy_bucket") in {
                "FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_BALANCED_PROXY",
                "FALLBACK_RECORD_LEVEL_EVENT15_DEPTH10_IMBALANCED_PROXY",
            }
        ),
        "repaired_from_no_event_rows": sum(
            1 for row in feature_rows
            if row.get("fallback_ladder_snapshot_bucket") in {
                "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_BALANCED",
                "FALLBACK_RECORD_LEVEL_EVENT_DEPTH10_IMBALANCED",
            }
        ),
    }
    buckets = bucket_rows(feature_rows, blocker_rows)
    questions = question_rows(bucket_counts, event15_proxy_bucket_counts, relation_counts, counts)
    counts["fallback_bucket_rows"] = len(buckets)
    counts["question_rows"] = len(questions)

    write_jsonl(FEATURE_LEDGER, feature_rows)
    write_jsonl(SAMPLE_LEDGER, sample_rows)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(FILE_LEDGER, file_rows)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_no_event_fallback_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_RECORD_LEVEL_NO_EVENT_FALLBACK_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "fallback_bucket_counts": dict(sorted(bucket_counts.items())),
        "event15_proxy_bucket_counts": dict(sorted(event15_proxy_bucket_counts.items())),
        "command_fallback_relation_counts": dict(sorted(relation_counts.items())),
        "next_same_resource_work": [
            "join fallback relation buckets to same-source intraday neighbor controls",
            "recompute ladder source/capture requirements after record-level boundary proof and full-event15 proxy split",
            "continue exact missing .depth source-date acquisition and imbalanced descriptor split work",
        ],
        "not_completion": "This fallback proves the boundary60 blocker class remains true at record level, adds full-event15 proxies, and does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, bucket_counts, event15_proxy_bucket_counts)
    write_summary(generated_utc, counts, bucket_counts, event15_proxy_bucket_counts, relation_counts)
    print(
        json.dumps(
            {
                "ok": True,
                "counts": counts,
                "bucket_counts": dict(bucket_counts),
                "event15_proxy_bucket_counts": dict(event15_proxy_bucket_counts),
                "result": str(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
