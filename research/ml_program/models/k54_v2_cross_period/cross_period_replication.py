"""K54 v2 Cross-Period Replication Auditor

Re-trains K54 v2 + paired K54 v1 baseline on a strict cross-period split:
  - Train: rows with `__date < 2026-01-01`
  - Test: rows with `2026-01-01 <= __date <= 2026-04-28`

Hyperparameter selection: 4-fold CV (time-ordered) on TRAIN cohort only,
27-combo grid, mean OOS AUC selects fixed HP. Final model fit on full TRAIN.

Both K54 v2 (1234 features post-Patch-1 prune) and K54 v1 (15 features per
meta.json) trained on identical cohorts. DeLong paired test on test cohort.

Outputs to research/ml_program/models/k54_v2_cross_period/.
"""
from __future__ import annotations

import json
import math
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
K54_V2_DIR = ROOT / "research/ml_program/models/k54_v2"
OUT_DIR = ROOT / "research/ml_program/models/k54_v2_cross_period"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_CUTOFF = "2026-04-28"
SPLIT_DATE = "2026-01-01"
RANDOM_SEED = 42

HYPER_GRID = [
    {"n_estimators": ne, "max_depth": md, "learning_rate": lr}
    for ne in (100, 200, 400)
    for md in (3, 5, 7)
    for lr in (0.01, 0.05, 0.1)
]  # 27 combos

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
    """Load scout feature matrix; build dedup key + return feature col list."""
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
    assert df["dedup_key"].nunique() == len(df), "V2 matrix has duplicate dedup keys"
    feature_cols = [
        c for c in df.columns
        if not c.startswith("__") and c not in ("dedup_key",)
    ]
    return df, feature_cols


def apply_existing_prune(feature_cols: list[str]) -> list[str]:
    """Apply same Patch-1 prune list as K54 v2 build."""
    prune_path = K54_V2_DIR / "feature_prune_list.json"
    with open(prune_path, "r", encoding="utf-8") as f:
        pl = json.load(f)
    drop_set = {e["feature"] for e in pl["prune_list"]}
    pruned = [c for c in feature_cols if c not in drop_set]
    return pruned


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
    v1d = v1.drop_duplicates(subset="dedup_key", keep="first").copy()
    return v1d


def prepare_v1_X(v1d: pd.DataFrame, dedup_keys: list[tuple]) -> tuple[pd.DataFrame, np.ndarray]:
    """Build K54 v1 design matrix on supplied dedup keys (matches train_k54_v2)."""
    keys_df = pd.DataFrame({"dedup_key": dedup_keys})
    v1_aligned = keys_df.merge(v1d, on="dedup_key", how="left")
    assert len(v1_aligned) == len(dedup_keys), "V1 cohort alignment failed"
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


def time_indexed_4fold(dates: pd.Series) -> list[np.ndarray]:
    """4 contiguous time-ordered fold indices into the train cohort.

    For HP selection: each fold serves once as validation; mean OOS AUC across
    the 4 folds is the score per HP. No purge/embargo (train cohort already
    pre-cohort-of-cross-period; CPCV inside CPCV is overkill at n_train≈93).
    """
    sort_idx = np.argsort(dates.values)
    n = len(sort_idx)
    fold_size = n // 4
    folds = []
    for i in range(4):
        start = i * fold_size
        end = (i + 1) * fold_size if i < 3 else n
        folds.append(sort_idx[start:end])
    return folds


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
    fit_kw = {}
    if X_val is not None and len(X_val) > 0:
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
    calibrator = LogisticRegression(max_iter=1000, C=1.0)
    calibrator.fit(model_proba_tr.reshape(-1, 1), y_tr)
    return calibrator.predict_proba(model_proba_te.reshape(-1, 1))[:, 1]


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
    """DeLong's test for paired AUC difference (matches train_k54_v2 impl)."""
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


def select_hp_via_4fold(
    X: pd.DataFrame, y: np.ndarray, dates: pd.Series,
) -> tuple[int, dict, list[float], list[list[float]]]:
    """Select HP via 4-fold time-ordered CV on TRAIN cohort only.

    Returns (best_hp_idx, best_hp, mean_auc_per_hp, per_fold_auc_per_hp).
    """
    folds = time_indexed_4fold(dates)
    per_hp_aucs: list[list[float]] = [[] for _ in range(len(HYPER_GRID))]
    for hp_idx, hp in enumerate(HYPER_GRID):
        for fold_idx, val_fold in enumerate(folds):
            tr_idx = np.concatenate(
                [folds[i] for i in range(4) if i != fold_idx]
            )
            X_tr = X.iloc[tr_idx]
            y_tr = y[tr_idx]
            X_va = X.iloc[val_fold]
            y_va = y[val_fold]
            try:
                # No early-stop val — keep CV pure; min_data_in_leaf scales
                m = lgb.LGBMClassifier(
                    n_estimators=hp["n_estimators"],
                    max_depth=hp["max_depth"],
                    learning_rate=hp["learning_rate"],
                    min_data_in_leaf=max(3, len(tr_idx) // 30),
                    num_leaves=2 ** hp["max_depth"],
                    objective="binary",
                    metric="auc",
                    n_jobs=1,
                    verbosity=-1,
                    random_state=RANDOM_SEED,
                    deterministic=True,
                    force_row_wise=True,
                )
                m.fit(X_tr, y_tr)
                p = m.predict_proba(X_va)[:, 1]
                a = safe_auc(y_va, p)
            except Exception:
                a = float("nan")
            per_hp_aucs[hp_idx].append(a)
    mean_auc = [float(np.nanmean(per_hp_aucs[i])) if any(
        not (isinstance(x, float) and math.isnan(x)) for x in per_hp_aucs[i]
    ) else float("nan") for i in range(len(HYPER_GRID))]
    best_hp_idx = int(np.nanargmax(mean_auc))
    return best_hp_idx, HYPER_GRID[best_hp_idx], mean_auc, per_hp_aucs


def main():
    print(f"=== K54 v2 cross-period replication — {utc_now()} ===")
    t_start = time.time()

    # ===== Load + prune =====
    print("\n[1/8] Loading scout feature matrix + applying Patch-1 prune list...")
    df, feature_cols_raw = load_v2_matrix()
    feature_cols = apply_existing_prune(feature_cols_raw)
    print(f"  Matrix: {len(df)} rows × {len(feature_cols_raw)} pre-prune features")
    print(f"  Post-prune: {len(feature_cols)} features (Patch-1, 13 dropped)")

    # ===== Build cross-period split =====
    df["date_only"] = pd.to_datetime(df["__date"].astype(str).str[:10])
    train_mask = df["date_only"] < pd.Timestamp(SPLIT_DATE)
    test_mask = (
        (df["date_only"] >= pd.Timestamp(SPLIT_DATE))
        & (df["date_only"] <= pd.Timestamp(DATA_CUTOFF))
    )
    n_train = int(train_mask.sum())
    n_test = int(test_mask.sum())
    print(f"\n[2/8] Cross-period split (split={SPLIT_DATE}):")
    print(f"  TRAIN n={n_train}, TEST n={n_test}")
    print("  Train cohort symbol breakdown:")
    print(df[train_mask]["__symbol"].value_counts().to_string())
    print("  Test cohort symbol breakdown:")
    print(df[test_mask]["__symbol"].value_counts().to_string())

    # ===== Build features =====
    print("\n[3/8] Constructing X matrices (V1 + V2)...")
    v1d = load_v1_baseline_features()
    dedup_keys_train = df.loc[train_mask, "dedup_key"].tolist()
    dedup_keys_test = df.loc[test_mask, "dedup_key"].tolist()
    X_v1_train, y_v1_train = prepare_v1_X(v1d, dedup_keys_train)
    X_v1_test, y_v1_test = prepare_v1_X(v1d, dedup_keys_test)

    y_train = df.loc[train_mask, "__win_label"].astype(int).values
    y_test = df.loc[test_mask, "__win_label"].astype(int).values
    np.testing.assert_array_equal(y_v1_train, y_train)
    np.testing.assert_array_equal(y_v1_test, y_test)

    X_v2_train = df.loc[train_mask, feature_cols].astype(float).copy()
    X_v2_train = X_v2_train.replace([np.inf, -np.inf], np.nan)
    X_v2_test = df.loc[test_mask, feature_cols].astype(float).copy()
    X_v2_test = X_v2_test.replace([np.inf, -np.inf], np.nan)

    dates_train = df.loc[train_mask, "date_only"].reset_index(drop=True)
    print(f"  V2 train: {X_v2_train.shape}, V2 test: {X_v2_test.shape}")
    print(f"  V1 train: {X_v1_train.shape}, V1 test: {X_v1_test.shape}")
    print(f"  Train win-rate: {y_train.mean():.3f}")
    print(f"  Test win-rate: {y_test.mean():.3f}")

    # ===== HP selection on TRAIN via 4-fold CV =====
    print("\n[4/8] Selecting HP for K54 v2 via 4-fold CV on TRAIN cohort...")
    X_v2_train_r = X_v2_train.reset_index(drop=True)
    X_v1_train_r = X_v1_train.reset_index(drop=True)
    best_hp_v2_idx, best_hp_v2, mean_auc_v2, per_fold_v2 = select_hp_via_4fold(
        X_v2_train_r, y_train, dates_train
    )
    print(f"  V2 selected HP: idx={best_hp_v2_idx} {best_hp_v2}")
    print(f"  V2 4-fold mean OOS AUC at selected HP: {mean_auc_v2[best_hp_v2_idx]:.4f}")

    print("\n[5/8] Selecting HP for K54 v1 via 4-fold CV on TRAIN cohort...")
    best_hp_v1_idx, best_hp_v1, mean_auc_v1, per_fold_v1 = select_hp_via_4fold(
        X_v1_train_r, y_train, dates_train
    )
    print(f"  V1 selected HP: idx={best_hp_v1_idx} {best_hp_v1}")
    print(f"  V1 4-fold mean OOS AUC at selected HP: {mean_auc_v1[best_hp_v1_idx]:.4f}")

    # ===== Train final models on full TRAIN =====
    print("\n[6/8] Fitting final models on full TRAIN; calibrating + scoring TEST...")
    # Use last 1/8 of TRAIN (sorted by date) as inner-val for calibration + early stop
    train_dates_arr = dates_train.values
    sort_perm = np.argsort(train_dates_arr)
    n_inner = max(10, len(sort_perm) // 8)
    inner_val = sort_perm[-n_inner:]
    inner_train = sort_perm[:-n_inner]

    final_v2 = train_lgbm(
        X_v2_train_r.iloc[inner_train], y_train[inner_train],
        X_v2_train_r.iloc[inner_val], y_train[inner_val],
        best_hp_v2, len(inner_train),
    )
    p_v2_iv = final_v2.predict_proba(X_v2_train_r.iloc[inner_val])[:, 1]
    p_v2_te_raw = final_v2.predict_proba(X_v2_test)[:, 1]
    p_v2_te = calibrate(p_v2_iv, y_train[inner_val], p_v2_te_raw)
    auc_v2_test = safe_auc(y_test, p_v2_te)
    brier_v2_test = brier_score_loss(y_test, p_v2_te) if len(np.unique(y_test)) > 1 else float("nan")

    final_v1 = train_lgbm(
        X_v1_train_r.iloc[inner_train], y_train[inner_train],
        X_v1_train_r.iloc[inner_val], y_train[inner_val],
        best_hp_v1, len(inner_train),
    )
    p_v1_iv = final_v1.predict_proba(X_v1_train_r.iloc[inner_val])[:, 1]
    p_v1_te_raw = final_v1.predict_proba(X_v1_test)[:, 1]
    p_v1_te = calibrate(p_v1_iv, y_train[inner_val], p_v1_te_raw)
    auc_v1_test = safe_auc(y_test, p_v1_te)
    brier_v1_test = brier_score_loss(y_test, p_v1_te) if len(np.unique(y_test)) > 1 else float("nan")

    auc_diff, p_delong = delong_paired_test(y_test, p_v1_te, p_v2_te)

    # Save final models
    final_v2.booster_.save_model(str(OUT_DIR / "k54_v2.lgb"))
    final_v1.booster_.save_model(str(OUT_DIR / "k54_v1.lgb"))

    print(f"  TEST AUC v2: {auc_v2_test:.4f}")
    print(f"  TEST AUC v1: {auc_v1_test:.4f}")
    print(f"  Diff (v2-v1): {auc_v2_test - auc_v1_test:+.4f}, DeLong p={p_delong:.4f}")
    print(f"  TEST Brier v2: {brier_v2_test:.4f}")
    print(f"  TEST Brier v1: {brier_v1_test:.4f}")

    # ===== Per-group analysis on TEST cohort =====
    print("\n[7/8] Per-group cross-period AUC analysis...")
    test_df = df.loc[test_mask].reset_index(drop=True).copy()
    test_df["__group"] = test_df["__symbol"].map(GROUP_MAP).fillna("residual")
    per_group: dict[str, dict] = {}
    for grp, sub in test_df.groupby("__group"):
        idx = sub.index.values
        y_grp = y_test[idx]
        pv2 = p_v2_te[idx]
        pv1 = p_v1_te[idx]
        if len(idx) < 30:
            per_group[grp] = {
                "n": int(len(idx)),
                "auc_v2": None,
                "auc_v1": None,
                "auc_diff": None,
                "lift_sign_positive": None,
                "below_min_n": True,
            }
            continue
        a_v2 = safe_auc(y_grp, pv2)
        a_v1 = safe_auc(y_grp, pv1)
        per_group[grp] = {
            "n": int(len(idx)),
            "win_rate": float(y_grp.mean()),
            "auc_v2": float(a_v2) if not math.isnan(a_v2) else None,
            "auc_v1": float(a_v1) if not math.isnan(a_v1) else None,
            "auc_diff": float(a_v2 - a_v1) if not (math.isnan(a_v2) or math.isnan(a_v1)) else None,
            "lift_sign_positive": (a_v2 > a_v1) if not (math.isnan(a_v2) or math.isnan(a_v1)) else None,
            "below_min_n": False,
        }
    n_groups_pass = sum(1 for v in per_group.values() if v["lift_sign_positive"])
    n_groups_eligible = sum(1 for v in per_group.values() if not v["below_min_n"])
    for grp, v in per_group.items():
        marker = "PASS" if v["lift_sign_positive"] else (
            "BELOW_N" if v["below_min_n"] else "FAIL"
        )
        print(f"  {grp}: n={v['n']}, AUC_v2={v.get('auc_v2')}, AUC_v1={v.get('auc_v1')}, diff={v.get('auc_diff')} [{marker}]")
    print(f"  n_groups_pass: {n_groups_pass}/{n_groups_eligible}")

    # ===== Top features (cross-period model) =====
    print("\n[8/8] Top-30 features + XAU_XAG group cross-period top-10...")
    importances = final_v2.feature_importances_
    feat_imp_pairs = sorted(
        [(feature_cols[i], float(importances[i])) for i in range(len(feature_cols))],
        key=lambda x: x[1], reverse=True,
    )
    top30 = [{"feature": f, "gain": g, "family": family_of(f)} for f, g in feat_imp_pairs[:30]]
    print("  Top-10 cross-period:")
    for f, g in feat_imp_pairs[:10]:
        print(f"    {f} ({family_of(f)}) gain={g:.1f}")

    # Per-group top-10: train a small model per group on the TEST cohort
    # (we cannot train on TRAIN cohort because it's mostly XAUUSD).
    # Per-group train on TEST is informational (NOT used for headline AUC).
    per_group_top10: dict[str, list[dict]] = {}
    for grp, sub in test_df.groupby("__group"):
        idx_grp = sub.index.values
        if len(idx_grp) < 30:
            continue
        try:
            X_grp = X_v2_test.iloc[idx_grp]
            y_grp = y_test[idx_grp]
            m_g = train_lgbm(X_grp, y_grp, None, None, best_hp_v2, len(idx_grp))
            imp = m_g.feature_importances_
            grp_imp = sorted(
                [(feature_cols[i], float(imp[i])) for i in range(len(feature_cols))],
                key=lambda x: x[1], reverse=True,
            )
            per_group_top10[grp] = [
                {"feature": f, "gain": g, "family": family_of(f)}
                for f, g in grp_imp[:10]
            ]
        except Exception as e:
            per_group_top10[grp] = [{"error": str(e)}]

    # XAU_XAG calendar feature persistence check
    calendar_features = [
        "ts__t_days_to_nearest_opex_signed",
        "ts__t_day_of_year_cos",
        "ts__t_days_to_nearest_holiday_signed",
        "ts__t_day_of_year_sin",
    ]
    cpcv_xau_xag_top10 = {
        "ts__t_days_to_nearest_opex_signed": 44.0,
        "ts__t_day_of_year_cos": 40.0,
        "ts__t_days_to_nearest_holiday_signed": 35.0,
        "ts__t_day_of_year_sin": 28.0,
    }
    xau_xag_top10 = per_group_top10.get("XAU_XAG", [])
    xau_xag_gain_map = {item["feature"]: item["gain"] for item in xau_xag_top10}
    # Also need full importances for XAU_XAG model for the 4 features (may not be in top-10)
    xau_xag_grp_idx = test_df[test_df["__group"] == "XAU_XAG"].index.values
    xau_xag_full_gain: dict[str, float] = {}
    if len(xau_xag_grp_idx) >= 30:
        m_xag = train_lgbm(
            X_v2_test.iloc[xau_xag_grp_idx], y_test[xau_xag_grp_idx],
            None, None, best_hp_v2, len(xau_xag_grp_idx),
        )
        imp_xag = m_xag.feature_importances_
        for f in calendar_features:
            if f in feature_cols:
                fidx = feature_cols.index(f)
                xau_xag_full_gain[f] = float(imp_xag[fidx])

    calendar_persistence: dict[str, dict] = {}
    for f in calendar_features:
        cpcv_g = cpcv_xau_xag_top10.get(f, 0.0)
        cp_g = xau_xag_full_gain.get(f, 0.0)
        ratio = (cp_g / cpcv_g) if cpcv_g > 0 else 0.0
        if ratio >= 0.75:
            verdict = "PERSISTENT"
        elif ratio >= 0.50:
            verdict = "DECAYING"
        else:
            verdict = "OVERFIT"
        calendar_persistence[f] = {
            "cpcv_gain": cpcv_g,
            "cross_period_gain": cp_g,
            "ratio": ratio,
            "drop_pct": (1 - ratio) * 100 if cpcv_g > 0 else None,
            "verdict": verdict,
        }
        print(f"  Calendar {f}: CPCV={cpcv_g:.1f} -> CP={cp_g:.1f} (ratio={ratio:.2f}) -> {verdict}")

    # CPCV reference top-1 feature (vol__h1_range_over_mean_50)
    top_cp_feature_names = [item["feature"] for item in top30]
    top_cp_gains = {item["feature"]: item["gain"] for item in top30}
    cpcv_top1 = "vol__h1_range_over_mean_50"
    cpcv_top1_gain_in_cp = top_cp_gains.get(cpcv_top1, 0.0)
    cpcv_top1_in_cp_top10 = cpcv_top1 in [t["feature"] for t in top30[:10]]
    print(f"\n  CPCV top-1 ({cpcv_top1}): in cross-period top-10? {cpcv_top1_in_cp_top10}, "
          f"gain in CP={cpcv_top1_gain_in_cp:.1f} (CPCV gain=6.0)")

    # ===== Save outputs =====
    # CPCV reference values from existing artifacts
    CPCV_AUC_V2 = 0.5429
    CPCV_AUC_V1 = 0.5120
    CPCV_DIFF_MEAN = 0.0309

    delta_v2 = float(auc_v2_test - CPCV_AUC_V2)
    delta_v1 = float(auc_v1_test - CPCV_AUC_V1)
    delta_diff = float((auc_v2_test - auc_v1_test) - CPCV_DIFF_MEAN)

    if abs(delta_diff) <= 0.01:
        robustness_verdict = "ROBUST"
    elif abs(delta_diff) <= 0.02:
        robustness_verdict = "PARTIAL"
    else:
        robustness_verdict = "NOT_ROBUST"

    if (auc_v2_test - auc_v1_test) * CPCV_DIFF_MEAN < 0:
        robustness_verdict = "NOT_ROBUST_SIGN_FLIP"

    cpcv_per_group_lifts = {
        "XAU_XAG": True,        # CPCV: lift positive
        "NAS_US30": True,       # CPCV: lift positive
        "GBPJPY": False,        # CPCV: lift negative
        "GBPUSD_USDJPY": False, # CPCV: lift negative
    }
    sign_flips = {}
    for grp in ["XAU_XAG", "NAS_US30", "GBPJPY", "GBPUSD_USDJPY"]:
        cpcv_pos = cpcv_per_group_lifts[grp]
        cp = per_group.get(grp, {})
        cp_pos = cp.get("lift_sign_positive")
        sign_flips[grp] = {
            "cpcv_lift_positive": cpcv_pos,
            "cross_period_lift_positive": cp_pos,
            "flipped": (cpcv_pos != cp_pos) if cp_pos is not None else None,
        }

    n_calendar_overfit = sum(
        1 for v in calendar_persistence.values() if v["verdict"] == "OVERFIT"
    )
    n_calendar_decaying = sum(
        1 for v in calendar_persistence.values() if v["verdict"] == "DECAYING"
    )
    if n_calendar_overfit >= 2:
        calendar_overall = "OVERFIT"
    elif n_calendar_overfit + n_calendar_decaying >= 2:
        calendar_overall = "DECAYING"
    else:
        calendar_overall = "PERSISTENT"

    results = {
        "split": {
            "train_max_date": str(df.loc[train_mask, "date_only"].max().date()),
            "train_min_date": str(df.loc[train_mask, "date_only"].min().date()),
            "test_min_date": str(df.loc[test_mask, "date_only"].min().date()),
            "test_max_date": str(df.loc[test_mask, "date_only"].max().date()),
            "n_train": n_train,
            "n_test": n_test,
            "train_win_rate": float(y_train.mean()),
            "test_win_rate": float(y_test.mean()),
            "train_symbol_breakdown": df.loc[train_mask, "__symbol"].value_counts().to_dict(),
            "test_symbol_breakdown": df.loc[test_mask, "__symbol"].value_counts().to_dict(),
            "data_inventory_audit_estimate_train": "~114 (audit)",
            "actual_train_n": n_train,
            "audit_caveat": (
                "Data Inventory Audit Section 10 estimated train n~114 (XAUUSD 108 "
                "+ GBPUSD 6) and explicitly flagged 'Insufficient on its own', "
                "recommending augmentation via 2022-2023 mechanical OB synthesis BEFORE "
                "running cross-period split. Augmentation was NOT performed (out-of-scope "
                "for this audit). Actual n_train=93 (XAUUSD 87 + GBPUSD 6) reflects the "
                "post-dedup reality on the existing scout matrix. The orchestrator brief's "
                "n_train≈280 estimate appears to be aspirational (assumed augmentation)."
            ),
        },
        "hp_selection": {
            "v2_best_hp_idx": best_hp_v2_idx,
            "v2_best_hp": best_hp_v2,
            "v2_4fold_mean_oos_auc": mean_auc_v2[best_hp_v2_idx],
            "v1_best_hp_idx": best_hp_v1_idx,
            "v1_best_hp": best_hp_v1,
            "v1_4fold_mean_oos_auc": mean_auc_v1[best_hp_v1_idx],
            "v2_per_hp_mean_auc": mean_auc_v2,
            "v1_per_hp_mean_auc": mean_auc_v1,
        },
        "test_metrics": {
            "auc_v2_test": float(auc_v2_test),
            "auc_v1_test": float(auc_v1_test),
            "auc_diff": float(auc_v2_test - auc_v1_test),
            "delong_p_two_sided": float(p_delong),
            "brier_v2_test": float(brier_v2_test),
            "brier_v1_test": float(brier_v1_test),
        },
        "cpcv_reference": {
            "cpcv_auc_v2_mean": CPCV_AUC_V2,
            "cpcv_auc_v1_mean": CPCV_AUC_V1,
            "cpcv_diff_mean": CPCV_DIFF_MEAN,
            "delta_auc_v2": delta_v2,
            "delta_auc_v1": delta_v1,
            "delta_diff": delta_diff,
            "robustness_verdict": robustness_verdict,
            "robustness_threshold_doc": (
                "robust |Δ|<=0.01; partial |Δ|<=0.02; not_robust |Δ|>=0.03 "
                "OR sign flip in mean-lift direction"
            ),
        },
        "per_group": per_group,
        "n_groups_pass": int(n_groups_pass),
        "n_groups_eligible": int(n_groups_eligible),
        "per_group_sign_flips": sign_flips,
        "top30_cross_period": top30,
        "per_group_top10_cross_period": per_group_top10,
        "calendar_persistence_xau_xag": calendar_persistence,
        "calendar_persistence_overall": calendar_overall,
        "cpcv_top1_check": {
            "cpcv_top1_feature": cpcv_top1,
            "cpcv_top1_gain": 6.0,
            "in_cross_period_top10": cpcv_top1_in_cp_top10,
            "cross_period_gain": cpcv_top1_gain_in_cp,
        },
        "selected_hp_meta": {
            "v2_hp": best_hp_v2,
            "v1_hp": best_hp_v1,
        },
        "wallclock_seconds": time.time() - t_start,
        "computed_at": utc_now(),
        "k54_v2_commit_reference": K54_V2_DIR.as_posix(),
        "data_cutoff_utc": DATA_CUTOFF,
        "split_date_utc": SPLIT_DATE,
    }
    with open(OUT_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    # Save meta
    meta = {
        "k54_version": "v2_cross_period",
        "training_spec": {
            "data_cutoff_utc": DATA_CUTOFF,
            "split_date_utc": SPLIT_DATE,
            "n_train": n_train,
            "n_test": n_test,
            "n_features_post_prune": len(feature_cols),
            "v1_baseline_n_features": int(X_v1_train.shape[1]),
        },
        "selected_hp_v2": best_hp_v2,
        "selected_hp_v2_idx": best_hp_v2_idx,
        "selected_hp_v1": best_hp_v1,
        "selected_hp_v1_idx": best_hp_v1_idx,
        "test_auc_v2": float(auc_v2_test),
        "test_auc_v1": float(auc_v1_test),
        "test_brier_v2": float(brier_v2_test),
        "test_brier_v1": float(brier_v1_test),
        "delta_auc_v2_vs_cpcv": delta_v2,
        "delta_auc_v1_vs_cpcv": delta_v1,
        "delong_p": float(p_delong),
        "robustness_verdict": robustness_verdict,
        "calendar_persistence_overall": calendar_overall,
        "n_groups_pass_cross_period": int(n_groups_pass),
        "computed_at": utc_now(),
        "wallclock_seconds": time.time() - t_start,
    }
    with open(OUT_DIR / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Per-group results
    with open(OUT_DIR / "per_group_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "per_group": per_group,
            "n_groups_pass": int(n_groups_pass),
            "n_groups_eligible": int(n_groups_eligible),
            "sign_flips_vs_cpcv": sign_flips,
            "computed_at": utc_now(),
        }, f, indent=2)

    print(f"\n=== DONE in {time.time()-t_start:.0f}s ===")
    print(f"Robustness verdict: {robustness_verdict}")
    print(f"Calendar persistence: {calendar_overall}")
    print(f"Outputs: {OUT_DIR}")
    return results


if __name__ == "__main__":
    main()
