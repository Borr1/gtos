#!/usr/bin/env python3
"""Phase 1: Trade Index Analyses — Monte Carlo, Rolling Stability, Autocorrelation, Drawdowns, DOW×KZ, Timing."""
import json, csv, os, sys, math, random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from scipy import stats as scipy_stats

BASE = Path('/Users/borr/Documents/trading/gold-agent')
OUT = BASE / 'knowledge_base_backtest' / 'analysis' / 'deep_dive_20260406'

with open(OUT / 'trade_index_enriched.json') as f:
    data = json.load(f)
trades = data['trades']

# Sort chronologically
trades.sort(key=lambda t: (t['date'], t['kill_zone']))
r_multiples = [t['r_multiple'] for t in trades]
outcomes = [1 if t['outcome'] == 'WIN' else 0 for t in trades]

# XAUUSD only
xau_trades = [t for t in trades if t['symbol'] == 'XAUUSD']
xau_r = [t['r_multiple'] for t in xau_trades]
xau_outcomes = [1 if t['outcome'] == 'WIN' else 0 for t in xau_trades]

###############################################################################
# 1A: Monte Carlo Equity Curve
###############################################################################
def monte_carlo(r_values, n_sims=10000, n_trades=100, label="combined"):
    """Bootstrap Monte Carlo simulation."""
    random.seed(42)
    np.random.seed(42)

    r_arr = np.array(r_values, dtype=float)
    risk_levels = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    starting_equity = 100000

    results = {}

    for risk_pct in risk_levels:
        risk = risk_pct / 100.0

        # Track stats
        pass_8_before_5 = 0
        pass_8_before_10 = 0
        max_dd_exceeds_5 = 0
        max_dd_exceeds_10 = 0
        final_equities = []
        max_consec_losses_all = []
        trades_to_3pct = []

        for sim in range(n_sims):
            # Sample with replacement
            sampled = np.random.choice(r_arr, size=n_trades, replace=True)

            equity = starting_equity
            peak = equity
            hit_8 = False
            hit_neg5 = False
            hit_neg10 = False
            max_dd = 0
            consec_loss = 0
            max_consec = 0
            reached_3 = None

            for i, r in enumerate(sampled):
                pnl = equity * risk * r
                equity += pnl

                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd

                gain_pct = (equity - starting_equity) / starting_equity
                if gain_pct >= 0.03 and reached_3 is None:
                    reached_3 = i + 1

                if gain_pct >= 0.08 and not hit_8:
                    hit_8 = True
                if dd >= 0.05 and not hit_neg5:
                    hit_neg5 = True
                if dd >= 0.10 and not hit_neg10:
                    hit_neg10 = True

                # Consecutive losses
                if r < 0:
                    consec_loss += 1
                    max_consec = max(max_consec, consec_loss)
                else:
                    consec_loss = 0

            # Score outcomes
            if hit_8 and not hit_neg5:
                pass_8_before_5 += 1
            elif hit_8:
                # Check order: did +8% come before -5%?
                # Re-simulate to check order
                eq2 = starting_equity
                pk2 = eq2
                first_8 = None
                first_neg5 = None
                for i, r in enumerate(sampled):
                    eq2 += eq2 * risk * r
                    if eq2 > pk2: pk2 = eq2
                    dd2 = (pk2 - eq2) / pk2
                    g2 = (eq2 - starting_equity) / starting_equity
                    if g2 >= 0.08 and first_8 is None: first_8 = i
                    if dd2 >= 0.05 and first_neg5 is None: first_neg5 = i
                if first_8 is not None and (first_neg5 is None or first_8 < first_neg5):
                    pass_8_before_5 += 1

            if hit_8 and not hit_neg10:
                pass_8_before_10 += 1
            elif hit_8:
                eq2 = starting_equity
                pk2 = eq2
                first_8 = None
                first_neg10 = None
                for i, r in enumerate(sampled):
                    eq2 += eq2 * risk * r
                    if eq2 > pk2: pk2 = eq2
                    dd2 = (pk2 - eq2) / pk2
                    g2 = (eq2 - starting_equity) / starting_equity
                    if g2 >= 0.08 and first_8 is None: first_8 = i
                    if dd2 >= 0.10 and first_neg10 is None: first_neg10 = i
                if first_8 is not None and (first_neg10 is None or first_8 < first_neg10):
                    pass_8_before_10 += 1

            if max_dd >= 0.05:
                max_dd_exceeds_5 += 1
            if max_dd >= 0.10:
                max_dd_exceeds_10 += 1

            final_equities.append(equity)
            max_consec_losses_all.append(max_consec)
            if reached_3 is not None:
                trades_to_3pct.append(reached_3)

        fe = np.array(final_equities)
        cl = np.array(max_consec_losses_all)

        results[risk_pct] = {
            'P_8_before_5': round(pass_8_before_5 / n_sims, 4),
            'P_8_before_10': round(pass_8_before_10 / n_sims, 4),
            'P_dd_exceeds_5': round(max_dd_exceeds_5 / n_sims, 4),
            'P_dd_exceeds_10': round(max_dd_exceeds_10 / n_sims, 4),
            'median_final_equity': round(float(np.median(fe)), 2),
            'pct5_final_equity': round(float(np.percentile(fe, 5)), 2),
            'pct95_final_equity': round(float(np.percentile(fe, 95)), 2),
            'max_consec_loss_95th': int(np.percentile(cl, 95)),
            'median_trades_to_3pct': int(np.median(trades_to_3pct)) if trades_to_3pct else None,
            'pct_reaching_3pct': round(len(trades_to_3pct) / n_sims, 4),
        }

    # Kelly criterion
    mean_r = float(np.mean(r_arr))
    var_r = float(np.var(r_arr))
    kelly_full = mean_r / var_r if var_r > 0 else 0
    kelly_half = kelly_full / 2

    # Block bootstrap (block_size=5)
    block_size = 5
    n_blocks = n_trades // block_size
    block_pass = 0
    risk = 1.0 / 100
    np.random.seed(42)

    for sim in range(n_sims):
        equity = starting_equity
        peak = equity
        hit_8 = False
        hit_neg5 = False
        first_8 = None
        first_neg5 = None

        trade_idx = 0
        for _ in range(n_blocks):
            start = np.random.randint(0, len(r_arr) - block_size + 1)
            block = r_arr[start:start+block_size]
            for r in block:
                equity += equity * risk * r
                if equity > peak: peak = equity
                dd = (peak - equity) / peak
                g = (equity - starting_equity) / starting_equity
                if g >= 0.08 and first_8 is None: first_8 = trade_idx
                if dd >= 0.05 and first_neg5 is None: first_neg5 = trade_idx
                trade_idx += 1

        if first_8 is not None and (first_neg5 is None or first_8 < first_neg5):
            block_pass += 1

    block_p = round(block_pass / n_sims, 4)
    iid_p = results[1.0]['P_8_before_5']
    autocorr_flag = abs(block_p - iid_p) > 0.05

    return {
        'label': label,
        'n_trades_input': len(r_values),
        'mean_r': round(mean_r, 4),
        'win_rate': round(sum(1 for r in r_values if r > 0) / len(r_values), 4),
        'profit_factor': round(sum(r for r in r_values if r > 0) / abs(sum(r for r in r_values if r < 0)), 4) if sum(r for r in r_values if r < 0) != 0 else float('inf'),
        'kelly_full': round(kelly_full, 4),
        'kelly_half': round(kelly_half, 4),
        'kelly_full_pct': round(kelly_full * 100, 2),
        'kelly_half_pct': round(kelly_half * 100, 2),
        'risk_level_results': results,
        'block_bootstrap_1pct': {
            'P_8_before_5_block': block_p,
            'P_8_before_5_iid': iid_p,
            'difference_pp': round((block_p - iid_p) * 100, 2),
            'autocorrelation_detected': autocorr_flag,
        }
    }

###############################################################################
# 1B: Rolling Edge Stability
###############################################################################
def rolling_stability():
    window = 20
    rolling = []

    for i in range(len(r_multiples) - window + 1):
        chunk = r_multiples[i:i+window]
        wins = sum(1 for r in chunk if r > 0)
        pos = sum(r for r in chunk if r > 0)
        neg = abs(sum(r for r in chunk if r < 0))

        rolling.append({
            'start_idx': i,
            'end_idx': i + window - 1,
            'start_date': trades[i]['date'],
            'end_date': trades[i+window-1]['date'],
            'win_rate': round(wins / window, 4),
            'mean_r': round(sum(chunk) / window, 4),
            'total_r': round(sum(chunk), 4),
            'profit_factor': round(pos / neg, 4) if neg > 0 else float('inf'),
        })

    # Expanding
    expanding = []
    for i in range(1, len(r_multiples) + 1):
        chunk = r_multiples[:i]
        wins = sum(1 for r in chunk if r > 0)
        pos = sum(r for r in chunk if r > 0)
        neg = abs(sum(r for r in chunk if r < 0))
        expanding.append({
            'trade_n': i,
            'date': trades[i-1]['date'],
            'cumulative_wr': round(wins / i, 4),
            'cumulative_mean_r': round(sum(chunk) / i, 4),
            'cumulative_total_r': round(sum(chunk), 4),
            'cumulative_pf': round(pos / neg, 4) if neg > 0 else float('inf'),
        })

    # Best/worst windows
    best = max(rolling, key=lambda x: x['total_r'])
    worst = min(rolling, key=lambda x: x['total_r'])
    neg_windows = sum(1 for w in rolling if w['total_r'] < 0)

    # First-half vs second-half
    mid = len(r_multiples) // 2
    h1 = r_multiples[:mid]
    h2 = r_multiples[mid:]

    return {
        'rolling_windows': rolling,
        'expanding_curve': expanding,
        'best_window': best,
        'worst_window': worst,
        'negative_expectancy_windows': neg_windows,
        'total_windows': len(rolling),
        'first_half': {
            'n': len(h1),
            'win_rate': round(sum(1 for r in h1 if r > 0) / len(h1), 4),
            'mean_r': round(sum(h1) / len(h1), 4),
            'total_r': round(sum(h1), 4),
        },
        'second_half': {
            'n': len(h2),
            'win_rate': round(sum(1 for r in h2 if r > 0) / len(h2), 4),
            'mean_r': round(sum(h2) / len(h2), 4),
            'total_r': round(sum(h2), 4),
        }
    }

###############################################################################
# 1C: Trade Autocorrelation
###############################################################################
def autocorrelation_analysis():
    # Binary outcomes
    binary = np.array(outcomes, dtype=float)
    r_arr = np.array(r_multiples, dtype=float)

    # Autocorrelation
    binary_ac = {}
    r_ac = {}
    for lag in [1, 2, 3]:
        if len(binary) > lag:
            c = np.corrcoef(binary[:-lag], binary[lag:])[0, 1]
            binary_ac[f'lag_{lag}'] = round(float(c), 4) if not np.isnan(c) else None
    for lag in [1, 2]:
        if len(r_arr) > lag:
            c = np.corrcoef(r_arr[:-lag], r_arr[lag:])[0, 1]
            r_ac[f'lag_{lag}'] = round(float(c), 4) if not np.isnan(c) else None

    # Wald-Wolfowitz runs test
    median_r = np.median(binary)
    signs = ['W' if b > median_r else 'L' for b in binary]
    runs = 1
    for i in range(1, len(signs)):
        if signs[i] != signs[i-1]:
            runs += 1

    n1 = sum(1 for s in signs if s == 'W')
    n2 = sum(1 for s in signs if s == 'L')
    n = n1 + n2
    if n1 > 0 and n2 > 0:
        expected_runs = 1 + (2 * n1 * n2) / n
        var_runs = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))
        if var_runs > 0:
            z_runs = (runs - expected_runs) / math.sqrt(var_runs)
            p_runs = 2 * (1 - scipy_stats.norm.cdf(abs(z_runs)))
        else:
            z_runs = 0
            p_runs = 1
    else:
        expected_runs = runs
        z_runs = 0
        p_runs = 1

    # Streaks
    streaks_w = []
    streaks_l = []
    current = 0
    current_type = None
    for o in outcomes:
        t = 'W' if o == 1 else 'L'
        if t == current_type:
            current += 1
        else:
            if current_type is not None:
                (streaks_w if current_type == 'W' else streaks_l).append(current)
            current = 1
            current_type = t
    if current_type:
        (streaks_w if current_type == 'W' else streaks_l).append(current)

    return {
        'binary_autocorrelation': binary_ac,
        'r_multiple_autocorrelation': r_ac,
        'wald_wolfowitz_runs_test': {
            'observed_runs': runs,
            'expected_runs': round(expected_runs, 2),
            'z_statistic': round(z_runs, 4),
            'p_value': round(p_runs, 4),
            'conclusion': 'random' if p_runs > 0.05 else 'non-random (clustered)' if z_runs < 0 else 'non-random (alternating)',
        },
        'longest_win_streak': max(streaks_w) if streaks_w else 0,
        'longest_loss_streak': max(streaks_l) if streaks_l else 0,
        'all_win_streaks': sorted(streaks_w, reverse=True)[:5],
        'all_loss_streaks': sorted(streaks_l, reverse=True)[:5],
    }

###############################################################################
# 1D: Drawdown Duration Analysis
###############################################################################
def drawdown_analysis():
    # Build equity curve in R-units
    equity_r = [0]
    for r in r_multiples:
        equity_r.append(equity_r[-1] + r)

    # Find drawdowns
    peak = 0
    drawdowns = []
    in_dd = False
    dd_start = None
    dd_depth = 0

    for i, eq in enumerate(equity_r):
        if eq > peak:
            if in_dd:
                # Drawdown ended
                drawdowns.append({
                    'start_trade': dd_start,
                    'end_trade': i,
                    'depth_r': round(dd_depth, 4),
                    'duration_trades': i - dd_start,
                    'start_date': trades[dd_start]['date'] if dd_start < len(trades) else None,
                    'end_date': trades[min(i, len(trades)-1)]['date'],
                })
                in_dd = False
            peak = eq
            dd_depth = 0
        else:
            dd = peak - eq
            if dd > 0:
                if not in_dd:
                    dd_start = i
                    in_dd = True
                dd_depth = max(dd_depth, dd)

    # Still in drawdown at end
    if in_dd:
        drawdowns.append({
            'start_trade': dd_start,
            'end_trade': len(equity_r) - 1,
            'depth_r': round(dd_depth, 4),
            'duration_trades': len(equity_r) - 1 - dd_start,
            'start_date': trades[dd_start]['date'] if dd_start < len(trades) else None,
            'end_date': trades[-1]['date'],
            'still_in_drawdown': True,
        })

    max_dd = max(drawdowns, key=lambda d: d['depth_r']) if drawdowns else None
    avg_depth = np.mean([d['depth_r'] for d in drawdowns]) if drawdowns else 0
    avg_duration = np.mean([d['duration_trades'] for d in drawdowns]) if drawdowns else 0

    # Convert to dollars at 1% risk
    risk_pct = 0.01
    equity_dollar = [100000]
    for r in r_multiples:
        pnl = equity_dollar[-1] * risk_pct * r
        equity_dollar.append(equity_dollar[-1] + pnl)

    peak_d = 100000
    max_dd_dollar = 0
    max_dd_pct = 0
    for eq in equity_dollar:
        if eq > peak_d:
            peak_d = eq
        dd_d = peak_d - eq
        dd_p = dd_d / peak_d
        max_dd_dollar = max(max_dd_dollar, dd_d)
        max_dd_pct = max(max_dd_pct, dd_p)

    return {
        'equity_curve_r': [round(e, 4) for e in equity_r],
        'final_equity_r': round(equity_r[-1], 4),
        'drawdowns': drawdowns,
        'max_drawdown': max_dd,
        'average_drawdown_depth_r': round(float(avg_depth), 4),
        'average_drawdown_duration_trades': round(float(avg_duration), 1),
        'total_drawdown_periods': len(drawdowns),
        'dollar_analysis_1pct_risk': {
            'starting_equity': 100000,
            'final_equity': round(equity_dollar[-1], 2),
            'max_drawdown_dollars': round(max_dd_dollar, 2),
            'max_drawdown_pct': round(max_dd_pct * 100, 2),
            'exceeds_5pct_limit': max_dd_pct > 0.05,
            'exceeds_10pct_limit': max_dd_pct > 0.10,
        }
    }

###############################################################################
# 1E: DOW × KZ Matrix
###############################################################################
def dow_kz_matrix():
    dow_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri'}
    matrix = {}

    for t in trades:
        dt = datetime.strptime(t['date'], '%Y-%m-%d')
        dow = dt.weekday()
        dow_name = dow_names.get(dow, str(dow))
        kz = t['kill_zone']
        key = f"{dow_name}_{kz}"

        if key not in matrix:
            matrix[key] = {'n': 0, 'wins': 0, 'total_r': 0, 'r_values': []}
        matrix[key]['n'] += 1
        if t['outcome'] == 'WIN':
            matrix[key]['wins'] += 1
        matrix[key]['total_r'] += t['r_multiple']
        matrix[key]['r_values'].append(t['r_multiple'])

    results = {}
    for key, v in matrix.items():
        results[key] = {
            'n': v['n'],
            'win_rate': round(v['wins'] / v['n'], 4) if v['n'] > 0 else 0,
            'mean_r': round(v['total_r'] / v['n'], 4) if v['n'] > 0 else 0,
            'total_r': round(v['total_r'], 4),
            'flag_low_n': v['n'] < 10,
        }

    # DOW aggregates
    dow_agg = {}
    for t in trades:
        dt = datetime.strptime(t['date'], '%Y-%m-%d')
        dow = dow_names.get(dt.weekday(), str(dt.weekday()))
        if dow not in dow_agg:
            dow_agg[dow] = {'n': 0, 'wins': 0, 'total_r': 0}
        dow_agg[dow]['n'] += 1
        if t['outcome'] == 'WIN':
            dow_agg[dow]['wins'] += 1
        dow_agg[dow]['total_r'] += t['r_multiple']

    for k in dow_agg:
        n = dow_agg[k]['n']
        dow_agg[k]['win_rate'] = round(dow_agg[k]['wins'] / n, 4) if n > 0 else 0
        dow_agg[k]['mean_r'] = round(dow_agg[k]['total_r'] / n, 4) if n > 0 else 0

    # Fisher exact on best vs worst DOW
    best_dow = max(dow_agg.items(), key=lambda x: x[1]['win_rate'])
    worst_dow = min(dow_agg.items(), key=lambda x: x[1]['win_rate'])

    a = best_dow[1]['wins']
    b = best_dow[1]['n'] - a
    c = worst_dow[1]['wins']
    d = worst_dow[1]['n'] - c

    _, fisher_p = scipy_stats.fisher_exact([[a, b], [c, d]])

    return {
        'matrix': results,
        'dow_aggregate': dow_agg,
        'best_dow': {'day': best_dow[0], **best_dow[1]},
        'worst_dow': {'day': worst_dow[0], **worst_dow[1]},
        'fisher_exact_best_vs_worst': {
            'p_value': round(fisher_p, 4),
            'significant_at_05': fisher_p < 0.05,
        }
    }

###############################################################################
# 1F: Trade Timing and Frequency
###############################################################################
def trade_timing():
    dates = sorted(set(t['date'] for t in trades))
    all_dates = [datetime.strptime(d, '%Y-%m-%d') for d in dates]

    gaps = []
    for i in range(1, len(all_dates)):
        gap = (all_dates[i] - all_dates[i-1]).days
        gaps.append(gap)

    # Monthly counts
    monthly = Counter()
    for t in trades:
        ym = t['date'][:7]
        monthly[ym] += 1

    # All months in range
    start = datetime.strptime(dates[0], '%Y-%m-%d')
    end = datetime.strptime(dates[-1], '%Y-%m-%d')
    all_months = []
    cur = start.replace(day=1)
    while cur <= end:
        ym = cur.strftime('%Y-%m')
        all_months.append(ym)
        if cur.month == 12:
            cur = cur.replace(year=cur.year+1, month=1)
        else:
            cur = cur.replace(month=cur.month+1)

    zero_months = [m for m in all_months if monthly.get(m, 0) == 0]
    monthly_counts = [monthly.get(m, 0) for m in all_months]

    return {
        'calendar_gaps_days': {
            'mean': round(np.mean(gaps), 1) if gaps else 0,
            'median': round(float(np.median(gaps)), 1) if gaps else 0,
            'max': max(gaps) if gaps else 0,
            'std': round(float(np.std(gaps)), 1) if gaps else 0,
            'min': min(gaps) if gaps else 0,
        },
        'longest_dry_spell_days': max(gaps) if gaps else 0,
        'monthly_trade_counts': dict(zip(all_months, monthly_counts)),
        'mean_trades_per_month': round(np.mean(monthly_counts), 1),
        'months_with_zero_trades': len(zero_months),
        'zero_trade_months': zero_months,
        'total_trading_months': len(all_months),
        'total_unique_trade_dates': len(dates),
    }

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 1: TRADE INDEX ANALYSES")
    print("=" * 60)

    # 1A: Monte Carlo
    print("\n--- 1A: Monte Carlo (Combined 129) ---")
    mc_combined = monte_carlo(r_multiples, label="combined_129")
    print(f"  Kelly full: {mc_combined['kelly_full_pct']}%, half: {mc_combined['kelly_half_pct']}%")
    print(f"  At 1.0% risk: P(+8% before -5%) = {mc_combined['risk_level_results'][1.0]['P_8_before_5']}")

    print("\n--- 1A: Monte Carlo (XAUUSD 105) ---")
    mc_xau = monte_carlo(xau_r, label="xauusd_105")
    print(f"  Kelly full: {mc_xau['kelly_full_pct']}%, half: {mc_xau['kelly_half_pct']}%")

    mc_result = {'combined': mc_combined, 'xauusd': mc_xau}
    with open(OUT / 'monte_carlo_20260406.json', 'w') as f:
        json.dump(mc_result, f, indent=2, default=str)

    # 1B: Rolling Stability
    print("\n--- 1B: Rolling Stability ---")
    rs = rolling_stability()
    print(f"  Negative expectancy windows: {rs['negative_expectancy_windows']}/{rs['total_windows']}")
    print(f"  First half WR: {rs['first_half']['win_rate']}, Second half WR: {rs['second_half']['win_rate']}")
    with open(OUT / 'rolling_stability_20260406.json', 'w') as f:
        json.dump(rs, f, indent=2, default=str)

    # 1C: Autocorrelation
    print("\n--- 1C: Autocorrelation ---")
    ac = autocorrelation_analysis()
    print(f"  Binary lag-1: {ac['binary_autocorrelation'].get('lag_1')}")
    print(f"  Runs test p: {ac['wald_wolfowitz_runs_test']['p_value']} ({ac['wald_wolfowitz_runs_test']['conclusion']})")
    print(f"  Longest win streak: {ac['longest_win_streak']}, loss streak: {ac['longest_loss_streak']}")
    with open(OUT / 'autocorrelation_20260406.json', 'w') as f:
        json.dump(ac, f, indent=2, default=str)

    # 1D: Drawdown
    print("\n--- 1D: Drawdown Analysis ---")
    dd = drawdown_analysis()
    print(f"  Final equity (R): {dd['final_equity_r']}")
    if dd['max_drawdown']:
        print(f"  Max DD: {dd['max_drawdown']['depth_r']}R, duration: {dd['max_drawdown']['duration_trades']} trades")
    print(f"  At 1% risk: max DD = {dd['dollar_analysis_1pct_risk']['max_drawdown_pct']}%")
    with open(OUT / 'drawdown_analysis_20260406.json', 'w') as f:
        json.dump(dd, f, indent=2, default=str)

    # 1E: DOW × KZ
    print("\n--- 1E: DOW × KZ Matrix ---")
    dk = dow_kz_matrix()
    print(f"  Best DOW: {dk['best_dow']['day']} (WR={dk['best_dow']['win_rate']})")
    print(f"  Worst DOW: {dk['worst_dow']['day']} (WR={dk['worst_dow']['win_rate']})")
    print(f"  Fisher exact p: {dk['fisher_exact_best_vs_worst']['p_value']}")
    with open(OUT / 'dow_kz_matrix_20260406.json', 'w') as f:
        json.dump(dk, f, indent=2, default=str)

    # 1F: Timing
    print("\n--- 1F: Trade Timing ---")
    tt = trade_timing()
    print(f"  Avg gap: {tt['calendar_gaps_days']['mean']} days")
    print(f"  Longest dry spell: {tt['longest_dry_spell_days']} days")
    print(f"  Avg trades/month: {tt['mean_trades_per_month']}")
    print(f"  Zero-trade months: {tt['months_with_zero_trades']}")
    with open(OUT / 'trade_timing_20260406.json', 'w') as f:
        json.dump(tt, f, indent=2, default=str)

    # Write markdown summary
    md = f"""# Phase 1: Trade Index Analyses — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1A: Monte Carlo Equity Curve

### Combined (129 trades)
- Win Rate: {mc_combined['win_rate']:.1%} | Mean R: {mc_combined['mean_r']} | PF: {mc_combined['profit_factor']}
- Kelly Full: {mc_combined['kelly_full_pct']}% | Half-Kelly: {mc_combined['kelly_half_pct']}%

| Risk % | P(+8% before -5%) | P(+8% before -10%) | P(DD>5%) | P(DD>10%) | Median Final | 5th pct | 95th pct | Max Consec Loss (95th) | Median to +3% |
|--------|-------------------|-------------------|----------|-----------|-------------|---------|---------|----------------------|---------------|
"""
    for risk_pct in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
        r = mc_combined['risk_level_results'][risk_pct]
        md += f"| {risk_pct}% | {r['P_8_before_5']:.1%} | {r['P_8_before_10']:.1%} | {r['P_dd_exceeds_5']:.1%} | {r['P_dd_exceeds_10']:.1%} | ${r['median_final_equity']:,.0f} | ${r['pct5_final_equity']:,.0f} | ${r['pct95_final_equity']:,.0f} | {r['max_consec_loss_95th']} | {r['median_trades_to_3pct'] or 'N/A'} |\n"

    md += f"""
### Block Bootstrap (autocorrelation check at 1.0% risk)
- i.i.d. P(+8% before -5%): {mc_combined['block_bootstrap_1pct']['P_8_before_5_iid']:.1%}
- Block P(+8% before -5%): {mc_combined['block_bootstrap_1pct']['P_8_before_5_block']:.1%}
- Difference: {mc_combined['block_bootstrap_1pct']['difference_pp']}pp
- Autocorrelation detected: {'YES' if mc_combined['block_bootstrap_1pct']['autocorrelation_detected'] else 'NO'}

### XAUUSD Only (105 trades)
- Win Rate: {mc_xau['win_rate']:.1%} | Mean R: {mc_xau['mean_r']} | PF: {mc_xau['profit_factor']}
- Kelly Full: {mc_xau['kelly_full_pct']}% | Half-Kelly: {mc_xau['kelly_half_pct']}%

| Risk % | P(+8% before -5%) | P(+8% before -10%) | P(DD>5%) | Median Final |
|--------|-------------------|-------------------|----------|-------------|
"""
    for risk_pct in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
        r = mc_xau['risk_level_results'][risk_pct]
        md += f"| {risk_pct}% | {r['P_8_before_5']:.1%} | {r['P_8_before_10']:.1%} | {r['P_dd_exceeds_5']:.1%} | ${r['median_final_equity']:,.0f} |\n"

    md += f"""
## 1B: Rolling Edge Stability
- Total 20-trade windows: {rs['total_windows']}
- Negative expectancy windows: {rs['negative_expectancy_windows']}
- Best window: {rs['best_window']['start_date']} to {rs['best_window']['end_date']} (Total R: {rs['best_window']['total_r']}, WR: {rs['best_window']['win_rate']:.1%})
- Worst window: {rs['worst_window']['start_date']} to {rs['worst_window']['end_date']} (Total R: {rs['worst_window']['total_r']}, WR: {rs['worst_window']['win_rate']:.1%})

### First Half vs Second Half
| Half | N | WR | Mean R | Total R |
|------|---|-----|--------|---------|
| First | {rs['first_half']['n']} | {rs['first_half']['win_rate']:.1%} | {rs['first_half']['mean_r']} | {rs['first_half']['total_r']} |
| Second | {rs['second_half']['n']} | {rs['second_half']['win_rate']:.1%} | {rs['second_half']['mean_r']} | {rs['second_half']['total_r']} |

## 1C: Trade Autocorrelation
- Binary lag-1: {ac['binary_autocorrelation'].get('lag_1')}
- Binary lag-2: {ac['binary_autocorrelation'].get('lag_2')}
- R-multiple lag-1: {ac['r_multiple_autocorrelation'].get('lag_1')}
- Runs test: z={ac['wald_wolfowitz_runs_test']['z_statistic']}, p={ac['wald_wolfowitz_runs_test']['p_value']} → {ac['wald_wolfowitz_runs_test']['conclusion']}
- Longest win streak: {ac['longest_win_streak']} | Longest loss streak: {ac['longest_loss_streak']}

## 1D: Drawdown Analysis
- Final equity (R-units): {dd['final_equity_r']}
- Max drawdown: {dd['max_drawdown']['depth_r'] if dd['max_drawdown'] else 'N/A'}R over {dd['max_drawdown']['duration_trades'] if dd['max_drawdown'] else 'N/A'} trades
- At 1% risk on $100K: max DD = {dd['dollar_analysis_1pct_risk']['max_drawdown_pct']}% (${dd['dollar_analysis_1pct_risk']['max_drawdown_dollars']:,.0f})
- {'EXCEEDS' if dd['dollar_analysis_1pct_risk']['exceeds_5pct_limit'] else 'WITHIN'} 5% prop firm limit
- {'EXCEEDS' if dd['dollar_analysis_1pct_risk']['exceeds_10pct_limit'] else 'WITHIN'} 10% prop firm limit

## 1E: Day-of-Week × Kill Zone
| Cell | N | WR | Mean R | Total R | Low N? |
|------|---|-----|--------|---------|--------|
"""
    for key in sorted(dk['matrix'].keys()):
        v = dk['matrix'][key]
        md += f"| {key} | {v['n']} | {v['win_rate']:.1%} | {v['mean_r']} | {v['total_r']} | {'⚠️' if v['flag_low_n'] else ''} |\n"

    md += f"""
- Best vs Worst DOW Fisher exact p: {dk['fisher_exact_best_vs_worst']['p_value']}
- Significant: {'YES' if dk['fisher_exact_best_vs_worst']['significant_at_05'] else 'NO'}

## 1F: Trade Timing
- Mean gap between trades: {tt['calendar_gaps_days']['mean']} days
- Longest dry spell: {tt['longest_dry_spell_days']} days
- Avg trades/month: {tt['mean_trades_per_month']}
- Zero-trade months: {tt['months_with_zero_trades']}/{tt['total_trading_months']}
"""

    with open(OUT / 'monte_carlo_20260406.md', 'w') as f:
        f.write(md)

    # Also save drawdown md
    with open(OUT / 'drawdown_analysis_20260406.md', 'w') as f:
        f.write(md)  # Full report covers drawdowns

    print("\nPhase 1 complete. Files saved.")
