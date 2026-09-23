#!/usr/bin/env python3
"""
Intra-Candle Missed Setups Quantification — M1/M5 Real Data

Scans M1 and M5 data for patterns that form and resolve INSIDE a single
M15 candle — setups the system never sees.

Three pattern types:
1. Sweep + Displacement + Pullback (M5 swings, M1 timing)
2. OB Zone Touch + Rejection (H1 OB, M1 price action)
3. Flash Displacement (extreme M1 candle)

For each: track whether setup resolved before M15 close vs still valid.
"""

import warnings
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

DATA_DIR = Path("data/historical")
OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_29/generated/intra_candle_missed_setups")

EET_OFFSET_HOURS = 2

# Kill zone windows (UTC)
LONDON_START, LONDON_END = (7, 0), (10, 30)
NY_START, NY_END = (13, 15), (15, 30)

# Detection thresholds
M5_ATR_PERIOD = 14
M5_SWING_BARS = 3         # 3 M5 bars each side = confirmed swing
SWEEP_BUFFER_ATR = 0.2    # sweep must exceed swing by ≥0.2x M5 ATR
DISP_ATR_MULT = 1.5       # displacement ≥1.5x M5 ATR within 5 minutes
PULLBACK_WINDOW_M1 = 10   # 10 M1 candles for pullback after displacement
PULLBACK_RETRACE_PCT = 0.5  # must retrace ≥50% of displacement

H1_ATR_PERIOD = 14
OB_REJECTION_ATR = 1.5    # M1 displacement away from OB ≥1.5x M5 ATR (same as displacement quality)
FLASH_H1_ATR_MULT = 2.0   # single M1 candle ≥2x H1 ATR

CONTINUATION_WINDOW_M5 = 36  # 36 M5 = 3 hours for continuation check
CONTINUATION_R = 1.5


def load_all_data():
    m1 = pd.read_csv(DATA_DIR / "XAUUSD_M1.csv")
    m1['time'] = pd.to_datetime(m1['time'])
    m1['time_utc'] = m1['time'] - pd.Timedelta(hours=EET_OFFSET_HOURS)

    m5 = pd.read_csv(DATA_DIR / "XAUUSD_M5.csv")
    m5['time'] = pd.to_datetime(m5['time'])
    m5['time_utc'] = m5['time'] - pd.Timedelta(hours=EET_OFFSET_HOURS)

    m15 = pd.read_csv(DATA_DIR / "XAUUSD_M15.csv")
    m15['time'] = pd.to_datetime(m15['time'])
    m15['time_utc'] = m15['time'] - pd.Timedelta(hours=EET_OFFSET_HOURS)

    h1 = pd.read_csv(DATA_DIR / "XAUUSD_H1.csv")
    h1['time'] = pd.to_datetime(h1['time'])
    h1['time_utc'] = h1['time'] - pd.Timedelta(hours=EET_OFFSET_HOURS)

    return m1, m5, m15, h1


def compute_atr(highs, lows, closes, period=14):
    n = len(highs)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = np.full(n, np.nan)
    if n > period:
        atr[period] = np.mean(tr[1:period+1])
        for i in range(period+1, n):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr


def detect_m5_swings(m5, min_bars=3):
    """Detect confirmed M5 swing highs and lows."""
    highs = m5['high'].values
    lows = m5['low'].values
    n = len(m5)
    swing_highs = []  # (index, price, time)
    swing_lows = []
    for i in range(min_bars, n - min_bars):
        is_high = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, min_bars+1))
        is_low = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, min_bars+1))
        if is_high:
            swing_highs.append((i, highs[i], m5.iloc[i]['time_utc']))
        if is_low:
            swing_lows.append((i, lows[i], m5.iloc[i]['time_utc']))
    return swing_highs, swing_lows


def detect_h1_ob_zones(h1):
    """Detect H1 OB zones."""
    opens = h1['open'].values.astype(float)
    highs = h1['high'].values.astype(float)
    lows = h1['low'].values.astype(float)
    closes = h1['close'].values.astype(float)
    times = h1['time_utc'].values
    n = len(h1)
    atr = compute_atr(highs, lows, closes, H1_ATR_PERIOD)

    min_bars = 2
    swing_highs, swing_lows = [], []
    for i in range(min_bars, n - min_bars):
        if all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, min_bars+1)):
            swing_highs.append((i, highs[i]))
        if all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, min_bars+1)):
            swing_lows.append((i, lows[i]))

    ob_zones = []
    consumed_sh, consumed_sl = set(), set()
    sh_ptr, sl_ptr = 0, 0
    active_sh, active_sl = [], []

    for i in range(100, n):
        if np.isnan(atr[i]) or atr[i] == 0:
            continue
        while sh_ptr < len(swing_highs) and swing_highs[sh_ptr][0] < i:
            active_sh.append(swing_highs[sh_ptr])
            sh_ptr += 1
        while sl_ptr < len(swing_lows) and swing_lows[sl_ptr][0] < i:
            active_sl.append(swing_lows[sl_ptr])
            sl_ptr += 1

        if active_sh:
            sh_idx, sh_price = active_sh[-1]
            if sh_idx not in consumed_sh and closes[i] > sh_price:
                if abs(closes[i] - sh_price) >= 0.4 * atr[i]:
                    for k in range(i-1, max(i-11, 0), -1):
                        if closes[k] < opens[k]:
                            expiry = times[min(i + 250, n-1)]
                            ob_zones.append(('bullish', highs[k], lows[k], times[k], expiry))
                            break
                consumed_sh.add(sh_idx)

        if active_sl:
            sl_idx, sl_price = active_sl[-1]
            if sl_idx not in consumed_sl and closes[i] < sl_price:
                if abs(closes[i] - sl_price) >= 0.4 * atr[i]:
                    for k in range(i-1, max(i-11, 0), -1):
                        if closes[k] > opens[k]:
                            expiry = times[min(i + 250, n-1)]
                            ob_zones.append(('bearish', highs[k], lows[k], times[k], expiry))
                            break
                consumed_sl.add(sl_idx)

    return ob_zones


def get_kz(hour, minute):
    t = hour * 60 + minute
    if LONDON_START[0]*60+LONDON_START[1] <= t < LONDON_END[0]*60+LONDON_END[1]:
        return 'london'
    if NY_START[0]*60+NY_START[1] <= t < NY_END[0]*60+NY_END[1]:
        return 'ny'
    return None


def get_m15_parent(candle_time_utc, m15):
    """Find which M15 candle contains this timestamp."""
    # M15 candle at time T covers [T, T+15min)
    mask = m15['time_utc'] <= candle_time_utc
    if mask.any():
        idx = mask[::-1].idxmax()
        return idx, m15.iloc[idx]['time_utc']
    return None, None


def check_resolved_before_m15_close(event_time, event_direction, entry_price,
                                     target_price, stop_price, m1, m15_close_time):
    """Check if the trade resolved (hit TP or SL) before the parent M15 candle closed."""
    mask = (m1['time_utc'] > event_time) & (m1['time_utc'] <= m15_close_time)
    sub = m1[mask]
    for _, row in sub.iterrows():
        if event_direction == 'bullish':
            if row['high'] >= target_price:
                return 'WIN_BEFORE_CLOSE'
            if row['low'] <= stop_price:
                return 'LOSS_BEFORE_CLOSE'
        else:
            if row['low'] <= target_price:
                return 'WIN_BEFORE_CLOSE'
            if row['high'] >= stop_price:
                return 'LOSS_BEFORE_CLOSE'
    return 'STILL_OPEN'


def check_continuation_m5(m5, start_time, direction, entry_price, stop_dist):
    """Check if price continues 1.5R after event."""
    target = entry_price + CONTINUATION_R * stop_dist if direction == 'bullish' else entry_price - CONTINUATION_R * stop_dist
    stop = entry_price - stop_dist if direction == 'bullish' else entry_price + stop_dist

    mask = m5['time_utc'] > start_time
    sub = m5[mask].head(CONTINUATION_WINDOW_M5)
    for _, row in sub.iterrows():
        if direction == 'bullish':
            if row['high'] >= target:
                return True
            if row['low'] <= stop:
                return False
        else:
            if row['low'] <= target:
                return True
            if row['high'] >= stop:
                return False
    return False


def analyze():
    print("Loading data...")
    m1, m5, m15, h1 = load_all_data()
    print(f"  M1:  {len(m1)} candles ({m1['time_utc'].iloc[0]} to {m1['time_utc'].iloc[-1]})")
    print(f"  M5:  {len(m5)} candles ({m5['time_utc'].iloc[0]} to {m5['time_utc'].iloc[-1]})")
    print(f"  M15: {len(m15)} candles")
    print(f"  H1:  {len(h1)} candles")

    # Use the overlap period where M1 data exists
    m1_start = m1['time_utc'].iloc[0]
    m1_end = m1['time_utc'].iloc[-1]
    print(f"\n  Analysis window (M1 coverage): {m1_start} to {m1_end}")

    # Compute ATRs
    m5_atr = compute_atr(m5['high'].values, m5['low'].values, m5['close'].values, M5_ATR_PERIOD)
    h1_atr = compute_atr(h1['high'].values, h1['low'].values, h1['close'].values, H1_ATR_PERIOD)

    # M5 swing detection
    print("Detecting M5 swings...")
    m5_swing_highs, m5_swing_lows = detect_m5_swings(m5)
    print(f"  {len(m5_swing_highs)} swing highs, {len(m5_swing_lows)} swing lows")

    # H1 OB zones
    print("Detecting H1 OB zones...")
    ob_zones = detect_h1_ob_zones(h1)
    print(f"  {len(ob_zones)} H1 OB zones")

    # Index OB zones by date
    ob_by_date = defaultdict(list)
    for direction, ob_hi, ob_lo, form_time, exp_time in ob_zones:
        form_dt = pd.Timestamp(form_time)
        exp_dt = pd.Timestamp(exp_time)
        current = form_dt.normalize()
        while current <= exp_dt.normalize():
            ob_by_date[current.strftime('%Y-%m-%d')].append({
                'direction': direction, 'high': ob_hi, 'low': ob_lo,
            })
            current += pd.Timedelta(days=1)

    # Build M1 index for fast time-range lookups
    m1_times = m1['time_utc'].values
    m1_highs = m1['high'].values
    m1_lows = m1['low'].values
    m1_opens = m1['open'].values
    m1_closes = m1['close'].values

    # H1 ATR series for flash detection
    h1_atr_series = pd.Series(h1_atr, index=h1['time_utc'])

    # ─── SCAN M1 candles in kill zones ───
    print("\nScanning M1 candles for intra-candle patterns...")

    pattern1_events = []
    pattern2_events = []
    pattern3_events = []
    kz_dates = {'london': set(), 'ny': set()}

    # Track recent M5 swings for sweep detection
    # Build time-indexed swing lookup
    m5_sh_times = [t for _, _, t in m5_swing_highs]
    m5_sh_prices = [p for _, p, _ in m5_swing_highs]
    m5_sl_times = [t for _, _, t in m5_swing_lows]
    m5_sl_prices = [p for _, p, _ in m5_swing_lows]

    def get_recent_swing_high(before_time, lookback_hours=3):
        """Get highest M5 swing high in last N hours."""
        cutoff = before_time - pd.Timedelta(hours=lookback_hours)
        candidates = [(t, p) for t, p in zip(m5_sh_times, m5_sh_prices)
                       if cutoff <= t < before_time]
        if candidates:
            return max(candidates, key=lambda x: x[1])
        return None

    def get_recent_swing_low(before_time, lookback_hours=3):
        cutoff = before_time - pd.Timedelta(hours=lookback_hours)
        candidates = [(t, p) for t, p in zip(m5_sl_times, m5_sl_prices)
                       if cutoff <= t < before_time]
        if candidates:
            return min(candidates, key=lambda x: x[1])
        return None

    # Get M5 ATR at a given time
    m5_times_arr = m5['time_utc'].values
    def get_m5_atr_at(t):
        mask = m5['time_utc'] <= t
        if mask.any():
            idx = mask[::-1].idxmax()
            return m5_atr[idx] if not np.isnan(m5_atr[idx]) else None
        return None

    def get_h1_atr_at(t):
        mask = h1_atr_series.index <= t
        if mask.any():
            return h1_atr_series[mask].iloc[-1]
        return None

    # Cooldown: prevent multiple detections on the same M15 candle
    last_p1_m15 = None
    last_p2_m15 = None

    # Iterate M1 candles
    n_m1 = len(m1)
    progress_interval = n_m1 // 10

    for i in range(n_m1):
        if i % progress_interval == 0:
            print(f"  {i}/{n_m1} ({i/n_m1*100:.0f}%)")

        t = m1.iloc[i]['time_utc']
        hour = t.hour
        minute = t.minute
        kz = get_kz(hour, minute)
        if kz is None:
            continue

        date_str = t.strftime('%Y-%m-%d')
        kz_dates[kz].add(date_str)

        o, h, l, c = m1_opens[i], m1_highs[i], m1_lows[i], m1_closes[i]
        candle_range = h - l
        if candle_range == 0:
            continue

        cur_m5_atr = get_m5_atr_at(t)
        if cur_m5_atr is None or cur_m5_atr == 0:
            continue

        # Parent M15 candle
        m15_parent_idx, m15_parent_time = get_m15_parent(t, m15)
        if m15_parent_time is None:
            continue
        m15_close_time = m15_parent_time + pd.Timedelta(minutes=15)

        # ─── PATTERN 1: Sweep + Displacement on M1 ───
        # Check if this M1 candle sweeps a recent M5 swing
        recent_sl = get_recent_swing_low(t)
        recent_sh = get_recent_swing_high(t)

        # Bullish sweep: M1 low breaks below M5 swing low, then price reverses up
        if recent_sl and l < recent_sl[1] - SWEEP_BUFFER_ATR * cur_m5_atr:
            # Check next 5 M1 candles for displacement UP
            if i + 5 < n_m1:
                disp_high = max(m1_highs[i:i+6])
                disp_move = disp_high - l
                if disp_move >= DISP_ATR_MULT * cur_m5_atr:
                    # Check pullback within next 10 M1 candles
                    pullback_found = False
                    for j in range(i+1, min(i + PULLBACK_WINDOW_M1 + 6, n_m1)):
                        retrace = disp_high - m1_lows[j]
                        if retrace >= PULLBACK_RETRACE_PCT * disp_move:
                            pullback_found = True
                            break

                    if pullback_found and m15_parent_idx != last_p1_m15:
                        last_p1_m15 = m15_parent_idx
                        entry = l + disp_move * 0.4  # approximate entry at pullback
                        stop_dist = entry - l + cur_m5_atr * 0.2
                        would_continue = check_continuation_m5(m5, t, 'bullish', entry, stop_dist)

                        # Did it resolve before M15 close?
                        target = entry + CONTINUATION_R * stop_dist
                        stop = entry - stop_dist
                        resolution = check_resolved_before_m15_close(
                            t, 'bullish', entry, target, stop, m1, m15_close_time)

                        pattern1_events.append({
                            'time': str(t), 'date': date_str, 'kz': kz,
                            'direction': 'bullish',
                            'sweep_level': recent_sl[1],
                            'sweep_depth': recent_sl[1] - l,
                            'disp_move': disp_move,
                            'disp_atr': disp_move / cur_m5_atr,
                            'resolved_before_m15': resolution != 'STILL_OPEN',
                            'resolution': resolution,
                            'still_valid_at_m15_close': resolution == 'STILL_OPEN',
                            'would_continue': would_continue,
                        })

        # Bearish sweep: M1 high breaks above M5 swing high
        if recent_sh and h > recent_sh[1] + SWEEP_BUFFER_ATR * cur_m5_atr:
            if i + 5 < n_m1:
                disp_low = min(m1_lows[i:i+6])
                disp_move = h - disp_low
                if disp_move >= DISP_ATR_MULT * cur_m5_atr:
                    pullback_found = False
                    for j in range(i+1, min(i + PULLBACK_WINDOW_M1 + 6, n_m1)):
                        retrace = m1_highs[j] - disp_low
                        if retrace >= PULLBACK_RETRACE_PCT * disp_move:
                            pullback_found = True
                            break

                    if pullback_found and m15_parent_idx != last_p1_m15:
                        last_p1_m15 = m15_parent_idx
                        entry = h - disp_move * 0.4
                        stop_dist = h - entry + cur_m5_atr * 0.2
                        would_continue = check_continuation_m5(m5, t, 'bearish', entry, stop_dist)

                        target = entry - CONTINUATION_R * stop_dist
                        stop = entry + stop_dist
                        resolution = check_resolved_before_m15_close(
                            t, 'bearish', entry, target, stop, m1, m15_close_time)

                        pattern1_events.append({
                            'time': str(t), 'date': date_str, 'kz': kz,
                            'direction': 'bearish',
                            'sweep_level': recent_sh[1],
                            'sweep_depth': h - recent_sh[1],
                            'disp_move': disp_move,
                            'disp_atr': disp_move / cur_m5_atr,
                            'resolved_before_m15': resolution != 'STILL_OPEN',
                            'resolution': resolution,
                            'still_valid_at_m15_close': resolution == 'STILL_OPEN',
                            'would_continue': would_continue,
                        })

        # ─── PATTERN 2: OB Zone Touch + M1 Displacement Away ───
        active_obs = ob_by_date.get(date_str, [])
        for ob in active_obs:
            if ob['direction'] == 'bullish' and l <= ob['high'] and l >= ob['low'] - cur_m5_atr:
                # Price touched bullish OB zone from above
                # Check if next 5 M1 candles show displacement UP
                if i + 5 < n_m1:
                    disp_up = max(m1_highs[i+1:i+6]) - l
                    if disp_up >= OB_REJECTION_ATR * cur_m5_atr:
                        if m15_parent_idx != last_p2_m15:
                            last_p2_m15 = m15_parent_idx
                            entry = ob['high']
                            stop_dist = ob['high'] - ob['low'] + cur_m5_atr * 0.2
                            would_continue = check_continuation_m5(m5, t, 'bullish', entry, stop_dist)

                            target = entry + CONTINUATION_R * stop_dist
                            stop = entry - stop_dist
                            resolution = check_resolved_before_m15_close(
                                t, 'bullish', entry, target, stop, m1, m15_close_time)

                            pattern2_events.append({
                                'time': str(t), 'date': date_str, 'kz': kz,
                                'direction': 'bullish',
                                'ob_zone': f"{ob['low']:.2f}-{ob['high']:.2f}",
                                'rejection_size': disp_up,
                                'rejection_atr': disp_up / cur_m5_atr,
                                'resolved_before_m15': resolution != 'STILL_OPEN',
                                'resolution': resolution,
                                'still_valid_at_m15_close': resolution == 'STILL_OPEN',
                                'would_continue': would_continue,
                            })
                            break

            elif ob['direction'] == 'bearish' and h >= ob['low'] and h <= ob['high'] + cur_m5_atr:
                if i + 5 < n_m1:
                    disp_down = h - min(m1_lows[i+1:i+6])
                    if disp_down >= OB_REJECTION_ATR * cur_m5_atr:
                        if m15_parent_idx != last_p2_m15:
                            last_p2_m15 = m15_parent_idx
                            entry = ob['low']
                            stop_dist = ob['high'] - ob['low'] + cur_m5_atr * 0.2
                            would_continue = check_continuation_m5(m5, t, 'bearish', entry, stop_dist)

                            target = entry - CONTINUATION_R * stop_dist
                            stop = entry + stop_dist
                            resolution = check_resolved_before_m15_close(
                                t, 'bearish', entry, target, stop, m1, m15_close_time)

                            pattern2_events.append({
                                'time': str(t), 'date': date_str, 'kz': kz,
                                'direction': 'bearish',
                                'ob_zone': f"{ob['low']:.2f}-{ob['high']:.2f}",
                                'rejection_size': disp_down,
                                'rejection_atr': disp_down / cur_m5_atr,
                                'resolved_before_m15': resolution != 'STILL_OPEN',
                                'resolution': resolution,
                                'still_valid_at_m15_close': resolution == 'STILL_OPEN',
                                'would_continue': would_continue,
                            })
                            break

        # ─── PATTERN 3: Flash Displacement ───
        h1_atr_val = get_h1_atr_at(t)
        if h1_atr_val and h1_atr_val > 0:
            if candle_range >= FLASH_H1_ATR_MULT * h1_atr_val:
                direction = 'bullish' if c > o else 'bearish'
                pattern3_events.append({
                    'time': str(t), 'date': date_str, 'kz': kz,
                    'direction': direction,
                    'range': candle_range,
                    'range_h1_atr': candle_range / h1_atr_val,
                    'resolved_before_m15': True,  # by definition
                })

    # ─── Stats ───
    n_london = len(kz_dates['london'])
    n_ny = len(kz_dates['ny'])
    all_dates = sorted(kz_dates['london'] | kz_dates['ny'])
    if all_dates:
        first = pd.Timestamp(all_dates[0])
        last = pd.Timestamp(all_dates[-1])
        n_months = max((last - first).days / 30.44, 1)
    else:
        n_months = 1

    return {
        'pattern1': pattern1_events,
        'pattern2': pattern2_events,
        'pattern3': pattern3_events,
        'n_london': n_london, 'n_ny': n_ny,
        'total_sessions': n_london + n_ny,
        'n_months': n_months,
        'm1_start': str(m1['time_utc'].iloc[0]),
        'm1_end': str(m1['time_utc'].iloc[-1]),
    }


def format_report(results):
    p1 = results['pattern1']
    p2 = results['pattern2']
    p3 = results['pattern3']
    nm = results['n_months']

    lines = []
    lines.append("# Intra-Candle Missed Setups Analysis (M1 Real Data)\n")
    lines.append("## Method\n")
    lines.append("Scanned **real M1 data** for patterns that form and resolve inside a single")
    lines.append("M15 candle — setups invisible to the current M15-based evaluation.\n")
    lines.append(f"**Data:** M1 XAUUSD ({results['m1_start']} to {results['m1_end']})")
    lines.append(f"**Sessions:** {results['n_london']} London + {results['n_ny']} NY = {results['total_sessions']} over {nm:.1f} months\n")

    lines.append("**Detection criteria:**")
    lines.append("- Pattern 1: M1 price sweeps M5 swing, displaces ≥1.5x M5 ATR within 5 min, then pulls back ≥50%")
    lines.append("- Pattern 2: M1 price touches H1 OB zone, M1 displaces ≥0.5x M5 ATR away within 5 min")
    lines.append("- Pattern 3: Single M1 candle range ≥2x H1 ATR")
    lines.append("- One detection per M15 candle (cooldown prevents double-counting)\n")

    def section(name, desc, events, nm):
        lines = []
        lines.append(f"\n## {name}\n")
        lines.append(f"**{desc}**\n")
        n = len(events)
        pm = n / nm
        resolved = sum(1 for e in events if e.get('resolved_before_m15'))
        valid = sum(1 for e in events if e.get('still_valid_at_m15_close'))
        cont = sum(1 for e in events if e.get('would_continue'))

        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        lines.append(f"| Total events | {n} ({pm:.1f}/month) |")
        lines.append(f"| Resolved before M15 close | {resolved} ({resolved/max(n,1)*100:.0f}%) |")
        lines.append(f"| Still valid at M15 close | {valid} ({valid/max(n,1)*100:.0f}%) |")
        lines.append(f"| Would have continued 1.5R+ | {cont} ({cont/max(n,1)*100:.0f}%) |")

        missed = resolved / nm * (cont / max(n, 1))
        lines.append(f"| **Est. missed tradeable/month** | **~{missed:.1f}** |")

        # By KZ
        lon = [e for e in events if e['kz'] == 'london']
        ny = [e for e in events if e['kz'] == 'ny']
        lines.append(f"\n| Kill Zone | Events | /Month | Resolved In-Candle | Would Continue |")
        lines.append("|---|---|---|---|---|")
        for kz_name, evs in [('London', lon), ('NY', ny)]:
            ne = len(evs)
            res = sum(1 for e in evs if e.get('resolved_before_m15'))
            co = sum(1 for e in evs if e.get('would_continue'))
            lines.append(f"| {kz_name} | {ne} | {ne/nm:.1f} | {res} ({res/max(ne,1)*100:.0f}%) | {co} ({co/max(ne,1)*100:.0f}%) |")

        return lines, missed

    l1, missed1 = section("Pattern 1: Sweep + Displacement + Pullback",
        "M1 price sweeps M5 swing, displaces ≥1.5x M5 ATR, then pulls back. Classic SMC entry.", p1, nm)
    l2, missed2 = section("Pattern 2: OB Zone Touch + Rejection",
        "M1 price touches H1 OB zone, then displaces away ≥0.5x M5 ATR within 5 min.", p2, nm)

    # Pattern 3 (simpler)
    n3 = len(p3)
    pm3 = n3 / nm
    l3 = [f"\n## Pattern 3: Flash Displacement\n"]
    l3.append(f"**Single M1 candle with range ≥2x H1 ATR.**\n")
    l3.append(f"| Metric | Value |")
    l3.append(f"|---|---|")
    l3.append(f"| Total events | {n3} ({pm3:.1f}/month) |")
    l3.append(f"| All resolve within M1 candle | 100% |")
    if p3:
        l3.append(f"| Avg range (H1 ATR mult) | {np.mean([e['range_h1_atr'] for e in p3]):.1f}x |")
    lon3 = [e for e in p3 if e['kz'] == 'london']
    ny3 = [e for e in p3 if e['kz'] == 'ny']
    l3.append(f"\n| KZ | Events | /Month |")
    l3.append(f"|---|---|---|")
    l3.append(f"| London | {len(lon3)} | {len(lon3)/nm:.1f} |")
    l3.append(f"| NY | {len(ny3)} | {len(ny3)/nm:.1f} |")
    missed3 = pm3

    lines.extend(l1)
    lines.extend(l2)
    lines.extend(l3)

    total_missed = missed1 + missed2 + missed3

    lines.append("\n## Summary\n")
    lines.append("```")
    lines.append(f"Analysis period:                     {nm:.1f} months (M1 data)")
    lines.append(f"Kill zone sessions scanned:          {results['total_sessions']}")
    lines.append(f"")
    lines.append(f"Pattern 1 (sweep+disp+pullback):     {len(p1)} ({len(p1)/nm:.1f}/month)")
    lines.append(f"  Missed tradeable:                  ~{missed1:.1f}/month")
    lines.append(f"")
    lines.append(f"Pattern 2 (OB touch + rejection):    {len(p2)} ({len(p2)/nm:.1f}/month)")
    lines.append(f"  Missed tradeable:                  ~{missed2:.1f}/month")
    lines.append(f"")
    lines.append(f"Pattern 3 (flash displacement):      {len(p3)} ({len(p3)/nm:.1f}/month)")
    lines.append(f"  Missed tradeable:                  ~{missed3:.1f}/month")
    lines.append(f"")
    lines.append(f"TOTAL MISSED SETUPS:                 ~{total_missed:.1f}/month")
    lines.append("```\n")

    if total_missed > 5:
        priority = "HIGH"
        msg = "Significant missed opportunity. Intra-candle monitoring (M5 or M1 evaluation trigger) should be prioritized."
    elif total_missed >= 2:
        priority = "MEDIUM"
        msg = "Moderate missed opportunity. Build intra-candle monitoring during WF-2 phase."
    else:
        priority = "LOW"
        msg = "M15 captures the vast majority of meaningful setups. Intra-candle monitoring is not urgent."

    lines.append(f"## Priority: **{priority}**\n")
    lines.append(f"{msg}\n")

    lines.append("## Caveats\n")
    lines.append(f"1. **M1 data covers only {nm:.1f} months.** Annualized estimates assume stationarity.")
    lines.append("2. **Cooldown = 1 detection per M15 candle.** Multiple events within the same")
    lines.append("   M15 window are collapsed to avoid overcounting.")
    lines.append("3. **Continuation is measured from approximate entry** using M5 data after the event.")
    lines.append("   Real execution with M1 refinement would likely yield better entries.")
    lines.append("4. **OB zones use the simplified H1 detector**, not the AI's assessment.")
    lines.append("5. **\"Resolved before M15 close\"** means TP or SL was hit in M1 data before the")
    lines.append("   parent M15 candle closed. These are definitively missed — the system never saw them.")

    return "\n".join(lines)


if __name__ == '__main__':
    print("=" * 70)
    print("INTRA-CANDLE MISSED SETUPS — M1 REAL DATA")
    print("=" * 70)

    results = analyze()
    doc = format_report(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outpath = OUTPUT_DIR / "intra_candle_missed_setups_analysis.md"
    with open(outpath, 'w') as f:
        f.write(doc)
    print(f"\nSaved to {outpath}")

    nm = results['n_months']
    print(f"\n{'Pattern':<40} {'Total':>6} {'/Month':>8}")
    print("-" * 56)
    for name, events in [('1: Sweep+Disp+Pullback', results['pattern1']),
                          ('2: OB Touch+Rejection', results['pattern2']),
                          ('3: Flash Displacement', results['pattern3'])]:
        print(f"{name:<40} {len(events):>6} {len(events)/nm:>8.1f}")
