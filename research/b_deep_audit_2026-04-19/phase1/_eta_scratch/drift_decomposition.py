"""Decompose the JPY-23 SHORT edge and XAUUSD-11 SHORT edge.

Question: is the edge a simple drift (mean price return is negative) or is it a predictable
asymmetric outcome structure?

Test:
  For each instrument×hour slice, compute:
    - Mean 4h forward return (close-to-close over 16 M15 bars)
    - Median forward return
    - Skewness
    - Proportion of positive vs negative 4h returns
  Compare to all hours.
"""
import json
import math
import statistics
from pathlib import Path

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")




def main():
    # Use the feature+outcome dataset; add forward-return to each row by recomputing from CSVs.
    import sys
    sys.path.insert(0, str(OUT_DIR))
    from load_data import load_m15, find_candle_idx_at_or_before

    with open(OUT_DIR / "all_candles_features_outcomes.json", "r", encoding="utf-8") as f:
        d = json.load(f)

    # Build lookup of close prices for each instrument's M15 candles
    all_symbols = sorted(set(r["symbol"] for r in d["rows"]))
    print(f"Loading M15 for: {all_symbols}")
    m15_cache = {}
    for s in all_symbols:
        m15 = load_m15(s)
        # Build time index
        m15_cache[s] = m15
        m15_cache[s + "_time_map"] = {c["time"]: i for i, c in enumerate(m15)}

    from datetime import datetime
    # For each row, compute 4h forward return (t+16 M15 bars' close / current close - 1)
    from collections import defaultdict

    by_inst_hour = defaultdict(list)
    for r in d["rows"]:
        s = r["symbol"]
        # Parse candle_time
        t_str = r["candle_time"]
        try:
            t = datetime.fromisoformat(t_str.replace(" ", "T"))
        except Exception:
            continue
        m15 = m15_cache[s]
        # Find idx by matching time without tz
        t_naive = t.replace(tzinfo=None) if t.tzinfo else t
        # Find in m15_time_map (store as UTC-aware — let's compare by str)
        # Simpler: scan; actually we have time_map keyed on aware datetime.
        # m15_cache already stores candles with aware datetime.
        # Let's just find idx with binary search:
        lo, hi = 0, len(m15) - 1
        tgt = t  # aware datetime
        idx = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if m15[mid]["time"] == tgt:
                idx = mid
                break
            if m15[mid]["time"] < tgt:
                lo = mid + 1
            else:
                hi = mid - 1
        if idx is None or idx + 16 >= len(m15):
            continue
        c0 = m15[idx]["close"]
        c_end = m15[idx + 16]["close"]
        ret_4h = c_end / c0 - 1.0
        # Also 16-bar max high / min low (for skew)
        bars = m15[idx + 1: idx + 17]
        max_up = max((b["high"] for b in bars), default=c0) / c0 - 1.0
        max_dn = min((b["low"] for b in bars), default=c0) / c0 - 1.0

        by_inst_hour[(s, r["hour_utc"])].append({
            "ret_4h": ret_4h,
            "max_up": max_up,
            "max_dn": max_dn,
        })

    summary = []
    for (s, h), vals in sorted(by_inst_hour.items()):
        if len(vals) < 30:
            continue
        rets = [v["ret_4h"] for v in vals]
        mean_ret = statistics.mean(rets)
        med_ret = statistics.median(rets)
        stdev_ret = statistics.stdev(rets)
        pos_frac = sum(1 for r in rets if r > 0) / len(rets)
        max_ups = [v["max_up"] for v in vals]
        max_dns = [v["max_dn"] for v in vals]
        summary.append({
            "instrument": s,
            "hour_utc": h,
            "n": len(vals),
            "mean_ret_4h": mean_ret,
            "median_ret_4h": med_ret,
            "stdev_ret_4h": stdev_ret,
            "pos_frac": pos_frac,
            "mean_max_up": statistics.mean(max_ups),
            "mean_max_dn": statistics.mean(max_dns),
            "skew_proxy": (mean_ret - med_ret) / stdev_ret if stdev_ret else 0,
        })

    # Sort by instrument/hour
    summary.sort(key=lambda x: (x["instrument"], x["hour_utc"]))

    # Print the "strong edge" subset
    strong_set = {
        ("GBPJPY", 23), ("USDJPY", 23), ("GBPUSD", 23),
        ("GBPJPY", 22), ("USDJPY", 22),
        ("GBPJPY", 0), ("USDJPY", 0),
        ("XAUUSD", 11), ("XAUUSD", 12),
        ("USDJPY", 19),
        ("EURUSD", 13), ("EURUSD", 15),
    }

    print(f"\n{'Inst':8s} {'Hr':3s} {'n':4s} {'mean_ret_4h':15s} {'median_4h':10s} {'pos_frac':10s} {'mean_max_up':12s} {'mean_max_dn':12s}")
    print("=" * 90)
    for r in summary:
        if (r["instrument"], r["hour_utc"]) in strong_set:
            print(f"{r['instrument']:8s} {r['hour_utc']:3d} {r['n']:4d} {r['mean_ret_4h']*10000:+7.2f}bp      {r['median_ret_4h']*10000:+6.2f}bp  {r['pos_frac']:.3f}    {r['mean_max_up']*10000:+6.2f}bp   {r['mean_max_dn']*10000:+6.2f}bp")

    print(f"\nFull summary (all inst/hour with n>=30) written to drift_summary.json")
    with open(OUT_DIR / "drift_summary.json", "w", encoding="utf-8") as f:
        json.dump({"rows": summary, "strong_set": list(strong_set)}, f, indent=2)


if __name__ == "__main__":
    main()
