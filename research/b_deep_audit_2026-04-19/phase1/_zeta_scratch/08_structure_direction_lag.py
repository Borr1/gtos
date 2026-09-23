"""
Does identify_structure() lag on regime changes? Simulate by running it on a
rolling window and see how many bars it takes to flip after a real trend flip.

Specifically: on NAS100 around 2026-03-28 → 2026-04-03 (W14 — the D1-bias-lag
episode in the synthesis), what was D1 structure direction each day?
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
sys.path.insert(0, str(ROOT))

from src.components.market_state import detect_swings, identify_structure


def load_tf(symbol: str, tf: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{symbol}_{tf}.csv"
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["time"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    return rows


def main():
    symbol = "NAS100"
    tf = "D1"
    d1 = load_tf(symbol, tf)
    h4 = load_tf(symbol, "H4")
    h1 = load_tf(symbol, "H1")

    print(f"{symbol} {tf}: n={len(d1)} bars; range {d1[0]['time']} -> {d1[-1]['time']}")
    # Rolling eval: for each day i, compute structure from [i-60:i]
    print(f"\nRolling-60-bar D1 structure direction:")
    print(f"{'as_of':<12}{'close':>10}{'direction':<17}{'hh':>4}{'hl':>4}{'lh':>4}{'ll':>4}{'sw':>4}")
    for i in range(60, len(d1)):
        window = d1[i-60:i+1]
        swings = detect_swings(window, min_bars=2)
        structure = identify_structure(swings)
        print(f"{window[-1]['time'][:10]:<12}{window[-1]['close']:>10.2f}{structure.direction:<17}"
              f"{structure.hh_count or 0:>4}{structure.hl_count or 0:>4}"
              f"{structure.lh_count or 0:>4}{structure.ll_count or 0:>4}{len(swings):>4}")
    print()
    # Also H4 rolling
    print(f"Rolling-120-bar H4 structure:")
    for i in range(120, len(h4), 6):  # every 6 H4 = 1 day
        window = h4[i-120:i+1]
        swings = detect_swings(window, min_bars=2)
        structure = identify_structure(swings)
        if window[-1]['time'].startswith(('2026-03-2', '2026-03-3', '2026-04-0')):
            print(f"{window[-1]['time']:<20}{window[-1]['close']:>10.2f}{structure.direction:<17}"
                  f"{structure.hh_count or 0:>4}{structure.hl_count or 0:>4}"
                  f"{structure.lh_count or 0:>4}{structure.ll_count or 0:>4}{len(swings):>4}")


if __name__ == "__main__":
    main()
