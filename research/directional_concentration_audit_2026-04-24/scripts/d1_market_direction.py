"""
Compute naive D1 direction from historical CSVs for each instrument in April 2026.
Cross-reference with system-reported daily_bias.
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "historical_2026"


def _read_d1(symbol: str) -> list[dict]:
    rows = []
    fp = DATA / f"{symbol}_D1.csv"
    if not fp.exists():
        return rows
    with open(fp, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append({
                "time": r["time"],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
            })
    return rows


def _direction_label(o: float, c: float) -> str:
    if c > o:
        return "bull"
    if c < o:
        return "bear"
    return "flat"


def main() -> None:
    for symbol in ("XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"):
        rows = _read_d1(symbol)
        if not rows:
            print(f"-- {symbol}: no CSV")
            continue
        print(f"\n-- {symbol} — D1 direction by day (April 2026) --")
        april = [r for r in rows if r["time"].startswith("2026-04")]
        if not april:
            print("  (no April rows)")
            continue
        dir_counter = Counter()
        for r in april:
            d = _direction_label(r["open"], r["close"])
            dir_counter[d] += 1
            # Also compute 3-day rolling momentum
            idx = rows.index(r)
            if idx >= 3:
                ma_dir = "bull" if r["close"] > rows[idx - 3]["close"] else "bear"
            else:
                ma_dir = "?"
            body_frac = (r["close"] - r["open"]) / max(r["high"] - r["low"], 1e-9)
            print(
                f"  {r['time']}: O={r['open']:.3f} H={r['high']:.3f} L={r['low']:.3f} "
                f"C={r['close']:.3f} dir={d} body_frac={body_frac:+.2f} 3day_trend={ma_dir}"
            )
        print(f"  Summary: {dict(dir_counter)}  "
              f"(bull_pct={100*dir_counter['bull']/len(april):.0f}%)")

        # Net April performance
        first_open = april[0]["open"]
        last_close = april[-1]["close"]
        net_pct = (last_close - first_open) / first_open * 100.0
        print(f"  Net April move (open Apr-first -> close Apr-last): {net_pct:+.2f}%")


if __name__ == "__main__":
    main()
