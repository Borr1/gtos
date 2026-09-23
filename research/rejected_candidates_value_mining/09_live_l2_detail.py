"""
Re-run live L2 analysis with proper extraction from level2_verification.checks.
"""
import json
import os
from pathlib import Path
from datetime import timedelta
from collections import Counter, defaultdict
import pandas as pd
import math

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


def get_l2_failed_check(trade):
    l2 = trade.get("decision_pipeline", {}).get("level2_verification", {})
    if not isinstance(l2, dict):
        return None
    checks = l2.get("checks", [])
    for c in checks:
        if c.get("status") == "FAIL":
            return c.get("name")
    return None


def main():
    h1_dfs = {}
    for inst in INSTRUMENTS:
        h1_dfs[inst] = load_csv(inst, "H1")

    tr_dir = ROOT / "knowledge_base/trade_records"
    trades = []
    for inst in os.listdir(tr_dir):
        ind = tr_dir / inst
        if not ind.is_dir():
            continue
        for fname in os.listdir(ind):
            if fname.endswith(".json"):
                with open(ind / fname, "r") as f:
                    try:
                        t = json.load(f)
                        t["_instrument"] = inst
                        t["_file"] = fname
                        trades.append(t)
                    except Exception:
                        pass

    l2_rejected = [t for t in trades if t.get("decision_pipeline", {}).get("final_outcome") == "REJECTED_L2"]
    print(f"Live L2 rejected: {len(l2_rejected)}")

    # Failed-check distribution
    failed_checks = Counter()
    for t in l2_rejected:
        fc = get_l2_failed_check(t)
        failed_checks[str(fc)] += 1
    print(f"Failed L2 check distribution:")
    for k, v in failed_checks.most_common():
        print(f"  {v}: {k}")

    def resolve(trade):
        inst = trade["_instrument"]
        if inst not in h1_dfs or h1_dfs[inst] is None:
            return None
        h1 = h1_dfs[inst]
        ts_str = trade.get("metadata", {}).get("candle_time")
        if not ts_str:
            return None
        ts = pd.to_datetime(ts_str, utc=True)
        tp = trade.get("trade_parameters", {})
        direction = tp.get("direction")
        entry = tp.get("entry_price")
        sl = tp.get("stop_loss")
        tp1 = tp.get("take_profit_1")
        if direction is None or entry is None or sl is None or tp1 is None:
            return None
        entry = float(entry); sl = float(sl); tp1 = float(tp1)
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_matches = h1.index[h1["time"] >= next_h1]
        if len(h1_matches) == 0:
            return None
        h1_start = int(h1_matches[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            return None
        r_unit = abs(entry - sl)
        if r_unit == 0:
            return None
        for _, c in h1_window.iterrows():
            if direction == "LONG":
                sl_hit = c["low"] <= sl
                tp_hit = c["high"] >= tp1
            else:
                sl_hit = c["high"] >= sl
                tp_hit = c["low"] <= tp1
            if sl_hit and tp_hit:
                return -1.0
            elif sl_hit:
                return -1.0
            elif tp_hit:
                if direction == "LONG":
                    r = (tp1 - entry) / r_unit
                else:
                    r = (entry - tp1) / r_unit
                return r
        last_close = float(h1_window.iloc[-1]["close"])
        if direction == "LONG":
            r = (last_close - entry) / r_unit
        else:
            r = (entry - last_close) / r_unit
        return r

    # Per failed check
    print()
    print("Per-check forward-resolution:")
    by_check = defaultdict(list)
    for t in l2_rejected:
        fc = get_l2_failed_check(t)
        by_check[str(fc)].append(t)
    for check, ts in sorted(by_check.items()):
        rs = [resolve(t) for t in ts]
        rs = [r for r in rs if r is not None]
        if not rs:
            continue
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        lo, hi = wilson_ci(wins, n)
        print(f"  {check:20s}: n={n}, WR={wins/n:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={sum(rs)/n:+.3f}, TotalR={sum(rs):+.1f}")

    # Per instrument
    print()
    print("Per-instrument live L2 resolution:")
    by_inst = defaultdict(list)
    for t in l2_rejected:
        by_inst[t["_instrument"]].append(t)
    for inst, ts in sorted(by_inst.items()):
        rs = [resolve(t) for t in ts]
        rs = [r for r in rs if r is not None]
        if not rs:
            continue
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        lo, hi = wilson_ci(wins, n)
        print(f"  {inst:14s}: n={n}, WR={wins/n:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={sum(rs)/n:+.3f}, TotalR={sum(rs):+.1f}")

    # Per direction
    print()
    print("Per-direction live L2 resolution:")
    by_dir = defaultdict(list)
    for t in l2_rejected:
        d = t.get("trade_parameters", {}).get("direction", "UNK")
        by_dir[d].append(t)
    for d, ts in sorted(by_dir.items()):
        rs = [resolve(t) for t in ts]
        rs = [r for r in rs if r is not None]
        if not rs:
            continue
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        lo, hi = wilson_ci(wins, n)
        print(f"  {d:6s}: n={n}, WR={wins/n:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={sum(rs)/n:+.3f}, TotalR={sum(rs):+.1f}")

    # Save full detail for csv
    rows = []
    for t in l2_rejected:
        r = resolve(t)
        rows.append({
            "trade_id": t.get("metadata", {}).get("trade_id"),
            "_instrument": t["_instrument"],
            "candle_time": t.get("metadata", {}).get("candle_time"),
            "kill_zone": t.get("metadata", {}).get("kill_zone"),
            "direction": t.get("trade_parameters", {}).get("direction"),
            "entry": t.get("trade_parameters", {}).get("entry_price"),
            "sl": t.get("trade_parameters", {}).get("stop_loss"),
            "tp1": t.get("trade_parameters", {}).get("take_profit_1"),
            "l2_failed_check": get_l2_failed_check(t),
            "fwd_r": r,
        })
    with open(OUT_DIR / "live_l2_detailed.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")

    # Live ALL inputs
    all_outcomes = Counter(str(t.get("decision_pipeline", {}).get("final_outcome")) for t in trades)
    print()
    print(f"Total live trade records: {len(trades)}")
    print(f"Live final_outcome distribution:")
    for k, v in all_outcomes.most_common():
        print(f"  {v}: {k}")


if __name__ == "__main__":
    main()
