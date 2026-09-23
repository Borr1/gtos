#!/usr/bin/env python3
"""
Session 9 — Task 4: DXY-Gold Correlation Analysis
"""
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_29/generated/session9")

print("=" * 80)
print("TASK 4: DXY-GOLD CORRELATION ANALYSIS")
print("=" * 80)

# Download data
print("\nDownloading DXY (DX-Y.NYB) and Gold (GC=F)...")
dxy = yf.download('DX-Y.NYB', start='2023-01-01', end='2026-04-05', progress=False)
gold = yf.download('GC=F', start='2023-01-01', end='2026-04-05', progress=False)

# Flatten multi-level columns
for df in [dxy, gold]:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

print(f"DXY: {len(dxy)} bars ({dxy.index[0].date()} to {dxy.index[-1].date()})")
print(f"Gold: {len(gold)} bars ({gold.index[0].date()} to {gold.index[-1].date()})")

# Align on common dates
merged = pd.DataFrame({
    'DXY': dxy['Close'],
    'Gold': gold['Close']
}).dropna()

print(f"Merged: {len(merged)} common trading days")

# Compute returns
merged['DXY_Return'] = merged['DXY'].pct_change()
merged['Gold_Return'] = merged['Gold'].pct_change()
merged.dropna(inplace=True)

# =============================================================================
print("\n" + "=" * 60)
print("OVERALL CORRELATION")
print("=" * 60)

corr_pearson, p_pearson = stats.pearsonr(merged['DXY_Return'], merged['Gold_Return'])
corr_spearman, p_spearman = stats.spearmanr(merged['DXY_Return'], merged['Gold_Return'])

print(f"Pearson correlation: {corr_pearson:.4f} (p={p_pearson:.2e})")
print(f"Spearman correlation: {corr_spearman:.4f} (p={p_spearman:.2e})")
print(f"Interpretation: {'Significant inverse' if corr_pearson < -0.1 and p_pearson < 0.05 else 'Weak or not significant'}")

# =============================================================================
print("\n" + "=" * 60)
print("ROLLING 30-DAY CORRELATION")
print("=" * 60)

merged['Rolling_Corr_30'] = merged['DXY_Return'].rolling(30).corr(merged['Gold_Return'])
merged['Rolling_Corr_60'] = merged['DXY_Return'].rolling(60).corr(merged['Gold_Return'])

# Stats on rolling correlation
rc = merged['Rolling_Corr_30'].dropna()
print(f"30-day rolling correlation stats:")
print(f"  Mean: {rc.mean():.4f}")
print(f"  Std:  {rc.std():.4f}")
print(f"  Min:  {rc.min():.4f} on {rc.idxmin().date()}")
print(f"  Max:  {rc.max():.4f} on {rc.idxmax().date()}")
print(f"  % of time positive: {(rc > 0).mean()*100:.1f}%")
print(f"  % of time < -0.3 (strong inverse): {(rc < -0.3).mean()*100:.1f}%")

# Identify breakdown periods (correlation > 0 for sustained period)
print("\n" + "=" * 60)
print("CORRELATION BREAKDOWN PERIODS (30-day corr > 0)")
print("=" * 60)

positive_periods = merged[merged['Rolling_Corr_30'] > 0]
if len(positive_periods) > 0:
    # Find contiguous positive periods
    pos_idx = positive_periods.index
    gaps = pd.Series(pos_idx).diff()
    # Group by contiguous periods (gap > 3 business days = new period)
    group_id = 0
    groups = [0]
    for i in range(1, len(gaps)):
        if gaps.iloc[i].days > 5:
            group_id += 1
        groups.append(group_id)

    positive_periods = positive_periods.copy()
    positive_periods['Group'] = groups

    print(f"\n{'Start':>12} | {'End':>12} | {'Duration':>10} | {'Avg Corr':>10} | {'Gold Δ':>10} | {'DXY Δ':>10}")
    print(f"{'-'*12}-+-{'-'*12}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

    for g in positive_periods['Group'].unique():
        subset = positive_periods[positive_periods['Group'] == g]
        if len(subset) >= 5:  # Only show sustained breakdowns (5+ days)
            start = subset.index[0]
            end = subset.index[-1]
            dur = (end - start).days
            avg_corr = subset['Rolling_Corr_30'].mean()
            gold_change = (merged.loc[end, 'Gold'] / merged.loc[start, 'Gold'] - 1) * 100
            dxy_change = (merged.loc[end, 'DXY'] / merged.loc[start, 'DXY'] - 1) * 100
            print(f"{start.date()} | {end.date()} | {dur:>8}d | {avg_corr:>+9.3f} | {gold_change:>+9.1f}% | {dxy_change:>+9.1f}%")

# =============================================================================
# Charts
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

# 1. Price overlay (dual axis)
ax1 = axes[0]
ax2 = ax1.twinx()
ax1.plot(merged.index, merged['Gold'], 'gold', linewidth=1.5, label='Gold')
ax2.plot(merged.index, merged['DXY'], 'steelblue', linewidth=1.5, label='DXY')
ax1.set_ylabel('Gold Price', color='goldenrod')
ax2.set_ylabel('DXY', color='steelblue')
ax1.set_title('Gold vs DXY (2023-2026)')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# 2. Rolling correlation
axes[1].plot(merged.index, merged['Rolling_Corr_30'], 'purple', linewidth=1, alpha=0.7, label='30-day')
axes[1].plot(merged.index, merged['Rolling_Corr_60'], 'darkblue', linewidth=1.5, alpha=0.9, label='60-day')
axes[1].axhline(y=0, color='black', linewidth=0.5)
axes[1].axhline(y=-0.3, color='red', linewidth=0.5, linestyle='--', alpha=0.5)
axes[1].fill_between(merged.index, 0, merged['Rolling_Corr_30'],
                     where=merged['Rolling_Corr_30'] > 0, alpha=0.3, color='red', label='Breakdown zone')
axes[1].set_title('Rolling DXY-Gold Correlation')
axes[1].set_ylabel('Correlation')
axes[1].legend()
axes[1].set_ylim(-1, 1)

# 3. Scatter plot
axes[2].scatter(merged['DXY_Return']*100, merged['Gold_Return']*100, alpha=0.3, s=10)
# Regression line
slope, intercept, r, p, se = stats.linregress(merged['DXY_Return']*100, merged['Gold_Return']*100)
x_range = np.linspace(merged['DXY_Return'].min()*100, merged['DXY_Return'].max()*100, 100)
axes[2].plot(x_range, slope * x_range + intercept, 'r-', linewidth=2,
             label=f'y={slope:.2f}x + {intercept:.4f}, R²={r**2:.3f}')
axes[2].set_xlabel('DXY Daily Return %')
axes[2].set_ylabel('Gold Daily Return %')
axes[2].set_title('DXY vs Gold Daily Returns')
axes[2].legend()
axes[2].axhline(y=0, color='black', linewidth=0.3)
axes[2].axvline(x=0, color='black', linewidth=0.3)

plt.tight_layout()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
outpath = OUTPUT_DIR / 'session9_dxy_gold_correlation.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight')
print(f"\nChart saved: {outpath}")

# =============================================================================
print("\n" + "=" * 60)
print("REGRESSION DETAILS")
print("=" * 60)
print(f"Slope: {slope:.4f} (a 1% DXY move → {slope:.2f}% gold move)")
print(f"R²: {r**2:.4f}")
print(f"Standard error: {se:.4f}")

print("\n" + "=" * 80)
print("TASK 4 COMPLETE")
print("=" * 80)
