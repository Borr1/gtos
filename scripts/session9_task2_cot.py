#!/usr/bin/env python3
"""
Session 9 — Task 2: COT Data Analysis for Gold
Uses CFTC combined futures report + historical archives.
"""
import urllib.request
from pathlib import Path
import pandas as pd
import numpy as np
import io
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_29/generated/session9")

print("=" * 80)
print("TASK 2: COT DATA ANALYSIS FOR GOLD (COMEX, Code 088691)")
print("=" * 80)

# Column names for combined report (deacom.txt format)
# Based on CFTC documentation
combined_cols = [
    'Market_and_Exchange_Names', 'As_of_Date_In_Form_YYMMDD', 'Report_Date_as_YYYY-MM-DD',
    'CFTC_Contract_Market_Code', 'CFTC_Market_Code', 'CFTC_Region_Code', 'CFTC_Commodity_Code',
    'Open_Interest_All', 'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All',
    'NonComm_Positions_Spread_All', 'Comm_Positions_Long_All', 'Comm_Positions_Short_All',
    'Tot_Rept_Positions_Long_All', 'Tot_Rept_Positions_Short_All',
    'NonRept_Positions_Long_All', 'NonRept_Positions_Short_All',
    # Futures-only columns follow...
    'Open_Interest_FO', 'NonComm_Positions_Long_FO', 'NonComm_Positions_Short_FO',
    'NonComm_Positions_Spread_FO', 'Comm_Positions_Long_FO', 'Comm_Positions_Short_FO',
    'Tot_Rept_Positions_Long_FO', 'Tot_Rept_Positions_Short_FO',
    'NonRept_Positions_Long_FO', 'NonRept_Positions_Short_FO',
    'Change_OI_All', 'Change_NonComm_Long_All', 'Change_NonComm_Short_All',
    'Change_NonComm_Spread_All', 'Change_Comm_Long_All', 'Change_Comm_Short_All',
]

def download_url(url, timeout=20):
    """Download a URL with error handling."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh)'})
    response = urllib.request.urlopen(req, timeout=timeout)
    return response.read()

def parse_cot_text(text, is_current=True):
    """Parse COT text file into gold records."""
    lines = text.strip().split('\n')
    records = []

    for line in lines:
        if '088691' not in line:
            continue

        fields = line.split(',')
        if len(fields) < 20:
            continue

        # Clean fields
        fields = [f.strip().strip('"') for f in fields]

        try:
            record = {
                'name': fields[0],
                'date': pd.to_datetime(fields[2]),
                'oi': int(fields[7].strip()),
                'noncomm_long': int(fields[8].strip()),
                'noncomm_short': int(fields[9].strip()),
                'noncomm_spread': int(fields[10].strip()),
                'comm_long': int(fields[11].strip()),
                'comm_short': int(fields[12].strip()),
            }
            record['noncomm_net'] = record['noncomm_long'] - record['noncomm_short']
            record['comm_net'] = record['comm_long'] - record['comm_short']
            records.append(record)
        except (ValueError, IndexError) as e:
            continue

    return records

# Download current year
print("\nDownloading current year COT data...")
all_records = []

try:
    data = download_url('https://www.cftc.gov/dea/newcot/deacom.txt')
    text = data.decode('latin-1')
    records = parse_cot_text(text)
    all_records.extend(records)
    print(f"  Current year: {len(records)} gold records")
except Exception as e:
    print(f"  Current year failed: {e}")

# Download historical years
for year in [2025, 2024, 2023, 2022]:
    url = f'https://www.cftc.gov/files/dea/history/deacom{year}.zip'
    print(f"  Downloading {year}...")
    try:
        data = download_url(url, timeout=30)
        zf = zipfile.ZipFile(io.BytesIO(data))
        for fname in zf.namelist():
            if fname.endswith('.txt'):
                text = zf.read(fname).decode('latin-1')
                records = parse_cot_text(text)
                all_records.extend(records)
                print(f"    {year}: {len(records)} gold records")
    except Exception as e:
        print(f"    {year} failed: {e}")

if not all_records:
    print("NO DATA OBTAINED. Task 2 failed.")
    exit(1)

# Build DataFrame
df = pd.DataFrame(all_records)
df = df.drop_duplicates(subset='date').sort_values('date').reset_index(drop=True)
print(f"\nTotal: {len(df)} weekly gold COT records from {df['date'].min().date()} to {df['date'].max().date()}")

# =============================================================================
print("\n" + "=" * 60)
print("POSITIONING PERCENTILES")
print("=" * 60)

for col, label in [('comm_net', 'Commercial Net'), ('noncomm_net', 'Non-Commercial (Managed Money) Net'), ('oi', 'Open Interest')]:
    vals = df[col]
    current = vals.iloc[-1]
    pctile = stats.percentileofscore(vals, current)
    print(f"\n{label}:")
    print(f"  Current: {current:,.0f}")
    print(f"  Percentile: {pctile:.0f}th")
    print(f"  Range: [{vals.min():,.0f}, {vals.max():,.0f}]")
    print(f"  Mean: {vals.mean():,.0f}")
    print(f"  Extremes (>90th): >{np.percentile(vals, 90):,.0f}")
    print(f"  Extremes (<10th): <{np.percentile(vals, 10):,.0f}")

# =============================================================================
print("\n" + "=" * 60)
print("CORRELATION: COT CHANGES vs GOLD PRICE CHANGES")
print("=" * 60)

# We need gold price data aligned with COT dates
import yfinance as yf
gold_price = yf.download('GC=F', start=df['date'].min(), end=df['date'].max() + pd.Timedelta(days=35), progress=False)
if isinstance(gold_price.columns, pd.MultiIndex):
    gold_price.columns = gold_price.columns.get_level_values(0)

# For each COT date, get gold price change over next 1 week and 4 weeks
df['gold_1w_chg'] = np.nan
df['gold_4w_chg'] = np.nan

for i, row in df.iterrows():
    cot_date = row['date']
    # Find gold price on COT date (or closest after)
    future_prices = gold_price[gold_price.index >= cot_date]
    if len(future_prices) < 2:
        continue
    p0 = future_prices['Close'].iloc[0]

    # 1 week later
    week_later = future_prices[future_prices.index >= cot_date + pd.Timedelta(days=5)]
    if len(week_later) > 0:
        df.at[i, 'gold_1w_chg'] = (week_later['Close'].iloc[0] / p0 - 1) * 100

    # 4 weeks later
    month_later = future_prices[future_prices.index >= cot_date + pd.Timedelta(days=25)]
    if len(month_later) > 0:
        df.at[i, 'gold_4w_chg'] = (month_later['Close'].iloc[0] / p0 - 1) * 100

# Weekly changes in positioning
df['comm_net_chg'] = df['comm_net'].diff()
df['noncomm_net_chg'] = df['noncomm_net'].diff()

valid = df.dropna(subset=['gold_1w_chg', 'comm_net_chg'])

for pos_col, label in [('comm_net_chg', 'Commercial Net Change'), ('noncomm_net_chg', 'Non-Commercial Net Change'),
                        ('comm_net', 'Commercial Net Level'), ('noncomm_net', 'Non-Commercial Net Level')]:
    for price_col, period in [('gold_1w_chg', '1-week'), ('gold_4w_chg', '4-week')]:
        v = valid.dropna(subset=[pos_col, price_col])
        if len(v) < 10:
            continue
        corr, p = stats.spearmanr(v[pos_col], v[price_col])
        sig = '*' if p < 0.05 else ''
        print(f"  {label} vs {period} gold: r={corr:+.3f} (p={p:.3f}) {sig}")

# =============================================================================
print("\n" + "=" * 60)
print("EXTREME POSITIONING ANALYSIS")
print("=" * 60)

for col, label in [('comm_net', 'Commercial'), ('noncomm_net', 'Non-Commercial')]:
    p90 = np.percentile(df[col], 90)
    p10 = np.percentile(df[col], 10)

    extreme_high = df[df[col] >= p90].dropna(subset=['gold_4w_chg'])
    extreme_low = df[df[col] <= p10].dropna(subset=['gold_4w_chg'])
    middle = df[(df[col] > p10) & (df[col] < p90)].dropna(subset=['gold_4w_chg'])

    print(f"\n{label} Net Positioning:")
    print(f"  >90th percentile (>{p90:,.0f}): n={len(extreme_high)}, avg 4w gold chg: {extreme_high['gold_4w_chg'].mean():+.2f}%")
    print(f"  <10th percentile (<{p10:,.0f}): n={len(extreme_low)}, avg 4w gold chg: {extreme_low['gold_4w_chg'].mean():+.2f}%")
    print(f"  Middle (10-90th): n={len(middle)}, avg 4w gold chg: {middle['gold_4w_chg'].mean():+.2f}%")

    # Mann-Whitney test: extreme vs middle
    if len(extreme_high) >= 5 and len(middle) >= 5:
        u, p_val = stats.mannwhitneyu(extreme_high['gold_4w_chg'], middle['gold_4w_chg'])
        print(f"  High extreme vs middle: U-test p={p_val:.3f}")
    if len(extreme_low) >= 5 and len(middle) >= 5:
        u, p_val = stats.mannwhitneyu(extreme_low['gold_4w_chg'], middle['gold_4w_chg'])
        print(f"  Low extreme vs middle: U-test p={p_val:.3f}")

# =============================================================================
# Charts
fig, axes = plt.subplots(3, 1, figsize=(14, 14))

# Get gold price for overlay
gold_weekly = gold_price['Close'].resample('W').last()

# 1. Commercial net + gold price
ax1 = axes[0]
ax2 = ax1.twinx()
ax1.bar(df['date'], df['comm_net'], width=5, alpha=0.6, color='blue', label='Commercial Net')
gold_aligned = gold_weekly[gold_weekly.index >= df['date'].min()]
ax2.plot(gold_aligned.index, gold_aligned.values, 'gold', linewidth=2, label='Gold Price')
ax1.set_ylabel('Commercial Net Contracts', color='blue')
ax2.set_ylabel('Gold Price', color='goldenrod')
ax1.set_title('Commercial Net Positioning vs Gold Price')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# 2. Non-commercial net + gold price
ax3 = axes[1]
ax4 = ax3.twinx()
ax3.bar(df['date'], df['noncomm_net'], width=5, alpha=0.6, color='green', label='Non-Commercial Net')
ax4.plot(gold_aligned.index, gold_aligned.values, 'gold', linewidth=2, label='Gold Price')
ax3.set_ylabel('Non-Comm Net Contracts', color='green')
ax4.set_ylabel('Gold Price', color='goldenrod')
ax3.set_title('Non-Commercial Net Positioning vs Gold Price')
lines3, labels3 = ax3.get_legend_handles_labels()
lines4, labels4 = ax4.get_legend_handles_labels()
ax3.legend(lines3 + lines4, labels3 + labels4, loc='upper left')

# 3. Percentile bands
comm_pctile = df['comm_net'].rank(pct=True) * 100
noncomm_pctile = df['noncomm_net'].rank(pct=True) * 100
axes[2].plot(df['date'], comm_pctile, 'b-', label='Commercial Net Percentile', alpha=0.7)
axes[2].plot(df['date'], noncomm_pctile, 'g-', label='Non-Commercial Net Percentile', alpha=0.7)
axes[2].axhline(y=90, color='red', linestyle='--', alpha=0.5, label='90th / 10th')
axes[2].axhline(y=10, color='red', linestyle='--', alpha=0.5)
axes[2].set_title('Positioning Percentiles Over Time')
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
