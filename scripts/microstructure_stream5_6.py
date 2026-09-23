#!/usr/bin/env python3
"""
Microstructure Analysis: Streams 5 (Session Dynamics) & 6 (Cross-Instrument Dynamics)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

BASE = Path("/Users/borr/Documents/trading/gold-agent")

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data...")
xau_m15 = pd.read_csv(BASE / "data/historical/XAUUSD_M15.csv", parse_dates=["time"])
gbp_m15 = pd.read_csv(BASE / "data/historical/GBPUSD_M15.csv", parse_dates=["time"])
xau_h1 = pd.read_csv(BASE / "data/historical/XAUUSD_H1.csv", parse_dates=["time"])
gbp_h1 = pd.read_csv(BASE / "data/historical/GBPUSD_H1.csv", parse_dates=["time"])

with open(BASE / "knowledge_base_backtest/analysis/displacement_database_20260403_0030.json") as f:
    displacements = json.load(f)

print(f"XAU M15: {len(xau_m15)} rows, date range: {xau_m15['time'].min()} to {xau_m15['time'].max()}")
print(f"GBP M15: {len(gbp_m15)} rows, date range: {gbp_m15['time'].min()} to {gbp_m15['time'].max()}")
print(f"Displacements: {len(displacements)} entries")

# Add helper columns
for df in [xau_m15, gbp_m15]:
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour
    df['body'] = abs(df['close'] - df['open'])
    df['range_hl'] = df['high'] - df['low']

for df in [xau_h1, gbp_h1]:
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour

# ═══════════════════════════════════════════════════════════════════════════════
# STREAM 5: SESSION DYNAMICS
# ═══════════════════════════════════════════════════════════════════════════════

stream5 = {}

# ── 5A: First-Hour Direction Persistence ──────────────────────────────────────
print("\n=== 5A: First-Hour Direction Persistence ===")

def first_hour_persistence(m15_df, label):
    """
    London first hour: 07:00-08:00 (candles at 07:00, 07:15, 07:30, 07:45)
    Rest of London: 08:00-12:00
    NY first hour: 13:00-14:00
    Rest of NY: 14:00-17:00
    """
    results = {}

    for session_name, first_start, first_end, rest_end in [
        ("london", 7, 8, 12),
        ("ny", 13, 14, 17)
    ]:
        persist_count = 0
        total = 0
        bullish_persist = 0
        bearish_persist = 0
        bullish_total = 0
        bearish_total = 0

        for date, day_data in m15_df.groupby('date'):
            # First hour candles
            first_hour = day_data[(day_data['hour'] >= first_start) & (day_data['hour'] < first_end)]
            rest = day_data[(day_data['hour'] >= first_end) & (day_data['hour'] < rest_end)]

            if len(first_hour) < 2 or len(rest) < 2:
                continue

            first_open = first_hour.iloc[0]['open']
            first_close = first_hour.iloc[-1]['close']
            rest_close = rest.iloc[-1]['close']

            first_dir = "bullish" if first_close > first_open else "bearish"
            total += 1

            if first_dir == "bullish":
                bullish_total += 1
                if rest_close > first_close:
                    persist_count += 1
                    bullish_persist += 1
            else:
                bearish_total += 1
                if rest_close < first_close:
                    persist_count += 1
                    bearish_persist += 1

        rate = persist_count / total if total > 0 else 0
        results[session_name] = {
            "total_days": total,
            "persistence_rate": round(rate, 4),
            "bullish_first_hour_count": bullish_total,
            "bullish_persistence_rate": round(bullish_persist / bullish_total, 4) if bullish_total > 0 else None,
            "bearish_first_hour_count": bearish_total,
            "bearish_persistence_rate": round(bearish_persist / bearish_total, 4) if bearish_total > 0 else None,
        }
        print(f"  {label} {session_name}: persistence={rate:.1%} (n={total}), bull={bullish_persist}/{bullish_total}, bear={bearish_persist}/{bearish_total}")

    return results

stream5["5A_first_hour_persistence"] = {
    "XAUUSD": first_hour_persistence(xau_m15, "XAUUSD"),
    "GBPUSD": first_hour_persistence(gbp_m15, "GBPUSD"),
}

# ── 5B: Asian Session as Predictor ────────────────────────────────────────────
print("\n=== 5B: Asian Session as Predictor ===")

def asian_analysis(m15_df, label):
    """
    Asian session: 00:00-07:00 UTC
    London open: 07:00-12:00
    """
    asian_ranges = []
    asian_dirs = []
    london_dirs = []
    first_touch_predicts = []

    for date, day_data in m15_df.groupby('date'):
        asian = day_data[(day_data['hour'] >= 0) & (day_data['hour'] < 7)]
        london = day_data[(day_data['hour'] >= 7) & (day_data['hour'] < 12)]

        if len(asian) < 4 or len(london) < 4:
            continue

        a_high = asian['high'].max()
        a_low = asian['low'].min()
        a_range = a_high - a_low
        asian_ranges.append(a_range)

        # Asian direction: close of last vs open of first
        a_dir = 1 if asian.iloc[-1]['close'] > asian.iloc[0]['open'] else -1
        asian_dirs.append(a_dir)

        # London direction
        l_dir = 1 if london.iloc[-1]['close'] > london.iloc[0]['open'] else -1
        london_dirs.append(l_dir)

        # First touch during Asian: which is touched first, Asian H or Asian L?
        # Track candle-by-candle from start of Asian
        first_touch = None
        running_high = asian.iloc[0]['high']
        running_low = asian.iloc[0]['low']

        for i in range(1, len(asian)):
            candle = asian.iloc[i]
            if candle['high'] >= running_high and first_touch is None:
                # New high touched first
                if candle['low'] <= running_low:
                    pass  # Both touched same candle, skip
                else:
                    first_touch = "high"
                    break
            if candle['low'] <= running_low and first_touch is None:
                if candle['high'] >= running_high:
                    pass
                else:
                    first_touch = "low"
                    break
            running_high = max(running_high, candle['high'])
            running_low = min(running_low, candle['low'])

        if first_touch is not None:
            # Does London sweep the OPPOSITE side?
            if first_touch == "high":
                # First touch was high during Asian build -> does London sweep the low?
                london_swept_low = london['low'].min() < a_low
                first_touch_predicts.append({
                    "first_touch": first_touch,
                    "london_sweeps_opposite": london_swept_low,
                    "london_sweeps_same": london['high'].max() > a_high,
                })
            else:
                london_swept_high = london['high'].max() > a_high
                first_touch_predicts.append({
                    "first_touch": first_touch,
                    "london_sweeps_opposite": london_swept_high,
                    "london_sweeps_same": london['low'].min() < a_low,
                })

    ar = np.array(asian_ranges)
    percentiles = {
        "p10": round(float(np.percentile(ar, 10)), 5),
        "p25": round(float(np.percentile(ar, 25)), 5),
        "p50": round(float(np.percentile(ar, 50)), 5),
        "p75": round(float(np.percentile(ar, 75)), 5),
        "p90": round(float(np.percentile(ar, 90)), 5),
    }

    # Correlation: Asian dir vs London dir
    corr = np.corrcoef(asian_dirs, london_dirs)[0, 1]
    same_dir = sum(1 for a, l in zip(asian_dirs, london_dirs) if a == l)

    # First touch analysis
    ft_high = [x for x in first_touch_predicts if x["first_touch"] == "high"]
    ft_low = [x for x in first_touch_predicts if x["first_touch"] == "low"]

    ft_high_opp = sum(1 for x in ft_high if x["london_sweeps_opposite"]) / len(ft_high) if ft_high else 0
    ft_low_opp = sum(1 for x in ft_low if x["london_sweeps_opposite"]) / len(ft_low) if ft_low else 0
    ft_high_same = sum(1 for x in ft_high if x["london_sweeps_same"]) / len(ft_high) if ft_high else 0
    ft_low_same = sum(1 for x in ft_low if x["london_sweeps_same"]) / len(ft_low) if ft_low else 0

    result = {
        "asian_range_percentiles": percentiles,
        "sample_size": len(asian_ranges),
        "asian_london_direction_correlation": round(float(corr), 4),
        "asian_london_same_direction_pct": round(same_dir / len(asian_dirs), 4) if asian_dirs else None,
        "first_touch_analysis": {
            "first_touch_high_count": len(ft_high),
            "first_touch_low_count": len(ft_low),
            "high_first_london_sweeps_opposite_low": round(ft_high_opp, 4),
            "high_first_london_sweeps_same_high": round(ft_high_same, 4),
            "low_first_london_sweeps_opposite_high": round(ft_low_opp, 4),
            "low_first_london_sweeps_same_low": round(ft_low_same, 4),
        }
    }

    print(f"  {label} Asian range P50: {percentiles['p50']}, correlation: {corr:.4f}, same_dir: {same_dir}/{len(asian_dirs)}")
    print(f"  First touch high: {len(ft_high)}, opp sweep: {ft_high_opp:.1%}; low: {len(ft_low)}, opp sweep: {ft_low_opp:.1%}")

    return result

stream5["5B_asian_predictor"] = {
    "XAUUSD": asian_analysis(xau_m15, "XAUUSD"),
    "GBPUSD": asian_analysis(gbp_m15, "GBPUSD"),
}

# ── 5C: London-NY Relationship ────────────────────────────────────────────────
print("\n=== 5C: London-NY Relationship ===")

def london_ny_relationship(m15_df, label):
    same = 0
    opposite = 0
    total = 0
    london_bull_ny_bull = 0
    london_bull_ny_bear = 0
    london_bear_ny_bull = 0
    london_bear_ny_bear = 0
    london_bull_total = 0
    london_bear_total = 0

    for date, day_data in m15_df.groupby('date'):
        london = day_data[(day_data['hour'] >= 7) & (day_data['hour'] < 12)]
        ny = day_data[(day_data['hour'] >= 13) & (day_data['hour'] < 17)]

        if len(london) < 4 or len(ny) < 4:
            continue

        l_dir = 1 if london.iloc[-1]['close'] > london.iloc[0]['open'] else -1
        n_dir = 1 if ny.iloc[-1]['close'] > ny.iloc[0]['open'] else -1

        total += 1
        if l_dir == n_dir:
            same += 1
        else:
            opposite += 1

        if l_dir == 1:
            london_bull_total += 1
            if n_dir == 1:
                london_bull_ny_bull += 1
            else:
                london_bull_ny_bear += 1
        else:
            london_bear_total += 1
            if n_dir == 1:
                london_bear_ny_bull += 1
            else:
                london_bear_ny_bear += 1

    result = {
        "total_days": total,
        "same_direction_pct": round(same / total, 4) if total > 0 else None,
        "opposite_direction_pct": round(opposite / total, 4) if total > 0 else None,
        "london_bullish_ny_continuation": round(london_bull_ny_bull / london_bull_total, 4) if london_bull_total > 0 else None,
        "london_bullish_ny_reversal": round(london_bull_ny_bear / london_bull_total, 4) if london_bull_total > 0 else None,
        "london_bearish_ny_continuation": round(london_bear_ny_bear / london_bear_total, 4) if london_bear_total > 0 else None,
        "london_bearish_ny_reversal": round(london_bear_ny_bull / london_bear_total, 4) if london_bear_total > 0 else None,
        "london_bullish_days": london_bull_total,
        "london_bearish_days": london_bear_total,
    }

    print(f"  {label}: same={same/total:.1%}, opposite={opposite/total:.1%} (n={total})")
    print(f"    London bull -> NY bull: {london_bull_ny_bull}/{london_bull_total}, London bear -> NY bear: {london_bear_ny_bear}/{london_bear_total}")

    return result

stream5["5C_london_ny_relationship"] = {
    "XAUUSD": london_ny_relationship(xau_m15, "XAUUSD"),
    "GBPUSD": london_ny_relationship(gbp_m15, "GBPUSD"),
}

# ── 5D: Volatility Distribution by Hour ──────────────────────────────────────
print("\n=== 5D: Volatility Distribution by Hour ===")

def vol_by_hour(m15_df, label):
    hourly = {}
    for hour in range(24):
        h_data = m15_df[m15_df['hour'] == hour]
        if len(h_data) == 0:
            continue
        hourly[str(hour)] = {
            "avg_body": round(float(h_data['body'].mean()), 5),
            "avg_range": round(float(h_data['range_hl'].mean()), 5),
            "median_body": round(float(h_data['body'].median()), 5),
            "p90_body": round(float(h_data['body'].quantile(0.9)), 5),
            "sample_size": int(len(h_data)),
        }
    return hourly

xau_vol = vol_by_hour(xau_m15, "XAUUSD")
gbp_vol = vol_by_hour(gbp_m15, "GBPUSD")

# Displacement analysis by hour (XAUUSD only)
disp_df = pd.DataFrame(displacements)
disp_df['timestamp'] = pd.to_datetime(disp_df['timestamp'])
disp_df['hour'] = disp_df['timestamp'].dt.hour

disp_by_hour = {}
for hour in range(24):
    h_disp = disp_df[disp_df['hour'] == hour]
    if len(h_disp) == 0:
        disp_by_hour[str(hour)] = {"count": 0, "avg_cont_3h": None}
        continue
    disp_by_hour[str(hour)] = {
        "count": int(len(h_disp)),
        "avg_cont_3h": round(float(h_disp['cont_3h'].mean()), 4),
    }

# Print top hours
print("  XAUUSD top volatility hours (avg range):")
for h in sorted(xau_vol.keys(), key=lambda x: xau_vol[x]['avg_range'], reverse=True)[:5]:
    print(f"    Hour {h}: avg_range={xau_vol[h]['avg_range']}, avg_body={xau_vol[h]['avg_body']}")

print("  XAUUSD top displacement hours:")
for h in sorted(disp_by_hour.keys(), key=lambda x: disp_by_hour[x]['count'], reverse=True)[:5]:
    d = disp_by_hour[h]
    print(f"    Hour {h}: count={d['count']}, cont_3h={d['avg_cont_3h']}")

stream5["5D_volatility_by_hour"] = {
    "XAUUSD": {"m15_stats": xau_vol, "displacements": disp_by_hour},
    "GBPUSD": {"m15_stats": gbp_vol},
}


# ═══════════════════════════════════════════════════════════════════════════════
# STREAM 6: CROSS-INSTRUMENT DYNAMICS
# ═══════════════════════════════════════════════════════════════════════════════

stream6 = {}

# ── 6A: Correlation Analysis ─────────────────────────────────────────────────
print("\n=== 6A: Correlation Analysis ===")

# Build daily returns from M15 data
def daily_returns(m15_df):
    daily = m15_df.groupby('date').agg(
        open=('open', 'first'),
        close=('close', 'last'),
        high=('high', 'max'),
        low=('low', 'min'),
    ).reset_index()
    daily['return'] = (daily['close'] - daily['open']) / daily['open']
    daily['return_pct'] = daily['return'] * 100
    return daily

xau_daily = daily_returns(xau_m15)
gbp_daily = daily_returns(gbp_m15)

# Merge on common dates
merged = pd.merge(xau_daily, gbp_daily, on='date', suffixes=('_xau', '_gbp'))
print(f"  Common trading days: {len(merged)}")

# Overall correlation
overall_corr = np.corrcoef(merged['return_xau'], merged['return_gbp'])[0, 1]
print(f"  Daily return correlation: {overall_corr:.4f}")

# Rolling 20-day correlation
merged_sorted = merged.sort_values('date').reset_index(drop=True)
rolling_corrs = []
for i in range(19, len(merged_sorted)):
    window = merged_sorted.iloc[i-19:i+1]
    rc = np.corrcoef(window['return_xau'], window['return_gbp'])[0, 1]
    rolling_corrs.append(rc)

rc_arr = np.array(rolling_corrs)
print(f"  Rolling 20d corr: mean={rc_arr.mean():.4f}, std={rc_arr.std():.4f}, min={rc_arr.min():.4f}, max={rc_arr.max():.4f}")

# Intraday H1 direction alignment
xau_h1_c = xau_h1.copy()
gbp_h1_c = gbp_h1.copy()
xau_h1_c['dir'] = np.sign(xau_h1_c['close'] - xau_h1_c['open'])
gbp_h1_c['dir'] = np.sign(gbp_h1_c['close'] - gbp_h1_c['open'])

h1_merged = pd.merge(xau_h1_c[['time', 'dir']], gbp_h1_c[['time', 'dir']], on='time', suffixes=('_xau', '_gbp'))
# Exclude zero-body candles
h1_active = h1_merged[(h1_merged['dir_xau'] != 0) & (h1_merged['dir_gbp'] != 0)]
h1_same = (h1_active['dir_xau'] == h1_active['dir_gbp']).sum()

stream6["6A_correlation"] = {
    "common_trading_days": int(len(merged)),
    "daily_return_correlation": round(float(overall_corr), 4),
    "rolling_20d_correlation": {
        "mean": round(float(rc_arr.mean()), 4),
        "std": round(float(rc_arr.std()), 4),
        "min": round(float(rc_arr.min()), 4),
        "max": round(float(rc_arr.max()), 4),
        "p25": round(float(np.percentile(rc_arr, 25)), 4),
        "p75": round(float(np.percentile(rc_arr, 75)), 4),
    },
    "h1_direction_alignment": {
        "total_h1_candles_both_active": int(len(h1_active)),
        "same_direction_count": int(h1_same),
        "same_direction_pct": round(float(h1_same / len(h1_active)), 4) if len(h1_active) > 0 else None,
    },
}

print(f"  H1 alignment: {h1_same}/{len(h1_active)} = {h1_same/len(h1_active):.1%}")

# ── 6B: Divergence as Signal ─────────────────────────────────────────────────
print("\n=== 6B: Divergence as Signal ===")

merged_sorted = merged_sorted.reset_index(drop=True)

# Divergence days: opposite signs
div_days = merged_sorted[np.sign(merged_sorted['return_xau']) != np.sign(merged_sorted['return_gbp'])]
# Alignment days: same sign AND both > 0.5%
strong_align = merged_sorted[
    (np.sign(merged_sorted['return_xau']) == np.sign(merged_sorted['return_gbp'])) &
    (abs(merged_sorted['return_pct_xau']) > 0.5) &
    (abs(merged_sorted['return_pct_gbp']) > 0.5)
]

def next_day_outcomes(condition_df, all_df):
    """For each day in condition_df, get next day's returns"""
    dates = set(condition_df['date'].values)
    all_dates = list(all_df['date'].values)

    xau_next = []
    gbp_next = []

    for i, row in all_df.iterrows():
        if row['date'] in dates and i + 1 < len(all_df):
            next_row = all_df.iloc[i + 1]
            xau_next.append(next_row['return_pct_xau'])
            gbp_next.append(next_row['return_pct_gbp'])

    if not xau_next:
        return None

    return {
        "sample_size": len(xau_next),
        "xau_next_day_avg_return_pct": round(float(np.mean(xau_next)), 4),
        "xau_next_day_median_return_pct": round(float(np.median(xau_next)), 4),
        "xau_next_day_positive_pct": round(float(sum(1 for x in xau_next if x > 0) / len(xau_next)), 4),
        "gbp_next_day_avg_return_pct": round(float(np.mean(gbp_next)), 4),
        "gbp_next_day_median_return_pct": round(float(np.median(gbp_next)), 4),
        "gbp_next_day_positive_pct": round(float(sum(1 for x in gbp_next if x > 0) / len(gbp_next)), 4),
    }

div_outcomes = next_day_outcomes(div_days, merged_sorted)
align_outcomes = next_day_outcomes(strong_align, merged_sorted)

# Breakdown: XAU up / GBP down vs XAU down / GBP up
xau_up_gbp_down = merged_sorted[
    (merged_sorted['return_xau'] > 0) & (merged_sorted['return_gbp'] < 0)
]
xau_down_gbp_up = merged_sorted[
    (merged_sorted['return_xau'] < 0) & (merged_sorted['return_gbp'] > 0)
]

stream6["6B_divergence_signal"] = {
    "divergence_days": {
        "count": int(len(div_days)),
        "pct_of_total": round(float(len(div_days) / len(merged_sorted)), 4),
        "next_day_outcomes": div_outcomes,
    },
    "xau_up_gbp_down_divergence": {
        "count": int(len(xau_up_gbp_down)),
        "next_day_outcomes": next_day_outcomes(xau_up_gbp_down, merged_sorted),
    },
    "xau_down_gbp_up_divergence": {
        "count": int(len(xau_down_gbp_up)),
        "next_day_outcomes": next_day_outcomes(xau_down_gbp_up, merged_sorted),
    },
    "strong_alignment_days": {
        "count": int(len(strong_align)),
        "pct_of_total": round(float(len(strong_align) / len(merged_sorted)), 4),
        "next_day_outcomes": align_outcomes,
    },
}

print(f"  Divergence days: {len(div_days)}/{len(merged_sorted)} ({len(div_days)/len(merged_sorted):.1%})")
if div_outcomes:
    print(f"    Next day XAU avg: {div_outcomes['xau_next_day_avg_return_pct']:.4f}%, GBP avg: {div_outcomes['gbp_next_day_avg_return_pct']:.4f}%")
print(f"  Strong alignment days: {len(strong_align)}")
if align_outcomes:
    print(f"    Next day XAU avg: {align_outcomes['xau_next_day_avg_return_pct']:.4f}%, GBP avg: {align_outcomes['gbp_next_day_avg_return_pct']:.4f}%")

# ── 6C: Sweep Timing Comparison ──────────────────────────────────────────────
print("\n=== 6C: Sweep Timing Comparison ===")

XAU_SWEEP_MIN = 3.0
GBP_SWEEP_MIN = 0.00015

def compute_asian_ranges_and_sweeps(m15_df, sweep_min, label):
    """Return dict of date -> {asian_high, asian_low, sweep_high_time, sweep_low_time}"""
    day_info = {}

    for date, day_data in m15_df.groupby('date'):
        asian = day_data[(day_data['hour'] >= 0) & (day_data['hour'] < 7)]
        london = day_data[(day_data['hour'] >= 7) & (day_data['hour'] < 17)]

        if len(asian) < 4 or len(london) < 2:
            continue

        a_high = asian['high'].max()
        a_low = asian['low'].min()

        sweep_high_time = None
        sweep_low_time = None

        for _, candle in london.iterrows():
            if sweep_high_time is None and candle['high'] > a_high + sweep_min:
                sweep_high_time = candle['time']
            if sweep_low_time is None and candle['low'] < a_low - sweep_min:
                sweep_low_time = candle['time']
            if sweep_high_time and sweep_low_time:
                break

        day_info[date] = {
            "asian_high": a_high,
            "asian_low": a_low,
            "sweep_high_time": sweep_high_time,
            "sweep_low_time": sweep_low_time,
        }

    return day_info

xau_sweeps = compute_asian_ranges_and_sweeps(xau_m15, XAU_SWEEP_MIN, "XAUUSD")
gbp_sweeps = compute_asian_ranges_and_sweeps(gbp_m15, GBP_SWEEP_MIN, "GBPUSD")

# Compare sweep timing on common dates
common_dates = set(xau_sweeps.keys()) & set(gbp_sweeps.keys())
print(f"  Common dates for sweep comparison: {len(common_dates)}")

xau_first_count = 0
gbp_first_count = 0
same_time_count = 0
time_diffs = []
opposite_sweep_days = []

for date in common_dates:
    xau = xau_sweeps[date]
    gbp = gbp_sweeps[date]

    # Determine first sweep time for each instrument (earliest of high/low sweep)
    xau_times = []
    if xau['sweep_high_time'] is not None:
        xau_times.append(('high', xau['sweep_high_time']))
    if xau['sweep_low_time'] is not None:
        xau_times.append(('low', xau['sweep_low_time']))

    gbp_times = []
    if gbp['sweep_high_time'] is not None:
        gbp_times.append(('high', gbp['sweep_high_time']))
    if gbp['sweep_low_time'] is not None:
        gbp_times.append(('low', gbp['sweep_low_time']))

    if not xau_times or not gbp_times:
        continue

    xau_first_sweep = min(xau_times, key=lambda x: x[1])
    gbp_first_sweep = min(gbp_times, key=lambda x: x[1])

    if xau_first_sweep[1] < gbp_first_sweep[1]:
        xau_first_count += 1
    elif gbp_first_sweep[1] < xau_first_sweep[1]:
        gbp_first_count += 1
    else:
        same_time_count += 1

    diff_minutes = abs((xau_first_sweep[1] - gbp_first_sweep[1]).total_seconds()) / 60
    time_diffs.append(diff_minutes)

    # Opposite sweeps: one sweeps high, other sweeps low
    if xau_first_sweep[0] != gbp_first_sweep[0]:
        opposite_sweep_days.append(date)

total_compared = xau_first_count + gbp_first_count + same_time_count

# What happens on opposite sweep days? Check next day returns
opposite_next_day = []
for date in opposite_sweep_days:
    idx = merged_sorted[merged_sorted['date'] == date].index
    if len(idx) > 0 and idx[0] + 1 < len(merged_sorted):
        next_row = merged_sorted.iloc[idx[0] + 1]
        opposite_next_day.append({
            "xau_return": float(next_row['return_pct_xau']),
            "gbp_return": float(next_row['return_pct_gbp']),
        })

td = np.array(time_diffs) if time_diffs else np.array([0])

stream6["6C_sweep_timing"] = {
    "common_dates_analyzed": int(len(common_dates)),
    "dates_with_both_sweeps": total_compared,
    "xau_sweeps_first_count": xau_first_count,
    "gbp_sweeps_first_count": gbp_first_count,
    "simultaneous_count": same_time_count,
    "xau_sweeps_first_pct": round(xau_first_count / total_compared, 4) if total_compared > 0 else None,
    "gbp_sweeps_first_pct": round(gbp_first_count / total_compared, 4) if total_compared > 0 else None,
    "avg_time_diff_minutes": round(float(td.mean()), 1),
    "median_time_diff_minutes": round(float(np.median(td)), 1),
    "opposite_sweep_days": {
        "count": len(opposite_sweep_days),
        "pct_of_compared": round(len(opposite_sweep_days) / total_compared, 4) if total_compared > 0 else None,
        "next_day_xau_avg_return": round(float(np.mean([x['xau_return'] for x in opposite_next_day])), 4) if opposite_next_day else None,
        "next_day_gbp_avg_return": round(float(np.mean([x['gbp_return'] for x in opposite_next_day])), 4) if opposite_next_day else None,
        "next_day_sample_size": len(opposite_next_day),
    },
    "sweep_min_thresholds": {"XAUUSD": XAU_SWEEP_MIN, "GBPUSD": GBP_SWEEP_MIN},
}

print(f"  XAU sweeps first: {xau_first_count}/{total_compared} ({xau_first_count/total_compared:.1%})" if total_compared else "  No data")
print(f"  GBP sweeps first: {gbp_first_count}/{total_compared} ({gbp_first_count/total_compared:.1%})" if total_compared else "")
print(f"  Avg time diff: {td.mean():.1f} min, Median: {np.median(td):.1f} min")
print(f"  Opposite sweep days: {len(opposite_sweep_days)}")


# ═══════════════════════════════════════════════════════════════════════════════
# SAVE OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════════

out_dir = BASE / "knowledge_base_backtest/analysis"
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "microstructure_stream5_session_dynamics_20260405.json", "w") as f:
    json.dump(stream5, f, indent=2, default=str)

with open(out_dir / "microstructure_stream6_cross_instrument_20260405.json", "w") as f:
    json.dump(stream6, f, indent=2, default=str)

print("\n=== FILES SAVED ===")
print(f"  {out_dir / 'microstructure_stream5_session_dynamics_20260405.json'}")
print(f"  {out_dir / 'microstructure_stream6_cross_instrument_20260405.json'}")
print("\nDone.")
