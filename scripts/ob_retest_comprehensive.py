#!/usr/bin/env python3
"""Comprehensive OB Retest Analysis — Every H1 OB Across All Dates.

Computes ALL H1 order blocks across ~580+ trading days for XAUUSD and GBPUSD,
tracks retests on M15 timeframe, measures outcomes, and mines features that
predict retest success.

Usage:
    python scripts/ob_retest_comprehensive.py
"""

from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone, time as dtime
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import stats as scipy_stats

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv, LOOKBACK
from src.components.market_state import (
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    identify_fvgs,
    calculate_atr,
    avg_candle_body,
    calculate_premium_discount,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
OUTPUT_DIR = _PROJECT_ROOT / "knowledge_base_backtest" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Discovery/Validation split
DISCOVERY_START = date(2024, 4, 1)
DISCOVERY_END = date(2025, 6, 30)
VALIDATION_START = date(2025, 7, 1)
VALIDATION_END = date(2026, 3, 30)

# Kill zone windows (UTC)
LONDON_KZ = (dtime(7, 0), dtime(12, 0))
NY_KZ = (dtime(13, 0), dtime(17, 0))

SYMBOLS = ["XAUUSD", "GBPUSD"]


# ═══════════════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════════════

def load_all_candles() -> dict[str, dict[str, list[dict]]]:
    """Load all candles for both symbols, all timeframes."""
    data = {}
    for symbol in SYMBOLS:
        data[symbol] = {}
        for tf in ("D1", "H4", "H1", "M15"):
            fpath = HISTORICAL_DIR / f"{symbol}_{tf}.csv"
            if fpath.exists():
                data[symbol][tf] = parse_tradingview_csv(fpath)
                logger.info(f"Loaded {symbol} {tf}: {len(data[symbol][tf])} candles")
            else:
                logger.warning(f"Missing: {fpath}")
                data[symbol][tf] = []
    return data


def candle_time_to_dt(t: str) -> datetime:
    """Parse candle time string to datetime."""
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


def candle_dow(t: str) -> str:
    return candle_time_to_dt(t).strftime("%A")


def is_in_kz(t: str) -> tuple[bool, Optional[str]]:
    """Check if time is in a kill zone. Returns (is_kz, kz_name)."""
    dt = candle_time_to_dt(t)
    tm = dt.time()
    if LONDON_KZ[0] <= tm < LONDON_KZ[1]:
        return True, "london"
    if NY_KZ[0] <= tm < NY_KZ[1]:
        return True, "ny"
    return False, None


# ═══════════════════════════════════════════════════════════════════════════
# Index candles by date for efficient slicing
# ═══════════════════════════════════════════════════════════════════════════

def index_candles_by_date(candles: list[dict]) -> dict[date, list[int]]:
    """Map each date to indices in the candle list."""
    idx_map: dict[date, list[int]] = defaultdict(list)
    for i, c in enumerate(candles):
        d = candle_date(c["time"])
        idx_map[d].append(i)
    return idx_map


def get_candles_up_to(candles: list[dict], date_index: dict[date, list[int]],
                      target_date: date, lookback: int) -> list[dict]:
    """Get candles ending at end of target_date, with lookback count."""
    # Find last index for target_date
    if target_date not in date_index:
        return []
    last_idx = date_index[target_date][-1]
    start_idx = max(0, last_idx - lookback + 1)
    return candles[start_idx:last_idx + 1]


# ═══════════════════════════════════════════════════════════════════════════
# Phase 1: Compute OBs for a single date
# ═══════════════════════════════════════════════════════════════════════════

def compute_obs_for_date(
    symbol: str,
    target_date: date,
    h1_candles: list[dict],
    h1_date_idx: dict[date, list[int]],
    d1_candles: list[dict],
    d1_date_idx: dict[date, list[int]],
    h4_candles: list[dict],
    h4_date_idx: dict[date, list[int]],
) -> list[dict]:
    """Compute all H1 OBs visible on target_date with full features."""

    # Get H1 candles with lookback
    h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
    if len(h1_slice) < 20:
        return []

    # Compute H1 structure
    h1_swings = detect_swings(h1_slice)
    h1_structure = identify_structure(h1_swings)
    h1_events = detect_structure_breaks(h1_slice, h1_swings, h1_structure)
    h1_obs = identify_order_blocks(h1_slice, h1_events)
    h1_atr = calculate_atr(h1_slice)
    h1_avg_body = avg_candle_body(h1_slice)

    # FVGs for overlap detection
    min_gap = h1_atr * 0.1 if h1_atr > 0 else 0.5
    h1_fvgs = identify_fvgs(h1_slice, min_gap)

    # Premium/discount
    h1_pd = calculate_premium_discount(h1_swings, h1_structure)

    # D1 structure
    d1_slice = get_candles_up_to(d1_candles, d1_date_idx, target_date, LOOKBACK["D1"])
    d1_direction = "insufficient_data"
    if len(d1_slice) >= 10:
        d1_swings = detect_swings(d1_slice)
        d1_struct = identify_structure(d1_swings)
        d1_direction = d1_struct.direction

    # H4 structure
    h4_slice = get_candles_up_to(h4_candles, h4_date_idx, target_date, LOOKBACK["H4"])
    h4_direction = "insufficient_data"
    if len(h4_slice) >= 10:
        h4_swings = detect_swings(h4_slice)
        h4_struct = identify_structure(h4_swings)
        h4_direction = h4_struct.direction

    # Compute Asian range if M15 data is needed (we'll compute from H1 approximation)
    # Asian range from H1 candles: 00:00-07:00 UTC on target_date
    asian_candles = [c for c in h1_slice
                     if candle_date(c["time"]) == target_date
                     and 0 <= candle_hour(c["time"]) < 7]
    asian_high = max((c["high"] for c in asian_candles), default=0)
    asian_low = min((c["low"] for c in asian_candles), default=0)
    asian_range = asian_high - asian_low if asian_candles else 0

    # Average daily range from D1
    if len(d1_slice) >= 14:
        adr = sum(c["high"] - c["low"] for c in d1_slice[-14:]) / 14
    else:
        adr = h1_atr * 24 if h1_atr > 0 else 1  # rough approximation

    asian_pct_adr = asian_range / adr if adr > 0 else 0

    results = []

    # Find today's H1 candles in the slice
    today_start_idx = None
    for i, c in enumerate(h1_slice):
        if candle_date(c["time"]) == target_date:
            today_start_idx = i
            break

    if today_start_idx is None:
        return []

    # 3 hours = 3 H1 candles from end of day — exclude OBs formed too late
    # Actually we measure on M15 (12 candles = 3h), but OBs form on H1
    # Exclude OBs whose formation is in the last 3 hours of the day's H1 data
    today_candles = [c for c in h1_slice if candle_date(c["time"]) == target_date]
    if not today_candles:
        return []

    last_time = candle_time_to_dt(today_candles[-1]["time"])
    cutoff_time = last_time - timedelta(hours=3)

    for ob in h1_obs:
        # Only include OBs that are NOT already mitigated (fresh)
        if ob.mitigated:
            continue

        ob_time = candle_time_to_dt(ob.formation_time)

        # Skip OBs formed before the data range we care about
        if ob_time.date() < target_date - timedelta(days=7):
            continue

        # Skip OBs formed too late to measure outcome
        if ob_time > cutoff_time:
            continue

        # OB width features
        ob_width = ob.high - ob.low
        width_pct_atr = ob_width / h1_atr if h1_atr > 0 else 0
        body = abs(ob.close - ob.open)
        body_range_ratio = body / ob_width if ob_width > 0 else 0

        # Causing event details
        causing_event = None
        for ev in h1_events:
            if ev.candle_index == ob.causing_bos_index:
                causing_event = ev
                break
        displacement_ratio = causing_event.displacement_ratio if causing_event else 0.0
        causing_type = ob.causing_event_type

        # Premium/discount zone
        zone = "neutral"
        in_ote = False
        ob_mid = (ob.high + ob.low) / 2
        if h1_pd:
            if ob.type == "bullish":
                if h1_pd.discount_zone.bottom <= ob_mid <= h1_pd.discount_zone.top:
                    zone = "discount"
                elif h1_pd.premium_zone.bottom <= ob_mid <= h1_pd.premium_zone.top:
                    zone = "premium"
                if h1_pd.ote_zone.bottom <= ob_mid <= h1_pd.ote_zone.top:
                    in_ote = True
            elif ob.type == "bearish":
                if h1_pd.premium_zone.bottom <= ob_mid <= h1_pd.premium_zone.top:
                    zone = "premium"
                elif h1_pd.discount_zone.bottom <= ob_mid <= h1_pd.discount_zone.top:
                    zone = "discount"
                if h1_pd.ote_zone.bottom <= ob_mid <= h1_pd.ote_zone.top:
                    in_ote = True

        # D1/H4 alignment
        d1_aligned = (d1_direction == ob.type)
        h4_aligned = (h4_direction == ob.type)

        # FVG overlap
        fvg_overlap = False
        for fvg in h1_fvgs:
            if fvg.type == ob.type:
                # Check overlap
                if ob.low <= fvg.top and ob.high >= fvg.bottom:
                    fvg_overlap = True
                    break

        # Nearby OB count (within 1 ATR)
        nearby_count = 0
        for other_ob in h1_obs:
            if other_ob is not ob and other_ob.type == ob.type and not other_ob.mitigated:
                dist = abs((other_ob.high + other_ob.low) / 2 - ob_mid)
                if dist < h1_atr:
                    nearby_count += 1

        # OB sequence number (nth OB of this type in recent events)
        same_type_obs = [o for o in h1_obs if o.type == ob.type
                         and o.formation_index <= ob.formation_index]
        ob_seq = len(same_type_obs)

        # Session of formation
        form_hour = candle_hour(ob.formation_time)
        if 0 <= form_hour < 7:
            session = "asian"
        elif 7 <= form_hour < 13:
            session = "london"
        elif 13 <= form_hour < 18:
            session = "ny"
        else:
            session = "late"

        ob_record = {
            "ob_id": f"{symbol.lower()}_{target_date}_{ob.formation_index}",
            "date": str(target_date),
            "symbol": symbol,
            "formation_time": ob.formation_time,
            "ob_type": ob.type,
            "ob_high": ob.high,
            "ob_low": ob.low,
            "ob_open": ob.open,
            "ob_close": ob.close,
            "formation_index_in_slice": ob.formation_index,
            "causing_bos_index_in_slice": ob.causing_bos_index,
            "features": {
                "width_absolute": round(ob_width, 4),
                "width_pct_atr": round(width_pct_atr, 4),
                "body_range_ratio": round(body_range_ratio, 4),
                "causing_event_type": causing_type,
                "causing_displacement_ratio": round(displacement_ratio, 2),
                "premium_discount_zone": zone,
                "in_ote_zone": in_ote,
                "d1_direction": d1_direction,
                "d1_aligned": d1_aligned,
                "h4_direction": h4_direction,
                "h4_aligned": h4_aligned,
                "fvg_overlap": fvg_overlap,
                "nearby_ob_count": nearby_count,
                "ob_sequence_number": ob_seq,
                "hour_of_formation": form_hour,
                "day_of_week": candle_dow(ob.formation_time),
                "asian_range_pct_adr": round(asian_pct_adr, 4),
                "session": session,
                "h1_atr": round(h1_atr, 4),
            },
            "retest": None,
            "outcome": None,
        }
        results.append(ob_record)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Phase 2: Retest Detection on M15
# ═══════════════════════════════════════════════════════════════════════════

def detect_retests(
    ob_records: list[dict],
    m15_candles: list[dict],
    m15_date_idx: dict[date, list[int]],
    symbol: str,
) -> list[dict]:
    """For each OB, scan M15 candles forward to detect retests."""
    if not ob_records or not m15_candles:
        return ob_records

    # Build a time-to-index map for M15
    m15_time_map: dict[str, int] = {}
    for i, c in enumerate(m15_candles):
        m15_time_map[c["time"]] = i

    # For efficient lookup, sort OBs by formation time
    m15_avg_body = avg_candle_body(m15_candles[-200:] if len(m15_candles) > 200 else m15_candles, 20)

    for ob_rec in ob_records:
        ob_time = candle_time_to_dt(ob_rec["formation_time"])
        ob_high = ob_rec["ob_high"]
        ob_low = ob_rec["ob_low"]
        ob_type = ob_rec["ob_type"]

        # Find M15 candles starting after OB formation
        # Find the first M15 candle after the OB formation (H1 candle close)
        # H1 candle at 09:00 means the period 09:00-10:00, so M15 candles start at 09:15, 09:30, etc.
        start_m15_idx = None
        for i, c in enumerate(m15_candles):
            if candle_time_to_dt(c["time"]) > ob_time:
                start_m15_idx = i
                break

        if start_m15_idx is None:
            continue

        # Scan forward for retests — track all retests (multi-retest)
        retest_num = 0
        in_zone = False
        retests_for_ob = []

        # Limit scan to ~48 hours of M15 candles (192 candles) to avoid stale OBs
        end_m15_idx = min(start_m15_idx + 192, len(m15_candles))

        for i in range(start_m15_idx, end_m15_idx):
            c = m15_candles[i]

            if ob_type == "bullish":
                # Bullish OB retest: candle low enters zone
                enters_zone = c["low"] <= ob_high
                # But candle must come FROM above (price retraces down to OB)
                # Actually per spec: just check if low enters zone
                if enters_zone and not in_zone:
                    in_zone = True
                    retest_num += 1

                    # Entry = candle close if inside/above zone, else next candle open
                    if c["close"] >= ob_low:
                        entry_price = c["close"]
                        entry_idx = i
                    elif i + 1 < len(m15_candles):
                        entry_price = m15_candles[i + 1]["open"]
                        entry_idx = i + 1
                    else:
                        continue

                    # SL = ob_low - buffer
                    if symbol == "XAUUSD":
                        sl_price = ob_low - 0.001 * ob_low
                    else:
                        sl_price = ob_low - 0.00015
                    sl_distance = abs(entry_price - sl_price)

                    retest_info = _build_retest(
                        ob_rec, c, entry_price, entry_idx, sl_price, sl_distance,
                        m15_candles, m15_avg_body, retest_num, ob_type
                    )
                    retests_for_ob.append(retest_info)

                elif not enters_zone:
                    in_zone = False

            elif ob_type == "bearish":
                enters_zone = c["high"] >= ob_low
                if enters_zone and not in_zone:
                    in_zone = True
                    retest_num += 1

                    if c["close"] <= ob_high:
                        entry_price = c["close"]
                        entry_idx = i
                    elif i + 1 < len(m15_candles):
                        entry_price = m15_candles[i + 1]["open"]
                        entry_idx = i + 1
                    else:
                        continue

                    if symbol == "XAUUSD":
                        sl_price = ob_high + 0.001 * ob_high
                    else:
                        sl_price = ob_high + 0.00015
                    sl_distance = abs(sl_price - entry_price)

                    retest_info = _build_retest(
                        ob_rec, c, entry_price, entry_idx, sl_price, sl_distance,
                        m15_candles, m15_avg_body, retest_num, ob_type
                    )
                    retests_for_ob.append(retest_info)

                elif not enters_zone:
                    in_zone = False

        # Store first retest on the OB record itself
        if retests_for_ob:
            ob_rec["retest"] = retests_for_ob[0]
            ob_rec["outcome"] = retests_for_ob[0].get("outcome")
            # Store additional retests
            if len(retests_for_ob) > 1:
                ob_rec["additional_retests"] = retests_for_ob[1:]

    return ob_records


def _build_retest(
    ob_rec: dict, retest_candle: dict,
    entry_price: float, entry_idx: int,
    sl_price: float, sl_distance: float,
    m15_candles: list[dict], m15_avg_body: float,
    retest_num: int, ob_type: str,
) -> dict:
    """Build retest + outcome record."""
    retest_time = retest_candle["time"]
    ob_formation_time = ob_rec["formation_time"]

    # Freshness: approximate H1 candle count from formation to retest
    form_dt = candle_time_to_dt(ob_formation_time)
    retest_dt = candle_time_to_dt(retest_time)
    hours_diff = (retest_dt - form_dt).total_seconds() / 3600
    freshness_h1 = max(1, int(hours_diff))

    # KZ check
    in_kz, kz_name = is_in_kz(retest_time)

    # M15 displacement at retest (check retest candle + next 2)
    m15_disp = False
    m15_disp_ratio = 0.0
    for offset in range(3):
        idx = entry_idx + offset
        if idx >= len(m15_candles):
            break
        c = m15_candles[idx]
        body = abs(c["close"] - c["open"])
        ratio = body / m15_avg_body if m15_avg_body > 0 else 0

        if ratio >= 1.5:
            # Check direction matches expected
            if ob_type == "bullish" and c["close"] > c["open"]:
                m15_disp = True
                m15_disp_ratio = ratio
                break
            elif ob_type == "bearish" and c["close"] < c["open"]:
                m15_disp = True
                m15_disp_ratio = ratio
                break

    # Outcome: walk forward 12 M15 candles (3 hours)
    target_distance = 1.5 * sl_distance
    hit_target = False
    mfe = 0.0
    mae = 0.0
    time_to_target = None

    for j in range(1, 13):
        idx = entry_idx + j
        if idx >= len(m15_candles):
            break
        c = m15_candles[idx]

        if ob_type == "bullish":
            favorable = c["high"] - entry_price
            adverse = entry_price - c["low"]
            mfe = max(mfe, favorable)
            mae = max(mae, adverse)

            # Check SL hit
            if c["low"] <= sl_price:
                # SL hit — check same candle TP
                if c["high"] >= entry_price + target_distance:
                    # Both hit — conservative: check open
                    if c["open"] <= sl_price:
                        break  # SL hit first
                    elif c["open"] >= entry_price + target_distance:
                        hit_target = True
                        time_to_target = j
                        break
                    else:
                        # Ambiguous — conservative = SL
                        break
                else:
                    break  # SL hit

            if c["high"] >= entry_price + target_distance:
                hit_target = True
                time_to_target = j
                break

        elif ob_type == "bearish":
            favorable = entry_price - c["low"]
            adverse = c["high"] - entry_price
            mfe = max(mfe, favorable)
            mae = max(mae, adverse)

            if c["high"] >= sl_price:
                if c["low"] <= entry_price - target_distance:
                    if c["open"] >= sl_price:
                        break
                    elif c["open"] <= entry_price - target_distance:
                        hit_target = True
                        time_to_target = j
                        break
                    else:
                        break
                else:
                    break

            if c["low"] <= entry_price - target_distance:
                hit_target = True
                time_to_target = j
                break

    mfe_r = mfe / sl_distance if sl_distance > 0 else 0
    mae_r = mae / sl_distance if sl_distance > 0 else 0
    r_multiple = (mfe if hit_target else -mae) / sl_distance if sl_distance > 0 else 0

    retest_info = {
        "retested": True,
        "retest_time": retest_time,
        "retest_freshness_candles": freshness_h1,
        "retest_in_kz": in_kz,
        "retest_kz": kz_name,
        "retest_number": retest_num,
        "m15_displacement_at_retest": m15_disp,
        "m15_displacement_ratio": round(m15_disp_ratio, 2),
        "entry_price": round(entry_price, 5),
        "sl_price": round(sl_price, 5),
        "sl_distance": round(sl_distance, 5),
        "rr_to_target": 1.5,
        "outcome": {
            "hit_target_3h": hit_target,
            "r_multiple_3h": round(r_multiple, 3),
            "mfe_r": round(mfe_r, 3),
            "mae_r": round(mae_r, 3),
            "time_to_target_candles": time_to_target,
        },
    }
    return retest_info


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Feature Analysis
# ═══════════════════════════════════════════════════════════════════════════

def compute_feature_analysis(retested_obs: list[dict], period: str) -> list[dict]:
    """Compute univariate feature analysis on retested OBs."""
    features_config = [
        ("width_pct_atr", "quartile", None),
        ("body_range_ratio", "bins", [0.0, 0.3, 0.6, 1.01]),
        ("causing_event_type", "categorical", None),
        ("causing_displacement_ratio", "quartile", None),
        ("freshness", "bins", [0, 3, 8, 20, 999]),
        ("premium_discount_zone", "categorical", None),
        ("in_ote_zone", "boolean", None),
        ("d1_aligned", "boolean", None),
        ("h4_aligned", "boolean", None),
        ("fvg_overlap", "boolean", None),
        ("nearby_ob_count", "bins", [-0.5, 0.5, 1.5, 2.5, 99]),
        ("ob_sequence_number", "bins", [0, 1.5, 2.5, 99]),
        ("retest_number", "bins", [0, 1.5, 2.5, 99]),
        ("m15_displacement_at_retest", "boolean", None),
        ("retest_in_kz", "boolean", None),
        ("hour_of_retest", "by_hour", None),
        ("day_of_week", "categorical", None),
        ("asian_range_pct_adr", "quartile", None),
    ]

    results = []

    for feat_name, feat_type, bins in features_config:
        groups = _split_by_feature(retested_obs, feat_name, feat_type, bins)
        if not groups:
            continue

        group_stats = []
        all_rates = []
        for gname, obs_in_group in groups.items():
            n = len(obs_in_group)
            if n == 0:
                continue
            wins = sum(1 for o in obs_in_group if o.get("outcome", {}).get("hit_target_3h", False))
            rate = wins / n
            avg_mfe = np.mean([o.get("outcome", {}).get("mfe_r", 0) for o in obs_in_group])
            avg_mae = np.mean([o.get("outcome", {}).get("mae_r", 0) for o in obs_in_group])
            group_stats.append({
                "group": str(gname),
                "n": n,
                "continuation_rate": round(rate, 4),
                "avg_mfe_r": round(float(avg_mfe), 3),
                "avg_mae_r": round(float(avg_mae), 3),
            })
            all_rates.append(rate)

        if len(group_stats) < 2:
            continue

        spread = max(all_rates) - min(all_rates)

        # Chi-squared test
        contingency = []
        for gs in group_stats:
            wins = int(gs["n"] * gs["continuation_rate"])
            losses = gs["n"] - wins
            contingency.append([wins, losses])

        try:
            chi2, p_value, _, _ = scipy_stats.chi2_contingency(contingency)
        except Exception:
            chi2, p_value = 0.0, 1.0

        results.append({
            "feature": feat_name,
            "period": period,
            "groups": group_stats,
            "spread": round(spread, 4),
            "chi2": round(chi2, 3),
            "p_value": round(p_value, 6),
        })

    return results


def _split_by_feature(obs: list[dict], feat_name: str, feat_type: str,
                       bins: Optional[list]) -> dict[str, list[dict]]:
    """Split observations by feature value."""
    groups: dict[str, list[dict]] = defaultdict(list)

    for o in obs:
        # Get feature value
        val = _get_feature_value(o, feat_name)
        if val is None:
            continue

        if feat_type == "quartile":
            # We'll assign quartile labels later
            groups["_raw_"].append((val, o))
        elif feat_type == "bins":
            for i in range(len(bins) - 1):
                if bins[i] <= val < bins[i + 1]:
                    label = f"{bins[i]}-{bins[i+1]}"
                    groups[label].append(o)
                    break
        elif feat_type == "categorical":
            groups[str(val)].append(o)
        elif feat_type == "boolean":
            groups[str(bool(val))].append(o)
        elif feat_type == "by_hour":
            groups[str(int(val))].append(o)

    # Handle quartile grouping
    if "_raw_" in groups:
        raw_pairs = groups.pop("_raw_")
        values = [v for v, _ in raw_pairs]
        if len(values) >= 4:
            q25, q50, q75 = np.percentile(values, [25, 50, 75])
            for val, o in raw_pairs:
                if val <= q25:
                    groups["Q1"].append(o)
                elif val <= q50:
                    groups["Q2"].append(o)
                elif val <= q75:
                    groups["Q3"].append(o)
                else:
                    groups["Q4"].append(o)

    return dict(groups)


def _get_feature_value(o: dict, feat_name: str):
    """Extract feature value from an OB record."""
    features = o.get("features", {})
    retest = o.get("retest", {}) or {}

    if feat_name == "freshness":
        return retest.get("retest_freshness_candles")
    elif feat_name == "retest_number":
        return retest.get("retest_number")
    elif feat_name == "m15_displacement_at_retest":
        return retest.get("m15_displacement_at_retest")
    elif feat_name == "retest_in_kz":
        return retest.get("retest_in_kz")
    elif feat_name == "hour_of_retest":
        rt = retest.get("retest_time")
        if rt:
            return candle_hour(rt)
        return None
    elif feat_name == "day_of_week":
        rt = retest.get("retest_time")
        if rt:
            return candle_dow(rt)
        return None
    elif feat_name in features:
        return features[feat_name]
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4B: Feature Combinations
# ═══════════════════════════════════════════════════════════════════════════

def compute_feature_combinations(retested_obs: list[dict], top_features: list[dict],
                                  period: str) -> list[dict]:
    """Test 2-feature combinations of top features."""
    if len(top_features) < 2:
        return []

    # Determine "favorable" state for each feature
    favorable = {}
    for feat in top_features:
        groups = feat["groups"]
        best_group = max(groups, key=lambda g: g["continuation_rate"])
        favorable[feat["feature"]] = best_group["group"]

    combos = []
    feat_names = [f["feature"] for f in top_features]

    for i in range(len(feat_names)):
        for j in range(i + 1, len(feat_names)):
            f1, f2 = feat_names[i], feat_names[j]
            fav1, fav2 = favorable[f1], favorable[f2]

            # Filter obs where both features are in favorable state
            both_favorable = []
            neither = []
            for o in retested_obs:
                v1 = str(_get_feature_value(o, f1))
                v2 = str(_get_feature_value(o, f2))

                # Handle boolean/quartile matching
                if v1 == fav1 and v2 == fav2:
                    both_favorable.append(o)
                elif v1 != fav1 and v2 != fav2:
                    neither.append(o)

            if len(both_favorable) < 10:
                continue

            both_wins = sum(1 for o in both_favorable
                          if o.get("outcome", {}).get("hit_target_3h", False))
            both_rate = both_wins / len(both_favorable)

            baseline_wins = sum(1 for o in retested_obs
                              if o.get("outcome", {}).get("hit_target_3h", False))
            baseline_rate = baseline_wins / len(retested_obs)

            # Fisher's exact or chi2
            try:
                neither_wins = sum(1 for o in neither
                                  if o.get("outcome", {}).get("hit_target_3h", False))
                neither_rate = neither_wins / len(neither) if neither else 0
                contingency = [
                    [both_wins, len(both_favorable) - both_wins],
                    [neither_wins, len(neither) - neither_wins] if neither else [0, 1],
                ]
                _, p_val = scipy_stats.fisher_exact(contingency) if min(len(both_favorable), len(neither)) < 100 else (0, scipy_stats.chi2_contingency([contingency])[1] if len(neither) > 0 else 1.0)
            except Exception:
                p_val = 1.0

            combos.append({
                "features": [f1, f2],
                "favorable_states": [fav1, fav2],
                "n_both": len(both_favorable),
                "rate_both": round(both_rate, 4),
                "n_neither": len(neither),
                "baseline_rate": round(baseline_rate, 4),
                "lift": round(both_rate - baseline_rate, 4),
                "p_value": round(p_val, 6),
                "period": period,
            })

    # Bonferroni correction
    n_tests = len(combos)
    for c in combos:
        c["bonferroni_alpha"] = round(0.05 / n_tests, 6) if n_tests > 0 else 0.05
        c["significant_after_bonferroni"] = c["p_value"] < c["bonferroni_alpha"]

    return sorted(combos, key=lambda x: -x["lift"])


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4C: OB Quality Score
# ═══════════════════════════════════════════════════════════════════════════

def compute_quality_score(retested_obs: list[dict], top_features: list[dict]) -> dict:
    """Build additive quality score from top features."""
    favorable = {}
    for feat in top_features:
        groups = feat["groups"]
        best_group = max(groups, key=lambda g: g["continuation_rate"])
        favorable[feat["feature"]] = best_group["group"]

    # Score each OB
    scored = []
    for o in retested_obs:
        score = 0
        for feat_name, fav_val in favorable.items():
            val = str(_get_feature_value(o, feat_name))
            if val == fav_val:
                score += 1
        hit = o.get("outcome", {}).get("hit_target_3h", False)
        scored.append({"score": score, "hit": hit, "ob": o})

    # Compute rate by score level
    levels = defaultdict(lambda: {"n": 0, "wins": 0})
    for s in scored:
        levels[s["score"]]["n"] += 1
        if s["hit"]:
            levels[s["score"]]["wins"] += 1

    level_stats = []
    for score in sorted(levels.keys()):
        n = levels[score]["n"]
        w = levels[score]["wins"]
        rate = w / n if n > 0 else 0
        level_stats.append({
            "score": score,
            "n": n,
            "continuation_rate": round(rate, 4),
        })

    # Find threshold
    threshold = None
    for ls in level_stats:
        if ls["continuation_rate"] >= 0.55 and ls["n"] >= 20:
            threshold = ls["score"]
            break

    return {
        "definition": f"Additive score: +1 for each favorable feature from top {len(favorable)}",
        "favorable_features": favorable,
        "levels": level_stats,
        "threshold": threshold,
        "scored_obs": scored,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 5: Cross-reference with traded OBs
# ═══════════════════════════════════════════════════════════════════════════

def cross_reference_trades(
    retested_obs: list[dict],
    quality_scores: dict,
    trade_index_path: Path,
) -> dict:
    """Compare AI-selected OBs vs full population."""
    if not trade_index_path.exists():
        return {"error": "trade index not found"}

    with open(trade_index_path) as f:
        trade_index = json.load(f)

    trades = trade_index.get("trades", [])
    trade_dates = {(t["date"], t["symbol"]) for t in trades}

    # KZ retested OBs
    kz_retested = [o for o in retested_obs
                   if o.get("retest", {}) and o["retest"].get("retest_in_kz")]

    # Matched: traded OBs that we can find in our computed OBs
    matched = 0
    for o in kz_retested:
        key = (o["date"], o["symbol"])
        if key in trade_dates:
            matched += 1

    # Quality score distribution for traded vs non-traded
    scored = quality_scores.get("scored_obs", [])
    traded_scores = []
    non_traded_scores = []
    for s in scored:
        o = s["ob"]
        if not o.get("retest", {}) or not o["retest"].get("retest_in_kz"):
            continue
        key = (o["date"], o["symbol"])
        if key in trade_dates:
            traded_scores.append(s["score"])
        else:
            non_traded_scores.append(s["score"])

    return {
        "total_kz_retested": len(kz_retested),
        "matched_to_trades": matched,
        "trade_count": len(trades),
        "ai_selection_pct": round(matched / len(kz_retested) * 100, 2) if kz_retested else 0,
        "traded_avg_score": round(float(np.mean(traded_scores)), 2) if traded_scores else None,
        "non_traded_avg_score": round(float(np.mean(non_traded_scores)), 2) if non_traded_scores else None,
        "traded_score_dist": {str(k): int(v) for k, v in zip(*np.unique(traded_scores, return_counts=True))} if traded_scores else {},
        "non_traded_score_dist": {str(k): int(v) for k, v in zip(*np.unique(non_traded_scores, return_counts=True))} if non_traded_scores else {},
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 6: M15 Displacement Confirmation Deep Dive
# ═══════════════════════════════════════════════════════════════════════════

def analyze_m15_confirmation(retested_obs: list[dict]) -> dict:
    """Analyze the value of M15 displacement confirmation."""
    with_disp = [o for o in retested_obs
                 if o.get("retest", {}).get("m15_displacement_at_retest")]
    without_disp = [o for o in retested_obs
                    if o.get("retest") and not o["retest"].get("m15_displacement_at_retest")]

    def _rate(obs):
        if not obs:
            return 0.0
        wins = sum(1 for o in obs if o.get("outcome", {}).get("hit_target_3h", False))
        return wins / len(obs)

    with_rate = _rate(with_disp)
    without_rate = _rate(without_disp)
    all_rate = _rate(retested_obs)

    # Displacement ratio quartiles
    disp_ratios = [o["retest"]["m15_displacement_ratio"] for o in with_disp
                   if o["retest"]["m15_displacement_ratio"] > 0]
    ratio_analysis = []
    if len(disp_ratios) >= 20:
        bins = [1.5, 2.0, 2.5, 3.0, 99]
        for i in range(len(bins) - 1):
            in_bin = [o for o in with_disp
                      if bins[i] <= o["retest"]["m15_displacement_ratio"] < bins[i + 1]]
            r = _rate(in_bin)
            ratio_analysis.append({
                "range": f"{bins[i]}-{bins[i+1]}",
                "n": len(in_bin),
                "rate": round(r, 4),
            })

    return {
        "all_retests": {"n": len(retested_obs), "rate": round(all_rate, 4)},
        "with_confirmation": {"n": len(with_disp), "rate": round(with_rate, 4)},
        "without_confirmation": {"n": len(without_disp), "rate": round(without_rate, 4)},
        "spread": round(with_rate - without_rate, 4),
        "displacement_ratio_analysis": ratio_analysis,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Phase 7: H4 OB Analysis
# ═══════════════════════════════════════════════════════════════════════════

def compute_h4_obs(
    symbol: str,
    all_dates: list[date],
    h4_candles: list[dict],
    h4_date_idx: dict[date, list[int]],
    d1_candles: list[dict],
    d1_date_idx: dict[date, list[int]],
    m15_candles: list[dict],
    m15_date_idx: dict[date, list[int]],
) -> dict:
    """Compute H4 OBs and their retests."""
    all_h4_obs = []

    # Process in weekly batches to avoid redundant computation
    processed_weeks = set()

    for target_date in all_dates:
        week_key = target_date.isocalendar()[:2]
        if week_key in processed_weeks:
            continue
        processed_weeks.add(week_key)

        h4_slice = get_candles_up_to(h4_candles, h4_date_idx, target_date, LOOKBACK["H4"])
        if len(h4_slice) < 20:
            continue

        h4_swings = detect_swings(h4_slice)
        h4_structure = identify_structure(h4_swings)
        h4_events = detect_structure_breaks(h4_slice, h4_swings, h4_structure)
        h4_obs = identify_order_blocks(h4_slice, h4_events)
        h4_atr = calculate_atr(h4_slice)

        # D1 direction
        d1_slice = get_candles_up_to(d1_candles, d1_date_idx, target_date, LOOKBACK["D1"])
        d1_dir = "insufficient_data"
        if len(d1_slice) >= 10:
            d1_swings = detect_swings(d1_slice)
            d1_dir = identify_structure(d1_swings).direction

        for ob in h4_obs:
            if ob.mitigated:
                continue
            ob_time = candle_time_to_dt(ob.formation_time)
            if ob_time.date() < target_date - timedelta(days=14):
                continue

            all_h4_obs.append({
                "symbol": symbol,
                "formation_time": ob.formation_time,
                "ob_type": ob.type,
                "ob_high": ob.high,
                "ob_low": ob.low,
                "h4_atr": h4_atr,
                "d1_direction": d1_dir,
                "d1_aligned": d1_dir == ob.type,
            })

    # Detect retests on M15
    retested_count = 0
    kz_retested_count = 0
    hit_target_count = 0
    total = len(all_h4_obs)

    m15_avg_body = avg_candle_body(m15_candles[-200:] if len(m15_candles) > 200 else m15_candles, 20)

    for h4_ob in all_h4_obs:
        ob_time = candle_time_to_dt(h4_ob["formation_time"])
        ob_high = h4_ob["ob_high"]
        ob_low = h4_ob["ob_low"]
        ob_type = h4_ob["ob_type"]

        start_idx = None
        for i, c in enumerate(m15_candles):
            if candle_time_to_dt(c["time"]) > ob_time:
                start_idx = i
                break

        if start_idx is None:
            continue

        end_idx = min(start_idx + 384, len(m15_candles))  # ~4 days
        retested = False

        for i in range(start_idx, end_idx):
            c = m15_candles[i]
            if ob_type == "bullish" and c["low"] <= ob_high:
                retested = True
                in_kz, _ = is_in_kz(c["time"])
                if in_kz:
                    kz_retested_count += 1

                # Simple outcome check
                entry = c["close"]
                if symbol == "XAUUSD":
                    sl = ob_low - 0.001 * ob_low
                else:
                    sl = ob_low - 0.00015
                sl_dist = abs(entry - sl)
                target = entry + 1.5 * sl_dist

                for j in range(1, 13):
                    if i + j >= len(m15_candles):
                        break
                    if m15_candles[i + j]["high"] >= target:
                        hit_target_count += 1
                        break
                    if m15_candles[i + j]["low"] <= sl:
                        break
                break

            elif ob_type == "bearish" and c["high"] >= ob_low:
                retested = True
                in_kz, _ = is_in_kz(c["time"])
                if in_kz:
                    kz_retested_count += 1

                entry = c["close"]
                if symbol == "XAUUSD":
                    sl = ob_high + 0.001 * ob_high
                else:
                    sl = ob_high + 0.00015
                sl_dist = abs(sl - entry)
                target = entry - 1.5 * sl_dist

                for j in range(1, 13):
                    if i + j >= len(m15_candles):
                        break
                    if m15_candles[i + j]["low"] <= target:
                        hit_target_count += 1
                        break
                    if m15_candles[i + j]["high"] >= sl:
                        break
                break

        if retested:
            retested_count += 1

    return {
        "total_h4_obs": total,
        "retested": retested_count,
        "retested_pct": round(retested_count / total * 100, 2) if total > 0 else 0,
        "kz_retested": kz_retested_count,
        "hit_target": hit_target_count,
        "continuation_rate": round(hit_target_count / retested_count * 100, 2) if retested_count > 0 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Main Orchestration
# ═══════════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 70)
    logger.info("COMPREHENSIVE OB RETEST ANALYSIS")
    logger.info("=" * 70)

    # Load all data
    logger.info("Loading all candle data...")
    all_data = load_all_candles()

    # Build date indices
    date_indices = {}
    for symbol in SYMBOLS:
        date_indices[symbol] = {}
        for tf in ("D1", "H4", "H1", "M15"):
            date_indices[symbol][tf] = index_candles_by_date(all_data[symbol][tf])

    # Get all trading dates from H1 data
    all_dates = set()
    for symbol in SYMBOLS:
        for d in date_indices[symbol]["H1"].keys():
            if DISCOVERY_START <= d <= VALIDATION_END:
                all_dates.add(d)
    all_dates = sorted(all_dates)
    logger.info(f"Total trading dates: {len(all_dates)}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 1 & 2: Compute OBs and detect retests for ALL dates
    # ═══════════════════════════════════════════════════════════════
    all_ob_records = []
    dates_processed = 0

    for symbol in SYMBOLS:
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing {symbol}...")

        symbol_dates = sorted(date_indices[symbol]["H1"].keys())
        symbol_dates = [d for d in symbol_dates if DISCOVERY_START <= d <= VALIDATION_END]

        h1_candles = all_data[symbol]["H1"]
        m15_candles = all_data[symbol]["M15"]
        h4_candles = all_data[symbol]["H4"]
        d1_candles = all_data[symbol]["D1"]

        h1_idx = date_indices[symbol]["H1"]
        m15_idx = date_indices[symbol]["M15"]
        h4_idx = date_indices[symbol]["H4"]
        d1_idx = date_indices[symbol]["D1"]

        symbol_obs = []

        for i, target_date in enumerate(symbol_dates):
            if i % 50 == 0:
                logger.info(f"  {symbol} date {i+1}/{len(symbol_dates)}: {target_date}")

            try:
                day_obs = compute_obs_for_date(
                    symbol, target_date,
                    h1_candles, h1_idx,
                    d1_candles, d1_idx,
                    h4_candles, h4_idx,
                )
                symbol_obs.extend(day_obs)
            except Exception as e:
                logger.warning(f"  Error on {target_date}: {e}")
                continue

            dates_processed += 1

        logger.info(f"  {symbol}: {len(symbol_obs)} H1 OBs found across {len(symbol_dates)} dates")

        # Detect retests
        logger.info(f"  Detecting retests on M15 for {symbol}...")
        symbol_obs = detect_retests(symbol_obs, m15_candles, m15_idx, symbol)

        retested_count = sum(1 for o in symbol_obs if o.get("retest"))
        logger.info(f"  {symbol}: {retested_count}/{len(symbol_obs)} OBs retested")

        all_ob_records.extend(symbol_obs)

    # ═══════════════════════════════════════════════════════════════
    # Census
    # ═══════════════════════════════════════════════════════════════
    total_obs = len(all_ob_records)
    retested_obs = [o for o in all_ob_records if o.get("retest")]
    kz_retested = [o for o in retested_obs if o["retest"].get("retest_in_kz")]

    logger.info(f"\n{'='*50}")
    logger.info(f"OB CENSUS:")
    logger.info(f"  Total H1 OBs: {total_obs}")
    logger.info(f"  Retested: {len(retested_obs)} ({len(retested_obs)/total_obs*100:.1f}%)" if total_obs > 0 else "  Retested: 0")
    logger.info(f"  KZ-retested: {len(kz_retested)} ({len(kz_retested)/total_obs*100:.1f}%)" if total_obs > 0 else "  KZ: 0")

    # By instrument
    census_by_instrument = {}
    for symbol in SYMBOLS:
        sym_obs = [o for o in all_ob_records if o["symbol"] == symbol]
        sym_retested = [o for o in sym_obs if o.get("retest")]
        sym_kz = [o for o in sym_retested if o["retest"].get("retest_in_kz")]
        census_by_instrument[symbol] = {
            "total_obs": len(sym_obs),
            "retested": len(sym_retested),
            "retested_pct": round(len(sym_retested) / len(sym_obs) * 100, 2) if sym_obs else 0,
            "kz_retested": len(sym_kz),
            "kz_retested_pct": round(len(sym_kz) / len(sym_obs) * 100, 2) if sym_obs else 0,
        }

    # Overall success rate
    all_wins = sum(1 for o in retested_obs if o.get("outcome", {}).get("hit_target_3h", False))
    baseline_rate = all_wins / len(retested_obs) if retested_obs else 0
    logger.info(f"  Baseline continuation rate: {baseline_rate:.4f} ({all_wins}/{len(retested_obs)})")

    # ═══════════════════════════════════════════════════════════════
    # Split discovery/validation
    # ═══════════════════════════════════════════════════════════════
    discovery_retested = [o for o in retested_obs
                         if date.fromisoformat(o["date"]) <= DISCOVERY_END]
    validation_retested = [o for o in retested_obs
                          if date.fromisoformat(o["date"]) >= VALIDATION_START]

    logger.info(f"  Discovery retested: {len(discovery_retested)}")
    logger.info(f"  Validation retested: {len(validation_retested)}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 4A: Feature Analysis
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 4A: Feature Analysis...")
    discovery_features = compute_feature_analysis(discovery_retested, "discovery")
    validation_features = compute_feature_analysis(validation_retested, "validation")

    # Rank by spread in discovery
    discovery_features.sort(key=lambda x: -x["spread"])

    logger.info(f"  Features analyzed: {len(discovery_features)}")
    for f in discovery_features[:5]:
        logger.info(f"    {f['feature']}: spread={f['spread']:.4f}, p={f['p_value']:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 4B: Feature Combinations
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 4B: Feature Combinations...")
    # Top 5 features with >5pp spread and n>=50 per group
    top_features = []
    for f in discovery_features:
        if f["spread"] >= 0.05:  # 5pp
            min_n = min(g["n"] for g in f["groups"]) if f["groups"] else 0
            if min_n >= 50:
                top_features.append(f)
        if len(top_features) >= 5:
            break

    logger.info(f"  Top features for combinations: {[f['feature'] for f in top_features]}")

    discovery_combos = compute_feature_combinations(discovery_retested, top_features, "discovery")
    validation_combos = compute_feature_combinations(validation_retested, top_features, "validation")

    logger.info(f"  Combinations tested: {len(discovery_combos)}")
    for c in discovery_combos[:3]:
        logger.info(f"    {c['features']}: rate={c['rate_both']:.4f}, lift={c['lift']:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 4C: Quality Score
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 4C: Quality Score...")

    # Use all top features (not just those meeting strict criteria)
    score_features = top_features if top_features else discovery_features[:5]
    quality_disc = compute_quality_score(discovery_retested, score_features)
    quality_val = compute_quality_score(validation_retested, score_features)

    logger.info(f"  Score levels (discovery):")
    for lv in quality_disc["levels"]:
        logger.info(f"    Score {lv['score']}: n={lv['n']}, rate={lv['continuation_rate']:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 5: Cross-reference trades
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 5: Cross-reference with traded OBs...")
    trade_index_path = _PROJECT_ROOT / "knowledge_base" / "index" / "_trade_index.json"
    ai_selection = cross_reference_trades(retested_obs, quality_disc, trade_index_path)
    logger.info(f"  AI selection analysis: {ai_selection}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 6: M15 Confirmation
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 6: M15 Displacement Confirmation...")
    m15_analysis = analyze_m15_confirmation(retested_obs)
    logger.info(f"  With confirmation: {m15_analysis['with_confirmation']}")
    logger.info(f"  Without: {m15_analysis['without_confirmation']}")
    logger.info(f"  Spread: {m15_analysis['spread']:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Phase 7: H4 OBs
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nPhase 7: H4 OB Analysis...")
    h4_results = {}
    for symbol in SYMBOLS:
        symbol_dates = sorted(d for d in date_indices[symbol]["H4"].keys()
                             if DISCOVERY_START <= d <= VALIDATION_END)
        h4_res = compute_h4_obs(
            symbol, symbol_dates,
            all_data[symbol]["H4"], date_indices[symbol]["H4"],
            all_data[symbol]["D1"], date_indices[symbol]["D1"],
            all_data[symbol]["M15"], date_indices[symbol]["M15"],
        )
        h4_results[symbol] = h4_res
        logger.info(f"  {symbol} H4: {h4_res}")

    # Combined H4
    h4_combined = {
        "total_h4_obs": sum(v["total_h4_obs"] for v in h4_results.values()),
        "retested": sum(v["retested"] for v in h4_results.values()),
        "kz_retested": sum(v["kz_retested"] for v in h4_results.values()),
        "hit_target": sum(v["hit_target"] for v in h4_results.values()),
    }
    h4_combined["retested_pct"] = round(h4_combined["retested"] / h4_combined["total_h4_obs"] * 100, 2) if h4_combined["total_h4_obs"] > 0 else 0
    h4_combined["continuation_rate"] = round(h4_combined["hit_target"] / h4_combined["retested"] * 100, 2) if h4_combined["retested"] > 0 else 0

    # Estimate KZ per month
    total_months = (VALIDATION_END - DISCOVERY_START).days / 30.4
    h4_kz_per_month = round(h4_combined["kz_retested"] / total_months, 1) if total_months > 0 else 0

    # ═══════════════════════════════════════════════════════════════
    # Phase 5B: Missed opportunities
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nMissed Opportunities Analysis...")

    # Load trade dates for matching
    with open(trade_index_path) as f:
        trade_data = json.load(f)
    trade_keys = {(t["date"], t["symbol"]) for t in trade_data.get("trades", [])}

    # High-quality KZ retested OBs NOT traded
    threshold = quality_disc.get("threshold")
    high_quality_not_traded = []

    for s in quality_disc.get("scored_obs", []):
        o = s["ob"]
        if not o.get("retest", {}) or not o["retest"].get("retest_in_kz"):
            continue
        key = (o["date"], o["symbol"])
        if key in trade_keys:
            continue
        if threshold and s["score"] >= threshold:
            high_quality_not_traded.append(s)

    not_traded_wins = sum(1 for s in high_quality_not_traded if s["hit"])
    not_traded_rate = not_traded_wins / len(high_quality_not_traded) if high_quality_not_traded else 0
    not_traded_per_month = round(len(high_quality_not_traded) / total_months, 1) if total_months > 0 else 0

    missed_opps = {
        "high_quality_not_traded_total": len(high_quality_not_traded),
        "high_quality_not_traded_per_month": not_traded_per_month,
        "estimated_wr": round(not_traded_rate, 4),
        "quality_threshold_used": threshold,
    }

    logger.info(f"  Missed: {len(high_quality_not_traded)} total, {not_traded_per_month}/month, est WR: {not_traded_rate:.4f}")

    # ═══════════════════════════════════════════════════════════════
    # Build output JSON
    # ═══════════════════════════════════════════════════════════════
    logger.info("\nBuilding output...")

    # Merge discovery + validation feature analysis
    feature_ranking = []
    for df in discovery_features:
        vf = next((v for v in validation_features if v["feature"] == df["feature"]), None)
        feature_ranking.append({
            "feature": df["feature"],
            "discovery_groups": df["groups"],
            "discovery_spread": df["spread"],
            "discovery_chi2": df["chi2"],
            "discovery_p_value": df["p_value"],
            "validation_groups": vf["groups"] if vf else [],
            "validation_spread": vf["spread"] if vf else None,
            "validation_p_value": vf["p_value"] if vf else None,
        })

    output_json = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_range": f"{DISCOVERY_START} to {VALIDATION_END}",
        "discovery_period": f"{DISCOVERY_START} to {DISCOVERY_END}",
        "validation_period": f"{VALIDATION_START} to {VALIDATION_END}",
        "ob_census": {
            "total_obs": total_obs,
            "retested": len(retested_obs),
            "retested_pct": round(len(retested_obs) / total_obs * 100, 2) if total_obs > 0 else 0,
            "kz_retested": len(kz_retested),
            "kz_retested_pct": round(len(kz_retested) / total_obs * 100, 2) if total_obs > 0 else 0,
            "baseline_continuation_rate": round(baseline_rate, 4),
            "by_instrument": census_by_instrument,
        },
        "feature_ranking": feature_ranking,
        "combinations": {
            "discovery": discovery_combos,
            "validation": validation_combos,
            "total_tests": len(discovery_combos),
        },
        "quality_score": {
            "definition": quality_disc["definition"],
            "favorable_features": quality_disc["favorable_features"],
            "discovery_levels": quality_disc["levels"],
            "validation_levels": quality_val["levels"],
            "threshold": threshold,
        },
        "ai_selection": ai_selection,
        "m15_confirmation": m15_analysis,
        "h4_obs": {
            "combined": h4_combined,
            "by_instrument": h4_results,
            "kz_per_month": h4_kz_per_month,
        },
        "missed_opportunities": missed_opps,
    }

    # Save JSON
    json_path = OUTPUT_DIR / "ob_retest_comprehensive_20260405.json"
    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2, default=str)
    logger.info(f"Saved JSON: {json_path}")

    # ═══════════════════════════════════════════════════════════════
    # Generate Markdown Report
    # ═══════════════════════════════════════════════════════════════
    report = generate_report(output_json)
    md_path = OUTPUT_DIR / "ob_retest_comprehensive_20260405.md"
    with open(md_path, "w") as f:
        f.write(report)
    logger.info(f"Saved report: {md_path}")

    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("=" * 70)


def generate_report(data: dict) -> str:
    """Generate markdown report from analysis data."""
    census = data["ob_census"]
    fr = data["feature_ranking"]
    combos = data["combinations"]
    qs = data["quality_score"]
    ai = data["ai_selection"]
    m15 = data["m15_confirmation"]
    h4 = data["h4_obs"]
    missed = data["missed_opportunities"]

    lines = [
        "# Comprehensive OB Retest Analysis",
        f"Generated: {data['generated_utc']}",
        f"Data range: {data['data_range']}",
        f"Discovery: {data['discovery_period']} | Validation: {data['validation_period']}",
        "",
        "---",
        "",
        "## 1. OB Census",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total H1 OBs | {census['total_obs']:,} |",
        f"| Retested | {census['retested']:,} ({census['retested_pct']}%) |",
        f"| KZ-Retested | {census['kz_retested']:,} ({census['kz_retested_pct']}%) |",
        f"| **Baseline Continuation Rate** | **{census['baseline_continuation_rate']:.1%}** |",
        "",
        "### By Instrument",
        "",
        "| Instrument | Total OBs | Retested | Retested % | KZ Retested |",
        "|------------|-----------|----------|------------|-------------|",
    ]

    for sym, stats in census.get("by_instrument", {}).items():
        lines.append(f"| {sym} | {stats['total_obs']:,} | {stats['retested']:,} | {stats['retested_pct']}% | {stats['kz_retested']:,} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Feature Ranking (Discovery Period)",
        "",
        "| Rank | Feature | Spread | Chi2 p-value | Discovery Best | Validation Spread |",
        "|------|---------|--------|-------------|----------------|-------------------|",
    ])

    for i, f in enumerate(fr):
        best_group = max(f["discovery_groups"], key=lambda g: g["continuation_rate"]) if f["discovery_groups"] else {"group": "N/A", "continuation_rate": 0}
        val_spread = f"{f['validation_spread']:.4f}" if f["validation_spread"] is not None else "N/A"
        lines.append(
            f"| {i+1} | {f['feature']} | {f['discovery_spread']:.4f} | "
            f"{f['discovery_p_value']:.4f} | {best_group['group']} ({best_group['continuation_rate']:.1%}) | {val_spread} |"
        )

    # Feature detail tables
    lines.extend(["", "### Feature Details (Top 10)", ""])
    for f in fr[:10]:
        lines.extend([
            f"#### {f['feature']}",
            f"Discovery p={f['discovery_p_value']:.4f} | Validation p={f['validation_p_value']:.4f}" if f['validation_p_value'] else f"Discovery p={f['discovery_p_value']:.4f}",
            "",
            "| Group | N (disc) | Rate (disc) | N (val) | Rate (val) |",
            "|-------|----------|-------------|---------|------------|",
        ])
        val_groups = {g["group"]: g for g in f.get("validation_groups", [])}
        for dg in f["discovery_groups"]:
            vg = val_groups.get(dg["group"], {})
            vn = vg.get("n", "-")
            vr = f"{vg['continuation_rate']:.1%}" if "continuation_rate" in vg else "-"
            lines.append(f"| {dg['group']} | {dg['n']} | {dg['continuation_rate']:.1%} | {vn} | {vr} |")
        lines.append("")

    # Combinations
    lines.extend([
        "---",
        "",
        "## 3. Feature Combinations",
        "",
        f"Total combinations tested: {combos['total_tests']}",
        "",
        "### Discovery Period",
        "",
        "| Features | N | Rate | Baseline | Lift | p-value | Bonferroni Sig? |",
        "|----------|---|------|----------|------|---------|-----------------|",
    ])
    for c in combos.get("discovery", [])[:10]:
        sig = "YES" if c.get("significant_after_bonferroni") else "no"
        lines.append(
            f"| {' + '.join(c['features'])} | {c['n_both']} | {c['rate_both']:.1%} | "
            f"{c['baseline_rate']:.1%} | {c['lift']:+.1%} | {c['p_value']:.4f} | {sig} |"
        )

    # Quality Score
    lines.extend([
        "",
        "---",
        "",
        "## 4. OB Quality Score",
        "",
        f"**Definition:** {qs['definition']}",
        "",
        f"**Favorable features:**",
    ])
    for feat, val in qs.get("favorable_features", {}).items():
        lines.append(f"- {feat} = {val}")

    lines.extend([
        "",
        "### Continuation Rate by Score Level",
        "",
        "| Score | N (disc) | Rate (disc) | N (val) | Rate (val) |",
        "|-------|----------|-------------|---------|------------|",
    ])
    val_levels = {l["score"]: l for l in qs.get("validation_levels", [])}
    for dl in qs.get("discovery_levels", []):
        vl = val_levels.get(dl["score"], {})
        vn = vl.get("n", "-")
        vr = f"{vl['continuation_rate']:.1%}" if "continuation_rate" in vl else "-"
        lines.append(f"| {dl['score']} | {dl['n']} | {dl['continuation_rate']:.1%} | {vn} | {vr} |")

    if qs.get("threshold") is not None:
        lines.append(f"\n**Suggested threshold: >= {qs['threshold']}** (>55% continuation)")

    # AI Selection
    lines.extend([
        "",
        "---",
        "",
        "## 5. AI Selection Analysis",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total KZ-retested OBs | {ai.get('total_kz_retested', 'N/A')} |",
        f"| Matched to traded OBs | {ai.get('matched_to_trades', 'N/A')} |",
        f"| AI trades | {ai.get('trade_count', 'N/A')} |",
        f"| AI selection % | {ai.get('ai_selection_pct', 'N/A')}% |",
        f"| Traded avg quality score | {ai.get('traded_avg_score', 'N/A')} |",
        f"| Non-traded avg quality score | {ai.get('non_traded_avg_score', 'N/A')} |",
    ])

    # M15 Confirmation
    lines.extend([
        "",
        "---",
        "",
        "## 6. M15 Displacement Confirmation Value",
        "",
        f"| Condition | N | Continuation Rate |",
        f"|-----------|---|-------------------|",
        f"| All retests | {m15['all_retests']['n']} | {m15['all_retests']['rate']:.1%} |",
        f"| With M15 displacement | {m15['with_confirmation']['n']} | {m15['with_confirmation']['rate']:.1%} |",
        f"| Without M15 displacement | {m15['without_confirmation']['n']} | {m15['without_confirmation']['rate']:.1%} |",
        f"| **Spread** | | **{m15['spread']:+.1%}** |",
    ])

    if m15.get("displacement_ratio_analysis"):
        lines.extend([
            "",
            "### Displacement Ratio Analysis",
            "",
            "| Ratio Range | N | Rate |",
            "|-------------|---|------|",
        ])
        for ra in m15["displacement_ratio_analysis"]:
            lines.append(f"| {ra['range']} | {ra['n']} | {ra['rate']:.1%} |")

    # H4 OBs
    h4c = h4.get("combined", {})
    lines.extend([
        "",
        "---",
        "",
        "## 7. H4 OB Analysis",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total H4 OBs | {h4c.get('total_h4_obs', 0):,} |",
        f"| Retested | {h4c.get('retested', 0):,} ({h4c.get('retested_pct', 0)}%) |",
        f"| KZ Retested | {h4c.get('kz_retested', 0):,} |",
        f"| Continuation Rate | {h4c.get('continuation_rate', 0)}% |",
        f"| KZ per month | {h4.get('kz_per_month', 0)} |",
    ])

    # Missed Opportunities
    lines.extend([
        "",
        "---",
        "",
        "## 8. Missed Opportunities",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| High-quality non-traded total | {missed.get('high_quality_not_traded_total', 0):,} |",
        f"| Per month | {missed.get('high_quality_not_traded_per_month', 0)} |",
        f"| Estimated WR | {missed.get('estimated_wr', 0):.1%} |",
        f"| Quality threshold | >= {missed.get('quality_threshold_used', 'N/A')} |",
    ])

    # Top 5 Actionable Findings
    lines.extend([
        "",
        "---",
        "",
        "## 9. Top Actionable Findings",
        "",
        "*(To be filled after reviewing results — findings depend on what the data shows)*",
        "",
        "1. **Feature X**: [Finding based on highest-spread validated feature]",
        "2. **Feature Y**: [Second highest-impact finding]",
        "3. **M15 Confirmation**: [Value-add of displacement confirmation]",
        "4. **Quality Score**: [Whether additive score separates tradeable from non-tradeable]",
        "5. **Missed Opportunities**: [Frequency of high-quality untaken trades]",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    main()
