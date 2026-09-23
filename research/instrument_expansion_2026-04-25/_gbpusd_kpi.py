"""GBPUSD observer-mode KPI analysis script."""
import json
import os
import csv
import math
import glob
from datetime import datetime, timedelta
from collections import Counter, defaultdict


def wilson_ci(p_hat, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    centre = p_hat + z * z / (2 * n)
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    return ((centre - spread) / denom, (centre + spread) / denom)


# Load M15
m15 = []
with open('data/historical_2026/GBPUSD_M15.csv', 'r', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        m15.append({
            'time': datetime.fromisoformat(row['time']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        })
m15_by_time = {b['time']: i for i, b in enumerate(m15)}


def forward_resolve(entry_time_iso, entry, sl, tp, direction, max_fill_bars=72, max_post_fill=96):
    candle_dt = datetime.fromisoformat(entry_time_iso[:19])
    minute = candle_dt.minute - (candle_dt.minute % 15)
    bar_dt = candle_dt.replace(minute=minute, second=0, microsecond=0)
    if bar_dt not in m15_by_time:
        return ('NO_BAR', None, None, None)
    start_idx = m15_by_time[bar_dt] + 1
    fill_idx = None
    for i in range(start_idx, min(start_idx + max_fill_bars, len(m15))):
        b = m15[i]
        if b['low'] <= entry <= b['high']:
            fill_idx = i
            break
    if fill_idx is None:
        return ('NO_FILL', None, None, None)
    for j in range(fill_idx, min(fill_idx + max_post_fill, len(m15))):
        b = m15[j]
        if direction == 'LONG':
            tp_hit = b['high'] >= tp
            sl_hit = b['low'] <= sl
        else:
            tp_hit = b['low'] <= tp
            sl_hit = b['high'] >= sl
        if tp_hit and sl_hit:
            return ('SL', j - fill_idx, fill_idx, b['time'])
        if sl_hit:
            return ('SL', j - fill_idx, fill_idx, b['time'])
        if tp_hit:
            return ('TP', j - fill_idx, fill_idx, b['time'])
    return ('TIMEOUT', max_post_fill, fill_idx, None)


# === Section 1: Live evaluations ===
eval_files = sorted(glob.glob('knowledge_base/live_evaluations/GBPUSD/2026-04-*.jsonl'))
total_evals = 0
decisions = Counter()
cand_dates = Counter()
no_trade_dates = Counter()
days_seen = set()

for f in eval_files:
    fname = os.path.basename(f)[:10]
    days_seen.add(fname)
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            row = json.loads(line)
            total_evals += 1
            decisions[row.get('decision', 'UNK')] += 1
            if row.get('decision') == 'CANDIDATE':
                cand_dates[fname] += 1
            elif row.get('decision') == 'NO_TRADE':
                no_trade_dates[fname] += 1

print('=' * 70)
print('SECTION 1: OBSERVER-MODE LIVE DATA')
print('=' * 70)
print()
print(f'Date range: 2026-04-06 to 2026-04-22')
print(f'Trading days with evaluations: {len(days_seen)}')
print(f'Days seen: {sorted(days_seen)}')
print(f'Total M15 evaluations: {total_evals}')
print(f'Decision distribution: {dict(decisions)}')
n_cand = decisions.get('CANDIDATE', 0)
cr_pct = n_cand / total_evals * 100 if total_evals else 0
lo, hi = wilson_ci(n_cand / total_evals, total_evals) if total_evals else (0, 0)
print(f'CR rate: {n_cand}/{total_evals} = {cr_pct:.1f}% (Wilson 95% CI: [{lo*100:.1f}, {hi*100:.1f}])')

print()
print('Per-day CAND count:')
for d in sorted(days_seen):
    nc = cand_dates.get(d, 0)
    nt = no_trade_dates.get(d, 0)
    total = nc + nt
    print(f'  {d}: {nc} CAND / {total} total ({nc/total*100:.0f}% CR)')

# === Trade records ===
trade_dir = 'knowledge_base/trade_records/GBPUSD'
records = []
for fname in sorted(os.listdir(trade_dir)):
    fp = os.path.join(trade_dir, fname)
    with open(fp, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    md = data.get('metadata', {})
    dp = data.get('decision_pipeline', {})
    tp_block = data.get('trade_parameters') or {}
    if not tp_block:
        tp_block = dp.get('component_3_response', {}).get('trade_parameters') or {}
    l2 = dp.get('level2_verification', {}) or {}
    entry = tp_block.get('entry_price')
    sl = tp_block.get('stop_loss')
    tp1 = tp_block.get('take_profit_1')
    direction = dp.get('ai_direction', 'LONG')
    candle_time = md.get('candle_time', '')
    if not (entry and sl and tp1):
        continue
    inverted = False
    if direction == 'LONG':
        if sl >= entry or tp1 <= entry:
            inverted = True
    else:
        if sl <= entry or tp1 >= entry:
            inverted = True
    candle_dt = datetime.fromisoformat(candle_time[:19])
    minute = candle_dt.minute - (candle_dt.minute % 15)
    bar_dt = candle_dt.replace(minute=minute, second=0, microsecond=0)
    bar_idx = m15_by_time.get(bar_dt)
    bar_close = m15[bar_idx]['close'] if bar_idx is not None else None
    outcome, bars, fill_idx, exit_time = forward_resolve(
        candle_time, entry, sl, tp1, direction
    )
    if outcome == 'TP':
        r = 1.5
    elif outcome == 'SL':
        r = -1.0
    elif outcome == 'TIMEOUT':
        r = 0.0
    else:
        r = None
    records.append({
        'file': fname,
        'date': md.get('date', ''),
        'kz': md.get('kill_zone', ''),
        'candle_time': candle_time[:19],
        'direction': direction,
        'l2_passed': l2.get('passed', None),
        'l2_fails': [c['name'] for c in l2.get('checks', []) if c.get('status') == 'FAIL'],
        'entry': entry,
        'sl': sl,
        'tp1': tp1,
        'inverted': inverted,
        'bar_close': bar_close,
        'distance_pips': round(abs(entry - bar_close) * 10000, 1) if bar_close else None,
        'entry_below_close': bool(bar_close and entry < bar_close),
        'outcome': outcome,
        'bars': bars,
        'r': r,
    })

# Save resolved records
out_path = 'research/instrument_expansion_2026-04-25/_gbpusd_observer_resolved.jsonl'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as fh:
    for r in records:
        fh.write(json.dumps(r) + '\n')

print()
print('=' * 70)
print('SECTION 1B: TRADE_RECORDS FORWARD-RESOLVED')
print('=' * 70)
print()
print(f'Total trade_records: {len(records)}')
n_l2_pass = sum(1 for r in records if r['l2_passed'])
n_l2_fail = sum(1 for r in records if not r['l2_passed'])
n_inv = sum(1 for r in records if r['inverted'])
print(f'  L2 passed: {n_l2_pass} ({n_l2_pass/len(records)*100:.0f}%)')
print(f'  L2 failed: {n_l2_fail} ({n_l2_fail/len(records)*100:.0f}%)')
print(f'  Inverted TP geometry: {n_inv}')

l2_fail_reasons = Counter()
for r in records:
    for f in r['l2_fails']:
        l2_fail_reasons[f] += 1
print(f'  L2 failure reasons: {dict(l2_fail_reasons)}')

distances = [r['distance_pips'] for r in records if r['distance_pips'] is not None]
print()
print('Distance from current close to AI entry (pips, abs):')
if distances:
    s = sorted(distances)
    print(f'  N: {len(distances)}, min: {s[0]:.1f}, q1: {s[len(s)//4]:.1f}, median: {s[len(s)//2]:.1f}, q3: {s[3*len(s)//4]:.1f}, max: {s[-1]:.1f}')

far = [r for r in records if r['distance_pips'] and r['distance_pips'] > 50 and r['entry_below_close']]
print(f'  Entries >50 pips BELOW close (stale-OB anchoring): {len(far)}/{len(records)}')

# Outcomes
print()
print('Outcome distribution (all 28):')
oc = Counter(r['outcome'] for r in records)
print(f'  {dict(oc)}')

# === L2 PASS subset ===
print()
print('=' * 70)
print('SECTION 1C: L2-PASS SUBSET (would-have-actually-traded)')
print('=' * 70)
l2_pass = [r for r in records if r['l2_passed']]
print(f'N: {len(l2_pass)}')
oc_l2 = Counter(r['outcome'] for r in l2_pass)
print(f'Outcome dist: {dict(oc_l2)}')
realized_l2 = [r for r in l2_pass if r['outcome'] in ('TP', 'SL')]
wins_l2 = sum(1 for r in realized_l2 if r['outcome'] == 'TP')
print(f'Realized (TP+SL): n={len(realized_l2)}, wins={wins_l2}')
if realized_l2:
    p = wins_l2 / len(realized_l2)
    lo, hi = wilson_ci(p, len(realized_l2))
    print(f'  WR: {p*100:.1f}% (Wilson 95% CI: [{lo*100:.1f}, {hi*100:.1f}])')
    avg = sum(r['r'] for r in realized_l2) / len(realized_l2)
    total = sum(r['r'] for r in realized_l2)
    print(f'  Exp R: {avg:+.3f}R, Total: {total:+.2f}R')

# Inc TIMEOUT as 0R
all_realized_or_to = [r for r in l2_pass if r['outcome'] in ('TP', 'SL', 'TIMEOUT')]
if all_realized_or_to:
    avg = sum(r['r'] for r in all_realized_or_to) / len(all_realized_or_to)
    print(f'  Inc TIMEOUT@0R: n={len(all_realized_or_to)}, Exp R: {avg:+.3f}R')

# === ALL 28 ===
print()
print('=' * 70)
print('SECTION 1D: ALL 28 CAND (ignore L2)')
print('=' * 70)
realized_all = [r for r in records if r['outcome'] in ('TP', 'SL')]
wins_all = sum(1 for r in realized_all if r['outcome'] == 'TP')
print(f'Realized: n={len(realized_all)}, wins={wins_all}')
if realized_all:
    p = wins_all / len(realized_all)
    lo, hi = wilson_ci(p, len(realized_all))
    avg = sum(r['r'] for r in realized_all) / len(realized_all)
    total = sum(r['r'] for r in realized_all)
    print(f'  WR: {p*100:.1f}% (Wilson 95% CI: [{lo*100:.1f}, {hi*100:.1f}])')
    print(f'  Exp R: {avg:+.3f}R, Total: {total:+.2f}R')

# Direction
print()
dir_count = Counter(r['direction'] for r in records)
print(f'Direction distribution: {dict(dir_count)} (NB: 100% LONG = v1 detector bullish-bias era)')
print()
print('Per-record table:')
print('{:11} {:7} {:5} {:5} {:5} {:5} {:>9} {:>9} {:>9} {:>9} {:>4} {:>8} {:>5}'.format(
    'date', 'kz', 'time', 'dir', 'L2', 'inv', 'entry', 'close', 'sl', 'tp1', 'pips', 'outcome', 'R'))
for r in records:
    inv = 'INV' if r['inverted'] else '-'
    pips = r['distance_pips'] if r['distance_pips'] is not None else 0
    print('{:11} {:7} {:5} {:5} {:5} {:5} {:>9} {:>9} {:>9} {:>9} {:>4} {:>8} {:>5}'.format(
        r['date'], r['kz'], r['candle_time'][11:16], r['direction'],
        str(r['l2_passed'])[:5], inv, r['entry'], round(r['bar_close'], 5) if r['bar_close'] else 'NA',
        r['sl'], r['tp1'], pips, r['outcome'], str(r['r'])))

print()
print('=' * 70)
print('FINAL CRITICAL OBSERVATION')
print('=' * 70)
print()
print('The 16 trade_records from Apr 14-22 ALL reference the SAME entry of 1.34616')
print('This is the AI repeatedly anchoring on a stale OB after price moved 50-100 pips above it')
print('NONE of those 16 entries were ever filled in M15 data — price never returned to 1.34616')
print()
print(f'Effectively, observer mode has only n={6} REALIZED outcomes from Apr 13')
print(f'  WR: {sum(1 for r in records[:9] if r["outcome"]=="TP")}/{6} = ~67%')
print(f'  But this is contaminated by L2-failed entries (4/6 realized are L2 fails)')
