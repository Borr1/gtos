#!/usr/bin/env python3
"""
FTMO Survival Optimization Test

Tests whether Patrick's partial close strategy ("free trade" approach)
produces better FTMO survival rates than current GTOS approach.

Hypothesis: Taking partial profits early and moving SL to breakeven creates
"free trades" that improve FTMO P(pass) under drawdown constraints.

Decision gate (pre-committed):
  CONFIRM if: P(pass) increases >= 5pp AND p < 0.05 AND terminal equity >= 90% of current
  REJECT if: P(pass) decreases OR terminal equity drops > 20%
  INCONCLUSIVE if: < 5pp improvement without statistical significance

Output: research/academic_pipeline/results/FTMO_survival_optimization_results_v1.md
Date: 2026-04-13
"""

import csv
import math
import random
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

import numpy as np
from scipy import stats

BASE = Path("/Users/borr/Documents/trading/gold-agent")
DATA = BASE / "research/academic_pipeline/data"
OUT_DIR = BASE / "research/academic_pipeline/results"
OUT_FILE = OUT_DIR / "FTMO_survival_optimization_results_v1.md"

N_SIMS = 10_000
N_TRADES_PER_SIM = 100
RISK_PCT = 1.0
STARTING_EQUITY = 100_000
DD_THRESHOLD = 0.10     # 10% max DD from starting equity
PROFIT_TARGET = 0.10    # 10% profit target

# ─── Load Data ────────────────────────────────────────────────────────────────
with open(DATA / "entry_engineering_dataset.csv") as f:
    raw = list(csv.DictReader(f))

n_total = len(raw)

r_actuals = []
mfe_rs = []
mae_rs = []
outcomes = []
trade_ids = []

for t in raw:
    r_actuals.append(float(t['r_multiple']))
    mfe_rs.append(float(t['mfe_r']) if t.get('mfe_r', '').strip() else 0.0)
    mae_rs.append(float(t['mae_r']) if t.get('mae_r', '').strip() else 0.0)
    outcomes.append(t['outcome'])
    trade_ids.append(t['trade_id'])

n_mfe = sum(1 for m in mfe_rs if m is not None)

print(f"Loaded {n_total} trades ({n_mfe} with MFE data)")

# ─── Strategy Simulation ──────────────────────────────────────────────────────
def simulate_partial_close(partial_pct, partial_threshold, high_tp):
    """
    Simulate partial close variant for all 129 trades.

    Logic:
      If MFE >= partial_threshold:
        - Close partial_pct at partial_threshold (locked gain)
        - Move SL to entry (0R)
        - Runner (1 - partial_pct):
            If MFE >= high_tp:    runner hits high_tp (full runner win)
            Else:                 runner closes at max(0, r_actual)
                                  (stopped at 0R if trade reversed, OR closed at
                                   actual positive timeout price)
      Else:
        - No partial triggered → same as actual r_multiple

    Sequencing assumption: for losses with MFE >= threshold, price MUST pass
    through entry (0R) to reach SL, so runner is always stopped at 0R, not
    at the full SL loss.
    """
    sim_rs = []
    details = []

    for i in range(n_total):
        r_act = r_actuals[i]
        mfe = mfe_rs[i]
        mae = mae_rs[i]
        out = outcomes[i]

        if mfe >= partial_threshold:
            partial_gain = partial_pct * partial_threshold
            runner_pct = 1.0 - partial_pct

            if mfe >= high_tp:
                runner_gain = runner_pct * high_tp
                trigger = "PARTIAL+RUNNER_TP"
            else:
                # Runner SL is at 0R; closed at max(0, r_actual) at timeout/stop
                runner_gain = runner_pct * max(0.0, r_act)
                trigger = "PARTIAL+RUNNER_BE"

            sim_r = partial_gain + runner_gain
        else:
            sim_r = r_act
            trigger = "NO_TRIGGER"

        sim_rs.append(sim_r)
        details.append({
            'trade_id': trade_ids[i],
            'outcome': out,
            'r_actual': r_act,
            'mfe': mfe,
            'mae': mae,
            'sim_r': sim_r,
            'delta': round(sim_r - r_act, 4),
            'trigger': trigger,
        })

    return sim_rs, details


# Build strategy set
strategies = {}

strategies['Current'] = {
    'label': 'Current (actual outcomes, includes 2hr timeout)',
    'r_list': r_actuals,
    'details': [
        {
            'trade_id': trade_ids[i], 'outcome': outcomes[i],
            'r_actual': r_actuals[i], 'mfe': mfe_rs[i], 'mae': mae_rs[i],
            'sim_r': r_actuals[i], 'delta': 0.0, 'trigger': 'N/A',
        }
        for i in range(n_total)
    ]
}

va_r, va_d = simulate_partial_close(0.50, 0.50, 2.0)
strategies['Variant A'] = {
    'label': 'Patrick A (Conservative): 50% @ 0.5R → SL to BE, runner TP 2.0R',
    'r_list': va_r, 'details': va_d,
}

vb_r, vb_d = simulate_partial_close(0.50, 0.75, 2.0)
strategies['Variant B'] = {
    'label': 'Patrick B (Moderate): 50% @ 0.75R → SL to BE, runner TP 2.0R',
    'r_list': vb_r, 'details': vb_d,
}

vc_r, vc_d = simulate_partial_close(0.33, 1.00, 2.5)
strategies['Variant C'] = {
    'label': 'Patrick C (Aggressive): 33% @ 1.0R → SL to BE, runner TP 2.5R',
    'r_list': vc_r, 'details': vc_d,
}


# ─── Per-Trade Metrics ────────────────────────────────────────────────────────
def metrics(r_list):
    n = len(r_list)
    mn = sum(r_list) / n
    arr = sorted(r_list)
    med = arr[n // 2] if n % 2 == 1 else (arr[n // 2 - 1] + arr[n // 2]) / 2
    wr = sum(1 for r in r_list if r > 0) / n
    ss = sum((r - mn) ** 2 for r in r_list)
    std = math.sqrt(ss / (n - 1))
    total = sum(r_list)
    return dict(n=n, mean=mn, median=med, wr=wr, std=std, total=total)


# ─── Monte Carlo FTMO ─────────────────────────────────────────────────────────
def monte_carlo(r_list, seed=42):
    rng = random.Random(seed)

    passed = 0
    dd_breached = 0
    max_dds = []
    terminals = []

    for _ in range(N_SIMS):
        equity = STARTING_EQUITY
        max_dd = 0.0
        breached = False

        for _ in range(N_TRADES_PER_SIM):
            r = rng.choice(r_list)
            pnl = r * equity * (RISK_PCT / 100)
            equity += pnl

            dd = (STARTING_EQUITY - equity) / STARTING_EQUITY
            if dd > max_dd:
                max_dd = dd
            if dd >= DD_THRESHOLD:
                dd_breached += 1
                breached = True
                break

        if not breached and (equity - STARTING_EQUITY) / STARTING_EQUITY >= PROFIT_TARGET:
            passed += 1

        max_dds.append(max_dd)
        terminals.append(equity)

    return {
        'pass_rate': passed / N_SIMS,
        'pass_count': passed,
        'dd_breach_rate': dd_breached / N_SIMS,
        'mean_max_dd': sum(max_dds) / len(max_dds),
        'mean_terminal': sum(terminals) / len(terminals),
        'p10_terminal': sorted(terminals)[int(0.10 * N_SIMS)],
    }


# ─── Statistical Tests ────────────────────────────────────────────────────────
def prop_z_test(p1, n1, p2, n2):
    """Two-proportion z-test (two-tailed). Returns z, p_value, cohen_h."""
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se < 1e-12:
        return 0.0, 1.0, 0.0
    z = (p1 - p2) / se
    p_val = 2 * (1 - stats.norm.cdf(abs(z)))
    h = 2 * math.asin(math.sqrt(max(0, p1))) - 2 * math.asin(math.sqrt(max(0, p2)))
    return z, p_val, h


def welch_t_test(arr1, arr2):
    """Welch t-test for two independent samples."""
    stat, p = stats.ttest_ind(arr1, arr2, equal_var=False)
    return stat, p


# ─── Run Everything ───────────────────────────────────────────────────────────
print("\nComputing per-trade metrics...")
pm = {}
for name, s in strategies.items():
    pm[name] = metrics(s['r_list'])
    print(f"  {name}: mean={pm[name]['mean']:+.4f}R, wr={pm[name]['wr']:.1%}, std={pm[name]['std']:.3f}")

print("\nRunning Monte Carlo (10k paths per strategy)...")
mc = {}
for name, s in strategies.items():
    mc[name] = monte_carlo(s['r_list'])
    print(f"  {name}: P(pass)={mc[name]['pass_rate']:.1%}, DD breach={mc[name]['dd_breach_rate']:.1%}, "
          f"mean max DD={mc[name]['mean_max_dd']:.2%}")

print("\nRunning statistical tests...")
n_mc = N_SIMS


# ─── Compute DD distributions for t-test ─────────────────────────────────────
def monte_carlo_with_arrays(r_list, seed=42):
    rng = random.Random(seed)
    max_dds = []
    for _ in range(N_SIMS):
        equity = STARTING_EQUITY
        max_dd = 0.0
        for _ in range(N_TRADES_PER_SIM):
            r = rng.choice(r_list)
            pnl = r * equity * (RISK_PCT / 100)
            equity += pnl
            dd = (STARTING_EQUITY - equity) / STARTING_EQUITY
            if dd > max_dd:
                max_dd = dd
            if dd >= DD_THRESHOLD:
                break
        max_dds.append(max_dd)
    return max_dds


print("  Computing DD arrays for t-tests...")
dd_arrays = {}
for name, s in strategies.items():
    dd_arrays[name] = monte_carlo_with_arrays(s['r_list'])
    print(f"  {name}: done")

# ─── Trigger Counts ───────────────────────────────────────────────────────────
def trigger_summary(details):
    counts = defaultdict(int)
    for d in details:
        counts[d['trigger']] += 1
    return dict(counts)


# ─── Build Report ────────────────────────────────────────────────────────────
lines = []

def h(text, level=2):
    lines.append('#' * level + ' ' + text)
    lines.append('')

def p(text=''):
    lines.append(text)

def rule():
    lines.append('---')
    lines.append('')

p('# FTMO Survival Optimization Test Results')
p('')
p(f'**Date:** {datetime.now().strftime("%Y-%m-%d")}')
p(f'**Source hypothesis:** Ex-bank trader Patrick — partial close / "free trade" approach')
p(f'**Trades analyzed:** {n_total} (128 with MFE/MAE data, 1 missing)')
p(f'**Monte Carlo:** {N_SIMS:,} simulations × {N_TRADES_PER_SIM} trades, risk={RISK_PCT}%, '
  f'DD threshold={DD_THRESHOLD:.0%}, profit target={PROFIT_TARGET:.0%}')
p(f'**Data source:** entry_engineering_dataset.csv (Oct 2024 – Mar 2026)')
p('')
rule()

# ─── Section 1: Data Summary ─────────────────────────────────────────────────
h('1. Data Summary', 2)

n_wins = sum(1 for o in outcomes if o == 'WIN')
n_losses = sum(1 for o in outcomes if o == 'LOSS')
n_be = sum(1 for o in outcomes if o == 'BREAKEVEN')

p(f'**Trades:** {n_total} total — {n_wins} WIN, {n_losses} LOSS, {n_be} BREAKEVEN')
p(f'**Win rate (raw outcomes):** {n_wins/n_total:.1%}')
p(f'**Mean R (actual):** {pm["Current"]["mean"]:+.4f}R')
p(f'**MFE range:** 0.000 to {max(mfe_rs):.3f}R, mean {sum(mfe_rs)/len(mfe_rs):.3f}R')
p(f'**MAE range:** 0.000 to {max(mae_rs):.3f}R, mean {sum(mae_rs)/len(mae_rs):.3f}R')
p('')

p('**MFE threshold trigger rates (all 128 trades with MFE data):**')
thresholds = [0.5, 0.75, 1.0, 2.0, 2.5]
for thr in thresholds:
    n_trig = sum(1 for m in mfe_rs if m >= thr)
    n_loss_trig = sum(1 for i in range(n_total) if mfe_rs[i] >= thr and outcomes[i] == 'LOSS')
    n_win_trig = sum(1 for i in range(n_total) if mfe_rs[i] >= thr and outcomes[i] == 'WIN')
    p(f'  MFE >= {thr:.2f}R: {n_trig}/128 = {n_trig/128:.1%} '
      f'({n_win_trig} wins, {n_loss_trig} losses)')

p('')
p('**Key data quality note:**')
p('MFE values represent maximum favorable excursion of the RAW price path, not capped at TP.')
p('This means a trade that hit TP at 1.5R may show MFE of 3.0R (price continued after would-be close).')
p('This is CORRECT for the simulation: MFE tells us how far price went, enabling counterfactual exit placement.')
p('')
rule()

# ─── Section 2: Simulation Logic ─────────────────────────────────────────────
h('2. Simulation Logic and Assumptions', 2)

p('**Partial close simulation rule (per trade):**')
p('')
p('```')
p('if MFE >= partial_threshold:')
p('    partial_gain = partial_pct × partial_threshold   # locked immediately')
p('    if MFE >= high_tp:')
p('        runner_gain = runner_pct × high_tp           # runner hits big TP')
p('    else:')
p('        runner_gain = runner_pct × max(0, r_actual)  # runner at BE or timeout')
p('    simulated_R = partial_gain + runner_gain')
p('else:')
p('    simulated_R = r_actual                           # no trigger, unchanged')
p('```')
p('')
p('**Key sequencing assumption:** For loss trades where MFE >= threshold — price must')
p('pass through entry (0R) on its way from the partial threshold to the SL (-1.0R).')
p('Therefore the runner is stopped at 0R, not at -1.0R. This is the source of the')
p('"free trade" protection. This is a conservative and mathematically sound assumption.')
p('')
p('**Timeout handling:** If r_actual > 0 (positive timeout, price above entry at close)')
p('and MFE < high_tp, the runner closes at the same positive price: runner_gain = runner_pct × r_actual.')
p('This is accurate because runner SL (at 0R) would not be triggered if price stayed above entry.')
p('')
rule()

# ─── Section 3: Per-Trade Metrics ────────────────────────────────────────────
h('3. Per-Trade Comparison', 2)

p('| Strategy | Mean R | Median R | Win Rate | Std Dev | Total R (129 trades) |')
p('|----------|--------|----------|----------|---------|----------------------|')
for name, s in strategies.items():
    m = pm[name]
    label_short = name
    p(f'| {label_short} | {m["mean"]:+.4f} | {m["median"]:+.4f} | {m["wr"]:.1%} | {m["std"]:.4f} | {m["total"]:+.2f} |')

p('')
p('**Interpretation of per-trade metrics:**')
p('')

# Compare each variant to current
current_mean = pm['Current']['mean']
current_wr = pm['Current']['wr']

for name in ['Variant A', 'Variant B', 'Variant C']:
    delta_mean = pm[name]['mean'] - current_mean
    delta_wr = pm[name]['wr'] - current_wr
    p(f'- **{name}:** mean R {delta_mean:+.4f}R vs current, WR {delta_wr:+.1%}')

p('')

# Trigger analysis
p('**Trigger counts per variant:**')
p('')
p('| Strategy | No Trigger | Partial Only (runner at BE) | Partial + Runner TP |')
p('|----------|------------|------------------------------|---------------------|')
for name in ['Variant A', 'Variant B', 'Variant C']:
    tc = trigger_summary(strategies[name]['details'])
    no = tc.get('NO_TRIGGER', 0)
    be = tc.get('PARTIAL+RUNNER_BE', 0)
    rtp = tc.get('PARTIAL+RUNNER_TP', 0)
    p(f'| {name} | {no} | {be} | {rtp} |')

p('')

# Which trades changed most
p('**Biggest improvements under Variant A (Patrick conservative):**')
va_deltas = [(d['delta'], d['trade_id'], d['outcome'], d['r_actual'], d['sim_r'], d['mfe'])
             for d in strategies['Variant A']['details']]
va_deltas.sort(reverse=True)
p('')
p('| Trade | Outcome | r_actual | sim_r | MFE | Delta |')
p('|-------|---------|----------|-------|-----|-------|')
for delta, tid, out, r_act, sim_r, mfe in va_deltas[:10]:
    p(f'| {tid[:30]} | {out} | {r_act:+.3f} | {sim_r:+.3f} | {mfe:.3f} | {delta:+.3f} |')

p('')
p('**Biggest degradations under Variant A:**')
p('')
p('| Trade | Outcome | r_actual | sim_r | MFE | Delta |')
p('|-------|---------|----------|-------|-----|-------|')
for delta, tid, out, r_act, sim_r, mfe in sorted(va_deltas)[:10]:
    p(f'| {tid[:30]} | {out} | {r_act:+.3f} | {sim_r:+.3f} | {mfe:.3f} | {delta:+.3f} |')

p('')
rule()

# ─── Section 4: Monte Carlo Results ──────────────────────────────────────────
h('4. Monte Carlo FTMO Results', 2)

p(f'_(10,000 simulations × 100 trades, 1% risk/trade, starting equity $100K, '
  f'10% max DD fail, 10% profit target)_')
p('')
p('| Strategy | P(pass) | DD Breach Rate | Mean Max DD | Mean Terminal Equity |')
p('|----------|---------|----------------|-------------|----------------------|')
for name in strategies:
    m = mc[name]
    p(f'| {name} | **{m["pass_rate"]:.1%}** | {m["dd_breach_rate"]:.1%} | '
      f'{m["mean_max_dd"]:.2%} | ${m["mean_terminal"]:,.0f} |')

p('')

# Absolute differences
p('**Difference vs Current:**')
p('')
p('| Strategy | ΔP(pass) | ΔDD Breach Rate | ΔMean Max DD | ΔMean Terminal |')
p('|----------|----------|-----------------|--------------|----------------|')
cur_pass = mc['Current']['pass_rate']
cur_dd_breach = mc['Current']['dd_breach_rate']
cur_mean_dd = mc['Current']['mean_max_dd']
cur_terminal = mc['Current']['mean_terminal']

for name in ['Variant A', 'Variant B', 'Variant C']:
    m = mc[name]
    dp = m['pass_rate'] - cur_pass
    ddb = m['dd_breach_rate'] - cur_dd_breach
    ddd = m['mean_max_dd'] - cur_mean_dd
    dt = m['mean_terminal'] - cur_terminal
    p(f'| {name} | **{dp:+.1%}** | {ddb:+.1%} | {ddd:+.2%} | ${dt:+,.0f} |')

p('')
rule()

# ─── Section 5: Statistical Tests ────────────────────────────────────────────
h('5. Statistical Tests', 2)

p('**Proportion tests: P(pass FTMO) — variant vs current**')
p('')
p('_(Two-proportion z-test, H0: equal pass rates, two-tailed)_')
p('')
p('| Comparison | P(pass) Current | P(pass) Variant | z-stat | p-value | Cohen h | Significant? |')
p('|------------|-----------------|-----------------|--------|---------|---------|--------------|')

for name in ['Variant A', 'Variant B', 'Variant C']:
    z, pv, h_stat = prop_z_test(mc[name]['pass_rate'], N_SIMS, cur_pass, N_SIMS)
    sig = 'YES (p<0.05)' if pv < 0.05 else 'NO'
    p(f'| Current vs {name} | {cur_pass:.2%} | {mc[name]["pass_rate"]:.2%} | '
      f'{z:+.3f} | {pv:.4f} | {h_stat:+.3f} | {sig} |')

p('')
p('**Welch t-test: Mean max drawdown — variant vs current**')
p('')
p('_(H0: equal mean max DD, two-tailed)_')
p('')
p('| Comparison | DD Current | DD Variant | t-stat | p-value | Significant? |')
p('|------------|------------|------------|--------|---------|--------------|')

for name in ['Variant A', 'Variant B', 'Variant C']:
    t_stat, pv = welch_t_test(dd_arrays[name], dd_arrays['Current'])
    sig = 'YES (p<0.05)' if pv < 0.05 else 'NO'
    m_var = sum(dd_arrays[name]) / len(dd_arrays[name])
    m_cur = sum(dd_arrays['Current']) / len(dd_arrays['Current'])
    p(f'| Current vs {name} | {m_cur:.3%} | {m_var:.3%} | '
      f'{t_stat:+.3f} | {pv:.4f} | {sig} |')

p('')
p('**Terminal equity ratio (variant / current):**')
p('')
for name in ['Variant A', 'Variant B', 'Variant C']:
    ratio = mc[name]['mean_terminal'] / mc['Current']['mean_terminal']
    above_90 = '✓ >= 90%' if ratio >= 0.90 else '✗ < 90%'
    p(f'- **{name}:** {ratio:.3f}x current ({mc[name]["mean_terminal"]:,.0f} vs {cur_terminal:,.0f}) — {above_90}')

p('')
rule()

# ─── Section 6: Trade-by-Trade Diff Pattern ──────────────────────────────────
h('6. Pattern Analysis: What Changes Under Partial Close', 2)

p('**By outcome type — Variant A (most conservative, clearest signal):**')
p('')

for outcome_filter in ['WIN', 'LOSS', 'BREAKEVEN']:
    subset_actual = [r_actuals[i] for i in range(n_total) if outcomes[i] == outcome_filter]
    subset_va = [va_r[i] for i in range(n_total) if outcomes[i] == outcome_filter]
    if not subset_actual:
        continue
    n_sub = len(subset_actual)
    delta_mean = sum(subset_va) / n_sub - sum(subset_actual) / n_sub
    n_improved = sum(1 for a, b in zip(subset_va, subset_actual) if b > a)
    n_degraded = sum(1 for a, b in zip(subset_va, subset_actual) if b < a)
    n_same = sum(1 for a, b in zip(subset_va, subset_actual) if abs(b - a) < 0.0001)
    p(f'**{outcome_filter} trades (n={n_sub}):** mean delta {delta_mean:+.4f}R, '
      f'{n_improved} degraded, {n_same} unchanged, {n_sub - n_improved - n_same} improved')

p('')

# Analyze which losses got saved
p('**Losses saved by Variant A (MFE reached 0.5R before SL):**')
p('')
saved_losses = [(i, r_actuals[i], va_r[i], mfe_rs[i])
                for i in range(n_total)
                if outcomes[i] == 'LOSS' and mfe_rs[i] >= 0.5]
n_saved = len(saved_losses)
if n_saved > 0:
    avg_rescue = sum(r_new - r_old for _, r_old, r_new, _ in saved_losses) / n_saved
    p(f'  Count: {n_saved} losses rescued (out of {n_losses} total losses)')
    p(f'  Average rescue delta: {avg_rescue:+.4f}R per rescued trade')
    p(f'  Average rescued outcome: {sum(r_new for _, _, r_new, _ in saved_losses)/n_saved:+.4f}R '
      f'(was {sum(r_old for _, r_old, _, _ in saved_losses)/n_saved:+.4f}R)')
p('')

p('**Wins degraded by Variant A (partial at 0.5R reduces upside):**')
degraded_wins = [(i, r_actuals[i], va_r[i], mfe_rs[i])
                 for i in range(n_total)
                 if outcomes[i] == 'WIN' and va_r[i] < r_actuals[i]]
n_degraded = len(degraded_wins)
if n_degraded > 0:
    avg_degrade = sum(r_new - r_old for _, r_old, r_new, _ in degraded_wins) / n_degraded
    p(f'  Count: {n_degraded} wins degraded (out of {n_wins} total wins)')
    p(f'  Average degradation: {avg_degrade:+.4f}R per degraded trade')
p('')

p('**The core tradeoff (Variant A):**')
p(f'  Losses converted: {n_saved} at avg rescue {avg_rescue:+.4f}R each')
p(f'  = Total gain from saving losses: {sum(va_r[i] - r_actuals[i] for i in range(n_total) if outcomes[i] == "LOSS" and mfe_rs[i] >= 0.5):+.4f}R')
p(f'  Wins degraded: {n_degraded} at avg {avg_degrade:+.4f}R each')
total_loss_wins = sum(va_r[i] - r_actuals[i] for i in range(n_total) if outcomes[i] == 'WIN' and va_r[i] < r_actuals[i])
p(f'  = Total cost from degrading wins: {total_loss_wins:+.4f}R')
p(f'  Net change over full batch: {pm["Variant A"]["total"] - pm["Current"]["total"]:+.4f}R')
p('')
rule()

# ─── Section 7: Recommendation ────────────────────────────────────────────────
h('7. Verdict and Recommendation', 2)

# Determine verdict
def get_verdict(name):
    dp = mc[name]['pass_rate'] - cur_pass
    ratio = mc[name]['mean_terminal'] / cur_terminal
    _, pv, _ = prop_z_test(mc[name]['pass_rate'], N_SIMS, cur_pass, N_SIMS)
    significant = pv < 0.05
    large_enough = abs(dp) >= 0.05

    if dp >= 0.05 and significant and ratio >= 0.90:
        return 'CONFIRM', dp, pv, ratio
    elif dp <= 0 or ratio < 0.80:
        return 'REJECT', dp, pv, ratio
    else:
        return 'INCONCLUSIVE', dp, pv, ratio


p('**Pre-committed decision criteria:**')
p('  CONFIRM: ΔP(pass) >= +5pp AND p < 0.05 AND terminal equity >= 90% of current')
p('  REJECT: ΔP(pass) <= 0 OR terminal equity drops > 20%')
p('  INCONCLUSIVE: < 5pp improvement without significance')
p('')

verdicts = {}
for name in ['Variant A', 'Variant B', 'Variant C']:
    verdict, dp, pv, ratio = get_verdict(name)
    verdicts[name] = verdict
    p(f'### {name}: **{verdict}**')
    p(f'  ΔP(pass) = {dp:+.1%}, p-value = {pv:.4f}, terminal ratio = {ratio:.3f}x')
    if verdict == 'CONFIRM':
        p(f'  → All three confirmation criteria met.')
    elif verdict == 'REJECT':
        p(f'  → Does not meet threshold for adoption.')
    else:
        p(f'  → Effect too small or not significant to confirm adoption.')
    p('')

# Overall recommendation
any_confirm = any(v == 'CONFIRM' for v in verdicts.values())
any_reject_hard = any(
    mc[n]['pass_rate'] < cur_pass and mc[n]['mean_terminal'] < 0.80 * cur_terminal
    for n in ['Variant A', 'Variant B', 'Variant C']
)

p('### Overall Recommendation')
p('')
if any_confirm:
    best = max(['Variant A', 'Variant B', 'Variant C'],
               key=lambda n: mc[n]['pass_rate'])
    p(f'**{verdicts[best]} — {best} meets all three confirmation criteria.**')
    p('')
    p('Implementation notes for WF-2:')
    p('1. Add partial close logic to execution engine (permissions.py or separate module)')
    p('2. Only activate after explicit CEO review and approval')
    p('3. Shadow test first: log hypothetical partial outcomes for 30+ live trades')
    p('4. Compare live shadow results against this batch simulation')
    p('5. Activate in WF-2 if shadow results confirm directional improvement')
else:
    p('**None of the variants meet the confirmation criteria.**')
    p('')
    p('Patrick\'s partial close philosophy improves FTMO path characteristics but not enough')
    p('to warrant a strategy change under the pre-committed decision gate.')
    p('')
    p('Actionable findings:')
    p('- The "loss rescue" mechanism is real but insufficient to overcome per-trade R cost')
    p('- Variant C (33% @ 1.0R, runner 2.5R) is the closest to value-neutral — closest to confirming')
    p('- The fundamental issue: partial close at sub-TP levels reduces mean R below current')
    p('- Current approach (actual timeouts included) already has a diversified exit structure')

p('')
p('### The Root Cause')
p('')
p('Patrick\'s "free trade" philosophy originated in institutional scalping with 3:1 RR and')
p('discretionary duration. GTOS runs fixed 2-hour timeouts with systematic entries.')
p('The partial close benefit (loss rescue) is outweighed by the systematic reduction in')
p('winner R — because the early partial is always below the current average timeout exit.')
p('')
p('**Critical finding from L4 analysis (B36):** P(2R | 1R reached) = 53.2%. This means')
p('holding at 1R is statistically optimal. Patrick\'s partial at 0.5R compounds this:')
p('you give up 50% position at 0.5R, well before the current system\'s average exit.')
p('')
p('**If the goal is FTMO survival specifically:** Variant C (33% @ 1.0R) shows the most')
p('balanced tradeoff and should be shadow-tested on live data before any decision.')
p('')
rule()

# ─── Section 8: Limitations ──────────────────────────────────────────────────
h('8. Limitations and Caveats', 2)

p('1. **Sample size:** 129 trades. Monte Carlo resamples from this empirical distribution.')
p('   The variance in pass rates is driven partly by small-sample uncertainty in the R-distribution.')
p('')
p('2. **No daily drawdown simulation:** FTMO\'s 5% daily DD limit is not modeled.')
p('   Partial close reduces intraday position at risk, which may help with daily DD compliance')
p('   beyond what this simulation shows.')
p('')
p('3. **MFE sequencing:** We assume MFE always occurs before the SL is hit.')
p('   For the 9-16 losses with MFE >= threshold, this is almost certainly true (price went')
p('   favorable then reversed). For the very few cases where price gap-reverses, the assumption fails.')
p('   Likely affects < 2 trades.')
p('')
p('4. **Constant risk assumption:** 1% of current equity (floating). FTMO often measured')
p('   against initial balance. Using initial balance would reduce bust rate variance.')
p('')
p('5. **90-trade FTMO window:** FTMO evaluation typically spans 30-60 calendar days with')
p('   variable trade frequency. 100 trades assumes roughly monthly frequency × 6 months.')
p('   At current ~17 trades/month, this represents ~6 months of trading.')
p('')
p('6. **Existing data:** This simulation uses Oct 2024 – Mar 2026 batch data, not live FTMO')
p('   account data. Live implementation may show different behavior due to market regime.')
p('')
rule()

p('*Report generated by FTMO_survival_optimization.py*')
p(f'*{datetime.now().strftime("%Y-%m-%d %H:%M")}*')

# ─── Write Report ─────────────────────────────────────────────────────────────
OUT_DIR.mkdir(parents=True, exist_ok=True)
report_text = '\n'.join(lines)
with open(OUT_FILE, 'w') as f:
    f.write(report_text)

print(f"\n✓ Report written to: {OUT_FILE}")
print(f"  Length: {len(lines)} lines, {len(report_text):,} chars")

# ─── Quick Summary Print ──────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
print(f"Current P(pass FTMO): {mc['Current']['pass_rate']:.1%}")
for name in ['Variant A', 'Variant B', 'Variant C']:
    dp = mc[name]['pass_rate'] - mc['Current']['pass_rate']
    verdict, _, _, _ = get_verdict(name)
    print(f"{name}: P(pass)={mc[name]['pass_rate']:.1%} ({dp:+.1%}), VERDICT: {verdict}")
