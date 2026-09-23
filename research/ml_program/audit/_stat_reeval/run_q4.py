"""Q4 — Per-path feature-stability Jaccard.

Re-train K54 v2 LightGBM with selected HP (n_estimators=100, max_depth=5, lr=0.1)
per CPCV path; extract top-30 features by global gain per path; compute pairwise
Jaccard across the 15 paths.
"""
import json, os
from itertools import combinations
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
PRUNE_JSON = ROOT / "research/ml_program/models/k54_v2/feature_prune_list.json"
META_JSON = ROOT / "research/ml_program/models/k54_v2/meta.json"
CPCV_JSON = ROOT / "research/ml_program/models/k54_v2/cpcv_paired_results.json"
OUT_JSON = ROOT / "research/ml_program/audit/_stat_reeval/q4_jaccard.json"
OUT_TOP30 = ROOT / "research/ml_program/audit/_stat_reeval/q4_per_path_top30.json"

DATA_CUTOFF = "2026-04-28"
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
RANDOM_SEED = 42
SELECTED_HP = {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1}


def load_v2_matrix():
    df = pd.read_parquet(SCOUT_PARQUET)
    assert df["__date"].max() <= DATA_CUTOFF, f"Cutoff violated: max={df['__date'].max()}"
    print(f"Cohort: {len(df)} rows, max_date={df['__date'].max()}")
    feature_cols_raw = [c for c in df.columns if not c.startswith("__")]
    return df, feature_cols_raw


def apply_prune(feature_cols_raw):
    pl = json.load(open(PRUNE_JSON))
    drop_set = {p["feature"] for p in pl["prune_list"]}
    return [c for c in feature_cols_raw if c not in drop_set]


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
    return [
        ([i for i in range(len(folds)) if i not in test_combo], list(test_combo))
        for test_combo in combinations(range(len(folds)), n)
    ]


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


def main():
    print(f"=== Q4 per-path feature-stability Jaccard (HP={SELECTED_HP}) ===")
    df, feature_cols_raw = load_v2_matrix()
    feature_cols = apply_prune(feature_cols_raw)
    print(f"Features post-prune: {len(feature_cols)}")
    X_v2 = df[feature_cols].astype(float).copy()
    X_v2 = X_v2.replace([np.inf, -np.inf], np.nan)
    y = df["__win_label"].astype(int).values
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    folds = time_indexed_folds(dates, CPCV_K)
    paths = cpcv_paths(folds, CPCV_N)
    print(f"Folds: {[len(f) for f in folds]}")
    print(f"Paths: {len(paths)}")

    per_path_top30 = []
    for path_idx, (train_groups, test_groups) in enumerate(paths):
        train_idx_raw = np.concatenate([folds[i] for i in train_groups])
        test_groups_list = [folds[i] for i in test_groups]
        train_idx = purge_embargo(train_idx_raw, test_groups_list, dates, PURGE_DAYS, EMBARGO_DAYS)
        train_dates_path = dates.iloc[train_idx]
        sort_perm = np.argsort(train_dates_path.values)
        train_sorted = train_idx[sort_perm]
        n_inner = max(20, len(train_sorted) // 8)
        inner_val = train_sorted[-n_inner:]
        inner_train = train_sorted[:-n_inner]

        X_tr = X_v2.iloc[inner_train]
        X_iv = X_v2.iloc[inner_val]
        y_tr = y[inner_train]
        y_iv = y[inner_val]

        model = train_lgbm(X_tr, y_tr, X_iv, y_iv, SELECTED_HP, len(inner_train))
        importances = model.feature_importances_
        feat_imp = sorted(
            [(feature_cols[i], float(importances[i])) for i in range(len(feature_cols))],
            key=lambda x: x[1], reverse=True,
        )
        # Restrict to features with > 0 gain (LGBM may report ties of 0)
        top30 = [{"feature": f, "gain": g} for f, g in feat_imp[:30]]
        n_nonzero = sum(1 for f, g in feat_imp if g > 0)
        print(f"Path {path_idx:2d} | train n={len(inner_train)} | nonzero-gain={n_nonzero} | top1: {feat_imp[0][0]} ({feat_imp[0][1]:.0f})")
        per_path_top30.append({
            "path": path_idx,
            "train_groups": train_groups,
            "test_groups": list(test_groups),
            "n_train": int(len(inner_train)),
            "n_inner_val": int(len(inner_val)),
            "n_features_with_nonzero_gain": int(n_nonzero),
            "top30": top30,
        })

    # ---- Compute Jaccard ----
    sets = [set(item["feature"] for item in p["top30"]) for p in per_path_top30]
    pairs = list(combinations(range(len(sets)), 2))
    jaccs = []
    for i, j in pairs:
        si, sj = sets[i], sets[j]
        union = si | sj
        inter = si & sj
        jacc = len(inter) / len(union) if union else float("nan")
        jaccs.append(jacc)
    jaccs = np.array(jaccs)
    print(f"\nMean pairwise Jaccard ({len(pairs)} pairs): {jaccs.mean():.4f}")
    print(f"Median: {np.median(jaccs):.4f}, min: {jaccs.min():.4f}, max: {jaccs.max():.4f}")

    # Stable core: features in EVERY path's top-30
    core_all = set.intersection(*sets)
    print(f"\nFeatures in ALL 15 paths' top-30 (stable core): {len(core_all)}")
    print(sorted(core_all))

    # Features in >= 80% (12 of 15)
    from collections import Counter
    feat_counter = Counter()
    for s in sets:
        for f in s:
            feat_counter[f] += 1
    core_80 = sorted([f for f, c in feat_counter.items() if c >= 12])
    print(f"\nFeatures in >= 80% (>=12 of 15): {len(core_80)}")
    for f in core_80:
        print(f"  {f}  (in {feat_counter[f]} paths)")

    # Verdict
    mean_jacc = float(jaccs.mean())
    n_core_all = len(core_all)
    if mean_jacc > 0.5 or n_core_all >= 10:
        verdict = "STABLE"
    elif 0.3 <= mean_jacc <= 0.5:
        verdict = "MODERATE"
    elif mean_jacc < 0.3 or n_core_all <= 3:
        verdict = "UNSTABLE"
    else:
        verdict = "MODERATE"
    # tighten: also check unstable condition
    if mean_jacc < 0.3 and n_core_all <= 3:
        verdict = "UNSTABLE"
    print(f"\nVerdict: {verdict}")
    print(f"  mean Jacc: {mean_jacc:.4f} (STABLE >0.5; MODERATE 0.3-0.5; UNSTABLE <0.3)")
    print(f"  stable-core (in all 15): {n_core_all} (STABLE >=10; UNSTABLE <=3)")

    out = {
        "selected_hp": SELECTED_HP,
        "n_paths": len(per_path_top30),
        "n_pairs": len(pairs),
        "mean_pairwise_jaccard": float(jaccs.mean()),
        "median_pairwise_jaccard": float(np.median(jaccs)),
        "min_pairwise_jaccard": float(jaccs.min()),
        "max_pairwise_jaccard": float(jaccs.max()),
        "stable_core_count_in_all_15": int(len(core_all)),
        "stable_core_in_all_15": sorted(core_all),
        "core_count_in_at_least_80pct": int(len(core_80)),
        "core_in_at_least_80pct": [
            {"feature": f, "n_paths": int(feat_counter[f])} for f in core_80
        ],
        "verdict": verdict,
        "feature_count_distribution": {
            str(c): int(sum(1 for v in feat_counter.values() if v == c))
            for c in sorted(set(feat_counter.values()))
        },
    }
    os.makedirs(OUT_JSON.parent, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    with open(OUT_TOP30, "w", encoding="utf-8") as f:
        json.dump({"per_path_top30": per_path_top30}, f, indent=2)
    print(f"\nSaved: {OUT_JSON}")
    print(f"Saved: {OUT_TOP30}")


if __name__ == "__main__":
    main()
