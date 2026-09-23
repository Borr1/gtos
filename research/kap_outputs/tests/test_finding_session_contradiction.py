"""
TEST: Session performance contradiction
FINDING: Lewis Kelly says London ≈ NY; Eddy Pips says NY > London (49% vs 38%)
OUR DATA: London 74% vs NY 60% (14pp gap)
PRIORITY: 4 (CONTRADICTORY)

This test resolves the contradiction by analyzing our 331 session files
with higher granularity: by quarter, by instrument, by day-of-week.
"""
import json, glob, os
from collections import defaultdict
import numpy as np

# Load all sessions
sessions = sorted(glob.glob('knowledge_base_backtest/sessions/*.json'))
print(f"Loading {len(sessions)} session files...")

trades = []
for sf in sessions:
    s = json.load(open(sf))
    ts = s.get('trade_summary', {})
    t_list = ts.get('trades', [])
    if not isinstance(t_list, list):
        t_list = [t_list] if t_list else []
    for t in t_list:
        if isinstance(t, dict) and t.get('outcome'):
            t['date'] = s.get('date', '')
            t['day_of_week'] = s.get('day_of_week', '')
            trades.append(t)

print(f"Total trades: {len(trades)}")

# Split by session
london = [t for t in trades if t.get('kill_zone', '').lower() == 'london']
ny = [t for t in trades if t.get('kill_zone', '').lower() in ('new_york', 'ny', 'newyork')]

def win_rate(trade_list):
    if not trade_list:
        return 0, 0
    wins = sum(1 for t in trade_list if t['outcome'] == 'WIN')
    return wins / len(trade_list), len(trade_list)

def mean_r(trade_list):
    rs = [t.get('r_multiple', 0) for t in trade_list if t.get('r_multiple') is not None]
    return np.mean(rs) if rs else 0

print(f"\n{'='*60}")
print("SESSION SPLIT ANALYSIS")
print(f"{'='*60}")

lwr, ln = win_rate(london)
nwr, nn = win_rate(ny)
print(f"London: {lwr:.1%} WR ({ln} trades), mean R: {mean_r(london):.3f}")
print(f"NY:     {nwr:.1%} WR ({nn} trades), mean R: {mean_r(ny):.3f}")
print(f"Gap:    {(lwr-nwr)*100:.1f}pp")

# Statistical test
from scipy.stats import fisher_exact
if ln > 0 and nn > 0:
    l_wins = sum(1 for t in london if t['outcome'] == 'WIN')
    l_losses = ln - l_wins
    n_wins = sum(1 for t in ny if t['outcome'] == 'WIN')
    n_losses = nn - n_wins
    _, pval = fisher_exact([[l_wins, l_losses], [n_wins, n_losses]])
    print(f"Fisher exact p-value: {pval:.4f}")

# By quarter
print(f"\n{'='*60}")
print("BY QUARTER")
print(f"{'='*60}")
quarters = defaultdict(lambda: {'london': [], 'ny': []})
for t in trades:
    date = t.get('date', '')
    if len(date) >= 7:
        month = int(date[5:7])
        year = date[:4]
        q = f"{year}-Q{(month-1)//3+1}"
        kz = t.get('kill_zone', '').lower()
        if kz == 'london':
            quarters[q]['london'].append(t)
        elif kz in ('new_york', 'ny', 'newyork'):
            quarters[q]['ny'].append(t)

for q in sorted(quarters.keys()):
    lwr_q, ln_q = win_rate(quarters[q]['london'])
    nwr_q, nn_q = win_rate(quarters[q]['ny'])
    gap = (lwr_q - nwr_q) * 100 if ln_q > 0 and nn_q > 0 else float('nan')
    print(f"{q}: London {lwr_q:.0%} (n={ln_q}) | NY {nwr_q:.0%} (n={nn_q}) | Gap: {gap:+.0f}pp")

# By day of week
print(f"\n{'='*60}")
print("BY DAY OF WEEK")
print(f"{'='*60}")
days = defaultdict(list)
for t in trades:
    dow = t.get('day_of_week', 'Unknown')
    days[dow].append(t)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
for d in day_order:
    if d in days:
        wr, n = win_rate(days[d])
        mr = mean_r(days[d])
        print(f"{d:12s}: {wr:.0%} WR (n={n:3d}), mean R: {mr:+.3f}")

# By MFE/MAE (exit quality)
print(f"\n{'='*60}")
print("EXIT QUALITY BY SESSION")
print(f"{'='*60}")
for label, group in [('London', london), ('NY', ny)]:
    mfes = [t.get('mfe_r', 0) for t in group if t.get('mfe_r') is not None]
    maes = [t.get('mae_r', 0) for t in group if t.get('mae_r') is not None]
    rs = [t.get('r_multiple', 0) for t in group if t.get('r_multiple') is not None]
    if mfes:
        capture = np.mean(rs) / np.mean(mfes) if np.mean(mfes) > 0 else 0
        print(f"{label}: avg MFE={np.mean(mfes):.2f}R, avg MAE={np.mean(maes):.2f}R, "
              f"avg R={np.mean(rs):.3f}, capture={capture:.0%}")

# Decision gate
print(f"\n{'='*60}")
print("DECISION GATE")
print(f"{'='*60}")
if ln >= 10 and nn >= 10:
    if pval < 0.05 and abs(lwr - nwr) > 0.10:
        print("CONFIRMED: Session gap is statistically significant (>10pp, p<0.05)")
        print("→ Contradiction RESOLVED in favor of our data")
        print("→ Lewis Kelly/Eddy Pips likely have different strategy/instrument mix")
    elif pval > 0.10 or abs(lwr - nwr) < 0.05:
        print("REJECTED: Session gap is NOT significant")
        print("→ Their claim of equal sessions may be correct for OB-retest strategies")
    else:
        print("INCONCLUSIVE: Marginal significance. Need more data from WF-1")
        print(f"  p={pval:.4f}, gap={abs(lwr-nwr)*100:.1f}pp")
else:
    print("INSUFFICIENT DATA for session comparison")
