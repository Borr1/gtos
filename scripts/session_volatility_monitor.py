#!/usr/bin/env python3
"""H25 — Session Volatility Monitor (logging only).

Logs intra-session volatility distribution to validate the finding that
volatility peaks at session open and decays within each kill zone.

Confirmed across XAUUSD, US30, and GBPJPY (UTC-corrected):
- London unanimously shows W1 > W2 > W3
- NY shows instrument-specific patterns (gold peaks W1, equities peak W2)

Run after each trading day (or as a daily cron):
    python scripts/session_volatility_monitor.py [--date 2026-04-11]

Output: shadow_logs/session_volatility_log.csv

CRITICAL: MT5 M15 data is in the BROKER SERVER's wall clock (UTC+2 / UTC+3).
All internal calculations use UTC timestamps.

WARNING (2026-07-26, finding F7): the DST_RANGES table below is the EU/EET calendar and
it is the WRONG one. FTMO-Server3 switches on the US DST dates (2nd Sunday of March,
1st Sunday of November), so this converter is an hour off for ~3 weeks each spring and
~1 week each autumn. The conclusions in the docstring above ("London unanimously shows
W1 > W2 > W3") were produced with it and are unproven for those windows.
Use src.utils.broker_clock.NEW_YORK_PLUS_7 instead; this script is logging-only and was
left unrepaired deliberately, because fixing it without re-running it would only move
the error. See docs/audits/fable5-vision-audit-20260725/CLOCK_TRUTH_IMPACT_NOTE.md.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mt5 import create_mt5

logger = logging.getLogger(__name__)

OUTPUT_PATH = "shadow_logs/session_volatility_log.csv"

# EET/EEST DST ranges (European Summer Time).
# WRONG CALENDAR for this broker -- see the module docstring. Kept as-is so the script
# still reproduces its own historical output rather than silently producing a third one.
DST_RANGES = [
    (date(2024, 3, 31), date(2024, 10, 27)),
    (date(2025, 3, 30), date(2025, 10, 26)),
    (date(2026, 3, 29), date(2026, 10, 25)),
    (date(2027, 3, 28), date(2027, 10, 31)),
]

# Kill zone boundaries in UTC (hours, minutes)
KILL_ZONES = {
    "london": {"start": (7, 0), "end": (10, 30)},   # 3.5 hours = 14 M15 candles
    "ny":     {"start": (13, 0), "end": (15, 30)},   # 2.5 hours = 10 M15 candles
}

# Instruments to monitor
INSTRUMENTS = {
    "XAUUSD": "XAUUSD",
    "US30": "US30.cash",
    "GBPJPY": "GBPJPY",
    "USDJPY": "USDJPY",
    "GBPUSD": "GBPUSD",
}

TF_M15 = 15  # MetaTrader5 M15 timeframe constant


def eet_to_utc_offset(d: date) -> int:
    """Return EET/EEST UTC offset for a given date."""
    for start, end in DST_RANGES:
        if start <= d <= end:
            return 3  # EEST (summer)
    return 2  # EET (winter)


def broker_time_to_utc(broker_dt: datetime, d: date) -> datetime:
    """Convert broker (EET/EEST) datetime to UTC."""
    offset_hours = eet_to_utc_offset(d)
    return broker_dt - timedelta(hours=offset_hours)


def get_m15_candles_for_session(
    mt5, symbol: str, target_date: date, session: str,
) -> list[dict]:
    """Fetch M15 candles for a specific kill zone session in UTC.

    Returns candles with 'time_utc' added to each bar.
    """
    kz = KILL_ZONES[session]
    start_h, start_m = kz["start"]
    end_h, end_m = kz["end"]

    # Build UTC range for the session
    utc_start = datetime(
        target_date.year, target_date.month, target_date.day,
        start_h, start_m, tzinfo=timezone.utc,
    )
    utc_end = datetime(
        target_date.year, target_date.month, target_date.day,
        end_h, end_m, tzinfo=timezone.utc,
    )

    # Convert UTC range to broker time for the MT5 query
    offset = eet_to_utc_offset(target_date)
    broker_start = utc_start + timedelta(hours=offset)
    broker_end = utc_end + timedelta(hours=offset)

    candles = mt5.get_candles_range(symbol, TF_M15, broker_start, broker_end)
    if not candles:
        return []

    # Add UTC time to each candle
    for c in candles:
        t = c["time"]
        if isinstance(t, (int, float)):
            broker_dt = datetime.fromtimestamp(t, tz=timezone.utc)
        elif isinstance(t, str):
            broker_dt = datetime.fromisoformat(t)
            if broker_dt.tzinfo is None:
                broker_dt = broker_dt.replace(tzinfo=timezone.utc)
        else:
            broker_dt = t if t.tzinfo else t.replace(tzinfo=timezone.utc)
        c["time_utc"] = broker_time_to_utc(broker_dt, target_date)

    return candles


def compute_window_stats(candles: list[dict], window_minutes: int = 90) -> list[dict]:
    """Split candles into windows and compute avg candle range per window.

    Each M15 candle covers 15 minutes. A 90-minute window = 6 candles.
    Returns list of dicts: [{"window": "W1", "avg_range": ..., "candle_count": ...}, ...]
    """
    if not candles:
        return []

    candles_per_window = window_minutes // 15
    windows = []
    for i in range(0, len(candles), candles_per_window):
        chunk = candles[i:i + candles_per_window]
        if not chunk:
            break
        ranges = [c["high"] - c["low"] for c in chunk]
        avg_range = sum(ranges) / len(ranges) if ranges else 0
        window_num = (i // candles_per_window) + 1
        windows.append({
            "window": f"W{window_num}",
            "avg_range": round(avg_range, 5),
            "candle_count": len(chunk),
        })

    return windows


def classify_pattern(windows: list[dict]) -> str:
    """Classify the volatility pattern across windows."""
    if len(windows) < 2:
        return "INSUFFICIENT_DATA"

    ranges = [w["avg_range"] for w in windows]

    if all(ranges[i] > ranges[i + 1] for i in range(len(ranges) - 1)):
        return "DECREASING"
    if all(ranges[i] < ranges[i + 1] for i in range(len(ranges) - 1)):
        return "INCREASING"
    if len(ranges) >= 3 and ranges[1] > ranges[0] and ranges[1] > ranges[2]:
        return "W2_PEAK"
    return "OTHER"


def write_csv_row(row: dict, output_path: str = OUTPUT_PATH):
    """Append a row to the CSV log. Create with header if new."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0

    fieldnames = [
        "date", "instrument", "session", "w1_avg_range", "w2_avg_range",
        "w3_avg_range", "pattern", "candle_count",
    ]

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def analyze_session(mt5, instrument: str, mt5_symbol: str,
                    target_date: date, session: str,
                    output_path: str = OUTPUT_PATH) -> dict | None:
    """Analyze one instrument + session combination."""
    candles = get_m15_candles_for_session(mt5, mt5_symbol, target_date, session)
    if not candles:
        logger.info("No M15 data for %s %s on %s", instrument, session, target_date)
        return None

    windows = compute_window_stats(candles, window_minutes=90)
    pattern = classify_pattern(windows)

    row = {
        "date": target_date.isoformat(),
        "instrument": instrument,
        "session": session,
        "w1_avg_range": windows[0]["avg_range"] if len(windows) > 0 else "",
        "w2_avg_range": windows[1]["avg_range"] if len(windows) > 1 else "",
        "w3_avg_range": windows[2]["avg_range"] if len(windows) > 2 else "",
        "pattern": pattern,
        "candle_count": sum(w["candle_count"] for w in windows),
    }

    write_csv_row(row, output_path)
    logger.info("Logged: %s %s %s — %s (W1=%.5f W2=%.5f W3=%s)",
                target_date, instrument, session, pattern,
                row["w1_avg_range"] or 0, row["w2_avg_range"] or 0,
                row["w3_avg_range"] or "N/A")
    return row


def main():
    parser = argparse.ArgumentParser(description="Session Volatility Monitor (H25)")
    parser.add_argument("--date", type=str, default=None,
                        help="Date to analyze (YYYY-MM-DD). Default: today.")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH,
                        help="Output CSV path.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = datetime.now(timezone.utc).date()

    mt5 = create_mt5(mode="live")
    if not mt5.connect():
        logger.error("Failed to connect to MT5")
        sys.exit(1)

    results = []
    for instrument, mt5_symbol in INSTRUMENTS.items():
        for session in KILL_ZONES:
            result = analyze_session(
                mt5, instrument, mt5_symbol,
                target_date, session, args.output,
            )
            if result:
                results.append(result)

    logger.info("\nProcessed %d session entries for %s", len(results), target_date)


if __name__ == "__main__":
    main()
