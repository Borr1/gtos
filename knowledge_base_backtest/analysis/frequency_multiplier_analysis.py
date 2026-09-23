#!/usr/bin/env python3
"""Frequency Multiplier Investigation — Levers 2, 3, 4.

Pure data analysis on existing candle files. No code changes, no frameworks built.
Quantifies opportunity for H4 OB retest, pre-screen loosening, and extended sessions.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time as _time
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime, timedelta, date, time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent

# Import core functions from existing scanner
sys.path.insert(0, str(OUT_DIR))
from displacement_scanner import (
    load_csv, parse_time, detect_swings, identify_structure,
    precompute_htf, lookup_htf, get_session, is_kz, kz_minute,
    precompute_session_levels, measure_outcomes, check_fvg,
    SESSIONS, KZ_LONDON, KZ_NY,
    DISP_THRESHOLD_STD,
)

INSTRUMENTS = ["XAUUSD", "GBPUSD", "EURUSD", "NAS100", "XAGUSD"]

INST_CFG = {
    "XAUUSD": {"rn_step": 25.0, "pip_size": 0.01},
    "EURUSD": {"rn_step": 0.0100, "pip_size": 0.0001},
    "GBPUSD": {"rn_step": 0.0100, "pip_size": 0.0001},
    "XAGUSD": {"rn_step": 0.50, "pip_size": 0.001},
    "NAS100": {"rn_step": 100.0, "pip_size": 0.1},
}

# ═══════════════════════════════════════════════════════════════════════
# Data loading
# ═══════════════════════════════════════════════════════════════════════

def load_instrument(symbol):
    """Load all timeframes for an instrument."""
    data = {}
    for tf in ("D1", "H4", "H1", "M15"):
        path = DATA_DIR / f"{symbol}_{tf}.csv"
        if path.exists():
            data[tf] = load_csv(str(path))
            print(f"  {symbol} {tf}: {len(data[tf])} candles")
        else:
            print(f"  {symbol} {tf}: MISSING")
            data[tf] = []
    return data


def get_trading_dates(m15_candles):
    """Extract unique trading dates from M15 data."""
    dates = set()
    for c in m15_candles:
        dt = parse_time(c["time"])
        if dt.weekday() < 5:  # Mon-Fri
            dates.add(dt.date())
    return sorted(dates)


# ═══════════════════════════════════════════════════════════════════════
# H4 OB Detection (Lever 2)
# ═══════════════════════════════════════════════════════════════════════

def find_h4_obs(h4_candles, min_bars=2):
    """Find all H4 order blocks with their formation details."""
    swings = detect_swings(h4_candles, min_bars=min_bars)
    structure_dir, _ = identify_structure(swings)

    # Detect BOS/CHoCH on H4
    highs = [s for s in swings if s["type"] == "high"]
    lows = [s for s in swings if s["type"] == "low"]

    events = []
    broken_levels = set()

    avg_body = 0
    recent_bodies = [abs(c["close"] - c["open"]) for c in h4_candles[-20:]]
    if recent_bodies:
        avg_body = sum(recent_bodies) / len(recent_bodies)

    for i, c in enumerate(h4_candles):
        body = abs(c["close"] - c["open"])
        disp = body / avg_body if avg_body > 0 else 0

        if structure_dir == "bullish":
            recent_high = None
            for s in reversed(swings):
                if s["type"] == "high" and s["index"] < i:
                    recent_high = s
                    break
            if recent_high and c["close"] > recent_high["price"] and recent_high["price"] not in broken_levels:
                broken_levels.add(recent_high["price"])
                events.append({"type": "BOS", "dir": "bullish", "idx": i, "disp": disp})
        elif structure_dir == "bearish":
            recent_low = None
            for s in reversed(swings):
                if s["type"] == "low" and s["index"] < i:
                    recent_low = s
                    break
            if recent_low and c["close"] < recent_low["price"] and recent_low["price"] not in broken_levels:
                broken_levels.add(recent_low["price"])
                events.append({"type": "BOS", "dir": "bearish", "idx": i, "disp": disp})

    # Find OBs from events
    obs = []
    seen = set()
    for ev in events:
        break_idx = ev["idx"]
        if ev["dir"] == "bullish":
            for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
                if j < 0:
                    break
                if h4_candles[j]["close"] < h4_candles[j]["open"]:  # bearish candle
                    if j in seen:
                        break
                    seen.add(j)
                    ob_high = h4_candles[j]["high"]
                    ob_low = h4_candles[j]["low"]
                    # Check mitigation
                    mitigated = False
                    mitigated_idx = None
                    for k in range(break_idx + 1, len(h4_candles)):
                        if h4_candles[k]["low"] <= ob_high:
                            mitigated = True
                            mitigated_idx = k
                            break
                    obs.append({
                        "direction": "bullish",
                        "high": ob_high, "low": ob_low,
                        "formation_idx": j,
                        "formation_time": h4_candles[j]["time"],
                        "bos_idx": break_idx,
                        "mitigated": mitigated,
                        "mitigated_idx": mitigated_idx,
                        "zone_width": ob_high - ob_low,
                    })
                    break
        elif ev["dir"] == "bearish":
            for j in range(break_idx - 1, max(break_idx - 10, -1), -1):
                if j < 0:
                    break
                if h4_candles[j]["close"] > h4_candles[j]["open"]:  # bullish candle
                    if j in seen:
                        break
                    seen.add(j)
                    ob_high = h4_candles[j]["high"]
                    ob_low = h4_candles[j]["low"]
                    mitigated = False
                    mitigated_idx = None
                    for k in range(break_idx + 1, len(h4_candles)):
                        if h4_candles[k]["high"] >= ob_low:
                            mitigated = True
                            mitigated_idx = k
                            break
                    obs.append({
                        "direction": "bearish",
                        "high": ob_high, "low": ob_low,
                        "formation_idx": j,
                        "formation_time": h4_candles[j]["time"],
                        "bos_idx": break_idx,
                        "mitigated": mitigated,
                        "mitigated_idx": mitigated_idx,
                        "zone_width": ob_high - ob_low,
                    })
                    break

    return obs, structure_dir


def analyze_lever2(symbol, data):
    """Lever 2: H4 OB Retest opportunity sizing."""
    print(f"\n{'='*60}")
    print(f"  LEVER 2: H4 OB Retest — {symbol}")
    print(f"{'='*60}")

    d1 = data["D1"]
    h4 = data["H4"]
    h1 = data["H1"]
    m15 = data["M15"]

    if not h4 or not m15 or not d1:
        return {"symbol": symbol, "error": "missing data"}

    # Build date index for M15
    m15_by_date = defaultdict(list)
    for i, c in enumerate(m15):
        dt = parse_time(c["time"])
        m15_by_date[dt.date()].append((i, dt, c))

    # Pre-compute HTF structures
    d1_htf = precompute_htf(d1, min_bars=2, lookback=30)
    h4_htf = precompute_htf(h4, min_bars=2, lookback=80)
    h1_htf = precompute_htf(h1, min_bars=2, lookback=168)

    # Build H4 time index
    h4_time_idx = {}
    for i, c in enumerate(h4):
        h4_time_idx[parse_time(c["time"])] = i

    # Find ALL H4 OBs across the dataset
    all_h4_obs, _ = find_h4_obs(h4, min_bars=2)
    print(f"  Total H4 OBs found: {len(all_h4_obs)}")

    # For each trading date, check: D1 direction, H4 direction, H4 OBs aligned + unmitigated
    trading_dates = get_trading_dates(m15)
    results = {
        "total_dates": len(trading_dates),
        "d1_clear_dates": 0,
        "d1h4_aligned_dates": 0,
        "h4_ob_opportunities": [],
        "h4_ob_kz_retests": 0,
        "h4_ob_extended_retests": 0,
        "h1_overlap_dates": set(),
        "h4_only_dates": set(),
        "outcomes": [],
    }

    for td in trading_dates:
        td_dt = datetime.combine(td, time(7, 0))

        d1_dir, _ = lookup_htf(d1_htf, td_dt)
        if d1_dir not in ("bullish", "bearish"):
            continue
        results["d1_clear_dates"] += 1

        h4_dir, _ = lookup_htf(h4_htf, td_dt)
        if h4_dir != d1_dir:
            continue
        results["d1h4_aligned_dates"] += 1

        # Find unmitigated H4 OBs aligned with direction, formed before today
        for ob in all_h4_obs:
            ob_form_dt = parse_time(ob["formation_time"])
            if ob_form_dt.date() >= td:
                continue  # formed today or after
            if ob["direction"] != d1_dir:
                continue
            # Check if mitigated before today
            if ob["mitigated"] and ob["mitigated_idx"] is not None:
                mit_dt = parse_time(h4[ob["mitigated_idx"]]["time"])
                if mit_dt.date() < td:
                    continue  # already mitigated

            # OB is unmitigated and aligned — check if M15 price reaches the zone today
            ob_high = ob["high"]
            ob_low = ob["low"]

            kz_touch = False
            extended_touch = False
            touch_idx = None

            if td in m15_by_date:
                for m_idx, m_dt, m_c in m15_by_date[td]:
                    # Check if price reaches OB zone
                    if ob["direction"] == "bullish":
                        # Bullish OB: price pulls back DOWN to the zone
                        if m_c["low"] <= ob_high:
                            extended_touch = True
                            if touch_idx is None:
                                touch_idx = m_idx
                            minutes = m_dt.hour * 60 + m_dt.minute
                            if (KZ_LONDON[0] <= minutes < KZ_LONDON[1]) or (KZ_NY[0] <= minutes < KZ_NY[1]):
                                kz_touch = True
                    else:
                        # Bearish OB: price pulls back UP to the zone
                        if m_c["high"] >= ob_low:
                            extended_touch = True
                            if touch_idx is None:
                                touch_idx = m_idx
                            minutes = m_dt.hour * 60 + m_dt.minute
                            if (KZ_LONDON[0] <= minutes < KZ_LONDON[1]) or (KZ_NY[0] <= minutes < KZ_NY[1]):
                                kz_touch = True

            if kz_touch:
                results["h4_ob_kz_retests"] += 1
                results["h4_ob_opportunities"].append({
                    "date": td.isoformat(),
                    "direction": d1_dir,
                    "ob_zone": [ob_low, ob_high],
                    "zone_width": ob["zone_width"],
                    "kz_touch": True,
                })

                # Measure outcome from touch point
                if touch_idx is not None and touch_idx + 12 < len(m15):
                    outcome = measure_outcomes(m15, touch_idx, d1_dir)
                    outcome["date"] = td.isoformat()
                    results["outcomes"].append(outcome)

            elif extended_touch:
                results["h4_ob_extended_retests"] += 1

    # Analysis 2B: Overlap with H1 OB retest
    # Check which dates pass the standard pre-screen (proxy for H1 trade potential)
    prescreen_pass_dates = set()
    for td in trading_dates:
        td_dt = datetime.combine(td, time(7, 0))
        d1_dir, _ = lookup_htf(d1_htf, td_dt)
        h4_dir, _ = lookup_htf(h4_htf, td_dt)
        if d1_dir in ("bullish", "bearish") and h4_dir == d1_dir:
            prescreen_pass_dates.add(td)

    h4_opp_dates = set(o["date"] for o in results["h4_ob_opportunities"])
    h4_opp_dates_parsed = set(date.fromisoformat(d) for d in h4_opp_dates)
    overlap = h4_opp_dates_parsed & prescreen_pass_dates
    h4_only = h4_opp_dates_parsed - prescreen_pass_dates
    results["overlap_count"] = len(overlap)
    results["h4_only_count"] = len(h4_only)
    results["overlap_pct"] = round(len(overlap) / max(1, len(h4_opp_dates_parsed)) * 100, 1)

    # Outcome stats
    if results["outcomes"]:
        cont_3h = [o["cont_3h"] for o in results["outcomes"] if o.get("cont_3h") is not None]
        mfe_3h = [o["mfe_3h"] for o in results["outcomes"] if o.get("mfe_3h") is not None]
        mae_3h = [o["mae_3h"] for o in results["outcomes"] if o.get("mae_3h") is not None]
        results["cont_3h_rate"] = round(sum(cont_3h) / len(cont_3h) * 100, 1) if cont_3h else 0
        results["avg_mfe_3h"] = round(sum(mfe_3h) / len(mfe_3h), 4) if mfe_3h else 0
        results["avg_mae_3h"] = round(sum(mae_3h) / len(mae_3h), 4) if mae_3h else 0
        results["mfe_mae_ratio"] = round(results["avg_mfe_3h"] / results["avg_mae_3h"], 2) if results["avg_mae_3h"] > 0 else 0

    # Convert to months
    if trading_dates:
        months = (trading_dates[-1] - trading_dates[0]).days / 30.44
        results["kz_retests_per_month"] = round(results["h4_ob_kz_retests"] / max(1, months), 1)
        results["extended_retests_per_month"] = round(results["h4_ob_extended_retests"] / max(1, months), 1)
        results["months_covered"] = round(months, 1)

    # Avg zone width
    if results["h4_ob_opportunities"]:
        widths = [o["zone_width"] for o in results["h4_ob_opportunities"]]
        results["avg_zone_width"] = round(sum(widths) / len(widths), 4)
    else:
        results["avg_zone_width"] = 0

    print(f"  D1 clear dates: {results['d1_clear_dates']}")
    print(f"  D1+H4 aligned dates: {results['d1h4_aligned_dates']}")
    print(f"  H4 OB KZ retests: {results['h4_ob_kz_retests']} ({results.get('kz_retests_per_month', 0)}/mo)")
    print(f"  H4 OB extended retests: {results['h4_ob_extended_retests']} ({results.get('extended_retests_per_month', 0)}/mo)")
    print(f"  Overlap with prescreen-pass dates: {results['overlap_pct']}%")
    if results["outcomes"]:
        print(f"  3h continuation rate: {results['cont_3h_rate']}%")
        print(f"  MFE/MAE ratio: {results['mfe_mae_ratio']}")
    print(f"  Avg zone width: {results['avg_zone_width']}")

    # Clean up non-serializable
    results.pop("h1_overlap_dates", None)
    results.pop("h4_only_dates", None)
    return results


# ═══════════════════════════════════════════════════════════════════════
# Pre-screen loosening (Lever 3)
# ═══════════════════════════════════════════════════════════════════════

def analyze_lever3(symbol, data):
    """Lever 3: Pre-screen loosening — categorize killed dates."""
    print(f"\n{'='*60}")
    print(f"  LEVER 3: Pre-Screen Loosening — {symbol}")
    print(f"{'='*60}")

    d1 = data["D1"]
    h4 = data["H4"]
    h1 = data["H1"]
    m15 = data["M15"]

    if not m15 or not d1:
        return {"symbol": symbol, "error": "missing data"}

    d1_htf = precompute_htf(d1, min_bars=2, lookback=30)
    h4_htf = precompute_htf(h4, min_bars=2, lookback=80)
    h1_htf = precompute_htf(h1, min_bars=2, lookback=168)

    trading_dates = get_trading_dates(m15)
    m15_by_date = defaultdict(list)
    for i, c in enumerate(m15):
        dt = parse_time(c["time"])
        m15_by_date[dt.date()].append((i, dt, c))

    results = {
        "total_dates": len(trading_dates),
        "prescreen_pass": 0,
        "prescreen_kill": 0,
        "cat1_d1_unclear_h4_clear_h1_aligned": 0,
        "cat2_d1_unclear_h4_unclear": 0,
        "cat3_d1_clear_h4_mismatch": 0,
        "cat4_d1_unclear_h4_clear_h1_conflict": 0,
        "other_kills": 0,
        "cat1_with_displacement": 0,
        "cat1_with_disp_and_retest": 0,
        "cat1_outcomes": [],
    }

    # Compute rolling avg body for displacement detection
    bavg = {}
    for i in range(20, len(m15)):
        bodies = [abs(m15[j]["close"] - m15[j]["open"]) for j in range(i-20, i)]
        bavg[i] = sum(bodies) / 20

    for td in trading_dates:
        td_dt = datetime.combine(td, time(7, 0))

        d1_dir, _ = lookup_htf(d1_htf, td_dt)
        h4_dir, _ = lookup_htf(h4_htf, td_dt)
        h1_dir, _ = lookup_htf(h1_htf, td_dt)

        # Standard pre-screen
        if d1_dir in ("bullish", "bearish") and h4_dir == d1_dir:
            results["prescreen_pass"] += 1
            continue

        results["prescreen_kill"] += 1

        # Categorize the kill
        if d1_dir not in ("bullish", "bearish"):
            # D1 unclear
            if h4_dir in ("bullish", "bearish"):
                if h1_dir == h4_dir:
                    results["cat1_d1_unclear_h4_clear_h1_aligned"] += 1

                    # Check for displacement + OB retest during KZ
                    trade_dir = h4_dir
                    has_disp = False
                    has_retest = False

                    if td in m15_by_date:
                        for m_idx, m_dt, m_c in m15_by_date[td]:
                            minutes = m_dt.hour * 60 + m_dt.minute
                            if not ((KZ_LONDON[0] <= minutes < KZ_LONDON[1]) or (KZ_NY[0] <= minutes < KZ_NY[1])):
                                continue
                            if m_idx not in bavg:
                                continue

                            body = abs(m_c["close"] - m_c["open"])
                            ratio = body / bavg[m_idx] if bavg[m_idx] > 0 else 0

                            if ratio >= DISP_THRESHOLD_STD:
                                # Check direction alignment
                                is_bull_disp = m_c["close"] > m_c["open"]
                                if (trade_dir == "bullish" and is_bull_disp) or (trade_dir == "bearish" and not is_bull_disp):
                                    has_disp = True

                                    # Check origin revisit (OB retest proxy)
                                    origin = m_c["open"] if is_bull_disp else m_c["close"]
                                    for k in range(m_idx + 1, min(m_idx + 19, len(m15))):
                                        if is_bull_disp and m15[k]["low"] <= origin + body * 0.2:
                                            has_retest = True
                                            break
                                        elif not is_bull_disp and m15[k]["high"] >= origin - body * 0.2:
                                            has_retest = True
                                            break

                                    if has_disp:
                                        # Measure outcome
                                        outcome = measure_outcomes(m15, m_idx, trade_dir)
                                        outcome["date"] = td.isoformat()
                                        results["cat1_outcomes"].append(outcome)
                                        break  # one displacement per date is enough

                    if has_disp:
                        results["cat1_with_displacement"] += 1
                    if has_retest:
                        results["cat1_with_disp_and_retest"] += 1

                else:
                    results["cat4_d1_unclear_h4_clear_h1_conflict"] += 1
            else:
                results["cat2_d1_unclear_h4_unclear"] += 1
        elif d1_dir in ("bullish", "bearish"):
            if h4_dir not in ("bullish", "bearish") or h4_dir != d1_dir:
                results["cat3_d1_clear_h4_mismatch"] += 1
            else:
                results["other_kills"] += 1
        else:
            results["other_kills"] += 1

    # Outcome analysis for cat1
    if results["cat1_outcomes"]:
        cont = [o["cont_3h"] for o in results["cat1_outcomes"] if o.get("cont_3h") is not None]
        mfe = [o["mfe_3h"] for o in results["cat1_outcomes"] if o.get("mfe_3h") is not None]
        mae = [o["mae_3h"] for o in results["cat1_outcomes"] if o.get("mae_3h") is not None]
        results["cat1_cont_3h_rate"] = round(sum(cont)/len(cont)*100, 1) if cont else 0
        results["cat1_avg_mfe"] = round(sum(mfe)/len(mfe), 4) if mfe else 0
        results["cat1_avg_mae"] = round(sum(mae)/len(mae), 4) if mae else 0
        results["cat1_mfe_mae_ratio"] = round(results["cat1_avg_mfe"]/results["cat1_avg_mae"], 2) if results["cat1_avg_mae"] > 0 else 0

    months = (trading_dates[-1] - trading_dates[0]).days / 30.44 if trading_dates else 1
    results["cat1_per_month"] = round(results["cat1_d1_unclear_h4_clear_h1_aligned"] / months, 1)
    results["cat1_disp_per_month"] = round(results["cat1_with_displacement"] / months, 1)
    results["prescreen_pass_rate"] = round(results["prescreen_pass"] / max(1, results["total_dates"]) * 100, 1)
    results["prescreen_kill_rate"] = round(results["prescreen_kill"] / max(1, results["total_dates"]) * 100, 1)

    print(f"  Total dates: {results['total_dates']}")
    print(f"  Pre-screen pass: {results['prescreen_pass']} ({results['prescreen_pass_rate']}%)")
    print(f"  Pre-screen kill: {results['prescreen_kill']} ({results['prescreen_kill_rate']}%)")
    print(f"  Cat1 (D1 unclear, H4+H1 aligned): {results['cat1_d1_unclear_h4_clear_h1_aligned']} ({results['cat1_per_month']}/mo)")
    print(f"  Cat2 (D1+H4 unclear): {results['cat2_d1_unclear_h4_unclear']}")
    print(f"  Cat3 (D1 clear, H4 mismatch): {results['cat3_d1_clear_h4_mismatch']}")
    print(f"  Cat4 (D1 unclear, H4 clear, H1 conflict): {results['cat4_d1_unclear_h4_clear_h1_conflict']}")
    print(f"  Cat1 with displacement: {results['cat1_with_displacement']} ({results['cat1_disp_per_month']}/mo)")
    print(f"  Cat1 with disp+retest: {results['cat1_with_disp_and_retest']}")
    if results.get("cat1_cont_3h_rate"):
        print(f"  Cat1 3h continuation rate: {results['cat1_cont_3h_rate']}%")
        print(f"  Cat1 MFE/MAE ratio: {results['cat1_mfe_mae_ratio']}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# Extended Sessions (Lever 4)
# ═══════════════════════════════════════════════════════════════════════

def analyze_lever4(symbol, data):
    """Lever 4: Displacement activity and quality by hour."""
    print(f"\n{'='*60}")
    print(f"  LEVER 4: Extended Sessions — {symbol}")
    print(f"{'='*60}")

    m15 = data["M15"]
    d1 = data["D1"]
    h4 = data["H4"]
    h1 = data["H1"]

    if not m15:
        return {"symbol": symbol, "error": "missing M15 data"}

    # Pre-compute HTF
    d1_htf = precompute_htf(d1, min_bars=2, lookback=30)
    h4_htf = precompute_htf(h4, min_bars=2, lookback=80)

    # Compute rolling avg body
    bavg = {}
    for i in range(20, len(m15)):
        bodies = [abs(m15[j]["close"] - m15[j]["open"]) for j in range(i-20, i)]
        bavg[i] = sum(bodies) / 20

    trading_dates = get_trading_dates(m15)
    total_days = len(trading_dates)
    months = (trading_dates[-1] - trading_dates[0]).days / 30.44 if len(trading_dates) > 1 else 1

    # Hourly displacement analysis
    hourly = defaultdict(lambda: {
        "disp_count": 0, "cont_3h_list": [], "mfe_list": [], "mae_list": [],
        "origin_revisit_list": [], "aligned_count": 0,
    })

    for i in range(20, len(m15) - 12):
        c = m15[i]
        dt = parse_time(c["time"])
        if dt.weekday() >= 5:
            continue
        if i not in bavg:
            continue

        body = abs(c["close"] - c["open"])
        ratio = body / bavg[i] if bavg[i] > 0 else 0

        if ratio >= DISP_THRESHOLD_STD:
            hour = dt.hour
            is_bull = c["close"] > c["open"]
            direction = "bullish" if is_bull else "bearish"

            hourly[hour]["disp_count"] += 1

            # Check HTF alignment
            d1_dir, _ = lookup_htf(d1_htf, dt)
            h4_dir, _ = lookup_htf(h4_htf, dt)
            if d1_dir == direction and h4_dir == direction:
                hourly[hour]["aligned_count"] += 1

            # Measure outcomes
            outcome = measure_outcomes(m15, i, direction)
            if outcome.get("cont_3h") is not None:
                hourly[hour]["cont_3h_list"].append(outcome["cont_3h"])
            if outcome.get("mfe_3h") is not None:
                hourly[hour]["mfe_list"].append(outcome["mfe_3h"])
            if outcome.get("mae_3h") is not None:
                hourly[hour]["mae_list"].append(outcome["mae_3h"])
            if outcome.get("origin_revisited") is not None:
                hourly[hour]["origin_revisit_list"].append(outcome["origin_revisited"])

    # Compile hourly stats
    hourly_stats = {}
    total_disps = sum(h["disp_count"] for h in hourly.values())

    for hour in range(24):
        h = hourly[hour]
        n = h["disp_count"]
        cont = h["cont_3h_list"]
        mfe = h["mfe_list"]
        mae = h["mae_list"]
        revisit = h["origin_revisit_list"]

        hourly_stats[hour] = {
            "disp_count": n,
            "disps_per_day": round(n / max(1, total_days), 3),
            "pct_of_total": round(n / max(1, total_disps) * 100, 1),
            "cont_3h_rate": round(sum(cont)/len(cont)*100, 1) if cont else None,
            "avg_mfe": round(sum(mfe)/len(mfe), 4) if mfe else None,
            "avg_mae": round(sum(mae)/len(mae), 4) if mae else None,
            "mfe_mae_ratio": round((sum(mfe)/len(mfe)) / (sum(mae)/len(mae)), 2) if mae and sum(mae) > 0 else None,
            "ob_retest_rate": round(sum(revisit)/len(revisit)*100, 1) if revisit else None,
            "aligned_count": h["aligned_count"],
            "aligned_pct": round(h["aligned_count"] / max(1, n) * 100, 1),
        }

    # Current KZ capture rate
    kz_disps = sum(hourly_stats[h]["disp_count"] for h in range(7, 10))  # 07-09 (London core)
    kz_disps += sum(hourly_stats[h]["disp_count"] for h in range(13, 16))  # 13-15 (NY core)
    kz_capture_pct = round(kz_disps / max(1, total_disps) * 100, 1)

    # Candidate extension windows
    windows = {
        "09:30-12:00 Extended London": list(range(9, 12)),
        "12:00-13:00 London-NY gap": [12],
        "15:30-17:00 Extended NY": list(range(15, 17)),
        "22:00-02:00 Asian open": [22, 23, 0, 1],
        "05:00-07:00 Pre-London": [5, 6],
    }

    window_stats = {}
    for name, hours in windows.items():
        n = sum(hourly_stats.get(h, {}).get("disp_count", 0) for h in hours)
        conts = []
        mfes = []
        maes = []
        for h in hours:
            conts.extend(hourly[h]["cont_3h_list"])
            mfes.extend(hourly[h]["mfe_list"])
            maes.extend(hourly[h]["mae_list"])

        window_stats[name] = {
            "disp_count": n,
            "disps_per_month": round(n / max(1, months), 1),
            "cont_3h_rate": round(sum(conts)/len(conts)*100, 1) if conts else None,
            "avg_mfe": round(sum(mfes)/len(mfes), 4) if mfes else None,
            "avg_mae": round(sum(maes)/len(maes), 4) if maes else None,
            "mfe_mae_ratio": round((sum(mfes)/len(mfes))/(sum(maes)/len(maes)), 2) if maes and sum(maes) > 0 else None,
            "worth_testing": None,  # filled below
        }

        # Worth testing? needs cont >= 45% AND meaningful frequency
        cont_rate = window_stats[name]["cont_3h_rate"]
        freq = window_stats[name]["disps_per_month"]
        if cont_rate is not None and freq > 5:
            window_stats[name]["worth_testing"] = cont_rate >= 45 and (window_stats[name]["mfe_mae_ratio"] or 0) >= 1.0
        else:
            window_stats[name]["worth_testing"] = False

    results = {
        "symbol": symbol,
        "total_disps": total_disps,
        "total_days": total_days,
        "months": round(months, 1),
        "kz_capture_pct": kz_capture_pct,
        "hourly_stats": hourly_stats,
        "window_stats": window_stats,
    }

    print(f"  Total displacements: {total_disps}")
    print(f"  Current KZ capture: {kz_capture_pct}%")
    print(f"\n  Hourly breakdown (UTC):")
    print(f"  {'Hour':>4} | {'Count':>5} | {'Disps/Day':>9} | {'%Total':>6} | {'Cont3h%':>7} | {'MFE/MAE':>7} | {'OBRetest%':>9} | {'Aligned%':>8}")
    print(f"  {'-'*4}-+-{'-'*5}-+-{'-'*9}-+-{'-'*6}-+-{'-'*7}-+-{'-'*7}-+-{'-'*9}-+-{'-'*8}")
    for h in range(24):
        s = hourly_stats[h]
        cont = f"{s['cont_3h_rate']:5.1f}%" if s['cont_3h_rate'] is not None else "   N/A"
        ratio = f"{s['mfe_mae_ratio']:5.2f}" if s['mfe_mae_ratio'] is not None else "  N/A"
        ob_rt = f"{s['ob_retest_rate']:6.1f}%" if s['ob_retest_rate'] is not None else "    N/A"
        mark = " ◀ KZ" if (7 <= h <= 9 or 13 <= h <= 15) else ""
        print(f"  {h:02d}:00 | {s['disp_count']:5d} | {s['disps_per_day']:9.3f} | {s['pct_of_total']:5.1f}% | {cont} | {ratio} | {ob_rt} | {s['aligned_pct']:6.1f}%{mark}")

    print(f"\n  Extension windows:")
    for name, ws in window_stats.items():
        cont = f"{ws['cont_3h_rate']:.1f}%" if ws['cont_3h_rate'] is not None else "N/A"
        ratio = f"{ws['mfe_mae_ratio']:.2f}" if ws['mfe_mae_ratio'] is not None else "N/A"
        worth = "YES" if ws["worth_testing"] else "NO"
        print(f"    {name:30s} | {ws['disps_per_month']:5.1f}/mo | cont={cont} | MFE/MAE={ratio} | {worth}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    t0 = _time.time()
    all_results = {"lever2": {}, "lever3": {}, "lever4": {}, "synthesis": []}

    for symbol in INSTRUMENTS:
        print(f"\n{'#'*70}")
        print(f"  Loading {symbol}...")
        print(f"{'#'*70}")
        data = load_instrument(symbol)

        if not data["M15"]:
            print(f"  SKIP {symbol}: no M15 data")
            continue

        # Run all three levers
        all_results["lever2"][symbol] = analyze_lever2(symbol, data)
        all_results["lever3"][symbol] = analyze_lever3(symbol, data)
        all_results["lever4"][symbol] = analyze_lever4(symbol, data)

    # ═══════════════════════════════════════════════════════════════════
    # Synthesis
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print(f"  SYNTHESIS")
    print(f"{'='*70}")

    rows = []
    for sym in INSTRUMENTS:
        l2 = all_results["lever2"].get(sym, {})
        l3 = all_results["lever3"].get(sym, {})
        l4 = all_results["lever4"].get(sym, {})

        if l2 and not l2.get("error"):
            rows.append({
                "lever": "H4 OB Retest",
                "instrument": sym,
                "trades_per_month": l2.get("kz_retests_per_month", 0),
                "edge_quality": f"{l2.get('cont_3h_rate', 0)}% cont, MFE/MAE {l2.get('mfe_mae_ratio', 0)}",
                "impl_effort": "Medium (new H4 framework in PA prompt)",
                "overlap_pct": l2.get("overlap_pct", 0),
            })

        if l3 and not l3.get("error"):
            rows.append({
                "lever": "Loose Pre-screen (Cat1)",
                "instrument": sym,
                "trades_per_month": l3.get("cat1_disp_per_month", 0),
                "edge_quality": f"{l3.get('cat1_cont_3h_rate', 0)}% cont, MFE/MAE {l3.get('cat1_mfe_mae_ratio', 0)}",
                "impl_effort": "Low (prescreen gate change)",
            })

        if l4 and not l4.get("error"):
            ws = l4.get("window_stats", {})
            for wname, wdata in ws.items():
                if wdata.get("worth_testing"):
                    rows.append({
                        "lever": f"Extended: {wname.split(' ')[0]}",
                        "instrument": sym,
                        "trades_per_month": round(wdata["disps_per_month"] * 0.15, 1),  # ~15% qualify
                        "edge_quality": f"{wdata.get('cont_3h_rate', 0)}% cont, MFE/MAE {wdata.get('mfe_mae_ratio', 0)}",
                        "impl_effort": "Low (KZ config change)",
                    })

    all_results["synthesis"] = rows

    # Print synthesis table
    print(f"\n  {'Lever':30s} | {'Instrument':10s} | {'Trades/Mo':>9s} | {'Edge Quality':30s} | {'Effort':25s}")
    print(f"  {'-'*30}-+-{'-'*10}-+-{'-'*9}-+-{'-'*30}-+-{'-'*25}")
    for r in rows:
        print(f"  {r['lever']:30s} | {r['instrument']:10s} | {r['trades_per_month']:9.1f} | {r['edge_quality']:30s} | {r['impl_effort']:25s}")

    # Clean up non-serializable data before saving
    def clean_for_json(obj):
        if isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(v) for v in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        return obj

    # Save JSON
    json_path = OUT_DIR / "frequency_multiplier_data_20260403.json"
    with open(json_path, "w") as f:
        json.dump(clean_for_json(all_results), f, indent=2, default=str)
    print(f"\n  Data saved: {json_path}")

    elapsed = _time.time() - t0
    print(f"\n  Total elapsed: {elapsed:.1f}s")

    return all_results


if __name__ == "__main__":
    results = main()
