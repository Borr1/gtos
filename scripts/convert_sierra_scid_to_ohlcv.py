#!/usr/bin/env python3
"""Convert Sierra Chart .scid files into GTOS-compatible OHLCV CSV roots.

Research tooling only. This reads local Sierra Chart intraday files and writes
plain OHLCV CSV files plus a manifest that the Phase 3 replay tools can consume
through their existing --data-dir option. It does not interact with MT5, Sierra
Chart, brokers, live configuration, prompts, execution, or AI APIs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inspect_sierra_scid import (  # noqa: E402
    ScidRecord,
    iter_slice,
    parse_header,
    parse_utc,
    read_record,
)


SCHEMA_VERSION = "sierra_scid_to_gtos_ohlcv_root_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SUPPORTED_TIMEFRAMES = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "H1": timedelta(hours=1),
    "D1": timedelta(days=1),
}
INVALID_ABS_PRICE = 1.0e20


@dataclass(frozen=True)
class SymbolMapping:
    source_symbol: str
    file_symbol: str
    evidence_class: str
    price_transform: str = "identity"

    @property
    def source_file_name(self) -> str:
        return self.source_symbol if self.source_symbol.lower().endswith(".scid") else f"{self.source_symbol}.scid"


@dataclass
class OhlcvBucket:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    num_trades: int = 0
    bid_volume: int = 0
    ask_volume: int = 0
    source_records: int = 0

    def add(self, record: Mapping[str, float | int]) -> None:
        high = float(record["high"])
        low = float(record["low"])
        close = float(record["close"])
        self.high = max(self.high, high)
        self.low = min(self.low, low)
        self.close = close
        self.volume += float(record.get("volume") or 0.0)
        self.num_trades += int(record.get("num_trades") or 0)
        self.bid_volume += int(record.get("bid_volume") or 0)
        self.ask_volume += int(record.get("ask_volume") or 0)
        self.source_records += 1


@dataclass
class ConversionStats:
    raw_records_read: int = 0
    invalid_records_skipped: int = 0
    transformed_records: int = 0
    files: dict[str, dict[str, Any]] = field(default_factory=dict)


def parse_mapping(value: str) -> SymbolMapping:
    """Parse SOURCE=FILE_SYMBOL[:EVIDENCE_CLASS[:TRANSFORM]]."""

    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"mapping must look like SOURCE=FILE_SYMBOL[:EVIDENCE_CLASS[:TRANSFORM]], got {value!r}"
        )
    source, rest = value.split("=", 1)
    parts = rest.split(":")
    if not source.strip() or not parts[0].strip():
        raise argparse.ArgumentTypeError(f"mapping has empty source or file symbol: {value!r}")
    evidence = parts[1].strip() if len(parts) >= 2 and parts[1].strip() else "FUTURES_PROXY_TRANSFER"
    transform = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else "identity"
    if transform not in {"identity", "inverse"}:
        raise argparse.ArgumentTypeError(f"unsupported price transform {transform!r}")
    return SymbolMapping(
        source_symbol=source.strip(),
        file_symbol=parts[0].strip(),
        evidence_class=evidence,
        price_transform=transform,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid_price(value: float) -> bool:
    return math.isfinite(value) and abs(value) < INVALID_ABS_PRICE and value > 0.0


def transform_price(value: float, transform: str) -> float:
    if transform == "identity":
        return value
    if transform == "inverse":
        if value <= 0:
            raise ValueError("cannot invert non-positive price")
        return 1.0 / value
    raise ValueError(f"unsupported transform {transform!r}")


def normalize_record(record: ScidRecord, transform: str) -> dict[str, float | int] | None:
    close = record.close
    if not is_valid_price(close):
        return None
    open_ = record.open if is_valid_price(record.open) else close
    high = record.high if is_valid_price(record.high) else max(open_, close)
    low = record.low if is_valid_price(record.low) else min(open_, close)
    prices = [
        transform_price(float(open_), transform),
        transform_price(float(high), transform),
        transform_price(float(low), transform),
        transform_price(float(close), transform),
    ]
    if transform == "inverse":
        open_t, high_t, low_t, close_t = prices
        high_t, low_t = max(prices), min(prices)
    else:
        open_t, high_t, low_t, close_t = prices
        high_t, low_t = max(high_t, open_t, close_t), min(low_t, open_t, close_t)
    return {
        "open": open_t,
        "high": high_t,
        "low": low_t,
        "close": close_t,
        "volume": int(record.total_volume),
        "num_trades": int(record.num_trades),
        "bid_volume": int(record.bid_volume),
        "ask_volume": int(record.ask_volume),
    }


def floor_time(value: datetime, timeframe: str) -> datetime:
    dt = value.astimezone(timezone.utc)
    tf = timeframe.upper()
    if tf == "D1":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if tf == "H1":
        return dt.replace(minute=0, second=0, microsecond=0)
    if tf.startswith("M"):
        minutes = int(tf[1:])
        floored = (dt.minute // minutes) * minutes
        return dt.replace(minute=floored, second=0, microsecond=0)
    raise ValueError(f"unsupported timeframe {timeframe!r}")


def iter_records(path: Path, start: datetime | None, end: datetime | None) -> Iterable[ScidRecord]:
    header = parse_header(path)
    if header.record_count == 0:
        return
    if start is not None and end is not None:
        yield from iter_slice(path, start, end)
        return
    with path.open("rb") as handle:
        for idx in range(header.record_count):
            record = read_record(handle, header, idx)
            if start is not None and record.timestamp < start:
                continue
            if end is not None and record.timestamp >= end:
                break
            yield record


def aggregate_records(
    path: Path,
    *,
    mapping: SymbolMapping,
    timeframes: list[str],
    start: datetime | None,
    end: datetime | None,
) -> tuple[dict[str, list[OhlcvBucket]], ConversionStats]:
    buckets: dict[str, dict[datetime, OhlcvBucket]] = {tf: {} for tf in timeframes}
    stats = ConversionStats()
    for record in iter_records(path, start, end):
        stats.raw_records_read += 1
        normalized = normalize_record(record, mapping.price_transform)
        if normalized is None:
            stats.invalid_records_skipped += 1
            continue
        stats.transformed_records += 1
        for timeframe in timeframes:
            bucket_time = floor_time(record.timestamp, timeframe)
            by_time = buckets[timeframe]
            bucket = by_time.get(bucket_time)
            if bucket is None:
                bucket = OhlcvBucket(
                    time=bucket_time,
                    open=float(normalized["open"]),
                    high=float(normalized["high"]),
                    low=float(normalized["low"]),
                    close=float(normalized["close"]),
                    volume=float(normalized["volume"]),
                    num_trades=int(normalized["num_trades"]),
                    bid_volume=int(normalized["bid_volume"]),
                    ask_volume=int(normalized["ask_volume"]),
                    source_records=1,
                )
                by_time[bucket_time] = bucket
            else:
                bucket.add(normalized)
    return (
        {tf: [buckets[tf][key] for key in sorted(buckets[tf])] for tf in timeframes},
        stats,
    )


def format_ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def write_ohlcv_csv(path: Path, rows: list[OhlcvBucket]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "source_records",
                "num_trades",
                "bid_volume",
                "ask_volume",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "time": format_ts(row.time),
                    "open": f"{row.open:.10g}",
                    "high": f"{row.high:.10g}",
                    "low": f"{row.low:.10g}",
                    "close": f"{row.close:.10g}",
                    "volume": f"{row.volume:.10g}",
                    "source_records": row.source_records,
                    "num_trades": row.num_trades,
                    "bid_volume": row.bid_volume,
                    "ask_volume": row.ask_volume,
                }
            )


def gap_stats(rows: list[OhlcvBucket], timeframe: str) -> tuple[int, float | None]:
    if len(rows) < 2:
        return 0, None
    expected = SUPPORTED_TIMEFRAMES[timeframe]
    gaps: list[float] = []
    for previous, current in zip(rows, rows[1:]):
        delta = current.time - previous.time
        if delta > expected:
            gaps.append(delta.total_seconds())
    return len(gaps), max(gaps) if gaps else 0.0


def file_manifest(
    *,
    path: Path,
    rows: list[OhlcvBucket],
    mapping: SymbolMapping,
    timeframe: str,
    source_path: Path,
    source_sha256: str,
    stats: ConversionStats,
) -> dict[str, Any]:
    gap_count, max_gap_seconds = gap_stats(rows, timeframe)
    return {
        "path": str(path),
        "file_symbol": mapping.file_symbol,
        "mt5_symbol": mapping.source_symbol,
        "source_symbol": mapping.source_symbol,
        "source_system": "sierra_scid",
        "source_path": str(source_path),
        "source_sha256": source_sha256,
        "timeframe": timeframe,
        "rows": len(rows),
        "first": format_ts(rows[0].time) if rows else None,
        "last": format_ts(rows[-1].time) if rows else None,
        "gap_count": gap_count,
        "max_gap_seconds": max_gap_seconds,
        "raw_records_read": stats.raw_records_read,
        "invalid_records_skipped": stats.invalid_records_skipped,
        "transformed_records": stats.transformed_records,
        "evidence_class": mapping.evidence_class,
        "price_transform": mapping.price_transform,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def convert_batch(
    *,
    data_dir: Path,
    output_root: Path,
    batch_id: str,
    mappings: list[SymbolMapping],
    timeframes: list[str],
    start: datetime | None,
    end: datetime | None,
    notes: str | None = None,
) -> dict[str, Any]:
    batch_root = output_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "scope": "research/tooling only",
        "promotion_verdict": PROMOTION_VERDICT,
        "registered_before_outcomes_required": True,
        "source_system": "sierra_scid",
        "data_dir": str(data_dir),
        "output_root": str(batch_root),
        "start_utc": start.isoformat() if start else None,
        "end_utc": end.isoformat() if end else None,
        "timeframes": timeframes,
        "notes": notes,
        "symbols": [],
        "files": {},
        "errors": [],
    }
    for mapping in mappings:
        source_path = data_dir / mapping.source_file_name
        symbol_row = {
            "file_symbol": mapping.file_symbol,
            "mt5_symbol": mapping.source_symbol,
            "source_symbol": mapping.source_symbol,
            "source_path": str(source_path),
            "source_system": "sierra_scid",
            "evidence_class": mapping.evidence_class,
            "price_transform": mapping.price_transform,
        }
        manifest["symbols"].append(symbol_row)
        if not source_path.exists():
            manifest["errors"].append(
                {
                    "source_symbol": mapping.source_symbol,
                    "file_symbol": mapping.file_symbol,
                    "error": "source_scid_missing",
                    "path": str(source_path),
                }
            )
            continue
        try:
            source_sha = sha256_file(source_path)
            aggregated, stats = aggregate_records(
                source_path,
                mapping=mapping,
                timeframes=timeframes,
                start=start,
                end=end,
            )
        except Exception as exc:  # pragma: no cover - CLI manifest path
            manifest["errors"].append(
                {
                    "source_symbol": mapping.source_symbol,
                    "file_symbol": mapping.file_symbol,
                    "error": type(exc).__name__,
                    "detail": str(exc),
                    "path": str(source_path),
                }
            )
            continue
        for timeframe, rows in aggregated.items():
            out_path = batch_root / f"{mapping.file_symbol}_{timeframe}.csv"
            write_ohlcv_csv(out_path, rows)
            manifest["files"][f"{mapping.file_symbol}_{timeframe}"] = file_manifest(
                path=out_path,
                rows=rows,
                mapping=mapping,
                timeframe=timeframe,
                source_path=source_path,
                source_sha256=source_sha,
                stats=stats,
            )
    manifest_path = batch_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(r"C:\SierraChart\Data"))
    parser.add_argument("--output-root", type=Path, default=Path("data/sierra_ohlcv_roots"))
    parser.add_argument("--batch-id", required=True)
    parser.add_argument(
        "--mapping",
        action="append",
        type=parse_mapping,
        required=True,
        help="SOURCE=FILE_SYMBOL[:EVIDENCE_CLASS[:TRANSFORM]], e.g. NQM26-CME=NAS100:FUTURES_PROXY_TRANSFER",
    )
    parser.add_argument("--timeframe", action="append", dest="timeframes", default=[])
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--notes")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    timeframes = [str(tf).upper() for tf in (args.timeframes or ["M15", "H1", "D1"])]
    unsupported = [tf for tf in timeframes if tf not in SUPPORTED_TIMEFRAMES]
    if unsupported:
        raise ValueError(f"unsupported timeframes: {unsupported}")
    start = parse_utc(args.start) if args.start else None
    end = parse_utc(args.end) if args.end else None
    if start and end and end <= start:
        raise ValueError("--end must be after --start")
    manifest = convert_batch(
        data_dir=args.data_dir,
        output_root=args.output_root,
        batch_id=args.batch_id,
        mappings=args.mapping,
        timeframes=timeframes,
        start=start,
        end=end,
        notes=args.notes,
    )
    if args.quiet:
        print(
            json.dumps(
                {
                    "batch_id": manifest.get("batch_id"),
                    "manifest_path": manifest.get("manifest_path"),
                    "file_count": len(manifest.get("files") or {}),
                    "error_count": len(manifest.get("errors") or []),
                    "promotion_verdict": manifest.get("promotion_verdict"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
