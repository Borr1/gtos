#!/usr/bin/env python3
"""Session CI: provenance-bound Dukascopy M1 ingest and FTMO overlap validation.

This module is deliberately offline with respect to brokers.  Its only network client reads the
public Dukascopy Bank datafeed and two public Dukascopy documentation pages.  It never imports
MetaTrader5, never contacts a VPS, and never writes production config.

The source files use Dukascopy's public daily ``BID_candles_min_1.bi5`` representation.  A decoded
record is big-endian ``>5if``: seconds since the UTC day boundary, open, close, low, high and
volume.  Prices for both selected index CFDs carry three decimal places in this feed.

Commands are resumable and idempotent:

    python3 .../ci_thirdparty_m1.py fetch --start 2024-01-01 --end 2026-07-30
    python3 .../ci_thirdparty_m1.py convert
    python3 .../ci_thirdparty_m1.py validate
    python3 .../ci_thirdparty_m1.py splice
    python3 .../ci_thirdparty_m1.py verify

``fetch`` hard-caps itself at two workers.  ``validate`` compares independent converted
third-party files against the existing read-only FTMO bridge capture.  ``splice`` creates a gate
view that uses third-party M1 strictly before the first FTMO bar and FTMO from that timestamp
forward.  March 2026 is omitted from the gate view; no result filtering is used to protect it.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import lzma
import math
import os
import statistics
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Sequence

import requests


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.utils.research_timebase import TRUE_UTC, write_sidecar  # noqa: E402


DATA_ROOT = REPO / "data/mt5_research_exports/thirdparty_m1_ger40_uk100_20260731"
BROKER_ROOT = Path(
    "/Users/borr/GTOSActive/repo/data/mt5_research_exports/"
    "bridge_ftmo_carrycond_h4_m1_20260730"
)
RECEIPT_ROOT = Path(__file__).resolve().parent
SOURCE_RECEIPT = RECEIPT_ROOT / "CI_THIRD_PARTY_SOURCE_V1.json"
OVERLAP_RECEIPT = RECEIPT_ROOT / "CI_THIRD_PARTY_OVERLAP_V1.json"
SPLICE_RECEIPT = RECEIPT_ROOT / "CI_THIRD_PARTY_SPLICE_V1.json"
TICK_FETCH_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_FETCH_OVERLAP_V1.json"
TICK_SOURCE_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_SOURCE_OVERLAP_V1.json"
TICK_REPAIR_RECEIPT = RECEIPT_ROOT / "CI_TICK_COUNT_REPAIR_OVERLAP_V1.json"
DOWNSTREAM_VP_ARTIFACTS = (
    RECEIPT_ROOT / "CI_VP_TRADES_V1.json.gz",
    RECEIPT_ROOT / "CI_VP_GENERATION_V1.json",
    RECEIPT_ROOT / "CI_VP_GATE_V1.json",
)
SESSION_BASE = "be9b5ed4c46d4c4aa37bfc75301e1c21e3f53ff3"
R2_CONTRACT = REPO / (
    "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
    "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
)
PROTECTED_CONFIG_PATHS = {
    "config/agent_config.yaml",
    "config/profiles/redacted_account.yaml",
}
BROKER_CAPABLE_PATHS = {
    "run_book.py",
    "run_agent.py",
    "scripts/fn_smoke_trade.py",
    "scripts/mt5_preflight.py",
    "scripts/dual_broker_execution_follower.py",
}

DATAFEED = "https://datafeed.dukascopy.com/datafeed"
MARKETS_URL = "https://www.dukascopy.com/swiss/deutsch/cfd/range-of-markets/"
HISTORY_URL = "https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/historical-data-service/"
IBAR_URL = "https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/IBar.html"
FETCH_DATE = "2026-07-31"
PROTECTED_MARCH = (dt.date(2026, 3, 1), dt.date(2026, 3, 31))
CSV_FIELDS = ("time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume")
RECORD = struct.Struct(">5if")
_HTTP_LOCAL = threading.local()


@dataclass(frozen=True)
class Instrument:
    canonical: str
    broker_symbol: str
    code: str
    source_name: str
    quote_currency: str
    price_scale: int = 1000

    @property
    def source_url(self) -> str:
        return f"{DATAFEED}/{self.code}/<YYYY>/<zero-based-MM>/<DD>/BID_candles_min_1.bi5"


INSTRUMENTS: tuple[Instrument, ...] = (
    Instrument(
        canonical="GER40",
        broker_symbol="GER40.cash",
        code="DEUIDXEUR",
        source_name="Germany 40 Index CFD",
        quote_currency="EUR",
    ),
    Instrument(
        canonical="UK100",
        broker_symbol="UK100.cash",
        code="GBRIDXGBP",
        source_name="UK 100 Index CFD",
        quote_currency="GBP",
    ),
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n")


def _repo_label(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


@contextmanager
def _deterministic_gzip_text(path: Path, *, compresslevel: int = 6):
    """Text writer with mtime=0, so identical converted rows have an identical SHA-256."""
    raw = path.open("wb")
    compressed = gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, compresslevel=compresslevel, mtime=0
    )
    text = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
    try:
        yield text
    finally:
        text.close()


def _days(start: dt.date, end: dt.date) -> Iterator[dt.date]:
    if end < start:
        raise ValueError(f"reversed date range: {start}..{end}")
    for n in range((end - start).days + 1):
        yield start + dt.timedelta(days=n)


def _url(inst: Instrument, day: dt.date) -> str:
    # Dukascopy's path month is zero-based.  The day is the UTC day represented by the file.
    return (
        f"{DATAFEED}/{inst.code}/{day.year}/{day.month - 1:02d}/{day.day:02d}/"
        "BID_candles_min_1.bi5"
    )


def decode_bi5(payload: bytes, *, day: dt.date, inst: Instrument) -> list[dict]:
    """Decode and structurally validate one public daily candle payload."""
    try:
        raw = lzma.decompress(payload)
    except lzma.LZMAError as exc:
        raise ValueError(f"{inst.code} {day}: payload is not valid LZMA/bi5") from exc
    if not raw or len(raw) % RECORD.size:
        raise ValueError(
            f"{inst.code} {day}: decoded byte count {len(raw)} is not a positive multiple "
            f"of {RECORD.size}"
        )
    out: list[dict] = []
    previous = -1
    base = dt.datetime.combine(day, dt.time(), tzinfo=dt.timezone.utc)
    for offset in range(0, len(raw), RECORD.size):
        second, open_i, close_i, low_i, high_i, volume = RECORD.unpack_from(raw, offset)
        if second < 0 or second >= 86_400 or second % 60:
            raise ValueError(f"{inst.code} {day}: invalid minute offset {second}")
        if second <= previous:
            raise ValueError(f"{inst.code} {day}: minute offsets not strictly increasing")
        previous = second
        if min(open_i, close_i, low_i, high_i) <= 0:
            raise ValueError(f"{inst.code} {day}: non-positive OHLC integer")
        if low_i > min(open_i, close_i) or high_i < max(open_i, close_i) or low_i > high_i:
            raise ValueError(f"{inst.code} {day}: invalid OHLC ordering at second {second}")
        if not math.isfinite(volume) or volume < 0:
            raise ValueError(f"{inst.code} {day}: invalid volume {volume!r}")
        scale = float(inst.price_scale)
        out.append(
            {
                "time": (base + dt.timedelta(seconds=second)).isoformat(),
                "open": open_i / scale,
                "high": high_i / scale,
                "low": low_i / scale,
                "close": close_i / scale,
                "tick_volume": float(volume),
                "spread": 0,
                "real_volume": 0,
            }
        )
    return out


def _raw_path(inst: Instrument, day: dt.date, root: Path = DATA_ROOT) -> Path:
    return root / "raw" / inst.code / f"{day.year}" / f"{day.month:02d}" / f"{day.day:02d}.bi5"


def _converted_path(inst: Instrument, root: Path = DATA_ROOT) -> Path:
    return root / "converted" / f"{inst.canonical}_M1.csv.gz"


def _gate_path(inst: Instrument, root: Path = DATA_ROOT) -> Path:
    return root / "gate" / f"{inst.canonical}_M1_HYBRID.csv.gz"


def _http_get(url: str, *, timeout: float = 30.0) -> tuple[bytes, Mapping[str, str]]:
    # One Session per worker: at most two live connections, with keep-alive across the daily
    # objects.  A fresh TLS connection per 10-20 KB file turned a 1,884-object fetch into a
    # multi-hour job; connection reuse changes no bytes and keeps the explicit concurrency cap.
    session = getattr(_HTTP_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "GTOS-research-session-CI/1.0 (+declared third-party evidence ingest)",
            "Accept-Encoding": "identity",
        })
        _HTTP_LOCAL.session = session
    response = session.get(url, timeout=(min(timeout, 10.0), timeout))
    if response.status_code >= 400:
        raise urllib.error.HTTPError(
            url, response.status_code, response.reason, response.headers, None
        )
    return response.content, dict(response.headers.items())


def _fetch_one(item: tuple[Instrument, dt.date], root: Path) -> dict:
    inst, day = item
    path = _raw_path(inst, day, root)
    url = _url(inst, day)
    if path.is_file():
        payload = path.read_bytes()
        rows = decode_bi5(payload, day=day, inst=inst)
        return {
            "instrument": inst.canonical,
            "source_code": inst.code,
            "day": day.isoformat(),
            "url": url,
            "status": "present_validated",
            "bytes": len(payload),
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    last_error = ""
    for attempt in range(1, 4):
        try:
            payload, headers = _http_get(url)
            rows = decode_bi5(payload, day=day, inst=inst)
            path.parent.mkdir(parents=True, exist_ok=True)
            # A single task owns this explicit path.  replace() makes an interrupted write
            # recoverable without truncating a previously validated payload.
            temp = path.with_suffix(path.suffix + f".part.{os.getpid()}")
            temp.write_bytes(payload)
            temp.replace(path)
            return {
                "instrument": inst.canonical,
                "source_code": inst.code,
                "day": day.isoformat(),
                "url": url,
                "status": "downloaded_validated",
                "http_last_modified": headers.get("Last-Modified"),
                "http_etag": headers.get("ETag"),
                "bytes": len(payload),
                "rows": len(rows),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {
                    "instrument": inst.canonical,
                    "source_code": inst.code,
                    "day": day.isoformat(),
                    "url": url,
                    "status": "source_404",
                    "http_status": 404,
                }
            last_error = f"HTTP {exc.code}: {exc.reason}"
        except (OSError, TimeoutError, ValueError, urllib.error.URLError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < 3:
            time.sleep(0.5 * attempt)
    return {
        "instrument": inst.canonical,
        "source_code": inst.code,
        "day": day.isoformat(),
        "url": url,
        "status": "error",
        "error": last_error,
    }


def _capture_source_docs(root: Path) -> list[dict]:
    out = []
    doc_root = root / "raw" / "source_docs"
    doc_root.mkdir(parents=True, exist_ok=True)
    for name, url in (
        ("dukascopy_range_of_markets.html", MARKETS_URL),
        ("dukascopy_historical_data_service.html", HISTORY_URL),
        ("dukascopy_ibar_volume_semantics.html", IBAR_URL),
    ):
        path = doc_root / name
        status = "present"
        if not path.is_file():
            payload, _headers = _http_get(url)
            path.write_bytes(payload)
            status = "downloaded"
        out.append(
            {"url": url, "path": str(path.relative_to(root)), "status": status,
             "bytes": path.stat().st_size, "sha256": _sha256(path)}
        )
    return out


def fetch(*, start: dt.date, end: dt.date, workers: int, root: Path = DATA_ROOT) -> dict:
    if workers < 1 or workers > 2:
        raise SystemExit("--workers must be 1 or 2; Session CI's heavy/concurrent-work ceiling is 2")
    root.mkdir(parents=True, exist_ok=True)
    source_docs = _capture_source_docs(root)
    items = [(inst, day) for inst in INSTRUMENTS for day in _days(start, end)]
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ci-dukascopy") as pool:
        for n, result in enumerate(pool.map(lambda item: _fetch_one(item, root), items), 1):
            rows.append(result)
            if n % 250 == 0 or n == len(items):
                counts = Counter(r["status"] for r in rows)
                print(f"fetch {n}/{len(items)} {dict(sorted(counts.items()))}", flush=True)
    errors = [r for r in rows if r["status"] == "error"]
    manifest = root / "raw_manifest.jsonl"
    manifest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    summary: dict = {
        "schema": "gtos.wave15.ci.thirdparty_fetch.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "fetch_date": FETCH_DATE,
        "requested_span": [start.isoformat(), end.isoformat()],
        "workers": workers,
        "source_docs": source_docs,
        "raw_manifest": str(manifest.relative_to(root)),
        "raw_manifest_sha256": _sha256(manifest),
        "status_counts": dict(sorted(Counter(r["status"] for r in rows).items())),
        "instruments": {},
        "errors": errors[:20],
    }
    for inst in INSTRUMENTS:
        good = [r for r in rows if r["instrument"] == inst.canonical
                and r["status"] in ("present_validated", "downloaded_validated")]
        summary["instruments"][inst.canonical] = {
            "source_code": inst.code,
            "source_name": inst.source_name,
            "instrument_class": "index CFD (not the cash reference index; not a future)",
            "quote_currency": inst.quote_currency,
            "price_integer_scale": inst.price_scale,
            "bid_candles": True,
            "candle_volume_semantics": (
                "Dukascopy IBar.getVolume(): sum of best-price volumes for each tick in the "
                "bar; not an MT5 tick count"
            ),
            "url_template": inst.source_url,
            "n_daily_payloads": len(good),
            "n_decoded_rows": sum(int(r["rows"]) for r in good),
            "first_source_day": min((r["day"] for r in good), default=None),
            "last_source_day": max((r["day"] for r in good), default=None),
            "compressed_bytes": sum(int(r["bytes"]) for r in good),
            "n_source_404": sum(1 for r in rows if r["instrument"] == inst.canonical
                                and r["status"] == "source_404"),
        }
    _json_write(root / "fetch_summary.json", summary)
    if errors:
        raise SystemExit(f"{len(errors)} non-404 fetch failures remain; rerun to resume")
    return summary


def _format_number(value: float, *, price: bool = False) -> str:
    if price:
        return f"{value:.3f}"
    return format(value, ".9g")


def convert(*, root: Path = DATA_ROOT) -> dict:
    fetch_summary = json.loads((root / "fetch_summary.json").read_text())
    converted: dict[str, dict] = {}
    for inst in INSTRUMENTS:
        raw_files = sorted((root / "raw" / inst.code).glob("*/*/*.bi5"))
        if not raw_files:
            raise SystemExit(f"no raw files for {inst.code}; run fetch first")
        path = _converted_path(inst, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".part")
        n_rows = n_zero_volume = 0
        first = last = None
        source_days: list[str] = []
        with _deterministic_gzip_text(temp) as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
            writer.writeheader()
            for raw_path in raw_files:
                day = dt.date(int(raw_path.parts[-3]), int(raw_path.parts[-2]),
                              int(raw_path.stem))
                rows = decode_bi5(raw_path.read_bytes(), day=day, inst=inst)
                source_days.append(day.isoformat())
                for row in rows:
                    writer.writerow(
                        {
                            "time": row["time"],
                            "open": _format_number(row["open"], price=True),
                            "high": _format_number(row["high"], price=True),
                            "low": _format_number(row["low"], price=True),
                            "close": _format_number(row["close"], price=True),
                            "tick_volume": _format_number(row["tick_volume"]),
                            "spread": 0,
                            "real_volume": 0,
                        }
                    )
                    n_rows += 1
                    n_zero_volume += row["tick_volume"] == 0
                    first = first or row["time"]
                    last = row["time"]
        temp.replace(path)
        evidence = (
            f"THIRD-PARTY, provenance-declared: Dukascopy Bank public datafeed "
            f"{inst.code} BID M1 ({inst.source_name}), fetched 2026-07-31; NOT broker bars; "
            "see CI-3 for the measured divergence vs FTMO-Server3 on the overlap window."
        )
        sidecar = write_sidecar(
            path,
            basis=TRUE_UTC,
            rule=None,
            evidence=evidence,
            extra={
                "source_provider": "Dukascopy Bank SA",
                "source_instrument_code": inst.code,
                "source_instrument_name": inst.source_name,
                "source_instrument_class": "index CFD",
                "source_quote_currency": inst.quote_currency,
                "source_offer_side": "BID",
                "source_period": "ONE_MIN",
                "source_volume_semantics": (
                    "Dukascopy IBar.getVolume(): sum of best-price volumes for each tick in "
                    "the bar; stored in the estate CSV tick_volume compatibility column, but "
                    "NOT an MT5 tick count"
                ),
                "source_volume_semantics_url": IBAR_URL,
                "source_url_template": inst.source_url,
                "fetch_date": FETCH_DATE,
                "not_broker_bars": True,
                "ci_3_overlap_receipt": _repo_label(OVERLAP_RECEIPT),
            },
            valid_from=dt.date.fromisoformat(first[:10]),
            valid_through=dt.date.fromisoformat(last[:10]),
        )
        converted[inst.canonical] = {
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path),
            "sidecar": str(sidecar.relative_to(root)),
            "sidecar_sha256": _sha256(sidecar),
            "rows": n_rows,
            "zero_volume_rows": n_zero_volume,
            "first_utc": first,
            "last_utc": last,
            "n_source_days": len(source_days),
            "first_source_day": min(source_days),
            "last_source_day": max(source_days),
        }
        print(f"converted {inst.canonical}: {n_rows:,} rows {first}..{last}", flush=True)
    receipt = {
        "schema": "gtos.wave15.ci.thirdparty_source.v1",
        "session": "CI",
        "blocks": "B2500-B2504",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "fetch_summary": fetch_summary,
        "converted": converted,
        "identity_basis": {
            "official_market_page": MARKETS_URL,
            "official_ibar_volume_page": IBAR_URL,
            "reading": (
                "Dukascopy's Index-CFD table maps DEU.IDX/EUR to 'Germany 40 Index' and "
                "GBR.IDX/GBP to 'UK 100 Index'. These are provider BID CFD candles, not "
                "exchange futures and not the cash reference indices themselves."
            ),
            "official_declared_trading_hours_gmt": {
                "DEU.IDX/EUR": {
                    "summer": "Sun-Fri 22:00-20:15; daily break 20:15-22:00",
                    "winter": "Sun-Fri 23:00-21:00; daily break 21:00-23:00",
                },
                "GBR.IDX/GBP": {
                    "summer": "Sun-Fri 22:00-20:15; daily break 20:15-22:00",
                    "winter": "Sun-Fri 23:00-21:00; daily break 21:00-23:00",
                },
                "source": "the captured official market page's Index-CFD trading-hours table",
            },
            "volume_semantics": (
                "The public BID candle's float is Dukascopy IBar volume: the sum of volumes "
                "available at the best price for each tick in the bar. It is stored under "
                "tick_volume only to satisfy the estate CSV schema; it is not an MT5 tick "
                "count. CI-3 therefore treats volume-profile comparability as a measured gate, "
                "not as an identity inferred from the column name."
            ),
        },
        "ingest_span_disclosure": (
            "The landed surface begins 2024-01-01: nearly two years earlier than the "
            "commission's minimum and the explicitly requested 2024+ fold-buying depth. "
            "Dukascopy serves "
            "some older history; CI does not represent this bounded ingest as the provider's "
            "absolute full-history origin."
        ),
        "clock_basis": (
            "Each file path names a UTC calendar day and each record supplies seconds since "
            "that day boundary; converted timestamps are explicit +00:00 and the sanctioned "
            "sidecar writer declares true_utc."
        ),
        "raw_and_converted_local_root": str(root),
        "git_tracking_boundary": (
            "data/mt5_research_exports is intentionally gitignored; local raw/converted bytes "
            "are bound here by per-file and manifest SHA-256. Re-fetch is deterministic from "
            "the declared URLs subject to upstream historical corrections."
        ),
    }
    _json_write(SOURCE_RECEIPT, receipt)
    return receipt


def _read_rows(path: Path) -> Iterator[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as fh:
        for row in csv.DictReader(fh):
            yield row


def _as_utc_rows(path: Path, *, key: tuple[str, int]) -> list[dict]:
    # This is the same loader seam the production-free GenerationPort uses.  It proves that the
    # sanctioned sidecars are accepted through the front door, rather than parsed specially here.
    return CsvBarSource({key: path}, label="ci_timebase_front_door")._load(key)


def _quantiles(values: Sequence[float]) -> dict:
    if not values:
        return {k: None for k in ("min", "p50", "p90", "p95", "p99", "max", "mean")}
    ordered = sorted(values)

    def q(p: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        x = p * (len(ordered) - 1)
        lo, hi = int(math.floor(x)), int(math.ceil(x))
        if lo == hi:
            return ordered[lo]
        return ordered[lo] * (hi - x) + ordered[hi] * (x - lo)

    return {
        "min": round(ordered[0], 6),
        "p50": round(q(0.50), 6),
        "p90": round(q(0.90), 6),
        "p95": round(q(0.95), 6),
        "p99": round(q(0.99), 6),
        "max": round(ordered[-1], 6),
        "mean": round(statistics.fmean(ordered), 6),
    }


def _session_summary(stamps: set[dt.datetime]) -> dict:
    by_day: dict[dt.date, list[dt.datetime]] = defaultdict(list)
    for stamp in stamps:
        by_day[stamp.date()].append(stamp)
    sessions = []
    for day, values in sorted(by_day.items()):
        values.sort()
        sessions.append(
            {
                "day": day.isoformat(),
                "first_minute_utc": values[0].strftime("%H:%M"),
                "last_minute_utc": values[-1].strftime("%H:%M"),
                "n_minutes": len(values),
                "largest_intraday_gap_minutes": max(
                    [int((b - a).total_seconds() // 60) - 1 for a, b in zip(values, values[1:])]
                    or [0]
                ),
            }
        )
    return {
        "n_utc_days": len(sessions),
        "first_minute_mode": Counter(x["first_minute_utc"] for x in sessions).most_common(5),
        "last_minute_mode": Counter(x["last_minute_utc"] for x in sessions).most_common(5),
        "minutes_per_day": _quantiles([float(x["n_minutes"]) for x in sessions]),
        "largest_intraday_gap_minutes": _quantiles(
            [float(x["largest_intraday_gap_minutes"]) for x in sessions]
        ),
    }


def _profile_divergence(
    third_rows: Sequence[dict], broker_rows: Sequence[dict],
    *, lo: dt.datetime, hi: dt.datetime,
) -> dict:
    """Compare the actual prior-day POC/VA input the vp sleeve consumes.

    Volume units need not match across providers: each profile uses relative volume within its
    own day.  The resulting price levels are directly comparable and are more decision-relevant
    than a raw correlation between Dukascopy volume floats and FTMO tick counts.
    """
    from src.components.ultimate_book.primitives import Bar
    from src.components.ultimate_book.sleeves import volume_profile as vp

    def profiles(rows: Sequence[dict]):
        times, bars = [], []
        for row in rows:
            stamp = dt.datetime.fromisoformat(row["time"])
            if not (lo <= stamp <= hi):
                continue
            times.append(stamp)
            bars.append(
                Bar(
                    float(row["open"]), float(row["high"]), float(row["low"]),
                    float(row["close"]), float(row.get("volume") or 0.0),
                )
            )
        return vp.daily_profiles(bars, times, bin_atr_frac=vp.BIN_FRAC)[0]

    third_profiles = profiles(third_rows)
    broker_profiles = profiles(broker_rows)
    common_days = sorted(set(third_profiles) & set(broker_profiles))
    fields = {name: [] for name in ("poc", "vah", "val")}
    rows_out = []
    for day in common_days:
        third = third_profiles[day]
        broker = broker_profiles[day]
        if broker.poc <= 0:
            continue
        for field in fields:
            fields[field].append(
                abs(float(getattr(third, field)) - float(getattr(broker, field)))
                / float(broker.poc) * 10_000
            )
        rows_out.append(
            {
                "day": day.isoformat(),
                "thirdparty_n_m1": third.n_m1,
                "broker_n_m1": broker.n_m1,
                "poc_abs_bps": round(fields["poc"][-1], 6),
                "vah_abs_bps": round(fields["vah"][-1], 6),
                "val_abs_bps": round(fields["val"][-1], 6),
            }
        )
    return {
        "n_common_profile_days": len(rows_out),
        "absolute_level_divergence_bps": {
            field: _quantiles(values) for field, values in fields.items()
        },
        "per_day": rows_out,
        "reading": (
            "Same production volume-profile builder on each provider independently. Volume "
            "units are provider-local; POC/VA price levels are the comparable sleeve inputs."
        ),
    }


def _overlap_for(inst: Instrument, third_path: Path, broker_path: Path) -> dict:
    broker_rows = _as_utc_rows(broker_path, key=(inst.broker_symbol, 1))
    broker = {dt.datetime.fromisoformat(r["time"]): r for r in broker_rows}
    lo = min(broker)
    hi = max(broker)
    # CsvBarSource deliberately validates the entire provenance-declared file through the same
    # front door as GenerationPort.  Retain only the independently fixed broker-overlap window
    # after that parse: a full-history row list plus a second 1.35M-entry timestamp dictionary
    # bought no evidence and made this comparison contend with the shared replay machine.
    third_all = _as_utc_rows(third_path, key=(inst.broker_symbol, 1))
    third_rows = [
        row for row in third_all
        if lo <= dt.datetime.fromisoformat(row["time"]) <= hi
    ]
    del third_all
    third_window = {dt.datetime.fromisoformat(r["time"]): r for r in third_rows}
    common = sorted(set(third_window) & set(broker))
    third_only = set(third_window) - set(broker)
    broker_only = set(broker) - set(third_window)
    third_active = {
        t for t, row in third_window.items() if float(row.get("volume") or 0.0) > 0
    }
    broker_active = {t for t, row in broker.items() if float(row.get("volume") or 0.0) > 0}
    active_union = third_active | broker_active
    active_common = third_active & broker_active
    field_abs_bps: dict[str, list[float]] = {k: [] for k in ("open", "high", "low", "close")}
    close_signed_bps: list[float] = []
    for stamp in common:
        tr, br = third_window[stamp], broker[stamp]
        denom = abs(float(br["close"]))
        if denom <= 0:
            continue
        for field in field_abs_bps:
            field_abs_bps[field].append(abs(float(tr[field]) - float(br[field])) / denom * 10_000)
        close_signed_bps.append((float(tr["close"]) - float(br["close"])) / denom * 10_000)

    def by_dst(predicate) -> dict:
        stamps = [t for t in common if predicate(t.date())]
        values = [abs(float(third_window[t]["close"]) - float(broker[t]["close"]))
                  / abs(float(broker[t]["close"])) * 10_000 for t in stamps]
        return {"n_common_bars": len(stamps), "close_abs_bps": _quantiles(values)}

    # The overlap starts after the spring disagreement window.  The explicit zero is evidence
    # about coverage, not a claim that a DST transition was observed.  We still compare summer
    # UTC boundaries and publish that the decisive spring transition is outside the broker span.
    from src.utils.research_timebase import in_us_eu_dst_disagreement

    third_stamps = set(third_window)
    broker_stamps = set(broker)
    coverage_union = third_stamps | broker_stamps
    jaccard = len(third_stamps & broker_stamps) / len(coverage_union) if coverage_union else 0.0
    common_ratio_broker = len(common) / len(broker_stamps) if broker_stamps else 0.0
    active_jaccard = len(active_common) / len(active_union) if active_union else 0.0
    active_share_broker = len(active_common) / len(broker_active) if broker_active else 0.0
    profile = _profile_divergence(third_rows, broker_rows, lo=lo, hi=hi)
    close_p95 = _quantiles(field_abs_bps["close"])["p95"]
    poc_p95 = profile["absolute_level_divergence_bps"]["poc"]["p95"]
    comparable = (
        len(common) >= 20_000
        and active_share_broker >= 0.70
        and active_jaccard >= 0.50
        and close_p95 is not None
        and float(close_p95) <= 30.0
        and profile["n_common_profile_days"] >= 10
        and poc_p95 is not None
        and float(poc_p95) <= 40.0
    )
    return {
        "thirdparty_code": inst.code,
        "broker_symbol": inst.broker_symbol,
        "overlap_utc": [lo.isoformat(), hi.isoformat()],
        "n_thirdparty_bars_in_window": len(third_window),
        "n_broker_bars": len(broker),
        "n_common_minute_stamps": len(common),
        "n_thirdparty_only_minutes": len(third_only),
        "n_broker_only_minutes": len(broker_only),
        "common_share_of_broker_bars": round(common_ratio_broker, 6),
        "minute_set_jaccard": round(jaccard, 6),
        "active_gap_alignment": {
            "definition": "provider minute has positive provider-local volume",
            "n_thirdparty_active_minutes": len(third_active),
            "n_broker_active_minutes": len(broker_active),
            "n_common_active_minutes": len(active_common),
            "n_thirdparty_only_active_minutes": len(third_active - broker_active),
            "n_broker_only_active_minutes": len(broker_active - third_active),
            "common_active_share_of_broker": round(active_share_broker, 6),
            "active_minute_set_jaccard": round(active_jaccard, 6),
        },
        "ohlc_absolute_divergence_bps": {
            field: _quantiles(values) for field, values in field_abs_bps.items()
        },
        "close_signed_divergence_bps": _quantiles(close_signed_bps),
        "volume_profile_input_divergence": profile,
        "session_boundaries": {
            "thirdparty_active_minutes": _session_summary(third_active),
            "thirdparty_dense_candle_grid": _session_summary(third_stamps),
            "broker_active_tick_minutes": _session_summary(broker_active),
            "interpretation": (
                "Dukascopy emits a dense BID candle grid, including zero-volume/flat minutes; "
                "FTMO emits minutes in which its terminal received ticks. Exact-minute overlap "
                "and provider-only gaps are therefore both published."
            ),
        },
        "dst": {
            "us_eu_disagreement_inside_overlap": by_dst(in_us_eu_dst_disagreement),
            "ordinary_calendar_days": by_dst(lambda d: not in_us_eu_dst_disagreement(d)),
            "spring_2026_transition_observable": False,
            "reason": (
                "FTMO M1 begins after 2026-04-26 UTC, while the 2026 US/EU spring DST "
                "disagreement ended in March. No source can infer transition behaviour from "
                "an overlap that does not contain it; the series are compared in true UTC and "
                "the limitation is carried forward."
            ),
        },
        "structural_comparability_rule": {
            "minimum_common_minutes": 20_000,
            "minimum_common_active_share_of_broker": 0.70,
            "minimum_active_minute_set_jaccard": 0.50,
            "maximum_close_p95_absolute_bps": 30.0,
            "minimum_common_volume_profile_days": 10,
            "maximum_poc_p95_absolute_bps": 40.0,
            "chosen_before_gate": True,
        },
        "structurally_comparable": comparable,
    }


def validate(*, root: Path = DATA_ROOT) -> dict:
    if not BROKER_ROOT.is_dir():
        raise SystemExit(f"read-only broker capture missing: {BROKER_ROOT}")
    results = {}
    for inst in INSTRUMENTS:
        third = _converted_path(inst, root)
        broker = BROKER_ROOT / f"{inst.canonical}_M1.csv"
        results[inst.canonical] = _overlap_for(inst, third, broker)
        r = results[inst.canonical]
        p95 = r["ohlc_absolute_divergence_bps"]["close"]["p95"]
        print(
            f"overlap {inst.canonical}: common={r['n_common_minute_stamps']:,} "
            f"broker_share={r['common_share_of_broker_bars']:.3f} "
            f"close_abs_p95={p95} bps comparable={r['structurally_comparable']}",
            flush=True,
        )
    receipt = {
        "schema": "gtos.wave15.ci.thirdparty_overlap.v1",
        "session": "CI",
        "blocks": "B2505-B2511",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "thirdparty_source_receipt": str(SOURCE_RECEIPT.relative_to(REPO)),
        "broker_capture": str(BROKER_ROOT),
        "broker_capture_manifest_sha256": _sha256(BROKER_ROOT / "manifest.json"),
        "per_symbol": results,
        "gate_permitted": all(r["structurally_comparable"] for r in results.values()),
        "gate_rule": (
            "Both symbols must clear the declared per-symbol comparability rule. One failure "
            "stops CI before candidate generation; unlike data are not made admissible by pooling."
        ),
    }
    _json_write(OVERLAP_RECEIPT, receipt)
    return receipt


def _broker_rows(inst: Instrument) -> list[dict]:
    path = BROKER_ROOT / f"{inst.canonical}_M1.csv"
    return _as_utc_rows(path, key=(inst.broker_symbol, 1))


def splice(*, root: Path = DATA_ROOT) -> dict:
    overlap = json.loads(OVERLAP_RECEIPT.read_text())
    if not overlap.get("gate_permitted"):
        raise SystemExit("CI-3 did not establish structural comparability; refusing to build gate view")
    result = {}
    for inst in INSTRUMENTS:
        third_path = _converted_path(inst, root)
        third_rows = _as_utc_rows(third_path, key=(inst.broker_symbol, 1))
        broker_rows = _broker_rows(inst)
        join = min(dt.datetime.fromisoformat(r["time"]) for r in broker_rows)
        before = [r for r in third_rows if dt.datetime.fromisoformat(r["time"]) < join]
        after = [r for r in broker_rows if dt.datetime.fromisoformat(r["time"]) >= join]
        # Protect the outcome-unread month at the input-view boundary too.  This is stronger than
        # relying only on the generation driver's decision/horizon refusal.
        before_kept = [r for r in before if not (
            PROTECTED_MARCH[0] <= dt.datetime.fromisoformat(r["time"]).date() <= PROTECTED_MARCH[1]
        )]
        removed_march = len(before) - len(before_kept)
        combined = before_kept + after
        stamps = [dt.datetime.fromisoformat(r["time"]) for r in combined]
        if stamps != sorted(stamps) or len(stamps) != len(set(stamps)):
            raise SystemExit(f"{inst.canonical}: hybrid stamps are not unique and strictly ordered")
        path = _gate_path(inst, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".part")
        with _deterministic_gzip_text(temp) as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
            writer.writeheader()
            for r in combined:
                writer.writerow(
                    {
                        "time": r["time"],
                        "open": _format_number(float(r["open"]), price=True),
                        "high": _format_number(float(r["high"]), price=True),
                        "low": _format_number(float(r["low"]), price=True),
                        "close": _format_number(float(r["close"]), price=True),
                        "tick_volume": _format_number(float(r.get("volume", 0.0))),
                        "spread": 0,
                        "real_volume": 0,
                    }
                )
        temp.replace(path)
        evidence = (
            f"HYBRID RESEARCH VIEW: Dukascopy Bank {inst.code} BID M1 strictly before "
            f"{join.isoformat()}, FTMO-Server3 broker M1 from that instant; both decoded to "
            "true UTC through sanctioned loaders. THIRD-PARTY rows are NOT broker bars. "
            "March 2026 rows are absent by construction; see CI-3 and CI-4 receipts."
        )
        sidecar = write_sidecar(
            path,
            basis=TRUE_UTC,
            rule=None,
            evidence=evidence,
            extra={
                "hybrid_view": True,
                "thirdparty_source": inst.code,
                "broker_source": "FTMO-Server3",
                "join_utc": join.isoformat(),
                "protected_blackout": [d.isoformat() for d in PROTECTED_MARCH],
                "ci_3_overlap_receipt": _repo_label(OVERLAP_RECEIPT),
            },
            valid_from=stamps[0].date(),
            valid_through=stamps[-1].date(),
        )
        result[inst.canonical] = {
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path),
            "sidecar_sha256": _sha256(sidecar),
            "join_utc": join.isoformat(),
            "n_thirdparty_rows_before_join": len(before_kept),
            "n_broker_rows_from_join": len(after),
            "n_march_rows_removed_before_gate": removed_march,
            "n_rows": len(combined),
            "first_utc": stamps[0].isoformat(),
            "last_utc": stamps[-1].isoformat(),
        }
        print(
            f"splice {inst.canonical}: thirdparty={len(before_kept):,} broker={len(after):,} "
            f"march_removed={removed_march:,} join={join.isoformat()}",
            flush=True,
        )
    receipt = {
        "schema": "gtos.wave15.ci.thirdparty_splice.v1",
        "session": "CI",
        "blocks": "B2512-B2514",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "overlap_receipt": _repo_label(OVERLAP_RECEIPT),
        "gate_view": result,
        "march_outcome_read": False,
        "note": (
            "The gate view is an availability/provenance splice, fixed before candidate "
            "generation. It is not selected from outcomes."
        ),
    }
    _json_write(SPLICE_RECEIPT, receipt)
    return receipt


def _session_boundary() -> dict:
    """Mechanical proof of CI's edit boundary and the current R2 standing condition."""
    committed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{SESSION_BASE}..HEAD"],
        cwd=REPO,
        text=True,
    ).splitlines()
    porcelain = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO, text=True
    ).splitlines()
    dirty = [line[3:] for line in porcelain if len(line) > 3]
    changed = sorted(set(committed) | set(dirty))

    contract = json.loads(R2_CONTRACT.read_text())
    bound_rows = [
        row
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in contract["input_bindings"][group]
    ]
    bound_paths = {str(row["path"]) for row in bound_rows}
    drift = []
    for row in bound_rows:
        path = Path(row["path"])
        if not path.is_absolute():
            path = REPO / path
        actual = _sha256(path) if path.is_file() else None
        if actual != row["sha256"]:
            drift.append(
                {
                    "path": str(row["path"]),
                    "expected_sha256": row["sha256"],
                    "actual_sha256": actual,
                }
            )
    protected = sorted(PROTECTED_CONFIG_PATHS & set(changed))
    src = sorted(path for path in changed if path.startswith("src/"))
    r2_changed = sorted(bound_paths & set(changed))
    broker_capable = sorted(BROKER_CAPABLE_PATHS & set(changed))
    return {
        "session_base": SESSION_BASE,
        "changed_paths": changed,
        "protected_config_paths_changed": protected,
        "src_paths_changed": src,
        "r2_bound_paths_changed": r2_changed,
        "broker_capable_paths_changed": broker_capable,
        "r2": {
            "contract": str(R2_CONTRACT.relative_to(REPO)),
            "bound_paths": len(bound_rows),
            "current_drift_count": len(drift),
            "current_drift": drift,
            "session_introduced_drift": bool(r2_changed),
        },
        "pass": not (protected or src or r2_changed or broker_capable),
    }


def verify(*, root: Path = DATA_ROOT) -> dict:
    source = json.loads(SOURCE_RECEIPT.read_text())
    overlap = json.loads(OVERLAP_RECEIPT.read_text())
    checks: dict[str, bool] = {}
    for inst in INSTRUMENTS:
        converted = _converted_path(inst, root)
        expected = source["converted"][inst.canonical]
        checks[f"{inst.canonical}.converted_sha256"] = _sha256(converted) == expected["sha256"]
        checks[f"{inst.canonical}.sidecar_sha256"] = (
            _sha256(Path(str(converted) + ".timebase.json")) == expected["sidecar_sha256"]
        )
    # A failed structural comparison is a valid terminal state, not a failed verification.  It
    # must be harder to claim the stop than merely to write it in prose: bind the parameter-free
    # repair and assert that every artifact which would imply CI-4 ran is absent.
    stopped = not bool(overlap["gate_permitted"])
    terminal = "STOPPED_STRUCTURAL_DIVERGENCE" if stopped else "GATE_VIEW_BUILT"
    if stopped:
        tick_fetch = json.loads(TICK_FETCH_RECEIPT.read_text())
        tick_source = json.loads(TICK_SOURCE_RECEIPT.read_text())
        tick_repair = json.loads(TICK_REPAIR_RECEIPT.read_text())
        checks["original_overlap_gate_false"] = overlap["gate_permitted"] is False
        checks["tick_count_repair_gate_false"] = tick_repair["gate_permitted"] is False
        checks["repair_thresholds_unchanged"] = (
            tick_repair["thresholds_changed_after_original_result"] is False
        )
        manifest = root / tick_fetch["raw_manifest"]
        checks["raw_tick_manifest_sha256"] = (
            _sha256(manifest) == tick_fetch["raw_manifest_sha256"]
        )
        for inst in INSTRUMENTS:
            meta = tick_source["converted"][inst.canonical]
            path = root / meta["path"]
            checks[f"{inst.canonical}.tick_count_sha256"] = _sha256(path) == meta["sha256"]
            checks[f"{inst.canonical}.tick_count_sidecar_sha256"] = (
                _sha256(Path(str(path) + ".timebase.json")) == meta["sidecar_sha256"]
            )
            checks[f"{inst.canonical}.hybrid_gate_absent"] = not _gate_path(inst, root).exists()
        checks["splice_receipt_absent"] = not SPLICE_RECEIPT.exists()
        for path in DOWNSTREAM_VP_ARTIFACTS:
            checks[f"downstream_absent:{path.name}"] = not path.exists()
    else:
        splice_doc = json.loads(SPLICE_RECEIPT.read_text())
        for inst in INSTRUMENTS:
            gate_path = _gate_path(inst, root)
            gate_meta = splice_doc["gate_view"][inst.canonical]
            checks[f"{inst.canonical}.gate_sha256"] = (
                _sha256(gate_path) == gate_meta["sha256"]
            )
            checks[f"{inst.canonical}.overlap_comparable"] = bool(
                overlap["per_symbol"][inst.canonical]["structurally_comparable"]
            )
            checks[f"{inst.canonical}.march_removed"] = (
                gate_meta["n_march_rows_removed_before_gate"] > 0
            )
        checks["gate_permitted"] = True
    checks["all_sidecars_true_utc"] = all(
        json.loads(Path(str(_converted_path(inst, root)) + ".timebase.json").read_text())[
            "time_column_basis"
        ] == TRUE_UTC
        for inst in INSTRUMENTS
    )
    payload = {
        "schema": "gtos.wave15.ci.thirdparty_verify.v1",
        "session": "CI",
        "terminal_state": terminal,
        "march_2026_outcome_read": False,
        "session_boundary": _session_boundary(),
        "checks": checks,
        "pass": all(checks.values()),
    }
    payload["checks"]["session_boundary"] = payload["session_boundary"]["pass"]
    payload["pass"] = all(payload["checks"].values())
    _json_write(RECEIPT_ROOT / "CI_THIRD_PARTY_VERIFY_V1.json", payload)
    if not payload["pass"]:
        raise SystemExit(f"verification failed: {[k for k, v in checks.items() if not v]}")
    print(json.dumps(payload, indent=1, sort_keys=True))
    return payload


def _date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--start", type=_date, default=dt.date(2024, 1, 1))
    f.add_argument("--end", type=_date, default=dt.date(2026, 7, 30))
    f.add_argument("--workers", type=int, default=2)
    sub.add_parser("convert")
    sub.add_parser("validate")
    sub.add_parser("splice")
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    if args.command == "fetch":
        fetch(start=args.start, end=args.end, workers=args.workers)
    elif args.command == "convert":
        convert()
    elif args.command == "validate":
        validate()
    elif args.command == "splice":
        splice()
    elif args.command == "verify":
        verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
