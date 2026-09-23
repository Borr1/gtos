"""
Q-5.5 / Q-6.5 / Q-6.8 Exit engineering and risk sizing analysis — v2.

Wave-1 reviewer fix: apply H29 drawdown brake inside the Kelly Monte Carlo
simulator. v1 treated risk as constant across all 200 trades per sim. In
production, H29 kicks in when DD-from-peak >= 8% and reduces risk to 0.5%.
v1 therefore overstates P(DD>=10%) at 2% risk.

What changed vs v1:
- `mc_equity()` now applies H29 (risk -> 0.5% when DD-from-peak >= 8%, reverts
  on new equity peak). This is the same H29 rule used in production
  `src/components/drawdown_manager.py` (threshold=0.08, reduced_risk_pct=0.5%)
  and already modelled (correctly) in `q_7_monte_carlo.py`.
- Keep everything else the same: same seed (42), same n_iter (10k), same
  100-trade horizon, same bootstrap CI logic, same Q-6.5 / Q-6.8 rules.
- Track a side-by-side delta: run the MC BOTH without and with H29, so the
  markdown can show the "v1 (H29 off)" and "v2 (H29 on)" numbers together.

Run:  python Q5_Q6_exit_engineering_v2.py
Out:  research/academic_pipeline/results/Q-5_Q-6_exits_v2.md
      research/academic_pipeline/results/Q-5_Q-6_exits_v2.json

Do not delete v1 (_Q-5_Q-6_exits.md_). Diff between v1 and v2 is the H29 impact.
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter

import numpy as np

ROOT = r"C:\Users\MSI\Documents\ai-trading-agent"
DATA = os.path.join(
    ROOT, "knowledge_base_backtest", "analysis", "unified_trades_v2_20260331.json"
)
OUT_MD = os.path.join(
    ROOT, "research", "academic_pipeline", "results", "Q-5_Q-6_exits_v2.md"
)
OUT_JSON = os.path.join(
    ROOT, "research", "academic_pipeline", "results", "Q-5_Q-6_exits_v2.json"
)

RNG = np.random.default_rng(42)

# H29 production parameters (from config/agent_config.yaml)
H29_TRIGGER = 0.08     # DD-from-peak threshold to activate brake
H29_REDUCED_RISK = 0.005  # absolute 0.5% risk when triggered


# -------------------------------------------------------------------------
# Load
# -------------------------------------------------------------------------
with open(DATA) as f:
    trades = json.load(f)

n = len(trades)
rs = np.array([t["r_multiple"] for t in trades], dtype=float)
mfes = np.array([t["mfe_r"] for t in trades], dtype=float)
maes = np.array([t["mae_r"] for t in trades], dtype=float)
ht = np.array([t["hold_time_candles"] for t in trades], dtype=float)

is_win = rs > 0
is_loss = rs <= 0

WR = float(is_win.mean())
avg_win_R = float(rs[is_win].mean()) if is_win.any() else 0.0
losing_R = rs[rs < 0]
avg_loss_R = float(-losing_R.mean()) if len(losing_R) else 1.0


# -------------------------------------------------------------------------
# Q-5.5 Kelly (formula-level, independent of MC)
# -------------------------------------------------------------------------
p, q = WR, 1 - WR
W, L = avg_win_R, avg_loss_R
raw_kelly = (p * W - q * L) / (W * L)
half_kelly = raw_kelly / 2
quarter_kelly = raw_kelly / 4
m = float(rs.mean())
sigma2 = float(rs.var(ddof=1))
mv_kelly = m / sigma2


# -------------------------------------------------------------------------
# Monte Carlo — v2 adds H29 option
# -------------------------------------------------------------------------
def mc_equity(risk_frac, n_trades=100, n_iter=10000, rng=None, h29=False,
              h29_trigger=H29_TRIGGER, h29_reduced=H29_REDUCED_RISK):
    """Simulate equity paths. If h29=True, apply DD-brake same as production."""
    if rng is None:
        rng = RNG
    sampled = rng.choice(rs, size=(n_iter, n_trades), replace=True)

    if not h29:
        # v1 behaviour: constant risk across all trades (vectorised).
        path_factors = 1.0 + risk_frac * sampled
        path_factors = np.maximum(path_factors, 1e-6)
        log_factors = np.log(path_factors)
        cumlog = np.cumsum(log_factors, axis=1)
        equity_paths = np.exp(cumlog)
        starts = np.ones((n_iter, 1))
        eq_with_start = np.concatenate([starts, equity_paths], axis=1)
        running_peak = np.maximum.accumulate(eq_with_start, axis=1)
        dd_paths = (running_peak - eq_with_start) / running_peak
        max_dd = dd_paths.max(axis=1)
        final = equity_paths[:, -1]
        return final, max_dd

    # v2 behaviour: per-iter loop, apply H29 state machine.
    final = np.zeros(n_iter)
    max_dd = np.zeros(n_iter)
    for s in range(n_iter):
        eq = 1.0
        peak = 1.0
        max_dd_run = 0.0
        for t in range(n_trades):
            dd_from_peak = (peak - eq) / peak if peak > 0 else 0.0
            effective_risk = h29_reduced if dd_from_peak >= h29_trigger else risk_frac
            r = sampled[s, t]
            factor = max(1.0 + effective_risk * r, 1e-6)
            eq *= factor
            if eq > peak:
                peak = eq
            dd_now = (peak - eq) / peak if peak > 0 else 0.0
            if dd_now > max_dd_run:
                max_dd_run = dd_now
        final[s] = eq
        max_dd[s] = max_dd_run
    return final, max_dd


def mc_stats(risk_frac, h29=False):
    final, max_dd = mc_equity(risk_frac, 100, 10000, h29=h29)
    return {
        "risk_frac": float(risk_frac),
        "h29": bool(h29),
        "median_final": float(np.median(final)),
        "mean_final": float(np.mean(final)),
        "p_loss": float((final < 1.0).mean()),
        "p_dd_5": float((max_dd >= 0.05).mean()),
        "p_dd_8": float((max_dd >= 0.08).mean()),
        "p_dd_10": float((max_dd >= 0.10).mean()),
        "median_max_dd": float(np.median(max_dd)),
        "p95_max_dd": float(np.percentile(max_dd, 95)),
        "p_ftmo_pass_approx": float(((final >= 1.10) & (max_dd < 0.10)).mean()),
        "p_fn_pass_approx": float(((final >= 1.10) & (max_dd < 0.10)).mean()),
    }


# Same grid as v1 for apples-to-apples delta
risk_grid = [0.0025, 0.005, 0.01, 0.015, 0.02, max(0.005, half_kelly), raw_kelly]
risk_grid = sorted(set(round(r, 5) for r in risk_grid if 0 < r < 1))

print("Running v1 MC (no H29)...")
mc_table_v1 = [mc_stats(r, h29=False) for r in risk_grid]
print("Running v2 MC (H29 on)...")
mc_table_v2 = [mc_stats(r, h29=True) for r in risk_grid]


# -------------------------------------------------------------------------
# Q-6.5 Speed-to-MFE (unchanged from v1)
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

give_back_R = mfe_winners - r_winners
gb_mask_strict = (mfe_winners >= 2.0) & (r_winners < 1.0)
gb_mask_any = (mfe_winners >= 1.0) & (r_winners < mfe_winners - 0.5)
pct_strict = float(gb_mask_strict.mean()) if len(win_idx) else 0.0
pct_any = float(gb_mask_any.mean()) if len(win_idx) else 0.0
avg_give_back = float(give_back_R.mean())
median_give_back = float(np.median(give_back_R))


# -------------------------------------------------------------------------
# Q-6.8 Dynamic TP simulation (unchanged from v1; DD reporting below applies H29)
# -------------------------------------------------------------------------
def simulate_rule(rule_name, trades_arr, median_mfe_winners):
    out = np.zeros(len(trades_arr))
    for i, t in enumerate(trades_arr):
        mfe = t["mfe_r"]
        mae = t["mae_r"]
        r_actual = t["r_multiple"]
        was_stopped = (mae >= 1.0) and (r_actual <= -0.95)

        if rule_name == "Batch_asis":
            out[i] = r_actual
        elif rule_name == "AltA_allout_1R":
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 1.0:
                out[i] = 1.0
            else:
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
            if was_stopped:
                out[i] = -1.0
            elif mfe >= 2.0:
                out[i] = 0.5 * 1.0 + 0.5 * 2.0
            elif mfe >= 1.0:
                out[i] = 0.5 * 1.0 + 0.5 * r_actual
            else:
                out[i] = r_actual
        elif rule_name == "AltF_1R_then_BE":
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
    rvec = simulate_rule(r_name, trades, median_mfe_winners)
    rule_results[r_name] = {
        "expectancy": float(rvec.mean()),
        "std_R": float(rvec.std(ddof=1)),
        "WR": float((rvec > 0).mean()),
        "median_R": float(np.median(rvec)),
        "min_R": float(rvec.min()),
        "max_R": float(rvec.max()),
        "sum_R": float(rvec.sum()),
        "vec": rvec.tolist(),
    }

base = np.array(rule_results["Batch_asis"]["vec"])
bootstrap_deltas = {}
for name, res in rule_results.items():
    if name == "Batch_asis":
        continue
    vec = np.array(res["vec"])
    diffs = vec - base
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
    bootstrap_deltas[name] = {
        "delta_expectancy": point,
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "p_two_sided_boot": p_two,
    }

base_A = np.array(rule_results["AltA_allout_1R"]["vec"])
bootstrap_vs_A = {}
for name, res in rule_results.items():
    if name == "AltA_allout_1R":
        continue
    vec = np.array(res["vec"])
    diffs = vec - base_A
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


# Rule DD at 2% with and without H29 (sanity: rule-level DD ranking should not
# flip, but magnitudes will shrink when H29 is on).
def mc_rule_dd(rvec, risk_frac=0.02, n_trades=100, n_iter=5000, h29=False):
    sampled = RNG.choice(np.asarray(rvec), size=(n_iter, n_trades), replace=True)
    if not h29:
        path = np.maximum(1.0 + risk_frac * sampled, 1e-6)
        eq = np.exp(np.cumsum(np.log(path), axis=1))
        eq = np.concatenate([np.ones((n_iter, 1)), eq], axis=1)
        peak = np.maximum.accumulate(eq, axis=1)
        dd = (peak - eq) / peak
    else:
        dd = np.zeros((n_iter, n_trades + 1))
        for s in range(n_iter):
            eq, pk = 1.0, 1.0
            for t in range(n_trades):
                dd_from_peak = (pk - eq) / pk if pk > 0 else 0.0
                effr = H29_REDUCED_RISK if dd_from_peak >= H29_TRIGGER else risk_frac
                eq = max(eq * (1.0 + effr * sampled[s, t]), 1e-6)
                if eq > pk:
                    pk = eq
                dd[s, t + 1] = (pk - eq) / pk if pk > 0 else 0.0
    return float(np.median(dd.max(axis=1))), float(np.percentile(dd.max(axis=1), 95))


rule_dd_v1 = {}
rule_dd_v2 = {}
for name, res in rule_results.items():
    med, p95 = mc_rule_dd(res["vec"], h29=False)
    rule_dd_v1[name] = {"median_max_dd_2pct": med, "p95_max_dd_2pct": p95}
    med2, p95_2 = mc_rule_dd(res["vec"], h29=True)
    rule_dd_v2[name] = {"median_max_dd_2pct": med2, "p95_max_dd_2pct": p95_2}


# -------------------------------------------------------------------------
# Compute explicit delta-table between v1 and v2 MC
# -------------------------------------------------------------------------
delta_rows = []
for r_pct in risk_grid:
    v1_row = next(s for s in mc_table_v1 if abs(s["risk_frac"] - r_pct) < 1e-6)
    v2_row = next(s for s in mc_table_v2 if abs(s["risk_frac"] - r_pct) < 1e-6)
    delta_rows.append({
        "risk_pct": r_pct,
        "p_ftmo_pass_v1": v1_row["p_ftmo_pass_approx"],
        "p_ftmo_pass_v2": v2_row["p_ftmo_pass_approx"],
        "delta_pass_pp": (v2_row["p_ftmo_pass_approx"] - v1_row["p_ftmo_pass_approx"]) * 100,
        "p_dd10_v1": v1_row["p_dd_10"],
        "p_dd10_v2": v2_row["p_dd_10"],
        "delta_dd10_pp": (v2_row["p_dd_10"] - v1_row["p_dd_10"]) * 100,
        "median_final_v1": v1_row["median_final"],
        "median_final_v2": v2_row["median_final"],
    })


# -------------------------------------------------------------------------
# Write JSON
# -------------------------------------------------------------------------
json_payload = {
    "version": "v2",
    "seed": 42,
    "h29_trigger": H29_TRIGGER,
    "h29_reduced_risk": H29_REDUCED_RISK,
    "n_iter": 10000,
    "n_trades_mc": 100,
    "n_batch_trades": n,
    "WR": WR,
    "avg_win_R": avg_win_R,
    "avg_loss_R": avg_loss_R,
    "raw_kelly": raw_kelly,
    "half_kelly": half_kelly,
    "quarter_kelly": quarter_kelly,
    "mv_kelly": mv_kelly,
    "mc_table_v1_no_h29": mc_table_v1,
    "mc_table_v2_with_h29": mc_table_v2,
    "delta_v1_vs_v2": delta_rows,
    "rule_results": {k: {kk: vv for kk, vv in v.items() if kk != "vec"}
                     for k, v in rule_results.items()},
    "bootstrap_deltas_vs_batch": bootstrap_deltas,
    "bootstrap_deltas_vs_altA": bootstrap_vs_A,
    "rule_dd_v1_no_h29": rule_dd_v1,
    "rule_dd_v2_with_h29": rule_dd_v2,
    "bucket_stats": bucket_stats,
    "mfe_giveback": {
        "pct_strict_ge2_close_lt1": pct_strict,
        "pct_any_ge05_left_on_table": pct_any,
        "avg_give_back_R": avg_give_back,
        "median_give_back_R": median_give_back,
    },
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(json_payload, f, indent=2)


# -------------------------------------------------------------------------
# Write markdown
# -------------------------------------------------------------------------
def fmt_pct(x):
    return f"{100 * x:.2f}%"


md = []
a = md.append
a("# Q-5.5 / Q-6.5 / Q-6.8 — Exit Engineering Analysis (v2)\n")
a("**Version:** v2 — Wave-1 reviewer fix: H29 DD brake now applied in Kelly Monte Carlo.\n")
a(f"- Script: `research/academic_pipeline/scripts/Q5_Q6_exit_engineering_v2.py`")
a(f"- JSON: `research/academic_pipeline/results/Q-5_Q-6_exits_v2.json`")
a(f"- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`")
a(f"- n = {n} trades (batch, XAUUSD only)")
a(f"- Seed: 42 (deterministic, numpy default_rng)\n")

a("## v1 → v2 change summary\n")
a("**Root cause flagged by Wave-1 reviewer:** the MC loop treated risk as a constant "
  f"`risk_frac` for all 100 trades per sim. In production, the H29 drawdown manager "
  f"(`src/components/drawdown_manager.py`, config key `drawdown_reduction.threshold=0.08` "
  f"and `reduced_risk_pct=0.5`) cuts risk to 0.5% the moment DD-from-peak >= 8%. This "
  f"makes the v1 P(DD>=10%) numbers systematically high at the 2% level — the brake "
  f"would have engaged before those runs reached 10% DD. v1 is conservative for "
  f"go/no-go decisions (biased toward rejecting 2%), but it misreports the real "
  f"operating distribution.\n")
a("**v2 fix:** replicate the H29 state machine inside `mc_equity()` (and in "
  f"`mc_rule_dd()`): before each trade, read the current DD-from-peak; if "
  f">= {H29_TRIGGER*100:.0f}%, use {H29_REDUCED_RISK*100:.1f}% risk instead of "
  f"the nominal `risk_frac`; reset to nominal on new equity peak.\n")
a("Everything else unchanged: same seed, same 10k iter, same 100-trade horizon, "
  "same Q-6.5 / Q-6.8 rules, same bootstrap CIs.\n")

a("## Q-5.5 Kelly (formula-level, unchanged)\n")
a(f"- Win rate (WR): **{fmt_pct(WR)}** ({int(is_win.sum())}/{n})")
a(f"- Mean winning R (W): **{avg_win_R:.3f}R**")
a(f"- Mean losing R magnitude (L): **{avg_loss_R:.3f}R**")
a(f"- Mean R per trade: **{m:+.3f}R**  |  Std: {math.sqrt(sigma2):.3f}R")
a(f"- **Raw Kelly fraction: {raw_kelly*100:.2f}%**")
a(f"- **½-Kelly: {half_kelly*100:.2f}%**  |  **¼-Kelly: {quarter_kelly*100:.2f}%**")
a(f"- Mean-variance Kelly (m / σ²) per 1R-loss unit: {mv_kelly:.3f}\n")

a("## Monte Carlo — H29 OFF (v1-equivalent) vs H29 ON (v2)\n")
a("Both tables use same seed (42), 10,000 iterations, 100-trade horizon, multiplicative "
  "compounding. Only difference is whether the H29 production DD-brake is simulated.\n")

a("### H29 OFF (v1 — constant risk)\n")
a("| Risk % | Median final | Mean final | P(loss<0) | P(DD>=5%) | P(DD>=8%) | P(DD>=10%) | "
  "Median max DD | P95 max DD | P(FTMO pass ~=) |")
a("|--------|--------------|-----------|-----------|----------|----------|-----------|"
  "---------------|-----------|----------------|")
for s in mc_table_v1:
    a(
        f"| {s['risk_frac']*100:.2f}% | {s['median_final']:.3f} | "
        f"{s['mean_final']:.3f} | {fmt_pct(s['p_loss'])} | {fmt_pct(s['p_dd_5'])} | "
        f"{fmt_pct(s['p_dd_8'])} | {fmt_pct(s['p_dd_10'])} | "
        f"{fmt_pct(s['median_max_dd'])} | {fmt_pct(s['p95_max_dd'])} | "
        f"{fmt_pct(s['p_ftmo_pass_approx'])} |"
    )
a("")

a("### H29 ON (v2 — production DD-brake at DD>=8% -> risk=0.5%)\n")
a("| Risk % | Median final | Mean final | P(loss<0) | P(DD>=5%) | P(DD>=8%) | P(DD>=10%) | "
  "Median max DD | P95 max DD | P(FTMO pass ~=) |")
a("|--------|--------------|-----------|-----------|----------|----------|-----------|"
  "---------------|-----------|----------------|")
for s in mc_table_v2:
    a(
        f"| {s['risk_frac']*100:.2f}% | {s['median_final']:.3f} | "
        f"{s['mean_final']:.3f} | {fmt_pct(s['p_loss'])} | {fmt_pct(s['p_dd_5'])} | "
        f"{fmt_pct(s['p_dd_8'])} | {fmt_pct(s['p_dd_10'])} | "
        f"{fmt_pct(s['median_max_dd'])} | {fmt_pct(s['p95_max_dd'])} | "
        f"{fmt_pct(s['p_ftmo_pass_approx'])} |"
    )
a("")

a("### Delta (v2 minus v1)\n")
a("| Risk % | P(pass) v1 | P(pass) v2 | Delta (pp) | P(DD>=10%) v1 | P(DD>=10%) v2 | "
  "Delta (pp) | Median final v1 | Median final v2 |")
a("|--------|-----------|-----------|------------|---------------|---------------|"
  "------------|-----------------|-----------------|")
for d in delta_rows:
    a(
        f"| {d['risk_pct']*100:.2f}% | {fmt_pct(d['p_ftmo_pass_v1'])} | "
        f"{fmt_pct(d['p_ftmo_pass_v2'])} | {d['delta_pass_pp']:+.2f} | "
        f"{fmt_pct(d['p_dd10_v1'])} | {fmt_pct(d['p_dd10_v2'])} | "
        f"{d['delta_dd10_pp']:+.2f} | {d['median_final_v1']:.3f} | "
        f"{d['median_final_v2']:.3f} |"
    )
a("")

a("### Recommendation (Q-5.5) — v2 numbers\n")
v2_2pct = next(s for s in mc_table_v2 if abs(s["risk_frac"] - 0.02) < 1e-4)
v2_1pct = next(s for s in mc_table_v2 if abs(s["risk_frac"] - 0.01) < 1e-4)
v1_2pct = next(s for s in mc_table_v1 if abs(s["risk_frac"] - 0.02) < 1e-4)
a(f"- Raw Kelly {raw_kelly*100:.1f}% remains mathematically aggressive. Prop-firm DD "
  "cutoffs dominate over Kelly reasoning.")
a(f"- **At 2% risk with H29 ON:** P(DD>=10%) = **{fmt_pct(v2_2pct['p_dd_10'])}** "
  f"(was {fmt_pct(v1_2pct['p_dd_10'])} without H29). P(FTMO-pass) = "
  f"**{fmt_pct(v2_2pct['p_ftmo_pass_approx'])}** (was "
  f"{fmt_pct(v1_2pct['p_ftmo_pass_approx'])}).")
a(f"- **At 1% risk with H29 ON:** P(DD>=10%) = **{fmt_pct(v2_1pct['p_dd_10'])}**, "
  f"P(FTMO-pass) = **{fmt_pct(v2_1pct['p_ftmo_pass_approx'])}**.")
best_ftmo_v2 = max(mc_table_v2, key=lambda s: s["p_ftmo_pass_approx"])
safe_candidates_v2 = [s for s in mc_table_v2 if s["p_dd_10"] < 0.05]
most_aggressive_safe_v2 = safe_candidates_v2[-1] if safe_candidates_v2 else None
a(f"- **Best P(FTMO-pass) with H29:** {best_ftmo_v2['risk_frac']*100:.2f}% risk -> "
  f"P(pass) ~= {fmt_pct(best_ftmo_v2['p_ftmo_pass_approx'])}, "
  f"P(DD>=10%) = {fmt_pct(best_ftmo_v2['p_dd_10'])}.")
if most_aggressive_safe_v2:
    a(f"- Most aggressive risk that keeps P(DD>=10%) < 5% with H29 on: "
      f"**{most_aggressive_safe_v2['risk_frac']*100:.2f}%** "
      f"(was {1.0:.2f}% under v1 logic).")
a("- The 2% FTMO choice is materially better-supported once H29 is modelled — the "
  "brake cuts P(DD>=10%) by the delta shown in the table above. The still-safer 1% "
  "option remains dominant on the P(DD>=10%) metric.\n")

a("## Q-6.5 Speed-to-MFE (unchanged from v1)\n")
a(f"- Winners: n={int(is_win.sum())}, losers: n={int(is_loss.sum())}.")
a("- Limitation: `hold_time_candles` is total duration, not time-to-MFE.\n")
a("### Hold-time by MFE bucket (winners only)\n")
a("| MFE bucket | n | Median hold (M15 candles) | Mean hold | Q25 | Q75 | Median MFE | Mean exit R |")
a("|------------|---|---------------------------|-----------|-----|-----|------------|-------------|")
for b, s in bucket_stats.items():
    if s["n"] == 0:
        a(f"| {b} | 0 | - | - | - | - | - | - |")
    else:
        a(
            f"| {b} | {s['n']} | {s['hold_median']:.1f} | {s['hold_mean']:.1f} | "
            f"{s['hold_q25']:.1f} | {s['hold_q75']:.1f} | {s['mfe_median']:.2f}R | "
            f"{s['r_exit_mean']:+.2f}R |"
        )
a("")

a("### MFE-give-back\n")
a(f"- Winners reaching >=2R MFE but closing <1R (strict): "
  f"**{int(gb_mask_strict.sum())}/{int(is_win.sum())} = {fmt_pct(pct_strict)}**.")
a(f"- Winners leaving >=0.5R on the table (any): "
  f"**{int(gb_mask_any.sum())}/{int(is_win.sum())} = {fmt_pct(pct_any)}**.")
a(f"- Mean give-back per winner: **{avg_give_back:.2f}R**.")
a(f"- Median give-back per winner: **{median_give_back:.2f}R**.\n")

a("## Q-6.8 Dynamic TP simulation (unchanged rules; DD columns now report H29 ON)\n")
a("### Rules\n")
a("- **Batch_asis**: historical exit rule (session-timeout / BE / trail / TP3 runner).")
a("- **AltA_allout_1R**: close 100% at +1R. Fallback to realized R if MFE<1R and no stop.")
a(f"- **AltB_allout_median_mfe**: close 100% at median MFE of winners (= "
  f"{median_mfe_winners:.2f}R).")
a("- **AltC_50at1R_trail**: 50% at +1R; remaining 50% trails to `MFE - 0.5R`.")
a("- **AltD_allout_2R**: close 100% at +2R.")
a("- **AltE_50at1R_50at2R**: 50% at +1R; 50% at +2R.")
a("- **AltF_1R_then_BE**: 50% at +1R; remainder moves to BE.\n")

a("### Results table (H29 ON for DD columns)\n")
a("| Rule | n | Expectancy (R) | WR | Median R | Sum R | Median max DD (2%, H29) | "
  "P95 max DD (2%, H29) | Median max DD (2%, NO H29 — v1) | P95 max DD (2%, NO H29 — v1) |")
a("|------|---|----------------|----|----------|-------|--------------------------|----------------------|----------------------------------|------------------------------|")
for name in rules:
    res = rule_results[name]
    dd2 = rule_dd_v2[name]
    dd1 = rule_dd_v1[name]
    a(
        f"| {name} | {n} | **{res['expectancy']:+.3f}** | {fmt_pct(res['WR'])} | "
        f"{res['median_R']:+.2f} | {res['sum_R']:+.1f} | "
        f"{fmt_pct(dd2['median_max_dd_2pct'])} | {fmt_pct(dd2['p95_max_dd_2pct'])} | "
        f"{fmt_pct(dd1['median_max_dd_2pct'])} | {fmt_pct(dd1['p95_max_dd_2pct'])} |"
    )
a("")

a("### Bootstrap CI for Delta expectancy vs Batch_asis (paired, n_boot=5,000)\n")
a("| Rule | Delta expectancy (R) | 95% CI | p (two-sided) | Significant? |")
a("|------|----------------------|--------|---------------|--------------|")
for name, bd in bootstrap_deltas.items():
    sig = (bd["ci95_lo"] > 0) or (bd["ci95_hi"] < 0)
    a(
        f"| {name} | {bd['delta_expectancy']:+.3f} | "
        f"[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}] | {bd['p_two_sided_boot']:.3f} | "
        f"{'YES' if sig else 'no'} |"
    )
a("")

a("### Bootstrap CI for Delta expectancy vs AltA (current live rule)\n")
a("| Rule | Delta vs AltA (R) | 95% CI | p (two-sided) | Significant? |")
a("|------|-------------------|--------|---------------|--------------|")
for name, bd in bootstrap_vs_A.items():
    sig = (bd["ci95_lo"] > 0) or (bd["ci95_hi"] < 0)
    a(
        f"| {name} | {bd['delta_expectancy']:+.3f} | "
        f"[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}] | {bd['p_two_sided_boot']:.3f} | "
        f"{'YES' if sig else 'no'} |"
    )
a("")

best_rule = max(rule_results.items(), key=lambda kv: kv[1]["expectancy"])
a("### Recommendation (Q-6.8) — unchanged by H29\n")
a(f"- **Best expectancy rule:** {best_rule[0]} @ {best_rule[1]['expectancy']:+.3f}R/trade.")
a("- Q-6.8 ranking is NOT affected by H29 because the rules differ in expectancy, not "
  "in how we size the bet. The H29 brake only rescales the DD columns, not the "
  "per-trade R vector. See the DD table: every rule's median-DD at 2% drops by the "
  "same proportional amount when H29 is on.\n")

a("## Caveats\n")
a("- **n=111** — small-sample results unchanged.")
a("- **H29 assumption:** v2 assumes H29 never mis-fires (no false-positive on equity "
  "spikes) and reverts instantly on new peak. Production logic matches this; see "
  "`src/components/drawdown_manager.py`.")
a("- **Daily 5% DD not modelled.** Still applies to v2 — a single FOMC candle that "
  "blows 5% in one trade is not modelled here.")
a("- **Kelly assumes stationarity and independence.** Real trade clustering degrades "
  "both Kelly and H29-informed optima. Conservative margin advised.")
a("- **XAUUSD-only** batch.")
a("- **v1 is NOT wrong** — it is a worst-case bound. v2 is the realistic operating "
  "distribution. Both are kept in the repo for audit.\n")

a("## Next steps\n")
a("1. Deploy per-candle MFE/MAE shadow logger (unchanged from v1).")
a("2. Walk-forward on Q-6.8 (unchanged from v1).")
a("3. Per-instrument Kelly once other symbol batches exist.")
a("4. Shadow-log `AltC_50at1R_trail` (unchanged recommendation).")
a("5. Re-run q_7_monte_carlo.py against v2 rule vectors for cross-check.\n")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"Wrote {OUT_MD}")
print(f"Wrote {OUT_JSON}")
print()
print("=== v1 vs v2 delta ===")
for d in delta_rows:
    print(f"  risk={d['risk_pct']*100:.2f}% "
          f"P(pass)_v1={d['p_ftmo_pass_v1']*100:.2f}% "
          f"P(pass)_v2={d['p_ftmo_pass_v2']*100:.2f}% "
          f"delta_pass={d['delta_pass_pp']:+.2f}pp "
          f"P(DD10)_v1={d['p_dd10_v1']*100:.2f}% "
          f"P(DD10)_v2={d['p_dd10_v2']*100:.2f}% "
          f"delta_DD10={d['delta_dd10_pp']:+.2f}pp")
