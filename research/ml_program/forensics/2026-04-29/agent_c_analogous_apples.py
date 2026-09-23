"""Apples-to-apples paired comparison for analogous specialists.

For each cohort (XAU+XAG, GBPJPY, GBPUSD+USDJPY) — same K=4 N=2 paths
(or K=3 N=1 for GBPJPY n=62) — paired delta of (cohort-specialist AUC) - (global K54 v3 AUC)
on the SAME test folds.
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
feature_cols_base = [c for c in df.columns if not c.startswith("__") and c != "dedup_key" and c not in drop_set]

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
feature_cols = feature_cols_base + new_features
X = df[feature_cols].astype(float).replace([np.inf, -np.inf], np.nan)
y = df["__win_label"].astype(int).values
all_dates = pd.to_datetime(df["__date"].astype(str).str[:10])

top_data = json.load(open(ROOT / "research/ml_program/models/k54_v3/top_features.json", encoding="utf-8"))
spec_features = [t["feature"] for t in top_data["per_path_top100"][0]["top100"]]
spec_features = [c for c in spec_features if c in feature_cols]
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


def run_apples(cohort_name, cohort_symbols, K, N):
    print(f"\n=== {cohort_name} (n={(df['__symbol'].isin(cohort_symbols)).sum()}, K={K}, N={N}) ===")
    coh_idx = np.where(df["__symbol"].isin(cohort_symbols).values)[0]
    coh_dates = pd.to_datetime(df["__date"].iloc[coh_idx].astype(str).str[:10]).reset_index(drop=True)
    sort_idx = np.argsort(coh_dates.values)
    fold_size = len(sort_idx) // K
    folds = [sort_idx[i * fold_size:((i + 1) * fold_size if i < K - 1 else len(sort_idx))]
             for i in range(K)]
    paths = [([i for i in range(K) if i not in tc], list(tc))
             for tc in combinations(range(K), N)]

    spec_aucs, glob_aucs, records = [], [], []
    for path_idx, (tg, te) in enumerate(paths):
        te_local = np.concatenate([folds[i] for i in te])
        coh_test = coh_idx[te_local]
        coh_test_dates = all_dates.iloc[coh_test]
        purge_lo = coh_test_dates.min() - pd.Timedelta(days=7)
        purge_hi = coh_test_dates.max() + pd.Timedelta(days=1)

        # Specialist: cohort-only train minus test
        coh_train_local = np.concatenate([folds[i] for i in tg])
        coh_train_global = coh_idx[coh_train_local]
        train_dates_p = all_dates.iloc[coh_train_global]
        in_zone = (train_dates_p >= purge_lo) & (train_dates_p <= purge_hi)
        coh_train_p = coh_train_global[~in_zone.values]
        if len(coh_train_p) < 20:
            continue
        sort_p = np.argsort(all_dates.iloc[coh_train_p].values)
        n_iv = max(5, len(sort_p) // 8)
        c_iv = coh_train_p[sort_p[-n_iv:]]
        c_ti = coh_train_p[sort_p[:-n_iv]]
        Xtr_s = X[spec_features].iloc[c_ti].fillna(-9999)
        Xiv_s = X[spec_features].iloc[c_iv].fillna(-9999)
        Xte_s = X[spec_features].iloc[coh_test].fillna(-9999)
        try:
            m_s = train_lgbm(Xtr_s, y[c_ti], Xiv_s, y[c_iv], selected_hp)
            p_s_te = m_s.predict_proba(Xte_s)[:, 1]
            p_s_iv = m_s.predict_proba(Xiv_s)[:, 1]
            p_s_te = calibrate(p_s_iv, y[c_iv], p_s_te)
            auc_s = roc_auc_score(y[coh_test], p_s_te) if len(np.unique(y[coh_test])) > 1 else float("nan")
        except Exception as e:
            print(f"  Path {path_idx} specialist fail: {e}")
            continue

        # Global: train all minus cohort test
        all_idx = np.arange(len(df))
        train_idx = np.array([i for i in all_idx if i not in coh_test])
        train_dates_g = all_dates.iloc[train_idx]
        in_zone_g = (train_dates_g >= purge_lo) & (train_dates_g <= purge_hi)
        train_idx_p = train_idx[~in_zone_g.values]
        sort_g = np.argsort(all_dates.iloc[train_idx_p].values)
        n_iv_g = max(20, len(sort_g) // 8)
        iv_g = train_idx_p[sort_g[-n_iv_g:]]
        ti_g = train_idx_p[sort_g[:-n_iv_g]]
        Xtr_g = X[spec_features].iloc[ti_g].fillna(-9999)
        Xiv_g = X[spec_features].iloc[iv_g].fillna(-9999)
        Xte_g = X[spec_features].iloc[coh_test].fillna(-9999)
        try:
            m_g = train_lgbm(Xtr_g, y[ti_g], Xiv_g, y[iv_g], selected_hp)
            p_g_te = m_g.predict_proba(Xte_g)[:, 1]
            p_g_iv = m_g.predict_proba(Xiv_g)[:, 1]
            p_g_te = calibrate(p_g_iv, y[iv_g], p_g_te)
            auc_g = roc_auc_score(y[coh_test], p_g_te) if len(np.unique(y[coh_test])) > 1 else float("nan")
        except Exception as e:
            print(f"  Path {path_idx} global fail: {e}")
            continue

        spec_aucs.append(auc_s)
        glob_aucs.append(auc_g)
        records.append({
            "path": path_idx, "n_test": int(len(coh_test)),
            "n_train_specialist": int(len(coh_train_p)), "n_train_global": int(len(train_idx_p)),
            "test_win_rate": float(y[coh_test].mean()),
            "auc_specialist": float(auc_s), "auc_global": float(auc_g),
            "auc_delta": float(auc_s - auc_g),
        })
        print(f"  Path {path_idx}: n_te={len(coh_test):3d}, "
              f"WR={y[coh_test].mean():.3f}, "
              f"spec_AUC={auc_s:.4f}, glob_AUC={auc_g:.4f}, delta={auc_s-auc_g:+.4f}")

    deltas = np.array(spec_aucs) - np.array(glob_aucs)
    if len(deltas) >= 2:
        try:
            t_stat, p_t = stats.ttest_rel(spec_aucs, glob_aucs)
        except Exception:
            t_stat, p_t = float("nan"), float("nan")
        sd_d = float(np.std(deltas, ddof=1))
        sr = float(np.mean(deltas) / sd_d) if sd_d > 0 else 0.0
        sigma_sr = math.sqrt((1 + 0.5 * sr ** 2) / max(len(deltas) - 1, 1))
        gamma_E = 0.5772156649015329
        log_n = math.log(200)
        e_max_z = math.sqrt(2 * log_n) - gamma_E / math.sqrt(2 * log_n)
        e_max_sr = sigma_sr * e_max_z
        z = (sr - e_max_sr) / sigma_sr
        dsr_p = float(1 - stats.norm.cdf(z))
    else:
        t_stat = p_t = sr = dsr_p = float("nan")

    summary = {
        "cohort": cohort_name,
        "n": int((df["__symbol"].isin(cohort_symbols)).sum()),
        "n_paths_actual": len(records),
        "specialist_per_path_mean_auc": float(np.mean(spec_aucs)) if spec_aucs else None,
        "global_per_path_mean_auc": float(np.mean(glob_aucs)) if glob_aucs else None,
        "paired_delta_mean": float(np.mean(deltas)) if len(deltas) else None,
        "paired_delta_std": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else None,
        "paired_t_p": float(p_t) if not math.isnan(p_t) else None,
        "paired_dsr_p_at_N200": dsr_p if not math.isnan(dsr_p) else None,
        "verdict": ("Significant lift" if (p_t < 0.05 and np.mean(deltas) > 0.05)
                    else "No significant lift on apples-apples"),
        "per_path": records,
    }
    print(f"  -> Spec mean={summary['specialist_per_path_mean_auc']}, "
          f"Glob mean={summary['global_per_path_mean_auc']}, "
          f"delta_mean={summary['paired_delta_mean']}, paired t-p={summary['paired_t_p']}, "
          f"DSR-p={summary['paired_dsr_p_at_N200']}")
    return summary


cohorts = [
    ("XAU_XAG", {"XAUUSD", "XAGUSD"}, 4, 2),
    ("GBPJPY", {"GBPJPY"}, 3, 1),
    ("GBPUSD_USDJPY", {"GBPUSD", "USDJPY"}, 4, 2),
]
results = {}
for cn, csyms, K, N in cohorts:
    results[cn] = run_apples(cn, csyms, K, N)

with open(OUT_DIR / "agent_c_analogous_apples.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved: {OUT_DIR / 'agent_c_analogous_apples.json'}")
