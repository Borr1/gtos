"""Compute per-instrument characteristics from historical_2026 CSVs.

Reads M15, H1, D1 CSVs from data/historical_2026/ for all 24 instruments
and emits a JSON summary of:

- date range, bars, % weekend bars (liquidity profile)
- H1 ATR(14) median / mean / percentiles, expressed as % of price
- daily % range mean / std (volatility regime)
- daily net return skew (gap dynamics)
- Monday open gap magnitude (indices vs FX vs crypto)
- Session concentration (London vs NY vs Tokyo bars active)
- Realized fat-tail via daily-return kurtosis

Pure Python, no external deps.
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timezone

DATA_DIR = r"C:\Users\MSI\Documents\ai-trading-agent\data\historical_2026"
OUT = r"C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-addbe0c3101cfbb8c\research\v4_prompt_engineering\instrument_characteristics.json"

# Instrument class mapping (from commit 74f2fec)
CLASS_MAP = {
    "XAUUSD": "commodity_metal",
    "XAGUSD": "commodity_metal",
    "USOIL_cash": "commodity_energy",
    "UKOIL_cash": "commodity_energy",
    "US30_cash": "index",
    "NAS100": "index",
    "SPX500": "index",
    "GER40": "index",
    "UK100": "index",
    "JP225": "index",
    "EURUSD": "fx_major",
    "GBPUSD": "fx_major",
    "AUDUSD": "fx_major",
    "USDCAD": "fx_major",
    "USDCHF": "fx_major",
    "NZDUSD": "fx_major",
    "USDJPY": "fx_jpy",
    "EURJPY": "fx_jpy",
    "GBPJPY": "fx_jpy",
    "AUDJPY": "fx_jpy",
    "CHFJPY": "fx_jpy",
    "EURGBP": "fx_cross",
    "BTCUSD": "crypto",
    "ETHUSD": "crypto",
}

# Typical price-format decimals per instrument class
PRICE_DECIMALS = {
    "fx_major": 5,
    "fx_jpy": 3,
    "fx_cross": 5,
    "commodity_metal": 2,
    "commodity_energy": 2,
    "index": 1,  # varies widely; default 1dp
    "crypto": 1,
}


def read_csv(path):
    """Read a single CSV and return list of dicts with parsed columns."""
    rows = []
    with open(path, newline="") as fh:
        r = csv.reader(fh)
        header = next(r)
        # Common columns: time, open, high, low, close, volume
        for line in r:
            try:
                ts = line[0].strip('"').strip()
                if "T" in ts:
                    t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                elif " " in ts:
                    t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                else:
                    t = datetime.strptime(ts, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                rows.append({
                    "time": t,
                    "open": float(line[1]),
                    "high": float(line[2]),
                    "low": float(line[3]),
                    "close": float(line[4]),
                })
            except (ValueError, IndexError):
                continue
    return rows


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def atr(rows, n=14):
    """True Range based ATR over the given rows."""
    if len(rows) < n + 1:
        return None
    trs = []
    prev_close = rows[0]["close"]
    for r in rows[1:]:
        tr = max(r["high"] - r["low"], abs(r["high"] - prev_close), abs(r["low"] - prev_close))
        trs.append(tr)
        prev_close = r["close"]
    return trs


def daily_returns(rows):
    """Compute daily net returns (close-to-close %)."""
    if len(rows) < 2:
        return []
    return [(rows[i]["close"] - rows[i - 1]["close"]) / rows[i - 1]["close"] * 100 for i in range(1, len(rows))]


def skew_kurtosis(values):
    if len(values) < 4:
        return None, None
    mean = sum(values) / len(values)
    m2 = sum((v - mean) ** 2 for v in values) / len(values)
    if m2 < 1e-12:
        return 0.0, 0.0
    m3 = sum((v - mean) ** 3 for v in values) / len(values)
    m4 = sum((v - mean) ** 4 for v in values) / len(values)
    std = m2 ** 0.5
    skew = m3 / (std ** 3)
    kurt = m4 / (std ** 4) - 3  # excess kurtosis
    return skew, kurt


def session_concentration(h1_rows):
    """Count H1 bars by UTC hour buckets — London/NY/Tokyo/dead."""
    london = 0  # 07-11 UTC
    ny = 0  # 13-17 UTC
    tokyo = 0  # 00-04 UTC
    weekend = 0  # Sat/Sun
    total = 0
    for r in h1_rows:
        t = r["time"]
        total += 1
        if t.weekday() in (5, 6):
            weekend += 1
        h = t.hour
        if 0 <= h < 4:
            tokyo += 1
        elif 7 <= h < 11:
            london += 1
        elif 13 <= h < 17:
            ny += 1
    return {
        "total_h1_bars": total,
        "weekend_h1_bars": weekend,
        "weekend_pct": weekend / total * 100 if total else 0,
        "london_h1_bars": london,
        "ny_h1_bars": ny,
        "tokyo_h1_bars": tokyo,
    }


def per_instrument_summary(sym):
    h1_path = os.path.join(DATA_DIR, f"{sym}_H1.csv")
    d1_path = os.path.join(DATA_DIR, f"{sym}_D1.csv")

    if not os.path.exists(h1_path) or not os.path.exists(d1_path):
        return None

    h1 = read_csv(h1_path)
    d1 = read_csv(d1_path)
    if not h1 or not d1:
        return None

    # ATR(14) on H1, as % of close
    h1_atr_vals = atr(h1, 14)
    h1_close_med = percentile([r["close"] for r in h1], 50) or 1.0
    atr_pct = [a / h1_close_med * 100 for a in h1_atr_vals] if h1_atr_vals else []

    # Daily % range (high-low)/close and daily returns
    d1_hl_pct = [(r["high"] - r["low"]) / r["close"] * 100 for r in d1 if r["close"] > 0]
    d1_rets = daily_returns(d1)
    skew, kurt = skew_kurtosis(d1_rets)

    # Monday-open gap |Mon.open - prior Fri.close| as % of prior close
    mon_gaps = []
    for i in range(1, len(d1)):
        if d1[i]["time"].weekday() == 0:  # Monday (but with weekend-gap only if prev day was Friday)
            gap_pct = (d1[i]["open"] - d1[i - 1]["close"]) / d1[i - 1]["close"] * 100
            mon_gaps.append(abs(gap_pct))

    # Session concentration
    sess = session_concentration(h1)

    return {
        "symbol": sym,
        "class": CLASS_MAP.get(sym, "unknown"),
        "price_decimals": PRICE_DECIMALS.get(CLASS_MAP.get(sym), 2),
        "date_range_h1": {
            "start": h1[0]["time"].isoformat(),
            "end": h1[-1]["time"].isoformat(),
        },
        "date_range_d1": {
            "start": d1[0]["time"].isoformat(),
            "end": d1[-1]["time"].isoformat(),
        },
        "bars": {
            "h1": len(h1),
            "d1": len(d1),
        },
        "price_level": {
            "median_close": percentile([r["close"] for r in h1], 50),
            "min": min(r["low"] for r in h1),
            "max": max(r["high"] for r in h1),
        },
        "h1_atr14_pct_of_price": {
            "median": percentile(atr_pct, 50),
            "p25": percentile(atr_pct, 25),
            "p75": percentile(atr_pct, 75),
            "p95": percentile(atr_pct, 95),
            "mean": sum(atr_pct) / len(atr_pct) if atr_pct else None,
        },
        "d1_range_pct": {
            "median": percentile(d1_hl_pct, 50),
            "mean": sum(d1_hl_pct) / len(d1_hl_pct) if d1_hl_pct else None,
        },
        "d1_return_skew": skew,
        "d1_return_excess_kurtosis": kurt,  # >0 means fat-tailed vs normal
        "monday_gap_pct_abs_median": percentile(mon_gaps, 50) if mon_gaps else None,
        "monday_gap_pct_abs_max": max(mon_gaps) if mon_gaps else None,
        "session_concentration": sess,
    }


def main():
    instruments = sorted({p.split("_")[0] for p in os.listdir(DATA_DIR) if p.endswith(".csv")})
    # Handle compound names like US30_cash, USOIL_cash
    instruments = []
    seen = set()
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith("_H1.csv"):
            continue
        sym = fn.replace("_H1.csv", "")
        if sym not in seen:
            instruments.append(sym)
            seen.add(sym)

    out = {"generated_utc": datetime.now(timezone.utc).isoformat(), "instruments": {}}
    for sym in instruments:
        print(f"Processing {sym}...")
        s = per_instrument_summary(sym)
        if s:
            out["instruments"][sym] = s

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nWrote {OUT}")
    print(f"{len(out['instruments'])} instruments characterized.")


if __name__ == "__main__":
    main()
