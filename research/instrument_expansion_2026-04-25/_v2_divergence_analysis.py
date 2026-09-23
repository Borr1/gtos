"""Analyze v1 vs v2 structure detector divergences for GBPUSD."""
import json
from collections import Counter, defaultdict


# Note: symbol field is empty in the divergence log (regression bug — see CLAUDE.md item 4)
# But we can analyze the v1 vs v2 patterns globally.

div_file = 'shadow_logs/structure_detector_divergences.jsonl'

stats = defaultdict(lambda: defaultdict(int))
total = 0
by_v2_label = Counter()
by_v1_label = Counter()
total_divergences = 0
shorts_unlocked = 0

with open(div_file, 'r', encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        v1 = row.get('v1_direction', 'NA')
        v2 = row.get('v2_direction', 'NA')
        by_v1_label[v1] += 1
        by_v2_label[v2] += 1
        if v1 != v2:
            total_divergences += 1
            stats[v1][v2] += 1
            if v1 == 'bullish' and v2 == 'bearish':
                shorts_unlocked += 1

print(f'Total H1 windows logged: {total}')
print(f'Total v1!=v2 divergences: {total_divergences} ({total_divergences/total*100:.1f}%)')
print(f'  v1=bullish -> v2=bearish (SHORT unlocked): {shorts_unlocked}')
print()
print('v1 label distribution:')
for k, n in by_v1_label.most_common():
    print(f'  {k}: {n} ({n/total*100:.1f}%)')
print('v2 label distribution:')
for k, n in by_v2_label.most_common():
    print(f'  {k}: {n} ({n/total*100:.1f}%)')

print()
print('Transition matrix (v1 row -> v2 col):')
print(f'{"v1":15} {"bullish":>10} {"bearish":>10} {"transitional":>14}')
for v1 in ['bullish', 'bearish', 'transitional']:
    if v1 not in stats and v1 != by_v1_label.most_common()[0][0]:
        continue
    bull_v2 = stats.get(v1, {}).get('bullish', 0)
    bear_v2 = stats.get(v1, {}).get('bearish', 0)
    trans_v2 = stats.get(v1, {}).get('transitional', 0)
    same = by_v1_label[v1] - sum([bull_v2, bear_v2, trans_v2])
    # The "same" cases (v1 == v2) aren't in stats since we only count divergences
    print(f'{v1:15} {bull_v2:>10} {bear_v2:>10} {trans_v2:>14}  (divergences only)')
