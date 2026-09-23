"""
TEST: Gold fills FVGs more completely than EUR/USD
FINDING: "Gold normally fills imbalances before reversing — more reliable
  than EUR/USD where price often only reaches equilibrium" (Trade Forex with Paul)
OUR DATA: FVG 80-100% fill = 71.4% continuation rate (gold only)
PRIORITY: 3 (COMPLEMENTARY — could inform TP targeting)

Compares FVG fill rates on XAUUSD H1 vs EURUSD H1.
"""
import pandas as pd
import numpy as np

def detect_fvgs(df, min_gap_pct=0.001):
    """Detect Fair Value Gaps (3-candle pattern with gap between candle 1 and 3)"""
    fvgs = []
    for i in range(2, len(df)):
        c1 = df.iloc[i-2]  # First candle
        c3 = df.iloc[i]    # Third candle

        # Bullish FVG: c3.low > c1.high (gap up)
        if c3['low'] > c1['high']:
            gap_size = c3['low'] - c1['high']
            mid_price = (c1['high'] + c3['low']) / 2
            if gap_size / mid_price >= min_gap_pct:
                fvgs.append({
                    'idx': i,
                    'time': df.iloc[i]['time'],
                    'type': 'bullish',
                    'top': c3['low'],
                    'bottom': c1['high'],
                    'gap_size': gap_size,
                })

        # Bearish FVG: c1.low > c3.high (gap down)
        if c1['low'] > c3['high']:
            gap_size = c1['low'] - c3['high']
            mid_price = (c1['low'] + c3['high']) / 2
            if gap_size / mid_price >= min_gap_pct:
                fvgs.append({
                    'idx': i,
                    'time': df.iloc[i]['time'],
                    'type': 'bearish',
                    'top': c1['low'],
                    'bottom': c3['high'],
                    'gap_size': gap_size,
                })

    return fvgs

def measure_fill(df, fvg, lookforward=50):
    """Measure how much of the FVG gets filled within lookforward candles"""
    start_idx = fvg['idx'] + 1
    end_idx = min(start_idx + lookforward, len(df))
    future = df.iloc[start_idx:end_idx]

    if len(future) == 0:
        return None

    gap_size = fvg['gap_size']

    if fvg['type'] == 'bullish':
        # Price needs to come DOWN to fill (touch bottom from top)
        lowest = future['low'].min()
        filled = max(0, fvg['top'] - lowest)
    else:
        # Price needs to come UP to fill (touch top from bottom)
        highest = future['high'].max()
        filled = max(0, highest - fvg['bottom'])

    fill_pct = min(filled / gap_size, 1.0) if gap_size > 0 else 0
    return fill_pct

for pair, file_path, min_gap in [
    ('XAUUSD', 'data/XAUUSD_H1.csv', 0.0005),  # ~$1 gap on gold
    ('EURUSD', 'data/EURUSD_H1.csv', 0.0001),   # ~1 pip gap on EUR
]:
    df = pd.read_csv(file_path)
    df['time'] = pd.to_datetime(df['time'])
    print(f"\n{'='*60}")
    print(f"{pair} H1 ({len(df)} candles)")
    print(f"{'='*60}")

    fvgs = detect_fvgs(df, min_gap)
    print(f"FVGs detected: {len(fvgs)}")

    fills = []
    for fvg in fvgs:
        fill = measure_fill(df, fvg)
        if fill is not None:
            fills.append(fill)

    if fills:
        fills = np.array(fills)
        print(f"Mean fill: {np.mean(fills):.1%}")
        print(f"Median fill: {np.median(fills):.1%}")
        print(f"100% filled: {np.mean(fills >= 0.99):.1%}")
        print(f"80-100% filled: {np.mean(fills >= 0.80):.1%}")
        print(f"50-80% (equilibrium): {np.mean((fills >= 0.50) & (fills < 0.80)):.1%}")
        print(f"<50% filled: {np.mean(fills < 0.50):.1%}")
        print(f"Unfilled (<10%): {np.mean(fills < 0.10):.1%}")

        # Distribution buckets
        buckets = [0, 0.25, 0.50, 0.75, 1.01]
        for i in range(len(buckets)-1):
            low, high = buckets[i], buckets[i+1]
            count = np.sum((fills >= low) & (fills < high))
            pct = count / len(fills)
            print(f"  {low:.0%}-{high-0.01:.0%}: {count} ({pct:.1%})")

# Statistical comparison
print(f"\n{'='*60}")
print("CROSS-INSTRUMENT COMPARISON")
print(f"{'='*60}")
print("CONFIRMED if: XAUUSD 100% fill rate > EURUSD by 10+pp")
print("REJECTED if: gap < 5pp or EURUSD fills MORE")
print("If confirmed → FVG-based TP targets more reliable on gold")
