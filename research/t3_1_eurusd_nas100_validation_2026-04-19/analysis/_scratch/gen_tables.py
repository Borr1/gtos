"""Generate final counterfactual tables for C_l2_blocked_analysis.md"""
import json, csv, sys, re, os
from collections import defaultdict, Counter
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

ROOT = 'C:/Users/MSI/Documents/ai-trading-agent'
CSV_PATH = f'{ROOT}/data/historical_2026/NAS100_M15.csv'
m15 = []
with open(CSV_PATH) as f:
    rdr = csv.DictReader(f)
    for row in rdr:
        t = row['time'].replace(' ', 'T') + 'Z'
        m15.append({
            'time': t,
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        })
time_idx = {c['time']: i for i, c in enumerate(m15)}


def compute_outcome(entry, sl, tp, direction, candle_close, candle_time, timeout=None):
    if not entry or not sl or not tp:
        return {'outcome': 'UNKNOWN', 'r': 0}
    EPS = 0.05
    needs_fill_check = candle_close is not None and abs(entry - candle_close) > EPS
    entry_filled = not needs_fill_check
    fill_time = candle_time if entry_filled else None
    if candle_time not in time_idx:
        return {'outcome': 'UNKNOWN', 'r': 0}
    start = time_idx[candle_time]
    for i in range(start + 1, len(m15)):
        c = m15[i]
        h, l = c['high'], c['low']
        if not entry_filled:
            if direction == 'LONG':
                if entry < candle_close and l <= entry:
                    entry_filled = True
                    fill_time = c['time']
                elif entry > candle_close and h >= entry:
                    entry_filled = True
                    fill_time = c['time']
            else:
                if entry > candle_close and h >= entry:
                    entry_filled = True
                    fill_time = c['time']
                elif entry < candle_close and l <= entry:
                    entry_filled = True
                    fill_time = c['time']
            if not entry_filled:
                continue
        if timeout is not None and fill_time is not None:
            ft = datetime.fromisoformat(fill_time.replace('Z', '+00:00'))
            ct = datetime.fromisoformat(c['time'].replace('Z', '+00:00'))
            if (ct - ft).total_seconds() / 3600.0 >= timeout:
                if direction == 'LONG':
                    if l <= sl:
                        return {'outcome': 'LOSS', 'r': -1.0}
                    if h >= tp:
                        d = entry - sl
                        return {'outcome': 'WIN', 'r': round((tp - entry) / d, 2) if d > 0 else 0}
                else:
                    if h >= sl:
                        return {'outcome': 'LOSS', 'r': -1.0}
                    if l <= tp:
                        d = sl - entry
                        return {'outcome': 'WIN', 'r': round((entry - tp) / d, 2) if d > 0 else 0}
                return {'outcome': 'BE', 'r': 0}
        if direction == 'LONG':
            if l <= sl:
                return {'outcome': 'LOSS', 'r': -1.0}
            if h >= tp:
                d = entry - sl
                return {'outcome': 'WIN', 'r': round((tp - entry) / d, 2) if d > 0 else 0}
        else:
            if h >= sl:
                return {'outcome': 'LOSS', 'r': -1.0}
            if l <= tp:
                d = sl - entry
                return {'outcome': 'WIN', 'r': round((entry - tp) / d, 2) if d > 0 else 0}
    if not entry_filled:
        return {'outcome': 'UNFILLED', 'r': 0}
    return {'outcome': 'OPEN', 'r': 0}


def sl_subgroup(r):
    reason = r.get('l2_reason', '')
    if not reason.startswith('sl_beyond_ob'):
        return None
    m = re.search(r'SL ([\d.]+) is NOT (below|above) OB (low|high) ([\d.]+)', reason)
    if not m:
        return 'sl_beyond_ob_unparsed'
    sl_claim = float(m.group(1))
    ob_lvl = float(m.group(4))
    if sl_claim == ob_lvl:
        return 'sl=OB_bound_exact'
    return 'sl_inside_OB_zone'


def poi_subgroup(r):
    reason = r.get('l2_reason', '')
    if not reason.startswith('h1_poi_exists'):
        return None
    if 'poi_identified=False' in reason:
        return 'poi_self_contradict_False'
    if 'AI cites H1 POI' in reason:
        return 'poi_cited_no_matching_OB'
    return 'poi_other'


def subcat(r):
    s = sl_subgroup(r) or poi_subgroup(r)
    if s:
        return s
    reason = r.get('l2_reason', '')
    return reason.split(':')[0].split(' (')[0].strip()


slices = [1, 2, 3, 4, 5]
base = f'{ROOT}/research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{{}}/NAS100_t7_simulation.json'
all_results = []
for s in slices:
    with open(base.format(s)) as f:
        d = json.load(f)
    all_results.extend(d['results'])

rej = [r for r in all_results if r['decision'] == 'REJECTED_L2']
bl = [r for r in all_results if r['decision'] == 'BLOCKED_LIMIT']
cand = [r for r in all_results if r['decision'] == 'CANDIDATE']


def run_bucket(recs, catfn, timeout):
    buckets = defaultdict(list)
    for r in recs:
        o = compute_outcome(r['entry_price'], r['stop_loss'], r['take_profit_1'], r['direction'],
                            r['candle_close'], r['candle_time'], timeout=timeout)
        buckets[catfn(r)].append(o)
    rows = []
    tw = tl = tu = to = tbe = 0
    tr = 0
    for k in sorted(buckets):
        ps = buckets[k]
        w = sum(1 for p in ps if p['outcome'] == 'WIN')
        l = sum(1 for p in ps if p['outcome'] == 'LOSS')
        u = sum(1 for p in ps if p['outcome'] == 'UNFILLED')
        op = sum(1 for p in ps if p['outcome'] == 'OPEN')
        be = sum(1 for p in ps if p['outcome'] == 'BE')
        rs = sum(p.get('r', 0) for p in ps if p['outcome'] in ('WIN', 'LOSS', 'BE'))
        resolved = w + l + be
        wr = 100 * w / resolved if resolved else 0
        exp = rs / resolved if resolved else 0
        rows.append({'cat': k, 'N': len(ps), 'W': w, 'L': l, 'U': u, 'O': op, 'BE': be,
                     'WR': wr, 'sumR': rs, 'exp': exp})
        tw += w; tl += l; tu += u; to += op; tbe += be; tr += rs
    resolved = tw + tl + tbe
    rows.append({'cat': 'TOTAL', 'N': len(recs), 'W': tw, 'L': tl, 'U': tu, 'O': to, 'BE': tbe,
                 'WR': 100 * tw / resolved if resolved else 0,
                 'sumR': tr, 'exp': tr / resolved if resolved else 0})
    return rows


tables = {}
for label, recs, catfn in [
    ('REJECTED_L2', rej, subcat),
    ('BLOCKED_LIMIT', bl, lambda r: r.get('block_reason', '').split(' (')[0]),
]:
    for tmo, tkey in [(None, 'no_timeout'), (2, 'timeout_2h')]:
        tables[f'{label}_{tkey}'] = run_bucket(recs, catfn, tmo)

# Novel-only BLOCKED_LIMIT
cand_sigs = {(r['date'], r['entry_price'], r['stop_loss'], r['direction']) for r in cand}
bl_novel = [r for r in bl if (r['date'], r['entry_price'], r['stop_loss'], r['direction']) not in cand_sigs]
for tmo, tkey in [(None, 'no_timeout'), (2, 'timeout_2h')]:
    tables[f'BLOCKED_LIMIT_novel_{tkey}'] = run_bucket(
        bl_novel, lambda r: r.get('block_reason', '').split(' (')[0], tmo)

# CANDIDATE 2h sensitivity
for tmo, tkey in [(None, 'no_timeout'), (2, 'timeout_2h')]:
    tables[f'CANDIDATE_{tkey}'] = run_bucket(cand, lambda r: 'CANDIDATE', tmo)

# Volume / frequency context
meta = {
    'trading_days': 76,
    'cand_days': len({r['date'] for r in cand}),
    'bl_days': len({r['date'] for r in bl}),
    'cand_count': len(cand),
    'bl_count': len(bl),
    'bl_novel_count': len(bl_novel),
    'rej_count': len(rej),
    'by_kz': {
        'CAND': dict(Counter(r['kill_zone'] for r in cand)),
        'BL': dict(Counter(r['kill_zone'] for r in bl)),
        'REJ': dict(Counter(r['kill_zone'] for r in rej)),
    },
}

os.makedirs(f'{ROOT}/research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/_scratch', exist_ok=True)
with open(f'{ROOT}/research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/_scratch/tables.json', 'w') as f:
    json.dump({'tables': tables, 'meta': meta}, f, indent=2)

for k, rows in tables.items():
    print(f'\n{k}:')
    print(f'  {"cat":35s} {"N":>4} {"W":>3} {"L":>3} {"U":>3} {"O":>3} {"BE":>3} {"WR%":>6} {"sumR":>8} {"Exp":>8}')
    for row in rows:
        print(f'  {row["cat"]:35s} {row["N"]:4d} {row["W"]:3d} {row["L"]:3d} {row["U"]:3d} {row["O"]:3d} {row["BE"]:3d} {row["WR"]:6.1f} {row["sumR"]:+8.2f} {row["exp"]:+8.3f}')

print(f'\nMeta: {json.dumps(meta, indent=2)}')
