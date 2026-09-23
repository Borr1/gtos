"""
Test Finding F18: New Week Opening Gap (NWOG) alignment as confluence.
NWOG = gap between Friday close and Monday open.
Claim: OB retests near NWOG levels have higher continuation.

We test on XAUUSD H1 data: compute weekly NWOG, then check if
candles near NWOG show different behavior (higher rejection rate).

Decision gate:
  - If reaction rate near NWOG > 60% vs < 50% away → CONFIRMED
  - If no significant difference → REJECTED
  - Need at least 30 events per group
"""
import pandas as pd
import numpy as np
from scipy import stats

# Load H1 data (larger sample)
df = pd.read_csv('data/historical/XAUUSD_H1.csv', parse_dates=['time'])
print(f"H1 candles: {len(df)}")

# Add day of week
df['dow'] = df['time'].dt.dayofweek  # 0=Mon, 4=Fri

# Compute NWOG: Friday last close vs Monday first open
# Group by actual calendar week (year-week to avoid cross-year issues)
df['year_week'] = df['time'].dt.strftime('%G-%V')

nwogs = []
for yw in sorted(df['year_week'].unique()):
    week_data = df[df['year_week'] == yw]
    fri_data = week_data[week_data['dow'] == 4]
    mon_data = week_data[week_data['dow'] == 0]

    if len(fri_data) == 0 or len(mon_data) == 0:
        continue

    fri_close = fri_data.iloc[-1]['close']
    mon_open = mon_data.iloc[0]['open']
    gap = mon_open - fri_close
    gap_pct = abs(gap) / fri_close * 100
    nwog_mid = (fri_close + mon_open) / 2

    nwogs.append({
        'year_week': yw,
        'fri_close': fri_close,
        'mon_open': mon_open,
        'gap': gap,
        'gap_pct': gap_pct,
        'nwog_high': max(fri_close, mon_open),
        'nwog_low': min(fri_close, mon_open),
        'nwog_mid': nwog_mid,
        'mon_date': mon_data.iloc[0]['time']
    })

print(f"NWOGs computed: {len(nwogs)}")

if nwogs:
    gaps = [n['gap_pct'] for n in nwogs]
    print(f"Avg gap size: {np.mean(gaps):.3f}%")
    print(f"Median gap: {np.median(gaps):.3f}%")
    print(f"Gaps > 0.1%: {sum(1 for g in gaps if g > 0.1)}")

    # For each week, check if price retests the NWOG zone
    # and whether it reacts (reverses) or breaks through
    reactions = 0
    breaks = 0
    total_tests = 0

    for nwog in nwogs:
        week_candles = df[df['year_week'] == nwog['year_week']]
        # Skip Monday (gap already known), look at Tue-Fri
        rest_of_week = week_candles[week_candles['dow'] > 0]

        nwog_high = nwog['nwog_high']
        nwog_low = nwog['nwog_low']

        # Check if price touches NWOG zone
        for _, candle in rest_of_week.iterrows():
            if candle['low'] <= nwog_high and candle['high'] >= nwog_low:
                total_tests += 1
                # Reaction = next candle moves away from NWOG
                idx = df.index[df['time'] == candle['time']]
                if len(idx) > 0 and idx[0] + 1 < len(df):
                    next_c = df.iloc[idx[0] + 1]
                    # If price moved away from NWOG midpoint
                    dist_before = abs(candle['close'] - nwog['nwog_mid'])
                    dist_after = abs(next_c['close'] - nwog['nwog_mid'])
                    if dist_after > dist_before:
                        reactions += 1
                    else:
                        breaks += 1
                break  # Only count first touch per week

    print(f"\n{'='*60}")
    print(f"NWOG ZONE REACTION TEST")
    print(f"{'='*60}")
    print(f"Weeks with NWOG touch: {total_tests}")
    print(f"Reactions (price bounced): {reactions} ({reactions/max(total_tests,1)*100:.1f}%)")
    print(f"Breaks (price continued): {breaks} ({breaks/max(total_tests,1)*100:.1f}%)")

    if total_tests >= 30:
        # Binomial test: is reaction rate > 50%?
        p_val = stats.binomtest(reactions, total_tests, 0.5, alternative='greater').pvalue
        print(f"Binomial test (H0: reaction rate = 50%): p={p_val:.4f}")
        if p_val < 0.05 and reactions/total_tests > 0.6:
            print("*** CONFIRMED: NWOG zones show significant reaction tendency ***")
        elif p_val > 0.10:
            print("*** REJECTED: No significant NWOG reaction effect ***")
        else:
            print("*** INCONCLUSIVE: Weak signal, needs more data ***")
    else:
        print(f"*** INSUFFICIENT DATA: Only {total_tests} events (need 30+) ***")
else:
    print("*** NO NWOG DATA COMPUTED ***")
