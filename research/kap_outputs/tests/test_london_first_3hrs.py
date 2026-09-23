"""
TEST: London First 3 Hours Performance
CLAIM: Video 24 says first 3 hours of London (3-6am ET / 07:00-10:00 UTC) contain
       the bulk of turtle soup profits on gold. Trading after hour 3 adds noise.
QUESTION: Do our London session trades in early hours outperform later ones?
"""
import json, glob, os
import numpy as np
from scipy import stats
from datetime import datetime

project = '/Users/borr/Documents/trading/gold-agent'
sessions = sorted(glob.glob(f'{project}/knowledge_base_backtest/sessions/*.json'))

early_trades = []  # First 3 hours
late_trades = []   # After 3 hours

for s in sessions:
    d = json.load(open(s))
    session_start = d.get('session_start_utc', '')

    for t in d.get('trade_summary', {}).get('trades', []):
        if t.get('kill_zone') != 'london':
            continue

        # Use trade_id to infer timing (bt_YYYY-MM-DD_london_NNN)
        trade_id = t.get('trade_id', '')
        trade_num = int(trade_id.split('_')[-1]) if trade_id else 0

        # Also use hold_time_candles as proxy
        # First trade of session is typically early
        # We'll use candle_evaluations to get actual timing
        t['session_date'] = d.get('date', '')
        t['trade_num'] = trade_num

        # Approximate: trade 001 = early, trade 002+ = potentially later
        # Better: check candle_evaluations for executed trades

        evals = d.get('candle_evaluations', [])
        trade_time = None
        for e in evals:
            if e.get('trade_id') == trade_id:
                trade_time = e.get('candle_time', '')
                break

        t['trade_time'] = trade_time

        if trade_time:
            try:
                hour = int(trade_time.split(' ')[1].split(':')[0]) if ' ' in trade_time else 0
                # London early = 07:00-10:00 UTC (3-6am ET)
                if 7 <= hour < 10:
                    early_trades.append(t)
                else:
                    late_trades.append(t)
            except:
                pass

print(f"London trades with timing: {len(early_trades) + len(late_trades)}")
print(f"  Early (07-10 UTC): {len(early_trades)}")
print(f"  Late (10+ UTC): {len(late_trades)}")

if early_trades and late_trades:
    early_r = [t['r_multiple'] for t in early_trades]
    late_r = [t['r_multiple'] for t in late_trades]

    early_wr = sum(1 for t in early_trades if t['outcome']=='WIN') / len(early_trades)
    late_wr = sum(1 for t in late_trades if t['outcome']=='WIN') / len(late_trades)

    print(f"\nEarly London:")
    print(f"  WR: {early_wr:.1%}")
    print(f"  Avg R: {np.mean(early_r):.3f}")
    print(f"  Total R: {sum(early_r):.2f}")
    print(f"  Avg MFE: {np.mean([t['mfe_r'] for t in early_trades]):.3f}")

    print(f"\nLate London:")
    print(f"  WR: {late_wr:.1%}")
    print(f"  Avg R: {np.mean(late_r):.3f}")
    print(f"  Total R: {sum(late_r):.2f}")
    print(f"  Avg MFE: {np.mean([t['mfe_r'] for t in late_trades]):.3f}")

    if len(early_r) >= 5 and len(late_r) >= 5:
        t_stat, p_val = stats.ttest_ind(early_r, late_r)
        print(f"\nt-test: t={t_stat:.3f}, p={p_val:.4f}")

    print(f"\n{'='*60}")
    print("DECISION GATE:")
    if len(early_r) >= 5 and len(late_r) >= 5:
        if p_val < 0.05 and np.mean(early_r) > np.mean(late_r):
            print(f"  CONFIRMED: Early London significantly outperforms")
            print(f"  ACTION: Weight London entries towards first 3 hours (WF-2)")
        elif np.mean(early_r) > np.mean(late_r) and p_val < 0.20:
            print(f"  SUGGESTIVE: Early London trends better but not significant (p={p_val:.4f})")
            print(f"  ACTION: Track timing data during WF-1")
        else:
            print(f"  INCONCLUSIVE: No clear early advantage (p={p_val:.4f})")
    else:
        print(f"  INSUFFICIENT DATA: Need more London trades with timing")
else:
    print("\nInsufficient data — cannot split London trades by timing")
    print("INCONCLUSIVE: Need trade-level timing in candle evaluations")

# Also check: all London trades regardless of timing split
all_london = early_trades + late_trades
if not all_london:
    # Fall back to all London trades
    for s in sessions:
        d = json.load(open(s))
        for t in d.get('trade_summary', {}).get('trades', []):
            if t.get('kill_zone') == 'london':
                all_london.append(t)

print(f"\nAll London trades: {len(all_london)}")
print(f"  WR: {sum(1 for t in all_london if t['outcome']=='WIN')/max(1,len(all_london)):.1%}")
print(f"  Avg R: {np.mean([t['r_multiple'] for t in all_london]):.3f}")
print(f"  Avg MFE: {np.mean([t['mfe_r'] for t in all_london]):.3f}")
