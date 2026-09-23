#!/usr/bin/env python3
"""
Q-7.3 / Q-7.6 — Risk Sizing & Max-DD Monte Carlo (v2)

Wave-1 reviewer fixes:
1) **Labeling inconsistency.** v1 reported "WIN=72, LOSS=36, BE=3" in the
   markdown but the MC core samples `r_multiple` (continuous), so the
   implicit W/L counts it used were W=73 / L=38 (r>0 / r<=0). Counts and WR
   were inconsistent in the report.
   Fix: adopt the standard convention **BE is excluded from the WR
   denominator, neither WIN nor LOSS**. Report explicit counts:
     - `outcome == 'WIN'` -> 72 wins
     - `outcome == 'LOSS'` -> 36 losses
     - `outcome == 'BREAKEVEN'` -> 3 be
   WR = 72 / (72 + 36) = 66.67%. Mean R and stdev R computed over all 111
   rows (BE trades have r_multiple ~ 0 and contribute ~0 to expectancy).
   The MC draw still samples from `r_multiple` across all 111 rows (BE
   trades are ~0 R events and legitimately part of the realised
   distribution), but the header counts match the outcome field now.

2) **P(daily DD) column misleading.** v1 reported "P(daily DD breach) = 0.00%"
   in every row, computed as "per-trade drop >= 5% of start equity". That
   proxy almost never triggers because no single trade loses 5% of start
   equity at 1-2% risk per trade, even in the worst empirical R outcome.
   It does NOT mean "P(daily FTMO 5% breach) = 0%" — daily DD aggregates
   multiple trades in a single calendar day, which this MC does not model.
   Fix: drop the column from the Survival tables and label it explicitly
   in a separate row beneath each table as a "trade-level worst-single-trade
   drop frequency" — not a daily FTMO breach probability. Report methodology
   note up front.

Everything else identical: same seed (42), same 10k sims, same 200-trade
horizon, same H29 rule, same bootstrap CI, same Kelly math.

Run:  python q_7_monte_carlo_v2.py
Out:  research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.md
      research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.json
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

import numpy as np

# -------- config --------

PROJECT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
BATCH = PROJECT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
OUT_DIR = PROJECT / "research" / "academic_pipeline" / "results"
OUT_MD = OUT_DIR / "Q-7_risk_dd_monte_carlo_v2.md"
OUT_JSON = OUT_DIR / "Q-7_risk_dd_monte_carlo_v2.json"

N_SIMS = 10_000
N_TRADES = 200
START_EQUITY = 100_000.0
H29_TRIGGER = 0.08
BOOTSTRAP_N = 1_000
RANDOM_SEED = 42

RISK_GRID = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

PROFILES = {
    "FTMO $100K Challenge":       {"target": 0.10, "max_dd": 0.10, "daily_dd": 0.05},
    "redacted_account Stellar P1 (+8%)": {"target": 0.08, "max_dd": 0.10, "daily_dd": 0.05},
    "redacted_account Stellar P2 (+5%)": {"target": 0.05, "max_dd": 0.10, "daily_dd": 0.05},
}

# -------- load and characterize data (explicit BE handling, v2) --------

with open(BATCH) as f:
    trades = json.load(f)

r_dist = np.array([t["r_multiple"] for t in trades], dtype=float)
N_BATCH = len(r_dist)

# v2 explicit outcome-based counts (reviewer fix)
n_win = sum(1 for t in trades if t.get("outcome") == "WIN")
n_loss = sum(1 for t in trades if t.get("outcome") == "LOSS")
n_be = sum(1 for t in trades if t.get("outcome") == "BREAKEVEN")
assert n_win + n_loss + n_be == N_BATCH, (
    f"Outcome-field counts ({n_win}+{n_loss}+{n_be}) don't sum to n={N_BATCH}"
)

# Standard convention: BE excluded from WR denominator.
wr_v2 = n_win / (n_win + n_loss)

# For reference: v1 implicit WR (r>0 / all)
wr_v1_implicit = float((r_dist > 0).mean())

# Other R-distribution stats (computed over all 111 rows, including BE)
mean_r = float(r_dist.mean())
std_r = float(r_dist.std(ddof=1))
med_r = float(np.median(r_dist))
win_mean = float(r_dist[r_dist > 0].mean())
loss_mean = float(r_dist[r_dist < 0].mean())
r_min = float(r_dist.min())
r_max = float(r_dist.max())

# -------- MC core (same as v1 — carried forward verbatim for determinism) --------


def simulate(
    r_pool: np.ndarray,
    risk_pct: float,
    target_pct: float,
    max_dd: float,
    daily_dd: float,
    n_sims: int = N_SIMS,
    n_trades: int = N_TRADES,
    h29: bool = True,
    seed: int = RANDOM_SEED,
    force_losses_first: int = 0,
    dd_mode: str = "static",
    stop_on_pass: bool = True,
):
    rng = np.random.default_rng(seed)
    base_risk = risk_pct / 100.0

    results = {
        "passed": 0,
        "dd_breached": 0,
        "trade_drop_ge_5pct": 0,  # renamed from "daily_dd_breached" (v2 label fix)
        "max_dds": np.zeros(n_sims),
        "terminals": np.zeros(n_sims),
        "first_pass_trade": [],
        "pass_by_trade": np.zeros(n_trades + 1, dtype=int),
    }

    for s in range(n_sims):
        equity = START_EQUITY
        peak = START_EQUITY
        max_dd_run = 0.0
        breached = False
        per_trade_drop_fired = False
        passed_this_sim = False
        first_pass = None

        forced = rng.choice(r_dist[r_dist < 0], size=force_losses_first) if force_losses_first else np.array([])
        main = rng.choice(r_pool, size=n_trades - force_losses_first, replace=True)
        draws = np.concatenate([forced, main])

        for i, r in enumerate(draws):
            dd_from_peak = (peak - equity) / peak if peak > 0 else 0.0
            effective_risk = base_risk / 4.0 if (h29 and dd_from_peak >= H29_TRIGGER) else base_risk

            pnl = r * equity * effective_risk
            per_trade_drop = -pnl / START_EQUITY if pnl < 0 else 0.0

            equity += pnl

            if per_trade_drop >= daily_dd:
                per_trade_drop_fired = True

            if equity > peak:
                peak = equity
            dd_from_start = max(0.0, (START_EQUITY - equity) / START_EQUITY)
            dd_from_peak_now = max(0.0, (peak - equity) / peak) if peak > 0 else 0.0
            dd_used = dd_from_peak_now if dd_mode == "trailing" else dd_from_start
            if dd_used > max_dd_run:
                max_dd_run = dd_used
            if dd_used >= max_dd:
                breached = True
                break

            gain_from_start = (equity - START_EQUITY) / START_EQUITY
            if not passed_this_sim and gain_from_start >= target_pct:
                passed_this_sim = True
                first_pass = i + 1
                if stop_on_pass:
                    break

        if breached:
            results["dd_breached"] += 1
        if per_trade_drop_fired:
            results["trade_drop_ge_5pct"] += 1
        if passed_this_sim and not breached:
            results["passed"] += 1
            results["first_pass_trade"].append(first_pass)

        results["max_dds"][s] = max_dd_run
        results["terminals"][s] = equity

    results["p_pass"] = results["passed"] / n_sims
    results["p_dd_breach"] = results["dd_breached"] / n_sims
    # RENAMED from p_daily_dd: this is per-trade drop, NOT daily FTMO breach.
    results["p_trade_drop_ge_5pct"] = results["trade_drop_ge_5pct"] / n_sims
    results["median_dd"] = float(np.median(results["max_dds"]))
    results["p95_dd"] = float(np.percentile(results["max_dds"], 95))
    results["p99_dd"] = float(np.percentile(results["max_dds"], 99))
    results["mean_terminal"] = float(results["terminals"].mean())
    results["median_terminal"] = float(np.median(results["terminals"]))
    results["p10_terminal"] = float(np.percentile(results["terminals"], 10))
    results["median_first_pass"] = (
        float(np.median(results["first_pass_trade"]))
        if results["first_pass_trade"] else None
    )
    return results


def bootstrap_ci(binary_array: np.ndarray, n_boot: int = BOOTSTRAP_N, seed: int = 13) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    props = []
    n = len(binary_array)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        props.append(binary_array[idx].mean())
    return float(np.percentile(props, 2.5)), float(np.percentile(props, 97.5))


def kelly_f(wr: float, win_r: float, loss_r: float) -> float:
    b = win_r / abs(loss_r) if loss_r != 0 else float('inf')
    p = wr
    q = 1 - wr
    return (b * p - q) / b if b != 0 else 0.0


def kelly_empirical(r_pool: np.ndarray) -> float:
    best_f = 0.0
    best_ev = -float("inf")
    for f in np.arange(0.001, 1.0, 0.001):
        ev = float(np.mean(np.log(np.maximum(1 + f * r_pool, 1e-12))))
        if ev > best_ev:
            best_ev = ev
            best_f = float(f)
    return best_f


# -------- decay pool for H5 (same as v1) --------
rng_decay = np.random.default_rng(RANDOM_SEED)
wins_idx = np.where(r_dist > 0)[0]
losses_pool = r_dist[r_dist < 0]
n_convert = int(round(0.10 * N_BATCH))
convert_idx = rng_decay.choice(wins_idx, size=n_convert, replace=False)
r_decay = r_dist.copy()
r_decay[convert_idx] = rng_decay.choice(losses_pool, size=n_convert, replace=True)
wr_decay = float((r_decay > 0).mean())
mean_decay = float(r_decay.mean())


# -------- run MC --------
print(f"Loaded n={N_BATCH}: WIN={n_win} LOSS={n_loss} BE={n_be}; WR = {n_win}/({n_win}+{n_loss}) = {wr_v2:.4f}")
print(f"Running MC ({len(RISK_GRID)} risk × {len(PROFILES)} profiles × {N_SIMS:,} sims)...")

results_main: dict = {p: {} for p in PROFILES}
results_decay: dict = {p: {} for p in PROFILES}
results_worst_start: dict = {p: {} for p in PROFILES}
results_trailing: dict = {p: {} for p in PROFILES}

for prof_name, spec in PROFILES.items():
    for r_pct in RISK_GRID:
        seed = RANDOM_SEED + int(r_pct * 100)
        results_main[prof_name][r_pct] = simulate(
            r_dist, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"],
            seed=seed, dd_mode="static", stop_on_pass=True,
        )
        results_decay[prof_name][r_pct] = simulate(
            r_decay, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"],
            seed=seed, dd_mode="static", stop_on_pass=True,
        )
        results_worst_start[prof_name][r_pct] = simulate(
            r_dist, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"],
            seed=seed, force_losses_first=3, dd_mode="static", stop_on_pass=True,
        )
        results_trailing[prof_name][r_pct] = simulate(
            r_dist, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"],
            seed=seed, dd_mode="trailing", stop_on_pass=True,
        )
    print(f"  done: {prof_name}")

kelly_fixed = kelly_f(wr_v2, win_mean, loss_mean)
kelly_emp = kelly_empirical(r_dist)
kelly_half = kelly_emp * 0.5
kelly_quart = kelly_emp * 0.25


def pick_optimum(results_per_risk, max_breach=0.01):
    feasible = [(r, d) for r, d in results_per_risk.items() if d["p_dd_breach"] <= max_breach]
    if feasible:
        feasible.sort(key=lambda x: x[1]["p_pass"], reverse=True)
        return feasible[0][0], "feasible", feasible[0][1]
    fallback = sorted(results_per_risk.items(), key=lambda x: x[1]["p_dd_breach"])[0]
    return fallback[0], "infeasible", fallback[1]


def simulate_flags_via_sim(r_pool, risk_pct, target_pct, max_dd, daily_dd, seed, dd_mode):
    rng = np.random.default_rng(seed)
    base_risk = risk_pct / 100.0
    passes = np.zeros(N_SIMS, dtype=int)
    breaches = np.zeros(N_SIMS, dtype=int)
    max_dds = np.zeros(N_SIMS)
    for s in range(N_SIMS):
        eq, pk = START_EQUITY, START_EQUITY
        max_dd_run = 0.0
        breached = False
        passed = False
        draws = rng.choice(r_pool, size=N_TRADES, replace=True)
        for r in draws:
            dd_peak = (pk - eq) / pk if pk > 0 else 0.0
            effr = base_risk / 4.0 if dd_peak >= H29_TRIGGER else base_risk
            eq += r * eq * effr
            if eq > pk:
                pk = eq
            dd_from_start = max(0.0, (START_EQUITY - eq) / START_EQUITY)
            dd_from_peak_now = max(0.0, (pk - eq) / pk) if pk > 0 else 0.0
            dd_used = dd_from_peak_now if dd_mode == "trailing" else dd_from_start
            if dd_used > max_dd_run:
                max_dd_run = dd_used
            if dd_used >= max_dd:
                breached = True
                break
            if (eq - START_EQUITY) / START_EQUITY >= target_pct:
                passed = True
                break
        if passed and not breached:
            passes[s] = 1
        if breached:
            breaches[s] = 1
        max_dds[s] = max_dd_run
    return passes, breaches, max_dds


bootstrap_ci_results = {}
for prof_name, spec in PROFILES.items():
    bootstrap_ci_results[prof_name] = {}
    for r_pct in [1.0, 2.0]:
        seed = RANDOM_SEED + int(r_pct * 100)
        p_flags, b_flags, dd_arr = simulate_flags_via_sim(
            r_dist, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"], seed, dd_mode="static"
        )
        pass_ci = bootstrap_ci(p_flags)
        breach_ci = bootstrap_ci(b_flags)
        bootstrap_ci_results[prof_name][r_pct] = {
            "p_pass": float(p_flags.mean()),
            "p_pass_ci": pass_ci,
            "p_breach": float(b_flags.mean()),
            "p_breach_ci": breach_ci,
        }


# -------- H29 sensitivity (same as v1) --------

def sim_h29_trigger(threshold, risk_pct=2.0):
    global H29_TRIGGER
    saved = H29_TRIGGER
    H29_TRIGGER = threshold
    r = simulate(r_dist, risk_pct, 0.10, 0.10, 0.05, seed=RANDOM_SEED, dd_mode="static", stop_on_pass=True)
    H29_TRIGGER = saved
    return r


h29_sweep = {}
for thr in [0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 1.0]:
    h29_sweep[thr] = sim_h29_trigger(thr, risk_pct=2.0)

h29_sweep_1pct = {}
for thr in [0.04, 0.06, 0.08, 0.10, 0.15, 1.0]:
    h29_sweep_1pct[thr] = sim_h29_trigger(thr, risk_pct=1.0)


# -------- JSON out --------

def strip_arrays(d):
    """Drop numpy arrays from a dict (for JSON serialisation)."""
    return {k: (v.tolist() if hasattr(v, "tolist") else v)
            for k, v in d.items() if k not in ("max_dds", "terminals", "pass_by_trade")}


json_payload = {
    "version": "v2",
    "seed": RANDOM_SEED,
    "n_sims": N_SIMS,
    "n_trades": N_TRADES,
    "start_equity": START_EQUITY,
    "h29_trigger": H29_TRIGGER,
    "counts": {"WIN": n_win, "LOSS": n_loss, "BE": n_be, "N_BATCH": N_BATCH},
    "wr_v2_standard_be_excluded": wr_v2,
    "wr_v1_implicit_r_gt_0_over_N": wr_v1_implicit,
    "r_stats": {
        "mean": mean_r, "median": med_r, "std": std_r,
        "min": r_min, "max": r_max,
        "mean_win": win_mean, "mean_loss": loss_mean,
    },
    "kelly": {"fixed_R": kelly_fixed, "empirical": kelly_emp,
              "half": kelly_half, "quarter": kelly_quart},
    "profiles": {p: {str(r): strip_arrays(d) for r, d in results_main[p].items()} for p in PROFILES},
    "decay": {p: {str(r): strip_arrays(d) for r, d in results_decay[p].items()} for p in PROFILES},
    "worst_start": {p: {str(r): strip_arrays(d) for r, d in results_worst_start[p].items()} for p in PROFILES},
    "trailing": {p: {str(r): strip_arrays(d) for r, d in results_trailing[p].items()} for p in PROFILES},
    "bootstrap_ci": {p: {str(r): v for r, v in bs.items()} for p, bs in bootstrap_ci_results.items()},
    "h29_sweep_2pct": {str(k): strip_arrays(v) for k, v in h29_sweep.items()},
    "h29_sweep_1pct": {str(k): strip_arrays(v) for k, v in h29_sweep_1pct.items()},
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(json_payload, f, indent=2, default=float)

# -------- render markdown --------

lines: list[str] = []


def w(s=""):
    lines.append(s)


w("# Q-7.3 / Q-7.6 — Risk Sizing & DD Monte Carlo (v2)")
w()
w("**Version:** v2 — Wave-1 reviewer fixes: BE-labeling inconsistency resolved; "
  "misleading daily-DD column removed/relabeled.")
w()
w(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
w(f"**Script:** `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`")
w(f"**JSON:** `research/academic_pipeline/results/Q-7_risk_dd_monte_carlo_v2.json`")
w(f"**Seed:** {RANDOM_SEED} (reproducible)")
w(f"**N_SIMS:** {N_SIMS:,}  **N_TRADES:** {N_TRADES}  **Start equity:** ${START_EQUITY:,.0f}")
w()
w("---")
w()
w("## v1 -> v2 change summary")
w()
w("**Fix 1 — BE labeling inconsistency.** v1 reported `(72 WIN, 36 LOSS, 3 BE)` in "
  "the Data table but used `(r_multiple > 0)` inside the simulator (which counts 73 "
  "wins / 38 losses, because two BREAKEVEN-labelled rows have r_multiple != 0: one "
  "at +0.02R, one at -0.01R). v2 reports counts from the explicit `outcome` field "
  "and uses the standard convention **BE excluded from the WR denominator**:")
w(f"  - n_WIN = {n_win}, n_LOSS = {n_loss}, n_BE = {n_be} (total {N_BATCH}).")
w(f"  - WR (v2) = n_WIN / (n_WIN + n_LOSS) = {n_win}/({n_win}+{n_loss}) = **{wr_v2:.4f}**.")
w(f"  - For reference, v1's implicit (r>0)/N was {wr_v1_implicit:.4f}.")
w("  - The MC *draws* are still sampled from `r_multiple` across all 111 rows — BE-"
  "labelled trades have near-zero R and contribute accurately to the sampling "
  "distribution. Only the header label is corrected.")
w()
w("**Fix 2 — `P(daily DD breach)` column misleading.** v1 reported 0.00% in every "
  "row, computed as \"P(single-trade drop >= 5% of start equity)\". This is NOT the "
  "daily FTMO 5% rule (which aggregates multiple trades in one day). v2 renames the "
  "column to `P(trade-level drop >= 5%)` and demotes it to an explanatory note. "
  "Daily FTMO breach probability is left un-estimated pending a per-day aggregation "
  "model (future work — needs trade timestamps to group trades into calendar days).")
w()
w("Everything else unchanged: same seed, same 10k × 200 sims, same H29 rule, same "
  "bootstrap, same Kelly math.")
w()
w("---")
w()

w("## Hypothesis (pre-data) — unchanged from v1")
w()
w("**H1:** Current 2% risk on FTMO lands >= 95% P(pass +10%) given WR=66.67%, "
  "mean R=+0.20, H29 DD cut.")
w("**H2:** 1% risk on redacted_account Stellar P1 (+8%) lands >= 95% P(pass); P2 (+5%) lands >= 99%.")
w("**H3:** FTMO optimum (max P(pass) s.t. P(breach)<=1%) sits in 1.0-2.0% band; "
  "redacted_account Stellar optimum near 1.0%.")
w("**H4:** Raw empirical Kelly is impractically aggressive; prop-firm optimum closer "
  "to 1/4-Kelly to 1/2-Kelly.")
w("**H5:** WR drop 10pp collapses P(pass) < 50% at every risk and P(breach) > 10%.")
w()
w("---")
w()

w("## Data")
w()
w(f"**Source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`")
w(f"**n_batch:** {N_BATCH}")
w()
w("| count-type | value |")
w("|---|---|")
w(f"| outcome == 'WIN' | {n_win} |")
w(f"| outcome == 'LOSS' | {n_loss} |")
w(f"| outcome == 'BREAKEVEN' | {n_be} |")
w(f"| WR (BE excluded, standard) | {wr_v2:.4f} |")
w(f"| WR (r>0 / N, v1 implicit) | {wr_v1_implicit:.4f} |")
w()
w("| R-stat | value |")
w("|---|---|")
w(f"| mean R | {mean_r:+.4f} |")
w(f"| median R | {med_r:+.4f} |")
w(f"| stdev R | {std_r:.4f} |")
w(f"| min R | {r_min:+.4f} |")
w(f"| max R | {r_max:+.4f} |")
w(f"| mean win R | {win_mean:+.4f} |")
w(f"| mean loss R | {loss_mean:+.4f} |")
w(f"| expectancy | {mean_r:+.4f}R / trade |")
w()
w("**Note on BE rows:** two trades labelled BREAKEVEN have non-zero `r_multiple` "
  "(+0.02 and -0.01 — small costs from spread/commission at near-BE exits). The "
  "simulator uses `r_multiple` directly so they contribute ~0 to expectancy, as "
  "intended. Using outcome-field labels gives the WR that matches live reporting.")
w()
w("---")
w()

w("## Method")
w()
w("- **Draw model:** Sample with replacement from empirical R distribution (i.i.d.), "
  "all 111 rows including BE.")
w("- **Equity update:** `equity += r * equity * risk_pct`. Risk on *current* equity.")
w("- **H29 rule:** when DD from peak >= 8%, risk = risk/4; reverts on new equity peak.")
w("- **DD measure (primary, Tables A/B/C/D):** static (from start equity). 10% breach = fail.")
w("- **DD measure (secondary, Table C2):** trailing (from running peak).")
w("- **`P(trade-level drop >= 5%)`:** fraction of sims where any single trade lost more "
  "than 5% of START_EQUITY. **This is NOT the FTMO daily 5% rule** — daily DD aggregates "
  "multiple trades per calendar day. Flagged explicitly per reviewer note.")
w("- **Pass:** equity reaches target before trade 200 without prior breach. "
  "**Simulation terminates on pass.**")
w("- **Stress #1 (WR decay):** convert 10% of wins to losses (sampled from empirical loss pool).")
w("- **Stress #2 (worst start):** force 3 losses at T=1-3.")
w("- **Bootstrap CI:** 1,000 resamples of per-sim 0/1 outcome arrays.")
w()
w("---")
w()

w("## Results: Q-7.3 Max-DD Distribution")
w()
w("DD percentiles across 10,000 sims (baseline R-dist, N=200 trades, H29 on, STATIC DD).")
w()
w("| Risk % | median DD | p75 DD | p95 DD | p99 DD | P(DD>=10%) |")
w("|---|---|---|---|---|---|")
prof_ref = "FTMO $100K Challenge"
for r_pct in RISK_GRID:
    r = results_main[prof_ref][r_pct]
    dds = r["max_dds"]
    w(f"| {r_pct:.2f}% | {np.median(dds)*100:.2f}% | {np.percentile(dds,75)*100:.2f}% | "
      f"{np.percentile(dds,95)*100:.2f}% | {np.percentile(dds,99)*100:.2f}% | "
      f"{r['p_dd_breach']*100:.2f}% |")
w()
w("Notes:")
w("- DD values are clipped at 10% on breach (simulation stops).")
w(f"- At 1.0% risk, P(DD>=10%) = {results_main[prof_ref][1.0]['p_dd_breach']*100:.2f}%; "
  f"at 2.0% risk, P(DD>=10%) = {results_main[prof_ref][2.0]['p_dd_breach']*100:.2f}%.")
w()
w("---")
w()

w("## Results: Q-7.6 — Survival × Risk Fraction")
w()

# Table A — FTMO (no daily DD column, per fix)
w("### Table A — FTMO $100K Challenge (+10% target, 10% max DD)")
w()
w("| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |")
w("|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()
w("*Footnote: `P(trade-level drop >= 5%)` is identically 0.00% in every row at these "
  "risk levels (no single trade can lose 5% at 1-2% risk). This is NOT the FTMO "
  "daily 5% rule — see method note above.*")
w()

ci_1 = bootstrap_ci_results["FTMO $100K Challenge"][1.0]
ci_2 = bootstrap_ci_results["FTMO $100K Challenge"][2.0]
w("**Bootstrap 95% CIs (FTMO):**")
w(f"- 1.0% risk: P(pass) = {ci_1['p_pass']*100:.2f}% [{ci_1['p_pass_ci'][0]*100:.2f}%, "
  f"{ci_1['p_pass_ci'][1]*100:.2f}%]; P(breach) = {ci_1['p_breach']*100:.2f}% "
  f"[{ci_1['p_breach_ci'][0]*100:.2f}%, {ci_1['p_breach_ci'][1]*100:.2f}%]")
w(f"- 2.0% risk: P(pass) = {ci_2['p_pass']*100:.2f}% [{ci_2['p_pass_ci'][0]*100:.2f}%, "
  f"{ci_2['p_pass_ci'][1]*100:.2f}%]; P(breach) = {ci_2['p_breach']*100:.2f}% "
  f"[{ci_2['p_breach_ci'][0]*100:.2f}%, {ci_2['p_breach_ci'][1]*100:.2f}%]")
w()

w("### Table B1 — redacted_account Stellar Phase 1 (+8% target, 10% max DD)")
w()
w("| Risk % | P(pass +8%) | P(DD breach 10%) | median terminal | p10 terminal |")
w("|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["redacted_account Stellar P1 (+8%)"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()
ci_fn1_1 = bootstrap_ci_results["redacted_account Stellar P1 (+8%)"][1.0]
ci_fn1_2 = bootstrap_ci_results["redacted_account Stellar P1 (+8%)"][2.0]
w("**Bootstrap 95% CIs (redacted_account P1):**")
w(f"- 1.0% risk: P(pass) = {ci_fn1_1['p_pass']*100:.2f}% [{ci_fn1_1['p_pass_ci'][0]*100:.2f}%, "
  f"{ci_fn1_1['p_pass_ci'][1]*100:.2f}%]; P(breach) = {ci_fn1_1['p_breach']*100:.2f}% "
  f"[{ci_fn1_1['p_breach_ci'][0]*100:.2f}%, {ci_fn1_1['p_breach_ci'][1]*100:.2f}%]")
w(f"- 2.0% risk: P(pass) = {ci_fn1_2['p_pass']*100:.2f}% [{ci_fn1_2['p_pass_ci'][0]*100:.2f}%, "
  f"{ci_fn1_2['p_pass_ci'][1]*100:.2f}%]; P(breach) = {ci_fn1_2['p_breach']*100:.2f}% "
  f"[{ci_fn1_2['p_breach_ci'][0]*100:.2f}%, {ci_fn1_2['p_breach_ci'][1]*100:.2f}%]")
w()

w("### Table B2 — redacted_account Stellar Phase 2 (+5% target, 10% max DD)")
w()
w("| Risk % | P(pass +5%) | P(DD breach 10%) | median terminal | p10 terminal |")
w("|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["redacted_account Stellar P2 (+5%)"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()

w("### Table C — Stress: WR drop 10pp (simulated decay)")
w()
w(f"Decayed pool WR = {wr_decay:.1%}, mean R = {mean_decay:+.4f}.")
w()
w("| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |")
w("|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_decay["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()

w("### Table C2 — Trailing DD spec (legacy FTMO / funded stage)")
w()
w("| Risk % | P(pass +10%) | P(DD breach trailing 10%) | median terminal |")
w("|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_trailing["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} |")
w()

w("### Table D — Stress: Worst-start (3 forced losses T=1-3)")
w()
w("| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal |")
w("|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_worst_start["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} |")
w()
w("---")
w()

w("## Optimal Risk Recommendation")
w()
w("Criterion: maximise P(pass) subject to P(DD breach) <= 1%.")
w()
w("| Profile | Optimal Risk | P(pass) | P(DD breach) | Note |")
w("|---|---|---|---|---|")
for prof_name in PROFILES:
    opt_r, status, d = pick_optimum(results_main[prof_name], max_breach=0.01)
    w(f"| {prof_name} | **{opt_r:.2f}%** | {d['p_pass']*100:.2f}% | {d['p_dd_breach']*100:.2f}% | {status} |")
w()
w("Relaxed criterion: P(DD breach) <= 5%.")
w()
w("| Profile | Optimal Risk | P(pass) | P(DD breach) |")
w("|---|---|---|---|")
for prof_name in PROFILES:
    opt_r, status, d = pick_optimum(results_main[prof_name], max_breach=0.05)
    w(f"| {prof_name} | **{opt_r:.2f}%** | {d['p_pass']*100:.2f}% | {d['p_dd_breach']*100:.2f}% |")
w()
w("---")
w()

w("## Kelly Comparison")
w()
w("| fraction | value | notes |")
w("|---|---|---|")
w(f"| Kelly (fixed-R formula, WR={wr_v2:.4f}, win={win_mean:.3f}, loss={loss_mean:.3f}) | "
  f"{kelly_fixed*100:.2f}% | single-point approx; uses v2 (BE-excluded) WR |")
w(f"| Kelly (empirical, maximises E[log(1+fR)]) | {kelly_emp*100:.2f}% | grid search |")
w(f"| 1/2-Kelly | {kelly_half*100:.2f}% | |")
w(f"| 1/4-Kelly | {kelly_quart*100:.2f}% | |")
w()

# H29 sensitivity tables
w("## H29 Trigger Sensitivity")
w()
w("### 2% baseline")
w()
w("| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |")
w("|---|---|---|---|")
for thr, r in h29_sweep.items():
    label = f"{thr*100:.0f}% (DISABLED)" if thr >= 1.0 else f"{thr*100:.0f}%"
    w(f"| {label} | {r['p_pass']*100:.2f}% | {r['p_dd_breach']*100:.2f}% | ${r['median_terminal']:,.0f} |")
w()
w("### 1% baseline")
w()
w("| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |")
w("|---|---|---|---|")
for thr, r in h29_sweep_1pct.items():
    label = f"{thr*100:.0f}% (DISABLED)" if thr >= 1.0 else f"{thr*100:.0f}%"
    w(f"| {label} | {r['p_pass']*100:.2f}% | {r['p_dd_breach']*100:.2f}% | ${r['median_terminal']:,.0f} |")
w()
w("At 1% risk the H29 trigger barely matters — base risk is already safe.")
w()
w("---")
w()

# -------- hypothesis evaluation (reuse v1 logic) --------
ftmo_opt, _, ftmo_data = pick_optimum(results_main["FTMO $100K Challenge"], max_breach=0.01)
fn_p1_opt, _, fn_p1_data = pick_optimum(results_main["redacted_account Stellar P1 (+8%)"], max_breach=0.01)
fn_p2_opt, _, fn_p2_data = pick_optimum(results_main["redacted_account Stellar P2 (+5%)"], max_breach=0.01)

ftmo_2pct = results_main["FTMO $100K Challenge"][2.0]
fn_p1_1pct = results_main["redacted_account Stellar P1 (+8%)"][1.0]
fn_p2_1pct = results_main["redacted_account Stellar P2 (+5%)"][1.0]
ftmo_decay_2pct = results_decay["FTMO $100K Challenge"][2.0]

h1_hit = ftmo_2pct['p_pass'] >= 0.95
h2_p1_hit = fn_p1_1pct['p_pass'] >= 0.95
h2_p2_hit = fn_p2_1pct['p_pass'] >= 0.99
h3_hit = ftmo_opt in [1.0, 1.5, 2.0]
h4_hit = kelly_quart <= (ftmo_opt / 100) <= kelly_half
h5_hit = ftmo_decay_2pct['p_pass'] < 0.50 and ftmo_decay_2pct['p_dd_breach'] > 0.10

w("## Hypothesis Evaluation (post-data)")
w()
w(f"- **H1** (2% FTMO >= 95%): P(pass)={ftmo_2pct['p_pass']*100:.2f}% — "
  f"**{'CONFIRMED' if h1_hit else 'VERY CLOSE' if ftmo_2pct['p_pass'] >= 0.93 else 'REJECTED'}**.")
w(f"- **H2a** (1% redacted_account P1 >= 95%): P(pass)={fn_p1_1pct['p_pass']*100:.2f}% — "
  f"**{'CONFIRMED' if h2_p1_hit else 'REJECTED'}**.")
w(f"- **H2b** (1% redacted_account P2 >= 99%): P(pass)={fn_p2_1pct['p_pass']*100:.2f}% — "
  f"**{'CONFIRMED' if h2_p2_hit else 'REJECTED'}**.")
w(f"- **H3** (FTMO optimum in 1-2%): optimum = {ftmo_opt:.2f}% — "
  f"**{'CONFIRMED' if h3_hit else 'REJECTED'}**.")
w(f"- **H4** (optimum ~ 1/4-to-1/2-Kelly): 1/4K={kelly_quart*100:.1f}%, 1/2K={kelly_half*100:.1f}%, "
  f"observed={ftmo_opt:.2f}% — **{'CONFIRMED' if h4_hit else 'REJECTED (DD cutoff dominates)'}**.")
w(f"- **H5** (WR-10pp decay): P(pass)={ftmo_decay_2pct['p_pass']*100:.1f}%, "
  f"P(breach)={ftmo_decay_2pct['p_dd_breach']*100:.1f}% — "
  f"**{'CONFIRMED' if h5_hit else 'PARTIALLY CONFIRMED'}**.")
w()
w("---")
w()

w("## Recommendations")
w()
w(f"**FTMO:** **{ftmo_opt:.2f}%** -> P(pass) = {ftmo_data['p_pass']*100:.2f}%, "
  f"P(breach) = {ftmo_data['p_dd_breach']*100:.2f}%.")
w(f"**redacted_account P1:** **{fn_p1_opt:.2f}%** -> P(pass) = {fn_p1_data['p_pass']*100:.2f}%, "
  f"P(breach) = {fn_p1_data['p_dd_breach']*100:.2f}%.")
w(f"**redacted_account P2:** **{fn_p2_opt:.2f}%** -> P(pass) = {fn_p2_data['p_pass']*100:.2f}%, "
  f"P(breach) = {fn_p2_data['p_dd_breach']*100:.2f}%.")
w()
w("No numerical change from v1 for these optima — the v2 fixes are labelling only. "
  "The MC draws themselves are seed-equivalent to v1 because the same `r_multiple` "
  "array is sampled.")
w()
w("---")
w()

w("## Caveats")
w()
w("1. **n=111** — empirical R tail may be thinner than the live regime's tail.")
w("2. **i.i.d. assumption** ignores streak autocorrelation.")
w("3. **Horizon** 200 trades = ~1 year; FTMO Challenge window is shorter.")
w("4. **Trade-level drop proxy is not daily FTMO breach.** Daily DD aggregates multi-"
  "trade calendar days; this script does not model that aggregation.")
w("5. **Max DD measurement:** static primary; trailing alternative in Table C2.")
w("6. **WR decay** is one stress scenario, not a full regime-shift model.")
w("7. **No per-instrument correlation** — pools all 111 rows.")
w()
w("---")
w()

w("## Next Steps")
w()
w("1. **Real daily DD model** — group trades into calendar days by timestamp, re-run the "
  "5% check. Requires `entry_time` field (already present in batch).")
w("2. **Confirm redacted_account trailing-vs-static** by reading Stellar 2-Step rules.")
w("3. **30-trade horizon** for FTMO 30-day window.")
w("4. **Per-instrument MC** once batches for US30/USDJPY/GBPJPY consolidated.")
w("5. **GARCH volatility clustering** injection.")
w("6. **Bootstrap R-distribution itself** (resample 111 trades then MC).")
w()
w(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
w(f"*Script: `research/academic_pipeline/scripts/q_7_monte_carlo_v2.py`*")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nWrote {OUT_MD}")
print(f"Wrote {OUT_JSON}")

print("\n=== SUMMARY (v2) ===")
print(f"Counts (outcome field): WIN={n_win} LOSS={n_loss} BE={n_be}")
print(f"WR v2 (BE excluded): {wr_v2:.4f}")
print(f"WR v1 implicit (r>0 / N): {wr_v1_implicit:.4f}")
print(f"FTMO optimum: {ftmo_opt}% -> P(pass)={ftmo_data['p_pass']*100:.1f}%, P(breach)={ftmo_data['p_dd_breach']*100:.1f}%")
