"""
TEST: Asian Range Sweep as Directional Bias
CLAIM: Video 23 says when Asian high is taken first → bullish, Asian low first → bearish.
         Video 24 says Asian range sweep determines turtle soup direction on gold.
QUESTION: Does the order of Asian range sweep predict XAUUSD direction in London?

Uses M15 XAUUSD data to:
1. Define Asian range (00:00-04:00 UTC / 8pm-midnight ET)
2. Track which side gets swept first in London (04:00-12:00 UTC)
3. Measure continuation in the predicted direction
"""
import pandas as pd
import numpy as np
from scipy import stats
import os

project = '/Users/borr/Documents/trading/gold-agent'
data_file = f'{project}/data/historical/XAUUSD_M15.csv'

df = pd.read_csv(data_file, parse_dates=['time'])
df = df.sort_values('time').reset_index(drop=True)

# Extract hour (UTC)
df['hour'] = df['time'].dt.hour
df['date'] = df['time'].dt.date

results = []

for date, day_data in df.groupby('date'):
    # Asian session: 20:00-00:00 UTC (previous day 20:00 to current 00:00)
    # Approximate: use 00:00-04:00 UTC as Asian range (midnight-4am UTC = 8pm-midnight ET)
    asian = day_data[(day_data['hour'] >= 0) & (day_data['hour'] < 4)]
    if len(asian) < 4:
        continue

    asian_high = asian['high'].max()
    asian_low = asian['low'].min()
    asian_range = asian_high - asian_low

    if asian_range < 1.0:  # Skip tiny ranges
        continue

    # London session: 04:00-12:00 UTC (approximation)
    london = day_data[(day_data['hour'] >= 4) & (day_data['hour'] < 12)]
    if len(london) < 8:
        continue

    # Track which side of Asian range gets swept first
    high_swept_time = None
    low_swept_time = None

    for _, candle in london.iterrows():
        if high_swept_time is None and candle['high'] > asian_high:
            high_swept_time = candle['time']
        if low_swept_time is None and candle['low'] < asian_low:
            low_swept_time = candle['time']

    if high_swept_time is None and low_swept_time is None:
        continue  # No sweep — no signal

    # Determine predicted direction
    if high_swept_time is not None and low_swept_time is not None:
        if high_swept_time < low_swept_time:
            predicted = 'BEARISH'  # High swept first → bearish
            sweep_time = high_swept_time
        else:
            predicted = 'BULLISH'  # Low swept first → bullish
            sweep_time = low_swept_time
    elif high_swept_time is not None:
        predicted = 'BEARISH'  # Only high swept → bearish
        sweep_time = high_swept_time
    else:
        predicted = 'BULLISH'  # Only low swept → bullish
        sweep_time = low_swept_time

    # Measure: what happened AFTER the sweep for the rest of London?
    post_sweep = london[london['time'] > sweep_time]
    if len(post_sweep) < 2:
        continue

    # Direction of remaining London candles
    london_open_after = post_sweep.iloc[0]['open']
    london_close = post_sweep.iloc[-1]['close']
    actual_move = london_close - london_open_after
    actual_direction = 'BULLISH' if actual_move > 0 else 'BEARISH'

    correct = predicted == actual_direction
    move_r = abs(actual_move) / asian_range  # Normalize by Asian range

    results.append({
        'date': date,
        'asian_high': asian_high,
        'asian_low': asian_low,
        'asian_range': asian_range,
        'predicted': predicted,
        'actual': actual_direction,
        'correct': correct,
        'move_pips': actual_move,
        'move_r': move_r
    })

rdf = pd.DataFrame(results)
print(f"Total days with Asian sweep: {len(rdf)}")
print(f"Correct predictions: {rdf['correct'].sum()}/{len(rdf)} ({rdf['correct'].mean()*100:.1f}%)")

# By direction
for d in ['BULLISH', 'BEARISH']:
    subset = rdf[rdf['predicted'] == d]
    if len(subset) > 0:
        acc = subset['correct'].mean()
        print(f"  {d} predictions: {subset['correct'].sum()}/{len(subset)} ({acc*100:.1f}%)")

# Statistical test: is accuracy > 50%?
successes = rdf['correct'].sum()
n = len(rdf)
p_binom = stats.binomtest(successes, n, 0.5, alternative='greater').pvalue
print(f"\nBinomial test (H0: accuracy=50%): p={p_binom:.4f}")

# Wilson CI
from math import sqrt
z = 1.96
p_hat = successes / n
denom = 1 + z**2/n
center = (p_hat + z**2/(2*n)) / denom
spread = z * sqrt((p_hat*(1-p_hat) + z**2/(4*n)) / n) / denom
print(f"Wilson 95% CI: [{center-spread:.3f}, {center+spread:.3f}]")

# Average R-multiple when correct vs incorrect
correct_r = rdf[rdf['correct']]['move_r']
incorrect_r = rdf[~rdf['correct']]['move_r']
print(f"\nAvg move when correct: {correct_r.mean():.2f}x Asian range")
print(f"Avg move when incorrect: {incorrect_r.mean():.2f}x Asian range")

print(f"\n{'='*60}")
print("DECISION GATE:")
if p_binom < 0.05 and (center - spread) > 0.55:
    print(f"  CONFIRMED: Asian sweep direction predicts London move")
    print(f"  Accuracy: {successes}/{n} = {successes/n*100:.1f}% (p={p_binom:.4f})")
    print(f"  ACTION: Add Asian sweep filter to London session entries (WF-2)")
elif p_binom < 0.10:
    print(f"  SUGGESTIVE: Trend exists but needs more data")
    print(f"  ACTION: Track Asian sweeps during WF-1 for validation")
else:
    print(f"  INCONCLUSIVE or REJECTED: p={p_binom:.4f}")
    print(f"  Asian sweep may not reliably predict London direction on gold")
