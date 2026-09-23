#!/usr/bin/env python3
"""Extract Sierra Chart .depth ladder features for registered event windows.

Research/tooling only. The extractor reconstructs Sierra market-depth books
from local .depth files and emits the same top-of-book/top-10/top-20 depth
feature family used by the Databento MBP-10/MBO diagnostics. It does not touch
live trading code, prompts, risk, execution, or AI APIs.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


MAGIC = 0x44444353
HEADER_STRUCT = struct.Struct("<IIII")
RECORD_STRUCT = struct.Struct("<QBBHfII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
END_OF_BATCH = 0x01

COMMANDS = {
    0: "NO_COMMAND",
    1: "CLEAR_BOOK",
    2: "ADD_BID",
    3: "ADD_ASK",
    4: "MODIFY_BID",
    5: "MODIFY_ASK",
    6: "DELETE_BID",
    7: "DELETE_ASK",
}

FEATURE_FIELDS = (
    "pre60_median_total_depth10",
    "pre60_median_depth10_imbalance",
    "pre60_thin_depth10_threshold",
    "event15_median_total_depth10",
    "event15_median_depth10_imbalance",
    "event15_thin_depth10_rate",
    "event15_median_max_bid_wall",
    "event15_median_max_ask_wall",
    "event15_median_near_far_ratio",
    "event15_mid_change_ticks",
    "event15_sample_count",
)


@dataclass(frozen=True)
class DepthHeader:
    magic: int
    header_size: int
    record_size: int
    version: int
    record_count: int
    remainder: int
    size_bytes: int


def parse_utc(value: str) -> datetime:
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def sierra_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def sierra_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def read_header(path: Path) -> DepthHeader:
    size = path.stat().st_size
    if size < HEADER_STRUCT.size:
        raise ValueError(f"{path} is too small for Sierra depth header")
    with path.open("rb") as handle:
        raw = handle.read(HEADER_STRUCT.size)
    magic, header_size, record_size, version = HEADER_STRUCT.unpack(raw)
    if magic != MAGIC:
        raise ValueError(f"{path} has invalid magic {magic:#x}")
    if header_size < HEADER_STRUCT.size:
        raise ValueError(f"{path} has invalid header size {header_size}")
    if record_size != RECORD_STRUCT.size:
        raise ValueError(f"{path} record size {record_size} != expected {RECORD_STRUCT.size}")
    if size < header_size:
        raise ValueError(f"{path} is smaller than declared header size {header_size}")
    body_bytes = size - header_size
    return DepthHeader(
        magic=magic,
        header_size=header_size,
        record_size=record_size,
        version=version,
        record_count=body_bytes // record_size,
        remainder=body_bytes % record_size,
        size_bytes=size,
    )


def _unpack_record_at(handle: Any, header: DepthHeader, index: int) -> tuple[int, int, int, int, float, int]:
    handle.seek(header.header_size + index * header.record_size)
    raw = handle.read(header.record_size)
    if len(raw) != header.record_size:
        raise IndexError(f"record index {index} outside {header.record_count} records")
    dt_us, command, flags, num_orders, price, quantity, _reserved = RECORD_STRUCT.unpack(raw)
    return int(dt_us), int(command), int(flags), int(num_orders), round(float(price), 8), int(quantity)


def lower_bound_record_index(path: Path, header: DepthHeader, target_us: int) -> int:
    """Return first record index whose timestamp is >= target_us."""
    lo = 0
    hi = header.record_count
    with path.open("rb") as handle:
        while lo < hi:
            mid = (lo + hi) // 2
            dt_us, *_ = _unpack_record_at(handle, header, mid)
            if dt_us < target_us:
                lo = mid + 1
            else:
                hi = mid
    return lo


def replay_start_index_for_window(path: Path, header: DepthHeader, window_start_us: int) -> tuple[int, str]:
    """Find the nearest safe replay point before a feature window.

    Sierra depth command ``CLEAR_BOOK`` resets the reconstructed book. Starting
    replay at the last clear before the pre-decision window preserves book
    correctness while avoiding a full-day replay for every live candidate.
    """
    idx = lower_bound_record_index(path, header, window_start_us)
    if idx <= 0:
        return 0, "FILE_START_BEFORE_WINDOW"
    with path.open("rb") as handle:
        for cursor in range(idx - 1, -1, -1):
            _dt_us, command, _flags, _orders, _price, _quantity = _unpack_record_at(handle, header, cursor)
            if command == 1:
                return cursor, "LAST_CLEAR_BOOK_BEFORE_WINDOW"
    return 0, "NO_CLEAR_BOOK_BEFORE_WINDOW"


def iter_records(
    path: Path,
    header: DepthHeader,
    chunk_records: int = 1_000_000,
    *,
    start_record: int = 0,
) -> Iterable[tuple[int, int, int, int, float, int]]:
    chunk_size = header.record_size * chunk_records
    with path.open("rb") as handle:
        handle.seek(header.header_size + max(0, start_record) * header.record_size)
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            usable = len(chunk) - (len(chunk) % header.record_size)
            for offset in range(0, usable, header.record_size):
                dt_us, command, flags, num_orders, price, quantity, _reserved = RECORD_STRUCT.unpack_from(chunk, offset)
                yield int(dt_us), int(command), int(flags), int(num_orders), round(float(price), 8), int(quantity)


def apply_book_record(
    command: int,
    price: float,
    quantity: int,
    num_orders: int,
    bids: dict[float, tuple[int, int]],
    asks: dict[float, tuple[int, int]],
) -> None:
    value = (int(quantity), int(num_orders))
    if command == 1:
        bids.clear()
        asks.clear()
    elif command in (2, 4):
        bids[price] = value
    elif command in (3, 5):
        asks[price] = value
    elif command == 6:
        bids.pop(price, None)
    elif command == 7:
        asks.pop(price, None)
    elif command == 0:
        return
    else:
        raise ValueError(f"unknown Sierra depth command {command}")


def _top_qty(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(qty for _price, (qty, _orders) in levels[:n])


def _top_orders(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(orders for _price, (_qty, orders) in levels[:n])


def _max_wall(levels: list[tuple[float, tuple[int, int]]], n: int) -> int:
    return max((qty for _price, (qty, _orders) in levels[:n]), default=0)


def _imbalance(bid_qty: float, ask_qty: float) -> float | None:
    denom = bid_qty + ask_qty
    return None if denom <= 0 else (bid_qty - ask_qty) / denom


def snapshot_features(
    bids: dict[float, tuple[int, int]],
    asks: dict[float, tuple[int, int]],
    *,
    timestamp_us: int,
    tick_size: float,
) -> dict[str, Any]:
    bid_levels = sorted(bids.items(), key=lambda item: item[0], reverse=True)
    ask_levels = sorted(asks.items(), key=lambda item: item[0])
    best_bid = bid_levels[0][0] if bid_levels else None
    best_ask = ask_levels[0][0] if ask_levels else None
    out: dict[str, Any] = {
        "timestamp_utc": iso_utc(sierra_datetime(timestamp_us)),
        "timestamp_us": timestamp_us,
        "book_levels_bid": len(bid_levels),
        "book_levels_ask": len(ask_levels),
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
        total = bid_qty + ask_qty
        out[f"top_{n}_bid_qty"] = bid_qty
        out[f"top_{n}_ask_qty"] = ask_qty
        out[f"total_depth{n}"] = total
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


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def median(values: list[Any]) -> float | None:
    clean = sorted(v for v in (safe_float(value) for value in values) if v is not None)
    if not clean:
        return None
    mid = len(clean) // 2
    if len(clean) % 2:
        return clean[mid]
    return (clean[mid - 1] + clean[mid]) / 2.0


def quantile(values: list[Any], q: float) -> float | None:
    clean = sorted(v for v in (safe_float(value) for value in values) if v is not None)
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    pos = (len(clean) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return clean[low]
    return clean[low] + (clean[high] - clean[low]) * (pos - low)


def sign_change_rate(values: list[Any]) -> float | None:
    signs: list[int] = []
    for value in values:
        clean = safe_float(value)
        if clean is None or clean == 0:
            continue
        signs.append(1 if clean > 0 else -1)
    if len(signs) < 2:
        return None
    changes = sum(1 for previous, current in zip(signs, signs[1:]) if previous != current)
    return changes / (len(signs) - 1)


def summarize_samples(
    samples: list[dict[str, Any]],
    prefix: str,
    *,
    tick_size: float,
    thin_threshold: float | None = None,
) -> dict[str, Any]:
    if not samples:
        return {
            f"{prefix}_sample_count": 0,
            f"{prefix}_median_spread_ticks": None,
            f"{prefix}_median_depth10_imbalance": None,
            f"{prefix}_median_depth20_imbalance": None,
            f"{prefix}_median_total_depth10": None,
            f"{prefix}_median_total_depth20": None,
            f"{prefix}_thin_depth10_rate": None,
            f"{prefix}_thin_depth20_rate": None,
            f"{prefix}_median_near_far_ratio": None,
            f"{prefix}_median_near_far_ratio20": None,
            f"{prefix}_median_max_bid_wall": None,
            f"{prefix}_median_max_ask_wall": None,
            f"{prefix}_median_max_bid_wall20": None,
            f"{prefix}_median_max_ask_wall20": None,
            f"{prefix}_median_wall_concentration10": None,
            f"{prefix}_median_wall_concentration20": None,
            f"{prefix}_depth10_imbalance_flip_rate": None,
            f"{prefix}_mid_change_ticks": None,
        }
    mid = [sample.get("mid_px") for sample in samples if sample.get("mid_px") is not None]
    mid_change = None
    if len(mid) >= 2:
        mid_change = (float(mid[-1]) - float(mid[0])) / tick_size
    total10 = [sample.get("total_depth10") for sample in samples]
    total20 = [sample.get("total_depth20") for sample in samples]
    thin10 = None
    thin20 = None
    if thin_threshold is not None:
        thin10 = sum(1 for value in total10 if safe_float(value) is not None and float(value) <= thin_threshold) / len(total10)
        thin20 = sum(1 for value in total20 if safe_float(value) is not None and float(value) <= thin_threshold) / len(total20)
    return {
        f"{prefix}_sample_count": len(samples),
        f"{prefix}_median_spread_ticks": median([sample.get("spread_ticks") for sample in samples]),
        f"{prefix}_median_depth10_imbalance": median([sample.get("depth10_imbalance") for sample in samples]),
        f"{prefix}_median_depth20_imbalance": median([sample.get("depth20_imbalance") for sample in samples]),
        f"{prefix}_median_total_depth10": median(total10),
        f"{prefix}_median_total_depth20": median(total20),
        f"{prefix}_thin_depth10_rate": thin10,
        f"{prefix}_thin_depth20_rate": thin20,
        f"{prefix}_median_near_far_ratio": median([sample.get("near_far_ratio") for sample in samples]),
        f"{prefix}_median_near_far_ratio20": median([sample.get("near_far_ratio20") for sample in samples]),
        f"{prefix}_median_max_bid_wall": median([sample.get("max_bid_wall10") for sample in samples]),
        f"{prefix}_median_max_ask_wall": median([sample.get("max_ask_wall10") for sample in samples]),
        f"{prefix}_median_max_bid_wall20": median([sample.get("max_bid_wall20") for sample in samples]),
        f"{prefix}_median_max_ask_wall20": median([sample.get("max_ask_wall20") for sample in samples]),
        f"{prefix}_median_wall_concentration10": median([sample.get("wall_concentration10") for sample in samples]),
        f"{prefix}_median_wall_concentration20": median([sample.get("wall_concentration20") for sample in samples]),
        f"{prefix}_depth10_imbalance_flip_rate": sign_change_rate([sample.get("depth10_imbalance") for sample in samples]),
        f"{prefix}_mid_change_ticks": mid_change,
    }


def _samples_from_seconds(raw: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    return [raw[key] for key in sorted(raw)]


def extract_event_features(
    *,
    depth_path: Path,
    event: dict[str, Any],
    source_symbol: str,
    futures_symbol: str,
    tick_size: float,
) -> dict[str, Any]:
    header = read_header(depth_path)
    canonical = parse_utc(event["canonical_m15_close_utc"])
    window_start = parse_utc(event["window_start_utc"])
    pre_start_us = sierra_us(window_start)
    canonical_us = sierra_us(canonical)
    event15_start_us = sierra_us(canonical - timedelta(minutes=15))
    replay_start_index, replay_start_reason = replay_start_index_for_window(path=depth_path, header=header, window_start_us=pre_start_us)
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    command_counts: Counter[str] = Counter()
    pre60_by_second: dict[int, dict[str, Any]] = {}
    event15_by_second: dict[int, dict[str, Any]] = {}
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    records_processed = 0
    batches_seen = 0
    unknown_commands: Counter[int] = Counter()
    for dt_us, command, flags, num_orders, price, quantity in iter_records(depth_path, header, start_record=replay_start_index):
        if dt_us >= canonical_us:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_counts[COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in COMMANDS:
            unknown_commands[command] += 1
            continue
        apply_book_record(command, price, quantity, num_orders, bids, asks)
        if flags & END_OF_BATCH:
            batches_seen += 1
            if pre_start_us <= dt_us < canonical_us:
                sample = snapshot_features(bids, asks, timestamp_us=dt_us, tick_size=tick_size)
                pre60_by_second[dt_us // 1_000_000] = sample
                if event15_start_us <= dt_us < canonical_us:
                    event15_by_second[dt_us // 1_000_000] = sample
    pre60 = _samples_from_seconds(pre60_by_second)
    event15 = _samples_from_seconds(event15_by_second)
    pre60_threshold = quantile([sample.get("total_depth10") for sample in pre60], 0.2)
    row: dict[str, Any] = {
        "event_id": event["event_id"],
        "symbol": event.get("symbol"),
        "source_symbol": source_symbol,
        "futures_symbol": futures_symbol,
        "source_system": "sierra_depth",
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "event_class": event.get("event_class"),
        "decision": event.get("decision"),
        "framework": event.get("framework"),
        "direction": event.get("direction"),
        "canonical_m15_close_utc": event["canonical_m15_close_utc"],
        "window_start_utc": event["window_start_utc"],
        "window_end_utc": event["window_end_utc"],
        "depth_path": str(depth_path),
        "tick_size": tick_size,
        "data_status": "ok" if pre60 and event15 else "no_depth_samples",
        "sample_method": "end_of_batch_last_snapshot_per_second",
        "pre60_thin_depth10_threshold": pre60_threshold,
    }
    row.update(summarize_samples(pre60, "pre60", tick_size=tick_size))
    row.update(summarize_samples(event15, "event15", tick_size=tick_size, thin_threshold=pre60_threshold))
    return {
        "header": {
            "magic": f"{header.magic:#x}",
            "header_size": header.header_size,
            "record_size": header.record_size,
            "version": header.version,
            "record_count": header.record_count,
            "remainder": header.remainder,
            "size_bytes": header.size_bytes,
            "replay_start_record_index": replay_start_index,
            "replay_start_reason": replay_start_reason,
            "first_timestamp_utc_seen": iso_utc(sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
            "last_timestamp_utc_seen": iso_utc(sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
            "records_processed_until_canonical": records_processed,
            "batches_seen_until_canonical": batches_seen,
            "command_counts_until_canonical": dict(sorted(command_counts.items())),
            "unknown_commands_until_canonical": dict(sorted(unknown_commands.items())),
        },
        "feature_row": row,
    }


def _build_event_feature_row(
    *,
    depth_path: Path,
    event: dict[str, Any],
    source_symbol: str,
    futures_symbol: str,
    tick_size: float,
    pre60: list[dict[str, Any]],
    event15: list[dict[str, Any]],
) -> dict[str, Any]:
    pre60_threshold = quantile([sample.get("total_depth10") for sample in pre60], 0.2)
    row: dict[str, Any] = {
        "event_id": event["event_id"],
        "symbol": event.get("symbol"),
        "source_symbol": source_symbol,
        "futures_symbol": futures_symbol,
        "source_system": "sierra_depth",
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "event_class": event.get("event_class"),
        "decision": event.get("decision"),
        "framework": event.get("framework"),
        "direction": event.get("direction"),
        "canonical_m15_close_utc": event["canonical_m15_close_utc"],
        "window_start_utc": event["window_start_utc"],
        "window_end_utc": event["window_end_utc"],
        "depth_path": str(depth_path),
        "tick_size": tick_size,
        "data_status": "ok" if pre60 and event15 else "no_depth_samples",
        "sample_method": "end_of_batch_last_snapshot_per_second",
        "pre60_thin_depth10_threshold": pre60_threshold,
    }
    row.update(summarize_samples(pre60, "pre60", tick_size=tick_size))
    row.update(summarize_samples(event15, "event15", tick_size=tick_size, thin_threshold=pre60_threshold))
    return row


def _depth_header_payload(
    *,
    header: DepthHeader,
    replay_start_index: int,
    replay_start_reason: str,
    first_ts_us: int | None,
    last_ts_us: int | None,
    records_processed: int,
    batches_seen: int,
    command_counts: Counter[str],
    unknown_commands: Counter[int],
    batch_event_count: int | None = None,
) -> dict[str, Any]:
    payload = {
        "magic": f"{header.magic:#x}",
        "header_size": header.header_size,
        "record_size": header.record_size,
        "version": header.version,
        "record_count": header.record_count,
        "remainder": header.remainder,
        "size_bytes": header.size_bytes,
        "replay_start_record_index": replay_start_index,
        "replay_start_reason": replay_start_reason,
        "first_timestamp_utc_seen": iso_utc(sierra_datetime(first_ts_us)) if first_ts_us is not None else None,
        "last_timestamp_utc_seen": iso_utc(sierra_datetime(last_ts_us)) if last_ts_us is not None else None,
        "records_processed_until_canonical": records_processed,
        "batches_seen_until_canonical": batches_seen,
        "command_counts_until_canonical": dict(sorted(command_counts.items())),
        "unknown_commands_until_canonical": dict(sorted(unknown_commands.items())),
    }
    if batch_event_count is not None:
        payload["batch_depth_file_event_count"] = batch_event_count
        payload["feature_extraction_mode"] = "batch_depth_file_single_pass"
    return payload


def extract_events_features_batch(
    *,
    depth_path: Path,
    events: Iterable[dict[str, Any]],
    source_symbol: str,
    futures_symbol: str,
    tick_size: float,
) -> dict[str, dict[str, Any]]:
    """Extract multiple event windows from one .depth file in a single pass."""
    event_infos: list[dict[str, Any]] = []
    for event in events:
        canonical = parse_utc(event["canonical_m15_close_utc"])
        window_start = parse_utc(event["window_start_utc"])
        canonical_us = sierra_us(canonical)
        event_infos.append(
            {
                "event": event,
                "event_id": str(event["event_id"]),
                "canonical_us": canonical_us,
                "pre_start_us": sierra_us(window_start),
                "event15_start_us": sierra_us(canonical - timedelta(minutes=15)),
                "pre60_by_second": {},
                "event15_by_second": {},
                "header": None,
            }
        )
    if not event_infos:
        return {}

    header = read_header(depth_path)
    min_pre_start_us = min(int(info["pre_start_us"]) for info in event_infos)
    max_canonical_us = max(int(info["canonical_us"]) for info in event_infos)
    replay_start_index, replay_start_reason = replay_start_index_for_window(
        path=depth_path,
        header=header,
        window_start_us=min_pre_start_us,
    )
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    command_counts: Counter[str] = Counter()
    unknown_commands: Counter[int] = Counter()
    first_ts_us: int | None = None
    last_ts_us: int | None = None
    records_processed = 0
    batches_seen = 0
    finalize_order = sorted(event_infos, key=lambda item: int(item["canonical_us"]))
    finalize_index = 0

    def finalize_until(timestamp_us: int | None) -> None:
        nonlocal finalize_index
        threshold = max_canonical_us + 1 if timestamp_us is None else timestamp_us
        while finalize_index < len(finalize_order) and int(finalize_order[finalize_index]["canonical_us"]) <= threshold:
            info = finalize_order[finalize_index]
            if info.get("header") is None:
                info["header"] = _depth_header_payload(
                    header=header,
                    replay_start_index=replay_start_index,
                    replay_start_reason=replay_start_reason,
                    first_ts_us=first_ts_us,
                    last_ts_us=last_ts_us,
                    records_processed=records_processed,
                    batches_seen=batches_seen,
                    command_counts=command_counts.copy(),
                    unknown_commands=unknown_commands.copy(),
                    batch_event_count=len(event_infos),
                )
            finalize_index += 1

    for dt_us, command, flags, num_orders, price, quantity in iter_records(
        depth_path,
        header,
        start_record=replay_start_index,
    ):
        finalize_until(dt_us)
        if dt_us >= max_canonical_us:
            break
        if first_ts_us is None:
            first_ts_us = dt_us
        last_ts_us = dt_us
        records_processed += 1
        command_counts[COMMANDS.get(command, f"UNKNOWN_{command}")] += 1
        if command not in COMMANDS:
            unknown_commands[command] += 1
            continue
        apply_book_record(command, price, quantity, num_orders, bids, asks)
        if flags & END_OF_BATCH:
            batches_seen += 1
            if dt_us < min_pre_start_us:
                continue
            sample = snapshot_features(bids, asks, timestamp_us=dt_us, tick_size=tick_size)
            second = dt_us // 1_000_000
            for info in event_infos:
                if int(info["pre_start_us"]) <= dt_us < int(info["canonical_us"]):
                    info["pre60_by_second"][second] = sample
                    if int(info["event15_start_us"]) <= dt_us:
                        info["event15_by_second"][second] = sample
    finalize_until(None)

    out: dict[str, dict[str, Any]] = {}
    for info in event_infos:
        pre60 = _samples_from_seconds(info["pre60_by_second"])
        event15 = _samples_from_seconds(info["event15_by_second"])
        out[info["event_id"]] = {
            "header": info["header"]
            or _depth_header_payload(
                header=header,
                replay_start_index=replay_start_index,
                replay_start_reason=replay_start_reason,
                first_ts_us=first_ts_us,
                last_ts_us=last_ts_us,
                records_processed=records_processed,
                batches_seen=batches_seen,
                command_counts=command_counts.copy(),
                unknown_commands=unknown_commands.copy(),
                batch_event_count=len(event_infos),
            ),
            "feature_row": _build_event_feature_row(
                depth_path=depth_path,
                event=info["event"],
                source_symbol=source_symbol,
                futures_symbol=futures_symbol,
                tick_size=tick_size,
                pre60=pre60,
                event15=event15,
            ),
        }
    return out


def load_event(manifest_path: Path, event_id: str) -> dict[str, Any]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    for event in payload.get("events") or []:
        if event.get("event_id") == event_id:
            return event
    raise ValueError(f"event_id {event_id!r} not found in {manifest_path}")


def depth_path_for_event(depth_dir: Path, source_symbol: str, event: dict[str, Any]) -> Path:
    date = parse_utc(event["canonical_m15_close_utc"]).date().isoformat()
    return depth_dir / f"{source_symbol}.{date}.depth"


def compare_databento(feature_row: dict[str, Any], databento_feature_path: Path | None) -> dict[str, Any] | None:
    if databento_feature_path is None or not databento_feature_path.exists():
        return None
    payload = json.loads(databento_feature_path.read_text(encoding="utf-8"))
    rows = [row for row in payload.get("feature_rows") or [] if row.get("event_id") == feature_row.get("event_id")]
    expected_futures_symbol = feature_row.get("futures_symbol")
    if expected_futures_symbol:
        matched_symbol_rows = [row for row in rows if row.get("futures_symbol") == expected_futures_symbol]
        if matched_symbol_rows:
            rows = matched_symbol_rows
    if not rows:
        return {
            "status": "databento_row_missing",
            "databento_feature_path": str(databento_feature_path),
            "event_id": feature_row.get("event_id"),
            "futures_symbol": expected_futures_symbol,
        }
    db_row = rows[0]
    fields = [
        "pre60_median_total_depth10",
        "event15_median_total_depth10",
        "pre60_median_depth10_imbalance",
        "event15_median_depth10_imbalance",
        "event15_thin_depth10_rate",
        "event15_median_max_bid_wall",
        "event15_median_max_ask_wall",
        "event15_median_near_far_ratio",
        "event15_mid_change_ticks",
        "event15_sample_count",
    ]
    comparisons: dict[str, Any] = {}
    for field in fields:
        sierra_value = feature_row.get(field)
        databento_value = db_row.get(field)
        delta = None
        if safe_float(sierra_value) is not None and safe_float(databento_value) is not None:
            delta = float(sierra_value) - float(databento_value)
        comparisons[field] = {
            "sierra": sierra_value,
            "databento": databento_value,
            "sierra_minus_databento": delta,
        }
    return {
        "status": "matched_cached_databento_feature_row",
        "databento_feature_path": str(databento_feature_path),
        "event_id": feature_row.get("event_id"),
        "futures_symbol": expected_futures_symbol,
        "databento_futures_symbol": db_row.get("futures_symbol"),
        "field_comparisons": comparisons,
        "interpretation_boundary": "This is schema/field parity and rough source comparison only; it is not a validation or calibration claim.",
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    event = load_event(manifest_path, args.event_id)
    depth_path = Path(args.depth_path) if args.depth_path else depth_path_for_event(Path(args.depth_dir), args.source_symbol, event)
    extracted = extract_event_features(
        depth_path=depth_path,
        event=event,
        source_symbol=args.source_symbol,
        futures_symbol=args.futures_symbol,
        tick_size=float(args.tick_size),
    )
    feature_row = extracted["feature_row"]
    databento_comparison = compare_databento(
        feature_row,
        Path(args.databento_feature_json) if args.databento_feature_json else None,
    )
    return {
        "schema_version": "sierra_depth_feature_extraction_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "research/tooling only",
        "inputs": {
            "manifest": str(manifest_path),
            "event_id": args.event_id,
            "depth_path": str(depth_path),
            "source_symbol": args.source_symbol,
            "futures_symbol": args.futures_symbol,
            "tick_size": float(args.tick_size),
            "databento_feature_json": args.databento_feature_json,
            "feature_contract": list(FEATURE_FIELDS),
            "forbidden_inputs": ["post15", "post60", "future outcomes", "AI/LLM calls"],
        },
        "depth_header": extracted["header"],
        "feature_rows": [feature_row],
        "databento_comparison": databento_comparison,
        "synthesis": {
            "status": "DEPTH_FEATURE_EXTRACTION_COMPLETE" if feature_row.get("data_status") == "ok" else "DEPTH_FEATURE_EXTRACTION_NO_SAMPLES",
            "sample_method": feature_row.get("sample_method"),
            "feature_row_count": 1,
            "data_status_counts": {str(feature_row.get("data_status")): 1},
            "no_leak_status": "PASS_PRE_DECISION_WINDOWS_ONLY",
            "evidence_class": "FUTURES_PROXY_TRANSFER",
            "interpretation": [
                "Sierra .depth is parsed into the registered ladder-depth feature family.",
                "Feature windows are pre-decision only: pre60 and event15 ending at the canonical M15 close.",
                "The comparison to cached Databento, when present, is source/field parity only and not a promotion or validation claim.",
            ],
            "remaining_blockers": [
                "One event window does not establish source equivalence.",
                "Sierra depth records are source/proxy transfer and not MT5 broker execution truth.",
                "Actual broker-R label coverage remains sparse for orderflow promotion.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{float(value):.6g}"
    return str(value)


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    feature = payload["feature_rows"][0]
    header = payload["depth_header"]
    comparison = payload.get("databento_comparison") or {}
    lines = [
        "# Sierra Depth Feature Extraction Status - 2026-05-04",
        "",
        "**Scope:** research/tooling only",
        f"**Event:** `{payload['inputs']['event_id']}`",
        f"**Evidence class:** `{payload['synthesis']['evidence_class']}`",
        "",
        "## Source",
        "",
        f"- Depth file: `{payload['inputs']['depth_path']}`",
        f"- Source symbol: `{payload['inputs']['source_symbol']}`",
        f"- Futures symbol: `{payload['inputs']['futures_symbol']}`",
        f"- Header magic/header/record/version: `{header['magic']}` / `{header['header_size']}` / `{header['record_size']}` / `{header['version']}`",
        f"- File records: `{header['record_count']}`",
        f"- Records processed until canonical close: `{header['records_processed_until_canonical']}`",
        f"- Batches seen until canonical close: `{header['batches_seen_until_canonical']}`",
        "",
        "## Feature Row",
        "",
        "| Field | Value |",
        "|---|---:|",
    ]
    for field in FEATURE_FIELDS:
        lines.append(f"| `{field}` | {_fmt(feature.get(field))} |")
    lines.extend(
        [
            "",
            "## Cached Databento Field Comparison",
            "",
            f"- Status: `{comparison.get('status', 'not_requested')}`",
            f"- Boundary: `{comparison.get('interpretation_boundary', 'No cached comparison row was requested or found.')}`",
            "",
        ]
    )
    if comparison.get("field_comparisons"):
        lines.extend(["| Field | Sierra | Databento | Sierra - Databento |", "|---|---:|---:|---:|"])
        for field, row in comparison["field_comparisons"].items():
            lines.append(
                f"| `{field}` | {_fmt(row.get('sierra'))} | {_fmt(row.get('databento'))} | {_fmt(row.get('sierra_minus_databento'))} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Synthesis",
            "",
            f"- Status: `{payload['synthesis']['status']}`",
            f"- No-leak status: `{payload['synthesis']['no_leak_status']}`",
            *[f"- {item}" for item in payload["synthesis"]["interpretation"]],
            "",
            "## Remaining Blockers",
            "",
            *[f"- {item}" for item in payload["synthesis"]["remaining_blockers"]],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--source-symbol", required=True)
    parser.add_argument("--futures-symbol", required=True)
    parser.add_argument("--tick-size", type=float, required=True)
    parser.add_argument("--depth-dir", default=r"C:\SierraChart\Data\MarketDepthData")
    parser.add_argument("--depth-path")
    parser.add_argument("--databento-feature-json")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args)
    write_json(payload, Path(args.output_json))
    write_markdown(payload, Path(args.output_md))
    print(
        json.dumps(
            {
                "output_json": args.output_json,
                "output_md": args.output_md,
                "status": payload["synthesis"]["status"],
                "event_id": args.event_id,
                "data_status": payload["feature_rows"][0].get("data_status"),
                "event15_sample_count": payload["feature_rows"][0].get("event15_sample_count"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
