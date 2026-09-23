"""
Compute a "random KZ candle" baseline: pick all K-Z M15 candles regardless of decision,
forward-resolve at H1-direction (or random if absent), and compare WR/ExpR to bucket numbers.

This is the comparison we MUST make: if random KZ candles already produce ExpR≈+0.05,
then "+0.05 ExpR rejection bucket" is NOT alpha — it's the universe baseline.
"""
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import random

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"
DATA_DIR = ROOT / "data/historical_2026"

INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash",
               "EURUSD", "GER40", "NAS100", "UK100", "XAGUSD"]

KZ_HOURS = {
    "XAUUSD": [(7, 10), (13, 17)],
    "US30_cash": [(8, 10), (13, 16)],
    "USDJPY": [(0, 3), (7, 9), (13, 15)],
    "GBPJPY": [(0, 3), (7, 9), (13, 15)],
    "GBPUSD": [(7, 12), (13, 15)],
    "EURUSD": [(7, 12), (13, 15)],
    "GER40":  [(7, 10), (13, 16)],
    "NAS100": [(7, 10), (13, 16)],
    "UK100":  [(7, 12), (13, 15)],
    "XAGUSD": [(7, 12), (13, 15)],
}


def load_csv(symbol, tf):
    fp = DATA_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


def m15_atr(m15_df, time_idx, period=14):
    if time_idx < period:
        return None
    sub = m15_df.iloc[time_idx - period: time_idx + 1]
    high = sub["high"]; low = sub["low"]; close = sub["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high-low, (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return float(tr.tail(period).mean())


def in_kz(ts, inst):
    hours_list = KZ_HOURS.get(inst, [])
    h = ts.hour
    for start, end in hours_list:
        if start <= h <= end:
            return True
    return False


def main():
    random.seed(42)
    all_baseline = []
    for inst in INSTRUMENTS:
        m15 = load_csv(inst, "M15")
        h1 = load_csv(inst, "H1")
        if m15 is None or h1 is None:
            continue
        # Restrict to 2026-01-02 to 2026-04-10 (matching backtest window)
        m15 = m15[(m15["time"] >= pd.Timestamp("2026-01-02", tz="UTC")) &
                  (m15["time"] <= pd.Timestamp("2026-04-10", tz="UTC"))]
        kz_candles = []
        for idx, row in m15.iterrows():
            ts = row["time"]
            # only M15 candle openings inside KZ hours and at :00/:15/:30/:45 closes
            if in_kz(ts, inst):
                kz_candles.append(idx)
        # Subsample ~500 per instrument max for speed
        if len(kz_candles) > 500:
            kz_candles = random.sample(kz_candles, 500)
        for idx in kz_candles:
            atr = m15_atr(m15, idx, period=14)
            if not atr or atr <= 0:
                continue
            entry = float(m15.iloc[idx]["close"])
            ts = m15.iloc[idx]["time"]
            next_h1_ts = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            h1_matches = h1.index[h1["time"] >= next_h1_ts]
            if len(h1_matches) == 0:
                continue
            h1_start = int(h1_matches[0])
            h1_window = h1.iloc[h1_start: h1_start + 12]
            if len(h1_window) == 0:
                continue
            # 50/50 random direction
            direction = "LONG" if random.random() < 0.5 else "SHORT"
            if direction == "LONG":
                sl = entry - atr; tp = entry + 1.5*atr
            else:
                sl = entry + atr; tp = entry - 1.5*atr
            outcome = None
            for _, c in h1_window.iterrows():
                if direction == "LONG":
                    sl_hit = c["low"] <= sl; tp_hit = c["high"] >= tp
                else:
                    sl_hit = c["high"] >= sl; tp_hit = c["low"] <= tp
                if sl_hit and tp_hit: outcome = "SL"; break
                elif sl_hit: outcome = "SL"; break
                elif tp_hit: outcome = "TP"; break
            if outcome == "TP":
                r = 1.5
            elif outcome == "SL":
                r = -1.0
            else:
                last_close = float(h1_window.iloc[-1]["close"])
                r = (last_close - entry) / atr if direction == "LONG" else (entry - last_close) / atr
            all_baseline.append({"_instrument": inst, "fwd_r": r, "fwd_direction": direction})

    n = len(all_baseline)
    rs = [r["fwd_r"] for r in all_baseline]
    wins = sum(1 for x in rs if x >= 1.5 - 1e-9)
    print(f"=== Random KZ-candle baseline ===")
    print(f"n={n}, WR={wins/n:.3f}, ExpR={sum(rs)/n:+.3f}, TotalR={sum(rs):+.1f}")

    # Per instrument
    by_inst = defaultdict(list)
    for r in all_baseline:
        by_inst[r["_instrument"]].append(r)
    for inst, rs2 in sorted(by_inst.items()):
        rsf = [r["fwd_r"] for r in rs2]
        n2 = len(rsf)
        w = sum(1 for x in rsf if x >= 1.5 - 1e-9)
        if n2 > 0:
            print(f"  {inst:12s}: n={n2:4d}, WR={w/n2:.3f}, ExpR={sum(rsf)/n2:+.3f}, TotalR={sum(rsf):+.1f}")

    # Also: try baseline with H1-direction-aligned (use H1 close vs prev to infer momentum direction)
    print()
    print("=== H1-aligned KZ candle baseline (LONG when H1 prev_close > prev_prev_close) ===")
    for inst in INSTRUMENTS:
        m15 = load_csv(inst, "M15")
        h1 = load_csv(inst, "H1")
        if m15 is None or h1 is None:
            continue
        m15 = m15[(m15["time"] >= pd.Timestamp("2026-01-02", tz="UTC")) &
                  (m15["time"] <= pd.Timestamp("2026-04-10", tz="UTC"))]
        kz_candles = []
        for idx, row in m15.iterrows():
            ts = row["time"]
            if in_kz(ts, inst):
                kz_candles.append(idx)
        if len(kz_candles) > 500:
            kz_candles = random.sample(kz_candles, 500)
        rs2 = []
        for idx in kz_candles:
            atr = m15_atr(m15, idx, period=14)
            if not atr or atr <= 0:
                continue
            entry = float(m15.iloc[idx]["close"])
            ts = m15.iloc[idx]["time"]
            next_h1_ts = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            # H1 momentum: previous H1 close vs H1 close 5 bars ago
            h1_matches = h1.index[h1["time"] >= next_h1_ts]
            if len(h1_matches) == 0:
                continue
            h1_start = int(h1_matches[0])
            if h1_start < 5:
                continue
            prev = float(h1.iloc[h1_start-1]["close"])
            ref = float(h1.iloc[h1_start-5]["close"])
            direction = "LONG" if prev > ref else "SHORT"
            if direction == "LONG":
                sl = entry - atr; tp = entry + 1.5*atr
            else:
                sl = entry + atr; tp = entry - 1.5*atr
            h1_window = h1.iloc[h1_start: h1_start + 12]
            if len(h1_window) == 0:
                continue
            outcome = None
            for _, c in h1_window.iterrows():
                if direction == "LONG":
                    sl_hit = c["low"] <= sl; tp_hit = c["high"] >= tp
                else:
                    sl_hit = c["high"] >= sl; tp_hit = c["low"] <= tp
                if sl_hit and tp_hit: outcome = "SL"; break
                elif sl_hit: outcome = "SL"; break
                elif tp_hit: outcome = "TP"; break
            if outcome == "TP":
                rs2.append(1.5)
            elif outcome == "SL":
                rs2.append(-1.0)
            else:
                last_close = float(h1_window.iloc[-1]["close"])
                rs2.append((last_close - entry) / atr if direction == "LONG" else (entry - last_close) / atr)
        n2 = len(rs2)
        w = sum(1 for x in rs2 if x >= 1.5 - 1e-9)
        if n2 > 0:
            print(f"  {inst:12s}: n={n2:4d}, WR={w/n2:.3f}, ExpR={sum(rs2)/n2:+.3f}")


if __name__ == "__main__":
    main()
