#!/usr/bin/env python3
"""
Session 9 — Task 2: COT Data Analysis for Gold (Disaggregated Report)
"""
import urllib.request, zipfile, io
from pathlib import Path
import pandas as pd, numpy as np
from scipy import stats
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_29/generated/session9")

print("=" * 80)
print("TASK 2: COT GOLD ANALYSIS (Disaggregated, 2022-2025)")
print("=" * 80)

def download_url(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=timeout).read()

all_dfs = []
for year in [2025, 2024, 2023, 2022]:
    url = f'https://www.cftc.gov/files/dea/history/com_disagg_txt_{year}.zip'
    try:
        data = download_url(url)
        zf = zipfile.ZipFile(io.BytesIO(data))
        for fname in zf.namelist():
            if fname.endswith('.txt'):
                text = zf.read(fname).decode('latin-1')
                lines = text.strip().split('\n')
                gold_lines = [lines[0]] + [l for l in lines[1:] if '088691' in l]
                if len(gold_lines) > 1:
                    df_yr = pd.read_csv(io.StringIO('\n'.join(gold_lines)))
                    all_dfs.append(df_yr)
                    print(f'{year}: {len(df_yr)} records')
    except Exception as e:
        print(f'{year} failed: {e}')

df = pd.concat(all_dfs, ignore_index=True)
df['date'] = pd.to_datetime(df['Report_Date_as_YYYY-MM-DD'])
df = df.sort_values('date').reset_index(drop=True)

# Compute net positions
df['pm_net'] = df['Prod_Merc_Positions_Long_All'] - df['Prod_Merc_Positions_Short_All']
df['mm_net'] = df['M_Money_Positions_Long_All'] - df['M_Money_Positions_Short_All']
df['swap_net'] = df['Swap_Positions_Long_All'] - df['Swap__Positions_Short_All']
df['oi'] = df['Open_Interest_All']

print(f"\n{len(df)} weekly records: {df['date'].min().date()} to {df['date'].max().date()}")

# =============================================================================
print("\n" + "=" * 60)
print("CURRENT POSITIONING PERCENTILES")
print("=" * 60)

for col, label in [('pm_net', 'Producer/Merchant Net (Commercials)'),
                    ('mm_net', 'Managed Money Net'),
                    ('swap_net', 'Swap Dealer Net'),
                    ('oi', 'Open Interest')]:
    vals = df[col]
    current = vals.iloc[-1]
    pctile = stats.percentileofscore(vals, current)
    print(f"\n{label}:")
    print(f"  Current ({df['date'].iloc[-1].date()}): {current:,.0f}")
    print(f"  Percentile (4yr): {pctile:.0f}th")
    print(f"  Range: [{vals.min():,.0f}, {vals.max():,.0f}]")

# =============================================================================
# Get gold prices for forward return correlation
print("\n" + "=" * 60)
print("COT vs FORWARD GOLD RETURNS")
print("=" * 60)

gold_price = yf.download('GC=F', start=df['date'].min() - pd.Timedelta(days=5),
                          end=df['date'].max() + pd.Timedelta(days=35), progress=False)
if isinstance(gold_price.columns, pd.MultiIndex):
    gold_price.columns = gold_price.columns.get_level_values(0)

for i in range(len(df)):
    cot_date = df.at[i, 'date']
    future = gold_price[gold_price.index >= cot_date]
    if len(future) < 2:
        continue
    p0 = future['Close'].iloc[0]

    w1 = future[future.index >= cot_date + pd.Timedelta(days=5)]
    w4 = future[future.index >= cot_date + pd.Timedelta(days=25)]

    df.at[i, 'gold_1w'] = (w1['Close'].iloc[0] / p0 - 1) * 100 if len(w1) > 0 else np.nan
    df.at[i, 'gold_4w'] = (w4['Close'].iloc[0] / p0 - 1) * 100 if len(w4) > 0 else np.nan

# Weekly changes
df['mm_net_chg'] = df['mm_net'].diff()
df['pm_net_chg'] = df['pm_net'].diff()

valid = df.dropna(subset=['gold_1w', 'mm_net_chg'])
print(f"\n{'Position Metric':<30} | {'vs 1w gold':>12} | {'p':>7} | {'vs 4w gold':>12} | {'p':>7}")
print(f"{'-'*30}-+-{'-'*12}-+-{'-'*7}-+-{'-'*12}-+-{'-'*7}")

for col, label in [('mm_net', 'Managed Money Net Level'),
                    ('mm_net_chg', 'Managed Money Net Change'),
                    ('pm_net', 'Producer/Merchant Net Level'),
                    ('pm_net_chg', 'Producer/Merchant Net Change')]:
    for price_col, period in [('gold_1w', '1w'), ('gold_4w', '4w')]:
        v = valid.dropna(subset=[col, price_col])
        if len(v) < 10:
            continue
        corr, p = stats.spearmanr(v[col], v[price_col])
        sig = '*' if p < 0.05 else ' '
        if period == '1w':
            line = f"{label:<30} | r={corr:+.3f} {sig}  | {p:.3f} |"
        else:
            print(f"{line} r={corr:+.3f} {sig}  | {p:.3f}")

# =============================================================================
print("\n" + "=" * 60)
print("EXTREME POSITIONING → FORWARD RETURNS")
print("=" * 60)

for col, label in [('mm_net', 'Managed Money'), ('pm_net', 'Producer/Merchant')]:
    p90 = np.percentile(df[col], 90)
    p10 = np.percentile(df[col], 10)

    high = df[df[col] >= p90].dropna(subset=['gold_4w'])
    low = df[df[col] <= p10].dropna(subset=['gold_4w'])
    mid = df[(df[col] > p10) & (df[col] < p90)].dropna(subset=['gold_4w'])

    print(f"\n{label}:")
    print(f"  >90th (>{p90:,.0f}): n={len(high)}, avg 4w: {high['gold_4w'].mean():+.2f}%, median: {high['gold_4w'].median():+.2f}%")
    print(f"  <10th (<{p10:,.0f}): n={len(low)}, avg 4w: {low['gold_4w'].mean():+.2f}%, median: {low['gold_4w'].median():+.2f}%")
    print(f"  Middle: n={len(mid)}, avg 4w: {mid['gold_4w'].mean():+.2f}%")

    if len(high) >= 5 and len(mid) >= 5:
        u, p_val = stats.mannwhitneyu(high['gold_4w'], mid['gold_4w'], alternative='two-sided')
        print(f"  High vs Middle: p={p_val:.3f} {'*' if p_val < 0.05 else ''}")
    if len(low) >= 5 and len(mid) >= 5:
        u, p_val = stats.mannwhitneyu(low['gold_4w'], mid['gold_4w'], alternative='two-sided')
        print(f"  Low vs Middle: p={p_val:.3f} {'*' if p_val < 0.05 else ''}")

# =============================================================================
# Charts
fig, axes = plt.subplots(3, 1, figsize=(14, 14))

gold_weekly = gold_price['Close'].resample('W').last()
gold_aligned = gold_weekly[(gold_weekly.index >= df['date'].min()) & (gold_weekly.index <= df['date'].max())]

# 1. Managed Money Net + Gold
ax1 = axes[0]
ax2 = ax1.twinx()
ax1.fill_between(df['date'], df['mm_net'], alpha=0.5, color='green', label='Managed Money Net')
ax2.plot(gold_aligned.index, gold_aligned.values, 'gold', linewidth=2, label='Gold')
ax1.set_ylabel('Managed Money Net', color='green')
ax2.set_ylabel('Gold Price', color='goldenrod')
ax1.set_title('Managed Money Net Positioning vs Gold (2022-2025)')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, loc='upper left')

# 2. Producer/Merchant Net + Gold
ax3 = axes[1]
ax4 = ax3.twinx()
ax3.fill_between(df['date'], df['pm_net'], alpha=0.5, color='blue', label='Prod/Merch Net')
ax4.plot(gold_aligned.index, gold_aligned.values, 'gold', linewidth=2, label='Gold')
ax3.set_ylabel('Producer/Merchant Net', color='blue')
ax4.set_ylabel('Gold Price', color='goldenrod')
ax3.set_title('Producer/Merchant (Commercial) Net vs Gold')
lines3, labels3 = ax3.get_legend_handles_labels()
lines4, labels4 = ax4.get_legend_handles_labels()
ax3.legend(lines3+lines4, labels3+labels4, loc='upper left')

# 3. Percentiles
mm_pctile = df['mm_net'].rank(pct=True) * 100
pm_pctile = df['pm_net'].rank(pct=True) * 100
axes[2].plot(df['date'], mm_pctile, 'g-', label='Managed Money Pctile', alpha=0.8)
axes[2].plot(df['date'], pm_pctile, 'b-', label='Prod/Merch Pctile', alpha=0.8)
axes[2].axhline(90, color='red', linestyle='--', alpha=0.5)
axes[2].axhline(10, color='red', linestyle='--', alpha=0.5)
axes[2].set_title('Positioning Percentiles (4-year)')
axes[2].set_ylabel('Percentile')
axes[2].legend()
axes[2].set_ylim(0, 100)

plt.tight_layout()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
outpath = OUTPUT_DIR / 'session9_cot_analysis.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight')
print(f"\nChart saved: {outpath}")

print("\n" + "=" * 80)
print("TASK 2 COMPLETE")
print("=" * 80)
