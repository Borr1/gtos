"""
TEST: Body breaks vs wick breaks on gold HTF
FINDING: "On higher timeframes for gold, body breaks are more reliable
  than wick breaks" (Trade Forex with Paul)
ALSO: "Thick/heavy OBs contain more resting liquidity than thin OBs,
  causing larger price expansions" (The Soup Room)
OUR DATA: body_range_ratio < 0.3 (thin-wick OBs) = 70.9% val vs 46.5%
PRIORITY: 4 (potential contradiction + validation opportunity)

This test checks structural breaks (BOS/CHoCH) classified by whether
they broke via candle body-close or wick-only on H1/H4 XAUUSD.
"""
import pandas as pd
import numpy as np
from scipy.stats import fisher_exact

# Load H1 and H4 data
for tf_label, tf_file in [('H1', 'data/XAUUSD_H1.csv'), ('H4', 'data/XAUUSD_H4.csv')]:
    df = pd.read_csv(tf_file)
    df['time'] = pd.to_datetime(df['time'])
    print(f"\n{'='*60}")
    print(f"TIMEFRAME: {tf_label} ({len(df)} candles)")
    print(f"{'='*60}")

    # Identify swing highs and lows (simple: higher high + lower low around point)
    lookback = 5
    df['swing_high'] = False
    df['swing_low'] = False
    for i in range(lookback, len(df) - lookback):
        window_highs = df['high'].iloc[i-lookback:i+lookback+1]
        window_lows = df['low'].iloc[i-lookback:i+lookback+1]
        if df['high'].iloc[i] == window_highs.max():
            df.loc[df.index[i], 'swing_high'] = True
        if df['low'].iloc[i] == window_lows.min():
            df.loc[df.index[i], 'swing_low'] = True

    # Find breaks of structure
    swing_highs = df[df['swing_high']].copy()
    swing_lows = df[df['swing_low']].copy()

    body_breaks = {'continuation': 0, 'failure': 0}
    wick_breaks = {'continuation': 0, 'failure': 0}

    # Check each swing high break
    for idx in range(len(swing_highs)):
        sh = swing_highs.iloc[idx]
        sh_level = sh['high']
        sh_time = sh['time']

        # Find the candle that first breaks this level
        future = df[df['time'] > sh_time].head(20)
        for _, candle in future.iterrows():
            if candle['high'] > sh_level:
                # Determine body vs wick break
                candle_close = candle['close']
                candle_open = candle['open']
                body_top = max(candle_close, candle_open)

                if body_top > sh_level:
                    break_type = 'body'
                else:
                    break_type = 'wick'

                # Check continuation: does price close above sh_level
                # within next 5 candles?
                break_idx = df[df['time'] == candle['time']].index[0]
                followup = df.iloc[break_idx+1:break_idx+6]
                if len(followup) > 0:
                    continued = any(followup['close'] > sh_level)
                    target = body_breaks if break_type == 'body' else wick_breaks
                    if continued:
                        target['continuation'] += 1
                    else:
                        target['failure'] += 1
                break

    # Same for swing low breaks
    for idx in range(len(swing_lows)):
        sl = swing_lows.iloc[idx]
        sl_level = sl['low']
        sl_time = sl['time']

        future = df[df['time'] > sl_time].head(20)
        for _, candle in future.iterrows():
            if candle['low'] < sl_level:
                candle_close = candle['close']
                candle_open = candle['open']
                body_bottom = min(candle_close, candle_open)

                if body_bottom < sl_level:
                    break_type = 'body'
                else:
                    break_type = 'wick'

                break_idx = df[df['time'] == candle['time']].index[0]
                followup = df.iloc[break_idx+1:break_idx+6]
                if len(followup) > 0:
                    continued = any(followup['close'] < sl_level)
                    target = body_breaks if break_type == 'body' else wick_breaks
                    if continued:
                        target['continuation'] += 1
                    else:
                        target['failure'] += 1
                break

    # Results
    body_total = body_breaks['continuation'] + body_breaks['failure']
    wick_total = wick_breaks['continuation'] + wick_breaks['failure']

    if body_total > 0 and wick_total > 0:
        body_rate = body_breaks['continuation'] / body_total
        wick_rate = wick_breaks['continuation'] / wick_total
        print(f"Body breaks: {body_rate:.1%} continuation ({body_total} breaks)")
        print(f"Wick breaks: {wick_rate:.1%} continuation ({wick_total} breaks)")
        print(f"Gap: {(body_rate - wick_rate)*100:+.1f}pp")

        _, pval = fisher_exact([
            [body_breaks['continuation'], body_breaks['failure']],
            [wick_breaks['continuation'], wick_breaks['failure']]
        ])
        print(f"Fisher p-value: {pval:.4f}")
    else:
        print(f"Body breaks: {body_total}, Wick breaks: {wick_total}")
        print("Insufficient data for comparison")

print(f"\n{'='*60}")
print("DECISION GATE")
print(f"{'='*60}")
print("CONFIRMED if: body continuation > wick by 10+pp AND p < 0.05")
print("REJECTED if: gap < 5pp OR p > 0.10")
print("INCONCLUSIVE otherwise — need more granular BOS/CHoCH classification")
