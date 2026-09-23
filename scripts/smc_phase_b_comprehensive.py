#!/usr/bin/env python3
"""Phase B Comprehensive SMC Event Analysis.

Loads raw candles, computes market structure for every trading date, and
analyzes FVG fills (B1), breaker blocks (B2), equal H/L (B3), rejection
blocks (B4), and volume imbalances (B5).

Usage:
    python scripts/smc_phase_b_comprehensive.py
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
import time as _time
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone, time as dtime
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv, LOOKBACK
from src.components.market_state import (
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    identify_fvgs,
    identify_breaker_blocks,
    calculate_atr,
    avg_candle_body,
    calculate_premium_discount,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Discovery / Validation split
DISCOVERY_END = date(2025, 6, 30)
VALIDATION_START = date(2025, 7, 1)

SYMBOLS = ["XAUUSD", "GBPUSD"]

# Kill zone windows (UTC)
LONDON_KZ = (dtime(7, 0), dtime(12, 0))
NY_KZ = (dtime(13, 0), dtime(17, 0))

# Silver bullet hours (UTC)
SILVER_BULLET_HOURS = {15, 19}  # 3pm, 7pm UTC  (10am, 2pm EST)

# Buffers
def _sl_buffer(symbol: str, price: float) -> float:
    if "XAU" in symbol:
        return price * 0.001  # 0.1%
    else:
        return 0.00150  # 15 pips


def _sweep_min(symbol: str) -> float:
    if "XAU" in symbol:
        return 3.0  # $3
    else:
        return 0.00015  # 1.5 pips


def _tolerance_set(symbol: str, price: float) -> list[float]:
    """Return 3 tolerances for equal H/L detection."""
    if "XAU" in symbol:
        return [price * 0.0005, price * 0.001, price * 0.002]
    else:
        return [0.00006, 0.000125, 0.00025]


# ═══════════════════════════════════════════════════════════════════════════
# Data Loading & Indexing
# ═══════════════════════════════════════════════════════════════════════════

def candle_time_to_dt(t: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(t, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse: {t}")


def candle_date(t: str) -> date:
    return candle_time_to_dt(t).date()


def candle_hour(t: str) -> int:
    return candle_time_to_dt(t).hour


def is_in_kz(t: str) -> tuple[bool, Optional[str]]:
    dt = candle_time_to_dt(t)
    tm = dt.time()
    if LONDON_KZ[0] <= tm < LONDON_KZ[1]:
        return True, "london"
    if NY_KZ[0] <= tm < NY_KZ[1]:
        return True, "ny"
    return False, None


def index_candles_by_date(candles: list[dict]) -> dict[date, list[int]]:
    idx_map: dict[date, list[int]] = defaultdict(list)
    for i, c in enumerate(candles):
        d = candle_date(c["time"])
        idx_map[d].append(i)
    return idx_map


def get_candles_up_to(candles: list[dict], date_index: dict[date, list[int]],
                      target_date: date, lookback: int) -> list[dict]:
    if target_date not in date_index:
        return []
    last_idx = date_index[target_date][-1]
    start_idx = max(0, last_idx - lookback + 1)
    return candles[start_idx:last_idx + 1]


def load_all_candles() -> dict[str, dict[str, list[dict]]]:
    data = {}
    for symbol in SYMBOLS:
        data[symbol] = {}
        for tf in ("H1", "M15"):
            fpath = HISTORICAL_DIR / f"{symbol}_{tf}.csv"
            if fpath.exists():
                data[symbol][tf] = parse_tradingview_csv(fpath)
                logger.info(f"Loaded {symbol} {tf}: {len(data[symbol][tf])} candles")
            else:
                logger.warning(f"Missing: {fpath}")
                data[symbol][tf] = []
    return data


def load_day_classifications() -> dict[str, dict[str, dict]]:
    """Return {symbol: {date_str: classification_dict}}."""
    fpath = OUTPUT_DIR / "edge_discovery_d1unclear_20260405.json"
    result: dict[str, dict[str, dict]] = defaultdict(dict)
    if not fpath.exists():
        logger.warning("Day classifications file not found: %s", fpath)
        return result
    with open(fpath) as f:
        data = json.load(f)
    for entry in data.get("day_classifications", []):
        sym = entry.get("symbol", "")
        dt = entry.get("date", "")
        result[sym][dt] = entry
    return result


# ═══════════════════════════════════════════════════════════════════════════
# Outcome Measurement (shared by all B analyses)
# ═══════════════════════════════════════════════════════════════════════════

def walk_forward_outcome(
    m15_candles: list[dict],
    start_idx: int,
    entry_price: float,
    sl_price: float,
    direction: str,
    max_candles: int = 12,
    rr_target: float = 1.5,
) -> dict:
    """Walk forward on M15 candles, returns outcome dict.

    direction: 'long' or 'short'
    Returns: {hit_tp, hit_sl, max_r, candles_held, pnl_r}
    """
    risk = abs(entry_price - sl_price)
    if risk < 1e-10:
        return {"hit_tp": False, "hit_sl": False, "max_r": 0.0, "candles_held": 0, "pnl_r": 0.0}

    tp_price = entry_price + rr_target * risk if direction == "long" else entry_price - rr_target * risk

    max_r = 0.0
    for j in range(start_idx, min(start_idx + max_candles, len(m15_candles))):
        c = m15_candles[j]
        if direction == "long":
            # Check SL first (conservative)
            if c["low"] <= sl_price:
                return {"hit_tp": False, "hit_sl": True, "max_r": max_r,
                        "candles_held": j - start_idx + 1, "pnl_r": -1.0}
            if c["high"] >= tp_price:
                return {"hit_tp": True, "hit_sl": False, "max_r": rr_target,
                        "candles_held": j - start_idx + 1, "pnl_r": rr_target}
            current_r = (c["close"] - entry_price) / risk
            max_r = max(max_r, current_r)
        else:
            if c["high"] >= sl_price:
                return {"hit_tp": False, "hit_sl": True, "max_r": max_r,
                        "candles_held": j - start_idx + 1, "pnl_r": -1.0}
            if c["low"] <= tp_price:
                return {"hit_tp": True, "hit_sl": False, "max_r": rr_target,
                        "candles_held": j - start_idx + 1, "pnl_r": rr_target}
            current_r = (entry_price - c["close"]) / risk
            max_r = max(max_r, current_r)

    # Time expired — close at last candle
    last_idx = min(start_idx + max_candles - 1, len(m15_candles) - 1)
    if last_idx >= start_idx:
        last_close = m15_candles[last_idx]["close"]
        pnl_r = (last_close - entry_price) / risk if direction == "long" else (entry_price - last_close) / risk
    else:
        pnl_r = 0.0
    return {"hit_tp": False, "hit_sl": False, "max_r": max_r,
            "candles_held": max_candles, "pnl_r": round(pnl_r, 4)}


# ═══════════════════════════════════════════════════════════════════════════
# M15 index helper — find first M15 candle at or after a given H1 time
# ═══════════════════════════════════════════════════════════════════════════

def find_m15_idx_at_or_after(m15_candles: list[dict], target_time: str, m15_time_index: dict[str, int]) -> Optional[int]:
    """Binary-search-like lookup for M15 candle at or after target_time."""
    if target_time in m15_time_index:
        return m15_time_index[target_time]
    # Linear scan from approximate position
    target_dt = candle_time_to_dt(target_time)
    # Estimate index
    if not m15_candles:
        return None
    first_dt = candle_time_to_dt(m15_candles[0]["time"])
    approx = int((target_dt - first_dt).total_seconds() / 900)
    approx = max(0, min(approx, len(m15_candles) - 1))
    # Scan forward/backward
    if candle_time_to_dt(m15_candles[approx]["time"]) < target_dt:
        for i in range(approx, len(m15_candles)):
            if candle_time_to_dt(m15_candles[i]["time"]) >= target_dt:
                return i
        return None
    else:
        for i in range(approx, -1, -1):
            if candle_time_to_dt(m15_candles[i]["time"]) < target_dt:
                return i + 1
        return 0


# ═══════════════════════════════════════════════════════════════════════════
# Session levels from H1 (used for B4)
# ═══════════════════════════════════════════════════════════════════════════

def compute_session_levels_h1(h1_candles: list[dict], target_date: date) -> dict:
    """Compute Asian H/L, PDH/PDL from H1 data."""
    prev_date = target_date - timedelta(days=1)
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)

    asian_candles = []
    prev_day_candles = []
    for c in h1_candles:
        d = candle_date(c["time"])
        h = candle_hour(c["time"])
        if d == target_date and 0 <= h < 7:
            asian_candles.append(c)
        if d == prev_date:
            prev_day_candles.append(c)

    return {
        "asian_high": max((c["high"] for c in asian_candles), default=0),
        "asian_low": min((c["low"] for c in asian_candles), default=0),
        "pdh": max((c["high"] for c in prev_day_candles), default=0),
        "pdl": min((c["low"] for c in prev_day_candles), default=0),
    }


# ═══════════════════════════════════════════════════════════════════════════
# B1: FVG Fill Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze_fvg_fills(
    symbol: str,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    m15_candles: list[dict],
    m15_time_idx: dict[str, int],
    day_class: dict[str, dict],
    dates: list[date],
) -> list[dict]:
    """Analyze FVG fills for all dates."""
    results = []
    for di, target_date in enumerate(dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  B1 FVG: processed {di}/{len(dates)} dates, {len(results)} fills so far")

        h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
        if len(h1_slice) < 20:
            continue

        h1_atr = calculate_atr(h1_slice)
        h1_avg_body_val = avg_candle_body(h1_slice)
        if h1_atr < 1e-10:
            continue

        min_gap = h1_atr * 0.1
        fvgs = identify_fvgs(h1_slice, min_gap)

        # Premium/discount
        h1_swings = detect_swings(h1_slice)
        h1_structure = identify_structure(h1_swings)
        h1_pd = calculate_premium_discount(h1_swings, h1_structure)

        # Day classification
        day_str = target_date.isoformat()
        dc = day_class.get(day_str, {})
        d1_dir = dc.get("d1_direction", "unknown")

        # Today's H1 candles for cutoff
        today_h1 = [c for c in h1_slice if candle_date(c["time"]) == target_date]
        if not today_h1:
            continue
        last_h1_time = candle_time_to_dt(today_h1[-1]["time"])
        cutoff_time = last_h1_time - timedelta(hours=3)

        for fvg in fvgs:
            fvg_time_dt = candle_time_to_dt(fvg.formation_time)
            if fvg_time_dt.date() != target_date:
                continue
            if fvg_time_dt > cutoff_time:
                continue

            # FVG features
            fvg_width = fvg.top - fvg.bottom
            width_pct_atr = fvg_width / h1_atr

            # Middle candle displacement (the candle that creates the gap)
            mid_idx = fvg.candle_indices[1]
            if mid_idx < len(h1_slice):
                mid_c = h1_slice[mid_idx]
                mid_body = abs(mid_c["close"] - mid_c["open"])
                creation_disp = mid_body / h1_avg_body_val if h1_avg_body_val > 0 else 0
            else:
                creation_disp = 0

            # Formation session
            _, fvg_kz = is_in_kz(fvg.formation_time)
            in_silver_bullet = fvg_time_dt.hour in SILVER_BULLET_HOURS

            # Premium/discount zone
            fvg_mid = fvg.midpoint
            zone = "neutral"
            if h1_pd:
                if h1_pd.discount_zone.bottom <= fvg_mid <= h1_pd.discount_zone.top:
                    zone = "discount"
                elif h1_pd.premium_zone.bottom <= fvg_mid <= h1_pd.premium_zone.top:
                    zone = "premium"

            # D1 alignment
            d1_aligned = (d1_dir == "bullish" and fvg.type == "bullish") or \
                         (d1_dir == "bearish" and fvg.type == "bearish")

            # Scan M15 forward for fill — up to 48 H1 candles worth (~192 M15)
            m15_start = find_m15_idx_at_or_after(m15_candles, fvg.formation_time, m15_time_idx)
            if m15_start is None:
                continue

            max_m15_scan = 192  # ~48 H1 candles
            fill_found = False
            for mi in range(m15_start + 1, min(m15_start + max_m15_scan, len(m15_candles))):
                mc = m15_candles[mi]

                if fvg.type == "bullish":
                    # Fill = M15 low enters zone
                    if mc["low"] <= fvg.top:
                        fill_pct = (fvg.top - mc["low"]) / fvg_width if fvg_width > 0 else 0
                        freshness = (mi - m15_start) // 4  # approximate H1 candles
                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = fvg.bottom - buf
                        direction = "long"

                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, direction)

                        results.append({
                            "symbol": symbol, "date": day_str, "fvg_type": fvg.type,
                            "fvg_high": fvg.top, "fvg_low": fvg.bottom,
                            "creation_time": fvg.formation_time,
                            "width_pct_atr": round(width_pct_atr, 4),
                            "creation_displacement_ratio": round(creation_disp, 4),
                            "freshness_candles": freshness,
                            "fill_percentage": round(min(fill_pct, 2.0), 4),
                            "d1_aligned": d1_aligned,
                            "pd_zone": zone,
                            "session": fvg_kz or "off_kz",
                            "in_silver_bullet": in_silver_bullet,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        fill_found = True
                        break

                elif fvg.type == "bearish":
                    if mc["high"] >= fvg.bottom:
                        fill_pct = (mc["high"] - fvg.bottom) / fvg_width if fvg_width > 0 else 0
                        freshness = (mi - m15_start) // 4
                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = fvg.top + buf
                        direction = "short"

                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, direction)

                        results.append({
                            "symbol": symbol, "date": day_str, "fvg_type": fvg.type,
                            "fvg_high": fvg.top, "fvg_low": fvg.bottom,
                            "creation_time": fvg.formation_time,
                            "width_pct_atr": round(width_pct_atr, 4),
                            "creation_displacement_ratio": round(creation_disp, 4),
                            "freshness_candles": freshness,
                            "fill_percentage": round(min(fill_pct, 2.0), 4),
                            "d1_aligned": d1_aligned,
                            "pd_zone": zone,
                            "session": fvg_kz or "off_kz",
                            "in_silver_bullet": in_silver_bullet,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        fill_found = True
                        break

    return results


# ═══════════════════════════════════════════════════════════════════════════
# B2: Breaker Block Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze_breaker_blocks(
    symbol: str,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    m15_candles: list[dict],
    m15_time_idx: dict[str, int],
    day_class: dict[str, dict],
    dates: list[date],
) -> list[dict]:
    results = []
    for di, target_date in enumerate(dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  B2 Breaker: processed {di}/{len(dates)} dates, {len(results)} retests so far")

        h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
        if len(h1_slice) < 20:
            continue

        h1_atr = calculate_atr(h1_slice)
        if h1_atr < 1e-10:
            continue

        h1_swings = detect_swings(h1_slice)
        h1_structure = identify_structure(h1_swings)
        h1_events = detect_structure_breaks(h1_slice, h1_swings, h1_structure)
        h1_obs = identify_order_blocks(h1_slice, h1_events)
        breakers = identify_breaker_blocks(h1_slice, h1_obs)

        day_str = target_date.isoformat()
        dc = day_class.get(day_str, {})
        d1_dir = dc.get("d1_direction", "unknown")

        today_h1 = [c for c in h1_slice if candle_date(c["time"]) == target_date]
        if not today_h1:
            continue
        last_h1_time = candle_time_to_dt(today_h1[-1]["time"])
        cutoff_time = last_h1_time - timedelta(hours=3)

        for bb in breakers:
            mit_dt = candle_time_to_dt(bb.mitigation_time)
            if mit_dt.date() != target_date:
                continue
            if mit_dt > cutoff_time:
                continue

            ob_width = bb.zone_high - bb.zone_low
            width_pct_atr = ob_width / h1_atr if h1_atr > 0 else 0

            # Break distance: how far price went past the OB before returning
            # Approximate from H1 candles between mitigation and now
            break_distance = 0.0
            mit_idx_approx = None
            for ci, c in enumerate(h1_slice):
                if c["time"] == bb.mitigation_time:
                    mit_idx_approx = ci
                    break
            if mit_idx_approx is not None:
                for ci in range(mit_idx_approx, len(h1_slice)):
                    c = h1_slice[ci]
                    if bb.direction == "bullish":  # price broke below, now may rally back
                        dist = bb.zone_low - c["low"]
                    else:
                        dist = c["high"] - bb.zone_high
                    break_distance = max(break_distance, dist)

            # D1 aligned with breaker direction (NEW direction)
            d1_aligned = (d1_dir == bb.direction)

            # Scan M15 for retest from the other side
            m15_start = find_m15_idx_at_or_after(m15_candles, bb.mitigation_time, m15_time_idx)
            if m15_start is None:
                continue

            max_m15_scan = 192
            for mi in range(m15_start + 1, min(m15_start + max_m15_scan, len(m15_candles))):
                mc = m15_candles[mi]

                if bb.direction == "bearish":
                    # Was bullish OB that failed -> bearish breaker
                    # Price rallies back up into zone -> short
                    if mc["high"] >= bb.zone_low and mc["close"] <= bb.zone_high:
                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = bb.zone_high + buf
                        freshness = (mi - m15_start) // 4

                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, "short")

                        results.append({
                            "symbol": symbol, "date": day_str,
                            "breaker_direction": bb.direction,
                            "original_ob_direction": bb.original_ob_direction,
                            "zone_high": bb.zone_high, "zone_low": bb.zone_low,
                            "mitigation_time": bb.mitigation_time,
                            "width_pct_atr": round(width_pct_atr, 4),
                            "break_distance": round(break_distance, 4),
                            "freshness_candles": freshness,
                            "d1_aligned": d1_aligned,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        break

                elif bb.direction == "bullish":
                    # Was bearish OB that failed -> bullish breaker
                    # Price drops back into zone -> long
                    if mc["low"] <= bb.zone_high and mc["close"] >= bb.zone_low:
                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = bb.zone_low - buf
                        freshness = (mi - m15_start) // 4

                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, "long")

                        results.append({
                            "symbol": symbol, "date": day_str,
                            "breaker_direction": bb.direction,
                            "original_ob_direction": bb.original_ob_direction,
                            "zone_high": bb.zone_high, "zone_low": bb.zone_low,
                            "mitigation_time": bb.mitigation_time,
                            "width_pct_atr": round(width_pct_atr, 4),
                            "break_distance": round(break_distance, 4),
                            "freshness_candles": freshness,
                            "d1_aligned": d1_aligned,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        break

    return results


# ═══════════════════════════════════════════════════════════════════════════
# B3: Equal Highs / Equal Lows
# ═══════════════════════════════════════════════════════════════════════════

def analyze_equal_hl(
    symbol: str,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    m15_candles: list[dict],
    m15_time_idx: dict[str, int],
    day_class: dict[str, dict],
    dates: list[date],
) -> list[dict]:
    results = []
    ref_price = 2500.0 if "XAU" in symbol else 1.25
    tolerances = _tolerance_set(symbol, ref_price)

    for di, target_date in enumerate(dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  B3 EqualHL: processed {di}/{len(dates)} dates, {len(results)} sweeps so far")

        h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
        if len(h1_slice) < 20:
            continue

        h1_swings = detect_swings(h1_slice)

        day_str = target_date.isoformat()
        dc = day_class.get(day_str, {})
        d1_dir = dc.get("d1_direction", "unknown")

        # Today's candles for timing
        today_h1 = [c for c in h1_slice if candle_date(c["time"]) == target_date]
        if not today_h1:
            continue

        swing_highs = [s for s in h1_swings if s.type == "high"]
        swing_lows = [s for s in h1_swings if s.type == "low"]

        for tol_idx, tol in enumerate(tolerances):
            tol_label = f"tol_{tol_idx}"

            # Find equal highs
            for side_label, swings_list in [("equal_highs", swing_highs), ("equal_lows", swing_lows)]:
                used = set()
                for i, s1 in enumerate(swings_list):
                    if i in used:
                        continue
                    cluster = [s1]
                    cluster_indices = [i]
                    for j in range(i + 1, len(swings_list)):
                        if j in used:
                            continue
                        if abs(swings_list[j].price - s1.price) <= tol:
                            cluster.append(swings_list[j])
                            cluster_indices.append(j)
                    if len(cluster) < 2:
                        continue
                    used.update(cluster_indices)

                    # Cluster extreme
                    if side_label == "equal_highs":
                        cluster_extreme = max(s.price for s in cluster)
                    else:
                        cluster_extreme = min(s.price for s in cluster)

                    # Latest swing in cluster — must be before today's last candle
                    last_swing = max(cluster, key=lambda s: s.index)
                    last_swing_time = candle_time_to_dt(last_swing.time)

                    # Scan M15 for sweep
                    m15_start = find_m15_idx_at_or_after(m15_candles, last_swing.time, m15_time_idx)
                    if m15_start is None:
                        continue

                    sweep_min = _sweep_min(symbol)
                    max_m15_scan = 192
                    for mi in range(m15_start + 1, min(m15_start + max_m15_scan, len(m15_candles))):
                        mc = m15_candles[mi]
                        mc_date = candle_date(mc["time"])
                        # Only scan today and a bit ahead
                        if (mc_date - target_date).days > 2:
                            break

                        if side_label == "equal_highs":
                            if mc["high"] > cluster_extreme + sweep_min:
                                # Sweep detected — is it rejection (body back inside)?
                                body_top = max(mc["open"], mc["close"])
                                is_rejection = body_top < cluster_extreme
                                if is_rejection:
                                    entry = mc["close"]
                                    buf = _sl_buffer(symbol, entry)
                                    sl = mc["high"] + buf
                                    direction = "short"
                                    d1_aligned = (d1_dir == "bearish")

                                    outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, direction)

                                    results.append({
                                        "symbol": symbol, "date": day_str,
                                        "side": side_label, "tolerance_idx": tol_idx,
                                        "tolerance": tol,
                                        "n_touches": len(cluster),
                                        "cluster_extreme": cluster_extreme,
                                        "sweep_type": "rejection",
                                        "time_since_cluster_h1": (mi - m15_start) // 4,
                                        "d1_aligned": d1_aligned,
                                        "entry": entry, "sl": sl,
                                        **outcome,
                                        "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                                    })
                                break  # only take first sweep per cluster per day

                        elif side_label == "equal_lows":
                            if mc["low"] < cluster_extreme - sweep_min:
                                body_bottom = min(mc["open"], mc["close"])
                                is_rejection = body_bottom > cluster_extreme
                                if is_rejection:
                                    entry = mc["close"]
                                    buf = _sl_buffer(symbol, entry)
                                    sl = mc["low"] - buf
                                    direction = "long"
                                    d1_aligned = (d1_dir == "bullish")

                                    outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, direction)

                                    results.append({
                                        "symbol": symbol, "date": day_str,
                                        "side": side_label, "tolerance_idx": tol_idx,
                                        "tolerance": tol,
                                        "n_touches": len(cluster),
                                        "cluster_extreme": cluster_extreme,
                                        "sweep_type": "rejection",
                                        "time_since_cluster_h1": (mi - m15_start) // 4,
                                        "d1_aligned": d1_aligned,
                                        "entry": entry, "sl": sl,
                                        **outcome,
                                        "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                                    })
                                break

    return results


# ═══════════════════════════════════════════════════════════════════════════
# B4: Rejection Block Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze_rejection_blocks(
    symbol: str,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    m15_candles: list[dict],
    m15_time_idx: dict[str, int],
    m15_date_idx: dict[date, list[int]],
    day_class: dict[str, dict],
    dates: list[date],
) -> list[dict]:
    results = []
    for di, target_date in enumerate(dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  B4 Rejection: processed {di}/{len(dates)} dates, {len(results)} rejections so far")

        # Get H1 structure for key levels
        h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
        if len(h1_slice) < 20:
            continue

        h1_atr = calculate_atr(h1_slice)
        if h1_atr < 1e-10:
            continue

        h1_swings = detect_swings(h1_slice)
        h1_structure = identify_structure(h1_swings)
        h1_events = detect_structure_breaks(h1_slice, h1_swings, h1_structure)
        h1_obs = identify_order_blocks(h1_slice, h1_events)
        min_gap = h1_atr * 0.1
        h1_fvgs = identify_fvgs(h1_slice, min_gap)

        # Session levels
        sess_levels = compute_session_levels_h1(h1_candles, target_date)
        ref_price = h1_slice[-1]["close"] if h1_slice else 2500.0
        level_tol = ref_price * 0.002  # 0.2%

        # Collect key levels
        key_levels = []
        for ob in h1_obs:
            if not ob.mitigated:
                key_levels.append(("ob", ob.high))
                key_levels.append(("ob", ob.low))
        for fvg in h1_fvgs:
            key_levels.append(("fvg", fvg.top))
            key_levels.append(("fvg", fvg.bottom))
        for s in h1_swings[-20:]:
            key_levels.append(("swing", s.price))
        if sess_levels["asian_high"] > 0:
            key_levels.append(("asian_hl", sess_levels["asian_high"]))
            key_levels.append(("asian_hl", sess_levels["asian_low"]))
        if sess_levels["pdh"] > 0:
            key_levels.append(("pdhl", sess_levels["pdh"]))
            key_levels.append(("pdhl", sess_levels["pdl"]))

        day_str = target_date.isoformat()
        dc = day_class.get(day_str, {})
        d1_dir = dc.get("d1_direction", "unknown")

        # Get M15 candles for today
        if target_date not in m15_date_idx:
            continue
        today_m15_indices = m15_date_idx[target_date]
        if not today_m15_indices:
            continue

        # Exclude last 12 M15 candles (3 hours) for outcome measurement
        cutoff_idx = today_m15_indices[-1] - 12 if len(today_m15_indices) > 12 else today_m15_indices[0]

        for idx in today_m15_indices:
            if idx > cutoff_idx:
                break
            mc = m15_candles[idx]
            body = abs(mc["close"] - mc["open"])
            upper_wick = mc["high"] - max(mc["open"], mc["close"])
            lower_wick = min(mc["open"], mc["close"]) - mc["low"]

            # Check for rejection candle: wick >= 2x body
            if body < 1e-10:
                continue

            is_bearish_rejection = upper_wick >= 2 * body  # long upper wick -> bearish rejection
            is_bullish_rejection = lower_wick >= 2 * body  # long lower wick -> bullish rejection

            if not is_bearish_rejection and not is_bullish_rejection:
                continue

            # Check if at a key level
            if is_bearish_rejection:
                test_price = mc["high"]
                wick_ratio = upper_wick / body
            else:
                test_price = mc["low"]
                wick_ratio = lower_wick / body

            at_level = None
            for level_type, level_price in key_levels:
                if abs(test_price - level_price) <= level_tol:
                    at_level = level_type
                    break

            if at_level is None:
                continue

            _, kz_name = is_in_kz(mc["time"])

            if is_bearish_rejection:
                entry = mc["close"]
                buf = _sl_buffer(symbol, entry)
                sl = mc["high"] + buf
                direction = "short"
                d1_aligned = (d1_dir == "bearish")
            else:
                entry = mc["close"]
                buf = _sl_buffer(symbol, entry)
                sl = mc["low"] - buf
                direction = "long"
                d1_aligned = (d1_dir == "bullish")

            outcome = walk_forward_outcome(m15_candles, idx + 1, entry, sl, direction)

            wick_cat = "2x" if wick_ratio < 3 else ("3x" if wick_ratio < 5 else "5x+")

            results.append({
                "symbol": symbol, "date": day_str,
                "rejection_type": "bearish" if is_bearish_rejection else "bullish",
                "wick_to_body_ratio": round(wick_ratio, 2),
                "wick_category": wick_cat,
                "level_type": at_level,
                "d1_aligned": d1_aligned,
                "kz": kz_name or "off_kz",
                "entry": entry, "sl": sl,
                **outcome,
                "period": "discovery" if target_date <= DISCOVERY_END else "validation",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
# B5: Volume Imbalance Analysis
# ═══════════════════════════════════════════════════════════════════════════

def analyze_volume_imbalances(
    symbol: str,
    m15_candles: list[dict],
    m15_date_idx: dict[date, list[int]],
    day_class: dict[str, dict],
    dates: list[date],
) -> list[dict]:
    results = []
    ref_price = 2500.0 if "XAU" in symbol else 1.25
    min_gap_pct = 0.0005  # 0.05% of price
    min_gap = ref_price * min_gap_pct

    for di, target_date in enumerate(dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  B5 VolImb: processed {di}/{len(dates)} dates, {len(results)} imbalances so far")

        if target_date not in m15_date_idx:
            continue
        today_indices = m15_date_idx[target_date]
        if len(today_indices) < 15:
            continue

        day_str = target_date.isoformat()
        dc = day_class.get(day_str, {})
        d1_dir = dc.get("d1_direction", "unknown")

        # Exclude last 12 candles for outcome measurement
        cutoff_idx = today_indices[-1] - 12

        for i_pos in range(len(today_indices) - 1):
            idx1 = today_indices[i_pos]
            idx2 = idx1 + 1  # consecutive candle
            if idx2 >= len(m15_candles):
                break
            if idx1 > cutoff_idx:
                break

            c1 = m15_candles[idx1]
            c2 = m15_candles[idx2]

            # Bullish VI: c2 open > c1 close (gap up between bodies)
            bull_gap = c2["open"] - c1["close"]
            bear_gap = c1["open"] - c2["close"]  # c1 open > c2 close (gap down)

            if bull_gap >= min_gap:
                vi_type = "bullish"
                vi_high = c2["open"]
                vi_low = c1["close"]
                vi_width = bull_gap
            elif bear_gap >= min_gap:
                vi_type = "bearish"
                vi_high = c1["open"]
                vi_low = c2["close"]
                vi_width = bear_gap
            else:
                continue

            # Check if VI gets filled (price returns to gap) within 48 M15 candles
            fill_found = False
            continuation = False
            for fi in range(idx2 + 1, min(idx2 + 48, len(m15_candles))):
                fc = m15_candles[fi]
                if vi_type == "bullish":
                    if fc["low"] <= vi_high:  # price returns into gap
                        fill_found = True
                        # Continuation = does price then continue up?
                        entry = fc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = vi_low - buf
                        direction = "long"
                        d1_aligned = (d1_dir == "bullish")

                        outcome = walk_forward_outcome(m15_candles, fi + 1, entry, sl, direction)

                        results.append({
                            "symbol": symbol, "date": day_str,
                            "vi_type": vi_type,
                            "vi_high": vi_high, "vi_low": vi_low,
                            "vi_width": round(vi_width, 5),
                            "vi_width_pct": round(vi_width / ref_price, 6),
                            "filled": True,
                            "d1_aligned": d1_aligned,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        break
                else:
                    if fc["high"] >= vi_low:
                        fill_found = True
                        entry = fc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = vi_high + buf
                        direction = "short"
                        d1_aligned = (d1_dir == "bearish")

                        outcome = walk_forward_outcome(m15_candles, fi + 1, entry, sl, direction)

                        results.append({
                            "symbol": symbol, "date": day_str,
                            "vi_type": vi_type,
                            "vi_high": vi_high, "vi_low": vi_low,
                            "vi_width": round(vi_width, 5),
                            "vi_width_pct": round(vi_width / ref_price, 6),
                            "filled": True,
                            "d1_aligned": d1_aligned,
                            "entry": entry, "sl": sl,
                            **outcome,
                            "period": "discovery" if target_date <= DISCOVERY_END else "validation",
                        })
                        break

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Statistical Analysis Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _bucket(val, edges: list[float], labels: list[str]) -> str:
    for i, edge in enumerate(edges):
        if val < edge:
            return labels[i]
    return labels[-1]


def analyze_feature_groups(records: list[dict], feature: str, group_fn) -> dict:
    """Compute win rate per feature group + chi-squared test."""
    groups: dict[str, dict] = defaultdict(lambda: {"n": 0, "wins": 0})
    for r in records:
        g = group_fn(r)
        if g is None:
            continue
        groups[g]["n"] += 1
        if r.get("hit_tp", False):
            groups[g]["wins"] += 1

    result = {"feature": feature, "groups": {}}
    obs = []
    for g, data in sorted(groups.items()):
        wr = data["wins"] / data["n"] if data["n"] > 0 else 0
        result["groups"][g] = {"n": data["n"], "wins": data["wins"],
                                "win_rate": round(wr, 4),
                                "n_low": data["n"] < 30}
        obs.append([data["wins"], data["n"] - data["wins"]])

    # Chi-squared test
    if len(obs) >= 2 and all(sum(row) > 0 for row in obs):
        try:
            chi2, p, dof, expected = scipy_stats.chi2_contingency(obs)
            result["chi2"] = round(chi2, 4)
            result["p_value"] = round(p, 6)
        except Exception:
            result["chi2"] = None
            result["p_value"] = None
    else:
        result["chi2"] = None
        result["p_value"] = None

    return result


def split_disc_val(records: list[dict]) -> dict:
    """Compute summary stats split by discovery/validation."""
    disc = [r for r in records if r.get("period") == "discovery"]
    val = [r for r in records if r.get("period") == "validation"]

    def _summarize(recs):
        if not recs:
            return {"n": 0, "wins": 0, "win_rate": 0, "avg_pnl_r": 0, "n_low": True}
        wins = sum(1 for r in recs if r.get("hit_tp", False))
        wr = wins / len(recs)
        avg_pnl = np.mean([r.get("pnl_r", 0) for r in recs])
        return {
            "n": len(recs), "wins": wins,
            "win_rate": round(wr, 4),
            "avg_pnl_r": round(float(avg_pnl), 4),
            "n_low": len(recs) < 30,
        }

    return {
        "discovery": _summarize(disc),
        "validation": _summarize(val),
        "total": _summarize(records),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Main Orchestrator
# ═══════════════════════════════════════════════════════════════════════════

def main():
    t0 = _time.time()
    logger.info("=" * 70)
    logger.info("Phase B Comprehensive SMC Event Analysis")
    logger.info("=" * 70)

    # Load data
    all_data = load_all_candles()
    day_classifications = load_day_classifications()

    output = {
        "metadata": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "script": "smc_phase_b_comprehensive.py",
            "symbols": SYMBOLS,
            "discovery_end": str(DISCOVERY_END),
            "validation_start": str(VALIDATION_START),
        },
        "b1_fvg_fill": {},
        "b2_breaker_block": {},
        "b3_equal_hl": {},
        "b4_rejection_block": {},
        "b5_volume_imbalance": {},
    }

    for symbol in SYMBOLS:
        h1_candles = all_data[symbol].get("H1", [])
        m15_candles = all_data[symbol].get("M15", [])

        if not h1_candles or not m15_candles:
            logger.warning(f"Skipping {symbol}: insufficient data")
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {symbol}: {len(h1_candles)} H1, {len(m15_candles)} M15 candles")
        logger.info(f"{'='*60}")

        # Build indices
        h1_date_idx = index_candles_by_date(h1_candles)
        m15_date_idx = index_candles_by_date(m15_candles)
        m15_time_idx = {c["time"]: i for i, c in enumerate(m15_candles)}

        # Get trading dates
        all_dates = sorted(set(candle_date(c["time"]) for c in h1_candles if candle_date(c["time"]).weekday() < 5))
        # Skip first 30 days for lookback
        if len(all_dates) > 30:
            all_dates = all_dates[30:]

        day_class = day_classifications.get(symbol, {})
        logger.info(f"  Trading dates: {len(all_dates)} ({all_dates[0]} to {all_dates[-1]})")

        # ── B1: FVG Fill ──────────────────────────────────────────
        logger.info(f"\n  --- B1: FVG Fill Analysis for {symbol} ---")
        try:
            t1 = _time.time()
            b1_records = analyze_fvg_fills(symbol, h1_candles, h1_date_idx,
                                           m15_candles, m15_time_idx, day_class, all_dates)
            logger.info(f"  B1 complete: {len(b1_records)} FVG fills in {_time.time()-t1:.1f}s")

            # Feature analysis
            b1_features = []
            b1_features.append(analyze_feature_groups(
                b1_records, "width_pct_atr",
                lambda r: _bucket(r["width_pct_atr"], [0.3, 0.6, 1.0], ["narrow<0.3", "medium0.3-0.6", "wide0.6-1.0", "huge>1.0"])))
            b1_features.append(analyze_feature_groups(
                b1_records, "creation_displacement_ratio",
                lambda r: _bucket(r["creation_displacement_ratio"], [1.0, 1.5, 2.5], ["weak<1", "moderate1-1.5", "strong1.5-2.5", "extreme>2.5"])))
            b1_features.append(analyze_feature_groups(
                b1_records, "freshness_candles",
                lambda r: _bucket(r["freshness_candles"], [4, 9, 20], ["1-3", "4-8", "9-20", "20+"])))
            b1_features.append(analyze_feature_groups(
                b1_records, "fill_percentage",
                lambda r: _bucket(r["fill_percentage"], [0.5, 0.8, 1.0], ["<50%", "50-80%", "80-100%", ">100%"])))
            b1_features.append(analyze_feature_groups(
                b1_records, "d1_aligned",
                lambda r: "aligned" if r["d1_aligned"] else "unaligned"))
            b1_features.append(analyze_feature_groups(
                b1_records, "pd_zone",
                lambda r: r["pd_zone"]))
            b1_features.append(analyze_feature_groups(
                b1_records, "session",
                lambda r: r["session"]))
            b1_features.append(analyze_feature_groups(
                b1_records, "in_silver_bullet",
                lambda r: "silver_bullet" if r["in_silver_bullet"] else "non_sb"))

            output["b1_fvg_fill"][symbol] = {
                **split_disc_val(b1_records),
                "feature_analysis": b1_features,
            }
        except Exception as e:
            logger.error(f"  B1 FAILED for {symbol}: {e}")
            traceback.print_exc()
            output["b1_fvg_fill"][symbol] = {"error": str(e)}

        # ── B2: Breaker Block ─────────────────────────────────────
        logger.info(f"\n  --- B2: Breaker Block Analysis for {symbol} ---")
        try:
            t1 = _time.time()
            b2_records = analyze_breaker_blocks(symbol, h1_candles, h1_date_idx,
                                                m15_candles, m15_time_idx, day_class, all_dates)
            logger.info(f"  B2 complete: {len(b2_records)} breaker retests in {_time.time()-t1:.1f}s")

            b2_features = []
            b2_features.append(analyze_feature_groups(
                b2_records, "width_pct_atr",
                lambda r: _bucket(r["width_pct_atr"], [0.3, 0.6, 1.0], ["narrow<0.3", "medium0.3-0.6", "wide0.6-1.0", "huge>1.0"])))
            b2_features.append(analyze_feature_groups(
                b2_records, "d1_aligned",
                lambda r: "aligned" if r["d1_aligned"] else "unaligned"))
            b2_features.append(analyze_feature_groups(
                b2_records, "freshness_candles",
                lambda r: _bucket(r["freshness_candles"], [4, 9, 20], ["1-3", "4-8", "9-20", "20+"])))

            output["b2_breaker_block"][symbol] = {
                **split_disc_val(b2_records),
                "feature_analysis": b2_features,
            }
        except Exception as e:
            logger.error(f"  B2 FAILED for {symbol}: {e}")
            traceback.print_exc()
            output["b2_breaker_block"][symbol] = {"error": str(e)}

        # ── B3: Equal H/L ────────────────────────────────────────
        logger.info(f"\n  --- B3: Equal H/L Analysis for {symbol} ---")
        try:
            t1 = _time.time()
            b3_records = analyze_equal_hl(symbol, h1_candles, h1_date_idx,
                                          m15_candles, m15_time_idx, day_class, all_dates)
            logger.info(f"  B3 complete: {len(b3_records)} sweep rejections in {_time.time()-t1:.1f}s")

            b3_features = []
            b3_features.append(analyze_feature_groups(
                b3_records, "tolerance_idx",
                lambda r: f"tol_{r['tolerance_idx']}"))
            b3_features.append(analyze_feature_groups(
                b3_records, "n_touches",
                lambda r: "2" if r["n_touches"] == 2 else "3+"))
            b3_features.append(analyze_feature_groups(
                b3_records, "d1_aligned",
                lambda r: "aligned" if r["d1_aligned"] else "unaligned"))
            b3_features.append(analyze_feature_groups(
                b3_records, "side",
                lambda r: r["side"]))

            # By tolerance summary
            by_tol = []
            for ti in range(3):
                tol_recs = [r for r in b3_records if r["tolerance_idx"] == ti]
                s = split_disc_val(tol_recs)
                by_tol.append({"tolerance_idx": ti, **s})

            output["b3_equal_hl"][symbol] = {
                **split_disc_val(b3_records),
                "by_tolerance": by_tol,
                "feature_analysis": b3_features,
            }
        except Exception as e:
            logger.error(f"  B3 FAILED for {symbol}: {e}")
            traceback.print_exc()
            output["b3_equal_hl"][symbol] = {"error": str(e)}

        # ── B4: Rejection Block ───────────────────────────────────
        logger.info(f"\n  --- B4: Rejection Block Analysis for {symbol} ---")
        try:
            t1 = _time.time()
            b4_records = analyze_rejection_blocks(symbol, h1_candles, h1_date_idx,
                                                  m15_candles, m15_time_idx, m15_date_idx,
                                                  day_class, all_dates)
            logger.info(f"  B4 complete: {len(b4_records)} rejection blocks in {_time.time()-t1:.1f}s")

            b4_features = []
            b4_features.append(analyze_feature_groups(
                b4_records, "wick_category",
                lambda r: r["wick_category"]))
            b4_features.append(analyze_feature_groups(
                b4_records, "level_type",
                lambda r: r["level_type"]))
            b4_features.append(analyze_feature_groups(
                b4_records, "d1_aligned",
                lambda r: "aligned" if r["d1_aligned"] else "unaligned"))
            b4_features.append(analyze_feature_groups(
                b4_records, "kz",
                lambda r: r["kz"]))

            output["b4_rejection_block"][symbol] = {
                **split_disc_val(b4_records),
                "feature_analysis": b4_features,
            }
        except Exception as e:
            logger.error(f"  B4 FAILED for {symbol}: {e}")
            traceback.print_exc()
            output["b4_rejection_block"][symbol] = {"error": str(e)}

        # ── B5: Volume Imbalance ──────────────────────────────────
        logger.info(f"\n  --- B5: Volume Imbalance Analysis for {symbol} ---")
        try:
            t1 = _time.time()
            b5_records = analyze_volume_imbalances(symbol, m15_candles, m15_date_idx,
                                                   day_class, all_dates)
            logger.info(f"  B5 complete: {len(b5_records)} volume imbalances in {_time.time()-t1:.1f}s")

            b5_features = []
            b5_features.append(analyze_feature_groups(
                b5_records, "d1_aligned",
                lambda r: "aligned" if r["d1_aligned"] else "unaligned"))
            b5_features.append(analyze_feature_groups(
                b5_records, "vi_type",
                lambda r: r["vi_type"]))

            output["b5_volume_imbalance"][symbol] = {
                **split_disc_val(b5_records),
                "feature_analysis": b5_features,
            }
        except Exception as e:
            logger.error(f"  B5 FAILED for {symbol}: {e}")
            traceback.print_exc()
            output["b5_volume_imbalance"][symbol] = {"error": str(e)}

    # Save output
    elapsed = _time.time() - t0
    output["metadata"]["elapsed_seconds"] = round(elapsed, 1)

    out_path = OUTPUT_DIR / "smc_phase_b_comprehensive_20260405.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"\nOutput saved: {out_path}")
    logger.info(f"Total elapsed: {elapsed:.1f}s")

    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    for section in ["b1_fvg_fill", "b2_breaker_block", "b3_equal_hl", "b4_rejection_block", "b5_volume_imbalance"]:
        logger.info(f"\n{section}:")
        for sym, data in output[section].items():
            if "error" in data:
                logger.info(f"  {sym}: ERROR - {data['error']}")
            elif "total" in data:
                t = data["total"]
                logger.info(f"  {sym}: n={t['n']}, win_rate={t['win_rate']:.1%}, avg_pnl_r={t['avg_pnl_r']:.3f}")
                if "discovery" in data:
                    d = data["discovery"]
                    v = data["validation"]
                    logger.info(f"    disc: n={d['n']}, wr={d['win_rate']:.1%} | val: n={v['n']}, wr={v['win_rate']:.1%}")


if __name__ == "__main__":
    main()
