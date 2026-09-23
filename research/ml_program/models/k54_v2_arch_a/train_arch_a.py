"""K54 v2 — Architecture A: Per-fold feature screening (de Prado AFML §8.5).

For each CPCV path:
  1. Screening pass: train default-ish LightGBM on (purged) train fold, collect top-100
     features by gain.
  2. Final pass: train LightGBM on the same train fold restricted to top-100; same
     27-combo HP grid as v2.
  3. Score on path's test fold.

Selected HP: mean OOS AUC across 15 paths (single fixed HP, CPCV-honest).

Inputs: scout feature_matrix.parquet (post-prune via k54_v2's feature_prune_list.json),
        k54_v2's CPCV split structure (test_idx per path).

Outputs (research/ml_program/models/k54_v2_arch_a/):
  - cpcv_results.json  (paired vs k54_v1 baseline, per-path + summary)
  - top_features.json  (per-path top-100 + global frequency aggregation)
  - meta.json
  - k54_arch_a.lgb     (final on full cohort, top-100 by aggregated frequency)
  - cross_instrument_results.json
  - pbo_results.json
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
OUT_DIR = ROOT / "research/ml_program/models/k54_v2_arch_a"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_CUTOFF = "2026-04-28"
RANDOM_SEED = 42
TOP_K = 100
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
HYPER_GRID = [
    {"n_estimators": ne, "max_depth": md, "learning_rate": lr}
    for ne in (100, 200, 400)
    for md in (3, 5, 7)
    for lr in (0.01, 0.05, 0.1)
]  # 27 combos
# Default-ish screening HP per brief (n_estimators=200, max_depth=5, lr=0.05, mdl=10)
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


def load_v2_matrix() -> tuple[pd.DataFrame, list[str]]:
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


def apply_v2_prune(feature_cols: list[str]) -> list[str]:
    """Apply same 13-feature prune as k54_v2."""
    prune_path = V2_DIR / "feature_prune_list.json"
    with open(prune_path, "r", encoding="utf-8") as f:
        prune_data = json.load(f)
    drop = {item["feature"] for item in prune_data["prune_list"]}
    return [c for c in feature_cols if c not in drop]


def load_v1_baseline_features() -> pd.DataFrame:
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


def prepare_v1_X(v1d: pd.DataFrame, dedup_keys: list[tuple]) -> tuple[pd.DataFrame, np.ndarray]:
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


def time_indexed_folds(dates: pd.Series, k: int) -> list[np.ndarray]:
    sort_idx = np.argsort(dates.values)
    fold_size = len(sort_idx) // k
    folds = []
    for i in range(k):
        start = i * fold_size
        end = (i + 1) * fold_size if i < k - 1 else len(sort_idx)
        folds.append(sort_idx[start:end])
    return folds


def cpcv_paths(folds: list[np.ndarray], n: int):
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
):
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


def train_screening_lgbm(X_tr: pd.DataFrame, y_tr: np.ndarray):
    """Default-ish LightGBM for feature screening.
    n_estimators=200, max_depth=5, lr=0.05, min_data_in_leaf=10.
    """
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


def calibrate(
    model_proba_tr: np.ndarray, y_tr: np.ndarray,
    model_proba_te: np.ndarray,
):
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


def main():
    print(f"=== K54 v2 Architecture A — per-fold screening — {utc_now()} ===")
    t_start = time.time()

    print("\n[1/7] Loading scout feature matrix + applying v2 prune...")
    df, feature_cols_raw = load_v2_matrix()
    feature_cols = apply_v2_prune(feature_cols_raw)
    print(f"  Pre-prune {len(feature_cols_raw)} -> post-prune {len(feature_cols)}")

    print("\n[2/7] Building K54 v1 paired baseline (528-row cohort)...")
    v1d = load_v1_baseline_features()
    dedup_keys = df["dedup_key"].tolist()
    X_v1, y_v1 = prepare_v1_X(v1d, dedup_keys)
    y_v2 = df["__win_label"].astype(int).values
    np.testing.assert_array_equal(y_v1, y_v2)
    y = y_v2
    print(f"  V1: {X_v1.shape}, win-rate {y.mean():.3f}")

    X_v2_full = df[feature_cols].astype(float).copy()
    X_v2_full = X_v2_full.replace([np.inf, -np.inf], np.nan)
    print(f"  V2 full: {X_v2_full.shape} (NaN rate {(X_v2_full.isna().sum().sum() / X_v2_full.size):.3%})")

    print(f"\n[3/7] Building CPCV K={CPCV_K}, N={CPCV_N}...")
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    folds = time_indexed_folds(dates, CPCV_K)
    fold_meta = []
    for i, fi in enumerate(folds):
        d_tmp = dates.iloc[fi]
        fold_meta.append({
            "fold": i, "n": len(fi),
            "date_min": str(d_tmp.min().date()),
            "date_max": str(d_tmp.max().date()),
        })
    paths = cpcv_paths(folds, CPCV_N)
    print(f"  CPCV paths: {len(paths)}")

    # ===== Per-path screening + grid HP =====
    print(f"\n[4/7] Per-fold screening + 27-HP grid × {len(paths)} paths × 2 models...")
    print("  Screening: LightGBM (200 est, depth 5, lr 0.05, mdl 10) -> top-100 by gain")
    cpcv_results = []
    hp_path_aucs_arch_a: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}
    hp_path_aucs_v1: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}
    hp_is_aucs_arch_a: dict[int, list[float]] = {i: [] for i in range(len(HYPER_GRID))}
    per_path_top100: list[dict] = []

    t_loop_start = time.time()
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

        # 4a. Screening pass on FULL feature space (purged train fold only)
        # Fill NaN with median for screening (to avoid LightGBM NaN-branch dominance bias)
        X_screen_tr = X_v2_full.iloc[inner_train].fillna(X_v2_full.iloc[inner_train].median())
        y_screen_tr = y[inner_train]
        screen_model = train_screening_lgbm(X_screen_tr, y_screen_tr)
        importances = screen_model.feature_importances_
        feat_imp = sorted(
            [(feature_cols[i], float(importances[i])) for i in range(len(feature_cols))],
            key=lambda x: x[1], reverse=True,
        )
        top_k_features = [f for f, _ in feat_imp[:TOP_K]]
        per_path_top100.append({
            "path": path_idx,
            "top100": [{"feature": f, "gain": g, "family": family_of(f)} for f, g in feat_imp[:TOP_K]],
        })

        # 4b. Final pass on top-K features (no NaN-fill — LightGBM handles natively)
        X_a_tr = X_v2_full[top_k_features].iloc[inner_train]
        X_a_iv = X_v2_full[top_k_features].iloc[inner_val]
        X_a_te = X_v2_full[top_k_features].iloc[test_idx]
        X_v1_tr = X_v1.iloc[inner_train]
        X_v1_iv = X_v1.iloc[inner_val]
        X_v1_te = X_v1.iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        # 27-HP loop
        for hp_idx, hp in enumerate(HYPER_GRID):
            try:
                m_a = train_lgbm(X_a_tr, y_tr, X_a_iv, y_iv, hp, len(inner_train))
                p_a_iv = m_a.predict_proba(X_a_iv)[:, 1]
                p_a_te = m_a.predict_proba(X_a_te)[:, 1]
                p_a_te = calibrate(p_a_iv, y_iv, p_a_te)
                auc_a = safe_auc(y_te, p_a_te)
                # IS auc on train slice (for PBO)
                p_a_tr_is = m_a.predict_proba(X_a_tr)[:, 1]
                auc_is = safe_auc(y_tr, p_a_tr_is)
            except Exception:
                auc_a = float("nan")
                auc_is = float("nan")
            try:
                m_v1 = train_lgbm(X_v1_tr, y_tr, X_v1_iv, y_iv, hp, len(inner_train))
                p_v1_iv = m_v1.predict_proba(X_v1_iv)[:, 1]
                p_v1_te = m_v1.predict_proba(X_v1_te)[:, 1]
                p_v1_te = calibrate(p_v1_iv, y_iv, p_v1_te)
                auc_v1 = safe_auc(y_te, p_v1_te)
            except Exception:
                auc_v1 = float("nan")
            hp_path_aucs_arch_a[hp_idx].append(auc_a)
            hp_path_aucs_v1[hp_idx].append(auc_v1)
            hp_is_aucs_arch_a[hp_idx].append(auc_is)

        if (path_idx + 1) % 3 == 0 or path_idx == len(paths) - 1:
            elapsed = time.time() - t_loop_start
            print(f"  Path {path_idx+1}/{len(paths)} done; elapsed {elapsed:.0f}s")

    # ===== Select fixed HP via mean OOS AUC across paths =====
    n_hp = len(HYPER_GRID)
    hp_mean_aucs = np.array([np.nanmean(hp_path_aucs_arch_a[i]) for i in range(n_hp)])
    best_hp_idx = int(np.nanargmax(hp_mean_aucs))
    best_hp = HYPER_GRID[best_hp_idx]
    selected_oos_mean = float(hp_mean_aucs[best_hp_idx])
    print(f"\n  Selected HP: idx={best_hp_idx}, {best_hp}, OOS mean AUC = {selected_oos_mean:.4f}")

    # ===== Re-run final pass at fixed HP (paired DeLong, calibrated) =====
    print(f"\n[5/7] Re-running fixed-HP paired final pass for paired DeLong + Brier...")
    t_loop_start = time.time()
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_idx = np.concatenate([folds[i] for i in test_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)
        train_dates_p = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates_p.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        top_k_features = [t["feature"] for t in per_path_top100[path_idx]["top100"]]
        X_a_tr = X_v2_full[top_k_features].iloc[inner_train]
        X_a_iv = X_v2_full[top_k_features].iloc[inner_val]
        X_a_te = X_v2_full[top_k_features].iloc[test_idx]
        X_v1_tr = X_v1.iloc[inner_train]
        X_v1_iv = X_v1.iloc[inner_val]
        X_v1_te = X_v1.iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        m_a = train_lgbm(X_a_tr, y_tr, X_a_iv, y_iv, best_hp, len(inner_train))
        p_a_iv = m_a.predict_proba(X_a_iv)[:, 1]
        p_a_te = m_a.predict_proba(X_a_te)[:, 1]
        p_a_te = calibrate(p_a_iv, y_iv, p_a_te)

        m_v1 = train_lgbm(X_v1_tr, y_tr, X_v1_iv, y_iv, best_hp, len(inner_train))
        p_v1_iv = m_v1.predict_proba(X_v1_iv)[:, 1]
        p_v1_te = m_v1.predict_proba(X_v1_te)[:, 1]
        p_v1_te = calibrate(p_v1_iv, y_iv, p_v1_te)

        auc_a = safe_auc(y_te, p_a_te)
        auc_v1 = safe_auc(y_te, p_v1_te)
        brier_a = brier_score_loss(y_te, p_a_te) if len(np.unique(y_te)) > 1 else float("nan")
        brier_v1 = brier_score_loss(y_te, p_v1_te) if len(np.unique(y_te)) > 1 else float("nan")
        auc_diff, p_delong = delong_paired_test(y_te, p_v1_te, p_a_te)

        cpcv_results.append({
            "path": path_idx,
            "train_groups": list(train_groups),
            "test_groups": list(test_groups),
            "n_train_after_purge": int(len(inner_train)),
            "n_inner_val": int(len(inner_val)),
            "n_test": int(len(test_idx)),
            "selected_hp": best_hp,
            "selected_hp_idx": best_hp_idx,
            "auc_a": float(auc_a),
            "auc_v1": float(auc_v1),
            "auc_diff": float(auc_a - auc_v1),
            "delong_p": float(p_delong),
            "brier_a": float(brier_a),
            "brier_v1": float(brier_v1),
            "test_idx": test_idx.tolist(),
            "p_a_te": p_a_te.tolist(),
            "p_v1_te": p_v1_te.tolist(),
            "y_te": y_te.tolist(),
        })

    diffs = np.array([r["auc_diff"] for r in cpcv_results])
    delong_ps = [r["delong_p"] for r in cpcv_results]
    auc_a_mean = float(np.nanmean([r["auc_a"] for r in cpcv_results]))
    auc_v1_mean = float(np.nanmean([r["auc_v1"] for r in cpcv_results]))
    diff_mean = float(np.nanmean(diffs))
    diff_std = float(np.nanstd(diffs, ddof=1))
    diff_se = diff_std / math.sqrt(len(diffs))
    diff_ci_lo = diff_mean - 1.96 * diff_se
    diff_ci_hi = diff_mean + 1.96 * diff_se
    p_combined_stouffer = stouffer_combine(delong_ps)
    p_combined_fisher = fisher_combine(delong_ps)
    p_bonferroni = float(np.nanmin(delong_ps) * len(delong_ps))
    gate_a_pass = (diff_mean >= 0.04) and (p_combined_stouffer < 0.01)

    cpcv_summary = {
        "method_a": "Per-fold top-100 screening (de Prado AFML §8.5); fixed-HP CPCV-honest selection",
        "screening_hp": SCREEN_HP,
        "top_k": TOP_K,
        "n_paths": len(paths),
        "K": CPCV_K, "N": CPCV_N,
        "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS,
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "auc_a_mean": auc_a_mean,
        "auc_v1_mean": auc_v1_mean,
        "diff_mean": diff_mean,
        "diff_std": diff_std,
        "diff_se": float(diff_se),
        "diff_95ci": [float(diff_ci_lo), float(diff_ci_hi)],
        "delong_p_per_path": delong_ps,
        "delong_p_combined_stouffer": p_combined_stouffer,
        "delong_p_combined_fisher": p_combined_fisher,
        "delong_p_min_bonferroni": p_bonferroni,
        "gate_a_threshold": "diff_mean >= 0.04 AND combined DeLong p < 0.01",
        "gate_a_pass": bool(gate_a_pass),
        "computed_at": utc_now(),
    }
    print(f"  Gate (a): diff_mean={diff_mean:+.4f}, combined p={p_combined_stouffer:.6f}, PASS={gate_a_pass}")

    with open(OUT_DIR / "cpcv_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": cpcv_summary, "paths": cpcv_results, "fold_meta": fold_meta}, f, indent=2)

    # ===== PBO =====
    print(f"\n[6/7] PBO computation (Bailey & López de Prado 2014)...")
    pbo_below_median = 0
    pbo_path_records = []
    for path_idx in range(len(paths)):
        is_aucs = np.array([hp_is_aucs_arch_a[h][path_idx] for h in range(n_hp)])
        oos_aucs = np.array([hp_path_aucs_arch_a[h][path_idx] for h in range(n_hp)])
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
    pbo_summary = {
        "method": "BLP 2014; CPCV paths as S splits; below-median rank metric",
        "n_splits": len(pbo_path_records),
        "n_hp_grid": n_hp,
        "pbo": float(pbo),
        "below_median_count": int(pbo_below_median),
        "gate_b_threshold": "PBO < 0.5",
        "gate_b_pass": bool(pbo < 0.5),
        "path_records": pbo_path_records,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "pbo_results.json", "w", encoding="utf-8") as f:
        json.dump(pbo_summary, f, indent=2)
    print(f"  PBO = {pbo:.4f}")

    # ===== Cross-instrument =====
    print(f"\n[7/7] Cross-instrument breakdown (CPCV pred aggregation)...")
    pred_a_all = np.full(len(df), np.nan)
    pred_v1_all = np.full(len(df), np.nan)
    pred_count = np.zeros(len(df), dtype=int)
    for r in cpcv_results:
        for k_, ti in enumerate(r["test_idx"]):
            cur_a = pred_a_all[ti] if not np.isnan(pred_a_all[ti]) else 0.0
            cur_v1 = pred_v1_all[ti] if not np.isnan(pred_v1_all[ti]) else 0.0
            pred_a_all[ti] = cur_a + r["p_a_te"][k_]
            pred_v1_all[ti] = cur_v1 + r["p_v1_te"][k_]
            pred_count[ti] += 1
    pred_a_all = pred_a_all / np.maximum(pred_count, 1)
    pred_v1_all = pred_v1_all / np.maximum(pred_count, 1)

    df["__group"] = df["__symbol"].map(GROUP_MAP).fillna("residual")
    cross_results = {}
    for grp, sub in df.groupby("__group"):
        idx = sub.index.values
        y_grp = y[idx]
        pa = pred_a_all[idx]
        pv1 = pred_v1_all[idx]
        valid = ~(np.isnan(pa) | np.isnan(pv1))
        if valid.sum() < 30:
            cross_results[grp] = {"n": int(valid.sum()), "auc_a": None, "auc_v1": None,
                                  "auc_diff": None, "lift_sign_positive": None, "below_min_n": True}
            continue
        auc_a_g = safe_auc(y_grp[valid], pa[valid])
        auc_v1_g = safe_auc(y_grp[valid], pv1[valid])
        cross_results[grp] = {
            "n": int(valid.sum()),
            "auc_a": float(auc_a_g) if not math.isnan(auc_a_g) else None,
            "auc_v1": float(auc_v1_g) if not math.isnan(auc_v1_g) else None,
            "auc_diff": float(auc_a_g - auc_v1_g) if not (math.isnan(auc_a_g) or math.isnan(auc_v1_g)) else None,
            "lift_sign_positive": (auc_a_g > auc_v1_g) if not (math.isnan(auc_a_g) or math.isnan(auc_v1_g)) else None,
            "below_min_n": False,
        }
    n_groups_pass = sum(1 for v in cross_results.values()
                        if v["lift_sign_positive"] and not v["below_min_n"])
    n_groups_eligible = sum(1 for v in cross_results.values() if not v["below_min_n"])
    cross_summary = {
        "method": "Aggregate OOS CPCV predictions (mean across paths), per-group AUC arch_a vs v1",
        "groups": cross_results,
        "n_groups_pass": int(n_groups_pass),
        "n_groups_eligible": int(n_groups_eligible),
        "gate_d_threshold_actual_4_groups": "AUC_a > AUC_v1 on >=3 of 4 effective groups (n>=30)",
        "gate_d_pass_actual_4": bool(n_groups_pass >= 3),
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "cross_instrument_results.json", "w", encoding="utf-8") as f:
        json.dump(cross_summary, f, indent=2)
    for grp, v in cross_results.items():
        marker = "PASS" if v["lift_sign_positive"] else ("BELOW_N" if v["below_min_n"] else "FAIL")
        print(f"  {grp}: n={v['n']}, AUC_a={v['auc_a']}, AUC_v1={v['auc_v1']}, diff={v['auc_diff']} [{marker}]")
    print(f"  Cross-instrument: {n_groups_pass}/{n_groups_eligible} positive lift")

    # ===== Final feature aggregation + final-cohort model =====
    print("\n[Final] Aggregating per-path top-100 -> top features by frequency, fitting global model...")
    feat_freq: dict[str, int] = {}
    feat_total_gain: dict[str, float] = {}
    for r in per_path_top100:
        for entry in r["top100"]:
            f_ = entry["feature"]
            feat_freq[f_] = feat_freq.get(f_, 0) + 1
            feat_total_gain[f_] = feat_total_gain.get(f_, 0.0) + entry["gain"]
    # Rank by frequency (ties broken by total gain)
    ranked = sorted(feat_freq.items(), key=lambda kv: (kv[1], feat_total_gain.get(kv[0], 0.0)), reverse=True)
    aggregated_top = [
        {"feature": f, "freq_in_top100": c, "total_gain_across_paths": feat_total_gain[f], "family": family_of(f)}
        for f, c in ranked[:200]  # save top-200 for analysis
    ]

    # Fit final model on top-100 by frequency
    final_top_features = [e["feature"] for e in aggregated_top[:TOP_K]]
    sort_perm = np.argsort(dates.values)
    n_inner = len(sort_perm) // 8
    inner_val = sort_perm[-n_inner:]
    inner_train = sort_perm[:-n_inner]
    X_final_tr = X_v2_full[final_top_features].iloc[inner_train]
    X_final_iv = X_v2_full[final_top_features].iloc[inner_val]
    final_model = train_lgbm(X_final_tr, y[inner_train], X_final_iv, y[inner_val], best_hp, len(inner_train))
    final_model.booster_.save_model(str(OUT_DIR / "k54_arch_a.lgb"))

    # Final-model top-30 (for surface-level comparison)
    importances = final_model.feature_importances_
    f_imp = sorted(
        [(final_top_features[i], float(importances[i])) for i in range(len(final_top_features))],
        key=lambda x: x[1], reverse=True,
    )
    top30_global = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in f_imp[:30]]

    # Per-group top-10 (re-fit per group on top-100 features)
    per_group_top10 = {}
    for grp, sub in df.groupby("__group"):
        idx_grp = sub.index.values
        if len(idx_grp) < 30:
            continue
        try:
            m_g = train_lgbm(X_v2_full[final_top_features].iloc[idx_grp], y[idx_grp], None, None, best_hp, len(idx_grp))
            imp = m_g.feature_importances_
            grp_imp = sorted(
                [(final_top_features[i], float(imp[i])) for i in range(len(final_top_features))],
                key=lambda x: x[1], reverse=True,
            )
            per_group_top10[grp] = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in grp_imp[:10]]
        except Exception as e:
            per_group_top10[grp] = [{"error": str(e)}]

    with open(OUT_DIR / "top_features.json", "w", encoding="utf-8") as f:
        json.dump({
            "selected_hp_idx": best_hp_idx,
            "selected_hp": best_hp,
            "cpcv_mean_oos_auc_at_selected_hp": selected_oos_mean,
            "aggregated_top200_by_path_frequency": aggregated_top,
            "final_model_top30": top30_global,
            "per_group_top10": per_group_top10,
            "per_path_top100": per_path_top100,
            "computed_at": utc_now(),
        }, f, indent=2)

    # ===== meta.json =====
    meta = {
        "k54_version": "v2_arch_a",
        "architecture": "Per-fold top-100 feature screening (de Prado AFML §8.5)",
        "screening_hp": SCREEN_HP,
        "top_k_per_fold": TOP_K,
        "training_spec": {
            "data_cutoff_utc": DATA_CUTOFF,
            "cohort_size": int(len(df)),
            "cohort_max_date": str(df["__date"].max())[:10],
            "n_features_post_v2_prune": int(len(feature_cols)),
            "regime_as_feature": True,
            "v1_baseline_features": list(X_v1.columns),
            "v1_baseline_n_features": int(X_v1.shape[1]),
        },
        "selected_hp": best_hp,
        "selected_hp_idx": best_hp_idx,
        "selected_hp_cpcv_mean_oos_auc": selected_oos_mean,
        "cpcv_config": {"K": CPCV_K, "N": CPCV_N, "n_paths": len(paths),
                        "purge_days": PURGE_DAYS, "embargo_days": EMBARGO_DAYS},
        "rows_per_feature_effective_per_fold": float(528 / TOP_K),
        "code_revisions": {
            "v2_baseline_meta": str(V2_DIR / "meta.json"),
            "scout_matrix": str(SCOUT_PARQUET),
        },
        "wallclock_total_seconds": time.time() - t_start,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n=== Architecture A DONE in {time.time()-t_start:.0f}s ===")
    print(f"\nGate verdicts (Arch A):")
    print(f"  (a) CPCV paired: diff_mean={diff_mean:+.4f}, p_combined={p_combined_stouffer:.6f}, "
          f"PASS={gate_a_pass}")
    print(f"  (b) PBO: {pbo:.4f}")
    print(f"  (d) Cross-instrument (4-group): {n_groups_pass}/{n_groups_eligible}")


if __name__ == "__main__":
    main()
