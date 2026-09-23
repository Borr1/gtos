#!/usr/bin/env python3
"""Combined MC — J46-J49 winner + S79 shipped + side_aware_everywhere stack.

Per the H-PM03 follow-up dispatch (Phase 2 master synthesis decision #5).
Extends H-PM04's MC framework by layering the CEO-standardized
`side_aware_everywhere` multiplier (LONG=0.5x, SHORT=1.0x universal) on top
of J46-J49 + S79.

Pre-registered prediction (frozen 2026-04-29 by combined-MC dispatch brief):

  * Combined P(pass FN Phase 1) > 0.95.
  * Combined P(bust HARD daily/total) < 0.015.
  * p99 MTM-DD <= 8% (internal cap).
  * Median days-to-pass <= 3 (improvement over H-PM04's J46+S79 alone).

Methodology (frozen, reproducible):
  1. Same cohort + same R-distribution reconstruction as H-PM04
     (J46-J49 winner per-instrument 4-mode mixture). N=5000 paths.
     Same seed=42 (delegated per-config seeds = 42*1000+i).
  2. Side ratio from A5 regime cohort: LONG = 304/335 = 90.7%, SHORT = 31/335
     = 9.3%. Each fill draws a side via Bernoulli on this ratio.
     (J46-J49 cohort doesn't include direction; A5 is the most representative
     per-side empirical density we have for the live regime.)
  3. Sizing transforms layered in this order:
       (a) per-instrument profile multiplier (S79 uniform_fn)
       (b) side multiplier (side_aware_everywhere: LONG=0.5x SHORT=1.0x)
       (c) cross-instrument correlation HALVE
  4. Stack alphas exactly as the production system would compose them at
     ship time:
       PnL = equity * (base_risk_pct/100) * profile_mult * side_mult
                     * (0.5 if correlation_halve else 1.0) * R
  5. Two density modes (S79-faithful + Realistic), same as H-PM04.
  6. Sensitivity: also test base=1.5% and base=2.5% with side_aware on/off.
  7. Reproduce H-PM04 baseline (no side-aware) on identical seed for delta
     attribution.

Outputs:
  * combined_mc_results.json — all configs, per-density, full MC stats.
  * combined_mc_j46_s79_side_aware.md — synthesis with verdict.

CRITICAL: $0 API. READ-ONLY. No production / src / config / canary modifications.
Pure-Python + numpy. Reproducible.

Author: Combined-MC dispatch (Claude Code Opus 4.7, max effort, subscription-only)
Date: 2026-04-29
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import numpy as np

# --- Paths ---
ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
THIS_DIR = Path(__file__).resolve().parent
TRADE_INDEX = ROOT / "knowledge_base" / "index" / "_trade_index.json"
A5_FILLS = ROOT / "research" / "decay_diagnostic" / "A5_regime_matrix" / "cands_with_regime.jsonl"

# --- FN Phase 1 constants (mirror H-PM04) ---
START_EQUITY = 100_000.0
PHASE1_TARGET_PCT = 8.0
PHASE1_DAILY_LOSS_PCT_HARD = 5.0
PHASE1_TOTAL_LOSS_PCT_HARD = 10.0
PHASE1_DAILY_LOSS_PCT_INTERNAL = 4.0
PHASE1_TOTAL_LOSS_PCT_INTERNAL = 8.0
DAYS_HORIZON = 30
N_MC_TRIALS = 5000

# --- S79 uniform_fn profile multipliers (mirror H-PM04) ---
PROFILE_UNIFORM_FN = {
    "XAUUSD": 0.5, "XAGUSD": 0.5,
    "USDJPY": 1.0, "GBPJPY": 1.0, "GBPUSD": 1.0,
    "NAS100": 0.25, "US30_cash": 1.0,
}

# --- Correlation groups (mirror H-PM04) ---
CORR_GROUPS = {
    "XAUUSD": {"XAGUSD"},
    "XAGUSD": {"XAUUSD"},
    "USDJPY": {"GBPJPY"},
    "GBPJPY": {"USDJPY", "GBPUSD"},
    "GBPUSD": {"GBPJPY"},
    "NAS100": {"US30_cash"},
    "US30_cash": {"NAS100"},
}

# --- J46-J49 winner per-instrument outcome stats (mirror H-PM04) ---
J46_J49_WINNER_STATS = {
    "GBPJPY":    {"n": 81,  "mean_r": 1.339, "wr": 0.815, "mean_dd_r": -0.427, "worst_dd_r": -1.125, "bars": 11.0},
    "GBPUSD":    {"n": 35,  "mean_r": 3.042, "wr": 0.886, "mean_dd_r": -0.337, "worst_dd_r": -2.265, "bars":  9.0},
    "US30_cash": {"n": 67,  "mean_r": 0.538, "wr": 0.597, "mean_dd_r": -0.625, "worst_dd_r": -1.513, "bars": 10.6},
    "USDJPY":    {"n": 76,  "mean_r": 0.573, "wr": 0.632, "mean_dd_r": -0.627, "worst_dd_r": -1.690, "bars": 10.2},
    "XAUUSD":    {"n": 62,  "mean_r": 0.859, "wr": 0.677, "mean_dd_r": -0.265, "worst_dd_r": -1.304, "bars": 11.6},
}

BASELINE_STATS = {
    "GBPJPY":    {"n": 81, "mean_r": 0.416, "wr": 0.333, "mean_dd_r": -0.467, "worst_dd_r": -1.000},
    "GBPUSD":    {"n": 35, "mean_r": 0.996, "wr": 0.743, "mean_dd_r": -0.337, "worst_dd_r": -1.000},
    "US30_cash": {"n": 67, "mean_r": 0.153, "wr": 0.224, "mean_dd_r": -0.625, "worst_dd_r": -1.000},
    "USDJPY":    {"n": 76, "mean_r": 0.300, "wr": 0.420, "mean_dd_r": -0.627, "worst_dd_r": -1.000},
    "XAUUSD":    {"n": 62, "mean_r": 0.476, "wr": 0.532, "mean_dd_r": -0.265, "worst_dd_r": -1.000},
}


# ---------------------------------------------------------------------------
# Cohort reconstruction (mirror H-PM04 exactly for delta attribution)
# ---------------------------------------------------------------------------

def reconstruct_r_distribution(stats, policy="winner", rng=None):
    """4-mode mixture calibrated to (mean_r, wr) per H-PM04 spec.
    Identical to H-PM04 for parity / delta attribution.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    n = stats["n"]
    mean_r = stats["mean_r"]
    wr = stats["wr"]

    if policy == "winner":
        big_mean_target = 4.5
        runner_mean_target = 1.5
        sl_value = -1.0
        be_neutral_mean = -0.05
        p_sl_share = 0.85

        n_win = int(round(n * wr))
        n_loss = n - n_win
        n_sl = int(round(n_loss * p_sl_share))
        n_ben = n_loss - n_sl

        if n_win > 0:
            loss_total = n_sl * sl_value + n_ben * be_neutral_mean
            target_win_total = n * mean_r - loss_total
            target_win_mean = target_win_total / n_win
            share = (target_win_mean - runner_mean_target) / (big_mean_target - runner_mean_target)
            share = max(0.0, min(1.0, share))
        else:
            share = 0.0

        n_big = int(round(n_win * share))
        n_run = n_win - n_big

        rs = []
        upper_bound = max(6.0, mean_r * 1.5 + 1.5)
        if n_big > 0:
            big_samples = rng.uniform(3.0, upper_bound, size=n_big)
            big_samples = big_samples + (big_mean_target - float(big_samples.mean()))
            big_samples = np.maximum(big_samples, 3.0)
            rs.extend(big_samples.tolist())
        if n_run > 0:
            run_samples = rng.uniform(0.0, 3.0, size=n_run)
            run_samples = run_samples + (runner_mean_target - float(run_samples.mean()))
            run_samples = np.clip(run_samples, 0.001, 3.0)
            rs.extend(run_samples.tolist())
        rs.extend([-1.0] * n_sl)
        if n_ben > 0:
            ben_samples = rng.uniform(-0.3, 0.0, size=n_ben)
            ben_samples = ben_samples + (be_neutral_mean - float(ben_samples.mean()))
            ben_samples = np.minimum(ben_samples, 0.0)
            rs.extend(ben_samples.tolist())
        arr = np.array(rs) if rs else np.array([0.0])
        delta = mean_r - float(arr.mean())
        if abs(delta) > 1e-6 and (n_big + n_run) > 0:
            total_pos = n_big + n_run
            shift_per = delta * n / total_pos
            for i in range(len(arr)):
                if arr[i] > 0:
                    arr[i] = arr[i] + shift_per
            for i in range(len(arr)):
                if 0 < arr[i] < 3.0:
                    arr[i] = max(0.001, arr[i])
                elif arr[i] >= 3.0:
                    arr[i] = max(3.0, arr[i])
        return arr

    elif policy == "baseline":
        win_value = 1.5
        if wr < 1:
            loss_avg = (mean_r - wr * win_value) / (1 - wr)
            if loss_avg > 0:
                win_mean_adj = win_value + (loss_avg / wr) * (1 - wr) if wr > 0 else win_value
                loss_avg = 0.0
                win_value = win_mean_adj
            elif loss_avg < -1.0:
                loss_avg = -1.0
                if wr > 0:
                    win_value = (mean_r - (1 - wr) * loss_avg) / wr
            p_sl_share = max(0.0, min(1.0, -loss_avg))
        else:
            loss_avg = 0.0
            p_sl_share = 0.0

        n_win = int(round(n * wr))
        n_loss = n - n_win
        n_sl = int(round(n_loss * p_sl_share))
        n_be = n_loss - n_sl

        rs = []
        rs.extend([float(win_value)] * n_win)
        rs.extend([-1.0] * n_sl)
        rs.extend([0.0] * n_be)
        arr = np.array(rs) if rs else np.array([0.0])
        delta = mean_r - float(arr.mean())
        if abs(delta) > 1e-6 and n_win > 0:
            shift = delta * n / n_win
            for i in range(len(arr)):
                if arr[i] > 0:
                    arr[i] = arr[i] + shift
        return arr

    raise ValueError(policy)


def build_cohort(stats_dict, rng, policy):
    return {sym: reconstruct_r_distribution(st, policy=policy, rng=rng)
            for sym, st in stats_dict.items()}


def is_correlated(sym_a, sym_b):
    return sym_b in CORR_GROUPS.get(sym_a, set())


def empirical_fills_per_day_distribution(inflation=321 / 129, include_zero_days=False):
    """Same as H-PM04 — read trade_index, scale, optionally pad with zero days."""
    with TRADE_INDEX.open("r", encoding="utf-8") as f:
        d = json.load(f)
    by_date = defaultdict(int)
    for t in d["trades"]:
        by_date[t["date"]] += 1
    counts = np.array(list(by_date.values()))

    out = []
    for c in counts:
        inflated = max(1, int(round(c * inflation)))
        out.append(inflated)
    out_arr = np.array(out)

    if include_zero_days:
        zero_days = max(0, 24 * 22 - len(out_arr))
        if zero_days > 0:
            out_arr = np.concatenate([out_arr, np.zeros(zero_days, dtype=int)])
    return counts, out_arr


def derive_a5_side_ratio() -> tuple[float, float]:
    """Derive LONG/SHORT ratio from A5 regime cohort."""
    if not A5_FILLS.exists():
        # Fallback to memory-documented ratio
        return 304.0 / 335.0, 31.0 / 335.0
    long_n = short_n = 0
    with A5_FILLS.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("outcome") not in ("WIN", "LOSS"):
                continue
            d = r.get("direction") or r.get("side")
            if d == "LONG":
                long_n += 1
            elif d == "SHORT":
                short_n += 1
    total = long_n + short_n
    if total == 0:
        return 304.0 / 335.0, 31.0 / 335.0
    return long_n / total, short_n / total


# ---------------------------------------------------------------------------
# Combined MC (extends H-PM04 with side multiplier)
# ---------------------------------------------------------------------------

def run_combined_mc(
    cohort,
    cap,
    base_risk_pct,
    profile_mults,
    fills_per_day,
    long_ratio,
    side_aware_long_mult=1.0,
    side_aware_short_mult=1.0,
    n_trials=N_MC_TRIALS,
    rng_seed=42,
    apply_correlation_halve=True,
    days_horizon=DAYS_HORIZON,
):
    """Bootstrap-MC the combined J46-J49 + S79 + side-aware stack.

    side_aware_long_mult / side_aware_short_mult: per-side multiplicative scalar.
      Status quo:        long=1.0, short=1.0
      side_aware_everywhere: long=0.5, short=1.0
    """
    rng = np.random.default_rng(rng_seed)

    syms = list(cohort.keys())
    sym_weights = np.array([len(cohort[s]) for s in syms], dtype=float)
    sym_weights = sym_weights / sym_weights.sum()

    n_pass = n_bust_int_total = n_bust_int_daily = 0
    n_bust_hard_total = n_bust_hard_daily = 0
    pass_days = []
    final_pnls = []
    max_dds = []
    n_max_dd_gt_4 = n_max_dd_gt_8 = 0

    for _trial in range(n_trials):
        equity = START_EQUITY
        peak = equity
        max_dd_pct_path = 0.0
        pass_day = None
        bust_int_total = bust_int_daily = False
        bust_hard_total = bust_hard_daily = False

        for day in range(days_horizon):
            n_today = int(rng.choice(fills_per_day))
            n_today = min(n_today, 8)
            if n_today == 0:
                continue

            sym_indices = rng.choice(len(syms), size=n_today, p=sym_weights, replace=True)
            sampled_syms = [syms[i] for i in sym_indices]
            # Sample side per fill from A5 ratio (independent of symbol)
            side_draws = rng.random(size=n_today)  # uniform [0,1); LONG iff < long_ratio

            day_pnl = 0.0
            day_open = []
            for i, sym in enumerate(sampled_syms):
                r = float(rng.choice(cohort[sym]))
                is_long = side_draws[i] < long_ratio

                profile_mult = profile_mults.get(sym, 1.0)
                side_mult = side_aware_long_mult if is_long else side_aware_short_mult
                risk_pct_eff = base_risk_pct * profile_mult * side_mult

                if apply_correlation_halve:
                    for prior_sym in day_open:
                        if is_correlated(sym, prior_sym):
                            risk_pct_eff *= 0.5
                            break

                risk_usd = equity * (risk_pct_eff / 100.0)
                pnl = r * risk_usd
                equity += pnl
                day_pnl += pnl
                day_open.append(sym)

                if equity > peak:
                    peak = equity
                dd_pct = (peak - equity) / peak * 100.0
                if dd_pct > max_dd_pct_path:
                    max_dd_pct_path = dd_pct

                if (START_EQUITY - equity) >= START_EQUITY * (PHASE1_TOTAL_LOSS_PCT_HARD / 100.0):
                    bust_hard_total = True
                    bust_int_total = True
                    break
                if not bust_int_total and (peak - equity) >= START_EQUITY * (PHASE1_TOTAL_LOSS_PCT_INTERNAL / 100.0):
                    bust_int_total = True
                if (equity - START_EQUITY) >= START_EQUITY * (PHASE1_TARGET_PCT / 100.0):
                    pass_day = day + 1
                    break

            if bust_hard_total or pass_day is not None:
                break

            if day_pnl <= -START_EQUITY * (PHASE1_DAILY_LOSS_PCT_HARD / 100.0):
                bust_hard_daily = True
                bust_int_daily = True
                break
            if not bust_int_daily and day_pnl <= -START_EQUITY * (PHASE1_DAILY_LOSS_PCT_INTERNAL / 100.0):
                bust_int_daily = True

        if pass_day is not None:
            n_pass += 1
            pass_days.append(pass_day)
        if bust_int_total:
            n_bust_int_total += 1
        if bust_int_daily:
            n_bust_int_daily += 1
        if bust_hard_total:
            n_bust_hard_total += 1
        if bust_hard_daily:
            n_bust_hard_daily += 1

        final_pnls.append((equity - START_EQUITY) / START_EQUITY * 100.0)
        max_dds.append(max_dd_pct_path)
        if max_dd_pct_path > 4.0:
            n_max_dd_gt_4 += 1
        if max_dd_pct_path > 8.0:
            n_max_dd_gt_8 += 1

    return {
        "p_pass": n_pass / n_trials,
        "p_bust_internal_total": n_bust_int_total / n_trials,
        "p_bust_internal_daily": n_bust_int_daily / n_trials,
        "p_bust_hard_total": n_bust_hard_total / n_trials,
        "p_bust_hard_daily": n_bust_hard_daily / n_trials,
        "p_max_dd_gt_4pct": n_max_dd_gt_4 / n_trials,
        "p_max_dd_gt_8pct": n_max_dd_gt_8 / n_trials,
        "median_days_to_pass": float(np.median(pass_days)) if pass_days else float("inf"),
        "mean_total_pnl_pct": float(np.mean(final_pnls)),
        "median_total_pnl_pct": float(np.median(final_pnls)),
        "mean_max_dd_pct": float(np.mean(max_dds)),
        "p95_max_dd_pct": float(np.percentile(max_dds, 95)),
        "p99_max_dd_pct": float(np.percentile(max_dds, 99)),
        "max_max_dd_pct": float(np.max(max_dds)) if max_dds else 0.0,
    }


def evaluate_combined_gates(mc):
    """Apply combined-MC pre-registered gates (tighter than H-PM04)."""
    p_bust_max = max(mc["p_bust_hard_total"], mc["p_bust_hard_daily"])
    return {
        "gate_a_p_pass_gt_0.95": mc["p_pass"] > 0.95,
        "gate_b_p_bust_hard_lt_0.015": p_bust_max < 0.015,
        "gate_c_p99_dd_le_8pct": mc["p99_max_dd_pct"] <= 8.0,
        "gate_d_median_days_le_3": mc["median_days_to_pass"] <= 3,
        "all_gates_pass": (
            mc["p_pass"] > 0.95
            and p_bust_max < 0.015
            and mc["p99_max_dd_pct"] <= 8.0
            and mc["median_days_to_pass"] <= 3
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-trials", type=int, default=N_MC_TRIALS, help="MC trials per config")
    ap.add_argument("--seed", type=int, default=42, help="RNG master seed")
    args = ap.parse_args()

    print("=" * 80, flush=True)
    print("Combined MC — J46-J49 winner + S79 shipped + side_aware_everywhere", flush=True)
    print(f"  N MC trials = {args.n_trials}", flush=True)
    print(f"  Master seed = {args.seed}", flush=True)
    print(f"  Pre-registered gates:", flush=True)
    print(f"    (a) P(pass FN) > 0.95", flush=True)
    print(f"    (b) P(bust HARD) < 0.015", flush=True)
    print(f"    (c) p99 MTM-DD <= 8%", flush=True)
    print(f"    (d) Median days-to-pass <= 3", flush=True)
    print("=" * 80, flush=True)

    rng_master = np.random.default_rng(args.seed)

    # Build cohorts (mirror H-PM04)
    cohort_winner = build_cohort(J46_J49_WINNER_STATS, rng_master, "winner")
    cohort_baseline = build_cohort(BASELINE_STATS, rng_master, "baseline")

    # Side ratio from A5
    long_ratio, short_ratio = derive_a5_side_ratio()
    print(f"\n[info] A5 side ratio: LONG={long_ratio:.4f}  SHORT={short_ratio:.4f}", flush=True)

    # Density distributions
    raw_counts, fpd_5inst_s79 = empirical_fills_per_day_distribution(inflation=321/129, include_zero_days=False)
    _, fpd_5inst_real = empirical_fills_per_day_distribution(inflation=321/129, include_zero_days=True)
    print(f"[info] S79-density (5-inst, no zeros): mean={fpd_5inst_s79.mean():.2f}, n_days={len(fpd_5inst_s79)}", flush=True)
    print(f"[info] Realistic density (with zeros): mean={fpd_5inst_real.mean():.2f}, n_days={len(fpd_5inst_real)}", flush=True)

    # ---- Configurations ----
    # Stack labels (decode at result):
    #   layer_a = J46_winner | baseline
    #   layer_b = S79 base   (1.0 / 1.5 / 2.0 / 2.5)
    #   layer_c = side_aware (off / everywhere)
    #   density = s79 | realistic
    configs: list[dict[str, Any]] = []

    # PRIMARY HEADLINE: full ship stack at base=2.0% on both densities
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"FULL_STACK J46+S79+side_aware (base=2.0%) [{density_label}]",
            "cohort": cohort_winner,
            "policy": "winner",
            "cap": 4,
            "base_risk": 2.0,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 0.5,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    # Sensitivity: base=1.5% backoff
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"FULL_STACK J46+S79+side_aware (base=1.5%) [{density_label}]",
            "cohort": cohort_winner,
            "policy": "winner",
            "cap": 4,
            "base_risk": 1.5,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 0.5,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    # Sensitivity: base=2.5% overshoot
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"FULL_STACK J46+S79+side_aware (base=2.5%) [{density_label}]",
            "cohort": cohort_winner,
            "policy": "winner",
            "cap": 4,
            "base_risk": 2.5,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 0.5,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    # Comparison: H-PM04 J46+S79 only (no side_aware) — rerun for delta attribution
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"J46+S79 only (no side_aware) (base=2.0%) [{density_label}]",
            "cohort": cohort_winner,
            "policy": "winner",
            "cap": 4,
            "base_risk": 2.0,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 1.0,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    # Status quo: baseline cohort + S79 + no side-aware (pre-J46 floor)
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"BASELINE J46-disabled+S79 (base=2.0%) [{density_label}]",
            "cohort": cohort_baseline,
            "policy": "baseline",
            "cap": 4,
            "base_risk": 2.0,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 1.0,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    # Bonus: side_aware ONLY (no J46-J49) on baseline cohort — isolates side-aware lift
    for density_label, fpd in [("s79_density", fpd_5inst_s79), ("realistic_density", fpd_5inst_real)]:
        configs.append({
            "name": f"BASELINE+S79+side_aware ONLY (base=2.0%) [{density_label}]",
            "cohort": cohort_baseline,
            "policy": "baseline",
            "cap": 4,
            "base_risk": 2.0,
            "profile_mults": PROFILE_UNIFORM_FN,
            "halve": True,
            "side_long_mult": 0.5,
            "side_short_mult": 1.0,
            "density": density_label,
            "fpd": fpd,
        })

    print(f"\nRunning {len(configs)} configs × {args.n_trials} MC trials each...\n", flush=True)

    config_results = []
    for i, cfg in enumerate(configs, 1):
        print(f"[{i:2d}/{len(configs)}] {cfg['name']}", flush=True)
        seed = args.seed * 1000 + i
        mc = run_combined_mc(
            cohort=cfg["cohort"],
            cap=cfg["cap"],
            base_risk_pct=cfg["base_risk"],
            profile_mults=cfg["profile_mults"],
            fills_per_day=cfg["fpd"],
            long_ratio=long_ratio,
            side_aware_long_mult=cfg["side_long_mult"],
            side_aware_short_mult=cfg["side_short_mult"],
            n_trials=args.n_trials,
            rng_seed=seed,
            apply_correlation_halve=cfg["halve"],
        )
        gates = evaluate_combined_gates(mc)
        result = {
            "config_name": cfg["name"],
            "cohort_policy": cfg["policy"],
            "cap": cfg["cap"],
            "base_risk_pct": cfg["base_risk"],
            "profile": "uniform_fn",
            "halve_enabled": cfg["halve"],
            "side_long_mult": cfg["side_long_mult"],
            "side_short_mult": cfg["side_short_mult"],
            "density": cfg["density"],
            "n_trials": args.n_trials,
            "seed": seed,
            **mc,
            "gates": gates,
        }
        config_results.append(result)
        p_bust_max = max(mc["p_bust_hard_total"], mc["p_bust_hard_daily"])
        print(f"        P(pass)={mc['p_pass']*100:5.1f}%   P(bust HARD)={p_bust_max*100:5.2f}%   "
              f"PnL%={mc['mean_total_pnl_pct']:+6.2f}   p99 DD={mc['p99_max_dd_pct']:5.2f}%   "
              f"med-days={mc['median_days_to_pass']}", flush=True)
        print(f"        Gates a/b/c/d: {gates['gate_a_p_pass_gt_0.95']}/{gates['gate_b_p_bust_hard_lt_0.015']}/"
              f"{gates['gate_c_p99_dd_le_8pct']}/{gates['gate_d_median_days_le_3']}   "
              f"ALL={gates['all_gates_pass']}", flush=True)

    # ---- Decision matrix ----
    def find_cfg(substr, density):
        for c in config_results:
            if substr in c["config_name"] and c["density"] == density:
                return c
        return None

    primary_s79 = find_cfg("FULL_STACK J46+S79+side_aware (base=2.0%)", "s79_density")
    primary_real = find_cfg("FULL_STACK J46+S79+side_aware (base=2.0%)", "realistic_density")
    backoff_s79 = find_cfg("FULL_STACK J46+S79+side_aware (base=1.5%)", "s79_density")
    backoff_real = find_cfg("FULL_STACK J46+S79+side_aware (base=1.5%)", "realistic_density")
    overshoot_s79 = find_cfg("FULL_STACK J46+S79+side_aware (base=2.5%)", "s79_density")
    overshoot_real = find_cfg("FULL_STACK J46+S79+side_aware (base=2.5%)", "realistic_density")
    j46s79_only_s79 = find_cfg("J46+S79 only (no side_aware)", "s79_density")
    j46s79_only_real = find_cfg("J46+S79 only (no side_aware)", "realistic_density")
    baseline_s79 = find_cfg("BASELINE J46-disabled+S79", "s79_density")
    baseline_real = find_cfg("BASELINE J46-disabled+S79", "realistic_density")
    side_only_s79 = find_cfg("BASELINE+S79+side_aware ONLY", "s79_density")
    side_only_real = find_cfg("BASELINE+S79+side_aware ONLY", "realistic_density")

    decision = {
        "PRIMARY_full_stack_s79_density": {
            "p_pass": primary_s79["p_pass"],
            "p_bust_hard_max": max(primary_s79["p_bust_hard_total"], primary_s79["p_bust_hard_daily"]),
            "p99_dd_pct": primary_s79["p99_max_dd_pct"],
            "median_days_to_pass": primary_s79["median_days_to_pass"],
            "mean_pnl_pct": primary_s79["mean_total_pnl_pct"],
            "all_gates_pass": primary_s79["gates"]["all_gates_pass"],
        },
        "PRIMARY_full_stack_realistic_density": {
            "p_pass": primary_real["p_pass"],
            "p_bust_hard_max": max(primary_real["p_bust_hard_total"], primary_real["p_bust_hard_daily"]),
            "p99_dd_pct": primary_real["p99_max_dd_pct"],
            "median_days_to_pass": primary_real["median_days_to_pass"],
            "mean_pnl_pct": primary_real["mean_total_pnl_pct"],
            "all_gates_pass": primary_real["gates"]["all_gates_pass"],
        },
        "compounding_lift_vs_h_pm04": {
            "s79_density": {
                "p_pass_delta": primary_s79["p_pass"] - j46s79_only_s79["p_pass"],
                "p_bust_hard_delta": (max(primary_s79["p_bust_hard_total"], primary_s79["p_bust_hard_daily"])
                                       - max(j46s79_only_s79["p_bust_hard_total"], j46s79_only_s79["p_bust_hard_daily"])),
                "p99_dd_delta": primary_s79["p99_max_dd_pct"] - j46s79_only_s79["p99_max_dd_pct"],
                "median_days_delta": primary_s79["median_days_to_pass"] - j46s79_only_s79["median_days_to_pass"],
            },
            "realistic_density": {
                "p_pass_delta": primary_real["p_pass"] - j46s79_only_real["p_pass"],
                "p_bust_hard_delta": (max(primary_real["p_bust_hard_total"], primary_real["p_bust_hard_daily"])
                                       - max(j46s79_only_real["p_bust_hard_total"], j46s79_only_real["p_bust_hard_daily"])),
                "p99_dd_delta": primary_real["p99_max_dd_pct"] - j46s79_only_real["p99_max_dd_pct"],
                "median_days_delta": primary_real["median_days_to_pass"] - j46s79_only_real["median_days_to_pass"],
            },
        },
        "lift_vs_status_quo_baseline": {
            "s79_density_p_pass_delta": primary_s79["p_pass"] - baseline_s79["p_pass"],
            "realistic_density_p_pass_delta": primary_real["p_pass"] - baseline_real["p_pass"],
        },
        "side_aware_isolated_lift": {
            "s79_density_p_pass_delta": side_only_s79["p_pass"] - baseline_s79["p_pass"],
            "realistic_density_p_pass_delta": side_only_real["p_pass"] - baseline_real["p_pass"],
        },
        "sensitivity": {
            "base_1.5_s79_p_pass": backoff_s79["p_pass"],
            "base_1.5_real_p_pass": backoff_real["p_pass"],
            "base_2.5_s79_p_pass": overshoot_s79["p_pass"],
            "base_2.5_s79_p_bust_hard": max(overshoot_s79["p_bust_hard_total"], overshoot_s79["p_bust_hard_daily"]),
            "base_2.5_real_p_pass": overshoot_real["p_pass"],
            "base_2.5_real_p_bust_hard": max(overshoot_real["p_bust_hard_total"], overshoot_real["p_bust_hard_daily"]),
        },
        "ship_stack_recommendation": (
            "SHIP_FULL_STACK_at_base=2.0%" if primary_s79["gates"]["all_gates_pass"] and primary_real["gates"]["all_gates_pass"]
            else (
                "SHIP_FULL_STACK_s79_only" if primary_s79["gates"]["all_gates_pass"]
                else (
                    "BACKOFF_to_1.5%" if (backoff_s79["gates"]["all_gates_pass"] and backoff_real["gates"]["all_gates_pass"])
                    else "INVESTIGATE_FAILURE"
                )
            )
        ),
    }

    out = {
        "produced": "2026-04-29",
        "agent": "combined_mc_dispatch",
        "task": "Combined J46-J49 + S79 + side_aware_everywhere ship-stack MC re-run",
        "methodology": {
            "cohort": "J46-J49 winner per-instrument R-distributions reconstructed from pareto_frontier.csv aggregate stats (n=321 fills, 5 instruments). Identical to H-PM04 for delta attribution.",
            "side_ratio_source": "A5 regime cohort fills (research/decay_diagnostic/A5_regime_matrix/cands_with_regime.jsonl); LONG/SHORT empirical ratio applied per fill via Bernoulli draw.",
            "long_ratio": long_ratio,
            "short_ratio": short_ratio,
            "sizing_stack": "PnL = equity * base_risk_pct/100 * profile_mult * side_mult * (correlation_halve) * R",
            "side_aware_profile": "side_aware_everywhere: LONG=0.5x SHORT=1.0x universal (CEO-standardized per memory project_side_aware_profile_standardized_long_0_5x_2026-04-29).",
            "n_trials": args.n_trials,
            "days_horizon": DAYS_HORIZON,
            "fns_phase_1_caps_internal": {
                "total_dd": f"{PHASE1_TOTAL_LOSS_PCT_INTERNAL}% (peak-to-trough)",
                "daily_dd": f"{PHASE1_DAILY_LOSS_PCT_INTERNAL}% (single calendar day)",
            },
            "fns_phase_1_caps_hard": {
                "total_dd": f"{PHASE1_TOTAL_LOSS_PCT_HARD}% (FN actual fail)",
                "daily_dd": f"{PHASE1_DAILY_LOSS_PCT_HARD}% (FN actual fail)",
            },
            "pre_registered_gates": {
                "gate_a": "P(pass FN) > 0.95 (tighter than H-PM04's 0.90)",
                "gate_b": "P(bust HARD) < 0.015 (tighter than H-PM04's 0.025)",
                "gate_c": "p99 MTM-DD <= 8% (internal cap)",
                "gate_d": "Median days-to-pass <= 3 (improvement over J46+S79 alone)",
            },
        },
        "configurations_tested": len(configs),
        "configurations": config_results,
        "decision": decision,
    }

    out_json = THIS_DIR / "combined_mc_results.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n[ok] wrote {out_json}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("COMBINED MC DECISION MATRIX", flush=True)
    print("=" * 80, flush=True)
    print(json.dumps(decision, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
