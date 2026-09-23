#!/usr/bin/env python3
"""
Session 9 — Task 3: Gold Seasonality (Daily data from yfinance)
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
print("TASK 3: GOLD DAILY SEASONALITY ANALYSIS")
print("=" * 80)

# Download gold futures daily data
print("\nDownloading GC=F (gold futures) daily data...")
gold = yf.download('GC=F', start='2022-01-01', end='2026-04-05', progress=False)

if gold.empty:
    print("GC=F failed, trying GLD ETF...")
    gold = yf.download('GLD', start='2022-01-01', end='2026-04-05', progress=False)

# Flatten multi-level columns if needed
if isinstance(gold.columns, pd.MultiIndex):
    gold.columns = gold.columns.get_level_values(0)

print(f"Got {len(gold)} daily bars from {gold.index[0].date()} to {gold.index[-1].date()}")

# Compute returns and volatility
gold['Return'] = gold['Close'].pct_change()
gold['Log_Return'] = np.log(gold['Close'] / gold['Close'].shift(1))
gold['Range_Pct'] = (gold['High'] - gold['Low']) / gold['Close'] * 100
gold['DayOfWeek'] = gold.index.dayofweek  # 0=Mon, 4=Fri
gold['Month'] = gold.index.month
gold.dropna(inplace=True)

day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}

# =============================================================================
print("\n" + "=" * 60)
print("DAY-OF-WEEK ANALYSIS")
print("=" * 60)

print(f"\n{'Day':<12} | {'Mean Return':>12} | {'Std Dev':>10} | {'Avg Range%':>10} | {'n':>5} | {'t-stat':>8} | {'p-value':>8}")
print(f"{'-'*12}-+-{'-'*12}-+-{'-'*10}-+-{'-'*10}-+-{'-'*5}-+-{'-'*8}-+-{'-'*8}")

for dow in range(5):
    subset = gold[gold['DayOfWeek'] == dow]
    mean_ret = subset['Return'].mean()
    std_ret = subset['Return'].std()
    avg_range = subset['Range_Pct'].mean()
    n = len(subset)
    t_stat, p_val = stats.ttest_1samp(subset['Return'].values, 0)

    print(f"{day_names[dow]:<12} | {mean_ret*100:>+11.4f}% | {std_ret*100:>9.4f}% | {avg_range:>9.3f}% | {n:>5} | {t_stat:>+7.2f} | {p_val:>7.4f}")

# Kruskal-Wallis test for day-of-week effect
groups = [gold[gold['DayOfWeek'] == dow]['Return'].values for dow in range(5)]
kw_stat, kw_p = stats.kruskal(*groups)
print(f"\nKruskal-Wallis test (any day-of-week effect?): H={kw_stat:.3f}, p={kw_p:.4f}")
print(f"  {'Significant at 0.05' if kw_p < 0.05 else 'NOT significant'}")

# Day-of-week volatility (range)
groups_range = [gold[gold['DayOfWeek'] == dow]['Range_Pct'].values for dow in range(5)]
kw_stat_r, kw_p_r = stats.kruskal(*groups_range)
print(f"\nKruskal-Wallis (day-of-week VOLATILITY): H={kw_stat_r:.3f}, p={kw_p_r:.4f}")
print(f"  {'Significant at 0.05' if kw_p_r < 0.05 else 'NOT significant'}")

# =============================================================================
print("\n" + "=" * 60)
print("MONTHLY SEASONALITY")
print("=" * 60)

month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
               7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

print(f"\n{'Month':<6} | {'Mean Return':>12} | {'Std Dev':>10} | {'Avg Range%':>10} | {'n':>5} | {'WR (up days)':>12}")
print(f"{'-'*6}-+-{'-'*12}-+-{'-'*10}-+-{'-'*10}-+-{'-'*5}-+-{'-'*12}")

for m in range(1, 13):
    subset = gold[gold['Month'] == m]
    if len(subset) < 5:
        continue
    mean_ret = subset['Return'].mean()
    std_ret = subset['Return'].std()
    avg_range = subset['Range_Pct'].mean()
    n = len(subset)
    wr = (subset['Return'] > 0).mean()

    print(f"{month_names[m]:<6} | {mean_ret*100:>+11.4f}% | {std_ret*100:>9.4f}% | {avg_range:>9.3f}% | {n:>5} | {wr*100:>10.1f}%")

# =============================================================================
# Charts
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Day-of-week returns
dow_returns = gold.groupby('DayOfWeek')['Return'].mean() * 100
axes[0,0].bar([day_names[d] for d in range(5)], dow_returns.values,
              color=['green' if x > 0 else 'red' for x in dow_returns.values])
axes[0,0].set_title('Mean Daily Return by Day of Week (%)')
axes[0,0].axhline(y=0, color='black', linewidth=0.5)
axes[0,0].set_ylabel('Mean Return %')

# 2. Day-of-week volatility (range)
dow_range = gold.groupby('DayOfWeek')['Range_Pct'].mean()
axes[0,1].bar([day_names[d] for d in range(5)], dow_range.values, color='steelblue')
axes[0,1].set_title('Mean Daily Range by Day of Week (%)')
axes[0,1].set_ylabel('Avg High-Low Range %')

# 3. Monthly returns
monthly_returns = gold.groupby('Month')['Return'].mean() * 100
axes[1,0].bar([month_names[m] for m in range(1,13)],
              [monthly_returns.get(m, 0) for m in range(1,13)],
              color=['green' if monthly_returns.get(m,0) > 0 else 'red' for m in range(1,13)])
axes[1,0].set_title('Mean Daily Return by Month (%)')
axes[1,0].tick_params(axis='x', rotation=45)
axes[1,0].axhline(y=0, color='black', linewidth=0.5)

# 4. Monthly volatility
monthly_range = gold.groupby('Month')['Range_Pct'].mean()
axes[1,1].bar([month_names[m] for m in range(1,13)],
              [monthly_range.get(m, 0) for m in range(1,13)], color='steelblue')
axes[1,1].set_title('Mean Daily Range by Month (%)')
axes[1,1].tick_params(axis='x', rotation=45)

plt.tight_layout()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
seasonality_outpath = OUTPUT_DIR / 'session9_gold_seasonality.png'
plt.savefig(seasonality_outpath, dpi=150, bbox_inches='tight')
print(f"\nChart saved: {seasonality_outpath}")

# Try to get intraday data from yfinance (1h, last 730 days max)
print("\n" + "=" * 60)
print("ATTEMPTING HOURLY DATA (yfinance, last 60 days)")
print("=" * 60)

try:
    gold_1h = yf.download('GC=F', period='60d', interval='1h', progress=False)
    if isinstance(gold_1h.columns, pd.MultiIndex):
        gold_1h.columns = gold_1h.columns.get_level_values(0)

    if len(gold_1h) > 50:
        print(f"Got {len(gold_1h)} hourly bars")
        gold_1h['Range_Pct'] = (gold_1h['High'] - gold_1h['Low']) / gold_1h['Close'] * 100
        gold_1h['Hour'] = gold_1h.index.hour

        print(f"\n{'Hour (UTC)':>10} | {'Avg Range%':>10} | {'n':>5}")
        print(f"{'-'*10}-+-{'-'*10}-+-{'-'*5}")

        for h in sorted(gold_1h['Hour'].unique()):
            subset = gold_1h[gold_1h['Hour'] == h]
            avg_range = subset['Range_Pct'].mean()
            print(f"{h:>10} | {avg_range:>9.3f}% | {len(subset):>5}")

        # Test: London hours (7-10) vs overnight (20-6)
        london = gold_1h[gold_1h['Hour'].between(7, 10)]
        overnight = gold_1h[(gold_1h['Hour'] >= 20) | (gold_1h['Hour'] <= 6)]

        if len(london) > 10 and len(overnight) > 10:
            t_stat, p_val = stats.mannwhitneyu(
                london['Range_Pct'].values,
                overnight['Range_Pct'].values,
                alternative='greater'
            )
            print(f"\nLondon (7-10) vs Overnight (20-6) volatility:")
            print(f"  London avg range: {london['Range_Pct'].mean():.3f}%")
            print(f"  Overnight avg range: {overnight['Range_Pct'].mean():.3f}%")
            print(f"  Mann-Whitney U p-value (London > Overnight): {p_val:.4f}")

        # Chart hourly volatility
        fig2, ax = plt.subplots(figsize=(12, 5))
        hourly_range = gold_1h.groupby('Hour')['Range_Pct'].mean()
        colors = ['#2196F3' if 7 <= h <= 10 else '#FF9800' if 13 <= h <= 15 else '#9E9E9E'
                  for h in hourly_range.index]
        ax.bar(hourly_range.index, hourly_range.values, color=colors)
        ax.set_title('Gold Hourly Volatility (Avg Range %) — Blue=London, Orange=NY')
        ax.set_xlabel('Hour (UTC)')
        ax.set_ylabel('Avg Range %')
        hourly_outpath = OUTPUT_DIR / 'session9_gold_hourly_vol.png'
        plt.savefig(hourly_outpath, dpi=150, bbox_inches='tight')
        print(f"Chart saved: {hourly_outpath}")
    else:
        print("Hourly data insufficient")
except Exception as e:
    print(f"Hourly data failed: {e}")

print("\n" + "=" * 80)
print("TASK 3 COMPLETE")
print("=" * 80)
