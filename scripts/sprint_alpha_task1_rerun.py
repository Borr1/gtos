#!/usr/bin/env python3
"""
Sprint Alpha Task 1 RERUN — On the REAL batch trading population.

For each of the real XAUUSD batch BOS events:
1. OB zone entry outcome = actual batch outcome (ground truth)
2. "All OB entries, no AI" = simulate all candidates on H1 with same SL/TP
3. Dumb baseline = if price retraces to 80/85/90/95% of impulse, enter there, SAME SL/TP prices
"""

import json
import warnings
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

BATCH_DIR = Path(__file__).parent.parent / "knowledge_base_backtest" / "batch_api"
DATA_DIR = Path(__file__).parent.parent / "data" / "historical"
OUTPUT_DIR = (
    Path(__file__).parent.parent
    / "research"
    / "archive"
    / "root_legacy_artifacts_2026_05_31"
    / "generated"
    / "sprint_alpha"
)

PRIMARY_BATCH = "msgbatch_01WUZbzFQniomk49SoLRAsPg"

ALL_XAU_BATCHES = [
    'msgbatch_018GNt2yH8hrrj1BV3Mf35Q7', 'msgbatch_0195ug8PMEQvUM2pgrZGdkbB',
    'msgbatch_01BNRwLoPRLjDs8XyAXx25XU', 'msgbatch_01HJEdo4gP2s5nd9hrgtJUHK',
    'msgbatch_01KqQJoECovg19XS3mRf7XSQ', 'msgbatch_01M9NW1bUnhF4Zf6g3VrNR8g',
    'msgbatch_01NNvwcdiUQwUU9c2x7qbVjD', 'msgbatch_01PeezeEy1M3LiNHbKwfaj6o',
    'msgbatch_01VCZZM7cCZhW9Nb9MybySZq', 'msgbatch_01WUZbzFQniomk49SoLRAsPg',
    'msgbatch_01WXewYLHYVXzTeuJnq2vzHR', 'msgbatch_01WgP6eewwdQd8UgVemLH4cN',
]

MAX_SIM_CANDLES = 16  # ~16 H1 candles ≈ 16 hours, matches median real hold


def load_h1_data():
    df = pd.read_csv(DATA_DIR / "XAUUSD_H1.csv")
    df['time'] = pd.to_datetime(df['time'])
    df['time_utc'] = df['time'] - pd.Timedelta(hours=2)
    return df


def load_trade_outcomes():
    seen = {}
    for bid in ALL_XAU_BATCHES:
        fpath = BATCH_DIR / f"{bid}_results.json"
        if not fpath.exists():
            continue
        with open(fpath) as f:
            data = json.load(f)
        if not isinstance(data, list):
            continue
        for day in data:
            if not isinstance(day, dict) or not day.get('trade_taken'):
                continue
            for t in day.get('trades', []):
                if isinstance(t, dict):
                    tid = t.get('trade_id', '')
                    if tid not in seen or (t.get('entry_price') and not seen[tid].get('entry_price')):
                        seen[tid] = {**t, 'date': day['date']}
    return seen


def load_candidate_entries():
    raw_path = BATCH_DIR / f"{PRIMARY_BATCH}_raw_results.json"
    with open(raw_path) as f:
        raw = json.load(f)

    candidates = []
    for key, val in raw.items():
        text = val.get('text', '') if isinstance(val, dict) else str(val)
        try:
            parsed = json.loads(text)
        except:
            continue
        if not isinstance(parsed, dict):
            continue
        decision = parsed.get('decision', '')
        if decision not in ('CANDIDATE', 'ENTER_LONG', 'ENTER_SHORT'):
            continue

        reasoning = parsed.get('reasoning', {}) or {}
        h1 = reasoning.get('h1_setup', {}) or {}
        tp = parsed.get('trade_parameters', {}) or {}

        if not tp.get('entry_price') or not tp.get('stop_loss'):
            continue

        # Parse key: "YYYY-MM-DD_kz_HHMM"
        key_parts = key.rsplit('_', 1)
        time_part = key_parts[1] if len(key_parts) > 1 else '0000'
        prefix_parts = key_parts[0].rsplit('_', 1)
        date_str = prefix_parts[0]
        kz = prefix_parts[1] if len(prefix_parts) > 1 else 'unknown'

        candidates.append({
            'key': key, 'date': date_str, 'kz': kz,
            'framework': parsed.get('framework', ''),
            'confidence': parsed.get('confidence_score', 0),
            'direction': tp.get('direction', ''),
            'entry_price': float(tp['entry_price']),
            'stop_loss': float(tp['stop_loss']),
            'take_profit_1': float(tp.get('take_profit_1', 0)),
            'sl_distance': abs(float(tp['entry_price']) - float(tp['stop_loss'])),
            'fib_pct': h1.get('fib_retracement_pct'),
            'time_part': time_part,
        })
    return candidates


def simulate_h1(h1_df, entry_time, direction, entry_price, stop_loss, take_profit):
    """Simulate trade on H1 candles. Returns 'WIN', 'LOSS', or 'TIMEOUT'."""
    mask = h1_df['time_utc'] >= entry_time
    if mask.sum() == 0:
        return 'TIMEOUT'
    start_idx = mask.idxmax()
    end_idx = min(start_idx + MAX_SIM_CANDLES, len(h1_df))

    for idx in range(start_idx + 1, end_idx):
        h = h1_df.iloc[idx]['high']
        l = h1_df.iloc[idx]['low']
        if direction == 'LONG':
            if h >= take_profit:
                return 'WIN'
            if l <= stop_loss:
                return 'LOSS'
        else:
            if l <= take_profit:
                return 'WIN'
            if h >= stop_loss:
                return 'LOSS'
    return 'TIMEOUT'


def estimate_impulse_range(entry_price, stop_loss, direction, fib_pct):
    """
    Estimate the impulse (swing) range from known parameters.
    entry is at fib_pct retrace from impulse terminus.
    SL is at impulse origin + small buffer.
    """
    if fib_pct is None or fib_pct <= 0 or fib_pct >= 100:
        fib_pct = 78.5  # default assumption
    fib = fib_pct / 100.0
    sl_dist = abs(entry_price - stop_loss)

    # For LONG: entry = high - fib * range, SL ≈ low = high - range
    # sl_dist = entry - SL = (high - fib*range) - (high - range) = range*(1 - fib)
    # So range = sl_dist / (1 - fib)
    if (1 - fib) > 0.05:
        imp_range = sl_dist / (1 - fib)
    else:
        imp_range = sl_dist * 5

    if direction == 'LONG':
        imp_low = stop_loss
        imp_high = imp_low + imp_range
    else:
        imp_high = stop_loss
        imp_low = imp_high - imp_range

    return imp_high, imp_low, imp_range


def run_analysis():
    print("Loading data...")
    h1_df = load_h1_data()
    trade_outcomes = load_trade_outcomes()
    candidates = load_candidate_entries()

    print(f"  H1 candles: {len(h1_df)}")
    print(f"  Trade outcomes (deduped): {len(trade_outcomes)}")
    print(f"  Candidate entries (from raw): {len(candidates)}")

    # Deduplicate candidates: 1 per date+kz (highest confidence, ob_retest preferred)
    groups = defaultdict(list)
    for c in candidates:
        groups[(c['date'], c['kz'])].append(c)

    unique_events = []
    for (date, kz), cands in groups.items():
        ob_cands = [c for c in cands if c['framework'] == 'ob_retest'] or cands
        best = max(ob_cands, key=lambda c: c.get('confidence', 0))
        unique_events.append(best)
    unique_events.sort(key=lambda x: (x['date'], x['kz']))

    # Match to actual trades
    for ev in unique_events:
        ev['has_actual_trade'] = False
        ev['actual_outcome'] = None
        for tid, t in trade_outcomes.items():
            if t.get('date') == ev['date'] and t.get('kill_zone', '').lower() == ev['kz'].lower():
                ev['has_actual_trade'] = True
                ev['actual_outcome'] = t.get('outcome', 'UNKNOWN')
                break

    traded = [e for e in unique_events if e['has_actual_trade']]
    n_traded = len(traded)
    n_wins_actual = sum(1 for e in traded if e['actual_outcome'] in ('WIN', 'BREAKEVEN'))
    print(f"\n  Unique BOS events: {len(unique_events)}")
    print(f"  Became actual trades: {n_traded}")
    print(f"  Actual WR: {n_wins_actual}/{n_traded} = {n_wins_actual/n_traded*100:.1f}%")

    # ─── Run simulations ───
    THRESHOLDS = [0.80, 0.85, 0.90, 0.95]

    # Results containers
    res = {
        'ai_selected': {'wins': 0, 'losses': 0, 'timeout': 0, 'n': 0},
        'all_ob_sim': {'wins': 0, 'losses': 0, 'timeout': 0, 'n': 0},
        'ai_ob_sim': {'wins': 0, 'losses': 0, 'timeout': 0, 'n': 0},  # same trades, simulated
    }
    for t in THRESHOLDS:
        res[f'ret_{int(t*100)}'] = {'wins': 0, 'losses': 0, 'timeout': 0, 'n': 0, 'no_fill': 0}

    print("\nSimulating...")

    for ev in unique_events:
        direction = ev['direction']
        entry_price = ev['entry_price']
        stop_loss = ev['stop_loss']
        tp1 = ev['take_profit_1']
        sl_dist = ev['sl_distance']

        if not direction or sl_dist <= 0 or tp1 <= 0:
            continue

        # Parse entry time
        try:
            hour = int(ev['time_part'][:2])
            minute = int(ev['time_part'][2:])
            entry_time = pd.Timestamp(f"{ev['date']} {hour:02d}:{minute:02d}:00")
        except:
            continue

        # Estimate impulse range
        imp_high, imp_low, imp_range = estimate_impulse_range(
            entry_price, stop_loss, direction, ev['fib_pct'])

        if imp_range <= 0:
            continue

        # --- AI-selected: actual outcome ---
        if ev['has_actual_trade']:
            res['ai_selected']['n'] += 1
            if ev['actual_outcome'] in ('WIN', 'BREAKEVEN'):
                res['ai_selected']['wins'] += 1
            else:
                res['ai_selected']['losses'] += 1

            # Also simulate the SAME AI-selected trades on H1 for calibration
            sim_out = simulate_h1(h1_df, entry_time, direction, entry_price, stop_loss, tp1)
            res['ai_ob_sim']['n'] += 1
            res['ai_ob_sim'][{'WIN': 'wins', 'LOSS': 'losses', 'TIMEOUT': 'timeout'}[sim_out]] += 1

        # --- All OB entries (no AI filter), simulated ---
        sim_out = simulate_h1(h1_df, entry_time, direction, entry_price, stop_loss, tp1)
        res['all_ob_sim']['n'] += 1
        res['all_ob_sim'][{'WIN': 'wins', 'LOSS': 'losses', 'TIMEOUT': 'timeout'}[sim_out]] += 1

        # --- Dumb baselines: deeper entry, SAME SL and TP prices ---
        for thresh in THRESHOLDS:
            key = f'ret_{int(thresh*100)}'

            if direction == 'LONG':
                retrace_level = imp_high - thresh * imp_range  # lower than OB entry
            else:
                retrace_level = imp_low + thresh * imp_range  # higher than OB entry

            # Check if price actually retraces to this level in the H1 data
            # Search within a window around the entry time
            mask = h1_df['time_utc'] >= entry_time - pd.Timedelta(hours=2)
            if mask.sum() == 0:
                res[key]['no_fill'] += 1
                continue

            start_idx = mask.idxmax()
            search_end = min(start_idx + 48, len(h1_df))  # 48 H1 = 2 days

            retrace_found = False
            retrace_idx = None
            for idx in range(start_idx, search_end):
                row = h1_df.iloc[idx]
                if direction == 'LONG' and row['low'] <= retrace_level:
                    retrace_found = True
                    retrace_idx = idx
                    break
                elif direction == 'SHORT' and row['high'] >= retrace_level:
                    retrace_found = True
                    retrace_idx = idx
                    break

            if not retrace_found:
                res[key]['no_fill'] += 1
                continue

            # Simulate with SAME SL and TP prices, different entry
            retrace_time = h1_df.iloc[retrace_idx]['time_utc']
            sim_out = simulate_h1(h1_df, retrace_time, direction,
                                 retrace_level, stop_loss, tp1)

            res[key]['n'] += 1
            res[key][{'WIN': 'wins', 'LOSS': 'losses', 'TIMEOUT': 'timeout'}[sim_out]] += 1

    return res, unique_events


def format_results(res, events):
    lines = []
    lines.append("# Task 1 RERUN: Dumb Momentum Baseline — Real Batch Population\n")

    lines.append("## Method\n")
    lines.append("Used the primary XAUUSD batch (174 trading days, 2024-04-01 to 2026-03-13):")
    lines.append("- Extracted **all CANDIDATE entries** from raw API responses (688 entries)")
    lines.append("- Deduplicated to **1 per date+KZ** (219 unique BOS events)")
    lines.append("- Matched to actual trade outcomes (139 became real trades)")
    lines.append("- Estimated impulse range from entry price, SL, and Fibonacci retracement %")
    lines.append("- Simulated alternatives on H1 data with **same SL and TP price levels**")
    lines.append(f"- Simulation window: {MAX_SIM_CANDLES} H1 candles (matches median real hold time)\n")

    lines.append("## Simulation Calibration\n")
    lines.append("To validate the H1 simulation, we ran the **same AI-selected trades** through both")
    lines.append("actual outcomes and simulation:\n")

    ai = res['ai_selected']
    ai_sim = res['ai_ob_sim']
    ai_resolved = ai['wins'] + ai['losses']
    ai_sim_resolved = ai_sim['wins'] + ai_sim['losses']
    ai_wr = ai['wins'] / ai_resolved * 100 if ai_resolved > 0 else 0
    ai_sim_wr = ai_sim['wins'] / ai_sim_resolved * 100 if ai_sim_resolved > 0 else 0

    lines.append(f"| Method | n | Resolved | Wins | WR (resolved) |")
    lines.append(f"|---|---|---|---|---|")
    lines.append(f"| Actual outcomes | {ai['n']} | {ai_resolved} | {ai['wins']} | **{ai_wr:.1f}%** |")
    lines.append(f"| H1 simulation | {ai_sim['n']} | {ai_sim_resolved} | {ai_sim['wins']} | {ai_sim_wr:.1f}% |")
    lines.append(f"| Simulation gap | — | — | — | {ai_sim_wr - ai_wr:+.1f}pp |")

    sim_bias = ai_sim_wr - ai_wr  # positive = sim is too generous
    lines.append(f"\nThe simulation is {abs(sim_bias):.1f}pp {'too generous' if sim_bias > 0 else 'too conservative'}.")
    lines.append(f"All simulated WRs should be read with this ~{abs(sim_bias):.0f}pp calibration in mind.\n")

    # Main results table
    lines.append("## Results\n")
    lines.append("| Method | Events | Filled | Resolved | Wins | WR (resolved) | WR (calibrated) |")
    lines.append("|---|---|---|---|---|---|---|")

    def row(label, r, is_actual=False, no_fill=0, bold=False):
        resolved = r['wins'] + r['losses']
        wr = r['wins'] / resolved * 100 if resolved > 0 else 0
        cal_wr = wr if is_actual else wr - sim_bias
        filled = r['n']
        total = filled + no_fill
        b = "**" if bold else ""
        actual_note = " (actual)" if is_actual else ""
        return f"| {b}{label}{b} | {total} | {filled} | {resolved} | {r['wins']} | {b}{wr:.1f}%{actual_note}{b} | {b}{cal_wr:.1f}%{b} |"

    lines.append(row("AI-selected (real system)", ai, is_actual=True, bold=True))
    lines.append(row("All OB entries, no AI filter", res['all_ob_sim']))

    for t in [80, 85, 90, 95]:
        r = res[f'ret_{t}']
        nf = r.get('no_fill', 0)
        lines.append(row(f"{t}% retrace baseline", r, no_fill=nf))

    # Q1: Does AI add value?
    lines.append("\n## Q1: Does the AI add value?\n")

    all_ob = res['all_ob_sim']
    all_ob_resolved = all_ob['wins'] + all_ob['losses']
    all_ob_wr = all_ob['wins'] / all_ob_resolved * 100 if all_ob_resolved > 0 else 0
    all_ob_cal = all_ob_wr - sim_bias

    lines.append(f"- **AI-selected WR**: {ai_wr:.1f}% ({ai['wins']}/{ai_resolved} actual)")
    lines.append(f"- **All OB entries (sim)**: {all_ob_wr:.1f}% raw, **{all_ob_cal:.1f}% calibrated** ({all_ob['wins']}/{all_ob_resolved})")
    delta = ai_wr - all_ob_cal
    lines.append(f"- **AI advantage**: {delta:+.1f}pp")

    # Fisher's on raw simulated (same method, apples-to-apples)
    # Compare AI-sim vs all-OB-sim
    if ai_sim_resolved > 0 and all_ob_resolved > 0:
        table = [[ai_sim['wins'], ai_sim['losses']], [all_ob['wins'], all_ob['losses']]]
        _, p = stats.fisher_exact(table)
        lines.append(f"- Fisher p (AI-sim vs All-OB-sim, apples-to-apples): {p:.4f}")

    if delta > 5:
        lines.append(f"\n**YES, the AI adds {delta:.0f}pp.** The confidence scoring and multi-timeframe")
        lines.append(f"evaluation successfully filters out weak setups from the candidate pool.\n")
    elif delta > 0:
        lines.append(f"\n**MARGINAL.** AI adds only ~{delta:.0f}pp — less than expected.\n")
    else:
        lines.append(f"\n**NO.** The AI selection does not outperform unfiltered OB entries.\n")

    # Q2: Does OB zone add value over dumb pullback?
    lines.append("## Q2: Does the OB zone add value over generic deep pullback?\n")

    lines.append("| Comparison | OB sim WR | Baseline sim WR | Delta | Fisher p |")
    lines.append("|---|---|---|---|---|")

    for t in [80, 85, 90, 95]:
        r = res[f'ret_{t}']
        r_resolved = r['wins'] + r['losses']
        if all_ob_resolved > 0 and r_resolved > 0:
            r_wr = r['wins'] / r_resolved * 100
            delta_ob = all_ob_wr - r_wr
            tab = [[all_ob['wins'], all_ob['losses']], [r['wins'], r['losses']]]
            _, p = stats.fisher_exact(tab)
            sig = " *" if p < 0.05 else ""
            lines.append(f"| OB vs {t}% retrace | {all_ob_wr:.1f}% | {r_wr:.1f}% | {delta_ob:+.1f}pp | {p:.4f}{sig} |")

    # Find best dumb baseline
    best_t, best_wr = None, 0
    for t in [80, 85, 90, 95]:
        r = res[f'ret_{t}']
        r_resolved = r['wins'] + r['losses']
        if r_resolved > 0:
            wr = r['wins'] / r_resolved * 100
            if wr > best_wr:
                best_wr = wr
                best_t = t

    ob_vs_best = all_ob_wr - best_wr if best_t else 0

    if ob_vs_best > 5:
        lines.append(f"\n**YES.** OB zone ({all_ob_wr:.1f}%) outperforms best dumb baseline ({best_t}% at {best_wr:.1f}%)")
        lines.append(f"by {ob_vs_best:+.1f}pp. Zone identification provides meaningful precision.\n")
    elif ob_vs_best > -3:
        lines.append(f"\n**ROUGHLY EQUAL.** OB zone ({all_ob_wr:.1f}%) vs best baseline ({best_t}% at {best_wr:.1f}%)")
        lines.append(f"— only {ob_vs_best:+.1f}pp difference. Zone precision adds minimal value.\n")
    else:
        lines.append(f"\n**NO.** OB zone ({all_ob_wr:.1f}%) UNDERPERFORMS best baseline ({best_t}% at {best_wr:.1f}%)")
        lines.append(f"by {abs(ob_vs_best):.1f}pp. A generic deep pullback works better.\n")

    # Fill rate analysis
    lines.append("## Fill Rate Analysis\n")
    lines.append("Deeper retrace = better RR but lower fill probability:\n")
    lines.append("| Threshold | Fill Rate | Effective WR (filled × resolved WR) |")
    lines.append("|---|---|---|")

    total_events = len([e for e in events if e.get('direction') and e.get('sl_distance', 0) > 0])
    for t in [80, 85, 90, 95]:
        r = res[f'ret_{t}']
        filled = r['n']
        nf = r.get('no_fill', 0)
        total = filled + nf
        fill_rate = filled / total * 100 if total > 0 else 0
        r_resolved = r['wins'] + r['losses']
        wr = r['wins'] / r_resolved * 100 if r_resolved > 0 else 0
        effective = fill_rate / 100 * wr / 100 * 100
        lines.append(f"| {t}% | {fill_rate:.1f}% ({filled}/{total}) | {effective:.1f}% |")

    all_ob_fill = res['all_ob_sim']['n']
    all_ob_total = all_ob_fill  # OB always fills by definition (it's the entry point)
    lines.append(f"| OB zone | 100.0% ({all_ob_fill}/{all_ob_fill}) | {all_ob_wr:.1f}% |")

    # Value decomposition
    lines.append("\n## Value Chain Decomposition\n")

    if best_t:
        r = res[f'ret_{best_t}']
        r_resolved = r['wins'] + r['losses']
        base_wr = r['wins'] / r_resolved * 100 if r_resolved > 0 else 50
        base_cal = base_wr - sim_bias

        lines.append("| Component | WR (raw sim) | WR (calibrated) | Value Added |")
        lines.append("|---|---|---|---|")
        lines.append(f"| Momentum only (BOS + {best_t}% pullback) | {base_wr:.1f}% | {base_cal:.1f}% | baseline |")
        lines.append(f"| + OB zone precision | {all_ob_wr:.1f}% | {all_ob_cal:.1f}% | {all_ob_cal - base_cal:+.1f}pp |")
        lines.append(f"| + AI selection | — | {ai_wr:.1f}% | {ai_wr - all_ob_cal:+.1f}pp |")
        lines.append(f"| **Full system** | — | **{ai_wr:.1f}%** | **{ai_wr - base_cal:+.1f}pp total** |")

    lines.append("\n## So What?\n")
    lines.append("1. **Where does the edge come from?** This decomposition reveals whether the value is in")
    lines.append("   momentum (BOS detection), zone precision (OB identification), or AI selectivity.")
    lines.append("2. **Simplification opportunity**: If zone precision adds <3pp, the OB identification")
    lines.append("   step could be replaced with a simpler deep-pullback entry rule.")
    lines.append("3. **AI value**: The gap between unfiltered and AI-selected shows whether the")
    lines.append("   multi-timeframe evaluation and confidence scoring justify the API cost.")
    lines.append("4. **Note on fill rates**: Deeper entries have better RR but lower fill rates.")
    lines.append("   The effective WR (fill rate × conditional WR) is the true comparison metric.")

    return "\n".join(lines)


if __name__ == '__main__':
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("TASK 1 RERUN: Real Batch Population Analysis")
    print("=" * 70)

    results, events = run_analysis()
    doc = format_results(results, events)

    outpath = OUTPUT_DIR / "test_a_rerun_real_bos_results.md"
    with open(outpath, 'w') as f:
        f.write(doc)
    print(f"\nSaved to {outpath}")

    print("\n" + "=" * 70)
    print("QUICK SUMMARY")
    print("=" * 70)
    for method, r in results.items():
        resolved = r['wins'] + r['losses']
        wr = r['wins'] / resolved * 100 if resolved > 0 else 0
        nf = r.get('no_fill', 0)
        print(f"  {method:25s}: {r['n']:4d} filled (+{nf} no-fill), {resolved:4d} resolved, WR={wr:.1f}%")
