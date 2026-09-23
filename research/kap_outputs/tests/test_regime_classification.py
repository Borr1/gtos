#!/usr/bin/env python3
"""
Regime classification: Is 2026 decay caused by regime change?
Classify each month as trending/ranging using ADX(14) on D1.
Compare WR within each regime.
"""
import json, glob, os, sys
import numpy as np

# Load D1 candle data
d1_file = None
for candidate in ['data/historical/XAUUSD_D1.csv', 'data/XAUUSD_D1.csv',
                   'data/historical/XAUUSD_D1_historical.csv']:
    if os.path.exists(candidate):
        d1_file = candidate
        break

if not d1_file:
    # Try to find it
    import subprocess
    result = subprocess.run(['find', '.', '-name', '*D1*', '-name', '*.csv'],
                          capture_output=True, text=True)
    print(f"Available D1 files: {result.stdout}")
    print("ERROR: No D1 file found")
    sys.exit(1)

import pandas as pd

df = pd.read_csv(d1_file)
print(f"Loaded {len(df)} D1 candles from {d1_file}")
print(f"Date range: {df.iloc[0]['time'] if 'time' in df.columns else df.iloc[0][0]} to {df.iloc[-1]['time'] if 'time' in df.columns else df.iloc[-1][0]}")

# Compute ADX(14)
# Need: +DM, -DM, TR, smoothed versions, DX, ADX
high = df['high'].values
low = df['low'].values
close = df['close'].values

def compute_adx(high, low, close, period=14):
    n = len(high)
    tr = np.zeros(n)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)

    for i in range(1, n):
        tr[i] = max(high[i] - low[i],
                     abs(high[i] - close[i-1]),
                     abs(low[i] - close[i-1]))
        up = high[i] - high[i-1]
        down = low[i-1] - low[i]
        plus_dm[i] = up if (up > down and up > 0) else 0
        minus_dm[i] = down if (down > up and down > 0) else 0

    # Smoothed
    atr = np.zeros(n)
    plus_di = np.zeros(n)
    minus_di = np.zeros(n)
    dx = np.zeros(n)
    adx = np.zeros(n)

    atr[period] = np.sum(tr[1:period+1])
    s_plus = np.sum(plus_dm[1:period+1])
    s_minus = np.sum(minus_dm[1:period+1])

    for i in range(period+1, n):
        atr[i] = atr[i-1] - atr[i-1]/period + tr[i]
        s_plus = s_plus - s_plus/period + plus_dm[i]
        s_minus = s_minus - s_minus/period + minus_dm[i]

        if atr[i] > 0:
            plus_di[i] = 100 * s_plus / atr[i]
            minus_di[i] = 100 * s_minus / atr[i]

        di_sum = plus_di[i] + minus_di[i]
        if di_sum > 0:
            dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / di_sum

    # ADX = smoothed DX
    adx[2*period] = np.mean(dx[period+1:2*period+1])
    for i in range(2*period+1, n):
        adx[i] = (adx[i-1] * (period-1) + dx[i]) / period

    return adx

adx = compute_adx(high, low, close)
df['adx'] = adx

# Extract month from date
if 'time' in df.columns:
    df['month'] = pd.to_datetime(df['time']).dt.to_period('M')
else:
    df['month'] = pd.to_datetime(df.iloc[:, 0]).dt.to_period('M')

# Monthly ADX average
monthly_adx = df[df['adx'] > 0].groupby('month')['adx'].mean()
print("\n=== MONTHLY ADX (D1) ===")
for month, adx_val in monthly_adx.items():
    regime = "TRENDING" if adx_val >= 25 else "RANGING"
    print(f"  {month}: ADX={adx_val:.1f} → {regime}")

# Now load trades and match to regime
sessions_dir = None
for candidate in ['knowledge_base_backtest/sessions', 'data/batch_sessions']:
    if os.path.isdir(candidate):
        sessions_dir = candidate
        break

trades = []
for f in sorted(glob.glob(os.path.join(sessions_dir, '**/*.json'), recursive=True)):
    try:
        d = json.load(open(f))
        ts = d.get('trade_summary', {})
        if not (isinstance(ts, dict) and ts.get('trade_taken')):
            continue
        date = d.get('date', '')
        if date:
            month = pd.Period(date[:7], freq='M')
            adx_val = monthly_adx.get(month, 0)
            trades.append({
                'date': date,
                'month': str(month),
                'r_multiple': ts.get('r_multiple', 0),
                'win': 1 if ts.get('outcome') == 'WIN' else 0,
                'adx': adx_val,
                'regime': 'TRENDING' if adx_val >= 25 else 'RANGING',
            })
    except:
        continue

print(f"\nLoaded {len(trades)} trades with regime classification")

# Compare WR by regime
trending = [t for t in trades if t['regime'] == 'TRENDING']
ranging = [t for t in trades if t['regime'] == 'RANGING']

print(f"\n=== WR BY REGIME ===")
if trending:
    wr_t = np.mean([t['win'] for t in trending])
    avg_r_t = np.mean([t['r_multiple'] for t in trending])
    print(f"TRENDING: {wr_t:.1%} WR, {avg_r_t:.3f} avg R (n={len(trending)})")
if ranging:
    wr_r = np.mean([t['win'] for t in ranging])
    avg_r_r = np.mean([t['r_multiple'] for t in ranging])
    print(f"RANGING:  {wr_r:.1%} WR, {avg_r_r:.3f} avg R (n={len(ranging)})")

if trending and ranging:
    from scipy import stats
    wr_diff = np.mean([t['win'] for t in trending]) - np.mean([t['win'] for t in ranging])

    wins_t = sum(t['win'] for t in trending)
    wins_r = sum(t['win'] for t in ranging)
    table = [[wins_t, len(trending)-wins_t], [wins_r, len(ranging)-wins_r]]
    _, p_fisher = stats.fisher_exact(table)

    r_t = [t['r_multiple'] for t in trending]
    r_r = [t['r_multiple'] for t in ranging]
    _, p_ttest = stats.ttest_ind(r_t, r_r)

    print(f"\nDifference: {wr_diff:+.1%}pp")
    print(f"Fisher p-value (WR): {p_fisher:.4f}")
    print(f"t-test p-value (R): {p_ttest:.4f}")

# 2025 vs 2026 regime breakdown
print(f"\n=== REGIME BY YEAR ===")
for year in [2025, 2026]:
    yr_trades = [t for t in trades if t['date'].startswith(str(year))]
    if yr_trades:
        n_trending = sum(1 for t in yr_trades if t['regime'] == 'TRENDING')
        n_ranging = sum(1 for t in yr_trades if t['regime'] == 'RANGING')
        print(f"{year}: {n_trending} trending, {n_ranging} ranging ({n_trending/(n_trending+n_ranging):.0%} trending)")

print(f"\n=== VERDICT ===")
if trending and ranging:
    if p_fisher < 0.05:
        print("CONFIRMED: Regime significantly affects WR. The 2026 decay may be regime-driven.")
    elif p_fisher < 0.10:
        print("SUGGESTIVE: Regime may affect WR but not yet significant.")
    else:
        print("REJECTED: Regime does NOT significantly affect WR. Decay is NOT regime-driven.")

# Save
result = {
    "test": "regime_classification",
    "date": "2026-04-07",
    "trending_WR": round(np.mean([t['win'] for t in trending]), 3) if trending else None,
    "ranging_WR": round(np.mean([t['win'] for t in ranging]), 3) if ranging else None,
    "p_value": round(p_fisher, 4) if trending and ranging else None,
    "verdict": "check output above"
}
results_file = 'research/kap_outputs/test_results.json'
existing = json.load(open(results_file)) if os.path.exists(results_file) else []
existing.append(result)
with open(results_file, 'w') as f:
    json.dump(existing, f, indent=2)

print(f"\nSaved to {results_file}")
