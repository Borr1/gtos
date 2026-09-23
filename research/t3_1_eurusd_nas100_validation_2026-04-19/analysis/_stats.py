"""Statistical tests + refined aggregations."""
import json
import glob
import re
import os
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from math import sqrt, log, exp

ROOT = 'research/t3_1_eurusd_nas100_validation_2026-04-19'
files = sorted(glob.glob(os.path.join(ROOT, 'nas100_slice_*/NAS100_t7_simulation.json')))

all_records = []
for f in files:
    norm = f.replace('\\', '/')
    slice_idx = int(re.search(r'slice_(\d+)', norm).group(1))
    with open(f) as fh:
        data = json.load(fh)
    for r in data['results']:
        r['_slice'] = slice_idx
    all_records.extend(data['results'])

cands = [r for r in all_records if r.get('decision') == 'CANDIDATE']


def parse_raw(r):
    raw = r.get('raw_response', '')
    if not raw:
        return None
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


for c in cands:
    p = parse_raw(c) or {}
    reasoning = (p.get('reasoning') or {})
    c['confidence_score'] = p.get('confidence_score')
    c['model_used'] = p.get('model_used', '?')
    db = reasoning.get('daily_bias', {}) or {}
    c['bias_confidence'] = db.get('confidence')
    h1 = reasoning.get('h1_setup', {}) or {}
    c['poi_type'] = h1.get('poi_type')
    c['poi_zone'] = h1.get('zone')
    c['causing_event_type'] = h1.get('causing_event_type')
    liq = reasoning.get('liquidity_sweep', {}) or {}
    c['sweep_pool_type'] = liq.get('pool_type')
    c['sweep_quality'] = liq.get('quality') or liq.get('sweep_quality')
    m15 = reasoning.get('m15_confirmation', {}) or {}
    c['disp_ratio'] = m15.get('displacement_candle_body_vs_avg_ratio')


# Binomial p-value (two-sided) against null p0=0.5 using normal approx — small n, use exact
from math import comb
def binom_pvalue(k, n, p0=0.5):
    """two-sided exact binomial test"""
    def binom_cdf(k, n, p):
        return sum(comb(n, i) * p**i * (1-p)**(n-i) for i in range(k + 1))
    # probability of being at least as extreme
    # For two-sided, sum P(X) where P(X) <= P(k)
    probs = [comb(n, i) * p0**i * (1-p0)**(n-i) for i in range(n + 1)]
    pk = probs[k]
    tail = sum(p for p in probs if p <= pk + 1e-12)
    return tail


# Fisher exact
def fisher_exact(a, b, c, d):
    """2x2 table:  [[a,b],[c,d]]  two-sided p-value"""
    n = a + b + c + d
    r1 = a + b
    r2 = c + d
    c1 = a + c
    c2 = b + d
    # enumerate
    def log_comb(n, k):
        if k < 0 or k > n:
            return float('-inf')
        return sum(log(i) for i in range(1, n+1)) - sum(log(i) for i in range(1, k+1)) - sum(log(i) for i in range(1, n-k+1))
    log_p_obs = log_comb(r1, a) + log_comb(r2, c) - log_comb(n, c1)
    p_obs = exp(log_p_obs)
    # enumerate all
    p_sum = 0.0
    lo = max(0, c1 - r2)
    hi = min(r1, c1)
    for k in range(lo, hi + 1):
        lp = log_comb(r1, k) + log_comb(r2, c1 - k) - log_comb(n, c1)
        p = exp(lp)
        if p <= p_obs + 1e-12:
            p_sum += p
    return p_sum


# Counts
def wr_stats(records, label):
    resolved = [r for r in records if r.get('outcome') in ('WIN', 'LOSS')]
    nw = sum(1 for r in resolved if r.get('outcome') == 'WIN')
    nl = len(resolved) - nw
    total_r = sum(float(r.get('r_multiple') or 0) for r in records)
    return label, len(records), len(resolved), nw, nl, (nw / len(resolved) * 100 if resolved else 0), total_r


wins = [c for c in cands if c.get('outcome') == 'WIN']
losses = [c for c in cands if c.get('outcome') == 'LOSS']
unfilled = [c for c in cands if c.get('outcome') == 'UNFILLED']

# Against-breakeven for 22/33
print(f'Resolved: 22 WIN, 11 LOSS (WR=66.7%)')
print(f'Exact binomial p (two-sided vs p0=0.5):  p={binom_pvalue(22, 33, 0.5):.4f}')
print()


# Slice-by-slice  — drift test
print('Temporal drift (by slice):')
print('slice | n | W | L | WR')
for s in range(1, 6):
    rs = [r for r in cands if r['_slice'] == s]
    res = [r for r in rs if r.get('outcome') in ('WIN', 'LOSS')]
    nw = sum(1 for r in res if r.get('outcome') == 'WIN')
    nl = len(res) - nw
    wr = nw / len(res) * 100 if res else 0
    print(f'  {s} | {len(rs)} | {nw} | {nl} | {wr:.1f}%')

# 2x2 slice 1-2 vs slice 4-5 WR
early = [r for r in cands if r['_slice'] in (1, 2) and r.get('outcome') in ('WIN', 'LOSS')]
late = [r for r in cands if r['_slice'] in (4, 5) and r.get('outcome') in ('WIN', 'LOSS')]
ew = sum(1 for r in early if r.get('outcome') == 'WIN'); el = len(early) - ew
lw = sum(1 for r in late if r.get('outcome') == 'WIN'); ll = len(late) - lw
print(f'\nEarly (slice 1-2): {ew}W/{el}L  WR={ew/(ew+el)*100:.1f}%')
print(f'Late  (slice 4-5): {lw}W/{ll}L  WR={lw/max(1,(lw+ll))*100:.1f}%')
print(f'Fisher exact: p = {fisher_exact(ew, el, lw, ll):.4f}')


# LOSS feature correlations
# Build a cross-tab style
print()
print('=== LOSS feature correlation (Fisher exact on resolved subset N=33) ===')

resolved = [r for r in cands if r.get('outcome') in ('WIN', 'LOSS')]


def cross_tab(records, feature_fn, feature_label, target='LOSS'):
    # For feature = True vs False, L vs W counts
    a = b = c = d = 0
    for r in records:
        f_on = bool(feature_fn(r))
        is_loss = r.get('outcome') == target
        if f_on and is_loss: a += 1
        elif f_on and not is_loss: b += 1
        elif not f_on and is_loss: c += 1
        else: d += 1
    p = fisher_exact(a, b, c, d)
    tot = a + b + c + d
    if tot == 0:
        return
    wr_feat = b / (a + b) * 100 if (a + b) else 0
    wr_nofeat = d / (c + d) * 100 if (c + d) else 0
    n_feat = a + b
    n_nofeat = c + d
    print(f'  {feature_label}: feat=(n={n_feat} W={b} L={a} WR={wr_feat:.1f}%) nofeat=(n={n_nofeat} W={d} L={c} WR={wr_nofeat:.1f}%) Fisher p={p:.3f}')


# Features
cross_tab(resolved, lambda r: r.get('causing_event_type') == 'CHoCH', 'causing_event=CHoCH')
cross_tab(resolved, lambda r: r.get('poi_zone') == 'premium', 'poi_zone=premium')
cross_tab(resolved, lambda r: r.get('poi_zone') == 'discount', 'poi_zone=discount')
cross_tab(resolved, lambda r: (r.get('sweep_quality') == 'messy'), 'sweep_quality=messy')
cross_tab(resolved, lambda r: (r.get('sweep_quality') == 'clean'), 'sweep_quality=clean')
cross_tab(resolved, lambda r: (r.get('disp_ratio') is not None and r.get('disp_ratio') >= 3.0), 'disp_ratio>=3.0')
cross_tab(resolved, lambda r: (r.get('disp_ratio') is not None and r.get('disp_ratio') >= 5.0), 'disp_ratio>=5.0')
cross_tab(resolved, lambda r: r.get('bias_confidence') == 'medium', 'bias_confidence=medium')
cross_tab(resolved, lambda r: r.get('direction') == 'SHORT', 'direction=SHORT')
cross_tab(resolved, lambda r: r.get('kill_zone') == 'london', 'kill_zone=london')
cross_tab(resolved, lambda r: r.get('kill_zone') == 'ny', 'kill_zone=ny')
cross_tab(resolved, lambda r: r.get('_slice') in (4, 5), 'slice_in_4_5')
cross_tab(resolved, lambda r: r.get('confidence_score') is not None and r.get('confidence_score') >= 78, 'confidence_score>=78')
cross_tab(resolved, lambda r: (r.get('bias_source') == 'H4_primary'), 'bias_source=H4_primary')

print()
print('=== Confidence bucket WR (finer) ===')
from statistics import mean
for t in [70, 72, 75, 78, 80, 82]:
    hi = [r for r in resolved if (r.get('confidence_score') or 0) >= t]
    lo = [r for r in resolved if (r.get('confidence_score') or 0) < t]
    if not hi or not lo:
        continue
    whi = sum(1 for r in hi if r.get('outcome') == 'WIN')
    wlo = sum(1 for r in lo if r.get('outcome') == 'WIN')
    print(f'  conf>={t}: n={len(hi)} W={whi} WR={whi/len(hi)*100:.1f}%  |  conf<{t}: n={len(lo)} W={wlo} WR={wlo/len(lo)*100:.1f}%')

# Distinct days with >=1.5% drop and whether AI took SHORT
print()
print('=== DISTINCT DAYS with NAS100 >=1.5% drop (4h window) ===')
CSV_PATH = 'data/historical_2026/NAS100_M15.csv'
bars = []
with open(CSV_PATH) as fh:
    rdr = csv.DictReader(fh)
    for row in rdr:
        t_str = row['time']
        try:
            dt = datetime.fromisoformat(t_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        row['_dt'] = dt
        bars.append(row)
bars.sort(key=lambda b: b['_dt'])

window = 16  # 4h of M15
drop_days = {}
for i in range(window, len(bars)):
    seg = bars[i - window:i]
    try:
        highs = [float(b['high']) for b in seg]
        lows = [float(b['low']) for b in seg]
    except Exception:
        continue
    hi = max(highs)
    lo = min(lows)
    idx_hi = highs.index(hi)
    idx_lo = lows.index(lo)
    if idx_lo > idx_hi:
        drop = (hi - lo) / hi * 100
        if drop >= 1.5:
            d = seg[-1]['_dt'].date()
            if d not in drop_days or drop > drop_days[d]:
                drop_days[d] = drop

drop_sorted = sorted(drop_days.items())
print(f'Distinct days with >=1.5% drop: {len(drop_sorted)}')
for d, mag in drop_sorted:
    # what did AI do on that day
    day_recs = [r for r in all_records if r.get('date') == str(d)]
    evs = Counter(r.get('decision') for r in day_recs)
    short_cands = sum(1 for r in day_recs if r.get('decision') == 'CANDIDATE' and r.get('direction') == 'SHORT')
    long_cands = sum(1 for r in day_recs if r.get('decision') == 'CANDIDATE' and r.get('direction') == 'LONG')
    bearish_bias = sum(1 for r in day_recs if (r.get('bias') or '').lower() == 'bearish')
    print(f'  {d}  max_drop={mag:.2f}%  decisions={dict(evs)}  LONG_CANDs={long_cands}  SHORT_CANDs={short_cands}  bearish_bias_any={bearish_bias}')


# Distribution of bias across whole simulation
print()
print('=== Bias distribution across all 1600 evaluations ===')
bias_counts = Counter(r.get('bias') for r in all_records)
print(f'  {dict(bias_counts)}')
bias_of_cands = Counter(r.get('bias') for r in cands)
print(f'  Bias of CANDIDATEs: {dict(bias_of_cands)}')
h1_dir_all = Counter(r.get('h1_direction') for r in all_records)
print(f'  h1_direction of all 1600: {dict(h1_dir_all)}')

# MFE check on losses to answer "were losses coinflips"
print()
print('=== LOSS MFE before SL ===')
# reload bar_index
CSV_PATH = 'data/historical_2026/NAS100_M15.csv'
bar_index = {}
for b in bars:
    bar_index[b['_dt']] = b


def bars_between(start_dt, end_dt):
    out = []
    for b in bars:
        if start_dt <= b['_dt'] <= end_dt:
            out.append(b)
    return out


def ct_utc(r):
    return datetime.fromisoformat(r['candle_time'].replace('Z', '+00:00'))


def exit_utc(r):
    s = r.get('exit_candle')
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


for c in sorted(losses, key=lambda r: r['candle_time']):
    ct = ct_utc(c)
    ex = exit_utc(c)
    if ex is None:
        continue
    entry = c.get('entry_price')
    sl = c.get('stop_loss')
    tp = c.get('take_profit_1')
    direction = c.get('direction')
    seg = bars_between(ct + timedelta(minutes=15), ex)
    if direction == 'LONG':
        max_fav = max((float(b['high']) for b in seg if 'high' in b), default=None)
        mfe_r = (max_fav - entry) / abs(entry - sl) if max_fav is not None else None
    else:
        min_fav = min((float(b['low']) for b in seg if 'low' in b), default=None)
        mfe_r = (entry - min_fav) / abs(sl - entry) if min_fav is not None else None
    r_to_tp = abs(tp - entry) / abs(entry - sl)
    reached_tp = (mfe_r is not None and mfe_r >= r_to_tp)
    near_tp = (mfe_r is not None and mfe_r >= 0.8 * r_to_tp)
    print(f'  {c["candle_time"]}  MFE_r_before_SL={mfe_r:.2f}  TP_r={r_to_tp:.2f}  reached_TP_before_SL={reached_tp}  got_80%_toward_TP={near_tp}')
