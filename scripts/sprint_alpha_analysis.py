#!/usr/bin/env python3
"""
Sprint Alpha — Three Critical Tests
1. Dumb Momentum Baseline: OB zone vs simple deep pullback
2. Per-Instrument Sub-Period Splits: is WR decay real or mix artifact?
3. DST Effect Analysis: BST vs GMT impact on London KZ trades
"""

import json
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent / "data" / "historical"
SCREENING_DIR = Path(__file__).parent.parent / "exports" / "multi_instrument" / "screening_results"
BATCH_DIR = Path(__file__).parent.parent / "knowledge_base_backtest" / "batch_api"
OUTPUT_DIR = (
    Path(__file__).parent.parent
    / "research"
    / "archive"
    / "root_legacy_artifacts_2026_05_31"
    / "generated"
    / "sprint_alpha"
)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 1: DUMB MOMENTUM BASELINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_atr(highs, lows, closes, period=14):
    n = len(highs)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = np.full(n, np.nan)
    if n > period:
        atr[period] = np.mean(tr[1:period+1])
        for i in range(period+1, n):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr


def detect_swings(highs, lows, min_bars=2):
    """Detect swing highs and lows."""
    n = len(highs)
    swing_highs = []  # (index, price)
    swing_lows = []
    for i in range(min_bars, n - min_bars):
        is_high = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, min_bars+1))
        is_low = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, min_bars+1))
        if is_high:
            swing_highs.append((i, highs[i]))
        if is_low:
            swing_lows.append((i, lows[i]))
    return swing_highs, swing_lows


def run_momentum_baseline(symbols=None):
    """
    For each H1 BOS event, compare:
    - OB retest continuation rate (price enters OB zone then continues)
    - Dumb baseline: any deep pullback (≥80%, 70%, 85%, 90%, 95% of impulse range) then continues

    Uses the same screening logic: swing detection → BOS → measure continuation.
    """
    if symbols is None:
        symbols = ['XAUUSD', 'GBPUSD', 'USDJPY', 'US30_cash', 'GBPJPY']

    WARMUP = 100
    MIN_DISP_ATR = 0.4
    BODY_RATIO_MIN = 0.40
    RETEST_WINDOW = 250
    CONT_WINDOW = 20
    TARGET_ATR_MULT = 1.25
    STOP_ATR_MULT = 0.5
    RETRACE_THRESHOLDS = [0.70, 0.80, 0.85, 0.90, 0.95]

    all_results = {}

    for symbol in symbols:
        fpath = DATA_DIR / f"{symbol}_H1.csv"
        if not fpath.exists():
            print(f"  {symbol}: no H1 data, skipping")
            continue

        df = pd.read_csv(fpath)
        opens = df['open'].values.astype(float)
        highs = df['high'].values.astype(float)
        lows = df['low'].values.astype(float)
        closes = df['close'].values.astype(float)
        n = len(df)
        atr = compute_atr(highs, lows, closes)

        # Detect swings
        swing_highs_list, swing_lows_list = detect_swings(highs, lows, min_bars=2)

        # Convert to indexed lookups
        sh_by_idx = {idx: price for idx, price in swing_highs_list}
        sl_by_idx = {idx: price for idx, price in swing_lows_list}

        # Track structure and detect BOS events
        # Simplified: track recent swing highs/lows, detect when close breaks them
        bos_events = []  # (bos_index, direction, impulse_high, impulse_low)

        recent_sh = []  # (index, price, consumed, classification)
        recent_sl = []
        structure = 'transitional'
        protected = None

        for idx, price in swing_highs_list:
            cls = 'HH' if (not recent_sh or price > recent_sh[-1][1]) else 'LH'
            recent_sh.append((idx, price, False, cls))
        for idx, price in swing_lows_list:
            cls = 'HL' if (not recent_sl or price > recent_sl[-1][1]) else 'LL'
            recent_sl.append((idx, price, False, cls))

        # Sort all swings by index for sequential processing
        all_swings = [(idx, price, 'high', cls) for idx, price, _, cls in recent_sh] + \
                     [(idx, price, 'low', cls) for idx, price, _, cls in recent_sl]
        all_swings.sort(key=lambda x: x[0])

        # Re-process sequentially to track structure properly
        sh_ordered = []
        sl_ordered = []
        consumed_swings = set()

        for sw_idx, sw_price, sw_type, sw_cls in all_swings:
            if sw_type == 'high':
                sh_ordered.append((sw_idx, sw_price))
            else:
                sl_ordered.append((sw_idx, sw_price))

        # Now scan each candle for BOS
        sh_ptr = 0
        sl_ptr = 0
        active_sh = []  # recent unconsumed swing highs
        active_sl = []

        for i in range(WARMUP, n):
            if np.isnan(atr[i]) or atr[i] == 0:
                continue

            # Add any swings that were confirmed by now
            while sh_ptr < len(sh_ordered) and sh_ordered[sh_ptr][0] < i:
                active_sh.append(sh_ordered[sh_ptr])
                sh_ptr += 1
            while sl_ptr < len(sl_ordered) and sl_ordered[sl_ptr][0] < i:
                active_sl.append(sl_ordered[sl_ptr])
                sl_ptr += 1

            # Check BOS: close breaks above highest recent unconsumed swing high
            if active_sh:
                last_sh_idx, last_sh_price = active_sh[-1]
                if last_sh_idx not in consumed_swings and closes[i] > last_sh_price:
                    # Bullish BOS
                    displacement = abs(closes[i] - last_sh_price)
                    disp_atr = displacement / atr[i]
                    # Compute body ratio for displacement leg
                    leg_start = max(last_sh_idx, i - 10)
                    body_sum = sum(abs(closes[k] - opens[k]) for k in range(leg_start, i+1))
                    range_sum = sum(highs[k] - lows[k] for k in range(leg_start, i+1))
                    body_ratio = body_sum / range_sum if range_sum > 0 else 0

                    if disp_atr >= MIN_DISP_ATR and body_ratio >= BODY_RATIO_MIN:
                        # Find the impulse range (from recent swing low to BOS candle high)
                        # The impulse is the move that created the BOS
                        impulse_low = min(lows[k] for k in range(max(0, last_sh_idx - 5), i+1))
                        impulse_high = highs[i]

                        # Find OB zone: last bearish candle before BOS
                        ob_high, ob_low = None, None
                        for k in range(i-1, max(i-11, 0), -1):
                            if closes[k] < opens[k]:  # bearish candle
                                ob_high = highs[k]
                                ob_low = lows[k]
                                break

                        bos_events.append({
                            'index': i,
                            'direction': 'bullish',
                            'impulse_high': impulse_high,
                            'impulse_low': impulse_low,
                            'ob_high': ob_high,
                            'ob_low': ob_low,
                            'atr': atr[i]
                        })
                    consumed_swings.add(last_sh_idx)

            if active_sl:
                last_sl_idx, last_sl_price = active_sl[-1]
                if last_sl_idx not in consumed_swings and closes[i] < last_sl_price:
                    # Bearish BOS
                    displacement = abs(closes[i] - last_sl_price)
                    disp_atr = displacement / atr[i]
                    leg_start = max(last_sl_idx, i - 10)
                    body_sum = sum(abs(closes[k] - opens[k]) for k in range(leg_start, i+1))
                    range_sum = sum(highs[k] - lows[k] for k in range(leg_start, i+1))
                    body_ratio = body_sum / range_sum if range_sum > 0 else 0

                    if disp_atr >= MIN_DISP_ATR and body_ratio >= BODY_RATIO_MIN:
                        impulse_high = max(highs[k] for k in range(max(0, last_sl_idx - 5), i+1))
                        impulse_low = lows[i]

                        ob_high, ob_low = None, None
                        for k in range(i-1, max(i-11, 0), -1):
                            if closes[k] > opens[k]:  # bullish candle
                                ob_high = highs[k]
                                ob_low = lows[k]
                                break

                        bos_events.append({
                            'index': i,
                            'direction': 'bearish',
                            'impulse_high': impulse_high,
                            'impulse_low': impulse_low,
                            'ob_high': ob_high,
                            'ob_low': ob_low,
                            'atr': atr[i]
                        })
                    consumed_swings.add(last_sl_idx)

        print(f"  {symbol}: {len(bos_events)} qualified BOS events detected")

        # Now for each BOS event, check retests at various thresholds
        ob_retest_cont = {'yes': 0, 'no': 0, 'no_retest': 0}
        threshold_results = {t: {'yes': 0, 'no': 0, 'no_retest': 0} for t in RETRACE_THRESHOLDS}

        for ev in bos_events:
            bi = ev['index']
            d = ev['direction']
            imp_hi = ev['impulse_high']
            imp_lo = ev['impulse_low']
            imp_range = imp_hi - imp_lo
            ob_hi = ev['ob_high']
            ob_lo = ev['ob_low']
            ev_atr = ev['atr']

            if imp_range <= 0:
                continue

            end_window = min(bi + 1 + RETEST_WINDOW, n)

            # OB retest check
            ob_retested = False
            ob_retest_idx = None
            if ob_hi is not None and ob_lo is not None:
                for j in range(bi + 1, end_window):
                    if d == 'bullish' and lows[j] <= ob_hi:
                        ob_retested = True
                        ob_retest_idx = j
                        break
                    elif d == 'bearish' and highs[j] >= ob_lo:
                        ob_retested = True
                        ob_retest_idx = j
                        break

            if ob_retested and ob_retest_idx is not None:
                # Check continuation from OB retest
                cont = check_continuation(highs, lows, closes, ob_retest_idx, d, ev_atr,
                                         TARGET_ATR_MULT, STOP_ATR_MULT, CONT_WINDOW, n)
                if cont:
                    ob_retest_cont['yes'] += 1
                else:
                    ob_retest_cont['no'] += 1
            else:
                ob_retest_cont['no_retest'] += 1

            # Threshold-based retest checks
            for thresh in RETRACE_THRESHOLDS:
                if d == 'bullish':
                    retrace_level = imp_hi - thresh * imp_range  # price must come down to this level
                else:
                    retrace_level = imp_lo + thresh * imp_range  # price must come up to this level

                retested = False
                retest_idx = None
                for j in range(bi + 1, end_window):
                    if d == 'bullish' and lows[j] <= retrace_level:
                        retested = True
                        retest_idx = j
                        break
                    elif d == 'bearish' and highs[j] >= retrace_level:
                        retested = True
                        retest_idx = j
                        break

                if retested and retest_idx is not None:
                    cont = check_continuation(highs, lows, closes, retest_idx, d, ev_atr,
                                             TARGET_ATR_MULT, STOP_ATR_MULT, CONT_WINDOW, n)
                    if cont:
                        threshold_results[thresh]['yes'] += 1
                    else:
                        threshold_results[thresh]['no'] += 1
                else:
                    threshold_results[thresh]['no_retest'] += 1

        all_results[symbol] = {
            'total_bos': len(bos_events),
            'ob_retest': ob_retest_cont,
            'thresholds': threshold_results
        }

    return all_results


def check_continuation(highs, lows, closes, retest_idx, direction, atr_val,
                       target_mult, stop_mult, window, n):
    """Check if price continues in direction after retest."""
    entry = closes[retest_idx]
    target_dist = target_mult * atr_val
    stop_dist = stop_mult * atr_val

    end = min(retest_idx + 1 + window, n)
    for j in range(retest_idx + 1, end):
        if direction == 'bullish':
            if highs[j] >= entry + target_dist:
                return True
            if lows[j] <= entry - stop_dist:
                return False
        else:
            if lows[j] <= entry - target_dist:
                return True
            if highs[j] >= entry + stop_dist:
                return False
    return False


def format_task1_results(results):
    lines = []
    lines.append("# Task 1: Dumb Momentum Baseline Results\n")
    lines.append("## Question")
    lines.append("Does the OB zone identification add value over simple deep pullback after BOS?\n")
    lines.append("## Method")
    lines.append("For each qualified H1 BOS event (displacement ≥ 0.4 ATR, body ratio ≥ 40%):")
    lines.append("- **OB retest**: Enter when price touches the identified OB zone")
    lines.append("- **Dumb baseline**: Enter when price retraces ≥X% of the impulse range (no OB identification)")
    lines.append("- **Same continuation logic**: 1.25 ATR target, 0.5 ATR stop, 20-candle window")
    lines.append("- **Retest window**: 250 H1 candles (~10 trading days)\n")

    lines.append("## Raw Results\n")

    # Per-instrument tables
    pooled_ob = {'yes': 0, 'no': 0, 'no_retest': 0}
    pooled_thresh = {t: {'yes': 0, 'no': 0, 'no_retest': 0} for t in [0.70, 0.80, 0.85, 0.90, 0.95]}

    for sym, r in results.items():
        lines.append(f"### {sym} ({r['total_bos']} BOS events)\n")

        ob = r['ob_retest']
        ob_total = ob['yes'] + ob['no']
        ob_rate = ob['yes'] / ob_total * 100 if ob_total > 0 else 0
        pooled_ob['yes'] += ob['yes']
        pooled_ob['no'] += ob['no']
        pooled_ob['no_retest'] += ob['no_retest']

        lines.append(f"| Entry Method | Retested | Continued | Rate |")
        lines.append(f"|---|---|---|---|")
        lines.append(f"| **OB Zone** | {ob_total} | {ob['yes']} | **{ob_rate:.1f}%** |")

        for t in [0.70, 0.80, 0.85, 0.90, 0.95]:
            tr = r['thresholds'][t]
            total = tr['yes'] + tr['no']
            rate = tr['yes'] / total * 100 if total > 0 else 0
            lines.append(f"| {int(t*100)}% Retrace | {total} | {tr['yes']} | {rate:.1f}% |")
            pooled_thresh[t]['yes'] += tr['yes']
            pooled_thresh[t]['no'] += tr['no']
            pooled_thresh[t]['no_retest'] += tr['no_retest']

        lines.append("")

    # Pooled summary
    lines.append("## POOLED SUMMARY (All Instruments)\n")
    lines.append("| Entry Method | Retested | Continued | Rate | Delta vs OB |")
    lines.append("|---|---|---|---|---|")

    ob_total_p = pooled_ob['yes'] + pooled_ob['no']
    ob_rate_p = pooled_ob['yes'] / ob_total_p * 100 if ob_total_p > 0 else 0
    lines.append(f"| **OB Zone** | {ob_total_p} | {pooled_ob['yes']} | **{ob_rate_p:.1f}%** | — |")

    for t in [0.70, 0.80, 0.85, 0.90, 0.95]:
        tr = pooled_thresh[t]
        total = tr['yes'] + tr['no']
        rate = tr['yes'] / total * 100 if total > 0 else 0
        delta = ob_rate_p - rate
        lines.append(f"| {int(t*100)}% Retrace | {total} | {tr['yes']} | {rate:.1f}% | {delta:+.1f}pp |")

    # Interpretation
    lines.append("\n## Interpretation\n")

    # Best dumb baseline
    best_t = max(pooled_thresh.keys(), key=lambda t: pooled_thresh[t]['yes'] / max(pooled_thresh[t]['yes'] + pooled_thresh[t]['no'], 1))
    best_total = pooled_thresh[best_t]['yes'] + pooled_thresh[best_t]['no']
    best_rate = pooled_thresh[best_t]['yes'] / best_total * 100 if best_total > 0 else 0

    delta = ob_rate_p - best_rate
    if best_rate >= 65:
        verdict = "OB zone adds LITTLE value. The edge is primarily momentum/trend-following."
    elif best_rate >= 55:
        verdict = "OB zone adds MODERATE value. Some alpha from zone identification."
    else:
        verdict = "OB zone adds SIGNIFICANT value. Zone identification matters."

    lines.append(f"- **Best dumb baseline**: {int(best_t*100)}% retrace at {best_rate:.1f}%")
    lines.append(f"- **OB zone rate**: {ob_rate_p:.1f}%")
    lines.append(f"- **OB advantage**: {delta:+.1f}pp over best dumb baseline")
    lines.append(f"- **Verdict**: {verdict}")

    # Statistical test
    if ob_total_p > 0 and best_total > 0:
        table = [[pooled_ob['yes'], pooled_ob['no']],
                 [pooled_thresh[best_t]['yes'], pooled_thresh[best_t]['no']]]
        odds, p = stats.fisher_exact(table)
        lines.append(f"- **Fisher's exact p-value**: {p:.4f} (OB vs {int(best_t*100)}% retrace)")

    lines.append("\n## So What?\n")
    lines.append("If the dumb baseline matches or beats OB continuation:")
    lines.append("- The \"edge\" is structural momentum, not zone precision")
    lines.append("- AI evaluation still adds value through filtering (timing, context)")
    lines.append("- But the OB zone identification step itself may be unnecessary complexity")
    lines.append("- A simpler system (BOS → deep pullback → enter) could work comparably")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 2: PER-INSTRUMENT SUB-PERIOD SPLITS
# ═══════════════════════════════════════════════════════════════════════════════

def load_all_batch_trades():
    """Load all batch results, tagged by instrument."""
    # Map batch IDs to instruments (from full_prompts inspection)
    batch_instrument_map = {
        'msgbatch_016WB5a5VNzuK7ibgz6uSD93': 'NZDUSD',
        'msgbatch_018GNt2yH8hrrj1BV3Mf35Q7': 'XAUUSD',
        'msgbatch_0195ug8PMEQvUM2pgrZGdkbB': 'XAUUSD',
        'msgbatch_01AmGJjMMtgW5XoGLkTqPEHd': 'US30',
        'msgbatch_01BNRwLoPRLjDs8XyAXx25XU': 'XAUUSD',
        'msgbatch_01CnqZUhMLs9JHq9dHC3x4pN': 'GBPJPY',
        'msgbatch_01GFcnn3BoVnxZs3TseQt4hD': 'GBPUSD',
        'msgbatch_01HJEdo4gP2s5nd9hrgtJUHK': 'XAUUSD',
        'msgbatch_01KqQJoECovg19XS3mRf7XSQ': 'XAUUSD',
        'msgbatch_01M9NW1bUnhF4Zf6g3VrNR8g': 'XAUUSD',
        'msgbatch_01NNvwcdiUQwUU9c2x7qbVjD': 'XAUUSD',
        'msgbatch_01NoUmtxUEP81v71PuNf7s7V': 'GBPUSD',
        'msgbatch_01PeezeEy1M3LiNHbKwfaj6o': 'XAUUSD',
        'msgbatch_01SHS6gVwY7J2bTXXdYjbiyi': 'GBPUSD',
        'msgbatch_01SwM5Tf4uFNFegC7sXHFGaX': 'GBPUSD',
        'msgbatch_01VCZZM7cCZhW9Nb9MybySZq': 'XAUUSD',
        'msgbatch_01WUZbzFQniomk49SoLRAsPg': 'XAUUSD',
        'msgbatch_01WXewYLHYVXzTeuJnq2vzHR': 'XAUUSD',
        'msgbatch_01WgP6eewwdQd8UgVemLH4cN': 'XAUUSD',
        'msgbatch_01XF1mnQ53GU8B6eTBBJLXzL': 'USDJPY',
    }

    all_trades = []
    for batch_id, instrument in batch_instrument_map.items():
        fpath = BATCH_DIR / f"{batch_id}_results.json"
        if not fpath.exists():
            continue
        with open(fpath) as f:
            data = json.load(f)
        if not isinstance(data, list):
            continue
        for day in data:
            if not isinstance(day, dict) or not day.get('trade_taken'):
                continue
            for trade in day.get('trades', []):
                if not isinstance(trade, dict):
                    continue
                all_trades.append({
                    'date': day['date'],
                    'instrument': instrument,
                    'outcome': trade.get('outcome', day.get('outcome')),
                    'r_multiple': trade.get('r_multiple', day.get('r_multiple')),
                    'kill_zone': trade.get('kill_zone', ''),
                    'direction': trade.get('direction', ''),
                    'entry_price': trade.get('entry_price', 0),
                })

    return pd.DataFrame(all_trades)


def run_subperiod_splits():
    """Compute per-instrument first-half vs second-half WR."""
    df = load_all_batch_trades()
    if df.empty:
        return "No trade data found."

    df['date'] = pd.to_datetime(df['date'])
    df['win'] = df['outcome'].str.upper().isin(['WIN', 'TP1', 'TP2', 'TP3'])

    results = {}
    instruments = df['instrument'].unique()

    for inst in sorted(instruments):
        idf = df[df['instrument'] == inst].sort_values('date').reset_index(drop=True)
        n = len(idf)
        if n < 6:
            results[inst] = {'n': n, 'note': 'too few trades'}
            continue

        mid = n // 2
        h1 = idf.iloc[:mid]
        h2 = idf.iloc[mid:]

        w1, n1 = h1['win'].sum(), len(h1)
        w2, n2 = h2['win'].sum(), len(h2)
        wr1 = w1 / n1 * 100
        wr2 = w2 / n2 * 100

        # Fisher's exact test
        table = [[w1, n1 - w1], [w2, n2 - w2]]
        _, p_val = stats.fisher_exact(table)

        results[inst] = {
            'n': n,
            'h1_dates': f"{h1['date'].iloc[0].strftime('%Y-%m-%d')} to {h1['date'].iloc[-1].strftime('%Y-%m-%d')}",
            'h2_dates': f"{h2['date'].iloc[0].strftime('%Y-%m-%d')} to {h2['date'].iloc[-1].strftime('%Y-%m-%d')}",
            'h1_wr': wr1, 'h1_w': int(w1), 'h1_n': n1,
            'h2_wr': wr2, 'h2_w': int(w2), 'h2_n': n2,
            'delta': wr2 - wr1,
            'p_value': p_val,
        }

    # Pooled
    all_h1_w, all_h1_n, all_h2_w, all_h2_n = 0, 0, 0, 0
    for inst in sorted(instruments):
        idf = df[df['instrument'] == inst].sort_values('date').reset_index(drop=True)
        n = len(idf)
        if n < 6:
            continue
        mid = n // 2
        h1 = idf.iloc[:mid]
        h2 = idf.iloc[mid:]
        all_h1_w += h1['win'].sum()
        all_h1_n += len(h1)
        all_h2_w += h2['win'].sum()
        all_h2_n += len(h2)

    if all_h1_n > 0 and all_h2_n > 0:
        pooled_wr1 = all_h1_w / all_h1_n * 100
        pooled_wr2 = all_h2_w / all_h2_n * 100
        _, pooled_p = stats.fisher_exact([[all_h1_w, all_h1_n - all_h1_w],
                                          [all_h2_w, all_h2_n - all_h2_w]])
        results['POOLED'] = {
            'n': all_h1_n + all_h2_n,
            'h1_wr': pooled_wr1, 'h1_w': int(all_h1_w), 'h1_n': all_h1_n,
            'h2_wr': pooled_wr2, 'h2_w': int(all_h2_w), 'h2_n': all_h2_n,
            'delta': pooled_wr2 - pooled_wr1,
            'p_value': pooled_p,
        }

    return results


def format_task2_results(results):
    lines = []
    lines.append("# Task 2: Per-Instrument Sub-Period Splits\n")
    lines.append("## Question")
    lines.append("Is the quarterly WR decline (73.2% → 59.4%) real decay or an instrument-mix artifact?\n")
    lines.append("## Method")
    lines.append("For each instrument separately, split trades into first-half and second-half by date.")
    lines.append("Compare WR within each instrument. Fisher's exact test for significance.\n")
    lines.append("## Results\n")

    lines.append("| Instrument | N | 1st Half WR | 2nd Half WR | Delta | p-value | Decay? |")
    lines.append("|---|---|---|---|---|---|---|")

    decay_count = 0
    real_count = 0

    for inst in sorted(results.keys()):
        r = results[inst]
        if 'note' in r:
            lines.append(f"| {inst} | {r['n']} | — | — | — | — | {r['note']} |")
            continue

        delta_str = f"{r['delta']:+.1f}pp"
        p_str = f"{r['p_value']:.3f}"

        if r['delta'] < -5:
            if r['p_value'] < 0.05:
                decay = "YES (sig.)"
                real_count += 1
            else:
                decay = "yes (n.s.)"
                decay_count += 1
        elif r['delta'] > 5:
            decay = "NO (improved)"
        else:
            decay = "stable"

        wr1_str = f"{r['h1_wr']:.1f}% ({r['h1_w']}/{r['h1_n']})"
        wr2_str = f"{r['h2_wr']:.1f}% ({r['h2_w']}/{r['h2_n']})"
        bold = "**" if inst == 'POOLED' else ""
        lines.append(f"| {bold}{inst}{bold} | {r['n']} | {wr1_str} | {wr2_str} | {delta_str} | {p_str} | {decay} |")

    lines.append("\n## Interpretation\n")

    # Check if decay is within-instrument or mix artifact
    xau = results.get('XAUUSD', {})
    pooled = results.get('POOLED', {})

    if xau and 'h1_wr' in xau:
        xau_decay = xau['delta']
        lines.append(f"- **XAUUSD decay**: {xau['h1_wr']:.1f}% → {xau['h2_wr']:.1f}% ({xau['delta']:+.1f}pp, p={xau['p_value']:.3f})")

    if pooled and 'h1_wr' in pooled:
        lines.append(f"- **Pooled decay**: {pooled['h1_wr']:.1f}% → {pooled['h2_wr']:.1f}% ({pooled['delta']:+.1f}pp, p={pooled['p_value']:.3f})")

    non_xau_decay = []
    for inst, r in results.items():
        if inst in ('XAUUSD', 'POOLED') or 'note' in r:
            continue
        non_xau_decay.append((inst, r['delta']))

    if non_xau_decay:
        avg_non_xau = np.mean([d for _, d in non_xau_decay])
        lines.append(f"- **Avg non-XAUUSD instrument decay**: {avg_non_xau:+.1f}pp")

    lines.append("\n## So What?\n")
    lines.append("If decay is consistent within XAUUSD alone → real performance decay, need to investigate regime change.")
    lines.append("If decay is only in pooled data → mix artifact from adding lower-WR instruments to second half.")
    lines.append("If decay is consistent across ALL instruments → systemic issue (prompt, market regime).")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK 3: DST EFFECT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def is_bst(date):
    """Check if a date falls in British Summer Time (last Sunday Mar → last Sunday Oct)."""
    year = date.year
    # Last Sunday in March
    mar31 = datetime(year, 3, 31)
    bst_start = mar31 - pd.Timedelta(days=(mar31.weekday() + 1) % 7)
    # Last Sunday in October
    oct31 = datetime(year, 10, 31)
    bst_end = oct31 - pd.Timedelta(days=(oct31.weekday() + 1) % 7)

    d = datetime(date.year, date.month, date.day)
    return bst_start <= d < bst_end


def run_dst_analysis():
    """Analyze BST vs GMT effect on London KZ trades."""
    df = load_all_batch_trades()
    if df.empty:
        return "No trade data found."

    df['date'] = pd.to_datetime(df['date'])
    df['win'] = df['outcome'].str.upper().isin(['WIN', 'TP1', 'TP2', 'TP3'])
    df['is_bst'] = df['date'].apply(is_bst)

    # Filter to London KZ trades only
    london = df[df['kill_zone'].str.lower().isin(['london', 'lon'])].copy()

    results = {}

    # Overall London KZ: BST vs GMT
    for period_name, mask in [('BST', london['is_bst']), ('GMT', ~london['is_bst'])]:
        sub = london[mask]
        if len(sub) == 0:
            results[f'london_{period_name}'] = {'n': 0}
            continue
        w = sub['win'].sum()
        n = len(sub)
        results[f'london_{period_name}'] = {'n': n, 'wins': int(w), 'wr': w/n*100}

    # All KZ combined: BST vs GMT
    for period_name, mask in [('BST', df['is_bst']), ('GMT', ~df['is_bst'])]:
        sub = df[mask]
        if len(sub) == 0:
            results[f'all_{period_name}'] = {'n': 0}
            continue
        w = sub['win'].sum()
        n = len(sub)
        results[f'all_{period_name}'] = {'n': n, 'wins': int(w), 'wr': w/n*100}

    # Per instrument × BST/GMT
    for inst in sorted(df['instrument'].unique()):
        idf = df[df['instrument'] == inst]
        for period_name, mask in [('BST', idf['is_bst']), ('GMT', ~idf['is_bst'])]:
            sub = idf[mask]
            if len(sub) < 3:
                results[f'{inst}_{period_name}'] = {'n': len(sub)}
                continue
            w = sub['win'].sum()
            n = len(sub)
            results[f'{inst}_{period_name}'] = {'n': n, 'wins': int(w), 'wr': w/n*100}

    # Fisher's test: London BST vs GMT
    lb = results.get('london_BST', {})
    lg = results.get('london_GMT', {})
    if lb.get('n', 0) >= 3 and lg.get('n', 0) >= 3:
        table = [[lb['wins'], lb['n'] - lb['wins']],
                 [lg['wins'], lg['n'] - lg['wins']]]
        _, p = stats.fisher_exact(table)
        results['london_fisher_p'] = p

    # Per KZ breakdown
    for kz in df['kill_zone'].unique():
        kdf = df[df['kill_zone'] == kz]
        for period_name, mask in [('BST', kdf['is_bst']), ('GMT', ~kdf['is_bst'])]:
            sub = kdf[mask]
            if len(sub) < 3:
                continue
            w = sub['win'].sum()
            n = len(sub)
            results[f'kz_{kz}_{period_name}'] = {'n': n, 'wins': int(w), 'wr': w/n*100}

    return results


def format_task3_results(results):
    lines = []
    lines.append("# Task 3: DST Effect Analysis\n")
    lines.append("## Question")
    lines.append("Is the late-London WR inflated by BST timing (captures post-LBMA Fix trading)?\n")
    lines.append("## Background")
    lines.append("- LBMA AM Fix: 10:30 London time (09:30 UTC during BST, 10:30 UTC during GMT)")
    lines.append("- London KZ: 07:00-10:30 UTC fixed")
    lines.append("- During BST: KZ captures 1 hour AFTER the Fix")
    lines.append("- During GMT: KZ boundary coincides with Fix itself\n")

    lines.append("## Results\n")

    # Overall BST vs GMT
    lines.append("### All Trades: BST vs GMT\n")
    lines.append("| Period | Trades | Wins | WR |")
    lines.append("|---|---|---|---|")
    for period in ['BST', 'GMT']:
        r = results.get(f'all_{period}', {})
        if r.get('n', 0) > 0:
            lines.append(f"| {period} | {r['n']} | {r['wins']} | {r['wr']:.1f}% |")
        else:
            lines.append(f"| {period} | 0 | — | — |")

    lines.append("\n### London KZ: BST vs GMT\n")
    lines.append("| Period | Trades | Wins | WR |")
    lines.append("|---|---|---|---|")
    for period in ['BST', 'GMT']:
        r = results.get(f'london_{period}', {})
        if r.get('n', 0) > 0:
            lines.append(f"| {period} | {r['n']} | {r['wins']} | {r['wr']:.1f}% |")
        else:
            lines.append(f"| {period} | 0 | — | — |")

    p = results.get('london_fisher_p')
    if p is not None:
        lines.append(f"\nFisher's exact p-value (London BST vs GMT): **{p:.4f}**")

    # Per-KZ breakdown
    lines.append("\n### Per Kill Zone: BST vs GMT\n")
    kzs = set()
    for k in results:
        if k.startswith('kz_'):
            parts = k.split('_')
            kz = parts[1]
            kzs.add(kz)

    if kzs:
        lines.append("| Kill Zone | BST Trades | BST WR | GMT Trades | GMT WR | Delta |")
        lines.append("|---|---|---|---|---|---|")
        for kz in sorted(kzs):
            bst_r = results.get(f'kz_{kz}_BST', {})
            gmt_r = results.get(f'kz_{kz}_GMT', {})
            bst_n = bst_r.get('n', 0)
            gmt_n = gmt_r.get('n', 0)
            bst_wr = f"{bst_r['wr']:.1f}%" if bst_n >= 3 else "—"
            gmt_wr = f"{gmt_r['wr']:.1f}%" if gmt_n >= 3 else "—"
            if bst_n >= 3 and gmt_n >= 3:
                delta = f"{bst_r['wr'] - gmt_r['wr']:+.1f}pp"
            else:
                delta = "—"
            lines.append(f"| {kz} | {bst_n} | {bst_wr} | {gmt_n} | {gmt_wr} | {delta} |")

    # Per instrument
    lines.append("\n### Per Instrument: BST vs GMT\n")
    instruments = set()
    for k in results:
        for inst in ['XAUUSD', 'GBPUSD', 'GBPJPY', 'USDJPY', 'US30', 'NZDUSD']:
            if k.startswith(f'{inst}_'):
                instruments.add(inst)

    if instruments:
        lines.append("| Instrument | BST Trades | BST WR | GMT Trades | GMT WR | Delta |")
        lines.append("|---|---|---|---|---|---|")
        for inst in sorted(instruments):
            bst_r = results.get(f'{inst}_BST', {})
            gmt_r = results.get(f'{inst}_GMT', {})
            bst_n = bst_r.get('n', 0)
            gmt_n = gmt_r.get('n', 0)
            bst_wr = f"{bst_r['wr']:.1f}%" if bst_n >= 3 else f"({bst_n} trades)"
            gmt_wr = f"{gmt_r['wr']:.1f}%" if gmt_n >= 3 else f"({gmt_n} trades)"
            if bst_n >= 3 and gmt_n >= 3:
                delta = f"{bst_r['wr'] - gmt_r['wr']:+.1f}pp"
            else:
                delta = "—"
            lines.append(f"| {inst} | {bst_n} | {bst_wr} | {gmt_n} | {gmt_wr} | {delta} |")

    lines.append("\n## Interpretation\n")

    lb = results.get('london_BST', {})
    lg = results.get('london_GMT', {})
    if lb.get('n', 0) >= 3 and lg.get('n', 0) >= 3:
        delta = lb['wr'] - lg['wr']
        if abs(delta) > 10:
            lines.append(f"- **Large BST/GMT gap ({delta:+.1f}pp)**: DST timing is a meaningful confound")
            lines.append(f"- The London KZ extension decision should account for this seasonal effect")
        elif abs(delta) > 5:
            lines.append(f"- **Moderate BST/GMT gap ({delta:+.1f}pp)**: Some DST effect but not dominant")
        else:
            lines.append(f"- **Small BST/GMT gap ({delta:+.1f}pp)**: DST timing is NOT a significant confound")
            lines.append(f"- London KZ performance is robust across both clock settings")

    lines.append("\n## So What?\n")
    lines.append("If BST London WR >> GMT London WR:")
    lines.append("- The late-London edge may be capturing post-Fix flow, not structural setups")
    lines.append("- Consider adjusting KZ boundaries seasonally or treating BST/GMT as separate regimes")
    lines.append("If BST ≈ GMT:")
    lines.append("- The Fix timing is not a confound — London KZ edge is robust year-round")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SPRINT ALPHA — THREE CRITICAL TESTS")
    print("=" * 70)

    # Task 1
    print("\n>>> TASK 1: Dumb Momentum Baseline")
    print("-" * 50)
    t1_results = run_momentum_baseline()
    t1_doc = format_task1_results(t1_results)
    with open(OUTPUT_DIR / "test_a_momentum_baseline_results.md", 'w') as f:
        f.write(t1_doc)
    print("  Saved to test_a_momentum_baseline_results.md")

    # Task 2
    print("\n>>> TASK 2: Per-Instrument Sub-Period Splits")
    print("-" * 50)
    t2_results = run_subperiod_splits()
    t2_doc = format_task2_results(t2_results)
    with open(OUTPUT_DIR / "per_instrument_subperiod_splits.md", 'w') as f:
        f.write(t2_doc)
    print("  Saved to per_instrument_subperiod_splits.md")

    # Task 3
    print("\n>>> TASK 3: DST Effect Analysis")
    print("-" * 50)
    t3_results = run_dst_analysis()
    t3_doc = format_task3_results(t3_results)
    with open(OUTPUT_DIR / "dst_effect_analysis.md", 'w') as f:
        f.write(t3_doc)
    print("  Saved to dst_effect_analysis.md")

    print("\n" + "=" * 70)
    print("ALL TASKS COMPLETE")
    print("=" * 70)
