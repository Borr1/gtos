"""V1 Independent Validator — historical H1 replay.

Reads CSV OHLCV data for each of 5 instruments (XAUUSD, US30_cash, USDJPY,
GBPJPY, GBPUSD). For each bar beyond bar #168, builds a 168-bar sliding
window, runs detect_swings + identify_structure, and counts the labels.

If the prior audit is correct: 0 bearish labels, ~100% bullish.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, 'C:/Users/MSI/Documents/ai-trading-agent')
from src.components.market_state import identify_structure, detect_swings

DATA_DIR = Path('C:/Users/MSI/Documents/ai-trading-agent/data/historical_2026')
LOOKBACK = 168
INSTRUMENTS = ['XAUUSD', 'US30_cash', 'USDJPY', 'GBPJPY', 'GBPUSD']


def load_h1(symbol):
    fp = DATA_DIR / f'{symbol}_H1.csv'
    candles = []
    with open(fp) as f:
        reader = csv.DictReader(f)
        for r in reader:
            candles.append({
                'time': r['time'],
                'open': float(r['open']),
                'high': float(r['high']),
                'low': float(r['low']),
                'close': float(r['close']),
                'volume': float(r['volume']),
            })
    return candles


def replay_symbol(symbol):
    candles = load_h1(symbol)
    total = 0
    counts = Counter()
    # Also track hh/hl/lh/ll for bullish-labeled rows to see saturation
    bullish_with_bearish_qualified = 0  # bullish labeled, but ll>=rp AND lh>=rp (bug condition)
    for i in range(LOOKBACK, len(candles)):
        window = candles[i - LOOKBACK:i]
        swings = detect_swings(window, min_bars=2)
        struct = identify_structure(swings)
        counts[struct.direction] += 1
        total += 1
        # Check saturation condition
        recent_pairs = min(3, len([s for s in swings if s.type == 'high']) - 1,
                           len([s for s in swings if s.type == 'low']) - 1)
        if struct.direction == 'bullish' and recent_pairs >= 1:
            if (struct.ll_count or 0) >= recent_pairs and (struct.lh_count or 0) >= recent_pairs:
                bullish_with_bearish_qualified += 1
    return total, counts, bullish_with_bearish_qualified


grand_total = 0
grand_counts = Counter()
grand_bug = 0
print(f'{"Symbol":<12} {"Total":>6} {"Bull":>6} {"Bear":>6} {"Trans":>6} {"Insuf":>6} {"BothBranchesQualified":>23}')
print('-' * 80)
for sym in INSTRUMENTS:
    total, counts, bug = replay_symbol(sym)
    grand_total += total
    grand_counts.update(counts)
    grand_bug += bug
    b = counts.get('bullish', 0)
    be = counts.get('bearish', 0)
    tr = counts.get('transitional', 0)
    ins = counts.get('insufficient_data', 0)
    pct_bull = 100 * b / total if total else 0
    pct_bear = 100 * be / total if total else 0
    print(f'{sym:<12} {total:>6} {b:>6} ({pct_bull:>5.1f}%) {be:>6} ({pct_bear:>5.1f}%) {tr:>6} {ins:>6} {bug:>15} ({100*bug/total if total else 0:.1f}%)')

b = grand_counts.get('bullish', 0)
be = grand_counts.get('bearish', 0)
tr = grand_counts.get('transitional', 0)
ins = grand_counts.get('insufficient_data', 0)
pct_bull = 100 * b / grand_total if grand_total else 0
pct_bear = 100 * be / grand_total if grand_total else 0
print('-' * 80)
print(f'{"TOTAL":<12} {grand_total:>6} {b:>6} ({pct_bull:>5.1f}%) {be:>6} ({pct_bear:>5.1f}%) {tr:>6} {ins:>6} {grand_bug:>15} ({100*grand_bug/grand_total if grand_total else 0:.1f}%)')
