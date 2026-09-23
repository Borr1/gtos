"""
Test Finding F08: Is 3R fixed TP optimal?
Two independent backtests (Eddy Pips 100 trades, Trader Zan 2,310 trades) converge on 3R.
We test using actual MFE data from 100 batch trades.

Decision gate:
  - If 3R fixed produces higher expectancy than current variable TP → CONFIRMED
  - If 2R or current variable is better → REJECTED
  - Include profit factor and trade count at each level
"""
import json, glob, os
import numpy as np

# Load all trades
trades = []
for f in sorted(glob.glob('knowledge_base_backtest/sessions/*.json')):
    try:
        d = json.load(open(f))
        for t in d.get('trade_summary', {}).get('trades', []):
            t['_date'] = d.get('date', '')
            trades.append(t)
    except:
        pass

print(f"Total trades: {len(trades)}")
print(f"Trades with MFE: {sum(1 for t in trades if t.get('mfe_r') is not None)}")

# Simulate fixed TP at various R-multiples
# For each trade, if MFE >= target_R, it's a win at target_R
# If MFE < target_R, it's a loss at actual r_multiple (SL hit)
results = {}
for target_r in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    wins = 0
    losses = 0
    total_r = 0.0
    for t in trades:
        mfe = t.get('mfe_r', 0)
        if mfe is None:
            continue
        if mfe >= target_r:
            wins += 1
            total_r += target_r
        else:
            losses += 1
            # Use actual R outcome (negative for losses)
            actual_r = t.get('r_multiple', -1.0)
            if actual_r > 0:
                # Partial win - didn't reach target but was positive
                # At fixed TP, if MFE < target, price reversed → SL hit → -1R
                total_r -= 1.0
            else:
                total_r += actual_r  # actual loss

    n = wins + losses
    wr = wins / n * 100 if n > 0 else 0
    expectancy = total_r / n if n > 0 else 0
    gross_win = wins * target_r
    gross_loss = abs(total_r - gross_win) if total_r < gross_win else 0.01
    pf = gross_win / max(gross_loss, 0.01)

    results[target_r] = {
        'wins': wins, 'losses': losses, 'wr': wr,
        'expectancy': expectancy, 'total_r': total_r, 'pf': pf
    }

# Current system performance
current_wins = sum(1 for t in trades if t.get('outcome') == 'WIN')
current_total_r = sum(t.get('r_multiple', 0) for t in trades)
current_wr = current_wins / len(trades) * 100
current_exp = current_total_r / len(trades)

print(f"\n{'='*70}")
print(f"RR OPTIMIZER RESULTS (n={len(trades)} trades)")
print(f"{'='*70}")
print(f"\nCurrent system (variable TP):")
print(f"  WR: {current_wr:.1f}%  Expectancy: {current_exp:.3f}R  Total: {current_total_r:.1f}R")

print(f"\n{'Target R':<10} {'WR%':<8} {'Wins':<6} {'Losses':<8} {'Expectancy':<12} {'Total R':<10} {'PF':<8}")
print("-" * 62)
for tr in sorted(results.keys()):
    r = results[tr]
    print(f"{tr:<10.1f} {r['wr']:<8.1f} {r['wins']:<6} {r['losses']:<8} {r['expectancy']:<12.3f} {r['total_r']:<10.1f} {r['pf']:<8.2f}")

# Find optimal
best_tr = max(results, key=lambda x: results[x]['expectancy'])
best = results[best_tr]
print(f"\n>>> OPTIMAL FIXED TP: {best_tr}R (expectancy {best['expectancy']:.3f}R, WR {best['wr']:.1f}%)")
print(f">>> vs Current: {current_exp:.3f}R expectancy")

if best['expectancy'] > current_exp:
    print(f"\n*** FINDING CONFIRMED: {best_tr}R fixed TP beats current variable by {best['expectancy'] - current_exp:.3f}R/trade ***")
else:
    print(f"\n*** FINDING REJECTED: Current variable TP ({current_exp:.3f}R) beats best fixed ({best_tr}R: {best['expectancy']:.3f}R) ***")

# Also check if 3R specifically is better than 2R (the claim)
if 3.0 in results and 2.0 in results:
    r3 = results[3.0]
    r2 = results[2.0]
    print(f"\n3R vs 2R comparison:")
    print(f"  3R: {r3['expectancy']:.3f}R expectancy, {r3['total_r']:.1f}R total, PF {r3['pf']:.2f}")
    print(f"  2R: {r2['expectancy']:.3f}R expectancy, {r2['total_r']:.1f}R total, PF {r2['pf']:.2f}")
    if r3['expectancy'] > r2['expectancy']:
        print("  >>> 3R > 2R CONFIRMED")
    else:
        print("  >>> 3R > 2R REJECTED")
