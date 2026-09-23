"""Deep per-trade dive: losses post-mortem, winners time-to-TP, SHORT investigation."""
import json
import glob
import re
import os
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
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


# Enrich
for c in cands:
    p = parse_raw(c)
    c['_parsed'] = p
    if p:
        reasoning = p.get('reasoning', {}) or {}
        c['confidence_score'] = p.get('confidence_score')
        c['model_used'] = p.get('model_used', '?')
        db = reasoning.get('daily_bias', {}) or {}
        c['bias_confidence'] = db.get('confidence')
        h1 = reasoning.get('h1_setup', {}) or {}
        c['poi_type'] = h1.get('poi_type')
        c['poi_zone'] = h1.get('zone')
        c['causing_event_type'] = h1.get('causing_event_type')
        c['fib_pct'] = h1.get('fib_retracement_pct')
        liq = reasoning.get('liquidity_sweep', {}) or {}
        c['sweep_detected'] = liq.get('detected')
        c['sweep_pool_type'] = liq.get('pool_type')
        c['sweep_quality'] = liq.get('quality') or liq.get('sweep_quality')
        m15 = reasoning.get('m15_confirmation', {}) or {}
        c['m15_choch'] = m15.get('choch_detected')
        c['disp_quality'] = m15.get('displacement_quality')
        c['disp_ratio'] = m15.get('displacement_candle_body_vs_avg_ratio')
        c['overall_reasoning'] = reasoning.get('overall_reasoning', '')
        c['confidence_computation'] = p.get('confidence_computation', '')


wins = [c for c in cands if c.get('outcome') == 'WIN']
losses = [c for c in cands if c.get('outcome') == 'LOSS']
unfilled = [c for c in cands if c.get('outcome') == 'UNFILLED']

# Load M15 CSV for price verification
CSV_PATH = 'data/historical_2026/NAS100_M15.csv'
bars = []
with open(CSV_PATH) as fh:
    rdr = csv.DictReader(fh)
    for row in rdr:
        bars.append(row)
print(f'Loaded {len(bars)} M15 bars. Headers: {list(bars[0].keys())}')
# Build index by iso timestamp (handle both naive and with-tz)
bar_index = {}
for b in bars:
    t_str = b.get('time') or b.get('timestamp') or b.get('datetime') or b.get('Time') or b.get('date')
    if t_str is None:
        continue
    # normalize to aware UTC
    t_clean = t_str.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(t_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    except Exception:
        continue
    b['_dt'] = dt
    bar_index[dt.replace(tzinfo=timezone.utc)] = b


def ct_utc(r):
    s = r['candle_time']
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def exit_utc(r):
    s = r.get('exit_candle')
    if not s:
        return None
    return datetime.fromisoformat(s.replace('Z', '+00:00'))


def bar_at(dt):
    # Find bar with exact match; fallback to nearest earlier
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if dt_utc in bar_index:
        return bar_index[dt_utc]
    # fallback
    sorted_times = sorted(bar_index.keys())
    for t in sorted_times:
        if t >= dt_utc:
            return bar_index[t]
    return None


def bars_between(start_dt, end_dt):
    """Return bars with _dt in [start_dt, end_dt] inclusive."""
    start = start_dt.astimezone(timezone.utc) if start_dt.tzinfo else start_dt.replace(tzinfo=timezone.utc)
    end = end_dt.astimezone(timezone.utc) if end_dt.tzinfo else end_dt.replace(tzinfo=timezone.utc)
    out = []
    for b in bars:
        if '_dt' not in b:
            continue
        if start <= b['_dt'] <= end:
            out.append(b)
    return out


# ===== Per-trade table =====
print()
print('=== PER-TRADE TABLE ===')
header = f'{"#":>2} {"slice":>5} {"candle_time":<20} {"kz":<7} {"dir":<5} {"grade":<5} {"disp_r":>6} {"conf":>5} {"model":<16} {"outcome":<10} {"r":>5}'
print(header)
print('-' * len(header))
for i, c in enumerate(sorted(cands, key=lambda r: r['candle_time'])):
    print(f"{i+1:>2} {c['_slice']:>5} {c['candle_time']:<20} {c.get('kill_zone','?'):<7} {c.get('direction','?'):<5} {c.get('setup_grade','?'):<5} "
          f"{str(c.get('disp_ratio','?')):>6} {str(c.get('confidence_score','?')):>5} {str(c.get('model_used','?'))[:16]:<16} "
          f"{c.get('outcome','?'):<10} {str(c.get('r_multiple','?')):>5}")


# ===== LOSSES DEEP DIVE =====
print()
print('=' * 100)
print('LOSSES — FULL FEATURE TABLE')
print('=' * 100)
for i, c in enumerate(sorted(losses, key=lambda r: r['candle_time'])):
    print(f'\nLoss #{i+1}: {c["candle_time"]}  slice={c["_slice"]}  kz={c.get("kill_zone")}  dir={c.get("direction")}')
    print(f'  entry={c.get("entry_price")}  SL={c.get("stop_loss")}  TP1={c.get("take_profit_1")}  r={c.get("r_multiple")}  exit_candle={c.get("exit_candle")}')
    print(f'  model={c.get("model_used")}  setup_grade={c.get("setup_grade")}  confidence_score={c.get("confidence_score")}  conf_comp={c.get("confidence_computation")}')
    print(f'  bias={c.get("bias")} (conf={c.get("bias_confidence")}) bias_source={c.get("bias_source")}')
    print(f'  poi_type={c.get("poi_type")} zone={c.get("poi_zone")} causing_event={c.get("causing_event_type")} fib={c.get("fib_pct")}')
    print(f'  sweep_detected={c.get("sweep_detected")} pool={c.get("sweep_pool_type")} quality={c.get("sweep_quality")}')
    print(f'  m15: choch={c.get("m15_choch")} disp_quality={c.get("disp_quality")} disp_ratio={c.get("disp_ratio")}')
    print(f'  reasoning: {(c.get("overall_reasoning") or "")[:250]}')


# ===== POST-LOSS price action check =====
print()
print('=' * 100)
print('LOSSES — POST-SL PRICE ACTION (would TP have been hit within +6 hours of loss close?)')
print('=' * 100)
for c in sorted(losses, key=lambda r: r['candle_time']):
    ct = ct_utc(c)
    ex = exit_utc(c)
    if ex is None:
        print(f'  {c["candle_time"]}: no exit_candle, skipping')
        continue
    # Look 6h AFTER the exit candle for whether price subsequently reached the TP
    tp = c.get('take_profit_1')
    sl = c.get('stop_loss')
    direction = c.get('direction')
    after = bars_between(ex + timedelta(minutes=15), ex + timedelta(hours=6))
    reached_tp = False
    max_favor = -1e9
    for b in after:
        try:
            h = float(b['high'])
            l = float(b['low'])
        except Exception:
            continue
        if direction == 'LONG':
            if h >= tp:
                reached_tp = True
        else:
            if l <= tp:
                reached_tp = True
    # also compute max excursion vs entry from loss's entry to exit (to show how close to TP price got)
    entry = c.get('entry_price')
    e_low = None
    e_high = None
    during_exit = bar_at(ex)
    if during_exit is not None:
        try:
            e_low = float(during_exit['low'])
            e_high = float(during_exit['high'])
        except Exception:
            pass
    # max favorable excursion between entry fill and SL hit
    fills = bars_between(ct + timedelta(minutes=15), ex)
    max_favor_price = None
    if direction == 'LONG':
        max_favor_price = max((float(b['high']) for b in fills if 'high' in b), default=None)
    else:
        max_favor_price = min((float(b['low']) for b in fills if 'low' in b), default=None)
    if max_favor_price is not None and entry is not None and sl is not None:
        risk = abs(entry - sl)
        if direction == 'LONG':
            mfe_r = (max_favor_price - entry) / risk if risk else 0
        else:
            mfe_r = (entry - max_favor_price) / risk if risk else 0
    else:
        mfe_r = None
    print(f'  {c["candle_time"]} exit={c.get("exit_candle")} dir={direction} entry={entry} SL={sl} TP={tp}  '
          f'MFE_r_before_SL={mfe_r:.2f}  recovered_to_TP_within_6h_after={reached_tp}' if mfe_r is not None else
          f'  {c["candle_time"]} exit={c.get("exit_candle")} dir={direction} entry={entry} SL={sl} TP={tp}  MFE_r=NA  recovered_to_TP_within_6h_after={reached_tp}')


# ===== WINS TIME-TO-TP =====
print()
print('=' * 100)
print('WINS — time-to-TP')
print('=' * 100)
time_to_tp = []
for c in sorted(wins, key=lambda r: r['candle_time']):
    ct = ct_utc(c)
    ex = exit_utc(c)
    if ex is None:
        continue
    dur = (ex - ct).total_seconds() / 60
    time_to_tp.append(dur)
    print(f'  {c["candle_time"]} exit={c.get("exit_candle")} duration={dur:.0f}min direction={c.get("direction")} entry={c.get("entry_price")} TP={c.get("take_profit_1")}')

if time_to_tp:
    import statistics
    print(f'\n  n={len(time_to_tp)}  min={min(time_to_tp):.0f}min  max={max(time_to_tp):.0f}min  median={statistics.median(time_to_tp):.0f}min  mean={statistics.mean(time_to_tp):.0f}min')

# ===== WINS: coin-flip check (did SL get close before reversing)? =====
print()
print('=== WINS — max adverse excursion (MAE) before hitting TP ===')
for c in sorted(wins, key=lambda r: r['candle_time']):
    ct = ct_utc(c)
    ex = exit_utc(c)
    if ex is None:
        continue
    entry = c.get('entry_price')
    sl = c.get('stop_loss')
    direction = c.get('direction')
    # bars from entry candle (inclusive) to exit candle (inclusive) — simulate after fill
    seg = bars_between(ct + timedelta(minutes=15), ex)
    if direction == 'LONG':
        min_low = min((float(b['low']) for b in seg if 'low' in b), default=None)
        mae = (entry - min_low) / abs(entry - sl) if min_low is not None else None
    else:
        max_high = max((float(b['high']) for b in seg if 'high' in b), default=None)
        mae = (max_high - entry) / abs(sl - entry) if max_high is not None else None
    coinflip = mae is not None and mae >= 0.75
    print(f'  {c["candle_time"]} MAE_r={mae:.2f}  coinflip_near_SL={coinflip}' if mae is not None else f'  {c["candle_time"]} MAE=NA')


# ===== SHORT investigation =====
print()
print('=' * 100)
print('SHORT INVESTIGATION')
print('=' * 100)
shorts = [c for c in cands if c.get('direction') == 'SHORT']
for s in shorts:
    print(f'\nSHORT at {s["candle_time"]} slice={s["_slice"]}')
    print(f'  entry={s.get("entry_price")} SL={s.get("stop_loss")} TP={s.get("take_profit_1")} r={s.get("r_multiple")}')
    print(f'  kz={s.get("kill_zone")} bias={s.get("bias")} bias_source={s.get("bias_source")}')
    print(f'  model={s.get("model_used")} confidence_score={s.get("confidence_score")}')
    print(f'  poi_type={s.get("poi_type")} zone={s.get("poi_zone")} causing_event={s.get("causing_event_type")}')
    print(f'  reasoning: {(s.get("overall_reasoning") or "")[:500]}')

# Downward moves >1.5% -> check AI response
print()
print('=== Downward >=1.5% moves in NAS100 (rolling 4-hour window) — what was AI deciding? ===')
# Use hourly view from m15: slide window of 16 bars (4h) and find peak-to-trough ratio
sorted_bars = sorted(bars, key=lambda b: b.get('_dt') or datetime.min.replace(tzinfo=timezone.utc))
# annotate
window = 16
for i in range(window, len(sorted_bars)):
    seg = sorted_bars[i - window:i]
    try:
        highs = [float(b['high']) for b in seg]
        lows = [float(b['low']) for b in seg]
    except Exception:
        continue
    hi = max(highs)
    lo = min(lows)
    idx_hi = highs.index(hi)
    idx_lo = lows.index(lo)
    if idx_lo > idx_hi:  # trough after peak
        drop = (hi - lo) / hi * 100
        if drop >= 1.5:
            t_start = seg[0]['_dt']
            t_end = seg[-1]['_dt']
            # What did AI decide in kill zones on that day?
            date_key = t_end.date()
            sim_day = [r for r in all_records if r.get('date') == str(date_key)]
            evs = Counter(r.get('decision') for r in sim_day)
            short_count = sum(1 for r in sim_day if r.get('decision') == 'CANDIDATE' and r.get('direction') == 'SHORT')
            short_ntres = sum(1 for r in sim_day if r.get('decision') == 'NO_TRADE' and 'short' in (r.get('bias') or '').lower())
            print(f'  {t_start.isoformat()} to {t_end.isoformat()} drop={drop:.2f}%   day_decisions={dict(evs)}  SHORT_CANDs={short_count}  bearish_bias_NOTRADEs={short_ntres}')
