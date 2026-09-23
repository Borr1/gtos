"""
Resolve unresolved (no-direction) rejection rows by trying BOTH LONG and SHORT.
For these buckets:
  - ob_proximity_no_unmitigated  : structure exists but no unmitigated OBs nearby
  - prescreen_no_direction       : D1 / H4 didn't establish bias

We test both directions and report the better-of-two as a probe of "what was the
maximum value we could have captured if we'd had ANY direction signal here?"

Output: forward_resolution_neutral.jsonl
"""
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"
DATA_DIR = ROOT / "data/historical_2026"

INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash",
               "EURUSD", "GER40", "NAS100", "UK100", "XAGUSD"]


def load_csv(symbol, tf):
    fp = DATA_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


def normalize_inst(inst):
    if inst == "US30":
        return "US30_cash"
    return inst


def m15_atr(m15_df, time_idx, period=14):
    if time_idx < period:
        return None
    sub = m15_df.iloc[time_idx - period: time_idx + 1]
    high = sub["high"]
    low = sub["low"]
    close = sub["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return float(tr.tail(period).mean())


def find_idx(df, ts):
    try:
        ts_pd = pd.to_datetime(ts, utc=True)
    except Exception:
        return None
    matches = df.index[df["time"] == ts_pd]
    if len(matches) == 0:
        return None
    return int(matches[0])


def resolve_with_direction(direction, entry, atr, h1_window):
    if direction == "LONG":
        sl = entry - atr
        tp = entry + 1.5 * atr
    else:
        sl = entry + atr
        tp = entry - 1.5 * atr

    for i, c in h1_window.iterrows():
        if direction == "LONG":
            sl_hit = c["low"] <= sl
            tp_hit = c["high"] >= tp
        else:
            sl_hit = c["high"] >= sl
            tp_hit = c["low"] <= tp
        if sl_hit and tp_hit:
            return -1.0, "SL", int(i)
        elif sl_hit:
            return -1.0, "SL", int(i)
        elif tp_hit:
            return 1.5, "TP", int(i)
    last_close = float(h1_window.iloc[-1]["close"])
    if direction == "LONG":
        r = (last_close - entry) / atr
    else:
        r = (entry - last_close) / atr
    return float(r), "EXPIRY", int(h1_window.index[-1])


def main():
    rejected = []
    with open(OUT_DIR / "rejected_rows_bucketed.jsonl", "r") as f:
        for line in f:
            rejected.append(json.loads(line))

    target_buckets = {"ob_proximity_no_unmitigated", "prescreen_no_direction"}
    candidates = [r for r in rejected if r["bucket_sub"] in target_buckets]
    print(f"Neutral-resolution candidates: {len(candidates)}")

    m15_dfs = {}
    h1_dfs = {}
    for inst in INSTRUMENTS:
        m = load_csv(inst, "M15")
        h = load_csv(inst, "H1")
        if m is not None and h is not None:
            m15_dfs[inst] = m
            h1_dfs[inst] = h

    rows_out = []
    for r in candidates:
        inst = normalize_inst(r["_instrument"])
        m15 = m15_dfs.get(inst)
        h1 = h1_dfs.get(inst)
        if m15 is None or h1 is None:
            continue
        ts = r.get("timestamp_utc")
        m15_idx = find_idx(m15, ts)
        if m15_idx is None:
            continue
        atr = m15_atr(m15, m15_idx, period=14)
        if not atr or atr <= 0:
            continue
        entry = float(m15.iloc[m15_idx]["close"])
        candle_time = pd.to_datetime(ts, utc=True)
        next_h1_ts = (candle_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_matches = h1.index[h1["time"] >= next_h1_ts]
        if len(h1_matches) == 0:
            continue
        h1_start = int(h1_matches[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            continue
        long_r, long_outcome, _ = resolve_with_direction("LONG", entry, atr, h1_window)
        short_r, short_outcome, _ = resolve_with_direction("SHORT", entry, atr, h1_window)
        rows_out.append({
            "_instrument": r["_instrument"],
            "_slice": r.get("_slice"),
            "_source": r.get("_source"),
            "timestamp_utc": ts,
            "kill_zone": r.get("kill_zone"),
            "bucket_top": r.get("bucket_top"),
            "bucket_sub": r.get("bucket_sub"),
            "no_trade_reason": r.get("no_trade_reason"),
            "fwd_long_outcome": long_outcome,
            "fwd_long_r": long_r,
            "fwd_short_outcome": short_outcome,
            "fwd_short_r": short_r,
            "fwd_atr": atr,
            "fwd_entry": entry,
        })

    with open(OUT_DIR / "forward_resolution_neutral.jsonl", "w") as f:
        for r in rows_out:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Wrote {len(rows_out)} rows to forward_resolution_neutral.jsonl")

    # Brief stats
    import statistics
    if rows_out:
        long_rs = [r["fwd_long_r"] for r in rows_out]
        short_rs = [r["fwd_short_r"] for r in rows_out]
        avg_long = statistics.mean(long_rs)
        avg_short = statistics.mean(short_rs)
        avg_max = statistics.mean(max(l, s) for l, s in zip(long_rs, short_rs))
        long_win = sum(1 for x in long_rs if x >= 1.5) / len(long_rs)
        short_win = sum(1 for x in short_rs if x >= 1.5) / len(short_rs)
        print(f"Avg LONG R:  {avg_long:.3f}, WR: {long_win:.1%}")
        print(f"Avg SHORT R: {avg_short:.3f}, WR: {short_win:.1%}")
        print(f"Avg max(long,short) R: {avg_max:.3f}")

if __name__ == "__main__":
    main()
