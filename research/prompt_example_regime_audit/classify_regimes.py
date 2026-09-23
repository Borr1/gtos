"""Classify market regime per H4 candle for the 5 live instruments.

Regime types (per task spec):
  - trending_bull / trending_bear / chop / reversal / breakout

Methodology (deterministic, transparent):
  - Use a 20-period rolling window on H4 closes (~3.3 days, comparable to H1
    structure horizons in the GTOS pipeline).
  - Slope: linear regression slope of close vs. index over the 20-bar window,
    normalized by the window's mean ATR.
    * Strong positive slope (>= +0.5 ATR/window-bar) -> trending_bull candidate
    * Strong negative slope (<= -0.5 ATR/window-bar) -> trending_bear candidate
    * Otherwise -> chop / reversal candidate
  - Volatility: realized vol vs. 60-bar baseline.
    * If 20-bar realized vol >= 1.5x of 60-bar baseline AND slope is moderate,
      classify as breakout (volatility expansion without committed direction).
  - Reversal: a 5-bar swing flipping the sign of the slope inside the 20-bar
    window vs. the prior 20-bar window's slope.
    * Specifically, if prior-window slope was strongly positive (>=+0.5) and
      current-window slope is strongly negative (<=-0.5), or vice versa, label
      reversal. This dominates over trending_bull/bear.
  - Otherwise:
    * Strong slope (and not a reversal) -> trending_bull / trending_bear
    * Weak slope -> chop

This is a coarse 5-class taxonomy. It will not perfectly match every human
discretionary call, but it is reproducible and reasonable for regime-share
comparison.
"""
from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

DATA = Path(r"C:/Users/MSI/Documents/ai-trading-agent/data/historical_2026")
INSTRUMENTS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]


def load_h4(symbol: str) -> list[dict]:
    rows = []
    fp = DATA / f"{symbol}_H4.csv"
    with fp.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "time": datetime.strptime(r["time"], "%Y-%m-%d %H:%M:%S"),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
            })
    return rows


def compute_atr(rows: list[dict], n: int) -> list[float]:
    """Standard ATR(n) — Wilder's. Returns list aligned with rows."""
    trs = []
    for i, r in enumerate(rows):
        if i == 0:
            tr = r["high"] - r["low"]
        else:
            prev_close = rows[i - 1]["close"]
            tr = max(
                r["high"] - r["low"],
                abs(r["high"] - prev_close),
                abs(r["low"] - prev_close),
            )
        trs.append(tr)
    atrs = [float("nan")] * len(rows)
    if len(trs) < n:
        return atrs
    seed = sum(trs[:n]) / n
    atrs[n - 1] = seed
    for i in range(n, len(rows)):
        atrs[i] = (atrs[i - 1] * (n - 1) + trs[i]) / n
    return atrs


def slope_per_bar(closes: list[float]) -> float:
    """Linear regression slope (price units per bar)."""
    if len(closes) < 2:
        return 0.0
    x = np.arange(len(closes), dtype=float)
    y = np.asarray(closes, dtype=float)
    x_mean = x.mean()
    y_mean = y.mean()
    num = ((x - x_mean) * (y - y_mean)).sum()
    den = ((x - x_mean) ** 2).sum()
    return float(num / den) if den > 0 else 0.0


def realized_vol(closes: list[float]) -> float:
    if len(closes) < 2:
        return 0.0
    arr = np.asarray(closes, dtype=float)
    rets = np.diff(arr) / arr[:-1]
    return float(rets.std(ddof=0))


def classify_regimes(rows: list[dict], window: int = 20, vol_baseline: int = 60) -> list[str]:
    atrs = compute_atr(rows, n=14)
    n = len(rows)
    labels = ["unclassified"] * n

    for i in range(n):
        if i < window + vol_baseline:
            labels[i] = "warmup"
            continue
        win_closes = [rows[j]["close"] for j in range(i - window + 1, i + 1)]
        prior_closes = [rows[j]["close"] for j in range(i - 2 * window + 1, i - window + 1)]

        atr_win = float(np.nanmean([atrs[j] for j in range(i - window + 1, i + 1)]))
        if atr_win <= 0 or np.isnan(atr_win):
            labels[i] = "unclassified"
            continue

        slope = slope_per_bar(win_closes)  # price/bar
        slope_norm = slope / atr_win  # ATR/bar units (0.5 means each bar moves 0.5 ATR)
        prior_slope = slope_per_bar(prior_closes)
        prior_slope_norm = prior_slope / atr_win

        rv = realized_vol(win_closes)
        rv_baseline_closes = [rows[j]["close"] for j in range(i - vol_baseline + 1, i + 1)]
        rv_baseline = realized_vol(rv_baseline_closes)
        vol_ratio = rv / rv_baseline if rv_baseline > 0 else 1.0

        # Reversal first: prior window strongly opposite of current
        is_reversal = (
            (prior_slope_norm >= 0.05 and slope_norm <= -0.05)
            or (prior_slope_norm <= -0.05 and slope_norm >= 0.05)
        )
        if is_reversal:
            labels[i] = "reversal"
            continue

        # Breakout: high vol expansion + moderate slope (not a clean trend yet)
        # We require vol_ratio >= 1.5 AND |slope_norm| in (0.02, 0.08).
        if vol_ratio >= 1.5 and 0.02 <= abs(slope_norm) < 0.08:
            labels[i] = "breakout"
            continue

        # Trending vs chop
        if slope_norm >= 0.05:
            labels[i] = "trending_bull"
        elif slope_norm <= -0.05:
            labels[i] = "trending_bear"
        else:
            labels[i] = "chop"

    return labels


def month_of(ts: datetime) -> str:
    return f"{ts.year}-{ts.month:02d}"


def summarize(symbol: str) -> dict:
    rows = load_h4(symbol)
    labels = classify_regimes(rows)
    months = [month_of(r["time"]) for r in rows]
    by_month: dict[str, Counter] = {}
    overall = Counter()
    for r, lbl, m in zip(rows, labels, months):
        if lbl in ("warmup", "unclassified"):
            continue
        by_month.setdefault(m, Counter())[lbl] += 1
        overall[lbl] += 1
    return {
        "symbol": symbol,
        "total_h4": len([l for l in labels if l not in ("warmup", "unclassified")]),
        "overall": dict(overall),
        "by_month": {m: dict(c) for m, c in sorted(by_month.items())},
    }


def main() -> None:
    print("Per-instrument H4 regime distribution (Jan 2 - Apr 10, 2026)")
    print("=" * 80)
    fleet_overall = Counter()
    fleet_by_month: dict[str, Counter] = {}
    for sym in INSTRUMENTS:
        s = summarize(sym)
        print(f"\n{sym}: total classified H4 candles = {s['total_h4']}")
        for k, v in sorted(s["overall"].items(), key=lambda x: -x[1]):
            print(f"  {k:18s} {v:5d}  ({100*v/max(1,s['total_h4']):5.1f}%)")
        for m, c in s["by_month"].items():
            tot = sum(c.values())
            shares = ", ".join(f"{k}={v}({100*v/tot:.0f}%)" for k, v in sorted(c.items(), key=lambda x: -x[1]))
            print(f"    {m}: n={tot} {shares}")
            fleet_by_month.setdefault(m, Counter()).update(c)
        fleet_overall.update(s["overall"])

    print("\nFleet aggregate (5 instruments):")
    fleet_total = sum(fleet_overall.values())
    for k, v in sorted(fleet_overall.items(), key=lambda x: -x[1]):
        print(f"  {k:18s} {v:5d}  ({100*v/fleet_total:5.1f}%)")

    print("\nFleet by month:")
    for m, c in sorted(fleet_by_month.items()):
        tot = sum(c.values())
        shares = ", ".join(f"{k}={v}({100*v/tot:.0f}%)" for k, v in sorted(c.items(), key=lambda x: -x[1]))
        print(f"  {m}: n={tot} {shares}")


if __name__ == "__main__":
    main()
