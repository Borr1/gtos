"""Parallelized B=1000 white-noise null distribution for K54 v2 Q1.3 gate (e).

Strategy:
- Reads the selected hyperparameters from training_log.json (or meta.json).
- Reads CPCV path caches by re-deriving (folds + paths + per-group purge).
- Parallelizes across 1000 shuffle seeds using joblib (default 8 workers; tunable).

Per shuffle: shuffle the realized_r labels with a deterministic seed, run CPCV
K=6,N=2 (15 paths) with the selected HPs, return the mean OOS AUC across paths.

This is an alternative to the in-script null loop in train_k54_v2.py which is
single-threaded. With 8 workers on the 12-core box, expected speedup is ~6x:
- Single-thread B=1000: ~3-12 hours
- 8-worker B=1000: ~30-90 minutes

If train_k54_v2.py has not yet produced a meta.json, this script falls back to a
default selected HP (the brief's mid-range: n_estimators=200, max_depth=5, lr=0.05).

Output:
- research/ml_program/models/k54_v2/null_distribution.json (overwrites
  if already present)
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score

import lightgbm as lgb

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
OUT_DIR = ROOT / "research/ml_program/models/k54_v2"
RANDOM_SEED = 42
CPCV_K = 6
CPCV_N = 2
PURGE_DAYS = 7
EMBARGO_DAYS = 1
N_WORKERS = 8


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


def apply_patch1_prune(feature_cols, df):
    """Reproduce the same prune as train_k54_v2.py."""
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


def shuffle_one_path(seed, X_arr, y, path_caches, hp):
    """Run CPCV for one shuffle seed, return mean OOS AUC across paths."""
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
    print(f"=== Parallel B=1000 null — {utc_now()} ===")
    t_start = time.time()

    # Load matrix + apply prune
    df = pd.read_parquet(SCOUT_PARQUET)
    feature_cols_raw = [c for c in df.columns if not c.startswith("__")]
    feature_cols = apply_patch1_prune(feature_cols_raw, df)
    print(f"Matrix: {len(df)} rows × {len(feature_cols)} features (post-prune)")

    y = df["__win_label"].astype(int).values
    dates = pd.to_datetime(df["__date"].astype(str).str[:10])
    X = df[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan)
    X_arr = X.values
    print(f"X array: {X_arr.shape}")

    # CPCV path caches
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
            "inner_train": inner_train,
            "inner_val": inner_val,
            "test_idx": test_idx,
        })

    # Selected HP — read from meta.json if present, else fall back
    hp_path = OUT_DIR / "meta.json"
    if hp_path.exists():
        with open(hp_path, encoding="utf-8") as f:
            meta = json.load(f)
        hp = meta.get("selected_hp", {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05})
        print(f"HP from meta.json: {hp}")
    else:
        # Fall back: try training_log.json
        tlog_path = OUT_DIR / "training_log.json"
        if tlog_path.exists():
            with open(tlog_path, encoding="utf-8") as f:
                tlog = json.load(f)
            hp_idx = tlog.get("selected_hp_idx")
            grid = tlog.get("hp_grid", [])
            if grid and hp_idx is not None and 0 <= hp_idx < len(grid):
                hp = grid[hp_idx]
                print(f"HP from training_log.json: {hp}")
            else:
                hp = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05}
                print(f"Fallback HP: {hp}")
        else:
            hp = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05}
            print(f"Default HP (no meta yet): {hp}")

    B = 1000
    print(f"Running {B} shuffles with {N_WORKERS} workers...")

    seeds = list(range(1, B + 1))
    chunk = 50
    null_aucs = []
    for batch_start in range(0, len(seeds), chunk):
        batch = seeds[batch_start:batch_start + chunk]
        t0 = time.time()
        results = Parallel(n_jobs=N_WORKERS, backend="loky", verbose=0)(
            delayed(shuffle_one_path)(s, X_arr, y, path_caches, hp) for s in batch
        )
        # Sort by seed and append
        for s, a in sorted(results, key=lambda r: r[0]):
            null_aucs.append(a)
        elapsed = time.time() - t0
        total = time.time() - t_start
        est_remaining = total * (B - len(null_aucs)) / max(len(null_aucs), 1)
        print(f"  Shuffles {len(null_aucs)}/{B}: batch in {elapsed:.0f}s, total {total:.0f}s, est remaining {est_remaining:.0f}s")

    null_aucs_arr = np.array(null_aucs)

    # Read observed AUC from cpcv_paired_results.json
    cpcv_path = OUT_DIR / "cpcv_paired_results.json"
    if cpcv_path.exists():
        with open(cpcv_path, encoding="utf-8") as f:
            cpcv = json.load(f)
        obs_auc = cpcv["summary"]["auc_v2_mean"]
    else:
        obs_auc = float("nan")

    p_empirical = float(np.mean(null_aucs_arr >= obs_auc))
    p99 = float(np.percentile(null_aucs_arr, 99))
    p999 = float(np.percentile(null_aucs_arr, 99.9))
    p_smoothed = float((np.sum(null_aucs_arr >= obs_auc) + 1) / (len(null_aucs_arr) + 1))
    z_score = float((obs_auc - np.mean(null_aucs_arr)) / np.std(null_aucs_arr)) if np.std(null_aucs_arr) > 0 else float("nan")
    gate_e_pass = (obs_auc >= p99) and (p_empirical < 0.01)

    null_summary = {
        "B": B,
        "method": "Per shuffle: permute labels with seed; rerun CPCV K=6,N=2 with selected HP (from meta.json); report mean OOS AUC. Parallelized across 8 workers via joblib.",
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
        "wallclock_seconds": time.time() - t_start,
        "computed_at": utc_now(),
    }
    with open(OUT_DIR / "null_distribution.json", "w", encoding="utf-8") as f:
        json.dump(null_summary, f, indent=2)
    print(f"\nGate (e): obs={obs_auc:.4f}, null_mean={np.mean(null_aucs_arr):.4f}, p99={p99:.4f}, p_emp={p_empirical:.6f}")
    print(f"GATE (e) PASS: {gate_e_pass}")
    print(f"Wallclock: {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
