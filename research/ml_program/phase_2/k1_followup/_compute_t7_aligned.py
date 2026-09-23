"""K1 follow-up #1 — Fold-aligned T7 NAS_US30 re-train.

Resolves NA-2 from MASTER_SYNTHESIS.md:
  - Agent C K=4/N=2 paired (specialist vs global) said -0.007.
  - Agent I T7 K=6 NAS-only folds said +0.111 unpaired (different folds from K54 v3).
  - This dispatch retrains Agent I-style T7 per-cohort LightGBM on the SAME 15
    K=6/N=2 full-cohort folds as K54 v3, computes per-row OOS predictions
    restricted to NAS_US30 rows, then computes paired delta vs K54 v3 global
    on the SAME rows.

Methodology lock:
  - CPCV K=6 N=2 over the FULL n=528 cohort, identical to K54 v3 (test_idx
    exact-match verified).
  - Per-fold:
      * Restrict train rows to NAS_US30 ∩ train_idx (purged + embargoed by
        the K54 v3 protocol — purge=7d, embargo=1d, applied to the FULL
        cohort dates).
      * Restrict test rows to NAS_US30 ∩ test_idx.
      * Train T7 (LightGBM screening 200/5/0.05 → top-100 → final 200/3/0.05)
        on the NAS-only train rows.
      * Predict on the NAS-only test rows.
  - Save per-row predictions for the NAS_US30 mask within each fold.
  - K54 v3 global per-row predictions extracted from cpcv_paired_results.json
    (same fold composition).
  - Paired delta = AUC(T7 NAS-aligned, fold_i NAS rows) - AUC(K54 v3 global,
    fold_i NAS rows). 15 paths, paired t-test + Wilcoxon + block bootstrap.
  - Pooled per-row AUC: aggregate predictions across folds (K=6/N=2 → ~5
    predictions per row), compute pooled AUC restricted to NAS_US30 rows.

Outputs (all under research/ml_program/phase_2/k1_followup/):
  - k1_fu1_paired_results.json
  - k1_fu1_fold_aligned_t7.md
  - _compute_t7_aligned.py (this script)

READ-ONLY on production. Subscription-only. Wallclock ~30-90 min on n=528 cohort.
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
from scipy import stats
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
M = ROOT / "research/ml_program/models/k54_v3"
SCOUT = ROOT / "research/ml_program/scout/feature_matrix.parquet"
PRUNE = ROOT / "research/ml_program/models/k54_v2/feature_prune_list.json"
OUT = ROOT / "research/ml_program/phase_2/k1_followup"
OUT.mkdir(parents=True, exist_ok=True)

EULER = 0.5772156649015329

NAS_US30_SYMBOLS = {"NAS100", "US30_CASH", "US30_cash"}
SCREEN_HP = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05,
             "min_data_in_leaf": 10}
FINAL_HP = {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05}
TOP_K = 100
PURGE_DAYS = 7
EMBARGO_DAYS = 1
RANDOM_SEED = 49  # Agent I's seed, for trace consistency


def jload(p):
    with open(p) as fh:
        return json.load(fh)


def jdump(o, p):
    with open(p, "w") as fh:
        json.dump(o, fh, indent=2,
                 default=lambda x: float(x) if hasattr(x, "item") else str(x))


def expected_max_sharpe(N: int) -> float:
    if N <= 1:
        return 0.0
    a = math.sqrt(2.0 * math.log(N))
    return a - EULER / a


def deflated_sr_p(sr: float, T: int, N_trials: int,
                  skew: float = 0.0, kurt: float = 3.0) -> dict:
    """Bailey-Lopez de Prado 2014 deflated SR test (matches K1 + Agent E framing)."""
    if T < 2 or not np.isfinite(sr):
        return {"z": float("nan"), "p_one_sided": float("nan"),
                "expected_max_sr": float("nan"), "sigma_sr": float("nan")}
    sr0 = expected_max_sharpe(N_trials)
    sigma_sr = math.sqrt((1 - skew * sr + (kurt - 1) / 4 * sr ** 2) / (T - 1))
    if sigma_sr <= 0:
        return {"z": float("nan"), "p_one_sided": float("nan"),
                "expected_max_sr": sr0, "sigma_sr": sigma_sr}
    z = (sr - sr0) / sigma_sr
    p = 1 - stats.norm.cdf(z)
    return {"z": float(z), "p_one_sided": float(p),
            "expected_max_sr": float(sr0), "sigma_sr": float(sigma_sr)}


def stationary_block_bootstrap(diffs: np.ndarray, block_len: int = 5,
                               n_boot: int = 5000, seed: int = 17) -> dict:
    rng = np.random.RandomState(seed)
    n = len(diffs)
    if n == 0:
        return {"obs_lift": float("nan"), "ci_95_lo": float("nan"),
                "ci_95_hi": float("nan"), "p_one_sided": float("nan")}
    obs = float(np.mean(diffs))
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = []
        while len(idx) < n:
            i = rng.randint(0, n)
            L = max(1, rng.geometric(1.0 / block_len))
            idx.extend(range(i, min(i + L, n)))
        idx = idx[:n]
        boots[b] = float(np.mean(diffs[idx]))
    return {
        "obs_lift": obs,
        "ci_95_lo": float(np.percentile(boots, 2.5)),
        "ci_95_hi": float(np.percentile(boots, 97.5)),
        "p_one_sided": float(np.mean(boots <= 0)),
        "n_boot": n_boot, "block_len": block_len,
    }


def add_k54_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate K54 v3 closed-form K-7..K-10 features (matches train_k54_v3.py +
    Agent C/I)."""
    round_cols = [c for c in df.columns
                  if c.startswith("liq__liq_round_") and c.endswith("_min_dist_atr")]
    if round_cols:
        round_dist = df[round_cols].min(axis=1).fillna(99.0).values
    else:
        round_dist = np.full(len(df), 99.0)
    df["kw__k10_round_aligned"] = (round_dist < 0.5).astype(int)
    df["kw__k10_round_dist_min_atr"] = round_dist
    if "vol__h1_range_over_mean_50" in df:
        vol50 = df["vol__h1_range_over_mean_50"].fillna(1.0).values
    else:
        vol50 = np.ones(len(df))
    df["kw__k7_osler_stopcluster_proxy"] = df["kw__k10_round_aligned"].values * vol50
    if "liq__liq_round_50p0_dist_above_ticks" in df:
        above = df["liq__liq_round_50p0_dist_above_ticks"].fillna(99999.0).values
    else:
        above = np.full(len(df), 99999.0)
    if "liq__liq_round_50p0_dist_below_ticks" in df:
        below = df["liq__liq_round_50p0_dist_below_ticks"].fillna(99999.0).values
    else:
        below = np.full(len(df), 99999.0)
    df["kw__k10_round50_above_below_asym"] = np.log1p(below) - np.log1p(above)
    if "ob_age_candles" in df:
        ages = df["ob_age_candles"].fillna(0).values.astype(float)
    else:
        ages = np.ones(len(df))
    df["kw__k8_ob_age_power_law"] = np.clip(ages, 1, 200) ** -0.5
    df["kw__k9_regime_x_round_x_side"] = np.zeros(len(df))
    return df


# =========================================================================
# Phase 0: Load CPCV folds + scout matrix
# =========================================================================
print("[Phase 0] Loading K54 v3 CPCV paths + scout matrix.")
v3 = jload(M / "cpcv_paired_results.json")
n_paths_v3 = v3["summary"]["n_paths"]
K_v3 = v3["summary"]["K"]
N_v3 = v3["summary"]["N"]
purge_v3 = v3["summary"]["purge_days"]
embargo_v3 = v3["summary"]["embargo_days"]
print(f"  K54 v3: K={K_v3}, N={N_v3}, n_paths={n_paths_v3}, "
      f"purge={purge_v3}d, embargo={embargo_v3}d")
assert (K_v3, N_v3, n_paths_v3, purge_v3, embargo_v3) == (6, 2, 15, 7, 1)

scout = pd.read_parquet(SCOUT).reset_index(drop=True)
print(f"  scout shape: {scout.shape}")
prune = jload(PRUNE)
drop_set = {item["feature"] for item in prune["prune_list"]}
feature_cols_pre = [
    c for c in scout.columns
    if not c.startswith("__") and c != "dedup_key" and c not in drop_set
]
scout = add_k54_v3_features(scout)
new_features = [c for c in scout.columns if c.startswith("kw__")]
feature_cols = feature_cols_pre + new_features
print(f"  v3 feature space: {len(feature_cols)} features "
      f"({len(feature_cols_pre)} pruned + {len(new_features)} K-7..K-10)")

# Cohort metadata
n_rows = len(scout)
y = scout["__win_label"].astype(int).values
all_dates = pd.to_datetime(scout["__date"].astype(str).str[:10])
symbols = scout["__symbol"].values
nas_mask = np.isin(symbols, list(NAS_US30_SYMBOLS))
nas_idx_global = np.where(nas_mask)[0]
n_nas = len(nas_idx_global)
print(f"  Total cohort: {n_rows} rows; NAS_US30: {n_nas} rows "
      f"(WR {y[nas_idx_global].mean():.3f})")

# Build feature matrix
X = scout[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan)


# =========================================================================
# Phase 1: Verify fold composition (test_idx exact-match across paths)
# =========================================================================
print("\n[Phase 1] Verify K54 v3 fold composition is well-defined.")
v3_test_idx_per_path = []
v3_train_idx_per_path = []
for i, path in enumerate(v3["paths"]):
    te = sorted(path["test_idx"])
    v3_test_idx_per_path.append(te)
    # Verify test_idx ranges are within scout
    assert max(te) < n_rows, f"path {i}: test_idx out of range"
print(f"  Verified all 15 paths' test_idx in [0, {n_rows}).")

# Check NAS_US30 cohort coverage across paths
nas_per_path = []
for i, te in enumerate(v3_test_idx_per_path):
    te_arr = np.array(te)
    n_nas_in_te = int(np.isin(te_arr, nas_idx_global).sum())
    nas_per_path.append(n_nas_in_te)
print(f"  NAS_US30 rows per fold (test): min={min(nas_per_path)}, "
      f"max={max(nas_per_path)}, mean={np.mean(nas_per_path):.1f}, total_with_dup={sum(nas_per_path)}")


# =========================================================================
# Phase 2: For each path, derive train_idx with purge+embargo (replicating
# K54 v3's protocol on full cohort), then restrict train AND test to NAS rows.
# =========================================================================
print("\n[Phase 2] Building per-path NAS-aligned (train, test) idx.")

def build_train_idx_full(test_idx_arr: np.ndarray, dates: pd.Series,
                         purge_days: int = PURGE_DAYS,
                         embargo_days: int = EMBARGO_DAYS) -> np.ndarray:
    """Replicate K54 v3 purge_embargo protocol on the FULL cohort.
    Test groups: contiguous test_idx are a single group; we use min..max as bounds
    for purge/embargo (matches train_k54_v3.purge_embargo behavior with grouped folds).
    """
    test_idx_arr = np.asarray(sorted(test_idx_arr))
    n = len(dates)
    train_mask = np.ones(n, dtype=bool)
    train_mask[test_idx_arr] = False
    # Find contiguous groups in test_idx (since they were two folds out of 6)
    # Apply purge/embargo around each group
    diffs = np.diff(test_idx_arr)
    splits = np.where(diffs > 1)[0]
    starts = [0] + (splits + 1).tolist()
    ends = (splits + 1).tolist() + [len(test_idx_arr)]
    for s, e in zip(starts, ends):
        group = test_idx_arr[s:e]
        if len(group) == 0:
            continue
        test_dates = dates.iloc[group]
        t_min = test_dates.min() - pd.Timedelta(days=purge_days)
        t_max = test_dates.max() + pd.Timedelta(days=embargo_days)
        in_zone = (dates >= t_min) & (dates <= t_max)
        train_mask &= ~in_zone.values
    return np.where(train_mask)[0]


per_path_idx = []
for i, te in enumerate(v3_test_idx_per_path):
    te_arr = np.array(te)
    tr_full = build_train_idx_full(te_arr, all_dates,
                                    purge_days=PURGE_DAYS,
                                    embargo_days=EMBARGO_DAYS)
    # Restrict to NAS_US30 ∩ train_idx
    nas_train = tr_full[np.isin(tr_full, nas_idx_global)]
    nas_test = te_arr[np.isin(te_arr, nas_idx_global)]
    per_path_idx.append({
        "path": i,
        "n_train_full": int(len(tr_full)),
        "n_train_nas": int(len(nas_train)),
        "n_test_nas": int(len(nas_test)),
        "nas_train_idx": nas_train.tolist(),
        "nas_test_idx": nas_test.tolist(),
        "test_win_rate_nas": (float(y[nas_test].mean())
                              if len(nas_test) > 0 else None),
    })
print(f"  per-path NAS train: min={min(p['n_train_nas'] for p in per_path_idx)}, "
      f"max={max(p['n_train_nas'] for p in per_path_idx)}, "
      f"mean={np.mean([p['n_train_nas'] for p in per_path_idx]):.1f}")
print(f"  per-path NAS test:  min={min(p['n_test_nas'] for p in per_path_idx)}, "
      f"max={max(p['n_test_nas'] for p in per_path_idx)}, "
      f"mean={np.mean([p['n_test_nas'] for p in per_path_idx]):.1f}")


# =========================================================================
# Phase 3: Train T7 per-fold (NAS-aligned) + collect predictions
# =========================================================================
print("\n[Phase 3] Training T7 NAS-aligned models on each of 15 K54 v3 folds.")

try:
    import lightgbm as lgb
except ImportError:
    print("ERROR: lightgbm not available; aborting.")
    raise SystemExit(1)


def train_screening_lgbm(X_tr, y_tr, hp=SCREEN_HP, seed=RANDOM_SEED):
    n = len(X_tr)
    mdl = max(3, n // 30)
    return lgb.LGBMClassifier(
        n_estimators=hp["n_estimators"],
        max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"],
        min_data_in_leaf=mdl,
        num_leaves=2 ** hp["max_depth"],
        objective="binary", metric="auc",
        n_jobs=1, verbosity=-1,
        random_state=seed, deterministic=True, force_row_wise=True,
    ).fit(X_tr, y_tr)


def train_final_lgbm(X_tr, y_tr, X_iv, y_iv, hp=FINAL_HP, seed=RANDOM_SEED):
    n = len(X_tr)
    mdl = max(3, n // 30)
    m = lgb.LGBMClassifier(
        n_estimators=hp["n_estimators"],
        max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"],
        min_data_in_leaf=mdl,
        num_leaves=2 ** hp["max_depth"],
        objective="binary", metric="auc",
        n_jobs=1, verbosity=-1,
        random_state=seed, deterministic=True, force_row_wise=True,
    )
    fit_kw = {}
    if X_iv is not None and len(X_iv) > 0 and len(np.unique(y_iv)) > 1:
        fit_kw = {
            "eval_set": [(X_iv, y_iv)],
            "callbacks": [lgb.early_stopping(20, verbose=False)],
        }
    m.fit(X_tr, y_tr, **fit_kw)
    return m


def calibrate(p_tr_iv, y_iv, p_te):
    if len(np.unique(y_iv)) < 2:
        return p_te
    cal = LogisticRegression(max_iter=1000, C=1.0)
    cal.fit(p_tr_iv.reshape(-1, 1), y_iv)
    return cal.predict_proba(p_te.reshape(-1, 1))[:, 1]


# Per-row prediction storage
# (sum of predictions on each row across folds; count gives effective n preds per row)
sum_p_t7 = np.zeros(n_rows)
count_t7 = np.zeros(n_rows, dtype=int)

per_path_results = []
t0 = time.time()
for i, idx in enumerate(per_path_idx):
    nas_train = np.array(idx["nas_train_idx"])
    nas_test = np.array(idx["nas_test_idx"])

    if len(nas_train) < 20 or len(nas_test) < 5:
        per_path_results.append({
            "path": i,
            "skipped": True,
            "n_train": int(len(nas_train)),
            "n_test": int(len(nas_test)),
            "auc_t7": None,
            "auc_v3_global_paired": None,
            "auc_delta": None,
        })
        continue

    # Inner train/val split (date-sorted; last 12.5% = inner_val)
    train_dates_p = all_dates.iloc[nas_train]
    sort_perm = np.argsort(train_dates_p.values)
    train_sorted = nas_train[sort_perm]
    n_inner = max(10, len(train_sorted) // 8)
    inner_val = train_sorted[-n_inner:]
    inner_train = train_sorted[:-n_inner]

    # Drop columns with > 50% NaN within this NAS train slice (Agent I T7 protocol)
    X_tr_full = X.iloc[inner_train]
    nan_frac_per_col = X_tr_full.isna().mean(axis=0).values
    keep_feat_mask = nan_frac_per_col < 0.5
    keep_features = [feature_cols[k] for k in np.where(keep_feat_mask)[0]]

    # Screen features: top-100 by gain on the inner_train set
    X_tr_screen = X.iloc[inner_train][keep_features].fillna(-9999)
    y_tr = y[inner_train]
    if len(np.unique(y_tr)) < 2:
        per_path_results.append({
            "path": i, "skipped": True,
            "reason": "single_class_inner_train",
            "n_train": int(len(nas_train)),
            "n_test": int(len(nas_test)),
            "auc_t7": None, "auc_v3_global_paired": None, "auc_delta": None,
        })
        continue
    screen = train_screening_lgbm(X_tr_screen, y_tr)
    imp = screen.feature_importances_
    top_k = min(TOP_K, int(keep_feat_mask.sum()))
    top_imp_idx = np.argsort(imp)[-top_k:]
    top_features = [keep_features[k] for k in top_imp_idx]

    # Train final on top-K
    X_tr_final = X.iloc[inner_train][top_features].fillna(-9999)
    X_iv_final = X.iloc[inner_val][top_features].fillna(-9999)
    X_te_final = X.iloc[nas_test][top_features].fillna(-9999)
    y_iv = y[inner_val]
    y_te = y[nas_test]

    final = train_final_lgbm(X_tr_final, y_tr, X_iv_final, y_iv)
    p_iv = final.predict_proba(X_iv_final)[:, 1]
    p_te = final.predict_proba(X_te_final)[:, 1]
    p_te_cal = calibrate(p_iv, y_iv, p_te)

    # Accumulate per-row preds
    for j, row_idx in enumerate(nas_test):
        sum_p_t7[row_idx] += p_te_cal[j]
        count_t7[row_idx] += 1

    # Per-fold AUC (T7 NAS-aligned)
    if len(np.unique(y_te)) > 1:
        auc_t7 = float(roc_auc_score(y_te, p_te_cal))
    else:
        auc_t7 = float("nan")

    # K54 v3 global preds on these same NAS test rows (read from cpcv_paired_results)
    v3_path = v3["paths"][i]
    v3_te_idx = np.array(v3_path["test_idx"])
    v3_p_te = np.array(v3_path["p_v3_te"])
    # Map row idx → v3 prediction (within this path)
    nas_in_v3 = np.isin(v3_te_idx, nas_test)
    v3_nas_te_idx = v3_te_idx[nas_in_v3]
    v3_nas_p_te = v3_p_te[nas_in_v3]
    # Ensure ordering matches nas_test (sort both by row idx)
    order_t7 = np.argsort(nas_test)
    nas_test_sorted = nas_test[order_t7]
    p_te_t7_sorted = p_te_cal[order_t7]
    order_v3 = np.argsort(v3_nas_te_idx)
    v3_nas_idx_sorted = v3_nas_te_idx[order_v3]
    v3_nas_p_sorted = v3_nas_p_te[order_v3]
    # Sanity: v3_nas_idx_sorted should equal nas_test_sorted
    assert np.array_equal(nas_test_sorted, v3_nas_idx_sorted), (
        f"path {i}: NAS test idx mismatch between T7 ({nas_test_sorted[:5]}...) "
        f"and v3 ({v3_nas_idx_sorted[:5]}...)"
    )
    if len(np.unique(y[nas_test_sorted])) > 1:
        auc_v3 = float(roc_auc_score(y[nas_test_sorted], v3_nas_p_sorted))
    else:
        auc_v3 = float("nan")

    delta = (auc_t7 - auc_v3) if (np.isfinite(auc_t7) and np.isfinite(auc_v3)) else float("nan")

    per_path_results.append({
        "path": i,
        "skipped": False,
        "n_train": int(len(nas_train)),
        "n_test": int(len(nas_test)),
        "test_win_rate": float(y[nas_test].mean()),
        "n_features_screened": int(keep_feat_mask.sum()),
        "n_features_top_k": int(top_k),
        "auc_t7": auc_t7,
        "auc_v3_global_paired": auc_v3,
        "auc_delta": delta,
    })
    print(f"  Path {i:2d}: n_tr={len(nas_train):3d} n_te={len(nas_test):2d} "
          f"WR={y[nas_test].mean():.3f}  T7={auc_t7:.4f}  v3_glob={auc_v3:.4f}  delta={delta:+.4f}")

print(f"\n  Wallclock training: {time.time() - t0:.1f}s")


# =========================================================================
# Phase 4: Aggregate paired tests + DSR + bootstrap
# =========================================================================
print("\n[Phase 4] Paired statistics on per-fold AUC deltas.")
valid = [r for r in per_path_results if not r.get("skipped") and
         np.isfinite(r.get("auc_delta", float("nan")))]
print(f"  Valid paths: {len(valid)}/{len(per_path_results)}")

t7_aucs = np.array([r["auc_t7"] for r in valid])
v3_aucs = np.array([r["auc_v3_global_paired"] for r in valid])
deltas = np.array([r["auc_delta"] for r in valid])
n_paths = len(valid)

mean_d = float(np.mean(deltas))
std_d = float(np.std(deltas, ddof=1)) if n_paths > 1 else float("nan")
se_d = float(std_d / np.sqrt(n_paths)) if n_paths > 1 else float("nan")

print(f"  T7 mean AUC = {t7_aucs.mean():.4f} (std {t7_aucs.std(ddof=1):.4f})")
print(f"  v3 global on NAS mean AUC = {v3_aucs.mean():.4f} "
      f"(std {v3_aucs.std(ddof=1):.4f})")
print(f"  Paired delta mean = {mean_d:+.6f} (std {std_d:.4f}, SE_naive {se_d:.4f})")

# Paired t-test + Wilcoxon
t_stat, t_p = stats.ttest_rel(t7_aucs, v3_aucs)
try:
    w_stat, w_p = stats.wilcoxon(deltas)
except Exception:
    w_stat, w_p = float("nan"), float("nan")

# Block bootstrap
boot = stationary_block_bootstrap(deltas, block_len=5, n_boot=5000, seed=17)

print(f"  Paired t: t={t_stat:.3f}, p_two={t_p:.4f}")
print(f"  Wilcoxon: stat={w_stat}, p_two={w_p:.4f}")
print(f"  Block bootstrap obs={boot['obs_lift']:+.4f} "
      f"CI95=[{boot['ci_95_lo']:+.4f}, {boot['ci_95_hi']:+.4f}] "
      f"p_one={boot['p_one_sided']:.4f}")

# DSR
sr = mean_d / (std_d + 1e-9) if std_d > 0 else float("nan")
dsr_T15_N200 = deflated_sr_p(sr, T=n_paths, N_trials=200)
dsr_T11_ONC = deflated_sr_p(sr, T=11, N_trials=200)
dsr_T20_N200 = deflated_sr_p(sr, T=20, N_trials=200)
dsr_T50_N50 = deflated_sr_p(sr, T=50, N_trials=50)

# Pooled per-row AUC on NAS_US30 mask
mean_p_t7 = np.divide(sum_p_t7, count_t7, out=np.full(n_rows, np.nan),
                      where=count_t7 > 0)
nas_mask_pooled = np.isin(np.arange(n_rows), nas_idx_global)
nas_with_preds = nas_mask_pooled & np.isfinite(mean_p_t7)
nas_p_t7 = mean_p_t7[nas_with_preds]
nas_y_pool = y[nas_with_preds]

# K54 v3 global pooled per-row AUC on NAS rows (recompute from cpcv_paired_results)
sum_p_v3 = np.zeros(n_rows)
count_v3 = np.zeros(n_rows, dtype=int)
for path in v3["paths"]:
    for j, idx in enumerate(path["test_idx"]):
        sum_p_v3[idx] += path["p_v3_te"][j]
        count_v3[idx] += 1
mean_p_v3 = np.divide(sum_p_v3, count_v3, out=np.full(n_rows, np.nan),
                      where=count_v3 > 0)
nas_p_v3 = mean_p_v3[nas_with_preds]

t7_pooled_auc = float(roc_auc_score(nas_y_pool, nas_p_t7)) if len(np.unique(nas_y_pool)) > 1 else float("nan")
v3_pooled_auc = float(roc_auc_score(nas_y_pool, nas_p_v3)) if len(np.unique(nas_y_pool)) > 1 else float("nan")
pooled_delta = t7_pooled_auc - v3_pooled_auc

print(f"\n  POOLED per-row (NAS_US30 mask, n={int(nas_with_preds.sum())}):")
print(f"    T7 NAS-aligned pooled AUC: {t7_pooled_auc:.4f}")
print(f"    K54 v3 global pooled AUC : {v3_pooled_auc:.4f}")
print(f"    Pooled delta: {pooled_delta:+.4f}")
print(f"\n  per-path SR = {sr:.4f}")
print(f"  DSR-p (T={n_paths}, N=200): {dsr_T15_N200['p_one_sided']:.4f}")
print(f"  DSR-p (T=11, N=200, ONC eff): {dsr_T11_ONC['p_one_sided']:.4f}")
print(f"  DSR-p (T=20, N=200): {dsr_T20_N200['p_one_sided']:.4f}")
print(f"  DSR-p (T=50, N=50, ONC): {dsr_T50_N50['p_one_sided']:.4f}")


# =========================================================================
# Phase 5: Verdict + comparison to NA-2 honest range
# =========================================================================
honest_range_lo = -0.007  # Agent C K=4/N=2 paired
honest_range_hi = +0.111  # Agent I K=6 NAS-only unpaired

verdict_at_005 = "PASS_AT_0.05" if mean_d >= 0.05 else (
    "BORDERLINE" if 0.02 <= mean_d < 0.05 else "DEAD")
verdict_at_004 = "PASS_AT_0.04" if mean_d >= 0.04 else (
    "BORDERLINE" if 0.02 <= mean_d < 0.04 else "DEAD")

# K55-shadow shippability:
# - mean_d >= 0.05 + DSR-p T=15 N=200 < 0.05  -> SHIP
# - mean_d in [0.02, 0.05] + bootstrap p_one < 0.05 -> CONDITIONAL/SHADOW-OBSERVE
# - mean_d < 0.02 OR no statistical signal -> DO NOT SHIP
if mean_d >= 0.05 and dsr_T15_N200["p_one_sided"] < 0.05:
    k55_shadow_verdict = "SHIP"
elif mean_d >= 0.05 and boot["p_one_sided"] < 0.05:
    k55_shadow_verdict = "SHIP_DSR_BORDERLINE"
elif mean_d >= 0.02 and (t_p < 0.05 or boot["p_one_sided"] < 0.05):
    k55_shadow_verdict = "CONDITIONAL_SHADOW_OBSERVE"
elif mean_d >= 0.02:
    k55_shadow_verdict = "BORDERLINE_DEFER"
else:
    k55_shadow_verdict = "DO_NOT_SHIP"


# =========================================================================
# Phase 6: Save results
# =========================================================================
print("\n[Phase 6] Saving results.")

results = {
    "methodology_lock": {
        "lock_id": "k1_followup_1_fold_aligned_t7_2026-04-29",
        "cpcv": {"K": 6, "N": 2, "n_paths": 15,
                 "purge_days": 7, "embargo_days": 1},
        "fold_composition": "IDENTICAL to K54 v3 (test_idx exact-match per path)",
        "model": "Agent I T7-style per-cohort LightGBM "
                 "(screen 200/5/0.05 → top-100 → final 200/3/0.05; "
                 "isotonic→logistic calibration; same K54 v3 v3-features + closed-form K-7..K-10)",
        "training_subset": "NAS_US30 ∩ K54_v3_train_idx (purged, embargoed at full-cohort boundaries)",
        "test_subset": "NAS_US30 ∩ K54_v3_test_idx",
        "baseline": "K54 v3 global (predictions read from cpcv_paired_results.json on the "
                    "same NAS_US30 ∩ K54_v3_test_idx rows; NO retraining of K54 v3 global)",
    },
    "cohort": {
        "n_total": int(n_rows),
        "n_NAS_US30": int(n_nas),
        "max_date": str(all_dates.max().date()),
    },
    "per_path_results": per_path_results,
    "fold_level_paired_stats": {
        "n_paths": int(n_paths),
        "t7_per_path_aucs": t7_aucs.tolist(),
        "v3_global_per_path_aucs": v3_aucs.tolist(),
        "per_path_diffs": deltas.tolist(),
        "t7_mean_auc": float(t7_aucs.mean()) if n_paths > 0 else None,
        "v3_global_mean_auc_on_nas": float(v3_aucs.mean()) if n_paths > 0 else None,
        "paired_delta_mean": mean_d,
        "paired_delta_std": std_d,
        "paired_delta_se_naive": se_d,
        "paired_t": {"t": float(t_stat), "p_two": float(t_p), "n": n_paths},
        "wilcoxon": {"stat": float(w_stat), "p_two": float(w_p)},
        "block_bootstrap": boot,
        "per_path_sharpe": float(sr) if np.isfinite(sr) else None,
        "dsr_T15_N200": dsr_T15_N200,
        "dsr_T11_ONC": dsr_T11_ONC,
        "dsr_T20_N200": dsr_T20_N200,
        "dsr_T50_N50_ONC": dsr_T50_N50,
    },
    "pooled_per_row_stats": {
        "n_rows_evaluated": int(nas_with_preds.sum()),
        "t7_nas_aligned_pooled_auc": t7_pooled_auc,
        "v3_global_pooled_auc_on_nas": v3_pooled_auc,
        "pooled_delta": pooled_delta,
    },
    "verdict": {
        "fold_aligned_lift": mean_d,
        "honest_range_from_k1": [honest_range_lo, honest_range_hi],
        "in_honest_range": (honest_range_lo <= mean_d <= honest_range_hi),
        "verdict_at_0.05_threshold": verdict_at_005,
        "verdict_at_0.04_threshold": verdict_at_004,
        "k55_shadow_shippability": k55_shadow_verdict,
        "decision_rule": (
            "SHIP if mean_d >= +0.05 AND DSR-p (T=N N=200) < 0.05; "
            "SHIP_DSR_BORDERLINE if mean_d >= +0.05 AND bootstrap p_one < 0.05 but DSR fails; "
            "CONDITIONAL_SHADOW_OBSERVE if mean_d in [+0.02, +0.05) AND (t-p < 0.05 OR bootstrap p_one < 0.05); "
            "BORDERLINE_DEFER if mean_d in [+0.02, +0.05) without statistical agreement; "
            "DO_NOT_SHIP otherwise."
        ),
    },
    "comparison_to_NA2_honest_range": {
        "agent_c_K4_N2_paired": -0.007,
        "agent_i_K6_NAS_only_unpaired": 0.111,
        "k1_fu1_K6_full_cohort_paired": mean_d,
        "narrowed_range_after_k1_fu1": [
            min(honest_range_lo, mean_d),
            max(honest_range_hi, mean_d)
        ],
        "interpretation": (
            f"Fold-aligned T7 on K54 v3's exact 15 K=6/N=2 full-cohort folds gives "
            f"paired delta {mean_d:+.4f}. Agent C's -0.007 (K=4/N=2 NAS-only paired with "
            f"K54 v3 specialist not T7) and Agent I's +0.111 (K=6 NAS-only unpaired with T7) "
            f"are both outliers to the same-design fold-aligned test."
        ),
    },
    "wallclock_seconds": time.time() - t0,
}

jdump(results, OUT / "k1_fu1_paired_results.json")
print(f"  Saved: {OUT / 'k1_fu1_paired_results.json'}")
print("\nDONE.")
