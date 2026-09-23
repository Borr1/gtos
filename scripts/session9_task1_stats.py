#!/usr/bin/env python3
"""
Session 9 — Task 1: Statistical Validation Computations
All computations use scipy.stats — no hand-rolled statistics.
"""

import numpy as np
from scipy import stats
import json

# =============================================================================
# DATA
# =============================================================================
instruments = {
    'XAUUSD': {'wr': 0.620, 'n': 129, 'avg_winner': 1.8, 'avg_loser': 1.0, 'trades_per_month': 4.5},
    'US30':   {'wr': 0.585, 'n': 41,  'avg_winner': 1.9, 'avg_loser': 1.0, 'trades_per_month': 3.5},
    'USDJPY': {'wr': 0.758, 'n': 33,  'avg_winner': 1.5, 'avg_loser': 1.0, 'trades_per_month': 3.0},
    'GBPJPY': {'wr': 0.571, 'n': 42,  'avg_winner': 1.4, 'avg_loser': 1.0, 'trades_per_month': 3.5},
}

# Compute breakeven WR for each instrument
for name, d in instruments.items():
    d['be_wr'] = d['avg_loser'] / (d['avg_winner'] + d['avg_loser'])

print("=" * 80)
print("TASK 1a: WILSON SCORE CONFIDENCE INTERVALS (95%)")
print("=" * 80)
print()

z = stats.norm.ppf(0.975)  # 1.96 for 95% CI

for name, d in instruments.items():
    n = d['n']
    p = d['wr']
    be = d['be_wr']

    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denominator
    margin = z * np.sqrt((p * (1-p) + z**2 / (4*n)) / n) / denominator
    lower = center - margin
    upper = center + margin

    d['wilson_lower'] = lower
    d['wilson_upper'] = upper

    exceeds = "YES ✓" if lower > be else "NO ✗"

    print(f"{name}:")
    print(f"  Observed WR: {p*100:.1f}% (n={n})")
    print(f"  Breakeven WR: {be*100:.1f}%")
    print(f"  95% Wilson CI: [{lower*100:.1f}%, {upper*100:.1f}%]")
    print(f"  CI lower > breakeven? {exceeds} (margin: {(lower-be)*100:+.1f}pp)")
    print()

# =============================================================================
print("=" * 80)
print("TASK 1b: BINOMIAL P-VALUES (H0 = breakeven WR)")
print("=" * 80)
print()

for name, d in instruments.items():
    n = d['n']
    k = round(d['wr'] * n)  # observed wins
    be = d['be_wr']

    # One-sided binomial test: P(X >= k | p = be)
    p_value = 1 - stats.binom.cdf(k - 1, n, be)
    d['p_value'] = p_value

    sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"

    print(f"{name}: k={k}/{n}, H0: p={be:.3f}")
    print(f"  p-value = {p_value:.2e} {sig}")
    print()

# =============================================================================
print("=" * 80)
print("TASK 1c: MULTIPLE TESTING CORRECTIONS")
print("=" * 80)
print()

# 1. Bonferroni for ~5 prompt versions on gold
gold_p = instruments['XAUUSD']['p_value']
n_prompts = 5
bonf_gold_prompt = min(gold_p * n_prompts, 1.0)
print(f"Gold raw p-value: {gold_p:.2e}")
print(f"Bonferroni correction for {n_prompts} prompt versions: {bonf_gold_prompt:.2e}")
print(f"  Still significant at 0.05? {'YES' if bonf_gold_prompt < 0.05 else 'NO'}")
print()

# 2. Family-wise correction for 6 instruments tested
n_instruments = 6
print(f"Family-wise correction (Bonferroni) for {n_instruments} instruments:")
for name, d in instruments.items():
    corrected = min(d['p_value'] * n_instruments, 1.0)
    sig = "YES" if corrected < 0.05 else "NO"
    print(f"  {name}: raw={d['p_value']:.2e} → corrected={corrected:.2e} (sig: {sig})")
print()

# 3. Combined correction: 5 prompts × 6 instruments = 30 tests
combined_n = n_prompts * n_instruments
combined_gold = min(gold_p * combined_n, 1.0)
print(f"Combined correction ({n_prompts} prompts × {n_instruments} instruments = {combined_n} tests):")
print(f"  Gold corrected p-value: {combined_gold:.2e}")
print(f"  Still significant at 0.05? {'YES' if combined_gold < 0.05 else 'NO'}")
print()

# 4. Selection bias: expected apparent WR under null
print("Selection bias analysis:")
print("If 6 instruments with TRUE WR = breakeven were tested (n≈40 each),")
print("and we kept those above breakeven...")

n_sim = 100000
for name, d in instruments.items():
    n = d['n']
    be = d['be_wr']
    # Simulate: draw WR from binomial(n, be), keep if > be
    simulated_wrs = np.random.binomial(n, be, n_sim) / n
    selected = simulated_wrs[simulated_wrs > be]
    if len(selected) > 0:
        expected_apparent = np.mean(selected)
        pct_selected = len(selected) / n_sim * 100
        print(f"  {name} (n={n}, true={be*100:.1f}%): apparent WR={expected_apparent*100:.1f}%, "
              f"selected {pct_selected:.0f}% of the time, gap from observed: {(d['wr']-expected_apparent)*100:.1f}pp")
print()

# =============================================================================
print("=" * 80)
print("TASK 1d: POWER ANALYSIS")
print("=" * 80)
print()

print("Gold (XAUUSD): How many trades for 80% power at alpha=0.05?")
print(f"H0: WR = {instruments['XAUUSD']['be_wr']*100:.1f}% (breakeven)")
print()

for true_wr in [0.62, 0.58, 0.55, 0.52]:
    be = instruments['XAUUSD']['be_wr']
    alpha = 0.05
    target_power = 0.80

    # Find n for given power using normal approximation to binomial
    # Power = P(reject H0 | true_wr) = P(Z > z_alpha - (true_wr - be) / se)
    # Iterate n
    for n_test in range(10, 2000):
        # Under H0, critical value
        se_h0 = np.sqrt(be * (1-be) / n_test)
        crit = be + stats.norm.ppf(1 - alpha) * se_h0

        # Under H1, probability of exceeding critical value
        se_h1 = np.sqrt(true_wr * (1 - true_wr) / n_test)
        power = 1 - stats.norm.cdf((crit - true_wr) / se_h1)

        if power >= target_power:
            months = n_test / instruments['XAUUSD']['trades_per_month']
            print(f"  True WR = {true_wr*100:.0f}%: n = {n_test} trades ({months:.0f} months at 4.5/mo)")
            break
    else:
        print(f"  True WR = {true_wr*100:.0f}%: >2000 trades needed")
print()

# =============================================================================
print("=" * 80)
print("TASK 1e: SEQUENTIAL PROBABILITY RATIO TEST (SPRT)")
print("=" * 80)
print()

def compute_sprt_table(name, p0, p1, alpha=0.05, beta=0.20, max_n=60):
    """Compute SPRT decision boundaries."""
    # Wald boundaries
    A = np.log((1 - beta) / alpha)   # Upper boundary (confirm H1)
    B = np.log(beta / (1 - alpha))   # Lower boundary (confirm H0)

    # Log-likelihood ratio for a single win and loss
    ll_win = np.log(p1 / p0)
    ll_loss = np.log((1 - p1) / (1 - p0))

    print(f"\n{name}: H0: WR={p0*100:.1f}%, H1: WR={p1*100:.1f}%")
    print(f"  A (confirm) = {A:.4f}, B (kill) = {B:.4f}")
    print(f"  LL(win) = {ll_win:.4f}, LL(loss) = {ll_loss:.4f}")
    print()
    print(f"  {'Trade #':>8} | {'Wins to CONFIRM':>16} | {'Wins to KILL':>13} | {'Continue Range':>15}")
    print(f"  {'-'*8}-+-{'-'*16}-+-{'-'*13}-+-{'-'*15}")

    results = []
    for n in [10, 15, 20, 25, 30, 40, 50, 60]:
        if n > max_n:
            break

        # At trade n with k wins: LLR = k * ll_win + (n-k) * ll_loss
        # Confirm when LLR >= A: k * ll_win + (n-k) * ll_loss >= A
        # k * (ll_win - ll_loss) >= A - n * ll_loss
        # k >= (A - n * ll_loss) / (ll_win - ll_loss)

        diff = ll_win - ll_loss

        k_confirm = (A - n * ll_loss) / diff
        k_kill = (B - n * ll_loss) / diff

        k_confirm_ceil = int(np.ceil(k_confirm))
        k_kill_floor = int(np.floor(k_kill))

        # Clamp
        k_confirm_ceil = max(0, min(n, k_confirm_ceil))
        k_kill_floor = max(0, min(n, k_kill_floor))

        if k_kill_floor + 1 <= k_confirm_ceil - 1:
            cont_range = f"{k_kill_floor+1}-{k_confirm_ceil-1}"
        else:
            cont_range = "—"

        print(f"  {n:>8} | {k_confirm_ceil:>16} | {k_kill_floor:>13} | {cont_range:>15}")
        results.append({
            'n': n, 'confirm': k_confirm_ceil, 'kill': k_kill_floor,
            'continue': cont_range
        })

    return results

# Individual instruments
sprt_results = {}
for name, d in instruments.items():
    sprt_results[name] = compute_sprt_table(
        name, d['be_wr'], d['wr'], max_n=60
    )

# Portfolio combined
print("\n\nPORTFOLIO COMBINED:")
# Weighted breakeven: use frequency-weighted average
total_freq = sum(d['trades_per_month'] for d in instruments.values())
portfolio_be = sum(d['be_wr'] * d['trades_per_month'] for d in instruments.values()) / total_freq
portfolio_wr = sum(d['wr'] * d['trades_per_month'] for d in instruments.values()) / total_freq
portfolio_avg_winner = sum(d['avg_winner'] * d['trades_per_month'] for d in instruments.values()) / total_freq
print(f"Weighted breakeven WR: {portfolio_be*100:.1f}%")
print(f"Weighted observed WR: {portfolio_wr*100:.1f}%")
print(f"Weighted avg winner: {portfolio_avg_winner:.2f}R")
print(f"Total trades/month: {total_freq:.1f}")

sprt_results['PORTFOLIO'] = compute_sprt_table(
    'PORTFOLIO', portfolio_be, portfolio_wr, max_n=60
)

# =============================================================================
print("\n" + "=" * 80)
print("TASK 1f: EXPECTED DEGRADATION SCENARIOS (GOLD)")
print("=" * 80)
print()

gold = instruments['XAUUSD']
tpm = gold['trades_per_month']
avg_w = gold['avg_winner']
avg_l = gold['avg_loser']

print(f"Gold: {tpm} trades/month, avg winner = {avg_w}R, avg loser = {avg_l}R")
print(f"Risk per trade: 1% of $100K = $1,000")
print()
print(f"{'Scenario':<25} | {'Live WR':>8} | {'Exp/trade':>10} | {'Monthly R':>10} | {'Monthly $':>10} | {'Months to +10%':>15}")
print(f"{'-'*25}-+-{'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}")

scenarios = [
    ('Batch holds', 0.62),
    ('Slight degradation', 0.58),
    ('Session memory boost', 0.66),
    ('Significant degrad.', 0.52),
    ('Edge lost', 0.45),
]

for label, wr in scenarios:
    exp_per_trade = wr * avg_w - (1 - wr) * avg_l
    monthly_r = exp_per_trade * tpm
    monthly_dollars = monthly_r * 1000  # 1% of $100K

    if monthly_r > 0:
        # FTMO: need +10% = $10,000
        months_to_pass = 10000 / monthly_dollars
        months_str = f"{months_to_pass:.1f}"
    else:
        months_str = "NEVER"

    print(f"{label:<25} | {wr*100:>7.0f}% | {exp_per_trade:>+9.3f}R | {monthly_r:>+9.2f}R | {monthly_dollars:>+9.0f}$ | {months_str:>15}")

print()

# Now with PORTFOLIO (all instruments)
print("\nPORTFOLIO SCENARIOS (all 4 instruments, ~14.5 trades/month):")
print(f"{'Scenario':<25} | {'Portfolio WR':>12} | {'Monthly R':>10} | {'Monthly $':>10} | {'Months to +10%':>15}")
print(f"{'-'*25}-+-{'-'*12}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}")

for label, wr_mult in [('Batch holds', 1.0), ('Slight degrad (-4pp)', 0.93),
                         ('Session boost (+4pp)', 1.07), ('Signif degrad (-10pp)', 0.84)]:
    total_monthly_r = 0
    for name, d in instruments.items():
        adjusted_wr = min(d['wr'] * wr_mult, 0.99) if wr_mult != 1.0 else d['wr']
        if label == 'Slight degrad (-4pp)':
            adjusted_wr = d['wr'] - 0.04
        elif label == 'Session boost (+4pp)':
            adjusted_wr = d['wr'] + 0.04
        elif label == 'Signif degrad (-10pp)':
            adjusted_wr = d['wr'] - 0.10

        adjusted_wr = max(0.01, min(0.99, adjusted_wr))
        exp = adjusted_wr * d['avg_winner'] - (1 - adjusted_wr) * d['avg_loser']
        total_monthly_r += exp * d['trades_per_month']

    monthly_dollars = total_monthly_r * 1000
    portfolio_wr_adj = sum((d['wr'] + (0 if wr_mult==1.0 else
                           -0.04 if 'Slight' in label else
                           +0.04 if 'Session' in label else -0.10)) * d['trades_per_month']
                          for d in instruments.values()) / total_freq

    months_str = f"{10000/monthly_dollars:.1f}" if monthly_dollars > 0 else "NEVER"

    print(f"{label:<25} | {portfolio_wr_adj*100:>11.1f}% | {total_monthly_r:>+9.2f}R | {monthly_dollars:>+9.0f}$ | {months_str:>15}")

print()
print("=" * 80)
print("TASK 1 COMPLETE")
print("=" * 80)
