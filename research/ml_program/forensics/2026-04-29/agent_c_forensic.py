"""Agent C — NAS_US30 Specialist Forensic Deep-Dive.

Reproduces, decomposes, and stress-tests the K54 v3 NAS_US30 specialist
(Architecture B per-cohort LightGBM):
  - load `k54_v3_nas_us30_specialist.lgb` saved booster
  - extract feature importance (gain + split count)
  - per-feature attribution (compare global vs specialist)
  - per-period stability (per-year + per-quarter AUC)
  - per-instrument breakdown (NAS100-only vs US30_cash-only)
  - cross-period: train on 2022-2023 backfill (v1-schema; no US30 data) → test 2026 NAS+US30
  - cross-period reverse: train on pre-Q2-2026 NAS+US30 → test Q2-2026 NAS+US30
  - DSR-corrected p on specialist standalone lift at N=200
  - search for analogous specialists in XAU+XAG, GBPUSD+USDJPY, GBPJPY cohorts
  - K55-shadow operational spec proposal
  - all v1-schema (cross-period feasible) AND v3-feature (in-sample only) variants
"""
from __future__ import annotations
import json
import math
import sys
import warnings
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
SCOUT_PARQUET = ROOT / "research/ml_program/scout/feature_matrix.parquet"
K54_V1_FEATURES = ROOT / "research/ml_program/models/k54_v1_features_full.csv"
V3_DIR = ROOT / "research/ml_program/models/k54_v3"
SPECIALIST_LGB = V3_DIR / "k54_v3_nas_us30_specialist.lgb"
GLOBAL_LGB = V3_DIR / "k54_v3_global.lgb"
TOP_FEATURES_JSON = V3_DIR / "top_features.json"
BACKFILL_COHORT = ROOT / "data/historical_2022_2023/trade_cohort.csv"
OUT_DIR = ROOT / "research/ml_program/forensics/2026-04-29"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_CUTOFF = "2026-04-28"
RANDOM_SEED = 42
GROUP_MAP = {
    "XAUUSD": "XAU_XAG",
    "XAGUSD": "XAU_XAG",
    "NAS100": "NAS_US30",
    "US30_CASH": "NAS_US30",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD_USDJPY",
    "USDJPY": "GBPUSD_USDJPY",
}
NAS_US30_SYMBOLS = {"NAS100", "US30_CASH"}
ANCHOR_AUC = 0.5286


def safe_auc(y, p):
    if len(np.unique(y)) < 2:
        return float("nan")
    try:
        return float(roc_auc_score(y, p))
    except Exception:
        return float("nan")


def deflated_sharpe_p(sr_obs, sigma_sr, n_trials=200):
    if not (np.isfinite(sr_obs) and np.isfinite(sigma_sr) and sigma_sr > 0):
        return float("nan")
    gamma_E = 0.5772156649015329
    log_n = math.log(max(2.0, n_trials))
    e_max_z = math.sqrt(2 * log_n) - gamma_E / math.sqrt(2 * log_n)
    e_max_sr = sigma_sr * e_max_z
    z = (sr_obs - e_max_sr) / sigma_sr
    return float(1 - stats.norm.cdf(z))


def stouffer_combine(pvalues):
    pv = [p for p in pvalues if p is not None and 0 < p < 1 and np.isfinite(p)]
    if not pv:
        return float("nan")
    z = [stats.norm.ppf(1 - p) for p in pv]
    z_combined = sum(z) / math.sqrt(len(z))
    return float(1 - stats.norm.cdf(z_combined))


def family_of(col):
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
    if col.startswith("kw__"):
        return "k54_v3_new"
    return "unknown"


def kw_subfamily(col):
    """Granular family for narrative."""
    fam = family_of(col)
    name = col
    if fam == "time_session":
        if "opex" in name.lower():
            return "time_session_opex"
        if "cpi" in name.lower() or "nfp" in name.lower() or "fomc" in name.lower():
            return "time_session_econ_event"
        if "holiday" in name.lower():
            return "time_session_holiday"
        if "kz_" in name.lower() or "hour" in name.lower():
            return "time_session_intraday"
        return "time_session_calendar"
    if fam == "liquidity":
        if "round" in name.lower():
            return "liquidity_round_number"
        if "volcluster" in name.lower():
            return "liquidity_volcluster"
        return "liquidity_other"
    return fam


def add_k54_v3_features(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate the K54 v3 closed-form K-7..K-10 features (deterministic)."""
    new_features: dict[str, np.ndarray] = {}
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
            below_dist = df["liq__liq_round_50p0_dist_below_ticks"].fillna(99999.0).values \
                if "liq__liq_round_50p0_dist_below_ticks" in df.columns else np.full(len(df), 99999.0)
            new_features["kw__k10_round50_above_below_asym"] = np.log1p(below_dist) - np.log1p(above_dist)
        else:
            new_features["kw__k10_round50_above_below_asym"] = np.zeros(len(df))
    else:
        new_features["kw__k7_osler_stopcluster_proxy"] = np.zeros(len(df))
        new_features["kw__k10_round50_above_below_asym"] = np.zeros(len(df))
    age_col = None
    for cand in ("ob_age_candles", "struct__M15__ob_age_candles_top1",
                 "struct__M15__nearest_ob_age_candles"):
        if cand in df.columns:
            age_col = cand
            break
    if age_col is not None:
        ages = df[age_col].fillna(0).values.astype(float)
        ages_clip = np.clip(ages, 1.0, 200.0)
        new_features["kw__k8_ob_age_power_law"] = ages_clip ** (-0.5)
    else:
        new_features["kw__k8_ob_age_power_law"] = np.ones(len(df))
    long_flag = (df["__direction"] == "LONG").astype(int).values \
        if "__direction" in df.columns else np.zeros(len(df))
    if "reg__regime_aligned_v1" in df.columns:
        regime_v1 = df["reg__regime_aligned_v1"].fillna(0).values
        new_features["kw__k9_regime_x_round_x_side"] = regime_v1 * round_aligned * long_flag
    else:
        new_features["kw__k9_regime_x_round_x_side"] = np.zeros(len(df))
    for col, vals in new_features.items():
        df[col] = vals
    return df


# ============================================================================
# Per-fold top-100 screening pipeline (replicates K54 v3 train_lgbm + Arch A)
# ============================================================================
SCREEN_HP = {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05, "min_data_in_leaf": 10}
SELECTED_HP = {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05}


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


def train_lgbm(X_tr, y_tr, X_val, y_val, hp):
    n_train = len(X_tr)
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
        fit_kw = {"eval_set": [(X_val, y_val)],
                  "callbacks": [lgb.early_stopping(20, verbose=False)]}
    model.fit(X_tr, y_tr, **fit_kw)
    return model


def calibrate(p_tr, y_tr, p_te):
    if len(np.unique(y_tr)) < 2:
        return p_te
    cal = LogisticRegression(max_iter=1000, C=1.0).fit(p_tr.reshape(-1, 1), y_tr)
    return cal.predict_proba(p_te.reshape(-1, 1))[:, 1]


def time_indexed_folds(dates: pd.Series, k: int):
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
    return [([i for i in range(k) if i not in tc], list(tc))
            for tc in combinations(range(k), n)]


def purge_embargo(train_idx, test_idx_groups, dates: pd.Series, purge_days, embargo_days):
    train_dates = pd.to_datetime(dates.iloc[train_idx])
    keep_mask = pd.Series(True, index=train_idx)
    for tg in test_idx_groups:
        test_dates = pd.to_datetime(dates.iloc[tg])
        t_min = test_dates.min() - pd.Timedelta(days=purge_days)
        t_max = test_dates.max() + pd.Timedelta(days=embargo_days)
        in_zone = (train_dates >= t_min) & (train_dates <= t_max)
        keep_mask = keep_mask & ~in_zone.values
    return train_idx[keep_mask.values]


# ============================================================================
# Per-cohort specialist trial under K54 v3 substrate
# ============================================================================


def run_per_cohort_specialist(
    df_full: pd.DataFrame, X_full: pd.DataFrame, y_full: np.ndarray,
    feature_cols: list[str], cohort_name: str, cohort_symbols: set[str],
    cpcv_k: int = 4, cpcv_n: int = 2,
    purge_days: int = 7, embargo_days: int = 1,
    selected_hp: dict = SELECTED_HP,
) -> dict:
    """Train an Architecture B specialist on a sub-cohort via per-cohort CPCV."""
    mask = df_full["__symbol"].isin(cohort_symbols).values
    coh_idx = np.where(mask)[0]
    n_c = len(coh_idx)
    if n_c < 30:
        return {"cohort_name": cohort_name, "n": n_c, "skipped": True}
    coh_dates = pd.to_datetime(df_full["__date"].iloc[coh_idx].astype(str).str[:10])
    folds_local = time_indexed_folds(coh_dates.reset_index(drop=True), cpcv_k)
    paths = cpcv_paths(folds_local, cpcv_n)
    spec_pred = np.full(n_c, np.nan)
    v1_pred = np.full(n_c, np.nan)
    path_aucs_spec = []
    path_aucs_v1 = []
    n_paths_actual = 0
    # Use top-100 from full-cohort path 0 of K54 v3 (same as in production specialist)
    with open(TOP_FEATURES_JSON, "r", encoding="utf-8") as f:
        top_data = json.load(f)
    spec_features = [t["feature"] for t in top_data["per_path_top100"][0]["top100"]]
    spec_features = [c for c in spec_features if c in feature_cols]
    full_dates = pd.to_datetime(df_full["__date"].astype(str).str[:10])
    for path_idx, (tg, te) in enumerate(paths):
        tr_local = np.concatenate([folds_local[i] for i in tg])
        te_local = np.concatenate([folds_local[i] for i in te])
        tr_global = coh_idx[tr_local]
        te_global = coh_idx[te_local]
        test_groups_global = [coh_idx[folds_local[i]] for i in te]
        tr_global = purge_embargo(tr_global, test_groups_global, full_dates, purge_days, embargo_days)
        if len(tr_global) < 20 or len(te_global) < 5:
            continue
        sort_p = np.argsort(full_dates.iloc[tr_global].values)
        tr_sorted = tr_global[sort_p]
        n_iv = max(10, len(tr_sorted) // 8)
        iv = tr_sorted[-n_iv:]
        ti = tr_sorted[:-n_iv]
        try:
            X_tr = X_full[spec_features].iloc[ti]
            X_iv = X_full[spec_features].iloc[iv]
            X_te = X_full[spec_features].iloc[te_global]
            m = train_lgbm(X_tr, y_full[ti], X_iv, y_full[iv], selected_hp)
            p_iv = m.predict_proba(X_iv)[:, 1]
            p_te = m.predict_proba(X_te)[:, 1]
            p_te = calibrate(p_iv, y_full[iv], p_te)
            for k_, gi in enumerate(te_global):
                local_i = np.where(coh_idx == gi)[0]
                if len(local_i) > 0:
                    spec_pred[local_i[0]] = p_te[k_]
            auc = safe_auc(y_full[te_global], p_te)
            if not math.isnan(auc):
                path_aucs_spec.append(auc)
            n_paths_actual += 1
        except Exception as e:
            print(f"    {cohort_name} path {path_idx} failed: {e}")
            continue
    valid = ~np.isnan(spec_pred)
    if valid.sum() < 30:
        return {"cohort_name": cohort_name, "n": n_c, "n_valid_predictions": int(valid.sum()),
                "skipped_low_n": True}
    y_c = y_full[coh_idx][valid]
    spec_auc = safe_auc(y_c, spec_pred[valid])
    return {
        "cohort_name": cohort_name,
        "n": n_c,
        "n_valid_predictions": int(valid.sum()),
        "n_features_used": len(spec_features),
        "specialist_auc_pooled": spec_auc,
        "per_path_aucs": path_aucs_spec,
        "per_path_mean_auc": float(np.mean(path_aucs_spec)) if path_aucs_spec else None,
        "per_path_std_auc": float(np.std(path_aucs_spec, ddof=1)) if len(path_aucs_spec) > 1 else None,
        "n_paths_actual": n_paths_actual,
    }


# ============================================================================
# V1-schema cross-period (only feasible cross-period test)
# ============================================================================
V1_NUM_COLS = ["hour_utc", "day_of_week", "counter_direction_flag",
               "ob_distance_atr", "ob_age_candles", "displacement_quality_score",
               "fvg_present", "touch_count", "ai_confidence"]
V1_CAT_COLS = ["symbol", "instrument_class", "direction_long_short",
               "kill_zone", "setup_grade", "regime_tag"]


def encode_v1(df_v1: pd.DataFrame, drop_symbol: bool = True) -> pd.DataFrame:
    enc = pd.DataFrame(index=df_v1.index)
    for c in V1_NUM_COLS:
        enc[c] = pd.to_numeric(df_v1[c], errors="coerce").fillna(-1).astype(float)
    for c in V1_CAT_COLS:
        vals = df_v1[c].fillna("__missing__").astype(str)
        codes = vals.astype("category").cat.codes
        enc[c] = codes.astype(int)
    if drop_symbol and "symbol" in enc.columns:
        enc = enc.drop(columns=["symbol"])
    return enc


def main():
    print(f"=== Agent C — NAS_US30 Specialist Forensic Deep-Dive ({datetime.now(timezone.utc).isoformat()}) ===\n")

    # ============================================================
    # STAGE 0 — Load data
    # ============================================================
    print("[0] Loading scout matrix + v1 baseline + 2022-2023 backfill...")
    df = pd.read_parquet(SCOUT_PARQUET)
    df = df.reset_index(drop=True)
    df["__date_dt"] = pd.to_datetime(df["__date"].astype(str).str[:10])
    df["dedup_key"] = list(zip(
        df["__date_dt"].astype(str),
        df["__symbol"], df["__direction"], df["__framework"],
        df["__realized_r"].round(3),
    ))
    feature_cols_raw = [c for c in df.columns if not c.startswith("__") and c != "dedup_key"]

    # Apply v2 prune
    prune_path = ROOT / "research/ml_program/models/k54_v2/feature_prune_list.json"
    with open(prune_path, "r", encoding="utf-8") as f:
        prune_data = json.load(f)
    drop = {item["feature"] for item in prune_data["prune_list"]}
    feature_cols = [c for c in feature_cols_raw if c not in drop]
    df = add_k54_v3_features(df)
    new_features = [c for c in df.columns if c.startswith("kw__")]
    feature_cols = feature_cols + new_features
    print(f"  Final v3 feature space: {len(feature_cols)}")

    X_v3 = df[feature_cols].astype(float).copy()
    X_v3 = X_v3.replace([np.inf, -np.inf], np.nan)
    y = df["__win_label"].astype(int).values
    print(f"  Cohort: n={len(df)} (NAS+US30 = {(df['__symbol'].isin(NAS_US30_SYMBOLS)).sum()})")

    # NAS_US30 mask
    nas_mask = df["__symbol"].isin(NAS_US30_SYMBOLS).values
    nas_idx = np.where(nas_mask)[0]
    print(f"  NAS_US30 indices: {len(nas_idx)}")

    # ============================================================
    # STAGE 1 — Load saved specialist + extract feature importance
    # ============================================================
    print("\n[1] Loading saved specialist booster + feature importance...")
    specialist_booster = lgb.Booster(model_file=str(SPECIALIST_LGB))
    spec_feature_names = specialist_booster.feature_name()
    print(f"  Specialist features: {len(spec_feature_names)}")

    fi_gain = specialist_booster.feature_importance(importance_type="gain")
    fi_split = specialist_booster.feature_importance(importance_type="split")
    spec_imp = pd.DataFrame({
        "feature": spec_feature_names,
        "gain": fi_gain,
        "split": fi_split,
        "family": [family_of(f) for f in spec_feature_names],
        "subfamily": [kw_subfamily(f) for f in spec_feature_names],
    }).sort_values("gain", ascending=False).reset_index(drop=True)
    spec_imp["gain_pct"] = spec_imp["gain"] / spec_imp["gain"].sum() * 100
    spec_imp["cumgain_pct"] = spec_imp["gain_pct"].cumsum()
    spec_imp.to_csv(OUT_DIR / "agent_c_specialist_feature_importance.csv", index=False)
    print(f"  Top-20 specialist features (by gain):")
    for r in spec_imp.head(20).itertuples():
        print(f"    {r.gain:7.1f} gain ({r.gain_pct:5.2f}%) [{r.subfamily:24s}] {r.feature}")

    # Compare to global top features
    print("\n[1b] Loading global K54 v3 top features...")
    global_booster = lgb.Booster(model_file=str(GLOBAL_LGB))
    g_feature_names = global_booster.feature_name()
    g_gain = global_booster.feature_importance(importance_type="gain")
    g_split = global_booster.feature_importance(importance_type="split")
    glob_imp = pd.DataFrame({
        "feature": g_feature_names,
        "gain": g_gain,
        "split": g_split,
    }).sort_values("gain", ascending=False).reset_index(drop=True)
    glob_imp["gain_pct"] = glob_imp["gain"] / glob_imp["gain"].sum() * 100

    # NAS-specific features: high specialist gain, low/zero global gain
    print("\n[1c] NAS-specific features (high specialist gain pct relative to global)...")
    merged = spec_imp.merge(
        glob_imp[["feature", "gain_pct"]].rename(columns={"gain_pct": "global_gain_pct"}),
        on="feature", how="left",
    )
    merged["global_gain_pct"] = merged["global_gain_pct"].fillna(0.0)
    merged["spec_minus_global_pct"] = merged["gain_pct"] - merged["global_gain_pct"]
    merged_sorted = merged.sort_values("spec_minus_global_pct", ascending=False).head(20)
    print("  Top-15 NAS-specific features (specialist gain minus global gain, %):")
    for r in merged_sorted.head(15).itertuples():
        print(f"    spec_pct={r.gain_pct:5.2f}, global_pct={r.global_gain_pct:5.2f}, "
              f"diff={r.spec_minus_global_pct:+.2f}%, {r.feature}")
    merged.to_csv(OUT_DIR / "agent_c_specialist_vs_global_feature_diff.csv", index=False)

    # OPEX / round-number / gamma-proxy features audit
    print("\n[1d] Auditing for OPEX / round / gamma-proxy / Mag-7 mechanism features...")
    keywords = {
        "round_number": ["round_50p0", "round_100p0", "round_aligned", "round_dist"],
        "opex": ["opex", "quarterly_opex"],
        "gamma_proxy": ["gamma", "gex", "vix1d"],
        "mag7_concentration": ["mag7", "concentration"],
        "stop_cluster": ["stopcluster", "k7_osler"],
    }
    audit = {}
    for kw_name, terms in keywords.items():
        rows = spec_imp[spec_imp["feature"].apply(lambda f: any(t in f.lower() for t in terms))]
        audit[kw_name] = {
            "n_features_in_specialist": int(len(rows)),
            "total_gain_pct": float(rows["gain_pct"].sum()),
            "top_feature": rows.iloc[0]["feature"] if len(rows) else None,
            "top_feature_gain_pct": float(rows.iloc[0]["gain_pct"]) if len(rows) else 0.0,
        }
    print("  Mechanism-feature audit on specialist:")
    for k, v in audit.items():
        print(f"    {k}: {v['n_features_in_specialist']} features, "
              f"total {v['total_gain_pct']:.2f}% gain, top: {v['top_feature']}")

    # ============================================================
    # STAGE 2 — Per-period stability (per-year + per-quarter AUC)
    # ============================================================
    print("\n[2] Per-period stability — re-running specialist via leave-one-quarter-out CPCV...")
    df["year"] = df["__date_dt"].dt.year
    df["quarter"] = df["__date_dt"].dt.to_period("Q").astype(str)

    # NAS_US30 quarterly cohort
    nas_quarter_counts = df.iloc[nas_idx].groupby("quarter").size()
    print(f"  NAS_US30 by quarter: {dict(nas_quarter_counts)}")
    nas_year_counts = df.iloc[nas_idx].groupby("year").size()
    print(f"  NAS_US30 by year: {dict(nas_year_counts)}")
    nas_year_wr = df.iloc[nas_idx].groupby("year")["__win_label"].mean()
    print(f"  NAS_US30 win-rate by year: {dict(nas_year_wr.round(3))}")

    # Run per-quarter LOQO: train all-but-one-quarter, test the held-out
    # using the path-0 spec_features (same logic as production)
    spec_feature_names_in_X = [f for f in spec_feature_names if f in feature_cols]
    print(f"  Specialist features available in current matrix: {len(spec_feature_names_in_X)}")

    nas_df = df.iloc[nas_idx].copy().reset_index(drop=True)
    X_nas = X_v3.iloc[nas_idx].reset_index(drop=True)
    y_nas = y[nas_idx]
    nas_quarters = nas_df["quarter"].unique().tolist()
    per_quarter_results = []
    for hold_q in sorted(nas_quarters):
        tr_mask = nas_df["quarter"] != hold_q
        te_mask = nas_df["quarter"] == hold_q
        if tr_mask.sum() < 30 or te_mask.sum() < 5:
            per_quarter_results.append({
                "quarter": hold_q, "n_train": int(tr_mask.sum()),
                "n_test": int(te_mask.sum()),
                "auc_specialist": None,
                "skipped": True,
            })
            continue
        X_tr = X_nas[spec_feature_names_in_X].loc[tr_mask].fillna(-9999)
        X_te = X_nas[spec_feature_names_in_X].loc[te_mask].fillna(-9999)
        y_tr = y_nas[tr_mask.values]
        y_te = y_nas[te_mask.values]
        # Inner-val: last 10% of training cohort by date
        tr_sorted = np.argsort(nas_df.loc[tr_mask, "__date_dt"].values)
        n_iv = max(5, len(tr_sorted) // 10)
        iv = tr_sorted[-n_iv:]
        ti = tr_sorted[:-n_iv]
        X_tr_p = X_tr.iloc[ti]
        X_iv_p = X_tr.iloc[iv]
        try:
            m = train_lgbm(X_tr_p, y_tr[ti], X_iv_p, y_tr[iv], SELECTED_HP)
            p_iv = m.predict_proba(X_iv_p)[:, 1]
            p_te = m.predict_proba(X_te)[:, 1]
            p_te = calibrate(p_iv, y_tr[iv], p_te)
            auc = safe_auc(y_te, p_te)
        except Exception as e:
            print(f"    Quarter {hold_q} failed: {e}")
            auc = float("nan")
        per_quarter_results.append({
            "quarter": hold_q,
            "n_train": int(tr_mask.sum()),
            "n_test": int(te_mask.sum()),
            "n_pos_test": int(y_te.sum()),
            "win_rate_test": float(y_te.mean()),
            "auc_specialist": float(auc) if not math.isnan(auc) else None,
        })
    pd.DataFrame(per_quarter_results).to_csv(
        OUT_DIR / "agent_c_specialist_per_period.csv", index=False)
    print("  Per-quarter LOQO results:")
    for r in per_quarter_results:
        if r.get("skipped"):
            print(f"    {r['quarter']}: SKIPPED (n_train={r['n_train']}, n_test={r['n_test']})")
        else:
            print(f"    {r['quarter']}: n_train={r['n_train']}, n_test={r['n_test']}, "
                  f"WR={r['win_rate_test']:.3f}, specialist AUC={r['auc_specialist']}")

    # ============================================================
    # STAGE 3 — Per-instrument breakdown (NAS100 vs US30_cash)
    # ============================================================
    print("\n[3] Per-instrument breakdown (NAS100 vs US30_cash)...")
    per_instrument = {}
    for sym in ["NAS100", "US30_CASH"]:
        sub_idx_local = np.where(nas_df["__symbol"] == sym)[0]
        if len(sub_idx_local) < 10:
            continue
        # 1. Recover specialist's CPCV-honest pool predictions on this sub-cohort
        # We rebuild using the same per-cohort CPCV pipeline as production (K=4, N=2)
        spec_run = run_per_cohort_specialist(
            df, X_v3, y, feature_cols, sym, {sym}, cpcv_k=4, cpcv_n=2,
        )
        # Per-instrument feature importance from a model fit on ALL of that instrument
        try:
            sub_global_idx = np.where((df["__symbol"] == sym).values)[0]
            if len(sub_global_idx) >= 20:
                X_sub = X_v3[spec_feature_names_in_X].iloc[sub_global_idx].fillna(-9999)
                y_sub = y[sub_global_idx]
                # Time-split inner-val
                d_sub = df.iloc[sub_global_idx]["__date_dt"].values
                sort_p = np.argsort(d_sub)
                n_iv = max(5, len(sort_p) // 10)
                iv = sort_p[-n_iv:]
                ti = sort_p[:-n_iv]
                m_inst = train_lgbm(X_sub.iloc[ti], y_sub[ti], X_sub.iloc[iv], y_sub[iv], SELECTED_HP)
                imp = m_inst.feature_importances_
                inst_top = sorted(zip(spec_feature_names_in_X, imp),
                                  key=lambda x: x[1], reverse=True)[:10]
                inst_top_list = [{"feature": f, "gain": float(g),
                                  "subfamily": kw_subfamily(f)} for f, g in inst_top]
            else:
                inst_top_list = []
        except Exception as e:
            print(f"    {sym} feature importance failed: {e}")
            inst_top_list = []
        per_instrument[sym] = {
            "n": int(spec_run.get("n", 0)),
            "n_valid_predictions": spec_run.get("n_valid_predictions", 0),
            "specialist_auc_pooled_via_cpcv": spec_run.get("specialist_auc_pooled"),
            "per_path_mean_auc": spec_run.get("per_path_mean_auc"),
            "per_path_std_auc": spec_run.get("per_path_std_auc"),
            "top10_features": inst_top_list,
            "win_rate": float(y[(df["__symbol"] == sym).values].mean()),
            "raw_count": int((df["__symbol"] == sym).sum()),
        }
        print(f"  {sym}: n={per_instrument[sym]['raw_count']}, "
              f"WR={per_instrument[sym]['win_rate']:.3f}, "
              f"specialist AUC (pooled CPCV)={per_instrument[sym]['specialist_auc_pooled_via_cpcv']}")
        if inst_top_list:
            print(f"    top-5 features: {[f['feature'] for f in inst_top_list[:5]]}")

    # NAS100 vs US30_cash feature overlap
    if "NAS100" in per_instrument and "US30_CASH" in per_instrument:
        nas_top = set(f["feature"] for f in per_instrument["NAS100"]["top10_features"])
        us30_top = set(f["feature"] for f in per_instrument["US30_CASH"]["top10_features"])
        per_instrument["nas_vs_us30_jaccard_top10"] = float(
            len(nas_top & us30_top) / max(len(nas_top | us30_top), 1)
        )
        per_instrument["nas_unique_top10"] = list(nas_top - us30_top)
        per_instrument["us30_unique_top10"] = list(us30_top - nas_top)
        per_instrument["shared_top10"] = list(nas_top & us30_top)

    with open(OUT_DIR / "agent_c_per_instrument_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(per_instrument, f, indent=2, default=str)

    # ============================================================
    # STAGE 4 — Cross-period robustness on NAS_US30 specialist
    # ============================================================
    print("\n[4] Cross-period robustness (v1-schema only — feasible direction)...")
    cross_period_results = {}

    # Direction A: train 2022-2023 NAS+US30 v1-schema → test 2024-2026 NAS+US30 v1-schema
    print("\n  4a. Train 2022-2023 backfill (NAS only — no US30 in BF) → Test 2024-2026 NAS_US30")
    bf = pd.read_csv(BACKFILL_COHORT)
    bf["date_dt"] = pd.to_datetime(bf["date_iso"].astype(str).str[:10])
    bf_nas_mask = bf["symbol"].isin(NAS_US30_SYMBOLS)
    bf_nas = bf[bf_nas_mask].copy()
    print(f"    Backfill NAS_US30: n={len(bf_nas)} (NAS100={int((bf_nas['symbol']=='NAS100').sum())}, "
          f"US30_CASH={int((bf_nas['symbol']=='US30_CASH').sum())})")
    print(f"    Backfill NAS date range: {bf_nas['date_dt'].min()} to {bf_nas['date_dt'].max()}")

    # v1-schema train on backfill, test on 2024-2026 NAS+US30
    X_bf_nas = encode_v1(bf_nas, drop_symbol=True)
    y_bf_nas = bf_nas["win_label"].astype(int).values
    # Test: 2024-2026 NAS+US30 in scout (via v1 features rebuilt from k54_v1_features_full)
    v1_full = pd.read_csv(K54_V1_FEATURES)
    v1_full["date_only"] = v1_full["date_iso"].astype(str).str[:10]
    v1_full["dedup_key"] = list(zip(
        v1_full["date_only"], v1_full["symbol"],
        v1_full["direction_long_short"], v1_full["framework"],
        v1_full["realized_r"].round(3),
    ))
    v1_full = v1_full.drop_duplicates(subset="dedup_key", keep="first")
    keys_df = pd.DataFrame({"dedup_key": df["dedup_key"].tolist()})
    v1_aligned = keys_df.merge(v1_full, on="dedup_key", how="left")
    nas_v1_aligned = v1_aligned[df["__symbol"].isin(NAS_US30_SYMBOLS).values].copy()
    X_test_nas = encode_v1(nas_v1_aligned, drop_symbol=True)
    y_test_nas = y[nas_idx]

    # Train on backfill NAS, test on 2024-2026 NAS+US30
    sort_p = np.argsort(bf_nas["date_dt"].values)
    n_iv = max(15, len(sort_p) // 10)
    iv_bf = sort_p[-n_iv:]
    ti_bf = sort_p[:-n_iv]
    try:
        m_bf = train_lgbm(X_bf_nas.iloc[ti_bf], y_bf_nas[ti_bf],
                          X_bf_nas.iloc[iv_bf], y_bf_nas[iv_bf], SELECTED_HP)
        p_iv = m_bf.predict_proba(X_bf_nas.iloc[iv_bf])[:, 1]
        p_te = m_bf.predict_proba(X_test_nas)[:, 1]
        p_te_cal = calibrate(p_iv, y_bf_nas[iv_bf], p_te)
        bf_to_2026_auc = safe_auc(y_test_nas, p_te_cal)

        # Per-instrument breakdown on 2024-2026 holdout
        bf_to_2026_per_inst = {}
        for sym in ["NAS100", "US30_CASH"]:
            sub = (df.iloc[nas_idx]["__symbol"] == sym).values
            if sub.sum() >= 10:
                bf_to_2026_per_inst[sym] = {
                    "n": int(sub.sum()),
                    "auc": safe_auc(y_test_nas[sub], p_te_cal[sub]),
                    "win_rate": float(y_test_nas[sub].mean()),
                }
        cross_period_results["A_train_22_23_BF_NAS_to_2024_26_NAS_US30"] = {
            "n_train": int(len(bf_nas)),
            "n_test": int(len(y_test_nas)),
            "auc_test_pooled": float(bf_to_2026_auc),
            "per_instrument": bf_to_2026_per_inst,
            "method": "Train 2022-2023 backfill NAS100-only (no US30 data) → Test 2024-2026 NAS+US30 (v1-schema only)",
        }
        print(f"    Pooled NAS_US30 2024-2026 AUC: {bf_to_2026_auc:.4f}")
        for sym, r in bf_to_2026_per_inst.items():
            print(f"    {sym}: n={r['n']}, AUC={r['auc']}")
    except Exception as e:
        print(f"    Direction A failed: {e}")
        cross_period_results["A_train_22_23_BF_NAS_to_2024_26_NAS_US30"] = {"failed": str(e)}

    # Direction B: train pre-Q2 2026 → test Q2 2026 NAS_US30 (v1-schema)
    print("\n  4b. Train pre-2026-04-01 NAS_US30 → Test 2026-04-01+ NAS_US30 (v1-schema)")
    nas_dates_arr = df.iloc[nas_idx]["__date_dt"].values
    pre_q2_mask = pd.to_datetime(nas_dates_arr) < pd.Timestamp("2026-04-01")
    if pre_q2_mask.sum() >= 30 and (~pre_q2_mask).sum() >= 5:
        X_pre_v1 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[pre_q2_mask], drop_symbol=True)
        X_q2_v1 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[~pre_q2_mask], drop_symbol=True)
        y_pre = y_test_nas[pre_q2_mask]
        y_q2 = y_test_nas[~pre_q2_mask]
        sort_p = np.argsort(nas_dates_arr[pre_q2_mask])
        n_iv = max(5, len(sort_p) // 10)
        iv = sort_p[-n_iv:]
        ti = sort_p[:-n_iv]
        try:
            m = train_lgbm(X_pre_v1.iloc[ti], y_pre[ti], X_pre_v1.iloc[iv], y_pre[iv], SELECTED_HP)
            p_iv = m.predict_proba(X_pre_v1.iloc[iv])[:, 1]
            p_te = m.predict_proba(X_q2_v1)[:, 1]
            p_te = calibrate(p_iv, y_pre[iv], p_te)
            cross_period_results["B_pre_Q2_to_Q2_v1schema"] = {
                "n_train": int(pre_q2_mask.sum()),
                "n_test": int((~pre_q2_mask).sum()),
                "auc": safe_auc(y_q2, p_te),
                "win_rate_train": float(y_pre.mean()),
                "win_rate_test": float(y_q2.mean()),
            }
            print(f"    Pre-Q2 train AUC: {cross_period_results['B_pre_Q2_to_Q2_v1schema']}")
        except Exception as e:
            cross_period_results["B_pre_Q2_to_Q2_v1schema"] = {"failed": str(e)}
            print(f"    Direction B failed: {e}")

    # Direction C: train Q2 2026 → test pre-Q2 2026 NAS_US30 (v1-schema, reverse)
    print("\n  4c. Reverse: Train 2026-04-01+ NAS_US30 → Test pre-2026-04-01 NAS_US30 (v1)")
    if (~pre_q2_mask).sum() >= 20 and pre_q2_mask.sum() >= 30:
        X_q2_v1 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[~pre_q2_mask], drop_symbol=True)
        X_pre_v1 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[pre_q2_mask], drop_symbol=True)
        y_q2 = y_test_nas[~pre_q2_mask]
        y_pre = y_test_nas[pre_q2_mask]
        sort_p = np.argsort(nas_dates_arr[~pre_q2_mask])
        n_iv = max(3, len(sort_p) // 10)
        iv = sort_p[-n_iv:]
        ti = sort_p[:-n_iv] if len(sort_p) - n_iv > 5 else sort_p
        try:
            m = train_lgbm(X_q2_v1.iloc[ti], y_q2[ti],
                           X_q2_v1.iloc[iv] if len(iv) else None, y_q2[iv] if len(iv) else None, SELECTED_HP)
            p_te = m.predict_proba(X_pre_v1)[:, 1]
            cross_period_results["C_Q2_to_pre_Q2_v1schema_reverse"] = {
                "n_train": int((~pre_q2_mask).sum()),
                "n_test": int(pre_q2_mask.sum()),
                "auc": safe_auc(y_pre, p_te),
                "win_rate_train": float(y_q2.mean()),
                "win_rate_test": float(y_pre.mean()),
            }
            print(f"    Q2-train→pre-Q2-test AUC: {cross_period_results['C_Q2_to_pre_Q2_v1schema_reverse']}")
        except Exception as e:
            cross_period_results["C_Q2_to_pre_Q2_v1schema_reverse"] = {"failed": str(e)}
            print(f"    Direction C failed: {e}")

    # Direction D: in-cohort H1 2026 vs H2 2026 (Jan-Feb vs Mar-Apr) split
    print("\n  4d. In-cohort H1 2026 vs H2 2026 split (v1-schema)")
    h1_mask_arr = pd.to_datetime(nas_dates_arr) < pd.Timestamp("2026-03-01")
    if h1_mask_arr.sum() >= 30 and (~h1_mask_arr).sum() >= 30:
        X_h1 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[h1_mask_arr], drop_symbol=True)
        X_h2 = encode_v1(nas_v1_aligned.reset_index(drop=True).loc[~h1_mask_arr], drop_symbol=True)
        y_h1 = y_test_nas[h1_mask_arr]
        y_h2 = y_test_nas[~h1_mask_arr]
        sort_p = np.argsort(nas_dates_arr[h1_mask_arr])
        n_iv = max(5, len(sort_p) // 10)
        iv = sort_p[-n_iv:]
        ti = sort_p[:-n_iv]
        try:
            m = train_lgbm(X_h1.iloc[ti], y_h1[ti], X_h1.iloc[iv], y_h1[iv], SELECTED_HP)
            p_iv = m.predict_proba(X_h1.iloc[iv])[:, 1]
            p_te = m.predict_proba(X_h2)[:, 1]
            p_te = calibrate(p_iv, y_h1[iv], p_te)
            cross_period_results["D_H1_2026_to_H2_2026_v1"] = {
                "n_train": int(h1_mask_arr.sum()),
                "n_test": int((~h1_mask_arr).sum()),
                "auc": safe_auc(y_h2, p_te),
                "win_rate_train": float(y_h1.mean()),
                "win_rate_test": float(y_h2.mean()),
            }
            print(f"    H1→H2 2026 v1-schema NAS_US30 AUC: {cross_period_results['D_H1_2026_to_H2_2026_v1']}")
        except Exception as e:
            cross_period_results["D_H1_2026_to_H2_2026_v1"] = {"failed": str(e)}

    with open(OUT_DIR / "agent_c_specialist_cross_period.json", "w", encoding="utf-8") as f:
        json.dump(cross_period_results, f, indent=2, default=str)

    # ============================================================
    # STAGE 5 — DSR-corrected p on specialist standalone lift at N=200
    # ============================================================
    print("\n[5] DSR-corrected p on specialist lift at N=200...")
    # Re-run NAS_US30 specialist via Architecture B per-cohort CPCV pipeline (K=4, N=2 → 6 paths)
    # to produce per-path AUC + per-path lift over global K54 v3 on same cohort
    spec_run = run_per_cohort_specialist(
        df, X_v3, y, feature_cols, "NAS_US30", NAS_US30_SYMBOLS, cpcv_k=4, cpcv_n=2,
    )
    print(f"  NAS_US30 specialist re-run (per-cohort CPCV K=4, N=2): {spec_run}")
    # Compare to global K54 v3's NAS_US30 sub-cohort AUC (single-shot)
    # We need global predictions on NAS via re-running the full pipeline; use saved
    # cpcv_paired_results.json instead
    with open(V3_DIR / "cpcv_paired_results.json", "r", encoding="utf-8") as f:
        v3_cpcv = json.load(f)
    # Per-path NAS_US30 sub-AUC from v3 global predictions
    glob_pred_nas = np.full(len(nas_idx), np.nan)
    glob_pred_count = np.zeros(len(nas_idx), dtype=int)
    for r in v3_cpcv["paths"]:
        for k_, ti_global in enumerate(r["test_idx"]):
            local_match = np.where(nas_idx == ti_global)[0]
            if len(local_match):
                li = local_match[0]
                cur = glob_pred_nas[li] if not np.isnan(glob_pred_nas[li]) else 0.0
                glob_pred_nas[li] = cur + r["p_v3_te"][k_]
                glob_pred_count[li] += 1
    glob_pred_nas = glob_pred_nas / np.maximum(glob_pred_count, 1)
    valid_g = ~np.isnan(glob_pred_nas) & (glob_pred_count > 0)
    nas_y = y[nas_idx]
    if valid_g.sum() >= 30:
        global_nas_auc = safe_auc(nas_y[valid_g], glob_pred_nas[valid_g])
    else:
        global_nas_auc = float("nan")

    spec_auc_pooled = spec_run.get("specialist_auc_pooled", float("nan"))
    delta_pooled = (spec_auc_pooled - global_nas_auc) if not (math.isnan(spec_auc_pooled) or math.isnan(global_nas_auc)) else float("nan")

    # DSR computation: SR from per-path lift (specialist - global) per path
    # Per-path lifts not directly recoverable from saved data; use:
    #   spec per-path AUC vs anchor 0.5286 (gives standalone signal)
    spec_path_aucs = spec_run.get("per_path_aucs", [])
    if len(spec_path_aucs) >= 2:
        spec_lifts = np.array(spec_path_aucs) - ANCHOR_AUC
        sr_paired = float(np.mean(spec_lifts) / np.std(spec_lifts, ddof=1)) \
            if np.std(spec_lifts, ddof=1) > 0 else 0.0
        sigma_sr = math.sqrt((1 + 0.5 * sr_paired ** 2) / max(len(spec_lifts) - 1, 1))
        dsr_p = deflated_sharpe_p(sr_paired, sigma_sr, n_trials=200)
    else:
        sr_paired = float("nan")
        sigma_sr = float("nan")
        dsr_p = float("nan")
    print(f"  Specialist standalone vs anchor 0.5286: SR={sr_paired:.4f}, "
          f"sigma_SR={sigma_sr:.4f}, DSR-p (N=200) = {dsr_p:.4f}")
    print(f"  Specialist pooled AUC = {spec_auc_pooled}, global K54 v3 NAS AUC = {global_nas_auc}, "
          f"delta = {delta_pooled}")

    # ============================================================
    # STAGE 6 — Analogous specialists in other cohorts
    # ============================================================
    print("\n[6] Analogous specialists for other cohorts (XAU+XAG, GBPJPY, GBPUSD+USDJPY)...")
    analogous = {}
    cohorts_to_test = [
        ("XAU_XAG", {"XAUUSD", "XAGUSD"}),
        ("GBPJPY", {"GBPJPY"}),
        ("GBPUSD_USDJPY", {"GBPUSD", "USDJPY"}),
    ]
    for cn, csyms in cohorts_to_test:
        print(f"\n  {cn} (n={(df['__symbol'].isin(csyms)).sum()})")
        # cpcv_k=4 for n>=80, else cpcv_k=3
        n_c = (df["__symbol"].isin(csyms)).sum()
        cpcv_k = 4 if n_c >= 80 else 3
        cpcv_n = 2
        run = run_per_cohort_specialist(
            df, X_v3, y, feature_cols, cn, csyms, cpcv_k=cpcv_k, cpcv_n=cpcv_n,
        )
        # Compute global K54 v3 AUC on this cohort from the saved CPCV predictions
        cidx = np.where(df["__symbol"].isin(csyms).values)[0]
        glob_p = np.full(len(cidx), np.nan)
        glob_count = np.zeros(len(cidx), dtype=int)
        for r in v3_cpcv["paths"]:
            for k_, ti_global in enumerate(r["test_idx"]):
                local_match = np.where(cidx == ti_global)[0]
                if len(local_match):
                    li = local_match[0]
                    cur = glob_p[li] if not np.isnan(glob_p[li]) else 0.0
                    glob_p[li] = cur + r["p_v3_te"][k_]
                    glob_count[li] += 1
        glob_p = glob_p / np.maximum(glob_count, 1)
        valid_c = ~np.isnan(glob_p) & (glob_count > 0)
        if valid_c.sum() >= 30:
            global_auc_c = safe_auc(y[cidx][valid_c], glob_p[valid_c])
        else:
            global_auc_c = float("nan")
        delta_c = (run.get("specialist_auc_pooled", float("nan")) - global_auc_c) \
            if (run.get("specialist_auc_pooled") is not None and not math.isnan(global_auc_c)) else float("nan")
        # DSR per-path on cohort
        cpa = run.get("per_path_aucs", [])
        if len(cpa) >= 2:
            lifts_c = np.array(cpa) - ANCHOR_AUC
            sr_c = float(np.mean(lifts_c) / np.std(lifts_c, ddof=1)) if np.std(lifts_c, ddof=1) > 0 else 0.0
            sigma_c = math.sqrt((1 + 0.5 * sr_c ** 2) / max(len(lifts_c) - 1, 1))
            dsr_p_c = deflated_sharpe_p(sr_c, sigma_c, n_trials=200)
        else:
            sr_c = float("nan")
            dsr_p_c = float("nan")
        analogous[cn] = {
            "n": run.get("n", 0),
            "n_paths_actual": run.get("n_paths_actual", 0),
            "specialist_auc_pooled": run.get("specialist_auc_pooled"),
            "specialist_per_path_mean": run.get("per_path_mean_auc"),
            "specialist_per_path_std": run.get("per_path_std_auc"),
            "per_path_aucs": run.get("per_path_aucs", []),
            "global_v3_auc_on_cohort": global_auc_c if not math.isnan(global_auc_c) else None,
            "specialist_minus_global_delta": delta_c if not math.isnan(delta_c) else None,
            "vs_anchor_sharpe": sr_c if not math.isnan(sr_c) else None,
            "dsr_p_at_N200": dsr_p_c if not math.isnan(dsr_p_c) else None,
            "verdict_clears_05_threshold": (run.get("specialist_auc_pooled") or 0) >= 0.55,
            "verdict_delta_geq_005": (delta_c if not math.isnan(delta_c) else 0) >= 0.05,
        }
        print(f"    pooled AUC={run.get('specialist_auc_pooled')}, "
              f"global on cohort={global_auc_c}, delta={delta_c}, "
              f"DSR-p={dsr_p_c}")
    with open(OUT_DIR / "agent_c_analogous_specialists.json", "w", encoding="utf-8") as f:
        json.dump(analogous, f, indent=2, default=str)

    # ============================================================
    # STAGE 7 — write summary JSON
    # ============================================================
    print("\n[7] Writing summary JSON...")
    summary = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "specialist_artifact": str(SPECIALIST_LGB),
        "cohort_in_data_2026_only": True,
        "n_NAS_US30_total": int(len(nas_idx)),
        "n_NAS100": int((df["__symbol"] == "NAS100").sum()),
        "n_US30_CASH": int((df["__symbol"] == "US30_CASH").sum()),
        "specialist_pooled_auc_2026Q1Q2": spec_auc_pooled if not math.isnan(spec_auc_pooled) else None,
        "global_v3_auc_on_NAS_US30_2026Q1Q2": global_nas_auc if not math.isnan(global_nas_auc) else None,
        "specialist_minus_global_delta_2026Q1Q2": delta_pooled if not math.isnan(delta_pooled) else None,
        "specialist_per_path_aucs": spec_path_aucs,
        "specialist_vs_anchor_sharpe": sr_paired if not math.isnan(sr_paired) else None,
        "specialist_dsr_p_at_N200": dsr_p if not math.isnan(dsr_p) else None,
        "mechanism_audit": audit,
        "per_quarter_loqo": per_quarter_results,
        "per_instrument_breakdown": per_instrument,
        "cross_period_v1": cross_period_results,
        "analogous_specialists": analogous,
        "feature_overlap_specialist_vs_global_top20": int(len(set(spec_imp.head(20)["feature"]) &
                                                             set(glob_imp.head(20)["feature"]))),
    }
    with open(OUT_DIR / "agent_c_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print("\nDone. Outputs:")
    for p in [
        "agent_c_specialist_feature_importance.csv",
        "agent_c_specialist_vs_global_feature_diff.csv",
        "agent_c_specialist_per_period.csv",
        "agent_c_per_instrument_breakdown.json",
        "agent_c_specialist_cross_period.json",
        "agent_c_analogous_specialists.json",
        "agent_c_summary.json",
    ]:
        print(f"  {OUT_DIR / p}")


if __name__ == "__main__":
    main()
