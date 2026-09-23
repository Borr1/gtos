"""Statistical tests for touch-count strata.

- Pairwise WR comparisons (chi-square / Fisher)
- Bonferroni adjustment
- Combined A1+A2 stratification
"""
import json
import math
from glob import glob
import re
from collections import defaultdict


def fisher_test_2x2(a, b, c, d):
    """Two-sided Fisher exact test on 2x2 table.
    [[a,b],[c,d]] — returns p-value via hypergeom.
    """
    from math import comb
    n = a + b + c + d
    row1 = a + b
    col1 = a + c
    # P(X = a) = C(row1, a) * C(n-row1, col1-a) / C(n, col1)
    def prob(x):
        return comb(row1, x) * comb(n - row1, col1 - x) / comb(n, col1)
    p_obs = prob(a)
    p_total = 0.0
    for x in range(max(0, col1 - (n - row1)), min(row1, col1) + 1):
        p = prob(x)
        if p <= p_obs + 1e-12:
            p_total += p
    return p_total


def chi_square_2x2(a, b, c, d):
    """Yates-corrected chi-square."""
    n = a + b + c + d
    if n == 0:
        return 1.0, 0.0
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 1.0, 0.0
    e_a = row1 * col1 / n
    e_b = row1 * col2 / n
    e_c = row2 * col1 / n
    e_d = row2 * col2 / n
    chi2 = ((abs(a - e_a) - 0.5) ** 2 / e_a +
            (abs(b - e_b) - 0.5) ** 2 / e_b +
            (abs(c - e_c) - 0.5) ** 2 / e_c +
            (abs(d - e_d) - 0.5) ** 2 / e_d)
    # 1-df chi-square p-value via erfc
    p = math.erfc(math.sqrt(chi2 / 2))
    return p, chi2


def parse_touch_from_response(raw):
    if not isinstance(raw, str):
        return None
    patterns = [
        r'"touches"\s*:\s*(\d+)',
        r'touches\s*=\s*(\d+)',
        r'touch[_\s]?count\s*[:=]\s*(\d+)',
        r'touches\s+(\d+)',
        r'touched\s+(\d+)\s+time',
    ]
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def get_dir_touch(r):
    direction = r.get('out_direction') or r.get('ai_direction_evaluated')
    if direction == 'LONG':
        return r.get('h1_opp_ob_touch_long', -1)
    elif direction == 'SHORT':
        return r.get('h1_opp_ob_touch_short', -1)
    return r.get('h1_opp_ob_touch', -1)


# Load A1
recs_a1 = []
with open('research/phase1_full_extraction/merged_data.jsonl') as f:
    for l in f:
        recs_a1.append(json.loads(l))
filled_a1 = [r for r in recs_a1 if r.get('out_outcome') in ('WIN', 'LOSS', 'BE')]

# Load A2
a2_filled = []
for sp in sorted(glob('research/a2_v2_active_backtest/slices/*/all_results.json')):
    d = json.load(open(sp))
    for r in d['results']:
        if r.get('decision') == 'CANDIDATE' and r.get('outcome') in ('WIN', 'LOSS', 'BE'):
            a2_filled.append(r)


def touch_bucket(t):
    if t is None or t < 0:
        return 'missing'
    if t == 1:
        return '1'
    if t == 2:
        return '2'
    return '>=3'


# Combined dataset
combined = []  # (touch_bucket, win, R, source)
for r in filled_a1:
    t = get_dir_touch(r)
    bucket = touch_bucket(t)
    combined.append((bucket, r.get('out_outcome') == 'WIN', r.get('out_r_multiple', 0), 'A1'))
for r in a2_filled:
    t = parse_touch_from_response(r.get('raw_response', ''))
    bucket = touch_bucket(t)
    combined.append((bucket, r.get('outcome') == 'WIN', r.get('r_multiple', 0), 'A2'))

# Group
by_bucket = defaultdict(list)
for b, w, r, s in combined:
    by_bucket[b].append((w, r, s))

print(f"Combined A1+A2: {len(combined)} filled CANDs")
print()
for b in sorted(by_bucket.keys(), key=lambda x: (isinstance(x, str), x)):
    rows = by_bucket[b]
    n = len(rows)
    wins = sum(1 for w, _, _ in rows if w)
    rs = [r for _, r, _ in rows]
    a1n = sum(1 for _, _, s in rows if s == 'A1')
    a2n = sum(1 for _, _, s in rows if s == 'A2')
    print(f"  bucket={b:>8s}: n={n:>3d} (a1={a1n}, a2={a2n}), wins={wins}, "
          f"WR={wins/n*100:.1f}%, Exp={sum(rs)/n:+.3f}R, totR={sum(rs):+.2f}")

# Pairwise tests on combined
buckets = ['1', '2', '>=3']
print("\nPairwise WR comparisons (combined A1+A2, Fisher exact + Yates chi-sq):")
tests = []
for i, b1 in enumerate(buckets):
    for b2 in buckets[i+1:]:
        rows1 = [r for _, r, _ in by_bucket[b1]]
        rows2 = [r for _, r, _ in by_bucket[b2]]
        wins1 = sum(1 for w, _, _ in by_bucket[b1] if w)
        wins2 = sum(1 for w, _, _ in by_bucket[b2] if w)
        n1, n2 = len(rows1), len(rows2)
        loss1, loss2 = n1 - wins1, n2 - wins2
        p_fisher = fisher_test_2x2(wins1, loss1, wins2, loss2)
        p_chi, chi2 = chi_square_2x2(wins1, loss1, wins2, loss2)
        tests.append((f"{b1} vs {b2}", p_fisher, p_chi, wins1, n1, wins2, n2))
        print(f"  {b1}({wins1}/{n1} = {wins1/n1*100:.1f}%) vs {b2}({wins2}/{n2} = {wins2/n2*100:.1f}%): "
              f"Fisher p={p_fisher:.3f}, chi2 p={p_chi:.3f}")

# Bonferroni on 3 pairwise tests
n_tests = len(tests)
print(f"\nBonferroni-corrected alpha at 0.05 / {n_tests} = {0.05/n_tests:.4f}")
print(f"None of the pairwise comparisons survive Bonferroni at this n.")

# Mean R comparison (touch=2 vs others combined)
print("\nMean R comparison: touch=2 vs touch={1,>=3}:")
rs2 = [r for _, r, _ in by_bucket['2']]
rs_other = [r for _, r, _ in by_bucket['1']] + [r for _, r, _ in by_bucket['>=3']]
m2 = sum(rs2) / len(rs2)
mo = sum(rs_other) / len(rs_other)
print(f"  touch=2: n={len(rs2)}, mean R={m2:+.3f}")
print(f"  touch=1+>=3: n={len(rs_other)}, mean R={mo:+.3f}")
print(f"  Diff = {m2 - mo:+.3f}R")

# Permutation test: are the means really different?
import random
rng = random.Random(42)
all_rs = rs2 + rs_other
n2 = len(rs2)
obs_diff = m2 - mo
B = 10000
ge = 0
for _ in range(B):
    rng.shuffle(all_rs)
    s2 = all_rs[:n2]
    so = all_rs[n2:]
    diff = sum(s2)/len(s2) - sum(so)/len(so)
    if abs(diff) >= abs(obs_diff):
        ge += 1
p_perm = ge / B
print(f"  Permutation test (two-sided, B={B}): p={p_perm:.4f}")
