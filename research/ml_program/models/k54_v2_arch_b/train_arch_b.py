"""K54 v2 — Architecture B: Per-instrument-group ensemble.

Trains one LightGBM per effective group (4 total):
  - XAU_XAG (XAUUSD + XAGUSD, n=215)         -> CPCV K=6, N=2 (15 paths)
  - NAS_US30 (NAS100 + US30_CASH, n=113)     -> CPCV K=6, N=2 (15 paths)
  - GBPUSD_USDJPY (n=138)                    -> CPCV K=6, N=2 (15 paths)
  - GBPJPY (n=62)                            -> CPCV K=4, N=2  (6 paths) [thin-data adj]

For each group:
  - Drop features with > 50% NaN on the group's rows (per-instrument features that
    don't apply, e.g. JPY-only Tokyo KZ on XAU rows).
  - Per-fold top-100 screening (Architecture A's pattern, applied within group).
  - 27-HP grid; CPCV-honest fixed-HP selection (mean OOS AUC across paths).
  - Pair vs K54 v1 baseline on same group's test folds.

Aggregate metrics:
  - mean AUC per group (compare to k54_v2's per-group AUC).
  - weighted-by-group-n average AUC vs K54 v2 global (0.5429).
  - count of groups with positive lift (target ≥3 of 4).

Outputs (research/ml_program/models/k54_v2_arch_b/):
  - {group}/cpcv_results.json
  - {group}/top_features.json
  - {group}/meta.json
  - {group}/k54_arch_b_{group}.lgb
  - aggregate_summary.json
"""
from __future__ import annotations

import json
import math
import sys
import time
import warnings
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

import lightgbm as lgb

warnings.filterwarnings("ignore")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
K54_V1_FEATURES = ROOT / "research/ml_program/models/k54_v1_features_full.csv"
V2_DIR = ROOT / "research/ml_program/models/k54_v2"
OUT_DIR = ROOT / "research/ml_program/models/k54_v2_arch_b"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_CUTOFF = "2026-04-28"
RANDOM_SEED = 42
TOP_K = 100
PURGE_DAYS = 7
EMBARGO_DAYS = 1
NAN_DROP_THRESHOLD = 0.50  # Drop features with > 50% NaN within a group
HYPER_GRID = [
    {"n_estimators": ne, "max_depth": md, "learning_rate": lr}
    for ne in (100, 200, 400)
    for md in (3, 5, 7)
    for lr in (0.01, 0.05, 0.1)
]
SCREEN_HP = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05, "min_data_in_leaf": 10}

GROUP_MAP = {
    "XAUUSD": "XAU_XAG",
    "XAGUSD": "XAU_XAG",
    "NAS100": "NAS_US30",
    "US30_CASH": "NAS_US30",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD_USDJPY",
    "USDJPY": "GBPUSD_USDJPY",
}
# K54 v2's per-group AUC for context
K54_V2_PER_GROUP = {
    "XAU_XAG": 0.5145,
    "NAS_US30": 0.5063,
    "GBPUSD_USDJPY": 0.5156,
    "GBPJPY": 0.4433,
}
K54_V2_GLOBAL_AUC = 0.5429
GROUP_CPCV = {
    "XAU_XAG": {"K": 6, "N": 2},
    "NAS_US30": {"K": 6, "N": 2},
    "GBPUSD_USDJPY": {"K": 6, "N": 2},
    "GBPJPY": {"K": 4, "N": 2},  # thin-data: K=4 -> ~15/fold; 6 paths
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def family_of(col: str) -> str:
    if col.startswith("struct__"):
        return "structure"
    if col.startswith("vol__"):
        return "volatility"
    if col.startswith("micro__"):
        return "microstructure"
    if col.startswith("ts__"):
        return "time_session"
    if col.startswith("liq__"):
        return "liquidity"
    if col.startswith("reg__"):
        return "regime"
    return "unknown"


def load_v2_matrix():
    df = pd.read_parquet(SCOUT_PARQUET)
    assert df["__date"].max() <= DATA_CUTOFF
    df["dedup_key"] = list(
        zip(
            df["__date"].astype(str).str[:10],
            df["__symbol"],
            df["__direction"],
            df["__framework"],
            df["__realized_r"].round(3),
        )
    )
    feature_cols = [c for c in df.columns if not c.startswith("__") and c != "dedup_key"]
    return df, feature_cols


def apply_v2_prune(feature_cols):
    prune_path = V2_DIR / "feature_prune_list.json"
    with open(prune_path, "r", encoding="utf-8") as f:
        prune_data = json.load(f)
    drop = {item["feature"] for item in prune_data["prune_list"]}
    return [c for c in feature_cols if c not in drop]


def load_v1_baseline_features():
    v1 = pd.read_csv(K54_V1_FEATURES)
    v1["date_only"] = v1["date_iso"].astype(str).str[:10]
    v1["dedup_key"] = list(
        zip(
            v1["date_only"],
            v1["symbol"],
            v1["direction_long_short"],
            v1["framework"],
            v1["realized_r"].round(3),
        )
    )
    return v1.drop_duplicates(subset="dedup_key", keep="first").copy()


def prepare_v1_X(v1d, dedup_keys):
    keys_df = pd.DataFrame({"dedup_key": dedup_keys})
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
    y = v1_aligned["win_label"].astype(int).values
    return encoded, y


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
    paths = []
    for test_combo in combinations(range(k), n):
        train_combo = [i for i in range(k) if i not in test_combo]
        paths.append((train_combo, list(test_combo)))
    return paths


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


def train_lgbm(X_tr, y_tr, X_val, y_val, hp, n_train):
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


def train_screening_lgbm(X_tr, y_tr):
    return lgb.LGBMClassifier(
        n_estimators=SCREEN_HP["n_estimators"],
        max_depth=SCREEN_HP["max_depth"],
        learning_rate=SCREEN_HP["learning_rate"],
        min_data_in_leaf=SCREEN_HP["min_data_in_leaf"],
        num_leaves=2 ** SCREEN_HP["max_depth"],
        objective="binary",
        metric="auc",
        n_jobs=1,
        verbosity=-1,
        random_state=RANDOM_SEED,
        deterministic=True,
        force_row_wise=True,
    ).fit(X_tr, y_tr)


def calibrate(model_proba_tr, y_tr, model_proba_te):
    if len(np.unique(y_tr)) < 2:
        return model_proba_te
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(model_proba_tr.reshape(-1, 1), y_tr)
    return cal.predict_proba(model_proba_te.reshape(-1, 1))[:, 1]


def safe_auc(y, p):
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


def delong_paired_test(y, p1, p2):
    if len(np.unique(y)) < 2:
        return float("nan"), float("nan")
    pos_mask = y == 1
    neg_mask = y == 0
    n_pos = int(pos_mask.sum())
    n_neg = int(neg_mask.sum())
    if n_pos < 2 or n_neg < 2:
        return float("nan"), float("nan")

    def midrank(x):
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

    def aucs_and_cov(p_mat):
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


def stouffer_combine(p_values):
    pv = [p for p in p_values if p is not None and not math.isnan(p) and 0 < p < 1]
    if not pv:
        return float("nan")
    z = [stats.norm.ppf(1 - p) for p in pv]
    z_combined = sum(z) / math.sqrt(len(z))
    return float(1 - stats.norm.cdf(z_combined))


def fisher_combine(p_values):
    pv = [p for p in p_values if p is not None and not math.isnan(p) and 0 < p < 1]
    if not pv:
        return float("nan")
    chi2 = -2 * sum(math.log(p) for p in pv)
    df = 2 * len(pv)
    return float(1 - stats.chi2.cdf(chi2, df))


def train_group(group: str, df, feature_cols, X_v1_full, y_full, X_v2_full):
    """Train Arch B for one instrument group; return per-group results dict."""
    group_dir = OUT_DIR / group
    group_dir.mkdir(parents=True, exist_ok=True)
    cfg = GROUP_CPCV[group]
    K, N = cfg["K"], cfg["N"]
    print(f"\n--- Group {group}: K={K}, N={N} ---")

    # Subset rows by group
    grp_mask = df["__symbol"].map(GROUP_MAP) == group
    grp_idx = df.index[grp_mask].values  # row positions into the full 528 frame
    n_grp = len(grp_idx)
    print(f"  Rows in group: {n_grp}, win-rate: {y_full[grp_idx].mean():.3f}")

    # Drop columns with > NAN_DROP_THRESHOLD NaN ON THIS GROUP
    grp_X = X_v2_full[feature_cols].iloc[grp_idx]
    nan_rate = grp_X.isna().mean()
    keep_cols = [c for c in feature_cols if nan_rate.get(c, 0.0) <= NAN_DROP_THRESHOLD]
    dropped_n = len(feature_cols) - len(keep_cols)
    print(f"  Dropped {dropped_n} columns with >{NAN_DROP_THRESHOLD:.0%} NaN on group "
          f"-> kept {len(keep_cols)}")

    # Reindex group locally (0..n_grp-1)
    grp_X_local = grp_X[keep_cols].copy().reset_index(drop=True)
    grp_y_local = y_full[grp_idx]
    grp_dates_local = pd.to_datetime(df["__date"].iloc[grp_idx].astype(str).str[:10]).reset_index(drop=True)
    grp_v1_local = X_v1_full.iloc[grp_idx].reset_index(drop=True)

    # Build folds + paths within the group
    folds = time_indexed_folds(grp_dates_local, K)
    paths = cpcv_paths(folds, N)
    print(f"  CPCV paths: {len(paths)} (K={K}, N={N})")
    fold_meta = []
    for i, fi in enumerate(folds):
        d_tmp = grp_dates_local.iloc[fi]
        fold_meta.append({"fold": i, "n": len(fi),
                          "date_min": str(d_tmp.min().date()),
                          "date_max": str(d_tmp.max().date())})

    # Per-path: screening + 27-HP grid
    cpcv_results = []
    n_hp = len(HYPER_GRID)
    hp_path_aucs_b: dict[int, list[float]] = {i: [] for i in range(n_hp)}
    hp_path_aucs_v1: dict[int, list[float]] = {i: [] for i in range(n_hp)}
    hp_is_aucs_b: dict[int, list[float]] = {i: [] for i in range(n_hp)}
    per_path_top100: list[dict] = []

    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, grp_dates_local, PURGE_DAYS, EMBARGO_DAYS)
        if len(train_idx) < 20:
            print(f"    Path {path_idx}: train_idx after purge = {len(train_idx)}; SKIPPING")
            continue
        train_dates_p = grp_dates_local.iloc[train_idx]
        sort_perm = np.argsort(train_dates_p.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(10, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]
        if len(inner_train) < 10 or len(inner_val) < 5:
            print(f"    Path {path_idx}: too thin (it={len(inner_train)}, iv={len(inner_val)}); SKIPPING")
            continue
        # Skip if test fold is single-class
        y_te = grp_y_local[test_idx]
        if len(np.unique(y_te)) < 2:
            print(f"    Path {path_idx}: test fold single-class; SKIPPING")
            continue

        # Screening
        X_screen_tr = grp_X_local.iloc[inner_train].fillna(grp_X_local.iloc[inner_train].median())
        y_screen_tr = grp_y_local[inner_train]
        if len(np.unique(y_screen_tr)) < 2:
            print(f"    Path {path_idx}: train fold single-class; SKIPPING")
            continue
        screen_model = train_screening_lgbm(X_screen_tr, y_screen_tr)
        importances = screen_model.feature_importances_
        feat_imp = sorted(
            [(keep_cols[i], float(importances[i])) for i in range(len(keep_cols))],
            key=lambda x: x[1], reverse=True,
        )
        top_k_features = [f for f, _ in feat_imp[:TOP_K]]
        per_path_top100.append({
            "path": path_idx,
            "top100": [{"feature": f, "gain": g, "family": family_of(f)} for f, g in feat_imp[:TOP_K]],
        })

        X_b_tr = grp_X_local[top_k_features].iloc[inner_train]
        X_b_iv = grp_X_local[top_k_features].iloc[inner_val]
        X_b_te = grp_X_local[top_k_features].iloc[test_idx]
        X_v1_tr = grp_v1_local.iloc[inner_train]
        X_v1_iv = grp_v1_local.iloc[inner_val]
        X_v1_te = grp_v1_local.iloc[test_idx]
        y_tr = grp_y_local[inner_train]
        y_iv = grp_y_local[inner_val]

        # 27-HP grid
        for hp_idx, hp in enumerate(HYPER_GRID):
            try:
                m_b = train_lgbm(X_b_tr, y_tr, X_b_iv, y_iv, hp, len(inner_train))
                p_b_iv = m_b.predict_proba(X_b_iv)[:, 1]
                p_b_te = m_b.predict_proba(X_b_te)[:, 1]
                p_b_te = calibrate(p_b_iv, y_iv, p_b_te)
                auc_b = safe_auc(y_te, p_b_te)
                # IS auc on train slice (for PBO)
                p_b_tr_is = m_b.predict_proba(X_b_tr)[:, 1]
                auc_is = safe_auc(y_tr, p_b_tr_is)
            except Exception:
                auc_b = float("nan")
                auc_is = float("nan")
            try:
                m_v1 = train_lgbm(X_v1_tr, y_tr, X_v1_iv, y_iv, hp, len(inner_train))
                p_v1_iv = m_v1.predict_proba(X_v1_iv)[:, 1]
                p_v1_te = m_v1.predict_proba(X_v1_te)[:, 1]
                p_v1_te = calibrate(p_v1_iv, y_iv, p_v1_te)
                auc_v1 = safe_auc(y_te, p_v1_te)
            except Exception:
                auc_v1 = float("nan")
            hp_path_aucs_b[hp_idx].append(auc_b)
            hp_path_aucs_v1[hp_idx].append(auc_v1)
            hp_is_aucs_b[hp_idx].append(auc_is)

    if not per_path_top100:
        print(f"  Group {group}: NO valid paths; skipping group")
        return None

    # Select fixed HP via mean OOS AUC across paths
    hp_mean_aucs = np.array([np.nanmean(hp_path_aucs_b[i]) for i in range(n_hp)])
    best_hp_idx = int(np.nanargmax(hp_mean_aucs))
    best_hp = HYPER_GRID[best_hp_idx]
    selected_oos_mean = float(hp_mean_aucs[best_hp_idx])
    print(f"  Selected HP: idx={best_hp_idx}, {best_hp}, OOS mean AUC = {selected_oos_mean:.4f}")

    # Re-run final pass at fixed HP for paired DeLong + Brier
    valid_path_indices = [r["path"] for r in per_path_top100]
    for path_pos, path_idx_real in enumerate(valid_path_indices):
        train_groups, test_groups = paths[path_idx_real]
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, grp_dates_local, PURGE_DAYS, EMBARGO_DAYS)
        train_dates_p = grp_dates_local.iloc[train_idx]
        sort_perm = np.argsort(train_dates_p.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(10, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        top_k_features = [t["feature"] for t in per_path_top100[path_pos]["top100"]]
        X_b_tr = grp_X_local[top_k_features].iloc[inner_train]
        X_b_iv = grp_X_local[top_k_features].iloc[inner_val]
        X_b_te = grp_X_local[top_k_features].iloc[test_idx]
        X_v1_tr = grp_v1_local.iloc[inner_train]
        X_v1_iv = grp_v1_local.iloc[inner_val]
        X_v1_te = grp_v1_local.iloc[test_idx]
        y_tr = grp_y_local[inner_train]
        y_iv = grp_y_local[inner_val]
        y_te = grp_y_local[test_idx]

        m_b = train_lgbm(X_b_tr, y_tr, X_b_iv, y_iv, best_hp, len(inner_train))
        p_b_iv = m_b.predict_proba(X_b_iv)[:, 1]
        p_b_te = m_b.predict_proba(X_b_te)[:, 1]
        p_b_te = calibrate(p_b_iv, y_iv, p_b_te)

        m_v1 = train_lgbm(X_v1_tr, y_tr, X_v1_iv, y_iv, best_hp, len(inner_train))
        p_v1_iv = m_v1.predict_proba(X_v1_iv)[:, 1]
        p_v1_te = m_v1.predict_proba(X_v1_te)[:, 1]
        p_v1_te = calibrate(p_v1_iv, y_iv, p_v1_te)

        auc_b = safe_auc(y_te, p_b_te)
        auc_v1 = safe_auc(y_te, p_v1_te)
        brier_b = brier_score_loss(y_te, p_b_te) if len(np.unique(y_te)) > 1 else float("nan")
        brier_v1 = brier_score_loss(y_te, p_v1_te) if len(np.unique(y_te)) > 1 else float("nan")
        auc_diff, p_delong = delong_paired_test(y_te, p_v1_te, p_b_te)

        cpcv_results.append({
            "path": path_idx_real,
            "train_groups": list(train_groups),
            "test_groups": list(test_groups),
            "n_train_after_purge": int(len(inner_train)),
            "n_inner_val": int(len(inner_val)),
            "n_test": int(len(test_idx)),
            "selected_hp": best_hp,
            "auc_b": float(auc_b),
            "auc_v1": float(auc_v1),
            "auc_diff": float(auc_b - auc_v1),
            "delong_p": float(p_delong),
            "brier_b": float(brier_b),
            "brier_v1": float(brier_v1),
            "test_idx_local": test_idx.tolist(),
            "test_idx_global": grp_idx[test_idx].tolist(),
            "p_b_te": p_b_te.tolist(),
            "p_v1_te": p_v1_te.tolist(),
            "y_te": y_te.tolist(),
        })

    diffs = np.array([r["auc_diff"] for r in cpcv_results])
    delong_ps = [r["delong_p"] for r in cpcv_results]
    auc_b_mean = float(np.nanmean([r["auc_b"] for r in cpcv_results]))
    auc_v1_mean = float(np.nanmean([r["auc_v1"] for r in cpcv_results]))
    diff_mean = float(np.nanmean(diffs))
    diff_std = float(np.nanstd(diffs, ddof=1)) if len(diffs) > 1 else float("nan")
    diff_se = (diff_std / math.sqrt(len(diffs))) if len(diffs) > 1 else float("nan")
    if not math.isnan(diff_se):
        diff_ci_lo = diff_mean - 1.96 * diff_se
        diff_ci_hi = diff_mean + 1.96 * diff_se
    else:
        diff_ci_lo = diff_ci_hi = float("nan")
    p_combined_stouffer = stouffer_combine(delong_ps)
    p_combined_fisher = fisher_combine(delong_ps)

    # PBO within group
    pbo_below_median = 0
    pbo_path_records = []
    for path_pos, path_idx_real in enumerate(valid_path_indices):
        is_aucs = np.array([hp_is_aucs_b[h][path_pos] for h in range(n_hp)])
        oos_aucs = np.array([hp_path_aucs_b[h][path_pos] for h in range(n_hp)])
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
            "path": path_idx_real,
            "is_best_hp_idx": is_best_hp,
            "is_best_hp": HYPER_GRID[is_best_hp],
            "is_best_oos_rank": is_best_oos_rank,
            "n_hp": n_hp,
            "below_median": bool(below_median),
        })
    group_pbo = pbo_below_median / len(pbo_path_records) if pbo_path_records else float("nan")

    cpcv_summary = {
        "method_b_group": f"Per-group ensemble: {group}, K={K}, N={N}, top-{TOP_K} per-fold screening",
        "screening_hp": SCREEN_HP,
        "top_k": TOP_K,
        "n_grp": int(n_grp),
        "n_features_after_nan_drop": len(keep_cols),
        "n_paths_completed": len(cpcv_results),
        "K": K, "N": N,
        "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "auc_b_mean": auc_b_mean,
        "auc_v1_mean": auc_v1_mean,
        "diff_mean": diff_mean,
        "diff_std": diff_std,
        "diff_se": diff_se if not math.isnan(diff_se) else None,
        "diff_95ci": [diff_ci_lo, diff_ci_hi] if not math.isnan(diff_ci_lo) else None,
        "delong_p_per_path": delong_ps,
        "delong_p_combined_stouffer": p_combined_stouffer,
        "delong_p_combined_fisher": p_combined_fisher,
        "pbo": float(group_pbo),
        "computed_at": utc_now(),
    }
    print(f"  Group {group} summary: AUC_b={auc_b_mean:.4f}, AUC_v1={auc_v1_mean:.4f}, "
          f"diff={diff_mean:+.4f}, p_combined={p_combined_stouffer:.4f}, PBO={group_pbo:.4f}")

    with open(group_dir / "cpcv_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": cpcv_summary, "paths": cpcv_results, "fold_meta": fold_meta}, f, indent=2)

    # Aggregate per-path top-100 -> by frequency
    feat_freq, feat_total_gain = {}, {}
    for r in per_path_top100:
        for entry in r["top100"]:
            f_ = entry["feature"]
            feat_freq[f_] = feat_freq.get(f_, 0) + 1
            feat_total_gain[f_] = feat_total_gain.get(f_, 0.0) + entry["gain"]
    ranked = sorted(feat_freq.items(), key=lambda kv: (kv[1], feat_total_gain.get(kv[0], 0.0)), reverse=True)
    aggregated_top = [
        {"feature": f, "freq_in_top100": c, "total_gain_across_paths": feat_total_gain[f], "family": family_of(f)}
        for f, c in ranked[:200]
    ]

    # Final group model on top-100 by frequency
    final_top_features = [e["feature"] for e in aggregated_top[:TOP_K]]
    sort_perm = np.argsort(grp_dates_local.values)
    n_inner = max(8, len(sort_perm) // 8)
    inner_val = sort_perm[-n_inner:]
    inner_train = sort_perm[:-n_inner]
    X_final_tr = grp_X_local[final_top_features].iloc[inner_train]
    X_final_iv = grp_X_local[final_top_features].iloc[inner_val]
    final_model = train_lgbm(
        X_final_tr, grp_y_local[inner_train],
        X_final_iv, grp_y_local[inner_val],
        best_hp, len(inner_train),
    )
    final_model.booster_.save_model(str(group_dir / f"k54_arch_b_{group}.lgb"))

    importances = final_model.feature_importances_
    f_imp = sorted(
        [(final_top_features[i], float(importances[i])) for i in range(len(final_top_features))],
        key=lambda x: x[1], reverse=True,
    )
    top30_global = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in f_imp[:30]]

    with open(group_dir / "top_features.json", "w", encoding="utf-8") as f:
        json.dump({
            "group": group,
            "selected_hp": best_hp,
            "cpcv_mean_oos_auc_at_selected_hp": selected_oos_mean,
            "aggregated_top200_by_path_frequency": aggregated_top,
            "final_model_top30": top30_global,
            "per_path_top100": per_path_top100,
            "computed_at": utc_now(),
        }, f, indent=2)

    meta = {
        "k54_version": f"v2_arch_b_{group}",
        "architecture": f"Per-group ensemble (Arch B), group={group}",
        "screening_hp": SCREEN_HP,
        "top_k_per_fold": TOP_K,
        "training_spec": {
            "data_cutoff_utc": DATA_CUTOFF,
            "group_n": int(n_grp),
            "win_rate": float(grp_y_local.mean()),
            "n_features_after_nan_drop": len(keep_cols),
        },
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "selected_hp_cpcv_mean_oos_auc": selected_oos_mean,
        "cpcv_config": {"K": K, "N": N, "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS},
        "rows_per_feature_effective_per_fold": float(n_grp / TOP_K),
        "code_revisions": {
            "v2_baseline_meta": str(V2_DIR / "meta.json"),
            "scout_matrix": str(SCOUT_PARQUET),
        },
        "computed_at": utc_now(),
    }
    with open(group_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "group": group,
        "n_grp": n_grp,
        "auc_b_mean": auc_b_mean,
        "auc_v1_mean": auc_v1_mean,
        "diff_mean": diff_mean,
        "p_combined_stouffer": p_combined_stouffer,
        "pbo": float(group_pbo),
        "selected_hp": best_hp,
        "n_paths_completed": len(cpcv_results),
        "cpcv_results": cpcv_results,
        "top30_global": top30_global,
        "aggregated_top": aggregated_top,
        "k54_v2_per_group_auc_for_compare": K54_V2_PER_GROUP.get(group),
    }


def main():
    print(f"=== K54 v2 Architecture B — per-group ensemble — {utc_now()} ===")
    t_start = time.time()

    print("\n[1/3] Loading scout matrix + applying v2 prune...")
    df, feature_cols_raw = load_v2_matrix()
    feature_cols = apply_v2_prune(feature_cols_raw)
    print(f"  {len(feature_cols_raw)} -> {len(feature_cols)} features")

    print("\n[2/3] Building K54 v1 paired baseline...")
    v1d = load_v1_baseline_features()
    dedup_keys = df["dedup_key"].tolist()
    X_v1, y_v1 = prepare_v1_X(v1d, dedup_keys)
    y = df["__win_label"].astype(int).values
    np.testing.assert_array_equal(y_v1, y)
    print(f"  V1: {X_v1.shape}, win-rate {y.mean():.3f}")

    X_v2_full = df[feature_cols].astype(float).copy()
    X_v2_full = X_v2_full.replace([np.inf, -np.inf], np.nan)

    print("\n[3/3] Training per-group...")
    group_results = {}
    for group in ["XAU_XAG", "NAS_US30", "GBPUSD_USDJPY", "GBPJPY"]:
        result = train_group(group, df, feature_cols, X_v1, y, X_v2_full)
        if result is not None:
            group_results[group] = result

    # Aggregate
    weighted_auc_num = 0.0
    weighted_auc_den = 0
    aggregate_groups = {}
    for grp, r in group_results.items():
        weighted_auc_num += r["auc_b_mean"] * r["n_grp"]
        weighted_auc_den += r["n_grp"]
        # Compare to k54_v2 per-group AUC
        k54_v2_grp_auc = K54_V2_PER_GROUP.get(grp, float("nan"))
        diff_vs_v2 = r["auc_b_mean"] - k54_v2_grp_auc
        aggregate_groups[grp] = {
            "n_grp": r["n_grp"],
            "auc_b_mean": r["auc_b_mean"],
            "auc_v1_mean": r["auc_v1_mean"],
            "diff_b_vs_v1": r["diff_mean"],
            "k54_v2_global_per_group_auc": k54_v2_grp_auc,
            "diff_b_vs_k54_v2_global": diff_vs_v2,
            "lift_b_over_v1_positive": (r["auc_b_mean"] > r["auc_v1_mean"]),
            "p_combined_stouffer": r["p_combined_stouffer"],
            "pbo": r["pbo"],
            "selected_hp": r["selected_hp"],
            "n_paths_completed": r["n_paths_completed"],
        }
    weighted_b_auc = weighted_auc_num / weighted_auc_den if weighted_auc_den > 0 else float("nan")

    n_groups_b_lift_over_v1 = sum(1 for v in aggregate_groups.values() if v["lift_b_over_v1_positive"])
    n_groups_b_lift_over_v2 = sum(1 for v in aggregate_groups.values()
                                  if (v["diff_b_vs_k54_v2_global"] is not None
                                      and v["diff_b_vs_k54_v2_global"] > 0))

    summary = {
        "method": "Per-instrument-group LightGBM ensemble; 4 effective groups",
        "groups": aggregate_groups,
        "weighted_b_auc_by_group_n": float(weighted_b_auc),
        "k54_v2_global_auc": K54_V2_GLOBAL_AUC,
        "weighted_b_auc_minus_k54_v2_global": float(weighted_b_auc - K54_V2_GLOBAL_AUC),
        "n_groups_b_lift_over_v1": int(n_groups_b_lift_over_v1),
        "n_groups_b_lift_over_v2_per_group": int(n_groups_b_lift_over_v2),
        "gate_d_threshold_actual_4_groups": "AUC_b > AUC_v1 on >=3 of 4 effective groups",
        "gate_d_pass_actual_4_v1": bool(n_groups_b_lift_over_v1 >= 3),
        "gate_d_pass_actual_4_v2": bool(n_groups_b_lift_over_v2 >= 3),
        "wallclock_total_seconds": time.time() - t_start,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "aggregate_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Architecture B DONE in {time.time()-t_start:.0f}s ===")
    print(f"  Weighted B AUC = {weighted_b_auc:.4f} (k54_v2 global = {K54_V2_GLOBAL_AUC})")
    print(f"  Diff vs k54_v2 global: {weighted_b_auc - K54_V2_GLOBAL_AUC:+.4f}")
    print(f"  Groups with B>v1: {n_groups_b_lift_over_v1}/4")
    print(f"  Groups with B>k54_v2 (per-group): {n_groups_b_lift_over_v2}/4")


if __name__ == "__main__":
    main()
