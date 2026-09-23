#!/usr/bin/env python3
"""Inspect and export Sierra Chart .scid intraday files.

Research tooling only. This reads Sierra Chart intraday data files directly
from disk and does not interact with Sierra Chart, brokers, or trading logic.
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


HEADER_STRUCT = struct.Struct("<4sIIHHI36s")
RECORD_STRUCT = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
SPECIAL_OPEN_FIRST_SUB_TRADE = -1.99900095e37
SPECIAL_OPEN_LAST_SUB_TRADE = -1.99900197e37


@dataclass(frozen=True)
class ScidHeader:
    path: Path
    size_bytes: int
    magic: str
    header_size: int
    record_size: int
    version: int
    utc_start_index: int
    record_count: int
    remainder_bytes: int


@dataclass(frozen=True)
class ScidRecord:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    num_trades: int
    total_volume: int
    bid_volume: int
    ask_volume: int


def parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sierra_datetime(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def sierra_datetime_us(value: datetime) -> int:
    return int((value.astimezone(timezone.utc) - SIERRA_EPOCH).total_seconds() * 1_000_000)


def parse_header(path: Path) -> ScidHeader:
    size = path.stat().st_size
    with path.open("rb") as handle:
        raw = handle.read(HEADER_STRUCT.size)
    if len(raw) < HEADER_STRUCT.size:
        raise ValueError(f"{path} is too small for a Sierra SCID header")
    magic_raw, header_size, record_size, version, _unused1, utc_start_index, _reserve = (
        HEADER_STRUCT.unpack(raw)
    )
    magic = magic_raw.decode("ascii", errors="replace")
    if magic_raw != b"SCID":
        raise ValueError(f"{path} has invalid SCID magic {magic!r}")
    if header_size < HEADER_STRUCT.size:
        raise ValueError(f"{path} has invalid header size {header_size}")
    if record_size != RECORD_STRUCT.size:
        raise ValueError(
            f"{path} has record size {record_size}, expected {RECORD_STRUCT.size}"
        )
    if size < header_size:
        raise ValueError(f"{path} is smaller than declared header size {header_size}")
    payload = size - header_size
    return ScidHeader(
        path=path,
        size_bytes=size,
        magic=magic,
        header_size=header_size,
        record_size=record_size,
        version=version,
        utc_start_index=utc_start_index,
        record_count=payload // record_size,
        remainder_bytes=payload % record_size,
    )


def read_record(handle: Any, header: ScidHeader, index: int) -> ScidRecord:
    if index < 0 or index >= header.record_count:
        raise IndexError(index)
    handle.seek(header.header_size + index * header.record_size)
    raw = handle.read(header.record_size)
    if len(raw) != header.record_size:
        raise ValueError(f"short record read at index {index} from {header.path}")
    dt_us, open_, high, low, close, num_trades, total_volume, bid_volume, ask_volume = (
        RECORD_STRUCT.unpack(raw)
    )
    return ScidRecord(
        timestamp=sierra_datetime(dt_us),
        open=float(open_),
        high=float(high),
        low=float(low),
        close=float(close),
        num_trades=int(num_trades),
        total_volume=int(total_volume),
        bid_volume=int(bid_volume),
        ask_volume=int(ask_volume),
    )


def find_index(handle: Any, header: ScidHeader, target_us: int, *, left: bool) -> int:
    lo = 0
    hi = header.record_count
    while lo < hi:
        mid = (lo + hi) // 2
        record = read_record(handle, header, mid)
        record_us = sierra_datetime_us(record.timestamp)
        if record_us < target_us or (not left and record_us == target_us):
            lo = mid + 1
        else:
            hi = mid
    return lo


def summarize_file(path: Path) -> dict[str, Any]:
    header = parse_header(path)
    summary: dict[str, Any] = {
        "file": path.name,
        "path": str(path),
        "size_bytes": header.size_bytes,
        "magic": header.magic,
        "header_size": header.header_size,
        "record_size": header.record_size,
        "version": header.version,
        "utc_start_index": header.utc_start_index,
        "records": header.record_count,
        "remainder_bytes": header.remainder_bytes,
    }
    if header.record_count == 0:
        return summary
    with path.open("rb") as handle:
        first = read_record(handle, header, 0)
        last = read_record(handle, header, header.record_count - 1)
    summary.update(
        {
            "first_timestamp_utc": first.timestamp.isoformat(),
            "last_timestamp_utc": last.timestamp.isoformat(),
            "first_close": first.close,
            "last_close": last.close,
            "last_total_volume": last.total_volume,
            "last_bid_volume": last.bid_volume,
            "last_ask_volume": last.ask_volume,
        }
    )
    return summary


def iter_slice(path: Path, start: datetime, end: datetime) -> Iterable[ScidRecord]:
    if end <= start:
        raise ValueError("end must be after start")
    header = parse_header(path)
    if header.record_count == 0:
        return
    start_us = sierra_datetime_us(start)
    end_us = sierra_datetime_us(end)
    with path.open("rb") as handle:
        index = find_index(handle, header, start_us, left=True)
        while index < header.record_count:
            record = read_record(handle, header, index)
            if sierra_datetime_us(record.timestamp) >= end_us:
                break
            yield record
            index += 1


def export_slice_to_csv(path: Path, start: datetime, end: datetime, out: Path) -> dict[str, Any]:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    total_volume = 0
    bid_volume = 0
    ask_volume = 0
    num_trades = 0
    first_ts: str | None = None
    last_ts: str | None = None
    first_close: float | None = None
    last_close: float | None = None
    min_close: float | None = None
    max_close: float | None = None
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "timestamp_utc",
                "open",
                "high",
                "low",
                "close",
                "num_trades",
                "total_volume",
                "bid_volume",
                "ask_volume",
            ]
        )
        for record in iter_slice(path, start, end):
            timestamp = record.timestamp.isoformat()
            writer.writerow(
                [
                    timestamp,
                    record.open,
                    record.high,
                    record.low,
                    record.close,
                    record.num_trades,
                    record.total_volume,
                    record.bid_volume,
                    record.ask_volume,
                ]
            )
            rows += 1
            total_volume += record.total_volume
            bid_volume += record.bid_volume
            ask_volume += record.ask_volume
            num_trades += record.num_trades
            first_ts = first_ts or timestamp
            last_ts = timestamp
            first_close = record.close if first_close is None else first_close
            last_close = record.close
            min_close = record.close if min_close is None else min(min_close, record.close)
            max_close = record.close if max_close is None else max(max_close, record.close)
    return {
        "source_path": str(path),
        "output_path": str(out),
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "rows": rows,
        "first_timestamp_utc": first_ts,
        "last_timestamp_utc": last_ts,
        "first_close": first_close,
        "last_close": last_close,
        "min_close": min_close,
        "max_close": max_close,
        "sum_num_trades": num_trades,
        "sum_total_volume": total_volume,
        "sum_bid_volume": bid_volume,
        "sum_ask_volume": ask_volume,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=r"C:\SierraChart\Data")
    parser.add_argument("--pattern", default="*.scid")
    parser.add_argument("--inventory-json", type=Path)
    parser.add_argument("--export-file", type=Path)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--export-csv", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload: dict[str, Any] = {
        "schema_version": "sierra_scid_probe_v1",
        "data_dir": str(args.data_dir),
    }

    data_dir = Path(args.data_dir)
    files = sorted(data_dir.glob(args.pattern), key=lambda p: p.name.lower())
    payload["inventory"] = [summarize_file(path) for path in files]

    if args.inventory_json:
        args.inventory_json.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_json.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        payload["inventory_json"] = str(args.inventory_json)

    if args.export_file or args.export_csv or args.start or args.end:
        if not (args.export_file and args.export_csv and args.start and args.end):
            raise ValueError(
                "--export-file, --start, --end, and --export-csv are required together"
            )
        payload["export"] = export_slice_to_csv(
            path=args.export_file,
            start=parse_utc(args.start),
            end=parse_utc(args.end),
            out=args.export_csv,
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
