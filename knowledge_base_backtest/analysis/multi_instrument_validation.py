#!/usr/bin/env python3
"""Multi-Instrument Validation — Displacement Scan + Pre-Screen + Calibration.

Reuses core functions from displacement_scanner.py, parameterized per instrument.
Runs gold as calibration first, then scans all other instruments independently.
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
from typing import Optional, Dict, Any, List

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent

# Import core functions from the existing scanner
from displacement_scanner import (
    load_csv, parse_time, detect_swings, identify_structure,
    precompute_htf, lookup_htf, get_session, is_kz, kz_minute,
    precompute_session_levels, get_session_hl_before, check_fvg,
    detect_sweep, measure_outcomes, analyze_factor, analyze_combo,
    SESSIONS, KZ_LONDON, KZ_NY,
    DISP_THRESHOLD_STD, DISP_THRESHOLD_STRONG, DISP_THRESHOLD_EXTREME,
)

# ─── Instrument-specific round number check ─────────────────────────
def check_round_number_generic(o, c, rn_step):
    """Round number check parameterized by step size.
    Gold: $25 steps. EURUSD: 0.0100 steps. GBPUSD: 0.0100.
    NAS100: 100pt steps. XAGUSD: $0.50 steps.
    """
    if rn_step <= 0:
        return False, None
    lo, hi = min(o, c), max(o, c)
    lvl = (math.floor(lo / rn_step) + 1) * rn_step
    if lvl < hi:
        return True, round(lvl, 6)
    return False, None


# ─── Per-instrument config ──────────────────────────────────────────
INSTRUMENT_CONFIGS = {
    "XAUUSD": {
        "rn_step": 25.0,       # $25 round numbers
        "pip_size": 0.01,      # Gold: 1 pip = $0.01
        "pip_label": "$",
        "is_forex": True,      # 24/5 forex hours
        "is_index": False,
    },
    "EURUSD": {
        "rn_step": 0.0100,     # 100 pip levels (1.0800, 1.0900, etc.)
        "pip_size": 0.0001,
        "pip_label": "pips",
        "is_forex": True,
        "is_index": False,
    },
    "GBPUSD": {
        "rn_step": 0.0100,
        "pip_size": 0.0001,
        "pip_label": "pips",
        "is_forex": True,
        "is_index": False,
    },
    "XAGUSD": {
        "rn_step": 0.50,       # $0.50 levels
        "pip_size": 0.001,     # Silver: 1 pip = $0.001
        "pip_label": "$",
        "is_forex": True,
        "is_index": False,
    },
    "NAS100": {
        "rn_step": 100.0,      # 100-point levels
        "pip_size": 0.1,       # NAS100: 1 point = 0.1 (10 pips per point)
        "pip_label": "pts",
        "is_forex": False,
        "is_index": True,
    },
}


def compute_equal_tolerance(m15_candles):
    """Compute equal-level tolerance = 0.5 × average M15 body size."""
    bodies = [abs(c["close"] - c["open"]) for c in m15_candles]
    bodies = [b for b in bodies if b > 0]
    if not bodies:
        return 0.01
    avg_body = sum(bodies) / len(bodies)
    return avg_body * 0.5


def compute_basic_stats(m15, d1, symbol, cfg):
    """Compute basic statistics for an instrument."""
    # Price range
    prices = [c["close"] for c in m15]
    price_min, price_max = min(prices), max(prices)

    # Date range
    first_dt = parse_time(m15[0]["time"])
    last_dt = parse_time(m15[-1]["time"])
    trading_days = len(set(parse_time(c["time"]).date() for c in d1))

    # ADR
    daily_ranges = [c["high"] - c["low"] for c in d1]
    adr = sum(daily_ranges) / len(daily_ranges) if daily_ranges else 0

    # M15 ATR distribution
    m15_ranges = sorted([c["high"] - c["low"] for c in m15 if c["high"] - c["low"] > 0])
    n = len(m15_ranges)
    if n > 0:
        m15_atr = {
            "p10": m15_ranges[int(n * 0.10)],
            "p25": m15_ranges[int(n * 0.25)],
            "median": m15_ranges[int(n * 0.50)],
            "p75": m15_ranges[int(n * 0.75)],
            "p90": m15_ranges[int(n * 0.90)],
        }
    else:
        m15_atr = {"p10": 0, "p25": 0, "median": 0, "p75": 0, "p90": 0}

    # Average body
    bodies = [abs(c["close"] - c["open"]) for c in m15 if abs(c["close"] - c["open"]) > 0]
    avg_body = sum(bodies) / len(bodies) if bodies else 0

    # Equal tolerance
    eq_tol = compute_equal_tolerance(m15)

    pip = cfg["pip_size"]
    return {
        "symbol": symbol,
        "data_range": f"{first_dt.date()} to {last_dt.date()}",
        "trading_days": trading_days,
        "m15_candles": len(m15),
        "price_range": f"{price_min:.5f} - {price_max:.5f}",
        "adr": round(adr, 5),
        "adr_pips": round(adr / pip, 1) if pip > 0 else 0,
        "m15_atr": {k: round(v, 6) for k, v in m15_atr.items()},
        "m15_atr_pips": {k: round(v / pip, 1) for k, v in m15_atr.items()} if pip > 0 else {},
        "avg_m15_body": round(avg_body, 6),
        "equal_tolerance": round(eq_tol, 6),
    }


def scan_instrument(symbol, cfg, data_files=None):
    """Run full displacement scan on a single instrument. Completely isolated state."""
    t0 = _time.time()
    print(f"\n{'='*70}")
    print(f"SCANNING: {symbol}")
    print(f"{'='*70}")

    # Load data
    print(f"\n  [{symbol}] Loading data...")
    m15 = load_csv(DATA_DIR / f"{symbol}_M15.csv")
    h1 = load_csv(DATA_DIR / f"{symbol}_H1.csv")
    h4 = load_csv(DATA_DIR / f"{symbol}_H4.csv")
    d1 = load_csv(DATA_DIR / f"{symbol}_D1.csv")
    print(f"  M15={len(m15):,}  H1={len(h1):,}  H4={len(h4):,}  D1={len(d1):,}")

    # Basic stats
    stats = compute_basic_stats(m15, d1, symbol, cfg)
    eq_tol = stats["equal_tolerance"]
    rn_step = cfg["rn_step"]
    pip = cfg["pip_size"]

    print(f"  Equal tolerance: {eq_tol:.6f} ({eq_tol/pip:.1f} {cfg['pip_label']})")
    print(f"  ADR: {stats['adr']:.5f} ({stats['adr_pips']:.1f} {cfg['pip_label']})")

    # Split
    split_idx = len(m15) // 2
    split_time = m15[split_idx]["time"]
    print(f"  Split: idx={split_idx}, date={split_time}")

    # Pre-compute HTF
    print(f"\n  [{symbol}] Pre-computing HTF structures...")
    t1 = _time.time()
    d1_htf = precompute_htf(d1, min_bars=2, lookback=30)
    h4_htf = precompute_htf(h4, min_bars=2, lookback=80)
    h1_htf = precompute_htf(h1, min_bars=2, lookback=168)
    print(f"  D1={len(d1_htf)} H4={len(h4_htf)} H1={len(h1_htf)} ({_time.time()-t1:.1f}s)")

    # Session levels
    print(f"\n  [{symbol}] Pre-computing session levels...")
    sess_levels = precompute_session_levels(m15, d1)
    print(f"  {len(sess_levels)} trading days")

    # H1 Order Blocks
    print(f"\n  [{symbol}] Pre-computing H1 order blocks...")
    h1_obs = []
    h1_swings = detect_swings(h1, min_bars=2)
    h1_highs = [s for s in h1_swings if s["type"] == "high"]
    h1_lows = [s for s in h1_swings if s["type"] == "low"]
    for idx_h in range(1, len(h1_highs)):
        if h1_highs[idx_h]["price"] > h1_highs[idx_h-1]["price"]:
            brk = h1_highs[idx_h]["index"]
            for j in range(brk - 1, max(brk - 10, -1), -1):
                if j < 0: break
                if h1[j]["close"] < h1[j]["open"]:
                    form_dt = parse_time(h1[j]["time"])
                    mit_dt = None
                    for k in range(brk + 1, len(h1)):
                        if h1[k]["low"] <= h1[j]["high"]:
                            mit_dt = parse_time(h1[k]["time"])
                            break
                    h1_obs.append({"type": "bullish", "high": h1[j]["high"], "low": h1[j]["low"],
                                   "form_dt": form_dt, "mit_dt": mit_dt})
                    break
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

    # Rolling averages
    print(f"\n  [{symbol}] Pre-computing rolling averages...")
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

    # ─── SCAN ────────────────────────────────────────────────────────
    print(f"\n  [{symbol}] Scanning for displacements...")
    t1 = _time.time()
    disps = []
    sess_tracker = defaultdict(list)
    total_by_str = {"standard": 0, "strong": 0, "extreme": 0}

    for i in range(50, N):
        if i % 10000 == 0:
            print(f"    {i:,}/{N:,} ({_time.time()-t1:.0f}s)")

        c = m15[i]
        body = abs(c["close"] - c["open"])
        a20 = bavg20[i]
        if a20 <= 0: continue
        ratio = body / a20
        if ratio < DISP_THRESHOLD_STD: continue

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

        has_fvg, fvg_sz, fvg_pct = check_fvg(m15, i)
        has_rn, rn_lvl = check_round_number_generic(c["open"], c["close"], rn_step)

        d1_dir, d1_str = lookup_htf(d1_htf, dt)
        h4_dir, h4_str = lookup_htf(h4_htf, dt)
        h1_dir, h1_str = lookup_htf(h1_htf, dt)

        m15w = m15[max(0, i-30):i]
        if len(m15w) >= 5:
            m15_sw = detect_swings(m15w, 2)
            m15_dir, _ = identify_structure(m15_sw)
        else:
            m15_dir = "insufficient_data"

        align = sum([d1_dir == dr, h4_dir == dr, h1_dir == dr])

        d_date = dt.date()
        sl = sess_levels.get(d_date, {})
        ah = sl.get("asian_high", 0)
        al = sl.get("asian_low", 0)
        ar = sl.get("asian_range", 0)
        adr_val = sl.get("adr", 1)
        pdh = sl.get("pdh", 0)
        pdl = sl.get("pdl", 0)
        arpct = round(ar / adr_val * 100, 1) if adr_val > 0 else 0

        s_hi, s_lo = get_session_hl_before(m15, i, sess, d_date)

        levels = []
        if ah > 0: levels.append(("asian_high", ah, "high"))
        if al > 0: levels.append(("asian_low", al, "low"))
        if pdh > 0: levels.append(("pdh", pdh, "high"))
        if pdl > 0: levels.append(("pdl", pdl, "low"))
        if s_hi: levels.append(("session_high", s_hi, "high"))
        if s_lo and s_lo < 999999: levels.append(("session_low", s_lo, "low"))

        sw = detect_sweep(m15, i, levels)

        if sw["detected"] and adr_val > 0:
            if dr == "bullish" and pdl > 0 and c["close"] < pdl + adr_val * 0.3:
                align += 1
            elif dr == "bearish" and pdh > 0 and c["close"] > pdh - adr_val * 0.3:
                align += 1

        in_disc = in_prem = in_ote = False
        if pdh > 0 and pdl > 0:
            imp_range = pdh - pdl
            if imp_range > 0:
                eq = pdl + imp_range * 0.5
                in_disc = c["close"] < eq
                in_prem = c["close"] > eq
                f62 = pdh - imp_range * 0.618
                f79 = pdh - imp_range * 0.786
                in_ote = f79 <= c["close"] <= f62

        p10 = m15[max(0, i-10):i]
        p5 = m15[max(0, i-5):i]
        p10r = (max(x["high"] for x in p10) - min(x["low"] for x in p10)) if p10 else 0
        p10net = (p10[-1]["close"] - p10[0]["open"]) if p10 else 0
        p10dir = "flat" if abs(p10net) < p10r * 0.2 else ("bullish" if p10net > 0 else "bearish")
        p5r = (max(x["high"] for x in p5) - min(x["low"] for x in p5)) if p5 else 0
        p5ba = (sum(abs(x["close"]-x["open"]) for x in p5)/len(p5)) if p5 else 0
        consol = p10r / (atr20[i] * 4.0) if atr20[i] > 0 else 1
        tight = p5r / (atr20[i] * 2.5) if atr20[i] > 0 else 1

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
        ct = d1_dir in ("bullish", "bearish") and d1_dir != dr

        pd = sl.get("prev_day")
        pdbp = pdrva = 0
        pdd = "unknown"
        if pd:
            pdr2 = pd["high"] - pd["low"]
            pdb2 = abs(pd["close"] - pd["open"])
            pdbp = pdb2/pdr2 if pdr2 > 0 else 0
            pdrva = pdr2/adr_val if adr_val > 0 else 0
            if pdr2 > 0 and pdb2/pdr2 < 0.3: pdd = "doji"
            elif pd["close"] > pd["open"]: pdd = "bullish"
            else: pdd = "bearish"

        mss = (dt.hour - SESSIONS[sess][0]) * 60 + dt.minute
        first_kz = kzm is not None and kzm <= 15

        ob_type = None
        at_ob = False
        breaks_ob = False
        ob_dist = None
        price = c["close"]
        open_p = c["open"]
        nearest_dist = 999999
        for ob in reversed(h1_obs):
            if ob["form_dt"] >= dt: continue
            if ob["mit_dt"] is not None and ob["mit_dt"] < dt: continue
            mid = (ob["high"] + ob["low"]) / 2
            dist = abs(price - mid)
            if dist < nearest_dist:
                nearest_dist = dist
                ob_type = ob["type"]
                at_ob = ob["low"] <= open_p <= ob["high"]
                ob_dist = round(dist / price * 100, 3) if price > 0 else 0
                if ob["type"] != dr:
                    if dr == "bullish" and c["close"] > ob["high"]:
                        breaks_ob = True
                    elif dr == "bearish" and c["close"] < ob["low"]:
                        breaks_ob = True
            if nearest_dist < price * 0.01:
                break

        out = measure_outcomes(m15, i, dr)

        rec = {
            "symbol": symbol,
            "timestamp": c["time"], "date": str(d_date),
            "dow": dt.strftime("%A"), "session": sess,
            "kz": kz_on, "kz_min": kzm, "direction": dr, "strength": strength,
            "body_size": round(body, 6), "body_ratio": round(ratio, 2),
            "body_ratio_50": round(body/bavg50[i], 2) if bavg50[i]>0 else 0,
            "range": round(rng, 6), "wick_ratio": round(wr, 3),
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
            "p10_range": round(p10r, 6), "p10_dir": p10dir,
            "consol": round(consol, 3), "p5_range": round(p5r, 6),
            "p5_bavg": round(p5ba, 6), "tight": round(tight, 3), "p5_char": p5c,
            "seq": seq, "csld": csld, "csls": csls,
            "prior_body": round(pdb, 6) if pdb else None,
            "exhaust": exhaust, "ct": ct,
            "pd_body_pct": round(pdbp, 3), "pd_rva": round(pdrva, 3), "pd_dir": pdd,
            "mss": mss, "kz_min_open": kzm, "first_kz": first_kz,
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
    print(f"\n  [{symbol}] Total: {len(disps):,} displacements in {scan_time:.0f}s")
    for k, v in total_by_str.items():
        print(f"    {k}: {v:,}")

    disc = [d for d in disps if d["set"] == "disc"]
    val = [d for d in disps if d["set"] == "val"]
    print(f"  Discovery: {len(disc):,}  Validation: {len(val):,}")

    # ─── ANALYSIS ────────────────────────────────────────────────────
    print(f"\n  [{symbol}] Running analysis...")

    # Baseline
    all_c3 = [d["cont_3h"] for d in disc if d.get("cont_3h") is not None]
    baseline = sum(all_c3) / len(all_c3) if all_c3 else 0.5

    # Single-factor flagged
    factors = {
        "session": {"field": "session"},
        "kz": {"field": "kz"},
        "d1_aligned": {"value_fn": lambda d: d["d1_dir"] == d["direction"]},
        "align": {"field": "align"},
        "sweep": {"field": "sweep"},
        "creates_fvg": {"field": "creates_fvg"},
        "wick_ratio_bkt": {"bucket_fn": lambda d: "<0.3" if d["wick_ratio"]<0.3 else "0.3-0.5" if d["wick_ratio"]<0.5 else ">0.5"},
        "seq_bkt": {"bucket_fn": lambda d: "1st" if d["seq"]==1 else "2nd" if d["seq"]==2 else "3rd+"},
        "exhaust": {"field": "exhaust"},
        "ct": {"field": "ct"},
        "origin_revisited": {"field": "origin_revisited"},
    }

    sf_results = {}
    flagged = []
    for name, params in factors.items():
        sf_results[name] = analyze_factor(disc, **params)
        for key, grp in sf_results[name]["groups"].items():
            if grp.get("flag"):
                if name == "origin_revisited" and key == "False":
                    grp["flag"] = False
                    continue
                flagged.append((name, key, grp))

    # Combinations (same as gold)
    combos_def = {
        "full_smc": ([lambda d: d["sweep"], lambda d: d["creates_fvg"], lambda d: d["align"]>=3], "Sweep+FVG+Align>=3"),
        "fvg_align3": ([lambda d: d["creates_fvg"], lambda d: d["align"]>=3], "FVG+Align>=3"),
        "sweep_align3": ([lambda d: d["sweep"], lambda d: d["align"]>=3], "Sweep+Align>=3"),
        "fvg_lowwick_align": ([lambda d: d["creates_fvg"], lambda d: d["wick_ratio"]<0.3, lambda d: d["align"]>=2], "FVG+LowWick+Align>=2"),
        "sweep_fvg_kz": ([lambda d: d["sweep"], lambda d: d["creates_fvg"], lambda d: d["kz"]], "Sweep+FVG+KZ"),
        "kz_align3": ([lambda d: d["kz"], lambda d: d["align"]>=3], "KZ+Align>=3"),
        "1st_kz_align": ([lambda d: d["seq"]==1, lambda d: d["kz"], lambda d: d["align"]>=2], "1st+KZ+Align>=2"),
        "sweep_1st_align": ([lambda d: d["sweep"], lambda d: d["seq"]==1, lambda d: d["align"]>=2], "Sweep+1st+Align>=2"),
    }

    combo_results = {}
    for name, (filt, label) in combos_def.items():
        combo_results[name] = analyze_combo(disc, filt, label)

    # Validation
    val_combos = {}
    for name, (filt, label) in combos_def.items():
        vr = analyze_combo(val, filt, label)
        dr_res = combo_results.get(name, {})
        rep = (not vr.get("insuf", False) and vr.get("r3h", 0) >= 0.55
               and vr.get("mfe", 0) > 1.3 * vr.get("mae", 999))
        val_combos[name] = {
            "label": label,
            "disc": {"n": dr_res.get("n",0), "r3h": dr_res.get("r3h",0), "mfe": dr_res.get("mfe",0), "mae": dr_res.get("mae",0)},
            "val": {"n": vr.get("n",0), "r3h": vr.get("r3h",0), "mfe": vr.get("mfe",0), "mae": vr.get("mae",0)},
            "rep": rep,
        }

    # OB Retest Study
    revisited = [d for d in disc if d["origin_revisited"]]
    ob_rate_disc = len(revisited) / len(disc) if disc else 0

    cont_d = [d for d in disc if d["cont_3h"]]
    pb_ct = sum(1 for d in cont_d if d["origin_revisited"])
    rev_t = [d["revisit_candles"] for d in cont_d if d["origin_revisited"] and d["revisit_candles"]]
    rev_dep = [d["revisit_depth"] for d in cont_d if d["origin_revisited"] and d["revisit_depth"] is not None]

    entry_timing = {
        "pullback_rate": round(pb_ct/len(cont_d), 3) if cont_d else 0,
        "avg_timing": round(sum(rev_t)/len(rev_t), 1) if rev_t else 0,
        "avg_depth": round(sum(rev_dep)/len(rev_dep), 3) if rev_dep else 0,
    }

    # OB retest validation
    val_rev = [d for d in val if d["origin_revisited"]]
    ob_rate_val = len(val_rev) / len(val) if val else 0

    # Exhaustion
    exhaust_study = {}
    for lbl, fn in [("1st", lambda d: d["seq"]==1), ("2nd", lambda d: d["seq"]==2), ("3rd+", lambda d: d["seq"]>=3)]:
        g = [d for d in disc if fn(d)]
        if g:
            c3 = [d["cont_3h"] for d in g if d.get("cont_3h") is not None]
            exhaust_study[lbl] = {"n": len(g), "r3h": round(sum(c3)/len(c3),3) if c3 else 0}

    # Counter-trend
    ct_d = [d for d in disc if d["ct"]]
    ct_r3h = round(sum(1 for d in ct_d if d.get("cont_3h"))/len(ct_d), 3) if ct_d else 0

    # FVG creation rate
    fvg_rate = sum(1 for d in disps if d["creates_fvg"]) / len(disps) if disps else 0

    # KZ displacement rate
    kz_ct = sum(1 for d in disps if d["kz"])
    kz_pct = kz_ct / len(disps) if disps else 0

    # Session breakdown
    session_cont = {}
    for sess_name in ["asian", "london", "ny", "late"]:
        g = [d for d in disc if d["session"] == sess_name]
        if len(g) >= 20:
            c3 = [d["cont_3h"] for d in g if d.get("cont_3h") is not None]
            session_cont[sess_name] = round(sum(c3)/len(c3), 3) if c3 else 0

    # Direction balance
    bull_ct = sum(1 for d in disps if d["direction"] == "bullish")
    bear_ct = sum(1 for d in disps if d["direction"] == "bearish")

    # Asian sweep analysis
    asian_sweeps = [d for d in disc if d["sweep_level"] in ("asian_high", "asian_low") and d["session"] == "london"]
    non_asian_sweeps = [d for d in disc if d["sweep"] and d["sweep_level"] not in ("asian_high", "asian_low") and d["session"] == "london"]
    asian_sweep_cont = 0
    if asian_sweeps:
        c3 = [d["cont_3h"] for d in asian_sweeps if d.get("cont_3h") is not None]
        asian_sweep_cont = round(sum(c3)/len(c3), 3) if c3 else 0

    # Monthly rate
    total_months = len(m15) / (96 * 22)
    monthly_rate = len(disps) / total_months if total_months > 0 else 0

    # Replicated count
    rep_count = sum(1 for v in val_combos.values() if v["rep"])
    cand_count = sum(1 for v in combo_results.values() if v.get("edge"))

    result = {
        "symbol": symbol,
        "stats": stats,
        "total_disps": len(disps),
        "total_by_strength": total_by_str,
        "disc_count": len(disc),
        "val_count": len(val),
        "baseline_3h": round(baseline, 3),
        "fvg_rate": round(fvg_rate, 3),
        "kz_pct": round(kz_pct, 3),
        "ob_retest_disc": round(ob_rate_disc, 3),
        "ob_retest_val": round(ob_rate_val, 3),
        "entry_timing": entry_timing,
        "session_cont": session_cont,
        "direction_balance": {"bullish": bull_ct, "bearish": bear_ct},
        "monthly_rate": round(monthly_rate, 1),
        "flagged_factors": [(nm, k, g) for nm, k, g in flagged],
        "combo_results": combo_results,
        "val_combos": val_combos,
        "replicated_count": rep_count,
        "candidate_count": cand_count,
        "exhaust_study": exhaust_study,
        "ct_cont_3h": ct_r3h,
        "ct_count": len(ct_d),
        "asian_sweep_count": len(asian_sweeps),
        "asian_sweep_cont": asian_sweep_cont,
        "scan_time": round(_time.time() - t0, 1),
        "disps": disps,  # full database for saving
    }

    print(f"\n  [{symbol}] DONE in {result['scan_time']}s")
    print(f"    Baseline 3h: {baseline:.1%}")
    print(f"    FVG rate: {fvg_rate:.1%}")
    print(f"    OB retest: disc={ob_rate_disc:.1%} val={ob_rate_val:.1%}")
    print(f"    Pullback timing: {entry_timing['avg_timing']:.1f} candles ({entry_timing['avg_timing']*15:.0f} min)")
    print(f"    Pullback depth: {entry_timing['avg_depth']:.0%}")
    print(f"    Candidates: {cand_count}, Replicated: {rep_count}")
    print(f"    Monthly rate: {monthly_rate:.0f}/month")

    return result


def run_prescreen(symbol):
    """Run D1+H4 pre-screen calibration for an instrument."""
    print(f"\n  [{symbol}] Running pre-screen calibration...")
    d1 = load_csv(DATA_DIR / f"{symbol}_D1.csv")
    h4 = load_csv(DATA_DIR / f"{symbol}_H4.csv")

    # Group D1 by date
    d1_by_date = {}
    for c in d1:
        dt = parse_time(c["time"])
        d1_by_date[dt.date()] = c

    # For each weekday, compute D1 and H4 direction
    d1_dates = sorted(d1_by_date.keys())
    results = {"total": 0, "passing": 0, "bullish": 0, "bearish": 0,
               "fail_d1_unclear": 0, "fail_h4_mismatch": 0, "fail_insuf": 0,
               "by_dow": defaultdict(lambda: {"total": 0, "pass": 0})}

    for i, d in enumerate(d1_dates):
        if d.weekday() >= 5:  # skip weekends
            continue
        results["total"] += 1
        dow = d.strftime("%A")
        results["by_dow"][dow]["total"] += 1

        # D1 structure: last 30 candles up to this date
        d1_window = [d1_by_date[dd] for dd in d1_dates[max(0, i-29):i+1] if dd in d1_by_date]
        if len(d1_window) < 10:
            results["fail_insuf"] += 1
            continue
        d1_sw = detect_swings(d1_window, 2)
        d1_dir, d1_str = identify_structure(d1_sw)

        if d1_dir not in ("bullish", "bearish"):
            results["fail_d1_unclear"] += 1
            continue

        # H4 structure: candles up to this date
        h4_window = [c for c in h4 if parse_time(c["time"]).date() <= d]
        h4_window = h4_window[-80:] if len(h4_window) > 80 else h4_window
        if len(h4_window) < 10:
            results["fail_insuf"] += 1
            continue
        h4_sw = detect_swings(h4_window, 2)
        h4_dir, h4_str = identify_structure(h4_sw)

        if h4_dir != d1_dir:
            results["fail_h4_mismatch"] += 1
            continue

        # Passes!
        results["passing"] += 1
        results["by_dow"][dow]["pass"] += 1
        if d1_dir == "bullish":
            results["bullish"] += 1
        else:
            results["bearish"] += 1

    results["pass_rate"] = round(results["passing"] / results["total"], 3) if results["total"] > 0 else 0
    bull_pct = round(results["bullish"] / results["passing"] * 100, 1) if results["passing"] > 0 else 0
    bear_pct = round(results["bearish"] / results["passing"] * 100, 1) if results["passing"] > 0 else 0
    results["direction_split"] = f"{bull_pct}/{bear_pct}"

    print(f"    Total weekdays: {results['total']}")
    print(f"    Passing: {results['passing']} ({results['pass_rate']:.0%})")
    print(f"    Direction: {bull_pct:.0f}% bull / {bear_pct:.0f}% bear")
    print(f"    Fail reasons: D1 unclear={results['fail_d1_unclear']}, H4 mismatch={results['fail_h4_mismatch']}, insuf={results['fail_insuf']}")

    return results


def compute_daily_returns(symbol):
    """Compute daily returns for correlation analysis."""
    d1 = load_csv(DATA_DIR / f"{symbol}_D1.csv")
    returns = {}
    for c in d1:
        dt = parse_time(c["time"])
        if c["open"] > 0:
            returns[dt.date()] = (c["close"] - c["open"]) / c["open"]
    return returns


def compute_correlation(returns_a, returns_b):
    """Pearson correlation between two return series."""
    common_dates = sorted(set(returns_a.keys()) & set(returns_b.keys()))
    if len(common_dates) < 30:
        return None
    a = [returns_a[d] for d in common_dates]
    b = [returns_b[d] for d in common_dates]
    n = len(a)
    ma = sum(a) / n
    mb = sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / n
    sa = (sum((x - ma)**2 for x in a) / n) ** 0.5
    sb = (sum((x - mb)**2 for x in b) / n) ** 0.5
    if sa == 0 or sb == 0:
        return 0
    return round(cov / (sa * sb), 3)


def verify_gold_calibration(gold_result):
    """Check gold results match known benchmarks."""
    checks = []

    # Original: 6,641 disps from ~47K candles = 14.1% rate
    # Use rate-based comparison since data grows over time
    total = gold_result["total_disps"]
    candles = gold_result["stats"]["m15_candles"]
    rate = total / candles if candles > 0 else 0
    benchmark_rate = 6641 / 47000  # ~0.1413
    rate_diff = abs(rate - benchmark_rate) / benchmark_rate
    checks.append(("Displacement rate", f"{rate:.4f} ({total:,}/{candles:,})", f"~{benchmark_rate:.4f}", rate_diff < 0.10, f"{rate_diff:.1%} diff"))

    # Baseline continuation within 2pp of 48.7%
    baseline = gold_result["baseline_3h"]
    diff = abs(baseline - 0.487)
    checks.append(("Baseline 3h cont", f"{baseline:.1%}", "48.7%", diff < 0.02, f"{diff:.1%} diff"))

    # OB retest within 3pp of 84.1%
    ob = gold_result["ob_retest_disc"]
    diff_ob = abs(ob - 0.841)
    checks.append(("OB retest rate", f"{ob:.1%}", "84.1%", diff_ob < 0.03, f"{diff_ob:.1%} diff"))

    all_pass = True
    print("\n  GOLD CALIBRATION CHECK:")
    for name, actual, expected, passed, note in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"    [{status}] {name}: {actual} (expected {expected}, {note})")

    return all_pass


def score_instrument(result, prescreen):
    """Compute expansion readiness score."""
    score = 0

    # Replicated patterns × 2
    score += result["replicated_count"] * 2

    # OB retest rate / 10
    score += result["ob_retest_disc"] * 10  # scale to ~8 for 80%

    # Pre-screen reasonableness (20-50% ideal)
    ps_rate = prescreen["pass_rate"]
    if 0.20 <= ps_rate <= 0.50:
        score += 3
    elif 0.15 <= ps_rate < 0.20 or 0.50 < ps_rate <= 0.60:
        score += 1

    # Direction balance bonus (closer to 50/50 = better)
    bull = result["direction_balance"]["bullish"]
    bear = result["direction_balance"]["bearish"]
    total = bull + bear
    if total > 0:
        balance = min(bull, bear) / total  # 0=one-sided, 0.5=perfect
        score += balance * 4  # max 2 points

    return round(score, 1)


def traffic_light(result, prescreen):
    """Determine GREEN/YELLOW/RED verdict."""
    rep = result["replicated_count"]
    ob = result["ob_retest_disc"]
    ps = prescreen["pass_rate"]
    baseline = result["baseline_3h"]

    if baseline < 0.45:
        return "RED", "Baseline continuation too low"
    if ob < 0.60:
        return "RED", "OB retest rate too low"
    if rep >= 3 and ob >= 0.70 and 0.20 <= ps <= 0.50:
        return "GREEN", f"{rep} patterns replicated, OB retest {ob:.0%}, pre-screen {ps:.0%}"
    if rep >= 1 or (ob >= 0.60 and baseline >= 0.47):
        return "YELLOW", f"{rep} patterns replicated, OB retest {ob:.0%}"
    return "RED", f"Only {rep} patterns replicated"


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def run():
    t0 = _time.time()
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    print("=" * 70)
    print("MULTI-INSTRUMENT VALIDATION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    instruments = ["XAUUSD", "EURUSD", "GBPUSD", "NAS100", "XAGUSD"]
    all_results = {}
    all_prescreens = {}

    # ─── STEP 0.5: GOLD CALIBRATION ─────────────────────────────────
    print("\n\n*** STEP 0.5: GOLD CALIBRATION CHECK ***")
    gold_result = scan_instrument("XAUUSD", INSTRUMENT_CONFIGS["XAUUSD"])
    cal_pass = verify_gold_calibration(gold_result)
    if not cal_pass:
        print("\n  *** CALIBRATION FAILED — STOPPING ***")
        print("  Debug the scanner before processing other instruments.")
        return
    print("\n  *** CALIBRATION PASSED — proceeding to other instruments ***")
    all_results["XAUUSD"] = gold_result

    # Save gold database
    gold_disps_out = [{k: v for k, v in d.items() if k != "_idx"} for d in gold_result["disps"]]
    with open(OUT_DIR / f"XAUUSD_displacement_database_{ts}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=gold_disps_out[0].keys())
        w.writeheader()
        w.writerows(gold_disps_out)

    # Gold pre-screen
    all_prescreens["XAUUSD"] = run_prescreen("XAUUSD")

    # ─── STEP 1-2: SCAN ALL OTHER INSTRUMENTS ───────────────────────
    for symbol in ["EURUSD", "GBPUSD", "NAS100", "XAGUSD"]:
        cfg = INSTRUMENT_CONFIGS[symbol]
        result = scan_instrument(symbol, cfg)
        all_results[symbol] = result

        # Save per-instrument database
        disps_out = [{k: v for k, v in d.items() if k != "_idx"} for d in result["disps"]]
        if disps_out:
            with open(OUT_DIR / f"{symbol}_displacement_database_{ts}.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=disps_out[0].keys())
                w.writeheader()
                w.writerows(disps_out)

        # Pre-screen
        all_prescreens[symbol] = run_prescreen(symbol)

    # ─── STEP 3: RANKING ────────────────────────────────────────────
    print("\n\n*** STEP 3: INSTRUMENT RANKING ***")

    scores = {}
    verdicts = {}
    for sym in instruments:
        scores[sym] = score_instrument(all_results[sym], all_prescreens[sym])
        verdicts[sym] = traffic_light(all_results[sym], all_prescreens[sym])
        light, reason = verdicts[sym]
        print(f"  {sym}: {light} (score={scores[sym]}) — {reason}")

    # ─── STEP 4: CORRELATION ────────────────────────────────────────
    print("\n\n*** STEP 4: CORRELATION ANALYSIS ***")
    daily_returns = {}
    for sym in instruments:
        daily_returns[sym] = compute_daily_returns(sym)

    corr_matrix = {}
    for i, s1 in enumerate(instruments):
        for s2 in instruments[i+1:]:
            corr = compute_correlation(daily_returns[s1], daily_returns[s2])
            corr_matrix[f"{s1}-{s2}"] = corr
            if corr is not None:
                flag = " ** HIGH" if abs(corr) > 0.6 else ""
                print(f"  {s1} vs {s2}: {corr:+.3f}{flag}")

    # ─── STEP 5: GENERATE REPORT ────────────────────────────────────
    print("\n\n*** STEP 5: GENERATING REPORT ***")

    rpt = []
    rpt.append("# Multi-Instrument Validation Report")
    rpt.append(f"**Generated:** {ts}")
    rpt.append(f"**Total scan time:** {_time.time()-t0:.0f}s")
    rpt.append("")

    # Executive Summary
    green = [s for s in instruments if verdicts[s][0] == "GREEN"]
    yellow = [s for s in instruments if verdicts[s][0] == "YELLOW"]
    red = [s for s in instruments if verdicts[s][0] == "RED"]

    rpt.append("## Executive Summary")
    rpt.append("")
    rpt.append(f"- **{len(instruments)}** instruments scanned with the same displacement methodology")
    rpt.append(f"- **GREEN:** {', '.join(green) if green else 'None'}")
    rpt.append(f"- **YELLOW:** {', '.join(yellow) if yellow else 'None'}")
    rpt.append(f"- **RED:** {', '.join(red) if red else 'None'}")

    if green:
        best = max(green, key=lambda s: scores[s])
        rpt.append(f"- **Best expansion candidate:** {best} (score={scores[best]})")
        total_monthly = sum(all_results[s]["monthly_rate"] for s in green) + all_results["XAUUSD"]["monthly_rate"]
        est_trades = total_monthly * 0.213 * 0.20  # KZ% × AI selection rate (rough)
        rpt.append(f"- Estimated total trades/month with GREEN instruments + gold: ~{est_trades:.0f}")
    elif yellow:
        best = max(yellow, key=lambda s: scores[s])
        rpt.append(f"- **Best candidate for investigation:** {best} (score={scores[best]})")
    rpt.append("")

    # Section 1: Data Inventory
    rpt.append("## Section 1: Data Inventory")
    rpt.append("")
    rpt.append("| Instrument | D1 | H4 | H1 | M15 | M5 | Data Range | Trading Days |")
    rpt.append("|-----------|-----|-----|-----|------|-----|------------|-------------|")
    for sym in instruments:
        s = all_results[sym]["stats"]
        rpt.append(f"| {sym} | Y | Y | Y | Y | Y | {s['data_range']} | {s['trading_days']} |")
    rpt.append("")

    rpt.append("### Basic Statistics")
    rpt.append("")
    pip_col = "ADR (native)"
    rpt.append(f"| Instrument | {pip_col} | ADR (pips/pts) | M15 ATR (median) | Avg M15 Body | Equal Tolerance |")
    rpt.append("|-----------|-----------|----------------|------------------|-------------|-----------------|")
    for sym in instruments:
        s = all_results[sym]["stats"]
        cfg = INSTRUMENT_CONFIGS[sym]
        rpt.append(f"| {sym} | {s['adr']:.5f} | {s['adr_pips']:.1f} {cfg['pip_label']} | {s['m15_atr']['median']:.6f} | {s['avg_m15_body']:.6f} | {s['equal_tolerance']:.6f} |")
    rpt.append("")

    # Section 2: Master Ranking Table
    rpt.append("## Section 2: Master Ranking Table")
    rpt.append("")
    rpt.append("| Metric | XAUUSD (ref) | EURUSD | GBPUSD | NAS100 | XAGUSD |")
    rpt.append("|--------|-------------|--------|--------|--------|--------|")

    def val_or_dash(sym, key, fmt=".1f"):
        r = all_results.get(sym)
        if not r: return "—"
        v = r.get(key)
        if v is None: return "—"
        if isinstance(v, float):
            if "%" in fmt:
                return f"{v:{fmt}}"
            return f"{v:{fmt}}"
        return str(v)

    metrics = [
        ("Total displacements", "total_disps", ","),
        ("Disps/month", "monthly_rate", ".0f"),
        ("Baseline 3h continuation", "baseline_3h", ".1%"),
        ("FVG creation rate", "fvg_rate", ".1%"),
        ("OB retest (disc)", "ob_retest_disc", ".1%"),
        ("OB retest (val)", "ob_retest_val", ".1%"),
        ("KZ displacements (%)", "kz_pct", ".1%"),
        ("Replicated patterns", "replicated_count", "d"),
        ("Candidate edges", "candidate_count", "d"),
    ]

    for label, key, fmt in metrics:
        row = f"| {label}"
        for sym in instruments:
            r = all_results[sym]
            v = r.get(key)
            if v is None:
                row += " | —"
            elif fmt == ",":
                row += f" | {v:,}"
            elif fmt == ".1%":
                row += f" | {v:.1%}"
            elif fmt == ".0f":
                row += f" | {v:.0f}"
            elif fmt == "d":
                row += f" | {v}"
            else:
                row += f" | {v}"
        row += " |"
        rpt.append(row)

    # Entry timing rows
    row = "| Pullback rate"
    for sym in instruments:
        rpt_val = all_results[sym]["entry_timing"]["pullback_rate"]
        row += f" | {rpt_val:.1%}"
    row += " |"
    rpt.append(row)

    row = "| Pullback timing (min)"
    for sym in instruments:
        t_val = all_results[sym]["entry_timing"]["avg_timing"]
        row += f" | {t_val*15:.0f}"
    row += " |"
    rpt.append(row)

    row = "| Pullback depth"
    for sym in instruments:
        d_val = all_results[sym]["entry_timing"]["avg_depth"]
        row += f" | {d_val:.0%}"
    row += " |"
    rpt.append(row)

    # Pre-screen
    row = "| Pre-screen pass rate"
    for sym in instruments:
        ps = all_prescreens[sym]["pass_rate"]
        row += f" | {ps:.0%}"
    row += " |"
    rpt.append(row)

    row = "| Direction balance"
    for sym in instruments:
        ps = all_prescreens[sym]
        row += f" | {ps['direction_split']}"
    row += " |"
    rpt.append(row)

    # Verdict
    row = "| **VERDICT**"
    for sym in instruments:
        light, _ = verdicts[sym]
        row += f" | **{light}**"
    row += " |"
    rpt.append(row)

    row = "| Score"
    for sym in instruments:
        row += f" | {scores[sym]}"
    row += " |"
    rpt.append(row)
    rpt.append("")

    # Section 3: Per-instrument deep dives
    for sym in instruments:
        if sym == "XAUUSD":
            continue  # gold is the reference, already known

        r = all_results[sym]
        light, reason = verdicts[sym]
        ps = all_prescreens[sym]

        rpt.append(f"## {sym} {'Deep Dive' if sym == 'EURUSD' else 'Analysis'} ({light})")
        rpt.append("")
        rpt.append(f"**Verdict:** {light} — {reason}")
        rpt.append(f"**Score:** {scores[sym]}")
        rpt.append("")

        if light == "RED":
            rpt.append(f"This instrument failed the minimum criteria. Baseline 3h continuation: {r['baseline_3h']:.1%}, "
                       f"OB retest: {r['ob_retest_disc']:.1%}, Replicated patterns: {r['replicated_count']}.")
            rpt.append("")
            continue

        # Displacement summary
        rpt.append(f"### Displacement Summary")
        rpt.append(f"- Total: {r['total_disps']:,} ({r['monthly_rate']:.0f}/month)")
        rpt.append(f"- Baseline 3h continuation: {r['baseline_3h']:.1%}")
        rpt.append(f"- FVG creation rate: {r['fvg_rate']:.1%}")
        rpt.append(f"- KZ displacements: {r['kz_pct']:.1%}")
        rpt.append(f"- Direction: {r['direction_balance']['bullish']} bull / {r['direction_balance']['bearish']} bear")
        rpt.append("")

        # Session continuation
        if r["session_cont"]:
            rpt.append("### Session Continuation Rates")
            rpt.append("| Session | 3h Cont |")
            rpt.append("|---------|---------|")
            for sess, rate in sorted(r["session_cont"].items()):
                rpt.append(f"| {sess} | {rate:.1%} |")
            rpt.append("")

        # Combination results
        rpt.append("### Combination Results")
        rpt.append("| Pattern | Disc n | Disc 3h | Val n | Val 3h | Replicated? |")
        rpt.append("|---------|--------|---------|-------|--------|-------------|")
        for name in sorted(r["val_combos"].keys(), key=lambda x: -r["val_combos"][x]["disc"].get("r3h", 0)):
            v = r["val_combos"][name]
            verdict_str = "**YES**" if v["rep"] else "no"
            dn = v["disc"]["n"]
            dr3h = f"{v['disc']['r3h']:.1%}" if dn > 0 else "—"
            vn = v["val"]["n"]
            vr3h = f"{v['val']['r3h']:.1%}" if vn > 0 else "—"
            rpt.append(f"| {v['label']} | {dn} | {dr3h} | {vn} | {vr3h} | {verdict_str} |")
        rpt.append("")

        # OB Retest
        rpt.append("### OB Retest")
        rpt.append(f"- Pullback rate (continuing disps): {r['entry_timing']['pullback_rate']:.1%}")
        rpt.append(f"- Avg timing: {r['entry_timing']['avg_timing']*15:.0f} min")
        rpt.append(f"- Avg depth: {r['entry_timing']['avg_depth']:.0%}")
        rpt.append(f"- OB retest rate: disc={r['ob_retest_disc']:.1%}, val={r['ob_retest_val']:.1%}")
        rpt.append("")

        # Pre-screen
        rpt.append("### Pre-Screen Calibration")
        rpt.append(f"- Pass rate: {ps['pass_rate']:.0%} ({ps['passing']}/{ps['total']} weekdays)")
        rpt.append(f"- Direction: {ps['direction_split']} (bull/bear)")
        rpt.append(f"- Fail: D1 unclear={ps['fail_d1_unclear']}, H4 mismatch={ps['fail_h4_mismatch']}")
        rpt.append("")

        # Asian sweep
        rpt.append("### Asian Sweep Validity")
        rpt.append(f"- Asian level sweeps in London: {r['asian_sweep_count']}")
        if r["asian_sweep_count"] > 0:
            rpt.append(f"- Continuation rate after Asian sweep: {r['asian_sweep_cont']:.1%}")
        rpt.append("")

        # Exhaustion
        if r["exhaust_study"]:
            rpt.append("### Exhaustion Pattern")
            rpt.append("| Position | n | 3h Cont |")
            rpt.append("|----------|---|---------|")
            for lbl in ["1st", "2nd", "3rd+"]:
                if lbl in r["exhaust_study"]:
                    e = r["exhaust_study"][lbl]
                    rpt.append(f"| {lbl} | {e['n']} | {e['r3h']:.1%} |")
            rpt.append("")

        # Parameters
        rpt.append("### Recommended Parameters")
        s = r["stats"]
        cfg = INSTRUMENT_CONFIGS[sym]
        rpt.append(f"- Equal tolerance: {s['equal_tolerance']:.6f} ({s['equal_tolerance']/cfg['pip_size']:.1f} {cfg['pip_label']})")
        rpt.append(f"- Round number step: {cfg['rn_step']}")
        rpt.append(f"- M15 ATR median: {s['m15_atr']['median']:.6f} ({s['m15_atr_pips']['median']:.1f} {cfg['pip_label']})")
        rpt.append("")

    # Section 5: Correlation
    rpt.append("## Correlation Matrix")
    rpt.append("")
    rpt.append("| Pair | Correlation | Note |")
    rpt.append("|------|------------|------|")
    for pair, corr in sorted(corr_matrix.items()):
        if corr is None:
            continue
        note = ""
        if abs(corr) > 0.6:
            note = "HIGH — reduce combined position"
        elif abs(corr) < 0.2:
            note = "Low — good diversification"
        rpt.append(f"| {pair} | {corr:+.3f} | {note} |")
    rpt.append("")

    # Section 6: Expansion Plan
    rpt.append("## Expansion Plan")
    rpt.append("")

    ranked = sorted(instruments[1:], key=lambda s: -scores[s])
    rpt.append("### Recommended Order of Deployment")
    for i, sym in enumerate(ranked):
        light, reason = verdicts[sym]
        rpt.append(f"{i+1}. **{sym}** ({light}, score={scores[sym]}) — {reason}")
    rpt.append("")

    # Estimated frequencies
    rpt.append("### Estimated Trade Frequency")
    rpt.append("| Instrument | Disps/month | KZ Disps/month | Est. Qualifying | Est. AI Trades/month |")
    rpt.append("|-----------|-------------|----------------|-----------------|---------------------|")
    total_est = 0
    for sym in instruments:
        r = all_results[sym]
        kz_per_month = r["monthly_rate"] * r["kz_pct"]
        qualifying = kz_per_month * 0.5  # rough: half have alignment
        ai_est = qualifying * 0.20  # AI picks ~20%
        if verdicts[sym][0] in ("GREEN", "YELLOW") or sym == "XAUUSD":
            total_est += ai_est
        status = verdicts[sym][0] if sym != "XAUUSD" else "LIVE"
        rpt.append(f"| {sym} ({status}) | {r['monthly_rate']:.0f} | {kz_per_month:.0f} | {qualifying:.0f} | {ai_est:.1f} |")
    rpt.append(f"\n**Total estimated trades/month (GREEN+LIVE):** ~{total_est:.0f}")
    rpt.append(f"**Time to 20 demo trades:** ~{20/total_est:.0f} months" if total_est > 0 else "**Cannot estimate**")
    rpt.append("")

    # Save report
    report_path = OUT_DIR / f"multi_instrument_validation_{ts}.md"
    with open(report_path, "w") as f:
        f.write("\n".join(rpt))
    print(f"\n  Report saved: {report_path}")

    # Save combined JSON
    combined = {}
    for sym in instruments:
        r = all_results[sym]
        combined[sym] = {
            k: v for k, v in r.items()
            if k != "disps" and k != "flagged_factors"
        }
        combined[sym]["prescreen"] = all_prescreens[sym]
        combined[sym]["verdict"] = verdicts[sym][0]
        combined[sym]["verdict_reason"] = verdicts[sym][1]
        combined[sym]["score"] = scores[sym]
    combined["correlation"] = corr_matrix

    with open(OUT_DIR / f"multi_instrument_validation_data_{ts}.json", "w") as f:
        json.dump(combined, f, indent=2, default=str)
    print(f"  Data saved: multi_instrument_validation_data_{ts}.json")

    total_time = _time.time() - t0
    print(f"\n{'='*70}")
    print(f"COMPLETE in {total_time:.0f}s")
    print(f"{'='*70}")


if __name__ == "__main__":
    run()
