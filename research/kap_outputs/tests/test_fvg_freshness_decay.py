"""
TEST: FVG Freshness Decay
CLAIM: Video 20 (Trader Zan, 10yr quant backtest) says FVGs are strongest when fresh —
       edge decays as time passes. Restricting to 10-11am captures freshest FVGs.
QUESTION: Do FVGs that get filled quickly have higher continuation rates than stale ones?

Uses M15 XAUUSD data to detect FVGs and measure fill rates by age.
"""
import pandas as pd
import numpy as np
from scipy import stats
import os

project = '/Users/borr/Documents/trading/gold-agent'
data_file = f'{project}/data/historical/XAUUSD_M15.csv'

df = pd.read_csv(data_file, parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

# Detect Fair Value Gaps (3-candle pattern)
fvgs = []
for i in range(2, len(df)):
    c1 = df.iloc[i-2]  # First candle
    c2 = df.iloc[i-1]  # Middle candle (displacement)
    c3 = df.iloc[i]    # Third candle

    # Bullish FVG: candle 1 high < candle 3 low (gap up)
    if c1['high'] < c3['low']:
        fvgs.append({
            'type': 'bullish',
            'time_created': c3['time'],
            'gap_top': c3['low'],
            'gap_bottom': c1['high'],
            'gap_size': c3['low'] - c1['high'],
            'displacement_size': abs(c2['close'] - c2['open']),
            'idx': i
        })

    # Bearish FVG: candle 1 low > candle 3 high (gap down)
    if c1['low'] > c3['high']:
        fvgs.append({
            'type': 'bearish',
            'time_created': c3['time'],
            'gap_top': c1['low'],
            'gap_bottom': c3['high'],
            'gap_size': c1['low'] - c3['high'],
            'displacement_size': abs(c2['close'] - c2['open']),
            'idx': i
        })

print(f"Total FVGs detected on M15: {len(fvgs)}")
print(f"  Bullish: {sum(1 for f in fvgs if f['type']=='bullish')}")
print(f"  Bearish: {sum(1 for f in fvgs if f['type']=='bearish')}")

# For each FVG, measure:
# 1. Time until first touch (candles)
# 2. Whether price continued in FVG direction after fill
# 3. How far price moved after touching FVG (in multiples of gap size)

results = []
for fvg in fvgs:
    idx = fvg['idx']
    gap_mid = (fvg['gap_top'] + fvg['gap_bottom']) / 2

    # Look forward up to 48 candles (12 hours on M15)
    fill_candle = None
    for j in range(idx + 1, min(idx + 49, len(df))):
        candle = df.iloc[j]
        if fvg['type'] == 'bullish':
            # Price retraces down to touch FVG
            if candle['low'] <= fvg['gap_top']:
                fill_candle = j
                break
        else:
            # Price retraces up to touch FVG
            if candle['high'] >= fvg['gap_bottom']:
                fill_candle = j
                break

    if fill_candle is None:
        continue  # Never filled — skip

    candles_to_fill = fill_candle - idx
    fill_time = df.iloc[fill_candle]['time']

    # Measure continuation: what happened in next 8 candles (2 hours) after fill?
    post_fill = df.iloc[fill_candle:fill_candle + 9]
    if len(post_fill) < 4:
        continue

    fill_price = df.iloc[fill_candle]['close']
    post_high = post_fill['high'].max()
    post_low = post_fill['low'].min()

    if fvg['type'] == 'bullish':
        # Continuation = price goes up after filling bullish FVG
        continuation = post_high - fill_price
        adverse = fill_price - post_low
    else:
        # Continuation = price goes down after filling bearish FVG
        continuation = fill_price - post_low
        adverse = post_high - fill_price

    cont_r = continuation / max(fvg['gap_size'], 0.5)  # Normalize
    adv_r = adverse / max(fvg['gap_size'], 0.5)
    success = cont_r > adv_r  # More continuation than adverse = success

    results.append({
        'type': fvg['type'],
        'candles_to_fill': candles_to_fill,
        'gap_size': fvg['gap_size'],
        'continuation_r': cont_r,
        'adverse_r': adv_r,
        'success': success,
        'net_r': cont_r - adv_r
    })

rdf = pd.DataFrame(results)
print(f"\nFVGs filled (testable): {len(rdf)}")

# Bucket by freshness
buckets = [
    ('Fresh (1-4 candles)', 1, 4),
    ('Medium (5-12 candles)', 5, 12),
    ('Stale (13-24 candles)', 13, 24),
    ('Very stale (25-48 candles)', 25, 48),
]

print(f"\n{'Freshness':<30} {'N':>6} {'WR':>7} {'Avg Cont R':>12} {'Avg Net R':>11}")
print("-"*70)

bucket_data = {}
for label, lo, hi in buckets:
    subset = rdf[(rdf['candles_to_fill'] >= lo) & (rdf['candles_to_fill'] <= hi)]
    if len(subset) > 0:
        wr = subset['success'].mean()
        avg_cont = subset['continuation_r'].mean()
        avg_net = subset['net_r'].mean()
        print(f"{label:<30} {len(subset):>6} {wr:>6.1%} {avg_cont:>12.2f} {avg_net:>+11.2f}")
        bucket_data[label] = {'n': len(subset), 'wr': wr, 'net_r': avg_net}

# Statistical test: is fresh significantly better than stale?
fresh = rdf[rdf['candles_to_fill'] <= 4]['net_r']
stale = rdf[rdf['candles_to_fill'] > 12]['net_r']

if len(fresh) > 10 and len(stale) > 10:
    t_stat, p_val = stats.ttest_ind(fresh, stale)
    print(f"\nFresh vs Stale t-test: t={t_stat:.3f}, p={p_val:.4f}")
    print(f"  Fresh avg net R: {fresh.mean():.3f}")
    print(f"  Stale avg net R: {stale.mean():.3f}")
    print(f"  Difference: {fresh.mean() - stale.mean():+.3f}")

# Correlation: candles_to_fill vs net_r
corr, p_corr = stats.pearsonr(rdf['candles_to_fill'], rdf['net_r'])
print(f"\nCorrelation (age vs outcome): r={corr:.3f}, p={p_corr:.4f}")

print(f"\n{'='*60}")
print("DECISION GATE:")
if len(fresh) > 10 and len(stale) > 10:
    if p_val < 0.05 and fresh.mean() > stale.mean():
        print(f"  CONFIRMED: Fresh FVGs outperform stale ones (p={p_val:.4f})")
        print(f"  Fresh: {fresh.mean():.3f} net R vs Stale: {stale.mean():.3f} net R")
        print(f"  ACTION: Prioritize recent FVGs in entry selection (WF-2)")
    elif p_val < 0.10:
        print(f"  SUGGESTIVE: Trend towards fresh FVG edge (p={p_val:.4f})")
    else:
        print(f"  INCONCLUSIVE: No significant freshness effect (p={p_val:.4f})")
else:
    print(f"  INSUFFICIENT DATA: Need more samples in fresh/stale buckets")
