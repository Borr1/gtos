#!/usr/bin/env python3
"""Session CI follow-through: replace unlike candle-volume sums with raw provider tick counts.

The first CI-3 comparison was fixed and run before this repair existed.  It passed price, session,
gap and value-area conditions, but failed the decision-relevant POC p95 condition on both symbols.
The official Dukascopy ``IBar`` contract explains why the input was unlike: candle volume is the
sum of best-price volumes across ticks, whereas the FTMO/MT5 feed supplies a tick count.

This is a semantic repair, not a calibrated transformation.  It downloads Dukascopy's raw public
ticks, counts records per UTC minute, and substitutes that provider-local tick count into the
already-bound BID candle OHLC.  It fits no parameter and preserves CI's original structural rule
byte-for-byte.  The repaired source remains third-party and cannot pass merely because prices do.

Commands (hard cap: two download workers)::

    python3 .../ci_tick_count_repair.py fetch
    python3 .../ci_tick_count_repair.py convert
    python3 .../ci_tick_count_repair.py validate

The default span is the independent broker-overlap window only.  A full 2024+ tick fetch is allowed
only after this no-fit repair clears the unchanged overlap rule; a failed repair stops CI-4.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import lzma
import math
import os
import struct
import sys
import time
import urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Mapping, Sequence

import requests


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ci_thirdparty_m1 as base  # noqa: E402


DATA_ROOT = base.DATA_ROOT
BROKER_ROOT = base.BROKER_ROOT
RECEIPT_ROOT = HERE
FETCH_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_FETCH_OVERLAP_V1.json"
CONVERT_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_SOURCE_OVERLAP_V1.json"
VALIDATE_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_REPAIR_OVERLAP_V1.json"
ORIGINAL_OVERLAP = RECEIPT_ROOT / "CI_THIRD_PARTY_OVERLAP_V1.json"
ITICK_URL = "https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/ITick.html"
DEFAULT_START = dt.date(2026, 4, 26)
DEFAULT_END = dt.date(2026, 7, 30)
TICK_RECORD = struct.Struct(">3i2f")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")


def _days(start: dt.date, end: dt.date):
    if end < start:
        raise ValueError(f"reversed span: {start}..{end}")
    for offset in range((end - start).days + 1):
        yield start + dt.timedelta(days=offset)


def tick_url(inst: base.Instrument, day: dt.date, hour: int) -> str:
    if not 0 <= hour <= 23:
        raise ValueError(f"invalid UTC hour: {hour}")
    return (
        f"{base.DATAFEED}/{inst.code}/{day.year}/{day.month - 1:02d}/{day.day:02d}/"
        f"{hour:02d}h_ticks.bi5"
    )


def tick_path(inst: base.Instrument, day: dt.date, hour: int,
              root: Path = DATA_ROOT) -> Path:
    return (
        root / "raw_ticks" / inst.code / f"{day.year}" / f"{day.month:02d}"
        / f"{day.day:02d}" / f"{hour:02d}.bi5"
    )


def repaired_path(inst: base.Instrument, root: Path = DATA_ROOT) -> Path:
    return root / "repair_tick_count_overlap" / f"{inst.canonical}_M1_TICKCOUNT.csv.gz"


def decode_ticks(payload: bytes, *, label: str = "") -> list[tuple[int, int, int, float, float]]:
    """Decode one public hourly tick payload and validate its monotone UTC-hour offsets."""
    if not payload:
        return []
    try:
        raw = lzma.decompress(payload)
    except lzma.LZMAError as exc:
        raise ValueError(f"{label}: payload is not valid LZMA/bi5") from exc
    if len(raw) % TICK_RECORD.size:
        raise ValueError(
            f"{label}: decoded byte count {len(raw)} is not a multiple of {TICK_RECORD.size}"
        )
    out: list[tuple[int, int, int, float, float]] = []
    previous = -1
    for offset in range(0, len(raw), TICK_RECORD.size):
        millis, ask_i, bid_i, ask_volume, bid_volume = TICK_RECORD.unpack_from(raw, offset)
        if millis < 0 or millis >= 3_600_000 or millis < previous:
            raise ValueError(f"{label}: invalid/non-monotone millisecond offset {millis}")
        previous = millis
        if ask_i <= 0 or bid_i <= 0 or ask_i < bid_i:
            raise ValueError(f"{label}: invalid bid/ask integers {bid_i}/{ask_i}")
        if not all(math.isfinite(v) and v >= 0 for v in (ask_volume, bid_volume)):
            raise ValueError(f"{label}: invalid best-price volume")
        out.append((millis, ask_i, bid_i, float(ask_volume), float(bid_volume)))
    return out


def _fetch_one(item: tuple[base.Instrument, dt.date, int], root: Path) -> dict:
    inst, day, hour = item
    path = tick_path(inst, day, hour, root)
    url = tick_url(inst, day, hour)
    if path.is_file():
        payload = path.read_bytes()
        ticks = decode_ticks(payload, label=f"{inst.code} {day} {hour:02d}")
        return {
            "instrument": inst.canonical,
            "source_code": inst.code,
            "day": day.isoformat(),
            "hour_utc": hour,
            "url": url,
            "status": "present_validated",
            "bytes": len(payload),
            "ticks": len(ticks),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    last_error = ""
    for attempt in range(1, 4):
        try:
            payload, headers = base._http_get(url, timeout=45.0)
            ticks = decode_ticks(payload, label=f"{inst.code} {day} {hour:02d}")
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(path.suffix + f".part.{os.getpid()}")
            temp.write_bytes(payload)
            temp.replace(path)
            return {
                "instrument": inst.canonical,
                "source_code": inst.code,
                "day": day.isoformat(),
                "hour_utc": hour,
                "url": url,
                "status": "downloaded_validated",
                "http_last_modified": headers.get("Last-Modified"),
                "http_etag": headers.get("ETag"),
                "bytes": len(payload),
                "ticks": len(ticks),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {
                    "instrument": inst.canonical,
                    "source_code": inst.code,
                    "day": day.isoformat(),
                    "hour_utc": hour,
                    "url": url,
                    "status": "source_404_no_ticks",
                    "http_status": 404,
                    "ticks": 0,
                }
            last_error = f"HTTP {exc.code}: {exc.reason}"
        except (OSError, TimeoutError, ValueError, requests.RequestException) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < 3:
            time.sleep(0.5 * attempt)
    return {
        "instrument": inst.canonical,
        "source_code": inst.code,
        "day": day.isoformat(),
        "hour_utc": hour,
        "url": url,
        "status": "error",
        "error": last_error,
    }


def fetch_ticks(*, start: dt.date = DEFAULT_START, end: dt.date = DEFAULT_END,
                workers: int = 2, root: Path = DATA_ROOT) -> dict:
    if workers not in (1, 2):
        raise SystemExit("--workers must be 1 or 2")
    doc_path = root / "raw" / "source_docs" / "dukascopy_itick_semantics.html"
    if not doc_path.is_file():
        payload, _headers = base._http_get(ITICK_URL)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_bytes(payload)
    items = [
        (inst, day, hour)
        for inst in base.INSTRUMENTS
        for day in _days(start, end)
        for hour in range(24)
    ]
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ci-duka-ticks") as pool:
        for n, row in enumerate(pool.map(lambda item: _fetch_one(item, root), items), 1):
            rows.append(row)
            if n % 250 == 0 or n == len(items):
                counts = Counter(r["status"] for r in rows)
                ticks = sum(int(r.get("ticks") or 0) for r in rows)
                print(
                    f"tick fetch {n}/{len(items)} {dict(sorted(counts.items()))} "
                    f"ticks={ticks:,}",
                    flush=True,
                )
    manifest = root / "raw_tick_manifest_overlap.jsonl"
    manifest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    errors = [r for r in rows if r["status"] == "error"]
    payload = {
        "schema": "gtos.wave15.ci.tick_count_fetch.v1",
        "session": "CI",
        "blocks": "B2505-B2514",
        "generated_by": str(Path(__file__).relative_to(base.REPO)),
        "repair_declared_after_original_failure": True,
        "repair_hypothesis": (
            "Replace Dukascopy candle best-price-volume sums with the count of raw public tick "
            "records per UTC minute. No parameter is fitted and CI's original comparability "
            "thresholds remain unchanged."
        ),
        "requested_span": [start.isoformat(), end.isoformat()],
        "workers": workers,
        "url_template": (
            "https://datafeed.dukascopy.com/datafeed/<CODE>/<YYYY>/<zero-based-MM>/<DD>/"
            "<HH>h_ticks.bi5"
        ),
        "tick_record_schema": ">3i2f: millisecond offset, ask integer, bid integer, "
                              "ask best-price volume, bid best-price volume",
        "tick_count_definition": "number of raw Dukascopy ITick records in each UTC minute",
        "source_doc": {
            "url": ITICK_URL,
            "path": str(doc_path.relative_to(root)),
            "sha256": _sha256(doc_path),
        },
        "raw_manifest": str(manifest.relative_to(root)),
        "raw_manifest_sha256": _sha256(manifest),
        "status_counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "n_ticks": sum(int(r.get("ticks") or 0) for r in rows),
        "compressed_bytes": sum(int(r.get("bytes") or 0) for r in rows),
        "errors": errors[:20],
    }
    _json_write(FETCH_RECEIPT, payload)
    if errors:
        raise SystemExit(f"{len(errors)} raw-tick fetch errors remain; rerun to resume")
    return payload


def _aggregate_counts(inst: base.Instrument, *, start: dt.date, end: dt.date,
                      root: Path = DATA_ROOT) -> tuple[Counter[str], dict]:
    counts: Counter[str] = Counter()
    n_files = n_ticks = 0
    tick_root = root / "raw_ticks" / inst.code
    for path in sorted(tick_root.glob("*/*/*/*.bi5")):
        rel = path.relative_to(tick_root)
        year, month, day = map(int, rel.parts[:3])
        hour = int(Path(rel.parts[3]).stem)
        source_day = dt.date(year, month, day)
        if source_day < start or source_day > end:
            continue
        ticks = decode_ticks(path.read_bytes(), label=str(rel))
        hour_start = dt.datetime(
            year, month, day, hour, tzinfo=dt.timezone.utc
        )
        for millis, _ask, _bid, _ask_v, _bid_v in ticks:
            minute = hour_start + dt.timedelta(minutes=millis // 60_000)
            counts[minute.isoformat()] += 1
        n_files += 1
        n_ticks += len(ticks)
    return counts, {
        "n_payloads_present": n_files,
        "n_ticks": n_ticks,
        "n_active_minutes": len(counts),
    }


def convert(*, start: dt.date = DEFAULT_START, end: dt.date = DEFAULT_END,
            root: Path = DATA_ROOT) -> dict:
    fetch_doc = json.loads(FETCH_RECEIPT.read_text())
    if fetch_doc["requested_span"] != [start.isoformat(), end.isoformat()]:
        raise SystemExit("tick fetch span does not match conversion span")
    converted = {}
    for inst in base.INSTRUMENTS:
        counts, stats = _aggregate_counts(inst, start=start, end=end, root=root)
        source = base._converted_path(inst, root)
        path = repaired_path(inst, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".part")
        n_rows = n_zero = n_replaced = 0
        first = last = None
        with gzip.open(source, "rt", newline="") as src, base._deterministic_gzip_text(temp) as dst:
            reader = csv.DictReader(src)
            writer = csv.DictWriter(dst, fieldnames=base.CSV_FIELDS, lineterminator="\n")
            writer.writeheader()
            for row in reader:
                day = dt.date.fromisoformat(row["time"][:10])
                if day < start or day > end:
                    continue
                count = int(counts.get(row["time"], 0))
                row["tick_volume"] = str(count)
                writer.writerow(row)
                n_rows += 1
                n_zero += count == 0
                n_replaced += count > 0
                first = first or row["time"]
                last = row["time"]
        temp.replace(path)
        evidence = (
            f"THIRD-PARTY semantic repair: Dukascopy {inst.code} BID candle OHLC plus the "
            "COUNT of raw Dukascopy ITick records per UTC minute; provider ticks, NOT FTMO "
            "ticks or broker bars; fixed after CI's original volume-profile comparability failure."
        )
        sidecar = base.write_sidecar(
            path,
            basis=base.TRUE_UTC,
            rule=None,
            evidence=evidence,
            extra={
                "source_provider": "Dukascopy Bank SA",
                "source_instrument_code": inst.code,
                "source_offer_side": "BID",
                "source_ohlc": "BID_candles_min_1.bi5",
                "source_volume": "count of raw <HH>h_ticks.bi5 records by UTC minute",
                "source_volume_semantics": "provider-local tick count; not broker tick count",
                "semantic_repair": True,
                "original_overlap_receipt": str(ORIGINAL_OVERLAP.relative_to(base.REPO)),
            },
            valid_from=start,
            valid_through=end,
        )
        converted[inst.canonical] = {
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path),
            "sidecar_sha256": _sha256(sidecar),
            "rows": n_rows,
            "zero_tick_minutes": n_zero,
            "positive_tick_minutes": n_replaced,
            "first_utc": first,
            "last_utc": last,
            **stats,
        }
        print(
            f"tick-count convert {inst.canonical}: rows={n_rows:,} ticks={stats['n_ticks']:,} "
            f"active_minutes={stats['n_active_minutes']:,}",
            flush=True,
        )
    payload = {
        "schema": "gtos.wave15.ci.tick_count_source.v1",
        "session": "CI",
        "generated_by": str(Path(__file__).relative_to(base.REPO)),
        "fetch_receipt": str(FETCH_RECEIPT.relative_to(base.REPO)),
        "source_candle_receipt": str(base.SOURCE_RECEIPT.relative_to(base.REPO)),
        "span": [start.isoformat(), end.isoformat()],
        "semantic_repair": (
            "OHLC unchanged from the bound Dukascopy BID M1 candles; the CSV compatibility "
            "tick_volume field is replaced with a raw provider tick-record count."
        ),
        "no_fitted_parameters": True,
        "converted": converted,
    }
    _json_write(CONVERT_RECEIPT, payload)
    return payload


def validate(*, root: Path = DATA_ROOT) -> dict:
    original = json.loads(ORIGINAL_OVERLAP.read_text())
    source = json.loads(CONVERT_RECEIPT.read_text())
    results = {}
    for inst in base.INSTRUMENTS:
        third = repaired_path(inst, root)
        broker = BROKER_ROOT / f"{inst.canonical}_M1.csv"
        result = base._overlap_for(inst, third, broker)
        results[inst.canonical] = result
        poc_p95 = result["volume_profile_input_divergence"][
            "absolute_level_divergence_bps"
        ]["poc"]["p95"]
        print(
            f"tick-count overlap {inst.canonical}: "
            f"POC_p95={poc_p95} "
            f"comparable={result['structurally_comparable']}",
            flush=True,
        )
    payload = {
        "schema": "gtos.wave15.ci.tick_count_repair_overlap.v1",
        "session": "CI",
        "blocks": "B2505-B2514",
        "generated_by": str(Path(__file__).relative_to(base.REPO)),
        "original_overlap_receipt": str(ORIGINAL_OVERLAP.relative_to(base.REPO)),
        "original_gate_permitted": original["gate_permitted"],
        "source_receipt": str(CONVERT_RECEIPT.relative_to(base.REPO)),
        "repair_is_parameter_free": True,
        "thresholds_changed_after_original_result": False,
        "structural_rule": next(iter(results.values()))["structural_comparability_rule"],
        "per_symbol": results,
        "gate_permitted": all(r["structurally_comparable"] for r in results.values()),
        "next_action": (
            "fetch and bind 2024+ raw tick counts, revalidate, then permit CI-4"
            if all(r["structurally_comparable"] for r in results.values())
            else "stop before CI-4; exact blocker is a broker-comparable historical volume input"
        ),
    }
    _json_write(VALIDATE_RECEIPT, payload)
    return payload


def _date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("--start", type=_date, default=DEFAULT_START)
    fetch.add_argument("--end", type=_date, default=DEFAULT_END)
    fetch.add_argument("--workers", type=int, default=2)
    conv = sub.add_parser("convert")
    conv.add_argument("--start", type=_date, default=DEFAULT_START)
    conv.add_argument("--end", type=_date, default=DEFAULT_END)
    sub.add_parser("validate")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        fetch_ticks(start=args.start, end=args.end, workers=args.workers)
    elif args.command == "convert":
        convert(start=args.start, end=args.end)
    else:
        validate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
