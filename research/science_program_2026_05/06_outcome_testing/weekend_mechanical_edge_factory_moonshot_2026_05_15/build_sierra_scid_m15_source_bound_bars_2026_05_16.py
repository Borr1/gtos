#!/usr/bin/env python3
"""Build source-bound M15 bars from every audited Sierra SCID file.

This packet uses the Sierra parser/timestamp repair output as its source
contract. It reads only the ledger-prefix record range for each SCID file,
handles non-monotonic source records by stable timestamp/index ordering inside
each M15 bucket, and emits bars plus gap/source-audit ledgers. It does not
create strategy validation, outcomes, R/PnL, live-readiness, or promotion.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np
import pandas as pd


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.inspect_sierra_scid import (  # noqa: E402
    RECORD_STRUCT,
    SIERRA_EPOCH,
    SPECIAL_OPEN_FIRST_SUB_TRADE,
    SPECIAL_OPEN_LAST_SUB_TRADE,
    parse_header,
)


SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

PARSER_AUDIT_LEDGER = ROUTE_DIR / f"SIERRA_PARSER_AUDIT_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_BAR_PACKET_RESULT_{STAMP}.json"
BAR_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_BAR_LEDGER_{STAMP}.jsonl"
SOURCE_AUDIT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_AUDIT_LEDGER_{STAMP}.jsonl"
GAP_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_GAP_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_BAR_PACKET_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra SCID source-bound M15 bar construction only; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

M15_US = 15 * 60 * 1_000_000
INVALID_ABS_PRICE = 1.0e20
CHUNK_RECORDS = 250_000
SCID_DTYPE = np.dtype(
    [
        ("dt_us", "<u8"),
        ("open", "<f4"),
        ("high", "<f4"),
        ("low", "<f4"),
        ("close", "<f4"),
        ("num_trades", "<u4"),
        ("total_volume", "<u4"),
        ("bid_volume", "<u4"),
        ("ask_volume", "<u4"),
    ]
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sierra_us_to_dt(us: int) -> datetime:
    return SIERRA_EPOCH + timedelta(microseconds=int(us))


def iso_us(us: int | None) -> str | None:
    if us is None:
        return None
    return sierra_us_to_dt(us).astimezone(UTC).isoformat().replace("+00:00", "Z")


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


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def safe_price(value: float) -> float | None:
    if not math.isfinite(value):
        return None
    if abs(value) >= INVALID_ABS_PRICE:
        return None
    if value in (SPECIAL_OPEN_FIRST_SUB_TRADE, SPECIAL_OPEN_LAST_SUB_TRADE):
        return None
    if value <= 0.0:
        return None
    return float(value)


def normalize_prices(open_: float, high: float, low: float, close: float) -> tuple[float, float, float, float] | None:
    close_v = safe_price(close)
    if close_v is None:
        return None
    open_v = safe_price(open_) or close_v
    high_v = safe_price(high)
    low_v = safe_price(low)
    if high_v is None:
        high_v = max(open_v, close_v)
    if low_v is None:
        low_v = min(open_v, close_v)
    return open_v, max(high_v, open_v, close_v), min(low_v, open_v, close_v), close_v


def empty_bucket(bucket_us: int) -> dict[str, Any]:
    return {
        "bucket_us": bucket_us,
        "open": None,
        "high": None,
        "low": None,
        "close": None,
        "volume": 0,
        "num_trades": 0,
        "bid_volume": 0,
        "ask_volume": 0,
        "source_records": 0,
        "first_key": None,
        "last_key": None,
        "first_source_timestamp_us": None,
        "last_source_timestamp_us": None,
        "first_source_record_index": None,
        "last_source_record_index": None,
    }


def add_record(
    bucket: dict[str, Any],
    *,
    record_index: int,
    dt_us: int,
    prices: tuple[float, float, float, float],
    num_trades: int,
    total_volume: int,
    bid_volume: int,
    ask_volume: int,
) -> None:
    open_v, high_v, low_v, close_v = prices
    key = (dt_us, record_index)
    if bucket["first_key"] is None or key < bucket["first_key"]:
        bucket["first_key"] = key
        bucket["open"] = open_v
        bucket["first_source_timestamp_us"] = dt_us
        bucket["first_source_record_index"] = record_index
    if bucket["last_key"] is None or key >= bucket["last_key"]:
        bucket["last_key"] = key
        bucket["close"] = close_v
        bucket["last_source_timestamp_us"] = dt_us
        bucket["last_source_record_index"] = record_index
    bucket["high"] = high_v if bucket["high"] is None else max(bucket["high"], high_v)
    bucket["low"] = low_v if bucket["low"] is None else min(bucket["low"], low_v)
    bucket["volume"] += int(total_volume)
    bucket["num_trades"] += int(num_trades)
    bucket["bid_volume"] += int(bid_volume)
    bucket["ask_volume"] += int(ask_volume)
    bucket["source_records"] += 1


def merge_aggregate_row(buckets: dict[int, dict[str, Any]], row: Any) -> None:
    bucket_us = int(row.bucket_us)
    bucket = buckets.get(bucket_us)
    if bucket is None:
        bucket = empty_bucket(bucket_us)
        buckets[bucket_us] = bucket
    first_key = (int(row.first_source_timestamp_us), int(row.first_source_record_index))
    last_key = (int(row.last_source_timestamp_us), int(row.last_source_record_index))
    if bucket["first_key"] is None or first_key < bucket["first_key"]:
        bucket["first_key"] = first_key
        bucket["open"] = float(row.open)
        bucket["first_source_timestamp_us"] = first_key[0]
        bucket["first_source_record_index"] = first_key[1]
    if bucket["last_key"] is None or last_key >= bucket["last_key"]:
        bucket["last_key"] = last_key
        bucket["close"] = float(row.close)
        bucket["last_source_timestamp_us"] = last_key[0]
        bucket["last_source_record_index"] = last_key[1]
    bucket["high"] = float(row.high) if bucket["high"] is None else max(float(bucket["high"]), float(row.high))
    bucket["low"] = float(row.low) if bucket["low"] is None else min(float(bucket["low"]), float(row.low))
    bucket["volume"] += int(row.volume)
    bucket["num_trades"] += int(row.num_trades)
    bucket["bid_volume"] += int(row.bid_volume)
    bucket["ask_volume"] += int(row.ask_volume)
    bucket["source_records"] += int(row.source_records)


def process_chunk(
    raw: bytes,
    *,
    start_index: int,
    buckets: dict[int, dict[str, Any]],
) -> tuple[int, int, int | None, int | None, int, int | None, int | None]:
    usable = len(raw) - (len(raw) % RECORD_STRUCT.size)
    if usable <= 0:
        return 0, 0, None, None, 0, None, None
    array = np.frombuffer(raw[:usable], dtype=SCID_DTYPE)
    if array.size == 0:
        return 0, 0, None, None, 0, None, None
    dt_us = array["dt_us"].astype(np.int64, copy=False)
    first_dt_us = int(dt_us[0])
    last_dt_us = int(dt_us[-1])
    close = array["close"].astype(np.float64, copy=False)
    valid_close = np.isfinite(close) & (np.abs(close) < INVALID_ABS_PRICE) & (close > 0.0)
    raw_count = int(array.size)
    invalid_count = int(raw_count - int(valid_close.sum()))
    if not valid_close.any():
        return (
            raw_count,
            invalid_count,
            int(dt_us.min()),
            int(dt_us.max()),
            int(np.sum(dt_us[1:] < dt_us[:-1])),
            first_dt_us,
            last_dt_us,
        )

    idx = np.arange(start_index, start_index + raw_count, dtype=np.int64)[valid_close]
    dt_valid = dt_us[valid_close]
    open_raw = array["open"].astype(np.float64, copy=False)[valid_close]
    high_raw = array["high"].astype(np.float64, copy=False)[valid_close]
    low_raw = array["low"].astype(np.float64, copy=False)[valid_close]
    close_valid = close[valid_close]
    valid_open = (
        np.isfinite(open_raw)
        & (np.abs(open_raw) < INVALID_ABS_PRICE)
        & (open_raw > 0.0)
        & (open_raw != SPECIAL_OPEN_FIRST_SUB_TRADE)
        & (open_raw != SPECIAL_OPEN_LAST_SUB_TRADE)
    )
    open_v = np.where(valid_open, open_raw, close_valid)
    valid_high = np.isfinite(high_raw) & (np.abs(high_raw) < INVALID_ABS_PRICE) & (high_raw > 0.0)
    high_v = np.where(valid_high, high_raw, np.maximum(open_v, close_valid))
    valid_low = np.isfinite(low_raw) & (np.abs(low_raw) < INVALID_ABS_PRICE) & (low_raw > 0.0)
    low_v = np.where(valid_low, low_raw, np.minimum(open_v, close_valid))
    high_v = np.maximum.reduce([high_v, open_v, close_valid])
    low_v = np.minimum.reduce([low_v, open_v, close_valid])
    df = pd.DataFrame(
        {
            "bucket_us": (dt_valid // M15_US) * M15_US,
            "dt_us": dt_valid,
            "record_index": idx,
            "open": open_v,
            "high": high_v,
            "low": low_v,
            "close": close_valid,
            "volume": array["total_volume"].astype(np.int64, copy=False)[valid_close],
            "num_trades": array["num_trades"].astype(np.int64, copy=False)[valid_close],
            "bid_volume": array["bid_volume"].astype(np.int64, copy=False)[valid_close],
            "ask_volume": array["ask_volume"].astype(np.int64, copy=False)[valid_close],
        }
    )
    df.sort_values(["bucket_us", "dt_us", "record_index"], kind="mergesort", inplace=True)
    grouped = df.groupby("bucket_us", sort=True, as_index=False).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        num_trades=("num_trades", "sum"),
        bid_volume=("bid_volume", "sum"),
        ask_volume=("ask_volume", "sum"),
        source_records=("dt_us", "count"),
        first_source_timestamp_us=("dt_us", "first"),
        last_source_timestamp_us=("dt_us", "last"),
        first_source_record_index=("record_index", "first"),
        last_source_record_index=("record_index", "last"),
    )
    for aggregate_row in grouped.itertuples(index=False):
        merge_aggregate_row(buckets, aggregate_row)
    nonmonotonic_pairs = int(np.sum(dt_us[1:] < dt_us[:-1]))
    return raw_count, invalid_count, int(dt_us.min()), int(dt_us.max()), nonmonotonic_pairs, first_dt_us, last_dt_us


def aggregate_file(row: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    path = Path(row["path"])
    header = parse_header(path)
    ledger_record_count = int(row.get("ledger_record_count") or 0)
    buckets: dict[int, dict[str, Any]] = {}
    invalid_records = 0
    raw_records = 0
    timestamp_nonmonotonic_pairs = 0
    previous_dt_us: int | None = None
    first_source_timestamp_us: int | None = None
    last_source_timestamp_us: int | None = None

    usable_records = min(int(ledger_record_count), int(header.record_count))
    emitted = 0
    with path.open("rb") as handle:
        handle.seek(header.header_size)
        while emitted < usable_records:
            to_read_records = min(CHUNK_RECORDS, usable_records - emitted)
            raw = handle.read(to_read_records * RECORD_STRUCT.size)
            if not raw:
                break
            (
                chunk_records,
                chunk_invalid,
                chunk_min_us,
                chunk_max_us,
                chunk_nonmonotonic,
                chunk_first_us,
                chunk_last_us,
            ) = process_chunk(
                raw,
                start_index=emitted,
                buckets=buckets,
            )
            if chunk_records <= 0:
                break
            if previous_dt_us is not None and chunk_first_us is not None and chunk_first_us < previous_dt_us:
                timestamp_nonmonotonic_pairs += 1
            timestamp_nonmonotonic_pairs += chunk_nonmonotonic
            raw_records += chunk_records
            invalid_records += chunk_invalid
            if chunk_min_us is not None:
                first_source_timestamp_us = (
                    chunk_min_us
                    if first_source_timestamp_us is None
                    else min(first_source_timestamp_us, chunk_min_us)
                )
            if chunk_max_us is not None:
                last_source_timestamp_us = (
                    chunk_max_us
                    if last_source_timestamp_us is None
                    else max(last_source_timestamp_us, chunk_max_us)
                )
            if chunk_last_us is not None:
                previous_dt_us = chunk_last_us
            emitted += chunk_records

    source_symbol = str(row.get("symbol_hint") or path.stem)
    bar_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    sorted_buckets = [buckets[key] for key in sorted(buckets)]
    previous_bucket_us: int | None = None
    for sequence, bucket in enumerate(sorted_buckets):
        bucket_us = int(bucket["bucket_us"])
        if previous_bucket_us is not None and bucket_us - previous_bucket_us > M15_US:
            gap_seconds = (bucket_us - previous_bucket_us) / 1_000_000
            gap_rows.append(
                {
                    "route_id": ROUTE_ID,
                    "source_symbol": source_symbol,
                    "path": str(path),
                    "previous_bar_start_utc": iso_us(previous_bucket_us),
                    "next_bar_start_utc": iso_us(bucket_us),
                    "gap_seconds": gap_seconds,
                    "missing_m15_bars": int((bucket_us - previous_bucket_us) // M15_US) - 1,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )
        previous_bucket_us = bucket_us
        bar_rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": source_symbol,
                "bar_sequence": sequence,
                "bar_start_utc": iso_us(bucket_us),
                "bar_end_exclusive_utc": iso_us(bucket_us + M15_US),
                "open": bucket["open"],
                "high": bucket["high"],
                "low": bucket["low"],
                "close": bucket["close"],
                "volume": bucket["volume"],
                "num_trades": bucket["num_trades"],
                "bid_volume": bucket["bid_volume"],
                "ask_volume": bucket["ask_volume"],
                "source_records": bucket["source_records"],
                "first_source_timestamp_utc": iso_us(bucket["first_source_timestamp_us"]),
                "last_source_timestamp_utc": iso_us(bucket["last_source_timestamp_us"]),
                "first_source_record_index": bucket["first_source_record_index"],
                "last_source_record_index": bucket["last_source_record_index"],
                "bar_sort_policy": "stable_by_source_timestamp_us_then_source_record_index",
                "source_audit_key": f"{source_symbol}|{ledger_record_count}|{row.get('combined_segment_sha256')}",
            }
        )

    transformed_records = raw_records - invalid_records
    audit = {
        "route_id": ROUTE_ID,
        "source_symbol": source_symbol,
        "path": str(path),
        "parser_status": row.get("parser_status"),
        "ledger_record_count": ledger_record_count,
        "current_record_count": row.get("current_record_count"),
        "raw_records_read": raw_records,
        "transformed_records": transformed_records,
        "invalid_records_skipped": invalid_records,
        "bar_rows": len(bar_rows),
        "gap_rows": len(gap_rows),
        "timestamp_nonmonotonic_pairs": timestamp_nonmonotonic_pairs,
        "first_source_timestamp_utc": iso_us(first_source_timestamp_us),
        "last_source_timestamp_utc": iso_us(last_source_timestamp_us),
        "first_bar_start_utc": bar_rows[0]["bar_start_utc"] if bar_rows else None,
        "last_bar_start_utc": bar_rows[-1]["bar_start_utc"] if bar_rows else None,
        "byte_delta_current_minus_ledger": row.get("byte_delta_current_minus_ledger"),
        "mutable_status": row.get("mutable_status"),
        "combined_segment_sha256": row.get("combined_segment_sha256"),
        "source_status": "SCID_M15_BARS_BUILT",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
    }
    question_rows = build_question_rows(audit)
    return bar_rows, audit, gap_rows, question_rows


def build_question_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "route_id": ROUTE_ID,
            "source_symbol": audit["source_symbol"],
            "question": "Do source-bound Sierra M15 bars reproduce the same primitive signals as MT5/tick-derived bars on matched markets?",
            "next_action": "Run matched primitive factory on these bars and compare against existing Route C and historical OHLC ledgers.",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "route_id": ROUTE_ID,
            "source_symbol": audit["source_symbol"],
            "question": "Do non-monotonic source records materially change open/close if file order is used instead of stable timestamp/index order?",
            "next_action": "Build a file-order-vs-timestamp-order delta audit for any source with timestamp_nonmonotonic_pairs > 0.",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        },
    ]
    if int(audit.get("gap_rows") or 0) > 0:
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": audit["source_symbol"],
                "question": "Which session/calendar gaps are exchange schedule versus source capture holes?",
                "next_action": "Classify every emitted gap by exchange session calendar or route it to source-capture repair.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    if audit.get("mutable_status") != "UNCHANGED_SIZE_FROM_SOURCE_LEDGER":
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": audit["source_symbol"],
                "question": "Can appended current-tail records extend the same SCID primitive packet without contaminating the ledger-prefix sealed state?",
                "next_action": "Build a separate current-tail extension packet with its own byte-range freeze and no mixed sealed-prefix claim.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_scid_m15_source_bound_bar_builder", "created"),
        (RESULT_PATH, "sierra_scid_m15_source_bound_bar_packet_result", "created"),
        (BAR_LEDGER, "sierra_scid_m15_source_bound_bar_ledger", "created"),
        (SOURCE_AUDIT_LEDGER, "sierra_scid_m15_source_bound_audit_ledger", "created"),
        (GAP_LEDGER, "sierra_scid_m15_source_bound_gap_ledger", "created"),
        (QUESTION_LEDGER, "sierra_scid_m15_source_bound_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_scid_m15_source_bound_bar_packet_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], source_status_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_scid_m15_source_bound_bars",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": (
            "Built source-bound M15 bars from every audited SCID file using ledger-prefix record counts, "
            "accepted Sierra timestamp/as-of policy, and stable timestamp/index ordering."
        ),
        "counts": counts,
        "source_status_counts": source_status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(BAR_LEDGER),
            relative(SOURCE_AUDIT_LEDGER),
            relative(GAP_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(
    generated_utc: str,
    counts: dict[str, int],
    parser_status_counts: dict[str, int],
    mutable_status_counts: dict[str, int],
) -> None:
    lines = [
        "# Sierra SCID M15 Source-Bound Bar Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-bound bar construction only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Parser Status Counts", ""])
    for key, value in sorted(parser_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Mutable Status Counts", ""])
    for key, value in sorted(mutable_status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- Run a Sierra M15 primitive factory over this bar ledger.",
            "- Compare Sierra futures proxy primitives against existing tick/MT5 Route C primitives on same sessions and horizons.",
            "- Split exchange-calendar gaps from source-capture gaps before any completeness claim.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    audit_rows = [
        row
        for row in read_jsonl(PARSER_AUDIT_LEDGER)
        if row.get("extension") == ".scid" and str(row.get("parser_status", "")).startswith("SCID_PARSER_OK")
    ]
    source_audit_rows: list[dict[str, Any]] = []
    gap_rows_all: list[dict[str, Any]] = []
    question_rows_all: list[dict[str, Any]] = []
    total_bar_rows = 0
    total_raw_records = 0
    total_invalid_records = 0
    total_nonmonotonic_pairs = 0

    with BAR_LEDGER.open("w", encoding="utf-8") as bar_handle:
        for row in sorted(audit_rows, key=lambda item: str(item.get("symbol_hint") or item.get("path"))):
            bar_rows, source_audit, gap_rows, question_rows = aggregate_file(row)
            for bar in bar_rows:
                append_jsonl(bar_handle, bar)
            source_audit_rows.append(source_audit)
            gap_rows_all.extend(gap_rows)
            question_rows_all.extend(question_rows)
            total_bar_rows += len(bar_rows)
            total_raw_records += int(source_audit["raw_records_read"])
            total_invalid_records += int(source_audit["invalid_records_skipped"])
            total_nonmonotonic_pairs += int(source_audit["timestamp_nonmonotonic_pairs"])

    write_jsonl(SOURCE_AUDIT_LEDGER, source_audit_rows)
    write_jsonl(GAP_LEDGER, gap_rows_all)
    write_jsonl(QUESTION_LEDGER, question_rows_all)

    parser_status_counts = Counter(str(row.get("parser_status") or "missing") for row in source_audit_rows)
    mutable_status_counts = Counter(str(row.get("mutable_status") or "missing") for row in source_audit_rows)
    counts = {
        "scid_input_files": len(audit_rows),
        "source_audit_rows": len(source_audit_rows),
        "m15_bar_rows": total_bar_rows,
        "gap_rows": len(gap_rows_all),
        "question_rows": len(question_rows_all),
        "raw_records_read": total_raw_records,
        "invalid_records_skipped": total_invalid_records,
        "timestamp_nonmonotonic_pairs": total_nonmonotonic_pairs,
        "mutable_size_files": sum(
            count
            for status, count in mutable_status_counts.items()
            if status != "UNCHANGED_SIZE_FROM_SOURCE_LEDGER"
        ),
    }
    result = {
        "schema": "sierra_scid_m15_source_bound_bar_packet_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SCID_M15_SOURCE_BOUND_BAR_CONSTRUCTION_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "parser_status_counts": dict(sorted(parser_status_counts.items())),
        "mutable_status_counts": dict(sorted(mutable_status_counts.items())),
        "bar_construction_policy": {
            "bar_interval": "M15 UTC wall-clock boundaries",
            "bar_membership": "left_closed_right_open",
            "open_close_order": "stable_by_source_timestamp_us_then_source_record_index",
            "source_byte_range": "ledger_prefix_records_only_from_SIERRA_PARSER_AUDIT_LEDGER",
        },
        "next_same_resource_work": [
            "run primitive factory over source-bound Sierra M15 bar ledger",
            "classify all emitted gaps into exchange calendar versus source-capture gaps",
            "compare Sierra futures proxy primitives against Route C tick primitives on same session/horizon families",
            "build current-tail extension packet separately for mutable SCID files",
        ],
        "not_completion": "This materializes a Sierra bar substrate; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(generated_utc, counts, dict(parser_status_counts), dict(mutable_status_counts))
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(parser_status_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
