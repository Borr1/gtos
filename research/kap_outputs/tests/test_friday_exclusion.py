"""
TEST: Friday Exclusion Confirmation
CLAIM: Video 24 says removing Fridays improved turtle soup WR from 61% to 67%.
OUR BATCH 1 DATA: Friday WR=47%, avg R=-0.10 (worst day).
QUESTION: Is Friday exclusion statistically significant on our data?
"""
import json, glob, os
import numpy as np
from scipy import stats

project = '/Users/borr/Documents/trading/gold-agent'
sessions = sorted(glob.glob(f'{project}/knowledge_base_backtest/sessions/*.json'))

trades = []
for s in sessions:
    d = json.load(open(s))
    for t in d.get('trade_summary', {}).get('trades', []):
        t['day_of_week'] = d.get('day_of_week', '')
        trades.append(t)

friday = [t for t in trades if t['day_of_week'] == 'Friday']
non_friday = [t for t in trades if t['day_of_week'] != 'Friday']

fri_wins = sum(1 for t in friday if t['outcome'] == 'WIN')
fri_total = len(friday)
nf_wins = sum(1 for t in non_friday if t['outcome'] == 'WIN')
nf_total = len(non_friday)

print(f"Friday: {fri_wins}/{fri_total} wins ({fri_wins/max(1,fri_total)*100:.1f}%)")
print(f"Non-Friday: {nf_wins}/{nf_total} wins ({nf_wins/max(1,nf_total)*100:.1f}%)")

# Fisher's exact test
contingency = [[fri_wins, fri_total - fri_wins],
               [nf_wins, nf_total - nf_wins]]
odds_ratio, p_value = stats.fisher_exact(contingency)
print(f"\nFisher's exact test: p={p_value:.4f}, OR={odds_ratio:.3f}")

# R-multiple comparison
fri_r = [t['r_multiple'] for t in friday]
nf_r = [t['r_multiple'] for t in non_friday]
t_stat, p_r = stats.ttest_ind(fri_r, nf_r)
print(f"R-multiple t-test: p={p_r:.4f}, t={t_stat:.3f}")
print(f"  Friday avg R: {np.mean(fri_r):.3f} ± {np.std(fri_r):.3f}")
print(f"  Non-Fri avg R: {np.mean(nf_r):.3f} ± {np.std(nf_r):.3f}")

# Total R impact
fri_total_r = sum(fri_r)
nf_total_r = sum(nf_r)
all_total_r = sum(t['r_multiple'] for t in trades)
print(f"\nTotal R with Fridays: {all_total_r:.2f}R ({len(trades)} trades)")
print(f"Total R without Fridays: {nf_total_r:.2f}R ({len(non_friday)} trades)")
print(f"Friday contribution: {fri_total_r:+.2f}R ({len(friday)} trades)")

# Day-by-day breakdown
print(f"\n{'Day':<12} {'Trades':>7} {'WR':>7} {'Avg R':>8} {'Total R':>9}")
print("-"*50)
for day in ['Monday','Tuesday','Wednesday','Thursday','Friday']:
    day_trades = [t for t in trades if t['day_of_week'] == day]
    if day_trades:
        wr = sum(1 for t in day_trades if t['outcome']=='WIN') / len(day_trades)
        avg_r = np.mean([t['r_multiple'] for t in day_trades])
        tot_r = sum(t['r_multiple'] for t in day_trades)
        print(f"{day:<12} {len(day_trades):>7} {wr:>6.1%} {avg_r:>8.3f} {tot_r:>+9.2f}")

print(f"\n{'='*60}")
print("DECISION GATE:")
if p_value < 0.05:
    print(f"  CONFIRMED (p={p_value:.4f}): Friday significantly underperforms")
    print(f"  Excluding Fridays saves {abs(fri_total_r):.1f}R over {len(friday)} trades")
    print(f"  ACTION: Add Friday filter to trade execution (WF-2)")
elif p_value < 0.10:
    print(f"  SUGGESTIVE (p={p_value:.4f}): Friday underperformance trend exists")
    print(f"  ACTION: Continue collecting Friday data during WF-1, retest at n=30+")
else:
    print(f"  INCONCLUSIVE (p={p_value:.4f}): Cannot confirm Friday effect")
    print(f"  ACTION: Need more Friday trades for statistical power")
