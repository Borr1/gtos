#!/usr/bin/env python3
"""
Multi-Instrument OB & FVG Screening Analysis
Detects H1 Order Blocks, measures retest continuation rates, FVG fills,
cross-instrument correlations, and spread costs to screen expansion candidates.
"""

import os
import sys
import json
import time
import warnings
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ─── CONFIG ───────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "exports" / "multi_instrument"
OUTPUT_DIR = DATA_DIR / "screening_results"
EXTRACTION_SUMMARY = DATA_DIR / "extraction_summary.json"

SWING_MIN_BARS = 2
WARMUP_CANDLES = 100
MIN_DISPLACEMENT_ATR = 0.4
BODY_RATIO_MIN = 0.40
RETEST_WINDOW = 250  # H1 candles (~10 trading days)
CONTINUATION_WINDOW = 20  # candles after retest
ATR_PERIOD = 14
TARGET_ATR_MULT = 1.25
STOP_ATR_MULT = 0.5
FVG_MIN_GAP_ATR = 0.3
FVG_FILL_THRESHOLD = 0.80
FVG_LOOKFORWARD = 100
MIN_H1_CANDLES = 500
CORR_HIGH_THRESHOLD = 0.60

# ─── DATA CLASSES ─────────────────────────────────────────────────────────────

@dataclass
class Swing:
    index: int
    price: float
    swing_type: str  # 'high' or 'low'
    classification: str = ''  # HH, HL, LH, LL
    consumed: bool = False

@dataclass
class BreakEvent:
    index: int
    event_type: str  # 'BOS' or 'CHoCH'
    direction: str   # 'bullish' or 'bearish'
    broken_swing: Swing = None
    displacement_atr: float = 0.0
    body_ratio: float = 0.0
    quality_pass: bool = False

@dataclass
class OrderBlock:
    direction: str
    high: float
    low: float
    formation_index: int
    formation_time: object = None
    event_type: str = ''
    event_index: int = 0
    retested: bool = False
    retest_index: int = -1
    retest_time: object = None
    continuation: Optional[bool] = None
    candles_to_resolution: int = -1
    max_favorable: float = 0.0
    max_adverse: float = 0.0

@dataclass
class FVG:
    fvg_type: str  # 'bullish' or 'bearish'
    top: float
    bottom: float
    gap_size: float
    formation_index: int
    formation_time: object = None
    filled: bool = False
    max_fill_depth: float = 0.0
    fill_candle_index: int = -1
    continuation: Optional[bool] = None

# ─── TIMEZONE CONVERSION ─────────────────────────────────────────────────────

def convert_to_utc(df: pd.DataFrame) -> pd.DataFrame:
    """Convert EET server timestamps to UTC."""
    try:
        import pytz
        eet = pytz.timezone('EET')
        dt = pd.to_datetime(df['time'])
        df['dt_utc'] = dt.dt.tz_localize(eet, ambiguous='infer', nonexistent='shift_forward').dt.tz_convert('UTC').dt.tz_localize(None)
    except Exception:
        # Fallback: approximate - assume UTC+2 (most of the year is close enough)
        df['dt_utc'] = pd.to_datetime(df['time']) - pd.Timedelta(hours=2)
    return df

# ─── DATA LOADING ────────────────────────────────────────────────────────────

def load_instrument(symbol: str, timeframe: str = 'H1') -> Optional[pd.DataFrame]:
    """Load candle data for an instrument."""
    # Try exact filename first, then dotted version
    candidates = [
        DATA_DIR / f"{symbol}_{timeframe}.csv",
        DATA_DIR / f"{symbol.replace('.', '_')}_{timeframe}.csv",
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            # Standardize columns
            required = ['time', 'open', 'high', 'low', 'close']
            if not all(c in df.columns for c in required):
                print(f"  WARNING: {symbol} missing columns, skipping")
                return None
            df = convert_to_utc(df)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            return df
    return None

def compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Compute ATR as numpy array aligned to df index."""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    n = len(df)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
    atr = np.zeros(n)
    atr[:period] = np.nan
    atr[period] = np.mean(tr[1:period+1])
    for i in range(period+1, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr

def data_quality_check(df: pd.DataFrame, symbol: str) -> dict:
    """Check data quality and return stats."""
    dt = df['dt_utc']
    total_candles = len(df)
    date_range = (dt.min(), dt.max())
    trading_days = dt.dt.date.nunique()

    # Check for gaps > 4h (excluding weekends Fri 21 UTC - Sun 21 UTC)
    diffs = dt.diff().dt.total_seconds() / 3600
    gap_flags = []
    for i in range(1, len(df)):
        if diffs.iloc[i] > 4:
            day_of_week = dt.iloc[i-1].weekday()  # Mon=0, Fri=4
            hour = dt.iloc[i-1].hour
            # Skip if it's a weekend gap
            if day_of_week == 4 and hour >= 20:
                continue
            gap_flags.append((i, diffs.iloc[i]))

    zero_vol_pct = 0.0
    if 'tick_volume' in df.columns:
        zero_vol_pct = (df['tick_volume'] == 0).mean() * 100
    elif 'volume' in df.columns:
        zero_vol_pct = (df['volume'] == 0).mean() * 100

    return {
        'total_candles': total_candles,
        'date_range': (str(date_range[0]), str(date_range[1])),
        'trading_days': trading_days,
        'gaps_gt_4h': len(gap_flags),
        'zero_volume_pct': round(zero_vol_pct, 2),
    }

# ─── SWING DETECTION ─────────────────────────────────────────────────────────

def detect_swings_at(highs, lows, i, min_bars=2):
    """Check if candle at index i is a swing high and/or low."""
    n = len(highs)
    is_high = False
    is_low = False

    if i >= min_bars and i < n - min_bars:
        # Swing high
        is_high = True
        for j in range(1, min_bars + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_high = False
                break
        # Swing low
        is_low = True
        for j in range(1, min_bars + 1):
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_low = False
                break
    return is_high, is_low

# ─── MAIN PROCESSING: SINGLE LEFT-TO-RIGHT PASS ──────────────────────────────

def process_candles(df: pd.DataFrame, atr: np.ndarray):
    """
    Single left-to-right pass: detect swings, structure, breaks, OBs.
    """
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['dt_utc'].values
    n = len(df)

    confirmed_swings: List[Swing] = []
    swing_highs: List[Swing] = []
    swing_lows: List[Swing] = []

    structure_direction = 'transitional'
    protected_swing: Optional[Swing] = None

    order_blocks: List[OrderBlock] = []
    break_events: List[BreakEvent] = []

    for i in range(SWING_MIN_BARS, n - SWING_MIN_BARS):
        # Check if candle at (i - SWING_MIN_BARS) is now confirmed
        check_idx = i  # We confirm swing at check_idx - min_bars happened min_bars ago
        confirm_idx = i - SWING_MIN_BARS
        if confirm_idx < SWING_MIN_BARS:
            continue

        is_high, is_low = detect_swings_at(highs, lows, confirm_idx, SWING_MIN_BARS)

        if is_high:
            sw = Swing(index=confirm_idx, price=highs[confirm_idx], swing_type='high')
            # Classify
            if swing_highs:
                prev = swing_highs[-1]
                sw.classification = 'HH' if sw.price > prev.price else 'LH'
            else:
                sw.classification = 'HH'
            confirmed_swings.append(sw)
            swing_highs.append(sw)

        if is_low:
            sw = Swing(index=confirm_idx, price=lows[confirm_idx], swing_type='low')
            if swing_lows:
                prev = swing_lows[-1]
                sw.classification = 'HL' if sw.price > prev.price else 'LL'
            else:
                sw.classification = 'HL'
            confirmed_swings.append(sw)
            swing_lows.append(sw)

        # Update structure based on recent swings
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_h = swing_highs[-1].classification
            last_l = swing_lows[-1].classification
            if last_h == 'HH' and last_l == 'HL':
                structure_direction = 'bullish'
                protected_swing = swing_lows[-1]
            elif last_h == 'LH' and last_l == 'LL':
                structure_direction = 'bearish'
                protected_swing = swing_highs[-1]

        # Skip warmup for OB detection
        if i < WARMUP_CANDLES:
            continue
        if np.isnan(atr[i]) or atr[i] == 0:
            continue

        # Check for structural breaks at candle i
        break_event = None

        # CHoCH checks (priority)
        if protected_swing and not protected_swing.consumed:
            if structure_direction == 'bearish' and closes[i] > protected_swing.price:
                break_event = BreakEvent(
                    index=i, event_type='CHoCH', direction='bullish',
                    broken_swing=protected_swing
                )
                protected_swing.consumed = True
                structure_direction = 'bullish'
                if swing_lows:
                    protected_swing = swing_lows[-1]
            elif structure_direction == 'bullish' and closes[i] < protected_swing.price:
                break_event = BreakEvent(
                    index=i, event_type='CHoCH', direction='bearish',
                    broken_swing=protected_swing
                )
                protected_swing.consumed = True
                structure_direction = 'bearish'
                if swing_highs:
                    protected_swing = swing_highs[-1]

        # BOS checks (only if no CHoCH triggered)
        if break_event is None:
            if structure_direction == 'bullish' and len(swing_highs) >= 1:
                sh = swing_highs[-1]
                if not sh.consumed and closes[i] > sh.price:
                    break_event = BreakEvent(
                        index=i, event_type='BOS', direction='bullish',
                        broken_swing=sh
                    )
                    sh.consumed = True
            elif structure_direction == 'bearish' and len(swing_lows) >= 1:
                sl = swing_lows[-1]
                if not sl.consumed and closes[i] < sl.price:
                    break_event = BreakEvent(
                        index=i, event_type='BOS', direction='bearish',
                        broken_swing=sl
                    )
                    sl.consumed = True

        if break_event is None:
            continue

        # Displacement quality check
        broken_price = break_event.broken_swing.price
        displacement = abs(closes[i] - broken_price)
        break_event.displacement_atr = displacement / atr[i] if atr[i] > 0 else 0

        # Body ratio of the displacement leg
        leg_start = max(break_event.broken_swing.index, i - 10)
        body_sum = 0.0
        range_sum = 0.0
        for k in range(leg_start, i + 1):
            body_sum += abs(closes[k] - opens[k])
            range_sum += (highs[k] - lows[k])
        break_event.body_ratio = body_sum / range_sum if range_sum > 0 else 0

        if break_event.displacement_atr >= MIN_DISPLACEMENT_ATR and break_event.body_ratio >= BODY_RATIO_MIN:
            break_event.quality_pass = True

            # Find OB: walk backward from i-1 to find last opposite-color candle
            ob = None
            for k in range(i - 1, max(i - 11, 0), -1):
                if break_event.direction == 'bullish':
                    # Find last bearish candle
                    if closes[k] < opens[k]:
                        ob = OrderBlock(
                            direction='bullish',
                            high=highs[k], low=lows[k],
                            formation_index=k,
                            formation_time=times[k],
                            event_type=break_event.event_type,
                            event_index=i
                        )
                        break
                else:
                    # Find last bullish candle
                    if closes[k] > opens[k]:
                        ob = OrderBlock(
                            direction='bearish',
                            high=highs[k], low=lows[k],
                            formation_index=k,
                            formation_time=times[k],
                            event_type=break_event.event_type,
                            event_index=i
                        )
                        break

            if ob is not None:
                order_blocks.append(ob)

        break_events.append(break_event)

    return order_blocks, break_events, confirmed_swings

# ─── RETEST TRACKING ─────────────────────────────────────────────────────────

def track_retests(df: pd.DataFrame, order_blocks: List[OrderBlock]):
    """Track first retest of each OB within RETEST_WINDOW candles."""
    highs = df['high'].values
    lows = df['low'].values
    times = df['dt_utc'].values
    n = len(df)

    for ob in order_blocks:
        start = ob.formation_index + 1
        end = min(start + RETEST_WINDOW, n)
        for j in range(start, end):
            if ob.direction == 'bullish':
                if lows[j] <= ob.high:
                    ob.retested = True
                    ob.retest_index = j
                    ob.retest_time = times[j]
                    break
            else:
                if highs[j] >= ob.low:
                    ob.retested = True
                    ob.retest_index = j
                    ob.retest_time = times[j]
                    break

# ─── CONTINUATION MEASUREMENT ────────────────────────────────────────────────

def measure_continuation(df: pd.DataFrame, order_blocks: List[OrderBlock], atr: np.ndarray):
    """Measure continuation after retest using ATR-based targets."""
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    for ob in order_blocks:
        if not ob.retested:
            continue
        ri = ob.retest_index
        if ri >= n - 1 or np.isnan(atr[ri]) or atr[ri] == 0:
            continue

        target_dist = TARGET_ATR_MULT * atr[ri]
        stop_dist = STOP_ATR_MULT * atr[ri]
        entry = closes[ri]

        if ob.direction == 'bullish':
            target = entry + target_dist
            stop = entry - stop_dist
        else:
            target = entry - target_dist
            stop = entry + stop_dist

        max_fav = 0.0
        max_adv = 0.0
        end = min(ri + 1 + CONTINUATION_WINDOW, n)

        for j in range(ri + 1, end):
            if ob.direction == 'bullish':
                fav = highs[j] - entry
                adv = entry - lows[j]
                if highs[j] >= target:
                    ob.continuation = True
                    ob.candles_to_resolution = j - ri
                    break
                if lows[j] <= stop:
                    ob.continuation = False
                    ob.candles_to_resolution = j - ri
                    break
            else:
                fav = entry - lows[j]
                adv = highs[j] - entry
                if lows[j] <= target:
                    ob.continuation = True
                    ob.candles_to_resolution = j - ri
                    break
                if highs[j] >= stop:
                    ob.continuation = False
                    ob.candles_to_resolution = j - ri
                    break
            max_fav = max(max_fav, fav)
            max_adv = max(max_adv, adv)

        ob.max_favorable = max_fav
        ob.max_adverse = max_adv
        if ob.continuation is None:
            ob.continuation = False
            ob.candles_to_resolution = CONTINUATION_WINDOW

# ─── SESSION CLASSIFICATION ──────────────────────────────────────────────────

def classify_session(utc_hour: int) -> str:
    if 0 <= utc_hour <= 2:
        return 'Tokyo'
    elif 7 <= utc_hour <= 9:
        return 'London'
    elif 13 <= utc_hour <= 15:
        return 'NY'
    elif 16 <= utc_hour <= 18:
        return 'Late_NY'
    else:
        return 'Off_hours'

def session_analysis(df: pd.DataFrame, order_blocks: List[OrderBlock]) -> dict:
    """Analyze OB retests by session window."""
    times = df['dt_utc'].values
    retested_obs = [ob for ob in order_blocks if ob.retested]

    sessions = {}
    for ob in retested_obs:
        hour = pd.Timestamp(times[ob.retest_index]).hour
        session = classify_session(hour)
        if session not in sessions:
            sessions[session] = {'n': 0, 'cont': 0}
        sessions[session]['n'] += 1
        if ob.continuation:
            sessions[session]['cont'] += 1

    result = {}
    for s, data in sessions.items():
        rate = data['cont'] / data['n'] * 100 if data['n'] > 0 else 0
        result[s] = {'n': data['n'], 'continuation_rate': round(rate, 1)}

    return result

# ─── DIRECTIONAL BALANCE ─────────────────────────────────────────────────────

def directional_balance(order_blocks: List[OrderBlock]) -> dict:
    retested = [ob for ob in order_blocks if ob.retested]
    bull = [ob for ob in retested if ob.direction == 'bullish']
    bear = [ob for ob in retested if ob.direction == 'bearish']
    n = len(retested)
    if n == 0:
        return {'bull_pct': 0, 'bear_pct': 0, 'bull_cont': 0, 'bear_cont': 0}

    bull_cont = sum(1 for ob in bull if ob.continuation) / len(bull) * 100 if bull else 0
    bear_cont = sum(1 for ob in bear if ob.continuation) / len(bear) * 100 if bear else 0

    return {
        'n_bull': len(bull),
        'n_bear': len(bear),
        'bull_pct': round(len(bull) / n * 100, 1),
        'bear_pct': round(len(bear) / n * 100, 1),
        'bull_cont': round(bull_cont, 1),
        'bear_cont': round(bear_cont, 1),
    }

# ─── FVG DETECTION ───────────────────────────────────────────────────────────

def detect_fvgs(df: pd.DataFrame, atr: np.ndarray) -> List[FVG]:
    """Detect Fair Value Gaps on H1."""
    highs = df['high'].values
    lows = df['low'].values
    times = df['dt_utc'].values
    n = len(df)
    fvgs = []

    for i in range(1, n - 1):
        if np.isnan(atr[i]) or atr[i] == 0:
            continue
        min_gap = FVG_MIN_GAP_ATR * atr[i]

        # Bullish FVG: candle[i+1].low - candle[i-1].high >= min_gap
        bull_gap = lows[i + 1] - highs[i - 1]
        if bull_gap >= min_gap:
            fvgs.append(FVG(
                fvg_type='bullish',
                top=lows[i + 1],
                bottom=highs[i - 1],
                gap_size=bull_gap,
                formation_index=i,
                formation_time=times[i]
            ))

        # Bearish FVG: candle[i-1].low - candle[i+1].high >= min_gap
        bear_gap = lows[i - 1] - highs[i + 1]
        if bear_gap >= min_gap:
            fvgs.append(FVG(
                fvg_type='bearish',
                top=lows[i - 1],
                bottom=highs[i + 1],
                gap_size=bear_gap,
                formation_index=i,
                formation_time=times[i]
            ))

    return fvgs

def measure_fvg_fill(df: pd.DataFrame, fvgs: List[FVG], atr: np.ndarray):
    """Measure FVG fill depth and continuation after 80%+ fill."""
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    for fvg in fvgs:
        start = fvg.formation_index + 2  # after the 3-candle pattern
        end = min(start + FVG_LOOKFORWARD, n)
        gap_height = fvg.top - fvg.bottom
        if gap_height <= 0:
            continue

        for j in range(start, end):
            if fvg.fvg_type == 'bullish':
                if lows[j] < fvg.top:
                    depth = (fvg.top - lows[j]) / gap_height
                    fvg.max_fill_depth = max(fvg.max_fill_depth, min(depth, 1.0))
                    if depth >= FVG_FILL_THRESHOLD and fvg.fill_candle_index < 0:
                        fvg.filled = True
                        fvg.fill_candle_index = j
            else:
                if highs[j] > fvg.bottom:
                    depth = (highs[j] - fvg.bottom) / gap_height
                    fvg.max_fill_depth = max(fvg.max_fill_depth, min(depth, 1.0))
                    if depth >= FVG_FILL_THRESHOLD and fvg.fill_candle_index < 0:
                        fvg.filled = True
                        fvg.fill_candle_index = j

        # Measure continuation for filled FVGs
        if fvg.filled and fvg.fill_candle_index >= 0:
            fi = fvg.fill_candle_index
            if fi >= n - 1 or np.isnan(atr[fi]) or atr[fi] == 0:
                continue
            target_dist = TARGET_ATR_MULT * atr[fi]
            stop_dist = STOP_ATR_MULT * atr[fi]
            entry = closes[fi]

            if fvg.fvg_type == 'bullish':
                target = entry + target_dist
                stop = entry - stop_dist
            else:
                target = entry - target_dist
                stop = entry + stop_dist

            cont_end = min(fi + 1 + CONTINUATION_WINDOW, n)
            for j in range(fi + 1, cont_end):
                if fvg.fvg_type == 'bullish':
                    if highs[j] >= target:
                        fvg.continuation = True
                        break
                    if lows[j] <= stop:
                        fvg.continuation = False
                        break
                else:
                    if lows[j] <= target:
                        fvg.continuation = True
                        break
                    if highs[j] >= stop:
                        fvg.continuation = False
                        break
            if fvg.continuation is None:
                fvg.continuation = False

# ─── PROCESS ONE INSTRUMENT ──────────────────────────────────────────────────

def process_instrument(symbol: str) -> Optional[dict]:
    """Full pipeline for one instrument."""
    print(f"\n{'='*60}")
    print(f"Processing {symbol}...")

    df = load_instrument(symbol, 'H1')
    if df is None:
        print(f"  No H1 data for {symbol}")
        return None
    if len(df) < MIN_H1_CANDLES:
        print(f"  Only {len(df)} candles, need {MIN_H1_CANDLES}. Skipping.")
        return None

    # Data quality
    quality = data_quality_check(df, symbol)
    print(f"  Candles: {quality['total_candles']}, Days: {quality['trading_days']}, "
          f"Range: {quality['date_range'][0][:10]} to {quality['date_range'][1][:10]}")
    if quality['gaps_gt_4h'] > 0:
        print(f"  WARNING: {quality['gaps_gt_4h']} gaps > 4h during trading hours")

    # ATR
    atr = compute_atr(df, ATR_PERIOD)

    # OB Detection
    t0 = time.time()
    order_blocks, break_events, swings = process_candles(df, atr)
    print(f"  Swings: {len(swings)}, Breaks: {len(break_events)}, OBs: {len(order_blocks)}")

    # Retests
    track_retests(df, order_blocks)
    retested = [ob for ob in order_blocks if ob.retested]
    retest_pct = len(retested) / len(order_blocks) * 100 if order_blocks else 0
    print(f"  Retested: {len(retested)}/{len(order_blocks)} ({retest_pct:.1f}%)")

    # Continuation
    measure_continuation(df, order_blocks, atr)
    cont_obs = [ob for ob in retested if ob.continuation is not None]
    cont_true = sum(1 for ob in cont_obs if ob.continuation)
    cont_rate = cont_true / len(cont_obs) * 100 if cont_obs else 0
    print(f"  Continuation: {cont_true}/{len(cont_obs)} ({cont_rate:.1f}%)")

    # Retests per month
    if quality['trading_days'] > 0:
        months = quality['trading_days'] / 21.0
        retests_per_month = len(retested) / months if months > 0 else 0
    else:
        retests_per_month = 0

    # Session analysis
    sessions = session_analysis(df, order_blocks)
    best_kz = 'N/A'
    best_kz_rate = 0.0
    for s, data in sessions.items():
        if data['n'] >= 20 and data['continuation_rate'] > best_kz_rate:
            best_kz = s
            best_kz_rate = data['continuation_rate']
    if best_kz == 'N/A':
        best_kz_rate = None

    # Directional balance
    dir_bal = directional_balance(order_blocks)

    # FVG Detection
    fvgs = detect_fvgs(df, atr)
    measure_fvg_fill(df, fvgs, atr)
    filled_fvgs = [f for f in fvgs if f.filled]
    fvg_cont = sum(1 for f in filled_fvgs if f.continuation) / len(filled_fvgs) * 100 if filled_fvgs else 0
    print(f"  FVGs: {len(fvgs)}, 80%+ filled: {len(filled_fvgs)}, Fill cont: {fvg_cont:.1f}%")

    elapsed = time.time() - t0
    print(f"  Time: {elapsed:.1f}s")

    return {
        'symbol': symbol,
        'quality': quality,
        'n_obs': len(order_blocks),
        'n_retested': len(retested),
        'retest_pct': round(retest_pct, 1),
        'cont_rate': round(cont_rate, 1),
        'retests_per_month': round(retests_per_month, 1),
        'sessions': sessions,
        'best_kz': best_kz,
        'best_kz_rate': best_kz_rate,
        'dir_balance': dir_bal,
        'n_fvgs': len(fvgs),
        'n_fvgs_filled': len(filled_fvgs),
        'fvg_cont_rate': round(fvg_cont, 1),
        'ob_details': [
            {
                'direction': ob.direction,
                'formation_time': str(ob.formation_time),
                'retested': ob.retested,
                'continuation': ob.continuation,
                'event_type': ob.event_type,
            }
            for ob in order_blocks[:50]  # first 50 for detail file
        ],
    }

# ─── CORRELATION MATRIX ─────────────────────────────────────────────────────

def compute_correlation_matrix(symbols: List[str]) -> Tuple[pd.DataFrame, dict]:
    """Compute daily return correlations from D1 data."""
    returns = {}
    for sym in symbols:
        df = load_instrument(sym, 'D1')
        if df is None:
            # Try alternate filenames for cash instruments
            for alt in [sym.replace('_cash', '.cash'), sym.replace('.cash', '_cash')]:
                df = load_instrument(alt, 'D1')
                if df is not None:
                    break
        if df is None or len(df) < 100:
            continue
        df = df.sort_values('dt_utc').reset_index(drop=True)
        df['return'] = df['close'].pct_change()
        df = df.dropna(subset=['return'])
        returns[sym] = df.set_index('dt_utc')['return']

    if len(returns) < 2:
        return pd.DataFrame(), {}

    ret_df = pd.DataFrame(returns)
    corr = ret_df.corr()

    # High correlation pairs
    high_pairs = {}
    syms = list(returns.keys())
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            c = corr.loc[syms[i], syms[j]]
            if abs(c) > CORR_HIGH_THRESHOLD:
                high_pairs[f"{syms[i]} <-> {syms[j]}"] = round(c, 3)

    return corr, high_pairs

# ─── SPREAD / SL RATIO ──────────────────────────────────────────────────────

def load_spread_data() -> dict:
    """Load spread samples from extraction summary."""
    if not EXTRACTION_SUMMARY.exists():
        return {}
    with open(EXTRACTION_SUMMARY) as f:
        data = json.load(f)
    return data.get('spread_samples', {})

def compute_spread_sl(symbol: str, median_atr: float, spread_data: dict) -> Optional[float]:
    """Compute spread as % of typical SL (0.5 * ATR)."""
    # Try exact match, then dotted variant
    candidates = [symbol, symbol.replace('_cash', '.cash')]
    for key in candidates:
        if key in spread_data:
            spread = spread_data[key].get('median_spread', 0)
            sl = 0.5 * median_atr
            if sl > 0:
                return round(spread / sl * 100, 1)
    return None

# ─── VERDICT ─────────────────────────────────────────────────────────────────

def assign_verdict(result: dict, spread_sl: Optional[float], corr_with_xau: float,
                   green_symbols: List[str], corr_matrix: pd.DataFrame) -> str:
    """Apply verdict criteria."""
    cont = result['cont_rate']
    n_ret = result['n_retested']
    rpm = result['retests_per_month']
    min_dir = min(result['dir_balance'].get('bull_pct', 50), result['dir_balance'].get('bear_pct', 50))

    # RED checks
    if cont < 60:
        return 'RED'
    if n_ret < 50:
        return 'RED'
    if spread_sl is not None and spread_sl > 40:
        return 'RED'
    # Check correlation with any GREEN instrument
    sym = result['symbol']
    for gs in green_symbols:
        if sym in corr_matrix.index and gs in corr_matrix.columns:
            if abs(corr_matrix.loc[sym, gs]) > 0.75:
                return 'RED'

    # GREEN checks
    if (cont > 65 and n_ret > 100 and rpm > 2.0
            and (spread_sl is None or spread_sl < 30) and min_dir > 25):
        # Check correlation with all GREEN
        for gs in green_symbols:
            if sym in corr_matrix.index and gs in corr_matrix.columns:
                if abs(corr_matrix.loc[sym, gs]) > 0.60:
                    return 'YELLOW'
        return 'GREEN'

    return 'YELLOW'

# ─── CALIBRATION CHECK ───────────────────────────────────────────────────────

def calibration_check(result: dict) -> Tuple[bool, List[str]]:
    """Check XAUUSD calibration. Returns (passed, issues)."""
    issues = []
    if result['n_obs'] < 600 or result['n_obs'] > 1100:
        issues.append(f"OB count {result['n_obs']} outside 600-1100 range")
    if result['retest_pct'] < 85:
        issues.append(f"Retest rate {result['retest_pct']}% below 85%")
    if result['cont_rate'] < 60 or result['cont_rate'] > 80:
        issues.append(f"Continuation rate {result['cont_rate']}% outside 60-80% range")
    if result['n_fvgs'] < 1200 or result['n_fvgs'] > 2200:
        issues.append(f"FVG count {result['n_fvgs']} outside 1200-2200 range")
    # FVG continuation check (softer)
    if result['fvg_cont_rate'] < 30 or result['fvg_cont_rate'] > 85:
        issues.append(f"FVG continuation {result['fvg_cont_rate']}% outside 30-85% range")

    bull_pct = result['dir_balance'].get('bull_pct', 50)
    bear_pct = result['dir_balance'].get('bear_pct', 50)
    if min(bull_pct, bear_pct) < 20:
        issues.append(f"Extreme directional skew: {bull_pct}/{bear_pct}")

    return len(issues) == 0, issues

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    start_time = time.time()
    print("=" * 70)
    print("MULTI-INSTRUMENT OB & FVG SCREENING ANALYSIS")
    print("=" * 70)

    # Discover instruments
    h1_files = sorted(DATA_DIR.glob("*_H1.csv"))
    symbols = []
    for f in h1_files:
        sym = f.stem.replace('_H1', '')
        symbols.append(sym)
    print(f"\nFound {len(symbols)} instruments: {', '.join(symbols)}")

    # Load spread data
    spread_data = load_spread_data()
    print(f"Spread data available for: {list(spread_data.keys())}")

    # ── STEP 1: XAUUSD CALIBRATION ──
    print("\n" + "=" * 70)
    print("PHASE 1: XAUUSD CALIBRATION (QUALITY GATE)")
    print("=" * 70)

    xau_result = process_instrument('XAUUSD')
    if xau_result is None:
        print("\nFATAL: Cannot process XAUUSD. Aborting.")
        sys.exit(1)

    passed, issues = calibration_check(xau_result)
    if not passed:
        print("\n*** CALIBRATION FAILED ***")
        for issue in issues:
            print(f"  - {issue}")
        print("\nDebug info — first 5 OBs:")
        for ob in xau_result['ob_details'][:5]:
            print(f"  {ob}")
        print("\nAborting. Fix detection before running on other instruments.")
        sys.exit(1)
    else:
        print("\n*** XAUUSD CALIBRATION PASSED ***")
        print(f"  OBs: {xau_result['n_obs']}, Retested: {xau_result['n_retested']}, "
              f"Cont: {xau_result['cont_rate']}%, FVGs: {xau_result['n_fvgs']}, "
              f"FVG Cont: {xau_result['fvg_cont_rate']}%")

    # ── STEP 2: ALL OTHER INSTRUMENTS ──
    print("\n" + "=" * 70)
    print("PHASE 2: ALL INSTRUMENTS")
    print("=" * 70)

    results = {'XAUUSD': xau_result}
    for sym in symbols:
        if sym == 'XAUUSD':
            continue
        r = process_instrument(sym)
        if r is not None:
            results[sym] = r

    # ── STEP 3: CORRELATION MATRIX ──
    print("\n" + "=" * 70)
    print("PHASE 3: CORRELATION MATRIX")
    print("=" * 70)

    all_syms = list(results.keys())
    corr_matrix, high_pairs = compute_correlation_matrix(all_syms)
    if not corr_matrix.empty:
        print("\nCorrelation with XAUUSD:")
        for sym in all_syms:
            if sym in corr_matrix.columns and 'XAUUSD' in corr_matrix.index:
                print(f"  {sym}: {corr_matrix.loc['XAUUSD', sym]:.3f}")
        if high_pairs:
            print("\nHigh correlation pairs (>0.60):")
            for pair, c in sorted(high_pairs.items(), key=lambda x: -abs(x[1])):
                print(f"  {pair}: {c}")

    # ── STEP 4: SPREAD / SL ──
    print("\n" + "=" * 70)
    print("PHASE 4: SPREAD / SL RATIOS")
    print("=" * 70)

    spread_sl = {}
    for sym, r in results.items():
        df = load_instrument(sym, 'H1')
        if df is not None:
            atr = compute_atr(df, ATR_PERIOD)
            median_atr = np.nanmedian(atr[ATR_PERIOD:])
            ss = compute_spread_sl(sym, median_atr, spread_data)
            spread_sl[sym] = ss
            status = f"{ss:.1f}%" if ss is not None else "N/A"
            print(f"  {sym}: Spread/SL = {status} (median ATR={median_atr:.5f})")

    # ── STEP 5: VERDICTS ──
    print("\n" + "=" * 70)
    print("PHASE 5: SCREENING TABLE")
    print("=" * 70)

    # Assign verdicts (GREEN instruments processed first for correlation check)
    verdicts = {'XAUUSD': 'CALIBRATION'}
    green_symbols = ['XAUUSD']

    # Sort by continuation rate descending for verdict assignment
    sorted_syms = sorted(
        [s for s in results if s != 'XAUUSD'],
        key=lambda s: results[s]['cont_rate'],
        reverse=True
    )

    for sym in sorted_syms:
        r = results[sym]
        corr_xau = 0.0
        if not corr_matrix.empty and sym in corr_matrix.columns and 'XAUUSD' in corr_matrix.index:
            corr_xau = corr_matrix.loc['XAUUSD', sym]
        v = assign_verdict(r, spread_sl.get(sym), corr_xau, green_symbols, corr_matrix)
        verdicts[sym] = v
        if v == 'GREEN':
            green_symbols.append(sym)

    # Print screening table
    header = (f"{'Instrument':<14} {'OB Cont%':>8} {'n_OBs':>6} {'n_Ret':>6} {'Ret/Mo':>7} "
              f"{'Bull/Bear':>10} {'Best KZ':<10} {'KZ Cont%':>8} {'FVG Cont':>8} "
              f"{'Spr/SL%':>8} {'Corr XAU':>9} {'Verdict':<12}")
    print(f"\n{header}")
    print("-" * len(header))

    # Print XAUUSD first, then sorted by verdict priority
    verdict_order = {'CALIBRATION': 0, 'GREEN': 1, 'YELLOW': 2, 'RED': 3}
    ordered = ['XAUUSD'] + sorted(
        [s for s in results if s != 'XAUUSD'],
        key=lambda s: (verdict_order.get(verdicts.get(s, 'RED'), 4), -results[s]['cont_rate'])
    )

    table_rows = []
    for sym in ordered:
        r = results[sym]
        db = r['dir_balance']
        kz_rate = f"{r['best_kz_rate']:.1f}%" if r['best_kz_rate'] is not None else "N/A"
        ssl = f"{spread_sl[sym]:.1f}%" if spread_sl.get(sym) is not None else "N/A"
        corr_xau = 0.0
        if not corr_matrix.empty and sym in corr_matrix.columns and 'XAUUSD' in corr_matrix.index:
            corr_xau = corr_matrix.loc['XAUUSD', sym]

        row = (f"{sym:<14} {r['cont_rate']:>7.1f}% {r['n_obs']:>6} {r['n_retested']:>6} "
               f"{r['retests_per_month']:>6.1f} {db['bull_pct']:>4.0f}/{db['bear_pct']:<4.0f} "
               f"{r['best_kz']:<10} {kz_rate:>8} {r['fvg_cont_rate']:>7.1f}% "
               f"{ssl:>8} {corr_xau:>8.3f}  {verdicts[sym]:<12}")
        print(row)

        table_rows.append({
            'symbol': sym,
            'ob_cont_pct': r['cont_rate'],
            'n_obs': r['n_obs'],
            'n_retested': r['n_retested'],
            'retests_per_month': r['retests_per_month'],
            'bull_pct': db['bull_pct'],
            'bear_pct': db['bear_pct'],
            'best_kz': r['best_kz'],
            'kz_cont_pct': r['best_kz_rate'],
            'fvg_cont_pct': r['fvg_cont_rate'],
            'spread_sl_pct': spread_sl.get(sym),
            'corr_with_xau': round(corr_xau, 3),
            'verdict': verdicts[sym],
        })

    # ── SAVE OUTPUTS ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Screening table JSON
    with open(OUTPUT_DIR / 'screening_table.json', 'w') as f:
        json.dump(table_rows, f, indent=2, default=str)

    # Correlation matrix
    if not corr_matrix.empty:
        corr_matrix.to_json(OUTPUT_DIR / 'correlation_matrix.json')

    # Per-instrument details
    for sym, r in results.items():
        with open(OUTPUT_DIR / f'{sym}_detail.json', 'w') as f:
            json.dump(r, f, indent=2, default=str)

    # Summary markdown
    summary_lines = ["# Multi-Instrument OB Screening Results\n"]
    summary_lines.append(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
    summary_lines.append(f"**Instruments analyzed:** {len(results)}\n")

    green_list = [s for s, v in verdicts.items() if v == 'GREEN']
    yellow_list = [s for s, v in verdicts.items() if v == 'YELLOW']
    red_list = [s for s, v in verdicts.items() if v == 'RED']

    summary_lines.append(f"\n## Verdicts\n")
    summary_lines.append(f"- **GREEN** ({len(green_list)}): {', '.join(green_list) if green_list else 'None'}")
    summary_lines.append(f"- **YELLOW** ({len(yellow_list)}): {', '.join(yellow_list) if yellow_list else 'None'}")
    summary_lines.append(f"- **RED** ({len(red_list)}): {', '.join(red_list) if red_list else 'None'}")

    if high_pairs:
        summary_lines.append(f"\n## High Correlation Pairs (>0.60)\n")
        for pair, c in sorted(high_pairs.items(), key=lambda x: -abs(x[1])):
            summary_lines.append(f"- {pair}: {c}")

    summary_lines.append(f"\n## Recommended Batch Test Order\n")
    for i, sym in enumerate(green_list, 1):
        r = results[sym]
        summary_lines.append(f"{i}. **{sym}** — {r['cont_rate']}% cont, {r['retests_per_month']} ret/mo, "
                           f"spread/SL={spread_sl.get(sym, 'N/A')}%")

    with open(OUTPUT_DIR / 'screening_summary.md', 'w') as f:
        f.write('\n'.join(summary_lines))

    # ── VALIDATION CHECKLIST ──
    print("\n" + "=" * 70)
    print("VALIDATION CHECKLIST")
    print("=" * 70)

    checks = []
    # 1. Gold calibration
    checks.append(("Gold calibration passed", passed))
    # 2. No instrument > 2x XAUUSD OBs
    xau_obs = xau_result['n_obs']
    over_2x = [s for s, r in results.items() if s != 'XAUUSD' and r['n_obs'] > 2 * xau_obs]
    checks.append(("No instrument > 2x XAUUSD OBs", len(over_2x) == 0))
    if over_2x:
        print(f"  WARNING: {over_2x} have >2x XAUUSD OB count")
    # 3. Continuation rates not all identical
    rates = [r['cont_rate'] for r in results.values()]
    checks.append(("Continuation rates vary (>2pp spread)", max(rates) - min(rates) > 2))
    # 4. At least one RED
    checks.append(("At least one RED verdict", any(v == 'RED' for v in verdicts.values())))
    # 5. Correlation diagonal
    if not corr_matrix.empty:
        diag_ok = all(abs(corr_matrix.iloc[i, i] - 1.0) < 0.001 for i in range(len(corr_matrix)))
        checks.append(("Correlation diagonal = 1.00", diag_ok))
        # 6. Symmetric
        sym_ok = np.allclose(corr_matrix.values, corr_matrix.values.T, atol=0.001)
        checks.append(("Correlation matrix symmetric", sym_ok))
    # 7. Spread data coverage
    spread_coverage = sum(1 for v in spread_sl.values() if v is not None) / len(spread_sl) * 100
    checks.append((f"Spread data >50% ({spread_coverage:.0f}%)", spread_coverage > 50))

    for check, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {check}")

    elapsed = time.time() - start_time
    print(f"\n  Total compute time: {elapsed:.1f}s")
    checks.append((f"Compute time < 1800s ({elapsed:.0f}s)", elapsed < 1800))

    # Final count
    print(f"\n{'='*70}")
    print(f"GREEN: {len(green_list)} | YELLOW: {len(yellow_list)} | RED: {len(red_list)}")
    print(f"Recommended batch test investments: {len(green_list)} × $25 = ${len(green_list) * 25}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
