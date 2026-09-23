# -*- coding: utf-8 -*-
"""Canonical K54 v1 Re-run — Auditor.

Re-runs K54 v1 under the SAME CPCV K=6,N=2 splits as Q1.3 (commit `af5d97e`'s
modifier replaced canonical features), under TWO configurations:

  Config A — canonical v1 (17 features, global single model):
    `framework, instrument_class, direction_long_short, kill_zone,
     setup_grade, regime_tag, cross_instrument_xau_dir,
     hour_utc, day_of_week, counter_direction_flag,
     ob_distance_atr, ob_age_candles, displacement_quality_score,
     fvg_present, touch_count, ai_confidence, walk_level_signal`
    NO `symbol`. Includes `framework` (canonical, even though zero importance).

  Config B — per-regime v1 (17 features, ensemble):
    Same features. One LightGBM per regime label
    (bullish/bearish/transitional/UNTAGGED). Inference: route by `regime_tag`;
    fallback to global if per-regime train rows < 20.

Outputs:
  research/ml_program/models/k54_v1_canonical/
    - k54_v1_canonical.lgb (Config A final)
    - cpcv_results.json
  research/ml_program/models/k54_v1_per_regime/
    - regime_{label}.lgb (one per regime label trained)
    - cpcv_results.json
  research/ml_program/audit/canonical_v1_rerun.md (comparative report)
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
import warnings
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

import lightgbm as lgb

warnings.filterwarnings("ignore")

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
V1_FEATURES_FULL = ROOT / "research/ml_program/models/k54_v1_features_full.csv"
V2_CPCV = ROOT / "research/ml_program/models/k54_v2/cpcv_paired_results.json"
V2_META = ROOT / "research/ml_program/models/k54_v2/meta.json"
OUT_CANON = ROOT / "research/ml_program/models/k54_v1_canonical"
OUT_REGIME = ROOT / "research/ml_program/models/k54_v1_per_regime"
OUT_AUDIT = ROOT / "research/ml_program/audit"
OUT_CANON.mkdir(parents=True, exist_ok=True)
OUT_REGIME.mkdir(parents=True, exist_ok=True)
OUT_AUDIT.mkdir(parents=True, exist_ok=True)

DATA_CUTOFF = "2026-04-28"
RANDOM_SEED = 42

# CPCV must match v2 exactly
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1

# K54 v1 audit Section 6 #4: HP grid (n_estimators in {50,100,200},
# max_depth in {3,5,7}, learning_rate in {0.01,0.05,0.1}) = 27 combos
HYPER_GRID = [
    {"n_estimators": ne, "max_depth": md, "learning_rate": lr}
    for ne in (50, 100, 200)
    for md in (3, 5, 7)
    for lr in (0.01, 0.05, 0.1)
]
assert len(HYPER_GRID) == 27

# Per-regime min row threshold (K54 v1 audit Section 6 #2)
MIN_REGIME_ROWS = 20

# Canonical v1 17 features (matches k54_v1_features.csv)
CANONICAL_NUM_FEATURES = [
    "hour_utc", "day_of_week", "counter_direction_flag",
    "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
    "fvg_present", "touch_count", "ai_confidence", "walk_level_signal",
]
CANONICAL_CAT_FEATURES = [
    "framework",  # included per canonical (zero importance but present)
    "instrument_class", "direction_long_short", "kill_zone",
    "setup_grade", "regime_tag", "cross_instrument_xau_dir",
]
CANONICAL_FEATURES = CANONICAL_NUM_FEATURES + CANONICAL_CAT_FEATURES
assert len(CANONICAL_FEATURES) == 17


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_cohort() -> tuple[pd.DataFrame, np.ndarray, pd.Series]:
    """Load 528-row scout cohort + dedup keys + dates (matches v2 ordering)."""
    df = pd.read_parquet(SCOUT_PARQUET)
    assert df["__date"].max() <= DATA_CUTOFF, (
        f"V2 matrix has dates beyond cutoff: max={df['__date'].max()}"
    )
    df["dedup_key"] = list(
        zip(
            df["__date"].astype(str).str[:10],
            df["__symbol"],
            df["__direction"],
            df["__framework"],
            df["__realized_r"].round(3),
        )
    )
    assert df["dedup_key"].nunique() == len(df), "Cohort has duplicate keys"
    y = df["__win_label"].astype(int).values
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    return df, y, dates


def prepare_canonical_v1_X(df_cohort: pd.DataFrame) -> pd.DataFrame:
    """Build canonical v1 17-feature design matrix on the 528-row cohort.

    Joins the v1 features CSV onto the v2 cohort by dedup_key, in v2 cohort
    row order.
    """
    v1_raw = pd.read_csv(V1_FEATURES_FULL)
    v1_raw["date_only"] = v1_raw["date_iso"].astype(str).str[:10]
    v1_raw["dedup_key"] = list(
        zip(
            v1_raw["date_only"],
            v1_raw["symbol"],
            v1_raw["direction_long_short"],
            v1_raw["framework"],
            v1_raw["realized_r"].round(3),
        )
    )
    v1_dedup = v1_raw.drop_duplicates(subset="dedup_key", keep="first").copy()

    # Align by dedup_key in v2 cohort order
    keys_df = pd.DataFrame({"dedup_key": df_cohort["dedup_key"].tolist()})
    v1_aligned = keys_df.merge(v1_dedup, on="dedup_key", how="left")
    n_missing = v1_aligned[CANONICAL_NUM_FEATURES[0]].isna().sum()
    assert n_missing == 0, f"v1 alignment: {n_missing} unmatched cohort rows"

    encoded = pd.DataFrame(index=v1_aligned.index)

    # Numerical: cast to float, fill NaN with -1
    for c in CANONICAL_NUM_FEATURES:
        encoded[c] = pd.to_numeric(v1_aligned[c], errors="coerce").fillna(-1).astype(float)

    # Categorical: label-encode via category codes
    # NOTE: cross_instrument_xau_dir is always NaN; encoding -> -1 (single class).
    # framework has 3 classes ('ob_retest', 'session_sweep', 'breaker_retest').
    # Use stable encoding per-column.
    for c in CANONICAL_CAT_FEATURES:
        col = v1_aligned[c]
        if col.dtype == "float64" or col.dtype == "Float64":
            # cross_instrument_xau_dir is float64 with all-NaN -> single category code
            vals = col.fillna("__missing__").astype(str)
        else:
            vals = col.fillna("__missing__").astype(str)
        codes = vals.astype("category").cat.codes
        encoded[c] = codes.astype(int)

    return encoded


def time_indexed_folds(dates: pd.Series, k: int) -> list[np.ndarray]:
    """Match v2 fold construction exactly."""
    sort_idx = np.argsort(dates.values)
    fold_size = len(sort_idx) // k
    folds: list[np.ndarray] = []
    for i in range(k):
        start = i * fold_size
        end = (i + 1) * fold_size if i < k - 1 else len(sort_idx)
        folds.append(sort_idx[start:end])
    return folds


def cpcv_paths(folds: list[np.ndarray], n: int) -> list[tuple[list[int], list[int]]]:
    """Match v2 path construction exactly."""
    k = len(folds)
    paths = []
    for test_combo in combinations(range(k), n):
        train_combo = [i for i in range(k) if i not in test_combo]
        paths.append((train_combo, list(test_combo)))
    return paths


def purge_embargo(
    train_idx: np.ndarray,
    test_idx_groups: list[np.ndarray],
    dates: pd.Series,
    purge_days: int,
    embargo_days: int,
) -> np.ndarray:
    """Match v2 purge/embargo behavior exactly (per-group purge)."""
    train_dates = pd.to_datetime(dates.iloc[train_idx])
    keep_mask = pd.Series(True, index=train_idx)
    for tg in test_idx_groups:
        test_dates = pd.to_datetime(dates.iloc[tg])
        t_min = test_dates.min() - pd.Timedelta(days=purge_days)
        t_max = test_dates.max() + pd.Timedelta(days=embargo_days)
        in_zone = (train_dates >= t_min) & (train_dates <= t_max)
        keep_mask = keep_mask & ~in_zone.values
    return train_idx[keep_mask.values]


def train_lgbm(
    X_tr: pd.DataFrame, y_tr: np.ndarray,
    X_val: pd.DataFrame | None, y_val: np.ndarray | None,
    hp: dict, n_train: int,
) -> lgb.LGBMClassifier:
    min_data_in_leaf = max(3, n_train // 30)
    model = lgb.LGBMClassifier(
        n_estimators=hp["n_estimators"],
        max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"],
        min_data_in_leaf=min_data_in_leaf,
        num_leaves=2 ** hp["max_depth"],
        objective="binary",
        metric="auc",
        n_jobs=1,
        verbosity=-1,
        random_state=RANDOM_SEED,
        deterministic=True,
        force_row_wise=True,
    )
    fit_kw: dict[str, Any] = {}
    if X_val is not None and len(X_val) > 0 and len(np.unique(y_val)) >= 2:
        fit_kw = {
            "eval_set": [(X_val, y_val)],
            "callbacks": [lgb.early_stopping(20, verbose=False)],
        }
    model.fit(X_tr, y_tr, **fit_kw)
    return model


def calibrate(
    model_proba_tr: np.ndarray, y_tr: np.ndarray,
    model_proba_te: np.ndarray,
) -> np.ndarray:
    if len(np.unique(y_tr)) < 2:
        return model_proba_te
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(model_proba_tr.reshape(-1, 1), y_tr)
    return cal.predict_proba(model_proba_te.reshape(-1, 1))[:, 1]


def safe_auc(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


def delong_paired_test(
    y: np.ndarray, p1: np.ndarray, p2: np.ndarray,
) -> tuple[float, float]:
    """DeLong's test, ported from train_k54_v2.py."""
    if len(np.unique(y)) < 2:
        return float("nan"), float("nan")
    pos_mask = y == 1
    neg_mask = y == 0
    n_pos = int(pos_mask.sum())
    n_neg = int(neg_mask.sum())
    if n_pos < 2 or n_neg < 2:
        return float("nan"), float("nan")

    def midrank(x: np.ndarray) -> np.ndarray:
        order = np.argsort(x)
        x_sorted = x[order]
        n = len(x)
        T = np.zeros(n)
        i = 0
        while i < n:
            j = i
            while j < n and x_sorted[j] == x_sorted[i]:
                j += 1
            T[i:j] = 0.5 * (i + j - 1) + 1
            i = j
        T2 = np.empty(n)
        T2[order] = T
        return T2

    def aucs_and_cov(p_mat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        k = p_mat.shape[0]
        p_pos = p_mat[:, pos_mask]
        p_neg = p_mat[:, neg_mask]
        tx = np.zeros((k, n_pos))
        ty = np.zeros((k, n_neg))
        tz = np.zeros((k, n_pos + n_neg))
        for r in range(k):
            tx[r] = midrank(p_pos[r])
            ty[r] = midrank(p_neg[r])
            tz[r] = midrank(np.concatenate([p_pos[r], p_neg[r]]))
        aucs = (tz[:, :n_pos].sum(axis=1) / n_pos - (n_pos + 1) / 2.0) / n_neg
        v01 = (tz[:, :n_pos] - tx) / n_neg
        v10 = 1.0 - (tz[:, n_pos:] - ty) / n_pos
        sx = np.cov(v01, ddof=1) if k > 1 else np.atleast_2d(np.var(v01, ddof=1))
        sy = np.cov(v10, ddof=1) if k > 1 else np.atleast_2d(np.var(v10, ddof=1))
        if sx.ndim == 0:
            sx = np.atleast_2d(sx)
        if sy.ndim == 0:
            sy = np.atleast_2d(sy)
        cov = sx / n_pos + sy / n_neg
        return aucs, cov

    p_mat = np.stack([p1, p2])
    aucs, cov = aucs_and_cov(p_mat)
    auc_diff = float(aucs[1] - aucs[0])
    L = np.array([-1.0, 1.0])
    var = float(L @ cov @ L)
    if var <= 0 or not np.isfinite(var):
        return auc_diff, float("nan")
    z = auc_diff / math.sqrt(var)
    p_two = 2.0 * (1.0 - stats.norm.cdf(abs(z)))
    return auc_diff, float(p_two)


def stouffer_combine(p_values: list[float]) -> float:
    pv = [p for p in p_values if p is not None and not math.isnan(p) and 0 < p < 1]
    if not pv:
        return float("nan")
    z = [stats.norm.ppf(1 - p) for p in pv]
    z_combined = sum(z) / math.sqrt(len(z))
    return float(1 - stats.norm.cdf(z_combined))


def fisher_combine(p_values: list[float]) -> float:
    pv = [p for p in p_values if p is not None and not math.isnan(p) and 0 < p < 1]
    if not pv:
        return float("nan")
    chi2 = -2 * sum(math.log(p) for p in pv)
    df = 2 * len(pv)
    return float(1 - stats.chi2.cdf(chi2, df))


def regime_label_for_row(regime_code: int, code_to_label: dict[int, str]) -> str:
    """Map encoded category code -> string label."""
    return code_to_label.get(regime_code, "__missing__")


# =====================================================================
# Config A — Canonical v1 (17 features, global)
# =====================================================================

def run_config_a(
    X_v1: pd.DataFrame, y: np.ndarray, dates: pd.Series,
    folds: list[np.ndarray], paths: list[tuple[list, list]],
    v2_paths: list[dict],
) -> dict:
    print("\n=== CONFIG A — Canonical v1 (17 features, global) ===")
    cpcv_results = []
    hp_path_aucs: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}

    t0 = time.time()
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)

        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        X_tr = X_v1.iloc[inner_train]
        X_iv = X_v1.iloc[inner_val]
        X_te = X_v1.iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        # Train all 27 HP combos, record OOS AUC for each (for fixed-HP selection)
        path_aucs = []
        for hp_idx, hp in enumerate(HYPER_GRID):
            try:
                m = train_lgbm(X_tr, y_tr, X_iv, y_iv, hp, len(inner_train))
                p_iv = m.predict_proba(X_iv)[:, 1]
                p_te = m.predict_proba(X_te)[:, 1]
                p_te = calibrate(p_iv, y_iv, p_te)
                a = safe_auc(y_te, p_te)
            except Exception as e:
                a = float("nan")
                p_te = None
            path_aucs.append(a)
            hp_path_aucs[hp_idx].append(a)

        cpcv_results.append({
            "path": path_idx,
            "train_groups": list(train_groups),
            "test_groups": list(test_groups),
            "n_train_after_purge": int(len(inner_train)),
            "n_inner_val": int(len(inner_val)),
            "n_test": int(len(test_idx)),
            "test_idx": test_idx.tolist(),
            "y_te": y_te.tolist(),
            "per_hp_oos_auc": [float(a) for a in path_aucs],
        })

        if path_idx % 3 == 0 or path_idx == len(paths) - 1:
            print(f"  [A] Path {path_idx+1}/{len(paths)} t={time.time()-t0:.1f}s")

    # Select fixed HP by mean OOS AUC across paths
    n_hp = len(HYPER_GRID)
    hp_mean = np.array([np.nanmean(hp_path_aucs[i]) for i in range(n_hp)])
    best_hp_idx = int(np.nanargmax(hp_mean))
    best_hp = HYPER_GRID[best_hp_idx]

    # Re-train at fixed HP per path, generate predictions, paired DeLong vs v2
    fixed_results = []
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)

        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        X_tr = X_v1.iloc[inner_train]
        X_iv = X_v1.iloc[inner_val]
        X_te = X_v1.iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        m = train_lgbm(X_tr, y_tr, X_iv, y_iv, best_hp, len(inner_train))
        p_iv = m.predict_proba(X_iv)[:, 1]
        p_te = m.predict_proba(X_te)[:, 1]
        p_te = calibrate(p_iv, y_iv, p_te)
        auc_v1 = safe_auc(y_te, p_te)
        brier_v1 = brier_score_loss(y_te, p_te) if len(np.unique(y_te)) > 1 else float("nan")

        # Get v2 predictions on this path's test_idx (matched by index in v2 paths array)
        v2_path = v2_paths[path_idx]
        # v2 path's test_idx may be in different order; match by test_idx
        v2_test_idx = v2_path["test_idx"]
        v2_p = np.array(v2_path["p_v2_te"])
        # Match: each test_idx in our path has a corresponding entry in v2_test_idx
        v2_lookup = {ti: v2_p[i] for i, ti in enumerate(v2_test_idx)}
        p_v2_te = np.array([v2_lookup[ti] for ti in test_idx])
        auc_v2 = safe_auc(y_te, p_v2_te)

        # DeLong: v1 vs v2 paired
        auc_diff, p_delong = delong_paired_test(y_te, p_te, p_v2_te)

        fixed_results.append({
            "path": path_idx,
            "n_test": int(len(test_idx)),
            "auc_v1_canonical": float(auc_v1),
            "auc_v2": float(auc_v2),
            "auc_diff_v2_minus_v1": float(auc_v2 - auc_v1),
            "delong_p": float(p_delong),
            "brier_v1": float(brier_v1),
            "test_idx": test_idx.tolist(),
            "p_v1_te": p_te.tolist(),
            "y_te": y_te.tolist(),
        })

    # Summary stats
    diffs = np.array([r["auc_diff_v2_minus_v1"] for r in fixed_results])
    delong_ps = [r["delong_p"] for r in fixed_results]
    auc_v1_mean = float(np.nanmean([r["auc_v1_canonical"] for r in fixed_results]))
    auc_v2_mean = float(np.nanmean([r["auc_v2"] for r in fixed_results]))
    diff_mean = float(np.nanmean(diffs))
    diff_std = float(np.nanstd(diffs, ddof=1))
    diff_se = diff_std / math.sqrt(len(diffs))
    diff_ci_lo = diff_mean - 1.96 * diff_se
    diff_ci_hi = diff_mean + 1.96 * diff_se
    p_combined_stouffer = stouffer_combine(delong_ps)
    p_combined_fisher = fisher_combine(delong_ps)

    gate_a_pass = (diff_mean >= 0.04) and (p_combined_stouffer < 0.01)

    summary = {
        "config": "A — canonical v1 (17 features, global)",
        "n_paths": len(paths),
        "K": CPCV_K,
        "N": CPCV_N,
        "purge_days": PURGE_DAYS,
        "embargo_days": EMBARGO_DAYS,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "hp_mean_oos_auc_at_selected": float(hp_mean[best_hp_idx]),
        "auc_v1_canonical_mean": auc_v1_mean,
        "auc_v2_mean": auc_v2_mean,
        "diff_mean_v2_minus_v1": diff_mean,
        "diff_std": diff_std,
        "diff_se": float(diff_se),
        "diff_95ci": [float(diff_ci_lo), float(diff_ci_hi)],
        "delong_p_per_path": delong_ps,
        "delong_p_combined_stouffer": p_combined_stouffer,
        "delong_p_combined_fisher": p_combined_fisher,
        "gate_a_threshold": "diff_mean >= 0.04 AND combined DeLong p < 0.01",
        "gate_a_pass": bool(gate_a_pass),
        "computed_at": utc_now(),
    }
    print(f"  [A] Selected HP idx={best_hp_idx}: {best_hp}")
    print(f"  [A] auc_v1_mean={auc_v1_mean:.4f}, auc_v2_mean={auc_v2_mean:.4f}, "
          f"diff_mean={diff_mean:+.4f}, p_stouffer={p_combined_stouffer:.6f}, "
          f"PASS={gate_a_pass}")

    # Fit final canonical v1 on full cohort (most-recent 1/8 as inner val)
    sort_perm = np.argsort(dates.values)
    n_inner = len(sort_perm) // 8
    inner_val_full = sort_perm[-n_inner:]
    inner_train_full = sort_perm[:-n_inner]
    final_v1 = train_lgbm(
        X_v1.iloc[inner_train_full], y[inner_train_full],
        X_v1.iloc[inner_val_full], y[inner_val_full],
        best_hp, len(inner_train_full),
    )
    final_v1.booster_.save_model(str(OUT_CANON / "k54_v1_canonical.lgb"))

    out = {
        "summary": summary,
        "paths_per_hp": cpcv_results,
        "paths_fixed_hp": fixed_results,
        "hp_grid": HYPER_GRID,
        "hp_path_aucs": {i: hp_path_aucs[i] for i in range(n_hp)},
        "feature_list": CANONICAL_FEATURES,
    }
    with open(OUT_CANON / "cpcv_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out


# =====================================================================
# Config B — Per-regime v1 (17 features, ensemble)
# =====================================================================

def run_config_b(
    X_v1: pd.DataFrame, y: np.ndarray, dates: pd.Series,
    df_cohort: pd.DataFrame,
    folds: list[np.ndarray], paths: list[tuple[list, list]],
    v2_paths: list[dict],
) -> dict:
    """Per-regime ensemble: one LGBM per regime label. Routing at inference.

    Regime labels are taken from the v1 features CSV (regime_tag column),
    aligned to the v2 cohort. NaN -> '__missing__' (treated as UNTAGGED).
    """
    print("\n=== CONFIG B — Per-regime v1 (17 features, ensemble) ===")

    # Get regime labels per row in cohort order (string labels)
    v1_raw = pd.read_csv(V1_FEATURES_FULL)
    v1_raw["date_only"] = v1_raw["date_iso"].astype(str).str[:10]
    v1_raw["dedup_key"] = list(
        zip(
            v1_raw["date_only"],
            v1_raw["symbol"],
            v1_raw["direction_long_short"],
            v1_raw["framework"],
            v1_raw["realized_r"].round(3),
        )
    )
    v1d = v1_raw.drop_duplicates(subset="dedup_key", keep="first").copy()
    keys_df = pd.DataFrame({"dedup_key": df_cohort["dedup_key"].tolist()})
    aligned = keys_df.merge(v1d[["dedup_key", "regime_tag"]], on="dedup_key", how="left")
    regime_labels = aligned["regime_tag"].fillna("UNTAGGED").astype(str).values
    # Normalize: treat "" or NaN-string as UNTAGGED
    regime_labels = np.where(
        np.isin(regime_labels, ["nan", "", "None", "__missing__"]),
        "UNTAGGED",
        regime_labels,
    )
    unique_regimes = sorted(set(regime_labels))
    print(f"  Regime distribution: {dict(zip(*np.unique(regime_labels, return_counts=True)))}")
    print(f"  Unique regimes: {unique_regimes}")

    cpcv_results = []
    # Per-HP per-path AUC (whole-test-fold AUC after ensemble routing)
    hp_path_aucs: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}

    t0 = time.time()
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)

        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val_idx = train_sorted[-n_inner:]
        inner_train_idx = train_sorted[:-n_inner]

        regime_train = regime_labels[inner_train_idx]
        regime_val = regime_labels[inner_val_idx]
        regime_test = regime_labels[test_idx]

        X_tr_full = X_v1.iloc[inner_train_idx]
        X_iv_full = X_v1.iloc[inner_val_idx]
        X_te_full = X_v1.iloc[test_idx]
        y_tr_full = y[inner_train_idx]
        y_iv_full = y[inner_val_idx]
        y_te = y[test_idx]

        # Per-HP: train one global + one-per-regime; route by regime at inference
        path_aucs = []
        for hp_idx, hp in enumerate(HYPER_GRID):
            try:
                # Global fallback model
                m_global = train_lgbm(X_tr_full, y_tr_full, X_iv_full, y_iv_full, hp, len(inner_train_idx))
                p_iv_global = m_global.predict_proba(X_iv_full)[:, 1]
                p_te_global = m_global.predict_proba(X_te_full)[:, 1]
                p_te_global_cal = calibrate(p_iv_global, y_iv_full, p_te_global)

                # Per-regime models
                regime_models = {}
                regime_calibrators = {}
                for regime in unique_regimes:
                    mask_r = (regime_train == regime)
                    if mask_r.sum() < MIN_REGIME_ROWS:
                        # Fall back to global for this regime
                        regime_models[regime] = None
                        continue
                    X_tr_r = X_tr_full.iloc[mask_r]
                    y_tr_r = y_tr_full[mask_r]
                    # Use global inner_val rows for stopping (regime-specific val may be tiny)
                    mask_iv_r = (regime_val == regime)
                    if mask_iv_r.sum() >= 5 and len(np.unique(y_iv_full[mask_iv_r])) >= 2:
                        X_iv_r = X_iv_full.iloc[mask_iv_r]
                        y_iv_r = y_iv_full[mask_iv_r]
                    else:
                        X_iv_r, y_iv_r = X_iv_full, y_iv_full
                    try:
                        m_r = train_lgbm(X_tr_r, y_tr_r, X_iv_r, y_iv_r, hp, len(X_tr_r))
                        regime_models[regime] = m_r
                        # Per-regime calibrator on the full inner val
                        p_iv_r = m_r.predict_proba(X_iv_full)[:, 1]
                        regime_calibrators[regime] = (p_iv_r, y_iv_full)
                    except Exception:
                        regime_models[regime] = None

                # Route test predictions by regime
                p_te = np.zeros(len(test_idx))
                for k, ti in enumerate(test_idx):
                    r_te = regime_test[k]
                    m_r = regime_models.get(r_te)
                    if m_r is None:
                        # Fallback: global
                        p_te[k] = p_te_global_cal[k]
                    else:
                        p_raw = m_r.predict_proba(X_te_full.iloc[[k]])[:, 1][0]
                        # Calibrate using the per-regime calibrator's stored arrays
                        if r_te in regime_calibrators:
                            p_iv_r_arr, y_iv_arr = regime_calibrators[r_te]
                            p_iv_r_te_arr = m_r.predict_proba(X_te_full.iloc[[k]])[:, 1]
                            p_cal = calibrate(p_iv_r_arr, y_iv_arr, p_iv_r_te_arr)
                            p_te[k] = p_cal[0]
                        else:
                            p_te[k] = p_raw

                a = safe_auc(y_te, p_te)
            except Exception as e:
                a = float("nan")
                p_te = None
            path_aucs.append(a)
            hp_path_aucs[hp_idx].append(a)

        cpcv_results.append({
            "path": path_idx,
            "train_groups": list(train_groups),
            "test_groups": list(test_groups),
            "n_train_after_purge": int(len(inner_train_idx)),
            "n_inner_val": int(len(inner_val_idx)),
            "n_test": int(len(test_idx)),
            "test_idx": test_idx.tolist(),
            "y_te": y_te.tolist(),
            "regime_test_distribution": dict(zip(*np.unique(regime_test, return_counts=True))),
            "per_hp_oos_auc": [float(a) for a in path_aucs],
        })
        if path_idx % 3 == 0 or path_idx == len(paths) - 1:
            print(f"  [B] Path {path_idx+1}/{len(paths)} t={time.time()-t0:.1f}s")

    # Select fixed HP
    n_hp = len(HYPER_GRID)
    hp_mean = np.array([np.nanmean(hp_path_aucs[i]) for i in range(n_hp)])
    best_hp_idx = int(np.nanargmax(hp_mean))
    best_hp = HYPER_GRID[best_hp_idx]

    # Re-train at fixed HP, also collect per-regime AUCs (test-aggregated)
    fixed_results = []
    per_regime_predictions: dict[str, list] = {r: [] for r in unique_regimes}

    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)

        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val_idx = train_sorted[-n_inner:]
        inner_train_idx = train_sorted[:-n_inner]

        regime_train = regime_labels[inner_train_idx]
        regime_val = regime_labels[inner_val_idx]
        regime_test = regime_labels[test_idx]

        X_tr_full = X_v1.iloc[inner_train_idx]
        X_iv_full = X_v1.iloc[inner_val_idx]
        X_te_full = X_v1.iloc[test_idx]
        y_tr_full = y[inner_train_idx]
        y_iv_full = y[inner_val_idx]
        y_te = y[test_idx]

        m_global = train_lgbm(X_tr_full, y_tr_full, X_iv_full, y_iv_full, best_hp, len(inner_train_idx))
        p_iv_global = m_global.predict_proba(X_iv_full)[:, 1]
        p_te_global = m_global.predict_proba(X_te_full)[:, 1]
        p_te_global_cal = calibrate(p_iv_global, y_iv_full, p_te_global)

        regime_models = {}
        regime_calibrators = {}
        per_regime_train_n = {}
        for regime in unique_regimes:
            mask_r = (regime_train == regime)
            per_regime_train_n[regime] = int(mask_r.sum())
            if mask_r.sum() < MIN_REGIME_ROWS:
                regime_models[regime] = None
                continue
            X_tr_r = X_tr_full.iloc[mask_r]
            y_tr_r = y_tr_full[mask_r]
            mask_iv_r = (regime_val == regime)
            if mask_iv_r.sum() >= 5 and len(np.unique(y_iv_full[mask_iv_r])) >= 2:
                X_iv_r = X_iv_full.iloc[mask_iv_r]
                y_iv_r = y_iv_full[mask_iv_r]
            else:
                X_iv_r, y_iv_r = X_iv_full, y_iv_full
            try:
                m_r = train_lgbm(X_tr_r, y_tr_r, X_iv_r, y_iv_r, best_hp, len(X_tr_r))
                regime_models[regime] = m_r
                p_iv_r = m_r.predict_proba(X_iv_full)[:, 1]
                regime_calibrators[regime] = (p_iv_r, y_iv_full)
            except Exception:
                regime_models[regime] = None

        p_te = np.zeros(len(test_idx))
        used_global_count = 0
        for k, ti in enumerate(test_idx):
            r_te = regime_test[k]
            m_r = regime_models.get(r_te)
            if m_r is None:
                p_te[k] = p_te_global_cal[k]
                used_global_count += 1
            else:
                if r_te in regime_calibrators:
                    p_iv_r_arr, y_iv_arr = regime_calibrators[r_te]
                    p_iv_r_te_arr = m_r.predict_proba(X_te_full.iloc[[k]])[:, 1]
                    p_cal = calibrate(p_iv_r_arr, y_iv_arr, p_iv_r_te_arr)
                    p_te[k] = p_cal[0]
                else:
                    p_te[k] = m_r.predict_proba(X_te_full.iloc[[k]])[:, 1][0]

        auc_v1 = safe_auc(y_te, p_te)
        brier_v1 = brier_score_loss(y_te, p_te) if len(np.unique(y_te)) > 1 else float("nan")

        # v2 paired
        v2_path = v2_paths[path_idx]
        v2_test_idx = v2_path["test_idx"]
        v2_p = np.array(v2_path["p_v2_te"])
        v2_lookup = {ti: v2_p[i] for i, ti in enumerate(v2_test_idx)}
        p_v2_te = np.array([v2_lookup[ti] for ti in test_idx])
        auc_v2 = safe_auc(y_te, p_v2_te)
        auc_diff, p_delong = delong_paired_test(y_te, p_te, p_v2_te)

        # Per-regime test split AUC
        per_regime_test_auc = {}
        for regime in unique_regimes:
            mask_te_r = (regime_test == regime)
            if mask_te_r.sum() < 10 or len(np.unique(y_te[mask_te_r])) < 2:
                per_regime_test_auc[regime] = {
                    "n_test": int(mask_te_r.sum()),
                    "auc": None,
                    "below_min_n": True,
                }
            else:
                a_r = safe_auc(y_te[mask_te_r], p_te[mask_te_r])
                per_regime_test_auc[regime] = {
                    "n_test": int(mask_te_r.sum()),
                    "auc": float(a_r),
                    "below_min_n": False,
                }
            # accumulate predictions for whole-cohort per-regime AUC
            for k_in_te, k in enumerate(np.where(mask_te_r)[0]):
                per_regime_predictions[regime].append({
                    "path": path_idx,
                    "test_idx": int(test_idx[k]),
                    "y": int(y_te[k]),
                    "p": float(p_te[k]),
                })

        fixed_results.append({
            "path": path_idx,
            "n_test": int(len(test_idx)),
            "auc_v1_per_regime": float(auc_v1),
            "auc_v2": float(auc_v2),
            "auc_diff_v2_minus_v1": float(auc_v2 - auc_v1),
            "delong_p": float(p_delong),
            "brier_v1": float(brier_v1),
            "test_idx": test_idx.tolist(),
            "p_v1_te": p_te.tolist(),
            "y_te": y_te.tolist(),
            "n_used_global_fallback": int(used_global_count),
            "per_regime_train_n": per_regime_train_n,
            "per_regime_test_auc": per_regime_test_auc,
        })

    # Whole-cohort per-regime AUC (aggregate predictions across paths)
    per_regime_aggregate = {}
    for regime in unique_regimes:
        records = per_regime_predictions[regime]
        if len(records) < 30:
            per_regime_aggregate[regime] = {
                "n_predictions": len(records),
                "auc": None,
                "below_min_n": True,
            }
            continue
        # Average predictions per test_idx
        df_records = pd.DataFrame(records)
        agg = df_records.groupby("test_idx").agg({"y": "first", "p": "mean"}).reset_index()
        if len(agg) < 30 or len(np.unique(agg["y"])) < 2:
            per_regime_aggregate[regime] = {
                "n_predictions": len(agg),
                "auc": None,
                "below_min_n": True,
            }
            continue
        per_regime_aggregate[regime] = {
            "n_predictions": int(len(agg)),
            "auc": float(safe_auc(agg["y"].values, agg["p"].values)),
            "below_min_n": False,
        }

    # Summary
    diffs = np.array([r["auc_diff_v2_minus_v1"] for r in fixed_results])
    delong_ps = [r["delong_p"] for r in fixed_results]
    auc_v1_mean = float(np.nanmean([r["auc_v1_per_regime"] for r in fixed_results]))
    auc_v2_mean = float(np.nanmean([r["auc_v2"] for r in fixed_results]))
    diff_mean = float(np.nanmean(diffs))
    diff_std = float(np.nanstd(diffs, ddof=1))
    diff_se = diff_std / math.sqrt(len(diffs))
    diff_ci_lo = diff_mean - 1.96 * diff_se
    diff_ci_hi = diff_mean + 1.96 * diff_se
    p_combined_stouffer = stouffer_combine(delong_ps)
    p_combined_fisher = fisher_combine(delong_ps)
    gate_a_pass = (diff_mean >= 0.04) and (p_combined_stouffer < 0.01)

    summary = {
        "config": "B — per-regime v1 (17 features, ensemble)",
        "n_paths": len(paths),
        "K": CPCV_K,
        "N": CPCV_N,
        "purge_days": PURGE_DAYS,
        "embargo_days": EMBARGO_DAYS,
        "min_regime_rows": MIN_REGIME_ROWS,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "hp_mean_oos_auc_at_selected": float(hp_mean[best_hp_idx]),
        "auc_v1_per_regime_mean": auc_v1_mean,
        "auc_v2_mean": auc_v2_mean,
        "diff_mean_v2_minus_v1": diff_mean,
        "diff_std": diff_std,
        "diff_se": float(diff_se),
        "diff_95ci": [float(diff_ci_lo), float(diff_ci_hi)],
        "delong_p_per_path": delong_ps,
        "delong_p_combined_stouffer": p_combined_stouffer,
        "delong_p_combined_fisher": p_combined_fisher,
        "gate_a_threshold": "diff_mean >= 0.04 AND combined DeLong p < 0.01",
        "gate_a_pass": bool(gate_a_pass),
        "regime_label_distribution": {r: int((regime_labels == r).sum()) for r in unique_regimes},
        "per_regime_aggregate_auc": per_regime_aggregate,
        "computed_at": utc_now(),
    }
    print(f"  [B] Selected HP idx={best_hp_idx}: {best_hp}")
    print(f"  [B] auc_v1_mean={auc_v1_mean:.4f}, auc_v2_mean={auc_v2_mean:.4f}, "
          f"diff_mean={diff_mean:+.4f}, p_stouffer={p_combined_stouffer:.6f}, "
          f"PASS={gate_a_pass}")
    print(f"  [B] Per-regime aggregate AUC:")
    for r, v in per_regime_aggregate.items():
        print(f"      {r}: n={v['n_predictions']}, AUC={v['auc']}")

    # Fit final per-regime models on full cohort
    sort_perm = np.argsort(dates.values)
    n_inner = len(sort_perm) // 8
    inner_val_full = sort_perm[-n_inner:]
    inner_train_full = sort_perm[:-n_inner]
    regime_train_full = regime_labels[inner_train_full]
    regime_val_full = regime_labels[inner_val_full]

    final_models_saved = {}
    # Save global fallback
    m_global_final = train_lgbm(
        X_v1.iloc[inner_train_full], y[inner_train_full],
        X_v1.iloc[inner_val_full], y[inner_val_full],
        best_hp, len(inner_train_full),
    )
    m_global_final.booster_.save_model(str(OUT_REGIME / "regime_global_fallback.lgb"))
    final_models_saved["global_fallback"] = "regime_global_fallback.lgb"

    for regime in unique_regimes:
        mask_r = (regime_train_full == regime)
        if mask_r.sum() < MIN_REGIME_ROWS:
            final_models_saved[regime] = None
            continue
        X_tr_r = X_v1.iloc[inner_train_full].iloc[mask_r]
        y_tr_r = y[inner_train_full][mask_r]
        mask_iv_r = (regime_val_full == regime)
        if mask_iv_r.sum() >= 5 and len(np.unique(y[inner_val_full][mask_iv_r])) >= 2:
            X_iv_r = X_v1.iloc[inner_val_full].iloc[mask_iv_r]
            y_iv_r = y[inner_val_full][mask_iv_r]
        else:
            X_iv_r = X_v1.iloc[inner_val_full]
            y_iv_r = y[inner_val_full]
        try:
            m_r_final = train_lgbm(X_tr_r, y_tr_r, X_iv_r, y_iv_r, best_hp, len(X_tr_r))
            safe_label = regime.replace(" ", "_").replace("/", "_")
            m_r_final.booster_.save_model(str(OUT_REGIME / f"regime_{safe_label}.lgb"))
            final_models_saved[regime] = f"regime_{safe_label}.lgb"
        except Exception as e:
            final_models_saved[regime] = f"FAILED: {e}"

    out = {
        "summary": summary,
        "paths_per_hp": cpcv_results,
        "paths_fixed_hp": fixed_results,
        "hp_grid": HYPER_GRID,
        "hp_path_aucs": {i: hp_path_aucs[i] for i in range(n_hp)},
        "feature_list": CANONICAL_FEATURES,
        "final_models_saved": final_models_saved,
    }
    with open(OUT_REGIME / "cpcv_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return out


# =====================================================================
# Modeler-modified-v1 reference (re-run for symbol-attribution)
# =====================================================================

def run_modeler_modified_v1(
    df_cohort: pd.DataFrame, y: np.ndarray, dates: pd.Series,
    folds: list[np.ndarray], paths: list[tuple[list, list]],
) -> dict:
    """Re-run the MODELER's v1 baseline (15 features w/ symbol; framework dropped).

    Provides apples-to-apples confirmation of the modeler's auc_v1_mean=0.5120
    using THIS code path (not the modeler's). If we reproduce 0.5120 this
    confirms the v2 paired comparison is internally consistent and the only
    diff vs Config A is feature set (symbol added; framework + walk_level_signal +
    cross_instrument_xau_dir dropped).
    """
    print("\n=== MODELER-MODIFIED v1 (15 features w/ symbol; for symbol-attribution) ===")

    # Match modeler's prepare_v1_X exactly
    v1_raw = pd.read_csv(V1_FEATURES_FULL)
    v1_raw["date_only"] = v1_raw["date_iso"].astype(str).str[:10]
    v1_raw["dedup_key"] = list(
        zip(
            v1_raw["date_only"],
            v1_raw["symbol"],
            v1_raw["direction_long_short"],
            v1_raw["framework"],
            v1_raw["realized_r"].round(3),
        )
    )
    v1d = v1_raw.drop_duplicates(subset="dedup_key", keep="first").copy()
    keys_df = pd.DataFrame({"dedup_key": df_cohort["dedup_key"].tolist()})
    v1_aligned = keys_df.merge(v1d, on="dedup_key", how="left")

    num_cols = [
        "hour_utc", "day_of_week", "counter_direction_flag",
        "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
        "fvg_present", "touch_count", "ai_confidence",
    ]
    cat_cols = ["symbol", "instrument_class", "direction_long_short",
                "kill_zone", "setup_grade", "regime_tag"]

    encoded = pd.DataFrame(index=v1_aligned.index)
    for c in num_cols:
        encoded[c] = pd.to_numeric(v1_aligned[c], errors="coerce").fillna(-1).astype(float)
    for c in cat_cols:
        vals = v1_aligned[c].fillna("__missing__").astype(str)
        codes = vals.astype("category").cat.codes
        encoded[c] = codes.astype(int)

    X_v1_modifier = encoded
    print(f"  Modeler-modified v1: {X_v1_modifier.shape[1]} features")

    hp_path_aucs: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)
        train_dates = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        X_tr = X_v1_modifier.iloc[inner_train]
        X_iv = X_v1_modifier.iloc[inner_val]
        X_te = X_v1_modifier.iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        for hp_idx, hp in enumerate(HYPER_GRID):
            try:
                m = train_lgbm(X_tr, y_tr, X_iv, y_iv, hp, len(inner_train))
                p_iv = m.predict_proba(X_iv)[:, 1]
                p_te = m.predict_proba(X_te)[:, 1]
                p_te = calibrate(p_iv, y_iv, p_te)
                a = safe_auc(y_te, p_te)
            except Exception:
                a = float("nan")
            hp_path_aucs[hp_idx].append(a)

    # Use the SAME selected HP as v2 (idx=5: n_estimators=100, max_depth=5, lr=0.1)
    # to mirror the modeler's apples-to-apples comparison
    best_hp_idx = 5  # Per v2 meta.json
    best_hp = HYPER_GRID[best_hp_idx]
    auc_modeler_at_v2_hp = float(np.nanmean(hp_path_aucs[best_hp_idx]))

    # Also compute fixed-HP via independent selection on this matrix
    n_hp = len(HYPER_GRID)
    hp_mean = np.array([np.nanmean(hp_path_aucs[i]) for i in range(n_hp)])
    best_hp_idx_independent = int(np.nanargmax(hp_mean))

    print(f"  Modeler-modified v1: AUC at v2's HP idx 5 = {auc_modeler_at_v2_hp:.4f}")
    print(f"  (Modeler reported 0.5120 in cpcv_paired_results.json; "
          f"reproduces if matches.)")

    return {
        "auc_at_v2_hp": auc_modeler_at_v2_hp,
        "selected_hp_independent_idx": best_hp_idx_independent,
        "hp_mean_aucs": hp_mean.tolist(),
        "n_features": X_v1_modifier.shape[1],
    }


# =====================================================================
# Main
# =====================================================================

def main():
    print(f"=== Canonical K54 v1 Re-run — {utc_now()} ===")
    t_start = time.time()

    # Load cohort
    print("\n[1/5] Loading cohort + v2 paths...")
    df_cohort, y, dates = load_cohort()
    print(f"  Cohort: {len(df_cohort)} rows, max_date={df_cohort['__date'].max()}, win_rate={y.mean():.3f}")

    # Load v2's CPCV results to extract paired predictions
    with open(V2_CPCV, "r", encoding="utf-8") as f:
        v2_cpcv = json.load(f)
    v2_paths = v2_cpcv["paths_fixed_hp"]
    print(f"  Loaded {len(v2_paths)} v2 paths")

    # Build canonical v1 design matrix
    print("\n[2/5] Preparing canonical v1 design matrix (17 features)...")
    X_v1_canon = prepare_canonical_v1_X(df_cohort)
    print(f"  Shape: {X_v1_canon.shape}, cols: {list(X_v1_canon.columns)}")

    # Build CPCV folds + paths (must match v2 exactly)
    print("\n[3/5] Building CPCV folds + paths (matches v2)...")
    folds = time_indexed_folds(dates, CPCV_K)
    paths = cpcv_paths(folds, CPCV_N)
    print(f"  K={CPCV_K}, N={CPCV_N}, n_paths={len(paths)}")
    for i, fi in enumerate(folds):
        d = dates.iloc[fi]
        print(f"    Fold {i}: n={len(fi)}, dates {d.min().date()} -> {d.max().date()}")

    # Sanity: confirm v2's first path test_idx matches our folds
    v2_path0_test = sorted(v2_paths[0]["test_idx"])
    our_path0_test = sorted(np.concatenate([folds[i] for i in paths[0][1]]).tolist())
    assert v2_path0_test == our_path0_test, (
        f"CPCV split mismatch with v2!\n"
        f"  v2 path 0 test_idx (first 5): {v2_path0_test[:5]}\n"
        f"  our path 0 test_idx (first 5): {our_path0_test[:5]}"
    )
    print(f"  Splits match v2: confirmed.")

    # Config A
    print(f"\n[4/5] Running Config A (canonical v1 global)...")
    out_a = run_config_a(X_v1_canon, y, dates, folds, paths, v2_paths)

    # Config B
    print(f"\n[5/5] Running Config B (per-regime v1 ensemble)...")
    out_b = run_config_b(X_v1_canon, y, dates, df_cohort, folds, paths, v2_paths)

    # Bonus: modeler-modified v1 reproduction
    out_mod = run_modeler_modified_v1(df_cohort, y, dates, folds, paths)

    elapsed = time.time() - t_start
    print(f"\n=== DONE in {elapsed:.0f}s ===")

    # Build comparative report
    write_report(out_a, out_b, out_mod, elapsed)


def write_report(out_a: dict, out_b: dict, out_mod: dict, wall_seconds: float):
    sa = out_a["summary"]
    sb = out_b["summary"]
    modeler_v1_v2_meta_auc = 0.5119857072926994  # From v2 cpcv_paired_results.json
    modeler_v1_at_v2_hp = out_mod["auc_at_v2_hp"]
    canonical_a_auc = sa["auc_v1_canonical_mean"]
    canonical_b_auc = sb["auc_v1_per_regime_mean"]
    v2_auc = sa["auc_v2_mean"]

    # Symbol attribution: how much did adding `symbol` strengthen v1?
    symbol_attribution_estimate = canonical_a_auc - modeler_v1_v2_meta_auc

    # Per-path positive count
    pos_a = sum(1 for r in out_a["paths_fixed_hp"] if r["auc_diff_v2_minus_v1"] > 0)
    pos_b = sum(1 for r in out_b["paths_fixed_hp"] if r["auc_diff_v2_minus_v1"] > 0)

    md = f"""# Canonical K54 v1 Re-run — Comparative Report

**Computed:** {utc_now()}
**Wallclock:** {wall_seconds:.0f}s
**Cohort:** 528 rows (matches v2), max_date 2026-04-24, win_rate 0.580
**CPCV:** K={CPCV_K}, N={CPCV_N}, n_paths={CPCV_K * (CPCV_K - 1) * (CPCV_K - 2) * (CPCV_K - 3) // 24 if CPCV_N == 4 else len([1 for _ in combinations(range(CPCV_K), CPCV_N)])} (15 paths via C(6,2)), purge_days={PURGE_DAYS}, embargo_days={EMBARGO_DAYS}
**HP grid:** {len(HYPER_GRID)} combos, fixed-HP selection via mean OOS AUC across paths

---

## Section 1 — Headline numbers

| Configuration | n_features | Architecture | CPCV mean OOS AUC |
|---|---:|---|---:|
| **K54 v2** (modeler) | 1234 | Global LightGBM | **{v2_auc:.4f}** |
| **Modeler-modified v1** (15 feat w/ symbol) | 15 | Global LightGBM | **{modeler_v1_v2_meta_auc:.4f}** (v2 meta), {modeler_v1_at_v2_hp:.4f} (re-run) |
| **Config A — canonical v1** (17 feat, NO symbol) | 17 | Global LightGBM | **{canonical_a_auc:.4f}** |
| **Config B — per-regime v1** (17 feat, NO symbol) | 17 | Per-regime ensemble | **{canonical_b_auc:.4f}** |

---

## Section 2 — Comparison 1: Modeler-modified v1 vs canonical v1 (Config A)

**Question:** Did adding `symbol` to the modeler's v1 baseline strengthen v1 (narrowing the v2 gap)?

| Metric | Value |
|---|---:|
| Modeler-modified v1 (with `symbol`) | {modeler_v1_v2_meta_auc:.4f} |
| Canonical v1 Config A (no `symbol`) | {canonical_a_auc:.4f} |
| Δ (canonical − modeler-modified) | **{(canonical_a_auc - modeler_v1_v2_meta_auc):+.4f}** |
| Hypothesis verdict | {'**SUPPORTED** — adding `symbol` strengthened v1' if symbol_attribution_estimate < 0 else '**REFUTED** — adding `symbol` did NOT strengthen v1; canonical actually higher' if symbol_attribution_estimate > 0 else 'NEUTRAL'} |

**Symbol attribution:** {symbol_attribution_estimate:+.4f} AUC (positive = canonical without `symbol` is HIGHER).

---

## Section 3 — Comparison 2: Per-regime v1 (Config B) vs canonical v1 (Config A)

**Question:** Does the per-regime architecture preserve the +0.032 lift cited in K54 v1 audit?

| Metric | Value |
|---|---:|
| Config A — global | {canonical_a_auc:.4f} |
| Config B — per-regime ensemble | {canonical_b_auc:.4f} |
| Δ (B − A) | **{(canonical_b_auc - canonical_a_auc):+.4f}** |
| K54 v1 audit-cited lift | +0.032 (single time-walk-forward, n=94) |
| CPCV-honest verdict | {'**REPLICATES** — per-regime > global by ≥0.020' if (canonical_b_auc - canonical_a_auc) >= 0.020 else '**ATTENUATED** — lift smaller than +0.032 audit claim' if (canonical_b_auc - canonical_a_auc) > 0 else '**REVERSED** — per-regime < global'} |

### Per-regime AUC breakdown (Config B aggregate predictions)

| Regime | n predictions | AUC |
|---|---:|---:|
"""
    pra = sb["per_regime_aggregate_auc"]
    for r, v in pra.items():
        n_p = v["n_predictions"]
        auc_v = v["auc"]
        md += f"| {r} | {n_p} | {auc_v:.4f if auc_v is not None else 'NaN (below_min_n)'} |\n" if auc_v is not None else f"| {r} | {n_p} | NaN (below_min_n) |\n"

    md += f"""
### Regime label distribution (cohort)

"""
    for r, n in sb["regime_label_distribution"].items():
        md += f"- {r}: {n}\n"

    md += f"""

---

## Section 4 — Comparison 3: K54 v2 vs canonical v1 (Config A) — gate (a)

| Metric | Value |
|---|---:|
| auc_v2_mean | {sa['auc_v2_mean']:.4f} |
| auc_v1_canonical_mean | {sa['auc_v1_canonical_mean']:.4f} |
| Δ (v2 − canonical_v1) | **{sa['diff_mean_v2_minus_v1']:+.4f}** |
| 95% CI on diff | [{sa['diff_95ci'][0]:+.4f}, {sa['diff_95ci'][1]:+.4f}] |
| Combined DeLong p (Stouffer) | {sa['delong_p_combined_stouffer']:.6f} |
| Combined DeLong p (Fisher) | {sa['delong_p_combined_fisher']:.6f} |
| Per-path positive lift count | {pos_a}/{len(out_a['paths_fixed_hp'])} |
| **Gate (a) threshold** | diff_mean ≥ +0.04 AND combined p < 0.01 |
| **Gate (a) verdict (canonical baseline)** | **{'PASS' if sa['gate_a_pass'] else 'FAIL'}** |

### Comparison to modeler's gate (a)

The modeler's v1 baseline (modified, with `symbol`) reported:
- diff_mean = +0.0309
- combined Stouffer p = 0.001546
- gate (a) = FAIL (diff_mean < +0.04 even though p<0.01)

With the canonical v1 baseline (no `symbol`):
- diff_mean = **{sa['diff_mean_v2_minus_v1']:+.4f}**
- combined Stouffer p = **{sa['delong_p_combined_stouffer']:.6f}**
- gate (a) = **{'PASS' if sa['gate_a_pass'] else 'FAIL'}**

**Δ vs modeler's gate-a result:** {(sa['diff_mean_v2_minus_v1'] - 0.0309):+.4f} on diff_mean.

---

## Section 5 — Comparison 4: K54 v2 vs per-regime v1 (Config B)

| Metric | Value |
|---|---:|
| auc_v2_mean | {sb['auc_v2_mean']:.4f} |
| auc_v1_per_regime_mean | {sb['auc_v1_per_regime_mean']:.4f} |
| Δ (v2 − per_regime_v1) | **{sb['diff_mean_v2_minus_v1']:+.4f}** |
| 95% CI on diff | [{sb['diff_95ci'][0]:+.4f}, {sb['diff_95ci'][1]:+.4f}] |
| Combined DeLong p (Stouffer) | {sb['delong_p_combined_stouffer']:.6f} |
| Combined DeLong p (Fisher) | {sb['delong_p_combined_fisher']:.6f} |
| Per-path positive lift count | {pos_b}/{len(out_b['paths_fixed_hp'])} |
| **Gate (a) threshold** | diff_mean ≥ +0.04 AND combined p < 0.01 |
| **Gate (a) verdict (per-regime baseline)** | **{'PASS' if sb['gate_a_pass'] else 'FAIL'}** |

**If lift drops to ~0:** K54 v2 doesn't beat the proper-architecture v1.
**Observed:** {'lift ≈ 0 — K54 v2 does NOT beat the proper-architecture v1' if abs(sb['diff_mean_v2_minus_v1']) < 0.02 else 'lift {:+.4f} ({})'.format(sb['diff_mean_v2_minus_v1'], 'positive but below gate threshold' if 0 < sb['diff_mean_v2_minus_v1'] < 0.04 else 'PASS gate threshold' if sb['diff_mean_v2_minus_v1'] >= 0.04 else 'NEGATIVE')}

---

## Section 6 — Selected hyperparameters

| Config | n_estimators | max_depth | learning_rate | mean OOS AUC |
|---|---:|---:|---:|---:|
| Config A | {sa['selected_hp']['n_estimators']} | {sa['selected_hp']['max_depth']} | {sa['selected_hp']['learning_rate']} | {sa['hp_mean_oos_auc_at_selected']:.4f} |
| Config B | {sb['selected_hp']['n_estimators']} | {sb['selected_hp']['max_depth']} | {sb['selected_hp']['learning_rate']} | {sb['hp_mean_oos_auc_at_selected']:.4f} |
| K54 v2 (per meta) | 100 | 5 | 0.1 | 0.5429 |

---

## Section 7 — Per-path table (Config A canonical v1 vs v2)

| Path | n_test | AUC v1 (canonical) | AUC v2 | Δ | DeLong p |
|---:|---:|---:|---:|---:|---:|
"""
    for r in out_a["paths_fixed_hp"]:
        md += (f"| {r['path']} | {r['n_test']} | {r['auc_v1_canonical']:.4f} | "
               f"{r['auc_v2']:.4f} | {r['auc_diff_v2_minus_v1']:+.4f} | "
               f"{r['delong_p']:.4f} |\n")

    md += f"""

## Section 8 — Per-path table (Config B per-regime v1 vs v2)

| Path | n_test | AUC v1 (per-regime) | AUC v2 | Δ | DeLong p | n fallback to global |
|---:|---:|---:|---:|---:|---:|---:|
"""
    for r in out_b["paths_fixed_hp"]:
        md += (f"| {r['path']} | {r['n_test']} | {r['auc_v1_per_regime']:.4f} | "
               f"{r['auc_v2']:.4f} | {r['auc_diff_v2_minus_v1']:+.4f} | "
               f"{r['delong_p']:.4f} | {r['n_used_global_fallback']} |\n")

    md += f"""

---

## Section 9 — Final verdict on the K54 v2 Q1.3 modeler choice

The modeler dropped 3 canonical features (`framework`, `cross_instrument_xau_dir`,
`walk_level_signal`) and added `symbol` — net 15 features vs canonical 17.

- **Adding `symbol`** {'STRENGTHENED' if symbol_attribution_estimate < 0 else 'WEAKENED' if symbol_attribution_estimate > 0 else 'NEUTRAL EFFECT ON'} v1 by **{symbol_attribution_estimate:+.4f} AUC**.
- **Architectural:** the modeler used global single model. Per-regime ensemble
  delivers AUC {canonical_b_auc:.4f}, vs global {canonical_a_auc:.4f} (Δ {(canonical_b_auc - canonical_a_auc):+.4f}).
- **Gate (a) under canonical baseline:** {'PASS' if sa['gate_a_pass'] else 'FAIL'} (diff_mean={sa['diff_mean_v2_minus_v1']:+.4f}, p={sa['delong_p_combined_stouffer']:.4f}).
- **Gate (a) under per-regime baseline:** {'PASS' if sb['gate_a_pass'] else 'FAIL'} (diff_mean={sb['diff_mean_v2_minus_v1']:+.4f}, p={sb['delong_p_combined_stouffer']:.4f}).

---

## Section 10 — Outputs

- `research/ml_program/models/k54_v1_canonical/k54_v1_canonical.lgb` — Config A final model
- `research/ml_program/models/k54_v1_canonical/cpcv_results.json` — Config A per-path table
- `research/ml_program/models/k54_v1_per_regime/regime_*.lgb` — Config B per-regime models
- `research/ml_program/models/k54_v1_per_regime/regime_global_fallback.lgb` — global fallback for regimes <{MIN_REGIME_ROWS} train rows
- `research/ml_program/models/k54_v1_per_regime/cpcv_results.json` — Config B per-path table

---

*End of comparative report.*
"""

    with open(OUT_AUDIT / "canonical_v1_rerun.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\nReport written to {OUT_AUDIT / 'canonical_v1_rerun.md'}")


if __name__ == "__main__":
    main()
