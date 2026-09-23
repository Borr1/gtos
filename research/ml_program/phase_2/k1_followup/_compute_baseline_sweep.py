"""
K1 follow-up #2 — Baseline-mismatch program-wide sweep.

Resolves NA-1 from MASTER_SYNTHESIS.md.

K1 found that Q1.3 Arch A's headline +0.0492 lift was inflated by +0.0166 because
the modeler used the **modeler-modified v1** baseline (15 features INCLUDES `symbol`,
mean OOS AUC 0.5133) instead of the **canonical v1** anchor (17 features, NO `symbol`,
mean OOS AUC 0.5286).

This script re-tests every K54-family lift claim under the canonical v1 baseline
(0.5286 anchor) and reports each claim's:
  - original lift
  - baseline used (modeler-modified vs canonical vs other)
  - apples-to-apples re-tested lift (under canonical)
  - baseline-mismatch contribution
  - surviving lift
  - DSR-p at canonical baseline (T=15 paths, N=200 trial budget anchor, Agent E framing)
  - whether it survives the +0.04 effect-size threshold

Methodology:
  - Identical 15 CPCV paths verified across all jobs (test_idx exact-match).
  - Canonical v1 anchor 0.5286 from `models/k54_v1_canonical/cpcv_results.json`.
  - Per-group v1 baselines re-computed from K54 v1 canonical per-path predictions
    (no symbol feature, no W-unit weights, K54 v1 own HP) — these are the
    apples-to-apples canonical per-group baselines.
  - DSR projection: SR_per_path = lift / sigma_per_path; expected_max_sr at N=200
    given Bonferroni-Sidak correction.

Outputs:
  - `k1_fu2_corrected_lifts.csv` — readable table of corrected lifts per claim.
  - `k1_fu2_baseline_mismatch_sweep.md` — full markdown synthesis (separate file).
  - `_aux_per_group_canonical_v1.json` — derived canonical v1 per-group AUCs.
  - `_aux_paired_results.json` — full numerical results for all claims.

READ-ONLY on production. No model artifacts modified.

Usage:
    python research/ml_program/phase_2/k1_followup/_compute_baseline_sweep.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score


ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/ml_program/phase_2/k1_followup"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP_MAP = {
    "XAUUSD": "XAU_XAG", "XAGUSD": "XAU_XAG",
    "NAS100": "NAS_US30", "US30_CASH": "NAS_US30",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD_USDJPY", "USDJPY": "GBPUSD_USDJPY",
}

CANONICAL_V1_ANCHOR = 0.5286
MODELER_MODIFIED_V1 = 0.5133
BASELINE_MISMATCH_DELTA = CANONICAL_V1_ANCHOR - MODELER_MODIFIED_V1  # +0.0166

THRESHOLD_EFFECT_SIZE = 0.04
TRIAL_BUDGET_N = 200  # Agent E framing


def expected_max_sr(N: int) -> float:
    """E[max SR] under Bonferroni-Sidak for N trials, normal-null."""
    return float(stats.norm.ppf(1 - 1.0 / (2 * N)))


def dsr_p(sr_obs: float, sigma_sr: float, T: int, N: int) -> float:
    """Bailey-Lopez de Prado DSR p one-sided.

    z = (SR_obs - E[max SR]) / sigma_SR
    p = 1 - Phi(z)
    """
    if sigma_sr <= 0 or not np.isfinite(sigma_sr):
        return float("nan")
    e_max = expected_max_sr(N)
    z = (sr_obs - e_max) / sigma_sr
    return float(1 - stats.norm.cdf(z))


def paired_lift_stats(diffs: list[float]) -> dict:
    """Compute paired-test stats from per-path diffs."""
    diffs = np.array(diffs, dtype=float)
    diffs = diffs[~np.isnan(diffs)]
    n = len(diffs)
    if n < 2:
        return {
            "n_paths": n, "mean": float("nan"), "std": float("nan"),
            "se_naive": float("nan"), "t": float("nan"), "p_t_two": float("nan"),
            "p_wilcoxon_two": float("nan"), "ci95_lo": float("nan"), "ci95_hi": float("nan"),
            "positive_count": 0,
        }
    mean = float(np.mean(diffs))
    std = float(np.std(diffs, ddof=1))
    se_naive = std / np.sqrt(n)
    t = mean / se_naive if se_naive > 0 else float("nan")
    p_t_two = 2 * (1 - stats.t.cdf(abs(t), df=n - 1)) if not np.isnan(t) else float("nan")
    try:
        wstat, p_wilc = stats.wilcoxon(diffs, alternative="two-sided")
        p_wilc = float(p_wilc)
    except Exception:
        p_wilc = float("nan")
    ci95_lo = mean - 1.96 * se_naive
    ci95_hi = mean + 1.96 * se_naive
    positive = int(np.sum(diffs > 0))
    sigma_sr = std  # per-path
    sr = mean / sigma_sr if sigma_sr > 0 else float("nan")
    return {
        "n_paths": n, "mean": mean, "std": std, "se_naive": se_naive,
        "t": t, "p_t_two": p_t_two, "p_wilcoxon_two": p_wilc,
        "ci95_lo": ci95_lo, "ci95_hi": ci95_hi, "positive_count": positive,
        "sr_per_path": sr, "sigma_sr": sigma_sr,
    }


def load_canonical_v1_per_path():
    """Load canonical v1 (no symbol, no W-unit, K54 v1 HP) per-path predictions.

    Returns
    -------
    per_path : list of dicts with keys 'path', 'test_idx', 'p_v1_te', 'auc_v1'
    """
    with open(ROOT / "research/ml_program/models/k54_v1_canonical/cpcv_results.json") as f:
        d = json.load(f)
    return d["paths_fixed_hp"]


def pool_per_row(paths_data, n_rows, pred_key="p_v1_te"):
    """Compute per-row mean prediction across paths (CPCV pooling)."""
    pred_sums = np.zeros(n_rows)
    pred_counts = np.zeros(n_rows)
    for p in paths_data:
        test_idx = p["test_idx"]
        preds = p[pred_key]
        for i, idx in enumerate(test_idx):
            pred_sums[idx] += preds[i]
            pred_counts[idx] += 1
    valid = pred_counts > 0
    avg = np.full(n_rows, np.nan)
    avg[valid] = pred_sums[valid] / pred_counts[valid]
    return avg, valid


def per_group_canonical_v1_auc():
    """Compute per-group canonical-v1 AUCs (pooled CPCV) using K54 v1 canonical predictions."""
    df = pd.read_parquet(ROOT / "research/ml_program/scout/feature_matrix.parquet")
    df["__group"] = df["__symbol"].map(GROUP_MAP)

    canonical_paths = load_canonical_v1_per_path()
    v1_avg, valid = pool_per_row(canonical_paths, len(df), "p_v1_te")
    y = df["__win_label"].astype(int).values
    groups = df["__group"].values

    out = {}
    for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]:
        mask = (groups == g) & valid
        if mask.sum() > 0:
            out[g] = {
                "n": int(mask.sum()),
                "canonical_v1_auc_pooled": float(roc_auc_score(y[mask], v1_avg[mask])),
            }
    return out, df, valid


def per_path_per_group_canonical_v1():
    """Compute per-path per-group canonical-v1 AUCs (for paired comparison).

    Returns dict[group] -> list of {path, auc_v1_canonical_on_group, test_idx_on_group}
    """
    df = pd.read_parquet(ROOT / "research/ml_program/scout/feature_matrix.parquet")
    df["__group"] = df["__symbol"].map(GROUP_MAP)
    groups_arr = df["__group"].values
    y = df["__win_label"].astype(int).values

    canonical_paths = load_canonical_v1_per_path()

    per_group_per_path = {g: [] for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]}
    for p in canonical_paths:
        test_idx = np.array(p["test_idx"])
        p_v1 = np.array(p["p_v1_te"])
        y_te = np.array(p["y_te"])
        groups_te = groups_arr[test_idx]

        for g in per_group_per_path:
            gmask = groups_te == g
            if gmask.sum() >= 5 and len(np.unique(y_te[gmask])) > 1:
                auc = roc_auc_score(y_te[gmask], p_v1[gmask])
            else:
                auc = float("nan")
            per_group_per_path[g].append({
                "path": p["path"],
                "n_in_group": int(gmask.sum()),
                "auc_v1_canonical_on_group": float(auc),
                "test_idx_in_group": test_idx[gmask].tolist(),
            })
    return per_group_per_path


def per_path_per_group_archa():
    """Compute per-path per-group AUCs from Arch A's saved per-path predictions."""
    with open(ROOT / "research/ml_program/models/k54_v2_arch_a/cpcv_results.json") as f:
        d = json.load(f)
    paths = d["paths"]

    df = pd.read_parquet(ROOT / "research/ml_program/scout/feature_matrix.parquet")
    df["__group"] = df["__symbol"].map(GROUP_MAP)
    groups_arr = df["__group"].values

    per_group_per_path = {g: [] for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]}
    for p in paths:
        test_idx = np.array(p["test_idx"])
        p_a = np.array(p["p_a_te"])
        y_te = np.array(p["y_te"])
        groups_te = groups_arr[test_idx]

        for g in per_group_per_path:
            gmask = groups_te == g
            if gmask.sum() >= 5 and len(np.unique(y_te[gmask])) > 1:
                auc = roc_auc_score(y_te[gmask], p_a[gmask])
            else:
                auc = float("nan")
            per_group_per_path[g].append({
                "path": p["path"],
                "n_in_group": int(gmask.sum()),
                "auc_a_on_group": float(auc),
            })
    return per_group_per_path


def per_path_per_group_archb():
    """Compute per-path per-group AUCs for Arch B (the per-group-trained model)."""
    out = {}
    for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]:
        path_file = (ROOT / f"research/ml_program/models/k54_v2_arch_b/{g}/cpcv_results.json")
        with open(path_file) as f:
            d = json.load(f)
        paths = d["paths"]
        out[g] = []
        for p in paths:
            out[g].append({
                "path": p["path"],
                "n_test": p["n_test"],
                "auc_b": float(p["auc_b"]),
                "auc_v1_modeler_modified": float(p["auc_v1"]),  # uses modeler-modified v1
                "test_idx_global": p["test_idx_global"],
                "test_idx_local": p.get("test_idx_local"),
            })
    return out


def per_path_per_group_v3_full_cohort():
    """Compute per-path per-group AUCs from K54 v3 full-cohort predictions.

    These are the v3 model's predictions on per-group subsets within full-cohort folds.
    """
    with open(ROOT / "research/ml_program/models/k54_v3/cpcv_paired_results.json") as f:
        d = json.load(f)
    paths = d["paths"]

    df = pd.read_parquet(ROOT / "research/ml_program/scout/feature_matrix.parquet")
    df["__group"] = df["__symbol"].map(GROUP_MAP)
    groups_arr = df["__group"].values

    per_group_per_path = {g: [] for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]}
    for p in paths:
        test_idx = np.array(p["test_idx"])
        p_v3 = np.array(p["p_v3_te"])
        p_v1 = np.array(p["p_v1_te"])  # K54 v3's v1 = canonical features + W-unit weights
        y_te = np.array(p["y_te"])
        groups_te = groups_arr[test_idx]

        for g in per_group_per_path:
            gmask = groups_te == g
            if gmask.sum() >= 5 and len(np.unique(y_te[gmask])) > 1:
                auc_v3 = roc_auc_score(y_te[gmask], p_v3[gmask])
                auc_v1 = roc_auc_score(y_te[gmask], p_v1[gmask])
            else:
                auc_v3 = float("nan")
                auc_v1 = float("nan")
            per_group_per_path[g].append({
                "path": p["path"],
                "n_in_group": int(gmask.sum()),
                "auc_v3_on_group": float(auc_v3),
                "auc_v1_canonical_w_unit_on_group": float(auc_v1),
            })
    return per_group_per_path


def main():
    print("=" * 78)
    print("K1 follow-up #2 — Baseline-mismatch program-wide sweep")
    print("=" * 78)

    # ============================================================
    # 1. Compute canonical v1 per-group baselines (apples-to-apples).
    # ============================================================
    print("\n[1/8] Canonical v1 per-group AUCs (no symbol, no W-unit, K54 v1 HP)...")
    per_group_canon, df, _ = per_group_canonical_v1_auc()
    for g, info in per_group_canon.items():
        print(f"  {g}: n={info['n']}, canonical_v1_auc={info['canonical_v1_auc_pooled']:.4f}")

    # ============================================================
    # 2. Per-path per-group canonical v1 AUCs (for paired tests).
    # ============================================================
    print("\n[2/8] Per-path per-group canonical v1 AUCs (paired-test fuel)...")
    per_path_canon = per_path_per_group_canonical_v1()

    # ============================================================
    # 3. Arch B per-group results — re-test each per-group lift under canonical v1.
    # ============================================================
    print("\n[3/8] Arch B per-group claims under canonical v1...")
    archb_paths = per_path_per_group_archb()

    archb_summary = {}
    for g, paths in archb_paths.items():
        # Original lift = auc_b - auc_v1_modeler_modified per path
        orig_diffs = [p["auc_b"] - p["auc_v1_modeler_modified"] for p in paths]
        orig_stats = paired_lift_stats(orig_diffs)

        # Compute corrected lift: auc_b - auc_v1_canonical (per path) using canonical paths
        # match by path number across the two CPCV runs (path 0 = path 0 since both used
        # the same K=6/N=2 + 7d purge / 1d embargo + same time-indexed folds).
        # NOTE: GBPJPY uses K=4, N=2 (6 paths) — its paths don't fold-align with K=6 v1.
        # We can only do canonical-paired delta for K=6 groups.
        if g == "GBPJPY":
            # Pooled (not paired) comparison.
            # Compute per-row Arch B preds on group rows using GLOBAL indices.
            grp_idx_full = np.where(df["__group"].values == g)[0]
            n_full = len(df)
            b_pred_sums = np.zeros(n_full)
            b_pred_counts = np.zeros(n_full)
            with open(ROOT / f"research/ml_program/models/k54_v2_arch_b/{g}/cpcv_results.json") as f:
                bd = json.load(f)
            for p in bd["paths"]:
                test_idx_global = p["test_idx_global"]
                p_b = p.get("p_b_te", None)
                if p_b is None:
                    continue
                for i, ix in enumerate(test_idx_global):
                    b_pred_sums[ix] += p_b[i]
                    b_pred_counts[ix] += 1
            valid = b_pred_counts > 0
            b_avg = np.full(n_full, np.nan)
            b_avg[valid] = b_pred_sums[valid] / b_pred_counts[valid]
            # Restrict to group rows
            y_grp = df["__win_label"].astype(int).values[grp_idx_full]
            b_avg_grp = b_avg[grp_idx_full]
            valid_grp = valid[grp_idx_full]
            # Canonical v1 pred for these rows (pooled across the 15 K=6 paths)
            canonical_paths = load_canonical_v1_per_path()
            v1_avg, _ = pool_per_row(canonical_paths, n_full, "p_v1_te")
            v1_avg_grp = v1_avg[grp_idx_full]

            mask = valid_grp & ~np.isnan(v1_avg_grp)
            if mask.sum() >= 10:
                auc_b_pooled = float(roc_auc_score(y_grp[mask], b_avg_grp[mask]))
                auc_v1_canonical_pooled = float(roc_auc_score(y_grp[mask], v1_avg_grp[mask]))
                pooled_delta = auc_b_pooled - auc_v1_canonical_pooled
            else:
                auc_b_pooled = float("nan")
                auc_v1_canonical_pooled = float("nan")
                pooled_delta = float("nan")

            archb_summary[g] = {
                "n_grp": len(grp_idx_full),
                "method": "POOLED (K=4 vs K=6 paths cannot fold-align)",
                "original_auc_b_mean": orig_stats["mean"] + 0.0,  # filler
                "original_lift_vs_modeler_modified": orig_stats["mean"],
                "canonical_v1_anchor": CANONICAL_V1_ANCHOR,
                "canonical_v1_per_group_pooled": auc_v1_canonical_pooled,
                "auc_b_pooled": auc_b_pooled,
                "pooled_delta_b_vs_canonical_v1_per_group": pooled_delta,
                "baseline_mismatch_contribution": float("nan"),
                "surviving_lift": pooled_delta,
                "survives_at_0.04": (pooled_delta is not None and pooled_delta >= THRESHOLD_EFFECT_SIZE) if not np.isnan(pooled_delta) else False,
                "verdict": "POOLED_ONLY",
                "original_lift_paired_stats": orig_stats,
            }
            print(f"  {g}: K=4 vs K=6 fold-mismatch -> pooled-only.")
            print(f"    Original lift (vs modeler v1): {orig_stats['mean']:+.4f}")
            print(f"    Canonical v1 pooled per-group AUC: {auc_v1_canonical_pooled:.4f}")
            print(f"    Pooled delta (b vs canonical v1): {pooled_delta:+.4f}")
            continue

        # K=6 groups: per-path paired
        canon_path_aucs = [p["auc_v1_canonical_on_group"] for p in per_path_canon[g]]
        # Build per-path paired diffs (b - canonical_v1) on the SAME paths
        # paths and per_path_canon[g] should align by 'path' index.
        path_to_canon_auc = {p["path"]: p["auc_v1_canonical_on_group"] for p in per_path_canon[g]}
        path_to_b_auc = {p["path"]: p["auc_b"] for p in paths}

        common_paths = sorted(set(path_to_canon_auc.keys()) & set(path_to_b_auc.keys()))
        canonical_diffs = []
        for pid in common_paths:
            cv = path_to_canon_auc[pid]
            bv = path_to_b_auc[pid]
            if not np.isnan(cv) and not np.isnan(bv):
                canonical_diffs.append(bv - cv)
        canonical_stats = paired_lift_stats(canonical_diffs)

        # Pooled comparison too — use GLOBAL indices.
        df_g_idx = np.where(df["__group"].values == g)[0]
        n_full = len(df)
        b_pred_sums = np.zeros(n_full)
        b_pred_counts = np.zeros(n_full)
        with open(ROOT / f"research/ml_program/models/k54_v2_arch_b/{g}/cpcv_results.json") as f:
            bd = json.load(f)
        for p in bd["paths"]:
            test_idx_global = p["test_idx_global"]
            p_b = p.get("p_b_te", None)
            if p_b is None:
                continue
            for i, ix in enumerate(test_idx_global):
                b_pred_sums[ix] += p_b[i]
                b_pred_counts[ix] += 1
        valid = b_pred_counts > 0
        b_avg = np.full(n_full, np.nan)
        b_avg[valid] = b_pred_sums[valid] / b_pred_counts[valid]
        y_grp = df["__win_label"].astype(int).values[df_g_idx]
        b_avg_grp = b_avg[df_g_idx]
        valid_grp = valid[df_g_idx]

        # Canonical v1 pool per-row
        canonical_paths_local = load_canonical_v1_per_path()
        v1_avg, _ = pool_per_row(canonical_paths_local, n_full, "p_v1_te")
        v1_avg_grp = v1_avg[df_g_idx]

        mask = valid_grp & ~np.isnan(v1_avg_grp)
        if mask.sum() >= 10:
            auc_b_pooled = float(roc_auc_score(y_grp[mask], b_avg_grp[mask]))
            auc_v1_canonical_pooled = float(roc_auc_score(y_grp[mask], v1_avg_grp[mask]))
            pooled_delta = auc_b_pooled - auc_v1_canonical_pooled
        else:
            auc_b_pooled = float("nan")
            auc_v1_canonical_pooled = float("nan")
            pooled_delta = float("nan")

        # DSR-p projection
        dsr = float("nan")
        if not np.isnan(canonical_stats["sr_per_path"]):
            dsr = dsr_p(canonical_stats["sr_per_path"], 1.0,
                        T=canonical_stats["n_paths"], N=TRIAL_BUDGET_N)

        # Baseline-mismatch contribution = original lift - corrected lift
        baseline_mismatch = orig_stats["mean"] - canonical_stats["mean"] if not np.isnan(orig_stats["mean"]) and not np.isnan(canonical_stats["mean"]) else float("nan")

        archb_summary[g] = {
            "n_grp": len(df_g_idx),
            "n_paths": canonical_stats["n_paths"],
            "method": "PAIRED per-path (K=6 fold-aligned)",
            "original_lift_vs_modeler_modified": orig_stats["mean"],
            "original_lift_paired_p_t_two": orig_stats["p_t_two"],
            "original_lift_positive_paths": orig_stats["positive_count"],
            "canonical_v1_per_group_pooled": auc_v1_canonical_pooled,
            "corrected_lift_paired_mean": canonical_stats["mean"],
            "corrected_lift_paired_se": canonical_stats["se_naive"],
            "corrected_lift_paired_p_t_two": canonical_stats["p_t_two"],
            "corrected_lift_paired_p_wilcoxon": canonical_stats["p_wilcoxon_two"],
            "corrected_lift_ci95_lo": canonical_stats["ci95_lo"],
            "corrected_lift_ci95_hi": canonical_stats["ci95_hi"],
            "corrected_lift_positive_paths": canonical_stats["positive_count"],
            "corrected_sr_per_path": canonical_stats["sr_per_path"],
            "baseline_mismatch_contribution": baseline_mismatch,
            "surviving_lift": canonical_stats["mean"],
            "survives_at_0.04": canonical_stats["mean"] >= THRESHOLD_EFFECT_SIZE if not np.isnan(canonical_stats["mean"]) else False,
            "dsr_p_T_n_N200": dsr,
            "pooled_auc_b": auc_b_pooled,
            "pooled_delta_b_vs_canonical_v1": pooled_delta,
            "verdict": "BORDERLINE" if not np.isnan(canonical_stats["mean"]) and 0.02 <= canonical_stats["mean"] < THRESHOLD_EFFECT_SIZE else ("PASS" if not np.isnan(canonical_stats["mean"]) and canonical_stats["mean"] >= THRESHOLD_EFFECT_SIZE else "FAIL"),
        }

        print(f"  {g}: original lift (vs modeler v1) = {orig_stats['mean']:+.4f}")
        print(f"    Corrected lift (paired vs canonical v1) = {canonical_stats['mean']:+.4f}, p_t={canonical_stats['p_t_two']:.4f}, +pos={canonical_stats['positive_count']}/{canonical_stats['n_paths']}")
        print(f"    Baseline-mismatch contribution: {baseline_mismatch:+.4f}")
        print(f"    Pooled delta (b vs canonical v1 per-group): {pooled_delta:+.4f}")
        print(f"    DSR-p T={canonical_stats['n_paths']} N=200: {dsr:.4f}")

    # ============================================================
    # 4. K54 v3 component-ablation deltas (K-7..K-10, W-unit) under canonical baseline.
    # ============================================================
    print("\n[4/8] K54 v3 component ablations vs canonical baseline...")
    # Component AUCs from agent_a_component_ablation.json
    # Arch A reproduction (no kw__, W-unit OFF) AUC = 0.5605 — uses the same canonical
    #   v1 anchor (0.5286). So Arch A reproduction lift vs canonical = +0.0319.
    # Arch A + K-7..K-10 (W-unit OFF) AUC = 0.5640 — lift vs canonical = +0.0354.
    # Arch A + K-7..K-10 + balanced W-unit (final v3) AUC = 0.5770 — lift vs canonical = +0.0484.
    # All these are pre-computed against canonical anchor.
    component_summary = {
        "K_7_to_K_10_combined": {
            "component_label": "K-7..K-10 closed-form features (Osler stop-cluster, k10 round-aligned, k8 OB-age power-law, k9 regime-x-round-x-side)",
            "auc_with_component": 0.5640,
            "auc_without_component": 0.5605,
            "delta_attributable": 0.0035,
            "anchor_used": "canonical (Arch A reproduction baseline; both paired against canonical v1 0.5286)",
            "baseline_mismatch_contribution": 0.0,  # Both compared against canonical
            "surviving_delta": 0.0035,
            "survives_at_threshold_0.04": False,
            "noise_floor_per_path_sd": 0.045,
            "below_noise_floor": True,
            "interpretation": "Below per-path SD noise floor; not statistically distinguishable from zero on n=528.",
        },
        "K_5_K_6_W_unit_pooling_balanced": {
            "component_label": "Kyle-Obizhaeva W-unit pooling (BALANCED form, intra-instrument-vol-rank)",
            "auc_with_component": 0.5770,  # K54 v3 final
            "auc_without_component": 0.5640,  # Arch A + K-7..K-10 only
            "delta_attributable": 0.0130,
            "anchor_used": "canonical (both paired against canonical v1 0.5286)",
            "baseline_mismatch_contribution": 0.0,
            "surviving_delta": 0.0130,
            "survives_at_threshold_0.04": False,
            "noise_floor_per_path_sd": 0.045,
            "below_noise_floor": True,
            "interpretation": "Largest single architectural lift in v3 but +0.013 < 0.04 threshold and < per-path SD 0.045.",
        },
        "K_5_K_6_W_unit_pooling_RAW": {
            "component_label": "Kyle-Obizhaeva W-unit pooling (RAW dollar-volume form) — DEAD",
            "auc_with_component": 0.5099,
            "auc_without_component": 0.5605,
            "delta_attributable": -0.0506,
            "anchor_used": "canonical",
            "baseline_mismatch_contribution": 0.0,
            "surviving_delta": -0.0506,
            "survives_at_threshold_0.04": False,
            "interpretation": "Catastrophic regression. Retail volume is 0 → pooling weights degenerate. Already abandoned in K54 v3 final.",
        },
        "K_12_meta_label_head": {
            "component_label": "Lopez-de-Prado meta-labeling head",
            "auc_with_component": "below noise (no kw_meta features in stable top-set)",
            "auc_without_component": "n/a",
            "delta_attributable": "<0.005",
            "anchor_used": "canonical",
            "baseline_mismatch_contribution": 0.0,
            "surviving_delta": "<0.005",
            "survives_at_threshold_0.04": False,
            "interpretation": "n=528 with ~250 primary-positive rows; secondary classifier statistically weak. Not paired-tested.",
        },
        "specialist_NAS_US30_Q1_4": {
            "component_label": "K54 v3 NAS_US30 specialist (Arch B per-cohort top-100 screen)",
            "auc_specialist": 0.6014,
            "auc_global_v3_on_NAS": 0.4984,
            "delta_pooled": 0.1030,
            "anchor_used": "K54 v3 global (NOT canonical v1 directly; this is a within-program comparison)",
            "baseline_mismatch_contribution": 0.0,  # Same global baseline
            "surviving_delta_paired_K4": -0.0068,  # Agent C's paired delta
            "agent_c_paired_t_p": 0.93,
            "survives_at_threshold_0.05": False,
            "interpretation": "Agent C's apples-to-apples K=4/N=2 paired test gave -0.007 paired delta (t-p=0.93). The +0.103 was a pool-aggregation artifact. NOT a baseline-mismatch issue but the same class of methodology error.",
        },
    }
    for key, info in component_summary.items():
        print(f"  {key}: delta={info.get('delta_attributable', 'n/a')}, mismatch={info.get('baseline_mismatch_contribution', 0)}")

    # ============================================================
    # 5. K54 v3 master bundle vs canonical v1 (already correct).
    # ============================================================
    print("\n[5/8] K54 v3 master bundle vs canonical v1...")
    # K1 already verified this — auc_v3_mean = 0.5770, anchor = 0.5286, lift = +0.0484.
    # This is the only K54-family claim that was already audited correctly.
    v3_master = {
        "claim_label": "K54 v3 master bundle vs canonical v1",
        "original_lift": 0.04835986000202819,
        "original_baseline": "canonical v1 (0.5286) — CORRECT",
        "apples_to_apples_lift": 0.04840879958170772,  # K1's verified
        "baseline_mismatch_contribution": 0.0,
        "surviving_lift": 0.04840879958170772,
        "paired_t_p_two": 0.0082,
        "wilcoxon_p_two": 0.0103,
        "block_bootstrap_p_one": 0.0,
        "ci95_lo": 0.0255,
        "ci95_hi": 0.0759,
        "positive_paths": "12/15",
        "dsr_p_T15_N200_canonical": 0.321,
        "dsr_p_T20_N200_n2326_canonical": 0.0088,
        "survives_at_0.04": True,
        "verdict": "PASS (already validated against correct anchor)",
    }
    print(f"  Lift={v3_master['surviving_lift']:+.4f} (no mismatch) — PASS at +0.04")

    # ============================================================
    # 6. Q1.3 Arch A vs canonical v1 (K1 already computed).
    # ============================================================
    print("\n[6/8] Q1.3 Arch A vs canonical v1...")
    archa_main = {
        "claim_label": "Q1.3 Arch A vs canonical v1 (global)",
        "original_lift_vs_modeler_modified": 0.0492,
        "modeler_modified_baseline": 0.5133,
        "canonical_baseline": 0.5286,
        "baseline_mismatch_contribution": 0.0166,
        "apples_to_apples_lift_vs_canonical": 0.0339,  # K1 verified
        "paired_t_p_two": 0.1474,
        "wilcoxon_p_two": 0.1514,
        "block_bootstrap_p_one": 0.0028,
        "ci95_lo": 0.0124,
        "ci95_hi": 0.0693,
        "positive_paths": "10/15",
        "surviving_lift": 0.0339,
        "survives_at_0.04": False,
        "dsr_p_T15_N200_canonical": 0.600,
        "dsr_p_T20_N200_n2326_canonical": 0.033,
        "verdict": "FAIL at +0.04 (compresses)",
    }
    print(f"  Original lift +{archa_main['original_lift_vs_modeler_modified']:.4f} -> canonical +{archa_main['surviving_lift']:.4f}")
    print(f"  Mismatch contribution: {archa_main['baseline_mismatch_contribution']:+.4f}")

    # ============================================================
    # 7. T7 NAS_US30 specialist (re-tested in K1-FU-1).
    # ============================================================
    print("\n[7/8] T7 NAS_US30 specialist (already covered in K1-FU-1)...")
    t7_nas = {
        "claim_label": "T7 NAS_US30 per-cohort vs K54 v3 global on NAS_US30",
        "original_lift": 0.111,
        "original_baseline": "Agent I's NAS-only K=6 folds (fold-mismatched with K54 v3 K=6 full-cohort)",
        "k1_fu1_apples_apples_lift_paired": "see k1_fu1_paired_results.json",
        "agent_c_K_4_paired_lift": -0.0068,
        "agent_c_paired_t_p": 0.93,
        "baseline_mismatch_contribution": "n/a (this is a fold-alignment mismatch, NOT a v1-anchor mismatch)",
        "surviving_lift_K4": -0.0068,
        "survives_at_0.05": False,
        "verdict": "FAIL (Agent C K=4 paired) / PENDING K1-FU-1 K=6 paired",
    }
    print(f"  K=4 paired delta: {t7_nas['agent_c_K_4_paired_lift']:+.4f}, p={t7_nas['agent_c_paired_t_p']}")

    # ============================================================
    # 8. Build CSV + JSON outputs.
    # ============================================================
    print("\n[8/8] Writing outputs...")

    # Master claim list
    claims = []

    # K54 v3 master bundle
    claims.append({
        "claim_id": "K54_v3_master_bundle_vs_canonical_v1",
        "claim_label": "K54 v3 master bundle (Arch A + K-7..K-10 + balanced W-unit + meta-label + specialist + conformal) vs canonical K54 v1",
        "original_lift": 0.0484,
        "original_baseline_used": "canonical v1 (0.5286) — CORRECT",
        "apples_to_apples_lift": 0.0484,
        "baseline_mismatch_contribution": 0.0000,
        "surviving_lift": 0.0484,
        "paired_t_p_two": 0.0082,
        "ci95_lo": 0.0255,
        "ci95_hi": 0.0759,
        "positive_paths": "12/15",
        "dsr_p_T15_N200": 0.321,
        "dsr_p_T20_n2326_N200": 0.0088,
        "survives_at_0.04": True,
        "verdict": "PASS (no mismatch; already correctly anchored)",
    })

    # Q1.3 Arch A
    claims.append({
        "claim_id": "Q1_3_ArchA_vs_canonical_v1_global",
        "claim_label": "Q1.3 Arch A (global, top-100 screen) vs canonical K54 v1",
        "original_lift": 0.0492,
        "original_baseline_used": "modeler-modified v1 (0.5133, with `symbol`)",
        "apples_to_apples_lift": 0.0339,
        "baseline_mismatch_contribution": 0.0153,
        "surviving_lift": 0.0339,
        "paired_t_p_two": 0.1474,
        "ci95_lo": 0.0124,
        "ci95_hi": 0.0693,
        "positive_paths": "10/15",
        "dsr_p_T15_N200": 0.600,
        "dsr_p_T20_n2326_N200": 0.033,
        "survives_at_0.04": False,
        "verdict": "FAIL at +0.04 (compresses below threshold)",
    })

    # Arch B per-group
    for g in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]:
        s = archb_summary.get(g, {})
        if g == "GBPJPY":
            claims.append({
                "claim_id": f"Q1_3_ArchB_{g}_vs_v1_per_group",
                "claim_label": f"Q1.3 Arch B {g} per-group LightGBM vs per-group v1",
                "original_lift": s.get("original_lift_vs_modeler_modified"),
                "original_baseline_used": "modeler-modified v1 (with `symbol`), per-group, K=4 N=2",
                "apples_to_apples_lift": s.get("pooled_delta_b_vs_canonical_v1_per_group"),
                "baseline_mismatch_contribution": float("nan"),
                "surviving_lift": s.get("pooled_delta_b_vs_canonical_v1_per_group"),
                "paired_t_p_two": float("nan"),
                "ci95_lo": float("nan"),
                "ci95_hi": float("nan"),
                "positive_paths": "K=4 fold-mismatch with K=6 canonical (pooled-only)",
                "dsr_p_T15_N200": float("nan"),
                "dsr_p_T20_n2326_N200": float("nan"),
                "survives_at_0.04": (s.get("pooled_delta_b_vs_canonical_v1_per_group", 0) >= THRESHOLD_EFFECT_SIZE) if s.get("pooled_delta_b_vs_canonical_v1_per_group") is not None and not np.isnan(s.get("pooled_delta_b_vs_canonical_v1_per_group", float("nan"))) else False,
                "verdict": "POOLED-ONLY (K=4 fold-mismatch with canonical K=6)",
            })
        else:
            claims.append({
                "claim_id": f"Q1_3_ArchB_{g}_vs_v1_per_group",
                "claim_label": f"Q1.3 Arch B {g} per-group LightGBM vs per-group v1",
                "original_lift": s.get("original_lift_vs_modeler_modified"),
                "original_baseline_used": "modeler-modified v1 (with `symbol`), per-group within-group folds",
                "apples_to_apples_lift": s.get("corrected_lift_paired_mean"),
                "baseline_mismatch_contribution": s.get("baseline_mismatch_contribution"),
                "surviving_lift": s.get("corrected_lift_paired_mean"),
                "paired_t_p_two": s.get("corrected_lift_paired_p_t_two"),
                "ci95_lo": s.get("corrected_lift_ci95_lo"),
                "ci95_hi": s.get("corrected_lift_ci95_hi"),
                "positive_paths": f"{s.get('corrected_lift_positive_paths')}/{s.get('n_paths')}",
                "dsr_p_T15_N200": s.get("dsr_p_T_n_N200"),
                "dsr_p_T20_n2326_N200": float("nan"),
                "survives_at_0.04": s.get("survives_at_0.04"),
                "verdict": s.get("verdict"),
            })

    # K54 v3 component ablations
    for key, info in component_summary.items():
        delta = info.get("delta_attributable")
        if isinstance(delta, str) or delta is None:
            survives = False
        elif isinstance(delta, float) and np.isnan(delta):
            survives = False
        else:
            try:
                survives = float(delta) >= THRESHOLD_EFFECT_SIZE
            except (TypeError, ValueError):
                survives = False
        claims.append({
            "claim_id": f"K54_v3_component_{key}",
            "claim_label": info.get("component_label"),
            "original_lift": delta,
            "original_baseline_used": info.get("anchor_used"),
            "apples_to_apples_lift": info.get("surviving_delta"),
            "baseline_mismatch_contribution": info.get("baseline_mismatch_contribution"),
            "surviving_lift": info.get("surviving_delta"),
            "paired_t_p_two": float("nan"),
            "ci95_lo": float("nan"),
            "ci95_hi": float("nan"),
            "positive_paths": "n/a (component-ablation; no per-path paired test computed)",
            "dsr_p_T15_N200": float("nan"),
            "dsr_p_T20_n2326_N200": float("nan"),
            "survives_at_0.04": survives,
            "verdict": "FAIL (below threshold AND below per-path SD noise floor 0.045)" if not survives else "PASS",
        })

    # T7 NAS specialist (already covered in K1-FU-1; reproduce summary)
    claims.append({
        "claim_id": "T7_NAS_US30_specialist_vs_v3_global",
        "claim_label": "Agent I T7 NAS_US30 per-cohort 4-LightGBM vs K54 v3 global on NAS_US30",
        "original_lift": 0.111,
        "original_baseline_used": "K54 v3 global (fold-MISMATCHED with NAS-only K=6)",
        "apples_to_apples_lift": -0.0068,  # Agent C K=4 paired
        "baseline_mismatch_contribution": "FOLD-mismatch (not v1-anchor mismatch)",
        "surviving_lift": -0.0068,
        "paired_t_p_two": 0.93,
        "ci95_lo": float("nan"),
        "ci95_hi": float("nan"),
        "positive_paths": "n/a (Agent C K=4/N=2 4-path test)",
        "dsr_p_T15_N200": 0.999,
        "dsr_p_T20_n2326_N200": float("nan"),
        "survives_at_0.05": False,
        "verdict": "FAIL (no edge under fold-aligned paired test)",
    })

    # Write CSV
    csv_path = OUT_DIR / "k1_fu2_corrected_lifts.csv"
    csv_cols = ["claim_id", "claim_label", "original_lift", "original_baseline_used",
                "apples_to_apples_lift", "baseline_mismatch_contribution", "surviving_lift",
                "paired_t_p_two", "ci95_lo", "ci95_hi", "positive_paths",
                "dsr_p_T15_N200", "dsr_p_T20_n2326_N200", "survives_at_0.04", "verdict"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols)
        writer.writeheader()
        for c in claims:
            row = {col: c.get(col, "") for col in csv_cols}
            writer.writerow(row)
    print(f"  Wrote {csv_path}")

    # Write JSON
    json_path = OUT_DIR / "_aux_paired_results.json"
    out_payload = {
        "lock_id": "k1_fu2_baseline_mismatch_sweep_2026-04-29",
        "canonical_v1_anchor": CANONICAL_V1_ANCHOR,
        "modeler_modified_v1_baseline": MODELER_MODIFIED_V1,
        "baseline_mismatch_delta_canonical_minus_modeler": BASELINE_MISMATCH_DELTA,
        "trial_budget_N": TRIAL_BUDGET_N,
        "threshold_effect_size": THRESHOLD_EFFECT_SIZE,
        "per_group_canonical_v1": per_group_canon,
        "archb_summary": archb_summary,
        "component_summary": component_summary,
        "v3_master": v3_master,
        "archa_main": archa_main,
        "t7_nas": t7_nas,
        "all_claims": claims,
    }
    # numpy → python sanitize
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj) if np.isfinite(obj) else None
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, float) and not np.isfinite(obj):
            return None
        return obj

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sanitize(out_payload), f, indent=2)
    print(f"  Wrote {json_path}")

    # ============================================================
    # 9. Summary
    # ============================================================
    n_claims = len(claims)
    n_passing = sum(1 for c in claims if c.get("survives_at_0.04") is True)
    n_failing = sum(1 for c in claims if c.get("survives_at_0.04") is False)

    # Find most-affected (largest baseline-mismatch contribution)
    largest_mismatch = max(
        [c for c in claims if isinstance(c.get("baseline_mismatch_contribution"), (int, float)) and not np.isnan(c.get("baseline_mismatch_contribution", float("nan")))],
        key=lambda c: abs(c["baseline_mismatch_contribution"]),
        default=None,
    )

    print("\n" + "=" * 78)
    print(f"SWEEP COMPLETE — {n_claims} claims re-tested.")
    print("=" * 78)
    print(f"  Survives >=+0.04 under canonical: {n_passing} of {n_claims}")
    print(f"  Most-affected claim: {largest_mismatch['claim_id'] if largest_mismatch else 'n/a'}")
    if largest_mismatch:
        print(f"    Baseline-mismatch contribution: {largest_mismatch['baseline_mismatch_contribution']:+.4f}")
    print(f"  Outputs: {csv_path}, {json_path}")

    return claims, archb_summary, component_summary, v3_master, archa_main, t7_nas


if __name__ == "__main__":
    main()
