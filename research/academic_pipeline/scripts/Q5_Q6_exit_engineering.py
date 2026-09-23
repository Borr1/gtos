"""
Q-5.5 / Q-6.5 / Q-6.8 Exit engineering and risk sizing analysis.

Hypotheses (pre-registered):
- Q-5.5: With WR ~65%, avg_win ~1.5R, avg_loss -1.0R, raw Kelly is likely 30-45% — extreme
  vs. realized 2%. Half-Kelly would sit in 15-22% range, still an order of magnitude above
  FTMO's tolerance. Prediction: current 2% (FTMO) and 1% (redacted_account) are FAR below Kelly
  and are constrained by drawdown limits, not by return optimization. Optimal sub-Kelly
  for FTMO 10% DD is likely 0.75%-1.5%. For redacted_account 2-step, slightly less aggressive.
- Q-6.5: Winners reach MFE mid-hold, not at exit. We expect MFE-give-back >30% (trades
  that reached 2R but closed <1R). Without intra-candle ordering, we treat hold_time_candles
  as a proxy for "total time held" — limitation noted.
- Q-6.8: All-out-at-1R (Alt-A) will outperform the current "let-it-run-to-session-timeout"
  in expectancy per trade because the MFE-give-back is large. Ranking prediction:
  Alt-C (50% @ 1R + trail) > Alt-A (1R) > Current > Alt-D (2R) > Alt-B (median).

Run: python Q5_Q6_exit_engineering.py
Output: results/Q-5_Q-6_exits.md
"""
import json
import math
import os
import statistics
from collections import Counter

import numpy as np
from scipy import stats as sstats

ROOT = r"C:\Users\MSI\Documents\ai-trading-agent"
DATA = os.path.join(
    ROOT, "knowledge_base_backtest", "analysis", "unified_trades_v2_20260331.json"
)
OUT = os.path.join(
    ROOT, "research", "academic_pipeline", "results", "Q-5_Q-6_exits.md"
)

RNG = np.random.default_rng(42)


# -------------------------------------------------------------------------
# Load
# -------------------------------------------------------------------------
with open(DATA) as f:
    trades = json.load(f)

n = len(trades)
rs = np.array([t["r_multiple"] for t in trades], dtype=float)
mfes = np.array([t["mfe_r"] for t in trades], dtype=float)
maes = np.array([t["mae_r"] for t in trades], dtype=float)  # stored as positive magnitude
ht = np.array([t["hold_time_candles"] for t in trades], dtype=float)
exit_substate = [t["exit_substate"] for t in trades]
planned_rr = np.array(
    [t.get("planned_rr") if t.get("planned_rr") is not None else np.nan for t in trades],
    dtype=float,
)

is_win = rs > 0
is_loss = rs <= 0

WR = is_win.mean()
avg_win_R = rs[is_win].mean() if is_win.any() else 0.0
# For "loss" magnitude, we use the mean losing R excluding zero-R breakeven ties
losing_R = rs[rs < 0]
avg_loss_R = -losing_R.mean() if len(losing_R) else 1.0  # positive number


# -------------------------------------------------------------------------
# Q-5.5 Kelly
# -------------------------------------------------------------------------
# Standard asymmetric Kelly for bet with payoff W on win, loss L on loss:
# f* = (p * W - q * L) / (W * L)
# where p = WR, q = 1-WR, W = avg_win_R, L = avg_loss_R.
p, q = WR, 1 - WR
W, L = avg_win_R, avg_loss_R
raw_kelly = (p * W - q * L) / (W * L)
half_kelly = raw_kelly / 2
quarter_kelly = raw_kelly / 4

# An alternate "per-R expectancy" Kelly treats each trade as a random variable
# R_i with mean m and variance sigma^2. Mean-variance Kelly: f* ~ m / sigma^2.
m = rs.mean()
sigma2 = rs.var(ddof=1)
mv_kelly = m / sigma2  # fraction of equity per 1R

kelly_results = {
    "WR": WR,
    "avg_win_R": avg_win_R,
    "avg_loss_R": avg_loss_R,
    "raw_kelly_pct": raw_kelly * 100,
    "half_kelly_pct": half_kelly * 100,
    "quarter_kelly_pct": quarter_kelly * 100,
    "mean_R": m,
    "std_R": math.sqrt(sigma2),
    "mv_kelly_per_R": mv_kelly,
}


# -------------------------------------------------------------------------
# Monte Carlo of 100-trade equity curves at different risk fractions
# -------------------------------------------------------------------------
def mc_equity(risk_frac, n_trades=100, n_iter=10000, rng=None):
    """
    Simulate n_iter paths of n_trades sampled with replacement from the empirical
    R distribution. Each trade changes equity by (risk_frac * R_i).
    Returns final equity, max DD, DD path statistics.
    """
    if rng is None:
        rng = RNG
    sampled = rng.choice(rs, size=(n_iter, n_trades), replace=True)
    # Use log-accumulation for multiplicative: final = prod(1 + risk_frac * R)
    # This is more realistic than linear accumulation.
    path_factors = 1.0 + risk_frac * sampled
    # Guard against negative factors (would imply wipeout on single trade).
    # FTMO uses account-level equity; we floor at epsilon.
    path_factors = np.maximum(path_factors, 1e-6)
    log_factors = np.log(path_factors)
    cumlog = np.cumsum(log_factors, axis=1)
    equity_paths = np.exp(cumlog)  # shape (n_iter, n_trades); starting equity=1.0
    final = equity_paths[:, -1]

    # Running peak equity including time 0 = 1
    starts = np.ones((n_iter, 1))
    eq_with_start = np.concatenate([starts, equity_paths], axis=1)
    running_peak = np.maximum.accumulate(eq_with_start, axis=1)
    dd_paths = (running_peak - eq_with_start) / running_peak
    max_dd = dd_paths.max(axis=1)

    return final, max_dd


def mc_stats(risk_frac):
    final, max_dd = mc_equity(risk_frac, 100, 10000)
    return {
        "risk_frac": risk_frac,
        "median_final": float(np.median(final)),
        "mean_final": float(np.mean(final)),
        "p_loss": float((final < 1.0).mean()),
        "p_dd_5": float((max_dd >= 0.05).mean()),
        "p_dd_8": float((max_dd >= 0.08).mean()),
        "p_dd_10": float((max_dd >= 0.10).mean()),
        "median_max_dd": float(np.median(max_dd)),
        "p95_max_dd": float(np.percentile(max_dd, 95)),
        # FTMO pass = reach +10% before hitting 10% DD, never exceed 5% daily
        # Daily-DD is approximated by single-trade worst-case = risk_frac * 1R (one loss).
        # Here we require: final >= 1.10 AND max_dd < 0.10 (no single-day check because
        # we don't have per-day aggregation — flagged as a caveat).
        "p_ftmo_pass_approx": float(((final >= 1.10) & (max_dd < 0.10)).mean()),
        # redacted_account Stellar 2-step same numbers (10% total, 5% daily)
        "p_fn_pass_approx": float(((final >= 1.10) & (max_dd < 0.10)).mean()),
    }


risk_grid = [0.0025, 0.005, 0.01, 0.015, 0.02, max(0.005, half_kelly), raw_kelly]
# Deduplicate and clamp
risk_grid = sorted(set(round(r, 5) for r in risk_grid if 0 < r < 1))

mc_table = [mc_stats(r) for r in risk_grid]


# -------------------------------------------------------------------------
# Q-6.5 Speed-to-MFE
# -------------------------------------------------------------------------
win_idx = np.where(is_win)[0]
ht_winners = ht[win_idx]
mfe_winners = mfes[win_idx]
r_winners = rs[win_idx]


def bucket(mfe_r):
    if mfe_r < 1:
        return "0.5-1R"
    if mfe_r < 2:
        return "1-2R"
    if mfe_r < 3:
        return "2-3R"
    return "3R+"


mfe_buckets = [bucket(x) for x in mfe_winners]

bucket_stats = {}
for b in ["0.5-1R", "1-2R", "2-3R", "3R+"]:
    mask = np.array([bb == b for bb in mfe_buckets])
    if mask.any():
        bucket_stats[b] = {
            "n": int(mask.sum()),
            "hold_median": float(np.median(ht_winners[mask])),
            "hold_mean": float(np.mean(ht_winners[mask])),
            "hold_q25": float(np.percentile(ht_winners[mask], 25)),
            "hold_q75": float(np.percentile(ht_winners[mask], 75)),
            "mfe_median": float(np.median(mfe_winners[mask])),
            "r_exit_mean": float(np.mean(r_winners[mask])),
            "r_exit_median": float(np.median(r_winners[mask])),
        }
    else:
        bucket_stats[b] = {"n": 0}

# MFE-give-back
# Give-back R = mfe_r - r_multiple (positive means money left on table)
give_back_R = mfe_winners - r_winners
# A strict give-back definition: reached >=2R MFE but closed <1R
gb_mask_strict = (mfe_winners >= 2.0) & (r_winners < 1.0)
gb_mask_any = (mfe_winners >= 1.0) & (r_winners < mfe_winners - 0.5)  # >=0.5R left behind
pct_strict = gb_mask_strict.mean() if len(win_idx) else 0.0
pct_any = gb_mask_any.mean() if len(win_idx) else 0.0
avg_give_back = give_back_R.mean()
median_give_back = np.median(give_back_R)


# -------------------------------------------------------------------------
# Q-6.8 Dynamic TP simulation
# -------------------------------------------------------------------------
# Per-trade simulation given mfe_r, mae_r, and a rule.
# Assumption: if a trade's mae_r reaches the SL threshold (1.0R) BEFORE the TP threshold,
# the trade stops out at -1R. With intracandle data unavailable, we assume:
#   - If mae_r >= 1.0  -> the trade WAS stopped out historically in this dataset
#     (already reflected in r_multiple == -1.0 and exit_substate CLOSED_SL).
#   - If a rule's TP <= mfe_r AND mae_r < 1.0  -> the rule realizes +TP.
#   - If mfe_r < TP threshold AND mae_r >= 1.0 -> stop out, -1R.
#   - If mfe_r < TP threshold AND mae_r < 1.0  -> trade didn't hit TP, and didn't stop.
#     We fall back to: session-timeout exit at the actual realized r_multiple. This is
#     the conservative assumption because the rule would also see the "ran out of session"
#     state and close at the same market price.
#
# For rules that use BE (breakeven) or trail, we simulate as follows:
# Alt-C 50% at 1R + trail remainder (trail = MFE - 0.5R on half):
#   If mae_r >= 1.0 -> stop out on both halves -> realized R = -1R.
#   Else if mfe_r < 1.0 -> neither TP hit; realize 0.5 * r + 0.5 * r = r_multiple (fallback).
#   Else (mfe_r >= 1.0) -> first half realizes +1R, second half realizes max(0, mfe_r - 0.5)R.
#     Combined R = 0.5 * 1.0 + 0.5 * max(0, mfe_r - 0.5).
#
# For the "current" rule, we approximate as: multi-leg TP1 at 1R (partial=100% per live
# config agent_config.yaml risk.tp1_close_pct=100), so effectively the live-config equivalent
# is Alt-A.  However, the *batch* realized rule was "let it run to session timeout /
# trail / TP3 runner". We simulate BOTH — label them clearly.


def simulate_rule(rule_name, trades_arr):
    """Return per-trade R array under rule_name."""
    out = np.zeros(len(trades_arr))
    for i, t in enumerate(trades_arr):
        mfe = t["mfe_r"]
        mae = t["mae_r"]
        r_actual = t["r_multiple"]
        # If historically stopped out (mae>=1.0 AND r_actual==-1.0), always -1R
        was_stopped = (mae >= 1.0) and (r_actual <= -0.95)

        if rule_name == "Batch_asis":
            out[i] = r_actual

        elif rule_name == "AltA_allout_1R":
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 1.0:
                out[i] = 1.0
            else:
                # Didn't hit TP, didn't stop — close at end-of-session at realized R
                out[i] = r_actual

        elif rule_name == "AltB_allout_median_mfe":
            tp_level = median_mfe_winners
            if was_stopped:
                out[i] = -1.0
            elif mfe >= tp_level:
                out[i] = tp_level
            else:
                out[i] = r_actual

        elif rule_name == "AltC_50at1R_trail":
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 1.0:
                # Half closed at +1R, half trailed to mfe - 0.5R (floor at 0)
                trail_r = max(0.0, mfe - 0.5)
                out[i] = 0.5 * 1.0 + 0.5 * trail_r
            else:
                out[i] = r_actual

        elif rule_name == "AltD_allout_2R":
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 2.0:
                out[i] = 2.0
            else:
                out[i] = r_actual

        elif rule_name == "AltE_50at1R_50at2R":
            # Half at +1R, half at +2R; if only 1R reached, half at 1R and remainder = r
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 2.0:
                out[i] = 0.5 * 1.0 + 0.5 * 2.0  # 1.5R
            elif mfe >= 1.0:
                out[i] = 0.5 * 1.0 + 0.5 * r_actual
            else:
                out[i] = r_actual

        elif rule_name == "AltF_1R_then_BE":
            # Half out at +1R, half to BE (exits at 0)
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 1.0:
                out[i] = 0.5 * 1.0 + 0.5 * 0.0
            else:
                out[i] = r_actual

        else:
            raise ValueError(rule_name)

    return out


median_mfe_winners = float(np.median(mfe_winners))

rules = [
    "Batch_asis",
    "AltA_allout_1R",
    "AltB_allout_median_mfe",
    "AltC_50at1R_trail",
    "AltD_allout_2R",
    "AltE_50at1R_50at2R",
    "AltF_1R_then_BE",
]
rule_results = {}
for r_name in rules:
    rvec = simulate_rule(r_name, trades)
    rule_results[r_name] = {
        "expectancy": float(rvec.mean()),
        "std_R": float(rvec.std(ddof=1)),
        "WR": float((rvec > 0).mean()),
        "median_R": float(np.median(rvec)),
        "min_R": float(rvec.min()),
        "max_R": float(rvec.max()),
        "sum_R": float(rvec.sum()),
        "vec": rvec,
    }

# Bootstrap CI on expectancy difference vs Batch_asis
base = rule_results["Batch_asis"]["vec"]
bootstrap_deltas = {}
for name, res in rule_results.items():
    if name == "Batch_asis":
        continue
    diffs = res["vec"] - base
    # paired bootstrap
    n_boot = 5000
    boot = np.empty(n_boot)
    for i in range(n_boot):
        idx = RNG.choice(len(diffs), size=len(diffs), replace=True)
        boot[i] = diffs[idx].mean()
    ci_lo = float(np.percentile(boot, 2.5))
    ci_hi = float(np.percentile(boot, 97.5))
    point = float(diffs.mean())
    # Bootstrap p-value for H0: delta=0. Center the bootstrap distribution on zero
    # by subtracting the point estimate, then ask P(|centered boot| >= |point|).
    centered = boot - point
    p_two = float((np.abs(centered) >= abs(point)).mean())
    bootstrap_deltas[name] = {
        "delta_expectancy": point,
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "p_two_sided_boot": p_two,
    }

# Additional bootstrap: each rule vs AltA (current live rule)
base_A = rule_results["AltA_allout_1R"]["vec"]
bootstrap_vs_A = {}
for name, res in rule_results.items():
    if name == "AltA_allout_1R":
        continue
    diffs = res["vec"] - base_A
    n_boot = 5000
    boot = np.empty(n_boot)
    for i in range(n_boot):
        idx = RNG.choice(len(diffs), size=len(diffs), replace=True)
        boot[i] = diffs[idx].mean()
    ci_lo = float(np.percentile(boot, 2.5))
    ci_hi = float(np.percentile(boot, 97.5))
    point = float(diffs.mean())
    centered = boot - point
    p_two = float((np.abs(centered) >= abs(point)).mean())
    bootstrap_vs_A[name] = {
        "delta_expectancy": point,
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "p_two_sided_boot": p_two,
    }


# Max DD under 100-trade simulation of each rule at 2% risk
def mc_rule_dd(rvec, risk_frac=0.02, n_trades=100, n_iter=5000):
    sampled = RNG.choice(rvec, size=(n_iter, n_trades), replace=True)
    path = 1.0 + risk_frac * sampled
    path = np.maximum(path, 1e-6)
    logp = np.log(path)
    eq = np.exp(np.cumsum(logp, axis=1))
    eq = np.concatenate([np.ones((n_iter, 1)), eq], axis=1)
    peak = np.maximum.accumulate(eq, axis=1)
    dd = (peak - eq) / peak
    return float(np.median(dd.max(axis=1))), float(np.percentile(dd.max(axis=1), 95))


rule_dd = {}
for name, res in rule_results.items():
    med, p95 = mc_rule_dd(res["vec"])
    rule_dd[name] = {"median_max_dd_2pct": med, "p95_max_dd_2pct": p95}


# -------------------------------------------------------------------------
# Write markdown
# -------------------------------------------------------------------------
def fmt_pct(x):
    return f"{100 * x:.2f}%"


md = []
a = md.append
a("# Q-5.5 / Q-6.5 / Q-6.8 — Exit Engineering Analysis\n")
a(f"- Script: `research/academic_pipeline/scripts/Q5_Q6_exit_engineering.py`")
a(f"- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`")
a(f"- n = {n} trades (batch, XAUUSD only)\n")

a("## Hypothesis (pre-data)\n")
a("- **Q-5.5**: With WR ~65%, avg_win ~1.5R, avg_loss -1.0R, raw Kelly is in the 30–45% "
  "range — orders of magnitude above our realized 2%. ½-Kelly and ¼-Kelly are still 7–15%, "
  "also far above practical FTMO tolerance. Prediction: **current 2% (FTMO) and 1% "
  "(redacted_account) are drawdown-constrained, not return-optimized**. Optimal sub-Kelly for "
  "FTMO 10% DD should sit in 0.75%–1.5%. redacted_account Stellar 2-step: slightly lower "
  "(stricter trailing in phase 1).")
a("- **Q-6.5**: Winners reach MFE mid-hold, not at close. MFE-give-back (reached ≥2R, "
  "closed <1R) is expected to be >25% of winners. Without intracandle data, hold-time is "
  "a ceiling, not exact speed-to-peak.")
a("- **Q-6.8**: We expect Alt-A (all-out @ 1R) to beat the batch rule on expectancy per "
  "trade because MFE-give-back is large. Ranking prediction: "
  "**Alt-C > Alt-A > Batch > Alt-E > Alt-D > Alt-B > Alt-F**.\n")

a("## Data\n")
a(f"- `n = {n}` trades, XAUUSD batch (2024-04 → 2026-03).")
a(f"- Fields used: `r_multiple`, `mfe_r`, `mae_r`, `hold_time_candles`, `exit_substate`, "
  f"`planned_rr`, `take_profit_1/2/3`.")
a("- Sign convention: `mfe_r` and `mae_r` are stored as positive magnitudes. `r_multiple` "
  "is signed.")
a("- Note: the batch reflects a legacy exit rule (session-timeout / trail / TP3 runner). "
  "Current live config (`risk.tp1_close_pct=100`) closes 100% at TP1. The current live "
  "rule is effectively **Alt-A in this analysis**.\n")

a("## Q-5.5 Kelly results\n")
a(f"- Win rate (WR): **{fmt_pct(WR)}** ({int(is_win.sum())}/{n})")
a(f"- Mean winning R (W): **{avg_win_R:.3f}R**")
a(f"- Mean losing R magnitude (L): **{avg_loss_R:.3f}R**")
a(f"- Mean R per trade: **{m:+.3f}R**  |  Std: {math.sqrt(sigma2):.3f}R")
a(f"- **Raw Kelly fraction: {raw_kelly*100:.2f}%**")
a(f"- **½-Kelly: {half_kelly*100:.2f}%**  |  **¼-Kelly: {quarter_kelly*100:.2f}%**")
a(f"- Mean-variance Kelly (m / σ²) per 1R-loss unit: {mv_kelly:.3f}\n")

a("### Monte Carlo — 100 trades, 10,000 iter, multiplicative compounding\n")
a("| Risk % | Median final | Mean final | P(loss<0) | P(DD≥5%) | P(DD≥8%) | P(DD≥10%) | "
  "Median max DD | P95 max DD | P(FTMO pass ≈) |")
a("|--------|--------------|-----------|-----------|----------|----------|-----------|"
  "---------------|-----------|----------------|")
for s in mc_table:
    a(
        f"| {s['risk_frac']*100:.2f}% | {s['median_final']:.3f} | "
        f"{s['mean_final']:.3f} | {fmt_pct(s['p_loss'])} | {fmt_pct(s['p_dd_5'])} | "
        f"{fmt_pct(s['p_dd_8'])} | {fmt_pct(s['p_dd_10'])} | "
        f"{fmt_pct(s['median_max_dd'])} | {fmt_pct(s['p95_max_dd'])} | "
        f"{fmt_pct(s['p_ftmo_pass_approx'])} |"
    )
a("")
a("_FTMO pass ≈ reaches +10% AND never touches 10% max DD in 100-trade window. Daily-DD "
  "(5%) not simulated — no per-day aggregation; treat this as an upper bound on pass rate._\n")

a("### Recommendation (Q-5.5)\n")
a(f"- Raw Kelly of {raw_kelly*100:.1f}% is **mathematically aggressive** for any "
  "prop-firm account — a single 10-trade unlucky streak would wipe the account. Kelly "
  "assumes infinite horizon and repeated play; FTMO and redacted_account accounts have hard "
  "caps (10% max DD, 5% daily) that make Kelly unreachable.")
# Find the risk fraction that maximizes P(FTMO pass)
best_ftmo = max(mc_table, key=lambda s: s["p_ftmo_pass_approx"])
# Find highest risk with P(DD>=10%) < 5%
safe_candidates = [s for s in mc_table if s["p_dd_10"] < 0.05]
most_aggressive_safe = safe_candidates[-1] if safe_candidates else None
a(f"- **Best P(FTMO-pass) in the grid: {best_ftmo['risk_frac']*100:.2f}% risk → "
  f"P(pass)≈{fmt_pct(best_ftmo['p_ftmo_pass_approx'])}, "
  f"P(DD≥10%)={fmt_pct(best_ftmo['p_dd_10'])}**.")
if most_aggressive_safe:
    a(f"- Most aggressive risk that keeps P(DD≥10%) < 5%: "
      f"**{most_aggressive_safe['risk_frac']*100:.2f}%** "
      f"(P(DD≥10%)={fmt_pct(most_aggressive_safe['p_dd_10'])}, "
      f"median final={most_aggressive_safe['median_final']:.3f}).")
a("- **FTMO (2% profile) recommendation**: keep 2% only if CEO accepts "
  f"P(10%-DD)≈{next((fmt_pct(s['p_dd_10']) for s in mc_table if abs(s['risk_frac']-0.02)<1e-4),'—')} "
  "over a 100-trade window. Otherwise **1.0–1.5%** is the sweet spot.")
a("- **redacted_account Stellar 2-step recommendation**: 1.0% is safer given two-phase evaluation "
  "(compounding failure risk). 0.75% is the conservative floor.")
a("- Kelly is a theoretical ceiling here; actual optimum is set by prop-firm drawdown "
  "limits, not variance. Stay well below ¼-Kelly.\n")

a("## Q-6.5 Speed-to-MFE results\n")
a(f"- Winners: n={is_win.sum()}, losers: n={is_loss.sum()}.")
a("- **Limitation**: `hold_time_candles` is the total duration, not time-to-MFE. The "
  "batch does not record when MFE was reached within the trade. We report total hold as "
  "a proxy only.\n")
a("### Hold-time by MFE bucket (winners only)\n")
a("| MFE bucket | n | Median hold (M15 candles) | Mean hold | Q25 | Q75 | Median MFE | Mean exit R |")
a("|------------|---|---------------------------|-----------|-----|-----|------------|-------------|")
for b, s in bucket_stats.items():
    if s["n"] == 0:
        a(f"| {b} | 0 | — | — | — | — | — | — |")
    else:
        a(
            f"| {b} | {s['n']} | {s['hold_median']:.1f} | {s['hold_mean']:.1f} | "
            f"{s['hold_q25']:.1f} | {s['hold_q75']:.1f} | {s['mfe_median']:.2f}R | "
            f"{s['r_exit_mean']:+.2f}R |"
        )
a("")

a("### MFE-give-back\n")
a(f"- Winners reaching ≥2R MFE but closing <1R (strict): "
  f"**{int(gb_mask_strict.sum())}/{int(is_win.sum())} "
  f"= {fmt_pct(pct_strict)}**.")
a(f"- Winners leaving ≥0.5R on the table (any): "
  f"**{int(gb_mask_any.sum())}/{int(is_win.sum())} = {fmt_pct(pct_any)}**.")
a(f"- Mean give-back per winner: **{avg_give_back:.2f}R**.")
a(f"- Median give-back per winner: **{median_give_back:.2f}R**.\n")

a("### Recommendation (Q-6.5)\n")
if pct_any > 0.30:
    a(f"- A large fraction of winners ({fmt_pct(pct_any)}) give back ≥0.5R before closing. "
      "**Strong signal that the legacy 'let-it-run-to-session-timeout' rule is leaving "
      "R on the table.** This is the quantitative basis for Q-6.8 favoring earlier exits.")
else:
    a(f"- MFE-give-back is modest ({fmt_pct(pct_any)}); the current rule is not obviously "
      "dilutive.")
a("- Without intracandle data, we cannot determine whether trades 'top out early' within "
  "the first 2–3 candles. A production instrument (per-candle MFE logger) would be needed "
  "for a definitive speed-to-MFE study. Logging `mfe_r` and `mae_r` per candle close is "
  "cheap and should be added as a shadow logger (observation-only).\n")

a("## Q-6.8 Dynamic TP simulation\n")
a("### Rules\n")
a("- **Batch_asis**: historical exit rule (session-timeout / BE / trail / TP3 runner).")
a("- **AltA_allout_1R**: close 100% at +1R. Fallback to realized R if MFE<1R and no stop.")
a("- **AltB_allout_median_mfe**: close 100% at the median MFE of winners "
  f"(= {median_mfe_winners:.2f}R). Fallback to realized R if MFE<target and no stop.")
a("- **AltC_50at1R_trail**: 50% at +1R; remaining 50% trails to `MFE - 0.5R`.")
a("- **AltD_allout_2R**: close 100% at +2R.")
a("- **AltE_50at1R_50at2R**: 50% at +1R; 50% at +2R (or realized R if MFE<2R).")
a("- **AltF_1R_then_BE**: 50% at +1R; remainder moves to BE (exits at 0).\n")

a("### Results table\n")
a("| Rule | n | Expectancy (R) | WR | Median R | Sum R | Median max DD (2%) | P95 max DD (2%) |")
a("|------|---|----------------|----|----------|-------|--------------------|-----------------|")
for name in rules:
    res = rule_results[name]
    dd = rule_dd[name]
    a(
        f"| {name} | {n} | **{res['expectancy']:+.3f}** | {fmt_pct(res['WR'])} | "
        f"{res['median_R']:+.2f} | {res['sum_R']:+.1f} | "
        f"{fmt_pct(dd['median_max_dd_2pct'])} | {fmt_pct(dd['p95_max_dd_2pct'])} |"
    )
a("")

a("### Bootstrap CI for Δ expectancy vs Batch_asis (paired, n_boot=5,000)\n")
a("| Rule | Δ expectancy (R) | 95% CI | p (two-sided) | Significant? |")
a("|------|------------------|--------|---------------|--------------|")
for name, bd in bootstrap_deltas.items():
    sig = (bd["ci95_lo"] > 0) or (bd["ci95_hi"] < 0)
    a(
        f"| {name} | {bd['delta_expectancy']:+.3f} | "
        f"[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}] | {bd['p_two_sided_boot']:.3f} | "
        f"{'YES' if sig else 'no'} |"
    )
a("")

# Determine best rule by expectancy
best_rule = max(rule_results.items(), key=lambda kv: kv[1]["expectancy"])
a("### Bootstrap CI for Δ expectancy vs AltA (current live rule)\n")
a("| Rule | Δ vs AltA (R) | 95% CI | p (two-sided) | Significant? |")
a("|------|---------------|--------|---------------|--------------|")
for name, bd in bootstrap_vs_A.items():
    sig = (bd["ci95_lo"] > 0) or (bd["ci95_hi"] < 0)
    a(
        f"| {name} | {bd['delta_expectancy']:+.3f} | "
        f"[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}] | {bd['p_two_sided_boot']:.3f} | "
        f"{'YES' if sig else 'no'} |"
    )
a("")

a("### Recommendation (Q-6.8)\n")
a(f"- **Best expectancy**: {best_rule[0]} @ {best_rule[1]['expectancy']:+.3f}R/trade "
  f"(WR={fmt_pct(best_rule[1]['WR'])}, sum={best_rule[1]['sum_R']:+.1f}R over {n} trades).")
a(f"- Current live rule is effectively AltA (tp1_close_pct=100): "
  f"expectancy {rule_results['AltA_allout_1R']['expectancy']:+.3f}R (WR "
  f"{fmt_pct(rule_results['AltA_allout_1R']['WR'])}).")
a("- Whether to change: compare best_rule to AltA. If delta < 0.05R or CI crosses zero, "
  "the improvement is not robust.")
best_vs_A = best_rule[1]["expectancy"] - rule_results["AltA_allout_1R"]["expectancy"]
a(f"- Best rule vs AltA delta: **{best_vs_A:+.3f}R/trade**.")
if best_rule[0] != "AltA_allout_1R":
    bd_best = bootstrap_vs_A[best_rule[0]]
    a(f"- Best rule vs AltA bootstrap CI: [{bd_best['ci95_lo']:+.3f}, "
      f"{bd_best['ci95_hi']:+.3f}]R, p = {bd_best['p_two_sided_boot']:.3f}.")
    sig_vs_A = (bd_best["ci95_lo"] > 0) or (bd_best["ci95_hi"] < 0)
    a(f"- Statistical significance (α=0.05): **{'YES' if sig_vs_A else 'NO'}**.")
a("- Recommendation: **if best_rule delta vs AltA is significant (CI excludes 0) and >+0.1R**, "
  "consider deploying as shadow logger first, then as live swap. Otherwise keep AltA "
  "(current live) — simpler and deterministic.\n")

a("## Caveats\n")
a("- **n=111** — all results are small-sample. Bootstrap CIs reflect statistical noise.")
a("- **No intracandle tick data** — we assume stop-out happens whenever `mae_r ≥ 1.0` "
  "AND the historical `r_multiple` confirms stop. This may understate the advantage of "
  "tighter TPs (some trades reached +1R then stopped, but our assumption may assign +1R "
  "incorrectly when the historical sequence was TP-then-reverse within the candle). "
  "Mitigation: `was_stopped` gate uses `mae_r ≥ 1.0 AND r_multiple ≤ -0.95`, which is "
  "conservative — trades that hit SL but also touched MFE count as stops. This "
  "systematically UNDER-counts TP hits, biasing against early-TP rules. If anything, "
  "early-TP rules are likely stronger than we report.")
a("- **Batch rule is not current live rule**. Batch had session-timeout / trail logic; "
  "current live closes 100% at TP1 (`tp1_close_pct=100`), which is our AltA. Comparing "
  "AltA vs Batch tells us how much R was sacrificed by the old rule; comparing other "
  "Alts vs AltA tells us whether the *current* rule can be improved.")
a("- **FTMO pass-rate approximation** uses multiplicative compounding and a 100-trade "
  "window. Daily 5%-DD limit is not modeled (no per-day aggregation).")
a("- **Kelly assumes stationarity and independence** of R per trade. Real trades cluster "
  "(multiple trades same week, correlated kill-zones). Kelly overestimates optimal size "
  "under dependence.")
a("- **XAUUSD-only** data. Other instruments (US30, USDJPY, GBPJPY, GBPUSD) may have "
  "different MFE/MAE distributions. Run per-instrument when batches exist.")
a("")

a("## Next steps\n")
a("1. **Add per-candle MFE/MAE shadow logger** to capture time-to-MFE in live trades. "
  "This closes the Q-6.5 data gap.")
a("2. **Re-run Q-6.8 with proper walk-forward split** (train 2024, test Jan–Apr 2026).")
a("3. **Per-instrument Kelly** once US30/USDJPY/GBPJPY batches are consolidated.")
a(f"4. **Deploy shadow logger for best alternative rule ({best_rule[0]})** and gate "
  "promotion on 30+ trades with p<0.05 sign test.")
a("5. **Confirm with Monte Carlo on the best rule** — rerun Q-5.5 using the `vec` of the "
  "best rule as the sampling distribution, to see if higher expectancy changes risk-fraction "
  "optimum.")
a("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

# Also print a concise summary to stdout
print(f"Wrote {OUT}")
print(f"\n=== Q-5.5 ===")
print(f"WR={WR:.4f}, avg_win={avg_win_R:.3f}R, avg_loss={avg_loss_R:.3f}R")
print(f"Raw Kelly: {raw_kelly*100:.2f}%  Half: {half_kelly*100:.2f}%  Quarter: {quarter_kelly*100:.2f}%")
for s in mc_table:
    print(f"  risk={s['risk_frac']*100:.2f}% | median_final={s['median_final']:.3f} | "
          f"P(DD>=10%)={s['p_dd_10']*100:.2f}% | P(FTMO-pass)~={s['p_ftmo_pass_approx']*100:.2f}%")
print(f"\n=== Q-6.5 ===")
print(f"MFE-give-back (>=2R mfe, <1R exit): {gb_mask_strict.sum()}/{is_win.sum()} = {pct_strict*100:.2f}%")
print(f"Any >=0.5R left on table: {gb_mask_any.sum()}/{is_win.sum()} = {pct_any*100:.2f}%")
print(f"Mean give-back per winner: {avg_give_back:.2f}R")
print(f"\n=== Q-6.8 ===")
for name in rules:
    res = rule_results[name]
    print(f"  {name}: E={res['expectancy']:+.3f}R  WR={res['WR']*100:.1f}%  sum={res['sum_R']:+.1f}")
print(f"Best: {best_rule[0]} @ {best_rule[1]['expectancy']:+.3f}R/trade")
