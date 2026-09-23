"""Extract CANDIDATE data from all NAS100 slices and compute statistics."""
import json
import glob
import re
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import sqrt

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
        r['_slice_start'] = data['start']
        r['_slice_end'] = data['end']
    all_records.extend(data['results'])

cands = [r for r in all_records if r.get('decision') == 'CANDIDATE']
print(f'N candidates: {len(cands)}')


def parse_raw(r):
    raw = r.get('raw_response', '')
    if not raw:
        return None
    # strip ```json ... ``` fences
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except Exception:
        return None


# Parse every candidate's raw_response
enriched = []
for c in cands:
    p = parse_raw(c)
    rec = dict(c)
    rec['_parsed'] = p
    # model_used (from raw)
    if p:
        rec['model_used'] = p.get('model_used', '?')
        rec['confidence_score'] = p.get('confidence_score')
        rec['confidence_computation'] = p.get('confidence_computation', '')
        rec['framework'] = p.get('framework', '')
        reasoning = p.get('reasoning', {}) or {}
        daily_bias = reasoning.get('daily_bias', {}) or {}
        rec['bias_confidence'] = daily_bias.get('confidence')
        h4_align = reasoning.get('h4_alignment', {}) or {}
        rec['h4_aligned'] = h4_align.get('aligned')
        h1_setup = reasoning.get('h1_setup', {}) or {}
        rec['poi_type'] = h1_setup.get('poi_type')
        rec['poi_zone'] = h1_setup.get('zone')
        rec['causing_event_type'] = h1_setup.get('causing_event_type')
        rec['fib_retracement_pct'] = h1_setup.get('fib_retracement_pct')
        liq_sweep = reasoning.get('liquidity_sweep', {}) or {}
        rec['sweep_detected'] = liq_sweep.get('detected')
        rec['sweep_pool_type'] = liq_sweep.get('pool_type')
        rec['sweep_quality'] = liq_sweep.get('quality') or liq_sweep.get('sweep_quality')
        m15_conf = reasoning.get('m15_confirmation', {}) or {}
        rec['m15_choch'] = m15_conf.get('choch_detected')
        rec['m15_displacement_quality'] = m15_conf.get('displacement_quality')
        rec['m15_displacement_ratio'] = m15_conf.get('displacement_candle_body_vs_avg_ratio')
        rec['overall_reasoning'] = reasoning.get('overall_reasoning', '')
    else:
        rec['model_used'] = '?'
    enriched.append(rec)


# Helpers
def ct_utc(r):
    return datetime.fromisoformat(r['candle_time'].replace('Z', '+00:00'))


def day_of_week(r):
    return ct_utc(r).strftime('%a')


def month(r):
    return ct_utc(r).strftime('%Y-%m')


def hour(r):
    return ct_utc(r).hour


def outcome_win(r):
    return 1 if r.get('outcome') == 'WIN' else 0


def outcome_resolved(r):
    return r.get('outcome') in ('WIN', 'LOSS')


def breakdown(records, key_fn, label='key'):
    bins = defaultdict(list)
    for r in records:
        bins[key_fn(r)].append(r)
    rows = []
    for k, rs in sorted(bins.items(), key=lambda kv: str(kv[0])):
        resolved = [r for r in rs if outcome_resolved(r)]
        n = len(rs)
        nr = len(resolved)
        nw = sum(1 for r in resolved if r.get('outcome') == 'WIN')
        nl = sum(1 for r in resolved if r.get('outcome') == 'LOSS')
        nu = sum(1 for r in rs if r.get('outcome') == 'UNFILLED')
        wr = (nw / nr * 100) if nr else 0.0
        total_r = sum(float(r.get('r_multiple') or 0) for r in rs)
        rows.append((k, n, nw, nl, nu, wr, total_r))
    return rows


# Quick summary
wins = [r for r in enriched if r.get('outcome') == 'WIN']
losses = [r for r in enriched if r.get('outcome') == 'LOSS']
unfilled = [r for r in enriched if r.get('outcome') == 'UNFILLED']
print(f'WIN={len(wins)} LOSS={len(losses)} UNFILLED={len(unfilled)}')
print()

print('=== By setup_grade ===')
for row in breakdown(enriched, lambda r: r.get('setup_grade', '?')):
    print(f'  grade={row[0]:5s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By kill_zone ===')
for row in breakdown(enriched, lambda r: r.get('kill_zone', '?')):
    print(f'  kz={row[0]:8s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By direction ===')
for row in breakdown(enriched, lambda r: r.get('direction', '?')):
    print(f'  dir={row[0]:6s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By hour (UTC) ===')
for row in breakdown(enriched, hour):
    print(f'  hour={row[0]:02d}Z n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By day of week ===')
for row in breakdown(enriched, day_of_week):
    print(f'  dow={row[0]:5s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By month ===')
for row in breakdown(enriched, month):
    print(f'  month={row[0]:8s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By slice ===')
for row in breakdown(enriched, lambda r: r.get('_slice')):
    print(f'  slice={row[0]} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By bias_source ===')
for row in breakdown(enriched, lambda r: r.get('bias_source', '?')):
    print(f'  bias_src={row[0]:20s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By m15_displacement_quality ===')
for row in breakdown(enriched, lambda r: r.get('m15_displacement_quality', '?')):
    print(f'  disp_q={row[0]!r:15s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By bias_confidence ===')
for row in breakdown(enriched, lambda r: r.get('bias_confidence', '?')):
    print(f'  bias_conf={row[0]!r:15s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== By confidence_score (buckets) ===')
def conf_bucket(r):
    c = r.get('confidence_score')
    if c is None:
        return 'missing'
    if c >= 85: return '>=85'
    if c >= 80: return '80-84'
    if c >= 75: return '75-79'
    if c >= 70: return '70-74'
    return '<70'
for row in breakdown(enriched, conf_bucket):
    print(f'  conf={row[0]:8s} n={row[1]:3d} W={row[2]:2d} L={row[3]:2d} U={row[4]:2d} WR={row[5]:5.1f}% totalR={row[6]:+.2f}')

print()
print('=== Total API cost ===')
total_cost = sum(float(r.get('cost') or 0) for r in enriched)
print(f'Total API cost across 37 CANDIDATEs: ${total_cost:.4f}')
print(f'Per CANDIDATE:  ${total_cost/len(enriched):.4f}')
print(f'Per WIN: ${total_cost/len(wins):.4f}')

# Also parse L1 pass stats — skipped/no-trade/blocked to see ratio
print()
tot = len(all_records)
by_decision = Counter(r.get('decision') for r in all_records)
print(f'All decisions: {dict(by_decision)} of {tot}')
