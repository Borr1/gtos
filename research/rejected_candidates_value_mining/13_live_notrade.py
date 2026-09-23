"""
Live NO_TRADE forward resolution (using H1-aligned baseline direction since live evals don't carry MSO direction).
"""
import json
import os
import math
from pathlib import Path
from collections import Counter, defaultdict
from datetime import timedelta
import pandas as pd

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"
DATA_DIR = ROOT / "data/historical_2026"

INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash"]


def load_csv(symbol, tf):
    fp = DATA_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


def m15_atr(m15_df, ts, period=14):
    matches = m15_df.index[m15_df["time"] == ts]
    if len(matches) == 0:
        # Find nearest
        idx_arr = m15_df.index[m15_df["time"] <= ts]
        if len(idx_arr) == 0:
            return None
        idx = int(idx_arr[-1])
    else:
        idx = int(matches[0])
    if idx < period:
        return None
    sub = m15_df.iloc[idx - period: idx + 1]
    h = sub["high"]; l = sub["low"]; c = sub["close"]
    pc = c.shift(1)
    tr = pd.concat([h-l, (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return float(tr.tail(period).mean()), idx


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (lo, hi)


def main():
    h1_dfs = {inst: load_csv(inst, "H1") for inst in INSTRUMENTS}
    m15_dfs = {inst: load_csv(inst, "M15") for inst in INSTRUMENTS}

    le_dir = ROOT / "knowledge_base/live_evaluations"
    all_rows = []
    for inst in os.listdir(le_dir):
        ind = le_dir / inst
        if not ind.is_dir():
            continue
        for fname in os.listdir(ind):
            if not fname.endswith(".jsonl"):
                continue
            with open(ind / fname, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        r["_instrument"] = inst
                        all_rows.append(r)
                    except Exception:
                        pass

    nt_rows = [r for r in all_rows if r.get("decision") == "NO_TRADE"]
    print(f"Live NO_TRADE rows: {len(nt_rows)}")

    # Bucketize
    def bucket(reason):
        if not reason:
            return "no_reason"
        rl = reason.lower()
        if "c1" in rl or "directional bias" in rl or "daily bias" in rl:
            return "c1_failed_or_no_bias"
        if "c2" in rl or "displacement" in rl or "choch" in rl:
            return "c2_or_displacement"
        if "framework" in rl:
            return "framework_unmet"
        if "h1 poi" in rl or "h1 point of interest" in rl or "ob" in rl or "retest" in rl:
            return "no_h1_poi"
        if "unexpected" in rl:
            return "error"
        return "other"

    for r in nt_rows:
        r["bucket"] = bucket(r.get("no_trade_reason"))
    bucket_counts = Counter(r["bucket"] for r in nt_rows)
    print("Live NO_TRADE bucket counts:")
    for k, v in bucket_counts.most_common():
        print(f"  {k}: {v}")

    # Forward resolve using H1-momentum direction
    def resolve(row):
        inst = row["_instrument"]
        if inst not in h1_dfs or h1_dfs[inst] is None:
            return None
        h1 = h1_dfs[inst]
        m15 = m15_dfs[inst]
        ts_str = row.get("candle_time")
        if not ts_str:
            return None
        ts = pd.to_datetime(ts_str, utc=True).floor("15min")
        atr_result = m15_atr(m15, ts)
        if atr_result is None:
            return None
        atr, m15_idx = atr_result
        if not atr or atr <= 0:
            return None
        entry = float(m15.iloc[m15_idx]["close"])
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_idx = h1.index[h1["time"] >= next_h1]
        if len(h1_idx) == 0:
            return None
        h1_start = int(h1_idx[0])
        if h1_start < 5:
            return None
        # H1 momentum direction
        prev = float(h1.iloc[h1_start-1]["close"])
        ref = float(h1.iloc[h1_start-5]["close"])
        direction = "LONG" if prev > ref else "SHORT"
        if direction == "LONG":
            sl = entry - atr; tp = entry + 1.5 * atr
        else:
            sl = entry + atr; tp = entry - 1.5 * atr
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            return None
        for _, c in h1_window.iterrows():
            if direction == "LONG":
                sl_hit = c["low"] <= sl; tp_hit = c["high"] >= tp
            else:
                sl_hit = c["high"] >= sl; tp_hit = c["low"] <= tp
            if sl_hit and tp_hit: return -1.0
            elif sl_hit: return -1.0
            elif tp_hit: return 1.5
        last_close = float(h1_window.iloc[-1]["close"])
        return (last_close - entry) / atr if direction == "LONG" else (entry - last_close) / atr

    # Per bucket
    print()
    print("=== Live NO_TRADE forward-resolution per bucket ===")
    by_bucket = defaultdict(list)
    for r in nt_rows:
        rr = resolve(r)
        if rr is not None:
            by_bucket[r["bucket"]].append(rr)
    for b, rs in sorted(by_bucket.items()):
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.5 - 1e-9)
        total = sum(rs)
        lo, hi = wilson_ci(wins, n)
        print(f"  {b:30s} n={n:4d}, WR={wins/n:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={total/n:+.3f}, TotalR={total:+.1f}")

    # Per instrument
    print()
    print("=== Per-instrument live NO_TRADE ===")
    by_inst = defaultdict(list)
    for r in nt_rows:
        rr = resolve(r)
        if rr is not None:
            by_inst[r["_instrument"]].append(rr)
    for inst, rs in sorted(by_inst.items()):
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.5 - 1e-9)
        total = sum(rs)
        lo, hi = wilson_ci(wins, n)
        print(f"  {inst:12s} n={n:4d}, WR={wins/n:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={total/n:+.3f}, TotalR={total:+.1f}")


if __name__ == "__main__":
    main()
