"""Per-record MFE/MAE/fill replay engine.

Given a T7 CANDIDATE record, simulate fill + outcome against M15 CSV:
  - fill_time = first candle AFTER signal candle where LOW <= entry+eps (for LONG) /
                                                    HIGH >= entry-eps (for SHORT)
  - pre-entry MFE = (max price favorable pre-fill) — (entry)
  - post-entry MAE first-Xmin = max adverse excursion in first X minutes after fill
  - winner MFE = max favorable excursion at any point between fill and exit (OB→TP path)
  - stop_hunt: did SL touch within ±k ticks of OB bound, then price reverse >= 1R within 4h?

All prices are levels; R = abs(entry - stop_loss).
"""
from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from _loader import FILL_EPS, TICK_SIZE, _parse_iso, load_m15


def r_size(entry: float, stop_loss: float) -> float:
    return abs(entry - stop_loss)


def extract_ob_bounds_from_raw(raw_response: str) -> Optional[Tuple[float, float]]:
    """Try to parse OB zone bounds (low, high) from AI raw response.

    AI emits something like:
        "Nearest unmitigated H1 bullish OB at 4613.48-4599.17 (midpoint 4606.33)"
    or:
        "h1_poi_price_level": 4606.33
    or in MSO references.

    Returns (low, high) or None if not recoverable.
    """
    import re
    if not raw_response:
        return None
    # Try explicit ranges: "4599.17-4613.48" or "4613.48-4599.17"
    # XAUUSD / FX both match this pattern.
    for m in re.finditer(r"(\d{1,6}\.\d{1,5})\s*[-\u2013\u2014to]+\s*(\d{1,6}\.\d{1,5})", raw_response):
        a = float(m.group(1))
        b = float(m.group(2))
        if a == b:
            continue
        lo, hi = min(a, b), max(a, b)
        # Only accept plausible OB widths (ratio 1% or less — very loose)
        if hi - lo > 0 and (hi - lo) / max(hi, 1e-9) < 0.05:
            return lo, hi
    # Fall back to null
    return None


def simulate_fill(symbol: str, signal_time: datetime, direction: str, entry: float, stop_loss: float, take_profit: float, max_candles: int = 192) -> Optional[dict]:
    """Simulate a limit fill then forward to SL/TP/timeout.

    Returns dict with:
        fill_time, fill_idx, fill_price,
        pre_entry_mfe_R (favorable excursion signal→fill),
        pre_entry_mae_R (adverse excursion signal→fill),
        exit_time, exit_idx, exit_type ('SL','TP','TIMEOUT','UNFILLED'), exit_r,
        post_entry_mae_15m, _30m, _60m, _240m (in R units),
        post_entry_mfe_240m,
        winner_max_mfe_R (max favorable from fill to exit),
        sl_touch_to_reversal_r (if LOSS and price reverses ≥1R in TP direction within 4h after SL hit),
        any_sl_hit (bool),

    None if signal_time is past dataset.
    """
    candles = load_m15(symbol)
    times = [c["t"] for c in candles]
    sig_idx = bisect_left(times, signal_time)
    if sig_idx >= len(candles):
        return None
    # Fill search starts at candle AFTER signal
    eps = FILL_EPS.get(symbol, 0.05)
    R = r_size(entry, stop_loss)
    if R == 0:
        return None
    is_long = direction.upper() in ("LONG", "BUY")

    fill_idx = None
    fill_price = None
    pre_entry_mfe = 0.0  # favorable excursion signal → fill (R)
    pre_entry_mae = 0.0  # adverse excursion signal → fill (R)

    # Start iterating AFTER signal candle (signal candle is the one that emitted the limit)
    for i in range(sig_idx + 1, min(sig_idx + 1 + max_candles, len(candles))):
        c = candles[i]
        # Track excursions
        if is_long:
            # favorable = price goes UP (toward TP before filling)
            pre_entry_mfe = max(pre_entry_mfe, (c["high"] - entry) / R)
            pre_entry_mae = max(pre_entry_mae, (entry - c["low"]) / R)  # toward SL = adverse pre-fill
            # Fill if LOW <= entry+eps (buy limit): price touched our limit from above
            if c["low"] <= entry + eps:
                fill_idx = i
                # Fill price = conservative: min(open, entry)
                fill_price = min(c["open"], entry + eps)
                if c["open"] > entry + eps:
                    fill_price = entry + eps
                else:
                    fill_price = c["open"]
                break
        else:
            # short: favorable = price DOWN (toward TP before filling)
            pre_entry_mfe = max(pre_entry_mfe, (entry - c["low"]) / R)
            pre_entry_mae = max(pre_entry_mae, (c["high"] - entry) / R)
            # Fill if HIGH >= entry-eps (sell limit)
            if c["high"] >= entry - eps:
                fill_idx = i
                fill_price = max(c["open"], entry - eps)
                if c["open"] < entry - eps:
                    fill_price = entry - eps
                else:
                    fill_price = c["open"]
                break

    if fill_idx is None:
        return {
            "fill_time": None, "fill_idx": None, "fill_price": None,
            "pre_entry_mfe_R": pre_entry_mfe, "pre_entry_mae_R": pre_entry_mae,
            "exit_time": None, "exit_idx": None,
            "exit_type": "UNFILLED", "exit_r": 0.0,
            "post_entry_mae_15m_R": None, "post_entry_mae_30m_R": None,
            "post_entry_mae_60m_R": None, "post_entry_mae_240m_R": None,
            "post_entry_mfe_240m_R": None,
            "winner_max_mfe_R": None,
            "sl_touch_to_reversal_r": None,
            "any_sl_hit": False,
        }

    # Forward simulate from fill_idx
    exit_type = None
    exit_idx = None
    exit_r = None
    max_mfe_R = 0.0  # max favorable excursion in R between fill and exit
    post_entry_mae_vals = {15: 0.0, 30: 0.0, 60: 0.0, 240: 0.0}  # minutes; 1 candle = 15min
    post_entry_mfe_240 = 0.0
    any_sl_hit = False

    fill_time = candles[fill_idx]["t"]
    for j in range(fill_idx, min(fill_idx + max_candles, len(candles))):
        c = candles[j]
        minutes_since_fill = int((c["t"] - fill_time).total_seconds() / 60)
        # Favorable excursion (MFE post-fill)
        if is_long:
            mfe = (c["high"] - entry) / R
            mae = (entry - c["low"]) / R
        else:
            mfe = (entry - c["low"]) / R
            mae = (c["high"] - entry) / R
        max_mfe_R = max(max_mfe_R, mfe)
        if minutes_since_fill <= 240:
            post_entry_mfe_240 = max(post_entry_mfe_240, mfe)
        for window in (15, 30, 60, 240):
            if minutes_since_fill <= window:
                post_entry_mae_vals[window] = max(post_entry_mae_vals[window], mae)

        # Check SL hit
        sl_hit = False
        if is_long and c["low"] <= stop_loss:
            sl_hit = True
        elif (not is_long) and c["high"] >= stop_loss:
            sl_hit = True
        # Check TP hit
        tp_hit = False
        if is_long and c["high"] >= take_profit:
            tp_hit = True
        elif (not is_long) and c["low"] <= take_profit:
            tp_hit = True

        if sl_hit and tp_hit:
            # Ambiguous same candle — pessimistic: SL wins (conservative)
            exit_type = "SL"
            exit_idx = j
            exit_r = -1.0
            any_sl_hit = True
            break
        if sl_hit:
            exit_type = "SL"
            exit_idx = j
            exit_r = -1.0
            any_sl_hit = True
            break
        if tp_hit:
            exit_type = "TP"
            exit_idx = j
            # R = TP distance / R size — always 1.5 if TP set at 1.5R by design, but compute actual
            exit_r = (take_profit - entry) / R if is_long else (entry - take_profit) / R
            break

    if exit_type is None:
        exit_type = "TIMEOUT"
        exit_idx = min(fill_idx + max_candles, len(candles)) - 1
        c = candles[exit_idx]
        if is_long:
            exit_r = (c["close"] - entry) / R
        else:
            exit_r = (entry - c["close"]) / R

    # SL-touch-to-reversal: only for losses
    sl_touch_reversal_r = None
    if exit_type == "SL":
        # After SL (at exit_idx), did price reverse >=1R in TP direction within 16 M15 candles (4h)?
        rev_max_r = 0.0
        for k in range(exit_idx + 1, min(exit_idx + 17, len(candles))):
            c = candles[k]
            if is_long:
                # TP direction = up
                r_back = (c["high"] - stop_loss) / R
            else:
                r_back = (stop_loss - c["low"]) / R
            rev_max_r = max(rev_max_r, r_back)
        sl_touch_reversal_r = rev_max_r

    return {
        "fill_time": fill_time, "fill_idx": fill_idx, "fill_price": fill_price,
        "pre_entry_mfe_R": pre_entry_mfe, "pre_entry_mae_R": pre_entry_mae,
        "exit_time": candles[exit_idx]["t"] if exit_idx else None,
        "exit_idx": exit_idx,
        "exit_type": exit_type, "exit_r": exit_r,
        "post_entry_mae_15m_R": post_entry_mae_vals[15],
        "post_entry_mae_30m_R": post_entry_mae_vals[30],
        "post_entry_mae_60m_R": post_entry_mae_vals[60],
        "post_entry_mae_240m_R": post_entry_mae_vals[240],
        "post_entry_mfe_240m_R": post_entry_mfe_240,
        "winner_max_mfe_R": max_mfe_R,
        "sl_touch_to_reversal_r": sl_touch_reversal_r,
        "any_sl_hit": any_sl_hit,
    }


def check_stop_hunt_signature(symbol: str, sim: dict, entry: float, stop_loss: float, is_long: bool, ob_bound: Optional[float]) -> Optional[dict]:
    """Test bit-exact stop-hunt signature.

    Criteria:
      1. exit_type == 'SL' (or at least SL hit at some point)
      2. SL touch price (candle LOW/HIGH that triggered) within ±2 ticks of `ob_bound`
      3. sl_touch_to_reversal_r >= 1.0

    Returns dict {near_ob, reversed_1r, signature_match} or None if not applicable.
    """
    if sim["exit_type"] != "SL":
        return None
    tick = TICK_SIZE.get(symbol, 0.0001)
    tol = 2 * tick
    near_ob = False
    if ob_bound is not None:
        near_ob = abs(stop_loss - ob_bound) <= tol
    reversed_1r = (sim.get("sl_touch_to_reversal_r") or 0.0) >= 1.0
    return {
        "exit_type": sim["exit_type"],
        "near_ob": near_ob,
        "ob_bound": ob_bound,
        "sl_to_ob_distance_ticks": abs(stop_loss - ob_bound) / tick if ob_bound is not None else None,
        "reversed_1r": reversed_1r,
        "reversal_r": sim.get("sl_touch_to_reversal_r"),
        "signature_match": bool(near_ob and reversed_1r),
    }
