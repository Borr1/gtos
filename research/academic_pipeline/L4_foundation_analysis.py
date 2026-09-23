#!/usr/bin/env python3
"""L4 Foundation Analysis — All $0 computable items from L4 actionable inventory.

Computes ~50 testable hypotheses from the 128 L4 actionable items using
the existing entry_engineering_dataset (129 trades) and all_evaluations_features
(31k candle evaluations). No API calls needed.

Output: research/academic_pipeline/results/L4_foundation_results_v1.md
"""

import json
import warnings
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

BASE = Path("/Users/borr/Documents/trading/gold-agent")
DATA = BASE / "research/academic_pipeline/data"
OUT = BASE / "research/academic_pipeline/results/L4_foundation_results_v1.md"

# ─── Load data ───────────────────────────────────────────────────────────
trades = pd.read_csv(DATA / "entry_engineering_dataset.csv")
trades["date"] = pd.to_datetime(trades["date"])
trades["candle_time"] = pd.to_datetime(trades["candle_time"], errors="coerce")

# Load all evaluations for drift/BOS analysis
evals = pd.read_csv(DATA / "all_evaluations_features.csv")
evals["candle_time"] = pd.to_datetime(evals["candle_time"], errors="coerce")

# Load P2A winning results for per-trade AI decision data
with open(DATA / "P2A_s46_max_new_results.json") as f:
    p2a = json.load(f)
p2a_rows = pd.DataFrame(p2a["rows"])

# XAUUSD-only subset for gold-specific tests
gold = trades[trades.symbol == "XAUUSD"].copy()

results = []
results.append("# L4 Foundation Analysis Results\n")
results.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
results.append(f"**Trades:** {len(trades)} ({len(gold)} XAUUSD, {len(trades)-len(gold)} GBPUSD)")
results.append(f"**Candle evaluations:** {len(evals):,}")
results.append(f"**Date range:** {trades.date.min().date()} to {trades.date.max().date()}")
results.append(f"**WR:** {trades.win.mean():.1%} | **Mean R:** {trades.r_multiple.mean():.3f}")
results.append("")

# ═══════════════════════════════════════════════════════════════════════════
# CLUSTER A: STOP-LOSS REFINEMENT
# ═══════════════════════════════════════════════════════════════════════════
results.append("---\n## CLUSTER A: STOP-LOSS REFINEMENT\n")

# ─── A1: Sweeney MAE Scatter ────────────────────────────────────────────
results.append("### A1: Sweeney MAE Scatter — Optimal SL Calibration")
t = trades.dropna(subset=["mae_r", "sl_distance"])
winners = t[t.win == 1]
losers = t[t.win == 0]

results.append(f"\n**Winner MAE (n={len(winners)}):**")
for pct in [50, 75, 80, 85, 90, 95]:
    results.append(f"  P{pct}: {winners.mae_r.quantile(pct/100):.3f}R")

results.append(f"\n**Loser MAE (n={len(losers)}):**")
for pct in [50, 75, 80, 85, 90, 95]:
    results.append(f"  P{pct}: {losers.mae_r.quantile(pct/100):.3f}R")

# The key insight: what % of winners would survive at different MAE cutoffs
results.append("\n**Winner survival at MAE thresholds (% retained if SL = threshold):**")
for thresh in [0.3, 0.5, 0.7, 0.8, 0.9, 1.0]:
    pct_survive = (winners.mae_r <= thresh).mean()
    results.append(f"  SL={thresh:.1f}R: {pct_survive:.1%} of winners survive")

# Current SL: the OB boundary is approximately 1.0R by definition (since R = distance to SL)
# So MAE of 1.0R means the trade was stopped out
results.append(f"\n**Interpretation:** Current SL = 1.0R by definition.")
results.append(f"Winners with MAE > 0.8R (nearly stopped out): {(winners.mae_r > 0.8).mean():.1%}")
results.append(f"Winners with MAE > 0.5R (significant heat): {(winners.mae_r > 0.5).mean():.1%}")
results.append(f"Median winner MAE: {winners.mae_r.median():.3f}R")
results.append(f"Median loser MAE: {losers.mae_r.median():.3f}R (capped at 1.0R)")
results.append("")

# ─── A3: GPD Fit to MAE tail ────────────────────────────────────────────
results.append("### A3: GPD / Heavy Tail Check on MAE")
from scipy.stats import genpareto, normaltest, kurtosis as sp_kurtosis

mae_data = trades.mae_r.dropna().values
results.append(f"MAE kurtosis: {sp_kurtosis(mae_data):.2f} (>0 = heavier than normal)")
stat, p_normal = normaltest(mae_data)
results.append(f"D'Agostino-Pearson normality test: stat={stat:.1f}, p={p_normal:.2e}")
results.append(f"  -> {'REJECT normality' if p_normal < 0.05 else 'Cannot reject normality'}")

# Fit GPD to upper tail (above P75)
threshold = np.percentile(mae_data, 75)
exceedances = mae_data[mae_data > threshold] - threshold
if len(exceedances) > 10:
    try:
        shape, loc, scale = genpareto.fit(exceedances, floc=0)
        results.append(f"GPD fit (exceedances above P75={threshold:.3f}):")
        results.append(f"  Shape (xi): {shape:.3f} ({'heavy-tailed' if shape > 0 else 'light-tailed'})")
        results.append(f"  Scale: {scale:.3f}")
        results.append(f"  Expected range xi=0.3-0.4 per Khan et al. (2023)")
    except Exception as e:
        results.append(f"  GPD fit failed: {e}")
results.append("")

# ─── A6: Tail Asymmetry (MAE vs MFE) ────────────────────────────────────
results.append("### A6: Tail Asymmetry — MAE vs MFE")
mfe_data = trades.mfe_r.dropna().values

results.append(f"MAE: mean={np.mean(mae_data):.3f}, std={np.std(mae_data):.3f}, skew={stats.skew(mae_data):.3f}")
results.append(f"MFE: mean={np.mean(mfe_data):.3f}, std={np.std(mfe_data):.3f}, skew={stats.skew(mfe_data):.3f}")

# Fit GPD to both tails
mfe_thresh = np.percentile(mfe_data, 75)
mfe_exc = mfe_data[mfe_data > mfe_thresh] - mfe_thresh
if len(mfe_exc) > 10:
    try:
        mfe_shape, _, mfe_scale = genpareto.fit(mfe_exc, floc=0)
        results.append(f"MFE GPD shape (xi): {mfe_shape:.3f}")
        results.append(f"MAE GPD shape (xi): {shape:.3f}")
        if shape > mfe_shape:
            results.append(f"  -> MAE tail IS heavier than MFE (asymmetric risk confirmed)")
            results.append(f"  -> SL needs more buffer than TP distance, per MDPI (2025)")
        else:
            results.append(f"  -> Tails are roughly symmetric")
    except Exception:
        pass
results.append("")

# ─── A7: Vol-Regime SL Adequacy ──────────────────────────────────────────
results.append("### A7: Volatility-Regime SL Adequacy")
t_vol = trades.dropna(subset=["sl_distance_atr", "mae_r"])
if len(t_vol) > 20:
    median_atr = t_vol.sl_distance_atr.median()
    hi_vol = t_vol[t_vol.sl_distance_atr <= median_atr]  # smaller ATR ratio = tighter SL relative to vol
    lo_vol = t_vol[t_vol.sl_distance_atr > median_atr]

    results.append(f"Median SL/ATR ratio: {median_atr:.2f}")
    results.append(f"High-vol group (SL/ATR <= median): n={len(hi_vol)}, MAE mean={hi_vol.mae_r.mean():.3f}R")
    results.append(f"Low-vol group (SL/ATR > median): n={len(lo_vol)}, MAE mean={lo_vol.mae_r.mean():.3f}R")

    stat_u, p_u = stats.mannwhitneyu(hi_vol.mae_r, lo_vol.mae_r, alternative="two-sided")
    results.append(f"Mann-Whitney U: stat={stat_u:.0f}, p={p_u:.4f}")
    results.append(f"  -> {'SIGNIFICANT' if p_u < 0.05 else 'Not significant'}: vol regime {'does' if p_u < 0.05 else 'does not'} affect MAE")
results.append("")

# ─── A8 + A11: Round-Number SL Effects (XAUUSD only) ────────────────────
results.append("### A8 + A11: Round-Number SL Effects (XAUUSD)")
g = gold.dropna(subset=["stop_loss", "mae_r"])
if len(g) > 20:
    g = g.copy()
    g["sl_to_5"] = g.stop_loss.apply(lambda x: min(x % 5, 5 - x % 5))
    g["sl_to_10"] = g.stop_loss.apply(lambda x: min(x % 10, 10 - x % 10))
    g["near_round_5"] = g.sl_to_5 <= 2.0  # within $2 of $5 increment
    g["near_round_10"] = g.sl_to_10 <= 3.0  # within $3 of $10 increment

    results.append(f"SL within $2 of $5 round: {g.near_round_5.sum()} ({g.near_round_5.mean():.1%})")
    results.append(f"SL within $3 of $10 round: {g.near_round_10.sum()} ({g.near_round_10.mean():.1%})")

    near = g[g.near_round_5]
    far = g[~g.near_round_5]
    if len(near) >= 5 and len(far) >= 5:
        results.append(f"\nNear-round MAE: {near.mae_r.mean():.3f}R (n={len(near)})")
        results.append(f"Far-from-round MAE: {far.mae_r.mean():.3f}R (n={len(far)})")
        stat, p = stats.mannwhitneyu(near.mae_r, far.mae_r, alternative="greater")
        results.append(f"MWU (near > far): p={p:.4f}")
        results.append(f"  -> {'CONFIRMED' if p < 0.10 else 'NOT confirmed'}: round-number SL proximity {'amplifies' if p < 0.10 else 'does not amplify'} MAE")

    # A11: Chi-squared test for clustering
    # Under uniform, each $1 bin should have equal probability
    # Bin distances to $5 round: 0-0.5, 0.5-1.0, 1.0-1.5, 1.5-2.0, 2.0-2.5
    bins = pd.cut(g.sl_to_5, bins=[0, 0.5, 1.0, 1.5, 2.0, 2.5], right=True)
    observed = bins.value_counts().sort_index().values
    n_obs = observed.sum()
    n_bins = len(observed)
    expected = np.full(n_bins, n_obs / n_bins)
    chi2, p_chi = stats.chisquare(observed, expected)
    results.append(f"\nA11 Chi-squared (SL clustering at $5 rounds): chi2={chi2:.2f}, p={p_chi:.4f}")
    results.append(f"  -> {'SL CLUSTERS' if p_chi < 0.05 else 'No clustering'} at round numbers")
results.append("")

# ─── A15: Serial Correlation of M15 Returns ─────────────────────────────
results.append("### A15: Serial Correlation Check (validates SL framework)")
# Use trade-level returns as proxy (sequential trades)
# Sort by date and compute return autocorrelation
sorted_r = trades.sort_values("date").r_multiple.values
if len(sorted_r) > 20:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    # Lag-1 autocorrelation
    acf1 = np.corrcoef(sorted_r[:-1], sorted_r[1:])[0, 1]
    results.append(f"Trade-level R-multiple ACF(1): {acf1:.4f}")
    try:
        lb_result = acorr_ljungbox(sorted_r, lags=[1, 2, 3, 5], return_df=True)
        results.append("Ljung-Box test:")
        for lag, row in lb_result.iterrows():
            results.append(f"  Lag {lag}: stat={row['lb_stat']:.2f}, p={row['lb_pvalue']:.4f}")
        results.append(f"  -> {'SERIAL CORRELATION DETECTED' if lb_result.iloc[0]['lb_pvalue'] < 0.05 else 'No serial correlation (trades are independent)'}")
    except Exception as e:
        results.append(f"  Ljung-Box failed: {e}")
results.append("")

# ─── A20 + A21 + A25 + A26: Kelly / Position Sizing ─────────────────────
results.append("### A20-A26: Kelly Sizing Analysis")
R = trades.r_multiple.values
wr = trades.win.mean()
avg_win = trades[trades.win == 1].r_multiple.mean()
avg_loss = abs(trades[trades.win == 0].r_multiple.mean())

# A20: Binary Kelly
f_kelly = (wr * avg_win - (1 - wr) * avg_loss) / (avg_win * avg_loss) if avg_win > 0 and avg_loss > 0 else 0
results.append(f"**A20: Binary Kelly**")
results.append(f"  WR={wr:.3f}, Avg Win={avg_win:.3f}R, Avg Loss={avg_loss:.3f}R")
results.append(f"  Kelly f* = {f_kelly:.3f} ({f_kelly*100:.1f}% of account)")
results.append(f"  Half-Kelly = {f_kelly/2:.3f} ({f_kelly*50:.1f}%)")
results.append(f"  Current: 1.0% -> {1.0/f_kelly/100:.1f}x fraction of Kelly" if f_kelly > 0 else "  Kelly is zero/negative")

# A21: Vince optimal f (maximize geometric growth)
results.append(f"\n**A21: Vince Optimal f (full distribution)**")
worst_loss = abs(R.min())
best_f = 0
best_g = -999
f_range = np.arange(0.001, 0.50, 0.001)
g_values = []
for f in f_range:
    hpr = 1 + f * R / worst_loss
    if np.any(hpr <= 0):
        g_values.append(-999)
        continue
    g = np.exp(np.mean(np.log(hpr))) - 1
    g_values.append(g)
    if g > best_g:
        best_g = g
        best_f = f

g_values = np.array(g_values)
results.append(f"  Worst loss: {-worst_loss:.3f}R")
results.append(f"  Optimal f: {best_f:.3f} ({best_f*100:.1f}%)")
results.append(f"  Geometric growth at optimal: {best_g:.6f}")
results.append(f"  Growth at f=0.01 (current 1%): {g_values[9]:.6f}")
results.append(f"  Growth at f=0.02 (2%): {g_values[19]:.6f}")
results.append(f"  Growth at f=0.03 (3%): {g_values[29]:.6f}")

# A26: Verify unimodality
valid_g = g_values[g_values > -999]
peak_idx = np.argmax(valid_g)
is_unimodal = all(valid_g[:peak_idx+1][i] <= valid_g[:peak_idx+1][i+1] for i in range(peak_idx)) if peak_idx > 0 else True
results.append(f"\n**A26: Unimodality check:** {'CONFIRMED (single peak)' if is_unimodal else 'NOT unimodal'}")

# A25: Multi-outcome Kelly
results.append(f"\n**A25: Multi-Outcome Kelly**")
buckets = {
    "Full TP (>1.0R)": R[R > 1.0],
    "Partial win (0-1R)": R[(R > 0) & (R <= 1.0)],
    "Breakeven (-0.1 to 0.1R)": R[(R >= -0.1) & (R <= 0.1)],
    "Partial loss (-1 to -0.1R)": R[(R < -0.1) & (R > -1.0)],
    "Full SL (-1R)": R[R <= -1.0],
}
for name, vals in buckets.items():
    if len(vals) > 0:
        results.append(f"  {name}: n={len(vals)} ({len(vals)/len(R):.1%}), mean R={vals.mean():.3f}")
    else:
        results.append(f"  {name}: n=0")

# FTMO-specific: P(pass) at different f values using Monte Carlo
results.append(f"\n**FTMO Monte Carlo (10k paths, 90 trading days, current WR/RR):**")
np.random.seed(42)
n_sims = 10000
for f_test in [0.01, 0.015, 0.02, 0.025, 0.03]:
    equity_paths = np.ones(n_sims)
    max_equity = np.ones(n_sims)
    failed = np.zeros(n_sims, dtype=bool)
    for day in range(90):
        # ~0.4 trades per day (17/month / 22 days)
        if np.random.random() < 0.4:
            trade_r = np.random.choice(R, size=n_sims)
            pnl = f_test * trade_r
            equity_paths *= (1 + pnl)
            max_equity = np.maximum(max_equity, equity_paths)
            dd = 1 - equity_paths / max_equity
            failed |= dd > 0.10  # FTMO max DD
            failed |= (equity_paths < 0.96)  # daily loss proxy

    passed = (equity_paths >= 1.10) & ~failed  # 10% profit target
    results.append(f"  f={f_test*100:.1f}%: P(pass)={passed.mean():.1%}, P(bust)={failed.mean():.1%}, median equity={np.median(equity_paths[~failed]):.3f}")
results.append("")

# ─── A27: MAE by Kill Zone ───────────────────────────────────────────────
results.append("### A27: MAE by Kill Zone")
for kz in ["london", "ny"]:
    kz_trades = trades[trades.kill_zone == kz].dropna(subset=["mae_r"])
    if len(kz_trades) > 5:
        results.append(f"  {kz.upper()}: n={len(kz_trades)}, MAE mean={kz_trades.mae_r.mean():.3f}R, median={kz_trades.mae_r.median():.3f}R, P90={kz_trades.mae_r.quantile(0.9):.3f}R")

ldn = trades[(trades.kill_zone == "london")].mae_r.dropna()
ny = trades[(trades.kill_zone == "ny")].mae_r.dropna()
if len(ldn) > 5 and len(ny) > 5:
    stat, p = stats.mannwhitneyu(ldn, ny, alternative="two-sided")
    results.append(f"  MWU test: p={p:.4f}")
    results.append(f"  -> {'SIGNIFICANT difference' if p < 0.05 else 'No significant difference'} in MAE between sessions")
results.append("")


# ═══════════════════════════════════════════════════════════════════════════
# CLUSTER B: EXIT OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════
results.append("---\n## CLUSTER B: EXIT OPTIMIZATION\n")

# ─── B36: Conditional MFE Distribution (Foundation) ──────────────────────
results.append("### B36: Conditional MFE Distribution (FOUNDATION)")
mfe = trades.mfe_r.dropna()
results.append(f"\n**Unconditional P(reaching nR):**")
for n in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    p = (mfe >= n).mean()
    results.append(f"  P(MFE >= {n:.1f}R): {p:.1%} (n={(mfe >= n).sum()})")

results.append(f"\n**Conditional P(nR | mR reached) — the key exit table:**")
for m in [0.5, 1.0, 1.5, 2.0]:
    subset = mfe[mfe >= m]
    if len(subset) < 5:
        continue
    results.append(f"\n  Given MFE >= {m:.1f}R (n={len(subset)}):")
    for n in [m + 0.5, m + 1.0, m + 1.5, m + 2.0]:
        if n > 5:
            break
        p_cond = (subset >= n).mean()
        results.append(f"    P(MFE >= {n:.1f}R | >= {m:.1f}R): {p_cond:.1%} (n={(subset >= n).sum()})")

# ─── B1 + B2: P(2R|1R) and Kelly Runner Fraction ────────────────────────
results.append("\n### B1 + B2: Partial Close Decision")
reached_1r = mfe[mfe >= 1.0]
if len(reached_1r) > 5:
    p_2r_given_1r = (reached_1r >= 2.0).mean()
    results.append(f"P(2R | 1R reached): {p_2r_given_1r:.1%} (n_reached_1R={len(reached_1r)}, n_reached_2R={(reached_1r >= 2.0).sum()})")

    if p_2r_given_1r > 0 and p_2r_given_1r < 1:
        # Kelly for runner: f2* = (p*b - q) / b where b = additional 1R payoff
        b2 = 1.0  # additional R from 1R to 2R
        q2 = 1 - p_2r_given_1r
        f2_kelly = (p_2r_given_1r * b2 - q2) / b2
        results.append(f"Kelly-optimal runner fraction: f2* = {f2_kelly:.3f}")

        if p_2r_given_1r >= 0.50:
            results.append(f"  -> P(2R|1R) >= 50%: HOLD at 1R is correct. Partial close DESTROYS value.")
        else:
            results.append(f"  -> P(2R|1R) < 50%: EXIT at 1R is optimal. Partial close ADDS value.")

    p_3r_given_2r = 0
    reached_2r = mfe[mfe >= 2.0]
    if len(reached_2r) > 3:
        p_3r_given_2r = (reached_2r >= 3.0).mean()
        results.append(f"P(3R | 2R reached): {p_3r_given_2r:.1%} (n={len(reached_2r)})")
results.append("")

# ─── B4: MFE Skewness ───────────────────────────────────────────────────
results.append("### B4: MFE Distribution Skewness (partial close indicator)")
winners_mfe = trades[trades.win == 1].mfe_r.dropna()
results.append(f"Winner MFE skewness: {stats.skew(winners_mfe):.3f}")
results.append(f"  -> {'RIGHT-SKEWED (>0.5): partial close at 1R may truncate big winners' if stats.skew(winners_mfe) > 0.5 else 'MODERATE/LOW skew: partial close is reasonable'}")
results.append(f"Conditional MFE skewness (MFE > 1R): {stats.skew(mfe[mfe > 1.0]):.3f}" if len(mfe[mfe > 1.0]) > 5 else "")
results.append("")

# ─── B23: Implementation Shortfall Decomposition ────────────────────────
results.append("### B23: Implementation Shortfall (IS) Decomposition")
t_is = trades.dropna(subset=["mfe_r", "r_multiple"])
t_is = t_is.copy()
t_is["IS"] = t_is.mfe_r - t_is.r_multiple  # how much was left on the table
results.append(f"Overall IS: mean={t_is.IS.mean():.3f}R, median={t_is.IS.median():.3f}R")

winners_is = t_is[t_is.win == 1]
losers_is = t_is[t_is.win == 0]
results.append(f"\n**Winners (early exit cost):**")
results.append(f"  IS mean: {winners_is.IS.mean():.3f}R (MFE captured: {(winners_is.r_multiple / winners_is.mfe_r).replace([np.inf, -np.inf], np.nan).dropna().mean():.1%})")
results.append(f"  Trades where MFE > 2x actual R: {(winners_is.mfe_r > 2 * winners_is.r_multiple.clip(0.01)).sum()} ({(winners_is.mfe_r > 2 * winners_is.r_multiple.clip(0.01)).mean():.1%})")
results.append(f"\n**Losers (reversal cost):**")
results.append(f"  IS mean: {losers_is.IS.mean():.3f}R")
results.append(f"  Losers with MFE > 0.5R (was in profit then reversed): {(losers_is.mfe_r > 0.5).sum()} ({(losers_is.mfe_r > 0.5).mean():.1%})")
results.append(f"  Losers with MFE > 1.0R (was at +1R then lost): {(losers_is.mfe_r > 1.0).sum()} ({(losers_is.mfe_r > 1.0).mean():.1%})")

# Which IS component is larger?
total_early_exit = winners_is.IS.sum()
total_reversal = losers_is.IS.sum()
results.append(f"\n**Total IS breakdown:**")
results.append(f"  Early exit cost (winners): {total_early_exit:.1f}R")
results.append(f"  Reversal cost (losers): {total_reversal:.1f}R")
results.append(f"  -> {'EARLY EXIT dominates: wider TP or trailing stop is priority' if total_early_exit > total_reversal else 'REVERSAL dominates: tighter stops are priority'}")
results.append("")

# ─── B24: Late KZ Entry Outcomes ─────────────────────────────────────────
results.append("### B24: Entry Timing Within Kill Zone")
t_time = trades.dropna(subset=["candle_time"]).copy()
t_time["hour"] = t_time.candle_time.dt.hour
t_time["minute"] = t_time.candle_time.dt.minute
t_time["time_decimal"] = t_time.hour + t_time.minute / 60

for kz in ["london", "ny"]:
    kz_t = t_time[t_time.kill_zone == kz]
    if len(kz_t) < 10:
        continue
    q33 = kz_t.time_decimal.quantile(0.33)
    q67 = kz_t.time_decimal.quantile(0.67)
    early = kz_t[kz_t.time_decimal <= q33]
    mid = kz_t[(kz_t.time_decimal > q33) & (kz_t.time_decimal <= q67)]
    late = kz_t[kz_t.time_decimal > q67]
    results.append(f"\n**{kz.upper()} kill zone:**")
    for label, group in [("Early", early), ("Mid", mid), ("Late", late)]:
        if len(group) > 0:
            results.append(f"  {label}: n={len(group)}, WR={group.win.mean():.1%}, mean R={group.r_multiple.mean():.3f}")

results.append("")

# ─── B25: Trade Management Efficient Frontier ───────────────────────────
results.append("### B25: Exit Strategy Efficient Frontier")
results.append("*Simulated exits at different R-levels using MFE/MAE data:*\n")

t_exit = trades.dropna(subset=["mfe_r", "mae_r"]).copy()
for exit_r in [0.5, 1.0, 1.5, 2.0, 2.5]:
    # If MFE >= exit_r, trade would have reached this level -> exit at exit_r
    # If MFE < exit_r, trade didn't reach it -> actual outcome
    simulated_r = np.where(t_exit.mfe_r >= exit_r, exit_r, t_exit.r_multiple)
    mean_r = simulated_r.mean()
    var_r = simulated_r.var()
    sharpe = mean_r / np.sqrt(var_r) if var_r > 0 else 0
    wr_sim = (simulated_r > 0).mean()
    results.append(f"  TP={exit_r:.1f}R: E[R]={mean_r:.3f}, Var={var_r:.3f}, Sharpe={sharpe:.3f}, WR={wr_sim:.1%}")

# Actual outcomes for comparison
mean_actual = t_exit.r_multiple.mean()
var_actual = t_exit.r_multiple.var()
sharpe_actual = mean_actual / np.sqrt(var_actual) if var_actual > 0 else 0
results.append(f"  Actual: E[R]={mean_actual:.3f}, Var={var_actual:.3f}, Sharpe={sharpe_actual:.3f}, WR={t_exit.win.mean():.1%}")
results.append("")

# ─── B28: MFE scales with volatility ────────────────────────────────────
results.append("### B28: MFE vs Volatility Correlation")
t_vol2 = trades.dropna(subset=["mfe_r", "sl_distance_atr"])
if len(t_vol2) > 20:
    corr_p, p_p = stats.pearsonr(t_vol2.sl_distance_atr, t_vol2.mfe_r)
    corr_s, p_s = stats.spearmanr(t_vol2.sl_distance_atr, t_vol2.mfe_r)
    results.append(f"SL/ATR ratio vs MFE:")
    results.append(f"  Pearson: r={corr_p:.3f}, p={p_p:.4f}")
    results.append(f"  Spearman: rho={corr_s:.3f}, p={p_s:.4f}")
    results.append(f"  -> {'SIGNIFICANT: MFE scales with vol' if p_s < 0.05 else 'NOT significant'}")
results.append("")

# ─── B34: High-Vol Negative Skew ─────────────────────────────────────────
results.append("### B34: High-Vol Regime Risk (Skewness)")
t_skew = trades.dropna(subset=["sl_distance_atr", "r_multiple"])
if len(t_skew) > 20:
    med = t_skew.sl_distance_atr.median()
    hi = t_skew[t_skew.sl_distance_atr <= med]
    lo = t_skew[t_skew.sl_distance_atr > med]
    results.append(f"High-vol (tight SL/ATR): n={len(hi)}, R skew={stats.skew(hi.r_multiple):.3f}")
    results.append(f"Low-vol (wide SL/ATR): n={len(lo)}, R skew={stats.skew(lo.r_multiple):.3f}")
results.append("")


# ═══════════════════════════════════════════════════════════════════════════
# CLUSTER C: ALPHA DECAY AND CROWDING
# ═══════════════════════════════════════════════════════════════════════════
results.append("---\n## CLUSTER C: ALPHA DECAY AND CROWDING\n")

# ─── C1: Two-Proportion Z-Test (First Half vs Second Half) ──────────────
results.append("### C1: Formal Decay Test — First Half vs Second Half")
sorted_trades = trades.sort_values("date")
half = len(sorted_trades) // 2
first_half = sorted_trades.iloc[:half]
second_half = sorted_trades.iloc[half:]

wr1 = first_half.win.mean()
wr2 = second_half.win.mean()
n1, n2 = len(first_half), len(second_half)
p_pooled = trades.win.mean()
se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
z = (wr1 - wr2) / se if se > 0 else 0
p_z = 2 * (1 - stats.norm.cdf(abs(z)))

results.append(f"First half: WR={wr1:.1%} (n={n1}), dates={first_half.date.min().date()} to {first_half.date.max().date()}")
results.append(f"Second half: WR={wr2:.1%} (n={n2}), dates={second_half.date.min().date()} to {second_half.date.max().date()}")
results.append(f"Difference: {(wr1-wr2)*100:.1f}pp")
results.append(f"Two-proportion z-test: z={z:.3f}, p={p_z:.4f}")
results.append(f"  -> {'SIGNIFICANT decay' if p_z < 0.05 else 'NOT significant (cannot confirm decay)'}")
results.append("")

# ─── C6: Impulse Size vs R-Multiple ─────────────────────────────────────
results.append("### C6: Impulse Size Correlation with Trade Outcome")
# Use sl_distance as proxy for impulse size (OB boundary ~ impulse candle)
t_imp = trades.dropna(subset=["sl_distance", "r_multiple"])
if len(t_imp) > 20:
    corr, p = stats.spearmanr(t_imp.sl_distance, t_imp.r_multiple)
    results.append(f"SL distance (impulse proxy) vs R-multiple: rho={corr:.3f}, p={p:.4f}")
    results.append(f"  -> {'CONFIRMS OFI mechanism' if p < 0.05 and corr > 0 else 'Does not confirm OFI'}")
results.append("")

# ─── C7: Session WR Comparison ───────────────────────────────────────────
results.append("### C7: Win Rate by Session")
for kz in trades.kill_zone.unique():
    kz_t = trades[trades.kill_zone == kz]
    results.append(f"  {kz.upper()}: WR={kz_t.win.mean():.1%} (n={len(kz_t)}), mean R={kz_t.r_multiple.mean():.3f}")

# Fisher exact for London vs NY
ldn_t = trades[trades.kill_zone == "london"]
ny_t = trades[trades.kill_zone == "ny"]
table = [[ldn_t.win.sum(), len(ldn_t) - ldn_t.win.sum()],
         [ny_t.win.sum(), len(ny_t) - ny_t.win.sum()]]
_, p_fisher = stats.fisher_exact(table)
results.append(f"Fisher exact (London vs NY): p={p_fisher:.4f}")
results.append(f"  -> {'SIGNIFICANT difference' if p_fisher < 0.05 else 'No significant difference'}")
results.append("")

# ─── C14: Average Winning R-Multiple Over Time ──────────────────────────
results.append("### C14: Winning Trade Magnitude Over Time")
sorted_wins = trades[trades.win == 1].sort_values("date").copy()
if len(sorted_wins) > 20:
    sorted_wins["order"] = range(len(sorted_wins))
    corr, p = stats.spearmanr(sorted_wins.order, sorted_wins.r_multiple)
    results.append(f"Spearman correlation (win order vs R): rho={corr:.3f}, p={p:.4f}")
    results.append(f"  -> {'DECLINING: winners getting smaller' if corr < 0 and p < 0.10 else 'STABLE: no compression in win magnitude'}")

    # Quartile breakdown
    q_size = len(sorted_wins) // 4
    for i, label in enumerate(["Q1 (earliest)", "Q2", "Q3", "Q4 (latest)"]):
        q = sorted_wins.iloc[i*q_size:(i+1)*q_size] if i < 3 else sorted_wins.iloc[i*q_size:]
        results.append(f"  {label}: mean win R={q.r_multiple.mean():.3f}, n={len(q)}")
results.append("")

# ─── C15: Tail Fattening — Worst Losses Growing ─────────────────────────
results.append("### C15: Loss Tail Evolution")
sorted_losses = trades[trades.win == 0].sort_values("date").copy()
if len(sorted_losses) > 10:
    half_l = len(sorted_losses) // 2
    first_losses = sorted_losses.iloc[:half_l]
    second_losses = sorted_losses.iloc[half_l:]
    results.append(f"First-half losses: mean R={first_losses.r_multiple.mean():.3f}, worst={first_losses.r_multiple.min():.3f}")
    results.append(f"Second-half losses: mean R={second_losses.r_multiple.mean():.3f}, worst={second_losses.r_multiple.min():.3f}")
    # Both halves have worst = -1.0R since SL caps it. Check if MAE is growing.
    first_mae = first_losses.mae_r.dropna()
    second_mae = second_losses.mae_r.dropna()
    if len(first_mae) > 3 and len(second_mae) > 3:
        results.append(f"First-half loser MAE P90: {first_mae.quantile(0.9):.3f}R")
        results.append(f"Second-half loser MAE P90: {second_mae.quantile(0.9):.3f}R")
        results.append(f"  -> {'TAIL FATTENING' if second_mae.quantile(0.9) > first_mae.quantile(0.9) + 0.05 else 'Stable tails'}")
results.append("")

# ─── C16: Failure Clustering (Loss Autocorrelation) ─────────────────────
results.append("### C16: Failure Clustering")
outcomes = trades.sort_values("date").win.values
# Count runs
runs = 1
for i in range(1, len(outcomes)):
    if outcomes[i] != outcomes[i - 1]:
        runs += 1

n_w = outcomes.sum()
n_l = len(outcomes) - n_w
expected_runs = 1 + 2 * n_w * n_l / (n_w + n_l)
var_runs = (2 * n_w * n_l * (2 * n_w * n_l - n_w - n_l)) / ((n_w + n_l)**2 * (n_w + n_l - 1))
z_runs = (runs - expected_runs) / np.sqrt(var_runs) if var_runs > 0 else 0
p_runs = 2 * (1 - stats.norm.cdf(abs(z_runs)))

results.append(f"Total outcomes: {len(outcomes)} (W={int(n_w)}, L={int(n_l)})")
results.append(f"Observed runs: {runs}")
results.append(f"Expected runs (independence): {expected_runs:.1f}")
results.append(f"Wald-Wolfowitz runs test: z={z_runs:.3f}, p={p_runs:.4f}")
if z_runs < 0 and p_runs < 0.05:
    results.append(f"  -> CLUSTERING CONFIRMED: losses cluster (z negative, fewer runs than expected)")
elif z_runs > 0 and p_runs < 0.05:
    results.append(f"  -> ALTERNATING: outcomes alternate more than random (z positive)")
else:
    results.append(f"  -> INDEPENDENT: no clustering detected")

# Also compute ACF
acf1_out = np.corrcoef(outcomes[:-1], outcomes[1:])[0, 1]
results.append(f"Outcome ACF(1): {acf1_out:.4f}")
# Max consecutive losses
max_consec_loss = 0
current = 0
for o in outcomes:
    if o == 0:
        current += 1
        max_consec_loss = max(max_consec_loss, current)
    else:
        current = 0
results.append(f"Max consecutive losses: {max_consec_loss}")
results.append("")

# ─── C19: Round-Number Zone Effects ──────────────────────────────────────
results.append("### C19: Round-Number OB Zone Continuation")
g_zone = gold.dropna(subset=["poi_price_level"])
if len(g_zone) > 10:
    g_zone = g_zone.copy()
    g_zone["poi_to_5"] = g_zone.poi_price_level.apply(lambda x: min(x % 5, 5 - x % 5))
    g_zone["poi_to_10"] = g_zone.poi_price_level.apply(lambda x: min(x % 10, 10 - x % 10))
    g_zone["near_round"] = g_zone.poi_to_10 <= 3.0

    near = g_zone[g_zone.near_round]
    far = g_zone[~g_zone.near_round]
    if len(near) >= 5 and len(far) >= 5:
        results.append(f"Zones near $10 round: WR={near.win.mean():.1%} (n={len(near)})")
        results.append(f"Zones far from round: WR={far.win.mean():.1%} (n={len(far)})")
        _, p_rn = stats.fisher_exact([[near.win.sum(), len(near)-near.win.sum()],
                                       [far.win.sum(), len(far)-far.win.sum()]])
        results.append(f"Fisher exact: p={p_rn:.4f}")
results.append("")

# ─── C20: Loss/Win Magnitude Asymmetry ──────────────────────────────────
results.append("### C20: Loss/Win Magnitude Asymmetry (Fade Effect)")
winners_r = trades[trades.win == 1].r_multiple
losers_r = trades[trades.win == 0].r_multiple
mean_win = winners_r.mean()
mean_loss_abs = abs(losers_r.mean())
ratio = mean_loss_abs / mean_win if mean_win > 0 else float("inf")
results.append(f"Mean win: +{mean_win:.3f}R")
results.append(f"Mean loss (abs): {mean_loss_abs:.3f}R")
results.append(f"Asymmetry ratio (loss/win): {ratio:.3f}")
results.append(f"  -> {'ASYMMETRIC: losses larger than wins (fade effect present)' if ratio > 1.0 else 'SYMMETRIC or favorable: wins >= losses'}")
results.append("")

# ─── C22: Continuation/Impulse Ratio Over Time ──────────────────────────
results.append("### C22: Edge Carrying Capacity — R vs Time")
sorted_all = trades.sort_values("date").copy()
sorted_all["order"] = range(len(sorted_all))
corr_decay, p_decay = stats.spearmanr(sorted_all.order, sorted_all.r_multiple)
results.append(f"R-multiple trend over all trades: rho={corr_decay:.3f}, p={p_decay:.4f}")
results.append(f"  -> {'DECLINING expectancy' if corr_decay < 0 and p_decay < 0.10 else 'No significant trend'}")
results.append("")

# ─── C29: R-Multiple Variance Over Time ─────────────────────────────────
results.append("### C29: Outcome Variance Evolution (Fragility)")
if len(sorted_all) > 40:
    half_v = len(sorted_all) // 2
    first_var = sorted_all.iloc[:half_v].r_multiple.var()
    second_var = sorted_all.iloc[half_v:].r_multiple.var()
    # Levene's test
    stat_lev, p_lev = stats.levene(sorted_all.iloc[:half_v].r_multiple, sorted_all.iloc[half_v:].r_multiple)
    results.append(f"First-half R variance: {first_var:.4f}")
    results.append(f"Second-half R variance: {second_var:.4f}")
    results.append(f"Levene's test: stat={stat_lev:.2f}, p={p_lev:.4f}")
    results.append(f"  -> {'VARIANCE INCREASING (fragility)' if second_var > first_var and p_lev < 0.10 else 'Stable variance'}")
results.append("")

# ─── C31: Observed Decay Rate vs FX TA Baseline ─────────────────────────
results.append("### C31: Decay Rate Benchmarking")
# Quarterly WR from known data
quarterly_wr = [73.2, 71.4, 63.6, 59.4]
results.append(f"Quarterly WR: {quarterly_wr}")
total_decline = quarterly_wr[0] - quarterly_wr[-1]
annualized = total_decline  # 4 quarters = 1 year
results.append(f"Total decline: {total_decline:.1f}pp over 4 quarters")
results.append(f"Annualized rate: ~{annualized:.1f}pp/year")
results.append(f"FX TA baseline (Menkhoff & Taylor): ~1pp/year")
results.append(f"Post-publication benchmark (McLean & Pontiff): ~5pp/year")
results.append(f"Observed: {annualized:.0f}x faster than FX TA, {annualized/5:.0f}x faster than post-pub")
results.append(f"  -> CRITICAL: {annualized:.0f}pp/year is too fast for pure edge decay. Regime effects likely dominate.")
results.append("")

# ─── C32: Monthly Trade Count vs Avg R ───────────────────────────────────
results.append("### C32: Trade Frequency vs Quality")
t_monthly = trades.copy()
t_monthly["month"] = t_monthly.date.dt.to_period("M")
monthly = t_monthly.groupby("month").agg(
    count=("r_multiple", "count"),
    mean_r=("r_multiple", "mean"),
    wr=("win", "mean"),
).reset_index()
if len(monthly) > 3:
    corr_mq, p_mq = stats.spearmanr(monthly["count"], monthly["mean_r"])
    results.append(f"Monthly trade count vs avg R: rho={corr_mq:.3f}, p={p_mq:.4f}")
    results.append(f"  -> {'NEGATIVE: more trades = lower quality' if corr_mq < 0 and p_mq < 0.10 else 'No significant relationship'}")
    results.append("\nMonthly breakdown:")
    for _, row in monthly.iterrows():
        results.append(f"  {row['month']}: n={row['count']:.0f}, WR={row['wr']:.1%}, E[R]={row['mean_r']:.3f}")
results.append("")

# ─── C33a-d: Regime Decomposition ────────────────────────────────────────
results.append("### C33: Regime Decomposition of Quarterly WR Decline\n")

# Create quarterly groups
t_q = trades.copy()
t_q["quarter"] = t_q.date.dt.to_period("Q")
q_stats = t_q.groupby("quarter").agg(
    n=("win", "count"),
    wr=("win", "mean"),
    mean_r=("r_multiple", "mean"),
).reset_index()

results.append("**Quarterly stats:**")
for _, row in q_stats.iterrows():
    results.append(f"  {row['quarter']}: n={row['n']}, WR={row['wr']:.1%}, E[R]={row['mean_r']:.3f}")

# C33a: ATR correlation
results.append(f"\n**C33a: Volatility regime**")
t_qa = trades.dropna(subset=["sl_distance_atr"]).copy()
t_qa["quarter"] = t_qa.date.dt.to_period("Q")
q_atr = t_qa.groupby("quarter").agg(
    mean_atr_ratio=("sl_distance_atr", "mean"),
    wr=("win", "mean"),
).reset_index()
if len(q_atr) > 2:
    corr_qa, p_qa = stats.spearmanr(q_atr.mean_atr_ratio, q_atr.wr)
    results.append(f"Quarterly ATR ratio vs WR: rho={corr_qa:.3f}, p={p_qa:.4f}")
    for _, row in q_atr.iterrows():
        results.append(f"  {row['quarter']}: ATR ratio={row['mean_atr_ratio']:.2f}, WR={row['wr']:.1%}")

# C33b: Session composition shift
results.append(f"\n**C33b: Session composition shift**")
t_qb = trades.copy()
t_qb["quarter"] = t_qb.date.dt.to_period("Q")
for q in t_qb.quarter.unique():
    qt = t_qb[t_qb.quarter == q]
    ldn_pct = (qt.kill_zone == "london").mean()
    ny_pct = (qt.kill_zone == "ny").mean()
    ldn_wr = qt[qt.kill_zone == "london"].win.mean() if (qt.kill_zone == "london").sum() > 0 else 0
    ny_wr = qt[qt.kill_zone == "ny"].win.mean() if (qt.kill_zone == "ny").sum() > 0 else 0
    results.append(f"  {q}: London={ldn_pct:.0%} (WR={ldn_wr:.0%}), NY={ny_pct:.0%} (WR={ny_wr:.0%})")

# C33c: Instrument composition
results.append(f"\n**C33c: Per-instrument WR trend**")
for sym in trades.symbol.unique():
    sym_t = trades[trades.symbol == sym].sort_values("date")
    if len(sym_t) < 10:
        continue
    sym_t = sym_t.copy()
    sym_t["quarter"] = sym_t.date.dt.to_period("Q")
    for q in sym_t.quarter.unique():
        qt = sym_t[sym_t.quarter == q]
        results.append(f"  {sym} {q}: WR={qt.win.mean():.1%} (n={len(qt)})")

# C33d: In-sample overlap check
results.append(f"\n**C33d: In-sample overlap risk**")
results.append(f"Earliest trade: {trades.date.min().date()}")
results.append(f"  -> If parameters were tuned on data before {trades.date.min().date()}, no overlap")
results.append(f"  -> If early trades overlap with optimization set, baseline WR is inflated")
results.append(f"  ACTION: audit parameter tuning dates against first-quarter trade dates")
results.append("")


# ═══════════════════════════════════════════════════════════════════════════
# CLUSTER D: DRIFT MONITORING FOUNDATION
# ═══════════════════════════════════════════════════════════════════════════
results.append("---\n## CLUSTER D: DRIFT MONITORING FOUNDATION\n")

# ─── D1-D3: CUSUM / EWMA on Evaluations ─────────────────────────────────
results.append("### D1-D3: CUSUM/EWMA Baseline from 31k Evaluations")
evals_sorted = evals.sort_values("candle_time")
decision = evals_sorted.decision_bin.values

# Rolling CANDIDATE rate
window = 200
if len(decision) > window:
    rolling_cr = pd.Series(decision).rolling(window).mean().dropna().values
    results.append(f"Rolling {window}-eval CANDIDATE rate:")
    results.append(f"  Mean: {rolling_cr.mean():.3f}")
    results.append(f"  Std: {rolling_cr.std():.4f}")
    results.append(f"  Min: {rolling_cr.min():.3f} (date index: ~{evals_sorted.iloc[np.argmin(rolling_cr)+window].candle_time})")
    results.append(f"  Max: {rolling_cr.max():.3f}")

    # CUSUM for shift detection
    p0 = decision.mean()
    cusum_pos = np.zeros(len(decision))
    cusum_neg = np.zeros(len(decision))
    k = 0.02  # sensitivity parameter (detect 2pp shift)
    for i in range(1, len(decision)):
        cusum_pos[i] = max(0, cusum_pos[i-1] + (decision[i] - p0 - k))
        cusum_neg[i] = max(0, cusum_neg[i-1] + (-decision[i] + p0 - k))

    h = 4.0  # alarm threshold
    pos_alarms = np.where(cusum_pos > h)[0]
    neg_alarms = np.where(cusum_neg > h)[0]
    results.append(f"\nCUSUM (p0={p0:.3f}, k=0.02, h=4.0):")
    results.append(f"  Positive shift alarms: {len(pos_alarms)} (CANDIDATE rate increased)")
    results.append(f"  Negative shift alarms: {len(neg_alarms)} (CANDIDATE rate decreased)")
    results.append(f"  Max CUSUM+: {cusum_pos.max():.2f}")
    results.append(f"  Max CUSUM-: {cusum_neg.max():.2f}")

    # EWMA
    lam = 0.2
    ewma = np.zeros(len(decision))
    ewma[0] = p0
    for i in range(1, len(decision)):
        ewma[i] = lam * decision[i] + (1 - lam) * ewma[i-1]

    sigma_ewma = np.sqrt(p0 * (1 - p0) * lam / (2 - lam))
    ucl = p0 + 3 * sigma_ewma
    lcl = p0 - 3 * sigma_ewma
    ewma_violations = ((ewma > ucl) | (ewma < lcl)).sum()
    results.append(f"\nEWMA (lambda=0.2):")
    results.append(f"  Control limits: [{lcl:.4f}, {ucl:.4f}]")
    results.append(f"  Out-of-control points: {ewma_violations}")
results.append("")


# ═══════════════════════════════════════════════════════════════════════════
# SYNTHESIS: KEY FINDINGS FOR PROMPT OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════
results.append("---\n## SYNTHESIS: KEY FINDINGS FOR PROMPT OPTIMIZATION\n")
results.append("*Items below summarize the findings that directly inform how to optimize the prompt.*\n")

# Compile key numbers
findings = []

# From B36
if len(reached_1r) > 0:
    findings.append(f"1. **P(2R|1R)={p_2r_given_1r:.0%}** — {'hold' if p_2r_given_1r >= 0.5 else 'exit'} at 1R is correct")

# From B23
findings.append(f"2. **IS decomposition:** {'Early exit cost' if total_early_exit > total_reversal else 'Reversal cost'} dominates ({max(total_early_exit, total_reversal):.1f}R vs {min(total_early_exit, total_reversal):.1f}R)")

# From C1
findings.append(f"3. **WR decay test:** {'Confirmed (p={:.3f})'.format(p_z) if p_z < 0.05 else 'NOT confirmed (p={:.3f})'.format(p_z)}")

# From A20
findings.append(f"4. **Kelly f*={f_kelly:.3f}** — current 1% is {1/(f_kelly*100):.1f}x Kelly fraction" if f_kelly > 0 else "4. Kelly f* <= 0 (edge doesn't support positive sizing)")

# From C20
findings.append(f"5. **Loss/win asymmetry={ratio:.2f}** — {'losses > wins (unfavorable)' if ratio > 1 else 'wins >= losses (favorable)'}")

for f in findings:
    results.append(f)

results.append("")
results.append("---\n*Generated by L4_foundation_analysis.py*")

# Write output
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(results))
print(f"Results written to {OUT}")
print(f"\nTotal lines: {len(results)}")
