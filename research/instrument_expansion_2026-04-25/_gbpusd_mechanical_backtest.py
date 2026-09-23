"""Mechanical GBPUSD OB-retest backtest using H1 candles + M15 forward-resolve.

This is a SIMPLE proxy — NOT the full GTOS pipeline.
Identifies: bullish H1 OBs (last bearish H1 candle before a bullish H1 BOS)
After OB forms, treats first M15 retest as entry.
SL = OB low - 5 pips, TP = entry + 1.5 * (entry - SL).

Purpose: provide an order-of-magnitude WR/Exp R figure for GBPUSD across Jan-Apr 2026.
"""
import csv
import math
from datetime import datetime
from collections import defaultdict


def wilson_ci(p_hat, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    denom = 1 + z * z / n
    centre = p_hat + z * z / (2 * n)
    spread = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    return ((centre - spread) / denom, (centre + spread) / denom)


# Load H1
h1 = []
with open('data/historical_2026/GBPUSD_H1.csv', 'r', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for row in reader:
        h1.append({
            'time': datetime.fromisoformat(row['time']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        })

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

print(f'H1 bars: {len(h1)}, M15 bars: {len(m15)}')

# Detect bullish OBs:
# Find swing highs, then BOS = next bullish candle CLOSES above swing high.
# OB = the most recent bearish candle before the BOS impulse leg.

# Step 1: identify swings (3-bar fractal)
swings_high = []  # (idx, price)
swings_low = []
for i in range(2, len(h1) - 2):
    b = h1[i]
    if b['high'] > h1[i-1]['high'] and b['high'] > h1[i-2]['high'] and b['high'] > h1[i+1]['high'] and b['high'] > h1[i+2]['high']:
        swings_high.append((i, b['high']))
    if b['low'] < h1[i-1]['low'] and b['low'] < h1[i-2]['low'] and b['low'] < h1[i+1]['low'] and b['low'] < h1[i+2]['low']:
        swings_low.append((i, b['low']))

print(f'Swings high: {len(swings_high)}, low: {len(swings_low)}')

# Step 2: For each swing high, look for BOS = candle close > swing high
# Then OB = last bearish (close < open) candle in the impulse before BOS
bullish_obs = []  # list of (form_idx, ob_high, ob_low, bos_idx, swing_high)
for sw_idx, sw_high in swings_high:
    bos_idx = None
    for j in range(sw_idx + 1, min(sw_idx + 30, len(h1))):
        if h1[j]['close'] > sw_high:
            bos_idx = j
            break
    if bos_idx is None:
        continue
    # walk back from bos_idx to find last bearish candle
    ob_idx = None
    for k in range(bos_idx - 1, sw_idx - 1, -1):
        if h1[k]['close'] < h1[k]['open']:
            ob_idx = k
            break
    if ob_idx is None:
        continue
    bullish_obs.append({
        'form_idx': bos_idx,
        'ob_idx': ob_idx,
        'ob_high': h1[ob_idx]['high'],
        'ob_low': h1[ob_idx]['low'],
        'ob_time': h1[ob_idx]['time'],
        'bos_idx': bos_idx,
        'bos_time': h1[bos_idx]['time'],
        'sw_high': sw_high,
    })

print(f'Bullish OBs detected: {len(bullish_obs)}')

# Bearish OBs (symmetric)
bearish_obs = []
for sw_idx, sw_low in swings_low:
    bos_idx = None
    for j in range(sw_idx + 1, min(sw_idx + 30, len(h1))):
        if h1[j]['close'] < sw_low:
            bos_idx = j
            break
    if bos_idx is None:
        continue
    ob_idx = None
    for k in range(bos_idx - 1, sw_idx - 1, -1):
        if h1[k]['close'] > h1[k]['open']:
            ob_idx = k
            break
    if ob_idx is None:
        continue
    bearish_obs.append({
        'form_idx': bos_idx,
        'ob_idx': ob_idx,
        'ob_high': h1[ob_idx]['high'],
        'ob_low': h1[ob_idx]['low'],
        'ob_time': h1[ob_idx]['time'],
        'bos_idx': bos_idx,
        'bos_time': h1[bos_idx]['time'],
        'sw_low': sw_low,
    })

print(f'Bearish OBs detected: {len(bearish_obs)}')

# Build M15 index
m15_by_time = {b['time']: i for i, b in enumerate(m15)}


def find_m15_after(t):
    """Return earliest M15 idx after time t."""
    for i, b in enumerate(m15):
        if b['time'] >= t:
            return i
    return None


# Step 3: For each OB, simulate trade
# Entry: OB high (LONG) or OB low (SHORT) — first M15 candle to touch
# SL: OB low - 5 pips (LONG) or OB high + 5 pips (SHORT)
# TP: entry + 1.5*risk (LONG) or entry - 1.5*risk (SHORT)
# Walk M15 forward up to 96 bars (24h)


def simulate(direction, entry, sl, tp, start_idx, max_bars=96):
    for j in range(start_idx, min(start_idx + max_bars, len(m15))):
        b = m15[j]
        if direction == 'LONG':
            tp_hit = b['high'] >= tp
            sl_hit = b['low'] <= sl
        else:
            tp_hit = b['low'] <= tp
            sl_hit = b['high'] >= sl
        if tp_hit and sl_hit:
            return ('SL', j - start_idx)
        if sl_hit:
            return ('SL', j - start_idx)
        if tp_hit:
            return ('TP', j - start_idx)
    return ('TIMEOUT', max_bars)


PIP_BUF = 0.0005  # 5 pips
MIN_RR = 1.5

results = []
for ob in bullish_obs:
    bos_t = ob['bos_time']
    # Wait for first retest of OB high (price comes back down to OB)
    m15_start = find_m15_after(bos_t)
    if m15_start is None:
        continue
    # Find first M15 bar that touches the OB (low <= ob_high)
    fill_idx = None
    for i in range(m15_start, min(m15_start + 96 * 4, len(m15))):  # search up to 4 days
        b = m15[i]
        if b['low'] <= ob['ob_high'] <= b['high']:
            fill_idx = i
            break
    if fill_idx is None:
        continue
    entry = ob['ob_high']  # limit at OB high
    sl = ob['ob_low'] - PIP_BUF
    risk = entry - sl
    tp = entry + MIN_RR * risk
    if risk <= 0:
        continue
    outcome, bars = simulate('LONG', entry, sl, tp, fill_idx)
    if outcome == 'TP':
        r = 1.5
    elif outcome == 'SL':
        r = -1.0
    else:
        r = 0.0  # Timeout
    results.append({
        'direction': 'LONG',
        'ob_time': ob['ob_time'],
        'fill_time': m15[fill_idx]['time'],
        'entry': entry, 'sl': sl, 'tp': tp,
        'outcome': outcome, 'bars': bars, 'r': r,
        'month': m15[fill_idx]['time'].month,
    })

for ob in bearish_obs:
    bos_t = ob['bos_time']
    m15_start = find_m15_after(bos_t)
    if m15_start is None:
        continue
    fill_idx = None
    for i in range(m15_start, min(m15_start + 96 * 4, len(m15))):
        b = m15[i]
        if b['low'] <= ob['ob_low'] <= b['high']:
            fill_idx = i
            break
    if fill_idx is None:
        continue
    entry = ob['ob_low']
    sl = ob['ob_high'] + PIP_BUF
    risk = sl - entry
    tp = entry - MIN_RR * risk
    if risk <= 0:
        continue
    outcome, bars = simulate('SHORT', entry, sl, tp, fill_idx)
    if outcome == 'TP':
        r = 1.5
    elif outcome == 'SL':
        r = -1.0
    else:
        r = 0.0
    results.append({
        'direction': 'SHORT',
        'ob_time': ob['ob_time'],
        'fill_time': m15[fill_idx]['time'],
        'entry': entry, 'sl': sl, 'tp': tp,
        'outcome': outcome, 'bars': bars, 'r': r,
        'month': m15[fill_idx]['time'].month,
    })

print(f'\nTotal mechanical trades: {len(results)}')
print()
realized = [r for r in results if r['outcome'] in ('TP', 'SL')]
print(f'Realized: {len(realized)}')
wins = sum(1 for r in realized if r['outcome'] == 'TP')
losses = sum(1 for r in realized if r['outcome'] == 'SL')
print(f'  W: {wins}, L: {losses}')
if realized:
    p = wins / len(realized)
    lo, hi = wilson_ci(p, len(realized))
    avg = sum(r['r'] for r in realized) / len(realized)
    total = sum(r['r'] for r in realized)
    print(f'  WR: {p*100:.1f}% (Wilson 95% CI: [{lo*100:.1f}, {hi*100:.1f}])')
    print(f'  Exp R: {avg:+.3f}R, Total: {total:+.2f}R')

# Per-direction
print()
for d in ('LONG', 'SHORT'):
    sub = [r for r in realized if r['direction'] == d]
    if not sub:
        continue
    w = sum(1 for r in sub if r['outcome'] == 'TP')
    p = w / len(sub)
    lo, hi = wilson_ci(p, len(sub))
    avg = sum(r['r'] for r in sub) / len(sub)
    print(f'  {d}: n={len(sub)}, W={w}, WR={p*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}], Exp={avg:+.3f}R')

# Per-month
print()
print('Per-month decay:')
for m in (1, 2, 3, 4):
    sub = [r for r in realized if r['month'] == m]
    if not sub:
        continue
    w = sum(1 for r in sub if r['outcome'] == 'TP')
    p = w / len(sub)
    lo, hi = wilson_ci(p, len(sub))
    avg = sum(r['r'] for r in sub) / len(sub)
    mn = ['Jan', 'Feb', 'Mar', 'Apr'][m - 1]
    print(f'  {mn}: n={len(sub)}, W={w}, WR={p*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}], Exp={avg:+.3f}R')

# H1 (Jan+Feb) vs H2 (Mar+Apr)
h1_sub = [r for r in realized if r['month'] in (1, 2)]
h2_sub = [r for r in realized if r['month'] in (3, 4)]
if h1_sub and h2_sub:
    w1 = sum(1 for r in h1_sub if r['outcome'] == 'TP')
    w2 = sum(1 for r in h2_sub if r['outcome'] == 'TP')
    p1 = w1 / len(h1_sub)
    p2 = w2 / len(h2_sub)
    print(f'\nH1 (Jan+Feb): n={len(h1_sub)}, WR={p1*100:.1f}%')
    print(f'H2 (Mar+Apr): n={len(h2_sub)}, WR={p2*100:.1f}%')
    delta = (p2 - p1) * 100
    print(f'Decay (H2 - H1): {delta:+.1f}pp')
