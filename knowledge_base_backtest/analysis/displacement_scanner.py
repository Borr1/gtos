#!/usr/bin/env python3
"""Displacement Scanner — Edge Discovery Research for XAUUSD.

OPTIMIZED VERSION: Pre-computes everything upfront, uses indexed lookups.
Scans ~47K M15 candles in minutes, not hours.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time as _time
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent

DISP_THRESHOLD_STD = 2.0
DISP_THRESHOLD_STRONG = 3.0
DISP_THRESHOLD_EXTREME = 4.0

# Session boundaries UTC hours
SESSIONS = {"asian": (0, 7), "london": (7, 12), "ny": (12, 20), "late": (20, 24)}
KZ_LONDON = (420, 570)   # 07:00-09:30 in minutes
KZ_NY = (780, 930)        # 13:00-15:30 in minutes

# ─── Data Loading ────────────────────────────────────────────────────
def load_csv(filepath):
    candles = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                "time": row["time"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]) if row.get("volume") else 0,
            })
    return candles

_time_cache = {}
def parse_time(t):
    if t in _time_cache:
        return _time_cache[t]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(t, fmt)
            _time_cache[t] = dt
            return dt
        except ValueError:
            continue
    raise ValueError(f"Cannot parse: {t}")

# ─── Swing & Structure ───────────────────────────────────────────────
def detect_swings(candles, min_bars=2):
    swings = []
    n = len(candles)
    for i in range(min_bars, n - min_bars):
        h = candles[i]["high"]
        l = candles[i]["low"]
        is_high = True
        is_low = True
        for j in range(1, min_bars + 1):
            if h <= candles[i-j]["high"] or h <= candles[i+j]["high"]:
                is_high = False
            if l >= candles[i-j]["low"] or l >= candles[i+j]["low"]:
                is_low = False
            if not is_high and not is_low:
                break
        if is_high:
            swings.append({"index": i, "type": "high", "price": h})
        if is_low:
            swings.append({"index": i, "type": "low", "price": l})
    return sorted(swings, key=lambda s: s["index"])

def identify_structure(swings):
    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return "insufficient_data", 0
    # Match market_state.py: count ALL consecutive pairs, not just last N
    hh = sum(1 for i in range(1, len(highs)) if highs[i]["price"] > highs[i-1]["price"])
    hl = sum(1 for i in range(1, len(lows)) if lows[i]["price"] > lows[i-1]["price"])
    lh = sum(1 for i in range(1, len(highs)) if highs[i]["price"] < highs[i-1]["price"])
    ll = sum(1 for i in range(1, len(lows)) if lows[i]["price"] < lows[i-1]["price"])
    rp = min(3, len(highs) - 1, len(lows) - 1)
    if hh >= rp and hl >= rp:
        return "bullish", hh + hl
    elif ll >= rp and lh >= rp:
        return "bearish", ll + lh
    return "transitional", 0

# ─── Pre-compute HTF structures once ─────────────────────────────────
def precompute_htf(candles, min_bars, lookback):
    """Returns list of (datetime, direction, strength) sorted by time."""
    results = []
    n = len(candles)
    step = max(1, n // 200)  # sample ~200 points for speed on large datasets
    for i in range(lookback, n):
        window = candles[max(0, i-lookback):i+1]
        sw = detect_swings(window, min_bars)
        direction, strength = identify_structure(sw)
        results.append((parse_time(candles[i]["time"]), direction, strength))
    return results

def lookup_htf(htf_data, target_dt):
    """Binary search for most recent HTF state before target_dt."""
    if not htf_data:
        return "insufficient_data", 0
    # htf_data is sorted by time
    times = [h[0] for h in htf_data]
    idx = bisect_right(times, target_dt) - 1
    if idx < 0:
        return "insufficient_data", 0
    return htf_data[idx][1], htf_data[idx][2]

# ─── Session helpers ─────────────────────────────────────────────────
def get_session(dt):
    h = dt.hour
    if h < 7: return "asian"
    if h < 12: return "london"
    if h < 20: return "ny"
    return "late"

def is_kz(dt):
    m = dt.hour * 60 + dt.minute
    return (KZ_LONDON[0] <= m < KZ_LONDON[1]) or (KZ_NY[0] <= m < KZ_NY[1])

def kz_minute(dt):
    m = dt.hour * 60 + dt.minute
    if KZ_LONDON[0] <= m < KZ_LONDON[1]: return m - KZ_LONDON[0]
    if KZ_NY[0] <= m < KZ_NY[1]: return m - KZ_NY[0]
    return None

# ─── Pre-compute session levels by date ──────────────────────────────
def precompute_session_levels(m15, d1):
    """Build dict: date_str -> {asian_high, asian_low, pdh, pdl, ...}"""
    # Group M15 by date
    by_date = defaultdict(list)
    for i, c in enumerate(m15):
        dt = parse_time(c["time"])
        by_date[dt.date()].append((dt, c, i))

    # D1 by date
    d1_by_date = {}
    for c in d1:
        dt = parse_time(c["time"])
        d1_by_date[dt.date()] = c

    # D1 dates sorted
    d1_dates = sorted(d1_by_date.keys())

    result = {}
    for d in sorted(by_date.keys()):
        candles_today = by_date[d]

        # Asian range (00:00-07:00)
        asian = [(dt, c) for dt, c, _ in candles_today if dt.hour < 7]
        if asian:
            ah = max(c["high"] for _, c in asian)
            al = min(c["low"] for _, c in asian)
        else:
            ah, al = 0.0, 0.0

        # PDH/PDL
        pdh, pdl = 0.0, 0.0
        for days_back in range(1, 6):
            prev = d - timedelta(days=days_back)
            if prev in d1_by_date:
                pdh = d1_by_date[prev]["high"]
                pdl = d1_by_date[prev]["low"]
                break

        # ADR (20-day)
        idx = bisect_right(d1_dates, d) - 1
        adr_candles = []
        for j in range(max(0, idx-19), idx+1):
            if j < len(d1_dates):
                dc = d1_by_date[d1_dates[j]]
                adr_candles.append(dc["high"] - dc["low"])
        adr = sum(adr_candles) / len(adr_candles) if adr_candles else 1.0

        # Previous day
        prev_day = None
        for days_back in range(1, 6):
            prev = d - timedelta(days=days_back)
            if prev in d1_by_date:
                prev_day = d1_by_date[prev]
                break

        result[d] = {
            "asian_high": ah, "asian_low": al,
            "asian_range": ah - al if ah > 0 else 0.0,
            "pdh": pdh, "pdl": pdl, "adr": adr,
            "prev_day": prev_day,
        }

        # Session high/low by session — computed incrementally during scan
        # Store candle indices for each session
        for sess_name, (sh, eh) in SESSIONS.items():
            sess_candles = [(dt2, c2) for dt2, c2, _ in candles_today if sh <= dt2.hour < eh]
            if sess_candles:
                result[d][f"{sess_name}_high"] = max(c2["high"] for _, c2 in sess_candles)
                result[d][f"{sess_name}_low"] = min(c2["low"] for _, c2 in sess_candles)

    return result

# ─── Compute rolling session high/low up to index ────────────────────
def get_session_hl_before(m15, idx, session, date_val):
    """Get session high/low up to but not including idx."""
    sh = SESSIONS[session][0]
    hi, lo = 0.0, 999999.0
    # Walk backwards from idx to find same-session candles
    for j in range(idx - 1, max(idx - 100, -1), -1):
        dt2 = parse_time(m15[j]["time"])
        if dt2.date() != date_val:
            break
        if dt2.hour < sh:
            break
        hi = max(hi, m15[j]["high"])
        lo = min(lo, m15[j]["low"])
    if hi == 0.0:
        return None, None
    return hi, lo

# ─── Round number check ──────────────────────────────────────────────
def check_round_number(o, c):
    lo, hi = min(o, c), max(o, c)
    lvl = (math.floor(lo / 25) + 1) * 25
    if lvl < hi:
        return True, lvl
    return False, None

# ─── FVG check ───────────────────────────────────────────────────────
def check_fvg(m15, idx):
    if idx < 1 or idx >= len(m15) - 1:
        return False, None, None
    body = abs(m15[idx]["close"] - m15[idx]["open"])
    if body == 0: return False, None, None
    # Bullish
    bg = m15[idx+1]["low"] - m15[idx-1]["high"]
    if bg > 0 and m15[idx]["close"] > m15[idx]["open"]:
        return True, round(bg, 2), round(bg/body, 3)
    # Bearish
    bg = m15[idx-1]["low"] - m15[idx+1]["high"]
    if bg > 0 and m15[idx]["close"] < m15[idx]["open"]:
        return True, round(bg, 2), round(bg/body, 3)
    return False, None, None

# ─── Sweep detection ─────────────────────────────────────────────────
def detect_sweep(m15, idx, levels):
    """levels = list of (name, price, side='high'|'low')"""
    result = {"detected": False, "level": None, "candles_before": None,
              "quality": None, "wick_depth": None, "depth": 0, "levels_swept": 0}
    price = m15[idx]["close"]
    threshold = price * 0.005
    result["depth"] = sum(1 for _, p, _ in levels if abs(price - p) <= threshold)

    start = max(0, idx - 5)
    swept = set()
    best = None

    for i in range(start, idx + 1):
        c = m15[i]
        bt = max(c["open"], c["close"])
        bb = min(c["open"], c["close"])
        for name, lvl, side in levels:
            if lvl <= 0: continue
            if side == "high" and c["high"] > lvl and bt < lvl:
                swept.add(name)
                cb = idx - i
                if best is None or cb < best[1]:
                    best = (name, cb, "clean", round(c["high"] - lvl, 2))
            elif side == "high" and c["close"] > lvl:
                swept.add(name)
                cb = idx - i
                if best is None or cb < best[1]:
                    best = (name, cb, "run", round(c["high"] - lvl, 2))
            elif side == "low" and c["low"] < lvl and bb > lvl:
                swept.add(name)
                cb = idx - i
                if best is None or cb < best[1]:
                    best = (name, cb, "clean", round(lvl - c["low"], 2))
            elif side == "low" and c["close"] < lvl:
                swept.add(name)
                cb = idx - i
                if best is None or cb < best[1]:
                    best = (name, cb, "run", round(lvl - c["low"], 2))

    result["levels_swept"] = len(swept)
    if best:
        result["detected"] = True
        result["level"] = best[0]
        result["candles_before"] = best[1]
        result["quality"] = best[2]
        result["wick_depth"] = best[3]
    return result

# ─── Outcome measurement ─────────────────────────────────────────────
def measure_outcomes(m15, idx, direction):
    c = m15[idx]
    dc = c["close"]
    do = c["open"]
    body = abs(dc - do) or 0.01
    bull = direction == "bullish"
    n = len(m15)
    R = {}

    for label, count in [("1h", 4), ("3h", 12), ("session", 18)]:
        end = min(idx + count + 1, n)
        if end <= idx + 1:
            for k in [f"mfe_{label}", f"mae_{label}", f"net_{label}",
                      f"mfe_{label}_bm", f"mae_{label}_bm"]:
                R[k] = 0.0
            R[f"cont_{label}"] = False
            continue
        mfe = mae = 0.0
        for j in range(idx+1, end):
            if bull:
                mfe = max(mfe, m15[j]["high"] - dc)
                mae = max(mae, dc - m15[j]["low"])
            else:
                mfe = max(mfe, dc - m15[j]["low"])
                mae = max(mae, m15[j]["high"] - dc)
        lc = m15[min(idx+count, n-1)]["close"]
        net = (lc - dc) if bull else (dc - lc)
        R[f"mfe_{label}"] = round(mfe, 6)
        R[f"mae_{label}"] = round(mae, 6)
        R[f"net_{label}"] = round(net, 6)
        R[f"cont_{label}"] = net > 0
        R[f"mfe_{label}_bm"] = round(mfe/body, 2)
        R[f"mae_{label}_bm"] = round(mae/body, 2)

    # Origin revisit
    origin = do if bull else dc
    R["origin_revisited"] = False
    R["revisit_candles"] = None
    R["revisit_depth"] = None
    R["revisit_continued"] = False
    R["revisit_mfe"] = None

    check_end = min(idx + 19, n)
    for j in range(idx+1, check_end):
        hit = False
        if bull and m15[j]["low"] <= origin + body * 0.2:
            hit = True
            low_pt = m15[j]["low"]
            R["revisit_depth"] = round(min(1.0, max(0.0, (dc - low_pt)/body)), 3)
            post_mfe = max(m15[k]["high"] - low_pt for k in range(j, min(j+12, n)))
            R["revisit_mfe"] = round(post_mfe, 6)
            R["revisit_continued"] = m15[min(j+12, n-1)]["close"] > low_pt
        elif not bull and m15[j]["high"] >= origin - body * 0.2:
            hit = True
            hi_pt = m15[j]["high"]
            R["revisit_depth"] = round(min(1.0, max(0.0, (hi_pt - dc)/body)), 3)
            post_mfe = max(hi_pt - m15[k]["low"] for k in range(j, min(j+12, n)))
            R["revisit_mfe"] = round(post_mfe, 6)
            R["revisit_continued"] = m15[min(j+12, n-1)]["close"] < hi_pt
        if hit:
            R["origin_revisited"] = True
            R["revisit_candles"] = j - idx
            break

    # Next candle
    if idx + 1 < n:
        nc = m15[idx+1]
        nb = nc["close"] - nc["open"]
        nr = nc["high"] - nc["low"]
        nab = abs(nb)
        if nr > 0 and nab/nr < 0.3:
            R["nc_dir"] = "doji"
        elif (bull and nb > 0) or (not bull and nb < 0):
            R["nc_dir"] = "continuation"
        else:
            R["nc_dir"] = "reversal"
        R["nc_body_ratio"] = round(nab/body, 3)
        rw = (nc["high"] - max(nc["open"], nc["close"])) if bull else (min(nc["open"], nc["close"]) - nc["low"])
        R["nc_rej_wick"] = round(rw/nr, 3) if nr > 0 else 0
        cp = ((nc["close"] - dc)/body) if bull else ((dc - nc["close"])/body)
        R["nc_cont_pct"] = round(cp, 3)
    else:
        R["nc_dir"] = R["nc_body_ratio"] = R["nc_rej_wick"] = R["nc_cont_pct"] = None

    return R

# ─── Analysis Functions ──────────────────────────────────────────────
def analyze_factor(data, field=None, value_fn=None, bucket_fn=None):
    groups = defaultdict(list)
    for d in data:
        if bucket_fn: key = bucket_fn(d)
        elif value_fn: key = value_fn(d)
        else: key = d.get(field)
        if key is not None:
            groups[str(key)].append(d)

    all_c = [d["cont_3h"] for d in data if d.get("cont_3h") is not None]
    baseline = sum(all_c) / len(all_c) if all_c else 0.5
    all_mfe = [d["mfe_3h"] for d in data if d.get("mfe_3h") is not None]
    bm = sum(all_mfe)/len(all_mfe) if all_mfe else 0

    result = {"baseline": round(baseline, 3), "baseline_mfe": round(bm, 2), "groups": {}}
    for key, grp in sorted(groups.items()):
        n = len(grp)
        if n < 5: continue
        c1 = [d["cont_1h"] for d in grp if d.get("cont_1h") is not None]
        c3 = [d["cont_3h"] for d in grp if d.get("cont_3h") is not None]
        cs = [d["cont_session"] for d in grp if d.get("cont_session") is not None]
        mfe = [d["mfe_3h"] for d in grp if d.get("mfe_3h") is not None]
        mae = [d["mae_3h"] for d in grp if d.get("mae_3h") is not None]
        r1 = sum(c1)/len(c1) if c1 else 0
        r3 = sum(c3)/len(c3) if c3 else 0
        rs = sum(cs)/len(cs) if cs else 0
        am = sum(mfe)/len(mfe) if mfe else 0
        aa = sum(mae)/len(mae) if mae else 0
        eff = r3 - baseline
        result["groups"][key] = {
            "n": n, "r1h": round(r1,3), "r3h": round(r3,3), "rS": round(rs,3),
            "mfe": round(am,2), "mae": round(aa,2),
            "ratio": round(am/aa,2) if aa>0 else 0,
            "eff": round(eff,3),
            "flag": n>=30 and abs(eff)>=0.10 and (r1-baseline)*(r3-baseline)>0,
        }
    return result

def analyze_combo(data, filters, label):
    filtered = data
    for fn in filters:
        filtered = [d for d in filtered if fn(d)]
    n = len(filtered)
    if n < 20:
        return {"n": n, "label": label, "insuf": True}
    c3 = [d["cont_3h"] for d in filtered if d.get("cont_3h") is not None]
    mfe = [d["mfe_3h"] for d in filtered if d.get("mfe_3h") is not None]
    mae = [d["mae_3h"] for d in filtered if d.get("mae_3h") is not None]
    r = sum(c3)/len(c3) if c3 else 0
    am = sum(mfe)/len(mfe) if mfe else 0
    aa = sum(mae)/len(mae) if mae else 0
    # Fix 2: Consistent threshold: cont>=55%, MFE>1.3*MAE, n>=20
    return {"n": n, "label": label, "r3h": round(r,3), "mfe": round(am,2),
            "mae": round(aa,2), "ratio": round(am/aa,2) if aa>0 else 0,
            "edge": r>=0.55 and am>1.3*aa}

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def run():
    t0 = _time.time()
    print("=" * 70)
    print("DISPLACEMENT SCANNER — Edge Discovery Research")
    print("=" * 70)

    # Load
    print("\n[1] Loading data...")
    m15 = load_csv(DATA_DIR / "XAUUSD_M15.csv")
    h1 = load_csv(DATA_DIR / "XAUUSD_H1.csv")
    h4 = load_csv(DATA_DIR / "XAUUSD_H4.csv")
    d1 = load_csv(DATA_DIR / "XAUUSD_D1.csv")
    print(f"  M15={len(m15):,}  H1={len(h1):,}  H4={len(h4):,}  D1={len(d1):,}")

    split_idx = len(m15) // 2
    split_time = m15[split_idx]["time"]
    print(f"  Split: idx={split_idx}, date={split_time}")

    # Pre-compute HTF
    print("\n[2] Pre-computing HTF structures...")
    t1 = _time.time()
    d1_htf = precompute_htf(d1, min_bars=2, lookback=30)
    print(f"  D1: {len(d1_htf)} entries ({_time.time()-t1:.1f}s)")
    t1 = _time.time()
    h4_htf = precompute_htf(h4, min_bars=2, lookback=80)
    print(f"  H4: {len(h4_htf)} entries ({_time.time()-t1:.1f}s)")
    t1 = _time.time()
    h1_htf = precompute_htf(h1, min_bars=2, lookback=168)
    print(f"  H1: {len(h1_htf)} entries ({_time.time()-t1:.1f}s)")

    # Pre-compute session levels
    print("\n[3] Pre-computing session levels...")
    sess_levels = precompute_session_levels(m15, d1)
    print(f"  {len(sess_levels)} trading days")

    # Fix 4: Pre-compute H1 order blocks for OB context
    print("\n[3b] Pre-computing H1 order blocks...")
    h1_obs = []  # list of {type, high, low, form_time_dt, mitigated_time_dt}
    h1_swings = detect_swings(h1, min_bars=2)
    h1_highs = [s for s in h1_swings if s["type"] == "high"]
    h1_lows = [s for s in h1_swings if s["type"] == "low"]
    # Bullish OBs: last bearish candle before each HH
    for idx_h in range(1, len(h1_highs)):
        if h1_highs[idx_h]["price"] > h1_highs[idx_h-1]["price"]:
            brk = h1_highs[idx_h]["index"]
            for j in range(brk - 1, max(brk - 10, -1), -1):
                if j < 0: break
                if h1[j]["close"] < h1[j]["open"]:
                    form_dt = parse_time(h1[j]["time"])
                    # Check mitigation
                    mit_dt = None
                    for k in range(brk + 1, len(h1)):
                        if h1[k]["low"] <= h1[j]["high"]:
                            mit_dt = parse_time(h1[k]["time"])
                            break
                    h1_obs.append({"type": "bullish", "high": h1[j]["high"], "low": h1[j]["low"],
                                   "form_dt": form_dt, "mit_dt": mit_dt})
                    break
    # Bearish OBs: last bullish candle before each LL
    for idx_l in range(1, len(h1_lows)):
        if h1_lows[idx_l]["price"] < h1_lows[idx_l-1]["price"]:
            brk = h1_lows[idx_l]["index"]
            for j in range(brk - 1, max(brk - 10, -1), -1):
                if j < 0: break
                if h1[j]["close"] > h1[j]["open"]:
                    form_dt = parse_time(h1[j]["time"])
                    mit_dt = None
                    for k in range(brk + 1, len(h1)):
                        if h1[k]["high"] >= h1[j]["low"]:
                            mit_dt = parse_time(h1[k]["time"])
                            break
                    h1_obs.append({"type": "bearish", "high": h1[j]["high"], "low": h1[j]["low"],
                                   "form_dt": form_dt, "mit_dt": mit_dt})
                    break
    h1_obs.sort(key=lambda o: o["form_dt"])
    print(f"  {len(h1_obs)} H1 order blocks detected")

    # Pre-compute rolling averages
    print("\n[4] Pre-computing rolling averages...")
    N = len(m15)
    bavg20 = [0.0] * N
    bavg50 = [0.0] * N
    atr20 = [0.0] * N

    cum_body = [0.0] * (N + 1)
    cum_range = [0.0] * (N + 1)
    for i in range(N):
        cum_body[i+1] = cum_body[i] + abs(m15[i]["close"] - m15[i]["open"])
        cum_range[i+1] = cum_range[i] + (m15[i]["high"] - m15[i]["low"])

    for i in range(N):
        if i >= 20:
            bavg20[i] = (cum_body[i] - cum_body[i-20]) / 20
            atr20[i] = (cum_range[i] - cum_range[i-20]) / 20
        elif i > 0:
            bavg20[i] = cum_body[i] / i
            atr20[i] = cum_range[i] / i
        if i >= 50:
            bavg50[i] = (cum_body[i] - cum_body[i-50]) / 50
        elif i > 0:
            bavg50[i] = cum_body[i] / i

    # Scan
    print(f"\n[5] Scanning for displacements...")
    t1 = _time.time()
    disps = []
    sess_tracker = defaultdict(list)  # date_session -> [(idx, dir)]
    total_by_str = {"standard": 0, "strong": 0, "extreme": 0}

    for i in range(50, N):
        if i % 10000 == 0:
            print(f"  {i:,}/{N:,} ({_time.time()-t1:.0f}s)")

        c = m15[i]
        body = abs(c["close"] - c["open"])
        a20 = bavg20[i]
        if a20 <= 0: continue
        ratio = body / a20
        if ratio < DISP_THRESHOLD_STD: continue

        # It's a displacement
        dt = parse_time(c["time"])
        dr = "bullish" if c["close"] > c["open"] else "bearish"
        strength = "extreme" if ratio >= 4 else "strong" if ratio >= 3 else "standard"
        total_by_str[strength] += 1

        sess = get_session(dt)
        kz_on = is_kz(dt)
        kzm = kz_minute(dt)
        rng = c["high"] - c["low"]
        wick = rng - body
        wr = wick / body if body > 0 else 99

        # FVG
        has_fvg, fvg_sz, fvg_pct = check_fvg(m15, i)

        # Round number
        has_rn, rn_lvl = check_round_number(c["open"], c["close"])

        # HTF context
        d1_dir, d1_str = lookup_htf(d1_htf, dt)
        h4_dir, h4_str = lookup_htf(h4_htf, dt)
        h1_dir, h1_str = lookup_htf(h1_htf, dt)

        # M15 structure (quick: last 30 candles)
        m15w = m15[max(0, i-30):i]
        if len(m15w) >= 5:
            m15_sw = detect_swings(m15w, 2)
            m15_dir, _ = identify_structure(m15_sw)
        else:
            m15_dir = "insufficient_data"

        # Alignment
        align = sum([d1_dir == dr, h4_dir == dr, h1_dir == dr])

        # Session levels
        d_date = dt.date()
        sl = sess_levels.get(d_date, {})
        ah = sl.get("asian_high", 0)
        al = sl.get("asian_low", 0)
        ar = sl.get("asian_range", 0)
        adr = sl.get("adr", 1)
        pdh = sl.get("pdh", 0)
        pdl = sl.get("pdl", 0)
        arpct = round(ar / adr * 100, 1) if adr > 0 else 0

        # Session H/L before this candle
        s_hi, s_lo = get_session_hl_before(m15, i, sess, d_date)

        # Sweep
        levels = []
        if ah > 0: levels.append(("asian_high", ah, "high"))
        if al > 0: levels.append(("asian_low", al, "low"))
        if pdh > 0: levels.append(("pdh", pdh, "high"))
        if pdl > 0: levels.append(("pdl", pdl, "low"))
        if s_hi: levels.append(("session_high", s_hi, "high"))
        if s_lo and s_lo < 999999: levels.append(("session_low", s_lo, "low"))

        sw = detect_sweep(m15, i, levels)

        # Adjust alignment for sweep in zone
        if sw["detected"] and adr > 0:
            if dr == "bullish" and pdl > 0 and c["close"] < pdl + adr * 0.3:
                align += 1
            elif dr == "bearish" and pdh > 0 and c["close"] > pdh - adr * 0.3:
                align += 1

        # Premium/Discount (simplified from H1 swings)
        in_disc = in_prem = in_ote = False
        # Use simple PDH/PDL range
        if pdh > 0 and pdl > 0:
            imp_range = pdh - pdl
            if imp_range > 0:
                eq = pdl + imp_range * 0.5
                in_disc = c["close"] < eq
                in_prem = c["close"] > eq
                f62 = pdh - imp_range * 0.618
                f79 = pdh - imp_range * 0.786
                in_ote = f79 <= c["close"] <= f62

        # Prior candle context
        p10 = m15[max(0, i-10):i]
        p5 = m15[max(0, i-5):i]
        p10r = (max(x["high"] for x in p10) - min(x["low"] for x in p10)) if p10 else 0
        p10net = (p10[-1]["close"] - p10[0]["open"]) if p10 else 0
        p10dir = "flat" if abs(p10net) < p10r * 0.2 else ("bullish" if p10net > 0 else "bearish")
        p5r = (max(x["high"] for x in p5) - min(x["low"] for x in p5)) if p5 else 0
        p5ba = (sum(abs(x["close"]-x["open"]) for x in p5)/len(p5)) if p5 else 0
        # Fix 1: Normalize by expected multi-candle range, not single-candle ATR
        consol = p10r / (atr20[i] * 4.0) if atr20[i] > 0 else 1  # 10-candle range / (ATR * 4)
        tight = p5r / (atr20[i] * 2.5) if atr20[i] > 0 else 1    # 5-candle range / (ATR * 2.5)

        # Prior 5 character
        if p5:
            p5n = p5[-1]["close"] - p5[0]["open"]
            if abs(p5n) < p5r * 0.15:
                p5c = "consolidating" if p5r < atr20[i] * 0.5 else "choppy"
            elif (dr == "bullish" and p5n > 0) or (dr == "bearish" and p5n < 0):
                p5c = "trending_with"
            else:
                p5c = "trending_against"
        else:
            p5c = "unknown"

        # Sequence
        dsk = f"{d_date}_{sess}"
        same_dir = [x for x in sess_tracker[dsk] if x[1] == dr]
        seq = len(same_dir) + 1
        sess_tracker[dsk].append((i, dr))

        csld = csls = None
        pdb = None
        if disps:
            csld = i - disps[-1]["_idx"]
            for prev in reversed(disps):
                if prev["direction"] == dr:
                    csls = i - prev["_idx"]
                    if csls <= 30:
                        pdb = prev["body_size"]
                    break

        exhaust = seq >= 3 and pdb is not None and body < pdb

        # Counter-trend
        ct = d1_dir in ("bullish", "bearish") and d1_dir != dr

        # Previous day
        pd = sl.get("prev_day")
        pdbp = pdrva = 0
        pdd = "unknown"
        if pd:
            pdr2 = pd["high"] - pd["low"]
            pdb2 = abs(pd["close"] - pd["open"])
            pdbp = pdb2/pdr2 if pdr2 > 0 else 0
            pdrva = pdr2/adr if adr > 0 else 0
            if pdr2 > 0 and pdb2/pdr2 < 0.3: pdd = "doji"
            elif pd["close"] > pd["open"]: pdd = "bullish"
            else: pdd = "bearish"

        # Session timing
        mss = (dt.hour - SESSIONS[sess][0]) * 60 + dt.minute
        first_kz = kzm is not None and kzm <= 15

        # Fix 4: OB context from pre-computed H1 OBs
        ob_type = None
        at_ob = False
        breaks_ob = False
        ob_dist = None
        # Find nearest unmitigated OB at this time
        price = c["close"]
        open_p = c["open"]
        nearest_dist = 999999
        for ob in reversed(h1_obs):
            if ob["form_dt"] >= dt:
                continue  # formed after this candle
            if ob["mit_dt"] is not None and ob["mit_dt"] < dt:
                continue  # already mitigated
            mid = (ob["high"] + ob["low"]) / 2
            dist = abs(price - mid)
            if dist < nearest_dist:
                nearest_dist = dist
                ob_type = ob["type"]
                at_ob = ob["low"] <= open_p <= ob["high"]
                ob_dist = round(dist / price * 100, 3)
                # breaks_opposite_ob: displacement closes through opposite OB
                if ob["type"] != dr:
                    if dr == "bullish" and c["close"] > ob["high"]:
                        breaks_ob = True
                    elif dr == "bearish" and c["close"] < ob["low"]:
                        breaks_ob = True
            if nearest_dist < price * 0.01:  # within 1% is close enough
                break

        # Outcomes
        out = measure_outcomes(m15, i, dr)

        rec = {
            "timestamp": c["time"], "date": str(d_date),
            "dow": dt.strftime("%A"), "session": sess,
            "kz": kz_on, "kz_min": kzm, "direction": dr, "strength": strength,
            "body_size": round(body, 2), "body_ratio": round(ratio, 2),
            "body_ratio_50": round(body/bavg50[i], 2) if bavg50[i]>0 else 0,
            "range": round(rng, 2), "wick_ratio": round(wr, 3),
            "open": c["open"], "high": c["high"], "low": c["low"], "close": c["close"],
            "volume": c["volume"],
            "creates_fvg": has_fvg, "fvg_size": fvg_sz, "fvg_pct": fvg_pct,
            "crosses_rn": has_rn, "rn_level": rn_lvl,
            "d1_dir": d1_dir, "d1_str": d1_str,
            "h4_dir": h4_dir, "h4_aligned_d1": h4_dir == d1_dir,
            "h1_dir": h1_dir, "m15_dir": m15_dir,
            "m15_aligned": m15_dir == dr, "align": align,
            "asian_high": ah, "asian_low": al, "asian_range": ar, "asian_range_pct": arpct,
            "pdh": pdh, "pdl": pdl,
            "sweep": sw["detected"], "sweep_level": sw["level"],
            "sweep_cb": sw["candles_before"], "sweep_quality": sw["quality"],
            "sweep_wick": sw["wick_depth"], "liq_depth": sw["depth"],
            "levels_swept": sw["levels_swept"],
            "ob_type": ob_type, "at_ob": at_ob, "breaks_ob": breaks_ob, "ob_dist": ob_dist,
            "in_disc": in_disc, "in_prem": in_prem, "in_ote": in_ote,
            "p10_range": round(p10r, 2), "p10_dir": p10dir,
            "consol": round(consol, 3), "p5_range": round(p5r, 2),
            "p5_bavg": round(p5ba, 2), "tight": round(tight, 3), "p5_char": p5c,
            "seq": seq, "csld": csld, "csls": csls,
            "prior_body": round(pdb, 2) if pdb else None,
            "exhaust": exhaust, "ct": ct,
            "pd_body_pct": round(pdbp, 3), "pd_rva": round(pdrva, 3), "pd_dir": pdd,
            "mss": mss, "kz_min_open": kzm, "first_kz": first_kz,
            # Outcomes
            "mfe_1h": out["mfe_1h"], "mae_1h": out["mae_1h"], "net_1h": out["net_1h"],
            "cont_1h": out["cont_1h"], "mfe_1h_bm": out["mfe_1h_bm"],
            "mfe_3h": out["mfe_3h"], "mae_3h": out["mae_3h"], "net_3h": out["net_3h"],
            "cont_3h": out["cont_3h"], "mfe_3h_bm": out["mfe_3h_bm"],
            "mfe_sess": out["mfe_session"], "mae_sess": out["mae_session"],
            "net_sess": out["net_session"], "cont_session": out["cont_session"],
            "origin_revisited": out["origin_revisited"],
            "revisit_candles": out["revisit_candles"],
            "revisit_depth": out["revisit_depth"],
            "revisit_continued": out["revisit_continued"],
            "revisit_mfe": out["revisit_mfe"],
            "nc_dir": out["nc_dir"], "nc_body_ratio": out["nc_body_ratio"],
            "nc_rej_wick": out["nc_rej_wick"], "nc_cont_pct": out["nc_cont_pct"],
            "set": "disc" if i < split_idx else "val",
            "_idx": i,
        }
        disps.append(rec)

    scan_time = _time.time() - t1
    print(f"\n  Total: {len(disps):,} displacements in {scan_time:.0f}s")
    for k, v in total_by_str.items():
        print(f"    {k}: {v:,}")
    disc = [d for d in disps if d["set"] == "disc"]
    val = [d for d in disps if d["set"] == "val"]
    print(f"  Discovery: {len(disc):,}  Validation: {len(val):,}")

    # Save database
    print("\n[6] Saving database...")
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_disps = [{k: v for k, v in d.items() if k != "_idx"} for d in disps]

    with open(OUT_DIR / f"displacement_database_{ts}.json", "w") as f:
        json.dump(out_disps, f, indent=1, default=str)
    with open(OUT_DIR / f"displacement_database_{ts}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_disps[0].keys())
        w.writeheader()
        w.writerows(out_disps)
    print(f"  Saved displacement_database_{ts}.json/csv")

    # ── Pattern Discovery ────────────────────────────────────────────
    print("\n[7] Pattern discovery (discovery set)...")

    factors = {
        "session": {"field": "session"},
        "kz": {"field": "kz"},
        "d1_aligned": {"value_fn": lambda d: d["d1_dir"] == d["direction"]},
        "h4_aligned_d1": {"field": "h4_aligned_d1"},
        "align": {"field": "align"},
        "sweep": {"field": "sweep"},
        "sweep_level": {"field": "sweep_level"},
        "sweep_quality": {"field": "sweep_quality"},
        "in_disc": {"field": "in_disc"},
        "in_prem": {"field": "in_prem"},
        "in_ote": {"field": "in_ote"},
        "consol_bucket": {"bucket_fn": lambda d: "<0.4" if d["consol"]<0.4 else "0.4-0.7" if d["consol"]<0.7 else "0.7-1.0" if d["consol"]<1.0 else ">1.0"},
        "body_ratio_bkt": {"bucket_fn": lambda d: "2-3x" if d["body_ratio"]<3 else "3-4x" if d["body_ratio"]<4 else ">4x"},
        "wick_ratio_bkt": {"bucket_fn": lambda d: "<0.3" if d["wick_ratio"]<0.3 else "0.3-0.5" if d["wick_ratio"]<0.5 else ">0.5"},
        "dow": {"field": "dow"},
        "asian_range_bkt": {"bucket_fn": lambda d: "<30%" if d["asian_range_pct"]<30 else "30-50%" if d["asian_range_pct"]<50 else "50-80%" if d["asian_range_pct"]<80 else ">80%"},
        "creates_fvg": {"field": "creates_fvg"},
        "seq_bkt": {"bucket_fn": lambda d: "1st" if d["seq"]==1 else "2nd" if d["seq"]==2 else "3rd+"},
        "exhaust": {"field": "exhaust"},
        "ct": {"field": "ct"},
        "tight_bkt": {"bucket_fn": lambda d: "<0.4" if d["tight"]<0.4 else "0.4-0.7" if d["tight"]<0.7 else "0.7-1.0" if d["tight"]<1.0 else ">1.0"},
        "liq_depth_bkt": {"bucket_fn": lambda d: "0-1" if d["liq_depth"]<=1 else "2-3" if d["liq_depth"]<=3 else "4+"},
        "p5_char": {"field": "p5_char"},
        "pd_rva_bkt": {"bucket_fn": lambda d: "<0.5" if d["pd_rva"]<0.5 else "0.5-1.0" if d["pd_rva"]<1.0 else ">1.0"},
        "nc_dir": {"field": "nc_dir"},
        "crosses_rn": {"field": "crosses_rn"},
        "at_ob": {"field": "at_ob"},
        "breaks_ob": {"field": "breaks_ob"},
        "origin_revisited": {"field": "origin_revisited"},
    }

    sf_results = {}
    flagged = []
    for name, params in factors.items():
        sf_results[name] = analyze_factor(disc, **params)
        for key, grp in sf_results[name]["groups"].items():
            if grp.get("flag"):
                # Fix 5: Exclude origin_revisited=False (tautology: no pullback = continued)
                if name == "origin_revisited" and key == "False":
                    grp["flag"] = False
                    grp["tautology"] = True
                    continue
                flagged.append((name, key, grp))

    print(f"  Flagged factors: {len(flagged)}")
    for nm, k, g in flagged:
        print(f"    {nm}={k}: n={g['n']}, r3h={g['r3h']:.1%}, eff={g['eff']:+.1%}")

    # Combinations
    print("\n  Combinations...")
    combos_def = {
        "full_smc": ([lambda d: d["sweep"], lambda d: d["creates_fvg"], lambda d: d["align"]>=3], "Sweep+FVG+Align>=3"),
        "tight_kz_align": ([lambda d: d["tight"]<0.4, lambda d: d["kz"], lambda d: d["align"]>=2], "Tight+KZ+Align>=2"),
        "1st_sweep_zone": ([lambda d: d["seq"]==1, lambda d: d["sweep"], lambda d: (d["direction"]=="bullish" and d["in_disc"]) or (d["direction"]=="bearish" and d["in_prem"])], "1st+Sweep+Zone"),
        "ct_exhaust": ([lambda d: d["ct"], lambda d: d["seq"]>=3, lambda d: d["exhaust"]], "CT+3rd+Exhaust"),
        "coiled": ([lambda d: d["pd_rva"]<0.5, lambda d: d["kz"], lambda d: d["align"]>=3], "Quiet+KZ+Align>=3"),
        "sweep_fvg_kz": ([lambda d: d["sweep"], lambda d: d["creates_fvg"], lambda d: d["kz"]], "Sweep+FVG+KZ"),
        "align_kz_consol": ([lambda d: d["align"]>=3, lambda d: d["kz"], lambda d: d["consol"]<0.4], "Align>=3+KZ+Consol"),
        "1st_kz_align": ([lambda d: d["seq"]==1, lambda d: d["kz"], lambda d: d["align"]>=2], "1st+KZ+Align>=2"),
        "sweep_1st_align": ([lambda d: d["sweep"], lambda d: d["seq"]==1, lambda d: d["align"]>=2], "Sweep+1st+Align>=2"),
        "fvg_lowwick_align": ([lambda d: d["creates_fvg"], lambda d: d["wick_ratio"]<0.3, lambda d: d["align"]>=2], "FVG+LowWick+Align>=2"),
        # Additional 2-factor combos
        "sweep_kz": ([lambda d: d["sweep"], lambda d: d["kz"]], "Sweep+KZ"),
        "fvg_align3": ([lambda d: d["creates_fvg"], lambda d: d["align"]>=3], "FVG+Align>=3"),
        "1st_disp_fvg": ([lambda d: d["seq"]==1, lambda d: d["creates_fvg"]], "1st+FVG"),
        "kz_align3": ([lambda d: d["kz"], lambda d: d["align"]>=3], "KZ+Align>=3"),
        "sweep_align3": ([lambda d: d["sweep"], lambda d: d["align"]>=3], "Sweep+Align>=3"),
    }

    combo_results = {}
    for name, (filt, label) in combos_def.items():
        combo_results[name] = analyze_combo(disc, filt, label)
        r = combo_results[name]
        if r.get("edge"):
            print(f"  ** CANDIDATE: {label}: n={r['n']}, r3h={r['r3h']:.1%}, ratio={r['ratio']:.1f}x")

    # OB Retest Study
    print("\n  OB retest study...")
    revisited = [d for d in disc if d["origin_revisited"]]
    not_rev = [d for d in disc if not d["origin_revisited"]]
    deep = [d for d in revisited if d["revisit_depth"] and d["revisit_depth"] >= 0.5]
    ote_r = [d for d in revisited if d["revisit_depth"] and 0.62 <= d["revisit_depth"] <= 0.79]
    rev_cont = [d for d in revisited if d["revisit_continued"]]
    rev_mfe = [d["revisit_mfe"] for d in rev_cont if d["revisit_mfe"]]
    nr_mfe = [d["mfe_3h"] for d in not_rev if d["mfe_3h"]]

    ob_study = {
        "total": len(disc),
        "rev": len(revisited), "rev_pct": round(len(revisited)/len(disc), 3) if disc else 0,
        "deep50": len(deep), "deep50_pct": round(len(deep)/len(disc), 3) if disc else 0,
        "ote": len(ote_r), "ote_pct": round(len(ote_r)/len(disc), 3) if disc else 0,
        "rev_cont_rate": round(len(rev_cont)/len(revisited), 3) if revisited else 0,
        "mfe_retest": round(sum(rev_mfe)/len(rev_mfe), 2) if rev_mfe else 0,
        "mfe_close_norev": round(sum(nr_mfe)/len(nr_mfe), 2) if nr_mfe else 0,
        "missed_pct": round(len(not_rev)/len(disc), 3) if disc else 0,
    }
    # Entry timing for continuing disps
    cont_d = [d for d in disc if d["cont_3h"]]
    pb_ct = sum(1 for d in cont_d if d["origin_revisited"])
    rev_t = [d["revisit_candles"] for d in cont_d if d["origin_revisited"] and d["revisit_candles"]]
    rev_dep = [d["revisit_depth"] for d in cont_d if d["origin_revisited"] and d["revisit_depth"] is not None]

    entry_timing = {
        "continuing": len(cont_d),
        "pullback_rate": round(pb_ct/len(cont_d), 3) if cont_d else 0,
        "avg_rev_timing": round(sum(rev_t)/len(rev_t), 1) if rev_t else 0,
        "avg_rev_depth": round(sum(rev_dep)/len(rev_dep), 3) if rev_dep else 0,
    }

    # Exhaustion study
    exhaust_study = {}
    for lbl, fn in [("1st", lambda d: d["seq"]==1), ("2nd", lambda d: d["seq"]==2), ("3rd+", lambda d: d["seq"]>=3)]:
        g = [d for d in disc if fn(d)]
        if g:
            c3 = [d["cont_3h"] for d in g if d.get("cont_3h") is not None]
            mf = [d["mfe_3h"] for d in g if d.get("mfe_3h") is not None]
            ma = [d["mae_3h"] for d in g if d.get("mae_3h") is not None]
            exhaust_study[lbl] = {"n": len(g), "r3h": round(sum(c3)/len(c3),3) if c3 else 0,
                                   "mfe": round(sum(mf)/len(mf),2) if mf else 0,
                                   "mae": round(sum(ma)/len(ma),2) if ma else 0}

    # Counter-trend study
    ct_d = [d for d in disc if d["ct"]]
    ct_rev1h = [d for d in ct_d if not d.get("cont_1h", True)]
    ct_study = {
        "total": len(ct_d),
        "rev_1h": len(ct_rev1h),
        "rev_rate_1h": round(len(ct_rev1h)/len(ct_d), 3) if ct_d else 0,
        "r3h": round(sum(1 for d in ct_d if d.get("cont_3h"))/len(ct_d), 3) if ct_d else 0,
    }

    # ── Validation ───────────────────────────────────────────────────
    print("\n[8] Validation...")
    val_combos = {}
    for name, (filt, label) in combos_def.items():
        vr = analyze_combo(val, filt, label)
        dr = combo_results.get(name, {})
        # Fix 2: Same threshold as discovery: cont>=55%, MFE>1.3*MAE
        rep = (not vr.get("insuf", False) and vr.get("r3h", 0) >= 0.55
               and vr.get("mfe", 0) > 1.3 * vr.get("mae", 999))
        val_combos[name] = {
            "label": label,
            "disc": {"n": dr.get("n",0), "r3h": dr.get("r3h",0), "mfe": dr.get("mfe",0), "mae": dr.get("mae",0)},
            "val": {"n": vr.get("n",0), "r3h": vr.get("r3h",0), "mfe": vr.get("mfe",0), "mae": vr.get("mae",0)},
            "rep": rep,
        }
        status = "REPLICATED" if rep else ("insuf" if vr.get("insuf") else "NOT REP")
        print(f"  {label}: {status} (d={dr.get('r3h',0):.1%} v={vr.get('r3h',0):.1%})")

    # Validate single factors
    val_sf = {}
    for name, params in factors.items():
        val_sf[name] = analyze_factor(val, **params)

    # Validate structural
    val_rev = [d for d in val if d["origin_revisited"]]
    val_ob = round(len(val_rev)/len(val), 3) if val else 0
    val_exhaust = {}
    for lbl, fn in [("1st", lambda d: d["seq"]==1), ("2nd", lambda d: d["seq"]==2), ("3rd+", lambda d: d["seq"]>=3)]:
        g = [d for d in val if fn(d)]
        if g:
            c3 = [d["cont_3h"] for d in g if d.get("cont_3h") is not None]
            val_exhaust[lbl] = {"n": len(g), "r3h": round(sum(c3)/len(c3),3) if c3 else 0}
    val_ct = [d for d in val if d["ct"]]
    val_ct_r1h = round(sum(1 for d in val_ct if not d.get("cont_1h", True))/len(val_ct), 3) if val_ct else 0

    # ── Fix 3: AI System Comparison ────────────────────────────────
    print("\n[9] AI system comparison...")
    ai_trades_path = OUT_DIR / "unified_trades_v2_20260331.json"
    ai_comp = {"available": False}
    if ai_trades_path.exists():
        with open(ai_trades_path) as f:
            ai_trades = json.load(f)
        ai_comp["available"] = True
        ai_comp["total_ai_trades"] = len(ai_trades)

        # Build AI trade lookup: date -> list of {kz, direction}
        ai_by_date = defaultdict(list)
        for t in ai_trades:
            d = t.get("date", "")
            direction = "bullish" if t.get("direction") == "LONG" else "bearish" if t.get("direction") == "SHORT" else None
            kz = t.get("kill_zone", "")
            if d and direction:
                ai_by_date[d].append({"kz": kz, "dir": direction, "r": t.get("r_multiple", 0),
                                       "outcome": t.get("outcome", ""), "grade": t.get("setup_grade", "")})

        ai_dates = set(ai_by_date.keys())
        ai_comp["ai_trade_dates"] = len(ai_dates)

        # Map KZ names: london KZ = 07:00-09:30, ny KZ = 13:00-15:30
        def disp_matches_kz(d_rec, kz_name):
            if kz_name == "london":
                return d_rec["session"] == "london"
            elif kz_name == "ny":
                return d_rec["session"] == "ny"
            return False

        # For each AI trade date: was there a displacement in the same KZ + direction?
        overlap_count = 0
        ai_disp_quality = []  # alignment scores of matching displacements
        for ai_date, ai_list in ai_by_date.items():
            date_disps = [d for d in disps if d["date"] == ai_date]
            for ai_t in ai_list:
                matching = [d for d in date_disps
                           if disp_matches_kz(d, ai_t["kz"]) and d["direction"] == ai_t["dir"]]
                if matching:
                    overlap_count += 1
                    ai_disp_quality.append({
                        "align": max(d["align"] for d in matching),
                        "sweep": any(d["sweep"] for d in matching),
                        "fvg": any(d["creates_fvg"] for d in matching),
                        "body_ratio": max(d["body_ratio"] for d in matching),
                    })

        ai_comp["overlap_count"] = overlap_count
        ai_comp["overlap_rate"] = round(overlap_count / len(ai_trades), 3) if ai_trades else 0

        # Quality of AI-matching displacements vs all displacements
        if ai_disp_quality:
            ai_comp["ai_avg_align"] = round(sum(d["align"] for d in ai_disp_quality) / len(ai_disp_quality), 2)
            ai_comp["ai_sweep_rate"] = round(sum(1 for d in ai_disp_quality if d["sweep"]) / len(ai_disp_quality), 3)
            ai_comp["ai_fvg_rate"] = round(sum(1 for d in ai_disp_quality if d["fvg"]) / len(ai_disp_quality), 3)
        all_avg_align = sum(d["align"] for d in disps) / len(disps) if disps else 0
        all_sweep_rate = sum(1 for d in disps if d["sweep"]) / len(disps) if disps else 0
        all_fvg_rate = sum(1 for d in disps if d["creates_fvg"]) / len(disps) if disps else 0
        ai_comp["all_avg_align"] = round(all_avg_align, 2)
        ai_comp["all_sweep_rate"] = round(all_sweep_rate, 3)
        ai_comp["all_fvg_rate"] = round(all_fvg_rate, 3)

        # Missed opportunities: qualifying displacements on non-AI dates
        # Qualifying = in KZ + alignment>=2 + sweep
        qualifying_non_ai = [d for d in disps
                             if d["date"] not in ai_dates
                             and d["kz"]
                             and d["align"] >= 2
                             and d["sweep"]]
        ai_comp["qualifying_missed"] = len(qualifying_non_ai)
        qual_dates = set(d["date"] for d in qualifying_non_ai)
        ai_comp["qualifying_missed_dates"] = len(qual_dates)

        # What would simple entry produce on these?
        if qualifying_non_ai:
            qm_cont = [d["cont_3h"] for d in qualifying_non_ai if d.get("cont_3h") is not None]
            qm_mfe = [d["mfe_3h"] for d in qualifying_non_ai if d.get("mfe_3h") is not None]
            qm_mae = [d["mae_3h"] for d in qualifying_non_ai if d.get("mae_3h") is not None]
            ai_comp["missed_cont_3h"] = round(sum(qm_cont)/len(qm_cont), 3) if qm_cont else 0
            ai_comp["missed_mfe_3h"] = round(sum(qm_mfe)/len(qm_mfe), 2) if qm_mfe else 0
            ai_comp["missed_mae_3h"] = round(sum(qm_mae)/len(qm_mae), 2) if qm_mae else 0

        # Estimate additional trades/month
        total_months = len(m15) / (96 * 22)
        ai_comp["missed_per_month"] = round(len(qualifying_non_ai) / total_months, 1) if total_months > 0 else 0
        ai_comp["ai_per_month"] = round(len(ai_trades) / total_months, 1) if total_months > 0 else 0

        print(f"  AI trades: {len(ai_trades)}, overlap with displacements: {overlap_count} ({ai_comp['overlap_rate']:.0%})")
        print(f"  Qualifying missed opportunities: {len(qualifying_non_ai)} on {len(qual_dates)} dates")
        print(f"  Missed/month: {ai_comp['missed_per_month']:.1f}")
    else:
        print("  AI trade data not found — skipping comparison")

    # ── Generate Report ──────────────────────────────────────────────
    print("\n[10] Generating report...")

    baseline = sf_results.get("session", {}).get("baseline", 0.5)
    rep_count = sum(1 for v in val_combos.values() if v["rep"])
    cand_count = sum(1 for v in combo_results.values() if v.get("edge"))

    rpt = []
    rpt.append("# Displacement Scanner — Edge Discovery Report")
    rpt.append(f"**Generated:** {ts}")
    rpt.append(f"**Data:** {m15[0]['time']} to {m15[-1]['time']} ({len(m15):,} M15 candles)")
    rpt.append(f"**Split:** {split_time}")
    rpt.append(f"**Scan time:** {_time.time()-t0:.0f}s")
    rpt.append("")

    rpt.append("## Executive Summary")
    rpt.append("")
    rpt.append(f"- **{len(disps):,}** displacements detected (standard={total_by_str['standard']:,}, strong={total_by_str['strong']:,}, extreme={total_by_str['extreme']:,})")
    rpt.append(f"- Discovery: {len(disc):,} | Validation: {len(val):,}")
    rpt.append(f"- Baseline 3h continuation rate: **{baseline:.1%}**")
    rpt.append(f"- **{cand_count}** candidate edges found in discovery")
    rpt.append(f"- **{rep_count}** patterns replicated on validation data")
    rpt.append(f"- OB retest captures **{ob_study['rev_pct']:.0%}** of displacements; **{ob_study['missed_pct']:.0%}** never pull back")
    monthly = len(disps) / (len(m15) / (96 * 22)) if len(m15) > 0 else 0
    rpt.append(f"- Monthly displacement rate: ~{monthly:.0f}/month")
    rpt.append("")

    # Census
    rpt.append("## Section 1: Displacement Census")
    rpt.append("")
    for label, field in [("Session", "session"), ("Direction", "direction"), ("Strength", "strength"), ("Day", "dow")]:
        counts = defaultdict(int)
        for d in disps: counts[d[field]] += 1
        rpt.append(f"**{label}:** " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))
    rpt.append("")

    d1_align = sum(1 for d in disps if d["d1_dir"] == d["direction"])
    rpt.append(f"**D1 Aligned:** {d1_align} ({d1_align/len(disps)*100:.1f}%)")
    kz_ct = sum(1 for d in disps if d["kz"])
    rpt.append(f"**In Kill Zone:** {kz_ct} ({kz_ct/len(disps)*100:.1f}%)")
    rpt.append("")

    # Single Factor
    rpt.append("## Section 2: Single-Factor Results (Discovery)")
    rpt.append("")
    rpt.append(f"Baseline 3h cont: {baseline:.1%}")
    rpt.append("")

    if flagged:
        rpt.append("### Flagged Factors")
        rpt.append("| Factor | Value | n | 1h | 3h | Sess | MFE$ | MAE$ | MFE/MAE | Effect |")
        rpt.append("|--------|-------|---|----|----|------|------|------|---------|--------|")
        for nm, k, g in sorted(flagged, key=lambda x: -abs(x[2]["eff"])):
            rpt.append(f"| {nm} | {k} | {g['n']} | {g['r1h']:.1%} | {g['r3h']:.1%} | {g['rS']:.1%} | ${g['mfe']:.1f} | ${g['mae']:.1f} | {g['ratio']:.1f}x | {g['eff']:+.1%} |")
        rpt.append("")

    # All factors
    rpt.append("### All Factors")
    for name in sorted(sf_results.keys()):
        fd = sf_results[name]
        if not fd["groups"]: continue
        rpt.append(f"\n**{name}:** (baseline={fd['baseline']:.1%})")
        rpt.append("| Value | n | 3h | MFE | MAE | Effect |")
        rpt.append("|-------|---|----|----|-------|--------|")
        for k, g in sorted(fd["groups"].items(), key=lambda x: -x[1]["n"]):
            flag = " *" if g.get("flag") else ""
            rpt.append(f"| {k}{flag} | {g['n']} | {g['r3h']:.1%} | ${g['mfe']:.1f} | ${g['mae']:.1f} | {g['eff']:+.1%} |")
    rpt.append("")

    # Combos
    rpt.append("## Section 3: Combination Results (Discovery)")
    rpt.append("")
    rpt.append("| Combination | n | 3h | MFE | MAE | MFE/MAE | Candidate? |")
    rpt.append("|-------------|---|----|-----|-----|---------|------------|")
    for nm in sorted(combo_results.keys(), key=lambda x: -combo_results[x].get("r3h", 0)):
        r = combo_results[nm]
        if r.get("insuf"):
            rpt.append(f"| {r['label']} | {r['n']} | — | — | — | — | insuf |")
        else:
            rpt.append(f"| {r['label']} | {r['n']} | {r['r3h']:.1%} | ${r['mfe']:.1f} | ${r['mae']:.1f} | {r['ratio']:.1f}x | {'**YES**' if r.get('edge') else 'no'} |")
    rpt.append("")

    # OB Retest
    rpt.append("## Section 4: Entry Timing & OB Retest")
    rpt.append("")
    rpt.append(f"- Pullback rate (continuing disps): **{entry_timing['pullback_rate']:.1%}**")
    rpt.append(f"- Avg pullback timing: {entry_timing['avg_rev_timing']:.1f} candles ({entry_timing['avg_rev_timing']*15:.0f} min)")
    rpt.append(f"- Avg pullback depth: {entry_timing['avg_rev_depth']:.0%} of body")
    rpt.append("")
    rpt.append(f"**OB Retest Study:**")
    rpt.append(f"- All disps that revisit origin: **{ob_study['rev_pct']:.1%}** ({ob_study['rev']}/{ob_study['total']})")
    rpt.append(f"- Deep retest (50%+): {ob_study['deep50_pct']:.1%}")
    rpt.append(f"- OTE retest (62-79%): {ob_study['ote_pct']:.1%}")
    rpt.append(f"- Revisit→continued: **{ob_study['rev_cont_rate']:.1%}**")
    rpt.append(f"- Avg MFE from retest: **${ob_study['mfe_retest']:.1f}**")
    rpt.append(f"- Avg MFE from close (no retest): ${ob_study['mfe_close_norev']:.1f}")
    rpt.append(f"- **Opportunity cost: {ob_study['missed_pct']:.0%} of displacements never pull back**")
    rpt.append("")

    # Structural
    rpt.append("## Section 5: Structural Patterns")
    rpt.append("")
    rpt.append("### Exhaustion (Discovery)")
    rpt.append("| Pos | n | 3h | MFE | MAE |")
    rpt.append("|-----|---|----|-----|-----|")
    for lbl in ["1st", "2nd", "3rd+"]:
        if lbl in exhaust_study:
            e = exhaust_study[lbl]
            rpt.append(f"| {lbl} | {e['n']} | {e['r3h']:.1%} | ${e['mfe']:.1f} | ${e['mae']:.1f} |")
    rpt.append("")

    rpt.append("### Counter-Trend (Discovery)")
    rpt.append(f"- Total: {ct_study['total']}")
    rpt.append(f"- Reversed within 1h: {ct_study['rev_rate_1h']:.1%}")
    rpt.append(f"- Continued at 3h: {ct_study['r3h']:.1%}")
    rpt.append("")

    # Validation
    rpt.append("## Section 6: Validation")
    rpt.append("")
    rpt.append("### Combination Validation")
    rpt.append("| Pattern | Disc n | Disc 3h | Val n | Val 3h | Verdict |")
    rpt.append("|---------|--------|---------|-------|--------|---------|")
    for nm in sorted(val_combos.keys(), key=lambda x: -val_combos[x]["disc"]["r3h"]):
        v = val_combos[nm]
        verdict = "**REPLICATED**" if v["rep"] else "not rep"
        rpt.append(f"| {v['label']} | {v['disc']['n']} | {v['disc']['r3h']:.1%} | {v['val']['n']} | {v['val']['r3h']:.1%} | {verdict} |")
    rpt.append("")

    rpt.append("### Structural Validation")
    rpt.append(f"- OB retest rate: disc={ob_study['rev_pct']:.1%}, val={val_ob:.1%}")
    for lbl in ["1st", "2nd", "3rd+"]:
        de = exhaust_study.get(lbl, {})
        ve = val_exhaust.get(lbl, {})
        if de and ve:
            rpt.append(f"- Exhaustion {lbl}: disc={de['r3h']:.1%}, val={ve['r3h']:.1%}")
    rpt.append(f"- Counter-trend reversal 1h: disc={ct_study['rev_rate_1h']:.1%}, val={val_ct_r1h:.1%}")
    rpt.append("")

    # AI Comparison
    if ai_comp.get("available"):
        rpt.append("## Section 7: AI System Comparison")
        rpt.append("")
        rpt.append(f"**AI Trade Data:** {ai_comp['total_ai_trades']} trades across {ai_comp['ai_trade_dates']} unique dates")
        rpt.append(f"- AI trades/month: {ai_comp['ai_per_month']:.1f}")
        rpt.append("")
        rpt.append(f"**Overlap:** {ai_comp['overlap_count']}/{ai_comp['total_ai_trades']} AI trades ({ai_comp['overlap_rate']:.0%}) had a matching displacement in the same KZ + direction")
        rpt.append("")
        rpt.append("**Quality Comparison (AI trade dates vs all displacements):**")
        rpt.append("| Metric | AI Trade Dates | All Displacements |")
        rpt.append("|--------|----------------|-------------------|")
        rpt.append(f"| Avg alignment | {ai_comp.get('ai_avg_align', 0)} | {ai_comp['all_avg_align']} |")
        rpt.append(f"| Sweep rate | {ai_comp.get('ai_sweep_rate', 0):.0%} | {ai_comp['all_sweep_rate']:.0%} |")
        rpt.append(f"| FVG rate | {ai_comp.get('ai_fvg_rate', 0):.0%} | {ai_comp['all_fvg_rate']:.0%} |")
        rpt.append("")
        rpt.append(f"**Missed Opportunities:** {ai_comp['qualifying_missed']} qualifying displacements on {ai_comp['qualifying_missed_dates']} non-AI dates")
        rpt.append(f"- Qualifying = in KZ + alignment>=2 + sweep detected")
        rpt.append(f"- Estimated additional: **{ai_comp['missed_per_month']:.1f} setups/month**")
        if ai_comp.get("missed_cont_3h"):
            rpt.append(f"- Continuation rate on missed: {ai_comp['missed_cont_3h']:.1%}")
            rpt.append(f"- Avg MFE on missed: ${ai_comp['missed_mfe_3h']:.1f} (MAE: ${ai_comp['missed_mae_3h']:.1f})")
        rpt.append("")

    # Implications
    rpt.append("## Section 8: Implications")
    rpt.append("")
    replicated_names = [v["label"] for v in val_combos.values() if v["rep"]]
    if replicated_names:
        rpt.append("### Replicated Patterns (actionable)")
        for lbl in replicated_names:
            v = [x for x in val_combos.values() if x["label"] == lbl][0]
            rpt.append(f"- **{lbl}**: disc {v['disc']['r3h']:.1%} -> val {v['val']['r3h']:.1%} (n={v['val']['n']})")
        rpt.append("")

    rpt.append("### Key Takeaways")
    if ob_study['rev_pct'] < 0.5:
        rpt.append(f"1. **OB retest is too selective:** Only {ob_study['rev_pct']:.0%} of displacements pull back. The AI misses {ob_study['missed_pct']:.0%} of opportunities.")
    else:
        rpt.append(f"1. **OB retest works well:** {ob_study['rev_pct']:.0%} of displacements do pull back.")

    if exhaust_study.get("1st") and exhaust_study.get("3rd+"):
        diff = exhaust_study["1st"]["r3h"] - exhaust_study["3rd+"]["r3h"]
        if diff > 0.05:
            rpt.append(f"2. **Exhaustion confirmed:** 1st disp {exhaust_study['1st']['r3h']:.1%} vs 3rd+ {exhaust_study['3rd+']['r3h']:.1%} ({diff:+.0%} edge).")
        else:
            rpt.append("2. **No clear exhaustion:** Performance similar across sequence positions.")

    if ct_study["rev_rate_1h"] > 0.5:
        rpt.append(f"3. **Counter-trend disps mostly fail:** {ct_study['rev_rate_1h']:.0%} reverse within 1h — tradeable as trend continuation signal.")
    else:
        rpt.append(f"3. **Counter-trend disps persist:** Only {ct_study['rev_rate_1h']:.0%} reverse within 1h.")

    rpt.append(f"4. **Monthly frequency:** ~{monthly:.0f} displacements/month across all types.")

    if ai_comp.get("available") and ai_comp.get("missed_per_month", 0) > 0:
        rpt.append(f"5. **Additional trades available:** ~{ai_comp['missed_per_month']:.1f} qualifying displacement setups/month on non-AI dates (vs {ai_comp['ai_per_month']:.1f} current AI trades/month).")

    rpt.append("")
    rpt.append("### Methodology Notes")
    rpt.append("- `origin_revisited=False` excluded from flagged factors (tautology: no pullback = price kept moving = continuation by definition)")
    rpt.append(f"- Candidate edge threshold: cont>=55% AND MFE>1.3*MAE AND n>=20 (same for discovery and validation)")

    # Tightness distribution
    rpt.append("")
    rpt.append("### Fix 1 Verification: Tightness Distribution")
    t5_vals = [d["tight"] for d in disps]
    t10_vals = [d["consol"] for d in disps]
    t5_buckets = {"<0.4": 0, "0.4-0.7": 0, "0.7-1.0": 0, ">1.0": 0}
    for v in t5_vals:
        if v < 0.4: t5_buckets["<0.4"] += 1
        elif v < 0.7: t5_buckets["0.4-0.7"] += 1
        elif v < 1.0: t5_buckets["0.7-1.0"] += 1
        else: t5_buckets[">1.0"] += 1
    t10_buckets = {"<0.4": 0, "0.4-0.7": 0, "0.7-1.0": 0, ">1.0": 0}
    for v in t10_vals:
        if v < 0.4: t10_buckets["<0.4"] += 1
        elif v < 0.7: t10_buckets["0.4-0.7"] += 1
        elif v < 1.0: t10_buckets["0.7-1.0"] += 1
        else: t10_buckets[">1.0"] += 1
    rpt.append(f"- **Tightness 5-candle:** " + ", ".join(f"{k}={v} ({v/len(disps)*100:.1f}%)" for k, v in t5_buckets.items()))
    rpt.append(f"- **Consolidation 10-candle:** " + ", ".join(f"{k}={v} ({v/len(disps)*100:.1f}%)" for k, v in t10_buckets.items()))
    rpt.append("")

    # Save
    report_path = OUT_DIR / f"displacement_scan_{ts}.md"
    with open(report_path, "w") as f:
        f.write("\n".join(rpt))
    print(f"  Saved: {report_path}")

    # Save analysis data
    analysis = {
        "meta": {"total": len(disps), "disc": len(disc), "val": len(val),
                 "split": split_time, "ts": ts, "baseline": baseline},
        "single_factor": sf_results,
        "combos": combo_results,
        "validation": val_combos,
        "ob_study": ob_study,
        "entry_timing": entry_timing,
        "exhaust": exhaust_study,
        "ct_study": ct_study,
        "val_sf": val_sf,
        "val_exhaust": val_exhaust,
        "ai_comparison": ai_comp,
    }
    with open(OUT_DIR / f"displacement_scan_data_{ts}.json", "w") as f:
        json.dump(analysis, f, indent=1, default=str)

    print(f"\nTotal time: {_time.time()-t0:.0f}s")
    print("=" * 70)
    print("DONE")


if __name__ == "__main__":
    run()
