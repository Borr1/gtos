"""Correct MFE/MAE: measured AFTER the fill event, before exit."""
import json
import glob
import re
import os
import csv
from datetime import datetime, timezone, timedelta

ROOT = 'research/t3_1_eurusd_nas100_validation_2026-04-19'
files = sorted(glob.glob(os.path.join(ROOT, 'nas100_slice_*/NAS100_t7_simulation.json')))

all_records = []
for f in files:
    with open(f) as fh:
        data = json.load(fh)
    all_records.extend(data['results'])

cands = [r for r in all_records if r.get('decision') == 'CANDIDATE']
wins = [c for c in cands if c.get('outcome') == 'WIN']
losses = [c for c in cands if c.get('outcome') == 'LOSS']

# Load bars
bars = []
with open('data/historical_2026/NAS100_M15.csv') as fh:
    for r in csv.DictReader(fh):
        try:
            dt = datetime.fromisoformat(r['time']).replace(tzinfo=timezone.utc)
        except Exception:
            continue
        r['_dt'] = dt
        r['high'] = float(r['high'])
        r['low'] = float(r['low'])
        r['close'] = float(r['close'])
        bars.append(r)
bars.sort(key=lambda b: b['_dt'])


def find_fill_exit(c):
    """Return (fill_time, exit_time, outcome, mfe_r, mae_r, r_to_tp) mirroring simulator logic."""
    entry = c['entry_price']
    sl = c['stop_loss']
    tp = c['take_profit_1']
    direction = c['direction']
    candle_close = c.get('candle_close')
    candle_time = datetime.fromisoformat(c['candle_time'].replace('Z', '+00:00'))
    needs_fill = candle_close is not None and abs(entry - candle_close) > 0.05
    filled = not needs_fill
    fill_time = candle_time if filled else None
    post_fill_high = -1e18
    post_fill_low = 1e18
    exit_time = None
    outcome = None
    for b in bars:
        if b['_dt'] < candle_time:
            continue
        if b['_dt'] == candle_time:
            continue
        h, l = b['high'], b['low']
        if not filled:
            if direction == 'LONG':
                if entry < candle_close and l <= entry:
                    filled = True; fill_time = b['_dt']
                elif entry > candle_close and h >= entry:
                    filled = True; fill_time = b['_dt']
            else:
                if entry > candle_close and h >= entry:
                    filled = True; fill_time = b['_dt']
                elif entry < candle_close and l <= entry:
                    filled = True; fill_time = b['_dt']
            if not filled:
                continue
            # same-candle: skip TP/SL check unless we can tell order (approximate)
            continue
        # Track excursions
        if direction == 'LONG':
            post_fill_high = max(post_fill_high, h)
            post_fill_low = min(post_fill_low, l)
            if l <= sl:
                outcome = 'LOSS'; exit_time = b['_dt']; break
            if h >= tp:
                outcome = 'WIN'; exit_time = b['_dt']; break
        else:
            post_fill_high = max(post_fill_high, h)
            post_fill_low = min(post_fill_low, l)
            if h >= sl:
                outcome = 'LOSS'; exit_time = b['_dt']; break
            if l <= tp:
                outcome = 'WIN'; exit_time = b['_dt']; break
    if not filled:
        return (None, None, 'UNFILLED', None, None, None)
    risk = abs(entry - sl)
    r_to_tp = abs(tp - entry) / risk if risk else 0
    if direction == 'LONG':
        mfe_r = (post_fill_high - entry) / risk if post_fill_high > -1e17 else 0
        mae_r = (entry - post_fill_low) / risk if post_fill_low < 1e17 else 0
    else:
        mfe_r = (entry - post_fill_low) / risk if post_fill_low < 1e17 else 0
        mae_r = (post_fill_high - entry) / risk if post_fill_high > -1e17 else 0
    return (fill_time, exit_time, outcome, mfe_r, mae_r, r_to_tp)


print('=== LOSSES — proper post-fill excursions ===')
for c in sorted(losses, key=lambda r: r['candle_time']):
    ft, et, out, mfe, mae, rtp = find_fill_exit(c)
    print(f'  {c["candle_time"]} dir={c["direction"]:5s} fill={ft} exit={et} sim_outcome={c["outcome"]} my_outcome={out}  MFE={mfe:.2f}R  MAE={mae:.2f}R  TP_r={rtp:.2f}')

print()
print('=== WINS — MAE coin-flip check (proper post-fill) ===')
for c in sorted(wins, key=lambda r: r['candle_time']):
    ft, et, out, mfe, mae, rtp = find_fill_exit(c)
    coin = mae >= 0.75 if mae is not None else False
    print(f'  {c["candle_time"]} fill={ft} exit={et}  MAE={mae:.2f}R  TP_r={rtp:.2f}  coinflip(MAE>=0.75R)={coin}')

print()
# Also compute fill lag in minutes
print('=== Fill lag (candle_time -> fill) for all CANDIDATEs ===')
import statistics
lags = []
at_market = 0
for c in cands:
    ft, et, out, mfe, mae, rtp = find_fill_exit(c)
    if ft is None:
        print(f'  {c["candle_time"]} UNFILLED')
        continue
    ct = datetime.fromisoformat(c['candle_time'].replace('Z', '+00:00'))
    lag = (ft - ct).total_seconds() / 60
    lags.append((c['candle_time'], lag, c['outcome']))
    if lag <= 15:
        at_market += 1

lags.sort(key=lambda x: x[1])
print(f'n_filled={len(lags)}  at_market(<=15min)={at_market}')
print(f'median lag={statistics.median(l[1] for l in lags):.0f}min')
print(f'mean lag={statistics.mean(l[1] for l in lags):.0f}min')
print(f'max lag={max(l[1] for l in lags):.0f}min')
# Distribution by lag bucket
buckets = [(0, 15, '<=15min'), (15, 60, '15-60min'), (60, 240, '1-4h'), (240, 720, '4-12h'), (720, 10**9, '>12h')]
for lo, hi, lbl in buckets:
    in_bucket = [l for l in lags if lo < l[1] <= hi or (lo == 0 and l[1] <= 15)]
    wins = sum(1 for l in in_bucket if l[2] == 'WIN')
    losses = sum(1 for l in in_bucket if l[2] == 'LOSS')
    unf = sum(1 for l in in_bucket if l[2] == 'UNFILLED')
    print(f'  lag {lbl}: n={len(in_bucket)} W={wins} L={losses} U={unf}')
