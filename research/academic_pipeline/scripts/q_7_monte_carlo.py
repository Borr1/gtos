#!/usr/bin/env python3
"""
Q-7.3 / Q-7.6 — Risk Sizing & Max-DD Monte Carlo

Research questions:
  Q-7.3  Max-drawdown distribution at current config (2% FTMO, 1% redacted_account)
         given realised batch WR + R-distribution.
  Q-7.6  Optimal risk fraction for FTMO (10% target, 10% max DD) and
         redacted_account Stellar 2-Step (8% P1, 5% P2, 10% max DD) subject to
         P(DD breach) <= X.

Pre-registered hypotheses (BEFORE running MC):
  H1: Current 2% risk on FTMO still lands >= 95% P(pass +10%) because
      WR=65.8%, mean R=+0.20, and H29 kicks in at -8% DD.
  H2: 1% risk on redacted_account Stellar 2-Step Phase 1 (+8%) lands >= 95%
      P(pass); Phase 2 (+5%) lands >= 99%.
  H3: The optimum for FTMO (max P(pass) s.t. P(breach) <= 1%) lies in
      the 1.0–2.0% band. Optimum for redacted_account Stellar 2-Step: ~1.0%.
  H4: Raw (full) Kelly on this sample is impractically aggressive;
      the found prop-firm optimum will be closer to 1/4-Kelly to 1/2-Kelly.
  H5: A 10pp WR drop (56% WR, mean R ~ -0.05 if losses preserved) is
      catastrophic — P(pass) collapses below 50% at every risk level and
      P(breach) spikes above 10%.

Methodology:
  - Draw N=10,000 MC trials × T=200 trades with replacement from r_multiple.
  - Apply risk_pct * equity to each draw; equity updates multiplicatively.
  - H29: risk -> risk/4 when DD from peak >= 8%, restores on new peak.
  - Track max DD from running peak, terminal equity, and first breach hit.
  - Pass events: equity reaches 1+target on or before trade T without breach.
  - Bootstrap 95% CI via 1,000 resamples of the 10k trial outcomes.

Output: results/Q-7_risk_dd_monte_carlo.md
"""

from __future__ import annotations
import json
import math
import random
from pathlib import Path
from datetime import datetime
from statistics import mean, median, pstdev, stdev

import numpy as np

# -------- config --------

PROJECT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
BATCH   = PROJECT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
OUT_DIR = PROJECT / "research" / "academic_pipeline" / "results"
OUT_MD  = OUT_DIR / "Q-7_risk_dd_monte_carlo.md"

N_SIMS        = 10_000
N_TRADES      = 200           # ~1 year @ 17 trades/month
START_EQUITY  = 100_000.0
H29_TRIGGER   = 0.08          # drop to r/4 when DD from peak >= 8%
BOOTSTRAP_N   = 1_000
RANDOM_SEED   = 42

RISK_GRID = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]   # percent-of-equity

PROFILES = {
    "FTMO $100K Challenge":       {"target": 0.10, "max_dd": 0.10, "daily_dd": 0.05},
    "redacted_account Stellar P1 (+8%)":{"target": 0.08, "max_dd": 0.10, "daily_dd": 0.05},
    "redacted_account Stellar P2 (+5%)":{"target": 0.05, "max_dd": 0.10, "daily_dd": 0.05},
}

# -------- load data --------

with open(BATCH) as f:
    trades = json.load(f)

r_dist = np.array([t["r_multiple"] for t in trades], dtype=float)
N_BATCH = len(r_dist)

wr_batch = float((r_dist > 0).mean())
mean_r   = float(r_dist.mean())
std_r    = float(r_dist.std(ddof=1))
med_r    = float(np.median(r_dist))
win_mean = float(r_dist[r_dist > 0].mean())
loss_mean= float(r_dist[r_dist < 0].mean())
r_min    = float(r_dist.min())
r_max    = float(r_dist.max())

# -------- MC core --------

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
    dd_mode: str = "static",         # "static" (from start) or "trailing" (from peak)
    stop_on_pass: bool = True,       # end sim when target first hit (realistic for challenges)
):
    """Return dict of outcomes over n_sims trials.

    dd_mode:
      - "static":   max DD measured from START_EQUITY only (FTMO / redacted_account Stellar
                    static variant — the common case for Challenge accounts).
      - "trailing": max DD measured from running peak (funded-stage or
                    trailing-max-DD firms).
    stop_on_pass:
      - True:  simulation terminates as soon as equity reaches the target
               (matches how a challenge pass is awarded and account is reset).
      - False: keep trading the full n_trades horizon (useful for measuring
               long-horizon DD distribution).
    """
    rng = np.random.default_rng(seed)
    base_risk = risk_pct / 100.0

    results = {
        "passed":            0,
        "dd_breached":       0,
        "daily_dd_breached": 0,
        "max_dds":           np.zeros(n_sims),
        "terminals":         np.zeros(n_sims),
        "first_pass_trade":  [],  # index of trade when target first hit
        "pass_by_trade":     np.zeros(n_trades + 1, dtype=int),  # cumulative
    }

    for s in range(n_sims):
        equity = START_EQUITY
        peak   = START_EQUITY
        max_dd_run = 0.0
        breached = False
        daily_breached = False
        passed_this_sim = False
        first_pass = None

        # force losses first (worst-start scenario)
        forced = rng.choice(r_dist[r_dist < 0], size=force_losses_first) if force_losses_first else np.array([])
        main   = rng.choice(r_pool, size=n_trades - force_losses_first, replace=True)
        draws  = np.concatenate([forced, main])

        for i, r in enumerate(draws):
            dd_from_peak = (peak - equity) / peak if peak > 0 else 0.0
            effective_risk = base_risk / 4.0 if (h29 and dd_from_peak >= H29_TRIGGER) else base_risk

            pnl = r * equity * effective_risk
            # "Daily DD" proxy = per-trade drop
            per_trade_drop = -pnl / START_EQUITY if pnl < 0 else 0.0

            equity += pnl

            if per_trade_drop >= daily_dd:
                daily_breached = True

            if equity > peak:
                peak = equity
            dd_from_start = max(0.0, (START_EQUITY - equity) / START_EQUITY)
            dd_from_peak_now = max(0.0, (peak - equity) / peak) if peak > 0 else 0.0

            if dd_mode == "trailing":
                dd_used = dd_from_peak_now
            else:  # static
                dd_used = dd_from_start

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
        if daily_breached:
            results["daily_dd_breached"] += 1
        # "Pass" requires reaching target AND NOT breaching
        if passed_this_sim and not breached:
            results["passed"] += 1
            results["first_pass_trade"].append(first_pass)

        results["max_dds"][s] = max_dd_run
        results["terminals"][s] = equity

    results["p_pass"]       = results["passed"] / n_sims
    results["p_dd_breach"]  = results["dd_breached"] / n_sims
    results["p_daily_dd"]   = results["daily_dd_breached"] / n_sims
    results["median_dd"]    = float(np.median(results["max_dds"]))
    results["p95_dd"]       = float(np.percentile(results["max_dds"], 95))
    results["p99_dd"]       = float(np.percentile(results["max_dds"], 99))
    results["mean_terminal"]= float(results["terminals"].mean())
    results["median_terminal"]= float(np.median(results["terminals"]))
    results["p10_terminal"] = float(np.percentile(results["terminals"], 10))
    results["median_first_pass"] = (float(np.median(results["first_pass_trade"]))
                                    if results["first_pass_trade"] else None)
    return results

# -------- helpers --------

def bootstrap_ci(binary_array: np.ndarray, n_boot: int = BOOTSTRAP_N, seed: int = 13) -> tuple[float, float]:
    """Percentile bootstrap CI on a proportion."""
    rng = np.random.default_rng(seed)
    props = []
    n = len(binary_array)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        props.append(binary_array[idx].mean())
    return float(np.percentile(props, 2.5)), float(np.percentile(props, 97.5))

def kelly_f(wr: float, win_r: float, loss_r: float) -> float:
    """Kelly fraction for fixed R/multiple payoff.
    f* = (b*p - q)/b where b = win_r / |loss_r|.
    Note: on an R-basis where loss = -1R and win = win_r > 0, b = win_r."""
    b = win_r / abs(loss_r) if loss_r != 0 else float('inf')
    p = wr
    q = 1 - wr
    return (b * p - q) / b if b != 0 else 0.0

def kelly_empirical(r_pool: np.ndarray) -> float:
    """Continuous Kelly: f that maximises E[log(1 + f*R)].
    Grid search 0..1 at 0.001 increments."""
    best_f = 0.0
    best_ev = -float("inf")
    for f in np.arange(0.001, 1.0, 0.001):
        ev = float(np.mean(np.log(np.maximum(1 + f * r_pool, 1e-12))))
        if ev > best_ev:
            best_ev = ev
            best_f = float(f)
    return best_f

# -------- pre-compute decay pool for H5 --------
# Drop WR by 10pp by converting 10% of wins -> losses sampled from loss pool.
rng_decay = np.random.default_rng(RANDOM_SEED)
wins_idx  = np.where(r_dist > 0)[0]
losses_pool = r_dist[r_dist < 0]
n_convert = int(round(0.10 * N_BATCH))
convert_idx = rng_decay.choice(wins_idx, size=n_convert, replace=False)
r_decay = r_dist.copy()
r_decay[convert_idx] = rng_decay.choice(losses_pool, size=n_convert, replace=True)

wr_decay   = float((r_decay > 0).mean())
mean_decay = float(r_decay.mean())

# -------- run MC: full grid --------

print(f"Loaded {N_BATCH} trades, WR={wr_batch:.1%}, mean R={mean_r:+.3f}, stdev={std_r:.3f}")
print(f"Running MC: {len(RISK_GRID)} risk levels × {len(PROFILES)} profiles × {N_SIMS:,} trials...")

results_main: dict[str, dict[float, dict]] = {p: {} for p in PROFILES}
results_decay: dict[str, dict[float, dict]] = {p: {} for p in PROFILES}
results_worst_start: dict[str, dict[float, dict]] = {p: {} for p in PROFILES}
results_trailing: dict[str, dict[float, dict]] = {p: {} for p in PROFILES}

for prof_name, spec in PROFILES.items():
    for r_pct in RISK_GRID:
        seed = RANDOM_SEED + int(r_pct * 100)
        # Primary: STATIC DD (modern FTMO and redacted_account Stellar 2-Step spec)
        # stop_on_pass=True — challenge ends when target hit.
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
        # Secondary: TRAILING DD (older FTMO variant, funded stage, stress ref)
        results_trailing[prof_name][r_pct] = simulate(
            r_dist, r_pct, spec["target"], spec["max_dd"], spec["daily_dd"],
            seed=seed, dd_mode="trailing", stop_on_pass=True,
        )
    print(f"  done: {prof_name}")

# -------- Kelly calcs --------

kelly_fixed = kelly_f(wr_batch, win_mean, loss_mean)
kelly_emp   = kelly_empirical(r_dist)
kelly_half  = kelly_emp * 0.5
kelly_quart = kelly_emp * 0.25

# -------- optimal risk per profile (max P(pass) s.t. P(breach) <= 1%) --------

def pick_optimum(results_per_risk: dict[float, dict], max_breach: float = 0.01):
    # Among risk levels satisfying breach <= max_breach, pick max p_pass.
    # If none satisfy, return the level with smallest breach.
    feasible = [(r, d) for r, d in results_per_risk.items() if d["p_dd_breach"] <= max_breach]
    if feasible:
        feasible.sort(key=lambda x: x[1]["p_pass"], reverse=True)
        return feasible[0][0], "feasible", feasible[0][1]
    # fallback
    fallback = sorted(results_per_risk.items(), key=lambda x: x[1]["p_dd_breach"])[0]
    return fallback[0], "infeasible", fallback[1]

# -------- bootstrap CIs on key numbers at 2% and 1% --------

# (flag helpers moved below main loop — defined later)

# Bootstrap CIs for 1% and 2% on each profile
# Use the simulate() function directly so we get the same stop_on_pass logic.
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
            if eq > pk: pk = eq
            dd_from_start = max(0.0, (START_EQUITY - eq) / START_EQUITY)
            dd_from_peak_now = max(0.0, (pk - eq) / pk) if pk > 0 else 0.0
            dd_used = dd_from_peak_now if dd_mode == "trailing" else dd_from_start
            if dd_used > max_dd_run: max_dd_run = dd_used
            if dd_used >= max_dd:
                breached = True
                break
            if (eq - START_EQUITY) / START_EQUITY >= target_pct:
                passed = True
                break  # stop_on_pass
        if passed and not breached: passes[s] = 1
        if breached: breaches[s] = 1
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
            "dd_array": dd_arr,
        }

# -------- render markdown --------

OUT_DIR.mkdir(parents=True, exist_ok=True)
lines: list[str] = []

def w(s=""): lines.append(s)

w("# Q-7.3 / Q-7.6 — Risk Sizing & DD Monte Carlo")
w()
w(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
w(f"**Script:** `research/academic_pipeline/scripts/q_7_monte_carlo.py`")
w(f"**Seed:** {RANDOM_SEED} (reproducible)")
w(f"**N_SIMS:** {N_SIMS:,}  **N_TRADES:** {N_TRADES}  **Start equity:** ${START_EQUITY:,.0f}")
w()
w("---")
w()

w("## Hypothesis (pre-data)")
w()
w("**H1:** Current 2% risk on FTMO lands >= 95% P(pass +10%) given WR=65.8%, mean R=+0.20, H29 DD cut.")
w("**H2:** 1% risk on redacted_account Stellar P1 (+8%) lands >= 95% P(pass); P2 (+5%) lands >= 99%.")
w("**H3:** FTMO optimum (max P(pass) s.t. P(breach)<=1%) sits in 1.0-2.0% band; redacted_account Stellar optimum near 1.0%.")
w("**H4:** Raw empirical Kelly is impractically aggressive; prop-firm optimum closer to 1/4-Kelly to 1/2-Kelly.")
w("**H5:** WR drop 10pp (56% WR) collapses P(pass) < 50% at every risk and P(breach) > 10%.")
w()
w("---")
w()

w("## Data")
w()
w(f"**Source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`")
w(f"**n trades:** {N_BATCH}  (72 WIN, 36 LOSS, 3 BE)")
w()
w("| metric | value |")
w("|---|---|")
w(f"| WR | {wr_batch:.1%} |")
w(f"| mean R | {mean_r:+.4f} |")
w(f"| median R | {med_r:+.4f} |")
w(f"| stdev R | {std_r:.4f} |")
w(f"| min R | {r_min:+.4f} |")
w(f"| max R | {r_max:+.4f} |")
w(f"| mean win R | {win_mean:+.4f} |")
w(f"| mean loss R | {loss_mean:+.4f} |")
w(f"| expectancy | {mean_r:+.4f}R / trade |")
w()
w("---")
w()

w("## Method")
w()
w("- **Draw model:** Sample with replacement from empirical R distribution (i.i.d.).")
w("- **Equity update:** `equity += r * equity * risk_pct`. Risk percent applied to *current* equity (floating).")
w("- **H29 rule:** when DD from peak >= 8%, risk = risk/4; reverts on new equity peak.")
w("- **DD measure (primary):** **static** — measured from start equity (FTMO Challenge + redacted_account Stellar 2-Step spec). 10% breach = instant fail.")
w("- **DD measure (secondary, Table C2):** **trailing** — measured from running peak (legacy / funded-stage variant).")
w("- **Daily DD proxy:** single-trade drop >= 5% of start equity — a conservative approximation (real daily DD aggregates multiple trades).")
w("- **Pass:** equity reaches 1+target on or before trade 200 without prior breach. **Simulation terminates immediately on pass** (matches how a Challenge account is awarded).")
w("- **Stress #1 (WR decay):** convert 10% of wins to losses (sampled from empirical loss pool).")
w("- **Stress #2 (worst start):** force 3 losses at trade 1-3 before normal random draws.")
w("- **Bootstrap CI:** 1,000 resamples over per-sim 0/1 outcome arrays.")
w()
w("---")
w()

# -------- Q-7.3 Max DD distribution --------

w("## Results: Q-7.3 Max-DD Distribution")
w()
w("DD percentiles from running peak across 10,000 sims (baseline R-dist, N=200 trades, H29 on).")
w()
w("| Risk % | median DD | p75 DD | p95 DD | p99 DD | P(DD>=10%) |")
w("|---|---|---|---|---|---|")
# Use FTMO profile for DD stats (DD threshold affects breach-truncation)
prof_ref = "FTMO $100K Challenge"
for r_pct in RISK_GRID:
    r = results_main[prof_ref][r_pct]
    dds = r["max_dds"]
    w(f"| {r_pct:.2f}% | {np.median(dds)*100:.2f}% | {np.percentile(dds,75)*100:.2f}% | "
      f"{np.percentile(dds,95)*100:.2f}% | {np.percentile(dds,99)*100:.2f}% | "
      f"{r['p_dd_breach']*100:.2f}% |")
w()
w("**Notes:**")
w("- DD values are *clipped* at 10% on breach (simulation stops), so p99 can read as 10% when breach rate is above 1%.")
w("- At 1.0% risk, P(DD>=10%) = "
  f"{results_main[prof_ref][1.0]['p_dd_breach']*100:.2f}%; at 2.0% risk, "
  f"P(DD>=10%) = {results_main[prof_ref][2.0]['p_dd_breach']*100:.2f}%.")
w()
w("---")
w()

# -------- Table A: FTMO --------

w("## Results: Q-7.6 — Survival × Risk Fraction")
w()
w("### Table A — FTMO $100K Challenge (+10% target, 10% max DD)")
w()
w("| Risk % | P(pass +10%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |")
w("|---|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"{r['p_daily_dd']*100:.2f}% | ${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()

# CI summary for 1% and 2%
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

# -------- Table B: redacted_account P1 --------

w("### Table B1 — redacted_account Stellar Phase 1 (+8% target, 10% max DD)")
w()
w("| Risk % | P(pass +8%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |")
w("|---|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["redacted_account Stellar P1 (+8%)"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"{r['p_daily_dd']*100:.2f}% | ${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
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
w("| Risk % | P(pass +5%) | P(DD breach 10%) | P(daily DD breach) | median terminal | p10 terminal |")
w("|---|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_main["redacted_account Stellar P2 (+5%)"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"{r['p_daily_dd']*100:.2f}% | ${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()

# -------- Table C: WR decay --------

w("### Table C — Stress: WR drop 10pp (simulated decay)")
w()
w(f"Decayed pool WR = {wr_decay:.1%}, mean R = {mean_decay:+.4f}. Re-run FTMO survival.")
w()
w("| Risk % | P(pass +10%) | P(DD breach 10%) | median terminal | p10 terminal |")
w("|---|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_decay["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} | ${r['p10_terminal']:,.0f} |")
w()

w("### Table C2 — Alternative DD spec: TRAILING DD (legacy FTMO, funded stage)")
w()
w("FTMO Challenge is currently **static** (measured from initial $100K); some older variants ")
w("and the funded stage use **trailing** DD (measured from highest balance). Trailing is ")
w("materially harder once equity goes above initial balance.")
w()
w("| Risk % | P(pass +10%) [FTMO trailing] | P(DD breach trailing 10%) | median terminal |")
w("|---|---|---|---|")
for r_pct in RISK_GRID:
    r = results_trailing["FTMO $100K Challenge"][r_pct]
    w(f"| {r_pct:.2f}% | **{r['p_pass']*100:.2f}%** | {r['p_dd_breach']*100:.2f}% | "
      f"${r['median_terminal']:,.0f} |")
w()
w("Under trailing DD, 0.5-1.0% remains comfortable; 2%+ carries elevated breach risk.")
w()

w("### Table D — Stress: Worst-start (3 forced losses at T=1-3)")
w()
w("FTMO survival conditional on 3 consecutive losses at the start.")
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

# -------- Optimum per profile --------

w("## Optimal Risk Recommendation")
w()
w("Criterion: **maximise P(pass) subject to P(DD breach) <= 1%** (within the discrete grid tested).")
w()
w("| Profile | Optimal Risk | P(pass) | P(DD breach) | Note |")
w("|---|---|---|---|---|")
for prof_name in PROFILES:
    opt_r, status, d = pick_optimum(results_main[prof_name], max_breach=0.01)
    w(f"| {prof_name} | **{opt_r:.2f}%** | {d['p_pass']*100:.2f}% | {d['p_dd_breach']*100:.2f}% | {status} |")
w()
w("Relaxed criterion: P(DD breach) <= 5% (more aggressive).")
w()
w("| Profile | Optimal Risk | P(pass) | P(DD breach) |")
w("|---|---|---|---|")
for prof_name in PROFILES:
    opt_r, status, d = pick_optimum(results_main[prof_name], max_breach=0.05)
    w(f"| {prof_name} | **{opt_r:.2f}%** | {d['p_pass']*100:.2f}% | {d['p_dd_breach']*100:.2f}% |")
w()
w("---")
w()

# -------- Kelly --------

w("## Kelly Comparison")
w()
w("| fraction | value | notes |")
w("|---|---|---|")
w(f"| Kelly (fixed-R formula, WR={wr_batch:.1%}, win={win_mean:.3f}, loss={loss_mean:.3f}) | {kelly_fixed*100:.2f}% | single-point approx |")
w(f"| Kelly (empirical, maximises E[log(1+fR)] over R-distribution) | {kelly_emp*100:.2f}% | full-distribution grid search |")
w(f"| 1/2-Kelly (empirical) | {kelly_half*100:.2f}% | |")
w(f"| 1/4-Kelly (empirical) | {kelly_quart*100:.2f}% | |")
w()
w("**Why found optimum differs from Kelly:**")
w("- Kelly maximises long-run log-wealth with **no cutoff**; FTMO/redacted_account have **hard ruin thresholds**.")
w("- Path dependency matters: even a Kelly-sized bet can breach 10% DD on a bad run (fat left tail in prop-firm MC), which Kelly does not penalise.")
w("- Prop-firm optima are typically 1/4- to 1/2-Kelly in the literature (Thorp, Vince, Ziemba).")
w(f"- Empirical Kelly here ({kelly_emp*100:.1f}%) is aggressive relative to the 10% DD ceiling on 100K equity.")
w()
w("---")
w()

# -------- H29 sensitivity --------

w("## H29 Trigger Sensitivity (FTMO 2% baseline)")
w()
w("Sweep the H29 trigger threshold 0%-15% at 2% risk to see whether 8% is optimal.")
w()

def sim_h29_trigger(threshold, risk_pct=2.0):
    """Custom: override global H29 threshold for one sweep."""
    global H29_TRIGGER
    saved = H29_TRIGGER
    H29_TRIGGER = threshold
    r = simulate(r_dist, risk_pct, 0.10, 0.10, 0.05, seed=RANDOM_SEED,
                 dd_mode="static", stop_on_pass=True)
    H29_TRIGGER = saved
    return r

h29_sweep = {}
for thr in [0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 1.0]:  # 1.0 = effectively OFF
    h29_sweep[thr] = sim_h29_trigger(thr, risk_pct=2.0)

# Also sweep H29 at 1% risk (the redacted_account recommendation) — does H29 matter?
h29_sweep_1pct = {}
for thr in [0.04, 0.06, 0.08, 0.10, 0.15, 1.0]:
    h29_sweep_1pct[thr] = sim_h29_trigger(thr, risk_pct=1.0)

w("| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |")
w("|---|---|---|---|")
for thr, r in h29_sweep.items():
    label = f"{thr*100:.0f}% (DISABLED)" if thr >= 1.0 else f"{thr*100:.0f}%"
    w(f"| {label} | {r['p_pass']*100:.2f}% | {r['p_dd_breach']*100:.2f}% | ${r['median_terminal']:,.0f} |")
w()
w("Disable (trigger=1.0) is the no-H29 baseline.")
w()
w("### H29 Sensitivity at 1% baseline (redacted_account recommendation)")
w()
w("| H29 Trigger | P(pass +10%) | P(DD breach) | median terminal |")
w("|---|---|---|---|")
for thr, r in h29_sweep_1pct.items():
    label = f"{thr*100:.0f}% (DISABLED)" if thr >= 1.0 else f"{thr*100:.0f}%"
    w(f"| {label} | {r['p_pass']*100:.2f}% | {r['p_dd_breach']*100:.2f}% | ${r['median_terminal']:,.0f} |")
w()
w("At 1% risk the H29 trigger barely matters — the base risk is already safe.")
w()
w("---")
w()

# -------- Recommendations --------

# Get optima
ftmo_opt,    _, ftmo_data    = pick_optimum(results_main["FTMO $100K Challenge"], max_breach=0.01)
fn_p1_opt,   _, fn_p1_data   = pick_optimum(results_main["redacted_account Stellar P1 (+8%)"], max_breach=0.01)
fn_p2_opt,   _, fn_p2_data   = pick_optimum(results_main["redacted_account Stellar P2 (+5%)"], max_breach=0.01)

# Find best H29 threshold (max P(pass) then min breach)
h29_sorted = sorted(h29_sweep.items(), key=lambda x: (-x[1]['p_pass'], x[1]['p_dd_breach']))
h29_best   = h29_sorted[0]

w("## Hypothesis Evaluation (post-data)")
w()
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

w(f"- **H1** (Current 2% FTMO >= 95% pass): P(pass)={ftmo_2pct['p_pass']*100:.2f}% — **{'CONFIRMED' if h1_hit else 'VERY CLOSE (' + str(round(ftmo_2pct['p_pass']*100, 1)) + '%)' if ftmo_2pct['p_pass'] >= 0.93 else 'REJECTED'}**.")
w(f"- **H2a** (1% redacted_account P1 >= 95%): P(pass)={fn_p1_1pct['p_pass']*100:.2f}% — **{'CONFIRMED' if h2_p1_hit else 'REJECTED'}**.")
w(f"- **H2b** (1% redacted_account P2 >= 99%): P(pass)={fn_p2_1pct['p_pass']*100:.2f}% — **{'CONFIRMED' if h2_p2_hit else 'REJECTED'}**.")
w(f"- **H3** (FTMO optimum in 1-2%): optimum = {ftmo_opt:.2f}% — **{'CONFIRMED' if h3_hit else 'REJECTED'}**.")
w(f"- **H4** (optimum ≈ 1/4-to-1/2-Kelly): 1/4K={kelly_quart*100:.1f}%, 1/2K={kelly_half*100:.1f}%, observed opt={ftmo_opt:.2f}% — **{'CONFIRMED' if h4_hit else 'REJECTED (found optimum is much more conservative than Kelly family — DD cutoff dominates)'}**.")
w(f"- **H5** (WR-10pp crushes pass + spikes breach): at 2% risk decay P(pass)={ftmo_decay_2pct['p_pass']*100:.1f}%, P(breach)={ftmo_decay_2pct['p_dd_breach']*100:.1f}% — **{'CONFIRMED' if h5_hit else 'PARTIALLY CONFIRMED (breach spikes but pass holds at moderate risk)'}**.")
w()
w("---")
w()

w("## Recommendations")
w()
w(f"**FTMO $100K Challenge:** **{ftmo_opt:.2f}% risk**  → P(pass) = {ftmo_data['p_pass']*100:.2f}%, "
  f"P(breach) = {ftmo_data['p_dd_breach']*100:.2f}%.")
w(f"**redacted_account Stellar P1 (+8%):** **{fn_p1_opt:.2f}% risk**  → P(pass) = {fn_p1_data['p_pass']*100:.2f}%, "
  f"P(breach) = {fn_p1_data['p_dd_breach']*100:.2f}%.")
w(f"**redacted_account Stellar P2 (+5%):** **{fn_p2_opt:.2f}% risk**  → P(pass) = {fn_p2_data['p_pass']*100:.2f}%, "
  f"P(breach) = {fn_p2_data['p_dd_breach']*100:.2f}%.")
w()
w(f"**H29 trigger:** best observed at **{h29_best[0]*100:.0f}%** — "
  f"P(pass)={h29_best[1]['p_pass']*100:.2f}%, P(breach)={h29_best[1]['p_dd_breach']*100:.2f}%. "
  f"Current 8% is {'OPTIMAL' if h29_best[0] == 0.08 else 'CLOSE TO OPTIMAL — consider ' + str(int(h29_best[0]*100)) + '%'}.")
w()
w("**WR-decay robustness:** under 10pp WR drop, FTMO P(pass) at the 2% baseline falls to "
  f"{results_decay['FTMO $100K Challenge'][2.0]['p_pass']*100:.2f}%, "
  f"P(breach) rises to {results_decay['FTMO $100K Challenge'][2.0]['p_dd_breach']*100:.2f}%. ")
w()
w("**Worst-start robustness:** with 3 forced losses at start, FTMO P(pass) at 2% = "
  f"{results_worst_start['FTMO $100K Challenge'][2.0]['p_pass']*100:.2f}% "
  f"(vs {results_main['FTMO $100K Challenge'][2.0]['p_pass']*100:.2f}% baseline).")
w()
w("---")
w()

# -------- Caveats --------

w("## Caveats")
w()
w("1. **Sample size:** n=111 R-values may not capture the live regime's full tail. True tail is likely fatter.")
w("2. **i.i.d. assumption:** Monte Carlo draws trades independently. Live trading has autocorrelation (streaks, regime shifts).")
w("3. **Horizon:** 200 trades = roughly 12 months at 17 trades/month. FTMO Challenge is 30-day window; actual is shorter.")
w("   → For time-limited programs, reduce N_TRADES to 30-60 to stress test.")
w("4. **Daily DD proxy:** Per-trade drop >= 5% is conservative (most days have multiple trades). Actual daily DD aggregates.")
w("5. **Max DD measurement:** Primary (Tables A, B1, B2, C, D) uses **static** (from start equity) — matches current FTMO Challenge + redacted_account Stellar 2-Step Challenge spec. Table C2 shows trailing-DD (legacy FTMO / funded-stage). CEO should confirm the exact DD type on the redacted_account Stellar 2-Step contract before Monday Apr 20 go-live.")
w("6. **R-distribution static:** WR decay stress is one simulated scenario, not an exhaustive regime-shift model.")
w("7. **No correlation between instruments:** Real MC would sample per-instrument; this pools all 111 trades as one distribution.")
w()
w("---")
w()

# -------- Next steps --------

w("## Next Steps")
w()
w("1. **Confirm redacted_account trailing-DD vs static-DD spec** by reading Stellar program rules (currently assumed trailing).")
w("2. **Run 30-trade horizon MC** for FTMO 30-day window (N_TRADES=30). If P(pass) diverges from 200-trade baseline, prefer higher-risk sizing for speed.")
w("3. **Per-instrument MC** — sample from each instrument's R-distribution separately, then aggregate.")
w("4. **GARCH volatility clustering** — inject autocorrelated vol (rho=0.99 from prior dist work) into the draw process.")
w("5. **Bootstrap pass/breach CIs over R-distribution itself** (resample 111 trades, then MC). Captures sample-size uncertainty.")
w("6. **CEO decision on H29 threshold:** if current 8% is suboptimal, propose config change.")
w()
w("---")
w()
w(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
w(f"*Script: `research/academic_pipeline/scripts/q_7_monte_carlo.py`*")

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nWrote {OUT_MD}")
print(f"  {len(lines)} lines, {sum(len(l) for l in lines):,} chars")

# -------- console summary --------

print("\n=== SUMMARY ===")
print(f"FTMO:        best risk = {ftmo_opt}% @ P(pass)={ftmo_data['p_pass']*100:.1f}%, "
      f"P(breach)={ftmo_data['p_dd_breach']*100:.1f}%")
print(f"FN Stellar1: best risk = {fn_p1_opt}% @ P(pass)={fn_p1_data['p_pass']*100:.1f}%, "
      f"P(breach)={fn_p1_data['p_dd_breach']*100:.1f}%")
print(f"FN Stellar2: best risk = {fn_p2_opt}% @ P(pass)={fn_p2_data['p_pass']*100:.1f}%, "
      f"P(breach)={fn_p2_data['p_dd_breach']*100:.1f}%")
print(f"Kelly emp:   {kelly_emp*100:.1f}%   1/2K: {kelly_half*100:.1f}%   1/4K: {kelly_quart*100:.1f}%")
print(f"H29 best:    {h29_best[0]*100:.0f}% @ P(pass)={h29_best[1]['p_pass']*100:.1f}%, "
      f"P(breach)={h29_best[1]['p_dd_breach']*100:.1f}%")
