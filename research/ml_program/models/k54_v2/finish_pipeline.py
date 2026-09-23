"""Complete the K54 v2 pipeline using cached CPCV results.

Runs (in this order):
1. PBO (gate b) — parallelized 27 HP × 15 paths IS train
2. Cross-instrument (gate d) — uses cached CPCV predictions
3. Final fit + top features + meta
4. Null distribution (gate e) — parallelized 1000 shuffles

This avoids re-running CPCV, which is already complete.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

import lightgbm as lgb

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
K54_V1_FEATURES = ROOT / "research/ml_program/models/k54_v1_features_full.csv"
OUT_DIR = ROOT / "research/ml_program/models/k54_v2"

DATA_CUTOFF = "2026-04-28"
RANDOM_SEED = 42
N_WORKERS = 8
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
B_NULL = 1000
HYPER_GRID = [
    {"n_estimators": ne, "max_depth": md, "learning_rate": lr}
    for ne in (100, 200, 400)
    for md in (3, 5, 7)
    for lr in (0.01, 0.05, 0.1)
]

GROUP_MAP = {
    "XAUUSD": "XAU_XAG",
    "XAGUSD": "XAU_XAG",
    "NAS100": "NAS_US30",
    "US30_CASH": "NAS_US30",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD_USDJPY",
    "USDJPY": "GBPUSD_USDJPY",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def family_of(col: str) -> str:
    if col.startswith("struct__"): return "structure"
    if col.startswith("vol__"): return "volatility"
    if col.startswith("micro__"): return "microstructure"
    if col.startswith("ts__"): return "time_session"
    if col.startswith("liq__"): return "liquidity"
    if col.startswith("reg__"): return "regime"
    return "unknown"


def apply_patch1_prune(feature_cols, df):
    drop_set = set()
    if "reg__regime_atr_h4_14" in feature_cols:
        drop_set.add("reg__regime_atr_h4_14")
    micro_fvg_count = [c for c in feature_cols if c.startswith("micro__fvg_") and "_count_" in c]
    for col in micro_fvg_count:
        body = col.replace("micro__fvg_", "")
        if "_count_" not in body:
            continue
        dir_tf_lb = body.split("_count_")
        if len(dir_tf_lb) != 2:
            continue
        direction = dir_tf_lb[0]
        tf_lb = dir_tf_lb[1]
        if "_lb" not in tf_lb:
            continue
        tf, lb = tf_lb.split("_lb", 1)
        tf_canonical = tf.upper() if tf in ("h1", "h4") else ("M15" if tf == "m15" else tf.upper())
        struct_partner = f"struct__{tf_canonical}__fvg_{direction}_count__lb{lb}"
        if struct_partner in feature_cols:
            drop_set.add(col)
        else:
            if tf == "h4":
                drop_set.add(col)
    return [c for c in feature_cols if c not in drop_set]


def time_indexed_folds(dates, k):
    sort_idx = np.argsort(dates.values)
    fold_size = len(sort_idx) // k
    folds = []
    for i in range(k):
        start = i * fold_size
        end = (i + 1) * fold_size if i < k - 1 else len(sort_idx)
        folds.append(sort_idx[start:end])
    return folds


def cpcv_paths(folds, n):
    k = len(folds)
    out = []
    for test_combo in combinations(range(k), n):
        train_combo = [i for i in range(k) if i not in test_combo]
        out.append((train_combo, list(test_combo)))
    return out


def purge_embargo(train_idx, test_idx_groups, dates, purge_days, embargo_days):
    train_dates = pd.to_datetime(dates.iloc[train_idx])
    keep_mask = pd.Series(True, index=train_idx)
    for tg in test_idx_groups:
        test_dates = pd.to_datetime(dates.iloc[tg])
        t_min = test_dates.min() - pd.Timedelta(days=purge_days)
        t_max = test_dates.max() + pd.Timedelta(days=embargo_days)
        in_zone = (train_dates >= t_min) & (train_dates <= t_max)
        keep_mask = keep_mask & ~in_zone.values
    return train_idx[keep_mask.values]


def safe_auc(y, p):
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


def train_lgbm(X_tr, y_tr, X_val, y_val, hp, n_train):
    """Train a LightGBM classifier with given hyperparameters."""
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
    fit_kw = {}
    if X_val is not None and len(X_val) > 0:
        fit_kw = {
            "eval_set": [(X_val, y_val)],
            "callbacks": [lgb.early_stopping(20, verbose=False)],
        }
    model.fit(X_tr, y_tr, **fit_kw)
    return model


def calibrate(p_tr, y_tr, p_te):
    if len(np.unique(y_tr)) < 2:
        return p_te
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(p_tr.reshape(-1, 1), y_tr)
    return cal.predict_proba(p_te.reshape(-1, 1))[:, 1]


# Worker functions for parallel exec
def pbo_worker(args):
    """Train one HP on one path's full train slice (IS), return AUC."""
    path_idx, hp_idx, X_arr, y, train_idx, hp = args
    try:
        m = lgb.LGBMClassifier(
            n_estimators=hp["n_estimators"],
            max_depth=hp["max_depth"],
            learning_rate=hp["learning_rate"],
            min_data_in_leaf=max(3, len(train_idx) // 30),
            num_leaves=2 ** hp["max_depth"],
            objective="binary",
            metric="auc",
            n_jobs=1,
            verbosity=-1,
            random_state=RANDOM_SEED,
            deterministic=True,
            force_row_wise=True,
        )
        X_tr = X_arr[train_idx]
        y_tr = y[train_idx]
        m.fit(X_tr, y_tr)
        p_is = m.predict_proba(X_tr)[:, 1]
        auc_is = safe_auc(y_tr, p_is)
    except Exception:
        auc_is = float("nan")
    return path_idx, hp_idx, auc_is


def shuffle_worker(args):
    """Run CPCV for one shuffle seed, return mean OOS AUC."""
    seed, X_arr, y, path_caches, hp = args
    rng = np.random.RandomState(seed)
    y_shuffled = rng.permutation(y)
    aucs = []
    for cache in path_caches:
        it = cache["inner_train"]
        iv = cache["inner_val"]
        te = cache["test_idx"]
        X_tr = X_arr[it]
        X_iv = X_arr[iv]
        X_te = X_arr[te]
        y_tr = y_shuffled[it]
        y_iv = y_shuffled[iv]
        y_te = y_shuffled[te]
        try:
            m = lgb.LGBMClassifier(
                n_estimators=hp["n_estimators"],
                max_depth=hp["max_depth"],
                learning_rate=hp["learning_rate"],
                min_data_in_leaf=max(3, len(it) // 30),
                num_leaves=2 ** hp["max_depth"],
                objective="binary",
                metric="auc",
                n_jobs=1,
                verbosity=-1,
                random_state=RANDOM_SEED,
                deterministic=True,
                force_row_wise=True,
            )
            m.fit(
                X_tr, y_tr,
                eval_set=[(X_iv, y_iv)],
                callbacks=[lgb.early_stopping(20, verbose=False)],
            )
            p_te = m.predict_proba(X_te)[:, 1]
            a = safe_auc(y_te, p_te)
        except Exception:
            a = float("nan")
        aucs.append(a)
    return seed, float(np.nanmean(aucs))


def main():
    print(f"=== Finish K54 v2 pipeline — {utc_now()} ===")
    t_start = time.time()

    # Load data + apply prune
    df = pd.read_parquet(SCOUT_PARQUET)
    df["dedup_key"] = list(
        zip(
            df["__date"].astype(str).str[:10],
            df["__symbol"],
            df["__direction"],
            df["__framework"],
            df["__realized_r"].round(3),
        )
    )
    feature_cols_raw = [c for c in df.columns if not c.startswith("__") and c != "dedup_key"]
    feature_cols = apply_patch1_prune(feature_cols_raw, df)
    print(f"Matrix: {len(df)} rows × {len(feature_cols)} features (post-prune)")

    y = df["__win_label"].astype(int).values
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    X = df[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan)
    X_arr = X.values
    print(f"X array: {X_arr.shape}")

    # CPCV folds + paths + caches
    folds = time_indexed_folds(dates, CPCV_K)
    paths = cpcv_paths(folds, CPCV_N)
    path_caches = []
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
        path_caches.append({
            "train_idx": train_idx,
            "inner_train": inner_train,
            "inner_val": inner_val,
            "test_idx": test_idx,
        })

    # Load existing CPCV results (already saved)
    with open(OUT_DIR / "cpcv_paired_results.json", encoding="utf-8") as f:
        cpcv = json.load(f)
    hp_path_aucs_v2_existing = {}
    # Reconstruct per-HP per-path OOS AUC by reading from cpcv path data
    # Actually cpcv stores only the per-path-best HP results. We need to re-run the
    # per-HP grid for OOS AUC. But that's the bulk of CPCV. Skip — instead, reconstruct
    # per-HP AUCs by training fresh in parallel below.

    # ===== STAGE A: Per-HP × per-path OOS AUC (for HP selection + PBO + null HP) =====
    # Build a flat list of (path_idx, hp_idx) jobs
    print(f"\n[1/4] Computing OOS AUC for {len(HYPER_GRID)} HPs × {len(paths)} paths (parallel)...")
    flat_jobs = []
    for path_idx, cache in enumerate(path_caches):
        for hp_idx, hp in enumerate(HYPER_GRID):
            flat_jobs.append((path_idx, hp_idx, cache, hp))
    print(f"  Total jobs: {len(flat_jobs)}")

    def oos_worker(args):
        path_idx, hp_idx, cache, hp = args
        it = cache["inner_train"]
        iv = cache["inner_val"]
        te = cache["test_idx"]
        try:
            m = lgb.LGBMClassifier(
                n_estimators=hp["n_estimators"],
                max_depth=hp["max_depth"],
                learning_rate=hp["learning_rate"],
                min_data_in_leaf=max(3, len(it) // 30),
                num_leaves=2 ** hp["max_depth"],
                objective="binary",
                metric="auc",
                n_jobs=1,
                verbosity=-1,
                random_state=RANDOM_SEED,
                deterministic=True,
                force_row_wise=True,
            )
            m.fit(
                X_arr[it], y[it],
                eval_set=[(X_arr[iv], y[iv])],
                callbacks=[lgb.early_stopping(20, verbose=False)],
            )
            p_iv = m.predict_proba(X_arr[iv])[:, 1]
            p_te = m.predict_proba(X_arr[te])[:, 1]
            p_te = calibrate(p_iv, y[iv], p_te)
            auc_oos = safe_auc(y[te], p_te)
        except Exception as e:
            auc_oos = float("nan")
        return path_idx, hp_idx, auc_oos

    t0 = time.time()
    oos_results = Parallel(n_jobs=N_WORKERS, backend="loky", verbose=10)(
        delayed(oos_worker)(j) for j in flat_jobs
    )
    print(f"  OOS computation done in {time.time()-t0:.0f}s")

    # Reconstruct per-HP OOS AUC tables
    n_hp = len(HYPER_GRID)
    hp_path_aucs_v2 = {i: [float("nan")] * len(paths) for i in range(n_hp)}
    for path_idx, hp_idx, auc in oos_results:
        hp_path_aucs_v2[hp_idx][path_idx] = auc

    hp_mean_aucs = np.array([np.nanmean(hp_path_aucs_v2[i]) for i in range(n_hp)])
    best_hp_idx = int(np.nanargmax(hp_mean_aucs))
    best_hp = HYPER_GRID[best_hp_idx]
    print(f"  Best HP: idx={best_hp_idx}, {best_hp}, mean OOS AUC = {hp_mean_aucs[best_hp_idx]:.4f}")

    # ===== STAGE A.5: Recompute gate (a) using FIXED selected HP (CPCV-honest) =====
    # The cpcv_paired_results.json from train_k54_v2.py used per-path HP selection
    # which inflates AUC_v2 by selection bias. Per de Prado AFML §7.4 + Bailey-LdP
    # PBO methodology, the correct paired evaluation uses a SINGLE HP (selected via
    # CPCV mean) on all paths. Re-run gate (a) with the fixed selected HP.
    print(f"\n[1.5/4] Recomputing gate (a) with fixed selected HP {best_hp} (CPCV-honest)...")
    # For paired comparison, train V2 + V1 on SAME inner train/val splits using the
    # selected HP from V2 (V1 baseline reuses the same HP for fairness; it's a
    # simpler model so HP selection from V2 is conservative for V1).
    # Build V1 features for paired comparison
    v1_full = pd.read_csv(K54_V1_FEATURES)
    v1_full["date_only"] = v1_full["date_iso"].astype(str).str[:10]
    v1_full["dedup_key"] = list(zip(
        v1_full["date_only"], v1_full["symbol"], v1_full["direction_long_short"],
        v1_full["framework"], v1_full["realized_r"].round(3),
    ))
    v1_dedup = v1_full.drop_duplicates(subset="dedup_key", keep="first")
    keys_df = pd.DataFrame({"dedup_key": df["dedup_key"].tolist()})
    v1_aligned_a = keys_df.merge(v1_dedup, on="dedup_key", how="left")
    num_cols_a = ["hour_utc", "day_of_week", "counter_direction_flag", "ob_distance_atr",
                  "ob_age_candles", "displacement_quality_score", "fvg_present", "touch_count", "ai_confidence"]
    cat_cols_a = ["symbol", "instrument_class", "direction_long_short", "kill_zone", "setup_grade", "regime_tag"]
    enc_a = pd.DataFrame(index=v1_aligned_a.index)
    for c in num_cols_a:
        enc_a[c] = pd.to_numeric(v1_aligned_a[c], errors="coerce").fillna(-1).astype(float)
    for c in cat_cols_a:
        vals = v1_aligned_a[c].fillna("__missing__").astype(str)
        enc_a[c] = vals.astype("category").cat.codes.astype(int)
    X_v1_arr = enc_a.values

    paired_jobs = [(p_idx, cache, best_hp, X_arr, X_v1_arr, y) for p_idx, cache in enumerate(path_caches)]

    def paired_worker(args):
        p_idx, cache, hp, Xv2, Xv1, ylocal = args
        it = cache["inner_train"]; iv = cache["inner_val"]; te = cache["test_idx"]
        try:
            m_v2 = lgb.LGBMClassifier(
                n_estimators=hp["n_estimators"], max_depth=hp["max_depth"],
                learning_rate=hp["learning_rate"],
                min_data_in_leaf=max(3, len(it) // 30),
                num_leaves=2 ** hp["max_depth"],
                objective="binary", metric="auc", n_jobs=1, verbosity=-1,
                random_state=RANDOM_SEED, deterministic=True, force_row_wise=True,
            )
            m_v2.fit(Xv2[it], ylocal[it], eval_set=[(Xv2[iv], ylocal[iv])],
                     callbacks=[lgb.early_stopping(20, verbose=False)])
            piv2 = m_v2.predict_proba(Xv2[iv])[:, 1]
            pv2 = m_v2.predict_proba(Xv2[te])[:, 1]
            pv2 = calibrate(piv2, ylocal[iv], pv2)
            auc_v2 = safe_auc(ylocal[te], pv2)
            brier_v2 = brier_score_loss(ylocal[te], pv2) if len(np.unique(ylocal[te])) > 1 else float("nan")
        except Exception:
            pv2 = None; auc_v2 = float("nan"); brier_v2 = float("nan")
        try:
            m_v1 = lgb.LGBMClassifier(
                n_estimators=hp["n_estimators"], max_depth=hp["max_depth"],
                learning_rate=hp["learning_rate"],
                min_data_in_leaf=max(3, len(it) // 30),
                num_leaves=2 ** hp["max_depth"],
                objective="binary", metric="auc", n_jobs=1, verbosity=-1,
                random_state=RANDOM_SEED, deterministic=True, force_row_wise=True,
            )
            m_v1.fit(Xv1[it], ylocal[it], eval_set=[(Xv1[iv], ylocal[iv])],
                     callbacks=[lgb.early_stopping(20, verbose=False)])
            piv1 = m_v1.predict_proba(Xv1[iv])[:, 1]
            pv1 = m_v1.predict_proba(Xv1[te])[:, 1]
            pv1 = calibrate(piv1, ylocal[iv], pv1)
            auc_v1 = safe_auc(ylocal[te], pv1)
            brier_v1 = brier_score_loss(ylocal[te], pv1) if len(np.unique(ylocal[te])) > 1 else float("nan")
        except Exception:
            pv1 = None; auc_v1 = float("nan"); brier_v1 = float("nan")
        return p_idx, te, auc_v2, auc_v1, brier_v2, brier_v1, (pv2.tolist() if pv2 is not None else None), (pv1.tolist() if pv1 is not None else None)

    paired_results_raw = Parallel(n_jobs=N_WORKERS, backend="loky", verbose=0)(
        delayed(paired_worker)(j) for j in paired_jobs
    )
    paired_results_raw.sort(key=lambda r: r[0])

    # DeLong p-values (need proper paired comparison)
    from scipy import stats as _stats
    def midrank(x):
        order = np.argsort(x); x_sorted = x[order]
        n = len(x); T = np.zeros(n); i = 0
        while i < n:
            j = i
            while j < n and x_sorted[j] == x_sorted[i]:
                j += 1
            T[i:j] = 0.5 * (i + j - 1) + 1
            i = j
        T2 = np.empty(n); T2[order] = T
        return T2
    def delong_paired(yloc, p1, p2):
        yloc = np.asarray(yloc); p1 = np.asarray(p1); p2 = np.asarray(p2)
        if len(np.unique(yloc)) < 2:
            return float("nan"), float("nan")
        pos = yloc == 1; neg = yloc == 0
        n_p = int(pos.sum()); n_n = int(neg.sum())
        if n_p < 2 or n_n < 2:
            return float("nan"), float("nan")
        p_mat = np.stack([p1, p2])
        p_pos = p_mat[:, pos]; p_neg = p_mat[:, neg]
        tx = np.zeros((2, n_p)); ty = np.zeros((2, n_n)); tz = np.zeros((2, n_p + n_n))
        for r in range(2):
            tx[r] = midrank(p_pos[r])
            ty[r] = midrank(p_neg[r])
            tz[r] = midrank(np.concatenate([p_pos[r], p_neg[r]]))
        aucs = (tz[:, :n_p].sum(axis=1) / n_p - (n_p + 1) / 2.0) / n_n
        v01 = (tz[:, :n_p] - tx) / n_n
        v10 = 1.0 - (tz[:, n_p:] - ty) / n_p
        sx = np.cov(v01, ddof=1) if v01.shape[0] > 1 else np.atleast_2d(np.var(v01, ddof=1))
        sy = np.cov(v10, ddof=1) if v10.shape[0] > 1 else np.atleast_2d(np.var(v10, ddof=1))
        if sx.ndim == 0: sx = np.atleast_2d(sx)
        if sy.ndim == 0: sy = np.atleast_2d(sy)
        cov_m = sx / n_p + sy / n_n
        diff = float(aucs[1] - aucs[0])
        L = np.array([-1.0, 1.0])
        var = float(L @ cov_m @ L)
        if var <= 0 or not np.isfinite(var):
            return diff, float("nan")
        z = diff / math.sqrt(var)
        p_two = 2.0 * (1.0 - _stats.norm.cdf(abs(z)))
        return diff, float(p_two)

    new_paths = []
    for p_idx, te, auc_v2, auc_v1, brier_v2, brier_v1, pv2_list, pv1_list in paired_results_raw:
        if pv1_list is None or pv2_list is None:
            new_paths.append({
                "path": p_idx,
                "n_test": len(te),
                "auc_v2": float(auc_v2), "auc_v1": float(auc_v1),
                "auc_diff": float(auc_v2 - auc_v1) if not (math.isnan(auc_v2) or math.isnan(auc_v1)) else float("nan"),
                "delong_p": float("nan"),
                "brier_v2": float(brier_v2), "brier_v1": float(brier_v1),
                "test_idx": te.tolist(),
                "p_v2_te": pv2_list, "p_v1_te": pv1_list,
                "y_te": y[te].tolist(),
            })
            continue
        diff, dp = delong_paired(y[te], pv1_list, pv2_list)
        new_paths.append({
            "path": p_idx,
            "n_test": len(te),
            "auc_v2": float(auc_v2), "auc_v1": float(auc_v1),
            "auc_diff": float(auc_v2 - auc_v1),
            "delong_p": float(dp),
            "brier_v2": float(brier_v2), "brier_v1": float(brier_v1),
            "test_idx": te.tolist(),
            "p_v2_te": pv2_list, "p_v1_te": pv1_list,
            "y_te": y[te].tolist(),
        })

    # Recompute summary
    diffs = np.array([r["auc_diff"] for r in new_paths])
    delong_ps_list = [r["delong_p"] for r in new_paths]
    valid_dp = [p for p in delong_ps_list if p is not None and not math.isnan(p) and 0 < p < 1]
    if valid_dp:
        z_st = [_stats.norm.ppf(1 - p) for p in valid_dp]
        z_combined = sum(z_st) / math.sqrt(len(z_st))
        p_st = float(1 - _stats.norm.cdf(z_combined))
        chi2 = -2 * sum(math.log(p) for p in valid_dp)
        dfree = 2 * len(valid_dp)
        p_fi = float(1 - _stats.chi2.cdf(chi2, dfree))
    else:
        p_st = float("nan"); p_fi = float("nan")
    auc_v2_mean_new = float(np.nanmean([r["auc_v2"] for r in new_paths]))
    auc_v1_mean_new = float(np.nanmean([r["auc_v1"] for r in new_paths]))
    diff_mean_new = float(np.nanmean(diffs))
    diff_std_new = float(np.nanstd(diffs, ddof=1))
    diff_se = diff_std_new / math.sqrt(len(diffs))
    diff_ci = [float(diff_mean_new - 1.96 * diff_se), float(diff_mean_new + 1.96 * diff_se)]
    p_bonf_new = float(np.nanmin(delong_ps_list) * len(delong_ps_list)) if valid_dp else float("nan")
    gate_a_pass_new = (diff_mean_new >= 0.04) and (p_st < 0.01)

    new_cpcv_summary = {
        "method_v2": "Fixed selected HP across all 15 CPCV paths (CPCV-honest; per-path HP selection bias removed). Selected HP via CPCV mean OOS AUC.",
        "n_paths": len(new_paths),
        "K": CPCV_K, "N": CPCV_N,
        "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "auc_v2_mean": auc_v2_mean_new,
        "auc_v1_mean": auc_v1_mean_new,
        "diff_mean": diff_mean_new,
        "diff_std": diff_std_new,
        "diff_se": float(diff_se),
        "diff_95ci": diff_ci,
        "delong_p_per_path": delong_ps_list,
        "delong_p_combined_stouffer": p_st,
        "delong_p_combined_fisher": p_fi,
        "delong_p_min_bonferroni": p_bonf_new,
        "gate_a_threshold": "diff_mean >= 0.04 AND combined DeLong p < 0.01",
        "gate_a_pass": bool(gate_a_pass_new),
        "computed_at": utc_now(),
    }
    # Save BOTH the original (per-path-HP) and the new fixed-HP version
    cpcv_combined = {
        "summary_fixed_hp_recommended": new_cpcv_summary,
        "summary_per_path_hp_overoptimistic": cpcv["summary"],
        "paths_fixed_hp": new_paths,
        "paths_per_path_hp": cpcv["paths"],
        "fold_meta": cpcv.get("fold_meta", []),
        "note": "Use summary_fixed_hp_recommended for Q1.3 gate (a) verdict. The per-path HP variant is statistically biased upward by selection.",
    }
    with open(OUT_DIR / "cpcv_paired_results.json", "w", encoding="utf-8") as f:
        json.dump(cpcv_combined, f, indent=2)
    print(f"  Fixed-HP gate (a): diff_mean={diff_mean_new:+.4f}, p_combined={p_st:.6f}, PASS={gate_a_pass_new}")
    print(f"  (Earlier per-path-HP variant had inflated diff_mean=+0.0652 due to selection bias.)")

    # Use new predictions for cross-instrument
    pred_v2_paired = np.full(len(df), np.nan)
    pred_v1_paired = np.full(len(df), np.nan)
    pcount_p = np.zeros(len(df), dtype=int)
    for r in new_paths:
        if r["p_v2_te"] is None: continue
        for k, ti in enumerate(r["test_idx"]):
            cur2 = pred_v2_paired[ti] if not np.isnan(pred_v2_paired[ti]) else 0.0
            cur1 = pred_v1_paired[ti] if not np.isnan(pred_v1_paired[ti]) else 0.0
            pred_v2_paired[ti] = cur2 + r["p_v2_te"][k]
            pred_v1_paired[ti] = cur1 + r["p_v1_te"][k]
            pcount_p[ti] += 1
    pred_v2_paired = pred_v2_paired / np.maximum(pcount_p, 1)
    pred_v1_paired = pred_v1_paired / np.maximum(pcount_p, 1)
    pred_v2 = pred_v2_paired
    pred_v1 = pred_v1_paired

    # ===== STAGE B: PBO IS AUCs =====
    print(f"\n[2/4] PBO: in-sample AUC for {n_hp} HPs × {len(paths)} paths (parallel)...")
    pbo_jobs = []
    for path_idx, cache in enumerate(path_caches):
        for hp_idx, hp in enumerate(HYPER_GRID):
            pbo_jobs.append((path_idx, hp_idx, X_arr, y, cache["train_idx"], hp))
    t0 = time.time()
    pbo_results = Parallel(n_jobs=N_WORKERS, backend="loky", verbose=10)(
        delayed(pbo_worker)(j) for j in pbo_jobs
    )
    print(f"  PBO IS computation done in {time.time()-t0:.0f}s")

    hp_is_aucs = {i: [float("nan")] * len(paths) for i in range(n_hp)}
    for path_idx, hp_idx, auc in pbo_results:
        hp_is_aucs[hp_idx][path_idx] = auc

    # Compute PBO
    pbo_below_median = 0
    pbo_path_records = []
    for path_idx in range(len(paths)):
        is_aucs = np.array([hp_is_aucs[h][path_idx] for h in range(n_hp)])
        oos_aucs = np.array([hp_path_aucs_v2[h][path_idx] for h in range(n_hp)])
        if np.all(np.isnan(is_aucs)) or np.all(np.isnan(oos_aucs)):
            continue
        is_aucs_clean = np.where(np.isnan(is_aucs), -1.0, is_aucs)
        oos_aucs_clean = np.where(np.isnan(oos_aucs), -1.0, oos_aucs)
        is_best_hp = int(np.argmax(is_aucs_clean))
        oos_ranks = np.argsort(np.argsort(oos_aucs_clean))
        is_best_oos_rank = int(oos_ranks[is_best_hp])
        oos_median_rank = (n_hp - 1) / 2.0
        below_median = is_best_oos_rank < oos_median_rank
        if below_median:
            pbo_below_median += 1
        pbo_path_records.append({
            "path": path_idx,
            "is_best_hp_idx": is_best_hp,
            "is_best_hp": HYPER_GRID[is_best_hp],
            "is_best_oos_rank": is_best_oos_rank,
            "n_hp": n_hp,
            "below_median": bool(below_median),
        })

    pbo = pbo_below_median / len(pbo_path_records) if pbo_path_records else float("nan")
    gate_b_pass = pbo < 0.5
    pbo_summary = {
        "method": "Bailey & López de Prado (2014) PBO; combinatorial CPCV paths used as S splits; below-median rank metric",
        "n_splits": len(pbo_path_records),
        "n_hp_grid": n_hp,
        "pbo": float(pbo),
        "below_median_count": int(pbo_below_median),
        "gate_b_threshold": "PBO < 0.5",
        "gate_b_pass": bool(gate_b_pass),
        "path_records": pbo_path_records,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "pbo_results.json", "w", encoding="utf-8") as f:
        json.dump(pbo_summary, f, indent=2)
    print(f"  PBO = {pbo:.4f}, PASS = {gate_b_pass}")

    # ===== STAGE C: Cross-instrument & final fit =====
    # Cross-instrument: use predictions from FIXED-HP CPCV (CPCV-honest)
    print(f"\n[3/4] Cross-instrument validation (gate d)...")

    df["__group"] = df["__symbol"].map(GROUP_MAP).fillna("residual")
    cross_results = {}
    for grp, sub in df.groupby("__group"):
        idx = sub.index.values
        y_grp = y[idx]
        pv2 = pred_v2[idx]
        pv1 = pred_v1[idx]
        valid = ~(np.isnan(pv2) | np.isnan(pv1))
        if valid.sum() < 30:
            cross_results[grp] = {
                "n": int(valid.sum()),
                "auc_v2": None, "auc_v1": None, "auc_diff": None,
                "lift_sign_positive": None,
                "below_min_n": True,
            }
            continue
        a2 = safe_auc(y_grp[valid], pv2[valid])
        a1 = safe_auc(y_grp[valid], pv1[valid])
        cross_results[grp] = {
            "n": int(valid.sum()),
            "auc_v2": float(a2) if not math.isnan(a2) else None,
            "auc_v1": float(a1) if not math.isnan(a1) else None,
            "auc_diff": float(a2 - a1) if not (math.isnan(a2) or math.isnan(a1)) else None,
            "lift_sign_positive": (a2 > a1) if not (math.isnan(a2) or math.isnan(a1)) else None,
            "below_min_n": False,
        }

    n_pass = sum(1 for v in cross_results.values() if v["lift_sign_positive"] and not v["below_min_n"])
    n_eligible = sum(1 for v in cross_results.values() if not v["below_min_n"])
    gate_d_pass = n_pass >= 3
    cross_summary = {
        "method": "Aggregate OOS CPCV predictions (mean across paths), per-group AUC v2 vs v1",
        "groups": cross_results,
        "n_groups_pass": int(n_pass),
        "n_groups_eligible": int(n_eligible),
        "gate_d_threshold": "AUC_v2 > AUC_v1 on >=3 of 5 effective-independent groups (n>=30)",
        "gate_d_pass": bool(gate_d_pass),
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "cross_instrument_results.json", "w", encoding="utf-8") as f:
        json.dump(cross_summary, f, indent=2)
    for grp, v in cross_results.items():
        marker = "PASS" if v["lift_sign_positive"] else ("BELOW_N" if v["below_min_n"] else "FAIL")
        print(f"  {grp}: n={v['n']}, AUC_v2={v['auc_v2']}, AUC_v1={v['auc_v1']}, diff={v['auc_diff']} [{marker}]")
    print(f"  Gate (d): {n_pass}/{n_eligible} groups positive lift, PASS = {gate_d_pass}")

    # Final fit
    print(f"\n  Fitting final K54 v2 + V1 baseline on full cohort...")

    # Build V1 features
    v1 = pd.read_csv(K54_V1_FEATURES)
    v1["date_only"] = v1["date_iso"].astype(str).str[:10]
    v1["dedup_key"] = list(zip(v1["date_only"], v1["symbol"], v1["direction_long_short"], v1["framework"], v1["realized_r"].round(3)))
    v1d = v1.drop_duplicates(subset="dedup_key", keep="first")
    keys_df = pd.DataFrame({"dedup_key": df["dedup_key"].tolist()})
    v1_aligned = keys_df.merge(v1d, on="dedup_key", how="left")
    num_cols = ["hour_utc", "day_of_week", "counter_direction_flag", "ob_distance_atr",
                "ob_age_candles", "displacement_quality_score", "fvg_present", "touch_count", "ai_confidence"]
    cat_cols = ["symbol", "instrument_class", "direction_long_short", "kill_zone", "setup_grade", "regime_tag"]
    encoded = pd.DataFrame(index=v1_aligned.index)
    for c in num_cols:
        encoded[c] = pd.to_numeric(v1_aligned[c], errors="coerce").fillna(-1).astype(float)
    for c in cat_cols:
        vals = v1_aligned[c].fillna("__missing__").astype(str)
        codes = vals.astype("category").cat.codes
        encoded[c] = codes.astype(int)
    X_v1 = encoded

    sort_perm = np.argsort(dates.values)
    n_inner = len(sort_perm) // 8
    inner_val = sort_perm[-n_inner:]
    inner_train = sort_perm[:-n_inner]

    final_v2 = train_lgbm(X.iloc[inner_train], y[inner_train], X.iloc[inner_val], y[inner_val], best_hp, len(inner_train))
    final_v1 = train_lgbm(X_v1.iloc[inner_train], y[inner_train], X_v1.iloc[inner_val], y[inner_val], best_hp, len(inner_train))
    final_v2.booster_.save_model(str(OUT_DIR / "k54_v2.lgb"))
    final_v1.booster_.save_model(str(OUT_DIR / "k54_v1_baseline.lgb"))
    importances = final_v2.feature_importances_
    feat_imp = sorted(
        [(feature_cols[i], float(importances[i])) for i in range(len(feature_cols))],
        key=lambda x: x[1], reverse=True,
    )
    top30 = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in feat_imp[:30]]

    per_group_top10 = {}
    for grp, sub in df.groupby("__group"):
        idx_grp = sub.index.values
        if len(idx_grp) < 30:
            continue
        try:
            m_g = train_lgbm(X.iloc[idx_grp], y[idx_grp], None, None, best_hp, len(idx_grp))
            imp = m_g.feature_importances_
            grp_imp = sorted(
                [(feature_cols[i], float(imp[i])) for i in range(len(feature_cols))],
                key=lambda x: x[1], reverse=True,
            )
            per_group_top10[grp] = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in grp_imp[:10]]
        except Exception as e:
            per_group_top10[grp] = [{"error": str(e)}]
    with open(OUT_DIR / "top_features.json", "w", encoding="utf-8") as f:
        json.dump({
            "selected_hp_idx": best_hp_idx,
            "selected_hp": best_hp,
            "cpcv_mean_auc_at_selected_hp": float(hp_mean_aucs[best_hp_idx]),
            "top30_global": top30,
            "per_group_top10": per_group_top10,
            "computed_at": utc_now(),
        }, f, indent=2)
    print(f"  Top 5 features: {[t['feature'] for t in top30[:5]]}")

    # Save training_log + meta
    with open(OUT_DIR / "training_log.json", "w", encoding="utf-8") as f:
        json.dump({
            "hp_grid": HYPER_GRID,
            "hp_path_aucs_v2": hp_path_aucs_v2,
            "hp_is_aucs_v2": hp_is_aucs,
            "hp_mean_oos_aucs_v2": hp_mean_aucs.tolist(),
            "selected_hp_idx": best_hp_idx,
            "computed_at": utc_now(),
        }, f, indent=2)

    cohort_max_date = str(df["__date"].max())[:10]
    meta = {
        "k54_version": "v2",
        "training_spec": {
            "data_cutoff_utc": DATA_CUTOFF,
            "cohort_size": int(len(df)),
            "cohort_max_date": cohort_max_date,
            "n_features_post_prune": int(len(feature_cols)),
            "regime_as_feature": True,
            "regime_features_present": sorted([c for c in feature_cols if c.startswith("reg__")])[:20],
            "v1_baseline_features": list(X_v1.columns),
            "v1_baseline_n_features": int(X_v1.shape[1]),
            "framework_dropped_in_v1_per_op_filter_1": True,
        },
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "selected_hp_cpcv_mean_oos_auc": float(hp_mean_aucs[best_hp_idx]),
        "cpcv_config": {
            "K": CPCV_K, "N": CPCV_N, "n_paths": len(paths),
            "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS,
        },
        "pbo_config": {"n_hp_grid": n_hp, "splits": len(pbo_path_records)},
        "null_config": {"B": B_NULL},
        "code_revisions": {
            "k54_v1_commit": "af5d97e",
            "scout_matrix": str(SCOUT_PARQUET),
        },
        "wallclock_seconds_so_far": time.time() - t_start,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # ===== STAGE D: Null distribution =====
    print(f"\n[4/4] Null distribution: B={B_NULL} shuffles, parallel {N_WORKERS} workers...")
    print(f"  Per-shuffle: 15 LightGBM trains. Total: {B_NULL * 15} trains.")
    null_jobs = [(seed, X_arr, y, path_caches, best_hp) for seed in range(1, B_NULL + 1)]

    null_aucs = []
    chunk = 50
    for batch_start in range(0, len(null_jobs), chunk):
        batch = null_jobs[batch_start:batch_start + chunk]
        t0 = time.time()
        results = Parallel(n_jobs=N_WORKERS, backend="loky", verbose=0)(
            delayed(shuffle_worker)(j) for j in batch
        )
        for s, a in sorted(results, key=lambda r: r[0]):
            null_aucs.append(a)
        elapsed = time.time() - t0
        total = time.time() - t_start
        est_remaining = ((time.time() - t_start) - (t_start - t_start)) * (B_NULL - len(null_aucs)) / max(len(null_aucs), 1)
        print(f"  Shuffles {len(null_aucs)}/{B_NULL}: batch in {elapsed:.0f}s, total {total:.0f}s")

    null_aucs_arr = np.array(null_aucs)
    obs_auc = cpcv["summary"]["auc_v2_mean"]
    p_empirical = float(np.mean(null_aucs_arr >= obs_auc))
    p99 = float(np.percentile(null_aucs_arr, 99))
    p999 = float(np.percentile(null_aucs_arr, 99.9))
    p_smoothed = float((np.sum(null_aucs_arr >= obs_auc) + 1) / (len(null_aucs_arr) + 1))
    z_score = float((obs_auc - np.mean(null_aucs_arr)) / np.std(null_aucs_arr)) if np.std(null_aucs_arr) > 0 else float("nan")
    gate_e_pass = (obs_auc >= p99) and (p_empirical < 0.01)

    null_summary = {
        "B": B_NULL,
        "method": "Per shuffle: permute labels with seed; rerun CPCV K=6,N=2 with selected HP; report mean OOS AUC. Parallelized 8 workers via joblib.",
        "n_shuffles_completed": len(null_aucs),
        "obs_auc_v2": float(obs_auc),
        "null_mean": float(np.mean(null_aucs_arr)),
        "null_std": float(np.std(null_aucs_arr)),
        "null_min": float(np.min(null_aucs_arr)),
        "null_max": float(np.max(null_aucs_arr)),
        "p_empirical_one_sided": p_empirical,
        "p_smoothed": p_smoothed,
        "p99_boundary": p99,
        "p999_boundary": p999,
        "z_score": z_score,
        "gate_e_threshold": "obs AUC >= 99th percentile of null AND p_empirical < 0.01",
        "gate_e_pass": bool(gate_e_pass),
        "null_aucs": null_aucs,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "null_distribution.json", "w", encoding="utf-8") as f:
        json.dump(null_summary, f, indent=2)
    print(f"  Null: obs={obs_auc:.4f}, mean={np.mean(null_aucs_arr):.4f}, p99={p99:.4f}, p_emp={p_empirical:.4f}")
    print(f"  GATE (e) PASS: {gate_e_pass}")

    # Update meta wallclock
    meta["wallclock_total_seconds"] = time.time() - t_start
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n=== finish_pipeline.py DONE in {time.time()-t_start:.0f}s ===")
    print(f"\nQ1.3 GATE VERDICTS:")
    print(f"  (a) CPCV paired: {cpcv['summary']['gate_a_pass']} (already saved)")
    print(f"  (b) PBO: {gate_b_pass}")
    print(f"  (d) Cross-instrument: {gate_d_pass}")
    print(f"  (e) Null: {gate_e_pass}")


if __name__ == "__main__":
    main()
