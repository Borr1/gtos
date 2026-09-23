"""Test the saturation hypothesis:

When both branches qualify (hh>=3 AND hl>=3 AND ll>=3 AND lh>=3),
does identify_structure deterministically pick bullish?

Also: does it happen with realistic 168-bar H1 windows?
"""
import sys
sys.path.insert(0, 'C:/Users/MSI/Documents/ai-trading-agent')

from src.components.market_state import identify_structure
from src.models.market_state_models import Swing
from datetime import datetime, timezone


def make_swing(index, typ, price):
    return Swing(index=index, type=typ, price=price, time=datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat())


print('=== Test 1: Construct swings where BOTH branches qualify ===')
# We need highs AND lows such that:
#  - hh_count (highs[i] > highs[i-1]) >= 3
#  - hl_count (lows[i] > lows[i-1]) >= 3
#  - ll_count (lows[i] < lows[i-1]) >= 3
#  - lh_count (highs[i] < highs[i-1]) >= 3
# Build highs that oscillate up-down-up-down... with matching lows.
# 8 highs: 100, 105, 102, 108, 104, 110, 106, 112 (alternate HH/LH)
# hh pairs: (100->105)HH, (105->102)LH, (102->108)HH, (108->104)LH, (104->110)HH, (110->106)LH, (106->112)HH
# => hh=4, lh=3
# Similarly 8 lows: 90, 95, 92, 98, 94, 100, 96, 102 -> hl=4, ll=3
highs_prices = [100, 105, 102, 108, 104, 110, 106, 112]
lows_prices = [90, 95, 92, 98, 94, 100, 96, 102]

# But wait — the swing pattern needs to alternate high/low temporally.
# The function doesn't care about temporal order within highs or within lows,
# only within the highs list and within the lows list.
swings = []
idx = 0
for hp, lp in zip(highs_prices, lows_prices):
    swings.append(make_swing(idx, 'low', lp))
    idx += 1
    swings.append(make_swing(idx, 'high', hp))
    idx += 1

struct = identify_structure(swings)
print(f'  highs={highs_prices}')
print(f'  lows={lows_prices}')
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}')
print(f'  recent_pairs = min(3, {len(highs_prices)-1}, {len(lows_prices)-1}) = {min(3, len(highs_prices)-1, len(lows_prices)-1)}')
# Does bullish branch dominate when hh>=3 AND hl>=3 AND ll>=3 AND lh>=3?

print()
print('=== Test 2: hh=3, hl=3, ll=3, lh=3 exactly ===')
# Force all counts to 3 exactly by choosing 4 highs and 4 lows in alternating pattern
# 4 highs with 3 HH + 0 LH: 100, 105, 110, 115 -> hh=3, lh=0 (monotone rise)
# Try: 100, 105, 103, 108 -> hh pairs: 100->105 HH, 105->103 LH, 103->108 HH -> hh=2, lh=1
# We need hh=3 AND lh>=3 in same list: impossible with 4 highs (3 pairs total).
# Need at least 7 highs to have hh>=3 AND lh>=3 (6 pairs).
highs7 = [100, 105, 103, 110, 106, 112, 108]  # pairs: HH, LH, HH, LH, HH, LH -> hh=3, lh=3
lows7 = [90, 95, 93, 100, 96, 102, 98]        # same pattern -> hl=3, ll=3
swings = []
idx = 0
# Interleave
for i in range(len(highs7)):
    swings.append(make_swing(idx, 'low', lows7[i]))
    idx += 1
    swings.append(make_swing(idx, 'high', highs7[i]))
    idx += 1
struct = identify_structure(swings)
print(f'  highs={highs7}')
print(f'  lows={lows7}')
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}')

print()
print('=== Test 3: hh=4, hl=4, ll=4, lh=4 — CLEAR tie ===')
highs9 = [100, 106, 103, 109, 105, 111, 107, 113, 109]  # 4 HH + 4 LH
lows9 = [90, 96, 93, 99, 95, 101, 97, 103, 99]          # 4 HL + 4 LL
swings = []
idx = 0
for i in range(len(highs9)):
    swings.append(make_swing(idx, 'low', lows9[i]))
    idx += 1
    swings.append(make_swing(idx, 'high', highs9[i]))
    idx += 1
struct = identify_structure(swings)
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}  <-- does BULLISH win when tie?')

print()
print('=== Test 4: hh=3, hl=3, ll=10, lh=10 — bullish THRESHOLD MET but bearish dominant ===')
# bullish check is "hh>=3 AND hl>=3". If lh >> 3, does that matter? NO — the check is first-match.
highs13 = [100]
# Make 3 HH (100->102->104->106) then 10 LH (106->105->104->103->102->101->100->99->98->97->96)
highs13 = [100, 102, 104, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96]
# hh pairs (only ascending): 100->102=HH, 102->104=HH, 104->106=HH = 3
# lh pairs (descending): 106->105, 105->104, 104->103, 103->102, 102->101, 101->100, 100->99, 99->98, 98->97, 97->96 = 10
lows13 = [90, 92, 94, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86]
# hl=3, ll=10
swings = []
idx = 0
for i in range(len(highs13)):
    swings.append(make_swing(idx, 'low', lows13[i]))
    idx += 1
    swings.append(make_swing(idx, 'high', highs13[i]))
    idx += 1
struct = identify_structure(swings)
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}  <-- bullish would win since branch checked first')

print()
print('=== Test 5: hh=2 (BELOW threshold), ll=5, lh=5, hl=0 — should go bearish ===')
highs7 = [110, 108, 106, 104, 102, 100, 98]
# hh pairs: none (all LH): hh=0, lh=6
lows7 = [100, 98, 96, 94, 92, 90, 88]
# hl=0, ll=6
swings = []
idx = 0
for i in range(len(highs7)):
    swings.append(make_swing(idx, 'low', lows7[i]))
    idx += 1
    swings.append(make_swing(idx, 'high', highs7[i]))
    idx += 1
struct = identify_structure(swings)
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}')

print()
print('=== Test 6: Realistic H1 window — 168 bars with slightly noisy TREND DOWN ===')
# Simulate a real H1 lookback of 168 bars. Generate swings from a bearish random walk.
import random
random.seed(42)
n = 168
# Simulate a trending-down market: close[i] = close[i-1] - 0.2 + noise
prices = [100.0]
for i in range(1, n):
    prices.append(prices[-1] - 0.2 + random.gauss(0, 1.0))

# Build OHLC from these "closes"
from datetime import timedelta
from src.components.market_state import detect_swings
t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
candles = []
for i, p in enumerate(prices):
    o = prices[i-1] if i > 0 else p
    c = p
    h = max(o, c) + abs(random.gauss(0, 0.5))
    l = min(o, c) - abs(random.gauss(0, 0.5))
    candles.append({
        'open': o, 'high': h, 'low': l, 'close': c,
        'time': (t0 + timedelta(hours=i)).isoformat(),
        'volume': 1000,
    })
swings = detect_swings(candles, min_bars=2)
struct = identify_structure(swings)
print(f'  Bearish random walk (drift -0.2, sigma 1.0, 168 bars)')
n_high = sum(1 for s in swings if s.type == 'high')
n_low = sum(1 for s in swings if s.type == 'low')
print(f'  swings count: {len(swings)} (highs={n_high}, lows={n_low})')
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}')

print()
print('=== Test 7: Realistic H1 window — 168 bars with NEUTRAL random walk (drift 0) ===')
random.seed(42)
prices = [100.0]
for i in range(1, n):
    prices.append(prices[-1] + random.gauss(0, 1.0))
candles = []
for i, p in enumerate(prices):
    o = prices[i-1] if i > 0 else p
    c = p
    h = max(o, c) + abs(random.gauss(0, 0.5))
    l = min(o, c) - abs(random.gauss(0, 0.5))
    candles.append({
        'open': o, 'high': h, 'low': l, 'close': c,
        'time': (t0 + timedelta(hours=i)).isoformat(),
        'volume': 1000,
    })
swings = detect_swings(candles, min_bars=2)
struct = identify_structure(swings)
print(f'  Neutral random walk, 168 bars')
print(f'  swings count: {len(swings)}')
print(f'  hh={struct.hh_count} hl={struct.hl_count} lh={struct.lh_count} ll={struct.ll_count}')
print(f'  direction: {struct.direction}')

print()
print('=== Test 8: 100 random bearish runs — fraction labeled bearish? ===')
bearish_count = 0
bullish_count = 0
transitional_count = 0
insufficient = 0
for seed in range(100):
    random.seed(seed)
    prices = [100.0]
    for i in range(1, 168):
        prices.append(prices[-1] - 0.15 + random.gauss(0, 0.8))
    candles = []
    for i, p in enumerate(prices):
        o = prices[i-1] if i > 0 else p
        c = p
        h = max(o, c) + abs(random.gauss(0, 0.3))
        l = min(o, c) - abs(random.gauss(0, 0.3))
        candles.append({
            'open': o, 'high': h, 'low': l, 'close': c,
            'time': (t0 + timedelta(hours=i)).isoformat(),
            'volume': 1000,
        })
    swings = detect_swings(candles, min_bars=2)
    struct = identify_structure(swings)
    if struct.direction == 'bearish':
        bearish_count += 1
    elif struct.direction == 'bullish':
        bullish_count += 1
    elif struct.direction == 'transitional':
        transitional_count += 1
    else:
        insufficient += 1

print(f'  bearish-drift random walks (n=100): bearish={bearish_count}, bullish={bullish_count}, transitional={transitional_count}, insufficient={insufficient}')

print()
print('=== Test 9: 100 random BULLISH runs ===')
bearish_count = bullish_count = transitional_count = insufficient = 0
for seed in range(100):
    random.seed(seed)
    prices = [100.0]
    for i in range(1, 168):
        prices.append(prices[-1] + 0.15 + random.gauss(0, 0.8))
    candles = []
    for i, p in enumerate(prices):
        o = prices[i-1] if i > 0 else p
        c = p
        h = max(o, c) + abs(random.gauss(0, 0.3))
        l = min(o, c) - abs(random.gauss(0, 0.3))
        candles.append({
            'open': o, 'high': h, 'low': l, 'close': c,
            'time': (t0 + timedelta(hours=i)).isoformat(),
            'volume': 1000,
        })
    swings = detect_swings(candles, min_bars=2)
    struct = identify_structure(swings)
    if struct.direction == 'bearish': bearish_count += 1
    elif struct.direction == 'bullish': bullish_count += 1
    elif struct.direction == 'transitional': transitional_count += 1
    else: insufficient += 1
print(f'  bullish-drift random walks (n=100): bearish={bearish_count}, bullish={bullish_count}, transitional={transitional_count}, insufficient={insufficient}')

print()
print('=== Test 10: 100 random NEUTRAL (zero-drift) runs ===')
bearish_count = bullish_count = transitional_count = insufficient = 0
for seed in range(100):
    random.seed(seed)
    prices = [100.0]
    for i in range(1, 168):
        prices.append(prices[-1] + random.gauss(0, 0.8))
    candles = []
    for i, p in enumerate(prices):
        o = prices[i-1] if i > 0 else p
        c = p
        h = max(o, c) + abs(random.gauss(0, 0.3))
        l = min(o, c) - abs(random.gauss(0, 0.3))
        candles.append({
            'open': o, 'high': h, 'low': l, 'close': c,
            'time': (t0 + timedelta(hours=i)).isoformat(),
            'volume': 1000,
        })
    swings = detect_swings(candles, min_bars=2)
    struct = identify_structure(swings)
    if struct.direction == 'bearish': bearish_count += 1
    elif struct.direction == 'bullish': bullish_count += 1
    elif struct.direction == 'transitional': transitional_count += 1
    else: insufficient += 1
print(f'  neutral random walks (n=100): bearish={bearish_count}, bullish={bullish_count}, transitional={transitional_count}, insufficient={insufficient}')
