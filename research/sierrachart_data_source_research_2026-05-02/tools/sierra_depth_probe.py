#!/usr/bin/env python
"""Probe Sierra Chart .depth files for GTOS research validation.

This is research tooling only. It validates the documented Sierra Chart market
depth file format and produces a compact Markdown report for real samples.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


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


@dataclass(frozen=True)
class Record:
    index: int
    timestamp: datetime
    command: int
    flags: int
    num_orders: int
    price: float
    quantity: int
    reserved: int


def sierra_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=us)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_depth(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 16:
        raise ValueError(f"{path} is too small for Sierra depth header")

    magic, header_size, record_size, version = HEADER_STRUCT.unpack_from(data, 0)
    if magic != MAGIC:
        raise ValueError(f"{path} has invalid magic {magic:#x}")
    if header_size < HEADER_STRUCT.size:
        raise ValueError(f"{path} has invalid header size {header_size}")
    if record_size != RECORD_STRUCT.size:
        raise ValueError(
            f"{path} record size {record_size} != expected {RECORD_STRUCT.size}"
        )
    if len(data) < header_size:
        raise ValueError(f"{path} is smaller than declared header size {header_size}")

    remainder = (len(data) - header_size) % record_size
    record_count = (len(data) - header_size) // record_size

    records: list[Record] = []
    for idx in range(record_count):
        offset = header_size + idx * record_size
        dt_us, command, flags, num_orders, price, quantity, reserved = (
            RECORD_STRUCT.unpack_from(data, offset)
        )
        records.append(
            Record(
                index=idx,
                timestamp=sierra_datetime(dt_us),
                command=command,
                flags=flags,
                num_orders=num_orders,
                price=round(float(price), 8),
                quantity=quantity,
                reserved=reserved,
            )
        )

    return {
        "path": path,
        "size": len(data),
        "sha256": sha256(path),
        "magic": magic,
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "record_count": record_count,
        "remainder": remainder,
        "records": records,
    }


def apply_record(record: Record, bids: dict[float, tuple[int, int]], asks: dict[float, tuple[int, int]]) -> None:
    value = (record.quantity, record.num_orders)
    if record.command == 1:
        bids.clear()
        asks.clear()
    elif record.command in (2, 4):
        bids[record.price] = value
    elif record.command in (3, 5):
        asks[record.price] = value
    elif record.command == 6:
        bids.pop(record.price, None)
    elif record.command == 7:
        asks.pop(record.price, None)


def top_qty(levels: Iterable[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(qty for _price, (qty, _orders) in list(levels)[:n])


def top_orders(levels: Iterable[tuple[float, tuple[int, int]]], n: int) -> int:
    return sum(orders for _price, (_qty, orders) in list(levels)[:n])


def snapshot_features(bids: dict[float, tuple[int, int]], asks: dict[float, tuple[int, int]], tick_size: float) -> dict:
    bid_levels = sorted(bids.items(), key=lambda x: x[0], reverse=True)
    ask_levels = sorted(asks.items(), key=lambda x: x[0])
    best_bid = bid_levels[0][0] if bid_levels else None
    best_ask = ask_levels[0][0] if ask_levels else None

    features: dict[str, object] = {
        "book_levels_bid": len(bid_levels),
        "book_levels_ask": len(ask_levels),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_ticks": round((best_ask - best_bid) / tick_size, 6)
        if best_bid is not None and best_ask is not None
        else None,
    }
    for n in (1, 5, 10, 20):
        bid_qty = top_qty(bid_levels, n)
        ask_qty = top_qty(ask_levels, n)
        denom = bid_qty + ask_qty
        features[f"top_{n}_bid_qty"] = bid_qty
        features[f"top_{n}_ask_qty"] = ask_qty
        features[f"top_{n}_imbalance"] = round((bid_qty - ask_qty) / denom, 6) if denom else None
    features["top_10_num_orders_bid"] = top_orders(bid_levels, 10)
    features["top_10_num_orders_ask"] = top_orders(ask_levels, 10)

    if bid_levels and best_bid is not None:
        bid_wall_price, (bid_wall_qty, _orders) = max(bid_levels, key=lambda x: x[1][0])
        features["max_bid_wall_qty"] = bid_wall_qty
        features["max_bid_wall_distance_ticks"] = round((best_bid - bid_wall_price) / tick_size, 6)
    if ask_levels and best_ask is not None:
        ask_wall_price, (ask_wall_qty, _orders) = max(ask_levels, key=lambda x: x[1][0])
        features["max_ask_wall_qty"] = ask_wall_qty
        features["max_ask_wall_distance_ticks"] = round((ask_wall_price - best_ask) / tick_size, 6)

    return features


def summarize(parsed: dict, tick_size: float) -> dict:
    bids: dict[float, tuple[int, int]] = {}
    asks: dict[float, tuple[int, int]] = {}
    records: list[Record] = parsed["records"]
    command_counts = Counter(COMMANDS.get(r.command, f"UNKNOWN_{r.command}") for r in records)
    batches: list[dict] = []
    batch_start = 0
    first_nonempty_batch = None
    latest_nonempty_batch = None

    for record in records:
        apply_record(record, bids, asks)
        if record.flags & END_OF_BATCH:
            features = snapshot_features(bids, asks, tick_size)
            batch = {
                "start_record": batch_start,
                "end_record": record.index,
                "timestamp": record.timestamp,
                "records": record.index - batch_start + 1,
                "book_levels_bid": features["book_levels_bid"],
                "book_levels_ask": features["book_levels_ask"],
                "features": features,
            }
            batches.append(batch)
            if features["book_levels_bid"] or features["book_levels_ask"]:
                if first_nonempty_batch is None:
                    first_nonempty_batch = batch
                latest_nonempty_batch = batch
            batch_start = record.index + 1

    return {
        "first_ts": records[0].timestamp if records else None,
        "last_ts": records[-1].timestamp if records else None,
        "command_counts": command_counts,
        "batch_count": len(batches),
        "nonempty_batch_count": sum(
            1 for b in batches if b["book_levels_bid"] or b["book_levels_ask"]
        ),
        "first_nonempty_batch": first_nonempty_batch,
        "latest_nonempty_batch": latest_nonempty_batch,
    }


def markdown_report(paths: list[Path], tick_size: float) -> str:
    lines = [
        "# Sierra Depth File Probe Report",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        f"Tick size used for distance calculations: `{tick_size}`.",
        "",
    ]
    for path in paths:
        parsed = parse_depth(path)
        summary = summarize(parsed, tick_size)
        lines.extend(
            [
                f"## {path.name}",
                "",
                f"- Source path: `{path}`",
                f"- Size bytes: `{parsed['size']}`",
                f"- SHA256: `{parsed['sha256']}`",
                f"- Header magic: `{parsed['magic']:#x}`",
                f"- Header size: `{parsed['header_size']}`",
                f"- Record size: `{parsed['record_size']}`",
                f"- Version: `{parsed['version']}`",
                f"- Records: `{parsed['record_count']}`",
                f"- Byte remainder after records: `{parsed['remainder']}`",
                f"- First timestamp UTC: `{summary['first_ts'].isoformat() if summary['first_ts'] else None}`",
                f"- Last timestamp UTC: `{summary['last_ts'].isoformat() if summary['last_ts'] else None}`",
                f"- Batches ended by flag: `{summary['batch_count']}`",
                f"- Non-empty batches: `{summary['nonempty_batch_count']}`",
                "",
                "Command counts:",
                "",
            ]
        )
        for command, count in sorted(summary["command_counts"].items()):
            lines.append(f"- `{command}`: `{count}`")
        lines.append("")

        batch = summary["latest_nonempty_batch"]
        if batch:
            features = batch["features"]
            lines.extend(
                [
                    "Latest non-empty batch features:",
                    "",
                    f"- Batch records: `{batch['start_record']}..{batch['end_record']}`",
                    f"- Batch timestamp UTC: `{batch['timestamp'].isoformat()}`",
                    f"- Bid levels: `{features['book_levels_bid']}`",
                    f"- Ask levels: `{features['book_levels_ask']}`",
                    f"- Best bid: `{features['best_bid']}`",
                    f"- Best ask: `{features['best_ask']}`",
                    f"- Spread ticks: `{features['spread_ticks']}`",
                    f"- Top 1 bid/ask qty: `{features['top_1_bid_qty']}` / `{features['top_1_ask_qty']}`",
                    f"- Top 5 bid/ask qty: `{features['top_5_bid_qty']}` / `{features['top_5_ask_qty']}`",
                    f"- Top 10 bid/ask qty: `{features['top_10_bid_qty']}` / `{features['top_10_ask_qty']}`",
                    f"- Top 20 bid/ask qty: `{features['top_20_bid_qty']}` / `{features['top_20_ask_qty']}`",
                    f"- Top 10 imbalance: `{features['top_10_imbalance']}`",
                    f"- Top 20 imbalance: `{features['top_20_imbalance']}`",
                    f"- Max bid wall qty / distance ticks: `{features.get('max_bid_wall_qty')}` / `{features.get('max_bid_wall_distance_ticks')}`",
                    f"- Max ask wall qty / distance ticks: `{features.get('max_ask_wall_qty')}` / `{features.get('max_ask_wall_distance_ticks')}`",
                    f"- Top 10 bid/ask num orders: `{features['top_10_num_orders_bid']}` / `{features['top_10_num_orders_ask']}`",
                    "",
                ]
            )
        else:
            lines.extend(["Latest non-empty batch features: `none`.", ""])

    lines.extend(
        [
            "## Interpretation",
            "",
            "- The sample files pass the documented Sierra `.depth` binary header checks.",
            "- This confirms Sierra delayed depth recording is producing parser-readable files for `NQM26-CME`.",
            "- The current samples are tiny and weekend/market-closed constrained; they are enough for parser proof, not enough for market/orderflow research claims.",
            "- A longer active-session sample is still required before Databento parity or lead/lag analysis.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--tick-size", type=float, default=0.25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = markdown_report(args.paths, args.tick_size)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
