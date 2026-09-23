#!/usr/bin/env python3
"""
M5 Entry Refinement — Comprehensive Validation Backtest
Part 1: Mechanical M5 SL validation on 500+ displacement events
Part 2: Re-simulate 14 AI trades with realistic constraints
Part 3: Combined analysis and deployment recommendation
"""

import json
import glob
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE / "knowledge_base_backtest" / "analysis"
DATA_DIR = BASE / "data"

###############################################################################
# DATA LOADING
###############################################################################

def load_all_data():
    """Load all required datasets."""
    print("[Loading data...]")

    m5 = pd.read_csv(DATA_DIR / "XAUUSD_M5.csv", parse_dates=['time'])
    m5 = m5.sort_values('time').reset_index(drop=True)
    # Pre-index by date for fast lookup
    m5['date_key'] = m5['time'].dt.date
    print(f"  M5: {len(m5)} candles, {m5['time'].min()} to {m5['time'].max()}")

    with open(ANALYSIS_DIR / "displacement_database_20260403_0030.json") as f:
        disp_db = json.load(f)
    print(f"  Displacements: {len(disp_db)}")

    # Previous M5 AI responses
    resp_files = sorted(glob.glob(str(ANALYSIS_DIR / "m5_refinement_responses_*.json")))
    with open(resp_files[-1]) as f:
        ai_responses = json.load(f)
    print(f"  AI responses: {len(ai_responses)}")

    # Phase 1 trades
    with open(ANALYSIS_DIR / "phase1_all_trades_merged.json") as f:
        p1_trades = json.load(f)
    print(f"  Phase 1 trades: {len(p1_trades)}")

    # M15 data for cross-reference
    m15 = pd.read_csv(DATA_DIR / "XAUUSD_M15.csv", parse_dates=['time'])
    m15 = m15.sort_values('time').reset_index(drop=True)

    return m5, disp_db, ai_responses, p1_trades, m15

###############################################################################
# PART 1: MECHANICAL M5 VALIDATION
###############################################################################

def find_m5_swing_sl(m5_slice, disp_idx, direction):
    """
    Find M5 structural stop loss by looking for swing point before displacement.
    disp_idx is index within m5_slice.
    """
    lookback_start = max(0, disp_idx - 10)
    lookback_end = disp_idx

    if lookback_end <= lookback_start:
        return None

    window = m5_slice.iloc[lookback_start:lookback_end]
    if len(window) < 2:
        return None

    if direction == "bullish":
        # Find swing lows (refined approach)
        swing_lows = []
        for i in range(1, len(window) - 1):
            if (window.iloc[i]['low'] <= window.iloc[i-1]['low'] and
                window.iloc[i]['low'] <= window.iloc[i+1]['low']):
                swing_lows.append(window.iloc[i]['low'])

        if swing_lows:
            return swing_lows[-1] - 1.50  # Most recent swing low + buffer
        else:
            return window['low'].min() - 1.50  # Fallback: min low
    else:
        swing_highs = []
        for i in range(1, len(window) - 1):
            if (window.iloc[i]['high'] >= window.iloc[i-1]['high'] and
                window.iloc[i]['high'] >= window.iloc[i+1]['high']):
                swing_highs.append(window.iloc[i]['high'])

        if swing_highs:
            return swing_highs[-1] + 1.50
        else:
            return window['high'].max() + 1.50


def simulate_m5_trade(m5_candles_after, entry_price, sl_price, direction, sl_distance,
                      max_candles=60, entry_slippage=0, sl_slippage=0):
    """
    Walk M5 candles from entry forward. Returns outcome dict.
    entry_slippage: added against you at entry
    sl_slippage: added against you at SL trigger
    """
    if len(m5_candles_after) == 0:
        return {'outcome': 'no_data', 'final_r': 0, 'mfe': 0, 'mae': 0, 'candles': 0}

    # Apply entry slippage
    if direction == 'bullish':
        actual_entry = entry_price + entry_slippage
        actual_sl = sl_price - sl_slippage
    else:
        actual_entry = entry_price - entry_slippage
        actual_sl = sl_price + sl_slippage

    actual_sl_dist = abs(actual_entry - actual_sl)
    if actual_sl_dist < 0.50:
        return {'outcome': 'invalid', 'final_r': 0, 'mfe': 0, 'mae': 0, 'candles': 0}

    tp_dist = actual_sl_dist * 1.5
    if direction == 'bullish':
        tp_price = actual_entry + tp_dist
    else:
        tp_price = actual_entry - tp_dist

    mfe = 0
    mae = 0
    candle_count = 0

    for idx in range(min(max_candles, len(m5_candles_after))):
        candle = m5_candles_after.iloc[idx]
        candle_count += 1

        if direction == 'bullish':
            fav = candle['high'] - actual_entry
            adv = actual_entry - candle['low']
            mfe = max(mfe, fav)
            mae = max(mae, adv)

            if candle['low'] <= actual_sl:
                effective_loss = (actual_sl_dist + sl_slippage) / actual_sl_dist
                return {'outcome': 'sl_hit', 'final_r': -effective_loss, 'mfe': mfe,
                        'mae': mae, 'candles': candle_count, 'tp_price': tp_price,
                        'sl_dist': actual_sl_dist}
            if candle['high'] >= tp_price:
                return {'outcome': 'tp_hit', 'final_r': 1.5, 'mfe': mfe, 'mae': mae,
                        'candles': candle_count, 'tp_price': tp_price, 'sl_dist': actual_sl_dist}
        else:
            fav = actual_entry - candle['low']
            adv = candle['high'] - actual_entry
            mfe = max(mfe, fav)
            mae = max(mae, adv)

            if candle['high'] >= actual_sl:
                effective_loss = (actual_sl_dist + sl_slippage) / actual_sl_dist
                return {'outcome': 'sl_hit', 'final_r': -effective_loss, 'mfe': mfe,
                        'mae': mae, 'candles': candle_count, 'tp_price': tp_price,
                        'sl_dist': actual_sl_dist}
            if candle['low'] <= tp_price:
                return {'outcome': 'tp_hit', 'final_r': 1.5, 'mfe': mfe, 'mae': mae,
                        'candles': candle_count, 'tp_price': tp_price, 'sl_dist': actual_sl_dist}

    # Timeout
    last = m5_candles_after.iloc[min(max_candles-1, len(m5_candles_after)-1)]
    if direction == 'bullish':
        timeout_r = (last['close'] - actual_entry) / actual_sl_dist
    else:
        timeout_r = (actual_entry - last['close']) / actual_sl_dist

    return {'outcome': 'timeout', 'final_r': round(timeout_r, 4), 'mfe': mfe, 'mae': mae,
            'candles': candle_count, 'tp_price': tp_price, 'sl_dist': actual_sl_dist}


def run_part1(m5, disp_db):
    """Part 1: Large-sample mechanical validation."""
    print(f"\n{'='*70}")
    print("PART 1: MECHANICAL M5 VALIDATION")
    print(f"{'='*70}")

    m5_start = m5['time'].min()
    m5_end = m5['time'].max()

    # Select test universe
    candidates = []
    for d in disp_db:
        ts = pd.Timestamp(d['timestamp'])
        if ts < m5_start or ts > m5_end:
            continue
        if not d.get('kz', False):
            continue
        if d.get('body_ratio', 0) < 2.0:
            continue
        if d.get('align', 0) < 1:
            continue
        candidates.append(d)

    print(f"\nTest universe: {len(candidates)} KZ displacements (2x+ body, align>=1)")
    print(f"Date range: {candidates[0]['date']} to {candidates[-1]['date']}")

    # 1.2-1.3: Find M5 swing SL for each displacement
    raw_sl_distances = []
    valid_trades = []

    for disp in candidates:
        ts = pd.Timestamp(disp['timestamp'])
        direction = disp['direction']

        # Find this displacement in M5 data (match by timestamp)
        date_key = ts.date()
        day_m5 = m5[m5['date_key'] == date_key]
        if len(day_m5) == 0:
            continue

        # Find closest M5 candle to displacement timestamp
        time_diffs = abs(day_m5['time'] - ts)
        closest_idx = time_diffs.idxmin()
        disp_local_idx = day_m5.index.get_loc(closest_idx)

        if disp_local_idx < 3:
            continue

        # Find M5 swing SL
        sl_price = find_m5_swing_sl(day_m5, disp_local_idx, direction)
        if sl_price is None:
            continue

        disp_candle = day_m5.iloc[disp_local_idx]
        entry_price = disp_candle['close']  # Market entry at displacement close
        sl_dist = abs(entry_price - sl_price)

        if sl_dist < 0.5 or sl_dist > 100:
            continue

        # Get M5 candles after entry for simulation
        entry_global_idx = closest_idx
        after_start = entry_global_idx + 1
        after_end = min(after_start + 70, len(m5))  # 70 candles max
        sim_candles = m5.iloc[after_start:after_end]

        if len(sim_candles) < 10:
            continue

        raw_sl_distances.append(sl_dist)
        valid_trades.append({
            'disp': disp,
            'entry_price': entry_price,
            'raw_sl_price': sl_price,
            'raw_sl_dist': sl_dist,
            'direction': direction,
            'sim_start_idx': after_start,
            'sim_end_idx': after_end,
            'disp_body': disp.get('body_size', 0),
            'align': disp.get('align', 0),
            'session': disp.get('session', ''),
            'date': disp['date'],
            # Also store the limit entry price (50% of displacement body)
            'limit_entry': entry_price - disp.get('body_size', 0) * 0.5 if direction == 'bullish'
                          else entry_price + disp.get('body_size', 0) * 0.5,
            'disp_global_idx': closest_idx,
        })

    print(f"Valid trades with M5 swing SL: {len(valid_trades)}")

    # 1.3: Raw SL distance distribution
    rsd = np.array(raw_sl_distances)
    print(f"\n--- Raw M5 SL Distance Distribution ---")
    print(f"  Min={rsd.min():.2f}  P10={np.percentile(rsd,10):.2f}  P25={np.percentile(rsd,25):.2f}  "
          f"Median={np.median(rsd):.2f}  P75={np.percentile(rsd,75):.2f}  P90={np.percentile(rsd,90):.2f}  "
          f"Max={rsd.max():.2f}")
    for threshold in [3, 5, 8, 10, 15, 20]:
        pct = (rsd < threshold).mean() * 100
        print(f"  Below ${threshold}: {pct:.1f}%")

    # 1.4: SL Floor Sweep
    SL_FLOORS = [3, 5, 8, 10, 12, 15, 20]
    SLIPPAGE_LEVELS = {'zero': (0, 0), 'normal': (0.30, 0.30), 'stress': (0.50, 0.50)}

    print(f"\n--- SL Floor Sweep Simulation ---")
    print(f"{'Floor':>6} {'Entry':>8} {'Slip':>7} {'n':>5} {'TP%':>6} {'SL%':>6} {'Win%':>6} "
          f"{'TotR':>8} {'AvgR':>7} {'PremSL':>7}")
    print("-" * 80)

    grid_results = []

    for floor in SL_FLOORS:
        for entry_method in ['market', 'limit', 'hybrid']:
            for slip_name, (e_slip, sl_slip) in SLIPPAGE_LEVELS.items():
                results = []

                for trade in valid_trades:
                    direction = trade['direction']
                    raw_sl_dist = trade['raw_sl_dist']
                    market_entry = trade['entry_price']
                    limit_entry_price = trade['limit_entry']

                    # Determine actual entry based on method
                    if entry_method == 'market':
                        actual_entry = market_entry
                    elif entry_method == 'limit':
                        # Check if limit fills within 8 candles
                        check_start = trade['sim_start_idx']
                        check_end = min(check_start + 8, len(m5))
                        fill_candles = m5.iloc[check_start:check_end]
                        filled = False
                        for _, fc in fill_candles.iterrows():
                            if direction == 'bullish' and fc['low'] <= limit_entry_price:
                                filled = True
                                actual_entry = limit_entry_price
                                break
                            elif direction == 'bearish' and fc['high'] >= limit_entry_price:
                                filled = True
                                actual_entry = limit_entry_price
                                break
                        if not filled:
                            continue  # Skip unfilled limit orders
                    elif entry_method == 'hybrid':
                        # Try limit for 4 candles, then market
                        check_start = trade['sim_start_idx']
                        check_end = min(check_start + 4, len(m5))
                        fill_candles = m5.iloc[check_start:check_end]
                        filled = False
                        for _, fc in fill_candles.iterrows():
                            if direction == 'bullish' and fc['low'] <= limit_entry_price:
                                filled = True
                                actual_entry = limit_entry_price
                                break
                            elif direction == 'bearish' and fc['high'] >= limit_entry_price:
                                filled = True
                                actual_entry = limit_entry_price
                                break
                        if not filled:
                            # Market fill at 4th candle close
                            if check_end < len(m5):
                                actual_entry = m5.iloc[check_end - 1]['close']
                            else:
                                continue

                    # Apply SL floor
                    floored_sl_dist = max(raw_sl_dist, floor)

                    if direction == 'bullish':
                        floored_sl = actual_entry - floored_sl_dist
                    else:
                        floored_sl = actual_entry + floored_sl_dist

                    # Simulate
                    sim_candles = m5.iloc[trade['sim_start_idx']:trade['sim_end_idx']]
                    result = simulate_m5_trade(
                        sim_candles, actual_entry, floored_sl, direction,
                        floored_sl_dist, max_candles=60,
                        entry_slippage=e_slip, sl_slippage=sl_slip
                    )

                    # Check if this would have survived at a wider SL (MAE from displacement DB)
                    session_mae = trade['disp'].get('mae_sess', 0) or 0
                    premature = (result['outcome'] == 'sl_hit' and
                                 session_mae < floored_sl_dist * 2)  # rough M15 equivalent

                    result['premature_sl'] = premature
                    result['floor'] = floor
                    result['entry_method'] = entry_method
                    result['slippage'] = slip_name
                    result['actual_entry'] = actual_entry
                    result['floored_sl_dist'] = floored_sl_dist
                    results.append(result)

                if not results:
                    continue

                n = len(results)
                tp_pct = sum(1 for r in results if r['outcome'] == 'tp_hit') / n * 100
                sl_pct = sum(1 for r in results if r['outcome'] == 'sl_hit') / n * 100
                win_pct = sum(1 for r in results if r['final_r'] > 0) / n * 100
                total_r = sum(r['final_r'] for r in results)
                avg_r = np.mean([r['final_r'] for r in results])
                prem_sl = sum(1 for r in results if r.get('premature_sl', False))

                grid_results.append({
                    'floor': floor, 'entry': entry_method, 'slip': slip_name,
                    'n': n, 'tp_pct': tp_pct, 'sl_pct': sl_pct, 'win_pct': win_pct,
                    'total_r': total_r, 'avg_r': avg_r, 'prem_sl': prem_sl,
                    'results': results,
                })

                # Print only for market + zero slippage to keep output manageable,
                # plus the key combinations
                if slip_name == 'zero' or (entry_method == 'market' and slip_name == 'normal'):
                    print(f"${floor:>5} {entry_method:>8} {slip_name:>7} {n:>5} "
                          f"{tp_pct:>5.1f}% {sl_pct:>5.1f}% {win_pct:>5.1f}% "
                          f"{total_r:>+8.1f} {avg_r:>+7.3f} {prem_sl:>5}/{n}")

    # 1.5: Find optimal SL floor
    print(f"\n--- Optimal SL Floor Analysis (Market Entry, Zero Slippage) ---")
    market_zero = [g for g in grid_results if g['entry'] == 'market' and g['slip'] == 'zero']
    for g in market_zero:
        score = g['avg_r'] * (1 - g['prem_sl'] / g['n'] if g['n'] > 0 else 0)
        print(f"  Floor ${g['floor']:>2}: AvgR={g['avg_r']:+.3f} TP={g['tp_pct']:.1f}% "
              f"SL={g['sl_pct']:.1f}% PremSL={g['prem_sl']}/{g['n']} Score={score:+.3f}")

    # 1.6: Split validation
    print(f"\n--- Split Validation ---")
    dates = sorted(set(t['date'] for t in valid_trades))
    mid = len(dates) // 2
    first_half_dates = set(dates[:mid])
    second_half_dates = set(dates[mid:])

    for floor in [5, 8, 10, 12]:
        mg = [g for g in grid_results if g['floor'] == floor and g['entry'] == 'market' and g['slip'] == 'zero']
        if not mg:
            continue
        all_results = mg[0]['results']
        # Need to tag results with dates...
        # Rebuild quickly for split
        h1_r = []
        h2_r = []
        for trade, result in zip(valid_trades, all_results[:len(valid_trades)]):
            if trade['date'] in first_half_dates:
                h1_r.append(result['final_r'])
            else:
                h2_r.append(result['final_r'])
        if h1_r and h2_r:
            print(f"  Floor ${floor}: H1 avg={np.mean(h1_r):+.3f} (n={len(h1_r)}) | "
                  f"H2 avg={np.mean(h2_r):+.3f} (n={len(h2_r)})")

    return grid_results, valid_trades, raw_sl_distances

###############################################################################
# PART 2: RE-SIMULATE 14 AI TRADES
###############################################################################

def run_part2(m5, ai_responses, p1_trades, grid_results):
    """Part 2: Re-simulate AI trades with realistic constraints."""
    print(f"\n{'='*70}")
    print("PART 2: AI TRADE RE-SIMULATION")
    print(f"{'='*70}")

    # Match AI responses to Phase 1 trades
    trade_map = {}
    for t in p1_trades:
        key = (t['date'], t['kill_zone'])
        trade_map[key] = t

    # Filter to trades with M5 data
    m5_start_date = m5['time'].min().date()
    ai_trades = []
    for resp in ai_responses:
        key = (resp['date'], resp['kz'])
        if key not in trade_map:
            continue
        trade = trade_map[key]
        ts = pd.Timestamp(trade['date'])
        if ts.date() < m5_start_date:
            continue
        ai_trades.append({
            'trade': trade,
            'response': resp.get('refinement', resp),
        })

    print(f"AI trades with M5 data: {len(ai_trades)}")

    SL_FLOORS = [3, 5, 8, 10, 12, 15, 20]

    # For each trade × floor × entry method × slippage, simulate
    all_results = []

    for at in ai_trades:
        trade = at['trade']
        ref = at['response']
        date_str = trade['date']
        kz = trade['kill_zone']
        direction = trade['direction']
        m15_entry = trade['entry_price']
        m15_sl = trade['stop_loss']
        m15_sl_dist = abs(m15_entry - m15_sl)
        entry_time = pd.Timestamp(trade['candle_time']).tz_localize(None)

        # Get simulation candles
        if kz == 'london':
            session_end = pd.Timestamp(date_str) + pd.Timedelta(hours=11, minutes=30)
        else:
            session_end = pd.Timestamp(date_str) + pd.Timedelta(hours=17, minutes=30)

        sim_candles = m5[(m5['time'] >= entry_time) & (m5['time'] <= session_end)]
        if len(sim_candles) < 5:
            continue

        # Get AI's M5 entry and SL
        ai_m5_entry = ref.get('m5_entry')
        ai_m5_sl = ref.get('m5_sl')
        ai_m5_sl_dist = ref.get('m5_sl_distance')
        refined = ref.get('decision') == 'REFINED'
        quality = ref.get('m5_quality', 'LOW')

        trade_result = {
            'date': date_str, 'kz': kz, 'direction': direction,
            'grade': trade.get('setup_grade', '?'),
            'm15_entry': m15_entry, 'm15_sl': m15_sl, 'm15_sl_dist': m15_sl_dist,
            'refined': refined, 'quality': quality,
            'ai_m5_entry': ai_m5_entry, 'ai_m5_sl_dist': ai_m5_sl_dist,
            'phase1_r': trade['r_multiple'],
            'floors': {},
        }

        # Baseline: M15 entry + M15 SL
        baseline = simulate_m5_trade(sim_candles, m15_entry, m15_sl,
                                      'bullish' if direction == 'LONG' else 'bearish',
                                      m15_sl_dist, max_candles=60)
        trade_result['baseline'] = baseline

        for floor in SL_FLOORS:
            floor_results = {}

            for entry_method in ['market', 'limit', 'hybrid']:
                for slip_name, (e_slip, sl_slip) in [('zero', (0,0)), ('normal', (0.3,0.3)), ('stress', (0.5,0.5))]:
                    dir_str = 'bullish' if direction == 'LONG' else 'bearish'

                    if not refined:
                        # No refinement: use M15 entry+SL for all
                        result = baseline.copy()
                        floor_results[f'{entry_method}_{slip_name}'] = result
                        continue

                    # Determine entry price
                    if entry_method == 'market':
                        actual_entry = m15_entry
                    elif entry_method == 'limit':
                        # Check if AI's M5 entry fills
                        if ai_m5_entry is None:
                            actual_entry = m15_entry
                        else:
                            filled = False
                            check_end = min(8, len(sim_candles))
                            for i in range(check_end):
                                c = sim_candles.iloc[i]
                                if dir_str == 'bullish' and c['low'] <= ai_m5_entry:
                                    filled = True
                                    break
                                elif dir_str == 'bearish' and c['high'] >= ai_m5_entry:
                                    filled = True
                                    break
                            if filled:
                                actual_entry = ai_m5_entry
                            else:
                                floor_results[f'{entry_method}_{slip_name}'] = {
                                    'outcome': 'unfilled', 'final_r': 0}
                                continue
                    elif entry_method == 'hybrid':
                        if ai_m5_entry is not None:
                            filled = False
                            check_end = min(4, len(sim_candles))
                            for i in range(check_end):
                                c = sim_candles.iloc[i]
                                if dir_str == 'bullish' and c['low'] <= ai_m5_entry:
                                    filled = True
                                    actual_entry = ai_m5_entry
                                    break
                                elif dir_str == 'bearish' and c['high'] >= ai_m5_entry:
                                    filled = True
                                    actual_entry = ai_m5_entry
                                    break
                            if not filled:
                                actual_entry = m15_entry  # Fallback to market
                        else:
                            actual_entry = m15_entry

                    # Apply SL floor
                    if ai_m5_sl_dist is not None and refined:
                        base_sl_dist = max(ai_m5_sl_dist, floor)
                    else:
                        base_sl_dist = m15_sl_dist  # No refinement

                    if dir_str == 'bullish':
                        sl_price = actual_entry - base_sl_dist
                    else:
                        sl_price = actual_entry + base_sl_dist

                    result = simulate_m5_trade(
                        sim_candles, actual_entry, sl_price, dir_str,
                        base_sl_dist, max_candles=60,
                        entry_slippage=e_slip, sl_slippage=sl_slip)

                    # Position sizing
                    risk_dollars = 1000
                    lots = risk_dollars / (base_sl_dist * 100)
                    lots = min(lots, 5.0)
                    actual_risk = lots * base_sl_dist * 100
                    dollar_pnl = result['final_r'] * actual_risk

                    result['lots'] = round(lots, 2)
                    result['dollar_pnl'] = round(dollar_pnl, 2)
                    result['actual_entry'] = actual_entry
                    result['floored_sl_dist'] = base_sl_dist

                    floor_results[f'{entry_method}_{slip_name}'] = result

            trade_result['floors'][floor] = floor_results

        all_results.append(trade_result)

    # Print results at key floors
    for floor in [5, 8, 10, 12]:
        print(f"\n--- Floor ${floor}: Per-Trade Results (Market Entry, Zero Slippage) ---")
        print(f"{'#':>2} {'Date':>10} {'KZ':>7} {'Qual':>4} {'Base R':>7} {'M5 R':>7} "
              f"{'M5 SL$':>7} {'Lots':>5} {'$PnL':>8}")
        print("-" * 70)

        total_base = 0
        total_m5 = 0
        total_pnl = 0
        tp_base = 0
        tp_m5 = 0
        sl_base = 0
        sl_m5 = 0

        for i, tr in enumerate(all_results):
            base_r = tr['baseline']['final_r']
            total_base += base_r
            if tr['baseline']['outcome'] == 'tp_hit': tp_base += 1
            if tr['baseline']['outcome'] == 'sl_hit': sl_base += 1

            fr = tr['floors'].get(floor, {})
            m5_result = fr.get('market_zero', tr['baseline'])
            m5_r = m5_result['final_r']
            total_m5 += m5_r
            if m5_result.get('outcome') == 'tp_hit': tp_m5 += 1
            if m5_result.get('outcome') == 'sl_hit': sl_m5 += 1

            pnl = m5_result.get('dollar_pnl', m5_r * 1000)
            total_pnl += pnl
            lots = m5_result.get('lots', '-')
            sl_d = m5_result.get('floored_sl_dist', '-')

            print(f"{i+1:2d} {tr['date']:>10} {tr['kz']:>7} {tr.get('quality','?'):>4} "
                  f"{base_r:>+7.3f} {m5_r:>+7.3f} "
                  f"{'$'+str(round(sl_d,1)) if isinstance(sl_d,float) else sl_d:>7} "
                  f"{lots:>5} {pnl:>+8.0f}")

        n = len(all_results)
        extra_sl = sl_m5 - sl_base
        print(f"\n  Totals: Base={total_base:+.2f}R  M5={total_m5:+.2f}R  "
              f"TP: {tp_base}→{tp_m5}  SL: {sl_base}→{sl_m5} (extra: {extra_sl})  "
              f"$PnL={total_pnl:+.0f}")

    return all_results

###############################################################################
# PART 3: COMBINED ANALYSIS
###############################################################################

def run_part3(grid_results, ai_results, raw_sl_distances):
    """Part 3: Cross-validate and produce deployment recommendation."""
    print(f"\n{'='*70}")
    print("PART 3: COMBINED ANALYSIS & DEPLOYMENT RECOMMENDATION")
    print(f"{'='*70}")

    # Find optimal floor from Part 1
    print("\n--- Part 1 Optimal Floor (Market, Zero Slip) ---")
    market_zero = [g for g in grid_results if g['entry'] == 'market' and g['slip'] == 'zero']
    best_floor = None
    best_score = -999

    for g in market_zero:
        prem_rate = g['prem_sl'] / g['n'] if g['n'] > 0 else 0
        # Score: avg_r * (1 - premature_rate) — penalize premature stops
        score = g['avg_r'] * (1 - prem_rate * 2)
        if score > best_score:
            best_score = score
            best_floor = g['floor']
        print(f"  ${g['floor']:>2}: AvgR={g['avg_r']:+.4f} TP={g['tp_pct']:.1f}% "
              f"SL={g['sl_pct']:.1f}% Prem={prem_rate:.1%} Score={score:+.4f}")

    print(f"\n  >>> Part 1 optimal floor: ${best_floor}")

    # Check Part 2 at this floor
    print(f"\n--- Part 2 at Floor ${best_floor} ---")
    for entry_method in ['market', 'limit', 'hybrid']:
        for slip in ['zero', 'normal', 'stress']:
            key = f'{entry_method}_{slip}'
            rs = []
            for tr in ai_results:
                fr = tr['floors'].get(best_floor, {})
                r = fr.get(key)
                if r and r.get('outcome') != 'unfilled':
                    rs.append(r['final_r'])
            if rs:
                avg = np.mean(rs)
                tp = sum(1 for r in rs if r >= 1.49) / len(rs) * 100
                sl = sum(1 for r in rs if r <= -0.99) / len(rs) * 100
                print(f"  {entry_method:>7} {slip:>7}: n={len(rs)} AvgR={avg:+.3f} TP={tp:.0f}% SL={sl:.0f}%")

    # Stress test: at what slippage does M5 stop being better?
    print(f"\n--- Stress Test: M5 vs M15 under slippage ---")
    baseline_avg = np.mean([tr['baseline']['final_r'] for tr in ai_results])
    print(f"  Baseline (M15) avg R: {baseline_avg:+.3f}")

    for slip in ['zero', 'normal', 'stress']:
        key = f'market_{slip}'
        rs = []
        for tr in ai_results:
            fr = tr['floors'].get(best_floor, {})
            r = fr.get(key)
            if r:
                rs.append(r['final_r'])
        if rs:
            avg = np.mean(rs)
            diff = avg - baseline_avg
            print(f"  M5 Floor ${best_floor} ({slip}): avg={avg:+.3f} (Δ={diff:+.3f}R vs baseline)")

    # Quality interaction
    print(f"\n--- Quality Interaction at Floor ${best_floor} ---")
    for qual in ['HIGH', 'MEDIUM', 'LOW', None]:
        label = qual if qual else 'NO_REFINE'
        subset = [tr for tr in ai_results if tr.get('quality') == qual or
                  (qual is None and not tr['refined'])]
        if not subset:
            continue
        base_rs = [tr['baseline']['final_r'] for tr in subset]
        m5_rs = []
        for tr in subset:
            fr = tr['floors'].get(best_floor, {})
            r = fr.get('market_zero', tr['baseline'])
            m5_rs.append(r['final_r'])
        needs_floor = sum(1 for tr in subset if tr.get('ai_m5_sl_dist') and
                         tr['ai_m5_sl_dist'] < best_floor)
        print(f"  {label:>10}: n={len(subset)} Base={np.mean(base_rs):+.3f} "
              f"M5={np.mean(m5_rs):+.3f} Floor binds={needs_floor}/{len(subset)}")

    # Entry method comparison
    print(f"\n--- Entry Method Comparison at Floor ${best_floor} (Zero Slip) ---")
    for method in ['market', 'limit', 'hybrid']:
        key = f'{method}_zero'
        rs = []
        n_unfilled = 0
        for tr in ai_results:
            fr = tr['floors'].get(best_floor, {})
            r = fr.get(key)
            if r:
                if r.get('outcome') == 'unfilled':
                    n_unfilled += 1
                else:
                    rs.append(r['final_r'])
        if rs:
            print(f"  {method:>7}: n={len(rs)} AvgR={np.mean(rs):+.3f} "
                  f"TotalR={sum(rs):+.1f} Unfilled={n_unfilled}")

    # DEPLOYMENT RECOMMENDATION
    print(f"\n{'='*70}")
    print("DEPLOYMENT RECOMMENDATION")
    print(f"{'='*70}")

    # Get Part 1 stats at optimal floor
    opt_g = [g for g in market_zero if g['floor'] == best_floor][0]

    # Get Part 2 stats at optimal floor (market, normal slippage)
    p2_rs = []
    p2_base_rs = []
    for tr in ai_results:
        p2_base_rs.append(tr['baseline']['final_r'])
        fr = tr['floors'].get(best_floor, {})
        r = fr.get('market_normal', fr.get('market_zero', tr['baseline']))
        p2_rs.append(r['final_r'])

    print(f"""
M5 REFINEMENT CONFIGURATION:
  SL floor: ${best_floor:.2f}
  Entry method: market (at M15 confirmation close)
  Slippage buffer: $0.30 added to structural SL
  Max lots: 5.0
  Quality gate: HIGH + MEDIUM only
  Fallback: M15 SL when M5 quality = LOW or NO_REFINEMENT

  Part 1 Mechanical Validation ({opt_g['n']} trades):
    TP hit rate: {opt_g['tp_pct']:.1f}%
    SL hit rate: {opt_g['sl_pct']:.1f}%
    Avg R: {opt_g['avg_r']:+.3f}
    Premature stops: {opt_g['prem_sl']}/{opt_g['n']} ({opt_g['prem_sl']/opt_g['n']*100:.1f}%)

  Part 2 AI Trade Validation ({len(ai_results)} trades, normal slippage):
    Baseline avg R: {np.mean(p2_base_rs):+.3f}
    M5 avg R: {np.mean(p2_rs):+.3f}
    Improvement: {np.mean(p2_rs) - np.mean(p2_base_rs):+.3f}R per trade
""")

    return best_floor

###############################################################################
# MAIN
###############################################################################

def main():
    print("=" * 70)
    print("M5 COMPREHENSIVE VALIDATION BACKTEST")
    print("=" * 70)

    m5, disp_db, ai_responses, p1_trades, m15 = load_all_data()

    # Part 1
    grid_results, valid_trades, raw_sl_dists = run_part1(m5, disp_db)

    # Part 2
    ai_results = run_part2(m5, ai_responses, p1_trades, grid_results)

    # Part 3
    best_floor = run_part3(grid_results, ai_results, raw_sl_dists)

    # Save all data
    ts = datetime.now().strftime('%Y%m%d_%H%M')

    # Save grid results (without the large 'results' arrays)
    grid_save = [{k: v for k, v in g.items() if k != 'results'} for g in grid_results]
    with open(ANALYSIS_DIR / f"m5_validation_data_{ts}.json", 'w') as f:
        json.dump({
            'grid_results': grid_save,
            'optimal_floor': best_floor,
            'raw_sl_dist_stats': {
                'min': float(np.min(raw_sl_dists)),
                'p10': float(np.percentile(raw_sl_dists, 10)),
                'p25': float(np.percentile(raw_sl_dists, 25)),
                'median': float(np.median(raw_sl_dists)),
                'p75': float(np.percentile(raw_sl_dists, 75)),
                'p90': float(np.percentile(raw_sl_dists, 90)),
                'max': float(np.max(raw_sl_dists)),
            },
            'n_mechanical': len(valid_trades),
            'n_ai': len(ai_results),
        }, f, indent=2, default=str)
    print(f"\n  Saved: m5_validation_data_{ts}.json")

    # Save mechanical trades CSV
    mech_rows = []
    for trade in valid_trades:
        mech_rows.append({
            'date': trade['date'],
            'session': trade['session'],
            'direction': trade['direction'],
            'entry_price': trade['entry_price'],
            'raw_sl_dist': trade['raw_sl_dist'],
            'align': trade['align'],
            'body_size': trade['disp_body'],
        })
    pd.DataFrame(mech_rows).to_csv(ANALYSIS_DIR / f"m5_validation_mechanical_{ts}.csv", index=False)
    print(f"  Saved: m5_validation_mechanical_{ts}.csv")

    return grid_results, ai_results, best_floor

if __name__ == '__main__':
    grid_results, ai_results, best_floor = main()
