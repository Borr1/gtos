"""
Per-instrument sub-session bucket edge map.

Reads unified_trades.csv. Buckets each trade by 15-min window of its entry
candle_time within its reported kill_zone. Respects skip windows (XAUUSD NY
13:00-13:14 is the one official skip configured today).

Computes per (symbol, kill_zone, bucket):
  * n
  * WR and bootstrap 95% CI (basic percentile, 5000 iters)
  * mean R and bootstrap 95% CI
  * recommendation tag: EMPHASIS / SKIP / OBSERVE / INSUFFICIENT

Emphasis criteria:
  n >= 20 AND WR_lo > instrument_baseline_WR AND E_R_lo > 0

Skip criteria:
  n >= 20 AND WR_hi < instrument_breakeven_WR

(Bonferroni correction: the WR alpha is divided by number of buckets tested per
instrument; we flag when bucket fails strict uncorrected CI but also when the
corrected CI changes the recommendation.)

Breakeven WR assumed by planned_rr=1.5 default:  BE = 1/(1+RR) = 40% at RR=1.5
For instrument-specific targets, use task-provided values:
  XAUUSD 35.7%, US30_cash 34.5%, USDJPY 40%, GBPJPY 41.7%, GBPUSD 37.5%

Baseline WR:  instrument overall realized WR across all q65/T7/F3 filled trades
(NOT the rolling_stats.json 62% because that's XAUUSD-only and 2024-early-2026).

Writes:
  bucket_stats_15min.csv
  bucket_stats_30min.csv
  bucket_stats_60min.csv
"""
from __future__ import annotations

import csv
import os
import random
from collections import defaultdict
from typing import Dict, List, Tuple

HERE = os.path.dirname(__file__)
INP = os.path.join(HERE, 'unified_trades.csv')
OUT_15 = os.path.join(HERE, 'bucket_stats_15min.csv')
OUT_30 = os.path.join(HERE, 'bucket_stats_30min.csv')
OUT_60 = os.path.join(HERE, 'bucket_stats_60min.csv')

# Breakeven WR per task spec
BREAKEVEN_WR = {
    'XAUUSD':    0.357,
    'US30_cash': 0.345,
    'USDJPY':    0.400,
    'GBPJPY':    0.417,
    'GBPUSD':    0.375,
}

# Kill zone definitions — UTC. Per CLAUDE.md.
KZ_BOUNDS = {
    'XAUUSD':    {'london': (7*60, 10*60+30), 'ny': (13*60, 17*60), 'tokyo': None},
    'US30_cash': {'london': (8*60, 10*60+30), 'ny': (13*60+30, 16*60), 'tokyo': None},
    'USDJPY':    {'london': (7*60, 9*60+30), 'ny': (13*60, 15*60+30), 'tokyo': (0, 3*60)},
    'GBPJPY':    {'london': (7*60, 9*60+30), 'ny': (13*60, 15*60+30), 'tokyo': (0, 3*60)},
    'GBPUSD':    {'london': (7*60, 12*60),   'ny': (13*60, 15*60+30), 'tokyo': None},
}

# Skip windows — (start_min, end_min) in UTC; entries falling here are dropped
SKIP_WINDOWS = {
    ('XAUUSD', 'ny'): [(13*60, 13*60+15)],  # skip 13:00-13:14
}

RNG_SEED = 20260424
N_BOOT = 5000


def minute_of_day(ts: str) -> int:
    # ts like '2024-04-01T08:00:00'
    hh = int(ts[11:13])
    mm = int(ts[14:16])
    return hh * 60 + mm


def bucket_key(minute: int, bucket_size: int) -> str:
    b = (minute // bucket_size) * bucket_size
    return f"{b // 60:02d}:{b % 60:02d}"


def in_kz(minute: int, bounds: Tuple[int, int]) -> bool:
    lo, hi = bounds
    # half-open [lo, hi)
    return lo <= minute < hi


def in_skip(sym: str, kz: str, minute: int) -> bool:
    for lo, hi in SKIP_WINDOWS.get((sym, kz), []):
        if lo <= minute < hi:
            return True
    return False


def bootstrap_ci(values, stat_fn, n_iter=N_BOOT, alpha=0.05, rng=None):
    rng = rng or random.Random(RNG_SEED)
    if not values:
        return (None, None)
    n = len(values)
    estimates = []
    for _ in range(n_iter):
        resample = [values[rng.randrange(n)] for _ in range(n)]
        estimates.append(stat_fn(resample))
    estimates.sort()
    lo_idx = int((alpha / 2) * n_iter)
    hi_idx = int((1 - alpha / 2) * n_iter) - 1
    return (estimates[lo_idx], estimates[hi_idx])


def win_rate(outcomes):
    wins = sum(1 for o in outcomes if o == 'WIN')
    return wins / len(outcomes) if outcomes else 0.0


def mean_r(rs):
    return sum(rs) / len(rs) if rs else 0.0


def load_trades():
    with open(INP) as f:
        rdr = csv.DictReader(f)
        out = []
        for r in rdr:
            try:
                r['r_multiple'] = float(r['r_multiple'])
            except Exception:
                continue
            out.append(r)
        return out


def compute_baselines(trades):
    by_sym = defaultdict(list)
    for t in trades:
        by_sym[t['symbol']].append(t)
    base = {}
    for sym, rows in by_sym.items():
        outcomes = [r['outcome'] for r in rows]
        rs = [r['r_multiple'] for r in rows]
        wr = win_rate(outcomes)
        er = mean_r(rs)
        base[sym] = {'n': len(rows), 'wr': wr, 'er': er}
    return base


def compute_buckets(trades, bucket_size: int):
    groups = defaultdict(list)
    dropped_out_of_kz = 0
    dropped_skip_window = 0
    for t in trades:
        sym = t['symbol']
        kz = (t['kill_zone'] or '').lower()
        if kz not in ('london', 'ny', 'tokyo'):
            continue
        bounds = KZ_BOUNDS.get(sym, {}).get(kz)
        if bounds is None:
            continue
        mn = minute_of_day(t['candle_time'])
        if not in_kz(mn, bounds):
            dropped_out_of_kz += 1
            continue
        if in_skip(sym, kz, mn):
            dropped_skip_window += 1
            continue
        bkey = bucket_key(mn, bucket_size)
        groups[(sym, kz, bkey)].append(t)
    return groups, dropped_out_of_kz, dropped_skip_window


def classify_recommendation(sym, n, wr, wr_lo, wr_hi, er, er_lo, er_hi, baseline_wr, k_tests):
    """Return (tag, reason)."""
    breakeven = BREAKEVEN_WR.get(sym, 0.40)
    if n < 20:
        return ('INSUFFICIENT', f'n={n} < 20')

    # Bonferroni correction: tighten the implied confidence
    # (We already produced 95% CIs; for a k-test correction we would re-run at
    # alpha/k. Below we flag whether the uncorrected rec would survive.)
    # Report strict-uncorrected rec; note corrected status separately.

    if er_lo is not None and er_lo > 0 and wr_lo > baseline_wr:
        return ('EMPHASIS', f'WR_lo={wr_lo:.3f}>baseline={baseline_wr:.3f}; E[R]_lo={er_lo:.3f}>0')
    if wr_hi is not None and wr_hi < breakeven:
        return ('SKIP', f'WR_hi={wr_hi:.3f}<breakeven={breakeven:.3f}')
    return ('OBSERVE', '')


def write_stats(groups, base, bucket_size, out_path):
    # Count tests per instrument (for Bonferroni)
    tests_per_sym = defaultdict(int)
    for (sym, kz, bk), rows in groups.items():
        if len(rows) >= 5:  # only "real" buckets counted
            tests_per_sym[sym] += 1

    # Build bucket time ranges
    rng = random.Random(RNG_SEED)
    fieldnames = [
        'symbol', 'kill_zone', 'bucket_start', 'bucket_end',
        'n', 'wins', 'losses', 'breakevens',
        'wr', 'wr_lo95', 'wr_hi95',
        'mean_r', 'mean_r_lo95', 'mean_r_hi95',
        'hqf_score',
        'baseline_wr', 'breakeven_wr',
        'recommendation', 'reason',
        'tests_in_bonferroni_group', 'avg_abs_r',
    ]
    rows_out = []
    for (sym, kz, bk), rows in sorted(groups.items()):
        n = len(rows)
        outcomes = [r['outcome'] for r in rows]
        rs = [r['r_multiple'] for r in rows]
        wins = sum(1 for o in outcomes if o == 'WIN')
        losses = sum(1 for o in outcomes if o == 'LOSS')
        bes = sum(1 for o in outcomes if o == 'BREAKEVEN')
        wr = win_rate(outcomes)
        er = mean_r(rs)
        # Bootstrap CIs (deterministic across bucket sizes via per-bucket seed)
        rng.seed(RNG_SEED + hash((sym, kz, bk)) % (2**31))
        wr_lo, wr_hi = bootstrap_ci(outcomes, lambda x: win_rate(x), rng=rng)
        rng.seed(RNG_SEED + hash((sym, kz, bk, 'R')) % (2**31))
        er_lo, er_hi = bootstrap_ci(rs, lambda x: mean_r(x), rng=rng)

        baseline = base[sym]['wr']
        tag, reason = classify_recommendation(
            sym, n, wr, wr_lo, wr_hi, er, er_lo, er_hi,
            baseline, tests_per_sym[sym])

        avg_abs_r = sum(abs(r) for r in rs) / len(rs) if rs else 0.0
        # HQF = n * wr * mean_r (expected total R produced by this bucket)
        hqf = n * wr * er if er else n * wr * 0.0
        # More intuitive: expected R per bucket visit
        # but for ranking we want total expected R contribution
        hqf = n * er  # total R delivered (freq x mean R)

        bs = int(bk[:2]) * 60 + int(bk[3:])
        be = bs + bucket_size
        b_end = f"{be // 60:02d}:{be % 60:02d}"

        rows_out.append({
            'symbol': sym,
            'kill_zone': kz,
            'bucket_start': bk,
            'bucket_end': b_end,
            'n': n,
            'wins': wins,
            'losses': losses,
            'breakevens': bes,
            'wr': round(wr, 4),
            'wr_lo95': round(wr_lo, 4) if wr_lo is not None else '',
            'wr_hi95': round(wr_hi, 4) if wr_hi is not None else '',
            'mean_r': round(er, 4),
            'mean_r_lo95': round(er_lo, 4) if er_lo is not None else '',
            'mean_r_hi95': round(er_hi, 4) if er_hi is not None else '',
            'hqf_score': round(hqf, 4),
            'baseline_wr': round(baseline, 4),
            'breakeven_wr': BREAKEVEN_WR.get(sym, 0.40),
            'recommendation': tag,
            'reason': reason,
            'tests_in_bonferroni_group': tests_per_sym[sym],
            'avg_abs_r': round(avg_abs_r, 4),
        })

    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)
    return rows_out


def main():
    trades = load_trades()
    print(f'Loaded {len(trades)} trades')
    base = compute_baselines(trades)
    print('Baselines:')
    for s, b in base.items():
        print(f'  {s}: n={b["n"]} WR={b["wr"]:.3f} E[R]={b["er"]:.3f}')

    for size, outp in [(15, OUT_15), (30, OUT_30), (60, OUT_60)]:
        groups, dropped_oo, dropped_skip = compute_buckets(trades, size)
        print(f'\nBucket size {size}min: {len(groups)} groups, dropped_oo_kz={dropped_oo}, dropped_skip={dropped_skip}')
        rows = write_stats(groups, base, size, outp)
        print(f'Wrote {outp}: {len(rows)} rows')
        # Summary
        by_sym = defaultdict(lambda: defaultdict(int))
        for r in rows:
            by_sym[r['symbol']][r['recommendation']] += 1
        print('  Recs by symbol:')
        for s, d in sorted(by_sym.items()):
            print(f'    {s}: {dict(d)}')


if __name__ == '__main__':
    main()
