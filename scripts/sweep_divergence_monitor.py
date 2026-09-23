#!/usr/bin/env python3
"""H16 — US30 Sweep Divergence Monitor (logging only).

Tracks whether session sweeps continue or reverse, and compares across
instruments. US30 sweeps continue 68% of the time (n=657) vs XAUUSD
at 31% (n=280) — structurally opposite behavior.

Run after each trading day:
    python scripts/sweep_divergence_monitor.py [--date 2026-04-11]

Output: shadow_logs/sweep_divergence_log.csv

Alert: If US30 continuation rate drops below 55% over rolling 50 sweeps,
or XAUUSD continuation rises above 45%, the structural divergence may
be closing — flag for review.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mt5 import create_mt5

logger = logging.getLogger(__name__)

OUTPUT_PATH = "shadow_logs/sweep_divergence_log.csv"

TF_M15 = 15

# Sweep detection thresholds (instrument-native units)
SWEEP_THRESHOLDS = {
    "XAUUSD": 3.0,        # $3
    "US30": 25.0,          # 25 points
    "GBPJPY": 0.10,        # 10 pips
    "USDJPY": 0.10,        # 10 pips
    "GBPUSD": 0.0010,      # 10 pips
}

# MT5 symbol mapping
MT5_SYMBOLS = {
    "XAUUSD": "XAUUSD",
    "US30": "US30.cash",
    "GBPJPY": "GBPJPY",
    "USDJPY": "USDJPY",
    "GBPUSD": "GBPUSD",
}

# Kill zone boundaries (UTC)
SESSIONS = {
    "london": {"start": (7, 0), "end": (10, 30)},
    "ny": {"start": (13, 0), "end": (15, 30)},
}

# EET/EEST DST ranges
DST_RANGES = [
    (date(2024, 3, 31), date(2024, 10, 27)),
    (date(2025, 3, 30), date(2025, 10, 26)),
    (date(2026, 3, 29), date(2026, 10, 25)),
    (date(2027, 3, 28), date(2027, 10, 31)),
]


def eet_to_utc_offset(d: date) -> int:
    for start, end in DST_RANGES:
        if start <= d <= end:
            return 3
    return 2


def get_session_candles(mt5, symbol: str, target_date: date,
                        session: str) -> list[dict]:
    """Get M15 candles for a session window."""
    kz = SESSIONS[session]
    start_h, start_m = kz["start"]
    end_h, end_m = kz["end"]

    utc_start = datetime(
        target_date.year, target_date.month, target_date.day,
        start_h, start_m, tzinfo=timezone.utc,
    )
    utc_end = datetime(
        target_date.year, target_date.month, target_date.day,
        end_h, end_m, tzinfo=timezone.utc,
    )

    offset = eet_to_utc_offset(target_date)
    broker_start = utc_start + timedelta(hours=offset)
    broker_end = utc_end + timedelta(hours=offset)

    return mt5.get_candles_range(symbol, TF_M15, broker_start, broker_end) or []


def get_previous_session_range(mt5, symbol: str, target_date: date,
                               session: str) -> tuple[float, float] | None:
    """Get the high/low of the PREVIOUS occurrence of this session.

    For london: previous day's london session.
    For ny: previous day's ny session (or same day's london if checking ny).
    """
    prev_date = target_date - timedelta(days=1)
    # Skip weekends
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)

    candles = get_session_candles(mt5, symbol, prev_date, session)
    if not candles:
        return None

    session_high = max(c["high"] for c in candles)
    session_low = min(c["low"] for c in candles)
    return session_high, session_low


def detect_sweep(candles: list[dict], prev_high: float, prev_low: float,
                 threshold: float) -> dict | None:
    """Detect if a session sweep occurred.

    A sweep is when price exceeds previous session's H/L by at least
    the threshold amount, then closes back inside the range.
    """
    if not candles:
        return None

    session_high = max(c["high"] for c in candles)
    session_low = min(c["low"] for c in candles)
    last_close = candles[-1]["close"]

    # High sweep: exceeded prev high by threshold, then closed back inside
    high_sweep = (session_high >= prev_high + threshold
                  and last_close < prev_high)

    # Low sweep: exceeded prev low by threshold, then closed back inside
    low_sweep = (session_low <= prev_low - threshold
                 and last_close > prev_low)

    if high_sweep:
        return {"direction": "high", "extreme": session_high,
                "reference": prev_high, "close": last_close}
    if low_sweep:
        return {"direction": "low", "extreme": session_low,
                "reference": prev_low, "close": last_close}

    return None


def classify_outcome(candles: list[dict], sweep: dict, n_candles: int = 3) -> str:
    """Classify what happens in the N candles after the sweep.

    CONTINUATION: price reaches 50% of session range in rebreak direction
    REVERSAL: price exceeds the sweep extreme
    NEUTRAL: neither
    """
    if not candles or not sweep:
        return "NEUTRAL"

    # Find the candle index where the sweep extreme occurred
    sweep_idx = None
    extreme = sweep["extreme"]
    for i, c in enumerate(candles):
        if sweep["direction"] == "high" and c["high"] >= extreme:
            sweep_idx = i
            break
        elif sweep["direction"] == "low" and c["low"] <= extreme:
            sweep_idx = i
            break

    if sweep_idx is None:
        return "NEUTRAL"

    # Get the next N candles after the sweep
    post_sweep = candles[sweep_idx + 1: sweep_idx + 1 + n_candles]
    if not post_sweep:
        return "NEUTRAL"

    session_range = max(c["high"] for c in candles) - min(c["low"] for c in candles)
    if session_range <= 0:
        return "NEUTRAL"

    half_range = session_range * 0.5

    for c in post_sweep:
        if sweep["direction"] == "high":
            # Continuation = price breaks back above prev high by 50% of range
            if c["high"] >= sweep["reference"] + half_range:
                return "CONTINUATION"
            # Reversal = price goes below sweep low extreme reversal zone
            if c["low"] <= sweep["reference"] - half_range:
                return "REVERSAL"
        else:
            # Low sweep — continuation means price breaks lower
            if c["low"] <= sweep["reference"] - half_range:
                return "CONTINUATION"
            if c["high"] >= sweep["reference"] + half_range:
                return "REVERSAL"

    return "NEUTRAL"


def write_csv_row(row: dict, output_path: str = OUTPUT_PATH):
    """Append a row to the sweep divergence CSV log."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0

    fieldnames = [
        "date", "instrument", "session", "sweep_direction",
        "sweep_extreme", "reference_level", "outcome",
    ]

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def check_alerts(output_path: str = OUTPUT_PATH):
    """Check rolling 50-sweep continuation rates for alerts."""
    path = Path(output_path)
    if not path.exists():
        return

    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    for instrument, alert_threshold, direction in [
        ("US30", 0.55, "below"),
        ("XAUUSD", 0.45, "above"),
    ]:
        inst_rows = [r for r in rows if r["instrument"] == instrument]
        recent = inst_rows[-50:] if len(inst_rows) >= 50 else inst_rows
        if len(recent) < 20:
            continue

        cont_count = sum(1 for r in recent if r["outcome"] == "CONTINUATION")
        cont_rate = cont_count / len(recent)

        if direction == "below" and cont_rate < alert_threshold:
            logger.warning(
                "ALERT: %s sweep continuation rate %.1f%% < %.1f%% threshold "
                "(last %d sweeps). Structural divergence may be closing.",
                instrument, cont_rate * 100, alert_threshold * 100, len(recent),
            )
        elif direction == "above" and cont_rate > alert_threshold:
            logger.warning(
                "ALERT: %s sweep continuation rate %.1f%% > %.1f%% threshold "
                "(last %d sweeps). Structural divergence may be closing.",
                instrument, cont_rate * 100, alert_threshold * 100, len(recent),
            )


def analyze_instrument(mt5, instrument: str, target_date: date,
                       output_path: str = OUTPUT_PATH) -> list[dict]:
    """Analyze sweep behavior for one instrument across all sessions."""
    mt5_symbol = MT5_SYMBOLS[instrument]
    threshold = SWEEP_THRESHOLDS[instrument]
    results = []

    for session in SESSIONS:
        prev_range = get_previous_session_range(mt5, mt5_symbol, target_date, session)
        if not prev_range:
            continue

        prev_high, prev_low = prev_range
        candles = get_session_candles(mt5, mt5_symbol, target_date, session)
        if not candles:
            continue

        sweep = detect_sweep(candles, prev_high, prev_low, threshold)
        if not sweep:
            continue

        outcome = classify_outcome(candles, sweep)

        row = {
            "date": target_date.isoformat(),
            "instrument": instrument,
            "session": session,
            "sweep_direction": sweep["direction"],
            "sweep_extreme": round(sweep["extreme"], 5),
            "reference_level": round(sweep["reference"], 5),
            "outcome": outcome,
        }
        write_csv_row(row, output_path)
        results.append(row)

        logger.info("Sweep: %s %s %s — %s sweep → %s",
                     target_date, instrument, session,
                     sweep["direction"], outcome)

    return results


def main():
    parser = argparse.ArgumentParser(description="Sweep Divergence Monitor (H16)")
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

    all_results = []
    for instrument in SWEEP_THRESHOLDS:
        results = analyze_instrument(mt5, instrument, target_date, args.output)
        all_results.extend(results)

    logger.info("\nDetected %d sweeps across all instruments for %s",
                len(all_results), target_date)

    # Check rolling alerts
    check_alerts(args.output)


if __name__ == "__main__":
    main()
