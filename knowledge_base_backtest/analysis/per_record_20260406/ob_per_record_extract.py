#!/usr/bin/env python3
"""OB Per-Record Extraction — saves every H1 OB with full features + retracement_pct.

Reuses the same detection logic as ob_retest_comprehensive.py but outputs
per-record JSON + CSV instead of aggregate statistics.

Key new field: retracement_pct — how deep the pullback to the OB was as a
percentage of the impulse leg that created it.

Usage:
    python knowledge_base_backtest/analysis/per_record_20260406/ob_per_record_extract.py
"""

from __future__ import annotations

import csv
import json
import logging
import sys
import time as _time
from collections import defaultdict
from datetime import datetime, date, timedelta, timezone, time as dtime
from pathlib import Path
from typing import Optional

import numpy as np

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

HISTORICAL_DIR = _PROJECT_ROOT / "data" / "historical"
OUTPUT_DIR = Path(__file__).resolve().parent

# Date range matching the comprehensive analysis
DATE_START = date(2024, 4, 1)
DATE_END = date(2026, 3, 30)
DISCOVERY_END = date(2025, 6, 30)

# Kill zone windows (UTC)
LONDON_KZ = (dtime(7, 0), dtime(12, 0))
NY_KZ = (dtime(13, 0), dtime(17, 0))


# ═══════════════════════════════════════════════════════════════════════════
# Utilities (same as comprehensive)
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


def candle_dow(t: str) -> str:
    return candle_time_to_dt(t).strftime("%A")


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


def get_candles_up_to(candles, date_index, target_date, lookback):
    if target_date not in date_index:
        return []
    last_idx = date_index[target_date][-1]
    start_idx = max(0, last_idx - lookback + 1)
    return candles[start_idx:last_idx + 1]


# ═══════════════════════════════════════════════════════════════════════════
# Retracement % Calculation
# ═══════════════════════════════════════════════════════════════════════════

def compute_retracement_pct(ob, h1_slice, causing_event):
    """Compute how deep the retracement was to reach this OB, as % of impulse.

    For a bullish OB:
      - The impulse goes UP from the OB zone to the swing high created by the BOS
      - Impulse range = swing_high - ob_low
      - When price retraces back to OB: retracement depth = swing_high - ob_midpoint
      - retracement_pct = (swing_high - ob_midpoint) / (swing_high - ob_low)
      i.e., how much of the impulse has been retraced when price reaches OB midpoint

    For a bearish OB:
      - The impulse goes DOWN from the OB zone to the swing low created by the BOS
      - Impulse range = ob_high - swing_low
      - retracement_pct = (ob_midpoint - swing_low) / (ob_high - swing_low)
    """
    ob_mid = (ob.high + ob.low) / 2
    bos_idx = ob.causing_bos_index

    if ob.type == "bullish":
        # Find the highest point between the BOS candle and the end of the impulse
        # The impulse high is the highest high from the OB formation to some candles after BOS
        search_end = min(bos_idx + 10, len(h1_slice))
        if bos_idx >= len(h1_slice):
            return None
        impulse_high = max(c["high"] for c in h1_slice[ob.formation_index:search_end])
        impulse_range = impulse_high - ob.low
        if impulse_range <= 0:
            return None
        # Retracement to OB midpoint as % of impulse
        retrace_depth = impulse_high - ob_mid
        return round(retrace_depth / impulse_range, 4)

    elif ob.type == "bearish":
        search_end = min(bos_idx + 10, len(h1_slice))
        if bos_idx >= len(h1_slice):
            return None
        impulse_low = min(c["low"] for c in h1_slice[ob.formation_index:search_end])
        impulse_range = ob.high - impulse_low
        if impulse_range <= 0:
            return None
        retrace_depth = ob_mid - impulse_low
        return round(retrace_depth / impulse_range, 4)

    return None


def compute_impulse_characteristics(ob, h1_slice, h1_atr):
    """Compute characteristics of the impulse leg that created this OB."""
    start_idx = ob.formation_index
    end_idx = min(ob.causing_bos_index + 5, len(h1_slice))
    if end_idx <= start_idx:
        return {}

    impulse_candles = h1_slice[start_idx:end_idx]
    if not impulse_candles:
        return {}

    candle_count = len(impulse_candles)
    bodies = [abs(c["close"] - c["open"]) for c in impulse_candles]
    ranges = [c["high"] - c["low"] for c in impulse_candles]

    if ob.type == "bullish":
        impulse_range = max(c["high"] for c in impulse_candles) - min(c["low"] for c in impulse_candles)
    else:
        impulse_range = max(c["high"] for c in impulse_candles) - min(c["low"] for c in impulse_candles)

    avg_body_ratio = float(np.mean([b / r if r > 0 else 0 for b, r in zip(bodies, ranges)]))
    atr_multiple = impulse_range / h1_atr if h1_atr > 0 else 0

    return {
        "impulse_candle_count": candle_count,
        "impulse_atr_multiple": round(atr_multiple, 4),
        "impulse_body_ratio_avg": round(avg_body_ratio, 4),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Per-Date OB Extraction
# ═══════════════════════════════════════════════════════════════════════════

def extract_obs_for_date(
    symbol: str,
    target_date: date,
    h1_candles: list[dict],
    h1_date_idx: dict,
    d1_candles: list[dict],
    d1_date_idx: dict,
    h4_candles: list[dict],
    h4_date_idx: dict,
    m15_candles: list[dict],
    m15_date_idx: dict,
) -> list[dict]:
    """Extract all H1 OBs for a single date with full per-record features."""

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

    # Asian range
    asian_candles = [c for c in h1_slice
                     if candle_date(c["time"]) == target_date
                     and 0 <= candle_hour(c["time"]) < 7]
    asian_high = max((c["high"] for c in asian_candles), default=0)
    asian_low = min((c["low"] for c in asian_candles), default=0)
    asian_range = asian_high - asian_low if asian_candles else 0

    if len(d1_slice) >= 14:
        adr = sum(c["high"] - c["low"] for c in d1_slice[-14:]) / 14
    else:
        adr = h1_atr * 24 if h1_atr > 0 else 1
    asian_pct_adr = asian_range / adr if adr > 0 else 0

    # Today's H1 candles
    today_candles = [c for c in h1_slice if candle_date(c["time"]) == target_date]
    if not today_candles:
        return []
    last_time = candle_time_to_dt(today_candles[-1]["time"])
    cutoff_time = last_time - timedelta(hours=3)

    # M15 candles for retest detection
    m15_avg_body = avg_candle_body(m15_candles[-200:] if len(m15_candles) > 200 else m15_candles, 20)

    results = []

    for ob in h1_obs:
        if ob.mitigated:
            continue

        ob_time = candle_time_to_dt(ob.formation_time)
        if ob_time.date() < target_date - timedelta(days=7):
            continue
        if ob_time > cutoff_time:
            continue

        # === Core OB features ===
        ob_width = ob.high - ob.low
        width_pct_atr = ob_width / h1_atr if h1_atr > 0 else 0
        body = abs(ob.close - ob.open)
        body_range_ratio = body / ob_width if ob_width > 0 else 0
        ob_mid = (ob.high + ob.low) / 2

        # Causing event
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

        # Alignment
        d1_aligned = (d1_direction == ob.type)
        h4_aligned = (h4_direction == ob.type)

        # FVG overlap
        fvg_overlap = False
        for fvg in h1_fvgs:
            if fvg.type == ob.type:
                if ob.low <= fvg.top and ob.high >= fvg.bottom:
                    fvg_overlap = True
                    break

        # Nearby OB count
        nearby_count = 0
        for other_ob in h1_obs:
            if other_ob is not ob and other_ob.type == ob.type and not other_ob.mitigated:
                dist = abs((other_ob.high + other_ob.low) / 2 - ob_mid)
                if dist < h1_atr:
                    nearby_count += 1

        # OB sequence
        same_type_obs = [o for o in h1_obs if o.type == ob.type
                         and o.formation_index <= ob.formation_index]
        ob_seq = len(same_type_obs)

        # Session
        form_hour = candle_hour(ob.formation_time)
        if 0 <= form_hour < 7:
            session = "asian"
        elif 7 <= form_hour < 13:
            session = "london"
        elif 13 <= form_hour < 18:
            session = "ny"
        else:
            session = "late"

        # === NEW: Retracement % ===
        retracement_pct = compute_retracement_pct(ob, h1_slice, causing_event)

        # === NEW: Impulse characteristics ===
        impulse_chars = compute_impulse_characteristics(ob, h1_slice, h1_atr)

        # === NEW: FVG created by impulse? ===
        impulse_created_fvg = False
        for fvg in h1_fvgs:
            fvg_dt = candle_time_to_dt(fvg.formation_time)
            ob_dt = candle_time_to_dt(ob.formation_time)
            if ob_dt <= fvg_dt <= ob_dt + timedelta(hours=10):
                if fvg.type == ob.type:
                    impulse_created_fvg = True
                    break

        # === Retest detection (same logic as comprehensive) ===
        retested = False
        continuation = False
        kz_at_retest = None
        time_of_retest = None
        retest_freshness = None
        retest_outcome = {}

        # Find M15 start after OB formation
        start_m15_idx = None
        for i, c in enumerate(m15_candles):
            if candle_time_to_dt(c["time"]) > ob_time:
                start_m15_idx = i
                break

        if start_m15_idx is not None:
            end_m15_idx = min(start_m15_idx + 192, len(m15_candles))
            in_zone = False

            for i in range(start_m15_idx, end_m15_idx):
                c = m15_candles[i]
                if ob.type == "bullish":
                    enters_zone = c["low"] <= ob.high
                else:
                    enters_zone = c["high"] >= ob.low

                if enters_zone and not in_zone:
                    in_zone = True
                    retested = True
                    time_of_retest = c["time"]
                    retest_dt = candle_time_to_dt(c["time"])
                    retest_freshness = max(1, int((retest_dt - ob_time).total_seconds() / 3600))
                    in_kz, kz_name = is_in_kz(c["time"])
                    kz_at_retest = kz_name if in_kz else None

                    # Determine entry/SL
                    if ob.type == "bullish":
                        entry_price = c["close"] if c["close"] >= ob.low else (
                            m15_candles[i + 1]["open"] if i + 1 < len(m15_candles) else c["close"])
                        sl_price = ob.low - (0.001 * ob.low if symbol == "XAUUSD" else 0.00015)
                    else:
                        entry_price = c["close"] if c["close"] <= ob.high else (
                            m15_candles[i + 1]["open"] if i + 1 < len(m15_candles) else c["close"])
                        sl_price = ob.high + (0.001 * ob.high if symbol == "XAUUSD" else 0.00015)

                    sl_distance = abs(entry_price - sl_price)
                    target_distance = 1.5 * sl_distance
                    entry_idx = i if ob.type == "bullish" and c["close"] >= ob.low else (
                        i + 1 if i + 1 < len(m15_candles) else i)

                    # Walk forward 12 M15 candles
                    hit_target = False
                    mfe = 0.0
                    mae = 0.0
                    for j in range(1, 13):
                        idx = entry_idx + j
                        if idx >= len(m15_candles):
                            break
                        mc = m15_candles[idx]
                        if ob.type == "bullish":
                            mfe = max(mfe, mc["high"] - entry_price)
                            mae = max(mae, entry_price - mc["low"])
                            if mc["low"] <= sl_price:
                                break
                            if mc["high"] >= entry_price + target_distance:
                                hit_target = True
                                break
                        else:
                            mfe = max(mfe, entry_price - mc["low"])
                            mae = max(mae, mc["high"] - entry_price)
                            if mc["high"] >= sl_price:
                                break
                            if mc["low"] <= entry_price - target_distance:
                                hit_target = True
                                break

                    continuation = hit_target
                    mfe_r = mfe / sl_distance if sl_distance > 0 else 0
                    mae_r = mae / sl_distance if sl_distance > 0 else 0
                    retest_outcome = {
                        "hit_target_3h": hit_target,
                        "mfe_r": round(mfe_r, 3),
                        "mae_r": round(mae_r, 3),
                    }

                    # M15 displacement at retest
                    m15_disp = False
                    m15_disp_ratio = 0.0
                    for offset in range(3):
                        check_idx = entry_idx + offset
                        if check_idx >= len(m15_candles):
                            break
                        mc = m15_candles[check_idx]
                        mbody = abs(mc["close"] - mc["open"])
                        mratio = mbody / m15_avg_body if m15_avg_body > 0 else 0
                        if mratio >= 1.5:
                            if ob.type == "bullish" and mc["close"] > mc["open"]:
                                m15_disp = True
                                m15_disp_ratio = mratio
                                break
                            elif ob.type == "bearish" and mc["close"] < mc["open"]:
                                m15_disp = True
                                m15_disp_ratio = mratio
                                break

                    retest_outcome["m15_displacement_at_retest"] = m15_disp
                    retest_outcome["m15_displacement_ratio"] = round(m15_disp_ratio, 2)
                    break  # Only first retest

                elif not enters_zone:
                    in_zone = False

        # Determine period
        period = "discovery" if target_date <= DISCOVERY_END else "validation"

        record = {
            "date": str(target_date),
            "formation_time": ob.formation_time,
            "symbol": symbol,
            "timeframe": "H1",
            "ob_type": ob.type,
            "ob_price_top": round(ob.high, 5),
            "ob_price_bottom": round(ob.low, 5),
            "ob_midpoint": round(ob_mid, 5),
            "ob_open": round(ob.open, 5),
            "ob_close": round(ob.close, 5),
            "causing_event_type": causing_type,
            "d1_direction": d1_direction,
            "h4_direction": h4_direction,
            "h4_aligned": h4_aligned,
            "d1_aligned": d1_aligned,
            "body_range_ratio": round(body_range_ratio, 4),
            "width_pct_atr": round(width_pct_atr, 4),
            "displacement_ratio_at_formation": round(displacement_ratio, 2),
            "retracement_pct": retracement_pct,
            "premium_discount_zone": zone,
            "in_ote": in_ote,
            "session": session,
            "hour_of_formation": form_hour,
            "day_of_week": candle_dow(ob.formation_time),
            "nearby_ob_count": nearby_count,
            "ob_sequence_number": ob_seq,
            "fvg_overlap": fvg_overlap,
            "impulse_created_fvg": impulse_created_fvg,
            **impulse_chars,
            "asian_range_pct_adr": round(asian_pct_adr, 4),
            "h1_atr": round(h1_atr, 4),
            "retested": retested,
            "continuation": continuation,
            "kz_at_retest": kz_at_retest,
            "time_of_retest": time_of_retest,
            "freshness_candles": retest_freshness,
            **{f"outcome_{k}": v for k, v in retest_outcome.items()},
            "period": period,
        }
        results.append(record)

    return results


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    t0 = _time.time()
    logger.info("=== OB Per-Record Extraction ===")

    symbols_to_run = []
    for symbol in ["XAUUSD", "GBPUSD"]:
        h1_path = HISTORICAL_DIR / f"{symbol}_H1.csv"
        if h1_path.exists():
            symbols_to_run.append(symbol)
        else:
            logger.warning(f"Skipping {symbol} — H1 data not found")

    all_records = []

    for symbol in symbols_to_run:
        logger.info(f"Processing {symbol}...")

        # Load candles
        h1_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_H1.csv")
        d1_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_D1.csv")
        h4_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_H4.csv")
        m15_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_M15.csv")

        h1_date_idx = index_candles_by_date(h1_candles)
        d1_date_idx = index_candles_by_date(d1_candles)
        h4_date_idx = index_candles_by_date(h4_candles)
        m15_date_idx = index_candles_by_date(m15_candles)

        # Get all trading dates in range
        all_dates = sorted(set(candle_date(c["time"]) for c in h1_candles
                              if DATE_START <= candle_date(c["time"]) <= DATE_END))

        logger.info(f"  {symbol}: {len(all_dates)} trading dates to process")
        symbol_records = []

        for di, target_date in enumerate(all_dates):
            if di > 0 and di % 50 == 0:
                logger.info(f"  {symbol}: processed {di}/{len(all_dates)} dates, {len(symbol_records)} OBs so far")

            day_records = extract_obs_for_date(
                symbol, target_date,
                h1_candles, h1_date_idx,
                d1_candles, d1_date_idx,
                h4_candles, h4_date_idx,
                m15_candles, m15_date_idx,
            )
            symbol_records.extend(day_records)

        logger.info(f"  {symbol}: {len(symbol_records)} total OB records")
        all_records.extend(symbol_records)

    # Save JSON
    json_path = OUTPUT_DIR / "ob_per_record_xauusd.json"
    # If GBPUSD also ran, save combined; but also save XAUUSD-only
    xauusd_records = [r for r in all_records if r["symbol"] == "XAUUSD"]
    gbpusd_records = [r for r in all_records if r["symbol"] == "GBPUSD"]

    with open(json_path, "w") as f:
        json.dump(xauusd_records, f, indent=2, default=str)
    logger.info(f"Saved {len(xauusd_records)} XAUUSD records to {json_path}")

    if gbpusd_records:
        gbp_path = OUTPUT_DIR / "ob_per_record_gbpusd.json"
        with open(gbp_path, "w") as f:
            json.dump(gbpusd_records, f, indent=2, default=str)
        logger.info(f"Saved {len(gbpusd_records)} GBPUSD records to {gbp_path}")

    # Save CSV (XAUUSD)
    csv_path = OUTPUT_DIR / "ob_per_record_xauusd.csv"
    if xauusd_records:
        # Collect ALL fieldnames across all records (some have outcome fields, some don't)
        all_fields = set()
        for r in xauusd_records:
            all_fields.update(r.keys())
        # Stable ordering: use first record's keys, then any extras
        fieldnames = list(xauusd_records[0].keys())
        for f_name in sorted(all_fields - set(fieldnames)):
            fieldnames.append(f_name)
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in xauusd_records:
                writer.writerow({fn: r.get(fn, "") for fn in fieldnames})
        logger.info(f"Saved CSV to {csv_path}")

    if gbpusd_records:
        csv_gbp = OUTPUT_DIR / "ob_per_record_gbpusd.csv"
        all_fields = set()
        for r in gbpusd_records:
            all_fields.update(r.keys())
        fieldnames = list(gbpusd_records[0].keys())
        for f_name in sorted(all_fields - set(fieldnames)):
            fieldnames.append(f_name)
        with open(csv_gbp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in gbpusd_records:
                writer.writerow({fn: r.get(fn, "") for fn in fieldnames})

    elapsed = _time.time() - t0
    logger.info(f"=== Done in {elapsed:.1f}s ===")

    # Print verification summary
    print(f"\n{'='*60}")
    print(f"OB Per-Record Extraction Summary")
    print(f"{'='*60}")
    print(f"XAUUSD records: {len(xauusd_records)}")
    if gbpusd_records:
        print(f"GBPUSD records: {len(gbpusd_records)}")
    print(f"Total records:  {len(all_records)}")

    if xauusd_records:
        retested = [r for r in xauusd_records if r["retested"]]
        continued = [r for r in retested if r["continuation"]]
        print(f"\nXAUUSD retested: {len(retested)} ({len(retested)/len(xauusd_records)*100:.1f}%)")
        if retested:
            print(f"XAUUSD continuation: {len(continued)} ({len(continued)/len(retested)*100:.1f}% of retested)")

        # Retracement pct stats
        ret_pcts = [r["retracement_pct"] for r in xauusd_records if r["retracement_pct"] is not None]
        if ret_pcts:
            print(f"\nRetracement % (n={len(ret_pcts)}):")
            print(f"  min:    {min(ret_pcts):.4f}")
            print(f"  Q1:     {np.percentile(ret_pcts, 25):.4f}")
            print(f"  median: {np.median(ret_pcts):.4f}")
            print(f"  Q3:     {np.percentile(ret_pcts, 75):.4f}")
            print(f"  max:    {max(ret_pcts):.4f}")
            print(f"  mean:   {np.mean(ret_pcts):.4f}")

        # Body range ratio stats
        brr = [r["body_range_ratio"] for r in xauusd_records]
        print(f"\nBody range ratio (n={len(brr)}):")
        print(f"  min:    {min(brr):.4f}")
        print(f"  median: {np.median(brr):.4f}")
        print(f"  max:    {max(brr):.4f}")

        # Causing event type distribution
        from collections import Counter
        evt_counts = Counter(r["causing_event_type"] for r in xauusd_records)
        print(f"\nCausing event types: {dict(evt_counts)}")

        # Date range
        dates = sorted(set(r["date"] for r in xauusd_records))
        print(f"\nDate range: {dates[0]} to {dates[-1]}")

        # Sample record
        print(f"\nSample record (first):")
        print(json.dumps(xauusd_records[0], indent=2, default=str))

    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
