#!/usr/bin/env python3
"""Append-only MT5 ingestion helper for the retest-geometry study.

Reads the last timestamp in each ``data/historical/{symbol}_{TF}.csv`` file
and appends any new rows up to ``--end`` (default 2026-04-17 23:45 UTC). Does
NOT rewrite existing rows. If MT5 is unavailable or the symbol doesn't exist,
logs and continues — the study falls back to whatever data is on disk.

Usage (run once at session start):
    python research/retest_geometry/pull_missing_data.py --end 2026-04-17

Dedup strategy: read the last timestamp already in the CSV, pull MT5 rows
strictly AFTER that timestamp, append rows with the original timestamp format
preserved (``YYYY-MM-DD HH:MM:SS``).

Symbols handled: XAUUSD, US30_cash (-> MT5 'US30.cash'), USDJPY, GBPJPY,
GBPUSD. Timeframes: M15, H1 (H4/D1 also refreshed for completeness even
though the study only reads M15 + H1).
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

HIST_DIR = _PROJECT_ROOT / "data" / "historical"

# Symbol name map: our internal name -> MT5 name
SYMBOL_MT5_NAME: dict[str, str] = {
    "XAUUSD": "XAUUSD",
    "US30_cash": "US30.cash",
    "USDJPY": "USDJPY",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
}

TIMEFRAMES = ("M15", "H1", "H4", "D1")


def _read_last_timestamp(csv_path: Path) -> datetime | None:
    """Return the last timestamp in the CSV as a UTC datetime, or None if empty."""
    if not csv_path.exists():
        return None
    with open(csv_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    if len(lines) < 2:
        return None
    # Last line (skip trailing newline)
    last = lines[-1].strip()
    if not last:
        last = lines[-2].strip()
    parts = last.split(",")
    ts_str = parts[0]
    # ``YYYY-MM-DD HH:MM:SS`` format
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(ts_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    logger.warning("Could not parse last timestamp %r in %s", ts_str, csv_path)
    return None


def _detect_csv_format(csv_path: Path) -> tuple[str, list[str]]:
    """Return (time_format, field_names) detected from the CSV header."""
    with open(csv_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return "%Y-%m-%d %H:%M:%S", ["time", "open", "high", "low", "close", "volume"]
        fields = list(reader.fieldnames)
        # Peek first row to determine time format
        for row in reader:
            ts = row[fields[0]]
            if "T" in ts and ts.endswith("Z"):
                return "%Y-%m-%dT%H:%M:%SZ", fields
            return "%Y-%m-%d %H:%M:%S", fields
        return "%Y-%m-%d %H:%M:%S", fields


def pull_and_append(symbol: str, timeframe: str, end_utc: datetime) -> int:
    """Pull MT5 rows after last-existing timestamp and append. Return count appended.

    Silently returns 0 if the CSV is missing (no existing file to extend) or
    MT5 has no data for this symbol.
    """
    csv_path = HIST_DIR / f"{symbol}_{timeframe}.csv"
    if not csv_path.exists():
        logger.warning("CSV missing, skipping: %s", csv_path)
        return 0

    last_ts = _read_last_timestamp(csv_path)
    if last_ts is None:
        logger.warning("Empty CSV, skipping: %s", csv_path)
        return 0

    if last_ts.replace(tzinfo=None) >= end_utc.replace(tzinfo=None):
        logger.info("%s %s: up to date (last=%s)", symbol, timeframe, last_ts)
        return 0

    try:
        import MetaTrader5 as mt5  # type: ignore[import-untyped]
    except ImportError:
        logger.error("MT5 not importable; skipping %s %s", symbol, timeframe)
        return 0

    if not mt5.initialize():
        logger.error("MT5 init failed: %s", mt5.last_error())
        return 0

    tf_map = {
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    tf_const = tf_map[timeframe]
    mt5_symbol = SYMBOL_MT5_NAME.get(symbol, symbol)

    # Pull range: one minute after last_ts to end_utc
    pull_start = last_ts + timedelta(minutes=1)
    try:
        rates = mt5.copy_rates_range(mt5_symbol, tf_const, pull_start, end_utc)
    except Exception as exc:
        logger.error("MT5 pull failed for %s %s: %s", mt5_symbol, timeframe, exc)
        mt5.shutdown()
        return 0

    if rates is None or len(rates) == 0:
        logger.info("MT5 returned no rows for %s %s (pull_start=%s, end=%s)",
                    mt5_symbol, timeframe, pull_start, end_utc)
        mt5.shutdown()
        return 0

    time_fmt, fields = _detect_csv_format(csv_path)

    # Filter rows strictly AFTER last_ts (MT5 inclusive end)
    rows_to_append = []
    for r in rates:
        dt = datetime.fromtimestamp(int(r["time"]), tz=timezone.utc)
        if dt <= last_ts:
            continue
        if dt > end_utc:
            break
        ts_out = dt.strftime(time_fmt)
        row_values = {
            fields[0]: ts_out,
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["tick_volume"]),
        }
        rows_to_append.append(row_values)

    if not rows_to_append:
        logger.info("No new rows after filter for %s %s", symbol, timeframe)
        mt5.shutdown()
        return 0

    # Append rows preserving the symbol's CSV format
    with open(csv_path, "a", encoding="utf-8", newline="") as fh:
        # We only write the 6 canonical columns; legacy extra columns (e.g.
        # GBPJPY's "spread","real_volume") will simply be absent in the new
        # rows — blank. This matches how MT5 rates have no spread info on
        # historical pulls.
        for r in rows_to_append:
            # Match width of header: pad missing columns with ''
            values = []
            for f in fields:
                if f in r:
                    values.append(str(r[f]))
                elif f.lower() == "time":
                    values.append(str(r.get(fields[0], "")))
                else:
                    values.append("")
            fh.write(",".join(values) + "\n")

    logger.info("Appended %d rows to %s", len(rows_to_append), csv_path)
    mt5.shutdown()
    return len(rows_to_append)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--end", type=str, default="2026-04-17",
                   help="End date (YYYY-MM-DD), inclusive through 23:45 UTC.")
    p.add_argument("--symbols", type=str, default=None,
                   help="Comma-separated symbols (default: all 5).")
    p.add_argument("--timeframes", type=str, default="M15,H1",
                   help="Comma-separated timeframes (default M15,H1).")
    args = p.parse_args(argv)

    end_date = datetime.strptime(args.end, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )

    symbols = list(SYMBOL_MT5_NAME.keys())
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    total = 0
    for sym in symbols:
        for tf in timeframes:
            try:
                n = pull_and_append(sym, tf, end_date)
                total += n
            except Exception as exc:
                logger.exception("Unhandled error for %s %s: %s", sym, tf, exc)

    logger.info("Done. Total rows appended: %d", total)
    return 0 if total >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
