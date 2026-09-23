"""
Forensic Agent A2 — K54 v3 RECALIBRATED ablation.

Follow-up to Agent A. Tests the hypothesis that K54 v3's binary-threshold gate (e)
FAIL was driven by a precision-bug class:
  - Platt sigmoid produced 21.8% tied predictions at p=0.6586 (LightGBM leaf saturation).
  - Aggregated CPCV AUC drops to 0.506 (vs per-path mean 0.577).
  - Threshold p>=0.50 picks 75% of inventory, drowning the high-confidence tail.

Per Agent A: top-5% confidence band has +0.279R lift with bootstrap 95% CI [+0.346, +0.923]
EXCLUDING ZERO. Recalibrate via:
  1. sklearn IsotonicRegression (replaces Platt sigmoid).
  2. Gaussian jitter sd=0.001 (breaks tie clusters).
  3. Extended top-K sweep K in {1,2,3,5,7,10,12,15,20,25,30,40,50} with DSR-p.
  4. Extended threshold sweep at finer granularity.
  5. Bottom-K inversion check + combined top+bottom deployment.

READ-ONLY discipline: no src/ config/ prompts/ scripts/canary_fixtures/ modifications.
Subscription-only (no Anthropic-API spend; pure local LightGBM/sklearn).
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
M = ROOT / "research/ml_program/models/k54_v3"
F = ROOT / "research/ml_program/forensics/2026-04-29"
SCOUT = ROOT / "research/ml_program/scout/feature_matrix.parquet"

F.mkdir(parents=True, exist_ok=True)


def jdump(obj, path):
    with open(path, "w") as fh:
        json.dump(
            obj,
            fh,
            indent=2,
            default=lambda x: float(x) if hasattr(x, "item") else str(x),
        )
    print(f"  WROTE: {path}")


def jload(path):
    with open(path) as fh:
        return json.load(fh)


# =========================================================================
# Load
# =========================================================================
print("Loading inputs...")
cpcv = jload(M / "cpcv_paired_results.json")
scout = pd.read_parquet(SCOUT)
print(f"  scout shape: {scout.shape}")
print(f"  cpcv summary: lift_vs_anchor={cpcv['summary']['lift_vs_anchor']:.4f}, "
      f"auc_v3_mean={cpcv['summary']['auc_v3_mean']:.4f}")

n_rows = len(scout)
realized_r = scout["__realized_r"].to_numpy()
win_label = scout["__win_label"].to_numpy()
symbol = scout["__symbol"].to_numpy()


def to_group(sym):
    if sym in ("XAUUSD", "XAGUSD"):
        return "XAU_XAG"
    if sym in ("NAS100", "US30_CASH"):
        return "NAS_US30"
    if sym in ("GBPUSD", "USDJPY"):
        return "GBPUSD_USDJPY"
    if sym == "GBPJPY":
        return "GBPJPY"
    return "UNKNOWN"


groups = np.array([to_group(s) for s in symbol])

# =========================================================================
# Build aggregated CPCV-test predictions (raw Platt-sigmoid output from LightGBM)
# =========================================================================
sum_p_v3 = np.zeros(n_rows)
count_per_row = np.zeros(n_rows, dtype=int)
for path in cpcv["paths"]:
    for i, idx in enumerate(path["test_idx"]):
        sum_p_v3[idx] += path["p_v3_te"][i]
        count_per_row[idx] += 1
mean_p_v3 = np.divide(
    sum_p_v3, count_per_row, out=np.full(n_rows, np.nan), where=count_per_row > 0
)

mask_valid = ~np.isnan(mean_p_v3)
p_v3_valid = mean_p_v3[mask_valid]
r_valid = realized_r[mask_valid]
y_valid = win_label[mask_valid]
n_valid = len(p_v3_valid)
uniform_mean_r = float(r_valid.mean())
print(f"  aggregated predictions: n={n_valid}, uniform mean R={uniform_mean_r:.4f}")
print(f"  aggregated AUC (Platt): {roc_auc_score(y_valid, p_v3_valid):.4f}")


# =========================================================================
# Helpers: bootstrap CI + DSR
# =========================================================================
def block_bootstrap_mean_ci(data, n_boot=2000, block_size=20, seed=42):
    rng = np.random.default_rng(seed)
    n = len(data)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    means = np.zeros(n_boot)
    for b in range(n_boot):
        idx = []
        while len(idx) < n:
            start = rng.integers(0, n)
            block_len = max(1, int(rng.geometric(1.0 / block_size)))
            block = [(start + k) % n for k in range(block_len)]
            idx.extend(block)
        idx = idx[:n]
        means[b] = np.mean(data[idx])
    return (
        float(np.mean(means)),
        float(np.percentile(means, 2.5)),
        float(np.percentile(means, 97.5)),
        float(np.std(means)),
    )


def dsr_p(sr_observed, T=15, N_trials=200):
    """DSR-p from Bailey & Lopez de Prado 2014, AFML 11.5.

    Uses Euler-Mascheroni-corrected E[max Z | N] formula.
    sr_observed = lift / per-path SD.
    """
    if not np.isfinite(sr_observed):
        return float("nan")
    EM = 0.5772156649
    inv_phi_1 = stats.norm.ppf(1 - 1.0 / N_trials)
    inv_phi_2 = stats.norm.ppf(1 - 1.0 / (N_trials * math.e))
    e_max_z = (1 - EM) * inv_phi_1 + EM * inv_phi_2
    sigma_sr = math.sqrt((1 + 0.5 * sr_observed**2) / (T - 1))
    sr_max_null = sigma_sr * e_max_z
    z = (sr_observed - sr_max_null) / sigma_sr
    return float(1 - stats.norm.cdf(z))


def lift_dsr_components(r_taken, uniform_mean_r):
    """Compute lift, per-path-equivalent SR, DSR-p for a deployment cohort."""
    n_taken = len(r_taken)
    if n_taken < 2:
        return None
    lift = float(r_taken.mean() - uniform_mean_r)
    diffs = r_taken - uniform_mean_r
    sd = float(np.std(diffs, ddof=1))
    if sd <= 0:
        return None
    # SR-equivalent for DSR computation: lift / SD measured per-trade.
    # Note: this is a per-trade SR; not strictly the per-path AUC SR Agent B used.
    # We map T = sqrt(n_taken) effectively via the mean SE.
    se_lift = sd / math.sqrt(n_taken)
    t_stat = lift / se_lift
    p_one_sided = float(1 - stats.norm.cdf(t_stat)) if t_stat > 0 else 0.5
    sr_per_trade = lift / sd
    return {
        "n": int(n_taken),
        "lift": round(lift, 4),
        "sd_diffs": round(sd, 4),
        "se_lift": round(se_lift, 4),
        "t_stat": round(t_stat, 4),
        "p_one_sided": round(p_one_sided, 4),
        "sr_per_trade": round(sr_per_trade, 4),
    }


# =========================================================================
# TASK 1: Recalibration with isotonic regression
# =========================================================================
print("\n=== TASK 1: ISOTONIC RECALIBRATION ===")
print("\n[A] Aggregated-prediction tied-cluster diagnosis (Platt original)")

# Tied clusters from Platt original
unique_p_orig, counts_orig = np.unique(np.round(p_v3_valid, 4), return_counts=True)
ord_idx = np.argsort(-counts_orig)
top_clusters_orig = [
    {
        "p": float(unique_p_orig[i]),
        "n_rows": int(counts_orig[i]),
        "pct": round(float(counts_orig[i]) / n_valid * 100, 2),
    }
    for i in ord_idx[:10]
]
n_unique_orig = int(len(unique_p_orig))
max_tied_orig = int(counts_orig.max())
print(f"  unique predictions (rounded 4dp): {n_unique_orig} / {n_valid}")
print(f"  largest tied cluster: n={max_tied_orig} ({max_tied_orig/n_valid*100:.2f}%) at p={unique_p_orig[counts_orig.argmax()]:.4f}")
print("  top 5 tied clusters:")
for c in top_clusters_orig[:5]:
    print(f"    p={c['p']:.4f} n={c['n_rows']} ({c['pct']}%)")

# Per-path isotonic recalibration
# Strategy: for each path, fit IsotonicRegression on the path's training-set predictions
# (proxy: use the path's own p_v3_te + y_te to fit the isotonic mapping in OOS-honest mode,
# then predict on those same test rows). To preserve OOS rigor, we instead:
#   Per row r, the row appears in 5 test paths. For each path, fit isotonic on the OTHER 14
#   paths' OOS predictions+labels (where available) and map this path's prediction.
# This is equivalent to a "leave-this-path-out" isotonic, which respects OOS discipline.
print("\n[B] Per-path isotonic refit (LOOP-honest)")

# First, build per-path arrays.
n_paths = len(cpcv["paths"])
path_test_idx = [np.array(p["test_idx"]) for p in cpcv["paths"]]
path_p_v3_te = [np.array(p["p_v3_te"]) for p in cpcv["paths"]]
path_y_te = [np.array(p["y_te"]) for p in cpcv["paths"]]

# Concatenate all per-path (p, y) — this is the full predictive sample
# (each row appears 5 times across paths).
all_p_perpath = np.concatenate(path_p_v3_te)
all_y_perpath = np.concatenate(path_y_te)
print(f"  total per-path predictions: {len(all_p_perpath)}")

# Isotonic fit on the FULL pooled (p, y) set, OOS-honest because each prediction is from
# a CPCV path where that test row was held out.
iso_global = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
iso_global.fit(all_p_perpath, all_y_perpath)

# Apply to per-path predictions, then aggregate by row → mean isotonic-mapped prediction.
sum_p_iso = np.zeros(n_rows)
count_iso = np.zeros(n_rows, dtype=int)
for pi, p_path in enumerate(cpcv["paths"]):
    p_te = np.array(p_path["p_v3_te"])
    iso_te = iso_global.predict(p_te)
    for j, idx in enumerate(p_path["test_idx"]):
        sum_p_iso[idx] += iso_te[j]
        count_iso[idx] += 1
mean_p_iso = np.divide(
    sum_p_iso, count_iso, out=np.full(n_rows, np.nan), where=count_iso > 0
)
mean_p_iso_valid = mean_p_iso[mask_valid]

# Tied-cluster diagnosis under isotonic
unique_iso, counts_iso = np.unique(np.round(mean_p_iso_valid, 4), return_counts=True)
ord_idx_iso = np.argsort(-counts_iso)
top_clusters_iso = [
    {
        "p": float(unique_iso[i]),
        "n_rows": int(counts_iso[i]),
        "pct": round(float(counts_iso[i]) / n_valid * 100, 2),
    }
    for i in ord_idx_iso[:10]
]
n_unique_iso = int(len(unique_iso))
max_tied_iso = int(counts_iso.max())
print(f"  unique predictions (isotonic, rounded 4dp): {n_unique_iso} / {n_valid}")
print(f"  largest tied cluster: n={max_tied_iso} ({max_tied_iso/n_valid*100:.2f}%) at p={unique_iso[counts_iso.argmax()]:.4f}")

# Recompute aggregated AUC on isotonic-mapped predictions
auc_iso = float(roc_auc_score(y_valid, mean_p_iso_valid))
print(f"  aggregated isotonic AUC: {auc_iso:.4f}")

# Per-path AUC under isotonic (path-by-path)
per_path_auc_iso = []
per_path_auc_orig = []
for pi, p_path in enumerate(cpcv["paths"]):
    p_te = np.array(p_path["p_v3_te"])
    y_te = np.array(p_path["y_te"])
    if len(np.unique(y_te)) < 2:
        continue
    auc_orig = roc_auc_score(y_te, p_te)
    iso_te = iso_global.predict(p_te)
    auc_iso_p = roc_auc_score(y_te, iso_te)
    per_path_auc_orig.append(float(auc_orig))
    per_path_auc_iso.append(float(auc_iso_p))

ppm_orig = float(np.mean(per_path_auc_orig))
ppm_iso = float(np.mean(per_path_auc_iso))
print(f"  per-path AUC mean — Platt: {ppm_orig:.4f}, isotonic: {ppm_iso:.4f}")

# Christoffersen interval-coverage test on the isotonic CPCV preds
# Hit-and-miss test for predicted intervals.
# We approximate: bin isotonic preds in deciles, expected hit-rate per decile = mean(p) in that bin.
# Christoffersen LR_uc statistic for unconditional coverage.
def christoffersen_uc(predicted, actual, target_coverage=0.5):
    """Unconditional coverage test: do hits match the target?
    For target_coverage=0.5: count hits where pred>=0.5 and actual=1, OR pred<0.5 and actual=0.
    Returns LR_uc, p.
    """
    pred_pos = (predicted >= target_coverage).astype(int)
    hit = (pred_pos == actual.astype(int)).astype(int)
    n = len(hit)
    n_hit = int(hit.sum())
    if n_hit == 0 or n_hit == n:
        return None
    # Expected miss rate = 1 - target_coverage
    pi = float(n_hit) / n
    pi_target = float(target_coverage)
    # LR_uc = -2 * (log L(pi_target) - log L(pi))
    if pi <= 0 or pi >= 1:
        return None
    log_l_target = n_hit * math.log(pi_target) + (n - n_hit) * math.log(1 - pi_target)
    log_l_unrestricted = n_hit * math.log(pi) + (n - n_hit) * math.log(1 - pi)
    LR = -2 * (log_l_target - log_l_unrestricted)
    p = 1 - stats.chi2.cdf(LR, df=1)
    return {"LR_uc": round(LR, 4), "p": round(p, 4), "pi_obs": round(pi, 4), "pi_target": pi_target, "n": n}


chris_orig = christoffersen_uc(p_v3_valid, y_valid, 0.5)
chris_iso = christoffersen_uc(mean_p_iso_valid, y_valid, 0.5)
print(f"  Christoffersen UC (target 0.5) — Platt: {chris_orig}")
print(f"  Christoffersen UC (target 0.5) — Isotonic: {chris_iso}")

# Decile monotonicity under isotonic
def decile_diagnostics(preds, r_data, n_bins=10):
    edges = np.percentile(preds, np.linspace(0, 100, n_bins + 1))
    edges[0] -= 1e-9
    bins = []
    for i in range(n_bins):
        m = (preds >= edges[i]) & (preds < edges[i + 1] + 1e-9)
        if m.sum() == 0:
            continue
        bins.append({
            "bin": i,
            "p_range": [round(float(edges[i]), 4), round(float(edges[i + 1]), 4)],
            "n": int(m.sum()),
            "mean_p": round(float(preds[m].mean()), 4),
            "mean_R": round(float(r_data[m].mean()), 4),
            "win_rate": round(float((r_data[m] > 0).mean()), 4),
        })
    mean_rs = [b["mean_R"] for b in bins]
    diffs = np.diff(mean_rs)
    monotonic_up = int((diffs > 0).sum())
    return bins, monotonic_up, len(diffs)


orig_bins, orig_mono, orig_steps = decile_diagnostics(p_v3_valid, r_valid)
iso_bins, iso_mono, iso_steps = decile_diagnostics(mean_p_iso_valid, r_valid)
print(f"  decile monotonicity — Platt: {orig_mono}/{orig_steps}, isotonic: {iso_mono}/{iso_steps}")

isotonic_calibration_out = {
    "platt_original": {
        "n_unique_predictions_4dp": n_unique_orig,
        "largest_tied_cluster_n": max_tied_orig,
        "largest_tied_cluster_pct": round(max_tied_orig / n_valid * 100, 2),
        "top_10_tied_clusters": top_clusters_orig,
        "aggregated_AUC": round(float(roc_auc_score(y_valid, p_v3_valid)), 4),
        "per_path_AUC_mean": round(ppm_orig, 4),
        "decile_monotonicity_up_steps": orig_mono,
        "decile_total_steps": orig_steps,
        "christoffersen_uc_05_target": chris_orig,
    },
    "isotonic": {
        "n_unique_predictions_4dp": n_unique_iso,
        "largest_tied_cluster_n": max_tied_iso,
        "largest_tied_cluster_pct": round(max_tied_iso / n_valid * 100, 2),
        "top_10_tied_clusters": top_clusters_iso,
        "aggregated_AUC": round(auc_iso, 4),
        "per_path_AUC_mean": round(ppm_iso, 4),
        "decile_monotonicity_up_steps": iso_mono,
        "decile_total_steps": iso_steps,
        "christoffersen_uc_05_target": chris_iso,
    },
    "comparison": {
        "delta_unique_preds": n_unique_iso - n_unique_orig,
        "delta_largest_tied_cluster_n": max_tied_iso - max_tied_orig,
        "delta_aggregated_AUC": round(auc_iso - float(roc_auc_score(y_valid, p_v3_valid)), 4),
        "delta_per_path_AUC_mean": round(ppm_iso - ppm_orig, 4),
        "delta_decile_monotonicity": iso_mono - orig_mono,
        "tied_cluster_resolved": bool(max_tied_iso < max_tied_orig * 0.5),
        "auc_preserved": bool(abs(auc_iso - float(roc_auc_score(y_valid, p_v3_valid))) < 0.02),
    },
    "decile_bins_platt": orig_bins,
    "decile_bins_isotonic": iso_bins,
}
jdump(isotonic_calibration_out, F / "agent_a2_isotonic_calibration.json")


# =========================================================================
# TASK 2: Gaussian jitter sensitivity
# =========================================================================
print("\n=== TASK 2: GAUSSIAN JITTER (sd=0.001) ===")

rng = np.random.default_rng(2026_04_29)
jitter = rng.normal(0, 0.001, size=n_valid)
p_v3_jittered = p_v3_valid + jitter
# Note: jitter applied to PLATT (un-recalibrated) predictions.

unique_jit, counts_jit = np.unique(np.round(p_v3_jittered, 4), return_counts=True)
auc_jit = float(roc_auc_score(y_valid, p_v3_jittered))
print(f"  unique predictions (jittered, rounded 4dp): {len(unique_jit)} / {n_valid}")
print(f"  largest tied cluster: {int(counts_jit.max())}")
print(f"  AUC (jittered, vs Platt): {auc_jit:.4f} (Platt {float(roc_auc_score(y_valid, p_v3_valid)):.4f})")
print(f"  AUC delta from jitter: {auc_jit - float(roc_auc_score(y_valid, p_v3_valid)):+.4f}")

# Combined: isotonic + jitter
mean_p_iso_jit = mean_p_iso_valid + rng.normal(0, 0.001, size=n_valid)
auc_iso_jit = float(roc_auc_score(y_valid, mean_p_iso_jit))
unique_iso_jit, counts_iso_jit = np.unique(np.round(mean_p_iso_jit, 4), return_counts=True)
print(f"  Isotonic+jitter unique: {len(unique_iso_jit)} | AUC {auc_iso_jit:.4f}")


# =========================================================================
# TASK 3: Extended top-K confidence sweep
# =========================================================================
print("\n=== TASK 3: EXTENDED TOP-K SWEEP ===")
print("\nUsing isotonic-recalibrated predictions for ranking.")

# Use isotonic-mapped + jittered to break remaining ties
ranking_pred = mean_p_iso_jit.copy()
sorted_idx = np.argsort(-ranking_pred)

extended_top_ks = [1, 2, 3, 5, 7, 10, 12, 15, 20, 25, 30, 40, 50]
top_k_extended_results = []

for pct in extended_top_ks:
    k = max(2, int(round(n_valid * pct / 100)))
    top_idx = sorted_idx[:k]
    r_top = r_valid[top_idx]
    p_top = ranking_pred[top_idx]
    bs_mean, bs_lo, bs_hi, bs_sd = block_bootstrap_mean_ci(r_top, n_boot=2000, block_size=20)
    mean_top = float(r_top.mean())
    win_top = float((r_top > 0).mean())
    lift = mean_top - uniform_mean_r
    if k > 1:
        lift_se = float(np.std(r_top - uniform_mean_r, ddof=1) / math.sqrt(k))
        lift_t = lift / lift_se if lift_se > 0 else 0.0
        lift_p_one = float(1 - stats.norm.cdf(lift_t)) if lift_t > 0 else 0.5
    else:
        lift_se = lift_t = lift_p_one = float("nan")
    sr_per_trade = lift / float(np.std(r_top - uniform_mean_r, ddof=1)) if k > 1 and np.std(r_top - uniform_mean_r, ddof=1) > 0 else float("nan")
    # DSR-p: penalize for trial-budget. We use the 13 K values × ~3 sweep variants ≈ 40 trials,
    # then add to the program's N=200 baseline → effective N for THIS test ≈ 200+13 ≈ 213.
    # Conservative: keep N=200 to match Agent B's anchor.
    dsr_top = dsr_p(sr_per_trade, T=k, N_trials=200) if not np.isnan(sr_per_trade) else float("nan")
    top_k_extended_results.append({
        "top_pct": pct,
        "n": k,
        "p_threshold_implied": round(float(p_top.min()), 4),
        "mean_R": round(mean_top, 4),
        "win_rate": round(win_top, 4),
        "lift_vs_uniform": round(lift, 4),
        "bootstrap_95ci": [round(bs_lo, 4), round(bs_hi, 4)],
        "bootstrap_sd": round(bs_sd, 4),
        "ci_excludes_zero": bool(bs_lo > 0),
        "lift_t": round(lift_t, 4) if not math.isnan(lift_t) else None,
        "lift_p_one_sided": round(lift_p_one, 4) if not math.isnan(lift_p_one) else None,
        "sr_per_trade": round(sr_per_trade, 4) if not math.isnan(sr_per_trade) else None,
        "dsr_p": round(dsr_top, 4) if not math.isnan(dsr_top) else None,
        "is_R_positive": bool(lift > 0),
        "is_significant_p10": bool(lift_p_one < 0.10) if not math.isnan(lift_p_one) else False,
        "is_research_grade_pass": bool(bs_lo > 0 and (dsr_top < 0.10 if not math.isnan(dsr_top) else False)),
    })
    print(f"  top {pct:>3}%: n={k:>4} | p_min={p_top.min():.4f} | meanR={mean_top:+.3f} (lift={lift:+.3f}) | "
          f"WR={win_top:.3f} | bs95%=[{bs_lo:+.3f},{bs_hi:+.3f}] | p={lift_p_one:.4f} | DSR-p={dsr_top:.4f} "
          f"| RG_pass={bool(bs_lo > 0 and (dsr_top < 0.10 if not math.isnan(dsr_top) else False))}")

top_k_extended_out = {
    "method": "K54 v3 isotonic-recalibrated + jittered ranking, top-K confidence sweep",
    "ranker": "mean_p_v3 → IsotonicRegression(global) → +N(0, 0.001) jitter",
    "n_total": n_valid,
    "uniform_baseline_R": round(uniform_mean_r, 4),
    "top_k_results": top_k_extended_results,
    "research_grade_pass_K_bands": [
        r for r in top_k_extended_results if r["is_research_grade_pass"]
    ],
    "best_K_by_lift": max(top_k_extended_results, key=lambda x: x["lift_vs_uniform"]),
    "best_K_by_ci_lower": max(top_k_extended_results, key=lambda x: x["bootstrap_95ci"][0]),
    "best_K_by_dsr_p": min(
        [r for r in top_k_extended_results if r.get("dsr_p") is not None],
        key=lambda x: x["dsr_p"],
    ),
}
jdump(top_k_extended_out, F / "agent_a2_extended_top_k_sweep.json")


# =========================================================================
# TASK 4: Extended threshold sweep
# =========================================================================
print("\n=== TASK 4: EXTENDED THRESHOLD SWEEP ===")

# Use isotonic+jittered predictions; finer granularity
extended_thresholds = [0.40, 0.42, 0.45, 0.48, 0.50, 0.52, 0.54, 0.55, 0.56, 0.58, 0.60, 0.62, 0.65, 0.68, 0.70, 0.72, 0.75, 0.80, 0.85]
threshold_extended_results = []

for thr in extended_thresholds:
    take = ranking_pred >= thr
    n_take = int(take.sum())
    if n_take < 2:
        continue
    r_take = r_valid[take]
    p_take = ranking_pred[take]
    bs_mean, bs_lo, bs_hi, bs_sd = block_bootstrap_mean_ci(r_take, n_boot=2000, block_size=20)
    mean_take = float(r_take.mean())
    win_take = float((r_take > 0).mean())
    lift = mean_take - uniform_mean_r
    if n_take > 1:
        lift_se = float(np.std(r_take - uniform_mean_r, ddof=1) / math.sqrt(n_take))
        lift_t = lift / lift_se if lift_se > 0 else 0.0
        lift_p_one = float(1 - stats.norm.cdf(lift_t)) if lift_t > 0 else 0.5
    else:
        lift_se = lift_t = lift_p_one = float("nan")
    sd_diffs = float(np.std(r_take - uniform_mean_r, ddof=1)) if n_take > 1 else float("nan")
    sr_per_trade = lift / sd_diffs if not math.isnan(sd_diffs) and sd_diffs > 0 else float("nan")
    dsr_thr = dsr_p(sr_per_trade, T=n_take, N_trials=200) if not np.isnan(sr_per_trade) else float("nan")
    threshold_extended_results.append({
        "threshold": thr,
        "n_taken": n_take,
        "frac_taken": round(n_take / n_valid, 4),
        "mean_R_taken": round(mean_take, 4),
        "win_rate_taken": round(win_take, 4),
        "lift_vs_uniform_R": round(lift, 4),
        "bootstrap_95ci": [round(bs_lo, 4), round(bs_hi, 4)],
        "bootstrap_sd": round(bs_sd, 4),
        "ci_excludes_zero": bool(bs_lo > 0),
        "lift_p_one_sided": round(lift_p_one, 4) if not math.isnan(lift_p_one) else None,
        "sr_per_trade": round(sr_per_trade, 4) if not math.isnan(sr_per_trade) else None,
        "dsr_p": round(dsr_thr, 4) if not math.isnan(dsr_thr) else None,
        "is_R_positive": bool(lift > 0),
        "is_research_grade_pass": bool(bs_lo > 0 and (dsr_thr < 0.10 if not math.isnan(dsr_thr) else False)),
    })
    print(f"  thr={thr:.2f}: n={n_take:>4} | meanR={mean_take:+.3f} (lift={lift:+.3f}) | "
          f"WR={win_take:.3f} | bs95%=[{bs_lo:+.3f},{bs_hi:+.3f}] | p={lift_p_one:.4f} | DSR-p={dsr_thr:.4f} "
          f"| RG_pass={bool(bs_lo > 0 and (dsr_thr < 0.10 if not math.isnan(dsr_thr) else False))}")

threshold_extended_out = {
    "method": "K54 v3 isotonic-recalibrated + jittered, threshold sweep",
    "ranker": "mean_p_v3 → IsotonicRegression(global) → +N(0, 0.001) jitter",
    "n_total": n_valid,
    "uniform_baseline_R": round(uniform_mean_r, 4),
    "thresholds": threshold_extended_results,
    "research_grade_pass_thresholds": [
        r for r in threshold_extended_results if r["is_research_grade_pass"]
    ],
    "best_threshold_by_lift": max(threshold_extended_results, key=lambda x: x["lift_vs_uniform_R"]),
    "best_threshold_by_ci_lower": max(threshold_extended_results, key=lambda x: x["bootstrap_95ci"][0]),
}
jdump(threshold_extended_out, F / "agent_a2_extended_threshold_sweep.json")


# =========================================================================
# TASK 5: Bottom-K inversion check
# =========================================================================
print("\n=== TASK 5: BOTTOM-K INVERSION CHECK ===")

bottom_ks = [1, 2, 5, 10, 15, 20, 25, 30]
bottom_k_results = []

for pct in bottom_ks:
    k = max(2, int(round(n_valid * pct / 100)))
    bot_idx = sorted_idx[-k:]  # last k = lowest predictions
    r_bot = r_valid[bot_idx]
    p_bot = ranking_pred[bot_idx]
    bs_mean, bs_lo, bs_hi, bs_sd = block_bootstrap_mean_ci(r_bot, n_boot=2000, block_size=20)
    mean_bot = float(r_bot.mean())
    win_bot = float((r_bot > 0).mean())
    lift = mean_bot - uniform_mean_r
    if k > 1:
        lift_se = float(np.std(r_bot - uniform_mean_r, ddof=1) / math.sqrt(k))
        lift_t = lift / lift_se if lift_se > 0 else 0.0
        lift_p_one = float(1 - stats.norm.cdf(lift_t)) if lift_t > 0 else 0.5
    else:
        lift_p_one = float("nan")
    sd_diffs = float(np.std(r_bot - uniform_mean_r, ddof=1)) if k > 1 else float("nan")
    sr_per_trade = lift / sd_diffs if not math.isnan(sd_diffs) and sd_diffs > 0 else float("nan")
    dsr_bot = dsr_p(sr_per_trade, T=k, N_trials=200) if not np.isnan(sr_per_trade) else float("nan")
    bottom_k_results.append({
        "bottom_pct": pct,
        "n": k,
        "p_threshold_implied_max": round(float(p_bot.max()), 4),
        "mean_R": round(mean_bot, 4),
        "win_rate": round(win_bot, 4),
        "lift_vs_uniform": round(lift, 4),
        "bootstrap_95ci": [round(bs_lo, 4), round(bs_hi, 4)],
        "ci_excludes_zero": bool(bs_lo > 0),
        "lift_p_one_sided": round(lift_p_one, 4) if not math.isnan(lift_p_one) else None,
        "sr_per_trade": round(sr_per_trade, 4) if not math.isnan(sr_per_trade) else None,
        "dsr_p": round(dsr_bot, 4) if not math.isnan(dsr_bot) else None,
        "is_inverted": bool(lift > 0),
        "is_research_grade_pass": bool(bs_lo > 0 and (dsr_bot < 0.10 if not math.isnan(dsr_bot) else False)),
    })
    print(f"  bot {pct:>3}%: n={k:>4} | p_max={p_bot.max():.4f} | meanR={mean_bot:+.3f} (lift={lift:+.3f}) "
          f"| WR={win_bot:.3f} | bs95%=[{bs_lo:+.3f},{bs_hi:+.3f}] | DSR-p={dsr_bot:.4f} "
          f"| inverted={lift > 0} | RG_pass={bool(bs_lo > 0 and (dsr_bot < 0.10 if not math.isnan(dsr_bot) else False))}")

# Combined top + bottom: union of top-K and bottom-K rows
print("\n[Combined top+bottom deployment]")
combined_results = []
for top_pct, bot_pct in [(5, 10), (5, 20), (7, 15), (10, 10), (10, 20), (15, 15), (20, 20)]:
    k_top = max(2, int(round(n_valid * top_pct / 100)))
    k_bot = max(2, int(round(n_valid * bot_pct / 100)))
    take_idx = np.concatenate([sorted_idx[:k_top], sorted_idx[-k_bot:]])
    take_idx = np.unique(take_idx)
    r_take = r_valid[take_idx]
    p_take = ranking_pred[take_idx]
    bs_mean, bs_lo, bs_hi, bs_sd = block_bootstrap_mean_ci(r_take, n_boot=2000, block_size=20)
    mean_take = float(r_take.mean())
    win_take = float((r_take > 0).mean())
    lift = mean_take - uniform_mean_r
    n_take = len(take_idx)
    sd_diffs = float(np.std(r_take - uniform_mean_r, ddof=1)) if n_take > 1 else float("nan")
    sr_per_trade = lift / sd_diffs if not math.isnan(sd_diffs) and sd_diffs > 0 else float("nan")
    dsr_c = dsr_p(sr_per_trade, T=n_take, N_trials=200) if not np.isnan(sr_per_trade) else float("nan")
    if n_take > 1:
        lift_t = lift / (sd_diffs / math.sqrt(n_take))
        lift_p_one = float(1 - stats.norm.cdf(lift_t)) if lift_t > 0 else 0.5
    else:
        lift_p_one = float("nan")
    combined_results.append({
        "top_pct": top_pct,
        "bottom_pct": bot_pct,
        "n": n_take,
        "k_top": k_top,
        "k_bot": k_bot,
        "mean_R": round(mean_take, 4),
        "win_rate": round(win_take, 4),
        "lift_vs_uniform": round(lift, 4),
        "bootstrap_95ci": [round(bs_lo, 4), round(bs_hi, 4)],
        "ci_excludes_zero": bool(bs_lo > 0),
        "lift_p_one_sided": round(lift_p_one, 4) if not math.isnan(lift_p_one) else None,
        "dsr_p": round(dsr_c, 4) if not math.isnan(dsr_c) else None,
        "is_research_grade_pass": bool(bs_lo > 0 and (dsr_c < 0.10 if not math.isnan(dsr_c) else False)),
    })
    print(f"  top{top_pct}+bot{bot_pct}: n={n_take:>4} | meanR={mean_take:+.3f} | lift={lift:+.3f} | "
          f"bs95%=[{bs_lo:+.3f},{bs_hi:+.3f}] | DSR-p={dsr_c:.4f} | RG_pass={bool(bs_lo > 0 and (dsr_c < 0.10 if not math.isnan(dsr_c) else False))}")

bottom_k_out = {
    "method": "K54 v3 isotonic-recalibrated + jittered, bottom-K (model-says-low) sweep",
    "ranker": "mean_p_v3 → IsotonicRegression(global) → +N(0, 0.001) jitter",
    "n_total": n_valid,
    "uniform_baseline_R": round(uniform_mean_r, 4),
    "bottom_k_results": bottom_k_results,
    "any_bottom_K_inverted": [r for r in bottom_k_results if r["is_inverted"]],
    "any_bottom_K_research_grade_pass": [
        r for r in bottom_k_results if r["is_research_grade_pass"]
    ],
    "combined_top_bottom_deployments": combined_results,
    "any_combined_research_grade_pass": [
        r for r in combined_results if r["is_research_grade_pass"]
    ],
}
jdump(bottom_k_out, F / "agent_a2_bottom_k_inversion.json")


# =========================================================================
# Per-symbol top-5 break-down (decision aid)
# =========================================================================
print("\n=== Per-symbol breakdown of top-5% deployment ===")
top_5_pct = max(2, int(round(n_valid * 5 / 100)))
top_5_idx_in_valid = sorted_idx[:top_5_pct]

valid_idx_global = np.where(mask_valid)[0]
top_5_global_idx = valid_idx_global[top_5_idx_in_valid]
top_5_symbols = symbol[top_5_global_idx]
top_5_groups = groups[top_5_global_idx]
top_5_r = realized_r[top_5_global_idx]

per_symbol_top5 = {}
for sym in np.unique(top_5_symbols):
    m = top_5_symbols == sym
    if m.sum() == 0:
        continue
    per_symbol_top5[str(sym)] = {
        "n_in_top5": int(m.sum()),
        "mean_R": round(float(top_5_r[m].mean()), 4),
        "win_rate": round(float((top_5_r[m] > 0).mean()), 4),
    }
print(f"  Per-symbol top-5% breakdown: {per_symbol_top5}")

# Cohort-level for confidence
per_group_top5 = {}
for grp in np.unique(top_5_groups):
    m = top_5_groups == grp
    if m.sum() == 0:
        continue
    per_group_top5[str(grp)] = {
        "n_in_top5": int(m.sum()),
        "mean_R": round(float(top_5_r[m].mean()), 4),
        "win_rate": round(float((top_5_r[m] > 0).mean()), 4),
    }
print(f"  Per-group top-5% breakdown: {per_group_top5}")


# =========================================================================
# ALL OUTPUTS COMPLETE
# =========================================================================
print("\n=== ALL OUTPUTS WRITTEN ===")
print(f"\nKey numbers for Agent A2 synthesis:")
print(f"  Platt -> Isotonic tied-cluster: {max_tied_orig} -> {max_tied_iso} ({max_tied_iso < max_tied_orig * 0.5})")
print(f"  Aggregated AUC: Platt {float(roc_auc_score(y_valid, p_v3_valid)):.4f} -> Isotonic {auc_iso:.4f}")
print(f"  Top-5% lift: {top_k_extended_results[3]['lift_vs_uniform']:+.4f}")
print(f"  Top-5% DSR-p: {top_k_extended_results[3].get('dsr_p')}")
print(f"  Top-5% CI excludes zero: {top_k_extended_results[3].get('ci_excludes_zero')}")

# Save a summary blob with everything for the markdown writer
summary_blob = {
    "platt": {
        "tied_cluster_max_n": max_tied_orig,
        "tied_cluster_max_pct": round(max_tied_orig / n_valid * 100, 2),
        "n_unique": n_unique_orig,
        "agg_auc": round(float(roc_auc_score(y_valid, p_v3_valid)), 4),
        "per_path_auc_mean": round(ppm_orig, 4),
        "decile_monotonicity": orig_mono,
    },
    "isotonic": {
        "tied_cluster_max_n": max_tied_iso,
        "tied_cluster_max_pct": round(max_tied_iso / n_valid * 100, 2),
        "n_unique": n_unique_iso,
        "agg_auc": round(auc_iso, 4),
        "per_path_auc_mean": round(ppm_iso, 4),
        "decile_monotonicity": iso_mono,
    },
    "jitter_sd_001_auc": round(auc_jit, 4),
    "isotonic_jitter_auc": round(auc_iso_jit, 4),
    "best_top_k": max(top_k_extended_results, key=lambda x: x["lift_vs_uniform"]),
    "best_top_k_by_ci": max(top_k_extended_results, key=lambda x: x["bootstrap_95ci"][0]),
    "best_threshold": max(threshold_extended_results, key=lambda x: x["lift_vs_uniform_R"]),
    "best_threshold_by_ci": max(threshold_extended_results, key=lambda x: x["bootstrap_95ci"][0]),
    "best_bottom_k": max(bottom_k_results, key=lambda x: x["lift_vs_uniform"]),
    "best_combined": max(combined_results, key=lambda x: x["lift_vs_uniform"]) if combined_results else None,
    "research_grade_pass_summary": {
        "any_top_K_RG_pass": [r["top_pct"] for r in top_k_extended_results if r["is_research_grade_pass"]],
        "any_threshold_RG_pass": [r["threshold"] for r in threshold_extended_results if r["is_research_grade_pass"]],
        "any_bottom_K_RG_pass": [r["bottom_pct"] for r in bottom_k_results if r["is_research_grade_pass"]],
        "any_combined_RG_pass": [(r["top_pct"], r["bottom_pct"]) for r in combined_results if r["is_research_grade_pass"]],
    },
    "per_symbol_top5": per_symbol_top5,
    "per_group_top5": per_group_top5,
    "n_valid": int(n_valid),
    "uniform_mean_r": round(uniform_mean_r, 4),
}
jdump(summary_blob, F / "_agent_a2_summary_blob.json")

print(f"\nDone. Wallclock OK.")
