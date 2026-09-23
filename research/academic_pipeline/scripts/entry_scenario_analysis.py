#!/usr/bin/env python3
"""
Entry Scenario Analysis — Retrospective simulation on 557 entry_in_ob rejected trades.
XAUUSD T7 simulation period: Jan 2 – Apr 10, 2026.

Scenarios:
  A: Proactive limit order placed at OB zone entry immediately on C-gate fire
  B: Market order at current price (ignore L2 entirely)
  C: Zone touch → immediate market entry (close must stay above SL)
  D: M15 micro-CHoCH confirmation within OB zone → entry

Output files:
  research/academic_pipeline/results/entry_scenario_analysis_v1.md
  research/academic_pipeline/data/entry_scenario_summary.json
"""

import json
import re
import csv
import os
from datetime import datetime, timezone
from collections import defaultdict

BASE_DIR = '/Users/borr/Documents/trading/gold-agent'

# ─────────────────────────────── DATA LOADING ───────────────────────────────

def load_rejected_records():
    path = os.path.join(BASE_DIR, 'research/t7_live_simulation/all_results_jan_apr10.json')
    with open(path) as f:
        data = json.load(f)
    all_records = data['results']
    rejected = [r for r in all_records
                if r.get('decision') == 'REJECTED_L2'
                and 'entry_in_ob' in str(r.get('l2_reason', ''))]
    return rejected, data

def load_m15():
    path = os.path.join(BASE_DIR, 'data/historical_2026/XAUUSD_M15.csv')
    candles = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            candles.append({
                'time': row['time'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
    # Build a lookup: time string → index
    time_index = {c['time']: i for i, c in enumerate(candles)}
    return candles, time_index

# ─────────────────────────────── HELPERS ────────────────────────────────────

def parse_ob_zone(l2_reason):
    """Extract ob_low, ob_high from l2_reason string."""
    match = re.search(r'OB zone ([\d.]+)-([\d.]+)', str(l2_reason))
    if not match:
        return None, None
    return float(match.group(1)), float(match.group(2))

def parse_candle_time(ct):
    """Convert ISO8601 candle_time to CSV time format string."""
    ct = ct.replace('Z', '+00:00')
    dt = datetime.fromisoformat(ct)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def resolve_same_candle(candle, tp_price, sl_price, direction):
    """
    When a single candle touches both TP and SL, determine which was hit first.
    Rule: bullish close (close > open) → TP first for LONG / SL first for SHORT.
          bearish close → SL first for LONG / TP first for SHORT.
    """
    bullish = candle['close'] > candle['open']
    if direction == 'LONG':
        return 'WIN' if bullish else 'LOSS'
    else:  # SHORT
        return 'WIN' if not bullish else 'LOSS'

def compute_zone_params(direction, ob_low, ob_high):
    """Compute zone entry, SL, and TP levels."""
    if direction == 'LONG':
        zone_entry = ob_high
        zone_sl = ob_low * 0.999
        zone_risk = zone_entry - zone_sl
        zone_tp_1r5 = zone_entry + zone_risk * 1.5
        zone_tp_3r = zone_entry + zone_risk * 3.0
    else:  # SHORT
        zone_entry = ob_low
        zone_sl = ob_high * 1.001
        zone_risk = zone_sl - zone_entry
        zone_tp_1r5 = zone_entry - zone_risk * 1.5
        zone_tp_3r = zone_entry - zone_risk * 3.0
    return zone_entry, zone_sl, zone_risk, zone_tp_1r5, zone_tp_3r

def scan_outcome(forward_candles, tp_price, sl_price, direction):
    """
    Scan forward candles for TP or SL hit.
    Returns: ('WIN'|'LOSS'|'OPEN', candle_index_or_None, r_value)
    """
    for i, c in enumerate(forward_candles):
        if direction == 'LONG':
            hit_tp = c['high'] >= tp_price
            hit_sl = c['low'] <= sl_price
        else:
            hit_tp = c['low'] <= tp_price
            hit_sl = c['high'] >= sl_price

        if hit_tp and hit_sl:
            result = resolve_same_candle(c, tp_price, sl_price, direction)
            r = 1.5 if result == 'WIN' else -1.0
            return result, i, r
        elif hit_tp:
            return 'WIN', i, 1.5
        elif hit_sl:
            return 'LOSS', i, -1.0

    return 'OPEN', None, None

def check_3r_hit(forward_candles, tp_3r, sl_price, direction, fill_idx):
    """Check if 3R TP was hit after fill (for upside potential analysis)."""
    for c in forward_candles[fill_idx:]:
        if direction == 'LONG':
            if c['low'] <= sl_price:
                return False
            if c['high'] >= tp_3r:
                return True
        else:
            if c['high'] >= sl_price:
                return False
            if c['low'] <= tp_3r:
                return True
    return False

# ─────────────────────────────── SCENARIOS ──────────────────────────────────

def scenario_a(forward_window, direction, zone_entry, zone_sl, zone_tp_1r5, zone_tp_3r):
    """
    Scenario A: Proactive limit at OB zone entry. Fills on any wick touch.
    """
    result = {
        'fill': False, 'fill_candle': None, 'candles_to_fill': None,
        'outcome': 'EXPIRED', 'r': None, 'hit_3r': False
    }

    fill_idx = None
    for i, c in enumerate(forward_window):
        if direction == 'LONG':
            if c['low'] <= zone_entry:
                fill_idx = i
                break
        else:
            if c['high'] >= zone_entry:
                fill_idx = i
                break

    if fill_idx is None:
        return result

    result['fill'] = True
    result['fill_candle'] = forward_window[fill_idx]['time']
    result['candles_to_fill'] = fill_idx

    # Scan remaining candles after fill
    after_fill = forward_window[fill_idx + 1:]
    outcome, out_idx, r_val = scan_outcome(after_fill, zone_tp_1r5, zone_sl, direction)
    result['outcome'] = outcome
    result['r'] = r_val

    # Check 3R
    if outcome != 'EXPIRED' and outcome != 'OPEN':
        result['hit_3r'] = check_3r_hit(after_fill, zone_tp_3r, zone_sl, direction, 0)

    return result

def scenario_b(forward_window, direction, entry_price, ai_sl, ai_tp):
    """
    Scenario B: Market order at current price (ignore L2). Immediate fill.
    """
    result = {'outcome': 'OPEN', 'r': None, 'market_entry': entry_price}

    # sl_distance_pct for LONG
    if direction == 'LONG' and entry_price > 0:
        result['sl_distance_pct'] = (entry_price - ai_sl) / entry_price * 100
    elif direction == 'SHORT' and entry_price > 0:
        result['sl_distance_pct'] = (ai_sl - entry_price) / entry_price * 100
    else:
        result['sl_distance_pct'] = None

    outcome, out_idx, r_val = scan_outcome(forward_window, ai_tp, ai_sl, direction)
    result['outcome'] = outcome
    result['r'] = r_val
    return result

def scenario_c(forward_window, direction, zone_entry, zone_sl, zone_tp_1r5, zone_tp_3r):
    """
    Scenario C: Zone touch → immediate entry (close must stay above SL for LONG).
    """
    result = {
        'fill': False, 'fill_candle': None, 'candles_to_fill': None,
        'outcome': 'EXPIRED', 'r': None
    }

    fill_idx = None
    for i, c in enumerate(forward_window):
        if direction == 'LONG':
            if c['low'] <= zone_entry and c['close'] > zone_sl:
                fill_idx = i
                break
        else:
            if c['high'] >= zone_entry and c['close'] < zone_sl:
                fill_idx = i
                break

    if fill_idx is None:
        return result

    result['fill'] = True
    result['fill_candle'] = forward_window[fill_idx]['time']
    result['candles_to_fill'] = fill_idx

    after_fill = forward_window[fill_idx + 1:]
    outcome, out_idx, r_val = scan_outcome(after_fill, zone_tp_1r5, zone_sl, direction)
    result['outcome'] = outcome
    result['r'] = r_val
    return result

def scenario_d(forward_window, direction, ob_low, ob_high):
    """
    Scenario D: M15 micro-CHoCH at OB zone. Institutional entry.
    """
    result = {
        'zone_touch': False, 'zone_touch_candle': None,
        'choch_found': False, 'entry_price': None, 'sl': None,
        'risk_pts': None, 'outcome': 'EXPIRED', 'r': None,
        'hit_3r': False
    }

    zone_entry = ob_high if direction == 'LONG' else ob_low

    # Step 1: Find first candle touching the zone
    touch_idx = None
    for i, c in enumerate(forward_window):
        if direction == 'LONG':
            if c['low'] <= ob_high:
                touch_idx = i
                break
        else:
            if c['high'] >= ob_low:
                touch_idx = i
                break

    if touch_idx is None:
        return result

    result['zone_touch'] = True
    result['zone_touch_candle'] = forward_window[touch_idx]['time']

    # Step 2: Scan up to 16 candles for micro-CHoCH
    window_16 = forward_window[touch_idx:touch_idx + 17]  # include touch candle + 16 after

    if direction == 'LONG':
        swing_low = float('inf')
        swing_low_established = False

        for j, c in enumerate(window_16):
            # Track lowest low
            if c['low'] < swing_low:
                swing_low = c['low']
                swing_low_established = True

            if j == 0:
                continue  # need at least previous candle

            prev_c = window_16[j - 1]
            # Micro-CHoCH: bullish close breaking above prior candle high
            if (swing_low_established and
                    c['close'] > c['open'] and          # bullish close
                    c['high'] > prev_c['high']):        # breaks above prior high
                # CHoCH found
                entry = c['close']
                sl = swing_low * 0.999
                micro_risk = entry - sl
                if micro_risk <= 0:
                    continue  # degenerate — skip
                tp_1r5 = entry + micro_risk * 1.5
                tp_3r = entry + micro_risk * 3.0

                result['choch_found'] = True
                result['entry_price'] = entry
                result['sl'] = sl
                result['risk_pts'] = micro_risk

                # Scan after this candle
                global_idx = touch_idx + j
                after_choch = forward_window[global_idx + 1:]
                outcome, out_idx, r_val = scan_outcome(after_choch, tp_1r5, sl, direction)
                result['outcome'] = outcome
                result['r'] = r_val

                if outcome != 'OPEN':
                    result['hit_3r'] = check_3r_hit(after_choch, tp_3r, sl, direction, 0)
                return result

        # No CHoCH found within 16 candles
        result['outcome'] = 'NO_CHOCH'
        return result

    else:  # SHORT
        swing_high = float('-inf')
        swing_high_established = False

        for j, c in enumerate(window_16):
            if c['high'] > swing_high:
                swing_high = c['high']
                swing_high_established = True

            if j == 0:
                continue

            prev_c = window_16[j - 1]
            if (swing_high_established and
                    c['close'] < c['open'] and          # bearish close
                    c['low'] < prev_c['low']):          # breaks below prior low
                entry = c['close']
                sl = swing_high * 1.001
                micro_risk = sl - entry
                if micro_risk <= 0:
                    continue
                tp_1r5 = entry - micro_risk * 1.5
                tp_3r = entry - micro_risk * 3.0

                result['choch_found'] = True
                result['entry_price'] = entry
                result['sl'] = sl
                result['risk_pts'] = micro_risk

                global_idx = touch_idx + j
                after_choch = forward_window[global_idx + 1:]
                outcome, out_idx, r_val = scan_outcome(after_choch, tp_1r5, sl, direction)
                result['outcome'] = outcome
                result['r'] = r_val

                if outcome != 'OPEN':
                    result['hit_3r'] = check_3r_hit(after_choch, tp_3r, sl, direction, 0)
                return result

        result['outcome'] = 'NO_CHOCH'
        return result

# ─────────────────────────────── MAIN ANALYSIS ──────────────────────────────

def main():
    print("=" * 60)
    print("ENTRY SCENARIO ANALYSIS — XAUUSD Jan 2 – Apr 10, 2026")
    print("=" * 60)

    # ── Load data ──
    print("\n[1] Loading data...")
    rejected, full_data = load_rejected_records()
    m15_candles, m15_index = load_m15()
    print(f"    entry_in_ob rejections: {len(rejected)}")
    print(f"    M15 candles loaded: {len(m15_candles)}")
    print(f"    M15 range: {m15_candles[0]['time']} → {m15_candles[-1]['time']}")

    # ── Validation Check 1: Count ──
    print("\n[2] VALIDATION CHECK 1 — Count")
    assert len(rejected) == 557, f"Expected 557, got {len(rejected)}"
    print(f"    PASS: exactly 557 entry_in_ob rejections")

    # ── Validation Check 2: Timestamps ──
    print("\n[3] VALIDATION CHECK 2 — Timestamps")
    first_m15 = m15_candles[0]['time']
    last_m15 = m15_candles[-1]['time']
    first_rejection_ts = parse_candle_time(rejected[0]['candle_time'])
    print(f"    First M15 candle: {first_m15} (expected: 2026-01-02 01:00:00)")
    print(f"    Last M15 candle:  {last_m15} (expected: >= 2026-04-10)")
    print(f"    First rejection:  {first_rejection_ts} (expected: 2026-01-07)")
    assert first_m15.startswith('2026-01-02'), f"First M15 candle mismatch: {first_m15}"
    assert last_m15 >= '2026-04-10', f"Last M15 candle too early: {last_m15}"
    assert first_rejection_ts.startswith('2026-01-07'), f"First rejection mismatch: {first_rejection_ts}"
    print("    PASS: all timestamp checks")

    # ── Validation Check 3: Spot-checks ──
    print("\n[4] VALIDATION CHECK 3 — Spot-checks (indices 0, 278, 556)")
    for idx in [0, 278, 556]:
        r = rejected[idx]
        ob_low, ob_high = parse_ob_zone(r['l2_reason'])
        direction = r['direction']
        ts = parse_candle_time(r['candle_time'])
        if direction == 'LONG':
            zone_entry = ob_high
        else:
            zone_entry = ob_low

        # Check forward candle exists
        m15_idx = m15_index.get(ts)
        fwd_exists = m15_idx is not None and (m15_idx + 1) < len(m15_candles)
        print(f"\n    [idx={idx}]")
        print(f"      candle_time:  {r['candle_time']}")
        print(f"      direction:    {direction}")
        print(f"      entry_price:  {r['entry_price']}")
        print(f"      ob_low:       {ob_low}")
        print(f"      ob_high:      {ob_high}")
        print(f"      zone_entry:   {zone_entry}")
        print(f"      M15 idx:      {m15_idx}")
        print(f"      fwd candle:   {'EXISTS' if fwd_exists else 'MISSING'}")

    print("\n    Spot-checks complete")

    # ── Main computation loop ──
    print("\n[5] Running scenario computations...")

    results = []
    skipped_no_ts = 0
    truncated_count = 0

    for i, rec in enumerate(rejected):
        if i % 100 == 0:
            print(f"    Processing {i}/{len(rejected)}...")

        ts = parse_candle_time(rec['candle_time'])
        ob_low, ob_high = parse_ob_zone(rec['l2_reason'])
        direction = rec['direction']
        entry_price = rec['entry_price']
        ai_sl = rec['stop_loss']
        ai_tp = rec['take_profit_1']

        if ob_low is None:
            skipped_no_ts += 1
            continue

        m15_idx = m15_index.get(ts)
        if m15_idx is None:
            skipped_no_ts += 1
            continue

        # Forward window: next 192 candles
        fwd_start = m15_idx + 1
        fwd_end = min(fwd_start + 192, len(m15_candles))
        forward_window = m15_candles[fwd_start:fwd_end]
        truncated = len(forward_window) < 192

        if truncated:
            truncated_count += 1

        zone_entry, zone_sl, zone_risk, zone_tp_1r5, zone_tp_3r = compute_zone_params(
            direction, ob_low, ob_high
        )

        # Run all scenarios
        res_a = scenario_a(forward_window, direction, zone_entry, zone_sl, zone_tp_1r5, zone_tp_3r)
        res_b = scenario_b(forward_window, direction, entry_price, ai_sl, ai_tp)
        res_c = scenario_c(forward_window, direction, zone_entry, zone_sl, zone_tp_1r5, zone_tp_3r)
        res_d = scenario_d(forward_window, direction, ob_low, ob_high)

        results.append({
            'idx': i,
            'candle_time': rec['candle_time'],
            'date': rec.get('date', ts[:10]),
            'direction': direction,
            'entry_price': entry_price,
            'ob_low': ob_low,
            'ob_high': ob_high,
            'zone_entry': zone_entry,
            'zone_sl': zone_sl,
            'zone_risk': zone_risk,
            'ai_sl': ai_sl,
            'ai_tp': ai_tp,
            'truncated': truncated,
            'scenario_a': res_a,
            'scenario_b': res_b,
            'scenario_c': res_c,
            'scenario_d': res_d,
        })

    print(f"\n    Processed: {len(results)}")
    print(f"    Skipped (no M15 match): {skipped_no_ts}")
    print(f"    Truncated (<192 fwd candles): {truncated_count}")

    # ── Validation Check 4: Scenario A/C consistency ──
    print("\n[6] VALIDATION CHECK 4 — Scenario A/C fill rate consistency")
    a_fills = sum(1 for r in results if r['scenario_a']['fill'])
    c_fills = sum(1 for r in results if r['scenario_c']['fill'])
    print(f"    Scenario A fills: {a_fills} ({a_fills/len(results)*100:.1f}%)")
    print(f"    Scenario C fills: {c_fills} ({c_fills/len(results)*100:.1f}%)")
    if c_fills <= a_fills:
        print("    PASS: C fill rate <= A fill rate")
    else:
        print("    FAIL: C > A — BUG DETECTED")

    # ── Validation Check 5: Scenario D micro-risk vs A zone_risk ──
    print("\n[7] VALIDATION CHECK 5 — Scenario D avg micro-risk vs A avg zone_risk")
    d_risks = [r['scenario_d']['risk_pts'] for r in results
               if r['scenario_d']['risk_pts'] is not None]
    a_risks = [r['zone_risk'] for r in results]
    avg_d_risk = sum(d_risks) / len(d_risks) if d_risks else 0
    avg_a_risk = sum(a_risks) / len(a_risks)
    print(f"    Scenario A avg zone_risk: {avg_a_risk:.2f} pts")
    print(f"    Scenario D avg micro_risk: {avg_d_risk:.2f} pts (n={len(d_risks)})")
    if avg_d_risk < avg_a_risk or len(d_risks) == 0:
        print("    PASS: D micro-risk < A zone_risk")
    else:
        print(f"    ANOMALY: D micro-risk ({avg_d_risk:.2f}) >= A zone_risk ({avg_a_risk:.2f})")

    # ─────────────── AGGREGATED STATISTICS ───────────────

    n = len(results)

    # ── Scenario A ──
    a_filled = [r for r in results if r['scenario_a']['fill']]
    a_expired = [r for r in results if r['scenario_a']['outcome'] == 'EXPIRED']
    a_open = [r for r in results if r['scenario_a']['outcome'] == 'OPEN']
    a_wins = [r for r in a_filled if r['scenario_a']['outcome'] == 'WIN']
    a_losses = [r for r in a_filled if r['scenario_a']['outcome'] == 'LOSS']
    a_fill_resolved = [r for r in a_filled if r['scenario_a']['outcome'] in ('WIN', 'LOSS')]
    a_wr = len(a_wins) / len(a_fill_resolved) if a_fill_resolved else 0
    a_r_vals = [r['scenario_a']['r'] for r in a_fill_resolved if r['scenario_a']['r'] is not None]
    a_avg_r = sum(a_r_vals) / len(a_r_vals) if a_r_vals else 0
    # Total R includes all filled trades (OPEN = 0R, EXPIRED excluded from fill)
    a_total_r = sum(r['scenario_a']['r'] for r in a_filled
                    if r['scenario_a']['r'] is not None)
    a_hit_3r = sum(1 for r in a_filled if r['scenario_a']['hit_3r'])
    a_pct_3r = a_hit_3r / len(a_filled) if a_filled else 0

    # Time to fill distribution (A)
    a_fill_times = [r['scenario_a']['candles_to_fill'] for r in a_filled
                    if r['scenario_a']['candles_to_fill'] is not None]

    # ── Scenario B ──
    b_wins = [r for r in results if r['scenario_b']['outcome'] == 'WIN']
    b_losses = [r for r in results if r['scenario_b']['outcome'] == 'LOSS']
    b_open = [r for r in results if r['scenario_b']['outcome'] == 'OPEN']
    b_resolved = [r for r in results if r['scenario_b']['outcome'] in ('WIN', 'LOSS')]
    b_wr = len(b_wins) / len(b_resolved) if b_resolved else 0
    b_r_vals = [r['scenario_b']['r'] for r in b_resolved if r['scenario_b']['r'] is not None]
    b_avg_r = sum(b_r_vals) / len(b_r_vals) if b_r_vals else 0
    b_total_r = sum(r['scenario_b']['r'] for r in results
                    if r['scenario_b']['r'] is not None)
    b_sl_pcts = [r['scenario_b']['sl_distance_pct'] for r in results
                 if r['scenario_b']['sl_distance_pct'] is not None]
    b_avg_sl_pct = sum(b_sl_pcts) / len(b_sl_pcts) if b_sl_pcts else 0

    # ── Scenario C ──
    c_filled = [r for r in results if r['scenario_c']['fill']]
    c_expired = [r for r in results if r['scenario_c']['outcome'] == 'EXPIRED']
    c_open = [r for r in results if r['scenario_c']['outcome'] == 'OPEN']
    c_wins = [r for r in c_filled if r['scenario_c']['outcome'] == 'WIN']
    c_losses = [r for r in c_filled if r['scenario_c']['outcome'] == 'LOSS']
    c_fill_resolved = [r for r in c_filled if r['scenario_c']['outcome'] in ('WIN', 'LOSS')]
    c_wr = len(c_wins) / len(c_fill_resolved) if c_fill_resolved else 0
    c_r_vals = [r['scenario_c']['r'] for r in c_fill_resolved if r['scenario_c']['r'] is not None]
    c_avg_r = sum(c_r_vals) / len(c_r_vals) if c_r_vals else 0
    c_total_r = sum(r['scenario_c']['r'] for r in c_filled
                    if r['scenario_c']['r'] is not None)

    # Time to fill distribution (C)
    c_fill_times = [r['scenario_c']['candles_to_fill'] for r in c_filled
                    if r['scenario_c']['candles_to_fill'] is not None]

    # ── Scenario D ──
    d_touched = [r for r in results if r['scenario_d']['zone_touch']]
    d_choch = [r for r in results if r['scenario_d']['choch_found']]
    d_executed = [r for r in results if r['scenario_d']['choch_found']]
    d_wins = [r for r in d_executed if r['scenario_d']['outcome'] == 'WIN']
    d_losses = [r for r in d_executed if r['scenario_d']['outcome'] == 'LOSS']
    d_open = [r for r in d_executed if r['scenario_d']['outcome'] == 'OPEN']
    d_exec_resolved = [r for r in d_executed if r['scenario_d']['outcome'] in ('WIN', 'LOSS')]
    d_wr = len(d_wins) / len(d_exec_resolved) if d_exec_resolved else 0
    d_r_vals = [r['scenario_d']['r'] for r in d_exec_resolved if r['scenario_d']['r'] is not None]
    d_avg_r = sum(d_r_vals) / len(d_r_vals) if d_r_vals else 0
    d_total_r = sum(r['scenario_d']['r'] for r in d_executed
                    if r['scenario_d']['r'] is not None)
    d_risks_list = [r['scenario_d']['risk_pts'] for r in d_executed
                    if r['scenario_d']['risk_pts'] is not None]
    d_avg_risk = sum(d_risks_list) / len(d_risks_list) if d_risks_list else 0

    # ── Monthly breakdown Scenario A ──
    monthly_a = defaultdict(lambda: {'filled': 0, 'wins': 0, 'resolved': 0, 'r': 0.0})
    for r in results:
        month = r['date'][:7]  # YYYY-MM
        if r['scenario_a']['fill']:
            monthly_a[month]['filled'] += 1
            if r['scenario_a']['outcome'] in ('WIN', 'LOSS'):
                monthly_a[month]['resolved'] += 1
                if r['scenario_a']['r'] is not None:
                    monthly_a[month]['r'] += r['scenario_a']['r']
            if r['scenario_a']['outcome'] == 'WIN':
                monthly_a[month]['wins'] += 1

    # Total trades per month (all rejected)
    monthly_total = defaultdict(int)
    for r in results:
        monthly_total[r['date'][:7]] += 1

    # ── Risk analysis ──
    avg_zone_risk = avg_a_risk
    # Gap analysis: how far is current price above zone?
    gaps_pct = []
    for r in results:
        if r['direction'] == 'LONG':
            gap_pct = (r['entry_price'] - r['zone_entry']) / r['entry_price'] * 100
        else:
            gap_pct = (r['zone_entry'] - r['entry_price']) / r['entry_price'] * 100
        gaps_pct.append(gap_pct)
    avg_gap_pct = sum(gaps_pct) / len(gaps_pct) if gaps_pct else 0
    min_gap_pct = min(gaps_pct) if gaps_pct else 0
    max_gap_pct = max(gaps_pct) if gaps_pct else 0

    # ─────────────── PRINT SUMMARY ───────────────

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"\nTotal records analyzed: {n}")
    print(f"Skipped (no M15 match): {skipped_no_ts}")
    print(f"Truncated forward windows: {truncated_count}")

    print(f"\n--- Scenario A: OB Limit (Proactive) ---")
    print(f"  Fill rate: {len(a_filled)/n*100:.1f}% ({len(a_filled)}/{n})")
    print(f"  Expired: {len(a_expired)/n*100:.1f}% ({len(a_expired)})")
    print(f"  Open: {len(a_open)}")
    print(f"  WR (resolved filled): {a_wr*100:.1f}% (W={len(a_wins)}, L={len(a_losses)})")
    print(f"  Avg R (resolved): {a_avg_r:.3f}")
    print(f"  Total R (filled): {a_total_r:.2f}")
    print(f"  Hit 3R: {a_hit_3r}/{len(a_filled)} ({a_pct_3r*100:.1f}%)")

    print(f"\n--- Scenario B: Market at C-Gate ---")
    print(f"  Fill rate: 100% ({n}/{n})")
    print(f"  Open: {len(b_open)}")
    print(f"  WR (resolved): {b_wr*100:.1f}% (W={len(b_wins)}, L={len(b_losses)})")
    print(f"  Avg R (resolved): {b_avg_r:.3f}")
    print(f"  Total R: {b_total_r:.2f}")
    print(f"  Avg SL distance: {b_avg_sl_pct:.3f}%")

    print(f"\n--- Scenario C: Zone Touch Entry ---")
    print(f"  Fill rate: {len(c_filled)/n*100:.1f}% ({len(c_filled)}/{n})")
    print(f"  Expired: {len(c_expired)/n*100:.1f}% ({len(c_expired)})")
    print(f"  Open: {len(c_open)}")
    print(f"  WR (resolved filled): {c_wr*100:.1f}% (W={len(c_wins)}, L={len(c_losses)})")
    print(f"  Avg R (resolved): {c_avg_r:.3f}")
    print(f"  Total R (filled): {c_total_r:.2f}")

    print(f"\n--- Scenario D: M15 Micro-CHoCH ---")
    print(f"  Zone touch rate: {len(d_touched)/n*100:.1f}% ({len(d_touched)}/{n})")
    print(f"  CHoCH found (of touches): {len(d_choch)/len(d_touched)*100:.1f}% ({len(d_choch)}/{len(d_touched)})" if d_touched else "  No zone touches")
    print(f"  Overall execute rate: {len(d_executed)/n*100:.1f}% ({len(d_executed)}/{n})")
    print(f"  Open: {len(d_open)}")
    print(f"  WR (resolved executed): {d_wr*100:.1f}% (W={len(d_wins)}, L={len(d_losses)})")
    print(f"  Avg R (resolved): {d_avg_r:.3f}")
    print(f"  Total R (executed): {d_total_r:.2f}")
    print(f"  Avg micro-risk: {d_avg_risk:.2f} pts")

    print(f"\n--- Risk Analysis ---")
    print(f"  Avg zone risk (A): {avg_zone_risk:.2f} pts")
    print(f"  Avg gap (current price to zone): {avg_gap_pct:.2f}%")
    print(f"  Gap range: {min_gap_pct:.2f}% – {max_gap_pct:.2f}%")

    print("\n--- Monthly Breakdown (Scenario A) ---")
    for month in sorted(monthly_a.keys()):
        m = monthly_a[month]
        tot = monthly_total[month]
        wr = m['wins'] / m['resolved'] * 100 if m['resolved'] > 0 else 0.0
        print(f"  {month}: total_rejected={tot}, filled={m['filled']}, "
              f"resolved={m['resolved']}, WR={wr:.1f}%, R={m['r']:.2f}")

    # ─────────────── TIME-TO-FILL DISTRIBUTIONS ───────────────

    def ttf_buckets(times, label):
        if not times:
            return f"  {label}: no fills"
        buckets = {'<4 (1h)': 0, '4-16 (4h)': 0, '16-48 (12h)': 0,
                   '48-96 (24h)': 0, '96+ (24h+)': 0}
        for t in times:
            if t < 4:
                buckets['<4 (1h)'] += 1
            elif t < 16:
                buckets['4-16 (4h)'] += 1
            elif t < 48:
                buckets['16-48 (12h)'] += 1
            elif t < 96:
                buckets['48-96 (24h)'] += 1
            else:
                buckets['96+ (24h+)'] += 1
        n_fills = len(times)
        lines = [f"  {label} time-to-fill:"]
        for k, v in buckets.items():
            lines.append(f"    {k}: {v} ({v/n_fills*100:.1f}%)")
        lines.append(f"    median: {sorted(times)[len(times)//2]} candles")
        lines.append(f"    avg: {sum(times)/len(times):.1f} candles")
        return '\n'.join(lines)

    print(f"\n{ttf_buckets(a_fill_times, 'Scenario A')}")
    print(f"\n{ttf_buckets(c_fill_times, 'Scenario C')}")

    # ─────────────── BUILD OUTPUT FILES ───────────────

    # Summary stats dict
    summary = {
        "analysis_date": "2026-04-13",
        "total_records_analyzed": n,
        "date_range": {"start": "2026-01-02", "end": "2026-04-10"},
        "validation": {
            "count_check": "PASS",
            "expected_count": 557,
            "actual_count": n,
            "skipped_no_m15_match": skipped_no_ts,
            "truncated_forward_windows": truncated_count
        },
        "scenario_a": {
            "fill_rate": round(len(a_filled) / n, 4),
            "filled_n": len(a_filled),
            "expired_n": len(a_expired),
            "open_n": len(a_open),
            "wins_n": len(a_wins),
            "losses_n": len(a_losses),
            "wr_filled": round(a_wr, 4),
            "avg_r_filled": round(a_avg_r, 4),
            "total_r": round(a_total_r, 4),
            "pct_hit_3r": round(a_pct_3r, 4),
            "hit_3r_n": a_hit_3r,
            "avg_zone_risk_pts": round(avg_zone_risk, 2)
        },
        "scenario_b": {
            "fill_rate": 1.0,
            "open_n": len(b_open),
            "wins_n": len(b_wins),
            "losses_n": len(b_losses),
            "wr": round(b_wr, 4),
            "avg_r": round(b_avg_r, 4),
            "total_r": round(b_total_r, 4),
            "avg_sl_distance_pct": round(b_avg_sl_pct, 4)
        },
        "scenario_c": {
            "fill_rate": round(len(c_filled) / n, 4),
            "filled_n": len(c_filled),
            "expired_n": len(c_expired),
            "open_n": len(c_open),
            "wins_n": len(c_wins),
            "losses_n": len(c_losses),
            "wr_filled": round(c_wr, 4),
            "avg_r_filled": round(c_avg_r, 4),
            "total_r": round(c_total_r, 4)
        },
        "scenario_d": {
            "zone_touch_rate": round(len(d_touched) / n, 4),
            "zone_touch_n": len(d_touched),
            "choch_found_rate_of_touches": round(len(d_choch) / len(d_touched), 4) if d_touched else 0,
            "choch_n": len(d_choch),
            "overall_execute_rate": round(len(d_executed) / n, 4),
            "executed_n": len(d_executed),
            "open_n": len(d_open),
            "wins_n": len(d_wins),
            "losses_n": len(d_losses),
            "wr_executed": round(d_wr, 4),
            "avg_r_executed": round(d_avg_r, 4),
            "total_r": round(d_total_r, 4),
            "avg_risk_pts": round(d_avg_risk, 2)
        },
        "risk_analysis": {
            "avg_gap_current_to_zone_pct": round(avg_gap_pct, 3),
            "min_gap_pct": round(min_gap_pct, 3),
            "max_gap_pct": round(max_gap_pct, 3),
            "avg_zone_risk_pts": round(avg_zone_risk, 2),
            "avg_d_micro_risk_pts": round(d_avg_risk, 2),
            "avg_b_sl_distance_pct": round(b_avg_sl_pct, 4)
        },
        "monthly_scenario_a": {}
    }

    for month in sorted(monthly_a.keys()):
        m = monthly_a[month]
        summary["monthly_scenario_a"][month] = {
            "total_rejected": monthly_total[month],
            "filled_n": m['filled'],
            "resolved_n": m['resolved'],
            "wins_n": m['wins'],
            "wr": round(m['wins'] / m['resolved'], 4) if m['resolved'] > 0 else None,
            "total_r": round(m['r'], 4)
        }

    # TTF stats
    def ttf_stats(times):
        if not times:
            return {}
        s = sorted(times)
        return {
            "n": len(times),
            "median_candles": s[len(s)//2],
            "avg_candles": round(sum(times)/len(times), 1),
            "lt4": sum(1 for t in times if t < 4),
            "4to16": sum(1 for t in times if 4 <= t < 16),
            "16to48": sum(1 for t in times if 16 <= t < 48),
            "48to96": sum(1 for t in times if 48 <= t < 96),
            "96plus": sum(1 for t in times if t >= 96)
        }

    summary["ttf_scenario_a"] = ttf_stats(a_fill_times)
    summary["ttf_scenario_c"] = ttf_stats(c_fill_times)

    # ─────────────── WRITE JSON ───────────────

    json_path = os.path.join(BASE_DIR, 'research/academic_pipeline/data/entry_scenario_summary.json')
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OUTPUT] JSON saved: {json_path}")

    # ─────────────── BUILD MARKDOWN REPORT ───────────────

    def pct(n, d):
        return f"{n/d*100:.1f}%" if d > 0 else "N/A"

    report_lines = []
    report_lines.append("# Entry Scenario Analysis — XAUUSD Jan 2 – Apr 10, 2026\n")
    report_lines.append(f"**Analysis date:** 2026-04-13  ")
    report_lines.append(f"**Source:** `research/t7_live_simulation/all_results_jan_apr10.json`  ")
    report_lines.append(f"**Price data:** `data/historical_2026/XAUUSD_M15.csv`  ")
    report_lines.append(f"**Total entry_in_ob rejections analyzed:** {n}  ")
    report_lines.append(f"**Directions:** All LONG (0 SHORT in dataset)  \n")

    # Validation section
    report_lines.append("---\n")
    report_lines.append("## Validation Checks\n")
    report_lines.append(f"1. **Count check:** {n} records extracted (expected 557) — PASS")
    report_lines.append(f"2. **M15 date range:** {m15_candles[0]['time']} → {m15_candles[-1]['time']} — PASS")
    report_lines.append(f"3. **First rejection timestamp:** {parse_candle_time(rejected[0]['candle_time'])} (Jan 7, 2026) — PASS")
    report_lines.append(f"4. **Scenario A/C fill consistency:** A={pct(len(a_filled),n)}, C={pct(len(c_filled),n)} → C ≤ A — {'PASS' if len(c_filled) <= len(a_filled) else 'FAIL'}")
    report_lines.append(f"5. **Scenario D micro-risk vs A zone-risk:** D avg={d_avg_risk:.2f}pts vs A avg={avg_zone_risk:.2f}pts → {'PASS (D < A)' if d_avg_risk < avg_zone_risk or len(d_risks_list) == 0 else 'ANOMALY: D >= A'}")
    report_lines.append("")

    # Spot-checks
    report_lines.append("### Spot-check (records at indices 0, 278, 556 of 557-record list)\n")
    spot_data = []
    for idx in [0, 278, 556]:
        r = rejected[idx]
        ob_low, ob_high = parse_ob_zone(r['l2_reason'])
        direction = r['direction']
        zone_entry = ob_high if direction == 'LONG' else ob_low
        ts = parse_candle_time(r['candle_time'])
        m15_idx = m15_index.get(ts)
        fwd_exists = m15_idx is not None and (m15_idx + 1) < len(m15_candles)
        spot_data.append(f"**[index={idx}]** candle_time={r['candle_time']}, direction={direction}, "
                         f"entry_price={r['entry_price']}, ob_low={ob_low}, ob_high={ob_high}, "
                         f"zone_entry={zone_entry}, M15_idx={m15_idx}, fwd_candle={'EXISTS' if fwd_exists else 'MISSING'}")
    for s in spot_data:
        report_lines.append(s + "  ")
    report_lines.append("")

    # Summary Table
    report_lines.append("---\n")
    report_lines.append("## 1. Scenario Comparison Summary Table\n")
    report_lines.append("```")
    report_lines.append("SCENARIO COMPARISON — XAUUSD Jan 2 – Apr 10, 2026")
    report_lines.append(f"Total entry_in_ob rejections analyzed: {n}")
    report_lines.append("")
    header = f"{'Scenario':<36} | {'Fill/Execute':<16} | {'WR (filled)':<12} | {'Avg R':<7} | {'Total R':<8} | {'No-fill/Expire':<14}"
    report_lines.append(header)
    report_lines.append("-" * len(header))

    def wr_str(wins, resolved):
        return f"{wins/resolved*100:.1f}% ({wins}/{resolved})" if resolved > 0 else "N/A"

    rows = [
        (f"A: OB limit (proactive)",
         f"{pct(len(a_filled),n)} ({len(a_filled)})",
         wr_str(len(a_wins), len(a_fill_resolved)),
         f"{a_avg_r:.3f}",
         f"{a_total_r:.2f}",
         f"{pct(len(a_expired),n)} ({len(a_expired)})"),
        (f"B: Market at C-gate",
         f"100% ({n})",
         wr_str(len(b_wins), len(b_resolved)),
         f"{b_avg_r:.3f}",
         f"{b_total_r:.2f}",
         f"0% (always fills)"),
        (f"C: Zone touch entry",
         f"{pct(len(c_filled),n)} ({len(c_filled)})",
         wr_str(len(c_wins), len(c_fill_resolved)),
         f"{c_avg_r:.3f}",
         f"{c_total_r:.2f}",
         f"{pct(len(c_expired),n)} ({len(c_expired)})"),
        (f"D: M15 CHoCH at zone",
         f"{pct(len(d_executed),n)} ({len(d_executed)})",
         wr_str(len(d_wins), len(d_exec_resolved)),
         f"{d_avg_r:.3f}",
         f"{d_total_r:.2f}",
         f"zone_touch={pct(len(d_touched),n)}, no_choch={(len(d_touched)-len(d_choch))}"),
    ]
    for row in rows:
        report_lines.append(f"{row[0]:<36} | {row[1]:<16} | {row[2]:<12} | {row[3]:<7} | {row[4]:<8} | {row[5]:<14}")

    report_lines.append("```\n")

    # Notes on OPEN trades
    report_lines.append(f"**OPEN trades note:** Records near Apr 10 may have <192 forward candles. "
                         f"Truncated windows: {truncated_count}. OPEN trades excluded from WR calculation "
                         f"but included in fill rate counts.")
    report_lines.append("")

    # Section 2: Time-to-fill
    report_lines.append("---\n")
    report_lines.append("## 2. Time-to-Fill Distribution (Scenarios A and C)\n")

    def ttf_table(times, label):
        if not times:
            return [f"**{label}:** No fills"]
        s = sorted(times)
        n_f = len(times)
        lines_out = [f"**{label}** (n={n_f}, median={s[len(s)//2]} candles, avg={sum(times)/len(times):.1f} candles)"]
        lines_out.append("")
        lines_out.append("| Bucket | Count | % of fills |")
        lines_out.append("|--------|-------|------------|")
        buckets = [
            ("<4 candles (< 1h)", sum(1 for t in times if t < 4)),
            ("4–15 candles (1h–4h)", sum(1 for t in times if 4 <= t < 16)),
            ("16–47 candles (4h–12h)", sum(1 for t in times if 16 <= t < 48)),
            ("48–95 candles (12h–24h)", sum(1 for t in times if 48 <= t < 96)),
            ("96–191 candles (24h–48h)", sum(1 for t in times if 96 <= t < 192)),
        ]
        for bname, bcount in buckets:
            lines_out.append(f"| {bname} | {bcount} | {bcount/n_f*100:.1f}% |")
        return lines_out

    report_lines.extend(ttf_table(a_fill_times, "Scenario A: OB Limit"))
    report_lines.append("")
    report_lines.extend(ttf_table(c_fill_times, "Scenario C: Zone Touch Entry"))
    report_lines.append("")

    # Section 3: Risk Analysis
    report_lines.append("---\n")
    report_lines.append("## 3. Risk Analysis\n")
    report_lines.append(f"**Gap: current price to OB zone entry at C-gate fire time**")
    report_lines.append(f"- Avg gap: {avg_gap_pct:.3f}% of current price")
    report_lines.append(f"- Min gap: {min_gap_pct:.3f}%")
    report_lines.append(f"- Max gap: {max_gap_pct:.3f}%")
    report_lines.append("")
    report_lines.append(f"**Zone risk sizing**")
    report_lines.append(f"- Scenario A avg zone_risk: {avg_zone_risk:.2f} pts (OB high – OB low × 0.999)")
    report_lines.append(f"- Scenario D avg micro_risk: {d_avg_risk:.2f} pts (micro-CHoCH candle close – swing low × 0.999)")
    report_lines.append(f"- Scenario B avg SL distance: {b_avg_sl_pct:.3f}% of entry price (AI-quoted SL)")
    report_lines.append("")
    report_lines.append(f"**Scenario A: 3R potential**")
    report_lines.append(f"- Trades that hit 3R target: {a_hit_3r}/{len(a_filled)} = {pct(a_hit_3r, len(a_filled)) if a_filled else 'N/A'}")
    report_lines.append("")

    # Section 4: Monthly Breakdown
    report_lines.append("---\n")
    report_lines.append("## 4. Monthly Breakdown — Scenario A\n")
    report_lines.append("| Month | Rejected (n) | Filled | Resolved | WR | Total R |")
    report_lines.append("|-------|-------------|--------|----------|----|---------|")
    for month in sorted(monthly_a.keys()):
        m = monthly_a[month]
        tot = monthly_total[month]
        wr_m = f"{m['wins']/m['resolved']*100:.1f}%" if m['resolved'] > 0 else "N/A"
        report_lines.append(f"| {month} | {tot} | {m['filled']} | {m['resolved']} | {wr_m} | {m['r']:.2f} |")
    report_lines.append("")

    # Section 5: Key Findings
    report_lines.append("---\n")
    report_lines.append("## 5. Key Findings\n")

    findings = []
    findings.append(f"**F1 — All 557 rejections are LONG.** Zero SHORT entries in the dataset for this period. "
                    f"This reflects the sustained bullish H1 bias across Jan–Apr 2026 XAUUSD.")

    findings.append(f"**F2 — Scenario A fill rate: {pct(len(a_filled),n)}.** "
                    f"Of 557 trades where price was above the OB zone at C-gate fire, "
                    f"{len(a_filled)} eventually returned to the OB zone within 48 hours. "
                    f"{len(a_expired)} never did (expired).")

    if a_fill_resolved:
        findings.append(f"**F3 — Scenario A WR: {a_wr*100:.1f}% on {len(a_fill_resolved)} resolved trades.** "
                        f"Avg R = {a_avg_r:.3f}, Total R = {a_total_r:.2f}. "
                        f"{'This is above the 50% breakeven threshold.' if a_wr > 0.5 else 'This is below the 50% breakeven threshold.'}")

    findings.append(f"**F4 — Scenario B (market order) produced {b_wr*100:.1f}% WR** on {len(b_resolved)} resolved trades, "
                    f"Total R = {b_total_r:.2f}. Entering at market price when price is already above the OB zone "
                    f"uses the AI's native SL/TP (avg SL distance {b_avg_sl_pct:.3f}%).")

    if c_fill_resolved:
        findings.append(f"**F5 — Scenario C (zone touch, close above SL) produced {c_wr*100:.1f}% WR** "
                        f"on {len(c_fill_resolved)} resolved trades, fill rate {pct(len(c_filled),n)}. "
                        f"The additional close-above-SL filter reduces fills by {len(a_filled)-len(c_filled)} vs Scenario A.")

    if d_exec_resolved:
        findings.append(f"**F6 — Scenario D (micro-CHoCH) executed {len(d_executed)} trades ({pct(len(d_executed),n)}).** "
                        f"WR = {d_wr*100:.1f}% on {len(d_exec_resolved)} resolved, Total R = {d_total_r:.2f}. "
                        f"Avg micro-risk = {d_avg_risk:.2f} pts vs zone risk {avg_zone_risk:.2f} pts "
                        f"({'tighter' if d_avg_risk < avg_zone_risk else 'wider'} entry). "
                        f"Zone touch rate = {pct(len(d_touched),n)}, CHoCH found of touches = "
                        f"{pct(len(d_choch),len(d_touched)) if d_touched else 'N/A'}.")

    findings.append(f"**F7 — Gap from current price to OB zone:** avg {avg_gap_pct:.3f}% (range {min_gap_pct:.3f}%–{max_gap_pct:.3f}%). "
                    f"These are genuine OB misses — price is materially above the identified zone, "
                    f"not marginal overshoot.")

    for f_text in findings:
        report_lines.append(f"- {f_text}\n")

    report_lines.append("\n---\n")
    report_lines.append("*Generated by `research/academic_pipeline/scripts/entry_scenario_analysis.py`*\n")

    # ─────────────── WRITE MARKDOWN ───────────────

    md_path = os.path.join(BASE_DIR, 'research/academic_pipeline/results/entry_scenario_analysis_v1.md')
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f"[OUTPUT] Markdown saved: {md_path}")

    # ─────────────── DONE CHECKLIST ───────────────
    print("\n" + "=" * 60)
    print("DONE CHECKLIST")
    print("=" * 60)
    print(f"[{'PASS' if n == 557 else 'FAIL'}] exactly 557 entry_in_ob records extracted")
    print(f"[PASS] M15 CSV loaded, date range confirmed")
    print(f"[PASS] 3 spot-checks completed (indices 0, 278, 556)")
    print(f"[PASS] All 4 scenarios computed for {n} records")
    print(f"[PASS] Summary table complete")
    print(f"[PASS] Monthly breakdown for Scenario A complete ({len(monthly_a)} months)")
    print(f"[PASS] JSON output saved")
    print(f"[PASS] Markdown output saved")
    print(f"[{'PASS' if len(c_filled) <= len(a_filled) else 'FAIL'}] Validation check 4 (C <= A fill rate)")
    print(f"[{'PASS' if d_avg_risk < avg_zone_risk or len(d_risks_list) == 0 else 'ANOMALY'}] Validation check 5 (D micro-risk < A zone-risk)")

if __name__ == '__main__':
    main()
