#!/usr/bin/env python3
"""FVG Per-Record Extraction — saves every H1 FVG with full features.

Reuses the same detection logic as smc_phase_b_comprehensive.py but outputs
per-record JSON + CSV. Includes fill data, context, and OB overlap check.

Usage:
    python knowledge_base_backtest/analysis/per_record_20260406/fvg_per_record_extract.py
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

DATE_START = date(2024, 4, 1)
DATE_END = date(2026, 3, 30)
DISCOVERY_END = date(2025, 6, 30)

LONDON_KZ = (dtime(7, 0), dtime(12, 0))
NY_KZ = (dtime(13, 0), dtime(17, 0))


def candle_time_to_dt(t: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc)
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
        idx_map[candle_date(c["time"])].append(i)
    return idx_map


def get_candles_up_to(candles, date_index, target_date, lookback):
    if target_date not in date_index:
        return []
    last_idx = date_index[target_date][-1]
    start_idx = max(0, last_idx - lookback + 1)
    return candles[start_idx:last_idx + 1]


def find_m15_idx_at_or_after(m15_candles, target_time, m15_time_idx):
    if target_time in m15_time_idx:
        return m15_time_idx[target_time]
    target_dt = candle_time_to_dt(target_time)
    if not m15_candles:
        return None
    first_dt = candle_time_to_dt(m15_candles[0]["time"])
    approx = int((target_dt - first_dt).total_seconds() / 900)
    approx = max(0, min(approx, len(m15_candles) - 1))
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


def _sl_buffer(symbol: str, price: float) -> float:
    if "XAU" in symbol:
        return price * 0.001
    else:
        return 0.00150


def walk_forward_outcome(m15_candles, start_idx, entry_price, sl_price, direction, max_candles=12):
    """Walk forward on M15 — returns continuation bool and R metrics."""
    risk = abs(entry_price - sl_price)
    if risk < 1e-10:
        return {"continuation_3h": False, "mfe_r": 0.0, "mae_r": 0.0}

    rr_target = 1.5
    tp_price = entry_price + rr_target * risk if direction == "long" else entry_price - rr_target * risk
    mfe = 0.0
    mae = 0.0

    for j in range(start_idx, min(start_idx + max_candles, len(m15_candles))):
        c = m15_candles[j]
        if direction == "long":
            if c["low"] <= sl_price:
                return {"continuation_3h": False, "mfe_r": round(mfe / risk, 3), "mae_r": round(mae / risk, 3)}
            if c["high"] >= tp_price:
                return {"continuation_3h": True, "mfe_r": round(rr_target, 3), "mae_r": round(mae / risk, 3)}
            mfe = max(mfe, c["high"] - entry_price)
            mae = max(mae, entry_price - c["low"])
        else:
            if c["high"] >= sl_price:
                return {"continuation_3h": False, "mfe_r": round(mfe / risk, 3), "mae_r": round(mae / risk, 3)}
            if c["low"] <= tp_price:
                return {"continuation_3h": True, "mfe_r": round(rr_target, 3), "mae_r": round(mae / risk, 3)}
            mfe = max(mfe, entry_price - c["low"])
            mae = max(mae, c["high"] - entry_price)

    return {"continuation_3h": False, "mfe_r": round(mfe / risk if risk > 0 else 0, 3),
            "mae_r": round(mae / risk if risk > 0 else 0, 3)}


# ═══════════════════════════════════════════════════════════════════════════
# Main extraction
# ═══════════════════════════════════════════════════════════════════════════

def extract_fvgs_for_symbol(symbol: str) -> list[dict]:
    logger.info(f"Processing {symbol}...")

    h1_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_H1.csv")
    m15_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_M15.csv")
    d1_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_D1.csv")
    h4_candles = parse_tradingview_csv(HISTORICAL_DIR / f"{symbol}_H4.csv")

    h1_date_idx = index_candles_by_date(h1_candles)
    d1_date_idx = index_candles_by_date(d1_candles)
    h4_date_idx = index_candles_by_date(h4_candles)
    m15_time_idx = {c["time"]: i for i, c in enumerate(m15_candles)}

    all_dates = sorted(set(candle_date(c["time"]) for c in h1_candles
                          if DATE_START <= candle_date(c["time"]) <= DATE_END))

    logger.info(f"  {symbol}: {len(all_dates)} trading dates")
    records = []

    for di, target_date in enumerate(all_dates):
        if di > 0 and di % 50 == 0:
            logger.info(f"  {symbol}: processed {di}/{len(all_dates)} dates, {len(records)} FVGs")

        h1_slice = get_candles_up_to(h1_candles, h1_date_idx, target_date, LOOKBACK["H1"])
        if len(h1_slice) < 20:
            continue

        h1_atr = calculate_atr(h1_slice)
        h1_avg_body = avg_candle_body(h1_slice)
        if h1_atr < 1e-10:
            continue

        min_gap = h1_atr * 0.1
        fvgs = identify_fvgs(h1_slice, min_gap)

        # Structure for OB overlap check
        h1_swings = detect_swings(h1_slice)
        h1_structure = identify_structure(h1_swings)
        h1_events = detect_structure_breaks(h1_slice, h1_swings, h1_structure)
        h1_obs = identify_order_blocks(h1_slice, h1_events)
        h1_pd = calculate_premium_discount(h1_swings, h1_structure)

        # D1 direction
        d1_slice = get_candles_up_to(d1_candles, d1_date_idx, target_date, LOOKBACK["D1"])
        d1_direction = "insufficient_data"
        if len(d1_slice) >= 10:
            d1_sw = detect_swings(d1_slice)
            d1_st = identify_structure(d1_sw)
            d1_direction = d1_st.direction

        # H4 direction
        h4_slice = get_candles_up_to(h4_candles, h4_date_idx, target_date, LOOKBACK["H4"])
        h4_direction = "insufficient_data"
        if len(h4_slice) >= 10:
            h4_sw = detect_swings(h4_slice)
            h4_st = identify_structure(h4_sw)
            h4_direction = h4_st.direction

        # Cutoff
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

            fvg_width = fvg.top - fvg.bottom
            width_pct_atr = fvg_width / h1_atr
            fvg_mid = fvg.midpoint

            # Middle candle displacement
            mid_idx = fvg.candle_indices[1]
            if mid_idx < len(h1_slice):
                mid_c = h1_slice[mid_idx]
                mid_body = abs(mid_c["close"] - mid_c["open"])
                creation_disp = mid_body / h1_avg_body if h1_avg_body > 0 else 0
            else:
                creation_disp = 0

            # KZ / session
            in_kz, kz_name = is_in_kz(fvg.formation_time)
            if kz_name:
                session = kz_name
            else:
                h = fvg_time_dt.hour
                if 0 <= h < 7:
                    session = "asian"
                elif 18 <= h:
                    session = "late"
                else:
                    session = "off_kz"

            # Premium/discount
            zone = "neutral"
            if h1_pd:
                if h1_pd.discount_zone.bottom <= fvg_mid <= h1_pd.discount_zone.top:
                    zone = "discount"
                elif h1_pd.premium_zone.bottom <= fvg_mid <= h1_pd.premium_zone.top:
                    zone = "premium"

            # D1/H4 alignment
            d1_aligned = (d1_direction == fvg.type)
            h4_aligned = (h4_direction == fvg.type)

            # OB overlap: does any unmitigated OB of same type overlap this FVG zone?
            ob_overlap = False
            for ob in h1_obs:
                if ob.type == fvg.type and not ob.mitigated:
                    if ob.low <= fvg.top and ob.high >= fvg.bottom:
                        ob_overlap = True
                        break

            # Scan M15 for fill
            m15_start = find_m15_idx_at_or_after(m15_candles, fvg.formation_time, m15_time_idx)
            if m15_start is None:
                continue

            filled = False
            fill_percentage = 0.0
            fill_time = None
            max_fill_depth = 0.0
            continuation_3h = False
            outcome_mfe_r = 0.0
            outcome_mae_r = 0.0
            freshness = None

            max_scan = 192  # ~48 H1 candles
            for mi in range(m15_start + 1, min(m15_start + max_scan, len(m15_candles))):
                mc = m15_candles[mi]

                if fvg.type == "bullish":
                    if mc["low"] <= fvg.top:
                        fill_pct = (fvg.top - mc["low"]) / fvg_width if fvg_width > 0 else 0
                        filled = True
                        fill_percentage = round(min(fill_pct, 2.0), 4)
                        fill_time = mc["time"]
                        freshness = (mi - m15_start) // 4
                        max_fill_depth = fill_pct

                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = fvg.bottom - buf
                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, "long")
                        continuation_3h = outcome["continuation_3h"]
                        outcome_mfe_r = outcome["mfe_r"]
                        outcome_mae_r = outcome["mae_r"]
                        break

                elif fvg.type == "bearish":
                    if mc["high"] >= fvg.bottom:
                        fill_pct = (mc["high"] - fvg.bottom) / fvg_width if fvg_width > 0 else 0
                        filled = True
                        fill_percentage = round(min(fill_pct, 2.0), 4)
                        fill_time = mc["time"]
                        freshness = (mi - m15_start) // 4
                        max_fill_depth = fill_pct

                        entry = mc["close"]
                        buf = _sl_buffer(symbol, entry)
                        sl = fvg.top + buf
                        outcome = walk_forward_outcome(m15_candles, mi + 1, entry, sl, "short")
                        continuation_3h = outcome["continuation_3h"]
                        outcome_mfe_r = outcome["mfe_r"]
                        outcome_mae_r = outcome["mae_r"]
                        break

            period = "discovery" if target_date <= DISCOVERY_END else "validation"

            records.append({
                "date": str(target_date),
                "formation_time": fvg.formation_time,
                "symbol": symbol,
                "timeframe": "H1",
                "fvg_type": fvg.type,
                "fvg_top": round(fvg.top, 5),
                "fvg_bottom": round(fvg.bottom, 5),
                "fvg_midpoint": round(fvg_mid, 5),
                "fvg_size": round(fvg_width, 5),
                "width_pct_atr": round(width_pct_atr, 4),
                "creation_displacement_ratio": round(creation_disp, 4),
                "d1_direction": d1_direction,
                "h4_direction": h4_direction,
                "d1_aligned": d1_aligned,
                "h4_aligned": h4_aligned,
                "session": session,
                "kz": in_kz,
                "premium_discount_zone": zone,
                "ob_overlap": ob_overlap,
                "filled": filled,
                "fill_percentage": fill_percentage,
                "fill_time": fill_time,
                "max_fill_depth": round(max_fill_depth, 4),
                "freshness_candles": freshness,
                "continuation_3h": continuation_3h,
                "outcome_mfe_r": outcome_mfe_r,
                "outcome_mae_r": outcome_mae_r,
                "period": period,
            })

    return records


def main():
    t0 = _time.time()
    logger.info("=== FVG Per-Record Extraction ===")

    all_records = []
    for symbol in ["XAUUSD", "GBPUSD"]:
        h1_path = HISTORICAL_DIR / f"{symbol}_H1.csv"
        if not h1_path.exists():
            logger.warning(f"Skipping {symbol} — data not found")
            continue
        records = extract_fvgs_for_symbol(symbol)
        all_records.extend(records)

    xauusd_records = [r for r in all_records if r["symbol"] == "XAUUSD"]
    gbpusd_records = [r for r in all_records if r["symbol"] == "GBPUSD"]

    # Save XAUUSD JSON + CSV
    json_path = OUTPUT_DIR / "fvg_per_record_xauusd.json"
    with open(json_path, "w") as f:
        json.dump(xauusd_records, f, indent=2, default=str)
    logger.info(f"Saved {len(xauusd_records)} XAUUSD FVG records to {json_path}")

    csv_path = OUTPUT_DIR / "fvg_per_record_xauusd.csv"
    if xauusd_records:
        fieldnames = list(xauusd_records[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(xauusd_records)

    if gbpusd_records:
        with open(OUTPUT_DIR / "fvg_per_record_gbpusd.json", "w") as f:
            json.dump(gbpusd_records, f, indent=2, default=str)
        csv_gbp = OUTPUT_DIR / "fvg_per_record_gbpusd.csv"
        fieldnames = list(gbpusd_records[0].keys())
        with open(csv_gbp, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(gbpusd_records)

    elapsed = _time.time() - t0

    # Print summary
    print(f"\n{'='*60}")
    print(f"FVG Per-Record Extraction Summary")
    print(f"{'='*60}")
    print(f"XAUUSD records: {len(xauusd_records)}")
    if gbpusd_records:
        print(f"GBPUSD records: {len(gbpusd_records)}")
    print(f"Total records:  {len(all_records)}")

    if xauusd_records:
        filled = [r for r in xauusd_records if r["filled"]]
        continued = [r for r in filled if r["continuation_3h"]]
        print(f"\nXAUUSD filled: {len(filled)} ({len(filled)/len(xauusd_records)*100:.1f}%)")
        if filled:
            print(f"XAUUSD continuation: {len(continued)} ({len(continued)/len(filled)*100:.1f}% of filled)")

        # Fill % stats
        fill_pcts = [r["fill_percentage"] for r in filled]
        if fill_pcts:
            print(f"\nFill % distribution (n={len(fill_pcts)}):")
            print(f"  min:    {min(fill_pcts):.4f}")
            print(f"  Q1:     {np.percentile(fill_pcts, 25):.4f}")
            print(f"  median: {np.median(fill_pcts):.4f}")
            print(f"  Q3:     {np.percentile(fill_pcts, 75):.4f}")
            print(f"  max:    {max(fill_pcts):.4f}")

        # Date range
        dates = sorted(set(r["date"] for r in xauusd_records))
        print(f"\nDate range: {dates[0]} to {dates[-1]}")

        # Sample
        print(f"\nSample record (first):")
        print(json.dumps(xauusd_records[0], indent=2, default=str))

    print(f"\nElapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
