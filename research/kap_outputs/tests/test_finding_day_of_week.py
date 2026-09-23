"""
TEST: Day-of-week performance
FINDING: "Monday is the worst day: 22% WR (18 trades); Tuesday-Thursday best"
  (Eddy Pips Trading, 100-trade backtest)
OUR DATA: No day-of-week analysis done yet on batch trades
PRIORITY: 4 (directly testable, could inform session scheduling)

Tests our 331 sessions for day-of-week effects.
"""
import json, glob
import numpy as np
from collections import defaultdict
from scipy.stats import chi2_contingency, fisher_exact

sessions = sorted(glob.glob('knowledge_base_backtest/sessions/*.json'))

day_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'r_sum': 0, 'trades': []})

for sf in sessions:
    s = json.load(open(sf))
    dow = s.get('day_of_week', '')
    ts = s.get('trade_summary', {})
    t_list = ts.get('trades', [])
    if not isinstance(t_list, list):
        t_list = [t_list] if t_list else []

    for t in t_list:
        if not isinstance(t, dict) or not t.get('outcome'):
            continue
        r = t.get('r_multiple', 0) or 0
        day_stats[dow]['r_sum'] += r
        day_stats[dow]['trades'].append(t)
        if t['outcome'] == 'WIN':
            day_stats[dow]['wins'] += 1
        else:
            day_stats[dow]['losses'] += 1

print(f"{'='*60}")
print("DAY-OF-WEEK ANALYSIS — BATCH TRADES")
print(f"{'='*60}\n")

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
table_data = []

for d in day_order:
    stats = day_stats.get(d, {'wins': 0, 'losses': 0, 'r_sum': 0, 'trades': []})
    total = stats['wins'] + stats['losses']
    wr = stats['wins'] / total if total > 0 else 0
    avg_r = stats['r_sum'] / total if total > 0 else 0
    table_data.append((d, stats['wins'], stats['losses'], total, wr, avg_r))
    print(f"{d:12s}: {wr:5.1%} WR ({total:3d} trades), "
          f"W={stats['wins']:2d} L={stats['losses']:2d}, avg R={avg_r:+.3f}")

# Chi-squared test for overall day effect
print(f"\n{'='*60}")
print("STATISTICAL TESTS")
print(f"{'='*60}")

contingency = [[stats[0][1], stats[0][2]] for stats in
               [(d, day_stats[d]['wins'], day_stats[d]['losses'])
                for d in day_order if day_stats[d]['wins'] + day_stats[d]['losses'] > 0]]

if len(contingency) >= 2:
    # Reshape for chi2
    wins_losses = []
    for d in day_order:
        if day_stats[d]['wins'] + day_stats[d]['losses'] > 0:
            wins_losses.append([day_stats[d]['wins'], day_stats[d]['losses']])

    chi2, p_overall, dof, _ = chi2_contingency(wins_losses)
    print(f"Chi-squared (overall day effect): chi2={chi2:.2f}, p={p_overall:.4f}, dof={dof}")

# Monday vs Tue-Thu (Eddy Pips' specific claim)
mon = day_stats.get('Monday', {'wins': 0, 'losses': 0})
tue_thu = {'wins': 0, 'losses': 0}
for d in ['Tuesday', 'Wednesday', 'Thursday']:
    tue_thu['wins'] += day_stats.get(d, {'wins': 0})['wins']
    tue_thu['losses'] += day_stats.get(d, {'losses': 0})['losses']

if (mon['wins'] + mon['losses'] > 0) and (tue_thu['wins'] + tue_thu['losses'] > 0):
    _, p_mon = fisher_exact([
        [mon['wins'], mon['losses']],
        [tue_thu['wins'], tue_thu['losses']]
    ])
    mon_wr = mon['wins'] / (mon['wins'] + mon['losses'])
    tt_wr = tue_thu['wins'] / (tue_thu['wins'] + tue_thu['losses'])
    print(f"\nMonday vs Tue-Thu:")
    print(f"  Monday:  {mon_wr:.1%} (n={mon['wins']+mon['losses']})")
    print(f"  Tue-Thu: {tt_wr:.1%} (n={tue_thu['wins']+tue_thu['losses']})")
    print(f"  Fisher p={p_mon:.4f}")

# Friday check
fri = day_stats.get('Friday', {'wins': 0, 'losses': 0})
if fri['wins'] + fri['losses'] > 0:
    fri_wr = fri['wins'] / (fri['wins'] + fri['losses'])
    print(f"  Friday:  {fri_wr:.1%} (n={fri['wins']+fri['losses']})")

print(f"\n{'='*60}")
print("DECISION GATE")
print(f"{'='*60}")
print("CONFIRMED if: Monday WR significantly below Tue-Thu (p<0.05, gap>15pp)")
print("REJECTED if: p>0.10 or gap<5pp")
print("If confirmed → consider skipping Monday trades or requiring higher confidence")
