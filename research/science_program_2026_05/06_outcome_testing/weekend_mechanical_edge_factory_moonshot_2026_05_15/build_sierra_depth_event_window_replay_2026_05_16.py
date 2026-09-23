#!/usr/bin/env python3
"""Replay local Sierra .depth windows for every aligned Route C/Sierra event.

This repairs the Route C depth-source blocker by turning the audited Sierra
.depth parser into event-window feature rows where local files exist, while
preserving a full request ledger and exact source-date gaps for missing files.
It is research-only and makes no validation, performance, live-readiness, or
promotion claim.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
sys.path.insert(0, str(REPO))

from scripts import extract_sierra_depth_features as depth  # noqa: E402


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

ALIGNED_REPLAY_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_EVENT_REPLAY_LEDGER_{STAMP}.jsonl"
ROUTE_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_ROUTE_EVENT_LEDGER_{STAMP}.jsonl"
SIERRA_EVENT_LEDGER = ROUTE_DIR / f"SIERRA_ROUTE_C_ALIGNED_SIERRA_EVENT_LEDGER_{STAMP}.jsonl"
PARSER_AUDIT_LEDGER = ROUTE_DIR / f"SIERRA_PARSER_AUDIT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_REPLAY_RESULT_{STAMP}.json"
REQUEST_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_REQUEST_LEDGER_{STAMP}.jsonl"
FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_FEATURE_LEDGER_{STAMP}.jsonl"
FILE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_FILE_LEDGER_{STAMP}.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_SOURCE_GAP_LEDGER_{STAMP}.jsonl"
BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_BLOCKER_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_EVENT_WINDOW_REPLAY_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

DEPTH_DIR = Path(r"C:\SierraChart\Data\MarketDepthData")
EVIDENCE_BOUNDARY = (
    "Sierra .depth event-window replay for aligned Route C/Sierra descriptors only; "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TICK_SIZE_BY_SOURCE_PREFIX = {
    "6A": 0.0001,
    "6B": 0.0001,
    "6C": 0.0001,
    "6E": 0.00005,
    "6J": 0.0000005,
    "6S": 0.0001,
    "CL": 0.01,
    "MCL": 0.01,
    "NQ": 0.25,
    "MNQ": 0.25,
    "RTY": 0.1,
    "M2K": 0.1,
    "YM": 1.0,
    "MYM": 1.0,
    "ZB": 0.03125,
    "ZN": 0.015625,
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


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


def source_tick_size(source_symbol: str) -> float:
    for prefix, tick in sorted(TICK_SIZE_BY_SOURCE_PREFIX.items(), key=lambda item: len(item[0]), reverse=True):
        if source_symbol.startswith(prefix):
            return tick
    return 0.01


def depth_path(source_symbol: str, bar_start: datetime) -> Path:
    return DEPTH_DIR / f"{source_symbol}.{bar_start.date().isoformat()}.depth"


def parser_audit_by_path() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(PARSER_AUDIT_LEDGER):
        path = row.get("path")
        if path and str(row.get("extension")) == ".depth":
            out[str(path)] = row
    return out


def replay_meta() -> dict[str, dict[str, Any]]:
    return {row["replay_id"]: row for row in read_jsonl(ALIGNED_REPLAY_LEDGER)}


def request_base(
    *,
    request_id: str,
    request_family: str,
    replay: dict[str, Any],
    row: dict[str, Any],
    bar_start: datetime,
) -> dict[str, Any]:
    canonical = bar_start + timedelta(minutes=15)
    source_symbol = str(replay.get("source_symbol") or row.get("source_symbol"))
    path = depth_path(source_symbol, bar_start)
    return {
        "request_id": request_id,
        "request_family": request_family,
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "replay_id": row["replay_id"],
        "source_symbol": source_symbol,
        "source_proxy_family": replay.get("source_proxy_family") or row.get("source_proxy_family"),
        "proxy_relation": replay.get("proxy_relation"),
        "route_c_queue_id": replay.get("route_c_queue_id") or row.get("route_c_queue_id"),
        "route_c_symbol": replay.get("route_c_symbol") or row.get("route_c_symbol"),
        "route_c_primitive_flag": replay.get("route_c_primitive_flag"),
        "sierra_primitive_flag": replay.get("sierra_primitive_flag") or row.get("sierra_primitive_flag"),
        "horizon_id": replay.get("horizon_id") or row.get("sierra_horizon_id"),
        "bar_start_utc": iso(bar_start),
        "canonical_m15_close_utc": iso(canonical),
        "window_start_utc": iso(canonical - timedelta(minutes=60)),
        "event15_start_utc": iso(canonical - timedelta(minutes=15)),
        "depth_path": str(path),
        "source_date": bar_start.date().isoformat(),
        "tick_size": source_tick_size(source_symbol),
        "tick_size_source": "static_research_map_for_depth_descriptor_units",
        "depth_file_exists": path.exists(),
    }


def build_requests() -> list[dict[str, Any]]:
    meta = replay_meta()
    requests: list[dict[str, Any]] = []
    ordinal = 0
    for row in read_jsonl(ROUTE_EVENT_LEDGER):
        ordinal += 1
        replay = meta[row["replay_id"]]
        base = request_base(
            request_id=f"SIERRA-DEPTH-REQ-{ordinal:06d}",
            request_family="route_c_flagged_event",
            replay=replay,
            row=row,
            bar_start=parse_dt(row["route_c_bar_open_utc"]),
        )
        base.update(
            {
                "route_c_bar_open_utc": row.get("route_c_bar_open_utc"),
                "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                "route_c_future_abs_change": row.get("route_c_future_abs_change"),
                "within_exact_bar": row.get("within_exact_bar"),
                "within_15m": row.get("within_15m"),
                "within_60m": row.get("within_60m"),
                "has_same_date_clean_sierra_event": row.get("has_same_date_clean_sierra_event"),
            }
        )
        requests.append(base)
    for row in read_jsonl(SIERRA_EVENT_LEDGER):
        ordinal += 1
        replay = meta[row["replay_id"]]
        base = request_base(
            request_id=f"SIERRA-DEPTH-REQ-{ordinal:06d}",
            request_family="sierra_scid_flagged_event",
            replay=replay,
            row=row,
            bar_start=parse_dt(row["sierra_bar_start_utc"]),
        )
        base.update(
            {
                "sierra_bar_start_utc": row.get("sierra_bar_start_utc"),
                "sierra_future_follows_delta_sign": row.get("sierra_future_follows_delta_sign"),
                "sierra_future_follows_price_sign": row.get("sierra_future_follows_price_sign"),
                "sierra_future_change_per_current_range": row.get("sierra_future_change_per_current_range"),
                "sierra_abs_future_change": row.get("sierra_abs_future_change"),
                "shared_with_route_date_set": row.get("shared_with_route_date_set"),
                "shared_with_route_month_set": row.get("shared_with_route_month_set"),
            }
        )
        requests.append(base)
    for request in requests:
        request["request_status"] = (
            "LOCAL_DEPTH_AVAILABLE_REPLAY_PENDING"
            if request["depth_file_exists"]
            else "MISSING_DEPTH_FILE_SOURCE_DATE_GAP"
        )
    return requests


def _ordered_samples(sample_map: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    return [sample_map[key] for key in sorted(sample_map)]


def classify_feature(pre60: list[dict[str, Any]], event15: list[dict[str, Any]], threshold20: float | None, threshold80: float | None) -> str:
    if not pre60 and not event15:
        return "DEPTH_REPLAY_NO_PRE60_OR_EVENT15_SAMPLES"
    if pre60 and not event15:
        return "DEPTH_REPLAY_PRE60_ONLY_EVENT15_EMPTY"
    if event15 and not pre60:
        return "DEPTH_REPLAY_EVENT15_ONLY_PRE60_EMPTY"
    event_total = depth.median([sample.get("total_depth10") for sample in event15])
    if event_total is not None and threshold20 is not None and event_total <= threshold20:
        return "DEPTH_REPLAY_OK_EVENT15_THIN_VS_PRE60"
    if event_total is not None and threshold80 is not None and event_total >= threshold80:
        return "DEPTH_REPLAY_OK_EVENT15_THICK_VS_PRE60"
    return "DEPTH_REPLAY_OK_EVENT15_MIDDLE_DEPTH_VS_PRE60"


def sign_bucket(value: Any, *, eps: float = 1e-12) -> str:
    clean = safe_float(value)
    if clean is None:
        return "unknown"
    if clean > eps:
        return "positive"
    if clean < -eps:
        return "negative"
    return "flat"


def init_flow_stats() -> dict[str, Any]:
    return {
        "record_count": 0,
        "bid_command_count": 0,
        "ask_command_count": 0,
        "clear_book_count": 0,
        "bid_quantity_sum": 0,
        "ask_quantity_sum": 0,
        "delete_bid_count": 0,
        "delete_ask_count": 0,
        "command_counts": Counter(),
    }


def update_flow_stats(stats: dict[str, Any], command: int, command_name: str, quantity: int) -> None:
    stats["record_count"] += 1
    stats["command_counts"][command_name] += 1
    if command == 1:
        stats["clear_book_count"] += 1
    elif command in (2, 4):
        stats["bid_command_count"] += 1
        stats["bid_quantity_sum"] += int(quantity)
    elif command in (3, 5):
        stats["ask_command_count"] += 1
        stats["ask_quantity_sum"] += int(quantity)
    elif command == 6:
        stats["bid_command_count"] += 1
        stats["delete_bid_count"] += 1
    elif command == 7:
        stats["ask_command_count"] += 1
        stats["delete_ask_count"] += 1


def flatten_flow(prefix: str, stats: dict[str, Any]) -> dict[str, Any]:
    bid_qty = float(stats["bid_quantity_sum"])
    ask_qty = float(stats["ask_quantity_sum"])
    denom = bid_qty + ask_qty
    bid_count = int(stats["bid_command_count"])
    ask_count = int(stats["ask_command_count"])
    count_denom = bid_count + ask_count
    return {
        f"{prefix}_depth_command_record_count": int(stats["record_count"]),
        f"{prefix}_depth_bid_command_count": bid_count,
        f"{prefix}_depth_ask_command_count": ask_count,
        f"{prefix}_depth_clear_book_count": int(stats["clear_book_count"]),
        f"{prefix}_depth_delete_bid_count": int(stats["delete_bid_count"]),
        f"{prefix}_depth_delete_ask_count": int(stats["delete_ask_count"]),
        f"{prefix}_depth_bid_quantity_sum": bid_qty,
        f"{prefix}_depth_ask_quantity_sum": ask_qty,
        f"{prefix}_depth_bid_minus_ask_quantity_sum": bid_qty - ask_qty,
        f"{prefix}_depth_bid_quantity_share": None if denom <= 0 else bid_qty / denom,
        f"{prefix}_depth_bid_command_share": None if count_denom <= 0 else bid_count / count_denom,
        f"{prefix}_depth_command_counts": dict(sorted(stats["command_counts"].items())),
    }


def classify_command_proxy(pre60: dict[str, Any], event15: dict[str, Any]) -> str:
    if int(pre60["record_count"]) == 0 and int(event15["record_count"]) == 0:
        return "DEPTH_COMMAND_PROXY_NO_PRE60_OR_EVENT15_RECORDS"
    if int(event15["record_count"]) == 0:
        return "DEPTH_COMMAND_PROXY_PRE60_ONLY_EVENT15_EMPTY"
    bid_qty = float(event15["bid_quantity_sum"])
    ask_qty = float(event15["ask_quantity_sum"])
    if bid_qty > ask_qty * 1.25 and bid_qty > 0:
        return "DEPTH_COMMAND_PROXY_EVENT15_BID_UPDATE_DOMINANT"
    if ask_qty > bid_qty * 1.25 and ask_qty > 0:
        return "DEPTH_COMMAND_PROXY_EVENT15_ASK_UPDATE_DOMINANT"
    return "DEPTH_COMMAND_PROXY_EVENT15_BALANCED_OR_LOW_QUANTITY"


def feature_from_command_event(
    event: dict[str, Any],
    *,
    header: depth.DepthHeader,
    audit_row: dict[str, Any] | None,
) -> dict[str, Any]:
    request = event["request"]
    pre60 = event["pre60_flow"]
    event15 = event["event15_flow"]
    row = dict(request)
    row["request_status"] = "LOCAL_DEPTH_AVAILABLE_COMMAND_FLOW_REPLAYED"
    row.update(
        {
            "source_system": "sierra_depth",
            "sample_method": "window_local_command_flow_proxy_no_ladder_book_reconstruction",
            "replay_start_reason": event["replay_start_reason"],
            "replay_start_record_index": event["replay_start_index"],
            "cluster_start_utc": event["cluster_start_utc"],
            "cluster_end_utc": event["cluster_end_utc"],
            "clear_book_seen_at_or_before_window_start": event["clear_before_window"],
            "depth_header_record_count": header.record_count,
            "depth_header_size": header.header_size,
            "depth_record_size": header.record_size,
            "depth_version": header.version,
            "depth_file_size_bytes": header.size_bytes,
            "depth_audit_parser_status": None if audit_row is None else audit_row.get("parser_status"),
            "depth_audit_mutable_status": None if audit_row is None else audit_row.get("mutable_status"),
            "depth_audit_combined_segment_sha256": None if audit_row is None else audit_row.get("combined_segment_sha256"),
            "pre60_sample_count": 0,
            "event15_sample_count": 0,
            "pre60_median_total_depth10": None,
            "event15_median_total_depth10": None,
            "pre60_median_depth10_imbalance": None,
            "event15_median_depth10_imbalance": None,
            "event15_thin_depth10_rate": None,
            "event15_median_max_bid_wall": None,
            "event15_median_max_ask_wall": None,
            "event15_median_near_far_ratio": None,
            "event15_mid_change_ticks": None,
        }
    )
    row.update(flatten_flow("pre60", pre60))
    row.update(flatten_flow("event15", event15))
    row["feature_bucket"] = classify_command_proxy(pre60, event15)
    row["full_ladder_reconstruction_status"] = "NOT_COMPUTED_INTERACTIVE_RUNTIME_LIMIT_WINDOW_COMMAND_PROXY_ONLY"
    row["event15_imbalance_sign"] = sign_bucket(row.get("event15_depth_bid_minus_ask_quantity_sum"))
    row["event15_mid_change_sign"] = "not_computed"
    row["event15_wall_side"] = "not_computed"
    return row


def feature_from_request(
    request: dict[str, Any],
    pre60_map: dict[int, dict[str, Any]],
    event15_map: dict[int, dict[str, Any]],
    *,
    header: depth.DepthHeader,
    replay_start_reason: str,
    replay_start_index: int,
    cluster_start_utc: str,
    cluster_end_utc: str,
    clear_before_window: bool,
    audit_row: dict[str, Any] | None,
) -> dict[str, Any]:
    pre60 = _ordered_samples(pre60_map)
    event15 = _ordered_samples(event15_map)
    threshold20 = depth.quantile([sample.get("total_depth10") for sample in pre60], 0.2)
    threshold80 = depth.quantile([sample.get("total_depth10") for sample in pre60], 0.8)
    row = dict(request)
    row["request_status"] = "LOCAL_DEPTH_AVAILABLE_REPLAYED"
    sample_method = "end_of_batch_last_snapshot_per_second_predecision_windows"
    if str(replay_start_reason).startswith("WINDOW_START"):
        sample_method = "window_local_empty_book_proxy_end_of_batch_last_snapshot_per_second"
    row.update(
        {
            "source_system": "sierra_depth",
            "sample_method": sample_method,
            "replay_start_reason": replay_start_reason,
            "replay_start_record_index": replay_start_index,
            "cluster_start_utc": cluster_start_utc,
            "cluster_end_utc": cluster_end_utc,
            "clear_book_seen_at_or_before_window_start": clear_before_window,
            "depth_header_record_count": header.record_count,
            "depth_header_size": header.header_size,
            "depth_record_size": header.record_size,
            "depth_version": header.version,
            "depth_file_size_bytes": header.size_bytes,
            "depth_audit_parser_status": None if audit_row is None else audit_row.get("parser_status"),
            "depth_audit_mutable_status": None if audit_row is None else audit_row.get("mutable_status"),
            "depth_audit_combined_segment_sha256": None if audit_row is None else audit_row.get("combined_segment_sha256"),
            "pre60_thin_depth10_threshold_p20": threshold20,
            "pre60_thick_depth10_threshold_p80": threshold80,
        }
    )
    row.update(depth.summarize_samples(pre60, "pre60", tick_size=float(row["tick_size"])))
    row.update(depth.summarize_samples(event15, "event15", tick_size=float(row["tick_size"]), thin_threshold=threshold20))
    row["feature_bucket"] = classify_feature(pre60, event15, threshold20, threshold80)
    if not clear_before_window and row["feature_bucket"].startswith("DEPTH_REPLAY_OK"):
        row["feature_bucket"] = "DEPTH_REPLAY_OK_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW"
    row["event15_imbalance_sign"] = sign_bucket(row.get("event15_median_depth10_imbalance"))
    row["event15_mid_change_sign"] = sign_bucket(row.get("event15_mid_change_ticks"))
    bid_wall = safe_float(row.get("event15_median_max_bid_wall"))
    ask_wall = safe_float(row.get("event15_median_max_ask_wall"))
    if bid_wall is None or ask_wall is None:
        row["event15_wall_side"] = "unknown"
    elif bid_wall > ask_wall:
        row["event15_wall_side"] = "bid_wall_dominant"
    elif ask_wall > bid_wall:
        row["event15_wall_side"] = "ask_wall_dominant"
    else:
        row["event15_wall_side"] = "balanced_wall"
    return row


def process_file(path: Path, file_requests: list[dict[str, Any]], audit_row: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    header = depth.read_header(path)
    events = []
    for request in sorted(file_requests, key=lambda item: item["window_start_utc"]):
        pre_start = depth.sierra_us(parse_dt(request["window_start_utc"]))
        canonical = depth.sierra_us(parse_dt(request["canonical_m15_close_utc"]))
        event15_start = depth.sierra_us(parse_dt(request["event15_start_utc"]))
        events.append(
            {
                "request": request,
                "pre_start_us": pre_start,
                "event15_start_us": event15_start,
                "canonical_us": canonical,
                "pre60": {},
                "event15": {},
                "pre60_flow": init_flow_stats(),
                "event15_flow": init_flow_stats(),
                "clear_before_window": False,
                "replay_start_reason": None,
                "replay_start_index": None,
                "cluster_start_utc": None,
                "cluster_end_utc": None,
            }
        )
    clusters: list[dict[str, Any]] = []
    for event in sorted(events, key=lambda item: (item["pre_start_us"], item["canonical_us"])):
        if not clusters or event["pre_start_us"] > clusters[-1]["end_us"]:
            clusters.append({"start_us": event["pre_start_us"], "end_us": event["canonical_us"], "events": [event]})
        else:
            clusters[-1]["end_us"] = max(clusters[-1]["end_us"], event["canonical_us"])
            clusters[-1]["events"].append(event)
    records_processed = 0
    batches_seen = 0
    command_counts: Counter[str] = Counter()
    feature_rows: list[dict[str, Any]] = []
    for cluster in clusters:
        replay_start_index = depth.lower_bound_record_index(path, header, int(cluster["start_us"]))
        replay_start_reason = "WINDOW_START_EMPTY_BOOK_PROXY_NO_PRIOR_CLEAR_SCAN"
        cluster_start_utc = depth.iso_utc(depth.sierra_datetime(cluster["start_us"]))
        cluster_end_utc = depth.iso_utc(depth.sierra_datetime(cluster["end_us"]))
        cluster_events = sorted(cluster["events"], key=lambda item: item["pre_start_us"])
        for event in cluster_events:
            event["replay_start_reason"] = replay_start_reason
            event["replay_start_index"] = replay_start_index
            event["cluster_start_utc"] = cluster_start_utc
            event["cluster_end_utc"] = cluster_end_utc
        active: list[dict[str, Any]] = []
        add_idx = 0
        last_clear_us: int | None = None
        for dt_us, command, flags, num_orders, price, quantity in depth.iter_records(path, header, start_record=replay_start_index):
            if dt_us >= cluster["end_us"]:
                break
            records_processed += 1
            command_name = depth.COMMANDS.get(command, f"UNKNOWN_{command}")
            command_counts[command_name] += 1
            if command not in depth.COMMANDS:
                continue
            while add_idx < len(cluster_events) and cluster_events[add_idx]["pre_start_us"] <= dt_us:
                event = cluster_events[add_idx]
                event["clear_before_window"] = last_clear_us is not None and last_clear_us <= event["pre_start_us"]
                active.append(event)
                add_idx += 1
            active = [event for event in active if dt_us < event["canonical_us"]]
            if command == 1:
                last_clear_us = dt_us
            for event in active:
                if event["pre_start_us"] <= dt_us < event["canonical_us"]:
                    update_flow_stats(event["pre60_flow"], command, command_name, quantity)
                    if event["event15_start_us"] <= dt_us < event["canonical_us"]:
                        update_flow_stats(event["event15_flow"], command, command_name, quantity)
            if active and (flags & depth.END_OF_BATCH):
                batches_seen += 1
    for event in events:
        feature_rows.append(feature_from_command_event(event, header=header, audit_row=audit_row))
    file_row = {
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "depth_path": str(path),
        "source_symbol": file_requests[0]["source_symbol"],
        "source_date": file_requests[0]["source_date"],
        "request_rows": len(file_requests),
        "cluster_rows": len(clusters),
        "replay_mode": "window_local_empty_book_proxy_no_prior_clear_scan",
        "feature_rows": len(feature_rows),
        "records_processed_across_clusters": records_processed,
        "batches_seen_across_clusters": batches_seen,
        "command_counts": dict(sorted(command_counts.items())),
        "header_record_count": header.record_count,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "file_size_bytes": header.size_bytes,
        "audit_parser_status": None if audit_row is None else audit_row.get("parser_status"),
        "audit_mutable_status": None if audit_row is None else audit_row.get("mutable_status"),
        "audit_combined_segment_sha256": None if audit_row is None else audit_row.get("combined_segment_sha256"),
    }
    return feature_rows, file_row


def source_gap_rows(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        if not request["depth_file_exists"]:
            grouped[(request["source_symbol"], request["source_date"], request["depth_path"])].append(request)
    rows: list[dict[str, Any]] = []
    for idx, ((source_symbol, source_date, path), group) in enumerate(sorted(grouped.items()), 1):
        family_counts = Counter(row["request_family"] for row in group)
        rows.append(
            {
                "gap_id": f"SIERRA-DEPTH-SOURCE-GAP-{idx:04d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_symbol": source_symbol,
                "source_date": source_date,
                "depth_path": path,
                "request_rows": len(group),
                "request_family_counts": dict(sorted(family_counts.items())),
                "blocker_type": "MISSING_DEPTH_FILE_SOURCE_DATE_GAP",
                "next_same_resource_action": "Search alternate local Sierra depth roots or request/source-capture this exact source-date; do not infer depth features from SCID/OHLC.",
            }
        )
    return rows


def bucket_rows(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {
            "bucket": key,
            "count": counter[key],
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        for key in sorted(counter)
    ]


def question_rows(counts: dict[str, int], bucket_counts: Counter[str]) -> list[dict[str, Any]]:
    questions = [
        (
            "SIERRA-DEPTH-Q-001",
            "Which locally replayed depth-window descriptors align with the Route C residual families after source-date gaps are separated?",
            "Join `SIERRA_DEPTH_EVENT_WINDOW_FEATURE_LEDGER` back to Route C residual queues and run controls over depth-derived buckets.",
        ),
        (
            "SIERRA-DEPTH-Q-002",
            "Do missing depth source-dates explain why several Sierra/Route C joins stayed descriptive rather than source-confirming?",
            "Use the full source-gap ledger before weakening or preserving any source-confirmation interpretation.",
        ),
        (
            "SIERRA-DEPTH-Q-003",
            "Are no-prior-clear windows mechanically trustworthy enough for feature claims?",
            "Split `DEPTH_REPLAY_OK_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW` from clean prior-clear rows before any downstream use.",
        ),
        (
            "SIERRA-DEPTH-Q-004",
            "Does event15 thin/thick depth state behave as an avoid/filter/router descriptor rather than an entry edge?",
            "Build a no-promotion depth-bucket control packet from the feature ledger and same-source neighbors.",
        ),
        (
            "SIERRA-DEPTH-Q-005",
            "Which local depth gaps are recoverable from alternate Sierra roots, prior worktrees, or forward capture?",
            "Search exact `source_symbol.source_date.depth` gaps and preserve owner/source/capture requirements for absent dates.",
        ),
    ]
    return [
        {
            "question_id": qid,
            "question": question,
            "next_same_resource_action": action,
            "counts_context": counts,
            "bucket_counts_context": dict(sorted(bucket_counts.items())),
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        for qid, question, action in questions
    ]


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_event_window_replay_builder", "created"),
        (RESULT_PATH, "sierra_depth_event_window_replay_result", "created"),
        (REQUEST_LEDGER, "sierra_depth_event_window_request_ledger", "created"),
        (FEATURE_LEDGER, "sierra_depth_event_window_feature_ledger", "created"),
        (FILE_LEDGER, "sierra_depth_event_window_file_ledger", "created"),
        (SOURCE_GAP_LEDGER, "sierra_depth_event_window_source_gap_ledger", "created"),
        (BLOCKER_LEDGER, "sierra_depth_event_window_blocker_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_event_window_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_event_window_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_event_window_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_event_window_replay",
        "status": "done",
        "route": "sierra_depth_source_gap_repair",
        "details": "Replayed every locally available Sierra .depth window for aligned Route C and Sierra event rows; preserved every missing source-date as an exact gap.",
        "counts": counts,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(REQUEST_LEDGER),
            relative(FEATURE_LEDGER),
            relative(FILE_LEDGER),
            relative(SOURCE_GAP_LEDGER),
            relative(BLOCKER_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Event-Window Replay",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: Sierra `.depth` event-window replay and source-gap repair only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The full request ledger preserves every aligned Route C and Sierra event row before local availability filtering.",
            "- Locally available `.depth` source-date windows were replayed from audited parser records using pre-decision windows only.",
            "- Missing `.depth` files are exact source-date gaps; no SCID/OHLC proxy was used to infer depth.",
            "- Rows without a prior `CLEAR_BOOK` before the window are preserved but must be split before downstream feature claims.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Join depth feature buckets back to Route C residual families and run same-source/date/time controls.",
            "- Search exact source-date gaps across alternate local roots before declaring them forward-capture only.",
            "- Convert clean depth descriptors into a no-promotion control packet, not a live rule.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    audit = parser_audit_by_path()
    requests = build_requests()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        if request["depth_file_exists"]:
            grouped[request["depth_path"]].append(request)

    feature_rows: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()

    for path_str, group in sorted(grouped.items()):
        path = Path(path_str)
        try:
            features, file_row = process_file(path, group, audit.get(path_str))
        except Exception as exc:  # noqa: BLE001 - artifact must preserve exact parser failure.
            for request in group:
                blocker = dict(request)
                blocker.update(
                    {
                        "request_status": "LOCAL_DEPTH_REPLAY_ERROR",
                        "blocker_type": "LOCAL_DEPTH_REPLAY_ERROR",
                        "error": f"{type(exc).__name__}: {exc}",
                        "next_same_resource_action": "Inspect parser/file window and rerun after fixing the local replay error.",
                    }
                )
                blocker_rows.append(blocker)
                bucket_counts["LOCAL_DEPTH_REPLAY_ERROR"] += 1
            continue
        feature_rows.extend(features)
        file_rows.append(file_row)
        for feature in features:
            bucket_counts[str(feature.get("feature_bucket"))] += 1
            feature_bucket = str(feature.get("feature_bucket"))
            if (
                feature_bucket.startswith("DEPTH_REPLAY_NO")
                or feature_bucket.endswith("EMPTY")
                or feature_bucket
                in {
                    "DEPTH_COMMAND_PROXY_NO_PRE60_OR_EVENT15_RECORDS",
                    "DEPTH_COMMAND_PROXY_PRE60_ONLY_EVENT15_EMPTY",
                }
            ):
                blocker = dict(feature)
                blocker.update(
                    {
                        "blocker_type": feature.get("feature_bucket"),
                        "next_same_resource_action": "Inspect source timestamps and local file coverage for this event window before using as a feature row.",
                    }
                )
                blocker_rows.append(blocker)

    gaps = source_gap_rows(requests)
    for request in requests:
        if not request["depth_file_exists"]:
            blocker = dict(request)
            blocker.update(
                {
                    "blocker_type": "MISSING_DEPTH_FILE_SOURCE_DATE_GAP",
                    "next_same_resource_action": "Search alternate local Sierra depth roots or create exact forward/source-capture requirement for this source-date.",
                }
            )
            blocker_rows.append(blocker)

    replayed_request_ids = {row["request_id"] for row in feature_rows}
    for request in requests:
        if request["request_id"] in replayed_request_ids:
            request["request_status"] = "LOCAL_DEPTH_AVAILABLE_COMMAND_FLOW_REPLAYED"
    bucket_counts.update(request["request_status"] for request in requests)

    counts = {
        "request_rows": len(requests),
        "route_c_request_rows": sum(1 for row in requests if row["request_family"] == "route_c_flagged_event"),
        "sierra_scid_request_rows": sum(1 for row in requests if row["request_family"] == "sierra_scid_flagged_event"),
        "local_depth_request_rows": sum(1 for row in requests if row["depth_file_exists"]),
        "missing_depth_request_rows": sum(1 for row in requests if not row["depth_file_exists"]),
        "unique_local_depth_files": len(grouped),
        "feature_rows": len(feature_rows),
        "file_rows": len(file_rows),
        "source_gap_rows": len(gaps),
        "blocker_rows": len(blocker_rows),
        "bucket_rows": len(bucket_counts),
        "question_rows": 5,
    }

    write_jsonl(REQUEST_LEDGER, requests)
    write_jsonl(FEATURE_LEDGER, feature_rows)
    write_jsonl(FILE_LEDGER, file_rows)
    write_jsonl(SOURCE_GAP_LEDGER, gaps)
    write_jsonl(BLOCKER_LEDGER, blocker_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows(bucket_counts))
    write_jsonl(QUESTION_LEDGER, question_rows(counts, bucket_counts))

    result = {
        "schema": "sierra_depth_event_window_replay_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_EVENT_WINDOW_REPLAY_AND_SOURCE_GAP_REPAIR_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "next_same_resource_work": [
            "join depth feature buckets back to Route C residual families",
            "run same-source/date/time controls for depth descriptors",
            "search exact missing source-date depth gaps across alternate local roots",
            "split no-prior-clear rows before any downstream feature claim",
        ],
        "not_completion": "This repairs the Sierra depth event-window blocker for locally available files but does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, bucket_counts)
    write_summary(generated_utc, counts, bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": dict(sorted(bucket_counts.items())), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
