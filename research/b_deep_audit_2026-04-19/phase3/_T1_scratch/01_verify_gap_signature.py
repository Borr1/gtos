"""T1 phase 3 — verify gap signature claim from eta_review.

Measures the 23:45 → 00:00 transition gap (close-to-open) across FX pairs
in both historical_2026/ and historical/ datasets for 2026-Q1 overlap.

Expected (per eta_review §2):
  historical_2026/GBPJPY: mean -13.37 pips, 86.7% negative
  historical_2026/USDJPY: mean -5.21 pips, 83.3% negative
  historical_2026/EURUSD: mean -3.00 pips, 86.7% negative
  historical/GBPJPY: mean -1.06 pips, 48.6% negative

This script is standalone read-only; no production code paths touched.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


def load_csv_rows(path: Path):
    """Parse rows into (datetime, open, close) tuples."""
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            t = r["time"]
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(t, "%Y-%m-%d")
                except ValueError:
                    continue
            rows.append((dt, float(r["open"]), float(r["close"])))
    rows.sort(key=lambda x: x[0])
    return rows


def measure_gaps(rows, hour_start=23, hour_end=0, minute_start=45, minute_end=0, pip_scale=10000):
    """Measure close-to-open transition for consecutive candles at boundary.

    pip_scale = divisions to convert price-diff to pips
      - GBPJPY / USDJPY: 100 (2 decimals per pip)
      - EURUSD / GBPUSD: 10000 (4 decimals per pip)
    """
    gaps = []
    for i in range(len(rows) - 1):
        dt_a, _, close_a = rows[i]
        dt_b, open_b, _ = rows[i+1]
        # looking for boundary close_a at 23:45 to open_b at 00:00 NEXT DAY
        if dt_a.hour == hour_start and dt_a.minute == minute_start and dt_b.hour == hour_end and dt_b.minute == minute_end:
            dt_diff = (dt_b - dt_a).total_seconds() / 60
            if 10 < dt_diff < 20:  # exactly M15 next bar
                gap_pips = (open_b - close_a) * pip_scale
                gaps.append((dt_a.date(), gap_pips))
    return gaps


def summarize(label, gaps):
    if not gaps:
        print(f"  {label}: no gaps found")
        return
    values = [g[1] for g in gaps]
    mean = sum(values) / len(values)
    neg_pct = 100 * sum(1 for v in values if v < 0) / len(values)
    print(f"  {label}: n={len(gaps)}, mean={mean:+.2f} pips, neg%={neg_pct:.1f}%")


def main():
    cases = [
        ("GBPJPY", "GBPJPY", 100),
        ("USDJPY", "USDJPY", 100),
        ("EURUSD", "EURUSD", 10000),
        ("GBPUSD", "GBPUSD", 10000),
    ]
    print("=" * 70)
    print("23:45 -> 00:00 gap signature (pips)")
    print("=" * 70)
    for sym, file_key, pip_scale in cases:
        for subdir in ["historical_2026", "historical"]:
            path = ROOT / f"data/{subdir}/{file_key}_M15.csv"
            if not path.exists():
                print(f"  {sym:6s} {subdir:20s} FILE NOT FOUND")
                continue
            rows = load_csv_rows(path)
            # restrict to 2026-Q1 window for comparability
            q1 = [r for r in rows if r[0].year == 2026 and r[0].month <= 4]
            gaps = measure_gaps(q1, pip_scale=pip_scale)
            summarize(f"{sym:6s} {subdir:20s}", gaps)
        print()

    # Also check XAUUSD / NAS100 for gap signature (concern: is the bug FX-only?)
    print("=" * 70)
    print("XAUUSD / NAS100 / US30 gap-signature (NOT 23:45->00:00 — these instruments")
    print("don't trade through midnight; checking last->first daily candle instead).")
    print("=" * 70)
    for sym in ["XAUUSD", "NAS100", "US30_cash"]:
        path = ROOT / f"data/historical_2026/{sym}_M15.csv"
        if not path.exists():
            continue
        rows = load_csv_rows(path)
        # how many 23:45 -> 00:00 transitions with <20min gap?
        boundary_hits = 0
        daily_hour_range_first = {}
        daily_hour_range_last = {}
        for dt, o, c in rows:
            d = dt.date()
            daily_hour_range_first.setdefault(d, dt.hour)
            daily_hour_range_last[d] = dt.hour
        first_hrs = {}
        last_hrs = {}
        for d, h in daily_hour_range_first.items():
            first_hrs[h] = first_hrs.get(h, 0) + 1
        for d, h in daily_hour_range_last.items():
            last_hrs[h] = last_hrs.get(h, 0) + 1
        print(f"  {sym}:")
        print(f"    first-candle hour distribution: {sorted(first_hrs.items())[:5]}")
        print(f"    last-candle hour distribution:  {sorted(last_hrs.items())[-5:]}")


if __name__ == "__main__":
    main()
