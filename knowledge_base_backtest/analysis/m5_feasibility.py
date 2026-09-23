#!/usr/bin/env python3
"""
M5 Entry Refinement — Feasibility Test
Tests whether M5 entries within confirmed M15 OB zones improve trade outcomes.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent.parent

# For API calls - load .env manually
env_path = BASE / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()
import anthropic
ANALYSIS_DIR = BASE / "knowledge_base_backtest" / "analysis"
DATA_DIR = BASE / "data"

###############################################################################
# DATA LOADING
###############################################################################

def load_m5():
    df = pd.read_csv(DATA_DIR / "XAUUSD_M5.csv", parse_dates=['time'])
    df = df.sort_values('time').reset_index(drop=True)
    return df

def load_trades():
    with open(ANALYSIS_DIR / "phase1_all_trades_merged.json") as f:
        return json.load(f)

###############################################################################
# M5 CANDLE EXTRACTION
###############################################################################

def get_m5_candles_for_prompt(m5_df, date_str, kz, entry_time_str):
    """Get M5 candles BEFORE entry for the AI prompt (36 candles = 3 hours)."""
    entry_time = pd.Timestamp(entry_time_str).tz_localize(None)

    # Get 3 hours before entry
    window_start = entry_time - pd.Timedelta(hours=3)

    mask = (m5_df['time'] >= window_start) & (m5_df['time'] < entry_time)
    candles = m5_df[mask].copy()

    return candles

def get_m5_candles_for_simulation(m5_df, date_str, kz, entry_time_str):
    """Get M5 candles AFTER entry for outcome simulation."""
    entry_time = pd.Timestamp(entry_time_str).tz_localize(None)

    # Simulation window: from entry to end of session
    if kz == 'london':
        session_end = pd.Timestamp(date_str) + pd.Timedelta(hours=11, minutes=30)
    else:  # ny
        session_end = pd.Timestamp(date_str) + pd.Timedelta(hours=17, minutes=30)

    mask = (m5_df['time'] >= entry_time) & (m5_df['time'] <= session_end)
    candles = m5_df[mask].copy()

    return candles

def format_m5_candles(candles, mark_last=True):
    """Format M5 candles for the AI prompt."""
    lines = []
    for i, (_, row) in enumerate(candles.iterrows()):
        body = abs(row['close'] - row['open'])
        direction = "BULL" if row['close'] >= row['open'] else "BEAR"
        ts = row['time'].strftime('%Y-%m-%dT%H:%M:%SZ')
        marker = ""
        if mark_last and i == len(candles) - 1:
            marker = " ← CURRENT (M15 just closed)"
        lines.append(f"[{i+1:2d}] {ts} O:{row['open']:.2f} H:{row['high']:.2f} "
                     f"L:{row['low']:.2f} C:{row['close']:.2f} body:{body:.2f} [{direction}]{marker}")
    return "\n".join(lines)

###############################################################################
# M5 REFINEMENT PROMPT
###############################################################################

SYSTEM_PROMPT = """You are an expert gold scalper specializing in M5 entry refinement within confirmed Smart Money setups. A CANDIDATE trade has already been confirmed on M15. Your job is to find the OPTIMAL M5 entry — the price level within the setup zone that offers the best structural entry with the tightest valid stop loss."""

def build_user_prompt(trade, m5_candles_str, n_candles):
    direction = trade['direction']
    entry = trade['entry_price']
    sl = trade['stop_loss']
    sl_dist = abs(entry - sl)
    kz = trade['kill_zone']

    return f"""CONFIRMED M15 SETUP:
- Direction: {direction}
- M15 Entry: ${entry:.2f}
- M15 SL: ${sl:.2f} (${sl_dist:.2f} distance)
- Setup zone: ${sl:.2f} to ${entry:.2f} (this is the H1 OB zone the AI targeted)
- KZ: {kz}

M5 CANDLES ({n_candles} candles, most recent at bottom):
{m5_candles_str}

ANALYSIS INSTRUCTIONS:
1. STRUCTURE: Examine M5 candles for BOS, CHoCH, or clear swing structure within the setup zone. For LONG: look for M5 higher-low or bullish BOS/CHoCH. For SHORT: M5 lower-high or bearish BOS/CHoCH.

2. M5 ORDER BLOCK: If there's an M5 BOS with displacement, identify the M5 OB (last counter-direction candle before the BOS). This is the optimal limit entry zone.

3. M5 FVG: Did the M5 move create a Fair Value Gap? If yes, the midpoint of the FVG is a strong entry level.

4. DISPLACEMENT QUALITY: Is the M5 move clean (large bodies, minimal wicks) or messy (overlapping candles, long wicks)? Rate as CLEAN, MODERATE, or MESSY.

5. ENTRY SELECTION: Choose the best entry from:
   a) M5 OB zone midpoint (if available)
   b) M5 FVG midpoint (if available)
   c) 50% retracement of M5 impulse move
   d) M15 entry (if no valid M5 structure exists)

6. M5 SL: Place SL below (LONG) or above (SHORT) the M5 swing that confirmed the structure, plus $1.50 buffer. The M5 SL MUST be between the entry and the M15 SL. If no valid M5 SL exists that's tighter than M15 SL, output NO_REFINEMENT.

7. QUALITY GRADE: Based on M5 structure clarity, grade the setup:
   - HIGH: Clean M5 BOS/CHoCH with displacement + OB or FVG identifiable. Use M5 SL.
   - MEDIUM: Some M5 structure visible but messy. Use M5 SL with extra buffer.
   - LOW: No clear M5 structure. Use M15 SL (no refinement).

OUTPUT (JSON only, no other text):
{{
  "decision": "REFINED" or "NO_REFINEMENT",
  "m5_quality": "HIGH" or "MEDIUM" or "LOW",
  "m5_entry": <price or null>,
  "m5_sl": <price or null>,
  "m5_sl_distance": <dollars or null>,
  "m5_structure": "bos" or "choch" or "higher_low" or "lower_high" or null,
  "m5_ob_identified": true or false,
  "m5_fvg_identified": true or false,
  "m5_displacement_quality": "clean" or "moderate" or "messy" or null,
  "reasoning": "<2-3 sentences explaining the M5 read>"
}}"""

###############################################################################
# API CALL
###############################################################################

def call_sonnet_m5(trade, m5_candles_str, n_candles):
    """Call Claude Sonnet for M5 refinement."""
    client = anthropic.Anthropic()

    user_prompt = build_user_prompt(trade, m5_candles_str, n_candles)

    start = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    elapsed = time.time() - start

    text = response.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            elif line.startswith("```") and in_block:
                break
            elif in_block:
                json_lines.append(line)
        text = "\n".join(json_lines)

    # Parse JSON
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = {"decision": "PARSE_ERROR", "raw": text}

    # Token usage
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)

    return result, elapsed, cost, input_tokens, output_tokens

###############################################################################
# SIMULATION
###############################################################################

def simulate_trade(m5_sim_candles, entry_price, sl_price, direction, sl_distance):
    """Simulate a trade on M5 candles. Returns dict with outcome metrics."""
    if len(m5_sim_candles) == 0:
        return {'outcome': 'no_data', 'final_r': 0, 'mfe_dollar': 0, 'mae_dollar': 0}

    tp_distance = sl_distance * 1.5
    if direction == 'LONG':
        tp_price = entry_price + tp_distance
    else:
        tp_price = entry_price - tp_distance

    mfe_dollar = 0
    mae_dollar = 0
    final_r = 0
    outcome = 'timeout'

    for _, candle in m5_sim_candles.iterrows():
        if direction == 'LONG':
            # Track extremes
            favorable = candle['high'] - entry_price
            adverse = entry_price - candle['low']
            mfe_dollar = max(mfe_dollar, favorable)
            mae_dollar = max(mae_dollar, adverse)

            # Check SL first (conservative on same-candle)
            if candle['low'] <= sl_price:
                outcome = 'sl_hit'
                final_r = -1.0
                break
            # Check TP
            if candle['high'] >= tp_price:
                outcome = 'tp_hit'
                final_r = 1.5
                break
        else:  # SHORT
            favorable = entry_price - candle['low']
            adverse = candle['high'] - entry_price
            mfe_dollar = max(mfe_dollar, favorable)
            mae_dollar = max(mae_dollar, adverse)

            if candle['high'] >= sl_price:
                outcome = 'sl_hit'
                final_r = -1.0
                break
            if candle['low'] <= tp_price:
                outcome = 'tp_hit'
                final_r = 1.5
                break

    if outcome == 'timeout':
        last_close = m5_sim_candles.iloc[-1]['close']
        if direction == 'LONG':
            final_r = (last_close - entry_price) / sl_distance
        else:
            final_r = (entry_price - last_close) / sl_distance

    return {
        'outcome': outcome,
        'final_r': round(final_r, 3),
        'mfe_dollar': round(mfe_dollar, 2),
        'mae_dollar': round(mae_dollar, 2),
        'tp_price': round(tp_price, 2),
        'sl_distance': round(sl_distance, 2),
    }

###############################################################################
# MAIN
###############################################################################

def main():
    print("=" * 70)
    print("M5 ENTRY REFINEMENT — FEASIBILITY TEST")
    print("=" * 70)

    # Load data
    print("\n[Step 0] Loading data...")
    m5_df = load_m5()
    trades = load_trades()
    print(f"  M5 data: {len(m5_df)} candles, {m5_df['time'].min()} to {m5_df['time'].max()}")
    print(f"  Phase 1 trades: {len(trades)}")

    # Check M5 coverage
    covered = []
    not_covered = []
    for t in trades:
        date = pd.Timestamp(t['date']).date()
        has_data = len(m5_df[m5_df['time'].dt.date == date]) > 0
        if has_data:
            covered.append(t)
        else:
            not_covered.append(t)

    print(f"  M5 coverage: {len(covered)}/{len(trades)} trades")
    if not_covered:
        print(f"  Missing M5: {', '.join(t['date'] for t in not_covered)}")

    # Process each covered trade
    print(f"\n[Step 1-2] Running M5 refinement for {len(covered)} trades...")
    results = []
    total_cost = 0
    total_time = 0

    for i, trade in enumerate(covered):
        date_str = trade['date']
        kz = trade['kill_zone']
        entry_time = trade['candle_time']

        print(f"\n  Trade {i+1}/{len(covered)}: {date_str} {kz} {trade['direction']} "
              f"E={trade['entry_price']:.2f} SL={trade['stop_loss']:.2f}")

        # Get M5 candles for prompt (before entry)
        prompt_candles = get_m5_candles_for_prompt(m5_df, date_str, kz, entry_time)

        if len(prompt_candles) < 5:
            print(f"    ⚠ Only {len(prompt_candles)} M5 candles before entry, skipping")
            results.append({
                'trade': trade,
                'refinement': {'decision': 'NO_DATA'},
                'cost': 0,
            })
            continue

        # Format candles
        m5_str = format_m5_candles(prompt_candles)

        # Call Sonnet
        print(f"    Calling Sonnet ({len(prompt_candles)} M5 candles)...")
        refinement, elapsed, cost, in_tok, out_tok = call_sonnet_m5(trade, m5_str, len(prompt_candles))
        total_cost += cost
        total_time += elapsed

        print(f"    Decision: {refinement.get('decision', 'UNKNOWN')} | "
              f"Quality: {refinement.get('m5_quality', 'N/A')} | "
              f"Time: {elapsed:.1f}s | Cost: ${cost:.4f}")

        if refinement.get('decision') == 'REFINED':
            m5_entry = refinement.get('m5_entry')
            m5_sl = refinement.get('m5_sl')
            m5_sl_dist = refinement.get('m5_sl_distance')
            print(f"    M5 Entry: {m5_entry} | M5 SL: {m5_sl} | M5 SL Dist: ${m5_sl_dist}")
            print(f"    Structure: {refinement.get('m5_structure')} | "
                  f"OB: {refinement.get('m5_ob_identified')} | FVG: {refinement.get('m5_fvg_identified')}")

            # Validate constraints
            direction = trade['direction']
            m15_entry = trade['entry_price']
            m15_sl = trade['stop_loss']

            # M5 entry must be between M15 entry and M15 SL (within OB zone)
            if m5_entry is not None:
                if direction == 'LONG':
                    if m5_entry > m15_entry or m5_entry < m15_sl:
                        print(f"    ⚠ M5 entry {m5_entry} outside OB zone [{m15_sl}, {m15_entry}], using M15 entry")
                        refinement['m5_entry'] = m15_entry
                        refinement['m5_entry_corrected'] = True
                else:  # SHORT
                    if m5_entry < m15_entry or m5_entry > m15_sl:
                        print(f"    ⚠ M5 entry {m5_entry} outside OB zone [{m15_entry}, {m15_sl}], using M15 entry")
                        refinement['m5_entry'] = m15_entry
                        refinement['m5_entry_corrected'] = True

            # M5 SL must be between entry and M15 SL, min $3 from entry
            if m5_sl is not None and m5_entry is not None:
                actual_m5_entry = refinement.get('m5_entry', m5_entry)
                if direction == 'LONG':
                    if m5_sl >= actual_m5_entry or m5_sl < m15_sl:
                        print(f"    ⚠ M5 SL invalid, using entry-$3 minimum")
                        refinement['m5_sl'] = actual_m5_entry - 3.0
                        refinement['m5_sl_distance'] = 3.0
                    elif actual_m5_entry - m5_sl < 3.0:
                        refinement['m5_sl'] = actual_m5_entry - 3.0
                        refinement['m5_sl_distance'] = 3.0
                else:
                    if m5_sl <= actual_m5_entry or m5_sl > m15_sl:
                        refinement['m5_sl'] = actual_m5_entry + 3.0
                        refinement['m5_sl_distance'] = 3.0
                    elif m5_sl - actual_m5_entry < 3.0:
                        refinement['m5_sl'] = actual_m5_entry + 3.0
                        refinement['m5_sl_distance'] = 3.0

        results.append({
            'trade': trade,
            'refinement': refinement,
            'cost': cost,
            'elapsed': elapsed,
        })

    print(f"\n  Total API cost: ${total_cost:.4f}")
    print(f"  Total API time: {total_time:.1f}s")

    # Step 3: Simulate all approaches
    print(f"\n[Step 3] Simulating outcomes...")
    all_outcomes = []

    for r in results:
        trade = r['trade']
        ref = r['refinement']
        date_str = trade['date']
        kz = trade['kill_zone']
        entry_time = trade['candle_time']
        direction = trade['direction']
        m15_entry = trade['entry_price']
        m15_sl = trade['stop_loss']
        m15_sl_dist = abs(m15_entry - m15_sl)

        # Get simulation candles
        sim_candles = get_m5_candles_for_simulation(m5_df, date_str, kz, entry_time)

        if len(sim_candles) == 0:
            print(f"  {date_str} {kz}: No simulation candles, skipping")
            all_outcomes.append({
                'date': date_str, 'kz': kz, 'direction': direction,
                'm15_sl_dist': m15_sl_dist,
                'refined': False,
                'baseline': {'outcome': 'no_data', 'final_r': trade['r_multiple']},
                'approach_a': None, 'approach_b': None, 'approach_c': None,
            })
            continue

        # Baseline: M15 entry + M15 SL + 1.5R TP
        baseline = simulate_trade(sim_candles, m15_entry, m15_sl, direction, m15_sl_dist)

        outcome = {
            'date': date_str, 'kz': kz, 'direction': direction,
            'grade': trade.get('setup_grade', '?'),
            'm15_entry': m15_entry, 'm15_sl': m15_sl, 'm15_sl_dist': m15_sl_dist,
            'phase1_r': trade['r_multiple'],
            'baseline': baseline,
            'refined': ref.get('decision') == 'REFINED',
            'm5_quality': ref.get('m5_quality'),
            'm5_structure': ref.get('m5_structure'),
            'm5_ob': ref.get('m5_ob_identified'),
            'm5_fvg': ref.get('m5_fvg_identified'),
            'm5_disp_quality': ref.get('m5_displacement_quality'),
            'reasoning': ref.get('reasoning', ''),
        }

        if ref.get('decision') == 'REFINED':
            m5_entry = ref.get('m5_entry', m15_entry)
            m5_sl = ref.get('m5_sl')
            m5_sl_dist = ref.get('m5_sl_distance')

            if m5_entry is None or m5_sl is None or m5_sl_dist is None:
                outcome['approach_a'] = baseline
                outcome['approach_b'] = baseline
                outcome['approach_c'] = baseline
            else:
                # Entry improvement
                if direction == 'LONG':
                    entry_improvement = m15_entry - m5_entry
                else:
                    entry_improvement = m5_entry - m15_entry
                outcome['m5_entry'] = m5_entry
                outcome['m5_sl'] = m5_sl
                outcome['m5_sl_dist'] = m5_sl_dist
                outcome['entry_improvement'] = round(entry_improvement, 2)

                # Approach A: M5 entry + M5 SL
                outcome['approach_a'] = simulate_trade(
                    sim_candles, m5_entry, m5_sl, direction, m5_sl_dist)

                # Approach B: M5 entry + M15 SL (better price, same safety net)
                b_sl_dist = abs(m5_entry - m15_sl)
                outcome['approach_b'] = simulate_trade(
                    sim_candles, m5_entry, m15_sl, direction, b_sl_dist)

                # Approach C: M5 entry + M5 SL + $5 buffer
                if direction == 'LONG':
                    c_sl = m5_sl - 5.0
                else:
                    c_sl = m5_sl + 5.0
                c_sl_dist = abs(m5_entry - c_sl)
                outcome['approach_c'] = simulate_trade(
                    sim_candles, m5_entry, c_sl, direction, c_sl_dist)
        else:
            # No refinement — all approaches = baseline
            outcome['approach_a'] = baseline
            outcome['approach_b'] = baseline
            outcome['approach_c'] = baseline

        all_outcomes.append(outcome)

        status = "REFINED" if outcome['refined'] else "NO_REFINE"
        print(f"  {date_str} {kz}: {status} | "
              f"Base={baseline['final_r']:+.3f} "
              f"A={outcome['approach_a']['final_r']:+.3f} "
              f"B={outcome['approach_b']['final_r']:+.3f} "
              f"C={outcome['approach_c']['final_r']:+.3f}")

    # Step 4: Statistics
    print(f"\n{'='*70}")
    print("STEP 4: RESULTS")
    print(f"{'='*70}")

    # 4A: Refinement summary
    total_with_data = len([o for o in all_outcomes if o['baseline'].get('outcome') != 'no_data'])
    refined_count = sum(1 for o in all_outcomes if o['refined'])
    no_refine = sum(1 for o in all_outcomes if not o['refined'] and o['baseline'].get('outcome') != 'no_data')

    print(f"\n--- 4A: M5 Refinement Summary ---")
    print(f"Trades with M5 data:     {total_with_data}/{len(trades)}")
    print(f"REFINED (M5 structure):  {refined_count}/{total_with_data}")
    print(f"NO_REFINEMENT:           {no_refine}/{total_with_data}")

    refined_outcomes = [o for o in all_outcomes if o['refined']]
    if refined_outcomes:
        qualities = [o.get('m5_quality', 'N/A') for o in refined_outcomes]
        from collections import Counter
        q_counts = Counter(qualities)
        print(f"Quality distribution:    {dict(q_counts)}")

        ob_count = sum(1 for o in refined_outcomes if o.get('m5_ob'))
        fvg_count = sum(1 for o in refined_outcomes if o.get('m5_fvg'))
        print(f"M5 OB identified:        {ob_count}/{refined_count}")
        print(f"M5 FVG identified:       {fvg_count}/{refined_count}")

        m5_sls = [o.get('m5_sl_dist', 0) for o in refined_outcomes if o.get('m5_sl_dist')]
        m15_sls = [o['m15_sl_dist'] for o in refined_outcomes]
        entry_imps = [o.get('entry_improvement', 0) for o in refined_outcomes if o.get('entry_improvement') is not None]

        if m5_sls:
            print(f"Avg M5 SL distance:      ${np.mean(m5_sls):.2f}")
        print(f"Avg M15 SL distance:     ${np.mean(m15_sls):.2f}")
        if m5_sls and m15_sls:
            reductions = [m15 - m5 for m15, m5 in zip(m15_sls, m5_sls)]
            print(f"Avg SL reduction:        ${np.mean(reductions):.2f} ({np.mean(reductions)/np.mean(m15_sls)*100:.1f}%)")
        if entry_imps:
            print(f"Avg entry improvement:   ${np.mean(entry_imps):.2f}")

    # 4B: Per-trade comparison
    print(f"\n--- 4B: Per-Trade Outcome Comparison ---")
    print(f"{'#':>2} {'Date':>10} {'KZ':>7} {'M15 SL$':>8} {'M5 SL$':>7} {'Δ Entry':>7} "
          f"{'Base R':>7} {'A R':>7} {'B R':>7} {'C R':>7}")
    print("-" * 85)

    valid_outcomes = [o for o in all_outcomes if o['baseline'].get('outcome') != 'no_data']
    for i, o in enumerate(valid_outcomes):
        m5_sl = f"${o.get('m5_sl_dist', 0):.1f}" if o['refined'] else "—"
        entry_imp = f"${o.get('entry_improvement', 0):+.1f}" if o['refined'] else "—"
        print(f"{i+1:2d} {o['date']:>10} {o['kz']:>7} ${o['m15_sl_dist']:>6.1f} {m5_sl:>7} {entry_imp:>7} "
              f"{o['baseline']['final_r']:>+7.3f} "
              f"{o['approach_a']['final_r']:>+7.3f} "
              f"{o['approach_b']['final_r']:>+7.3f} "
              f"{o['approach_c']['final_r']:>+7.3f}")

    # 4C: Aggregate results
    print(f"\n--- 4C: Aggregate Results ---")
    approaches = {
        'Baseline': [o['baseline']['final_r'] for o in valid_outcomes],
        'A (M5+M5SL)': [o['approach_a']['final_r'] for o in valid_outcomes],
        'B (M5+M15SL)': [o['approach_b']['final_r'] for o in valid_outcomes],
        'C (M5+M5SL+$5)': [o['approach_c']['final_r'] for o in valid_outcomes],
    }

    print(f"{'Metric':<25} {'Baseline':>10} {'A (M5+M5SL)':>12} {'B (M5+M15SL)':>13} {'C (M5+M5SL+$5)':>14}")
    print("-" * 75)

    for name, rs in approaches.items():
        total_r = sum(rs)
        avg_r = np.mean(rs)
        win_rate = sum(1 for r in rs if r > 0) / len(rs) * 100
        tp_rate = sum(1 for r in rs if r >= 1.49) / len(rs) * 100
        sl_rate = sum(1 for r in rs if r <= -0.99) / len(rs) * 100
        # Only print for first metric, then individual lines
        pass

    for metric_name, metric_fn in [
        ('Total R', lambda rs: f"{sum(rs):+.3f}"),
        ('Avg R', lambda rs: f"{np.mean(rs):+.3f}"),
        ('Win Rate', lambda rs: f"{sum(1 for r in rs if r > 0)/len(rs)*100:.1f}%"),
        ('TP Hit Rate', lambda rs: f"{sum(1 for r in rs if r >= 1.49)/len(rs)*100:.1f}%"),
        ('SL Hit Rate', lambda rs: f"{sum(1 for r in rs if r <= -0.99)/len(rs)*100:.1f}%"),
        ('Avg MFE $', lambda rs: "—"),
        ('Dollar P&L ($1K)', lambda rs: f"${sum(rs)*1000:.0f}"),
    ]:
        vals = []
        for name, rs in approaches.items():
            if metric_name == 'Avg MFE $':
                key = {'Baseline': 'baseline', 'A (M5+M5SL)': 'approach_a',
                       'B (M5+M15SL)': 'approach_b', 'C (M5+M5SL+$5)': 'approach_c'}[name]
                mfes = [o[key].get('mfe_dollar', 0) for o in valid_outcomes]
                vals.append(f"${np.mean(mfes):.2f}")
            else:
                vals.append(metric_fn(rs))
        print(f"{metric_name:<25} {vals[0]:>10} {vals[1]:>12} {vals[2]:>13} {vals[3]:>12}")

    # Additional stop-outs analysis
    baseline_sl = set()
    a_sl = set()
    c_sl = set()
    for i, o in enumerate(valid_outcomes):
        if o['baseline']['outcome'] == 'sl_hit':
            baseline_sl.add(i)
        if o['approach_a']['outcome'] == 'sl_hit':
            a_sl.add(i)
        if o['approach_c']['outcome'] == 'sl_hit':
            c_sl.add(i)

    extra_a = a_sl - baseline_sl
    extra_c = c_sl - baseline_sl
    print(f"\nAdditional stop-outs:")
    print(f"  Approach A vs Baseline: {len(extra_a)} extra")
    print(f"  Approach B vs Baseline: 0 (same SL)")
    print(f"  Approach C vs Baseline: {len(extra_c)} extra")

    # 4D: Stop-out analysis
    if extra_a:
        print(f"\n--- 4D: Stop-Out Analysis ---")
        print(f"Trades stopped out in Approach A but NOT in Baseline:")
        for idx in extra_a:
            o = valid_outcomes[idx]
            print(f"  {o['date']} {o['kz']}: "
                  f"M5 SL=${o.get('m5_sl_dist', '?')} | "
                  f"MAE_A=${o['approach_a']['mae_dollar']:.2f} | "
                  f"Baseline outcome={o['baseline']['outcome']} R={o['baseline']['final_r']:+.3f}")

    # 4E: TP conversion analysis
    baseline_tp = set(i for i, o in enumerate(valid_outcomes) if o['baseline']['outcome'] == 'tp_hit')
    a_tp = set(i for i, o in enumerate(valid_outcomes) if o['approach_a']['outcome'] == 'tp_hit')
    b_tp = set(i for i, o in enumerate(valid_outcomes) if o['approach_b']['outcome'] == 'tp_hit')
    c_tp = set(i for i, o in enumerate(valid_outcomes) if o['approach_c']['outcome'] == 'tp_hit')

    new_tp_a = a_tp - baseline_tp
    new_tp_b = b_tp - baseline_tp
    new_tp_c = c_tp - baseline_tp

    print(f"\n--- 4E: TP Conversion Analysis ---")
    print(f"TP hits: Baseline={len(baseline_tp)}, A={len(a_tp)}, B={len(b_tp)}, C={len(c_tp)}")
    print(f"NEW TP hits vs baseline: A={len(new_tp_a)}, B={len(new_tp_b)}, C={len(new_tp_c)}")

    for name, new_tps, approach_key in [
        ('A', new_tp_a, 'approach_a'),
        ('B', new_tp_b, 'approach_b'),
        ('C', new_tp_c, 'approach_c'),
    ]:
        if new_tps:
            print(f"\n  New TP hits in Approach {name}:")
            for idx in new_tps:
                o = valid_outcomes[idx]
                print(f"    {o['date']} {o['kz']}: "
                      f"TP target=${o[approach_key]['tp_price']:.2f} | "
                      f"SL dist=${o[approach_key]['sl_distance']:.2f} | "
                      f"Baseline: {o['baseline']['outcome']} R={o['baseline']['final_r']:+.3f}")

    # 4F: Quality vs outcome
    print(f"\n--- 4F: M5 Quality vs Outcome ---")
    for quality in ['HIGH', 'MEDIUM', 'LOW', None]:
        q_label = quality if quality else 'NO_REFINEMENT'
        if quality:
            subset = [o for o in valid_outcomes if o.get('m5_quality') == quality]
        else:
            subset = [o for o in valid_outcomes if not o['refined']]

        if not subset:
            continue

        avg_reduction = np.mean([o['m15_sl_dist'] - o.get('m5_sl_dist', o['m15_sl_dist']) for o in subset])
        avg_r_a = np.mean([o['approach_a']['final_r'] for o in subset])
        extra = sum(1 for o in subset if o['approach_a']['outcome'] == 'sl_hit' and o['baseline']['outcome'] != 'sl_hit')
        print(f"  {q_label:15} n={len(subset):2d} | SL reduction=${avg_reduction:+.1f} | "
              f"Avg R(A)={avg_r_a:+.3f} | Extra SL={extra}")

    # Save all data
    ts = datetime.now().strftime('%Y%m%d_%H%M')

    # Save raw refinement responses
    responses_path = ANALYSIS_DIR / f"m5_refinement_responses_{ts}.json"
    save_results = []
    for r in results:
        sr = {
            'date': r['trade']['date'],
            'kz': r['trade']['kill_zone'],
            'direction': r['trade']['direction'],
            'entry_price': r['trade']['entry_price'],
            'stop_loss': r['trade']['stop_loss'],
            'refinement': r['refinement'],
            'cost': r.get('cost', 0),
        }
        save_results.append(sr)

    with open(responses_path, 'w') as f:
        json.dump(save_results, f, indent=2, default=str)
    print(f"\n  Saved: {responses_path}")

    # Save full feasibility data
    data_path = ANALYSIS_DIR / f"m5_feasibility_data_{ts}.json"
    with open(data_path, 'w') as f:
        json.dump(all_outcomes, f, indent=2, default=str)
    print(f"  Saved: {data_path}")

    return all_outcomes, results, valid_outcomes

if __name__ == '__main__':
    all_outcomes, results, valid_outcomes = main()
