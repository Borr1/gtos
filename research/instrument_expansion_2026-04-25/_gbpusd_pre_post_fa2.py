"""Stratify GBPUSD trade_records by pre/post FA-2 commit (Apr 19/20)."""
import json
import os
from collections import Counter
from datetime import datetime

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
    sl_buffer = tp_block.get('sl_buffer_applied', 'NA')
    direction = dp.get('ai_direction', '')
    entry = tp_block.get('entry_price')
    sl = tp_block.get('stop_loss')
    inverted = False
    if direction == 'LONG' and sl >= entry:
        inverted = True
    records.append({
        'date': md.get('date',''),
        'kz': md.get('kill_zone',''),
        'time': md.get('candle_time','')[:16],
        'l2_passed': l2.get('passed', None),
        'l2_fails': [c['name'] for c in l2.get('checks',[]) if c.get('status') == 'FAIL'],
        'sl_buffer_applied': sl_buffer,
        'inverted': inverted,
        'entry': entry,
        'sl': sl,
        'system_version': md.get('system_version', ''),
    })

# FA-2: 2026-04-20 (UTC). prompt v2: 2026-04-24
def era(date_str):
    if date_str < '2026-04-20':
        return 'pre_FA2'
    elif date_str < '2026-04-24':
        return 'post_FA2_pre_v2'
    else:
        return 'post_v2'

eras = Counter()
era_l2 = {}
era_inv = {}
era_buffer = {}
for r in records:
    e = era(r['date'])
    eras[e] += 1
    era_l2.setdefault(e, []).append(r['l2_passed'])
    era_inv.setdefault(e, []).append(r['inverted'])
    era_buffer.setdefault(e, []).append(r['sl_buffer_applied'])

print(f'{"Era":22} {"n":4} {"L2-PASS%":10} {"INV%":7} {"sl_buffer=0%":15}')
for e in ['pre_FA2', 'post_FA2_pre_v2', 'post_v2']:
    n = eras.get(e, 0)
    if n == 0:
        continue
    l2_p = sum(1 for v in era_l2[e] if v) / n * 100
    inv_p = sum(1 for v in era_inv[e] if v) / n * 100
    buf0 = sum(1 for v in era_buffer[e] if v == 0.0) / n * 100
    print(f'{e:22} {n:4} {l2_p:8.1f}%  {inv_p:5.1f}% {buf0:13.1f}%')

# Per-record table by era
print()
print('Per-record by era:')
for e in ['pre_FA2', 'post_FA2_pre_v2', 'post_v2']:
    rows = [r for r in records if era(r['date']) == e]
    if not rows:
        continue
    print(f'\n--- {e} (n={len(rows)}) ---')
    for r in rows:
        l2 = 'PASS' if r['l2_passed'] else 'FAIL'
        inv = 'INV' if r['inverted'] else '-'
        fails = ','.join(r['l2_fails']) if r['l2_fails'] else ''
        print(f'  {r["date"]} {r["kz"]:7} {r["time"][11:]} {l2:5} {inv:4} sl_buf={r["sl_buffer_applied"]} fails={fails}')
