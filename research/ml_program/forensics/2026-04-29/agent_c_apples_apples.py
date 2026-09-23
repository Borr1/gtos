"""Apples-to-apples per-path comparison: specialist vs global on the SAME NAS_US30 test folds.

Production specialist_results.json reports +0.103 delta — but that compares
pool-aggregated specialist AUC (over 6 paths) vs pool-aggregated global K54 v3 AUC
(over 15 paths covering the same NAS rows). The aggregations are NOT apples-to-apples:
- Specialist: each NAS row gets ~3 predictions averaged
- Global: each NAS row gets ~5 predictions averaged
- Different pooling depths produce different effective AUC under the same predictions

The honest test is paired per-path: same K=4/N=2 NAS test folds for both models,
and compare per-path AUC paired across the 6 folds.
"""
import json
import math
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/ml_program/forensics/2026-04-29"

df = pd.read_parquet(ROOT / "research/ml_program/scout/feature_matrix.parquet").reset_index(drop=True)
prune = json.load(open(ROOT / "research/ml_program/models/k54_v2/feature_prune_list.json", encoding="utf-8"))
drop_set = {item["feature"] for item in prune["prune_list"]}
feature_cols = [c for c in df.columns if not c.startswith("__") and c != "dedup_key" and c not in drop_set]

# Replicate K54 v3 closed-form features
round_cols = [c for c in df.columns if c.startswith("liq__liq_round_") and c.endswith("_min_dist_atr")]
round_dist = df[round_cols].min(axis=1).fillna(99.0).values if round_cols else np.full(len(df), 99.0)
round_aligned = (round_dist < 0.5).astype(int)
df["kw__k10_round_aligned"] = round_aligned
df["kw__k10_round_dist_min_atr"] = round_dist
vol50 = df["vol__h1_range_over_mean_50"].fillna(1.0).values if "vol__h1_range_over_mean_50" in df else np.ones(len(df))
df["kw__k7_osler_stopcluster_proxy"] = round_aligned * vol50
above = df["liq__liq_round_50p0_dist_above_ticks"].fillna(99999.0).values if "liq__liq_round_50p0_dist_above_ticks" in df else np.full(len(df), 99999.0)
below = df["liq__liq_round_50p0_dist_below_ticks"].fillna(99999.0).values if "liq__liq_round_50p0_dist_below_ticks" in df else np.full(len(df), 99999.0)
df["kw__k10_round50_above_below_asym"] = np.log1p(below) - np.log1p(above)
ages = df["ob_age_candles"].fillna(0).values.astype(float) if "ob_age_candles" in df else np.ones(len(df))
df["kw__k8_ob_age_power_law"] = np.clip(ages, 1, 200) ** -0.5
df["kw__k9_regime_x_round_x_side"] = np.zeros(len(df))
new_features = [c for c in df.columns if c.startswith("kw__")]
feature_cols = feature_cols + new_features
X = df[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan)
y = df["__win_label"].astype(int).values

NAS_US30 = {"NAS100", "US30_CASH"}
nas_idx = np.where(df["__symbol"].isin(NAS_US30).values)[0]
print(f"NAS_US30 cohort n={len(nas_idx)}")

top_data = json.load(open(ROOT / "research/ml_program/models/k54_v3/top_features.json", encoding="utf-8"))
spec_features = [t["feature"] for t in top_data["per_path_top100"][0]["top100"]]
spec_features = [c for c in spec_features if c in feature_cols]
print(f"Top-100 features (path-0): {len(spec_features)}")

nas_dates = pd.to_datetime(df["__date"].iloc[nas_idx].astype(str).str[:10]).reset_index(drop=True)
sort_idx = np.argsort(nas_dates.values)
fold_size = len(sort_idx) // 4
folds = [sort_idx[i*fold_size:((i+1)*fold_size if i < 3 else len(sort_idx))] for i in range(4)]
paths = [([i for i in range(4) if i not in tc], list(tc)) for tc in combinations(range(4), 2)]
print(f"NAS_US30 CPCV K=4 N=2 paths: {len(paths)}")

selected_hp = {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05}


def train_lgbm(Xt, yt, Xv, yv, hp):
    n = len(Xt)
    mdl = max(3, n // 30)
    m = lgb.LGBMClassifier(
        n_estimators=hp["n_estimators"], max_depth=hp["max_depth"],
        learning_rate=hp["learning_rate"], min_data_in_leaf=mdl,
        num_leaves=2 ** hp["max_depth"], objective="binary", metric="auc",
        n_jobs=1, verbosity=-1, random_state=42, deterministic=True, force_row_wise=True,
    )
    fit_kw = {}
    if Xv is not None and len(Xv) > 0:
        fit_kw = {"eval_set": [(Xv, yv)],
                  "callbacks": [lgb.early_stopping(20, verbose=False)]}
    m.fit(Xt, yt, **fit_kw)
    return m


def calibrate(p_tr, y_tr, p_te):
    if len(np.unique(y_tr)) < 2:
        return p_te
    cal = LogisticRegression(max_iter=1000).fit(p_tr.reshape(-1, 1), y_tr)
    return cal.predict_proba(p_te.reshape(-1, 1))[:, 1]


all_dates = pd.to_datetime(df["__date"].astype(str).str[:10])

print("\nRunning per-path apples-to-apples comparison...\n")
spec_path_aucs = []
glob_path_aucs = []
per_path_records = []

for path_idx, (tg, te) in enumerate(paths):
    te_local = np.concatenate([folds[i] for i in te])
    nas_test = nas_idx[te_local]
    nas_test_dates = all_dates.iloc[nas_test]
    purge_lo = nas_test_dates.min() - pd.Timedelta(days=7)
    purge_hi = nas_test_dates.max() + pd.Timedelta(days=1)

    # Specialist: train on NAS-only minus test
    nas_train_local = np.concatenate([folds[i] for i in tg])
    nas_train_global = nas_idx[nas_train_local]
    train_dates_p = all_dates.iloc[nas_train_global]
    in_zone = (train_dates_p >= purge_lo) & (train_dates_p <= purge_hi)
    nas_train_p = nas_train_global[~in_zone.values]
    if len(nas_train_p) < 20:
        continue
    sort_p = np.argsort(all_dates.iloc[nas_train_p].values)
    n_iv = max(10, len(sort_p) // 8)
    nas_iv = nas_train_p[sort_p[-n_iv:]]
    nas_ti = nas_train_p[sort_p[:-n_iv]]
    Xtr_s = X[spec_features].iloc[nas_ti].fillna(-9999)
    Xiv_s = X[spec_features].iloc[nas_iv].fillna(-9999)
    Xte_s = X[spec_features].iloc[nas_test].fillna(-9999)
    m_s = train_lgbm(Xtr_s, y[nas_ti], Xiv_s, y[nas_iv], selected_hp)
    p_s_iv = m_s.predict_proba(Xiv_s)[:, 1]
    p_s_te = m_s.predict_proba(Xte_s)[:, 1]
    p_s_te = calibrate(p_s_iv, y[nas_iv], p_s_te)
    auc_s = roc_auc_score(y[nas_test], p_s_te) if len(np.unique(y[nas_test])) > 1 else float("nan")
    spec_path_aucs.append(auc_s)

    # Global: train on ALL rows minus NAS test
    all_idx = np.arange(len(df))
    train_idx = np.array([i for i in all_idx if i not in nas_test])
    train_dates_g = all_dates.iloc[train_idx]
    in_zone_g = (train_dates_g >= purge_lo) & (train_dates_g <= purge_hi)
    train_idx_p = train_idx[~in_zone_g.values]
    sort_g = np.argsort(all_dates.iloc[train_idx_p].values)
    n_iv_g = max(20, len(sort_g) // 8)
    iv_g = train_idx_p[sort_g[-n_iv_g:]]
    ti_g = train_idx_p[sort_g[:-n_iv_g]]
    Xtr_g = X[spec_features].iloc[ti_g].fillna(-9999)
    Xiv_g = X[spec_features].iloc[iv_g].fillna(-9999)
    Xte_g = X[spec_features].iloc[nas_test].fillna(-9999)
    m_g = train_lgbm(Xtr_g, y[ti_g], Xiv_g, y[iv_g], selected_hp)
    p_g_iv = m_g.predict_proba(Xiv_g)[:, 1]
    p_g_te = m_g.predict_proba(Xte_g)[:, 1]
    p_g_te = calibrate(p_g_iv, y[iv_g], p_g_te)
    auc_g = roc_auc_score(y[nas_test], p_g_te) if len(np.unique(y[nas_test])) > 1 else float("nan")
    glob_path_aucs.append(auc_g)

    per_path_records.append({
        "path": path_idx,
        "n_test": int(len(nas_test)),
        "n_train_specialist": int(len(nas_train_p)),
        "n_train_global": int(len(train_idx_p)),
        "test_win_rate": float(y[nas_test].mean()),
        "auc_specialist": float(auc_s),
        "auc_global": float(auc_g),
        "auc_delta": float(auc_s - auc_g),
    })
    print(f"  Path {path_idx}: n_te={len(nas_test):3d}, "
          f"WR={y[nas_test].mean():.3f}, "
          f"spec_AUC={auc_s:.4f}, glob_AUC={auc_g:.4f}, delta={auc_s-auc_g:+.4f}")

deltas = np.array(spec_path_aucs) - np.array(glob_path_aucs)
print()
print(f"Per-path SPECIALIST AUCs: {[round(a, 3) for a in spec_path_aucs]}")
print(f"Per-path GLOBAL    AUCs: {[round(a, 3) for a in glob_path_aucs]}")
print(f"Per-path DELTAS:        {[round(d, 3) for d in deltas.tolist()]}")
print(f"Spec mean    = {np.mean(spec_path_aucs):.4f} (std {np.std(spec_path_aucs, ddof=1):.4f})")
print(f"Global mean  = {np.mean(glob_path_aucs):.4f} (std {np.std(glob_path_aucs, ddof=1):.4f})")
print(f"Delta mean   = {np.mean(deltas):.4f}")
print(f"Delta std    = {np.std(deltas, ddof=1):.4f}")

t_stat, p_t = stats.ttest_rel(spec_path_aucs, glob_path_aucs)
print(f"\nPaired t-test (specialist - global): t={t_stat:.3f}, p={p_t:.4f}")
try:
    w, p_w = stats.wilcoxon(spec_path_aucs, glob_path_aucs)
    print(f"Wilcoxon signed-rank: stat={w}, p={p_w:.4f}")
except Exception as e:
    print(f"Wilcoxon failed: {e}")

# DSR on paired delta
if np.std(deltas, ddof=1) > 0:
    sr_paired = float(np.mean(deltas) / np.std(deltas, ddof=1))
    sigma_sr = math.sqrt((1 + 0.5 * sr_paired ** 2) / max(len(deltas) - 1, 1))
    gamma_E = 0.5772156649015329
    log_n = math.log(200)
    e_max_z = math.sqrt(2 * log_n) - gamma_E / math.sqrt(2 * log_n)
    e_max_sr = sigma_sr * e_max_z
    z = (sr_paired - e_max_sr) / sigma_sr
    dsr_p = float(1 - stats.norm.cdf(z))
    print(f"\nApples-apples paired DSR (N=200): SR={sr_paired:.4f}, "
          f"sigma_SR={sigma_sr:.4f}, DSR-p={dsr_p:.4f}")

# Save
with open(OUT_DIR / "agent_c_apples_apples_paired.json", "w", encoding="utf-8") as f:
    json.dump({
        "method": "Per-path apples-apples comparison: specialist (NAS-only train) vs global (full-cohort train) on SAME NAS_US30 K=4 N=2 test folds",
        "n_paths": len(per_path_records),
        "per_path": per_path_records,
        "specialist_per_path_mean_auc": float(np.mean(spec_path_aucs)),
        "specialist_per_path_std_auc": float(np.std(spec_path_aucs, ddof=1)),
        "global_per_path_mean_auc": float(np.mean(glob_path_aucs)),
        "global_per_path_std_auc": float(np.std(glob_path_aucs, ddof=1)),
        "paired_delta_mean": float(np.mean(deltas)),
        "paired_delta_std": float(np.std(deltas, ddof=1)),
        "paired_t_stat": float(t_stat),
        "paired_t_p": float(p_t),
        "paired_dsr_p_at_N200": float(dsr_p) if 'dsr_p' in locals() else None,
        "paired_sr": float(sr_paired) if 'sr_paired' in locals() else None,
        "verdict": ("Significant" if (locals().get('p_t', 1) < 0.05 and np.mean(deltas) > 0)
                    else "Not significant under paired apples-to-apples test"),
    }, f, indent=2)
print(f"\nSaved: {OUT_DIR / 'agent_c_apples_apples_paired.json'}")
