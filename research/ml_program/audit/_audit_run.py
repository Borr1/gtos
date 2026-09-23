#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K54 v2 Data Inventory Audit -- runs once, writes CSVs to audit/."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Force UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
AUDIT = REPO / "research" / "ml_program" / "audit"
AUDIT.mkdir(parents=True, exist_ok=True)

INSTRUMENTS = ["XAUUSD", "XAGUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash", "NAS100"]
TFS = ["M15", "H1", "H4", "D1"]

DATA_DIRS = [
    REPO / "data" / "historical_2026",
    REPO / "data" / "historical",
    REPO / "data" / "raw",
    REPO / "data" / "old_huggingface_backup",
    REPO / "data",  # top-level CSVs (DXY/EURUSD)
]


# ---------------------------------------------------------------------------
# Q1 — coverage table
# ---------------------------------------------------------------------------

def parse_csv_dates(p: Path) -> tuple[str | None, str | None, int, int]:
    """Return (first_ts, last_ts, row_count, gap_count) for an OHLCV CSV.

    A gap is defined as a >2x-median-spacing jump (excluding weekends 48h+).
    """
    if not p.exists():
        return None, None, 0, 0
    rows = 0
    timestamps: list[str] = []
    try:
        with p.open(encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                return None, None, 0, 0
            for row in reader:
                if not row:
                    continue
                rows += 1
                # First column is time
                timestamps.append(row[0])
    except Exception:
        return None, None, 0, 0
    if not timestamps:
        return None, None, 0, 0
    first, last = timestamps[0], timestamps[-1]
    # Gap detection — only for sub-daily TFs
    gaps = 0
    if len(timestamps) >= 100 and " " in first:  # sub-daily
        # Build dt list, count jumps > 4h (M15/H1) or 12h (H4)
        prev = None
        median_step = None
        steps = []
        for ts in timestamps[:200]:  # sample for median
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d")
                except ValueError:
                    continue
            if prev is not None:
                steps.append((dt - prev).total_seconds())
            prev = dt
        if steps:
            steps.sort()
            median_step = steps[len(steps) // 2]
        if median_step:
            prev = None
            threshold = max(median_step * 5, 4 * 3600)  # 5x median or 4h
            for ts in timestamps:
                try:
                    dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(ts, "%Y-%m-%d")
                    except ValueError:
                        continue
                if prev is not None:
                    delta = (dt - prev).total_seconds()
                    # Skip weekends (Friday→Monday ~65h)
                    if delta > threshold and delta < 60 * 3600:
                        gaps += 1
                prev = dt
    return first, last, rows, gaps


def find_data_file(symbol: str, tf: str) -> Path | None:
    """Search known data dirs for {SYMBOL}_{TF}.csv."""
    candidates: list[Path] = []
    for d in DATA_DIRS:
        # Try exact
        p = d / f"{symbol}_{tf}.csv"
        if p.exists() and not p.is_symlink():
            candidates.append(p)
        elif p.is_symlink():
            # Resolve symlinks (data/historical/GBPUSD_*.csv → data/GBPUSD_*.csv)
            try:
                resolved = p.resolve()
                if resolved.exists():
                    candidates.append(resolved)
            except Exception:
                pass
    # De-dupe by canonical path, prefer largest
    seen: dict[Path, Path] = {}
    for c in candidates:
        try:
            key = c.resolve()
        except Exception:
            key = c
        if key not in seen or c.stat().st_size > seen[key].stat().st_size:
            seen[key] = c
    if not seen:
        return None
    # Pick the file with most rows (largest file is a good proxy)
    best = max(seen.values(), key=lambda p: p.stat().st_size)
    return best


def inventory_coverage() -> list[dict]:
    rows: list[dict] = []
    for sym in INSTRUMENTS:
        # Special case: US30_cash also stored as US30 (legacy)
        for tf in TFS:
            paths_seen: set[Path] = set()
            # Search all data dirs for any *_TF.csv that matches symbol or its alias
            aliases = [sym]
            if sym == "US30_cash":
                aliases.append("US30")
            for alias in aliases:
                for d in DATA_DIRS:
                    p = d / f"{alias}_{tf}.csv"
                    if not p.exists():
                        continue
                    try:
                        real = p.resolve()
                    except Exception:
                        real = p
                    if real in paths_seen:
                        continue
                    paths_seen.add(real)
                    first, last, n_rows, gaps = parse_csv_dates(p)
                    if n_rows == 0:
                        continue
                    rows.append({
                        "symbol": sym,
                        "tf": tf,
                        "source_path": str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p),
                        "first_ts": first or "",
                        "last_ts": last or "",
                        "rows": n_rows,
                        "gaps_detected": gaps,
                    })
    return rows


# ---------------------------------------------------------------------------
# Q2 — cross-period replication
# ---------------------------------------------------------------------------

def count_m15_per_period(coverage: list[dict]) -> dict:
    """Per-instrument M15 candle counts split into 2022-2023, 2024-2025, 2026."""
    out: dict[str, dict[str, int]] = defaultdict(lambda: {"2022-2023": 0, "2024-2025": 0, "2026": 0})
    for sym in INSTRUMENTS:
        # Get all M15 sources for this instrument
        m15_sources = [r for r in coverage if r["symbol"] == sym and r["tf"] == "M15"]
        # We need to count rows per period; since CSV is small enough, parse each one
        for src in m15_sources:
            p_str = src["source_path"]
            p = REPO / p_str if not Path(p_str).is_absolute() else Path(p_str)
            if not p.exists():
                continue
            try:
                with p.open(encoding="utf-8") as fh:
                    reader = csv.reader(fh)
                    next(reader, None)
                    for row in reader:
                        if not row or not row[0]:
                            continue
                        try:
                            yr = int(row[0][:4])
                        except ValueError:
                            continue
                        if 2022 <= yr <= 2023:
                            out[sym]["2022-2023"] += 1
                        elif 2024 <= yr <= 2025:
                            out[sym]["2024-2025"] += 1
                        elif yr == 2026:
                            out[sym]["2026"] += 1
            except Exception:
                continue
    return dict(out)


# ---------------------------------------------------------------------------
# Q3 — per-instrument trade cohort distribution
# ---------------------------------------------------------------------------

def load_features_csv() -> list[dict]:
    """Read K54 v1 features.csv from worktree."""
    path = REPO / ".claude" / "worktrees" / "agent-a01c00db65592ac2b" / "research" / "k54_ml_classifier_baseline" / "features.csv"
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows


def parse_period(date_iso: str) -> str:
    if not date_iso:
        return "unknown"
    try:
        yr = int(date_iso[:4])
    except ValueError:
        return "unknown"
    if 2022 <= yr <= 2023:
        return "2022-2023"
    if 2024 <= yr <= 2025:
        return "2024-2025"
    if yr == 2026:
        return "2026"
    return "unknown"


def trade_cohort_summary(features: list[dict]) -> dict:
    out = {
        "total_rows": len(features),
        "by_symbol": Counter(r["symbol"] for r in features),
        "by_source": Counter(r["source"] for r in features),
        "by_period": defaultdict(Counter),  # period → symbol counts
        "by_regime": defaultdict(Counter),  # regime → symbol counts
        "by_period_x_regime": defaultdict(Counter),  # (period, regime) → symbol counts
        "by_symbol_x_period": defaultdict(Counter),  # symbol → period counts
        "by_symbol_x_source": defaultdict(Counter),  # symbol → source counts
    }
    for r in features:
        sym = r["symbol"]
        src = r["source"]
        period = parse_period(r.get("date_iso", ""))
        regime = r.get("regime_tag", "") or "UNTAGGED"
        out["by_period"][period][sym] += 1
        out["by_regime"][regime][sym] += 1
        out["by_period_x_regime"][(period, regime)][sym] += 1
        out["by_symbol_x_period"][sym][period] += 1
        out["by_symbol_x_source"][sym][src] += 1
    return out


# ---------------------------------------------------------------------------
# Q4 — D1 direction distribution
# ---------------------------------------------------------------------------

def d1_direction_stats(coverage: list[dict]) -> dict:
    """Per (symbol, period) compute D1 swing direction approx via close > open."""
    stats: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "bullish": 0, "bearish": 0, "ranging": 0, "total": 0
    })
    for sym in INSTRUMENTS:
        d1 = [r for r in coverage if r["symbol"] == sym and r["tf"] == "D1"]
        if not d1:
            continue
        # Pick the largest D1 file
        src = max(d1, key=lambda r: r["rows"])
        p_str = src["source_path"]
        p = REPO / p_str if not Path(p_str).is_absolute() else Path(p_str)
        if not p.exists():
            continue
        try:
            with p.open(encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                # Header detection — csv.DictReader handles
                for row in reader:
                    ts = row.get("time") or row.get("date") or row.get("timestamp") or ""
                    if not ts:
                        continue
                    try:
                        yr = int(ts[:4])
                    except ValueError:
                        continue
                    if 2022 <= yr <= 2023:
                        period = "2022-2023"
                    elif 2024 <= yr <= 2025:
                        period = "2024-2025"
                    elif yr == 2026:
                        period = "2026"
                    else:
                        period = "other"
                    if period == "other":
                        continue
                    try:
                        op = float(row.get("open", "") or row.get("Open", "") or 0)
                        cl = float(row.get("close", "") or row.get("Close", "") or 0)
                        hi = float(row.get("high", "") or row.get("High", "") or 0)
                        lo = float(row.get("low", "") or row.get("Low", "") or 0)
                    except ValueError:
                        continue
                    rng = hi - lo if hi > lo else 0
                    body = abs(cl - op)
                    # Ranging = body < 25% of range (matches H4-swing-style detection)
                    key = (sym, period)
                    stats[key]["total"] += 1
                    if rng > 0 and body / rng < 0.25:
                        stats[key]["ranging"] += 1
                    elif cl > op:
                        stats[key]["bullish"] += 1
                    else:
                        stats[key]["bearish"] += 1
        except Exception:
            continue
    # Convert to dict-of-dicts
    out = {}
    for (sym, period), counts in stats.items():
        out[f"{sym}|{period}"] = counts
    return out


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("K54 v2 Data Inventory Audit")
    print(f"Repo: {REPO}")
    print(f"Output: {AUDIT}")
    print("=" * 70)

    # Q1 — Coverage
    print("\n[Q1] Inventorying coverage...")
    coverage = inventory_coverage()
    print(f"  Found {len(coverage)} (symbol, TF, source) entries")
    cov_csv = AUDIT / "coverage_table.csv"
    with cov_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["symbol", "tf", "source_path", "first_ts", "last_ts", "rows", "gaps_detected"])
        w.writeheader()
        for r in sorted(coverage, key=lambda x: (x["symbol"], x["tf"], x["source_path"])):
            w.writerow(r)
    print(f"  Wrote {cov_csv}")

    # Q2 — Cross-period
    print("\n[Q2] Counting M15 per period...")
    period_counts = count_m15_per_period(coverage)
    pc_csv = AUDIT / "m15_per_period.csv"
    with pc_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["symbol", "period_2022_2023", "period_2024_2025", "period_2026"])
        for sym in INSTRUMENTS:
            counts = period_counts.get(sym, {"2022-2023": 0, "2024-2025": 0, "2026": 0})
            w.writerow([sym, counts.get("2022-2023", 0), counts.get("2024-2025", 0), counts.get("2026", 0)])
    print(f"  Wrote {pc_csv}")

    # Q3 — Trade cohort
    print("\n[Q3] Analyzing K54 v1 features.csv trade cohort...")
    features = load_features_csv()
    print(f"  Loaded {len(features)} feature rows from K54 v1")
    cohort = trade_cohort_summary(features)
    cohort_csv = AUDIT / "trade_cohort.csv"
    with cohort_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["dimension", "key", "subkey", "count"])
        for sym, n in cohort["by_symbol"].items():
            w.writerow(["by_symbol", sym, "", n])
        for src, n in cohort["by_source"].items():
            w.writerow(["by_source", src, "", n])
        for period, sym_counts in cohort["by_period"].items():
            for sym, n in sym_counts.items():
                w.writerow(["by_period", period, sym, n])
        for regime, sym_counts in cohort["by_regime"].items():
            for sym, n in sym_counts.items():
                w.writerow(["by_regime", regime, sym, n])
        for (period, regime), sym_counts in cohort["by_period_x_regime"].items():
            for sym, n in sym_counts.items():
                w.writerow(["by_period_x_regime", f"{period}|{regime}", sym, n])
    print(f"  Wrote {cohort_csv}")

    # Q4 — D1 direction
    print("\n[Q4] Computing D1 direction distribution...")
    d1 = d1_direction_stats(coverage)
    d1_csv = AUDIT / "d1_direction.csv"
    with d1_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["symbol", "period", "bullish", "bearish", "ranging", "total", "pct_bullish", "pct_bearish", "pct_ranging"])
        for k, v in sorted(d1.items()):
            sym, period = k.split("|")
            tot = v["total"]
            if tot == 0:
                continue
            w.writerow([
                sym, period,
                v["bullish"], v["bearish"], v["ranging"], tot,
                f"{100*v['bullish']/tot:.1f}",
                f"{100*v['bearish']/tot:.1f}",
                f"{100*v['ranging']/tot:.1f}",
            ])
    print(f"  Wrote {d1_csv}")

    # Compact summary print
    print("\n" + "=" * 70)
    print("Q1 COVERAGE SUMMARY (per symbol per TF — pick best source)")
    print("=" * 70)
    by_st: dict[tuple[str, str], dict] = {}
    for r in coverage:
        key = (r["symbol"], r["tf"])
        if key not in by_st or r["rows"] > by_st[key]["rows"]:
            by_st[key] = r
    for sym in INSTRUMENTS:
        for tf in TFS:
            r = by_st.get((sym, tf))
            if r:
                print(f"  {sym:12s} {tf:4s}  {r['rows']:>7d} rows  {r['first_ts']} → {r['last_ts']}  gaps={r['gaps_detected']}  ({r['source_path']})")
            else:
                print(f"  {sym:12s} {tf:4s}  MISSING")

    print("\n" + "=" * 70)
    print("Q2 CROSS-PERIOD M15 COUNTS")
    print("=" * 70)
    feasible = 0
    for sym in INSTRUMENTS:
        c = period_counts.get(sym, {})
        a = c.get("2022-2023", 0)
        b = c.get("2024-2025", 0)
        d = c.get("2026", 0)
        periods_ok = sum(1 for x in (a, b, d) if x >= 1000)
        flag = "OK" if periods_ok >= 2 else "INSUFFICIENT"
        if periods_ok >= 2:
            feasible += 1
        print(f"  {sym:12s}  2022-23={a:>6d}  2024-25={b:>6d}  2026={d:>6d}  periods≥1000={periods_ok}  {flag}")
    print(f"\n  Feasibility: {feasible}/7 instruments support cross-period replication.")

    print("\n" + "=" * 70)
    print("Q3 TRADE COHORT")
    print("=" * 70)
    print(f"  Total rows: {cohort['total_rows']}")
    print(f"  By source: {dict(cohort['by_source'])}")
    print(f"  By symbol: {dict(cohort['by_symbol'])}")
    print(f"\n  Per-symbol × period:")
    for sym in INSTRUMENTS:
        sym_u = sym.upper()
        # K54 features uses upper-case; US30_cash is stored as US30_CASH
        key_lookup = sym_u if sym_u != "US30_CASH" else "US30_CASH"
        per = cohort["by_symbol_x_period"].get(key_lookup, Counter())
        per_str = " ".join(f"{p}={n}" for p, n in sorted(per.items()))
        print(f"    {sym:12s}  {per_str}")
    print(f"\n  Per-symbol × regime (n<30 cells flagged):")
    for sym in INSTRUMENTS:
        sym_u = sym.upper()
        regime_counts = Counter()
        for r in features:
            if r["symbol"].upper() == sym_u:
                regime_counts[r.get("regime_tag", "") or "UNTAGGED"] += 1
        flagged = []
        for reg, n in regime_counts.items():
            tag = " [LOW-N]" if n < 30 else ""
            flagged.append(f"{reg}={n}{tag}")
        print(f"    {sym:12s}  {'  '.join(flagged)}")

    print("\n" + "=" * 70)
    print("Q4 D1 DIRECTION DISTRIBUTION")
    print("=" * 70)
    for sym in INSTRUMENTS:
        for period in ("2022-2023", "2024-2025", "2026"):
            v = d1.get(f"{sym}|{period}")
            if not v or v["total"] == 0:
                print(f"  {sym:12s} {period:10s}  N/A")
                continue
            tot = v["total"]
            print(f"  {sym:12s} {period:10s}  bull={v['bullish']:>4d} ({100*v['bullish']/tot:5.1f}%)  bear={v['bearish']:>4d} ({100*v['bearish']/tot:5.1f}%)  range={v['ranging']:>4d} ({100*v['ranging']/tot:5.1f}%)  N={tot}")

    print("\nDone.")
    return coverage, period_counts, cohort, d1, features


if __name__ == "__main__":
    main()
