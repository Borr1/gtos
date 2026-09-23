"""
TEST: BE Stop Trigger Optimization
CLAIM: Multiple sources (videos 16, 18, 23) say move SL to breakeven at 3R MFE, not earlier.
OUR DATA: 19 CLOSED_BE trades have avg MFE=1.01R — we're moving to BE at ~1R.
QUESTION: What is the optimal MFE level to trigger BE stop?

This test simulates different BE trigger levels on our 100 historical trades
using MFE/MAE data to estimate outcomes.
"""
import json, glob, os
import numpy as np
from collections import defaultdict

project = '/Users/borr/Documents/trading/gold-agent'
sessions = sorted(glob.glob(f'{project}/knowledge_base_backtest/sessions/*.json'))

trades = []
for s in sessions:
    d = json.load(open(s))
    for t in d.get('trade_summary', {}).get('trades', []):
        trades.append(t)

print(f"Total trades: {len(trades)}")
print(f"="*70)

# Current system: BE appears to trigger around 1R MFE
# Test: what if we moved BE trigger to different levels?

# For each trade, we have:
#   mfe_r: maximum favorable excursion in R
#   mae_r: maximum adverse excursion in R
#   r_multiple: actual final R result
#   outcome: WIN/LOSS
#   exit_substate: how the trade actually exited

# Simulation logic:
# If MFE >= trigger_level before MAE >= 1R (SL hit):
#   - SL moves to BE (0R)
#   - Trade can still win (close at final r_multiple) or close at BE (0R)
#   - Worst case after BE trigger is 0R (not -1R)
# If MFE < trigger_level: trade plays out normally

print("\nBE TRIGGER OPTIMIZATION")
print("-"*70)
print(f"{'BE Trigger':>12} {'Trades Hit':>12} {'Avg R':>10} {'Total R':>10} {'WR':>8} {'Expectancy':>12}")
print("-"*70)

results = {}

for trigger in [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 999]:  # 999 = no BE
    simulated_results = []
    trades_triggered = 0

    for t in trades:
        mfe = t['mfe_r']
        mae = t['mae_r']
        actual_r = t['r_multiple']
        outcome = t['outcome']

        if trigger >= 999:
            # No BE stop at all — use actual results
            simulated_results.append(actual_r)
            continue

        if mfe >= trigger:
            # BE would trigger
            trades_triggered += 1
            # After BE trigger, worst case is 0R
            # The trade's actual R is the best estimate of final outcome
            # But if actual R < 0, BE would have saved it → 0R
            if actual_r < 0:
                simulated_results.append(0.0)  # Saved by BE
            else:
                simulated_results.append(actual_r)  # Normal win
        else:
            # MFE never reached trigger — trade plays out normally
            simulated_results.append(actual_r)

    arr = np.array(simulated_results)
    avg_r = arr.mean()
    total_r = arr.sum()
    wr = (arr > 0).sum() / len(arr)

    label = f"{trigger}R" if trigger < 999 else "No BE"
    results[trigger] = {'avg_r': avg_r, 'total_r': total_r, 'wr': wr, 'triggered': trades_triggered}

    print(f"{label:>12} {trades_triggered:>12} {avg_r:>10.3f} {total_r:>10.1f} {wr:>7.1%} {avg_r:>12.3f}")

print("-"*70)

# Find optimal
best_trigger = max(results.keys(), key=lambda k: results[k]['total_r'])
best_label = f"{best_trigger}R" if best_trigger < 999 else "No BE"
current_r = results.get(1.0, results.get(0.75, {}))

print(f"\nCurrent system (BE ~1R): Total R = {results[1.0]['total_r']:.1f}")
print(f"Best trigger ({best_label}): Total R = {results[best_trigger]['total_r']:.1f}")
improvement = results[best_trigger]['total_r'] - results[1.0]['total_r']
print(f"Improvement: {improvement:+.1f}R ({improvement/max(0.01,abs(results[1.0]['total_r']))*100:+.1f}%)")

# Detailed look at trades where BE fires at 1R but loses value
print(f"\n{'='*70}")
print("DEEP DIVE: Trades where BE triggers at 1R MFE")
print("-"*70)

be_at_1r = [t for t in trades if t['mfe_r'] >= 1.0]
print(f"Trades reaching 1R MFE: {len(be_at_1r)}")
for t in sorted(be_at_1r, key=lambda x: x['r_multiple']):
    status = t['exit_substate']
    print(f"  MFE={t['mfe_r']:.2f}R  MAE={t['mae_r']:.2f}R  Final={t['r_multiple']:+.2f}R  Exit={status}")

# Key insight: how many trades reach 1R MFE but end negative?
reach_1r_lose = [t for t in trades if t['mfe_r'] >= 1.0 and t['r_multiple'] < 0]
reach_3r_lose = [t for t in trades if t['mfe_r'] >= 3.0 and t['r_multiple'] < 0]
print(f"\nTradesreaching 1R MFE then going negative: {len(reach_1r_lose)}")
print(f"Trades reaching 3R MFE then going negative: {len(reach_3r_lose)}")

print(f"\n{'='*70}")
print("DECISION GATE:")
if improvement > 5:
    print(f"  CONFIRMED: Moving BE trigger from 1R to {best_label} improves total R by {improvement:.1f}")
    print(f"  ACTION: Adjust trade_manager BE trigger parameter")
elif improvement > 0:
    print(f"  MARGINAL: {best_label} is slightly better ({improvement:+.1f}R) but small sample")
    print(f"  ACTION: Monitor during WF-1, test with larger dataset")
else:
    print(f"  REJECTED: Current 1R trigger is already optimal or near-optimal")
