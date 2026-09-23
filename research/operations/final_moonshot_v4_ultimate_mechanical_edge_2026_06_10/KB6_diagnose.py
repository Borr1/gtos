"""KB6_diagnose.py — WHERE/WHEN does the 1.5x left tail concentrate?

Decomposes the clean_3 deploy book's worst days and worst block-bootstrap paths to find which
sleeves / which days / which clustering drives the binding 1.5x-stress P(pass). No averages as
verdicts: per-sleeve loss attribution, per-year, loss-day clustering, and the actual worst
sampled paths under the LOCKED MC. Leak-free (uses cached validated streams only).
"""
import sys, statistics, collections, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import KB6_stress_lib as L

d = L.build_clean3()
days, sleeves, M, comb, fwd_mask = d['all_days'], d['sleeves'], d['M'], d['comb'], d['fwd_mask']
vs = d['vol_scale']; breadth = d['breadth']
TARGET, MAXDD, DAILY, BLOCK, PATHCAP, N = L.TARGET, L.MAXDD, L.DAILY, L.BLOCK, L.PATHCAP, L.N

print("=" * 80)
print("KB6 DIAGNOSIS — clean_3 deploy book, what concentrates the 1.5x left tail")
print("=" * 80)

# ---- 1. Loss-day distribution (the raw material of the stress) ----
loss_days = [(i, comb[i]) for i in range(len(comb)) if comb[i] < 0]
neg = [v for _, v in loss_days]
neg_sorted = sorted(neg)
print(f"\n[1] LOSS-DAY DISTRIBUTION (unit-R, the days the 1.5x stress inflates)")
print(f"  total days {len(comb)} | loss days {len(neg)} ({100*len(neg)/len(comb):.1f}%) | "
      f"win/flat {len(comb)-len(neg)}")
print(f"  loss-day mean {statistics.fmean(neg):+.4f} | median {statistics.median(neg):+.4f} | "
      f"worst {min(neg):+.4f}")
pct = lambda p: neg_sorted[int(p*len(neg_sorted))]
print(f"  loss-day percentiles: p1 {pct(0.01):+.3f}  p5 {pct(0.05):+.3f}  p10 {pct(0.10):+.3f}")
print(f"  worst 15 loss days: {[round(x,3) for x in neg_sorted[:15]]}")
# how much of total negative mass is in worst 5% of loss days
tail5 = neg_sorted[:max(1, int(0.05*len(neg_sorted)))]
print(f"  worst 5% of loss days = {len(tail5)} days hold {100*sum(tail5)/sum(neg):.1f}% of all negative R")
tail10 = neg_sorted[:max(1, int(0.10*len(neg_sorted)))]
print(f"  worst 10% of loss days = {len(tail10)} days hold {100*sum(tail10)/sum(neg):.1f}% of all negative R")

# ---- 2. Per-sleeve attribution on the worst days ----
print(f"\n[2] PER-SLEEVE LOSS ATTRIBUTION (who drives the worst days)")
# total negative contribution per sleeve across ALL days
sl_neg = collections.defaultdict(float)
sl_neg_count = collections.defaultdict(int)
for i in range(len(comb)):
    for si, s in enumerate(sleeves):
        if M[i][si] < 0:
            sl_neg[s] += M[i][si]; sl_neg_count[s] += 1
total_neg_mass = sum(sl_neg.values())
print(f"  {'sleeve':>20} {'neg-mass':>10} {'share%':>7} {'#neg-days':>9}")
for s in sorted(sleeves, key=lambda k: sl_neg[k]):
    print(f"  {s:>20} {sl_neg[s]:>+10.2f} {100*sl_neg[s]/total_neg_mass:>6.1f}% {sl_neg_count[s]:>9}")

# attribution restricted to the WORST 5% of book-loss days (these drive the stress paths)
worst_idx = set(i for i, _ in sorted(loss_days, key=lambda x: x[1])[:max(1, int(0.05*len(loss_days)))])
print(f"\n  -- on the WORST 5% book-loss days (n={len(worst_idx)}) — sleeve contribution --")
wsl = collections.defaultdict(float)
for i in worst_idx:
    for si, s in enumerate(sleeves):
        wsl[s] += M[i][si]
wtot = sum(wsl.values())
print(f"  {'sleeve':>20} {'contrib':>10} {'share%':>7}")
for s in sorted(sleeves, key=lambda k: wsl[k]):
    print(f"  {s:>20} {wsl[s]:>+10.2f} {100*wsl[s]/wtot:>6.1f}%")

# ---- 3. Breadth on loss days vs win days (does the tail come from high-breadth co-firing?) ----
print(f"\n[3] BREADTH (#co-firing sleeves) on loss vs the worst days")
bw = collections.defaultdict(lambda: [0, 0.0])  # breadth -> [count, sum]
for i in range(len(comb)):
    bw[breadth[i]][0] += 1; bw[breadth[i]][1] += comb[i]
print(f"  {'breadth':>7} {'days':>6} {'mean dayR':>10} {'worst':>8}")
for b in sorted(bw):
    rs = [comb[i] for i in range(len(comb)) if breadth[i] == b]
    print(f"  {b:>7} {bw[b][0]:>6} {bw[b][1]/bw[b][0]:>+10.4f} {min(rs):>+8.3f}")

# ---- 4. Loss clustering — do losses come in runs (which the block-bootstrap punishes)? ----
print(f"\n[4] LOSS CLUSTERING (block-bootstrap BLOCK=5 punishes runs of consecutive loss days)")
runs = []; cur = 0
for v in comb:
    if v < 0: cur += 1
    else:
        if cur > 0: runs.append(cur)
        cur = 0
if cur > 0: runs.append(cur)
rc = collections.Counter(runs)
print(f"  consecutive-loss-run lengths: " + " ".join(f"{k}:{v}" for k, v in sorted(rc.items())))
print(f"  max loss-run {max(runs)} | mean {statistics.fmean(runs):.2f} | #runs {len(runs)}")
# worst 5-day rolling window (the BLOCK size) — the literal stress unit
roll = [sum(comb[i:i+5]) for i in range(len(comb)-5)]
roll_s = sorted(roll)
print(f"  worst 5-day rolling sum (unstressed): {[round(x,2) for x in roll_s[:8]]}")
roll_str = [sum(L.stress(comb[i:i+5])) for i in range(len(comb)-5)]
roll_str_s = sorted(roll_str)
print(f"  worst 5-day rolling sum (1.5x STRESSED): {[round(x,2) for x in roll_str_s[:8]]}")

# ---- 5. Per-year loss profile (distrust single-regime) ----
print(f"\n[5] PER-YEAR loss profile (forward years 2025-26 vs train)")
print(f"  {'year':>5} {'days':>5} {'loss%':>6} {'mean':>8} {'worst':>8} {'p5':>8}")
for y in sorted(set(dd.year for dd in days)):
    idx = [i for i in range(len(days)) if days[i].year == y]
    yv = [comb[i] for i in idx]
    ynl = sorted([v for v in yv if v < 0])
    p5 = ynl[int(0.05*len(ynl))] if ynl else 0.0
    print(f"  {y:>5} {len(idx):>5} {100*len(ynl)/len(yv):>5.0f}% {statistics.fmean(yv):>+8.4f} "
          f"{min(yv):>+8.3f} {p5:>+8.3f}")

# ---- 6. The ACTUAL worst MC paths: what days build the failing equity curves? ----
print(f"\n[6] WORST MC PATHS under the LOCKED stress engine @1% vm (which days kill them)")
risk = 0.01 * vs
svals = L.stress(comb)
n = len(svals)
fail_block_days = collections.Counter()  # day-index -> times it appeared in a failing path's blocks
path_outcomes = collections.Counter()
sample_fail = []
for s in range(4000):  # subsample for diagnosis speed
    rng = random.Random(s * 131 + 999 + int(risk * 1e6))
    eq = 1.0; peak = 1.0; res = 'timeout'; visited = []
    for _ in range(PATHCAP):
        start = rng.randrange(n); broke = False
        for k in range(BLOCK):
            di = (start + k) % n; visited.append(di)
            dp = svals[di] * risk
            if dp <= -DAILY: res = 'fail_daily'; broke = True; break
            eq *= (1 + dp); peak = max(peak, eq)
            if (peak - eq) / peak >= MAXDD: res = 'fail_maxdd'; broke = True; break
            if eq - 1.0 >= TARGET: res = 'pass'; broke = True; break
        if broke: break
    path_outcomes[res] += 1
    if res in ('fail_maxdd', 'fail_daily'):
        for di in visited[-60:]:  # the recent days that built the drawdown
            if comb[di] < 0:
                fail_block_days[di] += 1
        if len(sample_fail) < 3:
            sample_fail.append((res, eq, len([v for v in visited if comb[v] < 0])))
print(f"  subsample (4000 paths): {dict(path_outcomes)}")
print(f"  fail mode mix: maxdd-driven, not daily-breach (daily-breach is mechanically ~0)")
print(f"  TOP days appearing in failing-path drawdowns (idx, date, dayR, times):")
for di, c in fail_block_days.most_common(12):
    yr = days[di].year
    # which sleeve drove that day
    contrib = sorted(((M[di][si], sleeves[si]) for si in range(len(sleeves))))
    worst_sl = contrib[0]
    print(f"    {days[di]} (y{yr}) dayR={comb[di]:+.3f} times={c:>4} worst-sleeve={worst_sl[1]}({worst_sl[0]:+.2f})")
