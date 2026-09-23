"""K54 v3 Diagnostic — Isolate W-unit contribution to gate failure.

Re-runs the per-fold screening + fixed-HP CPCV with:
  Variant 1: W-unit ON (current K54 v3 spec)
  Variant 2: W-unit OFF (pure equal weighting)
  Variant 3: W-unit OFF + no K-7..K-10 features (pure Arch A reproduction)

Rapid (<2 min) ablation to pinpoint why K54 v3 underperformed Arch A.
Uses screening top-100 + first 5 HP combos for speed.
"""
from __future__ import annotations
import json
import math
import time
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

warnings.filterwarnings("ignore")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
V2_DIR = ROOT / "research/ml_program/models/k54_v2"
OUT_DIR = ROOT / "research/ml_program/models/k54_v3"

CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
TOP_K = 100
RANDOM_SEED = 42
HYPER_GRID = [
    {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.05},
    {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05},
    {"n_estimators": 400, "max_depth": 5, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.1},
    {"n_estimators": 200, "max_depth": 7, "learning_rate": 0.05},
]


def safe_auc(y, p):
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


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
    return [(list(set(range(k)) - set(t)), list(t))
            for t in combinations(range(k), n)]


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


def train_lgbm(X_tr, y_tr, X_val, y_val, hp, n_train, sample_weight=None):
    model = lgb.LGBMClassifier(
        n_estimators=hp["n_estimators"], max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"], min_data_in_leaf=max(3, n_train // 30),
        num_leaves=2 ** hp["max_depth"], objective="binary", metric="auc",
        n_jobs=1, verbosity=-1, random_state=RANDOM_SEED,
        deterministic=True, force_row_wise=True,
    )
    fit_kw = {}
    if X_val is not None and len(X_val) > 0:
        fit_kw = {"eval_set": [(X_val, y_val)],
                  "callbacks": [lgb.early_stopping(20, verbose=False)]}
    if sample_weight is not None:
        fit_kw["sample_weight"] = sample_weight
    model.fit(X_tr, y_tr, **fit_kw)
    return model


def screen_lgbm(X_tr, y_tr, sample_weight=None):
    fit_kw = {}
    if sample_weight is not None:
        fit_kw["sample_weight"] = sample_weight
    return lgb.LGBMClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        min_data_in_leaf=10, num_leaves=32, objective="binary",
        metric="auc", n_jobs=1, verbosity=-1, random_state=RANDOM_SEED,
        deterministic=True, force_row_wise=True,
    ).fit(X_tr, y_tr, **fit_kw)


def compute_w_units(df):
    per_instrument_dv = {
        "XAUUSD": 100.0, "XAGUSD": 50.0, "USDJPY": 667.0,
        "GBPUSD": 100000.0, "GBPJPY": 667.0, "NAS100": 1.0, "US30_CASH": 5.0,
    }
    symbols = df["__symbol"].values
    dv = np.array([per_instrument_dv.get(s, 1.0) for s in symbols])
    if "vol__h1_realized_vol_50" in df.columns:
        rv = df["vol__h1_realized_vol_50"].fillna(df["vol__h1_realized_vol_50"].median()).values
    else:
        rv = np.ones(len(df))
    w = dv * np.clip(rv, 1e-6, None)
    w_norm = w / np.maximum(w.mean(), 1e-9)
    return np.clip(w_norm, 0.1, 10.0)


def add_k54_v3_features(df):
    new_features = {}
    round_cols = [c for c in df.columns
                  if c.startswith("liq__liq_round_") and c.endswith("_min_dist_atr")]
    if round_cols:
        round_dist_min = df[round_cols].min(axis=1).fillna(99.0).values
        round_aligned = (round_dist_min < 0.5).astype(int)
        new_features["kw__k10_round_aligned"] = round_aligned
        new_features["kw__k10_round_dist_min_atr"] = round_dist_min
    else:
        round_aligned = np.zeros(len(df))
        new_features["kw__k10_round_aligned"] = round_aligned
        new_features["kw__k10_round_dist_min_atr"] = np.ones(len(df)) * 99.0
    if "vol__h1_range_over_mean_50" in df.columns:
        vol_proxy = df["vol__h1_range_over_mean_50"].fillna(1.0).values
        new_features["kw__k7_osler_stopcluster_proxy"] = round_aligned * vol_proxy
        if "liq__liq_round_50p0_dist_above_ticks" in df.columns:
            above_dist = df["liq__liq_round_50p0_dist_above_ticks"].fillna(99999.0).values
            below_dist = df.get("liq__liq_round_50p0_dist_below_ticks", pd.Series([99999.0] * len(df))).fillna(99999.0).values
            asym = np.log1p(below_dist) - np.log1p(above_dist)
            new_features["kw__k10_round50_above_below_asym"] = asym
        else:
            new_features["kw__k10_round50_above_below_asym"] = np.zeros(len(df))
    else:
        new_features["kw__k7_osler_stopcluster_proxy"] = np.zeros(len(df))
        new_features["kw__k10_round50_above_below_asym"] = np.zeros(len(df))
    age_col = None
    for cand in ("ob_age_candles", "struct__M15__ob_age_candles_top1"):
        if cand in df.columns:
            age_col = cand
            break
    if age_col is not None:
        ages = df[age_col].fillna(0).values.astype(float)
        ages_clip = np.clip(ages, 1.0, 200.0)
        new_features["kw__k8_ob_age_power_law"] = ages_clip ** (-0.5)
    else:
        new_features["kw__k8_ob_age_power_law"] = np.ones(len(df))
    long_flag = (df["__direction"] == "LONG").astype(int).values
    if "reg__regime_aligned_v1" in df.columns:
        regime_v1 = df["reg__regime_aligned_v1"].fillna(0).values
        new_features["kw__k9_regime_x_round_x_side"] = regime_v1 * round_aligned * long_flag
    else:
        new_features["kw__k9_regime_x_round_x_side"] = np.zeros(len(df))
    for col, vals in new_features.items():
        df[col] = vals
    return df


def run_variant(label, X_full, y, dates, paths, folds, w_units, feature_cols, hyper_grid):
    """Runs per-path screening + fixed-HP final pass on the given setup."""
    print(f"\n>>> Variant: {label}")
    t0 = time.time()
    hp_aucs = {i: [] for i in range(len(hyper_grid))}
    per_path_top100 = []

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

        # Screening
        X_screen = X_full.iloc[inner_train].fillna(X_full.iloc[inner_train].median())
        y_screen = y[inner_train]
        if w_units is not None:
            w_train = w_units[inner_train]
        else:
            w_train = None
        sm = screen_lgbm(X_screen, y_screen, sample_weight=w_train)
        imp = sm.feature_importances_
        top_idx = np.argsort(-imp)[:TOP_K]
        top_feat = [feature_cols[i] for i in top_idx]
        per_path_top100.append(set(top_feat))

        X_a_tr = X_full[top_feat].iloc[inner_train]
        X_a_iv = X_full[top_feat].iloc[inner_val]
        X_a_te = X_full[top_feat].iloc[test_idx]
        y_tr = y[inner_train]
        y_iv = y[inner_val]
        y_te = y[test_idx]

        for hp_idx, hp in enumerate(hyper_grid):
            try:
                m = train_lgbm(X_a_tr, y_tr, X_a_iv, y_iv, hp, len(inner_train), sample_weight=w_train)
                p_te = m.predict_proba(X_a_te)[:, 1]
                auc = safe_auc(y_te, p_te)
            except Exception:
                auc = float("nan")
            hp_aucs[hp_idx].append(auc)

    # Best HP
    hp_means = np.array([np.nanmean(hp_aucs[i]) for i in range(len(hyper_grid))])
    best_idx = int(np.nanargmax(hp_means))
    elapsed = time.time() - t0

    # Feature stability
    jaccards = []
    for i in range(len(per_path_top100)):
        for j in range(i + 1, len(per_path_top100)):
            inter = len(per_path_top100[i] & per_path_top100[j])
            union = len(per_path_top100[i] | per_path_top100[j])
            jaccards.append(inter / union if union > 0 else 0.0)

    print(f"  Selected HP idx={best_idx}, OOS mean AUC={hp_means[best_idx]:.4f}, "
          f"all HP means: {hp_means.round(4).tolist()}")
    print(f"  Mean Jaccard top-100 = {np.mean(jaccards):.4f}")
    print(f"  Elapsed {elapsed:.0f}s")
    return {
        "label": label,
        "best_hp_idx": best_idx,
        "best_hp_oos_mean_auc": float(hp_means[best_idx]),
        "all_hp_oos_means": hp_means.round(4).tolist(),
        "mean_jaccard_top100": float(np.mean(jaccards)),
        "elapsed_s": elapsed,
    }


def main():
    df = pd.read_parquet(SCOUT_PARQUET)
    df["dedup_key"] = list(zip(df["__date"].astype(str).str[:10], df["__symbol"], df["__direction"], df["__framework"], df["__realized_r"].round(3)))
    feature_cols_raw = [c for c in df.columns if not c.startswith("__") and c != "dedup_key"]
    # Apply v2 prune
    with open(V2_DIR / "feature_prune_list.json", "r", encoding="utf-8") as f:
        prune_data = json.load(f)
    drop = {item["feature"] for item in prune_data["prune_list"]}
    feature_cols_pruned = [c for c in feature_cols_raw if c not in drop]
    df = add_k54_v3_features(df)
    new_features = [c for c in df.columns if c.startswith("kw__")]
    feature_cols_v3 = feature_cols_pruned + new_features
    feature_cols_arch_a = feature_cols_pruned  # no kw__

    y = df["__win_label"].astype(int).values
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    folds = time_indexed_folds(dates, CPCV_K)
    paths = cpcv_paths(folds, CPCV_N)
    w_units = compute_w_units(df)

    X_v3_full = df[feature_cols_v3].astype(float).copy().replace([np.inf, -np.inf], np.nan)
    X_arch_a_full = df[feature_cols_arch_a].astype(float).copy().replace([np.inf, -np.inf], np.nan)

    print(f"Cohort: {len(df)} rows; v3 features {len(feature_cols_v3)}; arch_a features {len(feature_cols_arch_a)}")
    print(f"K54 v3 new features ({len(new_features)}): {new_features}")
    print(f"W-unit min/max: {w_units.min():.3f} / {w_units.max():.3f}")

    results = []
    # Variant 1: K54 v3 features + W-unit ON
    results.append(run_variant(
        "K54 v3 features + W-unit ON (current spec)",
        X_v3_full, y, dates, paths, folds, w_units, feature_cols_v3, HYPER_GRID,
    ))
    # Variant 2: K54 v3 features + W-unit OFF
    results.append(run_variant(
        "K54 v3 features + W-unit OFF",
        X_v3_full, y, dates, paths, folds, None, feature_cols_v3, HYPER_GRID,
    ))
    # Variant 3: arch_a features only + W-unit OFF (Q1.3 Arch A reproduction)
    results.append(run_variant(
        "Arch A reproduction (no kw__ + W-unit OFF)",
        X_arch_a_full, y, dates, paths, folds, None, feature_cols_arch_a, HYPER_GRID,
    ))

    # Save
    with open(OUT_DIR / "diagnostic_w_unit_ablation.json", "w", encoding="utf-8") as f:
        json.dump({"variants": results, "feature_cols_count": {
            "v3": len(feature_cols_v3), "arch_a": len(feature_cols_arch_a),
        }}, f, indent=2)
    print("\n=== Ablation summary ===")
    for r in results:
        print(f"  {r['label']}: best AUC={r['best_hp_oos_mean_auc']:.4f}, Jaccard={r['mean_jaccard_top100']:.4f}")


if __name__ == "__main__":
    main()
