"""V1 Independent Validator — synthetic stress test for identify_structure.

Constructs OHLCV dicts directly (not through project helpers) so swings
form via detect_swings. Tests whether identify_structure can EVER return
'bearish' for clearly bearish patterns.
"""
import sys
sys.path.insert(0, 'C:/Users/MSI/Documents/ai-trading-agent')

from src.components.market_state import identify_structure, detect_swings
from datetime import datetime, timedelta, timezone


def craft_swings(swing_pattern):
    """Place explicit highs/lows at specific bar indices, with neutral padding in between.

    swing_pattern: list of (index, type, price) tuples.
    Returns a candle list that will produce exactly those swings via detect_swings(min_bars=2).
    Padding bars use a narrow mid-range neutral OHLC so they are neither swing highs nor lows.
    """
    # Determine per-bar mid so padding never exceeds/undercuts swings.
    # We assign padding bars a rolling mid that interpolates between
    # adjacent swings, so the swing bars are strict local extremes.
    # Simplest: give each padding bar high < all nearby swing highs,
    # and low > all nearby swing lows. Use a wide "corridor" of ±0.001
    # around a dynamic midpoint.
    max_idx = max(s[0] for s in swing_pattern) + 3
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    # Map index -> (type, price)
    swing_map = {s[0]: (s[1], s[2]) for s in swing_pattern}

    # Walk through and compute a smooth mid for each bar.
    # Between two adjacent swing indices, the midpoint between their prices
    # is safe for padding — it's above any low swing and below any high swing
    # IF we arrange so that every high swing > neighbors > every low swing
    # locally. Since we alternate, just interpolate between consecutive swings.
    sorted_swings = sorted(swing_pattern, key=lambda x: x[0])
    def mid_at(i):
        # Find enclosing swings
        before = [s for s in sorted_swings if s[0] <= i]
        after = [s for s in sorted_swings if s[0] > i]
        if before and after:
            b = before[-1]
            a = after[0]
            # linear interp between b.price and a.price
            frac = (i - b[0]) / max(a[0] - b[0], 1)
            return b[2] + frac * (a[2] - b[2])
        if before:
            return before[-1][2]
        if after:
            return after[0][2]
        return 100.0

    candles = []
    for i in range(max_idx):
        if i in swing_map:
            typ, price = swing_map[i]
            if typ == 'high':
                # Strict local max
                candles.append({
                    'open': price - 1.0,
                    'high': price,
                    'low': price - 2.0,
                    'close': price - 0.5,
                    'time': (t0 + timedelta(hours=i)).isoformat(),
                    'volume': 1000,
                })
            else:
                candles.append({
                    'open': price + 1.0,
                    'high': price + 2.0,
                    'low': price,
                    'close': price + 0.5,
                    'time': (t0 + timedelta(hours=i)).isoformat(),
                    'volume': 1000,
                })
        else:
            m = mid_at(i)
            # Narrow padding candle — its high must be below any nearby
            # high swing, and its low must be above any nearby low swing.
            # Using m ± 0.01 and ensuring neighbors are far enough in price.
            candles.append({
                'open': m,
                'high': m + 0.01,
                'low': m - 0.01,
                'close': m,
                'time': (t0 + timedelta(hours=i)).isoformat(),
                'volume': 1000,
            })
    return candles


def run_case(label, pattern):
    candles = craft_swings(pattern)
    swings = detect_swings(candles, min_bars=2)
    struct = identify_structure(swings)
    print(f'{label}')
    swing_summary = [(s.index, s.type, round(s.price, 2)) for s in swings]
    print(f'  swings: {swing_summary}')
    print(f'  direction: {struct.direction}')
    print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
    print()


# Fixture A: Pure uptrend
run_case('Fixture A (6 swings, pure uptrend)', [
    (3, 'low', 98),
    (6, 'high', 103),
    (9, 'low', 99),    # HL
    (12, 'high', 105), # HH
    (15, 'low', 101),  # HL
    (18, 'high', 107), # HH
])

# Fixture B: Pure downtrend
run_case('Fixture B (6 swings, pure downtrend)', [
    (3, 'high', 107),
    (6, 'low', 102),
    (9, 'high', 105), # LH
    (12, 'low', 100), # LL
    (15, 'high', 103),# LH
    (18, 'low', 98),  # LL
])

# Fixture B2: Even stronger pure downtrend (8 swings)
run_case('Fixture B2 (8 swings, strong pure downtrend)', [
    (3, 'high', 110),
    (6, 'low', 105),
    (9, 'high', 108),  # LH
    (12, 'low', 103),  # LL
    (15, 'high', 106), # LH
    (18, 'low', 100),  # LL
    (21, 'high', 104), # LH
    (24, 'low', 97),   # LL
])

# Fixture C: Flat range (equal highs/lows throughout)
run_case('Fixture C (flat range, equal H & L)', [
    (3, 'high', 101),
    (6, 'low', 99),
    (9, 'high', 101),
    (12, 'low', 99),
    (15, 'high', 101),
    (18, 'low', 99),
])

# Fixture D: V reversal (down then up)
run_case('Fixture D (V reversal down-then-up)', [
    (3, 'high', 107),
    (6, 'low', 102),
    (9, 'high', 105), # LH
    (12, 'low', 98),  # LL (bottom)
    (15, 'high', 103),# LH
    (18, 'low', 99),  # HL vs 98 — reversal
    (21, 'high', 106),# HH vs 103
    (24, 'low', 101), # HL vs 99
])

# Fixture E: Inverted V (up then down)
run_case('Fixture E (inverted V up-then-down)', [
    (3, 'low', 98),
    (6, 'high', 103),
    (9, 'low', 99),   # HL
    (12, 'high', 106),# HH (top)
    (15, 'low', 100), # HL
    (18, 'high', 104),# LH — turns
    (21, 'low', 97),  # LL
    (24, 'high', 102),# LH
])

# Fixture G: Early bullish, LATE bearish — tests whether cumulative hh/hl
# locks in bullish even after structure turns down
run_case('Fixture G (bullish early, then sharp bearish turn)', [
    (3, 'low', 95),
    (6, 'high', 100),
    (9, 'low', 97),    # HL
    (12, 'high', 105), # HH
    (15, 'low', 102),  # HL
    (18, 'high', 110), # HH — top
    (21, 'low', 98),   # LL vs 102 (big drop)
    (24, 'high', 103), # LH vs 110
    (27, 'low', 92),   # LL vs 98
    (30, 'high', 97),  # LH vs 103
])

# Fixture H: ONLY 2 swings each (min case)
run_case('Fixture H (minimum: 2 high 2 low, bearish)', [
    (3, 'high', 110),
    (6, 'low', 105),
    (9, 'high', 108),  # LH
    (12, 'low', 100),  # LL
])

# Fixture I: EXACTLY 3 swings each (boundary for recent_pairs=3)
run_case('Fixture I (3 highs 3 lows, all bearish)', [
    (3, 'high', 110),
    (6, 'low', 105),
    (9, 'high', 108),  # LH
    (12, 'low', 103),  # LL
    (15, 'high', 106), # LH
    (18, 'low', 100),  # LL
])

# Fixture J: MIXED ambiguous — hh=3, hl=3, ll=3, lh=3 all simultaneously
# To construct: alternating pattern where each swing is sometimes HH sometimes LH
run_case('Fixture J (mixed — both branches qualify?)', [
    (3, 'low', 98),
    (6, 'high', 103),
    (9, 'low', 95),    # LL vs 98
    (12, 'high', 108), # HH vs 103
    (15, 'low', 92),   # LL vs 95
    (18, 'high', 110), # HH vs 108
    (21, 'low', 90),   # LL vs 92
    (24, 'high', 112), # HH vs 110
])
