#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K54 v2 — D1 5-bar direction analysis (matches MTF feature definition).

Two outputs:
  1. d1_5bar_ohlcv_distribution.csv — per (symbol, period), distribution of
     D1 5-bar direction (close[i] vs close[i-5]) across all OHLCV bars.
     Threshold: ±0.5% per `regime.csv:1212` definition.
  2. d1_5bar_trade_cohort.csv — per (symbol, period), distribution of
     D1 5-bar direction at trade timestamps in the K54 v1 features.csv.

Saturation criterion: a (symbol, period) is "saturated" if any single
direction (bull / bear / neutral) holds ≥80% of the cohort. Variance-
starved if neutral cell ≤10% (extreme directional bias either way).
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
AUDIT = REPO / "research" / "ml_program" / "audit"

INSTRUMENTS = ["XAUUSD", "XAGUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash", "NAS100"]
FEATURES_CSV = (
    REPO / ".claude" / "worktrees" / "agent-a01c00db65592ac2b"
    / "research" / "k54_ml_classifier_baseline" / "features.csv"
)


def find_d1(sym: str) -> Path | None:
    """Pick best D1 source: prefer historical/ (longest history), then top-level."""
    candidates = [
        REPO / "data" / "historical" / f"{sym}_D1.csv",
        REPO / "data" / f"{sym}_D1.csv",
    ]
    for c in candidates:
        if c.exists() and not c.is_symlink():
            return c
    for c in candidates:
        if c.exists():
            try:
                return c.resolve()
            except Exception:
                pass
    return None


def load_d1_sorted(sym: str) -> tuple[list[str], list[float]]:
    p = find_d1(sym)
    if not p:
        return [], []
    rows = []
    with p.open(encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        for row in r:
            ts = row.get("time") or row.get("date") or ""
            try:
                close = float(row.get("close", "") or row.get("Close", "") or 0)
            except (TypeError, ValueError):
                continue
            d = ts[:10]
            if d:
                rows.append((d, close))
    rows.sort()
    return [d for d, _ in rows], [c for _, c in rows]


def period_of(yr: int) -> str | None:
    if 2022 <= yr <= 2023:
        return "2022-2023"
    if 2024 <= yr <= 2025:
        return "2024-2025"
    if yr == 2026:
        return "2026"
    return None


def d1_dir(c_now: float, c_5ago: float, threshold: float = 0.005) -> str:
    if c_5ago == 0:
        return "skip"
    chg = (c_now - c_5ago) / c_5ago
    if chg > threshold:
        return "bull"
    if chg < -threshold:
        return "bear"
    return "neutral"


def ohlcv_distribution() -> list[dict]:
    out = []
    for sym in INSTRUMENTS:
        dates, closes = load_d1_sorted(sym)
        if not dates:
            continue
        per_period: dict[str, Counter] = {}
        for i in range(5, len(dates)):
            try:
                yr = int(dates[i][:4])
            except ValueError:
                continue
            period = period_of(yr)
            if not period:
                continue
            direction = d1_dir(closes[i], closes[i - 5])
            if direction == "skip":
                continue
            per_period.setdefault(period, Counter())[direction] += 1
        for period, c in per_period.items():
            tot = sum(c.values())
            if tot == 0:
                continue
            out.append({
                "symbol": sym,
                "period": period,
                "bull": c["bull"],
                "bear": c["bear"],
                "neutral": c["neutral"],
                "total": tot,
                "pct_bull": round(100 * c["bull"] / tot, 1),
                "pct_bear": round(100 * c["bear"] / tot, 1),
                "pct_neutral": round(100 * c["neutral"] / tot, 1),
                "saturated": any(c[k] / tot >= 0.80 for k in ("bull", "bear", "neutral")),
                "variance_starved": (c["neutral"] / tot) <= 0.10,
            })
    return out


def trade_cohort_distribution() -> list[dict]:
    if not FEATURES_CSV.exists():
        print(f"WARN: features.csv not found at {FEATURES_CSV}")
        return []
    # Build per-symbol D1 lookup
    d1_lookup: dict[str, tuple[list[str], list[float]]] = {}
    for sym in INSTRUMENTS:
        d1_lookup[sym] = load_d1_sorted(sym)

    def lookup_dir(sym: str, target_date: str) -> str | None:
        dates, closes = d1_lookup.get(sym, ([], []))
        if not dates or target_date < dates[0]:
            return None
        lo, hi = 0, len(dates) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if dates[mid] <= target_date:
                lo = mid
            else:
                hi = mid - 1
        i = lo
        if i < 5:
            return None
        return d1_dir(closes[i], closes[i - 5])

    per: dict[tuple[str, str], Counter] = {}
    with FEATURES_CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sym_u = row["symbol"].upper()
            sym = "US30_cash" if sym_u == "US30_CASH" else sym_u
            di = row.get("date_iso", "")[:10]
            if not di:
                continue
            try:
                yr = int(di[:4])
            except ValueError:
                continue
            period = period_of(yr)
            if not period:
                continue
            d = lookup_dir(sym, di)
            if d in (None, "skip"):
                continue
            per.setdefault((sym, period), Counter())[d] += 1

    out = []
    for (sym, period), c in sorted(per.items()):
        tot = sum(c.values())
        if tot == 0:
            continue
        out.append({
            "symbol": sym,
            "period": period,
            "trade_n": tot,
            "bull": c["bull"],
            "bear": c["bear"],
            "neutral": c["neutral"],
            "pct_bull": round(100 * c["bull"] / tot, 1),
            "pct_bear": round(100 * c["bear"] / tot, 1),
            "pct_neutral": round(100 * c["neutral"] / tot, 1),
            "saturated": any(c[k] / tot >= 0.80 for k in ("bull", "bear", "neutral")),
            "variance_starved": (c["neutral"] / tot) <= 0.10,
        })
    return out


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)

    ohlcv = ohlcv_distribution()
    p1 = AUDIT / "d1_5bar_ohlcv_distribution.csv"
    with p1.open("w", encoding="utf-8", newline="") as fh:
        if ohlcv:
            w = csv.DictWriter(fh, fieldnames=list(ohlcv[0].keys()))
            w.writeheader()
            for r in ohlcv:
                w.writerow(r)
    print(f"Wrote {p1} ({len(ohlcv)} rows)")

    cohort = trade_cohort_distribution()
    p2 = AUDIT / "d1_5bar_trade_cohort.csv"
    with p2.open("w", encoding="utf-8", newline="") as fh:
        if cohort:
            w = csv.DictWriter(fh, fieldnames=list(cohort[0].keys()))
            w.writeheader()
            for r in cohort:
                w.writerow(r)
    print(f"Wrote {p2} ({len(cohort)} rows)")

    # Summary print
    print("\n=== D1 5-bar OHLCV-derived distribution (per period) ===")
    for r in ohlcv:
        flags = []
        if r["saturated"]:
            flags.append("SATURATED")
        if r["variance_starved"]:
            flags.append("VARIANCE-STARVED")
        flag = "  [" + " ".join(flags) + "]" if flags else ""
        print(
            f"  {r['symbol']:10s} {r['period']:10s}  "
            f"bull={r['pct_bull']:5.1f}%  bear={r['pct_bear']:5.1f}%  "
            f"neutral={r['pct_neutral']:5.1f}%  N={r['total']}{flag}"
        )

    print("\n=== D1 5-bar at trade timestamps (K54 v1 cohort) ===")
    for r in cohort:
        flags = []
        if r["saturated"]:
            flags.append("SATURATED")
        if r["variance_starved"]:
            flags.append("VARIANCE-STARVED")
        flag = "  [" + " ".join(flags) + "]" if flags else ""
        print(
            f"  {r['symbol']:10s} {r['period']:10s}  trades={r['trade_n']:>3d}  "
            f"bull={r['pct_bull']:5.1f}%  bear={r['pct_bear']:5.1f}%  "
            f"neutral={r['pct_neutral']:5.1f}%{flag}"
        )


if __name__ == "__main__":
    main()
