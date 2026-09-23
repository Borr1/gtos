"""Compute per-feature Spearman rank correlation vs realized R.

Stability scoring per K54 v2 LIQUIDITY-family agent brief, hard
constraint #6: "Spearman rank correlation of feature value at
trade-entry-candle-close vs realized R, on pre-2026-04 data only."

This script is one-shot: writes the scores to
`research/ml_program/feature_catalogs/liquidity_stability_scores.json`
(consumed by `liquidity.csv` and `liquidity.md`).

Data sources
------------
* Trade outcomes: `research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl`
  Filter: `ob_retest.realized_r != null` AND `bos.bos_time < 2026-04-01`.
  Result: ~345 rows across 7 instruments (XAUUSD/GBPUSD/GBPJPY/USDJPY/
  US30_cash/NAS100/XAGUSD), Jan-Mar 2026.
* OHLCV: `data/historical_2026/{SYMBOL}_{TF}.csv`, M15+H1+H4. UTC.

Stability score
---------------
Spearman rank correlation = Pearson on ranks. NaN-safe via dropna.
We report per-feature:
  - n: row count after dropna
  - rho: Spearman rho
  - tied_with_constant_pct: pct of rows with the modal value (used to
                             flag "almost-constant" features)

Sample size threshold: n >= 30 to report a non-NaN rho.

Output
------
JSON dict {feature_name: {n, rho, tied_pct, abs_rho}} sorted by abs_rho desc.

Inference cost
--------------
~3-4 minutes wallclock on tier-4 CPU for 345 trades x 7 instruments x
~140 features. Acceptable for one-shot stability profiling; will not
run in production.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "research" / "ml_program" / "scripts" / "features"))
import liquidity  # type: ignore  # noqa: E402


F11_PATH = REPO_ROOT / "research" / "edge_decomposition" / "F11_ob_zone_original_geometry" / "population.jsonl"
DATA_DIR = REPO_ROOT / "data" / "historical_2026"
OUT_PATH = REPO_ROOT / "research" / "ml_program" / "feature_catalogs" / "liquidity_stability_scores.json"

CUTOFF_BEFORE = "2026-04-01"  # Pre-2026-04 only — see hard constraint #6


def parse_csv_to_candles(path: Path) -> list[dict]:
    """Parse OHLCV CSV (time,open,high,low,close,volume) -> list[dict]."""
    candles: list[dict] = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(float(row["volume"])) if row["volume"] else 0,
            })
    return candles


def load_ohlcv_for_symbol(symbol: str) -> dict[str, list[dict]]:
    """Return dict {M15, H1, H4} of candle lists for this symbol.

    Falls back to None if a TF file is missing.
    """
    out: dict[str, list[dict]] = {}
    # F11 uses "US30_cash" and "NAS100"; CSV files are named the same
    # except XAUUSD/USDJPY/etc. Direct mapping.
    candidates = [symbol]
    if symbol == "US30_cash":
        candidates.append("US30_cash")
    for tf in ("M15", "H1", "H4"):
        for cand in candidates:
            path = DATA_DIR / f"{cand}_{tf}.csv"
            if path.exists():
                out[tf] = parse_csv_to_candles(path)
                break
        else:
            out[tf] = []
    return out


def find_candle_idx(candles: list[dict], target_time: str) -> int:
    """Find index of candle whose time matches target_time (string compare).

    Returns -1 if not found. Uses string compare since CSV times and
    F11 timestamps are both ISO-ish UTC.
    """
    # Normalize: F11 "2026-01-05T17:00:00+00:00" -> "2026-01-05 17:00:00"
    if "T" in target_time:
        date_part, time_part = target_time.split("T")
        time_part = time_part.split("+")[0].split(".")[0]
        target = f"{date_part} {time_part}"
    else:
        target = target_time
    for i, c in enumerate(candles):
        if c["time"] == target:
            return i
    return -1


def find_candle_idx_at_or_before(candles: list[dict], target_time: str) -> int:
    """Find the largest index i such that candles[i]['time'] <= target_time.

    Used when an exact match isn't available (different TF granularity).
    """
    if "T" in target_time:
        date_part, time_part = target_time.split("T")
        time_part = time_part.split("+")[0].split(".")[0]
        target = f"{date_part} {time_part}"
    else:
        target = target_time
    last_idx = -1
    for i, c in enumerate(candles):
        if c["time"] <= target:
            last_idx = i
        else:
            break
    return last_idx


def spearman_rho(xs: list[float], ys: list[float]) -> tuple[float, int]:
    """Spearman rho via Pearson on ranks. NaN-pair drop.

    Returns (rho, n_after_dropna).
    """
    paired = [
        (x, y) for x, y in zip(xs, ys)
        if x is not None and y is not None
        and not (isinstance(x, float) and math.isnan(x))
        and not (isinstance(y, float) and math.isnan(y))
    ]
    n = len(paired)
    if n < 30:
        return float("nan"), n
    xs_, ys_ = zip(*paired)
    # Rank with average-tie handling
    rx = _rank(list(xs_))
    ry = _rank(list(ys_))
    return _pearson(rx, ry), n


def _rank(arr: list[float]) -> list[float]:
    """Average rank (handles ties)."""
    indexed = sorted(range(len(arr)), key=lambda i: arr[i])
    ranks = [0.0] * len(arr)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and arr[indexed[j + 1]] == arr[indexed[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def tied_pct(values: list[float]) -> float:
    """Fraction of values equal to the mode (NaN-excluded)."""
    finite = [v for v in values if v is not None and isinstance(v, (int, float)) and not math.isnan(v)]
    if not finite:
        return float("nan")
    from collections import Counter
    c = Counter(finite)
    mode_count = max(c.values())
    return mode_count / len(finite)


def main():
    t0 = time.time()
    # Load F11 records, filter to realized_r + pre-cutoff
    print(f"Loading F11 records from {F11_PATH}", flush=True)
    records: list[dict] = []
    with open(F11_PATH) as f:
        for line in f:
            rec = json.loads(line)
            ob_retest = rec.get("ob_retest", {})
            r = ob_retest.get("realized_r")
            if r is None:
                continue
            bos_time = rec["bos"]["bos_time"]
            if bos_time >= CUTOFF_BEFORE + "T00:00:00+00:00":
                continue
            records.append(rec)
    print(f"Pre-cutoff records w/ realized_r: {len(records)}")
    # Group by symbol (load OHLCV once per symbol)
    by_symbol: dict[str, list[dict]] = {}
    for r in records:
        by_symbol.setdefault(r["bos"]["symbol"], []).append(r)
    # Run feature extraction
    feature_rows: list[dict[str, float]] = []
    realized_r_list: list[float] = []
    for symbol, recs in by_symbol.items():
        print(f"\nLoading OHLCV for {symbol} ...", flush=True)
        candles_by_tf = load_ohlcv_for_symbol(symbol)
        if not all(candles_by_tf.get(tf) for tf in ("M15", "H1", "H4")):
            print(f"  Missing OHLCV for {symbol} (have {[tf for tf,c in candles_by_tf.items() if c]}); skipping {len(recs)} records.")
            continue
        for r in recs:
            bos = r["bos"]
            ob_retest = r["ob_retest"]
            bos_time = bos["bos_time"]
            current_price = bos["bos_close"]
            direction = bos.get("direction", "LONG")
            # Find anchor on each TF
            h1_idx = find_candle_idx(candles_by_tf["H1"], bos_time)
            if h1_idx < 0:
                # Try at-or-before
                h1_idx = find_candle_idx_at_or_before(candles_by_tf["H1"], bos_time)
            m15_idx = find_candle_idx_at_or_before(candles_by_tf["M15"], bos_time)
            h4_idx = find_candle_idx_at_or_before(candles_by_tf["H4"], bos_time)
            if h1_idx < 0 or m15_idx < 0 or h4_idx < 0:
                continue
            anchor_idx_by_tf = {"M15": m15_idx, "H1": h1_idx, "H4": h4_idx}
            try:
                feats = liquidity.extract_liquidity_features(
                    candles_by_tf=candles_by_tf,
                    anchor_idx_by_tf=anchor_idx_by_tf,
                    instrument=symbol,
                    side=direction,
                    current_price=current_price,
                )
            except Exception as e:
                print(f"  ERROR on {symbol} {bos_time}: {e}")
                continue
            feature_rows.append(feats)
            realized_r_list.append(float(ob_retest["realized_r"]))
        elapsed = time.time() - t0
        print(f"  {symbol}: {len([r2 for r2 in recs if True])} records processed (elapsed {elapsed:.1f}s)")
    print(f"\nTotal feature rows: {len(feature_rows)}")
    # Compute Spearman per feature
    if not feature_rows:
        print("No rows; aborting.")
        return
    all_keys = set()
    for row in feature_rows:
        all_keys.update(row.keys())
    all_keys_sorted = sorted(all_keys)
    scores: dict[str, dict[str, float]] = {}
    for k in all_keys_sorted:
        vals = [row.get(k, float("nan")) for row in feature_rows]
        rho, n = spearman_rho(vals, realized_r_list)
        scores[k] = {
            "n": n,
            "rho": float(rho) if not math.isnan(rho) else None,
            "abs_rho": abs(rho) if not math.isnan(rho) else None,
            "tied_pct": tied_pct(vals),
        }
    # Sort by abs_rho desc
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({
            "metadata": {
                "n_records": len(feature_rows),
                "cutoff_before": CUTOFF_BEFORE,
                "data_source": "F11 population.jsonl",
                "computed_at_utc": datetime.utcnow().isoformat() + "Z",
                "wallclock_sec": round(time.time() - t0, 2),
            },
            "scores": scores,
        }, f, indent=2, default=str)
    print(f"Wrote scores to {OUT_PATH}")
    # Print top-10 by |rho|
    finite_scores = [
        (k, v) for k, v in scores.items()
        if v["rho"] is not None
    ]
    finite_scores.sort(key=lambda kv: -kv[1]["abs_rho"])
    print(f"\nTop-10 |rho| (pre-2026-04 cohort):")
    for k, v in finite_scores[:10]:
        print(f"  {k}: rho={v['rho']:+.4f} n={v['n']} tied_pct={v['tied_pct']:.2%}")


if __name__ == "__main__":
    main()
