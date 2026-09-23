#!/usr/bin/env python3
"""
Deep Trade Analysis — System Optimization Research
Analyzes 36 validated trades from TP1-fixed system (Sonnet, session memory, ob_retest only)
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import os

# ─── Load Data ───────────────────────────────────────────────────────────────

with open('knowledge_base_backtest/analysis/replay/replay_results.json') as f:
    trades = json.load(f)

m15 = pd.read_csv('data/XAUUSD_M15.csv', parse_dates=['time'])
m15 = m15.sort_values('time').reset_index(drop=True)
m15.set_index('time', inplace=True)

print(f"Loaded {len(trades)} trades, M15 data: {m15.index[0]} to {m15.index[-1]}")

# ─── Helper Functions ────────────────────────────────────────────────────────

def get_forward_candles(entry_time_str, n_candles=60):
    """Get n_candles of M15 data starting from entry_time"""
    entry_time = pd.Timestamp(entry_time_str).tz_localize(None)
    mask = m15.index >= entry_time
    return m15[mask].head(n_candles)

def compute_r_at_candle(candle_close, entry_price, stop_loss, direction):
    """Compute R-multiple at a given price"""
    sl_dist = abs(entry_price - stop_loss)
    if sl_dist == 0:
        return 0
    if direction == 'LONG':
        return (candle_close - entry_price) / sl_dist
    else:
        return (entry_price - candle_close) / sl_dist

def compute_r_path(trade, n_candles=60):
    """Compute candle-by-candle R-multiple path for a trade"""
    fwd = get_forward_candles(trade['candle_time'], n_candles)
    if len(fwd) == 0:
        return [], []

    entry = trade['entry_price']
    sl = trade['stop_loss']
    direction = trade['direction']
    sl_dist = abs(entry - sl)

    r_path = []
    for _, candle in fwd.iterrows():
        # Use close for R, but track high/low for MFE/MAE
        r_close = compute_r_at_candle(candle['close'], entry, sl, direction)
        if direction == 'LONG':
            r_high = (candle['high'] - entry) / sl_dist
            r_low = (candle['low'] - entry) / sl_dist
        else:
            r_high = (entry - candle['low']) / sl_dist
            r_low = (entry - candle['high']) / sl_dist
        r_path.append({
            'r_close': r_close,
            'r_high': r_high,
            'r_low': r_low,
            'close': candle['close'],
            'high': candle['high'],
            'low': candle['low']
        })
    return r_path

# ─── ANALYSIS 1: Exit Strategy Optimization ──────────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 1: EXIT STRATEGY OPTIMIZATION")
print("="*80)

# Compute R-paths for all trades
trade_paths = []
for i, trade in enumerate(trades):
    path = compute_r_path(trade, 80)  # 80 candles = 20 hours forward
    trade_paths.append(path)
    if len(path) == 0:
        print(f"  WARNING: No candle data for trade {i} ({trade['date']})")

# --- 1a: Time to MFE ---
print("\n--- Time to Max Favorable Excursion ---")
mfe_candle_indices = []
for i, (trade, path) in enumerate(zip(trades, trade_paths)):
    if not path:
        mfe_candle_indices.append(None)
        continue
    max_r = -999
    max_idx = 0
    for j, p in enumerate(path):
        if p['r_high'] > max_r:
            max_r = p['r_high']
            max_idx = j
    mfe_candle_indices.append(max_idx)

winners_mfe_idx = [mfe_candle_indices[i] for i in range(len(trades)) if trades[i]['outcome'] == 'WIN' and mfe_candle_indices[i] is not None]
losers_mfe_idx = [mfe_candle_indices[i] for i in range(len(trades)) if trades[i]['outcome'] == 'LOSS' and mfe_candle_indices[i] is not None]

print(f"  Winners avg candles to MFE: {np.mean(winners_mfe_idx):.1f} (med: {np.median(winners_mfe_idx):.0f})")
print(f"  Losers avg candles to MFE: {np.mean(losers_mfe_idx):.1f} (med: {np.median(losers_mfe_idx):.0f})")

# Distribution
early_mfe = sum(1 for x in mfe_candle_indices if x is not None and x <= 4)
mid_mfe = sum(1 for x in mfe_candle_indices if x is not None and 5 <= x <= 15)
late_mfe = sum(1 for x in mfe_candle_indices if x is not None and x > 15)
print(f"  Early MFE (0-4 candles): {early_mfe} trades")
print(f"  Mid MFE (5-15 candles): {mid_mfe} trades")
print(f"  Late MFE (16+ candles): {late_mfe} trades")

# --- 1b: Breakeven move simulations ---
print("\n--- Breakeven Move Simulations ---")

def simulate_be_move(trades, trade_paths, be_threshold_r):
    """Simulate moving SL to breakeven when MFE reaches be_threshold_r"""
    results = []
    for i, (trade, path) in enumerate(zip(trades, trade_paths)):
        if not path:
            results.append({'r': trade['r_multiple'], 'outcome': trade['outcome']})
            continue

        entry = trade['entry_price']
        sl = trade['stop_loss']
        sl_dist = abs(entry - sl)
        direction = trade['direction']

        be_triggered = False
        final_r = None
        hold_limit = trade['hold_time_candles'] if trade['hold_time_candles'] else len(path)

        for j, p in enumerate(path):
            if j >= min(hold_limit, len(path)):
                break

            # Check if MFE reached threshold
            if p['r_high'] >= be_threshold_r:
                be_triggered = True

            # If BE triggered, check if price came back to entry (stopped at BE)
            if be_triggered and p['r_low'] <= 0:
                final_r = 0.0  # Stopped at breakeven
                break

            # Check original SL hit
            if not be_triggered and p['r_low'] <= -1.0:
                final_r = -1.0
                break

        if final_r is None:
            # Timed out - use close of last candle in hold period
            idx = min(hold_limit - 1, len(path) - 1)
            final_r = path[idx]['r_close']

        outcome = 'WIN' if final_r > 0 else ('BREAKEVEN' if final_r == 0 else 'LOSS')
        results.append({'r': final_r, 'outcome': outcome})

    return results

be_thresholds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
be_results = {}

for thresh in be_thresholds:
    res = simulate_be_move(trades, trade_paths, thresh)
    wins = sum(1 for r in res if r['r'] > 0)
    losses = sum(1 for r in res if r['r'] < 0)
    bes = sum(1 for r in res if r['r'] == 0)
    avg_win = np.mean([r['r'] for r in res if r['r'] > 0]) if wins > 0 else 0
    avg_loss = np.mean([r['r'] for r in res if r['r'] < 0]) if losses > 0 else 0
    total_r = sum(r['r'] for r in res)
    wr = wins / len(res) * 100
    exp = total_r / len(res)

    be_results[thresh] = {
        'wins': wins, 'losses': losses, 'bes': bes,
        'wr': wr, 'avg_win': avg_win, 'avg_loss': avg_loss,
        'total_r': total_r, 'expectancy': exp
    }
    print(f"  BE at {thresh}R: W={wins} L={losses} BE={bes} WR={wr:.1f}% AvgW={avg_win:+.2f}R AvgL={avg_loss:+.2f}R Total={total_r:+.2f}R Exp={exp:+.3f}R")

# --- 1c: Trailing stop simulations ---
print("\n--- Trailing Stop Simulations ---")

def simulate_trail(trades, trade_paths, trail_distance_r):
    """Simulate trailing stop at MFE - trail_distance_r"""
    results = []
    for i, (trade, path) in enumerate(zip(trades, trade_paths)):
        if not path:
            results.append({'r': trade['r_multiple']})
            continue

        entry = trade['entry_price']
        sl = trade['stop_loss']
        sl_dist = abs(entry - sl)

        max_r_seen = -999
        trail_sl_r = -1.0  # Start at original SL
        final_r = None
        hold_limit = trade['hold_time_candles'] if trade['hold_time_candles'] else len(path)

        for j, p in enumerate(path):
            if j >= min(hold_limit, len(path)):
                break

            # Update max R and trail SL
            if p['r_high'] > max_r_seen:
                max_r_seen = p['r_high']
                new_trail = max_r_seen - trail_distance_r
                if new_trail > trail_sl_r:
                    trail_sl_r = new_trail

            # Check if trail SL hit
            if p['r_low'] <= trail_sl_r:
                final_r = trail_sl_r
                break

        if final_r is None:
            idx = min(hold_limit - 1, len(path) - 1)
            final_r = path[idx]['r_close']

        results.append({'r': final_r})

    return results

trail_distances = [0.5, 0.75, 1.0, 1.5, 2.0]
trail_results = {}

for dist in trail_distances:
    res = simulate_trail(trades, trade_paths, dist)
    rs = [r['r'] for r in res]
    wins = sum(1 for r in rs if r > 0)
    losses = sum(1 for r in rs if r < 0)
    avg_win = np.mean([r for r in rs if r > 0]) if wins > 0 else 0
    avg_loss = np.mean([r for r in rs if r < 0]) if losses > 0 else 0
    total_r = sum(rs)
    wr = wins / len(rs) * 100
    exp = total_r / len(rs)

    trail_results[dist] = {
        'wins': wins, 'losses': losses,
        'wr': wr, 'avg_win': avg_win, 'avg_loss': avg_loss,
        'total_r': total_r, 'expectancy': exp
    }
    print(f"  Trail at MFE-{dist}R: W={wins} L={losses} WR={wr:.1f}% AvgW={avg_win:+.2f}R AvgL={avg_loss:+.2f}R Total={total_r:+.2f}R Exp={exp:+.3f}R")

# --- 1d: Fixed TP simulations ---
print("\n--- Fixed TP Simulations ---")

def simulate_fixed_tp(trades, trade_paths, tp_r):
    """Simulate closing 100% at fixed R-multiple"""
    results = []
    for i, (trade, path) in enumerate(zip(trades, trade_paths)):
        if not path:
            results.append({'r': trade['r_multiple']})
            continue

        final_r = None
        hold_limit = trade['hold_time_candles'] if trade['hold_time_candles'] else len(path)

        for j, p in enumerate(path):
            if j >= min(hold_limit, len(path)):
                break

            # Check TP hit
            if p['r_high'] >= tp_r:
                final_r = tp_r
                break

            # Check SL hit
            if p['r_low'] <= -1.0:
                final_r = -1.0
                break

        if final_r is None:
            idx = min(hold_limit - 1, len(path) - 1)
            final_r = path[idx]['r_close']

        results.append({'r': final_r})

    return results

fixed_tps = [0.75, 1.0, 1.5, 2.0, 2.5, 3.0]
fixed_tp_results = {}

for tp in fixed_tps:
    res = simulate_fixed_tp(trades, trade_paths, tp)
    rs = [r['r'] for r in res]
    wins = sum(1 for r in rs if r > 0)
    losses = sum(1 for r in rs if r < 0)
    tp_hits = sum(1 for r in rs if r == tp)
    avg_win = np.mean([r for r in rs if r > 0]) if wins > 0 else 0
    avg_loss = np.mean([r for r in rs if r < 0]) if losses > 0 else 0
    total_r = sum(rs)
    wr = wins / len(rs) * 100
    exp = total_r / len(rs)

    fixed_tp_results[tp] = {
        'wins': wins, 'losses': losses, 'tp_hits': tp_hits,
        'wr': wr, 'avg_win': avg_win, 'avg_loss': avg_loss,
        'total_r': total_r, 'expectancy': exp
    }
    print(f"  Fixed TP {tp}R: W={wins} L={losses} TPHits={tp_hits} WR={wr:.1f}% AvgW={avg_win:+.2f}R AvgL={avg_loss:+.2f}R Total={total_r:+.2f}R Exp={exp:+.3f}R")

# --- 1e: Partial close schemes ---
print("\n--- Partial Close Schemes ---")

def simulate_partial_close(trades, trade_paths, scheme):
    """
    scheme: list of (fraction, close_at_r, trail_after) tuples
    e.g. [(0.5, 1.5, None), (0.5, 3.0, None)] = 50% at 1.5R, 50% at 3.0R
    e.g. [(0.5, 1.0, None), (0.5, None, 1.0)] = 50% at 1.0R, 50% trail at MFE-1.0R
    """
    results = []
    for i, (trade, path) in enumerate(zip(trades, trade_paths)):
        if not path:
            results.append({'r': trade['r_multiple']})
            continue

        hold_limit = trade['hold_time_candles'] if trade['hold_time_candles'] else len(path)
        portions = []
        for frac, close_r, trail_dist in scheme:
            portions.append({
                'fraction': frac, 'target_r': close_r, 'trail_dist': trail_dist,
                'closed': False, 'close_r': None, 'max_r_seen': -999, 'trail_sl_r': -1.0
            })

        for j, p in enumerate(path):
            if j >= min(hold_limit, len(path)):
                break

            for port in portions:
                if port['closed']:
                    continue

                # Check SL hit
                if p['r_low'] <= -1.0:
                    port['close_r'] = -1.0
                    port['closed'] = True
                    continue

                # Fixed TP target
                if port['target_r'] is not None and p['r_high'] >= port['target_r']:
                    port['close_r'] = port['target_r']
                    port['closed'] = True
                    continue

                # Trailing stop
                if port['trail_dist'] is not None:
                    if p['r_high'] > port['max_r_seen']:
                        port['max_r_seen'] = p['r_high']
                        new_trail = port['max_r_seen'] - port['trail_dist']
                        if new_trail > port['trail_sl_r']:
                            port['trail_sl_r'] = new_trail
                    if p['r_low'] <= port['trail_sl_r'] and port['trail_sl_r'] > -1.0:
                        port['close_r'] = port['trail_sl_r']
                        port['closed'] = True

        # Close unclosed portions at timeout
        for port in portions:
            if not port['closed']:
                idx = min(hold_limit - 1, len(path) - 1)
                port['close_r'] = path[idx]['r_close']

        total_r = sum(port['fraction'] * port['close_r'] for port in portions)
        results.append({'r': total_r})

    return results

schemes = {
    'Current (50% TP1=2.5R, 50% runs)': [(0.5, 2.5, None), (0.5, None, None)],
    '50% at 1.5R, 50% at 3.0R': [(0.5, 1.5, None), (0.5, 3.0, None)],
    '33/33/33 at 1.0/2.0/3.0R': [(0.333, 1.0, None), (0.333, 2.0, None), (0.334, 3.0, None)],
    '50% at 1.0R, 50% trail MFE-1.0R': [(0.5, 1.0, None), (0.5, None, 1.0)],
    '50% at 1.5R, 50% trail MFE-1.0R': [(0.5, 1.5, None), (0.5, None, 1.0)],
    '100% trail MFE-1.0R': [(1.0, None, 1.0)],
    '50% at 1.0R, 50% trail MFE-0.75R': [(0.5, 1.0, None), (0.5, None, 0.75)],
}

partial_results = {}
for name, scheme in schemes.items():
    res = simulate_partial_close(trades, trade_paths, scheme)
    rs = [r['r'] for r in res]
    wins = sum(1 for r in rs if r > 0)
    losses = sum(1 for r in rs if r < 0)
    total_r = sum(rs)
    wr = wins / len(rs) * 100
    exp = total_r / len(rs)
    avg_win = np.mean([r for r in rs if r > 0]) if wins > 0 else 0
    avg_loss = np.mean([r for r in rs if r < 0]) if losses > 0 else 0

    partial_results[name] = {
        'wins': wins, 'losses': losses,
        'wr': wr, 'avg_win': avg_win, 'avg_loss': avg_loss,
        'total_r': total_r, 'expectancy': exp
    }
    print(f"  {name}: W={wins} L={losses} WR={wr:.1f}% Total={total_r:+.2f}R Exp={exp:+.3f}R")

# --- 1f: Post-timeout analysis ---
print("\n--- Post-Timeout Analysis ---")
timeout_trades = [(i, t) for i, t in enumerate(trades) if 'TIMEOUT' in t.get('exit_substate', '')]
print(f"  Timeout trades: {len(timeout_trades)}")

for hours_extra in [2, 4, 8]:
    extra_candles = hours_extra * 4  # M15 candles
    would_improve = 0
    would_worsen = 0
    would_hit_tp1 = 0

    for idx, trade in timeout_trades:
        path = trade_paths[idx]
        if not path:
            continue

        hold = trade['hold_time_candles']
        sl_dist = abs(trade['entry_price'] - trade['stop_loss'])
        tp1_r = trade['risk_reward_ratio']

        # Check extended period
        extended_end = min(hold + extra_candles, len(path))
        if extended_end <= hold:
            continue

        # R at timeout
        timeout_r = path[min(hold-1, len(path)-1)]['r_close']

        # Best R in extended period
        best_r_extended = max(p['r_high'] for p in path[hold:extended_end]) if hold < len(path) else timeout_r
        worst_r_extended = min(p['r_low'] for p in path[hold:extended_end]) if hold < len(path) else timeout_r
        end_r = path[min(extended_end-1, len(path)-1)]['r_close']

        if best_r_extended >= tp1_r:
            would_hit_tp1 += 1
        if end_r > timeout_r:
            would_improve += 1
        elif end_r < timeout_r:
            would_worsen += 1

    print(f"  +{hours_extra}h: Would hit TP1={would_hit_tp1}, Improved={would_improve}, Worsened={would_worsen}")

# ─── ANALYSIS 2: Loser Autopsy ──────────────────────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 2: LOSER AUTOPSY")
print("="*80)

losers = [(i, t) for i, t in enumerate(trades) if t['outcome'] == 'LOSS']
print(f"\nTotal losers: {len(losers)}")

loser_classifications = {}
for idx, trade in losers:
    mfe = trade['mfe_r']
    path = trade_paths[idx]

    # Classify
    if mfe < 0.25:
        classification = 'BAD_ENTRY'
    elif mfe >= 1.0:
        classification = 'NEAR_MISS'
    elif trade['hold_time_candles'] >= 20 and mfe < 0.5:
        classification = 'SLOW_BLEED'
    elif trade['hold_time_candles'] <= 5:
        classification = 'SPIKE_OUT'
    else:
        # Check speed of adverse move
        if path:
            # Find how fast it went negative
            first_deep_negative = None
            for j, p in enumerate(path):
                if p['r_low'] <= -0.75:
                    first_deep_negative = j
                    break
            if first_deep_negative is not None and first_deep_negative <= 3:
                classification = 'SPIKE_OUT'
            else:
                classification = 'SLOW_BLEED'
        else:
            classification = 'SLOW_BLEED'

    loser_classifications[idx] = classification

    # Detailed analysis
    candles_eval = trade.get('candles_evaluated_before_entry', 0)
    memory_entries = len(trade.get('session_memory_at_entry', []))

    # Time from MFE to SL/exit
    mfe_candle = mfe_candle_indices[idx] if mfe_candle_indices[idx] is not None else 0

    print(f"\n  Trade #{idx} ({trade['date']} {trade['kill_zone']}): {classification}")
    print(f"    Entry={trade['entry_price']}, SL={trade['stop_loss']}, Dir={trade['direction']}")
    print(f"    R={trade['r_multiple']:+.2f}, MFE={mfe:.3f}R, MAE={trade['mae_r']:.3f}R, Hold={trade['hold_time_candles']} candles")
    print(f"    Exit: {trade['exit_substate']}")
    print(f"    MFE reached at candle {mfe_candle}")
    print(f"    Prior NO_TRADEs: {memory_entries - 1}")
    print(f"    Confidence: {trade['confidence_score']}, PLC={trade['confidence_metrics']['price_level_count']}, HS={trade['confidence_metrics']['hesitation_score']}")

# Summary
class_counts = Counter(loser_classifications.values())
print(f"\n  Classification summary:")
for cls, count in class_counts.most_common():
    print(f"    {cls}: {count}")

# Near-miss analysis
near_misses = [(idx, trades[idx]) for idx, cls in loser_classifications.items() if cls == 'NEAR_MISS']
print(f"\n  NEAR_MISS detailed (MFE >= 1.0R but lost):")
for idx, trade in near_misses:
    print(f"    #{idx} {trade['date']}: MFE={trade['mfe_r']:.2f}R, final R={trade['r_multiple']:+.2f}, Would BE move at 1.0R have saved? ", end='')
    # Check
    path = trade_paths[idx]
    be_triggered = False
    for p in path[:trade['hold_time_candles']]:
        if p['r_high'] >= 1.0:
            be_triggered = True
        if be_triggered and p['r_low'] <= 0:
            print("YES (stopped at BE)")
            break
        if not be_triggered and p['r_low'] <= -1.0:
            print("NO (SL before BE trigger)")
            break
    else:
        print("MAYBE (timed out)")

# ─── ANALYSIS 3: Winner Anatomy ─────────────────────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 3: WINNER ANATOMY")
print("="*80)

winners = [(i, t) for i, t in enumerate(trades) if t['outcome'] == 'WIN']
print(f"\nTotal winners: {len(winners)}")

# Speed to profit milestones
milestones = [0.5, 1.0, 1.5, 2.0, 2.5]
milestone_times = {m: [] for m in milestones}

for idx, trade in winners:
    path = trade_paths[idx]
    if not path:
        continue
    for m in milestones:
        found = False
        for j, p in enumerate(path):
            if p['r_high'] >= m:
                milestone_times[m].append(j)
                found = True
                break
        if not found:
            milestone_times[m].append(None)

print("\n  Speed to profit milestones (candles):")
for m in milestones:
    times = [t for t in milestone_times[m] if t is not None]
    hit_count = len(times)
    if times:
        print(f"    {m}R: {hit_count}/{len(winners)} reached, avg {np.mean(times):.1f} candles (med {np.median(times):.0f})")
    else:
        print(f"    {m}R: 0/{len(winners)} reached")

# MAE on winners vs losers
winner_maes = [t['mae_r'] for _, t in winners]
loser_maes = [t['mae_r'] for _, t in losers]
print(f"\n  MAE comparison:")
print(f"    Winners avg MAE: {np.mean(winner_maes):.3f}R (med {np.median(winner_maes):.3f})")
print(f"    Losers avg MAE: {np.mean(loser_maes):.3f}R (med {np.median(loser_maes):.3f})")

# TP1 hit analysis
tp1_hits = [(i, t) for i, t in enumerate(trades) if 'TP1' in t.get('exit_substate', '')]
timeout_wins = [(i, t) for i, t in winners if 'TIMEOUT' in t.get('exit_substate', '')]
print(f"\n  TP1 hits: {len(tp1_hits)}, Timeout wins: {len(timeout_wins)}")

# What distinguishes TP1 hits from timeout wins?
if tp1_hits:
    tp1_mfes = [t['mfe_r'] for _, t in tp1_hits]
    timeout_mfes = [t['mfe_r'] for _, t in timeout_wins]
    tp1_plcs = [t['confidence_metrics']['price_level_count'] for _, t in tp1_hits]
    timeout_plcs = [t['confidence_metrics']['price_level_count'] for _, t in timeout_wins]
    print(f"  TP1 hits: avg MFE={np.mean(tp1_mfes):.2f}R, avg PLC={np.mean(tp1_plcs):.1f}")
    if timeout_mfes:
        print(f"  Timeout wins: avg MFE={np.mean(timeout_mfes):.2f}R, avg PLC={np.mean(timeout_plcs):.1f}")

# Golden window analysis
print("\n  Golden Window Analysis:")
for window in [4, 6, 8, 10]:
    profitable_at_window = 0
    total_checked = 0
    eventual_wins = 0
    eventual_losses = 0

    for i, trade in enumerate(trades):
        path = trade_paths[i]
        if not path or len(path) < window:
            continue
        total_checked += 1
        r_at_window = path[window-1]['r_close']
        if r_at_window > 0:
            profitable_at_window += 1
            if trade['outcome'] == 'WIN':
                eventual_wins += 1
        else:
            if trade['outcome'] == 'LOSS':
                eventual_losses += 1

    profitable_win_rate = eventual_wins / profitable_at_window * 100 if profitable_at_window > 0 else 0
    print(f"    Candle {window}: {profitable_at_window}/{total_checked} profitable → {profitable_win_rate:.0f}% become wins")

# ─── ANALYSIS 4: Session Memory Effectiveness ───────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 4: SESSION MEMORY EFFECTIVENESS")
print("="*80)

# Patience effect
patience_groups = {'low': [], 'medium': [], 'high': []}
for trade in trades:
    n_prior = trade.get('candles_evaluated_before_entry', 1) - 1  # subtract the entry candle
    if n_prior <= 2:
        patience_groups['low'].append(trade)
    elif n_prior <= 5:
        patience_groups['medium'].append(trade)
    else:
        patience_groups['high'].append(trade)

print("\n  Patience Effect (prior NO_TRADE evaluations):")
for group, trades_in_group in patience_groups.items():
    if not trades_in_group:
        continue
    wins = sum(1 for t in trades_in_group if t['outcome'] == 'WIN')
    total = len(trades_in_group)
    avg_r = np.mean([t['r_multiple'] for t in trades_in_group])
    total_r = sum(t['r_multiple'] for t in trades_in_group)
    print(f"    {group} patience ({len(trades_in_group)} trades): WR={wins/total*100:.1f}%, AvgR={avg_r:+.2f}, TotalR={total_r:+.2f}")

# Rejection reason patterns
rejection_reasons = defaultdict(list)
for trade in trades:
    for mem in trade.get('session_memory_at_entry', []):
        if mem['decision'] == 'NO_TRADE':
            summary = mem['summary']
            if 'U3' in summary or 'CHoCH' in summary or 'displacement' in summary.lower():
                reason = 'U3_failure'
            elif 'U4' in summary:
                reason = 'U4_failure'
            elif 'conflict' in summary.lower() or 'bias' in summary.lower():
                reason = 'bias_conflict'
            else:
                reason = 'other'
            rejection_reasons[reason].append(trade['date'])

print("\n  Rejection reason frequency:")
for reason, dates in rejection_reasons.items():
    print(f"    {reason}: {len(dates)} occurrences")

# First-candle entries
first_candle = [t for t in trades if t.get('candles_evaluated_before_entry', 0) <= 1]
later_candle = [t for t in trades if t.get('candles_evaluated_before_entry', 0) > 1]
print(f"\n  First-candle entries ({len(first_candle)} trades):")
if first_candle:
    wins_fc = sum(1 for t in first_candle if t['outcome'] == 'WIN')
    print(f"    WR={wins_fc/len(first_candle)*100:.1f}%, AvgR={np.mean([t['r_multiple'] for t in first_candle]):+.2f}")
print(f"  Later entries ({len(later_candle)} trades):")
if later_candle:
    wins_lc = sum(1 for t in later_candle if t['outcome'] == 'WIN')
    print(f"    WR={wins_lc/len(later_candle)*100:.1f}%, AvgR={np.mean([t['r_multiple'] for t in later_candle]):+.2f}")

# Same-day London → NY
print("\n  Same-day London → NY correlation:")
dates_with_both = defaultdict(dict)
for trade in trades:
    dates_with_both[trade['date']][trade['kill_zone']] = trade

for date, kz_trades in dates_with_both.items():
    if len(kz_trades) >= 2:
        ldn = kz_trades.get('london')
        ny = kz_trades.get('ny')
        if ldn and ny:
            print(f"    {date}: London R={ldn['r_multiple']:+.2f} ({ldn['outcome']}), NY R={ny['r_multiple']:+.2f} ({ny['outcome']})")

# ─── ANALYSIS 5: Confidence Metrics Deep Dive ───────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 5: CONFIDENCE METRICS DEEP DIVE")
print("="*80)

# Extract features
plcs = [t['confidence_metrics']['price_level_count'] for t in trades]
hss = [t['confidence_metrics']['hesitation_score'] for t in trades]
qss = [t['confidence_metrics']['quality_score'] for t in trades]
wcs = [t['confidence_metrics']['word_count'] for t in trades]
rs = [t['r_multiple'] for t in trades]
outcomes = [1 if t['outcome'] == 'WIN' else 0 for t in trades]

# Pearson correlations
from scipy import stats as scipy_stats

metrics = {'PLC': plcs, 'HS': hss, 'QS': qss, 'WordCount': wcs}
print("\n  Correlation with R-multiple:")
for name, values in metrics.items():
    try:
        r, p = scipy_stats.pearsonr(values, rs)
        print(f"    {name}: r={r:.3f}, p={p:.3f}")
    except:
        print(f"    {name}: insufficient variance")

print("\n  Correlation with Win (binary):")
for name, values in metrics.items():
    try:
        r, p = scipy_stats.pointbiserialr(outcomes, values)
        print(f"    {name}: r={r:.3f}, p={p:.3f}")
    except:
        print(f"    {name}: insufficient variance")

# Optimal thresholds
print("\n  Optimal thresholds:")
for name, values in metrics.items():
    unique_vals = sorted(set(values))
    best_split = None
    best_wr_diff = 0

    for cutoff in unique_vals:
        above = [rs[i] for i in range(len(values)) if values[i] >= cutoff]
        below = [rs[i] for i in range(len(values)) if values[i] < cutoff]

        if len(above) < 3 or len(below) < 3:
            continue

        wr_above = sum(1 for r in above if r > 0) / len(above)
        wr_below = sum(1 for r in below if r > 0) / len(below)
        exp_above = np.mean(above)
        exp_below = np.mean(below)

        diff = wr_above - wr_below
        if diff > best_wr_diff:
            best_wr_diff = diff
            best_split = {
                'cutoff': cutoff,
                'above_count': len(above), 'below_count': len(below),
                'wr_above': wr_above, 'wr_below': wr_below,
                'exp_above': exp_above, 'exp_below': exp_below
            }

    if best_split:
        s = best_split
        print(f"    {name} >= {s['cutoff']}: WR={s['wr_above']*100:.0f}% (n={s['above_count']}) vs <{s['cutoff']}: WR={s['wr_below']*100:.0f}% (n={s['below_count']})")
        print(f"      Exp: {s['exp_above']:+.3f}R vs {s['exp_below']:+.3f}R")

# Confidence grade analysis
grades = defaultdict(list)
for t in trades:
    grades[t['confidence_metrics']['confidence_grade']].append(t)

print("\n  By confidence grade:")
for grade in ['HIGH', 'MEDIUM']:
    if grade in grades:
        g = grades[grade]
        wins = sum(1 for t in g if t['outcome'] == 'WIN')
        avg_r = np.mean([t['r_multiple'] for t in g])
        print(f"    {grade}: {len(g)} trades, WR={wins/len(g)*100:.1f}%, AvgR={avg_r:+.2f}")

# Proposed composite score
print("\n  Proposed composite score:")
print("    Formula: score = (PLC * 5) + ((2 - HS) * 10) + ((2 - QS) * 5) + max(0, (40 - word_count))")
composite_scores = []
for t in trades:
    cm = t['confidence_metrics']
    score = (cm['price_level_count'] * 5) + ((2 - cm['hesitation_score']) * 10) + ((2 - cm['quality_score']) * 5) + max(0, (40 - cm['word_count']))
    composite_scores.append(score)

median_score = np.median(composite_scores)
above_median = [trades[i] for i in range(len(trades)) if composite_scores[i] >= median_score]
below_median = [trades[i] for i in range(len(trades)) if composite_scores[i] < median_score]
wr_above = sum(1 for t in above_median if t['outcome'] == 'WIN') / len(above_median) * 100 if above_median else 0
wr_below = sum(1 for t in below_median if t['outcome'] == 'WIN') / len(below_median) * 100 if below_median else 0
print(f"    Median score: {median_score:.0f}")
print(f"    Above median: {len(above_median)} trades, WR={wr_above:.1f}%")
print(f"    Below median: {len(below_median)} trades, WR={wr_below:.1f}%")

# ─── ANALYSIS 6: AI Reasoning Text Mining ───────────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 6: AI REASONING TEXT MINING")
print("="*80)

# Extract reasoning from session memory
winner_reasons = []
loser_reasons = []
for t in trades:
    text = t.get('session_memory_formatted', '')
    if t['outcome'] == 'WIN':
        winner_reasons.append(text)
    elif t['outcome'] == 'LOSS':
        loser_reasons.append(text)

# Word frequency analysis
def extract_key_phrases(texts):
    phrases = Counter()
    for text in texts:
        text_lower = text.lower()
        keywords = [
            'strong displacement', 'clean break', 'institutional', 'perfect',
            'clear', 'aggressive', 'sharp', 'significant', 'solid', 'valid',
            'possible', 'moderate', 'not ideal', 'concerns', 'weak',
            'conflict', 'missing', 'failed', 'violation', 'below',
            'choch', 'bos', 'displacement', 'ob retest', 'fair value gap',
            'bullish', 'bearish', 'premium', 'discount'
        ]
        for kw in keywords:
            if kw in text_lower:
                phrases[kw] += 1
    return phrases

winner_phrases = extract_key_phrases(winner_reasons)
loser_phrases = extract_key_phrases(loser_reasons)

print("\n  Winner reasoning phrases:")
for phrase, count in winner_phrases.most_common(15):
    print(f"    '{phrase}': {count}")

print("\n  Loser reasoning phrases:")
for phrase, count in loser_phrases.most_common(15):
    print(f"    '{phrase}': {count}")

# Reasoning length
winner_lengths = [len(t.get('session_memory_formatted', '')) for t in trades if t['outcome'] == 'WIN']
loser_lengths = [len(t.get('session_memory_formatted', '')) for t in trades if t['outcome'] == 'LOSS']
print(f"\n  Reasoning length:")
print(f"    Winners avg: {np.mean(winner_lengths):.0f} chars (med {np.median(winner_lengths):.0f})")
print(f"    Losers avg: {np.mean(loser_lengths):.0f} chars (med {np.median(loser_lengths):.0f})")

# ─── ANALYSIS 7: Temporal Patterns ──────────────────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 7: TEMPORAL PATTERNS")
print("="*80)

# Day of week
dow_trades = defaultdict(list)
for t in trades:
    dt = pd.Timestamp(t['candle_time'])
    dow = dt.strftime('%A')
    dow_trades[dow].append(t)

print("\n  Day of week:")
for dow in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
    if dow in dow_trades:
        ts = dow_trades[dow]
        wins = sum(1 for t in ts if t['outcome'] == 'WIN')
        total_r = sum(t['r_multiple'] for t in ts)
        print(f"    {dow}: {len(ts)} trades, WR={wins/len(ts)*100:.0f}%, TotalR={total_r:+.2f}")

# Kill zone analysis
kz_trades = defaultdict(list)
for t in trades:
    kz_trades[t['kill_zone']].append(t)

print("\n  Kill zone:")
for kz in ['london', 'ny']:
    ts = kz_trades[kz]
    wins = sum(1 for t in ts if t['outcome'] == 'WIN')
    total_r = sum(t['r_multiple'] for t in ts)
    avg_r = np.mean([t['r_multiple'] for t in ts])
    print(f"    {kz}: {len(ts)} trades, WR={wins/len(ts)*100:.0f}%, TotalR={total_r:+.2f}, AvgR={avg_r:+.2f}")

# Monthly
monthly = defaultdict(list)
for t in trades:
    dt = pd.Timestamp(t['candle_time'])
    month_key = dt.strftime('%Y-%m')
    monthly[month_key].append(t)

print("\n  Monthly breakdown:")
for month in sorted(monthly.keys()):
    ts = monthly[month]
    wins = sum(1 for t in ts if t['outcome'] == 'WIN')
    total_r = sum(t['r_multiple'] for t in ts)
    print(f"    {month}: {len(ts)} trades, W={wins}, TotalR={total_r:+.2f}")

# Quarterly
quarterly = defaultdict(list)
for t in trades:
    dt = pd.Timestamp(t['candle_time'])
    q = f"{dt.year}-Q{(dt.month-1)//3+1}"
    quarterly[q].append(t)

print("\n  Quarterly breakdown:")
for q in sorted(quarterly.keys()):
    ts = quarterly[q]
    wins = sum(1 for t in ts if t['outcome'] == 'WIN')
    total_r = sum(t['r_multiple'] for t in ts)
    print(f"    {q}: {len(ts)} trades, W={wins}, TotalR={total_r:+.2f}")

# Consecutive patterns
print("\n  Consecutive trade patterns:")
streak = 0
max_win_streak = 0
max_loss_streak = 0
current_streak_type = None

for t in trades:
    if t['outcome'] == 'WIN':
        if current_streak_type == 'WIN':
            streak += 1
        else:
            streak = 1
            current_streak_type = 'WIN'
        max_win_streak = max(max_win_streak, streak)
    elif t['outcome'] == 'LOSS':
        if current_streak_type == 'LOSS':
            streak += 1
        else:
            streak = 1
            current_streak_type = 'LOSS'
        max_loss_streak = max(max_loss_streak, streak)
    else:
        streak = 0
        current_streak_type = None

print(f"    Max win streak: {max_win_streak}")
print(f"    Max loss streak: {max_loss_streak}")

# After-win and after-loss performance
print("\n  Performance after prior outcome:")
after_win = []
after_loss = []
for i in range(1, len(trades)):
    if trades[i-1]['outcome'] == 'WIN':
        after_win.append(trades[i])
    elif trades[i-1]['outcome'] == 'LOSS':
        after_loss.append(trades[i])

if after_win:
    aw_wr = sum(1 for t in after_win if t['outcome'] == 'WIN') / len(after_win) * 100
    print(f"    After WIN ({len(after_win)} trades): WR={aw_wr:.0f}%, AvgR={np.mean([t['r_multiple'] for t in after_win]):+.2f}")
if after_loss:
    al_wr = sum(1 for t in after_loss if t['outcome'] == 'WIN') / len(after_loss) * 100
    print(f"    After LOSS ({len(after_loss)} trades): WR={al_wr:.0f}%, AvgR={np.mean([t['r_multiple'] for t in after_loss]):+.2f}")

# ─── ANALYSIS 8: Cross-Trade Feature Engineering ────────────────────────────

print("\n" + "="*80)
print("ANALYSIS 8: CROSS-TRADE FEATURE ENGINEERING")
print("="*80)

# Build feature matrix
features_data = []
for t in trades:
    dt = pd.Timestamp(t['candle_time'])
    sl_dist = abs(t['entry_price'] - t['stop_loss'])
    sl_pct = sl_dist / t['entry_price'] * 100

    features_data.append({
        'date': t['date'],
        'kill_zone': t['kill_zone'],
        'setup_grade': t['setup_grade'],
        'confidence_score': t['confidence_score'],
        'plc': t['confidence_metrics']['price_level_count'],
        'hs': t['confidence_metrics']['hesitation_score'],
        'qs': t['confidence_metrics']['quality_score'],
        'wc': t['confidence_metrics']['word_count'],
        'candles_before': t.get('candles_evaluated_before_entry', 0),
        'sl_distance': sl_dist,
        'sl_pct': sl_pct,
        'day_of_week': dt.dayofweek,
        'entry_hour': dt.hour,
        'hold_candles': t['hold_time_candles'],
        'mfe_r': t['mfe_r'],
        'mae_r': t['mae_r'],
        'r_multiple': t['r_multiple'],
        'outcome': t['outcome'],
        'is_win': 1 if t['outcome'] == 'WIN' else 0
    })

df = pd.DataFrame(features_data)

# Feature importance by median split
numeric_features = ['plc', 'hs', 'qs', 'wc', 'candles_before', 'sl_distance', 'sl_pct', 'entry_hour', 'confidence_score']

print("\n  Feature splits by median:")
feature_importance = []
for feat in numeric_features:
    med = df[feat].median()
    above = df[df[feat] >= med]
    below = df[df[feat] < med]

    if len(above) < 3 or len(below) < 3:
        continue

    wr_above = above['is_win'].mean() * 100
    wr_below = below['is_win'].mean() * 100
    exp_above = above['r_multiple'].mean()
    exp_below = below['r_multiple'].mean()

    wr_diff = abs(wr_above - wr_below)
    exp_diff = abs(exp_above - exp_below)

    feature_importance.append({
        'feature': feat, 'median': med,
        'wr_above': wr_above, 'wr_below': wr_below,
        'exp_above': exp_above, 'exp_below': exp_below,
        'wr_diff': wr_diff, 'exp_diff': exp_diff
    })

    print(f"    {feat} (med={med:.1f}): Above WR={wr_above:.0f}% Exp={exp_above:+.2f} | Below WR={wr_below:.0f}% Exp={exp_below:+.2f} | Diff={wr_diff:.0f}%")

# Sort by WR difference
feature_importance.sort(key=lambda x: x['wr_diff'], reverse=True)
print(f"\n  Top 3 most predictive features (by WR split):")
for fi in feature_importance[:3]:
    print(f"    {fi['feature']}: {fi['wr_diff']:.0f}% WR difference")

# Kill zone split
print(f"\n  Kill zone split:")
for kz in ['london', 'ny']:
    subset = df[df['kill_zone'] == kz]
    print(f"    {kz}: {len(subset)} trades, WR={subset['is_win'].mean()*100:.0f}%, AvgR={subset['r_multiple'].mean():+.2f}")

# Setup grade split
print(f"\n  Setup grade split:")
for grade in ['A+', 'A']:
    subset = df[df['setup_grade'] == grade]
    if len(subset) > 0:
        print(f"    {grade}: {len(subset)} trades, WR={subset['is_win'].mean()*100:.0f}%, AvgR={subset['r_multiple'].mean():+.2f}")

# ─── Compute baseline stats ─────────────────────────────────────────────────

print("\n" + "="*80)
print("BASELINE STATISTICS")
print("="*80)

total_trades = len(trades)
wins = sum(1 for t in trades if t['outcome'] == 'WIN')
losses = sum(1 for t in trades if t['outcome'] == 'LOSS')
bes = sum(1 for t in trades if t['outcome'] == 'BREAKEVEN')
all_r = [t['r_multiple'] for t in trades]
win_r = [t['r_multiple'] for t in trades if t['outcome'] == 'WIN']
loss_r = [t['r_multiple'] for t in trades if t['outcome'] == 'LOSS']

print(f"  Total: {total_trades} trades (W={wins}, L={losses}, BE={bes})")
print(f"  Win Rate: {wins/total_trades*100:.1f}%")
print(f"  Avg Win: {np.mean(win_r):+.2f}R")
print(f"  Avg Loss: {np.mean(loss_r):+.2f}R")
print(f"  Expectancy: {np.mean(all_r):+.3f}R")
print(f"  Total R: {sum(all_r):+.2f}R")
print(f"  Avg MFE: {np.mean([t['mfe_r'] for t in trades]):.2f}R")
print(f"  Avg MAE: {np.mean([t['mae_r'] for t in trades]):.2f}R")

# Exit type breakdown
exit_types = Counter(t['exit_substate'] for t in trades)
print(f"\n  Exit types:")
for et, count in exit_types.most_common():
    subset = [t for t in trades if t['exit_substate'] == et]
    avg_r = np.mean([t['r_multiple'] for t in subset])
    print(f"    {et}: {count} ({count/total_trades*100:.0f}%), AvgR={avg_r:+.2f}")

# ─── Save all data ──────────────────────────────────────────────────────────

timestamp = datetime.now().strftime('%Y%m%d_%H%M')

output_data = {
    'metadata': {
        'timestamp': timestamp,
        'total_trades': total_trades,
        'baseline': {
            'wins': wins, 'losses': losses, 'breakevens': bes,
            'win_rate': wins/total_trades*100,
            'avg_win': float(np.mean(win_r)),
            'avg_loss': float(np.mean(loss_r)),
            'expectancy': float(np.mean(all_r)),
            'total_r': float(sum(all_r))
        }
    },
    'exit_optimization': {
        'be_move': {str(k): v for k, v in be_results.items()},
        'trailing_stop': {str(k): v for k, v in trail_results.items()},
        'fixed_tp': {str(k): v for k, v in fixed_tp_results.items()},
        'partial_close': partial_results
    },
    'loser_classifications': {str(k): v for k, v in loser_classifications.items()},
    'feature_importance': feature_importance,
    'per_trade_data': []
}

for i, (trade, path) in enumerate(zip(trades, trade_paths)):
    trade_data = {
        'index': i,
        'date': trade['date'],
        'kill_zone': trade['kill_zone'],
        'outcome': trade['outcome'],
        'r_multiple': trade['r_multiple'],
        'mfe_r': trade['mfe_r'],
        'mae_r': trade['mae_r'],
        'mfe_candle_index': mfe_candle_indices[i],
        'loser_classification': loser_classifications.get(i, None),
        'r_path_first_20': [{'r_close': p['r_close'], 'r_high': p['r_high'], 'r_low': p['r_low']} for p in path[:20]] if path else []
    }
    output_data['per_trade_data'].append(trade_data)

data_file = f'knowledge_base_backtest/analysis/deep_trade_analysis_data_{timestamp}.json'
with open(data_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"\n\nData saved to: {data_file}")
print("Script complete. Use output to generate report.")
